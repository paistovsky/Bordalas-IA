"""
La puja del carril no entraba en el libro, y ademas era redonda.

SINTOMA (12/09/2026, 16:45)

    El carril hizo su primera puja de la historia: Trent,
    2.760.000 EUR. Confirmada al euro por tres vias —el tablon,
    la resta del `maximumBid` (16.715.906 -> 13.955.906) y la
    diferencia—. La puja es real.

    Pero al mirarla de cerca, dos cosas:

    1. NO ESTABA EN `bid_outcome_ledger`. Ni nombre, ni importe,
       ni marca de origen. Las cinco entradas del libro eran
       SUBASTA_CARTERA y ACQUISITION_BOARD.

       Ese mismo dia se habia hecho que el libro supiera perder.
       A las 07:00 del dia siguiente se resolvia la primera puja
       del carril y el libro no se iba a enterar de NINGUNA de
       las dos cosas: ni de que gano, ni de que perdio.

    2. ERA EL PRECIO DE MERCADO, REDONDO CLAVADO. Las cuatro de
       la rueda de esa misma mañana iban desviadas:

           Sotelo        1.604.001
           Caceres       1.503.751
           Diego Conde     240.601
           Fortuño         150.376
           ---------------------------
           Trent         2.760.000   <- el carril

       `bid_jitter.py` existe y la rueda lo usa. El carril no.
       Mismo patron que el plato vacio de esa tarde: la pieza
       montada y sin enchufar.

POR QUE EL DESVIO NO TIENE CONTRA

    Biwenger no publica como resuelve un empate. Como NO LO
    SABEMOS, pujar un numero raro un pelo por encima es
    estrictamente mejor que pujar el redondo. Y el desvio nunca
    pasa del techo ni del tope por operacion, asi que no puede
    empeorar nada.

REGLA 23

    No lee estado externo: el libro y el escritor se construyen
    aqui, y nada toca la red ni `data/`.
"""

from __future__ import annotations

from datetime import datetime, timezone

from pathlib import Path


RAIZ = Path(__file__).parents[2]


# LA PUJA REAL DEL 12/09/2026.
TRENT = {
    "id": 101,
    "name": "Trent",
    "position": 2,
    "market_price": 2_760_000,
    "status": "ok",
    "outside_computer_market": False,
}

CAJA = 4_333_406

# 16:45 de Madrid = 14:45 UTC. Fuera de la zona de silencio.
CUANDO = datetime(2026, 9, 12, 14, 45, tzinfo=timezone.utc)

# EL RITMO, QUE HACE FALTA PARA QUE HAYA MARGEN.
#
#     Sin ritmo —ni observado ni supuesto— `margen_esperado`
#     contesta "no se puede calcular" y el candidato queda fuera.
#     Es correcto: un margen sin ritmo seria un numero inventado.
#
#     Aqui se da el mediano del mercado de ese dia, +0,00 %/dia,
#     que es el que el carril uso de verdad con Trent.
RITMOS = {
    "101": {"rate_percent_per_day": 0.0},
    "999": {"rate_percent_per_day": 0.0},
}


class _EscritorDeMentira:
    """Acepta la puja y apunta con que importe la llamaron."""

    def __init__(self):
        self.pujas = []

    def place_bid(self, *, player_id, amount, execute=True):
        self.pujas.append(
            {"player_id": player_id, "amount": amount}
        )

        return {
            "sent": True,
            "success": True,
            "http_status": 200,
            "response": {"ok": True},
        }


def _correr(libro, escritor, tmp: Path):
    """Una vuelta del carril, sin red y sin tocar `data/`."""

    from src.actions.carril_executor import correr

    import src.intelligence.bid_outcome_ledger as ledger

    original_load = ledger.load_ledger

    original_save = ledger.save_ledger

    try:
        ledger.load_ledger = lambda path=None: libro

        ledger.save_ledger = lambda l, path=None: None

        return correr(
            accion_principal="MONITOR_OFFERS",
            cierres=[],
            objetivos=[TRENT],
            rates=RITMOS,
            prima_de_puja=0.0,
            curva=1.0,
            caja=CAJA,
            comprometido=0,
            presupuesto=2_109_030,
            escritor=escritor,
            disparo="workflow_dispatch",
            ahora=CUANDO,
            ruta_del_libro=tmp / "libro_del_carril.jsonl",
        )

    finally:
        ledger.load_ledger = original_load
        ledger.save_ledger = original_save


