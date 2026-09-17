"""
Las guardias de EMPEZAR A ANOTAR.

QUE SE PRUEBA AQUI

    1. Si llega la ventana, el once se anota — pase lo que pase
       en esa vuelta.
    2. La jornada de referencia es ANTERIOR en el tiempo, y el
       tiempo que manda para restar acumulados es CUANDO SE
       MIRO, no cuando se jugo.
    3. Con cero jornadas fiables no se publica una media.

NINGUNA LEE ESTADO DE PRODUCCION, SALE A LA RED, MIRA EL RELOJ
DEL SISTEMA NI ESCRIBE EN LOS LIBROS. Todas trabajan sobre
montajes en memoria, y la hora entra por la puerta (doctrina 50):
ninguna llama a `datetime.now()`.

Y NINGUNA PASA CON LAS MANOS VACIAS (doctrina 24): si la lista de
jornadas llega vacia, o el resumen llega vacio, la guardia FALLA.
Comprobar una propiedad sobre cero elementos es la forma exacta
en que un detector roto parece verde.
"""

from __future__ import annotations

import sys

from datetime import datetime, timedelta, timezone
from pathlib import Path


RAIZ = Path(__file__).resolve().parents[2]

sys.path.insert(0, str(RAIZ))

from src.analysis.el_once_que_jugo import (          # noqa: E402
    SON_ONCE,
    hay_que_anotar,
)

from src.analysis.marcador import (                  # noqa: E402
    orden_en_el_tiempo,
)


# La ventana de mañana, del calendario de LaLiga que guarda
# el motor de calendario, jornada 7. Se copian aqui como NUMEROS, no se leen del disco:
# una guardia que abre el calendario de produccion deja de ser
# determinista el dia que el calendario cambie.
PRIMER_PARTIDO = "2026-09-18T21:00:00+02:00"

VENTANA_DESDE = "2026-09-18T19:30:00+02:00"

RONDA = 5125


def _once(cuantos=SON_ONCE) -> dict:
    """Un once de juguete con `cuantos` jugadores.

    La forma es la que devuelve `once_del_dueno`: un diccionario
    con `players`, no una lista. Si esto se escribiera como lista
    la guardia pasaria por el camino del error y no probaria nada.
    """

    return {
        "players": [
            {"id": 1000 + i, "name": f"jugador {i}"}
            for i in range(cuantos)
        ]
    }


def _momento(texto):
    return datetime.fromisoformat(texto)


# ============================================================
# 1. LA VENTANA NO SE PIERDE
# ============================================================

