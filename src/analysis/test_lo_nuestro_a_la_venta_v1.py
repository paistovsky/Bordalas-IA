"""
Lo nuestro a la venta: la etiqueta la decide el motor.

SINTOMA (13/09/2026)

    De lo que tenemos publicado, la pantalla enseñaba un numero:
    "16 publicados". Catorce ofertas del Computer encima de la
    mesa y ni una de las decisiones a la vista.

LO QUE VIGILAN ESTAS GUARDIAS

    1. Que la etiqueta salga de la decision del motor y no de un
       umbral de la pantalla. Sin decision: "sin decidir".

    2. Que cada oferta lleve SU reloj. Hoy hay ofertas a 33,5 h y
       otras a 9,5 h: un unico reloj para todas seria falso.

    3. Que el aviso de "comprado y sin publicar" lo encienda el
       HECHO y no un cartel fijo (regla 37).

REGLA 23

    No lee estado externo: publicaciones, ofertas y catalogo se
    construyen aqui.
"""

from __future__ import annotations

import ast
from pathlib import Path


RAIZ = Path(__file__).parents[2]

PANEL = (
    RAIZ
    / "dashboard-v8"
    / "src"
    / "components"
    / "LoNuestroALaVentaPanel.jsx"
)


CATALOGO = {
    41606: {"id": 41606, "name": "Mangala", "position": 3,
            "points": 13, "price": 2_410_000, "status": "ok",
            "teamID": 5},
    17482: {"id": 17482, "name": "Dituro", "position": 1,
            "points": 4, "price": 2_310_000, "status": "ok",
            "teamID": 75},
    26271: {"id": 26271, "name": "Yamal", "position": 4,
            "points": 45, "price": 21_720_000, "status": "ok",
            "teamID": 1},
    3159: {"id": 3159, "name": "Jutgla", "position": 4,
           "points": 14, "price": 3_050_000, "status": "ok",
           "teamID": 7},
    9983: {"id": 9983, "name": "Djene", "position": 2,
           "points": 7, "price": 1_840_000, "status": "injured",
           "teamID": 9},
}

EL_ONCE = [
    {"id": 41606, "position": 3},
    {"id": 17482, "position": 1},
    {"id": 26271, "position": 4},
]

# CUATRO PUBLICACIONES CON OFERTA Y UNA SIN ELLA.
LISTADOS = [
    {"player_id": 41606, "listed_price": 2_410_000,
     "hours_to_expiry": 40.0, "expired": False,
     "renew_required": False},
    {"player_id": 17482, "listed_price": 2_310_000,
     "hours_to_expiry": 40.0, "expired": False,
     "renew_required": False},
    {"player_id": 26271, "listed_price": 21_720_000,
     "hours_to_expiry": 12.0, "expired": False,
     "renew_required": False},
    {"player_id": 3159, "listed_price": 3_050_000,
     "hours_to_expiry": 40.0, "expired": False,
     "renew_required": False},

    # Publicado y SIN oferta: el motor no ha dicho nada de el.
    {"player_id": 9983, "listed_price": 1_840_000,
     "hours_to_expiry": 3.0, "expired": False,
     "renew_required": True},
]

# LAS DOS HORAS DISTINTAS ESTAN AQUI A PROPOSITO: 33,5 y 9,5.
OFERTAS = [
    {"player_ids": [41606], "amount": 2_498_100,
     "premium_percent": 3.7, "action": "HOLD_SOLVENCY_RESERVED",
     "protection": "SELLABLE", "counterparty": "COMPUTER",
     "hours_to_expiry": 33.5, "expired": False,
     "decision_source": "OFFER_DECISION_V2",
     "decision_reason": "Oferta marcada SOLVENCY_RESERVED."},

    {"player_ids": [17482], "amount": 2_373_400,
     "premium_percent": 2.7, "action": "KEEP_GOOD_OFFER",
     "protection": "NORMAL", "counterparty": "COMPUTER",
     "hours_to_expiry": 33.5, "expired": False,
     "decision_source": "OFFER_DECISION_V2",
     "decision_reason": "Oferta buena, se conserva."},

    {"player_ids": [26271], "amount": 20_680_800,
     "premium_percent": -4.8, "action": "NEVER_SELL",
     "protection": "NEVER_AUTO_SELL", "counterparty": "COMPUTER",
     "hours_to_expiry": 9.5, "expired": False,
     "decision_source": "OFFER_DECISION_V2",
     "decision_reason": "Jugador Franchise/NEVER_AUTO_SELL."},

    # UNA ACCION QUE LA PANTALLA NO SABE TRADUCIR.
    {"player_ids": [3159], "amount": 3_115_700,
     "premium_percent": 2.2, "action": "INVENTADA_POR_EL_MOTOR",
     "protection": "NORMAL", "counterparty": "COMPUTER",
     "hours_to_expiry": 33.5, "expired": False,
     "decision_source": "OFFER_DECISION_V2",
     "decision_reason": "Un motivo cualquiera."},
]


