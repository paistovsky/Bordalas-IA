"""
Una foto al dia, en git.

POR QUE ESTO NO EXISTIA Y HACIA FALTA

    `diagnostico/` esta en `.gitignore` (linea 114) y no hay ni
    una foto guardada: `git log -- diagnostico/status.json` da
    CERO revisiones. Llevamos una semana pidiendo tablas "antes /
    despues" sobre un archivo que no existe.

    El 19/09 costo dos cosas a la vez: no se pudo recorrer el
    libro de pujas contra las fotos -no hay fotas- y la foto de
    referencia del encargo (12:32) sencillamente no estaba.

POR QUE LA FOTO ENTERA Y NO EL RECORTE

    Medido sobre la foto del 18/09 16:16:38:

        entera, compacta          1.054,3 KB
        lo que git guarda (zlib)    113,3 KB   ->  40,4 MB/ano
        recorte de 10 campos         23,6 KB
        recorte, zlib                 5,1 KB   ->   1,8 MB/ano

    El recorte es 22 veces mas barato y aun asi no compensa. La
    lista de campos que se propuso -summary, race, solvency,
    solvency_clock, subasta, listings, offers, acquisition,
    marcador, bid_outcomes- NO incluye `pujas_del_dueno`, que es
    exactamente el bloque que resolvio el caso de Maffeo el
    19/09. Tampoco `consistency`, ni `silencio`, ni
    `loNuestroALaVenta`, que tambien hicieron falta ese mismo dia.

    Un recorte guarda lo que hoy creemos que vamos a necesitar.
    El dia que haga falta otra cosa, no esta, y no se puede
    volver atras. 40 MB al ano es barato al lado de eso.

POR QUE COMPACTA Y NO COMPRIMIDA

    Git ya comprime: un blob de 1.054 KB se queda en ~113 KB. Un
    `.gz` no se puede deltificar entre dias ni se puede leer con
    `git log -p`, asi que comprimir a mano cuesta el doble: se
    pierde la delta Y se pierde poder mirarla.

    Compacta (sin `indent`) porque el indent son 487 KB de
    espacios que no dicen nada.

POR QUE UN PASO APARTE Y NO EL CICLO

    Es la leccion del tablon (doctrina 88). `guardar_los_libros`
    escribe desde donde corra el ciclo, y una maquina con la copia
    vieja puede pisar lo bueno. La foto es de SOLO ESCRITURA y
    nunca se relee, asi que no puede pisar nada — pero para que
    siga siendo verdad tiene que vivir fuera de esa ruta.

    Y una foto al dia, no una por vuelta: veinte vueltas diarias
    serian 800 MB al ano para ver lo mismo.

USO

    python scripts/guardar_la_foto.py            # guarda si no hay de hoy
    python scripts/guardar_la_foto.py --forzar   # la reescribe
    python scripts/guardar_la_foto.py --dry-run  # dice que haria

    No escribe en Biwenger, no sale a la red y no hace `git`:
    deja el fichero y quien empuje decide.
"""

from __future__ import annotations

import argparse
import json
import sys

from datetime import datetime, timezone
from pathlib import Path


RAIZ = Path(__file__).resolve().parents[1]

ORIGEN = RAIZ / "diagnostico" / "status.json"

DESTINO = RAIZ / "data" / "fotos"


def fecha_de_la_foto(foto: dict) -> str | None:
    """
    El dia que dice la FOTO, no el reloj del sistema.

    Si la foto no trae `generated_at` no se le inventa fecha: se
    dice y se para. Una foto archivada bajo el dia equivocado es
    peor que no tenerla, porque la siguiente comparacion sale mal
    y nadie sabe por que.
    """

    sello = (foto.get("meta") or {}).get("generated_at")

    if not sello:
        return None

    try:
        momento = datetime.fromisoformat(
            str(sello).replace("Z", "+00:00")
        )

    except ValueError:
        return None

    if momento.tzinfo is None:
        momento = momento.replace(tzinfo=timezone.utc)

    return momento.date().isoformat()


def guardar(forzar: bool = False, dry_run: bool = False) -> dict:
    """
    Forma fija, nunca lanza. Devuelve que ha pasado y por que.
    """

    salida = {
        "guardada": False,
        "ruta": None,
        "fecha": None,
        "bytes": 0,
        "reason": None,
    }

    try:
        if not ORIGEN.exists():
            return {
                **salida,
                "reason": (
                    f"No hay foto que guardar: {ORIGEN} no existe."
                ),
            }

        crudo = ORIGEN.read_text(encoding="utf-8-sig")

        foto = json.loads(crudo)

        if not isinstance(foto, dict):
            return {
                **salida,
                "reason": "La foto no es un objeto JSON.",
            }

        dia = fecha_de_la_foto(foto)

        if not dia:
            return {
                **salida,
                "reason": (
                    "La foto no trae `meta.generated_at` legible. "
                    "No se le pone fecha a mano: se archivaria "
                    "bajo el dia equivocado y la siguiente "
                    "comparacion saldria mal."
                ),
            }

        destino = DESTINO / f"{dia}.json"

        if destino.exists() and not forzar:
            return {
                **salida,
                "fecha": dia,
                "ruta": str(destino.relative_to(RAIZ)),
                "reason": (
                    f"Ya hay foto del {dia}. Una al dia basta; "
                    f"con --forzar se reescribe."
                ),
            }

        # Compacta: el `indent` son ~487 KB de espacios por foto.
        cuerpo = json.dumps(
            foto,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )

        if dry_run:
            return {
                **salida,
                "fecha": dia,
                "ruta": str(destino.relative_to(RAIZ)),
                "bytes": len(cuerpo.encode("utf-8")),
                "reason": (
                    f"--dry-run: se guardaria la foto del {dia} "
                    f"({len(cuerpo.encode('utf-8')) / 1024:.1f} KB)."
                ),
            }

        DESTINO.mkdir(parents=True, exist_ok=True)

        destino.write_text(cuerpo, encoding="utf-8")

        return {
            "guardada": True,
            "ruta": str(destino.relative_to(RAIZ)),
            "fecha": dia,
            "bytes": len(cuerpo.encode("utf-8")),
            "reason": (
                f"Foto del {dia} guardada: "
                f"{len(cuerpo.encode('utf-8')) / 1024:.1f} KB."
            ),
        }

    except Exception as error:                      # noqa: BLE001
        return {
            **salida,
            "reason": (
                f"No se pudo guardar la foto: "
                f"{type(error).__name__}: {error}"
            ),
        }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Guarda una foto al dia en data/fotos/."
    )

    parser.add_argument(
        "--forzar",
        action="store_true",
        help="Reescribe la foto de hoy si ya existe.",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Dice que haria, sin escribir.",
    )

    args = parser.parse_args()

    resultado = guardar(
        forzar=args.forzar,
        dry_run=args.dry_run,
    )

    print(resultado["reason"])

    if resultado["ruta"]:
        print(f"  {resultado['ruta']}")

    # Que no haya foto nueva no es un fallo: es lo normal en las
    # otras diecinueve vueltas del dia.
    return 0


if __name__ == "__main__":
    sys.exit(main())
