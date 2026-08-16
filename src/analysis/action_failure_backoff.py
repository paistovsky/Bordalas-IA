from __future__ import annotations

import json

from datetime import datetime, timedelta
from pathlib import Path


# ============================================================
# POR QUE EXISTE ESTE MODULO
# ============================================================
#
# El ciclo ejecuta UNA sola accion por vuelta: la primera
# ejecutable de la cola ordenada por prioridad.
#
# Si esa accion falla siempre -por ejemplo una renovacion que
# Biwenger rechaza con HTTP 400- vuelve a ser la primera en el
# siguiente ciclo, y en el siguiente, y en el siguiente. El
# resto de acciones -pujar, especular, mejorar el once- nunca
# llegan a ejecutarse.
#
# Eso fue exactamente lo que paso: 6 objetivos pujables sobre
# la mesa y 0 pujas vivas, porque RENEW_MARKET_LISTING ganaba
# la cola cada 30 minutos y fallaba cada 30 minutos.
#
# Este modulo recuerda los fallos reales de escritura y aparta
# temporalmente la accion que falla, para que la cola avance.
# No oculta el problema: lo registra y lo expone.


STATE_DIRECTORY = (
    Path("data")
    / "autopilot"
)

STATE_FILE = (
    STATE_DIRECTORY
    / "action_failure_backoff.json"
)


# Un ciclo completo. El primer fallo aparta la accion durante
# la siguiente vuelta, no mas.
BASE_BACKOFF_SECONDS = 1800

# Techo del castigo. Aunque falle veinte veces seguidas, la
# accion se reintenta al menos cada 6 horas.
MAX_BACKOFF_SECONDS = 21600

# Limite de entradas guardadas para que el fichero no crezca
# sin control.
MAX_TRACKED_ENTRIES = 200


# ============================================================
# HELPERS
# ============================================================


def ensure_state_directory() -> None:

    STATE_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )


def build_action_key(
    action: str | None,
    target_id=None,
) -> str:
    """
    Identifica la accion concreta que fallo.

    Renovar la publicacion de Yeray y renovar la de Dituro son
    dos cosas distintas: si una falla, la otra debe poder
    intentarse.
    """

    accion = str(
        action
        or "UNKNOWN"
    ).strip().upper()

    if target_id is None:
        return accion

    return f"{accion}:{target_id}"


def parse_moment(
    value,
) -> datetime | None:

    if value is None:
        return None

    if isinstance(
        value,
        datetime,
    ):
        return value

    try:
        return datetime.fromisoformat(
            str(
                value
            )
        )

    except (TypeError, ValueError):
        return None


def backoff_seconds(
    consecutive_failures: int,
) -> int:
    """
    Castigo exponencial con techo.

    1 fallo  -> 30 min
    2 fallos -> 1 h
    3 fallos -> 2 h
    4 fallos -> 4 h
    5+       -> 6 h (techo)
    """

    fallos = max(
        int(
            consecutive_failures
            or 0
        ),
        0,
    )

    if fallos <= 0:
        return 0

    segundos = (
        BASE_BACKOFF_SECONDS
        * (
            2
            ** (
                fallos
                - 1
            )
        )
    )

    return int(
        min(
            segundos,
            MAX_BACKOFF_SECONDS,
        )
    )


# ============================================================
# PERSISTENCIA
# ============================================================


def empty_state() -> dict:

    return {
        "actions": {},
    }


def load_backoff_state() -> dict:

    if not STATE_FILE.exists():
        return empty_state()

    try:

        with open(
            STATE_FILE,
            "r",
            encoding="utf-8-sig",
        ) as file:

            data = json.load(
                file
            )

        if not isinstance(
            data,
            dict,
        ):
            raise ValueError(
                "Root invalido."
            )

        acciones = data.get(
            "actions"
        )

        if not isinstance(
            acciones,
            dict,
        ):
            data["actions"] = {}

        return data

    except (
        OSError,
        json.JSONDecodeError,
        ValueError,
    ):
        return empty_state()


def save_backoff_state(
    state: dict,
) -> None:

    ensure_state_directory()

    acciones = (
        state.get(
            "actions",
            {},
        )
        or {}
    )

    if len(acciones) > MAX_TRACKED_ENTRIES:

        ordenadas = sorted(
            acciones.items(),
            key=lambda item: str(
                (item[1] or {}).get(
                    "last_failure_at",
                    "",
                )
            ),
            reverse=True,
        )

        state = {
            **state,
            "actions": dict(
                ordenadas[
                    :MAX_TRACKED_ENTRIES
                ]
            ),
        }

    temporary = (
        STATE_FILE.with_suffix(
            ".json.tmp"
        )
    )

    with open(
        temporary,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            state,
            file,
            ensure_ascii=False,
            indent=2,
        )

    temporary.replace(
        STATE_FILE
    )


# ============================================================
# CONSULTA
# ============================================================


def get_backoff(
    state: dict,
    action: str | None,
    target_id=None,
    now: datetime | None = None,
) -> dict:

    now = now or datetime.now()

    key = build_action_key(
        action,
        target_id,
    )

    entrada = (
        (
            state.get(
                "actions",
                {},
            )
            or {}
        ).get(
            key
        )
        or {}
    )

    fallos = int(
        entrada.get(
            "consecutive_failures",
            0,
        )
        or 0
    )

    bloqueada_hasta = parse_moment(
        entrada.get(
            "blocked_until"
        )
    )

    if (
        bloqueada_hasta is not None
        and now.tzinfo is not None
        and bloqueada_hasta.tzinfo is None
    ):
        bloqueada_hasta = (
            bloqueada_hasta.replace(
                tzinfo=now.tzinfo
            )
        )

    if (
        bloqueada_hasta is not None
        and now.tzinfo is None
        and bloqueada_hasta.tzinfo is not None
    ):
        bloqueada_hasta = (
            bloqueada_hasta.replace(
                tzinfo=None
            )
        )

    bloqueada = bool(
        bloqueada_hasta is not None
        and now < bloqueada_hasta
    )

    if bloqueada:
        restante = int(
            (
                bloqueada_hasta
                - now
            ).total_seconds()
        )
    else:
        restante = 0

    return {
        "key":
            key,

        "blocked":
            bloqueada,

        "consecutive_failures":
            fallos,

        "blocked_until":
            bloqueada_hasta,

        "seconds_remaining":
            restante,

        "last_status":
            entrada.get(
                "last_status"
            ),

        "last_http_status":
            entrada.get(
                "last_http_status"
            ),

        "last_reason":
            entrada.get(
                "last_reason"
            ),
    }


