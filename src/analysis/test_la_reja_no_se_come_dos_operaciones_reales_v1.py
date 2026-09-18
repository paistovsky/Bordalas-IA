"""
La reja colapsa reemisiones, y NO dos operaciones de verdad.

QUE SE ARREGLO Y QUE SE ARRIESGA

    La reja de `reconstruir` era

        (tipo, FECHA, jugador, de, a, importe)

    y la fecha estaba dentro. El 18/09/2026 nuestra venta de
    Lunin se conto dos veces -420.200 EUR- porque Biwenger
    reemite el mismo hecho minutos despues con otro `event_id` y
    otro `date`.

    Quitar la fecha a secas arregla eso y abre el fallo
    CONTRARIO, que es peor porque nadie lo estaria buscando: dos
    operaciones legitimas identicas -mismo jugador, mismo
    importe, mismas partes- se fundirian en una y la caja saldria
    de MAS.

    Por eso la fecha no se quita: se le pone tolerancia. Esta
    guardia vigila los DOS lados.

LO QUE SEPARA A LAS DOS POBLACIONES (medido el 18/09/2026)

    Sobre el tablon de 627 eventos, del 09/08 al 18/09, en 387
    grupos de (tipo, jugador, de, a, importe):

        reemisiones del tablon    n=5   tramo maximo    9m12s
        repeticiones legitimas    n=7   separacion min  5 dias

    Un factor de 783 entre las dos. La ventana de 3.600 s cae
    6,5 veces por encima de la mayor reemision y 120 por debajo
    de la repeticion legitima mas cercana.

    Y ni una sola repeticion con el MISMO importe separada por
    mas de una hora, en 40 dias.

POR QUE NO PUEDE HABER DOS IDENTICAS EN LA MISMA HORA

    No es solo estadistica, es como funciona la liga: el mercado
    RESUELVE UNA VEZ AL DIA. Los 42 eventos `market` de 39 dias
    caen todos en la hora 05:00, y ningun dia tiene dos horas de
    mercado.

    Asi que dos compras identicas del mismo jugador por el mismo
    manager no pueden estar a menos de ~24 h: veinticuatro veces
    la ventana. Y vender dos veces al mismo jugador exige
    recomprarlo por medio, que tambien pasa por un reset.

    Lo que SI puede pasar -y pasa, 7 veces en 40 dias- es que el
    mismo manager compre al mismo jugador dos veces en dias
    distintos. Se distinguen por dos cosas a la vez: los dias de
    separacion y el importe, que nunca coincidio porque el precio
    de Biwenger se mueve cada dia.

DE DONDE SALEN LOS NUMEROS

    Fijos, escritos aqui. No se lee `data/`, no se sale a la red
    y no se mira el reloj: las fechas son marcas escritas a mano.
"""

import os
import sys

sys.path.insert(0, ".")

from src.analysis.caja_de_la_liga import (  # noqa: E402
    SALDO_INICIAL,
    TOLERANCIA_ENV,
    VENTANA_REEMISION,
    reconstruir,
    ventana_activa,
)


fallos = []


def check(nombre, condicion, detalle=""):
    if condicion:
        print(f"  OK   {nombre}")
    else:
        print(f"  FALLA {nombre} {detalle}")
        fallos.append(nombre)


# ================================================================
# EL BANCO DE PRUEBAS
# ================================================================

VENDEDOR = 14156489
COMPRADOR = 14175949

# 04/09/2026 16:29:16 UTC, la hora del lote real.
T0 = 1_788_539_356

MINUTO = 60
HORA = 3_600
DIA = 86_400


def venta(date, player, de, importe, event_id):
    """Venta al Computer: `transfer` con `from` y sin `to`."""

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


def con_tolerancia(valor: str):
    """Enciende o apaga la reja nueva, sin depender del entorno."""

    if valor:
        os.environ[TOLERANCIA_ENV] = valor
    else:
        os.environ.pop(TOLERANCIA_ENV, None)


