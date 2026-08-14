from src.intelligence.multisource_starter_v112 import consensus

def main():
    a = consensus([
        {"source":"JP","probability":35,"available":True,"matched":True},
        {"source":"FF","probability":30,"available":True,"matched":True},
        {"source":"AF","probability":40,"available":True,"matched":True},
    ])
    assert a["starter_probability"] == 35.0
    assert a["consensus"] == "BENCH"
    assert a["confidence_tier"] == "HIGH"

    b = consensus([
        {"source":"JP","probability":88,"available":True,"matched":True},
        {"source":"FF","probability":30,"available":True,"matched":True},
        {"source":"AF","probability":40,"available":True,"matched":True},
    ])
    assert b["consensus"] == "BENCH"
    assert b["confidence_tier"] == "LOW_CONFLICT"

    c = consensus([
        {"source":"JP","probability":88,"available":True,"matched":True},
    ])
    assert c["source_coverage"] == 1
    assert c["confidence_tier"] == "LOW"

    print("V11.2 MULTISOURCE CONSENSUS: 3/3 OK")

if __name__ == "__main__":
    main()
