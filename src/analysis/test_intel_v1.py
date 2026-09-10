"""
Archivar hoy, y contar la pelea como lo que cuesta.

SINTOMA (09/09/2026)

    Al intentar cruzar las 156 subastas del tablon con las
    recomendaciones de las webs no se pudo: el libro del ojeador
    guardaba OCHO predicciones, todas del mismo dia. Las subastas
    iban del 10/08 al 06/09.

    No es que el analisis fuera dificil: el dato no existia. Se
    sobrescribia cada vuelta.

CAUSA

    Nadie guardaba la salida diaria. Un precio se recupera de
    Biwenger meses despues; un titular de prensa, no.

Y LA SEGUNDA MITAD

    Medido sobre esas 156 subastas: el jugador que subia mas de
    un 1 % el dia antes acaba disputado mucho mas a menudo que
    el que no, y el caro mucho menos que el barato.

                       CAE O PLANO    SUBE >= 1 %
        barato < 1,5 M     54 %           83 %
        medio 1,5-3 M      39 %           64 %
        caro >= 3 M        22 %           67 %

    Gastar una ficha en alguien que se perdera el 83 % de las
    veces es tirar capacidad, y la capacidad es lo escaso.

LO QUE SE PROTEGE AQUI

    1. Que archivar sea idempotente: una vez al dia, no 24.
    2. Que archivar NO pise lo que ya hay: un archivo
       sobrescrito es peor que no tenerlo.
    3. Que la poda no se lleve lo que no entiende.
    4. Que la probabilidad de llevarselo salga de la tabla
       medida, y que sin celda NO se invente un 1.
    5. Que contar la pelea cambie el orden, y que este APAGADO.
    6. Que el libro de la prensa tenga la misma forma vacio que
       lleno.

    Fixture entero: archivos temporales, dias inyectados. Ni
    disco de produccion, ni red, ni reloj.
"""

from __future__ import annotations

import json
import tempfile

from datetime import date, timedelta
from pathlib import Path

from src.analysis.la_subasta import (
    MUESTRA_QUE_MANDA,
    PELEA_MEDIDA,
    candidatos_en_modo_cartera,
    elegir_la_cesta,
    probabilidad_de_llevarselo,
    probabilidad_de_pelea,
)

from src.intelligence.archivo_diario import (
    archivar,
    dias_archivados,
    podar,
)

from src.intelligence.libro_de_la_prensa import (
    HORIZONTES,
    libro,
)


# ============================================================
# UN ARCHIVO DE MENTIRA
# ============================================================


HOY = date(2026, 9, 9)


class _archivo:
    """Un directorio temporal con dos ficheros de origen."""

    def __enter__(self):
        self.tmp = tempfile.TemporaryDirectory(
            prefix="bordalas_archivo_"
        )

        raiz = Path(self.tmp.name)

        self.destino = raiz / "archivo"

        self.origenes = {}

        for nombre, contenido in (
            (
                "scout",
                {
                    # LA FECHA VA DENTRO (09/09/2026). Sin ella
                    # no se archiva: ver `dia_del_informe`.
                    "generated_at": f"{HOY.isoformat()}T09:00:00",
                    "players": {"1": {"x": 1}},
                },
            ),
            (
                "press",
                {
                    "generated_at": f"{HOY.isoformat()}T16:00:00",
                    "players": {
                        "100": {
                            "player_name": "Uno",
                            "items": [
                                {"kind": "BAJA"},
                                {"kind": "BAJA"},
                                {"kind": "MENCION"},
                            ],
                        }
                    },
                },
            ),
        ):
            ruta = raiz / f"{nombre}_origen.json"

            ruta.write_text(
                json.dumps(contenido), encoding="utf-8"
            )

            self.origenes[nombre] = ruta

        return self

    def fechar(self, nombre, cuando):
        """Cambia el `generated_at` de un origen del fixture."""

        ruta = self.origenes[nombre]

        datos = json.loads(ruta.read_text(encoding="utf-8"))

        if cuando is None:
            datos.pop("generated_at", None)

        else:
            datos["generated_at"] = (
                f"{cuando.isoformat()}T12:00:00"
            )

        ruta.write_text(
            json.dumps(datos), encoding="utf-8"
        )

    def __exit__(self, *_):
        self.tmp.cleanup()
        return False


# ============================================================
# ARCHIVAR
# ============================================================


