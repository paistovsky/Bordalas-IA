"""
Las guardias de LA DIRECCION DEL PRECIO.

QUE SE PRUEBA AQUI

    1. Todo lo que el codigo escribe bajo el directorio de estado
       esta clasificado: o es libro y se guarda, o esta dicho por
       que no lo es.
    2. El rendimiento se publica partido por direccion Y por
       plazo, y cada celda lleva su `n`.
    3. El carril no compra a los que bajan, ni a los que no
       tienen pronostico.
    4. El plazo de salida sale de donde gira la curva.
    5. Esto sigue apagado.

NINGUNA DE ESTAS GUARDIAS LEE ESTADO, SALE A LA RED, MIRA EL
RELOJ DEL SISTEMA NI ESCRIBE EN LOS LIBROS. La primera abre
CODIGO FUENTE de este repositorio —los `.py` de `src/` y
`scripts/`—, que no es estado: es lo mismo que mira
`test_verja_determinista_v1`.

POR QUE LA PRIMERA NO CORRE LA VERJA ENTERA

    Lo mismo que se dijo ayer y sigue siendo verdad: correr las
    otras 151 guardias para vigilarlas duplicaria la verja
    —medido: no termina en diez minutos— y ADEMAS escribiria en
    los libros de verdad, que es justo lo que se quiere impedir.

    Asi que se prueba LA CAUSA —un fichero escrito por el codigo
    que nadie ha clasificado— y no el sintoma. El sintoma se
    midio a mano, ejecutando, y esta en el informe.

Y NINGUNA PASA CON LAS MANOS VACIAS: si el censo no encuentra
nada que el codigo escriba, o si la tabla medida llega vacia, la
guardia FALLA. Una comprobacion sobre cero elementos no prueba
nada, y es exactamente la forma en que un detector roto parece
verde.
"""

from __future__ import annotations

import sys

from pathlib import Path


RAIZ = Path(__file__).resolve().parents[2]

sys.path.insert(0, str(RAIZ))

from src.analysis import la_direccion as D           # noqa: E402

from src.estado.los_libros import (                  # noqa: E402
    LIBROS,
    NO_SON_LIBROS,
    clasificados,
    escritos_por_el_codigo,
    rutas,
    sin_clasificar,
)


# ============================================================
# 1. TODO LIBRO ESCRITO ESTA EN LA LISTA
# ============================================================

def test_todo_libro_escrito_esta_en_la_lista() -> None:
    """
    Nada que el codigo escriba se queda sin clasificar.

    EL FALLO QUE CAZA (medido el 17/09/2026)

        El codigo escribia 47 ficheros bajo el directorio de
        estado. La lista de guardado tenia 16. De los 31 que
        faltaban, OCHO eran libros de verdad —el de viajes, el de
        salidas, el de la ventana, el del escaparate del carril,
        los dos de acierto de fuentes, el de rechazos y el de
        reofertas del Computer—.

        Y como el `.gitignore` se genera de esa misma lista, un
        libro que no estuviera en ella quedaba TAPADO: vivia en
        la cache del runner y moria con ella a los siete dias.
        Es el mismo agujero que se comio la carpeta de
        solvencia la semana pasada, y llevaba ahi desde que cada uno de esos
        libros nacio.

        NADIE SE EQUIVOCO AL CLASIFICARLOS. Es que nadie tuvo que
        clasificarlos: un fichero nuevo aparecia en la carpeta
        de estado, el `.gitignore` lo tapaba, y no pasaba nada. Esta guardia es
        lo que hace que pase algo.

    POR QUE EXIGE CLASIFICACION Y NO PERTENENCIA

        No todo lo que se escribe es un libro: hay veinticinco
        caches que se recalculan de la foto cada vuelta, y
        meterlos en git seria commitear ruido. Asi que lo que se
        exige no es "esta en LIBROS" sino "alguien ha dicho cual
        de las dos cosas es".
    """

    escritos = escritos_por_el_codigo(RAIZ)

    # CON LAS MANOS VACIAS NO SE PASA. Si el censo no encuentra
    # nada, esta roto el censo: este repositorio escribe libros.
    assert escritos, (
        "El censo no ha encontrado NI UN fichero escrito bajo el "
        "directorio de estado. Eso no puede ser cierto en este "
        "repositorio, asi que lo que esta roto es el censo — y un "
        "censo roto es verde por el mismo motivo que uno vacio."
    )

    assert len(escritos) >= 20, (
        f"El censo solo ha encontrado {len(escritos)} ficheros "
        f"escritos. El 17/09 eran 47. Una caida asi es un "
        f"detector que ha dejado de seguir la ruta a traves de "
        f"las funciones, no un repositorio que ha dejado de "
        f"escribir."
    )

    huerfanos = sin_clasificar(RAIZ)

    assert not huerfanos, (
        "El codigo escribe ficheros que nadie ha clasificado:\n"
        + "\n".join(
            f"    {ruta}   <- {', '.join(quienes)}"
            for ruta, quienes in sorted(huerfanos.items())
        )
        + "\n\n  Cada uno tiene que ir a una de las dos listas de "
        "`src/estado/los_libros.py`:\n"
        "    LIBROS        si se acumula y no se puede volver a "
        "pedir. Se guarda en git.\n"
        "    NO_SON_LIBROS si se recalcula de la foto. Se dice "
        "por que, y ya esta.\n"
        "  Si se deja sin decidir, el `.gitignore` lo tapa y el "
        "fichero muere con el runner EN SILENCIO."
    )


