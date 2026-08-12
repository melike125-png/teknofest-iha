from abc import ABC, abstractmethod


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