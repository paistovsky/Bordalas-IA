"""
EL PARTE VENDE (17/10/2026; arreglado el 21/10/2026)

POR QUE EXISTE

    Paso 4 del laboratorio (verificado el 17/10): cuando Biwenger pasa a
    un jugador de 'ok' a 'doubt' o 'injured', su precio cae. Rentabilidad
    anormal a 3 dias (AR3) -3,4 % (n = 105 cambios de estado en 11 dias,
    lo mismo en las dos mitades); a 7 dias (AR7) -4,7 % (n = 54). Muestra
    pequeña: confianza MEDIA.

    Hasta hoy nadie vende por el parte: el de la plantilla que cae en
    duda o lesionado y no juega se queda en el banquillo perdiendo
    valor, salvo que el cierre de la jornada lo necesite para la caja.

    Ojo con lo que compra el suelo: aceptar al 95 % de su valor es ceder
    hoy lo que de media se pierde en una semana (-4,7 %). Lo que se gana
    es cualquier oferta por encima del suelo, no esperar a que caiga, y
    la caja libre para la ronda y la mejora.

LA REGLA

    1. A QUIEN. De la plantilla de la foto (`my_team`), los que el
       catalogo de la foto (`la_orden_del_gestor.leer_los_estados`) da
       en 'doubt' o 'injured' (`MALOS`). Nunca:
         - a uno del ONCE ESCRITO: el del panel (`status.lineup.players`,
           la misma fuente que `el_cierre_de_la_jornada`) y la alineacion
           vigente en Biwenger de la foto (`user_lineup.data.lineup
           .players`). Hacen falta LOS DOS: sin el del panel no se sabe
           quien es titular (`SIN_ONCE_ESCRITO`), sin el de Biwenger no
           se sabe quien sigue puesto (`SIN_ONCE_DE_BIWENGER`), y en los
           dos casos NO SE HACE NADA y la salida lo dice;
         - a un sancionado ('sanctioned'): se mira y no se toca
           (`SANCION`);
         - a un FICHAJE de hace menos de `DIAS_DE_FICHAJE` (7) dias
           (`RECIEN_FICHADO`), ni a uno del que no se sepa desde cuando
           es nuestro (`SIN_FECHA_DE_FICHAJE`);
         - a Yamal, por su nombre, siempre (este como este la orden).
           Sin nombre no se vende: no se sabria si es el;
         - a un protegido del gestor (`la_orden_del_gestor.protegidos`:
           `proteger` y `fichar`) ni a uno de `conservar`
           (`la_orden_del_gestor.conservados`);
         - a lo que aguanta LA CARTERA de la ronda
           (`la_ronda_de_la_manana.los_que_aguanta`): tiene su propia
           salida;
         - a lo que esta vuelta ya vendio (el estado de v10, la vuelta
           de la mejora y el plan del cierre, solo si son de ESTA
           vuelta, como los cuenta el cierre).
    2. QUE. Si la oferta viva del Computer llega al `SUELO` (95 %) de su
       valor de hoy (el `price` de la foto), ACEPTAR_OFERTA_DEL_COMPUTER.
       Si no, y no esta publicado (ni en la foto ni en esta vuelta),
       PONER_A_LA_VENTA a su valor: no saca a nadie del once y hace
       nacer la oferta del proximo reset. Publicado y sin oferta que
       llegue, NADA (con el motivo). Una escritura por jugador y vuelta.
    3. CUANDO. Nunca con una ronda jugandose
       (`la_proxima_jornada.jornada_en_curso`, como la ronda de la
       mañana): en esta liga el once no se cambia empezada la ronda, y
       vender a uno del once cerrado pierde sus puntos. Ni en la zona de
       silencio, ni sin calendario (`SIN_CALENDARIO`). En esos casos no
       se escribe nada, tampoco se publica.

LOS TRES ARREGLOS (21/10/2026)

    La revision del laboratorio del 21/10 reprodujo tres fallos.

    1. EL FICHAJE NO SE REVENDE ANTES DE JUGAR. Regla de la casa (E14,
       02/10): «un fichaje para el once no se revende antes de jugar con
       nosotros, salvo lesion larga» (cuatro vendidos en el paron sin
       jugar: -3,3 M y cero puntos; la ida y vuelta cuesta un 10-20 %).
       Nada protegia al recien llegado: la puja del dueño por Gaya (1844)
       se resuelve el 22/10 a las 05:00 UTC; si llega en duda y los once
       sanos lo dejan fuera del once, el parte lo publicaba el jueves y
       lo vendia el viernes, antes de la J10, deshaciendo la compra.
       Ahora no se toca a quien es nuestro desde hace menos de 7 dias.
       La salvedad de la lesion larga NO se aplica: el catalogo no dice
       cuanto dura; si hace falta, lo vende el dueño a mano.

       DE DONDE SALE LA FECHA: del tablon de la liga (`TABLON`,
       `data/rival_intelligence/board_events.json`), que el paso V10
       del workflow pide en cada vuelta ANTES del parte
       (`collect_board_history`) y que se guarda como libro. Es lo que
       publica Biwenger: una subasta ganada es un evento 'market' con
       `content[].to.id` = nosotros; una compra a un manager, un
       'transfer' con `to.id` = nosotros. Medido el 21/10 sobre el
       tablon de verdad: Sergi Cardona (30493), 'market' del 17/10 a
       las 05:05:38 UTC por 919.000; Luismi Cruz (25777), 'market' del
       14/10 a las 05:03:03 UTC por 3.252.000; estan los diez fichajes
       que siguen en la plantilla. El libro de posiciones
       (`data/trading/position_ledger.json`) tambien trae a los dos,
       pero con la hora a la que los VIO (14 minutos despues), no trae
       a Yamal (26271) y da por perdido a 19862, que sigue siendo
       nuestro: no sirve de fuente.

       QUIEN NO TIENE COMPRA EN EL TABLON es del reparto del dia 1 (el
       `leagueReset` del 09/08)... o un fichaje que el fichero todavia
       no trae (si la peticion de esta vuelta fallo, es el de la
       anterior). Se le da por nuestro DESDE EL RESET solo si (a) el
       tablon empieza en el reset, (b) el jugador no se ha movido nunca
       desde entonces y (c) el tablon esta AL DIA: trae el evento
       'market' (las subastas) del ultimo reset del Computer, que se
       lee de la foto (`el_ultimo_reset`: el `until` de sus ventas
       menos 24 h, `market_clock`). Si lo ultimo que dice el tablon de
       un jugador nuestro es que se fue o que lo compro otro, el tablon
       va por detras. En todos esos casos, y si el tablon no se puede
       leer: sin fecha, y no se vende (`SIN_FECHA_DE_FICHAJE`). Lo que
       cuesta: los dias en que nadie gana una subasta (5 de 73 hasta el
       21/10), y quiza el del cambio de hora (si el reset sigue la hora
       de Madrid, las 24 h no cuadran), los del reparto esperan: se
       falla del lado seguro. Lo que queda sin cubrir: una
       compra a un manager hecha despues de la ultima peticion buena,
       de uno que ese manager tenia del reparto, pasaria por nuestra
       desde el reset (tiene que fallar la peticion de esta vuelta, y
       compras entre managers hemos hecho una en 73 dias).

    2. LOS DOS ONCES. El once del panel ya deja fuera a los titulares
       lesionados y sancionados (es el once que se quiere poner); el de
       Biwenger es el que esta puesto. Antes bastaba el del panel, y
       `league_collector` deja `user_lineup` en None si `GET /user`
       falla: sin la mitad de Biwenger, el titular en duda que el panel
       ya habia quitado se podia vender. Ahora sin uno de los dos no se
       hace nada (`SIN_ONCE_DE_BIWENGER`).

    3. EL SANCIONADO NO SE VENDE. La regla del dueño lo nombraba
       ('sanctioned' estaba en `MALOS`), pero una sancion suele ser de
       un partido y el laboratorio solo midio 'doubt' e 'injured' (AR3
       -3,4 %, AR7 -4,7 %): al titular que se pierde una jornada por
       tarjetas se le vendia para siempre por una caida que nadie ha
       medido. Sale en `malos` (se miro) y en `no_se_tocan` (`SANCION`).

QUE NO HACE

    No compra, no pone el once, no toca a nadie 'ok', 'warned' o sin
    estado, no acepta ofertas de managers y no quita de la venta (el
    cliente de escritura no sabe). No mira la caja: eso es del cierre.

    Corre como paso propio del workflow, DESPUES del cierre de la jornada
    (necesita el once escrito del panel y lo que el cierre ya cobro y
    publico en esta vuelta): `python -m src.actions.el_parte_vende`.
    Nace APAGADO: `BORDALAS_EL_PARTE_VENDE`. Nunca lanza.

LO QUE DEJA PARA LA ROTACION (17/10/2026)

    La rotacion corre DESPUES y lee la foto de antes: sin esto no veia
    lo que el parte acababa de vender o publicar (emparejaba al que ya
    no estaba, o vendia al que salia con el que entro ya vendido).
    Encendido, `main` deja lo que mando en `VUELTA_PARTE`, con la forma
    del fichero de la vuelta de la mejora ({run_id, generated_at,
    hechas}: `la_mejora_del_once.escribir_la_vuelta`). `correr` no
    escribe nada (las guardias no tocan produccion).
"""