def _una_vuelta(tmp_dir=None):
    import tempfile

    libro = {"version": 1, "bids": {}}

    escritor = _EscritorDeMentira()

    with tempfile.TemporaryDirectory() as tmp:
        salida = _correr(libro, escritor, Path(tmp))

    return libro, escritor, salida


# ============================================================
# 1. LA PUJA DEL CARRIL SE ANOTA
# ============================================================


def test_la_puja_del_carril_se_anota() -> None:
    """
    Las cuatro cosas: nombre, importe, origen y hora.

    En el MISMO libro que la rueda. `target_source` es el campo
    que ya lleva el origen, asi que el carril usa ese y no uno
    nuevo (regla 33).
    """

    libro, escritor, salida = _una_vuelta()

    assert escritor.pujas, (
        f"el carril no llego a pujar: {salida.get('reason')}"
    )

    assert libro["bids"], (
        "el carril pujo y NO aparece en `bid_outcome_ledger`: su "
        "puja se resolvera sin que el libro se entere"
    )

    entrada = list(libro["bids"].values())[0]

    assert entrada["player_name"] == "Trent", entrada

    assert entrada["amount"] == escritor.pujas[0]["amount"], (
        "el libro anota un importe distinto del que se pujo"
    )

    assert entrada["target_source"] == "RENDIJA", entrada

    assert entrada["placed_at"], entrada

    assert entrada["outcome"] == "PENDING", entrada

    # Y el precio de mercado, que es lo que permitira saber
    # despues cuanta prima se pago.
    assert entrada["market_price"] == 2_760_000, entrada


def test_el_carril_tambien_pierde() -> None:
    """
    LA HERMANA, Y LA QUE IMPORTA.

    Una puja RENDIJA cuyo reset ya paso y cuyo jugador no esta en
    la plantilla es LOST, igual que las de la rueda. Si el carril
    entrara en el libro pero se quedara PENDING para siempre,
    estariamos donde estabamos.
    """

    from src.intelligence.bid_outcome_ledger import (
        reconcile,
        summary,
    )

    libro, escritor, _ = _una_vuelta()

    clave = list(libro["bids"])[0]

    # Se resolvio en el reset de las 07:00 del dia siguiente y
    # Trent NO esta en la plantilla.
    cerrado = reconcile(
        [],
        our_user_id=777,
        ledger=libro,
        save=False,
        ahora="2026-09-13T06:00:00+00:00",
        roster=[{"id": 1599, "name": "Jonny"}],
    )

    entrada = cerrado["bids"][clave]

    assert entrada["outcome"] == "LOST", entrada

    assert entrada["resolved_by"] == "RESET_SIN_JUGADOR", entrada

    assert summary(cerrado)["lost"] == 1, summary(cerrado)

    # Y si SI esta en la plantilla, se gano.
    ganada, _e, _s = _una_vuelta()

    clave = list(ganada["bids"])[0]

    gano = reconcile(
        [],
        our_user_id=777,
        ledger=ganada,
        save=False,
        ahora="2026-09-13T06:00:00+00:00",
        roster=[{"id": TRENT["id"], "name": "Trent"}],
    )

    # No la marca perdida: el jugador esta. Se queda esperando a
    # que el tablon confirme la operacion, que es lo correcto —
    # "lo tengo" no prueba por si solo que lo ganara ESTA puja.
    assert gano["bids"][clave]["outcome"] != "LOST", (
        gano["bids"][clave]
    )


# ============================================================
# 2. Y NO PUJA REDONDO
# ============================================================


