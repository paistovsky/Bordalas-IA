"""
Un sentido caducado se grita, y en los tres sitios.

SINTOMA (14/09/2026)

    El tablero de titulares se cayo el 17 de agosto y volvio el
    14 de septiembre. Las dos veces SOLO, sin que nadie lo
    tocara. Veintisiete dias con la via de fichar cerrada por
    falta de un dato.

    Y no fallaba la deteccion: la edad se calcula desde el 13/09
    y estaba a la vista. Fallaba que nadie gritara. Un numero
    dentro de una tabla de ocho filas no es un aviso — es un dato
    que hay que ir a buscar, y a una averia que dura veintisiete
    dias no la va a buscar nadie.

    Como volvio solo, se volvera a caer solo.

LO QUE VIGILAN ESTAS GUARDIAS

    1. Que un sentido pasado de su edad maxima produzca alarma en
       LOS TRES SITIOS: el bloque propio del estado, la banda de
       arriba y el registro de actividad.

    2. Que la alarma diga QUE DECISION QUEDA BLOQUEADA, no solo
       que el dato es viejo.

    3. Que el tope de cada sentido salga de cada cuanto cambia el
       dato, con su motivo escrito, y que los que no se pueden
       derivar salgan marcados «sin medir» en vez de con un
       numero redondo.

    4. Que el tablero se siga midiendo POR JORNADA y no por
       horas. Ese criterio ya estaba bien y no se toca.

REGLA 23

    No lee estado externo: los sentidos se construyen aqui.

REGLA 24

    Ninguna pasa con la lista de sentidos vacia.
"""

from __future__ import annotations

import re
from pathlib import Path

from datetime import datetime, timezone


RAIZ = Path(__file__).parents[2]

PANEL = (
    RAIZ
    / "dashboard-v8"
    / "src"
    / "components"
    / "LosSentidosPanel.jsx"
)

APP = RAIZ / "dashboard-v8" / "src" / "App.jsx"

NORMALIZA = RAIZ / "dashboard-v8" / "src" / "lib" / "status.js"


# LA HORA DE LA FOTO. Entra por la puerta (doctrina 50): ni esta
# guardia ni el modulo miran el reloj del sistema.
AHORA = datetime(2026, 9, 14, 18, 12, tzinfo=timezone.utc)

LA_JORNADA = 7


# EL TABLERO CAIDO, tal y como estuvo 27 dias: de la jornada 2,
# fechado el 17 de agosto.
TABLERO_CAIDO = {
    "starter_board_updated_at": "2026-08-17T20:00:00+00:00",
    "starter_board_matchday": 2,
    "starter_cache_status": "REFRESHED",
    "starter_source_error": None,
}

TABLERO_SANO = {
    "starter_board_updated_at": "2026-09-14T14:00:00+00:00",
    "starter_board_matchday": LA_JORNADA,
    "starter_cache_status": "REFRESHED",
    "starter_source_error": None,
}

OJEADOR_SANO = {
    "available": True,
    "generated_at": "2026-09-14T12:00:00+00:00",
    "matchday": LA_JORNADA,
    "sources": {"A": {"ok": True}},
    "sources_ok": 1,
    "players_count": 288,
}

PRENSA_SANA = {
    "available": True,
    "generated_at": "2026-09-14T07:00:00+00:00",
    "sources": {"MARCA": {"ok": True}},
    "players_with_signal": 20,
}

CALENDARIO_SANO = {
    "available": True,
    "fetched_at": "2026-09-14T16:00:00+00:00",
    "casan_todas": True,
    "reason": "Casan todas.",
}

VARA = {
    "active": True,
    "rows": [{"position": 1}],
    "window": {"matchdays": 3, "players": 81},
    "reason": "Vara activa.",
}

CAJA = {"cash_check": {"ok": True, "reason": "Cuadra."},
        "cash_reconstruction": {"events_read": 535}}

CATALOGO = {"plantillas": {"cuadra": True, "con_dueño": 128,
                           "libres": 400, "total": 528}}

MARCADOR = {"resumen": {"jornadas_medibles": 6,
                        "jornadas_fiables": 1},
            "reason": "Una jornada fiable."}

