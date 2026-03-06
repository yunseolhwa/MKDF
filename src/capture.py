import cv2
import numpy as np

# Win32 API for window-specific capture (works even when occluded)
_win32_available = False
try:
    import win32gui
    import win32ui
    import win32con
    import ctypes
    _win32_available = True
except ImportError:
    pass

def capture_window_win32(hwnd):
    """
    Capture a specific window using Win32 PrintWindow API.
    Works even if the window is behind other windows.
    Returns BGR numpy array or None on failure.
    """
    if not _win32_available:
        return None

    try:
        # Get client area dimensions
        left, top, right, bottom = win32gui.GetClientRect(hwnd)
        w = right - left
        h = bottom - top
        if w <= 0 or h <= 0:
            return None

        hwndDC = win32gui.GetWindowDC(hwnd)
        mfcDC = win32ui.CreateDCFromHandle(hwndDC)
        saveDC = mfcDC.CreateCompatibleDC()

        saveBitMap = win32ui.CreateBitmap()
        saveBitMap.CreateCompatibleBitmap(mfcDC, w, h)
        saveDC.SelectObject(saveBitMap)

        # PW_RENDERFULLCONTENT = 2 (captures DirectX/OpenGL content on some configs)
        # PW_CLIENTONLY = 1
        result = ctypes.windll.user32.PrintWindow(hwnd, saveDC.GetSafeHdc(), 3)

        bmpinfo = saveBitMap.GetInfo()
        bmpstr = saveBitMap.GetBitmapBits(True)

        img = np.frombuffer(bmpstr, dtype=np.uint8)
        img = img.reshape((bmpinfo['bmHeight'], bmpinfo['bmWidth'], 4))  # BGRA
        img_bgr = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

        # Cleanup
        win32gui.DeleteObject(saveBitMap.GetHandle())
        saveDC.DeleteDC()
        mfcDC.DeleteDC()
        win32gui.ReleaseDC(hwnd, hwndDC)

        return img_bgr
    except Exception as e:
        return None


def capture_screen(sct, region, hwnd=None):
    """
    Captures the game screen.
    If hwnd is provided and win32 is available, uses PrintWindow (works behind other windows).
    Otherwise falls back to mss region capture.
    """
    if hwnd is not None and _win32_available:
        img = capture_window_win32(hwnd)
        if img is not None:
            return img

    # Fallback: mss screen-region capture
    sct_img = sct.grab(region)
    img = np.array(sct_img)
    img_bgr = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
    return img_bgr
