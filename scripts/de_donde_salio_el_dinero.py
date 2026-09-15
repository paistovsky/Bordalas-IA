"""
De donde salio el dinero, impreso.

QUE HACE

    Lee del disco lo que ya esta medido -eventos, censo, precios-
    y llama a `src.analysis.de_donde_salio_el_dinero.descomponer`.
    Aqui SOLO hay lectura y formato: la cuenta esta en el modulo,
    que no lee nada, para que la guardia pueda probarla con
    fixtures.

    No escribe nada contra Biwenger. No escribe nada en `data/`.

DE DONDE SALE CADA COSA

    los eventos   data/rival_intelligence/board_events.json
    el censo      data/rival_intelligence/profiles_cache.json
    los precios   el catalogo de la foto mas reciente
    la caja       src.analysis.caja_de_la_liga

    Las tres fuentes tienen fechas DISTINTAS y se imprimen las
    tres. Un patrimonio que mezcla una plantilla de anoche con
    precios de anteayer no es falso, pero tampoco es "hoy", y
    quien lo lea tiene derecho a saberlo.

EL RELOJ

    `--ahora` toma la hora a la que se recogio el censo, no la
    del sistema: los dias que lleva un jugador en plantilla se
    cuentan hasta la foto, no hasta que a uno le dio por
    ejecutar esto.

COMO SE USA

    python -m scripts.de_donde_salio_el_dinero
    python -m scripts.de_donde_salio_el_dinero --detalle Pollo17
"""

from __future__ import annotations

import argparse
import glob
import json

from datetime import datetime, timezone
from pathlib import Path

from src.analysis.de_donde_salio_el_dinero import descomponer


RAIZ = Path(__file__).parent.parent

EVENTOS = RAIZ / "data" / "rival_intelligence" / "board_events.json"

CENSO = RAIZ / "data" / "rival_intelligence" / "profiles_cache.json"


def euros(valor) -> str:
    """Con su signo y sus puntos. Nunca abreviado."""

    if valor is None:
        return "SIN DATO"

    return f"{int(round(valor)):+,}".replace(",", ".")


def llanos(valor) -> str:
    if valor is None:
        return "SIN DATO"

    return f"{int(round(valor)):,}".replace(",", ".")


def cuando(epoch) -> str:
    if not epoch:
        return "SIN FECHA"

    return datetime.fromtimestamp(
        int(epoch), timezone.utc
    ).strftime("%Y-%m-%d %H:%M UTC")


def _leer(ruta: Path):
    return json.loads(ruta.read_text(encoding="utf-8"))


def la_foto_mas_reciente() -> Path | None:
    fotos = sorted(glob.glob(str(RAIZ / "data" / "snapshot_*.json")))

    return Path(fotos[-1]) if fotos else None


