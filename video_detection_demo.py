import time
import cv2

from config import CAMERA_INDEX
from detector import DetectorSystem
from video_ui import draw_video_ui


WINDOW_NAME = "TEKNOFEST IHA GOREV SISTEMI"

DISPLAY_WIDTH = 1280
DISPLAY_HEIGHT = 720

# Gorev sirasi kesin:
# 1) mavi_altigen
# 2) kirmizi_ucgen
MISSION_SEQUENCE = ["mavi_altigen", "kirmizi_ucgen"]

# Hedefin tamamlandi sayilmasi icin kac kare ust uste dogru algilanmasi gerekir.
# 18 kare, 20-30 FPS kamerada yaklasik 0.6 - 0.9 saniye demektir.
STABLE_REQUIRED = 18

# Yuku birakiyor durumunun ekranda kac saniye gorunecegi.
DROP_SECONDS = 2.0

# Bir hedef tamamlandiktan sonra siradaki hedefe gecis bekleme suresi.
TRANSITION_SECONDS = 2.0


def calculate_fps(prev_time):
    current_time = time.time()

    if prev_time == 0:
        fps = 0
    else:
        fps = 1 / (current_time - prev_time)

    return fps, current_time


def choose_best_detection(detections):
    if not detections:
        return None

    return max(
        detections,
        key=lambda detection: detection.get("confidence", 0)
    )


def choose_detection_for_expected_target(detections, expected_target):
    if not detections or expected_target is None:
        return None

    expected_detections = [
        detection for detection in detections
        if detection.get("class_name") == expected_target
    ]

    if not expected_detections:
        return None

    return max(
        expected_detections,
        key=lambda detection: detection.get("confidence", 0)
    )


def get_expected_target(completed_targets):
    for target in MISSION_SEQUENCE:
        if not completed_targets[target]:
            return target

    return None


def reset_completed_targets():
    return {
        "mavi_altigen": False,
        "kirmizi_ucgen": False
    }


def is_completed_target(class_name, completed_targets):
    return completed_targets.get(class_name, False)


def main():
    print("=" * 50)
    print("TEKNOFEST IHA GOREV SISTEMI")
    print("Kamera hedef algilama baslatiliyor...")
    print("Cikis icin q tusuna basin.")
    print("Hedef sirasi sifirlamak icin r tusuna basin.")
    print("=" * 50)

    print("YOLO modeli yukleniyor...")
    detector = DetectorSystem()
    print("YOLO modeli hazir.")

    camera = cv2.VideoCapture(CAMERA_INDEX)
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, DISPLAY_WIDTH)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, DISPLAY_HEIGHT)

    if not camera.isOpened():
        print("Kamera acilamadi.")
        return

    completed_targets = reset_completed_targets()

    stable_count = 0
    prev_time = 0

    drop_target = None
    drop_until = 0

    transition_until = 0
    transition_message = ""

    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(WINDOW_NAME, DISPLAY_WIDTH, DISPLAY_HEIGHT)

    while True:
        success, frame = camera.read()

        if not success:
            print("Goruntu alinamadi.")
            break

        frame = cv2.resize(frame, (DISPLAY_WIDTH, DISPLAY_HEIGHT))

        fps, prev_time = calculate_fps(prev_time)

        detections = detector.detect(frame)

        current_time = time.time()

        expected_target = get_expected_target(completed_targets)

        # -------------------------------------------------
        # Yuk birakma durumu
        # -------------------------------------------------
        if drop_target is not None:
            mission_status = "YUK BIRAKILIYOR"

            if current_time >= drop_until:
                completed_targets[drop_target] = True

                print("=" * 50)
                print(f"{drop_target} TAMAMLANDI")
                print("=" * 50)

                finished_target = drop_target
                drop_target = None
                stable_count = 0

                expected_target = get_expected_target(completed_targets)

                if expected_target is None:
                    mission_status = "GOREV TAMAMLANDI"
                    transition_until = 0
                    transition_message = ""
                else:
                    transition_message = (
                        f"{finished_target} TAMAMLANDI"
                    )
                    transition_until = current_time + TRANSITION_SECONDS
                    mission_status = transition_message

            display_frame = draw_video_ui(
                frame=frame,
                detections=detections,
                fps=fps,
                expected_target=drop_target if drop_target is not None else expected_target,
                mission_status=mission_status,
                completed_targets=completed_targets,
                stable_count=stable_count,
                stable_required=STABLE_REQUIRED
            )

            cv2.imshow(WINDOW_NAME, display_frame)

        # -------------------------------------------------
        # Tum gorev tamamlandiysa
        # -------------------------------------------------
        elif expected_target is None:
            mission_status = "GOREV TAMAMLANDI"
            stable_count = 0

            display_frame = draw_video_ui(
                frame=frame,
                detections=[],
                fps=fps,
                expected_target=None,
                mission_status=mission_status,
                completed_targets=completed_targets,
                stable_count=stable_count,
                stable_required=STABLE_REQUIRED
            )

            cv2.imshow(WINDOW_NAME, display_frame)

        # -------------------------------------------------
        # Hedefler arasi gecis bekleme durumu
        # -------------------------------------------------
        elif current_time < transition_until:
            mission_status = transition_message

            display_frame = draw_video_ui(
                frame=frame,
                detections=[],
                fps=fps,
                expected_target=expected_target,
                mission_status=mission_status,
                completed_targets=completed_targets,
                stable_count=0,
                stable_required=STABLE_REQUIRED
            )

            cv2.imshow(WINDOW_NAME, display_frame)

        # -------------------------------------------------
        # Normal otonom hedef arama ve dogrulama
        # -------------------------------------------------
        else:
            expected_detection = choose_detection_for_expected_target(
                detections=detections,
                expected_target=expected_target
            )

            best_detection = choose_best_detection(detections)

            if expected_detection is not None:
                stable_count += 1
                mission_status = f"HEDEF ALGILANDI {stable_count}/{STABLE_REQUIRED}"

                if stable_count >= STABLE_REQUIRED:
                    drop_target = expected_target
                    drop_until = current_time + DROP_SECONDS
                    stable_count = 0
                    mission_status = "YUK BIRAKILIYOR"

            elif best_detection is None:
                stable_count = 0
                mission_status = "HEDEF ARANIYOR"

            else:
                detected_class = best_detection.get("class_name", "unknown")

                if is_completed_target(detected_class, completed_targets):
                    stable_count = 0
                    mission_status = "TAMAMLANMIS HEDEF YOK SAYILDI"
                else:
                    stable_count = 0
                    mission_status = f"YANLIS HEDEF: {detected_class}"

            display_frame = draw_video_ui(
                frame=frame,
                detections=detections,
                fps=fps,
                expected_target=expected_target,
                mission_status=mission_status,
                completed_targets=completed_targets,
                stable_count=stable_count,
                stable_required=STABLE_REQUIRED
            )

            cv2.imshow(WINDOW_NAME, display_frame)

        key = cv2.waitKey(1) & 0xFF

        if key == ord("q"):
            print("Sistem kullanici tarafindan durduruldu.")
            break

        if key == ord("r"):
            completed_targets = reset_completed_targets()
            stable_count = 0
            drop_target = None
            drop_until = 0
            transition_until = 0
            transition_message = ""

            print("=" * 50)
            print("Hedef sirasi sifirlandi.")
            print("Ilk hedef: mavi_altigen")
            print("=" * 50)

    camera.release()
    cv2.destroyAllWindows()

    print("Hedef algilama sistemi kapatildi.")


if __name__ == "__main__":
    main()