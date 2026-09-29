"""
La verja no sale a la red (29/09/2026).

SINTOMA

    La regla «ninguna guardia sale a internet» existia y nada la
    hacia cumplir. El 28/09 una corrida local de la verja escribio
    311 lineas en `data/calendar/calendar_changes.jsonl`, bajadas
    de la web de LaLiga. Con la red cortada, el 29/09: 9 guardias
    intentaban salir, las 194 siguieron en verde y el calendario no
    se toco.

LO QUE VIGILAN ESTAS GUARDIAS

    1. Con `VERJA_SIN_RED=1`, una conexion fuera de la maquina se
       corta con `OSError` y deja su marca para la verja.
    2. La propia maquina (127.0.0.1) sigue abierta: eso no es red.
    3. La verja enciende el corte y quita el proxy a cada guardia.

REGLA 23

    Ni una conexion real sale de aqui: la direccion de fuera es de
    la red de documentacion (192.0.2.1, RFC 5737) y el corte actua
    antes de conectar. El proceso hijo lleva su propio entorno.
"""

from __future__ import annotations

import os
import subprocess
import sys

from pathlib import Path


RAIZ = Path(__file__).parents[2]

VIGILANTE = RAIZ / "scripts" / "vigila_data"

HIJO = r"""
import socket, sys

fuera = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
fuera.settimeout(1)
try:
    fuera.connect(("192.0.2.1", 9))
    print("FUERA:CONECTO")
except OSError as error:
    print("FUERA:" + ("CORTADO" if "no sale a la red" in str(error) else "OTRO"))

servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
servidor.bind(("127.0.0.1", 0))
servidor.listen(1)
dentro = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
dentro.settimeout(1)
try:
    dentro.connect(servidor.getsockname())
    print("DENTRO:CONECTO")
except OSError:
    print("DENTRO:CORTADO")
"""


def _hijo(sin_red: bool):

    entorno = {
        k: v for k, v in os.environ.items()
        if k.lower() not in {"http_proxy", "https_proxy", "all_proxy"}
    }

    entorno.pop("VERJA_SIN_RED", None)

    if sin_red:
        entorno["VERJA_SIN_RED"] = "1"

    entorno["PYTHONPATH"] = str(VIGILANTE)

    return subprocess.run(
        [sys.executable, "-c", HIJO],
        capture_output=True,
        text=True,
        env=entorno,
        timeout=60,
    )


def test_fuera_se_corta_y_deja_marca() -> None:

    proceso = _hijo(sin_red=True)

    assert "FUERA:CORTADO" in proceso.stdout, (proceso.stdout, proceso.stderr)

    assert "VIGILANTE-RED: 192.0.2.1:9" in proceso.stderr, proceso.stderr


def test_la_propia_maquina_sigue_abierta() -> None:

    proceso = _hijo(sin_red=True)

    assert "DENTRO:CONECTO" in proceso.stdout, (proceso.stdout, proceso.stderr)


def test_la_verja_enciende_el_corte_y_quita_el_proxy() -> None:

    texto = (RAIZ / "scripts" / "run_validation_gate.py").read_text(
        encoding="utf-8"
    )

    assert 'entorno["VERJA_SIN_RED"] = "1"' in texto, (
        "la verja ya no corta la red a las guardias"
    )

    assert '"HTTPS_PROXY"' in texto and "entorno.pop(_proxy" in texto, (
        "la verja ya no quita el proxy: con el, todo sale por "
        "127.0.0.1 y el corte no ve nada"
    )


TESTS = [
    test_fuera_se_corta_y_deja_marca,
    test_la_propia_maquina_sigue_abierta,
    test_la_verja_enciende_el_corte_y_quita_el_proxy,
]


def main() -> None:
    fallos = 0

    for test in TESTS:
        try:
            test()
            print(f"OK   {test.__name__}")

        except AssertionError as error:
            fallos += 1
            print(f"FALLA {test.__name__}: {error}")

    print("=" * 60)
    print(
        f"LA VERJA NO SALE A LA RED V1: {len(TESTS) - fallos}/"
        f"{len(TESTS)} OK"
    )
    print("=" * 60)

    if fallos:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
