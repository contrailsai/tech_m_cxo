import os
import gc
import cv2
import numpy as np
# from pathlib import Path
# from sklearn.cluster import DBSCAN
from scipy.spatial.distance import cosine
from insightface.app import FaceAnalysis
# from tqdm import tqdm
import subprocess
import argparse
import sys

def create_clip_with_audio(input_video, output_path, start_frame, end_frame, fps):
    """
    Create a video clip with audio using ffmpeg
    """
    start_time = start_frame / fps
    duration = (end_frame - start_frame) / fps
    
    cmd = f'ffmpeg -i "{input_video}" -ss {start_time:.3f} -t {duration:.3f} -c:v libx264 -c:a aac "{output_path}" -y'
    try:
        subprocess.run(cmd, shell=True, check=True, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        print(f"Error creating clip: {e.stderr.decode()}")
        return False
    return True

def align_face(img, landmarks, outsize=(256, 256), scale=1.3):
    src = landmarks.astype(np.float32)

    # Define the target positions for the key points in the aligned face
    target_size = [112, 112]  # Original target size used for normalization
    dst = np.array([
        [30.2946, 51.6963],  # leye
        [65.5318, 51.5014],  # reye
        [48.0252, 71.7366],  # nose
        [33.5493, 92.3655],  # lmouth
        [62.7299, 92.2041]   # rmouth
    ], dtype=np.float32)

    if target_size[1] == 112:
        dst[:, 0] += 8.0  # Adjust x coordinates based on the target size

    # Adjust dst coordinates based on the desired output size
    dst[:, 0] = dst[:, 0] * outsize[0] / target_size[0]
    dst[:, 1] = dst[:, 1] * outsize[1] / target_size[1]

    # Calculate margins for scaling
    margin_rate = scale - 1
    x_margin = outsize[0] * margin_rate / 2
    y_margin = outsize[1] * margin_rate / 2

    # Adjust dst coordinates based on margins
    dst[:, 0] += x_margin
    dst[:, 1] += y_margin
    dst[:, 0] *= outsize[0] / (outsize[0] + 2 * x_margin)
    dst[:, 1] *= outsize[1] / (outsize[1] + 2 * y_margin)

    # Calculate transformation matrix
    tform = cv2.estimateAffinePartial2D(src, dst)[0]
    aligned_img = cv2.warpAffine(img, tform, (outsize[1], outsize[0]))

    return aligned_img


def preprocess_video(video_filepath, ref_img_filepath, out_dir=None, resample_fps=None, num_frames=None):
    print("preprocessing video for IMAGE START")    
    # video_filepath = '/dir1/dir2/filename.mp4'
    filename = video_filepath.split("/")[-1].split(".")[0] 

    # face detection + embeddings creation model 
    app = FaceAnalysis(name='buffalo_l', providers=['CUDAExecutionProvider'])
    app.prepare(ctx_id=0, det_size=(640, 640))

    # prepare reference image's embedding
    ref_img = cv2.imread(ref_img_filepath)
    ref_face = app.get(ref_img)
    ref_face_emb = ref_face[0].normed_embedding
    print(ref_face_emb)

    face_is_there = 0
    usable_frame_indices = []
    curr_idx = 0

    # # saving all valid frames as images in frames folder
    # frames_path = os.path.join(out_dir, filename)
    # if not os.path.isdir( frames_path):
    #     os.makedirs( frames_path )

    # STARTING VIDEO PROCESSING
    print("processing video initiated ")        
    video_stream = cv2.VideoCapture(video_filepath)
    fps = video_stream.get(cv2.CAP_PROP_FPS)
    while True:
        ret, frame = video_stream.read()
        if not ret:
            video_stream.release()
            break

        if frame is not None:
            # check for face, comapre with poi store the result 
            # (index is face detected, false otherwise)
            faces = app.get(frame)
            for face in faces:

                embedding = face.normed_embedding   #embedding
                all_landmarks = face.landmark_2d_106
                landmark_indices = np.array([35, 93, 74, 52, 61])
                landmarks = all_landmarks[landmark_indices, :]

                print(cosine(ref_face_emb, embedding), face_is_there)
                if cosine(ref_face_emb, embedding) < 0.5:
                    face_is_there += 1
            del faces
        
        if(face_is_there >= 50): # confirmed the image's face was there for 50 frames (around 2 secs for 25 fps video)
            face_is_there = True
            print("got many frames with the face")
            break

        curr_idx+=1
        if curr_idx%100==0:
            print('.', end='')
    video_stream.release()

    gc.collect()

    if face_is_there:
        print("face is there")
        return 100 # face is there
    else:
        print("face is not there")
        return 200 # face is not there
    
if __name__ == "__main__":
    print("enter face check file")
    parser = argparse.ArgumentParser(description='check if the person in photo is there in the video')
    parser.add_argument('img_path', type=str, help='Image path of person s photo')
    parser.add_argument('video_path', type=str, help='video path of the video to check')
    args = parser.parse_args()
    
    img_path = args.img_path
    video_path = args.video_path    

    value = preprocess_video(video_path, img_path)
    sys.exit(value)