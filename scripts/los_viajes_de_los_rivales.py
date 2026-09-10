"""
Los viajes cerrados de Pollo17 y Manzagool, uno a uno.

LA PREGUNTA QUE CONTESTA

    "De sus 36 compras, ¿cuantas habriamos hecho nosotros, y
     cuanto dinero hay en las que NO?"

    Si la mayoria no pasan nuestro filtro, el problema no era el
    reloj: es el filtro, y llevamos un mes rechazando el negocio
    de la liga.

NUESTRO FILTRO NO ES UN NUMERO, SON DOS PUERTAS

    Y la segunda es mas dura que la primera, aunque no la hemos
    estado mirando:

    1. LA COMPUERTA DE RITMO (`market_rate_gate`)

           Sin RITMO OBSERVADO por el ojeador, la via de
           especulacion no se abre siquiera: `SIN_RITMO_OBSERVADO`.
           Y con ritmo negativo tampoco: `PRECIO_CAYENDO`.

           El ojeador existe desde el 08/09/2026. Antes de esa
           fecha NO HAY ritmo observado de nadie.

    2. EL RENDIMIENTO (`RENDIMIENTO_MINIMO_DEL_CAPITAL = 0.03`)

           expected_value / bid >= 3 %. Ojo: es rendimiento
           SOBRE EL CAPITAL de la operacion, no un ritmo diario.
           Se ha hablado de el como "el 3 % diario" y no lo es.

LO QUE SE PUEDE MEDIR Y LO QUE NO

    EX-POST -lo que paso de verdad- se puede para los 36 viajes:
    cuanto pago, cuanto cobro, cuantos dias y que rindio.

    EX-ANTE -lo que nuestro filtro habria visto el dia de la
    compra- necesita el precio de los dias ANTERIORES a cada
    compra, y el historico local solo cubre del 12 al 17/08 mas
    hoy. Se dice en cada fila si se pudo o no.

    Las vias XI_UPGRADE, ROSTER_FILL y TENER dependen de COMO
    ESTABA NUESTRA PLANTILLA ese dia, y de eso solo hay fotos
    del 12 al 17/08. Fuera de ahi se dice "no reconstruible" en
    vez de inventarlo.

COMO SE USA

    python -m scripts.los_viajes_de_los_rivales
"""

from __future__ import annotations

import collections
import glob
import json

from datetime import datetime, timedelta, timezone
from pathlib import Path


RAIZ = Path(__file__).parent.parent

MADRID = timezone(timedelta(hours=2))

POLLO = 14145555

MANZAGOOL = 14176382

NOSOTROS = 14175949


# El ojeador empezo a publicar ritmos el 08/09/2026. Antes de esa
# fecha, `market_rate_gate` devuelve SIN_RITMO_OBSERVADO para
# todo el mundo y la via de especulacion no se abre.
OJEADOR_DESDE = datetime(2026, 9, 8, tzinfo=MADRID)


def euros(valor) -> str:
    try:
        return f"{int(valor):,}".replace(",", ".")
    except (TypeError, ValueError):
        return "?"


def dia(epoch) -> str:
    try:
        return datetime.fromtimestamp(epoch, MADRID).strftime(
            "%d/%m"
        )
    except Exception:                               # noqa: BLE001
        return "?"


def viajes_de(uid: int) -> list:
    """Compro y vendio: los unicos con beneficio cobrable."""

    from scripts.las_mecanicas_del_juego import operaciones

    board = json.loads(
        (
            RAIZ
            / "data"
            / "rival_intelligence"
            / "board_events.json"
        ).read_text(encoding="utf-8")
    )

    compras = collections.defaultdict(list)

    cerrados = []

    for op in operaciones(board, ("market", "transfer")):

        if op["type"] == "market" and op["comprador"] == uid:
            compras[op["player"]].append(op)

        elif (
            op["type"] == "transfer"
            and op["vendedor"] == uid
            and compras.get(op["player"])
        ):

            compra = compras[op["player"]].pop(0)

            dias = max(
                1,
                round(
                    (op["date"] - compra["date"]) / 86400.0
                ),
            )

            cerrados.append(
                {
                    "player": op["player"],
                    "compra": compra["date"],
                    "pagado": compra["amount"],
                    "venta": op["date"],
                    "cobrado": op["amount"],
                    "beneficio": op["amount"] - compra["amount"],
                    "dias": dias,
                    "rendimiento": (
                        (op["amount"] - compra["amount"])
                        / max(compra["amount"], 1)
                    ),
                }
            )

    return cerrados


