"""
El escaparate: la rotacion sale de censos guardados, no de la foto de hoy.

QUE SE PRUEBA AQUI

    1. `test_la_rotacion_sale_del_historico`
       El reparto se calcula sobre censos guardados. Falla si el
       historico llega vacio, y no devuelve ceros que parezcan
       medidos.

    2. `test_el_dia_de_mercado_corta_en_el_reset`
       Dos fotos del mismo dia natural a un lado y otro del reset
       son escaparates distintos. Falla si el corte se pone a
       medianoche, porque entonces salen dias de 40 jugadores.

    3. `test_solo_cuentan_los_dias_seguidos`
       Entre dos dias con veinticuatro de agujero no hay rotacion
       que medir.

    4. `test_la_espera_no_se_inventa_con_cero_apariciones`
       Si nadie de la lista ha salido nunca, no hay plazo: solo
       "mas largo que la ventana".

    5. `test_el_patron_dice_su_n_y_no_demuestra_azar`

    6. `test_estabamos_listos_separa_aparecer_de_acertar`

    7. `test_la_regla_dice_lo_que_cuesta`
       Y con pocas subastas no publica regla.

    8. `test_esto_sigue_apagado`

REGLA 23 / DOCTRINA 50: NI DISCO, NI RED, NI RELOJ

    Todo son fixtures escritos aqui, con fechas fijas. `dia_de
    mercado` recibe el instante por argumento y la hora del reset
    tambien: aqui no se llama a `datetime.now()` ni se abre
    ningun fichero.

UNA GUARDIA QUE NO MUERDE ES PEOR QUE NINGUNA

    Las catorce inyecciones de fallo se probaron una a una, en
    memoria. Y `test_el_dia_de_mercado_corta_en_el_reset` NO
    MORDIA al principio: el fixture tenia las dos fotos a las
    08:00 y a las 20:00, o sea las dos DESPUES del reset, y con
    ese par cortar a medianoche o cortar a las cinco da lo mismo.
    Hace falta una foto ANTES del reset —03:00— y otra despues,
    que es exactamente lo que pasa cada madrugada.
"""

from __future__ import annotations

import datetime

from src.analysis.el_escaparate import (
    ENCENDIDO,
    HORA_DEL_RESET,
    dia_de_mercado,
    espera_de_un_jugador,
    esta_encendido,
    estabamos_listos,
    hay_patron,
    regla_de_estar_listo,
    rotacion,
)


# ============================================================
# LOS FIXTURES
# ============================================================
#
# Seis dias de mercado seguidos y uno suelto veinte dias despues,
# que es la forma real de lo que hay en disco: una tanda de
# agosto, un agujero, y unos dias de septiembre.


def _d(texto):
    return datetime.date.fromisoformat(texto)


HISTORICO = {
    _d("2026-08-12"): {1, 2, 3, 4, 5},
    _d("2026-08-13"): {1, 2, 6, 7, 8},
    _d("2026-08-14"): {6, 7, 9, 10, 11},
    # y uno muy posterior: no forma par con el anterior
    _d("2026-09-10"): {12, 13, 14, 15, 16},
}


# ============================================================
# 1. LA ROTACION SALE DEL HISTORICO
# ============================================================


def test_la_rotacion_sale_del_historico():
    """
    Y con el historico vacio, no hay rotacion que publicar.
    """

    salida = rotacion(HISTORICO)

    assert salida["available"]

    assert salida["dias"] == 4
    assert salida["plazas"] == 20
    assert salida["distintos"] == 16, (
        f"de 20 plazas hay 16 jugadores distintos: "
        f"{salida['distintos']}"
    )

    # El reparto de apariciones, con su forma.
    assert salida["reparto_de_apariciones"] == {1: 12, 2: 4}, (
        f"cuatro repiten y doce salen una sola vez: "
        f"{salida['reparto_de_apariciones']}"
    )

    assert salida["hay_agujeros"] is True, (
        "del 12/08 al 10/09 hay veintiocho dias y solo cuatro "
        "escaparates: eso es un agujero y hay que decirlo"
    )

    # ------------------------------------------------
    # EL HISTORICO VACIO: MUERDE AQUI
    # ------------------------------------------------
    vacio = rotacion({})

    assert vacio["available"] is False, (
        "sin censos guardados no se publica una rotacion"
    )

    assert vacio["distintos"] == 0
    assert "una foto sola" in vacio["reason"], (
        "el motivo tiene que decir que no se reconstruye desde una "
        "foto: es justo la tentacion de esta medicion"
    )

    assert rotacion(None)["available"] is False

    # Y un historico con dias vacios tampoco cuenta.
    assert rotacion(
        {_d("2026-08-12"): set(), _d("2026-08-13"): set()}
    )["available"] is False

    print("  OK  la rotacion sale de censos guardados, no de una foto")


