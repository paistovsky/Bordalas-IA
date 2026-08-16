"""
Reproduce y verifica el arreglo del HAMBRE DE ACCIONES.

Problema real observado el 2026-08-16:

  - 9 publicaciones marcadas para renovar.
  - RENEW_MARKET_LISTING tenia prioridad 660.
  - SPECULATION_BUY tenia prioridad 400.
  - El ciclo ejecuta UNA accion por vuelta.
  - La renovacion fallaba con HTTP 400 cada vez.

Resultado: 6 objetivos pujables sobre la mesa y 0 pujas vivas
durante dias, porque el ciclo se dedicaba a reintentar la misma
renovacion rota cada 30 minutos.

Este test cubre las tres piezas del arreglo:

  1. Una publicacion con horas de vida por delante NO adelanta
     a una puja.
  2. Una publicacion a punto de caducar SI la adelanta.
  3. Una accion que acaba de fallar al escribir se aparta un
     rato para que la cola avance.
"""

import sys

from datetime import datetime, timedelta

sys.path.insert(0, ".")

from src.analysis.action_failure_backoff import (  # noqa: E402
    MAX_BACKOFF_SECONDS,
    apply_backoff_to_candidates,
    backoff_seconds,
    build_action_key,
    candidate_target_id,
    empty_state,
    get_backoff,
    record_action_result,
)

from src.analysis.decision_orchestrator import (  # noqa: E402
    PRIORITY,
    build_action_queue,
)

from src.analysis.market_listing_lifecycle_engine import (  # noqa: E402
    RENEW_URGENT_HOURS,
    analyze_listing_lifecycle,
    resolve_renewal_price,
)

from src.analysis.computer_cycle_engine import (  # noqa: E402
    MADRID_TZ,
)


fallos = []


def check(nombre, condicion, detalle=""):

    if condicion:
        print(f"  OK   {nombre}")
    else:
        print(f"  FALLA {nombre} {detalle}")
        fallos.append(nombre)


# ================================================================
# UTILIDADES
# ================================================================


def build_cycle_state(now, cycle_start, cycle_end):

    return {
        "now": now,
        "safe_cycles": [
            {
                "cycle_start": cycle_start,
                "cycle_end": cycle_end,
                "safe_liquidity_at": cycle_end
                + timedelta(minutes=30),
            }
        ],
    }


def build_listing(player_id, name, expires_at, listed_at):

    return {
        "player_id": player_id,
        "player": {"id": player_id, "name": name},
        "listed_price": 1_000_000,
        "listed_at": listed_at,
        "expires_at": expires_at,
    }


def build_renew_candidate(analysis, urgent):

    clave = (
        "MARKET_LISTING_RENEW_URGENT"
        if urgent
        else "MARKET_LISTING_RENEW"
    )

    return {
        "type": clave,
        "priority": PRIORITY[clave],
        "action": "RENEW_MARKET_LISTING",
        "executable": True,
        "executor": "AUTOPILOT",
        "reason": "Renovar publicacion.",
        "data": {"listing": analysis},
    }


def build_speculation_candidate():

    return {
        "type": "SPECULATION_BUY",
        "priority": PRIORITY["SPECULATION_BUY"],
        "action": "BUY_SPECULATION",
        "executable": True,
        "executor": "AUTOPILOT",
        "reason": "Yusi Enriquez a 360.000 vale 2.925.844.",
        "data": {"player": {"id": 99999, "name": "Yusi"}},
    }


# ================================================================
# 1. CLASIFICACION DE URGENCIA
# ================================================================


print()
print("1. La publicacion sabe si de verdad corre peligro")
print("-" * 60)

now = datetime(2026, 8, 16, 16, 21, tzinfo=MADRID_TZ)

# El reset Computer de manana.
cycle_start = datetime(2026, 8, 17, 5, 0, tzinfo=MADRID_TZ)
cycle_end = datetime(2026, 8, 17, 7, 0, tzinfo=MADRID_TZ)

cycle_state = build_cycle_state(now, cycle_start, cycle_end)

# Yeray: caduca hoy a las 22:44 -> 6,39 h de vida.
yeray = analyze_listing_lifecycle(
    listing=build_listing(
        5771,
        "Yeray",
        datetime(2026, 8, 16, 22, 44, 20, tzinfo=MADRID_TZ),
        datetime(2026, 8, 14, 22, 44, 20, tzinfo=MADRID_TZ),
    ),
    cycle_state=cycle_state,
    now=now,
)

check(
    "Yeray necesita renovacion",
    yeray["renew_required"] is True,
)

