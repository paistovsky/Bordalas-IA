"""
Los cuatro trozos suman el patrimonio, y ningun precio de compra
se inventa.

QUE PROTEGE

    `de_donde_salio_el_dinero` contesta de donde salen los 55 M
    de Pollo17 partiendo su crecimiento en cuatro montones. Un
    reparto en montones solo vale si SUMA: si se cuenta una
    compra dos veces, o se pierde una venta, la tabla sigue
    saliendo bonita y dice otra cosa.

    Por eso la guardia no comprueba "parece razonable": comprueba
    la identidad al euro, contra cifras calculadas a mano en el
    encabezado de cada prueba.

LA SEGUNDA REGLA, LA QUE NO SE SALTA

    Si no se sabe a que precio compro a un jugador, NO SE ESTIMA.
    Va al cuarto monton, se cuenta y se dice cuanto vale hoy.

    El reparto inicial es el caso obvio -no dejo precios en el
    tablon- pero no el unico: una plantilla que cambia de dueno
    sin pasar por el mercado tampoco los deja.

SIN DISCO, SIN RED, SIN RELOJ

    Regla 23 y la del 08/09/2026: ninguna guardia lee estado
    externo. El tablon de aqui es un fixture escrito a mano; el
    `ahora` es una constante. Esta prueba da lo mismo hoy que
    dentro de un ano.

REGLA 24: NO SE PASA EN VACIO

    `test_el_fixture_tiene_de_todo` existe para que ninguna de
    las demas pueda ponerse verde sobre una tabla vacia. Si el
    fixture deja de traer viajes, quietos o cuarto monton, esta
    guardia cae antes que ninguna.
"""

from __future__ import annotations

from src.analysis.de_donde_salio_el_dinero import (
    descomponer,
    emparejar,
    operaciones,
)


ANA = 1001

BENI = 1002

SALDO = 23_300_000

# El `leagueReset` real del 09/08/2026. Aqui solo hace de origen
# de tiempos: de el cuelgan las fechas del fixture.
T0 = 1_786_278_446

DIA = 86_400

# La hora a la que se "recogio" el censo. CONSTANTE: los dias que
# lleva un jugador en plantilla se cuentan hasta aqui, nunca
# hasta el reloj de quien ejecute la prueba.
AHORA = T0 + 20 * DIA


# ============================================================
# EL TABLON DE MENTIRA, CON LA FORMA DEL DE VERDAD
# ============================================================


def _market(cuando: int, jugador: int, quien: int, importe: int):
    """Compra al mercado: paga `to`, no hay `from`."""

    return {
        "event_id": f"m{cuando}{jugador}",
        "date": cuando,
        "type": "market",
        "content": [
            {
                "player": jugador,
                "to": {"id": quien, "name": str(quien)},
                "amount": importe,
            }
        ],
    }


def _venta(
    cuando: int,
    jugador: int,
    quien: int,
    importe: int,
    a: int | None = None,
):
    """`transfer` sin `to` = al Computer; con `to` = entre dos."""

    operacion = {
        "player": jugador,
        "from": {"id": quien, "name": str(quien)},
        "amount": importe,
    }

    if a:
        operacion["to"] = {"id": a, "name": str(a)}

    return {
        "event_id": f"t{cuando}{jugador}",
        "date": cuando,
        "type": "transfer",
        "content": [operacion],
    }


# LAS DOS PARTES DE LA JORNADA 1.
#
# La liga tiene `splitRound: "ignoreFirst"`, asi que la primera
# NO paga y la segunda si. Va en el fixture a proposito: si
# alguien rompiera esa regla, los premios saldrian de mas y el
# cuadre lo diria.
J1_IGNORADA = {
    "event_id": "r1",
    "date": T0 + 12 * DIA,
    "type": "roundFinished",
    "content": {
        "round": {"id": 4899, "name": "Jornada 1"},
        "results": [
            {"user": {"id": ANA}, "points": 30, "bonus": 900_000},
            {"user": {"id": BENI}, "points": 20, "bonus": 600_000},
        ],
    },
}

