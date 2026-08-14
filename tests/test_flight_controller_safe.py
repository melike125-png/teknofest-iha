from flight_controller import FlightController


def main():
    fc = FlightController(use_real_cube=True)

    connected = fc.connect()

    print("Connect result:", connected)

    fc.print_status()

    fc.perform_infinity8()

    fc.search_forward()
    fc.yaw_scan(30)
    fc.approach_target(error_x=45, error_y=-20)
    fc.descend()
    fc.ascend()
    fc.hover()
    fc.land()

    fc.close()

    print("FlightController guvenli test tamamlandi")


if __name__ == "__main__":
    main()