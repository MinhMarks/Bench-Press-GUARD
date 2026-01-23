import time
import sys
import os
import math
import numpy as np

# Add parent dir to path to allow imports if run directly
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from config import *
from core.temporal_buffer import TemporalBuffer
from utils.geometry import calculate_horizontal_tilt, calculate_distance

from core.barbell import Barbell

class BenchPressAnalyzer:
    def __init__(self, fps=TARGET_FPS):
        self.fps = fps
        self.history = TemporalBuffer(maxlen=int(BUFFER_SIZE_SEC * fps))
        self.state = "NORMAL"
        self.last_state_change = 0
        self.danger_reason = ""
        
        self.barbell = Barbell()
        
    def analyze(self, landmarks, timestamp=None):
        """
        Analyzes the current frame landmarks to determine state.
        Returns (state, reason, metrics).
        """
        current_time = timestamp if timestamp is not None else time.time()
        
        if not landmarks:
            return self.update_state("NORMAL", "No Detection", current_time)

        # Update Barbell State
        if not self.barbell.update(landmarks):
             return self.update_state("NORMAL", "No Barbell", current_time)
            
        current_data = {
            "time": current_time,
            "y": self.barbell.get_center_y(),
            "x": self.barbell.get_center_x(),
            "tilt": self.barbell.get_tilt_angle()
        }
        
        self.history.add(current_data)
        
        # 1. Check Loss of Stability (Immediate)
        if current_data['tilt'] > TILT_THRESHOLD:
            return self.update_state("DANGER", f"Unstable: Tilt {current_data['tilt']:.1f} > {TILT_THRESHOLD}", current_time)
            
        # Check X-axis Shake (last 1 sec)
        shake = self._calculate_shake(1.0)
        
        # Use Barbell Grip Width or Shoulder Width?
        # User prompt suggested we weren't "using the barbell". 
        # Using Barbell Width as reference is valid physics (shake relative to length of bar). 
        # But shoulder width is safer if grip is narrow. 
        # Let's use Barbell Width (Grip Width) if available, it's more direct.
        # However, narrow grip bench press exists. 
        # Let's Stick to Shoulder width for now but maybe factor in barbell?
        # Actually let's use the Barbell width property we just made.
        ref_width = self.barbell.width if self.barbell.width > 0.1 else 0.5 # fallback
        
        # Or better stick to shoulders as per original logic to avoid breaking change in logic behavior?
        # Let's use shoulders to be safe unless user insists.
        shoulder_width = abs(landmarks[11]['x'] - landmarks[12]['x'])
        
        if shake > (shoulder_width * DANGER_SHAKE_PCT):
            return self.update_state("DANGER", f"Unstable: Shake {shake:.3f} > {shoulder_width*DANGER_SHAKE_PCT:.3f}", current_time)

        # 2. Check Uncontrolled Drop (Velocity based)
        velocity = self.history.get_average_velocity(0.5, self.fps)
        if velocity > DANGER_DROP_VELOCITY_THRESHOLD: 
             return self.update_state("DANGER", f"Drop detected: Vel {velocity:.2f}", current_time)

        # 3. Check Stalled Barbell
        if current_data['y'] > 0.4: # Below the top area
            if self.history.is_stagnant(DANGER_STALL_TIME, self.fps, threshold=0.03):
                 return self.update_state("DANGER", "Stalled: No motion > 5s", current_time)

        # 4. Check Prolonged Bottom Position
        if current_data['y'] > 0.6: # Deep in press
             if self.history.is_stagnant(DANGER_LONG_BOTTOM_TIME, self.fps, threshold=0.1):
                 return self.update_state("DANGER", "Prolonged Bottom Position > 7s", current_time)
        
        return self.update_state("NORMAL", "", current_time)

    def update_state(self, new_state, reason, timestamp=None):
        now = timestamp if timestamp is not None else time.time()
        
        # Consistency Filter
        if new_state != self.state:
            if (now - self.last_state_change) > STATE_CONSISTENCY_WINDOW:
                self.state = new_state
                self.danger_reason = reason
                self.last_state_change = now
        else:
            if new_state == "DANGER":
                self.danger_reason = reason
                
        return self.state, self.danger_reason

    def _extract_barbell(self, lm_list):
        # Legacy support: used by main.py for visualization
        # We can just return dict from self.barbell if current
        if self.barbell.exists:
            return {
                "left": self.barbell.left,
                "right": self.barbell.right,
                "midpoint": self.barbell.midpoint
            }
        return None

    def _calculate_shake(self, seconds):
        """Calculate variance in X over time."""
        data = self.history.get_last(seconds, self.fps)
        if not data: return 0
        xs = [d['x'] for d in data]
        return np.std(xs) # Standard deviation as metric for shake
