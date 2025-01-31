import boto3
import json
import os
import httpx
import shutil
import subprocess
import env_data
from pymongo import MongoClient
from bson import ObjectId
from preprocessing_raw import preprocess_video

test = True

#AWS
aws_region = env_data.aws_region
aws_access_key_id = env_data.aws_access_key_id
aws_access_key_secret = env_data.aws_access_key_secret
aws_sqs_queue_url = env_data.aws_sqs_queue_url
# aws_sqs_queue_url_verify = os.getenv("aws_sqs_queue_url_verify", "")
aws_s3_bucket_name = env_data.aws_s3_bucket_name

# Initialize S3 client
s3 = boto3.client('s3', region_name= aws_region, 
                  aws_access_key_id= aws_access_key_id, 
                  aws_secret_access_key= aws_access_key_secret)

# Initialize SQS client
sqs = boto3.client('sqs', region_name= aws_region, 
                   aws_access_key_id= aws_access_key_id, 
                   aws_secret_access_key= aws_access_key_secret)

#MONGODB
uri = f"mongodb+srv://{env_data.mongo_username}:{env_data.mongo_pass}@cluster0.82dnw.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
MONGO_URI = os.getenv('MONGO_URI', uri)

# Initialize MongoDB client
client = MongoClient(MONGO_URI)
db = client.poi_demo  # database name
collection = db.media  # collection name


# Directory setup
files_folder_generation_key = 2

curr_dir = os.path.abspath(os.getcwd())
parent_dir = os.path.dirname(curr_dir)
wts_dir = os.path.join(parent_dir, "weights")
upload_vid_dir = os.path.join(curr_dir, "uploads", "videos")
upload_aud_dir = os.path.join(curr_dir, "uploads", "audios")

os.makedirs(upload_vid_dir, exist_ok=True)
os.makedirs(upload_aud_dir, exist_ok=True)

def save_file(file_content, directory):
    media_file_bytes = file_content['Body'].read()
    file_path = os.path.join(directory, "saved_file")
    
    with open(file_path, "wb") as file:
        file.write(media_file_bytes)
    return file_path

def get_file_duration(file_path):
    if test:
        return 10
    else:
        # Run ffprobe command to get multimedia file information
        print(file_path)
        # ----------------------
        result = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'json', file_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Check if ffprobe executed successfully
        if result.returncode == 0:
            # Parse JSON output
            data = json.loads(result.stdout.decode('utf-8'))
            # Extract duration
            duration = float(data['format']['duration'])
            return duration
        else:
            # Error handling
            print("Error executing ffprobe:", result.stderr.decode('utf-8'))
            return None

def convert_seconds_to_minutes_and_seconds(seconds):
    minutes = seconds // 60
    remaining_seconds = seconds % 60
    return str(minutes), str(remaining_seconds)

def write_list_to_file(file_path, lst):
    try:
        with open(file_path, 'w') as file:
            for item in lst:
                file.write(str(item) + '\n')
        print(f"List written to file '{file_path}' successfully.")
    except Exception as e:
        print(f"Error: {e}")

def get_frame_check(content_folder):
    '''
        get video frame check result from ML model
        result is json with aggregrate value, values at frames, index of frames  
    '''
    
    with httpx.Client() as client:
        response = client.get(f"http://localhost:5001/frameCheck/?loc={content_folder}")
        data = response.json()
        print("got result from frame model")
    
    return {"frameCheck": data}

def get_audio_analysis(file_path, content_folder):
    '''
        runs the ML model after creating a model useable system
        return a json response as {result, result_values, result_idx}
        #### FILE SETUP TO CREATE ####
        Audio_dir
        |
        |--> temp
        |    |
        |    |-->proto.txt (audio chunks metadata)
        |    |--> (... all audio chunks) 
        |--> audio_file    
    '''    

    if test:
        print("audio analaysis test")
    else:
        temp_dir = os.path.join(content_folder, 'audio', 'temp')
        #create a new temp dir inside audio dir (recreate it if it already exist)
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        os.makedirs(temp_dir)
        # proto_filepath -> /uploads/audio/temp/test_proto.txt (data on audio files here)
        proto_filepath = os.path.join(temp_dir, 'test_proto.txt')

        file_duration = get_file_duration(file_path)
        step_size = 3.0 # a 3 second chunk size for eval
        num_steps = int( file_duration / step_size )
        out_basename = 'audioSaved'

        all_files = []
        # creating the database of audio files as chunks from the video's audio
        for i_ in range(num_steps):
            start_t = i_*step_size
            start_str = str(int(start_t)).zfill(3)
            end_t = min( (i_+1)*step_size , file_duration)
            end_str = str(int(end_t)).zfill(3)

            start_min, start_sec = convert_seconds_to_minutes_and_seconds(int(start_t))
            end_min, end_sec = convert_seconds_to_minutes_and_seconds(int(end_t))

            out_filename = out_basename + '_' + str(start_str) + '_' + str(end_str) + '.flac'
            out_file_path = os.path.join(temp_dir, out_filename)
            ffmpeg_cmnd = 'ffmpeg -loglevel error -i ' + file_path + ' -vn -ss 00:' + start_min.zfill(2) + ':' + start_sec.zfill(2) + ' -t 00:' + end_min.zfill(2) + ':' + end_sec.zfill(2) + ' ' + out_file_path
            # print(ffmpeg_cmnd)
            all_files.append(out_filename.split('.')[0])
            os.system(ffmpeg_cmnd)

        write_list_to_file(proto_filepath, all_files)
        
    #FINALLY GET THE RESPONSE FROM THE SERVER
    with httpx.Client() as client:
        response = client.get(f"http://localhost:5002/audioAnalysis/?loc={content_folder}")
        data = response.json()
        print("got result from Audio model")
        # shutil.rmtree(temp_dir)
    
    return {"audioAnalysis": data}

