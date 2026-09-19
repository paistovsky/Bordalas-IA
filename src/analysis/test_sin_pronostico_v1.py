"""
Sin pronostico no se entra al XI si hay con pronostico en el puesto.

EL CASO QUE LO DESTAPO

    18/09/2026, jornada 7, cinco horas antes del cierre. El once
    salia con este portero:

        Esquivel   150.000 EUR   0 puntos   0 partidos
                   tercer portero del Atletico, dorsal 25
                   SIN una sola fuente que diga si juega

    Y este en el banquillo:

        Dituro     2.180.000 EUR   6 puntos   6 partidos
                   123 puntos la temporada pasada
                   Importante en el Elche, FutbolFantasy al 50 %

    El motor no se equivocaba de cuentas: las hacia bien y le
    salia eso.

        Esquivel   250.030,15   = 250.000 de suelo + 30,15 de base
        Dituro     235.067,68   = vara 0,2269 x 1.000.000 + extras
        Iturbe     213.230,15   = vara 0,2052 x 1.000.000 + extras

    El suelo de "sin dato" estaba calibrado contra la escalera de
    etiquetas -cuyo peldano mas bajo es 0,25- y dejo de valer
    cuando la vara paso a medirse con puntos reales. Desde ese
    momento, no saber ganaba a saber.

LA DECISION DEL DUEÑO (18/09/2026)

    "Hay que traerlo. Si es fallo de las fuentes, tenemos a
    Dituro y ya esta."

    Un jugador sin pronostico NO entra en el XI si hay uno con
    pronostico en su puesto. Sin dato no es cero -no se le
    declara inalineable- pero tampoco es una apuesta: es el
    ULTIMO RECURSO.

QUE SE COMPRUEBA AQUI

    1. Con los numeros reales de aquel dia, el portero es Dituro
       y no Esquivel.
    2. El ultimo recurso sigue siendo un recurso: si no hay otro
       portero, el que no tiene pronostico juega. La porteria no
       se deja vacia.
    3. El score cae por debajo de cualquiera con pronostico y se
       queda por encima del -1.000.000 del que no se puede
       alinear. Ni se cuela por arriba ni se confunde por abajo.
    4. No se inventa vara: `weekly_expected_value` viaja a None.
       Ni 0,25 ni 0,0.
    5. El banquillo dice el motivo de verdad -SIN_PRONOSTICO- y
       no "puntua menos", que seria mentir sobre la comparacion.

LA GUARDIA MUERDE CON EL TABLERO VACIO

    Es la trampa de este test concreto. Si el tablero de
    titularidad llega vacio, TODOS son "sin pronostico", nadie
    desplaza a nadie y las cinco comprobaciones de arriba pasan
    sin haber probado nada.

    Por eso lo primero que se comprueba es que el banco de
    pruebas tiene de verdad a alguien con pronostico. Con el
    tablero vacio esta guardia FALLA, no pasa.

DE DONDE SALEN LOS NUMEROS

    Fijos, escritos aqui. No se lee el estado de produccion, no
    se sale a la red y no se mira el reloj: esta guardia tiene
    que dar lo mismo hoy que en enero.
"""

import sys

sys.path.insert(0, ".")

from src.analysis.lineup_engine import (  # noqa: E402
    suelo_sin_pronostico,
    banquillo_con_motivo,
    prepare_players,
    search_best_lineup_for_formation,
)


fallos = []


def check(nombre, condicion, detalle=""):
    if condicion:
        print(f"  OK   {nombre}")
    else:
        print(f"  FALLA {nombre} {detalle}")
        fallos.append(nombre)


# ================================================================
# EL BANCO DE PRUEBAS
# ================================================================
#
# Los tres porteros de la plantilla el 18/09/2026, con el precio,
# los puntos y los puntos de la temporada pasada que tenian en la
# foto de las 15:16. No hace falta mas: la regla se juega dentro
# de una sola posicion.