J1_APLAZADA = {
    "event_id": "r2",
    "date": T0 + 14 * DIA,
    "type": "roundFinished",
    "content": {
        "round": {
            "id": 4937,
            "name": "Jornada 1 (aplazada)",
            "part": 2,
        },
        "results": [
            {
                "user": {"id": ANA},
                "points": 40,
                "bonus": 1_200_000,
            },
            {
                "user": {"id": BENI},
                "points": 26,
                "bonus": 800_000,
            },
        ],
    },
}

RACHA = {
    "event_id": "b1",
    "date": T0 + 15 * DIA,
    "type": "bonus",
    "content": [
        {
            "user": {"id": ANA},
            "amount": 250_000,
            "reason": "dailyStreak",
        }
    ],
}


TABLON = [
    # ANA vende un jugador del reparto: cobra, sin coste conocido.
    _venta(T0 + 3 * DIA, 101, ANA, 2_500_000),

    # ANA compra al 200, lo vende, y MAS TARDE lo vuelve a
    # comprar. Es el caso que obliga al FIFO: la venta tiene que
    # emparejarse con la PRIMERA compra, no con la segunda.
    _market(T0 + 1 * DIA, 200, ANA, 5_000_000),
    _venta(T0 + 6 * DIA, 200, ANA, 6_200_000),
    _market(T0 + 10 * DIA, 200, ANA, 6_500_000),

    # ANA compra y se queda al 201.
    _market(T0 + 8 * DIA, 201, ANA, 3_000_000),

    # BENI compra y se queda al 301.
    _market(T0 + 2 * DIA, 301, BENI, 4_000_000),

    # BENI compra al 302 y se lo vende A ANA: un solo evento que
    # es venta para uno y compra para el otro.
    _market(T0 + 4 * DIA, 302, BENI, 2_000_000),
    _venta(T0 + 5 * DIA, 302, BENI, 2_400_000, a=ANA),

    J1_IGNORADA,
    J1_APLAZADA,
    RACHA,
]


# ============================================================
# EL CENSO Y LOS PRECIOS DE HOY
# ============================================================

# `owner` sin `price` = del reparto inicial. Es exactamente como
# llega de Biwenger: la ausencia ES el dato.
CENSO = {
    str(ANA): {
        "id": ANA,
        "name": "Ana",
        "players": [
            {"id": 100, "owner": {"date": T0}},
            {
                "id": 200,
                "owner": {
                    "date": T0 + 10 * DIA,
                    "price": 6_500_000,
                },
            },
            {
                "id": 201,
                "owner": {
                    "date": T0 + 8 * DIA,
                    "price": 3_000_000,
                },
            },
            {
                "id": 302,
                "owner": {
                    "date": T0 + 5 * DIA,
                    "price": 2_400_000,
                },
            },
        ],
    },
    str(BENI): {
        "id": BENI,
        "name": "Beni",
        "players": [
            {"id": 300, "owner": {"date": T0}},
            {
                "id": 301,
                "owner": {
                    "date": T0 + 2 * DIA,
                    "price": 4_000_000,
                },
            },
        ],
    },
}

PRECIOS = {
    100: 4_000_000,
    200: 6_900_000,
    201: 3_400_000,
    300: 7_000_000,
    301: 3_700_000,
    302: 2_600_000,
}


# LAS CUENTAS, HECHAS A MANO.
#
#   ANA   caja 23.300.000 + 1.450.000 premios
#                         + 8.700.000 ventas
#                        - 16.900.000 compras  = 16.550.000
#         plantilla 4.000.000 + 6.900.000
#                 + 3.400.000 + 2.600.000      = 16.900.000
#         patrimonio                             33.450.000
#
#   BENI  caja 23.300.000 +   800.000 premios
#                         + 2.400.000 ventas
#                         - 6.000.000 compras  = 20.500.000
#         plantilla 7.000.000 + 3.700.000      = 10.700.000
#         patrimonio                             31.200.000
ESPERADO = {
    ANA: {
        "prizes": 1_450_000,
        "trading": 1_200_000,
        "holding": 1_000_000,
        "endowment": 6_500_000,
        "net_worth": 33_450_000,
    },
    BENI: {
        "prizes": 800_000,
        "trading": 400_000,
        "holding": -300_000,
        "endowment": 7_000_000,
        "net_worth": 31_200_000,
    },
}


