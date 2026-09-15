"""
El antes y el despues: que cambia si se enchufa el ojeador.

QUE HACE

    Recorre los candidatos del informe del ojeador y pone dos
    columnas al lado:

        rinde HOY          el 0,1443 % constante que se observo
        rinde CON ojeador  el que sale de `el_pronostico_del_ojeador`

    y cuenta cuantos pasan el liston del 3 %. NO cambia nada: el
    interruptor sigue apagado.

LO QUE NO PUEDE HACER, Y SE DICE

    La foto de los 69 candidatos es la del 14/09 y en este disco
    no esta —el `status.json` local es del 16/08—. Asi que la
    tabla se hace sobre los jugadores del informe del ojeador que
    hay, y se publica cuantos son. El reparto entre "entra" y "no
    entra" es el que importa, y ese no depende de cual sea la
    foto.

EL LIBRO DE ACIERTO TAMPOCO ESTA EN ESTE DISCO

    El local tiene 8 predicciones, todas de prensa y todas sin
    resolver. Los numeros de produccion —89,1 %, 95,5 %, 97,1 %,
    72,9 %— se pasan con `--libro produccion` y se dice que
    vienen de fuera. Con `--libro local` se usa el de disco, y
    entonces no habra pronostico para nadie: eso TAMBIEN es un
    resultado, y es el que hay que ver si el libro no llega.

COMO SE USA

    python -m scripts.el_ojeador_conectado
    python -m scripts.el_ojeador_conectado --libro local
"""

from __future__ import annotations

import argparse
import json

from pathlib import Path

from src.analysis.el_pronostico_del_ojeador import (
    esta_encendido,
    estimacion,
    medir_persistencia,
)
from src.analysis.player_value_engine import speculation_value
from src.analysis import rival_bid_model as puja


RAIZ = Path(__file__).parent.parent

INFORME = RAIZ / "data" / "intelligence" / "scout_report.json"

PRECIOS = RAIZ / "data" / "autopilot" / "price_history.json"

LIBRO_LOCAL = (
    RAIZ / "data" / "intelligence" / "scout_accuracy_ledger.json"
)

# EL LIBRO DE PRODUCCION, copiado del encargo del 15/09/2026.
#
#     No esta en este disco. Se escribe aqui con su `n` y se dice
#     de donde viene cada vez que se usa: un numero de fuera que
#     se pinta como propio es la peor clase de dato.
LIBRO_DE_PRODUCCION = {
    "FUTBOLFANTASY": {
        "decided": 7579,
        "hit_rate": 89.1,
        "mean_magnitude_error_percent": 3.98,
    },
    "ANALITICA": {
        "decided": 3295,
        "hit_rate": 95.5,
        "mean_magnitude_error_percent": 1.12,
    },
    "COMUNIATE": {
        "decided": 2982,
        "hit_rate": 97.1,
        "mean_magnitude_error_percent": 0.93,
    },
    "COMUNIATE_PULSO": {
        "decided": 1031,
        "hit_rate": 72.9,
        "mean_magnitude_error_percent": 35.71,
    },
}

# El numero que se observo en los nueve rechazos del 14/09.
RINDE_HOY = 0.1443

HORIZONTE = 3


