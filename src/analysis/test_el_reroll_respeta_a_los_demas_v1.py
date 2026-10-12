"""
EL REROLL RESPETA A LOS DEMAS (12/10/2026). Guardias de
`src/analysis/los_que_otros_venden.py`, de
`decision_orchestrator.los_que_se_pueden_rerollear` y de
`computer_offer_reroll_engine.revalidate_reroll_offer`.

LO QUE PASABA

    El REROLL del orquestador (670, la escritura de la vuelta) tiraba
    toda oferta del Computer a -2 % o peor si quedaba otro ciclo. No
    leia a la ronda, los chollos, la mejora, la orden del gestor ni el
    cierre, que corren DESPUES en la misma vuelta y cobran justo esas
    ofertas (desde pagado + 1 % o desde el 90 %; Jutgla, desde
    2.466.000). La oferta que iban a aceptar ya estaba rechazada.

QUE SE PRUEBA

    1. Cada libro aporta a los suyos: la ronda y los chollos (claves),
       la mejora (el que entra y el que sale), la orden VIVA
       (`vender_si_ficha`: encendida y valida) y el cierre (`vender` y
       `candidatos`, solo si es de las ultimas 3 h).
    2. Los libros por defecto son los de cada modulo, no una copia.
    3. El orquestador saca esas ofertas de los candidatos, dice por que
       y deja el resto en su orden; si algo falla, ningun candidato.
    4. El orquestador filtra ANTES de elegir el reroll y lo publica en
       `no_se_rerollean`.
    5. `revalidate_reroll_offer` no autoriza esas ofertas.
    6. El executor entero, con un escritor de mentira, no llega a
       `reject_offer` para ellas (y si para las demas).
    7. Nunca lanza.

    Sin red, sin login, sin reloj real y sin disco de produccion.
"""

from __future__ import annotations

import inspect
import json
import os
import sys
import tempfile

from datetime import datetime, timedelta, timezone
from pathlib import Path


RAIZ = Path(__file__).parents[2]

if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))


import src.actions.autopilot_executor as executor_mod          # noqa: E402
import src.analysis.computer_offer_reroll_engine as motor_mod  # noqa: E402
import src.analysis.decision_orchestrator as orquestador       # noqa: E402
import src.analysis.los_que_otros_venden as otros_mod          # noqa: E402

from src.analysis.decision_orchestrator import (               # noqa: E402
    los_que_se_pueden_rerollear,
)
from src.analysis.los_que_otros_venden import (                # noqa: E402
    HORAS_DEL_CIERRE,
    los_de_la_oferta,
    los_que_otros_venden,
    quien_los_vende,
)


AHORA = datetime(2026, 10, 12, 12, 0, tzinfo=timezone.utc)

# Los ids reales del 12/10.
JUTGLA, DIEGO_RICO, IVAN, GERARD, MOI = 3159, 5678, 17937, 34111, 1462
OTRO = 99_001          # nadie lo vende

ENV_ORDEN = "BORDALAS_LA_ORDEN_DEL_GESTOR"

ORDEN = {
    "caduca": "2026-11-30T23:59:00+01:00",
    "fichar": [
        {"player_id": IVAN, "nombre": "Iván Romero", "puja": 3_777_000},
        {"player_id": GERARD, "nombre": "Gerard Martín", "puja": 4_989_000},
    ],
    "vender_si_ficha": {"jugadores": [
        {"player_id": JUTGLA, "nombre": "Jutglà", "suelo": 2_466_000, "si_esta": IVAN},
        {"player_id": DIEGO_RICO, "nombre": "Diego Rico", "suelo": 470_000, "si_esta": GERARD},
    ]},
    "proteger": [{"player_id": 26271, "nombre": "Yamal"}],
}


class _Entorno:
    """Pone y quita una variable de entorno sin dejar rastro."""

    def __init__(self, nombre, valor):
        self.nombre, self.valor = nombre, valor

    def __enter__(self):
        self.antes = os.environ.get(self.nombre)
        if self.valor is None:
            os.environ.pop(self.nombre, None)
        else:
            os.environ[self.nombre] = self.valor
        return self

    def __exit__(self, *_):
        if self.antes is None:
            os.environ.pop(self.nombre, None)
        else:
            os.environ[self.nombre] = self.antes


def _libros(carpeta: Path, **contenido) -> dict:
    """Escribe en `carpeta` los libros dados y devuelve sus rutas (todas)."""

    rutas = {
        "ronda": carpeta / "la_ronda.json",
        "chollos": carpeta / "los_chollos.json",
        "mejora": carpeta / "la_mejora.json",
        "cierre": carpeta / "el_cierre.json",
        "orden": carpeta / "la_orden_del_gestor.json",
    }
    for nombre, datos in contenido.items():
        texto = datos if isinstance(datos, str) else json.dumps(datos)
        rutas[nombre].write_text(texto, encoding="utf-8")
    return rutas


