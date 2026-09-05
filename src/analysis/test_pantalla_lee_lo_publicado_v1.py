"""
Lo que se publica, se ve. Y lo que se ve, se publica.

SINTOMA

    El fallo mas repetido de este repo, contado por sus propios
    comentarios: "Septima vez en dos dias que un dato se calcula,
    se publica y se pierde en el ultimo metro."

    `priorities` llegaba en el JSON y el normalizador no lo
    copiaba: la columna COLA DE DECISIONES se pintaba en blanco.
    `rival_squads` se calculaba desde el 20/08 y llegaba vacio.
    El libro de pujas se escribe desde el 03/09 y no lo enseñaba
    nadie.

CAUSA

    Entre el generador de `status.json` y la pantalla hay dos
    saltos, y cada uno se puede romper sin que nada avise:

        dashboard_state.py  ->  status.js  ->  el componente

    El primero es Python y el segundo JavaScript, asi que ningun
    test de los que hay cruza los dos.

CONSECUENCIA

    Un bloque calculado que no se pinta cuesta lo mismo que no
    calcularlo, y ademas engaña: en el JSON esta, asi que parece
    hecho.

    Esta guardia cose los dos saltos para los bloques nuevos. No
    comprueba que se vean bonitos -eso no lo puede comprobar un
    test- sino que la cadena esta entera: el backend lo escribe,
    el normalizador lo copia, un componente lo lee y una pagina
    monta ese componente.
"""

from __future__ import annotations

import re

from pathlib import Path


DASHBOARD = Path("dashboard-v8/src")
ESTADO = Path("src/telemetry/dashboard_state.py")
NORMALIZADOR = DASHBOARD / "lib" / "status.js"


# (clave en status.json, nombre en el normalizador, componente,
#  paginas donde tiene que estar montado)
CADENAS = [
    (
        "bid_outcomes",
        "bidOutcomes",
        "BidOutcomesPanel",
        ["AuditPage.jsx"],
    ),
    (
        "rival_squads",
        "rivalSquads",
        None,                       # ya se pinta en SquadPage
        [],
    ),
    (
        "race",
        "race",
        "RacePanel",
        ["HomePage.jsx"],
    ),
    (
        "season_horizon",
        "seasonHorizon",
        "SeasonHorizonPanel",
        ["MarketPage.jsx"],
    ),
    (
        "roster_expansion",
        "rosterExpansion",
        "RosterExpansionPanel",
        ["MarketPage.jsx"],
    ),
    (
        "scout",
        "scout",
        "ScoutPanel",
        ["BrainPage.jsx"],
    ),
    (
        "concentration",
        "concentration",
        "ConcentrationPanel",
        ["SquadPage.jsx"],
    ),
    (
        "sale_order",
        "saleOrder",
        "SaleOrderPanel",
        ["SquadPage.jsx"],
    ),
    (
        "solvency_clock",
        "solvencyClock",
        "SolvencyClockPanel",
        ["BrainPage.jsx"],
    ),
    (
        "press",
        "press",
        "PressPanel",
        ["BrainPage.jsx"],
    ),
]


def _lee(ruta: Path) -> str:
    return ruta.read_text(encoding="utf-8")


# ============================================================
# 1. EL BACKEND LO ESCRIBE
# ============================================================


def test_el_backend_publica_los_bloques() -> None:
    fuente = _lee(ESTADO)

    for clave, _, _, _ in CADENAS:
        assert f'"{clave}":' in fuente, (
            f"`{clave}` no se publica en status.json"
        )


# ============================================================
# 2. EL NORMALIZADOR LO COPIA
# ============================================================


def test_el_normalizador_copia_los_bloques() -> None:
    """
    El salto que rompio `priorities`: llegaba en el JSON y este
    fichero no lo copiaba, asi que para la pantalla no existia.
    """

    fuente = _lee(NORMALIZADOR)

    for clave, nombre, _, _ in CADENAS:
        assert f"raw.{clave}" in fuente, (
            f"el normalizador no lee `raw.{clave}`: la pantalla no "
            f"puede verlo aunque el backend lo publique"
        )
        assert re.search(rf"\b{nombre}\s*:", fuente), (
            f"el normalizador no expone `{nombre}`"
        )


