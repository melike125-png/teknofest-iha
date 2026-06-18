# flight_controller.py

import math
import time

from config import (
    MISSION_ALTITUDE,
    DROP_ALTITUDE,
    INFINITY8_RADIUS,
    INFINITY8_POINT_COUNT
)


class FlightController:

    def __init__(self):

        # Simdilik gercek Pixhawk / Cube Orange baglantisi yok.
        # Bu yuzden test modunda sadece terminal mesajlariyla calisiyor.
        self.connected = False

    def connect(self):

        print("Pixhawk / Cube Orange baglantisi simdilik TEST MODUNDA.")
        self.connected = False

    def takeoff(self, altitude=MISSION_ALTITUDE):

        print(f"TEST MODU -> Drone {altitude} metreye kalkis yapar.")

    def move_to_point(self, x, y, altitude=MISSION_ALTITUDE):

        # 8 cizme gorevi sirasinda cok fazla nokta olustugu icin
        # artik her noktayi terminale yazdirmiyoruz.
        # Fonksiyon bos kalmasin diye pass yaziyoruz.
        pass

    def search_forward(self):

        print("TEST MODU -> Ileri tarama hareketi yapilir.")

    def yaw_scan(self, angle):

        print(f"TEST MODU -> Yaw tarama: {angle} derece")

    def approach_target(self, error_x, error_y):

        print(f"TEST MODU -> Hedefe yaklas | X hata: {error_x}, Y hata: {error_y}")

    def descend(self, altitude=DROP_ALTITUDE):

        print(f"TEST MODU -> Drone {altitude} metreye alcalir.")

    def ascend(self, altitude=MISSION_ALTITUDE):

        print(f"TEST MODU -> Drone tekrar {altitude} metreye yukselir.")

    def hover(self):

        print("TEST MODU -> Drone havada sabit bekler.")

    def land(self):

        print("TEST MODU -> Drone inis yapar.")

    def perform_infinity8(self):

        print("=" * 50)
        print("1. GOREV BASLADI -> 8 CIZME GOREVI")
        print("=" * 50)

        self.takeoff(MISSION_ALTITUDE)

        # Sonsuz isareti / 8 sekli icin parametrik denklem:
        # x = r * sin(t)
        # y = r * sin(t) * cos(t)
        for i in range(INFINITY8_POINT_COUNT):

            t = 2 * math.pi * i / INFINITY8_POINT_COUNT

            x = INFINITY8_RADIUS * math.sin(t)
            y = INFINITY8_RADIUS * math.sin(t) * math.cos(t)

            self.move_to_point(x, y, MISSION_ALTITUDE)

            time.sleep(0.03)

        self.hover()

        print("=" * 50)
        print("1. GOREV TAMAMLANDI -> 8 CIZME BITTI")
        print("=" * 50)