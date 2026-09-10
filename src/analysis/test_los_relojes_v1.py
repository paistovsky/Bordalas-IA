"""
Los relojes: una sola cadencia, y el cambio de hora se detecta.

SINTOMA

    10/09/2026. El cron paso a ser HORARIO y dos textos se
    quedaron con la cadencia vieja:

        aviso amarillo   "el ciclo corre cada 30"
        lateral          "ciclo 30 min"

    La cuenta atras iba bien -esa lee el cron de verdad- y eran
    los textos los que mentian. Un dato, tres nombres.

    Y por debajo, peor: `STALE_CYCLE_SECONDS = 2 * 30 * 60`
    marcaba "historia" un ciclo perfectamente normal a la hora
    de vida.

CAUSA

    La cadencia estaba escrita a mano en tres sitios y ninguno
    miraba al cron.

CONSECUENCIA

    Ahora hay una autoridad -el cron de `bordalas-live.yml`- y
    dos espejos que esta guardia obliga a coincidir con ella.

EL OTRO RELOJ: LOS CRONES EXTERNOS

    cron-job.org aplica CET aunque le pongas "Europe/Madrid", asi
    que los disparos llevan escrita UNA HORA DE MENOS para que
    ocurran a la hora real que queremos.

    El 25/10/2026, al acabar el horario de verano, esa
    compensacion sobra y los disparos se adelantarian una hora:
    la ventana del reset se abriria con el mercado sin resetear.

    No se recuerda: se detecta. Se le pregunta a la base de zonas
    si Madrid sigue en verano. Doctrina 35, y este es el caso que
    la motivo.
"""

from __future__ import annotations

import re
import shutil
import subprocess

from pathlib import Path


RAIZ = Path(__file__).parents[2]

WORKFLOW = RAIZ / ".github" / "workflows" / "bordalas-live.yml"

RELOJES = RAIZ / "dashboard-v8" / "src" / "lib" / "relojes.js"

TELEMETRIA = RAIZ / "src" / "telemetry" / "dashboard_state.py"


def _lee(ruta: Path) -> str:
    if not ruta.exists():
        raise AssertionError(f"no existe {ruta}")

    return ruta.read_text(encoding="utf-8")


def _sin_comentarios(fuente: str) -> str:
    """
    El codigo, sin las notas que cuentan el incidente.

    Van tres guardias tropezando con lo mismo: el fallo esta
    contado por escrito -"aqui ponia `cycle_minutes || 30`"- y la
    guardia leia esa nota como si fuera codigo vivo. Una guardia
    que obligue a borrar la explicacion para pasar hace dano: la
    proxima persona se encuentra el arreglo sin el motivo.
    """

    limpio = []

    for linea in fuente.splitlines():

        desnuda = linea.lstrip()

        if desnuda.startswith(("#", "//", "*", "/*")):
            continue

        limpio.append(linea.split("//")[0])

    return chr(10).join(limpio)


def cron_del_workflow() -> str:
    """El cron que de verdad dispara. Es la autoridad."""

    fuente = _lee(WORKFLOW)

    encontrados = re.findall(
        r"-\s*cron:\s*[\"']([^\"']+)[\"']", fuente
    )

    assert encontrados, (
        "el workflow no declara ningun `cron`: si esto pasa, la "
        "cadencia de la pantalla no la pina nadie"
    )

    return encontrados[0].strip()


def cadencia_del_cron(expresion: str) -> int:
    """
    Cada cuantos minutos dispara un cron de cinco campos.

    Solo se apoya en los dos primeros campos, que es lo que usa
    esta casa. Si algun dia el cron se complica, esta guardia se
    pone roja en vez de mentir.
    """

    partes = expresion.split()

    assert len(partes) == 5, expresion

    minutos, horas = partes[0], partes[1]

    def _cuantos(campo: str, tope: int) -> int:
        if campo == "*":
            return tope

        total = 0

        for trozo in campo.split(","):
            if trozo.startswith("*/"):
                total += tope // int(trozo[2:])
            elif "-" in trozo:
                a, b = trozo.split("-")
                total += int(b) - int(a) + 1
            else:
                total += 1

        return total

    disparos_al_dia = _cuantos(minutos, 60) * _cuantos(horas, 24)

    assert disparos_al_dia > 0, expresion

    # Los disparos NO estan repartidos por igual -el cron salta
    # la madrugada- asi que esto es el hueco entre dos seguidos
    # dentro de la franja activa, que es lo que vive el dueno.
    return 60 // _cuantos(minutos, 60)