def test_lo_que_no_se_sabe_llega_diciendo_que_no_se_sabe() -> None:
    """
    Cada bloque cae a `available: false` si falta, para que la
    pantalla diga "no hay dato" en vez de desaparecer o pintar
    ceros. Un cero se lee como una medida.
    """

    fuente = _lee(NORMALIZADOR)

    for clave, _, _, _ in CADENAS:
        trozo = fuente[fuente.index(f"raw.{clave}"):]
        trozo = trozo[: trozo.index("\n\n") if "\n\n" in trozo else 200]

        assert "available: false" in trozo, (
            f"`{clave}` no tiene respaldo con `available: false`"
        )


# ============================================================
# 3. UN COMPONENTE LO LEE, Y UNA PAGINA LO MONTA
# ============================================================


def test_cada_bloque_tiene_componente_que_lo_lee() -> None:
    for _, nombre, componente, _ in CADENAS:

        if componente is None:
            continue

        ruta = DASHBOARD / "components" / f"{componente}.jsx"

        assert ruta.exists(), f"falta el componente {componente}"

        assert f"data.{nombre}" in _lee(ruta), (
            f"{componente} no lee `data.{nombre}`: seria un panel "
            f"que no enseña su propio dato"
        )


def test_cada_componente_esta_montado_en_su_pagina() -> None:
    """
    EL ULTIMO METRO.

    Un componente escrito y no montado es exactamente igual de
    invisible que un dato no calculado, y encima parece hecho.
    """

    for _, _, componente, paginas in CADENAS:

        if componente is None:
            continue

        for pagina in paginas:

            fuente = _lee(DASHBOARD / "pages" / pagina)

            assert f"import {componente}" in fuente, (
                f"{pagina} no importa {componente}"
            )
            assert f"<{componente}" in fuente, (
                f"{pagina} importa {componente} y no lo monta"
            )


def test_la_pagina_donde_se_monta_esta_viva() -> None:
    """
    EL ULTIMO METRO TIENE UN METRO MAS (12/09/2026)

        `AnalysisPage.jsx` existe, importa siete paneles y NO
        ESTA ENRUTADA en `App.jsx`. Es codigo muerto.

        El reloj de solvencia se monto ahi, la guardia de arriba
        se puso verde -la pagina importa el componente y lo
        monta- y el panel no salia por ninguna pantalla. Se
        descubrio mirando el bundle: la cadena "RELOJ DE
        SOLVENCIA" no aparecia en `dist/`.

        Comprobar que el componente esta en UNA pagina no basta.
        Hay que comprobar que esa pagina existe para la app.
    """

    app = _lee(DASHBOARD / "App.jsx")

    paginas_vivas = {
        f"{nombre}.jsx"
        for nombre in re.findall(r"from \"\./pages/(\w+)\"", app)
        if f"<{nombre}" in app
    }

    assert paginas_vivas, (
        "no se ha podido leer ninguna pagina enrutada en App.jsx"
    )

    for _, _, componente, paginas in CADENAS:

        for pagina in paginas:

            assert pagina in paginas_vivas, (
                f"{componente} se monta en {pagina}, que NO esta "
                f"enrutada en App.jsx: es codigo muerto y el panel "
                f"no lo ve nadie. Paginas vivas: "
                f"{sorted(paginas_vivas)}"
            )


