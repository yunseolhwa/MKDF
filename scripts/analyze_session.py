"""
Session Analyzer — Frame-by-frame analysis of recorded bot sessions.

Usage:
    py scripts/analyze_session.py debug_recordings/session_YYYYMMDD_HHMMSS_log.json

Opens the corresponding video and lets you step through frame-by-frame,
showing detection data from the JSON log on each frame.

Controls:
    → / D    Next frame
    ← / A    Previous frame
    SPACE    Play/Pause
    G        Jump to a specific frame (enter in console)
    M        Jump to next MISS frame (target or cursor not detected)
    Q        Quit
"""

import json
import sys
import os
import cv2


def load_session(log_path):
    with open(log_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def find_video(log_path):
    """Derive video path from log path."""
    base = log_path.replace('_log.json', '.avi')
    if os.path.exists(base):
        return base
    return None


def draw_overlay(frame, entry, total_frames):
    h, w = frame.shape[:2]
    lines = [
        f"Frame {entry['frame']}/{total_frames}",
        f"Target: {'OK' if entry['target_x'] else 'MISS'} x={entry.get('target_x', '-')}",
        f"Cursor: {'OK' if entry['cursor_x'] else 'MISS'} x={entry.get('cursor_x', '-')}",
        f"PID: {entry['pid_output']:.2f} Shift:{'DN' if entry['shift'] else 'UP'} Bot:{'ON' if entry['bot_on'] else 'OFF'}",
    ]
    # Highlight MISS frames
    is_miss = entry['target_x'] is None or entry['cursor_x'] is None
    panel_color = (0, 0, 80) if is_miss else (0, 40, 0)

    overlay = frame.copy()
    cv2.rectangle(overlay, (0, h - 90), (w, h), panel_color, -1)
    cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)

    for i, line in enumerate(lines):
        color = (0, 0, 255) if 'MISS' in line else (255, 255, 255)
        cv2.putText(frame, line, (10, h - 72 + i * 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1, cv2.LINE_AA)
    return frame


def main():
    if len(sys.argv) < 2:
        print("Usage: py scripts/analyze_session.py <session_log.json>")
        print("  Available logs:")
        debug_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'debug_recordings')
        if os.path.exists(debug_dir):
            for f in sorted(os.listdir(debug_dir)):
                if f.endswith('_log.json'):
                    print(f"    {os.path.join('debug_recordings', f)}")
        sys.exit(1)

    log_path = sys.argv[1]
    data = load_session(log_path)
    video_path = find_video(log_path)

    if not video_path:
        print(f"Video not found for {log_path}")
        sys.exit(1)

    print(f"Log: {log_path} ({len(data)} frames)")
    print(f"Video: {video_path}")

    # Find miss frames
    miss_frames = [i for i, e in enumerate(data) if e['target_x'] is None or e['cursor_x'] is None]
    miss_pct = len(miss_frames) / len(data) * 100 if data else 0
    print(f"MISS frames: {len(miss_frames)} ({miss_pct:.1f}%)")

    cap = cv2.VideoCapture(video_path)
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    idx = 0
    playing = False

    cv2.namedWindow('Session Analyzer')

    while True:
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ret, frame = cap.read()
        if not ret:
            break

        if idx < len(data):
            frame = draw_overlay(frame, data[idx], total)

        cv2.imshow('Session Analyzer', frame)

        wait = 30 if playing else 0
        key = cv2.waitKey(wait) & 0xFF

        if key == ord('q'):
            break
        elif key == ord('d') or key == 83:  # → or D
            idx = min(idx + 1, total - 1)
            playing = False
        elif key == ord('a') or key == 81:  # ← or A
            idx = max(idx - 1, 0)
            playing = False
        elif key == ord(' '):
            playing = not playing
        elif key == ord('g'):
            try:
                n = int(input(f"Jump to frame (0-{total-1}): "))
                idx = max(0, min(n, total - 1))
            except ValueError:
                pass
            playing = False
        elif key == ord('m'):
            # Jump to next miss frame
            next_miss = [i for i in miss_frames if i > idx]
            if next_miss:
                idx = next_miss[0]
                print(f"Jumped to MISS frame {idx}")
            else:
                print("No more MISS frames after current position")
            playing = False
        elif playing:
            idx = min(idx + 1, total - 1)
            if idx >= total - 1:
                playing = False

    cap.release()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
