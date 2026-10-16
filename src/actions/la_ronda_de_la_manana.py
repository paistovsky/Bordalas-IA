"""
LA RONDA DE LA MAÑANA (12/10/2026)

POR QUE EXISTE

    Lo pidió el dueño el 12/10: «cada día, revisar quiénes están nuevos
    en el mercado, leer sus noticias y pujar por todos los que se pueda
    si van a subir». Es lo que hacen Pollo17 y Luismi (E28: ~2-2,5 M a
    la semana): compran al Computer a quien SUBE (E1), tiran de la
    deuda entre jornadas y se lo revenden al Computer a los pocos días,
    liquidando antes de cada jornada. A Pepe la reventa le cabe en la
    caja libre, y la caja libre casi nunca llega: no lo hacemos nunca.

LA REGLA

    1. A quién: del Computer, no nuestro, sin puja nuestra, no vetado ni
       protegido por el gestor, estado «ok» (las noticias solo como
       guardia, E4: ni lesionados, ni dudas, ni sancionados, ni lo que no
       se sepa), subiendo de verdad (`priceIncrement` de al menos la
       `la_subida_minima` de su tramo de precio, E1 y la medida del 12/10:
       un tic de +10.000 no basta) y que juega y puntúa (3 partidos o más
       y 3 puntos por partido o más). Primero el que más sube en
       proporción a su precio.
    2. Cuánto: precio + 1 % redondeado a miles (E9: sin pelear la
       subasta). Como mucho `TOPE_POR_VIAJE` por jugador; todo lo de la
       ronda (pujas vivas + lo comprado, a lo pagado) como mucho
       `TOPE_TOTAL` (sin tope: «se ejecuta toda la deuda»); y nunca más
       que `maximumBid` - `RESERVA` (que ya descuenta las pujas vivas).
    3. Cuándo: en CADA vuelta (el dueño, 12/10: «revisión cada ciclo,
       que para eso está 24/7») salvo en la zona de silencio, y solo si
       la jornada está a `HORAS_SIN_COMPRAR` o más. Sin calendario, no
       compra.
    4. Salida (solo lo del libro y lo que tenemos): se publica a su valor;
       se acepta la oferta del Computer con beneficio (pagado + 1 %); el
       primer día que baja (E3), a pagado - 2 %; a menos de
       `HORAS_LIQUIDAR` de la jornada, a pagado - 7 %; a menos de
       `HORAS_SOLVENCIA`, lo que ofrezca (en rojo al empezar la jornada
       se hacen 0 puntos). Con una ronda jugándose
       (`la_proxima_jornada.jornada_en_curso`) no se acepta ninguna
       oferta, solo se publica: el que se vende con su partido por jugar
       deja de puntuar para nosotros. Las horas a la jornada cuentan
       hasta el próximo cierre de Biwenger, aplazados incluidos (el
       Levante-Athletic de la J6, el 21/10).

QUE NO HACE

    No compra a rivales (salvo, con `ENV_PUERTA`, a los que piden su
    valor: ver LA PUERTA), no sube pujas, no vende a nadie que no haya
    comprado ella (lo apunta en `LIBRO`) ni a un protegido del gestor.

    Con `ENV_CARTERA` (LA CARTERA, 16/10) cambian 2, 3 y 4: puja para
    ganar a los que suben, cerca de la jornada compra solo con caja, y
    aguanta lo que sube en vez de revenderlo antes de la jornada.

    Nace APAGADA: `BORDALAS_LA_RONDA_DE_LA_MANANA`. Nunca lanza.
"""

from __future__ import annotations

import json
import math
import os

from datetime import datetime, timezone
from pathlib import Path

from src.actions.los_chollos import (
    CALENDARIO, MINUTOS_ULTIMA_VUELTA, _int, _puede_escribir, horas_a_la_jornada,
)


ENV = "BORDALAS_LA_RONDA_DE_LA_MANANA"
RAIZ = Path(__file__).parents[2]
LIBRO = RAIZ / "data" / "trading" / "la_ronda.json"

