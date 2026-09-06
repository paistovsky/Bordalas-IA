"""
Quien tenia razon se contesta con numeros, o no se contesta.

SINTOMA

    Cuatro noches construyendo una maquina de valorar cada vez
    mejor. Cada noche la maquina concluye, con razon medida, que
    no hay que comprar nada. Y nadie habia mirado que paso
    despues con lo que rechazo.

    Mientras tanto Pollo compro siete jugadores por 21.198.020
    EUR y va primero.

CAUSA

    La casa puntua a las fuentes con Brier desde el 06/09 —
    FutbolFantasy saca 0,3365, peor que tirar una moneda — y
    nunca se habia aplicado esa vara a sus propias decisiones.

CONSECUENCIA

    Un marcador de rivales es facil de hacer mal, y de tres
    formas:

        - contando dos veces lo que el tablon repite;
        - olvidando los DIAS, y entonces una compra de hace cinco
          horas parece un veredicto sobre la tesis;
        - mirando solo las compras, y entonces Pollo parece un
          acumulador cuando en realidad vendio 21.259.800 EUR el
          mismo dia que compro 21.198.020.

    Las tres estan aqui dentro.
"""

from __future__ import annotations

import ast
import json

from datetime import datetime, timedelta, timezone
from pathlib import Path

from src.analysis.hold_backtest import store_depth
from src.analysis.price_store_fixture import almacen_de_mentira
from src.analysis.rejection_ledger import (
    HORIZON_DAYS,
    MIN_SAMPLE,
    empty_ledger,
    record_rejections,
    rule_backtest,
    settle_rejections,
    summary,
)
from src.analysis.rival_scoreboard import (
    build_scoreboard,
    manager_scoreboard,
    value_versus_points,
)


FOTO = Path("diagnostico/status.json")


def _produccion():
    if not FOTO.exists():
        return None

    return json.loads(FOTO.read_text(encoding="utf-8"))


# ============================================================
# 1. EL MARCADOR NO CUENTA DE MAS
# ============================================================


def test_el_tablon_repetido_no_se_cuenta_dos_veces() -> None:
    """
    EL CASO REAL

        Mikel Rodriguez aparece TRES veces vendido por Luismi el
        mismo dia por el mismo importe, y Ayoze dos. Contarlas
        como ventas distintas triplicaria el marcador.
    """

    repetido = {
        "meta": {"generated_at": "2026-09-06T12:33:05"},
        "rival_squads": {"managers": []},
        "league_center": {
            "market_feed": [
                {
                    "type": "SELL_TO_COMPUTER",
                    "player_id": 1,
                    "player_name": "Mikel Rodriguez",
                    "amount": 2_464_100,
                    "seller": "Luismi_Haz",
                    "buyer": "Computer",
                    "timestamp": 1788000000,
                }
            ]
            * 3
        },
    }

    marcador = manager_scoreboard(repetido, "Luismi_Haz")

    assert len(marcador["sells"]) == 1, (
        f"el tablon repetido produce {len(marcador['sells'])} "
        f"ventas de la misma"
    )
    assert marcador["sold_total"] == 2_464_100


def test_los_dias_viajan_con_cada_operacion() -> None:
    """
    Sin los dias, un -0,13 % parece un veredicto. Tres de las
    siete compras de Pollo son de hace cinco horas.
    """

    foto = _produccion()

    if not foto:
        return

    marcador = manager_scoreboard(foto, "Pollo17")

    if not marcador["available"]:
        return

    for compra in marcador["buys"]:
        assert "days" in compra and compra["days"] is not None, (
            f"{compra['player']} no dice cuantos dias han pasado"
        )

    for clave in ("min_days", "median_days", "max_days"):
        assert marcador[clave] is not None, (
            f"el marcador no publica `{clave}`"
        )


def test_las_ventas_se_miran_igual_que_las_compras() -> None:
    """
    Mirar solo las compras hace parecer a Pollo un acumulador.
    El 06/09 solto a Vinicius Jr por 17.633.400 el mismo dia que
    compraba.
    """

    foto = _produccion()

    if not foto:
        return

    marcador = manager_scoreboard(foto, "Pollo17")

    if not marcador["available"]:
        return

    assert marcador["sells"], (
        "el marcador de Pollo no trae ninguna venta: se le esta "
        "mirando media foto"
    )
    assert marcador["sold_total"] > 0