def main() -> int:

    parser = argparse.ArgumentParser()

    parser.add_argument("--detalle", default=None)

    opciones = parser.parse_args()

    # ----------------------------------------------------
    # LAS TRES FUENTES
    # ----------------------------------------------------
    if not EVENTOS.exists() or not CENSO.exists():
        print("FALTA UNA FUENTE:")
        print(f"  eventos {EVENTOS}: {EVENTOS.exists()}")
        print(f"  censo   {CENSO}: {CENSO.exists()}")
        return 1

    eventos = _leer(EVENTOS)

    censo_crudo = _leer(CENSO)

    foto = la_foto_mas_reciente()

    if foto is None:
        print("No hay ninguna foto en data/: sin precios de hoy.")
        return 1

    instantanea = _leer(foto)

    catalogo = (
        (instantanea.get("catalog") or {}).get("data") or {}
    ).get("players") or {}

    precios = {
        int(k): (v or {}).get("price")
        for k, v in catalogo.items()
        if (v or {}).get("price") is not None
    }

    recogido = int(censo_crudo.get("collected_at") or 0)

    salida = descomponer(
        eventos=eventos,
        censo=censo_crudo.get("profiles") or {},
        precios=precios,
        ahora=recogido,
    )

    # ----------------------------------------------------
    # LA CABECERA: QUE SE HA LEIDO Y DE CUANDO
    # ----------------------------------------------------
    print("=" * 78)
    print("DE DONDE SALIO EL DINERO")
    print("=" * 78)
    print()
    print(f"  eventos   {EVENTOS.name}: {len(eventos)} "
          f"({cuando(max((e.get('date') or 0) for e in eventos))} "
          f"el ultimo)")
    print(f"  censo     {CENSO.name}: {cuando(recogido)}")
    print(f"  precios   {foto.name}: {len(precios)} jugadores")
    print()

    if not salida.get("available"):
        print(f"  NO SE PUDO: {salida.get('reason')}")
        return 1

    print(f"  {salida['reason']}")

    caja = salida.get("cash") or {}

    print(
        f"  jornadas pagadas {caja.get('rounds_paid')} de "
        f"{caja.get('rounds_seen')}; sin pagar "
        f"{', '.join(caja.get('ignored_rounds') or []) or 'ninguna'}."
    )
    print()

    # ----------------------------------------------------
    # LA TABLA DE LOS OCHO
    # ----------------------------------------------------
    gente = sorted(
        salida["managers"].values(),
        key=lambda m: -m["net_worth"],
    )

    print("-" * 78)
    print("LOS CUATRO TROZOS")
    print("-" * 78)
    print()
    print(
        f"  {'manager':<20}{'premios':>12}{'viajes':>13}"
        f"{'subida':>13}{'4o monton':>13}"
    )
    print()

    for m in gente:
        print(
            f"  {m['name'][:18]:<20}"
            f"{llanos(m['prizes']):>12}"
            f"{euros(m['trading']):>13}"
            f"{euros(m['holding']):>13}"
            f"{llanos(m['endowment']):>13}"
        )

    print()
    print(
        f"  {'manager':<20}{'+23.300.000':>14}{'patrimonio':>14}"
        f"{'cuadra':>10}"
    )
    print()

    for m in gente:
        print(
            f"  {m['name'][:18]:<20}"
            f"{llanos(m['reconstructed']):>14}"
            f"{llanos(m['net_worth']):>14}"
            f"{('SI' if m['balances'] else euros(m['difference'])):>10}"
        )

    print()
    print(f"  {salida['cuadre']['reason']}")
    print()

    # ----------------------------------------------------
    # EL CUARTO MONTON
    # ----------------------------------------------------
    print("-" * 78)
    print("EL CUARTO MONTON: SIN COSTE CONOCIDO")
    print("-" * 78)
    print()
    print(
        f"  {'manager':<20}{'en plantilla':>14}{'valen hoy':>14}"
        f"{'vendidos':>10}{'cobro':>14}"
    )
    print()

    en_plantilla = valen = vendidos = cobrado = 0

    for m in gente:
        u = m["unknown_cost"]
        en_plantilla += u["in_roster_n"]
        valen += u["in_roster_value"]
        vendidos += u["sold_n"]
        cobrado += u["sold_proceeds"]

        print(
            f"  {m['name'][:18]:<20}{u['in_roster_n']:>14}"
            f"{llanos(u['in_roster_value']):>14}"
            f"{u['sold_n']:>10}{llanos(u['sold_proceeds']):>14}"
        )

    print()
    print(
        f"  {'TOTAL':<20}{en_plantilla:>14}{llanos(valen):>14}"
        f"{vendidos:>10}{llanos(cobrado):>14}"
    )
    print()

    sin_precio = [
        (m["name"], m["players_without_price"])
        for m in gente
        if m["players_without_price"]
    ]

    if sin_precio:
        print("  JUGADORES SIN PRECIO EN EL CATALOGO (no valorados):")
        for nombre, ids in sin_precio:
            print(f"    {nombre}: {ids}")
    else:
        print("  Todos los jugadores de las ocho plantillas tienen "
              "precio en el catalogo.")
    print()

    # ----------------------------------------------------
    # COMERCIANTE O COLECCIONISTA
    # ----------------------------------------------------
    print("-" * 78)
    print("COMERCIANTE O COLECCIONISTA")
    print("-" * 78)
    print()
    print(
        f"  {'manager':<20}{'compras':>9}{'ventas':>8}{'viajes':>8}"
        f"{'dias med':>10}{'gana':>9}{'euro/viaje':>13}"
    )
    print()

    for m in sorted(
        salida["managers"].values(), key=lambda m: -m["trips"]["n"]
    ):
        t = m["trips"]
        dias = (
            f"{t['mean_days']:.1f}"
            if t["mean_days"] is not None
            else "-"
        )
        acierto = f"{t['winners']}/{t['n']}"

        print(
            f"  {m['name'][:18]:<20}{m['buys']:>9}{m['sells']:>8}"
            f"{t['n']:>8}{dias:>10}{acierto:>9}"
            f"{euros(t['mean_profit']):>13}"
        )

    print()
    print(
        f"  {'manager':<20}{'quietos':>9}{'dias med':>10}{'suben':>9}"
        f"{'euro/jugador':>15}"
    )
    print()

    for m in sorted(
        salida["managers"].values(), key=lambda m: -m["held"]["gain"]
    ):
        h = m["held"]
        dias = (
            f"{h['mean_days']:.1f}"
            if h["mean_days"] is not None
            else "-"
        )
        acierto = f"{h['winners']}/{h['n']}"

        print(
            f"  {m['name'][:18]:<20}{h['n']:>9}{dias:>10}"
            f"{acierto:>9}{euros(h['mean_gain']):>15}"
        )

    print()

    # ----------------------------------------------------
    # EL VIAJE MEDIO DE LA LIGA
    # ----------------------------------------------------
    liga = salida["liga"]

    v, h = liga["trip"], liga["held"]

    print("-" * 78)
    print("CUANTO DA UN VIAJE, Y CUANTO DA TENER QUIETO")
    print("-" * 78)
    print()
    print(
        f"  COMPRAR Y VENDER   n={v['n']:<4} "
        f"medio {euros(v['mean_profit'])}   "
        f"mediana {euros(v['median_profit'])}   "
        f"{v['winners']}/{v['n']} en verde"
    )
    print(
        f"                     dura {v['mean_days']:.1f} dias de "
        f"media ({v['median_days']:.1f} de mediana)"
    )
    print()
    print(
        f"  TENER QUIETO       n={h['n']:<4} "
        f"medio {euros(h['mean_gain'])}   "
        f"mediana {euros(h['median_gain'])}   "
        f"{h['winners']}/{h['n']} en verde"
    )
    print(
        f"                     lleva {h['mean_days']:.1f} dias de "
        f"media ({h['median_days']:.1f} de mediana)"
    )
    print()

    if v["mean_days"] and h["mean_days"]:
        print(
            f"  POR DIA DE CAPITAL "
            f"  viaje {euros(v['mean_profit'] / v['mean_days'])}"
            f"/dia   quieto "
            f"{euros(h['mean_gain'] / h['mean_days'])}/dia"
        )
        print()

    # ----------------------------------------------------
    # EL DETALLE DE UNO
    # ----------------------------------------------------
    if opciones.detalle:

        elegido = next(
            (
                m
                for m in salida["managers"].values()
                if opciones.detalle.lower() in m["name"].lower()
            ),
            None,
        )

        if elegido is None:
            print(f"  No hay ningun manager '{opciones.detalle}'.")
            return 1

        nombres = {
            int(k): (v or {}).get("name")
            for k, v in catalogo.items()
        }

        print("-" * 78)
        print(f"DETALLE: {elegido['name']}")
        print("-" * 78)
        print()
        print("  VIAJES CERRADOS")
        print()

        for t in sorted(
            elegido["trips"]["detail"],
            key=lambda t: -t["beneficio"],
        ):
            print(
                f"    {nombres.get(t['player'], t['player'])[:22]:<24}"
                f"{llanos(t['pagado']):>12} -> "
                f"{llanos(t['cobrado']):>12}  "
                f"{euros(t['beneficio']):>12}  "
                f"{t['dias']:>5.1f} d"
            )

        print()
        print("  EN PLANTILLA, CON COSTE CONOCIDO")
        print()

        for q in sorted(
            elegido["held"]["detail"], key=lambda q: -q["subida"]
        ):
            print(
                f"    {nombres.get(q['player'], q['player'])[:22]:<24}"
                f"{llanos(q['pagado']):>12} -> "
                f"{llanos(q['vale_hoy']):>12}  "
                f"{euros(q['subida']):>12}  "
                f"{(q['dias'] or 0):>5.1f} d"
            )

        print()
        print("  EN PLANTILLA, SIN COSTE CONOCIDO (cuarto monton)")
        print()

        for c in elegido["unknown_cost"]["detail"]:
            print(
                f"    {nombres.get(c['player'], c['player'])[:22]:<24}"
                f"{'SIN COSTE':>12}    "
                f"{llanos(c['valor']):>12}"
            )

        print()

    return 0 if salida["cuadre"]["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
