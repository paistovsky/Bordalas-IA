"""
A quien conviene soltar.

QUE CAMBIO EL 17/08/2026

    Esto puntuaba con tres cosas: puntos de la TEMPORADA PASADA,
    variacion de precio y si entra en el once. Ninguna dice que es
    un jugador AHORA.

    Con la plantilla real del 17/08 producia dos errores opuestos
    y sistematicos:

        Gustavo Puerta  CLAVE en el Racing, sin LaLiga el ano
                        pasado -> +25 por "bajo rendimiento
                        historico". Marcado para vender por ser un
                        fichaje nuevo.

        Hugo Rincon     RESERVA en el Athletic, 107 puntos el ano
                        pasado y titular hoy por falta de
                        alternativa -> -15 por estar en el once.
                        Protegido.

    El historico mide lo que fue; la jerarquia mide lo que es. Para
    decidir una venta -que dura meses- manda la segunda.

LO QUE SIGUE SIN HACER

    No vende. Puntua y ordena. Quien decide si una venta esta
    permitida es `position_guardrail`, y quien la ejecuta, el
    executor.
"""

from src.analysis.lineup_engine import build_lineup
from src.analysis.team_analyzer import analyze_team


MIN_POSITION_COUNTS = {
    1: 1,  # Portero
    2: 4,  # Defensas
    3: 3,  # Centrocampistas
    4: 3,  # Delanteros
}


# Cuanto pesa la jerarquia en la decision de vender.
#
# Un Reserva no va a puntuar aunque el ano pasado lo hiciera en
# otro sitio, y un Clave no se suelta aunque no tenga historico.
HIERARCHY_SALE_SCORE = {
    60: -30,   # Dios
    50: -25,   # Clave
    40: -10,   # Importante
    30: 5,     # Rotacion
    25: 15,    # Revulsivo
    20: 25,    # Reserva
    10: 30,    # Descarte
}

# Desde que escalon el historico deja de contar en contra: no
# tener puntos del ano pasado no es un defecto en alguien que hoy
# es titular fijo de su equipo. Suele ser un fichaje nuevo.
HIERARCHY_TRUSTS_PRESENT = 40

# Una baja larga es un activo que se deshace solo: pierde
# jornadas y pierde precio.
ABSENCE_SALE_SCORE = (
    (10, 30),
    (4, 20),
    (1, 5),
)


def _ff_signal(player_id) -> dict:
    """
    Blindado: sin tablero de FutbolFantasy se puntua como antes.
    Peor, pero nunca se cae.
    """

    try:
        from src.analysis.candidate_starter_lookup import (
            get_starter_lookup,
        )

        return get_starter_lookup().get(int(player_id)) or {}

    except Exception:
        return {}


