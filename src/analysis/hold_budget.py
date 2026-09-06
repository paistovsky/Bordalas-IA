"""
De que bolsillo sale una compra por la via TENER, y cuanto.

EL DIAGNOSTICO DEL 14/09

    La via TENER quedo encendida y bloqueada. No por el liston
    del 3 % —que el retrotest confirmo— sino por el tope de
    973.594 EUR por operacion.

    Y ese tope no es un limite de riesgo pensado: es lo que sale
    de anidar dos fracciones.

        bolsillo de especular  2.433.987 x 40 %  =  973.594
        bolsillo de fichar     5.350.683         sin usar

DOS PIEZAS, Y SON DISTINTAS

    1. DE DONDE SALE EL DINERO. Lo decide el efecto sobre el
       balance, no el nombre de la via:

           ocupa una ficha vacia  ->  bolsillo de fichar
           rota (entra uno, sale otro)  ->  bolsillo de especular

       Tenemos 8 fichas libres. Comprar para llenar una no da
       nada a cambio: convierte caja en activo. Eso es un fichaje
       a efectos contables, aunque la tesis sea la rampa.

    2. CUANTO SE PUEDE PONER DE UNA VEZ. Eso NO lo decide el
       bolsillo: lo decide un tope deducido, aqui abajo.

SOBRE LA REGLA DEL 13/09, QUE VALE MAS QUE ESTE MODULO

    "El bolsillo, el liston y el valor salen todos de la misma
     via."

    Nacio para impedir que una compra se justificara con el
    numero de una via, se cobrara del bolsillo de otra y se
    examinara con el liston de una tercera. Aqui el valor lo da
    TENER y el liston es el de TENER, su 3 %. Los dos siguen
    emparejados.

    PERO HAY UN PELIGRO REAL Y HAY QUE DECIRLO. El bolsillo de
    especular es mas pequeño A PROPOSITO: el 40 % por operacion
    es donde vive la leccion de Soler, que fue meter el 81 % del
    presupuesto en un jugador. Mandar una apuesta de precio al
    bolsillo grande diluiria ese limite aunque no rompa la regla
    de las vias.

    Por eso el tope de abajo no es el del bolsillo: es propio,
    deducido, y arranca exactamente donde esta hoy el limite que
    de verdad ha estado gobernando estas compras. El primer dia
    no se afloja nada. Solo se afloja con evidencia viva.

EL TOPE, DEDUCIDO EN VEZ DE DECRETADO

    Tres condiciones a la vez, y manda la mas estrecha:

    1. QUE LA PEOR PERDIDA MEDIDA LA AGUANTE LA CAJA.
       El retrotest del 15/09 mide la peor operacion de la celda
       buena: -12,86 %. Poniendo P, la peor perdida son 0,1286 P,
       y tiene que quedar saldo positivo despues.

    2. QUE NO PASE DEL 10 % DEL PATRIMONIO EN UNA POSICION QUE NO
       JUEGA. Medido sobre la liga el 15/09, la mayor posicion no
       titular de cada manager:

           Pollo17   (1º)   9,48 %      Prinzipote (5º)   5,79 %
           Mex       (2º)   4,29 %      Manzagool  (7º)  15,53 %
           Luismi    (3º)   1,70 %      PEPE       (4º)  10,42 %

       Los tres que van por delante estan entre el 1,7 % y el
       9,5 %. El mas concentrado va ultimo. Mismo metodo que el
       tope de concentracion del 10/09: el limite se pone justo
       encima de la banda de los que ganan.

    3. UNA SOLA POSICION TENER ABIERTA A LA VEZ, hasta que el
       libro de pujas tenga operaciones cerradas de verdad.

LA ESCALERA, ESCRITA ANTES DE SUBIRLA

    142 operaciones de UNA semana de agosto son evidencia decente
    y fina a la vez. Agosto es la semana rara: se acaba de cerrar
    el mercado y los precios se estan recolocando.

    Asi que el tope arranca abajo y sube con evidencia viva:

        peldaño 0   973.594 EUR   el limite con el que este
                                  sistema ha operado siempre
        cada peldaño duplica, hasta el techo deducido

    PARA SUBIR UN PELDAÑO hacen falta N operaciones TENER
    cerradas cuya mediana realizada se parezca a la del
    retrotest. Y ninguno de los dos numeros es redondo:

        N = 12    Es el mismo corte que ya usa la casa para
                  decidir cuando una medida pesa mas que su
                  prior: `PREMIUM_SHRINK_SAMPLES = 12`, "con las
                  12 ventas minimas que exige el propio medidor,
                  el ratio y el prior pesarian lo mismo".

        margen    La mediana viva tiene que llegar al P25 del
                  retrotest, +2,68 %. No a la mediana: al p25.
                  Es decir, si la mitad de lo que nos pasa en
                  vivo bate lo que batia un cuarto de lo medido,
                  el retrotest aguanta.

    Y BAJA si la mediana viva se pone en negativo. Si ademas el
    tramo bueno deja de rendir el 3 %, la via se apaga sola: eso
    ya quedo puesto el 14/09.
"""

