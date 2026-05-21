# mission.py

import cv2
import time

from config import STABLE_LIMIT, VIDEO_OUTPUT_NAME
from camera import CameraSystem
from detector import DetectorSystem
from payload import PayloadSystem
from targeting import TargetingSystem
from ui import UISystem
from logger import LoggerSystem
from failsafe import FailsafeSystem


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

        self.completed_targets = {
            "mavi_altigen": False,
            "kirmizi_ucgen": False
        }

        self.stable_count = 0
        self.prev_time = 0
        self.video_writer = None

    def all_targets_completed(self):
        return (
            self.completed_targets["mavi_altigen"]
            and self.completed_targets["kirmizi_ucgen"]
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

        cv2.imshow("TEKNOFEST IHA GOREV SISTEMI", frame)
        cv2.waitKey(2000)

    def start(self):
        if not self.camera.is_opened():
            print("Kamera acilamadi.")
            self.logger.camera_failed()
            self.stop()
            return

        self.logger.camera_opened()
        self.start_video_recording()

        print("Gorev basladi.")
        self.logger.write_log("GOREV BASLADI")

        while True:
            frame = self.camera.read_frame()

            if frame is None:
                print("Goruntu alinamadi.")
                self.logger.write_log("GORUNTU ALINAMADI")
                break

            self.failsafe.update_frame_time()

            fps = self.calculate_fps()

            failsafe_status = self.failsafe.get_status(fps)
            print(failsafe_status)

            detections = self.detector.detect(frame)

            target_data = self.targeting.find_best_target(
                detections=detections,
                completed_targets=self.completed_targets,
                frame=frame
            )

            status = "HEDEF YOK"
            direction = "ARAMA MODU"
            current_target = None

            if self.all_targets_completed():
                self.finish_mission(frame, target_data, fps)
                break

            elif target_data is not None:
                current_target = target_data["class_name"]

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
                        status = "YUK BIRAKILDI"

                        self.payload.drop_payload(current_target)
                        self.logger.payload_dropped(current_target)

                        self.completed_targets[current_target] = True

                        self.stable_count = 0
                        time.sleep(1)

                else:
                    self.stable_count = 0
                    status = "HEDEF VAR - ORTALA"
                    direction = target_data["direction"]

            else:
                self.stable_count = 0
                self.logger.target_lost()

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

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

        self.stop()

    def stop(self):
        self.camera.release()

        if self.video_writer is not None:
            self.video_writer.release()

        cv2.destroyAllWindows()

        print("Sistem kapatildi.")
        self.logger.system_stopped()