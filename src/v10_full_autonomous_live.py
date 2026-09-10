from __future__ import annotations

import json
from datetime import date, datetime, time, timezone
from pathlib import Path

from src.autopilot import (
    _publicar_peticiones,
    refresh_snapshot,
    run_cycle,
)

from src.biwenger.peticiones import LimiteDePeticiones
from src.analysis.controlled_speculation_live import (
    build_controlled_run,
    print_result as print_controlled_buy,
)
from src.analysis.position_manager_shadow_v106 import (
    sync_current as sync_position_manager,
    print_board as print_position_manager,
)
from src.analysis.dynamic_counteroffer_repricing_v107 import (
    sync_current as sync_counter_repricing,
    print_board as print_counter_repricing,
)
from src.actions.live_sale_executor import execute_sale_listing
from src.biwenger.write_client import BiwengerWriteClient


STATUS_PATH = Path("data/trading/v10_full_autonomous_status.json")

EXIT_ACTIONS = {
    "TAKE_PROFIT",
    "CUT_LOSS",
    "ROTATE_CAPITAL",
}


def _json_default(value):
    """Serializa tipos auxiliares presentes en resultados LIVE anidados."""
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, set):
        return sorted(value)
    raise TypeError(
        f"Object of type {type(value).__name__} is not JSON serializable"
    )


def _write_used(cycle: dict) -> bool:
    legacy = cycle.get("execution", {}) or {}
    competitive = cycle.get("competitive_execution", {}) or {}
    return bool(
        legacy.get("write_performed")
        or competitive.get("write_performed")
    )


def _cycle_write_execution(
    cycle: dict,
) -> tuple[str | None, dict | None]:
    """Devuelve la escritura real consumida por el ciclo principal."""
    for source, key in (
        ("AUTOPILOT", "execution"),
        ("COMPETITIVE", "competitive_execution"),
    ):
        execution = cycle.get(key, {}) or {}
        if execution.get("write_performed"):
            return source, execution

    return None, None


def _compact_execution(
    *,
    source: str | None,
    action: str | None,
    result: dict | None,
    write_used: bool,
) -> dict:
    result = result or {}
    return {
        "source": source,
        "action": action,
        "status": result.get("status"),
        "write_performed": bool(write_used),
        "success": result.get(
            "success",
            (
                result.get(
                    "writes_biwenger",
                    result.get("sent"),
                )
                if write_used
                else None
            ),
        ),
        "reason": result.get("reason"),
        "http_status": result.get("http_status"),
    }


def _best_exit(board: dict) -> dict | None:
    items = [
        item
        for item in (board.get("actionable", []) or [])
        if item.get("action") in EXIT_ACTIONS
    ]
    if not items:
        return None
    return sorted(
        items,
        key=lambda x: (
            int(x.get("priority") or 0),
            abs(int(x.get("unrealized_pnl") or 0)),
        ),
        reverse=True,
    )[0]


def _best_cancel(board: dict) -> dict | None:
    """
    CANCEL_COUNTER tiene prioridad 100 en el motor, por encima de
    RAISE_COUNTER (90), porque mantener viva una contraoferta que
    el rival puede aceptar sobre un jugador que ya es NEVER_SELL
    es la situacion mas peligrosa del tablero.

    Hasta ahora esa accion no la consumia nadie: se emitia, se
    imprimia y se olvidaba. cancel_bid() no tenia un solo
    llamante en todo el repositorio.

    Se cancela counter_offer_id -NUESTRA contraoferta-, nunca
    incoming_offer_id, que es la oferta del rival.
    """
    items = [
        item
        for item in (board.get("actions", []) or [])
        if item.get("action") == "CANCEL_COUNTER"
        and int(item.get("counter_offer_id") or 0) > 0
    ]
    if not items:
        return None
    return sorted(
        items,
        key=lambda x: (
            int(x.get("priority") or 0),
            float(x.get("urgency_score") or 0),
        ),
        reverse=True,
    )[0]


def _temporal_block(cycle: dict) -> str | None:
    """
    Devuelve la fase si las operaciones estan bloqueadas.

    Las escrituras V10 -contraoferta, cancelacion, salida- no
    pasaban por ninguna barrera temporal: solo el ejecutor legacy
    la respetaba. Un ciclo que arranca en fase NORMAL y termina
    90 segundos despues ya dentro del bloqueo podia escribir.
    """
    state = (
        (
            cycle.get(
                "result",
                {},
            )
            or {}
        ).get(
            "state",
            {},
        )
        or {}
    )

    if bool(
        state.get(
            "operations_locked",
            False,
        )
    ):
        return str(
            state.get(
                "phase",
                "UNKNOWN",
            )
        )

    return None


