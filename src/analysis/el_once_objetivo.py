"""
El once objetivo: primero a donde vas, despues cuanto te cuesta.

POR QUE EXISTE (26/09/2026)

    Hoy Pepe va candidato a candidato preguntando "¿este mejora mi
    once?". El dueño lo quiere al reves:

        1  el ONCE OBJETIVO, sin mirar el dinero
        2  la DISTANCIA entre lo que tienes y ese once
        3  de ahi, compras y ventas, ya con el dinero delante

    Y son dos onces: el de la TEMPORADA decide a quien tienes (la
    titularidad es una tasa) y el de la JORNADA a quien alineas (la
    titularidad ya casi es un hecho).

LO QUE HAY AQUI

    Funciones puras para MEDIR y DISEÑAR. Nadie las llama para
    decidir. Ni disco, ni red, ni reloj, ni entorno. Nunca lanzan.

        desviacion_por_contexto   el efecto del calendario, medido
                                  como desviacion sobre la PROPIA
                                  media, no en puntos brutos
        estimar_k                 cuanto encoger, sacado de los datos
        encoger                   la media hacia la de su posicion
        el_mejor_once             once de 11 entre las siete
                                  formaciones de `lineup_engine`
        el_plan                   la secuencia de compras y ventas
                                  hacia el objetivo, con caja y fichas

POR QUE LA DESVIACION Y NO LOS PUNTOS

    Si se miden puntos brutos, "en casa se puntua mas" puede ser
    solo que los buenos juegan mas en casa, o que los buenos estan
    en equipos que ganan. Restando a cada partido la media de su
    propio jugador, lo que queda es lo que el CONTEXTO añade a ese
    jugador. Doctrina 95: un numero que encaja no es una causa.
"""

from __future__ import annotations

import math

from src.analysis.lineup_engine import FORMATIONS


def safe_float(value, default=None):
    try:
        out = float(value)
    except (TypeError, ValueError):
        return default
    return out if math.isfinite(out) else default


# ============================================================
# EL CALENDARIO, EN DESVIACION
# ============================================================

def _media_y_error(valores: list) -> dict:
    n = len(valores)
    if n == 0:
        return {"n": 0, "media": None, "ic95": None}
    media = sum(valores) / n
    if n < 2:
        return {"n": n, "media": round(media, 3), "ic95": None}
    var = sum((v - media) ** 2 for v in valores) / (n - 1)
    return {
        "n": n,
        "media": round(media, 3),
        "ic95": round(1.96 * math.sqrt(var / n), 3),
    }


def desviacion_por_contexto(partidos, medias=None) -> dict:
    """
    El efecto de cada contexto, en desviacion sobre la media propia.

    `partidos`: `[{jugador, posicion, puntos, casa, rival_alto}]`,
    uno por partido JUGADO. `medias`: `{jugador: media de la
    temporada}`; sin ella, la media de sus partidos de aqui.

    Devuelve, por posicion y en "todas": la desviacion media en
    casa, fuera, contra la mitad alta, contra la baja, y en casa
    contra la baja, cada una con su `n` y su intervalo del 95 %. Y,
    para comparar, lo mismo en puntos BRUTOS, que es lo que NO hay
    que usar. Nunca lanza.
    """

    try:
        filas = [
            p for p in (partidos or [])
            if isinstance(p, dict) and safe_float(p.get("puntos")) is not None
        ]

        propias = dict(medias or {})
        sumas: dict = {}
        for p in filas:
            s = sumas.setdefault(p.get("jugador"), [0.0, 0])
            s[0] += float(p["puntos"])
            s[1] += 1
        for jugador, (total, n) in sumas.items():
            if safe_float(propias.get(jugador)) is None:
                propias[jugador] = total / n

        contextos = {
            "casa": lambda p: p.get("casa") is True,
            "fuera": lambda p: p.get("casa") is False,
            "rival_alto": lambda p: p.get("rival_alto") is True,
            "rival_bajo": lambda p: p.get("rival_alto") is False,
            "casa_y_rival_bajo": lambda p: p.get("casa") is True
            and p.get("rival_alto") is False,
        }

        def cuadro(sub):
            out = {}
            for nombre, cumple in contextos.items():
                elegidos = [p for p in sub if cumple(p)]
                out[nombre] = {
                    "desviacion": _media_y_error(
                        [
                            float(p["puntos"]) - float(propias[p.get("jugador")])
                            for p in elegidos
                        ]
                    ),
                    "bruto": _media_y_error([float(p["puntos"]) for p in elegidos]),
                    "jugadores": len({p.get("jugador") for p in elegidos}),
                }
            return out

        resultado = {"todas": cuadro(filas)}
        for posicion in sorted({p.get("posicion") for p in filas}, key=str):
            resultado[str(posicion)] = cuadro(
                [p for p in filas if p.get("posicion") == posicion]
            )
        return resultado

    except Exception as error:                      # noqa: BLE001
        return {"error": f"{type(error).__name__}: {error}"}


