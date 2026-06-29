import time
import cv2
from ultralytics import YOLO


MODEL_PATH = "best.pt"
CAMERA_INDEX = 0

FRAME_WIDTH = 640
FRAME_HEIGHT = 480

YOLO_IMGSZ = 320
CONF_LIMIT = 0.50
IOU_LIMIT = 0.30

PROCESS_EVERY_N_FRAMES = 2
TARGET_CONFIRM_SECONDS = 1.0

WINDOW_NAME = "TEKNOFEST IHA HEDEF ALGILAMA"

TARGET_SEQUENCE = [
    "mavi_altigen",
    "kirmizi_ucgen",
]


def draw_detection_panel(
    frame,
    next_target,
    detected_target,
    detection_status,
    confidence,
    mission_step,
    total_steps,
    fps
):
    panel_x1 = 10
    panel_y1 = 10
    panel_x2 = 510
    panel_y2 = 205

    overlay = frame.copy()

    cv2.rectangle(
        overlay,
        (panel_x1, panel_y1),
        (panel_x2, panel_y2),
        (20, 20, 20),
        -1
    )

    cv2.addWeighted(overlay, 0.75, frame, 0.25, 0, frame)

    cv2.rectangle(
        frame,
        (panel_x1, panel_y1),
        (panel_x2, panel_y2),
        (170, 170, 170),
        1
    )

    title_color = (0, 180, 255)
    label_color = (210, 210, 210)
    good_color = (0, 255, 0)
    warn_color = (0, 255, 255)
    bad_color = (0, 0, 255)
    white_color = (235, 235, 235)

    cv2.putText(
        frame,
        "TEKNOFEST IHA HEDEF ALGILAMA",
        (25, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.58,
        title_color,
        2,
        cv2.LINE_AA
    )

    if detection_status == "DOGRU HEDEF ALGILANDI":
        status_color = good_color
    elif detection_status == "YANLIS HEDEF ALGILANDI":
        status_color = bad_color
    elif detection_status == "GOREV TAMAMLANDI":
        status_color = good_color
    else:
        status_color = warn_color

    rows = [
        ("SIRADAKI HEDEF", next_target, warn_color if next_target != "-" else good_color),
        ("ALGILANAN HEDEF", detected_target, good_color if detected_target != "-" else warn_color),
        ("ALGILAMA DURUMU", detection_status, status_color),
        ("GUVEN ORANI", confidence, white_color),
        ("GOREV ADIMI", f"{mission_step}/{total_steps}", white_color),
        ("FPS", fps, white_color),
    ]

    y = 68

    for label, value, color in rows:
        cv2.putText(
            frame,
            f"{label:16s}:",
            (25, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.43,
            label_color,
            1,
            cv2.LINE_AA
        )

        cv2.putText(
            frame,
            str(value),
            (235, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.43,
            color,
            2,
            cv2.LINE_AA
        )

        y += 24


def draw_detection_box(frame, detection, is_correct_target):
    if detection is None:
        return

    x1, y1, x2, y2 = detection["box"]
    class_name = detection["class_name"]
    confidence = detection["confidence"]

    if is_correct_target:
        box_color = (0, 255, 0)
    else:
        box_color = (0, 0, 255)

    cv2.rectangle(
        frame,
        (x1, y1),
        (x2, y2),
        box_color,
        2
    )

    label = f"{class_name} {confidence:.2f}"

    cv2.putText(
        frame,
        label,
        (x1, max(25, y1 - 8)),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        box_color,
        2,
        cv2.LINE_AA
    )


def get_best_detection(results, model):
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
                "box": (x1, y1, x2, y2)
            }

    return best_detection


def main():
    print("TEKNOFEST IHA hedef algilama demosu baslatiliyor...")
    print("Hedef sirasi: mavi_altigen -> kirmizi_ucgen")
    print("Cikis icin q tusuna basin.")

    model = YOLO(MODEL_PATH)

    cap = cv2.VideoCapture(CAMERA_INDEX)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
    cap.set(cv2.CAP_PROP_FPS, 15)

    if not cap.isOpened():
        print("Kamera acilamadi.")
        return

    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(WINDOW_NAME, FRAME_WIDTH, FRAME_HEIGHT)

    target_index = 0
    total_steps = len(TARGET_SEQUENCE)

    frame_count = 0
    last_detection = None
    last_time = time.time()
    fps = 0.0

    correct_target_start_time = None
    mission_done = False

    while True:
        ret, frame = cap.read()

        if not ret:
            print("Kameradan goruntu alinamadi.")
            break

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
                verbose=False
            )

            last_detection = get_best_detection(results, model)

        if mission_done:
            next_target = "-"
            detected_target = "-"
            confidence_text = "-"
            detection_status = "GOREV TAMAMLANDI"
            is_correct_target = False

        else:
            next_target = TARGET_SEQUENCE[target_index]

            if last_detection is None:
                detected_target = "-"
                confidence_text = "-"
                detection_status = "HEDEF YOK"
                is_correct_target = False
                correct_target_start_time = None

            else:
                detected_target = last_detection["class_name"]
                confidence_text = f"{last_detection['confidence']:.2f}"
                is_correct_target = detected_target == next_target

                if is_correct_target:
                    detection_status = "DOGRU HEDEF ALGILANDI"

                    if correct_target_start_time is None:
                        correct_target_start_time = time.time()

                    correct_duration = time.time() - correct_target_start_time

                    if correct_duration >= TARGET_CONFIRM_SECONDS:
                        target_index += 1
                        correct_target_start_time = None
                        last_detection = None

                        if target_index >= total_steps:
                            mission_done = True
                            detection_status = "GOREV TAMAMLANDI"
                            next_target = "-"
                        else:
                            next_target = TARGET_SEQUENCE[target_index]

                else:
                    detection_status = "YANLIS HEDEF ALGILANDI"
                    correct_target_start_time = None

        draw_detection_box(frame, last_detection, not mission_done and last_detection is not None and last_detection["class_name"] == next_target)

        mission_step = min(target_index + 1, total_steps)

        draw_detection_panel(
            frame,
            next_target,
            detected_target,
            detection_status,
            confidence_text,
            mission_step,
            total_steps,
            f"{fps:.1f}"
        )

        cv2.imshow(WINDOW_NAME, frame)

        key = cv2.waitKey(1) & 0xFF

        if key == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()
    print("Program kapatildi.")


if __name__ == "__main__":
    main()