"""
El once se anota antes del primer partido, y una sola vez.

SINTOMA (14/09/2026)

    Siete jornadas observadas, CERO fiables. Todas descartadas
    por lo mismo: "No se anoto que once jugo esa jornada".

    Sin marcador, "mejorar el once" no tiene ningun numero que
    oponer a "+2 % de prima al revender", asi que pierde todas
    las discusiones internas aunque sea la via buena.

LO QUE VIGILAN ESTAS GUARDIAS

    1. Que se anote ANTES del primer partido, y que despues no se
       toque. Lo que da valor a esa entrada no es el once: es que
       conste que se escribio antes.

    2. Una jornada, un once. Dos vueltas antes del cierre no
       pueden escribir dos entradas.

    3. Que no se anote una alineacion a medias. Ocho nombres
       dejan una entrada que parece buena y da una nota coja.

REGLA 23

    No leen ni escriben estado de produccion: cada prueba usa un
    fichero temporal propio.

DOCTRINA 50

    Ni una llamada al reloj del sistema. Todas las horas son
    fijas y estan escritas aqui.
"""

from __future__ import annotations

import json
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path


# EL PRIMER PARTIDO DE LA JORNADA 7, de verdad: 18/09 a las
# 21:00 de Madrid, que son las 19:00 UTC.
EL_PARTIDO = datetime(2026, 9, 18, 19, 0, tzinfo=timezone.utc)

# LA VENTANA. El `safety_deadline` que ya calcula el motor de
# calendario: noventa minutos antes del primer partido.
#
#     Antes de esa hora el dueño todavia puede cambiar el once,
#     asi que congelarlo no probaria nada.
LA_VENTANA = EL_PARTIDO - timedelta(minutes=90)

UNA_HORA_ANTES = EL_PARTIDO - timedelta(hours=1)

CINCO_DIAS_ANTES = EL_PARTIDO - timedelta(days=5)

DIEZ_MINUTOS_DESPUES = EL_PARTIDO + timedelta(minutes=10)

# El once real del 13/09, tal y como lo tiene Biwenger.
EL_ONCE = {
    "formation": "4-4-2",
    "date": 1789280811,   # 13/09 06:26 UTC, como lo publica Biwenger
    "players": [
        17482, 1599, 1721, 9983, 8376,
        19862, 29661, 14800, 41606,
        26271, 3159,
    ],
}

# LA MISMA ALINEACION, CON LAS FICHAS ENTERAS.
#
#     Asi es como llega de `user_lineup`, que es la fuente viva.
#     Tratarla como la de `standings` —ids sueltos— daba once
#     ceros y un once vacio.
EL_ONCE_CON_FICHAS = {
    "formation": "4-4-2",
    "date": 1789280811,
    "players": [
        {"id": pid, "name": f"Jugador {pid}"}
        for pid in EL_ONCE["players"]
    ],
}

LA_JORNADA = 4904


def _libro(carpeta) -> Path:
    return Path(carpeta) / "onces.jsonl"


def _lineas(ruta: Path) -> list:
    if not ruta.exists():
        return []

    return [
        json.loads(linea)
        for linea in ruta.read_text(
            encoding="utf-8"
        ).splitlines()
        if linea.strip()
    ]


