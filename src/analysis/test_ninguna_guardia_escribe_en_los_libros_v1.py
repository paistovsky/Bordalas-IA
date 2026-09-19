"""
Ninguna guardia escribe en los libros.

EL HECHO, CONFIRMADO Y NO SOSPECHADO

    19/09/2026. `data/autopilot/computer_offer_history.json`
    cambio de fecha a las 18:23:54, en mitad de un barrido de
    guardias. Una de ellas escribio en estado de produccion.

    Que el contenido acabara igual que en git es suerte, no
    diseno.

DOCTRINA 92: UNA GUARDIA QUE ESCRIBE DONDE MIRA ES UNA VUELTA MAS

    Deja de medir el sistema y pasa a moverlo. Y arrastra a las
    que vienen detras: si la primera escribe el historial, la
    segunda ya no lee lo mismo que habria leido sola. Eso
    convierte el resultado de la suite en algo que depende del
    ORDEN, y un resultado que depende del orden no es un
    resultado.

    Explica ademas lo que costo una tarde: una guardia dio rojo y
    luego verde con el arbol identico, y se le achaco al azar.

COMO SE COMPRUEBA

    Huella SHA-256 de cada fichero bajo `data/` antes y despues
    de correr la poblacion PURA -la que no lee produccion-. Si
    alguna huella cambia, sale con el nombre del fichero.

    Se corre cada guardia en su propio proceso y se comprueba
    DESPUES DE CADA UNA, para poder decir CUAL fue. Un barrido
    que solo mira al final dice que alguien escribio y no quien.

POR QUE SOLO LA POBLACION PURA

    Las 71 que leen produccion ya estan fuera de la cuenta por la
    doctrina 91, y se corren a mano. Meterlas aqui mezclaria las
    dos enfermedades.

LA GUARDIA MUERDE SI NO HAY FICHEROS BAJO `data/`

    Sin ficheros que vigilar, cualquier escritura pasaria
    desapercibida y esto seria verde por vacuidad. Por eso lo
    primero es exigir que haya libros que mirar.

USO

    Es LENTA a proposito: corre la poblacion pura entera. Se
    ejecuta a mano o en la verja, no en cada vuelta.

        python src/analysis/test_ninguna_guardia_escribe_en_los_libros_v1.py
        python ... --rapida     solo un subconjunto declarado

DE DONDE SALEN LOS NUMEROS

    Del arbol de ficheros y de las huellas, que son codigo y
    disco. No se sale a la red y no se mira el reloj. NO ESCRIBE
    NADA: solo lee huellas.
"""

import hashlib
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, ".")


RAIZ = Path(__file__).resolve().parents[2]

DATA = RAIZ / "data"

LEE_PRODUCCION = "get_latest_snapshot"

TIMEOUT = 120

ESTA_GUARDIA = Path(__file__).stem


fallos = []


def check(nombre, condicion, detalle=""):
    if condicion:
        print(f"  OK   {nombre}")
    else:
        print(f"  FALLA {nombre} {detalle}")
        fallos.append(nombre)


def huellas() -> dict:
    """SHA-256 de cada fichero bajo `data/`. Nunca lanza."""

    salida = {}

    if not DATA.exists():
        return salida

    for fichero in sorted(DATA.rglob("*")):

        if not fichero.is_file():
            continue

        try:
            salida[str(fichero.relative_to(RAIZ))] = (
                hashlib.sha256(
                    fichero.read_bytes()
                ).hexdigest()
            )

        except OSError:
            continue

    return salida


def poblacion_pura() -> list:
    """Las guardias que NO leen estado de produccion."""

    puras = []

    for fichero in sorted(RAIZ.rglob("src/**/test_*.py")):

        if "__pycache__" in fichero.parts:
            continue

        if fichero.stem == ESTA_GUARDIA:
            continue

        try:
            fuente = fichero.read_text(
                encoding="utf-8", errors="replace"
            )

        except OSError:
            continue

        # Esta otra nombra el string para poder buscarlo.
        if fichero.stem == (
            "test_ninguna_guardia_nueva_lee_produccion_v1"
        ):
            puras.append(fichero)
            continue

        if LEE_PRODUCCION not in fuente:
            puras.append(fichero)

    return puras


# ================================================================
# 0. HAY LIBROS QUE VIGILAR
# ================================================================

print()
print("0. Hay ficheros bajo `data/` que vigilar")

antes = huellas()

print(f"       ficheros bajo data/: {len(antes)}")

check(
    "hay ficheros bajo `data/`",
    len(antes) > 0,
    "<- sin libros que vigilar esto seria verde por vacuidad",
)

puras = poblacion_pura()

print(f"       poblacion pura: {len(puras)} guardias")

check(
    "hay poblacion pura que correr",
    len(puras) > 0,
    f"({len(puras)})",
)


# ================================================================
# 1. NINGUNA CAMBIA UNA HUELLA
# ================================================================

print()
print("1. Corriendo la poblacion pura, ninguna huella cambia")

rapida = "--rapida" in sys.argv

if rapida:
    puras = puras[:25]
    print(f"       --rapida: solo las {len(puras)} primeras")

culpables = []

previo = dict(antes)

for indice, fichero in enumerate(puras, 1):

    try:
        subprocess.run(
            [sys.executable, str(fichero)],
            cwd=str(RAIZ),
            capture_output=True,
            timeout=TIMEOUT,
        )

    except subprocess.TimeoutExpired:
        pass

    ahora = huellas()

    cambiados = [
        ruta
        for ruta, firma in ahora.items()
        if previo.get(ruta) != firma
    ]

    nuevos = [
        ruta for ruta in ahora if ruta not in previo
    ]

    borrados = [
        ruta for ruta in previo if ruta not in ahora
    ]

    if cambiados or nuevos or borrados:
        culpables.append({
            "guardia": fichero.stem,
            "cambiados": cambiados,
            "nuevos": nuevos,
            "borrados": borrados,
        })

        print(
            f"       [{indice}/{len(puras)}] {fichero.stem} "
            f"TOCO {cambiados + nuevos + borrados}"
        )

    previo = ahora

check(
    "ninguna guardia pura toca un fichero bajo `data/`",
    not culpables,
    f"<- {[c['guardia'] for c in culpables]}. Una guardia que "
    f"escribe donde mira deja de medir el sistema y pasa a "
    f"moverlo, y arrastra a las que vienen detras (doctrina 92).",
)

if culpables:
    print()
    print("       EL DETALLE:")
    for c in culpables:
        print(f"         {c['guardia']}")
        for ruta in c["cambiados"]:
            print(f"            cambio  {ruta}")
        for ruta in c["nuevos"]:
            print(f"            creo    {ruta}")
        for ruta in c["borrados"]:
            print(f"            borro   {ruta}")


# ================================================================
# RESULTADO
# ================================================================

print()
print("=" * 60)

if fallos:
    print(f"FALLOS: {len(fallos)}")
    for nombre in fallos:
        print(f"  - {nombre}")
    sys.exit(1)

print("TODO OK")
print("=" * 60)
