"""
El ocho por ciento: contra que esta medido, y cuanto es de verdad.

QUE HACE

    Lee del disco lo que ya esta medido y llama a
    `src.analysis.la_prima_de_compra`. Aqui solo hay lectura y
    formato: la cuenta esta en el modulo, que no lee nada, para
    que la guardia pueda probarla con fixtures.

    No escribe nada contra Biwenger. No escribe nada en `data/`.

LAS TRES FUENTES, Y PARA QUE SIRVE CADA UNA

    board_events.json          las operaciones, con sus pujas
    price_history.json         el precio del dia (la referencia)
    bid_outcome_ledger.json    la via de cada compra NUESTRA, y
                               el contraste de la referencia

    Las fotos (`snapshot_*.json`) se leen SOLO para enseñar
    cuantas compras cubrian, que es el cuadro que se creyo.

COMO SE USA

    python -m scripts.el_ocho_por_ciento
    python -m scripts.el_ocho_por_ciento --detalle
"""

from __future__ import annotations

import argparse
import glob
import json

from datetime import datetime
from pathlib import Path

from src.analysis.la_prima_de_compra import (
    MADRID,
    bajo_el_agua,
    cuando_cambian_los_precios,
    indexar_precios,
    operaciones,
    precio_del_dia,
    primas,
)


RAIZ = Path(__file__).parent.parent

EVENTOS = RAIZ / "data" / "rival_intelligence" / "board_events.json"

PRECIOS = RAIZ / "data" / "autopilot" / "price_history.json"

LIBRO_DE_PUJAS = RAIZ / "data" / "trading" / "bid_outcome_ledger.json"

CARRIL = RAIZ / "data" / "trading" / "libro_del_carril.jsonl"

# SOLO PARA PONER NOMBRES. Ningun numero sale de aqui: el
# catalogo de hoy no sabe lo que valia un jugador en agosto.
FOTOS = "data/snapshot_*.json"

NOSOTROS = 14175949

POLLO = 14145555

NOMBRES = {
    NOSOTROS: "Pepe",
    POLLO: "Pollo17",
    14156489: "Luismi_Haz",
    14176382: "Manzagool",
    14178736: "Mex",
    14151726: "DiosMande",
    14154203: "Prinzipote",
    14456960: "Alvaro",
}


def pct(bloque, ancho: int = 22) -> str:
    """Una mediana NUNCA sale sin su n al lado."""

    if not bloque or not bloque.get("n"):
        return "sin muestra".rjust(ancho)

    return f"{bloque['median']:+7.2f}% (n={bloque['n']:>2})".rjust(
        ancho
    )


def dia(epoch) -> str:
    return datetime.fromtimestamp(int(epoch), MADRID).strftime(
        "%Y-%m-%d"
    )


