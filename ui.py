import cv2


FONT = cv2.FONT_HERSHEY_SIMPLEX


def _draw_text(frame, text, x, y, scale=0.55, color=(255, 255, 255), thickness=1):
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


def _draw_panel(frame, x1, y1, x2, y2, alpha=0.65):
    overlay = frame.copy()
    cv2.rectangle(overlay, (x1, y1), (x2, y2), (20, 20, 20), -1)
    cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)
    cv2.rectangle(frame, (x1, y1), (x2, y2), (180, 180, 180), 1)


def _get_best_detection(detections):
    """
    detections listesi su formatta beklenir:
    {
        "class_name": "kirmizi_ucgen",
        "confidence": 0.87,
        "box": [x1, y1, x2, y2]
    }
    """

    if not detections:
        return None

    return max(detections, key=lambda d: d.get("confidence", 0))


def draw_professional_camera_screen(frame, detections=None, fps=0):
    """
    Kamera ekranini profesyonel gorev arayuzu gibi cizer.
    Model class isimleri degistirilmez:
    - kirmizi_ucgen
    - mavi_altigen
    """

    if detections is None:
        detections = []

    height, width = frame.shape[:2]

    best_detection = _get_best_detection(detections)

    # -----------------------------
    # Ust baslik paneli
    # -----------------------------
    cv2.rectangle(frame, (0, 0), (width, 58), (15, 15, 15), -1)

    _draw_text(
        frame,
        "TEKNOFEST IHA GOREV SISTEMI",
        18,
        37,
        scale=0.75,
        color=(255, 255, 255),
        thickness=2
    )

    _draw_text(
        frame,
        f"FPS: {fps:.1f}",
        width - 120,
        36,
        scale=0.55,
        color=(220, 220, 220),
        thickness=1
    )

    # -----------------------------
    # Merkez cizgisi
    # -----------------------------
    center_x = width // 2
    center_y = height // 2

    cv2.line(frame, (center_x - 20, center_y), (center_x + 20, center_y), (180, 180, 180), 1)
    cv2.line(frame, (center_x, center_y - 20), (center_x, center_y + 20), (180, 180, 180), 1)
    cv2.circle(frame, (center_x, center_y), 4, (180, 180, 180), -1)

    # -----------------------------
    # Sag bilgi paneli
    # -----------------------------
    panel_width = 340
    panel_x1 = max(width - panel_width - 15, 15)
    panel_y1 = 75
    panel_x2 = width - 15
    panel_y2 = 335

    _draw_panel(frame, panel_x1, panel_y1, panel_x2, panel_y2)

    x = panel_x1 + 18
    y = panel_y1 + 32
    line_gap = 30

    _draw_text(frame, "CAMERA       : ONLINE", x, y, color=(220, 220, 220))
    y += line_gap

    _draw_text(frame, "MODEL        : LOADED", x, y, color=(220, 220, 220))
    y += line_gap

    _draw_text(frame, "MISSION MODE : TARGET DETECTION", x, y, color=(220, 220, 220))
    y += line_gap + 8

    if best_detection is not None:
        class_name = best_detection.get("class_name", "unknown")
        confidence = best_detection.get("confidence", 0)
        box = best_detection.get("box", None)

        status = "TARGET DETECTED"

        # Kutu bilgisi varsa hedef kutusunu ciz
        if box is not None:
            x1, y1, x2, y2 = map(int, box)

            target_center_x = (x1 + x2) // 2
            target_center_y = (y1 + y2) // 2

            offset_x = target_center_x - center_x
            offset_y = target_center_y - center_y

            # Hedef kutusu
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 220, 0), 2)

            # Hedef merkezi
            cv2.circle(frame, (target_center_x, target_center_y), 5, (0, 220, 0), -1)
            cv2.line(frame, (center_x, center_y), (target_center_x, target_center_y), (0, 180, 0), 1)

            # Kutunun ustunde class adi
            label = f"{class_name}  {confidence * 100:.0f}%"
            cv2.rectangle(frame, (x1, max(y1 - 28, 0)), (x1 + 250, y1), (0, 120, 0), -1)
            _draw_text(frame, label, x1 + 6, max(y1 - 8, 18), scale=0.5, color=(255, 255, 255))

        else:
            offset_x = 0
            offset_y = 0

        _draw_text(frame, f"TARGET       : {class_name}", x, y, color=(255, 255, 255), thickness=2)
        y += line_gap

        _draw_text(frame, f"CONFIDENCE   : {confidence * 100:.0f}%", x, y, color=(255, 255, 255))
        y += line_gap

        _draw_text(frame, f"STATUS       : {status}", x, y, color=(0, 255, 0), thickness=2)
        y += line_gap

        _draw_text(frame, f"OFFSET       : X:{offset_x:+d}  Y:{offset_y:+d}", x, y, color=(220, 220, 220))

    else:
        _draw_text(frame, "TARGET       : NONE", x, y, color=(255, 255, 255), thickness=2)
        y += line_gap

        _draw_text(frame, "CONFIDENCE   : -", x, y, color=(220, 220, 220))
        y += line_gap

        _draw_text(frame, "STATUS       : SEARCHING TARGET", x, y, color=(0, 220, 255), thickness=2)
        y += line_gap

        _draw_text(frame, "OFFSET       : -", x, y, color=(220, 220, 220))

    # -----------------------------
    # Alt durum seridi
    # -----------------------------
    cv2.rectangle(frame, (0, height - 42), (width, height), (15, 15, 15), -1)

    if best_detection is not None:
        bottom_status = "SYSTEM STATUS: TARGET DETECTED - DATA READY FOR MISSION LOGIC"
        bottom_color = (0, 255, 0)
    else:
        bottom_status = "SYSTEM STATUS: SEARCHING TARGET - NO MISSION DECISION"
        bottom_color = (0, 220, 255)

    _draw_text(
        frame,
        bottom_status,
        18,
        height - 15,
        scale=0.55,
        color=bottom_color,
        thickness=1
    )

    return frame