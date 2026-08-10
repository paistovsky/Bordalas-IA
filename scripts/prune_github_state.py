from __future__ import annotations

from pathlib import Path


DATA_DIR = Path("data")
SNAPSHOT_KEEP = 24
AUTOPILOT_LOG_MAX_LINES = 2000


def prune_snapshots() -> int:
    snapshots = sorted(
        DATA_DIR.glob("snapshot_*.json"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )

    removed = 0

    for path in snapshots[SNAPSHOT_KEEP:]:
        try:
            path.unlink()
            removed += 1
        except OSError:
            pass

    return removed


def prune_autopilot_log() -> bool:
    log_file = (
        DATA_DIR
        / "autopilot"
        / "autopilot_log.jsonl"
    )

    if not log_file.exists():
        return False

    try:
        lines = log_file.read_text(
            encoding="utf-8"
        ).splitlines()
    except OSError:
        return False

    if len(lines) <= AUTOPILOT_LOG_MAX_LINES:
        return False

    log_file.write_text(
        "\n".join(
            lines[-AUTOPILOT_LOG_MAX_LINES:]
        )
        + "\n",
        encoding="utf-8",
    )

    return True


def main() -> None:
    DATA_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    removed = prune_snapshots()
    log_pruned = prune_autopilot_log()

    print(
        f"Snapshots eliminados: {removed}"
    )

    print(
        "Log autopilot recortado: "
        f"{'SI' if log_pruned else 'NO'}"
    )


if __name__ == "__main__":
    main()
