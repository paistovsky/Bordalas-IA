from __future__ import annotations

POSITION_NAMES = {
    1: "Portero",
    2: "Defensa",
    3: "Centrocampista",
    4: "Delantero",
}

VALID_POSITIONS = frozenset(POSITION_NAMES)

# Politica deportiva de Bordalas IA.
#
# Aunque Biwenger exponga altPositions y la liga permita multiposicion,
# Pepe toma decisiones usando exclusivamente la posicion principal del
# jugador. Esto se aplica a XI, necesidades de plantilla y cobertura de
# pujas/reestructuracion.
POSITION_POLICY = "STRICT_PRIMARY"


def get_primary_position(player: dict) -> int | None:
    value = player.get("position")

    if value is None:
        return None

    try:
        position = int(value)
    except (TypeError, ValueError):
        return None

    if position not in VALID_POSITIONS:
        return None

    return position


def get_effective_positions(player: dict) -> list[int]:
    position = get_primary_position(player)

    if position is None:
        return []

    return [position]


def position_name(position: int | None) -> str:
    return POSITION_NAMES.get(position, "Desconocida")


def assert_lineup_position_integrity(players: list[dict]) -> None:
    for player in players:
        assigned = player.get("lineup_position")
        primary = get_primary_position(player)

        if assigned is None:
            raise AssertionError(
                f"{player.get('name', '?')} no tiene lineup_position."
            )

        if primary is None:
            raise AssertionError(
                f"{player.get('name', '?')} no tiene posicion principal valida."
            )

        if int(assigned) != primary:
            raise AssertionError(
                "POSITION_INTEGRITY_VIOLATION: "
                f"{player.get('name', '?')} es {position_name(primary)} "
                f"({primary}) y fue asignado a {position_name(int(assigned))} "
                f"({assigned})."
            )