def test_el_once_se_anota_antes_del_primer_partido() -> None:
    """
    ANTES SI, DESPUES NO.

    A partir del primer partido el once ya no puede cambiar sin
    que Biwenger lo sepa, asi que lo anotado antes ES lo que
    jugo. Lo anotado despues no prueba nada: pudo cambiarse a
    mano media hora antes y nadie lo sabria.
    """

    from src.analysis.el_once_que_jugo import (
        anotar_el_once,
        onces_anotados,
    )

    with tempfile.TemporaryDirectory() as carpeta:

        ruta = _libro(carpeta)

        # 1. UNA HORA ANTES: se anota.
        hecho = anotar_el_once(
            LA_JORNADA,
            EL_ONCE,
            primer_partido=EL_PARTIDO,
            desde=LA_VENTANA,
            ahora=UNA_HORA_ANTES,
            ruta=ruta,
        )

        assert hecho["anotado"] is True, hecho

        assert hecho["players"] == EL_ONCE["players"], hecho

        assert len(hecho["players"]) == 11, hecho

        assert hecho["minutos_de_margen"] == 60, hecho

        # Y esta en el libro, con de donde salio.
        filas = _lineas(ruta)

        assert len(filas) == 1, filas

        assert filas[0]["origen"] == (
            "BIWENGER_USER_LINEUP"
        ), filas[0]

        # CUANDO LO GUARDO EL DUEÑO, que es la prueba de que el
        # once congelado es el vigente y no uno de hace cinco
        # dias.
        assert filas[0]["guardado_en"] == (
            "2026-09-13T06:26:51+00:00"
        ), filas[0]

        assert filas[0]["formation"] == "4-4-2", filas[0]

        assert onces_anotados(ruta)[LA_JORNADA][
            "players"
        ] == EL_ONCE["players"]

    # 2. YA EMPEZADO: no se anota, y se dice por que.
    with tempfile.TemporaryDirectory() as carpeta:

        ruta = _libro(carpeta)

        tarde = anotar_el_once(
            LA_JORNADA,
            EL_ONCE,
            primer_partido=EL_PARTIDO,
            desde=LA_VENTANA,
            ahora=DIEZ_MINUTOS_DESPUES,
            ruta=ruta,
        )

        assert tarde["anotado"] is False, tarde

        assert "ya empezo" in tarde["reason"], tarde["reason"]

        assert _lineas(ruta) == [], _lineas(ruta)

    # 3. Y NO SE SOBREESCRIBE LO ANOTADO A TIEMPO.
    #
    #    Es el caso que de verdad importa: el dueño cambia la
    #    alineacion despues del pitido y el ciclo sigue
    #    corriendo. Lo que queda tiene que ser lo de antes.
    with tempfile.TemporaryDirectory() as carpeta:

        ruta = _libro(carpeta)

        anotar_el_once(
            LA_JORNADA,
            EL_ONCE,
            primer_partido=EL_PARTIDO,
            desde=LA_VENTANA,
            ahora=UNA_HORA_ANTES,
            ruta=ruta,
        )

        OTRO = {
            "formation": "3-5-2",
            "players": [90000 + i for i in range(11)],
        }

        despues = anotar_el_once(
            LA_JORNADA,
            OTRO,
            primer_partido=EL_PARTIDO,
            desde=LA_VENTANA,
            ahora=DIEZ_MINUTOS_DESPUES,
            ruta=ruta,
        )

        assert despues["anotado"] is False, despues

        guardado = onces_anotados(ruta)[LA_JORNADA]

        assert guardado["players"] == EL_ONCE["players"], guardado

        assert guardado["formation"] == "4-4-2", guardado


def test_las_dos_formas_del_once_valen() -> None:
    """
    IDS SUELTOS O FICHAS ENTERAS: LAS DOS.

    SINTOMA QUE EVITA (14/09/2026)

        Biwenger publica nuestra alineacion en dos sitios y con
        dos formas. `standings[mi].lineup.players` trae ids;
        `user_lineup.data.lineup.players` trae la ficha entera.

        Tratar la segunda como la primera da once ceros, se
        filtran, y el once sale VACIO — con el motivo diciendo
        "alineacion a medias" cuando estaba entera. Un fallo que
        se explica a si mismo con la frase equivocada.
    """

    from src.analysis.el_once_que_jugo import (
        anotar_el_once,
        ids_del_once,
    )

    # Las dos dan los mismos once ids.
    assert ids_del_once(EL_ONCE) == EL_ONCE["players"]

    assert ids_del_once(EL_ONCE_CON_FICHAS) == EL_ONCE["players"]

    # REGLA 24: y no es que las dos den vacio.
    assert len(ids_del_once(EL_ONCE_CON_FICHAS)) == 11

    with tempfile.TemporaryDirectory() as carpeta:

        ruta = _libro(carpeta)

        hecho = anotar_el_once(
            LA_JORNADA,
            EL_ONCE_CON_FICHAS,
            primer_partido=EL_PARTIDO,
            desde=LA_VENTANA,
            ahora=UNA_HORA_ANTES,
            ruta=ruta,
        )

        assert hecho["anotado"] is True, hecho

        assert hecho["players"] == EL_ONCE["players"], hecho


