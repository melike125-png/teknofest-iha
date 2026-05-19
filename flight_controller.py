class FlightController:



    _NO_MOVE_DIRECTIONS = {"", "CENTER", "MERKEZDE"}



    _DIRECTION_MESSAGES = {

        "LEFT": "Drone sola kaymali.",

        "RIGHT": "Drone saga kaymali.",

        "UP": "Drone ileri gitmeli.",

        "DOWN": "Drone geri gitmeli.",

    }



    def __init__(self):

        self.connected = False

        print("Flight controller test modu acildi.")



    def move_by_direction(self, direction):



        if direction in self._NO_MOVE_DIRECTIONS:

            print("Hedef merkezde, hareket yok.")

            return



        print("=" * 40)

        print("UCUS KOMUTU")

        print(f"Yon bilgisi: {direction}")



        movement_found = False



        for part in direction.upper().split():

            message = self._DIRECTION_MESSAGES.get(part)



            if message is not None:

                print(message)

                movement_found = True



        if not movement_found:

            print("Simulasyon: Bu yon icin hareket komutu tanimli degil.")



        print("=" * 40)



    def stop(self):

        print("Drone hareketi durduruldu.")



    def land(self):

        print("Inis komutu verildi.")



    def failsafe_hold(self):

        print("Failsafe: Drone sabit bekleme moduna alinmali.")


