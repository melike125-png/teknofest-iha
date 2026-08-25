from pymavlink import mavutil

from config import MAVLINK_BAUD, MAVLINK_PORT
import math
import time

PORT = MAVLINK_PORT
BAUD = MAVLINK_BAUD


def connect_cube():
    print("TEKNOFEST MAVLINK STATUS")
    print("------------------------")
    print("Port:", PORT)
    print("Baud:", BAUD)
    print("Cube bağlantısı bekleniyor...")

    master = mavutil.mavlink_connection(PORT, baud=BAUD)
    master.wait_heartbeat(timeout=10)

    print("Cube bağlantısı: OK")
    print("System ID:", master.target_system)
    print("Component ID:", master.target_component)

    return master


def read_attitude(master):
    master.mav.request_data_stream_send(
        master.target_system,
        master.target_component,
        mavutil.mavlink.MAV_DATA_STREAM_EXTRA1,
        10,
        1
    )

    msg = master.recv_match(type="ATTITUDE", blocking=True, timeout=5)

    if msg is None:
        print("Roll/Pitch/Yaw: veri gelmedi")
        return

    roll = round(math.degrees(msg.roll), 2)
    pitch = round(math.degrees(msg.pitch), 2)
    yaw = round(math.degrees(msg.yaw), 2)

    print("Roll:", roll)
    print("Pitch:", pitch)
    print("Yaw:", yaw)


def read_heartbeat_status(master):
    msg = master.recv_match(type="HEARTBEAT", blocking=True, timeout=5)

    if msg is None:
        print("Heartbeat durumu: veri gelmedi")
        return

    armed = bool(msg.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED)

    try:
        mode = mavutil.mode_string_v10(msg)
    except Exception:
        mode = "UNKNOWN"

    print("Flight Mode:", mode)
    print("Armed:", "YES" if armed else "NO")


def read_gps(master):
    msg = master.recv_match(type="GPS_RAW_INT", blocking=True, timeout=5)

    if msg is None:
        print("GPS: veri gelmedi")
        return

    fix_type = msg.fix_type
    satellites = msg.satellites_visible

    print("GPS Fix Type:", fix_type)
    print("Satellite Count:", satellites)

    if fix_type >= 3:
        lat = msg.lat / 10000000
        lon = msg.lon / 10000000
        alt = msg.alt / 1000

        print("Latitude:", lat)
        print("Longitude:", lon)
        print("Altitude:", alt, "m")
    else:
        print("GPS konumu hazır değil")


def read_battery(master):
    msg = master.recv_match(type="SYS_STATUS", blocking=True, timeout=5)

    if msg is None:
        print("Battery: veri gelmedi")
        return

    voltage = msg.voltage_battery / 1000
    current = msg.current_battery / 100

    if msg.voltage_battery == 65535:
        print("Battery voltage: veri yok")
    else:
        print("Battery voltage:", voltage, "V")

    if msg.current_battery == -1:
        print("Battery current: veri yok")
    else:
        print("Battery current:", current, "A")


def main():
    try:
        master = connect_cube()

        print("------------------------")
        read_heartbeat_status(master)

        print("------------------------")
        read_attitude(master)

        print("------------------------")
        read_gps(master)

        print("------------------------")
        read_battery(master)

        print("------------------------")
        print("Status testi tamamlandı")

    except Exception as e:
        print("HATA:", e)


if __name__ == "__main__":
    main()
