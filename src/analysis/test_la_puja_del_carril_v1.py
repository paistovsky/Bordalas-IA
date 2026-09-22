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

import os


# EL ENTORNO NO DECIDE ESTA GUARDIA  (doctrina 104, 20/09/2026)
#
#     Medido: con `BORDALAS_CUPO_POR_ENVIOS` y `BORDALAS_NO_REPETIR_LA_ESCRITURA` puestos en el
#     entorno, esta guardia se caia — y una guardia roja para el
#     paso «Validate optimized production cycle», o sea para EL
#     CICLO. Es lo que paso la noche del 20/09 con
#     `BORDALAS_OBJETIVOS_EL_CATALOGO`.
#
#     Este caso mide el comportamiento POR DEFECTO, asi que el
#     interruptor se apaga aqui. El comportamiento con el puesto
#     lo mide su propia guardia, que lo enciende y lo apaga ella.
os.environ.pop("BORDALAS_CUPO_POR_ENVIOS", None)
os.environ.pop("BORDALAS_NO_REPETIR_LA_ESCRITURA", None)

# Y LA REVENTA, QUE ES LO QUE ESTA GUARDIA MIDE (22/09/2026)
#
#     `BORDALAS_SIN_REVENTA` CIERRA la cesta de reventa, que es
#     justo el sujeto de este fichero. Con el puesto no hay
#     subasta que medir y esto se pone rojo sin que nada este
#     roto: la guardia se cae por su propia guarda de doctrina 24
#     —"si no, esta guardia no prueba nada"—, que dice la verdad.
#
#     Y NO ES UN CASO INCOMPLETO. No hay campo que anadirle a un
#     candidato de cartera para que sobreviva a un interruptor
#     que cierra la cartera entera: lo que se compra para
#     revender ES reventa. El unico arreglo honesto es el de
#     siempre (doctrina 104): la guardia pone su propio
#     interruptor. El comportamiento CON el puesto lo mide
#     `test_el_corte_y_el_cupo_v1`, que lo enciende y lo apaga
#     ella.
os.environ.pop("BORDALAS_SIN_REVENTA", None)

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
            # SU PROPIO LIBRO DE VIAJES, EN UN TEMPORAL.
            #
            #     Sin esto, `correr` preguntaba el cupo a
            #     `data/trading/libro_de_viajes.jsonl` —el de
            #     verdad—. `data/trading` se restaura entre
            #     ciclos, asi que la verja dependia de lo que
            #     Pepe hubiera hecho esa mañana:
            #
            #         08:23 verde · 10:07 verde · 10:50 ROJO
            #
            #     y el mismo commit. El ciclo de las 10:07 anoto
            #     a Trent como viaje y gasto el cupo del reset.
            #     Pepe se echaba el candado a si mismo
            #     trabajando.
            #
            #     Cero lecturas de `data/`. Ni con fallback, ni
            #     "si existe lo uso": el escenario lo monta esta
            #     guardia entero.
            ruta_de_viajes=tmp / "libro_de_viajes.jsonl",
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


def _una_vuelta(viajes_ya_abiertos=0):
    """
    Una vuelta del carril con TODO el escenario montado aqui.

    `viajes_ya_abiertos` permite probar el cupo sin depender de
    lo que haya hecho el bot: se escriben en el libro temporal.
    """

    import json
    import tempfile

    from datetime import timedelta

    libro = {"version": 1, "bids": {}}

    escritor = _EscritorDeMentira()

    with tempfile.TemporaryDirectory() as tmp:

        carpeta = Path(tmp)

        if viajes_ya_abiertos:

            # Dentro del ciclo de reset del fixture, para que
            # cuenten: `cuantos_en_este_reset` mira `at`.
            de_hoy = (CUANDO - timedelta(minutes=5)).isoformat()

            (carpeta / "libro_de_viajes.jsonl").write_text(
                "".join(
                    json.dumps(
                        {
                            "at": de_hoy,
                            "player_id": 900 + i,
                            "name": f"Ya comprado {i}",
                            "via": "RENDIJA",
                            "state": "ABIERTO",
                        }
                    )
                    + chr(10)
                    for i in range(viajes_ya_abiertos)
                ),
                encoding="utf-8",
            )

        salida = _correr(libro, escritor, carpeta)

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


