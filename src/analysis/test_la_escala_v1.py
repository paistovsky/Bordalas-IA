"""
Las guardias de LA ESCALA.

BLOQUE 0 — el once se anota con la jornada BUENA, y no se pierde.

    `round_id` es el round de Biwenger y `matchday` la jornada de
    LaLiga. Son dos fuentes distintas y nadie las cruzaba: el
    17/09 la foto traia `round_id: 5125` —la jornada 6 aplazada,
    ya jugada— mientras la ventana abierta era la de la jornada
    7.

    La linea se guarda con LAS DOS, porque perder la jornada es
    peor que una etiqueta dudosa y la jornada no vuelve.

NINGUNA GUARDIA LEE ESTADO DE PRODUCCION, SALE A LA RED, MIRA EL
RELOJ DEL SISTEMA NI ESCRIBE EN LOS LIBROS: escriben en un
directorio temporal propio, que se borra al salir. La hora entra
por la puerta (doctrina 50).

Y NINGUNA PASA CON LAS MANOS VACIAS (doctrina 24).
"""

from __future__ import annotations

import json
import sys
import tempfile

from datetime import datetime, timedelta
from pathlib import Path


RAIZ = Path(__file__).resolve().parents[2]

sys.path.insert(0, str(RAIZ))

from src.analysis.el_once_que_jugo import (          # noqa: E402
    SON_ONCE,
    anotar_el_once,
)


# La ventana de la jornada 7, tal y como la trae el calendario de
# LaLiga. Se copian como numeros: una guardia que abre el
# calendario de produccion deja de ser determinista.
PRIMER_PARTIDO = "2026-09-18T21:00:00+02:00"

VENTANA_DESDE = "2026-09-18T19:30:00+02:00"

# La vuelta del ciclo que cae dentro de la ventana.
LA_VUELTA = "2026-09-18T20:07:00+02:00"

# El round de Biwenger que traia la foto: la jornada 6 aplazada.
ROUND_RETRASADO = 5125

# Y la jornada de LaLiga a la que pertenece la ventana.
JORNADA = 7


def _once(cuantos=SON_ONCE) -> dict:
    """Un once de juguete. Los ids empiezan en 1: el 0 es falsy."""

    return {
        "formation": "4-4-2",
        "players": [{"id": i} for i in range(1, cuantos + 1)],
    }


def _ruta():
    return Path(tempfile.mkdtemp(prefix="escala_")) / "onces.jsonl"


def _lineas(ruta):
    if not ruta.exists():
        return []

    return [
        json.loads(linea)
        for linea in ruta.read_text(encoding="utf-8").splitlines()
        if linea.strip()
    ]


# ============================================================
# BLOQUE 0
# ============================================================

