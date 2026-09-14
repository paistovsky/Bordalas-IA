"""
El once que de verdad jugo, anotado antes del primer partido.

SINTOMA (14/09/2026)

    El marcador lleva siete jornadas observadas y CERO fiables.
    Todas descartadas por lo mismo:

        "No se anoto que once jugo esa jornada."

    Sin marcador, "mejorar el once" no tiene ningun numero que
    oponer a "+2 % de prima al revender", asi que pierde todas
    las discusiones internas — aunque sea la via buena.

CAUSA

    `marcador.observar()` anota la alineacion EN CADA VUELTA y
    sobreescribe. La que sobrevive es la ultima que se escribio,
    que puede ser:

        de mucho antes del partido, si el ciclo se paro
        de despues de empezar, si el dueño la cambio a mano
        de ninguna parte, si esa jornada no corrio ningun ciclo

    Tres formas distintas de anotar algo que no es el once que
    jugo, y ninguna se distingue de las otras al mirarlo.

LO QUE HACE ESTE LIBRO

    Una entrada por jornada, escrita en la ULTIMA VUELTA ANTES
    DEL PRIMER PARTIDO, y nunca reescrita despues.

    A partir de ese momento el once ya no puede cambiar sin que
    Biwenger lo sepa, asi que lo que hay ahi es lo que jugo.

EL ONCE DE BIWENGER, NO EL NUESTRO

    Se anota lo que Biwenger tiene puesto, NO la recomendacion
    del motor. Si anotaramos la nuestra y el dueño la cambiara a
    mano, el marcador compararia nuestra idea contra los puntos
    que pago Biwenger por OTRO once: volveria a descuadrar, y
    esta vez sin enterarnos, porque los once nombres estarian
    ahi y pareceria que cuadra.

Y DE LOS DOS SITIOS DE BIWENGER, EL VIVO

    Biwenger publica nuestra alineacion en dos sitios, y NO
    dicen lo mismo. Medido en la foto del 13/09 a las 17:17:

        standings[mi].lineup   4-4-2, fechado el 08/09 05:20
        user_lineup.lineup     3-5-2, fechado el 13/09 06:26

    Cinco dias de diferencia y once nombres distintos. El vivo es
    `user_lineup`; el de `standings` va por detras.

    Esto importa mas de lo que parece: `marcador.observar()` lee
    el de `standings`, asi que lleva anotando una alineacion
    vieja. Es la explicacion mas probable de "el once que
    anotamos no es el que jugo" — el descuadre que tiene el
    marcador a cero jornadas fiables.

    NO SE TOCA `observar()` EN ESTE ENCARGO. Queda dicho aqui y
    en el informe.

LO QUE NO SE HACE

    NO SE RECONSTRUYEN LAS JORNADAS PERDIDAS. Estan perdidas. Un
    once reconstruido a ojo daria una nota inventada, y una nota
    inventada es peor que no tener nota: se usa para decidir.

    La pantalla dice cuantas se perdieron y desde cual se mide.

REGLA 23 Y DOCTRINA 50

    Ni la hora ni la ruta se buscan: las dos entran por la
    puerta. Sin hora no se anota nada — un respaldo que mira el
    reloj falla solo a medianoche.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


LIBRO = (
    Path("data")
    / "intelligence"
    / "onces_de_la_jornada.jsonl"
)

# Cuantos jugadores tiene un once. Biwenger no acepta otra cosa,
# asi que un numero distinto es una foto a medio cargar y no un
# once: se rechaza en vez de guardarlo.
SON_ONCE = 11


def safe_int(value, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def ids_del_once(once) -> list:
    """
    Los once ids, venga la lista como venga.

    DOS FORMAS, Y LAS DOS LLEGAN (14/09/2026)

        `standings[mi].lineup.players` trae ids sueltos:

            [17482, 1599, 1721, ...]

        `user_lineup.data.lineup.players` trae la ficha entera:

            [{"id": 17482, "name": "Dituro", ...}, ...]

        Tratar la segunda como la primera da `safe_int(dict)` =
        0 en los once, se filtran los ceros, y el once sale
        VACIO. No es un fallo ruidoso: es una jornada que no se
        anota y un motivo que dice "alineacion a medias" cuando
        la alineacion estaba entera.
    """

    salida = []

    for jugador in ((once or {}).get("players") or []):

        pid = safe_int(
            jugador.get("id")
            if isinstance(jugador, dict)
            else jugador
        )

        if pid:
            salida.append(pid)

    return salida


def once_del_dueno(snapshot) -> dict:
    """La alineacion vigente del dueño. LA FUENTE, en singular.

    Forma fija —siempre un dict— y nunca lanza.

    POR QUE ESTA FUNCION EXISTE (14/09/2026)

        Biwenger publica nuestro once en DOS sitios y no dicen lo
        mismo. Medido en la foto del 13/09 a las 17:17:

            standings[mi].lineup      4-4-2, guardado el 08/09
            user_lineup.data.lineup   3-5-2, guardado el 13/09

        Coinciden 10 de los 11. Cambia el dibujo y cambia un
        nombre: Zubeldia (defensa) por Ruben Garcia (medio),
        coherente con el paso de 4-4-2 a 3-5-2.

        Y el motor leia de los dos: `marcador.observar()` de
        `standings`, el libro de las jornadas de `user_lineup`.
        Dos ideas distintas de "el once de esa jornada" viviendo
        en el mismo sitio.

    POR QUE GANA `user_lineup`, Y NO ES CUESTION DE GUSTO

        Es la alineacion VIGENTE del dueño, la que Biwenger usa
        para pagar. `standings` es una copia que se quedo parada
        el 08/09: cinco dias mirando un once que ya no existia.

    UNA FUENTE, UN SITIO. Quien quiera el once del dueño llama
    aqui. Si algun dia cambia la ruta, cambia en una linea.
    """

    try:
        return (
            (
                (snapshot or {}).get("user_lineup") or {}
            ).get("data")
            or {}
        ).get("lineup") or {}

    except (AttributeError, TypeError):
        return {}


def _momento(valor):
    """Una marca de tiempo con zona, o `None`. Nunca lanza."""

    if valor is None:
        return None

    if isinstance(valor, datetime):
        cuando = valor

    else:
        try:
            cuando = datetime.fromisoformat(str(valor))

        except (TypeError, ValueError):
            return None

    if cuando.tzinfo is None:
        return cuando.replace(tzinfo=timezone.utc)

    return cuando


def _ruta(ruta) -> Path:
    return Path(ruta) if ruta else LIBRO


def onces_anotados(ruta=None) -> dict:
    """
    Lo que hay en el libro, por jornada. Nunca lanza.

    Si una jornada tuviera dos lineas —no deberia, pero un
    fichero se puede editar a mano— gana la PRIMERA: es la que se
    escribio antes del partido, y la segunda solo puede ser
    posterior.
    """

    libro = _ruta(ruta)

    anotados = {}

    try:
        if not libro.exists():
            return anotados

        for linea in libro.read_text(
            encoding="utf-8"
        ).splitlines():

            linea = linea.strip()

            if not linea:
                continue

            try:
                fila = json.loads(linea)

            except json.JSONDecodeError:
                continue

            if not isinstance(fila, dict):
                continue

            ronda = safe_int(fila.get("round_id"))

            if ronda and ronda not in anotados:
                anotados[ronda] = fila

        return anotados

    except OSError:
        return anotados


def hay_que_anotar(
    round_id,
    primer_partido,
    ahora,
    once=None,
    desde=None,
    ruta=None,
) -> dict:
    """
    ¿Toca anotar el once de esta jornada? Forma fija.

    Seis puertas, y cada una dice cual es. Nunca lanza.

    LA VENTANA, Y POR QUE NO VALE ANOTAR ANTES

        La primera version anotaba en cuanto veia la jornada. En
        la foto del 13/09 eso eran SIETE MIL TRESCIENTOS MINUTOS
        antes del primer partido: cinco dias en los que el dueño
        puede cambiar la alineacion veinte veces.

        Un once congelado cinco dias antes no prueba nada, que es
        exactamente el problema que este libro venia a arreglar.

        `desde` es el momento a partir del cual se anota. Sale
        del `safety_deadline` que ya calcula el motor de
        calendario — no se inventa otro reloj aqui.
    """

    salida = {
        "anota": False,
        "round_id": safe_int(round_id),
        "reason": None,
    }

    ronda = safe_int(round_id)

    if not ronda:
        return {
            **salida,
            "reason": "El snapshot no trae jornada.",
        }

    # 1. LA HORA ENTRA POR LA PUERTA (doctrina 50).
    cuando = _momento(ahora)

    if cuando is None:
        return {
            **salida,
            "reason": (
                "No se ha pasado la hora: sin ella no se puede "
                "saber si el partido ya ha empezado."
            ),
        }

    # 2. SIN HORA DE PARTIDO NO SE ANOTA.
    #
    #     Anotar "por si acaso" es exactamente lo que ya se hace
    #     y lo que no funciona: lo que da valor a esta entrada es
    #     saber que se escribio ANTES.
    arranque = _momento(primer_partido)

    if arranque is None:
        return {
            **salida,
            "reason": (
                "No se sabe cuando empieza el primer partido de "
                "la jornada: sin esa hora, anotar el once no "
                "prueba que sea el que jugo."
            ),
        }

    # 3. YA EMPEZADO, NO SE TOCA.
    if cuando >= arranque:
        return {
            **salida,
            "reason": (
                f"El primer partido ya empezo "
                f"({arranque.isoformat()}): lo que haya puesto "
                f"ahora no es necesariamente lo que jugo."
            ),
        }

    # 4. LA VENTANA. Antes de ella, todavia puede cambiar.
    apertura = _momento(desde)

    if apertura is None:
        return {
            **salida,
            "reason": (
                "No se ha pasado desde cuando se puede anotar: "
                "sin esa ventana, el once se congelaria dias "
                "antes y el dueño aun podria cambiarlo."
            ),
        }

    if cuando < apertura:
        return {
            **salida,
            "reason": (
                f"Todavia no toca: la ventana se abre a las "
                f"{apertura.isoformat()} y faltan "
                f"{round((apertura - cuando).total_seconds() / 60)}"
                f" min."
            ),
        }

    # 5. IDEMPOTENTE: una jornada, un once.
    ya = onces_anotados(ruta)

    if ronda in ya:
        return {
            **salida,
            "reason": (
                f"La jornada {ronda} ya esta anotada "
                f"({ya[ronda].get('anotado_en')})."
            ),
        }

    # 6. UN ONCE A MEDIAS NO ES UN ONCE (regla 24).
    #
    #     Guardar ocho nombres dejaria una entrada que parece
    #     buena y da una nota coja. Mejor no anotar y que la
    #     pantalla diga que falta.
    jugadores = ids_del_once(once)

    if len(jugadores) != SON_ONCE:
        return {
            **salida,
            "reason": (
                f"El once trae {len(jugadores)} jugadores y no "
                f"{SON_ONCE}: no se anota una alineacion a "
                f"medias."
            ),
        }

    return {
        "anota": True,
        "round_id": ronda,
        "reason": (
            f"Faltan "
            f"{round((arranque - cuando).total_seconds() / 60)} "
            f"min para el primer partido y la jornada {ronda} no "
            f"esta anotada."
        ),
    }


def anotar_el_once(
    round_id,
    once,
    primer_partido,
    ahora,
    desde=None,
    ruta=None,
) -> dict:
    """
    Escribe una linea con el once de esta jornada. Forma fija.

    Nunca lanza. Si no toca, lo dice y no escribe: este libro es
    la unica prueba de que el once se fijo antes del partido, y
    una linea de mas lo convierte en otra memoria mas.
    """

    salida = {
        "anotado": False,
        "round_id": safe_int(round_id),
        "reason": None,
    }

    try:
        veredicto = hay_que_anotar(
            round_id,
            primer_partido,
            ahora,
            once=once,
            desde=desde,
            ruta=ruta,
        )

        if not veredicto["anota"]:
            return {**salida, "reason": veredicto["reason"]}

        cuando = _momento(ahora)

        arranque = _momento(primer_partido)

        fila = {
            "round_id": safe_int(round_id),
            # BIWENGER LA LLAMA `type`. `formation` es como la
            # llamamos nosotros: se aceptan las dos o la fila
            # sale con la formacion en blanco y nadie se entera.
            "formation": (
                (once or {}).get("formation")
                or (once or {}).get("type")
            ),
            "players": ids_del_once(once),
            "anotado_en": cuando.isoformat(),
            "primer_partido": arranque.isoformat(),
            "minutos_de_margen": round(
                (arranque - cuando).total_seconds() / 60
            ),

            # Desde cuando se podia anotar. Deja la ventana
            # escrita en la propia linea: el dia que alguien la
            # cambie, las viejas siguen diciendo cual tenian.
            "ventana_desde": _momento(desde).isoformat(),

            # CUANDO LO GUARDO EL DUEÑO. Biwenger lo publica en
            # `lineup.date`, y es la prueba de que el once que se
            # congela es el vigente y no uno de hace cinco dias.
            "guardado_en": (
                datetime.fromtimestamp(
                    safe_int((once or {}).get("date")),
                    timezone.utc,
                ).isoformat()
                if safe_int((once or {}).get("date"))
                else None
            ),

            # DE DONDE SALE. El dia que alguien cambie la fuente,
            # las lineas viejas siguen diciendo cual era la suya.
            #
            #     `USER_LINEUP` es el once vivo. El de
            #     `standings` va cinco dias por detras: medido el
            #     13/09, decia 4-4-2 del 08/09 cuando el vigente
            #     era un 3-5-2 del 13/09.
            "origen": "BIWENGER_USER_LINEUP",
        }

        libro = _ruta(ruta)

        libro.parent.mkdir(parents=True, exist_ok=True)

        with libro.open("a", encoding="utf-8") as mano:
            mano.write(
                json.dumps(fila, ensure_ascii=False) + "\n"
            )

        return {
            "anotado": True,
            "round_id": fila["round_id"],
            "players": fila["players"],
            "formation": fila["formation"],
            "minutos_de_margen": fila["minutos_de_margen"],
            "reason": (
                f"Once de la jornada {fila['round_id']} anotado a "
                f"{fila['minutos_de_margen']} min del primer "
                f"partido."
            ),
        }

    except Exception as error:                      # noqa: BLE001
        return {
            **salida,
            "reason": (
                f"No se pudo anotar el once: "
                f"{type(error).__name__}: {error}"
            ),
        }


def lo_que_se_perdio(observadas, ruta=None) -> dict:
    """
    Cuantas jornadas no tienen once anotado, y desde cual se mide.

    SE CUENTA, NO SE ESCRIBE (regla 18). "6 jornadas perdidas"
    escrito a mano es verdad hoy y mentira la semana que viene, y
    justo entonces nadie estara mirando este numero.

    Las perdidas son IRRECUPERABLES y se dice: reconstruir un
    once a ojo daria una nota inventada.
    """

    try:
        anotadas = set(onces_anotados(ruta))

        rondas = sorted(
            {
                safe_int(r)
                for r in (observadas or [])
                if safe_int(r)
            }
        )

        sin_once = [r for r in rondas if r not in anotadas]

        desde = min(anotadas) if anotadas else None

        return {
            "available": True,
            "observadas": len(rondas),
            "anotadas": len([r for r in rondas if r in anotadas]),
            "sin_once": sin_once,
            "irrecuperables": len(sin_once),
            "desde": desde,
            "reason": (
                (
                    f"{len(sin_once)} jornada(s) sin once "
                    f"anotado, irrecuperables. La medicion "
                    f"empieza en la jornada {desde}."
                )
                if sin_once and desde
                else (
                    f"{len(sin_once)} jornada(s) sin once "
                    f"anotado, irrecuperables. Todavia no hay "
                    f"ninguna anotada: la medicion no ha "
                    f"empezado."
                )
                if sin_once
                else (
                    f"Las {len(rondas)} jornadas observadas "
                    f"tienen su once anotado."
                )
            ),
        }

    except Exception as error:                      # noqa: BLE001
        return {
            "available": False,
            "observadas": 0,
            "anotadas": 0,
            "sin_once": [],
            "irrecuperables": 0,
            "desde": None,
            "reason": (
                f"No se pudo contar lo que falta: "
                f"{type(error).__name__}: {error}"
            ),
        }