def _venta(**cambios):
    from src.analysis.lo_nuestro_a_la_venta import (
        lo_nuestro_a_la_venta,
    )

    argumentos = {
        "listados": LISTADOS,
        "ofertas": OFERTAS,
        "catalogo": CATALOGO,
        "once": EL_ONCE,
        "sin_listar": None,
        "renovacion": {"reason": "Nada que renovar."},
    }

    argumentos.update(cambios)

    return lo_nuestro_a_la_venta(**argumentos)


def _por_nombre(visto, nombre):
    for fila in visto["players"]:
        if fila["name"] == nombre:
            return fila

    raise AssertionError(f"no esta {nombre}")


def _codigo_vivo(fuente: str, nombre: str) -> str:
    """
    El cuerpo de una funcion SIN su docstring ni sus comentarios.

    Ocho guardias de esta casa se han puesto rojas por el texto
    que las explica. El AST tira los comentarios solo; el
    docstring hay que quitarlo a mano.
    """

    arbol = ast.parse(fuente)

    for nodo in ast.walk(arbol):

        if (
            isinstance(nodo, ast.FunctionDef)
            and nodo.name == nombre
        ):
            cuerpo = list(nodo.body)

            if (
                cuerpo
                and isinstance(cuerpo[0], ast.Expr)
                and isinstance(cuerpo[0].value, ast.Constant)
                and isinstance(cuerpo[0].value.value, str)
            ):
                cuerpo = cuerpo[1:]

            return ast.dump(
                ast.Module(body=cuerpo, type_ignores=[])
            )

    raise AssertionError(f"no existe la funcion `{nombre}`")


def _jsx_sin_comentarios(fuente: str) -> str:
    import re

    fuente = re.sub(r"/\*.*?\*/", " ", fuente, flags=re.S)

    return re.sub(r"(?m)^\s*//.*$", " ", fuente)


# ============================================================
# 1. LA ETIQUETA SALE DE LA DECISION
# ============================================================


