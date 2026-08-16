"""
¿De verdad conocemos la historia de cada rival?

POR QUE EXISTE
    El ledger de rivales se reconstruye del tablon, y trae una
    validacion que decia:

        validation: {exact: true, official_balance: -4.651.032,
                     ledger_balance: -4.651.032}

    Ese `exact` compara nuestro saldo oficial con el reconstruido.
    Solo el nuestro. No dice absolutamente nada sobre si conocemos
    las operaciones de los demas, porque Biwenger no publica el
    saldo de nadie mas.

    Y sobre ese `exact` se estaba decidiendo cuanto arriesgar al
    pujar: si el ledger "cuadraba", se pujaba al minimo dando por
    hecho que sabiamos quien tiene dinero. Se estaba midiendo una
    cosa para decidir sobre otra.

    Salio a la luz el 16/08/2026 porque el dueno del equipo hablo
    con un rival, Mex, y lo que le conto no encajaba con lo que
    decia el panel. La respuesta resulto ser que si encajaba, pero
    para averiguarlo hubo que hacer a mano la comprobacion que
    faltaba.

LA COMPROBACION QUE FALTABA
    Cada jugador de la plantilla de un rival llego de una de dos
    formas: en el reparto inicial de la liga, o comprandolo. Si
    tiene un jugador que no estaba en el reparto y no tenemos
    registrada su compra, nos falta historia suya.

    Es una conciliacion jugador a jugador, y no depende de que
    nadie nos diga su saldo.

EL CASO MEX, RESUELTO
    Mex tenia 15 jugadores y cero compras registradas, lo que
    parecia un agujero enorme. Pero sus 15 comparten `owner_since`
    exacto -09/08 12:32:42-, cinco minutos despues del
    `leagueReset`, y coincidiendo con su `userJoin`: se incorporo
    despues del reparto y recibio plantilla entonces.

    El resto de managers tienen su lote a las 12:27:2x, que es el
    reparto. Ninguno tiene jugadores sin explicar.

    O sea: el ledger estaba bien. Lo que faltaba era poder
    demostrarlo en una linea en vez de en media hora.

PARA QUE SIRVE EL RESULTADO
    La cobertura por rival alimenta el modelo de puja. De un rival
    del que lo sabemos todo se puede afirmar "este nunca puja". De
    uno del que nos falta media historia, no: ahi hay que tirar de
    prudencia y no pujar al filo.
"""

from __future__ import annotations


# Un lote de adquisiciones con el mismo instante y al menos este
# tamano es un reparto, no una racha de compras.
INITIAL_BATCH_MIN_PLAYERS = 5

# Tolerancia al agrupar: los repartos llegan con segundos de
# diferencia entre managers.
BATCH_WINDOW_SECONDS = 120

# Cobertura minima para poder afirmar algo en negativo, del tipo
# "este rival no puja nunca".
MIN_COVERAGE_FOR_NEGATIVE_CLAIM = 0.80

# Tipos de operacion que anaden un jugador a la plantilla.
ACQUISITION_KINDS = frozenset(
    {
        "BUY_FROM_COMPUTER",
        "BUY_FROM_USER",
        "CLAUSE_PAID",
    }
)


