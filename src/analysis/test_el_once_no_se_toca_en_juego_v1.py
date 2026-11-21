"""
EL ONCE NO SE TOCA EN JUEGO (21/11/2026). Guardias de
`BORDALAS_EL_ONCE_NO_SE_TOCA_EN_JUEGO`
(`src/analysis/el_once_no_se_toca_en_juego.py` y sus dos enganches: el
plan de `decision_orchestrator` y el GUARDAR XI de
`autopilot_executor.execute_autopilot_decision`).

EL CASO (sab 21/11, vuelta de las 07:15, #3098)

    Con la J13 en juego (vie 20/11 21:00 - lun 23/11 21:00) el monitor
    guardo el once «para la Jornada 14» y Biwenger lo aplico a la J13:
    Remiro por Gulacsi.

QUE SE COMPRUEBA

    1. Nace apagado, se lee en UN sitio, tiene frase en el tablon y no
       hace nada al importarse.
    2. Apagado, nada cambia: ni el plan (el ayudante del orquestador da
       False) ni el ejecutor (escribe con la ronda en juego, como main).
    3. El caso de hoy: encendido, a las 07:15 del sab 21/11 la J13 esta
       en juego; el ejecutor no escribe (ROUND_IN_PROGRESS, sin
       escritura, success True, el escritor ni se construye) y el plan
       no propone el once.
    4. Los bordes: un minuto antes del primer partido se guarda; en el
       primer partido no; hasta 3 h despues del ultimo no; un minuto
       despues, si. Un aplazado entre semana (ronda aparte) tambien
       bloquea mientras se juega.
    5. Sin calendario (ilegible, vacio, basura) NO bloquea: lo de
       siempre.
    6. Nunca lanza.
"""

import json
import os
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

RAIZ = Path(__file__).parents[2]
sys.path.insert(0, str(RAIZ))

from src.analysis import el_once_no_se_toca_en_juego as M   # noqa: E402
from src.analysis import la_proxima_jornada as LPJ          # noqa: E402

ENV = "BORDALAS_EL_ONCE_NO_SE_TOCA_EN_JUEGO"
UTC = timezone.utc


def _partidos(jornada, horas):
    return {"matchday": jornada,
            "matches": [{"kickoff": h, "home": f"L{i}", "away": f"V{i}"}
                        for i, h in enumerate(horas)]}


# El calendario de verdad de la J13 y la J14 (hora de Madrid, sin zona,
# como lo trae LaLiga) y el adelantado de la J23 del mie 02/12.
CALENDARIO = {"matchdays": [
    _partidos(13, ["2026-11-20T21:00:00", "2026-11-21T14:00:00", "2026-11-21T16:15:00",
                   "2026-11-21T18:30:00", "2026-11-21T21:00:00", "2026-11-22T14:00:00",
                   "2026-11-22T16:15:00", "2026-11-22T18:30:00", "2026-11-22T21:00:00",
                   "2026-11-23T21:00:00"]),
    _partidos(14, ["2026-11-27T21:00:00", "2026-11-28T14:00:00", "2026-11-28T16:15:00",
                   "2026-11-28T18:30:00", "2026-11-28T21:00:00", "2026-11-29T14:00:00",
                   "2026-11-29T16:15:00", "2026-11-29T18:30:00", "2026-11-29T21:00:00",
                   "2026-11-30T21:00:00"]),
    _partidos(23, ["2026-12-02T19:00:00", "2026-12-02T21:30:00",
                   "2027-02-13T14:00:00", "2027-02-13T16:15:00", "2027-02-13T18:30:00",
                   "2027-02-14T14:00:00", "2027-02-14T16:15:00", "2027-02-14T18:30:00"]),
]}


class _Entorno:
    """Pone o quita el interruptor y lo deja como estaba."""

    def __init__(self, valor):
        self.valor = valor

    def __enter__(self):
        self.antes = os.environ.get(ENV)
        if self.valor is None:
            os.environ.pop(ENV, None)
        else:
            os.environ[ENV] = self.valor
        return self

    def __exit__(self, *a):
        if self.antes is None:
            os.environ.pop(ENV, None)
        else:
            os.environ[ENV] = self.antes


class _Calendario:
    """El calendario de produccion apuntando a un fichero de prueba."""

    def __init__(self, datos):
        self.datos = datos

    def __enter__(self):
        self.antes = LPJ.CALENDARIO
        self.dir = tempfile.TemporaryDirectory()
        ruta = Path(self.dir.name) / "laliga_calendar.json"
        if self.datos is not None:
            ruta.write_text(self.datos if isinstance(self.datos, str)
                            else json.dumps(self.datos))
        LPJ.CALENDARIO = ruta
        return self

    def __exit__(self, *a):
        LPJ.CALENDARIO = self.antes
        self.dir.cleanup()


