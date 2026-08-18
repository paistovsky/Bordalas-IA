"""
Que ofertas cobraria Pepe ahora mismo, y por que las demas no.

POR QUE EXISTE

    El 18/08/2026, despues de conectar el gatillo de cobro, la
    pantalla de MERCADO seguia enseñando trece ofertas y las
    trece decian "Conservar buena oferta". Cinco de ellas por
    encima del 3 % de prima.

    Y no habia forma de saber si eso era la respuesta del motor
    que decide o la de otro.

    Lo era de otro. La tabla OFERTAS RECIBIDAS se pinta desde
    `offer_reroll`, el motor viejo, que solo sabe decir si merece
    la pena pedir otra oferta. Quien decide si se cobra es Offer
    Decision Engine V2, y su veredicto no aparecia en ninguna
    pantalla.

    Es el mismo fallo de siempre en este proyecto: el dato
    existe, se calcula bien y nadie lo enseña. Aqui ademas duele
    doble, porque el sitio donde no se enseñaba es justo donde
    se mira para saber si hay que arreglar algo.

QUE HACE

    Recalcula la decision del ciclo desde el ultimo snapshot
    guardado -lo mismo que hace el dashboard- y enseña, oferta a
    oferta, lo que dice el motor que manda:

        - que decidio y por que
        - cuanto paga y cuanta prima deja
        - cuanto vale la venta en puntuacion
        - si esta protegido o reservado
        - cual se cobraria EN ESTE CICLO y cuales esperan turno

QUE NO HACE

    No escribe nada y no toca Biwenger: lee el ultimo snapshot
    del disco y recalcula.

    Ojo, red si usa. Recalcular el ciclo refresca el calendario
    de LaLiga por HTTP, igual que hace el dashboard. Sin red se
    queda esperando ahi.

USO

    python scripts/que_ofertas_cobro.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.analysis.decision_orchestrator import (  # noqa: E402
    build_global_decision,
)

from src.analysis.market_analyzer import (  # noqa: E402
    get_latest_snapshot,
    load_snapshot,
)


ORDEN = [
    "ACCEPT_FOR_SOLVENCY",
    "ACCEPT_NOW",
    "REROLL_CANDIDATE",
    "HOLD_OFFER",
    "KEEP_GOOD_OFFER",
    "HOLD_SOLVENCY_RESERVED",
    "NEVER_SELL",
]


def euros(valor) -> str:
    try:
        return f"{int(valor or 0):,}".replace(",", ".") + " EUR"
    except (TypeError, ValueError):
        return "? EUR"


def main() -> None:

    snapshot = load_snapshot(get_latest_snapshot())

    resultado = build_global_decision(snapshot)

    candidato = next(
        (
            item
            for item in (resultado.get("candidates") or [])
            if item.get("type") == "OFFER_DECISION_INTELLIGENCE"
        ),
        None,
    )

    if candidato is None:
        print(
            "No hay bloque de ofertas en este ciclo: o no hay "
            "ofertas sobre la mesa o las operaciones estan "
            "bloqueadas por fase temporal."
        )
        return

    datos = candidato.get("data") or {}

    decisiones = (
        (datos.get("offer_decisions") or {}).get("decisions")
        or []
    )

    print()
    print("=" * 70)
    print(f"OFERTAS SOBRE LA MESA: {len(decisiones)}")
    print("=" * 70)
    print()

    def clave(item):
        decision = item.get("decision")
        return (
            ORDEN.index(decision)
            if decision in ORDEN
            else len(ORDEN)
        )

    for item in sorted(decisiones, key=clave):

        prima = item.get("premium_percent")
        venta = item.get("sale_score")

        print(
            f"  {str(item.get('decision') or '?'):<22} "
            f"{str(item.get('player_name') or '?'):<22} "
            f"{euros(item.get('amount')):>16}  "
            f"prima {float(prima or 0):+5.1f} %  "
            f"venta {float(venta or 0):3.0f}/100"
        )

        proteccion = item.get("protection")

        if proteccion:
            print(f"  {'':<22} proteccion: {proteccion}")

        for motivo in (item.get("reasons") or [])[:2]:
            print(f"  {'':<22} {motivo}")

        print()

    cola = datos.get("queued_to_collect") or []
    ahora = datos.get("offer")

    print("=" * 70)

    if ahora:
        print(
            f"SE COBRA AHORA: {ahora.get('player_name')} por "
            f"{euros(ahora.get('amount'))}"
        )
        print(f"Accion emitida: {candidato.get('action')}")
        print(f"Ejecutable:     {candidato.get('executable')}")

        if len(cola) > 1:
            print()
            print(f"Esperan turno ({len(cola) - 1}):")

            for item in cola[1:]:
                print(
                    f"  - {item.get('player_name')} "
                    f"({float(item.get('premium_percent') or 0):+.1f} %)"
                )

    else:
        print("NO SE COBRA NADA EN ESTE CICLO.")
        print(f"Accion emitida: {candidato.get('action')}")
        print()
        print(
            "Si arriba hay alguna con prima buena, mira su "
            "puntuacion de venta: cobrar exige las dos cosas."
        )

    print("=" * 70)
    print()


if __name__ == "__main__":
    main()