check(
    "Yeray NO es urgente todavia (6,39 h)",
    yeray["renew_urgent"] is False,
    f"hours_to_expiry={yeray['hours_to_expiry']}",
)

# La misma publicacion vista 4 horas mas tarde.
mas_tarde = datetime(2026, 8, 16, 20, 30, tzinfo=MADRID_TZ)

yeray_tarde = analyze_listing_lifecycle(
    listing=build_listing(
        5771,
        "Yeray",
        datetime(2026, 8, 16, 22, 44, 20, tzinfo=MADRID_TZ),
        datetime(2026, 8, 14, 22, 44, 20, tzinfo=MADRID_TZ),
    ),
    cycle_state=build_cycle_state(
        mas_tarde, cycle_start, cycle_end
    ),
    now=mas_tarde,
)

check(
    "Yeray SI es urgente a 2,24 h de caducar",
    yeray_tarde["renew_urgent"] is True,
    f"hours_to_expiry={yeray_tarde['hours_to_expiry']}",
)

check(
    "El umbral de urgencia es explicito",
    yeray_tarde["hours_to_expiry"] <= RENEW_URGENT_HOURS,
)


# ================================================================
# 2. EL ORDEN DE LA COLA
# ================================================================


print()
print("2. Una puja no espera detras de un anuncio con 6 h de vida")
print("-" * 60)

check(
    "RENEW normal esta POR DEBAJO de SPECULATION_BUY",
    PRIORITY["MARKET_LISTING_RENEW"]
    < PRIORITY["SPECULATION_BUY"],
    f"{PRIORITY['MARKET_LISTING_RENEW']} vs "
    f"{PRIORITY['SPECULATION_BUY']}",
)

check(
    "RENEW urgente esta POR ENCIMA de SPECULATION_BUY",
    PRIORITY["MARKET_LISTING_RENEW_URGENT"]
    > PRIORITY["SPECULATION_BUY"],
)

cola = build_action_queue(
    [
        build_renew_candidate(yeray, urgent=False),
        build_speculation_candidate(),
    ]
)

check(
    "Con 6 h de vida, primero se puja",
    cola[0]["action"] == "BUY_SPECULATION",
    f"primero={cola[0]['action']}",
)

check(
    "La renovacion sigue en la cola, no desaparece",
    any(
        item["action"] == "RENEW_MARKET_LISTING"
        for item in cola
    ),
)

cola_urgente = build_action_queue(
    [
        build_renew_candidate(yeray_tarde, urgent=True),
        build_speculation_candidate(),
    ]
)

check(
    "A 2 h de caducar, primero se renueva",
    cola_urgente[0]["action"] == "RENEW_MARKET_LISTING",
    f"primero={cola_urgente[0]['action']}",
)


# ================================================================
# 3. BACKOFF POR FALLO DE ESCRITURA
# ================================================================


print()
print("3. Una accion rota no puede bloquear el ciclo para siempre")
print("-" * 60)

check(
    "La clave distingue jugadores",
    build_action_key("RENEW_MARKET_LISTING", 5771)
    != build_action_key("RENEW_MARKET_LISTING", 17482),
)

check(
    "1 fallo = 30 min",
    backoff_seconds(1) == 1800,
    str(backoff_seconds(1)),
)

check(
    "2 fallos = 1 h",
    backoff_seconds(2) == 3600,
)

check(
    "El castigo tiene techo",
    backoff_seconds(50) == MAX_BACKOFF_SECONDS,
)

check(
    "Sin fallos no hay castigo",
    backoff_seconds(0) == 0,
)

check(
    "El objetivo se lee de la publicacion",
    candidate_target_id(
        build_renew_candidate(yeray, urgent=True)
    )
    == 5771,
)

check(
    "El objetivo se lee tambien del jugador",
    candidate_target_id(build_speculation_candidate())
    == 99999,
)

# El fallo real del 2026-08-16.
estado = empty_state()

estado = record_action_result(
    estado,
    action="RENEW_MARKET_LISTING",
    target_id=5771,
    success=False,
    write_performed=True,
    status="FAILED",
    http_status=400,
    reason="Biwenger no confirmo la renovacion.",
    now=now,
)

info = get_backoff(estado, "RENEW_MARKET_LISTING", 5771, now)

check(
    "Tras el HTTP 400 la accion queda en espera",
    info["blocked"] is True,
)

check(
    "Se recuerda el codigo HTTP para poder diagnosticar",
    info["last_http_status"] == 400,
)

check(
    "Otro jugador NO queda bloqueado por el fallo de Yeray",
    get_backoff(
        estado, "RENEW_MARKET_LISTING", 17482, now
    )["blocked"]
    is False,
)

