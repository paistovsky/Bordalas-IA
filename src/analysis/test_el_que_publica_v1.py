"""
El que publica: la cola manda, y el once no se publica.

LO QUE PASA HOY (22/09/2026)

    Dos motores dicen a quien soltar y ninguno publica:
    `sale_intent` imprime "OBSERVACION: no se publica ni se vende
    nada" y `sale_order` ordena la cola entera para la pantalla.

    Quien SI publica es `LIST_FOR_LIQUIDITY`, del motor de
    solvencia, y publica `to_list[0]` — la plantilla en el orden
    en que la devuelve Biwenger, sin criterio ninguno.

    Medido sobre la foto de plantilla del 19/09 (n=19 fichas):
    `to_list[0]` es JUTGLA, que esta en el once. Con el
    interruptor puesto es MAFFEO, el primero de la cola de venta,
    y los CUATRO del once que habia en la cola salen fuera.

LO QUE SE PROTEGE

    1. QUE UN JUGADOR DEL ONCE NO ENTRE EN LA COLA DE PUBLICAR.
       Es la guardia que pidio el encargo.
    2. Que el resto SI entre, y en el orden de la cola de venta
       — sin eso, el corte seria un apagado con otro nombre.
    3. Que apagado no cambie ni una publicacion.
    4. Que al que ya esta publicado no se le republique.
    5. Que sin cola de venta no se invente un orden.
    6. Que el que la cola no conoce vaya DETRAS y no se pierda.
    7. Que `to_list` salga ordenado de `build_liquidity_state`.
    8. Que la forma no cambie con los datos.
    9. Que el modulo no lea el mundo.

ESTAS GUARDIAS NO LEEN EL MUNDO

    Ni `data/`, ni red, ni reloj: todo se pasa. La unica que toca
    el entorno es la del interruptor —que ES una variable de
    entorno— y lo deja como estaba.

COMO SE USA

    python -m src.analysis.test_el_que_publica_v1
"""

from __future__ import annotations

import os


# EL ENTORNO NO DECIDE ESTA GUARDIA (doctrina 104)
#
#     Un caso incompleto se cae en cuanto alguien enciende un
#     interruptor que mire un campo que el caso no trae. Aqui los
#     casos se construyen COMPLETOS —con `in_lineup` y con
#     precio— y ademas se quita el interruptor propio, que cada
#     prueba pone y quita ella.
os.environ.pop("BORDALAS_PUBLICAR_LA_COLA", None)

import json                                         # noqa: E402