def test_la_ventana_de_anotar_no_se_pierde() -> None:
    """
    Dentro de la ventana, el once se anota — haga lo que haga la
    vuelta.

    POR QUE ESTO NO ES OBVIO

        Cada vuelta elige UNA accion por prioridad y tiene un
        presupuesto de escrituras contra Biwenger. Si anotar el
        once compitiera por ese presupuesto, una vuelta ocupada
        en aceptar una oferta se comeria el turno de anotar — y
        el turno de anotar NO VUELVE: la jornada se juega una
        vez.

        MEDIDO: no compite. `anotar_el_once` vive en el camino de
        telemetria, es observador puro y escribe SU PROPIO
        fichero. Esta guardia ata esa propiedad: la decision de
        anotar no mira ni una sola cosa de lo que la vuelta este
        haciendo.

    LA FORMA DE PROBARLO es que `hay_que_anotar` no acepta ningun
    argumento sobre acciones, presupuesto ni prioridad: solo la
    jornada, el once, las dos horas y la hora de ahora. Si algun
    dia alguien le pasa el estado de la vuelta, esto muerde.
    """

    # LA LISTA DE JORNADAS NO PUEDE LLEGAR VACIA.
    jornadas = [RONDA]

    assert jornadas, (
        "La lista de jornadas llega vacia: sin una jornada que "
        "anotar, «el once se anota» es cierto sin que nada "
        "funcione."
    )

    apertura = _momento(VENTANA_DESDE)

    arranque = _momento(PRIMER_PARTIDO)

    assert apertura < arranque, (
        "La ventana abre despues del primer partido: el montaje "
        "no representa ninguna ventana real."
    )

    # DENTRO DE LA VENTANA: se anota.
    dentro = apertura + timedelta(minutes=37)

    veredicto = hay_que_anotar(
        round_id=RONDA,
        once=_once(),
        primer_partido=PRIMER_PARTIDO,
        ahora=dentro.isoformat(),
        desde=VENTANA_DESDE,
        ruta=Path("no_existe_a_proposito.jsonl"),
    )

    assert veredicto["anota"] is True, (
        f"Estando DENTRO de la ventana ({dentro.isoformat()}, "
        f"entre {VENTANA_DESDE} y {PRIMER_PARTIDO}) no se anota: "
        f"{veredicto['reason']}"
    )

    # ANTES DE LA VENTANA: no, y por ese motivo.
    antes = apertura - timedelta(minutes=1)

    previo = hay_que_anotar(
        round_id=RONDA,
        once=_once(),
        primer_partido=PRIMER_PARTIDO,
        ahora=antes.isoformat(),
        desde=VENTANA_DESDE,
        ruta=Path("no_existe_a_proposito.jsonl"),
    )

    assert previo["anota"] is False, (
        "Un minuto ANTES de la ventana ya se anota: el once se "
        "congelaria cuando el dueño todavia puede cambiarlo."
    )

    # DESPUES DEL PRIMER PARTIDO: tampoco, y este es el limite
    # que hace que el turno se pueda perder.
    tarde = arranque + timedelta(minutes=1)

    tardio = hay_que_anotar(
        round_id=RONDA,
        once=_once(),
        primer_partido=PRIMER_PARTIDO,
        ahora=tarde.isoformat(),
        desde=VENTANA_DESDE,
        ruta=Path("no_existe_a_proposito.jsonl"),
    )

    assert tardio["anota"] is False, (
        "Se anota DESPUES del primer partido. Lo que haya puesto "
        "entonces no es necesariamente lo que jugo, y anotarlo "
        "daria una nota falsa que parece buena."
    )

    # Y LA DECISION NO DEPENDE DE LO QUE HAGA LA VUELTA.
    #
    #     Se comprueba sobre la firma: si `hay_que_anotar` empezara
    #     a recibir el plan de la vuelta, el presupuesto de
    #     escrituras o la accion elegida, anotar pasaria a
    #     competir y el turno podria perderse.
    import inspect

    parametros = set(inspect.signature(hay_que_anotar).parameters)

    prohibidos = {
        "plan",
        "accion",
        "action",
        "presupuesto",
        "budget",
        "escrituras",
        "writes",
        "prioridad",
        "priority",
        "decision",
    }

    coladas = parametros & prohibidos

    assert not coladas, (
        f"`hay_que_anotar` ha empezado a recibir {sorted(coladas)}. "
        f"Anotar el once no puede depender de lo que la vuelta "
        f"este haciendo: la jornada se juega una vez y el turno "
        f"no vuelve."
    )


def test_un_once_a_medias_no_se_anota() -> None:
    """
    Diez nombres no son un once (regla 24).

    Existe porque es la puerta que mas facil falla mañana: si la
    foto llega con el once incompleto, se prefiere no anotar a
    dejar una entrada que parece buena y da una nota coja.
    """

    dentro = (_momento(VENTANA_DESDE) + timedelta(minutes=30)).isoformat()

    for cuantos in (0, 10, 12):

        veredicto = hay_que_anotar(
            round_id=RONDA,
            once=_once(cuantos),
            primer_partido=PRIMER_PARTIDO,
            ahora=dentro,
            desde=VENTANA_DESDE,
            ruta=Path("no_existe_a_proposito.jsonl"),
        )

        assert veredicto["anota"] is False, (
            f"Se ha anotado un once de {cuantos} jugadores."
        )

    completo = hay_que_anotar(
        round_id=RONDA,
        once=_once(SON_ONCE),
        primer_partido=PRIMER_PARTIDO,
        ahora=dentro,
        desde=VENTANA_DESDE,
        ruta=Path("no_existe_a_proposito.jsonl"),
    )

    assert completo["anota"] is True, (
        "Con los once no se anota: entonces la puerta del numero "
        "de jugadores esta cerrada para todos y no anotaria nunca."
    )


