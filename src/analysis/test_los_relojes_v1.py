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

    Del 10 al 11/09/2026 llevaron UNA HORA DE MENOS escrita a
    mano, sobre la teoria de que cron-job.org aplica CET aunque
    le pongas "Europe/Madrid".

    ERA FALSA. Se dedujo de UN solo caso y el historial del dia
    siguiente la desmintio: con el job en "45,50 3" los disparos
    salieron a las 03:45 y 03:50. Madrid SI se honra, la
    compensacion los adelantaba una hora, y la primera ventana
    del reset se abrio con el mercado sin resetear.

    Ya no hay compensacion. Lo que se vigila aqui no es el
    cambio de hora -no hay nada que revertir en octubre- sino
    que un ciclo entre a una hora que NO es ninguna de las
    configuradas, sea cual sea el motivo.

    UN SOLO CASO NO ES UNA MEDICION. Esa es la leccion, y esta
    guardia existe para que no se vuelva a montar una regla
    sobre n=1.
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


def test_no_queda_compensacion_en_los_crones_externos() -> None:
    """
    LA TEORIA FALSA, Y SU RASTRO.

    Los crones externos NO llevan compensacion: la hora escrita
    es la hora de Madrid en que ocurren. Lo que si tiene que
    quedar es la explicacion de por que hubo una y como se
    desmintio, para que nadie la vuelva a deducir de un caso.
    """

    relojes = _lee(RELOJES)

    # Los de verdad, sin compensar.
    for cron in ("45 4 * * *", "50 4 * * *", "15 7 * * *"):
        assert cron in relojes, (
            f"falta el cron externo `{cron}` tal cual esta puesto"
        )

    # Y los compensados NO pueden volver como configuracion.
    codigo = _sin_comentarios(relojes)

    for viejo in ("45 3 * * *", "50 3 * * *", "15 6 * * *"):
        assert viejo not in codigo, (
            f"ha vuelto el cron compensado `{viejo}`: eso "
            f"adelanta el disparo una hora y abre la ventana con "
            f"el mercado sin resetear"
        )

    # El rastro, en cambio, tiene que estar.
    assert "ERA FALSA" in relojes, (
        "se ha borrado que la compensacion se probo y no valia: "
        "dentro de tres meses alguien la deduce otra vez"
    )

    assert "03:45" in relojes and "07:52" in relojes, (
        "falta la medicion que desmintio la teoria"
    )


def test_el_bot_avisa_si_el_ciclo_no_entra_a_su_hora() -> None:
    """
    LO QUE SUSTITUYE AL AVISO DEL CAMBIO DE HORA.

    Aquel vigilaba una compensacion que no existe. Este vigila lo
    que si importa: que un ciclo entre a una hora que no es
    ninguna de las configuradas.

    Se ejecuta de verdad, con dos fotos: una en hora -no avisa- y
    una desplazada -avisa, y dice cuanto-.

    Y NO diagnostica la causa. Esa es la mitad que importa: la
    ultima vez que se dedujo una causa de un solo caso costo la
    primera ventana del reset.
    """

    if shutil.which("node") is None:
        print("     AVISO: sin `node` no se puede ejecutar.")
        return

    guion = """
import { avisoDeDisparoFueraDeHora } from "./src/lib/relojes.js";
const ahora = new Date("2026-09-11T05:07:00Z");
const enHora = avisoDeDisparoFueraDeHora(ahora, "2026-09-11T02:47:00Z");
const fuera = avisoDeDisparoFueraDeHora(ahora, "2026-09-11T01:46:00Z");
console.log(JSON.stringify({
  enHora: enHora === null,
  motivo: fuera && fuera.motivo,
  minutos: fuera && fuera.minutos,
  texto: fuera && fuera.texto,
  configurados: fuera && fuera.configurados.map((c) => c.cron)
}));
"""

    carpeta = RAIZ / "dashboard-v8"

    fichero = carpeta / "_aviso_fuera_de_hora.mjs"

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

    assert visto["enHora"] is True, (
        "avisa con un ciclo que entro a su hora: una alarma que "
        "salta siempre no se lee"
    )

    assert visto["motivo"] == "DISPARO_FUERA_DE_HORA", visto

    assert visto["minutos"] > 12, visto

    # Los crones que enseña son los de verdad, sin compensar.
    assert visto["configurados"] == [
        "45 4 * * *",
        "50 4 * * *",
        "15 7 * * *",
    ], visto

    # Y no le echa la culpa a nadie.
    for causa in ("CET", "horario de verano", "cron-job"):
        assert causa not in visto["texto"], (
            f"el aviso diagnostica una causa (`{causa}`) y no "
            f"puede: con una observacion no se sabe"
        )


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
    test_no_queda_compensacion_en_los_crones_externos,
    test_el_bot_avisa_si_el_ciclo_no_entra_a_su_hora,
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
