import difflib
import unicodedata

from src.intelligence.api_football import search_player


def normalize_text(text: str) -> str:
    text = unicodedata.normalize(
        "NFKD",
        text,
    )

    text = "".join(
        char
        for char in text
        if not unicodedata.combining(char)
    )

    return text.lower().strip()


def name_similarity(
    name_a: str,
    name_b: str,
) -> float:

    a = normalize_text(name_a)
    b = normalize_text(name_b)

    return difflib.SequenceMatcher(
        None,
        a,
        b,
    ).ratio()


def get_biwenger_team_name(
    snapshot: dict,
    team_id: int,
) -> str | None:

    teams = (
        snapshot["catalog"]
        ["data"]
        ["teams"]
    )

    team = teams.get(
        str(team_id)
    )

    if not team:
        return None

    return team.get("name")


def find_external_player(
    player_name: str,
    expected_team: str | None = None,
) -> dict | None:

    results = search_player(
        player_name
    )

    if not results:
        return None

    candidates = []

    for result in results:

        player = result.get(
            "player",
            {},
        )

        external_name = (
            player.get("name")
            or ""
        )

        name_score = name_similarity(
            player_name,
            external_name,
        )

        statistics = result.get(
            "statistics",
            [],
        )

        teams = []

        for stat in statistics:

            team = stat.get(
                "team",
                {},
            )

            team_name = team.get(
                "name"
            )

            if (
                team_name
                and team_name not in teams
            ):
                teams.append(
                    team_name
                )

        team_bonus = 0

        if expected_team:

            expected_normalized = (
                normalize_text(
                    expected_team
                )
            )

            for team_name in teams:

                if (
                    normalize_text(
                        team_name
                    )
                    == expected_normalized
                ):
                    team_bonus = 0.50
                    break

        total_score = (
            name_score
            + team_bonus
        )

        candidates.append(
            {
                "external_id":
                    player.get("id"),

                "external_name":
                    external_name,

                "teams":
                    teams,

                "name_score":
                    name_score,

                "team_bonus":
                    team_bonus,

                "total_score":
                    total_score,
            }
        )

    candidates.sort(
        key=lambda item:
            item["total_score"],
        reverse=True,
    )

    best = candidates[0]

    # Evitamos mappings demasiado dudosos.
    if best["total_score"] < 0.60:
        return None

    return best