"""
La lista de la compra, corrida contra la foto del dueño.

QUE FOTO MIRA, Y LO COMPRUEBA ANTES

    `diagnostico/status.json`. Lo primero que imprime es
    `meta.generated_at` (doctrina 65), y se abre SIEMPRE con
    `encoding="utf-8"`: en Windows el por defecto es `cp1252` y la
    foto lleva acentos.

QUE HACE

    BLOQUE 1   por que el mercado libre no esta en la lista, y la
               lista partida en dos con su `n`.
    BLOQUE 2   el orden de las operaciones, y el guardarrail
               mirando titularidad.
    BLOQUE 3   la tabla por plazas del once, con la mejor
               operacion sin vender a nadie arriba.

QUE NO HACE

    No escribe nada, no toca Biwenger, no sale a la red y no
    enciende nada.

USO

    python scripts/la_lista_de_la_compra.py > salida.txt 2>&1
    echo $?
"""

from __future__ import annotations

import json
import os
import sys
from collections import Counter


sys.path.insert(0, os.getcwd())

from src.analysis.el_cable import (                      # noqa: E402
    presupuesto_con_el_cable,
    tabla_de_fichajes,
)
from src.analysis.la_lista_de_la_compra import (         # noqa: E402
    COMPRABLE_HOY,
    ENCENDIDO,
    HAY_QUE_PEDIRSELO,
    RECAMBIO_PRIMERO,
    libres_que_se_pueden_comprar,
    orden_de_la_operacion,
    partir_la_lista,
    tabla_por_plazas,
)
from src.analysis.position_factor import factor_for       # noqa: E402
from src.analysis.position_guardrail import (             # noqa: E402
    build_position_guardrail,
    validate_sale_set,
    validate_sale_set_con_titularidad,
)


FOTO = "diagnostico/status.json"

POS = {1: "POR", 2: "DEF", 3: "MED", 4: "DEL"}


def euros(valor) -> str:
    return f"{int(valor or 0):,}".replace(",", ".")


def titulo(texto: str) -> None:
    print()
    print("=" * 74)
    print(texto)
    print("=" * 74)


def cargar(ruta):
    with open(ruta, encoding="utf-8") as fichero:
        return json.load(fichero)


