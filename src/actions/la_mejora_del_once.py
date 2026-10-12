"""
LA MEJORA DEL ONCE (12/10/2026)

POR QUE EXISTE

    El dueño, 12/10: «2 días que te he preguntado, 2 días que había
    jugadores en el mercado que eran interesantes para mejorar el XI o
    subían de precio y Pepe no ha hecho nada… Se compra, se ejecuta toda
    la deuda, se aguanta y se vende más caro o se mejora el XI. Revisión
    cada ciclo, que para eso está 24/7». Y: «no se trata de ejecutar mis
    órdenes al pie de la letra, se trata de que entiendas cómo funciona
    el juego».

    Hasta hoy la mejora del once la decidía `scripts/el_fichaje_del_dia.py`
    una vez al día, fuera de Pepe, y con la caja en positivo SIN deuda: el
    12/10 tiró a Iván Romero (por Jutglà, +1,7 puntos por jornada) por
    520.000 € y a Gerard Martín (por Diego Rico, +2,3) por 3,8 M. Los dos
    los tuvo que señalar el dueño.

LA REGLA

    Puntos esperados = puntos por partido x titularidad (la vara E16/E23).

    1. En CADA vuelta fuera de la zona de silencio y con la jornada a
       `HORAS_SIN_COMPRAR` o más (el relevo tiene que llegar en un reset y
       el que sale cobrar la oferta del Computer en el siguiente).
    2. Cambios de uno por uno y de la misma posición (el once no pierde
       su forma): entra uno del Computer de hoy (sano, 3+ partidos, 60 %+
       de titularidad) o uno que ya compró la ronda o los chollos (se lo
       queda el once y deja de revenderse: «se aguanta… o se mejora el
       XI»); sale un titular que no sea intocable ni protegido.
    3. Se busca la COMBINACIÓN (hasta `MAXIMO_POR_VUELTA` cambios) que más
       puntos suma, con al menos `GANANCIA_MINIMA`. Vale meter un cambio
       que pierde un poco de puntos si da caja para otro que gana más
       (cambiar caro por barato para fichar mejor).
    4. La caja, CON deuda: saldo - pujas vivas (las de la ronda y los
       chollos se venden solas) + lo que darán las ventas pendientes y el
       inventario de la ronda (al 95 % de su valor) + lo que dan los que
       salen (al 95 %) - lo que cuestan los que entran (precio + 1 %, E9).
       Tiene que quedar >= - `DEUDA_TOLERADA` si la jornada está a
       `HORAS_CON_DEUDA` o más (dos resets para arreglarlo), y >= 0 si no.
       Y las pujas, dentro de `maximumBid` - `RESERVA`.
    4b. Si la caja de la jornada YA no llega (pujas de la orden, compras
       con deuda) y faltan menos de `HORAS_DEFICIT`: se elige la
       combinación que la devuelve al mínimo perdiendo menos puntos, aunque
       pierda (vender caro y fichar barato antes que quedarse en rojo, que
       son 0 puntos). Antes de esa hora se espera: el premio de la jornada
       recién jugada entra en la caja sin hacer nada.
    5. Salida: el que sale se publica cuando su relevo está dentro, y se
       acepta la oferta del Computer desde el 90 % de su valor; a menos de
       `HORAS_SOLVENCIA` de la jornada y en rojo, la que haya. Si la puja
       se pierde, el que iba a salir se queda.

QUE NO HACE

    No toca a Yamal (salvo su llave de lesión), ni a los `proteger` de la
    orden del gestor, ni a nadie que la orden ya esté fichando o
    vendiendo. No sube pujas ni compra a rivales.

    Corre DESPUÉS del panel (necesita su titularidad), como paso propio
    del workflow: `python -m src.actions.la_mejora_del_once`.
    Nace APAGADA: `BORDALAS_LA_MEJORA_DEL_ONCE`. Nunca lanza.
"""

from __future__ import annotations

import json
import os

from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path


ENV = "BORDALAS_LA_MEJORA_DEL_ONCE"
RAIZ = Path(__file__).parents[2]
LIBRO = RAIZ / "data" / "trading" / "la_mejora.json"
STATUS = RAIZ / "dashboard" / "data" / "status.json"
V10 = RAIZ / "data" / "trading" / "v10_full_autonomous_status.json"

