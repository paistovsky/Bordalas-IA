"""
Un jugador que suma puntos y conserva su valor se ficha, aunque su
precio sea mayor que los puntos que añade.

EL CASO (26/09/2026)

    Hinojo: "vale 883.575 y cuesta 1.690.000. No hay margen." Y
    sumaba +0,73 puntos por jornada. El valor solo contaba los puntos
    y se comparaba con el precio ENTERO, como si pagar fuera perder.

QUE COMPRUEBA

    0. El caso muerde: con la cuenta vieja (precio entero) el jugador
       NO pasa. Si pasara, "con la nueva pasa" no distinguiria nada.
    1. Con la cuenta nueva SI pasa, y el coste es lo que se deprecia,
       no el precio.
    2. El mismo jugador, con el precio cayendo, no pasa: la cuenta no
       aprueba a todo el mundo.
    3. La subida nunca se cuenta: SUBE deprecia 0, no revaloriza.
    4. Ganancia y coste con el mismo horizonte: doblarlo dobla los dos.
    5. El coste de oportunidad es 0 por defecto y, si se pasa, suma.
    6. El comparador de la puja (`optimal_bid`) dice NO_COMPENSA con
       la vieja y no con la nueva: la cuenta llega a la decision.
    7. Apagado, `xi_upgrade_value` da exactamente lo de siempre.
    8. El interruptor se lee al llamar y nace apagado. Nada lanza.

DE DONDE SALEN LOS NUMEROS

    Fijos, escritos aqui. Ni `data/`, ni red, ni reloj. El interruptor
    se pasa por parametro; donde se lee del entorno, lo pone y lo
    quita esta misma guardia.
"""

import os
import sys

sys.path.insert(0, ".")

from src.analysis import el_precio_no_se_pierde as epn  # noqa: E402
from src.analysis.player_value_engine import xi_upgrade_value  # noqa: E402
from src.analysis.rival_bid_model import optimal_bid  # noqa: E402


fallos = []


def check(nombre, condicion, detalle=""):
    if condicion:
        print(f"  OK   {nombre}")
    else:
        print(f"  FALLA {nombre} {detalle}")
        fallos.append(nombre)


# ================================================================
# EL CASO: un Hinojo
# ================================================================
#
#     1.690.000 de precio. Suma 28 puntos de temporada sobre el que
#     sale (~0,74 por jornada). Tarifa 30.000. Y CONSERVA SU VALOR:
#     el precio viene subiendo (+0,5 %/dia, tramo SUBE), asi que la
#     cuenta conservadora no le espera depreciacion.
#
#     OJO, Y ES UN RESULTADO: el mismo jugador con el precio PLANO no
#     pasa. Se le espera un 7,34 % de depreciacion en 14 dias (el
#     tercil bajo medido) y 0,74 puntos por jornada no lo pagan. La
#     seccion 2 lo deja escrito.

PRECIO = 1_690_000
DELTA = 28
MERCADO = {"rate_median": 30_000}
ENTRA = {"probability": 90.0, "hierarchy_value": 50, "hierarchy_label": "Clave"}
SALE = {"probability": 70.0, "hierarchy_value": 50, "hierarchy_label": "Clave"}


CONSERVA = 0.5    # %/dia: tramo SUBE


def valor(cuenta_nueva, tasa=CONSERVA):
    return xi_upgrade_value(
        candidate_points=100 + DELTA,
        replaced_points=100,
        points_market=MERCADO,
        confidence=1.0,
        recovered_value=0,
        candidate_starter=ENTRA,
        replaced_starter=SALE,
        replaced_in_lineup=False,
        candidate_price=PRECIO,
        price_rate=tasa,
        precio_no_se_pierde=cuenta_nueva,
    )


vieja = valor(False)
nueva = valor(True)

print()
print("0. El caso muerde: con el precio entero no pasa")

check(
    "la cuenta vieja da un valor POR DEBAJO del precio",
    0 < vieja["value"] < PRECIO,
    f"(valor {vieja['value']:,} precio {PRECIO:,})",
)
check(
    "y lo que ganan sus puntos en el horizonte es menor que el precio",
    (nueva.get("el_precio_no_se_pierde") or {}).get("ganancia", 0) < PRECIO,
    f"({nueva.get('el_precio_no_se_pierde')})",
)

print()
print("1. Con el precio que no se pierde, pasa")

cuenta = nueva.get("el_precio_no_se_pierde") or {}

check(
    "la cuenta nueva da un valor POR ENCIMA del precio",
    nueva["value"] > PRECIO,
    f"(valor {nueva['value']:,} precio {PRECIO:,}, {cuenta.get('cuenta')})",
)
check(
    "el coste no es el precio: lo que se deprecia mas la oportunidad",
    cuenta.get("coste") is not None
    and cuenta.get("coste") == (cuenta.get("depreciacion") or 0) + (cuenta.get("oportunidad") or 0)
    and cuenta.get("coste") < PRECIO / 5,
    f"(coste {cuenta.get('coste')})",
)
check(
    "valor = precio - coste + ganancia",
    bool(cuenta)
    and nueva["value"] == PRECIO - (cuenta.get("coste") or 0) + (cuenta.get("ganancia") or 0),
    f"({nueva['value']} vs {PRECIO} - {cuenta.get('coste')} + {cuenta.get('ganancia')})",
)
check(
    "y dice que compensa",
    cuenta.get("compensa") is True and cuenta.get("tramo") == "SUBE",
    f"({cuenta})",
)

