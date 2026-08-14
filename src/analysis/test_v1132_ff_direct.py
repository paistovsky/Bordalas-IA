
from bs4 import BeautifulSoup

from src.intelligence.multisource_starter_v1124 import (
    parse_ff_team_page,
)

SNAPSHOT = {
    "catalog": {
        "data": {
            "players": {}
        }
    }
}

PLAYERS = [
    {
        "id": 1,
        "name": "Javi Hernández",
    },
    {
        "id": 2,
        "name": "Mangala",
    },
]


def main():

    html = """
    <html>
      <body>
        <h2>Posible alineación</h2>
        <table>
          <thead>
            <tr>
              <th>Jugador</th>
              <th>Prob.</th>
              <th>Forma</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td><a href="/jugadores/javi-hernandez">Javi Hernández</a></td>
              <td>35%</td>
              <td>Bien</td>
            </tr>
            <tr>
              <td><a href="/jugadores/mangala">Mangala</a></td>
              <td>75%</td>
              <td>Bien</td>
            </tr>
          </tbody>
        </table>
      </body>
    </html>
    """

    records = parse_ff_team_page(
        html,
        PLAYERS,
        SNAPSHOT,
    )

    by_id = {
        int(
            item[
                "player"
            ][
                "id"
            ]
        ):
            item
        for item in records
    }

    assert (
        by_id[
            1
        ][
            "probability"
        ]
        == 35.0
    )

    assert (
        by_id[
            2
        ][
            "probability"
        ]
        == 75.0
    )

    assert (
        by_id[
            1
        ][
            "method"
        ]
        ==
        "TEAM_TABLE_PROB_COLUMN"
    )

    print(
        "V11.3.2 FF DIRECT: 3/3 OK"
    )


if __name__ == "__main__":
    main()
