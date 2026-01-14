import cv2
import numpy as np
from config import VISUALIZATION_COLORS

def draw_roi(img, roi, state="NORMAL", active_reason=""):
    """
    Draws the ROI box and status with a modern look.
    ROI is dict {x, y, w, h} normalized.
    """
    h_img, w_img, _ = img.shape
    
    x = int(roi['x'] * w_img)
    y = int(roi['y'] * h_img)
    w = int(roi['w'] * w_img)
    h = int(roi['h'] * h_img)
    
    color = VISUALIZATION_COLORS.get(state, (0, 255, 0))
    
    # 1. Draw Corner Box (More stylish than full rectangle)
    # Top-Left
    cv2.line(img, (x, y), (x + 30, y), color, 3)
    cv2.line(img, (x, y), (x, y + 30), color, 3)
    # Top-Right
    cv2.line(img, (x + w, y), (x + w - 30, y), color, 3)
    cv2.line(img, (x + w, y), (x + w, y + 30), color, 3)
    # Bottom-Left
    cv2.line(img, (x, y + h), (x + 30, y + h), color, 3)
    cv2.line(img, (x, y + h), (x, y + h - 30), color, 3)
    # Bottom-Right
    cv2.line(img, (x + w, y + h), (x + w - 30, y + h), color, 3)
    cv2.line(img, (x + w, y + h), (x + w, y + h - 30), color, 3)
    
    # Thin rectangle for the rest
    cv2.rectangle(img, (x, y), (x + w, y + h), color, 1)
    
    # 2. Status Label with Background
    label = f"{state}"
    if active_reason:
        label += f": {active_reason}"
        
    (text_w, text_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
    
    # Draw background for text
    cv2.rectangle(img, (x, y - 35), (x + text_w + 20, y), color, -1)
    # Text (White or Black depending on contrast? assume White text on color bg usually works for Red/Green)
    text_color = (255, 255, 255)
    cv2.putText(img, label, (x + 10, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, text_color, 2)

def draw_dashboard(img, stats):
    """
    Draws a semi-transparent side panel with system stats.
    stats: dict of messages or values
    """
    h, w, _ = img.shape
    
    # Panel settings
    panel_w = 300
    overlay = img.copy()
    
    # Draw dark panel on the left or top-left
    cv2.rectangle(overlay, (0, 0), (panel_w, 150), (0, 0, 0), -1)
    
    # Blend it
    alpha = 0.6
    cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0, img)
    
    # Draw Text
    y_offset = 30
    for key, value in stats.items():
        text = f"{key}: {value}"
        cv2.putText(img, text, (15, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        y_offset += 30

def draw_info(img, text, position=(10, 30), color=(255, 255, 255)):
    # Legacy wrapper if needed, but we prefer draw_dashboard
    cv2.putText(img, text, position, cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
