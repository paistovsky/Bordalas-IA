from __future__ import annotations

import ast
import re
import shutil
from pathlib import Path

ROOT = Path.cwd()
TARGET = ROOT / "src" / "telemetry" / "dashboard_state.py"
RESOLVER_SOURCE = ROOT / "photo_resolver_v3" / "player_photo_resolver.py"
RESOLVER_TARGET = ROOT / "src" / "telemetry" / "player_photo_resolver.py"
BACKUP = ROOT / "src" / "telemetry" / "dashboard_state_PRE_PHOTO_V3_BACKUP.py"

def function_span(source: str, function_name: str) -> tuple[int, int]:
    tree = ast.parse(source)
    lines = source.splitlines(keepends=True)
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == function_name:
            start = sum(len(line) for line in lines[:node.lineno - 1])
            end = sum(len(line) for line in lines[:node.end_lineno])
            return start, end
    raise RuntimeError(f"No encuentro {function_name}")

def replace_function(source: str, function_name: str, replacement: str) -> str:
    start, end = function_span(source, function_name)
    return source[:start] + replacement.rstrip() + "\n\n" + source[end:].lstrip("\n")

def main() -> None:
    if not TARGET.exists():
        raise SystemExit(f"No existe {TARGET}")
    if not RESOLVER_SOURCE.exists():
        raise SystemExit("Descomprime el paquete como .\\photo_resolver_v3 primero.")

    if not BACKUP.exists():
        shutil.copy2(TARGET, BACKUP)

    shutil.copy2(RESOLVER_SOURCE, RESOLVER_TARGET)

    source = TARGET.read_text(encoding="utf-8")

    import_block = (
        "from src.telemetry.player_photo_resolver import (\n"
        "    build_player_photo_lookup as build_player_photo_lookup_v3,\n"
        "    display_name as display_player_name,\n"
        ")\n"
    )

    if "build_player_photo_lookup_v3" not in source:
        match = re.search(r"\n[A-Z][A-Z0-9_]+\s*=", source)
        if not match:
            raise RuntimeError("No encuentro punto seguro para insertar import.")
        pos = match.start() + 1
        source = source[:pos] + import_block + "\n" + source[pos:]

    wrapper = '''def build_player_photo_lookup(
    snapshot: dict,
) -> dict[int, dict]:
    return build_player_photo_lookup_v3(snapshot)
'''
    source = replace_function(source, "build_player_photo_lookup", wrapper)

    compact = '''def compact_lineup(
    lineup_state: dict,
    snapshot: dict,
    photo_lookup: dict[int, dict] | None = None,
) -> dict:
    lineup = lineup_state.get("lineup", {}) or {}
    selected = lineup.get("selected", []) or []
    photo_lookup = photo_lookup or {}

    my_team_by_id = {
        safe_int(player.get("id")): player
        for player in snapshot.get("my_team", []) or []
    }

    catalog_players = (
        snapshot.get("catalog", {})
        .get("data", {})
        .get("players", {})
        or {}
    )

    players = []

    for player in selected:
        player_id = safe_int(player.get("id"))

        catalog_source = {}
        if isinstance(catalog_players, dict):
            catalog_source = (
                catalog_players.get(str(player_id))
                or catalog_players.get(player_id)
                or {}
            )

        source = my_team_by_id.get(player_id) or catalog_source or {}
        photo = photo_lookup.get(player_id) or {}

        icon_hero = (
            player.get("iconHero")
            or source.get("iconHero")
            or photo.get("icon_hero")
        )

        raw_name = (
            player.get("name")
            or source.get("name")
            or photo.get("name")
            or "?"
        )

        fixed_name = display_player_name(raw_name)

        price = safe_int(
            player.get(
                "price",
                source.get("price"),
            )
        )

        players.append(
            {
                "id": player_id,
                "name": fixed_name,
                "position": safe_int(
                    player.get(
                        "lineup_position",
                        player.get(
                            "position",
                            source.get("position"),
                        ),
                    )
                ),
                "price": price,
                "price_increment": safe_int(
                    player.get(
                        "priceIncrement",
                        source.get("priceIncrement"),
                    )
                ),
                "points": safe_int(
                    player.get(
                        "points",
                        source.get("points"),
                    )
                ),
                "lineup_score": round(
                    safe_float(player.get("lineup_score")),
                    2,
                ),
                "availability": player.get("availability_label"),
                "jp_status": player.get("external_lineup_status"),
                "jp_confidence": round(
                    safe_float(player.get("external_lineup_confidence")),
                    1,
                ),
                "icon_hero": icon_hero,
                "biwenger_photo_url": photo.get("biwenger_photo_url"),
                "api_football_id": photo.get("api_football_id"),
                "api_photo_url": photo.get("api_photo_url"),
                "photo_url": photo.get("photo_url"),
                "photo_source": photo.get("photo_source"),
                "team_id": safe_int(
                    player.get(
                        "teamID",
                        source.get("teamID"),
                    )
                ),
                "number": safe_int(
                    player.get(
                        "number",
                        source.get("number"),
                    )
                ),
            }
        )

    return {
        "formation": lineup.get("formation_name"),
        "playable": safe_int(lineup_state.get("playable_count")),
        "missing": safe_int(lineup_state.get("missing")),
        "score": round(safe_float(lineup.get("score")), 2),
        "total_value": sum(safe_int(item.get("price")) for item in players),
        "players": players,
    }
'''
    source = replace_function(source, "compact_lineup", compact)

    TARGET.write_text(source, encoding="utf-8")
    compile(source, str(TARGET), "exec")

    print("PHOTO RESOLVER V3 INSTALADO")
    print("Backup:", BACKUP)
    print("Resolver:", RESOLVER_TARGET)

if __name__ == "__main__":
    main()
