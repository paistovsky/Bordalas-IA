"""
Cero contra cero no es un cuadre: es que no se midio nada.

EL CASO, DE LA FOTO DEL 20/09/2026

    4904   puntos_once 0   ·   puntos_biwenger 0   ·   cuadra: true
           reconstruccion_completa: false
           motivo_incompleta: "No se anoto que once jugo esa jornada."

    De esa jornada no anotamos NADA, y salia diciendo que
    concuerda con Biwenger.

DOCTRINA 91, DEL OTRO LADO

    Una roja que puede significar cualquier cosa vale lo mismo
    que una verde. Y al reves: un VERDE que puede darse sin
    haber medido nada vale lo mismo que un rojo.

    `cuadra` no puede ser cierto si no hubo reconstruccion. No
    es que sea falso — es que NO ES MEDIBLE, y eso se dice con
    un `None`, no con un `true`.

LO QUE NO CAMBIA, Y HAY QUE DECIRLO

    La fila sigue siendo `medible`: la resta de totales SI
    funciono, y sus puntos de liga son un hecho. Lo unico que
    deja de afirmarse es el cuadre.

    `jornadas_fiables` ya exigia `reconstruccion_completa`, asi
    que no se mueve. El que si se apoyaba en el verde falso era
    `cuadra_todo`.

REGLA 23, DOCTRINA 24 Y DOCTRINA 104

    No lee `data/`, ni la red, ni el reloj: el libro se escribe
    en un directorio temporal y se aparta el real. No depende de
    ningun `BORDALAS_*`. Y si en el caso todas las jornadas
    estuvieran completas, la guardia FALLA en vez de pasar sin
    mirar nada.
"""

from __future__ import annotations

import json
import tempfile

from pathlib import Path

from src.analysis import marcador as M


PRIMERA = M.PRIMERA_JORNADA        # 4899
SEGUNDA = 4900
TERCERA = 4901


CALENDARIO = {
    PRIMERA: {
        "round_id": PRIMERA,
        "primer_partido": "2026-08-15T17:30:00+00:00",
        "fuente": "EVENTOS_DEL_TABLON",
        "nombre": "Jornada 1",
    },
    SEGUNDA: {
        "round_id": SEGUNDA,
        "primer_partido": "2026-08-20T19:00:00+00:00",
        "fuente": "EVENTOS_DEL_TABLON",
        "nombre": "Jornada 2",
    },
    TERCERA: {
        "round_id": TERCERA,
        "primer_partido": "2026-08-28T17:00:00+00:00",
        "fuente": "EVENTOS_DEL_TABLON",
        "nombre": "Jornada 3",
    },
}


MI_USER_ID = 14175949

RIVAL_ID = 14145555


class ledger_temporal:
    """Aparta el libro real mientras dura la prueba."""

    def __enter__(self):
        self._directorio = tempfile.TemporaryDirectory()

        self._state = M.STATE_DIRECTORY
        self._file = M.LEDGER_FILE

        M.STATE_DIRECTORY = Path(self._directorio.name)
        M.LEDGER_FILE = M.STATE_DIRECTORY / "marcador.json"

        return M.LEDGER_FILE

    def __exit__(self, *_):
        M.STATE_DIRECTORY = self._state
        M.LEDGER_FILE = self._file
        self._directorio.cleanup()


def _plantilla() -> list:
    """Once justos: un portero, tres defensas, cinco medios, dos puntas."""

    jugadores = [{"id": 100, "name": "POR", "position": 1}]

    jugadores += [
        {"id": 200 + i, "name": f"DEF{i}", "position": 2}
        for i in range(3)
    ]

    jugadores += [
        {"id": 300 + i, "name": f"MED{i}", "position": 3}
        for i in range(5)
    ]

    jugadores += [
        {"id": 400 + i, "name": f"DEL{i}", "position": 4}
        for i in range(2)
    ]

    return jugadores


LOS_ONCE = [j["id"] for j in _plantilla()]


def _jornada(
    round_id,
    *,
    totales,
    puntos_liga,
    con_once: bool,
) -> dict:
    """Una fila del libro. Con o sin el once anotado."""

    return {
        "round_id": round_id,
        "mi_user_id": MI_USER_ID,
        "datos_de": f"2026-08-{round_id % 100:02d}T06:00:00+00:00",
        "escrito_en": f"2026-08-{round_id % 100:02d}T07:00:00+00:00",
        "plantilla": _plantilla(),
        "nombres": {
            str(j["id"]): j["name"] for j in _plantilla()
        },
        "totales": {
            str(pid): totales for pid in LOS_ONCE
        },
        "mi_once": (
            {
                "formation": "3-5-2",
                "players": list(LOS_ONCE),
            }
            if con_once
            else {}
        ),
        "clasificacion": [
            {
                "user_id": MI_USER_ID,
                "name": "Pepe Bordalas",
                "points": puntos_liga,
            },
            {
                "user_id": RIVAL_ID,
                "name": "Pollo17",
                "points": puntos_liga,
            },
        ],
    }


def _libro() -> dict:
    """
    Tres jornadas. La del medio SIN once anotado, que es el caso
    de 4904: cero contra cero.
    """

    return {
        "version": 1,
        "jornadas": {
            str(PRIMERA): _jornada(
                PRIMERA, totales=0, puntos_liga=0, con_once=True
            ),
            str(SEGUNDA): _jornada(
                SEGUNDA, totales=0, puntos_liga=0, con_once=False
            ),
            str(TERCERA): _jornada(
                TERCERA, totales=3, puntos_liga=33, con_once=True
            ),
        },
    }


def _filas() -> tuple[list, dict]:

    with ledger_temporal() as fichero:

        fichero.write_text(
            json.dumps(_libro(), ensure_ascii=False),
            encoding="utf-8",
        )

        salida = M.marcador(CALENDARIO)

    return salida["jornadas"], salida["resumen"]


