"""
La regla de compra: no se revende a quien no va a jugar.

DE DONDE SALE (22/09/2026)

    Emparejando cada compra con su venta en el tablon de los ocho
    managers, el beneficio de un viaje es el MOVIMIENTO DEL
    MERCADO: +10.690.000 de los 13.072.324 de Pollo17. Y el
    mercado se mueve CERO para el que no juega.

    De las seis filas en que se parten sus 91 viajes, la unica
    que pierde dinero es "habia partido y no jugo": n=6, 33 % en
    verde, ROI mediano -2,03 %.

LO QUE SE PROTEGE

    1. QUE UN CANDIDATO SIN PRONOSTICO NO GENERE PUJA DE REVENTA.
       Es la guardia que pidio el encargo.
    2. Que el suplente tampoco.
    3. Que el titular SI siga pujando -sin esto, la regla seria
       un interruptor de apagado con otro nombre-.
    4. Que apagada no cambie ni una puja.
    5. Que el umbral sea el de la casa y no uno nuevo.
    6. Que la lectura del estado lleve los campos que la regla
       mira.
    7. Que la forma no cambie con los datos.
    8. Y las dos piezas de las que cuelga la tabla de viajes: la
       reja de reemisiones y el emparejamiento FIFO.

ESTAS GUARDIAS NO LEEN EL MUNDO

    Ni `data/`, ni red, ni reloj: todo se pasa. La unica que toca
    el entorno es la del interruptor -que ES una variable de
    entorno- y lo deja como estaba.

COMO SE USA

    python -m src.analysis.test_la_regla_de_compra_v1
"""

from __future__ import annotations

import os


# EL ENTORNO NO DECIDE ESTA GUARDIA (doctrina 104)
#
#     `BORDALAS_SIN_SUBASTA` cierra `plan_del_reset` entero, y
#     esta guardia mide justo lo que pasa dentro. Con ese
#     interruptor puesto en el `env` del workflow se pondria roja
#     sin que nada estuviera roto.
os.environ.pop("BORDALAS_SIN_SUBASTA", None)
os.environ.pop("BORDALAS_REVENTA_SOLO_SI_JUEGA", None)

import json                                         # noqa: E402

from src.analysis.deployment import (                # noqa: E402
    MIN_HIERARCHY_VALUE,
    MIN_STARTER_PERCENT,
    roster_fill_veto,
)
from src.analysis.la_regla_de_compra import (        # noqa: E402
    ENV as REGLA_ENV,
    mira_si_va_a_jugar,
    por_que_no,
)
from src.analysis.la_subasta import (                # noqa: E402
    lectura_del_estado,
    plan_del_reset,
)


PRIMA = 0.0187


class _Interruptor:
    """Pone y quita una variable, y la deja como estaba."""

    def __init__(self, nombre, valor="1"):
        self.nombre = nombre
        self.valor = valor

    def __enter__(self):
        self.antes = os.environ.get(self.nombre)
        os.environ[self.nombre] = self.valor
        return self

    def __exit__(self, *_):
        if self.antes is None:
            os.environ.pop(self.nombre, None)
        else:
            os.environ[self.nombre] = self.antes
        return False


def _titular(i=0) -> dict:
    """Un candidato del que consta que juega."""

    return {
        "id": 100 + i,
        "name": f"Titular {i}",
        "market_price": 1_000_000 + 10_000 * i,
        "team_id": 50 + i,
        "starter_probability": 80.0,
        "hierarchy_value": 60,
    }


def _sin_pronostico(i=0) -> dict:
    """Uno del que NO consta si va a jugar. No es un suplente."""

    return {
        "id": 200 + i,
        "name": f"Sin pronostico {i}",
        "market_price": 1_000_000 + 10_000 * i,
        "team_id": 70 + i,
        "starter_probability": None,
        "hierarchy_value": None,
    }


