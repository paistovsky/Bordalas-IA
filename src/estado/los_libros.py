"""
Los libros: lo que no se puede reconstruir.

EL CIMIENTO ERA ARENA (14/09/2026)

    Todo `data/` estaba en `.gitignore` y vivia UNICAMENTE en una
    cache de GitHub Actions:

        .gitignore:15              data/
        ficheros de data/ en git   0
        cache                      bordalas-state-*, desalojo a
                                   los 7 dias sin uso
        artefactos                 retencion 2 dias, y NUNCA se
                                   restauran

    El libro del marcador no esta en git, no esta en ningun
    artefacto y no esta en ninguna otra parte. Solo en esa cache.

    Y el ciclo ya estuvo parado VEINTICUATRO DIAS en agosto. No
    costo los libros solo porque entonces no habia libros que
    perder.

LA SEPARACION

    LAS FOTOS son desechables: caducan a las 24 (unas 12 horas) y
    esta bien. Una foto perdida es una foto.

    LOS LIBROS no se pueden reconstruir. Un libro perdido es la
    temporada. Pesan poco, cambian poco, y son lo unico que no
    se puede volver a pedir.

POR QUE LA LISTA VIVE AQUI Y NO EN EL `.gitignore`

    Porque la leen TRES sitios: el `.gitignore` —para dejarlos
    entrar—, el guardado del ciclo —para saber que mirar— y la
    guardia que comprueba las dos cosas.

    Con la lista escrita a mano en cada sitio, el dia que se
    añada un libro habria que acordarse de tres. Y el dia que
    alguien se olvidara, el libro nuevo se perderia EN SILENCIO,
    que es como se han perdido todos los demas.

    Es la misma forma del arreglo del 07/09 con la lista de
    guardias de la verja: una linea, un sitio.

QUE ENTRA Y QUE NO

    Entra lo que se ACUMULA y no se puede volver a pedir: una
    linea por jornada, por puja, por traspaso o por dia.

    NO entra lo que se recalcula de la foto en cada vuelta
    —`scout_report`, `cache_biwenger`, `jornada_perfecta_*`— por
    grande que sea: eso no es un libro, es un cache.

    Y NO entran las fotos.
"""

from __future__ import annotations

from pathlib import Path