# ============================================================
# 1. UNA SOLA CADENCIA
# ============================================================


def test_la_cadencia_sale_del_cron() -> None:
    """
    El cron del workflow manda. Los dos espejos -`relojes.js` y
    `dashboard_state.py`- tienen que decir lo mismo que el.
    """

    cron = cron_del_workflow()

    esperada = cadencia_del_cron(cron)

    # Regla 24: si el calculo diera algo absurdo, la guardia no
    # puede pasar tan contenta.
    assert 1 <= esperada <= 24 * 60, (cron, esperada)

    relojes = _lee(RELOJES)

    assert f'CRON_INTERNO = "{cron}"' in relojes, (
        f"`relojes.js` no lleva el cron real ({cron}): la cuenta "
        f"atras y el cron pueden discrepar"
    )

    telemetria = _lee(TELEMETRIA)

    assert f'CRON_INTERNO = "{cron}"' in telemetria, (
        f"`dashboard_state.py` no lleva el cron real ({cron})"
    )

    encontrada = re.search(
        r"CADENCIA_MINUTOS\s*=\s*(\d+)", telemetria
    )

    assert encontrada, "no hay `CADENCIA_MINUTOS`"

    assert int(encontrada.group(1)) == esperada, (
        f"el cron dispara cada {esperada} min y "
        f"`CADENCIA_MINUTOS` dice {encontrada.group(1)}"
    )


def test_ningun_texto_lleva_la_cadencia_escrita_a_mano() -> None:
    """
    Los dos que mintieron. Si vuelven a escribir un numero, se
    quedaran atras el dia que el cron cambie otra vez.
    """

    app = _sin_comentarios(
        _lee(RAIZ / "dashboard-v8" / "src" / "App.jsx")
    )

    assert "cadenciaEnPalabras" in app, (
        "el aviso amarillo ya no saca la cadencia del cron"
    )

    assert "cycle_minutes" not in app, (
        "el aviso amarillo ha vuelto a leer `cycle_minutes`, que "
        "es un numero escrito a mano en Python"
    )

    lateral = _sin_comentarios(
        _lee(
            RAIZ
            / "dashboard-v8"
            / "src"
            / "components"
            / "Sidebar.jsx"
        )
    )

    assert "cadenciaEnPalabras" in lateral, (
        "el lateral ya no saca la cadencia del cron"
    )

    assert "cycle_minutes" not in lateral, (
        "el lateral ha vuelto a leer `cycle_minutes`"
    )


def test_el_ciclo_no_se_pone_rancio_antes_de_tiempo() -> None:
    """
    `STALE_CYCLE_SECONDS = 2 * 30 * 60` con un ciclo horario
    marcaba "esto es historia" a la hora de vida, o sea en el
    ciclo siguiente. Un aviso que salta siempre no se lee.
    """

    from src.telemetry.dashboard_state import (
        CADENCIA_MINUTOS,
        STALE_CYCLE_SECONDS,
    )

    assert STALE_CYCLE_SECONDS == 2 * CADENCIA_MINUTOS * 60, (
        STALE_CYCLE_SECONDS,
        CADENCIA_MINUTOS,
    )

    # Un ciclo normal, con retraso normal, NO es historia.
    assert STALE_CYCLE_SECONDS > CADENCIA_MINUTOS * 60 * 1.5


# ============================================================
# 2. EL CAMBIO DE HORA SE DETECTA, NO SE RECUERDA
# ============================================================


def test_la_compensacion_de_cron_job_esta_escrita_donde_se_ve() -> None:
    """
    Una compensacion a mano que solo vive en la cabeza de alguien
    es una bomba con fecha. Va junto a la definicion de los
    relojes, con la fecha en que caduca.
    """

    relojes = _lee(RELOJES)

    assert "cron-job.org" in relojes, (
        "la compensacion de los crones externos no esta escrita "
        "donde vive la definicion de los relojes"
    )

    assert "25 DE OCTUBRE DE 2026" in relojes, (
        "no se dice cuando caduca la compensacion"
    )

    for cron in ("45 3 * * *", "50 3 * * *", "15 6 * * *"):
        assert cron in relojes, (
            f"falta el cron externo `{cron}` tal cual esta puesto"
        )


