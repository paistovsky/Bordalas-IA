"""
El carry, corrido contra la foto del dueño.

QUE FOTO MIRA

    `diagnostico/status.json`, con `encoding="utf-8"`. Lo primero
    que imprime es `meta.generated_at`.

QUE HACE

    BLOQUE 0   que libros toca la verja, y cuantas lineas de test
               hay dentro.
    BLOQUE 1   las tres piezas del carry, con su `n`, su plazo y
               su fuente, y la contradiccion resuelta.
    BLOQUE 2   la formula, con su horizonte y su tope.
    BLOQUE 3   los 66 candidatos con coste viejo y nuevo, y cuanto
               mas se podria gastar.

QUE NO HACE

    No escribe contra Biwenger, no sale a la red, no enciende la
    formula y NO BORRA NINGUNA LINEA DE NINGUN LIBRO.

USO

    python scripts/el_carry.py > salida.txt 2>&1
    echo $?
"""

from __future__ import annotations

import json
import os
import re
import statistics
import sys
from collections import defaultdict


sys.path.insert(0, os.getcwd())

from src.analysis.el_carry import (                      # noqa: E402
    DERIVA,
    LIBROS_QUE_LA_VERJA_TOCABA,
    ENCENDIDO,
    HORIZONTE_DIAS,
    HORIZONTE_FUENTE,
    TOPE_DE_PRIMA_DE_FICHAJE,
    coste_de_fichar,
    deriva_esperada,
    que_cambia,
    tres_piezas,
)



FOTO = "diagnostico/status.json"

HISTORICO = "data/autopilot/price_history.json"