def _best_raise(board: dict) -> dict | None:
    items = [
        item
        for item in (board.get("actions", []) or [])
        if item.get("action") == "RAISE_COUNTER"
        and int(item.get("incoming_offer_id") or 0) > 0
        and int(item.get("recommended_counter") or 0) > 0
    ]
    if not items:
        return None
    return sorted(
        items,
        key=lambda x: (
            float(x.get("urgency_score") or 0),
            int(x.get("raise_by") or 0),
        ),
        reverse=True,
    )[0]


def _verify_v10_write(action: str) -> dict:
    """Actualiza una sola vez tras una escritura nacida fuera de run_cycle."""
    print()
    print(
        f"Verificando {action} con un unico refresco post-escritura..."
    )

    try:
        snapshot_file, _ = refresh_snapshot()
    except Exception as error:
        # La escritura ya fue consumida: un fallo de verificacion no debe
        # habilitar otra accion ni ocultar lo ocurrido.
        return {
            "attempted": True,
            "success": False,
            "snapshot_file": None,
            "error": f"{type(error).__name__}: {error}",
        }

    return {
        "attempted": True,
        "success": True,
        "snapshot_file": snapshot_file,
        "error": None,
    }


def _estado_publicado(cycle: dict | None) -> dict:
    """
    El tablero del reset, con la misma forma que el dashboard.

    POR QUE HAY QUE ARMARLO Y NO BASTA CON `cycle`

        `run_cycle` devuelve {snapshot, result, execution,
        post_action}, y su `result["state"]` NO lleva ni el
        tablero de adquisicion, ni los bolsillos compactados, ni
        el reloj del mercado: eso lo monta la telemetria, que
        corre DESPUES en otro proceso.

        Leer `cycle["state"]` -o incluso `result["state"]`-
        buscando `acquisition` devuelve vacio: cero candidatos,
        cero pujas y ni un error en el log. Encendido y mudo,
        que es la peor forma de estar apagado.

    NO CUESTA NI UNA PETICION

        El tablon y el retrato de la competencia se piden UNA
        vez por vuelta y quedan cacheados desde el 07/09.
        `load_rival_intelligence` y `board_del_ciclo` devuelven
        lo ya pedido; aqui no se abre ninguna conexion nueva.

    Nunca lanza. Devuelve la forma aunque falte todo.
    """

    publicado = {
        "acquisition": {},
        "exposure": {},
        "market_clock": {},
        "rival_intelligence": {},
        "solvency_clock": None,
        "operations_locked": False,
        "phase": None,
    }

    try:
        from src.autopilot import (
            board_del_ciclo,
            load_rival_intelligence,
        )
        from src.analysis.acquisition_board import (
            build_acquisition_board,
        )
        from src.analysis.market_clock import build_market_clock
        from src.analysis.solvency_clock import (
            build_solvency_clock,
        )

        snapshot = (cycle or {}).get("snapshot") or {}

        estado = (
            (cycle or {}).get("result") or {}
        ).get("state") or {}

        especulacion = estado.get("speculation") or {}
        bolsillo = especulacion.get("budget") or {}
        fichajes = especulacion.get("acquisition_budget") or {}

        publicado["operations_locked"] = bool(
            estado.get("operations_locked")
        )
        publicado["phase"] = estado.get("phase")

        publicado["exposure"] = {
            "available_budget": bolsillo.get("available_budget"),
            "cash_budget": bolsillo.get("cash_budget"),
        }

        publicado["market_clock"] = build_market_clock(snapshot)

        # EL RELOJ DE SOLVENCIA, EN SU VERSION ESTRICTA
        #
        #     La telemetria se lo calcula contando la venta de
        #     rescate que taparia la deuda. Aqui no hay orden de
        #     ventas montada, asi que se calcula sin ella.
        #
        #     La diferencia siempre cae del lado de NO pujar: si
        #     hay deuda y aqui no consta como tapada, no se puja.
        #     Que un dia se deje de pujar por prudencia es
        #     barato; lo caro es lo contrario.
        publicado["solvency_clock"] = build_solvency_clock(
            estado.get("balance"),
            estado.get("hours_to_deadline"),
            market_clock=publicado["market_clock"],
        )

        inteligencia = load_rival_intelligence(snapshot)
        tablon = board_del_ciclo(snapshot)

        # `is_us` NO viene en el retrato crudo: lo pone la
        # telemetria al compactarlo. Sin el, "nuestra plantilla"
        # sale 0, las fichas libres salen enormes y la
        # barandilla de fichas deja de morder. Se marca aqui.
        yo = tablon.get("current_user_id") or inteligencia.get(
            "current_user_id"
        )

        publicado["rival_intelligence"] = {
            "managers": [
                {
                    "user_id": m.get("user_id"),
                    "roster_count": m.get("roster_count"),
                    "is_us": (
                        yo is not None
                        and str(m.get("user_id")) == str(yo)
                    ),
                }
                for m in (inteligencia.get("managers") or [])
                if isinstance(m, dict)
            ]
        }

        publicado["acquisition"] = build_acquisition_board(
            snapshot=snapshot,
            rival_intelligence=inteligencia,
            current_user_id=tablon.get("current_user_id"),
            available_budget=(
                bolsillo.get("available_budget") or None
            ),
            acquisition_budget=(
                (
                    fichajes.get("available_budget")
                    or fichajes.get("total_budget")
                )
                if fichajes.get("enabled")
                else None
            ),
        )

        return publicado

    except Exception:                               # noqa: BLE001
        return publicado


