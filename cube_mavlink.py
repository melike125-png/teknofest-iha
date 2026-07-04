from pymavlink import mavutil
import math


class CubeMavlink:
    def __init__(self, port="/dev/ttyACM0", baud=115200):
        self.port = port
        self.baud = baud
        self.master = None
        self.system_id = None
        self.component_id = None

    def connect(self, timeout=10):
        self.master = mavutil.mavlink_connection(self.port, baud=self.baud)

        heartbeat = self.master.wait_heartbeat(timeout=timeout)

        if heartbeat is None:
            raise TimeoutError("Cube heartbeat gelmedi")

        self.system_id = self.master.target_system
        self.component_id = self.master.target_component

        if self.system_id == 0:
            try:
                self.system_id = heartbeat.get_srcSystem()
            except Exception:
                self.system_id = 1

        if self.component_id == 0:
            try:
                self.component_id = heartbeat.get_srcComponent()
            except Exception:
                self.component_id = 1

        self.request_attitude_stream()
        self.request_position_stream()
        self.request_extended_status_stream()

        return True

    def is_connected(self):
        return self.master is not None and self.system_id is not None

    def request_attitude_stream(self):
        if self.master is None:
            return False

        self.master.mav.request_data_stream_send(
            self.system_id,
            self.component_id,
            mavutil.mavlink.MAV_DATA_STREAM_EXTRA1,
            10,
            1
        )

        return True

    def request_position_stream(self):
        if self.master is None:
            return False

        self.master.mav.request_data_stream_send(
            self.system_id,
            self.component_id,
            mavutil.mavlink.MAV_DATA_STREAM_POSITION,
            5,
            1
        )

        return True

    def request_extended_status_stream(self):
        if self.master is None:
            return False

        self.master.mav.request_data_stream_send(
            self.system_id,
            self.component_id,
            mavutil.mavlink.MAV_DATA_STREAM_EXTENDED_STATUS,
            2,
            1
        )

        return True

    def get_system_info(self):
        if not self.is_connected():
            return {
                "connected": False,
                "system_id": None,
                "component_id": None,
                "port": self.port,
                "baud": self.baud
            }

        return {
            "connected": True,
            "system_id": self.system_id,
            "component_id": self.component_id,
            "port": self.port,
            "baud": self.baud
        }

    def get_mode_and_arm_status(self, timeout=3):
        if self.master is None:
            return {
                "mode": "UNKNOWN",
                "armed": False,
                "message": "Cube bağlantısı yok"
            }

        msg = self.master.recv_match(type="HEARTBEAT", blocking=True, timeout=timeout)

        if msg is None:
            return {
                "mode": "UNKNOWN",
                "armed": False,
                "message": "Heartbeat verisi gelmedi"
            }

        try:
            mode = mavutil.mode_string_v10(msg)
        except Exception:
            mode = "UNKNOWN"

        armed = bool(msg.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED)

        return {
            "mode": mode,
            "armed": armed,
            "message": "OK"
        }

    def get_attitude(self, timeout=5):
        if self.master is None:
            return {
                "ok": False,
                "roll": None,
                "pitch": None,
                "yaw": None,
                "message": "Cube bağlantısı yok"
            }

        self.request_attitude_stream()

        msg = self.master.recv_match(type="ATTITUDE", blocking=True, timeout=timeout)

        if msg is None:
            return {
                "ok": False,
                "roll": None,
                "pitch": None,
                "yaw": None,
                "message": "ATTITUDE verisi gelmedi"
            }

        return {
            "ok": True,
            "roll": round(math.degrees(msg.roll), 2),
            "pitch": round(math.degrees(msg.pitch), 2),
            "yaw": round(math.degrees(msg.yaw), 2),
            "message": "OK"
        }

    def get_gps(self, timeout=3):
        if self.master is None:
            return {
                "ok": False,
                "fix_type": None,
                "satellites": None,
                "lat": None,
                "lon": None,
                "alt": None,
                "message": "Cube bağlantısı yok"
            }

        self.request_position_stream()

        msg = self.master.recv_match(type="GPS_RAW_INT", blocking=True, timeout=timeout)

        if msg is None:
            return {
                "ok": False,
                "fix_type": None,
                "satellites": None,
                "lat": None,
                "lon": None,
                "alt": None,
                "message": "GPS verisi gelmedi"
            }

        gps_data = {
            "ok": True,
            "fix_type": msg.fix_type,
            "satellites": msg.satellites_visible,
            "lat": None,
            "lon": None,
            "alt": None,
            "message": "OK"
        }

        if msg.fix_type >= 3:
            gps_data["lat"] = msg.lat / 10000000
            gps_data["lon"] = msg.lon / 10000000
            gps_data["alt"] = msg.alt / 1000
        else:
            gps_data["message"] = "GPS fix hazır değil"

        return gps_data

    def get_battery(self, timeout=3):
        if self.master is None:
            return {
                "ok": False,
                "voltage": None,
                "current": None,
                "message": "Cube bağlantısı yok"
            }

        self.request_extended_status_stream()

        msg = self.master.recv_match(type="SYS_STATUS", blocking=True, timeout=timeout)

        if msg is None:
            return {
                "ok": False,
                "voltage": None,
                "current": None,
                "message": "Batarya verisi gelmedi"
            }

        voltage = None
        current = None

        if msg.voltage_battery != 65535:
            voltage = msg.voltage_battery / 1000

        if msg.current_battery != -1:
            current = msg.current_battery / 100

        return {
            "ok": True,
            "voltage": voltage,
            "current": current,
            "message": "OK"
        }

    def get_full_status(self):
        return {
            "system": self.get_system_info(),
            "mode": self.get_mode_and_arm_status(),
            "attitude": self.get_attitude(),
            "gps": self.get_gps(),
            "battery": self.get_battery()
        }

    def close(self):
        self.master = None
        self.system_id = None
        self.component_id = None