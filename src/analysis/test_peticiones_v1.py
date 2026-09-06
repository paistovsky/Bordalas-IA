"""
Un 429 no es un fallo, y las peticiones se cuentan.

SINTOMA (27/09/2026)

    Biwenger limito la cuenta entera por exceso de peticiones.
    Produccion se cayo con "ERROR EN CICLO" y el workflow hubo
    que desactivarlo a mano.

CAUSA — DOS, Y NINGUNA ERA EL NUMERO DE LLAMADAS

    1. NADIE CONTABA. Cuantas peticiones hace un ciclo solo se
       sabia sumando a mano leyendo el codigo. Un consumo que
       nadie mide es un consumo que crece sin que nadie se
       entere hasta el siguiente 429.

    2. UN 429 SUBIA COMO ERROR. La excepcion llegaba al `except
       Exception` del bucle y se imprimia "ERROR EN CICLO", que
       es falso: no hay nada roto. El servidor esta diciendo
       "ahora no".

CONSECUENCIA

    El diagnostico decia que Pepe estaba roto cuando lo que
    pasaba es que habia que esperar. Y el consumo real -32
    peticiones por vuelta, 12 de ellas duplicadas- no aparecia
    en ninguna pantalla.

LO QUE SE PROTEGE AQUI

    1. Que un 429 se reintente con espera creciente.
    2. Que si no cede, salga como `LimiteDePeticiones` y no
       como un error cualquiera: el bucle lo distingue.
    3. Que cada peticion quede contada, agrupada por endpoint
       con los identificadores fuera.
    4. Que `repetidas` cuente lo que dice contar, que es el
       ahorro disponible sin perder un dato.
    5. Que envolver dos veces no cuente doble.

    Sesiones de mentira. Ni una llamada a Biwenger, ni una
    lectura del estado, ni un `sleep` de verdad.
"""

from __future__ import annotations

from src.biwenger import peticiones

from src.biwenger.peticiones import (
    DEMASIADAS,
    REINTENTOS_429,
    Contador,
    LimiteDePeticiones,
    _endpoint,
    envolver,
)


# ============================================================
# SESIONES DE MENTIRA
# ============================================================


class _Respuesta:

    def __init__(self, status_code=200, headers=None):
        self.status_code = status_code
        self.headers = headers or {}


class _Sesion:
    """
    Una sesion que devuelve lo que se le diga.

    `guion` es la lista de codigos que devolvera, en orden. Al
    agotarse repite el ultimo, para poder simular "limitado para
    siempre" sin escribir cuarenta doscientos.
    """

    def __init__(self, guion=None, headers=None):
        self.guion = list(guion or [200])
        self.headers_de_respuesta = headers
        self.llamadas = []

    def _responder(self, url):
        self.llamadas.append(url)

        codigo = (
            self.guion.pop(0)
            if len(self.guion) > 1
            else self.guion[0]
        )

        return _Respuesta(codigo, self.headers_de_respuesta)

    def get(self, url, *a, **k):
        return self._responder(url)

    def post(self, url, *a, **k):
        return self._responder(url)

    def put(self, url, *a, **k):
        return self._responder(url)

    def delete(self, url, *a, **k):
        return self._responder(url)


class _sin_esperar:
    """
    `time.sleep` desactivado, y apuntando lo que se habria
    esperado.

    Una guardia que duerme de verdad es una guardia que nadie
    ejecuta. Y la espera es justo lo que hay que comprobar.
    """

    def __init__(self):
        self.esperas = []
        self.original = None

    def __enter__(self):
        self.original = peticiones.time.sleep
        peticiones.time.sleep = self.esperas.append
        return self

    def __exit__(self, *_):
        peticiones.time.sleep = self.original
        return False


API = "https://biwenger.as.com/api/v2"


# ============================================================
# PRUEBAS
# ============================================================


def test_un_429_se_reintenta_con_espera_creciente():
    """
    LA GUARDIA DEL INCIDENTE.

    Dos 429 seguidos y luego un 200: la peticion tiene que salir
    bien, y las esperas tienen que ir a mas.
    """

    contador = Contador()

    sesion = envolver(
        _Sesion([DEMASIADAS, DEMASIADAS, 200]), contador
    )

    with _sin_esperar() as reloj:
        respuesta = sesion.get(f"{API}/market")

    assert respuesta.status_code == 200, (
        "un 429 pasajero ya no se supera: la peticion buena se "
        "ha perdido"
    )

    assert len(reloj.esperas) == 2, (
        f"se esperaron {len(reloj.esperas)} veces y hubo dos 429"
    )

    assert reloj.esperas[1] > reloj.esperas[0], (
        f"la espera no crece: {reloj.esperas}. Insistir al mismo "
        f"ritmo solo alarga el castigo."
    )