# "No me han pasado nada" tiene que poder distinguirse de "me han
# pasado None", que es justo uno de los casos a probar.
POR_DEFECTO = object()


def _medir(
    tablon=POR_DEFECTO,
    censo=POR_DEFECTO,
    precios=POR_DEFECTO,
):
    return descomponer(
        eventos=TABLON if tablon is POR_DEFECTO else tablon,
        censo=CENSO if censo is POR_DEFECTO else censo,
        precios=PRECIOS if precios is POR_DEFECTO else precios,
        ahora=AHORA,
    )


# ============================================================
# REGLA 24: EL FIXTURE TIENE QUE TRAER DE TODO
# ============================================================


def test_el_fixture_tiene_de_todo() -> None:
    """
    Si el fixture se quedara sin viajes, sin quietos o sin cuarto
    monton, las demas guardias se pondrian verdes sin haber
    probado la parte que les toca. Esta cae primero.
    """

    salida = _medir()

    assert salida["available"], salida

    assert len(salida["managers"]) == 2, salida["managers"].keys()

    for quien, manager in salida["managers"].items():

        assert manager["trips"]["n"] > 0, (
            f"{manager['name']} no tiene ni un viaje cerrado: "
            f"la prueba de los viajes no probaria nada."
        )

        assert manager["held"]["n"] > 0, (
            f"{manager['name']} no tiene ni un jugador comprado "
            f"en plantilla: no hay subida que medir."
        )

        assert manager["unknown_cost"]["in_roster_n"] > 0, (
            f"{manager['name']} no tiene cuarto monton: la regla "
            f"de no inventar precios no se estaria probando."
        )

    assert salida["operations"] >= 8, salida["operations"]

    print(
        f"  OK  el fixture trae {salida['operations']} "
        f"operaciones, viajes, quietos y cuarto monton"
    )


# ============================================================
# EL DINERO CUADRA
# ============================================================


def test_el_dinero_cuadra() -> None:
    """
    23.300.000 + premios + viajes + subida + cuarto monton tiene
    que dar el patrimonio de hoy. Al euro, para los dos.
    """

    salida = _medir()

    assert salida["cuadre"]["available"], salida["cuadre"]

    descuadres = salida["cuadre"]["descuadres"]

    assert not descuadres, (
        "EL DINERO NO CUADRA: "
        + "; ".join(
            f"{d['name']} se separa {d['difference']:+,}"
            for d in descuadres
        )
    )

    for quien, manager in salida["managers"].items():

        suma = (
            SALDO
            + manager["prizes"]
            + manager["trading"]
            + manager["holding"]
            + manager["endowment"]
        )

        assert suma == manager["net_worth"], (
            f"{manager['name']}: los cuatro trozos dan "
            f"{suma:,} y el patrimonio es "
            f"{manager['net_worth']:,}; se separan "
            f"{suma - manager['net_worth']:+,}"
        )

    print(
        f"  OK  los cuatro trozos dan el patrimonio de "
        f"{len(salida['managers'])} managers, al euro"
    )


def test_cada_trozo_vale_lo_que_tiene_que_valer() -> None:
    """
    Que la identidad cuadre no basta: dos errores que se cancelan
    tambien cuadran. Aqui cada trozo va contra su cifra, calculada
    a mano arriba.
    """

    salida = _medir()

    for quien, esperado in ESPERADO.items():

        manager = salida["managers"][quien]

        for trozo, valor in esperado.items():

            assert manager[trozo] == valor, (
                f"{manager['name']} / {trozo}: "
                f"{manager[trozo]:,} en vez de {valor:,}"
            )

    print("  OK  los cuatro trozos valen lo calculado a mano")