def test_una_alineacion_a_medias_no_se_anota() -> None:
    """
    OCHO NOMBRES NO SON UN ONCE (regla 24).

    Guardarlos dejaria una entrada que PARECE buena: los once
    campos estan, el libro dice que se anoto a tiempo, y la nota
    sale coja sin que nadie sepa por que.

    Mejor no anotar y que la pantalla diga que esa jornada falta.
    """

    from src.analysis.el_once_que_jugo import (
        anotar_el_once,
        hay_que_anotar,
    )

    with tempfile.TemporaryDirectory() as carpeta:

        ruta = _libro(carpeta)

        for cuantos in (0, 1, 8, 10, 12):

            a_medias = {
                "formation": "4-4-2",
                "players": EL_ONCE["players"][:cuantos]
                + [70000 + i for i in range(max(0, cuantos - 11))],
            }

            hecho = anotar_el_once(
                LA_JORNADA,
                a_medias,
                primer_partido=EL_PARTIDO,
            desde=LA_VENTANA,
                ahora=UNA_HORA_ANTES,
                ruta=ruta,
            )

            assert hecho["anotado"] is False, (cuantos, hecho)

            assert "medias" in hecho["reason"], (
                cuantos,
                hecho["reason"],
            )

        # NI SIN ONCE NINGUNO.
        for sin_once in (None, {}, {"players": None}):

            assert (
                anotar_el_once(
                    LA_JORNADA,
                    sin_once,
                    primer_partido=EL_PARTIDO,
            desde=LA_VENTANA,
                    ahora=UNA_HORA_ANTES,
                    ruta=ruta,
                )["anotado"]
                is False
            ), sin_once

        assert _lineas(ruta) == [], _lineas(ruta)

        # Y CON LOS ONCE, SI.
        assert hay_que_anotar(
            LA_JORNADA,
            EL_PARTIDO,
            UNA_HORA_ANTES,
            once=EL_ONCE,
            desde=LA_VENTANA,
            ruta=ruta,
        )["anota"] is True


def test_no_se_congela_el_once_cinco_dias_antes() -> None:
    """
    LA VENTANA SE ABRE AL FINAL, NO AL PRINCIPIO.

    SINTOMA QUE EVITA (14/09/2026)

        La primera version anotaba en cuanto veia la jornada. En
        la foto del 13/09 eso salian SIETE MIL TRESCIENTOS
        MINUTOS de margen: cinco dias en los que el dueño puede
        cambiar la alineacion veinte veces.

        Un once congelado cinco dias antes no prueba nada, que es
        justo el problema que este libro venia a arreglar. Habria
        quedado una entrada con pinta de buena y el marcador
        volveria a descuadrar sin que nadie supiera por que.

    La ventana sale del `safety_deadline` del motor de
    calendario. Aqui no se inventa ningun reloj.
    """

    from src.analysis.el_once_que_jugo import anotar_el_once

    with tempfile.TemporaryDirectory() as carpeta:

        ruta = _libro(carpeta)

        # 1. CINCO DIAS ANTES: no.
        pronto = anotar_el_once(
            LA_JORNADA,
            EL_ONCE,
            primer_partido=EL_PARTIDO,
            desde=LA_VENTANA,
            ahora=CINCO_DIAS_ANTES,
            ruta=ruta,
        )

        assert pronto["anotado"] is False, pronto

        assert "Todavia no toca" in pronto["reason"], (
            pronto["reason"]
        )

        assert _lineas(ruta) == [], _lineas(ruta)

        # 2. UN MINUTO ANTES DE LA VENTANA: tampoco.
        casi = anotar_el_once(
            LA_JORNADA,
            EL_ONCE,
            primer_partido=EL_PARTIDO,
            desde=LA_VENTANA,
            ahora=LA_VENTANA - timedelta(minutes=1),
            ruta=ruta,
        )

        assert casi["anotado"] is False, casi

        # 3. EN EL MINUTO EXACTO EN QUE SE ABRE: si.
        justo = anotar_el_once(
            LA_JORNADA,
            EL_ONCE,
            primer_partido=EL_PARTIDO,
            desde=LA_VENTANA,
            ahora=LA_VENTANA,
            ruta=ruta,
        )

        assert justo["anotado"] is True, justo

        assert justo["minutos_de_margen"] == 90, justo

    # 4. SIN VENTANA NO SE ANOTA NADA.
    #
    #    Un respaldo que anotara igual dejaria la puerta abierta
    #    a congelarlo cinco dias antes otra vez.
    with tempfile.TemporaryDirectory() as carpeta:

        ruta = _libro(carpeta)

        sin_ventana = anotar_el_once(
            LA_JORNADA,
            EL_ONCE,
            primer_partido=EL_PARTIDO,
            desde=None,
            ahora=UNA_HORA_ANTES,
            ruta=ruta,
        )

        assert sin_ventana["anotado"] is False, sin_ventana

        assert "ventana" in sin_ventana["reason"], (
            sin_ventana["reason"]
        )


