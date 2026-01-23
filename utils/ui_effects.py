import cv2
import numpy as np
from config import VISUALIZATION_COLORS

def create_gradient_overlay(h, w, color1, color2, direction='vertical'):
    """
    Create a smooth gradient overlay.
    
    Args:
        h: Height
        w: Width
        color1: Starting color (B, G, R)
        color2: Ending color (B, G, R)
        direction: 'vertical' or 'horizontal'
    
    Returns:
        gradient: Numpy array of gradient
    """
    gradient = np.zeros((h, w, 3), dtype=np.uint8)
    
    if direction == 'vertical':
        for i in range(h):
            ratio = i / h
            color = tuple(int(color1[j] * (1 - ratio) + color2[j] * ratio) for j in range(3))
            gradient[i, :] = color
    else:  # horizontal
        for i in range(w):
            ratio = i / w
            color = tuple(int(color1[j] * (1 - ratio) + color2[j] * ratio) for j in range(3))
            gradient[:, i] = color
    
    return gradient

def apply_glassmorphism(img, x, y, w, h, alpha=0.3, blur_amount=15):
    """
    Apply glassmorphism effect to a region.
    
    Args:
        img: Image to apply effect to
        x, y, w, h: Region coordinates
        alpha: Transparency level
        blur_amount: Blur strength
    
    Returns:
        Modified image with glassmorphism
    """
    # Ensure blur amount is odd
    if blur_amount % 2 == 0:
        blur_amount += 1
    
    # Bounds checking
    img_h, img_w = img.shape[:2]
    if x < 0 or y < 0 or x + w > img_w or y + h > img_h or w <= 0 or h <= 0:
        print(f"[WARNING] Glassmorphism ROI out of bounds: ({x},{y},{w},{h}) vs image ({img_w},{img_h})")
        return img
    
    try:
        # Extract ROI
        roi = img[y:y+h, x:x+w].copy()
        
        if roi.size == 0:
            return img
        
        # Apply blur
        blurred = cv2.GaussianBlur(roi, (blur_amount, blur_amount), 0)
        
        # Create semi-transparent dark overlay
        overlay = np.zeros_like(blurred)
        overlay[:] = (20, 20, 30)  # Dark background
        
        # Blend
        result = cv2.addWeighted(blurred, alpha, overlay, 1 - alpha, 0)
        
        # Add frosted glass effect (subtle noise)
        noise = np.random.randint(-5, 5, result.shape, dtype=np.int16)
        result = np.clip(result.astype(np.int16) + noise, 0, 255).astype(np.uint8)
        
        # Place back
        img[y:y+h, x:x+w] = result
    except Exception as e:
        print(f"[ERROR] Glassmorphism failed: {e}")
    
    return img

def draw_glow_text(img, text, position, font=cv2.FONT_HERSHEY_SIMPLEX, 
                   font_scale=0.7, color=(255, 255, 255), thickness=2, glow_color=(100, 200, 255)):
    """
    Draw text with a glowing effect.
    
    Args:
        img: Image to draw on
        text: Text string
        position: (x, y) position
        font: Font face
        font_scale: Font size
        color: Main text color
        thickness: Text thickness
        glow_color: Glow/shadow color
    """
    x, y = position
    
    # Draw glow (multiple layers)
    for offset in [6, 4, 2]:
        glow_alpha = 0.3 / offset
        for dx, dy in [(-offset, 0), (offset, 0), (0, -offset), (0, offset)]:
            cv2.putText(img, text, (x + dx, y + dy), font, font_scale, glow_color, thickness + offset // 2)
    
    # Draw main text
    cv2.putText(img, text, position, font, font_scale, color, thickness)

def create_progress_bar(img, x, y, w, h, progress, color_low=(0, 0, 255), color_high=(0, 255, 0)):
    """
    Draw a gradient progress bar.
    
    Args:
        img: Image to draw on
        x, y: Position
        w, h: Dimensions
        progress: Progress value (0.0 to 1.0)
        color_low: Color at 0%
        color_high: Color at 100%
    """
    # Background
    cv2.rectangle(img, (x, y), (x + w, y + h), (50, 50, 50), -1)
    cv2.rectangle(img, (x, y), (x + w, y + h), (100, 100, 100), 1)
    
    # Progress fill
    fill_w = int(w * progress)
    if fill_w > 0:
        # Create gradient for progress bar
        gradient = create_gradient_overlay(h, fill_w, color_low, color_high, direction='horizontal')
        img[y:y+h, x:x+fill_w] = gradient
    
    # Percentage text
    percent_text = f"{int(progress * 100)}%"
    (text_w, text_h), _ = cv2.getTextSize(percent_text, cv2.FONT_HERSHEY_SIMPLEX, 0.4, 1)
    text_x = x + (w - text_w) // 2
    text_y = y + (h + text_h) // 2
    cv2.putText(img, percent_text, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
