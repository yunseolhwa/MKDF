import unittest
import numpy as np
import cv2
import time
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from mini_game_auto import find_green_bar, find_cursor, SimplePID

class TestMiniGameBot(unittest.TestCase):
    def test_find_green_bar(self):
        img = np.zeros((200, 800, 3), dtype=np.uint8)
        cv2.rectangle(img, (200, 50), (400, 100), (0, 255, 0), -1)

        lower = np.array([35, 50, 50])
        upper = np.array([85, 255, 255])

        center_x, bbox = find_green_bar(img, lower, upper)
        self.assertIsNotNone(center_x)
        self.assertTrue(290 <= center_x <= 310)
        self.assertIsNotNone(bbox)

    def test_pid_controller(self):
        pid = SimplePID(Kp=1.0, Ki=0.1, Kd=0.0)
        pid.last_time = time.time() - 0.1
        output1 = pid.update(100, 0)
        self.assertTrue(output1 > 0)

        pid.last_time = time.time() - 0.1
        output2 = pid.update(100, 0)
        self.assertTrue(output2 > output1)

if __name__ == '__main__':
    unittest.main()
