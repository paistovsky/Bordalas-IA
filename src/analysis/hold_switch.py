"""
La via TENER se apaga sola si su tramo deja de rendir.

DE DONDE SALE ESTO (17/09/2026)

    La noche que se cayo produccion se quitaron de la verja dos
    aserciones que no podian estar ahi:

        "el tramo 2-4 % rinde mas del 3 % a tres dias"
        "comprar a alguien que cae pierde el 80 % de las veces"

    Las dos eran ciertas. Ninguna era una propiedad del codigo:
    eran mediciones del mercado, y por eso la verja se ponia roja
    sola cuando el mercado cambiaba, sin que nadie tocara nada.

    Pero la pregunta que hacian SI importa, y mucho: si el tramo
    que sostiene la via TENER deja de rendir el 3 %, la via se
    esta apoyando en nada.

    Asi que la comprobacion no se pierde: se muda. De comprobarse
    una vez en CI, a comprobarse EN CADA CICLO, con el almacen de
    produccion y con consecuencias de verdad.

LA DIFERENCIA, QUE ES TODA

    Una verja roja para el despliegue y no dice nada del mercado.
    Este interruptor no para nada: apaga la via que se ha quedado
    sin respaldo, deja las demas trabajando, y lo escribe en el
    tablero.

QUE APAGA Y QUE NO

    Se apaga un tramo cuando ESTA MEDIDO y rinde por debajo del
    liston, o cuando pierde demasiado a menudo.

    NO se apaga un tramo sin muestra. Ausencia de dato no es dato:
    un tramo sin medir sale como "sin muestra" en el tablero, que
    es una cosa distinta de "medido y malo", y quien lo mire tiene
    que poder distinguirlas.

EL LISTON ES EL MISMO, Y SE IMPORTA

    `MIN_SPECULATION_YIELD`, el 3 % de siempre. Importado y no
    copiado, porque la regla del 13/09 dice que el bolsillo, el
    liston y el valor salen todos de la misma via. Dos treses en
    dos ficheros se separan el dia que alguien mueve uno.
"""

from __future__ import annotations

from src.analysis.rival_bid_model import MIN_SPECULATION_YIELD


# El liston de la via, sin copiarlo.
MIN_TENER_YIELD = MIN_SPECULATION_YIELD


# EL TECHO DE PERDIDAS, QUE VENIA DE LA VERJA
#
#     Era la segunda mitad de la asercion que se quito: el tramo
#     bueno tenia menos de un 20 % de operaciones en perdida. Un
#     tramo puede rendir de mediana y perder la mitad de las
#     veces; eso no es una via, es una moneda.
MAX_TENER_LOSS_RATE = 0.20


# LA RACHA CON LA QUE SE JUZGA LA VIA EN EL TABLERO
#
#     La doctrina compra racha corta -"comprar a alguien que sube
#     mas del 1 % diario con racha corta y venderlo a tres
#     dias"-. Asi que el estado que se publica es el de esa
#     racha, no el de una que no se compraria.
#
#     Cada jugador se juzga con la SUYA; esto es solo para el
#     titular del tablero.
RACHA_QUE_SE_COMPRA = 1


def safe_float(value, default=None):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


# ============================================================
# UN TRAMO
# ============================================================


# DE RACHA A BANDA DEL RETROTEST
#
#     Las mismas de `hold_backtest.STREAK_BUCKETS`. Se importan
#     en vez de copiarse: si alli se parten, aqui tiene que
#     seguirlas.
def _banda_de_la_racha(racha) -> str | None:

    try:
        from src.analysis.hold_backtest import STREAK_BUCKETS

        dias = abs(int(racha))

        for nombre, minimo, maximo in STREAK_BUCKETS:
            if dias >= minimo and (maximo is None or dias <= maximo):
                return nombre

        return None

    except (TypeError, ValueError):
        return None


