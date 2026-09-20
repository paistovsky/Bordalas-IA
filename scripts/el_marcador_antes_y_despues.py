"""
El marcador: el orden de las fotos, los negativos y los siete puntos.

LAS TRES COSAS QUE MIDE, Y POR QUE JUNTAS

    1. EL ORDEN. Las nueve jornadas observadas, colocadas con el
       calendario de hoy y con la fecha que publica el tablon.
       Y cuantas pasan de descartadas a medibles.

    2. LOS NEGATIVOS. Las 72 restas que permiten las 9 fotos,
       separadas por si la previa es de verdad anterior. Es lo
       que dice si «un negativo pequeño» y «las fotos al reves»
       son dos cosas distintas o la misma.

    3. LOS SIETE PUNTOS de la jornada 5125, jugador a jugador.

    Van juntas porque las tres salen del mismo libro y la
    tercera solo se entiende con la primera.

NI RED, NI ESCRITURAS, NI RELOJ

    Lee `data/` -el libro del marcador, la foto, el calendario y
    los eventos del tablon- y no escribe nada. No es una
    guardia: es un mirador que se corre a mano.

    El interruptor se pone y se quita aqui dentro, y se deja
    como estaba.

COMO SE USA

    python -m scripts.el_marcador_antes_y_despues
"""

from __future__ import annotations

import glob
import json
import os
import sys

from pathlib import Path


RAIZ = Path(__file__).resolve().parents[1]

if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))


from src.analysis import marcador as M                       # noqa: E402


LIBRO = RAIZ / "data" / "intelligence" / "marcador.json"

CALENDARIO_LALIGA = RAIZ / "data" / "calendar" / "laliga_calendar.json"

EVENTOS = RAIZ / "data" / "rival_intelligence" / "board_events.json"


LA_JORNADA_BUENA = 5125


