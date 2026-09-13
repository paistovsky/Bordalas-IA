"""
El libro de pujas: que pusimos, y como acabo.

SINTOMA

    El dueño dice que pierde muchas pujas. El sistema no registra
    ninguna: en el ledger, "Pepe Bordalas" tiene lost_bids = 0, y
    nuestro user_id no aparece como perdedor en ninguna de las 48
    subastas del tablon. El autopilot escribe SPECULATION_BID_PLACED y
    ahi se acaba la historia: no hay campo de resultado.

CAUSA

    Poner la puja y saber quien la gano son dos momentos distintos,
    separados por horas. Nadie los estaba cosiendo.

CONSECUENCIA

    Sin ese cosido no se puede calibrar nada. "Perder por un 2 %" y
    "perder por un 40 %" son dos problemas opuestos -uno se arregla
    subiendo un pelo, el otro dice que el jugador no era para
    nosotros- y a ojo no se distinguen. Este libro es la materia
    prima: primero medir, despues decidir.

    No decide nada. Solo apunta.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

LEDGER_PATH = Path("data/trading/bid_outcome_ledger.json")

# El tablon que persiste board_history_collector. Es una LISTA pelada de
# eventos, no un dict con "events": si algun dia cambia, _operaciones
# traga las dos formas.
BOARD_EVENTS_PATH = Path("data/rival_intelligence/board_events.json")

VERSION = "V1.0"

# El tablon de Biwenger solo publica las dos mejores pujas perdedoras
# de cada subasta. Si nuestra puja no sale ahi, sabemos que perdimos
# pero no por cuanto: quedan como LOST sin margen, y se cuentan aparte
# para no ensuciar la media.
PUJAS_PERDEDORAS_PUBLICADAS = 2

# Una puja sin resolver despues de esto se da por perdida de vista. El
# mercado del Computer se resetea a diario; 72 h es de sobra.
HORAS_PARA_CADUCAR = 72


def _ahora() -> str:
    return datetime.now(timezone.utc).isoformat()


def _libro_vacio() -> dict:
    return {"version": VERSION, "bids": {}}


def load_ledger(path: Path | None = None) -> dict:
    ruta = path or LEDGER_PATH
    try:
        libro = json.loads(ruta.read_text(encoding="utf-8"))
    except Exception:
        return _libro_vacio()

    if not isinstance(libro, dict) or "bids" not in libro:
        return _libro_vacio()

    if not isinstance(libro.get("bids"), dict):
        libro["bids"] = {}

    libro.setdefault("version", VERSION)
    return libro


def save_ledger(libro: dict, path: Path | None = None) -> bool:
    """Nunca lanza: perder una anotacion no puede tumbar un ciclo."""
    ruta = path or LEDGER_PATH
    try:
        ruta.parent.mkdir(parents=True, exist_ok=True)
        ruta.write_text(
            json.dumps(libro, ensure_ascii=False, indent=1),
            encoding="utf-8",
        )
        return True
    except Exception:
        return False


def safe_int(value, default: int = 0) -> int:
    """Un entero o el defecto. Nunca lanza."""

    try:
        return int(value or 0)

    except (TypeError, ValueError):
        return default


def _clave(player_id: int, puesta_en: str) -> str:
    return f"{int(player_id)}:{puesta_en}"


def record_bid(
    player_id: int,
    amount: int,
    *,
    player_name: str | None = None,
    our_value: int | None = None,
    win_probability: float | None = None,
    market_price: int | None = None,
    recommended_bid: int | None = None,
    intent: str | None = None,
    target_source: str | None = None,
    seller_user_id: int | None = None,

    # EL RITMO CON EL QUE SE COMPRO (08/09/2026)
    #
    # Desde el 08/09 una compra especulativa solo se hace con un
    # ritmo observado del jugador. Apuntarlo aqui es lo unico que
    # permitira contestar dentro de una semana a "¿comprar rachas
    # funciono?", en vez de discutirlo.
    market_rate_percent_per_day: float | None = None,
    market_gate: str | None = None,
    trend_days: int | None = None,

    placed_at: str | None = None,
    ledger: dict | None = None,
    path: Path | None = None,
    save: bool = True,
) -> dict:
    """
    Apunta una puja recien colocada, en estado PENDIENTE.

    `our_value` y `win_probability` pueden venir vacios: las pujas del
    respaldo legacy (target_source == "SPECULATION_SCORING") no traen
    fila de adquisicion. Se apuntan igual; simplemente no serviran para
    calibrar la curva.
    """

    libro = ledger if ledger is not None else load_ledger(path)
    puesta_en = placed_at or _ahora()

    libro["bids"][_clave(player_id, puesta_en)] = {
        "player_id": int(player_id),
        "player_name": player_name,
        "amount": int(amount),
        "our_value": int(our_value) if our_value is not None else None,
        "win_probability": (
            float(win_probability) if win_probability is not None else None
        ),
        "market_price": int(market_price) if market_price is not None else None,
        "recommended_bid": (
            int(recommended_bid) if recommended_bid is not None else None
        ),
        "intent": intent,
        "target_source": target_source,

        # Con que se compro, para poder puntuar la regla despues.
        "market_rate_percent_per_day": (
            float(market_rate_percent_per_day)
            if market_rate_percent_per_day is not None
            else None
        ),
        "market_gate": market_gate,
        "trend_days": trend_days,
        # None = mercado del Computer; un id = puja a un rival.
        "seller_user_id": seller_user_id,
        "placed_at": puesta_en,
        "outcome": "PENDING",
        "resolved_at": None,
        "winning_amount": None,
        # Cuanto nos gano el ganador. Positivo = nos superaron por eso.
        "margin": None,
        "event_id": None,
    }

    if save:
        save_ledger(libro, path)

    return libro


def _operaciones(board):
    """
    Aplana el tablon a (event_id, fecha_epoch, operacion).

    Acepta la lista pelada que escribe board_history_collector y
    tambien un dict con "events", que es lo que devuelve el colector
    en vivo.
    """

    if isinstance(board, dict):
        eventos = board.get("events") or []
    elif isinstance(board, list):
        eventos = board
    else:
        return

    for evento in eventos:
        if not isinstance(evento, dict):
            continue
        if evento.get("type") not in (None, "market"):
            continue

        event_id = evento.get("event_id") or evento.get("id")
        fecha = evento.get("date")

        for operacion in evento.get("content") or []:
            if isinstance(operacion, dict):
                yield event_id, fecha, operacion


def _epoch(iso: str) -> float:
    try:
        return datetime.fromisoformat(iso).timestamp()
    except Exception:
        return 0.0


# ============================================================
# EL RESET QUE RESUELVE UNA PUJA
# ============================================================
#
# SINTOMA (12/09/2026)
#
#     Cuatro pujas de la misma tanda en la ventana del 12/09:
#
#         04:46:55  Caceres      1.503.751  -> PENDING
#         04:46:55  Fortuño        150.376  -> WON
#         04:46:55  Diego Conde    240.601  -> WON
#         04:52:15  Sotelo       1.604.001  -> PENDING
#
#     Las cuatro se resolvieron a las 07:00 del mismo dia.
#     Caceres y Sotelo no estan en la plantilla: se perdieron. El
#     libro decia PENDING.
#
#     Publicado: `lost: 0`, `win_rate: 1.0` sobre 5 pujas, en una
#     liga donde el 76 % de las subastas estan disputadas.
#
# CAUSA
#
#     El detector sabia reconocer una VICTORIA —el jugador
#     aparece en una operacion del tablon comprada por
#     nosotros— y no tenia forma de reconocer una DERROTA cuando
#     el tablon no trae la operacion: sin candidata, se quedaba
#     PENDING hasta caducar a UNKNOWN 72 horas despues.
#
#     Es el septimo caso del mismo patron: un valor por defecto
#     se traga el caso importante. Y encima el que se traga es el
#     UNICO QUE ENSEÑA ALGO — ganar no dice cuanto hay que pujar;
#     perder, si.
#
# LA REGLA, QUE NO NECESITA EL TABLON
#
#     Una puja cuyo reset YA HA PASADO y cuyo jugador NO esta en
#     la plantilla es LOST. No hay tercera opcion: o lo tienes o
#     no lo tienes.
#
#     PENDING se queda solo para las pujas cuyo reset aun no ha
#     llegado.
RESET_MADRID_MINUTOS = 7 * 60


def _reset_que_la_resuelve(placed_at: str):
    """
    El instante UTC del reset que resuelve una puja puesta a esa
    hora. `None` si no se sabe.

    Las 07:00 de Madrid siguientes a la puja. Se apoya en la zona
    de silencio, que ya sabe de Madrid y de horarios de verano,
    para no escribir aqui un desfase a mano (doctrina 35).
    """

    try:
        from datetime import timedelta

        from src.analysis.zona_de_silencio import _hora_de_madrid

        puesta = datetime.fromisoformat(placed_at)

        if puesta.tzinfo is None:
            puesta = puesta.replace(tzinfo=timezone.utc)

        madrid = _hora_de_madrid(puesta)

        minutos = madrid.hour * 60 + madrid.minute

        dias = 0 if minutos < RESET_MADRID_MINUTOS else 1

        reset_madrid = (madrid + timedelta(days=dias)).replace(
            hour=RESET_MADRID_MINUTOS // 60,
            minute=RESET_MADRID_MINUTOS % 60,
            second=0,
            microsecond=0,
        )

        # Y DE VUELTA A UTC, QUE NO ES LO MISMO.
        #
        #     `_hora_de_madrid` devuelve la HORA DE PARED de
        #     Madrid, todavia etiquetada UTC. Devolverla tal cual
        #     daria "07:00+00:00", que como instante son las
        #     09:00 de Madrid: dos horas tarde, y la puja se
        #     quedaria sin resolver toda la mañana.
        #
        #     Es la doctrina 35 otra vez —una hora sin zona es un
        #     dato con dos nombres— y aqui las dos caras del
        #     mismo numero se llamaban igual.
        from src.analysis.market_clock import madrid_offset_hours

        return reset_madrid - timedelta(
            hours=madrid_offset_hours(puesta)
        )

    except Exception:                               # noqa: BLE001
        return None


def _en_la_plantilla(roster) -> set:
    """
    Los ids de nuestra plantilla. `None` si no se sabe.

    DISTINGUIR "NO ESTA" DE "NO SE SABE" ES TODO EL PUNTO
    (doctrina 36). Si el roster no llega, esta funcion devuelve
    `None` y NO se marca nada como perdido: un libro que inventa
    derrotas es peor que uno que no mide.
    """

    if roster is None:
        return None

    ids = set()

    for jugador in roster or []:

        if isinstance(jugador, dict):
            try:
                ids.add(int(jugador.get("id")))
            except (TypeError, ValueError):
                continue

    # Regla 24: una plantilla vacia es sospechosa -tenemos 15- y
    # tratarla como "no tiene a nadie" marcaria TODO como
    # perdido. Sin plantilla, no se sabe.
    return ids or None


# ============================================================
# EL LIBRO RECOGE LO QUE VE
# ============================================================
#
# SINTOMA (12/09/2026, noche)
#
#     Una puja viva por Trent de 2.760.000, puesta a las 16:45
#     con el codigo de antes de que el carril aprendiera a
#     anotar. No estaba en ningun libro, y se resolvia a las
#     07:00 del dia siguiente: el primer viaje del carril se
#     habria cerrado sin quedar registrado.
#
#     Anotar AL PUJAR no la recoge. Ya se pujo.
#
# LA REGLA
#
#     Si el tablon publica una puja viva nuestra que no esta en
#     el libro, EL LIBRO LA ANOTA. Con el importe del tablon, no
#     con el que el codigo pujaria hoy.
#
#     Es mas honesto que anotar al pujar: el libro se llena de lo
#     que OCURRIO, no de lo que el codigo creyo hacer. Una puja
#     hecha a mano, una puesta por una version anterior o una que
#     fallo al apuntarse entran igual.
#
# EL ORIGEN, SOLO SI SE PUEDE PROBAR
#
#     De una puja recogida del tablon no se sabe de que via
#     salio. Se marca DESCONOCIDO salvo que haya prueba: el libro
#     del carril, que se escribe en el mismo instante en que se
#     puja. Inventar el origen es peor que no tenerlo — el dia
#     que se comparen las dos vias, una marca inventada mueve el
#     resultado y nadie lo sabra.
ORIGEN_SIN_PROBAR = "DESCONOCIDO"

LIBRO_DEL_CARRIL = (
    Path("data") / "trading" / "libro_del_carril.jsonl"
)


def _origen_probado(player_id: int, amount: int, ruta=None):
    """
    De que via salio esta puja. Solo si se puede PROBAR.

    El carril escribe su propio libro en el mismo instante en que
    puja. Si ahi consta este jugador con este importe, el origen
    esta probado. Si no, DESCONOCIDO.

    Nunca lanza.
    """

    try:
        destino = ruta or LIBRO_DEL_CARRIL

        if not destino.exists():
            return ORIGEN_SIN_PROBAR

        for linea in destino.read_text(
            encoding="utf-8"
        ).splitlines():

            if not linea.strip():
                continue

            fila = json.loads(linea)

            if int(
                fila.get("player_id") or 0
            ) == int(player_id) and int(
                fila.get("amount") or 0
            ) == int(amount):
                return str(
                    fila.get("marca") or ORIGEN_SIN_PROBAR
                )

        return ORIGEN_SIN_PROBAR

    except Exception:                               # noqa: BLE001
        return ORIGEN_SIN_PROBAR


def _cuando_se_puso(created):
    """La fecha de la oferta del tablon, en ISO. None si no se sabe."""

    try:
        if created is None:
            return None

        return datetime.fromtimestamp(
            int(created), timezone.utc
        ).isoformat()

    except Exception:                               # noqa: BLE001
        return None


def _nombre_en_la_foto(snapshot, player_id):
    """El nombre del jugador, si la foto lo trae. None si no."""

    try:
        # OJO AL `if`: hay que exigir que HAYA nombre, no solo
        # que el id case. Las ventas del mercado traen
        # `{"id": 1602}` a secas, asi que un `return
        # jugador.get("name")` sale con None y no llega nunca al
        # catalogo, que es donde estan los nombres.
        for venta in (
            (snapshot.get("market") or {}).get("sales") or []
        ):
            jugador = venta.get("player")

            if (
                isinstance(jugador, dict)
                and safe_int(jugador.get("id"))
                == int(player_id)
                and jugador.get("name")
            ):
                return jugador.get("name")

        for jugador in (snapshot.get("my_team") or []):
            if (
                isinstance(jugador, dict)
                and safe_int(jugador.get("id"))
                == int(player_id)
                and jugador.get("name")
            ):
                return jugador.get("name")

        # EL CATALOGO, QUE ES DONDE ESTAN LOS NOMBRES.
        #
        #     Las ventas del mercado traen el jugador sin nombre
        #     -`{"id": 1602, "name": null}`- asi que sin esto el
        #     libro se llenaria de entradas llamadas `None` y
        #     habria que cruzar ids a mano para leerlas.
        catalogo = (
            (snapshot.get("catalog") or {}).get("data") or {}
        ).get("players") or {}

        ficha = None

        if isinstance(catalogo, dict):
            ficha = catalogo.get(str(player_id)) or catalogo.get(
                player_id
            )

        elif isinstance(catalogo, list):
            for x in catalogo:
                if isinstance(x, dict) and safe_int(
                    x.get("id")
                ) == int(player_id):
                    ficha = x
                    break

        if isinstance(ficha, dict) and ficha.get("name"):
            return ficha.get("name")

        return None

    except Exception:                               # noqa: BLE001
        return None


def _lo_que_prueba_el_carril(player_id: int, ruta=None) -> dict:
    """
    Lo que el libro del carril prueba sobre esta compra.

    Devuelve `{marca, amount, at}` o `{}`. El carril escribe su
    libro en el mismo instante en que puja, asi que de ahi salen
    las tres cosas que el tablon no sabe: de que via vino, con
    que importe se pujo, y a que hora.

    Nunca lanza.
    """

    try:
        destino = ruta or LIBRO_DEL_CARRIL

        if not destino.exists():
            return {}

        for linea in destino.read_text(
            encoding="utf-8"
        ).splitlines():

            if not linea.strip():
                continue

            fila = json.loads(linea)

            if int(fila.get("player_id") or 0) != int(player_id):
                continue

            return {
                "marca": fila.get("marca"),
                "amount": safe_int(fila.get("amount")),
                "at": fila.get("at"),
            }

        return {}

    except Exception:                               # noqa: BLE001
        return {}


def _compras_del_tablon(board, our_user_id) -> dict:
    """
    Lo que el tablon dice que hemos COMPRADO: {player_id: (importe, fecha_iso)}.

    Del tablon y no de la plantilla: la plantilla dice que lo
    tenemos, el tablon dice CUANTO COSTO y CUANDO. Los jugadores
    del sorteo inicial no aparecen aqui —nadie nos los vendio— y
    por eso esta funcion distingue sola una compra de un regalo.

    Nunca lanza.
    """

    compras = {}

    try:
        # RECORRIDO PROPIO, Y NO `_operaciones`, A PROPOSITO.
        #
        #     `_operaciones` acepta solo eventos `market` —lo que
        #     necesita `reconcile`— y medido el 13/09 sobre el
        #     tablon real, nuestras compras llegan asi:
        #
        #         market     21
        #         transfer    1   <- comprado a un rival
        #
        #     Para "¿que hemos comprado?" las dos cuentan: un
        #     jugador comprado a un manager es tan nuestro como
        #     uno comprado al Computer.
        #
        #     No se toca el filtro de `_operaciones`: cambiarlo
        #     mueve como se resuelven las pujas ya anotadas, y
        #     eso es otra decision. Queda dicho en el informe.
        eventos = (
            board.get("events")
            if isinstance(board, dict)
            else board
        ) or []

        for evento in eventos:

            if not isinstance(evento, dict):
                continue

            if evento.get("type") not in (
                None,
                "market",
                "transfer",
            ):
                continue

            fecha = evento.get("date")

            for operacion in (evento.get("content") or []):

                if not isinstance(operacion, dict):
                    continue


                destino = operacion.get("to")

                if not isinstance(destino, dict):
                    continue

                if safe_int(destino.get("id")) != int(our_user_id):
                    continue

                pid = safe_int(operacion.get("player"))

                if pid <= 0:
                    continue

                cuando = None

                try:
                    cuando = datetime.fromtimestamp(
                        int(fecha), timezone.utc
                    ).isoformat()

                except Exception:                       # noqa: BLE001
                    cuando = None

                # La mas reciente manda: si un jugador se compro,
                # se vendio y se volvio a comprar, la que cuenta es
                # la ultima.
                anterior = compras.get(pid)

                if anterior is None or (
                    cuando and anterior[1] and cuando > anterior[1]
                ):
                    compras[pid] = (
                        safe_int(operacion.get("amount")),
                        cuando,
                    )

        return compras

    except Exception:                               # noqa: BLE001
        return compras


def recoger_compras_de_la_plantilla(
    snapshot,
    board,
    our_user_id,
    *,
    ledger: dict,
    ruta_del_carril=None,
    ruta_de_viajes=None,
) -> dict:
    """
    Un jugador NUESTRO que no esta en el libro es una compra que
    no anotamos.

    SINTOMA (13/09/2026)

        Trent en el banquillo, sin publicar, y el carril sin
        saber que lo tenia. Se gano la puja en el reset de las
        07:00 y `recoger_pujas_vivas` se desplego a las 08:xx:
        para entonces ya no habia puja VIVA que recoger.

        Llego tarde por una hora, y la mitad que falta del primer
        viaje del carril se quedo sin registrar.

    EL AGUJERO ERA DE FORMA, NO DE HORA

        Recoger solo pujas VIVAS deja fuera todo lo que se
        resuelve entre dos despliegues. Mirar LA PLANTILLA no:
        un jugador que tenemos y que el tablon dice que compramos
        es una compra, la viera alguien pujar o no.

        Esta via cierra el agujero para siempre, no solo para
        hoy.

    DE DONDE SALE CADA COSA

        el importe   del TABLON, que es lo que se pago de verdad
        la hora      del libro del carril si lo prueba; si no, la
                     del tablon —que es cuando se resolvio, no
                     cuando se pujo, y se dice—
        el origen    solo si el libro del carril lo prueba

    Y SI VINO DEL CARRIL, SE ABRE EL VIAJE. Un jugador comprado
    para revender que no esta marcado VIAJE es medio viaje: lo
    juzgaria el motor de ofertas de siempre, con la pregunta
    equivocada.

    Forma fija. Nunca lanza.
    """

    salida = {
        "available": False,
        "recogidas": [],
        "viajes_abiertos": [],
        "reason": None,
    }

    try:
        if not snapshot or our_user_id is None:
            return {
                **salida,
                "reason": (
                    "Sin foto o sin saber quienes somos no se "
                    "recoge nada."
                ),
            }

        plantilla = snapshot.get("my_team") or []

        if not plantilla:
            # REGLA 24: una plantilla vacia es una lectura rota
            # -tenemos 15- y tratarla como buena no recogeria
            # nada mientras parece que si.
            return {
                **salida,
                "reason": (
                    "La plantilla llega vacia: no se recoge "
                    "nada, porque eso no es una plantilla sin "
                    "nadie, es una lectura rota."
                ),
            }

        compras = _compras_del_tablon(board, our_user_id)

        ya_estan = {
            int(e.get("player_id") or 0)
            for e in (ledger.get("bids") or {}).values()
            if isinstance(e, dict)
        }

        recogidas = []

        viajes = []

        for ficha in plantilla:

            if not isinstance(ficha, dict):
                continue

            pid = safe_int(ficha.get("id"))

            if pid <= 0 or pid in ya_estan:
                continue

            comprado = compras.get(pid)

            if not comprado:
                # No consta que nos lo vendiera nadie: es del
                # sorteo inicial. No es una compra sin anotar.
                continue

            importe, cuando_del_tablon = comprado

            if importe <= 0:
                continue

            prueba = _lo_que_prueba_el_carril(
                pid, ruta_del_carril
            )

            puesta = prueba.get("at") or cuando_del_tablon

            if not puesta:
                continue

            record_bid(
                pid,
                importe,
                player_name=(
                    ficha.get("name")
                    or _nombre_en_la_foto(snapshot, pid)
                ),
                market_price=_precio_en_la_foto(snapshot, pid),
                target_source=(
                    prueba.get("marca") or ORIGEN_SIN_PROBAR
                ),
                placed_at=puesta,
                ledger=ledger,
                save=False,
            )

            entrada = ledger["bids"][_clave(pid, puesta)]

            # LO TENEMOS: la puja se gano. Eso no es una
            # deduccion, es la plantilla.
            entrada["outcome"] = "WON"

            entrada["margin"] = 0

            entrada["resolved_at"] = cuando_del_tablon

            entrada["resolved_by"] = "EN_LA_PLANTILLA"

            entrada["recorded_by"] = "PLANTILLA"

            # Y si la hora no la prueba el carril, se dice: la
            # del tablon es cuando se RESOLVIO, no cuando se
            # pujo (doctrina 35, un dato con dos nombres).
            entrada["placed_at_is_resolution"] = not prueba.get(
                "at"
            )

            ya_estan.add(pid)

            recogidas.append(
                {
                    "player_id": pid,
                    "name": entrada["player_name"],
                    "amount": importe,
                    "placed_at": puesta,
                    "target_source": entrada["target_source"],
                }
            )

            # SI VINO DEL CARRIL, ES UN VIAJE ABIERTO.
            if str(entrada["target_source"]).upper() == "RENDIJA":

                try:
                    from src.analysis.libro_de_viajes import (
                        abrir,
                    )

                    marca = abrir(
                        player_id=pid,
                        name=entrada["player_name"],
                        position=ficha.get("position"),
                        ruta=ruta_de_viajes,
                    )

                    if marca.get("opened"):
                        viajes.append(
                            {
                                "player_id": pid,
                                "name": entrada["player_name"],
                            }
                        )

                except Exception:                   # noqa: BLE001
                    pass

        return {
            "available": True,
            "recogidas": recogidas,
            "viajes_abiertos": viajes,
            "reason": (
                f"{len(recogidas)} compra(s) de la plantilla que "
                f"no estaban en el libro"
                + (
                    f"; {len(viajes)} viaje(s) abierto(s)."
                    if viajes
                    else "."
                )
                if recogidas
                else (
                    "Ninguna compra de la plantilla falta en el "
                    "libro."
                )
            ),
        }

    except Exception as error:                      # noqa: BLE001
        return {
            **salida,
            "reason": (
                f"No se pudieron recoger las compras de la "
                f"plantilla: {type(error).__name__}: {error}"
            ),
        }


def recoger_pujas_vivas(
    snapshot,
    our_user_id,
    *,
    ledger: dict,
    ruta_del_carril=None,
) -> dict:
    """
    Anota en el libro las pujas vivas del tablon que no estan.

    Forma fija. Nunca lanza. Devuelve las que ha recogido, para
    que el ciclo pueda decirlo.

    NO DUPLICA: se mira POR JUGADOR y no por clave, porque la
    clave lleva la hora y la del tablon no tiene por que coincidir
    al segundo con la que anoto el ejecutor. La misma foto dos
    veces deja una sola entrada.
    """

    salida = {
        "available": False,
        "recogidas": [],
        "reason": None,
    }

    try:
        if not snapshot or our_user_id is None:
            return {
                **salida,
                "reason": (
                    "Sin foto o sin saber quienes somos no se "
                    "recoge nada: marcar pujas ajenas como "
                    "nuestras seria peor que no verlas."
                ),
            }

        from src.analysis.bid_exposure_engine import (
            build_bid_exposure,
        )

        exposicion = build_bid_exposure(
            snapshot, own_user_id=our_user_id
        )

        ya_estan = {
            int(e.get("player_id") or 0)
            for e in (ledger.get("bids") or {}).values()
            if isinstance(e, dict)
            and e.get("outcome") == "PENDING"
        }

        recogidas = []

        for operacion in (exposicion.get("operations") or []):

            importe = safe_int(operacion.get("amount"))

            if importe <= 0:
                continue

            for jugador in (operacion.get("player_ids") or []):

                pid = safe_int(jugador)

                if pid <= 0 or pid in ya_estan:
                    continue

                puesta = (
                    _cuando_se_puso(operacion.get("created"))
                    or _ahora()
                )

                record_bid(
                    pid,
                    importe,
                    player_name=_nombre_en_la_foto(
                        snapshot, pid
                    ),
                    market_price=_precio_en_la_foto(
                        snapshot, pid
                    ),
                    target_source=_origen_probado(
                        pid, importe, ruta_del_carril
                    ),
                    seller_user_id=operacion.get(
                        "counterparty_id"
                    ),
                    placed_at=puesta,
                    ledger=ledger,
                    save=False,
                )

                # Queda dicho que NO la vimos pujar: se anoto al
                # verla puesta.
                ledger["bids"][_clave(pid, puesta)][
                    "recorded_by"
                ] = "TABLON"

                ya_estan.add(pid)

                recogidas.append(
                    {
                        "player_id": pid,
                        "amount": importe,
                        "placed_at": puesta,
                    }
                )

        return {
            "available": True,
            "recogidas": recogidas,
            "reason": (
                f"{len(recogidas)} puja(s) viva(s) del tablon "
                f"que no estaban en el libro."
                if recogidas
                else (
                    "Ninguna puja viva del tablon falta en el "
                    "libro."
                )
            ),
        }

    except Exception as error:                      # noqa: BLE001
        return {
            **salida,
            "reason": (
                f"No se pudieron recoger las pujas vivas: "
                f"{type(error).__name__}: {error}"
            ),
        }


def _precio_en_la_foto(snapshot, player_id):
    """El precio de mercado del jugador, si la foto lo trae."""

    try:
        for venta in (
            (snapshot.get("market") or {}).get("sales") or []
        ):
            jugador = venta.get("player")

            pid = (
                jugador.get("id")
                if isinstance(jugador, dict)
                else jugador
            )

            if safe_int(pid) == int(player_id):
                return safe_int(venta.get("price")) or None

        return None

    except Exception:                               # noqa: BLE001
        return None


def _quedo_sin_ella(entrada, en_plantilla, momento) -> bool:
    """
    ¿Esta puja se perdio? Solo dice True cuando SE SABE.

    Tres condiciones, y las tres tienen que darse:

        1. se sabe quien esta en la plantilla
        2. el reset que resolvia esta puja YA PASO
        3. el jugador NO esta en la plantilla

    Si falta cualquiera de las tres, esto devuelve False y la
    puja se queda como estaba. No marcar una derrota que no
    consta es barato; inventarla envenena la calibracion de la
    prima de puja, que es el numero que decide cuanto pagamos de
    mas.
    """

    if not en_plantilla:
        return False

    try:
        jugador = int(entrada.get("player_id"))

    except (TypeError, ValueError):
        return False

    if jugador in en_plantilla:
        return False

    reset = _reset_que_la_resuelve(
        entrada.get("placed_at") or ""
    )

    if reset is None:
        return False

    try:
        ahora = datetime.fromisoformat(momento)

        if ahora.tzinfo is None:
            ahora = ahora.replace(tzinfo=timezone.utc)

    except Exception:                               # noqa: BLE001
        return False

    return ahora >= reset


def reconcile(
    board,
    our_user_id: int | None,
    *,
    ledger: dict | None = None,
    path: Path | None = None,
    save: bool = True,
    ahora: str | None = None,
    roster=None,
) -> dict:
    """
    Cierra las pujas pendientes contra las subastas ya resueltas.

    Ganamos si el comprador de la operacion somos nosotros. Si no, el
    importe de la operacion es lo que pago el ganador, y la diferencia
    con lo nuestro es por cuanto nos ganaron.
    """

    libro = ledger if ledger is not None else load_ledger(path)

    # Sin saber quienes somos no se puede distinguir ganar de perder, y
    # marcarlo todo como perdido seria peor que no medir: dejaria un
    # libro que miente. Se prefiere no tocar nada.
    if our_user_id is None:
        return libro

    momento = ahora or _ahora()
    limite = _epoch(momento) - HORAS_PARA_CADUCAR * 3600

    # `None` si no se sabe. Sin plantilla no se marca nada como
    # perdido: un libro que inventa derrotas es peor que uno que
    # no mide.
    en_plantilla = _en_la_plantilla(roster)

    ops_por_jugador: dict[int, list] = {}
    for event_id, fecha, operacion in _operaciones(board):
        try:
            pid = int(operacion.get("player"))
        except (TypeError, ValueError):
            continue
        ops_por_jugador.setdefault(pid, []).append((event_id, fecha, operacion))

    for entrada in libro["bids"].values():
        if entrada.get("outcome") != "PENDING":
            continue

        puesta = _epoch(entrada.get("placed_at") or "")
        candidatas = [
            (e, f, o)
            for e, f, o in ops_por_jugador.get(entrada["player_id"], [])
            if not f or not puesta or f >= puesta
        ]

        if not candidatas:

            # O LA TIENES O NO LA TIENES.
            #
            #     Si el reset que resolvia esta puja ya paso y el
            #     jugador no esta en la plantilla, se perdio. No
            #     hace falta el tablon para eso, y es justo
            #     cuando el tablon no trae la operacion cuando
            #     esto importa.
            perdida = _quedo_sin_ella(
                entrada, en_plantilla, momento
            )

            if perdida:
                entrada["outcome"] = "LOST"
                entrada["resolved_at"] = momento
                entrada["resolved_by"] = "RESET_SIN_JUGADOR"
                # Sin operacion en el tablon no se sabe por
                # cuanto nos ganaron: se cuenta la derrota y no
                # el margen (los margenes se cuentan aparte).
                entrada["margin"] = None
                continue

            if puesta and puesta < limite:
                entrada["outcome"] = "UNKNOWN"
                entrada["resolved_at"] = momento
            continue

        event_id, _fecha, operacion = min(
            candidatas, key=lambda c: c[1] or 0
        )

        comprador = (operacion.get("to") or {}).get("id")
        importe = operacion.get("amount")

        entrada["event_id"] = event_id
        entrada["resolved_at"] = momento
        entrada["winning_amount"] = (
            int(importe) if importe is not None else None
        )

        if our_user_id is not None and comprador == our_user_id:
            entrada["outcome"] = "WON"
            entrada["margin"] = 0
        else:
            entrada["outcome"] = "LOST"
            if importe is not None:
                entrada["margin"] = int(importe) - int(entrada["amount"])

    if save:
        save_ledger(libro, path)

    return libro


def summary(
    ledger: dict | None = None,
    path: Path | None = None,

    # DE DONDE SALIERON LAS PUJAS QUE SE CUENTAN (09/09/2026)
    #
    # Con el modo cartera encendido conviven dos caminos que
    # pujan: el de siempre y la subasta del reset. Sumados, el
    # dashboard diria un porcentaje de acierto que no es el de
    # ninguno de los dos. Con este filtro se puede mirar cada uno
    # por separado.
    #
    # None = todas, que es lo que hacia antes.
    target_source: str | None = None,
) -> dict:
    """
    El resumen que va al dashboard. Sin datos, dice que no los hay:
    nunca inventa un 0 % que parezca una medida.
    """

    libro = ledger if ledger is not None else load_ledger(path)
    entradas = list(libro.get("bids", {}).values())

    if target_source is not None:
        entradas = [
            e for e in entradas
            if e.get("target_source") == target_source
        ]

    ganadas = [e for e in entradas if e.get("outcome") == "WON"]
    perdidas = [e for e in entradas if e.get("outcome") == "LOST"]
    pendientes = [e for e in entradas if e.get("outcome") == "PENDING"]
    perdidas_de_vista = [e for e in entradas if e.get("outcome") == "UNKNOWN"]

    margenes = sorted(
        e["margin"] for e in perdidas if e.get("margin") is not None
    )

    resueltas = len(ganadas) + len(perdidas)

    return {
        "available": bool(entradas),
        "target_source": target_source,
        "placed": len(entradas),
        "won": len(ganadas),
        "lost": len(perdidas),
        "pending": len(pendientes),
        "unknown": len(perdidas_de_vista),
        "win_rate": (len(ganadas) / resueltas) if resueltas else None,
        "lost_with_margin": len(margenes),
        "median_lost_margin": (
            margenes[len(margenes) // 2] if margenes else None
        ),
        "mean_lost_margin": (
            int(sum(margenes) / len(margenes)) if margenes else None
        ),
        "worst_lost_margin": (margenes[-1] if margenes else None),
    }


def pujados_desde(
    desde,
    ledger: dict | None = None,
    path: Path | None = None,
) -> list:
    """
    Que jugadores tienen una puja NUESTRA apuntada desde ese
    momento, todavia sin resolver.

    POR QUE EXISTE (10/09/2026)

        Con dos disparos externos a cinco minutos, los dos
        dentro de la ventana, la segunda vuelta podria pujar
        otra vez por el mismo jugador y comprometer capacidad
        POR DUPLICADO.

        El tablero trae `has_live_bid`, pero eso depende de que
        la foto haya llegado fresca. El libro no: se escribe en
        el mismo instante en que se puja.

    Nunca lanza.
    """

    try:
        libro = (
            ledger if ledger is not None else load_ledger(path)
        )

        if isinstance(desde, str):
            desde = datetime.fromisoformat(desde)

        if desde.tzinfo is None:
            desde = desde.replace(tzinfo=timezone.utc)

        ids = []

        for entrada in (libro.get("bids") or {}).values():

            if not isinstance(entrada, dict):
                continue

            if entrada.get("outcome") not in (None, "PENDING"):
                continue

            try:
                marca = datetime.fromisoformat(
                    str(entrada.get("placed_at"))
                )

            except Exception:                       # noqa: BLE001
                continue

            if marca.tzinfo is None:
                marca = marca.replace(tzinfo=timezone.utc)

            if marca >= desde and entrada.get("player_id"):
                ids.append(int(entrada["player_id"]))

        return ids

    except Exception:                               # noqa: BLE001
        return []


def sync_bid_outcomes(
    our_user_id: int | None,
    *,
    board_path: Path | None = None,
    path: Path | None = None,
    roster=None,
    snapshot=None,
) -> dict:
    """
    El enganche del ciclo: cierra pendientes y devuelve el resumen.

    Lee el tablon ya persistido en vez de volver a pedirlo por red: el
    colector lo deja escrito en cada ciclo.

    Blindado a proposito, igual que el libro de fuentes: un fallo
    apuntando jamas puede detener un ciclo de produccion.
    """

    try:
        eventos = json.loads(
            (board_path or BOARD_EVENTS_PATH).read_text(encoding="utf-8")
        )
    except Exception:
        eventos = []

    if our_user_id is None:
        return {
            "available": False,
            "error": "Sin identificar nuestro usuario, no se cierra nada.",
        }

    try:
        libro = load_ledger(path)

        # PRIMERO SE RECOGE, LUEGO SE CIERRA.
        #
        #     En este orden a proposito: una puja que el tablon
        #     publica y el libro no tenia entra, y se resuelve en
        #     ESTA MISMA vuelta si su reset ya paso. Al reves se
        #     quedaria un ciclo entero sin cerrar.
        recogidas = recoger_pujas_vivas(
            snapshot, our_user_id, ledger=libro
        )

        # Y LO QUE YA SE RESOLVIO ENTRE DOS DESPLIEGUES.
        #
        #     Mirar solo pujas VIVAS deja fuera todo lo que se
        #     resuelve mientras no corremos. Trent se gano a las
        #     07:00 y la recogida se desplego a las 08:xx: para
        #     entonces no habia puja viva que ver.
        #
        #     La plantilla si lo sabe.
        de_la_plantilla = recoger_compras_de_la_plantilla(
            snapshot, eventos, our_user_id, ledger=libro
        )

        libro = reconcile(
            eventos,
            our_user_id,
            ledger=libro,
            path=path,
            roster=roster,
        )

        resumen = summary(libro)

        resumen["recogidas_del_tablon"] = recogidas

        resumen["recogidas_de_la_plantilla"] = de_la_plantilla

        return resumen
    except Exception:
        return {"available": False, "error": "El libro de pujas no pudo cerrarse."}
