import sys
from pathlib import Path

# Añadimos src/ al path de Python
SRC_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SRC_DIR))

from collectors.league_collector import collect_league_snapshot


if __name__ == "__main__":
    collect_league_snapshot()