def test_se_archiva_una_vez_al_dia_y_no_veinticuatro():
    """
    El ciclo pasa por aqui cada vuelta. La primera del dia
    escribe; las demas ven que ya esta.
    """

    with _archivo() as a:

        primera = archivar(
            HOY, directorio=a.destino, fuentes=a.origenes
        )

        assert primera["available"], primera["reason"]

        assert sorted(primera["written"]) == [
            "press",
            "scout",
        ], primera

        segunda = archivar(
            HOY, directorio=a.destino, fuentes=a.origenes
        )

        assert not segunda["written"], (
            "la segunda vuelta del dia vuelve a escribir"
        )

        assert sorted(segunda["already"]) == [
            "press",
            "scout",
        ]


def test_archivar_nunca_pisa_lo_que_ya_hay():
    """
    LA MITAD QUE IMPORTA.

    Un archivo sobrescrito es peor que no tenerlo: parece que
    hay historico y es la foto de hoy repetida.
    """

    with _archivo() as a:

        archivar(HOY, directorio=a.destino, fuentes=a.origenes)

        guardado = (
            a.destino / HOY.isoformat() / "scout.json"
        )

        original = guardado.read_text(encoding="utf-8")

        # Cambia el origen y se vuelve a archivar el MISMO dia.
        a.origenes["scout"].write_text(
            json.dumps({"players": {"9": {"otra": "cosa"}}}),
            encoding="utf-8",
        )

        archivar(HOY, directorio=a.destino, fuentes=a.origenes)

        assert guardado.read_text(encoding="utf-8") == original, (
            "el archivo del dia se ha sobrescrito"
        )


def test_se_guarda_el_informe_entero_y_no_un_resumen():
    """
    Lo que hoy parece irrelevante es lo que mañana hara falta.
    El mes pasado nadie sabia que ibamos a querer cruzar
    titulares con subastas.
    """

    with _archivo() as a:

        archivar(HOY, directorio=a.destino, fuentes=a.origenes)

        guardado = json.loads(
            (a.destino / HOY.isoformat() / "press.json")
            .read_text(encoding="utf-8")
        )

        original = json.loads(
            a.origenes["press"].read_text(encoding="utf-8")
        )

        assert guardado == original, (
            "lo archivado no es identico al informe del ciclo"
        )


def test_sin_origen_se_dice_en_vez_de_fallar():
    """
    Si el ojeador no ha corrido hoy, no hay nada que copiar. Eso
    no es un error: es un dia sin informe, y hay que poder
    distinguirlo de un dia sin archivar.
    """

    with _archivo() as a:

        salida = archivar(
            HOY,
            directorio=a.destino,
            fuentes={"scout": Path("no-existe.json")},
        )

        assert salida["available"]
        assert salida["missing"] == ["scout"]
        assert not salida["written"]


def test_la_carpeta_lleva_la_fecha_DEL_INFORME():
    """
    LA SEXTA DE LA FAMILIA, CAZADA ANTES DE DECIDIR CON ELLA.

    La primera version estampaba el dia en que se archivaba. El
    09/09 guardo bajo `2026-09-09` un informe cuyo
    `generated_at` era del 05/09.

    El libro de la prensa fecha los avisos por la carpeta, asi
    que habria concluido que la noticia NO movio el precio
    —cuando lo movio cuatro dias antes, y el libro miraba desde
    el dia equivocado—.
    """

    with _archivo() as a:

        anteayer = HOY - timedelta(days=1)

        a.fechar("press", anteayer)

        archivar(HOY, directorio=a.destino, fuentes=a.origenes)

        assert (
            a.destino / anteayer.isoformat() / "press.json"
        ).exists(), (
            "el informe de ayer no se ha archivado bajo su "
            "propia fecha"
        )

        assert not (
            a.destino / HOY.isoformat() / "press.json"
        ).exists(), (
            "el informe de ayer se ha archivado como si fuera "
            "de hoy"
        )

        # Y el de hoy si va en hoy.
        assert (
            a.destino / HOY.isoformat() / "scout.json"
        ).exists()


def test_lo_caducado_se_queda_fuera_y_se_dice():
    """
    Un informe de hace cuatro dias no representa el mercado de
    hoy. Y callarse que su fuente lleva cuatro dias parada es
    peor que no archivarlo: nadie se entera de que esta muerta.
    """

    with _archivo() as a:

        viejo = HOY - timedelta(days=4)

        a.fechar("press", viejo)

        salida = archivar(
            HOY, directorio=a.destino, fuentes=a.origenes
        )

        assert salida["available"]

        assert "press" not in salida["written"]

        assert any(
            "press" in x for x in salida["stale"]
        ), salida

        assert not (
            a.destino / viejo.isoformat()
        ).exists(), (
            "lo caducado se ha archivado igual"
        )

        assert "CADUCADOS" in salida["reason"], (
            "el motivo no avisa de que hay una fuente parada"
        )