def test_la_jornada_partida_no_paga_dos_veces() -> None:
    """
    La J1 se jugo partida y la liga ignora la primera parte.
    Si alguien la contara, los premios de Ana saldrian 900.000 de
    mas y este numero lo dice.
    """

    salida = _medir()

    assert salida["managers"][ANA]["prizes"] == 1_450_000, (
        "los premios de Ana no son 1.450.000: o se ha pagado la "
        "parte ignorada de la J1, o se ha perdido la racha"
    )

    assert salida["cash"]["rounds_paid"] == 1, salida["cash"]

    assert "Jornada 1" in (
        salida["cash"]["ignored_rounds"] or []
    ), salida["cash"]

    print("  OK  la jornada partida paga una sola vez")


def test_el_fifo_empareja_con_la_compra_mas_antigua() -> None:
    """
    Ana compro al 200, lo vendio, y lo volvio a comprar mas caro.

    La venta tiene que emparejarse con la PRIMERA compra
    (5.000.000 -> 6.200.000 = +1.200.000). Si se emparejara con
    la segunda, el viaje daria -300.000 y ademas quedaria en
    plantilla un jugador sin coste que nunca estuvo sin coste.
    """

    filas = operaciones(TABLON)

    libro = emparejar(filas)

    viajes = libro["viajes"][ANA]

    del_200 = [v for v in viajes if v["player"] == 200]

    assert len(del_200) == 1, del_200

    assert del_200[0]["pagado"] == 5_000_000, del_200[0]

    assert del_200[0]["beneficio"] == 1_200_000, del_200[0]

    # Y lo que queda abierto es la SEGUNDA compra.
    assert (
        libro["abiertos"][ANA][200]["amount"] == 6_500_000
    ), libro["abiertos"][ANA][200]

    print("  OK  el FIFO empareja con la compra mas antigua")


def test_una_venta_entre_dos_es_venta_y_compra() -> None:
    """
    El mismo evento resta al que vende y suma al que compra. Si
    solo contara para uno, la caja de la liga no se conservaria.
    """

    salida = _medir()

    beni = salida["managers"][BENI]

    ana = salida["managers"][ANA]

    assert beni["trading"] == 400_000, beni["trading"]

    quietos = {q["player"]: q for q in ana["held"]["detail"]}

    assert 302 in quietos, (
        "el jugador que Ana compro a Beni no esta entre sus "
        "quietos: una compra entre usuarios se ha perdido"
    )

    assert quietos[302]["pagado"] == 2_400_000, quietos[302]

    print("  OK  una venta entre dos cuenta en los dos lados")


# ============================================================
# NINGUN PRECIO DE COMPRA INVENTADO
# ============================================================


def test_ningun_precio_de_compra_inventado() -> None:
    """
    Todo jugador del que se publica una subida tiene que tener un
    coste LEIDO, de una de las dos fuentes. Y todo jugador sin
    coste tiene que estar en el cuarto monton, contado, sin
    ninguna cifra de compra pegada.
    """

    salida = _medir()

    con_coste = sin_coste = 0

    for manager in salida["managers"].values():

        for quieto in manager["held"]["detail"]:

            del_tablon = quieto["coste_del_tablon"]

            de_biwenger = quieto["coste_de_biwenger"]

            assert (
                del_tablon is not None or de_biwenger is not None
            ), (
                f"{manager['name']} / jugador {quieto['player']}: "
                f"se publica una subida de {quieto['subida']:+,} "
                f"sobre un coste que no viene de ninguna fuente"
            )

            assert quieto["pagado"] in (
                del_tablon,
                de_biwenger,
            ), (
                f"{manager['name']} / jugador {quieto['player']}: "
                f"el coste {quieto['pagado']:,} no es el del "
                f"tablon ({del_tablon}) ni el de Biwenger "
                f"({de_biwenger}): se ha fabricado"
            )

            con_coste += 1

        for huerfano in manager["unknown_cost"]["detail"]:

            assert "pagado" not in huerfano, (
                f"{manager['name']} / jugador "
                f"{huerfano['player']}: esta en el cuarto monton "
                f"Y lleva un precio de compra pegado"
            )

            assert "subida" not in huerfano, (
                f"{manager['name']} / jugador "
                f"{huerfano['player']}: no se puede publicar su "
                f"subida sin saber lo que costo"
            )

            assert huerfano["valor"] > 0, huerfano

            sin_coste += 1

    assert con_coste > 0 and sin_coste > 0, (
        f"la prueba no ha visto de los dos tipos "
        f"({con_coste} con coste, {sin_coste} sin)"
    )

    print(
        f"  OK  {con_coste} costes leidos, {sin_coste} sin coste "
        f"y ninguno estimado"
    )