def test_el_carril_no_puja_redondo() -> None:
    """
    EL CASO DE TRENT.

    2.760.000 es el precio de mercado exacto. La puja tiene que
    quedar por encima —nunca por debajo, que seria pagar la ficha
    por perder— y por debajo del techo del desvio.
    """

    from src.analysis.bid_jitter import jitter_ceiling

    _libro, escritor, salida = _una_vuelta()

    assert escritor.pujas, salida.get("reason")

    puja = escritor.pujas[0]["amount"]

    precio = TRENT["market_price"]

    assert puja != precio, (
        f"el carril puja {puja}, que es el precio de mercado "
        f"redondo clavado: es la puja de Trent otra vez"
    )

    assert puja > precio, (
        "puja por debajo del precio: eso es pagar la ficha por "
        "perder la subasta"
    )

    # Ni un multiplo redondo.
    for redondo in (10_000, 100_000, 1_000_000):
        assert puja % redondo != 0, (
            f"la puja {puja} es multiplo de {redondo}: sigue "
            f"siendo un numero que cualquiera escribiria"
        )

    # Y NUNCA por encima del techo del desvio.
    techo = jitter_ceiling(precio)

    assert puja - precio <= techo, (puja, precio, techo)

    # El tope por operacion del carril tampoco se pasa.
    assert puja <= 3_000_000, puja


def test_el_desvio_no_pasa_del_tope_por_operacion() -> None:
    """
    El desvio NUNCA puede sacar una puja por encima del tope.

    Con la caja justa para 2.760.001 y ni un euro mas, el carril
    tiene que pujar dentro del tope o no pujar — pero nunca
    pasarse por culpa del desvio.
    """

    import tempfile

    from src.actions.carril_executor import correr

    import src.intelligence.bid_outcome_ledger as ledger

    libro = {"version": 1, "bids": {}}

    escritor = _EscritorDeMentira()

    original_load, original_save = (
        ledger.load_ledger,
        ledger.save_ledger,
    )

    try:
        ledger.load_ledger = lambda path=None: libro
        ledger.save_ledger = lambda l, path=None: None

        with tempfile.TemporaryDirectory() as tmp:
            correr(
                accion_principal="MONITOR_OFFERS",
                cierres=[],
                objetivos=[TRENT],
                rates=RITMOS,
                prima_de_puja=0.0,
                curva=1.0,
                caja=2_760_001,
                comprometido=0,
                presupuesto=2_109_030,
                escritor=escritor,
                disparo="workflow_dispatch",
                ahora=CUANDO,
                ruta_del_libro=Path(tmp) / "l.jsonl",
            )

    finally:
        ledger.load_ledger = original_load
        ledger.save_ledger = original_save

    for puja in escritor.pujas:
        assert puja["amount"] <= 2_760_001, (
            f"el desvio ha sacado la puja por encima del tope: "
            f"{puja['amount']} > 2.760.001"
        )


def test_el_carril_llama_al_desvio_por_donde_la_rueda() -> None:
    """
    Del arbol, no de un grep: que el ejecutor llame de verdad a
    `apply_bid_jitter`, la misma funcion que usa la rueda, y no
    una copia.
    """

    import ast

    fuente = (
        RAIZ / "src" / "actions" / "carril_executor.py"
    ).read_text(encoding="utf-8")

    arbol = ast.parse(fuente)

    llamadas = {
        n.func.id
        for n in ast.walk(arbol)
        if isinstance(n, ast.Call)
        and isinstance(n.func, ast.Name)
    }

    assert "apply_bid_jitter" in llamadas, (
        "el carril no llama al desvio: volveria a pujar el "
        "precio redondo"
    )

    assert "record_bid" in llamadas, (
        "el carril no anota en el libro de pujas"
    )


TESTS = [
    test_la_puja_del_carril_se_anota,
    test_el_carril_tambien_pierde,
    test_el_carril_no_puja_redondo,
    test_el_desvio_no_pasa_del_tope_por_operacion,
    test_el_carril_llama_al_desvio_por_donde_la_rueda,
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
        f"LA PUJA DEL CARRIL V1: "
        f"{len(TESTS) - fallos}/{len(TESTS)} OK"
    )
    print("=" * 60)

    if fallos:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
