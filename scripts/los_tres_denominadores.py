"""
Los tres denominadores: el plazo, los dias planos y la masa.

QUE HACE

    Mide, sobre la foto del 14/09 que SI esta en este disco
    (`diagnostico/status.json`, generada a las 18:12 y bajada a
    las 18:20) y sobre nuestra propia serie de precios:

        0. EL ECO       la magnitud del ojeador contra nuestro
                        `price_increment` y contra nuestra serie.

        1. LA RESERVA   de donde sale el 0,1443 %, con el ritmo
                        del ojeador presente.

        2. EL PLAZO     la tabla sube / plano / baja, arriba y
                        abajo, a 1, 3 y 7 dias, y el factor con
                        los dos denominadores.

        3. LA MASA      cuantas de las 72 pujas caen en cada
                        peldaño de verdad, y que cambia.

        4. SIN RED      la estimacion desde `price_history.json`
                        y los "sin pronostico".

    NO TOCA NADA. No escribe, no puja, no enciende. Imprime.

COMO SE USA

    python -m scripts.los_tres_denominadores
    python -m scripts.los_tres_denominadores --bloque 2
"""

from __future__ import annotations

import argparse
import json

from datetime import date
from pathlib import Path

from src.analysis import rival_bid_model as puja
from src.analysis.la_prima_de_compra import MADRID
from src.analysis.los_tres_denominadores import (
    contraste_con_el_ojeador,
    el_valor_de_reserva,
    estimacion_desde_el_historico,
    factor_de_persistencia,
    masa_real_de_la_curva,
    pares_al_plazo,
    se_agota_la_racha,
    serie_por_dia,
    tabla_de_persistencia,
)
from src.analysis.player_value_engine import (
    MAX_PROJECTED_DAILY_RATE,
    computer_resale_value,
    speculation_value,
)


RAIZ = Path(__file__).parent.parent

FOTO = RAIZ / "diagnostico" / "status.json"

PRECIOS = RAIZ / "data" / "autopilot" / "price_history.json"

INFORME = RAIZ / "data" / "intelligence" / "scout_report.json"

PUJAS = RAIZ / "data" / "trading" / "bid_outcome_ledger.json"

# Los cortes de `calibrate_premium_curve`. Se importan a mano
# porque la funcion los tiene dentro y no los publica.
CORTES = [0.05, 0.20, 0.40, 0.60, 0.80, 0.95, 0.995]

# El dia de la foto. No se deduce del reloj: se lee del `meta`.
HORIZONTE_DEL_LIBRO = 3


def _leer(ruta: Path, por_defecto=None):
    try:
        return json.loads(ruta.read_text(encoding="utf-8"))

    except (OSError, ValueError):
        return por_defecto


def _lo_publicado(motivo: str):
    """
    El valor esperado y el importe que lleva escrito el rechazo.

    El texto es
        "... rinde un 0.14 % (4.864 EUR sobre 3.370.001
         inmovilizados) ..."

    y esos dos numeros son los unicos que no hay que reconstruir:
    salieron del motor tal cual. Devuelve `(0, 0)` si el texto no
    tiene la forma esperada — nunca lanza, y un cero se ve.
    """

    try:
        trozo = motivo.split("(")[1].split(" EUR sobre ")

        return (
            int(trozo[0].replace(".", "").replace(",", "")),
            int(
                trozo[1]
                .split(" ")[0]
                .replace(".", "")
                .replace(",", "")
            ),
        )

    except (AttributeError, IndexError, ValueError):
        return (0, 0)


def _titulo(texto: str) -> None:
    print()
    print("=" * 76)
    print(texto)
    print("=" * 76)
    print()


def _sub(texto: str) -> None:
    print()
    print("-" * 76)
    print(texto)
    print("-" * 76)
    print()


# ============================================================
# BLOQUE 0 — EL ECO
# ============================================================