TOPE_POR_VIAJE = 3_000_000
TOPE_TOTAL = None                # el dueño (12/10): «se ejecuta toda la deuda»; manda maximumBid - RESERVA
RESERVA = 1_000_000             # lo que se deja sin tocar de `maximumBid`
HORAS_SIN_COMPRAR = 40           # lo comprado tiene que recibir al menos una oferta del Computer (en el reset) antes de la jornada
HORAS_LIQUIDAR = 36
HORAS_SOLVENCIA = 20
SUBE = 1.01                     # la puja (E9) y el beneficio mínimo
BAJA = 0.98                     # el primer día que baja (E3)
LIQUIDA = 0.93                  # cerca de la jornada
PUNTOS_POR_PARTIDO = 3.0
PARTIDOS_MINIMOS = 3

# LA SUBIDA MÍNIMA (12/10/2026). Medido sobre
# data/autopilot/price_history.json (n = 7.286 días-jugador, 398 jugadores,
# 55 días, estable en las dos mitades): de 1 M para arriba, un solo tic de
# +10.000 sigue subiendo solo el 70,5 % de las veces (n = 1.154) y a 7
# días la mediana es -0,95 %; +20.000 sigue el 90,5 % (+1,9 %), +30-50 mil
# el 97,4 %. Dentro de cada tramo de precio, el tercio de abajo por % de
# subida sigue el 77-82 % y el de arriba el 96-100 %: los cortes por
# tramo son de esa misma medida. Se sigue ordenando por sube/precio (E1,
# n = 191 viajes; E28).
#   (hasta este precio, sin incluir; % del precio; mínimo en euros)
TRAMOS_DE_SUBIDA = (
    (1_000_000, 0.031, 0),
    (3_000_000, 0.011, 20_000),
    (6_000_000, 0.005, 20_000),
    (None, 0.0045, 20_000),
)


def activa() -> bool:
    try:
        return str(os.environ.get(ENV, "")).strip().lower() in {"1", "true", "si", "yes"}
    except Exception:                               # noqa: BLE001
        return False


# LA PUERTA, A PRECIO DE MERCADO (16/10/2026)
#
#     El dueño, 16/10 noche: «Pollo nos sigue ganando pujas… sigue
#     distanciándose en patrimonio… ponlo en marcha ya». Lo que sube ese
#     día no estaba en el Computer: estaba en las listas de los managers
#     (Álvaro Núñez +3,7 %/día pidiendo 1.080.000 por 1.070.000 de valor;
#     Freeman +4 %/día pidiendo 1.992.000 por 2.000.000). La puerta se
#     cerró en septiembre con datos (EL-PUESTO-DE-MANDO: pedían +14,5 % de
#     media y salía -13,2 %); el ÚNICO grupo en verde era el de los que
#     piden su valor (+-3 %: n=10, +2,6 %). Se abre solo para ese grupo:
#     piden como mucho su valor + `PRIMA_DEL_MANAGER`, y pasan las mismas
#     reglas de la ronda (sube de verdad, está bien, juega). La puja va a
#     nombre del vendedor (`vendedor`); el resto, igual que con el
#     Computer. Nace APAGADA: `ENV_PUERTA`.
ENV_PUERTA = "BORDALAS_LA_PUERTA_A_PRECIO_DE_MERCADO"
PRIMA_DEL_MANAGER = 0.03


def la_puerta_abierta() -> bool:
    try:
        return str(os.environ.get(ENV_PUERTA, "")).strip().lower() in {"1", "true", "si", "yes"}
    except Exception:                               # noqa: BLE001
        return False


def los_de_managers(de_managers, fichas, veto=frozenset()) -> tuple:
    """
    De lo que venden los managers, lo que piden a su precio de mercado
    (como mucho su valor + `PRIMA_DEL_MANAGER`): ({pid: lo que piden},
    {pid: vendedor}). El valor es el de la ficha del catálogo; sin valor
    o sin vendedor, fuera. Pura. Nunca lanza.
    """

    piden, vendedores = {}, {}
    try:
        for pid, v in (de_managers or {}).items():
            pid = _int(pid)
            if pid is None or pid in (veto or ()) or not isinstance(v, dict):
                continue
            pide = _int(v.get("precio"), 0) or 0
            valor = _int((fichas.get(pid) or {}).get("price"), 0) or 0
            vendedor = _int(v.get("vendedor"))
            if pide <= 0 or valor <= 0 or vendedor is None:
                continue
            if pide > valor * (1 + PRIMA_DEL_MANAGER):
                continue
            piden[pid] = pide
            vendedores[pid] = vendedor
    except Exception:                               # noqa: BLE001
        return {}, {}
    return piden, vendedores