def test_el_del_reparto_va_al_cuarto_monton_valorado() -> None:
    """
    El jugador 100 de Ana viene del reparto: `owner` sin `price`
    y ninguna compra en el tablon. No puede colarse entre los
    quietos, y tiene que contarse con su valor de hoy.
    """

    salida = _medir()

    ana = salida["managers"][ANA]

    assert 100 not in [
        q["player"] for q in ana["held"]["detail"]
    ], "un jugador del reparto se ha colado entre los quietos"

    huerfanos = {
        c["player"]: c for c in ana["unknown_cost"]["detail"]
    }

    assert 100 in huerfanos, ana["unknown_cost"]

    assert huerfanos[100]["valor"] == 4_000_000, huerfanos[100]

    # Y lo que vendio del reparto se cuenta aparte, como cobro.
    assert ana["unknown_cost"]["sold_n"] == 1, ana["unknown_cost"]

    assert (
        ana["unknown_cost"]["sold_proceeds"] == 2_500_000
    ), ana["unknown_cost"]

    print(
        "  OK  el reparto va al cuarto monton: se cuenta y se "
        "valora, no se le inventa coste"
    )


def test_las_dos_fuentes_del_coste_se_contrastan() -> None:
    """
    El tablon y `owner.price` de Biwenger dicen lo mismo. Cuando
    las dos hablan, la salida lo declara; si un dia discreparan,
    este campo se pone a False y se ve.
    """

    salida = _medir()

    contrastados = 0

    for manager in salida["managers"].values():

        for quieto in manager["held"]["detail"]:

            if quieto["las_dos_fuentes_coinciden"] is None:
                continue

            assert quieto["las_dos_fuentes_coinciden"], (
                f"{manager['name']} / jugador {quieto['player']}: "
                f"el tablon dice {quieto['coste_del_tablon']:,} y "
                f"Biwenger dice {quieto['coste_de_biwenger']:,}"
            )

            contrastados += 1

    assert contrastados > 0, (
        "ningun coste se ha podido contrastar contra las dos "
        "fuentes: el contraste no se esta probando"
    )

    print(
        f"  OK  {contrastados} costes coinciden en las dos "
        f"fuentes"
    )


# ============================================================
# UN DESCUADRE SE PUBLICA CON NOMBRE
# ============================================================


def test_una_plantilla_que_cambia_de_manos_descuadra_y_se_dice(
) -> None:
    """
    El caso real: alguien entra en la liga el dia 33 y aparece con
    una plantilla que el tablon nunca le vio comprar.

    Aqui se simula al reves y con lo que rompe la identidad: a
    Beni le desaparece de la plantilla un jugador que COMPRO y
    nunca vendio. La caja le resto la compra y ya no hay nada que
    la devuelva, asi que la cuenta se separa exactamente por lo
    que pago.

    Lo que se prueba no es que descuadre: es que el descuadre
    SALE, con nombre y con la cifra.
    """

    censo = {
        ANA: CENSO[str(ANA)],
        BENI: {
            "id": BENI,
            "name": "Beni",
            "players": [
                # Se ha ido el 301, que costo 4.000.000.
                {"id": 300, "owner": {"date": T0}},
            ],
        },
    }

    salida = _medir(censo={str(k): v for k, v in censo.items()})

    assert not salida["cuadre"]["ok"], (
        "una plantilla que pierde un jugador comprado SIN "
        "venderlo tiene que descuadrar: si cuadra, el reparto en "
        "montones esta tapando el agujero"
    )

    descuadres = {
        d["name"]: d["difference"]
        for d in salida["cuadre"]["descuadres"]
    }

    assert "Beni" in descuadres, descuadres

    assert descuadres["Beni"] == 4_000_000, (
        f"el descuadre tiene que ser lo que pago por el jugador "
        f"que falta (4.000.000), y es {descuadres['Beni']:+,}"
    )

    assert "Ana" not in descuadres, (
        f"el descuadre de uno no puede contagiar al otro: "
        f"{descuadres}"
    )

    assert "Beni" in salida["cuadre"]["reason"], (
        f"el motivo no dice de quien es el descuadre: "
        f"{salida['cuadre']['reason']}"
    )

    print(
        "  OK  un jugador que desaparece sin venderse descuadra "
        "por su precio, con nombre"
    )


