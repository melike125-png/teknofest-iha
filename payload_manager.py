# payload_manager.py

from gpiozero import AngularServo
from time import sleep

from config import (
    SERVO_1_PIN,
    SERVO_2_PIN,
    SERVO_CLOSED_ANGLE,
    SERVO_OPEN_ANGLE
)


class PayloadManager:

    def __init__(self):

        self.servo1 = AngularServo(
            SERVO_1_PIN,
            min_angle=0,
            max_angle=180
        )

        self.servo2 = AngularServo(
            SERVO_2_PIN,
            min_angle=0,
            max_angle=180
        )

        self.close_all()

    def close_all(self):

        self.servo1.angle = SERVO_CLOSED_ANGLE
        self.servo2.angle = SERVO_CLOSED_ANGLE

    def drop_red_payload(self):

        print("KIRMIZI YUK BIRAKILIYOR")

        self.servo1.angle = SERVO_OPEN_ANGLE

        sleep(1)

        self.servo1.angle = SERVO_CLOSED_ANGLE

    def drop_blue_payload(self):

        print("MAVI YUK BIRAKILIYOR")

        self.servo2.angle = SERVO_OPEN_ANGLE

        sleep(1)

        self.servo2.angle = SERVO_CLOSED_ANGLE