# failsafe.py

import time


class FailsafeSystem:

    def __init__(self):

        self.last_target_time = time.time()
        self.last_frame_time = time.time()

        self.min_fps_limit = 5
        self.target_lost_limit = 3
        self.frame_lost_limit = 2

    def update_frame_time(self):

        self.last_frame_time = time.time()

    def update_target_time(self):

        self.last_target_time = time.time()

    def check_fps(self, fps):

        if fps < self.min_fps_limit and fps != 0:
            return False

        return True

    def check_target_lost(self):

        elapsed_time = time.time() - self.last_target_time

        if elapsed_time > self.target_lost_limit:
            return False

        return True

    def check_frame_lost(self):

        elapsed_time = time.time() - self.last_frame_time

        if elapsed_time > self.frame_lost_limit:
            return False

        return True

    def get_status(self, fps):

        if not self.check_fps(fps):
            return "FAILSAFE: FPS COK DUSUK"

        if not self.check_frame_lost():
            return "FAILSAFE: KAMERA GORUNTUSU KOPTU"

        if not self.check_target_lost():
            return "FAILSAFE: HEDEF UZUN SURE KAYIP"

        return "SISTEM NORMAL"