def bloque_cero(foto: dict, series: dict, dia_de_la_foto) -> None:

    _titulo("BLOQUE 0 — EL ECO: ¿nos dicen algo que no tengamos?")

    objetivos = (foto.get("acquisition") or {}).get("targets") or []

    iguales = distintos = 0

    for fila in objetivos:

        ojeador = (fila.get("scout") or {}).get(
            "mean_magnitude_percent"
        )

        precio = fila.get("market_price") or 0

        incremento = fila.get("price_increment")

        if ojeador is None or not precio or incremento is None:
            continue

        if abs(round(incremento / precio * 100, 3) - ojeador) <= 0.002:
            iguales += 1
        else:
            distintos += 1

    print(
        f"  acquisition.targets   magnitud == "
        f"price_increment/precio    {iguales} de "
        f"{iguales + distintos}"
    )

    # Y contra NUESTRA serie, que es lo que de verdad importa.
    destacados = (foto.get("scout") or {}).get("highlights") or []

    ok = mal = sin_serie = 0

    ayer = date.fromordinal(dia_de_la_foto.toordinal() - 1)

    for fila in destacados:

        serie = series.get(str(fila.get("player_id")))

        if not serie or dia_de_la_foto not in serie or ayer not in serie:
            sin_serie += 1
            continue

        nuestro = estimacion_desde_el_historico(
            serie, dia_de_la_foto, persistencia=1.0, minimo=0.0
        )

        contraste = contraste_con_el_ojeador(
            nuestro, fila.get("magnitude_percent")
        )

        if contraste.get("agree"):
            ok += 1
        else:
            mal += 1
            print(f"     DISCREPA  {contraste['reason']}")

    print(
        f"  scout.highlights      magnitud == "
        f"(precio-ayer)/precio      {ok} de {ok + mal}"
        + (f"   ({sin_serie} sin serie)" if sin_serie else "")
    )

    gate_ok = gate_mal = 0

    for fila in objetivos:

        compuerta = (fila.get("market_gate") or {}).get(
            "rate_percent_per_day"
        )

        ojeador = (fila.get("scout") or {}).get(
            "mean_magnitude_percent"
        )

        if compuerta is None or ojeador is None:
            continue

        if abs(compuerta - ojeador) <= 0.002:
            gate_ok += 1
        else:
            gate_mal += 1

    print(
        f"  market_gate.rate      == "
        f"scout.mean_magnitude_percent      {gate_ok} de "
        f"{gate_ok + gate_mal}"
    )

    print()
    print(
        "  DOCTRINA 57. El ritmo que decide la especulacion es "
        "nuestro propio `price_increment`"
    )
    print(
        "  dividido entre el precio. Las tres webs confirman la "
        "tuberia; no aportan un dato."
    )


# ============================================================
# BLOQUE 1 — DE DONDE SALE EL 0,1443 %
# ============================================================