from __future__ import annotations

import json
import os

from datetime import datetime, timedelta, timezone
from pathlib import Path


ENV = "BORDALAS_EL_PARTE_VENDE"
RAIZ = Path(__file__).parents[2]

# Lo que mando en esta vuelta, para la rotacion (que corre despues).
VUELTA_PARTE = RAIZ / "data" / "trading" / "el_parte_vuelta.json"

# El tablon de la liga: de donde sale desde cuando es nuestro cada uno.
TABLON = RAIZ / "data" / "rival_intelligence" / "board_events.json"

# Lo que dice el parte del catalogo de Biwenger para vender. Sin
# 'sanctioned' desde el 21/10/2026: ver `SANCIONADO`.
MALOS = frozenset({"doubt", "injured"})

# El sancionado se mira y no se vende (`SANCION`): una sancion suele ser
# de un partido y su caida no esta medida.
SANCIONADO = "sanctioned"

# Un fichaje no se toca hasta que lleva estos dias con nosotros (E14).
DIAS_DE_FICHAJE = 7

# Lo minimo que se acepta del Computer, sobre el valor de hoy.
SUELO = 0.95

# Nunca se vende. Regla de la casa (= `la_orden_del_gestor.INTOCABLES`);
# aqui se mira si el nombre CONTIENE "yamal", por si el catalogo lo
# escribe de otra forma.
INTOCABLE = "yamal"


