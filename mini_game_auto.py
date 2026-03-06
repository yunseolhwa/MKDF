import time
import os
import cv2
import mss
import sys
import traceback
import numpy as np
# Import custom modules
from src.capture import _win32_available, capture_screen, win32gui
from src.vision import find_green_bar, find_cursor, load_cursor_template
from src.control import SimplePID, apply_control, reset_controls
from src.utils import draw_debug_info, SessionLogger, draw_status_window
from src.bot_state import BotState
import keyboard

try:
    import pygetwindow as gw
except ImportError:
    print('Warning: pygetwindow not found. Window tracking disabled.')
    gw = None

# --- Constants ---
GAME_REGION = {"top": 0, "left": 0, "width": 1280, "height": 720}

# Hardcoded detection and control parameters
TARGET_HSV_LOWER = [35, 50, 50]
TARGET_HSV_UPPER = [85, 255, 255]
KP = 2.5
KD = 0.5

def main():
    print("=" * 60)
    print("  Mini-Game Auto Bot (Modularized + ROI Filtering)")
    print("=" * 60)
    print("Controls:")
    print("  q — Exit (saves recording + analysis log)")
    print("  s — Save debug snapshot")
    print("=" * 60)

    # Load resources
    cursor_template = load_cursor_template()
    use_template = cursor_template is not None
    if use_template:
        print("Mode: TEMPLATE MATCHING (Strict ROI Mode)")
    else:
        print("Error: cursor_template.png not found. Bot expects template.")
        sys.exit(1)

    logger = SessionLogger(os.path.dirname(os.path.abspath(__file__)))

    # Initialize Capture & Control
    sct = mss.mss()
    pid = SimplePID(Kp=KP, Ki=0.0, Kd=KD)
    current_shift_state = False

    # Find Minecraft window
    minecraft_window = None
    mc_hwnd = None
    if gw:
        windows = gw.getWindowsWithTitle('Minecraft')
        if windows:
            for win in windows:
                if 'Minecraft' in win.title:
                    minecraft_window = win
                    break

    if minecraft_window:
        GAME_REGION['top'] = minecraft_window.top
        GAME_REGION['left'] = minecraft_window.left
        GAME_REGION['width'] = minecraft_window.width
        GAME_REGION['height'] = minecraft_window.height
        print(f"Tracking Minecraft window at {GAME_REGION['left']}, {GAME_REGION['top']}")

        if _win32_available:
            try:
                mc_hwnd = minecraft_window._hWnd
                print(f"Win32 HWND acquired: {mc_hwnd}")
            except Exception:
                mc_hwnd = win32gui.FindWindow(None, minecraft_window.title)
                if mc_hwnd:
                    print(f"Win32 HWND found by title: {mc_hwnd}")
    else:
        print("Minecraft window not found! Using default top-left screen region.")

    # Hotkey state
    debug_mode = False
    running = True

    def quit_bot():
        nonlocal running
        running = False
        print("Quit signal received.")

    keyboard.add_hotkey('q', quit_bot)

    # --- Main Loop ---
    last_state = BotState.IDLE
    print("Main loop started. Press 'q' to quit.")
    try:
        while running:
            key = -1 # Default
            if minecraft_window:
                try:
                    GAME_REGION['top'] = minecraft_window.top
                    GAME_REGION['left'] = minecraft_window.left
                except Exception:
                    pass

            # 1. Capture Image
            frame = capture_screen(sct, GAME_REGION, hwnd=mc_hwnd)
            if frame is None or frame.size == 0:
                time.sleep(0.1)
                continue

            # 2. Vision Pipeline
            # Find the target green bar
            target_x, target_bbox = find_green_bar(frame, TARGET_HSV_LOWER, TARGET_HSV_UPPER)

            # Find the cursor (ONLY within the vertical bounds of the target_bbox to stop false positives)
            cursor_x, cursor_bbox = find_cursor(
                frame,
                roi_bbox=target_bbox, # This restricts the scan!
                template=cursor_template,
                use_template=use_template
            )

            # 3. State Machine & Control Logic
            pid_output = 0.0
            current_state = BotState.IDLE

            if target_x is not None:
                if cursor_x is not None:
                    current_state = BotState.TRACKING
                else:
                    current_state = BotState.FINISHED

            # Trigger a snapshot on new tracking event for debugging
            if current_state == BotState.TRACKING and last_state != BotState.TRACKING:
                # Use a small delay/re-read to avoid blurry capture? No, use current frame.
                logger.save_snapshot(frame, frame) # Save raw for diagnosis

            if current_state == BotState.TRACKING:
                pid_output = pid.update(target_x, cursor_x)
                current_shift_state = apply_control(pid_output, current_shift_state)
            else:
                current_shift_state = reset_controls(current_shift_state)
                pid.reset()

            last_state = current_state

            # 4. Logging & Debug Drawing
            logger.update_stats(target_x, cursor_x)
            logger.record_frame_data(target_x, target_bbox, cursor_x, cursor_bbox, pid_output, current_shift_state, debug_mode, current_state)
            
            # This overlay logic decides whether to draw the big text panel and write to the video file
            debug_frame = draw_debug_info(frame, target_x, target_bbox, cursor_x, cursor_bbox, pid_output, current_state)
            debug_frame = logger.draw_overlay_and_record(debug_frame, use_template, pid_output, debug_mode, current_shift_state, current_state)

            if debug_mode:
                # In debug mode, show the full detailed vision window
                try: cv2.destroyWindow('Status')
                except cv2.error: pass
                cv2.imshow('Mini-Game Bot (Debug)', debug_frame)
                key = cv2.waitKey(1) & 0xFF
            else:
                try: cv2.destroyWindow('Mini-Game Bot (Debug)')
                except cv2.error: pass
                
                # In runtime mode, logic dictates: only show Status UI if NOT IDLE.
                if current_state != BotState.IDLE:
                    status_img = draw_status_window(current_state)
                    cv2.imshow('Status', status_img)
                    key = cv2.waitKey(1) & 0xFF
                else:
                    try: cv2.destroyWindow('Status')
                    except cv2.error: pass
                    # Sleep to save CPU since waitKey isn't blocking on a window
                    time.sleep(0.01)

    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Error in main loop: {e}")
        traceback.print_exc()
    finally:
        reset_controls(current_shift_state)
        logger.close()
        cv2.destroyAllWindows()
        sct.close()
        print("Exited cleanly.")

if __name__ == "__main__":
    main()
