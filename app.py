from flask import Flask, request, jsonify
import boto3
from pymongo import MongoClient
from bson import ObjectId
import os
import csv
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
# from bs4 import BeautifulSoup
import requests
import env_data
from datetime import datetime

app = Flask(__name__)

#SELENIUM
# Set up ChromeDriver options
chrome_options = Options()
chrome_options.add_argument("--headless")  # Run Chrome in headless mode
chrome_options.add_argument("--disable-gpu")  # Disable GPU acceleration

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

version = str('0.1')

uri = f"mongodb+srv://{env_data.mongo_username}:{env_data.mongo_pass}@cluster0.82dnw.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
MONGO_URI = os.getenv('MONGO_URI', uri)

# Initialize MongoDB client
client = MongoClient(MONGO_URI)
db = client.poi_demo  # database name
collection = db.media  # collection name

@app.route('/')
def home():
    return "Welcome to the Flask MongoDB API!"

@app.route('/add', methods=['POST'])
def add_document():
    data = request.json
    result = collection.insert_one(data)
    return jsonify({"inserted_id": str(result.inserted_id)}), 201

@app.route('/documents', methods=['GET'])
def get_documents():
    documents = list(collection.find())
    for doc in documents:
        doc['_id'] = str(doc['_id'])
    return jsonify(documents)

@app.route('/document/<id>', methods=['GET'])
def get_document(id):
    from bson.objectid import ObjectId
    document = collection.find_one({"_id": ObjectId(id)})
    if document:
        document['_id'] = str(document['_id'])
        return jsonify(document)
    else:
        return jsonify({"error": "Document not found"}), 404

@app.route('/update/<id>', methods=['PUT'])
def update_document(id):
    from bson.objectid import ObjectId
    data = request.json
    result = collection.update_one({"_id": ObjectId(id)}, {"$set": data})
    if result.matched_count:
        return jsonify({"message": "Document updated"})
    else:
        return jsonify({"error": "Document not found"}), 404

@app.route('/delete/<id>', methods=['DELETE'])
def delete_document(id):
    from bson.objectid import ObjectId
    result = collection.delete_one({"_id": ObjectId(id)})
    if result.deleted_count:
        return jsonify({"message": "Document deleted"})
    else:
        return jsonify({"error": "Document not found"}), 404

#
#
#
#
#
#CSV CRAWLER HERE

@app.route('/get-crawler-links', methods=['GET'])
def crawler_links():
    
    with open('crawl_links.csv', 'r') as csv_file:
        reader = csv.reader(csv_file)
        links = [row[0] for row in reader][1:]  # Extract the first element of each row
        
    return jsonify({"count": len(links),'links': links, "version": f"v{version}"})

@app.route('/add-crawler-link', methods=['POST'])
def add_crawler_link():
    new_link = request.json.get('link')
    
    if not new_link:
        return jsonify({'error': 'Missing link parameter', 'version': f"v{version}"}), 400
    
    with open('crawl_links.csv', 'a', newline='') as csv_file:
        csv_file.write(new_link + '\n')
    
    return jsonify({'success': True, 'message': 'Link added successfully', 'version': f"v{version}"})

#----crawling related functions
def get_video_links(url):
    '''
    get all video sources from the given url 
    -> search includes the documents hidden inside object tags

    - input: the url to search inside
    - output: list of video source urls
    '''
    driver = webdriver.Chrome(options=chrome_options)

    def get_videolinks():        
        src_urls = []
        # Get video elements
        video_elements = driver.find_elements(By.TAG_NAME, 'video')
        for video in video_elements:
            src = video.get_attribute('src')
            if src:
                src_urls.append(src)

        # Get iframe elements
        iframe_elements = driver.find_elements(By.TAG_NAME, 'iframe')
        for iframe in iframe_elements:
            src = iframe.get_attribute('src')
            if src:
                src_urls.append(src)

        # Get Source elements (video tags containing source tags instead of src in video tags)
        src_elements = driver.find_elements(By.XPATH, "//source[ contains(@type, 'video/mp4') ]")
        for sources in src_elements:
            src = sources.get_attribute('src')
            if src:
                src_urls.append(src)

        return src_urls
    
    try:
        # url = "https://investseries.shop/"
        video_urls = []
        driver.get(url)
        time.sleep(4)
        video_urls.extend(get_videolinks())

        objects = driver.find_elements(By.TAG_NAME, 'object')
        for object in objects:
            data = object.get_attribute('data')
            temp_url = data
            driver.get(temp_url)
            time.sleep(4)
            video_urls.extend(get_videolinks())
    except Exception as e:
        print("Error::: ", e)
    finally:
        driver.quit()

    return video_urls

