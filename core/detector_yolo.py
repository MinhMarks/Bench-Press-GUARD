import cv2
import numpy as np
from ultralytics import YOLO
from typing import List, Dict, Optional

class YOLOPoseDetector:
    """
    YOLO11-Pose detector wrapper compatible with MediaPipe interface.
    Uses Ultralytics YOLO for pose estimation with GPU acceleration.
    """
    
    def __init__(self, model_size: str = 'm', device: str = 'cuda:0'):
        """
        Initialize YOLO11-Pose detector.
        
        Args:
            model_size: Model size - 'n' (nano), 's' (small), 'm' (medium), 'l' (large), 'x' (extra-large)
            device: 'cuda:0' for GPU, 'cpu' for CPU
        """
        self.model_size = model_size
        self.device = device
        
        # Model mapping
        model_name = f'yolo11{model_size}-pose.pt'
        
        print(f"[YOLO] Initializing YOLO11-Pose model: {model_name}")
        print(f"[YOLO] Device: {device}")
        
        # Load model (auto-downloads if not present)
        try:
            self.model = YOLO(model_name)
            print(f"[YOLO] Model loaded successfully")
        except Exception as e:
            print(f"[ERROR] Failed to load YOLO model: {e}")
            raise
        
        # COCO keypoint names (17 keypoints)
        self.keypoint_names = [
            'nose', 'left_eye', 'right_eye', 'left_ear', 'right_ear',
            'left_shoulder', 'right_shoulder', 'left_elbow', 'right_elbow',
            'left_wrist', 'right_wrist', 'left_hip', 'right_hip',
            'left_knee', 'right_knee', 'left_ankle', 'right_ankle'
        ]
        
        # Keypoint IDs for barbell detection (COCO format)
        self.LEFT_WRIST_ID = 9
        self.RIGHT_WRIST_ID = 10
        self.LEFT_SHOULDER_ID = 5
        self.RIGHT_SHOULDER_ID = 6
        
        self.results = None
        
    def find_pose(self, img: np.ndarray, draw: bool = False) -> np.ndarray:
        """
        Run pose estimation on image.
        
        Args:
            img: Input image BGR format
            draw: Whether to draw keypoints on image
            
        Returns:
            img: Image (with keypoints drawn if draw=True)
        """
        # Run inference
        self.results = self.model(img, device=self.device, verbose=False)[0]
        
        # Draw if requested
        if draw and self.results.keypoints is not None:
            img_annotated = self.results.plot()
            return img_annotated
        
        return img
    
    def find_position(self, img: np.ndarray) -> List[Dict]:
        """
        Extract landmarks compatible with MediaPipe format.
        
        Args:
            img: Input image (used for shape reference)
            
        Returns:
            lm_list: List of landmark dicts with same format as MediaPipe
        """
        if self.results is None or self.results.keypoints is None:
            return []
        
        lm_list = []
        h, w = img.shape[:2]
        
        # Get keypoints (shape: [num_people, num_keypoints, 2 or 3])
        keypoints = self.results.keypoints.xy.cpu().numpy()  # [x, y] coordinates
        
        # For single-person detection, use first person
        if len(keypoints) == 0:
            return []
        
        person_keypoints = keypoints[0]  # Shape: [17, 2]
        
        # Get confidence scores if available
        if self.results.keypoints.conf is not None:
            confidences = self.results.keypoints.conf.cpu().numpy()[0]  # Shape: [17]
        else:
            confidences = np.ones(17)  # Default confidence
        
        for idx, (kp, conf) in enumerate(zip(person_keypoints, confidences)):
            x_px, y_px = kp
            
            lm_list.append({
                "id": idx,
                "x_px": int(x_px),
                "y_px": int(y_px),
                "x": x_px / w,
                "y": y_px / h,
                "visibility": float(conf)
            })
        
        return lm_list
    
    def get_barbell_landmarks(self, lm_list: List[Dict]) -> Optional[Dict]:
        """
        Extract barbell position from wrists (COCO format).
        
        Args:
            lm_list: Landmark list from find_position()
            
        Returns:
            Dict with 'left', 'right', 'midpoint' or None
        """
        if not lm_list or len(lm_list) < 17:
            return None
        
        # COCO keypoints: 9=left_wrist, 10=right_wrist
        left_wrist = lm_list[self.LEFT_WRIST_ID]
        right_wrist = lm_list[self.RIGHT_WRIST_ID]
        
        # Check visibility (YOLO uses confidence scores)
        if left_wrist['visibility'] < 0.3 or right_wrist['visibility'] < 0.3:
            return None
        
        # Calculate midpoint
        mid_x = (left_wrist['x'] + right_wrist['x']) / 2
        mid_y = (left_wrist['y'] + right_wrist['y']) / 2
        
        return {
            "left": left_wrist,
            "right": right_wrist,
            "midpoint": {"x": mid_x, "y": mid_y}
        }