#
# LOS PARTIDOS JUGADOS NO SON DECORADO
#
#     `calidad_para_la_vara` mide puntos POR PARTIDO JUGADO. Sin
#     `played_home`/`played_away` no hay medicion, manda la
#     etiqueta, y Dituro sale a 0,54 de vara en vez de a 0,227.
#     Con esa vara nunca perdio contra el suelo y el fallo del
#     18/09 no se reproduce: el test pasaria antes y despues del
#     arreglo, que es la peor clase de guardia.
#
#     Por eso mas abajo se comprueba, numero a numero, que este
#     banco reproduce la foto de aquel dia.

ESQUIVEL = {
    "id": 43281,
    "name": "Esquivel",
    "position": 1,
    "price": 150_000,
    "points": 0,
    "played_home": 0,
    "played_away": 0,
    "pointsLastSeason": 0,
    "status": "ok",
}

DITURO = {
    "id": 17482,
    "name": "Dituro",
    "position": 1,
    "price": 2_180_000,
    "points": 6,
    "played_home": 3,
    "played_away": 3,
    "pointsLastSeason": 123,
    "status": "ok",
}

ITURBE = {
    "id": 37526,
    "name": "Iturbe",
    "position": 1,
    "price": 150_000,
    "points": 0,
    "played_home": 0,
    "played_away": 0,
    "pointsLastSeason": 0,
    "status": "ok",
}


# Los scores que tenian los tres en la foto de las 15:16 del
# 18/09/2026, tal cual salieron publicados.
FOTO = {
    "Esquivel": 250_030.15,     # con el suelo viejo de 250.000
    "Dituro": 235_067.68,
    "Iturbe": 213_230.15,
}


# El suelo que habia antes del arreglo. Se conserva aqui, y solo
# aqui, para poder demostrar que el fallo era real.
SUELO_VIEJO = 250_000.0


def tablero(*filas) -> dict:
    """El tablero de titularidad, con la forma que lee el motor."""

    return {"players": list(filas)}


def fila(player_id, probabilidad, jerarquia=None):

    return {
        "player_id": player_id,
        "starter_probability": probabilidad,
        "consensus": "UNCERTAIN",
        "source_coverage": 1,
        "hierarchy": jerarquia,
    }


# Dituro e Iturbe tienen pronostico; Esquivel no aparece. Las
# jerarquias son las que publicaba FutbolFantasy aquel dia.
TABLERO_REAL = tablero(
    fila(17482, 50.0, {"value": 40, "label": "Importante"}),
    fila(37526, 50.0, {"value": 20, "label": "Reserva"}),
)


PORTERIA = {1: 1}


def preparar(plantilla, board):

    return prepare_players(
        {"my_team": list(plantilla)},
        None,
        board,
    )


def por_nombre(preparados) -> dict:

    return {p["name"]: p for p in preparados}


# ================================================================
# 0. EL BANCO DE PRUEBAS SIRVE
# ================================================================
#
# Si esto falla, lo de abajo no prueba nada: con el tablero vacio
# nadie tiene pronostico, nadie desplaza a nadie y las cinco
# comprobaciones pasarian por vacuidad.

print()
print("0. El banco de pruebas tiene a alguien con pronostico")

preparados = preparar([ESQUIVEL, DITURO, ITURBE], TABLERO_REAL)

fichas = por_nombre(preparados)

check(
    "el tablero de la prueba NO llega vacio",
    len(TABLERO_REAL["players"]) > 0,
    f"(filas={len(TABLERO_REAL['players'])})",
)

check(
    "Dituro entra al motor CON pronostico",
    fichas["Dituro"]["starter_probability"] is not None
    and fichas["Dituro"]["starter_source_coverage"] > 0,
    f"(prob={fichas['Dituro']['starter_probability']}, "
    f"cob={fichas['Dituro']['starter_source_coverage']})",
)

check(
    "Esquivel entra al motor SIN pronostico",
    fichas["Esquivel"]["starter_probability"] is None
    and fichas["Esquivel"]["sin_pronostico"] is True,
    f"(prob={fichas['Esquivel']['starter_probability']}, "
    f"bandera={fichas['Esquivel'].get('sin_pronostico')})",
)