def test_si_no_cede_sale_como_limite_y_no_como_error():
    """
    Y esta es la mitad que arregla el diagnostico: la excepcion
    tiene tipo propio para que el bucle no la llame "ERROR EN
    CICLO".
    """

    sesion = envolver(_Sesion([DEMASIADAS]), Contador())

    with _sin_esperar():

        try:
            sesion.get(f"{API}/market")

        except LimiteDePeticiones as limite:

            assert "429" in str(limite)

            assert "se retira" in str(limite).lower(), (
                "el mensaje no dice que no se ha tocado nada"
            )

            return

        except Exception as otro:                   # noqa: BLE001
            raise AssertionError(
                f"un 429 persistente sale como "
                f"{type(otro).__name__} y el bucle lo contara "
                f"como fallo"
            )

    raise AssertionError(
        "un 429 persistente no levanto nada: la peticion mala "
        "se dio por buena"
    )


def test_no_se_reintenta_para_siempre():
    """
    Insistir sin fin contra un servidor que nos esta limitando
    es la forma mas rapida de que la limitacion dure mas.
    """

    sesion = _Sesion([DEMASIADAS])

    envolver(sesion, Contador())

    with _sin_esperar():

        try:
            sesion.get(f"{API}/market")

        except LimiteDePeticiones:
            pass

    assert len(sesion.llamadas) == REINTENTOS_429 + 1, (
        f"se hicieron {len(sesion.llamadas)} peticiones y el "
        f"tope son {REINTENTOS_429 + 1}"
    )


def test_se_hace_caso_a_retry_after():
    """
    Si el servidor dice cuanto esperar, adivinarlo es peor que
    preguntarlo.
    """

    sesion = envolver(
        _Sesion(
            [DEMASIADAS, 200], headers={"Retry-After": "7"}
        ),
        Contador(),
    )

    with _sin_esperar() as reloj:
        sesion.get(f"{API}/market")

    assert reloj.esperas == [7.0], (
        f"se esperaron {reloj.esperas} y la cabecera pedia 7 s"
    )


def test_un_retry_after_de_horas_no_se_espera():
    """
    Un ciclo dura minutos. Si Biwenger pide media hora, lo que
    toca es retirarse y volver, no dormir dentro del workflow.
    """

    sesion = envolver(
        _Sesion(
            [DEMASIADAS, 200], headers={"Retry-After": "1800"}
        ),
        Contador(),
    )

    with _sin_esperar() as reloj:
        sesion.get(f"{API}/market")

    assert reloj.esperas and reloj.esperas[0] <= 60, (
        f"el ciclo se echaria a dormir {reloj.esperas[0]} s "
        f"dentro del workflow"
    )


def test_cada_peticion_queda_contada():
    """
    Sin esto el consumo solo se conoce por aritmetica, y una
    llamada nueva dentro de un bucle no la ve nadie.
    """

    contador = Contador()

    sesion = envolver(_Sesion([200]), contador)

    sesion.get(f"{API}/market")
    sesion.get(f"{API}/account")
    sesion.post(f"{API}/offers")

    cuenta = contador.resumen()

    assert cuenta["total"] == 3, (
        f"contadas {cuenta['total']} de 3"
    )

    assert cuenta["by_method"] == {"GET": 2, "POST": 1}


def test_los_identificadores_no_parten_el_recuento():
    """
    `/user/1/finances` y `/user/2/finances` son la misma llamada
    hecha dos veces. Si contaran por separado, `repetidas`
    diria cero teniendo siete.
    """

    assert _endpoint(f"{API}/user/1234/finances") == (
        "/user/{id}/finances"
    )

    assert _endpoint(f"{API}/league/99/board") == (
        "/league/{id}/board"
    )

    # Y la query tampoco parte nada: el catalogo se pide dos
    # veces por ciclo con los MISMOS parametros.
    assert _endpoint(
        f"{API}/competitions/la-liga/data?lang=es&score=5"
    ) == "/competitions/la-liga/data"


def test_repetidas_cuenta_el_ahorro_disponible():
    """
    EL NUMERO QUE IMPORTA.

    `repetidas` son las peticiones a un endpoint al que ya se
    habia ido en este mismo ciclo: ahorro sin perder un dato.
    En el ciclo real son 12 de 32.
    """

    contador = Contador()

    sesion = envolver(_Sesion([200]), contador)

    # El catalogo, dos veces, como hace `collect_league_snapshot`.
    sesion.get(f"{API}/competitions/la-liga/data")
    sesion.get(f"{API}/competitions/la-liga/data")

    # Y siete perfiles distintos, que NO son repeticion... salvo
    # que se pidan dos veces, como pasa con las dos colectas del
    # tablon.
    for numero in range(1, 8):
        sesion.get(f"{API}/user/{numero}")

    cuenta = contador.resumen()

    assert cuenta["total"] == 9

    # El catalogo repetido una vez, y los siete perfiles
    # colapsados en un endpoint con 7 llamadas -6 de ellas
    # "repetidas" segun esta definicion-.
    assert cuenta["repeated"] == 1 + 6, (
        f"repetidas dice {cuenta['repeated']}"
    )

    assert cuenta["unique_endpoints"] == 2