def test_un_coste_que_solo_conoce_biwenger_descuadra_a_proposito(
) -> None:
    """
    Si Biwenger dice que un jugador costo X y el tablon no tiene
    esa compra, el tablon ha perdido un evento: la caja tampoco
    resto esos X.

    Se podria tapar mandandolo al cuarto monton, y entonces
    cuadraria. NO SE HACE. Se usa el coste que se conoce y el
    descuadre sale, porque lo que hay que arreglar es el tablon,
    no la tabla.

    Esta prueba no describe un accidente: fija la decision.
    """

    censo = {
        str(ANA): CENSO[str(ANA)],
        str(BENI): {
            "id": BENI,
            "name": "Beni",
            "players": [
                # El 300 es del reparto; aqui le ponemos un
                # precio que el tablon no respalda.
                {
                    "id": 300,
                    "owner": {"date": T0, "price": 5_000_000},
                },
                {
                    "id": 301,
                    "owner": {
                        "date": T0 + 2 * DIA,
                        "price": 4_000_000,
                    },
                },
            ],
        },
    }

    salida = _medir(censo=censo)

    assert not salida["cuadre"]["ok"], (
        "un coste que solo conoce una fuente tiene que verse: si "
        "cuadra, se esta tapando un evento perdido del tablon"
    )

    descuadres = {
        d["name"]: d["difference"]
        for d in salida["cuadre"]["descuadres"]
    }

    assert descuadres.get("Beni") == -5_000_000, descuadres

    # Y el jugador NO acaba en el cuarto monton: su coste se
    # conoce, aunque solo lo diga una de las dos fuentes.
    beni = salida["managers"][BENI]

    quietos = {q["player"]: q for q in beni["held"]["detail"]}

    assert 300 in quietos, beni["held"]["detail"]

    assert quietos[300]["coste_del_tablon"] is None, quietos[300]

    assert (
        quietos[300]["coste_de_biwenger"] == 5_000_000
    ), quietos[300]

    assert (
        quietos[300]["las_dos_fuentes_coinciden"] is None
    ), "con una sola fuente no se puede declarar coincidencia"

    print(
        "  OK  un coste que solo conoce Biwenger se usa y el "
        "descuadre sale, no se tapa"
    )


# ============================================================
# NO SE PASA CON LAS MANOS VACIAS
# ============================================================


def test_sin_eventos_no_hay_descomposicion() -> None:
    """Regla 24. Un tablon vacio no puede devolver una tabla."""

    for vacio in ([], None):

        salida = _medir(tablon=vacio)

        assert not salida["available"], (
            f"con el tablon {vacio!r} ha devuelto una "
            f"descomposicion disponible"
        )

        assert not salida["managers"], salida["managers"]

        assert salida["cuadre"]["ok"] is None, salida["cuadre"]

        assert salida["reason"], (
            "sin eventos hay que DECIR por que no se puede, no "
            "devolver un hueco mudo"
        )

    print("  OK  sin eventos no hay descomposicion, y se dice")


def test_sin_censo_no_hay_patrimonio() -> None:
    """
    Los eventos solos no bastan: sin saber que tiene cada uno hoy
    no hay plantilla que valorar. Se dice, no se supone vacia.
    """

    salida = _medir(censo={})

    assert not salida["available"], salida

    assert "censo" in (salida["reason"] or "").lower(), (
        salida["reason"]
    )

    assert salida["events_read"] == len(TABLON), salida

    print("  OK  sin censo no hay patrimonio, y se dice cual falta")


