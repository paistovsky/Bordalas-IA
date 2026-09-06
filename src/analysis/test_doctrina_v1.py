"""
LA DOCTRINA V1 - que Pepe cite la regla, y que se vea la que no.

SINTOMA

    Dieciocho reglas escritas por el dueño en `docs/DOCTRINA.md`,
    y ninguna forma de saber si Pepe las sigue. La regla 17 lo
    dice:

        "Una decision sin cita es una decision que nadie ha
         escrito, y esas son las que hay que descubrir."

CAUSA

    Pepe publica el motivo de cada decision en prosa, pero nadie
    habia cruzado esos motivos con el documento. Con 45 decisiones
    por ciclo, a ojo no se hace.

CONSECUENCIA

    Cuatro decisiones al dia salen de reglas que no existen. La
    mas gorda: `MONITOR_OFFERS`, gestionar las ofertas que
    ENTRAN, que es lo que mas veces hace el ciclo y no aparece en
    ninguna de las dieciocho.

LO QUE VIGILAN ESTAS PRUEBAS

    Que la cita no se invente, que la lista de huerfanas exista y
    tenga motivo escrito, que los ascendidos se deduzcan del dato
    y no de la memoria, que el embudo señale la causa MAYOR y no
    la primera, y que el activo grande no sume puntos de cinco
    fichas cuando solo puntuan once.

    Todo con fixture. Ni una lectura de `data/`.
"""

from __future__ import annotations

import tempfile

from pathlib import Path

from src.analysis.activo_grande import evaluar
from src.analysis.ascendidos import (
    detectar,
    en_el_mercado,
    medir_ascendidos,
)
from src.analysis.doctrina import (
    CITAS,
    SIN_REGLA,
    auditar,
    cargar_reglas,
    citar,
)
from src.analysis.embudo import embudo


DOCUMENTO = Path("docs") / "DOCTRINA.md"


# ============================================================
# FIXTURES
# ============================================================


DOCTRINA_FALSA = """# LA DOCTRINA DE PEPE

**Version 9.9 - 2026-01-01**

| # | Regla | Estado |
|---|---|---|
| 1 | El once es lo unico que marca | entendido |
| 9 | Comprar lo que sube | construido |
| 13 | No comprar lo que cae | hecho |
"""


def _con_documento(texto: str):
    """Un documento de doctrina de mentira, en un temporal."""

    temporal = tempfile.NamedTemporaryFile(
        "w",
        suffix=".md",
        delete=False,
        encoding="utf-8",
    )

    temporal.write(texto)
    temporal.close()

    return Path(temporal.name)


def _catalogo() -> dict:
    """
    Veinte equipos: tres sin puntos la temporada pasada -los que
    ascendieron- y diecisiete con ellos.
    """

    jugadores = {}
    equipos = {}

    player_id = 1

    for equipo in range(20):

        equipos[str(equipo)] = {"name": f"Equipo {equipo}"}

        # Los tres primeros vienen de Segunda.
        asciende = equipo < 3

        for _ in range(25):

            jugadores[str(player_id)] = {
                "id": player_id,
                "teamID": equipo,
                "pointsLastSeason": 0 if asciende else 80,
                "price": 500_000 if asciende else 5_000_000,
            }

            player_id += 1

    return {"data": {"players": jugadores, "teams": equipos}}


def _objetivo(nombre, decision, **extra) -> dict:
    base = {
        "id": abs(hash(nombre)) % 100000,
        "name": nombre,
        "position": 3,
        "decision": decision,
        "market_price": 1_000_000,
        "our_value": 1_100_000,
        "availability": "DISPONIBLE",
        "budget_applied": 2_000_000,
        "expected_points": 100,
    }
    base.update(extra)
    return base


# ============================================================
# 1. LA CITA NO SE INVENTA
# ============================================================


def test_las_reglas_salen_del_documento_no_del_codigo() -> None:
    """
    "No conviertas la doctrina en constantes nuevas."

    Si el dueño renumera o cambia un estado, esto lo sigue solo.
    """

    ruta = _con_documento(DOCTRINA_FALSA)

    try:
        cargadas = cargar_reglas(ruta)

        assert cargadas["available"]
        assert cargadas["version"] == "9.9"
        assert set(cargadas["rules"]) == {1, 9, 13}
        assert cargadas["rules"][9]["title"] == "Comprar lo que sube"

    finally:
        ruta.unlink(missing_ok=True)


