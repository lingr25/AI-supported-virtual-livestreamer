import pyautogui
import time
import random
import threading

class ActionControl:
    def __init__(self):
        self.action_map = {"愉悦": 2, "思考": 3, "害羞": 4, "好奇": 5, "卖萌": 6, "惊讶": 7, "快乐": 8, "震惊": 9, "失落": 0}

    def simulate_keypress(self, key):
        pyautogui.keyDown(str(key))
        time.sleep(0.1)  # 短暂按下以确保按键被识别
        pyautogui.keyUp(str(key))

    def random_action(self):
        while True:
            time.sleep(15)
            self.simulate_keypress(random.randint(2, 9))

    def start_random_action_thread(self):
        random_action_thread = threading.Thread(target=self.random_action)
        random_action_thread.daemon = True
        random_action_thread.start()
