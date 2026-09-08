"""
Por quien pujaria Pepe en el proximo reset, y cuanto.

EL BLOQUE 4 DEL ENCARGO

    "No veo pujas para ganar algun jugador, ni en estrategia
     pone «espero a cinco minutos antes del reset»."

    Antes del reset tiene que verse por quien va a pujar, cuanto,
    por que ese importe, cuanto dinero compromete y cuantas
    fichas ocuparia si ganara todas.

DE DONDE SALEN LOS DATOS

    De `diagnostico/status.json`, que es lo que produccion
    publica de si misma. Ni una llamada a Biwenger.

NO PUJA

    Publica lo que HARIA. `enabled` sale False a proposito.

COMO SE USA

    python -m scripts.que_pujaria_en_el_reset
"""

from __future__ import annotations

import json

from pathlib import Path

from src.analysis.la_subasta import (
    IMPORTE_DE_CARTERA,
    comparar_los_dos_modos,
    elegir_la_cesta,
    para_la_pantalla,
    peor_caso,
    ventana_abierta,
)


ESTADO = (
    Path(__file__).parent.parent
    / "diagnostico"
    / "status.json"
)


# Cuatro por club: es la regla de la casa sobre concentracion
# por equipo, y aqui se comprueba sobre la cesta entera.
MAX_POR_CLUB = 4


def euros(valor) -> str:
    try:
        return f"{int(valor or 0):,}".replace(",", ".")
    except (TypeError, ValueError):
        return "?"