# LOS LIBROS, GUARDADOS HACE DOCE MINUTOS. La vuelta anterior
# llego a git: 18:00 contra las 18:12 de la foto.
GUARDADO_SANO = {
    "cuando": "2026-09-14T18:00:00+00:00",
    "ultimo_guardado_ok": "2026-09-14T18:00:00+00:00",
    "libros_en_disco": 12,
    "ok": True,
    "empujado": True,
    "intentos": 1,
    "motivo": None,
}

# Y LOS MISMOS LIBROS CON EL EMPUJON ATASCADO desde hace seis
# horas: por encima del tope de cinco.
GUARDADO_ATASCADO = {
    "cuando": "2026-09-14T18:11:00+00:00",
    "ultimo_guardado_ok": "2026-09-14T12:12:00+00:00",
    "libros_en_disco": 12,
    "ok": False,
    "empujado": False,
    "intentos": 3,
    "motivo": (
        "El empujon no salio en 3 intentos. Ultimo motivo de "
        "git: the remote contains work that you do not have "
        "locally."
    ),
}


def _sentidos(**cambios):
    from src.analysis.los_sentidos import los_sentidos

    argumentos = {
        "lineup": TABLERO_SANO,
        "scout": OJEADOR_SANO,
        "press": PRENSA_SANA,
        "vara": VARA,
        "rival_intelligence": CAJA,
        "toda_la_liga": CATALOGO,
        "calendario": CALENDARIO_SANO,
        "marcador": MARCADOR,
        "objetivos": [],
        "guardado_de_los_libros": GUARDADO_SANO,
        "jornada_de_hoy": LA_JORNADA,
        "ahora": AHORA,
    }

    argumentos.update(cambios)

    return los_sentidos(**argumentos)


def _fila(visto, nombre):
    for fila in visto["sentidos"]:
        if fila["sentido"] == nombre:
            return fila

    raise AssertionError(f"no esta el sentido {nombre}")


def _jsx_sin_comentarios(fuente: str) -> str:
    fuente = re.sub(r"/\*.*?\*/", " ", fuente, flags=re.S)

    return re.sub(r"(?m)^\s*//.*$", " ", fuente)


# ============================================================
# 1. UN SENTIDO CADUCADO SE GRITA, EN LOS TRES SITIOS
# ============================================================