def test_el_gitignore_no_tapa_un_libro() -> None:
    """
    Un libro de la lista que el `.gitignore` siga tapando no
    existe: se guardaria en un sitio y se borraria en otro.
    """

    import subprocess

    faltan = []

    for ruta in rutas():

        proceso = subprocess.run(
            ["git", "check-ignore", "-q", "--", ruta],
            cwd=str(RAIZ),
            capture_output=True,
        )

        if proceso.returncode == 0:
            faltan.append(ruta)

    assert rutas(), "La lista de libros llega vacia."

    assert not faltan, (
        "Estos libros estan en la lista y el `.gitignore` los "
        "sigue tapando:\n"
        + "\n".join(f"    {r}" for r in faltan)
        + "\n  Regenere el bloque con "
        "`python scripts/guardar_los_libros.py --gitignore`."
    )


def test_ningun_libro_se_clasifico_dos_veces() -> None:
    """
    Un mismo fichero no puede ser libro y cache a la vez: si lo
    fuera, cual gana dependeria de quien lo mire.
    """

    en_libros = set(rutas())

    en_caches = {ruta for ruta, _ in NO_SON_LIBROS}

    assert en_libros and en_caches, (
        "Alguna de las dos listas llega vacia: sin las dos no hay "
        "clasificacion que comprobar."
    )

    ambas = sorted(en_libros & en_caches)

    assert not ambas, (
        "Estos ficheros estan clasificados como libro Y como "
        "cache a la vez: " + ", ".join(ambas)
    )

    assert len(en_libros) == len(LIBROS), (
        "Hay rutas repetidas dentro de `LIBROS`: "
        f"{len(LIBROS)} entradas para {len(en_libros)} rutas."
    )

    sin_motivo = [
        ruta for ruta, motivo in NO_SON_LIBROS if not str(motivo).strip()
    ]

    assert not sin_motivo, (
        "Estos no-libros no dicen por que no lo son: "
        + ", ".join(sin_motivo)
        + ". Una exclusion sin motivo es una exclusion por "
        "comodidad, y asi es como se perdieron los ocho de hoy."
    )


# ============================================================
# 2. EL RENDIMIENTO LLEVA DIRECCION Y PLAZO
# ============================================================