def test_la_etiqueta_sale_de_la_decision() -> None:
    """
    LA ETIQUETA NO LA DECIDE LA PANTALLA. LA DECIDE EL MOTOR Y LA
    PANTALLA LA TRADUCE.

    CONSECUENCIA DE QUE NO FUERA ASI

        Un umbral en la pantalla —"si la prima pasa del 3 %,
        vender"— seria una segunda opinion sin medir, con la
        pinta de ser la del motor. El dueño creeria estar viendo
        lo que Pepe va a hacer y estaria viendo otra cosa.

    Y SIN DECISION, «SIN DECIDIR»

        Djene esta publicado y no tiene oferta: el motor no ha
        dicho nada de el. No se rellena con la etiqueta mas
        probable.
    """

    visto = _venta()

    assert visto["available"] is True, visto

    # REGLA 24: con la lista vacia esto no probaria nada.
    assert len(visto["players"]) == len(LISTADOS), visto

    # 1. CADA ETIQUETA ES LA TRADUCCION DE SU ACCION.
    espera = {
        "Mangala": ("HOLD_SOLVENCY_RESERVED",
                    "guardar para tapar deuda"),
        "Dituro": ("KEEP_GOOD_OFFER", "buena, la conservamos"),
        "Yamal": ("NEVER_SELL", "no se vende nunca"),
    }

    for nombre, (accion, etiqueta) in espera.items():
        fila = _por_nombre(visto, nombre)

        assert fila["accion_del_motor"] == accion, fila
        assert fila["que_va_a_hacer"] == etiqueta, fila
        assert fila["decidido"] is True, fila

    # 2. SIN DECISION, "SIN DECIDIR" Y CONTADO.
    djene = _por_nombre(visto, "Djene")

    assert djene["accion_del_motor"] is None, djene
    assert djene["que_va_a_hacer"] == "sin decidir", djene
    assert djene["decidido"] is False, djene

    assert visto["sin_decidir"] == 1, visto

    # Y arriba del todo, que es lo que hay que mirar.
    assert visto["players"][0]["name"] == "Djene", [
        f["name"] for f in visto["players"]
    ]

    # 3. UNA ACCION QUE NO SE SABE TRADUCIR SALE EN CRUDO.
    #
    #    Un nombre feo y verdadero antes que uno bonito e
    #    inventado.
    jutgla = _por_nombre(visto, "Jutgla")

    assert jutgla["que_va_a_hacer"] == (
        "INVENTADA_POR_EL_MOTOR"
    ), jutgla

    assert jutgla["traducida"] is False, jutgla

    assert visto["sin_traducir"] == [
        "INVENTADA_POR_EL_MOTOR"
    ], visto

    # 4. CAMBIA LA DECISION DEL MOTOR, CAMBIA LA ETIQUETA.
    otras = [
        dict(o, action="REROLL_CANDIDATE")
        if o["player_ids"] == [17482]
        else o
        for o in OFERTAS
    ]

    assert _por_nombre(_venta(ofertas=otras), "Dituro")[
        "que_va_a_hacer"
    ] == "pedir otra oferta"

    # 5. NI UN UMBRAL EN EL MODULO NI EN LA PANTALLA.
    #
    #    La etiqueta sale de `accion`, y de nada mas.
    fuente = (
        RAIZ / "src" / "analysis" / "lo_nuestro_a_la_venta.py"
    ).read_text(encoding="utf-8")

    # `_codigo_vivo` deja el cuerpo sin docstring ni comentarios:
    # ocho guardias de esta casa se han puesto rojas por el texto
    # que las explicaba.
    codigo = _codigo_vivo(fuente, "lo_nuestro_a_la_venta")

    assert "QUE_VA_A_HACER" in codigo, (
        "la etiqueta ya no sale de la tabla de traduccion"
    )

    arbol = ast.parse(fuente)

    comparaciones = [
        nodo
        for nodo in ast.walk(arbol)
        if isinstance(nodo, ast.Compare)
        and any(
            isinstance(op, (ast.Gt, ast.GtE, ast.Lt, ast.LtE))
            for op in nodo.ops
        )
    ]

    assert not comparaciones, (
        f"el modulo compara con umbrales ({len(comparaciones)} "
        f"comparaciones de mayor/menor): la etiqueta tiene que "
        f"salir de la decision del motor, no de un numero puesto "
        f"aqui"
    )

    # Y LA PANTALLA SOLO PINTA `que_va_a_hacer`.
    panel = _jsx_sin_comentarios(
        PANEL.read_text(encoding="utf-8")
    )

    assert "fila.que_va_a_hacer" in panel, (
        "la pantalla no pinta la etiqueta que publica el motor"
    )

    # LA CELDA QUE DECIDE NO MIRA NINGUN NUMERO.
    #
    #     Se mira SOLO la celda de QUE VA A HACER, cortada en su
    #     propio `</td>`. En el resto de la fila hay
    #     comparaciones legitimas —`prima > 0` pinta el signo en
    #     verde o en rojo— y prohibirlas en todo el fichero
    #     convierte la guardia en un estorbo que alguien acaba
    #     relajando.
    #
    #     Y se comprueba por los DATOS que toca, no por los
    #     operadores: en JSX el simbolo `>` cierra cada etiqueta,
    #     asi que buscarlo caza la sintaxis en vez del defecto.
    celda = panel[panel.index(chr(34) + "ac" + chr(34)) :]

    celda = celda[: celda.index("</td>")]

    assert "fila.que_va_a_hacer" in celda, celda

    for numero in (
        "fila.prima",
        "fila.nos_ofrecen",
        "fila.vale",
        "fila.points",
        "fila.oferta_caduca_en",
    ):
        assert numero not in celda, (
            f"la celda de QUE VA A HACER mira `{numero}`: la "
            f"etiqueta la decide el motor, no la pantalla"
        )

    # Y no hay ninguna tabla de etiquetas indexada por un numero.
    for inventa in ("premium_percent >", "prima > 3", "> 3 ?"):
        assert inventa not in panel, (
            f"la pantalla decide por su cuenta con `{inventa}`"
        )


# ============================================================
# 2. CADA OFERTA CON SU RELOJ
# ============================================================


