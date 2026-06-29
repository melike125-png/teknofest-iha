import cv2
import numpy as np


FONT = cv2.FONT_HERSHEY_SIMPLEX


WHITE = (225, 225, 225)
LIGHT_GRAY = (170, 170, 170)
GRAY = (120, 120, 120)
PANEL_BG = (16, 16, 16)

SOFT_GREEN = (150, 220, 150)
SOFT_CYAN = (130, 200, 220)
SOFT_ORANGE = (120, 180, 230)


def draw_text(frame, text, x, y, scale=0.5, color=WHITE, thickness=1):
    cv2.putText(
        frame,
        text,
        (x, y),
        FONT,
        scale,
        color,
        thickness,
        cv2.LINE_AA
    )


def choose_best_detection(detections, expected_target=None):
    if not detections:
        return None

    if expected_target is not None:
        expected_detections = [
            detection for detection in detections
            if detection.get("class_name") == expected_target
        ]

        if expected_detections:
            return max(
                expected_detections,
                key=lambda detection: detection.get("confidence", 0)
            )

    return max(
        detections,
        key=lambda detection: detection.get("confidence", 0)
    )


def get_payload_name(expected_target):
    if expected_target == "mavi_altigen":
        return "kirmizi_yuk"

    if expected_target == "kirmizi_ucgen":
        return "mavi_yuk"

    return "-"


def get_status_color(mission_status, expected_target, detected_class):
    if mission_status == "GOREV TAMAMLANDI":
        return SOFT_GREEN

    if mission_status == "YUK BIRAKILIYOR":
        return SOFT_GREEN

    if "HEDEF ALGILANDI" in mission_status:
        return SOFT_GREEN

    if "YANLIS" in mission_status:
        return SOFT_ORANGE

    if "YOK SAYILDI" in mission_status:
        return SOFT_CYAN

    if expected_target is not None and detected_class == expected_target:
        return SOFT_GREEN

    return SOFT_CYAN


def draw_status_line(frame, x, y, label, value, value_color=WHITE):
    draw_text(
        frame,
        label,
        x,
        y,
        scale=0.43,
        color=LIGHT_GRAY,
        thickness=1
    )

    draw_text(
        frame,
        value,
        x + 130,
        y,
        scale=0.43,
        color=value_color,
        thickness=1
    )