def _componentes_alcanzables() -> set:
    """
    Los componentes a los que se llega desde `App.jsx`.

    Se sigue el grafo de imports de verdad, resolviendo la ruta
    relativa: `SquadTable` importa `./AbsenceCells` sin decir
    `components/`, y una version anterior de esta guardia lo daba
    por huerfano estando vivo.
    """

    componentes = DASHBOARD / "components"

    def importados(ruta: Path) -> set:
        nombres = set()

        for spec in re.findall(r'from "([^"]+)"', _lee(ruta)):

            if not spec.startswith("."):
                continue

            destino = (ruta.parent / spec).resolve()

            try:
                relativa = destino.relative_to(componentes.resolve())

            except ValueError:
                continue

            nombres.add(relativa.as_posix())

        return nombres

    app = _lee(DASHBOARD / "App.jsx")

    vivas = {
        nombre
        for nombre in re.findall(r'from "\./pages/(\w+)"', app)
        if f"<{nombre}" in app
    }

    alcanzables: set = set()
    vistos: set = set()

    frontera = [DASHBOARD / "App.jsx"] + [
        DASHBOARD / "pages" / f"{nombre}.jsx" for nombre in vivas
    ]

    while frontera:

        fichero = frontera.pop()

        if fichero in vistos or not fichero.exists():
            continue

        vistos.add(fichero)

        for nombre in importados(fichero):

            if nombre not in alcanzables:
                alcanzables.add(nombre)
                frontera.append(componentes / f"{nombre}.jsx")

    return alcanzables


def test_no_queda_ni_una_pagina_muerta() -> None:
    """
    EL CASO (05/09/2026)

        `AnalysisPage.jsx` importaba siete paneles y NO estaba
        enrutada en `App.jsx`. `NegotiationsPage.jsx` tampoco.
        Dos paginas enteras que el dueño no podia abrir.

        La noche del 12/09 casi se publica ahi el reloj de
        solvencia: la guardia de "esta montado en su pagina" se
        puso verde y el panel no salia por ninguna pantalla.
    """

    app = _lee(DASHBOARD / "App.jsx")

    vivas = {
        f"{nombre}.jsx"
        for nombre in re.findall(r'from "\./pages/(\w+)"', app)
        if f"<{nombre}" in app
    }

    todas = {
        ruta.name for ruta in (DASHBOARD / "pages").glob("*.jsx")
    }

    muertas = sorted(todas - vivas)

    assert not muertas, (
        f"paginas que no estan enrutadas en App.jsx y nadie puede "
        f"abrir: {muertas}. O se enrutan o se borran."
    )


def test_no_queda_ni_un_componente_huerfano() -> None:
    """
    Un panel que no se alcanza desde `App.jsx` es informacion que
    el dueño cree tener y no le llega. Y ademas envejece: los
    doce paneles que se borraron esta tarde seguian el sistema de
    diseño anterior (`ui/Card`) mientras el resto de la pantalla
    llevaba meses en otro.

    Si algun dia hace falta uno, esta en el historial de git. Lo
    que no puede quedarse es a medio camino.
    """

    todos = {
        ruta.stem for ruta in (DASHBOARD / "components").glob("*.jsx")
    }

    huerfanos = sorted(todos - _componentes_alcanzables())

    assert not huerfanos, (
        f"componentes que no se alcanzan desde App.jsx: "
        f"{huerfanos}. O se montan en una pagina viva o se "
        f"borran; a medias no."
    )


def test_los_paneles_nuevos_avisan_cuando_no_hay_dato() -> None:
    """
    Un panel que se esconde cuando falla es un panel que no se
    mira nunca. Todos tienen que tener rama de "no hay".
    """

    for _, _, componente, _ in CADENAS:

        if componente is None:
            continue

        fuente = _lee(DASHBOARD / "components" / f"{componente}.jsx")

        assert "available" in fuente, (
            f"{componente} no comprueba `available`"
        )
        assert 'className="empty"' in fuente, (
            f"{componente} no tiene rama de 'no hay dato': si falla, "
            f"desaparece sin decirlo"
        )


# ============================================================
# 4. EL TOPE POR OPERACION, QUE ERA EL CASO DE AYER
# ============================================================


def test_el_tope_por_operacion_se_ve() -> None:
    """
    Se arreglo el lector el 04/09 y seguia sin salir por ninguna
    pantalla: arreglado y invisible es medio arreglado.
    """

    fuente = _lee(DASHBOARD / "pages" / "MarketPage.jsx")

    assert "max_operation" in fuente, (
        "el tope por operacion no se pinta en ninguna parte"
    )


