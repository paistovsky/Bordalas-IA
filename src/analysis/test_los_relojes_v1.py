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

    Hubo una autoridad -el cron de `bordalas-live.yml`- y dos
    espejos que esta guardia obligaba a coincidir con ella.

SEGUNDO SINTOMA (12/09/2026): LA AUTORIDAD SE FUE DE CASA

    La verja en rojo y el ciclo parado, 5 de 6. Fallaba
    `test_la_cadencia_sale_del_cron` porque leia un `schedule`
    que ya no existe.

    EL SCHEDULE DE GITHUB SE RETIRO EL 12/09/2026, y con un dato
    detras: SE SALTABA VUELTAS TODOS LOS DIAS. Llegaba 30-40
    minutos tarde y perdia ciclos enteros. Los `schedule` de
    Actions son una cola de baja prioridad, no una promesa; con
    una vuelta por hora, 30-40 minutos tarde es la vuelta
    perdida. QUE NADIE LO VUELVA A PONER SIN SABER ESTO.

    El latido pasa a cron-job.org. Y eso es un cambio de fondo,
    no un parche: LA AUTORIDAD DEL RELOJ YA NO VIVE EN EL
    REPOSITORIO. Esta en un servicio externo que el codigo no
    puede leer.

    Asi que la autoridad pasa a ser `config/disparos.json`: la
    declaracion de los disparos que se ESPERAN. Y esta guardia
    comprueba los espejos contra esa declaracion.

    OJO A LO QUE NO PUEDE HACER ESTA GUARDIA

        La declaracion no es la verdad: es lo que creemos haber
        configurado. Ninguna guardia puede comprobar que
        cron-job.org este vivo. Lo unico que mira la realidad es
        el aviso de DISPARO FUERA DE HORA, y por eso
        `test_el_bot_avisa_si_el_ciclo_no_entra_a_su_hora` pasa
        a ser la guardia mas importante de este fichero.

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

DECLARACION = RAIZ / "config" / "disparos.json"

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


def _declaracion() -> dict:
    """La autoridad. Si no se puede leer, no hay reloj."""

    from src.analysis.los_disparos import declaracion

    decl = declaracion()

    assert decl["available"], decl["reason"]

    return decl


# ============================================================
# 1. UNA SOLA CADENCIA
# ============================================================


def test_la_cadencia_sale_de_la_declaracion() -> None:
    """
    La declaracion manda, y los que la leen no la copian.

    Antes esto comparaba tres numeros -el cron, `relojes.js` y
    `dashboard_state.py`- y obligaba a que coincidieran. Hoy no
    hay nada que comparar en `relojes.js`: IMPORTA el mismo
    fichero. Eso es mejor que una guardia, porque no puede
    desincronizarse.

    Lo que si se comprueba es que sigan importandolo, y que
    Python no se haya vuelto a escribir un numero a mano.
    """

    decl = _declaracion()

    esperada = decl["cadencia_minutos"]

    # Regla 24: si el calculo diera algo absurdo, la guardia no
    # puede pasar tan contenta.
    assert 1 <= esperada <= 24 * 60, decl

    # Un latido por hora y tres puntuales: 23 al dia.
    assert len(decl["todos_los_minutos"]) == 23, decl

    relojes = _sin_comentarios(_lee(RELOJES))

    assert "config/disparos.json" in relojes, (
        "`relojes.js` no importa la declaracion: ha vuelto a "
        "tener un espejo, y un espejo se desincroniza"
    )

    # Y no lleva ninguna hora escrita a mano.
    for suelto in ("04:45", "04:50", "07:15", "0-2,7-23"):
        assert suelto not in relojes, (
            f"`relojes.js` lleva `{suelto}` escrito a mano en "
            f"vez de leerlo de la declaracion"
        )

    telemetria = _sin_comentarios(_lee(TELEMETRIA))

    assert "los_disparos" in telemetria, (
        "`dashboard_state.py` no lee la declaracion"
    )

    assert not re.search(
        r"CADENCIA_MINUTOS\s*=\s*\d+", telemetria
    ), (
        "`dashboard_state.py` ha vuelto a escribir la cadencia a "
        "mano: es exactamente el fallo del 10/09"
    )

    from src.telemetry.dashboard_state import CADENCIA_MINUTOS

    assert CADENCIA_MINUTOS == esperada, (
        CADENCIA_MINUTOS,
        esperada,
    )


