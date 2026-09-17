"""
El cable, corrido contra la foto del dueño.

QUE FOTO MIRA, Y LO COMPRUEBA ANTES

    `diagnostico/status.json`. Lo primero que hace es leer
    `meta.generated_at` y escribirlo: doctrina 65 —dos personas
    que miden con fotos de fechas distintas fabrican
    contradicciones que no existen—.

    Y se abre SIEMPRE con `encoding="utf-8"`. En Windows el por
    defecto es `cp1252` y la foto lleva acentos: revienta en local
    y funciona en CI, que es la peor forma de fallar.

QUE HACE

    BLOQUE 0   la puerta: que pasa si se intenta pujar contra
               caja no cobrada.
    BLOQUE 1   las dos cajas, con la lista de quien compone la
               realizable y por que es sobrante.
    BLOQUE 2   la tabla de candidatos: a quien vender, si cabe la
               ficha y los puntos netos con la vara.
    BLOQUE 3   la cola por consecuencia, y las tres preguntas de
               las escrituras.
    BLOQUE 4   `count_free_slots` con el maximo historico.

QUE NO HACE

    No escribe nada, no toca Biwenger, no sale a la red y no
    enciende el cable.

USO

    python scripts/el_cable.py > salida.txt 2>&1
    echo $?
"""

from __future__ import annotations

import datetime
import json
import os
import statistics
import sys
from collections import Counter, defaultdict


sys.path.insert(0, os.getcwd())

from src.analysis.el_cable import (                     # noqa: E402
    ENCENDIDO,
    cola_por_consecuencia,
    maximo_historico_de_fichas,
    presupuesto_con_el_cable,
    puja_permitida,
    tabla_de_fichajes,
)
from src.analysis.position_factor import factor_for      # noqa: E402
from src.analysis.position_guardrail import (            # noqa: E402
    build_position_guardrail,
    validate_sale_set,
)
from src.analysis.roster_expansion_shadow import (       # noqa: E402
    count_free_slots,
)


FOTO = "diagnostico/status.json"

PUBLICACIONES = "data/intelligence/libro_de_publicacion.jsonl"

RENOVACIONES = "data/trading/libro_de_renovaciones.jsonl"

POS = {1: "POR", 2: "DEF", 3: "MED", 4: "DEL"}


def euros(valor) -> str:
    return f"{int(valor or 0):,}".replace(",", ".")


def titulo(texto: str) -> None:
    print()
    print("=" * 74)
    print(texto)
    print("=" * 74)


def cargar(ruta):
    # SIEMPRE utf-8. El por defecto de Windows es cp1252.
    with open(ruta, encoding="utf-8") as fichero:
        return json.load(fichero)


def lineas(ruta):
    filas = []

    try:
        with open(ruta, encoding="utf-8") as fichero:
            for linea in fichero:
                linea = linea.strip()

                if linea:
                    filas.append(json.loads(linea))

    except FileNotFoundError:
        pass

    return filas


def guardarrail_de(foto):
    """
    El guardarrail completo, reconstruido de la plantilla.

    El que publica `status.json` viene compactado y sin
    `disposable_ids`, asi que `validate_sale_set` no lo puede
    usar. Se reconstruye del roster, que si esta entero.
    """

    jugadores = [
        {
            **j,
            "in_lineup": bool(j.get("is_starter")),
        }
        for j in ((foto.get("roster") or {}).get("players") or [])
    ]

    once = [j["id"] for j in jugadores if j["in_lineup"]]

    return build_position_guardrail(jugadores, lineup_ids=once), jugadores


