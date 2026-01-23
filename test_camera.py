"""
Simple test to check camera reading
"""
import cv2
import time
from core.camera import CameraStream

video_path = "v4.www-y2mate.blog - Swiss Bar Bench Press (360p).mp4"

print("Testing camera stream...")
camera = CameraStream(src=video_path, width=640, height=360).start()
time.sleep(2)

frame_count = 0
start = time.time()

while True:
    if camera.stopped:
        print(f"Camera stopped after {frame_count} frames")
        break
    
    frame = camera.read()
    if frame is None:
        print("Got None frame")
        continue
    
    frame_count += 1
    print(f"Frame {frame_count}: {frame.shape}")
    
    cv2.imshow("Test", frame)
    
    key = cv2.waitKey(30) & 0xFF
    if key == ord('q') or frame_count >= 100:
        break

elapsed = time.time() - start
print(f"Processed {frame_count} frames in {elapsed:.2f}s ({frame_count/elapsed:.1f} FPS)")

camera.stop()
cv2.destroyAllWindows()
