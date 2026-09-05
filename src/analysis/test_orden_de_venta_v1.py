"""
El orden de venta no puede romper la plantilla.

SINTOMA

    En la foto de produccion del 05/09/2026 a las 14:03 el saldo
    esta en -421.792 EUR, `pepe_now` dice "Prioridad: recuperar
    solvencia", hay doce ofertas sobre la mesa por 45.746.500 EUR
    y el motor de ofertas contesta, textualmente:

        "0 con signal accionable. Ninguna para cobrar ahora."

    Tres planes de solvencia calculados, ninguno ejecutado. El
    plan A es vender a Lucas Cepeda por 471.200 -no juega, no toca
    el once, deja el saldo en +49.408- y el motor de ofertas
    contesta HOLD_OFFER a esa misma oferta.

CAUSA

    Nadie decide el orden de venta. `sales_analyzer` puntua,
    `sale_intent` propone y se imprime en un terminal que no mira
    nadie, y `offer_decision_engine` reacciona oferta a oferta sin
    una cola detras.

CONSECUENCIA

    Un modulo que ordena ventas es la pieza mas peligrosa que se
    puede escribir en este repo:

        "Una compra mala cuesta dinero y se corrige; una venta
        mala te deja SIN el jugador, y en un fantasy no se
        recupera: se lo lleva otro."

    Asi que esta guardia no comprueba que la cola sea lista.
    Comprueba que no pueda hacer daño:

        - que no proponga a un intocable,
        - que PARARSE EN CUALQUIER PUNTO de la cola deje todas las
          posiciones por encima de su suelo,
        - que el orden sea el que dijo el dueño y no otro,
        - y que cada fila diga por que.
"""

from __future__ import annotations

import ast
import json

from pathlib import Path

from src.analysis.position_guardrail import (
    build_position_guardrail,
    validate_sale_set,
)

from src.analysis.sale_order import (
    BENCH_PERCENT,
    CARO_POR_PUNTO,
    NO_JUEGA,
    build_sale_order,
    euros_per_point,
)


FOTO = Path("diagnostico/status.json")

MODULO = Path("src/analysis/sale_order.py")


def _produccion():
    """
    La foto de PRODUCCION, no `data/` del repo.

    `data/` es un resto de desarrollo de agosto. Medir contra el
    ya costo una conclusion falsa el 09/09 -"el tablero de
    titularidad esta rancio"- que era solo el disco local.
    """

    if not FOTO.exists():
        return None

    return json.loads(FOTO.read_text(encoding="utf-8"))


def _cola_de_produccion():
    foto = _produccion()

    if not foto:
        return None

    return build_sale_order(
        (foto.get("roster") or {}).get("players") or [],
        lineup_ids=[
            p.get("id")
            for p in ((foto.get("lineup") or {}).get("players") or [])
        ],
        offers=foto.get("offers"),
    )


# ============================================================
# 1. LOS INTOCABLES
# ============================================================


def test_ningun_intocable_entra_en_la_cola() -> None:
    """
    "Que no me venda a Yamal ni haga locuras."
    """

    cola = _cola_de_produccion()

    if cola is None:
        return

    assert cola["available"], cola.get("reason")

    nombres = {f["name"] for f in cola["queue"]}

    for jugador in cola["excluded"]:
        assert jugador["name"] not in nombres, (
            f"{jugador['name']} esta apartado y ademas en la cola"
        )

    # Los cuatro casos concretos de esta plantilla.
    for quien in ("Yamal", "Djen", "Olasagasti"):
        assert not any(quien in n for n in nombres), (
            f"{quien} es intocable y esta en la cola de venta"
        )


