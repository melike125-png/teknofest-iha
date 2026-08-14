import time
import cv2
import numpy as np
from ultralytics import YOLO

# ============================================================
# TEKNOFEST IHA - PROFESYONEL VIDEO PANEL
# - Web/Flask yok
# - Kamera solda
# - Sade ve profesyonel bilgi paneli sagda
# - Terminalde koordinatlar yazilir
# - Cikis: kamera penceresindeyken q tusu
# ============================================================

WINDOW_NAME = "TEKNOFEST IHA - KAMERA SISTEMI"
MODEL_PATH = "best.pt"
CAMERA_INDEX = 0

# Performans icin bu degerler dusuk tutuldu.
DISPLAY_W = 640
DISPLAY_H = 480

INFER_W = 320
INFER_H = 240

PANEL_W = 400

# YOLO her karede degil, belirli araliklarla calisir.
# Daha akici goruntu icin 5-8 arasi iyi.
DETECT_EVERY_N_FRAMES = 5
PRINT_EVERY_SECONDS = 2.0

CONF_LIMIT = 0.50
IOU_LIMIT = 0.20

MISSION_SEQUENCE = ["mavi_altigen", "kirmizi_ucgen"]
STABLE_SECONDS = 4.0


# =========================
# RENK PALETI
# =========================
COLOR_BG = (10, 14, 20)
COLOR_PANEL = (18, 24, 34)
COLOR_CARD = (25, 33, 46)
COLOR_BORDER = (55, 68, 88)

COLOR_TEXT = (238, 242, 247)
COLOR_MUTED = (145, 158, 176)

COLOR_ACCENT = (255, 185, 75)
COLOR_BLUE = (255, 170, 70)
COLOR_GREEN = (90, 220, 120)
COLOR_YELLOW = (70, 210, 240)
COLOR_RED = (80, 100, 255)

COLOR_BOX_OK = (80, 220, 120)
COLOR_BOX_BAD = (80, 100, 255)
COLOR_CENTER = (70, 220, 240)


model = YOLO(MODEL_PATH)

cap = cv2.VideoCapture(CAMERA_INDEX)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, DISPLAY_W)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, DISPLAY_H)
cap.set(cv2.CAP_PROP_FPS, 30)
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

if not cap.isOpened():
    print("KAMERA OFFSETSI: Kamera acilamadi. USB kameranin Raspberry Pi'ye takili oldugunu kontrol edin.")
    raise SystemExit


target_index = 0
stable_start_time = None
mission_done = False

frame_count = 0
prev_time = time.time()
last_print_time = 0.0
fps = 0.0

last_detection = None
last_status = "HEDEF ARANIYOR"
last_center = "-"
last_error = "-"
last_box = "-"
last_conf = "-"
last_detected = "-"


def put_text(img, value, x, y, size=0.50, color=COLOR_TEXT, thick=1):
    cv2.putText(
        img,
        value,
        (x, y),
        cv2.FONT_HERSHEY_SIMPLEX,
        size,
        color,
        thick,
        cv2.LINE_AA
    )


def draw_card(panel, x, y, w, h):
    cv2.rectangle(panel, (x, y), (x + w, y + h), COLOR_CARD, -1)
    cv2.rectangle(panel, (x, y), (x + w, y + h), COLOR_BORDER, 1)


def draw_header(panel):
    put_text(panel, "TEKNOFEST IHA", 24, 38, 0.82, COLOR_TEXT, 2)
    put_text(panel, "Hedef Algilama Sistemi", 24, 66, 0.46, COLOR_MUTED, 1)
    cv2.line(panel, (24, 82), (PANEL_W - 24, 82), COLOR_BORDER, 1)


def draw_status_badge(panel, status):
    x, y, w, h = 24, 92, PANEL_W - 48, 42

    if "YANLIS" in status:
        fill = (35, 25, 40)
        color = COLOR_RED
    elif "YOK" in status:
        fill = (35, 32, 24)
        color = COLOR_YELLOW
    else:
        fill = (22, 38, 30)
        color = COLOR_GREEN

    cv2.rectangle(panel, (x, y), (x + w, y + h), fill, -1)
    cv2.rectangle(panel, (x, y), (x + w, y + h), color, 1)
    put_text(panel, status, x + 14, y + 27, 0.56, color, 2)