def test_sin_documento_no_se_cita_nada_y_se_dice() -> None:
    cargadas = cargar_reglas(Path("no") / "existe.md")

    assert cargadas["available"] is False
    assert cargadas["rules"] == {}
    assert "No se encuentra" in cargadas["reason"]


def test_una_decision_sin_regla_sale_sin_regla() -> None:
    """
    EL ENCARGO, LITERAL

        "No fuerces la cita. Un mapeo inventado para que no haya
         huecos es peor que los huecos."
    """

    cita = citar("SUPERA_PRESUPUESTO")

    assert cita["rule"] is None
    assert cita["uncited_reason"]
    assert "tope por operacion" in cita["uncited_reason"]

    inventada = citar("UNA_QUE_NO_EXISTE")

    assert inventada["rule"] is None
    assert inventada["uncited_reason"]


def test_las_huerfanas_conocidas_tienen_motivo_escrito() -> None:
    """
    Una decision sin cita y sin explicacion no informa de nada.
    """

    for codigo, motivo in SIN_REGLA.items():
        assert len(motivo) > 40, (
            f"{codigo} sale sin cita y sin explicar por que"
        )


def test_ninguna_cita_apunta_a_una_regla_que_no_existe() -> None:
    """
    Si alguien renumera el documento, esto lo pilla.
    """

    reales = cargar_reglas()

    if not reales["available"]:
        return

    for codigo, (numero, _) in CITAS.items():
        assert numero in reales["rules"], (
            f"{codigo} cita la regla {numero} y esa regla no "
            f"esta en {DOCUMENTO}"
        )


def test_la_auditoria_separa_las_que_citan_de_las_que_no() -> None:
    estado = {
        "acquisition": {
            "targets": [
                _objetivo("Uno", "SIN_VALOR"),
                _objetivo("Dos", "SUPERA_PRESUPUESTO"),
                _objetivo("Tres", "NO_DISPONIBLE"),
            ]
        },
        "decision": {"action": "MONITOR_OFFERS"},
    }

    auditoria = auditar(estado)

    assert auditoria["available"]
    assert auditoria["decisions"] == 4
    assert auditoria["cited"] == 1
    assert auditoria["uncited"] == 3

    codigos = {h["decision"] for h in auditoria["without_rule"]}

    assert "SUPERA_PRESUPUESTO" in codigos
    assert "MONITOR_OFFERS" in codigos

    for huerfana in auditoria["without_rule"]:
        assert huerfana["why"], (
            f"{huerfana['decision']} sale sin motivo"
        )


# ============================================================
# 2. LOS ASCENDIDOS, DEDUCIDOS
# ============================================================


def test_los_ascendidos_se_deducen_del_catalogo() -> None:
    """
    No de mi memoria: de los puntos de la temporada anterior.
    """

    detectados = detectar(_catalogo())

    assert detectados["available"]
    assert len(detectados["teams"]) == 3
    assert detectados["clean_split"] is True

    assert set(detectados["teams"]) == {
        "Equipo 0",
        "Equipo 1",
        "Equipo 2",
    }


def test_si_la_separacion_no_es_limpia_se_avisa() -> None:
    """
    Un año la frontera podria no ser tan clara. Entonces el
    modulo lo dice en vez de elegir por su cuenta.
    """

    catalogo = _catalogo()

    # El cuarto equipo pasa a parecerse a los ascendidos.
    for jugador in catalogo["data"]["players"].values():
        if jugador["teamID"] == 3:
            jugador["pointsLastSeason"] = 6

    detectados = detectar(catalogo)

    assert detectados["clean_split"] is False
    assert "CUIDADO" in detectados["reason"]


def test_sin_catalogo_no_se_inventa_la_lista() -> None:
    for basura in (None, {}, {"data": {}}):
        salida = detectar(basura)
        assert salida["available"] is False
        assert salida["teams"] == []
        assert salida["reason"]


