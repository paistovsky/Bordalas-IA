from __future__ import annotations

from datetime import datetime, timezone
from math import log10
from typing import Any

from src.intelligence.jornada_perfecta_market_provider import (
    load_jornada_perfecta_market_data,
    refresh_jornada_perfecta_market_data,
)


HORIZONS = (1, 2, 3, 5, 10, 14, 30)

TIP_SCORES = {
    "muyrecomendable": 100.0,
    "recomendable": 78.0,
    "neutral": 50.0,
    "duda": 42.0,
    "norecomendable": 18.0,
    "muy_norecomendable": 5.0,
}

FORECAST_SCORES = {
    "titular": 100.0,
    "probable": 72.0,
    "suplente": 30.0,
}

EDITORIAL_BASE = {
    "CHOLLO": 100.0,
    "TAPADO": 88.0,
    "RENTABLE": 82.0,
    "EDITORIAL": 70.0,
}

# El mercado de JP no necesita refresco cada 30 minutos.
# Dos horas mantienen la inteligencia suficientemente fresca
# sin bombardear la fuente externa.
MAX_PROVIDER_CACHE_AGE_HOURS = 2.0


def clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, float(value)))


def normalize_token(value: Any) -> str:
    return (
        str(value or "")
        .strip()
        .lower()
        .replace("_", "")
        .replace("-", "")
        .replace(" ", "")
    )


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return default


def parse_datetime(value: Any) -> datetime | None:
    if not value:
        return None

    try:
        parsed = datetime.fromisoformat(
            str(value).replace("Z", "+00:00")
        )
    except (TypeError, ValueError):
        return None

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)

    return parsed.astimezone(timezone.utc)


def age_hours(value: Any) -> float | None:
    parsed = parse_datetime(value)

    if parsed is None:
        return None

    return max(
        0.0,
        (datetime.now(timezone.utc) - parsed).total_seconds() / 3600.0,
    )


def horizon_change(player: dict, horizon: int) -> float:
    last = player.get("last_markets") or {}
    return safe_float(
        last.get(str(horizon), last.get(horizon, 0))
    )


def previous_price(player: dict, horizon: int) -> float:
    """
    JP expone lastMarkets como variacion acumulada respecto al precio
    actual. Por tanto, precio_hace_N ~= precio_actual - variacion_N.
    """
    current = safe_float(player.get("price"))
    change = horizon_change(player, horizon)
    return max(current - change, 1.0)


def return_pct(player: dict, horizon: int) -> float:
    change = horizon_change(player, horizon)
    base = previous_price(player, horizon)

    if base <= 0:
        return 0.0

    return (change / base) * 100.0


def daily_return_pct(player: dict, horizon: int) -> float:
    return return_pct(player, horizon) / max(float(horizon), 1.0)


def saturating_positive_score(value: float, full_at: float) -> float:
    """
    0 -> 0 puntos.
    full_at o mas -> 100 puntos.
    Valores negativos no suman momentum positivo.
    """
    if value <= 0:
        return 0.0

    return clamp((value / full_at) * 100.0)