def _ahora_en_juego():
    """Un calendario con una ronda que se esta jugando AHORA (para los
    enganches, que miran el reloj de verdad)."""
    ahora = datetime.now(UTC)
    horas = [(ahora - timedelta(hours=20)).isoformat(),
             (ahora - timedelta(hours=1)).isoformat(),
             (ahora + timedelta(hours=30)).isoformat()]
    return {"matchdays": [_partidos(13, horas)]}


def _ahora_sin_ronda():
    ahora = datetime.now(UTC)
    return {"matchdays": [_partidos(14, [(ahora + timedelta(days=4)).isoformat(),
                                         (ahora + timedelta(days=6)).isoformat()])]}


# ------------------------------------------------------------
# El ejecutor con un escritor de mentira
# ------------------------------------------------------------

class _Escritor:
    construidos = 0
    llamadas: list = []

    def __init__(self):
        type(self).construidos += 1

    def save_lineup(self, **kw):
        type(self).llamadas.append(kw)
        return {"sent": False, "success": False}


def _decision():
    once = [{"id": 1000 + i} for i in range(11)]
    return {
        "action": "SAVE_LINEUP",
        "executable": True,
        "temporal_gate": {"phase": "NORMAL", "operations_locked": False,
                          "hard_safety_mode": False},
        "data": {"lineup_monitor": {"lineup": {
            "selected": once, "playable_count": 11, "formation_name": "4-4-2"}}},
    }


def _ejecutar():
    from src.actions import autopilot_executor as E
    from src.actions import el_rastro

    antes_w, antes_r = E.BiwengerWriteClient, el_rastro.apuntar_escritura
    _Escritor.construidos = 0
    _Escritor.llamadas = []
    E.BiwengerWriteClient = _Escritor
    el_rastro.apuntar_escritura = lambda *a, **k: None
    try:
        return E.execute_autopilot_decision(_decision(), execute=True)
    finally:
        E.BiwengerWriteClient = antes_w
        el_rastro.apuntar_escritura = antes_r


# ------------------------------------------------------------
# 1. Nace apagado, un lector, su frase
# ------------------------------------------------------------

def test_nace_apagado_un_lector_y_su_frase():
    assert M.ENV == ENV
    with _Entorno(None):
        assert M.activo() is False
    for v in ("", "0", "off", "2", "no"):
        with _Entorno(v):
            assert M.activo() is False, v
    for v in ("1", "true", "si", "sí", "yes", "on", " TRUE "):
        with _Entorno(v):
            assert M.activo() is True, v
    from src.analysis.el_paso_0 import ENCENDIDO
    assert M.ENCENDIDO == ENCENDIDO
    for v in ENCENDIDO:
        with _Entorno(v):
            assert M.activo() is True, v
    # Se lee en un sitio: solo el modulo nombra el entorno.
    lectores = []
    for camino in (RAIZ / "src").rglob("*.py"):
        if camino.name.startswith("test_") or "PRE_" in camino.name or "BACKUP" in camino.name:
            continue
        texto = camino.read_text(errors="ignore")
        if ENV in texto and camino.name != "el_tablon.py":
            lectores.append(camino.name)
    assert lectores == ["el_once_no_se_toca_en_juego.py"], lectores
    from src.telemetry.el_tablon import QUE_HACE
    assert ENV in QUE_HACE and len(QUE_HACE[ENV]) > 40


# ------------------------------------------------------------
# 2. Apagado, nada cambia
# ------------------------------------------------------------

def test_apagado_nada_cambia():
    from src.analysis import decision_orchestrator as O
    with _Entorno(None), _Calendario(_ahora_en_juego()):
        assert M.por_que_no_se_guarda() is None
        assert O._el_once_no_se_toca() is False
        r = _ejecutar()
        assert _Escritor.construidos == 1 and len(_Escritor.llamadas) == 1, r
        assert r.get("status") != "ROUND_IN_PROGRESS", r


# ------------------------------------------------------------
# 3. El caso de hoy
# ------------------------------------------------------------

def test_el_caso_de_hoy():
    hoy = datetime(2026, 11, 21, 6, 15, tzinfo=UTC)
    with _Entorno("1"):
        motivo = M.por_que_no_se_guarda(hoy, CALENDARIO)
        assert motivo and "J13" in motivo and "20/11 21:00" in motivo, motivo
        assert M.en_juego(hoy, CALENDARIO).startswith("J13")
    from src.analysis import decision_orchestrator as O
    with _Entorno("1"), _Calendario(_ahora_en_juego()):
        assert O._el_once_no_se_toca() is True
        r = _ejecutar()
        assert r["status"] == "ROUND_IN_PROGRESS", r
        assert r["write_performed"] is False and r["success"] is True, r
        assert r["action"] == "SAVE_LINEUP"
        assert "EL_ONCE_NO_SE_TOCA_EN_JUEGO" in r["reason"], r
        assert _Escritor.construidos == 0 and not _Escritor.llamadas
    # Encendido y sin ronda en juego: se escribe como siempre.
    with _Entorno("1"), _Calendario(_ahora_sin_ronda()):
        assert O._el_once_no_se_toca() is False
        r = _ejecutar()
        assert len(_Escritor.llamadas) == 1, r
        assert r.get("status") != "ROUND_IN_PROGRESS", r