def bucket_backing(
    calibration: dict | None,
    bucket: str,
    streak=None,
) -> dict:
    """
    ¿Sostiene este tramo a la via TENER, ahora mismo?

    LA CELDA QUE SE MIRA (24/09/2026)

        Esto miraba la mediana de bloque, que `calibration`
        rellena con la banda de racha MAS LARGA con muestra. Para
        el recorte esta bien -a una racha de 50 dias se le
        reconoce como mucho lo que rindio la mas larga medida-,
        pero para decidir si la via esta respaldada manda otra
        cosa: la racha que de verdad se compra.

        En el tramo 1-2 % la diferencia lo tenia todo apagado:

            racha 1 dia   +3,22 %   <- la que compra la doctrina
            racha 2 dias  +1,80 %   <- la que decidia

        Y ese tramo es donde cabe el 100 % del capital: 1,24 M al
        mes contra los 310.000 del tramo de arriba.

        El liston del 3 % NO se ha movido. Lo que cambia es
        contra que numero se compara.

    Sin `streak` se comporta como siempre, para no cambiar a
    quien no le pase la racha.

    Nunca lanza. Sin calibracion o sin muestra devuelve
    `backed=None`, que NO es lo mismo que `False`.
    """

    try:
        datos = (
            (calibration or {}).get("by_rate_bucket") or {}
        ).get(bucket)

        if not datos or not datos.get("calibrated"):
            return {
                "bucket": bucket,
                "backed": None,
                "measured": False,
                "median": None,
                "loss_rate": None,
                "n": (datos or {}).get("n"),
                "required": MIN_TENER_YIELD,
                "max_loss_rate": MAX_TENER_LOSS_RATE,
                "band": None,
                "streak": streak,
                "margin": None,
                "reason": (
                    f"El tramo «{bucket}» no tiene muestra "
                    f"suficiente: no se puede decir ni que "
                    f"respalde ni que no."
                ),
            }

        # La celda que se compra, si se sabe cual es.
        banda = _banda_de_la_racha(streak)

        celda = (datos.get("bands") or {}).get(banda)

        if celda:
            mediana = safe_float(celda.get("median"))
            perdidas = safe_float(celda.get("loss_rate"))
            muestra = celda.get("n")
            mirada = banda
        else:
            mediana = safe_float(datos.get("median"))
            perdidas = safe_float(datos.get("loss_rate"))
            muestra = datos.get("n")
            mirada = datos.get("band")

        rinde = mediana is not None and mediana >= MIN_TENER_YIELD

        aguanta = (
            perdidas is None
            or perdidas <= MAX_TENER_LOSS_RATE
        )

        if rinde and aguanta:
            motivo = (
                f"El tramo «{bucket}» rinde un "
                f"{mediana * 100:.2f} % de mediana con un "
                f"{(perdidas or 0) * 100:.0f} % de operaciones en "
                f"perdida sobre {muestra}, mirando la racha de "
                f"«{mirada}»: respalda la via."
            )

        elif not rinde:
            motivo = (
                f"El tramo «{bucket}» rinde un "
                f"{mediana * 100:.2f} % de mediana y el liston de "
                f"la via es el {MIN_TENER_YIELD * 100:.0f} %. "
                f"Apagado: no hay con que sostener una compra."
            )

        else:
            motivo = (
                f"El tramo «{bucket}» rinde un "
                f"{mediana * 100:.2f} % pero pierde el "
                f"{perdidas * 100:.0f} % de las veces, por encima "
                f"del {MAX_TENER_LOSS_RATE * 100:.0f} % que "
                f"aguanta la via. Apagado."
            )

        return {
            "bucket": bucket,
            "backed": bool(rinde and aguanta),
            "measured": True,
            "median": mediana,
            "loss_rate": perdidas,
            "n": muestra,
            "band": mirada,
            "streak": streak,
            "required": MIN_TENER_YIELD,
            "max_loss_rate": MAX_TENER_LOSS_RATE,

            # Cuanto le sobra -o le falta- al tramo para el
            # liston. Es lo que avisa ANTES de que se apague.
            "margin": (
                round(mediana - MIN_TENER_YIELD, 4)
                if mediana is not None
                else None
            ),

            "reason": motivo,
        }

    except Exception as error:                       # noqa: BLE001
        return {
            "bucket": bucket,
            "backed": None,
            "measured": False,
            "median": None,
            "loss_rate": None,
            "n": None,
            "required": MIN_TENER_YIELD,
            "max_loss_rate": MAX_TENER_LOSS_RATE,
            "band": None,
            "streak": None,
            "margin": None,
            "reason": (
                f"No se pudo comprobar el respaldo: "
                f"{type(error).__name__}: {error}"
            ),
        }


# ============================================================
# LA VIA ENTERA, PARA EL TABLERO
# ============================================================