def activa() -> bool:
    try:
        return str(os.environ.get(ENV, "")).strip().lower() in {"1", "true", "si", "yes"}
    except Exception:                               # noqa: BLE001
        return False


# ============================================================
# AYUDAS QUE NUNCA LANZAN
# ============================================================

def _int(x, defecto=None):
    try:
        if x is None or isinstance(x, bool):
            return defecto
        return int(x)
    except (TypeError, ValueError, OverflowError):
        return defecto


def _dict(x) -> dict:
    return x if isinstance(x, dict) else {}


def _lista(x) -> list:
    try:
        if isinstance(x, dict):
            x = list(x.values())
        return [f for f in (x or []) if isinstance(f, dict)]
    except Exception:                               # noqa: BLE001
        return []


def _ids(x) -> set:
    try:
        if isinstance(x, (str, bytes)):
            return set()
        return {i for i in (_int(v) for v in (x or [])) if i is not None}
    except Exception:                               # noqa: BLE001
        return set()


def _por_id(x) -> dict:
    """`{player_id: valor}` con las claves en entero. Nunca lanza."""
    try:
        return {_int(k): v for k, v in _dict(x).items() if _int(k) is not None}
    except Exception:                               # noqa: BLE001
        return {}


def _nombres(x) -> list:
    """Los nombres de un jugador (uno o varios), sin blancos."""
    try:
        if isinstance(x, str):
            x = [x]
        return [str(n).strip() for n in (x or []) if str(n or "").strip()]
    except Exception:                               # noqa: BLE001
        return []


def _fecha(x) -> datetime | None:
    """Un instante en UTC: un `datetime` (sin zona, UTC), un epoch en
    segundos (el `date` del tablon) o un texto ISO. None si no es nada de
    eso. Nunca lanza."""
    try:
        if isinstance(x, datetime):
            cuando = x
        elif isinstance(x, (int, float)) and not isinstance(x, bool):
            if x <= 0:
                return None
            cuando = datetime.fromtimestamp(x, timezone.utc)
        elif isinstance(x, str) and x.strip():
            cuando = datetime.fromisoformat(x.strip().replace("Z", "+00:00"))
        else:
            return None
        if cuando.tzinfo is None:
            cuando = cuando.replace(tzinfo=timezone.utc)
        return cuando.astimezone(timezone.utc)
    except Exception:                               # noqa: BLE001
        return None


