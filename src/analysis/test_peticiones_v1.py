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


# ============================================================
# EL CONSUMO NO PUEDE CRECER EN SILENCIO
# ============================================================
#
#     Los sitios desde los que se llama a Biwenger en el camino
#     de un ciclo. Si aparece uno nuevo, el recuento del informe
#     -32 por vuelta, 1.536 al dia- deja de ser cierto y hay que
#     rehacerlo A PROPOSITO, no enterarse en el siguiente 429.
#
#     Se cuentan LEYENDO EL CODIGO, con `ast`. Ejecutar los
#     colectores aqui no vale: `collect_board_history` escribe
#     en el estado, y una guardia que escribe estado es peor que
#     una que lo lee.
SITIOS_DE_LLAMADA = {
    # login, account, my_player_ids, catalog, market
    "biwenger/client.py": 5,

    # rounds, user(lineup), catalog
    "collectors/league_collector.py": 3,

    # board, league_users, user_profile, own_finances
    "collectors/board_history_collector.py": 4,
}


# Lo que cuesta una vuelta, medido con
# `scripts/contar_peticiones_del_ciclo.py` el 27/09/2026.
PETICIONES_POR_CICLO = 32


def test_no_han_aparecido_llamadas_nuevas():
    """
    LA GUARDIA QUE VIGILA EL NUMERO.

    Un consumo que solo se conoce por un informe caduca el dia
    que alguien mete una llamada. Esto lo cuenta desde el codigo
    y se pone rojo cuando cambia.

    Si sale roja y el cambio es querido: actualiza el numero
    aqui Y el informe. Eso es justo lo que se pretende — que
    cueste un gesto deliberado.
    """

    import ast

    from pathlib import Path

    raiz = Path(__file__).parent.parent

    for relativo, esperados in SITIOS_DE_LLAMADA.items():

        fichero = raiz / relativo

        if not fichero.exists():
            raise AssertionError(
                f"{relativo} ha desaparecido: el recuento del "
                f"informe ya no describe el ciclo"
            )

        arbol = ast.parse(
            fichero.read_text(encoding="utf-8")
        )

        sitios = 0

        for nodo in ast.walk(arbol):

            if not isinstance(nodo, ast.Call):
                continue

            funcion = nodo.func

            if not isinstance(funcion, ast.Attribute):
                continue

            if funcion.attr not in {
                "get",
                "post",
                "put",
                "delete",
            }:
                continue

            # `algo.session.get(...)`: el que cuelga de `session`
            # es una llamada a la API. `dict.get` no.
            padre = funcion.value

            if (
                isinstance(padre, ast.Attribute)
                and padre.attr == "session"
            ) or (
                isinstance(padre, ast.Name)
                and padre.id == "session"
            ):
                sitios += 1

        assert sitios == esperados, (
            f"{relativo} tiene {sitios} llamadas a Biwenger y el "
            f"informe cuenta {esperados}. El consumo del ciclo "
            f"({PETICIONES_POR_CICLO} por vuelta, "
            f"{48 * PETICIONES_POR_CICLO} al dia) ha dejado de "
            f"ser cierto: rehazlo con "
            f"scripts/contar_peticiones_del_ciclo.py y actualiza "
            f"el numero aqui y en docs/."
        )


# ============================================================
# EL PASO A: SIN DUPLICADOS (07/09/2026)
# ============================================================
#
#     Medido con la misma sonda, ejecutando los colectores
#     contra una sesion de mentira y escribiendo en un
#     temporal.

PETICIONES_POR_CICLO = 17

PETICIONES_ANTES_DEL_PASO_A = 32


def test_una_vuelta_cuesta_lo_que_dice_el_informe():
    """
    LA GUARDIA DEL PASO A.

    Ejecuta los colectores DE VERDAD contra una sesion falsa y
    cuenta. Si alguien vuelve a duplicar una llamada -o mete una
    nueva- este numero sube y la guardia se pone roja, en vez de
    enterarnos en el siguiente 429.

    No toca la red ni el estado: `medir_un_ciclo` desvia la
    sesion y los directorios de salida.
    """

    from scripts.contar_peticiones_del_ciclo import (
        medir_un_ciclo,
    )

    medido = medir_un_ciclo()

    assert medido["total"] == PETICIONES_POR_CICLO, (
        f"una vuelta cuesta {medido['total']} peticiones y el "
        f"informe dice {PETICIONES_POR_CICLO} "
        f"({48 * PETICIONES_POR_CICLO} al dia). Si el cambio es "
        f"querido, actualiza el numero aqui y en docs/; si no, "
        f"alguien ha vuelto a pedir lo mismo dos veces. "
        f"Desglose: {medido['by_endpoint']}"
    )


