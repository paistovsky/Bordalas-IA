"""
Cuanto puede dar la rueda al mes, y si el volumen bate al margen.

LA PREGUNTA QUE NADIE HABIA HECHO

    Pepe juega dos juegos: el once, que da puntos, y la rueda,
    que da dinero -comprar al que sube, aguantar tres dias,
    vender al Computer, repetir-.

    Nadie ha calculado nunca cuanto puede dar la rueda al mes. Y
    ese numero decide cuanto esfuerzo merece todo lo demas: si
    son doscientos mil, es un entretenimiento caro; si son tres
    millones, es la liga.

LO QUE LIMITA LA RUEDA, Y EN QUE ORDEN

    1. EL CAPITAL. El bolsillo de especular mas la deuda que se
       autorice. Es el limite que casi siempre manda.
    2. LAS FICHAS. Cada operacion ocupa una: con ocho libres no
       caben nueve operaciones a la vez.
    3. EL TOPE POR OPERACION. Ninguna operacion puede llevarse
       mas de lo que el tope permita.
    4. EL MERCADO. El Computer solo pone ~20 jugadores al dia y
       casi ninguno cumple. Esto NO se modela aqui porque no se
       ha medido: se dice, y es la razon por la que el numero de
       abajo es un TECHO y no una prevision.

LO QUE NO SE ESCONDE

    El +4,47 % -y el +3,22 % del tramo 1-2 %- se midieron en una
    semana de agosto: mercado recien cerrado y precios
    recolocandose. Es la semana mas rara del año. Por eso todo
    sale con rango, y el rango incluye "la mitad de lo medido".

NO ENCIENDE NADA

    Calcula y publica. No compra, no vende y no mueve ningun
    liston.
"""

from __future__ import annotations


# Un mes de calendario, para pasar de ciclos a meses.
DIAS_DEL_MES = 30


# Lo que hay que descontar a una medicion hecha en una sola
# semana. No es un ajuste fino: es el reconocimiento de que la
# ventana era rara.
ESCENARIOS = (
    ("optimista", 1.00),
    ("prudente", 0.50),
    ("pesimista", 0.25),
)


