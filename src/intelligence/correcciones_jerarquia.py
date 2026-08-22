from __future__ import annotations

"""
Cuando FutbolFantasy se equivoca de escalon.

EL CASO (22/08/2026)

    "El caso es que Mangala este año es clave en el Getafe, viene
     mal en FF."

    FF lo tenia como ROTACION. Y ese dato es el mas pesado de todo
    el sistema: un escalon de jerarquia mueve 307.200 en el score
    del once -medido-, ordena el XI, decide el veto de compra y
    elige a quien se vende para tapar deuda.

    Aquel dia, Mangala tenia tres cosas en contra a la vez: la
    etiqueta mal, una vara que ignora los puntos, y un plan de
    deuda que usa esa vara. El plan A era venderlo con "coste
    deportivo: ninguno" siendo el jugador que mas puntos llevaba
    del once. Lo paro el dueño a mano.

QUE ES ESTO Y QUE NO ES

    Es una correccion puntual y CADUCA de la jerarquia, escrita a
    mano, versionada y visible.

    No es un sitio para mejorar a los propios. Solo toca el
    ESCALON -lo estructural, lo que FF tarda semanas en
    actualizar-. El PORCENTAJE de titularidad de la semana no se
    toca: eso es un pronostico fresco y falsearlo es otra cosa
    completamente distinta.

POR QUE CADUCA

    Una correccion sin fecha de muerte deja de ser una correccion
    y pasa a ser una opinion fosil. Dentro de un mes puede que FF
    tenga razon y tu no, y nadie se va a acordar de revisarlo.

    Caducada no se aplica, y se dice en pantalla que caduco. El
    silencio es lo unico que no se permite.

DONDE VIVE

    `config/correcciones_jerarquia.json`, versionado. NO en
    `data/`, que esta en .gitignore y no llegaria a GitHub
    Actions: la correccion no serviria de nada justo donde se
    toman las decisiones.

EL DESTINO

    Esto es el parche honesto, no la solucion. La solucion es que
    el sistema lo detecte solo: si FF dice Rotacion y el jugador
    lleva dos de dos titularidades, la evidencia observada deberia
    pesar mas que la etiqueta. Con dos jornadas jugadas todavia no
    se puede; dentro de un mes, si.
"""

import json

from datetime import date, timedelta
from pathlib import Path


ARCHIVO = Path("config") / "correcciones_jerarquia.json"


# Los escalones de FutbolFantasy, con su valor. Es la misma
# escalera que usa `player_value_engine`; aqui se necesita al
# reves -de nombre a numero- porque una correccion se escribe con
# palabras, que es como piensa quien la escribe.
ESCALONES = {
    "DIOS": (60, "Dios"),
    "CLAVE": (50, "Clave"),
    "IMPORTANTE": (40, "Importante"),
    "ROTACION": (30, "Rotación"),
    "REVULSIVO": (25, "Revulsivo"),
    "RESERVA": (20, "Reserva"),
    "DESCARTE": (10, "Descarte"),
}


# Cuanto vive una correccion si no se le pone fecha. Un mes es
# tiempo de sobra para que FF se entere de un cambio de rol.
DIAS_POR_DEFECTO = 30


def _normalizar(texto) -> str:
    """
    'Importante', 'IMPORTANTE', 'rotación' -> la misma clave.
    """

    import unicodedata

    crudo = unicodedata.normalize("NFD", str(texto or ""))

    sin_tildes = "".join(
        c for c in crudo
        if unicodedata.category(c) != "Mn"
    )

    return sin_tildes.strip().upper()


def _fecha(valor):
    try:
        return date.fromisoformat(str(valor))
    except (TypeError, ValueError):
        return None


