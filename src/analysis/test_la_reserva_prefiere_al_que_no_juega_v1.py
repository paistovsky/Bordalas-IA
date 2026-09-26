"""
La reserva de solvencia guarda primero al que no juega.

EL CASO (25-26/09/2026)

    La reserva guardo la oferta por Ruben Garcia, titular, y a la
    01:13 -primer ciclo a menos de 6 h de caducar- se cobro sola. El
    orden de la reserva era franquicia, estrategica, prima e importe:
    ninguno pregunta quien juega.

    Medido reproduciendo la reserva sobre las 96 fotos locales: en 4
    de 5 episodios con deficit metio a un titular teniendo ofertas de
    suplentes que tapaban la deuda.

QUE COMPRUEBA

    0. El caso trae UNA oferta de un titular y UNA de un suplente,
       del mismo importe. Si no, esto no prueba nada y se pone roja.
    1. Con el interruptor, la reserva guarda la del suplente.
    2. Sin el -y sin cartera- guarda la del titular, como antes: la
       diferencia es el interruptor, no el caso. La del titular tiene
       mejor prima a proposito, para que el orden viejo la elija.
    3. El aviso: sale para la reservada del titular, con los cuatro
       datos -quien, por cuanto, cuanto once cuesta, la alternativa y
       lo que cuesta ella-; no sale para la del suplente; la
       alternativa no usa ofertas ya reservadas ni intocables.
    4. El aviso dice cuando entra en la ventana, y la ventana es la
       del motor de reroll, no un numero de aqui.
    5. Nada lanza con basura.
    6. El interruptor se lee al llamar, y nace apagado.

DE DONDE SALEN LOS NUMEROS

    Fijos, escritos aqui. Ni `data/`, ni red, ni reloj, ni libros. El
    interruptor se pasa como parametro; donde se lee del entorno, lo
    pone y lo quita esta misma guardia.
"""

import os
import sys

sys.path.insert(0, ".")

from src.analysis.computer_offer_reroll_engine import (  # noqa: E402
    ACCEPT_BEFORE_DEADLINE_HOURS,
    ACCEPT_BEFORE_EXPIRY_HOURS,
)
from src.analysis.la_reserva_mira_el_once import (  # noqa: E402
    LA_RESERVA_MIRA_EL_ONCE_ENV,
    las_ventas_de_titular,
    mira_el_once,
    ordenar_por_puntos_por_euro,
    ventana_de_cobro,
)
from src.analysis.safe_debt_portfolio_engine import (  # noqa: E402
    _build_position_index,
    _project_lineup_fast,
)
from src.analysis.solvency_engine import (  # noqa: E402
    calculate_offer_reservations,
)


fallos = []


def check(nombre, condicion, detalle=""):
    if condicion:
        print(f"  OK   {nombre}")
    else:
        print(f"  FALLA {nombre} {detalle}")
        fallos.append(nombre)


# ================================================================
# EL BANCO
# ================================================================
#
#     Un once de 3-4-3 con el delantero 1 muy por encima de todos:
#     juega en cualquier formacion. Y un segundo portero: en ninguna
#     formacion caben dos.

TITULAR = 101      # el delantero 1
SUPLENTE = 202     # el portero 2
OTRO = 303         # un medio del banquillo, para la alternativa


def jugador(i, pos, score, nombre=None):
    return {
        "id": i,
        "name": nombre or f"J{i}",
        "position": pos,
        "lineup_score": float(score),
        "lineup_score_sporting": float(score),
    }


PLANTILLA = [
    jugador(1, 1, 50),
    jugador(SUPLENTE, 1, 5, "Portero 2"),
    *[jugador(10 + k, 2, 40) for k in range(3)],
    *[jugador(20 + k, 3, 40) for k in range(4)],
    jugador(OTRO, 3, 1, "Medio suplente"),
    jugador(TITULAR, 4, 200, "Delantero titular"),
    jugador(31, 4, 30),
    jugador(32, 4, 30),
    jugador(33, 4, 10),
]

CARTERA = {"plantilla_del_once": PLANTILLA}

IMPORTE = 1_000_000
SALDO = -600_000
GARANTIA = {"required_recovery": 600_000, "expected_liquidity": 0}


def oferta(offer_id, jugador_id, nombre, importe, prima, horas=100.0):
    return {
        "offer_id": offer_id,
        "amount": importe,
        "premium_percent": prima,
        "hours_to_expiry": horas,
        "player_ids": [jugador_id],
        "players": [
            {"name": nombre, "franchise_score": 0.0, "strategic_score": 0.0}
        ],
    }


# La del titular con MEJOR prima: el orden viejo la elige primero.
DEL_TITULAR = oferta(1, TITULAR, "Delantero titular", IMPORTE, 4.0, horas=10.0)
DEL_SUPLENTE = oferta(2, SUPLENTE, "Portero 2", IMPORTE, 1.0)
DEL_OTRO = oferta(3, OTRO, "Medio suplente", 400_000, 0.5)

OFERTAS = [DEL_TITULAR, DEL_SUPLENTE]