check(
    "Un DRY_RUN no cuenta como fallo",
    get_backoff(
        record_action_result(
            empty_state(),
            action="RENEW_MARKET_LISTING",
            target_id=5771,
            success=False,
            write_performed=False,
            now=now,
        ),
        "RENEW_MARKET_LISTING",
        5771,
        now,
    )["blocked"]
    is False,
)

check(
    "Pasado el castigo se reintenta",
    get_backoff(
        estado,
        "RENEW_MARKET_LISTING",
        5771,
        now + timedelta(seconds=1801),
    )["blocked"]
    is False,
)

check(
    "Un exito borra el historial de fallos",
    get_backoff(
        record_action_result(
            estado,
            action="RENEW_MARKET_LISTING",
            target_id=5771,
            success=True,
            write_performed=True,
            now=now,
        ),
        "RENEW_MARKET_LISTING",
        5771,
        now,
    )["blocked"]
    is False,
)


# ================================================================
# 4. EL ESCENARIO COMPLETO
# ================================================================


print()
print("4. Escenario real: renovacion urgente rota + 1 puja buena")
print("-" * 60)

# Peor caso: la renovacion es URGENTE (gana la cola) y ademas
# esta rota. Sin backoff, la puja no se ejecuta nunca.

estado_roto = empty_state()

estado_roto = record_action_result(
    estado_roto,
    action="RENEW_MARKET_LISTING",
    target_id=5771,
    success=False,
    write_performed=True,
    status="FAILED",
    http_status=400,
    reason="Biwenger no confirmo la renovacion.",
    now=now,
)

candidatos = [
    build_renew_candidate(yeray_tarde, urgent=True),
    build_speculation_candidate(),
]

reporte = apply_backoff_to_candidates(
    candidates=candidatos,
    state=estado_roto,
    now=now,
)

cola_final = build_action_queue(candidatos)

check(
    "El backoff detecta la accion rota",
    reporte["blocked_count"] == 1,
    str(reporte),
)

check(
    "Ahora la puja SI se ejecuta",
    cola_final and cola_final[0]["action"] == "BUY_SPECULATION",
    str([item["action"] for item in cola_final]),
)

renovacion = candidatos[0]

check(
    "La renovacion no se borra: sigue visible",
    renovacion.get("blocked_by_backoff") is True,
)

check(
    "El motivo explica por que no se ejecuta",
    "EN ESPERA" in renovacion.get("reason", ""),
    renovacion.get("reason", ""),
)

check(
    "La puja no queda marcada por error",
    candidatos[1].get("blocked_by_backoff") is None,
)


# ================================================================
# 5. EL PRECIO DE LA RENOVACION
# ================================================================


print()
print("5. Nunca republicamos por debajo del valor de mercado")
print("-" * 60)

# Caso real que fallo: Yeray publicado a 1.941.001 cuando su
# valor ya era 1.950.000.
yeray_precio = resolve_renewal_price(
    listed_price=1_941_001,
    market_value=1_950_000,
)

check(
    "Yeray sube al valor de mercado",
    yeray_precio["renewal_price"] == 1_950_000,
    str(yeray_precio),
)

check(
    "Y queda registrado que se ha subido",
    yeray_precio["price_raised"] is True,
)

# Caso real que funciono: Fidalgo publicado por encima.
fidalgo_precio = resolve_renewal_price(
    listed_price=1_183_812,
    market_value=1_060_000,
)

check(
    "Fidalgo mantiene su precio, no se toca",
    fidalgo_precio["renewal_price"] == 1_183_812,
    str(fidalgo_precio),
)

check(
    "Y no se marca como subida",
    fidalgo_precio["price_raised"] is False,
)

check(
    "La correccion NUNCA baja el precio",
    all(
        resolve_renewal_price(
            listed_price=publicado,
            market_value=valor,
        )["renewal_price"]
        >= publicado
        for publicado, valor in (
            (1_000_000, 1),
            (1_000_000, 0),
            (1_000_000, None),
            (33_480_000, 22_250_000),
        )
    ),
)

check(
    "Valores ausentes no rompen nada",
    resolve_renewal_price(
        listed_price=None,
        market_value=None,
    )["renewal_price"]
    == 0,
)


# ================================================================
# RESULTADO
# ================================================================


print()
print("=" * 60)

if fallos:
    print(f"FALLOS: {len(fallos)}")
    for nombre in fallos:
        print(f"  - {nombre}")
    sys.exit(1)

print("TODO OK")
print("=" * 60)
