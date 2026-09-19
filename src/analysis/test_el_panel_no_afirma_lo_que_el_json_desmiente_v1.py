"""
El panel no afirma lo que su propio JSON desmiente.

LAS FRASES, MEDIDAS SOBRE LA FOTO DEL 18/09 16:16:38

    (a) TRENT, QUE NO ESTA EN LA PLANTILLA

        loNuestroALaVenta.comprado_sin_publicar:
            "Trent esta comprado para revender y no esta a la
             venta. Lo compramos el 13/09 a las 10:08..."

        Y en el MISMO objeto, por_que_no_se_publico.saltados:
            "Trent no esta en la plantilla: la puja no se ha
             resuelto a nuestro favor."

        Los 18 de `roster` no incluyen a Trent. Las dos frases se
        contradicen, y LAS DOS estan mal. Lo que paso de verdad:

            12/09 14:45   puja de 2.760.000, via RENDIJA
            13/09 05:06   GANADA  (tablon: 37499 -> Pepe)
            13/09 08:08   se abre el viaje, estado ABIERTO
            17/09 22:12   VENDIDO (tablon: 37499 from Pepe)

        La puja SI se resolvio a nuestro favor. Lo compramos y lo
        vendimos. Lo que quedo mal es el viaje, que se abrio y no
        se cerro al venderlo.

        La causa: `viajes_sin_listar` cruza los viajes contra los
        LISTADOS, y nunca contra la PLANTILLA. Un viaje de un
        jugador que ya no es nuestro sale como "comprado y sin
        publicar" para siempre.

    (c) DOS FICHAS O OCHO

        `signing_priority` devuelve, literalmente:
            "Con ocho fichas vacias, llenar una vale mas que una
             especulacion..."

        La palabra "ocho" esta escrita a mano en el codigo. La
        funcion NO recibe `free_roster_slots`: no puede saber
        cuantas hay. En la foto habia 2.

    (b) CUANDO SOMOS LIDERES, EL LIDER SOMOS NOSOTROS

        `value_gap_to_leader = valor_lider - nuestro_valor`. El
        dia que vamos primeros, `lider` somos nosotros, la resta
        da 0 y la frase sale "Tu plantilla vale lo mismo que la
        del lider". La cabeza de la misma frase YA usa
        `is_leader` para decir "Vas 1º": el dato esta, y la cola
        no lo mira.

QUE COMPRUEBA ESTA GUARDIA

    1. Ninguna frase publicada nombra a un jugador que no este en
       la plantilla.
    2. Ninguna frase da un recuento distinto del campo del que
       sale.
    3. Siendo lideres, la comparacion no se hace contra nosotros
       mismos.

    (1) y (2) ESTAN EN ROJO. Son las frases, convertidas en
    comprobacion.

LA GUARDIA MUERDE CON EL PANEL VACIO

    Sin frases no hay nada que contradecir y las tres pasarian
    por vacuidad. Por eso lo primero es exigir que el banco traiga
    plantilla, viajes y frases.

DE DONDE SALEN LOS NUMEROS

    Fijos, escritos aqui, copiados de la foto del 18/09 16:16:38.
    No se lee `diagnostico/status.json` ni `data/`, no se sale a
    la red y no se mira el reloj: `viajes_sin_listar` recibe el
    `ahora` como parametro.
"""

import re
import sys
from datetime import datetime, timezone

sys.path.insert(0, ".")

from src.actions.escaparate_executor import (  # noqa: E402
    viajes_sin_listar,
)
from src.analysis.deployment import (  # noqa: E402
    signing_priority,
)
from src.analysis.race_state import _headline  # noqa: E402


fallos = []


def check(nombre, condicion, detalle=""):
    if condicion:
        print(f"  OK   {nombre}")
    else:
        print(f"  FALLA {nombre} {detalle}")
        fallos.append(nombre)


# ================================================================
# EL BANCO: LA FOTO DEL 18/09, TAL CUAL
# ================================================================

# Los 18 de `roster`. Trent NO esta.
PLANTILLA = [
    "Barzic", "Boyomo", "Dituro", "Djene", "Esquivel",
    "Exposito", "Iturbe", "Jonny", "Jutgla", "Manu Sanchez",
    "Marcao", "Olasagasti", "Oriol Rey", "Pablo Duran",
    "Pablo Ibanez", "Ruben Garcia", "Yamal", "Alvaro Carreras",
]

# El viaje que se abrio el 13/09 y nunca se cerro.
VIAJES = [
    {
        "player_id": 37499,
        "name": "Trent",
        "opened_at": "2026-09-13T08:08:32.022440+00:00",
        "cost": 2_760_000,
    }
]

