"""
La salida del viaje: la primera ruta que vende sola.

POR QUE ESTA GUARDIA ES LA MAS SERIA DE LA CASA

    Renovar solo lista, y listar se deshace. Esto ACEPTA
    OFERTAS, y aceptar una oferta es irreversible: el jugador se
    va y no vuelve.

    Por eso cada prohibicion tiene aqui su propia prueba con
    nombre, y hay una que le pasa datos TRUCADOS para intentar
    que venda a quien no debe.

LAS CINCO QUE NO PUEDE HACER NUNCA

    1. Tocar a un jugador que no este marcado VIAJE.
    2. Vender a alguien que haya entrado en el once.
    3. Dejarnos con un solo portero.
    4. Vender por debajo de coste sin corte de perdidas
       declarado.
    5. Mas de cuatro ventas por vuelta.

Y ADEMAS

    · Que el suelo sea el medido y no otro.
    · Que un viaje caduque, y que caducar NO fuerce una venta a
      perdidas.
    · Que el ejecutor no sepa hacer nada que no sea cobrar.

REGLA 24: si no hay casos que mirar, falla.

ESTAS GUARDIAS NO LEEN EL MUNDO: ni `data/`, ni red, ni reloj.

COMO SE USA

    python -m src.analysis.test_la_salida_del_viaje_v1
"""

from __future__ import annotations

import tempfile

from pathlib import Path

from src.actions.salida_executor import cobrar
from src.analysis.salida_del_viaje import (
    RESETS_QUE_DURA_UN_VIAJE,
    SUELO_DEL_VIAJE,
    VENTAS_POR_VUELTA,
    precio_de_salida,
    que_cobrar,
)


COSTE = 1_000_000

# Con el suelo en el 1 %, esta oferta pasa y la de abajo no.
BUENA = 1_050_000

JUSTA = 1_005_000


def _viaje(nombre="Viajero", pid=1, coste=COSTE, **extra):
    fila = {
        "player_id": pid,
        "name": nombre,
        "cost": coste,
        "position": 4,
        "state": "ABIERTO",
    }
    fila.update(extra)
    return fila


def _oferta(pid=1, amount=BUENA, offer_id=None):
    return {
        "player_id": pid,
        "amount": amount,
        "offer_id": offer_id if offer_id is not None else 900 + pid,
    }


class ClienteEspia:
    """Apunta TODO lo que se le llama y revienta con lo prohibido."""

    def __init__(self):
        self.llamadas = []

    def accept_offer(self, **kwargs):
        self.llamadas.append(("accept_offer", kwargs))
        return {"sent": bool(kwargs.get("execute")), "success": True}

    def list_player_for_sale(self, **kwargs):
        self.llamadas.append(("list_player_for_sale", kwargs))
        raise AssertionError("la salida ha listado a alguien")

    def place_bid(self, **kwargs):
        self.llamadas.append(("place_bid", kwargs))
        raise AssertionError("la salida ha pujado")

    def reject_offer(self, **kwargs):
        self.llamadas.append(("reject_offer", kwargs))
        raise AssertionError("la salida ha rechazado una oferta")

    def counter_offer(self, **kwargs):
        self.llamadas.append(("counter_offer", kwargs))
        raise AssertionError("la salida ha contraofertado")

    def cancel_bid(self, **kwargs):
        self.llamadas.append(("cancel_bid", kwargs))
        raise AssertionError("la salida ha cancelado una puja")

    def save_lineup(self, **kwargs):
        self.llamadas.append(("save_lineup", kwargs))
        raise AssertionError("la salida ha tocado el once")


# ============================================================
# REGLA 24
# ============================================================

def test_hay_casos_que_mirar():

    plan = que_cobrar([_viaje()], [_oferta()])

    assert plan["count"] == 1, (
        "el caso base no vende: todas las guardias de abajo "
        "pasarian sin mirar nada"
    )

    assert SUELO_DEL_VIAJE == 0.01, (
        f"el suelo ya no es el 1 % medido: {SUELO_DEL_VIAJE}"
    )

    assert VENTAS_POR_VUELTA == 4
    assert RESETS_QUE_DURA_UN_VIAJE == 4


