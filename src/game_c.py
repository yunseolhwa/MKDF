"""
Game C — Cursor PID Tracking

The player holds Shift to keep a cursor aligned with a green bar.
Uses a PID controller for smooth tracking.

This is the most mature game logic, previously in mini_game_auto.py.
"""
import cv2
import numpy as np
from src.bot_state import GameResult
from src.vision import find_green_bar, find_cursor, load_cursor_template
from src.control import SimplePID, key_down, key_up, VK_SHIFT

# HSV range for green bar detection
TARGET_HSV_LOWER = [35, 50, 50]
TARGET_HSV_UPPER = [85, 255, 255]

# PID constants
KP = 2.5
KD = 0.5
PID_THRESHOLD = 0.3


class GameC:
    def __init__(self):
        self.pid = SimplePID(Kp=KP, Ki=0.0, Kd=KD)
        self.cursor_template = load_cursor_template()
        self.shift_held = False
        self.frames_since_start = 0
        self.lost_frames = 0  # Consecutive frames without green bar

    def reset(self):
        if self.shift_held:
            key_up(VK_SHIFT)
        self.shift_held = False
        self.pid.reset()
        self.frames_since_start = 0
        self.lost_frames = 0

    def tick(self, frame):
        """
        Process one frame of Game C.
        Returns GameResult.RUNNING, .SUCCESS, or .FAILED
        """
        self.frames_since_start += 1

        # 1. Find the target green bar
        target_x, target_bbox = find_green_bar(frame, TARGET_HSV_LOWER, TARGET_HSV_UPPER)

        if target_x is None:
            self.lost_frames += 1
            # If we lose the bar for too many frames, the game ended
            if self.lost_frames > 30:
                self._release_shift()
                return GameResult.SUCCESS  # Game likely finished
            self._release_shift()
            self.pid.reset()
            return GameResult.RUNNING

        self.lost_frames = 0  # Reset lost counter

        # 2. Find the cursor within the bar's ROI
        cursor_x, cursor_bbox = find_cursor(
            frame,
            roi_bbox=target_bbox,
            template=self.cursor_template,
            use_template=(self.cursor_template is not None)
        )

        if cursor_x is None:
            # Bar visible but cursor not found
            self._release_shift()
            self.pid.reset()
            return GameResult.RUNNING

        # 3. PID control
        pid_output = self.pid.update(target_x, cursor_x)

        if pid_output > PID_THRESHOLD:
            if not self.shift_held:
                key_down(VK_SHIFT)
                self.shift_held = True
        elif pid_output < -PID_THRESHOLD:
            if self.shift_held:
                key_up(VK_SHIFT)
                self.shift_held = False

        return GameResult.RUNNING

    def _release_shift(self):
        if self.shift_held:
            key_up(VK_SHIFT)
            self.shift_held = False
