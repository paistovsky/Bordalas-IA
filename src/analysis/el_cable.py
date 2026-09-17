"""
El cable: unir la cola de venta con el presupuesto de fichar.

QUE ARREGLA

    Pepe tiene dinero que no sabe que tiene. En la foto del
    17/09 07:30:

        saldo                                     -373.984 EUR
        acquisition_budget                       8.874.116 EUR
        caja sobre la mesa en ofertas vivas      14.447.000 EUR
        free_slots                                         0

    `acquisition_budget` mira el saldo y el margen de deuda. No
    mira las nueve ofertas vivas que hay encima de la mesa por
    jugadores que la cola de venta ya marca como sobrantes.

LA ARITMETICA DEL 25 %, MEDIDA (17/09/2026)

        maximumBid = saldo + valor_de_plantilla/4 - comprometido

    18 de 18 combinaciones al euro. De cada jugador hay UN CUARTO
    de su precio dentro del techo, asi que venderlo a precio de
    mercado sube el techo 0,75 x precio, no el precio entero.

    La caja realizable NO esta contada dos veces: esta contada al
    25 %, y el saldo no la tiene contada en absoluto.

LA SEGURIDAD VA PRIMERO, Y NO SE NEGOCIA

    Contar caja que todavia no esta cobrada tiene un peligro
    obvio:

        si Pepe compromete una puja contra dinero que aun no ha
        cobrado y la venta no se cierra, se queda comprometido
        por encima de lo que tiene.

    Tres reglas, y las tres con guardia:

    1. DOS CIFRAS SEPARADAS, con nombres distintos y las dos
       publicadas. Nunca se suman en un solo numero. No hay
       ningun campo que valga `caja_ahora + caja_realizable`:
       si lo hubiera, alguien acabaria pujando contra el.

    2. NINGUNA PUJA CONTRA CAJA REALIZABLE. Si una operacion la
       necesita se marca `needs_sale_first` -el campo ya existe
       en `acquisition_valuation`- y la venta se ejecuta PRIMERO.
       Cobrada la venta, esa caja es caja normal y la puja va en
       la vuelta siguiente.

    3. LA CAJA REALIZABLE SOLO CUENTA LO QUE CUMPLE LAS TRES:
       la oferta esta viva, el jugador esta en la cola de venta
       como sobrante, y el conjunto pasa el `position_guardrail`.
       Lo que no cumple las tres no existe.

FASE OBSERVADOR

    `ENCENDIDO = False`. Esto calcula, publica y no manda. Lo
    enciende el dueño.

EL GUARDARRAIL NO SE REESCRIBE

    `position_guardrail.validate_sale_set` ya sabe decir si un
    CONJUNTO de ventas deja el once sin alinear. Aqui se le
    llama, prefijo a prefijo, igual que hace `sale_order`.
    Entra por argumento para que quede escrito.

DOCTRINA 64 — LA COLA SE ORDENA POR CONSECUENCIA

    En la foto del 17/09 Pepe eligio bien por el reloj y mal por
    las consecuencias:

        renovar la publicacion de Yamal   2,85 h   desbloquea: nada
        aceptar la oferta de Balde       47,5 h    desbloquea: todo

    Lo que se hace es dejar pasar delante a la que desbloquea,
    PERO SOLO SI LA OTRA SOBREVIVE A LA ESPERA. Y la espera se
    mide, no se supone: son `intervalo_de_cron + duracion_del
    ciclo`, las dos por argumento.
"""

from __future__ import annotations

from src.analysis.la_plaza_y_el_cable import (
    techo_tras_vender,
)


# ============================================================
# EL INTERRUPTOR
# ============================================================
#
# Se construye apagado. Lo enciende el dueño.
ENCENDIDO = False


# La regla que no se negocia. No es un interruptor: es una
# constante que existe para que se pueda leer y para que haya
# guardia sobre ella.
NUNCA_SE_PUJA_CONTRA_CAJA_REALIZABLE = True


# Solo esto es caja. Un jugador que vale mucho a mercado no es
# dinero: es una esperanza de que alguien lo compre.
CAJA_DE_VERDAD = "OFERTA_VIVA"