def test_cada_oferta_con_su_reloj() -> None:
    """
    DOS OFERTAS, DOS RELOJES.

    SINTOMA

        Hoy hay ofertas que caducan en 33,5 h y otras en 9,5 h.
        Un unico reloj —el del reset— para todas las filas es el
        mismo error que ya se arreglo en el cuadro de objetivos:
        un numero que parece medido y no lo es.

    Y CADUCAN DOS COSAS DISTINTAS (regla 33)

        LA OFERTA y LA PUBLICACION. Llevan numeros distintos y
        van con su nombre puesto. Yamal tiene la publicacion a
        12 h y la oferta a 9,5 h: no es lo mismo.
    """

    visto = _venta()

    horas = {
        f["name"]: f["oferta_caduca_en"] for f in visto["players"]
    }

    # REGLA 24.
    assert len(horas) == len(LISTADOS), horas

    # 1. NO SON TODAS IGUALES.
    distintas = {
        h for h in horas.values() if h is not None
    }

    assert len(distintas) > 1, (
        f"todas las ofertas caducan a la misma hora ({horas}): "
        f"eso es un reloj unico disfrazado de reloj por fila"
    )

    assert horas["Mangala"] == 33.5, horas
    assert horas["Yamal"] == 9.5, horas

    # 2. LOS DOS RELOJES, CON SU NOMBRE.
    yamal = _por_nombre(visto, "Yamal")

    assert yamal["oferta_caduca_en"] == 9.5, yamal
    assert yamal["publicacion_caduca_en"] == 12.0, yamal

    assert (
        yamal["oferta_caduca_en"]
        != yamal["publicacion_caduca_en"]
    ), "los dos relojes se han vuelto el mismo numero"

    # 3. SIN OFERTA NO SE INVENTA UN CERO.
    #
    #    Un 0,0 se lee como "vence ya", que es lo contrario de
    #    "no se sabe".
    djene = _por_nombre(visto, "Djene")

    assert djene["oferta_caduca_en"] is None, djene
    assert djene["nos_ofrecen"] is None, djene
    assert djene["prima"] is None, djene

    # Su publicacion SI tiene reloj: son dos cosas distintas.
    assert djene["publicacion_caduca_en"] == 3.0, djene

    # 4. LA PANTALLA USA EL DE LA FILA, no el del reset.
    panel = _jsx_sin_comentarios(
        PANEL.read_text(encoding="utf-8")
    )

    assert "horas={fila.oferta_caduca_en}" in panel, (
        "la cuenta atras no usa el reloj de su oferta"
    )

    for del_reset in (
        "marketClock",
        "seconds_to_reset",
        "hours_to_reset",
    ):
        assert del_reset not in panel, (
            f"la cuenta atras vuelve a usar `{del_reset}`: seria "
            f"la misma para las catorce filas"
        )

    assert "sin dato" in panel, (
        "sin horas pintaria un cero, que se lee como «vence ya»"
    )

    assert "setInterval" in panel, (
        "la cuenta atras no corre: se queda congelada"
    )


# ============================================================
# 3. EL AVISO LO ENCIENDE EL HECHO
# ============================================================


def test_el_aviso_de_comprado_sin_publicar_no_es_fijo() -> None:
    """
    REGLA 37: UN INDICADOR LO ENCIENDE EL HECHO, NO LA INTENCION.

    SINTOMA

        Un jugador comprado para revender y sin poner a la venta
        esta parado: mientras no este publicado, el Computer no
        le hace ninguna oferta y el viaje no avanza.

    CONSECUENCIA DE UN CARTEL FIJO

        Un aviso que sale siempre se deja de leer a los dos dias.
        El unico dia que hace falta, ya no avisa de nada.

    El aviso sale cuando HAY alguno, y no sale cuando no lo hay.
    """

    from src.analysis.lo_nuestro_a_la_venta import _el_aviso

    # 1. SIN VIAJES ABIERTOS, NO SALE.
    apagado = _venta(
        sin_listar={
            "available": True,
            "hay_viajes": False,
            "abiertos": 0,
            "players": [],
            "reason": "NO HAY NINGUN VIAJE ABIERTO",
        }
    )["comprado_sin_publicar"]

    assert apagado["hay"] is False, apagado
    assert apagado["players"] == [], apagado

    # 2. CON UNO, SALE Y CON SU NOMBRE.
    encendido = _venta(
        sin_listar={
            "available": True,
            "hay_viajes": True,
            "abiertos": 1,
            "players": [{"id": 37499, "name": "Trent"}],
            "reason": "1 viaje abierto sin publicar.",
        }
    )["comprado_sin_publicar"]

    assert encendido["hay"] is True, encendido
    assert encendido["players"] == ["Trent"], encendido

    # 3. SIN EL DATO, TAMPOCO SE ENCIENDE.
    #
    #    "No se sabe" no es "hay uno". Inventar el aviso es el
    #    mismo error que inventar el numero.
    for sin_dato in (None, {}, {"players": None}):
        assert _el_aviso(sin_dato)["hay"] is False, sin_dato

    # 4. EL AVISO SE MONTA AUNQUE NO HAYA NI UNA PUBLICACION.
    #
    #    Es justo el caso en que hace falta: comprado, sin
    #    publicar, y por tanto sin fila en el cuadro.
    sin_cuadro = _venta(
        listados=[],
        sin_listar={
            "players": [{"name": "Trent"}],
            "reason": "1 viaje abierto sin publicar.",
        },
    )

    assert sin_cuadro["available"] is False, sin_cuadro

    assert sin_cuadro["comprado_sin_publicar"]["hay"] is True, (
        "el aviso desaparece cuando no hay publicaciones, que es "
        "justo cuando hace falta"
    )

    # 5. LA PANTALLA LO PINTA CONDICIONADO, no siempre.
    panel = _jsx_sin_comentarios(
        PANEL.read_text(encoding="utf-8")
    )

    assert "aviso.hay ?" in panel, (
        "el aviso no depende del hecho: seria un cartel fijo"
    )

    # Y en las dos ramas del panel: con cuadro y sin cuadro.
    assert panel.count("aviso.hay ?") >= 2, (
        "el aviso solo se pinta en una de las dos ramas"
    )


