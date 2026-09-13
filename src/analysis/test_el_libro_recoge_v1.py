"""
El libro recoge lo que ve, no solo lo que el codigo creyo hacer.

SINTOMA (12/09/2026, noche)

    Una puja viva por Trent de 2.760.000, puesta a las 16:45 con
    el codigo de antes de que el carril aprendiera a anotar. No
    estaba en ningun libro —ni en el local ni en produccion— y se
    resolvia a las 07:00 del dia siguiente.

    El primer viaje del carril de la historia se habria cerrado
    sin quedar registrado.

    Y ANOTAR AL PUJAR NO LA RECOGE: ya se pujo.

LA REGLA

    Si el tablon publica una puja viva nuestra que no esta en el
    libro, el libro la anota. Con el importe DEL TABLON, no con
    el que el codigo pujaria hoy.

    Es mas honesto que anotar al pujar: el libro se llena de lo
    que OCURRIO. Entran igual una puja hecha a mano, una puesta
    por una version anterior y una que fallo al apuntarse.

EL ORIGEN, SOLO SI SE PUEDE PROBAR

    De una puja recogida del tablon no se sabe de que via salio.
    DESCONOCIDO salvo prueba —el libro del carril, escrito en el
    mismo instante en que se puja—. Inventar el origen es peor
    que no tenerlo: el dia que se comparen las dos vias, una
    marca inventada mueve el resultado y nadie lo sabra.

REGLA 23

    No lee estado externo: la foto y el libro se construyen aqui,
    y el libro del carril se apunta a un fichero temporal.
"""

from __future__ import annotations

import json
import tempfile

from datetime import datetime, timezone

from pathlib import Path


# LA PUJA REAL DEL 12/09/2026, a las 16:45 de Madrid.
TRENT_ID = 101

TRENT_IMPORTE = 2_760_000

TRENT_PRECIO = 2_760_000

PUESTA_EPOCH = int(
    datetime(
        2026, 9, 12, 14, 45, tzinfo=timezone.utc
    ).timestamp()
)

YO = 14175949


def _foto_con_la_puja_viva(
    importe: int = TRENT_IMPORTE,
) -> dict:
    """
    Una foto de Biwenger con UNA puja viva nuestra.

    Las ofertas del mercado llevan `from` = quien puja. Las que
    van dirigidas a nosotros —`from: null`— son el Computer
    ofreciendo por los nuestros, y esas NO son pujas nuestras.
    """

    return {
        "league": {"user": {"id": YO, "name": "Pepe"}},
        "my_team": [{"id": 1599, "name": "Jonny"}],
        "market": {
            "status": {"balance": 1_573_406},
            "sales": [
                {
                    "player": {
                        "id": TRENT_ID,
                        "name": "Trent",
                    },
                    "price": TRENT_PRECIO,
                    "date": PUESTA_EPOCH - 3600,
                    "until": PUESTA_EPOCH + 40 * 3600,
                }
            ],
            "offers": [
                # LA NUESTRA.
                {
                    "id": 900001,
                    "amount": importe,
                    "created": PUESTA_EPOCH,
                    "until": PUESTA_EPOCH + 14 * 3600,
                    "status": "waiting",
                    "type": "purchase",
                    "from": {"id": YO, "name": "Pepe"},
                    "requestedPlayers": [TRENT_ID],
                },
                # Y UNA QUE NO LO ES: el Computer ofreciendo por
                # un jugador nuestro. Si esta se colara, el libro
                # se llenaria de pujas que no hemos hecho.
                {
                    "id": 900002,
                    "amount": 2_417_400,
                    "created": PUESTA_EPOCH,
                    "until": PUESTA_EPOCH + 14 * 3600,
                    "status": "waiting",
                    "type": "purchase",
                    "from": None,
                    "to": {"id": YO, "name": "Pepe"},
                    "requestedPlayers": [1599],
                },
            ],
        },
    }


def _libro_vacio() -> dict:
    return {"version": 1, "bids": {}}


# `None` es un VALOR aqui —"no sabemos quienes somos"— asi que
# no puede servir tambien de "no me lo has pasado". Un centinela.
_SIN_DECIR = object()


