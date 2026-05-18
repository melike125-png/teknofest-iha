class FlightController:

    def __init__(self):
        self.connected = False
        print("Flight controller test modu acildi.")

    def move_by_direction(self, direction):

        if direction == "":
            print("Hedef merkezde, hareket yok.")
            return

        print("=" * 40)
        print("UCUS KOMUTU")
        print(f"Yon bilgisi: {direction}")

        if "SAGDA" in direction:
            print("Drone saga kaymali.")

        if "SOLDA" in direction:
            print("Drone sola kaymali.")

        if "YUKARIDA" in direction:
            print("Drone ileri gitmeli.")

        if "ASAGIDA" in direction:
            print("Drone geri gitmeli.")

        print("=" * 40)

    def stop(self):
        print("Drone hareketi durduruldu.")

    def land(self):
        print("Inis komutu verildi.")

    def failsafe_hold(self):
        print("Failsafe: Drone sabit bekleme moduna alinmali.")