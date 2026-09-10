"""
La salida del viaje: cuando se cobra la oferta de un VIAJE.

QUE ES UN VIAJE

    Un jugador comprado por el cupo de la rendija con una sola
    intencion: darle la vuelta. Se marca VIAJE en el libro con
    lo que costo, y esa marca es LO UNICO que le da permiso a
    esta ruta para tocarlo.

POR QUE HACE FALTA UNA RUTA APARTE

    El motor de ventas de siempre pregunta "¿esta este jugador
    PARA VENDER?" y contesta bien: mira su `sale_score`, su
    proteccion y si hace falta en el once. Con las 14 ofertas
    vivas del 10/09 dijo KEEP_GOOD_OFFER ocho veces: "oferta
    buena, pero el jugador no esta para vender".

    Para un VIAJE esa es la pregunta equivocada. El jugador no
    tiene nada malo: es que se compro para revenderlo. La
    pregunta correcta es otra, y solo una:

        ¿la oferta supera lo que me costo mas el suelo?

EL SUELO SALE DE LA MEDICION, Y CONTRADICE LA INTUICION

    La prima de recompra del Computer (n=34) va de -2,73 % a
    +10,50 %, con mediana +2,91 %. Parecia que elegir CUANDO
    cobrar valdria tanto como elegir que comprar.

    Midiendolo, no: cada reset es una tirada nueva de esa
    distribucion, asi que esperar a una prima mejor cuesta dias
    con la ficha y el capital inmovilizados.

        suelo   acepta   espera   prima media   neto   %/dia
         0,0 %     94 %    1,1 d       3,49 %  3,24 %  3,05 %
         1,0 %     88 %    1,1 d       3,71 %  3,46 %  3,05 %   <--
         2,9 %     50 %    2,0 d       5,12 %  4,87 %  2,44 %
         4,2 %     26 %    3,8 d       6,40 %  6,15 %  1,63 %

    ESPERAR A LA MEDIANA CUESTA UN 20 % DEL RENDIMIENTO POR DIA.
    Esperar al p75, casi la mitad.

    Se elige el 1,0 % y no el 0,0 %: rinden igual -no hay ni una
    observacion entre +0,22 % y +1,00 %- y el 1,0 % deja margen
    para que un viaje no se cierre por migajas.

LO QUE ESTA RUTA NO PUEDE HACER, NUNCA

    1. Tocar a un jugador que no este marcado VIAJE.
    2. Vender a alguien que haya entrado en el once.
    3. Dejarnos con un solo portero.
    4. Vender por debajo de coste, salvo corte de perdidas
       explicito y publicado.
    5. Mas de `VENTAS_POR_VUELTA` ventas en una vuelta.

    Cada una tiene guardia con nombre en
    `test_la_salida_del_viaje_v1`.

NO DECIDE SOLA Y NO ESCRIBE

    Este modulo calcula y publica. Quien escribe es
    `salida_executor`, cuya unica llamada es `accept_offer`.
    Y esta APAGADO: se enciende el sabado, con el dueno delante.

Este modulo no lee el mundo: todo se le pasa. Nunca lanza.
"""

from __future__ import annotations


# ============================================================
# EL SUELO
# ============================================================
#
#     Sobre el COSTE, no sobre el precio de mercado: lo que
#     decide es si la operacion gana dinero, no si el Computer
#     paga caro.
SUELO_DEL_VIAJE = 0.01

PRIMA_MEDIANA_MEDIDA = 2.91

VENTAS_MEDIDAS = 34


# ============================================================
# CUANTAS VENTAS POR VUELTA
# ============================================================
#
#     Cuatro, que es el cupo de compras al dia de la rendija.
#
#     No es un numero a ojo: si se pueden cerrar tantos viajes
#     como se abren, la cola NO PUEDE CRECER. Con un tope menor,
#     un dia de cuatro compras dejaria un viaje colgando; con
#     uno mayor no se gana nada, porque nunca hay mas de cuatro
#     abiertos por dia.
#
#     Y con el suelo en el 1 %, el 88 % de los viajes cierran en
#     el primer reset: la cola real sera de uno o dos.
VENTAS_POR_VUELTA = 4