def _pujar_en_el_reset(cycle: dict | None) -> dict:
    """
    Las pujas de la ventana del reset, ejecutadas de verdad.

    LO QUE HACE Y LO QUE NO

        Puja por hasta `MAX_PUJAS_PRIMER_DIA` en los ultimos
        minutos antes del reset, y SOLO ahi. Cada puja al precio
        topado por la curva.

        No vende, no acepta ofertas y no toca el once.

    LAS PUERTAS ESTAN EN `plan_del_reset`, NO AQUI

        Esta funcion no decide: pregunta y ejecuta. Si algun dia
        hay que endurecer una condicion, se endurece en un sitio
        y esta no cambia.

    Nunca lanza: una subasta que revienta no puede tumbar el
    ciclo entero.
    """

    vacio = {
        "available": False,
        "execute": False,
        "bids": [],
        "sent": [],
        "failed": [],
        "reason": None,
    }

    try:
        from src.analysis.la_subasta import plan_desde_el_estado

        publicado = _estado_publicado(cycle)

        plan = plan_desde_el_estado(
            publicado,
            (cycle or {}).get("snapshot"),
            en_vivo=True,
        )

        print()
        print("=" * 100)
        print("LA SUBASTA DEL RESET")
        print("=" * 100)
        print(f"  {plan['reason']}")

        # `_euros` y no `.replace(",", ".")` sobre la linea
        # entera: eso se come las comas del nombre.
        from src.analysis.la_subasta import _euros

        for puja in plan["bids"]:
            print(
                f"    {str(puja.get('name'))[:22]:<22}"
                f"{_euros(puja.get('bid')):>12}"
                f"   se lo lleva "
                f"{100 * (puja.get('win_odds') or 0):.0f} %"
            )

        if not plan.get("execute"):
            return {**vacio, "available": True, **plan}

        enviadas = []
        fallidas = []

        from src.biwenger.write_client import (
            BiwengerWriteClient,
        )

        escritor = BiwengerWriteClient()

        for puja in plan["bids"]:

            try:
                resultado = escritor.place_bid(
                    player_id=int(puja["id"]),
                    amount=int(puja["bid"]),
                    seller_user_id=puja.get("seller_id"),
                    execute=True,
                )

                enviadas.append(
                    {
                        "id": puja["id"],
                        "name": puja.get("name"),
                        "amount": puja["bid"],
                        "market_price": puja.get("market_price"),
                        "win_odds": puja.get("win_odds"),
                        "seller_id": puja.get("seller_id"),
                        "rate_percent_per_day": puja.get(
                            "rate_percent_per_day"
                        ),
                        "sent": bool(resultado.get("sent")),
                    }
                )

            except Exception as error:              # noqa: BLE001
                fallidas.append(
                    {
                        "id": puja.get("id"),
                        "name": puja.get("name"),
                        "error": (
                            f"{type(error).__name__}: {error}"
                        ),
                    }
                )

        print()
        print(
            f"  ENVIADAS {len(enviadas)}  ·  FALLIDAS "
            f"{len(fallidas)}"
        )

        # AL LIBRO DE PUJAS, que hoy tiene UN registro. Sin esto
        # no se podria medir nunca si esto funciona.
        _anotar_en_el_libro(enviadas)

        return {
            **plan,
            "available": True,
            "sent": enviadas,
            "failed": fallidas,
        }

    except Exception as error:                      # noqa: BLE001
        return {
            **vacio,
            "reason": (
                f"La subasta no pudo correr: "
                f"{type(error).__name__}: {error}"
            ),
        }


