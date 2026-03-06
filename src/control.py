import time
import sys
import ctypes
from ctypes import wintypes

# --- Win32 API Constants & Structures ---
USER32 = ctypes.windll.user32

INPUT_KEYBOARD = 1
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_SCANCODE = 0x0008

# Map virtual key to scan code
VK_SHIFT = 0x10

class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]

class INPUT(ctypes.Structure):
    class _INPUT(ctypes.Union):
        _fields_ = [("ki", KEYBDINPUT)]
    _anonymous_ = ("_input",)
    _fields_ = [("type", wintypes.DWORD), ("_input", _INPUT)]

def _send_input(key_code, is_up=False):
    """Internal helper to send a keystroke via SendInput."""
    # Minecraft (DirectX) prefers scan codes
    scan_code = USER32.MapVirtualKeyW(key_code, 0)
    
    flags = KEYEVENTF_SCANCODE
    if is_up:
        flags |= KEYEVENTF_KEYUP
        
    ki = KEYBDINPUT(0, scan_code, flags, 0, None)
    input_obj = INPUT(INPUT_KEYBOARD, INPUT._INPUT(ki))
    USER32.SendInput(1, ctypes.byref(input_obj), ctypes.sizeof(input_obj))

def key_down(key_code):
    _send_input(key_code, is_up=False)

def key_up(key_code):
    _send_input(key_code, is_up=True)


# --- Mouse Input ---
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
INPUT_MOUSE = 0

class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", ctypes.c_long),
        ("dy", ctypes.c_long),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]

class INPUT_MOUSE_UNION(ctypes.Union):
    _fields_ = [("ki", KEYBDINPUT), ("mi", MOUSEINPUT)]

class INPUT_EX(ctypes.Structure):
    _anonymous_ = ("_input",)
    _fields_ = [("type", wintypes.DWORD), ("_input", INPUT_MOUSE_UNION)]

def right_click():
    """Send a right-click (press + release) for Game A timing."""
    import time as _time

    def _mouse_event(flags):
        mi = MOUSEINPUT(0, 0, 0, flags, 0, None)
        inp = INPUT_EX(INPUT_MOUSE, INPUT_MOUSE_UNION(mi=mi))
        USER32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))

    _mouse_event(MOUSEEVENTF_RIGHTDOWN)
    _time.sleep(0.05)
    _mouse_event(MOUSEEVENTF_RIGHTUP)

class SimplePID:
    def __init__(self, Kp, Ki, Kd):
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd

        self.previous_error = 0
        self.integral = 0
        self.last_time = time.time()

    def update(self, setpoint, current_value):
        current_time = time.time()
        dt = current_time - self.last_time
        if dt <= 0.0:
            dt = 1e-16

        error = setpoint - current_value

        self.integral += error * dt
        derivative = (error - self.previous_error) / dt

        output = (self.Kp * error) + (self.Ki * self.integral) + (self.Kd * derivative)

        self.previous_error = error
        self.last_time = current_time

        return output

    def reset(self):
        self.previous_error = 0
        self.integral = 0
        self.last_time = time.time()

def apply_control(pid_output, current_shift_state):
    """
    Applies keyboard control based on the PID output.
    Positive output means we need to move right (hold shift).
    Negative output means we need to move left (release shift).
    """
    THRESHOLD = 0.3
    new_state = current_shift_state

    if pid_output > THRESHOLD:
        if not current_shift_state:
            key_down(VK_SHIFT)
            new_state = True
    elif pid_output < -THRESHOLD:
        if current_shift_state:
            key_up(VK_SHIFT)
            new_state = False

    return new_state

def reset_controls(current_shift_state):
    """Safety function to release held keys"""
    if current_shift_state:
        key_up(VK_SHIFT)
    return False