def historico() -> dict:
    try:
        return json.loads(
            (
                RAIZ / "data" / "autopilot" / "price_history.json"
            ).read_text(encoding="utf-8")
        ).get("players") or {}
    except Exception:                               # noqa: BLE001
        return {}


def ritmo_antes(serie: dict, cuando: int):
    """
    El ritmo %/dia con los DOS ultimos precios anteriores a la
    compra, y cuantos dias hace de esa lectura.

    Devuelve (ritmo, antiguedad_en_dias) o (None, None).
    """

    if not serie:
        return None, None

    pares = [
        (t, p)
        for t, p in zip(serie.get("t") or [], serie.get("p") or [])
        if t <= cuando
    ]

    if len(pares) < 2:
        return None, None

    (t0, p0), (t1, p1) = pares[-2], pares[-1]

    dias = max((t1 - t0) / 86400.0, 0.25)

    if not p0:
        return None, None

    ritmo = ((p1 / p0) ** (1 / dias) - 1) * 100

    return ritmo, (cuando - t1) / 86400.0


def nuestra_plantilla_el(cuando: int):
    """
    Nuestro once y nuestra plantilla en la foto MAS CERCANA
    anterior. None si no hay ninguna del mismo dia o el
    anterior: reconstruir con una foto de tres semanas despues
    seria inventarselo.
    """

    mejor = None

    for ruta in sorted(
        glob.glob(str(RAIZ / "data" / "snapshot_*.json"))
    ):

        marca = Path(ruta).name.split("snapshot_")[1][:15]

        try:
            momento = datetime.strptime(
                marca, "%Y%m%d_%H%M%S"
            ).replace(tzinfo=MADRID)
        except ValueError:
            continue

        epoch = momento.timestamp()

        if epoch > cuando:
            continue

        if (cuando - epoch) > 36 * 3600:
            continue

        mejor = ruta

    if not mejor:
        return None

    try:
        return json.loads(
            Path(mejor).read_text(encoding="utf-8")
        )
    except Exception:                               # noqa: BLE001
        return None


