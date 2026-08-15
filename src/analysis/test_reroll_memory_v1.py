"""
Regresion del defecto 8 de la auditoria del 15/08/2026.

SINTOMA
    reroll_count y best_offer_rejected se calculaban, se persistian y
    no los leia nadie. No habia tope de rechazos ni comparacion
    contra la mejor oferta historica.

    Jugador de 1.000.000. Ciclo 1 ofrece 970.000 (premium -3%,
    WEAK) -> reroll. Ciclo 2 ofrece 960.000 -> reroll. Ciclo 3:
    950.000... El motor no recordaba que ya habia rechazado algo
    mejor y acababa aceptando una oferta peor que la primera, o
    perdiendolas todas por caducidad.

    Ademas best_offer_rejected ni siquiera llegaba al disco: el
    tablero se construye siempre con persist_history=False.

ARREGLO - dos frenos complementarios
    MEMORIA: no se rechaza una oferta que iguale o supere la
    mejor vista por ese jugador. Si esta por debajo, si hay
    evidencia de que se puede mejorar.
    TOPE: maximo 3 rechazos por jugador, por si las ofertas
    oscilan y la memoria sola no converge.

Ejecutar:
    python -m src.analysis.test_reroll_memory_v1
"""

import inspect

from src.analysis.computer_offer_reroll_engine import (
    MAX_REROLLS_PER_PLAYER,
    record_reroll,
    reroll_block_reason,
)


# ============================================================
# MEMORIA
# ============================================================

def test_no_rechaza_si_iguala_su_mejor_marca() -> None:
    bloqueo = reroll_block_reason(
        {"reroll_count": 1, "best_offer_rejected": 970_000},
        970_000,
    )

    assert bloqueo is not None, (
        "REGRESION: rechaza una oferta igual a la que ya tiro. "
        "El reroll no ha mejorado nada."
    )
    assert bloqueo[0] == "KEEP_NO_IMPROVEMENT"

    print("  OK  no rechaza una oferta igual a su mejor marca")


def test_si_permite_rechazar_si_ha_mejorado() -> None:
    """
    Si el reroll SI funciono -la nueva oferta supera a la que
    tiramos- tiene sentido plantearse otro intento.
    """
    bloqueo = reroll_block_reason(
        {"reroll_count": 1, "best_offer_rejected": 970_000},
        1_050_000,
    )

    assert bloqueo is None, (
        "Si la oferta mejora lo rechazado, el reroll esta "
        "funcionando y se puede intentar otra vez."
    )

    print("  OK  si el reroll mejoro, permite otro intento")


def test_no_rechaza_si_ha_empeorado() -> None:
    """
    El nucleo del arreglo: tuvimos 970.000 y lo tiramos. Ahora
    nos ofrecen 900.000. Volver a rechazar es la espiral.
    """
    bloqueo = reroll_block_reason(
        {"reroll_count": 1, "best_offer_rejected": 970_000},
        900_000,
    )

    assert bloqueo is not None, (
        "REGRESION: la oferta empeoro respecto a lo que ya "
        "tiramos y aun asi se rechaza. Eso es la espiral."
    )
    assert bloqueo[0] == "KEEP_NO_IMPROVEMENT"

    print("  OK  si la oferta empeoro, no se vuelve a rechazar")


def test_sin_historial_no_bloquea() -> None:
    assert reroll_block_reason({}, 900_000) is None
    assert reroll_block_reason(
        {"reroll_count": 0, "best_offer_rejected": 0},
        900_000,
    ) is None

    print("  OK  la primera oferta de un jugador no se bloquea")


# ============================================================
# TOPE
# ============================================================

def test_el_tope_es_tres() -> None:
    assert MAX_REROLLS_PER_PLAYER == 3, (
        f"El tope acordado con el usuario era 3, no "
        f"{MAX_REROLLS_PER_PLAYER}."
    )

    print(f"  OK  tope de {MAX_REROLLS_PER_PLAYER} rechazos")


def test_el_tope_corta_aunque_la_oferta_sea_mala() -> None:
    """
    Tercer rechazo consumido: aunque la oferta haya mejorado y
    la memoria dejase pasar, el tope corta.
    """
    bloqueo = reroll_block_reason(
        {"reroll_count": 3, "best_offer_rejected": 970_000},
        1_200_000,
    )

    assert bloqueo is not None, (
        "REGRESION: se supera el tope de rechazos."
    )
    assert bloqueo[0] == "KEEP_REROLL_CAP_REACHED"

    print("  OK  al llegar al tope se deja de rechazar")


