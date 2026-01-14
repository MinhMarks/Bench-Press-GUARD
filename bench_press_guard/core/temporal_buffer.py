from collections import deque
import numpy as np

class TemporalBuffer:
    def __init__(self, maxlen=100):
        self.buffer = deque(maxlen=maxlen)

    def add(self, value):
        self.buffer.append(value)

    def get_last(self, seconds, fps):
        """Get the last N items covering X seconds."""
        count = int(seconds * fps)
        if count > len(self.buffer):
            count = len(self.buffer)
        if count == 0:
            return []
        
        # Convert to list effectively
        return list(self.buffer)[-count:]

    def is_stagnant(self, seconds, fps, threshold=0.01):
        """Checks if values have barely changed over the last X seconds."""
        data = self.get_last(seconds, fps)
        if not data or len(data) < fps: # Need at least 1 second of data
            return False
        
        # Calculate amplitude/std dev
        values = [d['y'] for d in data] # Assuming dict with 'y'
        min_v = min(values)
        max_v = max(values)
        
        return (max_v - min_v) < threshold

    def get_average_velocity(self, seconds, fps):
        """Calculates average velocity over the window."""
        data = self.get_last(seconds, fps)
        if len(data) < 2:
            return 0
        
        # Simple: (End - Start) / Time
        start_y = data[0]['y']
        end_y = data[-1]['y']
        
        # Y is inverted (0 is top), so positive motion (up) is decreasing Y
        # We want strict velocity: dy/dt
        # Let's say: negative result = moving UP, positive result = moving DOWN
        return (end_y - start_y) / seconds