def test_el_rendimiento_lleva_direccion_y_plazo() -> None:
    """
    El rendimiento se publica partido por las dos cosas, y cada
    celda con su `n`.

    POR QUE LAS DOS Y NO UNA

        Doctrina 53: un porcentaje sin su plazo no es un
        rendimiento. Y este ademas no es monotono —el que sube
        gira a los 10 dias—, asi que un numero sin plazo no solo
        esta incompleto: puede estar del lado equivocado del pico.

        Doctrina 55: y sin su `n` es una anecdota.

        Las dos juntas son la celda. Por eso `rendimiento()`
        devuelve `percent`, `n` y `plazo_dias` en la misma
        respuesta y no hay forma de pedir uno sin los otros.
    """

    # CON LA TABLA VACIA NO SE PASA.
    assert D.RENDIMIENTO, (
        "La tabla de rendimiento llega vacia. Sin historico no "
        "hay nada que partir por direccion, y una guardia que "
        "aprueba una tabla vacia aprueba cualquier cosa."
    )

    assert len(D.PLAZOS_MEDIDOS) >= 3, (
        "Con menos de tres plazos no se ve si la curva gira, que "
        "es de donde sale el plazo de salida."
    )

    faltan = [
        (direccion, plazo)
        for direccion in D.DIRECCIONES
        for plazo in D.PLAZOS_MEDIDOS
        if (direccion, plazo) not in D.RENDIMIENTO
    ]

    assert not faltan, (
        "La tabla esta incompleta; faltan estas celdas: "
        + ", ".join(f"{d} a {p} d" for d, p in faltan)
    )

    for (direccion, plazo), (percent, n) in D.RENDIMIENTO.items():

        ficha = D.rendimiento(direccion, plazo)

        assert ficha["available"], (
            f"{direccion} a {plazo} dias esta en la tabla y "
            f"`rendimiento()` dice que no hay dato."
        )

        assert ficha["percent"] == percent, (
            f"{direccion} a {plazo} d: `rendimiento()` devuelve "
            f"{ficha['percent']} y la tabla dice {percent}."
        )

        assert ficha["plazo_dias"] == plazo, (
            f"{direccion}: el plazo publicado ({ficha['plazo_dias']}) "
            f"no es el de la celda ({plazo})."
        )

        assert ficha["n"] == n and n > 0, (
            f"{direccion} a {plazo} dias sale con n={ficha['n']}. "
            f"Un rendimiento sin su `n` es una anecdota, y con "
            f"n=0 no es ni eso."
        )

        assert ficha.get("fuente") and ficha.get("sello"), (
            f"{direccion} a {plazo} dias no dice de donde sale ni "
            f"de cuando es la fuente."
        )

    # Y NO SE INTERPOLA: un plazo que no se midio se dice, no se
    # inventa. La curva ni siquiera es monotona.
    hueco = D.rendimiento("SUBIA", 7)

    assert not hueco["available"], (
        "`rendimiento('SUBIA', 7)` ha devuelto un numero, y los 7 "
        "dias no se midieron. Interpolar en una curva que gira a "
        "los 10 dias es inventarse el lado del pico."
    )

    # LAS TRES DIRECCIONES SON TRES NEGOCIOS DISTINTOS y no se
    # promedian: si se promediaran, el hueco de 19 puntos —que es
    # todo el motivo de este carril— desapareceria.
    sube = D.RENDIMIENTO[("SUBIA", D.PLAZO_DE_SALIDA)][0]

    baja = D.RENDIMIENTO[("BAJABA", D.PLAZO_DE_SALIDA)][0]

    assert sube > baja, (
        f"A {D.PLAZO_DE_SALIDA} dias el que subia rinde {sube} y "
        f"el que bajaba {baja}. Si eso se invierte, este carril "
        f"esta comprando al reves."
    )

    assert abs((sube - baja) - D.HUECO_BRUTO_PP) < 0.5, (
        f"El hueco publicado es {D.HUECO_BRUTO_PP} pp y la tabla "
        f"da {sube - baja:.2f} pp. El numero del informe y el de "
        f"la tabla tienen que ser el mismo."
    )


