
from src.intelligence.jornada_perfecta_provider import (
    parse_player_profile_pronostico,
)

def main():
    cases = [
        ("Titular", "TITULAR"),
        ("Suplente", "SUPLENTE"),
        ("Duda", "DUDA"),
        ("No convocado", "NO_CONVOCADO"),
    ]

    for raw, expected in cases:
        result = parse_player_profile_pronostico(
            f"<div>Pronóstico: {raw}</div>"
        )
        assert result
        assert result["status"] == expected

    assert parse_player_profile_pronostico(
        "<div>Sin dato</div>"
    ) is None

    print("JP PROFILE V11.2.2C: 5/5 OK")

if __name__ == "__main__":
    main()