from __future__ import annotations


FICHAR = "FICHAR"
ESPECULAR = "ESPECULAR"


# El peldaño cero: el limite por operacion con el que este
# sistema ha operado siempre. No se afloja nada el primer dia.
FIRST_RUNG = 973_594


# Medido sobre las siete plantillas el 15/09/2026: la mayor
# posicion NO TITULAR de los tres que van por delante esta entre
# el 1,70 % y el 9,48 %. El tope queda justo encima.
MAX_NON_XI_SHARE = 0.10


# La peor operacion de la celda buena del retrotest del 15/09
# (`> 1 %/dia`, racha 1 dia, m=3, n=142).
WORST_MEASURED_LOSS = 0.1286


# Cuantas operaciones cerradas hacen falta para subir un peldaño.
# Es `PREMIUM_SHRINK_SAMPLES`: el corte que ya usa la casa para
# decidir cuando una medida pesa mas que su prior.
RUNG_SAMPLE = 12


# Y a donde tiene que llegar su mediana: al p25 del retrotest.
RUNG_MEDIAN_FLOOR = 0.0268


def safe_int(value, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def safe_float(value, default=None):
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def hold_pocket(free_roster_slots, occupies_empty_slot=None) -> dict:
    """
    De que bolsillo sale esta compra.

    `occupies_empty_slot` permite decirlo explicitamente; si no
    llega, se deduce de que haya fichas libres.
    """

    huecos = safe_int(free_roster_slots)

    ocupa = (
        bool(occupies_empty_slot)
        if occupies_empty_slot is not None
        else huecos > 0
    )

    if ocupa:
        return {
            "pocket": FICHAR,
            "intent": "XI_UPGRADE",
            "reason": (
                f"Llena una de las {huecos} fichas vacias: no sale "
                f"nadie, asi que a efectos de balance es un "
                f"fichaje. La tesis sigue siendo la rampa y el "
                f"liston sigue siendo el de TENER."
            ),
        }

    return {
        "pocket": ESPECULAR,
        "intent": "SPECULATION",
        "reason": (
            "No hay ficha vacia: entra uno y sale otro. Eso es "
            "cartera, y sale del bolsillo de especular."
        ),
    }


def _ladder(ceiling: int) -> list:
    """
    Los peldaños, del primero al techo. Cada uno dobla al
    anterior.
    """

    peldaños = []
    valor = FIRST_RUNG

    while valor < ceiling:
        peldaños.append(valor)
        valor *= 2

    peldaños.append(int(ceiling))

    return peldaños


def hold_cap(
    balance,
    squad_value,
    *,
    closed_operations: int = 0,
    live_median=None,
    open_positions: int = 0,
    worst_loss: float = WORST_MEASURED_LOSS,
) -> dict:
    """
    Cuanto se puede poner de una vez en una posicion TENER.

    Nunca lanza. Sin datos devuelve el peldaño cero, que es el
    limite de siempre.
    """

    try:
        saldo = safe_int(balance)
        plantilla = safe_int(squad_value)

        perdida = safe_float(worst_loss, WORST_MEASURED_LOSS)

        if not perdida or perdida <= 0:
            perdida = WORST_MEASURED_LOSS

        # --------------------------------------------------
        # CONDICION 1: la peor perdida medida la aguanta la caja
        # --------------------------------------------------
        #
        #     Poniendo P, la peor perdida medida son `perdida x P`
        #     y tiene que quedar saldo positivo despues.
        por_perdida = (
            int(saldo / perdida) if saldo > 0 else 0
        )

        # --------------------------------------------------
        # CONDICION 2: el 10 % del patrimonio, con la compra
        # dentro del denominador
        # --------------------------------------------------
        #
        #     parte = P / (plantilla + P) <= tope
        #     ->  P <= tope x plantilla / (1 - tope)
        por_concentracion = (
            int(
                MAX_NON_XI_SHARE
                * plantilla
                / (1.0 - MAX_NON_XI_SHARE)
            )
            if plantilla > 0
            else 0
        )

        candidatos = [
            valor for valor in (por_perdida, por_concentracion)
            if valor > 0
        ]

        techo = min(candidatos) if candidatos else FIRST_RUNG

        # --------------------------------------------------
        # LA ESCALERA
        # --------------------------------------------------

        peldaños = _ladder(max(techo, FIRST_RUNG))

        cerradas = safe_int(closed_operations)
        mediana = safe_float(live_median)

        # Se sube un peldaño por cada tanda de N operaciones
        # cerradas, y solo si la mediana viva llega al p25 del
        # retrotest.
        ganados = cerradas // RUNG_SAMPLE if cerradas else 0

        if ganados and (
            mediana is None or mediana < RUNG_MEDIAN_FLOOR
        ):
            ganados = 0

        # Y baja al peldaño cero si lo vivo pierde dinero.
        if mediana is not None and mediana < 0:
            ganados = 0

        indice = min(ganados, len(peldaños) - 1)

        tope = peldaños[indice]

        # --------------------------------------------------
        # CONDICION 3: una sola posicion abierta
        # --------------------------------------------------

        abiertas = safe_int(open_positions)

        bloqueado = abiertas >= 1

        return {
            "available": True,

            "cap": 0 if bloqueado else int(tope),
            "rung": indice,
            "rungs": peldaños,

            "ceiling": int(techo),
            "ceiling_by_worst_loss": por_perdida,
            "ceiling_by_concentration": por_concentracion,

            "worst_loss": perdida,
            "max_non_xi_share": MAX_NON_XI_SHARE,

            "closed_operations": cerradas,
            "live_median": mediana,
            "rung_sample": RUNG_SAMPLE,
            "rung_median_floor": RUNG_MEDIAN_FLOOR,

            "open_positions": abiertas,
            "blocked_by_open_position": bloqueado,

            "reason": (
                (
                    f"Ya hay {abiertas} posicion(es) TENER "
                    f"abierta(s). Solo una a la vez hasta que el "
                    f"libro de pujas tenga operaciones cerradas "
                    f"que confirmen el retrotest."
                )
                if bloqueado
                else (
                    f"Peldaño {indice} de {len(peldaños) - 1}: "
                    f"{format(int(tope), ',').replace(',', '.')} "
                    f"EUR. El techo son "
                    f"{format(int(techo), ',').replace(',', '.')} "
                    f"—el menor entre aguantar una perdida del "
                    f"{perdida * 100:.2f} % "
                    f"({format(por_perdida, ',').replace(',', '.')}) "
                    f"y no pasar del "
                    f"{MAX_NON_XI_SHARE * 100:.0f} % del patrimonio "
                    f"({format(por_concentracion, ',').replace(',', '.')})—. "
                    f"Se sube con {RUNG_SAMPLE} operaciones cerradas "
                    f"cuya mediana llegue al "
                    f"{RUNG_MEDIAN_FLOOR * 100:.2f} %."
                )
            ),
        }

    except Exception as error:                       # noqa: BLE001
        return {
            "available": False,
            "cap": FIRST_RUNG,
            "rung": 0,
            "reason": (
                f"No se pudo deducir el tope: "
                f"{type(error).__name__}: {error}. Se usa el "
                f"peldaño cero."
            ),
        }