# LOS LIBROS, uno por linea y con el motivo de cada uno.
#
#     `ruta` es relativa a la raiz del repo, siempre con `/`:
#     es la que entiende git y la que se escribe en el
#     `.gitignore`.
LIBROS = (
    {
        "ruta": "data/intelligence/libro_de_la_valoracion.jsonl",
        "que_es": (
            "Una linea por jugador del tablero y dia de mercado: "
            "el valor que le dimos, el precio, lo que pujariamos, "
            "y a 7 y a 14 dias su precio, puntos y partidos."
        ),
        "por_que_no_se_reconstruye": (
            "El valor que le dio el motor un dia concreto no esta en "
            "ninguna parte: se recalcula cada vuelta y se pisa. Sin "
            "el no se puede saber si ganar el 89,5 % de las subastas "
            "es punteria o pagar de mas."
        ),
    },
    {
        "ruta": "data/intelligence/puntos_por_jornada.jsonl",
        "que_es": (
            "Los puntos, partidos y precio de todo el catalogo al "
            "cerrar cada jornada."
        ),
        "por_que_no_se_reconstruye": (
            "El catalogo publica los totales de HOY. Los de la "
            "jornada pasada desaparecen al jugarse la siguiente."
        ),
    },
    {
        "ruta": "data/intelligence/marcador.json",
        "que_es": (
            "El marcador de la temporada: una entrada por "
            "jornada con la clasificacion, el once y los totales "
            "de cada jugador en ese momento."
        ),
        "por_que_no_se_reconstruye": (
            "`/rounds/league` devuelve SOLO la jornada en curso. "
            "Cuando cierra y salta a la siguiente, los puntos de "
            "la anterior desaparecen del endpoint. Lo que no se "
            "anoto en el momento no se recupera JAMAS."
        ),
    },
    {
        "ruta": "data/intelligence/onces_de_la_jornada.jsonl",
        "que_es": (
            "El once que jugo cada jornada, congelado en la "
            "ventana anterior al primer partido."
        ),
        "por_que_no_se_reconstruye": (
            "A partir del pitido inicial Biwenger ya no dice que "
            "once estaba puesto ANTES. Sin esta linea, la unica "
            "forma de saberlo seria mirarlo a ojo, que es "
            "inventarselo."
        ),
    },
    {
        "ruta": "data/intelligence/libro_de_publicacion.jsonl",
        "que_es": "Que se publico en el escaparate y cuando.",
        "por_que_no_se_reconstruye": (
            "Una publicacion que caduco no deja rastro en "
            "ninguna peticion."
        ),
    },
    {
        "ruta": "data/intelligence/libro_en_la_sombra.jsonl",
        "que_es": (
            "Lo que se habria hecho sin ejecutarlo: la fase "
            "observador de cada motor nuevo."
        ),
        "por_que_no_se_reconstruye": (
            "Es el contrafactual del dia. Se puede recalcular el "
            "de HOY, nunca el del martes pasado."
        ),
    },
    {
        "ruta": "data/intelligence/divergence_ledger.json",
        "que_es": (
            "En que discrepan las fuentes de titularidad, dia a "
            "dia."
        ),
        "por_que_no_se_reconstruye": (
            "Cada fuente publica su estado de HOY. La "
            "discrepancia de anteayer no se puede volver a "
            "pedir."
        ),
    },
    {
        "ruta": "data/trading/bid_outcome_ledger.json",
        "que_es": (
            "Que paso con cada puja: si se gano, por cuanto y "
            "contra quien."
        ),
        "por_que_no_se_reconstruye": (
            "Es la unica medicion de si pujamos bien. El tablon "
            "publica la venta, no nuestra puja perdedora."
        ),
    },
    {
        "ruta": "data/trading/libro_de_renovaciones.jsonl",
        "que_es": "Cada renovacion de publicacion, con su motivo.",
        "por_que_no_se_reconstruye": (
            "No queda en ninguna peticion: es una decision "
            "nuestra."
        ),
    },
    {
        "ruta": "data/trading/libro_del_carril.jsonl",
        "que_es": (
            "Los viajes del carril: que se compro para revender, "
            "por cuanto, y como acabo."
        ),
        "por_que_no_se_reconstruye": (
            "El COSTE de un viaje abierto es lo que fija el "
            "suelo de cobro. Sin el, `precio_de_salida` no puede "
            "calcularse y la prohibicion 0 de `que_cobrar` dice "
            "NO VENDER."
        ),
    },
    {
        "ruta": "data/trading/position_ledger.json",
        "que_es": "La posicion abierta de cada jugador nuestro.",
        "por_que_no_se_reconstruye": (
            "Guarda a que precio entro cada uno. Biwenger "
            "publica el precio de HOY, no el de la compra."
        ),
    },
    {
        "ruta": "data/autopilot/price_history.json",
        "que_es": (
            "El historico compacto de precios, uno por jugador y "
            "dia."
        ),
        "por_que_no_se_reconstruye": (
            "Se construyo EXACTAMENTE para sobrevivir al borrado "
            "de fotos: `price_history_store` lo dice en su "
            "cabecera. Perderlo devuelve el problema que vino a "
            "arreglar — y es lo que dejo "
            "`con_precio_de_mercado: 0` sobre los 8 traspasos."
        ),
    },
    {
        "ruta": "data/calendar/calendar_changes.jsonl",
        "que_es": (
            "Cada cambio del calendario de LaLiga, con cuando se "
            "detecto."
        ),
        "por_que_no_se_reconstruye": (
            "El calendario publica el estado de hoy. Que un "
            "partido SE MOVIO, y cuando nos enteramos, solo esta "
            "aqui."
        ),
    },
    {
        "ruta": "data/solvency/bitacora_del_saldo.jsonl",
        "que_es": "El saldo, vuelta a vuelta.",
        "por_que_no_se_reconstruye": (
            "Biwenger da el saldo de AHORA. La curva de como se "
            "llego hasta el no existe en ninguna parte."
        ),
    },
    {
        "ruta": "data/solvency/censo_de_ofertas.jsonl",
        "que_es": "Las ofertas que entraron, y que se hizo.",
        "por_que_no_se_reconstruye": (
            "Una oferta caducada desaparece del endpoint."
        ),
    },
    {
        "ruta": "data/solvency/pujas_bajo_precio.jsonl",
        "que_es": "Las pujas por debajo de precio, contadas.",
        "por_que_no_se_reconstruye": (
            "Es una observacion nuestra sobre el mercado de un "
            "dia concreto."
        ),
    },
    {
        "ruta": "data/trading/libro_del_escaparate.jsonl",
        "que_es": (
            "Los veinte del escaparate del Computer en cada "
            "reset, con precio, puntos, partidos jugados y "
            "pronostico de titularidad."
        ),
        "por_que_no_se_reconstruye": (
            "El escaparate de ayer no existe en ningun endpoint: "
            "se renueva entero cada reset y el anterior no deja "
            "rastro. Medido el 17/09: lo unico reconstruible eran "
            "NUEVE dias sueltos sacados de `market.sales` dentro "
            "de los snapshots, con un agujero de tres semanas "
            "—del 18/08 al 09/09— porque las fotos no se guardan.\n"
            "            Y el PRONOSTICO no se reconstruye ni con "
            "las fotos: la titularidad de un jugador un martes de "
            "agosto no esta en ninguna parte. Sin ella no se "
            "puede saber si nos mejoraba alguno de los que "
            "dejamos pasar."
        ),
    },
    {
        "ruta": "data/trading/libro_de_viajes.jsonl",
        "que_es": (
            "Quien esta de viaje del carril y cuanto costo entrar."
        ),
        "por_que_no_se_reconstruye": (
            "`salida_del_viaje.que_cobrar` lee de aqui el COSTE de "
            "cada viaje abierto, y ese coste es el que fija el "
            "suelo de cobro. Biwenger publica el precio de HOY, no "
            "el que pagamos. Sin este libro, la prohibicion 0 dice "
            "NO VENDER y el carril se queda con la mercancia "
            "dentro. "
            "Y es el que `cuantos_en_este_reset()` abre "
            "por defecto: es lo que gasta el cupo del reset."
        ),
    },
    {
        "ruta": "data/trading/libro_de_escaparate.jsonl",
        "que_es": (
            "Que se puso a la venta al comprarlo, a que precio y "
            "cuando."
        ),
        "por_que_no_se_reconstruye": (
            "Una publicacion que caduco no deja rastro en ninguna "
            "peticion. OJO AL NOMBRE: este no es "
            "`libro_del_escaparate.jsonl` —con `del`—, que es el "
            "de los veinte del Computer. Son dos libros distintos "
            "a una letra de distancia."
        ),
    },
    {
        "ruta": "data/trading/libro_de_salidas.jsonl",
        "que_es": "Cada oferta cobrada para cerrar un viaje.",
        "por_que_no_se_reconstruye": (
            "Es la unica medicion de si el carril cierra bien. "
            "Aceptar una oferta es irreversible y la oferta "
            "aceptada desaparece del endpoint."
        ),
    },
    {
        "ruta": "data/trading/libro_de_la_ventana.jsonl",
        "que_es": (
            "Cuando se entro por ultima vez en la ventana del "
            "reset y que se hizo alli."
        ),
        "por_que_no_se_reconstruye": (
            "Existe para que una ventana que no se abre NUNCA deje "
            "de ser indistinguible de una noche normal. Si el libro "
            "se pierde, vuelve el fallo que vino a destapar: el "
            "cron disparando una hora tarde durante semanas sin que "
            "nada lo dijera."
        ),
    },
    {
        "ruta": "data/intelligence/scout_accuracy_ledger.json",
        "que_es": (
            "Quien dijo que un precio subiria, y si acerto."
        ),
        "por_que_no_se_reconstruye": (
            "Un pronostico solo se puede puntuar contra lo que "
            "paso DESPUES, asi que hay que haberlo anotado ANTES. "
            "Es el libro que decide a cual de las tres fuentes "
            "hacerle caso y cual se apaga por ruido — y ninguna "
            "entra en esta casa por prestigio."
        ),
    },
    {
        "ruta": "data/intelligence/source_accuracy_ledger.json",
        "que_es": (
            "El acierto de cada fuente de titularidad, con su "
            "Brier."
        ),
        "por_que_no_se_reconstruye": (
            "Lo mismo: el pronostico de ayer no esta en ningun "
            "endpoint. Es de donde sale que FutbolFantasy puntua "
            "0,3365 —peor que tirar una moneda— y por eso el "
            "consenso no premia a la mayoria por ser mayoria."
        ),
    },
    {
        "ruta": "data/intelligence/rejection_ledger.json",
        "que_es": (
            "Lo que decidimos NO comprar, y que paso despues."
        ),
        "por_que_no_se_reconstruye": (
            "Es la unica vara que nos medimos a nosotros. Cada "
            "noche el modelo concluye que no hay que comprar nada; "
            "sin este libro nadie apunta si los que rechazo "
            "subieron. El contrafactual de anteayer no se puede "
            "volver a pedir."
        ),
    },
    {
        "ruta": "data/autopilot/computer_offer_history.json",
        "que_es": (
            "Cuantas veces el Computer ha vuelto a ofrecer al "
            "mismo jugador."
        ),
        "por_que_no_se_reconstruye": (
            "Una oferta que caduco desaparece del endpoint, asi "
            "que el recuento de cuantas veces se repitio solo "
            "existe porque se fue anotando. Es lo que impide "
            "tratar la quinta oferta por el mismo jugador como si "
            "fuera la primera."
        ),
    },
    {
        "ruta": "data/rival_intelligence/board_events.json",
        "que_es": (
            "El tablon de la liga acumulado: 303 eventos desde "
            "el `leagueReset` del 09/08, el dia 1."
        ),
        "por_que_no_se_reconstruye": (
            "El tablon se pide de 1000 en 1000 y este fichero "
            "los MEZCLA vuelta a vuelta —`merge_board_events`—. "
            "Esa mezcla existe porque una sola peticion no "
            "alcanza a cubrir la temporada. Es de donde salen "
            "los 8 traspasos de manager a manager.\n"
            "            ES EL MAS PESADO CON DIFERENCIA (960 KB "
            "de los 1.404 del total). Si algun dia estorba, es "
            "el primero que se mira — pero no el primero que se "
            "quita sin medir si la peticion alcanza."
        ),
    },
)