def el_suelo(valor) -> int | None:
    """El `SUELO` de `valor`, redondeado hacia arriba (al menos el 95 %).
    None si no hay valor. Pura."""
    valor = _int(valor)
    if valor is None or valor <= 0:
        return None
    return -(-valor * int(SUELO * 100) // 100)


def ids_del_once(alineacion) -> set:
    """Los ids de `{"players": [...]}` (el once del panel o el de
    Biwenger). Vacio si no se sabe. Nunca lanza."""
    try:
        return _ids(p.get("id") for p in _lista(_dict(alineacion).get("players")))
    except Exception:                               # noqa: BLE001
        return set()


# ============================================================
# DESDE CUANDO ES NUESTRO (21/10/2026)
# ============================================================

def el_ultimo_reset(snapshot) -> datetime | None:
    """
    El ultimo reset del Computer que ve la foto: el `until` comun de sus
    ventas es el PROXIMO (`market_clock.computer_reset_epoch`), y el
    ultimo fue 24 h antes. None si la foto no trae ventas del Computer:
    entonces no se puede saber si el tablon esta al dia. Nunca lanza.
    """
    try:
        from src.analysis.market_clock import computer_reset_epoch

        proximo, _ = computer_reset_epoch(_dict(snapshot))
        proximo = _int(proximo)
        if proximo is None or proximo <= 24 * 3600:
            return None
        return datetime.fromtimestamp(proximo - 24 * 3600, timezone.utc)
    except Exception:                               # noqa: BLE001
        return None


AVISOS = {
    "SIN_TABLON": ("el tablon no se pudo leer: no se sabe cuando llego nadie y no "
                   "se vende a nadie (SIN_FECHA_DE_FICHAJE)"),
    "SIN_RESET_EN_EL_TABLON": ("el tablon no empieza en el reset de la liga: a los "
                               "del reparto no se les puede dar fecha y no se venden"),
    "TABLON_ATRASADO": ("el tablon no trae las subastas del ultimo reset del "
                        "Computer (o la foto no dice cuando fue): a los del reparto "
                        "no se les puede dar fecha y no se venden en esta vuelta"),
}


def las_fechas_de_fichaje(eventos, yo, plantilla, ultimo_reset=None) -> dict:
    """
    Desde cuando es nuestro cada jugador de `plantilla`, del tablon de
    la liga (la lista de `board_events.json`). Pura. Nunca lanza.

        {"fechas": {player_id: datetime UTC}, "aviso": None o un AVISOS}

    Con compra en el tablon (lo ultimo que lo movio fue un 'market' o un
    'transfer' con `to.id` = `yo`), la fecha de ese evento. Sin ningun
    movimiento desde el reset, la del reset, pero solo si el tablon
    empieza en el y trae un 'market' desde `ultimo_reset` (esta al dia).
    Si lo ultimo que lo movio no es hacia nosotros, el tablon va por
    detras: sin fecha. Quien no tiene fecha no esta en `fechas`.
    """

    salida = {"fechas": {}, "aviso": None}
    try:
        yo = _int(yo)
        if isinstance(eventos, dict):
            eventos = eventos.get("events")
        eventos = _lista(eventos) if isinstance(eventos, list) else []
        if yo is None or not eventos:
            salida["aviso"] = "SIN_TABLON"
            return salida

        # El reset vigente: lo de antes es de otra temporada.
        reset = None
        for e in eventos:
            cuando = _fecha(_int(e.get("date")))
            if e.get("type") == "leagueReset" and cuando is not None:
                reset = cuando if reset is None or cuando > reset else reset

        tope = _fecha(ultimo_reset)
        al_dia = False
        movidos: dict = {}                  # {player_id: (cuando, hacia nosotros)}
        for e in eventos:
            if e.get("type") not in ("market", "transfer"):
                continue
            cuando = _fecha(_int(e.get("date")))
            if cuando is None or (reset is not None and cuando < reset):
                continue
            if e.get("type") == "market" and tope is not None and cuando >= tope:
                al_dia = True
            for op in _lista(e.get("content")):
                jugador = op.get("player")
                pid = _int(_dict(jugador).get("id") if isinstance(jugador, dict) else jugador)
                if pid is None:
                    continue
                a_nosotros = _int(_dict(op.get("to")).get("id")) == yo
                antes = movidos.get(pid)
                if antes is None or cuando > antes[0]:
                    movidos[pid] = (cuando, a_nosotros)
                elif cuando == antes[0]:
                    # Dos movimientos en el mismo segundo: hacia nosotros
                    # solo si lo son los dos.
                    movidos[pid] = (cuando, antes[1] and a_nosotros)

        fechas = {}
        for pid in _ids(plantilla):
            if pid in movidos:
                cuando, a_nosotros = movidos[pid]
                if a_nosotros:
                    fechas[pid] = cuando
            elif reset is not None and al_dia:
                fechas[pid] = reset

        salida["fechas"] = fechas
        if reset is None:
            salida["aviso"] = "SIN_RESET_EN_EL_TABLON"
        elif not al_dia:
            salida["aviso"] = "TABLON_ATRASADO"
        return salida
    except Exception:                               # noqa: BLE001
        return {"fechas": {}, "aviso": "SIN_TABLON"}


# ============================================================
# LA DECISION (pura)
# ============================================================

def por_que_no(*, puede_escribir=True, sin_calendario=False, en_curso=False,
               once_escrito=None, once_de_biwenger=None):
    """None si toca mirar el parte en esta vuelta. Si no, el motivo.
    `en_curso` None es no saberlo: no se hace nada. `once_escrito` (el
    del panel) y `once_de_biwenger` None es no mirarlos todavia (el reloj
    va antes que leer el panel); vacios, no saber quien es titular: no
    se hace nada. Nunca lanza."""
    try:
        if not puede_escribir:
            return "ZONA_DE_SILENCIO"
        if sin_calendario:
            return "SIN_CALENDARIO"
        if en_curso or en_curso is None:
            return "JORNADA_EN_CURSO"
        if once_escrito is not None and not _ids(once_escrito):
            return "SIN_ONCE_ESCRITO"
        if once_de_biwenger is not None and not _ids(once_de_biwenger):
            return "SIN_ONCE_DE_BIWENGER"
        return None
    except Exception:                               # noqa: BLE001
        return "SIN_ONCE_ESCRITO"


MOTIVOS = {
    "ZONA_DE_SILENCIO": "zona de silencio: no se escribe",
    "SIN_CALENDARIO": "sin calendario no se sabe si hay una ronda jugandose: no se vende",
    "JORNADA_EN_CURSO": ("hay una ronda jugandose (el once no se cambia empezada la "
                         "ronda): no se vende ni se publica"),
    "SIN_ONCE_ESCRITO": ("sin el once escrito del panel (status.lineup.players) no se "
                         "sabe quien es titular: no se vende ni se publica a nadie"),
    "SIN_ONCE_DE_BIWENGER": ("sin la alineacion vigente en Biwenger "
                             "(user_lineup.data.lineup.players: la foto la deja en None "
                             "si GET /user falla) no se sabe quien sigue puesto, y el "
                             "once del panel ya deja fuera a los lesionados y "
                             "sancionados: no se vende ni se publica a nadie"),
}


def decidir(
    *, plantilla, estados, nombres=None, precios=None, ofertas_del_computer=None,
    en_venta=frozenset(), once_escrito=frozenset(), once_de_biwenger=frozenset(),
    protegidos=frozenset(), conservados=frozenset(), aguanta=frozenset(),
    vendidos=frozenset(), fichajes=None, ahora=None,
    en_curso=False, puede_escribir=True, sin_calendario=False,
) -> dict:
    """
    Que vende el parte en esta vuelta. Pura: ni red, ni disco, ni reloj.

        plantilla             {player_id} nuestros (la foto)
        estados               {player_id: status del catalogo}
        nombres               {player_id: nombre o [nombres]} (Yamal)
        precios               {player_id: valor de hoy}
        ofertas_del_computer  {player_id: {"offer_id", "amount"}}
        en_venta              {player_id} publicados (foto y esta vuelta)
        once_escrito          {player_id} titulares del panel; vacio = no
                              se sabe y no se hace nada
        once_de_biwenger      {player_id} la alineacion vigente en
                              Biwenger; vacio = no se sabe y no se hace
                              nada
        protegidos            `proteger` y `fichar` de la orden
        conservados           `conservar` de la orden
        aguanta               lo de LA CARTERA de la ronda
        vendidos              {player_id} vendidos en esta vuelta
        fichajes              {player_id: datetime} desde cuando es
                              nuestro (`las_fechas_de_fichaje`); quien
                              no esta, o None, no se vende
        ahora                 la hora de la vuelta (sin ella, no se
                              cuentan los dias y no se vende a nadie)
        en_curso              hay una ronda jugandose (None: no se sabe)
        puede_escribir        fuera de la zona de silencio
        sin_calendario        no hay rondas que mirar

    `{"activo", "motivo", "acciones", "malos", "no_se_tocan"}`: `malos`
    son los del parte que se miraron (tambien los sancionados);
    `no_se_tocan`, los que no se venden y por que.
    """

    salida = {"activo": False, "motivo": None, "acciones": [], "malos": [],
              "no_se_tocan": []}
    try:
        once_escrito, once_de_biwenger = _ids(once_escrito), _ids(once_de_biwenger)
        motivo = por_que_no(puede_escribir=puede_escribir, sin_calendario=sin_calendario,
                            en_curso=en_curso, once_escrito=once_escrito,
                            once_de_biwenger=once_de_biwenger)
        if motivo:
            salida["motivo"] = motivo
            return salida

        once = once_escrito | once_de_biwenger
        estados, nombres = _por_id(estados), _por_id(nombres)
        precios, ofertas = _por_id(precios), _por_id(ofertas_del_computer)
        en_venta, vendidos = _ids(en_venta), _ids(vendidos)
        protegidos, conservados, aguanta = _ids(protegidos), _ids(conservados), _ids(aguanta)
        fichajes = {pid: f for pid, f in ((p, _fecha(v)) for p, v in _por_id(fichajes).items())
                    if f is not None}
        ahora = _fecha(ahora)

        acciones, malos, no_se_tocan = [], [], []
        for pid in sorted(_ids(plantilla)):
            estado = str(estados.get(pid) or "").strip().lower()
            if estado not in MALOS and estado != SANCIONADO:
                continue
            malos.append(pid)
            suyos = _nombres(nombres.get(pid))
            nombre = suyos[0] if suyos else None
            fichado = fichajes.get(pid)

            if pid in vendidos:
                por = "VENDIDO_EN_ESTA_VUELTA"
            elif pid in once:
                por = "ONCE_ESCRITO"
            elif any(INTOCABLE in n.lower() for n in suyos):
                por = "YAMAL"
            elif not suyos:
                por = "SIN_NOMBRE"
            elif pid in protegidos:
                por = "PROTEGIDO"
            elif pid in conservados:
                por = "CONSERVAR"
            elif pid in aguanta:
                por = "LA_CARTERA"
            elif estado == SANCIONADO:
                por = "SANCION"
            elif fichado is None or ahora is None:
                por = "SIN_FECHA_DE_FICHAJE"
            elif ahora - fichado < timedelta(days=DIAS_DE_FICHAJE):
                por = "RECIEN_FICHADO"
            else:
                por = None
            valor = _int(precios.get(pid))
            suelo = el_suelo(valor)
            if por is None and suelo is None:
                por = "SIN_VALOR"
            if por:
                fila = {"player_id": pid, "nombre": nombre, "estado": estado, "por": por}
                if por == "RECIEN_FICHADO":
                    fila["fichado"] = fichado.isoformat()
                no_se_tocan.append(fila)
                continue

            oferta = _dict(ofertas.get(pid))
            importe = _int(oferta.get("amount"), 0) or 0
            offer_id = _int(oferta.get("offer_id"))
            if offer_id and importe >= suelo:
                acciones.append({
                    "accion": "ACEPTAR_OFERTA_DEL_COMPUTER", "player_id": pid,
                    "nombre": nombre, "offer_id": offer_id, "importe": importe,
                    "valor": valor, "suelo": suelo, "estado": estado, "parte": True,
                })
            elif pid not in en_venta:
                acciones.append({
                    "accion": "PONER_A_LA_VENTA", "player_id": pid, "nombre": nombre,
                    "precio": valor, "estado": estado, "parte": True,
                })
            else:
                acciones.append({
                    "accion": "NADA", "player_id": pid, "nombre": nombre,
                    "estado": estado, "parte": True,
                    "motivo": (
                        f"publicado; la oferta del Computer ({importe}) no llega al "
                        f"{int(SUELO * 100)} % de su valor ({suelo})" if offer_id else
                        "publicado; esperando la oferta del Computer"
                    ),
                })

        salida.update({"activo": True, "acciones": acciones, "malos": malos,
                       "no_se_tocan": no_se_tocan})
        return salida
    except Exception as error:                      # noqa: BLE001
        return {"activo": False, "motivo": f"ERROR: {type(error).__name__}: {error}",
                "acciones": [], "malos": [], "no_se_tocan": []}


# ============================================================
# EL PASO DEL WORKFLOW
# ============================================================

def _leer(ruta, defecto):
    try:
        return json.loads(Path(ruta).read_text(encoding="utf-8"))
    except Exception:                               # noqa: BLE001
        return defecto


def lo_vendido_y_publicado(v10, vuelta_mejora, plan_cierre, ahora, run_id=None) -> dict:
    """
    Lo que ESTA vuelta ya cobro y publico antes del parte (la foto es de
    antes): las `hechas` de v10 (si su estado es de esta vuelta), las de
    la mejora (su fichero de la vuelta) y las del cierre (su plan), con
    las mismas pruebas de vuelta que usa el cierre (`run_id`; si no, la
    hora). `{"vendidos", "listados", "descartados"}`. Nunca lanza.
    """
    salida = {"vendidos": set(), "listados": set(), "descartados": []}
    try:
        from src.actions.el_cierre_de_la_jornada import (
            la_vuelta_de_la_mejora, lo_de_esta_vuelta,
        )
        from src.actions.la_mejora_del_once import es_de_esta_vuelta

        descartado = es_de_esta_vuelta(v10, ahora, run_id)
        de_la_vuelta = {} if descartado else dict(_dict(v10))
        if descartado:
            salida["descartados"].append(f"v10: {descartado}")
        hechas_mejora, d_mejora = la_vuelta_de_la_mejora(vuelta_mejora, ahora, run_id)
        hechas_cierre, d_cierre = la_vuelta_de_la_mejora(plan_cierre, ahora, run_id)
        if d_mejora:
            salida["descartados"].append(f"mejora: {d_mejora}")
        if d_cierre:
            salida["descartados"].append(f"cierre: {d_cierre}")
        de_la_vuelta["la_mejora_del_once"] = {"hechas": hechas_mejora}
        de_la_vuelta["el_cierre_de_la_jornada"] = {"hechas": hechas_cierre}
        vuelta = lo_de_esta_vuelta(de_la_vuelta)
        salida["vendidos"] = _ids(vuelta.get("vendidos"))
        salida["listados"] = _ids(vuelta.get("listados"))
    except Exception as error:                      # noqa: BLE001
        salida["descartados"].append(f"lo de esta vuelta: {type(error).__name__}")
    return salida


def correr(cycle=None, escritor_factory=None, ahora: datetime | None = None, *,
           status=None, calendario=None, orden_ruta=None, libro_ronda_ruta=None,
           v10=None, vuelta_mejora=None, plan_cierre=None, tablon=None) -> dict:
    """
    El parte, en esta vuelta. Nunca lanza.

    Lo que no se pasa se lee de produccion: la foto de `cycle["snapshot"]`
    (sin `cycle`, la ultima `snapshot_*.json`, como el cierre), `status`
    del panel, el calendario de los chollos, la orden del gestor
    (`orden_ruta`), el libro de la ronda (`libro_ronda_ruta`), lo que
    esta vuelta ya hizo (`v10`, `vuelta_mejora`, `plan_cierre`) y los
    eventos del tablon (`tablon`, la lista de `TABLON`).
    Apagado, no lee ni escribe nada.
    """

    salida = {"activa": activa(), "motivo": None, "acciones": [], "hechas": [],
              "decision": None}

    try:
        if not salida["activa"]:
            salida["motivo"] = "APAGADA"
            return salida

        from src.actions.la_orden_del_gestor import (
            _pid, conservados, ejecutar, leer_la_foto, leer_los_estados, protegidos,
        )
        from src.actions.la_ronda_de_la_manana import los_que_aguanta
        from src.actions.los_chollos import CALENDARIO, _puede_escribir
        from src.analysis.la_proxima_jornada import jornada_en_curso, las_rondas

        ahora = ahora or datetime.now(timezone.utc)

        # 3. CUANDO: con una ronda jugandose, en la zona de silencio o sin
        # calendario, nada (y sin leer nada mas).
        cal = CALENDARIO if calendario is None else calendario
        sin_calendario = not las_rondas(cal)
        en_curso = bool(jornada_en_curso(ahora, cal))
        puede_escribir = bool(_puede_escribir(ahora))
        salida["en_curso"] = en_curso
        motivo = por_que_no(puede_escribir=puede_escribir, sin_calendario=sin_calendario,
                            en_curso=en_curso)
        if motivo:
            salida["motivo"] = motivo
            salida["detalle"] = MOTIVOS.get(motivo)
            return salida

        if cycle is None:
            from src.actions.la_mejora_del_once import _la_ultima_foto

            snapshot = _la_ultima_foto()
        else:
            snapshot = _dict(cycle).get("snapshot")
        snapshot = _dict(snapshot)

        yo = _pid(_dict(snapshot.get("league")).get("user"))
        if yo is None:
            salida["motivo"] = "SIN_SABER_QUIEN_SOY"
            return salida
        foto = leer_la_foto(snapshot, yo)

        # EL ONCE ESCRITO: el del panel (la fuente del cierre) Y la
        # alineacion vigente en Biwenger de la foto (21/10/2026: hacen
        # falta los dos; el del panel ya deja fuera a los lesionados y
        # sancionados). Sin uno de los dos, no se hace nada. Con los dos,
        # no se toca a ninguno de ninguno.
        if status is None:
            from src.actions.la_mejora_del_once import STATUS

            status = _leer(STATUS, {})
        del_panel = ids_del_once(_dict(status).get("lineup"))
        de_biwenger = ids_del_once(_dict(_dict(snapshot.get("user_lineup")).get("data"))
                                   .get("lineup"))
        once_escrito = (del_panel | de_biwenger) if (del_panel and de_biwenger) else set()
        salida["once_escrito"] = sorted(once_escrito)

        motivo = por_que_no(puede_escribir=puede_escribir, sin_calendario=sin_calendario,
                            en_curso=en_curso, once_escrito=del_panel,
                            once_de_biwenger=de_biwenger)
        if motivo:
            salida["motivo"] = motivo
            salida["detalle"] = MOTIVOS.get(motivo)
            return salida

        # Lo que esta vuelta ya cobro y publico (la foto es de antes).
        if v10 is None or vuelta_mejora is None or plan_cierre is None:
            from src.actions.el_cierre_de_la_jornada import PLAN, VUELTA_MEJORA
            from src.actions.la_mejora_del_once import V10

            v10 = _leer(V10, {}) if v10 is None else v10
            vuelta_mejora = _leer(VUELTA_MEJORA, {}) if vuelta_mejora is None else vuelta_mejora
            plan_cierre = _leer(PLAN, {}) if plan_cierre is None else plan_cierre
        vuelta = lo_vendido_y_publicado(v10, vuelta_mejora, plan_cierre, ahora,
                                        os.environ.get("GITHUB_RUN_ID"))
        salida["vuelta_descartada"] = vuelta["descartados"]

        # DESDE CUANDO ES NUESTRO CADA UNO (21/10/2026): del tablon que el
        # paso V10 acaba de pedir. Sin tablon, nadie tiene fecha y no se
        # vende a nadie.
        if tablon is None:
            tablon = _leer(TABLON, None)
        fichajes = las_fechas_de_fichaje(tablon, yo, foto["plantilla"],
                                         el_ultimo_reset(snapshot))
        if fichajes["aviso"]:
            salida["aviso_del_tablon"] = fichajes["aviso"]
            salida["detalle_del_tablon"] = AVISOS.get(fichajes["aviso"])

        # Nombres y valor: la foto (plantilla y catalogo) y el panel.
        catalogo = _dict(_dict(_dict(snapshot.get("catalog")).get("data")).get("players"))
        nombres: dict = {}

        def _apuntar(pid, nombre):
            pid = _int(pid)
            if pid is not None and str(nombre or "").strip():
                nombres.setdefault(pid, []).append(str(nombre))

        for k, ficha in catalogo.items():
            _apuntar(k, _dict(ficha).get("name"))
        for j in _lista(snapshot.get("my_team")):
            _apuntar(j.get("id"), j.get("name"))
        for j in _lista(_dict(_dict(status).get("roster")).get("players")):
            _apuntar(j.get("id"), j.get("name"))
        precios = {}
        for k, ficha in catalogo.items():
            if _int(k) is not None and _int(_dict(ficha).get("price")):
                precios[_int(k)] = _int(_dict(ficha).get("price"))
        precios.update(_por_id(foto.get("precios")))

        d = decidir(
            plantilla=foto["plantilla"], estados=leer_los_estados(snapshot),
            nombres=nombres, precios=precios,
            ofertas_del_computer=foto["ofertas_del_computer"],
            en_venta=set(foto["en_venta"]) | vuelta["listados"],
            once_escrito=del_panel, once_de_biwenger=de_biwenger,
            protegidos=protegidos(orden_ruta, ahora),
            conservados=conservados(orden_ruta, ahora),
            aguanta=los_que_aguanta(libro_ronda_ruta),
            vendidos=vuelta["vendidos"], fichajes=fichajes["fechas"], ahora=ahora,
            en_curso=en_curso, puede_escribir=puede_escribir,
            sin_calendario=sin_calendario,
        )
        salida["decision"] = d
        salida["acciones"] = d["acciones"]

        escrituras = [a for a in d["acciones"] if a.get("accion") != "NADA"]
        if not d.get("activo"):
            salida["motivo"] = d.get("motivo")
            return salida
        if not escrituras:
            salida["motivo"] = "NADA_QUE_HACER"
            return salida

        if escritor_factory is None:
            from src.biwenger.write_client import BiwengerWriteClient

            escritor_factory = BiwengerWriteClient

        salida["hechas"] = ejecutar(escrituras, escritor_factory())
        salida["motivo"] = "EJECUTADA"

    except Exception as error:                      # noqa: BLE001
        salida["motivo"] = f"ERROR: {type(error).__name__}: {error}"

    return salida


def el_parte(r) -> list:
    """Las lineas de la vuelta, para leerlas en el log. Nunca lanza."""
    lineas = []
    try:
        r = _dict(r)
        lineas.append(f"  {r.get('motivo')}"
                      + (f": {r.get('detalle')}" if r.get("detalle") else ""))
        if r.get("once_escrito"):
            lineas.append(f"  Once escrito (no se toca): {r.get('once_escrito')}")
        for v in r.get("vuelta_descartada") or []:
            lineas.append(f"  Sin contar lo de esta vuelta de {v}")
        if r.get("aviso_del_tablon"):
            lineas.append(f"  Fechas de fichaje: {r.get('aviso_del_tablon')}"
                          + (f": {r.get('detalle_del_tablon')}"
                             if r.get("detalle_del_tablon") else ""))
        d = _dict(r.get("decision"))
        if d.get("malos"):
            lineas.append(f"  Con parte malo en la plantilla: {d.get('malos')}")
        for n in _lista(d.get("no_se_tocan")):
            lineas.append(f"      no se toca {n.get('player_id')} {n.get('nombre') or ''} "
                          f"({n.get('estado')}): {n.get('por')}"
                          + (f" (nuestro desde {n.get('fichado')})" if n.get("fichado") else ""))
        for a in _lista(r.get("acciones")):
            importe = a.get("importe") or a.get("precio")
            lineas.append(f"  -> {a.get('accion')} {a.get('player_id')} {a.get('nombre') or ''} "
                          f"({a.get('estado')}) {importe if importe else ''}"
                          f"{(' suelo ' + str(a.get('suelo'))) if a.get('suelo') else ''}"
                          f"{(' (' + str(a.get('motivo')) + ')') if a.get('motivo') else ''}")
        for h in _lista(r.get("hechas")):
            lineas.append(f"  hecha {h.get('accion')} {h.get('player_id')} exito={h.get('exito')} "
                          f"http={h.get('http_status')} {h.get('error') or ''}")
    except Exception as error:                      # noqa: BLE001
        lineas.append(f"  (el parte no se pudo escribir: {type(error).__name__})")
    return lineas


def main() -> int:
    r = correr()
    # Encendido, SIEMPRE (tambien sin nada hecho): lo de esta vuelta, para
    # la rotacion. Apagado no se escribe (la rotacion no lo echa de menos).
    try:
        if r.get("activa"):
            from src.actions.la_mejora_del_once import escribir_la_vuelta

            escribir_la_vuelta(r.get("hechas") or [], VUELTA_PARTE)
    except Exception:                               # noqa: BLE001
        pass
    print("=" * 100)
    print("EL PARTE VENDE")
    print("=" * 100)
    for linea in el_parte(r):
        print(linea)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