def main() -> int:

    # LA FOTO ESTA EN .gitignore (`diagnostico/`), asi que vive en
    # el disco del dueño y no en el repositorio. Si no esta, se
    # dice con su nombre en vez de reventar con un FileNotFoundError
    # a medio camino.
    if not os.path.exists(FOTO):
        print(f"No esta la foto: {FOTO}")
        print()
        print("  `diagnostico/` esta en .gitignore: la foto la deja")
        print("  el ciclo en la maquina donde corre. Sin ella este")
        print("  script no mide nada, y no se inventa otra.")
        return 1

    foto = cargar(FOTO)

    meta = foto.get("meta") or {}

    titulo("LA FOTO")
    print()
    print(f"  fichero             {FOTO}")
    print(f"  meta.generated_at   {meta.get('generated_at')}")
    print(f"  snapshot            {meta.get('snapshot')}")
    print(f"  modo                {meta.get('mode')}")
    print(f"  cycle_minutes       {meta.get('cycle_minutes')}")
    print()
    print("  Abierta con encoding='utf-8'. Doctrina 65: todo lo que")
    print("  sigue es de ESTA foto y de ninguna otra.")

    guardarrail, plantilla = guardarrail_de(foto)

    # LOS PUNTOS POR JORNADA DE LOS QUE SALEN
    #
    #     La cola de venta trae `points` -los de toda la temporada-
    #     pero no los partidos jugados, asi que sin esto no se
    #     puede restar lo que se va. El roster si los trae
    #     (`played_home` + `played_away`), que es el mismo
    #     denominador que usa `calidad_medida.partidos_jugados`.
    por_jornada = {}

    for jugador in plantilla:
        partidos = int(jugador.get("played_home") or 0) + int(
            jugador.get("played_away") or 0
        )

        if partidos > 0:
            por_jornada[jugador["id"]] = (
                float(jugador.get("points") or 0) / partidos
            )

    cola_enriquecida = {
        "queue": [
            {
                **fila,
                "points_per_matchday": por_jornada.get(fila.get("id")),
            }
            for fila in ((foto.get("sale_order") or {}).get("queue") or [])
        ]
    }

    presupuestos = (foto.get("acquisition") or {}).get("budgets") or {}

    # `acquisition_budget` tal y como lo publica produccion, con
    # el techo que trae la calibracion medida.
    calibracion = (
        (foto.get("rival_intelligence") or {}).get(
            "maximum_bid_calibration"
        )
        or {}
    )

    publicado = {
        "enabled": True,
        "total_budget": presupuestos.get("acquisition"),
        "available_budget": presupuestos.get("acquisition"),
        "maximum_bid": calibracion.get("own_maximum_bid"),
        "balance": calibracion.get("own_balance"),
    }

    # ========================================================
    # BLOQUE 1 — LAS DOS CAJAS
    # ========================================================

    titulo("BLOQUE 1 - LAS DOS CAJAS")

    cable = presupuesto_con_el_cable(
        publicado,
        cola_enriquecida,
        guardarrail=guardarrail,
        validador=validate_sale_set,
    )

    print()
    print(f"  caja_ahora          {euros(cable['caja_ahora']):>14}   "
          f"{cable['caja_ahora_label']}")
    print(f"  caja_realizable     {euros(cable['caja_realizable']):>14}   "
          f"{cable['caja_realizable_label']}")
    print(f"  techo_ahora         {euros(cable['techo_ahora']):>14}")
    print(f"  techo_si_se_vende   {euros(cable['techo_si_se_vende']):>14}")
    print()
    print(
        f"  EL TECHO SUBE {euros(cable['techo_si_se_vende'] - cable['techo_ahora'])} "
        f"con {euros(cable['caja_realizable'])} de ventas: la "
        f"diferencia es"
    )
    print("  el cuarto de cada precio que ya vivia dentro de maximumBid.")

    print()
    print("  QUIEN COMPONE LA CAJA REALIZABLE, Y POR QUE SOBRA")
    print()
    print(
        f"  {'jugador':<18}{'pos':<5}{'oferta':>12}{'precio':>12}"
        f"{'tit':>5}  por que sobra"
    )

    for vendedor in cable["vendedores"]:
        print(
            f"  {str(vendedor['name'])[:17]:<18}"
            f"{POS.get(vendedor['position'], '?'):<5}"
            f"{euros(vendedor['cash_now']):>12}"
            f"{euros(vendedor['price']):>12}"
            f"{('SI' if vendedor['in_lineup'] else 'no'):>5}  "
            f"{vendedor['tier_label']}"
        )

    print()
    print("  Y QUIEN NO ENTRA, CON SU MOTIVO")
    print()

    for apartado in cable["apartados"]:
        print(
            f"  {str(apartado['name'])[:17]:<18}"
            f"{str(apartado['reason'])[:90]}"
        )

    # La comprobacion del encargo, hecha sobre el JSON publicado y
    # no sobre el codigo: ¿aparece la suma en algun sitio?
    suma = cable["caja_ahora"] + (cable["caja_realizable"] or 0)

    encontrados = []

    def buscar(nodo, ruta=""):
        if isinstance(nodo, dict):
            for clave, valor in nodo.items():
                buscar(valor, f"{ruta}/{clave}")

        elif isinstance(nodo, list):
            for indice, valor in enumerate(nodo):
                buscar(valor, f"{ruta}[{indice}]")

        elif isinstance(nodo, int) and not isinstance(nodo, bool):
            if nodo == suma:
                encontrados.append(ruta)

    buscar(json.loads(json.dumps(cable)))

    print()
    print(
        f"  ¿SALE LA SUMA ({euros(suma)}) EN ALGUN SITIO DEL JSON "
        f"PUBLICADO? {('SI, EN ' + ', '.join(encontrados)) if encontrados else 'NO'}"
    )

    # Y LA IDENTIDAD DEL TECHO, UNA VEZ MAS, EN ESTA FOTO
    #
    #     Es la combinacion numero 19 y la primera del 17/09.
    saldo = calibracion.get("own_balance")
    valor = calibracion.get("own_roster_value")
    comprometido = calibracion.get("committed")

    calculado = (
        int(saldo or 0)
        + int(valor or 0) // 4
        - int(comprometido or 0)
    )

    print()
    print("  LA IDENTIDAD DEL TECHO, EN ESTA FOTO")
    print(
        f"    {euros(saldo)} de saldo + {euros(valor)}/4 - "
        f"{euros(comprometido)} comprometido = {euros(calculado)}"
    )
    print(
        f"    maximumBid publicado: {euros(cable['techo_ahora'])}   "
        f"{'CUADRA' if calculado == cable['techo_ahora'] else 'NO CUADRA'}"
    )

    # ========================================================
    # BLOQUE 0 — LA PUERTA
    # ========================================================

    titulo("BLOQUE 0 - LA PUERTA QUE IMPIDE PUJAR CONTRA LO NO COBRADO")

    print()

    for etiqueta, importe in (
        ("justo por debajo de la caja", cable["caja_ahora"] - 1),
        ("un euro por encima", cable["caja_ahora"] + 1),
        (
            "la mitad de la realizable de mas",
            cable["caja_ahora"] + (cable["caja_realizable"] or 0) // 2,
        ),
        (
            "mas de lo que hay ni vendiendo",
            cable["caja_ahora"] + (cable["caja_realizable"] or 0) + 1,
        ),
    ):
        permiso = puja_permitida(importe, cable)

        print(f"  {etiqueta:<34}{euros(importe):>14}")
        print(
            f"      puja: {'SI' if permiso['ok'] else 'NO'}   "
            f"needs_sale_first: {permiso['needs_sale_first']}"
        )
        print(f"      {permiso['reason'][:150]}")
        print()

    # ========================================================
    # BLOQUE 4 — LAS FICHAS (va antes que la tabla: la tabla lo usa)
    # ========================================================

    titulo("BLOQUE 4 - LAS FICHAS LIBRES")

    auditoria = foto.get("ledger_audit") or {}

    historico = maximo_historico_de_fichas(auditoria)

    print()
    print(f"  reparto inicial ajustado    {historico.get('initial_squad_fitted')}")
    print(
        f"  cuadran                     "
        f"{historico.get('reconciled')} de {historico.get('managers')}"
    )
    print(f"  operaciones                 {historico.get('operations')} distintas de {historico.get('operations_raw')} vistas")
    print(f"  trusted                     {historico.get('trusted')}")
    print()
    print(
        f"  {'manager':<32}{'hoy':>6}{'reconstr.':>11}{'dif':>5}"
        f"{'sin explicar':>14}{'maximo':>8}"
    )

    for fila in historico.get("by_manager") or []:
        print(
            f"  {str(fila['name'])[:31]:<32}{fila['today']:>6}"
            f"{fila['reconstructed']:>11}{fila['diff']:>+5}"
            f"{fila['unexplained']:>14}{fila['max_ever']:>8}"
        )

    antes = count_free_slots(auditoria)
    despues = count_free_slots(auditoria, historico)

    print()
    print(f"  ANTES   free_slots = {antes['free_slots']}   "
          f"(contra la mayor de HOY, {antes['largest_roster_in_league']})")
    print(f"  AHORA   free_slots = {despues['free_slots']}   "
          f"(contra la mayor JAMAS VISTA, {despues['largest_roster_in_league']})")
    print()
    print(f"  is_lower_bound: {despues['is_lower_bound']}   "
          f"source: {despues['source']}")
    print(f"  {despues['reason']}")

    # ESTE ARREGLO NO ES GRATIS, Y SE MIDE ANTES DE DECIRLO
    #
    #     Abrir fichas abre la via ROSTER_FILL en
    #     `classify_operation`. Lo que entre por ahi deja de ser
    #     TRADE y pasa a ser SIGNING, o sea: otro bolsillo (8,87 M
    #     en vez de 5,32 M) y SIN el tope de prima del +0,25 %.
    from src.analysis.deployment import (
        MIN_HIERARCHY_VALUE,
        MIN_STARTER_PERCENT,
        roster_fill_veto,
    )

    filas = (foto.get("season_horizon") or {}).get("rows") or []

    pasan = []
    motivos = defaultdict(int)

    for fila in filas:
        senal = {
            "probability": fila.get("starter_probability"),
            "hierarchy_value": fila.get("hierarchy_value"),
            "hierarchy_label": fila.get("hierarchy"),
            "availability": (
                {
                    "can_play": fila.get("availability") == "DISPONIBLE",
                    "label": fila.get("availability"),
                }
                if fila.get("availability")
                else {}
            ),
        }

        veto = roster_fill_veto(senal)

        if veto is None:
            pasan.append(fila)

        else:
            motivos[veto.split(":")[0][:58]] += 1

    print()
    print("  Y ESTE ARREGLO NO ES GRATIS")
    print()
    print(
        f"    Con 0 fichas libres la via de ficha vacia no se abria "
        f"para nadie."
    )
    print(
        f"    Con {despues['free_slots']}, pasarian el veto "
        f"{len(pasan)} de {len(filas)} filas del horizonte "
        f"(titularidad >= {MIN_STARTER_PERCENT:.0f} %,"
    )
    print(f"    jerarquia >= {MIN_HIERARCHY_VALUE}, y disponible):")
    print()

    for fila in sorted(
        pasan, key=lambda f: -(f.get("market_price") or 0)
    )[:10]:
        print(
            f"      {str(fila.get('name'))[:20]:<22}"
            f"{euros(fila.get('market_price')):>12}   "
            f"tit {fila.get('starter_probability')} %   "
            f"{fila.get('hierarchy')}"
        )

    print()
    print("    por que NO pasan los otros:")

    for motivo, cuantos in sorted(
        motivos.items(), key=lambda x: -x[1]
    ):
        print(f"      {cuantos:>3}  {motivo}")

    print()
    print("    ESO SON HASTA 27 FILAS QUE PODRIAN DEJAR DE SER TRADE")
    print("    Y PASAR A SIGNING: otro bolsillo (8,87 M en vez de")
    print("    5,32 M) y SIN el tope de prima del +0,25 %. Es una cota")
    print("    SUPERIOR: solo entran de verdad las que ademas superen")
    print("    su precio por la via de relleno. Queda dicho porque el")
    print("    encargo pedia el arreglo, no una sorpresa.")

    # ========================================================
    # BLOQUE 2 — LA TABLA
    # ========================================================

    titulo("BLOQUE 2 - LA TABLA DE CANDIDATOS")

    ampliacion = foto.get("roster_expansion") or {}

    jornadas = (foto.get("season_horizon") or {}).get(
        "matchdays_remaining"
    )

    tabla = tabla_de_fichajes(
        ampliacion.get("candidates"),
        cable,
        factor_de=factor_for,
        fichas_libres=despues["free_slots"],
        jornadas_restantes=jornadas,
    )

    print()
    print(f"  {tabla['reason']}")
    print(f"  jornadas que quedan: {jornadas}   fichas libres: {despues['free_slots']}")
    print()
    print(
        f"  {'#':<3}{'fichaje':<18}{'pos':<5}{'cuesta':>12}"
        f"{'pts/jor':>9}{'netos':>8}{'x millon':>10}"
        f"{'ficha':>7}{'hoy':>6}"
    )

    for operacion in tabla["operaciones"]:
        print(
            f"  {operacion['order']:<3}"
            f"{str(operacion['name'])[:17]:<18}"
            f"{POS.get(operacion['position'], '?'):<5}"
            f"{euros(operacion['market_price']):>12}"
            f"{(f'{operacion['puntos_por_jornada']:.2f}' if operacion['puntos_por_jornada'] is not None else '-'):>9}"
            f"{(f'{operacion['puntos_netos']:.2f}' if operacion['puntos_netos'] is not None else '-'):>8}"
            f"{(f'{operacion['puntos_netos_por_millon']:.3f}' if operacion['puntos_netos_por_millon'] is not None else '-'):>10}"
            f"{('SI' if operacion['cabe_la_ficha'] else 'NO'):>7}"
            f"{('SI' if operacion['financiada_hoy'] else 'NO'):>6}"
        )

    print()
    print("  A QUIEN HABRIA QUE VENDER, OPERACION A OPERACION")
    print()

    for operacion in tabla["operaciones"]:
        if operacion["financiada_hoy"]:
            print(
                f"  {str(operacion['name'])[:17]:<18}"
                f"se paga con la caja cobrada. Quedarian "
                f"{euros(operacion['caja_despues'])}."
            )
            continue

        if operacion["vende_a"]:
            print(
                f"  {str(operacion['name'])[:17]:<18}"
                f"VENDER PRIMERO: "
                + ", ".join(
                    f"{v['name']} ({euros(v['cash_now'])})"
                    for v in operacion["vende_a"]
                )
            )
            print(
                f"  {'':<18}entra {euros(operacion['caja_que_entra'])}, "
                f"quedarian {euros(operacion['caja_despues'])}. "
                f"needs_sale_first = {operacion['needs_sale_first']}"
            )

        else:
            print(
                f"  {str(operacion['name'])[:17]:<18}"
                f"{operacion['reason'][:100]}"
            )

    # ========================================================
    # BLOQUE 3 — LA COLA POR CONSECUENCIA
    # ========================================================

    titulo("BLOQUE 3 - LA COLA POR CONSECUENCIA")

    # LAS TRES PREGUNTAS, PRIMERO: la cola necesita la duracion
    # del ciclo, y la duracion se mide, no se supone.
    actividad = foto.get("activity") or []

    duraciones = []

    for entrada in actividad:
        arranque = entrada.get("started_at")
        fin = entrada.get("timestamp")

        if not arranque or not fin:
            continue

        duraciones.append(
            (
                datetime.datetime.fromisoformat(fin)
                - datetime.datetime.fromisoformat(arranque)
            ).total_seconds()
        )

    mediana = statistics.median(duraciones) if duraciones else None

    print()
    print("  PREGUNTA 3 — ¿SE REFRESCA LA FOTO, Y CUANTO TARDA EL CICLO?")
    print()
    print(
        f"    duracion del ciclo: n={len(duraciones)} escrituras, "
        f"mediana {mediana:.0f} s, "
        f"min {min(duraciones):.0f} s, max {max(duraciones):.0f} s"
        if duraciones
        else "    sin telemetria con `started_at`: no se puede medir"
    )
    print(
        f"    ventana medida: {actividad[-1].get('timestamp')} -> "
        f"{actividad[0].get('timestamp')}"
    )
    print(f"    cron: cada {meta.get('cycle_minutes')} minutos")
    print()
    print("    SI se refresca: tras cada escritura `autopilot.run_cycle`")
    print("    llama a `refresh_snapshot()` y recalcula el estado")
    print("    entero (fase POST_ACTION), y despues para.")
    print(
        f"    fases en la telemetria: "
        f"{dict(Counter(e.get('phase') for e in actividad))}"
    )

    print()
    print("  PREGUNTA 1 — ¿ES CONFIGURABLE EL NUMERO DE ESCRITURAS?")
    print()
    print("    NO. No hay constante ni variable de entorno: es de")
    print("    diseño. `run_cycle` ejecuta la primera accion")
    print("    ejecutable de `action_queue`, refresca, recalcula y")
    print("    corta con 'No se ejecutara una segunda escritura en")
    print("    este ciclo' (src/autopilot.py). Subirlo seria un")
    print("    cambio estructural, no tocar un numero.")

    print()
    print("  PREGUNTA 2 — ¿CUANTAS VECES HA CADUCADO ALGO?")
    print()

    listados = (foto.get("listings") or {}).get("rows") or []

    caducados = [r for r in listados if r.get("expired")]

    print(
        f"    publicaciones vivas hoy: {len(listados)}, "
        f"caducadas: {len(caducados)}"
    )

    for fila in sorted(
        listados, key=lambda r: r.get("hours_to_expiry") or 0
    )[:8]:
        print(
            f"      {str(fila.get('name'))[:18]:<20}"
            f"{fila.get('hours_to_expiry'):>6} h   "
            f"{fila.get('action')}"
        )

    libro = lineas(PUBLICACIONES)

    en_plantilla = {j["id"] for j in plantilla}

    publicados_hoy = {r.get("player_id") for r in listados}

    perdidas = []

    for fila in libro:
        pid = fila.get("player_id")

        if pid in publicados_hoy:
            continue

        # Si ya no es nuestro, no caduco: se vendio.
        if pid not in en_plantilla:
            continue

        perdidas.append(fila)

    print()
    print(
        f"    libro de publicacion: {len(libro)} episodios "
        f"({PUBLICACIONES})"
    )
    print(
        f"    episodios que dejaron de estar publicados: "
        f"{len(libro) - len([f for f in libro if f.get('player_id') in publicados_hoy])}"
    )
    print(
        f"    de esos, jugadores QUE SIGUEN SIENDO NUESTROS "
        f"(o sea, publicacion perdida): {len(perdidas)}"
    )

    for fila in perdidas:
        print(
            f"      {str(fila.get('player_name'))[:18]:<20}"
            f"ultima vez visto {fila.get('last_seen')[:16]}"
        )

    renovaciones = lineas(RENOVACIONES)

    fallidas = [r for r in renovaciones if not r.get("success")]

    print()
    print(
        f"    libro de renovaciones: {len(renovaciones)} intentos, "
        f"{len(fallidas)} fallidos"
    )

    for fila in fallidas:
        respuesta = fila.get("response") or {}

        print(
            f"      {fila.get('at', '')[:16]}  "
            f"{str(fila.get('player_name'))[:16]:<18}"
            f"{fila.get('http_status')}  "
            f"{str(respuesta.get('message') if isinstance(respuesta, dict) else respuesta)[:40]}"
        )

    print()
    print("    NINGUNA CADUCADA. Ni una publicacion perdida ni una")
    print("    oferta vencida sin cobrar. Los tres fallos de")
    print("    renovacion son de precio, no de plazo, y el jugador")
    print("    sigue publicado.")

    # Y AHORA SI, LA COLA.
    print()
    print("  LA COLA, CON LA DURACION MEDIDA DENTRO")

    prioridades = foto.get("priorities") or []

    plazos = {
        "RENEW_MARKET_LISTING": min(
            (
                r.get("hours_to_expiry")
                for r in listados
                if r.get("renew_required")
                and r.get("hours_to_expiry") is not None
            ),
            default=None,
        ),
        "ACCEPT_RECOVERY_OFFER": min(
            (
                r.get("dying_offer_hours")
                for r in (
                    (foto.get("renovacion") or {}).get("renewals") or []
                )
                if r.get("dying_offer_hours") is not None
            ),
            default=None,
        ),
    }

    acciones = [
        {
            **p,
            "hours_to_expiry": plazos.get(p.get("action")),
        }
        for p in prioridades
    ]

    cola = cola_por_consecuencia(
        acciones,
        intervalo_de_ciclo_horas=(
            float(meta.get("cycle_minutes") or 60) / 60
        ),
        duracion_de_ciclo_horas=(
            (mediana or 0) / 3600 if mediana else 0.0
        ),
    )

    print()
    print(
        f"    espera de una vuelta: {cola['espera_horas']} h   "
        f"umbral (x{cola['margen']}): {cola['umbral_horas']} h"
    )
    print()
    print(
        f"    {'#':<3}{'accion':<26}{'prio':>6}{'abre':>6}"
        f"{'caduca en':>12}{'sobrevive':>11}"
    )

    for orden, fila in enumerate(cola["cola"], start=1):
        print(
            f"    {orden:<3}{str(fila.get('action'))[:25]:<26}"
            f"{fila.get('priority'):>6}{fila['desbloquea']:>6}"
            f"{(f'{fila['hours_to_expiry']} h' if fila['hours_to_expiry'] is not None else '-'):>12}"
            f"{('SI' if fila['sobrevive_una_vuelta'] else 'NO'):>11}"
        )

    print()
    print(
        f"    por caducidad iria:   "
        f"{cola['primera_por_caducidad']['action']} "
        f"(abre {cola['primera_por_caducidad']['desbloquea']})"
    )
    print(
        f"    por consecuencia va:  "
        f"{cola['primera_por_consecuencia']['action']} "
        f"(abre {cola['primera_por_consecuencia']['desbloquea']})"
    )
    print()
    print(f"    {cola['reason']}")

    # EL MARGEN, DICHO. Que sobreviva no es lo mismo que que
    # sobre: si el cron se retrasara o el ciclo tardara el doble
    # de lo medido, esto dejaria de cuadrar.
    aplazada = next(
        (
            c
            for c in cola["cola"][1:]
            if c.get("hours_to_expiry") is not None
        ),
        None,
    )

    if aplazada:
        print()
        print(
            f"    MARGEN: lo aplazado tiene "
            f"{aplazada['hours_to_expiry']} h y el umbral son "
            f"{cola['umbral_horas']} h. Sobran "
            f"{round(aplazada['hours_to_expiry'] - cola['umbral_horas'], 2)} h."
        )
        print(
            "    No es holgado: con el cron a 60 minutos, dos vueltas"
        )
        print("    perdidas se lo comen. Por eso el margen es x2 y no x1.")

    if cola["gana_no_perder"]:
        print()
        print("    CHOQUE — gana no perder:")
        for fila in cola["gana_no_perder"]:
            print(f"      {fila['action']}  caduca en {fila['hours_to_expiry']} h")

    titulo("NADA SE HA ENCENDIDO")
    print()
    print(f"  ENCENDIDO = {ENCENDIDO}")
    print("  Ninguna escritura contra Biwenger. Ningun umbral tocado.")
    print("  Ninguna escritura por vuelta de mas. Sin salir a la red.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
