"""
Regresion del defecto 3 de la auditoria del 15/08/2026.

SINTOMA
    La rama BUY_SPECULATION de autopilot_executor revalidaba
    saldo, presupuesto, propiedad y precio, pero NO comprobaba si
    ya teniamos una puja viva por el mismo jugador.

    Una puja no se resuelve hasta el cierre de mercado: hasta
    entonces el jugador sigue en el mercado, el saldo no se
    descuenta y el score no cambia. El mismo objetivo volvia a
    salir como executable_buys[0] en el ciclo siguiente, asi que
    el bot pujaba otra vez. Con ciclos de 30 minutos eso son ~15
    escrituras por noche sobre la misma puja.

    Ademas el presupuesto se deriva del saldo y no descuenta
    compromisos pendientes, asi que podian acumularse pujas por
    varios jugadores que sumasen mas que la caja.

ARREGLO
    find_own_pending_bid() detecta pujas SALIENTES vivas y la
    rama devuelve SPECULATION_BID_ALREADY_PENDING sin escribir.

NOTA SOBRE LA DIRECCION
    Se filtra por 'from' a proposito. En el snapshot real las
    ofertas entrantes llegan con from=None y las nuestras con
    from=<nuestro id>. find_existing_offer de live_bid_executor
    solo mira requestedPlayers, que puede confundir una oferta
    entrante con una puja propia.

Ejecutar:
    python -m src.analysis.test_bid_deduplication_v1
"""

from src.actions.autopilot_executor import (
    find_own_pending_bid,
    get_own_user_id,
)


NUESTRO_ID = 14175949
RIVAL_ID = 14151726


def _snapshot(ofertas: list) -> dict:
    """
    Reproduce la forma real del snapshot de Biwenger.
    """
    return {
        "league": {
            "user": {
                "id": NUESTRO_ID,
                "name": "Pepe Bordalas",
            },
        },
        "market": {
            "offers": ofertas,
        },
    }


def _oferta_entrante(player_id: int, offer_id: int) -> dict:
    """
    Computer u otro manager nos ofrece dinero por un jugador
    NUESTRO. En el snapshot real llegan con from=None.
    """
    return {
        "id": offer_id,
        "amount": 1_665_100,
        "status": "waiting",
        "type": "purchase",
        "from": None,
        "to": {"id": NUESTRO_ID, "name": "Pepe Bordalas"},
        "requestedPlayers": [player_id],
    }


def _puja_nuestra(
    player_id: int,
    offer_id: int,
    status: str = "waiting",
) -> dict:
    return {
        "id": offer_id,
        "amount": 1_390_000,
        "status": status,
        "type": "purchase",
        "from": NUESTRO_ID,
        "to": {"id": RIVAL_ID, "name": "Rival"},
        "requestedPlayers": [player_id],
    }


# ============================================================

def test_lee_nuestro_user_id() -> None:
    assert get_own_user_id(_snapshot([])) == NUESTRO_ID
    assert get_own_user_id({}) is None
    assert get_own_user_id({"league": {}}) is None

    print("  OK  extrae el user_id del snapshot")


def test_detecta_puja_propia_viva() -> None:
    """
    El caso real: puja viva por Hugo Gonzalez (31468).
    """
    snap = _snapshot([
        _puja_nuestra(31468, 4138078754),
    ])

    encontrada = find_own_pending_bid(snap, 31468)

    assert encontrada is not None, (
        "REGRESION: no detecta nuestra propia puja viva. "
        "El bot volveria a pujar por el mismo jugador."
    )
    assert encontrada["id"] == 4138078754

    print("  OK  detecta la puja propia viva")


def test_oferta_entrante_no_es_puja_propia() -> None:
    """
    Falso positivo que SI tendria find_existing_offer.
    """
    snap = _snapshot([
        _oferta_entrante(38194, 105480289),
    ])

    assert find_own_pending_bid(snap, 38194) is None, (
        "REGRESION: una oferta ENTRANTE se confundio con una "
        "puja nuestra. Eso bloquearia compras legitimas."
    )

    print("  OK  una oferta entrante no cuenta como puja propia")