# LA CARTERA (16/10/2026)
#
#     El dueño, 16/10 noche: «Hazlo ya. Que se revaloricen, la misma
#     estrategia que ellos». Medido sobre el tablón (10/08 a 16/10, 855
#     eventos): Pollo17 pasó de 52,9 M a 103,3 M y +46,1 M son la subida de
#     precio de una plantilla de ~20 jugadores que compra cuando suben y
#     AGUANTA (sus viajes de más de 7 días: n=32, +18,68 M, el 86 %; los de
#     3 días o menos, +1,03 M). Pepe, revendiendo antes de cada jornada:
#     n=42, -2,84 M. Y las subastas de los que suben tienen rival: la liga
#     las gana a +8,1 % de mediana (+7,2 % si sube 0,5-2 %, +10,4 % si 2-4 %,
#     +20,9 % si más), Pollo17 a +7,4 %; a +1 % perdimos las 20.
#
#     Con `ENV_CARTERA` la ronda:
#       1. AGUANTA mientras sube (`priceIncrement` > 0): publicado, para
#          que llegue la oferta del Computer, pero no se cobra. El primer
#          día que no sube se vende a lo que ofrezca el Computer desde el
#          97 % de su valor (simulado sobre todas las señales: +4,8 % de
#          mediana por viaje frente a +1,9 % revendiendo antes de la
#          jornada; Pollo17 vende en un día de bajada en 47 de 64). Sin
#          liquidar por la jornada: la caja de la jornada la cuadra
#          `el_cierre_de_la_jornada`, que vende lo justo de lo que no juega.
#       2. PUJA PARA GANAR en el Computer, con la prima de su TRAMO DE
#          PRECIO (`PRIMAS_DE_LA_CARTERA`): en los baratos la prima se
#          recupera (por debajo de 1 M, +33 % a 7 días en las señales; de 1
#          a 3 M, +9,5 %) y en los caros no (con +10 %, -4,2 % de 3 a 6 M):
#          ahí, +1 %. Terminada en 9.000 (Pollo17 termina en 7.000: 142 de
#          sus 150 pujas). A los managers, lo que piden + 1 % (no es una
#          subasta).
#       3. Cerca de la jornada (menos de `HORAS_SIN_COMPRAR`) no compra,
#          como siempre: lo que se gana en el último reset no se puede
#          vender antes de empezarla (revisión del 16/10: comprar ahí «con
#          caja» gastaba dos veces la caja que los chollos ya habían
#          pujado en la misma vuelta).
#       4. Como mucho `MAXIMO_EN_PLANTILLA` entre plantilla y pujas vivas,
#          y hasta `TOPE_POR_VIAJE_CARTERA` por jugador (Pollo17 compra a
#          3,49 M de mediana; con 3 M el tramo de los caros no existía).
#     Nace APAGADA: `ENV_CARTERA`.
ENV_CARTERA = "BORDALAS_LA_CARTERA"
MAXIMO_EN_PLANTILLA = 20
TOPE_POR_VIAJE_CARTERA = 6_000_000
VENDE_SI_BAJA = 0.97
#   (hasta este precio, sin incluir; prima sobre el precio)
PRIMAS_DE_LA_CARTERA = (
    (1_000_000, 0.12),
    (3_000_000, 0.05),
    (None, 0.01),
)


def la_cartera_activa() -> bool:
    try:
        return str(os.environ.get(ENV_CARTERA, "")).strip().lower() in {"1", "true", "si", "yes"}
    except Exception:                               # noqa: BLE001
        return False


def los_que_aguanta(libro_ruta=None) -> set:
    """
    Los del libro de la ronda mientras LA CARTERA está encendida: ni el
    motor viejo (solvencia, aceptar antes de caducar) ni nadie más que la
    ronda y el cierre los venden. Vacío si está apagada. Nunca lanza.
    """

    try:
        if not la_cartera_activa():
            return set()
        return {p for p in (_int(k) for k in leer_libro(libro_ruta)) if p is not None}
    except Exception:                               # noqa: BLE001
        return set()


