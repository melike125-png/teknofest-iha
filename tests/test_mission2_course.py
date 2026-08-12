from mission2_course import (
    CourseState,
    Mission2CourseGate,
    REQUIRED_DROP_CHECKS,
)
from mission2_rules import (
    PAYLOAD_BLUE,
    PAYLOAD_RED,
    TARGET_BLUE_HEXAGON,
    TARGET_RED_TRIANGLE,
)


def valid_safety_checks() -> dict[str, bool]:
    return {
        check_name: True
        for check_name in REQUIRED_DROP_CHECKS
    }


def assert_runtime_error(
    action,
    expected_message: str,
) -> None:
    try:
        action()

    except RuntimeError as error:
        message = str(error)

        assert expected_message in message, (
            f"Beklenen hata bulunamadı.\n"
            f"Beklenen: {expected_message}\n"
            f"Gerçek: {message}"
        )

        return

    raise AssertionError(
        "RuntimeError bekleniyordu fakat oluşmadı."
    )


def prepare_search_state() -> Mission2CourseGate:
    gate = Mission2CourseGate()

    gate.start_mission()

    confirmed = gate.confirm_pole_2_passage(
        outside_confirmed=True
    )

    assert confirmed is True
    assert gate.state == CourseState.SEARCH_ACTIVE

    return gate


def complete_target(
    gate: Mission2CourseGate,
    target_name: str,
    payload_name: str,
) -> None:
    locked = gate.lock_target(target_name)

    assert locked is True

    authorized = gate.authorize_payload_release(
        target_name=target_name,
        payload_name=payload_name,
        safety_checks=valid_safety_checks(),
    )

    assert authorized is True
    assert gate.payload_release_authorized is True

    gate.record_payload_release(
        target_name=target_name,
        payload_name=payload_name,
    )


def test_initial_state_is_safe() -> None:
    gate = Mission2CourseGate()

    assert gate.state == CourseState.PRE_FLIGHT
    assert gate.camera_search_authorized is False
    assert gate.payload_release_authorized is False


def test_search_blocked_before_pole_2() -> None:
    gate = Mission2CourseGate()

    gate.start_mission()

    assert (
        gate.state
        == CourseState.TRANSIT_TO_POLE_2
    )

    assert gate.camera_search_authorized is False

    locked = gate.lock_target(
        TARGET_BLUE_HEXAGON
    )

    assert locked is False


def test_inside_pole_passage_rejected() -> None:
    gate = Mission2CourseGate()

    gate.start_mission()

    confirmed = gate.confirm_pole_2_passage(
        outside_confirmed=False
    )

    assert confirmed is False

    assert (
        gate.state
        == CourseState.TRANSIT_TO_POLE_2
    )

    assert gate.camera_search_authorized is False


def test_outside_pole_passage_opens_search() -> None:
    gate = prepare_search_state()

    assert gate.pole_2_outside_confirmed is True
    assert gate.camera_search_authorized is True


def test_unknown_target_rejected() -> None:
    gate = prepare_search_state()

    locked = gate.lock_target("mavi_kare")

    assert locked is False
    assert gate.active_target is None
    assert gate.state == CourseState.SEARCH_ACTIVE


def test_wrong_payload_rejected() -> None:
    gate = prepare_search_state()

    assert gate.lock_target(
        TARGET_BLUE_HEXAGON
    )

    authorized = gate.authorize_payload_release(
        target_name=TARGET_BLUE_HEXAGON,
        payload_name=PAYLOAD_BLUE,
        safety_checks=valid_safety_checks(),
    )

    assert authorized is False
    assert gate.payload_release_authorized is False
    assert gate.state == CourseState.TARGET_LOCKED


def test_each_safety_check_is_required() -> None:
    for failed_check in REQUIRED_DROP_CHECKS:
        gate = prepare_search_state()

        assert gate.lock_target(
            TARGET_BLUE_HEXAGON
        )

        checks = valid_safety_checks()
        checks[failed_check] = False

        authorized = gate.authorize_payload_release(
            target_name=TARGET_BLUE_HEXAGON,
            payload_name=PAYLOAD_RED,
            safety_checks=checks,
        )

        assert authorized is False, (
            f"{failed_check} başarısızken "
            "yük bırakmaya izin verildi."
        )

        assert (
            gate.payload_release_authorized
            is False
        )


def test_first_payload_returns_to_search() -> None:
    gate = prepare_search_state()

    complete_target(
        gate,
        TARGET_BLUE_HEXAGON,
        PAYLOAD_RED,
    )

    assert gate.state == CourseState.SEARCH_ACTIVE

    assert (
        TARGET_BLUE_HEXAGON
        in gate.completed_targets
    )

    assert PAYLOAD_RED in gate.released_payloads

    assert gate.active_target is None


def test_completed_target_cannot_lock_again() -> None:
    gate = prepare_search_state()

    complete_target(
        gate,
        TARGET_BLUE_HEXAGON,
        PAYLOAD_RED,
    )

    locked_again = gate.lock_target(
        TARGET_BLUE_HEXAGON
    )

    assert locked_again is False


def test_two_payloads_open_exit_route() -> None:
    gate = prepare_search_state()

    complete_target(
        gate,
        TARGET_BLUE_HEXAGON,
        PAYLOAD_RED,
    )

    complete_target(
        gate,
        TARGET_RED_TRIANGLE,
        PAYLOAD_BLUE,
    )

    assert gate.state == CourseState.EXIT_ROUTE
    assert len(gate.released_payloads) == 2
    assert len(gate.completed_targets) == 2
    assert gate.camera_search_authorized is False


def test_finish_blocked_before_two_payloads() -> None:
    gate = prepare_search_state()

    complete_target(
        gate,
        TARGET_BLUE_HEXAGON,
        PAYLOAD_RED,
    )

    assert_runtime_error(
        gate.confirm_finish_line_crossed,
        "İki yük tamamlanmadan",
    )


def test_complete_mission_flow() -> None:
    gate = prepare_search_state()

    complete_target(
        gate,
        TARGET_RED_TRIANGLE,
        PAYLOAD_BLUE,
    )

    complete_target(
        gate,
        TARGET_BLUE_HEXAGON,
        PAYLOAD_RED,
    )

    gate.confirm_finish_line_crossed()

    assert (
        gate.state
        == CourseState.FINISH_LINE_CROSSED
    )

    gate.start_landing()

    assert gate.state == CourseState.LANDING

    gate.confirm_landed()

    assert gate.state == CourseState.COMPLETE


def test_abort_blocks_future_actions() -> None:
    gate = Mission2CourseGate()

    gate.abort("Telemetri bağlantısı kesildi.")

    assert gate.state == CourseState.ABORT
    assert gate.mission_aborted is True
    assert gate.camera_search_authorized is False
    assert gate.payload_release_authorized is False

    assert_runtime_error(
        gate.start_mission,
        "ABORT",
    )


def main() -> None:
    test_initial_state_is_safe()
    test_search_blocked_before_pole_2()
    test_inside_pole_passage_rejected()
    test_outside_pole_passage_opens_search()
    test_unknown_target_rejected()
    test_wrong_payload_rejected()
    test_each_safety_check_is_required()
    test_first_payload_returns_to_search()
    test_completed_target_cannot_lock_again()
    test_two_payloads_open_exit_route()
    test_finish_blocked_before_two_payloads()
    test_complete_mission_flow()
    test_abort_blocks_future_actions()

    print(
        "GOREV 2 GUVENLIK DURUM MAKINESI "
        "TESTLERI BASARILI"
    )


if __name__ == "__main__":
    main()