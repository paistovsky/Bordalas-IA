import json

from src.biwenger.client import BiwengerClient


def main() -> None:
    print()
    print("=" * 80)
    print("          BORDALÁS IA - LINEUP STATE INSPECTOR")
    print("=" * 80)

    client = BiwengerClient()

    print()
    print("Iniciando sesión...")

    client.login()
    client.select_league()

    print("Sesión correcta.")

    print()
    print("Consultando alineación actual...")

    response = client.session.get(
        f"{client.BASE_URL}/user",
        params={
            "fields": "*,lineup(date)",
        },
        timeout=30,
    )

    print()
    print(
        f"HTTP: {response.status_code}"
    )

    response.raise_for_status()

    data = response.json()

    user_data = data.get(
        "data",
        {},
    )

    # ==================================================
    # CLAVES GENERALES
    # ==================================================

    print()
    print("=" * 80)
    print("CLAVES DEL USUARIO")
    print("=" * 80)
    print()

    for key in user_data.keys():
        print(
            f"- {key}"
        )

    # ==================================================
    # LINEUP
    # ==================================================

    lineup = user_data.get(
        "lineup"
    )

    print()
    print("=" * 80)
    print("LINEUP ACTUAL")
    print("=" * 80)

    print()

    if lineup is None:
        print(
            "No se ha encontrado el campo lineup."
        )

    else:
        print(
            json.dumps(
                lineup,
                ensure_ascii=False,
                indent=2,
            )
        )

    # ==================================================
    # POSIBLES CAMPOS RELACIONADOS
    # ==================================================

    print()
    print("=" * 80)
    print("CAMPOS RELACIONADOS")
    print("=" * 80)

    interesting_words = (
        "lineup",
        "captain",
        "striker",
        "formation",
        "reserve",
    )

    found = False

    for key, value in user_data.items():

        key_lower = (
            str(key).lower()
        )

        if not any(
            word in key_lower
            for word in interesting_words
        ):
            continue

        found = True

        print()
        print(
            f"{key}:"
        )

        print(
            json.dumps(
                value,
                ensure_ascii=False,
                indent=2,
            )
        )

    if not found:
        print()
        print(
            "No se encontraron otros "
            "campos relacionados."
        )

    print()
    print("=" * 80)
    print("INSPECCIÓN TERMINADA")
    print("=" * 80)
    print()


if __name__ == "__main__":
    main()