# ============================================================
# 4. ESTO NO DECIDE NADA
# ============================================================


def test_este_cuadro_no_vende_nada() -> None:
    """
    No se vende, no se acepta y no se rerollea nada desde aqui.

    El dia que alguien lo conecte, esta guardia se pone roja y se
    habla antes.
    """

    fuente = (
        RAIZ / "src" / "analysis" / "lo_nuestro_a_la_venta.py"
    ).read_text(encoding="utf-8")

    arbol = ast.parse(fuente)

    llamadas = {
        nodo.func.id
        for nodo in ast.walk(arbol)
        if isinstance(nodo, ast.Call)
        and isinstance(nodo.func, ast.Name)
    } | {
        nodo.func.attr
        for nodo in ast.walk(arbol)
        if isinstance(nodo, ast.Call)
        and isinstance(nodo.func, ast.Attribute)
    }

    for escribe in (
        "accept_offer",
        "reroll_offer",
        "list_player_for_sale",
        "place_bid",
        "abrir",
    ):
        assert escribe not in llamadas, (
            f"el cuadro llama a `{escribe}`: deberia ser solo "
            f"para mirar"
        )

    for modulo in ("write_client", "executor", "autopilot"):
        assert modulo not in fuente, (
            f"el cuadro importa `{modulo}`"
        )


def test_el_cuadro_esta_montado_y_lee_lo_publicado() -> None:
    """
    Que exista no basta: tiene que estar en la pagina, en su
    sitio, y leer el bloque que publica la telemetria.
    """

    mercado = (
        RAIZ / "dashboard-v8" / "src" / "pages" / "MarketPage.jsx"
    ).read_text(encoding="utf-8")

    assert "<LoNuestroALaVentaPanel" in mercado, (
        "el cuadro no esta montado en MERCADO"
    )

    # EL ORDEN QUE PIDIO EL DUEÑO: objetivos, lo nuestro a la
    # venta, y la liga entera al final.
    assert mercado.index("<LoNuestroALaVentaPanel") < (
        mercado.index("<TodaLaLigaPanel")
    ), (
        "la liga entera va DESPUES de lo nuestro a la venta"
    )

    assert mercado.index("<TargetsPanel") < (
        mercado.index("<LoNuestroALaVentaPanel")
    ), (
        "los objetivos de hoy van ANTES de lo nuestro a la venta"
    )

    estado = (
        RAIZ / "src" / "telemetry" / "dashboard_state.py"
    ).read_text(encoding="utf-8")

    assert '"loNuestroALaVenta"' in estado, (
        "la telemetria no publica lo nuestro a la venta"
    )

    assert "lo_nuestro_a_la_venta(" in estado, (
        "no se llama al modulo que lo monta"
    )

    # Y LAS OFERTAS SE CRUZAN POR ID, no por nombre.
    assert '"player_ids"' in estado, (
        "las ofertas no publican el id del jugador: el cuadro "
        "tendria que cruzar por nombre, que Biwenger repite"
    )


TESTS = [
    test_la_etiqueta_sale_de_la_decision,
    test_cada_oferta_con_su_reloj,
    test_el_aviso_de_comprado_sin_publicar_no_es_fijo,
    test_este_cuadro_no_vende_nada,
    test_el_cuadro_esta_montado_y_lee_lo_publicado,
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
        f"LO NUESTRO A LA VENTA V1: "
        f"{len(TESTS) - fallos}/{len(TESTS)} OK"
    )
    print("=" * 60)

    if fallos:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