def _recoger(foto, ledger, quien=_SIN_DECIR, carril=None):
    """
    `recoger_pujas_vivas` CON RUTA PROPIA, siempre.

    Sin ella, `_origen_probado` abre el
    `libro_del_carril.jsonl` de produccion —que en CI existe— y
    la guardia pasa a depender de lo que el carril pujara esa
    mañana. Es el fallo del 13/09 otra vez, un paso mas abajo.
    """

    import tempfile

    from src.intelligence.bid_outcome_ledger import (
        recoger_pujas_vivas,
    )

    with tempfile.TemporaryDirectory() as tmp:

        return recoger_pujas_vivas(
            foto,
            YO if quien is _SIN_DECIR else quien,
            ledger=ledger,
            ruta_del_carril=(
                carril or Path(tmp) / "sin_carril.jsonl"
            ),
        )


# ============================================================
# 1. LO QUE NO SE ANOTO, SE RECOGE
# ============================================================


def test_el_libro_recoge_la_puja_que_no_anoto() -> None:
    """
    Foto con puja viva de 2.760.000 y libro vacio. Despues de
    recoger, la entrada existe CON ESE IMPORTE EXACTO.
    """

    from src.intelligence.bid_outcome_ledger import (
        recoger_pujas_vivas,
    )

    libro = _libro_vacio()

    visto = _recoger(_foto_con_la_puja_viva(), libro)

    assert visto["available"] is True, visto

    assert len(visto["recogidas"]) == 1, visto

    assert len(libro["bids"]) == 1, libro

    entrada = list(libro["bids"].values())[0]

    # EL IMPORTE DEL TABLON, no el que el codigo pujaria hoy.
    assert entrada["amount"] == TRENT_IMPORTE, entrada

    assert entrada["player_id"] == TRENT_ID, entrada

    assert entrada["player_name"] == "Trent", entrada

    assert entrada["outcome"] == "PENDING", entrada

    # Y la hora es la de la oferta, no la de ahora: de ella
    # depende cual es el reset que la resuelve.
    assert entrada["placed_at"].startswith("2026-09-12T14:45"), (
        entrada
    )

    # Queda dicho que se anoto al VERLA, no al hacerla.
    assert entrada["recorded_by"] == "TABLON", entrada


def test_no_duplica_lo_que_ya_tiene() -> None:
    """
    La misma foto dos veces deja UNA sola entrada.

    Y se mira por JUGADOR, no por clave: la clave lleva la hora,
    y la del tablon no tiene por que coincidir al segundo con la
    que anoto el ejecutor.
    """

    from src.intelligence.bid_outcome_ledger import (
        recoger_pujas_vivas,
    )

    libro = _libro_vacio()

    foto = _foto_con_la_puja_viva()

    primera = _recoger(foto, libro)

    segunda = _recoger(foto, libro)

    assert len(primera["recogidas"]) == 1, primera

    assert segunda["recogidas"] == [], segunda

    assert len(libro["bids"]) == 1, libro

    # Y si el ejecutor ya la habia anotado con otra hora, tampoco
    # se duplica.
    from src.intelligence.bid_outcome_ledger import record_bid

    otro = _libro_vacio()

    record_bid(
        TRENT_ID,
        2_762_258,
        player_name="Trent",
        target_source="RENDIJA",
        placed_at="2026-09-12T14:45:03.123456+00:00",
        ledger=otro,
        save=False,
    )

    tercera = _recoger(foto, otro)

    assert tercera["recogidas"] == [], tercera

    assert len(otro["bids"]) == 1, otro


def test_solo_recoge_pujas_NUESTRAS() -> None:
    """
    La foto trae DOS ofertas y solo una es nuestra.

    La otra es el Computer ofreciendo por un jugador de nuestra
    plantilla. Si esa se colara, el libro se llenaria de pujas
    que no hemos hecho y el `win_rate` diria cualquier cosa.
    """

    from src.intelligence.bid_outcome_ledger import (
        recoger_pujas_vivas,
    )

    libro = _libro_vacio()

    _recoger(_foto_con_la_puja_viva(), libro)

    jugadores = {
        e["player_id"] for e in libro["bids"].values()
    }

    assert jugadores == {TRENT_ID}, (
        f"se ha colado una oferta que no es nuestra: {jugadores}"
    )

    # Y sin saber quienes somos NO se recoge nada: marcar pujas
    # ajenas como nuestras es peor que no verlas (regla 24).
    a_ciegas = _libro_vacio()

    visto = _recoger(
        _foto_con_la_puja_viva(), a_ciegas, quien=None
    )

    assert visto["available"] is False, visto
    assert a_ciegas["bids"] == {}, a_ciegas