def test_el_consejo_se_mide_antes_de_creerselo() -> None:
    """
    REGLA 18: ningun umbral sin numero detras.

    El video dice que los recien ascendidos suben. Aqui se
    comprueba que el modulo lo MIDE y contesta que no cuando los
    datos dicen que no.
    """

    equipos = {"1": "10", "2": "10", "3": "99", "4": "99"}
    precios = {"1": 500_000, "2": 500_000, "3": 500_000, "4": 500_000}

    # Los del equipo 10 -el "ascendido"- caen; los otros suben.
    historico = {
        "players": {
            "1": {"p": [100, 90, 80]},
            "2": {"p": [100, 95, 90]},
            "3": {"p": [100, 110, 120]},
            "4": {"p": [100, 105, 110]},
        }
    }

    medido = medir_ascendidos(
        historico, equipos, ["10"], precios
    )

    assert medido["available"]
    assert medido["supports_advice"] is False
    assert "NO se confirma" in medido["reason"]


def test_cuando_si_suben_lo_dice_con_la_muestra() -> None:
    equipos = {str(i): ("10" if i <= 12 else "99") for i in range(1, 25)}
    precios = {str(i): 500_000 for i in range(1, 25)}

    historico = {"players": {}}

    for i in range(1, 25):
        sube = 1.10 if i <= 12 else 1.01
        precio = 100.0
        serie = []
        for _ in range(4):
            serie.append(int(precio))
            precio *= sube
        historico["players"][str(i)] = {"p": serie}

    medido = medir_ascendidos(
        historico, equipos, ["10"], precios
    )

    assert medido["supports_advice"] is True
    assert "n=12" in medido["reason"]
    assert "no para darles un factor" in medido["reason"]


def test_el_mercado_de_ascendidos_no_compra_nada() -> None:
    salida = en_el_mercado(
        [_objetivo("Uno", "SIN_VALOR", id=1)],
        {"1": "10"},
        ["10"],
    )

    assert salida["available"]
    assert salida["count"] == 1

    # Publica, no decide.
    assert "decision" in salida["rows"][0]
    assert "bid" not in salida["rows"][0]


# ============================================================
# 3. EL EMBUDO
# ============================================================


def test_el_embudo_señala_la_causa_mayor_no_la_primera() -> None:
    """
    EL FALLO QUE ESTO ARREGLA (20/09/2026)

        La frase de cabecera cogia la primera causa con muertos
        en el orden en que estan escritas, no la mas frecuente:
        decia "la causa mas comun es DISPONIBILIDAD" con 2
        cuando eran 12 por no mejorar el once.

        El titular apuntaba al sitio equivocado, que es justo lo
        que esta tabla existe para evitar.
    """

    objetivos = (
        [_objetivo(f"D{i}", "NO_DISPONIBLE") for i in range(2)]
        + [_objetivo(f"S{i}", "SIN_VALOR") for i in range(12)]
    )

    salida = embudo({"targets": objetivos})

    assert salida["available"]
    assert "NO_MEJORA_EL_ONCE" in salida["reason"]
    assert "DISPONIBILIDAD" not in salida["reason"]
    assert salida["deaths"][0]["cause"] == "NO_MEJORA_EL_ONCE"


def test_el_embudo_separa_no_tener_dinero_de_no_poder_ponerlo() -> None:
    """
    `SUPERA_PRESUPUESTO` mezclaba dos cosas: no tener el dinero,
    y tenerlo pero no poder ponerlo de una vez. Aflojar una no
    arregla la otra.
    """

    sin_dinero = _objetivo(
        "Caro", "SUPERA_PRESUPUESTO",
        market_price=15_000_000, budget_applied=2_000_000,
    )

    cabe_pero_no = _objetivo(
        "Justo", "SUPERA_PRESUPUESTO",
        market_price=1_500_000, budget_applied=2_000_000,
    )

    salida = embudo({"targets": [sin_dinero, cabe_pero_no]})

    causas = {f["name"]: f["cause"] for f in salida["rows"]}

    assert causas["Caro"] == "PRECIO"
    assert causas["Justo"] == "TOPE_POR_OPERACION"


