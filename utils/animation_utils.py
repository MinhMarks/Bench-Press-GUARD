import cv2
import numpy as np
import time
import math

class DangerAnimator:
    """
    Handles animated effects for danger states.
    """
    
    def __init__(self):
        self.pulse_phase = 0
        self.shake_phase = 0
        self.alert_active = False
        self.last_alert_time = 0
        
    def animate_danger_pulse(self, img, roi, intensity=0.3):
        """
        Create pulsing red overlay for danger state.
        
        Args:
            img: Image to apply effect to
            roi: Region dict {x, y, w, h} normalized
            intensity: Max alpha intensity
        
        Returns:
            Modified image
        """
        h_img, w_img, _ = img.shape
        
        x = int(roi['x'] * w_img)
        y = int(roi['y'] * h_img)
        w = int(roi['w'] * w_img)
        h = int(roi['h'] * h_img)
        
        # Update pulse phase
        self.pulse_phase = (self.pulse_phase + 0.15) % (2 * math.pi)
        
        # Calculate alpha (pulsing between 0 and intensity)
        alpha = intensity * (0.5 + 0.5 * math.sin(self.pulse_phase))
        
        # Create red overlay
        overlay = img.copy()
        cv2.rectangle(overlay, (x, y), (x + w, y + h), (0, 0, 255), -1)
        
        # Blend
        cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0, img)
        
        return img
    
    def animate_shake(self, img, roi):
        """
        Create shake effect for critical warnings.
        
        Args:
            img: Image
            roi: Region dict
        
        Returns:
            Shake offset (dx, dy)
        """
        self.shake_phase = (self.shake_phase + 0.5) % (2 * math.pi)
        
        # Random shake within small range
        shake_amplitude = 8
        dx = int(shake_amplitude * math.sin(self.shake_phase * 3))
        dy = int(shake_amplitude * math.cos(self.shake_phase * 2))
        
        return dx, dy
    
    def reset(self):
        """Reset animation state."""
        self.pulse_phase = 0
        self.shake_phase = 0

class StateTransition:
    """
    Smooth color transitions between states.
    """
    
    def __init__(self):
        self.current_color = np.array([0, 255, 0], dtype=np.float32)  # Green
        self.target_color = np.array([0, 255, 0], dtype=np.float32)
        self.transition_speed = 0.15
        
    def update(self, target_state):
        """
        Update color based on target state.
        
        Args:
            target_state: 'NORMAL' or 'DANGER'
        
        Returns:
            Current color as tuple (B, G, R)
        """
        if target_state == "DANGER":
            self.target_color = np.array([0, 0, 255], dtype=np.float32)  # Red
        else:
            self.target_color = np.array([0, 255, 0], dtype=np.float32)  # Green
        
        # Lerp to target color
        self.current_color += (self.target_color - self.current_color) * self.transition_speed
        
        return tuple(self.current_color.astype(int))

class FadeTransition:
    """
    Fade in/out effects for UI elements.
    """
    
    def __init__(self, duration=1.0):
        self.duration = duration
        self.alpha = 0.0
        self.start_time = None
        self.fading_in = True
        
    def start_fade_in(self):
        """Start fade in animation."""
        self.start_time = time.time()
        self.fading_in = True
        
    def start_fade_out(self):
        """Start fade out animation."""
        self.start_time = time.time()
        self.fading_in = False
        
    def get_alpha(self):
        """Get current alpha value."""
        if self.start_time is None:
            return 1.0 if self.fading_in else 0.0
        
        elapsed = time.time() - self.start_time
        progress = min(elapsed / self.duration, 1.0)
        
        if self.fading_in:
            self.alpha = progress
        else:
            self.alpha = 1.0 - progress
        
        return self.alpha
