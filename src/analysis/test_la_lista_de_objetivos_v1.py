"""
La lista de objetivos: a quien se le pregunta si juega.

DOCTRINA 103 — «no lo sabemos» y «no lo hemos preguntado» no son
lo mismo.

    Las veinte paginas de equipo de FutbolFantasy traen los 513
    jugadores de LaLiga con su `probability` y su
    `hierarchy_value`. El tablero empareja muchos menos porque
    `build_targets` decide A QUIEN se le busca pareja.

    Con el interruptor apagado la lista es plantilla + mercado
    del dia + plantillas de los rivales. Con el puesto, el
    catalogo entero.

EL MOTIVO POR EL QUE ESTABA ACOTADA, Y ESTA ESCRITO

    «cero decisiones cambiadas -nadie valora a un jugador que no
    esta en venta-», del bloque RIVAL del 20/08/2026. La lista se
    hizo con "a quien puedo comprar hoy", no con "quien hay". Es
    una decision, no un olvido.

LO QUE ESTA GUARDIA EXIGE

    1. Que la muestra sirva: sin catalogo no se comprueba nada.
    2. Que con el interruptor puesto la lista DEJE DE SER la del
       escaparate del dia: tiene que cubrir tambien a quien no
       esta en venta ni lo tiene nadie.
    3. Que apagado el comportamiento sea exactamente el de ayer.
    4. Que ampliarla no pida un equipo mas del que ya se pide.

REGLA 23 Y DOCTRINA 24

    No lee `data/`, ni `diagnostico/`, ni la red, ni el reloj: la
    foto se construye aqui. Y si el catalogo llegase vacio, la
    guardia FALLA en vez de pasar en verde sin mirar nada.
"""

from __future__ import annotations

import os

from src.intelligence.futbolfantasy_provider import (
    ENV_EL_CATALOGO,
    build_targets,
    objetivos_el_catalogo,
    team_slug,
)


# ----------------------------------------------------------------
# UNA LIGA DE MENTIRA, CON LAS CUATRO POBLACIONES SEPARADAS
#
#     Los cuatro grupos existen a proposito y ninguno se solapa:
#     asi se puede afirmar que el interruptor solo añade LIBRES,
#     que es lo unico que tiene que añadir.
# ----------------------------------------------------------------

NUESTROS = (101, 102)

EN_VENTA = (201, 202, 203)

DE_RIVALES = (301, 302)

LIBRES = (401, 402, 403, 404, 405)


EQUIPOS = {
    "1": {"name": "Getafe"},
    "2": {"name": "Osasuna"},
}


def _ficha(player_id: int) -> dict:
    return {
        "id": player_id,
        "name": f"Jugador {player_id}",
        "slug": f"jugador-{player_id}",
        "teamID": 1 if player_id % 2 else 2,
        "price": 100_000 + player_id,
    }


def _foto(con_catalogo: bool = True) -> dict:
    """La foto de una liga, con o sin catalogo."""

    todos = NUESTROS + EN_VENTA + DE_RIVALES + LIBRES

    catalogo = (
        {str(pid): _ficha(pid) for pid in todos}
        if con_catalogo
        else {}
    )

    return {
        "catalog": {
            "data": {
                "players": catalogo,
                "teams": EQUIPOS,
            }
        },

        "my_team": [_ficha(pid) for pid in NUESTROS],

        "market": {
            "sales": [
                {
                    "price": 999_000,
                    "player": {
                        "id": pid,
                        "name": f"Jugador {pid}",
                        "teamID": 1 if pid % 2 else 2,
                    },
                }
                for pid in EN_VENTA
            ]
        },

        "rounds": {
            "data": {
                "league": {
                    "standings": [
                        {
                            "name": "Rival",
                            "lineup": {
                                "players": [DE_RIVALES[0]],
                                "discarded": [DE_RIVALES[1]],
                            },
                        }
                    ]
                }
            }
        },
    }


# ----------------------------------------------------------------
# EL INTERRUPTOR LO PONE ESTA GUARDIA, NO EL ENTORNO
# (20/09/2026, y costo dos vueltas)
#
#     `test_apagado_se_comporta_como_ayer` empezaba por
#     comprobar que el interruptor NO estuviese puesto en el
#     entorno. La noche que el dueño lo encendio en el `env` del
#     workflow, la verja se puso roja, el paso «Validate
#     optimized production cycle» devolvio 1 y NO HUBO CICLO.
#
#     Doctrina 104: un interruptor encendido es estado de
#     produccion, y una guardia no lee estado de produccion. La
#     que mide el apagado tiene que APAGARLO ELLA.
#
#     Y para el caso «apagado» se BORRA la variable, no se pone
#     a "0": es el estado que de verdad tiene una maquina
#     limpia. Que "0" y borrada signifiquen lo mismo esta
#     medido aparte, en
#     `test_para_el_lector_borrada_y_cero_son_lo_mismo`.
# ----------------------------------------------------------------


