# servo_test.py

from gpiozero import Servo
import time

servo = Servo(17)

print("Servo test basliyor...")

while True:
    print("Servo sola gidiyor")
    servo.min()
    time.sleep(1)

    print("Servo ortaya gidiyor")
    servo.mid()
    time.sleep(1)

    print("Servo saga gidiyor")
    servo.max()
    time.sleep(1)