# ============================================================
# 2. LA REFERENCIA ES ANTERIOR EN EL TIEMPO
# ============================================================

def test_la_referencia_es_anterior_en_el_tiempo() -> None:
    """
    La jornada de referencia va SIEMPRE antes que la medida, por
    FECHA y no por numero.

    EL FALLO QUE CAZA (14/09/2026)

        Este motor ordenaba por `round_id` y daba por hecho que
        ese orden era el del calendario. Es falso y esta liga lo
        demuestra sola: la jornada 6 viene partida en dos ids
        porque uno de sus partidos se adelanto diez dias.

            4903  Jornada 5             10 partidos  13-14/09
            4904  Jornada 6              1 partido      03/09

        Por id, 4903 queda como previa de 4904 — pero 4904 se
        jugo ANTES. La resta de acumulados va al reves y salen
        puntos negativos: el `mejor_puntos: -55` que llego a
        aparecer en pantalla.

    EL MONTAJE LO PONE DIFICIL A PROPOSITO: los `round_id` van en
    un orden y las fechas en otro. Si alguien vuelve a ordenar
    por numero, esta guardia lo dice.
    """

    # DOS LISTAS, Y NINGUNA VACIA.
    jornadas = [
        {"round_id": 4903, "visto": "2026-09-16T07:19:10+00:00"},
        {"round_id": 4904, "visto": "2026-09-04T20:34:49+00:00"},
        {"round_id": 4899, "visto": "2026-08-20T20:55:51+00:00"},
    ]

    # El numero mas alto se jugo EN MEDIO, y el mas bajo primero.
    calendario = {
        4899: {"primer_partido": "2026-08-19T19:00:00+00:00"},
        4904: {"primer_partido": "2026-09-03T19:00:00+00:00"},
        4903: {"primer_partido": "2026-09-13T19:00:00+00:00"},
    }

    assert jornadas and calendario, (
        "Alguna de las dos listas llega vacia: sin jornadas y sin "
        "calendario no hay ningun orden que comprobar."
    )

    # Y TIENE QUE SER UN MONTAJE QUE DISTINGA: si el orden por
    # numero y el orden por fecha coincidieran, la guardia
    # pasaria con las dos reglas y no probaria nada.
    por_numero = sorted(j["round_id"] for j in jornadas)

    por_fecha = [
        r
        for r, _ in sorted(
            calendario.items(),
            key=lambda par: par[1]["primer_partido"],
        )
    ]

    assert por_numero != por_fecha, (
        f"El montaje da el mismo orden por numero {por_numero} y "
        f"por fecha {por_fecha}: asi no distingue una regla de la "
        f"otra."
    )

    colocadas = orden_en_el_tiempo(jornadas, calendario)

    ordenadas = colocadas["ordenadas"]

    assert len(ordenadas) == len(jornadas), (
        f"Se han colocado {len(ordenadas)} de {len(jornadas)} "
        f"jornadas; las demas se han caido sin decirlo."
    )

    salida = [item["round_id"] for item in ordenadas]

    # 1. SE ORDENA POR FECHA.
    assert salida == por_fecha, (
        f"El orden es {salida} y por fecha tenia que ser "
        f"{por_fecha}."
    )

    # 2. Y NO POR NUMERO.
    assert salida != por_numero, (
        f"El orden {salida} es el de los `round_id`. Ordenar por "
        f"numero es lo que puso a 4903 de previa de 4904 y dio "
        f"puntos negativos."
    )

    # 3. CADA UNA VA DESPUES DE SU REFERENCIA, en el tiempo.
    for antes, despues in zip(ordenadas, ordenadas[1:]):

        assert antes["momento"] < despues["momento"], (
            f"La jornada {despues['round_id']} tiene como "
            f"referencia a {antes['round_id']}, que se jugo "
            f"DESPUES ({antes['momento']} vs "
            f"{despues['momento']}). La resta de acumulados iria "
            f"al reves."
        )

    # 4. Y UNA SIN HORA NO SE COLOCA A OJO.
    cojas = jornadas + [{"round_id": 4900, "visto": "2026-08-25T00:00:00+00:00"}]

    sin_calendario = orden_en_el_tiempo(cojas, calendario)

    assert len(sin_calendario["sin_hora"]) == 1, (
        "Una jornada sin hora de partido se ha colocado igual. "
        "Sin esa hora no se sabe que va antes, y la resta daria "
        "un numero inventado."
    )

    assert sin_calendario["sin_hora"][0]["round_id"] == 4900, (
        "La que se ha dejado fuera no es la que no tenia hora."
    )


