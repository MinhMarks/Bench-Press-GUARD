import cv2

# Detector Settings
DETECTOR_TYPE = 'yolo'  # 'mediapipe' or 'yolo'
GPU_DEVICE = 'cuda:0'  # 'cuda:0', 'cuda:1', or 'cpu'
YOLO_MODEL_SIZE = 'm'  # 'n' (nano), 's' (small), 'm' (medium), 'l' (large), 'x' (xlarge)
VITPOSE_MODEL_PATH = 'checkpoints/vitpose-b.onnx'  # Legacy, kept for reference

# System Constraints
TARGET_FPS = 20
MAX_LATENCY_SEC = 0.5
BUFFER_SIZE_SEC = 10  # Store last 10 seconds of data for analysis

# Bench Colors for Multi-ROI (up to 6 benches)
BENCH_COLORS = [
    (0, 255, 100),    # Green
    (255, 165, 0),    # Orange  
    (0, 200, 255),    # Cyan
    (255, 0, 255),    # Magenta
    (255, 255, 0),    # Yellow
    (128, 0, 255)     # Purple
]

# Camera Settings
# Standard resolution requirement is > 256px ROI, but input can be 2MP (1920x1080)
CAMERA_WIDTH = 1920
CAMERA_HEIGHT = 1080
CAMERA_FPS = 30  # Hardware FPS (we process at 20)

# Detection Thresholds
DANGER_STALL_TIME = 5.0  # Seconds
TILT_THRESHOLD = 170.0  # Degrees - barbell tilt angle threshold
DANGER_SHAKE_PCT = 0.10  # 10% of shoulder width
DANGER_DROP_VELOCITY_THRESHOLD = 0.8  # Relative height per second
MIN_REPS_FOR_FATIGUE = 5
SPEED_DROP_THRESHOLD = 0.5  # Relative drop threshold
DANGER_LONG_BOTTOM_TIME = 7.0  # Seconds
DANGER_RECOVERY_ATTEMPTS = 2

# Consistency
STATE_CONSISTENCY_WINDOW = 0.5  # Seconds to suppress short changes

# ROI Defaults (normalized 0-1) - This would ideally be set via UI
DEFAULT_ROI = {
    "x": 0.2,
    "y": 0.1,
    "w": 0.6,
    "h": 0.8
}

VISUALIZATION_COLORS = {
    "NORMAL": (0, 255, 0),  # Green
    "DANGER": (0, 0, 255),  # Red
    "TEXT": (255, 255, 255)
}

# Keypoint Mappings
# MediaPipe Pose: 33 landmarks
MEDIAPIPE_LEFT_WRIST = 15
MEDIAPIPE_RIGHT_WRIST = 16
MEDIAPIPE_LEFT_SHOULDER = 11
MEDIAPIPE_RIGHT_SHOULDER = 12

# COCO/ViTPose: 17 keypoints
COCO_LEFT_WRIST = 9
COCO_RIGHT_WRIST = 10
COCO_LEFT_SHOULDER = 5
COCO_RIGHT_SHOULDER = 6