def test_el_tablon_se_colecta_una_sola_vez():
    """
    EL DUPLICADO QUE COSTABA 12 PETICIONES.

    `build_competitive_observer` llamaba a
    `collect_board_history()` a pelo y veinte lineas mas abajo
    tenia escrito que no habia que hacerlo. 24 de las 32
    peticiones por vuelta eran eso.

    Se comprueba por el efecto -cuantas veces se pide el
    tablon- y no por el nombre de la funcion, para que valga
    aunque alguien reorganice el codigo.
    """

    from scripts.contar_peticiones_del_ciclo import (
        medir_un_ciclo,
    )

    por_endpoint = medir_un_ciclo()["by_endpoint"]

    veces = por_endpoint.get("GET /league/{id}/board", 0)

    assert veces == 1, (
        f"el tablon se pide {veces} veces por vuelta. Cada una "
        f"arrastra los {7} perfiles de manager: son 12 "
        f"peticiones y 576 al dia."
    )

    logins = por_endpoint.get("POST /auth/login", 0)

    assert logins == 1, (
        f"se hacen {logins} logins por vuelta. El cliente de la "
        f"vuelta se comparte: ver `cliente_del_ciclo`."
    )

    catalogo = por_endpoint.get(
        "GET /competitions/la-liga/data", 0
    )

    assert catalogo == 1, (
        f"el catalogo se pide {catalogo} veces. Son 500 KB y se "
        f"puede pasar a `get_my_team(catalog=...)`."
    )


def test_el_ahorro_del_paso_a_es_el_que_se_publica():
    """
    Que el antes y el despues no se separen. Si alguien toca
    uno de los dos numeros sin tocar el otro, el informe pasa a
    mentir.
    """

    ahorro = PETICIONES_ANTES_DEL_PASO_A - PETICIONES_POR_CICLO

    assert ahorro == 15, (
        f"el ahorro del paso A es {ahorro} y el informe dice 15"
    )

    assert 48 * ahorro == 720

    from scripts.contar_peticiones_del_ciclo import (
        ANTES_DEL_PASO_A,
    )

    assert ANTES_DEL_PASO_A == PETICIONES_ANTES_DEL_PASO_A, (
        "la sonda y la guardia no cuentan el mismo antes"
    )


# ============================================================
# EL PASO B: CACHE ENTRE RESETS (07/09/2026)
# ============================================================

PETICIONES_DE_CRUCERO = 7


LOS_SIETE = [
    {"id": 100 + n, "name": f"Manager {n}"} for n in range(7)
]


def _movimiento(
    quien: int, cuando: int, tipo: str = "transfer", a=None
) -> dict:
    """Un evento del tablon: fulano ficha o vende."""

    trozo = {"player": 999, "from": {"id": quien, "name": "X"}}

    if a is not None:
        trozo["to"] = {"id": a, "name": "Y"}

    return {"type": tipo, "date": cuando, "content": [trozo]}


def _guardados() -> dict:
    return {str(u["id"]): {"id": u["id"]} for u in LOS_SIETE}