# ============================================================
# 2. EL ORIGEN, SOLO SI SE PUEDE PROBAR
# ============================================================


def test_el_origen_no_se_inventa() -> None:
    """
    Sin prueba, DESCONOCIDO. Con el libro del carril delante,
    RENDIJA.
    """

    from src.intelligence.bid_outcome_ledger import (
        ORIGEN_SIN_PROBAR,
        recoger_pujas_vivas,
    )

    assert ORIGEN_SIN_PROBAR == "DESCONOCIDO"

    # 1. SIN PRUEBA.
    with tempfile.TemporaryDirectory() as tmp:

        vacio = Path(tmp) / "no_existe.jsonl"

        libro = _libro_vacio()

        _recoger(
            _foto_con_la_puja_viva(), libro, carril=vacio
        )

        entrada = list(libro["bids"].values())[0]

        assert entrada["target_source"] == "DESCONOCIDO", (
            entrada
        )

    # 2. CON PRUEBA: el libro del carril, escrito en el mismo
    #    instante en que se pujo.
    with tempfile.TemporaryDirectory() as tmp:

        del_carril = Path(tmp) / "libro_del_carril.jsonl"

        del_carril.write_text(
            json.dumps(
                {
                    "player_id": TRENT_ID,
                    "player_name": "Trent",
                    "amount": TRENT_IMPORTE,
                    "marca": "RENDIJA",
                },
                ensure_ascii=False,
            )
            + chr(10),
            encoding="utf-8",
        )

        libro = _libro_vacio()

        _recoger(
            _foto_con_la_puja_viva(), libro, carril=del_carril
        )

        entrada = list(libro["bids"].values())[0]

        assert entrada["target_source"] == "RENDIJA", entrada

    # 3. Y CON UN IMPORTE QUE NO CUADRA no se da por probado: es
    #    otra puja, aunque sea el mismo jugador.
    with tempfile.TemporaryDirectory() as tmp:

        del_carril = Path(tmp) / "libro_del_carril.jsonl"

        del_carril.write_text(
            json.dumps(
                {
                    "player_id": TRENT_ID,
                    "amount": 999_999,
                    "marca": "RENDIJA",
                }
            )
            + chr(10),
            encoding="utf-8",
        )

        libro = _libro_vacio()

        _recoger(
            _foto_con_la_puja_viva(), libro, carril=del_carril
        )

        assert list(libro["bids"].values())[0][
            "target_source"
        ] == "DESCONOCIDO"


# ============================================================
# 3. Y SE CIERRA EN LA MISMA VUELTA
# ============================================================


def test_lo_recogido_se_resuelve_sin_esperar_otro_ciclo() -> None:
    """
    Se recoge ANTES de reconciliar, a proposito.

    Una puja que el tablon publica y el libro no tenia entra y se
    resuelve en ESTA MISMA vuelta si su reset ya paso. Al reves se
    quedaria un ciclo entero sin cerrar — y el reset del carril
    solo pasa una vez al dia.
    """

    from src.intelligence.bid_outcome_ledger import (
        recoger_pujas_vivas,
        reconcile,
        summary,
    )

    libro = _libro_vacio()

    _recoger(_foto_con_la_puja_viva(), libro)

    # Ya paso el reset de las 07:00 del 13/09, y Trent no esta en
    # la plantilla.
    cerrado = reconcile(
        [],
        our_user_id=YO,
        ledger=libro,
        save=False,
        ahora="2026-09-13T06:00:00+00:00",
        roster=[{"id": 1599, "name": "Jonny"}],
    )

    entrada = list(cerrado["bids"].values())[0]

    assert entrada["outcome"] == "LOST", entrada

    assert entrada["resolved_by"] == "RESET_SIN_JUGADOR", entrada

    assert summary(cerrado)["lost"] == 1, summary(cerrado)