def _leer(ruta: Path, por_defecto=None):
    try:
        return json.loads(ruta.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return por_defecto


def rendimiento(precio: int, ritmo: float) -> float | None:
    """
    Lo que el motor calcularia con ese ritmo. Sin rivales.

    Es la MISMA aritmetica de `rival_bid_model`: el mejor importe
    por valor esperado, y el rendimiento sobre el capital que
    inmoviliza. Sin rivales la probabilidad es 1, asi que esto es
    el TECHO de lo que rendiria — y aun asi sirve para comparar,
    porque el 0,1443 % de hoy es el mismo para todos.
    """

    valor = speculation_value(
        price=precio,
        daily_increment=0,
        horizon_days=HORIZONTE,
        velocity_percent_per_day=ritmo,
    )

    tope = int(valor.get("value") or 0)

    if tope <= 0:
        return None

    modelo = {"premium": {"curve": list(puja.DEFAULT_PREMIUM_CURVE)}}

    opciones = []

    for importe in puja.candidate_bids(
        precio, tope, modelo,
        prima_maxima=puja.PRIMA_MAXIMA_DE_PUJA,
    ):
        p = puja.win_probability(importe, precio, modelo, [])
        opciones.append((round(p * (tope - importe)), importe))

    if not opciones:
        return None

    ev, importe = max(opciones, key=lambda o: (o[0], -o[1]))

    return 100.0 * ev / max(importe, 1)


def main() -> int:

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--libro",
        choices=("produccion", "local"),
        default="produccion",
    )

    opciones = parser.parse_args()

    informe = _leer(INFORME, {})

    jugadores = (informe or {}).get("players") or {}

    if not jugadores:
        print(
            "El informe del ojeador llega vacio: no hay nada que "
            "comparar."
        )
        return 1

    if opciones.libro == "produccion":
        libro = LIBRO_DE_PRODUCCION
        de_donde = (
            "los numeros de PRODUCCION del 15/09 (no estan en "
            "este disco: vienen del encargo)"
        )
    else:
        from src.intelligence.scout.accuracy import summary

        libro = (summary(_leer(LIBRO_LOCAL, {})) or {}).get(
            "sources"
        ) or {}
        de_donde = "el libro de acierto LOCAL"

    print("=" * 78)
    print("EL OJEADOR CONECTADO — EL ANTES Y EL DESPUES")
    print("=" * 78)
    print()
    print(f"  interruptor: {'ENCENDIDO' if esta_encendido() else 'APAGADO'}")
    print(f"  informe del ojeador: {informe.get('generated_at')}")
    print(f"  jugadores en el informe: {len(jugadores)}")
    print(f"  libro de acierto: {de_donde}")
    print()

    for fuente, medida in sorted(libro.items()):
        print(
            f"     {fuente:<18} acierto "
            f"{medida.get('hit_rate')}  error de tamaño "
            f"{medida.get('mean_magnitude_error_percent')}  "
            f"n={medida.get('decided')}"
        )

    print()

    # LA PERSISTENCIA, RECALCULADA DESDE LA SERIE DE ESTE DISCO.
    historico = (_leer(PRECIOS) or {}).get("players") or {}

    # EL PRECIO DEL DIA, NO LA MUESTRA CRUDA.
    #
    #     El almacen muestrea dos veces al dia —03h y 07h— y las
    #     dos traen el mismo precio hasta que cambia a las 07:00.
    #     Midiendo sobre las muestras crudas, la mitad de los
    #     "movimientos de ayer" son cero y la persistencia sale
    #     0,000. Se colapsa a un precio por dia.
    from datetime import datetime                    # noqa: PLC0415

    from src.analysis.la_prima_de_compra import (     # noqa: PLC0415
        MADRID,
    )

    series = {}

    for k, v in historico.items():

        por_dia = {}

        for marca, precio in zip(
            (v or {}).get("t") or [], (v or {}).get("p") or []
        ):
            momento = datetime.fromtimestamp(marca, MADRID)

            if momento.hour >= 7:
                por_dia.setdefault(momento.date(), precio)

        series[k] = [por_dia[d] for d in sorted(por_dia)]

    medido = medir_persistencia(series)

    print(f"  persistencia recalculada aqui: {medido['reason']}")

    if medido.get("misma_direccion") is not None:
        print(
            f"     y el movimiento sigue en el mismo sentido el "
            f"{100 * medido['misma_direccion']:.1f} % de las "
            f"veces (n={medido['n_direccion']:,})"
        )

    print()

    filas = []

    for pid, ficha in jugadores.items():

        precio = int(ficha.get("market_price") or 0)

        if precio <= 0:
            continue

        r = estimacion(ficha, libro, horizonte=1)

        con = (
            rendimiento(precio, r["percent_per_day"])
            if r["available"]
            else None
        )

        filas.append(
            {
                "nombre": ficha.get("player_name"),
                "precio": precio,
                "pronostico": (
                    r["percent_per_day"] if r["available"] else None
                ),
                "con": con,
                "motivo": r.get("reason"),
            }
        )

    liston = 100.0 * puja.RENDIMIENTO_MINIMO_DEL_CAPITAL

    pasan_hoy = RINDE_HOY >= liston

    entran = [f for f in filas if f["con"] is not None and f["con"] >= liston]

    sin_pronostico = [f for f in filas if f["pronostico"] is None]

    print("-" * 78)
    print("EL REPARTO")
    print("-" * 78)
    print()
    print(f"  el liston son {liston:.1f} % (NO se toca)")
    print()
    print(f"  candidatos mirados            {len(filas)}")
    print(
        f"  rinde HOY {RINDE_HOY:.4f} % para todos  ->  "
        f"pasan {len(filas) if pasan_hoy else 0}"
    )
    print(
        f"  con el ojeador                ->  pasan "
        f"{len(entran)}"
    )
    print(
        f"  sin pronostico (no entran)    {len(sin_pronostico)}"
        f"   ({100 * len(sin_pronostico) / len(filas):.0f} %)"
    )
    print()

    if not pasan_hoy:
        print(
            f"  ANTES no entraba NI UNO: el 0,1443 % esta por "
            f"debajo del {liston:.0f} % para todo el mundo."
        )
        print(
            f"  AHORA entran {len(entran)}, y los "
            f"{len(filas) - len(entran)} restantes siguen fuera."
        )
        print()
        print(
            "  NADIE SALE que antes entrara, porque antes no "
            "entraba nadie."
        )

    print()
    print("-" * 78)
    print(f"LOS QUE ENTRARIAN ({len(entran)})")
    print("-" * 78)
    print()

    if not entran:
        print("  Ninguno.")

    else:
        print(
            f"  {'jugador':<22}{'precio':>12}{'pronostico':>13}"
            f"{'rinde':>10}"
        )
        print()

        for f in sorted(entran, key=lambda f: -f["con"])[:40]:
            print(
                f"  {(f['nombre'] or '?')[:20]:<22}"
                f"{f['precio']:>12,}"
                f"{f['pronostico']:>+12.3f}%{f['con']:>9.2f}%"
            )

        if len(entran) > 40:
            print(f"  ... y {len(entran) - 40} mas")

    print()

    if len(entran) > 40:
        print(
            "  AVISO: entran mas de cuarenta. El encargo lo dijo: "
            "eso es una alarma, no una victoria."
        )
        print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