def la_puja_de_la_cartera(precio, sube=None) -> int:
    """
    Lo que se puja en el Computer por uno que sube: precio + la prima de
    su tramo de precio, bajado a la decena de mil y terminado en 9.000;
    nunca menos que `la_puja`. Con basura, `la_puja`. Nunca lanza.
    """

    try:
        precio = _int(precio, 0) or 0
        if precio <= 0:
            return la_puja(precio)
        prima = PRIMAS_DE_LA_CARTERA[-1][1]
        for hasta, p in PRIMAS_DE_LA_CARTERA:
            if hasta is None or precio < hasta:
                prima = p
                break
        puja = int(precio * (1 + prima)) // 10_000 * 10_000 + 9_000
        return max(puja, la_puja(precio))
    except Exception:                               # noqa: BLE001
        return la_puja(precio)


def el_suelo_de_la_cartera(pagado, incremento, valor):
    """
    Lo mínimo que se acepta del Computer por uno de la cartera; None si
    sube (se aguanta). Pura. Nunca lanza (con basura, None: se aguanta).
    """

    try:
        sube = _int(incremento)
        if sube is None or sube > 0:
            return None
        valor = _int(valor, 0) or 0
        if valor <= 0:
            return None
        return int(valor * VENDE_SI_BAJA)
    except Exception:                               # noqa: BLE001
        return None


def la_puja(precio: int) -> int:
    """Precio + 1 %, redondeado a miles (E9)."""
    return int(round(precio * SUBE, -3))


def la_subida_minima(precio) -> int | None:
    """
    Lo mínimo que tiene que subir hoy (`priceIncrement`) un jugador de
    este precio para que la ronda puje: el % de su tramo, y nunca menos
    de 20.000 € de 1 M para arriba (`TRAMOS_DE_SUBIDA`). None si no hay
    precio (sin precio no se puja).
    """
    try:
        precio = _int(precio, 0) or 0
        if precio <= 0:
            return None
        for hasta, pct, minimo in TRAMOS_DE_SUBIDA:
            if hasta is None or precio < hasta:
                return max(int(minimo), math.ceil(round(precio * pct, 6)))
        return None
    except Exception:                               # noqa: BLE001
        return None


def el_suelo(pagado: int, incremento, horas_jornada) -> int:
    """Lo mínimo que se acepta del Computer por un jugador de la ronda."""
    suelo = SUBE
    if (_int(incremento, 0) or 0) < 0:
        suelo = min(suelo, BAJA)
    # Sin calendario se trata como cerca (liquidar), pero no a cualquier precio.
    if horas_jornada is None or horas_jornada < HORAS_LIQUIDAR:
        suelo = min(suelo, LIQUIDA)
    if horas_jornada is not None and horas_jornada < HORAS_SOLVENCIA:
        return 0
    return int(pagado * suelo)


def juega(ficha: dict) -> bool:
    """3 partidos o más y 3 puntos por partido o más."""
    partidos = (_int(ficha.get("playedHome"), 0) or 0) + (_int(ficha.get("playedAway"), 0) or 0)
    if partidos < PARTIDOS_MINIMOS:
        return False
    return (_int(ficha.get("points"), 0) or 0) / partidos >= PUNTOS_POR_PARTIDO


