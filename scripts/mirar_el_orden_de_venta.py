"""
MIRAR la cola de venta contra la foto de produccion de ahora.

ESTO NO ES UNA GUARDIA, Y POR ESO YA NO VIVE ENTRE ELLAS

    Estas ocho comprobaciones vivian en
    `src/analysis/test_orden_de_venta_v1.py` y leian
    `diagnostico/status.json`, que NO esta versionado: lo rehace
    cada vuelta de produccion.

    El 20/09/2026 una de ellas se puso roja sin que cambiara una
    linea de codigo:

        `test_el_portero_titular_no_se_salva_por_accidente`
        buscaba a DITURO por su nombre. A las 08:55 lo vendimos
        —2.188.300 EUR, evento `transfer` del tablon— y a las
        09:16 la foto se rehizo sin el. Verde a las 09:00, roja a
        las 09:20, mismo commit.

    Es la misma familia que `mirar_accept_before_expiry`: una
    comprobacion que falla por el estado del mundo no protege
    nada, enseña a ignorar el rojo (doctrina 91), y rompe la
    regla de la casa desde el primer dia.

Y HABIA UN SEGUNDO PROBLEMA, PEOR

    Las ocho empiezan por `if cola is None: return`. En CI, donde
    `diagnostico/` no existe, PASABAN SIN MIRAR NADA. Asi que
    daban rojos que no significaban un fallo en el portatil y
    verdes que no significaban nada en el servidor.

    Aqui eso deja de ser un problema: un mirador que no encuentra
    la foto lo DICE y sale por la puerta de atras, que es lo
    honesto para una herramienta que se corre a mano.

LO QUE SIGUE CUBIERTO CON DATOS FIJOS, EN LA VERJA

    Las once pruebas que se quedan en
    `test_orden_de_venta_v1` no tocan produccion: el orden de la
    cola, el suelo por posicion, el coste por punto, que el
    modulo no venda y que no reimplemente los intocables. Son las
    que protegen de verdad, porque protegen del codigo.

USO

    python scripts/mirar_el_orden_de_venta.py

    Solo lectura. No escribe en Biwenger ni en ningun libro.
"""

from __future__ import annotations

import json
import sys

from pathlib import Path


RAIZ = Path(__file__).resolve().parents[1]

if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from src.analysis.position_guardrail import (        # noqa: E402
    build_position_guardrail,
    validate_sale_set,
)

from src.analysis.sale_order import (                # noqa: E402
    build_sale_order,
)


FOTO = RAIZ / "diagnostico" / "status.json"


def _produccion():
    """
    La foto de PRODUCCION, no `data/` del repo.

    `data/` es un resto de desarrollo de agosto. Medir contra el
    ya costo una conclusion falsa el 09/09 —"el tablero de
    titularidad esta rancio"— que era solo el disco local.
    """

    if not FOTO.exists():
        return None

    try:
        return json.loads(FOTO.read_text(encoding="utf-8"))

    except (OSError, ValueError):
        return None


def _cola_de_produccion(foto):
    return build_sale_order(
        (foto.get("roster") or {}).get("players") or [],
        lineup_ids=[
            p.get("id")
            for p in ((foto.get("lineup") or {}).get("players") or [])
        ],
        offers=foto.get("offers"),
    )


# ============================================================
# LAS OCHO
# ============================================================
#
#     Cada una devuelve la lista de lo que no cuadra. Ninguna
#     lanza: un mirador que revienta a la tercera no enseña las
#     otras cinco.


def el_apartado_no_esta_ademas_en_la_cola(foto, cola) -> list:
    """O se vende o no se vende, pero no las dos cosas."""

    fallos = []

    if not cola["available"]:
        return [f"la cola no esta disponible: {cola.get('reason')}"]

    nombres = {f["name"] for f in cola["queue"]}

    for jugador in cola["excluded"]:
        if jugador["name"] in nombres:
            fallos.append(
                f"{jugador['name']} esta apartado y ademas en la cola"
            )

    return fallos


