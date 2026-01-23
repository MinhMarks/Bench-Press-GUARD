"""
Processing worker for running YOLO detection and analysis in background thread
"""
from PyQt6.QtCore import QThread, pyqtSignal
import numpy as np
import time

from core.detector_yolo import YOLOPoseDetector
from core.analyzer import BenchPressAnalyzer
from core.logger import FailureLogger
from config import TARGET_FPS, GPU_DEVICE, YOLO_MODEL_SIZE

class ProcessingWorker(QThread):
    """Background thread for pose detection and analysis"""
    
    # Signals
    results_ready = pyqtSignal(list)  # List of bench results
    fps_updated = pyqtSignal(float)  # FPS value
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.running = False
        self.current_frame = None
        self.rois = []
        
        # Initialize detector
        self.detector = None
        self.benches = []
        self.logger = FailureLogger()
        
        # FPS calculation
        self.prev_time = 0
        
        # Debug/visualization mode
        self.show_keypoints = False
        
    def set_show_keypoints(self, enabled):
        """Enable/disable keypoint visualization"""
        self.show_keypoints = enabled
        
    def set_rois(self, rois):
        """
        Set ROIs for processing
        
        Args:
            rois: List of normalized ROI dicts
        """
        self.rois = rois
        
        # Recreate benches
        self.benches = []
        for idx, roi in enumerate(rois):
            self.benches.append({
                'id': idx + 1,
                'roi': roi,
                'analyzer': BenchPressAnalyzer(fps=TARGET_FPS),
                'state': 'NORMAL',
                'reason': '',
                'fps': 0
            })
            
    def set_frame(self, frame):
        """Update current frame to process"""
        self.current_frame = frame.copy() if frame is not None else None
        
    def run(self):
        """Main processing loop"""
        self.running = True
        
        # Initialize YOLO detector
        try:
            print("[ProcessingWorker] Initializing YOLO detector...")
            self.detector = YOLOPoseDetector(model_size=YOLO_MODEL_SIZE, device=GPU_DEVICE)
            print("[ProcessingWorker] YOLO detector ready!")
        except Exception as e:
            print(f"[ProcessingWorker] Failed to initialize detector: {e}")
            return
        
        while self.running:
            if self.current_frame is None or len(self.benches) == 0:
                time.sleep(0.01)
                continue
            
            try:
                # Calculate FPS
                curr_time = time.time()
                if self.prev_time > 0:
                    fps = 1.0 / (curr_time - self.prev_time)
                    self.fps_updated.emit(fps)
                self.prev_time = curr_time
                
                # Process each bench
                frame = self.current_frame.copy()
                h, w = frame.shape[:2]
                
                results = []
                
                for bench in self.benches:
                    roi = bench['roi']
                    
                    # Extract ROI
                    r_x = int(roi['x'] * w)
                    r_y = int(roi['y'] * h)
                    r_w = int(roi['w'] * w)
                    r_h = int(roi['h'] * h)
                    
                    # Clamp
                    r_x = max(0, r_x)
                    r_y = max(0, r_y)
                    r_w = min(w - r_x, r_w)
                    r_h = min(h - r_y, r_h)
                    
                    if r_w <= 0 or r_h <= 0:
                        continue
                    
                    roi_img = frame[r_y:r_y+r_h, r_x:r_x+r_w]
                    
                    # Detect pose
                    self.detector.find_pose(roi_img, draw=False)
                    lm_list = self.detector.find_position(roi_img)
                    
                    # Analyze
                    if lm_list:
                        state, reason = bench['analyzer'].analyze(lm_list)
                        bench['state'] = state
                        bench['reason'] = reason
                        
                        # Log danger events
                        if state == "DANGER":
                            self.logger.log(bench['id'], state, reason, 0)
                    else:
                        bench['state'] = 'NO_POSE'
                        bench['reason'] = 'No person detected'
                    
                    # Collect result with keypoints if visualization enabled
                    result = {
                        'id': bench['id'],
                        'state': bench['state'],
                        'reason': bench['reason'],
                        'roi': roi
                    }
                    
                    if self.show_keypoints and lm_list:
                        result['keypoints'] = lm_list
                    
                    results.append(result)
                
                # Emit results
                self.results_ready.emit(results)
                
                # Throttle to target FPS
                time.sleep(1.0 / TARGET_FPS)
                
            except Exception as e:
                print(f"[ProcessingWorker] Error in processing loop: {e}")
                import traceback
                traceback.print_exc()
                time.sleep(0.1)
        
        print("[ProcessingWorker] Stopped")
        
    def stop(self):
        """Stop processing"""
        self.running = False
        self.wait()  # Wait for thread to finish
