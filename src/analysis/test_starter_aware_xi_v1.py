"""
No se mejora el once quitando a un titular para meter a un suplente.

EL CASO QUE LO DESTAPO

    16/08/2026, 20:47. Bordalas propone pujar 1.236.001 EUR por
    Andres Castrin, defensa del Sevilla, 1,03 M de precio y 97
    puntos la temporada pasada. Motivo escrito por el propio
    programa: "Suma 73 puntos".

    A quien sustituye: Yeray, defensa del Athletic, 1,95 M, 24
    puntos la temporada pasada.

    Los 73 puntos son reales. Y la operacion es mala, porque:

        Castrin  -> pronostico SUPLENTE
        Yeray    -> pronostico TITULAR (JP 92,2 %, FF 70 %)

    Un suplente no puntua. Se estaba pagando 1,2 M por empeorar
    el once, y la razon es que la valoracion nunca preguntaba
    quien juega: `estimate_season_points` devolvia
    `pointsLastSeason` y ahi se acababa la conversacion.

QUE SE COMPRUEBA AQUI

    1. Que con los datos reales de aquel dia la operacion se
       rechaza, y se rechaza por el motivo correcto.
    2. Que la regla no apaga las mejoras buenas: un titular mejor
       que otro titular sigue pasando.
    3. Que "el peor de la posicion" -a quien se propone vender-
       tambien se elige mirando quien juega.
"""

import sys

sys.path.insert(0, ".")

from src.analysis.acquisition_valuation import (  # noqa: E402
    build_valuation_context,
    value_candidate,
)

from src.analysis.candidate_starter_lookup import (  # noqa: E402
    build_starter_lookup,
    vote_label,
)

from src.analysis.player_value_engine import (  # noqa: E402
    BENCH_POINTS_FACTOR,
    estimate_season_points,
    starter_factor,
    xi_upgrade_value,
)


fallos = []


def check(nombre, condicion, detalle=""):
    if condicion:
        print(f"  OK   {nombre}")
    else:
        print(f"  FALLA {nombre} {detalle}")
        fallos.append(nombre)


TARIFA = 22_240

MERCADO = {
    "available": True,
    "rate_median": TARIFA,
    "samples": 393,
}


TITULAR = {
    "probability": 92.2,
    "consensus": "STARTER",
    "coverage": 2,
    "source": "MULTISOURCE",
}

SUPLENTE = {
    "probability": 31.3,
    "consensus": "BENCH",
    "coverage": 1,
    "source": "JORNADA_PERFECTA",
}


# ================================================================
# 1. EL CASO REAL
# ================================================================


print()
print("1. Castrin (suplente, 97 pts) por Yeray (titular, 24 pts)")
print("-" * 60)


castrin = {
    "id": 38072,
    "name": "Andres Castrin",
    "position": 2,
    "price": 1_030_000,
    "pointsLastSeason": 97,
    "teamID": 5,
}

yeray = {
    "id": 5771,
    "name": "Yeray",
    "position": 2,
    "price": 1_950_000,
    "pointsLastSeason": 24,
    "teamID": 9,
}


snapshot = {
    "my_team": [yeray],
    "catalog": {"data": {"players": {}, "teams": {}}},
    "market": {"sales": []},
}

contexto = build_valuation_context(
    snapshot,
    velocity_lookup={},
    starter_lookup={5771: TITULAR, 38072: SUPLENTE},
)

# El catalogo de prueba esta vacio, asi que la tarifa se inyecta.
contexto["points_market"] = MERCADO

valor = value_candidate(castrin, contexto)

check(
    "la operacion no se valora como mejora del once",
    (valor.get("as_xi") or {}).get("decision")
    == "NO_MEJORA_TITULARIDAD",
    str((valor.get("as_xi") or {}).get("decision")),
)

check(
    "y por tanto no se propone como XI_UPGRADE",
    valor.get("intent") != "XI_UPGRADE",
    str(valor.get("intent")),
)

check(
    "el motivo dice que el once empeora, no habla de euros",
    "once empeora"
    in ((valor.get("as_xi") or {}).get("reason") or ""),
    str((valor.get("as_xi") or {}).get("reason"))[:120],
)

check(
    "se conservan los 97 puntos brutos para poder explicarlo",
    (valor.get("points") or {}).get("raw_points") == 97,
    str((valor.get("points") or {}).get("raw_points")),
)

check(
    "y los esperados son bastantes menos, por ser suplente",
    (valor.get("points") or {}).get("points", 0) < 97,
    str((valor.get("points") or {}).get("points")),
)


# ================================================================
# 2. LA REGLA NO APAGA LAS MEJORAS BUENAS
# ================================================================


print()
print("2. Titular por titular sigue pasando")
print("-" * 60)


bueno = xi_upgrade_value(
    candidate_points=150,
    replaced_points=60,
    points_market=MERCADO,
    candidate_starter=TITULAR,
    replaced_starter=TITULAR,
)