from src.analysis.el_que_publica import (            # noqa: E402
    ENV as COLA_ENV,
    cola_de_publicacion,
    es_del_once,
    orden_de_la_cola,
    ordenar_para_publicar,
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


def _fila(id_, nombre, once=False, precio=1_000_000, orden=1) -> dict:
    """Una fila de la cola de venta, con lo que la cola publica."""

    return {
        "id": id_,
        "name": nombre,
        "order": orden,
        "price": precio,
        "in_lineup": once,
        "plays": True,
        "position": 3,
        "reason": "el motivo de su puesto",
    }


def _cola(*filas) -> dict:
    """La forma que devuelve `build_sale_order`."""

    return {
        "available": True,
        "reason": None,
        "queue": [
            {**f, "order": i + 1} for i, f in enumerate(filas)
        ],
        "excluded": [],
        "blocked": [],
        "queue_size": len(filas),
    }


# El caso de la foto del 20/09: el lastre delante y DOS
# titulares al final de la cola de venta.
def _caso_de_la_foto() -> dict:
    return _cola(
        _fila(1, "Jonny", once=False, precio=2_350_000),
        _fila(2, "Iturbe", once=False, precio=150_000),
        _fila(3, "Alvaro Carreras", once=False, precio=1_370_000),
        _fila(4, "Pablo Duran", once=False, precio=420_000),
        _fila(5, "Exposito", once=True, precio=5_330_000),
        _fila(6, "Ruben Garcia", once=True, precio=2_510_000),
    )


# ============================================================
# 1. LA QUE PIDIO EL ENCARGO
# ============================================================

def test_el_que_publica_no_publica_titulares():
    """
    Con el interruptor puesto, un jugador del once NO entra en la
    cola de publicacion.

    MUERDE SI EN EL CASO NO HAY NINGUN TITULAR: sin un titular en
    la cola no habria nada que frenar, y esta guardia pasaria con
    las manos vacias (doctrina 24). Y muerde tambien si no queda
    nadie que publicar, porque entonces no distinguiria el corte
    de un apagado.
    """

    cola = _caso_de_la_foto()

    filas = cola["queue"]

    titulares = [f for f in filas if es_del_once(f)]

    assert titulares, (
        "el caso no trae ningun jugador del once en la cola de "
        "venta: esta guardia no estaria midiendo nada"
    )

    resto = [f for f in filas if not es_del_once(f)]

    assert resto, (
        "el caso no trae a nadie fuera del once: sin eso, que no "
        "se publique no prueba que el corte distinga"
    )

    with _Interruptor(COLA_ENV):
        visto = cola_de_publicacion(cola)

    assert visto["available"] is True, visto["reason"]

    publicados = {f["id"] for f in visto["cola"]}

    for titular in titulares:
        assert titular["id"] not in publicados, (
            f"{titular['name']} esta en el once y ha entrado en "
            f"la cola de publicacion"
        )

    assert publicados == {f["id"] for f in resto}, (
        f"se publicaria {publicados} y fuera del once estan "
        f"{[f['id'] for f in resto]}"
    )

    frenados = [
        f
        for f in visto["frenados"]
        if f["motivo"] == "EL_ONCE_NO_SE_PUBLICA"
    ]

    assert len(frenados) == len(titulares), (
        f"frenados {len(frenados)} y titulares {len(titulares)}"
    )

    for f in frenados:
        assert "once" in (f["reason"] or "").lower(), (
            f"el motivo no nombra el once: {f['reason']}"
        )


# ============================================================
# 2. Y EL ORDEN ES EL DE LA COLA, NO OTRO
# ============================================================

def test_la_cola_se_publica_en_su_orden():
    """
    El encargo dice "en su orden". Si el corte reordenara, seria
    un criterio nuevo y no se ha pedido ninguno.
    """

    cola = _caso_de_la_foto()

    with _Interruptor(COLA_ENV):
        visto = cola_de_publicacion(cola)

    esperado = [
        f["name"] for f in cola["queue"] if not es_del_once(f)
    ]

    assert [f["name"] for f in visto["cola"]] == esperado, (
        f"el orden ha cambiado: {[f['name'] for f in visto['cola']]} "
        f"contra {esperado}"
    )

    puestos = orden_de_la_cola(cola)

    assert puestos == {1: 0, 2: 1, 3: 2, 4: 3}, puestos


# ============================================================
# 3. APAGADO NO CAMBIA NADA
# ============================================================

def test_apagado_se_publica_en_el_orden_de_siempre():
    """
    Un interruptor apagado que cambia el orden no esta apagado.
    """

    assert os.environ.get(COLA_ENV) is None

    to_list = [
        {"id": 9, "name": "Jutgla", "in_lineup": True},
        {"id": 8, "name": "Maffeo", "in_lineup": False},
    ]

    visto = ordenar_para_publicar(to_list, _caso_de_la_foto())

    assert visto["activa"] is False
    assert visto["to_list"] == to_list, (
        "apagado, `to_list` tiene que salir tal cual"
    )
    assert visto["frenados"] == []

    # Y con el puesto, el titular se cae: si no, la de arriba no
    # probaria que el interruptor hace algo.
    with _Interruptor(COLA_ENV):
        encendido = ordenar_para_publicar(
            to_list, _caso_de_la_foto()
        )

    assert [x["name"] for x in encendido["to_list"]] == ["Maffeo"], (
        f"con el interruptor puesto Jutgla tenia que caerse: "
        f"{[x['name'] for x in encendido['to_list']]}"
    )


# ============================================================
# 4. AL QUE YA ESTA PUBLICADO NO SE LE REPUBLICA
# ============================================================

def test_al_publicado_no_se_le_republica():
    """
    Republicar gasta la escritura de la vuelta en nada.
    """

    cola = _caso_de_la_foto()

    with _Interruptor(COLA_ENV):
        visto = cola_de_publicacion(cola, publicados=[1, 2])

    assert visto["sabemos_quien_esta_publicado"] is True

    assert [f["id"] for f in visto["cola"]] == [3, 4], (
        f"salen {[f['id'] for f in visto['cola']]}"
    )

    ya = [
        f
        for f in visto["frenados"]
        if f["motivo"] == "YA_ESTA_PUBLICADO"
    ]

    assert len(ya) == 2

    # Y sin preguntar, NO se filtra ni se finge que no hay nadie.
    with _Interruptor(COLA_ENV):
        a_ciegas = cola_de_publicacion(cola)

    assert a_ciegas["sabemos_quien_esta_publicado"] is False
    assert len(a_ciegas["cola"]) == 4, (
        "sin la lista de publicados no se puede filtrar por ella"
    )
    assert "no se ha preguntado" in (a_ciegas["reason"] or "").lower()


# ============================================================
# 5. SIN COLA NO SE INVENTA UN ORDEN
# ============================================================

def test_sin_cola_de_venta_no_se_inventa_un_orden():
    """
    Doctrina 24: no saber en que orden publicar no es publicar en
    cualquiera. Se deja el de siempre y se dice.
    """

    to_list = [
        {"id": 8, "name": "Maffeo", "in_lineup": False},
        {"id": 7, "name": "Pablo Duran", "in_lineup": False},
    ]

    for rota in (
        None,
        {},
        {"available": False, "reason": "reventó", "queue": []},
        {"available": True, "queue": []},
    ):
        with _Interruptor(COLA_ENV):
            visto = ordenar_para_publicar(to_list, rota)

        assert visto["to_list"] == to_list, (
            f"con la cola {rota} se ha cambiado el orden"
        )
        assert visto["available"] is False
        assert visto["activa"] is True
        assert "no hay cola" in (visto["reason"] or "").lower()


# ============================================================
# 6. EL QUE LA COLA NO CONOCE VA DETRAS, NO SE PIERDE
# ============================================================

def test_el_desconocido_va_detras_y_no_se_pierde():
    """
    Un jugador que no esta en la cola de venta —recien comprado,
    sin escalon— no se publica el primero, pero tampoco
    desaparece: no saber su puesto no es motivo para no publicarlo
    nunca (doctrina 103).
    """

    to_list = [
        {"id": 99, "name": "Recien comprado", "in_lineup": False},
        {"id": 4, "name": "Pablo Duran", "in_lineup": False},
        {"id": 1, "name": "Jonny", "in_lineup": False},
    ]

    with _Interruptor(COLA_ENV):
        visto = ordenar_para_publicar(to_list, _caso_de_la_foto())

    assert [x["name"] for x in visto["to_list"]] == [
        "Jonny",
        "Pablo Duran",
        "Recien comprado",
    ], [x["name"] for x in visto["to_list"]]

    assert [x["name"] for x in visto["sin_puesto"]] == [
        "Recien comprado"
    ]


# ============================================================
# 7. Y SALE ORDENADO DEL MOTOR DE LIQUIDEZ
# ============================================================

def test_el_motor_de_liquidez_publica_el_orden():
    """
    El corte no sirve de nada si `to_list` no sale ordenado de
    donde lo lee el orquestador. Se ejercita el motor, no se lee
    el mapa contra si mismo.
    """

    from src.analysis.liquidity_manager import (
        _ordenar_la_publicacion,
    )

    to_list = [
        {"id": 9, "name": "Jutgla", "in_lineup": True},
        {"id": 1, "name": "Jonny", "in_lineup": False},
        {"id": 4, "name": "Pablo Duran", "in_lineup": False},
    ]

    del_once = [x for x in to_list if es_del_once(x)]

    assert del_once, (
        "el caso no trae ningun titular en `to_list`: no probaria "
        "que el motor de liquidez aplica el corte"
    )

    # Apagado: tal cual, y SIN calcular la cola.
    apagado = _ordenar_la_publicacion(to_list, {}, [])

    assert apagado["to_list"] == to_list
    assert apagado["activa"] is False

    # Encendido, con la cola inyectada por la puerta.
    from src.analysis import liquidity_manager

    original = liquidity_manager._cola_de_venta

    try:
        liquidity_manager._cola_de_venta = (
            lambda snapshot, roster: _caso_de_la_foto()
        )

        with _Interruptor(COLA_ENV):
            visto = _ordenar_la_publicacion(to_list, {}, [])

    finally:
        liquidity_manager._cola_de_venta = original

    assert [x["name"] for x in visto["to_list"]] == [
        "Jonny",
        "Pablo Duran",
    ], [x["name"] for x in visto["to_list"]]

    assert [f["name"] for f in visto["frenados"]] == ["Jutgla"]


# ============================================================
# 8. LA FORMA NO CAMBIA CON LOS DATOS
# ============================================================

def test_la_forma_no_cambia_con_los_datos():

    casos = [
        None,
        {},
        {"queue": None},
        {"available": True, "queue": ["basura", 7, None]},
        _caso_de_la_foto(),
    ]

    for cola in casos:

        for encendido in (False, True):

            if encendido:
                with _Interruptor(COLA_ENV):
                    visto = cola_de_publicacion(cola)
                    orden = ordenar_para_publicar(None, cola)
            else:
                visto = cola_de_publicacion(cola)
                orden = ordenar_para_publicar(None, cola)

            for campo in (
                "available",
                "activa",
                "cola",
                "frenados",
                "reason",
            ):
                assert campo in visto, f"falta `{campo}` con {cola}"

            assert isinstance(visto["cola"], list)
            assert isinstance(visto["frenados"], list)
            assert isinstance(orden["to_list"], list)

            json.dumps(visto, default=str)
            json.dumps(orden, default=str)


# ============================================================
# 9. NO LEE EL MUNDO
# ============================================================

def test_el_que_publica_no_lee_el_mundo():

    import inspect

    from src.analysis import el_que_publica

    fuente = inspect.getsource(el_que_publica)

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
            f"`el_que_publica` usa `{prohibido}`: lo que decide a "
            f"quien se publica no puede leer el mundo"
        )


# ============================================================
# EL CORREDOR
# ============================================================

TESTS = [
    test_el_que_publica_no_publica_titulares,
    test_la_cola_se_publica_en_su_orden,
    test_apagado_se_publica_en_el_orden_de_siempre,
    test_al_publicado_no_se_le_republica,
    test_sin_cola_de_venta_no_se_inventa_un_orden,
    test_el_desconocido_va_detras_y_no_se_pierde,
    test_el_motor_de_liquidez_publica_el_orden,
    test_la_forma_no_cambia_con_los_datos,
    test_el_que_publica_no_lee_el_mundo,
]


def main() -> None:

    print()
    print("=" * 60)
    print("EL QUE PUBLICA V1")
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