def test_otro_jugador_no_bloquea() -> None:
    snap = _snapshot([
        _puja_nuestra(31468, 4138078754),
    ])

    assert find_own_pending_bid(snap, 99999) is None, (
        "REGRESION: una puja por otro jugador bloquea esta "
        "compra."
    )

    print("  OK  una puja por otro jugador no bloquea")


def test_puja_resuelta_no_bloquea() -> None:
    for estado in ("accepted", "rejected", "expired"):
        snap = _snapshot([
            _puja_nuestra(31468, 1, status=estado),
        ])

        assert find_own_pending_bid(snap, 31468) is None, (
            f"REGRESION: una puja en estado {estado} sigue "
            f"bloqueando. Nunca podriamos volver a pujar."
        )

    print("  OK  una puja ya resuelta no bloquea")


def test_mercado_real_completo() -> None:
    """
    Las 16 ofertas reales del snapshot del 14/08: 15 entrantes
    y una puja nuestra por el jugador 31468.
    """
    ofertas = [
        _oferta_entrante(pid, 100000 + i)
        for i, pid in enumerate([
            38194, 26271, 37898, 1599, 29661, 18178,
            17482, 38318, 9065, 41271, 41606, 32435,
            3159, 5771, 41605,
        ])
    ]
    ofertas.append(
        _puja_nuestra(31468, 4138078754)
    )

    snap = _snapshot(ofertas)

    assert find_own_pending_bid(snap, 31468) is not None, (
        "REGRESION: con el mercado real no detecta la puja."
    )

    bloqueados = [
        pid
        for pid in [
            38194, 26271, 37898, 1599, 29661, 18178,
            17482, 38318, 9065, 41271, 41606, 32435,
            3159, 5771, 41605,
        ]
        if find_own_pending_bid(snap, pid) is not None
    ]

    assert not bloqueados, (
        f"REGRESION: las ofertas entrantes de {bloqueados} se "
        f"tomaron por pujas nuestras."
    )

    print(
        "  OK  mercado real de 16 ofertas: solo 1 es puja propia"
    )


def test_formatos_raros_no_revientan() -> None:
    casos = [
        {},
        {"league": {"user": {"id": NUESTRO_ID}}},
        _snapshot([{"id": 1}]),
        _snapshot([{"id": 1, "from": {"id": NUESTRO_ID}}]),
        _snapshot([{
            "id": 1,
            "from": NUESTRO_ID,
            "requestedPlayers": [{"id": 31468}],
        }]),
        _snapshot([{
            "id": 1,
            "from": "no-numerico",
            "requestedPlayers": [31468],
        }]),
    ]

    for i, snap in enumerate(casos):
        try:
            find_own_pending_bid(snap, 31468)
        except Exception as error:
            raise AssertionError(
                f"REGRESION: caso {i} lanzo "
                f"{type(error).__name__}: {error}"
            )

    # El formato dict anidado si debe detectarse.
    anidado = _snapshot([{
        "id": 1,
        "from": {"id": NUESTRO_ID},
        "requestedPlayers": [{"id": 31468}],
    }])

    assert find_own_pending_bid(anidado, 31468) is not None, (
        "REGRESION: no detecta el formato con from y "
        "requestedPlayers anidados como diccionario."
    )

    print("  OK  formatos raros no revientan y el anidado se ve")


# ============================================================

TESTS = [
    test_lee_nuestro_user_id,
    test_detecta_puja_propia_viva,
    test_oferta_entrante_no_es_puja_propia,
    test_otro_jugador_no_bloquea,
    test_puja_resuelta_no_bloquea,
    test_mercado_real_completo,
    test_formatos_raros_no_revientan,
]


def main() -> None:
    print("=" * 60)
    print(" DEDUPLICACION DE PUJAS (defecto 3)")
    print("=" * 60)

    fallos = 0

    for test in TESTS:
        print(f"\n{test.__name__}")
        try:
            test()
        except AssertionError as error:
            fallos += 1
            print(f"  FALLO  {error}")

    print("\n" + "=" * 60)
    if fallos:
        print(f" {fallos}/{len(TESTS)} TESTS FALLIDOS")
        raise SystemExit(1)
    print(f" {len(TESTS)}/{len(TESTS)} TESTS OK")
    print("=" * 60)


if __name__ == "__main__":
    main()