def test_un_sentido_caducado_se_grita() -> None:
    """
    Alarma en el estado, en la banda de arriba y en el registro.

    LOS TRES, NO UNO

        Un aviso que solo vive en una pantalla se pierde cuando
        esa pantalla no se abre. Y el cuadro de los sentidos
        justo no se abrio durante veintisiete dias.
    """

    # CON TODO SANO NO SE GRITA.
    #
    #     Una alarma que suena siempre deja de ser una alarma a
    #     los dos dias (regla 37: lo enciende el hecho).
    sano = _sentidos()

    # REGLA 24: con la lista vacia esto no probaria nada.
    assert len(sano["sentidos"]) == 9, sano

    assert sano["alarma"]["hay"] is False, sano["alarma"]
    assert sano["alarma"]["cuantos"] == 0, sano["alarma"]

    # AHORA EL TABLERO CAIDO, como estuvo 27 dias.
    roto = _sentidos(lineup=TABLERO_CAIDO)

    assert len(roto["sentidos"]) == 9, roto

    # 1. SITIO UNO: EL BLOQUE PROPIO DEL ESTADO.
    alarma = roto["alarma"]

    assert alarma["hay"] is True, alarma
    assert alarma["cuantos"] == 1, alarma

    grito = alarma["sentidos"][0]

    assert grito["sentido"] == "Tablero de titulares", grito

    # 2. DICE QUE QUEDA BLOQUEADO, no solo que el dato es viejo.
    #
    #    "El tablero es de la jornada 2" es un dato. "No se puja
    #    para mejorar el once" es la razon por la que alguien se
    #    levanta a mirarlo.
    assert grito["que_queda_bloqueado"], grito

    assert "no se puja" in grito["que_queda_bloqueado"].lower(), (
        grito["que_queda_bloqueado"]
    )

    # Y con los dos numeros: la jornada del dato y la de hoy.
    assert "jornada 2" in grito["texto"], grito
    assert str(LA_JORNADA) in grito["texto"], grito

    # Y la fila lo lleva marcado.
    tablero = _fila(roto, "Tablero de titulares")

    assert tablero["edad_maxima"]["caducado"] is True, tablero

    # 3. SITIO DOS: LA BANDA DE ARRIBA.
    app = _jsx_sin_comentarios(APP.read_text(encoding="utf-8"))

    assert "alarmaDeLosSentidos" in app, (
        "la banda de arriba no pinta la alarma de los sentidos"
    )

    assert "que_queda_bloqueado" in app, (
        "la banda de arriba no dice que decision queda bloqueada"
    )

    # Y llega hasta la pantalla: sin esto, `raw` la trae y
    # `normalizeStatus` la tira por el camino.
    normaliza = NORMALIZA.read_text(encoding="utf-8")

    assert "alarmaDeLosSentidos" in normaliza, (
        "`normalizeStatus` no publica la alarma: la telemetria la "
        "escribe y la pantalla nunca la ve"
    )

    # 4. SITIO TRES: EL REGISTRO DE ACTIVIDAD.
    from src.telemetry.dashboard_state import (
        _con_la_alarma_de_sentidos,
    )

    registro = _con_la_alarma_de_sentidos([], roto, AHORA)

    assert len(registro) == 1, registro

    linea = registro[0]

    assert linea["action"] == "SENTIDO_CADUCADO", linea
    assert linea["phase"] == "SENTIDOS", linea
    assert "Tablero de titulares" in linea["label"], linea

    # NO ES UNA ESCRITURA Y SE DICE. Colarla entre las escrituras
    # seria afirmar que Pepe hizo algo, y no hizo nada.
    assert linea["write_performed"] is False, linea

    # LA HORA ENTRA POR LA PUERTA (doctrina 50).
    assert linea["timestamp"] == AHORA.isoformat(), linea

    # Y el motivo dice lo que queda bloqueado.
    assert "Queda bloqueado" in linea["reason"], linea

    # 5. SIN ALARMA NO SE ESCRIBE NADA EN EL REGISTRO.
    #
    #    Una linea por vuelta diciendo "todo bien" son 8.760
    #    lineas al año que tapan las que importan.
    limpio = _con_la_alarma_de_sentidos(
        [{"action": "ALGO"}], sano, AHORA
    )

    assert len(limpio) == 1, limpio
    assert limpio[0]["action"] == "ALGO", limpio

    # 6. Y NO SE GRITA POR NO SABER.
    #
    #    Sin marca de tiempo la edad no se puede medir. Eso NO es
    #    "caducado": es que falta un dato, y ya lo cuenta el
    #    estado MUERTO. Gritar aqui haria que la banda estuviera
    #    encendida siempre.
    sin_fecha = _sentidos(
        scout={**OJEADOR_SANO, "generated_at": None}
    )

    ojeador = _fila(sin_fecha, "Ojeador de precios")

    assert ojeador["edad_maxima"]["caducado"] is False, ojeador
    assert ojeador["edad_maxima"]["medible"] is False, ojeador


# ============================================================
# 2. EL TOPE SALE DE CADA CUANTO CAMBIA EL DATO
# ============================================================


