# mission.py

import time
import cv2

from config import (
    STABLE_LIMIT,
    VIDEO_OUTPUT_NAME,
    TARGET_BLUE_HEXAGON,
    TARGET_RED_TRIANGLE,
    MISSION_ALTITUDE,
    DROP_ALTITUDE
)

from camera import CameraSystem
from detector import DetectorSystem
from payload import PayloadSystem
from targeting import TargetingSystem
from ui import UISystem
from logger import LoggerSystem
from failsafe import FailsafeSystem
from flight_controller import FlightController


class MissionSystem:

    def __init__(self):

        self.logger = LoggerSystem()
        self.logger.system_started()

        self.failsafe = FailsafeSystem()

        self.camera = CameraSystem()
        self.detector = DetectorSystem()
        self.payload = PayloadSystem()
        self.targeting = TargetingSystem()
        self.ui = UISystem()
        self.flight_controller = FlightController()

        # Görevde tamamlanan hedefler burada tutulur.
        # İlk başta ikisi de tamamlanmamış olur.
        self.completed_targets = {
            TARGET_BLUE_HEXAGON: False,
            TARGET_RED_TRIANGLE: False
        }

        self.stable_count = 0
        self.prev_time = 0
        self.video_writer = None

        # 1. görev olan 8 çizme görevi bir kere yapılsın diye kullanılır.
        self.infinity8_done = False

    def get_expected_target(self):

        # Sıradaki hedefi targeting.py içindeki görev sırasına göre alıyoruz.
        # İlk başta mavi_altigen döner.
        # Mavi altıgen tamamlandıktan sonra kirmizi_ucgen döner.
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

    def perform_first_mission(self):

        if self.infinity8_done:
            return

        self.logger.write_log("1. GOREV BASLADI -> 8 CIZME")

        self.flight_controller.connect()
        self.flight_controller.perform_infinity8()

        self.infinity8_done = True

        self.logger.write_log("1. GOREV TAMAMLANDI -> 8 CIZME")

    def release_payload_sequence(self, current_target):

        print("=" * 50)
        print("YUK BIRAKMA SEKANSI BASLADI")
        print(f"Hedef: {current_target}")
        print("=" * 50)

        # Hedef merkezdeyken önce hover.
        self.flight_controller.hover()
        time.sleep(0.5)

        # Yük bırakma irtifasına alçal.
        self.flight_controller.descend(DROP_ALTITUDE)
        time.sleep(1)

        # İrtifa azaldıktan sonra ilgili servo açılır.
        self.payload.drop_payload(current_target)

        # Yük bırakıldıktan sonra tekrar görev irtifasına yüksel.
        time.sleep(0.5)
        self.flight_controller.ascend(MISSION_ALTITUDE)

        # Tekrar hover.
        time.sleep(0.5)
        self.flight_controller.hover()

        print("=" * 50)
        print("YUK BIRAKMA SEKANSI BITTI")
        print("=" * 50)

    def finish_mission(self, frame, target_data, fps):

        status = "GOREV TAMAMLANDI"
        direction = "TUM YUKLER BIRAKILDI"

        self.logger.mission_completed()

        self.ui.draw(
            frame=frame,
            target_data=target_data,
            current_target=None,
            status=status,
            direction=direction,
            fps=fps
        )

        if self.video_writer is not None:
            self.video_writer.write(frame)

        print("=" * 50)
        print("2. GOREV TAMAMLANDI")
        print("TUM YUKLER BIRAKILDI")
        print("=" * 50)

        time.sleep(2)

    def find_wrong_detected_target(self, detections, expected_target):

        # Bu fonksiyon şunu anlamak için var:
        # Model bir şey gördü ama sıradaki hedef o değil mi?
        #
        # Örneğin:
        # Beklenen hedef mavi_altigen iken kirmizi_ucgen görünürse
        # bunu "yanlış hedef" olarak ekranda göstereceğiz.

        if expected_target is None:
            return None

        for detection in detections:

            class_name = detection.get("class_name")

            if class_name != expected_target:
                return class_name

        return None

    def start(self):

        # Önce 1. görev yapılır.
        # Şu an test modunda sadece terminale koordinat yazar.
        self.perform_first_mission()

        # Sonra 2. görev yani görüntü işleme ile yük bırakma başlar.
        print("=" * 50)
        print("2. GOREV BASLADI -> GORUNTU ISLEME ILE YUK BIRAKMA")
        print("=" * 50)

        if not self.camera.is_opened():

            print("Kamera acilamadi.")
            self.logger.camera_failed()
            self.stop()
            return

        self.logger.camera_opened()
        self.start_video_recording()

        print("Gorev basladi.")
        self.logger.write_log("2. GOREV BASLADI")

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

            # targeting.py sadece sıradaki hedefi seçecek.
            # Örneğin sıradaki hedef mavi_altigen ise,
            # kirmizi_ucgen algılansa bile target_data None döner.
            target_data = self.targeting.find_best_target(
                detections=detections,
                completed_targets=self.completed_targets,
                frame=frame
            )

            wrong_target = self.find_wrong_detected_target(
                detections=detections,
                expected_target=expected_target
            )

            if expected_target is None:
                status = "GOREV TAMAMLANDI"
                direction = "TUM YUKLER BIRAKILDI"
                current_target = None

            else:
                status = f"SIRADAKI HEDEF: {expected_target}"
                direction = "ARAMA MODU"
                current_target = expected_target

            if self.all_targets_completed():

                self.finish_mission(frame, target_data, fps)
                break

            elif target_data is not None:

                detected_target = target_data["class_name"]

                self.failsafe.update_target_time()

                self.logger.target_detected(
                    target_data["class_name"],
                    target_data["confidence"]
                )

                is_centered = target_data["is_centered"]

                if is_centered:

                    self.stable_count += 1

                    status = f"HEDEF ORTADA - {self.stable_count}/{STABLE_LIMIT}"
                    direction = "MERKEZDE"

                    if self.stable_count >= STABLE_LIMIT:

                        status = "YUK BIRAKMA SEKANSI"
                        direction = "ALCAL - YUK BIRAK - YUKSEL"

                        self.release_payload_sequence(detected_target)

                        self.logger.payload_dropped(detected_target)

                        # Sadece doğru sıradaki hedef tamamlandı olarak işaretlenir.
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
                    direction = target_data["direction"]

                    error_x = target_data.get("error_x", 0)
                    error_y = target_data.get("error_y", 0)

                    self.flight_controller.approach_target(error_x, error_y)

            else:

                self.stable_count = 0

                if wrong_target is not None:

                    status = f"YANLIS HEDEF: {wrong_target}"
                    direction = f"BEKLENEN: {expected_target} - YOK SAYILDI"

                    print(
                        f"YANLIS HEDEF GORULDU: {wrong_target} | "
                        f"BEKLENEN: {expected_target} | YOK SAYILDI"
                    )

                else:

                    if expected_target is not None:
                        status = f"SIRADAKI HEDEF: {expected_target}"
                        direction = "HEDEF YOK - ARAMA MODU"

                    self.logger.target_lost()
                    self.flight_controller.search_forward()

            self.ui.draw(
                frame=frame,
                target_data=target_data,
                current_target=current_target,
                status=status,
                direction=direction,
                fps=fps
            )

            if self.video_writer is not None:
                self.video_writer.write(frame)

            cv2.imshow("TEKNOFEST IHA GOREV SISTEMI", frame)

            key = cv2.waitKey(1) & 0xFF

            if key == ord("q"):
                print("Kullanici tarafindan durduruldu.")
                break

        self.stop()

    def stop(self):

        self.camera.release()

        if self.video_writer is not None:
            self.video_writer.release()

        cv2.destroyAllWindows()

        print("Sistem kapatildi.")
        self.logger.system_stopped()