def test_un_informe_sin_fecha_no_se_archiva():
    """
    Sin `generated_at` no se puede saber a que dia pertenece.
    Meterlo en la carpeta de hoy seria exactamente el fallo que
    se acaba de arreglar.
    """

    with _archivo() as a:

        a.fechar("scout", None)

        salida = archivar(
            HOY, directorio=a.destino, fuentes=a.origenes
        )

        assert salida["undated"] == ["scout"], salida

        assert "scout" not in salida["written"]


def test_la_fecha_se_lee_del_informe_y_no_del_nombre():
    """
    `dia_del_informe` sobre basura no lanza ni inventa un dia.
    """

    from src.intelligence.archivo_diario import dia_del_informe

    for ruta in (None, "no-existe.json", 12345):

        salida = dia_del_informe(ruta)

        assert isinstance(salida, dict)
        assert salida["dia"] is None
        assert salida["reason"]


def test_la_poda_no_se_lleva_lo_que_no_entiende():
    """
    Perder archivo es el fallo que este modulo existe para
    evitar. Ante la duda, no se borra.
    """

    with _archivo() as a:

        viejo = HOY - timedelta(days=90)

        # La carpeta vieja se monta a mano, no con `archivar`:
        # un informe de hace 90 dias lo rechaza la regla de
        # caducidad, y la poda opera sobre lo que HAY en disco,
        # venga de donde venga.
        antigua = a.destino / viejo.isoformat()
        antigua.mkdir(parents=True, exist_ok=True)
        (antigua / "press.json").write_text("{}", encoding="utf-8")

        archivar(HOY, directorio=a.destino, fuentes=a.origenes)

        (a.destino / "carpeta-rara").mkdir(
            parents=True, exist_ok=True
        )

        resultado = podar(HOY, directorio=a.destino)

        assert resultado["removed"] == [viejo.isoformat()], (
            resultado
        )

        assert (a.destino / "carpeta-rara").exists(), (
            "la poda ha borrado una carpeta que no entendia"
        )

        assert (a.destino / HOY.isoformat()).exists()


def test_se_ve_cuantos_dias_hay():
    """
    Para que el archivo no vuelva a estar vacio sin que nadie se
    entere.
    """

    with _archivo() as a:

        vacio = dias_archivados(directorio=a.destino)

        assert vacio["available"]
        assert vacio["days"] == 0
        assert vacio["reason"]

        archivar(HOY, directorio=a.destino, fuentes=a.origenes)

        lleno = dias_archivados(directorio=a.destino)

        assert lleno["days"] == 1
        assert lleno["oldest"] == HOY.isoformat()
        assert set(vacio) == set(lleno), "cambia de forma"


# ============================================================
# LA PELEA COMO COSTE
# ============================================================


def test_la_tabla_de_la_pelea_no_esta_vacia():
    """
    REGLA DE LA CASA: ninguna guardia pasa con las manos vacias.
    Si alguien vacia la tabla, las pruebas de abajo pasarian sin
    comprobar nada.
    """

    assert PELEA_MEDIDA, "la tabla de la pelea esta vacia"

    assert len(PELEA_MEDIDA) == 6, (
        f"la tabla tiene {len(PELEA_MEDIDA)} celdas y eran 6 "
        f"(tres tramos de precio x sube/no sube)"
    )

    for _, _, _, probabilidad, n in PELEA_MEDIDA:
        assert 0 < probabilidad < 1
        assert n > 0


def test_el_que_sube_atrae_mas_pelea_en_todos_los_precios():
    """
    LA IRONIA, MEDIDA.

    La señal que nos hace fijarnos es la misma que hace que se
    fijen los demas. Y pasa en los tres tramos de precio, no
    solo en uno.
    """

    for precio in (300_000, 2_000_000, 4_500_000):

        plano = probabilidad_de_pelea(precio, 0.0)
        subiendo = probabilidad_de_pelea(precio, 2.0)

        assert subiendo["probabilidad"] > plano["probabilidad"], (
            f"a {precio} subir no atrae mas pelea: "
            f"{subiendo['probabilidad']} contra "
            f"{plano['probabilidad']}"
        )