def test_ningun_panel_nuevo_decide_nada() -> None:
    """
    Los tres bloques de esta noche son FASE OBSERVADOR. La
    pantalla tiene que decirlo: si no, el dueño puede creer que
    Pepe ya ficha asi.
    """

    for componente, aviso in (
        ("RacePanel", "no</b> lo usa para decidir"),
        ("SeasonHorizonPanel", "el motor decide"),
        ("RosterExpansionPanel", "no</b> puede hacer esto hoy"),
        ("ScoutPanel", "Esto no manda todavía"),
        ("PressPanel", "NO DECIDE"),
    ):
        fuente = _lee(DASHBOARD / "components" / f"{componente}.jsx")

        assert aviso in fuente, (
            f"{componente} no avisa de que es un termometro: "
            f"falta «{aviso}»"
        )




def test_las_dos_opiniones_estan_pegadas_en_mercado() -> None:
    """
    Lo que hay que ver es la DIFERENCIA: Pepe le da el mismo
    0,17 % a uno que subio un 17 % ayer y a uno que bajo un 2 %.
    En columnas separadas por media tabla, nadie las compara.
    """

    fuente = _lee(DASHBOARD / "pages" / "MarketPage.jsx")

    assert "PEPE DICE" in fuente, "falta la columna de Pepe"
    assert "OJEADOR" in fuente, "falta la columna del ojeador"
    assert "target.scout" in fuente, (
        "la tabla no lee el veredicto del ojeador"
    )
    assert "pepe_yield_percent" in fuente, (
        "la tabla no lee lo que Pepe dice que rinde"
    )

    # Las cabeceras, contiguas. Se compara sobre el `<th>` y no
    # sobre la palabra suelta: "OJEADOR" tambien sale en los
    # comentarios del fichero, y ahi el indice no significa nada.
    cabecera_pepe = '<th className="n">PEPE DICE</th>'
    cabecera_ojeador = '<th className="n">OJEADOR</th>'

    assert cabecera_pepe in fuente and cabecera_ojeador in fuente

    hueco = fuente.index(cabecera_ojeador) - (
        fuente.index(cabecera_pepe) + len(cabecera_pepe)
    )

    assert 0 <= hueco < 40, (
        f'las dos columnas se han separado ({hueco} caracteres)'
    )


def test_sin_veredicto_no_se_pinta_un_cero() -> None:
    """
    "Sin dato" y "no se mueve" son cosas distintas. Confundirlas
    seria justo el fallo que este panel viene a arreglar.
    """

    fuente = _lee(DASHBOARD / "pages" / "MarketPage.jsx")

    assert "sin dato" in fuente, (
        "un candidato sin veredicto tiene que decir 'sin dato', no "
        "un 0 %"
    )


def test_el_ojeador_publica_a_quien_no_pudo_identificar() -> None:
    """
    Un emparejamiento que no se hizo y no se cuenta es un agujero
    invisible.
    """

    fuente = _lee(DASHBOARD / "components" / "ScoutPanel.jsx")

    assert "unmatched" in fuente, (
        "el panel no enseña los que se quedaron sin emparejar"
    )
    assert "fila.reason" in fuente, "ni el motivo de cada uno"




def test_la_divergencia_se_ve_en_mercado_y_no_como_recomendacion() -> None:
    """
    Es una HIPOTESIS. El estudio del 07/09 midio que el precio de
    Biwenger tiene un momento enorme, asi que una divergencia es
    una apuesta a que una rampa se gira — y esa apuesta no esta
    medida.
    """

    mercado = _lee(DASHBOARD / "pages" / "MarketPage.jsx")

    assert "DIVERGE" in mercado, "falta la columna de divergencia"
    assert "target.divergence" in mercado, (
        "la tabla no lee la divergencia de la fila"
    )

    panel = _lee(DASHBOARD / "components" / "ScoutPanel.jsx")

    assert "Hipótesis sin comprobar" in panel, (
        "el panel no avisa de que la divergencia no esta medida"
    )
    assert "scout.divergence" in panel, (
        "el panel no lee el estudio de la divergencia"
    )


