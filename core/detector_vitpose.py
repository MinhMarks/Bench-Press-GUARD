import cv2
import numpy as np
import onnxruntime as ort
from typing import List, Dict, Tuple, Optional

class ViTPoseDetector:
    """
    ViTPose detector using ONNX Runtime for GPU inference.
    Avoids MMCV compilation issues on Windows.
    """
    
    def __init__(self, model_path: str = "checkpoints/vitpose-b.onnx", device: str = 'cuda:0'):
        """
        Initialize ViTPose detector with ONNX model.
        
        Args:
            model_path: Path to ONNX model file
            device: 'cuda:0' for GPU, 'cpu' for CPU
        """
        self.model_path = model_path
        self.device = device
        
        # Setup ONNX Runtime providers
        providers = []
        if 'cuda' in device.lower():
            providers.append(('CUDAExecutionProvider', {
                'device_id': int(device.split(':')[1]) if ':' in device else 0,
            }))
        providers.append('CPUExecutionProvider')
        
        print(f"[ViTPose] Initializing with providers: {providers}")
        
        # Load ONNX model
        try:
            self.session = ort.InferenceSession(model_path, providers=providers)
            self.input_name = self.session.get_inputs()[0].name
            self.input_shape = self.session.get_inputs()[0].shape  # Usually [1, 3, 256, 192]
            print(f"[ViTPose] Model loaded successfully. Input shape: {self.input_shape}")
        except Exception as e:
            print(f"[ERROR] Failed to load ONNX model: {e}")
            print(f"[INFO] Please download ViTPose ONNX model first!")
            raise
        
        # COCO keypoint names (17 keypoints)
        self.keypoint_names = [
            'nose', 'left_eye', 'right_eye', 'left_ear', 'right_ear',
            'left_shoulder', 'right_shoulder', 'left_elbow', 'right_elbow',
            'left_wrist', 'right_wrist', 'left_hip', 'right_hip',
            'left_knee', 'right_knee', 'left_ankle', 'right_ankle'
        ]
        
        # Keypoint IDs for barbell detection
        self.LEFT_WRIST_ID = 9
        self.RIGHT_WRIST_ID = 10
        self.LEFT_SHOULDER_ID = 5
        self.RIGHT_SHOULDER_ID = 6
        
        self.results = None
        
    def preprocess(self, img: np.ndarray) -> Tuple[np.ndarray, float, Tuple[int, int]]:
        """
        Preprocess image for ViTPose model.
        
        Args:
            img: Input image (H, W, 3) BGR format
            
        Returns:
            preprocessed: Model input (1, 3, 256, 192)
            scale: Scale factor used
            center: Center point of transformation
        """
        h, w = img.shape[:2]
        target_h, target_w = self.input_shape[2], self.input_shape[3]  # 256, 192
        
        # Calculate scale to fit image into model input
        scale = min(target_w / w, target_h / h)
        
        # Resize image
        new_w = int(w * scale)
        new_h = int(h * scale)
        resized = cv2.resize(img, (new_w, new_h))
        
        # Pad to target size
        pad_w = (target_w - new_w) // 2
        pad_h = (target_h - new_h) // 2
        
        padded = np.zeros((target_h, target_w, 3), dtype=np.uint8)
        padded[pad_h:pad_h+new_h, pad_w:pad_w+new_w] = resized
        
        # Convert BGR to RGB and normalize
        rgb = cv2.cvtColor(padded, cv2.COLOR_BGR2RGB)
        normalized = rgb.astype(np.float32) / 255.0
        
        # Normalize with ImageNet mean/std
        mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
        std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
        normalized = (normalized - mean) / std
        
        # Transpose to (C, H, W) and add batch dimension
        transposed = normalized.transpose(2, 0, 1)[np.newaxis, ...]
        
        center = (w // 2, h // 2)
        return transposed, scale, center
        
    def postprocess(self, heatmaps: np.ndarray, scale: float, orig_shape: Tuple[int, int]) -> np.ndarray:
        """
        Convert heatmaps to keypoints.
        
        Args:
            heatmaps: Model output heatmaps (1, 17, H, W)
            scale: Scale factor from preprocessing
            orig_shape: Original image (h, w)
            
        Returns:
            keypoints: (17, 3) array [x, y, confidence]
        """
        num_keypoints = heatmaps.shape[1]
        heatmap_h, heatmap_w = heatmaps.shape[2:4]
        
        keypoints = []
        for i in range(num_keypoints):
            heatmap = heatmaps[0, i, :, :]
            
            # Find max confidence location
            max_val = np.max(heatmap)
            max_idx = np.argmax(heatmap)
            y, x = np.unravel_index(max_idx, heatmap.shape)
            
            # Convert heatmap coordinates to original image coordinates
            # Account for preprocessing padding and scaling
            target_h, target_w = self.input_shape[2], self.input_shape[3]
            
            # Convert from heatmap space to input image space
            scale_factor = target_w / heatmap_w
            x_img = x * scale_factor
            y_img = y * scale_factor
            
            # Remove padding offset
            orig_h, orig_w = orig_shape
            pad_w = (target_w - int(orig_w * scale)) // 2
            pad_h = (target_h - int(orig_h * scale)) // 2
            
            x_img = (x_img - pad_w) / scale
            y_img = (y_img - pad_h) / scale
            
            keypoints.append([x_img, y_img, float(max_val)])
        
        return np.array(keypoints)
    
    def find_pose(self, img: np.ndarray, draw: bool = False) -> np.ndarray:
        """
        Run pose estimation on image.
        
        Args:
            img: Input image BGR format
            draw: Whether to draw keypoints (not implemented for ONNX)
            
        Returns:
            img: Same image (drawing not implemented)
        """
        # Store original shape
        self.orig_shape = img.shape[:2]
        
        # Preprocess
        input_tensor, self.scale, self.center = self.preprocess(img)
        
        # Run inference
        outputs = self.session.run(None, {self.input_name: input_tensor.astype(np.float32)})
        heatmaps = outputs[0]  # Heatmaps (1, 17, H, W)
        
        # Postprocess to get keypoints
        self.keypoints = self.postprocess(heatmaps, self.scale, self.orig_shape)
        
        # Store results in similar format to MediaPipe
        self.results = {'keypoints': self.keypoints}
        
        return img
    
    def find_position(self, img: np.ndarray) -> List[Dict]:
        """
        Extract landmarks compatible with MediaPipe format.
        
        Args:
            img: Input image (used for shape reference)
            
        Returns:
            lm_list: List of landmark dicts with same format as MediaPipe
        """
        if self.results is None or 'keypoints' not in self.results:
            return []
        
        lm_list = []
        h, w = img.shape[:2]
        
        for idx, (x, y, conf) in enumerate(self.keypoints):
            lm_list.append({
                "id": idx,
                "x_px": int(x),
                "y_px": int(y),
                "x": x / w,
                "y": y / h,
                "visibility": conf
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
        
        # Check visibility
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
