# detector.py

from ultralytics import YOLO

from config import (
    MODEL_PATH,
    CONF_LIMIT,
    IOU_LIMIT,
    MAX_DETECTION
)

class DetectorSystem:

    def __init__(self):

        print("YOLO modeli yukleniyor...")

        self.model = YOLO(MODEL_PATH)

        print("YOLO modeli hazir.")

    def detect(self, frame):

        results = self.model(
            frame,
            conf=CONF_LIMIT,
            iou=IOU_LIMIT,
            max_det=MAX_DETECTION,
            verbose=False
        )

        detections = []

        for box in results[0].boxes:

            conf = float(box.conf[0])

            cls_id = int(box.cls[0])

            class_name = self.model.names[cls_id]

            x1, y1, x2, y2 = map(int, box.xyxy[0])

            detections.append({
                "class_name": class_name,
                "confidence": conf,
                "box": (x1, y1, x2, y2)
            })

        return detections