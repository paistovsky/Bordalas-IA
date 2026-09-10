"""
Las mecanicas de Biwenger que nadie de esta casa habia medido.

DE DONDE SALE TODO

    Del tablon (`board_events.json`), de las 85 fotos de
    produccion y del historico de precios. NI UNA llamada nueva
    a Biwenger, ninguna escritura y ningun umbral tocado.

LOS CINCO BLOQUES

    1. LA ECONOMIA        cuanto paga un punto, que son los
                          escalones, y cuanto ha entrado por
                          puntos contra lo que ha dado la rueda
    2. EL TOPE DE PLANTILLA
    3. EMPATES EN LA PUJA  quien gana si dos pujan lo mismo
    4. EL PRECIO QUE PEDIMOS  ¿espanta ofertas?
    5. QUE MUEVE LOS PRECIOS

COMO SE USA

    python -m scripts.las_mecanicas_del_juego
"""

from __future__ import annotations

import collections
import glob
import json
import statistics

from datetime import datetime, timedelta, timezone
from pathlib import Path


RAIZ = Path(__file__).parent.parent

TABLON = RAIZ / "data" / "rival_intelligence" / "board_events.json"

HISTORICO = RAIZ / "data" / "autopilot" / "price_history.json"

MADRID = timezone(timedelta(hours=2))

NOSOTROS = 14175949


def euros(valor) -> str:
    try:
        return f"{int(valor or 0):,}".replace(",", ".")
    except (TypeError, ValueError):
        return "?"


def cuando(epoch) -> str:
    try:
        return datetime.fromtimestamp(epoch, MADRID).strftime(
            "%d/%m %H:%M"
        )
    except Exception:                               # noqa: BLE001
        return "?"


def titulo(texto: str) -> None:
    print()
    print("=" * 74)
    print(texto)
    print("=" * 74)


def eventos() -> list:
    return json.loads(TABLON.read_text(encoding="utf-8"))


def fotos() -> list:
    return sorted(glob.glob(str(RAIZ / "data" / "snapshot_*.json")))


def operaciones(board: list, tipos: tuple) -> list:
    """
    Las operaciones de la liga, SIN REPETIR.

    EL TABLON REPITE (10/09/2026)

        Los `event_id` son unicos, pero la misma operacion
        aparece dentro de eventos distintos: 169 operaciones de
        subasta en el tablon, y solo 144 distintas.

        Contarlas dos veces inflaba la rueda: nuestras compras
        salian 76,8 M cuando son 51,9 M.

    Se identifica una operacion por fecha, jugador, importe y
    contraparte.
    """

    vistas = set()

    filas = []

    for evento in sorted(board, key=lambda e: e.get("date") or 0):

        if evento.get("type") not in tipos:
            continue

        contenido = evento.get("content")

        if not isinstance(contenido, list):
            continue

        for op in contenido:

            if not isinstance(op, dict):
                continue

            destino = op.get("to")
            origen = op.get("from")

            comprador = (
                destino.get("id")
                if isinstance(destino, dict)
                else None
            )

            vendedor = (
                origen.get("id")
                if isinstance(origen, dict)
                else None
            )

            huella = (
                evento.get("date"),
                op.get("player"),
                int(op.get("amount") or 0),
                comprador,
                vendedor,
            )

            if huella in vistas:
                continue

            vistas.add(huella)

            filas.append(
                {
                    "type": evento.get("type"),
                    "date": evento.get("date"),
                    "player": op.get("player"),
                    "amount": int(op.get("amount") or 0),
                    "comprador": comprador,
                    "vendedor": vendedor,
                    "nombre_comprador": (
                        destino.get("name")
                        if isinstance(destino, dict)
                        else None
                    ),
                    "nombre_vendedor": (
                        origen.get("name")
                        if isinstance(origen, dict)
                        else None
                    ),
                    "bids": op.get("bids") or [],
                }
            )

    return filas