def _anotar_en_el_libro(enviadas: list | None) -> None:
    """
    Cada puja enviada, al libro. Nunca lanza.

    Es lo que permitira decir dentro de una semana si el modo
    cartera gana dinero o no.
    """

    if not enviadas:
        return

    try:
        from src.intelligence.bid_outcome_ledger import (
            record_bid,
        )

        for puja in enviadas:
            try:
                record_bid(
                    player_id=int(puja.get("id")),
                    amount=int(puja.get("amount")),
                    player_name=puja.get("name"),
                    market_price=puja.get("market_price"),
                    recommended_bid=puja.get("amount"),
                    win_probability=puja.get("win_odds"),
                    intent="SPECULATION",

                    # De donde salio esta puja. Sin esto, dentro
                    # de una semana no se podria separar lo que
                    # gano el modo cartera de lo que gano el
                    # camino de siempre.
                    target_source="SUBASTA_CARTERA",

                    seller_user_id=puja.get("seller_id"),
                    market_rate_percent_per_day=puja.get(
                        "rate_percent_per_day"
                    ),
                )

            except Exception:                       # noqa: BLE001
                continue

    except Exception:                               # noqa: BLE001
        pass


def run_full_autonomous_cycle() -> dict:
    print("\n" + "=" * 100)
    print("BORDALAS IA - V10.13.1 FULL AUTONOMOUS LIVE")
    print("=" * 100)

    # 1) Existing production engine first.
    cycle = run_cycle(
        live=True,
        competitive_live=True,
    )

    execution_source, cycle_execution = _cycle_write_execution(cycle)
    write_used = _write_used(cycle)
    action_taken = (
        cycle_execution.get("action")
        if cycle_execution
        else None
    )
    action_result = cycle_execution
    v10_verification = {
        "attempted": False,
        "success": None,
        "snapshot_file": None,
        "error": None,
    }

    # ==========================================================
    # 1-bis) LA SUBASTA DEL RESET (09/09/2026)
    # ==========================================================
    #
    #     Va ANTES de la puerta de "una escritura por ciclo",
    #     porque en la ventana del reset la regla es otra: se
    #     puja por varios a la vez, que es todo el punto.
    #
    #     Fuera de la ventana ni se entera: `plan_del_reset`
    #     devuelve `execute: False` y esto no toca nada.
    #
    #     Y no consume `write_used`: una puja no es una compra.
    #     El balance no se mueve hasta el reset, asi que el resto
    #     del ciclo puede seguir haciendo su unica accion.
    subasta = _pujar_en_el_reset(cycle)

    # ==========================================================
    # 2) If no prior write, allow BUY V10.
    if not write_used:
        buy = build_controlled_run(
            # run_cycle ya creo el snapshot autoritativo de este ciclo.
            # El executor BUY conserva su lectura directa read-before-write.
            refresh=False,
            execute_live=True,
            live_confirmation="BORDALAS",
        )
        print_controlled_buy(buy)

        if buy.get("writes_biwenger"):
            write_used = True
            action_taken = "BUY_V10"
            action_result = buy
            execution_source = "V10_BUY"
            v10_verification = _verify_v10_write(
                action_taken
            )

    # 3) V10.6 comparte el snapshot mas reciente del ciclo.
    position = sync_position_manager(refresh=False)
    print_position_manager(position.get("board", {}) or {})

    # 4) V10.7 comparte el mismo snapshot; no vuelve a descargar Biwenger.
    counter = sync_counter_repricing(refresh=False)
    print_counter_repricing(counter.get("board", {}) or {})

    # 5) If still no write, execute ONE best autonomous action.
    temporal_block = _temporal_block(cycle)

    if temporal_block:
        print()
        print(
            f"V10: escrituras bloqueadas por fase "
            f"{temporal_block}. Ninguna accion autonoma."
        )

    if not write_used and not temporal_block:
        cancel_candidate = _best_cancel(counter.get("board", {}) or {})
        counter_candidate = _best_raise(counter.get("board", {}) or {})
        exit_candidate = _best_exit(position.get("board", {}) or {})

        # CANCEL_COUNTER va primero: prioridad 100 en el motor,
        # por encima de RAISE_COUNTER (90). Mantener viva una
        # contraoferta sobre un NEVER_SELL puede costar el jugador.
        if cancel_candidate:
            writer = BiwengerWriteClient()

            action_result = writer.cancel_bid(
                offer_id=int(
                    cancel_candidate["counter_offer_id"]
                ),
                execute=True,
            )
            write_used = bool(
                action_result.get("success")
            )
            action_taken = "CANCEL_COUNTER"
            execution_source = "V10_CANCEL"
            if write_used:
                v10_verification = _verify_v10_write(
                    action_taken
                )

        elif counter_candidate:
            writer = BiwengerWriteClient()

            offer_id = int(counter_candidate["incoming_offer_id"])
            amount = int(counter_candidate["recommended_counter"])

            action_result = writer.counter_offer(
                offer_id=offer_id,
                amount=amount,
                execute=True,
            )
            write_used = bool(
                action_result.get("success")
            )
            action_taken = "RAISE_COUNTER"
            execution_source = "V10_COUNTER"
            if write_used:
                v10_verification = _verify_v10_write(
                    action_taken
                )

        elif exit_candidate:
            player_id = int(exit_candidate["player_id"])
            price = int(exit_candidate["current_value"])

            action_result = execute_sale_listing(
                player_id=player_id,
                price=price,
                execute=True,
            )
            write_used = bool(action_result.get("sent"))
            action_taken = "EXIT_LISTING"
            execution_source = "V10_EXIT"
            if write_used:
                v10_verification = _verify_v10_write(
                    action_taken
                )

    payload = {
        "version": "V10.13.1",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "full_autonomous_live": True,
        "write_used": write_used,
        "action_taken": action_taken,
        "action_result": action_result,
        "execution": _compact_execution(
            source=execution_source,
            action=action_taken,
            result=action_result,
            write_used=write_used,
        ),
        "snapshot_policy": {
            "initial": 1,
            "legacy_post_write": bool(
                cycle.get("post_action")
            ),
            "v10_post_write": bool(
                v10_verification.get("success")
            ),
            "maximum_full_reads": 2,
        },
        "v10_write_verification": v10_verification,
    }

    STATUS_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATUS_PATH.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
            default=_json_default,
        ),
        encoding="utf-8",
    )

    print("\n" + "=" * 100)
    print("V10.13.1 SUMMARY")
    print("=" * 100)
    print("Full autonomous LIVE: YES")
    print(f"Write used: {'YES' if write_used else 'NO'}")
    print(f"Action: {action_taken or 'NONE'}")
    print(
        "Full Biwenger snapshots: "
        f"{1 + int(bool(cycle.get('post_action'))) + int(bool(v10_verification.get('success')))}"
        "/2 max"
    )
    print("=" * 100)

    return payload


