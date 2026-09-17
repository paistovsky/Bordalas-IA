"""
La direccion del precio: lo unico del ojeador que sirve para comprar.

QUE ES ESTO Y POR QUE NO ES EL CARRY (17/09/2026)

    Ayer se midio el carry —prima + deriva + oportunidad— y salio
    que estaba BIEN Y MAL COLOCADO: dentro de `xi_upgrade_value`
    hacia que la via del once aprobara fichajes por razones de
    mercado, que es el fallo que `classify_operation` existe para
    evitar. Budimir salia a -758.571 EUR, y un coste que sale
    negativo no es un coste (doctrina 76).

    Lo que quedo dicho entonces, y es lo que se construye aqui:

        lo que le falta a la via de reventa no es el carry;
        es LA DIRECCION DEL PRECIO.

    `as_computer_resale` no distingue hoy comprar a uno que subia
    de comprar a uno que bajaba. Y son DIECINUEVE PUNTOS a diez
    dias.

POR QUE LA DIRECCION Y NO LA MAGNITUD DEL OJEADOR

    Doctrina 57: una fuente que coincide al 100 % con un dato que
    ya se tiene es un eco. La MAGNITUD del ojeador es un eco de
    `price_increment`, y por eso lleva una semana sin conectarse.

    La DIRECCION no lo es: persiste al 88,3 % de un dia al
    siguiente (n=16.873 pares), y es lo unico que se sabe del
    futuro de un precio en el momento de pujar.

    Asi que se conecta el ojeador SOLO POR LA DIRECCION. No entra
    ni un euro suyo en ninguna cuenta.

=========================================================
LO QUE SE MIDIO, Y CON QUE
=========================================================

FUENTE: `data/autopilot/price_history.json`, sello 16/09 18:23,
ventana 17/08 - 17/09, 617 jugadores con serie diaria seguida. El
dia de mercado corta en el RESET (05:00 UTC), no a medianoche.

La direccion es la de LA VISPERA: lo que hizo el precio el dia
anterior al de la compra. Es el unico dato que se tiene en la
mano cuando hay que decidir.

    plazo         SUBIA              PLANO             BAJABA
     1 d     +1,235 % (n=4120)   0,000 %    -1,389 % (n=6268)
     3 d     +3,356 % (n=3806)   0,000 %    -4,032 % (n=5739)
     5 d     +4,911 % (n=3536)   0,000 %    -6,502 % (n=5252)
    10 d     +7,430 % (n=3057)   0,000 %   -11,711 % (n=4500)   <- el pico
    15 d     +6,418 % (n=2281)   0,000 %   -15,152 % (n=3281)

EL `n` ES DE OBSERVACIONES, NO DE JUGADORES, y las ventanas se
solapan: la de un jugador el martes y la del miercoles comparten
nueve dias. Asi que el `n` dice cuanta materia hay, no cuantas
pruebas independientes. Por jugador distinto son 617.

DONDE SATURA Y SE DA LA VUELTA

    A los 10 dias. Despues DEVUELVE: +7,430 % a 10, +6,418 % a
    15. Ese es el plazo de salida, y no es un redondeo: es donde
    la curva gira.

    Del que baja no gira: sigue cayendo hasta donde alcanza la
    ventana (-15,152 % a 15 dias). Del que baja no se sale
    esperando.

Y LA FUERZA DE LA SUBIDA IMPORTA, MUCHO MAS DE LO ESPERADO

    a 10 dias, segun cuanto subio la vispera:

        subio 0-1 %        +0,889 %   (n=1175, 216 jugadores)
        subio 1-2 %        +7,745 %   (n= 658, 167 jugadores)
        subio 2-4 %       +15,410 %   (n= 465, 140 jugadores)
        subio mas de 4 %  +44,444 %   (n= 759, 119 jugadores)

    NO ES EL TAMAÑO DEL JUGADOR. Los que suben fuerte son mas
    baratos —880.000 de mediana contra 4.420.000—, asi que se
    repitio la cuenta dentro de la misma franja de precio, de
    1 a 6 millones:

        0-1 %  +0,996 %    1-2 %  +6,962 %
        2-4 % +14,050 %    +4 %  +36,667 %

    El orden aguanta entero. Un +0,3 % diario y un +4 % diario no
    son el mismo negocio, y por eso `FUERZA` esta aqui: no se
    usa todavia, pero el dia que se ordenen candidatos es esto y
    no el precio lo que los ordena.

=========================================================
LOS 19 PUNTOS AGUANTAN AL DESCONTAR AL COMPUTER
=========================================================

    La pregunta incomoda del encargo: a un dia el Computer paga
    PEOR por los que suben, y eso va en contra.

    Es cierto y esta medido (censo A, 90 ofertas vivas del 12/08
    al 13/09, sin sesgo de aceptacion): SUBIA +0,0299 %, PLANO
    +0,5758 %, BAJABA +1,8446 %.

    Pero la prima se cobra AL VENDER, y a los diez dias la mitad
    de los que entraron subiendo ya no suben:

        entrando a uno que SUBIA, a los 10 dias sale
            SUBIA 52,3 %   PLANO 8,9 %   BAJABA 38,7 %  (n=2919)

        entrando a uno que BAJABA
            SUBIA 21,1 %   PLANO 12,4 %  BAJABA 66,5 %  (n=4262)

    Con eso, la prima esperada al vender es +0,781 % entrando al
    que sube y +1,304 % entrando al que baja. El que baja cobra
    mas prima, si — medio punto mas.

        neto entrando al que SUBIA     +8,211 %
        neto entrando al que BAJABA   -10,407 %

        hueco bruto   +19,14 pp
        hueco NETO    +18,62 pp

    EL HUECO NO SE CIERRA: la prima se come 0,52 de 19,14.

=========================================================
QUE HACE ESTE MODULO, Y QUE NO
=========================================================

    HACE: decir si el carril puede comprar a alguien, mirando
    UNICAMENTE la direccion que dice el ojeador.

    NO HACE: mover ni un umbral. Ni el liston del 3 %, ni el
    suelo del +1 %, ni `bid_cap`, ni `PRIMA_MAXIMA_DE_PUJA`, ni
    `MIN_WIN_PROBABILITY`, ni el cupo. Se filtra QUE ENTRA, no
    CUANTO SE PAGA. El precio lo sigue poniendo `regla_de_compra`
    y el tope sigue siendo el suyo.

    Y ESTA APAGADO: `ENCENDIDO = False`.

SIN PRONOSTICO NO SE COMPRA

    Doctrina 24: «SIN PRONOSTICO» es una respuesta. Un jugador
    del que ninguna fuente dice nada no es un jugador que vaya a
    subir: es uno del que no se sabe. Se queda fuera, y el motivo
    lo dice con esas palabras.

    LO QUE ESO CUESTA, dicho antes de que lo pregunten: sobre las
    182 subastas medidas, 56 no tenian pronostico reconstruible
    —31 %—. Pero eso es un agujero del HISTORICO, no del filtro:
    `price_history` empieza el 17/08 y la liga empezo el 09/08.
    En produccion el ojeador habla de los veinte de hoy.
"""

