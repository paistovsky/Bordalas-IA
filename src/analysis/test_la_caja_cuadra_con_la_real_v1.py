"""
La caja reconstruida de los ocho cuadra con la real.

POR QUE ESTA COMPROBACION ES LA UNICA QUE HAY

    La liga tiene `settings.balance = "hidden"`. De los siete
    rivales NO hay saldo contra el que contrastar: el unico
    numero comprobable del sistema es el nuestro.

    Si el metodo acierta con el nuestro, acierta con el suyo. Y
    si falla con el nuestro, la caja de los seis rivales tampoco
    vale — que es exactamente lo que dijo la pantalla el
    18/09/2026, con 420.200 EUR de separacion.

LO QUE SE COMPRUEBA, ENTONCES

    1. NUESTRA caja reconstruida cuadra con la oficial, al euro.
    2. Los otros siete salen con un numero, no con un None: una
       caja que no se puede calcular no se pinta como cero
       (doctrina 36).
    3. Cuando NO cuadra, se publica la diferencia Y el tipo de
       evento sospechoso, no solo el numero.
    4. El descuadre real del 18/09 se reproduce y se arregla: con
       la reja vieja salen los 420.200, con la nueva cuadra.

    El (4) es el que ata esta guardia al caso real. Sin el, las
    tres primeras se podrian cumplir con cualquier tablon
    inventado que casualmente cuadre.

LA GUARDIA MUERDE CON LA LISTA DE EVENTOS VACIA

    Sin eventos no hay caja, `available` sale a False y no hay
    nada que cuadrar: las cuatro comprobaciones pasarian por
    vacuidad. Por eso lo primero es comprobar que el banco trae
    eventos y que con la lista vacia no se reconstruye nada.

DE DONDE SALEN LOS NUMEROS

    Fijos, escritos aqui. No se lee `diagnostico/status.json` ni
    `data/`, no se sale a la red y no se mira el reloj.
"""

import os
import sys

sys.path.insert(0, ".")

from src.analysis.caja_de_la_liga import (  # noqa: E402
    SALDO_INICIAL,
    TOLERANCIA_ENV,
    cuadra,
    reconstruir,
)


fallos = []


def check(nombre, condicion, detalle=""):
    if condicion:
        print(f"  OK   {nombre}")
    else:
        print(f"  FALLA {nombre} {detalle}")
        fallos.append(nombre)


# ================================================================
# EL BANCO DE PRUEBAS: OCHO MANAGERS
# ================================================================

NOSOTROS = 14175949

RIVALES = [
    14145555,
    14156489,
    14154203,
    14152000,
    14153000,
    14157000,
    14158000,
]

LOS_OCHO = [NOSOTROS] + RIVALES

# 18/09/2026 07:03:10 UTC: la venta de Lunin, la de verdad.
VENTA_LUNIN = 1_789_707_790

# 17/09/2026 05:08 UTC: la compra de Lunin en el reset anterior.
COMPRA_LUNIN = 1_789_621_680


def venta(date, player, de, importe, event_id):

    return {
        "event_id": event_id,
        "date": date,
        "type": "transfer",
        "content": [
            {
                "player": player,
                "from": {"id": de, "name": "vendedor"},
                "amount": importe,
            }
        ],
    }


def compra(date, player, a, importe, event_id):

    return {
        "event_id": event_id,
        "date": date,
        "type": "market",
        "content": [
            {
                "player": player,
                "to": {"id": a, "name": "comprador"},
                "amount": importe,
            }
        ],
    }


# Nuestro trozo: compramos a Lunin por 421.000 y lo vendimos al
# dia siguiente por 420.200. -800 EUR, que es lo que paso.
TABLON = [
    compra(COMPRA_LUNIN, 15289, NOSOTROS, 421_000, "n1"),
    venta(VENTA_LUNIN, 15289, NOSOTROS, 420_200, "n2"),

    # Y algo de movimiento de rivales, para que los ocho tengan
    # libro y no solo nosotros.
    compra(COMPRA_LUNIN, 31069, RIVALES[0], 2_000_000, "r1"),
    venta(VENTA_LUNIN, 31069, RIVALES[0], 2_100_000, "r2"),
]

# La caja que sale de ahi: inicial - 421.000 + 420.200.
NUESTRA_CAJA = SALDO_INICIAL - 421_000 + 420_200

# El tablon como lo sirve produccion: con la venta reemitida
# 3m07s despues, que es lo que descuadro la caja el 18/09.
REEMITIDA = dict(
    venta(VENTA_LUNIN + 187, 15289, NOSOTROS, 420_200, "n2bis")
)

TABLON_SUCIO = TABLON + [REEMITIDA]


def con_tolerancia(valor: str):

    if valor:
        os.environ[TOLERANCIA_ENV] = valor
    else:
        os.environ.pop(TOLERANCIA_ENV, None)


def caja(eventos):
    return reconstruir(eventos, LOS_OCHO)


# ================================================================
# 0. EL BANCO DE PRUEBAS SIRVE
# ================================================================

