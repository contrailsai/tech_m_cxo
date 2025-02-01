from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from contextlib import asynccontextmanager
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional, Dict, Any
import asyncio
import aiohttp
from pydantic import BaseModel
from mongo import MongoDBClient
from playwright_scraper import Scraper
import json
from datetime import datetime
import os
import re
from aws_functions import s3_uploader, sqs_sender

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Creation
    db_name = "poi_demo"
    col_name = "media"
    app.state.mongodb = MongoDBClient(db_name, col_name)
    await app.state.mongodb.connect()
    # app.state.scraper = Scraper()
    yield
    # Clean up
    # await app.state.scraper.close()
    await app.state.mongodb.close()
    
# Create FastAPI app
app = FastAPI(lifespan= lifespan)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins (replace with your frontend URL in production)
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, OPTIONS, etc.)
    allow_headers=["*"],  # Allows all headers
)

#---------ENDPOINTS--------------
#-----MONGO
@app.post("/add")
async def create_item(request: Request):
    """Get a document by ID from specified collection"""
    try:
        document = await request.json()
        if not len(document.keys()) > 0: 
            return Response(status_code=400, content=json.dumps({"detail":"No data to add in document"}))
        document_id = await app.state.mongodb.insert_document(document)
        return Response(status_code=201, content=json.dumps({"id": document_id}), media_type="json")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get('/documents')
async def get_documents(request: Request):
    """Get all docs of the collection"""
    try:
        documents = list(await app.state.mongodb.get_documents({}))
        for doc in documents:
            doc['_id'] = str(doc['_id'])
            if( doc.get('created_at', False)):
                doc['created_at'] = str(doc['created_at'])
        return Response(status_code=200, content=json.dumps(documents), media_type="json")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get('/document/{id}')
async def get_document(id):
    """get a document by ID"""
    try:
        from bson.objectid import ObjectId
        if not ObjectId.is_valid(id):
            return Response(status_code=400, content=json.dumps({"detail":"Invalid ObjectId format"}))
            
        document = await app.state.mongodb.get_document({"_id": ObjectId(id)})
        if document:
            document['_id'] = str(document['_id'])
            return Response(status_code=200, content=json.dumps(document), media_type="json")
        else:
            return Response(status_code=404, content=json.dumps({"detail":"Document not found"}))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
@app.put('/update/{id}')
async def update_document(id, request: Request):
    """Update a document"""
    try:
        document = await request.json()
        from bson.objectid import ObjectId
        if not ObjectId.is_valid(id):
            return Response(status_code=400, content=json.dumps({"detail":"Invalid ObjectId format"}))

        modified_count = await app.state.mongodb.update_document({"_id": ObjectId(id)}, document)
        
        if modified_count:
            return Response(status_code=201, content=json.dumps({"status": "updated"}), media_type="json")
        
        return Response(status_code=404, content=json.dumps({"detail":"Document not found"}))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete('/delete/{id}')
async def delete_document(id):
    """Delete a document from specified collection"""
    try:
        from bson.objectid import ObjectId
        if not ObjectId.is_valid(id):
           return Response(status_code=400, content=json.dumps({"detail":"Invalid ObjectId format"}))

        deleted_count = await app.state.mongodb.delete_document({"_id": ObjectId(id)})
        if deleted_count:
            return Response(status_code=200, content=json.dumps({"status": "deleted"}), media_type="json")
        
        return Response(status_code=404, content=json.dumps({"detail":"Document not found"}))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def create_link_string(link):
    '''
    create the folder nmaes based on the links scrapped (also change . for _)
    '''
    items = link.split('/')
    if (len(items)>3) and (items[0]=='https:'):
        return "_".join(items[2].split('.'))

    elif (len(items)>=1):
        return "_".join(items[0].split('.'))

async def save_video(link, video_src):
    # MongoDB -> Create document in Media for this file
    video_metadata = {
        'source_url': link,
        'upload_status': 'pending',  # initial status
        's3_key': '',  # to be updated after upload
        'created_at': datetime.now(),  # Add creation time
    }
    #insert to mongo
    mongodb_id = await app.state.mongodb.insert_document(video_metadata)
    # result = await collection.insert_one(video_metadata)

    #save to S3
    link_str = create_link_string(link)
    s3_key = f"{link_str}/raw/{mongodb_id}.mp4"
    await s3_uploader(s3_key=s3_key, video_src=video_src)

    try:
        filename = os.path.basename(video_src)
        if len(filename) == 0:
            raise ValueError("error: no filename")
    except Exception:
        filename = "saved_mediafile.mp4"

    # update the mongo
    from bson.objectid import ObjectId
    count = await app.state.mongodb.update_document({"_id": ObjectId(mongodb_id)}, {
        'upload_status': 'completed',
        's3_key': s3_key,
        'contentType': 'video/mp4',
        'processing_status': 'pending',
        'file_name': filename
    })

    # success
    return mongodb_id

def is_valid_url(url: str) -> bool:
    if len(url)< 0:
        return False
    
    pattern = re.compile(
        r'^(https?|ftp)://'  # Protocol (http, https, or ftp)
        r'([A-Za-z0-9-]+\.)+[A-Za-z]{2,}'  # Domain (e.g., example.com)
        r'(/[\w\-./?%&=]*)?'  # Optional path and query string
        r'(\?[\w&=]*)?'  # Optional query parameters
        r'(#\w*)?$',  # Optional fragment
        re.IGNORECASE
    )
    return bool(pattern.match(url))

#----- LINK BASED
@app.post("/crawl")
async def crawl(request: Request):
    """Scrape a given link for videos | youtube or any other social media content """
    try:
        body = await request.json()
        link = body.get("link", "")

        if not is_valid_url(link):
            return Response(status_code=400, content=json.dumps({"detail": "invalid Link provided"}), media_type="json")

        async with Scraper(navigation_timeout=60000, wait_for='domcontentloaded') as scraper:
            urls = await scraper.scrape_page(link)

        mongo_ids = []        
        for url in urls:
            mongo_ids.append( await save_video(link, url) )

        return Response(status_code=201, content=json.dumps({
            'video_sources': urls,
            'video_count': len(urls),
            'media_mongo_ids': mongo_ids,
            'success': True,
        }), media_type="json")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

#----- LINK BASED
@app.post("/process-pending")
async def crawl(request: Request):
    """ SEND THE MEDIA TO SQS WITH THE REQUESTED POI"""
    try:
        # get the link from json
        body = await request.json()
        media_ids = body.get('media_ids', None)   #['id-1', 'id-2', 'id-3']
        poi_id = body.get('poi_id', None)   # pid-1

        if media_ids == None or poi_id == None:    
            return Response(status_code=400, content=json.dumps({"Details": "Invalid media_id or POi ID"}), media_type="json")

        updated_ids = []
        for _id in media_ids:
            # Send _id to SQS queue
            # MESSAGE = Media_ID|POI_ID 
            await sqs_sender(message_body=f"{_id}|{poi_id}")
            print(f"Sent message with _id: {_id} to SQS queue.")

            # Update the document's processing_status to "in-queue"
            from bson.objectid import ObjectId
            count = await app.state.mongodb.update_document({"_id": ObjectId(_id)}, {"processing_status": "in-queue"})
            updated_ids.append(_id)

        return Response(status_code=201, content=json.dumps({
            "message": "Documents updated and sent to queue for processing.",
            "updated_ids": updated_ids,
            "count": len(updated_ids),
        }), media_type="json")
    except Exception as e:  
        raise HTTPException(status_code=500, detail=str(e))
    

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)

