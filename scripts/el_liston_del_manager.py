"""
El liston del que paga mas: la tabla contrafactual, margen a margen.

LA PREGUNTA

    Con un liston de `mercado x (1 + 0,55 % + margen)`, que
    habria pasado con las cinco ofertas de manager que nos
    llegaron el 12 y el 13/08/2026 y contraofertamos las cinco?

DE DONDE SALE CADA NUMERO

    · Las cinco ofertas -importe, valor de mercado del momento y
      hasta cuando vivian- salen de las fotos de `data/`.
    · Lo que pasó DESPUES sale del tablon: a Yeray y a Ximo
      Navarro acabamos vendiendolos al Computer, y esos dos
      importes son el contrafactual entero.
    · Jutgla y Olasagasti siguen siendo nuestros Y ESTAN EN EL
      ONCE. La excepcion del dueño los protege con cualquier
      margen, asi que su fila no depende de este numero.

    Se corre el MOTOR de verdad -`evaluate_sale_to_rival`- en
    las dos posiciones del interruptor. Lo que no se sabe de
    aquel dia -las puntuaciones internas de venta- va con los
    valores por defecto del motor, y se dice: con ellos las
    cinco salen COUNTER_OFFER, que es exactamente lo que pasó.

EL `n` QUE TIENE ESTA TABLA, Y ES PEQUEÑO

    Dos. Solo dos de las cinco tienen desenlace medible, y las
    dos van en direcciones contrarias. La tabla entera gira
    sobre UN jugador: Ximo Navarro.

NI RED, NI ESCRITURAS, NI RELOJ

    Todo son constantes de este fichero y el motor. No abre
    `data/`, no sale a la red y no enciende nada.

COMO SE USA

    python -m scripts.el_liston_del_manager
"""

from __future__ import annotations

import os
import sys

from pathlib import Path


RAIZ = Path(__file__).resolve().parents[1]

if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))


from src.analysis.competitive_transaction_engine import (     # noqa: E402
    ENV_LISTON_DEL_MANAGER,
    ENV_MARGEN_DEL_MANAGER,
    VARA_DEL_COMPUTER_PERCENT,
    evaluate_sale_to_rival,
)

from src.analysis.offer_decision_engine import PREMIUM_GOOD   # noqa: E402


# ----------------------------------------------------------------
# LAS CINCO, CON SU DESENLACE
#
#     `cobrado_despues` es lo que acabamos cobrando por el
#     jugador. `None` cuando sigue con nosotros.
# ----------------------------------------------------------------

LAS_CINCO = (
    dict(
        fecha="2026-08-12 05:26",
        jugador="Yeray",
        de="Luismi_Haz",
        importe=2_000_000,
        mercado=1_880_000,
        vive_horas=3.1,
        en_el_once=False,
        cobrado_despues=1_838_100,
        cuando_despues="2026-08-22, al Computer",
    ),
    dict(
        fecha="2026-08-12 08:29",
        jugador="Ximo Navarro",
        de="Pollo17",
        importe=1_200_000,
        mercado=1_170_000,
        vive_horas=45.3,
        en_el_once=False,
        cobrado_despues=1_385_700,
        cuando_despues="2026-08-20, al Computer",
    ),
    dict(
        fecha="2026-08-12 08:31",
        jugador="Jutgla",
        de="Pollo17",
        importe=4_300_000,
        mercado=4_120_000,
        vive_horas=44.8,
        en_el_once=True,
        cobrado_despues=None,
        cuando_despues="sigue con nosotros, 29 puntos, EN EL ONCE",
    ),
    dict(
        fecha="2026-08-12 11:03",
        jugador="Olasagasti",
        de="Pollo17",
        importe=2_750_000,
        mercado=2_620_000,
        vive_horas=43.5,
        en_el_once=True,
        cobrado_despues=None,
        cuando_despues="sigue con nosotros, 32 puntos, EN EL ONCE",
    ),
    dict(
        fecha="2026-08-13 13:35",
        jugador="Olasagasti",
        de="Pollo17",
        importe=2_740_000,
        mercado=2_660_000,
        vive_horas=16.9,
        en_el_once=True,
        cobrado_despues=None,
        cuando_despues="sigue con nosotros, 32 puntos, EN EL ONCE",
    ),
)


MARGENES = (0.0, 1.0, 2.0, 2.05, 2.1, 2.45, 3.0)


# El margen que propone el informe del 20/09. Se PROPONE: no
# esta puesto en ningun sitio y no lo pone este fichero.
MARGEN_PROPUESTO = 2.45


def _decide(oferta: dict, margen) -> dict:
    """El motor de verdad, con el interruptor donde toque."""

    antes = (
        os.environ.get(ENV_LISTON_DEL_MANAGER),
        os.environ.get(ENV_MARGEN_DEL_MANAGER),
    )

    try:

        if margen is None:
            os.environ.pop(ENV_LISTON_DEL_MANAGER, None)
            os.environ.pop(ENV_MARGEN_DEL_MANAGER, None)

        else:
            os.environ[ENV_LISTON_DEL_MANAGER] = "1"
            os.environ[ENV_MARGEN_DEL_MANAGER] = str(margen)

        return evaluate_sale_to_rival(
            amount=oferta["importe"],
            market_value=oferta["mercado"],
            rival_user_id=14145555,
            rival_intelligence={},
            in_lineup=oferta["en_el_once"],
        )

    finally:

        for clave, valor in zip(
            (ENV_LISTON_DEL_MANAGER, ENV_MARGEN_DEL_MANAGER), antes
        ):
            if valor is None:
                os.environ.pop(clave, None)
            else:
                os.environ[clave] = valor


