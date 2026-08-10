import inspect
import re
from pathlib import Path

import pybiwenger

from src.biwenger.client import BiwengerClient


def print_header(title: str) -> None:
    print()
    print("=" * 80)
    print(title)
    print("=" * 80)


def inspect_custom_client() -> None:
    print_header("CLIENTE BORDALÁS IA")

    print()
    print("Métodos públicos de BiwengerClient:")
    print()

    methods = [
        name
        for name in dir(BiwengerClient)
        if not name.startswith("_")
    ]

    for method in methods:
        print(f"- {method}")

    print()
    print("Código fuente:")
    print("-" * 80)

    try:
        print(
            inspect.getsource(
                BiwengerClient
            )
        )
    except Exception as error:
        print(
            f"No se pudo obtener source: "
            f"{type(error).__name__}: {error}"
        )


def inspect_pybiwenger_files() -> None:
    print_header(
        "BUSCANDO ESCRITURAS EN PYBIWENGER"
    )

    package_path = Path(
        pybiwenger.__path__[0]
    )

    print()
    print(
        f"Paquete: {package_path}"
    )

    patterns = [
        re.compile(
            r"requests\.(post|put|patch|delete)",
            re.IGNORECASE,
        ),
        re.compile(
            r"session\.(post|put|patch|delete)",
            re.IGNORECASE,
        ),
    ]

    found = []

    for file in package_path.rglob("*.py"):

        try:
            content = file.read_text(
                encoding="utf-8"
            )
        except UnicodeDecodeError:
            continue

        lines = content.splitlines()

        for number, line in enumerate(
            lines,
            start=1,
        ):

            if any(
                pattern.search(line)
                for pattern in patterns
            ):
                found.append(
                    (
                        file,
                        number,
                        line.strip(),
                    )
                )

    if not found:
        print()
        print(
            "No se han encontrado operaciones "
            "POST/PUT/PATCH/DELETE adicionales."
        )
        return

    print()

    for file, number, line in found:
        print(
            f"{file}:{number}"
        )
        print(
            f"    {line}"
        )


def inspect_urls() -> None:
    print_header(
        "ENDPOINTS INSTALADOS"
    )

    package_path = Path(
        pybiwenger.__path__[0]
    )

    urls_file = (
        package_path
        / "src"
        / "client"
        / "urls.py"
    )

    if not urls_file.exists():
        print(
            "No se encuentra urls.py"
        )
        return

    print()
    print(
        urls_file.read_text(
            encoding="utf-8"
        )
    )


def main() -> None:
    print_header(
        "BORDALÁS IA - WRITE CAPABILITY INSPECTOR"
    )

    print()
    print(
        "MODO SOLO LECTURA."
    )

    print(
        "Este script NO envía ninguna "
        "operación a Biwenger."
    )

    inspect_custom_client()
    inspect_pybiwenger_files()
    inspect_urls()

    print_header(
        "INSPECCIÓN TERMINADA"
    )


if __name__ == "__main__":
    main()