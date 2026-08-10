from src.intelligence.api_football import api_get


def get_player_sidelined(
    external_player_id: int,
) -> list[dict]:

    data = api_get(
        "sidelined",
        params={
            "player": external_player_id,
        },
    )

    return data.get(
        "response",
        [],
    )