def test_el_caro_se_pelea_menos_que_el_barato():
    """
    Contraintuitivo y medido: pocos managers pueden pagar seis
    millones, asi que arriba hay menos gente.
    """

    barato = probabilidad_de_pelea(300_000, 0.0)
    caro = probabilidad_de_pelea(4_500_000, 0.0)

    assert caro["probabilidad"] < barato["probabilidad"], (
        f"el caro se pelea {caro['probabilidad']} y el barato "
        f"{barato['probabilidad']}"
    )


def test_sin_celda_medida_no_se_inventa_un_uno():
    """
    Dar por hecho que se gana lo que no se ha medido es
    exactamente como se fabrica una ventaja que no existe.
    """

    for precio in (None, 0, -5, "x"):

        salida = probabilidad_de_llevarselo(precio)

        assert salida["probabilidad"] is None, salida

        assert salida["reason"]


def test_la_muestra_corta_se_marca():
    """
    Un 67 % de seis casos no es un 67 %. Se publica, pero se
    dice.
    """

    corta = probabilidad_de_pelea(4_500_000, 2.0)

    assert corta["n"] < MUESTRA_QUE_MANDA
    assert corta["fiable"] is False
    assert "muestra corta" in corta["reason"]

    larga = probabilidad_de_pelea(4_500_000, 0.0)

    assert larga["fiable"] is True


# ============================================================
# LAS DOS CESTAS, MEDIDAS SOBRE EL ESCAPARATE REAL
# ============================================================
#
#     Del 09/09/2026, sobre los 20 objetivos publicados y con
#     siete fichas libres. Es lo que justifica encender el orden
#     que cuenta la pelea, guardado aqui para que la decision no
#     pueda alejarse de su motivo.
#
#     `(pujas, compromete, si_gana_todas, esperado, por_ficha)`
CESTA_SIN_LA_PELEA = (7, 1_964_907, 30_373, 13_972, 1_996)

CESTA_CON_LA_PELEA = (4, 2_375_929, 36_731, 20_918, 5_230)


def test_contar_la_pelea_gana_en_las_dos_dimensiones():
    """
    LA GUARDIA QUE JUSTIFICA EL CAMBIO.

    No basta con que la cesta que cuenta la pelea rinda mas: si
    para eso ocupara MAS fichas, habria un intercambio que
    discutir. No lo hay — rinde mas con menos.

    Si alguien rehace las cestas y deja de ser cierto, esto se
    pone rojo y hay que volver a decidir, no seguir por
    inercia.
    """

    pujas_sin, _, _, esperado_sin, ficha_sin = (
        CESTA_SIN_LA_PELEA
    )

    pujas_con, _, _, esperado_con, ficha_con = (
        CESTA_CON_LA_PELEA
    )

    assert esperado_con > esperado_sin, (
        "contar la pelea rinde menos: "
        + str(esperado_con)
        + " contra "
        + str(esperado_sin)
    )

    assert pujas_con < pujas_sin, (
        "contar la pelea ocupa mas fichas y habria que decidir "
        "si compensa"
    )

    assert ficha_con > ficha_sin, (
        "por ficha ocupada no es mejor: "
        + str(ficha_con)
        + " contra "
        + str(ficha_sin)
    )

    # Y que la mejora sea grande, no ruido: si algun dia cae al
    # 5 %, esto deja de valer la pena y conviene enterarse.
    assert esperado_con >= 1.4 * esperado_sin, (
        "la mejora ha bajado al "
        + f"{100 * (esperado_con / esperado_sin - 1):.0f} %"
    )


def test_el_esperado_no_es_lo_que_se_gana_si_todo_sale_bien():
    """
    La trampa de la que salio este numero.

    "Si ganara todas" son 30.373 y 36.731: parecidos. El numero
    que decide es el ESPERADO —multiplicado por la probabilidad
    de llevarselo—, y ahi la diferencia es del 50 %.

    Medir la cesta por lo que daria ganandolo todo es contar
    billetes que no se han cobrado.
    """

    _, _, todas_sin, esperado_sin, _ = CESTA_SIN_LA_PELEA
    _, _, todas_con, esperado_con, _ = CESTA_CON_LA_PELEA

    assert esperado_sin < todas_sin
    assert esperado_con < todas_con

    ganando_todo = todas_con / todas_sin
    de_verdad = esperado_con / esperado_sin

    assert de_verdad > ganando_todo, (
        "mirando solo 'si gana todas' las dos cestas se parecen "
        f"({ganando_todo:.2f}x) y de verdad no "
        f"({de_verdad:.2f}x): el esperado es el que decide"
    )


