import json
import os
import time
from enum import Enum

import cv2

from config import (
    ALIGN_COMMAND_INTERVAL,
    CENTER_HOLD_SECONDS,
    CENTER_TOLERANCE_X,
    CENTER_TOLERANCE_Y,
    DROP_ALTITUDE,
    MODEL_PATH,
    MISSION_ALTITUDE,
    TARGET_CONFIRMATION_FRAMES,
    TARGET_BLUE_HEXAGON,
    TARGET_RED_TRIANGLE,
    VIDEO_OUTPUT_NAME,
)
from camera import CameraSystem
from detector import DetectorSystem
from failsafe import FailsafeSystem
from flight_controller import FlightController
from logger import LoggerSystem
from mission2_rules import Mission2Rules
from mission2_supervisor import Mission2Supervisor, Mission2Waypoints
from payload_controller import SimulatedPayloadController
from targeting import TargetingSystem


WINDOW_NAME = "TEKNOFEST IHA 2. GOREV SISTEMI"
DISPLAY_WIDTH = 1280
DISPLAY_HEIGHT = 720
MISSION2_COORDINATE_FILE = "mission2_coordinates.json"
MISSION2_ROUTE_FILE = "mission2_route.json"
MISSION_SAFE_MODE = True


class MissionPhase(str, Enum):
    WAIT_POLE_2 = "DIREK 2 BEKLENIYOR"
    AUTO_SEARCH = "AUTO TARAMA"
    TARGET_CONFIRM = "HEDEF DOGRULANIYOR"
    GUIDED_ALIGN = "GUIDED MERKEZLEME"
    STABILIZE = "MERKEZDE SABITLEME"
    DROP = "YUK BIRAKMA"
    ASCEND = "GOREV IRTIFASINA CIKIS"
    RESUME_AUTO = "AUTO ROTAYA DONUS"
    EXIT_ROUTE = "AUTO CIKIS ROTASI"
    ABORT = "GOREV DURDURULDU"