def test_lo_que_no_se_puede_medir_se_dice() -> None:
    """
    Un jugador vendido al Computer desaparece de todas las
    plantillas, asi que no hay precio de hoy con el que
    compararlo. `None` no es cero.
    """

    foto = _produccion()

    if not foto:
        return

    marcador = manager_scoreboard(foto, "Luismi_Haz")

    for venta in marcador["sells"]:

        if venta.get("avoided") is None:
            assert venta.get("unmeasurable_reason"), (
                f"{venta['player']} no se puede medir y no dice "
                f"por que"
            )


def test_el_marcador_no_lanza_con_basura() -> None:
    for entrada in (None, {}, {"league_center": None}):
        marcador = manager_scoreboard(entrada, "Pollo17")

        assert isinstance(marcador, dict)
        assert "buys" in marcador


# ============================================================
# 2. LA CORRELACION SE PUBLICA CON SU LIMITE
# ============================================================


def test_con_siete_managers_la_correlacion_no_decide() -> None:
    """
    r = +0,553 entre valor de plantilla y puntos. Para que eso
    distinga de casualidad con n=7 hace falta 0,754.

    Publicar el r sin el critico seria dar por demostrado lo que
    no lo esta.
    """

    foto = _produccion()

    if not foto:
        return

    correlacion = value_versus_points(foto)

    if not correlacion["available"]:
        return

    assert "critical_r" in correlacion
    assert "significant" in correlacion

    assert correlacion["critical_r"] > 0.5, (
        "el valor critico parece de otra muestra"
    )

    if abs(correlacion["r_value_points"]) < correlacion["critical_r"]:
        assert correlacion["significant"] is False
        assert "No lo alcanza" in correlacion["reason"]


# ============================================================
# 3. EL LIBRO DE RECHAZOS
# ============================================================


def _libro_con(entradas, ahora):
    libro = empty_ledger()

    return record_rejections(
        entradas,
        ledger=libro,
        save=False,
        now=ahora,
    )


def test_un_libro_vacio_dice_que_esta_vacio() -> None:
    """
    Empieza hoy. Publicar una mediana de dos rechazos seria
    exactamente el error que este proyecto lleva un mes evitando.
    """

    resumen = summary(empty_ledger())

    assert resumen["closed"] == 0
    assert resumen["enough"] is False
    assert resumen["reason"]
    assert "median_return_percent" not in resumen


def test_una_puja_no_es_un_rechazo() -> None:
    ahora = datetime(2026, 9, 6, tzinfo=timezone.utc)

    libro = _libro_con(
        [
            {"id": 1, "name": "Pujado", "decision": "BID",
             "market_price": 1_000_000},
            {"id": 2, "name": "Rechazado", "decision": "NO_COMPENSA",
             "market_price": 1_000_000},
        ],
        ahora,
    )

    assert len(libro["rejections"]) == 1
    assert list(libro["rejections"].values())[0]["player_name"] == (
        "Rechazado"
    )


def test_el_mismo_rechazo_dos_ciclos_no_son_dos() -> None:
    """
    El ciclo corre cada media hora. Sin esto, un rechazo se
    apuntaria 48 veces al dia y la muestra seria mentira.
    """

    ahora = datetime(2026, 9, 6, 10, tzinfo=timezone.utc)

    fila = [
        {"id": 7, "name": "X", "decision": "NO_COMPENSA",
         "market_price": 1_000_000}
    ]

    libro = _libro_con(fila, ahora)

    libro = record_rejections(
        fila,
        ledger=libro,
        save=False,
        now=ahora + timedelta(hours=6),
    )

    assert len(libro["rejections"]) == 1


