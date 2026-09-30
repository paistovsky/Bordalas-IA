"""
EL COMPARADOR DE CAMBIOS (30/09/2026)

POR QUE EXISTE

    Pepe sabe decir si un jugador «vale lo que cuesta», pero no lo que
    hay que dar a cambio. La pregunta del dueño: «¿vender a X para
    fichar a Y nos da más puntos? ¿y cómo queda la caja?». Hasta hoy
    la contestaba el gestor a mano cada mañana (Akhomach contra
    Jutglà). Esto la contesta para todo el mercado del Computer.

QUE HACE

    Por cada jugador del Computer que juega (puntos por partido con al
    menos `MIN_PARTIDOS` jugados, sano) y por cada uno nuestro de su
    misma posición que se puede vender (ni Yamal ni los protegidos de
    la orden):

        puntos = su tasa por partido - la del nuestro
        caja   = lo que vale el nuestro - lo que cuesta el suyo

    La venta se cuenta a precio de mercado: el Computer paga más o
    menos eso (censo de ofertas). Se queda con los que suben puntos, y
    con los que dan caja perdiendo como mucho `TOLERANCIA` por partido
    (el «caro por un titular barato» que pidió el dueño para salir del
    rojo). Por cada fichaje, el mejor cambio; ordenados: primero los
    que suben puntos Y dan caja, luego por puntos, luego por caja.

QUE NO HACE

    No escribe nada: es para mirar (panel El Plan) y para que el gestor
    lo convierta en orden. Función pura: ni red ni disco. Nunca lanza.
"""

from __future__ import annotations


MIN_PARTIDOS = 3
TOLERANCIA = 0.5          # puntos por partido que se aceptan perder por caja
CUANTOS = 8
MALOS = frozenset({"injured", "sanctioned"})
INTOCABLES = frozenset({"yamal", "lamine yamal"})


def _num(x):
    try:
        if x is None or isinstance(x, bool):
            return None
        return float(x)
    except (TypeError, ValueError):
        return None


def _tasa(f: dict):
    t = _num(f.get("tasa"))
    if t is not None:
        return t
    jugados = _num(f.get("played")) or 0
    puntos = _num(f.get("points"))
    if jugados <= 0 or puntos is None:
        return None
    return puntos / jugados


def comparar(filas, saldo=None, protegidos=None) -> dict:
    """
    `filas`: las de `todaLaLiga.players`. `saldo`: el nuestro ahora.
    `protegidos`: ids que no se venden. Devuelve
    `{"ok", "saldo", "cambios": [...], "n"}`.
    """

    salida = {"ok": False, "saldo": saldo, "cambios": [], "n": 0}

    try:
        protegidos = {int(p) for p in (protegidos or set()) if p is not None}
        nuestros, suyos = [], []

        for f in filas or []:
            if not isinstance(f, dict):
                continue
            quien = f.get("de_quien")
            if quien == "nuestro":
                nombre = str(f.get("name") or "").strip().lower()
                if nombre in INTOCABLES or f.get("id") in protegidos:
                    continue
                nuestros.append(f)
            elif quien == "computer":
                if str(f.get("status") or "").lower() in MALOS:
                    continue
                if (_num(f.get("played")) or 0) < MIN_PARTIDOS:
                    continue
                suyos.append(f)

        cambios = []
        for c in suyos:
            tc, pc = _tasa(c), _num(c.get("price"))
            if tc is None or not pc:
                continue
            mejor = None
            for o in nuestros:
                if o.get("position") != c.get("position"):
                    continue
                to, po = _tasa(o), _num(o.get("price"))
                if to is None or po is None:
                    continue
                puntos = round(tc - to, 2)
                caja = int(po - pc)
                if puntos <= 0 and not (caja > 0 and puntos >= -TOLERANCIA):
                    continue
                fila = {
                    "ficha": c.get("name"), "ficha_id": c.get("id"),
                    "ficha_precio": int(pc), "ficha_tasa": round(tc, 2),
                    "ficha_sube": c.get("price_increment"),
                    "vende": o.get("name"), "vende_id": o.get("id"),
                    "vende_precio": int(po), "vende_tasa": round(to, 2),
                    "posicion": c.get("position"),
                    "puntos": puntos, "caja": caja,
                    "gana_las_dos": puntos > 0 and caja > 0,
                    "saca_del_rojo": (
                        saldo is not None and saldo < 0 and saldo + caja >= 0
                    ),
                }
                clave = (fila["gana_las_dos"], puntos, caja)
                if mejor is None or clave > mejor[0]:
                    mejor = (clave, fila)
            if mejor:
                cambios.append(mejor[1])

        cambios.sort(key=lambda f: (not f["gana_las_dos"], -f["puntos"], -f["caja"]))
        salida.update(ok=True, cambios=cambios[:CUANTOS], n=len(cambios))

    except Exception as error:                      # noqa: BLE001
        salida["error"] = f"{type(error).__name__}: {error}"

    return salida