def _oferta(offer_id, pid, nombre, importe=2_600_000):
    return {
        "offer_id": offer_id,
        "amount": importe,
        "player_ids": [pid],
        "players": [{"id": pid, "name": nombre}],
        "player_id": pid,
        "action": "REROLL_CANDIDATE",
        "reroll_safe": True,
        "replacement_cycle_available": True,
        "simulation": {"guaranteed_after_reroll": True},
    }


# ============================================================
# 1. CADA LIBRO APORTA A LOS SUYOS
# ============================================================


def test_la_ronda_y_los_chollos_por_sus_claves():
    with tempfile.TemporaryDirectory() as d:
        rutas = _libros(Path(d), ronda={str(MOI): 1_101_000},
                        chollos={"4321": 500_000})
        with _Entorno(ENV_ORDEN, None):
            quien = quien_los_vende(rutas, AHORA)
    assert quien == {MOI: ["LA_RONDA"], 4321: ["LOS_CHOLLOS"]}, quien
    print("  OK  la ronda y los chollos venden lo de su libro")


def test_la_mejora_el_que_entra_y_el_que_sale():
    with tempfile.TemporaryDirectory() as d:
        rutas = _libros(Path(d), mejora={
            "7001": {"sale": 7002, "suelo": 900_000, "puja": 1_000_000},
            "7003": {"sale": None},
            "no-es-un-id": {"sale": "7004"},
        })
        with _Entorno(ENV_ORDEN, None):
            ids = los_que_otros_venden(rutas, AHORA)
    assert ids == {7001, 7002, 7003, 7004}, ids
    print("  OK  la mejora: el que entra y el que sale")


def test_la_orden_solo_viva():
    with tempfile.TemporaryDirectory() as d:
        rutas = _libros(Path(d), orden=ORDEN)

        with _Entorno(ENV_ORDEN, "1"):
            quien = quien_los_vende(rutas, AHORA)
        assert quien == {JUTGLA: ["LA_ORDEN_DEL_GESTOR"],
                         DIEGO_RICO: ["LA_ORDEN_DEL_GESTOR"]}, quien

        # Apagada: no vende nadie (como `vetados`/`protegidos`).
        with _Entorno(ENV_ORDEN, None):
            assert los_que_otros_venden(rutas, AHORA) == set()

        # Caducada.
        with _Entorno(ENV_ORDEN, "1"):
            despues = datetime(2026, 12, 1, tzinfo=timezone.utc)
            assert los_que_otros_venden(rutas, despues) == set()

        # No vale (nombra a Yamal): ni la orden la ejecuta.
        mala = json.loads(json.dumps(ORDEN))
        mala["vender_si_ficha"]["jugadores"].append(
            {"player_id": 26271, "nombre": "Yamal"})
        rutas = _libros(Path(d), orden=mala)
        with _Entorno(ENV_ORDEN, "1"):
            assert los_que_otros_venden(rutas, AHORA) == set()
    print("  OK  la orden: solo la viva, encendida y valida")


def test_el_cierre_solo_si_es_de_las_ultimas_3_horas():
    plan = {
        "version": 2, "activo": True,
        "vender": [OTRO + 1],
        "candidatos": [{"id": OTRO + 1, "elegido": True},
                       {"id": OTRO + 2, "elegido": False}, OTRO + 3],
    }
    with tempfile.TemporaryDirectory() as d, _Entorno(ENV_ORDEN, None):
        for horas, esperado in (
            (0.5, {OTRO + 1, OTRO + 2, OTRO + 3}),
            (HORAS_DEL_CIERRE - 0.01, {OTRO + 1, OTRO + 2, OTRO + 3}),
            (HORAS_DEL_CIERRE + 0.01, set()),
            (30, set()),
            (-1, set()),                      # del futuro: raro, no manda
        ):
            generado = (AHORA - timedelta(hours=horas)).isoformat()
            rutas = _libros(Path(d), cierre={**plan, "generated_at": generado})
            ids = los_que_otros_venden(rutas, AHORA)
            assert ids == esperado, (horas, ids)

        # Sin hora, no se sabe de cuando es: no manda.
        rutas = _libros(Path(d), cierre=plan)
        assert los_que_otros_venden(rutas, AHORA) == set()

        quien = quien_los_vende(
            _libros(Path(d), cierre={**plan, "generated_at": AHORA.isoformat()}),
            AHORA,
        )
        assert set(quien[OTRO + 1]) == {"EL_CIERRE"}, quien
    print("  OK  el cierre: vender y candidatos, solo de las ultimas 3 h")


