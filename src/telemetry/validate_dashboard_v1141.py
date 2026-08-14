
from src.telemetry.dashboard_state import (
    build_dashboard_state,
    save_dashboard_state,
)


def main():

    state = build_dashboard_state()
    path = save_dashboard_state(
        state
    )

    lineup = (
        state.get(
            "lineup",
            {},
        )
        or {}
    )

    players = (
        lineup.get(
            "players",
            [],
        )
        or []
    )

    print()
    print("=" * 132)
    print("V11.4.1 DASHBOARD MULTISOURCE - VALIDACION REAL")
    print("=" * 132)
    print("Status:", path)
    print("-" * 132)

    javi = None

    for player in players:

        print(
            f"{player.get('name',''):<24} "
            f"CONS={str(player.get('starter_consensus')):<11} "
            f"P={str(player.get('starter_probability')):<5} "
            f"SRC={player.get('starter_source_coverage')}/3 "
            f"V={player.get('starter_votes')}S/"
            f"{player.get('uncertain_votes')}U/"
            f"{player.get('bench_votes')}B "
            f"JP={player.get('jp_probability')} "
            f"FF={player.get('ff_probability')} "
            f"AF={player.get('af_probability')} "
            f"UI_COMPAT={player.get('jp_status')} "
            f"{player.get('jp_confidence')}"
        )

        if (
            "javi hern"
            in str(
                player.get(
                    "name",
                    "",
                )
            ).lower()
        ):
            javi = player

    if len(players) != 11:
        raise RuntimeError(
            f"Dashboard XI != 11: {len(players)}"
        )

    if not javi:
        raise RuntimeError(
            "Javi no aparece en el XI del dashboard."
        )

    if (
        javi.get(
            "starter_consensus"
        )
        != "UNCERTAIN"
    ):
        raise RuntimeError(
            "Javi no aparece UNCERTAIN."
        )

    if (
        float(
            javi.get(
                "starter_probability"
            )
            or 0
        )
        != 50.0
    ):
        raise RuntimeError(
            "Javi no aparece al 50%."
        )

    if (
        javi.get(
            "jp_status"
        )
        != "UNCERTAIN"
    ):
        raise RuntimeError(
            "Frontend legacy aun recibira TITULAR."
        )

    if (
        float(
            javi.get(
                "jp_confidence"
            )
            or 0
        )
        != 50.0
    ):
        raise RuntimeError(
            "Frontend legacy aun recibira 96%."
        )

    if not any(
        player.get(
            "ff_probability"
        )
        is not None
        for player in players
    ):
        raise RuntimeError(
            "Dashboard no recibe FutbolFantasy."
        )

    print()
    print("OK - Javi: UNCERTAIN 50%.")
    print("OK - JP/FF/AF llegan al status.json.")
    print("OK - frontend actual ya no recibira TITULAR 96 para Javi.")
    print("=" * 132)


if __name__ == "__main__":
    main()
