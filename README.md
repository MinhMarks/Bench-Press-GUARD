# Bench Press Guard 🏋️‍♂️🤖

**Automated Bench Press Failure Detection System using Computer Vision.**

This project uses MediaPipe Pose Estimation and OpenCV to detect dangerous situations during the Bench Press exercise in real-time. It analyzes the physics of the barbell (Tilt, Velocity, Stability) to alert usage failures.

## 🚀 Features
- **Real-time Failure Detection**: Identifies Stalled Barbell, Uncontrolled Drop, Loss of Stability (Tilt/Shake), and Prolonged Bottom Position.
- **Interactive ROI Selection**: Select the exact workout area to optimize detection.
- **Video Demo Mode**: Run the system on pre-recorded video files with simulated streaming speed.
- **Smart Analytics**: Uses a dedicated `Barbell` physics engine to calculate metrics.
- **Visual Dashboard**: Modern transparent overlay with real-time FPS, Latency, and Status.
- **Debug Mode**: Visualize skeletal landmarks and barbell vector vectors.

## 🛠️ Installation

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/yourusername/bench-press-guard.git
    cd bench-press-guard
    ```

2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *(Requires Python 3.9+)*

## 🖥️ Usage

### 1. Live Camera (Webcam)
Run the main script to start using your default webcam (Index 0).
```bash
python main.py
```

### 2. Video File Demo
Run the detection on a video file. The system will auto-throttle playback to match the video's FPS.
```bash
python main.py --video "path/to/video.mp4"
```

### 3. Controls & Interaction
- **Step 1 (Startup):** A window will appear. **Draw a box** around the bench press area and press **ENTER**.
- **`q`**: Quit the application.
- **`d`**: Toggle **Debug View** (show/hide skeleton & barbell lines).

## ⚙️ Configuration
Edit `config.py` to tune the system:
- `TARGET_FPS`: Adjust processing speed (Default: 20).
- `DANGER_TILT_ANGLE`: Threshold for tilt detection (Default: 20 degrees).
- `DANGER_DROP_VELOCITY_THRESHOLD`: Sensitivity for drop detection.

## 📂 Project Structure
- `core/`:
  - `analyzer.py`: Main state machine logic.
  - `barbell.py`: Physics model for the barbell.
  - `detector.py`: MediaPipe wrapper.
  - `camera.py`: Video stream handler.
- `utils/`: Visualization and geometry helpers.
- `main.py`: Entry point.

## 📝 Logs
Danger events are logged with timestamps and latency metrics to `bench_press_log.csv`.
