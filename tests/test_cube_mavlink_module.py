from cube_mavlink import CubeMavlink


def print_section(title):
    print("------------------------")
    print(title)
    print("------------------------")


def main():
    cube = CubeMavlink(port="/dev/ttyACM0", baud=115200)

    print_section("CUBE MAVLINK MODULE TEST")

    try:
        cube.connect()
        print("Cube bağlantısı: OK")

        print_section("SYSTEM")
        system = cube.get_system_info()
        print(system)

        print_section("MODE / ARM")
        mode = cube.get_mode_and_arm_status()
        print(mode)

        print_section("ATTITUDE")
        attitude = cube.get_attitude()
        print(attitude)

        print_section("GPS")
        gps = cube.get_gps()
        print(gps)

        print_section("BATTERY")
        battery = cube.get_battery()
        print(battery)

        print_section("FULL STATUS")
        status = cube.get_full_status()
        print(status)

        print_section("TEST TAMAMLANDI")

    except Exception as e:
        print("HATA:", e)

    finally:
        cube.close()


if __name__ == "__main__":
    main()