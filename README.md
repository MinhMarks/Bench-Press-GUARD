# BenchGuard Pro 🏋️‍♂️

![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![PyQt6](https://img.shields.io/badge/GUI-PyQt6-green.svg)
![YOLO](https://img.shields.io/badge/AI-YOLO11--Pose-orange.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

**Professional Bench Press Safety Monitoring System** - Hệ thống giám sát an toàn bench press sử dụng AI với giao diện desktop chuyên nghiệp dành cho phòng gym.

<p align="center">
  <img src="image/Screenshot2026-01-23 075001.png" alt="Main Interface" width="750"/>
</p>


> ⚡ **v2.0**: Hoàn toàn mới với GUI PyQt6, multi-bench monitoring, và PIP mode

## ✨ Features

### 🎯 Core Features
- **Multi-Bench Monitoring**: Giám sát đồng thời nhiều bench press từ một camera
- **Real-time Pose Detection**: YOLO11-Pose với độ chính xác 72% AP
- **Danger Alerts**: Phát hiện tức thì các tình huống nguy hiểm:
  - Thanh tạ nghiêng > 170° (mất cân bằng)
  - Stall > 5 giây (kẹt không nâng được)
  - Rơi nhanh không kiểm soát
  - Rung lắc bất thường

### 🖥️ Professional GUI
- **Dark Theme**: Giao diện chuyên nghiệp giảm mỏi mắt
- **2-Panel Layout**: Settings panel (trái) + Video display (phải)
- **Interactive ROI Selection**: Click-and-drag để chọn vùng giám sát
- **Color-coded Status**: 🟢 OK / 🔴 DANGER dễ nhận biết
- **Per-Bench Cards**: Theo dõi trạng thái riêng từng bench

### 📹 Intelligent PIP Mode
- **Auto-Zoom**: Tự động phóng to vùng nguy hiểm
- **Picture-in-Picture**: Thumbnail toàn cảnh ở góc màn hình
- **Multi-Danger**: Tự động cycle qua nhiều vùng nguy hiểm (3s/bench)
- **ROI Highlighting**: Vùng đang zoom được highlight trên thumbnail

### ⚙️ Advanced Controls
- **Pause/Resume**: Tạm dừng xử lý nhưng giữ camera chạy
- **Keypoint Debug**: Hiển thị 17 COCO keypoints + skeleton khi pause
- **Live Camera Support**: Webcam hoặc camera IP
- **Video Testing Mode**: Load file MP4/AVI để testing

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- (Optional) NVIDIA GPU với CUDA để tăng tốc
- Webcam hoặc video file

### Installation

```bash
# Clone repository
git clone https://github.com/MinhMarks/Bench-Press-GUARD.git
cd GymerGaurd

# Install dependencies
pip install -r requirements.txt
```

**Dependencies:**
- `PyQt6>=6.5.0` - GUI framework
- `ultralytics>=8.0.0` - YOLO11-Pose
- `opencv-python>=4.8.0` - Video processing
- `numpy>=1.24.0` - Numerical operations

### Run Application

```bash
# Launch GUI (recommended)
python gui_app.py
```

YOLO model sẽ tự động download lần đầu (~40MB).

## 📖 Usage Guide

### 1️⃣ Chọn Video Source

**Option A: Video File (Recommended for Testing)**
- Click radio button "Video File (Testing)"
- Click "📁 Browse Video File"
- Chọn file MP4/AVI

**Option B: Live Camera**
- Click radio button "Live Camera"
- Chọn Camera ID (0 = webcam mặc định)

### 2️⃣ Start Monitoring

- Click **"▶️ Start Monitoring"**
- Video feed sẽ hiển thị bên phải

### 3️⃣ Setup ROI (Region of Interest)

1. Click **"🎯 Setup Bench Areas"**
2. ROI Wizard mở ra với frame hiện tại
3. **Click và kéo chuột** để vẽ khung vùng bench press
4. Mỗi ROI có màu riêng biệt
5. Có thể chọn nhiều ROI (multi-bench)
6. Click **"Save"** để lưu

### 4️⃣ Monitoring

Hệ thống tự động:
- ✅ Phát hiện pose với YOLO11
- ✅ Phân tích các chỉ số nguy hiểm
- ✅ Cập nhật status cards real-time
- ✅ Zoom tự động khi có DANGER

### 5️⃣ Debug với Keypoints (Optional)

- Click **"⏸️ Pause Processing"**
- Keypoints (17 COCO points) tự động hiển thị
- Skeleton connections màu vàng
- Click **"▶️ Resume"** để tiếp tục

## 📊 Performance

Tested trên NVIDIA RTX 3050 (4GB VRAM):

| Metric | Value |
|--------|-------|
| **FPS** | 20-25 FPS @ 1080p |
| **Latency** | < 100ms |
| **GPU Usage** | 60-70% |
| **Model Accuracy** | 72% AP (COCO) |

## ⚙️ Configuration

Edit `config.py` để điều chỉnh:

```python
# Detection thresholds
TILT_THRESHOLD = 170.0        # Barbell tilt angle (degrees)
DANGER_STALL_TIME = 5.0       # Stall detection (seconds)
DANGER_SHAKE_PCT = 0.10       # Shake threshold (10% shoulder width)

# Performance
TARGET_FPS = 20               # Processing FPS
GPU_DEVICE = 0                # GPU ID (0, 1, 2... or 'cpu')
YOLO_MODEL_SIZE = 'n'         # Model size: n, s, m, l, x
```

## 🏗️ Project Structure

```
GymerGaurd/
├── gui/                      # PyQt6 GUI components
│   ├── main_window.py       # Main application
│   ├── camera_widget.py     # Video display + overlays
│   ├── roi_wizard.py        # ROI selection dialog
│   ├── processing_worker.py # Background YOLO thread
│   └── styles.qss           # Dark theme stylesheet
├── core/                     # Core logic
│   ├── analyzer.py          # Danger analysis
│   ├── detector_yolo.py     # YOLO11-Pose wrapper
│   ├── barbell.py           # Barbell tracking
│   └── temporal_buffer.py   # Time-series data
├── utils/                    # Utilities
│   ├── geometry.py          # Math helpers
│   └── visualization.py     # Drawing utilities
├── config.py                # Configuration
├── gui_app.py              # GUI entry point ⭐
├── main.py                 # CLI entry point (legacy)
└── requirements.txt        # Dependencies
```

## 🎨 Screenshots

### 1. Main Interface - Giao diện chính
<p align="center">
  <img src="image/Screenshot2026-01-23 075001.png" alt="Main Interface" width="750"/>
</p>

Settings panel (trái) + Video display (phải) với dark theme chuyên nghiệp

---

### 2. Multi-Bench Monitoring - Giám sát đa bench
<p align="center">
  <img src="image/Screenshot 2026-01-22 184025.png" alt="Monitoring Active" width="750"/>
</p>

Real-time monitoring với ROI overlays màu sắc + status cards cho từng bench

---

### 3. PIP Danger Mode - Chế độ cảnh báo nguy hiểm
<p align="center">
  <img src="image/Screenshot 2026-01-22 183932.png" alt="PIP Mode" width="750"/>
</p>

Auto-zoom vào vùng nguy hiểm + PIP thumbnail toàn cảnh + keypoints debug

---


## 🔧 Development

### Run CLI Version (Legacy)

```bash
python main.py --source video.mp4 --detector yolo
```

### Test Camera

```bash
python test_camera.py
```

## 📝 Documentation

- [DATASET_TECHNOLOGIES.md](DATASET_TECHNOLOGIES.md) - Chi tiết về data pipeline và features
- [POSE_ESTIMATION_ALTERNATIVES.md](POSE_ESTIMATION_ALTERNATIVES.md) - So sánh các mô hình pose estimation
- [demo_section.tex](demo_section.tex) - LaTeX demo cho báo cáo (Vietnamese)

## 🐛 Known Issues

- PIP mode chỉ hoạt động khi có ít nhất 1 ROI được setup
- Live camera mode yêu cầu camera ID chính xác
- Keypoints chỉ hiển thị khi pause (by design)

## 🗺️ Roadmap

- [ ] Multi-camera support
- [ ] Settings persistence (save config to JSON)
- [ ] Alert history log
- [ ] Sound notifications
- [ ] Export detection reports
- [ ] Custom font integration (Orbitron, Roboto)

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Ultralytics YOLO](https://github.com/ultralytics/ultralytics) - YOLO11-Pose model
- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) - GUI framework
- [OpenCV](https://opencv.org/) - Computer vision library

## 📧 Contact

- **GitHub**: [@MinhMarks](https://github.com/MinhMarks)
- **Project**: [Bench-Press-GUARD](https://github.com/MinhMarks/Bench-Press-GUARD)

For questions or suggestions, please open an issue on GitHub.

---

**Made with ❤️ for gym safety** | **UIT - University of Information Technology**