def test_el_once_se_anota_con_la_jornada_de_laliga() -> None:
    """
    La linea lleva la jornada de LaLiga, no solo el round.

    EL FALLO QUE CAZA

        El `round_id` sale de `rounds.data.round.id`, que es lo
        que Biwenger dice que esta en curso. La ventana sale del
        calendario de LaLiga. Si el round va retrasado cuando se
        cruza la ventana —y el 17/09 lo iba— el once quedaba
        anotado bajo la jornada equivocada SIN NINGUNA FORMA DE
        SABERLO desde la propia linea.

    LO QUE NO SE HACE: negarse a anotar. La jornada se juega una
    vez y no vuelve; una etiqueta dudosa se puede arreglar
    despues, una jornada perdida no.
    """

    ruta = _ruta()

    veredicto = anotar_el_once(
        round_id=ROUND_RETRASADO,
        once=_once(),
        primer_partido=PRIMER_PARTIDO,
        ahora=LA_VUELTA,
        desde=VENTANA_DESDE,
        ruta=ruta,
        matchday=JORNADA,
    )

    assert veredicto["anotado"] is True, (
        f"La vuelta de las 20:07 no anota: {veredicto['reason']}"
    )

    lineas = _lineas(ruta)

    # MANOS VACIAS, NO.
    assert lineas, (
        "No se ha escrito ninguna linea: no hay nada que "
        "comprobar."
    )

    fila = lineas[0]

    # 1. LAS DOS NUMERACIONES, Y SON DISTINTAS A PROPOSITO.
    assert fila.get("matchday") == JORNADA, (
        f"La linea dice matchday={fila.get('matchday')} y la "
        f"ventana era la de la jornada {JORNADA}. Sin ese campo, "
        f"una linea anotada con el round retrasado no se puede "
        f"distinguir de una buena."
    )

    assert fila.get("round_id") == ROUND_RETRASADO, (
        "El `round_id` de Biwenger ha dejado de guardarse. Hace "
        "falta para cruzar esta linea con el libro del marcador."
    )

    assert fila["matchday"] != fila["round_id"], (
        "El montaje tiene las dos numeraciones iguales, asi que "
        "no distingue si se guarda una o la otra."
    )

    # 2. Y EL ONCE ENTERO, con su ventana.
    assert len(fila.get("players") or []) == SON_ONCE, (
        f"La linea trae {len(fila.get('players') or [])} "
        f"jugadores y no {SON_ONCE}."
    )

    assert fila.get("ventana_desde"), (
        "La linea no dice desde cuando se podia anotar."
    )

    # 3. Y EL MOTIVO NOMBRA LA JORNADA DE LALIGA, no el round: es
    #    lo que va a leer quien mire el log de las 20:07.
    assert f"jornada {JORNADA} " in veredicto["reason"], (
        f"El motivo dice «{veredicto['reason']}» y tiene que "
        f"nombrar la jornada {JORNADA}: es lo que se mira para "
        f"saber si funciono."
    )


def test_sin_jornada_de_laliga_se_anota_igual_y_se_dice() -> None:
    """
    Sin `matchday` NO se pierde la jornada: se anota y se avisa.

    Es la otra mitad de la decision. Si el calendario fallara,
    negarse a anotar costaria la jornada entera — y la jornada no
    vuelve. Se anota con lo que hay y el motivo dice que la
    etiqueta es el round de Biwenger.
    """

    ruta = _ruta()

    veredicto = anotar_el_once(
        round_id=ROUND_RETRASADO,
        once=_once(),
        primer_partido=PRIMER_PARTIDO,
        ahora=LA_VUELTA,
        desde=VENTANA_DESDE,
        ruta=ruta,
        matchday=None,
    )

    assert veredicto["anotado"] is True, (
        "Sin jornada de LaLiga no se anota. Eso cuesta la jornada "
        "entera por no tener una etiqueta."
    )

    lineas = _lineas(ruta)

    assert lineas, "No se ha escrito ninguna linea."

    assert lineas[0].get("matchday") is None, (
        "Se ha inventado una jornada de LaLiga que no habia."
    )

    assert "round de Biwenger" in veredicto["reason"], (
        f"El motivo dice «{veredicto['reason']}» y no avisa de "
        f"que la etiqueta es el round y no la jornada."
    )


def test_la_ventana_sigue_mandando() -> None:
    """
    Guardar la jornada no ha abierto la puerta.

    Las tres puertas que importan esta noche siguen cerradas:
    antes de la ventana, despues del pitido, y con un once a
    medias.
    """

    apertura = datetime.fromisoformat(VENTANA_DESDE)

    arranque = datetime.fromisoformat(PRIMER_PARTIDO)

    assert apertura < arranque, "El montaje no es una ventana."

    casos = (
        ("antes de la ventana", (apertura - timedelta(minutes=1)).isoformat(), _once()),
        ("despues del pitido", (arranque + timedelta(minutes=1)).isoformat(), _once()),
        ("un once a medias", LA_VUELTA, _once(10)),
    )

    assert casos, "No hay casos que probar."

    for etiqueta, cuando, once in casos:

        ruta = _ruta()

        veredicto = anotar_el_once(
            round_id=ROUND_RETRASADO,
            once=once,
            primer_partido=PRIMER_PARTIDO,
            ahora=cuando,
            desde=VENTANA_DESDE,
            ruta=ruta,
            matchday=JORNADA,
        )

        assert veredicto["anotado"] is False, (
            f"Se ha anotado «{etiqueta}»."
        )

        assert not _lineas(ruta), (
            f"Se ha escrito una linea con «{etiqueta}»."
        )

    # Y DENTRO SI, o las tres puertas estarian cerradas para
    # todos y no anotaria nunca.
    ruta = _ruta()

    bueno = anotar_el_once(
        round_id=ROUND_RETRASADO,
        once=_once(),
        primer_partido=PRIMER_PARTIDO,
        ahora=LA_VUELTA,
        desde=VENTANA_DESDE,
        ruta=ruta,
        matchday=JORNADA,
    )

    assert bueno["anotado"] is True, (
        "Dentro de la ventana y con los once tampoco anota: "
        "entonces no anotaria nunca."
    )


