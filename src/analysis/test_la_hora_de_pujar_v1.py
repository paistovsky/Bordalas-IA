"""
La hora de pujar: dentro de la ventana la puja no pierde contra un tramite.

DE DONDE SALE (22/09/2026)

    `BUY_SPECULATION` vale 400 SIEMPRE. Con ese numero pierde
    contra renovar urgente (690), caducidad urgente (680),
    cobrar ofertas (650) y publicar por solvencia (500) — y gana
    a renovar sin prisa (350) a las cuatro de la tarde, cuando la
    puja no corre ninguna prisa.

    Las dos mitades estan mal y en direcciones contrarias, porque
    una accion que solo sirve en una franja no cabe en un numero
    fijo.

LO QUE SE PROTEGE

    1. QUE DENTRO DE LA VENTANA LA PUJA GANE A UN TRAMITE. Es la
       guardia que pidio el encargo.
    2. Que FUERA de la ventana pierda contra renovar y publicar
       — sin eso, esto seria "subir la puja", que no es lo que se
       propone.
    3. QUE EL ONCE GANE SIEMPRE, dentro y fuera. No se discute.
    4. Que apagado el numero siga siendo el 400 de siempre.
    5. Que los dos numeros salgan de la tabla y no de la cabeza
       de nadie.
    6. Que sin reloj no se suba nada.
    7. Que la ventana no se redefina aqui.
    8. Que la forma no cambie con los datos.
    9. Que el modulo no lea el mundo.

ESTAS GUARDIAS NO LEEN EL MUNDO

    Ni `data/`, ni red, ni reloj: los segundos al reset entran
    por la puerta. La unica que toca el entorno es la del
    interruptor —que ES una variable de entorno— y lo deja como
    estaba.

COMO SE USA

    python -m src.analysis.test_la_hora_de_pujar_v1
"""

from __future__ import annotations

import os


# EL ENTORNO NO DECIDE ESTA GUARDIA (doctrina 104)
os.environ.pop("BORDALAS_PUJAR_EN_LA_VENTANA", None)

import json                                         # noqa: E402

from src.analysis.decision_orchestrator import PRIORITY  # noqa: E402
from src.analysis.la_subasta import (                # noqa: E402
    VENTANA_MINUTOS,
    ventana_abierta,
)
from src.analysis.la_hora_de_pujar import (          # noqa: E402
    EN_LA_VENTANA,
    ENV as HORA_ENV,
    FUERA_DE_LA_VENTANA,
    LA_DE_HOY,
    gana_la_puja,
    prioridad_de_la_puja,
)


class _Interruptor:
    """Pone y quita una variable, y la deja como estaba."""

    def __init__(self, nombre, valor="1"):
        self.nombre = nombre
        self.valor = valor

    def __enter__(self):
        self.antes = os.environ.get(self.nombre)
        os.environ[self.nombre] = self.valor
        return self

    def __exit__(self, *_):
        if self.antes is None:
            os.environ.pop(self.nombre, None)
        else:
            os.environ[self.nombre] = self.antes
        return False


# Los dos instantes salen de la constante, no se escriben a mano:
# el 10/09 la ventana paso de 15 a 135 minutos y unos numeros
# escritos a mano se quedaron dentro sin que nadie se enterara.
DENTRO = VENTANA_MINUTOS * 60 - 60

FUERA = VENTANA_MINUTOS * 60 + 60


def _cola(*candidatos) -> list:
    """La cola del orquestador, ordenada como el la ordena."""

    filas = list(candidatos)

    filas.sort(key=lambda item: item["priority"], reverse=True)

    return filas


def _tramite(nombre, prioridad) -> dict:
    return {"action": nombre, "priority": prioridad}


# ============================================================
# 1. LA QUE PIDIO EL ENCARGO
# ============================================================