def test_todos_a_la_vez_y_quien():
    with tempfile.TemporaryDirectory() as d:
        rutas = _libros(
            Path(d),
            ronda={str(MOI): 1_101_000},
            mejora={str(MOI): {"sale": JUTGLA}},
            orden=ORDEN,
            cierre={"vender": [JUTGLA], "generated_at": AHORA.isoformat()},
        )
        with _Entorno(ENV_ORDEN, "1"):
            quien = quien_los_vende(rutas, AHORA)
    assert sorted(quien[MOI]) == ["LA_MEJORA", "LA_RONDA"], quien
    assert sorted(quien[JUTGLA]) == ["EL_CIERRE", "LA_MEJORA",
                                     "LA_ORDEN_DEL_GESTOR"], quien
    assert quien[DIEGO_RICO] == ["LA_ORDEN_DEL_GESTOR"], quien
    print("  OK  todos a la vez: cada uno dice quien lo vende")


# ============================================================
# 2. LOS LIBROS POR DEFECTO SON LOS DE CADA MODULO
# ============================================================


def test_los_libros_por_defecto_son_los_de_cada_modulo():
    from src.actions import el_cierre_de_la_jornada as cierre
    from src.actions import la_mejora_del_once as mejora
    from src.actions import la_ronda_de_la_manana as ronda
    from src.actions import los_chollos as chollos

    rutas = otros_mod._rutas_por_defecto()
    assert rutas["ronda"] == ronda.LIBRO, rutas
    assert rutas["chollos"] == chollos.LIBRO, rutas
    assert rutas["mejora"] == mejora.LIBRO, rutas
    assert rutas["cierre"] == cierre.PLAN, rutas
    # None: `leer_la_orden` lee `la_orden_del_gestor.RUTA`, como sus
    # ayudantes.
    assert rutas["orden"] is None, rutas
    print("  OK  los libros por defecto son los de cada modulo")


# ============================================================
# 3. EL ORQUESTADOR SACA ESAS OFERTAS DE LOS CANDIDATOS
# ============================================================


def test_el_orquestador_saca_a_los_que_otros_venden():
    jutgla = _oferta(901, JUTGLA, "Jutglà", 2_600_000)
    otro = _oferta(902, OTRO, "Otro", 1_000_000)
    moi = _oferta(903, MOI, "Moi Gómez", 1_050_000)

    r = los_que_se_pueden_rerollear(
        [jutgla, otro, moi],
        {JUTGLA: ["LA_ORDEN_DEL_GESTOR"], MOI: ["LA_RONDA"]},
    )
    assert r["reroll_candidates"] == [otro], r
    fuera = {x["offer_id"]: x for x in r["no_se_rerollean"]}
    assert set(fuera) == {901, 903}, fuera
    assert fuera[901]["player_ids"] == [JUTGLA], fuera
    assert fuera[901]["names"] == ["Jutglà"], fuera
    assert fuera[901]["motivo"] == "LO_VENDE_OTRO_MODULO", fuera
    assert fuera[901]["modulos"] == ["LA_ORDEN_DEL_GESTOR"], fuera
    assert fuera[903]["modulos"] == ["LA_RONDA"], fuera

    # Nadie vende: la lista sale como entra, en su orden.
    r = los_que_se_pueden_rerollear([jutgla, otro, moi], {})
    assert r["reroll_candidates"] == [jutgla, otro, moi], r
    assert r["no_se_rerollean"] == [], r

    # Sin candidatos no se lee nada.
    r = los_que_se_pueden_rerollear([], None)
    assert r == {"reroll_candidates": [], "no_se_rerollean": []}, r
    print("  OK  el orquestador saca a los que otros venden")


def test_el_orquestador_lee_los_libros_si_no_se_le_dan():
    original = otros_mod.quien_los_vende
    try:
        otros_mod.quien_los_vende = lambda *a, **k: {JUTGLA: ["EL_CIERRE"]}
        r = los_que_se_pueden_rerollear([_oferta(901, JUTGLA, "Jutglà")])
    finally:
        otros_mod.quien_los_vende = original
    assert r["reroll_candidates"] == [], r
    assert r["no_se_rerollean"][0]["modulos"] == ["EL_CIERRE"], r
    print("  OK  en produccion el orquestador lee los libros")