# ============================================================
# BLOQUE 2 — LA ESCALA SE RESPETA
# ============================================================

def test_la_escala_se_respeta() -> None:
    """
    El orden manda, y manda en los dos sentidos.

    1. Con un fichaje y una reventa peleando por el mismo euro,
       GANA EL FICHAJE (peldaño 3 contra peldaño 4).
    2. Con la solvencia en riesgo, GANA LA SOLVENCIA a las dos
       (peldaño 1).
    3. Y lo que no se reconoce no se cuela por delante de nada.
    """

    from src.analysis import la_escala as E

    # MANOS VACIAS, NO.
    assert E.LA_ESCALA, "La escala llega vacia."

    assert len(E.peldaños()) == 5, (
        f"La escala tiene {len(E.peldaños())} peldaños y son 5."
    )

    # Y LOS PELDAÑOS SON DISTINTOS Y ORDENADOS: si dos empataran,
    # «manda» no significaria nada.
    assert list(E.peldaños()) == sorted(set(E.peldaños())), (
        f"Los peldaños no son estrictamente crecientes: "
        f"{E.peldaños()}"
    )

    # 1. EL FICHAJE GANA A LA REVENTA.
    assert E.manda("REVENDER", "MEJORAR_EL_XI") == "MEJORAR_EL_XI", (
        "La reventa gana al fichaje. La caja es para mejorar el "
        "once."
    )

    # Y EN EUROS, no solo en el orden.
    bolsillo = 1_000_000

    fichajes = [{"nombre": "mejora el once", "coste": 800_000}]

    reventas = [{"nombre": "el viaje", "coste": 500_000}]

    assert fichajes and reventas, (
        "Alguna de las dos listas llega vacia: sin las dos no hay "
        "competencia que arbitrar."
    )

    assert (
        fichajes[0]["coste"] + reventas[0]["coste"] > bolsillo
    ), (
        "Las dos caben en el bolsillo, asi que no compiten: este "
        "montaje aprobaria cualquier regla."
    )

    # EL REPARTO, hecho con la escala y nada mas: el once coge
    # primero porque su peldaño es menor, no porque venga antes
    # en la lista.
    orden = sorted(
        (
            ("MEJORAR_EL_XI", fichajes[0]["coste"]),
            ("REVENDER", reventas[0]["coste"]),
        ),
        key=lambda par: E.por_clave(par[0])["peldaño"],
    )

    libre = bolsillo

    dado = {}

    for clave, coste in orden:
        dado[clave] = coste if coste <= libre else 0
        libre -= dado[clave]

    assert dado["MEJORAR_EL_XI"] == fichajes[0]["coste"], (
        "El once no se ha llevado lo que pedia."
    )

    assert dado["REVENDER"] == 0, (
        f"A la reventa se le han dado {dado['REVENDER']} con "
        f"{bolsillo - fichajes[0]['coste']} libres: esta usando "
        f"dinero del once."
    )

    # 2. LA SOLVENCIA GANA A LAS DOS.
    for otra in ("MEJORAR_EL_XI", "REVENDER", "NO_DEGRADAR_EL_XI"):

        assert E.manda(
            "POSITIVO_AL_CIERRE", otra
        ) == "POSITIVO_AL_CIERRE", (
            f"«{otra}» gana a estar en positivo al cierre. Si al "
            f"cierre estamos en negativo no puntuamos: no hay "
            f"nada que gane a eso."
        )

    # 3. Y NO DEGRADAR EL XI GANA A MEJORARLO: primero no
    #    estropear, despues mejorar.
    assert E.manda(
        "MEJORAR_EL_XI", "NO_DEGRADAR_EL_XI"
    ) == "NO_DEGRADAR_EL_XI", (
        "Mejorar el once gana a no degradarlo. Con ese orden, "
        "una mejora podria justificar vender a un titular sin "
        "recambio."
    )

    # 4. LO QUE NO SE RECONOCE NO GANA A NADA.
    assert E.manda("UNA_VIA_NUEVA", "REVENDER") == "REVENDER", (
        "Una via sin nombre se ha colado por delante de la "
        "reventa."
    )

    assert E.a_que_peldaño_responde(
        "algo que nadie ha escrito"
    )["clave"] == "SIN_PELDAÑO", (
        "Una decision desconocida se coloca en un peldaño a ojo "
        "en vez de decir que no se sabe."
    )


