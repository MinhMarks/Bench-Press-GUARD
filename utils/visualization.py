import cv2
import numpy as np
from config import VISUALIZATION_COLORS
from utils.ui_effects import (
    create_gradient_overlay, 
    draw_glow_text,
    create_progress_bar
)
from utils.animation_utils import StateTransition

# Initialize state transition handler
state_transition = StateTransition()

def draw_roi(img, roi, state="NORMAL", active_reason=""):
    """
    Draws the ROI box with modern styling and smooth transitions.
    """
    h_img, w_img, _ = img.shape
    
    x = int(roi['x'] * w_img)
    y = int(roi['y'] * h_img)
    w = int(roi['w'] * w_img)
    h = int(roi['h'] * h_img)
    
    # Get smooth transitioning color
    color = state_transition.update(state)
    color = tuple(int(c) for c in color)
    
    # Draw modern corner brackets
    corner_length = 50
    corner_thickness = 4
    
    # Top-Left
    cv2.line(img, (x, y), (x + corner_length, y), color, corner_thickness)
    cv2.line(img, (x, y), (x, y + corner_length), color, corner_thickness)
    
    # Top-Right
    cv2.line(img, (x + w, y), (x + w - corner_length, y), color, corner_thickness)
    cv2.line(img, (x + w, y), (x + w, y + corner_length), color, corner_thickness)
    
    # Bottom-Left
    cv2.line(img, (x, y + h), (x + corner_length, y + h), color, corner_thickness)
    cv2.line(img, (x, y + h), (x, y + h - corner_length), color, corner_thickness)
    
    # Bottom-Right
    cv2.line(img, (x + w, y + h), (x + w - corner_length, y + h), color, corner_thickness)
    cv2.line(img, (x + w, y + h), (x + w, y + h - corner_length), color, corner_thickness)
    
    # Subtle border line
    cv2.rectangle(img, (x, y), (x + w, y + h), color, 2)
    
    # Status label with gradient background (at BOTTOM-RIGHT of ROI)
    label = f"{state}"
    if active_reason:
        if len(active_reason) > 25:
            active_reason = active_reason[:22] + "..."
        label += f": {active_reason}"
    
    (text_w, text_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
    
    label_h = 38
    label_w = text_w + 30
    
    # Position at BOTTOM-RIGHT of ROI
    label_y = y + h
    label_x = x + w - label_w
    
    if label_y + label_h > h_img:
        label_y = y - label_h
    if label_x < 0:
        label_x = x
    
    if state == "DANGER":
        gradient_bg = create_gradient_overlay(label_h, label_w, (0, 0, 180), (0, 0, 255), 'horizontal')
    else:
        gradient_bg = create_gradient_overlay(label_h, label_w, (0, 180, 0), (0, 255, 100), 'horizontal')
    
    # Draw gradient background with safe bounds
    bg_y1 = max(0, label_y)
    bg_y2 = min(h_img, label_y + label_h)
    bg_x1 = max(0, label_x)
    bg_x2 = min(w_img, label_x + label_w)
    
    if bg_y2 > bg_y1 and bg_x2 > bg_x1:
        bg_h = bg_y2 - bg_y1
        bg_w = bg_x2 - bg_x1
        img[bg_y1:bg_y2, bg_x1:bg_x2] = gradient_bg[:bg_h, :bg_w]
    
    cv2.rectangle(img, (label_x, label_y), (label_x + label_w, label_y + label_h), (255, 255, 255), 2)
    draw_glow_text(img, label, (label_x + 15, label_y + 26), font_scale=0.7, color=(255, 255, 255), thickness=2)

def create_dashboard_panel(stats, height, width=400):
    """
    Creates standalone dashboard panel (left side).
    
    Args:
        stats: Dictionary of statistics
        height: Panel height (match video height)
        width: Panel width (default 400px)
    
    Returns:
        panel: numpy array (H x W x 3) BGR image
    """
    # Create dark panel
    panel = np.zeros((height, width, 3), dtype=np.uint8)
    panel[:] = (20, 20, 30)  # Dark background
    
    # Title section
    title = "BENCH PRESS GUARD"
    title_h = 50
    title_gradient = create_gradient_overlay(title_h, width, (50, 100, 150), (30, 60, 100), 'horizontal')
    panel[0:title_h, :] = title_gradient
    
    # Draw title text
    draw_glow_text(panel, title, (15, 35), font_scale=0.8, 
                   color=(255, 255, 255), thickness=2, glow_color=(100, 200, 255))
    
    # Separator line
    cv2.line(panel, (10, title_h + 10), (width - 10, title_h + 10), (100, 150, 255), 2)
    
    # Stats section
    y_offset = title_h + 30
    line_spacing = 40
    
    # Icons (ASCII)
    icons = {
        "System FPS": ">",
        "Latency": "|",
        "Status": "*" if "DANGER" not in str(stats.get("Status", "")).upper() else "!",
        "Debug (d)": "#",
        "Detector": "+",
        "Speed": "~"
    }
    
    for key, value in stats.items():
        icon = icons.get(key, "*")
        text = f"{icon} {key}: {value}"
        
        # Color code based on status
        if "DANGER" in str(value).upper():
            text_color = (0, 100, 255)  # Red
        elif "ON" in str(value).upper() or "YOLO" in str(value).upper():
            text_color = (100, 255, 100)  # Green
        else:
            text_color = (255, 255, 255)  # White
        
        cv2.putText(panel, text, (20, y_offset), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, text_color, 2)
        y_offset += line_spacing
        
        if y_offset > height - 150:
            break
    
    # Separator before progress bar
    sep_y = height - 130
    cv2.line(panel, (10, sep_y), (width - 10, sep_y), (100, 150, 255), 2)
    
    # Progress bar
    if "System FPS" in stats:
        try:
            fps_value = int(stats["System FPS"])
            fps_progress = min(fps_value / 30.0, 1.0)
            
            bar_y = height - 110
            create_progress_bar(panel, 20, bar_y, width - 40, 20, 
                              fps_progress, color_low=(0, 100, 255), color_high=(0, 255, 100))
            
            cv2.putText(panel, "Performance", (20, bar_y - 8), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
        except:
            pass
    
    # Controls help section
    help_y = height - 75
    cv2.putText(panel, "[CONTROLS]", (20, help_y), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (150, 150, 150), 1)
    cv2.putText(panel, "d  = Debug", (20, help_y + 20), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (180, 180, 180), 1)
    cv2.putText(panel, "+/- = Speed", (20, help_y + 38), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (180, 180, 180), 1)
    cv2.putText(panel, "q  = Quit", (20, help_y + 56), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (180, 180, 180), 1)
    
    # Border
    cv2.rectangle(panel, (0, 0), (width-1, height-1), (100, 150, 255), 3)
    
    return panel

def draw_info(img, text, position=(10, 30), color=(255, 255, 255)):
    """Legacy function for simple text drawing."""
    draw_glow_text(img, text, position, color=color, font_scale=0.7, thickness=2)
