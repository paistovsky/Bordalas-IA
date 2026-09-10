"""
Lo desconocido sale como desconocido. Doctrina 35 y 36.

SINTOMA

    Tres fallos de zona horaria en un dia -el cron externo, el
    calculo interno y `meta.generated_at`- y dos defectos
    benignos que se tragaron el caso mas importante:

        THREAT[nivel] || "pill idle"   -> VERY_HIGH en gris
        state or ABIERTO               -> permiso para vender

CAUSA

    Las dos familias fallan igual: NO fallan ruidosamente. Dan
    una respuesta plausible y equivocada, sin excepcion, sin
    registro, sin nada que buscar despues. Un instante sin zona
    es correcto para dos lecturas distintas; un `||` benigno
    informa de calma con la misma cara con la que informaria de
    calma verdadera.

CONSECUENCIA

    Estas guardias no comprueban un calculo: comprueban una
    FORMA. Que ninguna tabla de severidad tenga un defecto
    tranquilo, que ninguna ruta de decision conceda por la
    veracidad de un valor, y que ninguna hora cruce un limite
    sin su zona.
"""

from __future__ import annotations

import re

from pathlib import Path


RAIZ = Path(__file__).parents[2]

DASHBOARD = RAIZ / "dashboard-v8" / "src"


def _sin_comentarios(fuente: str) -> str:
    """
    El codigo, sin las notas que cuentan el incidente.

    Dos guardias han tropezado ya con lo mismo: el fallo esta
    contado por escrito -"aqui ponia `state or ABIERTO`",
    "`minutesOld` la leia como hora LOCAL"- y la guardia leia esa
    nota como si fuera codigo vivo.

    Una guardia que obligue a borrar la explicacion del fallo
    para pasar es una guardia que hace dano: la proxima persona
    se encuentra el arreglo sin el motivo.
    """

    limpio = []

    for linea in fuente.splitlines():

        desnuda = linea.lstrip()

        if desnuda.startswith(("#", "//", "*", "/*")):
            continue

        limpio.append(linea.split("//")[0])

    return chr(10).join(limpio)


def _lee(ruta: Path) -> str:
    if not ruta.exists():
        raise AssertionError(f"no existe {ruta}")

    return ruta.read_text(encoding="utf-8")


# ============================================================
# 1. NINGUNA TABLA DE SEVERIDAD CON DEFECTO TRANQUILO
# ============================================================


# Las tablas que traducen un estado a un TONO. Son las que
# pintan alarmas: si una cae al gris, la alarma desaparece.
TABLAS_DE_ALARMA = [
    ("StandingsIntelPanel.jsx", "THREAT"),
    ("PressPanel.jsx", "TONO"),
    ("SolvencyClockPanel.jsx", "TONO"),
    ("ScoutPanel.jsx", "DIRECCION"),
    ("ScoutPanel.jsx", "ACUERDO"),
    ("PosiblesCambiosPanel.jsx", "TONO"),
]

# Lo que NO puede ir detras de un `||` cuando se traduce una
# severidad: son los tonos que significan "no pasa nada".
BENIGNOS = (
    "pill idle",
    "idle",
    "dim",
    "pill ok",
    "ok",
)


def test_ninguna_tabla_de_alarma_cae_en_lo_benigno() -> None:
    """
    EL INCIDENTE DEL 10/09.

    `VERY_HIGH` no estaba en `THREAT` y caia al gris del `||`: la
    amenaza mas alta del tablero se pintaba exactamente igual que
    "ninguna". El caso que mas urgia ver era el unico invisible.

    El fallo no fue olvidar una fila: fue que hubiera un defecto
    capaz de tragarsela sin decir nada.
    """

    fallos = []

    for fichero, tabla in TABLAS_DE_ALARMA:

        fuente = _lee(DASHBOARD / "components" / fichero)

        for linea in fuente.splitlines():

            if f"{tabla}[" not in linea or "||" not in linea:
                continue

            despues = linea.split("||", 1)[1]

            for benigno in BENIGNOS:

                if f'"{benigno}"' in despues:
                    fallos.append(
                        f"{fichero}: {tabla} cae en "
                        f"'{benigno}' -> {linea.strip()}"
                    )

    assert not fallos, (
        "una tabla de severidad se traga lo desconocido como "
        "benigno:\n  " + "\n  ".join(fallos)
    )

    # Regla 24: la guardia no pasa con las manos vacias.
    assert len(TABLAS_DE_ALARMA) >= 6, TABLAS_DE_ALARMA


def test_el_tono_desconocido_existe_y_no_se_parece_a_ninguno() -> None:
    """
    Un tono de "no lo se" que se pareciera al de "no pasa nada"
    seria el mismo fallo con otro color. Y si no esta en el CSS,
    la clase no pinta nada: invisible otra vez.
    """

    fuente = _lee(DASHBOARD / "lib" / "tono.js")

    assert "TONO_DESCONOCIDO" in fuente, (
        "no hay un tono con nombre para lo desconocido"
    )

    css = _lee(DASHBOARD / "styles.css")

    assert ".pill.unknown{" in css, (
        "el tono desconocido no existe en el CSS: la clase se "
        "pinta transparente y vuelve a ser invisible"
    )