class interruptor:
    """Pone el interruptor y devuelve el entorno como estaba.

    `None` lo BORRA. Sale bien pase lo que pase dentro.
    """

    def __init__(self, valor):
        self.valor = valor

    def __enter__(self):

        self.antes = os.environ.get(ENV_EL_CATALOGO)

        if self.valor is None:
            os.environ.pop(ENV_EL_CATALOGO, None)
        else:
            os.environ[ENV_EL_CATALOGO] = self.valor

        return self

    def __exit__(self, *_):

        if self.antes is None:
            os.environ.pop(ENV_EL_CATALOGO, None)
        else:
            os.environ[ENV_EL_CATALOGO] = self.antes

        return False


def _lista(foto: dict, encendido: bool) -> list:

    with interruptor("1" if encendido else None):
        return build_targets(foto)


def _equipos(lista: list) -> set:
    return {
        objetivo["team"]
        for objetivo in lista
        if objetivo.get("team") and team_slug(objetivo["team"])
    }


# ============================================================
# 1. LA MUESTRA TIENE QUE SERVIR
# ============================================================


def test_sin_catalogo_no_se_comprueba_nada() -> None:
    """
    Doctrina 24. Si el catalogo llega vacio, el interruptor no
    tiene a quien añadir y la prueba de abajo pasaria sin haber
    comprobado nada. Aqui se dice, en vez de salir en verde.
    """

    catalogo = _foto()["catalog"]["data"]["players"]

    assert catalogo, (
        "el catalogo de la prueba llega vacio: el interruptor no "
        "tiene a quien añadir y nada de lo de abajo significa "
        "nada"
    )

    # Y con el catalogo vacio de verdad, el interruptor no añade
    # ni uno: es la demostracion de que la muestra hace falta.
    sin_catalogo = _lista(_foto(con_catalogo=False), encendido=True)

    assert not [
        objetivo
        for objetivo in sin_catalogo
        if objetivo["scope"] == "CATALOGO"
    ], (
        "sin catalogo han salido objetivos de scope CATALOGO: "
        "entonces salen de otro sitio y el nombre miente"
    )

    # El catalogo tiene que traer gente que NO esta en ninguna de
    # las otras tres poblaciones. Si no, ampliar no amplia.
    ya_cubiertos = set(NUESTROS) | set(EN_VENTA) | set(DE_RIVALES)

    fuera = {
        int(pid)
        for pid in catalogo
        if int(pid) not in ya_cubiertos
    }

    assert fuera, (
        "en el catalogo de la prueba no hay ni un jugador libre: "
        "sin ellos el interruptor no tiene nada que añadir"
    )


# ============================================================
# 2. LA PRUEBA QUE DA NOMBRE AL FICHERO
# ============================================================


def test_la_lista_de_objetivos_cubre_el_catalogo() -> None:
    """
    Con el interruptor puesto, el numero de objetivos NO es el
    del escaparate del dia.
    """

    foto = _foto()

    catalogo = foto["catalog"]["data"]["players"]

    puesta = _lista(foto, encendido=True)

    escaparate = len(EN_VENTA)

    del_escaparate = len(NUESTROS) + escaparate

    assert len(puesta) != escaparate, (
        f"con el interruptor puesto la lista sigue siendo la del "
        f"escaparate del dia: {escaparate} objetivos"
    )

    assert len(puesta) > del_escaparate, (
        f"con el interruptor puesto la lista es "
        f"{len(puesta)} y la de plantilla + escaparate es "
        f"{del_escaparate}: no ha cubierto a nadie mas"
    )

    assert len(puesta) == len(catalogo), (
        f"la lista cubre {len(puesta)} de los {len(catalogo)} "
        f"del catalogo: alguien se queda sin que le preguntemos"
    )

    # Y los libres entran con su nombre, no de rebote como
    # ROSTER o MARKET: un dato, un nombre (doctrina 33).
    scopes = {o["id"]: o["scope"] for o in puesta}

    for player_id in LIBRES:

        assert scopes.get(player_id) == "CATALOGO", (
            f"el jugador libre {player_id} entra como "
            f"{scopes.get(player_id)}: el scope tiene que decir "
            f"de donde sale"
        )

    for player_id in NUESTROS:

        assert scopes.get(player_id) == "ROSTER", (
            f"el interruptor ha degradado a {player_id}, que es "
            f"nuestro, a {scopes.get(player_id)}"
        )

    for player_id in EN_VENTA:

        assert scopes.get(player_id) == "MARKET", (
            f"el interruptor ha degradado a {player_id}, que "
            f"esta en venta, a {scopes.get(player_id)}"
        )


# ============================================================
# 3. NO CUESTA UNA PAGINA MAS
# ============================================================