def el_portero_titular_no_se_salva_por_accidente(foto, cola) -> list:
    """
    `untouchable_reason` protege al portero titular mirando
    `in_lineup`, y el roster trae ese dato como `is_starter`. Sin
    normalizarlo, el portero salia de la cola solo porque el
    suelo posicional lo bloqueaba — que es el accidente contra el
    que avisa el propio `sale_intent`.

    SE PREGUNTA POR EL PUESTO, NO POR EL NOMBRE (20/09/2026)

        Aqui ponia «Dituro». Lo vendimos y esto se puso rojo sin
        que cambiara el codigo. Un nombre propio en una
        comprobacion es una fecha de caducidad que nadie apunto.
    """

    titular = next(
        (
            p
            for p in ((foto.get("roster") or {}).get("players") or [])
            if p.get("position") == 1 and p.get("is_starter")
        ),
        None,
    )

    if titular is None:
        return ["no hay portero titular en la foto: nada que mirar"]

    apartado = next(
        (
            e
            for e in cola["excluded"]
            if e.get("id") == titular.get("id")
        ),
        None,
    )

    if apartado is None:
        return [
            f"el portero titular ({titular.get('name')}) no aparece "
            f"entre los que no se proponen"
        ]

    if "portero" not in str(apartado.get("reason", "")).lower():
        return [
            f"el portero {titular.get('name')} se aparta por el "
            f"motivo equivocado: {apartado.get('reason')}"
        ]

    return []


def pararse_en_cualquier_punto_deja_el_once_en_pie(foto, cola) -> list:
    """
    El motivo de que esto sea una COLA y no una lista: vender a
    los `k` primeros, para CUALQUIER k, tiene que dejar todas las
    posiciones por encima del suelo.
    """

    jugadores = (foto.get("roster") or {}).get("players") or []

    titulares = [
        p.get("id")
        for p in ((foto.get("lineup") or {}).get("players") or [])
    ]

    guardarrail = build_position_guardrail(
        [
            {**j, "in_lineup": bool(j.get("is_starter"))}
            for j in jugadores
        ],
        lineup_ids=titulares,
    )

    ids = [f["id"] for f in cola["queue"]]

    fallos = []

    for k in range(1, len(ids) + 1):

        comprobacion = validate_sale_set(guardarrail, ids[:k])

        if not comprobacion.get("ok"):
            fallos.append(
                f"vender a los {k} primeros de la cola rompe el "
                f"suelo: {comprobacion.get('reason')}"
            )

    return fallos


def el_bloqueado_no_se_cuela_mas_abajo(foto, cola) -> list:
    """
    Si meter al siguiente rompiera un suelo, se APARTA con el
    motivo. Bajarlo de puesto seria mentir sobre el orden.
    """

    fallos = []

    en_cola = {f["id"] for f in cola["queue"]}

    for bloqueado in cola["blocked"]:

        if bloqueado["id"] in en_cola:
            fallos.append(
                f"{bloqueado['name']} esta bloqueado y en la cola"
            )

        if not bloqueado.get("blocked_reason"):
            fallos.append(
                f"{bloqueado['name']} se bloquea sin decir por que"
            )

    return fallos


def toda_fila_lleva_su_motivo(foto, cola) -> list:

    fallos = []

    for fila in cola["queue"]:

        if not fila.get("reason"):
            fallos.append(
                f"{fila['name']} entra en la cola sin motivo"
            )

        elif len(fila["reason"]) <= 20:
            fallos.append(
                f"el motivo de {fila['name']} no explica nada: "
                f"{fila['reason']}"
            )

    for fila in cola["excluded"]:
        if not fila.get("reason"):
            fallos.append(f"{fila['name']} se aparta sin motivo")

    return fallos


def la_coma_de_los_miles_no_se_come_la_de_la_frase(foto, cola) -> list:
    """
    `.replace(",", ".")` sobre la frase entera dejaba escrito
    "si hay que vender. antes que despues".
    """

    return [
        f"la coma de los miles se comio la de la frase: "
        f"{fila['reason']}"
        for fila in cola["queue"]
        if "vender. antes" in str(fila.get("reason", ""))
    ]