check(
    "un titular mejor que un titular es una mejora",
    bueno.get("intent") == "XI_UPGRADE" and bueno["value"] > 0,
    str(bueno.get("decision")),
)


sube_de_banquillo = xi_upgrade_value(
    candidate_points=150,
    replaced_points=60,
    points_market=MERCADO,
    candidate_starter=SUPLENTE,
    replaced_starter=SUPLENTE,
)

check(
    "sustituir a un suplente no lo bloquea la regla",
    sube_de_banquillo.get("intent") == "XI_UPGRADE",
    str(sube_de_banquillo.get("decision")),
)


sin_dato = xi_upgrade_value(
    candidate_points=150,
    replaced_points=60,
    points_market=MERCADO,
    candidate_starter=None,
    replaced_starter=TITULAR,
)

# El motivo cambio de nombre el 17/08/2026. Lo que importa es que
# la operacion no se hace: sin saber quien entra, no se toca a un
# titular.
check(
    "sin pronostico del candidato tampoco se toca a un titular",
    sin_dato.get("decision") == "SIN_PRONOSTICO"
    and sin_dato.get("intent") is None,
    str(sin_dato.get("decision")),
)


# ================================================================
# LA REGLA SE DIO LA VUELTA EL 17/08/2026
#
# Este check decia, literalmente, "sin ningun dato de titularidad
# la regla NO se aplica", y comprobaba que la compra salia
# adelante. Era cierto, y era el agujero.
#
# La regla del once solo frenaba cuando SABIA que el sustituido
# era titular. O sea que cuanto menos sabia, mas permitia. Se vio
# al cambiar de fuente: con el tablero vacio bloqueo cero
# operaciones y el sistema propuso tres compras a ciegas, entre
# ellas la de Castrin, que es el caso que abre este mismo fichero.
#
# Ahora la ausencia de dato FRENA. Si la fuente se cae, Pepe deja
# de mejorar el once -que es molesto- en vez de fichar a ciegas
# -que es caro-.
# ================================================================

a_ciegas = xi_upgrade_value(
    candidate_points=150,
    replaced_points=60,
    points_market=MERCADO,
)

check(
    "sin ningun dato de titularidad NO se puja",
    a_ciegas.get("decision") == "SIN_PRONOSTICO"
    and a_ciegas.get("value") == 0,
    str(a_ciegas.get("decision")),
)


# ================================================================
# 3. EL PEOR DE LA POSICION
# ================================================================


print()
print("3. A quien se vende tambien se elige mirando quien juega")
print("-" * 60)


modesto_titular = {
    "id": 1,
    "name": "Titular modesto",
    "position": 2,
    "price": 1_000_000,
    "pointsLastSeason": 40,
    "teamID": 1,
}

bueno_suplente = {
    "id": 2,
    "name": "Mejor historial, banquillo",
    "position": 2,
    "price": 3_000_000,
    "pointsLastSeason": 60,
    "teamID": 2,
}

contexto_plantilla = build_valuation_context(
    {
        "my_team": [modesto_titular, bueno_suplente],
        "catalog": {"data": {"players": {}, "teams": {}}},
        "market": {"sales": []},
    },
    velocity_lookup={},
    starter_lookup={1: TITULAR, 2: SUPLENTE},
)

peor = contexto_plantilla["weakest_by_position"][2]

# Por historial el prescindible seria el titular de 40 puntos:
# 40 < 60. Al mirar quien juega el orden se da la vuelta, que es
# justo lo que antes no pasaba.
check(
    "por historial el peor seria el titular",
    modesto_titular["pointsLastSeason"]
    < bueno_suplente["pointsLastSeason"],
)

check(
    "mirando quien juega, el prescindible es el suplente",
    peor["id"] == 2,
    f"eligio a {peor['name']}",
)

check(
    "y se deja escrito por que",
    peor.get("starter_consensus") == "BENCH"
    and peor.get("raw_points") == 60,
    str(peor),
)


# ================================================================
# 4. EL FACTOR
# ================================================================


print()
print("4. El escalado por titularidad")
print("-" * 60)


check(
    "titular seguro cuenta entero",
    abs(starter_factor(100.0) - 1.0) < 1e-9,
)

check(
    "el que no juega nunca no cuenta cero, cuenta poco",
    abs(starter_factor(0.0) - BENCH_POINTS_FACTOR) < 1e-9,
)

check(
    "sin dato no se escala",
    starter_factor(None) == 1.0,
)

check(
    "es monotono",
    starter_factor(20.0)
    < starter_factor(50.0)
    < starter_factor(80.0),
)

check(
    "aguanta basura",
    starter_factor("no soy un numero") == 1.0
    and starter_factor(500.0) == 1.0,
)

