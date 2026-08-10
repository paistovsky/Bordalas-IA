from types import SimpleNamespace

from src.biwenger.write_client import (
    BiwengerWriteClient,
)


TEST_OFFER_ID = 3749851250


def main() -> None:
    """
    Test 100% local del request.

    NO hace login.
    NO envia HTTP.
    NO modifica Biwenger.
    """

    writer = BiwengerWriteClient.__new__(
        BiwengerWriteClient
    )

    writer.client = SimpleNamespace(
        BASE_URL="https://biwenger.as.com/api/v2"
    )

    writer.version = 631
    writer.league_id = 2165477
    writer.user_id = 14175949

    request = writer.build_reject_offer_request(
        offer_id=TEST_OFFER_ID
    )

    print()
    print("=" * 100)
    print("                    BORDALAS IA - REJECT OFFER REQUEST TEST")
    print("=" * 100)
    print()

    print(f"Operation:      {request['operation']}")
    print(f"Method:         {request['method']}")
    print(f"URL:            {request['url']}")
    print(f"Payload:        {request['json']}")
    print(f"Execute:        {request['execute']}")
    print()

    if request["method"] != "PUT":
        raise SystemExit(
            "ERROR: metodo incorrecto."
        )

    if request["json"] != {
        "status": "rejected"
    }:
        raise SystemExit(
            "ERROR: payload incorrecto."
        )

    expected_url = (
        "https://biwenger.as.com/api/v2/"
        f"offers/{TEST_OFFER_ID}"
    )

    if request["url"] != expected_url:
        raise SystemExit(
            "ERROR: endpoint incorrecto."
        )

    if request["execute"] is not False:
        raise SystemExit(
            "ERROR: el builder debe ser DRY-RUN."
        )

    print("REJECT OFFER REQUEST: OK")
    print("=" * 100)


if __name__ == "__main__":
    main()
