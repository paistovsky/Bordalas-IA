"""
El escaparate: cada cuanto sale el bueno, y si estabamos alli.

LA TESIS QUE SE MIDE

    "20 jugadores al dia de 570. Mejorar el once no es elegir
     bien: es estar listo el dia que sale el bueno."

    Se mide, y sale VERDADERA, pero no por donde el encargo
    creia. No fallamos esperando al jugador: fallamos
    apareciendo.

DOCTRINA 72 — LIBRE NO ES COMPRABLE. MANDA EL ESCAPARATE.

NO HAY HISTORICO DE ESCAPARATES, Y HAY QUE DECIRLO

    `censo_del_reset` -lo que hacia pensar que si- es el censo de
    las OFERTAS QUE RECIBIMOS por nuestros jugadores
    (`data/solvency/censo_de_ofertas.jsonl`, 2 lineas, 15 y
    16/09). No tiene nada que ver con los 20 del escaparate.

    `data/trading/libro_de_escaparate.jsonl` lo nombra
    `escaparate_executor` y NO EXISTE en disco; ademas ese
    "escaparate" es el NUESTRO -publicar para vender-, no el del
    Computer.

    Lo unico que hay es indirecto: los 95 ficheros
    `data/snapshot_*.json` llevan `market.sales` dentro. De ahi
    salen NUEVE dias de mercado, mas el de la foto del 17/09:
    diez en total, y con un agujero del 18/08 al 09/09.

    Diez dias no son una serie. Todo lo que sale de aqui lleva
    ese `n` delante.

EL DIA DE MERCADO NO ES EL DIA NATURAL

    El escaparate se renueva en el reset, a las 05:00 UTC. Una
    foto de las 23:00 y otra de las 06:00 del dia siguiente son
    escaparates DISTINTOS; dos del mismo dia natural a un lado y
    otro del reset, tambien.

    Agrupando por dia natural salian dias con 29 y 34 jugadores
    -imposible, son 20-. Agrupando por dia de mercado salen 20
    exactos los diez dias. Esa es la comprobacion de que el corte
    esta bien puesto.

FASE OBSERVADOR

    `ENCENDIDO = False`. Esto cuenta. No compra, no vende y no
    propone comprar ni vender a nadie.
"""

from __future__ import annotations

import datetime
import random
import statistics


ENCENDIDO = False


# El escaparate se renueva a esta hora UTC. Medido: agrupando
# por aqui salen 20 exactos todos los dias, y por dia natural no.
HORA_DEL_RESET = 5


# Cuantos jugadores saca el Computer cada dia. No es una
# constante de la casa: es lo que se cuenta, y se comprueba.
PLAZAS_POR_DIA = 20


