"""
El propósito: qué freno cuelga de cada `intent`, y qué mide cada vía.

EL MAPA SALE DEL CODIGO, NO DE LA MEMORIA

    Los numeros de este modulo NO se escriben aqui: se importan
    de donde se aplican. Si alguien mueve el liston del 3 % en
    `rival_bid_model`, el mapa lo dice solo. Un mapa que hay que
    acordarse de actualizar es un mapa que miente a la tercera
    semana.

    Y hay guardia que EJERCITA el motor —no lee el mapa— para
    comprobar que lo que dice es lo que pasa.

DOCTRINA 69 — ANTES DE MOVER UN VALOR, LISTA QUE FRENOS CUELGAN

    Ya ha mordido tres veces: `intent` se llevaba el tope de puja
    al quitarse, `free_slots` abre `ROSTER_FILL` sin tope.

LO QUE EL ENCARGO DABA POR HECHO, Y NO ES ASI (17/09/2026)

    El encargo dice: "el `intent` se elige por que via da mas
    euros, y luego se aplican los listones de esa via".

    ESO DESCRIBE UN CAMINO QUE NO CORRE. Desde el 13/09
    `DEPLOYMENT_ENABLED` esta en 1 y la etiqueta la reparte
    `deployment.classify_operation`, que elige por CLASE DE
    OPERACION y no por euros. El `max(opciones, key=value)` de
    `acquisition_valuation` solo manda con el interruptor
    apagado.

    Y la separacion que el encargo pide YA EXISTE, con este
    nombre:

        el PROPOSITO   classify_operation  ->  SIGNING / TRADE
        la VALORACION  las cuatro vias     ->  cuanto vale
        el proposito manda bolsillo, liston y tope

    Medido: ha fichado DOS veces en once dias —Kiko Femenia el
    05/09 y Ruben Garcia el 12/09— y gano las dos. En las dos, el
    valor como fichaje SUPERABA al precio, que es justo la puerta.

ENTONCES ¿QUE PASA HOY? OTRA COSA, Y ES LA QUE IMPORTA

    De los 66 candidatos de la foto del 17/09, SEIS tienen valor
    positivo como fichaje. En CERO de los seis ese valor llega al
    precio. El mas cerca, Chupe: vale 2.895.184 y cuesta
    3.960.000.

    No se les aplica el liston equivocado. La via del once dice,
    correctamente, que no pagariamos ese precio por esos puntos.

LA ASIMETRIA QUE SI EXISTE, Y NO ES EL `intent`

    `xi_upgrade_value` mide el dinero COMO SI DESAPARECIERA.
    Devuelve el 80 % del que sale -`recovered_value`- pero no
    cuenta que el que ENTRA es tambien un activo que se puede
    revender.

    A Kiko Femenia por 1,15 M eso da igual. A Budimir por 11,99 M
    lo decide entero:

        valor como fichaje      3.427.226   (899.227 de puntos
                                             + 2.528.000 de Jutgla)
        valor como activo      12.200.424
        precio                 11.990.000

    Por la primera columna es un disparate; sumando la segunda,
    no. Y la via de reventa SI cuenta el activo, que es por lo que
    Pepe compra —26 subastas ganadas— pero nunca como fichaje.

    ESO es lo que se propone mirar, y se deja APAGADO, porque
    contar el activo entero abre una puerta muy ancha y el numero
    de cuanto se abre esta medido en el bloque 3.

FASE OBSERVADOR

    `ENCENDIDO = False`. Esto publica un mapa y calcula una
    sombra. No mueve ningun liston, ningun bolsillo y ningun tope.
"""

from __future__ import annotations

from src.analysis.acquisition_budget import (
    ACQUISITION_CASH_PERCENT,
)
from src.analysis.deployment import (
    DEPLOYMENT_ENABLED,
    INTENT_BY_CLASS,
    SIGNING,
    SIGNING_ROUTES,
    TRADE,
)
from src.analysis.player_value_engine import (
    DEFAULT_XI_MARGIN,
    HIERARCHY_VETO_STEPS,
    STARTER_SWAP_MARGIN,
    STARTER_SWAP_MIN_DELTA,
)
from src.analysis.rival_bid_model import (
    MIN_SPECULATION_EXPECTED_VALUE,
    MIN_WIN_PROBABILITY,
    PRIMA_MAXIMA_DE_PUJA,
    RENDIMIENTO_MINIMO_DEL_CAPITAL,
    SPECULATION_INTENT,
)