GANANCIA_MINIMA = 0.5            # puntos por jornada, la combinación entera
PEOR_FINANCIACION = -1.5         # lo más que se pierde en un cambio que da caja
MAXIMO_POR_VUELTA = 3
TITULARIDAD_MINIMA = 60
PARTIDOS_MINIMOS = 3
HORAS_SIN_COMPRAR = 40
HORAS_CON_DEUDA = 64
HORAS_DEFICIT = 88               # en rojo, desde aquí se cambia caro por barato
HORAS_SOLVENCIA = 20
DEUDA_TOLERADA = 1_000_000
RESERVA = 1_000_000
SUBE = 1.01                      # la puja (E9)
VENTA = 0.95                     # lo que se espera de la oferta del Computer
SUELO = 0.90                     # lo mínimo que se acepta por el que sale
CANDIDATOS = 25                  # de cada lista, para la combinación


def activa() -> bool:
    try:
        return str(os.environ.get(ENV, "")).strip().lower() in {"1", "true", "si", "yes"}
    except Exception:                               # noqa: BLE001
        return False


def _int(x, defecto=None):
    try:
        if x is None or isinstance(x, bool):
            return defecto
        return int(x)
    except (TypeError, ValueError):
        return defecto


def esperado(tasa, prob):
    """Puntos por jornada: puntos por partido x titularidad."""
    try:
        if tasa is None or prob is None:
            return None
        return float(tasa) * float(prob) / 100.0
    except (TypeError, ValueError):
        return None


def la_puja(precio: int) -> int:
    return int(round(precio * SUBE, -3))


def la_mejor_combinacion(cambios: list, caja: int, minimo_de_caja: int,
                         disponible: int, deficit: bool = False) -> list:
    """
    De los cambios posibles (cada uno con `entra`, `sale`, `puntos`,
    `caja`, `puja`), la combinación sin repetir jugador que más puntos
    suma con al menos `GANANCIA_MINIMA`, sin bajar la caja de
    `minimo_de_caja` ni pasar de `disponible` en pujas. A igualdad, la
    que deja más caja. Pura.

    Con `deficit` (la caja de la jornada ya no llega): vale una
    combinación que pierde puntos si es la que menos pierde de las que
    devuelven la caja a `minimo_de_caja` («fichar y luego ver con quién
    nos quedamos y vender para quedarnos en positivo», el dueño, 12/10).
    """

    mejoras = sorted((c for c in cambios if c["puntos"] >= GANANCIA_MINIMA),
                     key=lambda c: -c["puntos"])[:CANDIDATOS]
    financian = sorted((c for c in cambios
                        if PEOR_FINANCIACION <= c["puntos"] < GANANCIA_MINIMA and c["caja"] > 0),
                       key=lambda c: -c["caja"])[:CANDIDATOS]
    todos = mejoras + financian

    mejor, clave = [], None
    for n in range(1, MAXIMO_POR_VUELTA + 1):
        for combo in combinations(todos, n):
            if not deficit and not any(c["puntos"] >= GANANCIA_MINIMA for c in combo):
                continue
            entran = {c["entra"] for c in combo}
            salen = {c["sale"] for c in combo}
            if len(entran) < n or len(salen) < n:
                continue
            puntos = sum(c["puntos"] for c in combo)
            if not deficit and puntos < GANANCIA_MINIMA:
                continue
            if caja + sum(c["caja"] for c in combo) < minimo_de_caja:
                continue
            if sum(c["puja"] for c in combo) > disponible:
                continue
            k = (round(puntos, 6), caja + sum(c["caja"] for c in combo))
            if clave is None or k > clave:
                mejor, clave = list(combo), k
    return mejor