def test_cada_decision_dice_a_que_peldaño_responde() -> None:
    """
    Las decisiones que el motor toma de verdad se traducen.

    No vale que la escala exista: tiene que saber leer lo que el
    motor dice hoy.
    """

    from src.analysis import la_escala as E

    casos = {
        "needs_sale_first": 2,
        "XI_UPGRADE": 3,
        "COMPUTER_RESALE": 4,
        "SPECULATION": 4,
        "renovar la publicacion antes de que caduque": 1,
        "ROSTER_FILL": 3,
        "guardarrail: quedarian los cuerpos pero no los titulares": 2,
    }

    assert casos, "No hay decisiones que traducir."

    for decision, esperado in casos.items():

        salida = E.a_que_peldaño_responde(decision)

        assert salida["peldaño"] == esperado, (
            f"«{decision}» sale en el peldaño "
            f"{salida['peldaño']} y responde al {esperado}."
        )

    # Y LA SOLVENCIA GANA AUNQUE EL TEXTO NOMBRE LAS DOS: es el
    # caso que mas facil se cuela.
    mezcla = E.a_que_peldaño_responde(
        "vender por deficit aunque sea un XI_UPGRADE"
    )

    assert mezcla["peldaño"] == 1, (
        f"Un motivo que nombra la solvencia Y el once sale en el "
        f"peldaño {mezcla['peldaño']}. La solvencia manda."
    )


def test_la_escala_se_publica_entera() -> None:
    """
    Media regla es la que se interpreta mal.

    Cada peldaño se publica con su regla Y su consecuencia, y con
    de donde sale.
    """

    from src.analysis import la_escala as E

    publicada = E.publicar()

    assert publicada.get("available"), "La escala no se publica."

    filas = publicada.get("peldaños") or []

    assert len(filas) == 5, (
        f"Se publican {len(filas)} peldaños y son 5."
    )

    for fila in filas:
        for campo in ("peldaño", "clave", "titulo", "regla", "consecuencia"):
            assert str(fila.get(campo) or "").strip(), (
                f"El peldaño {fila.get('clave')} se publica sin "
                f"`{campo}`."
            )

    assert publicada.get("fuente", "").strip(), (
        "La escala se publica sin decir de donde sale."
    )


def main() -> None:

    pruebas = [
        valor
        for nombre, valor in sorted(globals().items())
        if nombre.startswith("test_") and callable(valor)
    ]

    for prueba in pruebas:
        prueba()
        print(f"  OK  {prueba.__name__}")

    print()
    print(f"{len(pruebas)} guardias de LA ESCALA, todas en verde.")


if __name__ == "__main__":
    main()
