# target_tracker.py

import time


class TargetTracker:

    def __init__(self):

        self.last_target = None
        self.last_seen_time = 0

        self.lock_count = 0
        self.required_lock_count = 5

        self.memory_timeout = 2.0

    def update(self, target_data):

        if target_data is None:
            return

        self.last_target = target_data
        self.last_seen_time = time.time()

        self.lock_count += 1

    def target_lost(self):

        elapsed_time = time.time() - self.last_seen_time

        if elapsed_time > self.memory_timeout:
            self.last_target = None
            self.lock_count = 0
            return True

        return False

    def get_last_target(self):

        return self.last_target

    def is_locked(self):

        return self.lock_count >= self.required_lock_count

    def reset(self):

        self.last_target = None
        self.last_seen_time = 0
        self.lock_count = 0