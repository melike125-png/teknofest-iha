# infinity8.py

import math


class Infinity8Mission:

    def __init__(self):

        self.radius = 15
        self.center_x = 0
        self.center_y = 0

        self.total_points = 80
        self.current_index = 0

        self.path_points = self.generate_path()

    def generate_path(self):

        points = []

        for i in range(self.total_points):

            t = 2 * math.pi * i / self.total_points

            x = self.radius * math.sin(t)
            y = self.radius * math.sin(t) * math.cos(t)

            points.append((x, y))

        return points

    def get_current_target_point(self):

        if self.current_index >= len(self.path_points):
            return None

        return self.path_points[self.current_index]

    def move_to_next_point(self):

        self.current_index += 1

    def is_completed(self):

        return self.current_index >= len(self.path_points)

    def reset(self):

        self.current_index = 0