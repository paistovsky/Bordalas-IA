"""
La lista de la noche se calcula y NO escribe. Ni un euro.

QUE VIGILA (22/09/2026)

    El dueño quiere ver por quien y cuanto pujaria Pepe con la
    moneda de la liga puesta ANTES de encenderla, porque la
    ventana del reset es a las 04:45 y a esa hora esta dormido.

    Eso solo vale si la sombra es exactamente eso: una sombra.

        1. Que se calcule con candidatos de verdad. Una lista
           vacia no prueba nada: pasaria igual con el modulo
           roto (doctrina 24).

        2. Que NO ocurra ni una escritura contra Biwenger.

        3. Que la moneda siga APAGADA despues de mirarla. Este
           es el riesgo de verdad: encender el interruptor para
           poder calcular la sombra y dejarlo encendido seria
           poner produccion en otro estado sin que nadie lo
           pidiera. Doctrina 104.

        4. Que la cuenta de la sombra sea la de verdad: la misma
           que da `xi_upgrade_value` corrido CON el interruptor
           puesto. Si algun dia la formula deja de ser lineal en
           la tarifa, esto se pone rojo.

NO MIRA EL MUNDO

    Ni disco, ni red, ni reloj, ni `data/`. Las fichas son de
    mentira y estan aqui escritas. El unico `os.environ` que
    toca es el suyo, y lo deja como estaba.
"""

from __future__ import annotations

import ast
import os
import sys

from pathlib import Path


RAIZ = Path(__file__).resolve().parents[2]

if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))


# LA MONEDA, QUITADA ANTES DE IMPORTAR NADA (doctrina 104)
#
#     Esta guardia comprueba lo que pasa con el interruptor
#     APAGADO. Si el que la corre lo trae puesto, la comprobacion
#     seria otra y no lo diria.
os.environ.pop("BORDALAS_LA_MONEDA_DE_LA_LIGA", None)


from src.analysis.la_lista_de_la_noche import (               # noqa: E402
    MONEDA_DE_LA_LIGA,
    con_la_moneda,
    la_fila,
    la_lista,
    la_via_que_ganaria,
    ordenar,
)
from src.analysis.la_moneda_del_fichaje import (              # noqa: E402
    ENV as ENV_MONEDA,
    activa as moneda_activa,
)
from src.analysis.player_value_engine import (                # noqa: E402
    xi_upgrade_value,
)


EL_MODULO = RAIZ / "src" / "analysis" / "la_lista_de_la_noche.py"


class _Interruptor:
    """Pone un interruptor y lo deja como estaba. Nunca falla."""

    def __init__(self, nombre: str, valor: str = "1") -> None:
        self.nombre = nombre
        self.valor = valor
        self.antes = None

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


# ============================================================
# EL CASO: TRES CANDIDATOS DE VERDAD
# ============================================================
#
#     La forma es la que publica `acquisition_valuation`: las
#     cinco vias, cada una con su `value`, y las dos del que se
#     queda con `rate_per_point` y `recovered_value`, que es lo
#     que hace falta para despejar la tarifa.


def _ficha(id_, nombre, posicion, precio, techo_comerciante, techo_queda):
    return {
        "id": id_,
        "name": nombre,
        "position": posicion,
        "market_price": precio,
        "los_dos_techos": {
            "available": True,
            "comerciante": {
                "available": True,
                "techo": techo_comerciante,
            },
            "el_que_se_queda": {
                "available": True,
                "techo": techo_queda,
            },
        },
    }


def _valoracion_de_fichaje(valor, tarifa, recuperado, delta, sale):
    return {
        "value": valor,
        "route": "COMPUTER_RESALE",
        "intent": "SPECULATION",
        "as_xi": {
            "value": valor,
            "route": "XI_UPGRADE",
            "intent": "XI_UPGRADE",
            "rate_per_point": tarifa,
            "recovered_value": recuperado,
            "points_delta": delta,
            "replaces_starter": True,
            "replaces": {"id": 900, "name": sale},
        },
        "as_roster_fill": None,
        "as_speculation": {
            "value": int(valor * 0.5),
            "route": "SPECULATION",
            "intent": "SPECULATION",
        },
        "as_computer_resale": {
            "value": int(valor * 0.9),
            "route": "COMPUTER_RESALE",
            "intent": "SPECULATION",
        },
        "as_hold": None,
    }


