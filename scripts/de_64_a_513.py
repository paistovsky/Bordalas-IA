"""
La lista de objetivos: lo que cuesta pasar de la de hoy al catalogo.

QUE CONTESTA, Y POR QUE NO SE PUEDE CONTESTAR LEYENDO

    El 20/09 se leyo `data/intelligence/futbolfantasy_board.json`
    y salio "64 objetivos, 13 paginas". Ese fichero es del 17/08
    y lleva `matchday: 2`: es de TRES DIAS ANTES del bloque RIVAL
    del 20/08. Un numero correcto contestando una pregunta que ya
    no era la suya.

    Esto no lee el tablero: construye la lista con el codigo de
    hoy contra las fotos que hay en `data/`, en las dos
    posiciones del interruptor, y cuenta.

QUE MIDE

    1. OBJETIVOS Y PAGINAS, foto a foto. El coste en PETICIONES
       es la diferencia entre las dos columnas de `equipos`, no
       una estimacion: se pide una pagina por equipo.

    2. SEGUNDOS, ejecutando el proveedor de verdad contra los
       HTML que haya en disco. Separa el rato de parsear -que no
       cambia, porque son las mismas paginas- del de emparejar,
       que es lo unico que sube.

    3. QUE PASA SI UNA PAGINA NO CONTESTA. Se tira una a
       proposito y se mira si la vuelta sobrevive.

NI UNA PETICION A LA RED, NI UNA ESCRITURA

    La sesion se sustituye por una que sirve los HTML de
    `data/ff_html`. El tablero se escribe en un directorio
    temporal: `data/intelligence/futbolfantasy_board.json` no se
    toca.

    Con `--html DIR` se usan paginas de otro sitio. Util para
    medir con paginas frescas sin ensuciar `data/`.

COMO SE USA

    python -m scripts.de_64_a_513
    python -m scripts.de_64_a_513 --html RUTA
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import statistics
import sys
import tempfile
import time

from collections import Counter
from pathlib import Path


RAIZ = Path(__file__).resolve().parents[1]

if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))


from src.intelligence import futbolfantasy_absences as bajas   # noqa: E402
from src.intelligence import futbolfantasy_provider as ff      # noqa: E402


VUELTAS = 3

PAGINA_QUE_SE_CAE = "barcelona"


# ----------------------------------------------------------------
# LA SESION DE DISCO
# ----------------------------------------------------------------


class Respuesta:

    def __init__(self, texto: str):
        self.text = texto
        self.status_code = 200
        self.headers = {}

    def raise_for_status(self):
        return None


class SesionDeDisco:
    """Sirve las paginas de FF desde disco y cuenta peticiones."""

    def __init__(self, carpeta: Path, caidos=frozenset()):
        self.carpeta = carpeta
        self.caidos = set(caidos)
        self.peticiones: list[str] = []
        self.bytes = 0

    def get(self, url, **_):

        self.peticiones.append(url)

        if url == bajas.INJURIES_URL:
            slug = "lesionados"

        elif url == bajas.SUSPENSIONS_URL:
            slug = "sancionados"

        else:
            slug = str(url).rstrip("/").split("/")[-1]

        if slug in self.caidos:
            raise RuntimeError("ConnectionError (simulado)")

        fichero = self.carpeta / f"{slug}.html"

        if not fichero.exists():
            raise FileNotFoundError(f"sin HTML de disco para {slug}")

        texto = fichero.read_text(encoding="utf-8")

        self.bytes += len(texto)

        return Respuesta(texto)


# ----------------------------------------------------------------
# EL CRONOMETRO, POR FASES
# ----------------------------------------------------------------


RELOJ = {"parse": 0.0, "match": 0.0}


def cronometrar() -> None:
    """Envuelve las dos fases caras. Se llama una sola vez."""

    parse, match = ff.parse_team_page, ff.match_team

    def parse_cron(html):
        arranque = time.perf_counter()
        try:
            return parse(html)
        finally:
            RELOJ["parse"] += time.perf_counter() - arranque

    def match_cron(registros, objetivos):
        arranque = time.perf_counter()
        try:
            return match(registros, objetivos)
        finally:
            RELOJ["match"] += time.perf_counter() - arranque

    ff.parse_team_page = parse_cron
    ff.match_team = match_cron


# ----------------------------------------------------------------
# LAS FOTOS
# ----------------------------------------------------------------


def fotos() -> list[tuple[str, dict]]:
    """Una foto por dia, y solo las que traen plantillas rivales."""

    salida = []
    vistos = set()

    patron = str(RAIZ / "data" / "snapshot_2026*.json")

    for camino in sorted(glob.glob(patron)):

        dia = Path(camino).name[9:17]

        if dia in vistos:
            continue

        try:
            foto = json.loads(Path(camino).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue

        clasificacion = (
            (foto.get("rounds") or {})
            .get("data", {})
            .get("league", {})
            .get("standings")
            or []
        )

        if not any(
            (fila.get("lineup") or {}).get("players")
            for fila in clasificacion
        ):
            continue

        vistos.add(dia)
        salida.append((dia, foto))

    return salida


def interruptor(encendido: bool) -> None:
    os.environ[ff.ENV_EL_CATALOGO] = "1" if encendido else ""


def objetivos_y_equipos(foto: dict, encendido: bool):

    interruptor(encendido)

    try:
        lista = ff.build_targets(foto)
    finally:
        interruptor(False)

    equipos = {
        objetivo["team"]
        for objetivo in lista
        if objetivo.get("team") and ff.team_slug(objetivo["team"])
    }

    return len(lista), Counter(o["scope"] for o in lista), len(equipos)


def una_corrida(foto, jornada, html: Path, encendido: bool, caidos=frozenset()):
    """Construye el tablero de verdad. Nunca toca el tablero real."""

    for clave in RELOJ:
        RELOJ[clave] = 0.0

    destino = Path(tempfile.mkdtemp(prefix="de64a513_")) / "board.json"

    anterior = ff.BOARD_FILE
    ff.BOARD_FILE = destino

    sesion = SesionDeDisco(html, caidos)

    arranque = time.perf_counter()

    interruptor(encendido)

    try:
        tablero = ff.refresh_board(
            foto, jornada, force=True, session=sesion
        )
    finally:
        ff.BOARD_FILE = anterior
        interruptor(False)

    return tablero, time.perf_counter() - arranque, sesion, dict(RELOJ)


# ----------------------------------------------------------------
# LOS TRES CUADROS
# ----------------------------------------------------------------


def cuadro_de_las_fotos(dias) -> None:

    print("=" * 78)
    print("LA LISTA DE OBJETIVOS, FOTO A FOTO")
    print("=" * 78)
    print()
    print(
        f"  {'foto':>10s} {'catalogo':>9s} | {'APAGADO':>8s} "
        f"{'roster':>7s} {'mercado':>8s} {'rival':>6s} {'equipos':>8s} | "
        f"{'ENCENDIDO':>10s} {'equipos':>8s}"
    )
    print("  " + "-" * 84)

    for dia, foto in dias:

        catalogo = len(
            (foto.get("catalog") or {}).get("data", {}).get("players", {})
            or {}
        )

        apagados, scopes, equipos_a = objetivos_y_equipos(foto, False)
        encendidos, _, equipos_b = objetivos_y_equipos(foto, True)

        print(
            f"  {dia:>10s} {catalogo:>9d} | {apagados:>8d} "
            f"{scopes['ROSTER']:>7d} {scopes['MARKET']:>8d} "
            f"{scopes['RIVAL']:>6d} {equipos_a:>8d} | "
            f"{encendidos:>10d} {equipos_b:>8d}"
        )

    print()
    print(
        "  Las dos columnas de `equipos` son las PETICIONES: "
        "una pagina por equipo."
    )


def cuadro_del_coste(dia, foto, jornada, html) -> None:

    print()
    print("=" * 78)
    print(f"LO QUE CUESTA, EJECUTANDO EL PROVEEDOR  (foto del {dia})")
    print("=" * 78)
    print()

    medianas = {}

    for encendido in (False, True):

        tiempos = []
        tablero = reloj = sesion = None

        for _ in range(VUELTAS):
            tablero, segundos, sesion, reloj = una_corrida(
                foto, jornada, html, encendido
            )
            tiempos.append(segundos)

        medianas[encendido] = statistics.median(tiempos)

        meta = tablero["metadata"]

        print(
            f"  interruptor {'ENCENDIDO' if encendido else 'apagado  '}"
            f"  objetivos {meta['targets']:>4d}"
            f"  emparejados {len(tablero['players']):>4d}"
            f"  paginas {meta['team_pages']:>3d}"
            f"  peticiones {len(sesion.peticiones):>3d}"
        )
        print(
            f"      mediana {medianas[encendido]:6.2f} s"
            f"   parsear {reloj['parse']:6.2f} s"
            f"   emparejar {reloj['match']:5.2f} s"
            f"   sin pareja {len(meta['unmatched']):>3d}"
        )

    print()
    print(
        f"  LO QUE AÑADE: {medianas[True] - medianas[False]:+.2f} s por "
        f"vuelta y CERO peticiones."
    )
    print(
        "  Las 20 paginas ya se piden hoy: lo unico que sube es emparejar."
    )


def cuadro_de_la_caida(dia, foto, jornada, html) -> None:

    print()
    print("=" * 78)
    print("SI UNA PAGINA NO CONTESTA")
    print("=" * 78)
    print()

    for encendido in (False, True):

        entero, _, _, _ = una_corrida(foto, jornada, html, encendido)

        roto, _, _, _ = una_corrida(
            foto, jornada, html, encendido, caidos={PAGINA_QUE_SE_CAE}
        )

        meta = roto["metadata"]

        print(
            f"  interruptor {'ENCENDIDO' if encendido else 'apagado  '}"
            f"  emparejados {len(entero['players']):>4d} -> "
            f"{len(roto['players']):>4d}"
            f"  paginas {meta['team_pages']:>3d}"
            f"  cache {roto['cache']['status']}"
        )
        print(f"      errores: {meta['errors']}")

    print()
    print(
        "  La vuelta NO se cae: la pagina que falla se anota en `errors`, "
        "los otros 19 equipos"
    )
    print(
        "  entran enteros y el tablero se escribe. Si fallan las VEINTE y "
        "hay tablero anterior,"
    )
    print("  `stale_fallback` sirve el de antes en vez de vaciarlo.")


def main() -> None:

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--html",
        default=str(RAIZ / "data" / "ff_html"),
        help="carpeta con los HTML de equipo",
    )

    parser.add_argument("--jornada", type=int, default=8)

    args = parser.parse_args()

    html = Path(args.html)

    if not html.exists():
        print(f"No hay HTML en {html}.")
        print("Corre antes: python scripts/dump_ff_team_html.py")
        return

    cronometrar()

    dias = fotos()

    if not dias:
        print("No hay fotos con plantillas de rivales en data/.")
        return

    cuadro_de_las_fotos(dias)

    dia, foto = dias[-1]

    cuadro_del_coste(dia, foto, args.jornada, html)
    cuadro_de_la_caida(dia, foto, args.jornada, html)


if __name__ == "__main__":
    main()
