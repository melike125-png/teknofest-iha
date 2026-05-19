# targeting.py



from config import CENTER_TOLERANCE



_CONFIDENCE_WEIGHT = 0.6

_AREA_WEIGHT = 0.4





class TargetingSystem:



    def __init__(self):

        pass



    def _score_detection(self, detection, frame_area):



        x1, y1, x2, y2 = detection["box"]

        box_area = max(0, (x2 - x1) * (y2 - y1))

        normalized_area = box_area / frame_area if frame_area > 0 else 0.0



        return (

            _CONFIDENCE_WEIGHT * detection["confidence"]

            + _AREA_WEIGHT * normalized_area

        )



    def _filter_by_target(self, detections, current_target):



        return [

            detection for detection in detections

            if detection["class_name"] == current_target

        ]



    def _select_best_detection(self, candidates, frame_area):



        return max(

            candidates,

            key=lambda detection: self._score_detection(detection, frame_area)

        )



    def _compute_center(self, box):



        x1, y1, x2, y2 = box

        target_center_x = (x1 + x2) // 2

        target_center_y = (y1 + y2) // 2



        return target_center_x, target_center_y



    def _is_near_frame_center(self, error_x, error_y):



        return (

            abs(error_x) < CENTER_TOLERANCE

            and abs(error_y) < CENTER_TOLERANCE

        )



    def calculate_direction(self, error_x, error_y):



        directions = []



        if error_x > CENTER_TOLERANCE:

            directions.append("RIGHT")

        elif error_x < -CENTER_TOLERANCE:

            directions.append("LEFT")



        if error_y > CENTER_TOLERANCE:

            directions.append("DOWN")

        elif error_y < -CENTER_TOLERANCE:

            directions.append("UP")



        if not directions:

            return "CENTER"



        return " ".join(directions)



    def find_best_target(self, detections, current_target, frame):



        if current_target is None:

            return None



        frame_height, frame_width, _ = frame.shape



        frame_center_x = frame_width // 2

        frame_center_y = frame_height // 2

        frame_area = frame_width * frame_height



        candidates = self._filter_by_target(detections, current_target)



        if not candidates:

            return None



        best_detection = self._select_best_detection(candidates, frame_area)



        target_center_x, target_center_y = self._compute_center(best_detection["box"])



        error_x = target_center_x - frame_center_x

        error_y = target_center_y - frame_center_y



        is_centered = self._is_near_frame_center(error_x, error_y)

        direction = self.calculate_direction(error_x, error_y)



        return {

            "class_name": best_detection["class_name"],

            "confidence": best_detection["confidence"],

            "box": best_detection["box"],

            "target_center": (target_center_x, target_center_y),

            "frame_center": (frame_center_x, frame_center_y),

            "error_x": error_x,

            "error_y": error_y,

            "is_centered": is_centered,

            "direction": direction

        }


