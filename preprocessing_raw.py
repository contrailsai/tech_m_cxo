import os
import gc
import cv2
import numpy as np
from pathlib import Path
from sklearn.cluster import DBSCAN
from scipy.spatial.distance import cosine
# from skimage import transform as trans
# import torch
from insightface.app import FaceAnalysis
# import dlib
# from imutils import face_utils
from tqdm import tqdm

def resample_video(video_filepath, resampled_video_filepath, resample_fps):
    
    cmd = f"ffmpeg -i \"{video_filepath}\" -vf fps={resample_fps} \"{resampled_video_filepath}\""
    os.system(cmd)
    pass

def get_video_frames(video_filepath, resample_fps):

    if resample_fps is not None:
        video_stream = cv2.VideoCapture(video_filepath)
        orig_fps = video_stream.get(cv2.CAP_PROP_FPS)
        video_stream.release()

        resampled_video_dir = os.path.join(os.path.dirname(video_filepath), "resampled")
        os.makedirs(resampled_video_dir, exist_ok = True)

        if orig_fps != 25:
            resampled_video_filepath = os.path.join(resampled_video_dir, os.path.basename(video_filepath).split('.')[0] + f"_{resample_fps}fps.mp4")
            if not os.path.isfile(resampled_video_filepath):
                resample_video(video_filepath, resampled_video_filepath, resample_fps)
            video_filepath = resampled_video_filepath

    video_frames = []
    null_count = 0
    video_stream = cv2.VideoCapture(video_filepath)

    while True:
        
        ret, frame = video_stream.read()
        
        if not ret:
            video_stream.release()
            break
        
        if frame is not None:
            video_frames.append(frame)
            if len(video_frames) >= 5000:
                break
        else:
            null_count += 1

    video_stream.release()

    return video_frames

def cluster_embeddings(embeddings, eps=0.5, min_samples=2):
    clustering_model = DBSCAN(eps=eps, min_samples=min_samples, metric='cosine')
    labels = clustering_model.fit_predict(embeddings)

    return labels

# def get_keypts(image, face, predictor, face_detector):
#     # detect the facial landmarks for the selected face
#     shape = predictor(image, face)
    
#     # select the key points for the eyes, nose, and mouth
#     leye = np.array([shape.part(37).x, shape.part(37).y]).reshape(-1, 2)
#     reye = np.array([shape.part(44).x, shape.part(44).y]).reshape(-1, 2)
#     nose = np.array([shape.part(30).x, shape.part(30).y]).reshape(-1, 2)
#     lmouth = np.array([shape.part(49).x, shape.part(49).y]).reshape(-1, 2)
#     rmouth = np.array([shape.part(55).x, shape.part(55).y]).reshape(-1, 2)
    
#     pts = np.concatenate([leye, reye, nose, lmouth, rmouth], axis=0)

#     return pts

# def img_align_crop(img, landmark=None, outsize=None, scale=1.3, mask=None):
#     """ 
#     align and crop the face according to the given bbox and landmarks
#     landmark: 5 key points
#     """

#     M = None
#     target_size = [112, 112]
#     dst = np.array([
#         [30.2946, 51.6963],
#         [65.5318, 51.5014],
#         [48.0252, 71.7366],
#         [33.5493, 92.3655],
#         [62.7299, 92.2041]], dtype=np.float32)

#     if target_size[1] == 112:
#         dst[:, 0] += 8.0

#     dst[:, 0] = dst[:, 0] * outsize[0] / target_size[0]
#     dst[:, 1] = dst[:, 1] * outsize[1] / target_size[1]

#     target_size = outsize

#     margin_rate = scale - 1
#     x_margin = target_size[0] * margin_rate / 2.
#     y_margin = target_size[1] * margin_rate / 2.

#     # move
#     dst[:, 0] += x_margin
#     dst[:, 1] += y_margin

#     # resize
#     dst[:, 0] *= target_size[0] / (target_size[0] + 2 * x_margin)
#     dst[:, 1] *= target_size[1] / (target_size[1] + 2 * y_margin)

#     src = landmark.astype(np.float32)

#     # use skimage tranformation
#     tform = trans.SimilarityTransform()
#     tform.estimate(src, dst)
#     M = tform.params[0:2, :]

#     # M: use opencv
#     # M = cv2.getAffineTransform(src[[0,1,2],:],dst[[0,1,2],:])

#     img = cv2.warpAffine(img, M, (target_size[1], target_size[0]))

