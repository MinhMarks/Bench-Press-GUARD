import time
import sys
import os

# Setup path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.analyzer import BenchPressAnalyzer
from config import TARGET_FPS

def run_test_scenario(name, data_generator, duration_sec):
    print(f"\n--- Running Scenario: {name} ---")
    analyzer = BenchPressAnalyzer(fps=TARGET_FPS)
    analyzer.last_state_change = 0 # Reset to 0 for mock time (t=0 started)
    
    steps = int(duration_sec * TARGET_FPS)
    start_time = time.time()
    
    danger_detected = False
    
    for i in range(steps):
        # Generate mock landmarks based on time t (i / FPS)
        t = i / TARGET_FPS
        landmarks = data_generator(t)
        
        # Pass the mock time 't' to the analyzer
        state, reason = analyzer.analyze(landmarks, timestamp=t)
        
        if state == "DANGER":
            print(f"Frame {i} ({t:.1f}s): DANGER DETECTED -> {reason}")
            danger_detected = True
            break
            
    if not danger_detected:
        print("Result: NO DANGER detected.")
    else:
        print("Result: DANGER Confirm.")

def normal_reps(t):
    # Sin wave motion
    import math
    y = 0.5 + 0.3 * math.sin(t * 2) # goes between 0.2 and 0.8
    return _mock_landmarks(y, 0)

def stalled_rep(t):
    # Normal then stops at t=2
    if t < 2:
        import math
        y = 0.5 + 0.3 * math.sin(t * 2)
    else:
        y = 0.5 # Stalled mid-way
    return _mock_landmarks(y, 0)

def unsafe_tilt(t):
    # Normal motion but tilts at t=2
    import math
    y = 0.5 + 0.3 * math.sin(t * 2)
    tilt = 0
    if t > 2:
        tilt = 25 # High tilt
    return _mock_landmarks(y, tilt)

def _mock_landmarks(y_mid, tilt_deg):
    # Construct mock wrist dict (normalized)
    import math
    
    # 15 L, 16 R
    # If tilt is 0, yL = yR = y_mid
    # If tilt > 0, we offset yL and yR
    # simple approx: dy = tan(tilt) * dx
    # let dx = 0.2
    
    dx = 0.2
    dy = math.tan(math.radians(tilt_deg)) * dx
    
    yl = y_mid - dy/2
    yr = y_mid + dy/2
    
    lm_list = {}
    # We need index 11, 12 for shoulder width check too (approx x=0.3, 0.7)
    lm_list[11] = {"x": 0.4, "y": 0.2}
    lm_list[12] = {"x": 0.6, "y": 0.2}
    
    lm_list[15] = {"x": 0.4, "y": yl}
    lm_list[16] = {"x": 0.6, "y": yr}
    
    # Fill others to avoid IndexErrors if code checks len
    for i in range(33):
        if i not in lm_list:
            lm_list[i] = {"x": 0, "y": 0}
            
    return lm_list

if __name__ == "__main__":
    run_test_scenario("Normal Reps (10s)", normal_reps, 10)
    run_test_scenario("Stalled Barbell (Expected Danger > 5s stall)", stalled_rep, 8)
    run_test_scenario("Severe Tilt (Expected Danger immediate)", unsafe_tilt, 4)