from __future__ import annotations


# ============================================================
# EL INTERRUPTOR
# ============================================================

# APAGADO. El encargo lo dice y aqui queda escrito: esto se
# construye, se mide y no se enciende.
ENCENDIDO = False


def esta_encendido() -> bool:
    return bool(ENCENDIDO)


# ============================================================
# LO MEDIDO
# ============================================================

FUENTE = "data/autopilot/price_history.json"

SELLO_DE_LA_FUENTE = "2026-09-16T18:23:46"

VENTANA = "17/08/2026 - 17/09/2026"

JUGADORES_MEDIDOS = 617

# EL CORTE DEL DIA DE MERCADO. El mismo de toda la casa: el reset
# de las 05:00 UTC, no la medianoche.
HORA_DEL_RESET = 5

# Lo que hizo el precio LA VISPERA -> lo que hace despues.
#
#     `(percent, n)`. El `n` es de observaciones con ventanas que
#     se solapan, no de pruebas independientes.
RENDIMIENTO = {
    ("SUBIA", 1): (1.235, 4120),
    ("SUBIA", 3): (3.356, 3806),
    ("SUBIA", 5): (4.911, 3536),
    ("SUBIA", 10): (7.430, 3057),
    ("SUBIA", 15): (6.418, 2281),

    ("PLANO", 1): (0.000, 4865),
    ("PLANO", 3): (0.000, 4489),
    ("PLANO", 5): (0.000, 4030),
    ("PLANO", 10): (0.000, 3400),
    ("PLANO", 15): (0.000, 2458),

    ("BAJABA", 1): (-1.389, 6268),
    ("BAJABA", 3): (-4.032, 5739),
    ("BAJABA", 5): (-6.502, 5252),
    ("BAJABA", 10): (-11.711, 4500),
    ("BAJABA", 15): (-15.152, 3281),
}