def test_contar_la_pelea_cambia_el_orden():
    """
    El caro y plano se lleva el 78 %; el barato y plano, el
    46 %. Con la misma ganancia por euro, el primero rinde mas.
    """

    candidatos = candidatos_en_modo_cartera(
        [
            {
                "id": 1,
                "name": "Barato",
                "market_price": 300_000,
                "rate_percent_per_day": 0.0,
            },
            {
                "id": 2,
                "name": "Caro",
                "market_price": 4_500_000,
                "rate_percent_per_day": 0.0,
            },
        ],
        prima_de_reventa=0.018,
    )

    sin = elegir_la_cesta(
        candidatos,
        presupuesto=9_000_000,
        fichas_libres=1,
        caja_libre=9_000_000,
        contar_la_pelea=False,
    )

    con = elegir_la_cesta(
        candidatos,
        presupuesto=9_000_000,
        fichas_libres=1,
        caja_libre=9_000_000,
    )

    assert sin["elegidos"][0]["name"] == "Barato", (
        "apagando la pelea deberia ganar el que menos capacidad "
        "consume"
    )

    assert con["elegidos"][0]["name"] == "Caro", (
        "contando la pelea deberia ganar el que se lleva mas "
        "veces, y salio "
        + con["elegidos"][0]["name"]
    )


def test_la_pelea_esta_encendida_y_se_puede_apagar():
    """
    ENCENDIDA el 09/09/2026 con los numeros de arriba.

    Y se puede apagar en una linea, como todo en esta casa: el
    dia que la tabla de la pelea envejezca, `contar_la_pelea=
    False` devuelve el orden de antes sin tocar nada mas.
    """

    import inspect

    firma = inspect.signature(elegir_la_cesta)

    assert (
        firma.parameters["contar_la_pelea"].default is True
    ), "la pelea ya no entra en el reparto por defecto"


def test_la_probabilidad_se_publica_aunque_no_se_use():
    """
    Publicarla siempre es lo que permite comparar los dos
    ordenes sin recalcular nada.
    """

    cesta = elegir_la_cesta(
        candidatos_en_modo_cartera(
            [
                {
                    "id": 1,
                    "name": "Uno",
                    "market_price": 300_000,
                    "rate_percent_per_day": 0.0,
                }
            ],
            prima_de_reventa=0.018,
        ),
        presupuesto=9_000_000,
        fichas_libres=2,
        caja_libre=9_000_000,
    )

    elegido = cesta["elegidos"][0]

    for clave in (
        "win_odds",
        "win_odds_cell",
        "win_odds_n",
        "win_odds_reason",
    ):
        assert clave in elegido, f"falta «{clave}»"

    assert elegido["win_odds"] is not None


# ============================================================
# EL LIBRO DE LA PRENSA
# ============================================================


def test_el_libro_tiene_la_misma_forma_vacio_que_lleno():
    """
    El dia uno sale vacio y se publica igual: la pantalla se
    construye hoy, no cuando haya muestra.
    """

    with _archivo() as a:

        vacio = libro(
            directorio=a.destino, almacen={}, hoy=HOY
        )

        archivar(HOY, directorio=a.destino, fuentes=a.origenes)

        lleno = libro(
            directorio=a.destino, almacen={}, hoy=HOY
        )

        assert set(vacio) == set(lleno), (
            set(vacio) ^ set(lleno)
        )

        assert vacio["available"]
        assert vacio["days_archived"] == 0
        assert lleno["days_archived"] == 1


def test_una_noticia_repetida_por_tres_medios_cuenta_una():
    """
    Si tres periodicos dicen lo mismo sigue siendo una noticia.
    Contarla tres veces inflaria la muestra sin añadir
    informacion — y el libro entero se apoya en el tamaño de la
    muestra.
    """

    with _archivo() as a:

        archivar(HOY, directorio=a.destino, fuentes=a.origenes)

        resultado = libro(
            directorio=a.destino, almacen={}, hoy=HOY
        )

        # El fixture tiene DOS items BAJA y uno MENCION del
        # mismo jugador: dos avisos, no tres.
        assert resultado["notices"] == 2, (
            f"{resultado['notices']} avisos y el fixture tiene "
            f"dos clases distintas para un jugador"
        )

        assert resultado["by_kind"]["BAJA"]["notices"] == 1


