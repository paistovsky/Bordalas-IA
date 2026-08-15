from typing import Any

from src.biwenger.client import BiwengerClient


# Centinela: distingue "no me pasaron cuerpo" de "el cuerpo es None".
_UNSET = object()


class BiwengerWriteClient:
    """
    Cliente de escritura de BordalÃ¡s IA.

    Todas las operaciones son DRY-RUN salvo que
    se utilice explÃ­citamente execute=True.
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
        payload: Any = _UNSET,
    ) -> bool:

        return self._evaluate_success(
            status_code,
            payload,
        )[0]

    def _evaluate_success(
        self,
        status_code: int,
        payload: Any = _UNSET,
    ) -> tuple[bool, str]:
        """
        Un codigo HTTP 200 NO significa que la operacion se haya
        hecho. La API de Biwenger devuelve el estado real dentro
        del cuerpo: el cliente de lectura ya lo valida asi
        (client.py -> if data.get("status") != 200: raise).

        Este cliente solo miraba el codigo HTTP, de modo que una
        respuesta 200 con {"status": 400, "message": "saldo
        insuficiente"} -o una pagina HTML de mantenimiento con
        codigo 200- se daba por buena. El sistema consumia la
        escritura del ciclo y persistia historial creyendo que
        habia operado.

        Devuelve (exito, motivo). El motivo viaja en la respuesta
        para poder diagnosticar sin adivinar.
        """

        if status_code not in self.SUCCESS_CODES:
            return (
                False,
                f"HTTP {status_code}",
            )

        # 204 No Content: no hay cuerpo que validar.
        if payload is None:
            return (
                True,
                "OK",
            )

        # Llamada antigua sin cuerpo: se mantiene el
        # comportamiento previo para no romper nada.
        if payload is _UNSET:
            return (
                True,
                "OK (cuerpo no verificado)",
            )

        if isinstance(payload, dict):

            inner = payload.get("status")

            if isinstance(inner, bool):
                # Algunas APIs usan status booleano.
                if not inner:
                    return (
                        False,
                        "cuerpo con status=false",
                    )

            elif isinstance(inner, int):
                if inner not in self.SUCCESS_CODES:
                    mensaje = (
                        payload.get("message")
                        or payload.get("error")
                        or ""
                    )
                    return (
                        False,
                        f"cuerpo con status={inner} {mensaje}".strip(),
                    )

            error = payload.get("error")

            if error:
                return (
                    False,
                    f"cuerpo con error: {error}",
                )

            return (
                True,
                "OK",
            )

        if isinstance(payload, str):

            texto = payload.strip()

            if not texto:
                return (
                    True,
                    "OK (cuerpo vacio)",
                )

            # Respuesta no-JSON con codigo de exito: tipicamente
            # un portal de WAF, un error de proxy o una pagina de
            # mantenimiento. No es una operacion confirmada.
            if texto.startswith("<"):
                return (
                    False,
                    "respuesta HTML, no JSON",
                )

            return (
                True,
                "OK (cuerpo de texto)",
            )

        return (
            True,
            "OK",
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
            f"{self.client.BASE_URL}/offers/"
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

        body = (
            self._safe_response(
                response
            )
        )

        (
            success,
            success_detail,
        ) = self._evaluate_success(
            response.status_code,
            body,
        )

        return {
            **request,

            "sent":
                True,

            "http_status":
                response.status_code,

            "response":
                body,

            "success":
                success,

            "success_detail":
                success_detail,
        }


    # ==================================================
    # CONTRAOFERTA A OFERTA RECIBIDA
    # ==================================================

    def build_counter_offer_request(
        self,
        offer_id: int,
        amount: int,
    ) -> dict[str, Any]:
        """
        Contraoferta validada manualmente en Biwenger.

        POST /api/v2/offers

        Payload observado:
            {
                "type": "counterOffer",
                "to": <offer_id>,
                "amount": <importe>
            }

        `to` identifica la oferta concreta a la que respondemos.
        """

        if offer_id <= 0:
            raise ValueError(
                "El offer_id debe ser mayor que 0."
            )

        if amount <= 0:
            raise ValueError(
                "La contraoferta debe ser mayor que 0."
            )

        endpoint = (
            f"{self.client.BASE_URL}/offers"
        )

        payload = {
            "type":
                "counterOffer",

            "to":
                int(
                    offer_id
                ),

            "amount":
                int(
                    amount
                ),
        }

        return {
            "operation":
                "COUNTER_OFFER",

            "method":
                "POST",

            "url":
                endpoint,

            "headers":
                self.get_headers_preview(),

            "json":
                payload,

            "offer_id":
                int(
                    offer_id
                ),

            "amount":
                int(
                    amount
                ),

            "execute":
                False,
        }

    def counter_offer(
        self,
        offer_id: int,
        amount: int,
        execute: bool = False,
    ) -> dict:
        """
        Envia una contraoferta.

        DRY-RUN por defecto.
        """

        request = (
            self.build_counter_offer_request(
                offer_id=
                    offer_id,

                amount=
                    amount,
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
            self.client.session.post(
                request["url"],
                json=
                    request["json"],
                timeout=
                    30,
            )
        )

        body = (
            self._safe_response(
                response
            )
        )

        (
            success,
            success_detail,
        ) = self._evaluate_success(
            response.status_code,
            body,
        )

        return {
            **request,

            "sent":
                True,

            "http_status":
                response.status_code,

            "response":
                body,

            "success":
                success,

            "success_detail":
                success_detail,
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

        body = (
            self._safe_response(
                response
            )
        )

        (
            success,
            success_detail,
        ) = self._evaluate_success(
            response.status_code,
            body,
        )

        return {
            **request,

            "sent":
                True,

            "http_status":
                response.status_code,

            "response":
                body,

            "success":
                success,

            "success_detail":
                success_detail,
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

        body = (
            self._safe_response(
                response
            )
        )

        (
            success,
            success_detail,
        ) = self._evaluate_success(
            response.status_code,
            body,
        )

        return {
            **request,

            "sent":
                True,

            "http_status":
                response.status_code,

            "response":
                body,

            "success":
                success,

            "success_detail":
                success_detail,
        }

    # ==================================================
    # RECHAZAR OFERTA RECIBIDA
    # ==================================================

    def build_reject_offer_request(
        self,
        offer_id: int,
    ) -> dict[str, Any]:
        """
        Rechaza una oferta recibida.

        Endpoint validado manualmente en Biwenger:

            PUT /api/v2/offers/{offer_id}

        Payload:

            {"status": "rejected"}

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

        payload = {
            "status":
                "rejected",
        }

        return {
            "operation":
                "REJECT_OFFER",

            "method":
                "PUT",

            "url":
                endpoint,

            "headers":
                self.get_headers_preview(),

            "json":
                payload,

            "offer_id":
                offer_id,

            "execute":
                False,
        }

    def reject_offer(
        self,
        offer_id: int,
        execute: bool = False,
    ) -> dict:
        """
        Rechaza una oferta recibida.

        DRY-RUN por defecto.
        """

        request = (
            self.build_reject_offer_request(
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
                json=request["json"],
                timeout=30,
            )
        )

        body = (
            self._safe_response(
                response
            )
        )

        (
            success,
            success_detail,
        ) = self._evaluate_success(
            response.status_code,
            body,
        )

        return {
            **request,

            "sent":
                True,

            "http_status":
                response.status_code,

            "response":
                body,

            "success":
                success,

            "success_detail":
                success_detail,
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

        body = (
            self._safe_response(
                response
            )
        )

        (
            success,
            success_detail,
        ) = self._evaluate_success(
            response.status_code,
            body,
        )

        return {
            **request,

            "sent":
                True,

            "http_status":
                response.status_code,

            "response":
                body,

            "success":
                success,

            "success_detail":
                success_detail,
        }

    # ==================================================
    # ALINEACIÃ“N
    # ==================================================

    def build_lineup_request(
        self,
        player_ids: list[int],
        formation: str,
        reserve_ids: list[int] | None = None,
    ) -> dict[str, Any]:

        if len(player_ids) != 11:
            raise ValueError(
                "La alineaciÃ³n debe contener "
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

        body = (
            self._safe_response(
                response
            )
        )

        (
            success,
            success_detail,
        ) = self._evaluate_success(
            response.status_code,
            body,
        )

        return {
            **request,

            "sent":
                True,

            "http_status":
                response.status_code,

            "response":
                body,

            "success":
                success,

            "success_detail":
                success_detail,
        }