# Trent no esta listado: no es nuestro desde el 17/09.
LISTADOS = [{"player_id": 33694, "name": "Boyomo"}]

AHORA = datetime(2026, 9, 18, 16, 16, 38, tzinfo=timezone.utc)

FICHAS_LIBRES = 2


# ================================================================
# 0. EL BANCO NO LLEGA VACIO
# ================================================================

print()
print("0. El panel no llega vacio")

check(
    "hay plantilla",
    len(PLANTILLA) == 18,
    f"(n={len(PLANTILLA)})",
)

check(
    "hay un viaje abierto que mirar",
    len(VIAJES) == 1,
)

sin_viajes = viajes_sin_listar([], [], ahora=AHORA)

check(
    "sin viajes la pantalla no dice que todo vaya bien",
    "no hay nada que mirar" in (sin_viajes["reason"] or ""),
    f"({sin_viajes['reason']})",
)


# ================================================================
# 1. NINGUNA FRASE NOMBRA A QUIEN NO ESTA EN LA PLANTILLA
# ================================================================

print()
print("1. Ninguna frase nombra a un jugador que no tenemos")

aviso = viajes_sin_listar(VIAJES, LISTADOS, ahora=AHORA)

frase = aviso["reason"] or ""

print(f"       {frase[:110]}")

nombrados = [
    v["name"]
    for v in VIAJES
    if v["name"] and v["name"] in frase
]

fuera = [n for n in nombrados if n not in PLANTILLA]

check(
    "la frase no nombra a nadie que no este en la plantilla",
    not fuera,
    f"<- nombra a {fuera} y no esta en los {len(PLANTILLA)} de "
    f"`roster`. El viaje se cruza contra LISTADOS, nunca contra "
    f"la plantilla.",
)

check(
    "y no afirma una compra que no consta como nuestra",
    "comprado para revender" not in frase or not fuera,
    "<- dice 'lo compramos' de un jugador vendido el 17/09.",
)


# ================================================================
# 2. NINGUN RECUENTO DISTINTO DEL CAMPO DEL QUE SALE
# ================================================================

print()
print("2. Ningun recuento distinto del campo del que sale")

NUMEROS = {
    "cero": 0, "una": 1, "dos": 2, "tres": 3, "cuatro": 4,
    "cinco": 5, "seis": 6, "siete": 7, "ocho": 8, "nueve": 9,
    "diez": 10,
}

operacion = {
    "operation_class": "SIGNING",
    "route": "ROSTER_FILL",
}

prioridad = signing_priority(
    operacion,
    as_xi={"is_upgrade": True},
    price_increment=1,
)

razon = prioridad["priority_reason"] or ""

print(f"       {razon[:110]}")

dichos = [
    (palabra, valor)
    for palabra, valor in NUMEROS.items()
    if re.search(rf"\b{palabra}\b fichas", razon)
]

check(
    "la frase de fichas no dice un recuento que no le han dado",
    not dichos,
    f"<- dice {dichos} y las fichas libres eran "
    f"{FICHAS_LIBRES}. `signing_priority` no recibe "
    f"`free_roster_slots`: no puede saberlo.",
)


# ================================================================
# 3. SIENDO LIDERES NO NOS COMPARAMOS CON NOSOTROS MISMOS
# ================================================================

print()
print("3. Siendo lideres, la comparacion no es contra nosotros")

# El 19/09: primeros con 276, Pollo segundo con 270.
LIDERES = {
    "position": 1,
    "points": 276,
    "is_leader": True,
    "season_started": True,
    "points_ahead": 6,
    "points_behind": 0,
    "matchdays_remaining": 31,
    "required_pace": 0.0,
    "team_value": 57_350_000,
    "leader_team_value": 57_350_000,
    "value_gap_to_leader": 0,
}

titular = _headline(LIDERES)

print(f"       {titular[:150]}")

check(
    "no dice que valemos lo mismo que el lider siendo el lider",
    "lo mismo que la del lider" not in titular,
    "<- siendo lideres, `value_gap_to_leader` es 0 por "
    "construccion: el lider somos nosotros. Tapa que el segundo "
    "tiene 93,06 M contra nuestros 57,35 M.",
)

# Y el otro lado: siendo segundos la frase SI vale.
SEGUNDOS = {
    **LIDERES,
    "position": 2,
    "is_leader": False,
    "points": 247,
    "points_behind": 6,
    "leader_team_value": 79_040_000,
    "team_value": 54_480_000,
    "value_gap_to_leader": 24_560_000,
}

titular_2 = _headline(SEGUNDOS)

check(
    "siendo segundos la comparacion contra el lider si vale",
    "24,6 M menos que la del lider" in titular_2,
    f"({titular_2[-60:]})",
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
