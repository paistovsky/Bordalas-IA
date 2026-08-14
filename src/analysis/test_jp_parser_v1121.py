
from bs4 import BeautifulSoup

from src.intelligence.jornada_perfecta_provider import (
    build_signals_from_pitch,
)


def make_pitch(starters, alternatives):
    html = ['<div class="campo-futbol">']

    for index, name in enumerate(starters):
        slug = f"starter-{index}"
        html.append(
            f'<a class="player" href="/jugador/{slug}"></a>'
        )
        html.append(
            f'<a href="/jugador/{slug}">{name}</a>'
        )

    for index, item in enumerate(alternatives):
        name, probability = item
        slug = f"alternative-{index}"
        html.append(
            f'<a class="player" href="/jugador/{slug}">{probability}</a>'
        )
        html.append(
            f'<a href="/jugador/{slug}">{name}</a>'
        )

    html.append("</div>")

    soup = BeautifulSoup(
        "".join(html),
        "html.parser",
    )

    return soup.find(
        "div",
        class_="campo-futbol",
    )


def main():
    pitch = make_pitch(
        [f"Titular {i}" for i in range(11)],
        [("Fidalgo", 35)],
    )

    signals = build_signals_from_pitch(
        pitch,
        "Betis",
        "https://example.test",
    )

    titular = [
        item
        for item in signals
        if item["status"] == "TITULAR"
    ]

    fidalgo = next(
        item
        for item in signals
        if item["name"] == "Fidalgo"
    )

    assert len(titular) == 11
    assert fidalgo["status"] == "SUPLENTE"
    assert fidalgo["jp_probability"] == 35

    ambiguous = make_pitch(
        [f"Jugador {i}" for i in range(12)],
        [],
    )

    ambiguous_signals = build_signals_from_pitch(
        ambiguous,
        "Betis",
        "https://example.test",
    )

    assert all(
        item["status"] == "UNKNOWN"
        for item in ambiguous_signals
    )

    print("JP PARSER V11.2.1: 2/2 OK")


if __name__ == "__main__":
    main()