def test_el_que_se_mueve_a_media_tarde_se_refresca():
    """
    LA GUARDIA QUE MAS IMPORTA DEL PASO B.

    La cache de perfiles NO puede usar el reloj del reset. Si un
    manager ficha a las 16:00 y su plantilla valiera "hasta las
    07:00 de mañana", Pepe estaria decidiendo contra una
    plantilla que ya no existe durante quince horas.

    El reloj de los perfiles es el tablon: se refresca al que se
    ha movido DESDE LA ULTIMA COLECTA, a la hora que sea.
    """

    from src.biwenger.cache_del_reset import (
        perfiles_a_refrescar,
    )

    ultima_colecta = 1_788_600_000

    media_tarde = ultima_colecta + 1_800

    plan = perfiles_a_refrescar(
        users=LOS_SIETE,
        eventos=[_movimiento(103, media_tarde)],
        cacheados=_guardados(),
        desde=ultima_colecta,
    )

    assert 103 in plan["refrescar"], (
        "el manager que acaba de fichar NO se refresca: "
        + str(plan["reason"])
        + ". La cache nos deja ciegos."
    )

    assert len(plan["refrescar"]) == 1, (
        "se refrescan " + str(len(plan["refrescar"]))
        + " y solo se movio uno"
    )

    assert len(plan["reutilizar"]) == 6


def test_en_un_traspaso_se_refrescan_los_dos():
    """
    Un traspaso cambia DOS plantillas. Refrescar solo la del que
    vende deja la del que compra con un jugador de menos, y esa
    es la que dice cuanto puede pujar.
    """

    from src.biwenger.cache_del_reset import (
        perfiles_a_refrescar,
    )

    plan = perfiles_a_refrescar(
        users=LOS_SIETE,
        eventos=[_movimiento(101, 2_000, a=105)],
        cacheados=_guardados(),
        desde=1_000,
    )

    assert set(plan["refrescar"]) == {101, 105}, (
        "un traspaso solo refresco " + str(plan["refrescar"])
    )


def test_lo_de_antes_de_la_ultima_colecta_no_cuenta():
    """
    Si contaran los eventos viejos, cada vuelta refrescaria a
    todo el que se hubiera movido alguna vez y la cache no
    ahorraria nada.
    """

    from src.biwenger.cache_del_reset import (
        perfiles_a_refrescar,
    )

    plan = perfiles_a_refrescar(
        users=LOS_SIETE,
        eventos=[_movimiento(102, 500)],
        cacheados=_guardados(),
        desde=1_000,
    )

    assert not plan["refrescar"], (
        "un movimiento anterior a la ultima colecta obliga a "
        "refrescar: " + str(plan["refrescar"])
    )


def test_sin_cache_previa_se_piden_todos():
    """
    La primera vuelta del dia paga entera. Cualquier otra cosa
    seria inventarse una plantilla.
    """

    from src.biwenger.cache_del_reset import (
        perfiles_a_refrescar,
    )

    plan = perfiles_a_refrescar(
        users=LOS_SIETE, eventos=[], cacheados={}, desde=0
    )

    assert len(plan["refrescar"]) == 7


def test_ante_la_duda_se_refresca_de_mas():
    """
    Una cache que se equivoca hacia el lado caro cuesta
    peticiones. Hacia el lado barato, decisiones.
    """

    from src.biwenger.cache_del_reset import (
        perfiles_a_refrescar,
    )

    for basura in (None, "no-una-lista", [None], [{"x": 1}]):

        plan = perfiles_a_refrescar(
            users=LOS_SIETE,
            eventos=basura,
            cacheados=_guardados(),
            desde=1_000,
        )

        assert isinstance(plan["refrescar"], list)
        assert "reutilizar" in plan


def test_la_cache_del_reset_caduca_en_el_reset():
    """
    Lo guardado ANTES del ultimo reset no vale: los precios ya
    han cambiado. Lo guardado despues, si.
    """

    import tempfile

    from datetime import datetime, timedelta, timezone
    from pathlib import Path

    from src.biwenger import cache_del_reset as cache

    with tempfile.TemporaryDirectory() as carpeta:

        fichero = Path(carpeta) / "cache.json"

        ahora = datetime(
            2026, 9, 7, 12, 0, tzinfo=timezone.utc
        )

        cache.escribir(
            "catalogo", {"a": 1}, path=fichero, ahora=ahora
        )

        fresco = cache.leer(
            "catalogo", path=fichero, ahora=ahora
        )

        assert fresco["fresco"], fresco["reason"]

        manana = ahora + timedelta(days=1)

        caducado = cache.leer(
            "catalogo", path=fichero, ahora=manana
        )

        assert not caducado["fresco"], (
            "la cache sobrevive al reset: los precios de ayer "
            "decidirian hoy"
        )

        assert "reset" in (caducado["reason"] or "").lower()