def test_la_edad_maxima_no_es_un_numero_redondo() -> None:
    """
    Cada tope con su motivo, y los que no se pueden derivar dichos.

    LO QUE ROMPE ESTA GUARDIA

        Un numero puesto a ojo. El proyecto ya arrastra uno
        —`DIAS_PARA_VIEJO`— y viaja publicado como «sin medir»
        justamente para que se vea que no esta medido.

    Y EL TABLERO SE MIDE POR JORNADA

        Un tablero de la jornada 2 no dice nada de la 7 aunque se
        hubiera bajado hace una hora. Ese criterio ya estaba bien
        y no se toca: esta guardia lo fija.
    """

    from src.analysis.los_sentidos import (
        EDAD_MAXIMA,
        POR_HORAS,
        POR_JORNADA,
        SIN_RELOJ_PROPIO,
    )

    visto = _sentidos()

    # REGLA 24.
    assert len(visto["sentidos"]) == 9, visto

    # 1. LOS NUEVE TRAEN TOPE, Y TODOS CON MOTIVO ESCRITO.
    for fila in visto["sentidos"]:

        tope = fila.get("edad_maxima") or {}

        assert tope.get("criterio"), fila

        assert tope.get("motivo"), (
            f"{fila['sentido']} trae un tope sin motivo: un "
            f"numero sin justificacion es un umbral inventado"
        )

        # UN TOPE EN HORAS SIN MOTIVO ES UN NUMERO REDONDO.
        if tope["criterio"] == POR_HORAS:
            assert tope.get("horas"), fila
            assert tope.get("medida") is True, fila

        # Y SIN TOPE, «SIN MEDIR» DICHO.
        if tope["criterio"] == SIN_RELOJ_PROPIO:
            assert tope.get("horas") is None, fila
            assert tope.get("medida") is False, fila

    # 2. EL TABLERO, POR JORNADA Y NO POR HORAS.
    tablero = _fila(visto, "Tablero de titulares")

    assert (
        tablero["edad_maxima"]["criterio"] == POR_JORNADA
    ), tablero

    assert tablero["edad_maxima"]["horas"] is None, tablero

    # Y LA PRUEBA DE QUE NO ES POR HORAS: un tablero de hace un
    # rato pero de la jornada anterior esta caducado igual.
    recien = _sentidos(
        lineup={
            **TABLERO_SANO,
            "starter_board_updated_at": "2026-09-14T18:00:00+00:00",
            "starter_board_matchday": LA_JORNADA - 1,
        }
    )

    de_ayer = _fila(recien, "Tablero de titulares")

    assert de_ayer["edad"]["horas"] < 24, (
        f"el tablero de la prueba tiene {de_ayer['edad']} y la "
        f"gracia es que sea reciente: por horas pasaria, y aun "
        f"asi tiene que caducar"
    )

    assert de_ayer["edad_maxima"]["caducado"] is True, de_ayer

    assert recien["alarma"]["hay"] is True, recien["alarma"]

    # 3. LOS MOTIVOS APUNTAN A DONDE SE MIDIO.
    #
    #    No basta con que haya una frase: tiene que decir DE
    #    DONDE sale el numero, que es lo que impide que el
    #    siguiente lo cambie a ojo.
    assert "RESET_HOUR_MADRID" in (
        EDAD_MAXIMA["Ojeador de precios"]["motivo"]
    ), EDAD_MAXIMA["Ojeador de precios"]

    assert "DEFAULT_TTL_SECONDS" in (
        EDAD_MAXIMA["Prensa"]["motivo"]
    ), EDAD_MAXIMA["Prensa"]

    assert "calculate_refresh_" in (
        EDAD_MAXIMA["Calendario de LaLiga"]["motivo"]
    ), EDAD_MAXIMA["Calendario de LaLiga"]

    # 4. Y LA PANTALLA PINTA EL TOPE Y SU MOTIVO.
    jsx = _jsx_sin_comentarios(PANEL.read_text(encoding="utf-8"))

    assert "CUÁNTO PUEDE ENVEJECER" in jsx, (
        "el cuadro no enseña cuanto puede envejecer cada sentido"
    )

    assert "edad_maxima" in jsx, (
        "el cuadro no lee el tope de cada sentido"
    )

    assert "sin medir" in jsx, (
        "el cuadro no dice cuales van sin medir"
    )


# ============================================================
# 3. SI LOS LIBROS NO SE GUARDAN, SE GRITA (15/09/2026)
# ============================================================