def decidir(
    *, once, liga, escaparate, foto, libro, inventario=frozenset(),
    pendientes=frozenset(), intocables=frozenset(), protegidos=frozenset(),
    ya_pujados=frozenset(), caja, horas_jornada, puede_escribir=True,
    en_curso=False,
) -> dict:
    """
    Qué hace la mejora del once en esta vuelta. Pura.

        once        [{id, name, position, starter_probability, price}]
        liga        {id: {tasa, status, price, de_quien, position}}
        escaparate  [{id, name, position, price, points, played,
                      starter_probability}] (Computer, hoy)
        foto        la de `leer_la_foto` (plantilla, nuestras_pujas,
                    ofertas_del_computer, en_venta, maximo_de_puja, saldo)
        libro       {"entra": {"sale", "suelo", ...}} de los cambios vivos
        inventario  lo que tienen la ronda y los chollos en la plantilla
        caja        la caja de la jornada sin estos cambios (ver `la_caja`)
        en_curso    hay jornada jugándose: no se vende a nadie (el once de
                    la jornada es el de su inicio, pero el que se vende
                    deja de puntuar para nosotros)
    """

    acciones, soltar, adoptar = [], [], []
    plantilla = foto.get("plantilla") or set()
    ofertas = foto.get("ofertas_del_computer") or {}
    en_venta = foto.get("en_venta") or set()
    saldo = _int(foto.get("saldo"), 0) or 0

    # 5. SALIDA de los cambios vivos.
    saliendo = set()
    for k, c in (libro or {}).items():
        entra, sale = _int(k), _int(c.get("sale"))
        if sale not in plantilla:
            soltar.append(k)                         # ya vendido
            continue
        if entra not in plantilla:
            if entra not in (foto.get("nuestras_pujas") or {}):
                soltar.append(k)                     # puja perdida: se queda
            else:
                saliendo.add(sale)
            continue
        saliendo.add(sale)
        if en_curso:
            continue
        suelo = _int(c.get("suelo"), 0) or 0
        if horas_jornada is not None and horas_jornada < HORAS_SOLVENCIA and saldo < 0:
            suelo = 0
        oferta = ofertas.get(sale)
        if oferta and (_int(oferta.get("amount"), 0) or 0) >= suelo:
            acciones.append({
                "accion": "ACEPTAR_OFERTA_DEL_COMPUTER", "player_id": sale,
                "offer_id": _int(oferta.get("offer_id")),
                "importe": _int(oferta.get("amount")), "suelo": suelo,
                "relevo": entra, "mejora": True,
            })
        elif sale not in en_venta and _int((liga.get(sale) or {}).get("price")):
            acciones.append({
                "accion": "PONER_A_LA_VENTA", "player_id": sale,
                "precio": _int((liga.get(sale) or {}).get("price")),
                "relevo": entra, "mejora": True,
            })

    plan = {"caja": caja, "cambios": []}
    if not puede_escribir or horas_jornada is None or horas_jornada < HORAS_SIN_COMPRAR:
        return {"acciones": acciones, "soltar": soltar, "adoptar": adoptar, "plan": plan}

    # 2. Quién puede salir: titulares, ni intocables ni protegidos, ni
    # los que ya salen o la orden vende.
    vivos = {_int(k) for k in (libro or {})}
    nuestros = []
    for p in once:
        pid = _int(p.get("id"))
        if (str(p.get("name") or "").strip().lower() in intocables or pid in protegidos
                or pid in saliendo or pid in pendientes or pid in vivos or pid in inventario):
            continue
        e = esperado((liga.get(pid) or {}).get("tasa"), p.get("starter_probability"))
        if e is None:
            continue
        valor = _int(p.get("price")) or _int((liga.get(pid) or {}).get("price"), 0) or 0
        nuestros.append({"id": pid, "nombre": p.get("name"), "pos": p.get("position"),
                         "esperado": e, "valor": valor})

    # Quién puede entrar: el Computer de hoy, y lo que ya tienen la ronda
    # y los chollos (sin pujar: ya es nuestro).
    entran = []
    for c in escaparate or []:
        pid = _int(c.get("id"))
        lc = liga.get(pid) or {}
        if (pid in plantilla or pid in pendientes or pid in ya_pujados
                or pid in (foto.get("nuestras_pujas") or {})
                or lc.get("de_quien") not in (None, "computer")
                or str(lc.get("status") or "ok").lower() != "ok"
                or (_int(c.get("played"), 0) or 0) < PARTIDOS_MINIMOS):
            continue
        prob = c.get("starter_probability")
        if prob is None or prob < TITULARIDAD_MINIMA:
            continue
        tasa = lc.get("tasa") or ((c.get("points") or 0) / c["played"])
        e = esperado(tasa, prob)
        # Lo que PIDE el Computer (E12: el precio del día en que salió).
        precio = _int((foto.get("mercado") or {}).get(pid)) or _int(c.get("price"), 0) or 0
        if foto.get("mercado") and pid not in foto["mercado"]:
            continue
        if e is None or not precio:
            continue
        entran.append({"id": pid, "nombre": c.get("name"), "pos": c.get("position"),
                       "esperado": e, "puja": la_puja(precio), "coste": la_puja(precio),
                       "ya_es_nuestro": False})
    prob_once = {_int(p.get("id")): p.get("starter_probability") for p in once}
    for pid in inventario:
        lc = liga.get(pid) or {}
        if pid not in plantilla or str(lc.get("status") or "ok").lower() != "ok":
            continue
        e = esperado(lc.get("tasa"), prob_once.get(pid) or lc.get("starter_probability"))
        valor = _int(lc.get("price"), 0) or 0
        if e is None or not valor:
            continue
        # Quedárselo cuesta lo que ya no da su reventa.
        entran.append({"id": pid, "nombre": lc.get("name"), "pos": lc.get("position"),
                       "esperado": e, "puja": 0, "coste": int(valor * VENTA),
                       "ya_es_nuestro": True})

    cambios = []
    for e in entran:
        for o in nuestros:
            if o["pos"] != e["pos"]:
                continue
            cambios.append({
                "entra": e["id"], "entra_nombre": e["nombre"], "sale": o["id"],
                "sale_nombre": o["nombre"], "puntos": round(e["esperado"] - o["esperado"], 2),
                "caja": int(o["valor"] * VENTA) - e["coste"], "puja": e["puja"],
                "suelo": int(o["valor"] * SUELO), "ya_es_nuestro": e["ya_es_nuestro"],
            })

    minimo = -DEUDA_TOLERADA if horas_jornada >= HORAS_CON_DEUDA else 0
    disponible = (_int(foto.get("maximo_de_puja"), 0) or 0) - RESERVA
    # En rojo, cambiar caro por barato solo a partir de `HORAS_DEFICIT`:
    # antes puede entrar el premio de la jornada que acaba de jugarse.
    deficit = caja < minimo and horas_jornada < HORAS_DEFICIT
    elegidos = la_mejor_combinacion(cambios, caja, minimo, disponible, deficit=deficit)
    plan = {"caja": caja, "minimo": minimo, "disponible": disponible, "deficit": deficit,
            "cambios": elegidos,
            "caja_despues": caja + sum(c["caja"] for c in elegidos)}

    for c in elegidos:
        if c["ya_es_nuestro"]:
            adoptar.append(c)
        else:
            acciones.append({
                "accion": "PUJAR", "player_id": c["entra"], "importe": c["puja"],
                "sustituye": None, "sale": c["sale"], "suelo": c["suelo"],
                "puntos": c["puntos"], "mejora": True,
            })

    return {"acciones": acciones, "soltar": soltar, "adoptar": adoptar, "plan": plan}


