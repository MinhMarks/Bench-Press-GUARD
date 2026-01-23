"""
Camera widget for displaying video feed
"""
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QImage, QPixmap
import cv2
import numpy as np

class CameraWidget(QWidget):
    """Widget to display camera/video feed"""
    
    frame_ready = pyqtSignal(np.ndarray)  # Signal when new frame is available
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.camera = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        
        # ROI overlay
        self.rois = []  # List of normalized ROI dicts
        self.roi_colors = []  # List of colors
        self.danger_mode = False  # Danger flash mode
        self.flash_alpha = 0  # Flash animation
        
        # PIP mode
        self.pip_mode = False
        self.danger_rois = []  # List of ROIs in danger state
        self.current_danger_index = 0  # Which danger ROI to show
        self.last_pip_switch = 0  # Time of last ROI switch
        self.pip_switch_interval = 3.0  # Seconds between ROI switches
        
        # Keypoint visualization
        self.show_keypoints = False
        self.current_keypoints = {}  # {roi_index: keypoints_list}
        
        self.init_ui()
        
    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Video display label
        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setStyleSheet("background-color: #000000;")
        self.video_label.setScaledContents(True)
        
        # Show placeholder
        self.show_placeholder()
        
        layout.addWidget(self.video_label)
        
    def show_placeholder(self):
        """Show placeholder when no video"""
        # Create blank image
        placeholder = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.putText(placeholder, "No Video Source", 
                   (150, 240), cv2.FONT_HERSHEY_SIMPLEX, 
                   1.2, (100, 100, 100), 2)
        cv2.putText(placeholder, "Select a camera or video file to begin", 
                   (80, 280), cv2.FONT_HERSHEY_SIMPLEX, 
                   0.7, (80, 80, 80), 1)
        
        self.display_frame(placeholder)
        
    def start_camera(self, source):
        """
        Start camera/video capture
        
        Args:
            source: Camera index (int) or video file path (str)
            
        Returns:
            bool: True if successful
        """
        try:
            # Stop existing camera
            if self.camera is not None:
                self.stop_camera()
            
            # Open camera/video
            self.camera = cv2.VideoCapture(source)
            
            if not self.camera.isOpened():
                return False
            
            # Set resolution for cameras
            if isinstance(source, int):
                self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
                self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            
            # Start timer (30 FPS)
            self.timer.start(33)
            
            return True
            
        except Exception as e:
            print(f"Error starting camera: {e}")
            return False
            
    def stop_camera(self):
        """Stop camera capture"""
        self.timer.stop()
        
        if self.camera is not None:
            self.camera.release()
            self.camera = None
        
        # Clear all overlays before showing placeholder
        self.rois = []
        self.roi_colors = []
        self.pip_mode = False
        self.danger_rois = []
            
        self.show_placeholder()
        
    def update_frame(self):
        """Read and display next frame"""
        if self.camera is None or not self.camera.isOpened():
            return
            
        ret, frame = self.camera.read()
        
        if ret:
            # Emit signal for processing
            self.frame_ready.emit(frame.copy())
            
            # Display frame
            self.display_frame(frame)
        else:
            # Video ended - loop or show placeholder
            if isinstance(self.camera, cv2.VideoCapture):
                # Try to loop video
                self.camera.set(cv2.CAP_PROP_POS_FRAMES, 0)
                
                
    def display_frame(self, frame):
        """
        Display frame on label with ROI overlays and PIP mode
        
        Args:
            frame: numpy array (BGR)
        """
        # Store full frame for PIP
        full_frame_backup = frame.copy()
        
        # PIP Mode: Zoom to danger ROI
        if self.pip_mode and self.danger_rois:
            import time
            
            # Auto-cycle through danger ROIs
            current_time = time.time()
            if current_time - self.last_pip_switch > self.pip_switch_interval:
                self.current_danger_index = (self.current_danger_index + 1) % len(self.danger_rois)
                self.last_pip_switch = current_time
            
            # Get current danger ROI to display
            danger_roi = self.danger_rois[self.current_danger_index]
            roi_idx = danger_roi['index']
            roi_data = danger_roi['roi']
            
            h, w = frame.shape[:2]
            
            # Extract zoomed ROI
            x = int(roi_data['x'] * w)
            y = int(roi_data['y'] * h)
            roi_w = int(roi_data['w'] * w)
            roi_h = int(roi_data['h'] * h)
            
            # Clamp
            x = max(0, min(x, w - roi_w))
            y = max(0, min(y, h - roi_h))
            
            if roi_w > 0 and roi_h > 0:
                zoomed = frame[y:y+roi_h, x:x+roi_w].copy()
                
                # Resize zoomed to match frame size
                zoomed = cv2.resize(zoomed, (w, h))
                
                # Add DANGER header
                header_text = f"DANGER - Bench #{roi_idx + 1}"
                if len(self.danger_rois) > 1:
                    header_text += f" ({self.current_danger_index + 1}/{len(self.danger_rois)})"
                
                cv2.putText(zoomed, header_text, 
                           (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 
                           1.2, (0, 0, 255), 3)
                
                # Add PIP (picture-in-picture) of full view in corner
                pip_h = h // 4
                pip_w = w // 4
                pip_thumbnail = cv2.resize(full_frame_backup, (pip_w, pip_h))
                
                # Draw ROI overlays on PIP thumbnail
                if self.rois:
                    for idx, roi in enumerate(self.rois):
                        # Convert normalized to pixel coordinates (for thumbnail)
                        pip_x_roi = int(roi['x'] * pip_w)
                        pip_y_roi = int(roi['y'] * pip_h)
                        pip_roi_w = int(roi['w'] * pip_w)
                        pip_roi_h = int(roi['h'] * pip_h)
                        
                        # Get color
                        color = self.roi_colors[idx] if idx < len(self.roi_colors) else (0, 255, 100)
                        
                        # Scale border thickness for small thumbnail (1 pixel)
                        border_thickness = 1
                        
                        # Draw rectangle on thumbnail
                        cv2.rectangle(pip_thumbnail, 
                                     (pip_x_roi, pip_y_roi), 
                                     (pip_x_roi + pip_roi_w, pip_y_roi + pip_roi_h), 
                                     color, border_thickness)
                        
                        # Highlight currently zoomed ROI with slightly thicker border
                        if idx == roi_idx:
                            cv2.rectangle(pip_thumbnail, 
                                         (pip_x_roi, pip_y_roi), 
                                         (pip_x_roi + pip_roi_w, pip_y_roi + pip_roi_h), 
                                         (255, 255, 255), 2)
                
                # Draw PIP border
                cv2.rectangle(pip_thumbnail, (0, 0), (pip_w-1, pip_h-1), (255, 255, 255), 3)
                
                # Place PIP in top-right corner
                pip_x = w - pip_w - 20
                pip_y = 20
                zoomed[pip_y:pip_y+pip_h, pip_x:pip_x+pip_w] = pip_thumbnail
                
                # Use zoomed frame
                frame = zoomed
        
        # Draw ROI overlays (on normal or zoomed frame)
        # Only draw if NOT in PIP mode (to avoid overlays on zoomed view)
        if self.rois and not self.pip_mode:
            h, w = frame.shape[:2]
            for idx, roi in enumerate(self.rois):
                # Convert normalized to pixel coordinates
                x = int(roi['x'] * w)
                y = int(roi['y'] * h)
                roi_w = int(roi['w'] * w)
                roi_h = int(roi['h'] * h)
                
                # Get color
                color = self.roi_colors[idx] if idx < len(self.roi_colors) else (0, 255, 100)
                
                # Draw rectangle
                cv2.rectangle(frame, (x, y), (x + roi_w, y + roi_h), color, 3)
                
                # Draw label
                label = f"Bench #{idx + 1}"
                (text_w, text_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
                cv2.rectangle(frame, (x, y - 30), (x + text_w + 10, y), color, -1)
                cv2.putText(frame, label, (x + 5, y - 8),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                
                # Draw keypoints if enabled
                if self.show_keypoints and idx in self.current_keypoints:
                    self._draw_keypoints_in_roi(frame, self.current_keypoints[idx], roi)
        
        # Danger flash overlay
        if self.danger_mode:
            import math
            import time
            # Pulsing effect
            self.flash_alpha = (math.sin(time.time() * 5) + 1) / 2  # 0 to 1
            overlay = frame.copy()
            cv2.rectangle(overlay, (0, 0), (frame.shape[1], frame.shape[0]), (0, 0, 255), -1)
            cv2.addWeighted(frame, 1, overlay, self.flash_alpha * 0.2, 0, frame)
        
        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        h, w, ch = rgb_frame.shape
        bytes_per_line = ch * w
        
        # Convert to QImage
        qt_image = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        
        # Scale to label size while maintaining aspect ratio
        pixmap = QPixmap.fromImage(qt_image)
        scaled_pixmap = pixmap.scaled(
            self.video_label.size(), 
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        
        self.video_label.setPixmap(scaled_pixmap)
        
    def resizeEvent(self, event):
        """Handle resize event"""
        super().resizeEvent(event)
        # Re-scale current pixmap
        if self.video_label.pixmap() is not None:
            # Trigger frame update to rescale
            pass
    
    def set_rois(self, rois, colors):
        """
        Set ROIs to display on video
        
        Args:
            rois: List of normalized ROI dicts
            colors: List of (B, G, R) tuples
        """
        self.rois = rois
        self.roi_colors = colors
    
    def set_danger_mode(self, enabled):
        """Enable/disable danger flash overlay"""
        self.danger_mode = enabled
    
    def set_pip_mode(self, enabled, danger_rois=None):
        """
        Enable/disable PIP mode with danger ROIs
        
        Args:
            enabled: bool
            danger_rois: List of dicts with 'index' and 'roi' keys
        """
        import time
        self.pip_mode = enabled
        if enabled and danger_rois:
            self.danger_rois = danger_rois
            self.current_danger_index = 0
            self.last_pip_switch = time.time()
        else:
            self.danger_rois = []
    
    def _draw_keypoints_in_roi(self, frame, keypoints, roi):
        """
        Draw COCO keypoints and skeleton within ROI
        
        Args:
            frame: Frame to draw on
            keypoints: List of keypoint dicts with x, y, visibility
            roi: ROI dict with normalized coordinates
        """
        h, w = frame.shape[:2]
        
        # ROI offset
        roi_x = int(roi['x'] * w)
        roi_y = int(roi['y'] * h)
        roi_w = int(roi['w'] * w)
        roi_h = int(roi['h'] * h)
        
        # COCO skeleton connections
        skeleton = [
            (0, 1), (0, 2),  # Nose to eyes
            (1, 3), (2, 4),  # Eyes to ears
            (0, 5), (0, 6),  # Nose to shoulders
            (5, 7), (7, 9),  # Left arm
            (6, 8), (8, 10), # Right arm
            (5, 6),          # Shoulders
            (5, 11), (6, 12), # Shoulders to hips
            (11, 12),        # Hips
            (11, 13), (13, 15), # Left leg
            (12, 14), (14, 16)  # Right leg
        ]
        
        # Draw skeleton lines
        for conn in skeleton:
            if conn[0] < len(keypoints) and conn[1] < len(keypoints):
                pt1 = keypoints[conn[0]]
                pt2 = keypoints[conn[1]]
                
                if pt1.get('visibility', 0) > 0.5 and pt2.get('visibility', 0) > 0.5:
                    x1 = int(roi_x + pt1['x'] * roi_w)
                    y1 = int(roi_y + pt1['y'] * roi_h)
                    x2 = int(roi_x + pt2['x'] * roi_w)
                    y2 = int(roi_y + pt2['y'] * roi_h)
                    
                    cv2.line(frame, (x1, y1), (x2, y2), (0, 255, 255), 2)
        
        # Draw keypoints
        for kp in keypoints:
            if kp.get('visibility', 0) > 0.5:
                x = int(roi_x + kp['x'] * roi_w)
                y = int(roi_y + kp['y'] * roi_h)
                cv2.circle(frame, (x, y), 4, (0, 0, 255), -1)
                cv2.circle(frame, (x, y), 6, (255, 255, 255), 1)
    
    def set_keypoints(self, keypoints_dict):
        """
        Set keypoints to visualize
        
        Args:
            keypoints_dict: {roi_index: keypoints_list}
        """
        self.current_keypoints = keypoints_dict
    
    def set_show_keypoints(self, enabled):
        """Enable/disable keypoint visualization"""
        self.show_keypoints = enabled
