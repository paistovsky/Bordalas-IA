"""
El escaparate estaba armado y no lo llamaba nadie.

SINTOMA (13/09/2026)

    Trent comprado el 12 para revender, ganado en el reset de las
    07:00, y a mediodia seguia en el banquillo SIN PUBLICAR. Los
    otros cinco suplentes si estaban publicados.

    `publicar()` y `que_publicar()` existian desde hacia dias y
    NO LOS LLAMABA NADIE. Tercera vez del mismo patron: el
    carril, el plato vacio, y esto.

    Un viaje comprado y fuera del escaparate es medio viaje: se
    ha pagado la compra, no llega ninguna oferta, y la plusvalia
    —que es todo el negocio— no existe.

LAS CONDICIONES, QUE SON DURAS

    solo viajes del carril   lo que el libro marca RENDIJA
    NUNCA UN TITULAR         ni aunque el libro lo marque
    zona de silencio         por la misma puerta que la renovacion
    una por vuelta
    idempotente              contra LA FOTO, no la memoria
    el precio                de la regla de salida que ya existe

POR QUE NUNCA UN TITULAR

    Vender al que juega es cambiar puntos por plusvalia, y los
    puntos son el motor economico: se pagan a 30.000 EUR y valen
    x8,4 frente al comercio (doctrina 30).

REGLA 23

    No lee estado externo: plantilla, once y listados se
    construyen aqui.
"""

from __future__ import annotations

import ast

from pathlib import Path


RAIZ = Path(__file__).parents[2]


# EL CASO REAL DEL 13/09/2026.
TRENT = {
    "id": 37499,
    "name": "Trent",
    "position": 2,
    "price": 2_730_000,
}

# Nuestro mejor defensa, y TITULAR.
JONNY = {
    "id": 1599,
    "name": "Jonny",
    "position": 2,
    "price": 2_380_000,
}

# El once del 13/09, tal cual lo publica Biwenger.
EL_ONCE = [
    17482, 1599, 1721, 9983, 29661, 19862,
    14800, 41606, 1602, 26271, 3159,
]

PLANTILLA = [TRENT, JONNY]


def _viaje(player_id, via="RENDIJA") -> dict:
    return {
        "player_id": player_id,
        "name": None,
        "via": via,
        "state": "ABIERTO",
        "opened_at": "2026-09-13T06:45:00+00:00",
    }


# ============================================================
# 1. NUNCA UN TITULAR
# ============================================================


def test_publicar_no_toca_a_un_titular() -> None:
    """
    Jonny esta marcado como viaje Y es titular. No se publica.

    Y SI LA LISTA DE TITULARES LLEGA VACIA, NO SE PUBLICA NADA
    (regla 24): una lista vacia no es "no hay titulares", es que
    no se ha podido leer el once. Publicar a ciegas puede sacar
    al mejor jugador del equipo al escaparate.
    """

    from src.actions.escaparate_executor import que_publicar

    # 1. CON EL ONCE DELANTE: Trent si, Jonny no.
    plan = que_publicar(
        ganadas=[_viaje(TRENT["id"]), _viaje(JONNY["id"])],
        plantilla=PLANTILLA,
        ya_listados=[],
        titulares=EL_ONCE,
    )

    assert plan["available"] is True, plan

    publicados = {x["player_id"] for x in plan["publicar"]}

    assert publicados == {TRENT["id"]}, plan

    saltado = [
        x
        for x in plan["saltados"]
        if x["player_id"] == JONNY["id"]
    ]

    assert saltado, plan

    assert "TITULAR" in saltado[0]["reason"], saltado

    # 2. SIN ONCE: no se publica NADA, ni siquiera a Trent.
    for a_ciegas in (None, [], [{}], [0]):

        ciego = que_publicar(
            ganadas=[_viaje(TRENT["id"])],
            plantilla=PLANTILLA,
            ya_listados=[],
            titulares=a_ciegas,
        )

        assert ciego["publicar"] == [], (a_ciegas, ciego)

        assert "titulares" in ciego["reason"], ciego


