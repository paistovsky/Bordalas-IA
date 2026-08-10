from typing import Any

from src.biwenger.client import BiwengerClient


class BiwengerWriteClient:
    """
    Cliente de escritura de Bordalás IA.

    Todas las operaciones son DRY-RUN salvo que
    se utilice explícitamente execute=True.
    """

    SUCCESS_CODES = {
        200,
        201,
        204,
    }

    def __init__(self) -> None:
        self.client = BiwengerClient()

        self.client.login()

        account = self.client.get_account()

        self.version = account.get(
            "version"
        )

        league = self.client.select_league()

        self.league = league
        self.league_id = self.client.league_id
        self.user_id = self.client.user_id

        if self.version is not None:
            self.client.session.headers.update(
                {
                    "X-Version": str(
                        self.version
                    ),
                }
            )

    # ==================================================
    # HEADERS / RESPUESTAS
    # ==================================================

    def get_headers_preview(
        self,
    ) -> dict:

        return {
            "Content-Type":
                "application/json",

            "Accept":
                "application/json, text/plain, */*",

            "X-Lang":
                "es",

            "X-Version":
                str(self.version),

            "X-League":
                str(self.league_id),

            "X-User":
                str(self.user_id),

            "Authorization":
                "*** OCULTO ***",
        }

    def _is_success(
        self,
        status_code: int,
    ) -> bool:

        return (
            status_code
            in self.SUCCESS_CODES
        )

    @staticmethod
    def _safe_response(
        response,
    ) -> Any:

        if response.status_code == 204:
            return None

        try:
            return response.json()

        except Exception:
            return response.text[:2000]

    # ==================================================
    # PUJAS
    # ==================================================

    def build_bid_request(
        self,
        player_id: int,
        amount: int,
        seller_user_id: int | None = None,
    ) -> dict[str, Any]:

        if amount <= 0:
            raise ValueError(
                "La puja debe ser mayor que 0."
            )

        endpoint = (
            f"{self.client.BASE_URL}/offers"
        )

        payload = {
            "to":
                seller_user_id,

            "type":
                "purchase",

            "amount":
                amount,

            "requestedPlayers": [
                player_id
            ],
        }

        return {
            "operation":
                "BID",

            "method":
                "POST",

            "url":
                endpoint,

            "headers":
                self.get_headers_preview(),

            "json":
                payload,

            "execute":
                False,
        }

    def place_bid(
        self,
        player_id: int,
        amount: int,
        seller_user_id: int | None = None,
        execute: bool = False,
    ) -> dict:

        request = (
            self.build_bid_request(
                player_id=player_id,
                amount=amount,
                seller_user_id=
                    seller_user_id,
            )
        )

        if not execute:
            return {
                **request,
                "sent": False,
            }

        response = (
            self.client.session.post(
                request["url"],
                json=request["json"],
                timeout=30,
            )
        )

        return {
            **request,

            "sent":
                True,

            "http_status":
                response.status_code,

            "response":
                self._safe_response(
                    response
                ),

            "success":
                self._is_success(
                    response.status_code
                ),
        }

    # ==================================================
    # CANCELAR PUJAS
    # ==================================================

    def build_cancel_bid_request(
        self,
        offer_id: int,
    ) -> dict[str, Any]:

        if offer_id <= 0:
            raise ValueError(
                "El offer_id debe ser mayor que 0."
            )

        endpoint = (
            f"{self.client.BASE_URL}"
            f"/offers/{offer_id}"
        )

        return {
            "operation":
                "CANCEL_BID",

            "method":
                "DELETE",

            "url":
                endpoint,

            "headers":
                self.get_headers_preview(),

            "offer_id":
                offer_id,

            "execute":
                False,
        }

    def cancel_bid(
        self,
        offer_id: int,
        execute: bool = False,
    ) -> dict:

        request = (
            self.build_cancel_bid_request(
                offer_id=offer_id,
            )
        )

        if not execute:
            return {
                **request,

                "sent":
                    False,

                "success":
                    True,
            }

        response = (
            self.client.session.delete(
                request["url"],
                timeout=30,
            )
        )

        return {
            **request,

            "sent":
                True,

            "http_status":
                response.status_code,

            "response":
                self._safe_response(
                    response
                ),

            "success":
                self._is_success(
                    response.status_code
                ),
        }

    # ==================================================
    # ACEPTAR OFERTA RECIBIDA
    # ==================================================

    def build_accept_offer_request(
        self,
        offer_id: int,
    ) -> dict[str, Any]:
        """
        Acepta una oferta recibida.

        Endpoint validado manualmente en Biwenger:

        PUT /api/v2/offers/{offer_id}

        La respuesta esperada marca la oferta como:
            status = processed

        IMPORTANTE:
        offer_id es el ID de la oferta,
        no el ID del jugador.
        """

        if offer_id <= 0:
            raise ValueError(
                "El offer_id debe ser mayor que 0."
            )

        endpoint = (
            f"{self.client.BASE_URL}"
            f"/offers/{offer_id}"
        )

        return {
            "operation":
                "ACCEPT_OFFER",

            "method":
                "PUT",

            "url":
                endpoint,

            "headers":
                self.get_headers_preview(),

            "offer_id":
                offer_id,

            "execute":
                False,
        }

    def accept_offer(
        self,
        offer_id: int,
        execute: bool = False,
    ) -> dict:
        """
        Acepta una oferta recibida.

        DRY-RUN por defecto.
        """

        request = (
            self.build_accept_offer_request(
                offer_id=offer_id,
            )
        )

        if not execute:
            return {
                **request,

                "sent":
                    False,

                "success":
                    True,
            }

        response = (
            self.client.session.put(
                request["url"],
                timeout=30,
            )
        )

        return {
            **request,

            "sent":
                True,

            "http_status":
                response.status_code,

            "response":
                self._safe_response(
                    response
                ),

            "success":
                self._is_success(
                    response.status_code
                ),
        }

    # ==================================================
    # MERCADO / VENTA
    # ==================================================

    def build_sale_request(
        self,
        player_id: int,
        price: int,
    ) -> dict[str, Any]:

        if price <= 0:
            raise ValueError(
                "El precio debe ser mayor que 0."
            )

        endpoint = (
            f"{self.client.BASE_URL}/market"
        )

        payload = {
            "type":
                "sell",

            "player":
                player_id,

            "price":
                price,
        }

        return {
            "operation":
                "LIST_FOR_SALE",

            "method":
                "POST",

            "url":
                endpoint,

            "headers":
                self.get_headers_preview(),

            "json":
                payload,

            "execute":
                False,
        }

    def list_player_for_sale(
        self,
        player_id: int,
        price: int,
        execute: bool = False,
    ) -> dict:

        request = (
            self.build_sale_request(
                player_id=player_id,
                price=price,
            )
        )

        if not execute:
            return {
                **request,
                "sent": False,
            }

        response = (
            self.client.session.post(
                request["url"],
                json=request["json"],
                timeout=30,
            )
        )

        return {
            **request,

            "sent":
                True,

            "http_status":
                response.status_code,

            "response":
                self._safe_response(
                    response
                ),

            "success":
                self._is_success(
                    response.status_code
                ),
        }

    # ==================================================
    # ALINEACIÓN
    # ==================================================

    def build_lineup_request(
        self,
        player_ids: list[int],
        formation: str,
        reserve_ids: list[int] | None = None,
    ) -> dict[str, Any]:

        if len(player_ids) != 11:
            raise ValueError(
                "La alineación debe contener "
                "exactamente 11 jugadores."
            )

        if len(set(player_ids)) != 11:
            raise ValueError(
                "Hay jugadores duplicados."
            )

        if reserve_ids is None:
            reserve_ids = []

        endpoint = (
            f"{self.client.BASE_URL}/user"
        )

        params = {
            "fields":
                "*,lineup(date)",
        }

        payload = {
            "lineup": {
                "type":
                    formation,

                "playersID":
                    player_ids,

                "reservesID":
                    reserve_ids,
            }
        }

        return {
            "operation":
                "LINEUP",

            "method":
                "PUT",

            "url":
                endpoint,

            "params":
                params,

            "headers":
                self.get_headers_preview(),

            "json":
                payload,

            "execute":
                False,
        }

    def save_lineup(
        self,
        player_ids: list[int],
        formation: str,
        reserve_ids: list[int] | None = None,
        execute: bool = False,
    ) -> dict:

        request = (
            self.build_lineup_request(
                player_ids=player_ids,
                formation=formation,
                reserve_ids=reserve_ids,
            )
        )

        if not execute:
            return {
                **request,
                "sent": False,
            }

        response = (
            self.client.session.put(
                request["url"],
                params=request["params"],
                json=request["json"],
                timeout=30,
            )
        )

        return {
            **request,

            "sent":
                True,

            "http_status":
                response.status_code,

            "response":
                self._safe_response(
                    response
                ),

            "success":
                self._is_success(
                    response.status_code
                ),
        }