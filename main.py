import cv2
import time
import signal
import sys
import argparse
from config import *
from config import BENCH_COLORS  # Explicit import for multi-ROI
from core.camera import CameraStream
from core.detector import PoseDetector
from core.analyzer import BenchPressAnalyzer
from core.logger import FailureLogger
from utils.visualization import draw_roi, draw_info
from utils.animation_utils import DangerAnimator

def signal_handler(sig, frame):
    print('You pressed Ctrl+C! Exiting...')
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

def main():
    # Parse Arguments
    parser = argparse.ArgumentParser(description='Bench Press Guard')
    parser.add_argument('--video', type=str, help='Path to video file for demo mode')
    parser.add_argument('--detector', type=str, default=DETECTOR_TYPE, 
                        choices=['mediapipe', 'yolo'], 
                        help='Pose detector to use')
    parser.add_argument('--device', type=str, default=GPU_DEVICE,
                        help='Device for inference: cuda:0 or cpu')
    args = parser.parse_args()

    # 1. Initialize System
    print("="*60)
    print("Initializing Bench Press Guard")
    print("="*60)
    print(f"Detector: {args.detector.upper()}")
    print(f"Device: {args.device}")
    
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
    
    # Initialize detector based on selection
    if args.detector == 'yolo':
        from core.detector_yolo import YOLOPoseDetector
        detector = YOLOPoseDetector(model_size=YOLO_MODEL_SIZE, device=args.device)
    else:  # mediapipe
        detector = PoseDetector(detection_con=0.7, track_con=0.7)
    
    # Wait for camera to warm up
    time.sleep(2.0)
    
    # --- Multi-ROI Selection ---
    print("="*60)
    print("Select bench press areas (one at a time)")
    print("Press ESC after selecting all benches to continue")
    print("="*60)
    
    rois = []
    bench_count = 0
    
    while True:
        # Get fresh frame for selection
        first_frame = None
        for _ in range(10):
            first_frame = camera.read()
            if first_frame is not None:
                break
            time.sleep(0.1)
        
        if first_frame is None:
            print("Error: Could not read frame from camera/video.")
            return
        
        # Draw existing ROIs on frame for reference
        display_frame = first_frame.copy()
        h, w, _ = display_frame.shape
        for idx, roi in enumerate(rois):
            x = int(roi['x'] * w)
            y = int(roi['y'] * h)
            roi_w = int(roi['w'] * w)
            roi_h = int(roi['h'] * h)
            color = BENCH_COLORS[idx % len(BENCH_COLORS)]
            cv2.rectangle(display_frame, (x, y), (x + roi_w, y + roi_h), color, 3)
            cv2.putText(display_frame, f"Bench #{idx + 1}", (x, y - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        
        # Prompt user
        if bench_count == 0:
            window_title = "Select Bench #1 (ESC to skip)"
        else:
            window_title = f"Select Bench #{bench_count + 1} or ESC to finish"
        
        cv2.namedWindow(window_title, cv2.WINDOW_NORMAL)
        r = cv2.selectROI(window_title, display_frame, fromCenter=False, showCrosshair=True)
        cv2.destroyWindow(window_title)
        
        # Check if selection was cancelled (ESC pressed)
        if r[2] == 0 or r[3] == 0:
            if bench_count == 0:
                print("No benches selected. Using default single bench.")
                # Use default ROI
                rois.append(DEFAULT_ROI)
                bench_count = 1
            else:
                print(f"Finished selecting {bench_count} benches.")
            break
        
        # Normalize and store ROI
        selected_roi = {
            "x": r[0] / w,
            "y": r[1] / h,
            "w": r[2] / w,
            "h": r[3] / h
        }
        rois.append(selected_roi)
        bench_count += 1
        print(f"Bench #{bench_count} selected: {selected_roi}")
        
        # Limit to 6 benches
        if bench_count >= 6:
            print("Maximum 6 benches reached.")
            break
    
    # CRITICAL FIX: Restart video stream to reset from beginning
    print(f"[DEBUG] camera.is_file = {camera.is_file}")
    if camera.is_file:
        print("[INFO] Restarting video stream...")
        camera.stop()
        print("[DEBUG] Camera stopped")
        time.sleep(0.5)
        camera = CameraStream(src=source, width=CAMERA_WIDTH, height=CAMERA_HEIGHT).start()
        print("[DEBUG] Camera restarted")
        time.sleep(1.0)
        print("[DEBUG] Ready to process")
    
    # Build benches list with unique colors
    benches = []
    for idx, roi in enumerate(rois):
        benches.append({
            "id": idx + 1,
            "roi": roi,
            "analyzer": BenchPressAnalyzer(fps=TARGET_FPS),
            "color": BENCH_COLORS[idx % len(BENCH_COLORS)]
        })
    
    print(f"Monitoring {len(benches)} bench(es)")
    
    logger = FailureLogger()
    
    # Initialize animations
    danger_animator = DangerAnimator()
    
    print("System Active. Press 'q' to quit.")

    prev_frame_time = 0
    show_debug = False
    playback_speed = 1.0  # Speed control
    
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
            if show_debug:
                # Check detector type and draw accordingly
                if args.detector == 'yolo':
                    # YOLO: Draw keypoints manually
                    if lm_list and len(lm_list) > 0:
                        roi_display = display_frame[r_y:r_y+r_h, r_x:r_x+r_w]
                        
                        # Draw skeleton connections (COCO format)
                        connections = [
                            (5, 6), (5, 7), (7, 9), (6, 8), (8, 10),  # Arms
                            (5, 11), (6, 12), (11, 12),  # Torso
                            (11, 13), (13, 15), (12, 14), (14, 16)  # Legs
                        ]
                        
                        # Draw connections
                        for conn in connections:
                            if conn[0] < len(lm_list) and conn[1] < len(lm_list):
                                p1 = lm_list[conn[0]]
                                p2 = lm_list[conn[1]]
                                if p1['visibility'] > 0.3 and p2['visibility'] > 0.3:
                                    cv2.line(roi_display, 
                                            (p1['x_px'], p1['y_px']),
                                            (p2['x_px'], p2['y_px']),
                                            (0, 255, 255), 2)
                        
                        # Draw keypoints
                        for landmark in lm_list:
                            if landmark['visibility'] > 0.3:
                                cv2.circle(roi_display, 
                                          (landmark['x_px'], landmark['y_px']),
                                          4, (0, 255, 0), -1)
                                cv2.circle(roi_display,
                                          (landmark['x_px'], landmark['y_px']),
                                          6, (255, 255, 255), 1)
                        
                        # Draw Barbell Line
                        barbell = bench['analyzer']._extract_barbell(lm_list)
                        if barbell:
                            p1 = (barbell['left']['x_px'], barbell['left']['y_px'])
                            p2 = (barbell['right']['x_px'], barbell['right']['y_px'])
                            cv2.line(roi_display, p1, p2, (255, 0, 255), 4)
                            cv2.circle(roi_display, p1, 8, (255, 0, 255), -1)
                            cv2.circle(roi_display, p2, 8, (255, 0, 255), -1)
                
                else:  # MediaPipe
                    if hasattr(detector, 'results') and detector.results and hasattr(detector.results, 'pose_landmarks'):
                        if detector.results.pose_landmarks:
                            roi_display = display_frame[r_y:r_y+r_h, r_x:r_x+r_w]
                            detector.mp_draw.draw_landmarks(roi_display, detector.results.pose_landmarks, 
                                                           detector.mp_pose.POSE_CONNECTIONS)
                            
                            # Draw Barbell Line
                            barbell = bench['analyzer']._extract_barbell(lm_list)
                            if barbell:
                                p1 = (barbell['left']['x_px'], barbell['left']['y_px'])
                                p2 = (barbell['right']['x_px'], barbell['right']['y_px'])
                                cv2.line(roi_display, p1, p2, (255, 0, 255), 4)
                                cv2.circle(roi_display, p1, 8, (255, 0, 255), -1)
                                cv2.circle(roi_display, p2, 8, (255, 0, 255), -1)

            # 4. Analyze State
            state, reason = bench['analyzer'].analyze(lm_list)
            
            # 5. Log
            logger.log(bench['id'], state, reason, camera.get_latency())
            
            # 6. Animate danger if needed
            if state == "DANGER":
                display_frame = danger_animator.animate_danger_pulse(display_frame, roi_def, intensity=0.4)
            else:
                danger_animator.reset()
            
            # 7. Visualize
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
            "Debug (d)": "ON" if show_debug else "OFF",
            "Detector": args.detector.upper(),
            "Speed": f"{playback_speed:.1f}x"
        }
        
        # Create dashboard panel (LEFT) and combine with video (RIGHT)
        from utils.visualization import create_dashboard_panel
        h, w, _ = display_frame.shape
        dashboard_panel = create_dashboard_panel(stats, h, width=400)
        combined_frame = cv2.hconcat([dashboard_panel, display_frame])
        
        # Show combined view
        cv2.imshow("Bench Press Guard", combined_frame)
        
        # 9. Keyboard Controls  
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('d'):
            show_debug = not show_debug
            print(f"Debug mode: {'ON' if show_debug else 'OFF'}")
        elif key == 82 or key == ord('+'):  # Up arrow or +
            playback_speed = min(playback_speed + 0.1, 3.0)
            print(f"Speed: {playback_speed:.1f}x")
        elif key == 84 or key == ord('-'):  # Down arrow or -  
            playback_speed = max(playback_speed - 0.1, 0.1)
            print(f"Speed: {playback_speed:.1f}x")
        elif key == ord('r'):  # Reset speed
            playback_speed = 1.0
            print(f"Speed reset to 1.0x")
        
        # Apply playback speed (delay for slow motion)
        if camera.is_file and playback_speed < 1.0:
            delay_time = (1.0 / TARGET_FPS) * (1.0 / playback_speed)
            time.sleep(max(0, delay_time - (time.time() - start_time)))
    camera.stop()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