def test_por_debajo_del_tope_deja_pasar() -> None:
    for intentos in (0, 1, 2):
        bloqueo = reroll_block_reason(
            {
                "reroll_count": intentos,
                "best_offer_rejected": 970_000,
            },
            1_200_000,
        )

        assert bloqueo is None, (
            f"Con {intentos} rechazos aun deberia poder "
            f"rerollear."
        )

    print("  OK  con 0, 1 o 2 rechazos aun puede intentarlo")


def test_el_tope_manda_sobre_la_memoria() -> None:
    """
    Si se dan las dos condiciones, el motivo que se reporta debe
    ser el tope: es el freno duro.
    """
    bloqueo = reroll_block_reason(
        {"reroll_count": 5, "best_offer_rejected": 900_000},
        800_000,
    )

    assert bloqueo[0] == "KEEP_REROLL_CAP_REACHED"

    print("  OK  con ambos frenos activos manda el tope")


# ============================================================
# EL ESCENARIO DE LA AUDITORIA
# ============================================================

def test_la_espiral_descendente_se_corta() -> None:
    """
    970.000 -> 960.000 -> 950.000 -> 940.000.
    Antes rechazaba las cuatro. Ahora para.
    """
    estado = {"reroll_count": 0, "best_offer_rejected": 0}
    ofertas = [970_000, 960_000, 950_000, 940_000]

    rechazadas = []

    for importe in ofertas:
        bloqueo = reroll_block_reason(estado, importe)

        if bloqueo is None:
            rechazadas.append(importe)
            estado["reroll_count"] += 1
            estado["best_offer_rejected"] = max(
                estado["best_offer_rejected"],
                importe,
            )
        else:
            break

    assert len(rechazadas) == 1, (
        f"REGRESION: rechazo {len(rechazadas)} ofertas de la "
        f"espiral ({rechazadas}). Deberia parar tras la primera, "
        f"porque 960.000 ya esta por debajo de los 970.000 que "
        f"vio."
    )

    print(
        f"  OK  la espiral se corta tras rechazar solo "
        f"{rechazadas[0]:,}".replace(",", ".")
    )


# ============================================================
# PERSISTENCIA
# ============================================================

def test_record_reroll_guarda_el_importe() -> None:
    firma = inspect.signature(record_reroll)

    assert "amount" in firma.parameters, (
        "REGRESION: record_reroll no acepta el importe, asi que "
        "best_offer_rejected nunca llegaria al disco y la memoria "
        "seria inservible."
    )

    fuente = inspect.getsource(record_reroll)

    assert "best_offer_rejected" in fuente, (
        "REGRESION: record_reroll ya no persiste el maximo "
        "historico."
    )

    print("  OK  record_reroll persiste el mejor importe visto")


def test_el_ejecutor_pasa_el_importe() -> None:
    from src.actions import autopilot_executor

    fuente = inspect.getsource(
        autopilot_executor.execute_autopilot_decision
    )

    posicion = fuente.find("record_reroll(")

    assert posicion != -1, (
        "El ejecutor ya no registra los rechazos."
    )

    bloque = fuente[posicion:posicion + 400]

    assert "amount" in bloque, (
        "REGRESION: el ejecutor llama a record_reroll sin el "
        "importe. La memoria se quedaria vacia."
    )

    print("  OK  el ejecutor pasa el importe al historial")


# ============================================================

TESTS = [
    test_no_rechaza_si_iguala_su_mejor_marca,
    test_si_permite_rechazar_si_ha_mejorado,
    test_no_rechaza_si_ha_empeorado,
    test_sin_historial_no_bloquea,
    test_el_tope_es_tres,
    test_el_tope_corta_aunque_la_oferta_sea_mala,
    test_por_debajo_del_tope_deja_pasar,
    test_el_tope_manda_sobre_la_memoria,
    test_la_espiral_descendente_se_corta,
    test_record_reroll_guarda_el_importe,
    test_el_ejecutor_pasa_el_importe,
]


def main() -> None:
    print("=" * 60)
    print(" MEMORIA Y TOPE DE RECHAZOS (defecto 8)")
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
