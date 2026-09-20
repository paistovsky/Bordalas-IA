"""
MIRAR contra la foto de produccion: las que dependen del mundo.

POR QUE EXISTEN AQUI Y NO ENTRE LAS GUARDIAS

    Estas ocho comprobaciones vivian en cuatro guardias de
    `src/analysis/` y leian `diagnostico/status.json` o el
    almacen de `data/`. Ninguna de las dos cosas esta versionada:
    la foto la rehace cada vuelta de produccion y el almacen
    crece solo.

    El 19/09 se separaron las dos poblaciones por
    `get_latest_snapshot(`, y estas se colaron porque no la
    llaman. El 20/09 se vio por que: `diagnostico/` se escapaba
    de las TRES redes a la vez.

        1. `las_dos_poblaciones()` miraba `get_latest_snapshot(`
        2. `test_verja_determinista_v1` buscaba `data/` ESCRITO
        3. el vigilante en ejecucion solo miraba `data/`

    Las tres ven ya `diagnostico/`. Estas se mudan, que es lo que
    tocaba desde el principio.

Y LA SEGUNDA RAZON, QUE ES PEOR QUE LA PRIMERA

    Las ocho empezaban por:

        foto = _produccion()
        if not foto:
            return

    En CI `diagnostico/` no existe. **Pasaban sin mirar nada**, y
    salian en verde. Rojos que no significan un fallo en el
    portatil, verdes que no significan nada en el servidor: las
    dos mitades de la doctrina 91, a la vez.

    Aqui eso deja de ser un problema. Un mirador que no encuentra
    la foto lo DICE y se va, que es lo honesto para una
    herramienta que se corre a mano.

LO QUE SIGUE EN LA VERJA

    Todo lo que se comprueba con datos fijos, que es la inmensa
    mayoria: 12 de 18 en el arbitro, 22 de 23 en el once, 17 de
    18 en el reloj de solvencia. Esas fallan solo si cambia el
    codigo, que es para lo que existe una guardia.

USO

    python scripts/mirar_contra_la_foto.py

    Solo lectura. No escribe en Biwenger ni en ningun libro.
"""

from __future__ import annotations

import json
import sys

from pathlib import Path


RAIZ = Path(__file__).resolve().parents[1]

if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

FOTO = RAIZ / "diagnostico" / "status.json"


def _produccion():
    """La foto de PRODUCCION. `None` si no esta."""

    if not FOTO.exists():
        return None

    try:
        return json.loads(FOTO.read_text(encoding="utf-8"))

    except (OSError, ValueError):
        return None


# ============================================================
# EL ARBITRO — el marcador de un manager y la correlacion
# ============================================================


def los_dias_viajan_con_cada_operacion(foto) -> list:
    """
    Sin los dias, un -0,13 % parece un veredicto. Tres de las
    siete compras de Pollo son de hace cinco horas.
    """

    from src.analysis.rival_scoreboard import manager_scoreboard

    marcador = manager_scoreboard(foto, "Pollo17")

    if not marcador["available"]:
        return [f"el marcador no esta: {marcador.get('reason')}"]

    fallos = []

    for compra in marcador["buys"]:
        if compra.get("days") is None:
            fallos.append(
                f"{compra['player']} no dice cuantos dias han "
                f"pasado"
            )

    for clave in ("min_days", "median_days", "max_days"):
        if marcador[clave] is None:
            fallos.append(f"el marcador no publica `{clave}`")

    return fallos


def las_ventas_se_miran_igual_que_las_compras(foto) -> list:
    """
    Mirar solo las compras hace parecer a Pollo un acumulador. El
    06/09 solto a Vinicius Jr por 17.633.400 el mismo dia que
    compraba.
    """

    from src.analysis.rival_scoreboard import manager_scoreboard

    marcador = manager_scoreboard(foto, "Pollo17")

    if not marcador["available"]:
        return [f"el marcador no esta: {marcador.get('reason')}"]

    fallos = []

    if not marcador["sells"]:
        fallos.append(
            "el marcador de Pollo no trae ninguna venta: se le "
            "esta mirando media foto"
        )

    if not marcador["sold_total"] > 0:
        fallos.append("`sold_total` no es positivo")

    return fallos