#     if outsize is not None:
#         img = cv2.resize(img, (outsize[1], outsize[0]))
    
#     if mask is not None:
#         mask = cv2.warpAffine(mask, M, (target_size[1], target_size[0]))
#         mask = cv2.resize(mask, (outsize[1], outsize[0]))
#         return img, mask
#     else:
#         return img, None

# def align_face(img, landmarks, outsize=(256, 256), scale=1.3):
#     src = landmarks.astype(np.float32)

#     # Define the target positions for the key points in the aligned face
#     target_size = [112, 112]  # Original target size used for normalization
#     dst = np.array([
#         [30.2946, 51.6963],  # leye
#         [65.5318, 51.5014],  # reye
#         [48.0252, 71.7366],  # nose
#         [33.5493, 92.3655],  # lmouth
#         [62.7299, 92.2041]   # rmouth
#     ], dtype=np.float32)

#     if target_size[1] == 112:
#         dst[:, 0] += 8.0  # Adjust x coordinates based on the target size

#     # Adjust dst coordinates based on the desired output size
#     dst[:, 0] = dst[:, 0] * outsize[0] / target_size[0]
#     dst[:, 1] = dst[:, 1] * outsize[1] / target_size[1]

#     # Calculate margins for scaling
#     margin_rate = scale - 1
#     x_margin = outsize[0] * margin_rate / 2
#     y_margin = outsize[1] * margin_rate / 2

#     # Adjust dst coordinates based on margins
#     dst[:, 0] += x_margin
#     dst[:, 1] += y_margin
#     dst[:, 0] *= outsize[0] / (outsize[0] + 2 * x_margin)
#     dst[:, 1] *= outsize[1] / (outsize[1] + 2 * y_margin)

#     # Calculate transformation matrix
#     tform = cv2.estimateAffinePartial2D(src, dst)[0]
#     aligned_img = cv2.warpAffine(img, tform, (outsize[1], outsize[0]))

#     return aligned_img

def preprocess_video(video_filepath, ref_img_filepath, out_dir, resample_fps=None, num_frames=None):

    app = FaceAnalysis(name='buffalo_l', providers=['CUDAExecutionProvider'])
    app.prepare(ctx_id=0, det_size=(640, 640))

    frames_out_dir = os.path.join(out_dir, "frames", Path(video_filepath).stem)
    os.makedirs(frames_out_dir, exist_ok=True)

    print(f"Preprocessing video: {video_filepath}. Saving frames to {frames_out_dir}")

    video_frames = get_video_frames(video_filepath, resample_fps)
    all_frame_data = []

    for frame_idx, frame in enumerate(tqdm(video_frames)):
        faces = app.get(frame)
        
        for face in faces:
            face_data = [
                face.normed_embedding,
                face.bbox.astype(int),
                face.landmark_2d_106
            ]
            all_frame_data.append([frame_idx, face_data])

    if len(all_frame_data) == 0: 
        return
    
    selected_frame_indices = set()

    if ref_img_filepath:
        ref_img = cv2.imread(ref_img_filepath)
        ref_face = app.get(ref_img)
        ref_face_emb = ref_face[0].normed_embedding

        selected_frame_data = []
        for frame_data in all_frame_data:
            embedding = frame_data[1][0]
            if cosine(ref_face_emb, embedding) < 0.5:
                selected_frame_indices.add(frame_data[0])
                selected_frame_data.append(frame_data)
    
    else:
        embeddings = [frame_data[1][0] for frame_data in all_frame_data]
        embeddings = np.array(embeddings)
        labels = cluster_embeddings(embeddings)

        label_counts = np.bincount(labels[labels != -1])
        most_common_label = np.argmax(label_counts)

        selected_frame_data = []
        for frame_data, label in zip(all_frame_data, labels):
            if label == most_common_label:
                selected_frame_indices.add(frame_data[0])
                selected_frame_data.append(frame_data)

    selected_frame_indices = list(selected_frame_indices)
    if num_frames is not None:
        if len(selected_frame_indices) <= num_frames:
            valid_frame_indices = selected_frame_indices
        else:
            valid_frame_indices = list(np.linspace(0, len(selected_frame_indices) - 1, num_frames, dtype=int))
    else:
        valid_frame_indices = selected_frame_indices

    padding = 0.2

    # valid_frame_indices = selected_frame_indices -> all indices selected for clips

    # get all consecutive indices with no gap as seperate clip frames to be used.  
    # only chose the sequences/clips with more that 16 frame indices
    # create clips out of them and save them in "preprocessing/clip_[i].mp4"
    clips_list = [] #list of clips indices
    clip_indices = [] #current chosen indices (to use while iterating)
    last_idx = -1
    for i in range(len(valid_frame_indices)):
        if(last_idx==-1):
            clip_indices.append(valid_frame_indices[i])
            last_idx = i
        
        elif(i <= last_idx+2):
            clip_indices.append(valid_frame_indices[i])
            last_idx = i
        else:
            #only save clips of length greater than 16 frames
            if(len(clip_indices)>16):
                clips_list.append(clip_indices)
            clip_indices = []
            last_idx = -1
    
    # now clip_list is a list of clips to be created using their value indexes
    # create clip out of them using cv2 

    # Open the video file
    cap = cv2.VideoCapture(video_filepath)
    # Get the video properties
    fps = cap.get(cv2.CAP_SPROP_FP)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    # Create a VideoWriter for each clip
    clip_writers = []
    for i, indices in enumerate(clips_list):
        clip_writer = cv2.VideoWriter(os.path.join(out_dir, f"clip_{i}.mp4"), cv2.VideoWriter_fourcc(*'mp4v'), fps, (width, height))
        clip_writers.append(clip_writer)

    # Iterate through the frames and write them to the corresponding clip
    frame_idx = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        for i, indices in enumerate(clips_list):
            if frame_idx in indices:
                clip_writers[i].write(frame)
        frame_idx += 1

    del video_frames
    del all_frame_data
    del selected_frame_data
    gc.collect()

