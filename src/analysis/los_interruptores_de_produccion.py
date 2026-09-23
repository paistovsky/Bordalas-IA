"""
Con que interruptores corre CI, leidos del propio fichero que
los enciende.

LO QUE ROMPIO LA PRODUCCION DOS VECES EL MISMO DIA (22/09/2026)

    La corrida #1753 murio en la verja, en
    `test_el_corte_y_el_cupo_v1`, y en el portatil esa misma
    guardia estaba verde.

    No era casualidad y no era suerte: el workflow trae
    encendido `BORDALAS_REVENTA_SOLO_SI_JUEGA` y la verja local
    corria sin el. Son dos verjas distintas con el mismo nombre.

        Un verde en el portatil no es un verde de produccion.
        Doctrina 112.

    Reproducir CI costaba abrir el YAML, leer que hay puesto y
    escribirlo a mano:

        $env:BORDALAS_JORNADAS_POR_SU_FECHA="1"
        $env:BORDALAS_REVENTA_SOLO_SI_JUEGA="1"

    Un paso que se hace a mano es un paso que se olvida. Y el
    dia que se olvida, el verde miente.

QUE HACE ESTE MODULO

    Una cosa: decir QUE `BORDALAS_*` declara encendidos el
    workflow, y preparar el entorno con ellos puestos.

    Quien lo llama -la verja- no nombra el fichero: lo nombra
    aqui. Eso no es un rodeo, es la separacion que pidio
    `test_la_puerta_no_lee_el_workflow` el 19/09 y que sigue en
    pie:

        LA LISTA DE GUARDIAS no sale del workflow. Esa es la
        que se fue al sitio equivocado y volvio.

        LOS INTERRUPTORES DE PRODUCCION si salen del workflow,
        porque es el workflow quien los enciende: leerlos de
        otro sitio seria mantener una copia, y una copia se
        desincroniza el dia que importa.

    Son dos cosas distintas que se leian del mismo fichero. La
    guardia se ha estrechado para decir cual de las dos prohibe.

EL PARSER NO SE ESCRIBE OTRA VEZ

    `el_paso_0.interruptores_encendidos_en` ya contesta
    exactamente esta pregunta sobre un texto YAML, con sus
    exclusiones medidas: lineas comentadas, secretos
    -`${{ secrets.X }}` no es un literal encendido- y `"0"`.
    Se importa (doctrina 84).

    Lo unico que este modulo añade es el DISCO: abrir el
    fichero y decir que hacer si no se puede.

SI NO SE PUEDE LEER, NO HAY VERDE

    Una verja que no sabe con que interruptores corre no puede
    afirmar que produccion esta bien. Devuelve `ok: False` con
    el motivo, y quien lo llama sale distinto de cero.
    Doctrina 91.

GANA EL YAML

    Si el entorno de quien lanza la verja dice una cosa y el
    YAML otra, manda el YAML y se avisa. Un `BORDALAS_*` suelto
    en la consola no puede cambiar en silencio lo que la verja
    esta probando -eso es justo el fallo de hoy, al reves-.

NO MIRA EL RELOJ NI SALE A LA RED

    Abre un fichero de texto del repositorio y devuelve forma
    fija. Nunca lanza.
"""

from __future__ import annotations

from pathlib import Path

from src.analysis.el_paso_0 import (                 # noqa: E402
    PREFIJO,
    interruptores_encendidos_en,
)


RAIZ = Path(__file__).resolve().parents[2]


# El fichero que enciende produccion. Se nombra AQUI y en ningun
# otro sitio del camino de la verja.
WORKFLOW = RAIZ / ".github" / "workflows" / "bordalas-live.yml"


# El unico `BORDALAS_*` que la verja se pone ella misma y que por
# tanto no es una contradiccion con el YAML: el vigilante de
# `data/`, que es herramienta del corredor, no comportamiento del
# bot.
DE_LA_PROPIA_VERJA = frozenset({"BORDALAS_VIGILA_DATA"})