def test_la_diferencia_contra_el_control_no_se_pinta_sin_muestra() -> None:
    """
    Que un divergente suba no dice nada si ese dia subieron
    todos. Pintar la diferencia antes de tener muestra seria
    presentar ruido como hallazgo.
    """

    panel = _lee(DASHBOARD / "components" / "ScoutPanel.jsx")

    assert "enough_sample" in panel, (
        "el panel pinta la diferencia sin mirar si hay muestra"
    )
    assert "sin muestra" in panel, (
        "y sin decirlo cuando no la hay"
    )




def test_se_ve_lo_que_decidia_antes_y_lo_que_decide_ahora() -> None:
    """
    Este es el primer cambio que mueve dinero de verdad. El dueño
    tiene que poder ver que cambia ANTES de que se gaste un euro,
    fila a fila y sin leer el codigo.
    """

    mercado = _lee(DASHBOARD / "pages" / "MarketPage.jsx")

    assert "ANTES / AHORA" in mercado, (
        "falta la columna de comparacion"
    )
    assert "target.market_gate" in mercado, (
        "la tabla no lee la compuerta"
    )
    assert "value_before" in mercado, (
        "no se pinta lo que se valoraba antes: sin eso no se ve el "
        "cambio"
    )


def test_el_motivo_del_freno_viaja_a_la_pantalla() -> None:
    """
    Un "no se compra" sin motivo no se puede discutir. Cada
    veto tiene que llegar con su razon.
    """

    mercado = _lee(DASHBOARD / "pages" / "MarketPage.jsx")

    for codigo in (
        "RITMO_OBSERVADO",
        "PRECIO_CAYENDO",
        "SIN_RITMO_OBSERVADO",
        "RACHA_SIN_DEMANDA",
    ):
        assert codigo in mercado, f"la pantalla no sabe pintar {codigo}"

    assert "gate_reason" in mercado, (
        "el motivo del veto no llega a la pantalla"
    )




def test_se_ve_que_via_gana_con_cada_esquema() -> None:
    """
    El encargo lo pide asi: el dueño tiene que poder mirar la
    lista y decir "esto si, esto no" antes de que se mueva un
    euro. Sin ver que via gana con cada uno, no se puede.
    """

    mercado = _lee(DASHBOARD / "pages" / "MarketPage.jsx")

    assert "CON SU CONFIANZA" in mercado, "falta la columna de la sombra"
    assert "target.confidence_shadow" in mercado, (
        "la tabla no lee la valoracion con confianzas por via"
    )
    assert "gate?.route_now" in mercado or "gate.route_now" in mercado, (
        "no se compara con la via que gana HOY"
    )
    assert "CAMBIA" in mercado, (
        "no se marca cuando el candidato cambia de via, que es lo "
        "que hay que mirar primero"
    )


def test_las_tres_vias_se_pintan_con_nombre() -> None:
    mercado = _lee(DASHBOARD / "pages" / "MarketPage.jsx")

    for via in ("PRICE_TREND", "COMPUTER_RESALE", "XI_UPGRADE"):
        assert via in mercado, f"la pantalla no sabe pintar {via}"


def test_la_sombra_dice_que_no_manda() -> None:
    mercado = _lee(DASHBOARD / "pages" / "MarketPage.jsx")

    assert "NO MANDA" in mercado, (
        "la columna nueva no avisa de que es una segunda opinion"
    )


