"""
El libro de aciertos de la valoracion y la foto de cada jornada.

LO QUE SE PROTEGE (23/09/2026)

    1. Se apunta el tablero de hoy: fecha, jugador, valor, precio,
       puja. Una linea por jugador y dia de mercado: dos vueltas el
       mismo dia no duplican.
    2. A los 7 y a los 14 dias, la primera vuelta que llega rellena
       precio, puntos y partidos. Antes, no.
    3. Con una foto de otro dia -la del 13/09 que usa la verja- o
       sin saber de cuando es, NO se escribe nada.
    4. La jornada cerrada sale del calendario, y un aplazado semanas
       despues no deja la jornada abierta para siempre.
    5. Una foto por jornada: la segunda vuelta no la duplica.

LA GUARDIA MUERDE SI EL CASO VIENE VACIO

    Sin tablero no hay nada que apuntar y la 1 pasaria con cero
    lineas. Lo primero es exigir que se escriban.

NO LEE EL MUNDO

    Escribe en un directorio temporal. Los instantes se pasan: no se
    mira el reloj. `data/` no se toca.

COMO SE USA

    python -m src.analysis.test_el_libro_de_la_valoracion_v1
"""

from __future__ import annotations

import json
import tempfile

from pathlib import Path

from src.intelligence.libro_de_la_valoracion import (
    apuntar_la_foto_de_la_jornada,
    apuntar_la_valoracion,
    la_ultima_jornada_cerrada,
)


HOY = "2026-09-23T09:00:00+00:00"

TABLERO = [
    {"id": 2044, "name": "Ceballos", "our_value": 4_254_299,
     "market_price": 4_180_000, "bid": 0, "live_bid": 0,
     "decision": "RENDIMIENTO_INSUFICIENTE", "intent": "SPECULATION",
     "seller_kind": "COMPUTER"},
    {"id": 1969, "name": "Unai Lopez", "our_value": 2_800_000,
     "market_price": 2_750_000, "bid": 2_756_876, "live_bid": 0,
     "decision": "PUJAR", "intent": "SPECULATION",
     "seller_kind": "COMPUTER"},
]


def _catalogo(puntos=13, precio=4_180_000) -> dict:
    return {
        2044: {"points": puntos, "playedHome": 1, "playedAway": 2,
               "price": precio},
        1969: {"points": 20, "playedHome": 3, "playedAway": 3,
               "price": 2_700_000},
    }


def _lineas(ruta: Path) -> list:
    if not ruta.exists():
        return []
    return [
        json.loads(x)
        for x in ruta.read_text(encoding="utf-8").splitlines()
        if x.strip()
    ]


# ============================================================
# 1-2. APUNTAR Y RELLENAR
# ============================================================

def test_se_apunta_una_vez_y_se_rellena_a_su_plazo() -> None:

    assert TABLERO, "sin tablero esta guardia no prueba nada"

    with tempfile.TemporaryDirectory() as tmp:

        ruta = Path(tmp) / "libro.jsonl"

        r = apuntar_la_valoracion(
            TABLERO, _catalogo(), foto_at=HOY, at=HOY, ruta=ruta
        )

        assert r["written"] and r["nuevas"] == 2, r

        filas = _lineas(ruta)

        assert len(filas) == 2, filas

        ceballos = next(f for f in filas if f["id"] == 2044)

        assert ceballos["dia"] == "2026-09-23", ceballos
        assert ceballos["value"] == 4_254_299
        assert ceballos["price"] == 4_180_000
        assert ceballos["bid"] == 0
        assert "d7" not in ceballos and "d14" not in ceballos

        # La misma vuelta, una hora despues: no duplica.
        r = apuntar_la_valoracion(
            TABLERO, _catalogo(), foto_at="2026-09-23T10:00:00+00:00",
            at="2026-09-23T10:00:00+00:00", ruta=ruta,
        )

        assert r["written"] is False, r
        assert len(_lineas(ruta)) == 2

        # A los 6 dias, nada que rellenar.
        seis = "2026-09-29T09:00:00+00:00"

        apuntar_la_valoracion(
            [], _catalogo(), foto_at=seis, at=seis, ruta=ruta
        )

        assert all("d7" not in f for f in _lineas(ruta))

        # A los 7, se rellena con lo de ese dia.
        siete = "2026-09-30T09:00:00+00:00"

        r = apuntar_la_valoracion(
            [], _catalogo(puntos=19, precio=4_500_000),
            foto_at=siete, at=siete, ruta=ruta,
        )

        assert r["rellenadas"] == 2, r

        ceballos = next(f for f in _lineas(ruta) if f["id"] == 2044)

        assert ceballos["d7"] == {
            "dia": "2026-09-30", "price": 4_500_000, "points": 19,
            "played": 3,
        }, ceballos
        assert "d14" not in ceballos

        catorce = "2026-10-07T09:00:00+00:00"

        apuntar_la_valoracion(
            [], _catalogo(puntos=25), foto_at=catorce, at=catorce,
            ruta=ruta,
        )

        ceballos = next(f for f in _lineas(ruta) if f["id"] == 2044)

        assert ceballos["d14"]["points"] == 25, ceballos
        assert ceballos["d7"]["points"] == 19, "el d7 se ha pisado"