def _suplente(i=0) -> dict:

    return {
        "id": 300 + i,
        "name": f"Suplente {i}",
        "market_price": 1_000_000 + 10_000 * i,
        "team_id": 80 + i,
        "starter_probability": 20.0,
        "hierarchy_value": 20,
    }


def _plan(candidatos, **cambios) -> dict:

    argumentos = {
        "candidatos": candidatos,
        "prima_de_reventa": PRIMA,
        "presupuesto": 20_000_000,
        "fichas_libres": 10,
        "caja_libre": 10_000_000,
        "seconds_to_reset": 300,
        "solvency_clock": {"state": "SIN_DEUDA", "deficit": 0},
        "plantilla": [],
        "bloqueo_temporal": None,
        "en_vivo": True,
        "max_por_club": 4,
    }

    argumentos.update(cambios)

    return plan_del_reset(**argumentos)


# ============================================================
# 1. LA QUE PIDIO EL ENCARGO
# ============================================================

def test_la_regla_de_compra_mira_si_va_a_jugar():
    """
    Con el interruptor puesto, un candidato SIN PRONOSTICO de
    titularidad no genera puja de reventa.

    MUERDE SI EN EL CASO TODOS LOS CANDIDATOS SON TITULARES: sin
    un candidato sin pronostico no habria nada que frenar, y sin
    un titular que siga pujando esto no distinguiria la regla de
    un apagado (doctrina 24).
    """

    candidatos = [_titular(0), _sin_pronostico(1), _suplente(2)]

    # ------------------------------------------------
    # EL CASO TIENE LO QUE DICE TENER
    # ------------------------------------------------
    sin_pronostico = [
        c
        for c in candidatos
        if c.get("starter_probability") is None
    ]

    assert sin_pronostico, (
        "el caso no trae ningun candidato SIN PRONOSTICO: esta "
        "guardia pasaria con las manos vacias"
    )

    titulares = [
        c
        for c in candidatos
        if (c.get("starter_probability") or 0) >= MIN_STARTER_PERCENT
    ]

    assert titulares, (
        "el caso no trae ningun titular: sin eso, que no se puje "
        "no probaria que la regla distingue, solo que apaga"
    )

    # ------------------------------------------------
    # SIN LA REGLA, LOS TRES PUJAN
    # ------------------------------------------------
    antes = _plan(candidatos)

    assert antes["execute"] is True, (
        f"sin la regla tendrian que pujar los tres: "
        f"{antes['reason']}"
    )

    assert {b["id"] for b in antes["bids"]} == {
        c["id"] for c in candidatos
    }, "sin la regla no pujan todos; el caso no sirve"

    # ------------------------------------------------
    # CON LA REGLA, SOLO EL TITULAR
    # ------------------------------------------------
    with _Interruptor(REGLA_ENV):

        plan = _plan(candidatos)

        suelto = por_que_no(sin_pronostico[0])

    pujados = {b["id"] for b in plan["bids"]}

    for c in sin_pronostico:
        assert c["id"] not in pujados, (
            f"{c['name']} no tiene pronostico de titularidad y "
            f"sigue generando puja de reventa"
        )

    assert pujados == {c["id"] for c in titulares}, (
        f"se puja por {pujados} y los titulares son "
        f"{[c['id'] for c in titulares]}"
    )

    assert plan["execute"] is True, (
        "el titular tendria que seguir pujando: la regla cierra "
        "la reventa del que no juega, no la reventa"
    )

    assert plan["dropped_by_no_juega"] == 2, (
        f"frenados {plan['dropped_by_no_juega']}, y sobran dos: "
        f"el que no tiene pronostico y el suplente"
    )

    assert suelto, (
        "preguntada a pelo, la regla tiene que dar un motivo "
        "para el que no tiene pronostico"
    )

    assert "pronostico" in suelto.lower(), (
        f"el motivo no nombra el pronostico: {suelto}"
    )


# ============================================================
# 2. Y SI NO QUEDA NINGUNO, SE DICE CON SU NOMBRE
# ============================================================