def lo_que_no_se_puede_medir_se_dice(foto) -> list:
    """
    Un jugador vendido al Computer desaparece de todas las
    plantillas, asi que no hay precio de hoy con el que
    compararlo. `None` no es cero.
    """

    from src.analysis.rival_scoreboard import manager_scoreboard

    marcador = manager_scoreboard(foto, "Luismi_Haz")

    return [
        f"{venta['player']} no se puede medir y no dice por que"
        for venta in marcador["sells"]
        if venta.get("avoided") is None
        and not venta.get("unmeasurable_reason")
    ]


def con_siete_managers_la_correlacion_no_decide(foto) -> list:
    """
    r = +0,553 entre valor de plantilla y puntos. Para que eso
    distinga de casualidad con n=7 hace falta 0,754.
    """

    from src.analysis.rival_scoreboard import value_versus_points

    correlacion = value_versus_points(foto)

    if not correlacion["available"]:
        return [
            f"no se pudo correlacionar: "
            f"{correlacion.get('reason')}"
        ]

    fallos = []

    for clave in ("critical_r", "significant"):
        if clave not in correlacion:
            fallos.append(f"no publica `{clave}`")

    if correlacion.get("critical_r", 0) <= 0.5:
        fallos.append("el valor critico parece de otra muestra")

    if abs(
        correlacion["r_value_points"]
    ) < correlacion["critical_r"]:

        if correlacion["significant"] is not False:
            fallos.append(
                "no alcanza el critico y aun asi se declara "
                "significativo"
            )

        if "No lo alcanza" not in correlacion["reason"]:
            fallos.append("no dice que no alcanza el critico")

    return fallos


def la_regla_discrimina_de_verdad(_foto) -> list:
    """
    Lo que la regla ACEPTA tiene que rendir mas que lo que
    RECHAZA. Si no, no separa nada y sobra.

    Con la trampa delante: los cortes se calibraron sobre ESTOS
    MISMOS datos, asi que mide coherencia interna, no acierto
    fuera de muestra.
    """

    from src.analysis.rejection_ledger import rule_backtest

    resultado = rule_backtest()

    if not resultado.get("available"):
        return [f"sin almacen: {resultado.get('reason')}"]

    aceptado = resultado["accepted"]
    rechazado = resultado["rejected"]

    if not (aceptado.get("enough") and rechazado.get("enough")):
        return [
            f"muestra corta: aceptados n={aceptado.get('n')}, "
            f"rechazados n={rechazado.get('n')}"
        ]

    fallos = []

    if resultado["discriminates"] is not True:
        fallos.append(
            f"lo aceptado rinde {aceptado['median'] * 100:+.2f} % "
            f"y lo rechazado {rechazado['median'] * 100:+.2f} %: "
            f"la regla no separa nada"
        )

    if not aceptado["loss_rate"] < rechazado["loss_rate"]:
        fallos.append(
            "lo aceptado pierde mas a menudo que lo rechazado"
        )

    return fallos


def los_dos_grupos_publican_su_muestra(_foto) -> list:

    from src.analysis.rejection_ledger import rule_backtest

    resultado = rule_backtest()

    if not resultado.get("available"):
        return [f"sin almacen: {resultado.get('reason')}"]

    fallos = []

    for grupo in ("accepted", "rejected"):

        for clave in ("n", "enough"):
            if clave not in resultado[grupo]:
                fallos.append(f"{grupo} no publica `{clave}`")

        if not resultado[grupo].get("enough") and not resultado[
            grupo
        ].get("reason"):
            fallos.append(
                f"{grupo} no llega a la muestra y no dice por que"
            )

    return fallos


# ============================================================
# EL ONCE — el sesgo por posicion
# ============================================================