def _acepta(salida: dict) -> bool:
    return salida["decision"] in {
        "ACCEPT_NOW",
        "ACCEPT_SACRIFICE_LINEUP",
    }


def _euros(valor) -> str:
    if valor is None:
        return "-"
    return f"{valor:,}".replace(",", ".")


def cuadro_de_las_cinco() -> None:

    print("=" * 78)
    print("LAS CINCO OFERTAS DE MANAGER  (12 y 13/08/2026)")
    print("=" * 78)
    print()
    print(
        f"  {'jugador':14s} {'de':11s} {'importe':>11s} "
        f"{'mercado':>11s} {'prima':>7s} {'vive':>6s}  desenlace"
    )
    print("  " + "-" * 74)

    for oferta in LAS_CINCO:

        prima = (
            oferta["importe"] / oferta["mercado"] - 1.0
        ) * 100.0

        print(
            f"  {oferta['jugador']:14s} {oferta['de']:11s} "
            f"{_euros(oferta['importe']):>11s} "
            f"{_euros(oferta['mercado']):>11s} {prima:+6.1f}% "
            f"{oferta['vive_horas']:5.1f}h  {oferta['cuando_despues']}"
        )

    print()
    print(
        f"  Las cinco se CONTRAOFERTARON. Apagado, el motor "
        f"sigue diciendo lo mismo:"
    )

    for oferta in LAS_CINCO:
        salida = _decide(oferta, None)
        print(
            f"    {oferta['jugador']:14s} {salida['decision']:14s} "
            f"precio estrategico {_euros(salida['strategic_sell_price']):>11s}"
        )


def cuadro_por_margen() -> None:

    print()
    print("=" * 78)
    print("QUE HABRIA PASADO, MARGEN A MARGEN")
    print("=" * 78)
    print()
    print(
        f"  liston = mercado x (1 + {VARA_DEL_COMPUTER_PERCENT:.2f} % "
        f"+ margen), topado en el +{PREMIUM_GOOD:.1f} % del Computer"
    )
    print()

    cabecera = "  " + f"{'margen':>7s} {'liston':>8s} "

    for oferta in LAS_CINCO:
        cabecera += f"{oferta['jugador'][:11]:>12s} "

    cabecera += f"{'resultado':>12s}"

    print(cabecera)
    print("  " + "-" * (len(cabecera) - 2))

    for margen in MARGENES:

        liston_pct = min(
            VARA_DEL_COMPUTER_PERCENT + margen, PREMIUM_GOOD
        )

        fila = f"  {margen:6.2f}  {liston_pct:+7.2f}% "

        resultado = 0

        for oferta in LAS_CINCO:

            salida = _decide(oferta, margen)

            if oferta["en_el_once"]:
                fila += f"{'ONCE':>12s} "
                continue

            if _acepta(salida):
                fila += f"{'ACEPTA':>12s} "
                resultado += (
                    oferta["importe"] - oferta["cobrado_despues"]
                )
            else:
                fila += f"{'contraoferta':>12s} "

        fila += f"{resultado:>+12,}".replace(",", ".")

        print(fila)

    print()
    print(
        "  `ONCE` = la excepcion del dueño lo protege con "
        "cualquier margen: no depende de este numero."
    )
    print(
        "  `resultado` = lo que habriamos cobrado aceptando "
        "menos lo que cobramos de verdad."
    )
    print()
    print("  De las cinco, solo DOS tienen desenlace medible.")
    print(
        "  Yeray: aceptar daba +161.900. Ximo Navarro: aceptar "
        "costaba -185.700."
    )
    print(
        "  La tabla entera gira sobre Ximo Navarro y sobre una "
        "decima de punto: n = 2."
    )


def cuadro_del_propuesto() -> None:

    print()
    print("=" * 78)
    print(f"CON EL MARGEN QUE SE PROPONE  (+{MARGEN_PROPUESTO} pp)")
    print("=" * 78)
    print()

    for oferta in LAS_CINCO:

        salida = _decide(oferta, MARGEN_PROPUESTO)

        print(
            f"  {oferta['jugador']:14s} "
            f"{salida['decision']:16s} "
            f"liston {_euros(salida['liston_del_manager']):>11s} "
            f"contra oferta de {_euros(oferta['importe']):>11s}"
        )
        print(f"      {salida['liston_del_manager_reason']}")

    print()
    print(
        f"  +{MARGEN_PROPUESTO} pp sobre el "
        f"{VARA_DEL_COMPUTER_PERCENT:.2f} % da un liston del "
        f"+{PREMIUM_GOOD:.1f} %: EL MISMO que le pedimos al "
        f"Computer."
    )
    print(
        "  Es el maximo que la regla permite, y no es un numero "
        "nuevo (doctrina 84)."
    )
    print()
    print("  NO ESTA PUESTO. El margen lo pone el dueño.")


def main() -> None:
    cuadro_de_las_cinco()
    cuadro_por_margen()
    cuadro_del_propuesto()


if __name__ == "__main__":
    main()