def test_en_la_ventana_la_puja_no_pierde_contra_un_tramite():
    """
    Con el interruptor puesto, dentro de la ventana y con una puja
    y una renovacion NO urgente en la cola, gana la puja.

    MUERDE SI EL CASO ESTA FUERA DE LA VENTANA: si `DENTRO` no
    cayera dentro de los 135 minutos, esto no estaria midiendo
    nada (doctrina 24). Y muerde tambien si la renovacion del caso
    fuese la urgente, que es otra cosa y tiene que seguir ganando.
    """

    # ------------------------------------------------
    # EL CASO ESTA DONDE DICE ESTAR
    # ------------------------------------------------
    assert ventana_abierta(DENTRO)["abierta"] is True, (
        f"a {DENTRO} s del reset la ventana esta CERRADA: este "
        f"caso no mide la ventana"
    )

    renovar = _tramite(
        "RENEW_MARKET_LISTING", PRIORITY["MARKET_LISTING_RENEW"]
    )

    assert renovar["priority"] != PRIORITY[
        "MARKET_LISTING_RENEW_URGENT"
    ], (
        "el tramite del caso es la renovacion URGENTE: esa tiene "
        "que ganar, y el caso no probaria lo que dice"
    )

    # ------------------------------------------------
    # HOY, CON EL NUMERO FIJO, LA PUJA PIERDE O EMPATA MAL
    # ------------------------------------------------
    hoy = prioridad_de_la_puja(DENTRO)

    assert hoy["prioridad"] == LA_DE_HOY, (
        f"apagado, la puja tiene que valer {LA_DE_HOY}"
    )

    # ------------------------------------------------
    # CON EL INTERRUPTOR, LA PUJA GANA
    # ------------------------------------------------
    with _Interruptor(HORA_ENV):

        puja = _tramite(
            "BUY_SPECULATION",
            prioridad_de_la_puja(DENTRO)["prioridad"],
        )

        cola = _cola(renovar, puja)

    assert cola[0]["action"] == "BUY_SPECULATION", (
        f"dentro de la ventana gana {cola[0]['action']} con "
        f"{cola[0]['priority']}, y la puja vale "
        f"{puja['priority']}"
    )

    assert puja["priority"] == EN_LA_VENTANA

    # Y le gana a TODOS los tramites, no solo a ese.
    with _Interruptor(HORA_ENV):
        for nombre in (
            "MARKET_LISTING_RENEW",
            "MARKET_LISTING_RENEW_URGENT",
            "ACCEPT_EXPIRY_URGENT",
            "COMPUTER_OFFER_REROLL_WATCH",
            "ACCEPT_EXPIRY_WATCH",
            "INCOMING_OFFERS",
            "LIQUIDITY_MAINTENANCE",
            "SOLVENCY_NORMAL",
        ):
            assert gana_la_puja(DENTRO, PRIORITY[nombre]), (
                f"dentro de la ventana la puja pierde contra "
                f"{nombre} ({PRIORITY[nombre]})"
            )


# ============================================================
# 2. Y FUERA PIERDE, QUE ES LA OTRA MITAD
# ============================================================

def test_fuera_de_la_ventana_la_puja_pierde_contra_renovar():
    """
    Si sólo subiera, esto seria "subir la puja" y no una prioridad
    por momento. Fuera de la ventana esperar una vuelta no le
    cuesta nada a la puja, y a la publicacion si.
    """

    assert ventana_abierta(FUERA)["abierta"] is False, (
        f"a {FUERA} s del reset la ventana sigue ABIERTA: el caso "
        f"no esta fuera"
    )

    with _Interruptor(HORA_ENV):

        puja = _tramite(
            "BUY_SPECULATION",
            prioridad_de_la_puja(FUERA)["prioridad"],
        )

        cola = _cola(
            _tramite(
                "RENEW_MARKET_LISTING",
                PRIORITY["MARKET_LISTING_RENEW"],
            ),
            puja,
        )

    assert puja["priority"] == FUERA_DE_LA_VENTANA
    assert cola[0]["action"] == "RENEW_MARKET_LISTING", (
        f"fuera de la ventana tendria que mandar renovar y manda "
        f"{cola[0]['action']}"
    )

    with _Interruptor(HORA_ENV):
        for nombre in ("MARKET_LISTING_RENEW", "SOLVENCY_NORMAL"):
            assert not gana_la_puja(FUERA, PRIORITY[nombre]), (
                f"fuera de la ventana la puja le gana a {nombre}"
            )

    # Y HOY ES AL REVES: con el 400 fijo la puja le gana a
    # renovar a cualquier hora. Sin esto no se veria que el
    # cambio tambien BAJA.
    assert LA_DE_HOY > PRIORITY["MARKET_LISTING_RENEW"], (
        "hoy la puja ya perderia contra renovar fuera de la "
        "ventana: entonces esta mitad del cambio no cambia nada"
    )


