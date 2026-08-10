import math
import time

from config import (
    DROP_ALTITUDE,
    INFINITY8_POINT_COUNT,
    INFINITY8_RADIUS,
    MAVLINK_BAUD,
    MAVLINK_COMMANDS_ENABLED,
    MAVLINK_CONNECTION_MODE,
    MAVLINK_CONNECTIONS,
    MISSION_ALTITUDE,
)

try:
    from cube_mavlink import CubeMavlink
except Exception:
    CubeMavlink = None


class FlightController:

    def __init__(self, use_real_cube=True):
        self.use_real_cube = use_real_cube
        self.connected = False
        self.cube = None
        self.last_status = None

        # config.py icinde False oldugu surece
        # hicbir ucus komutu gonderilemez.
        self.command_enabled = bool(
            MAVLINK_COMMANDS_ENABLED
        )

        self.point_counter = 0

    def connect(self):
        print("=" * 50)
        print("FLIGHT CONTROLLER BASLATILIYOR")
        print("=" * 50)

        if not self.use_real_cube:
            print(
                "TEST MODU -> MAVLink telemetri "
                "baglantisi kullanilmiyor."
            )
            self.connected = False
            return False

        if CubeMavlink is None:
            print(
                "HATA -> cube_mavlink.py bulunamadi "
                "veya yuklenemedi."
            )
            self.connected = False
            return False

        try:
            connection_port = MAVLINK_CONNECTIONS[
                MAVLINK_CONNECTION_MODE
            ]

            print(
                f"MAVLink modu: {MAVLINK_CONNECTION_MODE}"
            )
            print(
                f"MAVLink baglantisi: {connection_port}"
            )

            self.cube = CubeMavlink(
                port=connection_port,
                baud=MAVLINK_BAUD,
            )

            self.cube.connect()

            self.connected = True
            self.last_status = self.cube.get_full_status()

            print("MAVLink baglantisi: OK")
            self.print_status()

            print("=" * 50)

            if self.command_enabled:
                print(
                    "UYARI -> UCUS KOMUTLARI ETKIN"
                )
            else:
                print("GUVENLI MOD AKTIF")
                print(
                    "Arm, takeoff, hareket ve land "
                    "komutlari gonderilmeyecek."
                )

            print("=" * 50)

            return True

        except KeyError:
            print(
                "MAVLink baglantisi basarisiz: "
                f"Gecersiz mod: {MAVLINK_CONNECTION_MODE}"
            )
            self.connected = False
            self.cube = None
            return False

        except Exception as error:
            print(
                "MAVLink baglantisi basarisiz:",
                error,
            )
            self.connected = False
            self.cube = None
            return False

    def get_status(self):
        if not self.connected or self.cube is None:
            return {
                "connected": False,
                "message": "MAVLink baglantisi yok",
            }

        try:
            self.last_status = self.cube.get_full_status()
            return self.last_status

        except Exception as error:
            return {
                "connected": False,
                "message": str(error),
            }

    def print_status(self):
        status = self.get_status()

        print("-" * 50)
        print("MAVLINK DURUMU")
        print("-" * 50)

        if not status or status.get("connected") is False:
            print("Durum okunamadi:", status)
            return

        system = status.get("system", {})
        mode = status.get("mode", {})
        attitude = status.get("attitude", {})
        gps = status.get("gps", {})
        battery = status.get("battery", {})

        print("System ID:", system.get("system_id"))
        print(
            "Component ID:",
            system.get("component_id"),
        )
        print("Mode:", mode.get("mode"))
        print("Armed:", mode.get("armed"))
        print("Roll:", attitude.get("roll"))
        print("Pitch:", attitude.get("pitch"))
        print("Yaw:", attitude.get("yaw"))
        print("GPS Fix:", gps.get("fix_type"))
        print(
            "Satellite:",
            gps.get("satellites"),
        )
        print(
            "Battery Voltage:",
            battery.get("voltage"),
        )
        print("-" * 50)

    def is_safe_to_send_command(self):
        return (
            self.connected
            and self.command_enabled
        )

    def takeoff(self, altitude=MISSION_ALTITUDE):
        if not self.is_safe_to_send_command():
            print(
                "GUVENLI MOD -> Takeoff komutu "
                f"engellendi. Hedef irtifa: {altitude} m"
            )
            return False

        # Gercek ucus komutu henuz uygulanmadi.
        return False

    def move_to_point(
        self,
        x,
        y,
        altitude=MISSION_ALTITUDE,
    ):
        self.point_counter += 1

        if self.point_counter % 20 == 0:
            print(
                "GUVENLI MOD -> Nokta hazirlandi | "
                f"x: {round(x, 2)} "
                f"y: {round(y, 2)} "
                f"alt: {altitude}"
            )

        if not self.is_safe_to_send_command():
            return False

        # Gercek hareket komutu henuz uygulanmadi.
        return False

    def search_forward(self):
        if not self.is_safe_to_send_command():
            print(
                "GUVENLI MOD -> Ileri tarama "
                "komutu engellendi."
            )
            return False

        return False

    def yaw_scan(self, angle):
        if not self.is_safe_to_send_command():
            print(
                "GUVENLI MOD -> Yaw tarama komutu "
                f"engellendi. Aci: {angle}"
            )
            return False

        return False

    def approach_target(self, error_x, error_y):
        if not self.is_safe_to_send_command():
            print(
                "GUVENLI MOD -> Hedefe yaklasma "
                "komutu engellendi. "
                f"X hata: {error_x}, "
                f"Y hata: {error_y}"
            )
            return False

        return False

    def descend(self, altitude=DROP_ALTITUDE):
        if not self.is_safe_to_send_command():
            print(
                "GUVENLI MOD -> Alcalma komutu "
                f"engellendi. Hedef irtifa: {altitude} m"
            )
            return False

        return False

    def ascend(self, altitude=MISSION_ALTITUDE):
        if not self.is_safe_to_send_command():
            print(
                "GUVENLI MOD -> Yukselme komutu "
                f"engellendi. Hedef irtifa: {altitude} m"
            )
            return False

        return False

    def hover(self):
        if not self.is_safe_to_send_command():
            print(
                "GUVENLI MOD -> Hover komutu "
                "engellendi."
            )
            return False

        return False

    def land(self):
        if not self.is_safe_to_send_command():
            print(
                "GUVENLI MOD -> Inis komutu "
                "engellendi."
            )
            return False

        return False

    def perform_infinity8(self):
        print("=" * 50)
        print("1. GOREV TESTI -> 8 CIZME GOREVI")
        print("=" * 50)

        self.takeoff(MISSION_ALTITUDE)

        for index in range(INFINITY8_POINT_COUNT):
            angle = (
                2
                * math.pi
                * index
                / INFINITY8_POINT_COUNT
            )

            x = (
                INFINITY8_RADIUS
                * math.sin(angle)
            )

            y = (
                INFINITY8_RADIUS
                * math.sin(angle)
                * math.cos(angle)
            )

            self.move_to_point(
                x,
                y,
                MISSION_ALTITUDE,
            )

            time.sleep(0.03)

        self.hover()

        print("=" * 50)
        print(
            "1. GOREV TESTI TAMAMLANDI -> "
            "8 NOKTALARI HAZIRLANDI"
        )
        print("=" * 50)

    def close(self):
        if self.cube is not None:
            self.cube.close()

        self.connected = False
        self.cube = None
        self.last_status = None