# ============================================================
# CUANTO DURA UN VIAJE ABIERTO
# ============================================================
#
#     Cuatro resets. Con el suelo en el 1 % cierra el 88 % en el
#     primero y el 99 % en dos, asi que cuatro solo muerde en
#     una anomalia de verdad.
#
#     QUE PASA AL CADUCAR: el jugador DEJA DE SER UN VIAJE y
#     pasa al motor de ventas de siempre. NO se fuerza una venta
#     a perdidas: un plazo no es motivo para regalar dinero.
#
#     Y hay un limite mas duro que este, que manda cuando llega
#     antes: la jornada. Un VIAJE no puede seguir abierto cuando
#     arranca, porque si el jugador entra en el once ya no se
#     puede vender, y porque la deuda contingente se tapa antes
#     de jugar.
RESETS_QUE_DURA_UN_VIAJE = 4


ABIERTO = "ABIERTO"
CERRADO = "CERRADO"
CADUCADO = "CADUCADO"


# ============================================================
# EL ORDEN DE PREFERENCIA AL COMPRAR — NO ES UN FILTRO
# ============================================================
#
#     Sale de la misma medicion que el suelo: la prima que paga
#     el Computer al recomprar (n=34) NO es igual para todos.
#
#         POR POSICION      defensa   +3,67 %
#                           portero   +3,26 %
#                           medio     +2,85 %
#                           delantero +1,80 %
#
#         POR PRECIO        <1 M      +1,52 %
#                           1-3 M     +3,46 %
#                           3-6 M     +3,20 %
#                           6 M+      +3,83 %
#
#     UN DEFENSA SE RECOMPRA DOS PUNTOS MAS CARO QUE UN
#     DELANTERO, y es la mitad del negocio.
#
#     Y LOS BARATOS SE RECOMPRAN PEOR: +1,52 % sobre 150.000 son
#     2.250 EUR, que no pagan la ficha que ocupan.
#
#     ESTO NO RECHAZA A NADIE. Es un ORDEN: cuando haya que
#     elegir entre varios que ya pasaron todo lo demas, primero
#     los de arriba. Convertirlo en filtro seria inventar un
#     umbral nuevo con 34 observaciones, y no hay para tanto.
PRIMA_POR_POSICION = {
    2: 3.67,   # defensa
    1: 3.26,   # portero
    3: 2.85,   # medio
    4: 1.80,   # delantero
}


# Por debajo de esto la prima cae a la mitad y el viaje no paga
# la ficha. Se publica como AVISO en el orden, no como corte.
PRECIO_QUE_NO_PAGA_LA_FICHA = 1_000_000


def orden_de_preferencia(candidatos: list | None) -> list:
    """
    Los mismos candidatos, ORDENADOS por lo que se recompran.

    No quita a nadie: los pone en orden y dice por que. Forma
    fija. Nunca lanza.
    """

    try:
        filas = [
            c for c in (candidatos or []) if isinstance(c, dict)
        ]

        for fila in filas:

            posicion = safe_int(fila.get("position"))

            precio = safe_int(fila.get("market_price"))

            prima = PRIMA_POR_POSICION.get(posicion)

            fila["expected_buyback_percent"] = prima

            fila["thin"] = bool(
                precio and precio < PRECIO_QUE_NO_PAGA_LA_FICHA
            )

            fila["preference_reason"] = (
                (
                    f"Se recompra al {prima:+.2f} % de mediana."
                    if prima is not None
                    else "Sin prima medida para su posicion."
                )
                + (
                    f" AVISO: por debajo de "
                    f"{PRECIO_QUE_NO_PAGA_LA_FICHA // 1000}k la "
                    f"prima cae a la mitad y el viaje no paga la "
                    f"ficha."
                    if fila["thin"]
                    else ""
                )
            )

        # Primero los que mas se recompran; entre iguales, los
        # que no son finos de precio.
        return sorted(
            filas,
            key=lambda c: (
                -(c.get("expected_buyback_percent") or 0),
                bool(c.get("thin")),
                -safe_int(c.get("market_price")),
            ),
        )

    except Exception:                               # noqa: BLE001
        return list(candidatos or [])


