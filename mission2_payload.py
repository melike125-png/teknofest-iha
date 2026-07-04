import time
import json
import os
import cv2

from config import (
    STABLE_LIMIT,
    VIDEO_OUTPUT_NAME,
    TARGET_BLUE_HEXAGON,
    TARGET_RED_TRIANGLE,
    MISSION_ALTITUDE,
    DROP_ALTITUDE,
    CENTER_TOLERANCE_X,
    CENTER_TOLERANCE_Y
)

from camera import CameraSystem
from detector import DetectorSystem
from payload import PayloadSystem
from targeting import TargetingSystem
from ui import draw_professional_camera_screen
from logger import LoggerSystem
from failsafe import FailsafeSystem
from flight_controller import FlightController


WINDOW_NAME = "TEKNOFEST IHA 2. GOREV SISTEMI"
DISPLAY_WIDTH = 1280
DISPLAY_HEIGHT = 720

MISSION2_COORDINATE_FILE = "mission2_coordinates.json"

MISSION_SAFE_MODE = True
ALLOW_PAYLOAD_DROP = False

class Mission2UI:

    def draw(
        self,
        frame,
        target_data=None,
        current_target=None,
        status="",
        direction="",
        fps=0,
        stable_count=0,
        mission_state="",
        payload_status=""
    ):
        display_frame = frame.copy()

        h, w = display_frame.shape[:2]

        if target_data is not None:
            box = target_data.get("box")

            if box is not None:
                x1, y1, x2, y2 = box
                cv2.rectangle(display_frame, (x1, y1), (x2, y2), (0, 255, 0), 3)

                label = target_data.get("class_name", "target")
                confidence = target_data.get("confidence", 0)

                cv2.putText(
                    display_frame,
                    f"{label} {confidence:.2f}",
                    (x1, max(30, y1 - 10)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 0),
                    2
                )

                center = target_data.get("target_center")

                if center is not None:
                    cx, cy = center
                    cv2.circle(display_frame, (cx, cy), 6, (0, 255, 0), -1)
                    cv2.line(display_frame, (w // 2, h // 2), (cx, cy), (0, 255, 0), 2)

        cv2.circle(display_frame, (w // 2, h // 2), 7, (0, 255, 255), -1)
        cv2.line(display_frame, (w // 2 - 25, h // 2), (w // 2 + 25, h // 2), (0, 255, 255), 2)
        cv2.line(display_frame, (w // 2, h // 2 - 25), (w // 2, h // 2 + 25), (0, 255, 255), 2)

        panel_h = 190
        overlay = display_frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, panel_h), (0, 0, 0), -1)
        display_frame = cv2.addWeighted(overlay, 0.65, display_frame, 0.35, 0)

        if current_target is None:
            current_target_text = "YOK"
        else:
            current_target_text = current_target

        lines = [
            f"2. GOREV | FPS: {fps:.1f}",
            f"SIRADAKI HEDEF: {current_target_text}",
            f"DURUM: {status}",
            f"YON: {direction}",
            f"YUK: {payload_status}",
            f"STABLE: {stable_count}"
        ]

        y = 32

        for index, line in enumerate(lines):
            if index == 0:
                color = (0, 255, 255)
                scale = 0.75
                thickness = 2
            elif "SIRADAKI" in line:
                color = (255, 255, 255)
                scale = 0.65
                thickness = 2
            elif "DURUM" in line:
                color = (0, 255, 255)
                scale = 0.65
                thickness = 2
            else:
                color = (220, 220, 220)
                scale = 0.62
                thickness = 2

            cv2.putText(
                display_frame,
                line,
                (25, y),
                cv2.FONT_HERSHEY_SIMPLEX,
                scale,
                color,
                thickness
            )

            y += 30

        return display_frame
        
class Mission2Payload:

    def __init__(self):

        self.logger = LoggerSystem()
        self.logger.system_started()

        self.failsafe = FailsafeSystem()

        self.camera = CameraSystem()
        self.detector = DetectorSystem()

        if ALLOW_PAYLOAD_DROP:
            self.payload = PayloadSystem()
        else:
            self.payload = None
            print("GUVENLI MOD -> Payload sistemi fiziksel olarak baslatilmadi.")

        self.targeting = TargetingSystem()
        self.ui = Mission2UI()
        self.flight_controller = FlightController(use_real_cube=True)

        self.completed_targets = {
            TARGET_BLUE_HEXAGON: False,
            TARGET_RED_TRIANGLE: False
        }

        self.start_point = None
        self.finish_point = None

        self.stable_count = 0
        self.prev_time = 0
        self.video_writer = None

        self.last_target_log_time = 0
        self.last_lost_log_time = 0
        self.last_wrong_target_log_time = 0
        self.last_approach_log_time = 0

        self.TARGET_LOG_INTERVAL = 0.7
        self.LOST_LOG_INTERVAL = 1.0
        self.WRONG_TARGET_LOG_INTERVAL = 1.0
        self.APPROACH_LOG_INTERVAL = 0.5

        self.finish_point_reached = False

    def read_float(self, text):

        while True:
            value = input(text).strip()
            value = value.replace(",", ".")

            try:
                return float(value)
            except ValueError:
                print("Gecersiz deger. Tekrar gir.")

    def collect_coordinates(self):

        print("=" * 50)
        print("2. GOREV BASLANGIC VE BITIS KOORDINATLARI")
        print("=" * 50)

        print("Baslangic noktasi koordinatlarini gir")
        start_lat = self.read_float("Baslangic latitude: ")
        start_lon = self.read_float("Baslangic longitude: ")

        print("-" * 50)

        print("Bitis noktasi koordinatlarini gir")
        finish_lat = self.read_float("Bitis latitude: ")
        finish_lon = self.read_float("Bitis longitude: ")

        self.start_point = {
            "lat": start_lat,
            "lon": start_lon
        }

        self.finish_point = {
            "lat": finish_lat,
            "lon": finish_lon
        }

        self.save_coordinates()

    def save_coordinates(self):

        data = {
            "start_point": self.start_point,
            "finish_point": self.finish_point
        }

        with open(MISSION2_COORDINATE_FILE, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4)

        print("=" * 50)
        print("2. gorev koordinatlari kaydedildi")
        print("Dosya:", MISSION2_COORDINATE_FILE)
        print("=" * 50)

    def load_coordinates(self):

        if not os.path.exists(MISSION2_COORDINATE_FILE):
            return False

        with open(MISSION2_COORDINATE_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)

        self.start_point = data.get("start_point")
        self.finish_point = data.get("finish_point")

        if self.start_point is None or self.finish_point is None:
            return False

        return True

    def prepare_coordinates(self):

        coordinates_loaded = self.load_coordinates()

        if coordinates_loaded:
            print("Kayitli 2. gorev koordinatlari bulundu.")
            self.show_coordinates()

            use_saved = input("Kayitli koordinatlar kullanilsin mi? E/H: ").strip().lower()

            if use_saved != "e":
                self.collect_coordinates()
        else:
            print("Kayitli 2. gorev koordinati bulunamadi.")
            self.collect_coordinates()

        self.show_coordinates()

    def show_coordinates(self):

        print("=" * 50)
        print("2. GOREV KOORDINAT OZETI")
        print("=" * 50)

        print("Baslangic lat:", self.start_point.get("lat"))
        print("Baslangic lon:", self.start_point.get("lon"))

        print("-" * 50)

        print("Bitis lat:", self.finish_point.get("lat"))
        print("Bitis lon:", self.finish_point.get("lon"))

        print("=" * 50)

    def get_expected_target(self):

        return self.targeting.get_current_mission_target(
            self.completed_targets
        )

    def all_targets_completed(self):

        return (
            self.completed_targets[TARGET_BLUE_HEXAGON]
            and self.completed_targets[TARGET_RED_TRIANGLE]
        )

    def calculate_fps(self):

        current_time = time.time()

        if self.prev_time == 0:
            fps = 0
        else:
            fps = 1 / (current_time - self.prev_time)

        self.prev_time = current_time

        return fps

    def can_print(self, last_time, interval):

        current_time = time.time()

        if current_time - last_time >= interval:
            return True

        return False

    def format_panel_direction(self, target_data):

        if target_data is None:
            return "HEDEF_YOK"

        directions = []
        error_x = target_data.get("error_x", 0)
        error_y = target_data.get("error_y", 0)

        if error_x > CENTER_TOLERANCE_X:
            directions.append("SAG")
        elif error_x < -CENTER_TOLERANCE_X:
            directions.append("SOL")

        if error_y > CENTER_TOLERANCE_Y:
            directions.append("ASAGI")
        elif error_y < -CENTER_TOLERANCE_Y:
            directions.append("YUKARI")

        if not directions:
            return "MERKEZDE"

        return " ".join(directions)

    def start_video_recording(self):

        width = self.camera.get_width()
        height = self.camera.get_height()

        fourcc = cv2.VideoWriter_fourcc(*"mp4v")

        self.video_writer = cv2.VideoWriter(
            VIDEO_OUTPUT_NAME,
            fourcc,
            20.0,
            (width, height)
        )

    def get_payload_name_for_target(self, target_name):

        if target_name == TARGET_BLUE_HEXAGON:
            return "KIRMIZI YUK"

        if target_name == TARGET_RED_TRIANGLE:
            return "MAVI YUK"

        return "BILINMEYEN YUK"

    def release_payload_sequence(self, current_target):

        payload_name = self.get_payload_name_for_target(current_target)

        print("=" * 50)
        print("YUK BIRAKMA SEKANSI BASLADI")
        print("Hedef:", current_target)
        print("Birakilacak yuk:", payload_name)
        print("=" * 50)

        self.flight_controller.hover()
        time.sleep(0.5)

        self.flight_controller.descend(DROP_ALTITUDE)
        time.sleep(1)

        if ALLOW_PAYLOAD_DROP and self.payload is not None:
            self.payload.drop_payload(current_target)
        else:
            print(f"GUVENLI MOD -> {payload_name} birakma engellendi. Hedef: {current_target}")
            self.logger.write_log(f"GUVENLI MOD -> {payload_name} simule edildi. Hedef: {current_target}")

        time.sleep(0.5)

        self.flight_controller.ascend(MISSION_ALTITUDE)
        time.sleep(0.5)

        self.flight_controller.hover()

        print("=" * 50)
        print("YUK BIRAKMA SEKANSI BITTI")
        print("=" * 50)

    def go_to_finish_point(self):

        if self.finish_point is None:
            print("Bitis noktasi yok. Bitis noktasina gidilemiyor.")
            return

        print("=" * 50)
        print("BITIS NOKTASINA GIDIS")
        print("=" * 50)
        print("Bitis lat:", self.finish_point.get("lat"))
        print("Bitis lon:", self.finish_point.get("lon"))

        if MISSION_SAFE_MODE:
            print("GUVENLI MOD -> Bitis noktasina gercek ucus komutu gonderilmedi.")
        else:
            print("GERCEK MOD -> Bitis noktasina gidis komutu burada gonderilecek.")

        self.finish_point_reached = True

        print("=" * 50)

    def finish_mission(self, frame, target_data, fps):

        self.go_to_finish_point()

        status = "GOREV TAMAMLANDI"
        direction = "BITIS NOKTASI"
        mission_state = "GOREV_TAMAMLANDI"
        payload_status = "BIRAKILDI"

        self.logger.mission_completed()

        self.ui.draw(
            frame=frame,
            target_data=target_data,
            current_target=None,
            status=status,
            direction=direction,
            fps=fps,
            stable_count=0,
            mission_state=mission_state,
            payload_status=payload_status
        )

        if self.video_writer is not None:
            self.video_writer.write(frame)

        print("=" * 50)
        print("2. GOREV TAMAMLANDI")
        print("KIRMIZI YUK -> MAVI ALTIGEN")
        print("MAVI YUK -> KIRMIZI UCGEN")
        print("BITIS NOKTASINA GIDIS TAMAMLANDI / SIMULE EDILDI")
        print("=" * 50)

        time.sleep(2)

    def find_wrong_detected_target(self, detections, expected_target):

        if expected_target is None:
            return None

        for detection in detections:

            class_name = detection.get("class_name")

            if class_name != expected_target:
                return class_name

        return None

    def start(self):

        print("=" * 50)
        print("2. GOREV BASLATILIYOR")
        print("GORUNTU ISLEME ILE YUK BIRAKMA")
        print("=" * 50)
        print("MISSION SAFE MODE:", MISSION_SAFE_MODE)
        print("ALLOW PAYLOAD DROP:", ALLOW_PAYLOAD_DROP)
        print("=" * 50)

        self.prepare_coordinates()

        connected = self.flight_controller.connect()

        if not connected:
            print("UYARI -> Cube baglantisi kurulamadi.")
            print("2. gorev guvenli test modunda devam edecek.")
            self.logger.write_log("UYARI -> Cube baglantisi kurulamadi")

        print("=" * 50)
        print("2. GOREV HEDEF SIRASI")
        print("1 -> mavi_altigen: KIRMIZI YUK")
        print("2 -> kirmizi_ucgen: MAVI YUK")
        print("3 -> bitis noktasi")
        print("=" * 50)

        if not self.camera.is_opened():

            print("Kamera acilamadi.")
            self.logger.camera_failed()
            self.stop()
            return

        self.logger.camera_opened()
        self.start_video_recording()

        print("2. gorev kamera sistemi basladi.")
        self.logger.write_log("2. GOREV BASLADI")

        cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(WINDOW_NAME, DISPLAY_WIDTH, DISPLAY_HEIGHT)

        while True:

            expected_target = self.get_expected_target()

            frame = self.camera.read_frame()

            if frame is None:

                print("Goruntu alinamadi.")
                self.logger.write_log("GORUNTU ALINAMADI")
                break

            self.failsafe.update_frame_time()

            fps = self.calculate_fps()

            detections = self.detector.detect(frame)

            target_data = self.targeting.find_best_target(
                detections=detections,
                completed_targets=self.completed_targets,
                frame=frame
            )

            wrong_target = self.find_wrong_detected_target(
                detections=detections,
                expected_target=expected_target
            )

            mission_state = "HEDEF_ARIYOR"
            direction = "HEDEF_YOK"
            payload_status = "BEKLIYOR"
            status = "HEDEF YOK"
            current_target = expected_target

            if expected_target is None:
                status = "GOREV TAMAMLANDI"
                direction = "TUM YUKLER BIRAKILDI"
                current_target = None
                mission_state = "GOREV_TAMAMLANDI"
                payload_status = "BIRAKILDI"

            if self.all_targets_completed():

                self.finish_mission(frame, target_data, fps)
                break

            elif target_data is not None:

                detected_target = target_data["class_name"]

                current_time = time.time()

                if self.can_print(
                    self.last_target_log_time,
                    self.TARGET_LOG_INTERVAL
                ):

                    self.failsafe.update_target_time()

                    self.logger.target_detected(
                        target_data["class_name"],
                        target_data["confidence"]
                    )

                    self.last_target_log_time = current_time

                is_centered = target_data["is_centered"]

                if is_centered:

                    self.stable_count += 1
                    payload_text = self.get_payload_name_for_target(detected_target)

                    status = f"HEDEF ORTADA - {self.stable_count}/{STABLE_LIMIT}"
                    direction = "MERKEZDE"
                    mission_state = "MERKEZDE"
                    payload_status = payload_text

                    if self.stable_count >= STABLE_LIMIT:

                        status = "YUK BIRAKMA SEKANSI"
                        direction = "MERKEZDE"
                        mission_state = "YUK_BIRAKILIYOR"
                        payload_status = payload_text

                        self.release_payload_sequence(detected_target)

                        self.logger.payload_dropped(detected_target)

                        self.completed_targets[detected_target] = True

                        self.stable_count = 0

                        next_target = self.get_expected_target()

                        if next_target is not None:
                            print("=" * 50)
                            print(f"SIRADAKI HEDEF ARTIK: {next_target}")
                            print("=" * 50)

                        time.sleep(1)

                else:

                    self.stable_count = 0
                    status = "HEDEF VAR - ORTALA"
                    direction = self.format_panel_direction(target_data)
                    mission_state = "HEDEFE_HIZALANIYOR"
                    payload_status = "BEKLIYOR"

                    error_x = target_data.get("error_x", 0)
                    error_y = target_data.get("error_y", 0)

                    current_time = time.time()

                    if self.can_print(
                        self.last_approach_log_time,
                        self.APPROACH_LOG_INTERVAL
                    ):

                        self.flight_controller.approach_target(error_x, error_y)

                        self.last_approach_log_time = current_time

            else:

                self.stable_count = 0

                current_time = time.time()

                if wrong_target is not None:

                    status = f"YANLIS HEDEF: {wrong_target}"
                    mission_state = "HEDEF_ARIYOR"
                    direction = "HEDEF_YOK"
                    payload_status = "BEKLIYOR"

                    if self.can_print(
                        self.last_wrong_target_log_time,
                        self.WRONG_TARGET_LOG_INTERVAL
                    ):

                        print(
                            f"YANLIS HEDEF GORULDU: {wrong_target} | "
                            f"BEKLENEN: {expected_target} | YOK SAYILDI"
                        )

                        self.last_wrong_target_log_time = current_time

                else:

                    if expected_target is not None:
                        status = "HEDEF YOK"
                        direction = "HEDEF_YOK"
                        mission_state = "HEDEF_ARIYOR"
                        payload_status = "BEKLIYOR"

                    if self.can_print(
                        self.last_lost_log_time,
                        self.LOST_LOG_INTERVAL
                    ):

                        self.logger.target_lost()
                        self.flight_controller.search_forward()

                        self.last_lost_log_time = current_time

            display_frame = self.ui.draw(
                frame=frame,
                target_data=target_data,
                current_target=current_target,
                status=status,
                direction=direction,
                fps=fps,
                stable_count=self.stable_count,
                mission_state=mission_state,
                payload_status=payload_status
            )

            if self.video_writer is not None:
                self.video_writer.write(frame)

            cv2.imshow(WINDOW_NAME, display_frame)

            key = cv2.waitKey(1) & 0xFF

            if key == ord("q"):
                print("Kullanici tarafindan durduruldu.")
                break

        self.stop()

    def stop(self):

        self.flight_controller.close()

        self.camera.release()

        if self.video_writer is not None:
            self.video_writer.release()

        cv2.destroyAllWindows()

        print("2. gorev sistemi kapatildi.")
        self.logger.system_stopped()