# ============================================================
# 1. SIN LA MARCA, INTOCABLE
# ============================================================

def test_no_toca_a_quien_no_esta_marcado_viaje():
    """
    LA GUARDIA QUE MAS IMPORTA.

    Se le pasa todo trucado -una oferta jugosa, el jugador fuera
    del once, sin problemas de portero, muy por encima del
    suelo- y lo unico que falta es LA MARCA.

    No puede venderlo. La marca es el permiso, y no hay otro.
    """

    goloso = _oferta(pid=77, amount=99_000_000)

    # Sin ningun viaje: la lista de marcados esta vacia.
    plan = que_cobrar([], [goloso])

    assert plan["sell"] == [], (
        "ha vendido a alguien sin marca VIAJE"
    )

    # Con OTRO viaje abierto, por si colara por estar la lista
    # llena: sigue sin poder tocar al 77.
    plan = que_cobrar(
        [_viaje(pid=1)],
        [goloso, _oferta(pid=1)],
    )

    vendidos = {v["player_id"] for v in plan["sell"]}

    assert 77 not in vendidos, (
        f"ha vendido al 77, que no esta marcado: {vendidos}"
    )

    # Y con la marca en un estado que NO es ABIERTO tampoco.
    for estado in ("CERRADO", "CADUCADO", "", None, "abierto "):

        plan = que_cobrar(
            [_viaje(pid=77, state=estado)], [goloso]
        )

        assert plan["sell"] == [], (
            f"vende con state={estado!r}"
        )


def test_el_ejecutor_no_sabe_hacer_otra_cosa():
    """
    Con filas manipuladas: `list`, `bid`, `lineup`, lo que sea.
    La unica llamada que puede salir es `accept_offer`.
    """

    espia = ClienteEspia()

    manipuladas = [
        {
            "player_id": 1,
            "name": "Trampa",
            "offer_id": 901,
            "cost": COSTE,
            "amount": BUENA,
            # veneno
            "action": "LIST_FOR_SALE",
            "price": 999,
            "lineup": [1, 2, 3],
            "execute_sale": True,
            "bid": 500,
        }
    ]

    with tempfile.TemporaryDirectory() as carpeta:

        cobrar(
            manipuladas,
            escritor=espia,
            en_vivo=True,
            ruta_del_libro=Path(carpeta) / "l.jsonl",
        )

    assert espia.llamadas, "no se ha llamado a nada"

    metodos = {n for n, _ in espia.llamadas}

    assert metodos == {"accept_offer"}, (
        f"la salida ha llamado a {metodos}"
    )

    for _, kwargs in espia.llamadas:
        assert set(kwargs) <= {"offer_id", "execute"}, (
            f"a accept_offer le llegan argumentos de mas: "
            f"{sorted(kwargs)}"
        )


# ============================================================
# 2. EL ONCE NO SE TOCA
# ============================================================

def test_no_vende_a_quien_entro_en_el_once():

    plan = que_cobrar(
        [_viaje("Yeray", pid=1)],
        [_oferta(pid=1)],
        titulares=["Yeray"],
    )

    assert plan["sell"] == [], (
        "ha vendido a un titular"
    )

    motivos = [s["reason"] for s in plan["skipped"]]

    assert any("once" in m for m in motivos), (
        f"no dice que es por el once: {motivos}"
    )

    # Y la contraria: si NO esta en el once, si se vende. Sin
    # esto, un fallo que vaciara la venta pasaria igual.
    assert que_cobrar(
        [_viaje("Yeray", pid=1)],
        [_oferta(pid=1)],
        titulares=["Otro"],
    )["count"] == 1


# ============================================================
# 3. NUNCA CON UN SOLO PORTERO
# ============================================================

