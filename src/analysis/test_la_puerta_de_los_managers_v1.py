"""
La puerta de los managers: se cuenta, no se supone.

LA PREGUNTA (14/09/2026)

    49 de los 69 objetivos del dia mueren en MERCADO_DE_RIVAL: el
    71 % de la lista. El motivo declarado es que la tasa de
    aceptacion de una oferta a otro manager NO ESTA MEDIDA.

    Y se puede medir sin escribir nada: los rivales llevan cinco
    semanas haciendose ofertas entre ellos y el tablon lo publica.

LO QUE SALIO

    8 traspasos de manager a manager en los 301 eventos del
    tablon, contra 166 compras en el mercado del Computer. Y
    Pepe esta en CUATRO de los ocho.

    La ventana de tres dias que se miro primero -17 compras al
    Computer, 13 ventas al Computer y cero traspasos- no decia
    nada: en tres dias caben cero traspasos de una via que se usa
    cada semana y pico. Esta guardia existe para que esa
    conclusion no se vuelva a sacar de una muestra corta.

LO QUE VIGILAN ESTAS GUARDIAS

    1. Que se cuente el traspaso ENTRE MANAGERS y no la venta al
       Computer, que es la via que ya usamos y no prueba nada
       sobre esta.

    2. Que el tablon repetido no infle el recuento.

    3. Que este modulo NO OFREZCA NADA A NADIE. Cuenta lo que ya
       paso.

REGLA 23

    No lee estado externo: los eventos llegan como argumento.

REGLA 24

    Ninguna pasa con la lista de eventos vacia.
"""

from __future__ import annotations

import ast
from datetime import datetime, timezone
from pathlib import Path


RAIZ = Path(__file__).parents[2]

MODULO = (
    RAIZ / "src" / "analysis" / "la_puerta_de_los_managers.py"
)


AHORA = datetime(2026, 9, 14, 18, 12, tzinfo=timezone.utc)

YO = 14175949

# 19/08/2026, 24/08/2026 y 28/08/2026 en epoch UTC.
EL_19 = 1787097600
EL_24 = 1787529600
EL_28 = 1787875200


# EL TABLON, con las cuatro formas que trae de verdad.
EVENTOS = [
    # 1. TRASPASO ENTRE MANAGERS. Este es el que cuenta.
    {
        "event_id": "a1",
        "date": EL_19,
        "type": "transfer",
        "content": [
            {
                "player": 39874,
                "from": {"id": 14154203, "name": "Prinzipote"},
                "to": {"id": YO, "name": "Pepe Bordalas"},
                "amount": 463_500,
            }
        ],
    },

    # 2. EL MISMO, REPETIDO CON OTRO `event_id`.
    #
    #    El tablon lo hace: la misma fila llega dos veces, una
    #    con icono y otra sin el. Contar por `event_id` daria 9
    #    donde hay 8.
    {
        "event_id": "a2",
        "date": EL_19,
        "type": "transfer",
        "content": [
            {
                "player": 39874,
                "from": {
                    "id": 14154203,
                    "name": "Prinzipote",
                    "icon": "i/u/14154203.png",
                },
                "to": {
                    "id": YO,
                    "name": "Pepe Bordalas",
                    "icon": "i/u/14175949.png",
                },
                "amount": 463_500,
            }
        ],
    },

    # 3. OTRO TRASPASO, ESTE ENTRE RIVALES.
    {
        "event_id": "b1",
        "date": EL_28,
        "type": "transfer",
        "content": [
            {
                "player": 11,
                "from": {"id": 14145555, "name": "Pollo17"},
                "to": {"id": 14156489, "name": "Luismi_Haz"},
                "amount": 6_250_000,
            }
        ],
    },

    # 4. VENTA AL COMPUTER: `from` y sin `to`. NO cuenta.
    {
        "event_id": "c1",
        "date": EL_24,
        "type": "transfer",
        "content": [
            {
                "player": 23006,
                "from": {"id": 14145555, "name": "Pollo17"},
                "amount": 153_800,
            }
        ],
    },

    # 5. SUBASTA DEL COMPUTER: el jugador entra del mercado.
    {
        "event_id": "d1",
        "date": EL_24,
        "type": "market",
        "content": [
            {
                "player": 17057,
                "to": {"id": 14176382, "name": "Manzagool"},
                "amount": 6_027_930,
                "bids": [
                    {
                        "user": {"id": 14145555, "name": "Pollo17"},
                        "amount": 5_807_000,
                    }
                ],
            }
        ],
    },

    # 6. UN EVENTO CON EL CONTENIDO EN OTRA FORMA.
    #
    #    Medido en el tablon: hay eventos cuyo contenido no es
    #    una lista de fichas. Si esto reventara el recuento, la
    #    pantalla diria "no se pudo contar", que se lee igual que
    #    "cero" — y cero es justo la conclusion equivocada.
    {
        "event_id": "e1",
        "date": EL_28,
        "type": "adminText",
        "content": {"text": "Bienvenidos"},
    },

    # 7. Y OTRO CON `from` COMO CADENA.
    {
        "event_id": "e2",
        "date": EL_28,
        "type": "transfer",
        "content": [
            {"player": 999, "from": "el mercado", "amount": 1},
        ],
    },
]