def test_el_plan_lleva_el_enganche():
    """El SAVE_LINEUP del plan pasa por el ayudante (lectura del codigo:
    el plan entero necesita una foto de Biwenger)."""
    texto = (RAIZ / "src/analysis/decision_orchestrator.py").read_text()
    trozo = texto[texto.index("# CAMBIO RELEVANTE DEL XI"):]
    trozo = trozo[:trozo.index('"SAVE_LINEUP"')]
    assert "and not _el_once_no_se_toca()" in trozo


# ------------------------------------------------------------
# 4. Los bordes
# ------------------------------------------------------------

def test_los_bordes():
    madrid = timezone(timedelta(hours=1))
    primero = datetime(2026, 11, 20, 21, 0, tzinfo=madrid)
    ultimo = datetime(2026, 11, 23, 21, 0, tzinfo=madrid)
    minuto = timedelta(minutes=1)
    with _Entorno("1"):
        assert M.por_que_no_se_guarda(primero - minuto, CALENDARIO) is None
        assert M.por_que_no_se_guarda(primero, CALENDARIO)
        assert M.por_que_no_se_guarda(ultimo + timedelta(hours=3), CALENDARIO)
        assert M.por_que_no_se_guarda(ultimo + timedelta(hours=3) + minuto, CALENDARIO) is None
        # Entre jornadas (mar 24/11 10:00) se guarda.
        assert M.por_que_no_se_guarda(datetime(2026, 11, 24, 9, 0, tzinfo=UTC), CALENDARIO) is None
        # El adelantado de la J23 (mie 02/12) bloquea mientras se juega...
        en_el = datetime(2026, 12, 2, 20, 0, tzinfo=madrid)
        assert "J23" in M.por_que_no_se_guarda(en_el, CALENDARIO)
        # ...y el dia antes, no.
        assert M.por_que_no_se_guarda(en_el - timedelta(days=1), CALENDARIO) is None
        # Hora sin zona: UTC.
        assert M.por_que_no_se_guarda(datetime(2026, 11, 21, 6, 15), CALENDARIO)


# ------------------------------------------------------------
# 5. Sin calendario, lo de siempre
# ------------------------------------------------------------

def test_sin_calendario_no_bloquea():
    hoy = datetime(2026, 11, 21, 6, 15, tzinfo=UTC)
    with _Entorno("1"):
        for malo in ({}, {"matchdays": []}, {"matchdays": "x"}, {"matches": [{"kickoff": "no"}]},
                     str(RAIZ / "no_existe.json")):
            assert M.por_que_no_se_guarda(hoy, malo) is None, malo
            assert M.en_juego(hoy, malo) is None, malo
    from src.analysis import decision_orchestrator as O
    for datos in (None, "{no es json", "[]"):
        with _Entorno("1"), _Calendario(datos):
            assert M.por_que_no_se_guarda() is None, datos
            assert O._el_once_no_se_toca() is False, datos
            r = _ejecutar()
            assert len(_Escritor.llamadas) == 1, (datos, r)


# ------------------------------------------------------------
# 6. Nunca lanza
# ------------------------------------------------------------

def test_nunca_lanza():
    with _Entorno("1"):
        for ahora in ("ayer", 12, object(), [], {"a": 1}):
            assert M.por_que_no_se_guarda(ahora, CALENDARIO) is None
            assert M.en_juego(ahora, CALENDARIO) is None
        for cal in (12, object(), [1, 2], {"matchdays": [None, 3, {"matches": None}]}):
            assert M.por_que_no_se_guarda(datetime.now(UTC), cal) is None
    antes = M.activo
    try:
        M.activo = lambda: 1 / 0
        assert M.por_que_no_se_guarda() is None
    finally:
        M.activo = antes


TESTS = [
    test_nace_apagado_un_lector_y_su_frase,
    test_apagado_nada_cambia,
    test_el_caso_de_hoy,
    test_el_plan_lleva_el_enganche,
    test_los_bordes,
    test_sin_calendario_no_bloquea,
    test_nunca_lanza,
]


def main() -> None:
    fallos = 0
    for test in TESTS:
        try:
            test()
            print(f"OK   {test.__name__}")
        except Exception as error:                  # noqa: BLE001
            fallos += 1
            print(f"FALLA {test.__name__}: {type(error).__name__}: {error}")
    print("=" * 60)
    print(f"{len(TESTS) - fallos}/{len(TESTS)} en verde")
    sys.exit(1 if fallos else 0)


if __name__ == "__main__":
    main()