def analyze_sales(snapshot: dict) -> list[dict]:
    team = snapshot["my_team"]

    lineup = build_lineup(snapshot)
    team_analysis = analyze_team(snapshot)

    selected_ids = {
        player["id"]
        for player in lineup["selected"]
    }

    results = []

    for player in team:
        player_id = player["id"]
        position = player["position"]

        price = player.get("price", 0) or 0
        price_increment = player.get("priceIncrement", 0) or 0
        last_points = player.get("pointsLastSeason", 0) or 0

        position_count = (
            team_analysis["positions"]
            [position]
            ["count"]
        )

        in_lineup = (
            player_id
            in selected_ids
        )

        sale_score = 0
        reasons = []

        # --------------------------------------------------
        # QUE ES HOY EN SU EQUIPO
        # --------------------------------------------------

        senal = _ff_signal(player_id)

        jerarquia = senal.get("hierarchy_value")
        etiqueta = senal.get("hierarchy_label")

        if jerarquia:

            sale_score += HIERARCHY_SALE_SCORE.get(jerarquia, 0)

            if jerarquia >= 50:
                reasons.append(
                    f"Es {etiqueta} en su equipo: no se suelta"
                )

            elif jerarquia <= 20:
                reasons.append(
                    f"Es {etiqueta} en su equipo: no va a puntuar"
                )

        # --------------------------------------------------
        # CUANTO VA A ESTAR FUERA
        # --------------------------------------------------

        ausencia = senal.get("absence") or {}

        fuera = ausencia.get("matchdays_out")

        if ausencia.get("basis") == "INDEFINIDA" and not fuera:
            fuera = 10

        if fuera:

            for umbral, puntos in ABSENCE_SALE_SCORE:

                if fuera >= umbral:

                    sale_score += puntos

                    if puntos >= 20:
                        reasons.append(
                            f"Se pierde {fuera} jornadas: "
                            f"cada semana vale menos"
                        )

                    break

        # --------------------------------------------------
        # NO ENTRA EN EL XI
        # --------------------------------------------------

        if not in_lineup:
            sale_score += 20
            reasons.append(
                "No entra en el XI actual"
            )

        # --------------------------------------------------
        # RENDIMIENTO HISTÓRICO
        # --------------------------------------------------

        # EL HISTORICO NO CUENTA CONTRA QUIEN HOY ES TITULAR FIJO
        #
        # Sin esto, un fichaje nuevo que llega de Clave sale
        # marcado para vender por no haber jugado en LaLiga el ano
        # pasado. Le paso a Gustavo Puerta el 17/08/2026.
        historico_cuenta = not (
            jerarquia and jerarquia >= HIERARCHY_TRUSTS_PRESENT
        )

        if not historico_cuenta and last_points < 50:
            reasons.append(
                f"Sin histórico en LaLiga, pero hoy es {etiqueta}: "
                f"no cuenta en su contra"
            )

        elif last_points < 50:
            sale_score += 25
            reasons.append(
                "Bajo rendimiento histórico"
            )

        elif last_points < 100 and historico_cuenta:
            sale_score += 10
            reasons.append(
                "Rendimiento histórico limitado"
            )

        # --------------------------------------------------
        # TENDENCIA DE PRECIO
        # --------------------------------------------------

        if price_increment <= -100_000:
            sale_score += 25
            reasons.append(
                "Caída fuerte de valor"
            )

        elif price_increment < 0:
            sale_score += 10
            reasons.append(
                "Valor de mercado bajando"
            )

        # --------------------------------------------------
        # EXCESO DE JUGADORES EN POSICIÓN
        # --------------------------------------------------

        minimum_required = (
            MIN_POSITION_COUNTS[
                position
            ]
        )

        surplus = (
            position_count
            - minimum_required
        )

        if surplus >= 2:
            sale_score += 15
            reasons.append(
                "Hay margen en esta posición"
            )

        elif surplus >= 1:
            sale_score += 5

        # --------------------------------------------------
        # ACTIVO DE BAJO IMPACTO
        # --------------------------------------------------

        if (
            price <= 300_000
            and last_points < 50
        ):
            sale_score += 10
            reasons.append(
                "Activo de poco impacto deportivo"
            )

        # --------------------------------------------------
        # PENALIZACIÓN POR SER IMPORTANTE
        # --------------------------------------------------

        # ESTAR EN EL ONCE PROTEGE, PERO NO A CUALQUIERA
        #
        # Un Reserva puede estar hoy en el once simplemente porque
        # no hay nadie mejor en su puesto. Eso no es una razon para
        # conservarlo: es el sintoma de que hace falta fichar ahi.
        if in_lineup:

            if jerarquia and jerarquia <= 20:
                reasons.append(
                    "Está en el once por falta de alternativa, "
                    "no por ser mejor"
                )

            else:
                sale_score -= 15

        sale_score = max(
            sale_score,
            0,
        )

        # --------------------------------------------------
        # CLASIFICACIÓN
        # --------------------------------------------------

        if sale_score >= 60:
            recommendation = "VENDER"

        elif sale_score >= 40:
            recommendation = "CONSIDERAR VENTA"

        elif sale_score >= 20:
            recommendation = "VIGILAR"

        else:
            recommendation = "MANTENER"

        results.append(
            {
                "id":
                    player_id,

                "name":
                    player["name"],

                "position":
                    position,

                "price":
                    price,

                "price_increment":
                    price_increment,

                "points_last_season":
                    last_points,

                "in_lineup":
                    in_lineup,

                "position_count":
                    position_count,

                "minimum_required":
                    minimum_required,

                "hierarchy":
                    etiqueta,

                "hierarchy_value":
                    jerarquia,

                "starter_probability":
                    senal.get("probability"),

                "availability":
                    (senal.get("availability") or {}).get("label"),

                "matchdays_out":
                    fuera,

                "sale_score":
                    sale_score,

                "recommendation":
                    recommendation,

                "reasons":
                    reasons,
            }
        )

    results.sort(
        key=lambda player:
            player["sale_score"],
        reverse=True,
    )

    return results