"""
Real-time Facial Emotion Recognition using MediaPipe Face Mesh

This implementation is based on and adapted from:
    "hand-gesture-recognition-using-mediapipe" by Kazuhito Takahashi (Kazuhito00)
    Original repository: https://github.com/Kazuhito00/hand-gesture-recognition-using-mediapipe
    Licensed under Apache License 2.0
"""

import cv2
import numpy as np
import mediapipe as mp
from apps.shared.keypoint_classifier.classifier import KeyPointClassifier

CAMERA_INDEX = 0

# MediaPipe setup
mp_face_mesh = mp.solutions.face_mesh
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

EMOTIONS = ["happy", "sad", "neutral", "surprised"]

def calc_landmark_list(image, landmarks):
    """Convert MediaPipe landmarks to normalized coordinate list"""
    image_width, image_height = image.shape[1], image.shape[0]
    landmark_point = []
    
    for landmark in landmarks.landmark:
        landmark_x = min(int(landmark.x * image_width), image_width - 1)
        landmark_y = min(int(landmark.y * image_height), image_height - 1)
        landmark_point.append([landmark_x, landmark_y])
    
    return landmark_point

def pre_process_landmark(landmark_list):
    """Normalize landmark coordinates"""
    temp_landmark_list = np.array(landmark_list, dtype=np.float32)
    
    # Convert to relative coordinates
    base_x, base_y = temp_landmark_list[0][0], temp_landmark_list[0][1]
    temp_landmark_list[:, 0] = temp_landmark_list[:, 0] - base_x
    temp_landmark_list[:, 1] = temp_landmark_list[:, 1] - base_y
    
    # Normalize
    temp_landmark_list = temp_landmark_list.flatten()
    max_value = max(list(map(abs, temp_landmark_list)))
    
    if max_value == 0:
        return temp_landmark_list.tolist()
    
    def normalize_(n):
        return n / max_value
    
    temp_landmark_list = list(map(normalize_, temp_landmark_list))
    
    return temp_landmark_list

def draw_bounding_rect(image, landmarks):
    """Draw bounding rectangle around face"""
    image_width, image_height = image.shape[1], image.shape[0]
    
    landmark_array = np.empty((0, 2), int)
    for landmark in landmarks.landmark:
        landmark_x = min(int(landmark.x * image_width), image_width - 1)
        landmark_y = min(int(landmark.y * image_height), image_height - 1)
        landmark_point = [np.array((landmark_x, landmark_y))]
        landmark_array = np.append(landmark_array, landmark_point, axis=0)
    
    x, y, w, h = cv2.boundingRect(landmark_array)
    
    return x, y, x + w, y + h

def draw_info_text(image, brect, emotion, confidence):
    """Draw emotion information on image"""
    cv2.rectangle(image, (brect[0], brect[1]), (brect[2], brect[1] - 22), (0, 0, 0), -1)
    
    info_text = f'{emotion}: {confidence:.2f}'
    cv2.putText(image, info_text, (brect[0] + 5, brect[1] - 4),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)
    
    return image

def main():
    # Load emotion labels
    print(f"Loaded emotion labels: {EMOTIONS}")
    
    # Initialize emotion classifier
    try:
        emotion_classifier = KeyPointClassifier(model_path='./models/emotion_classifier.tflite')
        print("Emotion classifier loaded successfully!")
    except Exception as e:
        print(f"Error loading emotion classifier: {e}")
        print("Please train the model first by running train.py")
        return
    
    # Initialize camera
    vid = cv2.VideoCapture(CAMERA_INDEX)
    vid.set(cv2.CAP_PROP_FRAME_WIDTH, 960)
    vid.set(cv2.CAP_PROP_FRAME_HEIGHT, 540)
    
    if not vid.isOpened():
        print("Error: Could not open camera")
        return
    
    print("Starting facial emotion recognition...")
    print("Press 'q' to quit")
    
    with mp_face_mesh.FaceMesh(
        max_num_faces=1,
        refine_landmarks=True,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5) as face_mesh:
        
        while True:
            ret, frame = vid.read()
            if not ret:
                break
            
            frame = cv2.flip(frame, 1)
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            results = face_mesh.process(frame_rgb)
            
            if results.multi_face_landmarks:
                for face_landmarks in results.multi_face_landmarks:
                    # Draw face mesh
                    mp_drawing.draw_landmarks(
                        frame,
                        face_landmarks,
                        mp_face_mesh.FACEMESH_CONTOURS,
                        None,
                        mp_drawing_styles.get_default_face_mesh_contours_style())
                    
                    # Get bounding rectangle
                    brect = draw_bounding_rect(frame, face_landmarks)
                    
                    # Process landmarks for classification
                    landmark_list = calc_landmark_list(frame, face_landmarks)
                    pre_processed_landmark_list = pre_process_landmark(landmark_list)
                    
                    # Classify emotion
                    try:
                        emotion_id, confidence = emotion_classifier(pre_processed_landmark_list)
                        emotion = EMOTIONS[emotion_id] if emotion_id < len(EMOTIONS) else "unknown"
                        
                        # Draw emotion information
                        frame = draw_info_text(frame, brect, emotion, confidence)
                        
                    except Exception as e:
                        print(f"Classification error: {e}")
                        emotion = "error"
                        confidence = 0.0
                        frame = draw_info_text(frame, brect, emotion, confidence)
            
            # Display FPS
            cv2.putText(frame, f"Press 'q' to quit", (10, frame.shape[0] - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            
            cv2.imshow('Facial Emotion Recognition', frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    
    vid.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