# ============================================================
# 2. EL DIA DE MERCADO
# ============================================================


def test_el_dia_de_mercado_corta_en_el_reset():
    """
    Dos fotos del mismo dia natural, una antes del reset y otra
    despues, son escaparates DISTINTOS.
    """

    assert HORA_DEL_RESET == 5

    # LA FORMA DEL FIXTURE, COMPROBADA PRIMERO.
    #
    #     Con las dos fotos despues del reset, cortar a medianoche
    #     o cortar a las cinco da lo mismo y la guardia no prueba
    #     nada. Hace falta una ANTES.
    antes = "2026-09-13T03:20:00"
    despues = "2026-09-13T08:40:00"

    assert int(antes[11:13]) < HORA_DEL_RESET, (
        "el fixture necesita una foto ANTES del reset"
    )

    assert int(despues[11:13]) >= HORA_DEL_RESET

    assert dia_de_mercado(antes) == _d("2026-09-12"), (
        "una foto de las 03:20 pertenece al escaparate del dia "
        "ANTERIOR: el reset no ha pasado todavia"
    )

    assert dia_de_mercado(despues) == _d("2026-09-13")

    assert dia_de_mercado(antes) != dia_de_mercado(despues), (
        "si los dos cayeran en el mismo dia saldrian escaparates "
        "de cuarenta jugadores, y son veinte"
    )

    # Justo en el borde.
    assert dia_de_mercado("2026-09-13T05:00:00") == _d("2026-09-13")
    assert dia_de_mercado("2026-09-13T04:59:59") == _d("2026-09-12")

    # Con zona horaria y con `datetime`, lo mismo.
    assert dia_de_mercado("2026-09-13T03:20:00+00:00") == _d(
        "2026-09-12"
    )

    assert dia_de_mercado(
        datetime.datetime(2026, 9, 13, 3, 20)
    ) == _d("2026-09-12")

    # Y la hora entra por argumento: aqui no se mira ningun reloj.
    assert dia_de_mercado(antes, hora_del_reset=0) == _d(
        "2026-09-13"
    ), (
        "con el corte a medianoche las dos caen el mismo dia: por "
        "eso el corte importa"
    )

    print("  OK  el dia de mercado corta en el reset, no a medianoche")


# ============================================================
# 3. SOLO LOS DIAS SEGUIDOS
# ============================================================


def test_solo_cuentan_los_dias_seguidos():
    """
    Restar dos escaparates con veinticuatro dias en medio no es
    una rotacion: es inventarse veinticuatro dias.
    """

    salida = rotacion(HISTORICO)

    assert salida["pares_consecutivos"] == 2, (
        f"de cuatro dias solo hay dos pares seguidos: "
        f"{salida['pares_consecutivos']}"
    )

    for par in salida["pares"]:
        a = _d(par["de"])
        b = _d(par["a"])

        assert (b - a).days == 1, (
            f"el par {par['de']} -> {par['a']} no es de dias "
            f"seguidos"
        )

    primero = salida["pares"][0]

    assert primero["siguen"] == 2 and primero["nuevos"] == 3, (
        f"del 12 al 13 siguen dos y entran tres: {primero}"
    )

    assert salida["nuevos_por_dia"] == 3.0

    # Con un solo dia no hay pares, y no se publica un ritmo.
    suelto = rotacion({_d("2026-08-12"): {1, 2, 3}})

    assert suelto["available"] is True
    assert suelto["pares_consecutivos"] == 0
    assert suelto["nuevos_por_dia"] is None, (
        "con un solo dia no hay nuevos por dia que calcular"
    )

    print("  OK  solo los dias seguidos cuentan para la rotacion")


# ============================================================
# 4. LA ESPERA
# ============================================================