print()
print("0. La lista de eventos no llega vacia")

check(
    "el tablon de la prueba trae eventos",
    len(TABLON) > 0,
    f"(eventos={len(TABLON)})",
)

check(
    "con la lista VACIA no se reconstruye nada",
    caja([])["available"] is False
    and caja(None)["available"] is False,
)

check(
    "y sin caja no hay managers que cuadrar",
    caja([])["managers"] == {},
    f"(managers={caja([])['managers']})",
)


# ================================================================
# 1. test_la_caja_cuadra_con_la_real
# ================================================================

print()
print("1. test_la_caja_cuadra_con_la_real")

con_tolerancia("1")

limpio = caja(TABLON)

check(
    "la reconstruccion esta disponible",
    limpio["available"] is True,
    f"(motivo={limpio.get('reason')})",
)

check(
    "los OCHO managers tienen caja",
    len(limpio["managers"]) == 8,
    f"(managers={len(limpio['managers'])})",
)

# Doctrina 36: un sin dato no es un cero. Ninguno puede salir a
# None, porque `maximum_bid` y `net_worth` cuelgan de aqui.
check(
    "y ninguno sale a None",
    all(
        m.get("cash") is not None
        for m in limpio["managers"].values()
    ),
)

nuestra = limpio["managers"][NOSOTROS]["cash"]

check(
    "nuestra caja reconstruida cuadra con la real, al euro",
    nuestra == NUESTRA_CAJA,
    f"(reconstruida={nuestra}, real={NUESTRA_CAJA})",
)

comprobacion = cuadra(
    nuestra,
    NUESTRA_CAJA,
    eventos=TABLON,
    manager=NOSOTROS,
)

check(
    "y la comprobacion lo dice: ok, diferencia 0",
    comprobacion["ok"] is True
    and comprobacion["difference"] == 0,
    f"(ok={comprobacion['ok']}, "
    f"dif={comprobacion['difference']})",
)

check(
    "cuadrando no se senala ningun sospechoso",
    comprobacion["suspects"] == []
    and comprobacion["suspect_types"] == [],
)


# ================================================================
# 2. Y SI NO CUADRA, DICE POR QUE
# ================================================================

print()
print("2. Si no cuadra: la diferencia Y el tipo sospechoso")

# La reja vieja sobre el tablon reemitido: el fallo del 18/09.
con_tolerancia("")

roto = caja(TABLON_SUCIO)["managers"][NOSOTROS]["cash"]

check(
    "con la reja vieja la venta reemitida se cuenta dos veces",
    roto == NUESTRA_CAJA + 420_200,
    f"(reconstruida={roto}, esperada={NUESTRA_CAJA + 420_200})",
)

descuadre = cuadra(
    roto,
    NUESTRA_CAJA,
    eventos=TABLON_SUCIO,
    manager=NOSOTROS,
)

check(
    "se publica la diferencia",
    descuadre["ok"] is False
    and descuadre["difference"] == 420_200,
    f"(dif={descuadre['difference']})",
)

check(
    "se publica el tipo de evento sospechoso",
    descuadre["suspect_types"] == ["transfer"],
    f"(tipos={descuadre['suspect_types']})",
)

check(
    "y el sospechoso es la venta concreta, con su jugador",
    any(
        s["player"] == 15289
        and s["amount"] == 420_200
        and s["ours"] is True
        for s in descuadre["suspects"]
    ),
    f"(sospechosos={[(s['player'], s['amount']) for s in descuadre['suspects']]})",
)

check(
    "el motivo lo dice con palabras, no solo el numero",
    "transfer" in (descuadre["reason"] or "")
    and "sobra un cobro" in (descuadre["reason"] or ""),
    f"(motivo={descuadre['reason']!r})",
)


# ================================================================
# 3. Y CON LA REJA NUEVA, VUELVE A CUADRAR
# ================================================================

print()
print("3. La reja nueva cierra el descuadre")

con_tolerancia("1")

arreglado = caja(TABLON_SUCIO)["managers"][NOSOTROS]["cash"]

check(
    "el mismo tablon reemitido vuelve a cuadrar al euro",
    arreglado == NUESTRA_CAJA,
    f"(reconstruida={arreglado}, real={NUESTRA_CAJA})",
)

check(
    "y la comprobacion se pone en verde",
    cuadra(
        arreglado,
        NUESTRA_CAJA,
        eventos=TABLON_SUCIO,
        manager=NOSOTROS,
    )["ok"]
    is True,
)

# El otro lado: la reja nueva no puede inventar dinero. La caja
# del rival, que no tiene reemisiones, no se mueve.
con_tolerancia("")
rival_viejo = caja(TABLON)["managers"][RIVALES[0]]["cash"]
con_tolerancia("1")
rival_nuevo = caja(TABLON)["managers"][RIVALES[0]]["cash"]

check(
    "a quien no tiene reemisiones no se le toca la caja",
    rival_viejo == rival_nuevo,
    f"(viejo={rival_viejo}, nuevo={rival_nuevo})",
)


con_tolerancia("")


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
