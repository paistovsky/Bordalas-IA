"""
La puerta de validacion: las 66 guardias, en un solo sitio.

POR QUE LA LISTA VIVE AQUI Y NO EN EL WORKFLOW

    Hasta el 07/09/2026 era al reves: las 66 lineas estaban
    escritas a mano en `.github/workflows/bordalas-live.yml` y
    este script las leia de ahi con una expresion regular. La
    idea era buena -una sola fuente de verdad- pero el sitio era
    el equivocado.

    Con la lista en el YAML, cada guardia nueva habia que
    acordarse de ponerla en DOS sitios: el fichero del test y el
    workflow. Y el dia que se olvidara, CI habria corrido menos
    guardias que el dueño en local SIN AVISAR DE NADA: el paso
    habria salido verde por no haber ejecutado lo que faltaba.

    Un fallo silencioso, que es la clase mas cara.

    Ahora la lista esta aqui, el workflow llama a este script, y
    añadir una guardia es tocar una sola linea.

COMO SE AÑADE UNA GUARDIA

    Una linea en `TESTS`. Nada mas.

CODIGO DE SALIDA

    0 si pasan todas, 1 si falla cualquiera. De eso depende que
    el workflow pare el ciclo, asi que hay una guardia que lo
    comprueba: `test_puerta_una_sola_lista_v1`.

USO

    python scripts/run_validation_gate.py

    Parar en el primer fallo:

    python scripts/run_validation_gate.py --parar
"""

from __future__ import annotations

import argparse
import subprocess
import sys


# ============================================================
# LAS GUARDIAS
# ============================================================
#
#     El orden es el que tenian en el workflow: primero las del
#     ciclo, despues los candados de la auditoria del 15/08/2026
#     y al final lo que se ha ido añadiendo por noches.

TESTS = [
    "src.analysis.test_jp_profile_scope_v114",
    "src.analysis.test_multisource_starter_v1124",
    "src.analysis.test_v10_full_autonomous_live",
    "src.analysis.test_live_solvency_authority_v115",
    "src.telemetry.test_dashboard_execution_v121",
    "src.analysis.test_solvency_deadlock_v1",
    "src.analysis.test_write_path_guards_v1",
    "src.analysis.test_negotiation_persistence_v1",
    "src.analysis.test_bid_deduplication_v1",
    "src.analysis.test_source_accuracy_v1",
    "src.analysis.test_write_verification_v1",
    "src.analysis.test_protection_gate_v1",
    "src.analysis.test_reroll_memory_v1",
    "src.analysis.test_ledger_dedup_v1",
    "src.analysis.test_market_clock_v1",
    "src.analysis.test_position_guardrail_v1",
    "src.analysis.test_speculation_budget_v1",
    "src.analysis.test_bid_exposure_v1",
    "src.analysis.test_bid_targets_v1",
    "src.analysis.test_external_name_safety_v1",
    "src.analysis.test_portfolio_budget_v1",
    "src.analysis.test_roster_plan_guardrail_v1",
    "src.analysis.test_rival_bid_model_v1",
    "src.analysis.test_player_value_v1",
    "src.analysis.test_acquisition_wiring_v1",
    "src.analysis.test_bid_visibility_v1",
    "src.analysis.test_dashboard_truth_v1",
    "src.analysis.test_intocables_v1",
    "src.analysis.test_calendario_v1",
    "src.analysis.test_cobrar_ofertas_v1",
    "src.analysis.test_ciclo_una_sola_vez_v1",
    "src.analysis.test_escrituras_con_cuerpo_v1",
    "src.analysis.test_cambiar_titular_v1",
    "src.analysis.test_suelo_de_titulares_v1",
    "src.analysis.test_marcador_v1",
    "src.analysis.test_plantillas_rivales_v1",
    "src.analysis.test_abono_jornada_v1",
    "src.analysis.test_mercado_completo_v1",
    "src.analysis.test_pujar_por_el_xi_v1",
    "src.analysis.test_once_real_v1",
    "src.analysis.test_presupuesto_de_fichar_v1",
    "src.analysis.test_reventa_al_computer_v1",
    "src.analysis.test_once_de_verdad_v1",
    "src.analysis.test_correccion_jerarquia_v1",
    "src.analysis.test_contraoferta_v1",
    "src.analysis.test_escritura_contada_v1",
    "src.analysis.test_nombre_corto_v1",
    "src.analysis.test_action_starvation_v1",
    "src.analysis.test_price_history_store_v1",
    "src.analysis.test_futbolfantasy_source_v12",
    "src.analysis.test_starter_aware_xi_v1",
    "src.analysis.test_bid_outcome_ledger_v1",
    "src.analysis.test_etiqueta_vigilar_v1",
    "src.analysis.test_jornada_del_tablero_v1",
    "src.analysis.test_plantillas_rivales_llenas_v1",
    "src.analysis.test_penaltis_apagados_v1",
    "src.analysis.test_tope_por_operacion_v1",
    "src.analysis.test_jornada_en_la_valoracion_v1",
    "src.analysis.test_estado_de_carrera_v1",
    "src.analysis.test_valor_temporada_sombra_v1",
    "src.analysis.test_ampliar_plantilla_sombra_v1",
    "src.analysis.test_dashboard_orden_de_variables_v1",
    "src.analysis.test_pantalla_lee_lo_publicado_v1",
    "src.analysis.test_ojeador_fuentes_v1",
    "src.analysis.test_ojeador_emparejamiento_v1",
    "src.analysis.test_ojeador_informe_v1",
    "src.analysis.test_divergencia_v1",
    "src.analysis.test_puerta_una_sola_lista_v1",
    "src.analysis.test_freno_acelerador_v1",
    "src.analysis.test_freno_de_mano_v1",
]


