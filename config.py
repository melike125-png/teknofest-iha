# config.py

# =========================================
# PROJE
# =========================================

PROJECT_NAME = "TEKNOFEST IHA GOREV SISTEMI"


# =========================================
# MODEL
# =========================================

MODEL_PATH = "best.pt"

CONF_LIMIT = 0.60

MAX_DETECTION = 5

# YOLO'nun üst üste binen kutuları temizlemesi için kullanılır.
# Düşük olursa aynı hedefe çok fazla kutu çizmesini azaltır.
IOU_LIMIT = 0.10


# =========================================
# KAMERA
# =========================================

FRAME_WIDTH = 640
FRAME_HEIGHT = 480

CAMERA_INDEX = 0


# =========================================
# VIDEO
# =========================================

VIDEO_OUTPUT_NAME = "test_kaydi.mp4"


# =========================================
# SERVO / YUK BIRAKMA MEKANIZMASI
# =========================================

# Servo 1:
# Kirmizi yuku tutan servo.
# Mavi altigen gorulunce bu servo acilacak.
SERVO_1_PIN = 17

# Servo 2:
# Mavi yuku tutan servo.
# Kirmizi ucgen gorulunce bu servo acilacak.
SERVO_2_PIN = 18

# Servo kapali acisi.
# 60 derecede pim kapali olacak, yuk dusmeyecek.
SERVO_CLOSED_ANGLE = 60

# Servo acik acisi.
# 120 derecede pim acilacak, yuk birakilacak.
SERVO_OPEN_ANGLE = 120

# Servo acik kaldiktan sonra kac saniye beklenecek.
SERVO_RELEASE_WAIT = 1.0


# =========================================
# HEDEF SINIF ISIMLERI
# =========================================

# Bunlar YOLO modelinin class isimleriyle ayni olmalidir.
TARGET_BLUE_HEXAGON = "mavi_altigen"
TARGET_RED_TRIANGLE = "kirmizi_ucgen"


# =========================================
# YUK - HEDEF ESLESMESI
# =========================================

# Mavi altigen gorulunce Servo 1 acilir ve kirmizi yuk birakilir.
RED_PAYLOAD_TARGET = TARGET_BLUE_HEXAGON

# Kirmizi ucgen gorulunce Servo 2 acilir ve mavi yuk birakilir.
BLUE_PAYLOAD_TARGET = TARGET_RED_TRIANGLE


# =========================================
# HEDEF MERKEZLEME
# =========================================

CENTER_TOLERANCE_X = 40
CENTER_TOLERANCE_Y = 40

# Hedefin arka arkaya kac frame merkezde kalmasi gerektigi.
STABLE_LIMIT = 5


# =========================================
# GOREV AYARLARI
# =========================================

SEARCH_AREA_WIDTH = 30
SEARCH_AREA_LENGTH = 200
SEARCH_LINE_SPACING = 5

# Normal gorev irtifasi.
MISSION_ALTITUDE = 25

# Yuk birakmadan once alcalinacak irtifa.
DROP_ALTITUDE = 10


# =========================================
# PID AYARLARI
# =========================================

PID_X_KP = 0.4
PID_X_KI = 0.01
PID_X_KD = 0.15

PID_Y_KP = 0.4
PID_Y_KI = 0.01
PID_Y_KD = 0.15


# =========================================
# 8 CIZME GOREVI
# =========================================

INFINITY8_RADIUS = 15
INFINITY8_POINT_COUNT = 80


# =========================================
# STREAM
# =========================================

STREAM_WIDTH = 640
STREAM_HEIGHT = 480


# =========================================
# MEMORY
# =========================================

TARGET_MEMORY_TIMEOUT = 2.0


# =========================================
# FAILSAFE
# =========================================

MIN_FPS = 5
MAX_TARGET_LOST_TIME = 5


# =========================================
# LOGGER
# =========================================

LOG_FILE_NAME = "mission_log.txt"