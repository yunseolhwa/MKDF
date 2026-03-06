"""
Game A — Timing Right-Click

The player sees a cursor/marker moving along a bar.
When it enters the green zone, right-click must be pressed.

Logic:
  1. Detect the bar and the green zone boundaries
  2. Detect the moving marker position
  3. When marker X is inside the green zone X range → right_click()
  4. Return SUCCESS after clicking, FAILED if bar disappears
"""
import cv2
import numpy as np
from src.bot_state import GameResult
from src.control import right_click


class GameA:
    def __init__(self):
        self.clicked = False
        self.frames_since_start = 0

    def reset(self):
        self.clicked = False
        self.frames_since_start = 0

    def tick(self, frame):
        """
        Process one frame of Game A.
        Returns GameResult.RUNNING, .SUCCESS, or .FAILED
        """
        self.frames_since_start += 1

        # TODO: Implement actual detection logic
        # 1. Find the bar (horizontal element)
        # 2. Find the green zone within the bar
        # 3. Find the moving marker/cursor
        # 4. If marker is in green zone → click

        # Stub: return RUNNING until real logic is implemented
        return GameResult.RUNNING
