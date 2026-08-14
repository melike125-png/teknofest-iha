from config import PAYLOAD_ORDER, PAYLOAD_TARGET_MAP


def run_mock_mission():

    print("=" * 50)
    print("KAMERASIZ GOREV SIMULASYONU BASLADI")
    print("=" * 50)

    for index, payload in enumerate(PAYLOAD_ORDER):

        target = PAYLOAD_TARGET_MAP[payload]

        print(f"\nGOREV {index + 1}")
        print(f"Aktif yuk   : {payload}")
        print(f"Aktif hedef : {target}")

        print("Sahte algilama yapildi.")
        print(f"{target} kamerada goruldu kabul edildi.")

        print("Hedef ortalandi kabul edildi.")
        print(f"{payload} yuk -> {target} hedefine birakildi.")

    print("\n" + "=" * 50)
    print("TUM YUKLER BIRAKILDI")
    print("GOREV SIMULASYONU TAMAMLANDI")
    print("=" * 50)


if __name__ == "__main__":
    run_mock_mission()