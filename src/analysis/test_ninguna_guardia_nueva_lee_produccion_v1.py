"""
Ninguna guardia NUEVA lee estado de produccion.

POR QUE ESTA GUARDIA, Y POR QUE SOLO PARA LAS NUEVAS

    La regla de la casa siempre lo dijo. SETENTA Y UNA guardias
    la rompen -el 19/09 se contaron 69 mirando solo
    `src/analysis`; el barrido completo de `src/**` da 71-: llaman a `get_latest_snapshot()` y su
    color depende de como este el mercado, no de como este el
    codigo.

    DOCTRINA 91. Un rojo que puede significar cualquier cosa vale
    lo mismo que un verde. Mientras esas esten en la cuenta, un
    rojo del repositorio no se puede leer: nadie distingue de un
    vistazo si es un fallo o es que hoy no hay ofertas.

    Convertir las 71 de golpe seria un commit que nadie puede
    revisar, asi que se separan en `regression_check` y se van
    convirtiendo. Pero la lista NO PUEDE CRECER mientras tanto, o
    el arreglo no termina nunca.

    Por eso esta guardia congela el censo: las que hay, las que
    hay; una mas, roja.

    Censo congelado: 71 guardias, en `src/analysis` (66),
    `src/intelligence` (4) y `src/actions` (1).

COMO SE DECIDE QUE ES «NUEVA»

    Con un censo escrito aqui abajo. Es la unica forma honesta:
    la fecha de un fichero no dice cuando se escribio -`git
    clone` las pone todas iguales- y mirar `git log` haria que
    esta guardia dependiera del historial, o sea del mundo, que
    es justo lo que viene a prohibir.

    Cuando una de las 71 se convierta, se quita del censo. El
    numero solo puede BAJAR.

QUE COMPRUEBA ESTA GUARDIA

    1. Ninguna guardia fuera del censo llama a
       `get_latest_snapshot`.
    2. El censo no crece: si aparece una nueva, sale con su
       nombre.
    3. Y no se queda viejo: si una del censo ya no lee
       produccion, hay que quitarla de la lista.

LA GUARDIA MUERDE SI NO ENCUENTRA GUARDIAS

    Sin ficheros que mirar pasaria por vacuidad. Por eso lo
    primero es exigir que el barrido encuentre guardias.

DE DONDE SALEN LOS NUMEROS

    Del arbol de ficheros, que es codigo, no estado de
    produccion. No se lee `data/`, no se sale a la red y no se
    mira el reloj.
"""

import sys
from pathlib import Path

sys.path.insert(0, ".")


RAIZ = Path(__file__).resolve().parents[2]

# La LLAMADA, con su parentesis. El nombre suelto lo mencionan
# las dos guardias que vigilan esto -esta y la de las
# escrituras-, y cazarlas a ellas seria cazar al vigilante.
LEE_PRODUCCION = "get_latest_snapshot("

# Las dos que hablan de la llamada para poder buscarla. Se
# excluyen por nombre y quedan escritas: una excepcion que no se
# ve es un agujero.
LAS_QUE_VIGILAN = {
    "test_ninguna_guardia_nueva_lee_produccion_v1",
    "test_ninguna_guardia_escribe_en_los_libros_v1",
}