def test_nunca_deja_un_solo_portero():

    portero = _viaje("Dituro", pid=1, position=1)

    plan = que_cobrar(
        [portero], [_oferta(pid=1)], porteros_en_plantilla=1
    )

    assert plan["sell"] == [], (
        "ha vendido al unico portero"
    )

    assert any(
        "portero" in s["reason"] for s in plan["skipped"]
    )

    # Con dos porteros, el segundo si se puede vender.
    assert que_cobrar(
        [portero], [_oferta(pid=1)], porteros_en_plantilla=2
    )["count"] == 1

    # Y con dos VIAJES de portero y dos porteros en plantilla,
    # solo sale UNO: al vender el primero queda uno.
    dos = [
        _viaje("Portero A", pid=1, position=1),
        _viaje("Portero B", pid=2, position=1),
    ]

    plan = que_cobrar(
        dos,
        [_oferta(pid=1), _oferta(pid=2)],
        porteros_en_plantilla=2,
    )

    assert plan["count"] == 1, (
        f"vende {plan['count']} porteros y nos deja sin ninguno"
    )


# ============================================================
# 4. NUNCA POR DEBAJO DE COSTE
# ============================================================

def test_no_vende_por_debajo_de_coste():

    barata = _oferta(pid=1, amount=COSTE - 1)

    plan = que_cobrar([_viaje()], [barata])

    assert plan["sell"] == [], (
        "ha vendido por debajo de lo que costo"
    )

    assert any(
        "por debajo" in s["reason"] for s in plan["skipped"]
    )

    # SALVO corte de perdidas EXPLICITO. Y entonces se publica
    # que lo es.
    con_corte = que_cobrar(
        [_viaje()], [barata], corte_de_perdidas=True
    )

    assert con_corte["count"] == 1
    assert con_corte["sell"][0]["loss_cut"] is True, (
        "un corte de perdidas no queda marcado como tal"
    )


def test_el_suelo_es_el_medido_y_muerde():
    """
    coste + 1 %. Ni el 0 % -que cerraria por migajas- ni la
    mediana del 2,91 %, que cuesta un 20 % del rendimiento por
    dia esperando.
    """

    assert precio_de_salida(COSTE) == 1_010_000

    # Justo por debajo del suelo pero POR ENCIMA de coste: se
    # aguanta.
    plan = que_cobrar([_viaje()], [_oferta(amount=JUSTA)])

    assert plan["sell"] == [], (
        "cobra por debajo del suelo"
    )

    assert any(
        "suelo" in s["reason"] for s in plan["skipped"]
    )

    # Justo en el suelo: se cobra.
    assert que_cobrar(
        [_viaje()], [_oferta(amount=1_010_000)]
    )["count"] == 1


# ============================================================
# 5. EL TOPE POR VUELTA
# ============================================================

def test_no_mas_de_cuatro_ventas_por_vuelta():

    viajes = [_viaje(f"V{i}", pid=i) for i in range(1, 10)]

    ofertas = [
        _oferta(pid=i, amount=COSTE + 10_000 * i)
        for i in range(1, 10)
    ]

    plan = que_cobrar(viajes, ofertas)

    assert plan["count"] == VENTAS_POR_VUELTA, (
        f"cierra {plan['count']} viajes con el tope en "
        f"{VENTAS_POR_VUELTA}"
    )

    assert plan["dropped_by_cap"] == 9 - VENTAS_POR_VUELTA

    # Y corta por el que MENOS deja, no al azar.
    rindes = [v["yield_percent"] for v in plan["sell"]]

    assert rindes == sorted(rindes, reverse=True), (
        f"el recorte no deja los mas rentables: {rindes}"
    )

    # El ejecutor tambien corta, aunque le mientan.
    espia = ClienteEspia()

    with tempfile.TemporaryDirectory() as carpeta:

        resultado = cobrar(
            [
                {
                    "player_id": i,
                    "name": f"V{i}",
                    "offer_id": 900 + i,
                    "cost": COSTE,
                    "amount": BUENA,
                }
                for i in range(1, 10)
            ],
            escritor=espia,
            en_vivo=True,
            ruta_del_libro=Path(carpeta) / "l.jsonl",
        )

    assert len(espia.llamadas) == VENTAS_POR_VUELTA, (
        f"el ejecutor ha cobrado {len(espia.llamadas)} veces"
    )

    assert resultado["dropped_by_cap"] == 9 - VENTAS_POR_VUELTA


