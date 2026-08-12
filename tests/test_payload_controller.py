from payload_controller import SimulatedPayloadController


def main():
    payload = SimulatedPayloadController()

    print("\nİlk durum:")
    print(payload.get_status())

    print("\nKırmızı yük bırakılıyor:")
    assert payload.release_red_payload() is True

    print("\nKalan yük merkeze alınıyor:")
    assert payload.center_remaining_payload() is True

    print("\nKırmızı yük tekrar bırakılmaya çalışılıyor:")
    assert payload.release_red_payload() is False

    print("\nMavi yük bırakılıyor:")
    assert payload.release_blue_payload() is True

    print("\nBoş taşıyıcı orta konuma getiriliyor:")
    assert payload.center_remaining_payload() is True

    final_status = payload.get_status()

    print("\nSon durum:")
    print(final_status)

    assert final_status["red_payload_released"] is True
    assert final_status["blue_payload_released"] is True
    assert final_status["remaining_payload_centered"] is True

    print("\nTEST BAŞARILI")


if __name__ == "__main__":
    main()