def main() -> int:
    """
    El ciclo, con una sola salida especial: el limite de
    peticiones.

    EL INCIDENTE DEL 27/09/2026

        Biwenger empezo a devolver 429 a la cuenta entera y este
        `main` no tenia NINGUN try: la excepcion salia del
        proceso, el paso de Actions se ponia rojo y el workflow
        hubo que desactivarlo a mano.

        Un 429 no es un fallo nuestro. Es el servidor diciendo
        "ahora no". La sesion ya reintenta con espera creciente
        antes de llegar aqui; si aun asi no cede, lo unico
        correcto es retirarse sin tocar nada y volver en la
        siguiente vuelta.

    LO QUE NO CAMBIA

        Cualquier OTRA excepcion sigue subiendo igual que
        siempre y sigue poniendo el paso en rojo. Aqui solo se
        aparta el caso que no es un error.
    """

    try:
        run_full_autonomous_cycle()

    except LimiteDePeticiones as limite:

        print()
        print("=" * 100)
        print("LIMITE DE PETICIONES DE BIWENGER")
        print(f"{limite}")
        print(
            "El ciclo se retira limpiamente. NO es un fallo: no "
            "se ha tocado nada y se vuelve en la siguiente "
            "vuelta."
        )
        print("=" * 100)

        _publicar_peticiones()

        # Cero a proposito: el paso de Actions no debe ponerse
        # rojo por esto, o el dueño acaba desactivando el
        # workflow como el 27/09.
        return 0

    _publicar_peticiones()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