def bloque_uno(foto: dict) -> None:

    _titulo(
        "BLOQUE 1 — EL 0,1443 % CON EL RITMO PRESENTE: el nombre "
        "del fallo"
    )

    adquisicion = foto.get("acquisition") or {}

    objetivos = adquisicion.get("targets") or []

    prima = (adquisicion.get("computer_premium") or {}).get(
        "median_percent"
    )

    modelo = {
        "premium": {
            "curve": [
                tuple(c)
                for c in (adquisicion.get("premium_model") or {}).get(
                    "curve"
                )
                or []
            ]
        },
        "rivals": adquisicion.get("rivals") or [],
    }

    if prima is None or not modelo["premium"]["curve"]:
        print("  La foto no trae prima del Computer o curva de pujas.")
        return

    # Los rechazos de verdad, leidos del texto de la foto.
    rechazos = []

    for fila in objetivos:

        for motivo in fila.get("bid_reasons") or []:

            if "Como especulacion rinde" not in motivo:
                continue

            precio = fila.get("market_price") or 0

            compuerta = fila.get("market_gate") or {}

            trading = speculation_value(
                price=precio,
                daily_increment=fila.get("price_increment") or 0,
                horizon_days=HORIZONTE_DEL_LIBRO,
                velocity_percent_per_day=compuerta.get(
                    "rate_percent_per_day"
                ),
            )

            reventa = computer_resale_value(
                price=precio, premium=prima / 100.0
            )

            por_trading = int(trading.get("value") or 0)
            por_reventa = int(reventa.get("value") or 0)

            # LA VIA SE DEDUCE DEL NUMERO PUBLICADO, NO SE
            # RECONSTRUYE.
            #
            #     `speculation_value` recibe en produccion una
            #     `confidence` que la foto no publica, asi que
            #     reconstruirla a mano da valores algo altos y
            #     para Gulacsi cambiaba la via.
            #
            #     El valor que SI se puede despejar es el que de
            #     verdad se uso: `EV = p x (valor - importe)`, y
            #     `p` e `importe` estan los dos en la foto.
            ev, importe = _lo_publicado(motivo)

            probabilidad = (
                puja.win_probability(importe, precio, modelo)
                if importe
                else 0.0
            )

            despejado = (
                int(importe + ev / probabilidad)
                if ev and probabilidad
                else None
            )

            gana_reventa = (
                despejado is not None
                and abs(despejado - por_reventa) <= abs(
                    despejado - por_trading
                )
            )

            rechazos.append(
                {
                    "player": fila.get("name"),
                    "price": precio,
                    "value": despejado or max(por_trading, por_reventa),
                    "route": (
                        "COMPUTER_RESALE"
                        if gana_reventa
                        else "PRICE_TREND"
                    ),
                    "intent": "SPECULATION",
                    "rate_percent_per_day": compuerta.get(
                        "rate_percent_per_day"
                    ),
                    "gate": compuerta.get("gate"),
                    "trend_days": compuerta.get("trend_days"),
                    "speculation_value": por_trading,
                    "resale_value": por_reventa,
                    "despejado": despejado,
                    "rinde": (
                        100.0 * ev / importe if ev and importe else None
                    ),
                    "texto": motivo,
                }
            )

            break

    if not rechazos:
        print(
            "  La foto no trae ningun rechazo por rendimiento: no "
            "hay nada que explicar."
        )
        return

    print(
        f"  {'jugador':<16}{'precio':>11}{'ritmo':>8}{'racha':>7}"
        f"{'valor usado':>13}{'= precio x':>12}{'la via':>16}"
        f"{'rinde':>9}"
    )
    print("  " + "-" * 92)

    for fila in sorted(rechazos, key=lambda f: -f["price"]):

        print(
            f"  {(fila['player'] or '?')[:15]:<16}"
            f"{fila['price']:>11,}"
            f"{fila['rate_percent_per_day']:>8}"
            f"{str(fila['trend_days']):>7}"
            f"{(fila['despejado'] or 0):>13,}"
            f"{(fila['despejado'] or 0) / fila['price']:>12.6f}"
            f"{fila['route']:>16}"
            f"{(fila['rinde'] or 0):>8.4f}%"
        )

    print()
    print(
        "  «valor usado» esta DESPEJADO de lo que publica la foto "
        "(EV, importe y p), no"
    )
    print(
        "  reconstruido: `speculation_value` recibe en produccion "
        "una confianza que la foto"
    )
    print("  no publica, y reconstruirla a ojo cambiaba la via.")

    aviso = el_valor_de_reserva(rechazos)

    _sub("EL AVISO, CON NOMBRE Y MOTIVO")

    señalados = {a["player"] for a in aviso.get("reserva") or []}

    print(
        f"  De {aviso['n']} candidatos, {len(señalados)} llevan un "
        f"valor que no depende del jugador."
    )
    print()

    vistos = set()

    for entrada in aviso.get("reserva") or []:

        clave = (entrada["player"], entrada["motivo"])

        if clave in vistos:
            continue

        vistos.add(clave)

        print(f"   - {entrada['reason']}")

    _sub("LA CONSTANTE, DESPEJADA")

    base = 1_000_000

    reventa = computer_resale_value(price=base, premium=prima / 100.0)

    ratio = (reventa.get("value") or 0) / base

    tope = puja.tope_por_la_prima(base, puja.PRIMA_MAXIMA_DE_PUJA)

    p = puja.win_probability(base + 1, base, modelo)

    print(
        f"  prima mediana del Computer        {prima} %   "
        f"(la MISMA para todo el tablero)"
    )
    print(
        f"  valor por COMPUTER_RESALE         precio x "
        f"{ratio:.6f}   = 1 + {prima / 100:.4f} x 0,75"
    )
    print(
        f"  probabilidad a precio+1           {p:.6f}   "
        f"(curva y rivales: iguales para todos)"
    )
    print()
    print(
        f"  rendimiento = {p:.6f} x {ratio - 1:.6f} = "
        f"{100 * p * (ratio - 1):.4f} %"
    )
    print()
    print(
        "  Ninguno de los dos factores contiene nada de ESTE "
        "jugador. Por eso es constante."
    )

    _sub("Y ADEMAS: ESA VIA NO PUEDE LLEGAR AL 3 % NUNCA")

    print(
        f"  techo de COMPUTER_RESALE con p=1  "
        f"{100 * (ratio - 1):.4f} %"
    )
    print(
        f"  liston exigido                    "
        f"{100 * puja.RENDIMIENTO_MINIMO_DEL_CAPITAL:.4f} %"
    )
    print()
    print(
        "  El liston del 3 % esta pensado para la via de tendencia "
        "y se le aplica a una via"
    )
    print(
        "  cuyo techo estructural es la mitad. No es que no pasara "
        "nadie: es que no puede."
    )
    print(f"  (tope de puja por la prima: {tope:,} sobre {base:,})")


