"""
Hand Gesture Recognition using MediaPipe Hand Landmarks

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
GESTURES = ["thumbs_up", "peace_sign", "closed_fist", "open_palm"]

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

def calc_landmark_list(image, landmarks):
    """Convert MediaPipe hand landmarks to coordinate list"""
    image_width, image_height = image.shape[1], image.shape[0]
    landmark_point = []
    
    for landmark in landmarks.landmark:
        landmark_x = min(int(landmark.x * image_width), image_width - 1)
        landmark_y = min(int(landmark.y * image_height), image_height - 1)
        landmark_point.append([landmark_x, landmark_y])
    
    return landmark_point

def pre_process_landmark(landmark_list):
    """Normalize hand landmark coordinates"""
    temp_landmark_list = np.array(landmark_list, dtype=np.float32)
    
    base_x, base_y = temp_landmark_list[0][0], temp_landmark_list[0][1]
    temp_landmark_list[:, 0] = temp_landmark_list[:, 0] - base_x
    temp_landmark_list[:, 1] = temp_landmark_list[:, 1] - base_y
    
    temp_landmark_list = temp_landmark_list.flatten()
    max_value = max(list(map(abs, temp_landmark_list)))
    
    if max_value == 0:
        return temp_landmark_list.tolist()
    
    def normalize_(n):
        return n / max_value
    
    temp_landmark_list = list(map(normalize_, temp_landmark_list))
    
    return temp_landmark_list

def draw_bounding_rect(image, landmarks):
    """Draw bounding rectangle around hand"""
    image_width, image_height = image.shape[1], image.shape[0]
    
    landmark_array = np.empty((0, 2), int)
    for landmark in landmarks.landmark:
        landmark_x = min(int(landmark.x * image_width), image_width - 1)
        landmark_y = min(int(landmark.y * image_height), image_height - 1)
        landmark_point = [np.array((landmark_x, landmark_y))]
        landmark_array = np.append(landmark_array, landmark_point, axis=0)
    
    x, y, w, h = cv2.boundingRect(landmark_array)
    
    return x, y, x + w, y + h

def draw_info_text(image, brect, gesture, confidence):
    """Draw gesture information on image"""
    cv2.rectangle(image, (brect[0], brect[1]), (brect[2], brect[1] - 22), (0, 0, 0), -1)
    
    info_text = f'{gesture}: {confidence:.2f}'
    cv2.putText(image, info_text, (brect[0] + 5, brect[1] - 4),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)
    
    return image

def main():
    try:
        gesture_classifier = KeyPointClassifier(
            model_path='./models/gesture_classifier.tflite'
        )
        print("Gesture classifier loaded successfully!")
    except Exception as e:
        print(f"Error loading gesture classifier: {e}")
        print("Please train the model first by running train_keypoints.py")
        return
    
    vid = cv2.VideoCapture(CAMERA_INDEX)
    vid.set(cv2.CAP_PROP_FRAME_WIDTH, 960)
    vid.set(cv2.CAP_PROP_FRAME_HEIGHT, 540)
    
    if not vid.isOpened():
        print("Error: Could not open camera")
        return
    
    print("Starting hand gesture recognition...")
    print("Press 'q' to quit")
    
    with mp_hands.Hands(
        max_num_hands=1,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.5) as hands:
        
        while True:
            ret, frame = vid.read()
            if not ret:
                break
            
            frame = cv2.flip(frame, 1)
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            results = hands.process(frame_rgb)
            
            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    mp_drawing.draw_landmarks(
                        frame,
                        hand_landmarks,
                        mp_hands.HAND_CONNECTIONS,
                        mp_drawing_styles.get_default_hand_landmarks_style(),
                        mp_drawing_styles.get_default_hand_connections_style())
                    
                    brect = draw_bounding_rect(frame, hand_landmarks)
                    
                    landmark_list = calc_landmark_list(frame, hand_landmarks)
                    pre_processed_landmark_list = pre_process_landmark(landmark_list)
                    
                    try:
                        gesture_id, confidence = gesture_classifier(pre_processed_landmark_list)
                        gesture = GESTURES[gesture_id] if gesture_id < len(GESTURES) else "unknown"
                        
                        frame = draw_info_text(frame, brect, gesture, confidence)
                        
                    except Exception as e:
                        print(f"Classification error: {e}")
                        gesture = "error"
                        confidence = 0.0
                        frame = draw_info_text(frame, brect, gesture, confidence)
            
            cv2.putText(frame, f"Press 'q' to quit", (10, frame.shape[0] - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            
            cv2.imshow('Hand Gesture Recognition', frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    
    vid.release()
    cv2.destroyAllWindows()



if __name__ == "__main__":
    main()