# targeting.py

from config import (
    CENTER_TOLERANCE_X,
    CENTER_TOLERANCE_Y,
    STABLE_LIMIT
)


class TargetingSystem:

    def __init__(self):

        self.stable_counter = 0

    def calculate_error(
        self,
        target_center_x,
        target_center_y,
        frame_center_x,
        frame_center_y
    ):

        error_x = target_center_x - frame_center_x
        error_y = target_center_y - frame_center_y

        return error_x, error_y

    def target_is_centered(self, error_x, error_y):

        return (
            abs(error_x) < CENTER_TOLERANCE_X
            and
            abs(error_y) < CENTER_TOLERANCE_Y
        )

    def update_stable_counter(self, centered):

        if centered:
            self.stable_counter += 1
        else:
            self.stable_counter = 0

    def ready_to_drop(self):

        return self.stable_counter >= STABLE_LIMIT

    def reset(self):

        self.stable_counter = 0