def build_momentum_metrics(player: dict) -> dict:
    returns = {
        str(h): round(return_pct(player, h), 4)
        for h in HORIZONS
    }

    daily = {
        str(h): round(daily_return_pct(player, h), 4)
        for h in HORIZONS
    }

    # Corto plazo pesa mas: especulacion necesita velocidad reciente.
    momentum_score = (
        saturating_positive_score(daily["1"], 10.0) * 0.35
        + saturating_positive_score(daily["3"], 7.0) * 0.30
        + saturating_positive_score(daily["5"], 5.0) * 0.20
        + saturating_positive_score(daily["10"], 3.0) * 0.10
        + saturating_positive_score(daily["14"], 2.5) * 0.05
    )

    observed = [
        horizon_change(player, h)
        for h in (1, 3, 5, 10, 14)
        if horizon_change(player, h) != 0
    ]

    if observed:
        positive_ratio = sum(
            1 for value in observed if value > 0
        ) / len(observed)
        negative_ratio = sum(
            1 for value in observed if value < 0
        ) / len(observed)
        consistency_score = clamp(
            50.0 + 50.0 * positive_ratio - 70.0 * negative_ratio
        )
    else:
        consistency_score = 45.0

    # Comparamos velocidad muy reciente con velocidad 5d.
    acceleration_raw = daily["1"] - daily["5"]
    acceleration_score = clamp(
        50.0 + acceleration_raw * 8.0
    )

    # Deteccion conservadora de discontinuidades / cambios de base.
    # Si un horizonte largo implica una subida desproporcionada respecto
    # al precio actual y no esta respaldada por el corto plazo, no dejamos
    # que infle el score.
    suspicious = False
    reasons = []

    price = max(safe_float(player.get("price")), 1.0)
    change_5 = abs(horizon_change(player, 5))
    change_10 = abs(horizon_change(player, 10))
    change_30 = abs(horizon_change(player, 30))

    if change_5 > price * 1.5 and abs(horizon_change(player, 1)) < price * 0.10:
        suspicious = True
        reasons.append("5D_DISCONTINUITY")

    if change_10 > price * 2.5 and change_5 < change_10 * 0.35:
        suspicious = True
        reasons.append("10D_DISCONTINUITY")

    if change_30 > price * 4.0 and change_10 < change_30 * 0.35:
        suspicious = True
        reasons.append("30D_DISCONTINUITY")

    outlier_multiplier = 0.72 if suspicious else 1.0

    market_score = (
        momentum_score * 0.62
        + consistency_score * 0.23
        + acceleration_score * 0.15
    ) * outlier_multiplier

    return {
        "returns_pct": returns,
        "daily_returns_pct": daily,
        "momentum_score": round(clamp(momentum_score), 2),
        "consistency_score": round(consistency_score, 2),
        "acceleration_score": round(acceleration_score, 2),
        "acceleration_raw": round(acceleration_raw, 4),
        "outlier": suspicious,
        "outlier_reasons": reasons,
        "outlier_multiplier": outlier_multiplier,
        "market_score": round(clamp(market_score), 2),
    }


def build_price_context(player: dict) -> dict:
    price = max(safe_float(player.get("price")), 0.0)
    min_price = max(safe_float(player.get("min_price")), 0.0)
    max_price = max(safe_float(player.get("max_price")), 0.0)

    if max_price > min_price and price > 0:
        range_position = clamp(
            ((price - min_price) / (max_price - min_price)) * 100.0
        )
    else:
        range_position = 50.0

    if max_price > 0 and price > 0:
        distance_to_max_pct = ((max_price - price) / price) * 100.0
    else:
        distance_to_max_pct = 0.0

    # Precio bajo no significa automaticamente mejor, pero en especulacion
    # facilita rotacion de capital. El efecto es deliberadamente pequeño.
    if price <= 0:
        affordability_score = 0.0
    else:
        millions = price / 1_000_000.0
        affordability_score = clamp(
            100.0 - max(0.0, log10(max(millions, 0.1)) * 28.0)
        )

    return {
        "range_position_pct": round(range_position, 2),
        "distance_to_max_pct": round(distance_to_max_pct, 2),
        "affordability_score": round(affordability_score, 2),
    }


def build_tip_score(player: dict) -> dict:
    token = normalize_token(player.get("tip"))

    if token in TIP_SCORES:
        score = TIP_SCORES[token]
    elif "muyrecomend" in token:
        score = 100.0
    elif "norecomend" in token:
        score = 18.0
    elif "recomend" in token:
        score = 78.0
    else:
        score = 50.0

    return {
        "tip": player.get("tip"),
        "tip_desc": player.get("tip_desc"),
        "tip_score": round(score, 2),
    }


