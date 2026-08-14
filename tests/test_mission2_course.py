from mission2_course import CourseState, Mission2CourseGate


def main():
    gate = Mission2CourseGate()
    assert gate.state == CourseState.PRE_FLIGHT
    assert gate.camera_search_authorized is False
    assert gate.payload_release_authorized is False

    gate.start_mission()
    assert gate.state == CourseState.TRANSIT_TO_POLE_2
    assert gate.confirm_pole_2_passage(False) is False
    assert gate.camera_search_authorized is False

    try:
        gate.record_payload_release("kirmizi_yuk")
    except RuntimeError:
        pass
    else:
        raise AssertionError("Direk 2 oncesi yuk birakma engellenmeliydi.")

    assert gate.confirm_pole_2_passage(True) is True
    assert gate.camera_search_authorized is True
    assert gate.payload_release_authorized is True

    gate.record_payload_release("kirmizi_yuk")
    assert gate.state == CourseState.SEARCH_ACTIVE

    try:
        gate.record_payload_release("kirmizi_yuk")
    except RuntimeError:
        pass
    else:
        raise AssertionError("Ayni yuk ikinci kez birakilamamaliydi.")

    gate.record_payload_release("mavi_yuk")
    assert gate.state == CourseState.EXIT_ROUTE
    assert gate.camera_search_authorized is False

    gate.confirm_finish_line_crossed()
    gate.confirm_landed()
    assert gate.state == CourseState.COMPLETE

    aborted = Mission2CourseGate()
    aborted.abort("kamera baglantisi yok")
    assert aborted.state == CourseState.ABORT
    assert aborted.abort_reason == "kamera baglantisi yok"

    print("GOREV 2 SAHA GECIDI TESTLERI BASARILI")


if __name__ == "__main__":
    main()

