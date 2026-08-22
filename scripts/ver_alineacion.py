"""
Que forma tiene la alineacion que devuelve Biwenger.

POR QUE EXISTE (22/08/2026)

    Pepe escribe el once con `PUT /user?fields=*,lineup(date)`, y
    desde hoy lo lee del mismo sitio. Pero al leerlo, la lista de
    jugadores no venia como se esperaba y el lector se quedaba en
    cero: el cartel decia "No hay ningun XI puesto en Biwenger"
    con el XI puesto.

    Se puede seguir adivinando el formato o se puede mirar. Esto
    mira.

QUE HACE

    Pide `/user` con varias formas del parametro `fields` y
    enseña la ESTRUCTURA de lo que vuelve: que claves hay, de que
    tipo es cada una, y como es el primer elemento de la lista de
    jugadores.

QUE NO HACE

    No enseña credenciales ni escribe nada. Solo lee.

COMO SE USA

    python -m scripts.ver_alineacion
"""

from __future__ import annotations

import json

from src.biwenger.client import BiwengerClient


VARIANTES = [
    "*,lineup(*,players(*))",
    "*,lineup(*)",
    "lineup(*)",
    "*",
]


def describir(valor, profundidad=0, max_profundidad=3):
    """La forma, no el contenido."""

    sangria = "  " * (profundidad + 1)

    if profundidad > max_profundidad:
        return f"{type(valor).__name__}"

    if isinstance(valor, dict):
        lineas = [f"{type(valor).__name__} con {len(valor)} claves"]
        for clave, dentro in list(valor.items())[:12]:
            lineas.append(
                f"{sangria}{clave}: "
                f"{describir(dentro, profundidad + 1, max_profundidad)}"
            )
        return "\n".join(lineas)

    if isinstance(valor, list):
        if not valor:
            return "lista VACIA"
        return (
            f"lista de {len(valor)} -> primer elemento: "
            + describir(valor[0], profundidad + 1, max_profundidad)
        )

    if isinstance(valor, str):
        return f"str {valor[:40]!r}"

    return f"{type(valor).__name__} {valor}"


def buscar_lineup(datos):
    """El bloque `lineup`, este donde este."""

    if isinstance(datos, dict):

        if isinstance(datos.get("lineup"), dict):
            return datos["lineup"]

        for dentro in datos.values():
            encontrado = buscar_lineup(dentro)
            if encontrado is not None:
                return encontrado

    return None


def main():

    client = BiwengerClient()

    print("Iniciando sesión...")
    client.login()
    client.select_league()

    for fields in VARIANTES:

        print()
        print("=" * 62)
        print(f"fields = {fields}")
        print("=" * 62)

        try:
            respuesta = client.session.get(
                f"{client.BASE_URL}/user",
                params={"fields": fields},
            )

            print(f"  HTTP {respuesta.status_code}")

            if respuesta.status_code != 200:
                print(f"  {respuesta.text[:200]}")
                continue

            datos = respuesta.json()

        except Exception as error:
            print(f"  {type(error).__name__}: {error}")
            continue

        alineacion = buscar_lineup(datos)

        if alineacion is None:
            print("  No hay bloque `lineup` en la respuesta.")
            print("  Claves de primer nivel:",
                  list(datos.keys())[:12])
            if isinstance(datos.get("data"), dict):
                print("  Claves de data:",
                      list(datos["data"].keys())[:12])
            continue

        print("  BLOQUE lineup:")
        print("   ", describir(alineacion).replace("\n", "\n    "))

        # Lo unico que se imprime tal cual: los ids, que no son
        # un secreto y son justo lo que hay que ver.
        for clave in ("playersID", "players", "reservesID"):
            valor = alineacion.get(clave)
            if valor is None:
                continue
            print(f"    {clave} (crudo, primeros 3):")
            print("     ", json.dumps(valor[:3], ensure_ascii=False))


if __name__ == "__main__":
    main()