def test_aubameyang_se_cierra_como_perdida() -> None:
    """
    EL "Y DE PASO" DEL ENCARGO.

    La unica entrada del libro real: Aubameyang, 12.217.000,
    puesta el 10/09 y en PENDING. Se perdio. La misma
    reconciliacion tiene que cerrarla.

    Los numeros van escritos aqui, no leidos del fichero: una
    guardia de la verja no lee estado que cambia (regla 23).
    """

    from src.intelligence.bid_outcome_ledger import (
        reconcile,
        summary,
    )

    libro = {
        "version": 1,
        "bids": {
            "25769:2026-09-10T08:00:00+00:00": {
                "player_id": 25769,
                "player_name": "Aubameyang",
                "amount": 12_217_000,
                "market_price": 12_170_000,
                "target_source": "MANUAL_DUENO",
                "intent": "SPECULATION",
                "placed_at": "2026-09-10T08:00:00+00:00",
                "outcome": "PENDING",
                "resolved_at": None,
                "winning_amount": None,
                "margin": None,
                "event_id": None,
            }
        },
    }

    cerrado = reconcile(
        [],
        our_user_id=YO,
        ledger=libro,
        save=False,
        ahora="2026-09-12T20:00:00+00:00",
        roster=[{"id": 1599, "name": "Jonny"}],
    )

    entrada = list(cerrado["bids"].values())[0]

    assert entrada["outcome"] == "LOST", entrada

    assert summary(cerrado)["win_rate"] == 0.0, summary(cerrado)


def test_el_ciclo_le_pasa_la_foto_al_libro() -> None:
    """
    Sin la foto, la regla no se ejecuta nunca y no haria ruido.
    """

    import ast

    fuente = (
        Path(__file__).parents[2] / "src" / "autopilot.py"
    ).read_text(encoding="utf-8")

    con_foto = False

    for nodo in ast.walk(ast.parse(fuente)):

        if (
            isinstance(nodo, ast.Call)
            and isinstance(nodo.func, ast.Name)
            and nodo.func.id == "sync_bid_outcomes"
        ):
            con_foto = any(
                k.arg == "snapshot" for k in nodo.keywords
            )

    assert con_foto, (
        "el ciclo no le pasa la foto al libro: las pujas vivas "
        "que no anoto nadie no se recogerian nunca"
    )


def test_el_nombre_sale_del_catalogo_si_la_venta_no_lo_trae() -> None:
    """
    LAS VENTAS DEL MERCADO NO TRAEN NOMBRE.

    Biwenger las publica como `{"player": {"id": 1602}}`, a
    secas. Los nombres estan en el catalogo, en
    `catalog.data.players`, con la clave en texto.

    La primera version casaba el id en la venta y devolvia su
    `name` —que es None— sin llegar nunca al catalogo. El libro
    se habria llenado de entradas llamadas `None` y habria que
    cruzar ids a mano para leerlas.
    """

    from src.intelligence.bid_outcome_ledger import (
        _nombre_en_la_foto,
    )

    foto = _foto_con_la_puja_viva()

    # Como las da Biwenger: sin nombre.
    foto["market"]["sales"] = [
        {"player": {"id": TRENT_ID}, "price": TRENT_PRECIO}
    ]

    foto["catalog"] = {
        "data": {
            "players": {
                str(TRENT_ID): {
                    "id": TRENT_ID,
                    "name": "Trent",
                    "position": 2,
                }
            }
        }
    }

    assert _nombre_en_la_foto(foto, TRENT_ID) == "Trent"

    # Y si no esta en ningun sitio, None — no una cadena vacia
    # ni un id disfrazado de nombre.
    assert _nombre_en_la_foto(foto, 999_999) is None


# ============================================================
# 4. LO QUE SE RESOLVIO ENTRE DOS DESPLIEGUES
# ============================================================
#
# SINTOMA (13/09/2026)
#
#     Trent en el banquillo, sin publicar, y el carril sin saber
#     que lo tenia. Se gano la puja en el reset de las 07:00 y la
#     recogida de pujas vivas se desplego a las 08:xx: para
#     entonces ya no habia puja VIVA que recoger.
#
#     Llego tarde POR UNA HORA, y la mitad que falta del primer
#     viaje del carril se quedo sin registrar.
#
# EL AGUJERO ERA DE FORMA, NO DE HORA
#
#     Mirar solo pujas vivas deja fuera todo lo que se resuelve
#     entre dos despliegues. Mirar LA PLANTILLA no: un jugador
#     que tenemos y que el tablon dice que compramos es una
#     compra, la viera alguien pujar o no.