def test_el_portero_titular_no_se_salva_por_accidente() -> None:
    """
    `untouchable_reason` protege al portero titular mirando
    `in_lineup`, y el roster del dashboard trae ese dato como
    `is_starter`. Sin normalizarlo, Dituro salia de la cola solo
    porque el suelo posicional lo bloqueaba — que es el accidente
    contra el que avisa el propio `sale_intent`.

    Tiene que estar APARTADO POR SER PORTERO, no bloqueado por el
    suelo.
    """

    cola = _cola_de_produccion()

    if cola is None:
        return

    apartado = next(
        (
            e
            for e in cola["excluded"]
            if "Dituro" in str(e["name"])
        ),
        None,
    )

    assert apartado is not None, (
        "el portero titular no aparece entre los que no se "
        "proponen"
    )

    assert "portero" in apartado["reason"].lower(), (
        f"el portero se aparta por el motivo equivocado: "
        f"{apartado['reason']}"
    )


def test_sin_escalon_conocido_no_se_vende() -> None:
    """
    Aqui la ausencia de dato se resuelve al reves que en el once:
    alinear a quien no conoces cuesta unos puntos; venderlo te
    deja sin el jugador.
    """

    cola = build_sale_order(
        [
            {
                "id": 1,
                "name": "Sin escalon",
                "position": 3,
                "price": 3_000_000,
                "points": 1,
                "hierarchy_value": None,
                "starter_probability": None,
            },
        ]
        + _relleno(6)
    )

    assert "Sin escalon" not in {f["name"] for f in cola["queue"]}


# ============================================================
# 2. LA COLA AGUANTA PREFIJOS
# ============================================================


def test_pararse_en_cualquier_punto_deja_el_once_en_pie() -> None:
    """
    El motivo de que esto sea una COLA y no una lista.

    Preguntar "¿puedo vender a Dituro?" da que si, y "¿puedo
    vender a Bayindir?" tambien. Preguntar "¿puedo vender a los
    dos?" tiene que dar que no.

    Aqui la pregunta es mas fuerte: vender a los `k` primeros,
    para CUALQUIER k, tiene que dejar todas las posiciones por
    encima del suelo.
    """

    foto = _produccion()

    if not foto:
        return

    jugadores = (foto.get("roster") or {}).get("players") or []

    titulares = [
        p.get("id")
        for p in ((foto.get("lineup") or {}).get("players") or [])
    ]

    cola = build_sale_order(
        jugadores,
        lineup_ids=titulares,
        offers=foto.get("offers"),
    )

    guardarrail = build_position_guardrail(
        [
            {**j, "in_lineup": bool(j.get("is_starter"))}
            for j in jugadores
        ],
        lineup_ids=titulares,
    )

    ids = [f["id"] for f in cola["queue"]]

    for k in range(1, len(ids) + 1):

        comprobacion = validate_sale_set(guardarrail, ids[:k])

        assert comprobacion.get("ok"), (
            f"vender a los {k} primeros de la cola rompe el suelo: "
            f"{comprobacion.get('reason')}"
        )


def test_el_bloqueado_no_se_cuela_mas_abajo() -> None:
    """
    Si meter al siguiente rompiera un suelo, se APARTA con el
    motivo. Bajarlo de puesto seria mentir sobre el orden: la
    cola dejaria de aguantar prefijos sin que nada lo dijera.
    """

    cola = _cola_de_produccion()

    if cola is None:
        return

    en_cola = {f["id"] for f in cola["queue"]}

    for bloqueado in cola["blocked"]:

        assert bloqueado["id"] not in en_cola, (
            f"{bloqueado['name']} esta bloqueado y en la cola"
        )

        assert bloqueado.get("blocked_reason"), (
            f"{bloqueado['name']} se bloquea sin decir por que"
        )


# ============================================================
# 3. EL ORDEN ES EL QUE DIJO EL DUEÑO
# ============================================================
#
#     El suelo por posicion aparta a los que sobran, asi que los
#     casos de orden necesitan plantilla de sobra: con cuatro
#     medios y un suelo de tres, la cola solo admite uno y no se
#     puede comprobar ningun orden.
#
#     Los de relleno van baratisimos por punto a proposito: asi
#     caen al final de su escalon y son ELLOS los que se lleva el
#     suelo, no los jugadores del caso.


