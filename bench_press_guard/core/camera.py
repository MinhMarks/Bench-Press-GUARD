import cv2
import time
import threading
from collections import deque

class CameraStream:
    def __init__(self, src=0, name="Camera", width=1280, height=720):
        self.src = src
        self.name = name
        self.width = width
        self.height = height
        
        self.stream = cv2.VideoCapture(self.src)
        self.stream.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.stream.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        
        # Buffer to ensure we output stable FPS if needed, though mostly we just want the latest frame
        self.grabbed = False
        self.frame = None
        self.stopped = False
        self.frame_count = 0
        self.start_time = time.time()
        
        # Latency monitoring
        self.last_frame_time = 0
        
        # Check if source is a local file (string and not RTSP/HTTP)
        self.is_file = False
        if isinstance(self.src, str):
            if not (self.src.lower().startswith("rtsp") or self.src.lower().startswith("http")):
                self.is_file = True

    def start(self):
        """Starts the thread to read frames from the video stream."""
        if self.stream.isOpened():
            self.grabbed, self.frame = self.stream.read()
            if self.grabbed:
                t = threading.Thread(target=self.update, args=())
                t.daemon = True
                t.start()
                return self
        print(f"[ERROR] Could not open camera source: {self.src}")
        return self

    def update(self):
        """Keep looping infinitely until the thread is stopped."""
        # For files, we need to throttle to simulate stream
        chunk_delay = 0
        if self.is_file:
            fps = self.stream.get(cv2.CAP_PROP_FPS)
            if fps <= 0 or fps > 120: fps = 30
            chunk_delay = 1.0 / fps
            
        while True:
            start_read = time.time()
            
            if self.stopped:
                self.stream.release()
                return

            grabbed, frame = self.stream.read()
            if not grabbed:
                # Loop video for demo purposes? Or stop?
                # User said "demo on available video", looping is usually better for kiosk/demo
                # But for analysis, maybe loop is confusing.
                # Let's stop for now.
                self.stop()
                return
            
            # Update the latest frame
            self.grabbed = grabbed
            self.frame = frame
            self.frame_count += 1
            self.last_frame_time = time.time()
            
            # Throttle if file
            if self.is_file:
                process_time = time.time() - start_read
                wait = chunk_delay - process_time
                if wait > 0:
                    time.sleep(wait)
            else:
                # Simple sleep to prevent CPU hogging
                time.sleep(0.001)

    def read(self):
        """Returns the most recent frame."""
        return self.frame

    def stop(self):
        """Indicate that the thread should be stopped."""
        self.stopped = True

    def get_fps(self):
        """Calculates actual FPS being received."""
        elapsed = time.time() - self.start_time
        if elapsed > 0:
            return self.frame_count / elapsed
        return 0

    def get_latency(self):
        """Returns time since last frame was received (in seconds)."""
        return time.time() - self.last_frame_time