def safe_int(value, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def esta_encendido() -> bool:
    return bool(ENCENDIDO)


def _miles(valor) -> str:
    return f"{safe_int(valor):,}".replace(",", ".")


# ============================================================
# BLOQUE 0 — EL DIA DE MERCADO
# ============================================================


def dia_de_mercado(momento, hora_del_reset: int = HORA_DEL_RESET):
    """
    A que escaparate pertenece un instante.

    Nunca mira el reloj del sistema: el instante entra por
    argumento, como texto ISO o como `datetime`.
    """

    if isinstance(momento, str):
        texto = momento.replace("Z", "+00:00")

        instante = datetime.datetime.fromisoformat(texto)

    else:
        instante = momento

    if instante.tzinfo is not None:
        instante = instante.replace(tzinfo=None)

    return (
        instante - datetime.timedelta(hours=int(hora_del_reset))
    ).date()


# ============================================================
# BLOQUE 1 — COMO ROTA
# ============================================================


def rotacion(por_dia: dict | None) -> dict:
    """
    Cuantos distintos han pasado, cuantos se repiten y cuantos
    son nuevos de un dia para otro.

    `por_dia` es {dia_de_mercado: {ids}}. Nunca lanza.

    CON EL HISTORICO VACIO NO DEVUELVE CEROS: devuelve que no hay
    historico. Un cero medido y un cero por no haber guardado
    nada no son el mismo numero, y esta es justo la medicion que
    tienta a reconstruirse desde una sola foto.
    """

    try:
        dias = {
            d: set(ids)
            for d, ids in (por_dia or {}).items()
            if ids
        }

        if not dias:
            return {
                "available": False,
                "dias": 0,
                "distintos": 0,
                "reason": (
                    "No hay historico de escaparates: no se puede "
                    "reconstruir una rotacion desde una foto sola."
                ),
            }

        orden = sorted(dias)

        todos = set().union(*dias.values())

        apariciones = {}

        for ids in dias.values():
            for pid in ids:
                apariciones[pid] = apariciones.get(pid, 0) + 1

        # Solo los pares de dias SEGUIDOS dicen algo de la
        # rotacion. Entre el 17/08 y el 10/09 no hay nada, y
        # restar esos dos escaparates seria inventarse 24 dias.
        pares = []

        for anterior, siguiente in zip(orden, orden[1:]):

            if (siguiente - anterior).days != 1:
                continue

            siguen = dias[anterior] & dias[siguiente]

            pares.append(
                {
                    "de": anterior.isoformat(),
                    "a": siguiente.isoformat(),
                    "siguen": len(siguen),
                    "nuevos": len(dias[siguiente] - dias[anterior]),
                    "de_cuantos": len(dias[siguiente]),
                }
            )

        nuevos = [p["nuevos"] for p in pares]

        plazas = sum(len(ids) for ids in dias.values())

        reparto = {}

        for veces in apariciones.values():
            reparto[veces] = reparto.get(veces, 0) + 1

        return {
            "available": True,
            "dias": len(dias),
            "primero": orden[0].isoformat(),
            "ultimo": orden[-1].isoformat(),
            "hay_agujeros": (orden[-1] - orden[0]).days + 1 > len(dias),

            "plazas": plazas,
            "distintos": len(todos),
            "reparto_de_apariciones": dict(sorted(reparto.items())),

            "pares_consecutivos": len(pares),
            "pares": pares,

            "nuevos_por_dia": (
                round(statistics.mean(nuevos), 2) if nuevos else None
            ),
            "nuevos_por_dia_percent": (
                round(
                    statistics.mean(nuevos)
                    / statistics.mean(
                        p["de_cuantos"] for p in pares
                    )
                    * 100,
                    1,
                )
                if pares
                else None
            ),

            "reason": (
                f"{len(dias)} dias de mercado ({orden[0]} a "
                f"{orden[-1]}), {plazas} plazas y {len(todos)} "
                f"jugadores distintos. "
                + (
                    f"En los {len(pares)} pares de dias SEGUIDOS "
                    f"medibles, entran "
                    f"{statistics.mean(nuevos):.1f} nuevos de "
                    f"{statistics.mean(p['de_cuantos'] for p in pares):.0f}."
                    if pares
                    else "No hay dos dias seguidos que comparar."
                )
            ),
        }

    except Exception as error:                      # noqa: BLE001
        return {
            "available": False,
            "dias": 0,
            "distintos": 0,
            "reason": (
                f"No se pudo medir la rotacion: "
                f"{type(error).__name__}: {error}"
            ),
        }


def espera_de_un_jugador(
    apariciones: int,
    jugadores: int,
    dias: int,
) -> dict:
    """
    Cuanto se tarda en ver salir a UNO concreto de una lista.

    `apariciones` son las veces que alguien de la lista salio;
    `jugadores` cuantos hay en la lista; `dias` cuantos dias de
    escaparate se miraron.

    La tasa es apariciones / (jugadores x dias): la probabilidad
    diaria de que un jugador CONCRETO de esa lista salga. La
    espera es su inversa.

    NO ES UNA PREDICCION. Supone que la tasa se mantiene, y esta
    medida sobre pocos dias. Sale con su `n` para que quien la
    lea sepa de que tamaño de muestra viene.
    """

    lista = max(safe_int(jugadores), 0)

    ventana = max(safe_int(dias), 0)

    oportunidades = lista * ventana

    if not oportunidades:
        return {
            "available": False,
            "reason": (
                "Sin jugadores o sin dias no hay tasa que calcular."
            ),
        }

    vistas = max(safe_int(apariciones), 0)

    if not vistas:
        return {
            "available": True,
            "apariciones": 0,
            "oportunidades": oportunidades,
            "tasa_diaria": 0.0,
            "espera_dias": None,
            "reason": (
                f"Ninguno de los {lista} salio en {ventana} dias "
                f"({oportunidades} oportunidades jugador-dia). Con "
                f"cero apariciones no se puede poner un plazo: solo "
                f"se puede decir que es mas largo que {ventana} "
                f"dias."
            ),
        }

    tasa = vistas / oportunidades

    return {
        "available": True,
        "apariciones": vistas,
        "oportunidades": oportunidades,
        "tasa_diaria": round(tasa, 6),
        "espera_dias": round(1 / tasa, 1),
        "reason": (
            f"{vistas} apariciones en {oportunidades} "
            f"oportunidades jugador-dia ({lista} jugadores x "
            f"{ventana} dias): {tasa * 100:.2f} % al dia por "
            f"jugador, o sea {1 / tasa:.0f} dias de espera para uno "
            f"concreto. Medido sobre {ventana} dias: es el orden de "
            f"magnitud, no un plazo."
        ),
    }


# ============================================================
# BLOQUE 2 — ¿HAY PATRON?
# ============================================================


def hay_patron(
    salieron: list | None,
    no_salieron: list | None,
    *,
    nombre: str = "el rasgo",
    vueltas: int = 10_000,
    semilla: int = 20260917,
) -> dict:
    """
    ¿Se parecen en algo los que salen?

    Compara las medianas de un rasgo numerico entre los que
    salieron y los que no, y baraja para ver cuantas veces sale
    un hueco igual o mayor por azar.

    NO DEMUESTRA ALEATORIEDAD. Un `p` alto con pocas muestras
    quiere decir "esta prueba no lo ve", no "no existe". Se
    publica el `n` para que se pueda juzgar la fuerza de la
    prueba, no solo su resultado.
    """

    try:
        a = [float(x) for x in (salieron or []) if x is not None]

        b = [float(x) for x in (no_salieron or []) if x is not None]

        if len(a) < 5 or len(b) < 5:
            return {
                "available": False,
                "n_salieron": len(a),
                "n_no": len(b),
                "reason": (
                    f"Muestra corta para {nombre}: {len(a)} contra "
                    f"{len(b)}. No se publica un `p` que no aguanta."
                ),
            }

        observado = abs(statistics.median(a) - statistics.median(b))

        azar = random.Random(semilla)

        bolsa = a + b

        corte = len(a)

        veces = 0

        for _ in range(vueltas):
            azar.shuffle(bolsa)

            if (
                abs(
                    statistics.median(bolsa[corte:])
                    - statistics.median(bolsa[:corte])
                )
                >= observado
            ):
                veces += 1

        p = veces / vueltas

        return {
            "available": True,
            "nombre": nombre,
            "n_salieron": len(a),
            "n_no": len(b),
            "mediana_salieron": statistics.median(a),
            "mediana_no": statistics.median(b),
            "hueco": observado,
            "p": round(p, 4),
            "hay_patron": p < 0.05,
            "reason": (
                f"{nombre}: mediana {statistics.median(a):,.0f} en "
                f"los que salieron (n={len(a)}) contra "
                f"{statistics.median(b):,.0f} en los que no "
                f"(n={len(b)}). p = {p:.4f}. "
                + (
                    "Hay diferencia."
                    if p < 0.05
                    else "Esta prueba no ve diferencia."
                )
            ).replace(",", "."),
        }

    except Exception as error:                      # noqa: BLE001
        return {
            "available": False,
            "reason": (
                f"No se pudo probar el patron: "
                f"{type(error).__name__}: {error}"
            ),
        }


# ============================================================
# BLOQUE 3 — ¿ESTABAMOS LISTOS?
# ============================================================


def estabamos_listos(
    subastas: list | None,
    nuestro_id,
) -> dict:
    """
    En cuantas subastas del Computer aparecimos, y con que
    resultado, contra lo que hicieron los demas.

    `subastas` son las del tablon, deduplicadas, con:
        {date, to_id, to_name, pujadores: {ids}}

    LO QUE ESTO MIDE Y LO QUE NO

        Mide si estuvimos EN LA MESA. No mide si acertamos: para
        eso esta el libro de pujas.

        Y es una COTA INFERIOR de la participacion de todos: el
        tablon publica las pujas perdedoras que publica. Afecta
        igual a las ocho plantillas, asi que la comparacion entre
        managers se sostiene aunque el nivel absoluto sea bajo.

    Nunca lanza. Con la lista vacia dice que no hay subastas, no
    que participamos en cero.
    """

    try:
        filas = [
            s for s in (subastas or []) if isinstance(s, dict)
        ]

        if not filas:
            return {
                "available": False,
                "n": 0,
                "reason": (
                    "No hay subastas que contar: sin tablon no se "
                    "puede decir si estabamos alli."
                ),
            }

        nosotros = safe_int(nuestro_id)

        dias = {s.get("dia") for s in filas if s.get("dia")}

        por_manager = {}

        for subasta in filas:

            ganador = safe_int(subasta.get("to_id"))

            participantes = {
                safe_int(p)
                for p in (subasta.get("pujadores") or [])
            } | ({ganador} if ganador else set())

            for quien in participantes:

                ficha = por_manager.setdefault(
                    quien,
                    {
                        "id": quien,
                        "name": None,
                        "pujadas": 0,
                        "ganadas": 0,
                        "dias": set(),
                    },
                )

                ficha["pujadas"] += 1

                if subasta.get("dia"):
                    ficha["dias"].add(subasta["dia"])

                if quien == ganador:
                    ficha["ganadas"] += 1

                    if subasta.get("to_name"):
                        ficha["name"] = subasta["to_name"]

        tabla = []

        for ficha in por_manager.values():
            tabla.append(
                {
                    "id": ficha["id"],
                    "name": ficha["name"],
                    "pujadas": ficha["pujadas"],
                    "ganadas": ficha["ganadas"],
                    "conversion": (
                        round(
                            ficha["ganadas"] / ficha["pujadas"] * 100,
                            1,
                        )
                        if ficha["pujadas"]
                        else None
                    ),
                    "participacion_percent": round(
                        ficha["pujadas"] / len(filas) * 100, 1
                    ),
                    "dias_con_puja": len(ficha["dias"]),
                    "dias_percent": (
                        round(len(ficha["dias"]) / len(dias) * 100, 1)
                        if dias
                        else None
                    ),
                    "es_nuestro": ficha["id"] == nosotros,
                }
            )

        tabla.sort(key=lambda f: -f["pujadas"])

        nuestra = next(
            (f for f in tabla if f["es_nuestro"]), None
        )

        lider = tabla[0] if tabla else None

        # Las que pasaron en dias en que no aparecimos. Es el
        # numero que separa "elegimos mal" de "no estabamos".
        nuestros_dias = {
            d
            for s in filas
            if s.get("dia")
            and (
                safe_int(s.get("to_id")) == nosotros
                or nosotros
                in {safe_int(p) for p in (s.get("pujadores") or [])}
            )
            for d in [s["dia"]]
        }

        fuera = sum(
            1
            for s in filas
            if s.get("dia") and s["dia"] not in nuestros_dias
        )

        return {
            "available": True,
            "n": len(filas),
            "dias": len(dias),
            "tabla": tabla,
            "nosotros": nuestra,
            "lider": lider,
            "subastas_en_dias_sin_puja_nuestra": fuera,

            "reason": (
                (
                    f"{len(filas)} subastas del Computer en "
                    f"{len(dias)} dias. Pujamos en "
                    f"{nuestra['pujadas']} ({nuestra['participacion_percent']} %) "
                    f"y ganamos {nuestra['ganadas']}: convertimos el "
                    f"{nuestra['conversion']} %. "
                    f"{lider['name']} pujo en {lider['pujadas']} "
                    f"({lider['participacion_percent']} %) y convirtio "
                    f"el {lider['conversion']} %. "
                    f"{fuera} subastas pasaron en dias en los que no "
                    f"pujamos ni una vez."
                )
                if nuestra and lider
                else f"{len(filas)} subastas, y no aparecemos en ninguna."
            ),
        }

    except Exception as error:                      # noqa: BLE001
        return {
            "available": False,
            "n": 0,
            "reason": (
                f"No se pudo medir la participacion: "
                f"{type(error).__name__}: {error}"
            ),
        }


# ============================================================
# BLOQUE 5 — LA REGLA DE ESTAR LISTO
# ============================================================


def regla_de_estar_listo(
    importes_ganadores: list | None,
    *,
    cajas: dict | None = None,
    ritmo_de_plantilla_percent_dia: float | None = None,
    cobertura_objetivo: float = 0.75,
) -> dict:
    """
    Que significa "estar listo" en euros, y que cuesta.

    LA CAJA SE MIDE CONTRA LO QUE CUESTA GANAR, no contra una
    cifra redonda. `importes_ganadores` son los importes con los
    que se cerraron las subastas del Computer: el percentil que
    se elija dice a que fraccion de ellas se llega.

    Y EL COSTE SE DICE. Tener caja parada no es gratis: mientras
    duerme, la plantilla se revaloriza a
    `ritmo_de_plantilla_percent_dia`. Ese es el alquiler de estar
    listo, y sale con su numero.

    SE PROPONE Y NO SE APLICA. Nadie lee esto para decidir nada.
    """

    try:
        importes = sorted(
            safe_int(x) for x in (importes_ganadores or []) if x
        )

        if len(importes) < 10:
            return {
                "available": False,
                "n": len(importes),
                "reason": (
                    f"Solo {len(importes)} subastas con importe: no "
                    f"da para una regla, y prefiero ninguna a una "
                    f"inventada."
                ),
            }

        def percentil(fraccion):
            indice = min(
                int(len(importes) * fraccion), len(importes) - 1
            )

            return importes[indice]

        objetivo = percentil(cobertura_objetivo)

        alcance = {}

        for etiqueta, cantidad in (cajas or {}).items():
            cantidad = safe_int(cantidad)

            alcanzan = sum(1 for x in importes if x <= cantidad)

            alcance[etiqueta] = {
                "caja": cantidad,
                "subastas_al_alcance": alcanzan,
                "percent": round(alcanzan / len(importes) * 100, 1),
            }

        ritmo = (
            float(ritmo_de_plantilla_percent_dia)
            if ritmo_de_plantilla_percent_dia is not None
            else None
        )

        coste_dia = (
            round(objetivo * ritmo / 100)
            if ritmo is not None
            else None
        )

        return {
            "available": True,
            "n": len(importes),

            "mediana": percentil(0.5),
            "p75": percentil(0.75),
            "p90": percentil(0.90),

            "caja_propuesta": objetivo,
            "cobertura_objetivo": cobertura_objetivo,
            "alcance": alcance,

            # LAS FICHAS. Una plaza libre evita tener que vender
            # en la misma vuelta, que es lo que rompe el once.
            "fichas_libres_propuestas": 1,
            "fichas_reason": (
                "Una ficha libre. Con cero, cada compra obliga a "
                "vender en la misma vuelta, y vender un titular "
                "antes de tener el recambio es lo que el freno de "
                "titularidad acaba de destapar."
            ),

            "coste_por_dia": coste_dia,
            "coste_por_mes": (
                coste_dia * 30 if coste_dia is not None else None
            ),
            "ritmo_de_plantilla_percent_dia": ritmo,

            "reason": (
                f"Para llegar al {cobertura_objetivo * 100:.0f} % de "
                f"las {len(importes)} subastas medidas hacen falta "
                f"{_miles(objetivo)} EUR libres (la mediana son "
                f"{_miles(percentil(0.5))}). "
                + (
                    f"Tenerlos parados cuesta {_miles(coste_dia)} EUR "
                    f"al dia —{_miles(coste_dia * 30)} al mes— al "
                    f"ritmo de {ritmo:.4f} %/dia al que se revaloriza "
                    f"la plantilla. Eso es el alquiler de estar "
                    f"listo, y se paga aunque no salga nadie."
                    if coste_dia is not None
                    else "El coste de tenerlos parados no se ha "
                    "podido medir: falta el ritmo de la plantilla."
                )
            ),
        }

    except Exception as error:                      # noqa: BLE001
        return {
            "available": False,
            "n": 0,
            "reason": (
                f"No se pudo escribir la regla: "
                f"{type(error).__name__}: {error}"
            ),
        }
