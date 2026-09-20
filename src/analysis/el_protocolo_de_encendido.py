"""
El protocolo de encendido: un interruptor por vuelta, nunca dos.

POR QUE UNO SOLO

    Cambiar dos cosas a la vez es no saber cual movio que. Se
    dijo el 15/09 con el liston del 3 % y sigue valiendo: si se
    encienden la regla del deficit y el cupo la misma manana y el
    lunes aparecemos en cuatro subastas mas, no hay forma de
    saber cual lo hizo — ni cual apagar si sale mal.

    Este modulo NO enciende nada. Guarda las fichas y avisa
    cuando hay mas de uno nuevo puesto.

LA FICHA, Y POR QUE ESOS CINCO CAMPOS

    `que_mirar_antes` son los campos EXACTOS de la foto, con su
    nombre en el JSON. Sin eso, «mira la solvencia» es una
    invitacion a mirar otra cosa la semana que viene.

    `que_deberia_pasar` se escribe ANTES de encender. Es la
    parte que mas ha servido: cuando pasa otra cosa se ve, en vez
    de racionalizarla a posteriori. Este mes esa prediccion ha
    desmentido al dueno mas veces que al reves.

    `senal_de_apagarlo` lleva su plazo. Un interruptor sin
    criterio de vuelta atras no es un experimento: es una
    apuesta.

EL PASO 0, Y VA ANTES DE TOCAR EL YAML  (20/09/2026)

    CORRER LA VERJA ENTERA CON EL INTERRUPTOR PUESTO. Si no da
    el mismo verde que sin el, NO SE ENCIENDE.

        $env:BORDALAS_LO_QUE_SEA = "1"; python scripts/run_validation_gate.py > verja.txt 2>&1; $c = $LASTEXITCODE; Remove-Item Env:/BORDALAS_LO_QUE_SEA; "exit $c"

    Un mandato, un paso: pone el interruptor, corre la verja a
    FICHERO -doctrina 52: en una tuberia el codigo de salida es
    el del ultimo mandato-, guarda el codigo, quita el
    interruptor y lo enseña.

    POR QUE EXISTE ESTE PASO

        La noche del 20/09 se encendio
        `BORDALAS_OBJETIVOS_EL_CATALOGO` en el `env` del
        workflow. `test_la_lista_de_objetivos_v1` comprobaba que
        ese interruptor NO estuviese puesto, se puso roja, el
        paso «Validate optimized production cycle» devolvio 1 y
        NO HUBO CICLO. Dos vueltas perdidas.

        Las cuatro señales de abortar que habia escritas eran
        todas sobre el ciclo. Ninguna decia «la verja se pone
        roja y el ciclo no arranca», que es la que hacia falta.

        Las guardias ya no dependen del entorno —se arreglaron
        seis— y hay una que lo vigila,
        `test_ninguna_guardia_depende_del_entorno_v1`. Pero el
        paso 0 se queda: la guardia protege de la forma conocida
        del fallo, y el paso 0 protege de la que no conocemos.

EL ORDEN

    1. COBRAR_EN_DEFICIT     el que impide la jornada en blanco
    2. CUPO_POR_ENVIOS       el que nos hace aparecer mas
    3. REJA_CON_TOLERANCIA   riesgo ya medido: 0 de 27 cambian
    4. TOPE_DEL_ONCE         condicionado, y va el ultimo

    Va primero el que evita la perdida mas grande —una jornada en
    blanco son ~50 puntos de golpe— y ultimo el que solo cambia
    cuanto se paga por una puja que igual no se gana.

    Y LOS CUATRO DE LA COLA DEL 20/09, detras de esos:

    5. SIN_REFERENCIA_ESCALA  solo cambia lo que se VE
    6. CESTA_SOLO_EL_SUELO    para operaciones: mueve dinero
    7. JORNADAS_POR_SU_FECHA  arregla el marcador, no el juego
    8. OBJETIVOS_EL_CATALOGO  el que tumbo el ciclo; va el ultimo

    El criterio es el mismo de arriba, aplicado a los nuevos:
    primero los que cambian lo que se MIRA y despues los que
    cambian lo que se HACE. Y el octavo va ultimo por una razon
    que no es tecnica: es el unico que ya rompio una vuelta, y
    encenderlo el ultimo es encenderlo cuando ya se ha visto que
    el paso 0 funciona con los otros siete.
"""