check(
    "los tres son alineables: el corte no es la disponibilidad",
    all(
        fichas[nombre]["lineup_eligible"]
        for nombre in ("Esquivel", "Dituro", "Iturbe")
    ),
)


# LA TRAMPA, PROBADA DESDE DENTRO
#
#     Con el tablero vacio -que es lo que sirve
#     `build_starter_lookup` cuando lo rechaza por ser de otra
#     jornada- NADIE tiene pronostico. Entonces nadie desplaza a
#     nadie, el once se elige por valor y puntos, y las cinco
#     comprobaciones de abajo pasarian sin haber probado nada.
#
#     Aqui se comprueba que la reja de arriba se cierra: con el
#     tablero vacio, la condicion de "Dituro entra CON
#     pronostico" es falsa, y esta guardia se cae en vez de
#     pasar.

vacio = por_nombre(preparar([ESQUIVEL, DITURO, ITURBE], tablero()))

check(
    "con el tablero VACIO nadie tiene pronostico",
    all(
        vacio[nombre]["starter_probability"] is None
        and vacio[nombre]["sin_pronostico"] is True
        for nombre in ("Esquivel", "Dituro", "Iturbe")
    ),
    f"(Dituro prob={vacio['Dituro']['starter_probability']})",
)

check(
    "y por eso la reja de esta guardia se cierra sobre el vacio",
    not (
        vacio["Dituro"]["starter_probability"] is not None
        and vacio["Dituro"]["starter_source_coverage"] > 0
    ),
)


# ================================================================
# 0 bis. Y REPRODUCE EL FALLO DE AQUEL DIA
# ================================================================
#
# La otra forma de pasar con las manos vacias: un banco de
# pruebas en el que Esquivel nunca habria ganado. Si los dos con
# pronostico no salen EXACTAMENTE con los scores de la foto, este
# test no esta probando el fallo del 18/09 sino otro parecido, y
# entonces no vale.
#
# Ojo con `BORDALAS_CALIDAD_ETIQUETA`: apagar la calidad medida
# devuelve a Dituro a 0,54 de vara, muy por encima del suelo
# viejo. Aqui se cae, que es lo que tiene que pasar.

print()
print("0 bis. El banco reproduce la foto del 18/09/2026")

for nombre in ("Dituro", "Iturbe"):

    check(
        f"{nombre} sale con el score de la foto",
        abs(fichas[nombre]["lineup_score"] - FOTO[nombre]) < 0.01,
        f"(calculado={fichas[nombre]['lineup_score']:.2f}, "
        f"foto={FOTO[nombre]:.2f})",
    )

# Con el suelo viejo, Esquivel valia 250.000 mas su base. Su base
# no ha cambiado con el arreglo: solo el suelo. Asi se recupera el
# numero de la foto sin tener que conservar el codigo viejo.
base_esquivel = (
    fichas["Esquivel"]["lineup_score"] - suelo_sin_pronostico()
)

esquivel_con_suelo_viejo = SUELO_VIEJO + base_esquivel

check(
    "Esquivel con el suelo viejo sale con el score de la foto",
    abs(esquivel_con_suelo_viejo - FOTO["Esquivel"]) < 0.01,
    f"(calculado={esquivel_con_suelo_viejo:.2f}, "
    f"foto={FOTO['Esquivel']:.2f})",
)

check(
    "y con ese suelo ganaba a los dos: el fallo era real",
    esquivel_con_suelo_viejo > fichas["Dituro"]["lineup_score"]
    and esquivel_con_suelo_viejo > fichas["Iturbe"]["lineup_score"],
    f"(Esquivel={esquivel_con_suelo_viejo:.2f}, "
    f"Dituro={fichas['Dituro']['lineup_score']:.2f}, "
    f"Iturbe={fichas['Iturbe']['lineup_score']:.2f})",
)


# ================================================================
# 1. EL PORTERO ES DITURO
# ================================================================

print()
print("1. El sin-dato no desplaza al que si tiene pronostico")

elegido = search_best_lineup_for_formation(preparados, PORTERIA)

porteros = [p["name"] for p in elegido["selected"]]