def vias(viaje: dict, ritmo, foto) -> dict:
    """
    Que habria dicho cada una de nuestras cuatro vias.

    SPECULATION se puede contestar SIEMPRE, porque la primera
    puerta no depende de nuestra plantilla: depende de si el
    ojeador tenia ritmo de ese jugador ese dia.
    """

    cuando = datetime.fromtimestamp(viaje["compra"], MADRID)

    veredicto = {}

    # --- SPECULATION -------------------------------------
    if cuando < OJEADOR_DESDE:
        veredicto["SPECULATION"] = (
            "NO",
            "SIN_RITMO_OBSERVADO (el ojeador no existia)",
        )

    elif ritmo is None:
        veredicto["SPECULATION"] = (
            "NO",
            "SIN_RITMO_OBSERVADO",
        )

    elif ritmo < 0:
        veredicto["SPECULATION"] = (
            "NO",
            f"PRECIO_CAYENDO ({ritmo:+.2f} %/dia)",
        )

    else:
        veredicto["SPECULATION"] = (
            "quizá",
            f"ritmo {ritmo:+.2f} %/dia; faltaria el 3 % de "
            f"rendimiento",
        )

    # --- LAS TRES QUE DEPENDEN DE NUESTRA PLANTILLA ------
    if foto is None:
        for via in ("XI_UPGRADE", "ROSTER_FILL", "TENER"):
            veredicto[via] = ("?", "no reconstruible")
        return veredicto

    plantilla = foto.get("my_team") or []

    catalogo = (
        ((foto.get("catalog") or {}).get("data") or {}).get(
            "players"
        )
        or {}
    )

    filas = (
        catalogo.values()
        if isinstance(catalogo, dict)
        else catalogo
    )

    jugador = next(
        (
            j
            for j in filas
            if isinstance(j, dict)
            and j.get("id") == viaje["player"]
        ),
        None,
    )

    if not jugador:
        for via in ("XI_UPGRADE", "ROSTER_FILL", "TENER"):
            veredicto[via] = ("?", "no estaba en el catalogo")
        return veredicto

    posicion = jugador.get("position")

    puntos = int(jugador.get("points") or 0)

    mios = [
        j
        for j in plantilla
        if isinstance(j, dict) and j.get("position") == posicion
    ]

    peor = min(
        (int(j.get("points") or 0) for j in mios),
        default=None,
    )

    # ROSTER_FILL: ¿habia hueco? 21 fichas es el suelo medido.
    huecos = 21 - len(plantilla)

    veredicto["ROSTER_FILL"] = (
        ("sí", f"{huecos} huecos con el tope medido de 21")
        if huecos > 0
        else ("NO", "sin huecos")
    )

    veredicto["XI_UPGRADE"] = (
        ("sí", f"{puntos} pts contra {peor} del peor nuestro")
        if peor is not None and puntos > peor
        else (
            "NO",
            f"{puntos} pts, no mejora al peor nuestro ({peor})",
        )
    )

    # TENER: la via larga. Con los puntos que llevaba, ¿estaba
    # rindiendo? Sin jornadas suficientes no se puede decir.
    veredicto["TENER"] = (
        ("quizá", f"{puntos} pts acumulados")
        if puntos > 0
        else ("NO", "sin puntos")
    )

    return veredicto


def informe(nombre: str, uid: int, detalle: bool = True) -> None:

    print()
    print("=" * 78)
    print(f"{nombre.upper()} — LOS VIAJES CERRADOS, UNO A UNO")
    print("=" * 78)

    trips = viajes_de(uid)

    hist = historico()

    total = sum(t["beneficio"] for t in trips)

    print(
        f"  {len(trips)} viajes · beneficio total "
        f"{euros(total)} EUR"
    )
    print()

    if detalle:
        print(
            f"  {'compra':<7}{'jug':<7}{'pagado':>11}"
            f"{'cobrado':>11}{'benef':>11}{'d':>4}"
            f"{'rend':>8}{'ritmo ex-ante':>16}  SPECULATION"
        )

    haria = []

    no_haria = []

    for t in sorted(trips, key=lambda x: x["compra"]):

        ritmo, antiguedad = ritmo_antes(
            hist.get(str(t["player"])), t["compra"]
        )

        foto = nuestra_plantilla_el(t["compra"])

        v = vias(t, ritmo, foto)

        t["vias"] = v

        t["ritmo"] = ritmo

        # ¿La habriamos hecho? Basta con que UNA via diga que si.
        alguna = [
            via
            for via, (r, _) in v.items()
            if r in ("sí", "quizá")
        ]

        (haria if alguna else no_haria).append(t)

        if detalle:

            texto_ritmo = (
                f"{ritmo:+.2f} %/d"
                + (
                    f" ({antiguedad:.0f}d viejo)"
                    if antiguedad and antiguedad > 1.5
                    else ""
                )
                if ritmo is not None
                else "sin datos"
            )

            print(
                f"  {dia(t['compra']):<7}{t['player']:<7}"
                f"{euros(t['pagado']):>11}{euros(t['cobrado']):>11}"
                f"{euros(t['beneficio']):>11}{t['dias']:>4}"
                f"{t['rendimiento'] * 100:>7.1f}%"
                f"{texto_ritmo:>16}  {v['SPECULATION'][1][:34]}"
            )

    # ------------------------------------------------------
    # EL RESUMEN
    # ------------------------------------------------------

    print()
    print("  " + "-" * 74)
    print("  ¿CUANTAS HABRIAMOS HECHO NOSOTROS?")
    print("  " + "-" * 74)

    por_via = collections.Counter()

    for t in trips:
        for via, (r, _) in (t.get("vias") or {}).items():
            if r in ("sí", "quizá"):
                por_via[via] += 1

    print()
    print(f"     {'via':<14}{'la abre en':>12}{'de':>5}")

    for via in ("SPECULATION", "XI_UPGRADE", "ROSTER_FILL", "TENER"):
        print(f"     {via:<14}{por_via[via]:>12}{len(trips):>5}")

    dinero_no = sum(t["beneficio"] for t in no_haria)

    dinero_si = sum(t["beneficio"] for t in haria)

    print()
    print(
        f"     LAS HARIAMOS:    {len(haria):>3} viajes, "
        f"{euros(dinero_si)} EUR"
    )
    print(
        f"     NO LAS HARIAMOS: {len(no_haria):>3} viajes, "
        f"{euros(dinero_no)} EUR"
    )

    if trips:
        print()
        print(
            f"     Es el {100 * len(no_haria) / len(trips):.0f} % de "
            f"sus compras y el "
            f"{100 * dinero_no / total if total else 0:.0f} % de su "
            f"dinero."
        )

    # Y el rendimiento, contra nuestro 3 %.
    pasan = [t for t in trips if t["rendimiento"] >= 0.03]

    print()
    print(
        f"     Con el 3 % de rendimiento EX-POST: pasan "
        f"{len(pasan)} de {len(trips)} "
        f"({euros(sum(t['beneficio'] for t in pasan))} EUR)."
    )
    print(
        "     Ex-post, no ex-ante: es lo que rindieron, no lo "
        "que se veia."
    )