PLAZOS_MEDIDOS = (1, 3, 5, 10, 15)

DIRECCIONES = ("SUBIA", "PLANO", "BAJABA")


# EL PLAZO DE SALIDA, y de donde sale.
#
#     Donde la curva del que sube SATURA Y SE DA LA VUELTA. No se
#     elige: se lee de `RENDIMIENTO`, y `comprobar_el_plazo()` lo
#     vuelve a derivar para que nadie pueda moverlo sin que la
#     tabla lo respalde.
PLAZO_DE_SALIDA = 10

PLAZO_FUENTE = (
    "A los 10 dias el que subia rinde +7,430 % y a los 15 solo "
    "+6,418 %: la curva satura y devuelve. Del que baja no gira "
    "—sigue cayendo hasta -15,152 % a 15 dias—, asi que este "
    "plazo es el de salida DEL QUE SUBE, que es el unico que este "
    "carril compra."
)


# LA FUERZA DE LA SUBIDA DE LA VISPERA -> rendimiento a 10 dias.
#
#     `(percent, n, jugadores, percent_mismo_tramo_de_precio)`.
#     El cuarto numero es la misma cuenta dentro de la franja de
#     1 a 6 millones, que es lo que descarta que esto sea el
#     tamaño del jugador y no la fuerza de la subida.
FUERZA = {
    "0-1 %": (0.889, 1175, 216, 0.996),
    "1-2 %": (7.745, 658, 167, 6.962),
    "2-4 %": (15.410, 465, 140, 14.050),
    "mas de 4 %": (44.444, 759, 119, 36.667),
}


# LA PERSISTENCIA DE LA DIRECCION, que es lo que hace que el
# pronostico del ojeador valga para algo.
PERSISTENCIA = 0.883

PERSISTENCIA_N = 16_873


# LO QUE PAGA EL COMPUTER, por direccion, EN EL MOMENTO DE
# VENDER. Censo A: 90 ofertas vivas del 12/08 al 13/09,
# deduplicadas por `offer_id`. Sin sesgo de aceptacion.
PRIMA_DEL_COMPUTER = {
    "SUBIA": (0.0299, 52),
    "PLANO": (0.5758, 11),
    "BAJABA": (1.8446, 27),
}

# COMO SALE A LOS DIEZ DIAS el que entro en cada direccion. Es lo
# que decide cual de las tres primas se cobra.
COMO_SALE = {
    "SUBIA": {"SUBIA": 0.523, "PLANO": 0.089, "BAJABA": 0.387},
    "BAJABA": {"SUBIA": 0.211, "PLANO": 0.124, "BAJABA": 0.665},
}

COMO_SALE_N = {"SUBIA": 2919, "BAJABA": 4262}


# EL HUECO, antes y despues de descontar al Computer.
HUECO_BRUTO_PP = 19.14

