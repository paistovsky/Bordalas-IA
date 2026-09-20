"""
Un interruptor por vuelta, nunca dos.

POR QUE

    Cambiar dos cosas a la vez es no saber cual movio que. Si se
    encienden la regla del deficit y el cupo la misma manana y el
    lunes aparecemos en cuatro subastas mas, no hay forma de
    saber cual lo hizo — ni cual apagar si sale mal.

    Se dijo el 15/09 con el liston del 3 % y vuelve a valer
    ahora, con cuatro interruptores esperando.

QUE HACE EL AVISO, Y QUE NO

    AVISA. No apaga. Apagar por su cuenta seria decidir, y quien
    decide es el dueno: puede haber un dia en que quiera los dos
    puestos sabiendo lo que pierde. Lo que no puede pasar es que
    ocurra sin que nadie lo vea.

EL ENTORNO SE RECIBE

    `el_aviso(entorno)` toma un diccionario. Leer `os.environ` de
    verdad haria que esta guardia cambiara de color segun quien
    la corra y con que variables puestas — que es lo mismo que
    leer estado de produccion, con otro nombre.

QUE COMPRUEBA ESTA GUARDIA

    1. Con DOS interruptores nuevos puestos, la vuelta avisa.
    2. Con uno, no avisa.
    3. Con ninguno, tampoco.
    4. El aviso NOMBRA cuales son los dos (doctrina 87).
    5. Un interruptor de fuera del protocolo no cuenta.
    6. Los cuatro tienen ficha completa, con su prediccion
       escrita y su senal de apagado.

LA GUARDIA MUERDE SIN INTERRUPTORES

    Sin ninguno declarado no hay nada que vigilar y todo pasaria
    por vacuidad. Por eso lo primero es exigir que el protocolo
    traiga los cuatro.

DE DONDE SALEN LOS NUMEROS

    Fijos, escritos aqui. El entorno es un diccionario de este
    fichero: no se lee `os.environ`, ni `data/`, ni se sale a la
    red, ni se mira el reloj.
"""

import sys

sys.path.insert(0, ".")

from src.analysis.el_protocolo_de_encendido import (  # noqa: E402
    LOS_CUATRO,
    PROTOCOLO,
    el_aviso,
    ficha_de,
)


fallos = []


def check(nombre, condicion, detalle=""):
    if condicion:
        print(f"  OK   {nombre}")
    else:
        print(f"  FALLA {nombre} {detalle}")
        fallos.append(nombre)


# ================================================================
# 0. EL PROTOCOLO TRAE INTERRUPTORES
# ================================================================

print()
print("0. El protocolo no llega vacio")

# ERAN CUATRO, Y EL 20/09 SE PUSIERON OCHO
#
#     La cola del 20/09 —SIN_REFERENCIA_ESCALA,
#     CESTA_SOLO_EL_SUELO, JORNADAS_POR_SU_FECHA y
#     OBJETIVOS_EL_CATALOGO— vivia en un informe. Este modulo
#     dice, en su propia cabecera, que las fichas van en el
#     codigo y no en un informe: se mudaron aqui.
#
#     Por eso la cuenta no se escribe a mano. Lo que no puede
#     cambiar no es CUANTOS son, es que esten completos, sin
#     repetidos y numerados de uno en uno.

check(
    "el protocolo no llega vacio",
    len(PROTOCOLO) >= 4,
    f"(n={len(PROTOCOLO)})",
)

check(
    "y todos tienen nombre distinto",
    len(set(LOS_CUATRO)) == len(PROTOCOLO),
    f"({LOS_CUATRO})",
)

check(
    "van numerados de uno en uno, sin saltos",
    [f["orden"] for f in PROTOCOLO]
    == list(range(1, len(PROTOCOLO) + 1)),
    f"({[f['orden'] for f in PROTOCOLO]})",
)

check(
    "el primero es el que impide la jornada en blanco",
    PROTOCOLO[0]["interruptor"] == "BORDALAS_COBRAR_EN_DEFICIT",
    f"({PROTOCOLO[0]['interruptor']})",
)

check(
    "el cuarto sigue siendo el tope del once",
    PROTOCOLO[3]["interruptor"] == "BORDALAS_TOPE_DEL_ONCE",
    f"({PROTOCOLO[3]['interruptor']})",
)

