from typing import Any

from src.biwenger.client import BiwengerClient


# Centinela: distingue "no me pasaron cuerpo" de "el cuerpo es None".
_UNSET = object()


# EL ENSAYO (27/09/2026)
#
#     Un Pepe entero que lee Biwenger de verdad y no escribe NADA.
#     Todas las escrituras del proyecto pasan por los metodos de esta
#     clase (auditoria del 26/09, seccion C; eran siete, la racha del
#     28/09 es la octava), y todos salen por la misma puerta:
#     `if not execute`. Con `BORDALAS_ENSAYO=1`
#     esa puerta se cierra tambien con execute=True, y lo que se habria
#     enviado se apunta en `ESCRITURAS_DEL_ENSAYO` para revisarlo.
#
#     Lo usa `.github/workflows/bordalas-ensayo.yml`, el entorno de
#     pruebas. En produccion no esta puesto: sin el, nada cambia.
ENSAYO_ENV = "BORDALAS_ENSAYO"

ESCRITURAS_DEL_ENSAYO = "data/ensayo/escrituras_no_enviadas.jsonl"


def en_ensayo() -> bool:
    """Si esta vuelta es un ensayo. Nunca lanza."""

    try:
        import os

        return str(
            os.environ.get(ENSAYO_ENV, "")
        ).strip().lower() in {"1", "true", "si", "yes"}

    except Exception:                               # noqa: BLE001
        # Si no se puede leer, se trata como ensayo: el lado seguro de
        # no saber es no escribir.
        return True


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

    def _en_ensayo(self, request: dict) -> bool:
        """
        En ensayo, apunta la escritura que se habria hecho y dice que
        no se envie. Fuera de ensayo, no hace nada. Nunca lanza: si no
        puede apuntar, igualmente no se envia.
        """

        if not en_ensayo():
            return False

        try:
            import json
            import os

            from datetime import datetime, timezone

            os.makedirs(
                os.path.dirname(ESCRITURAS_DEL_ENSAYO),
                exist_ok=True,
            )

            with open(
                ESCRITURAS_DEL_ENSAYO, "a", encoding="utf-8"
            ) as fichero:
                fichero.write(
                    json.dumps(
                        {
                            "at": datetime.now(timezone.utc).isoformat(),
                            "operation": request.get("operation"),
                            "method": request.get("method"),
                            "url": request.get("url"),
                            "json": request.get("json"),
                        },
                        ensure_ascii=False,
                        default=str,
                    )
                    + "\n"
                )

        except Exception:                           # noqa: BLE001
            pass

        return True

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

        if not execute or self._en_ensayo(request):
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

        if not execute or self._en_ensayo(request):

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

        if not execute or self._en_ensayo(request):
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

        Payload:

            {"status": "accepted"}

        La respuesta esperada marca la oferta como:
            status = processed

        IMPORTANTE:
        offer_id es el ID de la oferta,
        no el ID del jugador.

        EL CUERPO QUE FALTABA (19/08/2026)

            Esta era la unica escritura del fichero que no
            mandaba cuerpo. Las otras cinco pasan
            `json=request["json"]`; esta hacia un PUT pelado a
            /offers/{id}, y Biwenger contestaba HTTP 500.

            Se vio en el dashboard: "ACCEPT RECOVERY OFFER
            apartada: ha fallado 4 veces seguidas (HTTP 500)".

            Llevaba asi desde que se escribio, y no se habia
            notado nunca porque nadie llamaba a esta rama: el
            camino de cobrar estaba desconectado del orquestador
            -las cinco paredes del 18/08- y se conecto ayer.

            El endpoint es el mismo que el de rechazar, que si
            manda {"status": "rejected"} y funciona. Lo unico
            que cambiaba entre aceptar y rechazar una oferta era
            justo la palabra que no se enviaba.
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
                "accepted",
        }

        return {
            "operation":
                "ACCEPT_OFFER",

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

        if not execute or self._en_ensayo(request):
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

        if not execute or self._en_ensayo(request):
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

        # LOS PROTEGIDOS DE LA ORDEN DEL GESTOR (29/09/2026)
        #
        #     Con el saldo en rojo, la liquidez publica a cualquiera en
        #     el orden de Biwenger, y lo publicado recibe oferta del
        #     Computer. Aqui, que es la unica puerta de publicar, se
        #     cierra para los que la orden protege (el fichaje y
        #     Yamal). Con la orden apagada o caducada, nada cambia.
        try:
            from src.actions.la_orden_del_gestor import protegidos

            if int(player_id) in protegidos():
                return {
                    **request,
                    "sent": False,
                    "success": False,
                    "blocked": "PROTEGIDO_POR_LA_ORDEN_DEL_GESTOR",
                }
        except Exception:                           # noqa: BLE001
            pass

        if not execute or self._en_ensayo(request):
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

        if not execute or self._en_ensayo(request):
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

    # ==================================================
    # COBRAR LA RACHA DIARIA (28/09/2026)
    # ==================================================
    #
    #     La octava escritura. 250.000 EUR al llegar a cinco dias
    #     seguidos. Es la misma llamada que hace el boton «Canjear»
    #     de la app de Biwenger (modulo de usuario, v631):
    #     POST /account/dailyStreak/redeem con {"league": <id>}.

    def build_redeem_streak_request(
        self,
        league_id: int,
    ) -> dict[str, Any]:

        if not league_id or int(league_id) <= 0:
            raise ValueError(
                "El league_id debe ser mayor que 0."
            )

        endpoint = (
            f"{self.client.BASE_URL}"
            f"/account/dailyStreak/redeem"
        )

        return {
            "operation":
                "REDEEM_DAILY_STREAK",

            "method":
                "POST",

            "url":
                endpoint,

            "headers":
                self.get_headers_preview(),

            "json":
                {"league": int(league_id)},

            "execute":
                False,
        }

    def redeem_daily_streak(
        self,
        league_id: int,
        execute: bool = False,
    ) -> dict:

        request = (
            self.build_redeem_streak_request(
                league_id=league_id,
            )
        )

        if not execute or self._en_ensayo(request):
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