def build_availability_score(player: dict) -> dict:
    injured = str(player.get("injured", "0")) not in ("0", "", "None", "none")
    doubt = str(player.get("doubt", "0")) not in ("0", "", "None", "none")
    penalized = str(player.get("penalized", "0")) not in ("0", "", "None", "none")
    available = str(player.get("available", "0"))

    score = 100.0

    if injured:
        score -= 70.0

    if penalized:
        score -= 55.0

    if doubt:
        score -= 28.0

    # No interpretamos available como booleano absoluto porque JP puede
    # usar codigos internos. Lo conservamos para diagnostico.
    return {
        "available_raw": available,
        "injured": injured,
        "doubt": doubt,
        "penalized": penalized,
        "availability_score": round(clamp(score), 2),
    }


def editorial_decay(age: float | None) -> float:
    """
    Señal editorial muy fresca: fuerte.
    7 dias: todavia util.
    14 dias: residual.
    >30 dias: cero para decisiones actuales.
    """
    if age is None:
        return 0.0

    days = age / 24.0

    if days <= 1:
        return 1.0
    if days <= 3:
        return 0.90
    if days <= 7:
        return 0.72
    if days <= 14:
        return 0.40
    if days <= 21:
        return 0.18
    if days <= 30:
        return 0.07

    return 0.0


def build_editorial_score(player: dict) -> dict:
    signals = player.get("editorial_signals") or []

    best_score = 0.0
    best_signal = None

    for signal in signals:
        signal_age = signal.get("age_hours")

        if signal_age is None:
            signal_age = age_hours(
                signal.get("published_at")
            )

        decay = editorial_decay(
            safe_float(signal_age, -1.0)
            if signal_age is not None
            else None
        )

        editorial_type = str(
            signal.get("editorial_type") or "EDITORIAL"
        ).upper()

        base = EDITORIAL_BASE.get(
            editorial_type,
            EDITORIAL_BASE["EDITORIAL"],
        )

        forecast = normalize_token(
            signal.get("forecast")
        )
        forecast_score = FORECAST_SCORES.get(
            forecast,
            50.0,
        )

        score = (
            base * 0.78
            + forecast_score * 0.22
        ) * decay

        if score > best_score:
            best_score = score
            best_signal = {
                **signal,
                "effective_age_hours": (
                    round(signal_age, 2)
                    if signal_age is not None
                    else None
                ),
                "decay": round(decay, 4),
            }

    return {
        "editorial_score": round(clamp(best_score), 2),
        "latest_relevant_editorial": best_signal,
        "editorial_signal_count": len(signals),
    }


def build_racha_score(player: dict) -> dict:
    racha = safe_float(player.get("racha"))

    # No conocemos aun la escala exacta editorial de racha en todos los
    # casos. La usamos como señal secundaria y acotada.
    score = clamp(50.0 + racha * 7.5)

    return {
        "racha": player.get("racha"),
        "racha_score": round(score, 2),
    }


def build_jp_market_intelligence(player: dict) -> dict:
    momentum = build_momentum_metrics(player)
    price_context = build_price_context(player)
    tip = build_tip_score(player)
    availability = build_availability_score(player)
    editorial = build_editorial_score(player)
    racha = build_racha_score(player)

    # El mercado manda. Editorial/tip ayudan, pero no pueden convertir
    # por si solos un jugador sin tendencia en una compra excelente.
    score = (
        momentum["market_score"] * 0.55
        + tip["tip_score"] * 0.16
        + availability["availability_score"] * 0.10
        + editorial["editorial_score"] * 0.10
        + racha["racha_score"] * 0.05
        + price_context["affordability_score"] * 0.04
    )

    # Penalizaciones duras.
    if availability["injured"]:
        score *= 0.58

    if availability["penalized"]:
        score *= 0.70

    # Tendencia negativa reciente: no queremos que un tip editorial
    # o una buena racha oculte que el precio ya esta cayendo.
    if horizon_change(player, 1) < 0:
        score *= 0.72

    if (
        horizon_change(player, 1) < 0
        and horizon_change(player, 3) < 0
    ):
        score *= 0.78

    final_score = round(clamp(score), 2)

    if final_score >= 82:
        action = "STRONG_BUY_INTEL"
    elif final_score >= 72:
        action = "BUY_INTEL"
    elif final_score >= 60:
        action = "WATCH_BUY"
    elif final_score >= 45:
        action = "NEUTRAL"
    else:
        action = "AVOID"

    return {
        "jp_player_id": player.get("jp_player_id"),
        "biwenger_remote_id": player.get("biwenger_remote_id"),
        "slug": player.get("slug"),
        "name": player.get("name"),
        "team": player.get("team"),
        "position": player.get("position"),
        "price": player.get("price"),
        "max_price": player.get("max_price"),
        "min_price": player.get("min_price"),
        "last_markets": player.get("last_markets") or {},
        **momentum,
        **price_context,
        **tip,
        **availability,
        **editorial,
        **racha,
        "jp_market_score": final_score,
        "intelligence_action": action,
    }