# ============================================================
# BLOQUE 2 — EL PLAZO Y LOS DIAS PLANOS
# ============================================================


def bloque_dos(series: dict) -> dict:

    _titulo(
        "BLOQUE 2 — LA TABLA: sube / plano / baja, con su plazo"
    )

    honesto = None

    for horizonte in (1, 3, 7):

        pares = pares_al_plazo(series, horizonte=horizonte)

        tabla = tabla_de_persistencia(pares)

        if not tabla["available"]:
            print(f"  plazo {horizonte}: {tabla['reason']}")
            continue

        factor = factor_de_persistencia(pares, contando_planos=True)

        viejo = factor_de_persistencia(pares, contando_planos=False)

        if horizonte == 1:
            honesto = factor

        _sub(
            f"PLAZO {horizonte} DIA(S)   —   {tabla['n']:,} pares, "
            f"{len(series)} jugadores"
        )

        for etiqueta, clave in (
            ("de los pares en que AYER SUBIO (cualquier cantidad)", "subio"),
            ("de los pares en que AYER SUBIO >= 1 punto", "subio_fuerte"),
            ("de los pares en que AYER BAJO (cualquier cantidad)", "bajo"),
            ("de los pares en que AYER BAJO >= 1 punto", "bajo_fuerte"),
            ("de los pares en que AYER SE QUEDO PLANO", "plano"),
        ):
            grupo = tabla["groups"][clave]

            print(f"  {etiqueta}   (n = {grupo['n']:,})")

            if not grupo["n"]:
                print("     sin muestra")
                print()
                continue

            for nombre, cuenta, porcentaje in (
                ("hoy sube", grupo["sube"], grupo["sube_percent"]),
                ("hoy plano", grupo["plano"], grupo["plano_percent"]),
                ("hoy baja", grupo["baja"], grupo["baja_percent"]),
            ):
                print(
                    f"     {nombre:<12} n = {cuenta:>6,}   "
                    f"{porcentaje:>5.1f} %"
                )

            print()

        print(
            f"  factor CONTANDO los dias planos   "
            f"{factor['factor']:.4f}   n = {factor['n']:,}   "
            f"misma direccion {100 * factor['misma_direccion']:.1f} %"
        )
        print(
            f"  factor SIN contar los planos      "
            f"{viejo['factor']:.4f}   n = {viejo['n']:,}   "
            f"misma direccion {100 * viejo['misma_direccion']:.1f} %"
        )

    _sub("¿SE AGOTA? LA PERSISTENCIA POR DIAS DE RACHA (plazo 1 dia)")

    racha = se_agota_la_racha(pares_al_plazo(series, horizonte=1))

    print(
        f"  {'racha':<10}{'n':>8}{'hoy sigue':>12}{'hoy plano':>12}"
        f"{'se gira':>10}{'factor':>9}"
    )
    print("  " + "-" * 61)

    for tramo in racha["tramos"]:

        if not tramo["n"]:
            print(
                f"  {tramo['tramo']:<10}{0:>8}"
                f"{'sin muestra':>12}"
            )
            continue

        print(
            f"  {tramo['tramo']:<10}{tramo['n']:>8,}"
            f"{tramo['sigue_percent']:>11.1f}%"
            f"{tramo['plano_percent']:>11.1f}%"
            f"{tramo['gira_percent']:>9.1f}%"
            f"{tramo['factor']:>9.3f}"
        )

    return honesto or {}


