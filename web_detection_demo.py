import time
import cv2
from flask import Flask, Response
from ultralytics import YOLO


MODEL_PATH = "best.pt"
CAMERA_INDEX = 0

FRAME_WIDTH = 640
FRAME_HEIGHT = 480

YOLO_IMGSZ = 320
CONF_LIMIT = 0.50
IOU_LIMIT = 0.30

PROCESS_EVERY_N_FRAMES = 3
TARGET_CONFIRM_SECONDS = 1.0

TARGET_SEQUENCE = [
    "mavi_altigen",
    "kirmizi_ucgen",
]

app = Flask(__name__)

model = None
cap = None

target_index = 0
mission_done = False
correct_target_start_time = None
last_detection = None
frame_count = 0
last_time = time.time()
fps = 0.0


def draw_panel(frame, next_target, detected_target, status, confidence, step_text, fps_text):
    panel_x1, panel_y1 = 14, 14
    panel_x2, panel_y2 = 505, 190

    overlay = frame.copy()

    cv2.rectangle(
        overlay,
        (panel_x1, panel_y1),
        (panel_x2, panel_y2),
        (12, 14, 18),
        -1
    )

    cv2.addWeighted(overlay, 0.82, frame, 0.18, 0, frame)

    cv2.rectangle(
        frame,
        (panel_x1, panel_y1),
        (panel_x2, panel_y2),
        (95, 105, 115),
        1
    )

    title_color = (245, 245, 245)
    label_color = (170, 175, 180)
    text_color = (235, 235, 235)
    blue_color = (255, 170, 60)
    green_color = (70, 220, 120)
    red_color = (70, 70, 230)
    muted_color = (150, 150, 150)

    cv2.putText(
        frame,
        "TEKNOFEST IHA HEDEF ALGILAMA",
        (30, 42),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        title_color,
        2,
        cv2.LINE_AA,
    )

    if status == "DOGRU HEDEF ALGILANDI":
        status_color = green_color
    elif status == "YANLIS HEDEF ALGILANDI":
        status_color = red_color
    elif status == "GOREV TAMAMLANDI":
        status_color = green_color
    elif status == "HEDEF YOK":
        status_color = muted_color
    else:
        status_color = text_color

    rows = [
        ("SIRADAKI HEDEF", next_target, blue_color if next_target != "-" else muted_color),
        ("ALGILANAN HEDEF", detected_target, green_color if detected_target != "-" else muted_color),
        ("ALGILAMA DURUMU", status, status_color),
        ("GUVEN ORANI", confidence, text_color if confidence != "-" else muted_color),
        ("GOREV ADIMI", step_text, text_color),
        ("FPS", fps_text, text_color),
    ]

    y = 68

    for label, value, color in rows:
        cv2.putText(
            frame,
            f"{label:16s}:",
            (30, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.42,
            label_color,
            1,
            cv2.LINE_AA,
        )

        cv2.putText(
            frame,
            str(value),
            (232, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.42,
            color,
            2,
            cv2.LINE_AA,
        )

        y += 22


def draw_box(frame, detection, is_correct):
    if detection is None:
        return

    x1, y1, x2, y2 = detection["box"]
    class_name = detection["class_name"]
    confidence = detection["confidence"]

    if is_correct:
        color = (70, 220, 120)
    else:
        color = (70, 70, 230)

    cv2.rectangle(
        frame,
        (x1, y1),
        (x2, y2),
        color,
        2
    )

    cv2.putText(
        frame,
        f"{class_name} {confidence:.2f}",
        (x1, max(25, y1 - 8)),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        color,
        2,
        cv2.LINE_AA,
    )


def get_best_detection(results):
    best_detection = None
    best_confidence = 0.0

    for result in results:
        if result.boxes is None:
            continue

        for box in result.boxes:
            confidence = float(box.conf[0])

            if confidence < best_confidence:
                continue

            cls_id = int(box.cls[0])
            class_name = model.names[cls_id]
            x1, y1, x2, y2 = map(int, box.xyxy[0])

            best_confidence = confidence

            best_detection = {
                "class_name": class_name,
                "confidence": confidence,
                "box": (x1, y1, x2, y2),
            }

    return best_detection


def generate_frames():
    global cap
    global target_index
    global mission_done
    global correct_target_start_time
    global last_detection
    global frame_count
    global last_time
    global fps

    while True:
        ret, frame = cap.read()

        if not ret:
            continue

        frame_count += 1

        now = time.time()
        elapsed = now - last_time

        if elapsed > 0:
            fps = 1.0 / elapsed

        last_time = now

        if frame_count % PROCESS_EVERY_N_FRAMES == 0 and not mission_done:
            results = model(
                frame,
                imgsz=YOLO_IMGSZ,
                conf=CONF_LIMIT,
                iou=IOU_LIMIT,
                max_det=1,
                verbose=False,
            )

            last_detection = get_best_detection(results)

        total_steps = len(TARGET_SEQUENCE)

        if mission_done:
            next_target = "-"
            detected_target = "-"
            confidence_text = "-"
            status = "GOREV TAMAMLANDI"
            step_text = f"{total_steps}/{total_steps}"
            is_correct = False

        else:
            next_target = TARGET_SEQUENCE[target_index]
            step_text = f"{target_index + 1}/{total_steps}"

            if last_detection is None:
                detected_target = "-"
                confidence_text = "-"
                status = "HEDEF YOK"
                correct_target_start_time = None
                is_correct = False

            else:
                detected_target = last_detection["class_name"]
                confidence_text = f"{last_detection['confidence']:.2f}"
                is_correct = detected_target == next_target

                if is_correct:
                    status = "DOGRU HEDEF ALGILANDI"

                    if correct_target_start_time is None:
                        correct_target_start_time = time.time()

                    if time.time() - correct_target_start_time >= TARGET_CONFIRM_SECONDS:
                        target_index += 1
                        correct_target_start_time = None
                        last_detection = None

                        if target_index >= total_steps:
                            mission_done = True
                            status = "GOREV TAMAMLANDI"
                            next_target = "-"
                            step_text = f"{total_steps}/{total_steps}"

                else:
                    status = "YANLIS HEDEF ALGILANDI"
                    correct_target_start_time = None

        draw_box(frame, last_detection, is_correct)

        draw_panel(
            frame,
            next_target,
            detected_target,
            status,
            confidence_text,
            step_text,
            f"{fps:.1f}",
        )

        success, buffer = cv2.imencode(".jpg", frame)

        if not success:
            continue

        frame_bytes = buffer.tobytes()

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
        )


@app.route("/")
def index():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>TEKNOFEST IHA HEDEF ALGILAMA</title>
        <style>
            body {
                margin: 0;
                background: #0f1115;
                color: white;
                font-family: Arial, sans-serif;
                text-align: center;
            }

            h2 {
                margin: 12px 0;
                font-size: 24px;
                font-weight: 600;
                letter-spacing: 0.5px;
                color: #f2f2f2;
            }

            img {
                width: 960px;
                max-width: 96vw;
                border: 1px solid #333;
                background: black;
            }
        </style>
    </head>
    <body>
        <h2>TEKNOFEST IHA HEDEF ALGILAMA</h2>
        <img src="/video_feed">
    </body>
    </html>
    """


@app.route("/video_feed")
def video_feed():
    return Response(
        generate_frames(),
        mimetype="multipart/x-mixed-replace; boundary=frame",
    )


def main():
    global model
    global cap

    print("TEKNOFEST IHA web hedef algilama baslatiliyor...")
    print("Hedef sirasi: mavi_altigen -> kirmizi_ucgen")
    print("Yuk / servo / payload bu demo icinde yoktur.")
    print("Tarayicidan ac:")
    print("http://teknopi.local:5000")
    print("veya")
    print("http://PI_IP:5000")
    print("Cikis icin terminalde Ctrl+C")

    model = YOLO(MODEL_PATH)

    cap = cv2.VideoCapture(CAMERA_INDEX)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
    cap.set(cv2.CAP_PROP_FPS, 15)

    if not cap.isOpened():
        print("Kamera acilamadi.")
        return

    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)

    cap.release()


if __name__ == "__main__":
    main()