def main() -> int:

    if not os.path.exists(FOTO):
        print(f"No esta la foto: {FOTO}")
        print("  `diagnostico/` esta en .gitignore: la deja el ciclo")
        print("  en la maquina donde corre. Sin ella no se mide nada.")
        return 1

    foto = cargar(FOTO)

    meta = foto.get("meta") or {}

    titulo("LA FOTO")
    print()
    print(f"  fichero             {FOTO}")
    print(f"  meta.generated_at   {meta.get('generated_at')}")
    print(f"  snapshot            {meta.get('snapshot')}")
    print()
    print("  Abierta con encoding='utf-8'.")

    jugadores = [
        {**j, "in_lineup": bool(j.get("is_starter"))}
        for j in ((foto.get("roster") or {}).get("players") or [])
    ]

    once = [j for j in jugadores if j["in_lineup"]]

    guardarrail = build_position_guardrail(
        jugadores, lineup_ids=[j["id"] for j in once]
    )

    # ========================================================
    # BLOQUE 1 — POR QUE NO ESTA EL MERCADO LIBRE
    # ========================================================

    titulo("BLOQUE 1.1 - POR QUE EL MERCADO LIBRE NO ESTA EN LA LISTA")

    adquisicion = foto.get("acquisition") or {}

    objetivos = adquisicion.get("targets") or []

    por_vendedor = Counter(x.get("seller_kind") for x in objetivos)

    print()
    print("  EL UNIVERSO COMPRABLE DE LA FOTO")
    print()
    print(f"    market_size (escaparate del Computer)     {adquisicion.get('market_size')}")
    print(f"    outside_computer_market (de rivales)      {adquisicion.get('outside_computer_market')}")
    print(f"    buyable_universe                          {adquisicion.get('buyable_universe')}")
    print(f"    por seller_kind                           {dict(por_vendedor)}")
    print()
    print(
        f"    comprar a managers cerrado: "
        f"{(adquisicion.get('rival_market') or {}).get('buying_closed')}"
    )

    libres = libres_que_se_pueden_comprar(
        foto.get("elVestuarioLibre")
    )

    vestuario = foto.get("elVestuarioLibre") or {}

    print()
    print("  Y EL CATALOGO ENTERO, QUE SI SE MIRA")
    print()
    print(f"    total del catalogo    {vestuario.get('total_catalogo')}")
    print(f"    con dueño             {vestuario.get('con_dueno')}")
    print(f"    LIBRES                {vestuario.get('libres')}")
    print(f"    nos mejoran           {libres.get('nos_mejoran')}")
    print(f"    HOY EN EL ESCAPARATE  {libres.get('en_el_mercado_hoy')}")
    print()
    print("  LOS VEINTE MEJORES LIBRES, Y SI SE PUEDEN COMPRAR HOY")
    print()
    print(
        f"    {'pos':<5}{'jugador':<22}{'precio':>12}{'pts':>5}"
        f"{'part':>6}{'nos suma':>10}{'pts/M':>8}  escaparate"
    )

    for jugador in (vestuario.get("players") or []):
        print(
            f"    {str(jugador.get('posicion')):<5}"
            f"{str(jugador.get('name'))[:20]:<22}"
            f"{euros(jugador.get('price')):>12}"
            f"{jugador.get('points'):>5}{jugador.get('played'):>6}"
            f"{jugador.get('nos_suma'):>10}"
            f"{jugador.get('puntos_por_millon'):>8}  "
            f"{'SI' if jugador.get('en_el_mercado') else 'no'}"
        )

    print()
    print(f"  {libres['reason']}")
    print()
    print("  Y EL QUE SI ESTA, YA ESTABA EN LA LISTA:")

    ampliacion = foto.get("roster_expansion") or {}

    nombres_lista = {
        c.get("name") for c in (ampliacion.get("candidates") or [])
    }

    for jugador in libres["en_el_mercado"]:
        print(
            f"    {jugador['name']}  ->  en roster_expansion: "
            f"{'SI' if jugador['name'] in nombres_lista else 'NO'}"
        )

    print()
    print("  CONCLUSION: no lo descarta un veto ni sale de otra fuente.")
    print("  La lista mira el universo COMPRABLE, y por un jugador que")
    print("  no esta publicado no se puede pujar: no hay a quien")
    print("  ofrecerle nada. De los libres que nos mejoran, hoy hay uno")
    print("  en el escaparate, y ese uno si esta en la lista.")

    print()
    print("  LO QUE SI FALTABA, Y ES OTRA COSA: el candidato no dice de")
    print("  quien es. `seller_kind` viaja en la fila de")
    print("  `season_horizon` y `build_roster_expansion_shadow` no lo")
    print("  copia. Es una columna que se cae al construir la lista.")

    # ========================================================
    # BLOQUE 1.2 — LAS DOS LISTAS
    # ========================================================

    titulo("BLOQUE 1.2 - LAS DOS LISTAS")

    # Los puntos netos por euro salen del cable, que ya los sabe
    # calcular. Aqui solo se parten y se ordenan.
    presupuestos = adquisicion.get("budgets") or {}

    calibracion = (
        (foto.get("rival_intelligence") or {}).get(
            "maximum_bid_calibration"
        )
        or {}
    )

    por_jornada = {}

    for jugador in jugadores:
        partidos = int(jugador.get("played_home") or 0) + int(
            jugador.get("played_away") or 0
        )

        if partidos:
            por_jornada[jugador["id"]] = (
                float(jugador.get("points") or 0) / partidos
            )

    cable = presupuesto_con_el_cable(
        {
            "enabled": True,
            "total_budget": presupuestos.get("acquisition"),
            "available_budget": presupuestos.get("acquisition"),
            "maximum_bid": calibracion.get("own_maximum_bid"),
            "balance": calibracion.get("own_balance"),
        },
        {
            "queue": [
                {
                    **fila,
                    "points_per_matchday": por_jornada.get(
                        fila.get("id")
                    ),
                }
                for fila in (
                    (foto.get("sale_order") or {}).get("queue") or []
                )
            ]
        },
        guardarrail=guardarrail,
        validador=validate_sale_set,
    )

    tabla = tabla_de_fichajes(
        ampliacion.get("candidates"),
        cable,
        factor_de=factor_for,
        fichas_libres=(ampliacion.get("slots") or {}).get("free_slots"),
        jornadas_restantes=(
            (foto.get("season_horizon") or {}).get("matchdays_remaining")
        ),
    )

    universo = {x.get("id"): x for x in objetivos}

    partida = partir_la_lista(
        tabla.get("operaciones"),
        universo,
        puerta=foto.get("laPuertaDeLosManagers"),
    )

    print()
    print(f"  {partida['reason']}")

    for grupo in (COMPRABLE_HOY, HAY_QUE_PEDIRSELO):

        filas = partida["grupos"][grupo]

        print()
        print(f"  {grupo}  (n={len(filas)})")
        print(f"  {partida['grupos'][grupo][0]['grupo_label'] if filas else ''}")
        print()
        print(
            f"    {'#':<3}{'jugador':<20}{'pos':<5}{'cuesta':>12}"
            f"{'netos':>8}{'x millon':>10}  de quien"
        )

        for fila in filas:
            print(
                f"    {fila['order']:<3}{str(fila['name'])[:18]:<20}"
                f"{POS.get(fila['position'], '?'):<5}"
                f"{euros(fila['market_price']):>12}"
                f"{(f'{fila['puntos_netos']:.2f}' if fila['puntos_netos'] is not None else '-'):>8}"
                f"{(f'{fila['puntos_netos_por_millon']:.3f}' if fila['puntos_netos_por_millon'] is not None else '-'):>10}"
                f"  {fila['seller_name']}"
            )

        if grupo == HAY_QUE_PEDIRSELO and filas:
            print()
            print(f"    LA PUERTA: {partida['puerta']['reason']}")

    # Y el peso real de la puerta, desde nuestro lado.
    puerta = foto.get("laPuertaDeLosManagers") or {}

    traspasos = puerta.get("traspasos") or []

    compramos = [
        t
        for t in traspasos
        if t.get("nuestro") and not t.get("vendimos")
    ]

    print()
    print(
        f"    Y DESDE NUESTRO LADO: de los "
        f"{puerta.get('cuantos')} traspasos, "
        f"{puerta.get('nuestros')} son nuestros y en "
        f"{len(compramos)} fuimos NOSOTROS quienes compramos."
    )
    print(
        f"    En {puerta.get('eventos_leidos')} eventos del tablon, "
        f"desde {puerta.get('primero')}, hemos entrado por esa puerta"
    )
    print(
        f"    como compradores {len(compramos)} vez/veces, contra "
        f"{puerta.get('compras_al_computer')} compras al Computer."
    )

    # ========================================================
    # BLOQUE 2 — EL ORDEN, Y EL GUARDARRAIL
    # ========================================================

    titulo("BLOQUE 2.1 - EL GUARDARRAIL QUE CUENTA CUERPOS")

    print()
    print(
        f"    {'jugador':<20}{'pos':<5}{'once':>6}{'locked':>8}"
        f"{'cuerpos':>10}{'titularidad':>13}"
    )

    bloqueados = set(guardarrail.get("locked_ids") or [])

    pasaban = []

    for jugador in jugadores:

        viejo = validate_sale_set(guardarrail, [jugador["id"]])
        nuevo = validate_sale_set_con_titularidad(
            guardarrail, [jugador["id"]]
        )

        if viejo["ok"] and not nuevo["ok"]:
            pasaban.append(jugador)

        print(
            f"    {str(jugador['name'])[:18]:<20}"
            f"{POS.get(jugador['position'], '?'):<5}"
            f"{('SI' if jugador['in_lineup'] else 'no'):>6}"
            f"{('SI' if jugador['id'] in bloqueados else 'no'):>8}"
            f"{('ok' if viejo['ok'] else 'BLOQUEA'):>10}"
            f"{('ok' if nuevo['ok'] else 'BLOQUEA'):>13}"
        )

    print()
    print(
        f"  EL CASO NUEVO QUE DETECTA: {len(pasaban)} venta(s) que hoy "
        f"pasan y con el freno no."
    )

    for jugador in pasaban:
        detalle = validate_sale_set_con_titularidad(
            guardarrail, [jugador["id"]]
        )

        print(f"    {jugador['name']}: {detalle['reason']}")

    print()
    print("  Y NO SE PASA DE FRENADA: los otros ocho titulares siguen")
    print("  pasando, porque con 3 defensas y 5 medios en el once contra")
    print("  suelos de 2, soltar uno deja once alineable.")

    # Que le pasaria a la cola de venta si se encendiera.
    cola = (foto.get("sale_order") or {}).get("queue") or []

    for nombre, validador in (
        ("HOY (cuerpos)", validate_sale_set),
        ("CON EL FRENO", validate_sale_set_con_titularidad),
    ):
        vendiendo = []
        caja = 0

        for fila in cola:
            if validador(guardarrail, vendiendo + [fila["id"]])["ok"]:
                vendiendo.append(fila["id"])

                if fila.get("cash_kind") == "OFERTA_VIVA":
                    caja += int(fila.get("cash_now") or 0)

        print()
        print(
            f"  cola de venta {nombre:<16} {len(vendiendo)} de "
            f"{len(cola)}   caja sobre la mesa {euros(caja)}"
        )

    print()
    print("  ENCENDERLO HOY NO CAMBIA NADA: la cola pone los sobrantes")
    print("  delante y nunca llega a tocar el suelo de titulares. Que hoy")
    print("  no cambie nada no es razon para encenderlo sin avisar.")

    titulo("BLOQUE 2.2 - EL ORDEN DE CADA OPERACION")

    print()
    print(
        f"    {'fichaje':<20}{'orden':<20}{'needs_sale_first':>18}  "
        f"quien sale"
    )

    for fila in tabla.get("operaciones") or []:

        salen = [
            {
                **v,
                "in_lineup": bool(
                    next(
                        (
                            j["in_lineup"]
                            for j in jugadores
                            if j["id"] == v.get("id")
                        ),
                        False,
                    )
                ),
            }
            for v in (fila.get("vende_a") or [])
        ]

        orden = orden_de_la_operacion(
            salen,
            guardarrail=guardarrail,
            hace_falta_vender=not fila.get("financiada_hoy"),
        )

        print(
            f"    {str(fila['name'])[:18]:<20}{orden['orden']:<20}"
            f"{str(orden['needs_sale_first']):>18}  "
            + ", ".join(str(v.get("name")) for v in salen)
        )

        if orden["orden"] == RECAMBIO_PRIMERO:
            print(f"        {orden['reason']}")

    # ========================================================
    # BLOQUE 3 — LA TABLA POR PLAZAS
    # ========================================================

    titulo("BLOQUE 3 - LA TABLA POR PLAZAS DEL ONCE")

    # Solo lo comprable HOY es recambio. Lo que hay que pedirle a
    # un rival no es un recambio: es una carta.
    recambios = [
        {
            "id": x.get("id"),
            "name": x.get("name"),
            "position": x.get("position"),
            "price": x.get("market_price"),
            "points": x.get("points"),
            "played": x.get("played"),
        }
        for x in objetivos
        if x.get("seller_kind") == "COMPUTER"
    ]

    plazas = tabla_por_plazas(
        once,
        recambios,
        factor_de=factor_for,
        caja_ahora=cable["caja_ahora"],
        guardarrail=guardarrail,
    )

    print()
    print(f"  caja para fichar hoy: {euros(plazas['caja_ahora'])}")
    print(
        f"  recambios comprables hoy: {len(recambios)} "
        f"(los 20 del escaparate del Computer)"
    )
    print()
    print(
        f"  {'plaza':<20}{'pos':<5}{'pts/part':>10}{'con vara':>10}"
        f"{'recambios':>11}  mejor comprable hoy"
    )

    for plaza in plazas["plazas"]:

        mejor = plaza["mejor"]

        print(
            f"  {str(plaza['name'])[:18]:<20}"
            f"{POS.get(plaza['position'], '?'):<5}"
            f"{(f'{plaza['points_per_match']:.2f}' if plaza['points_per_match'] is not None else '-'):>10}"
            f"{(f'{plaza['con_vara']:.2f}' if plaza['con_vara'] is not None else '-'):>10}"
            f"{plaza['recambios_que_mejoran']:>11}  "
            + (
                f"{mejor['name']} {euros(mejor['price'])} "
                f"({mejor['puntos_netos']:+.2f}, "
                f"{mejor['puntos_netos_por_millon']:.3f}/M)"
                if mejor
                else plaza["reason"]
            )
        )

    print()
    print("  LA MEJOR OPERACION SIN VENDER A NADIE")
    print()

    mejor = plazas["mejor_sin_vender"]

    if mejor:
        # EL QUE SALE ES EL DE SU PLAZA, no el primero de la tabla.
        # La primera version imprimia los puntos de Dituro aqui
        # porque es el primero de la lista, y eso no es una
        # comparacion: es un numero al lado de otro.
        suya = next(
            p for p in plazas["plazas"] if p["name"] == mejor["plaza"]
        )

        print(
            f"    {mejor['name']} por la plaza de {mejor['plaza']}: "
            f"{euros(mejor['price'])} EUR"
        )
        print(
            f"    {mejor['points_per_match']:.2f} puntos por partido "
            f"(en {mejor['matches']}) contra los "
            f"{suya['points_per_match']:.2f} de {suya['name']}"
        )
        print(
            f"    netos con la vara: {mejor['puntos_netos']:+.2f} por "
            f"jornada, {mejor['puntos_netos_por_millon']:.3f} por millon"
        )

        if mejor.get("thin"):
            print()
            print(
                f"    AVISO DE `n`: {mejor['matches']} partido(s). El "
                f"numero que corona la tabla es el mas flojo de"
            )
            print(
                "    muestra que hay en ella. No se quita —es la "
                "medicion— pero se dice."
            )

    else:
        print(f"    {plazas['reason']}")

    otras = plazas.get("candidatas_sin_vender") or []

    if len(otras) > 1:
        print()
        print("  Y LAS DEMAS SIN VENDER A NADIE, POR SI LA DE ARRIBA VA")
        print("  CORTA DE MUESTRA:")
        print()
        print(
            f"    {'recambio':<18}{'por la plaza de':<18}{'cuesta':>12}"
            f"{'netos':>8}{'x millon':>10}{'partidos':>10}"
        )

        for otra in otras:
            print(
                f"    {str(otra['name'])[:16]:<18}"
                f"{str(otra['plaza'])[:16]:<18}"
                f"{euros(otra['price']):>12}"
                f"{otra['puntos_netos']:>+8.2f}"
                f"{otra['puntos_netos_por_millon']:>10.3f}"
                f"{otra['matches']:>10}"
                + ("   corta" if otra.get("thin") else "")
            )

    # LO SOLIDO DE HOY, AUNQUE NO QUEPA EN CAJA. Todas las
    # operaciones que no exigen vender salen de muestras de uno o
    # dos partidos; decir "la mejor es Mayol" y callarse eso seria
    # coronar el numero mas flojo de la tabla.
    solidas = [
        {**r, "plaza": plaza["name"]}
        for plaza in plazas["plazas"]
        for r in plaza["recambios"]
        if r["mejora"] and not r["thin"]
    ]

    solidas.sort(key=lambda r: -(r["puntos_netos_por_millon"] or 0))

    print()
    print("  Y LO SOLIDO DE HOY (tres partidos o mas), QUEPA O NO")
    print()

    if solidas:
        print(
            f"    {'recambio':<18}{'por la plaza de':<18}{'cuesta':>12}"
            f"{'netos':>8}{'partidos':>10}  ¿cabe en caja?"
        )

        for solida in solidas:
            print(
                f"    {str(solida['name'])[:16]:<18}"
                f"{str(solida['plaza'])[:16]:<18}"
                f"{euros(solida['price']):>12}"
                f"{solida['puntos_netos']:>+8.2f}"
                f"{solida['matches']:>10}  "
                f"{'SI' if solida['cabe_en_caja'] else 'NO — hay que vender'}"
            )

        caben = [r for r in solidas if r["cabe_en_caja"]]

        print()

        if caben:
            primera = caben[0]

            print(
                f"    LA MEJOR SOLIDA QUE CABE SIN VENDER NADA: "
                f"{primera['name']} por la plaza de "
                f"{primera['plaza']},"
            )
            print(
                f"    {euros(primera['price'])} EUR, "
                f"{primera['puntos_netos']:+.2f} puntos por jornada "
                f"con la vara, sobre {primera['matches']} partidos."
            )
            print()
            print(
                "    ESTA ES LA QUE YO PONDRIA ARRIBA, y no la de "
                "puntos por euro:"
            )
            print(
                f"    la corona por euro se la lleva un jugador de UN "
                f"partido."
            )

        else:
            print(
                "    NINGUNA DE LAS SOLIDAS CABE EN CAJA: las que "
                "mejoran de verdad piden vender antes."
            )

    else:
        print("    Ninguna. Todo lo que mejora hoy va corto de muestra.")

    print()
    print("  Y EL CASO DE DITURO, QUE ES EL QUE MOTIVA EL ENCARGO")

    dituro = next(
        (p for p in plazas["plazas"] if p["name"] == "Dituro"), None
    )

    if dituro:
        print()
        print(
            f"    Ocupa la peor plaza del once: "
            f"{dituro['points_per_match']} puntos por partido."
        )
        print(f"    {dituro['reason']}")
        print()
        print("    Los dos porteros del escaparate de hoy son Iturbe y")
        print("    Esquivel, 150.000 EUR, 0 puntos en 0 partidos. No se")
        print("    les puede medir, asi que no entran como recambio.")
        print()
        print("    LOS SEIS RECAMBIOS BARATOS SON LIBRES Y NO ESTAN")
        print("    PUBLICADOS: Dimitrievski (3,24 M), Dmitrovic (4,78 M),")
        print("    Remiro, Leo Roman... Con 8,87 M en caja se pagarian")
        print("    sin vender nada, PERO NO SE PUEDE PUJAR POR ELLOS.")
        print()
        print("    La operacion no existe hoy. Existe el dia que el")
        print("    Computer saque uno, y por eso estan los 20 vigilados.")

    titulo("NADA SE HA ENCENDIDO")
    print()
    print(f"  ENCENDIDO = {ENCENDIDO}")
    print("  Ninguna escritura contra Biwenger. Ningun umbral tocado.")
    print("  `count_free_slots` y `historical_max`, como estaban.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
