from src.analysis.accept_before_expiry_live_selector import (
    select_emergency_accept_offer,
)

from src.analysis.speculation_engine import (
    build_speculation_board,
)

from src.analysis.market_listing_lifecycle_engine import (
    build_market_listing_lifecycle_board,
    resolve_renewal_price,
)

from src.analysis.computer_offer_reroll_engine import (
    record_reroll,
    revalidate_reroll_offer,
)

from src.analysis.market_analyzer import (
    get_latest_snapshot,
    load_snapshot,
)

from src.collectors.league_collector import (
    collect_league_snapshot,
)

from src.analysis.lineup_monitor import (
    save_lineup_monitor_state,
)

from src.biwenger.write_client import (
    BiwengerWriteClient,
)


HARD_SAFETY_ALLOWED_ACTIONS = {
    "LIST_FOR_LIQUIDITY",
    "ACCEPT_RECOVERY_OFFER",
    "ACCEPT_CLUSTER_BEFORE_EXPIRY",
    "SAVE_LINEUP",
}

# Reroll nunca se autoriza dentro de Hard Safety.
REROLL_ACTION = "REROLL_COMPUTER_OFFER"
RENEW_LISTING_ACTION = "RENEW_MARKET_LISTING"
ACCEPT_EXPIRY_ACTION = "ACCEPT_CLUSTER_BEFORE_EXPIRY"
SPECULATION_BUY_ACTION = "BUY_SPECULATION"


# ==================================================
# DEDUPLICACION DE PUJAS SALIENTES
# ==================================================

ACTIVE_OFFER_STATUS = {
    "waiting",
    "pending",
}


def get_own_user_id(
    snapshot: dict,
) -> int | None:

    valor = (
        (
            snapshot.get(
                "league",
                {},
            )
            or {}
        ).get(
            "user",
            {},
        )
        or {}
    ).get(
        "id"
    )

    try:
        return (
            int(valor)
            if valor is not None
            else None
        )

    except (TypeError, ValueError):
        return None


def find_own_pending_bid(
    snapshot: dict,
    player_id: int,
) -> dict | None:
    """
    Busca una puja SALIENTE nuestra, todavia viva, por este
    jugador.

    La rama BUY_SPECULATION revalidaba saldo, presupuesto,
    propiedad y precio, pero no miraba si ya teniamos una puja
    pendiente por el mismo jugador. Como una puja no se resuelve
    hasta el cierre de mercado, el jugador seguia en el mercado y
    el saldo no se descontaba, asi que el mismo objetivo volvia a
    salir como executable_buys[0] en cada ciclo: una puja nueva
    cada 30 minutos sobre lo mismo.

    Filtra por direccion a proposito. En el snapshot real las
    ofertas entrantes llegan con from=None y las nuestras con
    from=<nuestro id>; mirar solo requestedPlayers, como hace
    find_existing_offer en live_bid_executor, puede confundir una
    oferta entrante con una puja propia.
    """

    own_user_id = (
        get_own_user_id(
            snapshot
        )
    )

    if own_user_id is None:
        return None

    ofertas = (
        (
            snapshot.get(
                "market",
                {},
            )
            or {}
        ).get(
            "offers",
            [],
        )
        or []
    )

    for oferta in ofertas:

        origen = oferta.get(
            "from"
        )

        origen_id = (
            origen.get("id")
            if isinstance(origen, dict)
            else origen
        )

        try:
            origen_id = (
                int(origen_id)
                if origen_id is not None
                else None
            )

        except (TypeError, ValueError):
            origen_id = None

        if origen_id != own_user_id:
            continue

        estado = str(
            oferta.get(
                "status",
                "",
            )
        ).lower()

        if (
            estado
            and
            estado not in ACTIVE_OFFER_STATUS
        ):
            continue

        for solicitado in (
            oferta.get(
                "requestedPlayers",
                [],
            )
            or []
        ):

            solicitado_id = (
                solicitado.get("id")
                if isinstance(solicitado, dict)
                else solicitado
            )

            try:
                solicitado_id = int(solicitado_id)

            except (TypeError, ValueError):
                continue

            if solicitado_id == int(player_id):
                return oferta

    return None


def refresh_snapshot_for_write_revalidation() -> tuple[str, dict]:
    """
    Read-before-write obligatorio para operaciones delicadas.

    Refresca Biwenger y carga un snapshot nuevo justo antes
    de decidir si se permite la escritura.
    """
    collect_league_snapshot()

    snapshot_file = get_latest_snapshot()
    snapshot = load_snapshot(
        snapshot_file
    )

    return (
        snapshot_file,
        snapshot,
    )


