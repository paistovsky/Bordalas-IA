"""
Ningun interruptor se enciende en el YAML sin haber pasado el
paso 0.

QUE SUSTITUYE, Y CON QUE NUMERO

    `test_ninguna_guardia_depende_del_entorno_v1` sale de la
    verja el 21/09/2026. Medido ese dia en el portatil del dueño,
    sobre las 171 guardias, n=1:

        la verja entera                 453,4 s
        de eso, esa guardia sola        229,8 s   (50,7 %)

    Y el numero que la defendia -«275 s ella sola, 480 s la verja
    con ella»- era del portatil, aplicado al runner de GitHub,
    donde la verja tarda 1.312 s. Doctrina 90.

    La guardia no se borra: se vuelve EL PASO 0, se corre a mano
    antes de tocar el `env` del workflow, y deja constancia en
    `config/paso_0.json`.

    ESTA GUARDIA ES LO QUE HACE QUE NO SE PUEDA OLVIDAR. Si el
    YAML enciende algo que no consta en esa constancia, se pone
    roja y dice cual y que correr.

LO QUE CUESTA, Y LO QUE NO EVITA

    Cuesta lo que cuesta leer dos ficheros pequeños: medido en
    la verja del 21/09, por debajo de 0,3 s.

    Y NO EVITA PERDER UNA VUELTA. Si el dueño cambia el YAML sin
    correr el paso 0, la verja se pone roja y el ciclo no
    arranca, igual que el 20/09. Lo que cambia es que en vez de
    quince guardias rojas por motivos que no se parecen entre si,
    sale UNA linea con el nombre del interruptor y el mandato que
    lo arregla. Se dice aqui porque la diferencia importa y no
    conviene venderla como mas de lo que es.

DOCTRINA 107: QUE CAZA UN CASO REAL

    `test_el_lector_caza_la_linea_del_20_09` le pasa el trozo
    EXACTO de YAML de aquella noche y exige que lo cace. Una
    comprobacion que no caza ningun caso real no es barata: es
    que no esta.

REGLA 23 Y DOCTRINA 24

    Lee dos ficheros del propio repositorio, los dos versionados:
    `.github/workflows/bordalas-live.yml` y `config/paso_0.json`.
    Ni `data/`, ni `diagnostico/`, ni la red, ni el reloj, ni
    `os.environ` —leer el entorno aqui seria leer estado de
    produccion, que es lo que esta familia existe para prohibir-.

    Y no pasa con las manos vacias: las tres primeras pruebas
    corren siempre, con fichas escritas aqui, haya o no haya
    interruptores encendidos.
"""

from __future__ import annotations

import json
import sys

from pathlib import Path


RAIZ = Path(__file__).resolve().parents[2]

if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))


from src.analysis.el_paso_0 import (               # noqa: E402
    PREFIJO,
    el_mandato,
    interruptores_encendidos_en,
    los_que_faltan,
)


WORKFLOW = RAIZ / ".github" / "workflows" / "bordalas-live.yml"

REGISTRO = RAIZ / "config" / "paso_0.json"


# El trozo de `env:` de la noche del 20/09/2026, tal cual: el
# interruptor que tumbo el ciclo, el secreto que NO es un
# interruptor, y una linea comentada.
EL_YAML_DEL_20_09 = """
    env:
      TZ: Europe/Madrid
      BIWENGER_USERNAME: ${{ secrets.BIWENGER_USERNAME }}
      BORDALAS_BID_SALT: ${{ secrets.BORDALAS_BID_SALT }}

      # BORDALAS_CESTA_SOLO_EL_SUELO: "1"
      BORDALAS_OBJETIVOS_EL_CATALOGO: "1"
"""


# ============================================================
# 1. EL LECTOR, CONTRA EL CASO DE VERDAD
# ============================================================


