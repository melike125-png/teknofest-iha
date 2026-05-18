PROJECT_NAME = "TEKNOFEST IHA GOREV SISTEMI"

MODEL_PATH = "best.pt"

CAMERA_INDEX = 0

FRAME_WIDTH = 640
FRAME_HEIGHT = 480

CONF_LIMIT = 0.50
IOU_LIMIT = 0.10
MAX_DETECTION = 5

CENTER_TOLERANCE = 80
STABLE_LIMIT = 5

# Yarisma oncesi sadece burayi degistireceksin
# Alttaki yuk hangisiyse onu ilk yaz
PAYLOAD_ORDER = [
    "mavi",
    "kirmizi"
]

# Gorev kurali
PAYLOAD_TARGET_MAP = {
    "mavi": "kirmizi_ucgen",
    "kirmizi": "mavi_altigen"
}

VIDEO_OUTPUT_NAME = "test_kaydi.mp4"

# Tek servo kullaniyoruz
DROP_SERVO_PIN = 17