def test_lo_desconocido_ensena_el_valor_que_no_supo_traducir() -> None:
    """
    Un guion donde deberia ir el valor crudo tapa la unica pista
    de que llego. Si manana aparece un `VERY_HIGH` nuevo, hay que
    poder ver que aparecio.
    """

    fuente = _lee(DASHBOARD / "lib" / "tono.js")

    assert "conocido: false" in fuente, (
        "`tonoDe` no distingue lo que tradujo de lo que no"
    )

    assert "clave" in fuente.split("conocido: false")[0][-400:], (
        "la rama de desconocido no devuelve el valor crudo"
    )


def test_los_paneles_de_alarma_usan_el_ayudante() -> None:
    """
    Cada panel resolviendo esto por su cuenta es como llegamos
    aqui: seis tablas y seis defectos distintos. Un solo sitio
    que decida que es "desconocido".
    """

    faltan = [
        fichero
        for fichero, _ in TABLAS_DE_ALARMA
        if "tonoDe" not in _lee(DASHBOARD / "components" / fichero)
    ]

    assert not faltan, (
        f"estos paneles pintan alarmas sin pasar por `tonoDe`: "
        f"{faltan}"
    )


def test_las_rutas_de_decidir_del_mercado_tambien() -> None:
    """
    La compuerta de ritmo y la decision del tablero no pintan una
    alarma: DECIDEN. Un estado que no conocemos pintado como uno
    tranquilo es peor aqui que en ningun otro sitio.
    """

    fuente = _lee(DASHBOARD / "pages" / "MarketPage.jsx")

    for tabla in ("COMPUERTA", "DECISION", "DIVERGENCIA", "VIA"):

        patron = re.compile(
            r"%s\[[^\]]+\]\s*\|\|" % tabla
        )

        assert not patron.search(fuente), (
            f"{tabla} sigue eligiendo por defecto en la pagina "
            f"que decide que se compra"
        )


# ============================================================
# 2. NINGUN PERMISO POR LA VERACIDAD DE UN VALOR
# ============================================================


def test_ningun_estado_que_falta_se_lee_como_sano() -> None:
    """
    `str(ficha.get("status") or "ok")`.

    Un jugador sin ficha de estado entraba en el tablero de
    fichajes como sano, y el motor de puja lo compraba. Medido el
    10/09: 0 de 20 fichas llegan sin estado, asi que esto no
    cambiaba ninguna puja de ese dia. Cambia el dia que el
    catalogo venga cojo, que es exactamente cuando importa y
    cuando nadie estaria mirando.
    """

    for fichero in (
        "acquisition_board.py",
        "intelligent_bid_engine.py",
    ):

        fuente = _lee(Path(__file__).parent / fichero)

        assert 'or "ok"' not in fuente, (
            f"{fichero}: un estado que falta se sigue leyendo "
            f"como sano"
        )

        assert "ESTADO_DESCONOCIDO" in fuente, (
            f"{fichero}: no hay nombre para el estado ausente"
        )


def test_solo_se_puja_por_quien_sabemos_que_esta_bien() -> None:
    """
    Habia dos defectos benignos encadenados: la ficha sin estado
    se leia "ok", y ademas "unknown" estaba en la lista de los
    que SI se pujan. Un jugador del que no sabemos si esta
    disponible se compraba igual que uno del que sabemos que si.
    """

    fuente = _lee(
        Path(__file__).parent / "intelligent_bid_engine.py"
    )

    assert 'not in {"ok", "unknown"}' not in fuente, (
        "`unknown` sigue en la lista de los que se pujan"
    )

    assert 'if estado != "ok":' in fuente, (
        "la puerta de la puja ya no compara contra `ok` exacto"
    )


def test_el_permiso_de_vender_se_compara_exacto() -> None:
    """
    `state or ABIERTO`: una marca VIAJE en blanco daba permiso
    para vender. Lo cazo una guardia propia, no una prueba.
    """

    fuente = _lee(Path(__file__).parent / "salida_del_viaje.py")

    # SIN LOS COMENTARIOS.
    #
    # El fallo esta contado por escrito ahi dentro -"aqui ponia
    # `state or ABIERTO`"- y esa nota tiene que poder quedarse.
    # Una guardia que obligue a borrar la explicacion del
    # incidente para pasar es una guardia que hace dano.
    codigo = "\n".join(
        linea
        for linea in fuente.splitlines()
        if not linea.lstrip().startswith("#")
    )

    assert "or ABIERTO" not in codigo, (
        "un VIAJE sin marca vuelve a conceder permiso de venta"
    )

    assert "== ABIERTO" in codigo, (
        "el permiso de venta no se concede por comparacion exacta"
    )


# ============================================================
# 3. NINGUNA HORA SIN ZONA CRUZANDO UN LIMITE
# ============================================================