ENCENDIDO = False


# Las dos etiquetas que existen. Se importan de donde se
# reparten: `INTENT_BY_CLASS` es el unico sitio que las asigna
# con el interruptor puesto.
XI_UPGRADE = INTENT_BY_CLASS[SIGNING]

SPECULATION = INTENT_BY_CLASS[TRADE]

INTENTS = (XI_UPGRADE, SPECULATION)


# QUE HACE CADA FICHERO QUE NOMBRA EL `intent`.
#
#     ESTA LISTA NO ES EL MAPA: es la ANOTACION del mapa. El mapa
#     lo saca `lectores_del_intent()` recorriendo el arbol, y a
#     cada fichero que encuentra le pega la frase de aqui.
#
#     LA PRIMERA VERSION DE ESTE MODULO ESCRIBIO LA LISTA DE
#     MEMORIA Y SALIO MAL EN LAS DOS DIRECCIONES: cinco ficheros
#     que si lo nombran no estaban, y quince que no lo nombran
#     sobraban. El encargo pedia exactamente eso —"que salga del
#     codigo, no de la memoria"— y a la primera no lo cumpli.
#
#     Ahora, si un fichero nuevo empieza a nombrarlo y nadie
#     escribe aqui que decide, la verja se pone roja.
QUE_DECIDE_CADA_UNO = {
    "src/analysis/la_sombra_de_la_puja.py": (
        "NO DECIDE: copia el `intent` de cada puja de la sombra a "
        "la pantalla. Publica, no puja (23/09/2026)."
    ),
    "src/analysis/deployment.py": (
        "LO REPARTE: `classify_operation` por clase de operacion, "
        "y `signing_priority` por prioridad. Es el que manda con "
        "`DEPLOYMENT_ENABLED` encendido."
    ),
    "src/analysis/acquisition_valuation.py": (
        "LO REPARTE con el interruptor APAGADO: "
        "`max(opciones, key=value)`, por euros."
    ),
    "src/analysis/rival_bid_model.py": (
        "DECIDE: el tope de prima, el liston del 3 % y el minimo "
        "de 25.000 EUR cuelgan de que la etiqueta sea SPECULATION."
    ),
    "src/analysis/acquisition_budget.py": (
        "DECIDE: `budget_for_intent` elige el bolsillo."
    ),
    "src/analysis/acquisition_board.py": (
        "DECIDE: pasa el `intent` a `optimal_bid` y marca "
        "`budget_source` en pantalla."
    ),
    "src/analysis/hold_budget.py": (
        "DECIDE: de que bolsillo sale la via TENER."
    ),
    "src/analysis/roster_expansion_shadow.py": (
        "DECIDE: la segunda puerta de la lista de ampliar "
        "plantilla (INTENT_POR_EUROS)."
    ),
    "src/actions/autopilot_executor.py": (
        "DECIDE: que presupuesto lee el EJECUTOR antes de "
        "escribir la puja."
    ),
    "src/analysis/los_dos_techos.py": (
        "ENSEÑA: que columna se marca, QUEDARSE o REVENDER."
    ),
    "src/analysis/el_corte_de_la_reventa.py": (
        "DECIDE: con `BORDALAS_SIN_REVENTA` puesto, un candidato "
        "cuyo `intent` no sea de los de quedarse —y cuya `route` "
        "no sea de fichaje— no puja. No escribe ninguna etiqueta "
        "nueva: lee las que ya hay."
    ),
    "src/analysis/la_subasta.py": (
        "LO LLEVA desde la fila del tablero hasta la cesta, para "
        "que el corte de la reventa pueda mirarlo. La subasta no "
        "decide con el: su puja siempre es de modo cartera."
    ),
    "src/actions/carril_executor.py": (
        "LO LLEVA desde la fila del tablero hasta el corte de la "
        "reventa, y LO APUNTA como REVENDER en el libro de "
        "pujas: el carril compra para revender."
    ),
    "src/analysis/los_tres_denominadores.py": (
        "RECONSTRUYE: que liston se le aplica al recalcular."
    ),
    "src/analysis/player_value_engine.py": (
        "SE AUTODECLARA: cada via se pone su etiqueta."
    ),
    "src/analysis/hold_value.py": "SE AUTODECLARA como SPECULATION.",
    "src/analysis/speculation_engine.py": (
        "SE AUTODECLARA como SPECULATION."
    ),
    "src/analysis/speculative_exit.py": (
        "LO LEE para saber que posiciones son de especulacion al "
        "cerrarlas."
    ),
    "src/analysis/intelligent_bid_engine.py": (
        "LO PASA a `optimal_bid`; no decide con el."
    ),
    "src/analysis/decision_orchestrator.py": (
        "LO PASA a la decision; no decide con el."
    ),
    "src/analysis/season_horizon_shadow.py": "LO COPIA a la fila.",
    "src/analysis/la_plaza_y_el_cable.py": (
        "LO PUBLICA en el mapa del motivo entero."
    ),
    "src/intelligence/bid_outcome_ledger.py": (
        "LO APUNTA en el libro de pujas."
    ),
    "src/analysis/position_ledger_v105.py": (
        "LO APUNTA como `strategy` en el libro de posiciones."
    ),
    "src/analysis/doctrina.py": (
        "LO PUBLICA en la auditoria de doctrina."
    ),
    "src/autopilot.py": "LO IMPRIME en la tabla del ciclo.",
    "src/v10_full_autonomous_live.py": (
        "LO APUNTA al registrar una puja de la via vieja."
    ),
    "src/analysis/la_escala.py": (
        "LO TRADUCE: convierte la via o el motivo de una decision "
        "en el peldaño de la escala al que responde —`XI_UPGRADE` "
        "al 3, `SPECULATION` al 4—. No decide ninguna operacion "
        "ni toca ningun importe: solo pone nombre al orden."
    ),
    "src/analysis/el_proposito.py": "este mapa.",
}