def jornada_en_curso(ahora: datetime, ruta=None) -> bool:
    """
    Entre el primer partido de una jornada y 3 h después del último. Los
    aplazados (más de 5 días después del primero) no alargan la jornada:
    el de la J6 Levante-Athletic se juega el 21/10.
    """
    try:
        from datetime import timedelta

        from src.actions.los_chollos import CALENDARIO

        d = json.loads(Path(ruta or CALENDARIO).read_text())
        for j in d.get("matchdays") or []:
            ko = sorted(datetime.fromisoformat(m["kickoff"]) for m in j.get("matches") or []
                        if m.get("kickoff"))
            if not ko:
                continue
            ko = [k for k in ko if k <= ko[0] + timedelta(days=5)]
            if ko[0] <= ahora <= ko[-1] + timedelta(hours=3):
                return True
        return False
    except Exception:                               # noqa: BLE001
        return True                                 # sin saberlo, no se vende


def la_caja(foto: dict, *, se_venden_solos=frozenset(), inventario_valor=0,
            ventas_pendientes=0) -> int:
    """
    La caja con la que se llega a la jornada si nada más cambia: saldo -
    pujas vivas (salvo las que se revenden solas: ronda y chollos, que
    cuentan a -7 %) + lo que darán el inventario de la ronda y las ventas
    pendientes (ya al 95 %).
    """

    saldo = _int(foto.get("saldo"), 0) or 0
    pujas = 0
    for pid, p in (foto.get("nuestras_pujas") or {}).items():
        importe = _int(p.get("amount"), 0) or 0
        pujas += int(importe * 0.07) if pid in se_venden_solos else importe
    return saldo - pujas + int(inventario_valor) + int(ventas_pendientes)