check(
    "la porteria se llena",
    elegido["filled"] == 1,
    f"(filled={elegido['filled']})",
)

check(
    "el portero NO es Esquivel",
    "Esquivel" not in porteros,
    f"(elegido={porteros})",
)

check(
    "el portero es Dituro",
    porteros == ["Dituro"],
    f"(elegido={porteros})",
)


# ================================================================
# 2. EL ULTIMO RECURSO SIGUE SIENDO UN RECURSO
# ================================================================

print()
print("2. Sin alternativa, el sin-dato juega")

solo = preparar([ESQUIVEL], tablero())

solo_elegido = search_best_lineup_for_formation(solo, PORTERIA)

check(
    "con un solo portero y sin dato, la porteria NO se deja vacia",
    solo_elegido["filled"] == 1
    and [p["name"] for p in solo_elegido["selected"]] == ["Esquivel"],
    f"(filled={solo_elegido['filled']}, "
    f"elegido={[p['name'] for p in solo_elegido['selected']]})",
)

check(
    "y sigue siendo alineable, no un -1.000.000",
    solo[0]["lineup_eligible"] is True
    and solo[0]["lineup_score"] > -1_000_000.0,
    f"(score={solo[0]['lineup_score']})",
)


# ================================================================
# 3. LA BANDA DEL SCORE
# ================================================================

print()
print("3. El score cae en su banda y no se sale por ningun lado")

esquivel = fichas["Esquivel"]
dituro = fichas["Dituro"]
iturbe = fichas["Iturbe"]

check(
    "el sin-dato puntua por debajo de los dos con pronostico",
    esquivel["lineup_score"] < dituro["lineup_score"]
    and esquivel["lineup_score"] < iturbe["lineup_score"],
    f"(Esquivel={esquivel['lineup_score']:.2f}, "
    f"Dituro={dituro['lineup_score']:.2f}, "
    f"Iturbe={iturbe['lineup_score']:.2f})",
)

check(
    "y por encima del -1.000.000 del que no se puede alinear",
    esquivel["lineup_score"] > -1_000_000.0,
    f"(score={esquivel['lineup_score']:.2f})",
)

check(
    "el suelo viejo de 250.000 ya no existe",
    esquivel["lineup_score"] < 250_000.0
    and suelo_sin_pronostico() < 0,
    f"(score={esquivel['lineup_score']:.2f}, "
    f"suelo={suelo_sin_pronostico()})",
)

# El peor con pronostico posible: cobertura 1 y nada mas. Si
# alguien baja la cobertura o sube el suelo hasta cruzarse, esto
# lo canta antes de que lo cante el once.
check(
    "queda holgura contra el peor con pronostico imaginable",
    esquivel["lineup_score"] < 2_500.0,
    f"(score={esquivel['lineup_score']:.2f})",
)


# ================================================================
# 4. NO SE INVENTA PRONOSTICO
# ================================================================

print()
print("4. Sin dato es sin dato: ni 0,25 ni 0,0")

check(
    "la vara del sin-dato viaja a None",
    esquivel["weekly_expected_value"] is None,
    f"(vara={esquivel['weekly_expected_value']})",
)

check(
    "no se le inventa jerarquia ni consenso",
    esquivel["hierarchy"] in (None, {})
    and esquivel["starter_consensus"] is None,
    f"(jerarquia={esquivel['hierarchy']}, "
    f"consenso={esquivel['starter_consensus']})",
)

check(
    "al que SI lo tiene no se le toca la vara",
    dituro["weekly_expected_value"] is not None
    and dituro["weekly_expected_value"] > 0,
    f"(vara={dituro['weekly_expected_value']})",
)


# ================================================================
# 5. EL BANQUILLO DICE EL MOTIVO DE VERDAD
# ================================================================

print()
print("5. El banquillo no dice 'puntua menos'")

banquillo = banquillo_con_motivo(preparados, elegido["selected"])

suplentes = {f["name"]: f for f in banquillo}