HUECO_NETO_PP = 18.62


# ============================================================
# LO QUE DICE EL OJEADOR
# ============================================================

# Como llama el ojeador a cada direccion. Se traducen aqui y en
# un solo sitio: `scout/common.py` usa UP/DOWN/FLAT y la tabla
# medida usa SUBIA/PLANO/BAJABA.
DEL_OJEADOR = {
    "UP": "SUBIA",
    "FLAT": "PLANO",
    "DOWN": "BAJABA",
}

# LA UNICA DIRECCION QUE ESTE CARRIL COMPRA.
COMPRAMOS_SI = "SUBIA"

SIN_PRONOSTICO = (
    "SIN PRONOSTICO: ninguna fuente dice nada de este jugador, "
    "asi que no se sabe si su precio sube. No saberlo no es que "
    "vaya a subir, y este carril no compra a ciegas."
)


def direccion_de(pronostico) -> str | None:
    """
    La direccion medible que sale de un pronostico del ojeador.

    `None` cuando no hay pronostico, cuando el ojeador no se moja
    (`direction` a None) o cuando dice algo que no entendemos. En
    los tres casos la respuesta del carril es la misma —no se
    compra—, pero el motivo NO es el mismo y por eso lo dice
    `puede_comprar`.

    Nunca lanza.
    """

    if not isinstance(pronostico, dict):
        return None

    return DEL_OJEADOR.get(pronostico.get("direction"))


def puede_comprar(pronostico) -> dict:
    """
    ¿Deja este filtro que el carril puje por este jugador?

    Solo mira LA DIRECCION. No mira el precio, no mira el saldo y
    no propone ningun importe: de eso siguen encargandose
    `regla_de_compra` y los topes de siempre, sin tocar.

    Forma fija: `{available, direccion, reason}`. Nunca lanza.
    """

    direccion = direccion_de(pronostico)

    if direccion is None:
        return {
            "available": False,
            "direccion": None,
            "reason": SIN_PRONOSTICO,
        }

    if direccion != COMPRAMOS_SI:

        esperado = RENDIMIENTO.get((direccion, PLAZO_DE_SALIDA))

        cuanto = (
            f"{esperado[0]:+.3f} % a {PLAZO_DE_SALIDA} dias "
            f"(n={esperado[1]})"
            if esperado
            else "un rendimiento que no esta medido"
        )

        return {
            "available": False,
            "direccion": direccion,
            "reason": (
                f"El ojeador dice {direccion}, y a los que "
                f"{direccion.lower()} este carril no compra: "
                f"{cuanto}."
            ),
        }

    esperado = RENDIMIENTO[(COMPRAMOS_SI, PLAZO_DE_SALIDA)]

    return {
        "available": True,
        "direccion": direccion,
        "reason": (
            f"El ojeador dice {direccion}. Medido: {esperado[0]:+.3f} % "
            f"a {PLAZO_DE_SALIDA} dias (n={esperado[1]}), y se sale "
            f"a los {PLAZO_DE_SALIDA} dias porque ahi la curva "
            f"satura."
        ),
    }


# ============================================================
# EL RENDIMIENTO, SIEMPRE CON SU `n` Y SU PLAZO
# ============================================================