# Donde se busca. Ni `data/` ni los tests: solo el codigo.
RAIZ_DEL_CODIGO = "src"

NOMBRES_QUE_CUENTAN = ("intent", "XI_UPGRADE", "SPECULATION")


def lectores_del_intent(raiz=None) -> dict:
    """
    Los ficheros que NOMBRAN el `intent`, sacados del arbol.

    Recorre el codigo -no `data/`- y devuelve cada fichero con lo
    que hace, si alguien lo ha anotado, o marcado `SIN ANOTAR` si
    no. Un `SIN ANOTAR` es lo que pone la verja en rojo.

    Nunca lanza: un fichero que no compila se salta y se cuenta
    aparte.
    """

    import ast
    import pathlib

    base = pathlib.Path(raiz or ".")

    encontrados = {}
    ilegibles = []

    for fichero in sorted(base.glob(f"{RAIZ_DEL_CODIGO}/**/*.py")):

        nombre = fichero.as_posix()

        # Las guardias no cuentan: no deciden nada en produccion.
        if "/test_" in nombre:
            continue

        try:
            arbol = ast.parse(
                fichero.read_text(encoding="utf-8", errors="replace")
            )

        except Exception:                           # noqa: BLE001
            ilegibles.append(nombre)
            continue

        usos = sum(
            1
            for nodo in ast.walk(arbol)
            if isinstance(nodo, ast.Constant)
            and nodo.value in NOMBRES_QUE_CUENTAN
        )

        if not usos:
            continue

        relativo = nombre[len(base.as_posix()) + 1:] if base.as_posix() != "." else nombre

        encontrados[relativo] = {
            "usos": usos,
            "que_hace": QUE_DECIDE_CADA_UNO.get(relativo, "SIN ANOTAR"),
        }

    return {
        "available": bool(encontrados),
        "n": len(encontrados),
        "ficheros": encontrados,
        "sin_anotar": sorted(
            f for f, d in encontrados.items()
            if d["que_hace"] == "SIN ANOTAR"
        ),
        "anotados_que_no_aparecen": sorted(
            set(QUE_DECIDE_CADA_UNO) - set(encontrados)
        ),
        "ilegibles": ilegibles,
    }


# LOS DOS SITIOS QUE LO DECIDEN. Ninguno mas.
DECIDEN = {
    "src/analysis/deployment.py": (
        "classify_operation: por CLASE de operacion. Es el que "
        "manda con `DEPLOYMENT_ENABLED` encendido, que es lo de "
        "hoy."
    ),
    "src/analysis/acquisition_valuation.py": (
        "max(opciones, key=value): por euros. Solo manda con el "
        "interruptor APAGADO."
    ),
}