def test_la_espera_no_se_inventa_con_cero_apariciones():
    """
    Si nadie de la lista salio nunca, no hay plazo.
    """

    # Cinco apariciones de veinte vigilados en diez dias.
    salida = espera_de_un_jugador(5, 20, 10)

    assert salida["available"]
    assert salida["oportunidades"] == 200
    assert salida["tasa_diaria"] == 0.025
    assert salida["espera_dias"] == 40.0, (
        f"5 de 200 oportunidades es 2,5 % al dia, o sea 40 dias: "
        f"{salida['espera_dias']}"
    )

    assert "200" in salida["reason"], (
        "la tasa tiene que salir con su denominador"
    )

    # ------------------------------------------------
    # CERO APARICIONES: MUERDE AQUI
    # ------------------------------------------------
    ninguna = espera_de_un_jugador(0, 6, 10)

    assert ninguna["available"] is True
    assert ninguna["espera_dias"] is None, (
        "con cero apariciones no se puede poner un plazo, y un "
        "infinito tampoco es un plazo"
    )

    assert "mas largo que 10" in ninguna["reason"], (
        "lo unico que se puede decir es que es mas largo que la "
        "ventana mirada"
    )

    # Sin dias o sin jugadores, nada.
    assert espera_de_un_jugador(5, 0, 10)["available"] is False
    assert espera_de_un_jugador(5, 20, 0)["available"] is False

    print("  OK  con cero apariciones no se inventa un plazo")


# ============================================================
# 5. EL PATRON
# ============================================================


def test_el_patron_dice_su_n_y_no_demuestra_azar():
    """
    Un `p` alto con muestra corta dice "esta prueba no lo ve", no
    "no existe".
    """

    # Dos muestras iguales: no hay hueco.
    iguales = hay_patron(
        [1, 2, 3, 4, 5, 6, 7, 8],
        [1, 2, 3, 4, 5, 6, 7, 8],
        nombre="precio",
    )

    assert iguales["available"]
    assert iguales["hay_patron"] is False
    assert iguales["n_salieron"] == 8 and iguales["n_no"] == 8, (
        "el `n` de los dos lados se publica siempre"
    )

    assert "n=8" in iguales["reason"]

    # Dos muestras separadas: si lo ve.
    separadas = hay_patron(
        [100, 101, 102, 103, 104, 105, 106, 107],
        [1, 2, 3, 4, 5, 6, 7, 8],
        nombre="precio",
    )

    assert separadas["hay_patron"] is True, (
        "si el fixture no separa nada, la guardia no prueba nada"
    )

    assert separadas["p"] < 0.05

    # MUESTRA CORTA: no se publica un `p` que no aguanta.
    corta = hay_patron([1, 2], [3, 4], nombre="precio")

    assert corta["available"] is False
    assert "corta" in corta["reason"].lower()

    print("  OK  el patron sale con su `n` y no proclama azar")


# ============================================================
# 6. ¿ESTABAMOS LISTOS?
# ============================================================

NOSOTROS = 100

# LA FORMA QUE HAY QUE REPRODUCIR ES LA REAL: nosotros pujamos
# POCO y convertimos MEJOR que el lider. Con un fixture en el que
# el lider convierte mejor, la guardia no prueba la distincion que
# existe para probar.
SUBASTAS = [
    # Dia 1: pujamos y ganamos
    {"dia": "2026-09-10", "to_id": 100, "to_name": "Pepe", "pujadores": {200}},
    # Dia 1: pujamos y volvemos a ganar
    {"dia": "2026-09-10", "to_id": 100, "to_name": "Pepe", "pujadores": {200, 300}},
    # Dia 2: no aparecemos
    {"dia": "2026-09-11", "to_id": 200, "to_name": "Pollo", "pujadores": {300}},
    {"dia": "2026-09-11", "to_id": 300, "to_name": "Luismi", "pujadores": {200}},
    # Dia 3: tampoco
    {"dia": "2026-09-12", "to_id": 200, "to_name": "Pollo", "pujadores": set()},
]


