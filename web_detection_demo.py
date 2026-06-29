import time
import cv2
from flask import Flask, Response, jsonify
from ultralytics import YOLO


MODEL_PATH = "best.pt"
CAMERA_INDEX = 0

CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480

YOLO_IMGSZ = 320
CONF_LIMIT = 0.50
IOU_LIMIT = 0.30

PROCESS_EVERY_N_FRAMES = 3
TARGET_CONFIRM_SECONDS = 3.0

TARGET_SEQUENCE = [
    "mavi_altigen",
    "kirmizi_ucgen",
]

WEB_PORT = 5003

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

current_status = {
    "next_target": "mavi_altigen",
    "detected_target": "-",
    "status": "HEDEF YOK",
    "confidence": "-",
    "step": "1/2",
    "fps": "0.0",
}


def draw_box(frame, detection, is_correct):
    if detection is None:
        return

    x1, y1, x2, y2 = detection["box"]
    class_name = detection["class_name"]
    confidence = detection["confidence"]

    color = (90, 220, 125) if is_correct else (80, 80, 230)

    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

    label = f"{class_name} {confidence:.2f}"

    label_x1 = x1
    label_y1 = max(0, y1 - 24)
    label_x2 = min(frame.shape[1] - 1, x1 + 160)
    label_y2 = label_y1 + 24

    cv2.rectangle(frame, (label_x1, label_y1), (label_x2, label_y2), (8, 12, 20), -1)
    cv2.rectangle(frame, (label_x1, label_y1), (label_x2, label_y2), color, 1)

    cv2.putText(
        frame,
        label,
        (label_x1 + 6, label_y1 + 17),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.45,
        color,
        1,
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


def update_status(next_target, detected_target, status, confidence_text, step_text, fps_text):
    current_status["next_target"] = next_target
    current_status["detected_target"] = detected_target
    current_status["status"] = status
    current_status["confidence"] = confidence_text
    current_status["step"] = step_text
    current_status["fps"] = fps_text


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

        update_status(
            next_target,
            detected_target,
            status,
            confidence_text,
            step_text,
            f"{fps:.1f}",
        )

        success, buffer = cv2.imencode(
            ".jpg",
            frame,
            [cv2.IMWRITE_JPEG_QUALITY, 85]
        )

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
            * {
                box-sizing: border-box;
            }

            body {
                margin: 0;
                background: #0b0f14;
                color: #f5f5f5;
                font-family: Arial, sans-serif;
            }

            .page {
                min-height: 100vh;
                padding: 22px;
                display: flex;
                flex-direction: column;
                align-items: center;
            }

            .title {
                font-size: 30px;
                font-weight: 700;
                letter-spacing: 1px;
                margin-bottom: 6px;
            }

            .subtitle {
                font-size: 14px;
                color: #8b95a1;
                margin-bottom: 18px;
            }

            .content {
                display: flex;
                gap: 22px;
                align-items: flex-start;
                justify-content: center;
                width: 100%;
            }

            .video-card {
                background: #111720;
                border: 1px solid #2f3640;
                box-shadow: 0 0 25px rgba(0, 0, 0, 0.35);
                padding: 8px;
            }

            .video-card img {
                display: block;
                width: 760px;
                max-width: 65vw;
                background: black;
            }

            .status-card {
                width: 360px;
                min-height: 360px;
                background: #111720;
                border: 1px solid #2f3640;
                box-shadow: 0 0 25px rgba(0, 0, 0, 0.35);
                padding: 24px;
            }

            .status-title {
                font-size: 22px;
                font-weight: 700;
                margin-bottom: 22px;
                color: #f2f2f2;
            }

            .row {
                margin-bottom: 18px;
            }

            .label {
                font-size: 12px;
                color: #8b95a1;
                letter-spacing: 0.7px;
                margin-bottom: 5px;
            }

            .value {
                font-size: 22px;
                font-weight: 700;
                color: #f2f2f2;
                word-break: break-word;
            }

            .blue {
                color: #55b7ff;
            }

            .green {
                color: #5ee085;
            }

            .red {
                color: #ff5f6d;
            }

            .muted {
                color: #a0a6ad;
            }

            .small {
                font-size: 18px;
            }
        </style>
    </head>
    <body>
        <div class="page">
            <div class="title">TEKNOFEST IHA HEDEF ALGILAMA</div>
            <div class="subtitle">Sira: mavi_altigen -> kirmizi_ucgen</div>

            <div class="content">
                <div class="video-card">
                    <img src="/video_feed">
                </div>

                <div class="status-card">
                    <div class="status-title">GOREV DURUM PANELI</div>

                    <div class="row">
                        <div class="label">SIRADAKI HEDEF</div>
                        <div id="next_target" class="value blue">-</div>
                    </div>

                    <div class="row">
                        <div class="label">ALGILANAN HEDEF</div>
                        <div id="detected_target" class="value muted">-</div>
                    </div>

                    <div class="row">
                        <div class="label">ALGILAMA DURUMU</div>
                        <div id="status" class="value muted">HEDEF YOK</div>
                    </div>

                    <div class="row">
                        <div class="label">GUVEN ORANI</div>
                        <div id="confidence" class="value small">-</div>
                    </div>

                    <div class="row">
                        <div class="label">GOREV ADIMI</div>
                        <div id="step" class="value small">1/2</div>
                    </div>

                    <div class="row">
                        <div class="label">FPS</div>
                        <div id="fps" class="value small">0.0</div>
                    </div>
                </div>
            </div>
        </div>

        <script>
            async function updateStatus() {
                try {
                    const response = await fetch('/status');
                    const data = await response.json();

                    document.getElementById('next_target').textContent = data.next_target;
                    document.getElementById('detected_target').textContent = data.detected_target;
                    document.getElementById('status').textContent = data.status;
                    document.getElementById('confidence').textContent = data.confidence;
                    document.getElementById('step').textContent = data.step;
                    document.getElementById('fps').textContent = data.fps;

                    const detected = document.getElementById('detected_target');
                    const status = document.getElementById('status');

                    detected.className = 'value';
                    status.className = 'value';

                    if (data.detected_target === '-') {
                        detected.classList.add('muted');
                    } else {
                        detected.classList.add('green');
                    }

                    if (data.status === 'DOGRU HEDEF ALGILANDI' || data.status === 'GOREV TAMAMLANDI') {
                        status.classList.add('green');
                    } else if (data.status === 'YANLIS HEDEF ALGILANDI') {
                        status.classList.add('red');
                    } else {
                        status.classList.add('muted');
                    }
                } catch (error) {
                    console.log(error);
                }
            }

            setInterval(updateStatus, 300);
            updateStatus();
        </script>
    </body>
    </html>
    """


@app.route("/video_feed")
def video_feed():
    return Response(
        generate_frames(),
        mimetype="multipart/x-mixed-replace; boundary=frame",
    )


@app.route("/status")
def status():
    return jsonify(current_status)


def main():
    global model
    global cap

    print("TEKNOFEST IHA web hedef algilama baslatiliyor...")
    print("Hedef sirasi: mavi_altigen -> kirmizi_ucgen")
    print("Yuk / servo / payload bu demo icinde yoktur.")
    print(f"Tarayicidan ac: http://teknopi.local:{WEB_PORT}")
    print(f"veya: http://PI_IP:{WEB_PORT}")
    print("Cikis icin terminalde Ctrl+C")

    model = YOLO(MODEL_PATH)

    cap = cv2.VideoCapture(CAMERA_INDEX)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
    cap.set(cv2.CAP_PROP_FPS, 15)

    if not cap.isOpened():
        print("Kamera acilamadi.")
        return

    app.run(host="0.0.0.0", port=WEB_PORT, debug=False, threaded=True)

    cap.release()


if __name__ == "__main__":
    main()