# ============================================================
# EL PASO DEL WORKFLOW
# ============================================================

def _leer(ruta, defecto):
    try:
        return json.loads(Path(ruta).read_text(encoding="utf-8"))
    except Exception:                               # noqa: BLE001
        return defecto


def _la_ultima_foto():
    fotos = sorted((RAIZ / "data").glob("snapshot_*.json"))
    return _leer(fotos[-1], {}) if fotos else {}


def correr(status=None, snapshot=None, v10=None, escritor_factory=None,
           ahora: datetime | None = None, libro_ruta=None) -> dict:
    """La mejora del once, en esta vuelta. Nunca lanza."""

    salida = {"activa": activa(), "motivo": None, "acciones": [], "hechas": [],
              "adoptados": [], "plan": None}

    try:
        if not salida["activa"]:
            salida["motivo"] = "APAGADA"
            return salida

        from src.actions.la_orden_del_gestor import (
            _intocables, _pid, ejecutar, leer_la_foto, leer_la_orden, protegidos,
        )
        from src.actions.los_chollos import (
            LIBRO as LIBRO_CHOLLOS, _puede_escribir, horas_a_la_jornada,
        )
        from src.actions.la_ronda_de_la_manana import LIBRO as LIBRO_RONDA

        ahora = ahora or datetime.now(timezone.utc)
        status = status if status is not None else _leer(STATUS, {})
        snapshot = snapshot if snapshot is not None else _la_ultima_foto()
        v10 = v10 if v10 is not None else _leer(V10, {})

        yo = _pid((snapshot.get("league") or {}).get("user"))
        foto = leer_la_foto(snapshot, yo)

        # Lo que esta misma vuelta ya pujó (la foto es de antes).
        ya_pujados, gastado = set(), 0
        for bloque in ("orden_del_gestor", "chollos", "ronda"):
            for h in (v10.get(bloque) or {}).get("hechas") or []:
                if h.get("accion") == "PUJAR" and h.get("exito"):
                    ya_pujados.add(_int(h.get("player_id")))
                    gastado += _int(h.get("importe"), 0) or 0
        foto["maximo_de_puja"] = (_int(foto.get("maximo_de_puja"), 0) or 0) - gastado

        liga = {}
        for p in (status.get("todaLaLiga") or {}).get("players") or []:
            if _int(p.get("id")) is not None:
                liga[_int(p["id"])] = p
        once = (status.get("lineup") or {}).get("players") or []
        escaparate = (status.get("libro_del_escaparate") or {}).get("players") or []

        orden = leer_la_orden() or {}
        pendientes = {_int(f.get("player_id")) for f in orden.get("fichar") or []}
        venta = (orden.get("vender_si_ficha") or {}).get("jugadores") or []
        pendientes |= {_int(j.get("player_id")) for j in venta}

        libro_ronda = _leer(LIBRO_RONDA, {})
        libro_chollos = _leer(LIBRO_CHOLLOS, {})
        solos = {_int(k) for k in list(libro_ronda) + list(libro_chollos)}
        inventario = {p for p in solos if p in foto["plantilla"]}

        libro = _leer(libro_ruta or LIBRO, {})
        saliendo_valor = sum(
            _int((liga.get(_int(c.get("sale"))) or {}).get("price"), 0) or 0
            for c in libro.values()
        )
        caja = la_caja(
            foto, se_venden_solos=solos,
            inventario_valor=int(sum(_int((liga.get(p) or {}).get("price"), 0) or 0
                                     for p in inventario) * VENTA),
            ventas_pendientes=int((sum(int((_int(j.get("suelo"), 0) or 0) / SUELO) for j in venta)
                                   + saliendo_valor) * VENTA)
            - sum(_int(f.get("puja"), 0) or 0 for f in orden.get("fichar") or []
                  if _int(f.get("player_id")) not in (foto.get("nuestras_pujas") or {})
                  and _int(f.get("player_id")) not in foto["plantilla"]),
        )

        d = decidir(
            once=once, liga=liga, escaparate=escaparate, foto=foto, libro=libro,
            inventario=inventario, pendientes=pendientes,
            intocables=_intocables(orden), protegidos=protegidos(),
            ya_pujados=ya_pujados, caja=caja,
            horas_jornada=horas_a_la_jornada(ahora),
            puede_escribir=_puede_escribir(ahora),
            en_curso=jornada_en_curso(ahora),
        )
        salida["acciones"], salida["plan"] = d["acciones"], d["plan"]

        for k in d["soltar"]:
            libro.pop(k, None)
        for c in d["adoptar"]:
            libro[str(c["entra"])] = {"sale": c["sale"], "suelo": c["suelo"],
                                      "puntos": c["puntos"], "adoptado": True}
            libro_ronda.pop(str(c["entra"]), None)
            libro_chollos.pop(str(c["entra"]), None)
            salida["adoptados"].append(c)
        if d["adoptar"]:
            for ruta, datos in ((LIBRO_RONDA, libro_ronda), (LIBRO_CHOLLOS, libro_chollos)):
                try:
                    Path(ruta).write_text(json.dumps(datos, indent=2) + "\n")
                except Exception:                   # noqa: BLE001
                    pass

        if d["acciones"]:
            if escritor_factory is None:
                from src.biwenger.write_client import BiwengerWriteClient

                escritor_factory = BiwengerWriteClient
            hechas = ejecutar(d["acciones"], escritor_factory())
            salida["hechas"] = hechas
            for h in hechas:
                if h.get("accion") == "PUJAR" and h.get("exito"):
                    libro[str(h["player_id"])] = {
                        "sale": h.get("sale"), "suelo": h.get("suelo"),
                        "puja": h.get("importe"), "puntos": h.get("puntos"),
                    }

        try:
            ruta = Path(libro_ruta or LIBRO)
            ruta.parent.mkdir(parents=True, exist_ok=True)
            ruta.write_text(json.dumps(libro, indent=2) + "\n")
        except Exception:                           # noqa: BLE001
            pass

        salida["motivo"] = "EJECUTADA" if (d["acciones"] or d["adoptar"]) else "NADA_QUE_HACER"

    except Exception as error:                      # noqa: BLE001
        salida["motivo"] = f"ERROR: {type(error).__name__}: {error}"

    return salida


def main() -> int:
    r = correr()
    plan = r.get("plan") or {}
    print("=" * 100)
    print("LA MEJORA DEL ONCE")
    print("=" * 100)
    print(f"  {r.get('motivo')}  caja de la jornada {plan.get('caja')}  "
          f"minimo {plan.get('minimo')}  puja disponible {plan.get('disponible')}")
    for c in plan.get("cambios") or []:
        print(f"  {c['entra_nombre']} por {c['sale_nombre']}: {c['puntos']:+} pts por jornada, "
              f"caja {c['caja']:+,}{' (ya es nuestro)' if c['ya_es_nuestro'] else ''}")
    for a in r.get("acciones") or []:
        print(f"  -> {a.get('accion')} {a.get('player_id')} {a.get('importe') or a.get('precio')}")
    for h in r.get("hechas") or []:
        print(f"  hecha {h.get('accion')} {h.get('player_id')} exito={h.get('exito')} "
              f"http={h.get('http_status')} {h.get('error') or ''}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