# ============================================================
# BLOQUE 3 — LA MASA DE LA CURVA
# ============================================================


def bloque_tres(foto: dict, libro: dict) -> None:

    _titulo("BLOQUE 3 — LA MASA REAL DE CADA PELDAÑO")

    adquisicion = foto.get("acquisition") or {}

    premio = adquisicion.get("premium_model") or {}

    curva = [tuple(c) for c in premio.get("curve") or []]

    muestras = premio.get("samples") or 0

    medido = masa_real_de_la_curva(curva, CORTES, muestras)

    if not medido["available"]:
        print(f"  {medido['reason']}")
        return

    print(
        f"  {'peldaño':<9}{'prima':>10}{'corte':>8}"
        f"{'por construccion':>19}{'masa real':>12}{'n':>5}"
    )
    print("  " + "-" * 63)

    for k, paso in enumerate(medido["steps"], start=1):
        print(
            f"  {k:<9}{paso['factor']:>10.4f}{paso['corte']:>8}"
            f"{paso['peso_por_construccion']:>19.4f}"
            f"{paso['masa_real']:>12.4f}{paso['n']:>5}"
        )

    arriba = medido["steps"][-1]

    print()
    print(
        f"  el peldaño de arriba (+"
        f"{100 * (arriba['factor'] - 1):.2f} %) esta "
        f"{arriba['peso_por_construccion'] / max(arriba['masa_real'], 1e-9):.1f} "
        f"veces sobrevalorado"
    )

    rivales = adquisicion.get("rivals") or []

    por_construccion = {"premium": {"curve": curva}, "rivals": rivales}

    por_masa = {
        "premium": {"curve": medido["curva_por_masa"]},
        "rivals": rivales,
    }

    _sub("QUE CAMBIA EN NUESTRAS PUJAS REALES")

    filas = (libro or {}).get("bids") or {}

    if not filas:
        print("  El libro de pujas llega vacio: no hay pujas que medir.")

    else:
        print(
            f"  {'jugador':<18}{'precio':>11}{'puja':>11}"
            f"{'p 1/7':>9}{'p masa':>9}{'cambio':>9}"
        )
        print("  " + "-" * 67)

        cambios = []

        for entrada in filas.values():

            precio = entrada.get("market_price") or 0

            importe = entrada.get("amount") or 0

            if precio <= 0 or importe <= 0:
                continue

            antes = puja.win_probability(
                importe, precio, por_construccion
            )

            ahora = puja.win_probability(importe, precio, por_masa)

            cambios.append(ahora - antes)

            print(
                f"  {(entrada.get('player_name') or '?')[:17]:<18}"
                f"{precio:>11,}{importe:>11,}"
                f"{antes:>9.4f}{ahora:>9.4f}{ahora - antes:>+9.4f}"
            )

        if cambios:
            print()
            print(
                f"  n = {len(cambios)} pujas.  cambio medio "
                f"{sum(cambios) / len(cambios):+.4f}   "
                f"maximo {max(cambios):+.4f}"
            )

    _sub("RUBEN GARCIA — que habriamos pujado con una y con otra")

    rubén = None

    for entrada in filas.values():
        if str(entrada.get("player_id")) == "1602":
            rubén = entrada
            break

    if not rubén:
        print("  No esta en el libro de pujas de este disco.")
        return

    precio = rubén["market_price"]
    valor = rubén["our_value"]
    pagado = rubén["amount"]

    print(f"  precio de mercado   {precio:,}")
    print(f"  our_value           {valor:,}")
    print(
        f"  lo que se pago      {pagado:,}   "
        f"(+{100 * (pagado - precio) / precio:.2f} %, "
        f"+{pagado - precio:,} EUR)"
    )
    print(
        f"  compuerta           {rubén.get('market_gate')}, "
        f"{rubén.get('market_rate_percent_per_day')} %/dia, "
        f"racha {rubén.get('trend_days')}"
    )
    print("  rivales de verdad   NINGUNO")
    print()

    planes = {}

    for etiqueta, modelo in (
        ("por construccion 1/7", por_construccion),
        ("por masa real       ", por_masa),
    ):
        plan = puja.optimal_bid(
            price=precio,
            value=valor,
            model=modelo,
            intent="XI_UPGRADE",
        )

        planes[etiqueta] = plan

        print(
            f"  {etiqueta}  ->  pujar {plan['bid']:>10,}  "
            f"(+{100 * (plan['bid'] - precio) / precio:>5.2f} %)  "
            f"p={plan['win_probability']:.4f}"
        )

    distintos = {p["bid"] for p in planes.values()}

    print()

    if len(distintos) == 1:
        print(
            "  LA PUJA NO CAMBIA. La masa cambia la probabilidad "
            "que CREEMOS comprar"
        )
        print(
            f"  (0,5435 -> 0,8953), no el importe. Los dos fallos "
            f"NO son el mismo visto dos veces."
        )
    else:
        print(f"  la puja cambia en {max(distintos) - min(distintos):,} EUR")

    _sub("EL TECHO ESTRUCTURAL DE LA VIA SPECULATION (plazo 3 dias)")

    base = 1_000_000

    valor_max = speculation_value(
        price=base,
        daily_increment=0,
        horizon_days=HORIZONTE_DEL_LIBRO,
        velocity_percent_per_day=MAX_PROJECTED_DAILY_RATE,
    )

    tope = int(valor_max.get("value") or 0)

    importe = puja.tope_por_la_prima(base, puja.PRIMA_MAXIMA_DE_PUJA)

    margen = (tope - importe) / importe

    hace_falta = puja.RENDIMIENTO_MINIMO_DEL_CAPITAL / margen

    print(
        f"  ritmo maximo proyectable      "
        f"{MAX_PROJECTED_DAILY_RATE} %/dia   "
        f"(MAX_PROJECTED_DAILY_RATE)"
    )
    print(f"  valor maximo a 3 dias         precio x {tope / base:.5f}")
    print(
        f"  puja maxima                   precio x "
        f"{importe / base:.5f}   (PRIMA_MAXIMA_DE_PUJA)"
    )
    print(f"  margen bruto maximo           {100 * margen:.2f} %")
    print()
    print(
        f"  para llegar al "
        f"{100 * puja.RENDIMIENTO_MINIMO_DEL_CAPITAL:.0f} % hace "
        f"falta   p >= {hace_falta:.4f}"
    )

    for etiqueta, modelo in (
        ("1/7", por_construccion),
        ("masa real", por_masa),
    ):
        p = puja.win_probability(importe, base, modelo)

        print(
            f"  p a la puja maxima, {etiqueta:<12} = {p:.4f}   ->  "
            f"rinde {100 * p * margen:.2f} %   "
            f"{'PASA' if p >= hace_falta else 'NO LLEGA'}"
        )

    print()
    print(
        f"  rivales creibles: "
        f"{len(puja.credible_rivals({'rivals': rivales}, base))} "
        f"de {len(rivales)}"
    )


