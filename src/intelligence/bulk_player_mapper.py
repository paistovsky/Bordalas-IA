from src.intelligence.player_mapper import (
    find_external_player,
    get_biwenger_team_name,
)

from src.intelligence.player_mapping_cache import (
    get_cached_mapping,
    set_cached_mapping,
)


VERY_HIGH_CONFIDENCE = 1.10
HIGH_CONFIDENCE = 0.90
MEDIUM_CONFIDENCE = 0.75


def classify_confidence(
    confidence: float,
) -> str:

    if confidence >= VERY_HIGH_CONFIDENCE:
        return "MUY ALTA"

    if confidence >= HIGH_CONFIDENCE:
        return "ALTA"

    if confidence >= MEDIUM_CONFIDENCE:
        return "MEDIA"

    return "REVISAR"


def is_safe_for_automatic_use(
    confidence: float,
) -> bool:

    # Solo ALTA y MUY ALTA pueden afectar
    # decisiones automáticas.
    return confidence >= HIGH_CONFIDENCE


def build_result(
    mapping: dict,
    from_cache: bool,
) -> dict:

    confidence = mapping.get(
        "confidence",
        0.0,
    )

    return {
        **mapping,

        "confidence_level":
            classify_confidence(
                confidence
            ),

        "safe_for_automatic_use":
            is_safe_for_automatic_use(
                confidence
            ),

        "from_cache":
            from_cache,
    }


def get_player_team_id(
    player: dict,
) -> int | None:

    # Jugadores directamente obtenidos
    # del catálogo de Biwenger.
    if "teamID" in player:
        return player["teamID"]

    # Jugadores ya transformados por
    # nuestros analizadores.
    if "team_id" in player:
        return player["team_id"]

    return None


def map_player(
    snapshot: dict,
    player: dict,
) -> dict:

    biwenger_id = player["id"]

    # --------------------------------------------------
    # 1. COMPROBAR CACHÉ
    # --------------------------------------------------

    cached = get_cached_mapping(
        biwenger_id
    )

    if cached:
        return build_result(
            cached,
            from_cache=True,
        )

    # --------------------------------------------------
    # 2. OBTENER TEAM ID
    # --------------------------------------------------

    team_id = get_player_team_id(
        player
    )

    if team_id is None:
        return {
            "biwenger_id":
                biwenger_id,

            "biwenger_name":
                player.get(
                    "name",
                    "Desconocido",
                ),

            "biwenger_team":
                None,

            "external_id":
                None,

            "external_name":
                None,

            "external_teams":
                [],

            "confidence":
                0.0,

            "confidence_level":
                "REVISAR",

            "safe_for_automatic_use":
                False,

            "from_cache":
                False,
        }

    # --------------------------------------------------
    # 3. OBTENER CLUB BIWENGER
    # --------------------------------------------------

    team_name = get_biwenger_team_name(
        snapshot,
        team_id,
    )

    # --------------------------------------------------
    # 4. BUSCAR JUGADOR EXTERNO
    # --------------------------------------------------

    match = find_external_player(
        player["name"],
        team_name,
    )

    # --------------------------------------------------
    # 5. CONSTRUIR MAPPING
    # --------------------------------------------------

    if match is None:

        mapping = {
            "biwenger_id":
                biwenger_id,

            "biwenger_name":
                player["name"],

            "biwenger_team":
                team_name,

            "external_id":
                None,

            "external_name":
                None,

            "external_teams":
                [],

            "confidence":
                0.0,
        }

    else:

        mapping = {
            "biwenger_id":
                biwenger_id,

            "biwenger_name":
                player["name"],

            "biwenger_team":
                team_name,

            "external_id":
                match["external_id"],

            "external_name":
                match["external_name"],

            "external_teams":
                match["teams"],

            "confidence":
                match["total_score"],
        }

    # --------------------------------------------------
    # 6. GUARDAR EN CACHÉ
    # --------------------------------------------------

    set_cached_mapping(
        biwenger_id,
        mapping,
    )

    return build_result(
        mapping,
        from_cache=False,
    )