def build_noop_result(
    decision: dict,
    status: str,
    reason: str,
    success: bool = True,
) -> dict:

    return {
        "action":
            decision.get(
                "action"
            ),

        "status":
            status,

        "reason":
            reason,

        "write_performed":
            False,

        "success":
            success,

        "http_status":
            None,

        "response":
            None,
    }


def validate_temporal_write_gate(
    decision: dict,
) -> dict | None:
    """
    Segunda barrera independiente del Orchestrator.

    Si por un bug llegase una decision ejecutable durante
    ROUND_LOCKED o ROUND_TRANSITION_LOCK, el executor se
    niega a escribir.

    En HARD_SAFETY solo se permiten acciones destinadas a:
    - generar liquidez;
    - recuperar saldo;
    - guardar el XI.
    """

    gate = (
        decision.get(
            "temporal_gate",
            {},
        )
        or {}
    )

    action = (
        decision.get(
            "action"
        )
    )

    phase = str(
        gate.get(
            "phase",
            "UNKNOWN",
        )
    )

    if gate.get(
        "operations_locked",
        False,
    ):

        return build_noop_result(
            decision=
                decision,

            status=
                "TEMPORAL_LOCK",

            reason=(
                f"Escritura bloqueada por fase temporal "
                f"{phase}."
            ),

            success=
                True,
        )

    if (
        gate.get(
            "hard_safety_mode",
            False,
        )
        and
        action
        not in HARD_SAFETY_ALLOWED_ACTIONS
    ):

        return build_noop_result(
            decision=
                decision,

            status=
                "HARD_SAFETY_BLOCK",

            reason=(
                f"La accion {action} no esta autorizada "
                "durante HARD_SAFETY."
            ),

            success=
                True,
        )

    return None


