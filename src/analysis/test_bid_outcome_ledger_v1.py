"""
El libro de pujas: que pusimos, y como acabo.

SINTOMA

    El dueño pierde pujas y el sistema no registra ninguna. En el
    ledger, "Pepe Bordalas" tiene lost_bids = 0, y nuestro user_id no
    aparece como perdedor en ninguna de las 48 subastas del tablon.

CAUSA

    Poner la puja y saber quien la gano son dos momentos separados por
    horas, y nadie los cosia.

CONSECUENCIA

    Sin ese cosido, cualquier subida de agresividad se decide a ojo.
    Esta guardia protege el cosido: que se apunte al pujar, que se
    cierre contra el tablon, y que el resumen no invente numeros
    cuando no hay datos.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

from src.intelligence.bid_outcome_ledger import (
    load_ledger,
    record_bid,
    reconcile,
    summary,
    sync_bid_outcomes,
)

NOSOTROS = 14175949
RIVAL = 14178736

# El tablon fecha en epoch. Pujamos a las 10:00 del 30/08/2026, asi que
# una subasta que nos resuelve tiene que ser posterior a esa hora.
def _epoch(*args) -> float:
    return datetime(*args, tzinfo=timezone.utc).timestamp()

DESPUES = _epoch(2026, 8, 30, 11, 0)
ANTES = _epoch(2026, 8, 29, 10, 0)


def _tablon(operaciones: list, date: float = DESPUES) -> dict:
    return {
        "events": [
            {
                "event_id": "ev1",
                "type": "market",
                "date": date,
                "content": operaciones,
            }
        ]
    }


def _compra(player_id: int, comprador: int, importe: int) -> dict:
    return {
        "player": player_id,
        "to": {"id": comprador, "name": "quien sea"},
        "amount": importe,
        "bids": [],
    }


def test_una_puja_recien_puesta_queda_pendiente() -> None:
    libro = record_bid(
        26271, 1_000_000,
        player_name="Fulano", our_value=1_200_000, win_probability=0.7,
        placed_at="2026-08-30T10:00:00+00:00", ledger={"bids": {}}, save=False,
    )
    entrada = list(libro["bids"].values())[0]
    assert entrada["outcome"] == "PENDING", "una puja nace pendiente"
    assert entrada["amount"] == 1_000_000, "se guarda lo que pujamos"
    assert entrada["our_value"] == 1_200_000, "y lo que creiamos que valia"
    assert entrada["margin"] is None, "todavia no hay margen que medir"


def test_sin_fila_de_adquisicion_se_apunta_igual() -> None:
    """El respaldo legacy no trae valor ni probabilidad. No es excusa."""
    libro = record_bid(
        26271, 500_000, target_source="SPECULATION_SCORING",
        placed_at="2026-08-30T10:00:00+00:00", ledger={"bids": {}}, save=False,
    )
    entrada = list(libro["bids"].values())[0]
    assert entrada["our_value"] is None, "no habia valor, y no se inventa"
    assert entrada["win_probability"] is None, "ni probabilidad"
    assert entrada["outcome"] == "PENDING", "pero la puja se apunta"


def test_ganar_se_reconoce_por_el_comprador() -> None:
    libro = record_bid(26271, 1_000_000, placed_at="2026-08-30T10:00:00+00:00",
                       ledger={"bids": {}}, save=False)
    libro = reconcile(_tablon([_compra(26271, NOSOTROS, 1_000_000)]), NOSOTROS,
                      ledger=libro, save=False, ahora="2026-08-30T12:00:00+00:00")
    entrada = list(libro["bids"].values())[0]
    assert entrada["outcome"] == "WON", "el comprador somos nosotros"
    assert entrada["margin"] == 0, "ganar no tiene margen en contra"


def test_perder_mide_por_cuanto_nos_ganaron() -> None:
    libro = record_bid(26271, 1_000_000, placed_at="2026-08-30T10:00:00+00:00",
                       ledger={"bids": {}}, save=False)
    libro = reconcile(_tablon([_compra(26271, RIVAL, 1_150_000)]), NOSOTROS,
                      ledger=libro, save=False, ahora="2026-08-30T12:00:00+00:00")
    entrada = list(libro["bids"].values())[0]
    assert entrada["outcome"] == "LOST", "compro otro"
    assert entrada["margin"] == 150_000, "nos ganaron por 150.000, y se dice"
    assert entrada["winning_amount"] == 1_150_000, "y por cuanto se lo llevo"


def test_una_subasta_anterior_a_nuestra_puja_no_la_cierra() -> None:
    """La operacion de ayer no resuelve la puja de hoy."""
    tablon = _tablon([_compra(26271, RIVAL, 900_000)], date=ANTES)
    libro = record_bid(26271, 1_000_000, placed_at="2026-08-30T10:00:00+00:00",
                       ledger={"bids": {}}, save=False)
    libro = reconcile(tablon, NOSOTROS, ledger=libro, save=False,
                      ahora="2026-08-30T12:00:00+00:00")
    entrada = list(libro["bids"].values())[0]
    assert entrada["outcome"] == "PENDING", "sigue pendiente, no se cierra con lo viejo"


def test_lo_ya_resuelto_no_se_reescribe() -> None:
    libro = record_bid(26271, 1_000_000, placed_at="2026-08-30T10:00:00+00:00",
                       ledger={"bids": {}}, save=False)
    libro = reconcile(_tablon([_compra(26271, RIVAL, 1_150_000)]), NOSOTROS,
                      ledger=libro, save=False, ahora="2026-08-30T12:00:00+00:00")
    libro = reconcile(_tablon([_compra(26271, NOSOTROS, 9_999_999)]), NOSOTROS,
                      ledger=libro, save=False, ahora="2026-08-30T13:00:00+00:00")
    entrada = list(libro["bids"].values())[0]
    assert entrada["outcome"] == "LOST", "una puja cerrada no cambia de bando"
    assert entrada["margin"] == 150_000, "ni de margen"


def test_una_puja_muy_vieja_sin_rastro_se_da_por_perdida_de_vista() -> None:
    libro = record_bid(26271, 1_000_000, placed_at="2026-08-01T10:00:00+00:00",
                       ledger={"bids": {}}, save=False)
    libro = reconcile({"events": []}, NOSOTROS, ledger=libro, save=False,
                      ahora="2026-08-30T12:00:00+00:00")
    entrada = list(libro["bids"].values())[0]
    assert entrada["outcome"] == "UNKNOWN", "pasadas 72 h sin rastro, se cierra"
    assert entrada["margin"] is None, "y no se inventa un margen"


def test_el_tablon_tambien_vale_como_lista_pelada() -> None:
    """board_events.json es una lista, no un dict con "events"."""
    libro = record_bid(26271, 1_000_000, placed_at="2026-08-30T10:00:00+00:00",
                       ledger={"bids": {}}, save=False)
    lista = [{"event_id": "ev1", "type": "market", "date": DESPUES,
              "content": [_compra(26271, RIVAL, 1_150_000)]}]
    libro = reconcile(lista, NOSOTROS, ledger=libro, save=False,
                      ahora="2026-08-30T12:00:00+00:00")
    entrada = list(libro["bids"].values())[0]
    assert entrada["outcome"] == "LOST", "la lista pelada se entiende igual"
    assert entrada["margin"] == 150_000, "y mide el margen igual"


def test_el_enganche_del_ciclo_no_lanza_sin_tablon() -> None:
    """Un fallo del libro jamas puede detener un ciclo de produccion."""
    with TemporaryDirectory() as d:
        r = sync_bid_outcomes(
            NOSOTROS,
            board_path=Path(d) / "no-existe.json",
            path=Path(d) / "libro.json",
        )
        assert isinstance(r, dict), "devuelve un resumen aunque no haya tablon"
        assert r["available"] is False, "y dice que no hay datos"


def test_sin_saber_quienes_somos_no_se_cierra_nada() -> None:
    """Marcarlo todo perdido seria peor que no medir: mentiria."""
    libro = record_bid(26271, 1_000_000, placed_at="2026-08-30T10:00:00+00:00",
                       ledger={"bids": {}}, save=False)
    libro = reconcile(_tablon([_compra(26271, NOSOTROS, 1_000_000)]), None,
                      ledger=libro, save=False, ahora="2026-08-30T12:00:00+00:00")
    entrada = list(libro["bids"].values())[0]
    assert entrada["outcome"] == "PENDING", "sin nuestro id, no se toca la puja"


def test_el_resumen_sin_datos_dice_que_no_hay() -> None:
    r = summary({"bids": {}})
    assert r["available"] is False, "sin pujas, no hay nada que resumir"
    assert r["win_rate"] is None, "y NO un 0 % que parezca una medida"
    assert r["median_lost_margin"] is None, "ni una mediana inventada"


def test_el_resumen_cuenta_y_mide() -> None:
    libro = {"bids": {}}
    for i, (importe, ganador, pago) in enumerate([
        (1_000_000, RIVAL, 1_100_000),
        (2_000_000, RIVAL, 2_500_000),
        (3_000_000, NOSOTROS, 3_000_000),
    ]):
        libro = record_bid(100 + i, importe,
                           placed_at=f"2026-08-30T10:0{i}:00+00:00",
                           ledger=libro, save=False)
        libro = reconcile(
            _tablon([_compra(100 + i, ganador, pago)]),
            NOSOTROS, ledger=libro, save=False,
            ahora="2026-08-30T12:00:00+00:00")

    r = summary(libro)
    assert (r["placed"], r["won"], r["lost"]) == (3, 1, 2), "tres puestas, una ganada"
    assert abs(r["win_rate"] - 1 / 3) < 1e-9, "una de cada tres"
    assert r["mean_lost_margin"] == 300_000, "nos ganan por 300.000 de media"
    assert r["worst_lost_margin"] == 500_000, "y en el peor caso por 500.000"


def test_un_fichero_ilegible_no_tumba_nada() -> None:
    with TemporaryDirectory() as d:
        ruta = Path(d) / "roto.json"
        ruta.write_text("{esto no es json", encoding="utf-8")
        libro = load_ledger(ruta)
        assert libro["bids"] == {}, "un libro roto se lee como vacio"
        assert summary(libro)["available"] is False, "y el resumen lo dice"


TESTS = [
    test_una_puja_recien_puesta_queda_pendiente,
    test_sin_fila_de_adquisicion_se_apunta_igual,
    test_ganar_se_reconoce_por_el_comprador,
    test_perder_mide_por_cuanto_nos_ganaron,
    test_una_subasta_anterior_a_nuestra_puja_no_la_cierra,
    test_lo_ya_resuelto_no_se_reescribe,
    test_una_puja_muy_vieja_sin_rastro_se_da_por_perdida_de_vista,
    test_el_tablon_tambien_vale_como_lista_pelada,
    test_el_enganche_del_ciclo_no_lanza_sin_tablon,
    test_sin_saber_quienes_somos_no_se_cierra_nada,
    test_el_resumen_sin_datos_dice_que_no_hay,
    test_el_resumen_cuenta_y_mide,
    test_un_fichero_ilegible_no_tumba_nada,
]


def main() -> None:
    fallos = 0
    for test in TESTS:
        try:
            test()
            print(f"OK   {test.__name__}")
        except AssertionError as exc:
            fallos += 1
            print(f"FALLA {test.__name__}: {exc}")

    print("=" * 60)
    print(f"LIBRO DE PUJAS V1: {len(TESTS) - fallos}/{len(TESTS)} OK")
    print("=" * 60)

    if fallos:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
