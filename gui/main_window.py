"""
Main application window for BenchGuard Pro
"""
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QMenuBar, QMenu, QStatusBar,
    QFileDialog, QMessageBox, QGroupBox, QRadioButton,
    QComboBox, QLineEdit, QSplitter, QDialog
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QAction, QPixmap
import os
from pathlib import Path

from gui.camera_widget import CameraWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.camera_active = False
        self.video_path = None
        self.selected_rois = []  # Store selected ROIs
        self.bench_colors = [  # Colors for benches
            (0, 255, 100),    # Green
            (255, 165, 0),    # Orange
            (0, 200, 255),    # Cyan
            (255, 0, 255),    # Magenta
            (255, 255, 0),    # Yellow
            (128, 0, 255)     # Purple
        ]
        
        self.init_ui()
        self.load_stylesheet()
        
        # Initialize processing worker
        from gui.processing_worker import ProcessingWorker
        self.worker = ProcessingWorker()
        self.worker.results_ready.connect(self.update_bench_results)
        self.worker.fps_updated.connect(self.update_fps)
        
        # Processing state
        self.processing_paused = False
        
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("BenchGuard Pro - Bench Press Safety Monitor")
        self.setGeometry(100, 100, 1400, 900)
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create central widget with splitter layout
        central_widget = QWidget()
        main_layout = QHBoxLayout(central_widget)
        
        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel - Settings
        settings_panel = self.create_settings_panel()
        settings_panel.setObjectName("settingsPanel")
        settings_panel.setMinimumWidth(350)
        settings_panel.setMaximumWidth(500)
        
        # Right panel - Video/Dashboard
        video_panel = self.create_video_panel()
        video_panel.setObjectName("videoPanel")
        
        splitter.addWidget(settings_panel)
        splitter.addWidget(video_panel)
        splitter.setSizes([350, 1050])
        
        main_layout.addWidget(splitter)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        self.setCentralWidget(central_widget)
        
        # Create status bar
        self.create_status_bar()
        
    def create_menu_bar(self):
        """Create application menu bar"""
        menubar = self.menuBar()
        
        # File Menu
        file_menu = menubar.addMenu("File")
        
        open_video_action = QAction("Open Video File...", self)
        open_video_action.triggered.connect(self.open_video_file)
        file_menu.addAction(open_video_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Settings Menu
        settings_menu = menubar.addMenu("Settings")
        
        configure_action = QAction("Configure Camera...", self)
        configure_action.triggered.connect(self.configure_camera)
        settings_menu.addAction(configure_action)
        
        roi_action = QAction("Setup Bench Areas...", self)
        roi_action.triggered.connect(self.setup_rois)
        settings_menu.addAction(roi_action)
        
        # Help Menu
        help_menu = menubar.addMenu("Help")
        
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
    def create_settings_panel(self):
        """Create left settings panel"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title = QLabel("BenchGuard Pro")
        title.setObjectName("titleLabel")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Camera Source Group
        camera_group = QGroupBox("Camera Source")
        camera_layout = QVBoxLayout()
        
        self.radio_live = QRadioButton("Live Camera")
        self.radio_video = QRadioButton("Video File (Testing)")
        self.radio_video.setChecked(True)  # Default to video for testing
        
        camera_layout.addWidget(self.radio_live)
        camera_layout.addWidget(self.radio_video)
        
        # Camera ID selection (for live camera)
        self.camera_id_label = QLabel("Camera ID:")
        self.camera_id_combo = QComboBox()
        self.camera_id_combo.addItems(["Camera 0", "Camera 1", "Camera 2"])
        self.camera_id_label.setVisible(False)
        self.camera_id_combo.setVisible(False)
        camera_layout.addWidget(self.camera_id_label)
        camera_layout.addWidget(self.camera_id_combo)
        
        # Video file selection
        self.video_file_label = QLabel("Video File:")
        self.video_path_label = QLineEdit()
        self.video_path_label.setPlaceholderText("No video selected...")
        self.video_path_label.setReadOnly(True)
        
        self.browse_btn = QPushButton("📁 Browse Video File")
        self.browse_btn.clicked.connect(self.browse_video_file)
        
        camera_layout.addWidget(self.video_file_label)
        camera_layout.addWidget(self.video_path_label)
        camera_layout.addWidget(self.browse_btn)
        
        camera_group.setLayout(camera_layout)
        layout.addWidget(camera_group)
        
        # Connect signals
        self.radio_live.toggled.connect(self.camera_source_changed)
        
        # Control Buttons
        control_layout = QVBoxLayout()
        
        self.connect_btn = QPushButton("▶️ Start Monitoring")
        self.connect_btn.setObjectName("successButton")
        self.connect_btn.clicked.connect(self.toggle_monitoring)
        
        self.pause_btn = QPushButton("⏸️ Pause Processing")
        self.pause_btn.clicked.connect(self.toggle_pause)
        self.pause_btn.setEnabled(False)
        self.pause_btn.setVisible(False)  # Hidden until monitoring starts
        
        self.roi_btn = QPushButton("🎯 Setup Bench Areas")
        self.roi_btn.clicked.connect(self.setup_rois)
        self.roi_btn.setEnabled(False)
        
        control_layout.addWidget(self.connect_btn)
        control_layout.addWidget(self.pause_btn)
        control_layout.addWidget(self.roi_btn)
        
        layout.addLayout(control_layout)
        
        # System Info Section
        info_group = QGroupBox("System Info")
        info_layout = QVBoxLayout()
        
        self.status_label = QLabel("Status: Idle")
        self.fps_label = QLabel("FPS: --")
        
        info_layout.addWidget(self.status_label)
        info_layout.addWidget(self.fps_label)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # Benches Status Section (scrollable)
        from PyQt6.QtWidgets import QScrollArea
        self.benches_scroll = QScrollArea()
        self.benches_scroll.setWidgetResizable(True)
        self.benches_scroll.setMaximumHeight(300)
        
        self.benches_container = QWidget()
        self.benches_layout = QVBoxLayout(self.benches_container)
        self.benches_layout.setSpacing(10)
        
        self.bench_cards = []  # Store bench card widgets
        
        self.benches_scroll.setWidget(self.benches_container)
        layout.addWidget(self.benches_scroll)
        
        # Spacer
        layout.addStretch()
        
        # Footer
        footer = QLabel("© 2026 GymerGuard\nBench Press Safety System")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer.setStyleSheet("color: #808080; font-size: 9pt;")
        layout.addWidget(footer)
        
        return panel
        
    def create_video_panel(self):
        """Create right video display panel"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Camera widget
        self.camera_widget = CameraWidget()
        layout.addWidget(self.camera_widget)
        
        return panel
        
    def create_status_bar(self):
        """Create bottom status bar"""
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        self.statusbar.showMessage("Ready | Please select a video file or camera to begin")
        
    def load_stylesheet(self):
        """Load QSS stylesheet"""
        qss_path = Path(__file__).parent / "styles.qss"
        if qss_path.exists():
            with open(qss_path, 'r') as f:
                self.setStyleSheet(f.read())
                
    def camera_source_changed(self):
        """Handle camera source radio button change"""
        is_live = self.radio_live.isChecked()
        
        # Show/hide appropriate controls
        self.camera_id_label.setVisible(is_live)
        self.camera_id_combo.setVisible(is_live)
        self.video_file_label.setVisible(not is_live)
        self.video_path_label.setVisible(not is_live)
        self.browse_btn.setVisible(not is_live)
        
        # Clear ROIs when changing source
        self.clear_rois()
        
    def browse_video_file(self):
        """Open file dialog to select video"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Video File",
            "",
            "Video Files (*.mp4 *.avi *.mov *.mkv);;All Files (*.*)"
        )
        
        if file_path:
            self.video_path = file_path
            self.video_path_label.setText(file_path)
            self.statusbar.showMessage(f"Video loaded: {Path(file_path).name}")
            
            # Clear ROIs when changing video
            self.clear_rois()
            
    def toggle_monitoring(self):
        """Start/stop monitoring"""
        if not self.camera_active:
            self.start_monitoring()
        else:
            self.stop_monitoring()
            
    def start_monitoring(self):
        """Start camera monitoring"""
        # Validate source
        if self.radio_video.isChecked() and not self.video_path:
            QMessageBox.warning(
                self,
                "No Video Selected",
                "Please select a video file first."
            )
            return
            
        # Get source
        if self.radio_live.isChecked():
            source = self.camera_id_combo.currentIndex()
        else:
            source = self.video_path
            
        # Start camera
        success = self.camera_widget.start_camera(source)
        
        if success:
            self.camera_active = True
            self.processing_paused = False
            self.connect_btn.setText("⏹ Stop Monitoring")
            self.connect_btn.setObjectName("dangerButton")
            self.connect_btn.setStyle(self.connect_btn.style())  # Refresh style
            self.pause_btn.setEnabled(True)
            self.pause_btn.setVisible(True)
            self.roi_btn.setEnabled(True)
            self.status_label.setText("Status: Monitoring")
            self.statusbar.showMessage("Monitoring active")
            
            # Connect camera frames to worker
            self.camera_widget.frame_ready.connect(self.worker.set_frame)
        else:
            QMessageBox.critical(
                self,
                "Connection Failed",
                "Failed to connect to camera/video source."
            )
            
    def stop_monitoring(self):
        """Stop camera monitoring"""
        # Stop worker
        if self.worker.isRunning():
            self.worker.stop()
        
        # Disconnect signals
        try:
            self.camera_widget.frame_ready.disconnect(self.worker.set_frame)
        except:
            pass
        
        # Stop camera and reset display
        self.camera_widget.stop_camera()
        
        # Clear all visual overlays BEFORE showing placeholder
        self.camera_widget.set_rois([], [])
        self.camera_widget.set_pip_mode(False)
        
        # Reset UI state
        self.camera_active = False
        self.processing_paused = False
        self.connect_btn.setText("▶️ Start Monitoring")
        self.connect_btn.setObjectName("successButton")
        self.connect_btn.setStyle(self.connect_btn.style())
        self.pause_btn.setEnabled(False)
        self.pause_btn.setVisible(False)
        self.pause_btn.setText("⏸️ Pause Processing")
        self.roi_btn.setEnabled(False)
        self.status_label.setText("Status: Idle")
        self.statusbar.showMessage("Monitoring stopped")
        
        # Clear ROIs and bench cards
        self.clear_rois()
    
    def toggle_pause(self):
        """Toggle pause/resume processing"""
        if self.processing_paused:
            # Resume processing
            self.processing_paused = False
            self.pause_btn.setText("⏸️ Pause Processing")
            self.status_label.setText("Status: Monitoring")
            self.statusbar.showMessage("Processing resumed")
            
            # Disable keypoint visualization
            self.camera_widget.set_show_keypoints(False)
            self.worker.set_show_keypoints(False)
            
            # Worker should already be running, just re-enable full analysis
            # No need to restart worker
        else:
            # Pause processing (but keep worker running for keypoints)
            self.processing_paused = True
            self.pause_btn.setText("▶️ Resume Processing")
            self.status_label.setText("Status: Paused (Keypoints Visible)")
            self.statusbar.showMessage("Processing paused - Showing keypoints for debugging")
            
            # Enable keypoint visualization
            self.camera_widget.set_show_keypoints(True)
            self.worker.set_show_keypoints(True)
            
            # Clear PIP mode but keep ROI overlays and worker running
            self.camera_widget.set_pip_mode(False)
        
    def open_video_file(self):
        """Quick action to open video"""
        self.radio_video.setChecked(True)
        self.browse_video_file()
        
    def configure_camera(self):
        """Open camera configuration dialog"""
        QMessageBox.information(
            self,
            "Camera Configuration",
            "Camera configuration dialog coming soon!"
        )
        
    def setup_rois(self):
        """Open ROI setup wizard"""
        if not self.camera_active:
            QMessageBox.warning(
                self,
                "Camera Not Active",
                "Please start monitoring first before setting up bench areas."
            )
            return
        
        # Get current frame from camera widget
        if self.camera_widget.camera is None:
            QMessageBox.warning(
                self,
                "No Frame Available",
                "Could not get video frame. Please ensure video is playing."
            )
            return
        
        # Read a frame
        ret, frame = self.camera_widget.camera.read()
        if not ret or frame is None:
            QMessageBox.warning(
                self,
                "No Frame Available",
                "Could not read frame from video source."
            )
            return
        
        # Open ROI wizard
        from gui.roi_wizard import ROIWizard
        wizard = ROIWizard(frame, self, existing_rois=self.selected_rois)  # Pass existing ROIs
        
        if wizard.exec() == QDialog.DialogCode.Accepted:
            rois = wizard.get_rois()
            if rois:
                self.selected_rois = rois  # Save ROIs
                self.statusbar.showMessage(f"Configured {len(rois)} bench area(s)")
                
                # Enable ROI overlay on camera widget
                self.camera_widget.set_rois(self.selected_rois, self.bench_colors)
                
                # Start processing worker
                self.worker.set_rois(self.selected_rois)
                if not self.worker.isRunning():
                    self.worker.start()
                
                # Create bench status cards
                self.create_bench_cards(len(rois))
                
                self.statusbar.showMessage(f"Processing {len(rois)} bench area(s) with YOLO...")
                
                QMessageBox.information(
                    self,
                    "Processing Started",
                    f"Successfully configured {len(rois)} bench press area(s).\n\n"
                    "YOLO detection is now running!\n"
                    "Watch for DANGER alerts."
                )
            else:
                QMessageBox.warning(
                    self,
                    "No Areas Selected",
                    "No bench areas were selected."
                )
        
    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self,
            "About BenchGuard Pro",
            "<h2>BenchGuard Pro</h2>"
            "<p>Professional Bench Press Safety Monitoring System</p>"
            "<p>Version 2.0</p>"
            "<p>© 2026 GymerGuard</p>"
            "<p>Powered by YOLO11-Pose AI Detection</p>"
        )
    
    def clear_rois(self):
        """Clear all ROIs"""
        self.selected_rois = []
        # Clear bench cards
        for card in self.bench_cards:
            card.deleteLater()
        self.bench_cards.clear()
        
        self.camera_widget.set_rois([], [])
        if self.worker.isRunning():
            self.worker.stop()
    
    def create_bench_cards(self, count):
        """Create status cards for each bench"""
        # Clear existing cards
        for card in self.bench_cards:
            card.deleteLater()
        self.bench_cards.clear()
        
        # Create new cards
        for i in range(count):
            card = QWidget()
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(10, 10, 10, 10)
            
            # Card styling
            card.setStyleSheet(
                "QWidget { background-color: #3a3a3a; border-radius: 6px; "
                "border: 2px solid #4a4a4a; }"
            )
            
            # Bench title
            title = QLabel(f"<b>Bench #{i+1}</b>")
            color = self.bench_colors[i % len(self.bench_colors)]
            title.setStyleSheet(f"color: rgb{color}; font-size: 11pt; border: none;")
            
            # Status
            status = QLabel("Status: --")
            status.setObjectName(f"bench_{i}_status")
            status.setStyleSheet("color: #b0b0b0; border: none;")
            
            card_layout.addWidget(title)
            card_layout.addWidget(status)
            
            self.benches_layout.addWidget(card)
            self.bench_cards.append(card)
    
    def update_bench_results(self, results):
        """Update UI with processing results"""
        # Extract keypoints if available
        keypoints_dict = {}
        for result in results:
            if 'keypoints' in result:
                keypoints_dict[result['id'] - 1] = result['keypoints']
        
        if keypoints_dict:
            self.camera_widget.set_keypoints(keypoints_dict)
        
        # Update individual bench cards
        for idx, result in enumerate(results):
            if idx < len(self.bench_cards):
                status_label = self.bench_cards[idx].findChild(QLabel, f"bench_{idx}_status")
                if status_label:
                    state = result['state']
                    reason = result.get('reason', '')
                    
                    if state == 'DANGER':
                        status_label.setText(f"<b style='color: #ff1744;'>⚠️ DANGER</b><br><small>{reason}</small>")
                        # Update card border
                        self.bench_cards[idx].setStyleSheet(
                            "QWidget { background-color: rgba(255, 23, 68, 0.1); "
                            "border-radius: 6px; border: 2px solid #ff1744; }"
                        )
                    else:
                        status_label.setText(f"<span style='color: #00e676;'>✓ OK</span>")
                        self.bench_cards[idx].setStyleSheet(
                            "QWidget { background-color: #3a3a3a; border-radius: 6px; "
                            "border: 2px solid #4a4a4a; }"
                        )
        
        # Update global status and trigger PIP if needed
        danger_benches = [(idx, r) for idx, r in enumerate(results) if r['state'] == 'DANGER']
        
        if danger_benches:
            danger_count = len(danger_benches)
            self.status_label.setText(f"<b style='color: #ff1744;'>⚠️ DANGER: {danger_count} bench(es)</b>")
            self.statusbar.showMessage(f"⚠️ DANGER on bench(es): {', '.join([f'#{idx+1}' for idx, _ in danger_benches])}")
            
            # Trigger PIP mode with ALL danger benches
            danger_rois = [{'index': idx, 'roi': r['roi']} for idx, r in danger_benches]
            self.camera_widget.set_pip_mode(True, danger_rois)
        else:
            self.status_label.setText("Status: <span style='color: #00e676;'>✓ All Clear</span>")
            self.camera_widget.set_pip_mode(False)
    
    def update_fps(self, fps):
        """Update FPS display"""
        self.fps_label.setText(f"FPS: {int(fps)}")