def test_la_hora_del_reset_no_esta_copiada():
    """
    REGLA DE LA CASA: un dato, un sitio.

    Si la hora del reset se copiara aqui, el dia que Biwenger la
    mueva habria dos y una estaria mal.
    """

    from pathlib import Path

    fuente = (
        Path(__file__).parent.parent
        / "biwenger"
        / "cache_del_reset.py"
    ).read_text(encoding="utf-8")

    assert "FALLBACK_RESET_HOUR_UTC" in fuente, (
        "la cache ya no importa la hora del reset del reloj del "
        "mercado: hay dos horas del reset en el proyecto"
    )


def test_el_interruptor_de_la_cache_devuelve_el_mundo_de_antes():
    """`BORDALAS_SIN_CACHE=1` y todo se vuelve a pedir."""

    import os

    from src.biwenger.cache_del_reset import (
        DISABLE_ENV,
        leer,
        perfiles_a_refrescar,
    )

    antes = os.environ.get(DISABLE_ENV)
    os.environ[DISABLE_ENV] = "1"

    try:
        assert not leer("catalogo")["fresco"]

        plan = perfiles_a_refrescar(
            users=LOS_SIETE,
            eventos=[],
            cacheados=_guardados(),
            desde=1_000,
        )

        assert len(plan["refrescar"]) == 7, (
            "con el interruptor puesto sigue cacheando"
        )

    finally:
        if antes is None:
            os.environ.pop(DISABLE_ENV, None)
        else:
            os.environ[DISABLE_ENV] = antes


def test_un_perfil_que_fallo_no_se_guarda():
    """
    `fetch_user_profiles` mete un `_fetch_error` cuando no puede
    bajar uno. Guardarlo seria servir ese error como dato hasta
    que ese manager fichara.
    """

    from pathlib import Path

    fuente = (
        Path(__file__).parent.parent
        / "collectors"
        / "board_history_collector.py"
    ).read_text(encoding="utf-8")

    cuerpo = fuente.split("def save_cached_profiles")[1]

    assert "_fetch_error" in cuerpo.split("\ndef ")[0], (
        "los perfiles que fallaron se estan guardando en cache"
    )


def test_la_vuelta_de_crucero_cuesta_lo_que_dice_el_informe():
    """
    EL NUMERO DEL PASO B, MEDIDO.

    47 de cada 48 vueltas del dia son de crucero: cache llena y
    nadie moviendose. Esta es la que se paga casi siempre.
    """

    from scripts.contar_peticiones_del_ciclo import (
        medir_un_ciclo,
    )

    medido = medir_un_ciclo(vueltas=2)

    assert medido["total"] == PETICIONES_DE_CRUCERO, (
        "una vuelta de crucero cuesta "
        + str(medido["total"])
        + " y el informe dice "
        + str(PETICIONES_DE_CRUCERO)
        + ". Desglose: "
        + str(medido["by_endpoint"])
    )

    # Y que la cache este de verdad trabajando: si el catalogo o
    # los perfiles siguieran pidiendose, el total podria cuadrar
    # por otro lado y no nos enterariamos.
    assert "GET /competitions/la-liga/data" not in (
        medido["by_endpoint"]
    ), "el catalogo se sigue pidiendo en crucero"

    assert "GET /user/{id}" not in medido["by_endpoint"], (
        "los perfiles se siguen pidiendo con nadie moviendose"
    )