def _por_id(filas) -> dict:
    return {f["round_id"]: f for f in filas}


# ============================================================
# 1. EL CASO TIENE QUE TRAER UNA JORNADA INCOMPLETA
# ============================================================


def test_sin_jornada_incompleta_no_se_comprueba_nada() -> None:
    """
    Doctrina 24. Si todas las jornadas del caso estuvieran
    completas, `cuadra` nunca llegaria a valer `None` y la
    prueba de abajo pasaria sin haber mirado nada.
    """

    filas, _ = _filas()

    medibles = [f for f in filas if f.get("medible")]

    assert medibles, (
        "en el caso no hay ni una jornada medible: no se puede "
        "comprobar nada sobre el cuadre"
    )

    incompletas = [
        f
        for f in medibles
        if not f.get("reconstruccion_completa")
    ]

    assert incompletas, (
        "en el caso todas las jornadas tienen reconstruccion "
        "completa: esta guardia no esta midiendo lo que dice"
    )

    completas = [
        f for f in medibles if f.get("reconstruccion_completa")
    ]

    assert completas, (
        "en el caso NINGUNA jornada esta completa: entonces no "
        "se puede comprobar que las buenas siguen contestando"
    )


# ============================================================
# 2. LA PRUEBA QUE DA NOMBRE AL FICHERO
# ============================================================


def test_una_jornada_sin_once_no_cuadra() -> None:
    """
    Con `reconstruccion_completa` en falso, `cuadra` no puede
    ser cierto.
    """

    filas, _ = _filas()

    for fila in filas:

        if not fila.get("medible"):
            continue

        if fila.get("reconstruccion_completa"):
            continue

        assert fila.get("cuadra") is not True, (
            f"la jornada {fila['round_id']} dice que cuadra "
            f"teniendo la reconstruccion incompleta "
            f"({fila.get('motivo_incompleta')})"
        )

        assert fila.get("cuadra") is None, (
            f"la jornada {fila['round_id']} publica "
            f"`cuadra: {fila.get('cuadra')}`. No es que no "
            f"cuadre: es que no se puede medir, y eso se dice "
            f"con None"
        )

        assert fila.get("cuadra_motivo"), (
            f"la jornada {fila['round_id']} deja el cuadre sin "
            f"medir y no dice por que (regla 28)"
        )

    # Y el caso de verdad: la del medio es cero contra cero.
    sin_once = _por_id(filas)[SEGUNDA]

    assert sin_once.get("puntos_once") == 0, (
        f"la jornada sin once no suma cero: "
        f"{sin_once.get('puntos_once')}"
    )

    assert sin_once.get("puntos_biwenger") == 0, (
        f"la jornada sin once no tiene cero de Biwenger: "
        f"{sin_once.get('puntos_biwenger')}"
    )


# ============================================================
# 3. LO QUE NO SE PUEDE MEDIR NO CUENTA COMO FALLO
# ============================================================


def test_el_cuadre_no_medible_no_cuenta_como_no_cuadra() -> None:
    """
    La otra mitad del mismo error: convertir el verde falso en
    un rojo falso. `cuadra_todo` mira solo las que se pudieron
    medir.
    """

    filas, resumen = _filas()

    medibles = [f for f in filas if f.get("medible")]

    medidas = [
        f for f in medibles if f.get("cuadra") is not None
    ]

    assert medidas, (
        "ninguna jornada del caso tiene cuadre medible: "
        "`cuadra_todo` no podria significar nada"
    )

    esperado = all(f["cuadra"] for f in medidas)

    assert resumen["cuadra_todo"] is esperado, (
        f"`cuadra_todo` vale {resumen['cuadra_todo']} y las "
        f"jornadas con cuadre medible dicen {esperado}"
    )


# ============================================================
# 4. Y LAS FIABLES NO SE MUEVEN
# ============================================================


def test_las_fiables_siguen_exigiendo_las_dos_cosas() -> None:
    """
    `jornadas_fiables` ya exigia `reconstruccion_completa`. Si
    este cambio la moviera, estaria tocando el criterio de que
    jornada es fiable — y eso lo decide el dueño.
    """

    filas, resumen = _filas()

    fiables = [
        f
        for f in filas
        if f.get("medible")
        and f.get("cuadra")
        and f.get("reconstruccion_completa")
    ]

    assert resumen["jornadas_fiables"] == len(fiables), (
        f"`jornadas_fiables` vale {resumen['jornadas_fiables']} "
        f"y contando a mano salen {len(fiables)}"
    )

    for fila in filas:

        if not fila.get("medible"):
            continue

        if fila.get("reconstruccion_completa"):
            continue

        assert fila not in fiables, (
            f"la jornada {fila['round_id']} entra en las "
            f"fiables con la reconstruccion incompleta"
        )


def main() -> int:

    pruebas = [
        test_sin_jornada_incompleta_no_se_comprueba_nada,
        test_una_jornada_sin_once_no_cuadra,
        test_el_cuadre_no_medible_no_cuenta_como_no_cuadra,
        test_las_fiables_siguen_exigiendo_las_dos_cosas,
    ]

    fallos = 0

    for prueba in pruebas:

        try:
            prueba()
            print(f"OK   {prueba.__name__}")

        except AssertionError as error:
            fallos += 1
            print(f"FALLA {prueba.__name__}: {error}")

    print("=" * 60)
    print(
        f"UNA JORNADA SIN ONCE NO CUADRA V1: "
        f"{len(pruebas) - fallos}/{len(pruebas)} OK"
    )
    print("=" * 60)

    return 1 if fallos else 0


if __name__ == "__main__":
    raise SystemExit(main())