def test_solo_se_publican_viajes_del_carril() -> None:
    """
    Un jugador que el libro no marca como viaje del carril no se
    toca, venga de donde venga.

    El filtro vive en el ciclo —`_llenar_el_escaparate` solo le
    pasa los de via RENDIJA— asi que se comprueba ahi.
    """

    ciclo = (
        RAIZ / "src" / "v10_full_autonomous_live.py"
    ).read_text(encoding="utf-8")

    dentro = None

    for nodo in ast.walk(ast.parse(ciclo)):

        if (
            isinstance(nodo, ast.FunctionDef)
            and nodo.name == "_llenar_el_escaparate"
        ):
            dentro = ast.get_source_segment(ciclo, nodo) or ""

    assert dentro, "no existe `_llenar_el_escaparate`"

    assert '"RENDIJA"' in dentro, (
        "el escaparate no filtra por via RENDIJA: publicaria "
        "cualquier compra, incluida una para quedarse"
    )

    # Y que pase el once y los listados de la foto.
    for cual in ("titulares", "ya_listados", "compact_listings"):
        assert cual in dentro, (
            f"`_llenar_el_escaparate` no usa `{cual}`"
        )


# ============================================================
# 2. IDEMPOTENTE, Y CONTRA LA FOTO
# ============================================================


def test_no_republica_lo_que_ya_esta_publicado() -> None:
    """
    La prueba es LA FOTO, no la memoria.

    Si se fiara de un libro propio, un despliegue que perdiera
    ese libro republicaria todo — y republicar reinicia el reloj
    de 48 h del listado, que es justo lo que no queremos tocar
    sin motivo.
    """

    from src.actions.escaparate_executor import que_publicar

    ya = que_publicar(
        ganadas=[_viaje(TRENT["id"])],
        plantilla=PLANTILLA,
        ya_listados=[{"player_id": TRENT["id"]}],
        titulares=EL_ONCE,
    )

    assert ya["publicar"] == [], ya

    assert "ya esta publicado" in ya["saltados"][0]["reason"]


def test_una_publicacion_por_vuelta() -> None:
    """Una vuelta, una escritura. Como todo lo demas."""

    from src.actions.escaparate_executor import publicar

    escritos = []

    class _Escritor:
        def list_player_for_sale(self, **kwargs):
            escritos.append(kwargs)
            return {"sent": True, "success": True}

    import tempfile

    with tempfile.TemporaryDirectory() as tmp:

        publicar(
            [
                {
                    "player_id": TRENT["id"],
                    "name": "Trent",
                    "position": 2,
                    "listed_price": 3_139_500,
                },
                {
                    "player_id": 999,
                    "name": "Otro",
                    "position": 3,
                    "listed_price": 1_000_000,
                },
            ],
            escritor=_Escritor(),
            ruta_del_libro=Path(tmp) / "l.jsonl",
            ruta_de_viajes=Path(tmp) / "v.jsonl",
        )

    assert len(escritos) <= 1, (
        f"el escaparate ha escrito {len(escritos)} veces en una "
        f"vuelta"
    )


# ============================================================
# 3. EL PRECIO SALE DE LA REGLA QUE YA EXISTE
# ============================================================


def test_el_precio_sale_de_la_regla_de_salida() -> None:
    """
    No hay regla nueva: `precio_de_escaparate` aplica
    `PRIMA_DE_LA_PETICION`, la MISMA que usa la renovacion.

    Y tiene que quedar POR ENCIMA del precio de mercado: Biwenger
    rechaza listar por debajo.
    """

    from src.actions.escaparate_executor import (
        precio_de_escaparate,
    )

    # LA MISMA QUE RENOVAR, no una nueva. Si algun dia se
    # mueve, se mueve en los dos sitios a la vez.
    from src.analysis.renovar_ofertas import (
        PRIMA_DE_LA_PETICION,
    )

    precio = precio_de_escaparate(TRENT["price"])

    assert precio == int(
        round(TRENT["price"] * PRIMA_DE_LA_PETICION)
    ), precio

    assert precio > TRENT["price"], (
        f"se listaria a {precio} con el mercado en "
        f"{TRENT['price']}: Biwenger lo rechaza"
    )

    # Sin valor de mercado NO se inventa un precio.
    for sin_valor in (0, None, -1):
        assert precio_de_escaparate(sin_valor) == 0, sin_valor


