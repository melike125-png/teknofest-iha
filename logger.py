# logger.py



import os

from datetime import datetime





class LoggerSystem:



    def __init__(self, log_file="mission_log.txt"):



        self.log_file = log_file



        self._ensure_log_file()

        self.write_log("LOGGER SISTEMI BASLATILDI")



    def get_time(self):



        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")



    def _ensure_log_file(self):



        try:

            log_dir = os.path.dirname(os.path.abspath(self.log_file))



            if log_dir:

                os.makedirs(log_dir, exist_ok=True)



            if not os.path.exists(self.log_file):

                with open(self.log_file, "a", encoding="utf-8"):

                    pass



        except OSError:

            pass



    def write_log(self, message):



        safe_message = str(message)

        current_time = self.get_time()

        log_message = f"[{current_time}] {safe_message}"



        print(log_message)



        try:

            with open(self.log_file, "a", encoding="utf-8") as file:

                file.write(log_message + "\n")

                file.flush()



        except OSError as error:

            print(f"[LOGGER UYARI] Dosyaya yazilamadi: {error}")



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