TRENT_REAL = 37499

TRENT_GANADO = 2_760_000

# 07:06:58 de Madrid del 13/09 = 05:06:58 UTC: el reset que la
# resolvio.
RESUELTA_EPOCH = 1789268818


def _plantilla_con_trent() -> dict:
    return {
        "league": {"user": {"id": YO, "name": "Pepe"}},
        "my_team": [
            {"id": 1599, "name": "Jonny", "position": 2},
            {"id": TRENT_REAL, "name": "Trent", "position": 2},
        ],
        "market": {"status": {}, "sales": [], "offers": []},
    }


def _tablon_con_la_compra() -> list:
    """
    El tablon: el Computer nos vendio a Trent en el reset.

    EL TIPO DE EVENTO IMPORTA. Medido el 13/09 sobre el tablon
    real, nuestras compras llegan como `market` (21) y como
    `transfer` (1, comprado a un rival). Las dos cuentan: un
    jugador comprado a un manager es tan nuestro como uno
    comprado al Computer.
    """

    return [
        {
            "id": 5551,
            "date": RESUELTA_EPOCH,
            "type": "market",
            "content": [
                {
                    "player": TRENT_REAL,
                    "amount": TRENT_GANADO,
                    "from": None,
                    "to": {"id": YO, "name": "Pepe"},
                }
            ],
        },
        # Y uno que NO nos vendieron a nosotros.
        {
            "id": 5552,
            "date": RESUELTA_EPOCH,
            "type": "market",
            "content": [
                {
                    "player": 28087,
                    "amount": 3_677_000,
                    "from": None,
                    "to": {"id": 99999, "name": "Pollo17"},
                }
            ],
        },
    ]


def test_lo_que_se_resolvio_sin_nosotros_se_recoge() -> None:
    """
    EL CASO DE TRENT.

    Plantilla con Trent, tablon con la compra, libro vacio.
    Despues de recoger: la entrada existe, con el importe real y
    ganada.
    """

    from src.intelligence.bid_outcome_ledger import (
        recoger_compras_de_la_plantilla,
    )

    libro = _libro_vacio()

    # SUS PROPIAS RUTAS, SIEMPRE.
    #
    #     Sin ellas, `recoger_compras_de_la_plantilla` abre el
    #     viaje en `libro_de_viajes.jsonl` DE PRODUCCION cuando el
    #     libro del carril prueba el origen — y en CI ese libro
    #     existe. Reproducido el 13/09: la guardia escribio el
    #     viaje de Trent.
    #
    #     Una guardia que lee estado ajeno es deuda. Una que lo
    #     ESCRIBE es otra cosa: desde que el escaparate esta
    #     enchufado, un viaje escrito aqui es un jugador que Pepe
    #     publica.
    with tempfile.TemporaryDirectory() as tmp:

        visto = recoger_compras_de_la_plantilla(
            _plantilla_con_trent(),
            _tablon_con_la_compra(),
            YO,
            ledger=libro,
            ruta_del_carril=Path(tmp) / "carril.jsonl",
            ruta_de_viajes=Path(tmp) / "viajes.jsonl",
        )

    assert visto["available"] is True, visto

    assert len(visto["recogidas"]) == 1, visto

    entrada = libro["bids"][
        [
            k
            for k, v in libro["bids"].items()
            if v["player_id"] == TRENT_REAL
        ][0]
    ]

    # EL IMPORTE REAL, el del tablon.
    assert entrada["amount"] == TRENT_GANADO, entrada

    assert entrada["player_name"] == "Trent", entrada

    # LO TENEMOS: la puja se gano. No es una deduccion, es la
    # plantilla.
    assert entrada["outcome"] == "WON", entrada

    assert entrada["resolved_by"] == "EN_LA_PLANTILLA", entrada

    assert entrada["recorded_by"] == "PLANTILLA", entrada

    # Y Jonny NO entra: nadie nos lo vendio, es del sorteo
    # inicial. Esa es la linea que separa una compra de un
    # regalo, y no hace falta saber cual fue el sorteo.
    assert 1599 not in {
        v["player_id"] for v in libro["bids"].values()
    }, libro

    # Ni el que se llevo otro.
    assert 28087 not in {
        v["player_id"] for v in libro["bids"].values()
    }, libro