TITULARES = set(
    _project_lineup_fast(_build_position_index(PLANTILLA), set())["selected_ids"]
)


# ================================================================
# 0. EL CASO TRAE UNA DE CADA
# ================================================================

print()
print("0. El caso trae una oferta de un titular y una de un suplente")


def es_titular(o):
    return bool(set(o["player_ids"]) & TITULARES)


de_titular = [o for o in OFERTAS if es_titular(o)]
de_suplente = [o for o in OFERTAS if not es_titular(o)]

check(
    "una oferta de un titular",
    len(de_titular) == 1,
    f"(n={len(de_titular)}, titulares={sorted(TITULARES)})",
)
check(
    "una oferta de un suplente",
    len(de_suplente) == 1,
    f"(n={len(de_suplente)})",
)
check(
    "del mismo importe",
    DEL_TITULAR["amount"] == DEL_SUPLENTE["amount"],
)
check(
    "y cualquiera de las dos tapa la deuda sola",
    IMPORTE >= -SALDO,
)


# ================================================================
# 1. CON EL INTERRUPTOR, SE GUARDA LA DEL SUPLENTE
# ================================================================

print()
print("1. Con el interruptor, la reserva guarda la del suplente")

encendido = calculate_offer_reservations(
    balance=SALDO,
    incoming={"offers": [dict(o) for o in OFERTAS]},
    guarantee=GARANTIA,
    portfolio=CARTERA,
    mira_el_once=True,
)

check(
    "guarda solo una",
    len(encendido["reserved_offer_ids"]) == 1,
    f"({encendido['reserved_offer_ids']})",
)
check(
    "y es la del suplente",
    encendido["reserved_offer_ids"] == [DEL_SUPLENTE["offer_id"]],
    f"({encendido['reserved_offer_ids']})",
)
check(
    "y dice con que orden eligio",
    encendido.get("orden") == "PUNTOS_DEL_ONCE_POR_EURO",
    f"({encendido.get('orden')})",
)

filas = ordenar_por_puntos_por_euro(OFERTAS, PLANTILLA)

check(
    "el orden pone al suplente primero, a coste cero",
    [f["offer_id"] for f in filas] == [2, 1]
    and filas[0]["once_perdido_pct"] == 0.0
    and filas[1]["once_perdido_pct"] > 0.0,
    f"({filas})",
)


# ================================================================
# 2. SIN EL INTERRUPTOR, O SIN CARTERA, EL ORDEN DE SIEMPRE
# ================================================================

print()
print("2. Apagado, o sin cartera, guarda la del titular como antes")

apagado = calculate_offer_reservations(
    balance=SALDO,
    incoming={"offers": [dict(o) for o in OFERTAS]},
    guarantee=GARANTIA,
    portfolio=CARTERA,
    mira_el_once=False,
)

check(
    "apagado guarda la del titular (mejor prima)",
    apagado["reserved_offer_ids"] == [DEL_TITULAR["offer_id"]],
    f"({apagado['reserved_offer_ids']})",
)
check(
    "y dice que eligio por el orden de siempre",
    apagado.get("orden") == "FRANQUICIA",
    f"({apagado.get('orden')})",
)

sin_cartera = calculate_offer_reservations(
    balance=SALDO,
    incoming={"offers": [dict(o) for o in OFERTAS]},
    guarantee=GARANTIA,
    portfolio=None,
    mira_el_once=True,
)

check(
    "encendido pero sin cartera, tambien el orden de siempre",
    sin_cartera["reserved_offer_ids"] == [DEL_TITULAR["offer_id"]]
    and sin_cartera.get("orden") == "FRANQUICIA",
    f"({sin_cartera['reserved_offer_ids']}, {sin_cartera.get('orden')})",
)


# ================================================================
# 3. EL AVISO, CON SUS CUATRO DATOS
# ================================================================

print()
print("3. El aviso de venta de titular")

avisos = las_ventas_de_titular(
    reservadas=[DEL_TITULAR],
    ofertas=[DEL_TITULAR, DEL_SUPLENTE, DEL_OTRO],
    plantilla=PLANTILLA,
    titulares=TITULARES,
    ventana=6.0,
)

check("sale un aviso", len(avisos) == 1, f"(n={len(avisos)})")

aviso = avisos[0] if avisos else {}
alternativa = aviso.get("alternativa") or {}

check("dice quien", aviso.get("quien") == "Delantero titular", f"({aviso.get('quien')})")
check("dice por cuanto", aviso.get("por_cuanto") == IMPORTE)
check(
    "dice cuanto once cuesta, y no es cero",
    (aviso.get("once_perdido_pct") or 0) > 0,
    f"({aviso.get('once_perdido_pct')})",
)
check(
    "trae la alternativa que junta el mismo dinero",
    alternativa.get("junta") is True
    and alternativa.get("importe", 0) >= IMPORTE,
    f"({alternativa})",
)
check(
    "y lo que cuesta ella: cero, porque son suplentes",
    alternativa.get("once_perdido_pct") == 0.0,
    f"({alternativa.get('once_perdido_pct')})",
)
check(
    "la alternativa no usa la propia oferta reservada",
    DEL_TITULAR["offer_id"] not in (alternativa.get("ofertas") or []),
)
check(
    "y el texto lleva los cuatro datos",
    all(
        trozo in (aviso.get("texto") or "")
        for trozo in ("Delantero titular", "1.000.000", "% del once", "Alternativa")
    ),
    f"({aviso.get('texto')})",
)