class Mission2UI:
    def draw(
        self,
        frame,
        target_data=None,
        current_target=None,
        status="",
        direction="",
        fps=0,
        stable_count=0,
        mission_state="",
        payload_status="",
    ):
        display_frame = frame.copy()
        height, width = display_frame.shape[:2]

        if target_data is not None:
            box = target_data.get("box")

            if box is not None and len(box) == 4:
                x1, y1, x2, y2 = [int(value) for value in box]

                cv2.rectangle(
                    display_frame,
                    (x1, y1),
                    (x2, y2),
                    (0, 255, 0),
                    3,
                )

                label = target_data.get("class_name", "hedef")
                confidence = float(
                    target_data.get("confidence", 0.0)
                )

                cv2.putText(
                    display_frame,
                    f"{label} {confidence:.2f}",
                    (x1, max(30, y1 - 10)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 0),
                    2,
                )

                target_center = target_data.get("target_center")

                if target_center is not None:
                    target_x, target_y = target_center
                    target_x = int(target_x)
                    target_y = int(target_y)

                    cv2.circle(
                        display_frame,
                        (target_x, target_y),
                        6,
                        (0, 255, 0),
                        -1,
                    )

                    cv2.line(
                        display_frame,
                        (width // 2, height // 2),
                        (target_x, target_y),
                        (0, 255, 0),
                        2,
                    )

        cv2.circle(
            display_frame,
            (width // 2, height // 2),
            7,
            (0, 255, 255),
            -1,
        )

        cv2.line(
            display_frame,
            (width // 2 - 25, height // 2),
            (width // 2 + 25, height // 2),
            (0, 255, 255),
            2,
        )

        cv2.line(
            display_frame,
            (width // 2, height // 2 - 25),
            (width // 2, height // 2 + 25),
            (0, 255, 255),
            2,
        )

        # Yarışma/VNC görünümü sade tutulur. Görev adımı, yön, FPS ve
        # yük olayları kamera görüntüsüne basılmaz; yalnızca terminale yazılır.
        return display_frame

        panel_height = 205
        overlay = display_frame.copy()

        cv2.rectangle(
            overlay,
            (0, 0),
            (width, panel_height),
            (0, 0, 0),
            -1,
        )

        display_frame = cv2.addWeighted(
            overlay,
            0.68,
            display_frame,
            0.32,
            0,
        )

        current_target_text = current_target or "YOK"

        lines = [
            f"2. GOREV | FPS: {fps:.1f}",
            f"AKTIF HEDEF: {current_target_text}",
            f"DURUM: {status}",
            f"YON: {direction}",
            f"GOREV ADIMI: {mission_state}",
            f"YUK DURUMU: {payload_status}",
            f"MERKEZ KARARLILIGI: {stable_count} KARE",
        ]

        y_position = 28

        for line in lines:
            cv2.putText(
                display_frame,
                line,
                (18, y_position),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.58,
                (255, 255, 255),
                2,
            )

            y_position += 27

        return display_frame


class Mission2Payload:
    """
    Guvenli ikinci gorev akisi.

    Sabit hedef sirasi yoktur.

    Ilk guvenilir sekilde dogrulanan hedef kilitlenir.
    Yuk islemi tamamlanana kadar hedef kilidi degismez.
    """

    def __init__(self):
        self.logger = LoggerSystem()
        self._safe_log("system_started")

        self.failsafe = FailsafeSystem()
        self.camera = CameraSystem()
        self.detector = DetectorSystem()

        self.payload = SimulatedPayloadController()

        print(
            "GUVENLI MOD -> Fiziksel yuk mekanizmasi devre disi, "
            "simulasyon kontrolu kullaniliyor."
        )

        self.targeting = TargetingSystem()

        self.rules = Mission2Rules(
            required_confirmations=TARGET_CONFIRMATION_FRAMES
        )

        self.completed_targets = self.rules.completed_targets

        self.ui = Mission2UI()

        self.flight_controller = FlightController(
            use_real_cube=not MISSION_SAFE_MODE
        )
        self.mission_supervisor = None

        self.start_point = None
        self.finish_point = None
        self.finish_point_reached = False

        self.stable_count = 0
        self.centered_since = None
        self.phase = MissionPhase.WAIT_POLE_2
        self.prev_time = 0.0
        self.video_writer = None

        self.last_target_log_time = 0.0
        self.last_lost_log_time = 0.0
        self.last_approach_log_time = 0.0

        self.TARGET_LOG_INTERVAL = 2.0
        self.LOST_LOG_INTERVAL = 1.0
        self.APPROACH_LOG_INTERVAL = ALIGN_COMMAND_INTERVAL

        self._fallback_confirmation_counts = {
            TARGET_BLUE_HEXAGON: 0,
            TARGET_RED_TRIANGLE: 0,
        }

        self._terminal_announced_target = None
        self._terminal_centered_target = None
        self._last_fps_print_time = 0.0

    @staticmethod
    def terminal_event(message):
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}", flush=True)

    def _safe_log(self, method_name, *args):
        try:
            method = getattr(
                self.logger,
                method_name,
                None,
            )

            if callable(method):
                method(*args)

        except Exception as error:
            print(
                f"LOG UYARISI -> {method_name}: {error}"
            )

    def read_float(self, text):
        while True:
            value = input(text).strip()
            value = value.replace(",", ".")

            try:
                return float(value)

            except ValueError:
                print("Gecersiz deger. Tekrar gir.")

    def collect_coordinates(self):
        print("=" * 50)
        print("2. GOREV BASLANGIC VE BITIS KOORDINATLARI")
        print("=" * 50)

        start_lat = self.read_float(
            "Baslangic latitude: "
        )

        start_lon = self.read_float(
            "Baslangic longitude: "
        )

        print("-" * 50)

        finish_lat = self.read_float(
            "Bitis latitude: "
        )

        finish_lon = self.read_float(
            "Bitis longitude: "
        )

        self.start_point = {
            "lat": start_lat,
            "lon": start_lon,
        }

        self.finish_point = {
            "lat": finish_lat,
            "lon": finish_lon,
        }

        self.save_coordinates()

    def save_coordinates(self):
        data = {
            "start_point": self.start_point,
            "finish_point": self.finish_point,
        }

        with open(
            MISSION2_COORDINATE_FILE,
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                data,
                file,
                indent=4,
            )

        print("2. gorev koordinatlari kaydedildi.")

    def load_coordinates(self):
        if not os.path.exists(
            MISSION2_COORDINATE_FILE
        ):
            return False

        try:
            with open(
                MISSION2_COORDINATE_FILE,
                "r",
                encoding="utf-8",
            ) as file:
                data = json.load(file)

        except (
            OSError,
            json.JSONDecodeError,
        ) as error:
            print(
                "Koordinat dosyasi okunamadi:",
                error,
            )

            return False

        self.start_point = data.get("start_point")
        self.finish_point = data.get("finish_point")

        return (
            self.start_point is not None
            and self.finish_point is not None
        )

    def prepare_coordinates(self):
        coordinates_loaded = self.load_coordinates()

        if coordinates_loaded:
            print(
                "Kayitli 2. gorev koordinatlari bulundu."
            )

            self.show_coordinates()

            use_saved = input(
                "Kayitli koordinatlar kullanilsin mi? E/H: "
            ).strip().lower()

            if use_saved != "e":
                self.collect_coordinates()

        else:
            print(
                "Kayitli 2. gorev koordinati bulunamadi."
            )

            self.collect_coordinates()

        self.show_coordinates()

    def show_coordinates(self):
        print("=" * 50)
        print("2. GOREV KOORDINAT OZETI")
        print("=" * 50)

        print(
            "Baslangic lat:",
            self.start_point.get("lat"),
        )

        print(
            "Baslangic lon:",
            self.start_point.get("lon"),
        )

        print("-" * 50)

        print(
            "Bitis lat:",
            self.finish_point.get("lat"),
        )

        print(
            "Bitis lon:",
            self.finish_point.get("lon"),
        )

        print("=" * 50)

    def prepare_mission_supervisor(self):
        """Load waypoint gates matching the mission uploaded by Mission Planner."""
        if not os.path.exists(MISSION2_ROUTE_FILE):
            print(
                "UYARI -> mission2_route.json bulunamadi. "
                "Gercek Gorev 2 baslatilamaz."
            )
            return False

        try:
            with open(MISSION2_ROUTE_FILE, "r", encoding="utf-8") as file:
                data = json.load(file)

            waypoints = Mission2Waypoints(
                pole_2_outside=int(data["pole_2_outside_waypoint"]),
                search_exit=int(data["search_exit_waypoint"]),
                finish_line_crossed=int(
                    data["finish_line_crossed_waypoint"]
                ),
            )
        except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
            print("Gorev 2 rota ayari gecersiz:", error)
            return False

        self.mission_supervisor = Mission2Supervisor(
            self.flight_controller,
            waypoints,
        )
        self.mission_supervisor.start()
        return True

    def get_expected_target(self):
        return getattr(
            self.rules,
            "active_target",
            None,
        )

    def all_targets_completed(self):
        method = getattr(
            self.rules,
            "all_targets_completed",
            None,
        )

        if callable(method):
            return bool(method())

        return bool(
            self.completed_targets.get(
                TARGET_BLUE_HEXAGON,
                False,
            )
            and self.completed_targets.get(
                TARGET_RED_TRIANGLE,
                False,
            )
        )

    def calculate_fps(self):
        current_time = time.time()

        if self.prev_time == 0:
            fps = 0.0

        else:
            elapsed = current_time - self.prev_time

            if elapsed > 0:
                fps = 1.0 / elapsed
            else:
                fps = 0.0

        self.prev_time = current_time

        return fps

    @staticmethod
    def can_print(last_time, interval):
        return time.time() - last_time >= interval

    @staticmethod
    def _normalize_selected_target(result):
        if isinstance(result, str):
            return result

        if isinstance(result, dict):
            return (
                result.get("target_name")
                or result.get("class_name")
                or result.get("active_target")
            )

        return None

    def _select_active_target(self, detections):
        active_target = self.get_expected_target()

        if active_target is not None:
            return active_target

        candidate_method_names = (
            "select_first_confirmed_target",
            "select_target",
            "process_detections",
            "update",
            "choose_target",
        )

        for method_name in candidate_method_names:
            method = getattr(
                self.rules,
                method_name,
                None,
            )

            if not callable(method):
                continue

            try:
                result = method(detections)

            except TypeError:
                continue

            selected_target = (
                self._normalize_selected_target(result)
            )

            if selected_target is None:
                selected_target = (
                    self.get_expected_target()
                )

            if selected_target in (
                TARGET_BLUE_HEXAGON,
                TARGET_RED_TRIANGLE,
            ):
                return selected_target

        return self._fallback_select_target(
            detections
        )

    def _fallback_select_target(self, detections):
        valid_by_name = {
            TARGET_BLUE_HEXAGON: [],
            TARGET_RED_TRIANGLE: [],
        }

        for detection in detections:
            class_name = detection.get("class_name")

            if class_name not in valid_by_name:
                continue

            if self.completed_targets.get(
                class_name,
                False,
            ):
                continue

            valid_by_name[class_name].append(
                detection
            )

        visible_targets = [
            target_name
            for (
                target_name,
                target_detections,
            ) in valid_by_name.items()
            if target_detections
        ]

        for target_name in (
            self._fallback_confirmation_counts
        ):
            if target_name in visible_targets:
                self._fallback_confirmation_counts[
                    target_name
                ] += 1

            else:
                self._fallback_confirmation_counts[
                    target_name
                ] = 0

        confirmed_targets = [
            target_name
            for target_name in visible_targets
            if self._fallback_confirmation_counts[
                target_name
            ] >= TARGET_CONFIRMATION_FRAMES
        ]

        selected_target = None

        if len(confirmed_targets) == 1:
            selected_target = confirmed_targets[0]

        elif len(confirmed_targets) == 2:
            center_x = getattr(
                self.targeting,
                "frame_center_x",
                320,
            )

            center_y = getattr(
                self.targeting,
                "frame_center_y",
                240,
            )

            center_distances = {}

            for target_name in confirmed_targets:
                detection = valid_by_name[
                    target_name
                ][0]

                box = detection.get("box")

                if box is None or len(box) != 4:
                    continue

                x1, y1, x2, y2 = [
                    int(value)
                    for value in box
                ]

                target_x = (x1 + x2) // 2
                target_y = (y1 + y2) // 2

                center_distances[target_name] = (
                    (
                        target_x - center_x
                    ) ** 2
                    + (
                        target_y - center_y
                    ) ** 2
                ) ** 0.5

            if len(center_distances) == 2:
                sorted_targets = sorted(
                    center_distances,
                    key=center_distances.get,
                )

                distance_difference = abs(
                    center_distances[
                        sorted_targets[0]
                    ]
                    - center_distances[
                        sorted_targets[1]
                    ]
                )

                if distance_difference >= 10.0:
                    selected_target = sorted_targets[0]

        if selected_target is not None:
            self.rules.active_target = (
                selected_target
            )

        return selected_target

    def _mark_target_completed(
        self,
        target_name,
    ):
        candidate_method_names = (
            "mark_target_completed",
            "complete_target",
            "set_target_completed",
        )

        for method_name in candidate_method_names:
            method = getattr(
                self.rules,
                method_name,
                None,
            )

            if callable(method):
                try:
                    method(target_name)
                    break

                except TypeError:
                    continue

        self.completed_targets[target_name] = True
        self.rules.active_target = None

        self._fallback_confirmation_counts[
            TARGET_BLUE_HEXAGON
        ] = 0

        self._fallback_confirmation_counts[
            TARGET_RED_TRIANGLE
        ] = 0

    @staticmethod
    def get_payload_name_for_target(
        target_name,
    ):
        if target_name == TARGET_BLUE_HEXAGON:
            return "KIRMIZI YUK"

        if target_name == TARGET_RED_TRIANGLE:
            return "MAVI YUK"

        return "BILINMEYEN YUK"

    def format_panel_direction(
        self,
        target_data,
    ):
        if target_data is None:
            return "HEDEF YOK"

        directions = []

        error_x = int(
            target_data.get("error_x", 0)
        )

        error_y = int(
            target_data.get("error_y", 0)
        )

        if error_x > CENTER_TOLERANCE_X:
            directions.append("SAG")

        elif error_x < -CENTER_TOLERANCE_X:
            directions.append("SOL")

        if error_y > CENTER_TOLERANCE_Y:
            directions.append("ASAGI")

        elif error_y < -CENTER_TOLERANCE_Y:
            directions.append("YUKARI")

        if directions:
            return " ".join(directions)

        return "MERKEZDE"

    def start_video_recording(self):
        width = self.camera.get_width()
        height = self.camera.get_height()

        fourcc = cv2.VideoWriter_fourcc(
            *"mp4v"
        )

        self.video_writer = cv2.VideoWriter(
            VIDEO_OUTPUT_NAME,
            fourcc,
            20.0,
            (width, height),
        )

        if not self.video_writer.isOpened():
            print(
                "UYARI -> Video kaydi baslatilamadi."
            )

            self.video_writer = None

    def release_payload_sequence(
        self,
        current_target,
    ):
        payload_name = (
            self.get_payload_name_for_target(
                current_target
            )
        )

        print("=" * 50)
        print("YUK BIRAKMA SEKANSI BASLADI")
        print("Hedef:", current_target)
        print("Yuk:", payload_name)
        print("=" * 50)

        self.terminal_event(
            f"YUK BIRAKMA BASLADI | hedef={current_target} | yuk={payload_name}"
        )

        self.flight_controller.hover()
        time.sleep(0.5)

        self.flight_controller.descend(
            DROP_ALTITUDE
        )

        time.sleep(1.0)

        if current_target == TARGET_BLUE_HEXAGON:
            self.payload.release_red_payload()

        elif current_target == TARGET_RED_TRIANGLE:
            self.payload.release_blue_payload()

        else:
            print(
                "Bilinmeyen hedef. Yuk birakilmadi."
            )

            return False

        self.terminal_event(
            f"{payload_name} BIRAKILDI (GUVENLI SIMULASYON) | "
            f"hedef={current_target}"
        )

        self.payload.center_remaining_payload()

        self._safe_log(
            "write_log",
            f"GUVENLI MOD -> {payload_name} simule edildi. "
            f"Hedef: {current_target}",
        )

        time.sleep(0.5)

        self.flight_controller.ascend(
            MISSION_ALTITUDE
        )

        time.sleep(0.5)

        self.flight_controller.hover()

        print("YUK BIRAKMA SEKANSI BITTI")

        return True

    def go_to_finish_point(self):
        if self.mission_supervisor is not None:
            print("=" * 50)
            print("IKI YUK TAMAMLANDI")
            print("MISSION PLANNER AUTO CIKIS ROTASI DEVAM EDIYOR")
            print("BITIS CIZGISINDEN SONRA LAND KOMUTU UYGULANACAK")
            print("=" * 50)
            return True

        if self.finish_point is None:
            print("Bitis noktasi yok.")
            return False

        print("=" * 50)
        print("BITIS NOKTASINA GIDIS")

        print(
            "Bitis lat:",
            self.finish_point.get("lat"),
        )

        print(
            "Bitis lon:",
            self.finish_point.get("lon"),
        )

        if MISSION_SAFE_MODE:
            print(
                "GUVENLI MOD -> Gercek ucus komutu "
                "gonderilmedi."
            )

        self.finish_point_reached = True

        print("=" * 50)

        return True

    def finish_mission(
        self,
        frame,
        target_data,
        fps,
    ):
        self.go_to_finish_point()
        self._safe_log("mission_completed")

        display_frame = self.ui.draw(
            frame=frame,
            target_data=target_data,
            current_target=None,
            status="GOREV TAMAMLANDI",
            direction="BITIS NOKTASI",
            fps=fps,
            stable_count=0,
            mission_state="GOREV TAMAMLANDI",
            payload_status="IKI YUK DE BIRAKILDI",
        )

        if self.video_writer is not None:
            self.video_writer.write(
                display_frame
            )

        cv2.imshow(
            WINDOW_NAME,
            display_frame,
        )

        cv2.waitKey(500)

        print("=" * 50)
        print("2. GOREV TAMAMLANDI")
        print("KIRMIZI YUK -> MAVI ALTIGEN")
        print("MAVI YUK -> KIRMIZI UCGEN")
        print(
            "AUTO CIKIS ROTASI BASLATILDI"
            if self.mission_supervisor is not None
            else "BITIS NOKTASINA GIDIS SIMULE EDILDI"
        )
        print("=" * 50)

    def start(self):
        print("=" * 62)
        print("TEKNOFEST IHA - 2. GOREV KAMERA VE YUK SISTEMI")
        print(f"MODEL: {MODEL_PATH} | KAMERA: LOGITECH C920")
        print("MAVI ALTIGEN -> KIRMIZI YUK")
        print("KIRMIZI UCGEN -> MAVI YUK")
        print("CIKIS: Q")
        print("=" * 62)
        self.terminal_event("SISTEM BASLATILIYOR")

        if MISSION_SAFE_MODE:
            self.prepare_coordinates()

        connected = (
            self.flight_controller.connect()
        )

        if not connected:
            print(
                "UYARI -> Cube baglantisi kurulamadi."
            )

            print(
                "Guvenli test modunda devam ediliyor."
            )

            self._safe_log(
                "write_log",
                "UYARI -> Cube baglantisi kurulamadi",
            )

        if not MISSION_SAFE_MODE and not self.prepare_mission_supervisor():
            self.stop()
            return

        print("=" * 50)
        print("2. GOREV KURALI")
        print("SABIT HEDEF SIRASI YOK")
        print("ILK DOGRULANAN HEDEF KILITLENIR")
        print("MAVI ALTIGEN -> KIRMIZI YUK")
        print("KIRMIZI UCGEN -> MAVI YUK")
        print("=" * 50)

        if not self.camera.is_opened():
            print("Kamera acilamadi.")

            self._safe_log("camera_failed")

            self.stop()
            return

        self._safe_log("camera_opened")
        self.terminal_event("KAMERA HAZIR")
        self.terminal_event(f"YOLO MODEL HAZIR | {MODEL_PATH}")
        self.start_video_recording()

        self._safe_log(
            "write_log",
            "2. GOREV BASLADI",
        )

        cv2.namedWindow(
            WINDOW_NAME,
            cv2.WINDOW_NORMAL,
        )

        cv2.resizeWindow(
            WINDOW_NAME,
            DISPLAY_WIDTH,
            DISPLAY_HEIGHT,
        )

        while True:
            frame = self.camera.read_frame()

            if frame is None:
                print("Goruntu alinamadi.")

                self._safe_log(
                    "write_log",
                    "GORUNTU ALINAMADI",
                )

                break

            self.failsafe.update_frame_time()

            fps = self.calculate_fps()

            if time.monotonic() - self._last_fps_print_time >= 2.0:
                self.terminal_event(
                    f"KAMERA FPS: {fps:.1f} | "
                    f"MODEL FPS: {self.detector.get_fps():.1f} | "
                    f"MODEL: {MODEL_PATH}"
                )
                self._last_fps_print_time = time.monotonic()

            if self.mission_supervisor is not None:
                mission_sequence = self.flight_controller.get_mission_current()
                self.mission_supervisor.update_mission_sequence(mission_sequence)
                search_authorized = (
                    self.mission_supervisor.camera_search_authorized
                    or self.mission_supervisor.target_intervention_active
                )
            else:
                search_authorized = True

            if not search_authorized:
                self.phase = MissionPhase.WAIT_POLE_2
            elif self.get_expected_target() is None:
                self.phase = MissionPhase.AUTO_SEARCH

            if search_authorized:
                detections = self.detector.detect(frame)
            else:
                detections = []

            expected_target = self.get_expected_target()

            if (
                expected_target is None
                and not self.detector.consume_new_result()
            ):
                active_target = None
            else:
                active_target = self._select_active_target(
                    detections
                )

            if active_target is not None and self.phase == MissionPhase.AUTO_SEARCH:
                self.phase = MissionPhase.TARGET_CONFIRM

            if (
                active_target is not None
                and self.mission_supervisor is not None
                and not self.mission_supervisor.target_intervention_active
            ):
                if not self.mission_supervisor.begin_target_intervention():
                    self.rules.active_target = None
                    active_target = None
                else:
                    self.phase = MissionPhase.GUIDED_ALIGN

            if active_target is None:
                target_data = None

            else:
                target_data = (
                    self.targeting.find_target_by_name(
                        detections=detections,
                        target_name=active_target,
                    )
                )

            status = "HEDEF ARANIYOR"
            direction = "HEDEF YOK"
            mission_state = "HEDEF ARANIYOR"
            payload_status = "BEKLIYOR"

            if self.all_targets_completed():
                self.finish_mission(
                    frame,
                    target_data,
                    fps,
                )

                break

            if active_target is None:
                self.stable_count = 0
                self.centered_since = None
                mission_state = self.phase.value

            elif target_data is None:
                self.stable_count = 0
                self.centered_since = None
                self._terminal_centered_target = None

                status = "KILITLI HEDEF KAYIP"
                direction = "HEDEFI TEKRAR ARA"
                mission_state = "HEDEF KILITLI"

                payload_status = (
                    self.get_payload_name_for_target(
                        active_target
                    )
                )

                if self.can_print(
                    self.last_lost_log_time,
                    self.LOST_LOG_INTERVAL,
                ):
                    self._safe_log(
                        "target_lost"
                    )

                    self.flight_controller.hover()

                    self.last_lost_log_time = (
                        time.time()
                    )

            else:
                detected_target = target_data[
                    "class_name"
                ]

                payload_status = (
                    self.get_payload_name_for_target(
                        detected_target
                    )
                )

                if self._terminal_announced_target != detected_target:
                    confidence = float(
                        target_data.get("confidence", 0.0)
                    )
                    self.terminal_event(
                        f"{detected_target.upper()} ALGILANDI | "
                        f"guven=%{confidence * 100:.1f} | "
                        f"kutu={target_data.get('box')}"
                    )
                    self._terminal_announced_target = detected_target

                if self.can_print(
                    self.last_target_log_time,
                    self.TARGET_LOG_INTERVAL,
                ):
                    self.failsafe.update_target_time()

                    self._safe_log(
                        "target_detected",
                        detected_target,
                        target_data.get(
                            "confidence",
                            0.0,
                        ),
                    )

                    self.last_target_log_time = (
                        time.time()
                    )

                if target_data.get(
                    "is_centered",
                    False,
                ):
                    self.flight_controller.hover()
                    if self.centered_since is None:
                        self.centered_since = time.monotonic()

                    if self._terminal_centered_target != detected_target:
                        self.terminal_event(
                            f"{detected_target.upper()} MERKEZDE | "
                            f"{CENTER_HOLD_SECONDS:.1f} sn sabitleme basladi"
                        )
                        self._terminal_centered_target = detected_target

                    centered_elapsed = time.monotonic() - self.centered_since
                    self.stable_count = int(centered_elapsed * max(fps, 1.0))
                    self.phase = MissionPhase.STABILIZE

                    status = (
                        "HEDEF ORTADA - "
                        f"{centered_elapsed:.1f}/{CENTER_HOLD_SECONDS:.1f} sn"
                    )

                    direction = "MERKEZDE"
                    mission_state = self.phase.value

                    if centered_elapsed >= CENTER_HOLD_SECONDS:
                        status = "YUK BIRAKMA SEKANSI"
                        self.phase = MissionPhase.DROP
                        mission_state = self.phase.value

                        release_success = (
                            self.release_payload_sequence(
                                detected_target
                            )
                        )

                        if release_success:
                            self._safe_log(
                                "payload_dropped",
                                detected_target,
                            )

                            if self.mission_supervisor is not None:
                                payload_key = self.rules.get_payload_for_target(
                                    detected_target
                                )
                                resumed = (
                                    self.mission_supervisor.complete_payload_and_resume(
                                        payload_key
                                    )
                                )
                                if not resumed:
                                    self.phase = MissionPhase.ABORT
                                    self._safe_log(
                                        "write_log",
                                        "KRITIK -> AUTO rotasina donulemedi",
                                    )

                            self._mark_target_completed(
                                detected_target
                            )

                            if self.all_targets_completed():
                                self.phase = MissionPhase.EXIT_ROUTE
                            elif self.phase != MissionPhase.ABORT:
                                self.phase = MissionPhase.AUTO_SEARCH

                        self.stable_count = 0
                        self.centered_since = None
                        self._terminal_announced_target = None
                        self._terminal_centered_target = None

                        time.sleep(1.0)

                else:
                    self.stable_count = 0
                    self.centered_since = None
                    self._terminal_centered_target = None
                    self.phase = MissionPhase.GUIDED_ALIGN
                    status = "HEDEF VAR - ORTALA"

                    direction = (
                        self.format_panel_direction(
                            target_data
                        )
                    )

                    mission_state = self.phase.value

                    if self.can_print(
                        self.last_approach_log_time,
                        self.APPROACH_LOG_INTERVAL,
                    ):
                        self.flight_controller.approach_target(
                            target_data.get(
                                "error_x",
                                0,
                            ),
                            target_data.get(
                                "error_y",
                                0,
                            ),
                        )

                        self.last_approach_log_time = (
                            time.time()
                        )

            display_frame = self.ui.draw(
                frame=frame,
                target_data=target_data,
                current_target=active_target,
                status=status,
                direction=direction,
                fps=fps,
                stable_count=self.stable_count,
                mission_state=mission_state,
                payload_status=payload_status,
            )

            if self.video_writer is not None:
                self.video_writer.write(
                    display_frame
                )

            cv2.imshow(
                WINDOW_NAME,
                display_frame,
            )

            key = cv2.waitKey(1) & 0xFF

            if key == ord("q"):
                print(
                    "Kullanici tarafindan durduruldu."
                )

                break

        self.stop()

    def stop(self):
        try:
            self.detector.close()

        except Exception:
            pass

        try:
            self.flight_controller.close()

        except Exception:
            pass

        try:
            self.camera.release()

        except Exception:
            pass

        if self.video_writer is not None:
            self.video_writer.release()
            self.video_writer = None

        cv2.destroyAllWindows()

        print("2. gorev sistemi kapatildi.")

        self._safe_log("system_stopped")
