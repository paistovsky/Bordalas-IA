"""
Los viajes de los ocho managers, emparejando cada compra con su venta.

POR QUE EXISTE (22/09/2026)

    El dueño hizo a mano la tabla de viajes de la liga —54 de
    Pollo17 al 91 % en verde, 24 nuestros al 62 %— y pidio que se
    rehiciera bien antes de creersela. Dos cosas podian haberla
    roto:

        las REEMISIONES del tablon, que ya costaron 420.200 EUR
        en la caja reconstruida;

        el emparejamiento FIFO, si alguien hubiera comprado dos
        veces al mismo jugador antes de vender una.

    Este modulo rehace el calculo con las dos cosas miradas.

LO QUE NO HACE

    No decide nada, no escribe en ningun libro y no sale a la
    red. Lee los ficheros que el ciclo ya guarda y devuelve
    listas. Quien quiera una tabla, que la imprima.

DE DONDE SALE CADA COSA

    los movimientos   `data/rival_intelligence/rival_intelligence.json`
    las fechas        `data/calendar/laliga_calendar.json`
    los puntos        el `fitness` de los snapshots, FECHADO con
                      el calendario (ver `serie_de_puntos`)
    los precios       `data/autopilot/price_history.json`

LA REGLA DE LAS REEMISIONES NO ES NUEVA (doctrina 84)

    Es la misma de `caja_de_la_liga`: misma operacion logica
    dentro de `VENTANA_REEMISION`, anclada en la PRIMERA
    aparicion y sin reanclar. El numero se importa de alli.

EL `fitness`, Y POR QUE HAY QUE FECHARLO

    Biwenger publica los ultimos cinco partidos de cada jugador
    en `fitness`, sin fecha y sin jornada. Para saber que puntos
    hizo DENTRO de una ventana de tenencia hay que fecharlos, y
    eso se hace cruzando con los partidos de su equipo en el
    calendario, del mas reciente al mas antiguo.

    MEDIDO: con dos fotos (13/09 y 19/09) que se solapan, el
    fechado coincide en el 90 % de los 541 jugadores. El 10 % que
    discrepa se concentra en CUATRO equipos —Athletic, Alaves,
    Osasuna y Rayo—, que son los de los partidos aplazados: el
    calendario oficial los fecha donde estaban, no donde se
    jugaron.

    Esos cuatro NO se adivinan: sus jugadores salen con los
    puntos a `None` y se cuentan aparte (doctrina 103).
"""

from __future__ import annotations

import bisect
import collections
import datetime
import json
import re
import unicodedata

from pathlib import Path


RAIZ = Path(__file__).resolve().parents[1]

COMPRAS = frozenset({"BUY_FROM_COMPUTER", "BUY_FROM_USER"})

VENTAS = frozenset({"SELL_TO_COMPUTER", "SELL_TO_USER"})


def _ventana_de_reemision() -> int:
    """Los segundos de la reja. Del sitio donde ya vivia."""

    try:
        import sys

        if str(RAIZ) not in sys.path:
            sys.path.insert(0, str(RAIZ))

        from src.analysis.caja_de_la_liga import VENTANA_REEMISION

        return int(VENTANA_REEMISION)

    except Exception:                               # noqa: BLE001
        return 3_600


VENTANA_REEMISION = _ventana_de_reemision()


def _lee(ruta) -> dict:
    return json.loads((RAIZ / ruta).read_text(encoding="utf-8"))


# ============================================================
# EL PUENTE ENTRE LOS DOS NOMBRES DE CADA EQUIPO
# ============================================================
#
#     Biwenger dice "Athletic"; el calendario de LaLiga dice
#     "Athletic Club". Se casan por las palabras que quedan al
#     quitar el ruido societario, y lo que no cae solo se
#     resuelve por eliminacion. Si no salen las veinte, revienta:
#     un puente a medias fecharia mal sin avisar.

_RUIDO = frozenset(
    {"cf", "fc", "ud", "rc", "rcd", "cd", "sd", "ca", "club", "de", "r"}
)


def _palabras(texto: str) -> set:
    plano = (
        unicodedata.normalize("NFKD", str(texto or ""))
        .encode("ascii", "ignore")
        .decode()
        .lower()
    )

    return {
        t for t in re.findall(r"[a-z]+", plano) if t not in _RUIDO
    }