def el_sesgo_sale_de_produccion_y_no_de_una_copia(foto) -> list:
    """La regla de la casa: se mide contra la foto de verdad."""

    from src.analysis.sesgo_posicion import sesgo_por_posicion

    sesgo = sesgo_por_posicion(foto)

    if not sesgo["available"]:
        return [f"sin sesgo: {sesgo.get('reason')}"]

    fallos = []

    if not sesgo["matchdays"] > 0:
        fallos.append("cero jornadas en la muestra")

    if not sesgo["sample"] > 20:
        fallos.append(
            f"la muestra de la liga se ha quedado en nada: "
            f"{sesgo['sample']}"
        )

    for fila in sesgo["rows"]:
        if fila["points_per_expected"] is None:
            fallos.append(
                f"{fila.get('name')} no publica "
                f"`points_per_expected`"
            )

    return fallos


# ============================================================
# EL RELOJ DE SOLVENCIA — la foto contra el plazo
# ============================================================


def la_foto_de_produccion_no_esta_en_el_plazo(foto) -> list:
    """
    Que con saldo positivo el reloj no apriete, y que a mas de
    seis horas del cierre no fuerce ninguna venta.
    """

    from src.analysis.solvency_clock import (
        SIN_DEUDA,
        SOLVENCY_DEADLINE_HOURS,
        EN_EL_PLAZO,
        build_solvency_clock,
    )

    resumen = foto.get("summary") or {}

    reloj = build_solvency_clock(
        resumen.get("balance"),
        resumen.get("hours_to_deadline"),
        offers=foto.get("offers"),
        market_clock=foto.get("market_clock"),
    )

    fallos = []

    if not reloj["available"]:
        return [f"el reloj no esta: {reloj.get('reason')}"]

    horas = resumen.get("hours_to_deadline")

    if horas is None or horas <= SOLVENCY_DEADLINE_HOURS:
        fallos.append(
            f"la foto esta DENTRO del plazo ({horas} h): lo de "
            f"abajo mide otra cosa"
        )

    if reloj["solvency_overrides_hold"] is not False:
        fallos.append("el reloj fuerza una venta lejos del plazo")

    if reloj["deficit"] == 0:
        if reloj["state"] != SIN_DEUDA:
            fallos.append(
                f"sin deficit y el estado es {reloj['state']}"
            )
    elif reloj["state"] == EN_EL_PLAZO:
        fallos.append(
            "hay deficit y el reloj dice que esta en el plazo"
        )

    return fallos


LAS_OCHO = (
    ("el arbitro", los_dias_viajan_con_cada_operacion),
    ("el arbitro", las_ventas_se_miran_igual_que_las_compras),
    ("el arbitro", lo_que_no_se_puede_medir_se_dice),
    ("el arbitro", con_siete_managers_la_correlacion_no_decide),
    ("el arbitro", la_regla_discrimina_de_verdad),
    ("el arbitro", los_dos_grupos_publican_su_muestra),
    ("el once", el_sesgo_sale_de_produccion_y_no_de_una_copia),
    ("el reloj", la_foto_de_produccion_no_esta_en_el_plazo),
)


def main() -> int:

    print("=" * 78)
    print("MIRAR CONTRA LA FOTO DE PRODUCCION")
    print("=" * 78)

    foto = _produccion()

    if foto is None:
        print(f"  No hay foto de produccion en {FOTO}.")
        print("  Esto no es un fallo: es que no hay nada que mirar.")
        print("=" * 78)
        return 0

    print(f"  Foto: {(foto.get('meta') or {}).get('generated_at')}")
    print()

    total = 0

    for familia, comprobacion in LAS_OCHO:

        try:
            fallos = comprobacion(foto)

        except Exception as error:                  # noqa: BLE001
            fallos = [
                f"reviento: {type(error).__name__}: {error}"
            ]

        total += len(fallos)

        print(
            f"  {'OK  ' if not fallos else 'MIRA'}  "
            f"[{familia}] {comprobacion.__name__}"
        )

        for fallo in fallos:
            print(f"          {fallo}")

    print()
    print("=" * 78)
    print(
        f"CONTRA LA FOTO: {len(LAS_OCHO)} comprobaciones, "
        f"{total} cosa(s) que mirar"
    )
    print("=" * 78)

    # Un mirador NO devuelve error por el estado del mundo: lo
    # enseña. Quien lo corre decide si le preocupa.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