def test_sin_nadie_que_juegue_el_motivo_lo_dice():
    """
    Doctrina 87: el motivo nombra al que decidio. "No hay cesta"
    y "ninguno va a jugar" son dos cosas distintas.
    """

    candidatos = [_sin_pronostico(0), _suplente(1)]

    assert _plan(candidatos)["execute"] is True, (
        "sin la regla estos dos pujarian; si no, no hay nada que "
        "frenar"
    )

    with _Interruptor(REGLA_ENV):
        plan = _plan(candidatos)

    assert plan["bids"] == []
    assert plan["execute"] is False
    assert plan["blocked_by"] == "NO_VA_A_JUGAR", (
        f"cerrado por {plan['blocked_by']}, no por la regla"
    )
    assert plan["dropped_by_no_juega"] == 2
    assert plan["committed"] == 0


# ============================================================
# 3. APAGADA NO CAMBIA NI UNA PUJA
# ============================================================

def test_la_regla_apagada_no_frena_nada():

    assert os.environ.get(REGLA_ENV) is None, (
        "esta guardia arranca con la regla quitada"
    )

    candidatos = [_titular(0), _sin_pronostico(1), _suplente(2)]

    plan = _plan(candidatos)

    assert len(plan["bids"]) == 3, (
        "apagada, los tres siguen pujando"
    )
    assert plan["dropped_by_no_juega"] == 0

    reparto = mira_si_va_a_jugar(candidatos)

    assert reparto["activa"] is False
    assert reparto["frenados"] == []
    assert len(reparto["siguen"]) == 3


# ============================================================
# 4. EL UMBRAL NO ES NUEVO
# ============================================================

def test_la_regla_no_escribe_un_umbral_nuevo():
    """
    Doctrina 84: la pregunta "¿va a jugar?" ya estaba contestada
    en `roster_fill_veto`. Esta regla la LLAMA, no la reescribe.
    """

    reparto = mira_si_va_a_jugar([])

    assert reparto["min_starter_percent"] == MIN_STARTER_PERCENT
    assert reparto["min_hierarchy_value"] == MIN_HIERARCHY_VALUE

    # Y el veredicto es literalmente el del veto de la casa.
    for fila in (
        _titular(),
        _sin_pronostico(),
        _suplente(),
        {"starter_probability": MIN_STARTER_PERCENT, "hierarchy_value": 40},
        {"starter_probability": MIN_STARTER_PERCENT - 0.1,
         "hierarchy_value": 40},
    ):
        esperado = roster_fill_veto(
            {
                "probability": fila.get("starter_probability"),
                "hierarchy_value": fila.get("hierarchy_value"),
                "hierarchy_label": None,
                "availability": fila.get("availability"),
            }
        )

        assert por_que_no(fila) == esperado, (
            f"la regla y `roster_fill_veto` no dicen lo mismo de "
            f"{fila}: {por_que_no(fila)!r} contra {esperado!r}"
        )


# ============================================================
# 5. LA LECTURA DEL ESTADO LLEVA LO QUE LA REGLA MIRA
# ============================================================

def test_la_lectura_lleva_lo_que_la_regla_mira():
    """
    `lectura_del_estado` copiaba seis campos y tiraba los tres
    que contestan "¿va a jugar?". Sin ellos la regla frenaria a
    todos por igual.
    """

    fila = {
        "id": 900,
        "name": "El titular",
        "market_price": 1_660_000,
        "team_id": 42,
        "seller_id": None,
        "decision": "BID",
        "starter_probability": 80.0,
        "hierarchy_value": 60,
        "availability": {"can_play": True, "label": "DISPONIBLE"},
        "market_gate": {"rate_percent_per_day": 0.8},
    }

    visto = lectura_del_estado(
        {"acquisition": {"targets": [fila]}}
    )["candidatos"]

    assert visto, "el candidato no llego"

    visto = visto[0]

    for campo, esperado in (
        ("starter_probability", 80.0),
        ("hierarchy_value", 60),
        ("availability", fila["availability"]),
    ):
        assert visto.get(campo) == esperado, (
            f"`lectura_del_estado` tira `{campo}`: llego "
            f"{visto.get(campo)!r}"
        )

    # Los seis de siempre siguen estando.
    for campo in (
        "id",
        "name",
        "market_price",
        "team_id",
        "seller_id",
        "rate_percent_per_day",
    ):
        assert campo in visto, f"se perdio `{campo}`"

    # Y con esos campos la regla ya sabe que este juega.
    assert por_que_no(visto) is None, (
        f"un titular del 80 % con jerarquia 60 no se frena: "
        f"{por_que_no(visto)}"
    )


