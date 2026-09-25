"""
La lista de la noche, en una pantalla.

POR QUE EXISTE (22/09/2026)

    «Si hay que mirar un `.jsonl` a las tres de la mañana, no
    sirve.»

    La lista va en la foto del panel -`lista_de_la_noche`
    dentro de `status.json`-, que es donde tiene que estar. Esto
    es solo la forma de mirarla sin abrir un JSON de 500 KB:

        python scripts/la_lista_de_la_noche.py

    UN PASO QUE DECIDE, UN COMANDO.

QUE NO HACE

    No calcula nada. No sale a la red. No escribe. Lee la foto
    que ya esta publicada y la imprime. Si la foto no esta, lo
    dice en vez de inventar una.
"""

from __future__ import annotations

import json
import sys

from pathlib import Path


RAIZ = Path(__file__).resolve().parents[1]


# Donde deja la foto cada sitio. Se prueban en orden: la del
# diagnostico es la de la ultima vuelta de CI.
LAS_FOTOS = (
    RAIZ / "diagnostico" / "status.json",
    RAIZ / "dashboard" / "data" / "status.json",
    RAIZ / "dashboard-v8" / "public" / "data" / "status.json",
)


def _euros(valor) -> str:
    try:
        return f"{int(valor or 0):,}".replace(",", ".")

    except (TypeError, ValueError):
        return "?"


def la_foto(ruta=None):
    """La foto publicada, y de donde salio. Nunca lanza."""

    candidatas = [Path(ruta)] if ruta else list(LAS_FOTOS)

    for destino in candidatas:
        try:
            return json.loads(destino.read_text(encoding="utf-8")), destino

        except Exception:                           # noqa: BLE001
            continue

    return None, None


def main() -> int:

    foto, donde = la_foto(sys.argv[1] if len(sys.argv) > 1 else None)

    if foto is None:
        print("No hay foto publicada que mirar. Se probaron:")

        for destino in LAS_FOTOS:
            print(f"    {destino}")

        return 1

    lista = foto.get("lista_de_la_noche") or {}

    print("LA LISTA DE LA NOCHE")
    print("=" * 78)
    print(f"  foto: {donde}")
    print(f"  {(foto.get('meta') or {}).get('generated_at') or '(sin hora)'}")
    print()

    if not lista:
        print(
            "  Esta foto es anterior a la lista de la noche: no la "
            "lleva."
        )
        return 1

    print(f"  {lista.get('reason')}")
    print()

    # LA FORMA DEL 25/09: fila a fila, con el camino que pujaria.
    for numero, fila in enumerate(lista.get("filas") or [], start=1):
        print(
            f"  {numero:2}. {fila.get('jugador')}   "
            f"precio {_euros(fila.get('precio_de_mercado'))}   "
            f"PUJARIA {_euros(fila.get('lo_que_pujaria'))}   "
            f"por {fila.get('camino')} (via {fila.get('via')}, "
            f"bolsillo {_euros(fila.get('bolsillo')) if fila.get('bolsillo') is not None else '-'})"
        )

    print()
    print("  CAMINO A CAMINO")

    for camino, que in (lista.get("caminos") or {}).items():
        cubierto = "si" if que.get("cubierto") else "NO"
        print(f"    {camino:18s} cubierto: {cubierto:2s}  {que.get('reason')}")
        for viva in que.get("ya_vivas") or []:
            print(f"    {'':18s} ya tiene puja nuestra viva: {viva.get('jugador')} "
                  f"({_euros(viva.get('puja_viva'))} EUR), no se repite")
        if que.get("ultima_decision"):
            print(f"    {'':18s} ultima vuelta ({que.get('ultima_vuelta')}): "
                  f"{que.get('ultima_decision')}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