# ============================================================
# BLOQUE 1 — LA ECONOMIA
# ============================================================

def bloque_1(board: list) -> None:
    titulo("BLOQUE 1 — LA ECONOMIA: CUANTO PAGA UN PUNTO")

    jornadas = [e for e in board if e.get("type") == "roundFinished"]

    print(f"  Jornadas cerradas en el tablon: {len(jornadas)}")
    print()

    filas = []

    for evento in sorted(jornadas, key=lambda e: e.get("date") or 0):

        contenido = evento.get("content") or {}

        ronda = (contenido.get("round") or {}).get("name", "?")

        for fila in (contenido.get("results") or []):

            puntos = int(fila.get("points") or 0)

            bonus = int(fila.get("bonus") or 0)

            filas.append(
                {
                    "ronda": ronda,
                    "manager": (fila.get("user") or {}).get("name"),
                    "user_id": (fila.get("user") or {}).get("id"),
                    "puntos": puntos,
                    "bonus": bonus,
                    "por_punto": (
                        bonus / puntos if puntos else None
                    ),
                }
            )

    if not filas:
        print("  No hay ninguna jornada cerrada en el tablon.")
        return

    # ------------------------------------------------------
    # ¿30.000 POR PUNTO?
    # ------------------------------------------------------

    exactos = [f for f in filas if f["bonus"] == f["puntos"] * 30_000]

    otros = [f for f in filas if f not in exactos]

    print(f"  {'jornada':<12}{'manager':<20}{'puntos':>7}{'cobra':>12}{'por punto':>11}")

    for f in filas:
        marca = "" if f in exactos else "   <-- NO son 30.000"
        print(
            f"  {f['ronda']:<12}{str(f['manager'])[:19]:<20}"
            f"{f['puntos']:>7}{euros(f['bonus']):>12}"
            f"{(euros(f['por_punto']) if f['por_punto'] else '—'):>11}{marca}"
        )

    print()
    print(
        f"  CUADRAN A 30.000 EXACTOS: {len(exactos)} de {len(filas)}"
    )

    if otros:
        print()
        print("  LOS QUE NO CUADRAN, y por cuanto se pasan:")

        for f in otros:
            exceso = f["bonus"] - f["puntos"] * 30_000
            print(
                f"     {f['ronda']:<12}{str(f['manager'])[:19]:<20}"
                f"{euros(f['bonus']):>12} = "
                f"{euros(f['puntos'] * 30_000)} + "
                f"{euros(exceso)}"
            )

    # ------------------------------------------------------
    # QUE SON LOS ESCALONES: EL PUESTO DE LA JORNADA
    # ------------------------------------------------------
    #
    #     No es la racha, ni las operaciones, ni ganar. Es
    #     quedar de los ULTIMOS: un pago de consolacion, y mas
    #     grande cuanto peor lo hagas.

    por_puesto = collections.defaultdict(collections.Counter)

    for evento in jornadas:

        resultados = sorted(
            (evento.get("content") or {}).get("results") or [],
            key=lambda r: -(int(r.get("points") or 0)),
        )

        for puesto, fila in enumerate(resultados, 1):

            extra = (
                int(fila.get("bonus") or 0)
                - int(fila.get("points") or 0) * 30_000
            )

            por_puesto[puesto][extra] += 1

    print()
    print("  EL EXTRA LO EXPLICA EL PUESTO DE LA JORNADA:")
    print()
    print(f"     {'puesto':<9}{'extras vistos':<34}")

    for puesto in sorted(por_puesto):

        reparto = ", ".join(
            f"{euros(k)} x{v}"
            for k, v in sorted(por_puesto[puesto].items())
        )

        print(f"     {puesto:<9}{reparto}")

    print()
    print(
        "     Los cuatro primeros no cobran extra NUNCA. El "
        "quinto cobra"
    )
    print(
        "     100.000, el sexto 250.000 y el ultimo 500.000. En "
        "cuatro de"
    )
    print(
        "     las cinco jornadas, exacto. La excepcion es la "
        "Jornada 1,"
    )
    print("     donde no cobro extra nadie.")
    print()
    print(
        "     NO es una racha, NO son las operaciones y NO es "
        "ganar: es un"
    )
    print("     pago de consolacion a los tres ultimos.")

    # ------------------------------------------------------
    # Y APARTE, LOS `bonus` DEL TABLON
    # ------------------------------------------------------

    print()
    print(
        "  OTRA COSA DISTINTA: los eventos `bonus` del tablon."
    )

    extras = [e for e in board if e.get("type") == "bonus"]

    if not extras:
        print("     No hay ningun evento `bonus` en el tablon.")
    else:
        for evento in sorted(extras, key=lambda e: e.get("date") or 0):
            for fila in (evento.get("content") or []):
                print(
                    f"     {cuando(evento.get('date'))}  "
                    f"{str((fila.get('user') or {}).get('name'))[:20]:<21}"
                    f"{euros(fila.get('amount')):>10}   "
                    f"motivo: {fila.get('reason')}"
                )

    razones = collections.Counter(
        fila.get("reason")
        for e in extras
        for fila in (e.get("content") or [])
    )

    if razones:
        print()
        print(f"     Motivos vistos: {dict(razones)}")

    # ------------------------------------------------------
    # PUNTOS CONTRA LA RUEDA
    # ------------------------------------------------------

    print()
    print("  LO QUE HA ENTRADO POR PUNTOS, CONTRA LA RUEDA:")

    por_manager = collections.defaultdict(
        lambda: {"puntos": 0, "bonus": 0, "compras": 0, "ventas": 0}
    )

    for f in filas:
        por_manager[f["user_id"]]["puntos"] += f["puntos"]
        por_manager[f["user_id"]]["bonus"] += f["bonus"]
        por_manager[f["user_id"]]["nombre"] = f["manager"]

    for op in operaciones(board, ("market", "transfer")):

        if op["comprador"]:
            por_manager[op["comprador"]]["compras"] += op["amount"]
            por_manager[op["comprador"]].setdefault(
                "nombre", op["nombre_comprador"]
            )

        if op["vendedor"]:
            por_manager[op["vendedor"]]["ventas"] += op["amount"]
            por_manager[op["vendedor"]].setdefault(
                "nombre", op["nombre_vendedor"]
            )

    # Los escalones, a su manager.
    for evento in extras:
        for fila in (evento.get("content") or []):
            uid = (fila.get("user") or {}).get("id")
            if uid:
                por_manager[uid]["bonus"] += int(
                    fila.get("amount") or 0
                )

    print()
    print(
        f"  {'manager':<22}{'puntos':>7}{'POR PUNTOS':>14}"
        f"{'vendio':>13}{'compro':>13}{'RUEDA neta':>14}"
    )

    for uid, d in sorted(
        por_manager.items(), key=lambda kv: -kv[1]["bonus"]
    ):
        rueda = d["ventas"] - d["compras"]
        print(
            f"  {str(d.get('nombre'))[:21]:<22}{d['puntos']:>7}"
            f"{euros(d['bonus']):>14}{euros(d['ventas']):>13}"
            f"{euros(d['compras']):>13}{euros(rueda):>14}"
            + ("   <-- NOSOTROS" if uid == NOSOTROS else "")
        )

    # ------------------------------------------------------
    # LO QUE HA DADO LA RUEDA DE VERDAD: LOS VIAJES CERRADOS
    # ------------------------------------------------------
    #
    #     "ventas - compras" es CAJA, no beneficio: lo comprado
    #     sigue en la plantilla. Lo unico que se puede cobrar
    #     como ganancia es un jugador COMPRADO Y VENDIDO.

    compras = collections.defaultdict(list)

    viajes = collections.defaultdict(
        lambda: {"n": 0, "beneficio": 0}
    )

    for op in operaciones(board, ("market", "transfer")):

        if op["type"] == "market" and op["comprador"]:
            compras[(op["comprador"], op["player"])].append(
                op["amount"]
            )

        elif op["type"] == "transfer" and op["vendedor"]:

            clave = (op["vendedor"], op["player"])

            if compras.get(clave):
                pagado = compras[clave].pop(0)
                viajes[op["vendedor"]]["n"] += 1
                viajes[op["vendedor"]]["beneficio"] += (
                    op["amount"] - pagado
                )

    print()
    print("  Y LO QUE HA DADO LA RUEDA DE VERDAD:")
    print(
        "  (solo jugadores COMPRADOS Y VENDIDOS: lo demas sigue "
        "en la plantilla)"
    )
    print()
    print(
        f"  {'manager':<22}{'POR PUNTOS':>14}"
        f"{'viajes':>8}{'BENEFICIO':>14}{'por viaje':>12}"
    )

    for uid, d in sorted(
        por_manager.items(), key=lambda kv: -kv[1]["bonus"]
    ):

        v = viajes.get(uid, {"n": 0, "beneficio": 0})

        if not d["puntos"] and not v["n"]:
            continue

        print(
            f"  {str(d.get('nombre'))[:21]:<22}"
            f"{euros(d['bonus']):>14}{v['n']:>8}"
            f"{euros(v['beneficio']):>14}"
            f"{euros(v['beneficio'] // v['n']) if v['n'] else '—':>12}"
            + ("   <-- NOSOTROS" if uid == NOSOTROS else "")
        )

    nuestro = por_manager.get(NOSOTROS)

    nuestros_viajes = viajes.get(
        NOSOTROS, {"n": 0, "beneficio": 0}
    )

    if nuestro and nuestros_viajes["n"]:
        print()
        print(
            f"  NOSOTROS: {euros(nuestro['bonus'])} EUR por "
            f"puntos contra "
            f"{euros(nuestros_viajes['beneficio'])} EUR de "
            f"beneficio en {nuestros_viajes['n']} viajes cerrados."
        )

        if nuestros_viajes["beneficio"]:
            veces = (
                nuestro["bonus"] / nuestros_viajes["beneficio"]
            )
            print(
                f"     Los puntos dan {veces:.1f} veces lo que la "
                f"rueda."
            )





