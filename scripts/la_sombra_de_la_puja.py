"""
La sombra de la puja, en una pantalla: a quien pujaria Pepe y cuanto.

Lee la foto del panel -`subasta.sombra`- y la imprime de mayor a
menor puja, con el candado que le queda a cada uno. Para mirarla a
las tres de la mañana sin abrir un JSON de 1,3 MB.

Primero baja la foto:

    .\\scripts\\foto_para_claude.ps1

Y despues:

    python scripts/la_sombra_de_la_puja.py [ruta/a/status.json]

Solo lee. No escribe nada y no sale a la red.
"""

from __future__ import annotations

import json
import sys

from pathlib import Path


RAIZ = Path(__file__).resolve().parents[1]

FOTO = RAIZ / "diagnostico" / "status.json"


def _euros(valor) -> str:
    return f"{int(valor or 0):,}".replace(",", ".")


def main() -> int:

    ruta = Path(sys.argv[1]) if len(sys.argv) > 1 else FOTO

    foto = json.loads(ruta.read_text(encoding="utf-8"))

    sombra = (foto.get("subasta") or {}).get("sombra")

    print()
    print("LA SOMBRA DE LA PUJA")
    print("=" * 78)
    print(f"  foto: {ruta}")
    print(f"  {(foto.get('meta') or {}).get('generated_at')}")
    print()

    if not isinstance(sombra, dict):
        print(
            "  Esta foto no trae `subasta.sombra`: es de antes del "
            "23/09 o la telemetria no la publico."
        )
        return 1

    print(f"  {sombra.get('reason')}")
    print()

    for candado in sombra.get("candados") or []:
        print(f"  CANDADO {candado.get('candado')}")
        print(f"          {candado.get('reason')}")

    if sombra.get("candados"):
        print()

    for i, fila in enumerate(sombra.get("bids") or [], 1):
        print(f"  {i:>2}. {fila.get('name')}")
        print(
            f"      precio {_euros(fila.get('price'))}   PUJARIA "
            f"{_euros(fila.get('bid'))}   prima "
            f"{_euros(fila.get('prima'))} "
            f"({fila.get('prima_percent')} %)"
        )
        print(f"      por que: {fila.get('por_que')}")
        print(
            "      le queda: "
            + (", ".join(fila.get("candados") or []) or "nada")
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
