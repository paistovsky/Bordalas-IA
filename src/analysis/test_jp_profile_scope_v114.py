import tempfile

from pathlib import Path
from unittest.mock import patch

import src.intelligence.jornada_perfecta_provider as provider


def test_profiles_are_requested_only_after_roster_matching():
    raw_signals = [
        {
            "name": f"League player {index}",
            "player_url": f"https://example.test/player/{index}",
        }
        for index in range(220)
    ]
    roster_signals = [
        {
            "name": f"My player {index}",
            "player_url": f"https://example.test/my-player/{index}",
            "biwenger_id": index + 1,
        }
        for index in range(17)
    ]
    verified_sizes = []

    def verify_only_roster(*, session, signals):
        del session
        verified_sizes.append(len(signals))
        return signals, {
            "checked": len(signals),
            "explicit": len(signals),
            "overrides": 0,
        }

    crawl = {
        "pages": [("https://example.test/match", object())],
        "visited_pages": 1,
        "discovered_by_round": {1: 1},
        "errors": [],
    }

    with tempfile.TemporaryDirectory() as tmp:
        directory = Path(tmp)
        with (
            patch.object(provider, "DATA_DIRECTORY", directory),
            patch.object(
                provider,
                "DATA_FILE",
                directory / "lineups.json",
            ),
            patch.object(provider, "load_existing_file", return_value=None),
            patch.object(provider, "build_session", return_value=object()),
            patch.object(
                provider,
                "crawl_target_matchday",
                return_value=crawl,
            ),
            patch.object(
                provider,
                "build_page_signals",
                return_value=raw_signals,
            ),
            patch.object(
                provider,
                "extract_teams",
                return_value=("Home", "Away"),
            ),
            patch.object(
                provider,
                "attach_biwenger_identity",
                return_value=(
                    roster_signals,
                    set(range(1, 18)),
                    {"home", "away"},
                ),
            ),
            patch.object(
                provider,
                "verify_signals_with_player_profiles",
                side_effect=verify_only_roster,
            ),
        ):
            result = provider.refresh_jornada_perfecta_data(
                snapshot={},
                target_matchday=1,
                seconds_to_deadline=24 * 3600,
                force=True,
            )

    assert verified_sizes == [17]
    assert result["data"]["metadata"]["raw_signals"] == 220
    assert result["data"]["metadata"]["jp_profile_checked"] == 17


def main():
    test_profiles_are_requested_only_after_roster_matching()
    print("JP PROFILE SCOPE V11.4: 1/1 OK")


if __name__ == "__main__":
    main()