def execute_autopilot_decision(
    decision: dict,
    execute: bool = False,
) -> dict:
    """
    Ejecuta como maximo UNA escritura real.

    Acciones LIVE soportadas:
    - LIST_FOR_LIQUIDITY
    - ACCEPT_RECOVERY_OFFER
    - ACCEPT_CLUSTER_BEFORE_EXPIRY
    - REROLL_COMPUTER_OFFER
    - RENEW_MARKET_LISTING
    - BUY_SPECULATION
    - SAVE_LINEUP

    El flujo Franchise existente permanece fuera hasta
    integrarlo explicitamente.
    """

    action = (
        decision.get(
            "action"
        )
    )

    # --------------------------------------------------------
    # BARRERA TEMPORAL INDEPENDIENTE
    # --------------------------------------------------------

    temporal_block = (
        validate_temporal_write_gate(
            decision
        )
    )

    if temporal_block is not None:

        return temporal_block

    # --------------------------------------------------------
    # DECISION NO EJECUTABLE
    # --------------------------------------------------------

    if not decision.get(
        "executable",
        False,
    ):

        return build_noop_result(
            decision=
                decision,

            status=
                "NOT_EXECUTABLE",

            reason=(
                "La decision global no requiere "
                "una escritura."
            ),
        )

    # --------------------------------------------------------
    # OBSERVER
    # --------------------------------------------------------

    if not execute:

        return build_noop_result(
            decision=
                decision,

            status=
                "DRY_RUN",

            reason=(
                "Observer: no se ha modificado Biwenger."
            ),
        )

    # ========================================================
    # PUBLICAR PARA LIQUIDEZ
    # ========================================================

    if action == "LIST_FOR_LIQUIDITY":

        player = (
            (
                decision.get(
                    "data",
                    {},
                )
                or {}
            )
            .get(
                "player"
            )
        )

        if not player:

            return {
                "action":
                    action,

                "status":
                    "INVALID_DECISION",

                "reason":
                    "Falta el jugador a publicar.",

                "write_performed":
                    False,

                "success":
                    False,

                "http_status":
                    None,

                "response":
                    None,
            }

        player_id = int(
            player[
                "id"
            ]
        )

        price = int(
            player[
                "listing_price"
            ]
        )

        if price <= 0:

            return {
                "action":
                    action,

                "status":
                    "INVALID_PRICE",

                "reason":
                    "El precio de publicacion no es valido.",

                "write_performed":
                    False,

                "success":
                    False,

                "http_status":
                    None,

                "response":
                    None,
            }

        writer = (
            BiwengerWriteClient()
        )

        result = (
            writer.list_player_for_sale(
                player_id=
                    player_id,

                price=
                    price,

                execute=
                    True,
            )
        )

        return {
            "action":
                action,

            "status":
                (
                    "LISTED"
                    if result.get(
                        "success"
                    )
                    else "FAILED"
                ),

            "reason":
                (
                    f"Publicacion de "
                    f"{player.get('name')}."
                ),

            "write_performed":
                True,

            "success":
                bool(
                    result.get(
                        "success",
                        False,
                    )
                ),

            "http_status":
                result.get(
                    "http_status"
                ),

            "response":
                result.get(
                    "response"
                ),

            "player":
                player,
        }

    # ========================================================
    # ACEPTAR OFERTA PARA SOLVENCIA
    # ========================================================

    if action == "ACCEPT_RECOVERY_OFFER":

        offer = (
            (
                decision.get(
                    "data",
                    {},
                )
                or {}
            )
            .get(
                "offer"
            )
        )

        if not offer:

            return {
                "action":
                    action,

                "status":
                    "INVALID_DECISION",

                "reason":
                    "Falta la oferta de recuperacion.",

                "write_performed":
                    False,

                "success":
                    False,

                "http_status":
                    None,

                "response":
                    None,
            }

        if (
            offer.get(
                "protection"
            )
            == "NEVER_AUTO_SELL"
        ):

            return {
                "action":
                    action,

                "status":
                    "BLOCKED_PROTECTED_PLAYER",

                "reason": (
                    "La oferta pertenece a un jugador "
                    "NEVER_AUTO_SELL."
                ),

                "write_performed":
                    False,

                "success":
                    False,

                "http_status":
                    None,

                "response":
                    None,
            }

        offer_id = (
            offer.get(
                "offer_id"
            )
        )

        if offer_id is None:

            return {
                "action":
                    action,

                "status":
                    "INVALID_OFFER_ID",

                "reason":
                    "La oferta no tiene offer_id.",

                "write_performed":
                    False,

                "success":
                    False,

                "http_status":
                    None,

                "response":
                    None,
            }

        writer = (
            BiwengerWriteClient()
        )

        result = (
            writer.accept_offer(
                offer_id=
                    int(
                        offer_id
                    ),

                execute=
                    True,
            )
        )

        return {
            "action":
                action,

            "status":
                (
                    "OFFER_ACCEPTED"
                    if result.get(
                        "success"
                    )
                    else "FAILED"
                ),

            "reason": (
                "Oferta aceptada para "
                f"{offer.get('player_name')}."
            ),

            "write_performed":
                True,

            "success":
                bool(
                    result.get(
                        "success",
                        False,
                    )
                ),

            "http_status":
                result.get(
                    "http_status"
                ),

            "response":
                result.get(
                    "response"
                ),

            "offer":
                offer,
        }

    # ========================================================
    # ACCEPT BEFORE EXPIRY - LIVE CONTROLADO
    # ========================================================

    if action == ACCEPT_EXPIRY_ACTION:

        data = (
            decision.get(
                "data",
                {},
            )
            or {}
        )

        requested_cluster = (
            data.get(
                "cluster",
                {},
            )
            or {}
        )

        requested_offer_ids = (
            requested_cluster.get(
                "offer_ids",
                [],
            )
            or []
        )

        if not requested_offer_ids:

            return build_noop_result(
                decision=decision,
                status="INVALID_EXPIRY_CLUSTER",
                reason=(
                    "Aceptacion bloqueada: la decision no contiene "
                    "offer_ids del cluster."
                ),
                success=False,
            )

        # ----------------------------------------------------
        # READ-BEFORE-WRITE
        # ----------------------------------------------------

        try:

            (
                fresh_snapshot_file,
                fresh_snapshot,
            ) = (
                refresh_snapshot_for_write_revalidation()
            )

        except Exception as error:

            return build_noop_result(
                decision=decision,
                status="ACCEPT_REVALIDATION_REFRESH_FAILED",
                reason=(
                    "No se pudo obtener un snapshot fresco antes "
                    f"de aceptar: {type(error).__name__}: {error}"
                ),
                success=False,
            )

        selection = (
            select_emergency_accept_offer(
                snapshot=
                    fresh_snapshot,

                offer_ids=
                    requested_offer_ids,
            )
        )

        if not selection.get(
            "ready",
            False,
        ):

            return {
                **build_noop_result(
                    decision=decision,
                    status=selection.get(
                        "status",
                        "ACCEPT_BLOCKED",
                    ),
                    reason=selection.get(
                        "reason",
                        "Aceptacion bloqueada por Safety Gate.",
                    ),
                    success=True,
                ),

                "revalidation_snapshot":
                    fresh_snapshot_file,

                "selection":
                    selection,
            }

        selected = (
            selection.get(
                "selected",
                {},
            )
            or {}
        )

        offer_decision = (
            selected.get(
                "offer_decision",
                {},
            )
            or {}
        )

        # Barrera explicita adicional: nunca vendemos protegidos.
        if (
            offer_decision.get(
                "decision"
            )
            == "NEVER_SELL"
            or
            offer_decision.get(
                "protection"
            )
            == "NEVER_AUTO_SELL"
        ):

            return {
                **build_noop_result(
                    decision=decision,
                    status="BLOCKED_PROTECTED_PLAYER",
                    reason=(
                        "Accept-Before-Expiry bloqueado: "
                        "el selector ha devuelto un jugador protegido."
                    ),
                    success=False,
                ),

                "revalidation_snapshot":
                    fresh_snapshot_file,

                "selection":
                    selection,
            }

        offer_id = (
            selected.get(
                "offer_id"
            )
        )

        player_id = (
            selected.get(
                "player_id"
            )
        )

        if (
            offer_id is None
            or
            player_id is None
        ):

            return {
                **build_noop_result(
                    decision=decision,
                    status="INVALID_SELECTED_OFFER",
                    reason=(
                        "Accept-Before-Expiry bloqueado: "
                        "la oferta seleccionada no es valida."
                    ),
                    success=False,
                ),

                "revalidation_snapshot":
                    fresh_snapshot_file,

                "selection":
                    selection,
            }

        # ----------------------------------------------------
        # UNICA ESCRITURA REAL DEL CICLO
        # ----------------------------------------------------

        writer = (
            BiwengerWriteClient()
        )

        result = (
            writer.accept_offer(
                offer_id=
                    int(
                        offer_id
                    ),

                execute=
                    True,
            )
        )

        success = bool(
            result.get(
                "success",
                False,
            )
        )

        return {
            "action":
                action,

            "status":
                (
                    "EXPIRY_OFFER_ACCEPTED"
                    if success
                    else "FAILED"
                ),

            "reason":
                (
                    f"Oferta de {selected.get('player_name')} aceptada "
                    "tras revalidacion fresca de solvencia. "
                    "No se ejecutara otra venta en este ciclo."
                    if success
                    else
                    "Biwenger no confirmo la aceptacion de la oferta."
                ),

            "write_performed":
                True,

            "success":
                success,

            "http_status":
                result.get(
                    "http_status"
                ),

            "response":
                result.get(
                    "response"
                ),

            "offer":
                selected,

            "player_id":
                int(
                    player_id
                ),

            "revalidation_snapshot":
                fresh_snapshot_file,

            "selection":
                selection,
        }

    # ========================================================
    # REROLL COMPUTER OFFER
    # ========================================================

    if action == REROLL_ACTION:

        data = (
            decision.get(
                "data",
                {},
            )
            or {}
        )

        requested_offer = (
            data.get(
                "offer",
                {},
            )
            or {}
        )

        offer_id = (
            requested_offer.get(
                "offer_id"
            )
        )

        if offer_id is None:

            return build_noop_result(
                decision=decision,
                status="INVALID_OFFER_ID",
                reason=(
                    "Reroll bloqueado: la decision no contiene "
                    "un offer_id valido."
                ),
                success=False,
            )

        # ----------------------------------------------------
        # READ-BEFORE-WRITE
        # ----------------------------------------------------

        try:

            (
                fresh_snapshot_file,
                fresh_snapshot,
            ) = (
                refresh_snapshot_for_write_revalidation()
            )

        except Exception as error:

            return build_noop_result(
                decision=decision,
                status="REVALIDATION_REFRESH_FAILED",
                reason=(
                    "No se pudo obtener un snapshot fresco antes "
                    f"del reroll: {type(error).__name__}: {error}"
                ),
                success=False,
            )

        validation = (
            revalidate_reroll_offer(
                snapshot=
                    fresh_snapshot,

                offer_id=
                    int(
                        offer_id
                    ),
            )
        )

        if not validation.get(
            "authorized",
            False,
        ):

            return {
                **build_noop_result(
                    decision=decision,
                    status=validation.get(
                        "status",
                        "REROLL_BLOCKED",
                    ),
                    reason=validation.get(
                        "reason",
                        "Reroll bloqueado por Safety Gate.",
                    ),
                    success=True,
                ),

                "revalidation_snapshot":
                    fresh_snapshot_file,

                "revalidation":
                    validation,
            }

        fresh_offer = (
            validation.get(
                "offer",
                {},
            )
            or {}
        )

        player_ids = (
            fresh_offer.get(
                "player_ids",
                [],
            )
            or []
        )

        if len(player_ids) != 1:

            return {
                **build_noop_result(
                    decision=decision,
                    status="INVALID_REROLL_PLAYER",
                    reason=(
                        "Reroll bloqueado: la oferta fresca no "
                        "contiene exactamente un jugador."
                    ),
                    success=False,
                ),

                "revalidation_snapshot":
                    fresh_snapshot_file,
            }

        player_id = int(
            player_ids[
                0
            ]
        )

        # ----------------------------------------------------
        # UNICA ESCRITURA REAL DEL CICLO
        # ----------------------------------------------------

        writer = (
            BiwengerWriteClient()
        )

        result = (
            writer.reject_offer(
                offer_id=
                    int(
                        offer_id
                    ),

                execute=
                    True,
            )
        )

        success = bool(
            result.get(
                "success",
                False,
            )
        )

        if success:

            record_reroll(
                player_id=
                    player_id,

                offer_id=
                    int(
                        offer_id
                    ),

                # Sin el importe, best_offer_seen nunca llega al
                # disco y el motor no recuerda lo que rechazo.
                amount=
                    fresh_offer.get(
                        "amount"
                    ),
            )

        return {
            "action":
                action,

            "status":
                (
                    "OFFER_REROLLED"
                    if success
                    else "FAILED"
                ),

            "reason":
                (
                    "Oferta Computer rechazada tras revalidacion "
                    "fresca. El jugador permanece publicado y "
                    "esperara un nuevo ciclo Computer."
                    if success
                    else
                    "Biwenger no confirmo el rechazo de la oferta."
                ),

            "write_performed":
                True,

            "success":
                success,

            "http_status":
                result.get(
                    "http_status"
                ),

            "response":
                result.get(
                    "response"
                ),

            "offer":
                fresh_offer,

            "player_id":
                player_id,

            "revalidation_snapshot":
                fresh_snapshot_file,

            "revalidation":
                validation,
        }

    # ========================================================
    # RENOVAR PUBLICACION DE MERCADO
    # ========================================================

    if action == RENEW_LISTING_ACTION:

        data = (
            decision.get(
                "data",
                {},
            )
            or {}
        )

        requested = (
            data.get(
                "listing",
                {},
            )
            or {}
        )

        player_id = (
            requested.get(
                "player_id"
            )
        )

        if player_id is None:

            return build_noop_result(
                decision=decision,
                status="INVALID_LISTING_PLAYER",
                reason="Renovacion bloqueada: falta player_id.",
                success=False,
            )

        try:
            (
                fresh_snapshot_file,
                fresh_snapshot,
            ) = refresh_snapshot_for_write_revalidation()

        except Exception as error:

            return build_noop_result(
                decision=decision,
                status="RENEW_REVALIDATION_REFRESH_FAILED",
                reason=(
                    "No se pudo refrescar Biwenger antes de renovar: "
                    f"{type(error).__name__}: {error}"
                ),
                success=False,
            )

        lifecycle = (
            build_market_listing_lifecycle_board(
                fresh_snapshot
            )
        )

        fresh_listing = next(
            (
                item
                for item in lifecycle.get(
                    "renew_required",
                    [],
                )
                if int(
                    item.get(
                        "player_id",
                        0,
                    )
                    or 0
                )
                == int(
                    player_id
                )
            ),
            None,
        )

        if fresh_listing is None:

            return {
                **build_noop_result(
                    decision=decision,
                    status="RENEW_NO_LONGER_REQUIRED",
                    reason=(
                        "La publicacion ya no necesita renovacion "
                        "en el snapshot fresco."
                    ),
                    success=True,
                ),
                "revalidation_snapshot":
                    fresh_snapshot_file,
            }

        listed_price = int(
            fresh_listing.get(
                "listed_price",
                0,
            )
            or 0
        )

        if listed_price <= 0:

            return {
                **build_noop_result(
                    decision=decision,
                    status="INVALID_LISTING_PRICE",
                    reason=(
                        "Renovacion bloqueada: precio de publicacion invalido."
                    ),
                    success=False,
                ),
                "revalidation_snapshot":
                    fresh_snapshot_file,
            }

        # ----------------------------------------------------
        # SUELO DE PRECIO
        # ----------------------------------------------------
        #
        # Observado en produccion:
        #
        #   2026-08-11  Alvaro Fidalgo
        #               publicado 1.183.812 / valor 1.060.000
        #               -> HTTP 204, renovacion OK
        #
        #   2026-08-16  Yeray
        #               publicado 1.941.001 / valor 1.950.000
        #               -> HTTP 400, renovacion rechazada
        #
        # La unica diferencia medible es que Yeray estaba
        # publicado POR DEBAJO de su valor de mercado: su precio
        # habia subido despues de publicarlo.
        #
        # Es una hipotesis con dos observaciones, no una certeza.
        # Por eso la correccion es conservadora: subimos el
        # precio al valor de mercado cuando se ha quedado corto.
        # Nunca lo bajamos. En el peor caso la renovacion vuelve
        # a fallar y el backoff la aparta; en el mejor, deja de
        # fallar. Pedir mas dinero nunca nos perjudica.
        market_value = int(
            (
                (
                    fresh_listing.get(
                        "listing",
                        {},
                    )
                    or {}
                ).get(
                    "player",
                    {},
                )
                or {}
            ).get(
                "price",
                0,
            )
            or 0
        )

        renewal_pricing = (
            resolve_renewal_price(
                listed_price=
                    listed_price,

                market_value=
                    market_value,
            )
        )

        renewal_price = (
            renewal_pricing[
                "renewal_price"
            ]
        )

        price_raised = (
            renewal_pricing[
                "price_raised"
            ]
        )

        writer = BiwengerWriteClient()

        result = (
            writer.list_player_for_sale(
                player_id=
                    int(
                        player_id
                    ),

                price=
                    renewal_price,

                execute=True,
            )
        )

        success = bool(
            result.get(
                "success",
                False,
            )
        )

        return {
            "action":
                action,

            "status":
                (
                    "LISTING_RENEWED"
                    if success
                    else "FAILED"
                ),

            "reason":
                (
                    (
                        "Publicacion renovada usando POST /market."
                        if success
                        else
                        "Biwenger no confirmo la renovacion."
                    )
                    + (
                        f" Precio subido de {listed_price} a "
                        f"{renewal_price} para no publicar por "
                        "debajo del valor de mercado."
                        if price_raised
                        else ""
                    )
                ),

            "write_performed":
                True,

            "success":
                success,

            "http_status":
                result.get(
                    "http_status"
                ),

            "response":
                result.get(
                    "response"
                ),

            "player_id":
                int(
                    player_id
                ),

            "listed_price":
                listed_price,

            "renewal_price":
                renewal_price,

            "market_value":
                market_value,

            "price_raised_to_market_value":
                price_raised,

            "revalidation_snapshot":
                fresh_snapshot_file,

            "listing":
                fresh_listing,
        }

    # ========================================================
    # COMPRA ESPECULATIVA - LIVE CONTROLADO
    # ========================================================

    if action == SPECULATION_BUY_ACTION:

        data = (
            decision.get(
                "data",
                {},
            )
            or {}
        )

        requested_player = (
            data.get(
                "player",
                {},
            )
            or {}
        )

        requested_player_id = (
            requested_player.get(
                "id"
            )
        )

        if requested_player_id is None:

            return build_noop_result(
                decision=decision,
                status="INVALID_SPECULATION_PLAYER",
                reason=(
                    "Compra especulativa bloqueada: "
                    "falta player_id."
                ),
                success=False,
            )

        # ----------------------------------------------------
        # READ-BEFORE-WRITE
        # ----------------------------------------------------

        try:

            (
                fresh_snapshot_file,
                fresh_snapshot,
            ) = refresh_snapshot_for_write_revalidation()

        except Exception as error:

            return build_noop_result(
                decision=decision,
                status="SPECULATION_REVALIDATION_REFRESH_FAILED",
                reason=(
                    "No se pudo obtener snapshot fresco antes "
                    f"de pujar: {type(error).__name__}: {error}"
                ),
                success=False,
            )

        fresh_board = (
            build_speculation_board(
                fresh_snapshot
            )
        )

        fresh_budget = (
            fresh_board.get(
                "budget",
                {},
            )
            or {}
        )

        # Saldo negativo.
        #
        # Esta rama exigia saldo positivo y punto, aunque el motor
        # de presupuesto autorizase la operacion. Era un bloqueo
        # de mas: en Biwenger se puede operar en negativo y sanear
        # antes del inicio de jornada, y el juego mismo dice hasta
        # donde -maximumBid-.
        #
        # "balance >= 0" no es una comprobacion de seguridad, es
        # una aproximacion tosca a una. La de verdad la hace
        # calculate_speculation_budget, que con saldo negativo
        # exige SOLVENCY_GUARANTEE cubierta, ventana de deuda
        # abierta, permiso temporal vigente y margen dentro de
        # MAX_SAFE_DEBT. Cuatro condiciones en vez de una, y todas
        # miran si podremos pagar, que es lo que importaba.
        #
        # Asi que en vez de vetar el saldo negativo, se exige que
        # el motor lo haya autorizado explicitamente.
        fresh_balance = int(
            fresh_budget.get(
                "balance",
                0,
            )
            or 0
        )

        fresh_mode = str(
            fresh_budget.get(
                "mode",
                "",
            )
            or ""
        )

        if (
            fresh_balance < 0
            and fresh_mode not in {"DEBT", "CASH_AND_DEBT"}
        ):

            return {
                **build_noop_result(
                    decision=decision,
                    status="SPECULATION_NEGATIVE_BALANCE_BLOCK",
                    reason=(
                        "Saldo negativo y el presupuesto no viene "
                        "de una via de deuda autorizada "
                        f"(modo={fresh_mode or 'desconocido'})."
                    ),
                    success=True,
                ),
                "revalidation_snapshot":
                    fresh_snapshot_file,
                "speculation":
                    fresh_board,
            }

        if not fresh_budget.get(
            "enabled",
            False,
        ):

            return {
                **build_noop_result(
                    decision=decision,
                    status="SPECULATION_BUDGET_DISABLED",
                    reason=(
                        fresh_budget.get(
                            "reason",
                            "El presupuesto especulativo ya no esta habilitado.",
                        )
                    ),
                    success=True,
                ),
                "revalidation_snapshot":
                    fresh_snapshot_file,
                "speculation":
                    fresh_board,
            }

        fresh_player = next(
            (
                player
                for player in (
                    fresh_board.get(
                        "executable_buys",
                        [],
                    )
                    or []
                )
                if int(
                    player.get(
                        "id",
                        0,
                    )
                    or 0
                )
                == int(
                    requested_player_id
                )
            ),
            None,
        )

        if fresh_player is None:

            return {
                **build_noop_result(
                    decision=decision,
                    status="SPECULATION_NO_LONGER_EXECUTABLE",
                    reason=(
                        "El jugador ya no figura entre los "
                        "executable_buys del snapshot fresco."
                    ),
                    success=True,
                ),
                "revalidation_snapshot":
                    fresh_snapshot_file,
                "speculation":
                    fresh_board,
            }

        if fresh_player.get(
            "ownership_state"
        ) != "EN_MERCADO":

            return {
                **build_noop_result(
                    decision=decision,
                    status="SPECULATION_PLAYER_NOT_ON_MARKET",
                    reason=(
                        "El objetivo especulativo ya no esta "
                        "disponible en el mercado."
                    ),
                    success=True,
                ),
                "revalidation_snapshot":
                    fresh_snapshot_file,
                "speculation":
                    fresh_board,
            }

        # DEDUPLICACION: una puja viva por este jugador significa
        # que ya comprometimos ese dinero. Volver a pujar duplica
        # el compromiso sin que el saldo lo refleje, porque la
        # puja no se resuelve hasta el cierre de mercado.
        puja_viva = (
            find_own_pending_bid(
                snapshot=
                    fresh_snapshot,

                player_id=
                    int(
                        requested_player_id
                    ),
            )
        )

        if puja_viva is not None:

            return {
                **build_noop_result(
                    decision=decision,
                    status="SPECULATION_BID_ALREADY_PENDING",
                    reason=(
                        f"Ya existe una puja nuestra viva por "
                        f"este jugador "
                        f"(oferta {puja_viva.get('id')}, "
                        f"{puja_viva.get('amount')} EUR). "
                        f"No se duplica."
                    ),
                    success=True,
                ),
                "revalidation_snapshot":
                    fresh_snapshot_file,
                "speculation":
                    fresh_board,
                "existing_bid":
                    puja_viva,
            }

        market_sales = (
            fresh_snapshot.get(
                "market",
                {},
            ).get(
                "sales",
                [],
            )
            or []
        )

        fresh_sale = next(
            (
                sale
                for sale in market_sales
                if int(
                    (
                        sale.get(
                            "player",
                            {},
                        )
                        or {}
                    ).get(
                        "id",
                        0,
                    )
                    or 0
                )
                == int(
                    requested_player_id
                )
            ),
            None,
        )

        if fresh_sale is None:

            return {
                **build_noop_result(
                    decision=decision,
                    status="SPECULATION_MARKET_SALE_NOT_FOUND",
                    reason=(
                        "El jugador parece estar en mercado, "
                        "pero no se encontro su venta fresca."
                    ),
                    success=False,
                ),
                "revalidation_snapshot":
                    fresh_snapshot_file,
            }

        bid_amount = int(
            fresh_player.get(
                "price",
                0,
            )
            or 0
        )

        if bid_amount <= 0:

            return {
                **build_noop_result(
                    decision=decision,
                    status="SPECULATION_INVALID_BID_AMOUNT",
                    reason=(
                        "El precio fresco del jugador no es valido."
                    ),
                    success=False,
                ),
                "revalidation_snapshot":
                    fresh_snapshot_file,
            }

        single_limit = int(
            fresh_budget.get(
                "single_operation_limit",
                0,
            )
            or 0
        )

        total_budget = int(
            fresh_budget.get(
                "total_budget",
                0,
            )
            or 0
        )

        # Lo que queda despues de descontar las pujas vivas de
        # ciclos anteriores. Comparar contra total_budget dejaba
        # pasar una puja nueva cada 30 minutos sobre el mismo
        # presupuesto entero.
        available_budget = int(
            fresh_budget.get(
                "available_budget",
                total_budget,
            )
            or 0
        )

        if (
            bid_amount > single_limit
            or
            bid_amount > total_budget
            or
            bid_amount > available_budget
        ):

            return {
                **build_noop_result(
                    decision=decision,
                    status="SPECULATION_BUDGET_CHANGED",
                    reason=(
                        "El precio fresco ya no cabe dentro "
                        "del presupuesto especulativo."
                    ),
                    success=True,
                ),
                "revalidation_snapshot":
                    fresh_snapshot_file,
                "speculation":
                    fresh_board,
            }

        seller = (
            fresh_sale.get(
                "user",
                {},
            )
            or {}
        )

        seller_user_id = (
            seller.get(
                "id"
            )
        )

        # Computer / mercado general puede no tener seller id.
        if seller_user_id is not None:

            try:
                seller_user_id = int(
                    seller_user_id
                )
            except (
                TypeError,
                ValueError,
            ):
                seller_user_id = None

        writer = (
            BiwengerWriteClient()
        )

        result = (
            writer.place_bid(
                player_id=
                    int(
                        requested_player_id
                    ),

                amount=
                    int(
                        bid_amount
                    ),

                seller_user_id=
                    seller_user_id,

                execute=
                    True,
            )
        )

        success = bool(
            result.get(
                "success",
                False,
            )
        )

        return {
            "action":
                action,

            "status":
                (
                    "SPECULATION_BID_PLACED"
                    if success
                    else "FAILED"
                ),

            "reason":
                (
                    f"Puja especulativa por "
                    f"{fresh_player.get('name')} tras "
                    "revalidacion fresca."
                    if success
                    else
                    "Biwenger no confirmo la puja especulativa."
                ),

            "write_performed":
                True,

            "success":
                success,

            "http_status":
                result.get(
                    "http_status"
                ),

            "response":
                result.get(
                    "response"
                ),

            "player":
                fresh_player,

            "player_id":
                int(
                    requested_player_id
                ),

            "bid_amount":
                int(
                    bid_amount
                ),

            "seller_user_id":
                seller_user_id,

            "revalidation_snapshot":
                fresh_snapshot_file,

            "speculation":
                fresh_board,
        }

    # ========================================================
    # GUARDAR XI
    # ========================================================

    if action == "SAVE_LINEUP":

        monitor = (
            (
                decision.get(
                    "data",
                    {},
                )
                or {}
            )
            .get(
                "lineup_monitor",
                {},
            )
            or {}
        )

        lineup = (
            monitor.get(
                "lineup",
                {},
            )
            or {}
        )

        selected = (
            lineup.get(
                "selected",
                [],
            )
            or []
        )

        if len(
            selected
        ) != 11:

            return {
                "action":
                    action,

                "status":
                    "BLOCKED_INCOMPLETE_LINEUP",

                "reason":
                    "El XI no contiene exactamente 11 jugadores.",

                "write_performed":
                    False,

                "success":
                    False,

                "http_status":
                    None,

                "response":
                    None,
            }

        if int(
            lineup.get(
                "playable_count",
                0,
            )
            or 0
        ) < 11:

            return {
                "action":
                    action,

                "status":
                    "BLOCKED_INVALID_LINEUP",

                "reason": (
                    "El XI contiene 11 nombres, pero no "
                    "11 jugadores validos para la jornada."
                ),

                "write_performed":
                    False,

                "success":
                    False,

                "http_status":
                    None,

                "response":
                    None,
            }

        player_ids = [
            int(
                player[
                    "id"
                ]
            )

            for player in selected
        ]

        formation = (
            lineup.get(
                "formation_name"
            )
        )

        if not formation:

            return {
                "action":
                    action,

                "status":
                    "INVALID_FORMATION",

                "reason":
                    "La formacion no esta disponible.",

                "write_performed":
                    False,

                "success":
                    False,

                "http_status":
                    None,

                "response":
                    None,
            }

        writer = (
            BiwengerWriteClient()
        )

        result = (
            writer.save_lineup(
                player_ids=
                    player_ids,

                formation=
                    formation,

                reserve_ids=
                    [],

                execute=
                    True,
            )
        )

        success = bool(
            result.get(
                "success",
                False,
            )
        )

        if success:

            save_lineup_monitor_state(
                lineup
            )

        return {
            "action":
                action,

            "status":
                (
                    "LINEUP_SAVED"
                    if success
                    else "FAILED"
                ),

            "reason":
                "Actualizacion del XI recomendado.",

            "write_performed":
                True,

            "success":
                success,

            "http_status":
                result.get(
                    "http_status"
                ),

            "response":
                result.get(
                    "response"
                ),

            "formation":
                formation,

            "player_ids":
                player_ids,
        }

    return {
        "action":
            action,

        "status":
            "UNSUPPORTED_AUTOPILOT_ACTION",

        "reason": (
            "Esta accion aun no tiene executor LIVE "
            "dentro del Autopilot v3."
        ),

        "write_performed":
            False,

        "success":
            False,

        "http_status":
            None,

        "response":
            None,
    }