# ============================================================
# 3. EL ONCE GANA SIEMPRE. NO SE DISCUTE.
# ============================================================

def test_el_once_gana_siempre_dentro_y_fuera():

    del_once = (
        "LINEUP_LOW",
        "LINEUP_UPDATE_LOW",
        "LINEUP_MODERATE",
        "LINEUP_UPDATE_MODERATE",
        "LINEUP_HIGH",
        "LINEUP_UPDATE_HIGH",
        "LINEUP_VERY_HIGH",
        "LINEUP_UPDATE_VERY_HIGH",
        "LINEUP_UPDATE_EMERGENCY",
        "EMERGENCY_LINEUP",
        "HARD_SAFETY",
        "ROUND_LOCK",
    )

    with _Interruptor(HORA_ENV):
        for cuando in (DENTRO, FUERA):
            for nombre in del_once:
                assert not gana_la_puja(cuando, PRIORITY[nombre]), (
                    f"a {cuando} s del reset la puja le gana a "
                    f"{nombre} ({PRIORITY[nombre]}): el once tiene "
                    f"que ganar SIEMPRE"
                )


# ============================================================
# 4. APAGADO ES EL 400 DE SIEMPRE
# ============================================================

def test_apagado_la_prioridad_es_la_de_siempre():

    assert os.environ.get(HORA_ENV) is None

    for cuando in (DENTRO, FUERA, None, 0, -5):
        visto = prioridad_de_la_puja(cuando)
        assert visto["prioridad"] == LA_DE_HOY, (
            f"apagado y a {cuando} s la puja vale "
            f"{visto['prioridad']}"
        )
        assert visto["activa"] is False

    # Y encendido SI cambia, en las dos direcciones: sin esto la
    # de arriba pasaria aunque el interruptor no hiciera nada.
    with _Interruptor(HORA_ENV):
        assert prioridad_de_la_puja(DENTRO)["prioridad"] > LA_DE_HOY
        assert prioridad_de_la_puja(FUERA)["prioridad"] < LA_DE_HOY


# ============================================================
# 5. LOS DOS NUMEROS SALEN DE LA TABLA
# ============================================================

def test_los_dos_numeros_salen_de_la_tabla():
    """
    Doctrina 84: no se escribe un numero nuevo. `EN_LA_VENTANA` es
    "justo por debajo del once" y `FUERA_DE_LA_VENTANA` es "justo
    por debajo de renovar".
    """

    assert EN_LA_VENTANA == PRIORITY["LINEUP_LOW"] - 1
    assert FUERA_DE_LA_VENTANA == (
        PRIORITY["MARKET_LISTING_RENEW"] - 1
    )
    assert LA_DE_HOY == PRIORITY["SPECULATION_BUY"]

    # Y lo que esos dos numeros SIGNIFICAN, ejercitado contra la
    # tabla entera y no leido de ella.
    tramites = {
        k: v
        for k, v in PRIORITY.items()
        if not k.startswith(("LINEUP", "EMERGENCY", "HARD", "ROUND"))
        and k not in ("SOLVENCY_FINALIZATION", "SOLVENCY_HIGH_ATTENTION",
                      "SOLVENCY_PREPARATION", "FRANCHISE_ACTION",
                      "FRANCHISE_WAIT", "SPECULATION_BUY", "IDLE",
                      "PUJA_BLOQUEADA", "SPECULATION_WATCH")
    }

    assert tramites, "sin tramites que comparar esto no prueba nada"

    for nombre, valor in tramites.items():
        assert EN_LA_VENTANA > valor, (
            f"dentro de la ventana la puja no le gana a {nombre} "
            f"({valor})"
        )


# ============================================================
# 6. SIN RELOJ NO SE SUBE NADA
# ============================================================

def test_sin_reloj_no_se_sube_nada():
    """
    Doctrina 103: no saber si estamos en la ventana no es estar
    dentro. Y el reloj se recibe: este modulo no lo mira.
    """

    with _Interruptor(HORA_ENV):
        visto = prioridad_de_la_puja(None)

    assert visto["prioridad"] == LA_DE_HOY, (
        f"sin reloj la puja se ha puesto en {visto['prioridad']}"
    )
    assert visto["en_la_ventana"] is None
    assert visto["activa"] is True
    assert "no sabe" in (visto["reason"] or "").lower()