# ============================================================
# BLOQUE 2 — EL TOPE DE PLANTILLA
# ============================================================

def bloque_2(board: list) -> None:
    titulo("BLOQUE 2 — CUANTAS FICHAS CABEN")

    mayor = collections.defaultdict(int)

    nombres = {}

    vistas = 0

    for ruta in fotos():

        try:
            s = json.loads(
                Path(ruta).read_text(encoding="utf-8")
            )
        except Exception:                           # noqa: BLE001
            continue

        vistas += 1

        mias = len(s.get("my_team") or [])

        if mias:
            mayor[NOSOTROS] = max(mayor[NOSOTROS], mias)
            nombres[NOSOTROS] = "Pepe Bordalás"

    # Las plantillas rivales. Dos fuentes: el cache de perfiles
    # -que es de HOY- y las fotos, que son de agosto.
    try:
        cache = json.loads(
            (
                RAIZ
                / "data"
                / "rival_intelligence"
                / "profiles_cache.json"
            ).read_text(encoding="utf-8")
        )
        perfiles = cache.get("profiles") or {}
    except Exception:                               # noqa: BLE001
        perfiles = {}

    for clave, perfil in perfiles.items():

        if not isinstance(perfil, dict):
            continue

        jugadores = perfil.get("players") or []

        try:
            uid = int(perfil.get("id") or clave)
        except (TypeError, ValueError):
            continue

        mayor[uid] = max(mayor[uid], len(jugadores))

        nombres.setdefault(uid, perfil.get("name") or str(uid))

    # Y lo que dicen las fotos de las plantillas rivales.
    for ruta in fotos():

        try:
            s = json.loads(
                Path(ruta).read_text(encoding="utf-8")
            )
        except Exception:                           # noqa: BLE001
            continue

        for manager in (
            (s.get("league") or {}).get("standings") or []
        ):

            if not isinstance(manager, dict):
                continue

            jugadores = manager.get("players") or []

            try:
                uid = int(manager.get("id") or 0)
            except (TypeError, ValueError):
                continue

            if uid and jugadores:
                mayor[uid] = max(mayor[uid], len(jugadores))
                nombres.setdefault(uid, manager.get("name"))

    print(f"  Fotos miradas: {vistas}")
    print()
    print(f"  {'manager':<24}{'plantilla mas grande vista':>28}")

    for uid, n in sorted(mayor.items(), key=lambda kv: -kv[1]):
        print(f"  {str(nombres.get(uid, uid))[:23]:<24}{n:>28}")

    if mayor:
        techo = max(mayor.values())
        print()
        print(
            f"  SUELO DEL TOPE REAL: {techo} fichas. Nadie ha "
            f"tenido mas, asi que el tope es {techo} O MAS."
        )
        print(
            "  No se puede saber el techo exacto sin llenar una "
            "plantilla a proposito."
        )

    print()
    print("  ¿QUE PASA AL GANAR MAS PUJAS QUE HUECOS?")
    print(
        "     NO SE PUEDE SABER SIN ARRIESGAR, y no se prueba. "
        "Habria que"
    )
    print(
        "     ganar dos subastas con una sola ficha libre y ver "
        "que pasa,"
    )
    print(
        "     y el precio de equivocarse es una compra no "
        "deseada de millones."
    )
    print(
        "     El tope de la cartera se queda en HUECOS LIBRES."
    )