print()
print("2. Con el precio cayendo, o plano, el mismo jugador no pasa")

plano = valor(True, tasa=0.0)
check(
    "tramo PLANO: 0,74 pts/jornada no pagan un 7,34 % en 14 dias",
    plano["value"] < PRECIO
    and (plano.get("el_precio_no_se_pierde") or {}).get("tramo") == "PLANO",
    f"(valor {plano['value']:,}, {plano.get('el_precio_no_se_pierde')})",
)

cae = valor(True, tasa=-1.2)
check(
    "tramo BAJA: la depreciacion se come la ganancia",
    cae["value"] < PRECIO
    and (cae.get("el_precio_no_se_pierde") or {}).get("tramo") == "BAJA",
    f"(valor {cae['value']:,}, {cae.get('el_precio_no_se_pierde')})",
)

print()
print("3. La subida no se cuenta")

sube = epn.valor_para_jugar(PRECIO, DELTA, 30_000, 0.10, 1.0, tasa_por_dia=2.0)
check(
    "SUBE deprecia 0 y el valor no pasa de precio + ganancia",
    sube["depreciacion"] == 0 and sube["valor"] == PRECIO + sube["ganancia"],
    f"({sube})",
)

print()
print("4. El mismo horizonte a los dos lados")

h14 = epn.valor_para_jugar(PRECIO, DELTA, 30_000, 0.10, 1.0, tasa_por_dia=0.0, horizonte_dias=14)
h28 = epn.valor_para_jugar(PRECIO, DELTA, 30_000, 0.10, 1.0, tasa_por_dia=0.0, horizonte_dias=28)
check(
    "doblar el horizonte dobla la ganancia y el coste",
    abs(h28["ganancia"] - 2 * h14["ganancia"]) <= 1
    and abs(h28["depreciacion"] - 2 * h14["depreciacion"]) <= 1,
    f"({h14['ganancia']},{h28['ganancia']} / {h14['depreciacion']},{h28['depreciacion']})",
)

print()
print("5. El coste de oportunidad")

check("es 0 por defecto", h14["oportunidad"] == 0, f"({h14['oportunidad']})")
con_cola = epn.valor_para_jugar(
    PRECIO, DELTA, 30_000, 0.10, 1.0, tasa_por_dia=0.0, oportunidad_diaria=0.001
)
check(
    "con una tasa, suma al coste",
    con_cola["oportunidad"] > 0 and con_cola["coste"] > h14["coste"],
    f"({con_cola})",
)

print()
print("6. La cuenta llega al comparador de la puja")

no_compensa = optimal_bid(price=PRECIO, value=vieja["value"], model={}, intent="XI_UPGRADE")
si_compensa = optimal_bid(price=PRECIO, value=nueva["value"], model={}, intent="XI_UPGRADE")
check(
    "con la vieja: NO_COMPENSA",
    no_compensa.get("decision") == "NO_COMPENSA",
    f"({no_compensa.get('decision')})",
)
check(
    "con la nueva: ya no es NO_COMPENSA",
    si_compensa.get("decision") != "NO_COMPENSA",
    f"({si_compensa.get('decision')}: {si_compensa.get('reason')})",
)

print()
print("7. Apagado, lo de siempre")

sin_precio = xi_upgrade_value(
    candidate_points=100 + DELTA, replaced_points=100, points_market=MERCADO,
    confidence=1.0, candidate_starter=ENTRA, replaced_starter=SALE,
    precio_no_se_pierde=True,
)
check(
    "apagado y 'encendido sin precio' dan el mismo valor",
    vieja["value"] == sin_precio["value"]
    and vieja.get("el_precio_no_se_pierde") is None,
    f"({vieja['value']} vs {sin_precio['value']})",
)
check(
    "y es la cuenta vieja: puntos x tarifa x (1 - margen)",
    vieja["value"] == int(DELTA * 30_000 * 0.90),
    f"({vieja['value']})",
)

print()
print("8. El interruptor, y la basura")

antes = os.environ.pop(epn.EL_PRECIO_NO_SE_PIERDE_ENV, None)
try:
    check("sin el en el entorno, apagado", epn.encendido() is False)
    os.environ[epn.EL_PRECIO_NO_SE_PIERDE_ENV] = "1"
    check("puesto a 1, encendido, sin reimportar", epn.encendido() is True)
finally:
    os.environ.pop(epn.EL_PRECIO_NO_SE_PIERDE_ENV, None)
    if antes is not None:
        os.environ[epn.EL_PRECIO_NO_SE_PIERDE_ENV] = antes

try:
    basura = [
        epn.valor_para_jugar(None, None, None, None, None),
        epn.valor_para_jugar("x", "y", "z", "m", "c", tasa_por_dia="t"),
        epn.coste_real(None, None),
        epn.tramo("nada"),
    ]
    check("nunca lanza", True, f"({basura})")
except Exception as error:                          # noqa: BLE001
    check("nunca lanza", False, f"({type(error).__name__}: {error})")


print()
print("=" * 60)

if fallos:
    print(f"FALLOS: {len(fallos)}")
    for nombre in fallos:
        print(f"  - {nombre}")
    sys.exit(1)

print("TODO OK")
print("=" * 60)