# ============================================================
# 7. LA VENTANA NO SE REDEFINE AQUI
# ============================================================

def test_la_ventana_es_la_de_la_subasta():
    """
    Un segundo sitio que dijera "ventana" seria un segundo sitio
    que olvidar el dia que se mueva (doctrina 33).
    """

    import ast
    import inspect

    from src.analysis import la_hora_de_pujar

    fuente = inspect.getsource(la_hora_de_pujar)

    # SE MIRA EL CODIGO, NO LA PROSA. Contar el "135" del texto
    # ponia esto rojo por una frase de la cabecera que EXPLICA de
    # donde sale la ventana, que es justo lo que se quiere. Lo que
    # no puede haber es el numero COMO LITERAL.
    numeros = {
        nodo.value
        for nodo in ast.walk(ast.parse(fuente))
        if isinstance(nodo, ast.Constant)
        and isinstance(nodo.value, (int, float))
        and not isinstance(nodo.value, bool)
    }

    assert VENTANA_MINUTOS not in numeros, (
        f"`la_hora_de_pujar` escribe los {VENTANA_MINUTOS} "
        f"minutos por su cuenta: la ventana vive en `la_subasta`"
    )

    assert not (numeros & {60, 8100, VENTANA_MINUTOS * 60}), (
        f"`la_hora_de_pujar` hace la cuenta de la ventana por su "
        f"cuenta: {sorted(numeros)}"
    )

    assert "ventana_abierta" in fuente, (
        "no le pregunta a `la_subasta` donde esta la ventana"
    )

    # Y el borde es EL MISMO, ejercitado.
    with _Interruptor(HORA_ENV):
        borde = VENTANA_MINUTOS * 60

        assert prioridad_de_la_puja(borde)["prioridad"] == (
            EN_LA_VENTANA
        )
        assert prioridad_de_la_puja(borde + 1)["prioridad"] == (
            FUERA_DE_LA_VENTANA
        )


# ============================================================
# 8. LA FORMA NO CAMBIA CON LOS DATOS
# ============================================================

def test_la_forma_no_cambia_con_los_datos():

    casos = [None, 0, -1, 1, DENTRO, FUERA, "300", "basura", 10**9]

    for cuando in casos:
        for encendido in (False, True):

            if encendido:
                with _Interruptor(HORA_ENV):
                    visto = prioridad_de_la_puja(cuando)
            else:
                visto = prioridad_de_la_puja(cuando)

            for campo in (
                "prioridad",
                "activa",
                "en_la_ventana",
                "interruptor",
                "reason",
            ):
                assert campo in visto, (
                    f"falta `{campo}` con {cuando!r}"
                )

            assert isinstance(visto["prioridad"], int), (
                f"la prioridad salio {type(visto['prioridad'])} "
                f"con {cuando!r}"
            )

            json.dumps(visto, default=str)


# ============================================================
# 9. NO LEE EL MUNDO
# ============================================================

def test_la_hora_de_pujar_no_lee_el_mundo():

    import inspect

    from src.analysis import la_hora_de_pujar

    fuente = inspect.getsource(la_hora_de_pujar)

    for prohibido in (
        "open(",
        "Path(",
        "requests",
        "urllib",
        "datetime.now",
        "time.time",
        "json.load",
    ):
        assert prohibido not in fuente, (
            f"`la_hora_de_pujar` usa `{prohibido}`: lo que decide "
            f"el orden de la vuelta no puede leer el mundo"
        )


# ============================================================
# EL CORREDOR
# ============================================================

TESTS = [
    test_en_la_ventana_la_puja_no_pierde_contra_un_tramite,
    test_fuera_de_la_ventana_la_puja_pierde_contra_renovar,
    test_el_once_gana_siempre_dentro_y_fuera,
    test_apagado_la_prioridad_es_la_de_siempre,
    test_los_dos_numeros_salen_de_la_tabla,
    test_sin_reloj_no_se_sube_nada,
    test_la_ventana_es_la_de_la_subasta,
    test_la_forma_no_cambia_con_los_datos,
    test_la_hora_de_pujar_no_lee_el_mundo,
]


def main() -> None:

    print()
    print("=" * 60)
    print("LA HORA DE PUJAR V1")
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
