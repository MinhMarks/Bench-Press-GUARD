import cv2
import time
import signal
import sys
import argparse
from config import *
from core.camera import CameraStream
from core.detector import PoseDetector
from core.analyzer import BenchPressAnalyzer
from core.logger import FailureLogger
from utils.visualization import draw_roi, draw_info

def signal_handler(sig, frame):
    print('You pressed Ctrl+C! Exiting...')
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

def main():
    # Parse Arguments
    parser = argparse.ArgumentParser(description='Bench Press Guard')
    parser.add_argument('--video', type=str, help='Path to video file for demo mode')
    args = parser.parse_args()

    # 1. Initialize System
    print("Initializing Bench Press Guard...")
    
    # Determine source
    # Check if args.video is a digit (camera index) or path
    source = 0
    if args.video:
        if args.video.isdigit():
            source = int(args.video)
        else:
            source = args.video
            print(f"Running in Video Demo Mode: {source}")

    # Initialize components
    camera = CameraStream(src=source, width=CAMERA_WIDTH, height=CAMERA_HEIGHT).start()
    detector = PoseDetector(detection_con=0.7, track_con=0.7)
    
    # Wait for camera to warm up
    time.sleep(2.0)
    
    # --- ROI Selection ---
    print("Please select the Bench Press area on the window...")
    first_frame = None
    # Retry getting frame a few times if slow start
    for _ in range(10):
        first_frame = camera.read()
        if first_frame is not None:
            break
        time.sleep(0.1)
        
    if first_frame is None:
        print("Error: Could not read frame from camera/video.")
        return

    # User selects ROI
    # cv2.selectROI returns (x, y, w, h)
    # create a named window to ensure it pops up
    cv2.namedWindow("Select Bench Area", cv2.WINDOW_NORMAL)
    r = cv2.selectROI("Select Bench Area", first_frame, fromCenter=False, showCrosshair=True)
    cv2.destroyWindow("Select Bench Area")
    
    # If user cancelled (w=0 or h=0), use default or exit? 
    # Let's fallback to default/full screen if invalid
    if r[2] == 0 or r[3] == 0:
        print("No ROI selected. Using default/full screen configurations.")
        selected_roi = DEFAULT_ROI
    else:
        h, w, c = first_frame.shape
        selected_roi = {
            "x": r[0] / w,
            "y": r[1] / h,
            "w": r[2] / w,
            "h": r[3] / h
        }
        print(f"ROI Selected: {selected_roi}")

    # Support multiple benches (ROIs)
    benches = [
        {
            "id": 1,
            "roi": selected_roi,
            "analyzer": BenchPressAnalyzer(fps=TARGET_FPS)
        }
    ]
    
    logger = FailureLogger()
    
    print("System Active. Press 'q' to quit.")

    prev_frame_time = 0
    show_debug = False
    
    while True:
        # Loop start time
        start_time = time.time()
        
        # 1. Get Frame
        if camera.stopped:
            print("Video source ended.")
            break

        frame = camera.read()
        if frame is None:
            continue
            
        # Clone frame for drawing
        display_frame = frame.copy()
        h, w, c = frame.shape
        
        # 2. Process Each Bench
        for bench in benches:
            roi_def = bench['roi']
            
            # Extract ROI Image
            # Handle normalized coords
            r_x = int(roi_def['x'] * w)
            r_y = int(roi_def['y'] * h)
            r_w = int(roi_def['w'] * w)
            r_h = int(roi_def['h'] * h)
            
            # Clamp
            r_x = max(0, r_x)
            r_y = max(0, r_y)
            r_w = min(w - r_x, r_w)
            r_h = min(h - r_y, r_h)
            
            roi_img = frame[r_y:r_y+r_h, r_x:r_x+r_w]
            
            if roi_img.size == 0: continue
            
        # 3. Detect Pose in ROI
            detector.find_pose(roi_img, draw=False) 
            lm_list = detector.find_position(roi_img)
            
            # Draw Debug if enabled
            if show_debug and detector.results.pose_landmarks:
                # Create a view into display_frame to draw on it
                roi_display = display_frame[r_y:r_y+r_h, r_x:r_x+r_w]
                detector.mp_draw.draw_landmarks(roi_display, detector.results.pose_landmarks, detector.mp_pose.POSE_CONNECTIONS)
                
                # Draw Barbell Line specifically
                barbell = bench['analyzer']._extract_barbell(lm_list)
                if barbell:
                    # coords are normalized to ROI, need pixel relative to ROI
                    # actually lm_list has x_px, y_px relative to ROI image size
                    # we can just use those points
                   
                    # Accessing dictionary items from lm_list, but lm_list is list of dicts?
                    # Detector.find_position returns list of dicts.
                    # analyzer._extract_barbell returns dict with 'left', 'right' which are items from lm_list
                    
                    p1 = (barbell['left']['x_px'], barbell['left']['y_px'])
                    p2 = (barbell['right']['x_px'], barbell['right']['y_px'])
                    
                    cv2.line(roi_display, p1, p2, (255, 255, 0), 3) # Cyan line for barbell
                    cv2.circle(roi_display, p1, 5, (255, 0, 255), -1)
                    cv2.circle(roi_display, p2, 5, (255, 0, 255), -1)

            # 4. Analyze State
            state, reason = bench['analyzer'].analyze(lm_list)
            
            # 5. Log
            logger.log(bench['id'], state, reason, camera.get_latency())
            
            # 6. Visualize
            # Pass usage info or reason
            draw_roi(display_frame, roi_def, state, reason if state == "DANGER" else "")
        
        # 7. System Stats & Dashboard
        curr_time = time.time()
        fps = 1 / (curr_time - prev_frame_time) if (curr_time - prev_frame_time) > 0 else 0
        prev_frame_time = curr_time
        
        # Collect stats for dashboard
        stats = {
            "System FPS": f"{int(fps)}",
            "Latency": f"{int(camera.get_latency()*1000)}ms",
            "Status": "Monitoring" if not any(b['analyzer'].state == "DANGER" for b in benches) else "DANGER DETECTED",
            "Debug (d)": "ON" if show_debug else "OFF"
        }
        
        from utils.visualization import draw_dashboard
        draw_dashboard(display_frame, stats)
        
        # Show
        cv2.imshow("Bench Press Guard", display_frame)
        
        # Wait Key (Sleep to match Target FPS?)
        # Simple loop limiter
        process_time = time.time() - start_time
        wait_ms = max(1, int((1.0/TARGET_FPS - process_time) * 1000))
        
        key = cv2.waitKey(wait_ms) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('d'):
            show_debug = not show_debug

    camera.stop()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
