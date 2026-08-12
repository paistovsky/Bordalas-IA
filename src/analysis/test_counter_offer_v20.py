from src.biwenger.write_client import BiwengerWriteClient


def main():

    # No instanciamos el cliente real (haría login).
    client = object.__new__(
        BiwengerWriteClient
    )

    class FakeClient:
        BASE_URL = "https://biwenger.as.com/api/v2"

    client.client = FakeClient()
    client.version = 631
    client.league_id = 2165477
    client.user_id = 14175949

    request = (
        client.build_counter_offer_request(
            offer_id=
                2917410105,

            amount=
                5_640_000,
        )
    )

    print(request)

    assert request["method"] == "POST"
    assert request["url"] == "https://biwenger.as.com/api/v2/offers"
    assert request["json"] == {
        "type": "counterOffer",
        "to": 2917410105,
        "amount": 5640000,
    }
    assert request["execute"] is False

    print()
    print("=" * 92)
    print("BIWENGER COUNTER OFFER V2.0: OK")
    print("PAYLOAD IDENTICO A LA CAPTURA MANUAL")
    print("NO SE HA ENVIADO NINGUNA PETICION")
    print("=" * 92)


if __name__ == "__main__":
    main()
