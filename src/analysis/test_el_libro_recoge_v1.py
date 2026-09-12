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

    visto = recoger_pujas_vivas(
        _foto_con_la_puja_viva(), YO, ledger=libro
    )

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

    primera = recoger_pujas_vivas(foto, YO, ledger=libro)

    segunda = recoger_pujas_vivas(foto, YO, ledger=libro)

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

    tercera = recoger_pujas_vivas(foto, YO, ledger=otro)

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

    recoger_pujas_vivas(
        _foto_con_la_puja_viva(), YO, ledger=libro
    )

    jugadores = {
        e["player_id"] for e in libro["bids"].values()
    }

    assert jugadores == {TRENT_ID}, (
        f"se ha colado una oferta que no es nuestra: {jugadores}"
    )

    # Y sin saber quienes somos NO se recoge nada: marcar pujas
    # ajenas como nuestras es peor que no verlas (regla 24).
    a_ciegas = _libro_vacio()

    visto = recoger_pujas_vivas(
        _foto_con_la_puja_viva(), None, ledger=a_ciegas
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

        recoger_pujas_vivas(
            _foto_con_la_puja_viva(),
            YO,
            ledger=libro,
            ruta_del_carril=vacio,
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

        recoger_pujas_vivas(
            _foto_con_la_puja_viva(),
            YO,
            ledger=libro,
            ruta_del_carril=del_carril,
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

        recoger_pujas_vivas(
            _foto_con_la_puja_viva(),
            YO,
            ledger=libro,
            ruta_del_carril=del_carril,
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

    recoger_pujas_vivas(
        _foto_con_la_puja_viva(), YO, ledger=libro
    )

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


TESTS = [
    test_el_libro_recoge_la_puja_que_no_anoto,
    test_el_nombre_sale_del_catalogo_si_la_venta_no_lo_trae,
    test_no_duplica_lo_que_ya_tiene,
    test_solo_recoge_pujas_NUESTRAS,
    test_el_origen_no_se_inventa,
    test_lo_recogido_se_resuelve_sin_esperar_otro_ciclo,
    test_aubameyang_se_cierra_como_perdida,
    test_el_ciclo_le_pasa_la_foto_al_libro,
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