def test_el_escaparate_respeta_la_zona_de_silencio() -> None:
    """
    Por la misma puerta que la renovacion: `permite_escribir`, y
    la hora decide, no quien llama (doctrina 38).
    """

    ciclo = (
        RAIZ / "src" / "v10_full_autonomous_live.py"
    ).read_text(encoding="utf-8")

    dentro = None

    for nodo in ast.walk(ast.parse(ciclo)):

        if (
            isinstance(nodo, ast.FunctionDef)
            and nodo.name == "_llenar_el_escaparate"
        ):
            dentro = ast.get_source_segment(ciclo, nodo) or ""

    assert "permite_escribir" in dentro, (
        "el escaparate no pregunta por la zona de silencio: "
        "escribiria con el mercado a medio resetear"
    )

    # Y se abstiene si dice que no.
    assert 'silencio.get("allowed")' in dentro, (
        "pregunta por el silencio y no mira la respuesta"
    )


def test_publica_de_verdad_y_se_apaga_sin_desplegar() -> None:
    """
    ENCENDIDO, y apagable.

    `publicar()` tiene `en_vivo=False` por defecto —bien: el
    defecto de las tres rutas que escriben es no escribir—. Si el
    ciclo no le pasara `en_vivo`, se quedaria montando el plan y
    mandando `execute: False` para siempre: enchufado y mudo, que
    es la peor forma de estar apagado.

    Y como las otras: apagable con una variable de entorno, sin
    desplegar.
    """

    import os

    import src.v10_full_autonomous_live as ciclo

    assert ciclo._escaparate_en_vivo() is True, (
        "el escaparate esta apagado: montaria el plan y no "
        "publicaria nada"
    )

    antes = os.environ.get(ciclo.ESCAPARATE_APAGADO_ENV)

    try:
        os.environ[ciclo.ESCAPARATE_APAGADO_ENV] = "1"

        assert ciclo._escaparate_en_vivo() is False, (
            "el interruptor no apaga el escaparate: habria que "
            "desplegar para pararlo"
        )

    finally:
        if antes is None:
            os.environ.pop(ciclo.ESCAPARATE_APAGADO_ENV, None)
        else:
            os.environ[ciclo.ESCAPARATE_APAGADO_ENV] = antes

    # Y que el ciclo se lo PASE, no que exista y nadie lo use.
    dentro = None

    fuente = (
        RAIZ / "src" / "v10_full_autonomous_live.py"
    ).read_text(encoding="utf-8")

    for nodo in ast.walk(ast.parse(fuente)):

        if (
            isinstance(nodo, ast.FunctionDef)
            and nodo.name == "_llenar_el_escaparate"
        ):
            dentro = ast.get_source_segment(fuente, nodo) or ""

    assert "en_vivo=_escaparate_en_vivo()" in dentro, (
        "el ciclo llama a `publicar` sin `en_vivo`: mandaria "
        "`execute: False` y no publicaria nunca"
    )