def caja_de(eventos, quien=VENDEDOR):

    salida = reconstruir(eventos, [VENDEDOR, COMPRADOR])

    return salida, salida["managers"][quien]


# ================================================================
# 0. EL BANCO DE PRUEBAS SIRVE
# ================================================================

print()
print("0. La lista de eventos no llega vacia")

con_tolerancia("1")

check(
    "con la lista VACIA no hay caja que reconstruir",
    reconstruir([], [VENDEDOR])["available"] is False
    and reconstruir(None, [VENDEDOR])["available"] is False,
)

check(
    "y se dice por que, en vez de devolver ceros",
    "vacio" in (reconstruir([], [VENDEDOR])["reason"] or ""),
    f"(motivo={reconstruir([], [VENDEDOR])['reason']!r})",
)

# La reja de esta guardia: todo lo de abajo cuenta ventas. Si la
# lista llegara vacia no habria ni una y todo pasaria por
# vacuidad.
_, base = caja_de([venta(T0, 31069, VENDEDOR, 2_464_100, "z1")])

check(
    "el banco registra ventas de verdad",
    base["sales_count"] == 1 and base["sales"] == 2_464_100,
    f"(ventas={base['sales_count']}, importe={base['sales']})",
)


# ================================================================
# 1. LA REEMISION SE COLAPSA
# ================================================================

print()
print("1. test_la_reja_no_se_come_dos_operaciones_reales")
print("   (a) la reemision del tablon SI se colapsa")

con_tolerancia("1")

# El lote real del 04/09: 1 operacion a las 16:29, la misma mas
# otra a las 16:34, y las dos mas cinco a las 16:38.
lote = [
    venta(T0, 31069, VENDEDOR, 2_464_100, "a1"),
    venta(T0 + 4 * MINUTO + 45, 31069, VENDEDOR, 2_464_100, "a2"),
    venta(T0 + 9 * MINUTO + 12, 31069, VENDEDOR, 2_464_100, "a3"),
]

salida, libro = caja_de(lote)

check(
    "tres copias en 9m12s cuentan como UNA venta",
    libro["sales_count"] == 1
    and libro["sales"] == 2_464_100,
    f"(ventas={libro['sales_count']}, importe={libro['sales']})",
)

check(
    "y las dos descartadas se cuentan como repetidas",
    salida["repeats_skipped"] == 2,
    f"(repetidos={salida['repeats_skipped']})",
)

# Se ancla en la PRIMERA, no se reancla: si se reanclara en cada
# copia, una cadena podria arrastrar la ventana mas alla de una
# hora y tragarse algo real.
cadena = [
    venta(T0, 31069, VENDEDOR, 2_464_100, "b1"),
    venta(T0 + 50 * MINUTO, 31069, VENDEDOR, 2_464_100, "b2"),
    venta(T0 + 100 * MINUTO, 31069, VENDEDOR, 2_464_100, "b3"),
]

_, encadenado = caja_de(cadena)

check(
    "la ventana se ancla en la primera y no se arrastra",
    encadenado["sales_count"] == 2,
    f"(ventas={encadenado['sales_count']}, esperadas 2: "
    f"la de +50m se colapsa, la de +100m ya no)",
)


# ================================================================
# 2. DOS OPERACIONES REALES SIGUEN SIENDO DOS
# ================================================================

print("   (b) dos operaciones legitimas NO se funden")

# El caso que pide el encargo: MISMO dia, mismo jugador, mismo
# importe, mismas partes.
mismo_dia = [
    venta(T0, 31069, VENDEDOR, 2_464_100, "c1"),
    venta(T0 + 6 * HORA, 31069, VENDEDOR, 2_464_100, "c2"),
]

salida, dos = caja_de(mismo_dia)

check(
    "dos ventas identicas el MISMO dia, a 6 h, siguen siendo dos",
    dos["sales_count"] == 2
    and dos["sales"] == 2 * 2_464_100,
    f"(ventas={dos['sales_count']}, importe={dos['sales']})",
)

check(
    "y no se cuenta ninguna como repetida",
    salida["repeats_skipped"] == 0,
    f"(repetidos={salida['repeats_skipped']})",
)