def get_file_paths(folder_path):
    file_paths = []
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            file_path = os.path.join(root, file)
            file_paths.append(file_path)
    return file_paths

def cleanup_dirs(content_folder):
    shutil.rmtree( os.path.join(upload_aud_dir, content_folder))
    shutil.rmtree( os.path.join(upload_vid_dir, content_folder))

def get_message_from_sqs():
    response = sqs.receive_message(
        QueueUrl=aws_sqs_queue_url,
        MaxNumberOfMessages=1,
        WaitTimeSeconds=10
    )
    return response.get('Messages', [])

def process_message(message):
    global files_folder_generation_key

    # Extract transaction ID from the message
    print(message)
    body = json.loads(message['Body'])
    mongodb_id = body
    print("mongoID: ", mongodb_id)
    
    doc = collection.find_one({'_id': ObjectId(mongodb_id)})
    
    if doc:
        media_key = doc['s3_key']
        
        # Fetch media file from S3
        media_file = s3.get_object(Bucket=aws_s3_bucket_name, Key=media_key)
        
        # create folder save file
        content_folder = f"temp_folder_{files_folder_generation_key}"
        files_folder_generation_key += 2

        os.mkdir(os.path.join(upload_vid_dir, content_folder))
        file_path = save_file(media_file, os.path.join(upload_vid_dir, content_folder) )

        #folder for preprocessing
        preprocessed_dir = os.path.join(upload_vid_dir, content_folder, 'preprocessed')
        ref_image_path = os.path.join('referance_image/img1.jpg')
        #preprocess /step2
        # step 2.1 convert to smaller clips
        # step 2.2 filter poi containing clips
        preprocess_video(file_path, ref_image_path, preprocessed_dir)

        all_preprocessed_filepaths = get_file_paths(preprocessed_dir)

        results = []
        # step 3
        # Perform your deepfake analysis logic on the media file
        for preprocessed_file in all_preprocessed_filepaths:
            if os.path.exists(preprocessed_file):

                analysis_result = analyze_media(preprocessed_dir, preprocessed_file)
                #check if error occured in creating response
                if(analysis_result==1):
                    return
            
                # true->real, false->fake
                prediction = bool(analysis_result["frameCheck"]["result"]>0.7 and analysis_result["audioAnalysis"]["result"]>-1.3)
            
                if(prediction):
                    prediction = 'real'
                else:
                    prediction = 'fake'
                    
                # Generate the key for S3 as <file_name>
                file_name = os.path.basename(preprocessed_file)
                s3_folder_str = media_key.split('/')
                video_clip_s3_key = f"{s3_folder_str[0]}/preprocessed/{s3_folder_str[3]}/{file_name}"
                # Upload the file to S3
                s3.upload_file(file_path, aws_s3_bucket_name, video_clip_s3_key)

                result = dict({
                    "raw_video_path": media_key,
                    "clip_path": video_clip_s3_key,
                    "audio": analysis_result["audioAnalysis"],
                    "frame": analysis_result["frameCheck"],                
                    "final_clip_result": prediction
                })
                results.append(result)
            else:
                print(f" the given file path does not exist {preprocessed_file}")

        collection.update_one({'_id': ObjectId(mongodb_id)}, {'$set': {
            'prediction': prediction,
            'results': result,
            'processing_status': 'done'
        }})
        
        # Delete the message from SQS after processing
        sqs.delete_message(
            QueueUrl=aws_sqs_queue_url,
            ReceiptHandle=message['ReceiptHandle']
        )
    else:
        print(f"No transaction found for ID: {mongodb_id}")

def analyze_media(content_folder, file_path):

    try:
        results = dict()
        results.update(get_frame_check(content_folder))
        results.update(get_audio_analysis(file_path, content_folder))
        # cleanup dirs
        shutil.rmtree(os.path.join(upload_vid_dir, content_folder))

    except FileExistsError:
        print("file/directory already exist removing it ")
        # cleanup dirs
        shutil.rmtree(os.path.join(upload_vid_dir, content_folder))
        return 1
    
    return results

def main():
    while True:
        messages = get_message_from_sqs()
        print("got ",len(messages)," messages")
        for message in messages:
            process_message(message)

if __name__ == "__main__":
    main()