def test_tambien_se_ve_lo_comprado_a_un_rival() -> None:
    """
    LAS COMPRAS NO VIENEN TODAS DEL MISMO TIPO DE EVENTO.

    Medido el 13/09 sobre el tablon real: `market` 21 y
    `transfer` 1 —un jugador comprado a un manager—. El filtro
    que usa `reconcile` solo acepta `market`, asi que esa compra
    se le escapaba.

    Para "¿que hemos comprado?" las dos cuentan.
    """

    from src.intelligence.bid_outcome_ledger import (
        recoger_compras_de_la_plantilla,
    )

    OTRO = 39874

    foto = _plantilla_con_trent()

    foto["my_team"].append(
        {"id": OTRO, "name": "Comprado a un rival", "position": 3}
    )

    tablon = _tablon_con_la_compra() + [
        {
            "id": 5553,
            "date": RESUELTA_EPOCH - 86_400,
            "type": "transfer",
            "content": [
                {
                    "player": OTRO,
                    "amount": 463_500,
                    "from": {"id": 99999, "name": "Prinzipote"},
                    "to": {"id": YO, "name": "Pepe"},
                }
            ],
        }
    ]

    libro = _libro_vacio()

    with tempfile.TemporaryDirectory() as tmp:

        recoger_compras_de_la_plantilla(
            foto,
            tablon,
            YO,
            ledger=libro,
            ruta_del_carril=Path(tmp) / "carril.jsonl",
            ruta_de_viajes=Path(tmp) / "viajes.jsonl",
        )

    vistos = {v["player_id"] for v in libro["bids"].values()}

    assert OTRO in vistos, (
        "una compra a un rival no se recoge: llega como "
        "`transfer` y el filtro solo miraba `market`"
    )

    assert TRENT_REAL in vistos, vistos


def test_la_hora_dice_si_es_la_de_la_puja_o_la_del_reset() -> None:
    """
    DOCTRINA 35, EN UN CASO NUEVO.

    Del tablon solo se sabe CUANDO SE RESOLVIO, no cuando se
    pujo. Son dos horas distintas —aqui, 16:45 del 12 y 07:06 del
    13— y publicarlas con el mismo nombre haria creer que la puja
    se puso en el reset.

    Si el libro del carril prueba la hora de la puja, se usa esa.
    Si no, la del tablon Y SE DICE.
    """

    from src.intelligence.bid_outcome_ledger import (
        recoger_compras_de_la_plantilla,
    )

    # 1. SIN PRUEBA: la del tablon, y marcada.
    with tempfile.TemporaryDirectory() as tmp:

        libro = _libro_vacio()

        recoger_compras_de_la_plantilla(
            _plantilla_con_trent(),
            _tablon_con_la_compra(),
            YO,
            ledger=libro,
            ruta_del_carril=Path(tmp) / "no_existe.jsonl",
            ruta_de_viajes=Path(tmp) / "viajes.jsonl",
        )

        entrada = list(libro["bids"].values())[0]

        assert entrada["placed_at_is_resolution"] is True, (
            entrada
        )

        assert entrada["target_source"] == "DESCONOCIDO", entrada

    # 2. CON EL LIBRO DEL CARRIL DELANTE: su hora y su marca.
    with tempfile.TemporaryDirectory() as tmp:

        del_carril = Path(tmp) / "libro_del_carril.jsonl"

        del_carril.write_text(
            json.dumps(
                {
                    "at": "2026-09-12T14:45:03+00:00",
                    "marca": "RENDIJA",
                    "player_id": TRENT_REAL,
                    "player_name": "Trent",
                    "amount": TRENT_GANADO,
                }
            )
            + chr(10),
            encoding="utf-8",
        )

        libro = _libro_vacio()

        visto = recoger_compras_de_la_plantilla(
            _plantilla_con_trent(),
            _tablon_con_la_compra(),
            YO,
            ledger=libro,
            ruta_del_carril=del_carril,
            ruta_de_viajes=Path(tmp) / "viajes.jsonl",
        )

        entrada = list(libro["bids"].values())[0]

        assert entrada["placed_at"] == (
            "2026-09-12T14:45:03+00:00"
        ), entrada

        assert entrada["placed_at_is_resolution"] is False, (
            entrada
        )

        assert entrada["target_source"] == "RENDIJA", entrada

        # Y SI VINO DEL CARRIL, SE ABRE EL VIAJE. Un jugador
        # comprado para revender que no esta marcado VIAJE es
        # medio viaje: lo juzgaria el motor de ofertas de
        # siempre, con la pregunta equivocada.
        assert visto["viajes_abiertos"], visto

        assert visto["viajes_abiertos"][0]["name"] == "Trent"