def test_el_schedule_de_github_no_vuelve_sin_saber_por_que() -> None:
    """
    SE RETIRO EL 12/09/2026 Y NO POR CAPRICHO.

    Se saltaba vueltas todos los dias: llegaba 30-40 minutos
    tarde y perdia ciclos enteros. Si alguien ve un workflow con
    solo `workflow_dispatch` y piensa "le falta el cron", esto es
    lo que le falta saber.

    La guardia no prohibe volver a ponerlo —puede haber un motivo
    algun dia— pero obliga a que el motivo de la retirada siga
    escrito donde se lea.
    """

    from src.analysis.los_disparos import (
        SCHEDULE_MOTIVO,
        SCHEDULE_RETIRADO_EL,
        SCHEDULE_RETRASO_MEDIDO,
    )

    assert SCHEDULE_RETIRADO_EL == "2026-09-12"

    assert SCHEDULE_RETRASO_MEDIDO == "30-40 minutos"

    assert "vueltas" in SCHEDULE_MOTIVO, SCHEDULE_MOTIVO

    # El motivo, donde se va a leer: en el propio workflow.
    workflow = _lee(WORKFLOW)

    for dato in ("12/09/2026", "30-40", "cron-job.org"):
        assert dato in workflow, (
            f"el workflow no dice `{dato}`: quien lo abra vera "
            f"un fichero sin cron y no sabra que se quito a "
            f"proposito"
        )

    # Y si vuelve a haber un `schedule`, que sea deliberado: esta
    # guardia se pone roja y hay que venir aqui a leer por que.
    assert not re.search(
        r"^\s*schedule:", _sin_comentarios(workflow), re.M
    ), (
        "ha vuelto el `schedule` de GitHub. Se retiro el "
        "12/09/2026 porque llegaba 30-40 minutos tarde y perdia "
        "ciclos enteros. Si vuelve a ponerse a proposito, "
        "actualiza esta guardia y deja escrito por que."
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

    declarado = DECLARACION.read_text(encoding="utf-8")

    # Los de verdad, sin compensar, EN LA DECLARACION — que es
    # donde viven desde el 12/09. Ya no estan en `relojes.js`.
    for cron in ("45 4 * * *", "50 4 * * *", "15 7 * * *"):
        assert cron in declarado, (
            f"falta el cron externo `{cron}` tal cual esta puesto"
        )

    # Y los compensados NO pueden volver como configuracion.
    codigo = _sin_comentarios(relojes) + _sin_comentarios(
        declarado
    )

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
// 04:47 Madrid: dos minutos del disparo de la ventana. En hora.
const enHora = avisoDeDisparoFueraDeHora(ahora, "2026-09-11T02:47:00Z");
// 03:46 Madrid: 39 minutos del latido de las 03:07.
const fuera = avisoDeDisparoFueraDeHora(ahora, "2026-09-11T01:46:00Z");
// 05:30 Madrid: DENTRO de la ventana del reset, donde no hay
// ningun disparo declarado. Es la forma que tendria un
// cron-job.org mal configurado, y la unica alarma que lo veria.
const enLaVentana = avisoDeDisparoFueraDeHora(ahora, "2026-09-11T03:30:00Z");
console.log(JSON.stringify({
  enHora: enHora === null,
  motivo: fuera && fuera.motivo,
  minutos: fuera && fuera.minutos,
  texto: fuera && fuera.texto,
  configurados: fuera && fuera.configurados.map((c) => c.madrid),
  ventanaAvisa: enLaVentana !== null,
  ventanaMinutos: enLaVentana && enLaVentana.minutos
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

    # Las horas que enseña son las declaradas, sin compensar.
    assert visto["configurados"] == [
        "04:45",
        "04:50",
        "07:15",
    ], visto

    # Y CAZA UN DISPARO DENTRO DE LA VENTANA DEL RESET.
    #
    #     Es el caso que importa desde el 12/09: si cron-job.org
    #     se descolocara, un ciclo entraria a una hora en la que
    #     no hay ningun disparo declarado. Esta alarma es LA
    #     UNICA que mira la realidad — ninguna guardia puede
    #     comprobar que un servicio externo este vivo.
    assert visto["ventanaAvisa"] is True, (
        "un ciclo a las 05:30, dentro de la ventana del reset y "
        "sin ningun disparo declarado cerca, NO dispara la "
        "alarma: nos quedariamos sin saberlo"
    )

    assert visto["ventanaMinutos"] > 12, visto

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
    test_la_cadencia_sale_de_la_declaracion,
    test_el_schedule_de_github_no_vuelve_sin_saber_por_que,
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