def _relleno(cuantos: int, desde: int = 100) -> list:
    return [
        {
            "id": desde + i,
            "name": f"Relleno {i}",
            "position": 3,
            "price": 200_000,
            "points": 20,
            "hierarchy_value": 40,
            "starter_probability": 80.0,
            "is_starter": True,
        }
        for i in range(cuantos)
    ]



def test_primero_quien_no_juega() -> None:
    """
    "Primero quien no juega: un suplente no puntua, solo ocupa
    ficha y dinero."

    Es un ESCALON, no un sumando. Un titular carisimo por punto no
    sale antes que un suplente, aunque su numero sea peor.
    """

    cola = build_sale_order(
        [
            # Titular carisimo por punto: 2.000.000 el punto.
            {
                "id": 1,
                "name": "Titular caro",
                "position": 3,
                "price": 4_000_000,
                "points": 2,
                "hierarchy_value": 40,
                "starter_probability": 90.0,
                "is_starter": True,
            },
            # Suplente barato por punto: 50.000 el punto.
            {
                "id": 2,
                "name": "Suplente barato",
                "position": 3,
                "price": 500_000,
                "points": 10,
                "hierarchy_value": 25,
                "starter_probability": 20.0,
                "is_starter": False,
            },
        ]
        + _relleno(6)
    )

    primero = cola["queue"][0]

    assert primero["name"] == "Suplente barato", (
        f"sale primero {primero['name']}: el escalon de «no juega» "
        f"no manda sobre el coste por punto"
    )

    assert primero["tier"] == NO_JUEGA

    caro = next(f for f in cola["queue"] if f["name"] == "Titular caro")

    assert caro["tier"] == CARO_POR_PUNTO
    assert caro["order"] > primero["order"]


def test_dentro_del_escalon_manda_el_coste_por_punto() -> None:
    cola = build_sale_order(
        [
            {
                "id": 1,
                "name": "Barato",
                "position": 3,
                "price": 1_000_000,
                "points": 20,
                "hierarchy_value": 40,
                "starter_probability": 80.0,
                "is_starter": True,
            },
            {
                "id": 2,
                "name": "Caro",
                "position": 3,
                "price": 1_000_000,
                "points": 2,
                "hierarchy_value": 40,
                "starter_probability": 80.0,
                "is_starter": True,
            },
            {
                "id": 3,
                "name": "Medio",
                "position": 3,
                "price": 1_000_000,
                "points": 8,
                "hierarchy_value": 40,
                "starter_probability": 80.0,
                "is_starter": True,
            },
        ]
        + _relleno(6)
    )

    orden = [f["name"] for f in cola["queue"]]

    assert orden.index("Caro") < orden.index("Medio") < orden.index("Barato"), (
        f"el coste por punto no ordena dentro del escalon: {orden}"
    )


def test_el_que_cae_sale_antes_que_el_que_sube() -> None:
    """
    "El que viene subiendo es el que conviene retener, y el que
    cae se vende antes de que caiga mas."

    Con r=+0,90 de autocorrelacion diaria, eso esta medido, no
    supuesto.
    """

    cola = build_sale_order(
        [
            {
                "id": 1,
                "name": "Sube",
                "position": 3,
                "price": 1_000_000,
                "points": 10,
                "price_increment": 50_000,
                "hierarchy_value": 40,
                "starter_probability": 80.0,
                "is_starter": True,
            },
            {
                "id": 2,
                "name": "Cae",
                "position": 3,
                "price": 1_000_000,
                "points": 10,
                "price_increment": -50_000,
                "hierarchy_value": 40,
                "starter_probability": 80.0,
                "is_starter": True,
            },
        ]
        + _relleno(6)
    )

    orden = [f["name"] for f in cola["queue"]]

    assert orden.index("Cae") < orden.index("Sube"), (
        f"el que cae no sale antes que el que sube: {orden}"
    )


