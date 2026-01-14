import cv2

# System Constraints
TARGET_FPS = 20
MAX_LATENCY_SEC = 0.5
BUFFER_SIZE_SEC = 10  # Store last 10 seconds of data for analysis

# Camera Settings
# Standard resolution requirement is > 256px ROI, but input can be 2MP (1920x1080)
CAMERA_WIDTH = 1920
CAMERA_HEIGHT = 1080
CAMERA_FPS = 30  # Hardware FPS (we process at 20)

# Detection Thresholds
DANGER_STALL_TIME = 5.0  # Seconds
DANGER_TILT_ANGLE = 20.0  # Degrees
DANGER_SHAKE_PCT = 0.10  # 10% of shoulder width
DANGER_DROP_VELOCITY_THRESHOLD = 0.8  # Relative height per second (Needs tuning)
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
