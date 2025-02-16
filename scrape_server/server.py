from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
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
from aws_functions import s3_uploader, sqs_sender, sns_notif
from process_files import file_processor
import subprocess
import env

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Creation
    db_name = "poi_demo"
    col_name = "media"
    app.state.mongodb = MongoDBClient(db_name, col_name)
    await app.state.mongodb.connect()
    yield
    # Clean up
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

def get_filename(video_src):
    try:
        filename = os.path.basename(video_src)
        if len(filename) == 0:
            raise ValueError("error: no filename")
    except Exception:
        filename = "saved_mediafile.mp4"

async def save_video(link, video_src, filename):
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

        got_url = False
        urls = []
        async with aiohttp.ClientSession() as session:
            payload = {"url": link}
            headers = {"Accept": "application/json", "Content-Type": "application/json"}
            async with session.post(env.cobalt_api_url, json=payload, headers=headers) as response:
                print(response, response.status, await response.json())
                # Check if the request was successful
                if response.status == 200:
                    result = await response.json()
                    got_url = True
                    urls.append(result["url"])
                else:
                    got_url = False

        if not got_url:
            async with Scraper(navigation_timeout=60000, wait_for='domcontentloaded') as scraper:
                urls = await scraper.scrape_page(link)

        mongo_ids = []        
        for url in urls:
            mongo_ids.append( await save_video(link, url, result.get("filename", get_filename(url))) )

        return Response(status_code=201, content=json.dumps({
            'video_sources': urls,
            'video_count': len(urls),
            'media_mongo_ids': mongo_ids,
            'success': True,
        }), media_type="json")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
#----- LINK BASED

def run_media_files_processing_task(poi_id, media_ids):
    subprocess.Popen(["python", "process_files.py", poi_id, *media_ids])

@app.post("/process-pending")
async def process_pending(request: Request):
    # """ SEND THE MEDIA TO SQS WITH THE REQUESTED POI"""
    try:
         # get the link from json
        body = await request.json()
        media_ids = body.get('media_ids', None)   #['id-1', 'id-2', 'id-3']
        poi_id = body.get('poi_id', None)   # pid-1

        if media_ids == None or poi_id == None:    
            return Response(status_code=400, content=json.dumps({"Details": "Invalid media_id or POi ID"}), media_type="json")

        print("got media ids and poi id")
        for media_id in media_ids:
            # 1. save poi id to them
            from bson.objectid import ObjectId
            if not ObjectId.is_valid(media_id):
                raise Exception(f"invalid object ID: {media_id}")
            await app.state.mongodb.update_document(
                {"_id": ObjectId(media_id)}, 
                {
                    "poi_id": poi_id,
                }
            )
            # 2. send the sqs message
            await sqs_sender(message_body=json.dumps({
                "task_id": media_id,
                "application": "beacon"
            }))
            # 3. send the sns message
            await sns_notif(msg="start instance for poi media execution")

        return Response(status_code=201, content=json.dumps({
            "message": "Documents sent for processing.",
            "updated_ids": media_ids,
            "count": len(media_ids),
        }), media_type="json")
    except Exception as e:  
        import traceback
        traceback.print_exception(e)
        raise HTTPException(status_code=500, detail=str(e))
    

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)