# ============================================================
# REGISTRO
# ============================================================


def record_action_result(
    state: dict,
    *,
    action: str | None,
    target_id=None,
    success: bool,
    write_performed: bool = True,
    status: str | None = None,
    http_status=None,
    reason: str | None = None,
    now: datetime | None = None,
) -> dict:
    """
    Solo cuentan los intentos de escritura reales.

    Un DRY_RUN o un NOT_EXECUTABLE no son fallos: no se ha
    tocado Biwenger, no hay nada que castigar.
    """

    now = now or datetime.now()

    if not write_performed:
        return state

    key = build_action_key(
        action,
        target_id,
    )

    acciones = state.setdefault(
        "actions",
        {},
    )

    if success:
        acciones.pop(
            key,
            None,
        )

        return state

    entrada = (
        acciones.get(
            key
        )
        or {}
    )

    fallos = int(
        entrada.get(
            "consecutive_failures",
            0,
        )
        or 0
    ) + 1

    espera = backoff_seconds(
        fallos
    )

    acciones[key] = {
        "action":
            action,

        "target_id":
            target_id,

        "consecutive_failures":
            fallos,

        "last_failure_at":
            now.isoformat(),

        "blocked_until":
            (
                now
                + timedelta(
                    seconds=espera
                )
            ).isoformat(),

        "backoff_seconds":
            espera,

        "last_status":
            status,

        "last_http_status":
            http_status,

        "last_reason":
            reason,
    }

    return state


# ============================================================
# APLICACION SOBRE LA COLA DE DECISIONES
# ============================================================


def candidate_target_id(
    candidate: dict,
):
    """
    Extrae el objetivo concreto de una decision.

    No inventa: si la decision no apunta a un jugador o a una
    oferta identificable, devuelve None y el backoff se aplica
    a la accion entera.
    """

    data = (
        candidate.get(
            "data",
            {},
        )
        or {}
    )

    listing = (
        data.get(
            "listing",
            {},
        )
        or {}
    )

    if listing.get(
        "player_id"
    ) is not None:
        return listing[
            "player_id"
        ]

    player = (
        data.get(
            "player",
            {},
        )
        or {}
    )

    for campo in (
        "player_id",
        "id",
    ):
        if player.get(
            campo
        ) is not None:
            return player[
                campo
            ]

    offer = (
        data.get(
            "offer",
            {},
        )
        or {}
    )

    if offer.get(
        "offer_id"
    ) is not None:
        return offer[
            "offer_id"
        ]

    if data.get(
        "offer_id"
    ) is not None:
        return data[
            "offer_id"
        ]

    return None


def apply_backoff_to_candidates(
    candidates: list[dict],
    state: dict | None = None,
    now: datetime | None = None,
) -> dict:
    """
    Desactiva -no borra- los candidatos que estan en castigo.

    Se mantienen en la lista para que el dashboard y el log
    sigan viendo que existen y por que no se ejecutan.
    """

    state = (
        state
        if state is not None
        else load_backoff_state()
    )

    now = now or datetime.now()

    bloqueados = []

    for candidate in candidates:

        if not candidate.get(
            "executable",
            False,
        ):
            continue

        target_id = candidate_target_id(
            candidate
        )

        info = get_backoff(
            state=state,
            action=candidate.get(
                "action"
            ),
            target_id=target_id,
            now=now,
        )

        # El candidato acaba en telemetria y en JSON: nada de
        # datetime crudos aqui.
        candidate["backoff"] = {
            **info,

            "blocked_until":
                (
                    info["blocked_until"].isoformat()
                    if info["blocked_until"] is not None
                    else None
                ),
        }

        if not info["blocked"]:
            continue

        minutos = max(
            info["seconds_remaining"]
            // 60,
            1,
        )

        candidate["executable"] = False
        candidate["executor"] = None
        candidate["blocked_by_backoff"] = True

        candidate["reason"] = (
            f"{candidate.get('reason', '')} "
            f"[EN ESPERA] Esta accion ha fallado "
            + (
                "1 vez"
                if info["consecutive_failures"] == 1
                else
                f"{info['consecutive_failures']} veces seguidas"
            )
            + (
                f" (HTTP {info['last_http_status']})"
                if info["last_http_status"] is not None
                else ""
            )
            + f". Se reintenta en {minutos} min para no bloquear "
            "el resto de acciones del ciclo."
        ).strip()

        bloqueados.append(
            {
                "action":
                    candidate.get(
                        "action"
                    ),

                "type":
                    candidate.get(
                        "type"
                    ),

                "target_id":
                    target_id,

                "consecutive_failures":
                    info[
                        "consecutive_failures"
                    ],

                "seconds_remaining":
                    info[
                        "seconds_remaining"
                    ],

                "last_http_status":
                    info[
                        "last_http_status"
                    ],
            }
        )

    return {
        "blocked":
            bloqueados,

        "blocked_count":
            len(
                bloqueados
            ),
    }
