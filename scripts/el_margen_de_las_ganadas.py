"""
El margen de las pujas ganadas: ¿competitivos o generosos?

LA PREGUNTA (23/09/2026)

    57 pujas, 51 ganadas: 89,5 %. De las ganadas, cuanto pujamos por
    encima de la SEGUNDA puja cuando se sepa, o por encima del
    PRECIO cuando no.

LO QUE SE PUEDE Y LO QUE NO

    La segunda puja no la publica nadie: el tablon de la liga dice
    quien gano y por cuanto, no quien quedo segundo. Asi que para
    las ganadas se mide contra el precio de mercado del momento de
    pujar.

    Y SOLO las que se apuntaron AL PUJAR. Las reconstruidas desde la
    plantilla (`recorded_by: PLANTILLA` con `placed_at_is_resolution`)
    llevan el precio de cuando se reconstruyeron, no el de la puja:
    compararlas diria cualquier cosa. Se cuentan aparte, con nombre.

Solo lee `data/trading/bid_outcome_ledger.json`. No escribe nada.

    python scripts/el_margen_de_las_ganadas.py
"""

from __future__ import annotations

import json
import statistics

from collections import defaultdict
from pathlib import Path


RAIZ = Path(__file__).resolve().parents[1]

LIBRO = RAIZ / "data" / "trading" / "bid_outcome_ledger.json"


def _euros(valor) -> str:
    return f"{int(round(valor)):,}".replace(",", ".")


def main() -> None:

    pujas = list(
        json.loads(LIBRO.read_text(encoding="utf-8"))["bids"].values()
    )

    ganadas = [p for p in pujas if p.get("outcome") == "WON"]
    perdidas = [p for p in pujas if p.get("outcome") == "LOST"]

    comparables = [
        p for p in ganadas
        if p.get("market_price")
        and not p.get("placed_at_is_resolution")
    ]

    fuera = [p for p in ganadas if p not in comparables]

    print()
    print("EL MARGEN DE LAS GANADAS")
    print("=" * 78)
    print(
        f"  pujas {len(pujas)}   ganadas {len(ganadas)}   perdidas "
        f"{len(perdidas)}   ({100 * len(ganadas) / len(pujas):.1f} %)"
    )
    print(
        f"  desde {min(p['placed_at'] for p in pujas)[:10]} hasta "
        f"{max(p['placed_at'] for p in pujas)[:10]}"
    )
    print()
    print(
        f"  contra la SEGUNDA puja: 0 de {len(ganadas)}. No se publica "
        f"en ninguna parte."
    )
    print(
        f"  contra el PRECIO: {len(comparables)} de {len(ganadas)} "
        f"comparables. Las otras {len(fuera)} no traen el precio "
        f"del momento de pujar (reconstruidas o sin precio):"
    )
    print("      " + ", ".join(p["player_name"] for p in fuera))
    print()

    por_via = defaultdict(list)

    for p in comparables:
        por_via[p.get("target_source") or "?"].append(p)

    por_via["TODAS"] = comparables

    for via, filas in por_via.items():
        euros = [p["amount"] - p["market_price"] for p in filas]
        pct = [
            100.0 * (p["amount"] - p["market_price"]) / p["market_price"]
            for p in filas
        ]
        print(
            f"  {via:<18} n={len(filas):>2}   por encima del precio: "
            f"mediana {_euros(statistics.median(euros))} EUR "
            f"({statistics.median(pct):.2f} %), media "
            f"{statistics.mean(pct):.2f} %, max {max(pct):.2f} %, "
            f"total {_euros(sum(euros))} EUR"
        )

    print()

    con_margen = [p for p in perdidas if p.get("margin") is not None]

    print(
        f"  LAS PERDIDAS, que si dicen la puja ganadora: "
        f"{len(con_margen)} de {len(perdidas)} con margen"
    )

    for p in con_margen:
        print(
            f"      {p['player_name']:<12} pujamos {_euros(p['amount'])}"
            f"  gano {_euros(p['winning_amount'])}  "
            f"(nos quedamos a {_euros(p['margin'])} EUR)"
        )


if __name__ == "__main__":
    main()