def test_estabamos_listos_separa_aparecer_de_acertar():
    """
    Participacion y conversion son dos numeros distintos, y el
    que importa es el primero.
    """

    salida = estabamos_listos(SUBASTAS, NOSOTROS)

    assert salida["available"] and salida["n"] == 5

    nuestra = salida["nosotros"]

    assert nuestra["pujadas"] == 2 and nuestra["ganadas"] == 2
    assert nuestra["conversion"] == 100.0
    assert nuestra["participacion_percent"] == 40.0
    assert nuestra["dias_con_puja"] == 1

    lider = salida["lider"]

    assert lider["name"] == "Pollo"
    assert lider["pujadas"] == 5, (
        "si el lider no puja mas que nosotros, el fixture no prueba "
        "lo que se quiere probar"
    )

    # EL NUMERO QUE SEPARA "ELEGIMOS MAL" DE "NO ESTABAMOS".
    assert salida["subastas_en_dias_sin_puja_nuestra"] == 3, (
        f"tres subastas pasaron en dias en los que no pujamos: "
        f"{salida['subastas_en_dias_sin_puja_nuestra']}"
    )

    # Convertir mejor que el lider y pujar menos: las dos cosas a
    # la vez, que es justo el caso real.
    assert nuestra["conversion"] > lider["conversion"], (
        "el fixture tiene que tener a alguien que convierte mejor y "
        "puja menos, o no prueba la distincion"
    )

    assert nuestra["pujadas"] < lider["pujadas"]

    # La lista vacia no dice que participamos en cero.
    vacia = estabamos_listos([], NOSOTROS)

    assert vacia["available"] is False
    assert "sin tablon" in vacia["reason"]

    print("  OK  aparecer y acertar salen como dos numeros distintos")


# ============================================================
# 7. LA REGLA
# ============================================================

IMPORTES = [
    150_000, 300_000, 450_000, 700_000, 900_000,
    1_200_000, 1_800_000, 2_500_000, 3_200_000, 4_000_000,
    5_500_000, 7_000_000, 9_000_000, 12_000_000, 20_000_000,
]


def test_la_regla_dice_lo_que_cuesta():
    """
    Y con pocas subastas no se publica regla ninguna.
    """

    regla = regla_de_estar_listo(
        IMPORTES,
        cajas={"hoy": 1_000_000, "de fichar": 8_874_116},
        ritmo_de_plantilla_percent_dia=0.2479,
        cobertura_objetivo=0.75,
    )

    assert regla["available"] and regla["n"] == 15

    assert regla["mediana"] == 2_500_000

    assert regla["caja_propuesta"] == 7_000_000, (
        f"el percentil 75 de estos quince importes son 7 M: "
        f"{regla['caja_propuesta']}"
    )

    # EL COSTE SE DICE, NO SE ESCONDE.
    assert regla["coste_por_dia"] == round(
        7_000_000 * 0.2479 / 100
    ), (
        "tener la caja parada cuesta el ritmo al que se revaloriza "
        "la plantilla, y ese numero tiene que salir"
    )

    assert regla["coste_por_mes"] == regla["coste_por_dia"] * 30

    assert "cuesta" in regla["reason"], (
        "una regla que no dice lo que cuesta esconde la mitad"
    )

    # Y a que fraccion llega cada caja.
    assert regla["alcance"]["hoy"]["subastas_al_alcance"] == 5
    assert regla["alcance"]["de fichar"]["subastas_al_alcance"] == 12

    # Sin ritmo, el coste no se inventa.
    sin_ritmo = regla_de_estar_listo(IMPORTES, cajas={})

    assert sin_ritmo["coste_por_dia"] is None
    assert "no se ha podido medir" in sin_ritmo["reason"]

    # ------------------------------------------------
    # POCAS SUBASTAS: MUERDE AQUI
    # ------------------------------------------------
    corta = regla_de_estar_listo([100, 200, 300])

    assert corta["available"] is False, (
        "con tres subastas no hay regla: prefiero ninguna a una "
        "inventada"
    )

    assert "inventada" in corta["reason"]

    print("  OK  la regla sale con su coste, o no sale")


# ============================================================
# 8. APAGADO
# ============================================================


def test_esto_sigue_apagado():

    assert ENCENDIDO is False, (
        "este encargo es contar, no arreglar"
    )

    assert esta_encendido() is False

    # Pero cuenta.
    assert rotacion(HISTORICO)["available"]
    assert estabamos_listos(SUBASTAS, NOSOTROS)["available"]

    print("  OK  esto cuenta, se publica y sigue apagado")


TESTS = [
    test_la_rotacion_sale_del_historico,
    test_el_dia_de_mercado_corta_en_el_reset,
    test_solo_cuentan_los_dias_seguidos,
    test_la_espera_no_se_inventa_con_cero_apariciones,
    test_el_patron_dice_su_n_y_no_demuestra_azar,
    test_estabamos_listos_separa_aparecer_de_acertar,
    test_la_regla_dice_lo_que_cuesta,
    test_esto_sigue_apagado,
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
    print(f"EL ESCAPARATE V1: {len(TESTS) - fallos}/{len(TESTS)} OK")
    print("=" * 60)

    if fallos:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
