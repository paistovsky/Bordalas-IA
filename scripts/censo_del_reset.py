"""
Una linea al dia: que trae el reset, y si la puja sobrevivio.

LAS DOS PREGUNTAS QUE CONTESTA, CON EL TIEMPO

    1. ¿Hace falta vender a ciegas la noche antes de un reset?

       Si el Computer publica todas las mananas una tanda que
       tapa el agujero con gente que no juega, la respuesta es
       que no hace falta nunca. Hoy llevamos DOS observaciones,
       que no son un patron.

    2. ¿Sigue viva una puja por debajo del precio nuevo?

       El dueno pujo 11.800.000 por Aubameyang y al reset
       siguiente el jugador pasa a costar 12.170.000. Nadie de
       esta casa lo ha medido. Decide si se puede pujar la tarde
       anterior o hay que esperar al ultimo momento.

DE DONDE SALEN LOS DATOS

    De `diagnostico/status.json`, que es lo que produccion
    publica de si misma. Ni una llamada a Biwenger.

COMO SE USA

    python -m scripts.censo_del_reset

    Y para apuntar una puja del dueno que el tablon no publica:

    python -m scripts.censo_del_reset --jugador Aubameyang \\
        --puja 11800000
"""

from __future__ import annotations

import argparse
import json

from pathlib import Path

from src.intelligence.bitacora_del_saldo import (
    apuntar_puja_bajo_precio,
    censar_el_reset,
    historia_bajo_precio,
    historia_del_censo,
)


ESTADO = (
    Path(__file__).parent.parent / "diagnostico" / "status.json"
)


def euros(valor) -> str:
    try:
        return f"{int(valor or 0):,}".replace(",", ".")
    except (TypeError, ValueError):
        return "?"


def main() -> None:

    parser = argparse.ArgumentParser()

    parser.add_argument("--jugador", default=None)
    parser.add_argument("--puja", type=int, default=0)

    args = parser.parse_args()

    estado = json.loads(ESTADO.read_text(encoding="utf-8"))

    meta = estado.get("meta") or {}
    reloj = estado.get("market_clock") or {}

    titulares = [
        j.get("name")
        for j in ((estado.get("roster") or {}).get("players") or [])
        if isinstance(j, dict) and j.get("is_starter")
    ]

    print()
    print("=" * 70)
    print("CENSO DEL RESET")
    print("=" * 70)
    print(f"  Foto de produccion: {meta.get('generated_at')}")
    print(f"  {reloj.get('reason')}")
    print()

    # ------------------------------------------------------
    # 1. LA TANDA NUEVA
    # ------------------------------------------------------

    censo = censar_el_reset(
        estado.get("offers"),
        reloj.get("hours_to_reset"),
        starters=titulares,
    )

    print("  LA TANDA NUEVA (la de caducidad mas lejana)")
    print(f"    {censo.get('reason')}")

    for fila in (censo.get("players") or []):
        print(
            f"      {str(fila['name'])[:20]:<21}"
            f"{euros(fila['amount']):>12}"
            f"   {'TITULAR' if fila['starter'] else 'banquillo'}"
        )

    print()
    print(f"    {historia_del_censo().get('reason')}")

    # ------------------------------------------------------
    # 2. LA PUJA POR DEBAJO DEL PRECIO
    # ------------------------------------------------------

    print()
    print("  LA PUJA POR DEBAJO DEL PRECIO NUEVO")

    objetivos = (estado.get("acquisition") or {}).get(
        "targets"
    ) or []

    # Si el tablon ya publica una puja viva, se apunta sola. Si
    # no -que es lo que paso el 10/09- hace falta decirle cual.
    vivas = [
        f for f in objetivos if f.get("has_live_bid")
    ]

    candidatos = [
        (f.get("name"), f.get("live_bid"), f.get("market_price"))
        for f in vivas
    ]

    if args.jugador:
        fila = next(
            (
                f for f in objetivos
                if str(f.get("name")) == args.jugador
            ),
            None,
        )

        candidatos.append(
            (
                args.jugador,
                args.puja,
                (fila or {}).get("market_price"),
            )
        )

    if not candidatos:
        print(
            "    No hay ninguna puja que mirar. El tablon no "
            "publica ninguna y no se ha pasado ninguna a mano."
        )

    for nombre, puja, precio in candidatos:

        apuntada = apuntar_puja_bajo_precio(
            player_name=nombre,
            bid_amount=puja,
            price_now=precio,
            note=f"Foto {meta.get('generated_at')}",
        )

        print(
            f"    {nombre}: puja {euros(puja)} · precio hoy "
            f"{euros(precio)} · "
            + (
                f"POR DEBAJO en {euros(apuntada['gap'])}"
                if apuntada["below_price"]
                else "no esta por debajo"
            )
        )

    print(f"    {historia_bajo_precio().get('reason')}")
    print()


if __name__ == "__main__":
    main()