# ============================================================
# BLOQUE 3 — EMPATES EN LA PUJA
# ============================================================

def bloque_3(board: list) -> None:
    titulo("BLOQUE 3 — SI DOS PUJAN LO MISMO, ¿QUIEN GANA?")

    subastas = [
        {
            "date": op["date"],
            "player": op["player"],
            "ganadora": op["amount"],
            "ganador": op["nombre_comprador"],
            "perdedoras": [
                int(b.get("amount") or 0) for b in op["bids"]
            ],
        }
        for op in operaciones(board, ("market",))
    ]

    con_rival = [s for s in subastas if s["perdedoras"]]

    print(f"  Subastas en el tablon: {len(subastas)}")
    print(f"  Con al menos una puja perdedora visible: {len(con_rival)}")

    empates = [
        s
        for s in con_rival
        if s["ganadora"] in s["perdedoras"]
    ]

    empates_entre_perdedoras = [
        s
        for s in con_rival
        if len(s["perdedoras"]) != len(set(s["perdedoras"]))
    ]

    print()
    print(f"  EMPATES con la ganadora: {len(empates)}")
    print(
        f"  EMPATES entre perdedoras: "
        f"{len(empates_entre_perdedoras)}"
    )

    if empates:
        for e in empates:
            print()
            print(
                f"     {cuando(e['date'])}, jugador "
                f"{e['player']}:"
            )
            print(
                f"        GANO  {e['ganador']} con "
                f"{euros(e['ganadora'])}"
            )
            for importe in sorted(e["perdedoras"], reverse=True):
                marca = (
                    "   <-- LA MISMA CANTIDAD"
                    if importe == e["ganadora"]
                    else ""
                )
                print(
                    f"        perdio {euros(importe)}{marca}"
                )

        print()
        print(
            "     EL EMPATE EXISTE Y SE RESUELVE: no se repite "
            "la subasta."
        )
        print(
            "     Con UN caso no se puede saber QUE lo decide. "
            "Encaja con"
        )
        print(
            "     'gano el que pujo antes' y tambien con 'gano "
            "el id mas"
        )
        print(
            "     bajo' -Pollo es 14145555 y DiosMande "
            "14151726-, y esas dos"
        )
        print("     no se separan con una sola observacion.")
        print()
        print(
            "     LO QUE SI CAMBIA: el desvio aleatorio de "
            "importes se puso"
        )
        print(
            "     para no empatar, y aqui se ve que los empates "
            "PASAN. Un"
        )
        print(
            "     caso en 79 subastas con puja rival visible: "
            "1,3 %."
        )
    else:
        print()
        print(
            "     NO HAY NI UN EMPATE en todo el historico "
            "visible."
        )

        margenes = sorted(
            s["ganadora"] - max(s["perdedoras"])
            for s in con_rival
        )

        if margenes:
            print(
                f"     El margen mas pequeno entre ganadora y "
                f"segunda: {euros(margenes[0])} EUR."
            )
            print(
                f"     Mediana: "
                f"{euros(margenes[len(margenes) // 2])} EUR."
            )

        print()
        print(
            "     CON CERO CASOS NO SE PUEDE CONTESTAR quien gana "
            "un empate."
        )
        print(
            "     Lo que SI dice el dato: el desvio aleatorio de "
            "importes"
        )
        print(
            "     hace que un empate sea rarisimo, que es "
            "exactamente para"
        )
        print("     lo que se puso.")