def rendimiento(direccion, plazo) -> dict:
    """
    Lo que rinde entrar en esa direccion a ese plazo.

    Devuelve SIEMPRE `percent`, `n`, `plazo_dias` y `fuente`
    juntos. Doctrina 53 y 55: un porcentaje sin su plazo no es un
    rendimiento, y sin su `n` es una anecdota. Aqui no se pueden
    separar porque salen del mismo sitio.

    Con una direccion o un plazo que no se midieron dice que no
    hay dato, en vez de interpolar. Nunca lanza.
    """

    clave = (direccion, plazo)

    if clave not in RENDIMIENTO:
        return {
            "available": False,
            "percent": None,
            "n": 0,
            "plazo_dias": plazo,
            "fuente": FUENTE,
            "sello": SELLO_DE_LA_FUENTE,
            "reason": (
                f"No hay medicion de {direccion} a {plazo} dias. "
                f"Medidos: {sorted(set(PLAZOS_MEDIDOS))} dias, y "
                f"las direcciones {list(DIRECCIONES)}. No se "
                f"interpola entre plazos: la curva ni siquiera es "
                f"monotona —del que sube gira a los 10 dias—."
            ),
        }

    percent, n = RENDIMIENTO[clave]

    return {
        "available": True,
        "percent": percent,
        "n": n,
        "plazo_dias": plazo,
        "direccion": direccion,
        "fuente": FUENTE,
        "sello": SELLO_DE_LA_FUENTE,
        "ventana": VENTANA,
        "jugadores": JUGADORES_MEDIDOS,
    }


def comprobar_el_plazo() -> dict:
    """
    Vuelve a deducir el plazo de salida DE LA TABLA.

    Existe para que `PLAZO_DE_SALIDA` no pueda moverse a un
    numero que la medicion no respalde. Es el sitio donde gira la
    curva del que sube, y se calcula, no se escribe.
    """

    sube = [
        (plazo, RENDIMIENTO[("SUBIA", plazo)][0])
        for plazo in sorted(PLAZOS_MEDIDOS)
        if ("SUBIA", plazo) in RENDIMIENTO
    ]

    if not sube:
        return {
            "available": False,
            "reason": (
                "La tabla de rendimiento llega vacia: sin ella no "
                "hay plazo de salida que derivar."
            ),
        }

    pico, cuanto = max(sube, key=lambda fila: fila[1])

    despues = [fila for fila in sube if fila[0] > pico]

    return {
        "available": True,
        "plazo": pico,
        "percent": cuanto,
        "devuelve_despues": bool(despues) and all(
            fila[1] < cuanto for fila in despues
        ),
        "siguientes": despues,
        "cuadra_con_el_declarado": pico == PLAZO_DE_SALIDA,
        "fuente": PLAZO_FUENTE,
    }


def neto_al_salir(direccion) -> dict:
    """
    El rendimiento a `PLAZO_DE_SALIDA` mas la prima del Computer.

    La prima se cobra AL VENDER, asi que la que toca depende de
    como salga el jugador a los diez dias, no de como entro. Esa
    es toda la cuenta y por eso esta aqui y no repartida.

    Nunca lanza.
    """

    base = rendimiento(direccion, PLAZO_DE_SALIDA)

    reparto = COMO_SALE.get(direccion)

    if not base.get("available") or not reparto:
        return {
            "available": False,
            "reason": (
                f"No se puede netear {direccion}: hace falta el "
                f"rendimiento a {PLAZO_DE_SALIDA} dias y como sale "
                f"el jugador a ese plazo, y falta alguno de los "
                f"dos."
            ),
        }

    prima = sum(
        PRIMA_DEL_COMPUTER[como][0] * peso
        for como, peso in reparto.items()
        if como in PRIMA_DEL_COMPUTER
    )

    return {
        "available": True,
        "direccion": direccion,
        "deriva_percent": base["percent"],
        "deriva_n": base["n"],
        "prima_percent": round(prima, 3),
        "prima_n": COMO_SALE_N.get(direccion),
        "neto_percent": round(base["percent"] + prima, 3),
        "plazo_dias": PLAZO_DE_SALIDA,
        "como_sale": dict(reparto),
    }


# ============================================================
# QUE HABRIA CAMBIADO
# ============================================================