def test_la_foto_se_normaliza_antes_de_compararla() -> None:
    """
    `meta.generated_at` se publica en hora de Madrid SIN zona.
    Leerlo como UTC lo adelanta dos horas: la cuenta atras habria
    dicho "el ciclo llego" cuando no ha llegado.
    """

    # La comparacion contra el cron vive en la cabecera desde el
    # 10/09; la tira sigue usando la foto para el cierre de
    # jornada. Las DOS cruzan un limite, asi que las dos tienen
    # que normalizar.
    cabecera = _lee(DASHBOARD / "App.jsx")

    assert "madridNaiveAUTC" in cabecera, (
        "la pastilla compara la foto con el cron sin ponerle zona"
    )

    tira = _sin_comentarios(
        _lee(DASHBOARD / "components" / "KpiStrip.jsx")
    )

    assert "minutesOld" not in tira, (
        "la tira lee la foto como hora local: para quien no este "
        "en Madrid, el cierre de jornada sale con dos horas de "
        "menos y sin avisar"
    )

    relojes = _lee(DASHBOARD / "lib" / "relojes.js")

    assert "madridNaiveAUTC" in relojes, (
        "no existe la normalizacion en el sitio que sabe de horas"
    )


def test_la_hora_de_madrid_se_pide_a_la_base_de_zonas() -> None:
    """
    En marzo y octubre Madrid no es +2. Codificar el desfase es
    el fallo del cron externo -CET contra CEST- que dejo la
    ventana del reset sin abrir durante dos semanas.
    """

    fuente = _lee(DASHBOARD / "lib" / "relojes.js")

    assert "Europe/Madrid" in fuente, (
        "la zona no se pide por nombre a la base de zonas"
    )

    assert "Intl.DateTimeFormat" in fuente, (
        "el desfase se esta codificando a mano"
    )


# ============================================================
# 4. LA PANTALLA PUEDE AVISAR DE QUE SE EQUIVOCA
# ============================================================


def test_el_credito_derivado_se_contrasta_con_lo_medido() -> None:
    """
    El credito de la tira sale de restar:

        credito = deuda maxima + comprometido - saldo

    Con lo cual los cuatro numeros cuadran SIEMPRE, incluso si
    `maximumBid` viniera mal: el credito absorberia el error
    entero y seguirian sumando tan tranquilos.

    Una pantalla que no puede estar equivocada tampoco puede
    avisar de que lo esta. Por eso se contrasta contra la otra
    via, la que no pasa por `maximumBid`.
    """

    fuente = _lee(DASHBOARD / "components" / "KpiStrip.jsx")

    assert "creditoMedido" in fuente, (
        "la tira no contrasta el credito contra la via medida"
    )

    assert "NO CUADRA" in fuente, (
        "el descuadre no se canta en la etiqueta"
    )

    assert 'tone={!cuadra ? "bad"' in fuente, (
        "el descuadre no sale en ROJO"
    )


def test_la_via_medida_no_pasa_por_maximum_bid() -> None:
    """
    Si la segunda via se calculara desde `maximumBid`, las dos
    coincidirian siempre y el contraste no comprobaria nada. Todo
    el valor esta en que sean INDEPENDIENTES:

        via 1   deuda maxima + comprometido - saldo
        via 2   valor de plantilla x 0,25
    """

    from src.analysis.linea_de_credito import (
        LINEA_DE_CREDITO,
        headroom_de,
    )

    assert LINEA_DE_CREDITO == 0.25, LINEA_DE_CREDITO

    # La medicion del dueno, 09/09: 50.040.000 x 0,25.
    assert headroom_de(50_040_000) == 12_510_000, (
        headroom_de(50_040_000)
    )

    # Y no depende de maximumBid: no lo recibe siquiera.
    import inspect

    firma = inspect.signature(headroom_de)

    assert "maximum_bid" not in firma.parameters, (
        "la via medida recibe `maximumBid`: entonces no es una "
        "segunda via, es la misma"
    )

    publicador = _lee(
        RAIZ / "src" / "telemetry" / "dashboard_state.py"
    )

    assert '"credito"' in publicador, (
        "la via medida no se publica: la tira no puede contrastar "
        "contra nada"
    )


TESTS = [
    test_ninguna_tabla_de_alarma_cae_en_lo_benigno,
    test_el_tono_desconocido_existe_y_no_se_parece_a_ninguno,
    test_lo_desconocido_ensena_el_valor_que_no_supo_traducir,
    test_los_paneles_de_alarma_usan_el_ayudante,
    test_las_rutas_de_decidir_del_mercado_tambien,
    test_ningun_estado_que_falta_se_lee_como_sano,
    test_solo_se_puja_por_quien_sabemos_que_esta_bien,
    test_el_permiso_de_vender_se_compara_exacto,
    test_la_foto_se_normaliza_antes_de_compararla,
    test_la_hora_de_madrid_se_pide_a_la_base_de_zonas,
    test_el_credito_derivado_se_contrasta_con_lo_medido,
    test_la_via_medida_no_pasa_por_maximum_bid,
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
        f"LO DESCONOCIDO V1: "
        f"{len(TESTS) - fallos}/{len(TESTS)} OK"
    )
    print("=" * 60)

    if fallos:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
