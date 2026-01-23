"""
ROI Selection Wizard for selecting bench press monitoring areas
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QMessageBox, QListWidget, QListWidgetItem
)
from PyQt6.QtCore import Qt, QRect, QPoint
from PyQt6.QtGui import QImage, QPixmap, QPainter, QPen, QColor
import cv2
import numpy as np

class ROIWizard(QDialog):
    """Dialog for interactive ROI selection"""
    
    def __init__(self, current_frame, parent=None, existing_rois=None):
        super().__init__(parent)
        self.current_frame = current_frame.copy()
        self.frame_height, self.frame_width = current_frame.shape[:2]
        
        # Convert existing ROIs from normalized to pixel coordinates
        self.rois = []
        if existing_rois:
            for roi in existing_rois:
                pixel_roi = [
                    int(roi['x'] * self.frame_width),
                    int(roi['y'] * self.frame_height),
                    int(roi['w'] * self.frame_width),
                    int(roi['h'] * self.frame_height)
                ]
                self.rois.append(pixel_roi)
        
        self.current_roi = None  # ROI being drawn
        self.drawing = False
        self.start_point = None
        
        # Colors for different benches
        self.colors = [
            QColor(0, 255, 100),    # Green
            QColor(255, 165, 0),    # Orange
            QColor(0, 200, 255),    # Cyan
            QColor(255, 0, 255),    # Magenta
            QColor(255, 255, 0),    # Yellow
            QColor(128, 0, 255)     # Purple
        ]
        
        self.init_ui()
        self.update_bench_list()  # Show existing ROIs immediately
        self.update_display()
        
    def init_ui(self):
        """Initialize UI"""
        self.setWindowTitle("Setup Bench Press Areas")
        self.setModal(True)
        self.resize(1200, 800)
        
        layout = QHBoxLayout(self)
        
        # Left side - Video display
        left_panel = QVBoxLayout()
        
        # Instructions
        instructions = QLabel(
            "<b>Instructions:</b><br>"
            "1. Click and drag to select a bench press area<br>"
            "2. Release to confirm selection<br>"
            "3. Repeat for multiple benches (max 6)<br>"
            "4. Click 'Save' when done"
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet("padding: 10px; background-color: #2d2d2d; border-radius: 4px;")
        left_panel.addWidget(instructions)
        
        # Video label
        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setStyleSheet("background-color: #000000; border: 2px solid #4a4a4a;")
        self.video_label.setMinimumSize(800, 600)
        
        # Enable mouse tracking
        self.video_label.setMouseTracking(True)
        self.video_label.mousePressEvent = self.mouse_press
        self.video_label.mouseMoveEvent = self.mouse_move
        self.video_label.mouseReleaseEvent = self.mouse_release
        
        left_panel.addWidget(self.video_label)
        
        # Right side - Controls
        right_panel = QVBoxLayout()
        right_panel.setSpacing(10)
        
        # Selected benches list
        list_label = QLabel("<b>Selected Benches:</b>")
        right_panel.addWidget(list_label)
        
        self.bench_list = QListWidget()
        self.bench_list.setMaximumHeight(200)
        right_panel.addWidget(self.bench_list)
        
        # Buttons
        clear_btn = QPushButton("Clear Last")
        clear_btn.clicked.connect(self.clear_last_roi)
        right_panel.addWidget(clear_btn)
        
        clear_all_btn = QPushButton("Clear All")
        clear_all_btn.clicked.connect(self.clear_all_rois)
        right_panel.addWidget(clear_all_btn)
        
        right_panel.addStretch()
        
        # Bottom buttons
        button_layout = QHBoxLayout()
        
        save_btn = QPushButton("✓ Save & Apply")
        save_btn.setObjectName("successButton")
        save_btn.clicked.connect(self.accept)
        
        cancel_btn = QPushButton("✗ Cancel")
        cancel_btn.setObjectName("dangerButton")
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(save_btn)
        
        right_panel.addLayout(button_layout)
        
        # Add panels to main layout
        layout.addLayout(left_panel, 3)
        layout.addLayout(right_panel, 1)
        
    def update_display(self):
        """Update video display with ROIs"""
        # Draw frame with ROIs
        display_frame = self.current_frame.copy()
        
        # Draw saved ROIs
        for idx, roi in enumerate(self.rois):
            color = self.colors[idx % len(self.colors)]
            x, y, w, h = roi
            
            # Draw rectangle
            cv2.rectangle(display_frame, (x, y), (x + w, y + h), 
                         (color.blue(), color.green(), color.red()), 3)
            
            # Draw label
            label = f"Bench #{idx + 1}"
            (text_w, text_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)
            cv2.rectangle(display_frame, (x, y - 35), (x + text_w + 10, y), 
                         (color.blue(), color.green(), color.red()), -1)
            cv2.putText(display_frame, label, (x + 5, y - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        
        # Draw current ROI being drawn
        if self.current_roi is not None:
            x, y, w, h = self.current_roi
            if w > 0 and h > 0:
                color = self.colors[len(self.rois) % len(self.colors)]
                cv2.rectangle(display_frame, (x, y), (x + w, y + h),
                             (color.blue(), color.green(), color.red()), 2)
        
        # Convert to QPixmap
        rgb_frame = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_frame.shape
        bytes_per_line = ch * w
        qt_image = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        
        # Scale to label
        pixmap = QPixmap.fromImage(qt_image)
        scaled_pixmap = pixmap.scaled(
            self.video_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        
        self.video_label.setPixmap(scaled_pixmap)
        
    def mouse_press(self, event):
        """Handle mouse press"""
        if event.button() == Qt.MouseButton.LeftButton and len(self.rois) < 6:
            # Convert from widget coordinates to image coordinates
            pos = self.map_to_image(event.pos())
            if pos:
                self.drawing = True
                self.start_point = pos
                self.current_roi = [pos.x(), pos.y(), 0, 0]
                
    def mouse_move(self, event):
        """Handle mouse move"""
        if self.drawing and self.start_point:
            pos = self.map_to_image(event.pos())
            if pos:
                # Update current ROI
                x = min(self.start_point.x(), pos.x())
                y = min(self.start_point.y(), pos.y())
                w = abs(pos.x() - self.start_point.x())
                h = abs(pos.y() - self.start_point.y())
                
                self.current_roi = [x, y, w, h]
                self.update_display()
                
    def mouse_release(self, event):
        """Handle mouse release"""
        if event.button() == Qt.MouseButton.LeftButton and self.drawing:
            self.drawing = False
            
            # Add ROI if valid size
            if self.current_roi:
                x, y, w, h = self.current_roi
                if w > 20 and h > 20:  # Minimum size
                    self.rois.append(self.current_roi)
                    self.update_bench_list()
                    
            self.current_roi = None
            self.update_display()
            
    def map_to_image(self, widget_pos):
        """Map widget coordinates to image coordinates"""
        if not self.video_label.pixmap():
            return None
            
        # Get pixmap size
        pixmap = self.video_label.pixmap()
        pixmap_w = pixmap.width()
        pixmap_h = pixmap.height()
        
        # Get label size
        label_w = self.video_label.width()
        label_h = self.video_label.height()
        
        # Calculate offset (pixmap is centered)
        offset_x = (label_w - pixmap_w) // 2
        offset_y = (label_h - pixmap_h) // 2
        
        # Adjust widget position
        adj_x = widget_pos.x() - offset_x
        adj_y = widget_pos.y() - offset_y
        
        # Check if click is within pixmap
        if 0 <= adj_x < pixmap_w and 0 <= adj_y < pixmap_h:
            # Scale to original image size
            scale_x = self.frame_width / pixmap_w
            scale_y = self.frame_height / pixmap_h
            
            img_x = int(adj_x * scale_x)
            img_y = int(adj_y * scale_y)
            
            return QPoint(img_x, img_y)
            
        return None
        
    def update_bench_list(self):
        """Update list of selected benches"""
        self.bench_list.clear()
        for idx, roi in enumerate(self.rois):
            x, y, w, h = roi
            item_text = f"Bench #{idx + 1}: ({x}, {y}) - {w}x{h}"
            item = QListWidgetItem(item_text)
            color = self.colors[idx % len(self.colors)]
            item.setForeground(color)
            self.bench_list.addItem(item)
            
    def clear_last_roi(self):
        """Remove last ROI"""
        if self.rois:
            self.rois.pop()
            self.update_bench_list()
            self.update_display()
            
    def clear_all_rois(self):
        """Clear all ROIs"""
        if self.rois:
            reply = QMessageBox.question(
                self,
                "Clear All",
                "Are you sure you want to clear all bench areas?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.rois.clear()
                self.update_bench_list()
                self.update_display()
                
    def get_rois(self):
        """
        Get selected ROIs normalized to 0-1
        
        Returns:
            list: List of ROI dicts with normalized coordinates
        """
        normalized_rois = []
        for roi in self.rois:
            x, y, w, h = roi
            normalized_rois.append({
                'x': x / self.frame_width,
                'y': y / self.frame_height,
                'w': w / self.frame_width,
                'h': h / self.frame_height
            })
        return normalized_rois