def precios_por_dia() -> dict:
    """El precio de mercado de cada jugador, por dia con foto."""

    tabla = {}

    for ruta in sorted(
        glob.glob(str(RAIZ / "data" / "snapshot_*.json"))
    ):

        dia_foto = Path(ruta).name.split("snapshot_")[1][:8]

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

        tabla[dia_foto] = {
            j["id"]: int(j.get("price") or 0)
            for j in filas
            if isinstance(j, dict) and j.get("id")
        }

    return tabla


def descomposicion() -> None:
    """
    De donde sale la ganancia, en tres partes que suman.

        (a) lo que gana al COMPRAR   precio pagado contra mercado
        (b) la prima del Computer al VENDER
        (c) lo que subio mientras lo tuvo

    Las tres se miden sobre las operaciones que caen en un dia
    con foto, que es donde se sabe el precio de mercado.
    """

    import statistics

    from scripts.las_mecanicas_del_juego import operaciones

    print()
    print("=" * 78)
    print("DE DONDE SALE LA GANANCIA")
    print("=" * 78)

    board = json.loads(
        (
            RAIZ
            / "data"
            / "rival_intelligence"
            / "board_events.json"
        ).read_text(encoding="utf-8")
    )

    precios = precios_por_dia()

    def dia_clave(epoch):
        return datetime.fromtimestamp(epoch, MADRID).strftime(
            "%Y%m%d"
        )

    compra_por, venta_por = {}, {}

    for op in operaciones(board, ("market", "transfer")):

        precio = precios.get(dia_clave(op["date"]), {}).get(
            op["player"]
        )

        if not precio or not op["amount"]:
            continue

        prima = (op["amount"] - precio) / precio * 100

        if op["type"] == "market" and op["comprador"]:
            compra_por.setdefault(op["comprador"], []).append(prima)

        elif op["type"] == "transfer" and op["vendedor"]:
            venta_por.setdefault(op["vendedor"], []).append(prima)

    nombres = {
        POLLO: "Pollo17",
        MANZAGOOL: "Manzagool",
        NOSOTROS: "NOSOTROS",
        14156489: "Luismi_Haz",
        14151726: "DiosMande",
        14154203: "Prinzipote",
        14178736: "Mex",
    }

    print()
    print("  (a) LO QUE PAGA DE MAS EN LA SUBASTA")
    print("      (negativo = compra POR DEBAJO del precio)")
    print()
    print(f"      {'manager':<14}{'n':>4}{'mediana':>10}")

    for uid, xs in sorted(
        compra_por.items(), key=lambda kv: statistics.median(kv[1])
    ):
        print(
            f"      {nombres.get(uid, uid):<14}{len(xs):>4}"
            f"{statistics.median(xs):>+9.2f} %"
        )

    print()
    print("  (b) LO QUE LE PAGA EL COMPUTER AL VENDER")
    print()
    print(f"      {'manager':<14}{'n':>4}{'mediana':>10}")

    for uid, xs in sorted(
        venta_por.items(),
        key=lambda kv: -statistics.median(kv[1]),
    ):
        print(
            f"      {nombres.get(uid, uid):<14}{len(xs):>4}"
            f"{statistics.median(xs):>+9.2f} %"
        )

    # --- la cuenta del viaje mediano de Pollo ---
    a = statistics.median(compra_por.get(POLLO) or [0])
    b = statistics.median(venta_por.get(POLLO) or [0])

    trips = viajes_de(POLLO)

    rendimiento = (
        statistics.median([t["rendimiento"] for t in trips]) * 100
    )

    dias_medianos = statistics.median([t["dias"] for t in trips])

    print()
    print("  LA CUENTA DEL VIAJE MEDIANO DE POLLO:")
    print()
    print(f"      (a) compra                    {-a:+7.2f} %")
    print(f"      (b) prima del Computer        {b:+7.2f} %")
    print(f"      (a) + (b)                     {b - a:+7.2f} %")
    print(f"      su viaje mediano rinde        {rendimiento:+7.2f} %")
    print(
        f"      (c) el resto, en {dias_medianos:.0f} dias      "
        f"{rendimiento - (b - a):+7.2f} %"
        f"   = {(rendimiento - (b - a)) / dias_medianos:+.2f} %/dia"
    )
    print()
    print(
        f"      (a)+(b) son el "
        f"{100 * (b - a) / rendimiento:.0f} % de su ganancia."
    )