check(
    "y el ultimo es el que ya rompio una vuelta",
    PROTOCOLO[-1]["interruptor"]
    == "BORDALAS_OBJETIVOS_EL_CATALOGO",
    f"({PROTOCOLO[-1]['interruptor']})",
)


# ================================================================
# 1. DOS PUESTOS: AVISA
# ================================================================

print()
print("1. Con dos interruptores nuevos, la vuelta avisa")

DOS = {
    "BORDALAS_COBRAR_EN_DEFICIT": "1",
    "BORDALAS_CUPO_POR_ENVIOS": "1",
}

aviso = el_aviso(DOS)

print(f"       {aviso['reason'][:110]}")

check(
    "avisa",
    aviso["ok"] is False,
    f"({aviso})",
)

check(
    "y cuenta dos",
    aviso["cuantos"] == 2,
    f"({aviso['cuantos']})",
)

check(
    "nombrando cuales son",
    "BORDALAS_COBRAR_EN_DEFICIT" in aviso["reason"]
    and "BORDALAS_CUPO_POR_ENVIOS" in aviso["reason"],
    f"({aviso['reason']})",
)

check(
    "y explicando por que importa",
    "no saber cual movio que" in aviso["reason"],
    f"({aviso['reason']})",
)


# ================================================================
# 2. UNO: NO AVISA
# ================================================================

print()
print("2. Con uno solo, no avisa")

UNO = {"BORDALAS_COBRAR_EN_DEFICIT": "1"}

solo = el_aviso(UNO)

check(
    "no avisa",
    solo["ok"] is True,
    f"({solo})",
)

check(
    "y dice cual esta puesto",
    solo["encendidos"] == ["BORDALAS_COBRAR_EN_DEFICIT"],
    f"({solo['encendidos']})",
)


# ================================================================
# 3. NINGUNO: TAMPOCO
# ================================================================

print()
print("3. Con ninguno, tampoco")

nada = el_aviso({})

check(
    "no avisa",
    nada["ok"] is True,
)

check(
    "y lo dice",
    "Ningun interruptor" in nada["reason"],
    f"({nada['reason']})",
)


# ================================================================
# 4. LOS DE FUERA DEL PROTOCOLO NO CUENTAN
# ================================================================

print()
print("4. Un interruptor de fuera del protocolo no cuenta")

CON_AJENO = {
    "BORDALAS_COBRAR_EN_DEFICIT": "1",
    "BORDALAS_NO_REPETIR_LA_ESCRITURA": "1",
    "BORDALAS_SIN_SUBASTA": "1",
}

mixto = el_aviso(CON_AJENO)

check(
    "sigue contando uno solo",
    mixto["cuantos"] == 1,
    f"({mixto['encendidos']})",
)

check(
    "y no avisa",
    mixto["ok"] is True,
)


# ================================================================
# 5. LAS CUATRO FICHAS, COMPLETAS
# ================================================================

print()
print("5. Las cuatro fichas tienen sus cinco campos")

CAMPOS = (
    "interruptor",
    "que_cambia",
    "que_mirar_antes",
    "que_deberia_pasar",
    "senal_de_apagarlo",
)

for nombre in LOS_CUATRO:

    ficha = ficha_de(nombre)

    faltan = [c for c in CAMPOS if not ficha.get(c)]

    check(
        f"{nombre.replace('BORDALAS_', '')} completa",
        not faltan,
        f"(faltan {faltan})",
    )

print()

check(
    "todas dicen QUE MIRAR con campos del JSON, no en prosa",
    all(
        len(ficha_de(n)["que_mirar_antes"]) >= 3
        for n in LOS_CUATRO
    ),
)

check(
    "todas tienen su senal de apagado con plazo o condicion",
    all(
        len(ficha_de(n)["senal_de_apagarlo"]) > 80
        for n in LOS_CUATRO
    ),
)

check(
    "el primero avisa de encenderlo DESPUES de volver a positivo",
    "volver a positivo"
    in ficha_de("BORDALAS_COBRAR_EN_DEFICIT")[
        "condicion_de_encendido"
    ].lower(),
)

check(
    "y el ultimo esta condicionado a la tabla marginal",
    "tabla marginal"
    in ficha_de("BORDALAS_TOPE_DEL_ONCE")[
        "condicion_de_encendido"
    ].lower(),
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