def test_el_lector_caza_la_linea_del_20_09() -> None:

    encendidos = interruptores_encendidos_en(EL_YAML_DEL_20_09)

    assert "BORDALAS_OBJETIVOS_EL_CATALOGO" in encendidos, (
        "el lector no ve el interruptor que tumbo el ciclo el "
        "20/09: entonces esta guardia no caza el unico caso "
        "real que hay, que es no estar"
    )

    assert "BORDALAS_BID_SALT" not in encendidos, (
        "ha contado un secreto como interruptor encendido: "
        "`${{ secrets.* }}` no es un literal encendido y pedir "
        "el paso 0 por el seria pedirlo para siempre"
    )

    assert "BORDALAS_CESTA_SOLO_EL_SUELO" not in encendidos, (
        "ha contado una linea COMENTADA como encendida: un "
        "interruptor apagado con `#` delante no corre"
    )

    assert len(encendidos) == 1, sorted(encendidos)


def test_apagado_es_apagado() -> None:
    """
    `"0"`, vacio y `false` no son encendidos.

    LOS NOMBRES DE MENTIRA SE ARMAN, NO SE ESCRIBEN

        `scripts/los_interruptores.py` saca el inventario de
        los literales del codigo, saltandose los docstrings.
        Escribir aqui un nombre de ejemplo a pelo mete SIETE
        interruptores inventados en el inventario, y el paso 0
        los pone en el entorno como si existieran. Comprobado
        el 21/09: el inventario paso de 21 a 28.

        Armandolos con `PREFIJO + "..."` la prueba hace lo
        mismo y el inventario no se entera.
    """

    uno = PREFIJO + "UNO"
    dos = PREFIJO + "DOS"
    tres = PREFIJO + "TRES"
    cuatro = PREFIJO + "CUATRO"
    cinco = PREFIJO + "CINCO"

    texto = (
        f'      {uno}: "0"\n'
        f'      {dos}: ""\n'
        f"      {tres}: false\n"
        f'      {cuatro}: "1"\n'
        f"      {cinco}: 1   # con motivo detras\n"
    )

    encendidos = interruptores_encendidos_en(texto)

    assert encendidos == {cuatro, cinco}, sorted(encendidos)


def test_lo_que_falta_se_dice_con_su_nombre() -> None:

    # Armados, no escritos: ver `test_apagado_es_apagado`.
    probado = PREFIJO + "PROBADO"
    pendiente = PREFIJO + "PENDIENTE"

    faltan = los_que_faltan({probado, pendiente}, [probado])

    assert faltan == [pendiente], faltan

    assert pendiente in el_mandato(faltan)
    assert "--paso-0" in el_mandato(faltan)

    # Y sin nada encendido no falta nada: el caso normal tiene
    # que ser capaz de salir en verde, o la guardia seria una
    # alarma permanente y se acabaria quitando.
    assert los_que_faltan(set(), []) == []


# ============================================================
# 2. EL YAML DE VERDAD, CONTRA EL REGISTRO DE VERDAD
# ============================================================


def _encendidos_de_produccion() -> set:

    assert WORKFLOW.exists(), (
        f"no esta el workflow en {WORKFLOW}: sin el no se sabe "
        f"que interruptores hay encendidos, y eso no es «no hay "
        f"ninguno»"
    )

    return interruptores_encendidos_en(
        WORKFLOW.read_text(encoding="utf-8")
    )


def _registro() -> dict:

    if not REGISTRO.exists():
        return {}

    try:
        datos = json.loads(REGISTRO.read_text(encoding="utf-8"))

    except Exception as error:                      # noqa: BLE001
        raise AssertionError(
            f"`{REGISTRO.name}` no se puede leer "
            f"({type(error).__name__}): un registro roto no es "
            f"un registro vacio, y tratarlo como vacio dejaria "
            f"pasar cualquier cosa"
        ) from None

    assert isinstance(datos, dict), type(datos)

    return datos


