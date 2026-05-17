# logger.py

from datetime import datetime


class LoggerSystem:

    def __init__(self, log_file="mission_log.txt"):

        self.log_file = log_file

        self.write_log("LOGGER SISTEMI BASLATILDI")

    def get_time(self):

        return datetime.now().strftime("%H:%M:%S")

    def write_log(self, message):

        current_time = self.get_time()

        log_message = f"[{current_time}] {message}"

        print(log_message)

        with open(self.log_file, "a", encoding="utf-8") as file:
            file.write(log_message + "\n")

    def system_started(self):

        self.write_log("SISTEM BASLATILDI")

    def model_loaded(self):

        self.write_log("YOLO MODELI YUKLENDI")

    def camera_opened(self):

        self.write_log("KAMERA ACILDI")

    def camera_failed(self):

        self.write_log("KAMERA ACILAMADI")

    def target_detected(self, target_name, confidence):

        self.write_log(
            f"HEDEF ALGILANDI -> {target_name} | GUVEN: {confidence:.2f}"
        )

    def target_lost(self):

        self.write_log("HEDEF KAYBEDILDI")

    def payload_dropped(self, target_name):

        self.write_log(
            f"YUK BIRAKILDI -> {target_name}"
        )

    def mission_completed(self):

        self.write_log("GOREV TAMAMLANDI")

    def fps_log(self, fps):

        self.write_log(f"FPS -> {fps:.1f}")

    def system_stopped(self):

        self.write_log("SISTEM KAPATILDI")