def puente_de_equipos(catalogo: dict, calendario: dict) -> dict:
    """`teamID` de Biwenger -> nombre del calendario. 20 de 20."""

    biwenger = {
        int(k): v.get("name")
        for k, v in (catalogo.get("teams") or {}).items()
    }

    nombres = sorted(
        {m["home"] for m in calendario["matches"]}
        | {m["away"] for m in calendario["matches"]}
    )

    mapa = {}
    pendientes = []

    for tid, nombre in biwenger.items():

        suyas = _palabras(nombre)

        puntuacion = [
            (len(suyas & _palabras(c)), c) for c in nombres
        ]

        mejor = max(puntuacion)[0]

        empatan = [c for k, c in puntuacion if k == mejor]

        if mejor > 0 and len(empatan) == 1:
            mapa[tid] = empatan[0]
        else:
            pendientes.append((tid, empatan))

    for tid, empatan in pendientes:

        libres = [c for c in empatan if c not in set(mapa.values())]

        if len(libres) == 1:
            mapa[tid] = libres[0]

    if len(mapa) != 20 or len(set(mapa.values())) != 20:
        raise ValueError(
            f"el puente de equipos no casa 20 a 20: "
            f"{len(mapa)} equipos, {len(set(mapa.values()))} destinos"
        )

    return mapa


# ============================================================
# LOS PUNTOS, PARTIDO A PARTIDO Y CON FECHA
# ============================================================

class SerieDePuntos:
    """
    Que puntos hizo cada jugador y CUANDO.

    No lee el mundo por su cuenta si se le pasan los ficheros;
    por defecto lee los que el ciclo ya guarda.
    """

    def __init__(self, fotos=None, calendario=None):

        self.calendario = calendario or _lee(
            "data/calendar/laliga_calendar.json"
        )

        self._partidos = {}

        # Las dos fotos que cubren la temporada entera, con la
        # hora a la que se tomaron: `fitness` solo puede contener
        # partidos ANTERIORES a ese instante.
        self.fotos = fotos or [
            (
                "data/snapshot_20260913_084210.json",
                "2026-09-13T08:42:00+02:00",
            ),
            (
                "data/snapshot_20260919_181829.json",
                "2026-09-19T18:18:00+02:00",
            ),
        ]

        series = []

        for ruta, corte in self.fotos:
            series.append(self._de_una_foto(ruta, corte))

        ultima = _lee(self.fotos[-1][0])["catalog"]["data"]

        self.equipo_de = {
            int(k): p.get("teamID")
            for k, p in ultima["players"].items()
        }

        self.nombre_de_equipo = {
            int(k): v.get("name") for k, v in ultima["teams"].items()
        }

        self.puente = puente_de_equipos(ultima, self.calendario)

        # LOS QUE NO CUADRAN, MARCADOS (doctrina 103).
        discrepan = collections.Counter()

        for a, b in zip(series, series[1:]):
            for pid in set(a) & set(b):
                comunes = set(a[pid]) & set(b[pid])
                if comunes and not all(
                    a[pid][j][0] == b[pid][j][0] for j in comunes
                ):
                    discrepan[self.equipo_de.get(pid)] += 1

        self.discrepancias = dict(discrepan)

        self.equipos_sin_fiar = {
            t for t, c in discrepan.items() if c >= 5
        }

        self.serie = {}

        for parcial in series:
            for pid, tramo in parcial.items():
                self.serie.setdefault(pid, {}).update(tramo)

    # ------------------------------------------------

    def _partidos_de(self, nombre) -> list:

        if nombre not in self._partidos:
            self._partidos[nombre] = sorted(
                (
                    datetime.datetime.fromisoformat(m["kickoff"]),
                    m["matchday"],
                )
                for m in self.calendario["matches"]
                if m["home"] == nombre or m["away"] == nombre
            )

        return self._partidos[nombre]

    def _de_una_foto(self, ruta, corte_iso) -> dict:

        catalogo = _lee(ruta)["catalog"]["data"]

        mapa = puente_de_equipos(catalogo, self.calendario)

        corte = datetime.datetime.fromisoformat(corte_iso)

        salida = {}

        for pid, jugador in catalogo["players"].items():

            forma = jugador.get("fitness") or []

            equipo = mapa.get(jugador.get("teamID"))

            if not forma or not equipo:
                continue

            jugados = [
                x for x in self._partidos_de(equipo) if x[0] < corte
            ]

            if len(jugados) < len(forma):
                continue

            # `fitness` va del mas RECIENTE al mas antiguo.
            ultimos = jugados[-len(forma):]

            salida[int(pid)] = {
                jornada: (valor, fecha)
                for (fecha, jornada), valor in zip(
                    reversed(ultimos), forma
                )
            }

        return salida

    # ------------------------------------------------

    def partidos_del_equipo(self, pid, desde, hasta) -> list | None:

        equipo = self.puente.get(self.equipo_de.get(pid))

        if not equipo:
            return None

        return [
            x
            for x in self._partidos_de(equipo)
            if desde <= x[0] <= hasta
        ]

    def siguiente_partido(self, pid, desde):

        equipo = self.puente.get(self.equipo_de.get(pid))

        if not equipo:
            return None

        futuros = [
            x for x in self._partidos_de(equipo) if x[0] >= desde
        ]

        return futuros[0][0] if futuros else None

    def partido_anterior(self, pid, hasta):

        equipo = self.puente.get(self.equipo_de.get(pid))

        if not equipo:
            return None

        pasados = [
            x for x in self._partidos_de(equipo) if x[0] <= hasta
        ]

        return pasados[-1][0] if pasados else None

    def entre(self, pid, desde, hasta):
        """
        (puntos, partidos de su equipo, partidos que jugo) en la
        ventana, o `None` si de ese jugador no consta.
        """

        if self.equipo_de.get(pid) in self.equipos_sin_fiar:
            return None

        suya = self.serie.get(pid)

        if not suya:
            return None

        puntos = partidos = jugados = 0

        for _, (valor, fecha) in suya.items():

            if desde <= fecha <= hasta:

                partidos += 1

                # Biwenger cuela algun `fitness` como texto. Un
                # valor que no es un numero es "no jugo", no un
                # cero: se cuenta aparte y no suma.
                if valor is None:
                    continue

                try:
                    puntos += int(valor)

                except (TypeError, ValueError):
                    continue

                jugados += 1

        return puntos, partidos, jugados

    def antes_de(self, pid, hasta):
        """Lo mismo, pero de todo lo anterior a esa fecha."""

        return self.entre(
            pid,
            datetime.datetime(2000, 1, 1, tzinfo=datetime.timezone.utc),
            hasta,
        )