def que_cambia(subastas, nuestro_id) -> dict:
    """
    Sobre subastas ya ocurridas: en cuantas se habria pujado.

    `subastas` son las del tablon, cada una con `dir` —la
    direccion de la vispera—, `pujamos` y `ganamos`.

    LO QUE ESTO MIDE Y LO QUE NO. Mide el filtro como RESTA sobre
    lo que se hizo: de las que se pujaron, cuantas quedan. NO
    mide cuantas se habrian pujado de mas, porque el filtro no
    hace aparecer a nadie — solo quita. Las que deja pasar y no
    se pujaron salen aparte, en `deja_y_no_pujamos`, que es el
    hueco de verdad.

    Nunca lanza; con la lista vacia dice que no hay subastas.
    """

    filas = [s for s in (subastas or []) if isinstance(s, dict)]

    if not filas:
        return {
            "available": False,
            "n": 0,
            "reason": (
                "No hay subastas que contar: sin tablon no se "
                "puede decir que habria cambiado."
            ),
        }

    pasan = [s for s in filas if s.get("dir") == COMPRAMOS_SI]

    sin_dato = [s for s in filas if s.get("dir") is None]

    pujadas = [s for s in filas if s.get("pujamos")]

    ganadas = [s for s in filas if s.get("ganamos")]

    quedan = [s for s in pujadas if s.get("dir") == COMPRAMOS_SI]

    ganadas_que_quedan = [
        s for s in ganadas if s.get("dir") == COMPRAMOS_SI
    ]

    return {
        "available": True,
        "n": len(filas),
        "deja_pasar": len(pasan),
        "sin_pronostico": len(sin_dato),
        "pujadas": len(pujadas),
        "pujadas_con_filtro": len(quedan),
        "ganadas": len(ganadas),
        "ganadas_con_filtro": len(ganadas_que_quedan),
        "ganadas_que_se_caen": [
            s for s in ganadas if s.get("dir") != COMPRAMOS_SI
        ],
        "deja_y_no_pujamos": [
            s for s in pasan if not s.get("pujamos")
        ],

        # EL AVISO, calculado y no opinado: si el filtro deja
        # menos pujas de las que hubo, es una resta.
        "pujariamos_menos": len(quedan) < len(pujadas),
    }


# ============================================================
# EL ORDEN, QUE NO ES UNA PUERTA
# ============================================================
#
# LO QUE SE APRENDIO AYER, y es la unica razon de que esto sea un
# orden y no un filtro:
#
#     UN FILTRO NO HACE APARECER A NADIE. SOLO QUITA.
#
#     Medido sobre las 182 subastas: filtrando por direccion se
#     pujaba en 18 en vez de en 37, y se caian 19 de las 26 que
#     ganamos. El problema medido es que aparecemos poco -20 %
#     contra el 60 % de Pollo-, asi que cualquier cosa que reste
#     pujas va contra el problema.
#
#     Ordenar no resta. Con el mismo dinero y el mismo cupo, se
#     mira primero al que sube — y entre los que suben, al que
#     subio mas fuerte la vispera, que es donde estan los +44 %.
#
# DONDE VA CUANDO SE ENCIENDA
#
#     `acquisition_board.py`, en el `filas.sort(...)` de la linea
#     1330. Entra como un DESEMPATE mas, detras de los que ya
#     mandan —la decision, la puja viva y el escalon de
#     `deployment`— y delante del valor. Asi no cambia quien
#     entra ni cuanto se paga: cambia a quien se mira primero.
#
# POR QUE NO PUEDE CAER NINGUNA PUJA
#
#     Porque es un `sort`, no un `filter`: una ordenacion es una
#     permutacion y devuelve exactamente los mismos elementos.
#     Eso no es una opinion, es la propiedad que mide
#     `test_el_orden_no_quita_pujas` — misma cuenta, mismo
#     conjunto de identificadores, mismas decisiones BID.

# El interruptor del orden, aparte del interruptor del filtro:
# son dos cosas distintas y se encienden por separado.
ORDEN_ENCENDIDO = False


def esta_encendido_el_orden() -> bool:
    return bool(ORDEN_ENCENDIDO)


