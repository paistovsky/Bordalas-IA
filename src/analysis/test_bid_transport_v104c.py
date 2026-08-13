from src.biwenger.write_client import BiwengerWriteClient
from src.analysis.controlled_speculation_live import classify_live_execution


class FakeClient:
    BASE_URL = "https://biwenger.as.com/api/v2"


def make_writer():
    writer = BiwengerWriteClient.__new__(BiwengerWriteClient)
    writer.client = FakeClient()
    writer.version = 1
    writer.league_id = 2
    writer.user_id = 3
    return writer


def test_bid_endpoint_and_payload():
    req = make_writer().build_bid_request(
        player_id=123,
        amount=1170000,
        seller_user_id=456,
    )
    assert req["url"] == "https://biwenger.as.com/api/v2/offers/"
    assert req["json"] == {
        "to": 456,
        "type": "purchase",
        "amount": 1170000,
        "requestedPlayers": [123],
    }


def test_http_400_is_rejected():
    status, reason = classify_live_execution({
        "sent": True,
        "success": False,
        "http_status": 400,
        "api_response": {"status": 400, "message": "example"},
        "offer_detected_after": False,
    })
    assert status == "LIVE_BID_REJECTED"
    assert "HTTP 400" in reason


def test_success_verified():
    status, _ = classify_live_execution({
        "sent": True,
        "success": True,
        "http_status": 200,
        "offer_detected_after": True,
    })
    assert status == "LIVE_BID_SENT_AND_VERIFIED"


def test_success_unverified_warning():
    status, _ = classify_live_execution({
        "sent": True,
        "success": True,
        "http_status": 200,
        "offer_detected_after": False,
    })
    assert status == "LIVE_BID_SENT_VERIFY_WARNING"


def main():
    tests = [
        test_bid_endpoint_and_payload,
        test_http_400_is_rejected,
        test_success_verified,
        test_success_unverified_warning,
    ]
    for fn in tests:
        fn()
        print("OK ", fn.__name__)
    print("BID TRANSPORT V10.4C: OK")


if __name__ == "__main__":
    main()
