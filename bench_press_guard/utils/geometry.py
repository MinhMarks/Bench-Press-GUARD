import math
import numpy as np

def calculate_distance(p1, p2):
    """Calculates Euclidean distance between two points (x, y)."""
    return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)

def calculate_angle(a, b, c):
    """
    Calculates the angle at point b formed by points a-b-c.
    Returns angle in degrees.
    """
    a = np.array(a)
    b = np.array(b)
    c = np.array(c)
    
    radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(a[1] - b[1], a[0] - b[0])
    angle = np.abs(radians * 180.0 / np.pi)
    
    if angle > 180.0:
        angle = 360 - angle
        
    return angle

def calculate_horizontal_tilt(p1, p2):
    """
    Calculates the angle of the line p1-p2 relative to the horizontal axis.
    Used for barbell tilt.
    """
    if p1[0] == p2[0]:
        return 90.0
    
    dy = p2[1] - p1[1]
    dx = p2[0] - p1[0]
    
    angle_rad = math.atan2(dy, dx)
    angle_deg = math.degrees(angle_rad)
    
    # We want the deviation from horizontal (0 degrees)
    return abs(angle_deg)

def normalize_coordinate(value, dimension):
    """Converts pixel coordinate to normalized 0-1."""
    return value / dimension

def pixel_coordinate(value, dimension):
    """Converts normalized 0-1 to pixel coordinate."""
    return int(value * dimension)