# ============================================================
# 3. SIN JORNADAS FIABLES NO HAY MEDIA
# ============================================================

def test_una_jornada_que_no_midio_la_liga_no_entra_en_la_media() -> None:
    """
    Un cero que nadie midio no es un cero.

    EL NUMERO QUE MENTIA (medido el 17/09/2026)

        jornadas_fiables: 0 · jornadas_descartadas: 3
        diferencia_media: 1.5

        El 1,5 era la media de 0,0, 0,0 y 4,5:

            4903  media_rivales 0,0   DIEZ partidos, nuestro once
                                      sumo 60 puntos
            4904  media_rivales 0,0
            4899  media_rivales 24,5  Biwenger nos dio 29

        Que los ocho managers de la liga puntuen EXACTAMENTE
        cero no pasa. Esos dos ceros no son jornadas malas: son
        restas que no midieron nada, y hundian un +4,5 real
        hasta 1,5.

    LO QUE NO SE TOCA, Y POR QUE

        El +4,5 SI es un hecho —sale de los puntos oficiales, no
        de nuestra reconstruccion— y sigue contando aunque la
        jornada no cuadre. Eso lleva atado desde el 21/08 en
        `test_contra_la_liga_manda_el_dato_oficial`, y esta
        guardia NO lo contradice: lo que se excluye no es «la
        jornada que no cuadra» sino «la jornada que no midio la
        liga».

    Y LA MEDIA VIAJA CON SU `n` (doctrina 55): un promedio sobre
    una jornada no es lo mismo que sobre diez.
    """

    from src.analysis import marcador as M

    from src.analysis.test_marcador_v1 import (
        CALENDARIO,
        escribir_ledger,
        jornada,
        ledger_temporal,
        sin_puntos,
    )

    assert CALENDARIO, (
        "El calendario de montaje llega vacio: sin el no se "
        "coloca ninguna jornada y no se mide nada."
    )

    # El calendario de al lado solo llega a la jornada 2.
    calendario = {
        **CALENDARIO,
        4901: {
            "round_id": 4901, "nombre": "Jornada 3", "numero": 3,
            "primer_partido": "2026-08-27T21:00:00+00:00",
            "fuente": "CALENDARIO_DE_LALIGA",
        },
        4902: {
            "round_id": 4902, "nombre": "Jornada 4", "numero": 4,
            "primer_partido": "2026-09-03T21:00:00+00:00",
            "fuente": "CALENDARIO_DE_LALIGA",
        },
    }

    once = [100, 200, 201, 202, 203, 300, 301, 302, 303, 400, 401]

    with ledger_temporal() as fichero:

        t1, t2, t3 = sin_puntos(), sin_puntos(), sin_puntos()

        t1[300], t2[300], t3[300] = 7, 14, 21

        # DOS QUE MIDEN: la clasificacion avanza entre una y otra.
        primera = jornada(
            4899, t1, once,
            puntos_biwenger=29, puntos_rivales=(10, 20, 30),
        )

        segunda = jornada(
            4900, t2, once,
            puntos_biwenger=58, puntos_rivales=(20, 40, 60),
        )

        # LA QUE NO MIDE NADA, y es el caso real de produccion:
        # su clasificacion es IDENTICA a la anterior, asi que el
        # reparto oficial sale entero a cero. No es una foto a
        # medias —los jugadores tienen puntos y los managers
        # tambien—: es una resta que no encontro nada.
        tercera = jornada(
            4901, t3, once,
            puntos_biwenger=58, puntos_rivales=(20, 40, 60),
        )

        # La ultima solo cierra a la anterior.
        cierre = jornada(
            4902, t3, once,
            puntos_biwenger=99, puntos_rivales=(30, 50, 70),
        )

        escribir_ledger(
            fichero, [primera, segunda, tercera, cierre]
        )

        datos = M.marcador(calendario)

    resumen = datos["resumen"]

    assert resumen, "El resumen llega vacio."

    filas = {f["round_id"]: f for f in datos["jornadas"]}

    assert filas, "El marcador no ha devuelto ninguna jornada."

    medibles = [f for f in datos["jornadas"] if f.get("medible")]

    assert len(medibles) >= 3, (
        f"Solo hay {len(medibles)} jornada(s) medible(s): el "
        f"montaje no tiene a la vez las que miden y la que no."
    )

    # 1. LAS QUE MIDEN, MARCADAS.
    for ronda in (4899, 4900):
        assert filas[ronda]["liga_medida"] is True, (
            f"La jornada {ronda}, con reparto oficial distinto de "
            f"cero, sale como que no midio la liga."
        )

    # 2. LA QUE NO, TAMBIEN — y es medible, que es lo que la
    #    hacia colarse.
    assert filas[4901]["medible"] is True, (
        "El montaje ya no reproduce el caso: la jornada del "
        "reparto a cero se cae por otro motivo antes de llegar a "
        "la media, asi que no prueba nada."
    )

    assert filas[4901]["liga_medida"] is False, (
        "Una jornada cuya clasificacion es identica a la anterior "
        "—reparto oficial entero a cero— se da por medida. Eso no "
        "es una jornada mala: es una resta que no encontro nada."
    )

    # 3. LA MEDIA SOLO CUENTA LAS QUE MIDIERON.
    assert resumen.get("diferencia_media") == 9.0, (
        f"La media es {resumen.get('diferencia_media')} y tenia que "
        f"ser 9.0. Si sale 6.0 es que el cero de la que no midio "
        f"ha entrado y ha hundido las otras dos."
    )

    # 4. CON SU `n`.
    assert resumen.get("diferencia_media_n") == 2, (
        f"La media dice n={resumen.get('diferencia_media_n')} y "
        f"tenia que decir 2. Un promedio sin su `n` no distingue "
        f"dos jornadas de diez."
    )

    # 5. Y EL HECHO NO SE PIERDE: la diferencia sigue publicada
    #    en su jornada aunque no cuadre, que es lo que defiende
    #    `test_contra_la_liga_manda_el_dato_oficial` desde el
    #    21/08. Esta guardia no lo contradice.
    assert filas[4899]["diferencia_liga"] == 9.0, (
        "La diferencia con la liga ha dejado de publicarse en su "
        "jornada. El hecho se conserva; lo que se quita es el "
        "promedio que lo mezclaba con ceros que no midieron nada."
    )


def test_el_veredicto_dice_que_no_hay_media() -> None:
    """
    Cuando no hay nota, el panel lo dice con palabras.

    Un hueco sin explicacion se lee como un fallo de la pantalla;
    una frase se lee como lo que es.
    """

    from src.analysis import marcador as M

    import inspect

    fuente = inspect.getsource(M.marcador)

    assert fuente.strip(), "El codigo del resumen llega vacio."

    assert "ni diferencia con la liga" in fuente, (
        "El veredicto de «ninguna cuadra» ya no dice que las dos "
        "medias se quedan sin valor."
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
    print(f"{len(pruebas)} guardias de EMPEZAR A ANOTAR, todas en verde.")


if __name__ == "__main__":
    main()