def decidir(
    *, mercado, fichas, nuestras_pujas, plantilla, ofertas_del_computer,
    en_venta, maximo_de_puja, minutos_al_reset, horas_jornada, libro,
    protegidos=frozenset(), puede_escribir=True, en_curso=False,
    cartera=False, de_managers=frozenset(),
) -> list:
    """Qué hace la ronda en esta vuelta. Pura.

        fichas   {player_id: ficha del catálogo} (price, priceIncrement,
                 status, points, playedHome, playedAway)
        libro    {"player_id": lo pagado} de lo comprado por la ronda
        en_curso hay una ronda de Biwenger jugándose: no se acepta
                 ninguna oferta (publicar sí)
        cartera  LA CARTERA (`ENV_CARTERA`): aguanta lo que sube y puja
                 para ganar
        de_managers  los del `mercado` que vende un manager (la puerta):
                 a esos, lo que piden + 1 %
    """

    acciones = []
    protegidos = set(protegidos or ())

    # 4. SALIR de lo comprado por la ronda.
    for pid, pagado in (libro or {}).items():
        pid, pagado = _int(pid), _int(pagado, 0) or 0
        if pid not in plantilla or pid in protegidos or pagado <= 0:
            continue
        ficha = fichas.get(pid) or {}
        if cartera:
            # LA CARTERA: mientras sube, se aguanta (suelo None); la caja
            # de la jornada no la cuadra la ronda sino el cierre.
            suelo = el_suelo_de_la_cartera(
                pagado, ficha.get("priceIncrement"), ficha.get("price"))
        else:
            suelo = el_suelo(pagado, ficha.get("priceIncrement"), horas_jornada)
        oferta = ofertas_del_computer.get(pid)
        if (suelo is not None and oferta and not en_curso
                and (_int(oferta.get("amount"), 0) or 0) >= suelo):
            acciones.append({
                "accion": "ACEPTAR_OFERTA_DEL_COMPUTER", "player_id": pid,
                "offer_id": _int(oferta.get("offer_id")),
                "importe": _int(oferta.get("amount")), "pagado": pagado,
                "suelo": suelo, "ronda": True,
            })
        elif pid not in en_venta and _int(ficha.get("price")):
            acciones.append({
                "accion": "PONER_A_LA_VENTA", "player_id": pid,
                "precio": _int(ficha.get("price")), "ronda": True,
            })

    # 3. EN CADA VUELTA (el dueño, 12/10: «revisión cada ciclo, que para
    # eso está 24/7»), salvo en la zona de silencio, y lejos de la jornada.
    if (
        not puede_escribir
        or horas_jornada is None
        or horas_jornada < HORAS_SIN_COMPRAR
    ):
        return acciones

    # LA CARTERA: como mucho `MAXIMO_EN_PLANTILLA` entre plantilla y pujas.
    hueco = None
    if cartera:
        hueco = MAXIMO_EN_PLANTILLA - len(plantilla or ()) - len(nuestras_pujas or {})
        if hueco <= 0:
            return acciones

    # 2. Lo que ya lleva la ronda: pujas vivas + lo comprado, a lo pagado.
    expuesto = 0
    for pid, pagado in (libro or {}).items():
        pid = _int(pid)
        if pid in nuestras_pujas:
            expuesto += _int(nuestras_pujas[pid].get("amount"), 0) or 0
        elif pid in plantilla:
            expuesto += _int(pagado, 0) or 0
    disponible = (_int(maximo_de_puja, 0) or 0) - RESERVA

    # 1. Los que suben de verdad, están bien y juegan; el que más sube
    # (en proporción a su precio) primero. La subida mínima va por el
    # valor de hoy (la ficha; si no, lo que pide).
    candidatos = []
    for pid, precio in mercado.items():
        ficha = fichas.get(pid) or {}
        if not precio or pid in plantilla or pid in nuestras_pujas or pid in protegidos:
            continue
        if str(ficha.get("status") or "").lower() != "ok":
            continue
        sube = _int(ficha.get("priceIncrement"), 0) or 0
        minima = la_subida_minima(_int(ficha.get("price")) or precio)
        if sube <= 0 or minima is None or sube < minima or not juega(ficha):
            continue
        candidatos.append((sube / precio, pid, precio, sube))

    tope = TOPE_POR_VIAJE_CARTERA if cartera else TOPE_POR_VIAJE
    for _, pid, precio, sube in sorted(candidatos, reverse=True):
        puja = la_puja(precio)
        if cartera and pid not in de_managers and puja <= tope:
            # La prima nunca deja fuera a uno que cabe a precio + 1 %.
            puja = min(la_puja_de_la_cartera(precio, sube), tope)
        if puja > tope or (TOPE_TOTAL is not None and expuesto + puja > TOPE_TOTAL) or puja > disponible:
            continue
        if hueco is not None and hueco <= 0:
            break
        expuesto += puja
        disponible -= puja
        if hueco is not None:
            hueco -= 1
        acciones.append({
            "accion": "PUJAR", "player_id": pid, "importe": puja,
            "pide": precio, "sube": sube, "sustituye": None, "ronda": True,
        })

    return acciones


def leer_libro(ruta: Path | str | None = None) -> dict:
    try:
        return json.loads(Path(ruta or LIBRO).read_text())
    except Exception:                               # noqa: BLE001
        return {}


