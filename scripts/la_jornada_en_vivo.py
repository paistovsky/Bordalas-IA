"""
LA JORNADA EN VIVO (11/10/2026)

POR QUE EXISTE

    El 11/10 el gestor dio por puntuado con 0 a Diego Rico cuando su
    partido (Betis-Osasuna) era esa misma tarde, y situo a Olasagasti en
    la Real Sociedad sin mirarlo. Leccion del dueño: «empaparse de todo
    cuando hay liga». Esto lo contesta con datos y no de memoria:

        por cada jugador de nuestro once -> su equipo (de Biwenger), su
        partido de la jornada (del calendario), si ya se jugo, se esta
        jugando o falta, y los puntos que lleva en la jornada.

USO

    python3 -I scripts/la_jornada_en_vivo.py STATUS.json [MARCADOR_PREVIO.json]

    STATUS.json: el `dashboard/data/status.json` de la ultima vuelta
    (artefacto del ciclo). MARCADOR_PREVIO.json: un `marcador.json` de
    antes de empezar la jornada (para restar totales). Sin el, no hay
    puntos de jornada, solo el estado de los partidos.

    Solo lee. Nunca escribe en Biwenger.
"""

from __future__ import annotations

import json
import sys
import unicodedata

from datetime import datetime, timedelta, timezone
from pathlib import Path


RAIZ = Path(__file__).parents[1]
CALENDARIO = RAIZ / "data" / "calendar" / "laliga_calendar.json"
MARCADOR = RAIZ / "data" / "intelligence" / "marcador.json"
DURACION = timedelta(minutes=115)
SOBRA = {"cf", "ud", "rcd", "ca", "rc", "club", "fc", "sd", "r", "de",
         "barcelona", "deportivo"}


def _clave(nombre: str) -> str:
    s = unicodedata.normalize("NFKD", str(nombre or "")).encode("ascii", "ignore").decode()
    palabras = [p for p in s.lower().replace(".", " ").split() if p not in SOBRA]
    return " ".join(palabras) or s.lower()


def _mismo_equipo(a: str, b: str) -> bool:
    ka, kb = _clave(a), _clave(b)
    return bool(ka and kb) and (ka in kb or kb in ka)


def el_once_que_empezo(previo: dict | None, status: dict) -> list | None:
    """
    El once que cuenta (17/10/2026): una vez empezada la jornada no se
    admiten cambios, asi que es el `mi_once` de la ultima jornada del
    marcador de ANTES de empezar, no el `lineup` de ahora (que ya puede
    ser el de la siguiente: el 17/10 contaba los 7 puntos de temporada
    de Sergi Cardona, fichado con la J9 empezada). Con las fichas de la
    plantilla de ahora; el que ya no esta, con su nombre del marcador.
    None si el marcador no lo trae.
    """
    try:
        js = (previo or {}).get("jornadas") or {}
        entrada = js[list(js)[-1]] if js else {}
        ids = [str(i) for i in ((entrada.get("mi_once") or {}).get("players") or [])]
        if len(ids) != 11:
            return None
        fichas = {}
        for p in ((status.get("roster") or {}).get("players") or []) + \
                 ((status.get("lineup") or {}).get("players") or []):
            fichas.setdefault(str(p.get("id")), p)
        nombres = entrada.get("nombres") or {}
        return [fichas.get(i) or {"id": int(i), "name": nombres.get(i, i), "team_name": "?"}
                for i in ids]
    except Exception:                               # noqa: BLE001
        return None


def la_jornada(status: dict, calendario: dict, ahora: datetime,
               previo: dict | None = None, marcador: dict | None = None) -> dict:
    once = (el_once_que_empezo(previo, status)
            or [p for p in (status.get("lineup") or {}).get("players") or []])
    # La jornada en curso: la que tiene partidos alrededor de ahora.
    jornada = None
    for m in calendario.get("matchdays") or []:
        ko = [datetime.fromisoformat(x["kickoff"]) for x in m.get("matches") or []]
        if ko and min(ko) - timedelta(days=2) <= ahora <= max(ko) + timedelta(days=1):
            jornada = m
            break
    filas = []
    tot_prev, tot_now = {}, {}
    if previo and marcador:
        def ultimos(mm):
            js = mm.get("jornadas") or {}
            return js[list(js)[-1]].get("totales") or {} if js else {}
        tot_prev, tot_now = ultimos(previo), ultimos(marcador)
    for p in once:
        equipo = p.get("team_name") or "?"
        partido = None
        for x in (jornada or {}).get("matches") or []:
            if _mismo_equipo(equipo, x["home"]) or _mismo_equipo(equipo, x["away"]):
                partido = x
                break
        if partido is None:
            estado = "SIN PARTIDO EN EL CALENDARIO"
            cuando = ""
        else:
            ko = datetime.fromisoformat(partido["kickoff"])
            cuando = ko.strftime("%d/%m %H:%M") + f" {partido['home']}-{partido['away']}"
            if ahora < ko:
                estado = "FALTA"
            elif ahora < ko + DURACION:
                estado = "JUGANDOSE"
            else:
                estado = "JUGADO"
        pid = str(p.get("id"))
        pts = (tot_now.get(pid, 0) - tot_prev.get(pid, 0)) if tot_prev else None
        filas.append({"nombre": p.get("name"), "equipo": equipo, "partido": cuando,
                      "estado": estado, "puntos": pts,
                      "disponible": p.get("availability")})
    return {"jornada": (jornada or {}).get("matchday"), "filas": filas,
            "puntos": sum(f["puntos"] or 0 for f in filas) if tot_prev else None}


def main() -> None:
    status = json.loads(Path(sys.argv[1]).read_text())
    previo = json.loads(Path(sys.argv[2]).read_text()) if len(sys.argv) > 2 else None
    marcador = json.loads(MARCADOR.read_text()) if previo else None
    r = la_jornada(status, json.loads(CALENDARIO.read_text()),
                   datetime.now(timezone.utc), previo, marcador)
    print(f"Jornada {r['jornada']}  ·  puntos del once: {r['puntos']}")
    for f in r["filas"]:
        pts = "" if f["puntos"] is None else f"{f['puntos']:>3} pts"
        print(f"  {f['nombre'][:18]:18} {f['equipo'][:14]:14} {f['estado']:28} {pts:8} {f['partido']}  [{f['disponible']}]")


if __name__ == "__main__":
    main()
