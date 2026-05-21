# memory.py

import time


class TargetMemorySystem:

    def __init__(self):

        self.last_target_data = None
        self.last_seen_time = 0

        self.memory_timeout = 2.0

    def update(self, target_data):

        if target_data is None:
            return

        self.last_target_data = target_data
        self.last_seen_time = time.time()

    def get_last_target(self):

        if self.last_target_data is None:
            return None

        elapsed_time = time.time() - self.last_seen_time

        if elapsed_time > self.memory_timeout:
            self.clear()
            return None

        return self.last_target_data

    def clear(self):

        self.last_target_data = None
        self.last_seen_time = 0

    def has_target(self):

        return self.get_last_target() is not None