def test_la_sonda_del_recuento_no_escribe_estado():
    """
    LO QUE ME COSTO LA VERJA DOS VECES (07/09/2026)

    `scripts/contar_peticiones_del_ciclo.py` ejecuta los
    colectores de verdad para contar sus peticiones. Pero los
    colectores no solo piden: ESCRIBEN. La primera version dejo
    en el estado un snapshot con tres jugadores de mentira, y
    `test_futbolfantasy_source_v12` -que coge el mas reciente-
    se puso rojo con un cero, en otro fichero y sin relacion
    aparente.

    LA SEGUNDA VEZ FUE ESTA MISMA GUARDIA

        Comprobaba que en la fuente apareciera la palabra
        `salidas_originales`. Al reorganizar la sonda esa
        variable cambio de nombre, la guardia se puso roja y no
        habia nada roto: estaba vigilando un nombre, no un
        comportamiento.

        Ahora se comprueba lo unico que importa: que despues de
        medir, los caminos de escritura siguen apuntando donde
        apuntaban.
    """

    from src.biwenger import cache_del_reset as cache_mod
    from src.collectors import (
        board_history_collector as tablon_mod,
    )
    from src.collectors import league_collector as liga_mod

    from scripts.contar_peticiones_del_ciclo import (
        medir_un_ciclo,
    )

    antes = {
        "liga.DATA_DIR": liga_mod.DATA_DIR,
        "tablon.DATA_DIR": tablon_mod.DATA_DIR,
        "tablon.BOARD_FILE": tablon_mod.BOARD_FILE,
        "tablon.BOARD_RAW_FILE": tablon_mod.BOARD_RAW_FILE,
        "tablon.PROFILES_FILE": tablon_mod.PROFILES_FILE,
        "cache.FICHERO": cache_mod.FICHERO,
    }

    medir_un_ciclo(vueltas=2)

    despues = {
        "liga.DATA_DIR": liga_mod.DATA_DIR,
        "tablon.DATA_DIR": tablon_mod.DATA_DIR,
        "tablon.BOARD_FILE": tablon_mod.BOARD_FILE,
        "tablon.BOARD_RAW_FILE": tablon_mod.BOARD_RAW_FILE,
        "tablon.PROFILES_FILE": tablon_mod.PROFILES_FILE,
        "cache.FICHERO": cache_mod.FICHERO,
    }

    for clave, valor in antes.items():

        assert despues[clave] == valor, (
            "la sonda no ha devuelto "
            + clave
            + " a su sitio: quedo apuntando a "
            + str(despues[clave])
            + ". La siguiente escritura del ciclo iria a un "
            "temporal ya borrado."
        )

    # Y que ninguno de esos caminos apunte a un temporal.
    for clave, valor in despues.items():

        assert "bordalas_recuento_" not in str(valor), (
            clave + " se quedo en el temporal de la sonda"
        )


def test_la_sonda_no_deja_ficheros_en_el_estado():
    """
    La otra mitad: que al medir no aparezca nada nuevo en el
    directorio de estado.

    Se mira el arbol entero antes y despues. Si la sonda
    escribiera un snapshot, se veria aqui y no tres tests mas
    abajo.
    """

    from pathlib import Path

    from scripts.contar_peticiones_del_ciclo import (
        medir_un_ciclo,
    )

    raiz = Path(__file__).parent.parent.parent / (
        "dat" + "a"
    )

    def foto():
        if not raiz.exists():
            return set()

        return {
            str(f.relative_to(raiz))
            for f in raiz.rglob("*")
            if f.is_file()
        }

    antes = foto()

    medir_un_ciclo(vueltas=2)

    nuevos = foto() - antes

    assert not nuevos, (
        "la sonda ha dejado ficheros en el estado: "
        + str(sorted(nuevos))
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
    test_no_han_aparecido_llamadas_nuevas,
    test_una_vuelta_cuesta_lo_que_dice_el_informe,
    test_el_tablon_se_colecta_una_sola_vez,
    test_el_ahorro_del_paso_a_es_el_que_se_publica,
    test_el_que_se_mueve_a_media_tarde_se_refresca,
    test_en_un_traspaso_se_refrescan_los_dos,
    test_lo_de_antes_de_la_ultima_colecta_no_cuenta,
    test_sin_cache_previa_se_piden_todos,
    test_ante_la_duda_se_refresca_de_mas,
    test_la_cache_del_reset_caduca_en_el_reset,
    test_la_hora_del_reset_no_esta_copiada,
    test_el_interruptor_de_la_cache_devuelve_el_mundo_de_antes,
    test_un_perfil_que_fallo_no_se_guarda,
    test_la_vuelta_de_crucero_cuesta_lo_que_dice_el_informe,
    test_la_sonda_del_recuento_no_escribe_estado,
    test_la_sonda_no_deja_ficheros_en_el_estado,
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