def test_el_bot_avisa_del_cambio_de_hora() -> None:
    """
    LO QUE EVITA TENER QUE ACORDARSE.

    Se ejecuta de verdad `avisoDelCambioDeHora` con dos fechas:
    una de verano -no avisa- y una de invierno -avisa, y dice que
    crones poner-.

    Se le pregunta a la base de zonas. Ni una fecha codificada ni
    un `+1` escrito: doctrina 35.
    """

    if shutil.which("node") is None:
        print("     AVISO: sin `node` no se puede ejecutar.")
        return

    guion = (
        'import { avisoDelCambioDeHora } from '
        '"./src/lib/relojes.js";\n'
        'const verano = avisoDelCambioDeHora('
        'new Date("2026-09-10T12:00:00Z"));\n'
        'const invierno = avisoDelCambioDeHora('
        'new Date("2026-11-15T12:00:00Z"));\n'
        'console.log(JSON.stringify({\n'
        '  verano: verano === null,\n'
        '  invierno: invierno && invierno.motivo,\n'
        '  desfase: invierno && invierno.desfaseMadrid,\n'
        '  crones: invierno && invierno.cambiar.map('
        '(c) => c.nuevo)\n'
        '}));\n'
    )

    carpeta = RAIZ / "dashboard-v8"

    fichero = carpeta / "_aviso_cambio_hora.mjs"

    try:
        fichero.write_text(guion, encoding="utf-8")

        salida = subprocess.run(
            ["node", str(fichero)],
            cwd=str(carpeta),
            capture_output=True,
            text=True,
            timeout=120,
        )

    finally:
        if fichero.exists():
            fichero.unlink()

    assert salida.returncode == 0, (
        salida.stdout + salida.stderr
    )

    import json

    visto = json.loads(salida.stdout.strip().splitlines()[-1])

    assert visto["verano"] is True, (
        "avisa en pleno verano, cuando la compensacion es "
        "correcta: un aviso que salta siempre no se lee"
    )

    assert visto["invierno"] == "FIN_DEL_HORARIO_DE_VERANO", visto

    assert visto["desfase"] == 60, (
        f"Madrid en invierno son +60 y la base de zonas dice "
        f"{visto['desfase']}"
    )

    # Y dice EXACTAMENTE los crones que hay que poner.
    assert visto["crones"] == [
        "45 4 * * *",
        "50 4 * * *",
        "15 7 * * *",
    ], visto


def test_ningun_desfase_horario_escrito_a_mano() -> None:
    """
    DOCTRINA 35, y este es el caso que la motivo.

    El desfase de una zona se le pide SIEMPRE a la base de
    zonas. Escribirlo como +1 o +2 acierta diez meses al ano y
    falla justo el dia del cambio, que es el dia en que importa.
    """

    relojes = _lee(RELOJES)

    assert "Europe/Madrid" in relojes, (
        "la zona no se pide por nombre"
    )

    assert "Intl.DateTimeFormat" in relojes, (
        "el desfase se esta codificando a mano"
    )

    codigo = _sin_comentarios(relojes)

    # LO QUE SE PROHIBE ES EL DESFASE DE MADRID.
    #
    # `CET_DE_CRON_JOB = 60` SI puede estar escrito: CET es +1
    # por definicion y no cambia nunca. Lo que cambia es Madrid,
    # y por eso Madrid se pregunta y CET se escribe.
    #
    # Y lo que se cazo aqui de verdad: `desfaseMadrid` tenia un
    # `return 120` de reserva "porque rige diez meses al ano".
    # Acertaba diez meses y fallaba justo los dos en que el
    # desfase importa, callado.
    assert "return 120" not in codigo, (
        "`desfaseMadrid` ha vuelto a inventarse el horario de "
        "verano cuando no puede preguntarlo. Doctrina 35 y 36 a "
        "la vez: un desfase a mano, y un defecto benigno tapando "
        "un 'no se sabe'."
    )

    for prohibido in ("= 120;", "* 120 *", "+ 120)"):
        assert prohibido not in codigo, (
            f"hay un desfase de Madrid escrito a mano: "
            f"`{prohibido}`"
        )
        assert prohibido not in codigo, (
            f"hay un desfase horario escrito a mano: "
            f"`{prohibido}`"
        )


TESTS = [
    test_la_cadencia_sale_del_cron,
    test_ningun_texto_lleva_la_cadencia_escrita_a_mano,
    test_el_ciclo_no_se_pone_rancio_antes_de_tiempo,
    test_la_compensacion_de_cron_job_esta_escrita_donde_se_ve,
    test_el_bot_avisa_del_cambio_de_hora,
    test_ningun_desfase_horario_escrito_a_mano,
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
        f"LOS RELOJES V1: {len(TESTS) - fallos}/{len(TESTS)} OK"
    )
    print("=" * 60)

    if fallos:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