def test_si_algo_falla_ningun_candidato():
    r = los_que_se_pueden_rerollear(
        [_oferta(901, JUTGLA, "Jutglà")], {"no-es-un-id": ["X"]},
    )
    assert r["reroll_candidates"] == [], r
    assert "error" in r, r
    print("  OK  si algo falla, ningun reroll (la oferta no se tira)")


# ============================================================
# 4. EL ORQUESTADOR FILTRA ANTES DE ELEGIR EL REROLL
# ============================================================


def test_el_orquestador_filtra_antes_de_elegir():
    fuente = inspect.getsource(orquestador.build_global_decision_uncached)

    filtro = fuente.find("los_que_se_pueden_rerollear(")
    reasigna = fuente.find('reroll_candidates = rerolleables["reroll_candidates"]')
    elige = fuente.find("best_reroll = (")

    assert filtro != -1, "el orquestador no llama al filtro"
    assert reasigna > filtro, "el orquestador no usa la lista filtrada"
    assert elige > reasigna, "el reroll se elige antes del filtro"
    # Y se puede mirar a quien se dejo fuera.
    assert '"no_se_rerollean"' in fuente
    print("  OK  el orquestador filtra antes de elegir y lo publica")


# ============================================================
# 5. LA REVALIDACION NO LAS AUTORIZA
# ============================================================


class _Tablero:
    """Sustituye al motor entero por un tablero con estas ofertas."""

    def __init__(self, *ofertas):
        self.ofertas = list(ofertas)

    def __enter__(self):
        self.original = motor_mod.build_computer_offer_reroll_board
        motor_mod.build_computer_offer_reroll_board = (
            lambda *a, **k: {"offers": self.ofertas,
                             "reroll_candidates": self.ofertas}
        )
        return self

    def __exit__(self, *_):
        motor_mod.build_computer_offer_reroll_board = self.original


def test_la_revalidacion_no_autoriza_lo_que_otro_vende():
    with _Tablero(_oferta(901, JUTGLA, "Jutglà"), _oferta(902, OTRO, "Otro")):
        r = motor_mod.revalidate_reroll_offer(
            {}, 901, quien_los_vende={JUTGLA: ["LA_ORDEN_DEL_GESTOR"]})
        assert r["authorized"] is False, r
        assert r["status"] == "LO_VENDE_OTRO_MODULO", r
        assert r["modulos"] == ["LA_ORDEN_DEL_GESTOR"], r

        # La otra si, con el mismo tablero.
        r = motor_mod.revalidate_reroll_offer(
            {}, 902, quien_los_vende={JUTGLA: ["LA_ORDEN_DEL_GESTOR"]})
        assert r["authorized"] is True, r

        # Sin pasarlo, lee los libros (aqui, de mentira).
        original = otros_mod.quien_los_vende
        try:
            otros_mod.quien_los_vende = lambda *a, **k: {OTRO: ["LA_RONDA"]}
            r = motor_mod.revalidate_reroll_offer({}, 902)
        finally:
            otros_mod.quien_los_vende = original
        assert r["status"] == "LO_VENDE_OTRO_MODULO", r

        # Si no se puede saber, no se tira la oferta.
        r = motor_mod.revalidate_reroll_offer(
            {}, 902, quien_los_vende={"no-es-un-id": ["X"]})
        assert r["authorized"] is False, r
        assert r["status"] == "LO_VENDE_OTRO_MODULO_SIN_LEER", r
    print("  OK  la revalidacion no autoriza lo que otro vende")


# ============================================================
# 6. EL EXECUTOR ENTERO, CON UN ESCRITOR DE MENTIRA
# ============================================================


