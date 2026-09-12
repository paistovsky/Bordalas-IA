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
        con_margen,
        importe_de_la_puja,
        los_que_se_pueden_pagar,
        permiso,
    )
    from src.analysis.libro_de_viajes import (
        cuantos_en_este_reset,
    )

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
        #     El orden de preferencia va por prima de reventa, y
        #     esa prefiere a los caros: sin esto el carril elige
        #     sistematicamente al que menos puede pagar y gasta
        #     el ciclo en un nombre imposible.
        #
        #     Es el MISMO tope que ya habia, preguntado cuando
        #     todavia sirve de algo.
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

            if pid <= 0 or importe <= 0:
                fallidas.append(
                    {
                        "name": fila.get("name"),
                        "error": cuanto.get("reason")
                        or "Sin id no se puja.",
                    }
                )
                continue

            try:
                # LA UNICA ESCRITURA DE ESTE FICHERO.
                resultado = escritor.place_bid(
                    player_id=pid,
                    amount=importe,
                    execute=True,
                )

                anotacion = {
                    "at": _ahora(),
                    "marca": MARCA,
                    "player_id": pid,
                    "player_name": fila.get("name"),
                    "position": safe_int(fila.get("position")),
                    "amount": importe,
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
