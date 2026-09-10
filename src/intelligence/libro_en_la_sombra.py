"""
El libro en la sombra: lo que compraria con la compuerta apagada.

POR QUE EXISTE (10/09/2026)

    La compuerta de ritmo cierra la via de especulacion en la
    mitad del escaparate. Y medido sobre los 36 viajes cerrados
    de Pollo17, no discrimina: bloqueo las 6 compras con las que
    gano 1,78 M y habria dejado pasar las 3 con las que
    Manzagool perdio 1,24 M.

    Pero eso son 9 casos y con 9 casos no se retira un filtro.

    Asi que se apunta, TODOS LOS DIAS Y SIN DINERO, lo que
    habriamos comprado con la compuerta apagada del todo. En dos
    semanas hay unos 280 casos y entonces se decide si la
    compuerta se retira o se queda.

NO GASTA UN EURO Y NO DECIDE NADA

    Es un cuaderno. Ninguna ruta lo lee. Si manana desaparece,
    lo unico que se pierde es el estudio.

DE DONDE SALE, SIN CALCULAR NADA NUEVO

    La propia compuerta publica lo que habia ANTES de cerrar:

        intent_before   la via que iba a abrirse
        value_before    lo que valia el jugador antes del corte

    Asi que la sombra no re-valora: lee lo que el tablero ya
    publica y lo apunta. Si algun dia el tablero cambia de
    forma, esto se queda vacio y lo dice, en vez de inventar.

LO QUE SE APUNTA DE CADA CASO

    Jugador, precio, lo que valia antes del corte, el margen que
    eso implicaba, el motivo del corte y el ritmo observado. Con
    eso, dentro de dos semanas, se puede contestar la unica
    pregunta que importa: de los que la compuerta rechazo,
    ¿cuantos habrian ganado dinero?

    Para contestarla hara falta cruzar esto con el precio de
    esos jugadores DIAS DESPUES. El precio se guarda solo en el
    historico; aqui solo hay que apuntar quien era quien.
"""

from __future__ import annotations

import json

from datetime import datetime, timezone
from pathlib import Path


FICHERO = Path("data") / "intelligence" / "libro_en_la_sombra.jsonl"


# Dos semanas de escaparate. No es un umbral: es cuando el dueno
# dijo que se decide.
CASOS_PARA_DECIDIR = 280


DIAS_QUE_SE_GUARDAN = 60


def _ahora() -> str:
    return datetime.now(timezone.utc).isoformat()