def safe_int(value, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def safe_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _vacio(motivo: str) -> dict:
    return {
        "available": False,
        "capital": 0,
        "slots": 0,
        "cycle_days": 0,
        "per_operation_cap": None,
        "binding_limit": None,
        "deployable": 0,
        "cycles_per_month": None,
        "loss_rate": None,
        "resale_premium": None,
        "scenarios": [],
        "reason": motivo,
    }


def capacidad(
    capital: int,
    slots: int,
    cycle_days: int,
    median_return: float,
    loss_rate: float | None = None,
    resale_premium: float = 0.0,
    per_operation_cap: int | None = None,
) -> dict:
    """
    El techo mensual de la rueda, con su rango.

    `median_return` en tanto por uno: 0.0447 es el +4,47 %.

    Nunca lanza. Forma fija.
    """

    try:
        capital = safe_int(capital)
        slots = safe_int(slots)
        cycle_days = safe_int(cycle_days)

        if capital <= 0 or slots <= 0 or cycle_days <= 0:
            return _vacio(
                "Sin capital, sin fichas libres o sin ciclo: la "
                "rueda no puede girar."
            )

        tope = safe_int(per_operation_cap) or None

        # CUANTO SE PUEDE PONER A LA VEZ
        #
        #     Manda el mas estrecho de los tres. Publicar cual es
        #     importa mas que el numero: dice donde hay que tocar
        #     si se quiere que la rueda gire mas.
        por_fichas = (
            slots * tope if tope else capital
        )

        desplegable = min(capital, por_fichas)

        if desplegable == capital and (
            not tope or capital < por_fichas
        ):
            limite = "CAPITAL"
        elif tope and por_fichas < capital:
            limite = "FICHAS_Y_TOPE"
        else:
            limite = "CAPITAL"

        ciclos = DIAS_DEL_MES / cycle_days

        escenarios = []

        for nombre, factor in ESCENARIOS:

            rendimiento = safe_float(median_return) * factor

            # Cada ciclo se gana el rendimiento de la rampa mas la
            # prima del Computer al salir.
            por_ciclo = desplegable * (
                rendimiento + safe_float(resale_premium)
            )

            escenarios.append({
                "name": nombre,
                "factor": factor,
                "return_per_operation": round(
                    100 * rendimiento, 3
                ),
                "per_cycle": round(por_ciclo),
                "per_month": round(por_ciclo * ciclos),
                "per_month_percent": (
                    round(100 * por_ciclo * ciclos / capital, 1)
                    if capital
                    else None
                ),
            })

        return {
            "available": True,
            "capital": capital,
            "slots": slots,
            "cycle_days": cycle_days,
            "per_operation_cap": tope,
            "binding_limit": limite,
            "deployable": desplegable,
            "cycles_per_month": round(ciclos, 2),
            "loss_rate": (
                round(100 * safe_float(loss_rate), 1)
                if loss_rate is not None
                else None
            ),
            "resale_premium": round(
                100 * safe_float(resale_premium), 2
            ),
            "scenarios": escenarios,
            "reason": _reason_capacidad(
                desplegable, limite, ciclos, escenarios, capital
            ),
        }

    except Exception as error:                       # noqa: BLE001
        return _vacio(
            f"No se pudo calcular: "
            f"{type(error).__name__}: {error}"
        )


def _reason_capacidad(
    desplegable, limite, ciclos, escenarios, capital
) -> str:

    def euros(valor):
        return f"{round(valor):,}".replace(",", ".")

    optimista = escenarios[0]
    prudente = escenarios[1]

    frase = (
        f"Con {euros(desplegable)} EUR desplegables y "
        f"{ciclos:.1f} ciclos al mes, la rueda da entre "
        f"{euros(escenarios[-1]['per_month'])} y "
        f"{euros(optimista['per_month'])} EUR al mes; el "
        f"escenario prudente -la mitad de lo medido en una "
        f"semana de agosto- son "
        f"{euros(prudente['per_month'])}."
    )

    frase += (
        f" Lo que limita es el {limite.replace('_', ' ').lower()}."
    )

    return frase


# ============================================================
# VOLUMEN CONTRA MARGEN
# ============================================================


def volumen_contra_margen(
    estrategias: list,
    capital: int,
    slots: int,
    resale_premium: float = 0.0,
) -> dict:
    """
    Muchas operaciones finas contra pocas gruesas.

    `estrategias` son celdas del retrotest ya medidas:
    `{name, median, loss_rate, n, share}` donde `share` es que
    fraccion del capital cabe en ese tramo -no todo el mercado
    ofrece jugadores de cualquier tramo-.

    Nunca lanza. Forma fija.
    """

    vacio = {
        "available": False,
        "rows": [],
        "winner": None,
        "capital": safe_int(capital),
        "reason": None,
    }

    try:
        if not estrategias or safe_int(capital) <= 0:
            return {
                **vacio,
                "reason": (
                    "Sin estrategias medidas o sin capital: no "
                    "hay nada que comparar."
                ),
            }

        filas = []

        for estrategia in estrategias:

            if not isinstance(estrategia, dict):
                continue

            mediana = safe_float(estrategia.get("median"))
            muestra = safe_int(estrategia.get("n"))

            if not muestra:
                continue

            # CUANTAS OPERACIONES CABEN DE ESE TRAMO
            #
            #     No es "todo el capital en el tramo bueno": el
            #     mercado no ofrece infinitos jugadores al 4 %
            #     diario. `share` dice que parte del capital se
            #     puede colocar ahi de verdad.
            porcion = safe_float(
                estrategia.get("share"), 1.0
            )

            colocado = safe_int(capital) * porcion

            por_ciclo = colocado * (
                mediana + safe_float(resale_premium)
            )

            filas.append({
                "name": estrategia.get("name"),
                "median_percent": round(100 * mediana, 2),
                "loss_rate_percent": (
                    round(
                        100 * safe_float(
                            estrategia.get("loss_rate")
                        ),
                        1,
                    )
                    if estrategia.get("loss_rate") is not None
                    else None
                ),
                "n": muestra,
                "capital_share_percent": round(100 * porcion, 1),
                "capital_used": round(colocado),
                "per_cycle": round(por_ciclo),
                "per_month": round(por_ciclo * (DIAS_DEL_MES / 3)),
            })

        if not filas:
            return {
                **vacio,
                "reason": "Ninguna estrategia tiene muestra.",
            }

        filas.sort(key=lambda f: -f["per_month"])

        mejor = filas[0]

        return {
            "available": True,
            "rows": filas,
            "winner": mejor["name"],
            "capital": safe_int(capital),
            "reason": _reason_volumen(filas),
        }

    except Exception as error:                       # noqa: BLE001
        return {
            **vacio,
            "reason": (
                f"No se pudo comparar: "
                f"{type(error).__name__}: {error}"
            ),
        }


def _reason_volumen(filas: list) -> str:

    def euros(valor):
        return f"{round(valor):,}".replace(",", ".")

    mejor = filas[0]
    peor = filas[-1]

    frase = (
        f"Gana «{mejor['name']}» con {euros(mejor['per_month'])} "
        f"EUR al mes contra los {euros(peor['per_month'])} de "
        f"«{peor['name']}»."
    )

    if mejor["loss_rate_percent"] is not None:
        frase += (
            f" Pierde en el {mejor['loss_rate_percent']} % de las "
            f"operaciones."
        )

    frase += (
        " La diferencia sale de cuanto capital se puede colocar "
        "en cada tramo, no solo de lo que rinde cada operacion: "
        "el mercado no ofrece infinitos jugadores del tramo "
        "bueno."
    )

    return frase