def _puerta(**cambios):
    from src.analysis.la_puerta_de_los_managers import (
        traspasos_entre_managers,
    )

    argumentos = {
        "eventos": EVENTOS,
        "precio": None,
        "mi_user_id": YO,
        "ahora": AHORA,
    }

    argumentos.update(cambios)

    return traspasos_entre_managers(**argumentos)


def _codigo_vivo(fuente: str) -> str:
    """El modulo entero sin docstrings ni comentarios."""

    arbol = ast.parse(fuente)

    for nodo in ast.walk(arbol):

        if isinstance(
            nodo,
            (ast.FunctionDef, ast.AsyncFunctionDef,
             ast.ClassDef, ast.Module),
        ):
            cuerpo = list(nodo.body)

            if (
                cuerpo
                and isinstance(cuerpo[0], ast.Expr)
                and isinstance(cuerpo[0].value, ast.Constant)
                and isinstance(cuerpo[0].value.value, str)
            ):
                nodo.body = cuerpo[1:]

    return ast.dump(arbol)


# ============================================================
# 1. SE CUENTA EL TRASPASO, NO LA VENTA AL COMPUTER
# ============================================================


def test_la_puerta_se_cuenta_y_no_se_supone() -> None:
    """
    Dos traspasos entre managers, y ni uno mas.

    LO QUE ROMPE ESTA GUARDIA

        Contar las ventas al Computer como si fueran traspasos.
        Son la via que YA usamos: contarlas aqui haria que la
        puerta pareciera abierta de par en par sin haberla
        cruzado nunca.

        O al reves: contar por `event_id` y darle al tablon
        repetido el valor de un traspaso que no existio.
    """

    visto = _puerta()

    assert visto["available"] is True, visto

    # REGLA 24: con la lista vacia esto no probaria nada.
    assert visto["eventos_leidos"] == len(EVENTOS), visto

    # 1. DOS TRASPASOS: el nuestro y el de los rivales.
    #
    #    Hay siete eventos y cinco fichas con importe. Solo dos
    #    cruzan la puerta.
    assert visto["cuantos"] == 2, visto["traspasos"]

    assert visto["nuestros"] == 1, visto
    assert visto["de_los_rivales"] == 1, visto

    # 2. EL REPETIDO NO CUENTA DOS VECES.
    #
    #    Los eventos `a1` y `a2` son el mismo hecho con dos
    #    `event_id`.
    assert len(
        [t for t in visto["traspasos"] if t["player_id"] == 39874]
    ) == 1, visto["traspasos"]

    # 3. LA VENTA AL COMPUTER NO ES UN TRASPASO.
    assert not [
        t for t in visto["traspasos"] if t["player_id"] == 23006
    ], visto["traspasos"]

    # 4. LA SUBASTA TAMPOCO, Y SE CUENTA APARTE.
    #
    #    Es el denominador: 2 traspasos sobre 1 compra al
    #    Computer se lee muy distinto de 2 sobre 166.
    assert visto["compras_al_computer"] == 1, visto

    assert not [
        t for t in visto["traspasos"] if t["player_id"] == 17057
    ], visto["traspasos"]

    # 5. UN EVENTO CON OTRA FORMA NO TUMBA EL RECUENTO.
    #
    #    "No se pudo contar" se lee igual que "cero", y cero es
    #    justo la conclusion equivocada.
    assert visto["available"] is True, visto

    # 6. Y SE SABE QUE LA PUERTA NO ESTA CERRADA.
    assert visto["puerta_cerrada"] is False, visto

    assert "NO esta cerrada" in visto["reason"], visto["reason"]

    # 7. LOS DIAS SIN TRASPASO SALEN DE LA HORA QUE ENTRA POR LA
    #    PUERTA (doctrina 50). Sin hora no se dice un numero.
    assert visto["dias_sin_traspaso"] == 17, visto

    sin_hora = _puerta(ahora=None)

    assert sin_hora["dias_sin_traspaso"] is None, sin_hora

    # 8. Y CON CERO TRASPASOS, EL VEREDICTO ES EL OTRO.
    #
    #    Es la conclusion gorda del encargo: si en toda la liga
    #    nadie le vende a nadie, la puerta no la cierra nuestro
    #    codigo.
    solo_computer = _puerta(
        eventos=[e for e in EVENTOS if e["event_id"][0] in "cde"]
    )

    assert solo_computer["eventos_leidos"] == 4, solo_computer

    assert solo_computer["cuantos"] == 0, solo_computer

    assert solo_computer["puerta_cerrada"] is True, solo_computer

    assert "nadie le vende a nadie" in (
        solo_computer["reason"]
    ), solo_computer["reason"]

    # 9. Y SIN EVENTOS NO SE CONCLUYE NADA.
    #
    #    Cero eventos NO es "cero traspasos": es que no se ha
    #    podido mirar. Confundirlos daria el veredicto mas caro
    #    del encargo a partir de un fichero que no llego.
    sin_nada = _puerta(eventos=[])

    assert sin_nada["available"] is False, sin_nada
    assert sin_nada["puerta_cerrada"] is None, sin_nada
    assert "sin " in sin_nada["reason"], sin_nada["reason"]