# ============================================================
# BLOQUE 4 — SIN RED
# ============================================================


def bloque_cuatro(
    series: dict,
    foto: dict,
    informe: dict,
    honesto: dict,
    dia_de_la_foto,
) -> None:

    _titulo("BLOQUE 4 — LA ESTIMACION SIN SALIR A LA RED")

    factor = honesto.get("factor") or 1.0

    objetivos = (foto.get("acquisition") or {}).get("targets") or []

    con = sin = sin_serie = 0

    discrepan = 0

    ejemplos = []

    for fila in objetivos:

        serie = series.get(str(fila.get("id")))

        if not serie:
            sin_serie += 1
            continue

        nuestro = estimacion_desde_el_historico(
            serie, dia_de_la_foto, persistencia=factor
        )

        crudo = estimacion_desde_el_historico(
            serie, dia_de_la_foto, persistencia=1.0, minimo=0.0
        )

        contraste = contraste_con_el_ojeador(
            crudo,
            (fila.get("scout") or {}).get("mean_magnitude_percent"),
        )

        if contraste.get("available") and not contraste.get("agree"):
            discrepan += 1
            print(f"  DISCREPA  {fila.get('name')}: {contraste['reason']}")

        if nuestro["available"]:
            con += 1
            ejemplos.append((fila.get("name"), nuestro))
        else:
            sin += 1

    print(
        f"  los {len(objetivos)} candidatos de la foto del 14/09, "
        f"contra NUESTRA serie:"
    )
    print()
    print(f"     con pronostico propio       {con}")
    print(f"     sin pronostico              {sin}")
    print(f"     sin serie nuestra           {sin_serie}")
    print(f"     DISCREPAN con el ojeador    {discrepan}")
    print()
    print(
        f"  persistencia usada: {factor:.4f} "
        f"(n={honesto.get('n', 0):,}, plazo "
        f"{honesto.get('plazo')} dia)"
    )

    if ejemplos:
        print()
        print(
            f"  {'jugador':<18}{'observado':>12}{'esperado':>12}"
            f"{'racha':>7}"
        )
        print("  " + "-" * 49)

        for nombre, medido in sorted(
            ejemplos, key=lambda e: -abs(e[1]["percent_per_day"])
        )[:12]:
            print(
                f"  {(nombre or '?')[:17]:<18}"
                f"{medido['observed_percent']:>+11.3f}%"
                f"{medido['percent_per_day']:>+11.3f}%"
                f"{medido['trend_days']:>7}"
            )

    _sub("¿LOS «SIN PRONOSTICO» SON LOS DE INCREMENTO CERO?")

    jugadores = (informe or {}).get("players") or {}

    if not jugadores:
        print("  El informe del ojeador llega vacio.")
        return

    from src.analysis.el_pronostico_del_ojeador import (  # noqa: PLC0415
        estimacion,
    )

    from scripts.el_ojeador_conectado import (  # noqa: PLC0415
        LIBRO_DE_PRODUCCION,
    )

    sin_pronostico = []
    con_pronostico = []

    for ficha in jugadores.values():

        if int(ficha.get("market_price") or 0) <= 0:
            continue

        medido = estimacion(ficha, LIBRO_DE_PRODUCCION, horizonte=1)

        señales = [
            s
            for s in (ficha.get("signals") or [])
            if s.get("horizon_days") == 1
        ]

        euros = [
            s.get("magnitude_eur")
            for s in señales
            if s.get("magnitude_eur") is not None
        ]

        incremento = euros[0] if euros else None

        destino = (
            con_pronostico if medido["available"] else sin_pronostico
        )

        destino.append((ficha.get("player_name"), incremento, señales))

    total = len(sin_pronostico) + len(con_pronostico)

    ceros = [f for f in sin_pronostico if f[1] == 0]

    mueven = [f for f in sin_pronostico if f[1] not in (0, None)]

    print(
        f"  candidatos del informe del ojeador "
        f"({informe.get('generated_at', '?')[:10]}):  {total}"
    )
    print(
        f"     SIN pronostico   {len(sin_pronostico)}   "
        f"({100 * len(sin_pronostico) / max(total, 1):.0f} %)"
    )
    print()
    print(f"     de esos, con incremento = 0    {len(ceros):>4}")
    print(
        f"     de esos, con incremento != 0   {len(mueven):>4}   "
        f"<- NO son los de incremento cero"
    )
    print()

    if mueven:
        print("  Los que SI se mueven y aun asi se callan (los mayores):")
        print()

        for nombre, incremento, señales in sorted(
            mueven, key=lambda f: -abs(f[1])
        )[:10]:
            print(
                f"     {str(nombre)[:22]:<24} incremento "
                f"{incremento:>+9,}   magnitudes "
                f"{[s.get('magnitude_percent') for s in señales]}"
            )

        print()
        print(
            "  No es que no se muevan: es que se mueven MENOS que "
            "el error de tamaño de las"
        )
        print(
            "  fuentes. El silencio no describe al jugador, "
            "describe a la fuente."
        )