def test_la_plantilla_no_se_recoge_dos_veces() -> None:
    """La misma foto dos veces deja una sola entrada."""

    from src.intelligence.bid_outcome_ledger import (
        recoger_compras_de_la_plantilla,
    )

    libro = _libro_vacio()

    foto = _plantilla_con_trent()

    tablon = _tablon_con_la_compra()

    with tempfile.TemporaryDirectory() as tmp:

        rutas = {
            "ruta_del_carril": Path(tmp) / "carril.jsonl",
            "ruta_de_viajes": Path(tmp) / "viajes.jsonl",
        }

        primera = recoger_compras_de_la_plantilla(
            foto, tablon, YO, ledger=libro, **rutas
        )

        segunda = recoger_compras_de_la_plantilla(
            foto, tablon, YO, ledger=libro, **rutas
        )

    assert len(primera["recogidas"]) == 1, primera

    assert segunda["recogidas"] == [], segunda

    assert len(libro["bids"]) == 1, libro


def test_una_plantilla_vacia_no_se_toma_por_buena() -> None:
    """
    REGLA 24. Tenemos 15 jugadores: una plantilla vacia es una
    lectura rota, no una plantilla sin nadie.

    Si se tomara por buena, esto no recogeria nada mientras
    parece que si — que es el fallo que vino a arreglar.
    """

    from src.intelligence.bid_outcome_ledger import (
        recoger_compras_de_la_plantilla,
    )

    libro = _libro_vacio()

    with tempfile.TemporaryDirectory() as tmp:

        visto = recoger_compras_de_la_plantilla(
            {"league": {"user": {"id": YO}}, "my_team": []},
            _tablon_con_la_compra(),
            YO,
            ledger=libro,
            ruta_del_carril=Path(tmp) / "carril.jsonl",
            ruta_de_viajes=Path(tmp) / "viajes.jsonl",
        )

    assert visto["available"] is False, visto

    assert "lectura rota" in visto["reason"], visto

    assert libro["bids"] == {}, libro


def test_cero_viajes_no_es_todo_bien() -> None:
    """
    EL INDICADOR QUE TAPABA EL FALLO.

    El panel decia "todos los viajes abiertos estan publicados"
    teniendo CERO viajes, mientras Trent estaba en el banquillo
    sin publicar.

    Un indicador que se enciende con la AUSENCIA de datos es la
    regla 24 y la doctrina 37 a la vez — y tapo justo el fallo
    que tenia que enseñar.
    """

    from src.actions.escaparate_executor import viajes_sin_listar

    ninguno = viajes_sin_listar([], [])

    assert ninguno["hay_viajes"] is False, ninguno

    assert ninguno["abiertos"] == 0, ninguno

    assert "no hay nada que mirar" in ninguno["reason"], ninguno

    assert "todo vaya bien" in ninguno["reason"], ninguno

    # Con un viaje publicado, SI es "todo bien" — y se distingue.
    bien = viajes_sin_listar(
        [{"player_id": TRENT_REAL, "name": "Trent"}],
        [{"player_id": TRENT_REAL}],
    )

    assert bien["hay_viajes"] is True, bien
    assert bien["ok"] is True, bien
    assert bien["abiertos"] == 1, bien

    # Y con uno sin publicar, rojo.
    mal = viajes_sin_listar(
        [{"player_id": TRENT_REAL, "name": "Trent"}], []
    )

    assert mal["ok"] is False, mal
    assert mal["hay_viajes"] is True, mal

    # La pantalla tiene que poder distinguir los tres.
    panel = (
        Path(__file__).parents[2] / "dashboard-v8" / "src"
        / "components" / "RendijaPanel.jsx"
    ).read_text(encoding="utf-8")

    for dato in ("hay_viajes", "NADA QUE MIRAR"):
        assert dato in panel, (
            f"la pantalla no distingue «cero viajes» de «todos "
            f"publicados»: falta `{dato}`"
        )


