# Changelog

## [2.0.0] - 2026-01-22

### 🎉 Major Release: Professional GUI Application

Complete transformation from CLI to professional desktop GUI application with multi-bench monitoring capabilities.

### ✨ Features Added

#### GUI Application
- **PyQt6 Desktop Interface**: Professional dark theme with 2-panel layout
- **Camera Source Selection**: Support for both Live Camera and Video File modes
- **Interactive ROI Wizard**: Click-and-drag selection for multiple bench areas
- **Multi-Bench Monitoring**: Simultaneous monitoring of multiple benches with color-coded ROIs
- **Real-time Dashboard**: Per-bench status cards with live updates

#### Intelligent Danger Detection
- **PIP Mode (Picture-in-Picture)**: Auto-zoom to danger ROI with full-view thumbnail
- **Multi-Danger Handling**: Automatic cycling through multiple danger zones (3s intervals)
- **Status Indicators**: Color-coded warnings (🟢 OK / 🔴 DANGER)
- **Specific Alerts**: Detailed danger reasons (tilt angle, stall time, etc.)

#### Advanced Controls
- **Pause/Resume**: Pause processing while keeping camera feed active
- **Keypoint Visualization**: Debug mode showing 17 COCO keypoints + skeleton (in pause mode)
- **Dynamic Threshold**: Adjustable tilt threshold (default: 170°)
- **ROI Persistence**: Selected ROIs retained across wizard reopens

#### Visual Improvements
- **Professional Styling**: Dark theme with rounded corners, shadows
- **Smooth Transitions**: Color transitions for state changes
- **ROI Overlays**: Multi-colored borders for different benches
- **PIP Thumbnail**: Scaled-down borders for clarity
- **Clean UI Reset**: Proper cleanup on stop monitoring

### 🔧 Technical Improvements

- **Background Processing**: Separate QThread worker for YOLO processing
- **Signal/Slot Architecture**: Clean PyQt6 event handling
- **Frame Management**: Efficient frame passing and ROI extraction
- **GPU Optimization**: CUDA support with fallback to CPU
- **Modular Structure**: Separated GUI components (main_window, camera_widget, roi_wizard, processing_worker)

### 📦 Dependencies

- PyQt6 >= 6.5.0 - GUI framework
- ultralytics >= 8.0.0 - YOLO11-Pose
- opencv-python >= 4.8.0 - Video processing
- numpy >= 1.24.0 - Numerical operations

### 🐛 Bug Fixes

- Fixed video playback loop termination after ROI selection
- Fixed UI elements visibility (camera ID hidden in video mode)
- Fixed ROI overlay persistence after stop monitoring
- Fixed stylesheet syntax error (CSS comments)
- Resolved config constant naming conflicts (DANGER_TILT_ANGLE → TILT_THRESHOLD)
- Fixed bench cards not clearing on source change

### 📝 Documentation

- Comprehensive README.md with installation guide
- LaTeX demo section (demo_section.tex) for academic report
- MIT License added
- Updated .gitignore for large files exclusion

### 🎯 Performance

- **FPS**: 20-25 FPS @ 1080p on RTX 3050
- **Latency**: < 100ms from detection to alert
- **GPU Usage**: ~60-70% during processing
- **Accuracy**: YOLO11-Pose 72% AP on COCO dataset

### 🚀 Usage

```bash
# Install dependencies
pip install -r requirements.txt

# Run GUI application
python gui_app.py

# Legacy CLI (still available)
python main.py --source video.mp4 --detector yolo
```

### 📊 Project Structure

```
gui/                    # PyQt6 GUI components
├── main_window.py     # Main application
├── camera_widget.py   # Video display
├── roi_wizard.py      # ROI selection
├── processing_worker.py # YOLO worker thread
└── styles.qss         # Dark theme
```

### 🔮 Future Enhancements

- [ ] Multi-camera support
- [ ] Alert history log
- [ ] Sound notifications
- [ ] Settings persistence (config.json)
- [ ] Export detection reports

---

## [1.0.0] - Previous CLI Version

- Initial CLI implementation
- YOLO11-Pose integration
- Basic danger detection
- Single ROI monitoring