def test_si_los_libros_no_se_guardan_se_grita() -> None:
    """
    El empujon lleva horas fallando y la pantalla tiene que
    decirlo.

    POR QUE ESTA FILA NACE HOY

        Hasta hoy un empujon fallido ponia LA VUELTA ENTERA EN
        ROJO, y eso se veia solo. Desde hoy no: la vuelta sale
        verde y el ciclo sigue, que es lo correcto —un seguro no
        puede tirar el coche al rio—.

        Pero el precio de esa decision es que el fallo se vuelve
        invisible. Esta guardia es lo que lo paga: si el empujon
        se atasca, hay que enterarse ANTES de que la cache se
        desaloje, no despues.
    """

    from src.estado.los_libros import LIBROS

    # REGLA 24: SIN LIBROS DECLARADOS ESTO NO PRUEBA NADA.
    #
    #     Si la lista se quedara vacia no habria nada que
    #     guardar, el guardado nunca fallaria y esta guardia
    #     pasaria en verde para siempre sobre un proyecto que ha
    #     dejado de proteger sus libros.
    assert LIBROS, (
        "no hay ni un libro declarado en `los_libros.py`: sin "
        "libros que guardar esta alarma no vigila nada"
    )

    assert GUARDADO_SANO["libros_en_disco"] > 0, (
        "el montaje dice que no hay libros en el disco: la "
        "prueba no estaria mirando un guardado de verdad"
    )

    # 1. RECIEN GUARDADO: NI UNA PALABRA.
    #
    #    Una alarma que suena siempre deja de ser una alarma.
    sano = _sentidos()

    fila = _fila(sano, "El guardado de los libros")

    assert fila["edad_maxima"]["caducado"] is False, fila

    assert sano["alarma"]["hay"] is False, sano["alarma"]

    # Y LA LINEA DE LA PANTALLA, TAL CUAL SE VERA.
    assert "hace 12 min" in fila["de_cuando"], fila["de_cuando"]

    assert (
        str(GUARDADO_SANO["libros_en_disco"]) in fila["de_cuando"]
    ), fila["de_cuando"]

    assert "en git" in fila["de_cuando"], fila["de_cuando"]

    assert fila["que_bloquea"] is None, fila

    # 2. EL EMPUJON ATASCADO SEIS HORAS: SE GRITA.
    roto = _sentidos(guardado_de_los_libros=GUARDADO_ATASCADO)

    atascada = _fila(roto, "El guardado de los libros")

    assert atascada["edad_maxima"]["caducado"] is True, (
        f"seis horas sin llegar a git y no salta la alarma: "
        f"{atascada}"
    )

    assert roto["alarma"]["hay"] is True, roto["alarma"]

    gritos = [
        g["sentido"] for g in roto["alarma"]["sentidos"]
    ]

    assert "El guardado de los libros" in gritos, gritos

    # 3. Y DICE POR QUE, con la frase del guardador entera.
    #
    #    No se reescribe aqui: la pantalla no tiene autoridad
    #    sobre el motivo por el que git rechazo el empujon.
    assert (
        atascada["que_bloquea"] == GUARDADO_ATASCADO["motivo"]
    ), atascada

    assert "el empujón falla" in atascada["de_cuando"], (
        atascada["de_cuando"]
    )

    # 4. SIN DATO NO ES "TODO BIEN", pero tampoco es un grito.
    #
    #    La cache desalojada o la primera vuelta dejan la fila
    #    sin fichero: MUERTO y a la vista, sin inventar una
    #    averia que no se ha medido.
    mudo = _sentidos(guardado_de_los_libros=None)

    callada = _fila(mudo, "El guardado de los libros")

    assert callada["estado"] == "MUERTO", callada

    assert "sin dato" in callada["de_cuando"], callada

    assert callada["edad_maxima"]["caducado"] is False, (
        "sin saber cuando se guardo por ultima vez no se puede "
        "afirmar que lleve horas sin guardarse"
    )

    # 5. Y LA PANTALLA TIENE QUE PINTARLO.
    #
    #    La fila puede estar perfecta en el estado y no verse. El
    #    tablero estuvo 27 dias caido con su edad calculada y a
    #    la vista dentro de un cuadro que nadie abria: por eso
    #    esto ademas baja a una linea de AUDITORIA.
    telemetria = (
        RAIZ / "src" / "telemetry" / "dashboard_state.py"
    ).read_text(encoding="utf-8")

    assert '"librosGuardados"' in telemetria, (
        "la telemetria no publica `librosGuardados`: la linea de "
        "AUDITORIA se quedaria en SIN DATO para siempre"
    )

    auditoria = _jsx_sin_comentarios(
        (
            RAIZ
            / "dashboard-v8"
            / "src"
            / "pages"
            / "AuditPage.jsx"
        ).read_text(encoding="utf-8")
    )

    assert "librosGuardados" in auditoria, (
        "AUDITORIA no lee `librosGuardados`"
    )

    assert "Libros guardados" in auditoria, (
        "AUDITORIA no tiene la linea de los libros guardados"
    )

    # LA FRASE NO SE MONTA EN EL NAVEGADOR. Si la pantalla
    # compusiera su propia version habria dos verdades, y el dia
    # que discreparan nadie sabria cual mirar.
    assert "de_cuando" in auditoria, (
        "la linea de AUDITORIA no usa la frase que monta "
        "`los_sentidos`: se la esta inventando"
    )

    for inventado in ("en git", "el empujón falla"):
        assert inventado not in auditoria, (
            f"la pantalla escribe {inventado!r} por su cuenta en "
            f"vez de pintar lo que publica la telemetria"
        )

    assert "SIN DATO" in auditoria, (
        "sin dato, la linea tiene que decirlo: una telemetria "
        "que no publico nada no es «se estan guardando»"
    )


