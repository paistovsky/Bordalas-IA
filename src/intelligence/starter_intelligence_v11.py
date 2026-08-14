from __future__ import annotations

SOURCE_NAMES = ("JORNADA_PERFECTA","FUTBOLFANTASY","ANALITICA_FANTASY")
STATUS_PROBABILITY = {
    "TITULAR": 94.0,
    "PROBABLE": 76.0,
    "DUDA": 50.0,
    "SUPLENTE": 24.0,
    "NO_CONVOCADO": 1.0,
    "UNKNOWN": 50.0,
}

def clamp(value, lo=0.0, hi=100.0):
    return max(lo, min(hi, float(value)))

def normalize_confidence(value):
    try:
        value = float(value)
    except (TypeError, ValueError):
        return 0.0
    if 0.0 <= value <= 1.0:
        value *= 100.0
    return clamp(value)

def probability_from_signal(signal):
    if not signal:
        return 50.0

    explicit = signal.get("starter_probability")
    if explicit is None:
        explicit = signal.get("probability")

    if explicit is not None:
        try:
            value = float(explicit)
            if 0.0 <= value <= 1.0:
                value *= 100.0
            return clamp(value)
        except (TypeError, ValueError):
            pass

    status = str(signal.get("status") or "UNKNOWN").upper()
    base = STATUS_PROBABILITY.get(status, 50.0)
    confidence = normalize_confidence(
        signal.get("confidence")
        if signal.get("confidence") is not None
        else signal.get("effective_confidence")
    )
    return clamp(50.0 + (base - 50.0) * (confidence / 100.0))

def extract_source_signals(external):
    external = external or {}
    result = {}

    raw_sources = external.get("sources") or {}
    if isinstance(raw_sources, dict):
        for name in SOURCE_NAMES:
            signal = raw_sources.get(name) or raw_sources.get(name.lower())
            if isinstance(signal, dict) and signal:
                result[name] = signal

    if "JORNADA_PERFECTA" not in result:
        status = external.get("status")
        if status and str(status).upper() != "UNKNOWN":
            result["JORNADA_PERFECTA"] = {
                "status": status,
                "confidence": (
                    external.get("confidence")
                    if external.get("confidence") is not None
                    else external.get("effective_confidence")
                ),
                "probability": external.get("probability"),
            }

    return result

def build_starter_signal(external=None):
    signals = extract_source_signals(external or {})
    rows = []
    values = []

    for source in SOURCE_NAMES:
        signal = signals.get(source)
        if not signal:
            continue

        probability = probability_from_signal(signal)
        values.append(probability)
        rows.append({
            "source": source,
            "status": str(signal.get("status") or "UNKNOWN").upper(),
            "starter_probability": round(probability, 1),
        })

    coverage = len(rows)
    probability = sum(values) / len(values) if values else 50.0

    starter_votes = sum(r["starter_probability"] >= 67 for r in rows)
    bench_votes = sum(r["starter_probability"] <= 40 for r in rows)

    if coverage >= 2 and starter_votes >= 2:
        consensus = "STARTER"
    elif coverage >= 2 and bench_votes >= 2:
        consensus = "BENCH"
    elif coverage >= 2:
        consensus = "MIXED"
    elif coverage == 1:
        consensus = "SINGLE_SOURCE"
    else:
        consensus = "NO_DATA"

    tier = {3:"HIGH",2:"MEDIUM",1:"LOW",0:"NONE"}[coverage]

    return {
        "starter_probability": round(probability, 1),
        "expected_minutes": round(clamp(probability * 0.90, 0, 90), 1),
        "source_coverage": coverage,
        "confidence_tier": tier,
        "consensus": consensus,
        "sources": rows,
    }