# Tres, con pujas distintas a proposito: sin eso no se puede
# comprobar el orden.
EL_CASO = [
    (
        _ficha(11, "El Caro", 4, 9_000_000, 9_120_000, 9_400_000),
        _valoracion_de_fichaje(
            valor=8_000_000, tarifa=20_000, recuperado=1_000_000,
            delta=140, sale="Un Suplente",
        ),
        {"bid": 9_100_000, "decision": "BID", "reason": "Pasa el liston."},
    ),
    (
        _ficha(12, "El Mediano", 3, 4_000_000, 4_050_000, 4_300_000),
        _valoracion_de_fichaje(
            valor=3_600_000, tarifa=20_000, recuperado=0,
            delta=90, sale="Otro Suplente",
        ),
        {"bid": 4_020_000, "decision": "BID", "reason": "Pasa el liston."},
    ),
    (
        _ficha(13, "El Barato", 2, 1_500_000, 1_520_000, 1_600_000),
        _valoracion_de_fichaje(
            valor=1_400_000, tarifa=20_000, recuperado=0,
            delta=40, sale="Un Tercero",
        ),
        {"bid": 1_510_000, "decision": "BID", "reason": "Pasa el liston."},
    ),
]


def _la_lista_del_caso() -> dict:
    return la_lista(
        [la_fila(ficha, valoracion, puja) for ficha, valoracion, puja in EL_CASO]
    )


def test_la_sombra_de_la_moneda_no_escribe() -> None:
    """
    Con la moneda APAGADA, la lista se calcula entera y no
    ocurre ni una escritura contra Biwenger.
    """

    # LA MONEDA, APAGADA. Si no, esto mediria otra cosa.
    assert not moneda_activa(), (
        f"{ENV_MONEDA} esta puesto: esta guardia comprueba la "
        f"sombra, que es lo que pasa con el interruptor QUITADO"
    )

    # ESCRIBIR, PROHIBIDO MIENTRAS SE CALCULA.
    #
    #     No se confia en leer el codigo: se le quitan las manos
    #     al cliente de escritura y se corre. Si alguna ruta de
    #     la sombra llamase, reventaria aqui con su nombre.
    from src.biwenger.write_client import BiwengerWriteClient

    escrituras = []

    def _prohibido(nombre):
        def _no(*args, **kwargs):
            escrituras.append(nombre)
            raise AssertionError(
                f"la sombra ha llamado a {nombre}: esto calcula, "
                f"no puja"
            )

        return _no

    LAS_QUE_ESCRIBEN = (
        "place_bid",
        "counter_offer",
        "cancel_bid",
        "accept_offer",
        "reject_offer",
        "list_player_for_sale",
        "save_lineup",
    )

    originales = {}

    try:
        for nombre in LAS_QUE_ESCRIBEN:
            originales[nombre] = getattr(BiwengerWriteClient, nombre)
            setattr(BiwengerWriteClient, nombre, _prohibido(nombre))

        lista = _la_lista_del_caso()

    finally:
        for nombre, funcion in originales.items():
            setattr(BiwengerWriteClient, nombre, funcion)

    assert not escrituras, escrituras

    # EL CASO TIENE QUE TENER CANDIDATOS (doctrina 24).
    #
    #     Cero nombres es lo que devuelve un modulo roto. Sin
    #     esta linea, la guardia daria verde probando nada.
    assert lista["n"] == len(EL_CASO), (
        f"el caso tiene {len(EL_CASO)} candidatos y la lista saco "
        f"{lista['n']}: sin candidatos esta guardia no prueba nada"
    )

    assert lista["mirados"] == len(EL_CASO), lista

    # Y LOS OCHO DATOS QUE PIDIO EL DUEÑO, EN CADA FILA.
    LOS_OCHO = (
        "jugador",
        "posicion",
        "precio_de_mercado",
        "lo_que_pujaria",
        "prima",
        "por_que",
        "techo",
        "mejora_a",
    )

    for fila in lista["filas"]:
        for campo in LOS_OCHO:
            assert fila.get(campo) is not None, (
                f"falta `{campo}` en la fila de {fila.get('jugador')}"
            )

        assert fila["puntos_de_mas"] is not None, fila

    # Y LA MONEDA SIGUE APAGADA DESPUES DE MIRARLA.
    #
    #     Este es el riesgo de verdad: calcular la sombra
    #     encendiendo el interruptor y dejarlo puesto seria
    #     cambiar produccion sin que nadie lo pidiera.
    assert not moneda_activa(), (
        "calcular la lista de la noche ha dejado la moneda "
        "ENCENDIDA"
    )

    assert ENV_MONEDA not in os.environ, (
        f"la sombra ha dejado {ENV_MONEDA} en el entorno"
    )