check(
    "Esquivel esta en el banquillo con motivo SIN_PRONOSTICO",
    suplentes["Esquivel"]["reason"] == "SIN_PRONOSTICO",
    f"(motivo={suplentes['Esquivel']['reason']})",
)

check(
    "el motivo nombra a quien si tiene pronostico",
    "Dituro" in (suplentes["Esquivel"]["reason_text"] or ""),
    f"(frase={suplentes['Esquivel']['reason_text']!r})",
)

check(
    "no se publica una vara inventada en la ficha del banquillo",
    suplentes["Esquivel"]["weekly_expected_value"] is None,
    f"(vara={suplentes['Esquivel']['weekly_expected_value']})",
)

check(
    "al que si puntua menos se le sigue diciendo que puntua menos",
    suplentes["Iturbe"]["reason"] == "PUNTUA_MENOS",
    f"(motivo={suplentes['Iturbe']['reason']})",
)


# ================================================================
# 6. Y LA COLA DE VENTA SE DA LA VUELTA
# ================================================================
#
# EL PAR INVERTIDO (18/09/2026)
#
#     El fallo no solo sentaba a Dituro. Como `untouchable_reason`
#     protege al portero TITULAR -y el titular era Esquivel-, la
#     foto de las 16:16 tenia esto:
#
#         Dituro     segundo de la cola de venta
#                    motivo: "cae de precio y ademas no juega"
#
#         Esquivel   el UNICO apartado de la venta
#                    motivo: "sin escalon conocido"
#
#     El portero con 123 puntos la temporada pasada, en venta. El
#     que no tiene ni una fuente, protegido. Perder puntos era lo
#     de menos: se estaba ofreciendo al portero bueno.
#
#     Con el arreglo, Dituro vuelve al once, `is_starter` se le
#     pone a el y la proteccion de portero titular le sigue.

print()
print("6. El par invertido se endereza")

from src.analysis.sale_order import build_sale_order  # noqa: E402


def ficha_de_venta(player, titular):
    """La ficha como la publica el roster, con el XI de turno."""

    starter = TABLERO_REAL["players"]

    escalon = next(
        (
            (f.get("hierarchy") or {}).get("value")
            for f in starter
            if f["player_id"] == player["id"]
        ),
        None,
    )

    return {
        "id": player["id"],
        "name": player["name"],
        "position": player["position"],
        "price": player["price"],
        "points": player["points"],
        "price_increment": -20_000,
        "hierarchy_value": escalon,
        "is_starter": titular,
    }


def cola_con_portero(portero_id):

    roster = [
        ficha_de_venta(p, p["id"] == portero_id)
        for p in (ESQUIVEL, DITURO, ITURBE)
    ]

    return build_sale_order(roster, lineup_ids=[portero_id])


antes = cola_con_portero(ESQUIVEL["id"])

despues = cola_con_portero(DITURO["id"])

check(
    "el banco reproduce el par invertido de aquel dia",
    "Dituro" in [q["name"] for q in antes["queue"]]
    and "Esquivel" in [e["name"] for e in antes["excluded"]],
    f"(cola={[q['name'] for q in antes['queue']]}, "
    f"apartados={[e['name'] for e in antes['excluded']]})",
)

check(
    "con el arreglo, Dituro SALE de la cola de venta",
    "Dituro" not in [q["name"] for q in despues["queue"]],
    f"(cola={[q['name'] for q in despues['queue']]})",
)

check(
    "y queda apartado por ser el portero titular",
    any(
        e["name"] == "Dituro" and "portero" in e["reason"].lower()
        for e in despues["excluded"]
    ),
    f"(apartados={[(e['name'], e['reason']) for e in despues['excluded']]})",
)

# Esquivel sigue sin venderse, y esta bien: no se vende a ciegas a
# quien no se puede valorar. Lo que cambia es que ya no es por
# ser el portero titular.
check(
    "Esquivel sigue sin venderse, pero ya no por ser el titular",
    any(
        e["name"] == "Esquivel" and "escalon" in e["reason"].lower()
        for e in despues["excluded"]
    ),
    f"(apartados={[(e['name'], e['reason']) for e in despues['excluded']]})",
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