def safe_int(value, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def esta_encendido() -> bool:
    return bool(ENCENDIDO)


# ============================================================
# BLOQUE 1 — EL MAPA
# ============================================================


def mapa_del_intent(raiz=None) -> dict:
    """
    Para cada `intent`: que liston, que bolsillo, que tope, que
    minimo, quien lo lee y quien lo decide.

    LOS NUMEROS NO SE ESCRIBEN: SE IMPORTAN. Si alguien mueve el
    3 %, esto lo dice solo.
    """

    return {
        "available": True,
        "observer_only": True,
        "deployment_enabled": bool(DEPLOYMENT_ENABLED),

        "intents": {
            XI_UPGRADE: {
                "intent": XI_UPGRADE,
                "operation_class": SIGNING,
                "routes": sorted(SIGNING_ROUTES),

                # NINGUNO PUEDE SALIR None. Si una via no tiene
                # freno, hay que decir cual y por que, no dejar el
                # hueco.
                "liston": {
                    "aplica": False,
                    "valor": None,
                    "que_es": (
                        "No hay liston de rendimiento sobre el "
                        "capital: un fichaje se paga en puntos, no "
                        "en euros de reventa."
                    ),
                    "en_su_lugar": (
                        f"el margen del {STARTER_SWAP_MARGIN * 100:.0f} % "
                        f"al tocar el once "
                        f"(o {DEFAULT_XI_MARGIN * 100:.0f} % si no), "
                        f"un minimo de {STARTER_SWAP_MIN_DELTA} puntos "
                        f"de mejora, el veto de "
                        f"{HIERARCHY_VETO_STEPS} escalones de "
                        f"jerarquia, y que el valor SUPERE al precio"
                    ),
                },

                "bolsillo": {
                    "nombre": "FICHAJES",
                    "de_donde": (
                        f"`acquisition_budget`: el "
                        f"{ACQUISITION_CASH_PERCENT * 100:.0f} % de "
                        f"la caja mas el margen de deuda segura"
                    ),
                },

                "tope_de_prima": {
                    "aplica": False,
                    "valor": None,
                    "que_es": (
                        "SIN TOPE DE PRIMA. `optimal_bid` solo lo "
                        "aplica a SPECULATION; con cualquier otra "
                        "etiqueta puja hasta el valor."
                    ),
                    "aviso": (
                        "Este es el freno que se cae al mover la "
                        "etiqueta. Doctrina 69."
                    ),
                },

                "minimo": {
                    "aplica": False,
                    "valor": None,
                    "que_es": (
                        "No hay minimo de GANANCIA ESPERADA en "
                        "euros: la mejora de un fichaje se mide en "
                        "puntos, no en margen de reventa."
                    ),

                    # LO CAZO LA GUARDIA, Y ES EL CASO EXACTO DE LA
                    # DOCTRINA 69: la primera version decia "no
                    # aplica" y se callaba que en su lugar hay
                    # OTRO minimo, en otra unidad. Un freno que no
                    # se nombra es un freno que desaparece el dia
                    # que alguien reordene la vía.
                    "en_su_lugar": (
                        f"un minimo de {STARTER_SWAP_MIN_DELTA} "
                        f"PUNTOS de mejora cuando sale un titular "
                        f"(`STARTER_SWAP_MIN_DELTA`), y que el "
                        f"valor como fichaje supere al precio "
                        f"(`classify_operation`)"
                    ),
                },

                "probabilidad_minima": MIN_WIN_PROBABILITY,
            },

            SPECULATION: {
                "intent": SPECULATION,
                "operation_class": TRADE,
                "routes": ["PRICE_TREND", "COMPUTER_RESALE", "HOLD"],

                "liston": {
                    "aplica": True,
                    "valor": RENDIMIENTO_MINIMO_DEL_CAPITAL,
                    "que_es": (
                        f"rendimiento minimo del "
                        f"{RENDIMIENTO_MINIMO_DEL_CAPITAL * 100:.0f} % "
                        f"sobre el capital inmovilizado "
                        f"(`rival_bid_model.optimal_bid`)"
                    ),
                },

                "bolsillo": {
                    "nombre": "ESPECULACION",
                    "de_donde": (
                        "`speculation_budget`: el limite de apostar, "
                        "mas estrecho que el de fichar"
                    ),
                },

                "tope_de_prima": {
                    "aplica": True,
                    "valor": PRIMA_MAXIMA_DE_PUJA,
                    "que_es": (
                        f"no se paga mas de un "
                        f"{PRIMA_MAXIMA_DE_PUJA * 100:.2f} % sobre el "
                        f"precio de mercado"
                    ),
                },

                "minimo": {
                    "aplica": True,
                    "valor": MIN_SPECULATION_EXPECTED_VALUE,
                    "que_es": (
                        f"{MIN_SPECULATION_EXPECTED_VALUE:,} EUR de "
                        f"ganancia esperada: el ciclo solo ejecuta "
                        f"una accion por vuelta"
                    ).replace(",", "."),
                },

                "probabilidad_minima": MIN_WIN_PROBABILITY,
            },
        },

        # EL MAPA SE ESCANEA, NO SE RECUERDA.
        "lectores": lectores_del_intent(raiz),
        "deciden": dict(sorted(DECIDEN.items())),

        "n_deciden": len(DECIDEN),

        "reason": (
            f"Dos `intent`. {len(DECIDEN)} sitios los deciden y "
            f"{lectores_del_intent(raiz)['n']} ficheros los nombran. Con "
            f"`DEPLOYMENT_ENABLED={bool(DEPLOYMENT_ENABLED)}` manda "
            + (
                "`classify_operation`, que elige por clase de "
                "operacion."
                if DEPLOYMENT_ENABLED
                else "el `max()` por euros de `acquisition_valuation`."
            )
        ),
    }


def frenos_de(intent) -> dict:
    """
    Los frenos de una etiqueta, o el aviso de que no la conocemos.

    NINGUNO DEVUELVE None SIN DECIR POR QUE. Un `None` mudo en un
    freno es como se pierde un tope sin que nadie lo note.
    """

    mapa = mapa_del_intent()["intents"]

    etiqueta = str(intent or "").upper()

    if etiqueta not in mapa:
        return {
            "available": False,
            "intent": intent,
            "reason": (
                f"`{intent}` no es una etiqueta conocida. Sin saber "
                f"que frenos cuelgan de ella no se puja: lo "
                f"prudente con una etiqueta desconocida es no "
                f"dejarla decidir nada."
            ),
        }

    return {"available": True, **mapa[etiqueta]}


# ============================================================
# BLOQUE 2 — LA SOMBRA: CONTAR EL ACTIVO QUE ENTRA
# ============================================================
#
#     La vía del once mide el dinero como si desapareciera. Aquí
#     se calcula al lado lo que valdría contando que el que entra
#     es también un activo, y NO SE APLICA.

def valor_de_fichar_con_el_activo(
    valor_como_fichaje,
    valor_como_activo,
) -> dict:
    """
    Lo que valdria un fichaje si se contara que el que entra se
    puede revender.

    NO ES UNA PROPUESTA DE ENCENDERLO. Es el numero que hace
    falta para discutirlo, y el bloque 3 mide lo que abre.

    Se suman los dos porque miden cosas distintas: uno es lo que
    aportan sus puntos por encima del que sale; el otro, lo que
    se recupera revendiendolo. Sumarlos NO es contar dos veces el
    mismo euro — pero sí es asumir que se puede tener las dos
    cosas, y eso solo es cierto si de verdad se revende.
    """

    puntos = safe_int(valor_como_fichaje)

    activo = safe_int(valor_como_activo)

    return {
        "valor_como_fichaje": puntos,
        "valor_como_activo": activo,
        "valor_con_el_activo": puntos + activo,
        "reason": (
            "Lo que aportan sus puntos por encima del que sale, "
            "mas lo que se recupera revendiendolo. Solo es cierto "
            "si de verdad se revende."
        ),
    }


def que_cambiaria(
    filas: list | None,
    *,
    bolsillo_de_fichar: int,
    bolsillo_de_especular: int,
    techo_de_biwenger: int,
) -> dict:
    """
    Cuantos candidatos pasarian de TRADE a SIGNING si el valor de
    fichar contase el activo, y CUANTO MAS SE PODRIA GASTAR.

    Cada fila necesita: `name`, `market_price`, `xi_value`
    -el valor como fichaje, de `xi_reason`- y `value` -lo que vale
    por la mejor via de mercado-.

    Nunca lanza. Con la lista vacia no publica un cero: dice que
    no hay candidatos.
    """

    try:
        candidatos = [
            f for f in (filas or []) if isinstance(f, dict)
        ]

        if not candidatos:
            return {
                "available": False,
                "n": 0,
                "pasan_ahora": 0,
                "pasarian": 0,
                "reason": (
                    "La lista de candidatos llega vacia: no hay "
                    "nada que comparar."
                ),
            }

        ahora = []
        despues = []

        for fila in candidatos:

            precio = safe_int(fila.get("market_price"))

            fichaje = safe_int(fila.get("xi_value"))

            # EL ACTIVO ES LO QUE VALE POR UNA VIA QUE NO SEA LA
            # DEL ONCE.
            #
            #     `deployment.value` es el MAXIMO de las cuatro
            #     vias. Cuando la que gana es la del once, ese
            #     maximo ES el valor como fichaje, y sumarlo seria
            #     contar el mismo euro dos veces.
            #
            #     Lo destapo correr esto contra la foto: Pepe y
            #     Chupe salian con `activo` identico a `fichaje`
            #     —3.195.607 y 2.895.184— y la suma los doblaba.
            #     Sin `value_route` no se puede saber, y entonces
            #     no se supone: el activo vale cero.
            via = str(fila.get("value_route") or "").upper()

            activo = (
                safe_int(fila.get("value"))
                if via and via not in SIGNING_ROUTES
                else 0
            )

            if precio <= 0:
                continue

            # La puerta de hoy: el valor como fichaje supera al
            # precio.
            if fichaje > precio:
                ahora.append(
                    {**fila, "valor": fichaje, "margen": fichaje - precio}
                )

            con_activo = valor_de_fichar_con_el_activo(
                fichaje, activo
            )["valor_con_el_activo"]

            # Y la sombra: solo cuenta si la via del once le dio
            # valor. Si `xi_value` es cero es que la via del once
            # dijo que no, y el activo no lo convierte en fichaje.
            if fichaje > 0 and con_activo > precio and fichaje <= precio:
                despues.append(
                    {
                        **fila,
                        "valor": con_activo,
                        "margen": con_activo - precio,
                    }
                )

        # CUANTO MAS SE PODRIA GASTAR. El tope de una operacion es
        # el menor de: lo que vale, el bolsillo y el techo de
        # Biwenger.
        def tope(item, bolsillo):
            return min(
                safe_int(item["valor"]),
                safe_int(bolsillo),
                safe_int(techo_de_biwenger),
            )

        peor_hoy = max(
            (tope(i, bolsillo_de_especular) for i in ahora),
            default=0,
        )

        peor_despues = max(
            (
                tope(i, bolsillo_de_fichar)
                for i in ahora + despues
            ),
            default=0,
        )

        return {
            "available": True,
            "n": len(candidatos),

            "pasan_ahora": len(ahora),
            "pasarian": len(despues),
            "los_que_pasarian": sorted(
                despues, key=lambda f: -f["margen"]
            ),
            "los_de_ahora": sorted(ahora, key=lambda f: -f["margen"]),

            # EL NUMERO QUE PIDE EL ENCARGO ANTES DE ENCENDER.
            "peor_caso_hoy": peor_hoy,
            "peor_caso_con_el_activo": peor_despues,
            "cuanto_mas": peor_despues - peor_hoy,

            "bolsillo_de_fichar": safe_int(bolsillo_de_fichar),
            "bolsillo_de_especular": safe_int(bolsillo_de_especular),
            "techo_de_biwenger": safe_int(techo_de_biwenger),

            "reason": (
                f"De {len(candidatos)} candidatos, {len(ahora)} "
                f"pasan hoy como fichaje y {len(despues)} mas "
                f"pasarian contando el activo. La operacion mas "
                f"grande de un dia pasaria de "
                f"{peor_hoy:,} a {peor_despues:,} EUR."
            ).replace(",", "."),
        }

    except Exception as error:                      # noqa: BLE001
        return {
            "available": False,
            "n": 0,
            "pasan_ahora": 0,
            "pasarian": 0,
            "reason": (
                f"No se pudo medir que cambiaria: "
                f"{type(error).__name__}: {error}"
            ),
        }