def test_el_executor_no_rechaza_lo_que_otro_vende():
    import src.actions.el_rastro as rastro_mod

    rechazos, apuntes = [], []

    class _Escritor:
        def reject_offer(self, offer_id, execute=False):
            rechazos.append(offer_id)
            return {"success": True, "http_status": 204, "response": None}

    originales = (
        executor_mod.BiwengerWriteClient,
        executor_mod.refresh_snapshot_for_write_revalidation,
        executor_mod.record_reroll,
        rastro_mod.apuntar_escritura,
        otros_mod.quien_los_vende,
    )

    decision = {
        "action": "REROLL_COMPUTER_OFFER",
        "executable": True,
        "temporal_gate": {"phase": "NORMAL", "operations_locked": False,
                          "hard_safety_mode": False},
        "data": {"offer": {"offer_id": 901}},
    }

    try:
        executor_mod.BiwengerWriteClient = _Escritor
        executor_mod.refresh_snapshot_for_write_revalidation = (
            lambda: ("foto_de_mentira.json", {}))
        executor_mod.record_reroll = lambda **k: apuntes.append(k)
        rastro_mod.apuntar_escritura = lambda *a, **k: None
        otros_mod.quien_los_vende = (
            lambda *a, **k: {JUTGLA: ["LA_ORDEN_DEL_GESTOR"]})

        with _Tablero(_oferta(901, JUTGLA, "Jutglà"), _oferta(902, OTRO, "Otro")):
            r = executor_mod.execute_autopilot_decision(decision, execute=True)
            assert rechazos == [], rechazos
            assert r["write_performed"] is False, r
            assert r["status"] == "LO_VENDE_OTRO_MODULO", r

            # La de nadie si se rechaza: el arnes escribe de verdad.
            r = executor_mod.execute_autopilot_decision(
                {**decision, "data": {"offer": {"offer_id": 902}}}, execute=True)
            assert rechazos == [902], rechazos
            assert r["status"] == "OFFER_REROLLED", r
            assert [a["player_id"] for a in apuntes] == [OTRO], apuntes
    finally:
        (
            executor_mod.BiwengerWriteClient,
            executor_mod.refresh_snapshot_for_write_revalidation,
            executor_mod.record_reroll,
            rastro_mod.apuntar_escritura,
            otros_mod.quien_los_vende,
        ) = originales
    print("  OK  el executor no rechaza la oferta de lo que otro vende")


# ============================================================
# 7. NUNCA LANZA
# ============================================================


def test_nunca_lanza():
    with tempfile.TemporaryDirectory() as d, _Entorno(ENV_ORDEN, "1"):
        carpeta = Path(d)

        # Ficheros que no existen.
        assert los_que_otros_venden(_libros(carpeta), AHORA) == set()

        # Basura y tipos raros en todos los libros.
        for basura in ("no es json", "[1, 2, 3]", "null", "7", '"texto"',
                       '{"vender": "x", "generated_at": 5}'):
            rutas = _libros(carpeta, ronda=basura, chollos=basura,
                            mejora=basura, cierre=basura, orden=basura)
            assert los_que_otros_venden(rutas, AHORA) == set(), basura

        # Uno roto no tapa a los demas.
        rutas = _libros(carpeta, ronda="{roto", chollos={str(MOI): 1},
                        mejora={"x": "no es un cambio", "8": [1]},
                        cierre={"vender": [None, True, "x", {"id": None}, 5],
                                "generated_at": AHORA.isoformat()},
                        orden={"caduca": "manana"})
        assert los_que_otros_venden(rutas, AHORA) == {MOI, 8, 5}, \
            los_que_otros_venden(rutas, AHORA)

        # Rutas y relojes raros (todas dadas: nada de produccion).
        raras = {"ronda": 5, "chollos": None, "mejora": [],
                 "cierre": object(), "orden": carpeta / "no_existe.json"}
        assert los_que_otros_venden(raras, AHORA) == set()
        assert isinstance(los_que_otros_venden(rutas, "no es una fecha"), set)
        assert isinstance(los_que_otros_venden(rutas, datetime(2026, 10, 12)), set)
        assert isinstance(quien_los_vende("no es un dict", AHORA), dict)

    # Ofertas raras.
    assert los_de_la_oferta(None) == set()
    assert los_de_la_oferta({"player_ids": [None, "x", True, "5"],
                             "players": [None, {"id": 6}, "x"],
                             "player_id": 7}) == {5, 6, 7}
    r = los_que_se_pueden_rerollear([None, "x", {"offer_id": 1}], {JUTGLA: ["X"]})
    assert r["reroll_candidates"] == [None, "x", {"offer_id": 1}], r
    r = los_que_se_pueden_rerollear(5, {})
    assert r["reroll_candidates"] == [], r
    print("  OK  nunca lanza")


TESTS = [
    test_la_ronda_y_los_chollos_por_sus_claves,
    test_la_mejora_el_que_entra_y_el_que_sale,
    test_la_orden_solo_viva,
    test_el_cierre_solo_si_es_de_las_ultimas_3_horas,
    test_todos_a_la_vez_y_quien,
    test_los_libros_por_defecto_son_los_de_cada_modulo,
    test_el_orquestador_saca_a_los_que_otros_venden,
    test_el_orquestador_lee_los_libros_si_no_se_le_dan,
    test_si_algo_falla_ningun_candidato,
    test_el_orquestador_filtra_antes_de_elegir,
    test_la_revalidacion_no_autoriza_lo_que_otro_vende,
    test_el_executor_no_rechaza_lo_que_otro_vende,
    test_nunca_lanza,
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
    print(f"{len(TESTS) - fallos}/{len(TESTS)} en verde")
    sys.exit(1 if fallos else 0)


if __name__ == "__main__":
    main()