def test_el_registro_no_se_puede_inventar() -> None:
    """
    Lo apuntado tiene que ser una lista de interruptores QUE
    EXISTEN, con su fecha y la maquina donde se probo.

    Sin esto, «probados: ["todos"]» pasaria la guardia sin haber
    corrido nada.

    SIN REGISTRO TAMBIEN SE AFIRMA ALGO (doctrina 24)

        La primera version salia por un `return` desnudo cuando
        el fichero no estaba: verde sin haber mirado nada.
        `test_ninguna_pasa_con_las_manos_vacias_v1` lo cazo el
        mismo dia. Aqui no hay puerta de atras: las dos ramas
        afirman.
    """

    from scripts.los_interruptores import inventario

    conocidos = set(inventario())

    assert conocidos, (
        "no se ha encontrado ni un BORDALAS_* en el repositorio: "
        "sin inventario no se puede juzgar el registro"
    )

    datos = _registro()

    if not datos:
        # Lo que hay que afirmar sin registro es que entonces
        # NADA consta probado, y por tanto todo lo que el YAML
        # encienda sale en la lista de los que faltan.
        encendidos = _encendidos_de_produccion()

        assert los_que_faltan(encendidos, []) == sorted(
            encendidos
        ), (
            "sin `config/paso_0.json` hay interruptores "
            "encendidos que NO aparecen como pendientes: la "
            "cuenta de los que faltan esta rota"
        )

        print(
            f"     no hay registro del paso 0: los "
            f"{len(encendidos)} encendidos constan pendientes."
        )

    else:
        probados = datos.get("probados")

        assert isinstance(probados, list) and probados, (
            f"`probados` tiene que ser una lista con algo "
            f"dentro, y es {probados!r}"
        )

        inventados = sorted(set(probados) - conocidos)

        assert not inventados, (
            f"el registro dice haber probado interruptores que "
            f"no existen en el codigo: {inventados}. O son un "
            f"error de escritura, o el registro se escribio a "
            f"mano"
        )

        for campo in ("cuando", "maquina", "huella"):
            assert datos.get(campo), (
                f"al registro del paso 0 le falta `{campo}`: un "
                f"numero sin su plazo ni su maquina no se puede "
                f"volver a mirar"
            )

        print(
            f"     el registro apunta {len(probados)} "
            f"interruptores probados, todos conocidos."
        )


def test_todo_interruptor_encendido_ha_pasado_el_paso_0() -> None:

    encendidos = _encendidos_de_produccion()

    probados = (_registro() or {}).get("probados") or []

    faltan = los_que_faltan(encendidos, probados)

    assert not faltan, (
        "el workflow enciende interruptores que NO han pasado el "
        "paso 0. "
        + el_mandato(faltan)
    )

    print(
        f"     el workflow enciende {len(encendidos)} "
        f"interruptor(es); los "
        f"{len(encendidos)} constan probados."
    )


# ============================================================
# 3. Y QUE EL PASO 0 SIGA EXISTIENDO
# ============================================================


def test_el_paso_0_sigue_teniendo_a_quien_correr() -> None:
    """
    Si alguien vaciase `EL_PASO_0`, esta guardia seguiria en
    verde y la comprobacion cara habria desaparecido sin que
    nadie lo notase. Es el mismo fallo silencioso de siempre.
    """

    from scripts.run_validation_gate import EL_PASO_0, TESTS

    assert EL_PASO_0, (
        "`EL_PASO_0` esta vacia: la comprobacion cara ha "
        "desaparecido del proyecto sin dejar rastro"
    )

    for modulo in EL_PASO_0:

        camino = RAIZ / Path(modulo.replace(".", "/") + ".py")

        assert camino.exists(), (
            f"el paso 0 nombra `{modulo}` y ese fichero no "
            f"existe: el mandato fallaria el dia que se corra"
        )

        assert modulo not in TESTS, (
            f"`{modulo}` esta en las DOS listas: o se corre cada "
            f"vuelta o es el paso 0, no las dos cosas"
        )

    assert (
        "src.analysis.test_el_paso_0_no_se_olvida_v1" in TESTS
    ), (
        "esta guardia no esta en la verja: entonces no vigila "
        "nada, porque no se corre"
    )


def main() -> int:

    pruebas = [
        test_el_lector_caza_la_linea_del_20_09,
        test_apagado_es_apagado,
        test_lo_que_falta_se_dice_con_su_nombre,
        test_el_registro_no_se_puede_inventar,
        test_todo_interruptor_encendido_ha_pasado_el_paso_0,
        test_el_paso_0_sigue_teniendo_a_quien_correr,
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
        f"EL PASO 0 NO SE OLVIDA V1: "
        f"{len(pruebas) - fallos}/{len(pruebas)} OK"
    )
    print("=" * 60)

    return 1 if fallos else 0


if __name__ == "__main__":
    raise SystemExit(main())
