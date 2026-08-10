from src.intelligence.injuries import (
    find_laliga,
    search_spanish_leagues,
)


print()
print("=" * 80)
print("        BORDALÁS IA - API FOOTBALL DIAGNÓSTICO")
print("=" * 80)
print()

print("Consultando competiciones españolas...")

data = search_spanish_leagues()

print()
print("Errores API:")
print(data.get("errors"))

print()
print("Resultados:")
print(data.get("results"))

print()
print("Competiciones encontradas:")
print("-" * 80)

for item in data.get("response", []):
    league = item.get("league", {})
    seasons = item.get("seasons", [])

    print()
    print(
        f"ID: {league.get('id')} | "
        f"{league.get('name')}"
    )

    available_seasons = [
        season.get("year")
        for season in seasons
    ]

    print(
        f"Temporadas disponibles: "
        f"{available_seasons}"
    )

    current = [
        season
        for season in seasons
        if season.get("current")
    ]

    if current:
        print(
            "Temporada actual marcada por API:",
            current[0].get("year"),
        )


print()
print("=" * 80)
print("BUSCANDO LALIGA")
print("=" * 80)

laliga = find_laliga()

if laliga is None:
    print("No se ha identificado LaLiga.")
else:
    print(
        "Competición:",
        laliga["league"]["name"],
    )

    print(
        "ID:",
        laliga["league"]["id"],
    )

    print()
    print("Temporadas y cobertura:")

    for season in laliga.get(
        "seasons",
        [],
    ):
        print()
        print(
            f"Temporada: {season.get('year')}"
        )

        print(
            f"Actual: {season.get('current')}"
        )

        print(
            "Lesiones:",
            season
            .get("coverage", {})
            .get("injuries"),
        )