def test_se_cierra_a_los_tres_dias_con_el_precio_de_entonces() -> None:
    ahora = datetime(2026, 9, 6, tzinfo=timezone.utc)

    libro = _libro_con(
        [
            {"id": 7, "name": "X", "decision": "NO_COMPENSA",
             "market_price": 1_000_000}
        ],
        ahora,
    )

    # Antes de vencer no se toca.
    libro = settle_rejections(
        {"7": 1_100_000},
        ledger=libro,
        save=False,
        now=ahora + timedelta(days=1),
    )

    assert list(libro["rejections"].values())[0]["outcome"] == (
        "PENDING"
    )

    # Y al vencer, con el precio de entonces.
    libro = settle_rejections(
        {"7": 1_100_000},
        ledger=libro,
        save=False,
        now=ahora + timedelta(days=HORIZON_DAYS, hours=1),
    )

    entrada = list(libro["rejections"].values())[0]

    assert entrada["outcome"] == "SUBIO"
    assert entrada["return_percent"] == 10.0

    resumen = summary(libro)

    assert resumen["closed"] == 1
    assert resumen["rose"] == 1
    assert resumen["would_have_gained"] == 100_000
    assert resumen["enough"] is False, (
        "un solo rechazo cerrado no puede dar por buena una "
        "mediana"
    )


def test_sin_precio_al_vencer_se_dice() -> None:
    ahora = datetime(2026, 9, 6, tzinfo=timezone.utc)

    libro = _libro_con(
        [
            {"id": 9, "name": "Y", "decision": "SIN_VALOR",
             "market_price": 500_000}
        ],
        ahora,
    )

    libro = settle_rejections(
        {},
        ledger=libro,
        save=False,
        now=ahora + timedelta(days=HORIZON_DAYS + 1),
    )

    assert list(libro["rejections"].values())[0]["outcome"] == (
        "SIN_PRECIO"
    )


# ============================================================
# 4. EL RETROTEST DE NUESTRA PROPIA REGLA
# ============================================================


def test_la_regla_discrimina_de_verdad() -> None:
    """
    EL NUMERO QUE CONTESTA AL ENCARGO

        Aplicando la regla de Pepe a las operaciones del almacen,
        lo que ACEPTA tiene que rendir mas que lo que RECHAZA. Si
        no, la regla no separa nada y sobra.

        Y hay que decirlo con la trampa delante: los cortes de la
        regla se calibraron sobre ESTOS MISMOS datos, asi que
        esto mide coherencia interna, no acierto fuera de
        muestra. Para eso esta el libro de arriba.
    """

    resultado = rule_backtest()

    if not resultado.get("available"):
        return

    aceptado = resultado["accepted"]
    rechazado = resultado["rejected"]

    if not (aceptado.get("enough") and rechazado.get("enough")):
        return

    assert resultado["discriminates"] is True, (
        f"lo aceptado rinde {aceptado['median'] * 100:+.2f} % y lo "
        f"rechazado {rechazado['median'] * 100:+.2f} %: la regla "
        f"no separa nada"
    )

    assert aceptado["loss_rate"] < rechazado["loss_rate"], (
        "lo aceptado pierde mas a menudo que lo rechazado"
    )


def test_los_dos_grupos_publican_su_muestra() -> None:
    resultado = rule_backtest()

    if not resultado.get("available"):
        return

    for grupo in ("accepted", "rejected"):
        assert "n" in resultado[grupo]
        assert "enough" in resultado[grupo]

        if not resultado[grupo]["enough"]:
            assert resultado[grupo].get("reason")

    assert MIN_SAMPLE == 30


# ============================================================
# 5. CUANTO HISTORICO HAY DE VERDAD
# ============================================================


def test_los_dias_de_historico_se_publican() -> None:
    """
    Toda la discusion de "el almacen son seis dias" salio de
    mirar una copia local caducada. Que la pregunta no haya que
    volver a hacerla.

    SOBRE EL FIXTURE (17/09/2026)

        Esto llamaba a `store_depth()` a secas, que lee el
        almacen real. En un checkout limpio -lo que tiene Actions
        cuando la cache no acierta- el objeto venia sin
        `retention_days` y la guardia se caia.

        Eran dos fallos en uno: la guardia leia estado, y
        `store_depth` cambiaba de FORMA segun hubiera almacen o
        no. Lo segundo se arreglo en el modulo; lo primero, aqui.
    """

    with almacen_de_mentira() as almacen:

        profundidad = store_depth(almacen)

        for clave in (
            "days",
            "oldest",
            "newest",
            "retention_days",
            "measurable_horizons",
        ):
            assert clave in profundidad, f"falta `{clave}`"

        assert profundidad["available"]
        assert profundidad["days"] >= 1
        assert profundidad["oldest"]
        assert profundidad["retention_days"] == 60


