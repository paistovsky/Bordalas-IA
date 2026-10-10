"""
EL RELOJ FALSO: correr la verja como si fuera otro dia (10/10/2026).

POR QUE

    El 09/10, de 15:07 a 19:07, cinco vueltas del ciclo salieron
    rojas sin que nadie tocara nada: la orden del gestor caducaba a
    las 15:00 y una guardia leia el reloj real. La verja estaba verde
    por la manana y roja por la tarde. Una bomba con fecha.

COMO SE USA (no lo carga nadie salvo que se pida)

    RELOJ_FALSO=2026-10-16T19:00:00+00:00 \\
    PYTHONPATH=scripts/reloj_falso \\
    python3 scripts/run_validation_gate.py

    Se carga como `usercustomize` (no `sitecustomize`: ese nombre ya
    lo usa el vigilante de la verja, scripts/vigila_data, y lo
    taparia). La verja pasa el entorno a cada guardia, asi que todas
    ven la misma hora falsa: datetime.now/utcnow/today, date.today y
    time.time, desplazados a RELOJ_FALSO. El tiempo sigue corriendo.

COMPROBADO (10/10/2026)

    El codigo de ANTES del arreglo (b11cb53c^) con RELOJ_FALSO el
    09/10 a las 15:30 de Madrid: FALLA 1 de 200,
    test_la_orden_del_gestor_v1 (la misma que fallo de verdad). El
    08/10: 200/200. Main de hoy, el 16/10, el 31/10 y el 31/12: 200/200.

CUANDO

    Antes de cada plazo con fecha (caducidad de la orden, cierre de
    jornada, cambio de hora): una vuelta de la verja con el reloj en
    esa fecha. Sin RELOJ_FALSO no hace nada.
"""

import os

if os.environ.get("RELOJ_FALSO"):

    import datetime as _dt
    import time as _t

    _destino = _dt.datetime.fromisoformat(os.environ["RELOJ_FALSO"])
    _desfase = _destino.timestamp() - _t.time()
    _hora_real = _t.time

    def _ahora():
        return _hora_real() + _desfase

    _t.time = _ahora

    class _FechaHora(_dt.datetime):
        @classmethod
        def now(cls, tz=None):
            r = _dt.datetime.fromtimestamp(_ahora(), tz)
            return cls(*r.timetuple()[:6], r.microsecond, tzinfo=r.tzinfo)

        @classmethod
        def utcnow(cls):
            r = _dt.datetime.utcfromtimestamp(_ahora())
            return cls(*r.timetuple()[:6], r.microsecond)

        @classmethod
        def today(cls):
            return cls.now()

    class _Fecha(_dt.date):
        @classmethod
        def today(cls):
            r = _dt.date.fromtimestamp(_ahora())
            return cls(r.year, r.month, r.day)

    _dt.datetime = _FechaHora
    _dt.date = _Fecha
