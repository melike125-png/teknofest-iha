from abc import ABC, abstractmethod
import time

from config import MAVLINK_BAUD, MAVLINK_PORT


class PayloadController(ABC):
    """
    Fiziksel yük mekanizmasından bağımsız ortak arayüz.

    Servo, lineer aktüatör veya başka bir mekanizma seçildiğinde
    yalnızca bu arayüzü kullanan yeni bir donanım sınıfı yazılacaktır.
    Görev kodunun geri kalanı değişmeyecektir.
    """

    @abstractmethod
    def release_red_payload(self) -> bool:
        """Kırmızı yükü bırakır."""
        raise NotImplementedError

    @abstractmethod
    def release_blue_payload(self) -> bool:
        """Mavi yükü bırakır."""
        raise NotImplementedError

    @abstractmethod
    def center_remaining_payload(self) -> bool:
        """
        İlk yük bırakıldıktan sonra kalan yükü merkeze alma isteğini çalıştırır.

        Mekanizmada merkezleme sistemi bulunmazsa bu fonksiyon
        güvenli şekilde True döndüren bir işlem olarak bırakılabilir.
        """
        raise NotImplementedError

    @abstractmethod
    def get_status(self) -> dict:
        """Yük sisteminin güncel durumunu döndürür."""
        raise NotImplementedError


class SimulatedPayloadController(PayloadController):
    """
    Fiziksel donanım kullanmadan görev akışını test eder.
    Servo, GPIO veya motor komutu göndermez.
    """

    def __init__(self):
        self.red_payload_released = False
        self.blue_payload_released = False
        self.remaining_payload_centered = False

        print("Yük sistemi simülasyon modunda başlatıldı.")

    def release_red_payload(self) -> bool:
        if self.red_payload_released:
            print("UYARI: Kırmızı yük daha önce bırakılmış.")
            return False

        print("SİMÜLASYON: Kırmızı yük bırakma komutu oluşturuldu.")
        self.red_payload_released = True
        self.remaining_payload_centered = False
        return True

    def release_blue_payload(self) -> bool:
        if self.blue_payload_released:
            print("UYARI: Mavi yük daha önce bırakılmış.")
            return False

        print("SİMÜLASYON: Mavi yük bırakma komutu oluşturuldu.")
        self.blue_payload_released = True
        self.remaining_payload_centered = False
        return True

    def center_remaining_payload(self) -> bool:
        released_count = int(self.red_payload_released) + int(
            self.blue_payload_released
        )

        if released_count == 0:
            print("UYARI: Henüz yük bırakılmadı; merkezleme gerekmiyor.")
            return False

        if released_count == 2:
            print("SİMÜLASYON: İki yük de bırakıldı; taşıyıcı orta konuma döndü.")
            self.remaining_payload_centered = True
            return True

        print("SİMÜLASYON: Kalan yükü merkeze alma komutu oluşturuldu.")
        self.remaining_payload_centered = True
        return True

    def get_status(self) -> dict:
        return {
            "mode": "SIMULATION",
            "red_payload_released": self.red_payload_released,
            "blue_payload_released": self.blue_payload_released,
            "remaining_payload_centered": self.remaining_payload_centered,
        }


class MavlinkServoPayloadController(PayloadController):
    """Calibrated MG996R continuous-servo payload controller."""

    PORT = MAVLINK_PORT
    BAUD = MAVLINK_BAUD
    SERVO_CHANNEL = 9
    STOP_PWM = 1500
    CW_PWM = 1933
    CW_DURATION = 0.85
    CCW_PWM = 1000
    CCW_DURATION = 0.75

    def __init__(self, master=None, sleep_function=time.sleep):
        self._sleep = sleep_function
        if master is None:
            from pymavlink import mavutil

            print(f"GERCEK SERVO TEST MODU -> {self.PORT} baglantisi bekleniyor...")
            master = mavutil.mavlink_connection(self.PORT, baud=self.BAUD)
            heartbeat = master.wait_heartbeat(timeout=10)
            if heartbeat is None:
                raise RuntimeError("Cube heartbeat alinamadi; servo devre disi.")
        self.master = master
        self.current_state = "neutral"
        self.red_payload_released = False
        self.blue_payload_released = False
        print("GERCEK SERVO TEST MODU HAZIR -> AUX OUT 1 / kanal 9")

    def _set_pwm(self, pwm):
        from pymavlink import mavutil

        self.master.mav.command_long_send(
            self.master.target_system,
            self.master.target_component,
            mavutil.mavlink.MAV_CMD_DO_SET_SERVO,
            0,
            self.SERVO_CHANNEL,
            int(pwm),
            0, 0, 0, 0, 0,
        )

    def _move(self, target_state):
        transitions = {
            ("neutral", "cw_release"): (self.CW_PWM, self.CW_DURATION),
            ("neutral", "ccw_release"): (self.CCW_PWM, self.CCW_DURATION),
            ("cw_release", "ccw_release"): (
                self.CCW_PWM,
                self.CCW_DURATION * 2,
            ),
            ("ccw_release", "cw_release"): (
                self.CW_PWM,
                self.CW_DURATION * 2,
            ),
        }
        transition = transitions.get((self.current_state, target_state))
        if transition is None:
            print(f"SERVO -> Zaten {target_state} konumunda; hareket yok.")
            return False

        pwm, duration = transition
        print(
            f"SERVO HAREKET -> {self.current_state} => {target_state} | "
            f"PWM={pwm} | sure={duration:.2f} sn"
        )
        self._set_pwm(pwm)
        try:
            self._sleep(duration)
        finally:
            self._set_pwm(self.STOP_PWM)
        self.current_state = target_state
        print(f"SERVO DURDU -> PWM={self.STOP_PWM} | konum={target_state}")
        return True

    def release_red_payload(self) -> bool:
        if self.red_payload_released:
            print("UYARI -> Kirmizi yuk daha once birakildi.")
            return False
        if not self._move("ccw_release"):
            return False
        self.red_payload_released = True
        print("GERCEK SERVO -> KIRMIZI YUK BIRAKILDI")
        return True

    def release_blue_payload(self) -> bool:
        if self.blue_payload_released:
            print("UYARI -> Mavi yuk daha once birakildi.")
            return False
        if not self._move("cw_release"):
            return False
        self.blue_payload_released = True
        print("GERCEK SERVO -> MAVI YUK BIRAKILDI")
        return True

    def center_remaining_payload(self) -> bool:
        # Bu surekli donen mekanizmada ilk birakmadan sonra ek merkezleme
        # yapilmaz. Ikinci yuk icin karsi konuma gecis _move tarafindan yapilir.
        print("SERVO -> Ek merkezleme yok; mekanizma mevcut konumda tutuluyor.")
        return True

    def get_status(self) -> dict:
        return {
            "mode": "REAL_SERVO_TEST",
            "state": self.current_state,
            "red_payload_released": self.red_payload_released,
            "blue_payload_released": self.blue_payload_released,
        }
