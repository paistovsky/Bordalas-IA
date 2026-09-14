"""
El vestuario libre: los que no tienen dueño, y cuáles nos valen.

EL PUNTO CIEGO (14/09/2026)

    Pepe no puede querer a nadie que no este HOY en el
    escaparate. Su universo son los veinte que el Computer saca
    cada mañana. Un jugador libre que hoy no sale no existe: no
    esta descartado, no esta valorado, no esta en ninguna lista.

    Medido el 14/09:

        570 jugadores en el catalogo
        117 con dueño  +  453 LIBRES

    Y el que mas duele:

        delanteros LIBRES con 20 puntos o mas          19
        el mejor delantero del escaparate de ese dia   14 puntos

    Nuestra delantera ese dia: Yamal 45, Cepeda 17, Jutgla 14,
    Pablo Duran 9.

QUE ES ESTO

    La lista de la compra. Catalogo menos las ocho plantillas,
    calculada en cada vuelta. Es un calculo COMPLETO: no depende
    de que nadie escriba un articulo ni de que el Computer saque
    a nadie.

ESTO NO PUJA. NI UNA.

    Es una lista para MIRAR. No llama a ningun ejecutor, no
    importa ninguno, y no escribe nada en ninguna parte. Hay una
    guardia que recorre el arbol de este fichero y lo comprueba:
    `test_la_lista_no_puja`.

    Un jugador marcado `vigilado` tampoco esta autorizado a
    nada. La marca cambia DONDE SE VE, no si se puja: cuando
    aparezca en el mercado pasa por el mismo liston que
    cualquier otro.

COMO SE ORDENA, Y POR QUE NO POR PRIMA DE REVENTA

    Por lo que nos suma contra la vara —el peor titular nuestro
    de su posicion— y por lo que nos añade cada millon.

    La prima de reventa ordena por "cual se revende mejor", que
    es otra pregunta y la que ya contesta el carril.

EL FILTRO QUE EVITA LA LISTA DE PORTEROS SUPLENTES

    `calidad_precio` a pelo premia lo barato: un jugador de
    150.000 EUR que nos sume +2 sale a 13,3 puntos por millon y
    se pone por delante de uno que nos sume +27.

    Por eso entran SOLO los que nos suman de verdad y han jugado
    lo suficiente para que sus puntos digan algo. Los dos cortes
    van publicados en la salida: no son secretos y no estan
    calibrados, estan puestos para que la lista se pueda mirar.

REGLA 23

    No lee estado: la liga, el mercado y los topes entran por la
    puerta. Quien la llama es quien tiene la foto delante.
"""

from __future__ import annotations


# Cuantos se enseñan con nombre. El dueño pidio veinte.
LOS_QUE_SE_ENSEÑAN = 20

# Por debajo de esto, sus puntos no dicen nada todavia. Es el
# mismo corte que ya usa `toda_la_liga` para no llamar chollo a
# quien ha jugado un partido.
PARTIDOS_PARA_JUZGAR = 3

# Y tiene que sumarnos de verdad: la vara es el peor titular
# nuestro de su posicion, asi que +0 es "igual que el que ya
# tenemos" y no es un motivo para nada.
NOS_SUMA_MINIMO = 1

POSICIONES = {1: "POR", 2: "DEF", 3: "MED", 4: "DEL"}


