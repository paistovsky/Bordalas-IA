"""
El suelo del que no tiene pronostico no se escribe: se deriva.

DOCTRINA 85, QUE NOS COSTO UN PORTERO

    Un suelo calibrado contra otra cosa se queda flotando cuando
    esa cosa cambia.

    El suelo del que no tiene pronostico valia 0,25 "en la misma
    escala". La escala era `HIERARCHY_MATCH_QUALITY`, cuyo
    peldano mas bajo es 0,25 -"Descarte"-, asi que el suelo era
    de verdad el ultimo puesto y el comentario que lo explicaba
    era correcto.

    Nadie escribio que el uno dependia del otro. Eran dos numeros
    iguales, escritos a mano, en dos sitios.

    Cuando `calidad_para_la_vara` cambio la etiqueta por puntos
    por partido reales, la escalera dejo de ser el suelo de nada:
    Dituro, Importante, cayo a 0,227 de vara. El suelo se quedo
    en 0,25 y a partir de ese momento NO SABER GANABA A SABER.

    El 18/09/2026 eso puso al tercer portero del Atletico -0
    partidos, 0 puntos, cero fuentes- por delante de un portero
    con 123 puntos la temporada pasada.

QUE SE COMPRUEBA AQUI

    1. El suelo esta DERIVADO, no escrito: si se mueven los pesos
       de los que sale, el suelo se mueve con ellos.
    2. Y si NO se mueve -porque alguien lo volvio a escribir a
       mano- esta guardia falla. Es su razon de ser.
    3. La banda se respeta con la escalera ENTERA: para todos los
       peldanos y todas las probabilidades, quien tiene
       pronostico puntua por encima del suelo.
    4. Las dos escaleras tienen los mismos peldanos, y el escalon
       de "no se sabe" existe en las dos.

LA GUARDIA MUERDE SI LOS DOS VALORES SE ESCRIBEN POR SEPARADO

    Es literalmente lo que se le pide. La comprobacion 2 mueve
    los pesos y exige que el suelo se entere. Un `return
    -498_750.0` la pone en rojo, que es lo que habria pasado el
    dia que se toco la escalera.

DE DONDE SALEN LOS NUMEROS

    De los propios modulos, leidos en caliente. No se lee estado
    de produccion, no se sale a la red y no se mira el reloj.
"""

import sys

sys.path.insert(0, ".")

import src.analysis.lineup_engine as motor  # noqa: E402

from src.analysis.lineup_engine import (  # noqa: E402
    HIERARCHY_BENCH_APPEARANCE,
    HIERARCHY_MATCH_QUALITY,
    HIERARCHY_UNKNOWN_VALUE,
    NO_ALINEABLE,
    peor_con_pronostico,
    suelo_sin_pronostico,
    weekly_expected_value,
)


fallos = []


def check(nombre, condicion, detalle=""):
    if condicion:
        print(f"  OK   {nombre}")
    else:
        print(f"  FALLA {nombre} {detalle}")
        fallos.append(nombre)


# ================================================================
# 0. EL BANCO DE PRUEBAS SIRVE
# ================================================================
#
# Si las escaleras llegaran vacias, los barridos de abajo no
# recorrerian nada y todo pasaria por vacuidad.

print()
print("0. Las escaleras traen peldanos")

check(
    "la escalera de calidad no esta vacia",
    len(HIERARCHY_MATCH_QUALITY) > 0,
    f"(peldanos={len(HIERARCHY_MATCH_QUALITY)})",
)

check(
    "la escalera de banquillo no esta vacia",
    len(HIERARCHY_BENCH_APPEARANCE) > 0,
    f"(peldanos={len(HIERARCHY_BENCH_APPEARANCE)})",
)

check(
    "las dos tienen los MISMOS peldanos",
    set(HIERARCHY_MATCH_QUALITY) == set(HIERARCHY_BENCH_APPEARANCE),
    f"(calidad={sorted(HIERARCHY_MATCH_QUALITY)}, "
    f"banquillo={sorted(HIERARCHY_BENCH_APPEARANCE)})",
)

# `weekly_expected_value` cae a este escalon cuando no conoce el
# que le pasan, y luego indexa LAS DOS escaleras con el. Si
# desapareciera de una, reventaria con KeyError en produccion.
check(
    "el escalon de 'no se sabe' existe en las dos escaleras",
    HIERARCHY_UNKNOWN_VALUE in HIERARCHY_MATCH_QUALITY
    and HIERARCHY_UNKNOWN_VALUE in HIERARCHY_BENCH_APPEARANCE,
    f"(escalon={HIERARCHY_UNKNOWN_VALUE})",
)


# ================================================================
# 1. test_el_suelo_sigue_a_su_escalera
# ================================================================

print()
print("1. test_el_suelo_sigue_a_su_escalera")
print("   (a) el suelo esta en su banda")

suelo = suelo_sin_pronostico()

peor = peor_con_pronostico()