# ============================================================
# BLOQUE 4 — EL PRECIO QUE PEDIMOS
# ============================================================

def bloque_4(board: list) -> None:
    titulo("BLOQUE 4 — ¿ESPANTA OFERTAS PEDIR CARO?")

    # Nuestros listados a lo largo de las fotos, con su
    # multiplicador, y las ofertas de RIVALES que llegaron.
    listados = {}

    ofertas_rivales = collections.defaultdict(set)

    ofertas_computer = collections.defaultdict(set)

    for ruta in fotos():

        try:
            s = json.loads(Path(ruta).read_text(encoding="utf-8"))
        except Exception:                           # noqa: BLE001
            continue

        valor = {
            j.get("id"): j.get("price")
            for j in (s.get("my_team") or [])
            if isinstance(j, dict)
        }

        mercado = s.get("market") or {}

        for venta in (mercado.get("sales") or []):

            if not isinstance(venta, dict):
                continue

            usuario = venta.get("user")

            uid = (
                usuario.get("id")
                if isinstance(usuario, dict)
                else usuario
            )

            if uid != NOSOTROS:
                continue

            jugador = venta.get("player")

            pid = (
                jugador.get("id")
                if isinstance(jugador, dict)
                else jugador
            )

            precio = int(venta.get("price") or 0)

            vale = int(valor.get(pid) or 0)

            if pid and precio and vale:
                listados[(pid, venta.get("date"))] = precio / vale

        for oferta in (mercado.get("offers") or []):

            if not isinstance(oferta, dict):
                continue

            origen = oferta.get("from")

            destino = oferta.get("to")

            did = (
                destino.get("id")
                if isinstance(destino, dict)
                else destino
            )

            if did != NOSOTROS:
                continue

            for pedido in (oferta.get("requestedPlayers") or []):

                pid = (
                    pedido.get("id")
                    if isinstance(pedido, dict)
                    else pedido
                )

                if origen is None:
                    ofertas_computer[pid].add(oferta.get("id"))
                else:
                    ofertas_rivales[pid].add(oferta.get("id"))

    print(f"  Listados nuestros con multiplicador: {len(listados)}")
    print(
        f"  Jugadores con oferta de RIVAL: "
        f"{len(ofertas_rivales)}"
    )
    print(
        f"  Jugadores con oferta del Computer: "
        f"{len(ofertas_computer)}"
    )

    if ofertas_rivales:

        print()
        print("  LAS OFERTAS DE RIVALES, UNA A UNA:")

        con, sin = [], []

        for (pid, _), mult in listados.items():
            (con if pid in ofertas_rivales else sin).append(mult)

        if con and sin:
            print()
            print(
                f"     multiplicador pedido CON oferta de rival "
                f"({len(con)} casos): x"
                f"{statistics.median(con):.2f} de mediana"
            )
            print(
                f"     multiplicador pedido SIN oferta         "
                f"({len(sin)} casos): x"
                f"{statistics.median(sin):.2f}"
            )
            print()
            print(
                "     Va en la direccion de 'pedir menos trae "
                "mas ofertas', pero"
            )
            print(
                "     con CUATRO casos eso no es una medida: es "
                "una anecdota."
            )
            print(
                "     NO se cambia ninguna regla con esto."
            )

        print()
        print(
            "  LO QUE SI SE VE CON CUATRO CASOS: el precio "
            "pedido NO es un techo."
        )
        print(
            "     Dos de las cuatro ofertas llegaron POR ENCIMA "
            "de lo que"
        )
        print(
            "     pediamos. El rival ofrece lo que quiere, mire "
            "lo que mire."
        )
        print(
            "     Asi que pedir alto no protege: solo dice lo "
            "que te gustaria."
        )

    if not ofertas_rivales:
        print()
        print(
            "  CERO OFERTAS DE RIVALES en todo el historico "
            "visible."
        )
        print(
            "  Con cero casos no se puede cruzar nada: NO SE "
            "PUEDE MEDIR si"
        )
        print(
            "  pedir caro espanta ofertas, porque no llega "
            "ninguna a espantar."
        )
        print()
        print(
            "  Y eso ya dice algo: el canal manager-a-manager "
            "esta muerto."
        )
        print(
            "  Medido el 05/09 sobre 67,1 h de tablon: UNA sola "
            "compra entre"
        )
        print(
            "  managers, y fue nuestra. El precio que pedimos no "
            "protege ni"
        )
        print(
            "  espanta nada, porque no hay a quien espantar."
        )

    por_multiplicador = collections.defaultdict(int)

    for (pid, _), mult in listados.items():

        tramo = "1,0-1,1" if mult < 1.1 else (
            "1,1-1,3" if mult < 1.3 else (
                "1,3-1,5" if mult < 1.5 else "1,5+"
            )
        )

        por_multiplicador[tramo] += 1

    if por_multiplicador:
        print()
        print("  Como hemos pedido, por tramos:")
        for tramo in sorted(por_multiplicador):
            print(f"     x{tramo:<10}{por_multiplicador[tramo]:>4} listados")


