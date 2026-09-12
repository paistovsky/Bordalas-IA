"""
El carril de la rendija, ejecutado. La pieza que faltaba.

QUE PASABA

    12/09/2026. La rendija se encendio el 11 y al dia siguiente
    no habia comprado nada. El panel decia EN VIVO.

    El motivo no era ninguna de las cinco puertas: era que NADIE
    LLAMABA AL CARRIL. Los modulos estaban escritos, las
    guardias en verde, el estado publicado y la pantalla
    pintando "EN VIVO" — y el unico sitio del proyecto que
    importaba `la_rendija` era la TELEMETRIA.

    `en_vivo = True` era la bandera del modulo, no una prueba de
    que se ejecutara. Armar algo y no enchufarlo es peor que no
    armarlo: la pantalla dice que funciona.

QUE HACE ESTE FICHERO

    Lo llama el ciclo DESPUES de la accion principal. Pregunta el
    permiso, elige a quien pujar, puja, y apunta.

    No decide NADA por su cuenta: el permiso lo da
    `la_rendija.permiso`, a quien pujar lo dice `con_margen` y
    `a_quien_pujar`, y el importe sale del tablero de fichajes.
    Aqui solo se ejecuta.

LA UNICA ESCRITURA

    `place_bid`. No hay ninguna otra, igual que en las otras tres
    rutas que escriben.
"""

from __future__ import annotations

import json

from datetime import datetime, timezone
from pathlib import Path


LIBRO = Path("data") / "trading" / "libro_del_carril.jsonl"


def _ahora() -> str:
    return datetime.now(timezone.utc).isoformat()