def test_un_jugador_sin_precio_no_vale_cero() -> None:
    """
    Si el catalogo no trae el precio de un jugador, ese jugador
    NO vale cero: se aparta, se publica, y no se le cuenta como
    valor de plantilla.

    Un cero silencioso descuadraria la tabla sin dejar rastro, que
    es la unica cosa peor que descuadrar.
    """

    precios = {k: v for k, v in PRECIOS.items() if k != 301}

    salida = _medir(precios=precios)

    beni = salida["managers"][BENI]

    assert beni["players_without_price"] == [301], (
        f"el jugador sin precio no se ha publicado: "
        f"{beni['players_without_price']}"
    )

    assert 301 not in [
        q["player"] for q in beni["held"]["detail"]
    ], "un jugador sin precio se ha valorado igualmente"

    assert beni["roster_value"] == 7_000_000, (
        f"la plantilla de Beni solo puede valer lo que se sabe "
        f"valorar (7.000.000), y vale {beni['roster_value']:,}"
    )

    print(
        "  OK  un jugador sin precio se aparta y se publica, no "
        "vale cero"
    )


# ============================================================
# EL TABLON REPITE
# ============================================================


def test_un_tablon_repetido_no_cambia_los_montones() -> None:
    """
    Biwenger reemite el mismo hecho con otro `event_id` y una
    puja mas en `bids`. Si la deduplicacion fallara, las compras
    se contarian dos veces y los viajes tambien.
    """

    reemitido = []

    for evento in TABLON:
        reemitido.append(evento)

        copia = dict(evento)
        copia["event_id"] = f"{evento['event_id']}-bis"
        reemitido.append(copia)

    limpio = _medir()

    sucio = _medir(tablon=reemitido)

    assert sucio["available"], sucio

    assert sucio["events_read"] == 2 * len(TABLON), sucio

    assert sucio["operations"] == limpio["operations"], (
        f"el tablon reemitido produce "
        f"{sucio['operations']} operaciones y el limpio "
        f"{limpio['operations']}"
    )

    for quien in limpio["managers"]:

        for trozo in ("prizes", "trading", "holding", "endowment"):

            assert (
                sucio["managers"][quien][trozo]
                == limpio["managers"][quien][trozo]
            ), (
                f"{limpio['managers'][quien]['name']} / {trozo} "
                f"cambia cuando el tablon repite: "
                f"{sucio['managers'][quien][trozo]:,} contra "
                f"{limpio['managers'][quien][trozo]:,}"
            )

    assert sucio["cuadre"]["ok"], sucio["cuadre"]

    print("  OK  un tablon repetido no mueve ni un monton")


TESTS = [
    test_el_fixture_tiene_de_todo,
    test_el_dinero_cuadra,
    test_cada_trozo_vale_lo_que_tiene_que_valer,
    test_la_jornada_partida_no_paga_dos_veces,
    test_el_fifo_empareja_con_la_compra_mas_antigua,
    test_una_venta_entre_dos_es_venta_y_compra,
    test_ningun_precio_de_compra_inventado,
    test_el_del_reparto_va_al_cuarto_monton_valorado,
    test_las_dos_fuentes_del_coste_se_contrastan,
    test_una_plantilla_que_cambia_de_manos_descuadra_y_se_dice,
    test_un_coste_que_solo_conoce_biwenger_descuadra_a_proposito,
    test_sin_eventos_no_hay_descomposicion,
    test_sin_censo_no_hay_patrimonio,
    test_un_jugador_sin_precio_no_vale_cero,
    test_un_tablon_repetido_no_cambia_los_montones,
]


def main() -> None:
    fallos = 0

    for test in TESTS:
        try:
            test()

        except AssertionError as error:
            fallos += 1
            print(f"FALLA {test.__name__}: {error}")

    print("=" * 60)
    print(
        f"EL DINERO CUADRA V1: "
        f"{len(TESTS) - fallos}/{len(TESTS)} OK"
    )
    print("=" * 60)

    if fallos:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