def safe_int(value, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def esta_encendido() -> bool:
    """El cable esta tendido y sin corriente."""

    return bool(ENCENDIDO)


def _miles(valor) -> str:
    """
    El separador de miles en el numero, no en la frase.

    `f"{x:,}".replace(",", ".")` sobre una frase entera se lleva
    por delante las comas de la prosa.
    """

    return f"{safe_int(valor):,}".replace(",", ".")


# ============================================================
# BLOQUE 1 — LA CAJA REALIZABLE
# ============================================================


def caja_realizable(
    sale_order: dict | None,
    *,
    guardarrail: dict | None,
    validador,
) -> dict:
    """
    Lo que entraria HOY aceptando ofertas vivas sobre sobrantes,
    con la lista de quien, cuanto y por que es sobrante.

    LAS TRES CONDICIONES, Y LAS TRES SE COMPRUEBAN AQUI:

        1. la oferta esta VIVA          `cash_kind == OFERTA_VIVA`
        2. el jugador SOBRA             esta en `sale_order.queue`
        3. el conjunto pasa el once     `validate_sale_set`

    Nunca lanza. Con la cola vacia NO devuelve cero: devuelve que
    no lo sabe. Un cero medido y un cero por no haber mirado no
    son el mismo numero.
    """

    try:
        cola = [
            f
            for f in ((sale_order or {}).get("queue") or [])
            if isinstance(f, dict)
        ]

        if not cola:
            return {
                "available": False,
                "total": None,
                "n": 0,
                "vendedores": [],
                "apartados": [],
                "cola_vacia": True,
                "reason": (
                    "La cola de venta llega vacia: sin saber quien "
                    "sobra no se puede decir cuanta caja es "
                    "realizable, y no se publica un cero que "
                    "parezca medido."
                ),
            }

        vendedores = []
        apartados = []
        total = 0
        vendiendo = []

        for fila in cola:

            # 1. ¿Es caja de verdad?
            if str(fila.get("cash_kind") or "") != CAJA_DE_VERDAD:
                apartados.append(
                    {
                        "id": fila.get("id"),
                        "name": fila.get("name"),
                        "reason": (
                            "No tiene oferta viva: a precio de "
                            "mercado hay que publicarlo y esperar a "
                            "que alguien lo compre, y eso no es caja."
                        ),
                    }
                )
                continue

            importe = safe_int(fila.get("cash_now"))

            if importe <= 0:
                apartados.append(
                    {
                        "id": fila.get("id"),
                        "name": fila.get("name"),
                        "reason": "La oferta viva no trae importe.",
                    }
                )
                continue

            # 3. ¿Aguanta el once vendiendo a este ADEMAS de a los
            #    que ya van? Se valida el CONJUNTO, no la ficha.
            comprobacion = validador(
                guardarrail,
                vendiendo + [fila.get("id")],
            )

            if not comprobacion.get("ok"):
                apartados.append(
                    {
                        "id": fila.get("id"),
                        "name": fila.get("name"),
                        "reason": comprobacion.get("reason"),
                    }
                )
                continue

            vendiendo.append(fila.get("id"))
            total += importe

            vendedores.append(
                {
                    "id": fila.get("id"),
                    "name": fila.get("name"),
                    "position": fila.get("position"),
                    "cash_now": importe,
                    "price": safe_int(fila.get("price")),
                    "in_lineup": bool(fila.get("in_lineup")),
                    "points": safe_int(fila.get("points")),

                    # LO QUE APORTA POR JORNADA, SI SE SABE
                    #
                    #     Es lo que resta del once al venderlo, y
                    #     sin esto la tabla de fichajes no puede
                    #     hacer la resta y publica un hueco. No se
                    #     calcula aqui -la cola no trae partidos
                    #     jugados-: viaja si quien monta la cola lo
                    #     pone, y si no, la tabla lo dice.
                    "points_per_matchday": fila.get(
                        "points_per_matchday"
                    ),

                    # POR QUE SOBRA. Sin esto la lista es una lista
                    # de nombres y nadie puede discutirla.
                    "tier": fila.get("tier"),
                    "tier_label": fila.get("tier_label"),
                    "reason": fila.get("reason"),
                }
            )

        return {
            "available": True,
            "total": total,
            "n": len(vendedores),
            "vendedores": vendedores,
            "apartados": apartados,
            "cola_vacia": False,
            "reason": (
                f"{len(vendedores)} de {len(cola)} de la cola tienen "
                f"oferta viva y caben sin romper el once: "
                f"{_miles(total)} EUR. Los otros "
                f"{len(apartados)} salen con su motivo."
            ),
        }

    except Exception as error:                      # noqa: BLE001
        return {
            "available": False,
            "total": None,
            "n": 0,
            "vendedores": [],
            "apartados": [],
            "cola_vacia": True,
            "reason": (
                f"No se pudo calcular la caja realizable: "
                f"{type(error).__name__}: {error}"
            ),
        }


def presupuesto_con_el_cable(
    acquisition_budget: dict | None,
    sale_order: dict | None,
    *,
    guardarrail: dict | None,
    validador,
) -> dict:
    """
    Las dos cajas, con nombre cada una, y los dos techos.

    NUNCA DEVUELVE LA SUMA. No hay ningun campo que valga
    `caja_ahora + caja_realizable`, y hay guardia que lo lee del
    JSON publicado para comprobarlo. Un solo numero es lo que
    hace falta para que alguien acabe pujando contra dinero que
    no ha cobrado.

    Nunca lanza.
    """

    try:
        presupuesto = acquisition_budget or {}

        ahora = safe_int(
            presupuesto.get("available_budget")
            if presupuesto.get("available_budget") is not None
            else presupuesto.get("total_budget")
        )

        techo = safe_int(presupuesto.get("maximum_bid"))

        realizable = caja_realizable(
            sale_order,
            guardarrail=guardarrail,
            validador=validador,
        )

        techo_despues = techo

        for vendedor in realizable["vendedores"]:
            # La aritmetica del 25 %: entra el importe, sale un
            # cuarto del precio. Vive en `la_plaza_y_el_cable`
            # para que no haya dos versiones de la misma cuenta.
            techo_despues = techo_tras_vender(
                techo_despues,
                vendedor["cash_now"],
                vendedor["price"],
            )

        return {
            "available": True,
            "observer_only": True,
            "enabled": bool(ENCENDIDO),

            # LAS DOS CAJAS, CON SU NOMBRE. Nunca sumadas.
            "caja_ahora": ahora,
            "caja_ahora_label": (
                "lo que Pepe puede comprometer hoy"
            ),

            "caja_realizable": realizable["total"],
            "caja_realizable_label": (
                "lo que entraria cobrando ofertas vivas, y que NO "
                "se puede comprometer hasta cobrarla"
            ),
            "caja_realizable_n": realizable["n"],
            "vendedores": realizable["vendedores"],
            "apartados": realizable["apartados"],

            "techo_ahora": techo,
            "techo_si_se_vende": techo_despues,

            "cola_vacia": realizable["cola_vacia"],

            # La regla, publicada al lado de los numeros para que
            # quien lea el JSON la vea sin abrir el codigo.
            "regla": (
                "Ninguna puja se pone contra la caja realizable. "
                "La operacion que la necesite se marca "
                "`needs_sale_first` y la venta va primero."
            ),

            "reason": (
                f"Hoy se puede comprometer {_miles(ahora)} EUR. "
                + (
                    f"Cobrando las {realizable['n']} ofertas vivas "
                    f"sobre sobrantes entrarian "
                    f"{_miles(realizable['total'])} EUR mas, y el "
                    f"techo de Biwenger pasaria de {_miles(techo)} a "
                    f"{_miles(techo_despues)}. Ese segundo numero no "
                    "es gastable hasta que la venta este cobrada."
                    if realizable["available"]
                    else realizable["reason"]
                )
            ),
        }

    except Exception as error:                      # noqa: BLE001
        return {
            "available": False,
            "observer_only": True,
            "caja_ahora": 0,
            "caja_realizable": None,
            "caja_realizable_n": 0,
            "vendedores": [],
            "apartados": [],
            "reason": (
                f"No se pudo tender el cable: "
                f"{type(error).__name__}: {error}"
            ),
        }


# ============================================================
# BLOQUE 0 — LA PUERTA QUE IMPIDE PUJAR CONTRA LO NO COBRADO
# ============================================================


def puja_permitida(
    importe,
    presupuesto: dict | None,
) -> dict:
    """
    ¿Se puede comprometer este importe HOY?

    La unica respuesta que abre la puerta es que quepa en
    `caja_ahora`. La caja realizable no abre nada: marca
    `needs_sale_first` y dice a quien hay que vender primero.

    Nunca lanza, y ante la duda cierra: sin presupuesto conocido
    no se puja.
    """

    try:
        datos = presupuesto or {}

        cantidad = safe_int(importe)

        ahora = safe_int(datos.get("caja_ahora"))

        realizable = datos.get("caja_realizable")

        if cantidad <= 0:
            return {
                "ok": False,
                "needs_sale_first": False,
                "vende_primero": [],
                "reason": "Una puja de cero o menos no es una puja.",
            }

        if cantidad <= ahora:
            return {
                "ok": True,
                "needs_sale_first": False,
                "vende_primero": [],
                "budget_used": "CAJA_AHORA",
                "reason": (
                    f"{_miles(cantidad)} EUR caben en los "
                    f"{_miles(ahora)} que hay cobrados."
                ),
            }

        # NO CABE. Aqui es donde la version peligrosa diria que si
        # sumando la caja realizable. No se suma: se manda vender.
        vendedores = list(datos.get("vendedores") or [])

        falta = cantidad - ahora

        plan = []
        acumulado = 0

        for vendedor in vendedores:
            if acumulado >= falta:
                break

            plan.append(vendedor)
            acumulado += safe_int(vendedor.get("cash_now"))

        alcanza = acumulado >= falta

        return {
            "ok": False,
            "needs_sale_first": bool(plan) and alcanza,
            "vende_primero": plan,
            "budget_used": None,
            "falta": falta,
            "cubre_vendiendo": acumulado if plan else 0,
            "reason": (
                (
                    f"{_miles(cantidad)} EUR no caben en los "
                    f"{_miles(ahora)} cobrados. Faltan "
                    f"{_miles(falta)}"
                    + (
                        ", y se cubren vendiendo a "
                        + ", ".join(
                            str(v.get("name")) for v in plan
                        )
                        + f" ({_miles(acumulado)} EUR). LA VENTA VA "
                        "PRIMERO: hasta que este cobrada, esa caja "
                        "no se compromete."
                        if alcanza
                        else (
                            " y no se cubren ni vendiendo a todos "
                            "los que sobran"
                            + (
                                f" ({_miles(acumulado)} EUR)."
                                if plan
                                else (
                                    " — no hay caja realizable que "
                                    "contar."
                                    if realizable is None
                                    else "."
                                )
                            )
                        )
                    )
                )
            ),
        }

    except Exception as error:                      # noqa: BLE001
        return {
            "ok": False,
            "needs_sale_first": False,
            "vende_primero": [],
            "reason": (
                f"No se pudo comprobar la puja, asi que no se puja: "
                f"{type(error).__name__}: {error}"
            ),
        }


# ============================================================
# BLOQUE 2 — LA TABLA DE FICHAJES
# ============================================================


def _puntos_por_jornada_con_vara(puntos, posicion, factor_de) -> float:
    """
    Lo que una plaza aporta por jornada, con la vara puesta.

    `factor_de` entra por argumento: las guardias no pueden
    depender del entorno ni de `BORDALAS_VARA_PLANA`.
    """

    return float(puntos or 0) * float(factor_de(posicion))


def tabla_de_fichajes(
    candidatos: list | None,
    presupuesto: dict | None,
    *,
    factor_de,
    fichas_libres=None,
    jornadas_restantes: int = 0,
) -> dict:
    """
    Para cada candidato: cuesta, a quien hay que vender, cuanto
    da, si cabe la ficha, puntos netos del once con la vara y que
    queda de caja despues.

    Ordenada por PUNTOS NETOS POR EURO GASTADO. Doctrina 62: con
    las plazas llenas manda el punto por plaza, y aqui lo que se
    compara son operaciones enteras -lo que entra menos lo que
    sale- por el dinero que cuestan.

    Nunca lanza.
    """

    try:
        filas = [c for c in (candidatos or []) if isinstance(c, dict)]

        if not filas:
            return {
                "available": False,
                "n": 0,
                "operaciones": [],
                "reason": (
                    "La lista de candidatos llega vacia: no hay "
                    "operacion que montar."
                ),
            }

        datos = presupuesto or {}

        ahora = safe_int(datos.get("caja_ahora"))
        vendedores = list(datos.get("vendedores") or [])

        libres = (
            safe_int(fichas_libres) if fichas_libres is not None else None
        )

        jornadas = safe_int(jornadas_restantes)

        operaciones = []

        for candidato in filas:

            coste = safe_int(candidato.get("market_price"))

            permiso = puja_permitida(coste, datos)

            plan = list(permiso.get("vende_primero") or [])

            entra_caja = sum(
                safe_int(v.get("cash_now")) for v in plan
            )

            # ¿CABE LA FICHA? Con hueco libre no sale nadie por la
            # plaza. Sin hueco, entra uno y sale otro — y el que
            # sale es uno de los del plan de venta.
            hay_hueco = libres is not None and libres > 0

            cabe = bool(hay_hueco or plan)

            # LOS PUNTOS NETOS DEL ONCE, CON LA VARA
            #
            #     El que entra aporta su plaza. Los que salen solo
            #     restan si estaban EN EL ONCE: vender a un
            #     suplente no le quita un punto al equipo.
            restantes = candidato.get("season_points_remaining")

            por_jornada = (
                (float(restantes) / jornadas)
                if restantes is not None and jornadas > 0
                else None
            )

            entran = (
                _puntos_por_jornada_con_vara(
                    por_jornada, candidato.get("position"), factor_de
                )
                if por_jornada is not None
                else None
            )

            salen = 0.0
            salen_medibles = True

            for vendedor in plan:
                if not vendedor.get("in_lineup"):
                    continue

                puntos = vendedor.get("points_per_matchday")

                if puntos is None:
                    salen_medibles = False
                    continue

                salen += _puntos_por_jornada_con_vara(
                    puntos, vendedor.get("position"), factor_de
                )

            medible = entran is not None and salen_medibles

            netos = round(entran - salen, 3) if medible else None

            # PUNTOS NETOS POR EURO. Se publica por millon para
            # que se pueda leer sin contar ceros.
            por_millon = (
                round(netos / (coste / 1_000_000), 4)
                if medible and coste > 0
                else None
            )

            # Y SI NO CABE POR FICHAS, QUE LO DIGA CON ESE MOTIVO
            # Y NO CON OTRO.
            if not cabe:
                motivo = (
                    f"No cabe la ficha: hay {libres if libres is not None else '?'} "
                    "libres y no hay a quien vender sin romper el "
                    "once. No es que falte dinero."
                )

            elif permiso["ok"]:
                motivo = permiso["reason"]

            else:
                motivo = permiso["reason"]

            operaciones.append(
                {
                    "id": candidato.get("id"),
                    "name": candidato.get("name"),
                    "position": candidato.get("position"),
                    "market_price": coste,

                    "blocked_by": candidato.get("blocked_by"),

                    "cabe_la_ficha": cabe,
                    "cabe_sin_vender": hay_hueco,
                    "free_slots": libres,

                    "vende_a": plan,
                    "caja_que_entra": entra_caja,
                    "caja_ahora": ahora,
                    "caja_despues": ahora + entra_caja - coste,

                    # LA REGLA DE SEGURIDAD, FILA A FILA.
                    "needs_sale_first": bool(
                        permiso.get("needs_sale_first")
                    ),
                    "financiada_hoy": bool(permiso.get("ok")),

                    "puntos_por_jornada": (
                        round(por_jornada, 3)
                        if por_jornada is not None
                        else None
                    ),
                    "puntos_que_entran": (
                        round(entran, 3) if entran is not None else None
                    ),
                    "puntos_que_salen": round(salen, 3),
                    "puntos_netos": netos,
                    "puntos_netos_por_millon": por_millon,
                    "vara_puesta": True,

                    "reason": motivo,
                }
            )

        # El orden: puntos netos por euro. Las que no se pueden
        # medir van al final —no se les inventa un cero— y entre
        # ellas por coste, que es lo unico que se sabe.
        operaciones.sort(
            key=lambda o: (
                o["puntos_netos_por_millon"] is None,
                -(o["puntos_netos_por_millon"] or 0),
                o["market_price"],
            )
        )

        for orden, operacion in enumerate(operaciones, start=1):
            operacion["order"] = orden

        medibles = sum(
            1
            for o in operaciones
            if o["puntos_netos_por_millon"] is not None
        )

        return {
            "available": True,
            "n": len(operaciones),
            "medibles": medibles,
            "operaciones": operaciones,
            "orden": "PUNTOS_NETOS_POR_EURO",
            "reason": (
                f"{len(operaciones)} candidatos, {medibles} con "
                f"puntos netos medibles, ordenados por puntos netos "
                f"por millon gastado."
            ),
        }

    except Exception as error:                      # noqa: BLE001
        return {
            "available": False,
            "n": 0,
            "operaciones": [],
            "reason": (
                f"No se pudo montar la tabla: "
                f"{type(error).__name__}: {error}"
            ),
        }


# ============================================================
# BLOQUE 3 — LA COLA POR CONSECUENCIA
# ============================================================
#
#     DOCTRINA 64. Hoy la cola se ordena por `priority`, y esa
#     tabla mezcla dos cosas distintas: lo que urge y lo que
#     importa. En la foto del 17/09:
#
#         RENEW_MARKET_LISTING   690   caduca en 2,85 h   desbloquea nada
#         ACCEPT_RECOVERY_OFFER  650   caduca en 47,5 h   desbloquea todo
#
#     Lo que desbloquea cada accion NO se deduce: se declara, y
#     se declara aqui para que se pueda discutir mirando una
#     lista y no leyendo seis modulos.

QUE_DESBLOQUEA = {
    # Cobrar una oferta mete caja. Con el saldo en rojo, esa caja
    # es lo que abre `acquisition_budget`, el carril y la
    # subasta: las tres estan hoy en cero por lo mismo.
    "ACCEPT_RECOVERY_OFFER": (
        3,
        "Mete caja: con el saldo en rojo es lo que abre el "
        "presupuesto de fichar, el carril y la subasta.",
    ),
    "ACCEPT_BEFORE_EXPIRY": (
        3,
        "Mete caja: misma cadena que cobrar una oferta aprobada.",
    ),
    "SELL_PLAYER": (
        3,
        "Mete caja y libera una ficha.",
    ),

    # Publicar abre la puerta a que el Computer ofrezca. No mete
    # caja hoy, pero es condicion de la de mañana.
    "LIST_FOR_LIQUIDITY": (
        2,
        "Sin publicar no llega oferta: es la condicion de la caja "
        "de mañana, no de la de hoy.",
    ),

    # Alinear no desbloquea nada, pero perderlo cuesta la
    # jornada entera. Va por su propia via, no por esta.
    "SAVE_LINEUP": (
        1,
        "No desbloquea otras acciones, pero perderlo cuesta la "
        "jornada entera.",
    ),

    # Renovar mantiene viva una publicacion que ya existe. Evita
    # perder algo; no abre nada.
    "RENEW_MARKET_LISTING": (
        0,
        "Mantiene viva una publicacion que ya existe: evita "
        "perder algo, no abre nada.",
    ),
    "REROLL_COMPUTER_OFFER": (
        0,
        "Cambia una oferta por otra: no abre ninguna via nueva.",
    ),
    "BUY_SPECULATION": (
        0,
        "Inmoviliza caja en vez de liberarla.",
    ),
    "MONITOR_OFFERS": (0, "No escribe."),
    "MONITOR_SOLVENCY": (0, "No escribe."),
    "WAIT": (0, "No escribe."),
}


# Cuanto margen se le exige a la accion que se deja para la
# vuelta siguiente. Dos veces la espera: si la cuenta va justa,
# no se adelanta a nadie.
MARGEN_DE_SEGURIDAD = 2.0


def cuanto_desbloquea(accion) -> tuple:
    """
    Cuanto abre esta accion, y por que. Una accion desconocida
    abre CERO: no se le supone una consecuencia que nadie ha
    escrito.
    """

    return QUE_DESBLOQUEA.get(
        str(accion or "").upper(),
        (0, "Accion sin consecuencia declarada: se cuenta como que no abre nada."),
    )


def cola_por_consecuencia(
    candidatos: list | None,
    *,
    intervalo_de_ciclo_horas: float,
    duracion_de_ciclo_horas: float,
    margen: float = MARGEN_DE_SEGURIDAD,
) -> dict:
    """
    Reordena la cola por consecuencia SIN dejar caducar nada.

    LA REGLA, ENTERA:

        una accion que desbloquea a otras se adelanta a una que
        solo evita perder algo, PERO SOLO SI la que se queda
        atras sobrevive a la espera.

    LA ESPERA SE MIDE, NO SE SUPONE. Solo hay una escritura por
    vuelta, asi que lo que se aplaza no se hace dentro de un
    minuto: se hace en la vuelta siguiente. Eso es
    `intervalo_de_cron + duracion_del_ciclo`, y las dos entran
    por argumento: aqui no se mira ningun reloj.

    Si chocan, GANA NO PERDER, y se dice.

    Nunca lanza.
    """

    try:
        filas = [c for c in (candidatos or []) if isinstance(c, dict)]

        ejecutables = [
            c for c in filas if bool(c.get("executable", False))
        ]

        if not ejecutables:
            return {
                "available": False,
                "n": 0,
                "cola": [],
                "cambia": False,
                "reason": (
                    "Ninguna accion ejecutable: no hay cola que "
                    "ordenar."
                ),
            }

        espera = (
            float(intervalo_de_ciclo_horas)
            + float(duracion_de_ciclo_horas)
        )

        umbral = espera * float(margen)

        enriquecidos = []

        for candidato in ejecutables:

            abre, porque = cuanto_desbloquea(candidato.get("action"))

            horas = candidato.get("hours_to_expiry")

            # Sin plazo conocido se trata como que NO sobrevive:
            # ante la duda, no se aplaza.
            sobrevive = (
                float(horas) > umbral if horas is not None else False
            )

            enriquecidos.append(
                {
                    **candidato,
                    "desbloquea": abre,
                    "desbloquea_reason": porque,
                    "hours_to_expiry": horas,
                    "sobrevive_una_vuelta": sobrevive,
                    "umbral_horas": round(umbral, 3),
                }
            )

        por_prioridad = sorted(
            enriquecidos,
            key=lambda c: -safe_int(c.get("priority")),
        )

        # EL ORDEN NUEVO
        #
        #     Primero lo que NO sobrevive a la espera -da igual lo
        #     que abra: perderlo es perderlo-. Dentro de ese
        #     grupo, y dentro del otro, manda lo que mas
        #     desbloquea, y a igualdad la prioridad de siempre.
        por_consecuencia = sorted(
            enriquecidos,
            key=lambda c: (
                c["sobrevive_una_vuelta"],
                -c["desbloquea"],
                -safe_int(c.get("priority")),
            ),
        )

        cambia = [c.get("action") for c in por_prioridad] != [
            c.get("action") for c in por_consecuencia
        ]

        primera_vieja = por_prioridad[0]
        primera_nueva = por_consecuencia[0]

        # QUE SE APLAZA Y SI LLEGA. La parte del encargo que pide
        # ver el choque dicho, no solo resuelto.
        aplazadas = [
            {
                "action": c.get("action"),
                "label": c.get("label"),
                "hours_to_expiry": c.get("hours_to_expiry"),
                "sobrevive_una_vuelta": c["sobrevive_una_vuelta"],
                "umbral_horas": c["umbral_horas"],
            }
            for c in por_consecuencia[1:]
            if c.get("action") != primera_vieja.get("action")
            or primera_vieja.get("action") != primera_nueva.get("action")
        ]

        # Y el choque explicito: alguien que no sobrevive y que
        # ademas no abre nada se queda delante igualmente.
        choque = [
            c
            for c in por_consecuencia
            if not c["sobrevive_una_vuelta"] and c["desbloquea"] == 0
        ]

        return {
            "available": True,
            "n": len(por_consecuencia),
            "cola": por_consecuencia,
            "cambia": cambia,

            "espera_horas": round(espera, 3),
            "umbral_horas": round(umbral, 3),
            "margen": float(margen),

            "primera_por_caducidad": {
                "action": primera_vieja.get("action"),
                "label": primera_vieja.get("label"),
                "priority": primera_vieja.get("priority"),
                "desbloquea": primera_vieja["desbloquea"],
            },
            "primera_por_consecuencia": {
                "action": primera_nueva.get("action"),
                "label": primera_nueva.get("label"),
                "priority": primera_nueva.get("priority"),
                "desbloquea": primera_nueva["desbloquea"],
            },

            "aplazadas": aplazadas,
            "gana_no_perder": [
                {
                    "action": c.get("action"),
                    "hours_to_expiry": c.get("hours_to_expiry"),
                }
                for c in choque
            ],

            "reason": (
                (
                    f"Por caducidad iria "
                    f"{primera_vieja.get('action')}; por "
                    f"consecuencia va {primera_nueva.get('action')}, "
                    f"que desbloquea {primera_nueva['desbloquea']} "
                    f"contra {primera_vieja['desbloquea']}. "
                    f"Lo aplazado aguanta porque le quedan "
                    f"{primera_vieja.get('hours_to_expiry')} h y el "
                    f"umbral son {round(umbral, 2)} h "
                    f"({round(espera, 2)} h de espera x {margen})."
                    if cambia
                    else (
                        "El orden no cambia: "
                        + (
                            "lo que iria primero ya es lo que mas "
                            "desbloquea."
                            if primera_nueva["desbloquea"]
                            >= primera_vieja["desbloquea"]
                            else (
                                "lo que mas desbloquea no puede "
                                "adelantarse porque lo de delante no "
                                "sobrevive a la espera. Gana no "
                                "perder."
                            )
                        )
                    )
                )
            ),
        }

    except Exception as error:                      # noqa: BLE001
        return {
            "available": False,
            "n": 0,
            "cola": [],
            "cambia": False,
            "reason": (
                f"No se pudo ordenar por consecuencia: "
                f"{type(error).__name__}: {error}"
            ),
        }


# ============================================================
# BLOQUE 4 — LA PLANTILLA MAS GRANDE JAMAS VISTA
# ============================================================
#
#     `count_free_slots` compara contra la plantilla mas grande
#     DE HOY. En la foto del 17/09 eso da 20 - 20 = 0 huecos, y
#     nosotros mismos llegamos a tener 21 el 15/09.
#
#     Una plaza que creemos que no existe es una plaza que no
#     usamos.
#
# EL REPARTO INICIAL NO ES EL QUE DICE EL TABLON
#
#     El evento `leagueReset` declara `distribution: 12`. Con 12,
#     la reconstruccion sale -3 en SIETE de los ocho managers y
#     -4 en el octavo: un sesgo, no ruido.
#
#     Con 15 cuadran SIETE de ocho AL CERO, y el octavo -Pollo17-
#     falla por -1, que es exactamente su unico jugador sin
#     explicar en el ledger. Asi que el reparto se AJUSTA en vez
#     de creerse, y el ajuste se publica con su cuadre.

# Lo que mueve una ficha de una plantilla a otra.
ENTRA = "market"
SALE = "transfer"


def mayor_plantilla_jamas_vista(
    board_events: list | None,
    tamanos_de_hoy: dict | None,
    *,
    sin_explicar: dict | None = None,
    repartos_a_probar=range(8, 26),
) -> dict:
    """
    El tamaño maximo de plantilla que se ha llegado a ver en esta
    liga, reconstruido desde el tablon y CON SU PROPIO CUADRE.

    COMO SE LEE EL RESULTADO

        `trusted` es lo unico que importa. Solo es True si NUESTRA
        linea reconstruida coincide exactamente con la de hoy: es
        la unica que podemos comprobar, y si no cuadra la nuestra
        no hay razon para creerse las demas.

        `largest_ever` es siempre una COTA INFERIOR. Al tablon le
        faltan operaciones -los managers con jugadores sin
        explicar lo demuestran-, y todo lo que falta son compras,
        asi que el maximo real es ese o mayor. Nunca menor.

    EL TABLON REPITE OPERACIONES (medido el 10/09): los
    `event_id` son unicos pero la misma compra sale dentro de
    eventos distintos. Se dedupe por la OPERACION.

    Nunca lanza.
    """

    try:
        eventos = [
            e for e in (board_events or []) if isinstance(e, dict)
        ]

        hoy = {
            str(nombre): safe_int(tamano)
            for nombre, tamano in (tamanos_de_hoy or {}).items()
        }

        if not eventos or not hoy:
            return {
                "available": False,
                "trusted": False,
                "largest_ever": None,
                "is_lower_bound": True,
                "reason": (
                    "Sin tablon o sin tamaños de hoy no hay nada que "
                    "reconstruir, y un maximo inventado abriria una "
                    "plaza que no existe."
                ),
            }

        operaciones = []
        vistas = set()
        brutas = 0

        for evento in sorted(eventos, key=lambda e: e.get("date") or 0):

            if evento.get("type") not in (ENTRA, SALE):
                continue

            for fila in evento.get("content") or []:

                if not isinstance(fila, dict):
                    continue

                brutas += 1

                hacia = (fila.get("to") or {}).get("id")
                desde = (fila.get("from") or {}).get("id")

                clave = (
                    evento["type"],
                    fila.get("player"),
                    fila.get("amount"),
                    hacia,
                    desde,
                )

                if clave in vistas:
                    continue

                vistas.add(clave)

                operaciones.append(
                    {
                        "date": evento.get("date"),
                        "to": hacia,
                        "from": desde,
                        "to_name": (fila.get("to") or {}).get("name"),
                        "from_name": (fila.get("from") or {}).get("name"),
                    }
                )

        managers = {}

        for operacion in operaciones:
            for lado, nombre in (("to", "to_name"), ("from", "from_name")):
                identificador = operacion[lado]

                if identificador and operacion[nombre] in hoy:
                    managers[identificador] = operacion[nombre]

        if not managers:
            return {
                "available": False,
                "trusted": False,
                "largest_ever": None,
                "is_lower_bound": True,
                "reason": (
                    "Ninguno de los managers del tablon coincide con "
                    "los de hoy: no se puede cuadrar nada."
                ),
            }

        def recorrer(inicial):
            tamano = {u: inicial for u in managers}
            maximo = dict(tamano)
            cuando = {}

            for operacion in operaciones:
                if operacion["to"] in tamano:
                    tamano[operacion["to"]] += 1
                if operacion["from"] in tamano:
                    tamano[operacion["from"]] -= 1

                for u in tamano:
                    if tamano[u] > maximo[u]:
                        maximo[u] = tamano[u]
                        cuando[u] = operacion["date"]

            return tamano, maximo, cuando

        # EL REPARTO SE AJUSTA: se prueba cada tamaño inicial y se
        # queda el que hace cuadrar mas lineas. No se cree al
        # `distribution` del tablon, que sale -3 en siete de ocho.
        mejor = None

        for inicial in repartos_a_probar:
            tamano, maximo, cuando = recorrer(inicial)

            exactas = sum(
                1
                for u, nombre in managers.items()
                if tamano[u] == hoy[nombre]
            )

            if mejor is None or exactas > mejor[0]:
                mejor = (exactas, inicial, tamano, maximo, cuando)

        exactas, inicial, tamano, maximo, cuando = mejor

        # EL CUADRE QUE DECIDE: el nuestro. Es la unica linea que
        # sabemos de primera mano.
        nuestro = next(
            (
                u
                for u, nombre in managers.items()
                if (sin_explicar or {}).get("is_us_name") == nombre
            ),
            None,
        )

        nombre_nuestro = (sin_explicar or {}).get("is_us_name")

        cuadra_el_nuestro = (
            nombre_nuestro is not None
            and nuestro is not None
            and tamano[nuestro] == hoy[nombre_nuestro]
        )

        mayor = max(maximo.values())
        mayor_hoy = max(hoy.values())

        return {
            "available": True,

            # SOLO SE USA SI CUADRA EL NUESTRO.
            "trusted": bool(cuadra_el_nuestro),

            "largest_ever": mayor,
            "largest_today": mayor_hoy,

            # Y SIEMPRE, PASE LO QUE PASE: esto es un suelo.
            "is_lower_bound": True,

            "initial_squad_fitted": inicial,
            "reconciled": exactas,
            "managers": len(managers),
            "operations": len(operaciones),
            "operations_raw": brutas,

            "by_manager": [
                {
                    "name": nombre,
                    "today": hoy[nombre],
                    "reconstructed": tamano[u],
                    "diff": tamano[u] - hoy[nombre],
                    "max_ever": maximo[u],
                    "max_at": cuando.get(u),
                    "unexplained": safe_int(
                        ((sin_explicar or {}).get("by_manager") or {}).get(
                            nombre
                        )
                    ),
                }
                for u, nombre in sorted(
                    managers.items(), key=lambda x: -maximo[x[0]]
                )
            ],

            "reason": (
                f"Reparto inicial ajustado a {inicial} fichas: cuadran "
                f"{exactas} de {len(managers)} plantillas al cero. "
                f"La mayor jamas reconstruida son {mayor} fichas, "
                f"contra {mayor_hoy} hoy. Es una COTA INFERIOR: al "
                f"tablon le faltan operaciones y todas las que "
                f"faltan son compras, asi que el tope real es ese o "
                f"mayor, nunca menor."
                + (
                    ""
                    if cuadra_el_nuestro
                    else " NUESTRA linea NO cuadra, asi que este "
                    "numero no se usa para abrir ninguna plaza."
                )
            ),
        }

    except Exception as error:                      # noqa: BLE001
        return {
            "available": False,
            "trusted": False,
            "largest_ever": None,
            "is_lower_bound": True,
            "reason": (
                f"No se pudo reconstruir el maximo historico: "
                f"{type(error).__name__}: {error}"
            ),
        }


def maximo_historico_de_fichas(ledger_audit: dict | None) -> dict:
    """
    El maximo historico leyendo el tablon del disco.

    VIVE AQUI Y NO EN CADA LLAMANTE por la misma razon que
    `budget_for_intent`: produccion y dashboard no pueden
    contestar distinto a la misma pregunta. Ese es exactamente el
    fallo que el 16/08 puso cuatro pujas en pantalla y una viva en
    Biwenger.

    Lee disco, asi que NINGUNA GUARDIA lo llama: las guardias
    prueban `mayor_plantilla_jamas_vista`, que es pura y come
    fixtures.

    Nunca lanza.
    """

    try:
        from src.analysis.computer_resale_premium import (
            load_board_events,
        )

        managers = [
            m
            for m in ((ledger_audit or {}).get("by_manager") or [])
            if isinstance(m, dict) and safe_int(m.get("roster_size")) > 0
        ]

        if not managers:
            return {
                "available": False,
                "trusted": False,
                "largest_ever": None,
                "is_lower_bound": True,
                "reason": (
                    "El ledger no trae plantillas: no hay contra que "
                    "cuadrar la reconstruccion."
                ),
            }

        nosotros = next((m for m in managers if m.get("is_us")), None)

        return mayor_plantilla_jamas_vista(
            load_board_events(),
            {m.get("name"): m.get("roster_size") for m in managers},
            sin_explicar={
                "is_us_name": (nosotros or {}).get("name"),
                "by_manager": {
                    m.get("name"): len(m.get("unexplained") or [])
                    for m in managers
                },
            },
        )

    except Exception as error:                      # noqa: BLE001
        return {
            "available": False,
            "trusted": False,
            "largest_ever": None,
            "is_lower_bound": True,
            "reason": (
                f"No se pudo leer el tablon: "
                f"{type(error).__name__}: {error}"
            ),
        }
