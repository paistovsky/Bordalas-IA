import os
import requests
from dotenv import load_dotenv


load_dotenv()

USERNAME = os.getenv("BIWENGER_USERNAME")
PASSWORD = os.getenv("BIWENGER_PASSWORD")

BASE_URL = "https://biwenger.as.com/api/v2"
LEAGUE_ID = "2165477"


# --------------------------------------------------
# LOGIN
# --------------------------------------------------

login = requests.post(
    f"{BASE_URL}/auth/login",
    json={
        "email": USERNAME,
        "password": PASSWORD,
    },
)

login.raise_for_status()

token = login.json()["token"]

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json",
    "Accept": "application/json, text/plain, */*",
    "X-Lang": "es",
    "X-League": LEAGUE_ID,
    "X-User": "14175949",
}


# --------------------------------------------------
# ENDPOINTS
# --------------------------------------------------

endpoints = [
    f"/league/{LEAGUE_ID}",
    "/rounds/league",
    f"/league/{LEAGUE_ID}/board",
    f"/league/{LEAGUE_ID}/board?type=transfer,market",
]


for endpoint in endpoints:

    print()
    print("=" * 70)
    print(endpoint)
    print("=" * 70)

    response = requests.get(
        BASE_URL + endpoint,
        headers=headers,
    )

    print("HTTP:", response.status_code)

    try:
        data = response.json()

        # No imprimimos todo el JSON esta vez.
        # Solo queremos conocer las claves.
        print("Claves principales:", data.keys())

        if isinstance(data.get("data"), dict):
            print("Claves de data:", data["data"].keys())

            if "league" in data["data"]:
                print(
                    "Claves de league:",
                    data["data"]["league"].keys()
                )

        elif isinstance(data.get("data"), list):
            print(
                "data es una lista de",
                len(data["data"]),
                "elementos"
            )

            if data["data"]:
                print(
                    "Claves del primer elemento:",
                    data["data"][0].keys()
                )

    except Exception:
        print(response.text[:5000])