def test_la_profundidad_tiene_la_misma_forma_sin_almacen() -> None:
    """
    LO QUE PARTIO LA VERJA

        Sin almacen faltaban claves, y quien las daba por seguras
        se caia. La ausencia de dato se dice con el valor vacio y
        el motivo escrito, nunca quitando el campo.
    """

    vacio = store_depth(Path("no") / "existe.json")

    assert vacio["available"] is False
    assert vacio["reason"]

    for clave in (
        "days",
        "oldest",
        "newest",
        "retention_days",
        "measurable_horizons",
    ):
        assert clave in vacio, (
            f"sin almacen falta `{clave}`: la forma del objeto "
            f"cambia con el contenido"
        )

    assert vacio["measurable_horizons"] == []


def test_los_horizontes_medibles_salen_de_los_dias() -> None:
    """
    No se dice que se puede medir un horizonte de 10 dias con
    seis dias de historico.
    """

    with almacen_de_mentira() as almacen:

        profundidad = store_depth(almacen)

        assert profundidad["measurable_horizons"], (
            "el fixture no produce ningun horizonte medible"
        )

        for m in profundidad["measurable_horizons"]:
            assert m + 2 <= profundidad["days"], (
                f"dice poder medir un horizonte de {m} dias con "
                f"{profundidad['days']} dias de historico"
            )


# ============================================================
# 6. NI DECIDE NI REVIENTA
# ============================================================


def test_el_arbitro_no_decide_nada() -> None:
    prohibidos = (
        "autopilot_executor",
        "write_client",
        "BiwengerWriteClient",
        "optimal_bid",
    )

    for ruta in (
        "src/analysis/rival_scoreboard.py",
        "src/analysis/rejection_ledger.py",
    ):
        arbol = ast.parse(
            Path(ruta).read_text(encoding="utf-8")
        )

        for nodo in ast.walk(arbol):

            if isinstance(nodo, (ast.Import, ast.ImportFrom)):

                texto = ast.dump(nodo)

                for prohibido in prohibidos:
                    assert prohibido not in texto, (
                        f"{ruta} importa {prohibido}: deja de ser "
                        f"un observador"
                    )


def test_el_bloque_entero_no_lanza() -> None:
    for entrada in (None, {}, {"race": None, "rival_squads": None}):
        bloque = build_scoreboard(entrada)

        assert isinstance(bloque, dict)
        assert bloque["observer_only"] is True


TESTS = [
    test_el_tablon_repetido_no_se_cuenta_dos_veces,
    test_los_dias_viajan_con_cada_operacion,
    test_las_ventas_se_miran_igual_que_las_compras,
    test_lo_que_no_se_puede_medir_se_dice,
    test_el_marcador_no_lanza_con_basura,
    test_con_siete_managers_la_correlacion_no_decide,
    test_un_libro_vacio_dice_que_esta_vacio,
    test_una_puja_no_es_un_rechazo,
    test_el_mismo_rechazo_dos_ciclos_no_son_dos,
    test_se_cierra_a_los_tres_dias_con_el_precio_de_entonces,
    test_sin_precio_al_vencer_se_dice,
    test_la_regla_discrimina_de_verdad,
    test_los_dos_grupos_publican_su_muestra,
    test_los_dias_de_historico_se_publican,
    test_la_profundidad_tiene_la_misma_forma_sin_almacen,
    test_los_horizontes_medibles_salen_de_los_dias,
    test_el_arbitro_no_decide_nada,
    test_el_bloque_entero_no_lanza,
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
    print(f"EL ARBITRO V1: {len(TESTS) - fallos}/{len(TESTS)} OK")
    print("=" * 60)

    if fallos:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
