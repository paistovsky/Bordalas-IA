from __future__ import annotations

from collections import defaultdict

from src.analysis.lineup_engine import (
    FORMATIONS,
    prepare_players,
)

# Quien se puede vender y quien no lo decide el guardarrail, que
# es el unico sitio donde vive esa regla. Aqui solo se obedece.
from src.analysis.position_guardrail import (
    build_position_guardrail,
)


BEAM_WIDTH_PER_TIER = 192
DEFAULT_TRADING_MAX_LINEUP_LOSS_PERCENT = 5.0


def safe_int(value, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def _offer_source_id(offer: dict, player_ids: list[int]) -> str:
    offer_id = offer.get("offer_id")
    if offer_id is not None:
        return f"COMPUTER:{offer_id}"
    return "COMPUTER:" + ",".join(str(value) for value in player_ids)


def build_recovery_sources(
    incoming: dict,
    expected: dict,
) -> list[dict]:
    """
    Normaliza toda la liquidez candidata ya filtrada por Solvency.

    - COMPUTER_OFFER entra por su importe real (secured).
    - EXPECTED_LISTING entra por el valor ya haircutted calculado por
      calculate_expected_liquidity().

    La funcion NO suma todavia las fuentes: una combinacion puede ser
    incompatible porque vende el mismo jugador dos veces o rompe el XI.
    """

    sources: list[dict] = []

    for offer in incoming.get("offers", []) or []:
        amount = safe_int(offer.get("amount"))
        player_ids = sorted({
            safe_int(value)
            for value in (offer.get("player_ids", []) or [])
            if safe_int(value) > 0
        })

        if amount <= 0 or not player_ids:
            continue

        players = offer.get("players", []) or []
        names = [
            str(item.get("name") or item.get("id"))
            for item in players
            if isinstance(item, dict)
        ]
        if not names:
            names = [str(value) for value in player_ids]

        sources.append({
            "source_id": _offer_source_id(offer, player_ids),
            "kind": "COMPUTER_OFFER",
            "confidence": "SECURED",
            "amount": amount,
            "player_ids": player_ids,
            "player_names": names,
            "offer_id": offer.get("offer_id"),
            "hours_to_expiry": offer.get("hours_to_expiry"),
        })

    secured_player_ids = {
        player_id
        for source in sources
        if source["kind"] == "COMPUTER_OFFER"
        for player_id in source["player_ids"]
    }

    for player in expected.get("players", []) or []:
        player_id = safe_int(player.get("id"))
        amount = safe_int(player.get("expected_liquidity"))

        if player_id <= 0 or amount <= 0:
            continue

        # Defensa extra contra doble conteo. Normalmente
        # calculate_expected_liquidity() ya lo excluye.
        if player_id in secured_player_ids:
            continue

        sources.append({
            "source_id": f"LISTING:{player_id}",
            "kind": "EXPECTED_LISTING",
            "confidence": "HAIRCUTTED",
            "amount": amount,
            "player_ids": [player_id],
            "player_names": [str(player.get("name") or player_id)],
            "offer_id": None,
            "haircut": player.get("haircut"),
            "first_safe_cycle": player.get("first_safe_cycle"),
        })

    # Mas liquidez primero ayuda al beam search a encontrar pronto
    # carteras potentes. La seguridad la valida SIEMPRE el XI proyectado.
    sources.sort(
        key=lambda item: (
            -safe_int(item.get("amount")),
            0 if item.get("kind") == "COMPUTER_OFFER" else 1,
            item.get("source_id", ""),
        )
    )

    return sources


def _prepare_fast_roster(snapshot: dict) -> list[dict]:
    """
    Prepara UNA sola vez los jugadores que realmente cuentan para un XI
    seguro. Position Policy V1 usa posicion principal unica, por lo que la
    viabilidad de una formacion se puede resolver por conteo/top-N y no por
    una busqueda recursiva completa en cada combinacion de ventas.

    Esto conserva los mismos guardarrailes importantes del lineup_engine:
    lineup_eligible + automatic_lineup + lineup_score.
    """
    prepared = prepare_players(snapshot) or []
    roster: list[dict] = []

    for player in prepared:
        if not player.get("lineup_eligible", False):
            continue
        if not player.get("automatic_lineup", False):
            continue

        player_id = safe_int(player.get("id"))
        if player_id <= 0:
            continue

        positions = [
            safe_int(value)
            for value in (player.get("eligible_positions", []) or [])
            if safe_int(value) in {1, 2, 3, 4}
        ]
        if not positions:
            position = safe_int(player.get("position"))
            if position in {1, 2, 3, 4}:
                positions = [position]

        # En la politica actual la posicion efectiva es unica. Si en el
        # futuro cambia esa politica, conservar la primera posicion evita
        # dobles conteos y obliga a revisar conscientemente este fast-path.
        if not positions:
            continue

        roster.append({
            "id": player_id,
            "name": str(player.get("name") or player_id),
            "position": positions[0],
            "lineup_score": float(player.get("lineup_score", 0.0) or 0.0),
        })

    return roster


def _build_position_index(roster: list[dict]) -> dict[int, list[dict]]:
    result = {1: [], 2: [], 3: [], 4: []}
    for player in roster:
        position = safe_int(player.get("position"))
        if position in result:
            result[position].append(player)

    for position in result:
        result[position].sort(
            key=lambda item: (
                float(item.get("lineup_score", 0.0) or 0.0),
                safe_int(item.get("id")),
            ),
            reverse=True,
        )
    return result


def _project_lineup_fast(
    position_index: dict[int, list[dict]],
    removed_ids: set[int],
) -> dict:
    """
    Proyeccion exacta para la Position Policy V1 actual (una posicion por
    jugador). Devuelve el mejor XI SEGURO por filled y lineup_score entre
    todas las formaciones, sin invocar el buscador recursivo del lineup.

    Para Tier C nos interesa playable_count. Los jugadores warning no
    aumentan ese contador en build_lineup, por lo que trabajar solo con
    automatic_lineup reproduce la capacidad real de puntuar.
    """
    best: dict | None = None

    for formation_name, formation in FORMATIONS.items():
        selected: list[dict] = []
        shortages: dict[int, int] = {}
        score = 0.0

        for position, required in formation.items():
            available = [
                player
                for player in position_index.get(position, [])
                if safe_int(player.get("id")) not in removed_ids
            ]
            chosen = available[:safe_int(required)]
            selected.extend(chosen)
            score += sum(
                float(player.get("lineup_score", 0.0) or 0.0)
                for player in chosen
            )
            shortages[position] = max(safe_int(required) - len(chosen), 0)

        candidate = {
            "playable_count": len(selected),
            "missing": max(11 - len(selected), 0),
            "complete": len(selected) >= 11,
            "formation": formation_name,
            "shortages": shortages,
            "selected_ids": sorted(safe_int(item.get("id")) for item in selected),
            "lineup_score": round(score, 2),
        }

        if best is None or (
            candidate["playable_count"],
            candidate["lineup_score"],
        ) > (
            best["playable_count"],
            best["lineup_score"],
        ):
            best = candidate

    return best or {
        "playable_count": 0,
        "missing": 11,
        "complete": False,
        "formation": None,
        "shortages": {1: 1, 2: 3, 3: 3, 4: 1},
        "selected_ids": [],
        "lineup_score": 0.0,
    }


def _classify_lineup(
    *,
    current_starter_ids: set[int],
    removed_ids: set[int],
    simulation: dict,
) -> str:
    complete = bool(simulation.get("complete", False))
    playable_count = safe_int(simulation.get("playable_count"))
    starters_sold = bool(current_starter_ids & removed_ids)

    if complete and not starters_sold:
        return "A"
    if complete:
        return "B"
    if playable_count >= 10:
        return "C"
    return "D"


def _state_rank(state: dict) -> tuple:
    """
    Dentro de cada tier preferimos mas caja, menos titulares vendidos,
    menos jugadores vendidos y menor perdida de score.
    """
    return (
        safe_int(state.get("amount")),
        -safe_int(state.get("starters_sold")),
        -safe_int(state.get("sold_count")),
        -float(state.get("lineup_score_loss", 0.0) or 0.0),
    )


def _compact_state(state: dict) -> dict:
    return {
        "tier": state.get("tier"),
        "amount": safe_int(state.get("amount")),
        "secured_total": safe_int(state.get("secured_total")),
        "expected_total": safe_int(state.get("expected_total")),
        "source_ids": list(state.get("source_ids", [])),
        "offer_ids": [
            value for value in state.get("offer_ids", [])
            if value is not None
        ],
        "player_ids": sorted(state.get("removed_ids", set())),
        "player_names": list(state.get("player_names", [])),
        "sold_count": safe_int(state.get("sold_count")),
        "starters_sold": safe_int(state.get("starters_sold")),
        "playable_count": safe_int(state.get("playable_count")),
        "missing": safe_int(state.get("missing")),
        "lineup_complete": bool(state.get("lineup_complete", False)),
        "formation_after": state.get("formation_after"),
        "lineup_score_after": state.get("lineup_score_after"),
        "lineup_score_loss": state.get("lineup_score_loss"),
        "lineup_score_loss_percent": state.get("lineup_score_loss_percent"),
        "trading_safe": bool(state.get("trading_safe", False)),
        "sporting_tier": state.get("sporting_tier"),
        "sources": list(state.get("sources", [])),
    }


def build_safe_liquidity_portfolio(
    snapshot: dict,
    incoming: dict,
    expected: dict,
    *,
    beam_width_per_tier: int = BEAM_WIDTH_PER_TIER,
    trading_max_lineup_loss_percent: float = DEFAULT_TRADING_MAX_LINEUP_LOSS_PERCENT,
) -> dict:
    """
    V10.2.2 Fast Safe Debt Portfolio.

    Mantiene la politica V10.2.1 pero elimina el cuello de botella:
    NO vuelve a ejecutar build_lineup recursivo para cada combinacion.

    TIER A: liquidez sin vender ningun jugador del XI actual.
    TIER B: liquidez manteniendo XI completo 11/11 gracias al banquillo.
    TIER C: emergencia; permite 10/11. NO financia trading normal.

    Para Safe Debt normal solo se utiliza la mejor cartera A/B.
    """

    sources = build_recovery_sources(incoming, expected)
    roster = _prepare_fast_roster(snapshot)
    position_index = _build_position_index(roster)

    projection_cache: dict[frozenset[int], dict] = {}

    def project(removed_ids: set[int]) -> dict:
        key = frozenset(removed_ids)
        if key not in projection_cache:
            projection_cache[key] = _project_lineup_fast(
                position_index,
                removed_ids,
            )
        return projection_cache[key]

    current_lineup = project(set())
    current_starter_ids = set(current_lineup.get("selected_ids", []) or [])
    current_score = float(current_lineup.get("lineup_score", 0.0) or 0.0)

    # ==================================================
    # A QUIEN NO SE PUEDE TOCAR (20/08/2026)
    # ==================================================
    #
    # El dueño se encontro un Plan B que proponia vender a Jutgla
    # teniendo dos delanteros, y dijo lo que faltaba:
    #
    #     "El suelo tiene que ser para TITULARES."
    #
    # Este motor validaba una sola cosa: "¿sigue habiendo once?".
    # Y con un delantero se alinea un 5-4-1 perfectamente legal.
    # La formacion aguantaba; el equipo no.
    #
    # No se reescribe aqui la regla: se le pregunta al
    # guardarrail, que es donde vive y donde el dueño la ve. Si
    # llegan a existir dos versiones de "cuantos hacen falta",
    # acabaran diciendo cosas distintas -ya paso con una tercera
    # lista escondida en `sales_analyzer`-.
    #
    # SI EL GUARDARRAIL FALLA, NO SE PARALIZA
    #
    #     Sin bloqueados se sigue como antes. Un motor de deuda
    #     que no propone nada con la caja en rojo es peor que uno
    #     que propone de mas: al menos el segundo se puede
    #     revisar.

    try:
        guardarrail = build_position_guardrail(
            (snapshot or {}).get("my_team") or [],
            lineup_ids=current_starter_ids,
        )

        intocables = {
            safe_int(player_id)
            for player_id in (
                guardarrail.get("locked_ids") or []
            )
        }

    except Exception:
        intocables = set()

    base = {
        "tier": "A",
        "amount": 0,
        "secured_total": 0,
        "expected_total": 0,
        "source_ids": [],
        "offer_ids": [],
        "removed_ids": set(),
        "player_names": [],
        "sold_count": 0,
        "starters_sold": 0,
        "playable_count": safe_int(current_lineup.get("playable_count")),
        "missing": safe_int(current_lineup.get("missing")),
        "lineup_complete": bool(current_lineup.get("complete", False)),
        "formation_after": current_lineup.get("formation"),
        "lineup_score_after": current_score,
        "lineup_score_loss": 0.0,
        "lineup_score_loss_percent": 0.0,
        "trading_safe": True,
        "sporting_tier": "A",
        "sources": [],
    }

    states = [base]
    max_width = max(int(beam_width_per_tier), 16)

    for source in sources:
        expanded = list(states)
        source_player_ids = set(source["player_ids"])

        # Un intocable no entra en ninguna combinacion. Se corta
        # aqui, en la fuente, y no plan por plan: asi no hay forma
        # de que se cuele por una rama.
        if source_player_ids & intocables:
            continue

        for state in states:
            if state["removed_ids"] & source_player_ids:
                continue

            removed_ids = set(state["removed_ids"]) | source_player_ids
            simulation = project(removed_ids)
            tier = _classify_lineup(
                current_starter_ids=current_starter_ids,
                removed_ids=removed_ids,
                simulation=simulation,
            )

            # Vender mas jugadores nunca repara un XI que ya ha caido
            # por debajo de 10. D se poda inmediatamente.
            if tier == "D":
                continue

            score_after = float(simulation.get("lineup_score", 0.0) or 0.0)
            score_loss = max(current_score - score_after, 0.0)
            score_loss_percent = (
                (score_loss / current_score) * 100.0
                if current_score > 0
                else 0.0
            )
            trading_safe = bool(
                tier in {"A", "B"}
                and score_loss_percent <= float(trading_max_lineup_loss_percent)
            )
            sporting_tier = (
                "A"
                if tier == "A"
                else "B1"
                if tier == "B" and trading_safe
                else "B2"
                if tier == "B"
                else "C"
            )
            amount = state["amount"] + safe_int(source["amount"])
            secured = state["secured_total"]
            expected_total = state["expected_total"]

            if source["kind"] == "COMPUTER_OFFER":
                secured += safe_int(source["amount"])
            else:
                expected_total += safe_int(source["amount"])

            expanded.append({
                "tier": tier,
                "amount": amount,
                "secured_total": secured,
                "expected_total": expected_total,
                "source_ids": [*state["source_ids"], source["source_id"]],
                "offer_ids": [*state["offer_ids"], source.get("offer_id")],
                "removed_ids": removed_ids,
                "player_names": [*state["player_names"], *source["player_names"]],
                "sold_count": len(removed_ids),
                "starters_sold": len(current_starter_ids & removed_ids),
                "playable_count": safe_int(simulation.get("playable_count")),
                "missing": safe_int(simulation.get("missing")),
                "lineup_complete": bool(simulation.get("complete", False)),
                "formation_after": simulation.get("formation"),
                "lineup_score_after": round(score_after, 2),
                "lineup_score_loss": round(score_loss, 2),
                "lineup_score_loss_percent": round(score_loss_percent, 2),
                "trading_safe": trading_safe,
                "sporting_tier": sporting_tier,
                "sources": [*state["sources"], source],
            })

        # Dedup por conjunto de jugadores vendidos. Si dos caminos venden
        # los mismos jugadores, conservamos el que recupera mas caja.
        best_by_removed: dict[frozenset[int], dict] = {}
        for state in expanded:
            key = frozenset(state["removed_ids"])
            current = best_by_removed.get(key)
            if current is None or _state_rank(state) > _state_rank(current):
                best_by_removed[key] = state

        # V10.3: preservamos por separado B1 (XI completo con perdida
        # deportiva <= umbral) y B2 (XI completo pero demasiado caro
        # deportivamente). Asi el beam no descarta una cartera B1 valida
        # solo porque existan combinaciones B2 con mas caja bruta.
        buckets: dict[str, list[dict]] = defaultdict(list)
        for state in best_by_removed.values():
            sporting_tier = state.get("sporting_tier") or state.get("tier")
            buckets[str(sporting_tier)].append(state)

        states = []
        for sporting_tier in ("A", "B1", "B2", "C"):
            bucket = sorted(
                buckets.get(sporting_tier, []),
                key=_state_rank,
                reverse=True,
            )
            states.extend(bucket[:max_width])

    def best(predicate) -> dict:
        candidates = [state for state in states if predicate(state)]
        if not candidates:
            return _compact_state(base)
        return _compact_state(max(candidates, key=_state_rank))

    tier_a = best(lambda state: state["tier"] == "A")
    trading_safe = best(
        lambda state: state["tier"] in {"A", "B"}
        and bool(state.get("trading_safe", False))
    )
    tier_b = best(lambda state: state["tier"] in {"A", "B"})
    tier_c = best(lambda state: state["tier"] in {"A", "B", "C"})

    individually_blocked = []
    for source in sources:
        simulation = project(set(source["player_ids"]))
        tier = _classify_lineup(
            current_starter_ids=current_starter_ids,
            removed_ids=set(source["player_ids"]),
            simulation=simulation,
        )
        if tier not in {"A", "B"}:
            individually_blocked.append({
                **source,
                "tier": tier,
                "playable_count": safe_int(simulation.get("playable_count")),
                "missing": safe_int(simulation.get("missing")),
                "reason": (
                    "La fuente rompe el XI completo y no puede financiar "
                    "deuda especulativa normal."
                ),
            })

    selected_ids = set(tier_b["source_ids"])
    not_selected = [
        {
            **source,
            "reason": "No forma parte de la mejor cartera A/B conjunta.",
        }
        for source in sources
        if source["source_id"] not in selected_ids
    ]

    return {
        "version": "V10.3",
        "policy": "SAFE_DEBT_WITH_SPORTING_B1_FOR_TRADING",
        "current_lineup_complete": bool(current_lineup.get("complete", False)),
        "current_playable_count": safe_int(current_lineup.get("playable_count")),
        "current_formation": current_lineup.get("formation"),
        "current_lineup_score": round(current_score, 2),
        "current_starter_ids": sorted(current_starter_ids),
        "source_count": len(sources),
        "sources": sources,
        "gross_source_total": sum(safe_int(item["amount"]) for item in sources),
        "tier_a": tier_a,
        "trading_safe": trading_safe,
        "tier_b": tier_b,
        "tier_c": tier_c,
        "trading_max_lineup_loss_percent": float(trading_max_lineup_loss_percent),
        "trading_safe_total": safe_int(trading_safe["amount"]),
        "emergency_complete_total": safe_int(tier_b["amount"]),
        "emergency_ten_total": safe_int(tier_c["amount"]),
        # Compatibilidad V10.2.2: Solvency LIVE/legacy sigue viendo Tier B.
        # Market Trader V10.3 usa EXCLUSIVAMENTE trading_safe_total (B1).
        "usable_total": safe_int(tier_b["amount"]),
        "usable_secured_total": safe_int(tier_b["secured_total"]),
        "usable_expected_total": safe_int(tier_b["expected_total"]),
        "selected_source_ids": list(tier_b["source_ids"]),
        "selected_offer_ids": list(tier_b["offer_ids"]),
        "selected_player_ids": list(tier_b["player_ids"]),
        "selected_sources": list(tier_b["sources"]),
        "individually_blocked_by_lineup": individually_blocked,
        "not_selected_sources": not_selected,
        "search": {
            "method": "FAST_POSITIONAL_BEAM_V10.2.2",
            "sporting_extension": "V10.3_B1",
            "beam_width_per_tier": max_width,
            "simulations": len(projection_cache),
            "fast_projections": len(projection_cache),
            "full_lineup_simulations": 0,
            "position_policy_assumption": "PRIMARY_POSITION_ONLY",
        },
        "reason": (
            "Tier B mantiene XI completo para compatibilidad de solvencia. "
            "Trading V10.3 usa B1: XI completo y perdida deportiva dentro "
            "del umbral configurado. B2/C quedan para de-risk/emergencia. "
            "La viabilidad usa el fast-path posicional."
        ),
    }
