from src.intelligence.starter_intelligence_v11 import build_starter_signal

def main():
    a = build_starter_signal({"status":"TITULAR","confidence":88})
    assert a["source_coverage"] == 1
    assert a["confidence_tier"] == "LOW"

    b = build_starter_signal({"sources":{
        "JORNADA_PERFECTA":{"status":"SUPLENTE","probability":35},
        "ANALITICA_FANTASY":{"status":"SUPLENTE","probability":40},
    }})
    assert b["starter_probability"] == 37.5
    assert b["consensus"] == "BENCH"

    c = build_starter_signal({"sources":{
        "JORNADA_PERFECTA":{"status":"TITULAR","probability":96},
        "FUTBOLFANTASY":{"status":"TITULAR","probability":92},
        "ANALITICA_FANTASY":{"status":"TITULAR","probability":94},
    }})
    assert c["starter_probability"] == 94.0
    assert c["confidence_tier"] == "HIGH"

    print("V11.1 STARTER INTELLIGENCE: 3/3 OK")

if __name__ == "__main__":
    main()
