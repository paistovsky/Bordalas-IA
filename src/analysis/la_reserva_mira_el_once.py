"""
La reserva de solvencia mira el once: a quien se guarda para vender,
y el aviso cuando el guardado es un titular.

LO QUE PASO (26/09/2026)

    25/09 21:12   Ruben Garcia y Alvaro Carreras: KEEP_SOLVENCY_RESERVED
    26/09 01:13   VENDIDO Ruben Garcia     2.414.900   ERA TITULAR
    26/09 03:11   VENDIDO Alvaro Carreras  1.255.900

    `KEEP_SOLVENCY_RESERVED` no queria decir "no vender": queria decir
    "guardala para la deuda". La misma rama la convierte en
    ACCEPT_BEFORE_EXPIRY a 6 h de caducar, y se cobra en ese ciclo.
    El plan funciono como esta escrito. Lo que fallo es el criterio.

DONDE ESTABA EL HUECO

    La reserva (`solvency_engine.calculate_offer_reservations`) elige
    dentro de la cartera A/B (`safe_debt_portfolio_engine`), que junta
    "sin tocar el once" y "vendiendo titulares con el once completo" y
    se queda con la de MAS DINERO. Y luego ordena por puntuacion de
    franquicia y estrategica. Ninguno de los dos criterios pregunta
    quien juega.

    Medido reproduciendo la reserva con el codigo de hoy sobre las 96
    fotos locales (12/08-19/09), con el reloj fijado a la hora de cada
    foto: 55 con deficit, en 5 episodios distintos. En 4 de los 5 la
    reserva metio a un titular (Ximo Navarro 12-14/08, Mangala 13/09)
    teniendo ofertas de suplentes que tapaban la deuda de sobra.

LA UNIDAD: PUNTOS DEL ONCE PERDIDOS POR EURO

    Con el interruptor, la reserva guarda primero lo que menos once
    cuesta por cada euro que trae. Es la cuenta espejo de la cola de
    fichajes (`la_cola.mejora_del_once`, 26/09): alli, cuanto SUMA el
    once rehecho con el candidato dentro; aqui, cuanto PIERDE el once
    rehecho con el jugador fuera. Las dos rehacen el once entero, con
    todas las formaciones, y las dos dan cero a quien no entra.

    El valor de cada jugador es el `lineup_score` con el que la
    cartera ya proyecta el once (`_project_lineup_fast`): el mismo
    numero que decide quien juega y si una venta es A o B. No se
    inventa otra escala.

    PERO NO SON PUNTOS, Y NO ES EL MISMO NUMERO QUE LA COLA. Medido
    sobre la foto del 13/09: `lineup_score` ~ 1.000.000 x el valor
    semanal esperado, mas un termino base (Ruben Garcia 593.771,
    Mangala 570.200). La cola usa puntos de temporada estimados
    (`estimate_season_points`), que la plantilla del once no trae.
    La FORMA es la misma -rehacer el once y quedarse con la
    diferencia-; la entrada no. Por eso se enseña como PORCENTAJE
    DEL ONCE, que no depende de la escala y es la medida con la que
    la cartera ya corta (`lineup_score_loss_percent`, 5 %). Y el
    orden no cambia con la escala: dividir por euro es monotono.

COMO SE CUENTAN LOS PUNTOS DE UN SUPLENTE: CERO, Y ES LO JUSTO

    En esta liga solo puntuan once: `lineupReserves: false`, sin
    cambios automaticos. Un suplente que sale no le quita al once ni
    un punto, porque el once de despues es el mismo que el de antes.

    Lo que NO es cero es un titular: su perdida es lo que el once
    rehecho pierde sin el, o sea sus puntos MENOS los del que entra
    por el. Si el recambio es casi tan bueno, un titular cuesta poco;
    si no hay recambio, cuesta el hueco entero. Eso ya lo da rehacer
    el once, sin etiquetas.

    Lo que esta cuenta no ve: el seguro. Un suplente cubre lesiones y
    sanciones, y eso vale algo que hoy no esta medido. Por eso la
    posicion minima la sigue guardando el guardarrail posicional -los
    `intocables` no entran en ninguna combinacion- y no esta cuenta.
    Inventarle un numero seria peor que decir que no lo tiene.

EL AVISO: CUANDO QUEDA RESERVADO, NO CUANDO SE VENDE

    El encargo pedia avisar "al entrar en la ventana de 6 h". Pero
    entrar en la ventana y vender son el MISMO ciclo: a <= 6 h el
    motor de reroll dice ACCEPT_BEFORE_EXPIRY y el orquestador cobra
    en esa vuelta. Un aviso ahi llega a la vez que la venta.

    Asi que el aviso salta en cuanto una oferta de un titular esta
    RESERVADA, y dice cuantas horas faltan para que entre en la
    ventana. Anoche habria salido, como tarde, a las 21:12: cuatro
    horas antes de vender a Ruben, con el dueño despierto.

    Y lleva los cuatro datos, o no sirve: quien, por cuanto, cuantos
    puntos del once cuesta, y cual es la alternativa -otras ofertas
    NO reservadas que junten el mismo dinero- con lo que cuesta ella.

NO DECIDE NADA POR SI MISMO

    Funciones puras. Ni disco, ni red, ni reloj. El interruptor se lee
    al llamar, nunca al importar. Nunca lanza.
"""