# LO QUE EL CODIGO ESCRIBE BAJO `data/` Y NO ES UN LIBRO.
#
#     MEDIDO EL 17/09/2026, del AST y no de la memoria: el codigo
#     escribe 29 ficheros distintos bajo `data/`. Siete de ellos
#     eran libros que NO estaban en la lista —y por tanto el
#     `.gitignore` los tapaba, y morian con el runner—. Estan
#     arriba desde hoy.
#
#     Los otros veintidos son esto. No es una lista de exclusion
#     por comodidad: es la OTRA MITAD de la clasificacion. La
#     guardia `test_todo_libro_escrito_esta_en_la_lista` exige
#     que todo lo que el codigo escriba este en una de las dos,
#     asi que un escritor nuevo pone la verja en rojo hasta que
#     alguien diga cual de las dos cosas es.
#
#     POR QUE ESO ES EL ARREGLO Y NO LA LISTA EN SI. Los siete
#     que faltaban no se perdieron porque nadie supiera que eran
#     libros: se perdieron porque NADIE TUVO QUE DECIDIRLO. Un
#     fichero nuevo entraba en `data/`, el `.gitignore` lo tapaba
#     y no pasaba nada. Ahora pasa algo.
NO_SON_LIBROS = (
    # Se recalculan de la foto en cada vuelta.
    ("data/autopilot/cache_biwenger.json", "cache del reset"),
    ("data/calendar/laliga_calendar.json", "cache del calendario"),
    ("data/dashboard_player_photo_cache.json", "cache de fotos"),
    ("data/external_status_cache.json", "cache de estado externo"),
    ("data/player_mapping_cache.json", "cache de nombres"),
    ("data/intelligence/futbolfantasy_board.json", "cache de FF"),
    ("data/intelligence/penalty_kickers.json", "cache de penaltis"),
    ("data/intelligence/press_report.json", "cache de prensa"),
    ("data/intelligence/scout_report.json", "el informe de hoy"),
    (
        "data/intelligence/starter_multisource_v112.json",
        "consenso de titularidad, se rehace cada vuelta",
    ),
    (
        "data/intelligence/starter_multisource_v1124.json",
        "consenso de titularidad, se rehace cada vuelta",
    ),
    ("data/league_center/laliga_standings.json", "cache de LaLiga"),
    ("data/lineup_monitor/state.json", "estado del vigilante"),
    (
        "data/rival_intelligence/board_latest_raw.json",
        "el crudo de la ultima peticion; lo que se acumula es "
        "`board_events.json`, que si es libro",
    ),
    ("data/rival_intelligence/profiles_cache.json", "cache de perfiles"),
    ("data/trading/v10_full_autonomous_status.json", "estado de la vuelta"),
    ("data/trading/v10_production_status.json", "estado de la vuelta"),

    (
        "data/autopilot/action_failure_backoff.json",
        "la espera tras un fallo; perderla solo reintenta antes",
    ),
    (
        "data/intelligence/jornada_perfecta_lineups.json",
        "cache de Jornada Perfecta",
    ),
    (
        "data/intelligence/jornada_perfecta_market.json",
        "cache de Jornada Perfecta",
    ),

    # Las fotos y sus derivados.
    ("data/snapshot_{}.json", "una foto"),
    ("data/ff_html/{}.html", "el HTML crudo de una peticion"),
    ("data/intelligence/archivo/{}.json", "el archivo del dia, derivado de la foto"),

    # SE PODAN A PROPOSITO.
    #
    #     EL MOTIVO DE AQUI ERA ESTE, Y YA NO ES VERDAD
    #     (22/09/2026):
    #
    #         "`prune_github_state.py` los trunca DESPUES del
    #         ciclo y ANTES del guardado. Si se metieran en la
    #         lista se commitearia la version podada, que es peor
    #         que no commitear nada: pareceria un libro y seria
    #         un recorte."
    #
    #     El dueño invirtio los dos pasos del workflow el 22/09:
    #     `Guardar los libros` va ahora ANTES que `Prune
    #     persisted state`. Con ese orden se commitearia lo que
    #     la vuelta escribio, no el recorte, asi que EL MOTIVO
    #     QUE LOS DEJABA FUERA HA DESAPARECIDO.
    #
    #     SE QUEDAN FUERA IGUAL, Y AHORA ES UNA DECISION, NO UNA
    #     RESTRICCION. Meterlos es del dueño: `autopilot_log.jsonl`
    #     son 5.088 B por vuelta y 35,1 vueltas al dia —6,4 MB al
    #     mes con las candidatas perdedoras, 12,1 MB estables
    #     podado a 2.000 lineas, 57 dias de historia—. El
    #     repositorio ya versiona `scout_accuracy_ledger.json`
    #     (31 MB).
    #
    #     La guardia de aqui —`test_ningun_libro_se_clasifico_dos_veces`—
    #     sigue teniendo sentido: comprueba que un fichero no este
    #     en las dos listas a la vez, y eso vale con cualquier
    #     orden del workflow. Lo que habia caducado era el MOTIVO,
    #     no la guardia.
    ("data/autopilot/autopilot_log.jsonl", "lo poda `prune_github_state`"),
    (
        "data/autopilot/competitive_observer_log.jsonl",
        "lo poda `prune_github_state`",
    ),
)


