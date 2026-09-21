"""
Que interruptores declara ENCENDIDOS el workflow, y cuales de
esos no han pasado el paso 0.

POR QUE ESTO EXISTE (21/09/2026)

    Hasta hoy, la unica cosa que impedia encender un interruptor
    sin comprobarlo antes era
    `test_ninguna_guardia_depende_del_entorno_v1`: la verja
    entera, otra vez, con los 21 interruptores puestos, en CADA
    vuelta.

    Medido el 21/09 en el portatil del dueño, sobre las 171
    guardias de esa lista:

        la verja entera                 453,4 s
        de eso, esa guardia sola        229,8 s   (50,7 %)

    La mitad del reloj de la verja, cada hora, para proteger de
    algo que pasa una vez por semana.

    Y ademas protegia MENOS de lo que parecia. La verja corre
    DENTRO del job, con el `env` de produccion puesto: un
    interruptor que YA esta en el YAML y rompe guardias las
    rompe en la corrida normal. Eso es exactamente lo que se vio
    el 20/09 —«102/167 FALLA test_la_lista_de_objetivos_v1»— y
    lo cazo la verja de siempre.

    Lo unico que aquella guardia añadia era el aviso ANTICIPADO
    sobre los interruptores que TODAVIA NO estan en el YAML. Eso
    es una comprobacion previa al despegue.

LA REGLA QUE LA SUSTITUYE

    El paso 0 se corre a mano y DEJA CONSTANCIA en
    `config/paso_0.json`. Si el workflow enciende un interruptor
    que no esta en esa constancia, la verja se pone roja y dice
    cual y que mandato correr.

    No hace falta que nadie se acuerde: lo dispara el propio
    fichero que se cambia.

LO QUE ESTE MODULO NO HACE

    No abre disco, no sale a la red, no mira el reloj y no lee
    `os.environ`. Se le pasa el TEXTO del YAML y el registro ya
    leido. Quien toca disco es quien lo llama.

    Leer `os.environ` aqui seria leer estado de produccion
    (doctrina 104), que es la cosa concreta que esta familia de
    comprobaciones existe para prohibir.
"""

from __future__ import annotations

import re


# Un interruptor de esta casa. El prefijo no es decorativo: es
# lo que `scripts/los_interruptores.py` usa para censarlos.
PREFIJO = "BORDALAS_"


# `BORDALAS_ALGO: "1"` con cualquier sangria. El valor se
# captura entero y se juzga aparte.
LINEA = re.compile(
    r"^(?P<sangria>\s*)(?P<nombre>" + PREFIJO + r"[A-Z0-9_]+)\s*:\s*(?P<valor>.*?)\s*$"
)


# Lo que cuenta como "encendido". Es la misma familia de valores
# que aceptan los lectores del codigo -`{"1","true","si","yes"}`-
# mas `on`, que YAML tambien entiende como verdadero.
ENCENDIDO = frozenset({"1", "true", "si", "sí", "yes", "on"})


def _limpio(valor: str) -> str:
    """El valor sin comillas, sin comentario de linea y en minusculas."""

    texto = str(valor or "").strip()

    # `BORDALAS_X: "1"   # un motivo` -> `"1"`
    if "#" in texto:
        texto = texto.split("#", 1)[0].strip()

    if len(texto) >= 2 and texto[0] == texto[-1] and texto[0] in "\"'":
        texto = texto[1:-1].strip()

    return texto.lower()


def interruptores_encendidos_en(texto_yaml: str | None) -> set:
    """
    Los `BORDALAS_*` que ese texto declara ENCENDIDOS.

    Lo que queda fuera, y por que:

        · Una linea comentada. Un interruptor apagado con `#`
          delante esta apagado; contarlo seria pedir una prueba
          para algo que no corre.

        · `BORDALAS_BID_SALT: ${{ secrets.BORDALAS_BID_SALT }}`.
          Eso no es un interruptor de comportamiento, es un
          secreto, y su valor no es un literal encendido.

        · `BORDALAS_X: "0"` o `""`. Apagado es apagado.

    Nunca lanza: sin texto, el conjunto vacio.
    """

    encendidos = set()

    try:
        for linea in str(texto_yaml or "").splitlines():

            desnuda = linea.strip()

            if not desnuda or desnuda.startswith("#"):
                continue

            casa = LINEA.match(linea)

            if not casa:
                continue

            if _limpio(casa.group("valor")) in ENCENDIDO:
                encendidos.add(casa.group("nombre"))

        return encendidos

    except Exception:                               # noqa: BLE001
        return encendidos


def los_que_faltan(encendidos, probados) -> list:
    """
    Los encendidos que NO constan como probados. Ordenados.

    Nunca lanza.
    """

    try:
        tiene = {str(x) for x in (probados or [])}

        return sorted(
            str(x) for x in (encendidos or []) if str(x) not in tiene
        )

    except Exception:                               # noqa: BLE001
        return []


def el_mandato(faltan) -> str:
    """Que hay que correr para arreglarlo. Una linea, un mandato."""

    nombres = ", ".join(sorted(faltan or [])) or "(ninguno)"

    return (
        f"Sin probar: {nombres}. Corre el paso 0 y sube su "
        f"registro EN EL MISMO COMMIT:  "
        f"python scripts/run_validation_gate.py --paso-0 "
        f"> paso0.txt 2>&1"
    )