from __future__ import annotations

import os


# ============================================================
# LOS CUATRO, EN ORDEN, CON SU FICHA
# ============================================================

PROTOCOLO = (
    {
        "orden": 1,
        "interruptor": "BORDALAS_COBRAR_EN_DEFICIT",

        "que_cambia": (
            "Con el saldo en rojo, Pepe acepta la oferta de mejor "
            "prima de un jugador que NO esta en el once, y solo "
            "hasta volver a positivo."
        ),

        "que_mirar_antes": (
            "solvency_clock.deficit",
            "solvency_clock.state",
            "offers.<n> y su premium_percent",
            "sale_order.queue (quien esta fuera del once)",
            "acquisition.budgets (si sale SIN_CAPACIDAD)",
        ),

        "que_deberia_pasar": (
            "Con deficit vivo y ofertas de fuera del once sobre "
            "la mesa, en la PRIMERA vuelta se acepta UNA —la de "
            "mejor prima— y el deficit baja por su importe. Si "
            "las ofertas vivas no llegan a taparlo, se aceptan "
            "todas las de fuera del once y el deficit baja sin "
            "cerrarse: el motivo lo dice con lo que falta. "
            "`acquisition.budgets` deja de salir SIN_CAPACIDAD en "
            "cuanto el saldo vuelve a positivo."
        ),

        "senal_de_apagarlo": (
            "Que se acepte una oferta de alguien que ESTA en el "
            "once: eso no puede pasar nunca y se apaga en la "
            "misma vuelta. O que se acepten mas de las necesarias "
            "para volver a positivo: se apaga si pasa dos veces. "
            "O que el deficit no baje tras una aceptacion, en "
            "dos vueltas seguidas."
        ),

        "condicion_de_encendido": (
            "ENCENDERLO DESPUES DE COBRAR A MANO POR LA MANANA Y "
            "VOLVER A POSITIVO. Con cinco millones de deficit "
            "encima, su primera actuacion seria la mas grande de "
            "su vida — y la regla acepta HASTA cubrir, asi que "
            "soltaria todo lo de fuera del once de una vez. Se "
            "enciende en calma, no en la tormenta."
        ),
    },
    {
        "orden": 2,
        "interruptor": "BORDALAS_CUPO_POR_ENVIOS",

        "que_cambia": (
            "El cupo del reset pasa a contar escrituras ENVIADAS "
            "en vez de viajes ganados, con un tope por familia: "
            "renovar 12, puja 3, publicar 4."
        ),

        "que_mirar_antes": (
            "bid_outcomes.<n> (pujas puestas)",
            "acquisition.with_live_bid y live_bid_total",
            "listings.listing_count",
            "subasta.blocked_by",
            "data/trading/libro_del_carril.jsonl (escrituras del dia)",
        ),

        "que_deberia_pasar": (
            "En condiciones normales NO CAMBIA NADA: la demanda "
            "legitima medida fue 2 pujas y 1 publicacion por "
            "reset, muy por debajo de los topes. Lo que tiene que "
            "verse es el motivo nuevo cuando algo se frene: "
            "«van N de un cupo de M». Si en una semana no aparece "
            "ni un freno, es que los topes estan bien puestos, no "
            "que no funcione."
        ),

        "senal_de_apagarlo": (
            "Que frene una escritura LEGITIMA —distinta de las ya "
            "hechas ese reset— dos veces en la misma semana: "
            "querria decir que el tope se quedo corto, y el "
            "10/09 hubo NUEVE renovaciones buenas en un reset. O "
            "que aparezca `CUPO_SIN_SABER` mas de una vez al dia: "
            "eso no es el cupo, es que el libro no se puede leer."
        ),

        "condicion_de_encendido": (
            "Antes conviene tener `BORDALAS_NO_REPETIR_LA_ESCRITURA` "
            "puesto: el cupo limita VOLUMEN y la repeticion es "
            "IDENTIDAD (doctrina 93). Con las repeticiones aun "
            "vivas, el cupo se las come y deja fuera el trabajo "
            "bueno."
        ),
    },
    {
        "orden": 3,
        "interruptor": "BORDALAS_REJA_CON_TOLERANCIA",

        "que_cambia": (
            "La caja reconstruida de los ocho deja de contar dos "
            "veces un movimiento que Biwenger reemite con otro "
            "`event_id` dentro de una hora."
        ),

        "que_mirar_antes": (
            "marcador (la caja de cada manager)",
            "losRivales / rival_squads (balance y amenaza)",
            "acquisition.rival_market",
        ),

        "que_deberia_pasar": (
            "Nuestra caja reconstruida pasa de -35.566 a -455.766 "
            "y CUADRA con la real al euro. Luismi_Haz baja "
            "13.345.400 y Prinzipote 2.213.400; los otros cinco no "
            "se mueven un euro. Ninguna puja cambia: de las 27 del "
            "libro, ninguna lleva `seller_user_id`."
        ),

        "senal_de_apagarlo": (
            "Que se mueva la caja de alguno de los CINCO que no "
            "deberian moverse: querria decir que la ventana de "
            "3.600 s se esta comiendo repeticiones legitimas. Se "
            "apaga en la misma vuelta. Plazo de comprobacion: una "
            "vuelta, porque el efecto es inmediato y visible."
        ),

        "condicion_de_encendido": (
            "Requiere que la rama de la reja este en `main`. Ya "
            "esta mergeada; solo falta que el valor llegue al "
            "workflow."
        ),
    },
    {
        "orden": 4,
        "interruptor": "BORDALAS_TOPE_DEL_ONCE",

        "que_cambia": (
            "La via del once pasa de NO TENER TOPE de prima a "
            "tener uno. Hoy Pepe puja donde cae el optimo de EV "
            "—+5,29 % por Chust—; con el tope no pasaria de su "
            "valor."
        ),

        "que_mirar_antes": (
            "acquisition.premium_model.curve y sus rungs",
            "acquisition.premium_model.samples",
            "acquisition.targets[].bid y bid_sin_tope",
            "acquisition.techos",
        ),

        "que_deberia_pasar": (
            "Las pujas del once bajan del +5,29 % al peldano mas "
            "alto que quepa bajo el tope. CUIDADO: con la curva "
            "del 19/09 ese peldano era +0,52 %; con la del 20/09 "
            "es +0,31 %. La puja no aterriza en el tope, aterriza "
            "en el peldano de debajo, y cual sea cambia de un dia "
            "para otro (doctrina 94)."
        ),

        "senal_de_apagarlo": (
            "Que perdamos dos subastas seguidas por menos de lo "
            "que el tope nos impidio pujar. Eso se mide: la puja "
            "ganadora esta en el tablon y `bid_sin_tope` dice lo "
            "que habriamos ofrecido."
        ),

        "condicion_de_encendido": (
            "NO SE ENCIENDE hasta que este decidida la tabla "
            "marginal del peldano — encargo aparte. Un umbral fijo "
            "contra una rejilla que se mueve cada dia es una "
            "loteria (doctrina 94): el salto de P(ganar) entre "
            "+0,31 % y +1,95 % esta medido en +18,67 pp con IC 95 % "
            "[+13,83 , +20,96], pero DONDE caen los peldanos "
            "cambia con cada puja nueva."
        ),
    },

    # ========================================================
    # LA COLA DEL 20/09, y los cuatro llegaron aqui igual:
    # aprobados, armados y apagados.
    # ========================================================

    {
        "orden": 5,
        "interruptor": "BORDALAS_SIN_REFERENCIA_ESCALA",

        "que_cambia": (
            "Cuando el pronostico que falta es el DEL TITULAR QUE "
            "SALDRIA, la decision deja de llamarse "
            "`SIN_PRONOSTICO` y pasa a `SIN_REFERENCIA`, con el "
            "nombre de quien falta. Sigue valiendo cero: a ciegas "
            "no se puja."
        ),

        "que_mirar_antes": (
            "acquisition.targets[].xi_decision",
            "acquisition.targets[].xi_reason",
            "acquisition.starter_coverage.blocked_by_starter_rule",
            "roster_expansion.candidates[].blocked_by",
            "alarmaDeLosSentidos.sin_pronostico",
        ),

        "que_deberia_pasar": (
            "HOY, NADA: el 20/09 no hay ni un `SIN_PRONOSTICO` en "
            "el embudo, con 55 de 55 fichas con pronostico. El "
            "dia que vuelva a pasar -el caso conocido es la "
            "porteria del 18/09, con Esquivel de referencia- "
            "apareceran `SIN_REFERENCIA` en `xi_decision` y el "
            "motivo dira el nombre. Y `blocked_by_starter_rule` "
            "NO PUEDE BAJAR: es la prueba de que no se ha abierto "
            "ninguna puerta."
        ),

        "senal_de_apagarlo": (
            "Que `blocked_by_starter_rule` baje sin que haya "
            "bajado el numero de objetivos, o que aparezca un "
            "`SIN_REFERENCIA` con `our_value > 0`: cualquiera de "
            "las dos significa que el renombrado se ha llevado un "
            "freno por delante. UNA VUELTA basta: esto no acumula "
            "muestra, se ve o no se ve en la vuelta siguiente al "
            "encendido."
        ),

        "condicion_de_encendido": (
            "Ninguna. Va el primero de los cuatro porque no mueve "
            "un euro ni una decision -el valor sigue siendo cero "
            "en las dos posiciones, y hay guardia que lo exige- y "
            "porque deja legible la pantalla con la que se juzgan "
            "los otros tres."
        ),
    },
    {
        "orden": 6,
        "interruptor": "BORDALAS_CESTA_SOLO_EL_SUELO",

        "que_cambia": (
            "La cesta deja de pujar para revender por encima de "
            "1.500.000 EUR, que es `CORTES_DE_PRECIO[0]`. Debajo "
            "sigue entera, que es donde gana: 8 de 8 en verde, "
            "+28.867."
        ),

        "que_mirar_antes": (
            # El campo del porcentaje NO se nombra a proposito:
            # `test_el_libro_sabe_perder_v1` exige que el unico
            # fichero vivo que lo escriba sea el propio libro,
            # para que nadie calibre la prima de puja con
            # nuestros resultados. Con `placed` y `won` se ve
            # igual y esa guardia sigue entera.
            "subasta.outcomes.placed / .won / .lost",
            "subasta.bids_book[].source y .amount",
            "subasta.would_bid y .blocked_by",
            "roster_expansion.slots.our_roster_size",
            "roster_expansion.slots.free_slots",
        ),

        "que_deberia_pasar": (
            "La cesta sigue pujando en el suelo y deja de hacerlo "
            "arriba: de sus 10 compras de la temporada, NUEVE "
            "eran de abajo, asi que el corte le quita 1 de 10. "
            "`subasta.outcomes.placed` casi no se mueve — si cae "
            "mucho, el corte esta alcanzando al suelo y eso es un "
            "fallo, no el efecto. La plantilla NO encoge: hoy son "
            "15 fichas con 9 libres y quien compra arriba es la "
            "via del dueno, con 12 compras de 16. Lo que ahorra, "
            "medido, son 25.501 EUR: no un millon."
        ),

        "senal_de_apagarlo": (
            "Que `subasta.outcomes.placed` se quede parado "
            "durante TRES VUELTAS con la ventana abierta, o que "
            "aparezca una puja de `SUBASTA_CARTERA` por encima de "
            "1.500.000, que seria que no corta. Tres vueltas con "
            "ventana abierta es lo que hace falta para distinguir "
            "«no corta nada» de «hoy no habia nada»."
        ),

        "condicion_de_encendido": (
            "Va detras del quinto porque este SI para operaciones "
            "y SI mueve dinero. Y necesita tres vueltas con la "
            "ventana del reset abierta antes de poder juzgarlo."
        ),
    },
    {
        "orden": 7,
        "interruptor": "BORDALAS_JORNADAS_POR_SU_FECHA",

        "que_cambia": (
            "La hora de cada jornada sale del `roundStarted` del "
            "tablon, que trae el `round_id` dentro, en vez del "
            "calendario de LaLiga, que va por NUMERO y le da a "
            "«Jornada 6 (aplazada)» la misma hora que a «Jornada "
            "6»."
        ),

        "que_mirar_antes": (
            "marcador.resumen.jornadas_medibles",
            "marcador.resumen.diferencia_media y .diferencia_media_n",
            "marcador.resumen.jornadas_sin_hora",
            "marcador.jornadas[].motivo (los negativos)",
            "marcador.resumen.jornadas_fiables",
        ),

        "que_deberia_pasar": (
            "`jornadas_medibles` pasa de 4 a 5 y "
            "`diferencia_media` de +20,4 (n=2) a +3,6 (n=3). Los "
            "dos negativos grandes -9 jugadores con -31, y 2 con "
            "-7- DESAPARECEN, y quedan tres de un solo jugador y "
            "de -1 o -2, que son correcciones retroactivas de "
            "Biwenger. `jornadas_fiables` SIGUE EN CERO: esto no "
            "arregla que ninguna jornada cuadre todavia, y "
            "esperar otra cosa seria leerlo mal."
        ),

        "senal_de_apagarlo": (
            "Que `jornadas_sin_hora` suba por encima de cero: "
            "querria decir que el tablon no cubre alguna jornada "
            "y se ha perdido la hora que antes daba el "
            "calendario. O que `jornadas_medibles` BAJE de 5. Se "
            "ve en la PRIMERA vuelta: el marcador se recalcula "
            "entero en cada una."
        ),

        "condicion_de_encendido": (
            "Ninguna, y es el mas inofensivo de los cuatro: no "
            "toca ninguna decision de compra ni de venta. Solo "
            "cambia como se ordenan las fotos para medir lo que "
            "ya paso."
        ),
    },
    {
        "orden": 8,
        "interruptor": "BORDALAS_OBJETIVOS_EL_CATALOGO",

        "que_cambia": (
            "La lista de objetivos del tablero de titularidad "
            "pasa de plantilla + mercado + rivales a TODO el "
            "catalogo: se le pregunta tambien por los libres, que "
            "son la mayoria."
        ),

        "que_mirar_antes": (
            "acquisition.starter_coverage.with_forecast / .total",
            "acquisition.targets[].xi_decision (los SIN_PRONOSTICO)",
            "lineup.starter_board_players y .starter_data_total",
            "lineup.starter_cache_status",
            "losSentidos (el tablero de titulares y su edad)",
        ),

        "que_deberia_pasar": (
            "Los emparejados suben de 142 a 497, y "
            "`SIN_PRONOSTICO` como veredicto del once cae de 385 "
            "a 30 sobre el catalogo entero. PARA EL MERCADO DEL "
            "DIA NO CAMBIA NI UNA DECISION: los 52 del escaparate "
            "ya tenian pronostico. Y no cuesta ni una peticion: "
            "las 20 paginas ya se piden. Medido: +0,63 s por "
            "vuelta."
        ),

        "senal_de_apagarlo": (
            "Que la vuelta tarde mas de un minuto extra -lo "
            "medido son 0,63 s- o que `starter_cache_status` "
            "empiece a salir en fallo. Y sobre todo: que cambie "
            "UNA SOLA decision del mercado del dia, porque no "
            "deberia cambiar ninguna. DOS VUELTAS: una para el "
            "tiempo y otra para ver que las decisiones son las "
            "mismas."
        ),

        "condicion_de_encendido": (
            "VA EL ULTIMO, y no por razon tecnica: es el unico "
            "que ya rompio una vuelta -la noche del 20/09- y "
            "encenderlo al final es encenderlo cuando el paso 0 "
            "ya ha funcionado con los otros siete."
        ),
    },
)


