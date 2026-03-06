import json
import cv2
import os

log_path = r'C:\Users\0UA\Desktop\start-main\debug_recordings\session_20260305_200331_log.json'
vid_path = r'C:\Users\0UA\Desktop\start-main\debug_recordings\session_20260305_200331.avi'
out_dir = r'C:\Users\0UA\.gemini\antigravity\brain\1a0dac60-c412-4b9b-921e-57ee4147788c'

with open(log_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

# The user said EVERYTHING was a false positive. Let's just grab the first 5 frames where the bot thought it found the cursor.
false_positive_frames = [d['frame'] for d in data if d['cursor_x'] is not None]

print(f"Total frames with 'detected' cursor: {len(false_positive_frames)}")

selected_frames = []
if false_positive_frames:
    step = max(1, len(false_positive_frames) // 5)
    selected_frames = false_positive_frames[::step][:5]

print(f"Capturing frames: {selected_frames}")

cap = cv2.VideoCapture(vid_path)

output_images = []
for frame_idx in selected_frames:
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx - 1)
    ret, frame = cap.read()
    if ret:
        out_path = os.path.join(out_dir, f'false_positive_{frame_idx}.png')
        cv2.imwrite(out_path, frame)
        output_images.append(out_path)

cap.release()

report_path = os.path.join(out_dir, 'false_positive_report.md')
with open(report_path, 'w', encoding='utf-8') as f:
    f.write("# False Positives Debug Report\n\n")
    f.write("User reported that all detections in this session were false positives. Let's look at what the bot actually matched.\n\n")
    
    for p in output_images:
        f.write(f"![False Positive Frame {os.path.basename(p)}]({p})\n\n")

print("False positive report generated.")