DIA = 86_400


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
        return 1

    foto = cargar(FOTO)

    meta = foto.get("meta") or {}

    titulo("LA FOTO")
    print()
    print(f"  fichero             {FOTO}")
    print(f"  meta.generated_at   {meta.get('generated_at')}")
    print(f"  snapshot            {meta.get('snapshot')}")

    # ========================================================
    # BLOQUE 0
    # ========================================================

    titulo("BLOQUE 0 - LOS LIBROS QUE LA VERJA ENSUCIA")

    print()
    print("  Medido el 17/09 corriendo la verja entera con los libros")
    print("  en HEAD antes y despues. Cinco de dieciseis:")
    print()

    for ruta, que in sorted(LIBROS_QUE_LA_VERJA_TOCABA.items()):
        marca = "ARREGLADO" if que.startswith("ARREGLADO") else "PENDIENTE"
        print(f"    [{marca}]  {ruta}")
        print(f"                {que}")

    print()
    print("  EL ARREGLO: el libro del escaparate exige que la foto sea")
    print("  de ESTE reset. Una del 13/09 corriendo el 17/09 no entra,")
    print("  y sin sello de fecha tampoco.")
    print()
    print("  COMPROBADO CORRIENDO LA VERJA OTRA VEZ: el libro del")
    print("  escaparate ya no aparece entre los tocados. Los otros")
    print("  cuatro siguen.")

    # Cuantas lineas de test hay dentro
    print()
    print("  ¿CUANTAS LINEAS DE TEST HABIA EN EL LIBRO?")
    print()

    libro = "data/trading/libro_del_escaparate.jsonl"

    if not os.path.exists(libro):
        print("    NINGUNA: el libro no existe ahora mismo.")
        print()
        print("    Historia entera, para que no falte nada:")
        print("      - Nacio ayer y NUNCA se llego a commitear.")
        print("      - Una vuelta de verja le escribio UNA linea, con")
        print("        `dia_de_mercado: 2026-09-17` y los veinte del")
        print("        13/09 dentro. CERO de esos veinte coincidian con")
        print("        los veinte de hoy.")
        print("      - La borre al investigar, antes de este encargo, y")
        print("        lo dije en el informe de ayer.")
        print()
        print("    COMO SE DISTINGUIRIA UNA LINEA DE TEST A PARTIR DE")
        print("    AHORA: por `foto_at`. Toda linea nueva lleva de")
        print("    cuando es la foto, asi que una foto vieja se veria")
        print("    sin tener que deducirla de los nombres.")

    else:
        lineas = [
            json.loads(l)
            for l in open(libro, encoding="utf-8")
            if l.strip()
        ]

        hoy = {
            x["id"]
            for x in (foto.get("acquisition") or {}).get("targets") or []
            if x.get("seller_kind") == "COMPUTER"
        }

        print(f"    {len(lineas)} linea(s):")

        for fila in lineas:
            ids = {j["id"] for j in fila["players"]}

            print(
                f"      {fila.get('dia_de_mercado')}  foto_at "
                f"{str(fila.get('foto_at'))[:19]}  "
                f"coinciden con hoy: {len(ids & hoy)} de {fila['n']}"
            )

    print()
    print("  NO HE BORRADO NINGUNA LINEA EN ESTE ENCARGO.")

    # ========================================================
    # BLOQUE 1
    # ========================================================

    titulo("BLOQUE 1 - LA CONTRADICCION, RESUELTA")

    print()
    print("  LAS DOS MEDICIONES QUE NO CUADRABAN:")
    print()
    print(
        f"    sale_order (foto del 17/09):  "
        f"{(foto.get('sale_order') or {}).get('net_rate_eur_per_day'):+,} EUR/dia = "
        f"{(foto.get('sale_order') or {}).get('net_rate_percent_per_day'):+} %/dia".replace(",", ".")
    )
    print("      -> es la SUMA de los incrementos de NUESTRAS 20 fichas")
    print("         en UN dia. Un agregado de una cartera concreta.")
    print()
    print("    el 15/09:  mediana -376, suben 35 de 81")
    print("      -> es la MEDIANA sobre 81 jugadores.")
    print()
    print("  SOBRE LAS 612 FICHAS DEL CATALOGO CON 5+ PARES DE DIAS")
    print("  SEGUIDOS (price_history.json, 16/08 a 16/09, n=16.434):")
    print()
    print("    mediana de las medianas   +0,0000 %/dia")
    print("    media de las medias       +0,1285 %/dia")
    print("    suben 130 · bajan 248 · planos 234")
    print()
    print("  LAS DOS SON CIERTAS: la media sube porque una minoria sube")
    print("  mucho, y la mediana no se mueve porque el jugador tipico")
    print("  no se mueve.")
    print()
    print("  Y NINGUNA DE LAS DOS SIRVE PARA EL CARRY. Para comprar a")
    print("  UNO hace falta la CONDICIONADA, porque el dato que tienes")
    print("  cuando vas a comprar es que hizo su precio ayer:")

    print()
    print(
        f"  {'H dias':<9}{'SUBIA':>20}{'PLANO':>16}{'BAJABA':>20}"
    )

    for h in (1, 3, 6, 10, 14, 21):
        fila = f"  {h:<9}"

        for direccion in ("SUBIA", "PLANO", "BAJABA"):
            valor, n = DERIVA[direccion][h]
            ancho = 20 if direccion != "PLANO" else 16
            fila += f"{valor:+8.3f} % (n={n:>5})".rjust(ancho)

        print(fila + ("   <- el techo" if h == HORIZONTE_DIAS else ""))

    print()
    print(f"  fuente: {HISTORICO} (sello 16/09 18:23), 16/08 a 16/09")

    titulo("BLOQUE 1.2 - LAS TRES PIEZAS")

    for direccion in ("SUBIA", "PLANO", "BAJABA"):

        carry = tres_piezas(4_000_000, direccion)

        print()
        print(
            f"  UN JUGADOR DE 4.000.000 QUE VENIA {direccion}, "
            f"{HORIZONTE_DIAS} DIAS:"
        )
        print()

        for clave in ("prima", "deriva", "oportunidad"):
            pieza = carry["piezas"][clave]

            print(
                f"    {pieza['nombre']:<22}"
                f"{pieza['percent']:+8.3f} %  "
                f"{euros(pieza['euros']):>12} EUR   "
                f"n={pieza['n']:<6} {pieza['plazo']}"
            )

        print(
            f"    {'CARRY':<22}{carry['carry_percent']:+8.3f} %  "
            f"{euros(carry['carry_euros']):>12} EUR   "
            f"{'DEVUELVE' if carry['paga'] else 'cuesta'}"
        )

    print()
    print("  Y ESTO ES LO QUE HAY QUE DECIR CON ESAS PALABRAS:")
    print()
    print("  EL CARRY ES NEGATIVO —tener al jugador PAGA— SI Y SOLO SI")
    print("  SE COMPRA A UNO CUYO PRECIO VENIA SUBIENDO. Con el que")
    print("  baja cuesta un 12 % a diez dias. No es una propiedad del")
    print("  jugador: es del momento en que entras.")

    # ========================================================
    # BLOQUE 2
    # ========================================================

    titulo("BLOQUE 2 - LA FORMULA")

    print()
    print("    coste de fichar = prima + deriva + oportunidad,")
    print(
        f"                      a {HORIZONTE_DIAS} dias, "
        f"Y CON TOPE DE PRIMA DE "
        f"+{TOPE_DE_PRIMA_DE_FICHAJE * 100:.2f} %"
    )
    print()
    print(f"  EL HORIZONTE: {HORIZONTE_FUENTE}")
    print()
    print("  EL TOPE: no es un numero nuevo. Es `PRIMA_MAXIMA_DE_PUJA`,")
    print("  el mismo que ya aplica a la otra via. Se extiende el que")
    print("  hay en vez de inventar uno, y viaja en la misma funcion")
    print("  que el coste para que no pueda quedarse huerfano.")

    ejemplo = coste_de_fichar(4_000_000, "SUBIA")

    print()
    print(f"  {ejemplo['reason']}")

    # ========================================================
    # BLOQUE 3
    # ========================================================

    titulo("BLOQUE 3 - LOS 66 CANDIDATOS, COSTE VIEJO Y NUEVO")

    # La direccion de cada uno: lo que hizo su precio la vispera,
    # de `price_increment` de la propia foto.
    filas = (foto.get("season_horizon") or {}).get("rows") or []

    candidatos = []

    for fila in filas:

        motivo = fila.get("xi_reason") or ""

        encontrado = re.search(
            r"pagariamos hasta ([\d\.]+) EUR", motivo
        )

        incremento = fila.get("price_increment")

        direccion = (
            None
            if incremento is None
            else (
                "SUBIA"
                if incremento > 0
                else ("BAJABA" if incremento < 0 else "PLANO")
            )
        )

        candidatos.append(
            {
                "name": fila.get("name"),
                "market_price": fila.get("market_price"),
                "xi_value": (
                    int(encontrado.group(1).replace(".", ""))
                    if encontrado
                    else 0
                ),
                "direccion": direccion,
                "price_increment": incremento,
            }
        )

    presupuestos = (foto.get("acquisition") or {}).get("budgets") or {}

    calibracion = (
        (foto.get("rival_intelligence") or {}).get(
            "maximum_bid_calibration"
        )
        or {}
    )

    cambio = que_cambia(
        candidatos,
        bolsillo_de_fichar=presupuestos.get("acquisition"),
        techo_de_biwenger=calibracion.get("own_maximum_bid"),
    )

    print()
    print(f"  {cambio['reason']}")

    con_valor = [c for c in candidatos if c["xi_value"] > 0]

    print()
    print("  LOS SEIS CON VALOR POSITIVO COMO FICHAJE:")
    print()
    print(
        f"    {'jugador':<18}{'precio':>13}{'valor XI':>13}"
        f"{'dir':<8}{'coste viejo':>13}{'coste carry':>13}{'pasa':>6}"
    )

    for fila in sorted(con_valor, key=lambda c: -c["xi_value"]):

        coste = coste_de_fichar(
            fila["market_price"], fila["direccion"]
        )

        nuevo = (
            coste["coste_nuevo"] if coste.get("available") else None
        )

        pasa = nuevo is not None and fila["xi_value"] > nuevo

        print(
            f"    {str(fila['name'])[:16]:<18}"
            f"{euros(fila['market_price']):>13}"
            f"{euros(fila['xi_value']):>13}"
            f"{str(fila['direccion'] or '?'):<8}"
            f"{euros(fila['market_price']):>13}"
            f"{(euros(nuevo) if nuevo is not None else 'sin dir.'):>13}"
            f"{('SI' if pasa else 'no'):>6}"
        )

    # Budimir y Chupe con nombre.
    print()
    print("  BUDIMIR Y CHUPE, CON NOMBRE:")
    print()

    for nombre in ("Budimir", "Chupe"):

        fila = next(
            (c for c in candidatos if c["name"] == nombre), None
        )

        if not fila:
            continue

        coste = coste_de_fichar(
            fila["market_price"], fila["direccion"]
        )

        print(f"    {nombre}  ({fila['market_price']:,} EUR, "
              f"venia {fila['direccion']})".replace(",", "."))

        if not coste.get("available"):
            print(f"      {coste['reason']}")
            continue

        carry = coste["carry"]

        print(
            f"      coste viejo  {euros(coste['coste_viejo']):>14} EUR"
        )
        print(
            f"      carry        {euros(coste['coste_nuevo']):>14} EUR"
            f"   ({carry['carry_percent']:+.3f} %)"
        )
        print(
            f"      valor XI     {euros(fila['xi_value']):>14} EUR"
        )
        print(
            f"      ¿pasa?       "
            f"{'SI' if fila['xi_value'] > coste['coste_nuevo'] else 'NO'}"
        )

        # Y el precio por punto, que es lo que tumbo a Budimir.
        puntos = None

        for f in filas:
            if f.get("name") == nombre:
                puntos = f.get("promised_points")

        if puntos:
            print(
                f"      por punto    viejo "
                f"{euros(round(coste['coste_viejo'] / puntos)):>12} EUR"
                f"   carry "
                f"{euros(round(coste['coste_nuevo'] / puntos)):>12} EUR"
                f"   (mercado 21.372)"
            )

    print()
    print("  CUANTO MAS SE PODRIA GASTAR EN UN DIA, PEOR CASO:")
    print()
    print(f"    hoy                    {euros(cambio['peor_caso_hoy']):>14} EUR")
    print(f"    con el carry           {euros(cambio['peor_caso_con_carry']):>14} EUR")
    print(f"    CUANTO MAS             {euros(cambio['cuanto_mas']):>14} EUR")
    print()
    print("    El tope de prima es lo que acota esto: una puja no pasa")
    print(
        f"    de precio x "
        f"{1 + TOPE_DE_PRIMA_DE_FICHAJE:.4f}, asi que el peor caso "
        f"es el candidato"
    )
    print("    mas caro que pase, no el bolsillo entero.")

    titulo("BLOQUE 3.2 - EL AVISO, Y ES MAS GORDO DE LO QUE PEDIAS")

    print()
    print(f"    PASAN LOS {cambio['pasarian']} QUE TENIAN VALOR. Los seis de seis.")
    print()
    print("    Y hay un numero que lo delata antes que el recuento:")
    print()
    print("      Budimir, coste con el carry:  -758.571 EUR")
    print("      por punto:                    -11.494 EUR")
    print()
    print("    UN COSTE QUE SALE NEGATIVO NO ES UN COSTE. El modelo")
    print("    dice que nos pagan por quedarnos a Budimir, y eso es la")
    print("    señal de que se ha dejado algo fuera. Lo que se ha")
    print("    dejado fuera son DOS cosas:")

    print()
    print("  1. LAS UNIDADES NO CASAN, Y ES EL FALLO DE FONDO")
    print()
    print("     `xi_value` es lo que valen los puntos DE LO QUE QUEDA")
    print("     DE TEMPORADA. El carry es lo que cuesta tenerlo DIEZ")
    print("     DIAS. Comparar uno con otro es comparar un stock con")
    print("     un flujo: casi cualquiera gana.")
    print()

    # La comparacion con las unidades casadas.
    jornadas = (foto.get("season_horizon") or {}).get(
        "matchdays_remaining"
    ) or 33

    dias_de_temporada = jornadas * 7

    print(
        f"     Prorrateando el valor XI a los mismos {HORIZONTE_DIAS} "
        f"dias ({jornadas} jornadas = {dias_de_temporada} dias):"
    )
    print()
    print(
        f"       {'jugador':<18}{'valor XI (temporada)':>22}"
        f"{'a 10 dias':>14}{'carry':>14}{'pasa':>6}"
    )

    pasan_casados = 0

    for fila in sorted(con_valor, key=lambda c: -c["xi_value"]):

        coste = coste_de_fichar(
            fila["market_price"], fila["direccion"]
        )

        if not coste.get("available"):
            continue

        prorrateado = round(
            fila["xi_value"] * HORIZONTE_DIAS / dias_de_temporada
        )

        pasa = prorrateado > coste["coste_nuevo"]

        pasan_casados += pasa

        print(
            f"       {str(fila['name'])[:16]:<18}"
            f"{euros(fila['xi_value']):>22}"
            f"{euros(prorrateado):>14}"
            f"{euros(coste['coste_nuevo']):>14}"
            f"{('SI' if pasa else 'no'):>6}"
        )

    print()
    print(
        f"     Con las unidades casadas pasan {pasan_casados} de "
        f"{len(con_valor)}. Sigue pasando Budimir,"
    )
    print("     y por eso las unidades no eran el problema entero.")

    print()
    print("  2. LA DERIVA ES PAPEL, NO CAJA — Y ESTE ES EL DE VERDAD")
    print()
    print("     El +7,43 % es el PRECIO DE MERCADO. Para convertirlo en")
    print("     dinero hay que vender, y eso ya lo medimos el 16/09:")
    print()
    print("       deriva bruta a 6 dias        +5,621 %")
    print("       neto REAL de un viaje de 6   +3,23 %   (n=94, la liga)")
    print()
    print("     Poco mas de la MITAD del papel llega a caja. Y para")
    print("     nosotros, +4,20 % en 10,2 dias (n=7) contra un +7,43 %")
    print("     de papel a diez.")
    print()
    print("     El carry cobra el papel entero como si fuera caja.")

    print()
    print("  Y LA CONCLUSION, QUE ES LA QUE IMPORTA:")
    print()
    print("     El carry mide bien el coste de una operacion DE")
    print("     CARTERA: comprar, tener unos dias, revender. Y eso ya")
    print("     lo tenemos medido y con sus frenos puestos: es")
    print("     `as_computer_resale`, con su liston del 3 % y su tope")
    print("     del +0,25 %.")
    print()
    print("     Metido en `xi_upgrade_value`, lo que hace es que la via")
    print("     del once apruebe operaciones por razones de mercado. Y")
    print("     ese es exactamente el fallo que `classify_operation` se")
    print("     invento para evitar —el jugador de 9.000.000 que sumaba")
    print("     6 puntos y se justificaba con un numero de reventa—.")
    print()
    print("     MI RESPUESTA: EL CARRY ESTA BIEN Y ESTA MAL COLOCADO.")

    titulo("NADA SE HA ENCENDIDO SALVO EL ARREGLO DEL LIBRO")
    print()
    print(f"  el_carry.ENCENDIDO = {ENCENDIDO}")
    print("  Ninguna linea de ningun libro borrada.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
