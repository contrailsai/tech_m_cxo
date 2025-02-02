from typing import Optional, Dict, Any, List
from aws_functions import s3_downloader
from mongo import MongoDBClient
import os
import zmq
import zmq.asyncio
import asyncio
import json
import argparse

async def file_processor( poi_id: str, media_ids: List[str]):
    
    # Create MongoDB client and connect
    db_name = "poi_demo"
    col_name = "media"
    mongo_client = MongoDBClient(db_name, col_name)
    await mongo_client.connect()
    
    for media_id in media_ids:
        
        responses = []
        compiled_response = []
        compiled_prediction = 1
        
        print(f"starting file processing for media_id : {media_id}")
        # get media-id's document
        from bson.objectid import ObjectId
        if not ObjectId.is_valid(media_id):
            raise Exception(f"invalid object ID: {media_id}")
            
        doc= await mongo_client.get_document({"_id": ObjectId(media_id)})
        if doc:
            doc['_id'] = str(doc['_id'])
        else:
            raise Exception(f"Error in getting document from ID: {media_id}")        
        print("got doc", doc)    

        # download file from S3
        local_video_path = os.path.join("tmp", "temp_file.mp4")
        await s3_downloader(doc["s3_key"], local_video_path)
        video_path = os.path.abspath(local_video_path)
        
        # pre model results check to know if POI is there in the video
        poi_mongo_client = MongoDBClient(db_name, "poi")
        await poi_mongo_client.connect()
        poi_doc = await poi_mongo_client.get_document({"_id": ObjectId(poi_id)})

        local_img_path = os.path.join("tmp", "temp_file.png")
        await s3_downloader(poi_doc["s3_keys"][0], local_img_path)
        img_path = os.path.abspath(local_img_path)

        await poi_mongo_client.close()

        # run face_check_processor.py subprocess
        import subprocess
        conda_env = "DFB"
        command = f"$HOME/miniconda3/envs/{conda_env}/bin/python face_check_processor.py {img_path} {video_path}"
        print(command)
        process = subprocess.run(command, shell=True, capture_output=True, text=True)
        print("FACE CHECK Return value:", process.returncode)

        if process.returncode == 200:
            # face not present in video
            # save responses to mongo for no poi
            await mongo_client.update_document(
                {"_id": ObjectId(media_id)}, 
                {
                    "results": [],
                    "prediction": "no-poi",
                    "poi_id": poi_id,
                    "processing_status": "done", 
                }
            )
            break

        # CASES OF POI PRESENT IN VIDEO
        # Create json for file process request for each model
        json_request_data = dict()
        json_request_data["video_path"] = video_path
        json_request_data["video_duration"] = 0
        json_request_data["video_fps"] = 0
        
        # Iteratevely send request json to models for processing via zeroMQ
        for model in [
            ("dfdc", 6555, "video"), 
            ("altfreeze_exp_0", 6556, "video"), 
            ("ssl_w1", 6557, "audio"), 
            ("ssl_w2", 6558, "audio"), 
            ("altfreeze_exp_4", 6560, "video")]:

            context = zmq.asyncio.Context()
            socket = context.socket(zmq.REQ)
            socket.connect(f"tcp://127.0.0.1:{model[1]}")

            message = json.dumps(json_request_data).encode('utf-8')
            print(f"sending message {message} to socket {str(socket)}")
            # Send request
            await socket.send_multipart([message])

            # Wait for response with timeout
            response_parts = await asyncio.wait_for(socket.recv_multipart(), timeout=1200.0)
            response = json.loads(response_parts[0].decode('utf-8'))

            print(f"RESPONSE from {model} = {response}")
            responses.append(response)

            # compile all saved responses
            compiled_response.append({
                "model_name": model[0],
                "score": response["result"], # score of real/fake
                "result": "real" if response["result"]>response["threshold"] else "fake", #fake/real
                "model_type": model[2]
            })

            compiled_prediction = min(compiled_prediction, response["result"]-response["threshold"])

        # save responses to mongo
        await mongo_client.update_document(
            {"_id": ObjectId(media_id)}, 
            {
                "processing_status": "done", 
                "results": compiled_response, 
                "prediction": "real" if compiled_prediction>0 else "fake",
                "poi_id": poi_id
            }
        )

    # Clean up
    await mongo_client.close()

if __name__ == "__main__":
    # sample usage: python process_files.py p_id1 m_id1, m_id2, m_id3
    parser = argparse.ArgumentParser(description='Process some videos for POI deepfake detection')
    parser.add_argument('poi_id', type=str, help='POI ID')
    parser.add_argument('media_ids', type=str, nargs='+', help='Media IDs')
    args = parser.parse_args()
    
    poi_id = args.poi_id
    media_ids = args.media_ids    

    asyncio.run(file_processor(poi_id, media_ids))