def load_corrections(
    path: Path | str | None = None,
    hoy: date | None = None,
) -> dict:
    """
    Lee el fichero y separa lo que se aplica de lo que no.

    Nunca lanza. Un fichero roto no puede tumbar el ciclo: se
    devuelve vacio y se dice por que.
    """

    hoy = hoy or date.today()

    resultado = {
        "available": True,
        "aplicadas": {},
        "caducadas": [],
        "invalidas": [],
        "reason": None,
    }

    try:
        ruta = Path(path) if path else ARCHIVO

        if not ruta.exists():
            resultado["reason"] = (
                "No hay correcciones manuales de jerarquia."
            )
            return resultado

        datos = json.loads(ruta.read_text(encoding="utf-8"))

    except Exception as error:
        return {
            **resultado,
            "available": False,
            "reason": (
                f"No se pudo leer {ARCHIVO}: "
                f"{type(error).__name__}: {error}"
            ),
        }

    entradas = (
        datos.get("correcciones")
        if isinstance(datos, dict)
        else datos
    )

    for entrada in (entradas or []):

        if not isinstance(entrada, dict):
            continue

        motivo_invalida = None

        try:
            player_id = int(entrada.get("player_id"))
        except (TypeError, ValueError):
            player_id = None
            motivo_invalida = "sin player_id"

        clave = _normalizar(entrada.get("jerarquia"))

        if not motivo_invalida and clave not in ESCALONES:
            motivo_invalida = (
                f"escalon desconocido: {entrada.get('jerarquia')!r}. "
                f"Los validos son: {', '.join(ESCALONES)}"
            )

        # Un cambio sin motivo escrito no se aplica. Dentro de tres
        # semanas, "Mangala = Importante" sin explicacion no se
        # puede ni revisar ni defender.
        if not motivo_invalida and not str(
            entrada.get("motivo") or ""
        ).strip():
            motivo_invalida = "sin motivo escrito"

        if motivo_invalida:
            resultado["invalidas"].append({
                **entrada,
                "problema": motivo_invalida,
            })
            continue

        desde = _fecha(entrada.get("desde")) or hoy

        caduca = _fecha(entrada.get("caduca")) or (
            desde + timedelta(days=DIAS_POR_DEFECTO)
        )

        valor, etiqueta = ESCALONES[clave]

        ficha = {
            "player_id": player_id,
            "jugador": entrada.get("jugador"),
            "hierarchy_value": valor,
            "hierarchy_label": etiqueta,
            "motivo": entrada.get("motivo"),
            "desde": desde.isoformat(),
            "caduca": caduca.isoformat(),
            "dias_restantes": (caduca - hoy).days,
        }

        if caduca < hoy:
            resultado["caducadas"].append(ficha)
            continue

        resultado["aplicadas"][player_id] = ficha

    resultado["reason"] = (
        f"{len(resultado['aplicadas'])} correccion(es) viva(s)"
        + (
            f", {len(resultado['caducadas'])} caducada(s)"
            if resultado["caducadas"]
            else ""
        )
        + (
            f", {len(resultado['invalidas'])} sin aplicar"
            if resultado["invalidas"]
            else ""
        )
        + "."
    )

    return resultado


def apply_corrections(
    lookup: dict,
    corrections: dict | None = None,
) -> dict:
    """
    Cambia el escalon en el lookup y deja escrito que se cambio.

    Modifica el lookup que se le pasa y lo devuelve. La marca es
    lo que impide que esto sea una mentira: `hierarchy_source` en
    MANUAL y la correccion entera colgando, para que la pantalla
    pueda pintarla distinta.

    A un jugador que no esta en el tablero de FF NO se le inventa
    una ficha: sin porcentaje de titularidad no hay nada que
    corregir, y meterlo a medias seria peor.
    """

    if corrections is None:
        corrections = load_corrections()

    aplicadas = (corrections or {}).get("aplicadas") or {}

    if not aplicadas:
        return lookup

    for player_id, correccion in aplicadas.items():

        ficha = (lookup or {}).get(int(player_id))

        if not isinstance(ficha, dict):
            correccion["aplicada"] = False
            correccion["problema"] = (
                "El jugador no esta en el tablero de FutbolFantasy: "
                "sin pronostico no hay jerarquia que corregir."
            )
            continue

        jerarquia = dict(ficha.get("hierarchy") or {})

        correccion["aplicada"] = True
        correccion["hierarchy_before"] = jerarquia.get("label")
        correccion["hierarchy_before_value"] = jerarquia.get("value")

        jerarquia["value"] = correccion["hierarchy_value"]
        jerarquia["label"] = correccion["hierarchy_label"]
        jerarquia["source"] = "MANUAL"

        ficha["hierarchy"] = jerarquia
        ficha["hierarchy_value"] = correccion["hierarchy_value"]
        ficha["hierarchy_label"] = correccion["hierarchy_label"]

        # La marca. Sin esto, una jerarquia tocada a mano no se
        # distingue de una de FF, que es exactamente la mentira
        # silenciosa que esto viene a evitar.
        ficha["hierarchy_source"] = "MANUAL"
        ficha["hierarchy_override"] = correccion

    return lookup


def describe(corrections: dict | None = None) -> dict:
    """
    Lo que necesita la pantalla para contarlo.
    """

    if corrections is None:
        corrections = load_corrections()

    aplicadas = list(
        (corrections.get("aplicadas") or {}).values()
    )

    return {
        "available": bool(corrections.get("available")),
        "activas": len(
            [c for c in aplicadas if c.get("aplicada") is not False]
        ),
        "caducadas": len(corrections.get("caducadas") or []),
        "invalidas": len(corrections.get("invalidas") or []),
        "correcciones": aplicadas,
        "sin_aplicar": (
            [c for c in aplicadas if c.get("aplicada") is False]
            + list(corrections.get("invalidas") or [])
        ),
        "reason": corrections.get("reason"),
    }
