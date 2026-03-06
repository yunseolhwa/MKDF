import json
import cv2
import os
import shutil

log_path = r'C:\Users\0UA\Desktop\start-main\debug_recordings\session_20260305_195611_log.json'
vid_path = r'C:\Users\0UA\Desktop\start-main\debug_recordings\session_20260305_195611.avi'
out_dir = r'C:\Users\0UA\.gemini\antigravity\brain\1a0dac60-c412-4b9b-921e-57ee4147788c'

with open(log_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Find frames where cursor was missed
miss_frames = [d['frame'] for d in data if d['cursor_x'] is None]

print(f"Total miss frames: {len(miss_frames)}")

# Select a few evenly spaced miss frames to capture
selected_frames = []
if miss_frames:
    step = max(1, len(miss_frames) // 4)
    selected_frames = miss_frames[::step][:5]

print(f"Capturing frames: {selected_frames}")

cap = cv2.VideoCapture(vid_path)

output_images = []
for frame_idx in selected_frames:
    # Set video position (OpenCV frames are 0-indexed, our log frame_count starts at 1)
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx - 1)
    ret, frame = cap.read()
    if ret:
        out_path = os.path.join(out_dir, f'miss_frame_{frame_idx}.png')
        cv2.imwrite(out_path, frame)
        output_images.append(out_path)

cap.release()

# Generate markdown report
report_path = os.path.join(out_dir, 'debug_report.md')
with open(report_path, 'w', encoding='utf-8') as f:
    f.write("# Bot Session Debug Report\n\n")
    f.write(f"**Session:** {os.path.basename(vid_path)}\n")
    f.write(f"**Missing Cursor Frames:** {len(miss_frames)}\n\n")
    
    if output_images:
        f.write("## Sample Failed Frames (Cursor NOT detected)\n\n")
        f.write("Below are frames where the bot failed to find the cursor. We can inspect these to see why template matching or HSV failed (e.g., occlusion, motion blur, particle effects).\n\n")
        for p in output_images:
            f.write(f"![Frame {os.path.basename(p)}]({p})\n\n")
    else:
        f.write("No miss frames could be extracted.\n")

print("Report generated.")