def safe_int(value, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def safe_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _de_las_ocho_plantillas(nuestra_plantilla, managers) -> set:
    """Todos los que YA tienen dueño. Nunca lanza.

    LAS OCHO PLANTILLAS, Y NO LA CAJA DE `toda_la_liga`
    (14/09/2026)

        `toda_la_liga` reparte en `nuestro` / `rival` /
        `computer` / `libre`, y `computer` PISA a `rival`: se
        mira antes. Un jugador que estaba en el escaparate
        cuando se tomo la foto y que YA ha comprado un rival sale
        como `computer`, y de ahi a "libre" hay un paso.

        Medido en la foto del 13/09 contra el censo de rivales
        del 14/09: SEIS de los veinte del escaparate ya tenian
        dueño —Gimenez, Marcos Llorente, Victor Garcia, Maguette
        Gueye, Larrubia y Hjulmand—. El censo de rivales era
        VEINTISEIS HORAS mas nuevo que la foto.

        Recomendar seis jugadores que ya son de otro es
        exactamente el fallo que `_las_ocho_plantillas` vino a
        cazar en el cuadro de al lado: la lista queda MAL Y
        CALLADA.

    Asi que libre se calcula como dice el encargo, al pie de la
    letra: CATALOGO MENOS LAS OCHO PLANTILLAS. Estar hoy en el
    escaparate es una columna, no un dueño.
    """

    con_dueno = set()

    try:

        for jugador in (nuestra_plantilla or []):

            pid = safe_int(
                jugador.get("id")
                if isinstance(jugador, dict)
                else jugador
            )

            if pid:
                con_dueno.add(pid)

        for manager in (managers or []):

            if not isinstance(manager, dict):
                continue

            for jugador in (manager.get("roster") or []):

                pid = safe_int(
                    jugador.get("id")
                    if isinstance(jugador, dict)
                    else jugador
                )

                if pid:
                    con_dueno.add(pid)

        return con_dueno

    except Exception:                               # noqa: BLE001
        return con_dueno


def el_vestuario_libre(
    liga: dict | None,
    nuestra_plantilla=None,
    managers=None,
    en_el_mercado=None,
    cuantos: int = LOS_QUE_SE_ENSEÑAN,
) -> dict:
    """Los libres, contados y ordenados. Forma fija. Nunca lanza.

    `liga` es la salida de `toda_la_liga`: ya trae a cada jugador
    con su dueño, lo que nos suma contra la vara y su
    calidad-precio. Aqui no se recalcula nada de eso — se filtra,
    se cuenta y se ordena.

        libres        el recuento entero, sin filtrar
        candidatos    los que nos suman y han jugado bastante
        players       los `cuantos` primeros, con nombre
        vigilados     sus ids, para que el tablero los marque

    SIN LIGA NO HAY LISTA. Si `toda_la_liga` no esta disponible
    —sin catalogo, o sin once y por tanto sin vara— esto devuelve
    `available: False` con el motivo. Una lista de libres sin
    vara seria un listado alfabetico del catalogo.
    """

    vacio = {
        "available": False,
        "total_catalogo": 0,
        "con_dueno": 0,
        "libres": 0,
        "candidatos": 0,
        "players": [],
        "vigilados": [],
        "recuento": {},
        "cortes": {
            "partidos_para_juzgar": PARTIDOS_PARA_JUZGAR,
            "nos_suma_minimo": NOS_SUMA_MINIMO,
        },
        "reason": None,
    }

    try:

        datos = liga if isinstance(liga, dict) else {}

        if not datos.get("available"):
            return {
                **vacio,
                "reason": (
                    "Sin la liga entera no hay vestuario libre "
                    "que mirar: "
                    + str(datos.get("reason") or "no disponible")
                ),
            }

        todos = [
            f
            for f in (datos.get("players") or [])
            if isinstance(f, dict)
        ]

        if not todos:
            return {
                **vacio,
                "reason": (
                    "La liga vino sin jugadores: no se puede "
                    "decir quien esta libre."
                ),
            }

        en_venta = {
            safe_int(p) for p in (en_el_mercado or set())
        }

        # CATALOGO MENOS LAS OCHO PLANTILLAS, al pie de la letra.
        #
        #     No se usa la caja `de_quien` de `toda_la_liga`
        #     porque `computer` pisa a `rival` y colaria como
        #     libre a seis que ya tienen dueño. El motivo entero
        #     esta en `_de_las_ocho_plantillas`.
        con_dueno = _de_las_ocho_plantillas(
            nuestra_plantilla, managers
        )

        # SIN PLANTILLAS NO HAY LISTA. Si no llega ninguna, TODO
        # el catalogo saldria libre —570 de 570— y eso no es una
        # lista de la compra: es el catalogo con otro nombre.
        if not con_dueno:
            return {
                **vacio,
                "total_catalogo": len(todos),
                "reason": (
                    "No llego ninguna plantilla: sin saber quien "
                    "tiene dueño, los 570 saldrian libres y la "
                    "lista diria que se puede fichar a "
                    "cualquiera."
                ),
            }

        libres = [
            f
            for f in todos
            if safe_int(f.get("id")) not in con_dueno
        ]

        # LOS QUE MERECEN MIRARSE. Los dos cortes, y los dos
        # publicados arriba en `cortes`.
        candidatos = [
            f
            for f in libres
            if safe_int(f.get("nos_suma")) >= NOS_SUMA_MINIMO
            and safe_int(f.get("played")) >= PARTIDOS_PARA_JUZGAR
        ]

        # EL ORDEN: calidad-precio primero, y lo que nos suma
        # como desempate.
        #
        #     El dueño lo dijo con estas palabras el 13/09: "cual
        #     es el que mas le interesa por CALIDAD-PRECIO y ese
        #     este el primero".
        #
        #     El desempate por `nos_suma` no es decorativo: entre
        #     dos con la misma calidad-precio, el que mas suma
        #     arregla mas once. Y el tercer criterio es el id,
        #     solo para que el orden no baile entre dos vueltas
        #     con los mismos datos.
        candidatos.sort(
            key=lambda f: (
                -safe_float(f.get("calidad_precio")),
                -safe_int(f.get("nos_suma")),
                safe_int(f.get("id")),
            )
        )

        tope = max(0, safe_int(cuantos))

        primeros = candidatos[:tope]

        players = [
            {
                "id": safe_int(f.get("id")),
                "name": f.get("name"),
                "position": safe_int(f.get("position")),
                "posicion": POSICIONES.get(
                    safe_int(f.get("position")), "?"
                ),
                "team_id": f.get("team_id"),
                "status": f.get("status"),
                "points": safe_int(f.get("points")),
                "played": safe_int(f.get("played")),
                "price": safe_int(f.get("price")),
                "nos_suma": safe_int(f.get("nos_suma")),
                "calidad_precio": f.get("calidad_precio"),
                "puntos_por_millon": f.get("puntos_por_millon"),
                "vara_nombre": f.get("vara_nombre"),
                "vara_puntos": f.get("vara_puntos"),

                # VIGILADO NO ES AUTORIZADO (14/09/2026). Marca
                # donde se ve, no si se puja: cuando aparezca en
                # el mercado pasa por el mismo liston que
                # cualquier otro.
                "vigilado": True,

                # Y si HOY esta en el escaparate, se dice. Vale
                # el conjunto que entra por la puerta y tambien
                # la caja en que lo dejo `toda_la_liga`: si el
                # llamante no pasa el mercado, la marca sigue
                # saliendo.
                "en_el_mercado": (
                    safe_int(f.get("id")) in en_venta
                    or f.get("de_quien") == "computer"
                ),
            }
            for f in primeros
        ]

        por_posicion = {}

        for f in libres:
            clave = POSICIONES.get(
                safe_int(f.get("position")), "?"
            )
            por_posicion[clave] = por_posicion.get(clave, 0) + 1

        con_dueno = len(todos) - len(libres)

        return {
            "available": True,
            "total_catalogo": len(todos),
            "con_dueno": con_dueno,
            "libres": len(libres),
            "candidatos": len(candidatos),
            "players": players,
            "vigilados": [p["id"] for p in players],
            "recuento": {
                "por_posicion": por_posicion,
                "nos_mejoran": len([
                    f
                    for f in libres
                    if safe_int(f.get("nos_suma")) > 0
                ]),
                "en_el_mercado_hoy": len([
                    p for p in players if p["en_el_mercado"]
                ]),
            },
            "cortes": {
                "partidos_para_juzgar": PARTIDOS_PARA_JUZGAR,
                "nos_suma_minimo": NOS_SUMA_MINIMO,
            },
            "reason": (
                f"{len(libres)} libres de {len(todos)} del "
                f"catalogo. {len(candidatos)} nos suman y han "
                f"jugado {PARTIDOS_PARA_JUZGAR}+ partidos; se "
                f"enseñan los {len(players)} primeros por "
                f"calidad-precio. Esta lista NO puja."
            ),
        }

    except Exception as error:                      # noqa: BLE001
        return {
            **vacio,
            "reason": (
                f"No se pudo construir el vestuario libre: "
                f"{type(error).__name__}: {error}"
            ),
        }