def clasificados() -> set:
    """Todo lo que ya tiene decidido si es libro o no."""

    return set(rutas()) | {ruta for ruta, _ in NO_SON_LIBROS}


# Las FOTOS no son libros. Se dice aqui para que la guardia
# pueda comprobar que no se han colado en git por el camino.
FOTOS = "data/snapshot_*.json"


def rutas() -> tuple:
    """Solo las rutas, en el orden en que estan declaradas."""

    return tuple(libro["ruta"] for libro in LIBROS)


def existentes(raiz=None) -> list:
    """Los libros que hay AHORA MISMO en el disco.

    Un libro que todavia no existe no es un fallo: el del once
    se escribe la primera vez que se cruza la ventana de los 90
    minutos, y hasta entonces no hay fichero.
    """

    base = Path(raiz) if raiz else Path(".")

    return [
        ruta
        for ruta in rutas()
        if (base / ruta).exists()
    ]


def lineas_para_gitignore() -> list:
    """Las lineas que dejan pasar los libros, en orden.

    GIT NO DEJA RESCATAR UN FICHERO DE UNA CARPETA EXCLUIDA.

        Con `data/` a secas, `!data/intelligence/marcador.json`
        NO funciona: git ni siquiera entra en la carpeta. Hay que
        abrir el camino nivel a nivel —excluir el contenido de
        cada carpeta y volver a dejar entrar la siguiente— y solo
        al final el fichero.

    Se genera desde `LIBROS` para que el `.gitignore` no pueda
    quedarse desparejado de la lista.
    """

    # EL ORDEN IMPORTA Y NO ES EL DE LA LISTA. Git aplica las
    # reglas de arriba abajo y gana la ULTIMA que encaja, asi que
    # primero se cierra el nivel y luego se abre lo que se
    # rescata. Se agrupa por carpeta para que ademas se lea.
    #
    # Y TODO VA ANCLADO CON `/` AL PRINCIPIO (14/09/2026)
    #
    #     La regla vieja era `data/` a secas. Sin barra delante,
    #     git la aplica a CUALQUIER carpeta llamada `data` a
    #     cualquier profundidad — que era justo lo que hacia
    #     falta, porque hay varias:
    #
    #         dashboard/data/
    #         dashboard-v8/public/data/
    #         dashboard-v8/dist/data/
    #         dashboard-v8/node_modules/*/data/
    #
    #     La primera version de esto la sustituyo por `data/*`, y
    #     `data/*` SI lleva barra en medio, asi que queda anclado
    #     a la raiz: las cuatro de arriba se destaparon de golpe y
    #     `git status` se lleno de `node_modules`.
    #
    #     Asi que se conserva la regla generica y se abre SOLO la
    #     de la raiz, con `/` delante en todo lo demas.
    lineas = [
        "data/",
        "!/data/",
        "/data/*",
    ]

    por_carpeta = {}

    for ruta in rutas():

        carpeta, _, _ = ruta.rpartition("/")

        por_carpeta.setdefault(carpeta, []).append(ruta)

    for carpeta in sorted(por_carpeta):

        lineas.append("")
        lineas.append(f"!/{carpeta}/")
        lineas.append(f"/{carpeta}/*")

        for ruta in por_carpeta[carpeta]:
            lineas.append(f"!/{ruta}")

    return lineas


