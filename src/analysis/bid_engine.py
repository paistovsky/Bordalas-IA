from src.analysis.recommendation_engine import generate_recommendations


def calculate_bid_recommendations(
    snapshot: dict,
    budget_limit: int | None = None,
) -> list[dict]:
    """
    budget_limit es el techo de concentracion por jugador.

    Antes se calculaba aqui dentro como el 45 % del SALDO. Con el
    saldo real del 16/08/2026 -239.968 EUR- eso daba 107.985, y el
    jugador mas barato del mercado costaba 150.000: los veinte
    salian como DEMASIADO CARO. Ese fue el motivo mas directo de
    que Pepe no pujara por nadie.

    El error era la magnitud elegida. En Biwenger se puede operar
    con deuda, y la capacidad de gasto no es el saldo sino
    maximumBid, que el propio juego calcula como saldo mas el
    limite de deuda. Un motor de recomendaciones que mide contra
    la caja esta midiendo contra la magnitud equivocada.

    Ahora el techo por defecto es maximumBid, y quien llame puede
    pasar uno mas ajustado. Los controles de dinero de verdad
    -presupuesto especulativo, contador de exposicion y valor
    racional por jugador- viven aguas abajo y son los que deciden
    si la puja se escribe.
    """

    recommendations = generate_recommendations(snapshot)

    maximum_bid = snapshot["market"]["status"]["maximumBid"]

    if budget_limit is None:
        budget_limit = maximum_bid

    # Jugadores que ya son nuestros.
    #
    # El 16/08/2026 este motor evaluaba a 13 de los 15 de la
    # plantilla como objetivos de compra, y Jutgla salia PUJAR a
    # 5.170.000 EUR. Los otros doce se libraban solo porque su
    # score no llegaba a 55: no habia nada que lo impidiese.
    #
    # Aguas abajo si hay guardias -SKIP_OWN_PLAYER-, pero para
    # entonces el jugador ya ha ocupado un puesto en el ranking y
    # puede haber desplazado a un objetivo de verdad.
    own_player_ids = set()

    for player in (snapshot.get("my_team") or []):
        try:
            own_player_ids.add(int(player["id"]))
        except (KeyError, TypeError, ValueError):
            continue

    results = []

    for player in recommendations:
        market_price = player["market_price"]
        player_price = player["player_price"]
        final_score = player["final_score"]
        price_increment = player.get("price_increment", 0) or 0

        # --------------------------------------------------
        # PRIMA SEGÚN INTERÉS
        # --------------------------------------------------

        if final_score >= 80:
            premium = 0.08

        elif final_score >= 75:
            premium = 0.06

        elif final_score >= 65:
            premium = 0.04

        elif final_score >= 55:
            premium = 0.02

        else:
            premium = 0.00

        # --------------------------------------------------
        # PEQUEÑO BONUS SI EL JUGADOR ESTÁ SUBIENDO
        # --------------------------------------------------

        trend_bonus = 0

        if price_increment >= 100_000:
            trend_bonus = 0.02

        elif price_increment > 0:
            trend_bonus = 0.01

        # --------------------------------------------------
        # PRECIO BASE
        # --------------------------------------------------

        base_price = max(
            market_price,
            player_price,
        )

        suggested_bid = int(
            base_price * (1 + premium + trend_bonus)
        )

        # Redondeamos a bloques de 10.000 €
        suggested_bid = (
            round(suggested_bid / 10_000)
            * 10_000
        )

        # --------------------------------------------------
        # PROTECCIÓN DE PRESUPUESTO
        # --------------------------------------------------

        affordable = (
            suggested_bid <= maximum_bid
            and suggested_bid <= budget_limit
        )

        # --------------------------------------------------
        # DECISIÓN
        # --------------------------------------------------

        own_player = False

        try:
            own_player = int(player["id"]) in own_player_ids
        except (KeyError, TypeError, ValueError):
            own_player = False

        if own_player:
            action = "YA ES NUESTRO"
            suggested_bid = 0

        elif final_score < 55:
            action = "NO PUJAR"
            suggested_bid = 0

        elif not affordable:
            action = "DEMASIADO CARO"

        else:
            action = "PUJAR"

        results.append(
            {
                **player,

                "premium_percent": premium * 100,

                "trend_bonus_percent":
                    trend_bonus * 100,

                "suggested_bid": suggested_bid,

                "budget_limit": budget_limit,

                "affordable": affordable,

                "own_player": own_player,

                "action": action,
            }
        )

    return results