def test_cada_objetivo_muere_una_sola_vez() -> None:
    """
    Si se contaran todos los filtros que falla, la tabla sumaria
    mas que objetivos y no diria donde mirar.
    """

    objetivos = [
        _objetivo("Uno", "SIN_VALOR"),
        _objetivo("Dos", "NO_COMPENSA"),
        _objetivo("Tres", "NO_DISPONIBLE"),
    ]

    salida = embudo({"targets": objetivos})

    assert sum(m["count"] for m in salida["deaths"]) == 3


def test_el_embudo_no_toca_ningun_tope() -> None:
    """
    "No toques ningun tope ni ningun liston esta noche."
    """

    fuente = Path(
        "src/analysis/embudo.py"
    ).read_text(encoding="utf-8")

    for prohibido in (
        "MAX_SINGLE",
        "MIN_SPECULATION_YIELD",
        "budget =",
    ):
        assert prohibido not in fuente, (
            f"el embudo toca `{prohibido}`: solo cuenta cadaveres"
        )


# ============================================================
# 4. EL ACTIVO GRANDE
# ============================================================


def _plantilla_con_estrella() -> list:
    plantilla = [{
        "id": 1,
        "name": "Estrella",
        "position": 4,
        "price": 21_000_000,
        "price_increment": 40_000,
        "points": 30,
        "starter_probability": 100.0,
    }]

    for i in range(2, 15):
        plantilla.append({
            "id": i,
            "name": f"Otro {i}",
            "position": 2 if i % 2 else 3,
            "price": 2_000_000,
            "price_increment": 0,
            "points": 6,
            "starter_probability": 80.0,
        })

    return plantilla


def test_no_se_suman_los_puntos_de_cinco_cuando_juegan_once() -> None:
    """
    LA TRAMPA QUE NO SE COMETE

        Con 21 M caben cinco fichas, pero el once no crece. Sumar
        los cinco rendimientos seria el error mas caro del
        informe.
    """

    objetivos = [
        _objetivo(
            f"Fichaje {i}", "SIN_VALOR",
            market_price=2_000_000, expected_points=76,
        )
        for i in range(8)
    ]

    salida = evaluar(
        _plantilla_con_estrella(), objetivos, 3, cash=0
    )

    assert salida["available"]
    assert salida["sell"]["would_enter_xi"] <= 10, (
        "dice que entran mas de diez al once"
    )
    assert len(salida["sell"]["basket"]) <= 5


def test_las_dos_columnas_estan_y_no_hay_recomendacion() -> None:
    salida = evaluar(
        _plantilla_con_estrella(), [], 3, cash=0
    )

    assert salida["keep"]["points_per_matchday"] > 0
    assert salida["keep"]["warning"]
    assert salida["sell"]["warning"]

    for prohibido in ("VENDER YA", "recomienda", "hay que vender"):
        assert prohibido.lower() not in salida["reason"].lower()

    assert "decide el dueño" in salida["reason"]


def test_el_activo_grande_dice_con_cuantas_jornadas_decide() -> None:
    salida = evaluar(_plantilla_con_estrella(), [], 3)

    assert salida["keep"]["matchdays"] == 3
    assert "3 jornadas" in salida["keep"]["warning"]


def test_los_miles_no_se_comen_las_comas_de_la_prosa() -> None:
    """
    EL FALLO QUE YA HA PASADO CUATRO VECES

        Aplicar `.replace(",", ".")` a la frase entera convierte
        "el resto de la plantilla, 714.202" en "el resto de la
        plantilla. 714.202".
    """

    salida = evaluar(_plantilla_con_estrella(), [], 3)

    assert "el resto de la plantilla," in salida["reason"], (
        "las comas de la prosa se han convertido en puntos"
    )


# ============================================================
# 5. NI DECIDE NI CAMBIA DE FORMA
# ============================================================