def safe_int(value, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def apuntar(fila: dict, ruta: Path | None = None) -> bool:
    destino = ruta or LIBRO

    try:
        destino.parent.mkdir(parents=True, exist_ok=True)

        with destino.open("a", encoding="utf-8") as fichero:
            fichero.write(
                json.dumps(fila, ensure_ascii=False) + "\n"
            )

        return True

    except Exception:                               # noqa: BLE001
        return False


def _epoch_del_ultimo_reset(ahora: datetime) -> int:
    """
    Las 07:00 de Madrid mas recientes. Es la unidad del cupo.

    Se apoya en la zona de silencio, que ya sabe de Madrid y de
    horarios de verano, para no escribir aqui un desfase a mano
    (doctrina 35).
    """

    from src.analysis.zona_de_silencio import (
        SILENCIO_HASTA,
        _hora_de_madrid,
    )

    madrid = _hora_de_madrid(ahora)

    minutos = madrid.hour * 60 + madrid.minute

    dias = 0 if minutos >= SILENCIO_HASTA else 1

    from datetime import timedelta

    reset = (madrid - timedelta(days=dias)).replace(
        hour=SILENCIO_HASTA // 60,
        minute=SILENCIO_HASTA % 60,
        second=0,
        microsecond=0,
    )

    return int(reset.timestamp())


def correr(
    *,
    accion_principal: str | None,
    cierres: list | None = None,
    objetivos: list | None,
    rates: dict | None,
    prima_de_puja: float,
    curva: float = 1.0,
    caja=None,
    comprometido=None,
    presupuesto=None,
    tope_por_operacion=None,
    escritor=None,
    disparo: str | None = None,
    ahora: datetime | None = None,
    ruta_del_libro: Path | None = None,
) -> dict:
    """
    Una vuelta del carril. Forma fija, nunca lanza.

    `objetivos` son las filas del tablero de fichajes, que ya
    traen el importe a pujar. Aqui NO se recalcula ninguno.
    """

    from src.analysis.la_rendija import (
        MARCA,
        suelo_de_precio,
        a_quien_pujar,
        bolsillo_del_carril,
        con_margen,
        importe_de_la_puja,
        los_que_se_pueden_pagar,
        permiso,
    )
    from src.analysis.libro_de_viajes import (
        cuantos_en_este_reset,
    )
    from src.analysis.bid_jitter import apply_bid_jitter

    # EL HECHO, NO LA INTENCION.
    #
    #     `ran_at` va en TODAS las salidas, incluida la de
    #     bloqueado y la de error. Es lo que le permite a la
    #     pantalla distinguir "no ha corrido nunca" de
    #     "corrio y no habia a quien pujar", que es
    #     exactamente lo que hubo que descubrir a mano el
    #     12/09.
    salida = {
        "ran_at": _ahora(),
        "available": False,
        "executed": False,
        "bids": [],
        "failed": [],
        "blocked_by": None,
        "reason": None,
    }

    try:
        momento = ahora or datetime.now(timezone.utc)

        # Cuantas van en ESTE ciclo de reset, de 07:00 a 07:00.
        ya_van = cuantos_en_este_reset(
            desde_epoch=_epoch_del_ultimo_reset(momento)
        )

        puerta = permiso(
            cierres=cierres,
            ahora=momento,
            accion_principal=accion_principal,
            operaciones_en_este_reset=ya_van,
            disparo=disparo,
        )

        if not puerta.get("puede"):
            return {
                **salida,
                "ran_at": _ahora(),
                "available": True,
                "blocked_by": puerta.get("blocked_by"),
                "reason": puerta.get("reason"),
                "permiso": puerta,
            }

        # ------------------------------------------------
        # A QUIEN PUJAR
        # ------------------------------------------------
        suelo = suelo_de_precio(cierres)

        candidatos = [
            {
                "player_id": safe_int(t.get("id")),
                "name": t.get("name"),
                "position": safe_int(t.get("position")),
                "market_price": safe_int(t.get("market_price")),
                "bid": safe_int(t.get("bid")),
            }
            for t in (objetivos or [])
            if isinstance(t, dict)
            # EL SUELO VIVE EN UN SITIO. Durante la prueba de
            # humo son 400.000; despues vuelve a 1.000.000.
            and safe_int(t.get("market_price")) >= suelo["suelo"]
            and str(t.get("status") or "").lower() == "ok"
            and not t.get("outside_computer_market")
        ]

        margen = con_margen(
            candidatos,
            prima_de_puja=prima_de_puja,
            rates=rates,
        )

        # EL TOPE, ANTES DE ELEGIR Y NO DESPUES DE ELEGIR.
        #
        #     El 12/09, con el suelo ya bajado a 400.000, el
        #     carril elegia a Cancelo -5.970.000- contra un tope
        #     por operacion de 843.612, y la puja se rechazaba
        #     sola. Siete veces el tope.
        #
        #     El orden de preferencia NO MIRA EL PRECIO: va por
        #     prima de posicion, defensas primero. Asi que el
        #     primero de la lista puede costar cualquier cosa, y
        #     sin esto el ciclo se gasta en un nombre imposible.
        #
        #     Es el MISMO tope que ya habia, preguntado cuando
        #     todavia sirve de algo.
        # EL BOLSILLO DEL CARRIL, QUE ES SUYO.
        #
        #     En euros, no un porcentaje del motor de especular.
        #     Acotado por la caja: el carril no abre deuda para
        #     especular, asi que no puede comprometer dinero que
        #     no hay ni romper ninguna barandilla de solvencia.
        bolsillo = bolsillo_del_carril(
            caja, comprometido=comprometido
        )

        tope_por_operacion = (
            bolsillo["tope"]
            if tope_por_operacion is None
            else tope_por_operacion
        )

        pagables = los_que_se_pueden_pagar(
            margen.get("entran") or [],
            curva=curva,
            presupuesto=presupuesto,
            tope_por_operacion=tope_por_operacion,
        )

        caben = min(
            puerta["quedan_en_la_vuelta"],
            puerta["quedan_en_el_reset"],
        )

        elegidos = a_quien_pujar(
            pagables.get("caben") or [],
            cuantos=caben,
        )["elegidos"]

        if not elegidos:
            return {
                **salida,
                "available": True,
                "reason": (
                    f"El carril podia pujar y no hay a quien: "
                    f"{margen.get('reason')} "
                    f"{pagables.get('reason') or ''}".strip()
                ),
                "permiso": puerta,
                "margen": margen,
                "pagables": pagables,
                "bolsillo": bolsillo,
            }

        if escritor is None:
            from src.biwenger.write_client import (
                BiwengerWriteClient,
            )

            escritor = BiwengerWriteClient()

        puestas = []

        fallidas = []

        for fila in elegidos:

            pid = safe_int(fila.get("player_id"))

            # EL IMPORTE SALE DE LA CURVA, NO DEL TABLERO.
            #
            #     El tablero lo daba a CERO -decision
            #     RENDIMIENTO_INSUFICIENTE- porque decide con la
            #     compuerta de rendimiento, que es justo la que
            #     este carril no usa: el negocio de un viaje es
            #     el spread, no el rendimiento.
            #
            #     Los topes siguen mandando, y si no se saben no
            #     se puja.
            cuanto = importe_de_la_puja(
                fila.get("market_price"),
                curva=curva,
                presupuesto=presupuesto,
                tope_por_operacion=tope_por_operacion,
            )

            importe = safe_int(cuanto.get("amount"))

            # ============================================
            # EL DESVIO, QUE YA EXISTIA Y NO LO USABA NADIE
            # ============================================
            #
            #     12/09/2026. La primera puja del carril de la
            #     historia fue por Trent: 2.760.000 EUR. El
            #     precio de mercado, redondo clavado.
            #
            #     Las cuatro de la rueda esa misma mañana iban
            #     desviadas —1.604.001, 1.503.751, 240.601,
            #     150.376— porque la rueda SI llama a
            #     `apply_bid_jitter`. El carril no.
            #
            #     Mismo patron que el plato vacio de esa tarde:
            #     la pieza montada y sin enchufar.
            #
            #     Biwenger no publica como resuelve un empate.
            #     Como no lo sabemos, pujar un numero raro un
            #     pelo por encima es estrictamente mejor que
            #     pujar el redondo, y no hay contra: el desvio
            #     nunca pasa del techo ni del tope por operacion.
            #     `ceiling` es un TECHO DE IMPORTE, no el tamaño
            #     del desvio: la rueda le pasa el menor de sus
            #     limites ya comprobados. Aqui el limite ya
            #     comprobado es el bolsillo del carril, que es lo
            #     que `importe_de_la_puja` acaba de respetar.
            #
            #     (Se intento primero con `jitter_ceiling`, que
            #     devuelve 13.800 para un jugador de 2,76 M: el
            #     techo quedaba por debajo del suelo `precio + 1`
            #     y `apply_bid_jitter` devolvia el importe limpio
            #     sin desviar nada. Dos cosas distintas con
            #     nombres parecidos.)
            desvio = apply_bid_jitter(
                importe,
                safe_int(fila.get("market_price")),
                ceiling=safe_int(cuanto.get("tope")) or importe,
                player_id=pid,
                single_operation_limit=(
                    cuanto.get("tope")
                ),
            )

            importe = safe_int(desvio.get("bid")) or importe

            if pid <= 0 or importe <= 0:
                fallidas.append(
                    {
                        "name": fila.get("name"),
                        "error": cuanto.get("reason")
                        or "Sin id no se puja.",
                    }
                )
                continue

            # La MISMA marca de tiempo para los dos libros: si
            # discrepan, un dia habra que cruzarlos y no se
            # podra.
            puesta_en = _ahora()

            try:
                # LA UNICA ESCRITURA DE ESTE FICHERO.
                resultado = escritor.place_bid(
                    player_id=pid,
                    amount=importe,
                    execute=True,
                )

                # ====================================
                # EL MISMO LIBRO QUE LA RUEDA
                # ====================================
                #
                #     El carril tenia libro propio
                #     (`libro_del_carril.jsonl`) y no aparecia en
                #     `bid_outcome_ledger`. Asi que el arreglo de
                #     esta tarde —que el libro sepa perder— no le
                #     servia: su primera puja se habria resuelto
                #     a las 07:00 sin que nadie se enterara de si
                #     gano o perdio.
                #
                #     `target_source` es el campo que ya lleva el
                #     origen —SUBASTA_CARTERA, ACQUISITION_BOARD—
                #     asi que el carril usa ese y no uno nuevo:
                #     un dato, un nombre (regla 33).
                #
                #     Blindado: una puja ya confirmada por
                #     Biwenger no puede caerse por un fallo
                #     apuntandola.
                try:
                    from src.intelligence.bid_outcome_ledger import (
                        record_bid,
                    )

                    record_bid(
                        pid,
                        importe,
                        player_name=fila.get("name"),
                        market_price=safe_int(
                            fila.get("market_price")
                        ),
                        recommended_bid=safe_int(
                            cuanto.get("amount")
                        ),
                        intent="REVENDER",
                        target_source=MARCA,
                        market_rate_percent_per_day=(
                            fila.get("rate_percent_per_day")
                        ),
                        placed_at=puesta_en,
                    )

                except Exception:                   # noqa: BLE001
                    pass

                anotacion = {
                    "at": puesta_en,
                    "marca": MARCA,
                    "player_id": pid,
                    "player_name": fila.get("name"),
                    "position": safe_int(fila.get("position")),
                    "amount": importe,
                    "clean": safe_int(desvio.get("clean")),
                    "jitter": safe_int(desvio.get("jitter")),
                    "market_price": safe_int(
                        fila.get("market_price")
                    ),
                    "margen": (fila.get("margen") or {}).get(
                        "margen_percent"
                    ),
                    "supuesto": (fila.get("margen") or {}).get(
                        "supuesto"
                    ),
                    "sent": bool(resultado.get("sent")),
                    "success": resultado.get("success"),
                    "http_status": resultado.get("http_status"),
                    "response": resultado.get("response"),
                }

                apuntar(anotacion, ruta_del_libro)

                # Enviada no es hecha: la leccion de Jonny.
                if resultado.get("success") is False:
                    fallidas.append(
                        {
                            "name": fila.get("name"),
                            "error": (
                                f"Biwenger contesto "
                                f"{resultado.get('http_status')}"
                            ),
                        }
                    )
                    continue

                puestas.append(anotacion)

            except Exception as error:              # noqa: BLE001
                fallidas.append(
                    {
                        "name": fila.get("name"),
                        "error": (
                            f"{type(error).__name__}: {error}"
                        ),
                    }
                )

        return {
            "ran_at": _ahora(),
            "available": True,
            "executed": bool(puestas),
            "bids": puestas,
            "failed": fallidas,
            "permiso": puerta,
            "margen": margen,
            "pagables": pagables,
            "bolsillo": bolsillo,
            "reason": (
                f"{len(puestas)} puja(s) de la rendija"
                + (
                    f", {len(fallidas)} fallidas"
                    if fallidas
                    else ""
                )
                + "."
            ),
        }

    except Exception as error:                      # noqa: BLE001
        # Un carril que revienta no puede tumbar el ciclo.
        return {
            **salida,
            "reason": (
                f"El carril no pudo correr: "
                f"{type(error).__name__}: {error}"
            ),
        }
