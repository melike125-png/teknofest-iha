import time

from config import DROP_SERVO_PIN

try:
    from gpiozero import Servo
    GPIO_AVAILABLE = True
except:
    GPIO_AVAILABLE = False


class PayloadSystem:

    def __init__(self):

        self.gpio_active = GPIO_AVAILABLE

        if self.gpio_active:
            self.drop_servo = Servo(DROP_SERVO_PIN)
            print("Tek servo yuk birakma sistemi hazir.")
        else:
            print("GPIO aktif degil.")
            print("Servo test modu acildi.")

    def trigger_servo(self):

        self.drop_servo.max()
        time.sleep(0.7)

        self.drop_servo.min()
        time.sleep(0.7)

    def drop_payload(self, payload_color):

        print("=" * 40)
        print(f"{payload_color} yuk birakiliyor...")
        print("=" * 40)

        if not self.gpio_active:
            print("TEST MODU -> Servo fiziksel olarak calismiyor.")
            return

        self.trigger_servo()

        print("Yuk birakma tamamlandi.")