def test_la_mas_alta_va_la_primera() -> None:
    """
    «Porque es el que mas duele equivocarse.»
    """

    lista = _la_lista_del_caso()

    pujas = [f["lo_que_pujaria"] for f in lista["filas"]]

    assert pujas == sorted(pujas, reverse=True), pujas

    assert lista["filas"][0]["jugador"] == "El Caro", lista["filas"][0]

    # Y el orden no es el de entrada por casualidad: dado del
    # reves, tiene que salir igual.
    alreves = ordenar(list(reversed(lista["filas"])))

    assert [f["jugador"] for f in alreves] == [
        f["jugador"] for f in lista["filas"]
    ]


def test_la_cuenta_de_la_sombra_es_la_de_verdad() -> None:
    """
    Reescalar el valor publicado tiene que dar LO MISMO que
    correr `xi_upgrade_value` con el interruptor puesto.

    Si no diera lo mismo, la lista enseñaria una puja que Pepe
    no haria, que es peor que no enseñar ninguna.
    """

    entrada = dict(
        candidate_points=200,
        replaced_points=120,
        points_market={"rate_median": 20_000, "calibrated": True},
        recovered_value=1_000_000,
        candidate_starter={"probability": 80.0, "matchday": 6},
        replaced_starter={"probability": 40.0},
        matchday=6,
        replaced_in_lineup=True,
    )

    # Como esta hoy: la tarifa del mercado.
    con_el_mercado = xi_upgrade_value(**entrada)

    assert con_el_mercado["value"] > 0, con_el_mercado

    assert con_el_mercado["rate_per_point"] == 20_000, con_el_mercado

    # Lo que dice la sombra que valdria.
    sombra = con_la_moneda(con_el_mercado)

    assert sombra["escalado"] is True, sombra

    # Y lo que vale de verdad con el interruptor puesto.
    with _Interruptor(ENV_MONEDA):

        de_verdad = xi_upgrade_value(**entrada)

    assert de_verdad["rate_per_point"] == MONEDA_DE_LA_LIGA, de_verdad

    # UN EURO DE MARGEN, QUE ES EL REDONDEO DE `int`.
    assert abs(sombra["value"] - de_verdad["value"]) <= 1, (
        f"la sombra dice {sombra['value']} y de verdad son "
        f"{de_verdad['value']}: la cuenta de la lista de la noche "
        f"ya no es la del motor"
    )

    # Y MUERDE: con la moneda el valor tiene que SUBIR. Si los
    # dos fueran iguales, lo de arriba pasaria sin probar nada.
    assert de_verdad["value"] > con_el_mercado["value"], (
        f"la moneda no cambia el valor: {con_el_mercado['value']} "
        f"-> {de_verdad['value']}"
    )

    # Y el interruptor, como estaba.
    assert not moneda_activa()


def test_la_lista_dice_cuantos_miro() -> None:
    """
    Cero nombres puede ser "no hay nadie" o "esto se ha roto", y
    a las tres de la mañana no se distinguen. Doctrina 103.
    """

    ninguno = la_lista(
        [
            la_fila(ficha, valoracion, {"bid": 0, "decision": "NO_COMPENSA"})
            for ficha, valoracion, _ in EL_CASO
        ]
    )

    assert ninguno["n"] == 0, ninguno

    assert ninguno["mirados"] == len(EL_CASO), (
        "una lista vacia que no dice a cuantos miro no se "
        "distingue de una averia"
    )

    assert ninguno["el_mas_cerca"].get("jugador") == "El Caro", ninguno

    assert "no pujaria por nadie" in ninguno["reason"], ninguno


