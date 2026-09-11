"""
La rendija: el carril propio de las pujas de revender.

POR QUE UN CARRIL Y NO UN SITIO EN LA COLA

    `decision_orchestrator` elige UNA accion por vuelta, la de
    mas prioridad, y `SPECULATION_BUY` esta en 400: la ultima de
    la fila. Eso esta BIEN y no se discute — el once gana al
    dinero, y el dinero gana a especular.

    Pero la cola existe para elegir la mejor accion cuando las
    acciones son ESCASAS y CARAS. Una puja de revender no es
    ninguna de las dos cosas:

        · PERDERLA NO CUESTA NADA. Esta medido: todas las pujas
          se resuelven en el reset de las 07:00 y las pujas de
          los rivales son invisibles. No hay nada que reservar.

        · CUESTA CENTIMOS DE PETICIONES. Una puja es un POST.
          El ciclo entero son 7.

    Asi que no compite por el hueco de la vuelta: se ejecuta
    DESPUES de la accion principal, con presupuesto propio y
    pequeno.

LO QUE ESTE CARRIL NO EXIGE

    LA VENTANA. Las pujas de revender se pueden colocar a
    cualquier hora. El motivo esta medido: todas se resuelven en
    el reset y las de los rivales no se ven, asi que pujar tarde
    no nos esconde de nadie. La ventana no aportaba NADA para
    pujar — era una creencia nuestra, no una mecanica del juego.

    LA COMPUERTA DE RITMO, para el cupo de abajo.

LO QUE SE QUEDA, SIN EXCEPCION

    · LA ZONA DE SILENCIO. No se escribe nada mientras el
      mercado se resuelve. Se usa la que ya hay -04:45 a 07:00
      de Madrid-, que cubre de sobra el 05:00-07:00 pedido. No
      se mueve ningun umbral.

    · EL CUPO POR CICLO DE RESET, de 07:00 a 07:00. Al no
      haber ventana, el cupo necesitaba una unidad: esa.
      Empieza en DOS y sube a cuatro solo cuando se cierre un
      viaje entero. Vive en  y en ningun
      otro sitio.

    · DOS ESCRITURAS DE ESTE CARRIL POR VUELTA.

    · NI UNA SI LA ACCION PRINCIPAL FUE UNA EMERGENCIA. Si hay
      emergencia, el carril se calla esa vuelta.

    · El importe que dice la curva, el tope por operacion,
      `MAX_SINGLE_SPECULATION_PERCENT`, las fichas libres, las
      barandillas sobre el peor caso -que se ganen las cuatro-,
      la deuda y el reloj de solvencia. NINGUN umbral se mueve:
      esto no los toca, solo decide si el carril abre.

SE APAGA SOLA

    Tras 10 viajes cerrados, si la mediana del resultado es
    negativa, la rendija se cierra y sale en ROJO en la portada.
    No hace falta que nadie se acuerde de mirarla.
"""

from __future__ import annotations

import statistics

from datetime import datetime, timezone


# ============================================================
# LOS TOPES DEL CARRIL
# ============================================================

# Por vuelta. Dos es lo que cabe sin que el carril se note en el
# consumo: son 2 POST sobre una vuelta de 7 peticiones.
ESCRITURAS_POR_VUELTA = 2

# ============================================================
# EL CUPO, Y POR QUE HAY DOS
# ============================================================
#
# Por ciclo de reset, de 07:00 a 07:00.
#
# SE EMPIEZA POR DOS, NO POR CUATRO
#
#     Hasta que no se cierre UN viaje entero -comprado, listado,
#     oferta recibida y cobrada por encima del suelo- no sabemos
#     si la rueda gira. Abrir con cuatro seria comprometer el
#     doble sobre algo que no ha funcionado ni una vez.
#
#     En cuanto pase una vez, sube a cuatro solo.
#
# UN NUMERO EN UN SITIO
#
#     El cupo vigente no se escribe en ningun otro lado: se
#     pregunta a `cupo_del_reset()`, que ademas dice en cual
#     esta y por que, para que la portada lo pinte sin deducir
#     nada.
CUPO_DE_ESTRENO = 2

CUPO_PLENO = 4

# Cuantos viajes cerrados hacen falta antes de juzgar si esto
# merece la pena. Menos que esto es una racha, no una medicion.
VIAJES_PARA_JUZGAR = 10

# La marca que lleva cada operacion de este carril.
MARCA = "RENDIJA"

# Si la accion principal fue una de estas, el carril se calla.
EMERGENCIAS = ("EMERGENCY_", "HARD_SAFETY", "ROUND_LOCK")


