"""
Game B — Gauge Control

The player holds Shift to slow down a filling gauge icon in the center.
The goal is to reach the finish line without the gauge overflowing.

Logic:
  1. Detect the gauge icon fill level (how full it is)
  2. Detect the progress toward the finish line
  3. If gauge is filling too fast → release Shift
     If gauge is low → hold Shift to speed up
  4. Return SUCCESS when finish line is reached, FAILED if gauge overflows
"""
import cv2
import numpy as np
from src.bot_state import GameResult
from src.control import key_down, key_up, VK_SHIFT


class GameB:
    def __init__(self):
        self.shift_held = False
        self.frames_since_start = 0

    def reset(self):
        if self.shift_held:
            key_up(VK_SHIFT)
        self.shift_held = False
        self.frames_since_start = 0

    def tick(self, frame):
        """
        Process one frame of Game B.
        Returns GameResult.RUNNING, .SUCCESS, or .FAILED
        """
        self.frames_since_start += 1

        # TODO: Implement actual detection logic
        # 1. Find the central gauge icon
        # 2. Measure its fill level (pixel ratio or template match)
        # 3. Find the progress bar / finish line
        # 4. Control Shift based on fill level

        # Stub: return RUNNING until real logic is implemented
        return GameResult.RUNNING
