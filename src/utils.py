"""
Utils — Status Window and Session Logging for the 띵타이쿤 bot.
"""
import cv2
import numpy as np
import os
import json
import time
from datetime import datetime
from src.bot_state import TopState


# ── Status Window ──────────────────────────────────────────

# Color mapping for each TopState (BGR)
_STATE_COLORS = {
    TopState.IDLE:     (0, 0, 255),    # Red
    TopState.CLASSIFY: (255, 165, 0),  # Orange
    TopState.GAME_A:   (0, 255, 0),    # Green
    TopState.GAME_B:   (0, 255, 0),    # Green
    TopState.GAME_C:   (0, 255, 0),    # Green
    TopState.COOLDOWN: (0, 255, 255),  # Yellow
}


def draw_status_window(state):
    """Generates a solid-color image representing the current TopState."""
    color = _STATE_COLORS.get(state, (128, 128, 128))
    img = np.zeros((150, 250, 3), dtype=np.uint8)
    img[:] = color

    text_color = (0, 0, 0) if state != TopState.IDLE else (255, 255, 255)
    cv2.putText(img, state.name, (30, 85), cv2.FONT_HERSHEY_SIMPLEX, 1, text_color, 2)
    return img


# ── Session Logger ─────────────────────────────────────────

class SessionLogger:
    def __init__(self, base_dir):
        self.debug_dir = os.path.join(base_dir, 'debug_recordings')
        os.makedirs(self.debug_dir, exist_ok=True)

        self.session_ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.recording_path = os.path.join(self.debug_dir, f'session_{self.session_ts}.avi')
        self.log_path = os.path.join(self.debug_dir, f'session_{self.session_ts}_log.json')

        self.video_writer = None
        self.frame_log = []

        self.frame_count = 0
        self.target_found_count = 0
        self.cursor_found_count = 0
        self.fps_time = time.time()
        self.fps = 0.0

        print(f"Auto-recording to: {self.recording_path}")

    def update_stats(self, target_x, cursor_x):
        self.frame_count += 1
        if target_x is not None:
            self.target_found_count += 1
        if cursor_x is not None:
            self.cursor_found_count += 1

        if self.frame_count % 30 == 0:
            now = time.time()
            elapsed = now - self.fps_time
            self.fps = 30.0 / elapsed if elapsed > 0 else 0
            self.fps_time = now

    def record_frame_data(self, target_x, target_bbox, cursor_x, cursor_bbox,
                          pid_output, shift_state, bot_on, state):
        self.frame_log.append({
            'frame': self.frame_count,
            'time': time.time(),
            'target_x': target_x,
            'target_bbox': list(target_bbox) if target_bbox else None,
            'cursor_x': cursor_x,
            'cursor_bbox': list(cursor_bbox) if cursor_bbox else None,
            'pid_output': round(pid_output, 3),
            'shift': shift_state,
            'bot_on': bot_on,
            'state': state.name if hasattr(state, 'name') else str(state),
        })

    def save_snapshot(self, frame, debug_frame):
        ts = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]
        snap_path = os.path.join(self.debug_dir, f'snapshot_{ts}.png')
        raw_path = os.path.join(self.debug_dir, f'raw_{ts}.png')
        cv2.imwrite(snap_path, debug_frame)
        cv2.imwrite(raw_path, frame)
        print(f"Snapshot saved: {snap_path}")

    def close(self):
        if self.video_writer:
            self.video_writer.release()
            print(f"Recording saved: {self.recording_path}")

        if self.frame_log:
            with open(self.log_path, 'w', encoding='utf-8') as f:
                json.dump(self.frame_log, f)
            print(f"Frame log saved: {self.log_path} ({len(self.frame_log)} frames)")

        if self.frame_count > 0:
            stats_path = os.path.join(self.debug_dir, f'session_{self.session_ts}_stats.txt')
            with open(stats_path, 'w', encoding='utf-8') as f:
                f.write(f"Session: {self.session_ts}\n")
                f.write(f"{'=' * 40}\n")
                f.write(f"Total frames: {self.frame_count}\n")
                f.write(f"Target hit rate: {self.target_found_count}/{self.frame_count} "
                        f"({self.target_found_count / self.frame_count * 100:.1f}%)\n")
                f.write(f"Cursor hit rate: {self.cursor_found_count}/{self.frame_count} "
                        f"({self.cursor_found_count / self.frame_count * 100:.1f}%)\n")
                f.write(f"FPS: {self.fps:.1f}\n")
            print(f"Stats saved: {stats_path}")