# Los tramos de fuerza de la vispera, de mas fuerte a mas flojo,
# con lo que rinde cada uno a `PLAZO_DE_SALIDA` dias.
TRAMOS_DE_FUERZA = (
    ("mas de 4 %", 4.0),
    ("2-4 %", 2.0),
    ("1-2 %", 1.0),
    ("0-1 %", 0.0),
)


def tramo_de_fuerza(cambio_percent):
    """En que tramo cae una subida de la vispera. None si no sube."""

    if cambio_percent is None:
        return None

    try:
        cuanto = float(cambio_percent)

    except (TypeError, ValueError):
        return None

    if cuanto <= 0:
        return None

    for nombre, suelo in TRAMOS_DE_FUERZA:
        if cuanto >= suelo:
            return nombre

    return "0-1 %"


def clave_de_orden(pronostico, cambio_de_la_vispera=None) -> tuple:
    """
    El desempate por direccion. Mas pequeño va antes.

    `(escalon, -fuerza)`:

        escalon 0   el ojeador dice que SUBE
        escalon 1   todos los demas, sin distinguir

    Y dentro de los que suben ordena por lo que subio la vispera,
    de mas a menos, porque eso es lo que separa un +0,889 % de un
    +44,444 % a diez dias (n=1175 y n=759).

    NO SE PARTE EL ESCALON 1. Al que baja y al que no tiene
    pronostico se les trata igual a efectos de orden: distinguirlos
    seria empezar a castigar por no tener dato, y de ahi a quitarlo
    de la lista hay un paso. El que no tiene pronostico sigue
    pujando exactamente igual que hoy.

    Nunca lanza.
    """

    sube = direccion_de(pronostico) == COMPRAMOS_SI

    if not sube:
        return (1, 0.0)

    try:
        fuerza = float(cambio_de_la_vispera or 0.0)

    except (TypeError, ValueError):
        fuerza = 0.0

    return (0, -fuerza)


def ordenar(filas, pronosticos=None, cambios=None, clave=None) -> dict:
    """
    Reordena los candidatos por direccion. NO quita ninguno.

    `filas` son los candidatos; `pronosticos` y `cambios` son
    diccionarios por identificador. `clave` dice como sacar el
    identificador de una fila.

    Devuelve `{available, filas, movidos, reason}` — y `filas` es
    SIEMPRE una permutacion de la entrada, tambien cuando el
    interruptor esta apagado (entonces es la entrada tal cual).

    ORDENACION ESTABLE: `sorted` lo es, asi que dos candidatos con
    la misma direccion y la misma fuerza conservan el orden que
    traian. Lo que este desempate no decide, lo sigue decidiendo
    quien lo decidia antes.

    Nunca lanza.
    """

    entrada = list(filas or [])

    if not entrada:
        return {
            "available": False,
            "filas": [],
            "movidos": 0,
            "reason": (
                "No hay candidatos que ordenar. Ordenar una lista "
                "vacia no prueba nada."
            ),
        }

    if not ORDEN_ENCENDIDO:
        return {
            "available": False,
            "filas": entrada,
            "movidos": 0,
            "reason": (
                "El orden por direccion esta apagado "
                "(`ORDEN_ENCENDIDO = False`): las filas salen "
                "exactamente como entraron."
            ),
        }

    pronosticos = pronosticos or {}

    cambios = cambios or {}

    def identificador(fila):
        if clave is not None:
            return clave(fila)

        if isinstance(fila, dict):
            return fila.get("player_id", fila.get("id"))

        return None

    salida = sorted(
        entrada,
        key=lambda fila: clave_de_orden(
            pronosticos.get(identificador(fila)),
            cambios.get(identificador(fila)),
        ),
    )

    movidos = sum(
        1
        for antes, despues in zip(entrada, salida)
        if antes is not despues
    )

    return {
        "available": True,
        "filas": salida,
        "movidos": movidos,
        "reason": (
            f"Reordenados {len(salida)} candidatos por la direccion "
            f"de la vispera. No se ha quitado ninguno: "
            f"{len(entrada)} entraron y {len(salida)} salen."
        ),
    }