# ============================================================
# LOS PRECIOS DE MERCADO
# ============================================================

class Precios:
    """El precio de mercado mas cercano ANTES de un instante."""

    # Mas de tres dias sin dato no es un precio: es un recuerdo.
    TOLERANCIA = 3 * 86_400

    def __init__(self, historia=None):
        self.series = (
            historia
            or _lee("data/autopilot/price_history.json")["players"]
        )

    def en(self, pid, ts):

        serie = self.series.get(str(pid))

        if not serie:
            return None

        t = serie["t"]

        i = bisect.bisect_right(t, ts) - 1

        if i < 0 or ts - t[i] > self.TOLERANCIA:
            return None

        return serie["p"][i]


# ============================================================
# LAS REEMISIONES Y EL EMPAREJAMIENTO
# ============================================================

def sin_repetidos(transacciones: list) -> tuple:
    """
    (limpias, tiradas). La misma reja que la caja de la liga.
    """

    vistos = {}
    limpias = []
    tiradas = []

    for t in sorted(transacciones, key=lambda x: x.get("date") or 0):

        clave = (
            t.get("kind"),
            t.get("player_id"),
            t.get("amount"),
            t.get("counterparty_id"),
        )

        primera = vistos.get(clave)

        if (
            primera is not None
            and (t.get("date") or 0) - primera <= VENTANA_REEMISION
        ):
            tiradas.append(t)
            continue

        vistos[clave] = t.get("date") or 0

        limpias.append(t)

    return limpias, tiradas


