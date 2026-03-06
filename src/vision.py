import cv2
import numpy as np
import os

# Cursor HSV (fallback when template matching fails)
CURSOR_HSV_LOWER = [0, 0, 150]
CURSOR_HSV_UPPER = [180, 80, 255]

# Auto-load cursor template if available
TEMPLATE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'cursor_template.png')
_cursor_template_cache = None

def load_cursor_template(path=None):
    """Load cursor template image. Returns None if not found."""
    global _cursor_template_cache
    p = path or TEMPLATE_PATH
    if _cursor_template_cache is not None:
        return _cursor_template_cache
    if os.path.exists(p):
        _cursor_template_cache = cv2.imread(p)
        if _cursor_template_cache is not None:
            print(f"Loaded cursor template from {p} (shape: {_cursor_template_cache.shape})")
        else:
            print(f"Warning: Failed to decode cursor template at {p}")
    else:
        print(f"Warning: Cursor template not found at {p}. Falling back to HSV mode.")
    return _cursor_template_cache

def find_green_bar(image, lower_hsv, upper_hsv):
    """
    Finds the center X coordinate of the green target bar.
    Using HSV for robust color detection.
    """
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, np.array(lower_hsv), np.array(upper_hsv))
    
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    best_bar = None
    max_area = 0
    
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < 400: # Lowered minimum area
            continue
            
        x, y, w, h = cv2.boundingRect(cnt)
        if area > max_area:
            max_area = area
            best_bar = (x, y, w, h)

    if best_bar:
        bx, by, bw, bh = best_bar
        center_x = bx + (bw // 2)
        return center_x, best_bar

    return None, None


def find_cursor(image, roi_bbox=None, template=None, use_template=True):
    """
    Finds the center X coordinate of the player cursor.

    Important Fix (ROI):
    If roi_bbox is provided (x, y, w, h of the green bar), the template matching 
    is heavily restricted to only the horizontal band of the screen where the 
    green bar exists. This prevents false positives from background clutter.
    """

    if not use_template or template is None:
        return None, None

    img_to_search = image
    y_offset = 0

    if roi_bbox is not None:
        gx, gy, gw, gh = roi_bbox
        # Add a small vertical margin (e.g., 20 pixels) above and below the bar
        margin = 20
        y_start = max(0, gy - margin)
        y_end = min(image.shape[0], gy + gh + margin)
        img_to_search = image[y_start:y_end, :]
        y_offset = y_start

    # --- Multi-scale Template Matching ---
    best_val = -1
    best_loc = None
    best_scale = 1.0
    th, tw = template.shape[:2]

    # Don't bother searching if the ROI is smaller than the template
    if img_to_search.shape[0] < th or img_to_search.shape[1] < tw:
         return None, None

    for scale in [0.8, 0.9, 1.0, 1.1, 1.2]:
        new_w = max(1, int(tw * scale))
        new_h = max(1, int(th * scale))
        if new_w > img_to_search.shape[1] or new_h > img_to_search.shape[0]:
            continue
            
        resized = cv2.resize(template, (new_w, new_h), interpolation=cv2.INTER_AREA)
        res = cv2.matchTemplate(img_to_search, resized, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(res)
        
        if max_val > best_val:
            best_val = max_val
            best_loc = max_loc
            best_scale = scale

    threshold = 0.50  # Keep aggressive threshold but relying on ROI for safety
    if best_val >= threshold and best_loc is not None:
        w = int(tw * best_scale)
        h = int(th * best_scale)
        
        # Adjust Y coordinate back to global image space
        global_y = best_loc[1] + y_offset
        center_x = best_loc[0] + (w // 2)
        
        return center_x, (best_loc[0], global_y, w, h)

    return None, None