def main() -> int:

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--bloque",
        type=int,
        choices=(0, 1, 2, 3, 4),
        default=None,
        help="correr solo un bloque",
    )

    opciones = parser.parse_args()

    foto = _leer(FOTO, {}) or {}

    if not foto:
        print(f"No hay foto en {FOTO}: sin foto no se mide nada.")
        return 1

    meta = foto.get("meta") or {}

    generada = str(meta.get("generated_at") or "")

    try:
        dia_de_la_foto = date.fromisoformat(generada[:10])

    except ValueError:
        print(
            f"La foto no dice cuando se genero ({generada!r}): no se "
            f"deduce del reloj."
        )
        return 1

    historico = (_leer(PRECIOS) or {}).get("players") or {}

    series = serie_por_dia(historico, MADRID)

    if not series:
        print(
            f"El historico de precios llega vacio ({PRECIOS}): sin "
            f"serie no hay medicion."
        )
        return 1

    dias = sorted({d for s in series.values() for d in s})

    print("=" * 76)
    print("LOS TRES DENOMINADORES — el plazo, los dias planos y la masa")
    print("=" * 76)
    print()
    print(f"  foto:       {generada}  ({FOTO.name})")
    print(
        f"  historico:  {dias[0]} -> {dias[-1]}   "
        f"{len(dias)} dias, {len(series)} jugadores"
    )

    huecos = [
        d
        for a, d in zip(dias, dias[1:])
        if (d - a).days > 1
    ]

    if huecos:
        print(
            f"  AGUJEROS en el calendario: "
            f"{', '.join(str(h) for h in huecos)} "
            f"(el dia anterior falta entero)"
        )

    print("  escrituras contra Biwenger: NINGUNA. Esto solo mide.")

    bloques = (
        [opciones.bloque]
        if opciones.bloque is not None
        else [0, 1, 2, 3, 4]
    )

    honesto = {}

    if 0 in bloques:
        bloque_cero(foto, series, dia_de_la_foto)

    if 1 in bloques:
        bloque_uno(foto)

    if 2 in bloques or 4 in bloques:
        medido = bloque_dos(series) if 2 in bloques else {}

        honesto = medido or factor_de_persistencia(
            pares_al_plazo(series, horizonte=1)
        )

    if 3 in bloques:
        bloque_tres(foto, _leer(PUJAS, {}) or {})

    if 4 in bloques:
        bloque_cuatro(
            series,
            foto,
            _leer(INFORME, {}) or {},
            honesto,
            dia_de_la_foto,
        )

    print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