def empareja(transacciones: list) -> dict:
    """
    Cada compra con su venta, FIFO por jugador.

    Devuelve viajes cerrados, posiciones abiertas, ventas sin
    compra en el libro, y cuantos jugadores se llegaron a tener
    POR DUPLICADO —que es lo unico que podria cruzar el FIFO—.
    """

    cola = collections.defaultdict(collections.deque)

    viajes = []
    huerfanas = []

    a_la_vez = collections.Counter()
    tope = collections.Counter()

    for t in transacciones:

        pid = t.get("player_id")

        if t.get("kind") in COMPRAS:
            cola[pid].append(t)
            a_la_vez[pid] += 1
            tope[pid] = max(tope[pid], a_la_vez[pid])

        elif t.get("kind") in VENTAS:

            if cola[pid]:
                viajes.append((cola[pid].popleft(), t))
                a_la_vez[pid] -= 1
            else:
                huerfanas.append(t)

    return {
        "viajes": viajes,
        "abiertas": [c for q in cola.values() for c in q],
        "ventas_sin_compra": huerfanas,
        "con_dos_lotes": sorted(p for p, v in tope.items() if v > 1),
    }


# ============================================================
# LA FICHA DE UN VIAJE
# ============================================================

def _cuando(ts):
    return datetime.datetime.fromtimestamp(
        ts, datetime.timezone.utc
    ).astimezone()


def ficha_del_viaje(manager, compra, venta, puntos, precios) -> dict:

    entra = _cuando(compra["date"])
    sale = _cuando(venta["date"])

    pid = compra["player_id"]

    dentro = puntos.entre(pid, entra, sale)
    antes = puntos.antes_de(pid, entra)

    siguiente = puntos.siguiente_partido(pid, entra)
    anterior = puntos.partido_anterior(pid, sale)

    return {
        "manager": manager,
        "id": pid,
        "name": compra.get("player_name"),
        "compra": entra,
        "venta": sale,
        "importe": compra["amount"],
        "cobro": venta["amount"],
        "dias": (venta["date"] - compra["date"]) / 86_400.0,
        "pnl": venta["amount"] - compra["amount"],
        "roi": 100.0
        * (venta["amount"] - compra["amount"])
        / max(1, compra["amount"]),
        "puntos": None if dentro is None else dentro[0],
        "partidos": None if dentro is None else dentro[1],
        "jugados": None if dentro is None else dentro[2],
        "puntos_antes": None if antes is None else antes[0],
        "jugados_antes": None if antes is None else antes[2],
        "precio_compra": precios.en(pid, compra["date"]),
        "precio_venta": precios.en(pid, venta["date"]),
        "dias_al_siguiente_partido": (
            None
            if siguiente is None
            else (siguiente - entra).total_seconds() / 86_400.0
        ),
        "dias_desde_el_anterior": (
            None
            if anterior is None
            else (sale - anterior).total_seconds() / 86_400.0
        ),
        "kind_compra": compra["kind"],
        "kind_venta": venta["kind"],
    }


def clase_de_puntos(viaje: dict) -> str:
    """Las tres filas del bloque 1, y la cuarta que hace falta."""

    if viaje["puntos"] is None:
        return "no consta"

    if viaje["partidos"] == 0:
        return "no hubo partido"

    if viaje["jugados"] == 0:
        return "no llego a jugar"

    return "puntuo" if viaje["puntos"] > 0 else "no puntuo"


def todos_los_viajes(inteligencia=None, puntos=None, precios=None) -> dict:
    """
    {nombre del manager: [ficha, ...]} mas el recuento de la reja.
    """

    datos = inteligencia or _lee(
        "data/rival_intelligence/rival_intelligence.json"
    )

    puntos = puntos or SerieDePuntos()
    precios = precios or Precios()

    salida = {}

    for manager in datos.get("managers") or []:

        limpias, tiradas = sin_repetidos(
            manager.get("transactions") or []
        )

        casado = empareja(limpias)

        salida[manager["name"]] = {
            "user_id": manager.get("user_id"),
            "transacciones": len(manager.get("transactions") or []),
            "repetidas": tiradas,
            "con_dos_lotes": casado["con_dos_lotes"],
            "abiertas": casado["abiertas"],
            "ventas_sin_compra": casado["ventas_sin_compra"],
            "viajes": [
                ficha_del_viaje(
                    manager["name"], c, v, puntos, precios
                )
                for c, v in casado["viajes"]
            ],
        }

    return {
        "generated_at": datos.get("generated_at"),
        "managers": salida,
        "puntos": puntos,
        "precios": precios,
    }
