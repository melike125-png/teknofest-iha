# search.py

class SearchMission:

    def __init__(self):

        self.area_width = 30
        self.area_length = 200

        self.line_spacing = 5

        self.search_points = []

        self.current_index = 0

        self.generate_search_pattern()

    def generate_search_pattern(self):

        direction_forward = True

        y = 0

        while y <= self.area_width:

            if direction_forward:

                self.search_points.append((0, y))
                self.search_points.append((self.area_length, y))

            else:

                self.search_points.append((self.area_length, y))
                self.search_points.append((0, y))

            direction_forward = not direction_forward

            y += self.line_spacing

    def get_current_point(self):

        if self.current_index >= len(self.search_points):
            return None

        return self.search_points[self.current_index]

    def move_next(self):

        self.current_index += 1

    def is_completed(self):

        return self.current_index >= len(self.search_points)

    def reset(self):

        self.current_index = 0