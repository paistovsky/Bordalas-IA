"""
Una mediana sin su marea no es un dato.

SINTOMA (26/09/2026)

    Con historico de verdad, el retrotest dijo que aguantar diez
    dias rinde +7,09 % contra el +3,41 % de tres. Leido asi,
    "aguanta mas tiempo" parecia dinero gratis.

CAUSA — LA PREGUNTA QUE NADIE HABIA HECHO

    Cuanto subio el mercado ENTERO en esos diez dias.

    Si el mercado sube un 0,6 % al dia, aguantar diez dias cobra
    un 6 % sin ninguna habilidad, y una via que rinde un 7 %
    aporta un punto, no siete. La mediana de la via no significa
    nada hasta que se le resta la marea.

    En la ventana medida la marea resulto ser NEGATIVA -el
    mercado bajo un 2,30 % en 21 dias-, asi que el neto salio
    mejor que el bruto. Pero eso se supo despues de mirar. Antes
    de mirar, el +7,09 % era exactamente igual de compatible con
    "hay señal" que con "hay marea".

CONSECUENCIA

    Es la misma familia de siempre -un dato contestando una
    pregunta que no era la suya-, y esta vez habria hecho
    alargar el horizonte por una razon inventada.

LO QUE SE PROTEGE AQUI

    1. Que el indice exista y no cambie de forma con los datos.
    2. Que MIDA: sobre un mercado inventado que sube un 1 % al
       dia, el indice tiene que decir 1 % al dia. Un control que
       no detecta la marea que se le sirve no es un control.
    3. Que la ventana se recorte por marcas de tiempo y no
       despues, para que una compra a tres dias que salta de mes
       no se cuente en los dos.
    4. Que nada de esto lance: si el control revienta, se vuelve
       a leer el bruto como si fuera neto.

    Fixture entero: mercados sinteticos con la marea puesta a
    mano. Ni una lectura del estado ni de la red.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta

from src.analysis.hold_backtest import (
    build_operations,
    daily_rate,
)

from scripts.recalibrar_ventana_larga import (
    indice_del_mercado,
    recortar,
)


# ============================================================
# MERCADOS DE MENTIRA, CON LA MAREA PUESTA A MANO
# ============================================================

PRIMER_DIA = date(2026, 8, 1)

DIAS = 30

JUGADORES = 40

PRECIO_BASE = 1_000_000


def _marca(dia: date) -> int:
    """Mediodia, como el bajador."""

    return int(
        datetime(dia.year, dia.month, dia.day, 12, 0).timestamp()
    )


def mercado(deriva_diaria: float, ruido: float = 0.0) -> dict:
    """
    Un almacen con la marea que se le pida.

    `deriva_diaria` en tanto por uno: 0.01 es un 1 % al dia para
    TODOS los jugadores. `ruido` reparte a los jugadores por
    encima y por debajo de esa marea de forma determinista -sin
    `random`, que haria la guardia irrepetible-.
    """

    almacen = {"players": {}}

    for numero in range(JUGADORES):

        # Determinista y centrado en cero: el jugador de en medio
        # va justo con la marea.
        sesgo = ruido * (
            (numero - (JUGADORES - 1) / 2) / max(JUGADORES, 1)
        )

        marcas = []
        precios = []

        precio = float(PRECIO_BASE)

        for indice in range(DIAS):

            dia = PRIMER_DIA + timedelta(days=indice)

            marcas.append(_marca(dia))

            # Redondeo a 10.000, como Biwenger.
            precios.append(int(round(precio / 10_000) * 10_000))

            precio *= 1 + deriva_diaria + sesgo

        almacen["players"][str(1000 + numero)] = {
            "t": marcas,
            "p": precios,
        }

    return almacen


# ============================================================
# PRUEBAS
# ============================================================


def test_el_indice_mide_la_marea_que_se_le_sirve():
    """
    LA PRUEBA QUE IMPORTA.

    Un mercado que sube un 1 % diario, por construccion. Si el
    indice no lo detecta, no sirve para descontar nada.
    """

    indice = indice_del_mercado(
        mercado(deriva_diaria=0.01), PRIMER_DIA, None
    )

    assert indice["available"], indice.get("reason")

    medida = indice["drift_per_day"]

    assert abs(medida - 1.0) < 0.15, (
        f"el mercado sube un 1,00 % diario por construccion y el "
        f"indice dice {medida:.3f} %"
    )


def test_el_indice_ve_una_marea_a_la_baja():
    """
    Y hacia abajo, que es el caso que de verdad se dio: en la
    ventana de produccion el mercado BAJO.
    """

    indice = indice_del_mercado(
        mercado(deriva_diaria=-0.005), PRIMER_DIA, None
    )

    assert indice["available"]

    assert indice["drift_per_day"] < 0, (
        f"un mercado que baja se mide como "
        f"{indice['drift_per_day']:+.3f} %/dia"
    )


def test_un_mercado_plano_no_tiene_marea():
    """
    El caso de control. Sin marea, cero: si aqui saliera un
    numero, todo lo demas estaria descontando humo.
    """

    indice = indice_del_mercado(
        mercado(deriva_diaria=0.0), PRIMER_DIA, None
    )

    assert indice["available"]

    assert abs(indice["drift_per_day"]) < 0.02, (
        f"un mercado plano mide {indice['drift_per_day']:+.3f} "
        f"%/dia de marea"
    )


def test_la_marea_se_come_la_ganancia_bruta():
    """
    LO QUE SE ESTABA A PUNTO DE PUBLICAR MAL.

    En un mercado que sube un 1 % diario y donde TODOS suben
    igual, comprar "el que sube" no aporta nada: la ganancia
    bruta a m dias es la marea de m dias, y el neto es cero.

    Sin esta resta, esa misma tabla se lee como "la via rinde un
    10 % a diez dias".
    """

    almacen = mercado(deriva_diaria=0.01)

    indice = indice_del_mercado(almacen, PRIMER_DIA, None)

    series = {
        int(pid): list(ficha["p"])
        for pid, ficha in almacen["players"].items()
    }

    operaciones = [
        o for o in build_operations(series) if o["horizon"] == 10
    ]

    assert operaciones, "el fixture no genera operaciones"

    retornos = sorted(o["return"] for o in operaciones)

    bruto = 100 * retornos[len(retornos) // 2]

    neto = bruto - indice["drift_per_day"] * 10

    assert bruto > 5, (
        f"el bruto a diez dias sale {bruto:.2f} %: el fixture no "
        f"reproduce el caso"
    )

    assert abs(neto) < 2.0, (
        f"descontada la marea deberia quedar cerca de cero y "
        f"queda {neto:+.2f} %: la resta no esta funcionando"
    )


def test_la_ventana_se_recorta_por_la_marca_de_tiempo():
    """
    Recortar despues de calcular contaria una compra a tres dias
    que salta de agosto a septiembre en los DOS meses. Recortar
    antes la deja fuera de los dos, que es lo correcto: esa
    operacion no ocurrio dentro de ninguna de las dos ventanas.
    """

    almacen = mercado(deriva_diaria=0.0)

    mitad = PRIMER_DIA + timedelta(days=DIAS // 2)

    primera = recortar(almacen, PRIMER_DIA, mitad)
    segunda = recortar(almacen, mitad + timedelta(days=1), None)

    def dias_de(bloque):
        return {
            datetime.fromtimestamp(t).date()
            for ficha in bloque["players"].values()
            for t in ficha["t"]
        }

    solapan = dias_de(primera) & dias_de(segunda)

    assert not solapan, (
        f"las dos ventanas comparten dias: {sorted(solapan)[:5]}"
    )

    assert dias_de(primera), "la primera ventana salio vacia"
    assert dias_de(segunda), "la segunda ventana salio vacia"


def test_recortar_no_desalinea_precios_y_marcas():
    """
    `load_series` empareja `t` con `p` por posicion. Un recorte
    que quitara una marca sin quitar su precio correria la serie
    entera y todos los retornos saldrian del dia de al lado.
    """

    recortado = recortar(
        mercado(deriva_diaria=0.01),
        PRIMER_DIA + timedelta(days=5),
        PRIMER_DIA + timedelta(days=20),
    )

    for pid, ficha in recortado["players"].items():

        assert len(ficha["t"]) == len(ficha["p"]), (
            f"jugador {pid}: {len(ficha['t'])} marcas y "
            f"{len(ficha['p'])} precios"
        )

        assert ficha["t"] == sorted(ficha["t"]), (
            f"jugador {pid}: las marcas salen desordenadas"
        )


def test_la_forma_no_cambia_con_los_datos():
    """
    LA REGLA DEL 17/09. Con mercado y sin mercado, las mismas
    claves.
    """

    con = indice_del_mercado(mercado(0.01), PRIMER_DIA, None)
    sin = indice_del_mercado({"players": {}}, PRIMER_DIA, None)

    assert set(con) == set(sin), (
        f"el indice cambia de forma: {set(con) ^ set(sin)}"
    )

    assert sin["available"] is False
    assert sin["reason"]

    vacio = recortar({}, PRIMER_DIA, None)

    assert set(vacio) == {"players"}, (
        "recortar sin datos no devuelve la misma forma"
    )


def test_nada_de_esto_lanza():
    """
    Si el control revienta, se vuelve a leer el bruto como si
    fuera neto — que es justo el fallo que evita.
    """

    basura = [
        {},
        {"players": None},
        {"players": {"1": None}},
        {"players": {"1": {"t": [1], "p": []}}},
        {"players": {"1": {"t": ["no", None], "p": [1, 2]}}},
        {"players": {"1": {"t": [0, 1], "p": [0, 0]}}},
    ]

    for datos in basura:

        indice = indice_del_mercado(datos, PRIMER_DIA, None)

        assert isinstance(indice, dict)
        assert "available" in indice

        recortado = recortar(datos, PRIMER_DIA, None)

        assert isinstance(recortado, dict)
        assert "players" in recortado


def test_el_indice_solo_usa_series_completas():
    """
    Con jugadores que entran y salen, una subida del indice
    podria ser solo que hoy se cuentan mas jugadores que ayer.
    El indice tiene que quedarse con los que estan TODOS los
    dias y decir cuantos son.
    """

    almacen = mercado(deriva_diaria=0.0)

    # Uno al que le faltan los ultimos dias, y carisimo: si
    # entrara en el indice, su desaparicion se leeria como un
    # desplome del mercado.
    almacen["players"]["9999"] = {
        "t": [
            _marca(PRIMER_DIA + timedelta(days=i))
            for i in range(3)
        ],
        "p": [500_000_000, 500_000_000, 500_000_000],
    }

    indice = indice_del_mercado(almacen, PRIMER_DIA, None)

    assert indice["available"]

    assert indice["players"] == JUGADORES, (
        f"el indice cuenta {indice['players']} jugadores y solo "
        f"{JUGADORES} tienen la serie completa"
    )

    assert abs(indice["drift_per_day"]) < 0.02, (
        f"un jugador incompleto ha movido la marea a "
        f"{indice['drift_per_day']:+.3f} %/dia"
    )


def test_la_tasa_diaria_es_la_de_siempre():
    """
    El bajador construye la serie a partir de la ficha publica y
    no del almacen del ciclo. Si `daily_rate` leyera algo
    distinto de lo que se le da, todo lo medido esta noche
    estaria en otro sitio.
    """

    precios = [100, 110, 110, 99]

    assert daily_rate(precios, 0) is None, (
        "el primer dia no puede tener tasa: no hay anterior"
    )

    assert abs(daily_rate(precios, 1) - 0.10) < 1e-9
    assert daily_rate(precios, 2) == 0.0
    assert daily_rate(precios, 3) < 0


def test_estas_guardias_no_leen_el_estado():
    """
    LA REGLA DEL 18/09. Todo sale de mercados inventados aqui
    dentro.
    """

    import ast

    from pathlib import Path

    from src.analysis.test_verja_determinista_v1 import (
        _docstrings,
    )

    fuente = Path(__file__).read_text(encoding="utf-8")

    arbol = ast.parse(fuente)

    fuera = _docstrings(arbol)

    prohibido = "dat" + "a/"

    for nodo in ast.walk(arbol):

        if id(nodo) in fuera:
            continue

        if isinstance(nodo, ast.Constant) and isinstance(
            nodo.value, str
        ):

            if prohibido in nodo.value:
                raise AssertionError(
                    f"esta guardia lee el estado: {nodo.value!r}"
                )


TESTS = [
    test_el_indice_mide_la_marea_que_se_le_sirve,
    test_el_indice_ve_una_marea_a_la_baja,
    test_un_mercado_plano_no_tiene_marea,
    test_la_marea_se_come_la_ganancia_bruta,
    test_la_ventana_se_recorta_por_la_marca_de_tiempo,
    test_recortar_no_desalinea_precios_y_marcas,
    test_el_indice_solo_usa_series_completas,
    test_la_forma_no_cambia_con_los_datos,
    test_nada_de_esto_lanza,
    test_la_tasa_diaria_es_la_de_siempre,
    test_estas_guardias_no_leen_el_estado,
]


def main() -> None:

    print()
    print("=" * 60)
    print("CALIBRACION LARGA V1")
    print("=" * 60)

    fallos = 0

    for prueba in TESTS:

        try:
            prueba()
            print(f"  OK    {prueba.__name__}")

        except AssertionError as error:
            fallos += 1
            print(f"  FALLA {prueba.__name__}")
            print(f"        {error}")

        except Exception as error:                  # noqa: BLE001
            fallos += 1
            print(f"  ROMPE {prueba.__name__}")
            print(f"        {type(error).__name__}: {error}")

    print("=" * 60)

    if fallos:
        print(f"{fallos} de {len(TESTS)} en rojo.")
        raise SystemExit(1)

    print(f"Los {len(TESTS)} en verde.")


if __name__ == "__main__":
    main()