WORKFLOW = None   # ya no se lee de ningun sitio: la lista es esta.


def modulos_del_workflow() -> list[str]:
    """
    Se conserva el nombre por compatibilidad con quien lo llame.

    Devuelve la lista de este fichero, que es la unica que hay.
    """

    return list(TESTS)


def main() -> int:

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--parar",
        action="store_true",
        help="detenerse en el primer fallo",
    )

    parser.add_argument(
        "--extra",
        nargs="*",
        default=[],
        help="guardias adicionales, sueltas, para probar a mano",
    )

    parser.add_argument(
        "--solo",
        nargs="*",
        default=None,
        help=(
            "correr SOLO estas guardias, en vez de la lista entera. "
            "Para probar una a mano sin esperar a las 68."
        ),
    )

    args = parser.parse_args()

    modulos = list(args.solo) if args.solo else list(TESTS)

    for extra in (args.extra or []):
        if extra not in modulos:
            modulos.append(extra)

    # Sin lista no se puede dar verde: seria decir "todo bien"
    # por no haber mirado nada, que es justo el fallo que este
    # cambio viene a cerrar.
    if not modulos:
        print("La lista de guardias esta vacia: eso no es un exito.")
        return 1

    print(f"Puerta de validacion: {len(modulos)} tests")
    print("=" * 66)

    fallos = []

    for indice, modulo in enumerate(modulos, start=1):

        proceso = subprocess.run(
            [sys.executable, "-m", modulo],
            capture_output=True,
            text=True,
        )

        corto = modulo.rsplit(".", 1)[-1]

        if proceso.returncode == 0:
            print(f"  {indice:>2}/{len(modulos)}  OK    {corto}")

        else:
            print(f"  {indice:>2}/{len(modulos)}  FALLA {corto}")

            salida = (
                (proceso.stderr or "")
                + (proceso.stdout or "")
            ).strip().splitlines()

            for linea in salida[-6:]:
                print(f"            {linea[:100]}")

            fallos.append(modulo)

            if args.parar:
                break

    print("=" * 66)

    if fallos:
        print(f"FALLAN {len(fallos)} de {len(modulos)}:")
        for modulo in fallos:
            print(f"  - {modulo}")
        print()
        print("NO subas hasta arreglarlos: CI parara el ciclo.")
        return 1

    print(f"Los {len(modulos)} en verde. Se puede subir.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