puntos = estimate_season_points(
    castrin, MERCADO, None, starter=SUPLENTE
)

check(
    "97 puntos de suplente se quedan en menos de la mitad",
    puntos["points"] < 49,
    str(puntos["points"]),
)


# ================================================================
# 5. DE DONDE SALE EL PRONOSTICO DEL MERCADO
# ================================================================


print()
print("5. El pronostico de un candidato del mercado")
print("-" * 60)


# ACTUALIZADO EL 17/08/2026
#
# Esta seccion probaba Jornada Perfecta y el consenso multifuente,
# los dos retirados. Ahora hay una sola fuente -FutbolFantasy- y
# cubre mercado y plantilla por igual, asi que lo que hay que
# comprobar ya no es "de donde viene cada uno" sino que el mercado
# llega entero y con jerarquia.

lookup = build_starter_lookup(
    board={
        "players": [
            {
                "player_id": 5771,
                "player_name": "Uno de los nuestros",
                "scope": "ROSTER",
                "starter_probability": 92.2,
                "consensus": "STARTER",
                "source": "FUTBOLFANTASY",
                "source_coverage": 1,
                "hierarchy": {
                    "value": 50,
                    "label": "Clave",
                    "franchise": False,
                },
                "availability": {
                    "code": 0,
                    "label": "DISPONIBLE",
                    "can_play": True,
                },
            },
            {
                "player_id": 38072,
                "player_name": "Uno del mercado",
                "scope": "MARKET",
                "starter_probability": 24.0,
                "consensus": "BENCH",
                "source": "FUTBOLFANTASY",
                "source_coverage": 1,
                "hierarchy": {
                    "value": 20,
                    "label": "Reserva",
                    "franchise": False,
                },
                "availability": {
                    "code": 0,
                    "label": "DISPONIBLE",
                    "can_play": True,
                },
            },
        ]
    },
)

check(
    "un jugador del mercado ya tiene pronostico",
    lookup.get(38072, {}).get("consensus") == "BENCH",
    str(lookup.get(38072)),
)

check(
    "y viene con su jerarquia, que es el dato que aguanta",
    lookup[38072]["hierarchy_label"] == "Reserva"
    and lookup[38072]["hierarchy_value"] == 20,
    str(lookup[38072]),
)

check(
    "el mercado se distingue de la plantilla",
    lookup[38072]["scope"] == "MARKET"
    and lookup[5771]["scope"] == "ROSTER",
)

check(
    "la fuente es unica y se dice cual es",
    lookup[5771]["source"] == "FUTBOLFANTASY"
    and lookup[5771]["probability"] == 92.2,
    str(lookup[5771]),
)

check(
    "los cortes de voto siguen siendo los mismos",
    vote_label(67.0) == "STARTER"
    and vote_label(40.0) == "BENCH"
    and vote_label(55.0) == "UNCERTAIN"
    and vote_label(None) is None,
)

check(
    "un fichero ausente no tumba nada",
    build_starter_lookup(board={}) == {},
)


# ================================================================
# 6. LA IDENTIDAD DEL MERCADO
# ================================================================


print()
print("6. Los candidatos del mercado entran en el emparejamiento")
print("-" * 60)


from src.intelligence.jornada_perfecta_provider import (  # noqa: E402
    build_market_records,
    build_roster_records,
)


snapshot_identidad = {
    "my_team": [
        {"id": 5771, "name": "Yeray", "teamID": 9},
    ],
    "market": {
        "sales": [
            {"player": {"id": 38072}},
            {"player": {"id": 5771}},
            {"player": {"id": 999999}},
            {"player": None},
            "esto no es una venta",
        ]
    },
    "catalog": {
        "data": {
            "players": {
                "38072": {
                    "id": 38072,
                    "name": "Andres Castrin",
                    "teamID": 5,
                },
                "5771": {
                    "id": 5771,
                    "name": "Yeray",
                    "teamID": 9,
                },
            },
            "teams": {
                "5": {"name": "Sevilla"},
                "9": {"name": "Athletic"},
            },
        }
    },
}

mercado = build_market_records(snapshot_identidad)

check(
    "el candidato del mercado entra",
    [r["id"] for r in mercado] == [38072],
    str([r["id"] for r in mercado]),
)

check(
    "con su equipo resuelto, que es lo que ancla el matching",
    mercado[0]["team"] == "Sevilla" and mercado[0]["team_key"],
    str(mercado[0]),
)

check(
    "uno nuestro que esta en venta no se duplica",
    all(r["id"] != 5771 for r in mercado),
)

check(
    "y la plantilla sigue marcada como tal",
    build_roster_records(snapshot_identidad)[0]["scope"]
    == "ROSTER",
)

check(
    "un mercado roto no lanza",
    build_market_records({}) == []
    and build_market_records(
        {"market": {"sales": None}, "catalog": {}}
    )
    == [],
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