def test_el_suplente_al_noventa_por_ciento_si_juega() -> None:
    """
    Un suplente con el pronostico al 90 % esta a punto de entrar.
    Meterlo en el escalon de «no juega» seria vender al que va a
    jugar el domingo.
    """

    cola = build_sale_order(
        [
            {
                "id": 1,
                "name": "Suplente que entra",
                "position": 3,
                "price": 1_000_000,
                "points": 1,
                "hierarchy_value": 40,
                "starter_probability": 90.0,
                "is_starter": False,
            },
            {
                "id": 2,
                "name": "Suplente de verdad",
                "position": 3,
                "price": 1_000_000,
                "points": 10,
                "hierarchy_value": 25,
                "starter_probability": BENCH_PERCENT - 1,
                "is_starter": False,
            },
        ]
        + _relleno(6)
    )

    por_nombre = {f["name"]: f for f in cola["queue"]}

    assert por_nombre["Suplente que entra"]["tier"] == CARO_POR_PUNTO
    assert por_nombre["Suplente de verdad"]["tier"] == NO_JUEGA


# ============================================================
# 4. CADA FILA DICE POR QUE
# ============================================================


def test_toda_fila_lleva_su_motivo() -> None:
    cola = _cola_de_produccion()

    if cola is None:
        return

    for fila in cola["queue"]:
        assert fila.get("reason"), (
            f"{fila['name']} entra en la cola sin motivo"
        )
        assert len(fila["reason"]) > 20, (
            f"el motivo de {fila['name']} no explica nada: "
            f"{fila['reason']}"
        )

    for fila in cola["excluded"]:
        assert fila.get("reason"), (
            f"{fila['name']} se aparta sin motivo"
        )


def test_la_coma_de_los_miles_no_se_come_la_de_la_frase() -> None:
    """
    `.replace(",", ".")` sobre la frase entera dejaba escrito
    "si hay que vender. antes que despues". El separador se
    formatea aparte.
    """

    cola = _cola_de_produccion()

    if cola is None:
        return

    for fila in cola["queue"]:
        assert "vender. antes" not in fila["reason"], (
            f"la coma de los miles se comio la de la frase: "
            f"{fila['reason']}"
        )


def test_sin_puntos_no_se_inventa_un_coste() -> None:
    """
    Cero puntos no es coste infinito ni coste cero: es que no se
    sabe. Se ordena aparte y se dice.
    """

    assert euros_per_point(
        {"price": 1_000_000, "points": 0}
    ) is None

    assert euros_per_point(
        {"price": 0, "points": 10}
    ) is None

    assert euros_per_point(
        {"price": 1_000_000, "points": 10}
    ) == 100_000


# ============================================================
# 5. LA CAJA QUE PROMETE ES LA QUE PUEDE DAR
# ============================================================


def test_la_caja_de_un_ciclo_es_una_venta_no_la_suma() -> None:
    """
    Solo se ejecuta una accion por ciclo. Sumar las doce ofertas
    y llamarlo "caja en un ciclo" seria prometer en media hora lo
    que tardaria cinco ciclos — y esa promesa es justo la que
    sostiene una deuda.
    """

    cola = _cola_de_produccion()

    if cola is None:
        return

    if not cola["queue"]:
        return

    con_oferta = [
        f for f in cola["queue"] if f["cash_kind"] == "OFERTA_VIVA"
    ]

    if len(con_oferta) < 2:
        return

    assert cola["cash_one_cycle"] == con_oferta[0]["cash_now"], (
        "la caja de un ciclo no es la primera venta de la cola"
    )

    assert cola["cash_one_cycle"] < cola["cash_on_the_table"], (
        "la caja de un ciclo se esta calculando como la suma de "
        "todas las ofertas"
    )