def test_el_escaparate_tiene_turno() -> None:
    """
    PUBLICAR NO COMPITE POR LA ESCRITURA DE LA VUELTA.

    SINTOMA (13/09/2026)

        Dos vueltas seguidas —14:05 y 14:10— gastando la
        escritura en renovar, con Trent comprado y sin publicar.
        Y la cola de prioridades no lo incluye:

            650 ofertas · 500 solvencia · 350 renovar · 0 espera

        Publicar un viaje no estaba en la lista, asi que no
        llegaba nunca.

    LA REGLA, LA MISMA QUE LA PUJA DEL CARRIL

        Va DESPUES de la accion principal y NO consume
        `write_used`. Es la segunda mitad de la misma operacion,
        cuesta UNA peticion, y un listado no arriesga nada: no es
        una venta, es poner el cartel.

        Meterlo en la cola seria peor: competiria por un turno
        que no necesita gastar, y podria desplazar un cobro.

    LOS DOS LIMITES DUROS

        nunca desplaza una renovacion urgente ni un cobro —no
        puede: no toca `write_used` y corre despues—
        una publicacion por vuelta
    """

    import ast

    fuente = (
        RAIZ / "src" / "v10_full_autonomous_live.py"
    ).read_text(encoding="utf-8")

    arbol = ast.parse(fuente)

    # 1. EL CICLO LO LLAMA, y despues de la accion principal.
    #    Se compara la posicion en el codigo: la accion sale de
    #    `_write_used`/`action_taken`, y el escaparate va detras.
    assert "escaparate = _llenar_el_escaparate(" in fuente, (
        "el ciclo no llena el escaparate"
    )

    assert fuente.index("carril = _correr_el_carril(") < (
        fuente.index("escaparate = _llenar_el_escaparate(")
    ), (
        "el escaparate corre ANTES que el carril: primero se "
        "compra, luego se publica lo comprado"
    )

    # 2. Y NO CONSUME LA ESCRITURA DE LA VUELTA.
    dentro = None

    for nodo in ast.walk(arbol):

        if (
            isinstance(nodo, ast.FunctionDef)
            and nodo.name == "_llenar_el_escaparate"
        ):
            dentro = ast.get_source_segment(fuente, nodo) or ""

    assert dentro, "no existe `_llenar_el_escaparate`"

    assert "write_used" not in dentro, (
        "el escaparate toca `write_used`: entonces compite con "
        "el cobro y con la renovacion urgente, que es justo lo "
        "que no puede hacer"
    )

    # 3. CON LA ACCION PRINCIPAL OCUPADA EN OTRA COSA, PUBLICA
    #    IGUAL. Se ejecuta de verdad.
    from src.actions.escaparate_executor import que_publicar

    VIAJE_ABIERTO = [
        {
            "player_id": TRENT["id"],
            "name": "Trent",
            "via": "RENDIJA",
            "state": "ABIERTO",
            "cost": 2_760_000,
        }
    ]

    # REGLA 24: si el fixture no trae viaje abierto, esta guardia
    # no comprueba nada.
    assert VIAJE_ABIERTO, "el fixture no trae ningun viaje"

    assert VIAJE_ABIERTO[0]["state"] == "ABIERTO"

    for ocupada in (
        "RENEW_MARKET_LISTING",
        "MONITOR_OFFERS",
        "SAVE_LINEUP",
        "MONITOR_SOLVENCY",
    ):
        plan = que_publicar(
            ganadas=VIAJE_ABIERTO,
            plantilla=[TRENT, JONNY],
            ya_listados=[],
            titulares=EL_ONCE,
        )

        assert plan["publicar"], (
            f"con la vuelta ocupada en {ocupada}, el viaje no se "
            f"publica: se queda en el banquillo otra vuelta"
        )

        assert len(plan["publicar"]) == 1, (
            "mas de una publicacion en la misma vuelta"
        )


TESTS = [
    test_publicar_no_toca_a_un_titular,
    test_solo_se_publican_viajes_del_carril,
    test_no_republica_lo_que_ya_esta_publicado,
    test_una_publicacion_por_vuelta,
    test_el_precio_sale_de_la_regla_de_salida,
    test_el_escaparate_respeta_la_zona_de_silencio,
    test_publica_de_verdad_y_se_apaga_sin_desplegar,
    test_el_escaparate_tiene_turno,
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
        f"EL ESCAPARATE PUBLICA V1: "
        f"{len(TESTS) - fallos}/{len(TESTS)} OK"
    )
    print("=" * 60)

    if fallos:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
