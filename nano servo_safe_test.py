from gpiozero import AngularServo
from time import sleep

servo = AngularServo(17, min_angle=0, max_angle=180)

try:
    print("Servo ortaya gidiyor")
    servo.angle = 90
    sleep(1)

    print("Servo aciliyor")
    servo.angle = 110
    sleep(1)

    print("Servo tekrar ortaya donuyor")
    servo.angle = 90
    sleep(1)

finally:
    print("Servo serbest birakiliyor")
    servo.detach()