sin_aviso = las_ventas_de_titular(
    reservadas=[DEL_SUPLENTE],
    ofertas=OFERTAS,
    plantilla=PLANTILLA,
    titulares=TITULARES,
    ventana=6.0,
)

check(
    "guardar a un suplente no avisa",
    sin_aviso == [],
    f"({sin_aviso})",
)

todo_reservado = las_ventas_de_titular(
    reservadas=[DEL_TITULAR, DEL_SUPLENTE, DEL_OTRO],
    ofertas=[DEL_TITULAR, DEL_SUPLENTE, DEL_OTRO],
    plantilla=PLANTILLA,
    titulares=TITULARES,
    ventana=6.0,
)

check(
    "si todo esta reservado, no hay alternativa y lo dice",
    len(todo_reservado) == 1
    and todo_reservado[0]["alternativa"]["junta"] is False
    and "Sin alternativa" in todo_reservado[0]["texto"],
    f"({todo_reservado})",
)

con_intocable = las_ventas_de_titular(
    reservadas=[DEL_TITULAR],
    ofertas=[DEL_TITULAR, DEL_SUPLENTE, DEL_OTRO],
    plantilla=PLANTILLA,
    titulares=TITULARES,
    intocables=[SUPLENTE],
    ventana=6.0,
)

check(
    "un intocable no entra en la alternativa",
    len(con_intocable) == 1
    and DEL_SUPLENTE["offer_id"]
    not in con_intocable[0]["alternativa"]["ofertas"]
    and con_intocable[0]["alternativa"]["junta"] is False,
    f"({con_intocable})",
)


# ================================================================
# 4. CUANDO ENTRA EN LA VENTANA
# ================================================================

print()
print("4. Cuando entra en la ventana de cobro")

check(
    "a 10 h de caducar, entra en la ventana dentro de 4 h",
    aviso.get("horas_para_el_cobro") == 4.0
    and aviso.get("en_la_ventana") is False,
    f"({aviso.get('horas_para_el_cobro')}, {aviso.get('en_la_ventana')})",
)

dentro = las_ventas_de_titular(
    reservadas=[dict(DEL_TITULAR, hours_to_expiry=5.0)],
    ofertas=OFERTAS,
    plantilla=PLANTILLA,
    titulares=TITULARES,
    ventana=6.0,
)

check(
    "a 5 h, ya esta dentro",
    len(dentro) == 1 and dentro[0]["en_la_ventana"] is True,
    f"({dentro})",
)

por_el_plazo = las_ventas_de_titular(
    reservadas=[DEL_TITULAR],
    ofertas=OFERTAS,
    plantilla=PLANTILLA,
    titulares=TITULARES,
    horas_al_plazo=7.0,
    ventana=6.0,
)

check(
    "si el plazo de la jornada llega antes, manda el plazo",
    len(por_el_plazo) == 1 and por_el_plazo[0]["horas_para_el_cobro"] == 1.0,
    f"({por_el_plazo})",
)

check(
    "la ventana es la del motor de reroll, que es quien cobra",
    ventana_de_cobro()
    == min(ACCEPT_BEFORE_EXPIRY_HOURS, ACCEPT_BEFORE_DEADLINE_HOURS),
    f"({ventana_de_cobro()})",
)


# ================================================================
# 5. NADA LANZA CON BASURA
# ================================================================

print()
print("5. Con basura no lanza")

try:
    basura = [
        las_ventas_de_titular(None, None, None, None),
        las_ventas_de_titular([{"offer_id": 1, "player_ids": ["x"]}], [None], [{}], ["y"]),
        ordenar_por_puntos_por_euro(None, None),
        ordenar_por_puntos_por_euro([{"amount": "no"}], [{"id": "z"}]),
    ]
    check("nunca lanza", all(isinstance(b, list) for b in basura), f"({basura})")
except Exception as error:                          # noqa: BLE001
    check("nunca lanza", False, f"({type(error).__name__}: {error})")


# ================================================================
# 6. EL INTERRUPTOR SE LEE AL LLAMAR, Y NACE APAGADO
# ================================================================

print()
print("6. El interruptor")

antes = os.environ.pop(LA_RESERVA_MIRA_EL_ONCE_ENV, None)
try:
    check("sin el en el entorno, apagado", mira_el_once() is False)
    os.environ[LA_RESERVA_MIRA_EL_ONCE_ENV] = "1"
    check("puesto a 1, encendido, sin reimportar", mira_el_once() is True)
finally:
    os.environ.pop(LA_RESERVA_MIRA_EL_ONCE_ENV, None)
    if antes is not None:
        os.environ[LA_RESERVA_MIRA_EL_ONCE_ENV] = antes


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