def draw_video_ui(
    frame,
    detections,
    fps,
    expected_target=None,
    mission_status="HEDEF ARANIYOR",
    completed_targets=None,
    stable_count=0,
    stable_required=18
):
    if completed_targets is None:
        completed_targets = {
            "mavi_altigen": False,
            "kirmizi_ucgen": False
        }

    display_width = 1280
    display_height = 720

    # Sol panel, sag kamera goruntusu
    panel_width = 380
    camera_width = display_width - panel_width

    original_height, original_width = frame.shape[:2]

    camera_frame = cv2.resize(frame, (camera_width, display_height))

    scale_x = camera_width / original_width
    scale_y = display_height / original_height

    canvas = np.zeros((display_height, display_width, 3), dtype=np.uint8)

    # Sol panel
    canvas[:, :panel_width] = PANEL_BG

    # Sag kamera alani
    canvas[:, panel_width:] = camera_frame

    # Ayrim cizgisi
    cv2.line(
        canvas,
        (panel_width, 0),
        (panel_width, display_height),
        (70, 70, 70),
        1
    )

    best_detection = choose_best_detection(
        detections=detections,
        expected_target=expected_target
    )

    detected_class = "YOK"
    confidence_text = "-"
    confidence = 0

    if expected_target is not None and best_detection is not None:
        detected_class = best_detection.get("class_name", "unknown")
        confidence = best_detection.get("confidence", 0)
        confidence_text = f"{confidence * 100:.0f}%"

    center_x = panel_width + camera_width // 2
    center_y = display_height // 2

    # Kamera merkez isareti
    cv2.line(
        canvas,
        (center_x - 12, center_y),
        (center_x + 12, center_y),
        (150, 150, 150),
        1
    )

    cv2.line(
        canvas,
        (center_x, center_y - 12),
        (center_x, center_y + 12),
        (150, 150, 150),
        1
    )

    cv2.circle(
        canvas,
        (center_x, center_y),
        3,
        (150, 150, 150),
        -1
    )

    offset_x = 0
    offset_y = 0

    # Hedef kutusu
    if expected_target is not None and best_detection is not None:
        box = best_detection.get("box", None)

        if box is not None:
            x1, y1, x2, y2 = map(int, box)

            x1 = panel_width + int(x1 * scale_x)
            x2 = panel_width + int(x2 * scale_x)
            y1 = int(y1 * scale_y)
            y2 = int(y2 * scale_y)

            target_center_x = (x1 + x2) // 2
            target_center_y = (y1 + y2) // 2

            offset_x = target_center_x - center_x
            offset_y = target_center_y - center_y

            if detected_class == expected_target:
                box_color = SOFT_GREEN
                label_bg = (35, 75, 35)
            else:
                box_color = SOFT_ORANGE
                label_bg = (55, 65, 85)

            cv2.rectangle(
                canvas,
                (x1, y1),
                (x2, y2),
                box_color,
                2
            )

            cv2.circle(
                canvas,
                (target_center_x, target_center_y),
                4,
                box_color,
                -1
            )

            cv2.line(
                canvas,
                (center_x, center_y),
                (target_center_x, target_center_y),
                box_color,
                1
            )

            label = f"{detected_class} | {confidence_text}"

            label_x1 = x1
            label_y1 = max(y1 - 26, 8)
            label_x2 = min(x1 + 245, display_width - 5)
            label_y2 = label_y1 + 24

            cv2.rectangle(
                canvas,
                (label_x1, label_y1),
                (label_x2, label_y2),
                label_bg,
                -1
            )

            draw_text(
                canvas,
                label,
                label_x1 + 7,
                label_y1 + 17,
                scale=0.40,
                color=WHITE,
                thickness=1
            )

    # Sol panel yazilari
    px = 28
    y = 52

    draw_text(
        canvas,
        "TEKNOFEST IHA",
        px,
        y,
        scale=0.68,
        color=WHITE,
        thickness=2
    )

    y += 34

    draw_text(
        canvas,
        "GOREV SISTEMI",
        px,
        y,
        scale=0.68,
        color=WHITE,
        thickness=2
    )

    y += 54

    draw_text(
        canvas,
        "SISTEM DURUMU",
        px,
        y,
        scale=0.45,
        color=GRAY,
        thickness=1
    )

    y += 32

    draw_status_line(canvas, px, y, "KAMERA", "ONLINE", SOFT_GREEN)
    y += 28

    draw_status_line(canvas, px, y, "MODEL", "LOADED", SOFT_GREEN)
    y += 28

    draw_status_line(canvas, px, y, "FPS", f"{fps:.1f}", WHITE)
    y += 50

    if expected_target is None:
        expected_text = "YOK"
        payload_text = "-"
    else:
        expected_text = expected_target
        payload_text = get_payload_name(expected_target)

    status_color = get_status_color(
        mission_status=mission_status,
        expected_target=expected_target,
        detected_class=detected_class
    )

    draw_text(
        canvas,
        "GOREV BILGISI",
        px,
        y,
        scale=0.45,
        color=GRAY,
        thickness=1
    )

    y += 32

    draw_status_line(canvas, px, y, "BEKLENEN", expected_text, WHITE)
    y += 28

    draw_status_line(canvas, px, y, "ALGILANAN", detected_class, WHITE)
    y += 28

    draw_status_line(canvas, px, y, "GUVEN", confidence_text, WHITE)
    y += 28

    draw_status_line(canvas, px, y, "YUK", payload_text, WHITE)
    y += 28

    draw_status_line(canvas, px, y, "ONAY", f"{stable_count}/{stable_required}", WHITE)
    y += 48

    draw_text(
        canvas,
        "DURUM",
        px,
        y,
        scale=0.45,
        color=GRAY,
        thickness=1
    )

    y += 32

    draw_text(
        canvas,
        mission_status,
        px,
        y,
        scale=0.42,
        color=status_color,
        thickness=1
    )

    y += 66

    draw_text(
        canvas,
        "GOREV SIRASI",
        px,
        y,
        scale=0.45,
        color=GRAY,
        thickness=1
    )

    y += 32

    mavi_status = "TAMAM" if completed_targets.get("mavi_altigen", False) else "BEKLIYOR"
    kirmizi_status = "TAMAM" if completed_targets.get("kirmizi_ucgen", False) else "BEKLIYOR"

    draw_text(
        canvas,
        "1. mavi_altigen",
        px,
        y,
        scale=0.40,
        color=WHITE,
        thickness=1
    )

    draw_text(
        canvas,
        mavi_status,
        px + 210,
        y,
        scale=0.40,
        color=LIGHT_GRAY,
        thickness=1
    )

    y += 30

    draw_text(
        canvas,
        "2. kirmizi_ucgen",
        px,
        y,
        scale=0.40,
        color=WHITE,
        thickness=1
    )

    draw_text(
        canvas,
        kirmizi_status,
        px + 210,
        y,
        scale=0.40,
        color=LIGHT_GRAY,
        thickness=1
    )

    draw_text(
        canvas,
        f"OFFSET X:{offset_x:+d} Y:{offset_y:+d}",
        px,
        display_height - 36,
        scale=0.40,
        color=GRAY,
        thickness=1
    )

    return canvas