def test_no_recorta_sin_decirlo() -> None:
    """
    El encargo lo prohibe con todas las letras. Con mas de los
    que caben, se enseñan todos y se dice.
    """

    muchos = []

    for i in range(14):
        ficha, valoracion, _ = EL_CASO[0]

        muchos.append(
            la_fila(
                {**ficha, "id": 100 + i, "name": f"Uno {i}"},
                valoracion,
                {"bid": 9_000_000 - i * 1_000, "decision": "BID"},
            )
        )

    lista = la_lista(muchos)

    assert lista["n"] == 14, lista["n"]

    assert len(lista["filas"]) == 14, (
        "la lista se ha recortado: el encargo lo prohibe"
    )

    assert "mas de" in lista["reason"], lista["reason"]


def test_la_sombra_no_toca_ni_disco_ni_red() -> None:
    """
    Se mira el CODIGO, no el texto: el docstring cuenta la
    historia y nombra cosas a proposito.
    """

    arbol = ast.parse(EL_MODULO.read_text(encoding="utf-8"))

    docstrings = set()

    for nodo in ast.walk(arbol):
        if isinstance(
            nodo,
            (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef),
        ):
            texto = ast.get_docstring(nodo, clean=False)
            if texto:
                docstrings.add(texto)

    nombres = set()

    for nodo in ast.walk(arbol):

        if isinstance(nodo, ast.Name):
            nombres.add(nodo.id)

        elif isinstance(nodo, ast.Attribute):
            nombres.add(nodo.attr)

        elif isinstance(nodo, (ast.Import, ast.ImportFrom)):
            if isinstance(nodo, ast.ImportFrom):
                nombres.add(str(nodo.module or ""))
            for alias in nodo.names:
                nombres.add(alias.name)

    PROHIBIDO = {
        "open",
        "requests",
        "urlopen",
        "socket",
        "now",
        "utcnow",
        "time",
        "write_text",
        "write_bytes",
        "BiwengerWriteClient",
        "place_bid",
    }

    culpables = sorted(PROHIBIDO & nombres)

    assert not culpables, (
        f"la lista de la noche toca lo que no debe: {culpables}"
    )

    literales = [
        nodo.value
        for nodo in ast.walk(arbol)
        if isinstance(nodo, ast.Constant)
        and isinstance(nodo.value, str)
        and nodo.value not in docstrings
    ]

    # EL NOMBRE DE LA CARPETA, SIN ESCRIBIRLO ENTERO
    #
    #     `test_verja_determinista_v1` busca la ruta escrita en
    #     el codigo de una guardia y da por hecho que la lee.
    #     Esta no la lee: la PROHIBE. Se arma el nombre para no
    #     dar ese falso positivo -es la tercera vez que esta casa
    #     tropieza con mirar el texto en vez del codigo-.
    LA_CARPETA = "dat" + "a/"

    rutas = [c for c in literales if LA_CARPETA in c or ".jsonl" in c]

    assert not rutas, f"la lista de la noche nombra ficheros: {rutas}"


def test_sin_valoracion_no_inventa() -> None:
    """Lo que no se sabe se dice, no se rellena."""

    vacia = la_via_que_ganaria(None)

    assert vacia["value"] == 0, vacia

    assert vacia["reason"], vacia

    sin_tarifa = con_la_moneda({"value": 5_000_000})

    assert sin_tarifa["escalado"] is False, sin_tarifa

    assert sin_tarifa["value"] == 5_000_000, (
        "sin tarifa publicada se deja el valor de hoy, no se "
        "inventa uno nuevo"
    )


TESTS = [
    test_la_sombra_de_la_moneda_no_escribe,
    test_la_mas_alta_va_la_primera,
    test_la_cuenta_de_la_sombra_es_la_de_verdad,
    test_la_lista_dice_cuantos_miro,
    test_no_recorta_sin_decirlo,
    test_la_sombra_no_toca_ni_disco_ni_red,
    test_sin_valoracion_no_inventa,
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

        except Exception as error:                  # noqa: BLE001
            fallos += 1
            print(f"ERROR {test.__name__}: {type(error).__name__}: {error}")

    print()
    print(f"{len(TESTS) - fallos}/{len(TESTS)} en verde")

    if fallos:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