def field(panel, label, value, x, y, value_color=COLOR_TEXT):
    put_text(panel, label, x, y, 0.39, COLOR_MUTED, 1)
    put_text(panel, value, x, y + 27, 0.58, value_color, 2)


def draw_panel(next_target, detected, status, conf, step, fps_text, center, error, box):
    panel = np.zeros((DISPLAY_H, PANEL_W, 3), dtype=np.uint8)
    panel[:] = COLOR_PANEL

    draw_header(panel)
    draw_status_badge(panel, status)

    # Kart 1: hedef bilgisi
    draw_card(panel, 24, 150, PANEL_W - 48, 92)
    field(panel, "SIRADAKI HEDEF", next_target, 40, 180, COLOR_BLUE)
    field(panel, "ALGILANAN", detected, 220, 180, COLOR_TEXT)

    # Kart 2: performans ve gorev
    draw_card(panel, 24, 255, PANEL_W - 48, 62)
    field(panel, "GUVEN", conf, 40, 282, COLOR_TEXT)
    field(panel, "ADIM", step, 150, 282, COLOR_TEXT)
    field(panel, "FPS", fps_text, 250, 282, COLOR_TEXT)

    # Kart 3: koordinat
    draw_card(panel, 24, 330, PANEL_W - 48, 48)
    put_text(panel, f"MERKEZ  {center}", 40, 354, 0.43, COLOR_TEXT, 1)
    put_text(panel, f"HATA  {error}", 220, 354, 0.43, COLOR_TEXT, 1)

    # Kutu koordinatini en alta daha kucuk yaz
    put_text(panel, f"KUTU {box}", 40, 374, 0.38, COLOR_MUTED, 1)

    return panel


def run_detection(frame):
    infer_frame = cv2.resize(frame, (INFER_W, INFER_H))

    results = model(
        infer_frame,
        conf=CONF_LIMIT,
        iou=IOU_LIMIT,
        imgsz=320,
        verbose=False
    )

    best = None

    for result in results:
        if result.boxes is None:
            continue

        for box in result.boxes:
            conf = float(box.conf[0])
            cls_id = int(box.cls[0])
            class_name = model.names[cls_id]

            x1, y1, x2, y2 = map(int, box.xyxy[0])

            area = max(0, x2 - x1) * max(0, y2 - y1)
            area_ratio = min(area / float(INFER_W * INFER_H), 1.0)
            score = conf * 0.75 + area_ratio * 0.25

            if best is None or score > best["score"]:
                best = {
                    "class_name": class_name,
                    "conf": conf,
                    "box": (x1, y1, x2, y2),
                    "score": score
                }

    return best


def scale_box_to_display(box):
    x1, y1, x2, y2 = box
    sx = DISPLAY_W / float(INFER_W)
    sy = DISPLAY_H / float(INFER_H)

    return (
        int(x1 * sx),
        int(y1 * sy),
        int(x2 * sx),
        int(y2 * sy)
    )


def print_terminal_line(next_target, detected, status, conf, center, error, box, fps_text):
    clock = time.strftime("%H:%M:%S")

    if next_target == "mavi_altigen":
        step_text = "1/2"
    elif next_target == "kirmizi_ucgen":
        step_text = "2/2"
    else:
        step_text = "2/2"

    try:
        conf_value = float(conf)
        if conf_value <= 1:
            conf_text = f"%{int(conf_value * 100)}"
        else:
            conf_text = f"%{int(conf_value)}"
    except Exception:
        conf_text = str(conf)

    if detected == "-" or status in ["HEDEF YOK", "HEDEF ARANIYOR", "SEARCHING"]:
        print(
            f"[{clock}] BEKLEME  |  siradaki={next_target}  |  adim={step_text}  |  fps={fps_text}",
            flush=True
        )
    elif status in ["ALGILAMA TAMAMLANDI", "ALGILAMA TAMAMLANDI"]:
        print(
            f"[{clock}] ALGILAMA ALGILAMA TAMAMLANDI  |  hedef={detected}  |  guven={conf_text}  |  hedef_merkezi={center}",
            flush=True
        )
    else:
        print(
            f"[{clock}] KILITLENDI  |  hedef={detected}  |  guven={conf_text}  |  hedef_merkezi={center}  |  merkezden_sapma={error}",
            flush=True
        )
