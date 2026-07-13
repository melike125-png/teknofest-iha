from flight_controller import FlightController


def test_flight_controller():

    flight = FlightController()

    test_directions = [
        "AZ SAGDA",
        "ORTA SOLDA",
        "COK YUKARIDA",
        "AZ ASAGIDA",
        "AZ SAGDA ORTA YUKARIDA",
        ""
    ]

    for direction in test_directions:
        print("\nTest edilen yon:", direction)
        flight.move_by_direction(direction)

    flight.stop()
    flight.failsafe_hold()
    flight.land()


if __name__ == "__main__":
    test_flight_controller()