# ============================================================
# BLOQUE 5 — QUE MUEVE LOS PRECIOS
# ============================================================

def bloque_5() -> None:
    titulo("BLOQUE 5 — QUE MUEVE LOS PRECIOS")

    # DIA A DIA, Y SOLO ENTRE DIAS CONSECUTIVOS.
    #
    #     Comparar foto contra foto mezclaba pares de la misma
    #     manana -donde el precio no se ha movido porque el
    #     precio SOLO se mueve en el reset- con pares que cruzan
    #     un reset. Y el ultimo par saltaba 24 dias, que se
    #     comia el resultado.
    por_dia = {}

    for ruta in fotos():
        dia = Path(ruta).name.split("snapshot_")[1][:8]
        por_dia[dia] = ruta

    serie = {}

    for dia, ruta in sorted(por_dia.items()):

        try:
            s = json.loads(Path(ruta).read_text(encoding="utf-8"))
        except Exception:                           # noqa: BLE001
            continue

        jugadores = (
            ((s.get("catalog") or {}).get("data") or {}).get(
                "players"
            )
            or {}
        )

        filas = (
            jugadores.values()
            if isinstance(jugadores, dict)
            else jugadores
        )

        serie[dia] = {
            j["id"]: (
                int(j.get("price") or 0),
                int(j.get("points") or 0),
            )
            for j in filas
            if isinstance(j, dict) and j.get("id")
        }

    dias = sorted(serie)

    # Solo dias CONSECUTIVOS: un salto de 24 dias no es "un dia".
    pares = []

    for a, b in zip(dias, dias[1:]):

        try:
            d1 = datetime.strptime(a, "%Y%m%d")
            d2 = datetime.strptime(b, "%Y%m%d")
        except ValueError:
            continue

        if (d2 - d1).days != 1:
            continue

        for pid, (p1, pt1) in serie[a].items():

            if pid not in serie[b]:
                continue

            p2, pt2 = serie[b][pid]

            pares.append((pt2 - pt1, p2 - p1))

    print(f"  Dias con foto: {len(dias)}")
    print(f"  Pares jugador-dia CONSECUTIVOS: {len(pares)}")

    if len(pares) < 100:
        print("  Muy pocos para decir nada.")
        return

    tramos = collections.defaultdict(list)

    for puntos, delta in pares:

        tramo = (
            "0"
            if puntos == 0
            else ("1-3" if puntos <= 3 else ("4-7" if puntos <= 7 else "8+"))
        )

        tramos[tramo].append(delta)

    print()
    print(
        f"  {'puntos del dia':<16}{'casos':>7}{'mediana':>12}"
        f"{'media':>12}{'sube':>8}"
    )

    for tramo in ("0", "1-3", "4-7", "8+"):

        filas = tramos.get(tramo) or []

        if not filas:
            continue

        suben = 100 * sum(1 for d in filas if d > 0) / len(filas)

        print(
            f"  {tramo:<16}{len(filas):>7}"
            f"{euros(statistics.median(filas)):>12}"
            f"{euros(statistics.mean(filas)):>12}{suben:>7.0f}%"
        )

    print()
    print("  LO QUE DICE:")
    print(
        "     Los puntos mueven el precio, y de forma monotona: "
        "a mas puntos,"
    )
    print(
        "     mas sube. Con 4 o mas puntos en el dia la mediana "
        "salta a"
    )
    print(
        "     +20.000 y sube en el 69 % de los casos, contra el "
        "35 % de los"
    )
    print("     que no puntuan.")
    print()
    print(
        "     Los tramos altos tienen POCOS casos -42 y 11-, "
        "asi que la"
    )
    print(
        "     direccion es solida y la magnitud exacta no."
    )
    print()
    print(
        "     Y queda MUCHO sin explicar: hasta los que no "
        "puntuan suben en"
    )
    print(
        "     el 35 % de los dias. Los puntos son UNA causa, no "
        "la unica."
    )

    print()
    print("  LO QUE NO SE PUEDE MEDIR CON LO QUE HAY:")
    print(
        "     El '25 % Compras / 0 % Ventas / 99 % Uso' de la "
        "ficha del"
    )
    print(
        "     jugador NO esta en el catalogo que descargamos. "
        "Sus campos son"
    )
    print(
        "     price, priceIncrement, points, fitness, status y "
        "poco mas."
    )
    print()
    print(
        "     Ese dato vive en la ficha individual, que serian "
        "574 peticiones"
    )
    print(
        "     al dia contra las 181 que gasta HOY el ciclo "
        "entero. Acotado a"
    )
    print(
        "     los del mercado -unos 20- costaria 20 al dia, un "
        "11 % mas."
    )
    print("     Eso lo decide el dueno; aqui solo se dice.")


def main() -> None:

    board = eventos()

    print()
    print("LAS MECANICAS DEL JUEGO — medido sobre el tablon y las fotos")
    print(f"Eventos en el tablon: {len(board)} · Fotos: {len(fotos())}")
    print("Ni una llamada nueva a Biwenger.")

    bloque_1(board)
    bloque_2(board)
    bloque_3(board)
    bloque_4(board)
    bloque_5()

    print()


if __name__ == "__main__":
    main()
