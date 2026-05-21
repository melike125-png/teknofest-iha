# camera.py

from picamera2 import Picamera2
import cv2

from config import FRAME_WIDTH, FRAME_HEIGHT


class CameraSystem:

    def __init__(self):

        self.picam2 = Picamera2()

        config = self.picam2.create_preview_configuration(
            main={
                "size": (FRAME_WIDTH, FRAME_HEIGHT),
                "format": "RGB888"
            }
        )

        self.picam2.configure(config)

        self.picam2.start()

        self.opened = True

        print("CSI kamera baslatildi.")

    def is_opened(self):
        return self.opened

    def read_frame(self):

        frame = self.picam2.capture_array()

        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

        return frame

    def release(self):

        self.picam2.stop()

    def get_width(self):
        return FRAME_WIDTH

    def get_height(self):
        return FRAME_HEIGHT