# ============================================================
# 6. LA FORMA NO CAMBIA CON LOS DATOS
# ============================================================

def test_la_forma_no_cambia_con_los_datos():

    casos = [
        [],
        None,
        ["basura", 7, None],
        [{"id": 1}],
        [{"id": 2, "market_price": 100_000}],
        [_titular(), _suplente(), None],
    ]

    for candidatos in casos:

        for encendida in (False, True):

            if encendida:
                with _Interruptor(REGLA_ENV):
                    plan = _plan(candidatos)
                    reparto = mira_si_va_a_jugar(candidatos)
            else:
                plan = _plan(candidatos)
                reparto = mira_si_va_a_jugar(candidatos)

            assert "dropped_by_no_juega" in plan, (
                f"falta el campo con {candidatos}"
            )
            assert isinstance(plan["dropped_by_no_juega"], int)

            for campo in (
                "available",
                "activa",
                "siguen",
                "frenados",
                "reason",
            ):
                assert campo in reparto, (
                    f"falta `{campo}` con {candidatos}"
                )

            json.dumps(plan, default=str)
            json.dumps(reparto, default=str)


# ============================================================
# 7. LA REJA DE REEMISIONES, QUE SOSTIENE LA TABLA DE VIAJES
# ============================================================

def test_la_reja_colapsa_la_copia_y_no_la_operacion_de_verdad():
    """
    La tabla de viajes del 22/09 depende de esto. Una copia
    dentro de la ventana es una copia; la misma operacion dos
    semanas despues son dos hechos.
    """

    from scripts.los_viajes import (
        VENTANA_REEMISION,
        sin_repetidos,
    )

    base = {
        "kind": "SELL_TO_COMPUTER",
        "player_id": 15289,
        "amount": 420_200,
        "counterparty_id": None,
    }

    movimientos = [
        {**base, "date": 1_000_000},
        {**base, "date": 1_000_000 + VENTANA_REEMISION - 1},
        {**base, "date": 1_000_000 + VENTANA_REEMISION + 1},
    ]

    limpias, tiradas = sin_repetidos(movimientos)

    assert len(tiradas) == 1, (
        f"la copia dentro de la ventana tendria que caer una vez "
        f"sola; cayeron {len(tiradas)}"
    )
    assert len(limpias) == 2, (
        "la operacion de fuera de la ventana es un hecho, no una "
        "copia"
    )

    # Y NO SE REANCLA: tres copias seguidas colapsan contra la
    # primera, no encadenadas.
    cadena = [
        {**base, "date": 1_000_000 + i * (VENTANA_REEMISION - 10)}
        for i in range(3)
    ]

    limpias, tiradas = sin_repetidos(cadena)

    assert len(limpias) == 2, (
        f"la tercera esta a {2 * (VENTANA_REEMISION - 10)} s de "
        f"la primera: fuera de la ventana, es un hecho. Salieron "
        f"{len(limpias)} limpias"
    )


# ============================================================
# 8. EL FIFO
# ============================================================