def safe_int(value, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def _leer(ruta: Path) -> list:
    try:
        lineas = ruta.read_text(encoding="utf-8").splitlines()
    except Exception:                               # noqa: BLE001
        return []

    filas = []

    for linea in lineas:

        linea = linea.strip()

        if not linea:
            continue

        try:
            fila = json.loads(linea)
        except Exception:                           # noqa: BLE001
            continue

        if isinstance(fila, dict):
            filas.append(fila)

    return filas


def los_que_la_compuerta_rechaza(targets: list | None) -> list:
    """
    Las filas cuya via cerro LA COMPUERTA, no otra cosa.

    Se excluyen a proposito:

        · los de mercado de rival, que tienen la puerta cerrada
          por orden del dueno y no por la compuerta;
        · los que ya tenian puja viva nuestra.

    Si se colaran, la sombra mediria el efecto de otras reglas y
    le echaria la culpa a esta.
    """

    filas = []

    for fila in (targets or []):

        if not isinstance(fila, dict):
            continue

        compuerta = fila.get("market_gate") or {}

        puerta = compuerta.get("gate")

        if puerta in (None, "RITMO_OBSERVADO"):
            continue

        if fila.get("outside_computer_market") or fila.get(
            "seller_id"
        ):
            continue

        if fila.get("has_live_bid"):
            continue

        precio = safe_int(fila.get("market_price"))

        antes = safe_int(compuerta.get("value_before"))

        if precio <= 0 or antes <= 0:
            continue

        filas.append(
            {
                "id": fila.get("id"),
                "name": fila.get("name"),
                "market_price": precio,
                "value_before": antes,

                # El margen que la compuerta dejo sobre la mesa,
                # con la valoracion de ANTES del corte.
                "margin": antes - precio,
                "margin_percent": round(
                    (antes - precio) / precio * 100, 2
                ),

                "gate": puerta,
                "gate_reason": compuerta.get("gate_reason"),
                "rate_percent_per_day": compuerta.get(
                    "rate_percent_per_day"
                ),
                "trend_days": compuerta.get("trend_days"),
                "demand_net": compuerta.get("demand_net"),
                "intent_before": compuerta.get("intent_before"),
            }
        )

    return sorted(filas, key=lambda f: -f["margin_percent"])


def apuntar_dia(
    targets: list | None,
    at: str | None = None,
    ruta: Path | None = None,
) -> dict:
    """
    Una linea por dia. Si ya hay una de hoy, no se duplica.

    Nunca lanza: un cuaderno que revienta no puede tumbar nada.
    """

    vacio = {
        "available": False,
        "cases": 0,
        "written": False,
        "reason": None,
    }

    try:
        filas = los_que_la_compuerta_rechaza(targets)

        momento = at or _ahora()

        destino = ruta or FICHERO

        anteriores = _leer(destino)

        hoy = str(momento)[:10]

        ya = any(
            str(f.get("at"))[:10] == hoy for f in anteriores
        )

        entrada = {
            "at": momento,
            "cases": len(filas),
            "players": filas,
        }

        if ya:
            return {
                **vacio,
                "available": True,
                "cases": len(filas),
                "reason": (
                    "Ya hay apunte de hoy: no se duplica."
                ),
            }

        destino.parent.mkdir(parents=True, exist_ok=True)

        anteriores.append(entrada)

        destino.write_text(
            "\n".join(
                json.dumps(f, ensure_ascii=False)
                for f in anteriores[-DIAS_QUE_SE_GUARDAN:]
            )
            + "\n",
            encoding="utf-8",
        )

        return {
            "available": True,
            "cases": len(filas),
            "written": True,
            "reason": (
                f"{len(filas)} caso(s) apuntados hoy en la "
                f"sombra."
            ),
        }

    except Exception as error:                      # noqa: BLE001
        return {
            **vacio,
            "reason": (
                f"No se pudo apuntar la sombra: "
                f"{type(error).__name__}: {error}"
            ),
        }


def resumen(ruta: Path | None = None) -> dict:
    """
    Cuantos casos llevamos y cuando se puede decidir.

    Forma fija. Nunca lanza.
    """

    try:
        filas = _leer(ruta or FICHERO)

        casos = sum(safe_int(f.get("cases")) for f in filas)

        por_motivo = {}

        for f in filas:
            for j in (f.get("players") or []):
                clave = j.get("gate")
                por_motivo[clave] = por_motivo.get(clave, 0) + 1

        faltan = max(0, CASOS_PARA_DECIDIR - casos)

        return {
            "available": bool(filas),
            "days": len(filas),
            "cases": casos,
            "by_gate": por_motivo,
            "needed": CASOS_PARA_DECIDIR,
            "missing": faltan,
            "ready": casos >= CASOS_PARA_DECIDIR,
            "reason": (
                (
                    f"{casos} casos en {len(filas)} dia(s). "
                    f"Faltan {faltan} para los "
                    f"{CASOS_PARA_DECIDIR} con los que se decide "
                    f"si la compuerta se retira."
                )
                if filas
                else (
                    "Todavia no hay ningun dia apuntado en la "
                    "sombra."
                )
            ),
        }

    except Exception as error:                      # noqa: BLE001
        return {
            "available": False,
            "days": 0,
            "cases": 0,
            "by_gate": {},
            "needed": CASOS_PARA_DECIDIR,
            "missing": CASOS_PARA_DECIDIR,
            "ready": False,
            "reason": (
                f"No se pudo leer la sombra: "
                f"{type(error).__name__}: {error}"
            ),
        }