# ============================================================
# 3. CON LA FOTO DE OTRO DIA NO SE ESCRIBE
# ============================================================

def test_con_una_foto_vieja_no_se_escribe() -> None:

    with tempfile.TemporaryDirectory() as tmp:

        ruta = Path(tmp) / "libro.jsonl"
        fotos = Path(tmp) / "fotos.jsonl"

        for foto in ("2026-09-13T17:17:17", None):

            r = apuntar_la_valoracion(
                TABLERO, _catalogo(), foto_at=foto, at=HOY, ruta=ruta
            )

            assert r["written"] is False, (foto, r)

            r = apuntar_la_foto_de_la_jornada(
                _catalogo(), CALENDARIO, foto_at=foto, at=HOY,
                ruta=fotos,
            )

            assert r["written"] is False, (foto, r)

        assert not ruta.exists() and not fotos.exists()


# ============================================================
# 4-5. LA JORNADA CERRADA Y SU FOTO
# ============================================================

CALENDARIO = [
    {
        "matchday": 6,
        "first_kickoff": "2026-09-15T19:00:00+02:00",
        "matches": [
            {"kickoff": "2026-09-15T19:00:00+02:00"},
            {"kickoff": "2026-09-17T21:00:00+02:00"},
            # Aplazado: se juega un mes despues.
            {"kickoff": "2026-10-21T20:00:00+02:00"},
        ],
    },
    {
        "matchday": 7,
        "first_kickoff": "2026-09-18T21:00:00+02:00",
        "matches": [
            {"kickoff": "2026-09-18T21:00:00+02:00"},
            {"kickoff": "2026-09-20T21:00:00+02:00"},
        ],
    },
    {
        "matchday": 8,
        "first_kickoff": "2026-10-09T21:00:00+02:00",
        "matches": [{"kickoff": "2026-10-09T21:00:00+02:00"}],
    },
]


def test_la_jornada_cerrada_sale_del_calendario() -> None:

    # Durante la J7: la ultima cerrada es la 6, aunque tenga un
    # aplazado en octubre.
    assert la_ultima_jornada_cerrada(
        CALENDARIO, "2026-09-19T12:00:00+00:00"
    )["jornada"] == 6

    # El ultimo partido de la J7 empieza el 20/09 a las 21:00 de
    # Madrid: cerrada dos horas despues, y no antes.
    assert la_ultima_jornada_cerrada(
        CALENDARIO, "2026-09-20T20:59:00+00:00"
    )["jornada"] == 6

    cerrada = la_ultima_jornada_cerrada(
        CALENDARIO, "2026-09-20T21:00:00+00:00"
    )

    assert cerrada["jornada"] == 7, cerrada

    assert la_ultima_jornada_cerrada([], HOY) is None


def test_una_foto_por_jornada() -> None:

    with tempfile.TemporaryDirectory() as tmp:

        ruta = Path(tmp) / "fotos.jsonl"

        r = apuntar_la_foto_de_la_jornada(
            _catalogo(), CALENDARIO, foto_at=HOY, at=HOY, ruta=ruta
        )

        assert r["written"] and r["jornada"] == 7, r

        linea = _lineas(ruta)[0]

        assert linea["players"]["2044"] == [13, 3, 4_180_000], linea

        r = apuntar_la_foto_de_la_jornada(
            _catalogo(), CALENDARIO, foto_at=HOY, at=HOY, ruta=ruta
        )

        assert r["written"] is False, r
        assert len(_lineas(ruta)) == 1


TESTS = [
    test_se_apunta_una_vez_y_se_rellena_a_su_plazo,
    test_con_una_foto_vieja_no_se_escribe,
    test_la_jornada_cerrada_sale_del_calendario,
    test_una_foto_por_jornada,
]


def main() -> None:

    print()
    print("=" * 60)
    print("EL LIBRO DE LA VALORACION V1")
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
