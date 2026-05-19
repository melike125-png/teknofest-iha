# detector.py

import os

from ultralytics import YOLO

from config import (
    MODEL_PATH,
    CONF_LIMIT,
    IOU_LIMIT,
    MAX_DETECTION
)

_VALID_MODEL_EXTENSIONS = (".pt", ".onnx", ".engine", ".torchscript")


class DetectorSystem:

    def __init__(self):

        self._validate_model_file()

        print("YOLO modeli yukleniyor...")

        self.model = YOLO(MODEL_PATH)

        print("YOLO modeli hazir.")

    def _validate_model_file(self):

        if not MODEL_PATH or not str(MODEL_PATH).strip():
            raise FileNotFoundError("MODEL_PATH bos. config.py icinde gecerli bir model yolu tanimlayin.")

        model_path = os.path.abspath(MODEL_PATH)

        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"Model dosyasi bulunamadi: {model_path}\n"
                f"config.py MODEL_PATH degerini kontrol edin."
            )

        if not os.path.isfile(model_path):
            raise FileNotFoundError(f"Model yolu bir dosya degil: {model_path}")

        if os.path.getsize(model_path) == 0:
            raise ValueError(f"Model dosyasi bos: {model_path}")

        _, ext = os.path.splitext(model_path)
        if ext.lower() not in _VALID_MODEL_EXTENSIONS:
            raise ValueError(
                f"Desteklenmeyen model uzantisi: {ext}\n"
                f"Gecerli uzantilar: {', '.join(_VALID_MODEL_EXTENSIONS)}"
            )

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

        detections.sort(key=lambda item: item["confidence"], reverse=True)

        return detections