def test_un_viaje_sin_coste_sigue_contando_para_publicar() -> None:
    """
    EL SEGUNDO SITIO DONDE TRENT DESAPARECIA.

    `abiertos` aparta a `sin_coste` los viajes cuya ficha no trae
    `acquisition_cost`, y hace bien: `que_cobrar` no puede
    juzgarlos contra el suelo sin saber lo que costaron.

    Pero PUBLICAR no depende del coste. Trent se abrio como viaje
    y desaparecio de la cuenta por no traer coste: el panel decia
    "cero viajes" mientras el jugador estaba en el banquillo sin
    publicar.

    Dos filtros correctos por separado que juntos tapan el fallo.
    """

    import ast

    fuente = (
        Path(__file__).parents[2] / "src" / "telemetry"
        / "dashboard_state.py"
    ).read_text(encoding="utf-8")

    codigo = chr(10).join(
        linea
        for linea in fuente.splitlines()
        if not linea.strip().startswith("#")
    )

    assert 'sin_coste' in codigo, (
        "la telemetria no cuenta los viajes de coste desconocido "
        "para la comprobacion de sin listar: un viaje sin coste "
        "vuelve a ser invisible"
    )

    # Y el comportamiento, no solo el codigo.
    from src.actions.escaparate_executor import viajes_sin_listar

    sin_coste = [
        {
            "player_id": TRENT_REAL,
            "name": "Trent",
            "cost": 0,
            "opened_at": "2026-09-13T06:45:00+00:00",
        }
    ]

    visto = viajes_sin_listar(sin_coste, [])

    assert visto["ok"] is False, visto

    assert visto["abiertos"] == 1, visto

    assert "Trent" in visto["reason"], visto


def test_el_ciclo_recoge_tambien_por_la_plantilla() -> None:
    """
    Sin el enganche, la via no corre nunca y no haria ruido.
    """

    import ast

    fuente = (
        Path(__file__).parents[2] / "src" / "intelligence"
        / "bid_outcome_ledger.py"
    ).read_text(encoding="utf-8")

    dentro = set()

    for nodo in ast.walk(ast.parse(fuente)):

        if (
            isinstance(nodo, ast.FunctionDef)
            and nodo.name == "sync_bid_outcomes"
        ):
            for hijo in ast.walk(nodo):

                if isinstance(hijo, ast.Call) and isinstance(
                    hijo.func, ast.Name
                ):
                    dentro.add(hijo.func.id)

    for via in (
        "recoger_pujas_vivas",
        "recoger_compras_de_la_plantilla",
    ):
        assert via in dentro, (
            f"`sync_bid_outcomes` no llama a `{via}`: esa via no "
            f"corre nunca"
        )


TESTS = [
    test_el_libro_recoge_la_puja_que_no_anoto,
    test_el_nombre_sale_del_catalogo_si_la_venta_no_lo_trae,
    test_no_duplica_lo_que_ya_tiene,
    test_solo_recoge_pujas_NUESTRAS,
    test_el_origen_no_se_inventa,
    test_lo_recogido_se_resuelve_sin_esperar_otro_ciclo,
    test_aubameyang_se_cierra_como_perdida,
    test_el_ciclo_le_pasa_la_foto_al_libro,
    test_lo_que_se_resolvio_sin_nosotros_se_recoge,
    test_tambien_se_ve_lo_comprado_a_un_rival,
    test_la_hora_dice_si_es_la_de_la_puja_o_la_del_reset,
    test_la_plantilla_no_se_recoge_dos_veces,
    test_una_plantilla_vacia_no_se_toma_por_buena,
    test_cero_viajes_no_es_todo_bien,
    test_un_viaje_sin_coste_sigue_contando_para_publicar,
    test_el_ciclo_recoge_tambien_por_la_plantilla,
]


def main() -> None:
    fallos = 0

    for test in TESTS:
        try:
            test()
            print(f"OK   {test.__name__}")

        except AssertionError as error:
            fallos += 1
            print(f"FALLA {test.__name__}: {error}")

    print("=" * 60)
    print(
        f"EL LIBRO RECOGE V1: "
        f"{len(TESTS) - fallos}/{len(TESTS)} OK"
    )
    print("=" * 60)

    if fallos:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
