from flask import Flask, render_template, request, Response, jsonify
import cv2
import numpy as np
import os
import tempfile
import threading
from werkzeug.utils import secure_filename
import time
from mini_game_auto import find_green_bar, find_cursor, SimplePID, load_cursor_template, CURSOR_HSV_LOWER, CURSOR_HSV_UPPER

TARGET_HSV_LOWER = [35, 50, 50]
TARGET_HSV_UPPER = [85, 255, 255]

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.path.join(tempfile.gettempdir(), 'minigame_uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Load cursor template for web debugger too
_web_cursor_template = load_cursor_template()

# Global configuration that can be updated from web
config = {
    'target_h_min': TARGET_HSV_LOWER[0], 'target_s_min': TARGET_HSV_LOWER[1], 'target_v_min': TARGET_HSV_LOWER[2],
    'target_h_max': TARGET_HSV_UPPER[0], 'target_s_max': TARGET_HSV_UPPER[1], 'target_v_max': TARGET_HSV_UPPER[2],
    'cursor_h_min': CURSOR_HSV_LOWER[0], 'cursor_s_min': CURSOR_HSV_LOWER[1], 'cursor_v_min': CURSOR_HSV_LOWER[2],
    'cursor_h_max': CURSOR_HSV_UPPER[0], 'cursor_s_max': CURSOR_HSV_UPPER[1], 'cursor_v_max': CURSOR_HSV_UPPER[2],
    'kp': 50, 'kd': 10
}

current_video_path = None
video_thread_lock = threading.Lock()

def process_frame(frame, pid):
    global config

    lower_target = np.array([config['target_h_min'], config['target_s_min'], config['target_v_min']])
    upper_target = np.array([config['target_h_max'], config['target_s_max'], config['target_v_max']])
    lower_cursor = [config['cursor_h_min'], config['cursor_s_min'], config['cursor_v_min']]
    upper_cursor = [config['cursor_h_max'], config['cursor_s_max'], config['cursor_v_max']]

    target_center_x, target_bbox = find_green_bar(frame, lower_target, upper_target)

    # Use template matching (primary) with HSV fallback
    best_cursor_x, best_bbox = find_cursor(
        frame,
        lower_hsv=lower_cursor,
        upper_hsv=upper_cursor,
        template=_web_cursor_template,
        use_template=(_web_cursor_template is not None)
    )

    if target_center_x is not None:
        tx, ty, tw, th = target_bbox
        cv2.rectangle(frame, (tx, ty), (tx+tw, ty+th), (0, 255, 0), 2)
        cv2.circle(frame, (target_center_x, ty + th // 2), 5, (0, 0, 255), -1)
        cv2.putText(frame, "Target", (tx, ty - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    if best_cursor_x is not None:
        cx, cy, cw, ch = best_bbox
        cv2.rectangle(frame, (cx, cy), (cx+cw, cy+ch), (255, 0, 0), 2)
        cv2.circle(frame, (best_cursor_x, cy + ch // 2), 5, (255, 255, 0), -1)
        cv2.putText(frame, "Cursor", (cx, cy - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

    if target_center_x is not None and best_cursor_x is not None:
        cy_center = best_bbox[1] + best_bbox[3] // 2
        ty_center = target_bbox[1] + target_bbox[3] // 2

        pid.Kp = config['kp'] / 100.0
        pid.Kd = config['kd'] / 100.0
        pid.Ki = 0.0

        output = pid.update(target_center_x, best_cursor_x)
        cv2.putText(frame, f"PID Output: {output:.2f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
        cv2.line(frame, (best_cursor_x, cy_center), (target_center_x, ty_center), (255, 255, 255), 2)

    return frame


def generate_frames():
    global current_video_path

    if not current_video_path or not os.path.exists(current_video_path):
        # Yield a blank frame
        blank = np.zeros((720, 1280, 3), dtype=np.uint8)
        cv2.putText(blank, "No Video Uploaded", (500, 360), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        _, buffer = cv2.imencode('.jpg', blank)
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        return

    cap = cv2.VideoCapture(current_video_path)
    pid = SimplePID(Kp=0.5, Ki=0.0, Kd=0.1)

    while cap.isOpened():
        with video_thread_lock:
            # Check if video was changed or removed
            if not current_video_path:
                break

        ret, frame = cap.read()
        if not ret:
            # Restart video loop
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            continue

        # Process the frame with current config
        processed_frame = process_frame(frame.copy(), pid)

        # Add a sleep to simulate playback speed roughly
        time.sleep(0.03)

        ret, buffer = cv2.imencode('.jpg', processed_frame)
        if not ret:
            continue

        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

    cap.release()

@app.route('/')
def index():
    return render_template('index.html', config=config)

@app.route('/upload', methods=['POST'])
def upload_file():
    global current_video_path
    if 'video' not in request.files:
        return jsonify({'error': 'No video file part'}), 400

    file = request.files['video']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        with video_thread_lock:
            current_video_path = filepath

        return jsonify({'success': True, 'message': 'Video uploaded successfully'})

@app.route('/update_config', methods=['POST'])
def update_config():
    global config
    data = request.json
    for key, value in data.items():
        if key in config:
            config[key] = int(value)
    return jsonify({'success': True, 'config': config})

@app.route('/export_config', methods=['GET'])
def export_config():
    global config
    return jsonify(config)

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
