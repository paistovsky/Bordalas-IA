"""
El veredicto de la verja no lo decide el `env` del workflow.

LO QUE PASO (20/09/2026), Y COSTO DOS VUELTAS

    Se encendio `BORDALAS_OBJETIVOS_EL_CATALOGO: "1"` en el
    `env` de `.github/workflows/bordalas-live.yml`.

        102/167  FALLA test_la_lista_de_objetivos_v1
           -> "el interruptor esta encendido en el entorno de la
               verja: entonces esto no mide el comportamiento
               por defecto"

        exit 1 -> "Validate optimized production cycle" para el
                  job  ->  NO HUBO CICLO

    Doctrina 104: un interruptor encendido es estado de
    produccion, y una guardia no lee estado de produccion.

    Y NO ERA UNA. Midiendo la verja entera con los 21
    interruptores puestos salieron QUINCE guardias rojas, y dos
    de ellas se caian con el PRIMERO de la cola de encendido.
    Encenderlo habria parado el ciclo otra vez.

QUE FORMA TIENE ESTA GUARDIA, Y POR QUE ESTA, CON SU MEDICION

    Habia dos candidatas:

        LA BARATA   estatica: toda guardia que NOMBRE un
                    `BORDALAS_*` tiene que ponerlo ella. 7,4 s.

        LA CARA     correr la verja entera otra vez, con todos
                    los interruptores puestos, y exigir el mismo
                    veredicto. 205 s.

    LA BARATA SE MIDIO Y NO VALE. Se le pasaron las CATORCE
    guardias que de verdad se caian, en su version de antes del
    arreglo, y las cazo CERO. El motivo es exacto y vale la pena
    escribirlo: casi ninguna NOMBRA el interruptor que la tumba
    -lo hereda a traves del motor que llama-, y las que si lo
    nombran lo ponen en ALGUNA de sus pruebas, asi que la regla
    las daba por buenas. `test_la_lista_de_objetivos_v1`, la que
    rompio el ciclo, salia limpia con la regla barata.

    Una guardia que no caza ninguno de los catorce casos reales
    no es una guardia barata: es una guardia que no esta.

    LA CARA CABE, MEDIDO:

        la verja sin esta guardia   205-220 s   (3 min 30 s)
        esta guardia, ella sola         275 s   (4 min 35 s)
        la verja CON ella               480 s   (8 min)
        tope del job                   2100 s   (35 min)
        vuelta de produccion       780-1140 s   (13-19 min)

    Se dobla larga la verja y sigue sobrando el 60 % del tope. Y
    lo que compra es lo unico que protege de verdad: que
    encender cualquiera de los ocho de la cola no pare el ciclo.

    SI ALGUN DIA ESTORBA, la misma proteccion esta en el PASO 0
    del protocolo -correr la verja con ESE interruptor puesto
    antes de tocar el YAML- y en
    `python -m scripts.los_interruptores --todos`. Quitar esto de
    la verja es una decision del dueño, no un descuido: costaria
    volver a fiarlo de que alguien se acuerde.

ESTORBO, Y SALIO DE LA VERJA (21/09/2026, dueño)

    ESTA GUARDIA YA NO CORRE EN CADA VUELTA. Es el paso 0:

        python scripts/run_validation_gate.py --paso-0

    LOS NUMEROS DE ARRIBA ERAN DE OTRA MAQUINA. «205-220 s la
    verja», «275 s esta guardia», «480 s con ella»: todos del
    portatil del dueño. En el runner de GitHub la verja entera
    tarda 1.312 s. Aplicar uno al otro es doctrina 90.

    Vuelto a medir el 21/09 en el portatil, n=1, sobre las 171
    guardias de la lista de ese dia:

        la verja entera                 453,4 s
        de eso, ESTA guardia sola       229,8 s   (50,7 %)

    Y lo que compraba por hora era menos de lo que parecia: la
    verja corre DENTRO del job, con el `env` de produccion
    puesto, asi que un interruptor YA encendido que rompa
    guardias las rompe en la corrida normal —es lo que paso el
    20/09—. Lo unico que esto añade es el aviso ANTICIPADO sobre
    los que TODAVIA NO estan en el YAML: una comprobacion previa
    al despegue, no una de cada hora.

    LO QUE IMPIDE QUE SE OLVIDE es
    `test_el_paso_0_no_se_olvida_v1`, que si esta en la verja:
    lee el `env` del YAML —versionado— y `config/paso_0.json`, y
    se pone roja si el workflow enciende algo sin constancia.

    Y UN AVISO PARA QUIEN LA CORRA: al poner los 21
    interruptores, la corrida de dentro deja
    `test_el_ciclo_publica_v1` construyendo el panel de verdad,
    que SALE A LA RED Y ESCRIBE en tres libros
    -`marcador.json`, `libro_de_publicacion.jsonl` y
    `bitacora_del_saldo.jsonl`-. Medido el 21/09. Correr el paso
    0 con el arbol sucio y subir sin mirar mete esas escrituras
    en un commit.

COMO NO SE MUERDE LA COLA

    La corrida de dentro va con `--solo`, con la lista de la
    verja MENOS esta guardia. Y con `VERJA_ANIDADA=1`, que le
    dice al corredor que no apunte el veredicto: si no, el
    mensaje del commit contaria la corrida de dentro.

DOCTRINA 24

    Si no encuentra ni un interruptor que poner, FALLA. Correr
    la verja con un entorno vacio seria correrla dos veces igual
    y salir en verde sin haber comprobado nada.

REGLA 23

    Lee el codigo del propio repositorio, que esta versionado.
    Ni `data/`, ni `diagnostico/`, ni la red, ni el reloj.
"""

