import cv2
import mediapipe as mp
import numpy as np

class PoseDetector:
    def __init__(self, mode=False, complexity=1, smooth=True, detection_con=0.5, track_con=0.5):
        self.mode = mode
        self.complexity = complexity
        self.smooth = smooth
        self.detection_con = detection_con
        self.track_con = track_con

        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            static_image_mode=self.mode,
            model_complexity=self.complexity,
            smooth_landmarks=self.smooth,
            min_detection_confidence=self.detection_con,
            min_tracking_confidence=self.track_con
        )
        self.mp_draw = mp.solutions.drawing_utils

    def find_pose(self, img, draw=True):
        """Processes the image and finds the pose."""
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.results = self.pose.process(img_rgb)
        
        if draw and self.results.pose_landmarks:
            self.mp_draw.draw_landmarks(img, self.results.pose_landmarks, self.mp_pose.POSE_CONNECTIONS)
        return img

    def find_position(self, img):
        """Extracts landmarks and returns a list of coordinates."""
        lm_list = []
        if self.results.pose_landmarks:
            h, w, c = img.shape
            for id, lm in enumerate(self.results.pose_landmarks.landmark):
                cx, cy = int(lm.x * w), int(lm.y * h)
                # We store normalized coordinates as well for easier logic
                lm_list.append({
                    "id": id,
                    "x_px": cx, 
                    "y_px": cy,
                    "x": lm.x,
                    "y": lm.y,
                    "visibility": lm.visibility
                })
        return lm_list

    def get_barbell_landmarks(self, lm_list):
        """
        Approximates barbell position using wrists.
        Returns dict with left_wrist, right_wrist, and midpoint.
        """
        if not lm_list or len(lm_list) < 17:
            return None
            
        # 15: Left Wrist, 16: Right Wrist
        left_wrist = lm_list[15]
        right_wrist = lm_list[16]
        
        # Midpoint
        mid_x = (left_wrist['x'] + right_wrist['x']) / 2
        mid_y = (left_wrist['y'] + right_wrist['y']) / 2
        
        return {
            "left": left_wrist,
            "right": right_wrist,
            "midpoint": {"x": mid_x, "y": mid_y}
        }