def los_de_produccion(ruta=None) -> dict:
    """
    Los `BORDALAS_*` que el workflow declara encendidos.

    Forma fija:

        ok              si se pudo leer el fichero
        interruptores   lista ordenada de nombres
        ruta            que fichero se leyo
        reason          por que, siempre, tanto en verde como
                        en rojo

    Nunca lanza.
    """

    destino = Path(ruta) if ruta else WORKFLOW

    salida = {
        "ok": False,
        "interruptores": [],
        "ruta": str(destino),
        "reason": None,
    }

    try:
        texto = destino.read_text(encoding="utf-8")

    except Exception as error:                      # noqa: BLE001
        # NO SE PERDONA Y NO SE ADIVINA.
        #
        #     Seguir con el entorno de quien lanza seria volver
        #     al fallo de hoy sin avisar. Doctrina 91: un rojo
        #     que puede significar cualquier cosa vale lo mismo
        #     que un verde.
        return {
            **salida,
            "reason": (
                f"No se pudo leer el workflow ({destino}): "
                f"{type(error).__name__}: {error}. Sin saber con "
                f"que interruptores corre produccion, esta verja "
                f"no puede dar verde."
            ),
        }

    encendidos = sorted(interruptores_encendidos_en(texto))

    return {
        **salida,
        "ok": True,
        "interruptores": encendidos,
        "reason": (
            f"{len(encendidos)} interruptores de produccion en "
            f"{destino.name}: "
            f"{', '.join(encendidos) or '(ninguno)'}"
        ),
    }


def el_entorno_de_produccion(entorno, interruptores) -> dict:
    """
    El entorno de quien lanza, con los interruptores del YAML
    puestos y los que sobran quitados.

    Forma fija:

        entorno           el diccionario listo para el subproceso
        puestos           los que se encendieron aqui
        ya_estaban        los que el entorno ya traia bien
        quitados          los que el entorno traia y el YAML no
        avisos            una linea por cada contradiccion

    Nunca lanza. No lee `os.environ`: se le pasa.
    """

    salida = {
        "entorno": dict(entorno or {}),
        "puestos": [],
        "ya_estaban": [],
        "quitados": [],
        "avisos": [],
    }

    try:
        manda = {str(x) for x in (interruptores or [])}

        nuevo = dict(entorno or {})

        # 1. LO QUE EL YAML ENCIENDE, ENCENDIDO.
        #
        #     Y si el entorno lo traia APAGADO a proposito, eso
        #     es la contradiccion de verdad: alguien quiso correr
        #     sin el y CI corre con el. Gana el YAML y se dice.
        ENCENDIDO = {"1", "true", "si", "sí", "yes", "on"}

        for nombre in sorted(manda):

            tenia = str(nuevo.get(nombre, "")).strip()

            if tenia.lower() in ENCENDIDO:
                salida["ya_estaban"].append(nombre)

            else:
                salida["puestos"].append(nombre)

                if tenia:
                    salida["avisos"].append(
                        f"AVISO: {nombre} estaba en el entorno "
                        f"como \"{tenia}\" y el workflow lo "
                        f"enciende: gana el YAML, se pone a 1."
                    )

            nuevo[nombre] = "1"

        # 2. LO QUE EL ENTORNO TRAE Y EL YAML NO, FUERA.
        #
        #     Si no, la verja depende de que hubiera en la
        #     consola: dos corridas del mismo arbol podrian dar
        #     distinto y ninguna de las dos seria la de CI.
        sobrantes = sorted(
            nombre
            for nombre in list(nuevo)
            if str(nombre).startswith(PREFIJO)
            and nombre not in manda
            and nombre not in DE_LA_PROPIA_VERJA
            and str(nuevo.get(nombre, "")).strip()
        )

        for nombre in sobrantes:
            nuevo.pop(nombre, None)
            salida["quitados"].append(nombre)
            salida["avisos"].append(
                f"AVISO: {nombre} estaba en el entorno y el "
                f"workflow no lo enciende: gana el YAML, se quita."
            )

        salida["entorno"] = nuevo

        return salida

    except Exception as error:                      # noqa: BLE001
        return {
            **salida,
            "avisos": [
                f"AVISO: no se pudo preparar el entorno de "
                f"produccion: {type(error).__name__}: {error}"
            ],
        }


def la_cabecera(interruptores) -> str:
    """La linea que la verja imprime. Una frase, con su numero."""

    nombres = sorted(str(x) for x in (interruptores or []))

    return (
        f"corriendo con {len(nombres)} interruptores de "
        f"produccion: {', '.join(nombres) or '(ninguno)'}"
    )