def test_los_diecinueve_puntos_aguantan_la_prima_del_computer() -> None:
    """
    El hueco neto se calcula, no se afirma.

    LA PREGUNTA INCOMODA DEL ENCARGO: el Computer paga peor por
    los que suben, asi que la prima va EN CONTRA. Esta guardia
    comprueba que la cuenta se hace de verdad —prima del momento
    de VENDER, ponderada por como sale el jugador a los diez
    dias— y que el hueco que se publica es el que sale.
    """

    assert D.PRIMA_DEL_COMPUTER and D.COMO_SALE, (
        "Sin la prima del Computer o sin el reparto de salida no "
        "se puede netear nada."
    )

    # La premisa que va en contra tiene que ser cierta: si el
    # Computer no pagara peor por los que suben, esta cuenta no
    # haria falta y habria que volver a mirarla.
    assert (
        D.PRIMA_DEL_COMPUTER["SUBIA"][0]
        < D.PRIMA_DEL_COMPUTER["BAJABA"][0]
    ), (
        "La prima del Computer ya no es peor para los que suben. "
        "Si eso ha cambiado, esta cuenta sobra y el hueco neto "
        "hay que volver a medirlo."
    )

    for direccion, (percent, n) in D.PRIMA_DEL_COMPUTER.items():
        assert n > 0, (
            f"La prima de {direccion} llega sin `n`: es una "
            f"anecdota, no una prima."
        )

    sube = D.neto_al_salir("SUBIA")

    baja = D.neto_al_salir("BAJABA")

    assert sube["available"] and baja["available"], (
        "No se ha podido netear alguna de las dos direcciones."
    )

    # La prima entra SUMANDO y con el reparto de salida, no con
    # la direccion de entrada: si se cobrara la de entrada, el
    # que sube cobraria +0,03 % y el que baja +1,84 %, y el
    # numero saldria mal por casi un punto.
    assert sube["prima_percent"] > D.PRIMA_DEL_COMPUTER["SUBIA"][0], (
        "La prima del que entra subiendo es la de vender SUBIA a "
        "secas. Tiene que ser la mezcla de como sale a los diez "
        "dias, que es cuando se cobra."
    )

    hueco = sube["neto_percent"] - baja["neto_percent"]

    assert abs(hueco - D.HUECO_NETO_PP) < 0.5, (
        f"El hueco neto publicado es {D.HUECO_NETO_PP} pp y la "
        f"cuenta da {hueco:.2f} pp."
    )

    assert hueco > 0, (
        f"Con la prima descontada el hueco es {hueco:.2f} pp. Si "
        f"se cierra o se da la vuelta, este carril no tiene "
        f"motivo y hay que decirlo, no seguir."
    )


# ============================================================
# 3. EL CARRIL NO COMPRA A LOS QUE BAJAN
# ============================================================