def test_la_forma_no_cambia_con_los_datos() -> None:
    """
    Regla de la casa desde el 18/09.
    """

    casos = [
        (
            "doctrina.auditar",
            auditar({"acquisition": {"targets": [
                _objetivo("Uno", "SIN_VALOR")
            ]}}),
            auditar(None),
        ),
        (
            "doctrina.citar",
            citar("SIN_VALOR"),
            citar(None),
        ),
        (
            "ascendidos.detectar",
            detectar(_catalogo()),
            detectar(None),
        ),
        (
            "ascendidos.en_el_mercado",
            en_el_mercado(
                [_objetivo("Uno", "SIN_VALOR", id=1)],
                {"1": "10"},
                ["10"],
            ),
            en_el_mercado(None, None, None),
        ),
        (
            "embudo.embudo",
            embudo({"targets": [_objetivo("Uno", "SIN_VALOR")]}),
            embudo(None),
        ),
        (
            "activo_grande.evaluar",
            evaluar(_plantilla_con_estrella(), [], 3),
            evaluar(None, None, 0),
        ),
    ]

    rotas = []

    for nombre, lleno, vacio in casos:

        faltan = set(lleno) - set(vacio)
        sobran = set(vacio) - set(lleno)

        if faltan or sobran:
            rotas.append(
                f"  {nombre}: faltan {sorted(faltan)}, "
                f"sobran {sorted(sobran)}"
            )

    assert not rotas, (
        "estas cambian de forma segun los datos:\n"
        + "\n".join(rotas)
    )


def test_nada_de_esto_decide_ni_lanza() -> None:
    import ast

    prohibidos = (
        "autopilot_executor",
        "write_client",
        "BiwengerWriteClient",
        "optimal_bid",
    )

    for ruta in (
        "src/analysis/doctrina.py",
        "src/analysis/ascendidos.py",
        "src/analysis/embudo.py",
        "src/analysis/activo_grande.py",
    ):
        arbol = ast.parse(
            Path(ruta).read_text(encoding="utf-8")
        )

        for nodo in ast.walk(arbol):

            if not isinstance(nodo, (ast.Import, ast.ImportFrom)):
                continue

            texto = ast.dump(nodo)

            for prohibido in prohibidos:
                assert prohibido not in texto, (
                    f"{ruta} importa `{prohibido}`"
                )

    for basura in (None, {}, [], "x"):
        assert isinstance(auditar(basura), dict)
        assert isinstance(detectar(basura), dict)
        assert isinstance(embudo(basura), dict)
        assert isinstance(evaluar(basura, basura, 0), dict)


def test_estas_guardias_no_leen_el_estado() -> None:
    from src.analysis.test_verja_determinista_v1 import (
        lecturas_de_estado,
    )

    assert not lecturas_de_estado(
        "src.analysis.test_doctrina_v1"
    )

    for modulo in (
        "src.analysis.doctrina",
        "src.analysis.ascendidos",
        "src.analysis.embudo",
        "src.analysis.activo_grande",
    ):
        assert not lecturas_de_estado(modulo), (
            f"{modulo} lee estado mutable"
        )


TESTS = [
    test_las_reglas_salen_del_documento_no_del_codigo,
    test_sin_documento_no_se_cita_nada_y_se_dice,
    test_una_decision_sin_regla_sale_sin_regla,
    test_las_huerfanas_conocidas_tienen_motivo_escrito,
    test_ninguna_cita_apunta_a_una_regla_que_no_existe,
    test_la_auditoria_separa_las_que_citan_de_las_que_no,
    test_los_ascendidos_se_deducen_del_catalogo,
    test_si_la_separacion_no_es_limpia_se_avisa,
    test_sin_catalogo_no_se_inventa_la_lista,
    test_el_consejo_se_mide_antes_de_creerselo,
    test_cuando_si_suben_lo_dice_con_la_muestra,
    test_el_mercado_de_ascendidos_no_compra_nada,
    test_el_embudo_señala_la_causa_mayor_no_la_primera,
    test_el_embudo_separa_no_tener_dinero_de_no_poder_ponerlo,
    test_cada_objetivo_muere_una_sola_vez,
    test_el_embudo_no_toca_ningun_tope,
    test_no_se_suman_los_puntos_de_cinco_cuando_juegan_once,
    test_las_dos_columnas_estan_y_no_hay_recomendacion,
    test_el_activo_grande_dice_con_cuantas_jornadas_decide,
    test_los_miles_no_se_comen_las_comas_de_la_prosa,
    test_la_forma_no_cambia_con_los_datos,
    test_nada_de_esto_decide_ni_lanza,
    test_estas_guardias_no_leen_el_estado,
]


def main() -> None:

    print()
    print("=" * 60)
    print("LA DOCTRINA V1")
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