def correr(cycle, minutos_al_reset, escritor_factory=None,
           ahora: datetime | None = None, libro_ruta=None) -> dict:
    """La ronda, en esta vuelta. Nunca lanza."""

    salida = {"activa": activa(), "motivo": None, "acciones": [], "hechas": []}

    try:
        if not salida["activa"]:
            salida["motivo"] = "APAGADA"
            return salida

        from src.actions.la_orden_del_gestor import (
            _pid, ejecutar, leer_la_foto, protegidos, vetados,
        )
        from src.analysis.la_proxima_jornada import jornada_en_curso

        ahora = ahora or datetime.now(timezone.utc)
        snapshot = (cycle or {}).get("snapshot") or {}
        yo = _pid((snapshot.get("league") or {}).get("user"))
        foto = leer_la_foto(snapshot, yo)

        catalogo = (((snapshot.get("catalog") or {}).get("data") or {}).get("players")) or {}
        fichas = {}
        for k, f in catalogo.items():
            pid = _int(k)
            if pid is not None and isinstance(f, dict):
                fichas[pid] = f

        veto = vetados()
        mercado = {p: v for p, v in foto["mercado"].items() if p not in veto}

        # LA PUERTA (16/10/2026): con el interruptor, los de los managers
        # que piden su valor entran al mismo mercado (lo que piden hace de
        # precio) y se apunta a quién se le puja.
        vendedores = {}
        if la_puerta_abierta():
            piden, vendedores = los_de_managers(
                foto.get("de_managers"), fichas, veto)
            for pid, pide in piden.items():
                mercado.setdefault(pid, pide)
            salida["puerta"] = {"abierta": True, "a_precio_de_mercado": sorted(piden)}

        libro = leer_libro(libro_ruta)
        acciones = decidir(
            mercado=mercado, fichas=fichas,
            nuestras_pujas=foto["nuestras_pujas"], plantilla=foto["plantilla"],
            ofertas_del_computer=foto["ofertas_del_computer"],
            en_venta=foto["en_venta"], maximo_de_puja=foto["maximo_de_puja"],
            minutos_al_reset=minutos_al_reset,
            horas_jornada=horas_a_la_jornada(ahora), libro=libro,
            protegidos=protegidos(), puede_escribir=_puede_escribir(ahora),
            en_curso=jornada_en_curso(ahora, CALENDARIO),
            cartera=la_cartera_activa(), de_managers=frozenset(vendedores),
        )
        if la_cartera_activa():
            salida["cartera"] = {"activa": True, "saldo": foto.get("saldo"),
                                 "en_plantilla": len(foto["plantilla"]),
                                 "pujas_vivas": len(foto["nuestras_pujas"])}
        for a in acciones:
            pid = _int(a.get("player_id"))
            if a.get("accion") == "PUJAR" and pid in vendedores:
                a["vendedor"] = vendedores[pid]
        salida["acciones"] = acciones

        if not acciones:
            salida["motivo"] = "NADA_QUE_HACER"
            return salida

        if escritor_factory is None:
            from src.biwenger.write_client import BiwengerWriteClient

            escritor_factory = BiwengerWriteClient

        hechas = ejecutar(acciones, escritor_factory())
        salida["hechas"] = hechas

        # El libro, como el de los chollos: lo pujado queda apuntado para
        # revenderlo si se gana; lo vendido sale; lo que ni es nuestro ni
        # tiene puja viva se limpia solo.
        for pid in list(libro):
            if _int(pid) not in foto["plantilla"] and _int(pid) not in foto["nuestras_pujas"]:
                libro.pop(pid, None)
        for h in hechas:
            pid = str(h.get("player_id"))
            if h.get("accion") == "PUJAR" and h.get("exito"):
                libro[pid] = h.get("importe")
            elif h.get("accion") == "ACEPTAR_OFERTA_DEL_COMPUTER" and h.get("exito"):
                libro.pop(pid, None)
        try:
            ruta = Path(libro_ruta or LIBRO)
            ruta.parent.mkdir(parents=True, exist_ok=True)
            ruta.write_text(json.dumps(libro, indent=2) + "\n")
        except Exception:                           # noqa: BLE001
            pass

        salida["motivo"] = "EJECUTADA"

    except Exception as error:                      # noqa: BLE001
        salida["motivo"] = f"ERROR: {type(error).__name__}: {error}"

    return salida