def main() -> None:

    estado = json.loads(ESTADO.read_text(encoding="utf-8"))

    tablero = estado.get("acquisition") or {}
    reloj = estado.get("market_clock") or {}
    plantilla = (estado.get("roster") or {}).get("players") or []
    bolsillos = estado.get("exposure") or {}

    filas = tablero.get("targets") or []

    print()
    print("=" * 74)
    print("QUE PUJARIA PEPE EN EL PROXIMO RESET")
    print("=" * 74)
    print()
    print(
        f"  Publicado por produccion: "
        f"{(estado.get('meta') or {}).get('generated_at')}"
    )

    ventana = ventana_abierta(
        reloj.get("seconds_to_reset")
    )

    print(f"  {ventana['reason']}")

    # LAS FICHAS LIBRES, CON LA DEFINICION DE LA CASA
    #
    #     Biwenger no publica el tope de plantilla, asi que
    #     `roster_expansion_shadow.count_free_slots` lo deduce:
    #     la plantilla MAS GRANDE de la liga menos la nuestra.
    #
    #     Queda escrito alli que eso es un SUELO y no el tope de
    #     Biwenger: si alguien mas tiene sitio, nosotros tambien.
    #     Se reutiliza esa definicion en vez de inventar otra.
    managers = (
        (estado.get("rival_intelligence") or {}).get("managers")
        or []
    )

    tamanos = [
        int(m.get("roster_count") or 0)
        for m in managers
        if isinstance(m, dict)
    ]

    nuestra = next(
        (
            int(m.get("roster_count") or 0)
            for m in managers
            if isinstance(m, dict) and m.get("is_us")
        ),
        len(plantilla),
    )

    mayor = max(tamanos) if tamanos else nuestra

    huecos = max(0, mayor - nuestra)

    print(
        f"  Plantilla: {nuestra} jugadores; la mayor de la liga "
        f"tiene {mayor} -> {huecos} fichas libres"
    )
    print(
        "  (es un SUELO, no el tope de Biwenger: la casa lo "
        "deduce asi desde el 25/08)"
    )

    caja = (bolsillos.get("cash_budget") or 0)

    presupuesto = bolsillos.get("available_budget") or 0

    print(f"  Caja libre: {euros(caja)} EUR")
    print(f"  Bolsillo:   {euros(presupuesto)} EUR")

    # ==========================================================
    # LOS CANDIDATOS
    # ==========================================================
    #
    #     Solo los que el tablero da por pujables. Una fila que
    #     no es BID no es un candidato: es un deseo.
    def _fila(f, ):
        return {
            "id": f.get("id"),
            "name": f.get("name"),
            "market_price": f.get("market_price"),
            "bid": f.get("bid"),
            "expected_value": f.get("expected_value"),
            "team_id": f.get("team_id"),
            "decision": f.get("decision"),
            "bid_reason": (f.get("bid_reasons") or [None])[0],
        }

    # MODO UN DISPARO: solo los que el tablero da por pujables.
    # Una fila que no es BID no es un candidato: es un deseo.
    candidatos = [
        _fila(f) for f in filas if f.get("decision") == "BID"
    ]

    # MODO CARTERA: entran todos los que se pueden comprar de
    # verdad. Pujar bajo por muchos solo tiene sentido si «los
    # muchos» existen, y lo que veta a un jugador para una puja
    # cara -que no compense al +8 %- deja de vetarlo al +0,25 %.
    #
    # Lo que NO entra: lo indisponible. Un lesionado no mejora
    # por pujar barato.
    VETADOS = {"NO_DISPONIBLE"}

    para_cartera = [
        _fila(f)
        for f in filas
        if f.get("decision") not in VETADOS
        and (f.get("market_price") or 0) > 0
    ]

    print()
    print(
        f"  Candidatos con decision PUJAR: {len(candidatos)} "
        f"de {len(filas)}"
    )
    print(
        f"  Candidatos para el modo cartera: "
        f"{len(para_cartera)} de {len(filas)} "
        f"(fuera los indisponibles)"
    )

    cesta = elegir_la_cesta(
        candidatos,
        presupuesto=presupuesto,
        fichas_libres=huecos,
        caja_libre=caja,
        max_por_club=MAX_POR_CLUB,
    )

    pantalla = para_la_pantalla(cesta, ventana)

    print()
    print("-" * 74)
    print("LA CESTA")
    print("-" * 74)
    print()
    print(f"  {cesta['reason']}")

    if cesta.get("tope"):
        print()
        print(f"  Tope de la ventana: {cesta['tope']['reason']}")

    if pantalla["bids"]:

        print()
        print(
            f"  {'JUGADOR':<22}{'PRECIO':>12}{'PUJA':>12}"
            f"{'GANA':>11}{'POR EURO':>10}"
        )
        print("  " + "-" * 67)

        for puja in pantalla["bids"]:
            print(
                f"  {str(puja['name'])[:22]:<22}"
                f"{euros(puja['price']):>12}"
                f"{euros(puja['bid']):>12}"
                f"{euros(puja['expected_value']):>11}"
                f"{puja['yield_per_euro']:>9} %"
            )

        print()
        print(
            f"  COMPROMETE {euros(pantalla['committed'])} EUR "
            f"y {pantalla['slots_used']} de "
            f"{pantalla['slots_free']} fichas."
        )
        print(
            f"  Si las ganara TODAS: "
            f"{euros(pantalla['expected_gain'])} EUR de "
            f"ganancia esperada."
        )

        print()
        print("-" * 74)
        print("EL PEOR CASO: QUE SE GANEN TODAS")
        print("-" * 74)
        print()
        print(f"  {peor_caso(cesta, plantilla)['reason']}")

    # ==========================================================
    # LOS DOS MODOS, UNO AL LADO DEL OTRO
    # ==========================================================

    reventa = (
        (
            (tablero.get("computer_premium") or {}).get(
                "median_percent"
            )
            or 0
        )
        / 100.0
    )

    dos = comparar_los_dos_modos(
        para_cartera,
        prima_de_reventa=reventa,
        presupuesto=presupuesto,
        fichas_libres=huecos,
        caja_libre=caja,
        max_por_club=MAX_POR_CLUB,
    )

    print()
    print("=" * 74)
    print("LOS DOS MODOS, UNO AL LADO DEL OTRO")
    print("=" * 74)
    print()
    print(
        f"  El Computer recompra a +{100 * reventa:.1f} %. "
        f"El modo cartera ofrece precio "
        f"+{100 * IMPORTE_DE_CARTERA:.2f} %."
    )

    for etiqueta, clave in (
        ("HOY (un disparo)", "un_disparo"),
        ("MODO CARTERA", "cartera"),
    ):

        cesta_modo = dos.get(clave) or {}

        elegidos = cesta_modo.get("elegidos") or []

        print()
        print(f"  {etiqueta}")
        print("  " + "-" * 70)
        print(f"    {cesta_modo.get('reason')}")

        if not elegidos:
            continue

        print()
        print(
            f"    {'JUGADOR':<20}{'PRECIO':>12}{'PUJA':>12}"
            f"{'GANA':>11}{'POR EURO':>10}"
        )

        for c in elegidos:
            print(
                f"    {str(c.get('name'))[:20]:<20}"
                f"{euros(c.get('market_price')):>12}"
                f"{euros(c.get('bid')):>12}"
                f"{euros(c.get('expected_value')):>11}"
                f"{c.get('yield_per_euro'):>9} %"
            )

        peor = peor_caso(cesta_modo, plantilla)

        print()
        print(f"    Peor caso: {peor.get('reason')}")

    print()
    print(
        f"  ENCENDIDO: {pantalla['enabled']}  "
        f"(observador: {pantalla['observer_only']})"
    )
    print("  No se ha pujado nada. Ni una llamada a Biwenger.")


if __name__ == "__main__":
    main()