from __future__ import annotations

import os

from src.analysis.safe_debt_portfolio_engine import (
    _build_position_index,
    _project_lineup_fast,
)


LA_RESERVA_MIRA_EL_ONCE_ENV = "BORDALAS_LA_RESERVA_MIRA_EL_ONCE"


def mira_el_once() -> bool:
    """El interruptor. Se lee al llamar. NACE APAGADO."""

    return str(
        os.environ.get(LA_RESERVA_MIRA_EL_ONCE_ENV, "")
    ).strip().lower() in {"1", "true", "si", "yes"}


def safe_int(value, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def safe_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _ids(oferta: dict) -> set[int]:
    return {
        safe_int(value)
        for value in (oferta.get("player_ids") or [])
        if safe_int(value) > 0
    }


def _nombres(oferta: dict) -> str:
    nombres = [
        str(p.get("name"))
        for p in (oferta.get("players") or [])
        if isinstance(p, dict) and p.get("name")
    ]
    return " + ".join(nombres) or "+".join(
        str(i) for i in sorted(_ids(oferta))
    )


class _Once:
    """
    El once rehecho, con memoria. Lo que pierde al quitar a unos.

    Se ELIGE con `lineup_score`, como lo elige Pepe, y se VALORA con
    `lineup_score_sporting`, sin el bono del Dios: el bono esta para
    elegir, y dentro del total abarataria en proporcion a todos los
    demas (`lineup_engine`, "EL MISMO SCORE, SIN EL BONO DEL DIOS").
    """

    def __init__(self, plantilla):
        filas = [
            j for j in (plantilla or [])
            if isinstance(j, dict) and safe_int(j.get("id")) > 0
        ]
        self.valor = {
            safe_int(j.get("id")): float(
                j.get("lineup_score_sporting", j.get("lineup_score")) or 0.0
            )
            for j in filas
        }
        self.indice = _build_position_index(
            [
                {
                    "id": safe_int(j.get("id")),
                    "name": j.get("name"),
                    "position": safe_int(j.get("position")),
                    "lineup_score": float(j.get("lineup_score") or 0.0),
                }
                for j in filas
            ]
        )
        self.memoria: dict = {}
        self.base = self.puntos(set())

    def puntos(self, quitados: set[int]) -> float:
        clave = frozenset(quitados)
        if clave not in self.memoria:
            once = _project_lineup_fast(self.indice, set(quitados))
            self.memoria[clave] = sum(
                self.valor.get(safe_int(i), 0.0)
                for i in (once.get("selected_ids") or [])
            )
        return self.memoria[clave]

    def pierde(self, quitados: set[int]) -> float:
        return max(self.base - self.puntos(quitados), 0.0)

    def pct(self, perdido: float) -> float:
        """Lo perdido, en porcentaje del once de hoy."""
        return round(100.0 * perdido / self.base, 2) if self.base > 0 else 0.0


def _por_millon(pct: float, importe: int) -> float | None:
    return round(pct / (importe / 1_000_000), 4) if importe > 0 else None


def _desempate(oferta: dict) -> tuple:
    """El orden de antes, tal cual, para lo que cuesta lo mismo."""

    jugadores = oferta.get("players") or []
    return (
        max(
            [float((p or {}).get("franchise_score", 0) or 0) for p in jugadores]
            or [0.0]
        ),
        max(
            [float((p or {}).get("strategic_score", 0) or 0) for p in jugadores]
            or [0.0]
        ),
        -float(oferta.get("premium_percent", 0) or 0),
        -safe_int(oferta.get("amount")),
    )


def _voraz(once: _Once, ofertas: list, quitados0: set | None = None, tope=None):
    """
    En cada paso, la oferta que menos once pierde por euro, contando
    lo ya quitado. Con `tope`, para en cuanto junta ese dinero.
    """

    quedan = [o for o in ofertas if _ids(o) and safe_int(o.get("amount")) > 0]
    quitados = set(quitados0 or set())
    juntado = 0
    filas = []

    while quedan and (tope is None or juntado < tope):
        mejor = None
        for oferta in quedan:
            importe = safe_int(oferta.get("amount"))
            antes = once.pierde(quitados)
            marginal = max(once.pierde(quitados | _ids(oferta)) - antes, 0.0)
            clave = (marginal / importe, marginal, *_desempate(oferta))
            if mejor is None or clave < mejor[0]:
                mejor = (clave, oferta, marginal)

        _, oferta, marginal = mejor
        quedan.remove(oferta)
        quitados |= _ids(oferta)
        importe = safe_int(oferta.get("amount"))
        juntado += importe
        filas.append(
            {
                "offer_id": oferta.get("offer_id"),
                "jugadores": _nombres(oferta),
                "importe": importe,
                "once_perdido_pct": once.pct(marginal),
                "once_pct_por_millon": _por_millon(once.pct(marginal), importe),
            }
        )

    return filas, juntado, quitados


def ordenar_por_puntos_por_euro(ofertas, plantilla) -> list:
    """
    Las ofertas en el orden en que se deberian guardar: primero la que
    menos once cuesta por euro. Voraz y marginal: cada paso cuenta lo
    que el once pierde CON lo ya elegido fuera, porque dos laterales
    no cuestan la suma de lo que cuesta cada uno.

    Devuelve las filas con su `offer_id`. Nunca lanza: si algo falla,
    devuelve [] y quien llama se queda con el orden de siempre.
    """

    try:
        filas, _, _ = _voraz(_Once(plantilla), list(ofertas or []))
        return filas
    except Exception:                               # noqa: BLE001
        return []


def ventana_de_cobro() -> float:
    """
    Las horas a las que una reservada se cobra sola. No es un numero
    de aqui: es el del motor de reroll, que es quien la cobra.
    """

    from src.analysis.computer_offer_reroll_engine import (
        ACCEPT_BEFORE_DEADLINE_HOURS,
        ACCEPT_BEFORE_EXPIRY_HOURS,
    )

    return float(min(ACCEPT_BEFORE_EXPIRY_HOURS, ACCEPT_BEFORE_DEADLINE_HOURS))


def las_ventas_de_titular(
    reservadas,
    ofertas,
    plantilla,
    titulares,
    intocables=None,
    horas_al_plazo=None,
    ventana=None,
) -> list:
    """
    Un aviso por cada oferta RESERVADA que se lleva a un titular.

    Cada aviso trae los cuatro datos: quien, por cuanto, cuantos
    puntos del once cuesta, y la alternativa -ofertas NO reservadas,
    sin intocables, que junten el mismo dinero- con lo que cuesta
    ella. Si no hay con que juntarlo, lo dice.

    Y cuando se vende: las horas que faltan para que entre en la
    ventana de cobro, por caducidad o por el plazo de la jornada, lo
    que llegue antes. `en_la_ventana` si ya esta dentro.

    Nunca lanza: si algo falla, devuelve [].
    """

    try:
        titulares = {safe_int(i) for i in (titulares or [])}
        intocables = {safe_int(i) for i in (intocables or [])}
        ventana = float(ventana if ventana is not None else ventana_de_cobro())
        plazo = safe_float(horas_al_plazo)

        reservadas = [o for o in (reservadas or []) if isinstance(o, dict)]
        guardadas = {o.get("offer_id") for o in reservadas}

        libres = [
            o
            for o in (ofertas or [])
            if isinstance(o, dict)
            and o.get("offer_id") not in guardadas
            and not (_ids(o) & intocables)
        ]

        once = _Once(plantilla)
        avisos = []

        for oferta in reservadas:
            suyos = _ids(oferta) & titulares
            if not suyos:
                continue

            importe = safe_int(oferta.get("amount"))
            cuesta = once.pierde(_ids(oferta))

            caduca = safe_float(oferta.get("hours_to_expiry"))
            relojes = [h for h in (caduca, plazo) if h is not None]
            cobro_en = min(relojes) - ventana if relojes else None

            filas, juntado, fuera = _voraz(once, libres, tope=importe)
            alternativa = {
                "junta": importe > 0 and juntado >= importe,
                "jugadores": " + ".join(f["jugadores"] for f in filas),
                "importe": juntado,
                "once_perdido_pct": once.pct(once.pierde(fuera)),
                "ofertas": [f["offer_id"] for f in filas],
            }

            avisos.append(
                {
                    "offer_id": oferta.get("offer_id"),
                    "quien": _nombres(oferta),
                    "titulares": sorted(suyos),
                    "por_cuanto": importe,
                    "once_perdido_pct": once.pct(cuesta),
                    "once_pct_por_millon": _por_millon(once.pct(cuesta), importe),
                    "horas_a_caducar": caduca,
                    "horas_para_el_cobro": (
                        round(max(cobro_en, 0.0), 2) if cobro_en is not None else None
                    ),
                    "en_la_ventana": bool(cobro_en is not None and cobro_en <= 0),
                    "alternativa": alternativa,
                    "texto": _el_texto(
                        oferta, importe, once.pct(cuesta), cobro_en, alternativa
                    ),
                }
            )

        return avisos

    except Exception:                               # noqa: BLE001
        return []


def _euros(valor) -> str:
    return f"{safe_int(valor):,}".replace(",", ".")


def _el_texto(oferta, importe, cuesta_pct, cobro_en, alternativa) -> str:
    if cobro_en is None:
        cuando = "sin hora de caducidad conocida"
    elif cobro_en <= 0:
        cuando = "YA en la ventana: se cobra en este ciclo o el siguiente"
    else:
        cuando = f"entra en la ventana de cobro dentro de {cobro_en:.1f} h"

    if alternativa["junta"]:
        otra = (
            f"Alternativa: {alternativa['jugadores']} por "
            f"{_euros(alternativa['importe'])}, cuesta el "
            f"{alternativa['once_perdido_pct']:.1f} % del once."
        )
    elif alternativa["importe"] > 0:
        otra = (
            f"Sin alternativa entera: lo no reservado junta "
            f"{_euros(alternativa['importe'])} de {_euros(importe)} "
            f"({alternativa['jugadores']}, el "
            f"{alternativa['once_perdido_pct']:.1f} % del once)."
        )
    else:
        otra = "Sin alternativa: no queda ninguna oferta libre con que juntarlo."

    return (
        f"VENTA DE TITULAR RESERVADA: {_nombres(oferta)} por "
        f"{_euros(importe)}, cuesta el {cuesta_pct:.1f} % del once; "
        f"{cuando}. {otra}"
    )