# ============================================================
# CUANTO ENCOGER
# ============================================================

def estimar_k(jugadores, varianza_dentro) -> float | None:
    """
    El `k` del encogimiento, de los datos y no a ojo.

    `jugadores`: `[{ppg, jugados}]` de UNA posicion.
    `varianza_dentro`: la varianza de los puntos de un partido
    alrededor de la media de su jugador (de los partidos uno a uno).

        varianza entre = var(ppg observada) - media(var_dentro / jugados)
        k              = var_dentro / varianza entre

    Es el metodo de los momentos de un modelo normal-normal: con
    `k` partidos de "prior", la media observada y la de la posicion
    pesan lo que dice su ruido. None si no se puede estimar (la
    varianza entre sale <= 0 o faltan datos). Nunca lanza.
    """

    try:
        filas = [
            j for j in (jugadores or [])
            if safe_float(j.get("ppg")) is not None and (j.get("jugados") or 0) > 0
        ]
        w = safe_float(varianza_dentro)
        if len(filas) < 5 or w is None or w <= 0:
            return None
        media = sum(float(j["ppg"]) for j in filas) / len(filas)
        var_obs = sum((float(j["ppg"]) - media) ** 2 for j in filas) / (len(filas) - 1)
        ruido = sum(w / float(j["jugados"]) for j in filas) / len(filas)
        entre = var_obs - ruido
        if entre <= 0:
            return None
        return round(w / entre, 3)
    except Exception:                               # noqa: BLE001
        return None


def encoger(puntos, jugados, media_posicion, k) -> float:
    """(puntos + k * media) / (jugados + k). Sin partidos, la media."""

    try:
        n = max(float(jugados or 0), 0.0)
        k = max(float(k or 0), 0.0)
        if n + k <= 0:
            return float(media_posicion or 0.0)
        return (float(puntos or 0) + k * float(media_posicion or 0.0)) / (n + k)
    except Exception:                               # noqa: BLE001
        return 0.0


# ============================================================
# EL MEJOR ONCE
# ============================================================

def el_mejor_once(jugadores, valor: str = "valor") -> dict:
    """
    El mejor once por `valor` entre las siete formaciones de
    `lineup_engine` (1 portero, 3-5 defensas, 3-5 medios, 1-3
    delanteros: son exactamente esas siete).

    Con una sola posicion por jugador el optimo de cada formacion
    es coger los N mejores de cada puesto: es exacto, no una
    aproximacion. Empate de formaciones: la de menos coste, y
    despues el nombre (doctrina 110: el desempate tambien elige).

    `jugadores`: `[{id, posicion, <valor>, precio?}]`. Nunca lanza.
    """

    try:
        por_puesto: dict = {1: [], 2: [], 3: [], 4: []}
        for j in jugadores or []:
            pos = int(j.get("posicion") or 0)
            if pos in por_puesto and safe_float(j.get(valor)) is not None:
                por_puesto[pos].append(j)
        for pos in por_puesto:
            por_puesto[pos].sort(
                key=lambda j: (
                    -float(j[valor]),
                    int(j.get("precio") or 0),
                    str(j.get("id")),
                )
            )

        mejor = None
        for nombre, forma in FORMATIONS.items():
            elegidos = []
            for pos, cuantos in forma.items():
                elegidos.extend(por_puesto[pos][:cuantos])
            if len(elegidos) < 11:
                continue
            suma = sum(float(j[valor]) for j in elegidos)
            coste = sum(int(j.get("precio") or 0) for j in elegidos)
            clave = (round(suma, 6), -coste, nombre)
            if mejor is None or clave > mejor[0]:
                mejor = (clave, nombre, elegidos, suma, coste)

        if mejor is None:
            return {"lleno": False, "formacion": None, "ids": [], "suma": 0.0, "coste": 0}

        _, nombre, elegidos, suma, coste = mejor
        return {
            "lleno": True,
            "formacion": nombre,
            "ids": [j.get("id") for j in elegidos],
            "suma": round(suma, 3),
            "coste": coste,
        }
    except Exception as error:                      # noqa: BLE001
        return {"lleno": False, "formacion": None, "ids": [], "suma": 0.0,
                "coste": 0, "reason": f"{type(error).__name__}: {error}"}


