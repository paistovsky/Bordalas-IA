"""
La moneda del que se queda, corrida contra las fotos del tablero.

QUE HACE

    Para cada candidato del mercado del Computer de cada foto, la
    decision de hoy y la que saldria con `BORDALAS_LA_MONEDA_DE_LA_LIGA`
    puesto. Y antes de nada, que la reconstruccion SIN la moneda da
    la misma decision que publico la foto: si no, lo de despues no
    vale.

COMO, SIN VOLVER A VALORAR

    La moneda solo cambia la tarifa del punto dentro de
    `xi_upgrade_value`, que entra multiplicando:

        valor = int(justo x (1 - margen) x confianza) + recuperado

    Asi que el valor con la moneda sale de reescalar el publicado
    -(valor - recuperado) x 30.000 / tarifa + recuperado-, con el
    recuperado despejado del texto que publica la fila. Es la misma
    cuenta que `la_lista_de_la_noche`, y la guarda de que es lineal
    es `test_la_sombra_de_la_moneda_no_escribe`.

    Y DESPUES SE VUELVE A CLASIFICAR. Con la moneda, una via de
    plantilla puede pasar a superar el precio, y entonces
    `classify_operation` cambia la operacion de comerciar a fichar:
    otro bolsillo y otro liston. Por eso se llama a las funciones
    de produccion -`classify_operation`, `budget_for_intent`,
    `optimal_bid`- y no a una copia.

EL MODELO DE PUJA

    `build_bid_model` sobre `data/rival_intelligence/rival_intelligence.json`
    y el historico de precios, como el tablero. Es el del ultimo
    fichero que haya en disco, no el de cada foto.

QUE NO HACE

    No escribe contra Biwenger, no sale a la red, no enciende el
    interruptor y NO ESCRIBE NI UNA LINEA DE NINGUN LIBRO.

USO

    python scripts/la_moneda_contra_las_fotos.py [foto.json ...] > salida.txt 2>&1
"""

from __future__ import annotations

import json
import os
import re
import sys


sys.path.insert(0, os.getcwd())

os.environ.pop("BORDALAS_LA_MONEDA_DE_LA_LIGA", None)
os.environ.pop("BORDALAS_TOPE_DEL_ONCE", None)

from src.analysis.acquisition_board import build_historical_price_lookup  # noqa: E402
from src.analysis.acquisition_budget import budget_for_intent             # noqa: E402
from src.analysis.caja_de_la_liga import EUROS_POR_PUNTO                  # noqa: E402
from src.analysis.deployment import SIGNING_ROUTES, classify_operation    # noqa: E402
from src.analysis.rival_bid_model import build_bid_model, optimal_bid     # noqa: E402


FOTOS = (
    "dashboard/data/status.json",
    "data/fotos/2026-09-18.json",
    # La del 23/09 la pisa cada `foto_para_claude.ps1`: se guardo
    # aparte el 25/09 para que este informe y el del censo se puedan
    # repetir.
    "diagnostico/status-2026-09-23.json",
    "diagnostico/status.json",
)

RIVALES = "data/rival_intelligence/rival_intelligence.json"

# Lo que publica `xi_upgrade_value` en su motivo.
TEXTO = re.compile(
    r"A precio de mercado \(([\d.]+) EUR/punto\) valen ([\d.]+) EUR; "
    r"con un (\d+) % de margen exigido y confianza (\d+(?:\.\d+)?)"
)


def euros(texto) -> int:
    return int(str(texto).replace(".", ""))


def tarifa_de(foto) -> int | None:
    for f in foto["acquisition"]["targets"]:
        for texto in (f.get("reason"), f.get("xi_reason")):
            m = TEXTO.search(str(texto or ""))
            if m:
                return euros(m.group(1))
    return None


def reescala(valor: int, factor: float, texto) -> int:
    if valor <= 0 or factor == 1:
        return valor
    recuperado = 0
    m = TEXTO.search(str(texto or ""))
    if m:
        justo = euros(m.group(2))
        margen = int(m.group(3)) / 100
        confianza = float(m.group(4))
        recuperado = valor - int(justo * (1 - margen) * confianza)
        if not 0 <= recuperado <= valor:
            recuperado = 0
    return int((valor - recuperado) * factor) + recuperado


