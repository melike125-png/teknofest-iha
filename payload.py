# payload.py

import time

from config import (
    SERVO_TRIANGLE_PIN,
    SERVO_HEXAGON_PIN
)

try:
    from gpiozero import Servo
    GPIO_AVAILABLE = True

except:
    GPIO_AVAILABLE = False


class PayloadSystem:

    def __init__(self):

        self.gpio_active = GPIO_AVAILABLE

        if self.gpio_active:

            self.triangle_servo = Servo(SERVO_TRIANGLE_PIN)
            self.hexagon_servo = Servo(SERVO_HEXAGON_PIN)

            print("Servo sistemi hazir.")

        else:
            print("GPIO aktif degil.")
            print("Servo test modu acildi.")

    def trigger_servo(self, servo):

        servo.max()

        time.sleep(0.7)

        servo.min()

        time.sleep(0.7)

    def drop_payload(self, target_name):

        print("=" * 40)
        print(f"{target_name} icin yuk birakiliyor...")
        print("=" * 40)

        if not self.gpio_active:

            print("TEST MODU -> Servo fiziksel olarak calismiyor.")
            return

        if target_name == "kirmizi_ucgen":

            self.trigger_servo(self.triangle_servo)

        elif target_name == "mavi_altigen":

            self.trigger_servo(self.hexagon_servo)

        print("Yuk birakma tamamlandi.")