
from src.intelligence.jornada_perfecta_provider import (
    strict_identity_similarity,
)

def main():
    assert strict_identity_similarity(
        "Alvaro",
        "Alvaro Fidalgo",
    ) == 0.0

    assert strict_identity_similarity(
        "Alvaro Garcia",
        "Alvaro Fidalgo",
    ) < 0.80

    assert strict_identity_similarity(
        "Olasagasti",
        "Jon Ander Olasagasti",
    ) >= 0.80

    assert strict_identity_similarity(
        "Rincon",
        "Hugo Rincon",
    ) >= 0.80

    assert strict_identity_similarity(
        "Alvaro Fidalgo",
        "Alvaro Fidalgo",
    ) == 1.0

    print("V11.2.3 JP IDENTITY MATCH: 5/5 OK")

if __name__ == "__main__":
    main()