def test_una_jornada_un_once() -> None:
    """
    DOS VUELTAS ANTES DEL CIERRE NO ESCRIBEN DOS ENTRADAS.

    El ciclo corre cada pocos minutos. Sin esto, la ventana de
    una hora antes del partido dejaria doce lineas de la misma
    jornada y la ultima volveria a ser "la que se escribio al
    final", que es justo el problema que este libro arregla.
    """

    from src.analysis.el_once_que_jugo import (
        anotar_el_once,
        onces_anotados,
    )

    with tempfile.TemporaryDirectory() as carpeta:

        ruta = _libro(carpeta)

        # Doce vueltas en la hora previa.
        hechos = [
            anotar_el_once(
                LA_JORNADA,
                EL_ONCE,
                primer_partido=EL_PARTIDO,
            desde=LA_VENTANA,
                ahora=EL_PARTIDO - timedelta(minutes=minuto),
                ruta=ruta,
            )
            for minuto in range(60, 0, -5)
        ]

        # REGLA 24: si no se hubiera intentado nada, esto pasaria
        # solo.
        assert len(hechos) == 12, hechos

        anotados = [h for h in hechos if h["anotado"]]

        assert len(anotados) == 1, [
            (h["anotado"], h["reason"]) for h in hechos
        ]

        # La PRIMERA, que es la que mas margen tenia.
        assert anotados[0]["minutos_de_margen"] == 60, anotados[0]

        assert len(_lineas(ruta)) == 1, _lineas(ruta)

        # Y las once siguientes dicen que ya estaba.
        for h in hechos[1:]:
            assert "ya esta anotada" in h["reason"], h["reason"]

        # DOS JORNADAS, DOS ENTRADAS.
        otra = anotar_el_once(
            LA_JORNADA + 1,
            EL_ONCE,
            primer_partido=EL_PARTIDO + timedelta(days=7),
            desde=LA_VENTANA + timedelta(days=7),
            ahora=EL_PARTIDO + timedelta(days=7, hours=-1),
            ruta=ruta,
        )

        assert otra["anotado"] is True, otra

        assert set(onces_anotados(ruta)) == {
            LA_JORNADA,
            LA_JORNADA + 1,
        }


def test_sin_hora_no_se_anota_nada() -> None:
    """
    DOCTRINA 50: LA HORA ENTRA POR LA PUERTA.

    Ni la de ahora ni la del partido se buscan. Sin cualquiera de
    las dos no se anota: un respaldo que mirase el reloj haria
    que lo anotado dependiera de cuando corrio el ciclo, que es
    exactamente lo que este libro existe para quitar.
    """

    from src.analysis.el_once_que_jugo import anotar_el_once

    with tempfile.TemporaryDirectory() as carpeta:

        ruta = _libro(carpeta)

        sin_ahora = anotar_el_once(
            LA_JORNADA,
            EL_ONCE,
            primer_partido=EL_PARTIDO,
            desde=LA_VENTANA,
            ahora=None,
            ruta=ruta,
        )

        assert sin_ahora["anotado"] is False, sin_ahora

        assert "hora" in sin_ahora["reason"], sin_ahora["reason"]

        sin_partido = anotar_el_once(
            LA_JORNADA,
            EL_ONCE,
            primer_partido=None,
            desde=LA_VENTANA,
            ahora=UNA_HORA_ANTES,
            ruta=ruta,
        )

        assert sin_partido["anotado"] is False, sin_partido

        assert "primer partido" in sin_partido["reason"], (
            sin_partido["reason"]
        )

        sin_jornada = anotar_el_once(
            0,
            EL_ONCE,
            primer_partido=EL_PARTIDO,
            desde=LA_VENTANA,
            ahora=UNA_HORA_ANTES,
            ruta=ruta,
        )

        assert sin_jornada["anotado"] is False, sin_jornada

        assert _lineas(ruta) == [], _lineas(ruta)

    # Y NI UNA LLAMADA AL RELOJ EN EL MODULO.
    import ast

    fuente = (
        Path(__file__).parents[2]
        / "src"
        / "analysis"
        / "el_once_que_jugo.py"
    ).read_text(encoding="utf-8")

    for nodo in ast.walk(ast.parse(fuente)):

        if (
            isinstance(nodo, ast.Call)
            and isinstance(nodo.func, ast.Attribute)
            and nodo.func.attr in ("now", "utcnow", "today")
        ):
            raise AssertionError(
                "el libro del once mira el reloj del sistema: "
                "lo anotado dependeria de cuando corrio el ciclo"
            )