def route_state(
    calibration: dict | None,
    horizon_days: int | None = None,
) -> dict:
    """
    Como esta la via TENER: que tramos la sostienen y cual va mas
    justo.

    Una linea que se pueda leer de un vistazo, y debajo la tabla.
    """

    try:
        calibrado = calibration or {}

        if not calibrado.get("available"):
            return {
                "available": False,
                "on": None,
                "horizon_days": horizon_days,
                "required": MIN_TENER_YIELD,
                "max_loss_rate": MAX_TENER_LOSS_RATE,
                "backing": [],
                "switched_off": [],
                "unmeasured": [],
                "closest": None,
                "buckets": [],
                "reason": (
                    calibrado.get("reason")
                    or "Sin retrotest: no se puede decir si la "
                    "via TENER esta respaldada."
                ),
            }

        # LA RACHA QUE SE COMPRA (24/09/2026)
        #
        #     El tablero enseña el estado de la via para la racha
        #     corta, que es la unica que la doctrina compra. Con
        #     la mediana de bloque, el tramo 1-2 % salia apagado
        #     por una banda de racha que nunca compraríamos.
        tramos = [
            bucket_backing(calibrado, nombre, streak=RACHA_QUE_SE_COMPRA)
            for nombre in (calibrado.get("by_rate_bucket") or {})
        ]

        # CAE no sostiene nada por definicion: es el tramo de los
        # que bajan, y la via no compra ahi. Se mide igual —es la
        # otra mitad de la asercion que se mudo— pero no cuenta
        # para decidir si la via esta encendida.
        candidatos = [
            t
            for t in tramos
            if t["bucket"] != "CAE"
        ]

        respaldan = [t for t in candidatos if t.get("backed")]

        apagados = [
            t
            for t in candidatos
            if t.get("measured") and not t.get("backed")
        ]

        sin_muestra = [
            t
            for t in candidatos
            if not t.get("measured")
        ]

        # El que va mas justo de los que SI respaldan: si ese cae,
        # cae el primero.
        al_limite = min(
            respaldan,
            key=lambda t: t["margin"],
            default=None,
        )

        return {
            "available": True,
            "on": bool(respaldan),
            "horizon_days": horizon_days,
            "required": MIN_TENER_YIELD,
            "max_loss_rate": MAX_TENER_LOSS_RATE,

            "backing": [t["bucket"] for t in respaldan],
            "switched_off": [t["bucket"] for t in apagados],
            "unmeasured": [t["bucket"] for t in sin_muestra],

            "closest": al_limite,

            "buckets": sorted(
                tramos,
                key=lambda t: (
                    t.get("median") is None,
                    -(t.get("median") or 0),
                ),
            ),

            "reason": _reason(
                respaldan,
                apagados,
                sin_muestra,
                al_limite,
                horizon_days,
            ),
        }

    except Exception as error:                       # noqa: BLE001
        return {
            "available": False,
            "on": None,
            "horizon_days": horizon_days,
            "required": MIN_TENER_YIELD,
            "max_loss_rate": MAX_TENER_LOSS_RATE,
            "backing": [],
            "switched_off": [],
            "unmeasured": [],
            "closest": None,
            "buckets": [],
            "reason": (
                f"No se pudo leer el estado de la via: "
                f"{type(error).__name__}: {error}"
            ),
        }


def _reason(
    respaldan: list,
    apagados: list,
    sin_muestra: list,
    al_limite: dict | None,
    horizon_days,
) -> str:

    liston = f"{MIN_TENER_YIELD * 100:.0f} %"

    if not respaldan:

        if apagados:
            peor = max(
                apagados,
                key=lambda t: t.get("median") or -1,
            )

            return (
                f"VIA TENER APAGADA: ningun tramo llega al "
                f"{liston} a {horizon_days} dias. El mejor "
                f"medido, «{peor['bucket']}», se queda en "
                f"{(peor.get('median') or 0) * 100:.2f} %."
            )

        return (
            f"VIA TENER SIN RESPALDO MEDIDO: ningun tramo tiene "
            f"muestra suficiente a {horizon_days} dias. No se "
            f"apaga por eso -ausencia de dato no es dato- pero "
            f"tampoco hay nada que la sostenga."
        )

    encendidos = ", ".join(t["bucket"] for t in respaldan)

    frase = (
        f"Via TENER encendida por {len(respaldan)} tramo(s): "
        f"{encendidos}."
    )

    if al_limite is not None:
        frase += (
            f" El mas justo es «{al_limite['bucket']}», que rinde "
            f"{(al_limite.get('median') or 0) * 100:.2f} % contra "
            f"un liston del {liston}: le sobran "
            f"{(al_limite.get('margin') or 0) * 100:.2f} puntos. "
            f"Si baja de ahi, se apaga sola."
        )

    if apagados:
        frase += (
            f" Apagados por no llegar al liston: "
            + ", ".join(t["bucket"] for t in apagados)
            + "."
        )

    if sin_muestra:
        frase += (
            f" Sin muestra suficiente: "
            + ", ".join(t["bucket"] for t in sin_muestra)
            + "."
        )

    return frase