def test_se_distingue_la_oferta_viva_del_precio_de_mercado() -> None:
    """
    Una oferta sobre la mesa es caja en este ciclo. Sin oferta hay
    que publicarlo y esperar a que alguien lo compre, que no es lo
    mismo ni tarda lo mismo.
    """

    cola = _cola_de_produccion()

    if cola is None:
        return

    for fila in cola["queue"]:

        assert fila["cash_kind"] in ("OFERTA_VIVA", "A_MERCADO")

        if fila["cash_kind"] == "A_MERCADO":
            assert fila["cash_now"] == 0, (
                f"{fila['name']} no tiene oferta y aun asi promete "
                f"caja inmediata"
            )


# ============================================================
# 6. OBSERVADOR, Y SIN REIMPLEMENTAR LO QUE YA MANDA
# ============================================================


def test_el_modulo_no_vende() -> None:
    """
    No importa ningun executor, no escribe en disco y no llama a
    ningun cliente de escritura.
    """

    arbol = ast.parse(MODULO.read_text(encoding="utf-8"))

    prohibidos = (
        "autopilot_executor",
        "write_client",
        "BiwengerWriteClient",
        "accept_offer",
        "reject_offer",
    )

    for nodo in ast.walk(arbol):

        if isinstance(nodo, (ast.Import, ast.ImportFrom)):

            texto = ast.dump(nodo)

            for prohibido in prohibidos:
                assert prohibido not in texto, (
                    f"`sale_order` importa {prohibido}: deja de ser "
                    f"un observador"
                )

        if isinstance(nodo, ast.Call):

            objetivo = getattr(nodo.func, "attr", None)

            assert objetivo not in ("write_text", "write_bytes", "dump"), (
                "`sale_order` escribe en disco"
            )


def test_no_reimplementa_los_intocables_ni_el_suelo() -> None:
    """
    Una segunda copia de la regla de los intocables es una copia
    que se queda atras el dia que el dueño cambie de idea.
    """

    fuente = MODULO.read_text(encoding="utf-8")

    assert "from src.analysis.sale_intent import untouchable_reason" in fuente, (
        "no reutiliza la regla de los intocables"
    )

    assert "validate_sale_set" in fuente, (
        "no reutiliza la validacion del suelo por posicion"
    )

    arbol = ast.parse(fuente)

    definidas = {
        n.name
        for n in ast.walk(arbol)
        if isinstance(n, ast.FunctionDef)
    }

    for copia in ("untouchable_reason", "validate_sale_set",
                  "build_position_guardrail"):
        assert copia not in definidas, (
            f"`sale_order` redefine {copia} en vez de llamarlo"
        )


TESTS = [
    test_ningun_intocable_entra_en_la_cola,
    test_el_portero_titular_no_se_salva_por_accidente,
    test_sin_escalon_conocido_no_se_vende,
    test_pararse_en_cualquier_punto_deja_el_once_en_pie,
    test_el_bloqueado_no_se_cuela_mas_abajo,
    test_primero_quien_no_juega,
    test_dentro_del_escalon_manda_el_coste_por_punto,
    test_el_que_cae_sale_antes_que_el_que_sube,
    test_el_suplente_al_noventa_por_ciento_si_juega,
    test_toda_fila_lleva_su_motivo,
    test_la_coma_de_los_miles_no_se_come_la_de_la_frase,
    test_sin_puntos_no_se_inventa_un_coste,
    test_la_caja_de_un_ciclo_es_una_venta_no_la_suma,
    test_se_distingue_la_oferta_viva_del_precio_de_mercado,
    test_el_modulo_no_vende,
    test_no_reimplementa_los_intocables_ni_el_suelo,
]


def main() -> None:
    fallos = 0

    for test in TESTS:
        try:
            test()
            print(f"OK   {test.__name__}")
        except AssertionError as exc:
            fallos += 1
            print(f"FALLA {test.__name__}: {exc}")

    print("=" * 60)
    print(f"ORDEN DE VENTA V1: {len(TESTS) - fallos}/{len(TESTS)} OK")
    print("=" * 60)

    if fallos:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