def safe_int(value, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def safe_float(value):
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _euros(valor) -> str:
    try:
        return f"{int(valor):,}".replace(",", ".")
    except (TypeError, ValueError):
        return "?"


def precio_de_salida(
    coste, suelo: float = SUELO_DEL_VIAJE
) -> int:
    """Por debajo de esto no se cobra la oferta de un VIAJE."""

    return int(max(0, safe_int(coste)) * (1 + suelo))


def que_cobrar(
    viajes: list | None,
    ofertas: list | None,
    titulares: list | None = None,
    porteros_en_plantilla: int = 0,
    resets_pasados_por_viaje: dict | None = None,
    corte_de_perdidas: bool = False,
    suelo: float = SUELO_DEL_VIAJE,
    tope: int = VENTAS_POR_VUELTA,
) -> dict:
    """
    Que VIAJES se cobran en esta vuelta, y por que no los demas.

    CADA VIAJE trae `player_id`, `name`, `cost`, y opcionalmente
    `position`.

    CADA OFERTA trae `player_id` (o `players` con el nombre),
    `amount` y `offer_id`.

    Las cinco prohibiciones se aplican AQUI, en orden, y cada
    una deja dicho por que.

    Forma fija. Nunca lanza.
    """

    vacio = {
        "available": False,
        "sell": [],
        "skipped": [],
        "expired": [],
        "count": 0,
        "capped_at": tope,
        "dropped_by_cap": 0,
        "floor": suelo,
        "reason": None,
    }

    try:
        # LA MARCA TIENE QUE ESTAR, NO BASTA CON QUE NO ESTORBE
        #
        #     Aqui ponia `str(v.get("state") or ABIERTO)`, que
        #     convertia un estado VACIO en ABIERTO. Una marca a
        #     medio escribir -o un diccionario con la clave
        #     puesta a ""- daba permiso para vender.
        #
        #     La marca es el unico permiso que tiene esta ruta.
        #     Si no esta escrita entera, no hay permiso.
        #
        #     Y se compara EXACTA, sin normalizar mayusculas ni
        #     espacios. La escribe nuestro propio libro y
        #     siempre vale "ABIERTO"; cualquier otra cosa
        #     -"abierto ", "Abierto"- viene de un sitio que no
        #     hemos previsto, y un productor que no hemos
        #     previsto no puede dar permiso para vender.
        #
        #     Se cae del lado de no vender, que es el unico lado
        #     seguro cuando la accion es irreversible.
        abiertos = [
            v
            for v in (viajes or [])
            if isinstance(v, dict)
            and v.get("state") == ABIERTO
            and safe_int(v.get("player_id"))
        ]

        if not abiertos:
            return {
                **vacio,
                "available": True,
                "reason": "No hay ningun VIAJE abierto.",
            }

        # Las ofertas, por jugador.
        por_jugador = {}

        for oferta in (ofertas or []):

            if not isinstance(oferta, dict):
                continue

            pid = safe_int(oferta.get("player_id"))

            if pid:
                por_jugador[pid] = oferta

        del_once = {
            str(n).strip().lower()
            for n in (titulares or [])
            if n
        }

        resets = resets_pasados_por_viaje or {}

        elegidos = []

        saltados = []

        caducados = []

        def _saltar(viaje, motivo):
            saltados.append(
                {
                    "player_id": viaje.get("player_id"),
                    "name": viaje.get("name"),
                    "reason": motivo,
                }
            )

        # Cuantos porteros hay, para no quedarnos sin ninguno.
        porteros = max(0, safe_int(porteros_en_plantilla))

        for viaje in abiertos:

            pid = safe_int(viaje.get("player_id"))

            nombre = str(viaje.get("name") or "").strip().lower()

            coste = safe_int(viaje.get("cost"))

            # ------------------------------------------
            # PROHIBICION 2: el once no se toca
            # ------------------------------------------
            if nombre and nombre in del_once:
                _saltar(
                    viaje,
                    "Ha entrado en el once: un VIAJE no vende a "
                    "un titular.",
                )
                continue

            # ------------------------------------------
            # EL PLAZO
            # ------------------------------------------
            pasados = safe_int(resets.get(pid))

            if pasados >= RESETS_QUE_DURA_UN_VIAJE:
                caducados.append(
                    {
                        "player_id": pid,
                        "name": viaje.get("name"),
                        "resets": pasados,
                        "reason": (
                            f"Lleva {pasados} resets abierto. "
                            f"Deja de ser un VIAJE y pasa al "
                            f"motor de ventas de siempre. NO se "
                            f"fuerza una venta a perdidas."
                        ),
                    }
                )
                continue

            oferta = por_jugador.get(pid)

            if not oferta:
                _saltar(
                    viaje,
                    "Todavia no hay oferta del Computer: se "
                    "espera al proximo reset.",
                )
                continue

            importe = safe_int(oferta.get("amount"))

            # ------------------------------------------
            # PROHIBICION 3: nunca por debajo de un portero
            # ------------------------------------------
            if (
                safe_int(viaje.get("position")) == 1
                and porteros <= 1
            ):
                _saltar(
                    viaje,
                    "Es portero y solo queda uno: no se vende.",
                )
                continue

            # ------------------------------------------
            # PROHIBICION 4: nunca por debajo de coste
            # ------------------------------------------
            if importe < coste and not corte_de_perdidas:
                _saltar(
                    viaje,
                    (
                        f"La oferta ({_euros(importe)}) esta por "
                        f"debajo de lo que costo "
                        f"({_euros(coste)}) y no hay corte de "
                        f"perdidas declarado."
                    ),
                )
                continue

            # ------------------------------------------
            # EL SUELO
            # ------------------------------------------
            minimo = precio_de_salida(coste, suelo)

            if importe < minimo and not corte_de_perdidas:
                _saltar(
                    viaje,
                    (
                        f"La oferta ({_euros(importe)}) no llega "
                        f"al suelo ({_euros(minimo)} = coste + "
                        f"{suelo * 100:.0f} %). Se aguanta y se "
                        f"vuelve a mirar en el proximo reset."
                    ),
                )
                continue

            elegidos.append(
                {
                    "player_id": pid,
                    "name": viaje.get("name"),
                    "position": viaje.get("position"),
                    "offer_id": oferta.get("offer_id"),
                    "cost": coste,
                    "amount": importe,
                    "profit": importe - coste,
                    "yield_percent": round(
                        (importe - coste) / max(coste, 1) * 100, 2
                    ),
                    "loss_cut": bool(
                        corte_de_perdidas and importe < coste
                    ),
                }
            )

            if safe_int(viaje.get("position")) == 1:
                porteros -= 1

        # El mas rentable primero: si el tope corta, que corte
        # por el que menos deja.
        elegidos.sort(key=lambda v: -v["yield_percent"])

        limite = max(0, safe_int(tope))

        recortados = max(0, len(elegidos) - limite)

        elegidos = elegidos[:limite]

        return {
            "available": True,
            "sell": elegidos,
            "skipped": saltados,
            "expired": caducados,
            "count": len(elegidos),
            "capped_at": limite,
            "dropped_by_cap": recortados,
            "floor": suelo,
            "reason": (
                f"{len(elegidos)} viaje(s) se cobran"
                + (
                    f", {len(caducados)} caducado(s)"
                    if caducados
                    else ""
                )
                + (
                    f", {recortados} fuera por el tope de "
                    f"{limite}"
                    if recortados
                    else ""
                )
                + f". Suelo: coste + {suelo * 100:.0f} %."
            ),
        }

    except Exception as error:                      # noqa: BLE001
        return {
            **vacio,
            "reason": (
                f"No se pudo decidir la salida: "
                f"{type(error).__name__}: {error}"
            ),
        }