def test_el_carril_no_compra_a_los_que_bajan() -> None:
    """
    Un candidato con direccion DOWN no recibe puja del carril.

    Y EL QUE NO TIENE PRONOSTICO TAMPOCO. Doctrina 24: «SIN
    PRONOSTICO» es una respuesta. No saber si va a subir no es
    saber que va a subir.
    """

    # LA LISTA DEL OJEADOR NO PUEDE LLEGAR VACIA. Con cero
    # candidatos, "ninguno de los que bajan recibe puja" es cierto
    # sin que el filtro exista: es la forma exacta en que una
    # guardia aprueba un filtro desconectado.
    candidatos = [
        {"nombre": "el que sube", "pronostico": {"direction": "UP"}},
        {"nombre": "el que baja", "pronostico": {"direction": "DOWN"}},
        {"nombre": "el plano", "pronostico": {"direction": "FLAT"}},
        {"nombre": "el mudo", "pronostico": {"direction": None}},
        {"nombre": "el ausente", "pronostico": None},
    ]

    assert candidatos, (
        "La lista del ojeador llega vacia: sin candidatos esta "
        "guardia no prueba nada."
    )

    # Y TIENE QUE HABER DE LAS DOS CLASES. Una lista donde nadie
    # sube haria pasar igual a un filtro que dijera que no a todo.
    direcciones = {
        D.direccion_de(c["pronostico"]) for c in candidatos
    }

    assert "SUBIA" in direcciones and "BAJABA" in direcciones, (
        "El montaje no tiene a la vez uno que sube y uno que "
        "baja, asi que no distingue un filtro que funciona de uno "
        "que dice que no a todo."
    )

    veredictos = {
        c["nombre"]: D.puede_comprar(c["pronostico"])
        for c in candidatos
    }

    # EL QUE BAJA, NO.
    assert not veredictos["el que baja"]["available"], (
        "El carril ha dejado pujar por uno que el ojeador dice "
        "que BAJA. A diez dias eso es "
        f"{D.RENDIMIENTO[('BAJABA', D.PLAZO_DE_SALIDA)][0]:+.3f} %."
    )

    assert "BAJABA" in veredictos["el que baja"]["reason"], (
        "El motivo no dice que el ojeador dijera BAJABA, asi que "
        "no se puede saber por que no se pujo."
    )

    # EL PLANO TAMPOCO: 0,000 % a diez dias no paga ni la prima.
    assert not veredictos["el plano"]["available"], (
        "El carril ha dejado pujar por uno PLANO, que a diez dias "
        "rinde 0,000 %."
    )

    # SIN PRONOSTICO, TAMPOCO — y por ese motivo, no por otro.
    for quien in ("el mudo", "el ausente"):

        assert not veredictos[quien]["available"], (
            f"El carril ha dejado pujar por «{quien}», del que no "
            f"hay pronostico."
        )

        assert "SIN PRONOSTICO" in veredictos[quien]["reason"], (
            f"«{quien}» se rechaza, pero el motivo no dice SIN "
            f"PRONOSTICO: se confunde no saber con saber que no."
        )

    # Y EL QUE SUBE, SI. Sin esto, un filtro que rechazara a todo
    # el mundo pasaria esta guardia entera.
    assert veredictos["el que sube"]["available"], (
        "El carril no deja pujar ni por el que el ojeador dice "
        "que SUBE. Entonces no es un filtro: es un tapon."
    )

    assert sum(
        1 for v in veredictos.values() if v["available"]
    ) == 1, (
        "Tiene que pasar exactamente uno de los cinco: el que "
        "sube. Han pasado "
        + str(sum(1 for v in veredictos.values() if v["available"]))
        + "."
    )


def test_el_filtro_no_toca_ningun_umbral() -> None:
    """
    Este filtro decide QUE ENTRA, no CUANTO SE PAGA.

    El encargo lo dice y aqui se ata: el liston y el tope se
    quedan como estan. Si algun dia esto empieza a devolver un
    importe, es que ha dejado de ser un filtro.
    """

    veredicto = D.puede_comprar({"direction": "UP"})

    prohibidas = (
        "bid",
        "max_bid",
        "precio",
        "importe",
        "tope",
        "liston",
        "premium",
        "premium_percent",
    )

    coladas = [c for c in prohibidas if c in veredicto]

    assert not coladas, (
        "El filtro de direccion devuelve " + ", ".join(coladas)
        + ". Eso es poner precio, y el precio lo pone "
        "`regla_de_compra` con los topes de siempre. Este filtro "
        "solo dice si se mira o no se mira."
    )

    assert set(veredicto) == {"available", "direccion", "reason"}, (
        "La forma del veredicto ha cambiado: "
        f"{sorted(veredicto)}. Tiene que seguir siendo "
        "`available`, `direccion` y `reason`, para que no quepa un "
        "importe."
    )


# ============================================================
# 4. EL PLAZO SALE DE DONDE GIRA LA CURVA
# ============================================================