# UN DATO, UN NOMBRE (doctrina 33). Eran cuatro hasta que la cola
# del 20/09 trajo otros cuatro. `LOS_CUATRO` se queda como alias
# para no romper a quien ya lo importaba.
LOS_DEL_PROTOCOLO = tuple(f["interruptor"] for f in PROTOCOLO)

LOS_CUATRO = LOS_DEL_PROTOCOLO


def encendido(nombre: str, entorno=None) -> bool:
    """
    Si ese interruptor esta puesto. Forma fija, nunca lanza.

    El entorno se RECIBE. Una guardia que lee `os.environ` de
    verdad cambia de color segun quien la corra, y eso es lo
    mismo que leer estado de produccion.
    """

    fuente = os.environ if entorno is None else entorno

    try:
        return str(
            fuente.get(nombre, "")
        ).strip().lower() in {"1", "true", "si", "yes"}

    except Exception:                               # noqa: BLE001
        return False


def ficha_de(nombre: str) -> dict | None:
    """La ficha de encendido de ese interruptor, o None."""

    for ficha in PROTOCOLO:

        if ficha["interruptor"] == nombre:
            return dict(ficha)

    return None


def el_aviso(entorno=None) -> dict:
    """
    ¿Hay mas de un interruptor del protocolo puesto?

    Forma fija, nunca lanza. NO apaga nada: avisa. Apagar por su
    cuenta seria decidir, y quien decide es el dueno.
    """

    vacio = {
        "available": False,
        "encendidos": [],
        "cuantos": 0,
        "ok": None,
        "reason": None,
    }

    try:
        if not PROTOCOLO:
            return {
                **vacio,
                "reason": (
                    "No hay ningun interruptor declarado en el "
                    "protocolo: sin ellos no hay nada que "
                    "vigilar."
                ),
            }

        puestos = [
            nombre
            for nombre in LOS_CUATRO
            if encendido(nombre, entorno)
        ]

        if len(puestos) <= 1:
            return {
                "available": True,
                "encendidos": puestos,
                "cuantos": len(puestos),
                "ok": True,
                "reason": (
                    f"Un interruptor del protocolo puesto: "
                    f"{puestos[0]}."
                    if puestos
                    else "Ningun interruptor del protocolo puesto."
                ),
            }

        return {
            "available": True,
            "encendidos": puestos,
            "cuantos": len(puestos),
            "ok": False,
            "reason": (
                f"HAY {len(puestos)} INTERRUPTORES DEL PROTOCOLO "
                f"PUESTOS A LA VEZ: {', '.join(puestos)}. "
                f"Cambiar dos cosas en la misma vuelta es no "
                f"saber cual movio que, ni cual apagar si sale "
                f"mal. Uno por vuelta."
            ),
        }

    except Exception as error:                      # noqa: BLE001
        return {
            **vacio,
            "reason": (
                f"No se pudo mirar el protocolo: "
                f"{type(error).__name__}: {error}"
            ),
        }
