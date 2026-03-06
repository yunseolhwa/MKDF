"""
띵타이쿤 낚시 미니게임 자동화 — Main Orchestrator

Top-level state machine:
  IDLE → CLASSIFY → GAME_A / GAME_B / GAME_C → COOLDOWN → IDLE (loop)

Controls:
  Q — Quit
"""
import time
import os
import sys
import cv2
import mss
import traceback
import keyboard

from src.capture import _win32_available, capture_screen, win32gui
from src.bot_state import TopState, GameResult
from src.classifier import detect_minigame_ui, classify_minigame
from src.game_a import GameA
from src.game_b import GameB
from src.game_c import GameC
from src.control import reset_controls
from src.utils import draw_status_window

try:
    import pygetwindow as gw
except ImportError:
    gw = None

# --- Constants ---
GAME_REGION = {"top": 0, "left": 0, "width": 1280, "height": 720}
COOLDOWN_SECONDS = 2.0


def find_minecraft_window():
    """Find the Minecraft window and return (window, hwnd)."""
    minecraft_window = None
    mc_hwnd = None

    if gw:
        windows = gw.getWindowsWithTitle('Minecraft')
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

    return minecraft_window, mc_hwnd


def main():
    print("=" * 60)
    print("  ThingTycoon Fishing Minigame Bot")
    print("  State Machine: IDLE > CLASSIFY > GAME > COOLDOWN")
    print("=" * 60)
    print("  Q - Quit")
    print("=" * 60)

    # Find Minecraft
    minecraft_window, mc_hwnd = find_minecraft_window()

    # Initialize game modules
    game_a = GameA()
    game_b = GameB()
    game_c = GameC()

    # Screen capture
    sct = mss.mss()

    # State
    state = TopState.IDLE
    running = True
    cooldown_start = 0
    shift_held = False  # Global safety tracker

    def quit_bot():
        nonlocal running
        running = False
        print("Quit signal received.")

    keyboard.add_hotkey('q', quit_bot)

    print("Main loop started. Press 'Q' to quit.")

    try:
        while running:
            # Update window position
            if minecraft_window:
                try:
                    GAME_REGION['top'] = minecraft_window.top
                    GAME_REGION['left'] = minecraft_window.left
                except Exception:
                    pass

            # Capture frame
            frame = capture_screen(sct, GAME_REGION, hwnd=mc_hwnd)
            if frame is None or frame.size == 0:
                time.sleep(0.1)
                continue

            # ==========================================
            #  TOP-LEVEL STATE MACHINE
            # ==========================================

            if state == TopState.IDLE:
                # Wait for minigame UI to appear
                if detect_minigame_ui(frame):
                    state = TopState.CLASSIFY
                    print(f"[FSM] IDLE → CLASSIFY")
                else:
                    time.sleep(0.01)  # Save CPU

            elif state == TopState.CLASSIFY:
                # Determine which minigame
                game_type = classify_minigame(frame)
                if game_type == 'A':
                    game_a.reset()
                    state = TopState.GAME_A
                    print(f"[FSM] CLASSIFY → GAME_A")
                elif game_type == 'B':
                    game_b.reset()
                    state = TopState.GAME_B
                    print(f"[FSM] CLASSIFY → GAME_B")
                elif game_type == 'C':
                    game_c.reset()
                    state = TopState.GAME_C
                    print(f"[FSM] CLASSIFY → GAME_C")
                else:
                    state = TopState.IDLE
                    print(f"[FSM] CLASSIFY → IDLE (classification failed)")

            elif state == TopState.GAME_A:
                result = game_a.tick(frame)
                if result in (GameResult.SUCCESS, GameResult.FAILED):
                    print(f"[FSM] GAME_A → COOLDOWN ({result.name})")
                    state = TopState.COOLDOWN
                    cooldown_start = time.time()

            elif state == TopState.GAME_B:
                result = game_b.tick(frame)
                if result in (GameResult.SUCCESS, GameResult.FAILED):
                    game_b.reset()  # Release keys
                    print(f"[FSM] GAME_B → COOLDOWN ({result.name})")
                    state = TopState.COOLDOWN
                    cooldown_start = time.time()

            elif state == TopState.GAME_C:
                result = game_c.tick(frame)
                if result in (GameResult.SUCCESS, GameResult.FAILED):
                    game_c.reset()  # Release keys
                    print(f"[FSM] GAME_C → COOLDOWN ({result.name})")
                    state = TopState.COOLDOWN
                    cooldown_start = time.time()

            elif state == TopState.COOLDOWN:
                elapsed = time.time() - cooldown_start
                if elapsed >= COOLDOWN_SECONDS:
                    print(f"[FSM] COOLDOWN → IDLE")
                    state = TopState.IDLE
                else:
                    time.sleep(0.05)

            # ==========================================
            #  Status Window (always rendered)
            # ==========================================
            if state != TopState.IDLE:
                status_img = draw_status_window(state)
                cv2.imshow('Status', status_img)
                cv2.waitKey(1)
            else:
                try:
                    cv2.destroyWindow('Status')
                except cv2.error:
                    pass

    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Error in main loop: {e}")
        traceback.print_exc()
    finally:
        # Safety: release all keys
        game_a.reset() if hasattr(game_a, 'reset') else None
        game_b.reset()
        game_c.reset()
        reset_controls(False)
        cv2.destroyAllWindows()
        sct.close()
        keyboard.unhook_all()
        print("Exited cleanly.")


if __name__ == "__main__":
    main()