def test_el_bolsillo_se_ve_en_mercado() -> None:
    """
    SINTOMA

        Los 22 candidatos salian SPECULATION y se median contra
        los 3,5 M de especular mientras los 8,5 M de fichar
        seguian intactos. Cinco se rechazaron por "supera
        presupuesto" teniendo el dinero al lado.

    La columna INTENCION enseña la etiqueta, pero no de donde
    sale. Si el dueño no ve que clase de operacion es, no puede
    saber si el bolsillo elegido es el correcto.
    """

    mercado = _lee(DASHBOARD / "pages" / "MarketPage.jsx")

    assert "BOLSILLO" in mercado, "falta la columna del bolsillo"
    assert "target.deployment" in mercado, (
        "la tabla no lee la clase de operacion"
    )
    assert "target.concentration" in mercado, (
        "la tabla no lee el tope de concentracion de la fila"
    )

    for palabra in ("FICHAR", "COMERCIAR", "HUECO"):
        assert palabra in mercado, (
            f"la columna del bolsillo no sabe pintar «{palabra}»"
        )

    assert "roster_fill_value" in mercado, (
        "no se puede ver cuanto valdria llenando una ficha vacia"
    )


def test_el_interruptor_se_ve_apagado_en_pantalla() -> None:
    """
    Un bloque en sombra que no dice que esta en sombra se lee
    como una decision tomada. El interruptor de esta noche tiene
    que verse desde la propia tabla.
    """

    mercado = _lee(DASHBOARD / "pages" / "MarketPage.jsx")

    assert "observer_only" in mercado, (
        "la pantalla no mira si el despliegue esta en sombra"
    )
    assert "en sombra" in mercado, (
        "no se avisa en la fila de que el bolsillo aun no manda"
    )


def test_la_concentracion_avisa_y_dice_el_motivo() -> None:
    """
    Como el resto de guardarrailes de la casa: avisa y acota, no
    prohibe en silencio. Un tope que recorta sin decir por que es
    el mismo problema que este repo lleva una semana arreglando.
    """

    panel = _lee(DASHBOARD / "components" / "ConcentrationPanel.jsx")

    assert "b.reason" in panel or "breach.reason" in panel, (
        "el panel no pinta el motivo de cada aviso"
    )
    assert "limit_player_share" in panel, "no se ve el tope por jugador"
    assert "limit_same_team" in panel, "no se ve el tope por club"
    assert "avisa" in panel and "acota" in panel, (
        "el panel no dice que avisa y acota en vez de prohibir"
    )


def test_el_orden_de_venta_se_ve_entero() -> None:
    """
    SINTOMA

        En la foto del 05/09 a las 14:03 el saldo esta en
        -421.792, la prioridad declarada es "recuperar solvencia"
        y hay doce ofertas sobre la mesa. El dueño no puede ver en
        ninguna pantalla a quien le tocaria salir.

    Tiene que verse la cola ENTERA: los que estan, los que no se
    proponen y los que aparta el suelo de su posicion. Media cola
    es peor que ninguna, porque parece completa.
    """

    panel = _lee(DASHBOARD / "components" / "SaleOrderPanel.jsx")

    assert "orden.queue" in panel, "no se pinta la cola"
    assert "orden.excluded" in panel, (
        "no se ve quien NO se propone: un apartado en silencio es "
        "el problema que este repo lleva una semana arreglando"
    )
    assert "orden.blocked" in panel, (
        "no se ve a quien aparta el suelo de su posicion"
    )

    assert "fila.reason" in panel, "las filas no llevan su motivo"

    assert "cash_one_cycle" in panel and "cash_on_the_table" in panel, (
        "no se distingue la caja de este ciclo de la que hay sobre "
        "la mesa"
    )

    assert "NO VENDE" in panel, (
        "la cola no avisa de que Pepe no la ejecuta"
    )