def save_videos(link, video_src):
    '''
    Save the video to S3 bucket based on the url link and the video src
    Save the media to mongodb as well
    - input: 
        1. link (site source link)
        2. video_src (source of video found from link)
    - output: 
        S3 folder Key for the saved file (returns empty string on error)
    '''
     # MongoDB ->Create document in Media for this file
    video_metadata = {
        'source_url': link,
        'upload_status': 'pending',  # initial status
        's3_key': '',  # to be updated after upload
        'created_at': datetime.now()  # Add creation time
    }
    result = collection.insert_one(video_metadata)
    mongodb_id = str(result.inserted_id)  # Get MongoDB document ID

    # STREAM THE VIDEO AND SAVE IT IN S3
    response = requests.get(video_src, stream=True)
    if response.status_code == 200:
        link_str = create_link_string(link)
        s3_key = f"{link_str}/raw/{mongodb_id}"+".mp4"

        with response as video_stream:
            # s3.upload_fileobj(video_stream.raw, aws_s3_bucket_name, s3_key)
            s3.upload_fileobj(
                video_stream.raw, 
                aws_s3_bucket_name, 
                s3_key,
                ExtraArgs={'ContentType': 'video/mp4'}
            )
        try:
            filename = os.path.basename(video_src)
            if(len(filename)==0):
                raise "error: no filename"
        except:
            filename = "saved_mediafile.mp4"

        collection.update_one({'_id': ObjectId(mongodb_id)}, {'$set': {
            'upload_status': 'completed',
            's3_key': s3_key,
            'contentType': 'video/mp4',
            'processing_status': 'pending',
            'file_name': filename
        }})
    else:
        print(f"Failed to download video {video_src}: HTTP {response.status_code}")
        return ""
    
    #success
    return s3_key
        
def create_link_string(link):
    '''
    create the folder nmaes based on the links scrapped (also change . for _)
    '''
    items = link.split('/')
    if (len(items)>3) and (items[0]=='https:'):
        return "_".join(items[2].split('.'))
    
    elif (len(items)>=1):
        return "_".join(items[0].split('.'))
    
@app.route('/crawl-videos', methods=['POST'])
def crawl_videos():
    # get the link from json
    link = request.json.get('link')
    if not link:
        return jsonify({'error': 'Missing link parameter'}), 400
    
    # store link
    with open('crawl_links.csv', 'a', newline='') as csv_file:
        csv_file.write(link + '\n')

    #get video sources from link
    video_urls = []
    try:
        video_urls = get_video_links(link)
    except Exception as e:
        print(e)
        return jsonify({'error': "Error while scraping"}), 500
    
    print(video_urls)
    # handle for no vidoes found
    if not video_urls:
        return jsonify({
            'video_sources': [],
            'video_count': 0,
            'message': 'No videos found on the page.',
        }), 200

    # Download videos
    video_dir = 'videos'
    if not os.path.exists(video_dir):
        os.makedirs(video_dir)

    downloaded_videos = []
    for src in video_urls:
        try:
            s3_key = save_videos(link, src)
            downloaded_videos.append(s3_key)
        except requests.exceptions.RequestException as e:
            print(f"Error downloading video {src}: {str(e)}")
            continue

    return jsonify({
        'video_sources': video_urls,
        'video_count': len(video_urls),
        'downloaded_videos': downloaded_videos,
        'message': 'Videos saved successfully',
        'success': True,
        'version': f"v{version}"
    }), 200

@app.route('/scrape-crawler-videos', methods=['GET'])
def scrape_crawler_videos():

    links = []
    with open('crawl_links.csv', 'r') as csv_file:
        reader = csv.reader(csv_file)
        links = [row[0] for row in reader][1:]  # Extract the first element of each row
    
    count = 0
    saved_videos_info = dict()
    source_videos_info = dict()
    for link in links:
        print(f"starting url {link}")
        #get video sources from link
        video_urls = []
        try:
            video_urls = get_video_links(link)
        except Exception as e:
            print(e)
            return jsonify({'error': "Error while scraping"}), 500
        
        print(video_urls)
        # handle for no vidoes found
        if not video_urls:
            return jsonify({
                'video_sources': [],
                'video_count': 0,
                'message': 'No videos found on the page.',
            }), 200

        saved_videos = []
        source_videos = []
        for src in video_urls:
            try:
                source_videos.append(src)
                s3_key = save_videos(link, src)

                if(len(s3_key)==0):
                    print(f"Error saving video")
                    continue
                
                saved_videos.append(s3_key)
            except requests.exceptions.RequestException as e:
                print(f"Error saving video {src}: {str(e)}")
                continue
        saved_videos_info[link] = saved_videos
        source_videos_info[link] = source_videos
        count += len(saved_videos)

    return jsonify({
        'saved_data': saved_videos_info,
        'source_data': source_videos_info,
        'total_video_count': count,
        'message': 'Videos saved successfully',
        'success': True,
        'version': f"v{version}"
    }), 200

@app.route('/process-pending', methods=['GET'])
def process_pending():
    try:
        # Query MongoDB for documents with processing_status "pending"
        pending_documents = list(collection.find({"processing_status": "pending"}))

        if len(pending_documents) == 0:
            return jsonify({"message": "No pending documents found."}), 200

        updated_ids = []

        # Loop through each document and process it
        for doc in pending_documents:
            _id = doc['_id']
            
            # Send _id to SQS queue
            sqs.send_message(
                QueueUrl=aws_sqs_queue_url,
                MessageBody=str(_id)
            )
            print(f"Sent message with _id: {_id} to SQS queue.")

            # Update the document's processing_status to "in-queue"
            collection.update_one({"_id": ObjectId(_id)}, {"$set": {"processing_status": "in-queue"}})
            updated_ids.append(str(_id))

        return jsonify({
            "message": "Documents updated and sent to queue for processing.",
            "updated_ids": updated_ids,
            "count": len(updated_ids),
            "version": f"v{version}"
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