# El caso medido: 5 dias, que es la separacion legitima mas corta
# que hubo en 40 dias.
_, lejanas = caja_de([
    venta(T0, 31069, VENDEDOR, 2_464_100, "d1"),
    venta(T0 + 5 * DIA, 31069, VENDEDOR, 2_464_100, "d2"),
])

check(
    "a 5 dias -la separacion legitima mas corta medida- son dos",
    lejanas["sales_count"] == 2,
    f"(ventas={lejanas['sales_count']})",
)

# Dos compras del mismo jugador en el reset de dos dias
# seguidos, que es lo que de verdad pasa 7 veces en 40 dias.
compra = lambda date, imp, eid: {                # noqa: E731
    "event_id": eid,
    "date": date,
    "type": "market",
    "content": [
        {
            "player": 1599,
            "to": {"id": COMPRADOR, "name": "comprador"},
            "amount": imp,
        }
    ],
}

_, comprador = caja_de(
    [
        compra(T0, 1_570_000, "e1"),
        compra(T0 + DIA, 1_925_100, "e2"),
    ],
    quien=COMPRADOR,
)

check(
    "dos compras del mismo jugador en dos resets son dos compras",
    comprador["purchases_count"] == 2
    and comprador["purchases"] == 1_570_000 + 1_925_100,
    f"(compras={comprador['purchases_count']}, "
    f"importe={comprador['purchases']})",
)


# ================================================================
# 3. LA VENTANA CAE ENTRE LAS DOS POBLACIONES
# ================================================================

print("   (c) la ventana esta donde la puso la medicion")

# Si alguien la mueve, esto lo canta antes de que lo cante la
# caja. 9m12s es la mayor reemision medida; 5 dias, la
# repeticion legitima mas cercana.
check(
    "la ventana deja fuera la mayor reemision medida (9m12s)",
    VENTANA_REEMISION > 9 * MINUTO + 12,
    f"(ventana={VENTANA_REEMISION}s)",
)

check(
    "y no alcanza la repeticion legitima mas cercana (5 dias)",
    VENTANA_REEMISION < 5 * DIA,
    f"(ventana={VENTANA_REEMISION}s)",
)

check(
    "ni siquiera alcanza un dia: el mercado resuelve una vez",
    VENTANA_REEMISION < DIA,
    f"(ventana={VENTANA_REEMISION}s)",
)


# ================================================================
# 4. EL INTERRUPTOR
# ================================================================

print("   (d) el interruptor manda, y apagado no toca nada")

con_tolerancia("")

check(
    "apagado, la ventana es 0: la reja de siempre",
    ventana_activa() == 0,
    f"(ventana={ventana_activa()})",
)

_, apagado = caja_de(lote)

check(
    "apagado, las tres copias del lote vuelven a contar tres",
    apagado["sales_count"] == 3,
    f"(ventas={apagado['sales_count']})",
)

con_tolerancia("1")

check(
    "encendido, la ventana es la medida",
    ventana_activa() == VENTANA_REEMISION,
    f"(ventana={ventana_activa()})",
)

# Encendido o apagado, dos operaciones reales son dos. El
# interruptor solo puede quitar sobrecuenta, nunca crearla.
con_tolerancia("")
_, dos_apagado = caja_de(mismo_dia)
con_tolerancia("1")

check(
    "las dos legitimas son dos con el interruptor en cualquier lado",
    dos_apagado["sales_count"] == 2 and dos["sales_count"] == 2,
    f"(apagado={dos_apagado['sales_count']}, "
    f"encendido={dos['sales_count']})",
)


# ================================================================
# 5. LA CAJA NO SE INVENTA
# ================================================================

print("   (e) y la cuenta sigue siendo la de siempre")

con_tolerancia("1")

_, cuenta = caja_de(mismo_dia)

check(
    "caja = inicial + ventas, sin nada mas por medio",
    cuenta["cash"] == SALDO_INICIAL + 2 * 2_464_100,
    f"(caja={cuenta['cash']})",
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