def calendario() -> None:
    """
    ¿Compra ANTES de que el jugador juegue y aguanta la jornada?
    """

    print()
    print("=" * 78)
    print("LA HIPOTESIS DEL CALENDARIO")
    print("=" * 78)

    import statistics

    board = json.loads(
        (
            RAIZ
            / "data"
            / "rival_intelligence"
            / "board_events.json"
        ).read_text(encoding="utf-8")
    )

    ini = {
        ((e.get("content") or {}).get("round") or {}).get("id"): e["date"]
        for e in board
        if e.get("type") == "roundStarted"
    }

    fin = {
        ((e.get("content") or {}).get("round") or {}).get("id"): e["date"]
        for e in board
        if e.get("type") == "roundFinished"
    }

    jornadas = [
        (ini[r], fin[r]) for r in ini if r in fin
    ]

    print(f"  Jornadas completas en el tablon: {len(jornadas)}")

    for nombre, uid in (
        ("Pollo17", POLLO),
        ("Manzagool", MANZAGOOL),
    ):

        trips = viajes_de(uid)

        con = [
            t
            for t in trips
            if any(
                t["compra"] <= a and b <= t["venta"]
                for a, b in jornadas
            )
        ]

        sin = [t for t in trips if t not in con]

        print()
        print(f"  {nombre}:")

        for etiqueta, grupo in (
            ("ATRAVIESAN una jornada", con),
            ("NO atraviesan ninguna ", sin),
        ):

            if not grupo:
                continue

            rend = statistics.median(
                [t["rendimiento"] for t in grupo]
            ) * 100

            dias = statistics.median([t["dias"] for t in grupo])

            print(
                f"     {etiqueta}  {len(grupo):>3} viajes  "
                f"{euros(sum(t['beneficio'] for t in grupo)):>12}  "
                f"mediana {rend:+.1f} % en {dias:.0f} dias "
                f"({rend / dias:+.2f} %/dia)"
            )


def main() -> None:

    print()
    print("LOS VIAJES DE LOS RIVALES — ¿los habriamos hecho nosotros?")
    print("Del tablon y del historico. Ni una llamada nueva.")

    informe("Pollo17", POLLO)

    informe("Manzagool", MANZAGOOL)

    descomposicion()

    calendario()

    print()


if __name__ == "__main__":
    main()