def test_el_tope_de_los_libros_sale_de_los_disparos() -> None:
    """
    Las cinco horas no son un numero redondo puesto a ojo.

    Salen del hueco mas largo entre dos disparos declarados en
    `config/disparos.json` —la ventana del reset, de 04:50 a
    07:15 de Madrid— contado dos veces.

    Esta guardia RECALCULA ese hueco desde el fichero. El dia que
    alguien cambie el latido y se olvide de esto, salta.
    """

    import json

    from src.analysis.los_sentidos import (
        HORAS_SIN_GUARDAR,
        HUECO_MAS_LARGO_MINUTOS,
    )

    declaracion = json.loads(
        (RAIZ / "config" / "disparos.json").read_text(
            encoding="utf-8"
        )
    )

    # TODOS LOS DISPAROS DEL DIA, en minutos desde medianoche.
    minutos = set()

    latido = declaracion.get("latido") or {}

    for hora in latido.get("horas") or []:
        minutos.add(hora * 60 + int(latido.get("minuto") or 0))

    for puntual in declaracion.get("puntuales") or []:
        hh, _, mm = str(puntual.get("madrid") or "").partition(":")
        minutos.add(int(hh) * 60 + int(mm))

    # REGLA 24: sin disparos declarados no hay hueco que medir.
    assert len(minutos) >= 2, (
        f"`config/disparos.json` no declara disparos "
        f"suficientes: {sorted(minutos)}"
    )

    ordenados = sorted(minutos)

    # El dia da la vuelta: el hueco de la noche tambien cuenta.
    huecos = [
        b - a for a, b in zip(ordenados, ordenados[1:])
    ] + [ordenados[0] + 24 * 60 - ordenados[-1]]

    assert max(huecos) == HUECO_MAS_LARGO_MINUTOS, (
        f"el hueco mas largo entre disparos son "
        f"{max(huecos)} min y `los_sentidos` dice "
        f"{HUECO_MAS_LARGO_MINUTOS}: alguien cambio el latido y "
        f"no toco el tope de los libros"
    )

    # DOS HUECOS SEGUIDOS, redondeando hacia arriba. Uno puede
    # ser una vuelta perdida; dos seguidos es que no vuelve.
    assert (
        HORAS_SIN_GUARDAR * 60 >= 2 * HUECO_MAS_LARGO_MINUTOS
    ), (
        f"el tope ({HORAS_SIN_GUARDAR} h) es menor que dos "
        f"huecos ({2 * HUECO_MAS_LARGO_MINUTOS} min): gritaria "
        f"por una sola vuelta perdida"
    )

    # Y NO TANTO QUE SE VUELVA INUTIL: si se pudiera pasar un
    # dia entero sin guardar, la cache se habria desalojado
    # antes de que nadie mirara.
    assert HORAS_SIN_GUARDAR * 60 <= 3 * HUECO_MAS_LARGO_MINUTOS, (
        f"el tope ({HORAS_SIN_GUARDAR} h) deja pasar tres huecos "
        f"enteros sin avisar"
    )

    # Y VIAJA CON SU MOTIVO, como los demas.
    from src.analysis.los_sentidos import EDAD_MAXIMA

    tope = EDAD_MAXIMA["El guardado de los libros"]

    assert tope["horas"] == HORAS_SIN_GUARDAR, tope

    assert tope["medida"] is True, tope

    assert "disparos.json" in tope["motivo"], (
        f"el motivo no dice de donde sale el numero: "
        f"{tope['motivo']}"
    )


TESTS = [
    test_un_sentido_caducado_se_grita,
    test_la_edad_maxima_no_es_un_numero_redondo,
    test_si_los_libros_no_se_guardan_se_grita,
    test_el_tope_de_los_libros_sale_de_los_disparos,
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
        f"LA ALARMA DE LOS SENTIDOS V1: "
        f"{len(TESTS) - fallos}/{len(TESTS)} OK"
    )
    print("=" * 60)

    if fallos:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