def _json(camino: Path, por_defecto):
    try:
        return json.loads(camino.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return por_defecto


def ultima_foto():
    """La foto mas reciente de `data/`. `None` si no hay."""

    fotos = sorted(glob.glob(str(RAIZ / "data" / "snapshot_*.json")))

    return _json(Path(fotos[-1]), None) if fotos else None


def con_interruptor(encendido: bool, fn):

    antes = os.environ.get(M.ENV_POR_SU_FECHA)

    try:
        os.environ[M.ENV_POR_SU_FECHA] = "1" if encendido else "0"
        return fn()

    finally:

        if antes is None:
            os.environ.pop(M.ENV_POR_SU_FECHA, None)
        else:
            os.environ[M.ENV_POR_SU_FECHA] = antes


def calendarios(foto, calendario_laliga, eventos):

    return {
        etiqueta: con_interruptor(
            encendido,
            lambda: M.calendario_desde_la_foto(
                foto, calendario_laliga, eventos=eventos
            ),
        )
        for etiqueta, encendido in (
            ("HOY", False),
            ("CON LA FECHA DEL TABLON", True),
        )
    }


# ----------------------------------------------------------------
# 1. EL ORDEN
# ----------------------------------------------------------------


def cuadro_del_orden(cales, libro) -> None:

    print("=" * 76)
    print("1. EL ORDEN DE LAS FOTOS")
    print("=" * 76)

    for etiqueta, calendario in cales.items():

        salida = M.marcador(calendario)

        resumen = salida["resumen"]

        orden = [f["round_id"] for f in salida["jornadas"]][::-1]

        print()
        print(f"  --- {etiqueta} ---")
        print(f"  orden: {orden}")
        print(
            f"  observadas {resumen['jornadas_observadas']} · "
            f"MEDIBLES {resumen['jornadas_medibles']} · "
            f"fiables {resumen['jornadas_fiables']} · "
            f"descartadas {resumen['jornadas_descartadas']} · "
            f"sin hora {resumen['jornadas_sin_hora']} · "
            f"con hueco {resumen['jornadas_con_hueco']}"
        )
        print(
            f"  eficiencia_media {resumen['eficiencia_media']} · "
            f"diferencia_media {resumen['diferencia_media']} "
            f"(n={resumen['diferencia_media_n']}) · "
            f"cuadra_todo {resumen['cuadra_todo']}"
        )

        for fila in salida["jornadas"]:

            if fila.get("medible"):
                print(
                    f"    {fila['round_id']}  MEDIBLE   "
                    f"once {fila.get('puntos_once')} · "
                    f"biwenger {fila.get('puntos_biwenger')} · "
                    f"cuadra {fila.get('cuadra')} · "
                    f"completa {fila.get('reconstruccion_completa')}"
                )
            else:
                print(
                    f"    {fila['round_id']}  no medible: "
                    f"{str(fila.get('motivo'))[:90]}"
                )

    print()
    print("  Las horas de cada jornada, y de donde salen:")
    print(
        f"    {'round':>6s} {'nombre':24s} {'HOY':26s} "
        f"{'CON EL TABLON':26s}"
    )

    observadas = sorted(
        int(k) for k in (libro.get("jornadas") or {})
    )

    for round_id in observadas:

        hoy = (cales["HOY"].get(round_id) or {})
        nuevo = (cales["CON LA FECHA DEL TABLON"].get(round_id) or {})

        # SE COMPARA EL INSTANTE, NO EL TEXTO. Las dos fuentes
        # escriben la misma hora con husos distintos
        # (+02:00 y UTC) y compararlas como cadenas marcaria las
        # nueve como cambiadas.
        marca = (
            "  <== CAMBIA"
            if M._momento(hoy.get("primer_partido"))
            != M._momento(nuevo.get("primer_partido"))
            else ""
        )

        print(
            f"    {round_id:>6d} {str(nuevo.get('nombre'))[:24]:24s} "
            f"{str(hoy.get('primer_partido'))[:26]:26s} "
            f"{str(nuevo.get('primer_partido'))[:26]:26s}{marca}"
        )


# ----------------------------------------------------------------
# 2. LOS NEGATIVOS
# ----------------------------------------------------------------


def negativos_de(actual: dict, previa: dict) -> list:

    aqui = actual.get("totales") or {}
    alli = previa.get("totales") or {}

    return sorted(
        (
            (player_id, M.safe_int(total) - M.safe_int(alli[player_id]))
            for player_id, total in aqui.items()
            if player_id in alli
            and M.safe_int(total) - M.safe_int(alli[player_id]) < 0
        ),
        key=lambda par: par[1],
    )


def cuadro_de_los_negativos(cales, libro) -> None:

    print()
    print("=" * 76)
    print("2. LOS NEGATIVOS: DOS ENFERMEDADES CON LA MISMA ETIQUETA")
    print("=" * 76)

    jornadas = libro.get("jornadas") or {}

    calendario = cales["CON LA FECHA DEL TABLON"]

    def cuando(round_id):
        return (
            (calendario.get(int(round_id)) or {}).get("primer_partido")
            or ""
        )

    orden = sorted(jornadas, key=cuando)

    bien, mal = [], []

    for i, actual in enumerate(orden):
        for j, previa in enumerate(orden):

            if i == j:
                continue

            caso = {
                "actual": int(actual),
                "previa": int(previa),
                "negativos": negativos_de(
                    jornadas[actual], jornadas[previa]
                ),
            }

            (bien if j < i else mal).append(caso)

    for etiqueta, grupo in (
        ("ORDEN CORRECTO  (la previa es anterior)", bien),
        ("ORDEN INVERTIDO (la previa es posterior)", mal),
    ):

        con = [c for c in grupo if c["negativos"]]

        print()
        print(f"  {etiqueta}")
        print(
            f"    {len(grupo)} restas · {len(con)} con algun "
            f"negativo · {len(grupo) - len(con)} limpias"
        )

        if con:
            print(
                f"    jugadores con negativo: "
                f"{sorted(len(c['negativos']) for c in con)}"
            )
            print(
                f"    el peor de cada una:    "
                f"{sorted(c['negativos'][0][1] for c in con)}"
            )

    print()
    print("  Y las ocho restas consecutivas de verdad:")

    for i in range(1, len(orden)):

        actual, previa = orden[i], orden[i - 1]

        negativos = negativos_de(
            jornadas[actual], jornadas[previa]
        )

        print(
            f"    {actual} <- {previa}   "
            f"{len(negativos)} jugador(es)"
            + (
                f", el peor {negativos[0][1]}"
                if negativos
                else ", limpia"
            )
        )

    print()
    print(
        f"  El discriminante que usa el codigo: "
        f"{M.JUGADORES_DE_UN_DESORDEN} jugador(es) o mas es un "
        f"desorden; uno solo y de {M.CORRECCION_MAS_GRANDE} o "
        f"menos es una correccion."
    )


# ----------------------------------------------------------------
# 3. LOS SIETE PUNTOS
# ----------------------------------------------------------------


def cuadro_de_los_siete(cales, libro, foto) -> None:

    print()
    print("=" * 76)
    print(f"3. LOS PUNTOS SIN EXPLICAR DE LA JORNADA {LA_JORNADA_BUENA}")
    print("=" * 76)

    jornadas = libro.get("jornadas") or {}

    actual = jornadas.get(str(LA_JORNADA_BUENA))

    if not actual:
        print(f"  La jornada {LA_JORNADA_BUENA} no esta en el libro.")
        return

    catalogo = (
        ((foto or {}).get("catalog") or {}).get("data", {})
        .get("players", {})
        or {}
    )

    def nombre(player_id):
        return (
            (catalogo.get(str(player_id)) or {}).get("name")
            or f"#{player_id}"
        )

    for etiqueta, calendario in cales.items():

        salida = M.marcador(calendario)

        orden = [f["round_id"] for f in salida["jornadas"]][::-1]

        if LA_JORNADA_BUENA not in orden:
            continue

        indice = orden.index(LA_JORNADA_BUENA)

        if indice == 0:
            continue

        previa = jornadas.get(str(orden[indice - 1]))

        if not previa:
            continue

        aqui = actual.get("totales") or {}
        alli = previa.get("totales") or {}

        once = [
            str(p)
            for p in ((actual.get("mi_once") or {}).get("players") or [])
        ]

        print()
        print(
            f"  --- {etiqueta}: la previa es "
            f"{orden[indice - 1]} ---"
        )
        print(
            f"      foto de {LA_JORNADA_BUENA}: "
            f"{actual.get('datos_de') or actual.get('escrito_en')}"
        )
        print(
            f"      foto de {orden[indice - 1]}: "
            f"{previa.get('datos_de') or previa.get('escrito_en')}"
        )
        print()
        print(
            f"      {'jugador':20s} {'ahora':>7s} {'antes':>7s} "
            f"{'resta':>7s} {'el motor':>9s}"
        )

        suma_real = suma_motor = 0

        for player_id in once:

            ahora = M.safe_int(aqui.get(player_id))

            esta = player_id in alli

            antes = M.safe_int(alli.get(player_id))

            real = ahora - antes

            # El motor pone CERO al que no estaba en la foto
            # anterior: no sabe cuanto de su total es de esta
            # jornada.
            del_motor = real if esta else 0

            suma_real += real
            suma_motor += del_motor

            print(
                f"      {nombre(player_id):20s} {ahora:>7d} "
                f"{(str(antes) if esta else '-'):>7s} "
                f"{real:>7d} {del_motor:>9d}"
                + ("" if esta else "   <- no estaba en la foto")
            )

        mi_user_id = M.safe_int(actual.get("mi_user_id"))

        def oficial(jornada):
            return next(
                (
                    M.safe_int(f.get("points"))
                    for f in (jornada.get("clasificacion") or [])
                    if M.safe_int(f.get("user_id")) == mi_user_id
                ),
                0,
            )

        biwenger = oficial(actual) - oficial(previa)

        print()
        print(
            f"      suma cruda {suma_real}  ·  lo que publica el "
            f"motor {suma_motor}  ·  Biwenger {biwenger}"
        )
        print(
            f"      descuadre {biwenger - suma_motor}"
            + (
                f"  ({abs(biwenger - suma_motor) / biwenger * 100:.1f} %)"
                if biwenger
                else ""
            )
        )
        print(
            f"      lo que el motor puso a cero: "
            f"{suma_real - suma_motor}"
        )


def main() -> None:

    libro = _json(LIBRO, {})

    if not (libro.get("jornadas") or {}):
        print(f"No hay libro del marcador en {LIBRO}.")
        return

    foto = ultima_foto()

    if foto is None:
        print("No hay ninguna foto en data/.")
        return

    cales = calendarios(
        foto,
        _json(CALENDARIO_LALIGA, {}),
        _json(EVENTOS, []),
    )

    cuadro_del_orden(cales, libro)
    cuadro_de_los_negativos(cales, libro)
    cuadro_de_los_siete(cales, libro, foto)


if __name__ == "__main__":
    main()