from __future__ import annotations

import os
import subprocess
import sys

from pathlib import Path


RAIZ = Path(__file__).resolve().parents[2]

if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))


from scripts.los_interruptores import (           # noqa: E402
    ficheros,
    inventario,
    lectores,
)

from scripts.run_validation_gate import (         # noqa: E402
    EL_PASO_0,
    TESTS,
)


YO = "src.analysis.test_ninguna_guardia_depende_del_entorno_v1"


def _entorno(puestos: bool) -> dict:
    """Una copia del entorno con TODOS los interruptores puestos o fuera."""

    salida = dict(os.environ)

    for nombre in inventario():

        if puestos:
            salida[nombre] = "1"
        else:
            salida.pop(nombre, None)

    # La corrida de dentro no apunta el veredicto del commit.
    salida["VERJA_ANIDADA"] = "1"

    return salida


# EL GUARDIAN DEL PASO 0 NO ENTRA EN LA CORRIDA DE DENTRO
# (21/09/2026)
#
#     `test_el_paso_0_no_se_olvida_v1` se pone roja mientras el
#     YAML encienda algo que no conste en `config/paso_0.json`. Y
#     ese registro lo escribe EL PASO 0 AL PASAR.
#
#     Si entrase en la corrida de dentro, el paso 0 no podria
#     pasar nunca la primera vez: estaria esperando un registro
#     que solo existe si el paso 0 pasa. La pescadilla completa.
#
#     Dejarla fuera no abre ningun agujero: esa guardia NO LEE
#     `os.environ` —lee el YAML y el registro, los dos
#     versionados—, asi que ningun interruptor puesto puede
#     cambiar su veredicto. Lo comprueba ella misma, en
#     `test_ningun_interruptor_se_lee_al_importarse`, que barre
#     todos los ficheros que no son guardias.
EL_GUARDIAN = "src.analysis.test_el_paso_0_no_se_olvida_v1"