def test_la_hora_de_la_puja_se_pasa_no_se_deduce() -> None:
    """
    LA VERJA ROJA DEL 13/09/2026, Y EL CICLO PARADO.

        04:45 verde · 04:50 verde · 07:15 ROJO · 08:07 ROJO

    Mismo commit. Entre medias solo paso el reset de las 07:00.

    EL MECANISMO

        El ejecutor anotaba `placed_at` con `_ahora()` en vez de
        con el `momento` que se le pasa. Y de `placed_at` depende
        CUAL ES EL RESET que resuelve la puja: una puesta antes
        de las 07:00 de Madrid se resuelve en el reset de ese
        dia; una puesta despues, en el del dia siguiente.

        Asi que al pasar el reset de las 07:00, la puja del
        fixture dejaba de estar resuelta y la guardia hermana se
        ponia roja sin que nadie hubiera tocado una linea.

    ES LA SEGUNDA VEZ. `test_peticiones_v1` deducia la fase del
    reloj en vez de que se la dieran. Una prueba que cambia con
    la hora y no con el codigo no prueba el codigo, y una que
    para el ciclo de produccion cuesta dinero: esta lo tuvo
    parado desde las 04:50.

    EL ARREGLO NUNCA ES RELAJAR LA ASERCION. Es que la hora se le
    PASE.
    """

    libro, escritor, salida = _una_vuelta()

    assert escritor.pujas, salida.get("reason")

    entrada = list(libro["bids"].values())[0]

    # LA HORA QUE SE LE DIO, no la del reloj de la maquina.
    assert entrada["placed_at"] == CUANDO.isoformat(), (
        f"`placed_at` sale {entrada['placed_at']} y se le paso "
        f"{CUANDO.isoformat()}: el ejecutor deduce la hora en vez "
        f"de usar la que recibe, y entonces esta guardia depende "
        f"del reloj"
    )

    # Y EL CODIGO, no solo el resultado: que no vuelva a
    # colarse un `_ahora()` donde hay un `momento`.
    fuente = (
        RAIZ / "src" / "actions" / "carril_executor.py"
    ).read_text(encoding="utf-8")

    codigo = chr(10).join(
        linea
        for linea in fuente.splitlines()
        if not linea.strip().startswith("#")
    )

    assert "puesta_en = _ahora()" not in codigo, (
        "ha vuelto `puesta_en = _ahora()`: es el fallo que dejo "
        "el ciclo parado el 13/09"
    )

    # Los `_ahora()` que QUEDAN son de `ran_at` —cuando corrio de
    # verdad— y esos si son ahora: es el indicador de la doctrina
    # 37, que lo enciende el hecho.
    assert codigo.count("_ahora()") == 4, (
        f"hay {codigo.count('_ahora()')} usos de `_ahora()` y se "
        f"esperaban 4 (la definicion y los tres `ran_at`). Si has "
        f"añadido uno, comprueba que no sea una hora que deberia "
        f"venir dada"
    )


def test_el_cupo_del_reset_se_prueba_con_libro_propio() -> None:
    """
    LO QUE SE GANA AL MONTAR EL ESCENARIO UNO MISMO.

    Mientras el cupo salia del libro de verdad, esta guardia no
    podia probarlo: dependia de si el bot habia comprado esa
    mañana. Con el libro propio se prueba en los dos sentidos,
    siempre igual.

    Cupo 1 (PRUEBA_DE_HUMO): con cero viajes abiertos se puja;
    con uno, no. Y la guardia NO relaja nada — sigue exigiendo
    que con el cupo libre el carril puje de verdad.
    """

    from src.analysis.la_rendija import CUPO_DE_LA_PRUEBA

    assert CUPO_DE_LA_PRUEBA == 1, CUPO_DE_LA_PRUEBA

    # Cupo libre: PUJA.
    _l, escritor, salida = _una_vuelta(viajes_ya_abiertos=0)

    assert escritor.pujas, salida.get("reason")

    # Cupo gastado: no puja, y lo dice con el motivo bueno.
    _l2, agotado, bloqueada = _una_vuelta(viajes_ya_abiertos=1)

    assert agotado.pujas == [], (
        "el carril puja con el cupo del reset gastado"
    )

    assert "Ya van 1" in (bloqueada.get("reason") or ""), (
        bloqueada
    )

    assert bloqueada.get("blocked_by") == "CUPO_DEL_RESET", (
        bloqueada
    )


TESTS = [
    test_la_puja_del_carril_se_anota,
    test_el_carril_tambien_pierde,
    test_el_carril_no_puja_redondo,
    test_el_desvio_no_pasa_del_tope_por_operacion,
    test_el_carril_llama_al_desvio_por_donde_la_rueda,
    test_la_hora_de_la_puja_se_pasa_no_se_deduce,
    test_el_cupo_del_reset_se_prueba_con_libro_propio,
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