def test_las_jornadas_perdidas_se_cuentan_y_no_se_reconstruyen() -> None:
    """
    ESTAN PERDIDAS, Y SE DICE.

    Un once reconstruido a ojo daria una nota inventada, que es
    peor que no tener nota: una nota se usa para decidir.

    Y EL NUMERO SE CUENTA (regla 18). "6 jornadas perdidas"
    escrito a mano es verdad hoy y mentira la semana que viene —
    justo cuando nadie estara mirando este numero.
    """

    from src.analysis.el_once_que_jugo import (
        anotar_el_once,
        lo_que_se_perdio,
    )

    with tempfile.TemporaryDirectory() as carpeta:

        ruta = _libro(carpeta)

        OBSERVADAS = [4898, 4899, 4900, 4901, 4902, 4903, 4904]

        # 1. NADA ANOTADO: todas perdidas, y se dice que la
        #    medicion no ha empezado.
        antes = lo_que_se_perdio(OBSERVADAS, ruta=ruta)

        assert antes["irrecuperables"] == 7, antes

        assert antes["desde"] is None, antes

        assert "no ha empezado" in antes["reason"], antes

        # 2. SE ANOTA LA ULTIMA.
        anotar_el_once(
            4904,
            EL_ONCE,
            primer_partido=EL_PARTIDO,
            desde=LA_VENTANA,
            ahora=UNA_HORA_ANTES,
            ruta=ruta,
        )

        ahora = lo_que_se_perdio(OBSERVADAS, ruta=ruta)

        assert ahora["irrecuperables"] == 6, ahora

        assert ahora["sin_once"] == OBSERVADAS[:-1], ahora

        assert ahora["desde"] == 4904, ahora

        assert "irrecuperables" in ahora["reason"], ahora

        assert "empieza en la jornada 4904" in ahora["reason"], (
            ahora["reason"]
        )

        # 3. REGLA 24: sin jornadas observadas no se inventa nada.
        vacio = lo_que_se_perdio([], ruta=ruta)

        assert vacio["observadas"] == 0, vacio

        assert vacio["irrecuperables"] == 0, vacio

    # 4. Y EL MODULO NO RECONSTRUYE NADA.
    fuente = (
        Path(__file__).parents[2]
        / "src"
        / "analysis"
        / "el_once_que_jugo.py"
    ).read_text(encoding="utf-8")

    import ast

    llamadas = {
        nodo.func.attr
        for nodo in ast.walk(ast.parse(fuente))
        if isinstance(nodo, ast.Call)
        and isinstance(nodo.func, ast.Attribute)
    }

    for inventa in ("elegir_once", "mejor_once", "reconstruir"):
        assert inventa not in llamadas, (
            f"el libro llama a `{inventa}`: las jornadas "
            f"perdidas no se reconstruyen"
        )


TESTS = [
    test_el_once_se_anota_antes_del_primer_partido,
    test_las_dos_formas_del_once_valen,
    test_una_alineacion_a_medias_no_se_anota,
    test_no_se_congela_el_once_cinco_dias_antes,
    test_una_jornada_un_once,
    test_sin_hora_no_se_anota_nada,
    test_las_jornadas_perdidas_se_cuentan_y_no_se_reconstruyen,
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
        f"EL ONCE QUE JUGO V1: {len(TESTS) - fallos}/"
        f"{len(TESTS)} OK"
    )
    print("=" * 60)

    if fallos:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