def _corre_la_verja(entorno: dict) -> tuple[int, str]:
    """La verja entera menos esta guardia. (codigo, ultima linea)."""

    otras = [
        modulo
        for modulo in TESTS
        if modulo not in (YO, EL_GUARDIAN)
    ]

    # EL PASO 0 ESTABA VACIO (26/09/2026)
    #
    #     Desde que la verja pone ella el entorno de produccion
    #     (22/09), QUITA todo `BORDALAS_*` que el YAML no enciende:
    #     "gana el YAML, se quita". Asi que "todos puestos" llegaba a
    #     las guardias como "solo los de produccion", y el paso 0
    #     decia PASADO sin haber probado ninguno de los demas.
    #
    #     Se vio el 26/09: `test_acquisition_wiring_v1` caia con
    #     `BORDALAS_EL_PRECIO_NO_SE_PIERDE` puesto a mano y el paso 0
    #     salia verde. Ahora los encendidos se le pasan a la verja por
    #     `--con`, que es la forma de decirle "estos tambien".
    encendidos = [
        nombre
        for nombre in inventario()
        if str(entorno.get(nombre, "")).strip() == "1"
    ]

    proceso = subprocess.run(
        [
            sys.executable,
            "scripts/run_validation_gate.py",
            *(["--con", *encendidos] if encendidos else []),
            "--solo",
            *otras,
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=entorno,
        cwd=str(RAIZ),
    )

    rojas = sorted(
        linea.strip(" -")
        for linea in (proceso.stdout or "").splitlines()
        if linea.strip().startswith("- src.")
    )

    return proceso.returncode, ", ".join(rojas)


# ============================================================
# 1. NADA PASA CON LAS MANOS VACIAS
# ============================================================


def test_sin_interruptores_no_se_comprueba_nada() -> None:

    conocidos = inventario()

    assert conocidos, (
        "no se ha encontrado ni un BORDALAS_* en todo el "
        "repositorio: correr la verja dos veces con el mismo "
        "entorno no comprueba nada"
    )

    puestos = _entorno(True)

    encendidos = [n for n in conocidos if puestos.get(n) == "1"]

    assert len(encendidos) == len(conocidos), (
        f"solo se han podido poner {len(encendidos)} de "
        f"{len(conocidos)} interruptores"
    )

    # DONDE TIENE QUE ESTAR, DESDE EL 21/09/2026
    #
    #     Antes se exigia `YO in TESTS`: la corrida de dentro se
    #     saltaba esta guardia para no llamarse a si misma sin
    #     parar. Ahora esta fuera de `TESTS` —es el paso 0—, asi
    #     que la de dentro ya no la incluye y la recursion no
    #     puede darse.
    #
    #     Lo que si hay que seguir comprobando es que este en
    #     ALGUN sitio. Una guardia que no esta en ninguna lista
    #     no se corre nunca, y eso no se nota.
    assert YO in EL_PASO_0, (
        "esta guardia no esta en `EL_PASO_0`: entonces no la "
        "corre nadie, ni cada vuelta ni a mano"
    )

    assert YO not in TESTS, (
        "esta guardia ha vuelto a la verja: ahi corre la verja "
        "entera por dentro y se llamaria a si misma sin parar"
    )


# ============================================================
# 2. LA PRUEBA QUE DA NOMBRE AL FICHERO
# ============================================================


def test_ninguna_guardia_depende_del_entorno() -> None:
    """
    Con los 21 interruptores puestos, la verja da el mismo
    veredicto que sin ninguno.
    """

    codigo, rojas = _corre_la_verja(_entorno(True))

    assert codigo == 0, (
        "con TODOS los interruptores puestos la verja se cae, "
        "asi que encender cualquiera de ellos puede parar el "
        "ciclo — que es lo que paso la noche del 20/09. Rojas: "
        + (rojas or "(no se pudo leer cuales)")
    )


# ============================================================
# 3. LA CONDICION SIN LA CUAL LO DE ARRIBA NO VALDRIA
# ============================================================


def test_ningun_interruptor_se_lee_al_importarse() -> None:
    """
    Apagar un interruptor dentro de una prueba solo sirve si el
    lector SIGUE al entorno.

    Si alguien moviera un `os.environ.get(...)` al cuerpo de un
    modulo, el valor quedaria congelado con el que arranco el
    proceso: la prueba lo apagaria y el motor seguiria viendolo
    puesto.
    """

    from scripts.los_interruptores import es_guardia

    tardios = []

    for camino in ficheros():

        if es_guardia(camino):
            continue

        for nombre, cuando in lectores(camino).items():

            if cuando == "AL_IMPORTARSE":
                tardios.append(
                    (camino.relative_to(RAIZ).as_posix(), nombre)
                )

    assert not tardios, (
        "estos interruptores se leen AL IMPORTARSE el modulo, "
        "asi que apagarlos dentro de una prueba no sirve de "
        "nada -> "
        + "; ".join(
            f"{nombre} en {fichero}"
            for fichero, nombre in sorted(tardios)
        )
    )


def main() -> int:

    pruebas = [
        test_sin_interruptores_no_se_comprueba_nada,
        test_ninguna_guardia_depende_del_entorno,
        test_ningun_interruptor_se_lee_al_importarse,
    ]

    fallos = 0

    for prueba in pruebas:

        try:
            prueba()
            print(f"OK   {prueba.__name__}")

        except AssertionError as error:
            fallos += 1
            print(f"FALLA {prueba.__name__}: {error}")

    print("=" * 60)
    print(
        f"NINGUNA GUARDIA DEPENDE DEL ENTORNO V1: "
        f"{len(pruebas) - fallos}/{len(pruebas)} OK"
    )
    print("=" * 60)

    return 1 if fallos else 0


if __name__ == "__main__":
    raise SystemExit(main())