# ============================================================
# EL CENSO, CONGELADO EL 19/09/2026
# ============================================================
#
#     Las que ya leian produccion ese dia. No se anaden nunca:
#     esta lista solo puede encoger.
CENSO = {
    "test_accept_before_expiry_execution_planner_v1",
    "test_accept_before_expiry_execution_planner_v2",
    "test_accept_before_expiry_live_revalidation_v1",
    "test_accept_offer_live_v1",
    "test_autopilot_v3_safety",
    "test_bid_engine",
    "test_bid_restructuring_engine",
    "test_bulk_player_mapper",
    "test_competitive_transactions_real",
    "test_competitive_transactions_real_v13",
    "test_competitive_transactions_real_v131",
    "test_competitive_transactions_real_v14",
    "test_computer_cycle_engine",
    "test_computer_offer_reroll_engine",
    "test_computer_reroll_live_chain",
    "test_computer_reroll_simulated_live_chain",
    "test_decision_orchestrator",
    "test_dynamic_deadline_engine",
    "test_external_speculation_intelligence",
    "test_external_status",
    "test_fixture_analyzer",
    "test_franchise_autopilot",
    "test_franchise_engine",
    "test_franchise_executor",
    "test_franchise_funding_engine",
    "test_intelligence_targets",
    "test_intelligent_bid_engine",
    "test_jornada_perfecta_live",
    "test_lineup_engine",
    "test_lineup_monitor",
    "test_lineup_v2",
    "test_liquidity_manager",
    "test_listing_lifecycle_orchestrator",
    "test_market_analyzer",
    "test_market_listing_lifecycle_engine",
    "test_market_trend_engine",
    "test_offer_analyzer",
    "test_offer_authority_separation_v1",
    "test_offer_decision_engine_v2",
    "test_offer_decision_orchestrator_v2",
    "test_offer_intelligence_observer",
    "test_player_availability",
    "test_player_context",
    "test_player_status",
    "test_portfolio_optimizer",
    "test_portfolio_roi_engine",
    "test_premium_opportunity_engine",
    "test_recommendations",
    "test_replacement_validation_v151",
    "test_reroll_live_safety",
    "test_restructuring_roster_impact_engine",
    "test_rival_intelligence_v1",
    "test_rival_intelligence_v2",
    "test_roster_planner",
    "test_sale_price_engine",
    "test_sales_analyzer",
    "test_solvency_engine",
    "test_solvency_guarantee_v21",
    "test_speculation_engine",
    "test_speculation_live_v1",
    "test_speculation_v3",
    "test_speculation_v4_jp",
    "test_sporting_opportunity_cost_v16",
    "test_strategic_budget_engine",
    "test_strategic_decision_gate",
    "test_strategic_plan_comparator",
    "test_strategic_target_engine",
    "test_strategy_planner",
    "test_team_analyzer",
    "test_transaction_planner",
    "test_write_client",
}


fallos = []


def check(nombre, condicion, detalle=""):
    if condicion:
        print(f"  OK   {nombre}")
    else:
        print(f"  FALLA {nombre} {detalle}")
        fallos.append(nombre)


# ================================================================
# 0. HAY GUARDIAS QUE MIRAR
# ================================================================

print()
print("0. El barrido encuentra guardias")

ESTA_GUARDIA = Path(__file__).stem

guardias = [
    f
    for f in sorted(RAIZ.rglob("src/**/test_*.py"))
    if "__pycache__" not in f.parts
    and f.stem not in LAS_QUE_VIGILAN
]

check(
    "hay guardias en el arbol",
    len(guardias) > 100,
    f"(n={len(guardias)})",
)

check(
    "y el censo no esta vacio",
    len(CENSO) > 0,
    f"({len(CENSO)})",
)


# ================================================================
# 1. NINGUNA FUERA DEL CENSO LEE PRODUCCION
# ================================================================

print()
print("1. Ninguna guardia nueva lee estado de produccion")

leen = set()

for fichero in guardias:

    try:
        fuente = fichero.read_text(
            encoding="utf-8", errors="replace"
        )

    except OSError:
        continue

    if LEE_PRODUCCION in fuente:
        leen.add(fichero.stem)

nuevas = sorted(leen - CENSO)

print(f"       leen produccion: {len(leen)}  ·  censo: {len(CENSO)}")

check(
    "ninguna nueva",
    not nuevas,
    f"<- {nuevas} llama(n) a `{LEE_PRODUCCION}()`. Una guardia "
    f"que lee produccion cambia de color con el mercado, no con "
    f"el codigo, y arrastra a las demas (doctrina 91). Si de "
    f"verdad hace falta mirar el mundo, va a `scripts/mirar_*.py`.",
)

check(
    "el censo no ha crecido",
    len(leen) <= len(CENSO),
    f"({len(leen)} contra {len(CENSO)})",
)


# ================================================================
# 2. Y EL CENSO NO SE QUEDA VIEJO
# ================================================================

print()
print("2. El censo solo puede encoger, y hay que mantenerlo")

convertidas = sorted(CENSO - leen)

if convertidas:
    print(f"       ya convertidas: {convertidas}")

check(
    "las que ya no leen produccion estan fuera del censo",
    not convertidas,
    f"<- {convertidas} ya no lee(n) produccion: quitarla(s) del "
    f"CENSO para que el numero baje de verdad.",
)


# ================================================================
# RESULTADO
# ================================================================

print()
print("=" * 60)

if fallos:
    print(f"FALLOS: {len(fallos)}")
    for nombre in fallos:
        print(f"  - {nombre}")
    sys.exit(1)

print("TODO OK")
print("=" * 60)