print("==============================================")
print("TEKNOFEST IHA KAMERA SISTEMI BASLADI")
print("Terminalde hedef merkezi ve merkezden sapma degeri gosteriliyor.")
print("Cikis icin kamera penceresindeyken q tusuna basin.")
print("==============================================")

try:
    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL | cv2.WINDOW_GUI_NORMAL)
except Exception:
    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
cv2.resizeWindow(WINDOW_NAME, DISPLAY_W + PANEL_W, DISPLAY_H)

while True:
    ret, frame = cap.read()

    if not ret:
        print("KAMERA OFFSETSI: Goruntu alinamadi.")
        break

    frame = cv2.resize(frame, (DISPLAY_W, DISPLAY_H))

    now = time.time()
    fps = 1.0 / max(now - prev_time, 0.001)
    prev_time = now

    frame_count += 1

    next_target = MISSION_SEQUENCE[target_index] if not mission_done else "-"

    if frame_count % DETECT_EVERY_N_FRAMES == 0:
        last_detection = run_detection(frame)

    if last_detection is None:
        stable_start_time = None
        last_detected = "-"
        last_conf = "-"
        last_status = "HEDEF ARANIYOR"
        last_center = "-"
        last_error = "-"
        last_box = "-"
    else:
        display_box = scale_box_to_display(last_detection["box"])
        x1, y1, x2, y2 = display_box

        detected = last_detection["class_name"]
        conf = last_detection["conf"]

        last_detected = detected
        last_conf = f"{conf:.2f}"

        cx = int((x1 + x2) / 2)
        cy = int((y1 + y2) / 2)
        ex = cx - int(DISPLAY_W / 2)
        ey = cy - int(DISPLAY_H / 2)

        last_center = f"({cx},{cy})"
        last_error = f"({ex},{ey})"
        last_box = f"({x1},{y1},{x2},{y2})"

        is_correct = detected == next_target

        if is_correct and not mission_done:
            if stable_start_time is None:
                stable_start_time = time.time()

            elapsed = time.time() - stable_start_time
            remaining = max(0.0, STABLE_SECONDS - elapsed)

            if elapsed >= STABLE_SECONDS:
                last_status = "HEDEF ONAYLANDI"
                target_index += 1
                stable_start_time = None

                if target_index >= len(MISSION_SEQUENCE):
                    mission_done = True
                    last_status = "ALGILAMA TAMAMLANDI"
            else:
                last_status = f"DOGRU HEDEF {remaining:.1f}s"
        else:
            stable_start_time = None
            last_status = "ALGILAMA TAMAMLANDI" if mission_done else "YANLIS HEDEF"

        color = COLOR_BOX_OK if is_correct else COLOR_BOX_BAD
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        cv2.circle(frame, (cx, cy), 5, COLOR_CENTER, -1)
        put_text(frame, f"{detected} {conf:.2f}", x1, max(25, y1 - 8), 0.52, color, 2)

    step_text = f"{min(target_index + 1, len(MISSION_SEQUENCE))}/{len(MISSION_SEQUENCE)}"
    if mission_done:
        step_text = f"{len(MISSION_SEQUENCE)}/{len(MISSION_SEQUENCE)}"

    fps_text = f"{fps:.1f}"

    if now - last_print_time >= PRINT_EVERY_SECONDS:
        print_terminal_line(
            next_target,
            last_detected,
            last_status,
            last_conf,
            last_center,
            last_error,
            last_box,
            fps_text
        )
        last_print_time = now

    panel = draw_panel(
        next_target,
        last_detected,
        last_status,
        last_conf,
        step_text,
        fps_text,
        last_center,
        last_error,
        last_box
    )

    canvas = cv2.hconcat([frame, panel])

    cv2.imshow(WINDOW_NAME, canvas)

    key = cv2.waitKey(1) & 0xFF

    if key == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
print("TEKNOFEST IHA kamera sistemi kapatildi.")