def test_el_fifo_empareja_por_orden_y_avisa_de_los_dos_lotes():
    """
    La otra pata de la tabla: si alguien tuvo DOS lotes del mismo
    jugador a la vez, el orden puede cruzarse. Sobre el tablon
    real eso no pasa nunca, pero la funcion tiene que saber
    decirlo.
    """

    from scripts.los_viajes import empareja

    uno = [
        {"kind": "BUY_FROM_COMPUTER", "player_id": 7, "amount": 100, "date": 1},
        {"kind": "SELL_TO_COMPUTER", "player_id": 7, "amount": 150, "date": 2},
        {"kind": "BUY_FROM_COMPUTER", "player_id": 7, "amount": 200, "date": 3},
    ]

    casado = empareja(uno)

    assert len(casado["viajes"]) == 1
    assert casado["viajes"][0][0]["amount"] == 100
    assert len(casado["abiertas"]) == 1
    assert casado["con_dos_lotes"] == [], (
        "nunca tuvo dos a la vez: comprar, vender y volver a "
        "comprar no es tener dos lotes"
    )

    dos = [
        {"kind": "BUY_FROM_COMPUTER", "player_id": 9, "amount": 100, "date": 1},
        {"kind": "BUY_FROM_COMPUTER", "player_id": 9, "amount": 200, "date": 2},
        {"kind": "SELL_TO_COMPUTER", "player_id": 9, "amount": 300, "date": 3},
    ]

    casado = empareja(dos)

    assert casado["con_dos_lotes"] == [9], (
        "dos compras antes de una venta son dos lotes a la vez, "
        "y eso hay que decirlo"
    )
    assert casado["viajes"][0][0]["amount"] == 100, (
        "FIFO: se vende el que se compro primero"
    )

    huerfana = [
        {"kind": "SELL_TO_COMPUTER", "player_id": 3, "amount": 50, "date": 1},
    ]

    casado = empareja(huerfana)

    assert casado["viajes"] == []
    assert len(casado["ventas_sin_compra"]) == 1, (
        "una venta sin compra en el libro no inventa un viaje"
    )


# ============================================================
# 9. LA REGLA NO LEE EL MUNDO
# ============================================================

def test_la_regla_no_lee_el_mundo():
    """
    Ni disco, ni red, ni reloj. Solo el entorno, que es lo que ES
    el interruptor.
    """

    import inspect

    from src.analysis import la_regla_de_compra

    fuente = inspect.getsource(la_regla_de_compra)

    for prohibido in (
        "open(",
        "Path(",
        "requests",
        "urllib",
        "datetime.now",
        "time.time",
        "json.load",
    ):
        assert prohibido not in fuente, (
            f"`la_regla_de_compra` usa `{prohibido}`: una regla "
            f"que lee el mundo no se puede probar a mano"
        )


# ============================================================
# EL CORREDOR
# ============================================================

TESTS = [
    test_la_regla_de_compra_mira_si_va_a_jugar,
    test_sin_nadie_que_juegue_el_motivo_lo_dice,
    test_la_regla_apagada_no_frena_nada,
    test_la_regla_no_escribe_un_umbral_nuevo,
    test_la_lectura_lleva_lo_que_la_regla_mira,
    test_la_forma_no_cambia_con_los_datos,
    test_la_reja_colapsa_la_copia_y_no_la_operacion_de_verdad,
    test_el_fifo_empareja_por_orden_y_avisa_de_los_dos_lotes,
    test_la_regla_no_lee_el_mundo,
]


def main() -> None:

    print()
    print("=" * 60)
    print("LA REGLA DE COMPRA V1")
    print("=" * 60)

    fallos = 0

    for prueba in TESTS:

        try:
            prueba()
            print(f"  OK    {prueba.__name__}")

        except AssertionError as error:
            fallos += 1
            print(f"  FALLA {prueba.__name__}")
            print(f"        {error}")

        except Exception as error:                  # noqa: BLE001
            fallos += 1
            print(f"  ROMPE {prueba.__name__}")
            print(f"        {type(error).__name__}: {error}")

    print("=" * 60)

    if fallos:
        print(f"{fallos} de {len(TESTS)} en rojo.")
        raise SystemExit(1)

    print(f"Los {len(TESTS)} en verde.")


if __name__ == "__main__":
    main()