def safe_int(value, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def _initial_batch_timestamp(roster: list) -> int | None:
    """
    El instante del reparto para este manager: el `owner_since`
    que comparten muchos jugadores a la vez.
    """

    cuenta = {}

    for jugador in roster:

        momento = safe_int(jugador.get("owner_since"))

        if momento <= 0:
            continue

        cuenta[momento] = cuenta.get(momento, 0) + 1

    if not cuenta:
        return None

    momento, repeticiones = max(
        cuenta.items(),
        key=lambda item: (item[1], -item[0]),
    )

    if repeticiones < INITIAL_BATCH_MIN_PLAYERS:
        return None

    return momento


def audit_manager(manager: dict) -> dict:
    """
    Cuanto de la plantilla de este manager sabemos explicar.
    """

    roster = [
        p for p in (manager.get("roster") or [])
        if isinstance(p, dict)
    ]

    transacciones = [
        t for t in (manager.get("transactions") or [])
        if isinstance(t, dict)
    ]

    if not roster:
        return {
            "auditable": False,
            "coverage": None,
            "roster_size": 0,
            "from_initial_draft": 0,
            "acquired": 0,
            "explained": 0,
            "unexplained": [],
            "reason": (
                "Sin plantilla en el ledger: no se puede "
                "conciliar. Probablemente sea una version "
                "resumida del informe."
            ),
        }

    reparto = _initial_batch_timestamp(roster)

    comprados = set()

    for operacion in transacciones:

        if str(operacion.get("kind")) in ACQUISITION_KINDS:
            comprados.add(
                safe_int(operacion.get("player_id"))
            )

    del_reparto = []
    adquiridos = []

    for jugador in roster:

        momento = safe_int(jugador.get("owner_since"))

        if (
            reparto is not None
            and abs(momento - reparto) <= BATCH_WINDOW_SECONDS
        ):
            del_reparto.append(jugador)

        else:
            adquiridos.append(jugador)

    sin_explicar = [
        {
            "id": safe_int(j.get("id")),
            "name": j.get("name"),
            "value": safe_int(j.get("value")),
            "owner_since": safe_int(j.get("owner_since")),
        }
        for j in adquiridos
        if safe_int(j.get("id")) not in comprados
    ]

    explicados = len(adquiridos) - len(sin_explicar)

    cobertura = (
        1.0
        if not adquiridos
        else round(explicados / len(adquiridos), 4)
    )

    if not adquiridos:
        motivo = (
            f"Los {len(del_reparto)} jugadores vienen del reparto "
            f"inicial. No hay compras que explicar."
        )

    elif not sin_explicar:
        motivo = (
            f"Las {len(adquiridos)} incorporaciones posteriores al "
            f"reparto estan todas registradas."
        )

    else:
        motivo = (
            f"{len(sin_explicar)} de {len(adquiridos)} "
            f"incorporaciones no tienen operacion registrada: "
            + ", ".join(
                str(j["name"]) for j in sin_explicar[:4]
            )
            + ("..." if len(sin_explicar) > 4 else "")
            + ". Nos falta historia de este manager."
        )

    return {
        "auditable": True,
        "coverage": cobertura,
        "roster_size": len(roster),
        "initial_batch_ts": reparto,
        "from_initial_draft": len(del_reparto),
        "acquired": len(adquiridos),
        "explained": explicados,
        "unexplained": sin_explicar,
        "can_claim_never_bids": bool(
            cobertura >= MIN_COVERAGE_FOR_NEGATIVE_CLAIM
        ),
        "reason": motivo,
    }


def audit_rival_ledger(
    rival_intelligence: dict | None,
    own_user_id: int | None = None,
) -> dict:
    """
    Conciliacion de todos los managers.

    Nunca lanza: un fallo aqui no puede parar un ciclo, y ademas
    su respuesta correcta ante la duda es "no lo se", que es justo
    lo que hace que el modelo de puja sea prudente.
    """

    try:
        managers = [
            m for m in (
                (rival_intelligence or {}).get("managers") or []
            )
            if isinstance(m, dict)
        ]

        if not managers:
            return {
                "available": False,
                "by_manager": {},
                "min_coverage": None,
                "status": "SIN_DATOS",
                "reason": "No hay managers en el informe.",
            }

        por_manager = {}

        for manager in managers:

            identificador = safe_int(
                manager.get("user_id") or manager.get("id")
            )

            resultado = audit_manager(manager)
            resultado["name"] = manager.get("name")
            resultado["is_us"] = (
                own_user_id is not None
                and identificador == safe_int(own_user_id)
            )

            por_manager[identificador] = resultado

        coberturas = [
            r["coverage"]
            for r in por_manager.values()
            if r["auditable"] and r["coverage"] is not None
        ]

        if not coberturas:
            return {
                "available": False,
                "by_manager": por_manager,
                "min_coverage": None,
                "status": "NO_AUDITABLE",
                "reason": (
                    "El informe no trae plantillas: no se puede "
                    "conciliar jugador a jugador."
                ),
            }

        minima = min(coberturas)

        con_huecos = [
            r for r in por_manager.values()
            if r.get("unexplained")
        ]

        return {
            "available": True,
            "by_manager": por_manager,
            "min_coverage": minima,
            "managers_with_gaps": [
                {
                    "name": r["name"],
                    "unexplained": len(r["unexplained"]),
                    "coverage": r["coverage"],
                }
                for r in con_huecos
            ],
            "status": (
                "COMPLETO"
                if not con_huecos
                else "CON_HUECOS"
            ),
            "reason": (
                "Todas las plantillas se explican con el reparto "
                "inicial y las operaciones registradas."
                if not con_huecos
                else (
                    f"{len(con_huecos)} manager(es) con jugadores "
                    f"sin explicar. Las estimaciones de su saldo "
                    f"no son fiables."
                )
            ),
        }

    except Exception as error:
        return {
            "available": False,
            "by_manager": {},
            "min_coverage": None,
            "status": "ERROR",
            "reason": f"{type(error).__name__}: {error}",
        }


def print_rival_ledger_audit(audit: dict) -> None:

    print()
    print("-" * 70)
    print("CONCILIACION DEL LEDGER DE RIVALES")
    print("-" * 70)

    if not audit or not audit.get("available"):
        print(f"  No disponible: {(audit or {}).get('reason')}")
        return

    print(
        f"  {'MANAGER':<22}{'PLANTILLA':>10}{'REPARTO':>9}"
        f"{'FICHADOS':>10}{'EXPLIC.':>9}{'COBERT.':>9}"
    )

    for datos in audit["by_manager"].values():

        if not datos["auditable"]:
            continue

        marca = "  <- HUECOS" if datos["unexplained"] else ""

        print(
            f"  {str(datos['name'])[:21]:<22}"
            f"{datos['roster_size']:>10}"
            f"{datos['from_initial_draft']:>9}"
            f"{datos['acquired']:>10}"
            f"{datos['explained']:>9}"
            f"{datos['coverage'] * 100:>8.0f}%"
            f"{marca}"
        )

    print()
    print(f"  {audit['status']}: {audit['reason']}")
