"""
La direccion del precio, corrida contra los libros de esta casa.

QUE FOTO MIRA

    `diagnostico/status.json`, con `encoding="utf-8"`. Lo primero
    que imprime es `meta.generated_at`.

QUE HACE

    BLOQUE 0   que escribe el codigo bajo el directorio de
               estado, que esta clasificado y que no; y por que
               la bitacora del saldo tiene lineas de hoy con el
               saldo de ayer.
    BLOQUE 1   el rendimiento partido por direccion y por plazo,
               cada celda con su `n`; donde satura y se da la
               vuelta; si cambia con la fuerza de la subida; y si
               los 19 puntos aguantan al descontar al Computer.
    BLOQUE 2   el filtro, apagado.
    BLOQUE 3   las subastas del Computer: en cuantas se habria
               pujado con el filtro, y cuantas buenas se caen.

QUE NO HACE

    No escribe contra Biwenger, no sale a la red, no enciende el
    filtro y NO BORRA NI ESCRIBE NINGUNA LINEA DE NINGUN LIBRO.

USO

    python scripts/la_direccion.py > salida.txt 2>&1
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

from src.analysis.la_direccion import (                   # noqa: E402
    COMO_SALE,
    COMPRAMOS_SI,
    DIRECCIONES,
    ENCENDIDO,
    FUERZA,
    HUECO_BRUTO_PP,
    HUECO_NETO_PP,
    PERSISTENCIA,
    PERSISTENCIA_N,
    PLAZOS_MEDIDOS,
    PLAZO_DE_SALIDA,
    PRIMA_DEL_COMPUTER,
    comprobar_el_plazo,
    neto_al_salir,
    puede_comprar,
    que_cambia,
    rendimiento,
)

from src.estado.los_libros import (                       # noqa: E402
    LIBROS,
    NO_SON_LIBROS,
    escritos_por_el_codigo,
    rutas,
    sin_clasificar,
)


FOTO = "diagnostico/status.json"

HISTORICO = "data/autopilot/price_history.json"

TABLON = "data/rival_intelligence/board_events.json"

BITACORA = "data/solvency/bitacora_del_saldo.jsonl"

DIA = 86_400

# El dia de mercado corta en el reset, no a medianoche.
HORA_DEL_RESET = 5


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


def dia_de_mercado(marca) -> int:
    return int((marca - HORA_DEL_RESET * 3600) // DIA)


def series_diarias(historico) -> dict:
    """Un precio por jugador y dia de mercado."""

    salida = {}

    for identificador, ficha in (historico.get("players") or {}).items():

        porque = {}

        for marca, precio in zip(
            ficha.get("t") or [], ficha.get("p") or []
        ):
            if precio:
                porque[dia_de_mercado(marca)] = precio

        if len(porque) >= 3:
            salida[str(identificador)] = porque

    return salida


def direccion_de_la_vispera(serie, dia):
    """Que hizo el precio el dia ANTES de `dia`."""

    if dia - 1 not in serie or dia - 2 not in serie:
        return None

    antes, despues = serie[dia - 2], serie[dia - 1]

    if despues > antes:
        return "SUBIA"

    if despues < antes:
        return "BAJABA"

    return "PLANO"


# ============================================================
# BLOQUE 0
# ============================================================

def bloque_0() -> None:

    titulo("BLOQUE 0 — QUE ESCRIBE EL CODIGO, Y QUE SE GUARDABA")

    escritos = escritos_por_el_codigo(".")

    huerfanos = sin_clasificar(".")

    print(f"  ficheros que el codigo escribe : {len(escritos)}")
    print(f"  clasificados como LIBRO        : {len(LIBROS)}")
    print(f"  clasificados como cache        : {len(NO_SON_LIBROS)}")
    print(f"  SIN CLASIFICAR                 : {len(huerfanos)}")

    for ruta, quienes in sorted(huerfanos.items()):
        print(f"      {ruta}   <- {', '.join(quienes)}")

    print()
    print(f"  LOS {len(LIBROS)} LIBROS, Y DONDE ESTA CADA UNO HOY:")

    import subprocess

    for ruta in rutas():

        proceso = subprocess.run(
            ["git", "ls-files", "--error-unmatch", "--", ruta],
            capture_output=True,
        )

        en_git = "en git" if proceso.returncode == 0 else "NO esta"

        en_disco = "en disco" if os.path.exists(ruta) else "no existe"

        print(f"      {en_git:<8} {en_disco:<10} {ruta}")

    print()
    print(
        "  LO QUE ESTO SIGNIFICA: el `.gitignore` se genera de la "
        "misma lista,"
    )
    print(
        "  asi que un libro fuera de ella quedaba TAPADO — vivia "
        "en la cache del"
    )
    print(
        "  runner y moria con ella a los siete dias sin uso. Es "
        "el agujero que"
    )
    print("  ya se comio la carpeta de solvencia la semana pasada.")

    # LA BITACORA
    print()
    print("  " + "-" * 70)
    print("  LA BITACORA DEL SALDO: por que tiene fechas de hoy con")
    print("  datos de ayer.")
    print("  " + "-" * 70)

    try:
        filas = []

        with open(BITACORA, encoding="utf-8") as fichero:
            for linea in fichero:
                if linea.strip():
                    filas.append(json.loads(linea))

    except (OSError, ValueError) as error:
        print(f"      No se pudo leer la bitacora: {error}")
        return

    print(f"      lineas en este disco : {len(filas)}")

    por_dia = Counter(str(f.get("at", "?"))[:10] for f in filas)

    for dia in sorted(por_dia):
        print(f"         {dia}   {por_dia[dia]}")

    repetidas = sum(
        1
        for i in range(1, len(filas))
        if (
            filas[i - 1].get("balance"),
            filas[i - 1].get("roster_value"),
            filas[i - 1].get("maximum_bid"),
        )
        == (
            filas[i].get("balance"),
            filas[i].get("roster_value"),
            filas[i].get("maximum_bid"),
        )
    )

    print()
    print(
        f"      lineas identicas a la anterior: {repetidas} de "
        f"{max(len(filas) - 1, 0)}"
    )

    huecos = []

    for i in range(1, len(filas)):
        try:
            antes = datetime.datetime.fromisoformat(filas[i - 1]["at"])
            ahora = datetime.datetime.fromisoformat(filas[i]["at"])
            huecos.append((ahora - antes).total_seconds() / 60.0)
        except (KeyError, ValueError):
            continue

    if huecos:
        print(
            f"      hueco mediano entre lineas: "
            f"{statistics.median(huecos):.1f} min "
            f"(el ciclo corre una vez por hora)"
        )

    print()
    print("      LA CAUSA, medida ejecutando la verja entera con las")
    print("      escrituras interceptadas:")
    print()
    print(
        "        `test_el_ciclo_publica_v1` monta el estado del "
        "dashboard"
    )
    print(
        "        ENTERO con la foto que haya en disco, y "
        "`build_state` llama a"
    )
    print(
        "        `apuntar_lectura(...)` SIN `ruta`. Asi que la "
        "linea cae en el"
    )
    print(
        "        libro de verdad, con el saldo DE ESA FOTO y la "
        "hora de AHORA."
    )
    print()
    print(
        "        En produccion la foto que hay en disco cuando "
        "corre la verja"
    )
    print(
        "        es la de la VUELTA ANTERIOR — el ciclo escribe la "
        "nueva despues—,"
    )
    print(
        "        asi que cada vuelta deja dos lineas: la de la "
        "verja con el saldo"
    )
    print("        viejo, y la del ciclo con el bueno.")


# ============================================================
# BLOQUE 1
# ============================================================

def bloque_1(series) -> dict:

    titulo("BLOQUE 1 — EL RENDIMIENTO, PARTIDO POR DIRECCION")

    celdas = defaultdict(list)

    fuerza = defaultdict(list)

    salida = defaultdict(lambda: defaultdict(int))

    for identificador, serie in series.items():

        dias = sorted(serie)

        for i in range(1, len(dias)):

            # SOLO DIAS SEGUIDOS: con un hueco en medio no se sabe
            # que hizo el precio la vispera.
            if dias[i] - dias[i - 1] != 1:
                continue

            antes, hoy = serie[dias[i - 1]], serie[dias[i]]

            direccion = (
                "SUBIA" if hoy > antes
                else "BAJABA" if hoy < antes
                else "PLANO"
            )

            cambio = (hoy - antes) / antes * 100.0

            for plazo in PLAZOS_MEDIDOS:

                fin = dias[i] + plazo

                if fin not in serie:
                    continue

                celdas[(direccion, plazo)].append(
                    (serie[fin] - hoy) / hoy * 100.0
                )

            fin = dias[i] + PLAZO_DE_SALIDA

            if direccion == "SUBIA" and fin in serie:

                tramo = (
                    "0-1 %" if cambio < 1
                    else "1-2 %" if cambio < 2
                    else "2-4 %" if cambio < 4
                    else "mas de 4 %"
                )

                fuerza[tramo].append(
                    (serie[fin] - hoy) / hoy * 100.0
                )

            if fin in serie and fin - 1 in serie:

                como = (
                    "SUBIA" if serie[fin] > serie[fin - 1]
                    else "BAJABA" if serie[fin] < serie[fin - 1]
                    else "PLANO"
                )

                salida[direccion][como] += 1

    print(f"  jugadores con serie diaria: {len(series)}")
    print()
    print(
        f"  {'plazo':<8}{'SUBIA':>22}{'PLANO':>22}{'BAJABA':>22}"
    )

    for plazo in PLAZOS_MEDIDOS:

        fila = f"  {str(plazo) + ' d':<8}"

        for direccion in DIRECCIONES:

            valores = celdas[(direccion, plazo)]

            fila += (
                f"{statistics.median(valores):>+13.3f} % "
                f"(n={len(valores)})"
                if valores
                else f"{'-':>22}"
            )

        print(fila)

    print()
    print("  EL HUECO ENTRE LAS DOS COLUMNAS:")

    for plazo in PLAZOS_MEDIDOS:

        sube, baja = celdas[("SUBIA", plazo)], celdas[("BAJABA", plazo)]

        if sube and baja:
            print(
                f"     {plazo:>2} d   "
                f"{statistics.median(sube) - statistics.median(baja):>+7.2f} pp"
            )

    print()
    print("  EL PICO DE CADA COLUMNA:")

    for direccion in DIRECCIONES:

        mejor = max(
            PLAZOS_MEDIDOS,
            key=lambda p: (
                statistics.median(celdas[(direccion, p)])
                if celdas[(direccion, p)]
                else -999
            ),
        )

        valores = celdas[(direccion, mejor)]

        if valores:
            print(
                f"     {direccion:<7} a {mejor:>2} dias: "
                f"{statistics.median(valores):+.3f} % (n={len(valores)})"
            )

    derivado = comprobar_el_plazo()

    print()
    print(
        f"  DONDE SATURA Y SE DA LA VUELTA: {derivado['plazo']} dias "
        f"({derivado['percent']:+.3f} %)."
    )
    print(f"     y despues devuelve: {derivado['siguientes']}")
    print(f"     ESE ES EL PLAZO DE SALIDA.")

    print()
    print(
        f"  ¿CAMBIA SEGUN LO FUERTE QUE SUBA? "
        f"(a {PLAZO_DE_SALIDA} dias)"
    )

    for tramo in ("0-1 %", "1-2 %", "2-4 %", "mas de 4 %"):

        valores = fuerza.get(tramo) or []

        declarado = FUERZA.get(tramo)

        if valores:
            print(
                f"     subio {tramo:<11} -> "
                f"{statistics.median(valores):>+8.3f} % (n={len(valores)})"
                + (
                    f"   mismo tramo de precio: "
                    f"{declarado[3]:+.3f} %"
                    if declarado
                    else ""
                )
            )

    print()
    print(
        f"  Y la direccion PERSISTE: {PERSISTENCIA * 100:.1f} % de un "
        f"dia al siguiente (n={PERSISTENCIA_N})."
    )

    # LA PREGUNTA INCOMODA
    print()
    print("  " + "-" * 70)
    print("  ¿AGUANTAN LOS 19 PUNTOS AL DESCONTAR LO QUE PAGA EL")
    print("  COMPUTER POR CADA GRUPO?")
    print("  " + "-" * 70)
    print()
    print("     la prima del Computer AL VENDER, por direccion")
    print("     (censo A: 90 ofertas vivas 12/08-13/09, sin sesgo")
    print("     de aceptacion):")

    for direccion in DIRECCIONES:
        percent, n = PRIMA_DEL_COMPUTER[direccion]
        print(f"        {direccion:<7} {percent:>+8.4f} %   (n={n})")

    print()
    print("     y a los diez dias el jugador ya no sale como entro:")

    for direccion in ("SUBIA", "BAJABA"):

        reparto = salida.get(direccion) or {}

        total = sum(reparto.values())

        if total:
            print(
                f"        entro {direccion:<7} -> sale  "
                + "   ".join(
                    f"{como} {reparto[como] * 100 / total:4.1f} %"
                    for como in DIRECCIONES
                )
                + f"   (n={total})"
            )

    print()

    netos = {}

    for direccion in ("SUBIA", "BAJABA"):

        ficha = neto_al_salir(direccion)

        netos[direccion] = ficha

        print(f"     ENTRANDO A UNO QUE {direccion}:")
        print(
            f"        deriva del precio        "
            f"{ficha['deriva_percent']:>+8.3f} %   (n={ficha['deriva_n']})"
        )
        print(
            f"        prima esperada al vender "
            f"{ficha['prima_percent']:>+8.3f} %   (n={ficha['prima_n']})"
        )
        print(
            f"        NETO a {ficha['plazo_dias']} dias        "
            f"{ficha['neto_percent']:>+8.3f} %"
        )

    print()
    print(f"     HUECO BRUTO (solo deriva)   {HUECO_BRUTO_PP:>+7.2f} pp")
    print(f"     HUECO NETO  (con la prima)  {HUECO_NETO_PP:>+7.2f} pp")
    print()

    if HUECO_NETO_PP > 0:
        print(
            "     EL HUECO NO SE CIERRA. La prima se come 0,52 de "
            "19,14 puntos."
        )
    else:
        print(
            "     EL HUECO SE CIERRA: con la prima descontada este "
            "carril no tiene motivo."
        )

    return celdas


# ============================================================
# BLOQUE 2
# ============================================================

def bloque_2() -> None:

    titulo("BLOQUE 2 — EL FILTRO, APAGADO")

    print(f"  ENCENDIDO = {ENCENDIDO}")
    print()
    print(
        f"  el carril compra SOLO a los que el ojeador dice que "
        f"{COMPRAMOS_SI},"
    )
    print(
        f"  y los tiene {PLAZO_DE_SALIDA} dias — no hasta el dia "
        f"siguiente."
    )
    print()
    print("  QUE CONTESTA A CADA CASO:")

    casos = (
        ("el ojeador dice UP", {"direction": "UP"}),
        ("el ojeador dice DOWN", {"direction": "DOWN"}),
        ("el ojeador dice FLAT", {"direction": "FLAT"}),
        ("el ojeador no se moja", {"direction": None}),
        ("no hay pronostico", None),
    )

    for etiqueta, pronostico in casos:

        veredicto = puede_comprar(pronostico)

        print()
        print(
            f"     {etiqueta:<24} -> "
            f"{'PUJA' if veredicto['available'] else 'NO PUJA'}"
        )
        print(f"        {veredicto['reason']}")

    print()
    print(
        "  NINGUN UMBRAL SE MUEVE: el filtro dice QUE ENTRA, no "
        "CUANTO SE PAGA."
    )
    print(
        "  El precio lo sigue poniendo `regla_de_compra` con su "
        "tope de siempre."
    )


# ============================================================
# BLOQUE 3
# ============================================================

def bloque_3(series) -> None:

    titulo("BLOQUE 3 — QUE HABRIA CAMBIADO")

    try:
        crudo = cargar(TABLON)

    except (OSError, ValueError) as error:
        print(f"  No se pudo leer el tablon: {error}")
        return

    tablon = crudo.get("events") if isinstance(crudo, dict) else crudo

    subastas, vistas = [], set()

    for evento in tablon or []:

        if evento.get("type") != "market":
            continue

        for fila in evento.get("content") or []:

            if not isinstance(fila, dict):
                continue

            # Con vendedor es un traspaso entre managers.
            if (fila.get("from") or {}).get("id"):
                continue

            clave = (
                fila.get("player"),
                fila.get("amount"),
                (fila.get("to") or {}).get("id"),
            )

            if clave in vistas:
                continue

            vistas.add(clave)

            subastas.append(
                {
                    "dia": datetime.datetime.fromtimestamp(
                        evento["date"], datetime.UTC
                    ).date().isoformat(),
                    "d": dia_de_mercado(evento["date"]),
                    "player": str(fila.get("player")),
                    "to_id": (fila.get("to") or {}).get("id"),
                    "to_name": (fila.get("to") or {}).get("name"),
                    "amount": fila.get("amount"),
                    "bids": {
                        (b.get("user") or {}).get("id")
                        for b in (fila.get("bids") or [])
                    },
                }
            )

    nosotros = next(
        (
            s["to_id"]
            for s in subastas
            if s["to_name"] and "Bordal" in s["to_name"]
        ),
        None,
    )

    for subasta in subastas:

        serie = series.get(subasta["player"])

        subasta["dir"] = (
            direccion_de_la_vispera(serie, subasta["d"])
            if serie
            else None
        )

        # PARTICIPA quien puja O quien gana: el tablon no siempre
        # lista al ganador entre los pujadores.
        participantes = subasta["bids"] | (
            {subasta["to_id"]} if subasta["to_id"] else set()
        )

        subasta["pujamos"] = nosotros in participantes

        subasta["ganamos"] = subasta["to_id"] == nosotros

    print(f"  subastas del Computer: {len(subastas)}")
    print()

    por_direccion = Counter(s["dir"] for s in subastas)

    for clave in ("SUBIA", "PLANO", "BAJABA", None):
        cuantas = por_direccion[clave]
        print(
            f"     vispera {str(clave):<7} {cuantas:>4}  "
            f"({cuantas * 100 / max(len(subastas), 1):4.1f} %)"
        )

    cambio = que_cambia(subastas, nosotros)

    if not cambio.get("available"):
        print(f"  {cambio.get('reason')}")
        return

    print()
    print("  CADA MANAGER, Y CUANTO LE DEJA EL FILTRO:")

    por_manager = {}

    for subasta in subastas:

        participantes = subasta["bids"] | (
            {subasta["to_id"]} if subasta["to_id"] else set()
        )

        for quien in participantes:

            ficha = por_manager.setdefault(
                quien,
                {"n": 0, "gano": 0, "sube": 0, "name": None},
            )

            ficha["n"] += 1

            if subasta["dir"] == COMPRAMOS_SI:
                ficha["sube"] += 1

            if quien == subasta["to_id"]:
                ficha["gano"] += 1
                ficha["name"] = subasta["to_name"]

    print(
        f"     {'manager':<26}{'pujo':>6}{'gano':>6}{'conv':>7}"
        f"{'% subastas':>12}{'y con filtro':>14}"
    )

    for quien, ficha in sorted(
        por_manager.items(), key=lambda par: -par[1]["n"]
    )[:8]:
        print(
            f"     {str(ficha['name'] or quien)[:25]:<26}"
            f"{ficha['n']:>6}{ficha['gano']:>6}"
            f"{ficha['gano'] * 100 / ficha['n']:>6.0f} %"
            f"{ficha['n'] * 100 / len(subastas):>11.0f} %"
            f"{ficha['sube'] * 100 / len(subastas):>13.0f} %"
        )

    print()
    print(
        f"  el filtro deja pasar {cambio['deja_pasar']} de "
        f"{cambio['n']} subastas "
        f"({cambio['deja_pasar'] * 100 / cambio['n']:.0f} %)"
    )
    print(
        f"     ...de las que {cambio['sin_pronostico']} no tienen "
        f"pronostico reconstruible"
    )
    print()
    print(
        f"  de nuestras {cambio['pujadas']} pujas quedan "
        f"{cambio['pujadas_con_filtro']}  -> se caen "
        f"{cambio['pujadas'] - cambio['pujadas_con_filtro']}"
    )
    print(
        f"  de nuestras {cambio['ganadas']} ganadas quedan "
        f"{cambio['ganadas_con_filtro']} -> SE CAEN "
        f"{cambio['ganadas'] - cambio['ganadas_con_filtro']}"
    )

    print()
    print("  LAS GANADAS QUE EL FILTRO HABRIA QUITADO:")

    for subasta in sorted(
        cambio["ganadas_que_se_caen"], key=lambda s: s["dia"]
    ):
        print(
            f"     {subasta['dia']}  id {subasta['player']:<7}"
            f"{euros(subasta['amount']):>13}   "
            f"vispera={subasta['dir']}"
        )

    # ¿ERAN BUENAS? Es la pregunta de verdad: una ganada no es
    # una buena operacion, es una operacion.
    def rendimiento_real(subasta):

        serie = series.get(subasta["player"])

        if not serie:
            return None, None

        base = serie.get(subasta["d"]) or serie.get(subasta["d"] - 1)

        if not base:
            return None, None

        fin = subasta["d"] + PLAZO_DE_SALIDA

        if fin in serie:
            return (serie[fin] - base) / base * 100.0, PLAZO_DE_SALIDA

        ultimo = max(serie)

        if ultimo <= subasta["d"]:
            return None, None

        return (
            (serie[ultimo] - base) / base * 100.0,
            ultimo - subasta["d"],
        )

    print()
    print("  ¿ERAN BUENAS? LO QUE HIZO EL PRECIO DESPUES:")
    print()

    ganadas = [s for s in subastas if s["ganamos"]]

    for subasta in ganadas:
        subasta["rend"], subasta["plazo"] = rendimiento_real(subasta)

    medibles = [s for s in ganadas if s["rend"] is not None]

    def resumen(grupo, etiqueta):

        if not grupo:
            print(f"     {etiqueta}: n=0")
            return 0.0, 0

        capital = sum(int(s["amount"] or 0) for s in grupo)

        resultado = sum(
            int(s["amount"] or 0) * s["rend"] / 100.0 for s in grupo
        )

        print(f"     {etiqueta}")
        print(
            f"        n={len(grupo):<3} capital {euros(capital):>14}"
            f"   resultado {euros(resultado):>13}"
            f"   por euro {resultado * 100 / capital:>+6.2f} %"
        )

        return resultado, capital

    deja, capital_deja = resumen(
        [s for s in medibles if s["dir"] == COMPRAMOS_SI],
        "LAS QUE EL FILTRO DEJA   (la vispera subia)",
    )

    quita, capital_quita = resumen(
        [s for s in medibles if s["dir"] != COMPRAMOS_SI],
        "LAS QUE EL FILTRO QUITA  (plana o bajaba)",
    )

    if capital_deja and capital_quita:
        print()
        print(
            f"     el filtro se queda con el "
            f"{capital_deja * 100 / (capital_deja + capital_quita):.0f} % "
            f"del capital y con el "
            f"{deja * 100 / (deja + quita):.0f} % del resultado"
        )
        print(
            f"     y LIBERA {euros(capital_quita)} EUR que rindieron "
            f"{quita * 100 / capital_quita:+.2f} %"
        )

    # EL OTRO LADO.
    print()
    print("  EL HUECO DE VERDAD: las que el filtro deja y NO pujamos")
    print()

    perdidas = cambio["deja_y_no_pujamos"]

    for subasta in perdidas:
        subasta["rend"], subasta["plazo"] = rendimiento_real(subasta)

    medibles = [s for s in perdidas if s["rend"] is not None]

    print(f"     subastas que pasan el filtro y no pujamos: {len(perdidas)}")

    if medibles:

        capital = sum(int(s["amount"] or 0) for s in medibles)

        resultado = sum(
            int(s["amount"] or 0) * s["rend"] / 100.0 for s in medibles
        )

        suben = [s for s in medibles if s["rend"] > 0]

        print(
            f"     de esas, {len(medibles)} se pueden medir: "
            f"mediana "
            f"{statistics.median([s['rend'] for s in medibles]):+.2f} %"
        )
        print(f"     lo que costaban      {euros(capital):>15}")
        print(
            f"     lo que habrian dado  {euros(resultado):>15}"
            f"   ({resultado * 100 / capital:+.2f} % por euro)"
        )
        print(
            f"     subieron {len(suben)} de {len(medibles)} "
            f"({len(suben) * 100 / len(medibles):.0f} %)"
        )

    print()
    print("  " + "-" * 70)

    if cambio["pujariamos_menos"]:
        print("  EL FILTRO NOS HARIA PUJAR MENOS.")
        print()
        print(
            f"     {cambio['pujadas_con_filtro']} pujas en vez de "
            f"{cambio['pujadas']}. Y el problema medido es que "
            f"aparecemos"
        )
        conversion = (
            cambio["ganadas"] * 100.0 / cambio["pujadas"]
            if cambio["pujadas"]
            else 0.0
        )
        print(
            f"     poco, no que elijamos mal: convertimos el "
            f"{conversion:.0f} %, el mejor"
        )
        print(
            "     de los ocho. Por la regla del encargo, ESO ES UN "
            "FALLO Y NO UNA MEJORA."
        )
    else:
        print("  El filtro no reduce el numero de pujas.")

    print("  " + "-" * 70)


def main() -> int:

    try:
        foto = cargar(FOTO)

    except (OSError, ValueError) as error:
        print(f"No se pudo abrir la foto ({FOTO}): {error}")
        return 0

    print(
        f"FOTO: {FOTO}   generated_at = "
        f"{(foto.get('meta') or {}).get('generated_at')}"
    )

    bloque_0()

    try:
        historico = cargar(HISTORICO)

    except (OSError, ValueError) as error:
        print(f"No se pudo abrir el historico: {error}")
        return 0

    print()
    print(f"HISTORICO: {HISTORICO}   sello = {historico.get('updated_at')}")

    series = series_diarias(historico)

    bloque_1(series)

    bloque_2()

    bloque_3(series)

    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