# ============================================================
# QUE ESCRIBE EL CODIGO DE VERDAD
# ============================================================

# LA CARPETA DEL ESTADO, sacada de la propia lista para que no
# pueda quedarse desparejada de ella.
DIRECTORIO_DE_ESTADO = rutas()[0].split("/")[0]

# LAS CARPETAS DE CODIGO QUE SE MIRAN.
DONDE_VIVE_EL_CODIGO = ("src", "scripts")

# LOS MODOS DE `open()` QUE ESCRIBEN.
MODOS_QUE_ESCRIBEN = "wax"

_ESCRIBEN = frozenset({"write_text", "write_bytes", "writelines"})

_BARRA_INVERSA = chr(92)

# LAS COLAS DE UNA ESCRITURA ATOMICA.
SUFIJOS_TEMPORALES = (".tmp", ".temp", ".partial")


def _ruta_de(nodo, constantes):
    """
    La ruta que representa un nodo del AST, o None.

    Entiende el literal, la constante del modulo, la division de
    `Path`, el `ruta or CONSTANTE` con que empiezan todos los
    escritores de esta casa, y las `f"..."` —cuyo hueco se deja
    en `{}`, porque el nombre concreto no se sabe leyendo—.
    """

    import ast

    if isinstance(nodo, ast.Constant) and isinstance(nodo.value, str):
        return nodo.value

    if isinstance(nodo, ast.Name):
        return constantes.get(nodo.id)

    if isinstance(nodo, ast.Attribute):
        return constantes.get(nodo.attr)

    if isinstance(nodo, ast.BinOp) and isinstance(nodo.op, ast.Div):

        izquierda = _ruta_de(nodo.left, constantes)
        derecha = _ruta_de(nodo.right, constantes)

        if izquierda is None or derecha is None:
            return None

        return izquierda.rstrip("/") + "/" + derecha.lstrip("/")

    if isinstance(nodo, ast.BoolOp):

        for valor in nodo.values:

            hallada = _ruta_de(valor, constantes)

            if hallada:
                return hallada

    if isinstance(nodo, ast.Call):

        funcion = nodo.func

        nombre = (
            funcion.attr
            if isinstance(funcion, ast.Attribute)
            else getattr(funcion, "id", None)
        )

        if nombre == "Path" and nodo.args:
            return _ruta_de(nodo.args[0], constantes)

        # LA ESCRITURA ATOMICA: `X.with_suffix(".json.tmp")` y
        # luego `os.replace`. Sin esto el censo se dejaba CUATRO
        # libros —el marcador, el historico de precios, los onces
        # y el libro de posiciones—, que son justo los que se
        # escriben con cuidado. Se resuelve el destino temporal y
        # `apunta()` le quita el `.tmp`: escribir en `X.tmp` para
        # renombrarlo a `X` es escribir en `X`.
        if (
            nombre in ("with_suffix", "with_name")
            and isinstance(funcion, ast.Attribute)
            and nodo.args
        ):
            base = _ruta_de(funcion.value, constantes)

            cola = _ruta_de(nodo.args[0], constantes)

            if base is None or cola is None:
                return None

            if nombre == "with_name":
                return base.rpartition("/")[0] + "/" + cola

            tronco, punto, _ = base.rpartition(".")

            return (tronco if punto else base) + (
                cola if cola.startswith(".") else "." + cola
            )

    if isinstance(nodo, ast.JoinedStr):
        return "".join(
            str(trozo.value)
            if isinstance(trozo, ast.Constant)
            else "{}"
            for trozo in nodo.values
        )

    return None


