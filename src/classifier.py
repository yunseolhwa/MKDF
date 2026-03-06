"""
Minigame Classifier — Determines which minigame (A, B, or C) is active.

Strategy:
  1. Detect if any minigame UI is visible on screen
  2. Classify which type based on visual features:
     - Game A: Has a moving marker approaching a green zone (timing game)
     - Game B: Has a central gauge icon + progress bar (gauge control)
     - Game C: Has a green bar + cursor that moves (PID tracking)

TODO: Extract unique templates from actual gameplay screenshots for each game.
"""
import cv2
import numpy as np
import os

_TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'templates')


def _load_template(name):
    """Load a template image from the templates/ directory."""
    path = os.path.join(_TEMPLATE_DIR, name)
    if os.path.exists(path):
        return cv2.imread(path)
    return None


# Pre-load templates at import time
_game_a_tpl = _load_template('game_a_indicator.png')
_game_b_tpl = _load_template('game_b_indicator.png')
# Game C reuses green bar detection, no special template needed


def detect_minigame_ui(frame):
    """
    Quick check: is ANY minigame UI visible on screen?
    Returns True if a minigame-like UI element is detected.

    Current heuristic: look for a significant green bar region
    in the middle portion of the screen.
    """
    h, w = frame.shape[:2]
    # Focus on the center region
    roi = frame[h // 4 : 3 * h // 4, w // 4 : 3 * w // 4]

    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    # Broad green detection
    mask = cv2.inRange(hsv, np.array([35, 50, 50]), np.array([85, 255, 255]))
    green_ratio = np.count_nonzero(mask) / mask.size

    # If more than 1% of the center region is green, a game UI might be present
    return green_ratio > 0.01


def classify_minigame(frame):
    """
    Classify the active minigame as 'A', 'B', or 'C'.
    Returns: 'A', 'B', 'C', or None if classification fails.

    TODO: This is a stub. Real classification requires game-specific
    template matching or feature analysis once templates are collected.
    """
    # --- Template matching approach ---
    if _game_a_tpl is not None:
        res = cv2.matchTemplate(frame, _game_a_tpl, cv2.TM_CCOEFF_NORMED)
        if res.max() > 0.7:
            return 'A'

    if _game_b_tpl is not None:
        res = cv2.matchTemplate(frame, _game_b_tpl, cv2.TM_CCOEFF_NORMED)
        if res.max() > 0.7:
            return 'B'

    # Default: if green bar is found and no A/B templates matched, assume C
    # (This is the most common scenario currently)
    return 'C'
