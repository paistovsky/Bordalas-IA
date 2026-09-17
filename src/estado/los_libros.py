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