def test_el_desempate_se_ve_con_su_motivo() -> None:
    """
    El encargo lo pide con estas palabras: "que el motivo del
    desempate se vea en pantalla — se vende a Cepeda pese al HOLD
    porque quedan 5 h y el saldo es -421.792".

    Un desempate sin motivo es una venta que aparece de la nada.
    """

    panel = _lee(DASHBOARD / "components" / "SolvencyClockPanel.jsx")

    assert "override_reason" in panel, (
        "no se pinta el motivo del desempate"
    )
    assert "solvency_overrides_hold" in panel, (
        "no se ve quien manda: la solvencia o el motor de ofertas"
    )
    assert "SOLVENCIA" in panel and "MOTOR DE OFERTAS" in panel, (
        "no se distingue en pantalla cual de los dos gana"
    )

    assert "recommended_sale" in panel, (
        "no se ve con que venta se taparia el agujero"
    )

    for campo in (
        "hours_to_solvency_deadline",
        "hours_to_deadline",
        "covered_at_deadline",
    ):
        assert campo in panel, (
            f"el reloj no enseña `{campo}`: sin eso no se puede "
            f"saber si llega a tiempo"
        )

    assert "reason_text" in panel, "el reloj no dice que va a hacer"


def test_la_prensa_enseña_la_cita_y_separa_dato_de_deduccion() -> None:
    """
    "La cita literal siempre. Si mañana la señal falla, hay que
    poder ver quien lo dijo y con que palabras."

    Y la otra mitad: el titular es dato, la clase es deduccion, y
    en pantalla tienen que verse como cosas distintas.
    """

    panel = _lee(DASHBOARD / "components" / "PressPanel.jsx")

    assert "item.quote" in panel, "no se pinta la cita literal"
    assert "item.url" in panel, "la cita no lleva su enlace"
    assert "item.source" in panel, "no se ve que medio lo publico"

    assert "dato" in panel and "deducción" in panel.lower(), (
        "la pantalla no separa lo que publico el medio de lo que "
        "deduce el bot"
    )

    assert "press.sources" in panel, (
        "no se ven los canales, asi que una fuente apagada no se "
        "distingue de una olvidada"
    )
    assert "NO ENTRA" in panel, (
        "un canal apagado a proposito no se dice en pantalla"
    )


TESTS = [
    test_el_backend_publica_los_bloques,
    test_el_normalizador_copia_los_bloques,
    test_lo_que_no_se_sabe_llega_diciendo_que_no_se_sabe,
    test_cada_bloque_tiene_componente_que_lo_lee,
    test_cada_componente_esta_montado_en_su_pagina,
    test_la_pagina_donde_se_monta_esta_viva,
    test_no_queda_ni_una_pagina_muerta,
    test_no_queda_ni_un_componente_huerfano,
    test_los_paneles_nuevos_avisan_cuando_no_hay_dato,
    test_el_tope_por_operacion_se_ve,
    test_las_dos_opiniones_estan_pegadas_en_mercado,
    test_sin_veredicto_no_se_pinta_un_cero,
    test_el_ojeador_publica_a_quien_no_pudo_identificar,
    test_la_divergencia_se_ve_en_mercado_y_no_como_recomendacion,
    test_la_diferencia_contra_el_control_no_se_pinta_sin_muestra,
    test_se_ve_lo_que_decidia_antes_y_lo_que_decide_ahora,
    test_el_motivo_del_freno_viaja_a_la_pantalla,
    test_se_ve_que_via_gana_con_cada_esquema,
    test_las_tres_vias_se_pintan_con_nombre,
    test_la_sombra_dice_que_no_manda,
    test_el_bolsillo_se_ve_en_mercado,
    test_el_interruptor_se_ve_apagado_en_pantalla,
    test_la_concentracion_avisa_y_dice_el_motivo,
    test_el_orden_de_venta_se_ve_entero,
    test_el_desempate_se_ve_con_su_motivo,
    test_la_prensa_enseña_la_cita_y_separa_dato_de_deduccion,
    test_ningun_panel_nuevo_decide_nada,
]


def main() -> None:
    fallos = 0
    for test in TESTS:
        try:
            test()
            print(f"OK   {test.__name__}")
        except AssertionError as exc:
            fallos += 1
            print(f"FALLA {test.__name__}: {exc}")

    print("=" * 60)
    print(f"LA PANTALLA LEE LO PUBLICADO V1: {len(TESTS) - fallos}/{len(TESTS)} OK")
    print("=" * 60)

    if fallos:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