def decide(fila, foto, factor, modelo):
    """`(decision, clase)` para este candidato con este factor de moneda."""

    if fila.get("seller_id") is not None or fila.get("rival_market"):
        return "RIVAL", {}

    if str(fila.get("status") or "ok").lower() not in ("ok", "unknown"):
        return "NO_DISPONIBLE", {}

    despliegue = fila.get("deployment") or {}
    sombra = fila.get("confidence_shadow") or {}
    precio = int(fila.get("market_price") or 0)

    xi = reescala(int(sombra.get("xi_value") or 0), factor, fila.get("xi_reason"))
    relleno = reescala(
        int(despliegue.get("roster_fill_value") or 0),
        factor,
        fila.get("reason") if despliegue.get("route") == "ROSTER_FILL" else None,
    )

    # La mejor via de comerciar, si la hay: la moneda no la toca.
    comercio = None
    for ruta, valor in (
        (despliegue.get("value_route"), despliegue.get("value")),
        (despliegue.get("route"), fila.get("our_value")),
    ):
        if ruta and ruta not in SIGNING_ROUTES:
            comercio = {"value": int(valor or 0), "route": ruta}
            break

    clase = classify_operation(
        {"value": xi, "route": "XI_UPGRADE"},
        {"value": relleno, "route": "ROSTER_FILL"},
        comercio, None, None, price=precio,
    )
    clase["fichaje"] = max(xi, relleno)

    valor = int(clase.get("decision_value") or 0)
    if valor <= 0:
        return "SIN_VALOR", clase

    bolsillos = foto["acquisition"].get("budgets") or {}
    bolsillo = budget_for_intent(
        clase.get("intent"), bolsillos.get("speculation"), bolsillos.get("acquisition")
    )
    plan = optimal_bid(
        price=precio, value=valor, model=modelo, available_budget=bolsillo,
        intent=clase.get("intent"), route=clase.get("route"),
    )
    clase["plan"] = plan
    clase["bolsillo"] = bolsillo
    return plan.get("decision"), clase


def main() -> int:

    sys.stdout.reconfigure(encoding="utf-8")

    modelo = build_bid_model(
        json.load(open(RIVALES, encoding="utf-8-sig")),
        price_lookup=build_historical_price_lookup(),
        own_user_id=14175949,
    )

    fotos = {}
    for ruta in FOTOS + tuple(sys.argv[1:]):
        try:
            foto = json.load(open(ruta, encoding="utf-8-sig"))
        except Exception as error:                  # noqa: BLE001
            print(f"no se pudo leer {ruta}: {error}")
            continue
        fotos[(foto.get("meta") or {}).get("generated_at", "")[:16]] = (ruta, foto)

    for cuando, (ruta, foto) in sorted(fotos.items()):

        tarifa = tarifa_de(foto)
        filas = [
            f for f in foto["acquisition"]["targets"]
            if f.get("seller_id") is None and not f.get("rival_market")
        ]

        print(f"\n==== FOTO {cuando}  ({ruta})  candidatos del Computer: {len(filas)}  "
              f"bolsillos {foto['acquisition'].get('budgets')}")

        if not tarifa:
            print("  sin tarifa publicada: ninguna via de plantilla tiene valor y la "
                  "moneda no puede cambiar nada")
            continue

        factor = EUROS_POR_PUNTO / tarifa
        print(f"  tarifa del mercado {tarifa} EUR/punto -> x{factor:.3f}")

        fiel = pasan_hoy = pasan_con = 0
        for f in filas:
            hoy, _ = decide(f, foto, 1.0, modelo)
            con, clase = decide(f, foto, factor, modelo)
            publicada = f.get("decision")
            fiel += hoy == publicada
            pasan_hoy += publicada == "BID"
            pasan_con += con == "BID"
            marca = "" if hoy == publicada else f"   [reconstruido sin moneda: {hoy}]"
            if clase.get("fichaje") or publicada != con or marca:
                plan = clase.get("plan") or {}
                print(f"    {f['name']:20s} precio {f['market_price']:>9}  "
                      f"EUR/punto que pide {round(f['market_price'] / max(1, f.get('expected_points') or 1)):>6}  "
                      f"hoy {publicada:26s} con la moneda {con:26s} "
                      f"via {clase.get('route')} {clase.get('intent')}  "
                      f"valor de fichaje {clase.get('fichaje', 0):>9}  "
                      f"pujaria {plan.get('bid') or 0:>9}  bolsillo {clase.get('bolsillo')}{marca}")
        print(f"  reconstruccion SIN moneda igual a la foto: {fiel} de {len(filas)}")
        print(f"  pasan todas: hoy {pasan_hoy}, con la moneda {pasan_con}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