# ============================================================
# 2. ESTE MODULO NO OFRECE NADA A NADIE
# ============================================================


def test_contar_la_puerta_no_ofrece_nada() -> None:
    """
    Es una cuenta de lo que ya paso, no una via de escritura.

    El encargo lo dice con todas las letras: «No hagas ninguna
    oferta a ningun manager. Esto es contar lo que ya paso.» El
    experimento lo autoriza el dueño, no el codigo.
    """

    fuente = MODULO.read_text(encoding="utf-8")

    vivo = _codigo_vivo(fuente)

    # NI CLIENTE, NI PETICIONES, NI ESCRITURA.
    for prohibido in (
        "requests",
        "urllib",
        "httpx",
        "BiwengerClient",
        "send_offer",
        "make_offer",
        "post",
        "open(",
        "write_text",
    ):
        assert prohibido not in vivo, (
            f"el contador de la puerta menciona `{prohibido}`: "
            f"esto cuenta lo que ya paso, no llama a nadie"
        )

    # Y NO IMPORTA NADA DE LA RUTA DE ACCION.
    arbol = ast.parse(fuente)

    for nodo in ast.walk(arbol):

        if isinstance(nodo, (ast.Import, ast.ImportFrom)):

            nombre = (
                getattr(nodo, "module", None)
                or (nodo.names[0].name if nodo.names else "")
            )

            assert "actions" not in str(nombre), (
                f"importa `{nombre}`: la ruta de acciones no "
                f"pinta nada en un contador"
            )

    # Y SIGUE CONTANDO BIEN, que es lo que tiene que hacer.
    visto = _puerta()

    assert visto["cuantos"] == 2, visto

    # Y LLEGA HASTA LA PANTALLA.
    #
    #     Sin esto, la telemetria lo escribe y `normalizeStatus`
    #     lo tira por el camino: el numero existiria y no lo
    #     veria nadie, que es exactamente lo que pasaba con la
    #     edad de los sentidos.
    normaliza = (
        RAIZ / "dashboard-v8" / "src" / "lib" / "status.js"
    ).read_text(encoding="utf-8")

    assert "laPuertaDeLosManagers" in normaliza, (
        "`normalizeStatus` no publica la puerta de los managers"
    )

    # Y SIN DATO, `puerta_cerrada` NO ES `true`.
    #
    #     "No se pudo contar" y "en esta liga nadie vende" son
    #     cosas distintas, y la segunda cierra el 71 % de la
    #     lista de objetivos.
    assert "puerta_cerrada: null" in normaliza, (
        "el respaldo de la pantalla da por cerrada una puerta "
        "que no se ha podido contar"
    )

    panel = (
        RAIZ
        / "dashboard-v8"
        / "src"
        / "components"
        / "LaPuertaDeLosManagersPanel.jsx"
    )

    assert panel.exists(), (
        "no hay cuadro: el numero que decide el 71 % de la lista "
        "no se ve en ninguna pantalla"
    )


TESTS = [
    test_la_puerta_se_cuenta_y_no_se_supone,
    test_contar_la_puerta_no_ofrece_nada,
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
        f"LA PUERTA DE LOS MANAGERS V1: "
        f"{len(TESTS) - fallos}/{len(TESTS)} OK"
    )
    print("=" * 60)

    if fallos:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