def la_caja_de_un_ciclo_es_una_venta_no_la_suma(foto, cola) -> list:
    """
    Solo se ejecuta una accion por ciclo. Sumar las doce ofertas
    y llamarlo "caja en un ciclo" seria prometer en media hora lo
    que tardaria cinco ciclos.
    """

    con_oferta = [
        f for f in cola["queue"]
        if f["cash_kind"] == "OFERTA_VIVA"
    ]

    if len(con_oferta) < 2:
        return [
            f"solo {len(con_oferta)} oferta(s) viva(s): el caso no "
            f"se puede mirar hoy"
        ]

    fallos = []

    if cola["cash_one_cycle"] != con_oferta[0]["cash_now"]:
        fallos.append(
            "la caja de un ciclo no es la primera venta de la cola"
        )

    if cola["cash_one_cycle"] >= cola["cash_on_the_table"]:
        fallos.append(
            "la caja de un ciclo se esta calculando como la suma "
            "de todas las ofertas"
        )

    return fallos


def se_distingue_la_oferta_viva_del_precio_de_mercado(
    foto, cola
) -> list:
    """
    Una oferta sobre la mesa es caja en este ciclo. Sin oferta hay
    que publicarlo y esperar, que no es lo mismo ni tarda lo
    mismo.
    """

    fallos = []

    for fila in cola["queue"]:

        if fila["cash_kind"] not in ("OFERTA_VIVA", "A_MERCADO"):
            fallos.append(
                f"{fila['name']} tiene una clase de caja "
                f"desconocida: {fila['cash_kind']}"
            )

        elif (
            fila["cash_kind"] == "A_MERCADO"
            and fila["cash_now"] != 0
        ):
            fallos.append(
                f"{fila['name']} no tiene oferta y aun asi promete "
                f"caja inmediata"
            )

    return fallos


LAS_OCHO = (
    el_apartado_no_esta_ademas_en_la_cola,
    el_portero_titular_no_se_salva_por_accidente,
    pararse_en_cualquier_punto_deja_el_once_en_pie,
    el_bloqueado_no_se_cuela_mas_abajo,
    toda_fila_lleva_su_motivo,
    la_coma_de_los_miles_no_se_come_la_de_la_frase,
    la_caja_de_un_ciclo_es_una_venta_no_la_suma,
    se_distingue_la_oferta_viva_del_precio_de_mercado,
)


def main() -> int:

    print("=" * 78)
    print("MIRAR EL ORDEN DE VENTA, contra la foto de produccion")
    print("=" * 78)

    foto = _produccion()

    if foto is None:
        print(f"  No hay foto de produccion en {FOTO}.")
        print("  Esto no es un fallo: es que no hay nada que mirar.")
        print("=" * 78)
        return 0

    print(f"  Foto: {(foto.get('meta') or {}).get('generated_at')}")

    cola = _cola_de_produccion(foto)

    print(
        f"  Cola: {len(cola.get('queue') or [])} en la cola, "
        f"{len(cola.get('excluded') or [])} apartados, "
        f"{len(cola.get('blocked') or [])} bloqueados."
    )
    print()

    total = 0

    for comprobacion in LAS_OCHO:

        try:
            fallos = comprobacion(foto, cola)

        except Exception as error:                  # noqa: BLE001
            fallos = [
                f"reviento: {type(error).__name__}: {error}"
            ]

        total += len(fallos)

        print(
            f"  {'OK  ' if not fallos else 'MIRA'}  "
            f"{comprobacion.__name__}"
        )

        for fallo in fallos:
            print(f"          {fallo}")

    print()
    print("=" * 78)
    print(
        f"EL ORDEN DE VENTA, EN PRODUCCION: "
        f"{len(LAS_OCHO) - total if total <= len(LAS_OCHO) else 0}"
        f"/{len(LAS_OCHO)} sin nada que mirar"
    )
    print("=" * 78)

    # Un mirador NO devuelve error por el estado del mundo: lo
    # enseña. Quien lo corre decide si lo que ve le preocupa.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