def _leer(ruta: Path, por_defecto=None):
    try:
        return json.loads(ruta.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return por_defecto


def nombres_de_jugador() -> dict:
    """Los nombres, de la foto mas reciente. Solo para leer."""

    fotos = sorted(glob.glob(str(RAIZ / FOTOS)))

    if not fotos:
        return {}

    jugadores = (
        ((_leer(Path(fotos[-1])) or {}).get("catalog") or {}).get(
            "data"
        )
        or {}
    ).get("players") or {}

    return {
        int(k): (v or {}).get("name")
        for k, v in jugadores.items()
    }


def vias_nuestras() -> dict:
    """Por que via entro cada compra nuestra, segun nuestros libros."""

    via = {}

    libro = (_leer(LIBRO_DE_PUJAS) or {}).get("bids") or {}

    for apunte in libro.values():

        if apunte.get("outcome") != "WON":
            continue

        # UNA PUJA RECONSTRUIDA DESDE LA PLANTILLA NO SABE POR
        # QUE VIA ENTRO: se marca como tal, no se le inventa una.
        marca = apunte.get("intent") or (
            "RECONSTRUIDA"
            if apunte.get("recorded_by") == "PLANTILLA"
            else None
        )

        if marca:
            via.setdefault(apunte.get("player_id"), marca)

    if CARRIL.exists():
        for linea in CARRIL.read_text(
            encoding="utf-8"
        ).splitlines():

            if not linea.strip():
                continue

            try:
                fila = json.loads(linea)
            except ValueError:
                continue

            via[fila.get("player_id")] = (
                f"CARRIL/{fila.get('marca')}"
            )

    return via


def contraste(indice) -> dict:
    """
    El precio del dia contra nuestro `market_price` anotado.

    Separa las pujas anotadas EN VIVO de las reconstruidas: las
    reconstruidas guardan el precio del dia en que se
    reconstruyeron, asi que no valen de contraste y contarlas
    ensuciaria el numero.
    """

    libro = (_leer(LIBRO_DE_PUJAS) or {}).get("bids") or {}

    salida = {
        "vivo": {"iguales": 0, "distintos": 0, "casos": []},
        "reconstruidas": {"iguales": 0, "distintos": 0},
        "sin_muestra": 0,
    }

    for apunte in libro.values():

        anotado = apunte.get("market_price")

        cuando = apunte.get("placed_at")

        if not anotado or not cuando:
            salida["sin_muestra"] += 1
            continue

        try:
            momento = int(
                datetime.fromisoformat(cuando).timestamp()
            )
        except ValueError:
            salida["sin_muestra"] += 1
            continue

        referencia = precio_del_dia(
            indice, apunte.get("player_id"), momento
        )

        if referencia is None:
            salida["sin_muestra"] += 1
            continue

        grupo = (
            "reconstruidas"
            if apunte.get("recorded_by") == "PLANTILLA"
            else "vivo"
        )

        if referencia == anotado:
            salida[grupo]["iguales"] += 1

        else:
            salida[grupo]["distintos"] += 1

            if grupo == "vivo":
                salida["vivo"]["casos"].append(
                    {
                        "jugador": apunte.get("player_name"),
                        "cuando": cuando[:16],
                        "anotado": anotado,
                        "del_dia": referencia,
                    }
                )

    return salida


def cobertura_de_las_fotos(filas) -> dict:
    """Cuantas compras caen en un dia con foto. El cuadro viejo."""

    tabla = {}

    for ruta in sorted(glob.glob(str(RAIZ / "data" / "snapshot_*.json"))):

        fecha = Path(ruta).name.split("snapshot_")[1][:8]

        foto = _leer(Path(ruta))

        jugadores = (
            ((foto or {}).get("catalog") or {}).get("data") or {}
        ).get("players") or {}

        tabla[fecha] = {
            int(j["id"]): int(j.get("price") or 0)
            for j in jugadores.values()
            if isinstance(j, dict) and j.get("id")
        }

    cubiertas = {}

    for fila in filas:

        if not fila["buyer"]:
            continue

        clave = datetime.fromtimestamp(
            fila["date"], MADRID
        ).strftime("%Y%m%d")

        if tabla.get(clave, {}).get(fila["player"]):
            cubiertas.setdefault(fila["buyer"], []).append(fila)

    return {
        "dias_con_foto": len(tabla),
        "por_manager": {
            quien: len(xs) for quien, xs in cubiertas.items()
        },
    }


def main() -> int:

    parser = argparse.ArgumentParser()

    parser.add_argument("--detalle", action="store_true")

    opciones = parser.parse_args()

    eventos = _leer(EVENTOS, [])

    historico = (_leer(PRECIOS) or {}).get("players") or {}

    if not eventos or not historico:
        print("FALTA UNA FUENTE:")
        print(f"  {EVENTOS.name}: {len(eventos or [])} eventos")
        print(f"  {PRECIOS.name}: {len(historico)} jugadores")
        return 1

    indice = indexar_precios(historico)

    nombre = nombres_de_jugador()

    def quien_es(pid):
        return nombre.get(pid) or f"jugador {pid}"

    filas = operaciones(eventos)

    salida = primas(eventos, indice)

    print("=" * 78)
    print("EL OCHO POR CIENTO")
    print("=" * 78)
    print()

    if not salida.get("available"):
        print(f"  NO SE PUDO: {salida.get('reason')}")
        return 1

    # ----------------------------------------------------
    # BLOQUE 0 — CONTRA QUE ESTA MEDIDO
    # ----------------------------------------------------
    print("-" * 78)
    print("BLOQUE 0 — CONTRA QUE PRECIO SE MIDE LA PRIMA")
    print("-" * 78)
    print()

    cambios = cuando_cambian_los_precios(indice)

    print(
        f"  Los precios cambian a las "
        f"{cambios['hora_dominante']:02d}h de Madrid: "
        f"{100 * cambios['parte_en_la_dominante']:.1f} % de "
        f"{cambios['cambios']:,} cambios observados."
    )
    print(
        f"  Asi que el PRECIO DEL DIA es la primera muestra de "
        f"ese dia desde esa hora."
    )
    print()

    marcas = [t for t, _ in indice.values() for t in (t[:1] + t[-1:])]

    todas = [t for serie, _ in indice.values() for t in serie]

    print(
        f"  El almacen cubre de {dia(min(todas))} a "
        f"{dia(max(todas))}, {len(indice)} jugadores."
    )

    fotos = cobertura_de_las_fotos(filas)

    print(
        f"  Las fotos cubren {fotos['dias_con_foto']} dias "
        f"sueltos."
    )
    print()
    print(
        f"  {'manager':<12}{'compras':>9}{'con FOTO':>10}"
        f"{'con PRECIO DEL DIA':>21}"
    )
    print()

    for quien, resumen in sorted(
        salida["managers"].items(),
        key=lambda kv: -(
            kv[1]["buys"]["n"] + kv[1]["buys_without_reference"]
        ),
    ):
        total = (
            resumen["buys"]["n"]
            + resumen["buys_without_reference"]
        )

        print(
            f"  {NOMBRES.get(quien, quien):<12}{total:>9}"
            f"{fotos['por_manager'].get(quien, 0):>10}"
            f"{resumen['buys']['n']:>21}"
        )

    print()

    cruce = contraste(indice)

    print(
        f"  CONTRASTE contra nuestro `market_price` anotado al "
        f"pujar:"
    )
    print(
        f"    anotadas EN VIVO      coinciden al euro "
        f"{cruce['vivo']['iguales']}, distintas "
        f"{cruce['vivo']['distintos']}"
    )
    print(
        f"    RECONSTRUIDAS luego   coinciden "
        f"{cruce['reconstruidas']['iguales']}, distintas "
        f"{cruce['reconstruidas']['distintos']}"
        f"   (no valen de contraste: su precio es del dia en que"
        f" se reconstruyeron)"
    )

    for caso in cruce["vivo"]["casos"]:
        print(
            f"      distinta: {caso['jugador'][:16]:<18}"
            f"{caso['cuando']}  anotado {caso['anotado']:>10,}  "
            f"del dia {caso['del_dia']:>10,}"
        )

    print()

    # ----------------------------------------------------
    # BLOQUE 1 — DE DONDE SALE NUESTRA PRIMA
    # ----------------------------------------------------
    nuestro = salida["managers"].get(NOSOTROS) or {}

    print("-" * 78)
    print("BLOQUE 1 — DE DONDE SALE NUESTRA PRIMA")
    print("-" * 78)
    print()
    print(f"  TODAS                 {pct(nuestro.get('buys'))}")
    print()

    for mes, bloque in (nuestro.get("by_month") or {}).items():
        print(
            f"  {mes}               {pct(bloque['all'])}"
            f"    sin rival {pct(bloque['undisputed'], 20)}"
            f"    con rival {pct(bloque['disputed'], 20)}"
        )

    print()

    via = vias_nuestras()

    porvia = {}

    for compra in nuestro.get("buys_detail") or []:
        porvia.setdefault(
            via.get(compra["player"], "SIN LIBRO (mecanismo viejo)"),
            [],
        ).append(compra)

    print("  POR VIA:")
    print()

    for etiqueta, compras in sorted(
        porvia.items(), key=lambda kv: -len(kv[1])
    ):
        ps = [c["premium"] for c in compras]

        import statistics as _st

        print(
            f"    {etiqueta:<30}"
            f"{_st.median(ps):>+8.2f}% (n={len(ps):>2})"
        )

    print()

    detalle = sorted(
        nuestro.get("buys_detail") or [],
        key=lambda c: -c["premium"],
    )

    if detalle:
        peor, mejor = detalle[0], detalle[-1]

        for etiqueta, c in (("PEOR ", peor), ("MEJOR", mejor)):
            print(
                f"  {etiqueta} {dia(c['date'])}  "
                f"{quien_es(c['player']):<16} pago "
                f"{c['amount']:>11,} contra {c['reference']:>11,}"
                f"  {c['premium']:+.2f} %  "
                f"({c['amount'] - c['reference']:+,} EUR)"
            )

        de_mas = sum(
            c["amount"] - c["reference"] for c in detalle
        )

        print()
        print(
            f"  EUROS pagados por encima del precio del dia, "
            f"en total (n={len(detalle)}): {de_mas:+,}"
        )

    sin = nuestro.get("buys_without_reference", 0)

    if sin:
        print(
            f"  Y {sin} compra(s) sin precio del dia: NO se les "
            f"estima ninguno."
        )

    print()

    if opciones.detalle:
        print("  UNA A UNA:")
        print()

        for c in sorted(
            nuestro.get("buys_detail") or [],
            key=lambda c: c["date"],
        ):
            print(
                f"    {dia(c['date'])}  "
                f"{quien_es(c['player'])[:18]:<20}"
                f"pago {c['amount']:>11,}  dia "
                f"{c['reference']:>11,}  {c['premium']:>+7.2f}%  "
                f"rivales {c['rivals']}  "
                f"{via.get(c['player'], '—')}"
            )

        print()

    # ----------------------------------------------------
    # BLOQUE 2 — COMO COMPRA POLLO
    # ----------------------------------------------------
    print("-" * 78)
    print("BLOQUE 2 — COMO COMPRA POLLO")
    print("-" * 78)
    print()
    print(
        f"  {'manager':<12}{'compras':>9}{'sin rival':>22}"
        f"{'con rival':>22}"
    )
    print()

    for quien in (NOSOTROS, POLLO, 14156489, 14176382):

        resumen = salida["managers"].get(quien)

        if not resumen:
            continue

        print(
            f"  {NOMBRES.get(quien, quien):<12}"
            f"{resumen['buys']['n']:>9}"
            f"{pct(resumen['undisputed'])}"
            f"{pct(resumen['disputed'])}"
        )

    print()
    print("  CUANTAS SUBASTAS PELEA CADA UNO, y cuantas gana:")
    print()

    # SOBRE LAS OPERACIONES DEDUPLICADAS, no sobre los eventos
    # crudos: el tablon reemite y una subasta repetida sumaria
    # sus perdedores dos veces.
    ganadas = {}
    perdidas = {}

    for fila in filas:

        if fila["type"] != "market":
            continue

        if fila["buyer"]:
            ganadas[fila["buyer"]] = ganadas.get(fila["buyer"], 0) + 1

        for quien in fila["losers"]:
            perdidas[quien] = perdidas.get(quien, 0) + 1

    print(
        f"  {'manager':<12}{'ganadas':>9}{'perdidas':>10}"
        f"{'peleadas':>10}{'gana':>8}"
    )
    print()

    for quien in (NOSOTROS, POLLO, 14156489, 14176382):

        g, p = ganadas.get(quien, 0), perdidas.get(quien, 0)

        if not (g + p):
            continue

        print(
            f"  {NOMBRES.get(quien, quien):<12}{g:>9}{p:>10}"
            f"{g + p:>10}{100 * g / (g + p):>7.0f}%"
        )

    print()
    print("  A QUE HORA COMPRA CADA UNO (Madrid):")
    print()

    for quien in (NOSOTROS, POLLO):

        horas = {}

        for fila in filas:

            if fila["buyer"] != quien:
                continue

            h = datetime.fromtimestamp(
                fila["date"], MADRID
            ).hour

            horas[h] = horas.get(h, 0) + 1

        print(
            f"    {NOMBRES.get(quien, quien):<12}"
            f"{dict(sorted(horas.items()))}"
        )

    print()

    # ----------------------------------------------------
    # BLOQUE 3 — LOS VIAJES CERRADOS
    # ----------------------------------------------------
    #
    #     CON LA MISMA DEFINICION QUE LOS DE LA LIGA, y por eso
    #     se importa el emparejador en vez de repetirlo: dos
    #     definiciones de "viaje" darian dos numeros y los dos
    #     parecerian correctos.
    from src.analysis.de_donde_salio_el_dinero import (  # noqa: PLC0415
        emparejar,
        operaciones as operaciones_del_libro,
    )

    import statistics as _st

    libro = emparejar(operaciones_del_libro(eventos))

    viajes = libro["viajes"]

    print("-" * 78)
    print("BLOQUE 3 — LOS VIAJES CERRADOS, Y QUIEN CORTA")
    print("-" * 78)
    print()
    print(
        f"  Viajes cerrados en la liga: "
        f"{sum(len(v) for v in viajes.values())}"
    )
    print()
    print(
        f"  {'manager':<12}{'viajes':>8}{'beneficio':>14}"
        f"{'euro/viaje':>13}{'dias':>8}"
    )
    print()

    for quien in sorted(
        NOMBRES, key=lambda q: -len(viajes.get(q) or [])
    ):
        v = viajes.get(quien) or []

        if not v:
            continue

        b = [x["beneficio"] for x in v]

        print(
            f"  {NOMBRES[quien]:<12}{len(v):>8}{sum(b):>+14,}"
            f"{_st.fmean(b):>+13,.0f}"
            f"{_st.fmean([x['dias'] for x in v]):>8.1f}"
        )

    print()
    print("  ¿QUIEN CORTA CUANDO VA PERDIENDO?")
    print()
    print(
        f"  {'manager':<12}{'viajes':>8}{'en perdida':>12}{'%':>6}"
        f"{'lo perdido':>14}{'dias si pierde':>16}"
        f"{'dias si gana':>14}"
    )
    print()

    for quien in sorted(
        NOMBRES, key=lambda q: -len(viajes.get(q) or [])
    ):
        v = viajes.get(quien) or []

        if not v:
            continue

        mal = [x for x in v if x["beneficio"] < 0]
        bien = [x for x in v if x["beneficio"] >= 0]

        print(
            f"  {NOMBRES[quien]:<12}{len(v):>8}{len(mal):>12}"
            f"{100 * len(mal) / len(v):>5.0f}%"
            f"{sum(x['beneficio'] for x in mal):>+14,}"
            + (
                f"{_st.fmean([x['dias'] for x in mal]):>16.1f}"
                if mal
                else f"{'—':>16}"
            )
            + (
                f"{_st.fmean([x['dias'] for x in bien]):>14.1f}"
                if bien
                else f"{'—':>14}"
            )
        )

    print()
    print("  NUESTROS VIAJES, UNO A UNO:")
    print()

    for x in sorted(
        viajes.get(NOSOTROS) or [],
        key=lambda x: -x["beneficio"],
    ):
        print(
            f"    {quien_es(x['player'])[:18]:<20}"
            f"{x['pagado']:>11,} -> {x['cobrado']:>11,}  "
            f"{x['beneficio']:>+11,}  {x['dias']:>5.1f} d"
        )

    print()

    # ----------------------------------------------------
    # DOCTRINA 54
    # ----------------------------------------------------
    print("-" * 78)
    print("LA RESTA, SOLO DONDE LAS DOS MITADES CUBREN LO MISMO")
    print("-" * 78)
    print()
    print(
        f"  La prima del Computer al recomprar, toda la liga: "
        f"{pct(salida['computer'], 0)}"
    )
    print()

    for quien in (NOSOTROS, POLLO):

        resumen = salida["managers"].get(quien)

        if not resumen:
            continue

        print(f"  {NOMBRES.get(quien, quien)}:")

        for mes in list(resumen.get("by_month") or {}) + [None]:

            veredicto = bajo_el_agua(resumen, mes)

            print(f"    {veredicto['reason']}")

        print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
