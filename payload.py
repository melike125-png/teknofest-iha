# payload.py

import time

from config import (
    SERVO_RED_PAYLOAD_PIN,
    SERVO_BLUE_PAYLOAD_PIN,
    SERVO_CLOSED_ANGLE,
    SERVO_OPEN_ANGLE,
    TARGET_BLUE_HEXAGON,
    TARGET_RED_TRIANGLE
)

try:
    from gpiozero import AngularServo

    GPIO_AVAILABLE = True

except:
    GPIO_AVAILABLE = False


class PayloadSystem:

    def __init__(self):

        self.gpio_active = GPIO_AVAILABLE

        if self.gpio_active:

            self.red_payload_servo = AngularServo(
                SERVO_RED_PAYLOAD_PIN,
                min_angle=0,
                max_angle=180
            )

            self.blue_payload_servo = AngularServo(
                SERVO_BLUE_PAYLOAD_PIN,
                min_angle=0,
                max_angle=180
            )

            self.close_all_servos()

            print("Servo sistemi hazir.")

        else:

            print("GPIO aktif degil.")
            print("Servo test modu aktif.")

    def close_all_servos(self):

        if not self.gpio_active:
            return

        self.red_payload_servo.angle = SERVO_CLOSED_ANGLE
        self.blue_payload_servo.angle = SERVO_CLOSED_ANGLE

    def open_servo(self, servo):

        servo.angle = SERVO_OPEN_ANGLE

    def close_servo(self, servo):

        servo.angle = SERVO_CLOSED_ANGLE

    def drop_red_payload(self):

        print("KIRMIZI YUK BIRAKILIYOR")

        if not self.gpio_active:
            print("TEST MODU")
            return

        self.open_servo(self.red_payload_servo)

        time.sleep(1)

        self.close_servo(self.red_payload_servo)

    def drop_blue_payload(self):

        print("MAVI YUK BIRAKILIYOR")

        if not self.gpio_active:
            print("TEST MODU")
            return

        self.open_servo(self.blue_payload_servo)

        time.sleep(1)

        self.close_servo(self.blue_payload_servo)

    def drop_payload(self, target_name):

        print("=" * 40)
        print(f"HEDEF ALGILANDI -> {target_name}")
        print("=" * 40)

        if target_name == TARGET_BLUE_HEXAGON:

            print("MAVI ALTIGEN GORULDU")
            print("KIRMIZI YUK BIRAKILACAK")

            self.drop_red_payload()

        elif target_name == TARGET_RED_TRIANGLE:

            print("KIRMIZI UCGEN GORULDU")
            print("MAVI YUK BIRAKILACAK")

            self.drop_blue_payload()