def test_ampliarla_no_pide_un_equipo_mas() -> None:
    """
    El coste que importa. Se pide UNA pagina por equipo con
    objetivo: si ampliar la lista no añade equipos, no añade
    peticiones.
    """

    foto = _foto()

    apagada = _equipos(_lista(foto, encendido=False))

    puesta = _equipos(_lista(foto, encendido=True))

    assert apagada, (
        "apagada, la lista no pide ni un equipo: la foto de la "
        "prueba no tiene equipos reconocibles"
    )

    assert puesta == apagada, (
        f"ampliar la lista pide equipos nuevos "
        f"{sorted(puesta - apagada)}: entonces si cuesta "
        f"peticiones y el informe miente"
    )


# ============================================================
# 4. EL LECTOR: NI CACHEA, NI DISTINGUE BORRADA DE CERO
# ============================================================


def test_el_lector_no_cachea_el_valor() -> None:
    """
    Lo que decide si el arreglo de arriba basta.

    Si `objetivos_el_catalogo()` leyese el entorno UNA vez, al
    importarse el modulo, poner y quitar la variable dentro de
    la prueba no cambiaria nada: el valor con el que arranco el
    proceso mandaria hasta el final, y el arreglo seria de
    mentira.

    Se comprueba moviendola cuatro veces despues de importar.
    """

    for valor, esperado in (
        ("1", True),
        (None, False),
        ("1", True),
        ("0", False),
    ):

        with interruptor(valor):

            assert objetivos_el_catalogo() is esperado, (
                f"con la variable en {valor!r} el lector dice "
                f"{objetivos_el_catalogo()}. Si no sigue al "
                f"entorno despues del import, lo cachea, y "
                f"apagarlo dentro de la prueba no sirve"
            )


def test_para_el_lector_borrada_y_cero_son_lo_mismo() -> None:
    """
    Lo que permite escribir «apagado» con la variable BORRADA.

    Si algun dia "0" dejara de significar apagado -por ejemplo
    porque alguien mire solo si la variable existe- esta prueba
    salta antes de que nadie lo descubra en produccion.
    """

    foto = _foto()

    with interruptor(None):
        borrada = objetivos_el_catalogo()
        lista_borrada = build_targets(foto)

    with interruptor("0"):
        cero = objetivos_el_catalogo()
        lista_cero = build_targets(foto)

    assert borrada == cero is False, (
        f"borrada dice {borrada} y \"0\" dice {cero}: no son lo "
        f"mismo, y entonces escribir una por la otra es una "
        f"suposicion"
    )

    assert lista_borrada == lista_cero, (
        "la lista de objetivos cambia entre tener la variable "
        "borrada y tenerla a \"0\""
    )


# ============================================================
# 5. APAGADO, EXACTAMENTE COMO AYER
# ============================================================


def test_apagado_se_comporta_como_ayer() -> None:

    # EL INTERRUPTOR LO APAGA ESTA GUARDIA. Antes se comprobaba
    # que estuviese apagado en el entorno, y por eso la noche
    # que se encendio en el workflow esta linea paro el ciclo.
    with interruptor(None):

        assert not objetivos_el_catalogo(), (
            "con la variable borrada, el lector sigue diciendo "
            "que el interruptor esta puesto: entonces lo lee de "
            "otro sitio y esta guardia no controla nada"
        )

    foto = _foto()

    apagada = _lista(foto, encendido=False)

    ids = {o["id"] for o in apagada}

    assert ids == set(NUESTROS) | set(EN_VENTA) | set(DE_RIVALES), (
        f"apagada, la lista ya no es plantilla + mercado + "
        f"rivales: {sorted(ids)}"
    )

    for player_id in LIBRES:

        assert player_id not in ids, (
            f"apagada, el jugador libre {player_id} ya entra en "
            f"la lista: el interruptor no esta apagado del todo"
        )

    # Y lo que sale apagado sale IGUAL con el interruptor puesto:
    # ampliar añade, no reescribe.
    puesta = {o["id"]: o for o in _lista(foto, encendido=True)}

    for objetivo in apagada:

        assert puesta[objetivo["id"]] == objetivo, (
            f"el interruptor ha cambiado la ficha de "
            f"{objetivo['name']}: "
            f"{objetivo} -> {puesta[objetivo['id']]}"
        )


def main() -> int:

    pruebas = [
        test_sin_catalogo_no_se_comprueba_nada,
        test_la_lista_de_objetivos_cubre_el_catalogo,
        test_ampliarla_no_pide_un_equipo_mas,
        test_el_lector_no_cachea_el_valor,
        test_para_el_lector_borrada_y_cero_son_lo_mismo,
        test_apagado_se_comporta_como_ayer,
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
        f"LA LISTA DE OBJETIVOS V1: "
        f"{len(pruebas) - fallos}/{len(pruebas)} OK"
    )
    print("=" * 60)

    return 1 if fallos else 0


if __name__ == "__main__":
    raise SystemExit(main())
