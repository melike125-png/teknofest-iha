# payload.py

import time

from config import (
    SERVO_1_PIN,
    SERVO_2_PIN,
    SERVO_CLOSED_ANGLE,
    SERVO_OPEN_ANGLE,
    SERVO_RELEASE_WAIT,
    TARGET_BLUE_HEXAGON,
    TARGET_RED_TRIANGLE
)

try:
    from gpiozero import AngularServo
    GPIO_AVAILABLE = True

except Exception:
    GPIO_AVAILABLE = False


class PayloadSystem:

    def __init__(self):

        # Bu degisken, kodun Raspberry Pi uzerinde mi yoksa bilgisayarda test modunda mi
        # calistigini anlamak icin kullanilir.
        self.gpio_active = GPIO_AVAILABLE

        # Bu iki degisken ayni yuklerin iki kere birakilmasini engeller.
        self.red_payload_released = False
        self.blue_payload_released = False

        if self.gpio_active:

            # Servo 1 kirmizi yuku tutuyor.
            self.servo1_red_payload = AngularServo(
                SERVO_1_PIN,
                min_angle=0,
                max_angle=180
            )

            # Servo 2 mavi yuku tutuyor.
            self.servo2_blue_payload = AngularServo(
                SERVO_2_PIN,
                min_angle=0,
                max_angle=180
            )

            self.close_all_servos()

            print("Servo sistemi hazir.")

        else:

            # Bilgisayarda calisirken Raspberry Pi GPIO olmadigi icin
            # servo fiziksel olarak hareket etmez.
            print("GPIO aktif degil.")
            print("Payload sistemi TEST MODU ile calisiyor.")

    def close_all_servos(self):

        if not self.gpio_active:
            print("TEST MODU -> Tum servolar kapali konuma alindi.")
            return

        self.servo1_red_payload.angle = SERVO_CLOSED_ANGLE
        self.servo2_blue_payload.angle = SERVO_CLOSED_ANGLE

        print("Tum servolar kapali konuma alindi.")

    def open_servo(self, servo):

        servo.angle = SERVO_OPEN_ANGLE

    def close_servo(self, servo):

        servo.angle = SERVO_CLOSED_ANGLE

    def drop_red_payload(self):

        # Kirmizi yuk daha once birakildiysa tekrar birakma.
        if self.red_payload_released:
            print("Kirmizi yuk zaten daha once birakildi.")
            return

        print("=" * 40)
        print("KIRMIZI YUK BIRAKILIYOR")
        print("Servo 1 aciliyor.")
        print("=" * 40)

        if not self.gpio_active:
            print("TEST MODU -> Servo 1 120 dereceye giderdi.")
            self.red_payload_released = True
            return

        self.open_servo(self.servo1_red_payload)

        time.sleep(SERVO_RELEASE_WAIT)

        self.close_servo(self.servo1_red_payload)

        self.red_payload_released = True

        print("Kirmizi yuk birakildi.")

    def drop_blue_payload(self):

        # Mavi yuk daha once birakildiysa tekrar birakma.
        if self.blue_payload_released:
            print("Mavi yuk zaten daha once birakildi.")
            return

        print("=" * 40)
        print("MAVI YUK BIRAKILIYOR")
        print("Servo 2 aciliyor.")
        print("=" * 40)

        if not self.gpio_active:
            print("TEST MODU -> Servo 2 120 dereceye giderdi.")
            self.blue_payload_released = True
            return

        self.open_servo(self.servo2_blue_payload)

        time.sleep(SERVO_RELEASE_WAIT)

        self.close_servo(self.servo2_blue_payload)

        self.blue_payload_released = True

        print("Mavi yuk birakildi.")

    def drop_payload(self, target_name):

        print("=" * 40)
        print(f"HEDEF ALGILANDI -> {target_name}")
        print("=" * 40)

        # Mavi altigen gorulurse kirmizi yuk birakilacak.
        if target_name == TARGET_BLUE_HEXAGON:

            print("MAVI ALTIGEN GORULDU")
            print("KIRMIZI YUK BIRAKILACAK")
            self.drop_red_payload()

        # Kirmizi ucgen gorulurse mavi yuk birakilacak.
        elif target_name == TARGET_RED_TRIANGLE:

            print("KIRMIZI UCGEN GORULDU")
            print("MAVI YUK BIRAKILACAK")
            self.drop_blue_payload()

        else:

            print("Bilinmeyen hedef. Yuk birakilmadi.")