# ============================================================
# EL PLAZO
# ============================================================

def test_un_viaje_caduca_y_caducar_no_fuerza_una_venta():
    """
    Un VIAJE no puede quedarse abierto indefinido. Pero caducar
    NO es motivo para regalar dinero: deja de ser VIAJE y pasa
    al motor de siempre.
    """

    viaje = _viaje(pid=1)

    plan = que_cobrar(
        [viaje],
        [_oferta(pid=1, amount=COSTE - 500_000)],
        resets_pasados_por_viaje={1: RESETS_QUE_DURA_UN_VIAJE},
    )

    assert plan["sell"] == [], (
        "al caducar ha vendido a perdidas"
    )

    assert len(plan["expired"]) == 1, (
        "no ha caducado el viaje"
    )

    assert "perdidas" in plan["expired"][0]["reason"]

    # Un reset antes, sigue vivo.
    vivo = que_cobrar(
        [viaje],
        [_oferta(pid=1)],
        resets_pasados_por_viaje={
            1: RESETS_QUE_DURA_UN_VIAJE - 1
        },
    )

    assert vivo["count"] == 1, (
        "caduca antes de tiempo"
    )


# ============================================================
# EN SECO, FORMA Y BLINDAJE
# ============================================================

def test_en_seco_no_escribe_nada():

    espia = ClienteEspia()

    with tempfile.TemporaryDirectory() as carpeta:

        resultado = cobrar(
            [
                {
                    "player_id": 1,
                    "name": "Uno",
                    "offer_id": 901,
                    "cost": COSTE,
                    "amount": BUENA,
                }
            ],
            escritor=espia,
            ruta_del_libro=Path(carpeta) / "l.jsonl",
        )

    assert resultado["executed"] is False

    assert espia.llamadas[0][1]["execute"] is False, (
        "en seco esta mandando execute=True"
    )


def test_cada_salida_va_al_libro():

    import json

    espia = ClienteEspia()

    with tempfile.TemporaryDirectory() as carpeta:

        ruta = Path(carpeta) / "l.jsonl"

        cobrar(
            [
                {
                    "player_id": 5771,
                    "name": "Yeray",
                    "offer_id": 901,
                    "cost": COSTE,
                    "amount": BUENA,
                    "profit": BUENA - COSTE,
                    "yield_percent": 5.0,
                }
            ],
            escritor=espia,
            en_vivo=True,
            ruta_del_libro=ruta,
        )

        fila = json.loads(ruta.read_text(encoding="utf-8").strip())

    assert fila["player_id"] == 5771
    assert fila["cost"] == COSTE
    assert fila["amount"] == BUENA
    assert fila["at"]


def test_la_forma_no_cambia_con_los_datos():

    con = que_cobrar([_viaje()], [_oferta()])
    sin = que_cobrar(None, None)

    assert set(con) == set(sin), (
        f"la forma cambia: {set(con) ^ set(sin)}"
    )


def test_nada_de_esto_lanza():

    for basura in (None, "no", {}, [], 0):

        assert isinstance(que_cobrar(basura, basura), dict)
        assert isinstance(precio_de_salida(basura), int)


TESTS = [
    test_hay_casos_que_mirar,
    test_no_toca_a_quien_no_esta_marcado_viaje,
    test_el_ejecutor_no_sabe_hacer_otra_cosa,
    test_no_vende_a_quien_entro_en_el_once,
    test_nunca_deja_un_solo_portero,
    test_no_vende_por_debajo_de_coste,
    test_el_suelo_es_el_medido_y_muerde,
    test_no_mas_de_cuatro_ventas_por_vuelta,
    test_un_viaje_caduca_y_caducar_no_fuerza_una_venta,
    test_en_seco_no_escribe_nada,
    test_cada_salida_va_al_libro,
    test_la_forma_no_cambia_con_los_datos,
    test_nada_de_esto_lanza,
]


def main() -> None:

    print()
    print("=" * 60)
    print("LA SALIDA DEL VIAJE V1")
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