def test_el_plazo_de_salida_sale_de_donde_gira_la_curva() -> None:
    """
    `PLAZO_DE_SALIDA` no es un numero elegido: es el pico.

    Se vuelve a derivar de la tabla en cada vuelta de la verja.
    Si alguien lo mueve a un plazo que la medicion no respalda, o
    si la tabla deja de tener pico, esto muerde.
    """

    derivado = D.comprobar_el_plazo()

    assert derivado["available"], (
        "No se ha podido derivar el plazo de salida: la tabla "
        "llega vacia."
    )

    assert derivado["cuadra_con_el_declarado"], (
        f"`PLAZO_DE_SALIDA` dice {D.PLAZO_DE_SALIDA} dias y la "
        f"tabla tiene el pico en {derivado['plazo']} "
        f"({derivado['percent']:+.3f} %). El plazo se lee de la "
        f"medicion, no se escribe."
    )

    assert derivado["devuelve_despues"], (
        "Despues del pico la curva ya no devuelve, asi que ese "
        "plazo no es una saturacion: es solo el ultimo que se "
        "midio. Hay que medir mas lejos antes de llamarlo plazo "
        "de salida."
    )

    assert derivado["siguientes"], (
        "No hay ningun plazo medido DESPUES del pico, asi que no "
        "se puede saber si la curva gira. Un maximo en el borde "
        "de la ventana no es un pico."
    )


# ============================================================
# 5. ESTO SIGUE APAGADO
# ============================================================

def test_esto_sigue_apagado() -> None:
    """
    `ENCENDIDO = False`. El encargo lo pide y la verja lo ata.
    """

    assert D.ENCENDIDO is False, (
        "`la_direccion.ENCENDIDO` ya no es False. Este filtro se "
        "construyo apagado a proposito: enciende una via que "
        "compra, y eso lo decide el dueño."
    )

    assert D.esta_encendido() is False, (
        "`esta_encendido()` no dice lo mismo que `ENCENDIDO`."
    )


# ============================================================
# EL ORDEN NO QUITA PUJAS
# ============================================================

