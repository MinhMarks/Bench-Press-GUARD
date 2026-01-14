import math
import numpy as np

class Barbell:
    def __init__(self):
        self.exists = False
        self.left = None
        self.right = None
        self.midpoint = None
        self.width = 0
        
    def update(self, landmarks):
        """
        Updates barbell state from Pose landmarks.
        Expects landmarks dict/list with indices 15 (L) and 16 (R).
        """
        if not landmarks or len(landmarks) < 17:
            self.exists = False
            return False
            
        # Extract from dict or list
        # Assuming list format from detector: list of dicts with 'x', 'y' keys
        # Or dict of index -> dict
        
        # Detector returns list of dicts where index is implicitly position in list, 
        # but also has 'id' key. 
        # Let's handle list access safely.
        
        try:
            l_wrist = landmarks[15]
            r_wrist = landmarks[16]
            
            self.left = l_wrist
            self.right = r_wrist
            
            self.midpoint = {
                "x": (self.left['x'] + self.right['x']) / 2,
                "y": (self.left['y'] + self.right['y']) / 2
            }
            
            # Distance between wrists (Grip Width)
            dx = self.right['x'] - self.left['x']
            dy = self.right['y'] - self.left['y']
            self.width = math.sqrt(dx*dx + dy*dy)
            
            self.exists = True
            return True
            
        except (IndexError, KeyError):
            self.exists = False
            return False

    def get_tilt_angle(self):
        """Calculates absolute tilt angle in degrees."""
        if not self.exists: return 0.0
        
        dy = self.right['y'] - self.left['y']
        dx = self.right['x'] - self.left['x']
        
        angle = math.degrees(math.atan2(dy, dx))
        return abs(angle)

    def get_center_y(self):
        if not self.exists: return 0.0
        return self.midpoint['y']

    def get_center_x(self):
        if not self.exists: return 0.0
        return self.midpoint['x']
