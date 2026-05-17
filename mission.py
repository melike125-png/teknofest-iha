# mission.py

import cv2
import time

from config import (
    MISSION_SEQUENCE,
    CENTER_TOLERANCE,
    STABLE_LIMIT,
    VIDEO_OUTPUT_NAME
)

from camera import CameraSystem
from detector import DetectorSystem
from payload import PayloadSystem
from targeting import TargetingSystem
from ui import UISystem


class MissionSystem:

    def __init__(self):

        self.camera = CameraSystem()
        self.detector = DetectorSystem()
        self.payload = PayloadSystem()
        self.targeting = TargetingSystem()
        self.ui = UISystem()

        self.current_target_index = 0
        self.stable_count = 0
        self.prev_time = 0

        self.video_writer = None

    def get_current_target(self):

        if self.current_target_index < len(MISSION_SEQUENCE):
            return MISSION_SEQUENCE[self.current_target_index]

        return None

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

    def start(self):

        if not self.camera.is_opened():
            print("Kamera acilamadi.")
            return

        self.start_video_recording()

        print("Gorev basladi.")

        while True:

            frame = self.camera.read_frame()

            if frame is None:
                print("Goruntu alinamadi.")
                break

            fps = self.calculate_fps()

            current_target = self.get_current_target()

            detections = self.detector.detect(frame)

            target_data = self.targeting.find_best_target(
                detections,
                current_target,
                frame
            )

            status = "HEDEF YOK"
            direction = "ARAMA MODU"

            if current_target is None:

                status = "GOREV TAMAMLANDI"
                direction = "TUM YUKLER BIRAKILDI"

            elif target_data is not None:

                is_centered = target_data["is_centered"]

                if is_centered:
                    self.stable_count += 1
                    status = f"HEDEF ORTADA - {self.stable_count}/{STABLE_LIMIT}"
                    direction = "MERKEZDE"

                    if self.stable_count >= STABLE_LIMIT:
                        status = "YUK BIRAKILDI"

                        self.payload.drop_payload(current_target)

                        self.current_target_index += 1
                        self.stable_count = 0

                        time.sleep(1)

                else:
                    self.stable_count = 0
                    status = "HEDEF VAR - ORTALA"
                    direction = target_data["direction"]

            else:
                self.stable_count = 0

            self.ui.draw(
                frame=frame,
                target_data=target_data,
                current_target=current_target,
                status=status,
                direction=direction,
                fps=fps
            )

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