# ============================================================
# EL PLAN
# ============================================================

def el_plan(
    plantilla,
    comprables,
    ofertas,
    caja: int,
    fichas: int,
    no_se_vende=(),
    valor: str = "valor",
    maximo_pasos: int = 20,
) -> dict:
    """
    La secuencia mas barata de compras y ventas que acerca el once.

    `plantilla`: lo que tienes, `[{id, posicion, valor, precio}]`.
    `comprables`: lo que se puede comprar HOY, con su `precio`.
    `ofertas`: `{id: {importe, coste}}` de nuestros jugadores con
    oferta en firme; `coste` es lo que nos costo (None si no se
    sabe). `no_se_vende`: ids que no se venden nunca (Yamal).

    En cada paso se elige, de todo lo que sube el once, lo que mas
    sube por euro neto:

        COMPRAR x          si cabe en la caja y hay ficha libre
        VENDER y, COMPRAR x  si no hay ficha: dos escrituras

    Solo se vende con oferta en firme, sin perdida (importe >= coste,
    y con coste desconocido no se vende) y fuera del once que queda.
    El importe de una venta vuelve a la caja entero: es un SUPUESTO,
    se dice en el informe. Cada compra y cada venta es una escritura,
    y va una por ciclo: el plan cuenta escrituras.

    Nunca lanza.
    """

    try:
        tengo = {j["id"]: dict(j) for j in plantilla or []}
        mercado = {j["id"]: dict(j) for j in comprables or [] if j["id"] not in tengo}
        ofertas = dict(ofertas or {})
        bloqueados = set(no_se_vende or ())
        caja = int(caja or 0)
        fichas = int(fichas or 0)

        def once(ids):
            return el_mejor_once([tengo_o_mercado[i] for i in ids], valor)

        tengo_o_mercado = {**tengo, **mercado}
        actual = once(list(tengo))
        pasos = []
        escrituras = 0

        def vendible(i, once_tras):
            o = ofertas.get(i)
            if not o or i in bloqueados or i in once_tras:
                return False
            coste = o.get("coste")
            return coste is not None and int(o.get("importe") or 0) >= int(coste)

        for _ in range(int(maximo_pasos)):
            mejor = None
            for x, jx in mercado.items():
                precio = int(jx.get("precio") or 0)

                if fichas > 0 and precio <= caja:
                    nuevo = once(list(tengo) + [x])
                    gana = nuevo["suma"] - actual["suma"]
                    if gana > 1e-9:
                        clave = gana / max(precio, 1)
                        if mejor is None or clave > mejor[0]:
                            mejor = (clave, "COMPRAR", x, None, nuevo, gana, precio, precio)

                for y in list(tengo):
                    if y not in ofertas:
                        continue
                    importe = int(ofertas[y].get("importe") or 0)
                    if precio > caja + importe:
                        continue
                    ids = [i for i in tengo if i != y] + [x]
                    nuevo = once(ids)
                    if not vendible(y, set(nuevo["ids"])):
                        continue
                    gana = nuevo["suma"] - actual["suma"]
                    if gana <= 1e-9:
                        continue
                    neto = precio - importe
                    clave = gana / max(neto, 1) if neto > 0 else float("inf")
                    if mejor is None or clave > mejor[0]:
                        mejor = (clave, "VENDER_Y_COMPRAR", x, y, nuevo, gana, precio, neto)

            if mejor is None:
                break

            _, tipo, x, y, nuevo, gana, precio, neto = mejor
            if y is not None:
                caja += int(ofertas[y].get("importe") or 0)
                del tengo[y]
                fichas += 1
                escrituras += 1
            caja -= precio
            tengo[x] = mercado.pop(x)
            fichas -= 1
            escrituras += 1
            pasos.append(
                {
                    "tipo": tipo,
                    "compra": x,
                    "vende": y,
                    "precio": precio,
                    "neto": neto,
                    "gana": round(gana, 3),
                    "gana_por_millon": round(gana / (neto / 1e6), 3) if neto > 0 else None,
                    "caja_despues": caja,
                    "fichas_despues": fichas,
                    "once_despues": nuevo["suma"],
                    "formacion": nuevo["formacion"],
                }
            )
            actual = nuevo

        return {
            "pasos": pasos,
            "escrituras": escrituras,
            "once_final": actual,
            "caja_final": caja,
            "fichas_finales": fichas,
        }
    except Exception as error:                      # noqa: BLE001
        return {"pasos": [], "escrituras": 0, "once_final": None,
                "reason": f"{type(error).__name__}: {error}"}
