import os
from typing import Any

import requests
from dotenv import load_dotenv


class BiwengerClient:
    """Cliente básico para interactuar con la API de Biwenger."""

    BASE_URL = "https://biwenger.as.com/api/v2"

    def __init__(self) -> None:
        load_dotenv()

        self.username = os.getenv("BIWENGER_USERNAME")
        self.password = os.getenv("BIWENGER_PASSWORD")

        if not self.username or not self.password:
            raise RuntimeError(
                "No se han encontrado BIWENGER_USERNAME "
                "y/o BIWENGER_PASSWORD en .env"
            )

        self.token: str | None = None
        self.league_id: int | None = None
        self.user_id: int | None = None

        self.session = requests.Session()

        self.session.headers.update(
            {
                "Content-Type": "application/json",
                "Accept": "application/json, text/plain, */*",
                "X-Lang": "es",
            }
        )

    # --------------------------------------------------
    # AUTENTICACIÓN
    # --------------------------------------------------

    def login(self) -> None:
        """Inicia sesión y obtiene el token de Biwenger."""

        response = self.session.post(
            f"{self.BASE_URL}/auth/login",
            json={
                "email": self.username,
                "password": self.password,
            },
        )

        response.raise_for_status()

        data = response.json()

        if "token" not in data:
            raise RuntimeError("Biwenger no ha devuelto un token.")

        self.token = data["token"]

        self.session.headers.update(
            {
                "Authorization": f"Bearer {self.token}",
            }
        )

    # --------------------------------------------------
    # CUENTA / LIGA
    # --------------------------------------------------

    def get_account(self) -> dict[str, Any]:
        """Obtiene la información de la cuenta."""

        self._check_login()

        response = self.session.get(
            f"{self.BASE_URL}/account"
        )

        response.raise_for_status()

        data = response.json()

        if data.get("status") != 200:
            raise RuntimeError(
                f"Error obteniendo cuenta: {data}"
            )

        return data["data"]

    def select_league(self) -> dict[str, Any]:
        """Selecciona automáticamente la primera liga de la cuenta."""

        account = self.get_account()

        leagues = account.get("leagues", [])

        if not leagues:
            raise RuntimeError(
                "La cuenta no tiene ninguna liga."
            )

        league = leagues[0]

        self.league_id = league["id"]
        self.user_id = league["user"]["id"]

        self.session.headers.update(
            {
                "X-League": str(self.league_id),
                "X-User": str(self.user_id),
            }
        )

        return league

    # --------------------------------------------------
    # PLANTILLA
    # --------------------------------------------------

    def get_my_player_ids(self) -> list[int]:
        """Obtiene los IDs de los jugadores de nuestra plantilla."""

        self._check_login()

        response = self.session.get(
            f"{self.BASE_URL}/user",
            params={
                "fields": "players(id,owner)"
            },
        )

        response.raise_for_status()

        data = response.json()

        players = data.get("data", {}).get("players", [])

        return [
            int(player["id"])
            for player in players
        ]

    # --------------------------------------------------
    # CATÁLOGO
    # --------------------------------------------------

    def get_player_catalog(self) -> dict[str, Any]:
        """Obtiene el catálogo completo de jugadores de LaLiga."""

        self._check_login()

        response = self.session.get(
            f"{self.BASE_URL}/competitions/la-liga/data",
            params={
                "lang": "es",
                "score": 5,
            },
        )

        response.raise_for_status()

        data = response.json()

        return data["data"]["players"]

    # --------------------------------------------------
    # MI EQUIPO
    # --------------------------------------------------

    def get_my_team(self) -> list[dict[str, Any]]:
        """Obtiene información completa de nuestros jugadores."""

        player_ids = self.get_my_player_ids()
        catalog = self.get_player_catalog()

        team = []

        for player_id in player_ids:
            player = catalog.get(str(player_id))

            if player is not None:
                team.append(player)

        return team

    # --------------------------------------------------
    # MERCADO
    # --------------------------------------------------

    def get_market(self) -> dict[str, Any]:
        """Obtiene el mercado actual de la liga."""

        self._check_login()

        response = self.session.get(
            f"{self.BASE_URL}/market"
        )

        response.raise_for_status()

        data = response.json()

        return data["data"]

    # --------------------------------------------------
    # UTILIDADES
    # --------------------------------------------------

    def _check_login(self) -> None:
        """Comprueba que existe una sesión autenticada."""

        if self.token is None:
            raise RuntimeError(
                "El cliente no está autenticado. "
                "Ejecuta login() primero."
            )