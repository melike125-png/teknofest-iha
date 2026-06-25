# camera_stream.py

from flask import Flask, Response
import cv2
import time

from config import (
    CAMERA_INDEX,
    FRAME_WIDTH,
    FRAME_HEIGHT,
    CONF_LIMIT,
    IOU_LIMIT,
    MAX_DETECTION
)

from detector import DetectorSystem


app = Flask(__name__)

detector = DetectorSystem()

camera = cv2.VideoCapture(CAMERA_INDEX)

camera.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)

prev_time = 0


def draw_center(frame):
    height, width, _ = frame.shape

    center_x = width // 2
    center_y = height // 2

    cv2.circle(frame, (center_x, center_y), 7, (255, 0, 0), -1)
    cv2.line(frame, (center_x - 20, center_y), (center_x + 20, center_y), (255, 0, 0), 2)
    cv2.line(frame, (center_x, center_y - 20), (center_x, center_y + 20), (255, 0, 0), 2)


def calculate_fps():
    global prev_time

    current_time = time.time()

    if prev_time == 0:
        fps = 0
    else:
        fps = 1 / (current_time - prev_time)

    prev_time = current_time

    return fps


def choose_best_detection(detections):
    if not detections:
        return None

    # En guvenilir tek hedefi sec.
    detections.sort(key=lambda item: item["confidence"], reverse=True)

    return detections[0]


def draw_detection(frame, detection):
    if detection is None:
        return

    x1, y1, x2, y2 = detection["box"]

    class_name = detection["class_name"]
    confidence = detection["confidence"]

    frame_height, frame_width, _ = frame.shape

    frame_center_x = frame_width // 2
    frame_center_y = frame_height // 2

    target_center_x = (x1 + x2) // 2
    target_center_y = (y1 + y2) // 2

    error_x = target_center_x - frame_center_x
    error_y = target_center_y - frame_center_y

    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

    cv2.circle(frame, (target_center_x, target_center_y), 5, (0, 0, 255), -1)

    cv2.line(
        frame,
        (frame_center_x, frame_center_y),
        (target_center_x, target_center_y),
        (255, 255, 255),
        2
    )

    cv2.putText(
        frame,
        f"{class_name} {confidence:.2f}",
        (x1, max(y1 - 10, 25)),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (0, 255, 0),
        2
    )

    cv2.putText(
        frame,
        f"X hata: {error_x}",
        (20, 70),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 255),
        2
    )

    cv2.putText(
        frame,
        f"Y hata: {error_y}",
        (20, 100),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 255),
        2
    )


def process_frame(frame):
    detections = detector.detect(frame)

    best_detection = choose_best_detection(detections)

    draw_center(frame)

    draw_detection(frame, best_detection)

    fps = calculate_fps()

    cv2.putText(
        frame,
        f"FPS: {fps:.1f}",
        (20, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (255, 255, 255),
        2
    )

    return frame


def generate_frames():
    while True:
        success, frame = camera.read()

        if not success:
            continue

        frame = process_frame(frame)

        ret, buffer = cv2.imencode(".jpg", frame)

        if not ret:
            continue

        frame_bytes = buffer.tobytes()

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
        )


@app.route("/")
def index():
    return """
    <html>
        <head>
            <title>TEKNOFEST IHA Canli YOLO</title>
        </head>
        <body style="background-color:#111; color:white; text-align:center;">
            <h1>TEKNOFEST IHA Canli YOLO Kamerasi</h1>
            <img src="/video" width="640" height="480">
            <p>Gorev 1: Sonsuz 8 | Gorev 2: mavi_altigen -> kirmizi yuk, kirmizi_ucgen -> mavi yuk</p>
        </body>
    </html>
    """


@app.route("/video")
def video():
    return Response(
        generate_frames(),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)