def test_el_orden_no_quita_pujas() -> None:
    """
    Reordenar por direccion devuelve LOS MISMOS candidatos.

    POR QUE ES ESTA LA PROPIEDAD Y NO OTRA (doctrina 51)

        Ayer se midio que el filtro por direccion habria bajado
        nuestras pujas de 37 a 18, y el problema medido es que
        aparecemos poco. Asi que lo unico que hace falta demostrar
        de este reorden es que NO ES UN FILTRO DISFRAZADO.

        No se cuenta la sintaxis —«llama a `sorted`»—: se mide la
        propiedad. Entran N, salen N, y son los mismos N.

    SE PRUEBA ENCENDIDO A PROPOSITO. Apagado devuelve la entrada
    tal cual y cualquier cosa pasaria; lo que hay que atar es el
    comportamiento del dia que se encienda.
    """

    candidatos = [
        {"id": 1, "decision": "BID", "vispera": "UP", "cambio": 0.4},
        {"id": 2, "decision": "BID", "vispera": "DOWN", "cambio": -2.0},
        {"id": 3, "decision": "BID", "vispera": "UP", "cambio": 5.1},
        {"id": 4, "decision": "NO_BID", "vispera": None, "cambio": None},
        {"id": 5, "decision": "BID", "vispera": "FLAT", "cambio": 0.0},
        {"id": 6, "decision": "BID", "vispera": "UP", "cambio": 2.2},
    ]

    # CON LAS MANOS VACIAS NO SE PASA.
    assert candidatos, (
        "La lista de candidatos llega vacia: reordenar cero "
        "elementos no prueba que no se pierda ninguno."
    )

    # Y TIENE QUE HABER DE LOS DOS LADOS, o un reorden que
    # mandara a todo el mundo al mismo sitio pasaria igual.
    direcciones = {c["vispera"] for c in candidatos}

    assert "UP" in direcciones and "DOWN" in direcciones, (
        "El montaje no tiene a la vez uno que sube y uno que baja: "
        "asi no se distingue un reorden de una lista que ya venia "
        "ordenada."
    )

    pronosticos = {
        c["id"]: ({"direction": c["vispera"]} if c["vispera"] else None)
        for c in candidatos
    }

    cambios = {c["id"]: c["cambio"] for c in candidatos}

    encendido_antes = D.ORDEN_ENCENDIDO

    try:
        D.ORDEN_ENCENDIDO = True

        resultado = D.ordenar(
            candidatos, pronosticos, cambios, clave=lambda f: f["id"]
        )

        assert resultado["available"], (
            f"El reorden no se ha aplicado: {resultado['reason']}"
        )

        salida = resultado["filas"]

        # 1. EL MISMO NUMERO.
        assert len(salida) == len(candidatos), (
            f"Entraron {len(candidatos)} candidatos y salieron "
            f"{len(salida)}. Un orden que cambia la cuenta es un "
            f"filtro disfrazado, y eso no entra."
        )

        # 2. LOS MISMOS, uno a uno.
        assert sorted(f["id"] for f in salida) == sorted(
            c["id"] for c in candidatos
        ), (
            "La lista de salida no lleva los mismos candidatos que "
            "la de entrada."
        )

        # 3. Y LAS MISMAS PUJAS. Es el numero del encargo: si
        #    salen menos BID de los que entraron, se ha caido una.
        pujas_antes = sum(
            1 for c in candidatos if c["decision"] == "BID"
        )

        pujas_despues = sum(
            1 for f in salida if f["decision"] == "BID"
        )

        assert pujas_despues == pujas_antes, (
            f"Entraron {pujas_antes} pujas y salieron "
            f"{pujas_despues}. El orden no puede tocar ni una."
        )

        # 4. Y ORDENA DE VERDAD: el que subio mas fuerte va
        #    delante, o esto no sirve para nada.
        suben = [
            f["id"] for f in salida if f["vispera"] == "UP"
        ]

        assert suben == [3, 6, 1], (
            f"Los que suben salen en el orden {suben} y tenian que "
            f"salir [3, 6, 1] —de mas fuerte a mas flojo: +5,1 %, "
            f"+2,2 %, +0,4 %—."
        )

        assert salida[0]["id"] == 3, (
            "Delante del todo tiene que ir el que mas subio la "
            "vispera."
        )

        # 5. EL QUE NO TIENE PRONOSTICO NO SE CASTIGA MAS QUE EL
        #    QUE BAJA: los dos van al mismo escalon. Castigar al
        #    que no tiene dato es el primer paso para quitarlo.
        assert D.clave_de_orden(None, None)[0] == D.clave_de_orden(
            {"direction": "DOWN"}, None
        )[0], (
            "El que no tiene pronostico y el que baja tienen que "
            "ir al mismo escalon. No saber no es una falta."
        )

    finally:
        D.ORDEN_ENCENDIDO = encendido_antes


def test_el_orden_sigue_apagado() -> None:
    """
    `ORDEN_ENCENDIDO = False`, y apagado devuelve la entrada tal
    cual — no una copia reordenada «por si acaso».
    """

    assert D.ORDEN_ENCENDIDO is False, (
        "`la_direccion.ORDEN_ENCENDIDO` ya no es False. El orden "
        "se construyo apagado: lo enciende el dueño cuando vea la "
        "tabla."
    )

    filas = [{"id": 1}, {"id": 2}, {"id": 3}]

    resultado = D.ordenar(
        filas,
        {1: {"direction": "DOWN"}, 3: {"direction": "UP"}},
        {3: 9.0},
        clave=lambda f: f["id"],
    )

    assert [f["id"] for f in resultado["filas"]] == [1, 2, 3], (
        "Apagado, el orden ha movido las filas. Un interruptor "
        "apagado que cambia algo no es un interruptor."
    )


def main() -> None:

    pruebas = [
        valor
        for nombre, valor in sorted(globals().items())
        if nombre.startswith("test_") and callable(valor)
    ]

    for prueba in pruebas:
        prueba()
        print(f"  OK  {prueba.__name__}")

    print()
    print(f"{len(pruebas)} guardias de LA DIRECCION, todas en verde.")


if __name__ == "__main__":
    main()
