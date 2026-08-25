# detector.py

import os
import queue
import threading
import time

from ultralytics import YOLO

from config import (
    MODEL_PATH,
    INFERENCE_SIZE,
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

        self._frame_queue = queue.Queue(maxsize=1)
        self._result_lock = threading.Lock()
        self._stop_event = threading.Event()
        self._latest_detections = []
        self._latest_result_time = 0.0
        self._result_sequence = 0
        self._consumed_sequence = 0
        self._last_error = None
        self._result_timeout = 0.50
        self._model_fps = 0.0
        self._last_inference_time = 0.0

        self._worker = threading.Thread(
            target=self._worker_loop,
            name="ncnn-detector",
            daemon=True,
        )
        self._worker.start()

        print(f"YOLO modeli hazir | {MODEL_PATH} | asenkron algilama aktif.")

    def _validate_model_file(self):

        if not MODEL_PATH or not str(MODEL_PATH).strip():
            raise FileNotFoundError("MODEL_PATH bos. config.py icinde gecerli bir model yolu tanimlayin.")

        model_path = os.path.abspath(MODEL_PATH)

        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"Model dosyasi bulunamadi: {model_path}\n"
                f"config.py MODEL_PATH degerini kontrol edin."
            )

        if os.path.isdir(model_path):
            required_ncnn_files = (
                "metadata.yaml",
                "model.ncnn.bin",
                "model.ncnn.param",
            )
            missing_files = [
                name
                for name in required_ncnn_files
                if not os.path.isfile(os.path.join(model_path, name))
            ]
            if missing_files:
                raise FileNotFoundError(
                    "NCNN model klasoru eksik: " + ", ".join(missing_files)
                )
            return

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

        self._submit_latest_frame(frame)

        with self._result_lock:
            detections = list(self._latest_detections)
            result_time = self._latest_result_time

        if result_time <= 0 or time.monotonic() - result_time > self._result_timeout:
            return []

        return detections

    def _submit_latest_frame(self, frame):
        if frame is None or self._stop_event.is_set():
            return

        try:
            self._frame_queue.put_nowait(frame.copy())
            return
        except queue.Full:
            pass

        try:
            self._frame_queue.get_nowait()
        except queue.Empty:
            pass

        try:
            self._frame_queue.put_nowait(frame.copy())
        except queue.Full:
            pass

    def _worker_loop(self):
        while not self._stop_event.is_set():
            try:
                frame = self._frame_queue.get(timeout=0.10)
            except queue.Empty:
                continue

            try:
                detections = self._infer(frame)
                error = None
            except Exception as exc:
                detections = []
                error = str(exc)

            finished_at = time.monotonic()

            with self._result_lock:
                self._latest_detections = detections
                self._latest_result_time = finished_at
                self._result_sequence += 1

                if self._last_inference_time > 0:
                    elapsed = finished_at - self._last_inference_time
                    instant_fps = 1.0 / elapsed if elapsed > 0 else 0.0
                    if self._model_fps <= 0:
                        self._model_fps = instant_fps
                    else:
                        self._model_fps = self._model_fps * 0.85 + instant_fps * 0.15

                self._last_inference_time = finished_at

            if error is not None and error != self._last_error:
                print(f"YOLO ALGILAMA HATASI: {error}")

            self._last_error = error

    def consume_new_result(self):
        with self._result_lock:
            if self._result_sequence == self._consumed_sequence:
                return False

            self._consumed_sequence = self._result_sequence
            return True

    def get_fps(self):
        with self._result_lock:
            return self._model_fps

    def _infer(self, frame):

        results = self.model(
            frame,
            imgsz=INFERENCE_SIZE,
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

    def close(self):
        self._stop_event.set()

        if self._worker.is_alive():
            self._worker.join(timeout=2.0)