def _nodos_que_se_escriben(cuerpo):
    """Los nodos-ruta sobre los que se escribe dentro de `cuerpo`."""

    import ast

    salida = []

    for nodo in ast.walk(cuerpo):

        if not isinstance(nodo, ast.Call):
            continue

        funcion = nodo.func

        if isinstance(funcion, ast.Attribute) and funcion.attr in _ESCRIBEN:
            salida.append(funcion.value)

        elif getattr(funcion, "id", None) == "open" and nodo.args:

            modo = ""

            if len(nodo.args) > 1 and isinstance(nodo.args[1], ast.Constant):
                modo = str(nodo.args[1].value)

            for clave in nodo.keywords:

                if clave.arg == "mode" and isinstance(
                    clave.value, ast.Constant
                ):
                    modo = str(clave.value.value)

            if any(letra in modo for letra in MODOS_QUE_ESCRIBEN):
                salida.append(nodo.args[0])

        elif (
            isinstance(funcion, ast.Attribute)
            and funcion.attr == "open"
            and nodo.args
            and isinstance(nodo.args[0], ast.Constant)
            and any(
                letra in str(nodo.args[0].value)
                for letra in MODOS_QUE_ESCRIBEN
            )
        ):
            salida.append(funcion.value)

    return salida


def escritos_por_el_codigo(raiz=None) -> dict:
    """
    Que ficheros del directorio de estado escribe el codigo.

    Devuelve `{ruta: [modulos que la escriben]}`.

    POR QUE DEL AST Y NO DE UN `grep`

        Lo mismo que paso el 16/09 con los lectores del `intent`:
        la lista escrita a mano estaba mal EN LAS DOS
        DIRECCIONES. Aqui seria peor, porque lo que falte en la
        lista es un libro que se pierde en silencio.

    POR QUE SIGUE LA RUTA A TRAVES DE LAS FUNCIONES

        Ningun libro de esta casa se escribe con su ruta al lado
        del `write`. Se escriben con `_apendar(fila, ruta, ...)`,
        y la ruta llega como argumento —a veces como `ruta or
        BITACORA`, tres saltos mas abajo—.

        MEDIDO: mirando solo el sitio del `write` se encontraban
        2 de los 16 libros. El detector estaba roto, no el codigo.
        Asi que primero se marcan las funciones que escriben en un
        PARAMETRO, y despues se resuelven sus llamadas; y se
        repite hasta que deja de aparecer nada nuevo.

    LO QUE ESTO NO VE, dicho claro: una ruta armada en ejecucion
    a partir de algo que no sea constante. De esas se sabe la
    carpeta pero no el nombre, y salen con `{}` en el hueco — y
    con `{}` se clasifican, que es lo honesto.

    Nunca lanza: un modulo que no se pueda leer o parsear se
    salta. NO lee estado, no sale a la red y no mira el reloj:
    solo abre codigo fuente de este repositorio.
    """

    import ast

    base = Path(raiz) if raiz else Path(".")

    arboles = {}

    for carpeta in DONDE_VIVE_EL_CODIGO:

        for fichero in sorted((base / carpeta).rglob("*.py")):

            try:
                arboles[fichero] = ast.parse(
                    fichero.read_text(
                        encoding="utf-8", errors="replace"
                    )
                )

            except (OSError, SyntaxError, ValueError):
                continue

    # LAS CONSTANTES DE RUTA DE CADA MODULO.
    #
    #     Tres vueltas porque una constante puede apoyarse en otra
    #     que todavia no se habia visto —`BITACORA = DIRECTORIO /
    #     "bitacora_del_saldo.jsonl"`—.
    constantes = {}

    for modulo, arbol in arboles.items():

        vistas = {}

        for _ in range(3):

            for nodo in ast.walk(arbol):

                if (
                    isinstance(nodo, ast.Assign)
                    and len(nodo.targets) == 1
                    and isinstance(nodo.targets[0], ast.Name)
                ):
                    hallada = _ruta_de(nodo.value, vistas)

                    if hallada:
                        vistas[nodo.targets[0].id] = hallada

        constantes[modulo] = vistas

    funciones = []

    for modulo, arbol in arboles.items():

        for nodo in ast.walk(arbol):

            if isinstance(nodo, (ast.FunctionDef, ast.AsyncFunctionDef)):
                funciones.append(
                    (
                        modulo,
                        nodo,
                        [a.arg for a in nodo.args.args]
                        + [a.arg for a in nodo.args.kwonlyargs],
                    )
                )

    # `nombre de funcion -> parametros suyos que acaban escritos`.
    escritoras = {}

    escritos = {}

    marca = DIRECTORIO_DE_ESTADO + "/"

    def apunta(ruta, modulo) -> bool:
        """Anota una ruta. Dice si esto ha añadido algo nuevo."""

        if not ruta:
            return False

        texto = str(ruta).replace(_BARRA_INVERSA, "/")

        if marca not in texto:
            return False

        limpia = texto[texto.index(marca):]

        # El destino de una escritura atomica cuenta como su
        # destino final, no como un fichero aparte.
        while limpia.endswith(SUFIJOS_TEMPORALES):
            limpia = limpia.rpartition(".")[0]

        try:
            quien = modulo.relative_to(base)

        except ValueError:
            quien = modulo

        quien = str(quien).replace(_BARRA_INVERSA, "/")

        antes = escritos.setdefault(limpia, [])

        if quien in antes:
            return False

        antes.append(quien)

        return True

    def nombres(nodo) -> set:
        import ast as _ast

        return {
            n.id for n in _ast.walk(nodo) if isinstance(n, _ast.Name)
        }

    for _ in range(6):

        cambio = False

        for modulo, funcion, parametros in funciones:

            locales = constantes[modulo]

            # 1. ESCRITURAS DIRECTAS dentro de la funcion.
            for nodo in _nodos_que_se_escriben(funcion):

                if apunta(_ruta_de(nodo, locales), modulo):
                    cambio = True

                for nombre in nombres(nodo) & set(parametros):

                    donde = escritoras.setdefault(funcion.name, set())

                    if nombre not in donde:
                        donde.add(nombre)
                        cambio = True

            # 2. LLAMADAS A ESCRITORAS YA CONOCIDAS.
            for nodo in ast.walk(funcion):

                if not isinstance(nodo, ast.Call):
                    continue

                llamada = nodo.func

                llamado = (
                    llamada.attr
                    if isinstance(llamada, ast.Attribute)
                    else getattr(llamada, "id", None)
                )

                if llamado not in escritoras:
                    continue

                for _, otra, suyos in funciones:

                    if otra.name != llamado:
                        continue

                    for cual in escritoras[llamado]:

                        if cual not in suyos:
                            continue

                        indice = suyos.index(cual)

                        argumento = (
                            nodo.args[indice]
                            if indice < len(nodo.args)
                            else None
                        )

                        for clave in nodo.keywords:
                            if clave.arg == cual:
                                argumento = clave.value

                        if argumento is None:
                            continue

                        if apunta(_ruta_de(argumento, locales), modulo):
                            cambio = True

                        for nombre in nombres(argumento) & set(parametros):

                            donde = escritoras.setdefault(
                                funcion.name, set()
                            )

                            if nombre not in donde:
                                donde.add(nombre)
                                cambio = True

        # 3. Y LO QUE SE ESCRIBE FUERA DE TODA FUNCION.
        for modulo, arbol in arboles.items():

            for nodo in _nodos_que_se_escriben(arbol):

                if apunta(_ruta_de(nodo, constantes[modulo]), modulo):
                    cambio = True

        if not cambio:
            break

    return {ruta: quienes for ruta, quienes in escritos.items() if quienes}


def sin_clasificar(raiz=None) -> dict:
    """
    Lo que el codigo escribe y nadie ha dicho si es libro o cache.

    Es lo que mira `test_todo_libro_escrito_esta_en_la_lista`.
    Vacio es lo correcto.
    """

    ya = clasificados()

    return {
        ruta: quienes
        for ruta, quienes in escritos_por_el_codigo(raiz).items()
        if ruta not in ya
    }