if __name__ == "__main__":
    print("start")
    
    # app = FaceAnalysis(name='buffalo_l', providers=['CUDAExecutionProvider'])
    # app.prepare(ctx_id=0, det_size=(640, 640))

    # # dlib_face_detector = dlib.get_frontal_face_detector()
    # # predictor_path = '/workspace/video-dfd/morancium/DeepfakeBench/preprocessing/dlib_tools/shape_predictor_81_face_landmarks.dat'
    # # if not os.path.exists(predictor_path):
    #     # logger.error(f"Predictor path does not exist: {predictor_path}")
    #     # sys.exit()
    # # dlib_face_predictor = dlib.shape_predictor(predictor_path)

    # # video_dir = "/workspace/video-dfd/morancium/DeepfakeBench/datasets/FaceForensics++/original_sequences/actors/c23/videos"
    # # out_dir = "/workspace/video-dfd/morancium/DeepfakeBench/datasets/FaceForensics++/original_sequences/actors/c23/"
    # video_dir = "/workspace/video-dfd/eval_data/gold/combined/real"
    # out_dir = "/workspace/video-dfd/morancium/DeepfakeBench/datasets/gold/real"
    # os.makedirs(out_dir, exist_ok=True)

    # video_filepaths = [os.path.join(video_dir, video_filepath) for video_filepath in os.listdir(video_dir) if video_filepath.endswith(".mp4")]

    # for video_filepath in tqdm(video_filepaths):
    #     # resampled_video_dir = os.path.join(os.path.dirname(video_filepath), "resampled")
    #     # resampled_video_filepath = os.path.join(resampled_video_dir, os.path.basename(video_filepath).split('.')[0] + f"_{25}fps.mp4")
    #     # if not os.path.isfile(resampled_video_filepath):
    #     frames_out_dir = os.path.join(out_dir, "frames", Path(video_filepath).stem)
    #     if os.path.isdir(frames_out_dir):
    #         if len(os.listdir(frames_out_dir)) == 0:

    #             preprocess_video(
    #                 video_filepath=video_filepath,
    #                 ref_img_filepath=None,
    #                 out_dir=out_dir,
    #                 resample_fps=None,
    #                 num_frames=None,
    #                 app=app,
    #                 # dlib_face_detector=dlib_face_detector,
    #                 # dlib_shape_predictor=dlib_face_predictor
    #             )
    #     else:
    #         preprocess_video(
    #                 video_filepath=video_filepath,
    #                 ref_img_filepath=None,
    #                 out_dir=out_dir,
    #                 resample_fps=None,
    #                 num_frames=None,
    #                 app=app,
    #                 # dlib_face_detector=dlib_face_detector,
    #                 # dlib_shape_predictor=dlib_face_predictor
    #             )