def safe_int(value, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def safe_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _euros(valor) -> str:
    try:
        return f"{int(valor):,}".replace(",", ".")
    except (TypeError, ValueError):
        return "?"


# ============================================================
# SE APAGA SOLA
# ============================================================


def se_apaga_sola(cierres: list | None) -> dict:
    """
    ¿Sigue mereciendo la pena la rendija? Forma fija.

    `cierres` son los viajes YA CERRADOS, cada uno con su
    `profit`. Con menos de `VIAJES_PARA_JUZGAR` no se opina: una
    racha de tres no dice nada, y apagar por una racha seria el
    mismo error que montar una regla sobre un caso.
    """

    try:
        resultados = [
            safe_int(c.get("profit"))
            for c in (cierres or [])
            if isinstance(c, dict) and c.get("profit") is not None
        ]

        if len(resultados) < VIAJES_PARA_JUZGAR:
            return {
                "available": True,
                "apagada": False,
                "cerrados": len(resultados),
                "mediana": None,
                "reason": (
                    f"{len(resultados)} viaje(s) cerrado(s) de "
                    f"{VIAJES_PARA_JUZGAR}: aun no hay con que "
                    f"juzgar."
                ),
            }

        mediana = statistics.median(resultados)

        apagada = mediana < 0

        return {
            "available": True,
            "apagada": apagada,
            "cerrados": len(resultados),
            "mediana": mediana,
            "reason": (
                (
                    f"LA RENDIJA SE HA CERRADO SOLA: la mediana "
                    f"de {len(resultados)} viajes cerrados es "
                    f"{_euros(mediana)} EUR. Pierde dinero."
                )
                if apagada
                else (
                    f"Mediana de {len(resultados)} viajes: "
                    f"{_euros(mediana)} EUR."
                )
            ),
        }

    except Exception as error:                      # noqa: BLE001
        return {
            "available": False,
            "apagada": True,
            "cerrados": 0,
            "mediana": None,
            "reason": (
                f"No se pudo juzgar la rendija, asi que se cierra: "
                f"{type(error).__name__}: {error}"
            ),
        }


# ============================================================
# EL CUPO VIGENTE
# ============================================================


def un_viaje_cerrado_entero(cierres: list | None) -> dict:
    """
    ¿Ha dado alguno la vuelta completa? Forma fija.

    "Entero" es: comprado, listado, oferta recibida y COBRADA
    POR ENCIMA DEL SUELO. Un corte de perdidas o un viaje
    caducado NO cuentan: la rueda no ha girado, solo se ha
    parado.
    """

    try:
        for cierre in cierres or []:

            if not isinstance(cierre, dict):
                continue

            beneficio = cierre.get("profit")

            if beneficio is None:
                continue

            if safe_int(beneficio) > 0 and not cierre.get(
                "loss_cut"
            ):
                return {
                    "available": True,
                    "hay": True,
                    "player_name": cierre.get("player_name"),
                    "profit": safe_int(beneficio),
                    "at": cierre.get("at"),
                }

        return {"available": True, "hay": False}

    except Exception:                               # noqa: BLE001
        # Sin saberlo, por el lado prudente: no hay.
        return {"available": False, "hay": False}


def cupo_del_reset(cierres: list | None = None) -> dict:
    """
    Cuantas operaciones caben en este ciclo de reset, y POR QUE.

    ES EL UNICO SITIO DONDE VIVE ESE NUMERO. La portada lo pinta
    de aqui: ni lo deduce ni lo lleva escrito.
    """

    primero = un_viaje_cerrado_entero(cierres)

    if primero.get("hay"):
        return {
            "available": True,
            "cupo": CUPO_PLENO,
            "estado": "PLENO",
            "reason": (
                f"Cupo de {CUPO_PLENO} por ciclo de reset: ya se "
                f"cerro un viaje entero"
                + (
                    f" ({primero.get('player_name')}, "
                    f"+{_euros(primero.get('profit'))} EUR)"
                    if primero.get("player_name")
                    else ""
                )
                + "."
            ),
        }

    return {
        "available": True,
        "cupo": CUPO_DE_ESTRENO,
        "estado": "ESTRENO",
        "reason": (
            f"Cupo de {CUPO_DE_ESTRENO} por ciclo de reset: "
            f"todavia no se ha cerrado ningun viaje entero "
            f"-comprado, listado, oferta recibida y cobrada por "
            f"encima del suelo-. Sube a {CUPO_PLENO} en cuanto "
            f"pase una vez."
        ),
    }


# ============================================================
# EL RITMO DE LOS CANDIDATOS
# ============================================================


def ritmo_de_los_candidatos(
    candidatos: list | None,
    rates: dict | None = None,
) -> dict:
    """
    De lo que el carril compraria: ¿viene SUBIENDO o CAYENDO, y a
    que ritmo? Forma fija, nunca lanza.

    LA COMPUERTA DE RITMO SE QUITO A PROPOSITO. El negocio es el
    spread, no la rampa: se compra al precio del Computer y se
    revende por encima, y para eso da igual hacia donde vaya el
    precio.

    Pero quitarla no es dejar de mirar. El libro en la sombra
    decia que lo que se rechazaba era todo PRECIO_CAYENDO; si lo
    que compramos tambien lo es, el experimento real es "comprar
    caidos y revender", y eso hay que saberlo MIENTRAS PASA, no
    despues.

    ESTO NO DECIDE NADA. Solo cuenta lo que se esta comprando.
    """

    vacio = {
        "available": False,
        "filas": [],
        "subiendo": 0,
        "cayendo": 0,
        "planos": 0,
        "sin_dato": 0,
        "todos_cayendo": False,
        "reason": None,
    }

    try:
        from src.analysis.market_rate_gate import (
            FALLING,
            build_market_rates,
            evaluate,
        )

        ritmos = (
            rates if rates is not None else build_market_rates()
        )

        filas = []

        for candidato in candidatos or []:

            if not isinstance(candidato, dict):
                continue

            pid = safe_int(candidato.get("player_id"))

            visto = evaluate(pid, ritmos)

            ritmo = safe_float(visto.get("rate_percent_per_day"))

            if ritmo is None:
                direccion = "SIN_DATO"

            elif ritmo > 0:
                direccion = "SUBIENDO"

            elif ritmo < 0:
                direccion = FALLING

            else:
                direccion = "PLANO"

            filas.append(
                {
                    "player_id": pid,
                    "name": candidato.get("name"),
                    "position": safe_int(
                        candidato.get("position")
                    ),
                    "market_price": safe_int(
                        candidato.get("market_price")
                    ),
                    "direction": direccion,
                    "rate_percent_per_day": ritmo,
                    "trend_days": visto.get("trend_days"),
                }
            )

        cuenta = {
            "subiendo": sum(
                1 for f in filas if f["direction"] == "SUBIENDO"
            ),
            "cayendo": sum(
                1 for f in filas if f["direction"] == FALLING
            ),
            "planos": sum(
                1 for f in filas if f["direction"] == "PLANO"
            ),
            "sin_dato": sum(
                1 for f in filas if f["direction"] == "SIN_DATO"
            ),
        }

        con_dato = len(filas) - cuenta["sin_dato"]

        todos_cayendo = bool(
            con_dato and cuenta["cayendo"] == con_dato
        )

        return {
            "available": True,
            "filas": filas,
            **cuenta,
            "todos_cayendo": todos_cayendo,
            "reason": (
                f"{len(filas)} candidato(s): "
                f"{cuenta['subiendo']} subiendo, "
                f"{cuenta['cayendo']} cayendo, "
                f"{cuenta['planos']} planos, "
                f"{cuenta['sin_dato']} sin dato."
                + (
                    " TODOS los que traen dato vienen CAYENDO: el "
                    "experimento es «comprar caidos y revender»."
                    if todos_cayendo
                    else ""
                )
            ),
        }

    except Exception as error:                      # noqa: BLE001
        return {
            **vacio,
            "reason": (
                f"No se pudo medir el ritmo de los candidatos: "
                f"{type(error).__name__}: {error}"
            ),
        }



# ============================================================
# EL PERMISO DEL CARRIL
# ============================================================


def permiso(
    ahora: datetime | None = None,
    accion_principal: str | None = None,
    escrituras_en_esta_vuelta: int = 0,
    operaciones_en_este_reset: int = 0,
    cierres: list | None = None,
    en_vivo: bool = False,
) -> dict:
    """
    ¿Puede escribir el carril de la rendija ahora mismo?

    Forma fija, nunca lanza. Cada "no" dice por que, y en este
    orden: apagado, silencio, emergencia, cupo del reset, cupo de
    la vuelta.
    """

    vacio = {
        "available": False,
        "puede": False,
        "quedan_en_la_vuelta": 0,
        "quedan_en_el_reset": 0,
        "blocked_by": None,
        "reason": None,
    }

    try:
        momento = ahora or datetime.now(timezone.utc)

        apagado = se_apaga_sola(cierres)

        cupo = cupo_del_reset(cierres)

        quedan_reset = max(
            0,
            cupo["cupo"]
            - safe_int(operaciones_en_este_reset),
        )

        quedan_vuelta = max(
            0,
            ESCRITURAS_POR_VUELTA
            - safe_int(escrituras_en_esta_vuelta),
        )

        base = {
            "available": True,
            "puede": False,
            "quedan_en_la_vuelta": quedan_vuelta,
            "quedan_en_el_reset": quedan_reset,
            "cupo_por_vuelta": ESCRITURAS_POR_VUELTA,
            "cupo_por_reset": cupo["cupo"],
            "cupo_estado": cupo["estado"],
            "cupo_reason": cupo["reason"],
            "apagado": apagado,
        }

        # 1. ¿SE HA APAGADO SOLA?
        if apagado.get("apagada"):
            return {
                **base,
                "blocked_by": "APAGADA",
                "reason": apagado.get("reason"),
            }

        # 2. LA ZONA DE SILENCIO. La que ya hay, sin tocarla.
        from src.analysis.zona_de_silencio import (
            permite_escribir,
        )

        silencio = permite_escribir(momento)

        if not silencio.get("allowed", True):
            return {
                **base,
                "blocked_by": "SILENCIO",
                "reason": (
                    "Zona de silencio: el mercado se esta "
                    "resolviendo y los datos son de otro mundo. "
                    + str(silencio.get("reason") or "")
                ).strip(),
            }

        # 3. LA EMERGENCIA MANDA. Si la vuelta se fue en una,
        #    el carril se calla: no es momento de comprar para
        #    revender.
        principal = str(accion_principal or "").upper()

        if any(principal.startswith(e) for e in EMERGENCIAS):
            return {
                **base,
                "blocked_by": "EMERGENCIA",
                "reason": (
                    f"La accion principal de esta vuelta fue "
                    f"«{principal}»: con una emergencia encima, "
                    f"el carril no escribe."
                ),
            }

        # 4. EL CUPO DEL RESET, de 07:00 a 07:00.
        if quedan_reset <= 0:
            return {
                **base,
                "blocked_by": "CUPO_DEL_RESET",
                "reason": (
                    f"Ya van {safe_int(operaciones_en_este_reset)} "
                    f"operaciones en este ciclo de reset y el "
                    + cupo["reason"]
                ),
            }

        # 5. EL CUPO DE LA VUELTA.
        if quedan_vuelta <= 0:
            return {
                **base,
                "blocked_by": "CUPO_DE_LA_VUELTA",
                "reason": (
                    f"Ya van {safe_int(escrituras_en_esta_vuelta)} "
                    f"escrituras del carril en esta vuelta y el "
                    f"tope son {ESCRITURAS_POR_VUELTA}."
                ),
            }

        return {
            **base,
            "puede": True,
            "reason": (
                f"El carril puede escribir: quedan "
                f"{quedan_vuelta} en la vuelta y {quedan_reset} "
                f"en este ciclo de reset."
                + ("" if en_vivo else " (NO armado: en seco.)")
            ),
        }

    except Exception as error:                      # noqa: BLE001
        # Si no se sabe si se puede, NO se puede.
        return {
            **vacio,
            "reason": (
                f"No se pudo decidir el permiso del carril, asi "
                f"que no escribe: {type(error).__name__}: {error}"
            ),
        }


# ============================================================
# A QUIEN PREFERIR
# ============================================================


def a_quien_pujar(
    candidatos: list | None,
    cuantos: int | None = None,
) -> dict:
    """
    Los candidatos, EN ORDEN de preferencia, y cuantos caben.

    No es un filtro nuevo: es el orden que sale de lo medido el
    10/09 sobre 34 recompras del Computer —defensas +3,67 %,
    porteros +3,26 %, medios +2,85 %, delanteros +1,80 %— y del
    suelo de ficha: por debajo de 1 M, un +1,52 % sobre 150.000
    son 2.250 EUR y no pagan la ficha.

    `orden_de_preferencia` ya hace ese trabajo y aqui no se
    duplica: se reutiliza, para que el dia que la medicion se
    actualice cambien los dos sitios a la vez.
    """

    try:
        from src.analysis.salida_del_viaje import (
            orden_de_preferencia,
        )

        ordenados = orden_de_preferencia(candidatos)

        tope = (
            cupo_del_reset()["cupo"]
            if cuantos is None
            else max(0, safe_int(cuantos))
        )

        return {
            "available": True,
            "orden": ordenados,
            "elegidos": ordenados[:tope],
            "reason": (
                f"{len(ordenados)} candidato(s) en orden de "
                f"preferencia; caben {tope}."
            ),
        }

    except Exception as error:                      # noqa: BLE001
        return {
            "available": False,
            "orden": [],
            "elegidos": [],
            "reason": (
                f"No se pudo ordenar a los candidatos: "
                f"{type(error).__name__}: {error}"
            ),
        }