def build_all_jp_market_intelligence(
    data: dict,
) -> list[dict]:
    players = data.get("players") or []

    result = [
        build_jp_market_intelligence(player)
        for player in players
        if isinstance(player, dict)
    ]

    result.sort(
        key=lambda item: item["jp_market_score"],
        reverse=True,
    )

    return result


def refresh_jp_market_intelligence(
    force_provider_refresh: bool = False,
) -> dict:
    """
    Usa cache de mercado JP mientras sea reciente.

    Si no existe o supera MAX_PROVIDER_CACHE_AGE_HOURS,
    refresca automaticamente /mercado/ + /chollos/.
    """
    data = load_jornada_perfecta_market_data()

    current_age = (
        age_hours(data.get("updated_at"))
        if isinstance(data, dict)
        else None
    )

    stale = bool(
        data is None
        or current_age is None
        or current_age > MAX_PROVIDER_CACHE_AGE_HOURS
    )

    provider_error = None

    if force_provider_refresh or stale:

        # ESTO ES UN ENRIQUECIMIENTO, NO UNA DEPENDENCIA.
        #
        # Sin la red, `fetch_html` lanza y la excepcion subia
        # entera por `build_speculation_board` ->
        # `build_offer_decision_board` -> `build_global_decision`
        # hasta tumbar el ciclo y la generacion del dashboard.
        #
        # El scraper corre igual en el PC de casa que en GitHub
        # Actions, pero desde Actions sale por una IP de centro
        # de datos y Jornada Perfecta la rechaza. Resultado: en
        # local todo bien, y en produccion el paso falla, el
        # workflow aborta y el dashboard desplegado se queda
        # congelado en la ultima ejecucion que si salio.
        #
        # Sin este try, un 403 de una pagina de terceros decide
        # si Pepe opera.
        try:
            provider_result = refresh_jornada_perfecta_market_data(
                force=True
            )
            data = provider_result["data"]
            provider_status = provider_result["status"]

        except Exception as error:
            provider_error = f"{type(error).__name__}: {error}"
            provider_status = (
                "STALE_FALLBACK"
                if isinstance(data, dict)
                else "UNAVAILABLE"
            )

    else:
        provider_status = "CACHE"

    if not isinstance(data, dict):
        data = {}

    try:
        intelligence = build_all_jp_market_intelligence(data)
    except Exception as error:
        provider_error = (
            provider_error
            or f"{type(error).__name__}: {error}"
        )
        intelligence = []

    return {
        "source": "JORNADA_PERFECTA_MARKET_INTELLIGENCE",
        "provider_status": provider_status,
        "provider_error": provider_error,
        "available": bool(intelligence),
        "updated_at": data.get("updated_at"),
        "age_hours": age_hours(data.get("updated_at")),
        "players": intelligence,
        "player_count": len(intelligence),
    }

def intelligence_by_biwenger_id(
    intelligence_payload: dict,
) -> dict[int, dict]:
    result = {}

    for player in intelligence_payload.get("players") or []:
        remote_id = player.get("biwenger_remote_id")

        try:
            remote_id = int(remote_id)
        except (TypeError, ValueError):
            continue

        if remote_id:
            result[remote_id] = player

    return result