def test_envolver_dos_veces_no_cuenta_doble():
    """
    El cliente envuelve en el constructor. Si alguien envolviera
    otra vez, cada peticion contaria dos y el numero que vigila
    el consumo seria justo el que engaña.
    """

    contador = Contador()

    sesion = envolver(_Sesion([200]), contador)
    sesion = envolver(sesion, contador)

    sesion.get(f"{API}/market")

    assert contador.total() == 1, (
        f"una peticion se conto {contador.total()} veces"
    )


def test_la_forma_no_cambia_con_los_datos():
    """
    LA REGLA DEL 17/09. Con peticiones y sin ellas, las mismas
    claves.
    """

    vacio = Contador().resumen()

    lleno = Contador()
    envolver(_Sesion([200]), lleno).get(f"{API}/market")

    assert set(vacio) == set(lleno.resumen()), (
        f"el recuento cambia de forma: "
        f"{set(vacio) ^ set(lleno.resumen())}"
    )

    assert vacio["total"] == 0
    assert vacio["repeated_percent"] == 0.0


def test_nada_de_esto_lanza():
    """
    Un contador que revienta tumbaria el ciclo por vigilarlo,
    que seria peor que no vigilarlo.
    """

    contador = Contador()

    for url in (None, "", 12345, "no-una-url", "://roto"):
        contador.anota("GET", url)

    assert isinstance(contador.resumen(), dict)
    assert contador.resumen()["available"]

    for url in (None, "", 12345, "://roto"):
        assert isinstance(_endpoint(url), str)


def test_el_punto_de_entrada_de_verdad_lo_aguanta():
    """
    LA MITAD QUE CASI SE ME ESCAPA.

    El workflow NO ejecuta `autopilot.main`: ejecuta
    `python -m src.v10_full_autonomous_live`, y ese `main`
    llamaba a `run_cycle` sin un solo `try`. Un 429 salia del
    proceso, el paso de Actions se ponia rojo y el dueño acababa
    desactivando el workflow a mano — que es lo que paso el
    27/09.

    Poner el arreglo solo en el otro `main` habria dejado el
    incidente igual y con sensacion de resuelto.
    """

    from pathlib import Path

    fuente = (
        Path(__file__).parent.parent
        / "v10_full_autonomous_live.py"
    ).read_text(encoding="utf-8")

    assert "except LimiteDePeticiones" in fuente, (
        "el punto de entrada que ejecuta el workflow no "
        "distingue un 429: volveria a caerse el ciclo entero"
    )

    assert "return 0" in fuente, (
        "el limite no sale con codigo cero y el paso de Actions "
        "seguiria en rojo"
    )


def test_el_bucle_largo_tambien_lo_distingue():
    """
    Y el `main` de `autopilot`, que es el que se usa al ejecutar
    en bucle. La rama propia va ANTES del `except Exception` o
    no se alcanza nunca.
    """

    from pathlib import Path

    fuente = (
        Path(__file__).parent.parent / "autopilot.py"
    ).read_text(encoding="utf-8")

    assert fuente.index("except LimiteDePeticiones") < (
        fuente.index("ERROR EN CICLO")
    ), (
        "el `except Exception` esta antes: un 429 volveria a "
        "salir como ERROR EN CICLO"
    )

    assert "NO es un fallo" in fuente


def test_el_recuento_se_publica_cada_vuelta():
    """
    Un consumo que no se imprime es un consumo que nadie mira.
    """

    from pathlib import Path

    for nombre in (
        "autopilot.py",
        "v10_full_autonomous_live.py",
    ):

        fuente = (
            Path(__file__).parent.parent / nombre
        ).read_text(encoding="utf-8")

        assert "_publicar_peticiones" in fuente, (
            f"{nombre} no publica el recuento de peticiones"
        )


def test_estas_guardias_no_leen_el_estado():
    """
    LA REGLA DEL 18/09. Todo sale de sesiones inventadas aqui
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
    test_un_429_se_reintenta_con_espera_creciente,
    test_si_no_cede_sale_como_limite_y_no_como_error,
    test_no_se_reintenta_para_siempre,
    test_se_hace_caso_a_retry_after,
    test_un_retry_after_de_horas_no_se_espera,
    test_cada_peticion_queda_contada,
    test_los_identificadores_no_parten_el_recuento,
    test_repetidas_cuenta_el_ahorro_disponible,
    test_envolver_dos_veces_no_cuenta_doble,
    test_la_forma_no_cambia_con_los_datos,
    test_nada_de_esto_lanza,
    test_el_punto_de_entrada_de_verdad_lo_aguanta,
    test_el_bucle_largo_tambien_lo_distingue,
    test_el_recuento_se_publica_cada_vuelta,
    test_estas_guardias_no_leen_el_estado,
]


def main() -> None:

    print()
    print("=" * 60)
    print("PETICIONES V1")
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