def test_el_libro_dice_por_que_no_puede_medir_todavia():
    """
    "Vacio" no es una respuesta. Tiene que decir QUE falta: un
    dia archivado no permite medir ni el horizonte de uno.
    """

    with _archivo() as a:

        archivar(HOY, directorio=a.destino, fuentes=a.origenes)

        resultado = libro(
            directorio=a.destino, almacen={}, hoy=HOY
        )

        assert resultado["measurable"] == 0

        assert str(min(HORIZONTES)) in resultado["reason"], (
            "el motivo no dice cuantos dias hacen falta"
        )


def test_el_libro_nunca_lanza():

    for directorio in (None, "no-existe", Path("tampoco")):

        resultado = libro(
            directorio=directorio, almacen={}, hoy=HOY
        )

        assert isinstance(resultado, dict)
        assert "by_kind" in resultado


def test_estas_guardias_no_leen_el_estado():
    """REGLA 23. Ni disco de produccion, ni red, ni reloj."""

    import ast

    from src.analysis.test_verja_determinista_v1 import (
        _docstrings,
    )

    fuente = Path(__file__).read_text(encoding="utf-8")

    arbol = ast.parse(fuente)

    fuera = _docstrings(arbol)

    prohibido = "dat" + "a/"

    encontrados = 0

    for nodo in ast.walk(arbol):

        if id(nodo) in fuera:
            continue

        if isinstance(nodo, ast.Constant) and isinstance(
            nodo.value, str
        ):
            encontrados += 1
            assert prohibido not in nodo.value, nodo.value

    # NINGUNA GUARDIA PASA CON LAS MANOS VACIAS: si el escaneo
    # no ha mirado ni una cadena, no ha comprobado nada.
    assert encontrados > 20, (
        f"solo se han mirado {encontrados} cadenas: el escaneo "
        f"no esta recorriendo el fichero"
    )


TESTS = [
    test_se_archiva_una_vez_al_dia_y_no_veinticuatro,
    test_archivar_nunca_pisa_lo_que_ya_hay,
    test_se_guarda_el_informe_entero_y_no_un_resumen,
    test_sin_origen_se_dice_en_vez_de_fallar,
    test_la_carpeta_lleva_la_fecha_DEL_INFORME,
    test_lo_caducado_se_queda_fuera_y_se_dice,
    test_un_informe_sin_fecha_no_se_archiva,
    test_la_fecha_se_lee_del_informe_y_no_del_nombre,
    test_la_poda_no_se_lleva_lo_que_no_entiende,
    test_se_ve_cuantos_dias_hay,
    test_la_tabla_de_la_pelea_no_esta_vacia,
    test_el_que_sube_atrae_mas_pelea_en_todos_los_precios,
    test_el_caro_se_pelea_menos_que_el_barato,
    test_sin_celda_medida_no_se_inventa_un_uno,
    test_la_muestra_corta_se_marca,
    test_contar_la_pelea_gana_en_las_dos_dimensiones,
    test_el_esperado_no_es_lo_que_se_gana_si_todo_sale_bien,
    test_contar_la_pelea_cambia_el_orden,
    test_la_pelea_esta_encendida_y_se_puede_apagar,
    test_la_probabilidad_se_publica_aunque_no_se_use,
    test_el_libro_tiene_la_misma_forma_vacio_que_lleno,
    test_una_noticia_repetida_por_tres_medios_cuenta_una,
    test_el_libro_dice_por_que_no_puede_medir_todavia,
    test_el_libro_nunca_lanza,
    test_estas_guardias_no_leen_el_estado,
]


def main() -> None:

    print()
    print("=" * 60)
    print("INTEL V1")
    print("=" * 60)

    fallos = 0

    for prueba in TESTS:

        try:
            prueba()
            print(f"  OK    {prueba.__name__}")

        except AssertionError as error:
            fallos += 1
            print(f"  FALLA {prueba.__name__}")
            print(f"        {error}")

        except Exception as error:                  # noqa: BLE001
            fallos += 1
            print(f"  ROMPE {prueba.__name__}")
            print(f"        {type(error).__name__}: {error}")

    print("=" * 60)

    if fallos:
        print(f"{fallos} de {len(TESTS)} en rojo.")
        raise SystemExit(1)

    print(f"Los {len(TESTS)} en verde.")


if __name__ == "__main__":
    main()