check(
    "el suelo queda por DEBAJO del peor con pronostico",
    suelo < peor,
    f"(suelo={suelo}, peor con dato={peor})",
)

check(
    "y por ENCIMA del que no se puede alinear",
    suelo > NO_ALINEABLE,
    f"(suelo={suelo}, no alineable={NO_ALINEABLE})",
)

# El punto medio: el sitio con mas margen por los dos lados. Si
# alguien lo descentra, el margen se parte y esto lo canta.
check(
    "esta centrado en la banda, que es donde mas margen deja",
    abs((peor - suelo) - (suelo - NO_ALINEABLE)) < 1.0,
    f"(margen arriba={peor - suelo}, "
    f"margen abajo={suelo - NO_ALINEABLE})",
)


# ================================================================
# 2. Y SE MUEVE CON LOS PESOS DE LOS QUE SALE
# ================================================================

print("   (b) si se mueven los pesos, el suelo se entera")

# ESTA ES LA COMPROBACION QUE PIDE EL ENCARGO.
#
#     Se toca cada peso del que depende el suelo y se exige que
#     el suelo cambie. Si alguien sustituye la derivacion por un
#     numero escrito -que es lo que nos mordio- el suelo se queda
#     quieto y esto se pone en rojo.

originales = {
    "COBERTURA_POR_FUENTE": motor.COBERTURA_POR_FUENTE,
    "AVISO_NO_AUTOMATICO": motor.AVISO_NO_AUTOMATICO,
    "NO_ALINEABLE": motor.NO_ALINEABLE,
}


def con_peso(nombre, valor):
    """Cambia un peso, mide el suelo y lo deja como estaba."""

    setattr(motor, nombre, valor)

    try:
        return motor.suelo_sin_pronostico()

    finally:
        setattr(motor, nombre, originales[nombre])


for nombre, original in originales.items():

    movido = con_peso(nombre, original * 2 - 1_000.0)

    check(
        f"el suelo se mueve al tocar {nombre}",
        movido != suelo,
        f"(suelo={suelo}, con el peso movido={movido}; "
        f"si no se mueve, esta escrito a mano)",
    )

check(
    "y los pesos quedan como estaban",
    all(
        getattr(motor, nombre) == valor
        for nombre, valor in originales.items()
    ),
)


# ================================================================
# 3. LA ESCALERA ENTERA RESPETA LA BANDA
# ================================================================

print("   (c) ningun peldano de la escalera baja del suelo")

# El barrido: todos los peldanos, todas las probabilidades. Es la
# forma de que la escalera y el suelo no puedan separarse sin que
# alguien se entere, sin volver a atarlos con una constante.
peor_visto = None

peor_caso = None

for escalon in sorted(HIERARCHY_MATCH_QUALITY):

    for probabilidad in range(0, 101, 5):

        vara = weekly_expected_value(
            escalon,
            float(probabilidad),
        )

        # El peor score posible con ese pronostico: cobertura 1,
        # y la base mas baja que puede tener alguien alineable.
        score = (
            vara * motor.ESCALA_DE_LA_VARA
            + 1.0 * motor.COBERTURA_POR_FUENTE
            + probabilidad * motor.PESO_DE_LA_PROBABILIDAD
            + motor.AVISO_NO_AUTOMATICO
        )

        if peor_visto is None or score < peor_visto:
            peor_visto = score
            peor_caso = (escalon, probabilidad, round(vara, 4))

check(
    "se ha barrido la escalera de verdad",
    peor_visto is not None
    and len(HIERARCHY_MATCH_QUALITY) * 21 >= 21,
    f"(peor caso={peor_caso})",
)

check(
    "hasta el peor con pronostico queda por encima del suelo",
    peor_visto > suelo,
    f"(peor score con dato={peor_visto} en "
    f"escalon/prob/vara={peor_caso}, suelo={suelo})",
)

# Y el 0,25 de antes, contra el que se calibro el suelo viejo,
# ya no manda sobre nada. Si volviera a ser el suelo, un
# Importante medido a 0,227 volveria a perder contra "no se
# sabe".
peldano_mas_bajo = min(HIERARCHY_MATCH_QUALITY.values())

check(
    "el peldano mas bajo de la escalera ya NO es el suelo",
    peldano_mas_bajo * motor.ESCALA_DE_LA_VARA > suelo,
    f"(peldano={peldano_mas_bajo}, suelo={suelo})",
)

# El caso de Dituro, con numeros: una vara medida POR DEBAJO del
# peldano mas bajo de la escalera sigue ganando al que no tiene
# dato. Eso es lo que el 18/09 no pasaba.
vara_de_dituro = 0.2269125

check(
    "una vara medida bajo el peldano mas bajo gana al sin dato",
    vara_de_dituro < peldano_mas_bajo
    and (
        vara_de_dituro * motor.ESCALA_DE_LA_VARA
        + motor.COBERTURA_POR_FUENTE
    )
    > suelo,
    f"(vara medida={vara_de_dituro}, "
    f"peldano mas bajo={peldano_mas_bajo})",
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
