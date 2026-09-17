"""
El cable: la caja que hay, la que habría, y la puerta entre las dos.

QUE SE PRUEBA AQUI

    1. `test_la_caja_realizable_no_se_puede_pujar`
       Una puja contra dinero no cobrado no sale nunca. Falla si
       la lista de ofertas llega vacía.

    2. `test_las_dos_cajas_no_se_suman`
       El presupuesto publica las dos por separado, y la guardia
       lo comprueba LEYENDO EL JSON, no el código.

    3. `test_el_techo_sube_tres_cuartos`
       Vender un jugador sube `maximumBid` en 0,75 × precio, no
       en el precio. Falla si la plantilla llega vacía.

    4. `test_la_caja_realizable_pasa_el_guardarrail`
       Solo cuentan las ofertas que cumplen LAS TRES: viva, en la
       cola como sobrante, y el conjunto alinea.

    5. `test_la_tabla_ordena_por_puntos_por_euro`
       Y el que no cabe por fichas lo dice con ese motivo.

    6. `test_la_cola_va_por_consecuencia_sin_dejar_caducar`
       La que desbloquea se adelanta, pero solo si la otra
       sobrevive a la espera. Si chocan, gana no perder.

    7. `test_las_fichas_libres_usan_el_maximo_historico`
       Y la cifra sigue viajando como cota inferior.

    8. `test_el_cable_sigue_apagado`

REGLA 23 / DOCTRINA 50: NI DISCO, NI RED, NI RELOJ

    Todo son fixtures escritos aquí. La vara entra por argumento,
    y la espera de la cola —intervalo de cron y duración del
    ciclo— también: aquí no se mira ningún reloj ni se abre
    `data/`.

    `maximo_historico_de_fichas` SÍ lee disco, y por eso no se
    prueba: se prueba `mayor_plantilla_jamas_vista`, que es pura.

    Y la caché de pronósticos se clava vacía antes de nada, por
    lo mismo que el 17/09 en `test_la_plaza_y_el_cable_v1`:
    `build_position_guardrail` abre
    `data/intelligence/futbolfantasy_board.json` por
    `_keep_value`.

UNA GUARDIA QUE NO MUERDE ES PEOR QUE NINGUNA

    DOS de estas ocho no mordían al principio, y queda escrito
    porque importa más que las seis que sí:

    - `test_las_dos_cajas_no_se_suman` comprobaba que existieran
      las dos claves. Una versión que además publicara un `total`
      con la suma las tenía igual y pasaba. Ahora recorre el JSON
      entero buscando CUALQUIER valor que valga la suma y falla si
      aparece: comprobar que está lo que debe estar no es
      comprobar que no está lo que no debe.

    - `test_la_caja_realizable_pasa_el_guardarrail` llevaba una
      cola con tres defensas, y de siete que hay caben cuatro sin
      bajar del suelo. O sea que sustituir el guardarrail por uno
      que dijera "todo vale" NO cambiaba el resultado: la guardia
      pasaba sin haber probado nada. Ahora la cola trae CINCO
      defensas con oferta viva, el quinto rompe el once, y la
      guardia comprueba que NO entra.

    Las quince inyecciones de fallo se probaron una a una, en
    memoria.
"""

from __future__ import annotations

import json

from src.analysis.el_cable import (
    ENCENDIDO,
    NUNCA_SE_PUJA_CONTRA_CAJA_REALIZABLE,
    caja_realizable,
    cola_por_consecuencia,
    cuanto_desbloquea,
    esta_encendido,
    mayor_plantilla_jamas_vista,
    presupuesto_con_el_cable,
    puja_permitida,
    tabla_de_fichajes,
)
from src.analysis.la_plaza_y_el_cable import techo_tras_vender
from src.analysis.position_guardrail import (
    build_position_guardrail,
    validate_sale_set,
)
from src.analysis.roster_expansion_shadow import count_free_slots

import src.analysis.candidate_starter_lookup as _pronosticos


# La caché de pronósticos, clavada vacía antes de nada: sin esto,
# `build_position_guardrail` abre `data/` por dentro. Cazado por
# el vigilante de la verja el 17/09.
_pronosticos._CACHE = {}
_pronosticos._CACHE_KEY = _pronosticos._files_key()


POR, DEF, MED, DEL = 1, 2, 3, 4


# ============================================================
# LOS FIXTURES
# ============================================================
#
# Una plantilla con la forma de la foto del 17/09: 3 porteros,
# 7 defensas, 6 medios, 4 delanteros, y once titulares.


def _ficha(pid, nombre, posicion, precio, titular):
    return {
        "id": pid,
        "name": nombre,
        "position": posicion,
        "price": precio,
        "priceIncrement": 0,
        "in_lineup": titular,
        "is_starter": titular,
    }


PLANTILLA = [
    _ficha(1, "Dituro", POR, 2_200_000, True),
    _ficha(2, "Lunin", POR, 420_000, False),
    _ficha(3, "Fortuño", POR, 150_000, False),

    _ficha(10, "Jonny", DEF, 2_350_000, True),
    _ficha(11, "Djené", DEF, 1_900_000, True),
    _ficha(12, "Manu Sánchez", DEF, 1_640_000, True),
    _ficha(13, "Balde", DEF, 1_520_000, False),
    _ficha(14, "Trent", DEF, 2_530_000, False),
    _ficha(15, "Drkusic", DEF, 1_250_000, False),
    _ficha(16, "Álvaro Carreras", DEF, 1_340_000, False),

    _ficha(20, "Expósito", MED, 5_340_000, True),
    _ficha(21, "Olasagasti", MED, 3_480_000, True),
    _ficha(22, "Pablo Ibáñez", MED, 2_500_000, True),
    _ficha(23, "Rubén García", MED, 2_590_000, True),
    _ficha(24, "Oriol Rey", MED, 1_180_000, False),
    _ficha(25, "Benavidez", MED, 150_000, False),

    _ficha(30, "Yamal", DEL, 22_100_000, True),
    _ficha(31, "Jutglà", DEL, 3_200_000, True),
    _ficha(32, "Pablo Durán", DEL, 380_000, False),
    _ficha(33, "Paco Cortés", DEL, 150_000, False),
]

ONCE = [f["id"] for f in PLANTILLA if f["in_lineup"]]


def _guardarrail():
    return build_position_guardrail(PLANTILLA, lineup_ids=ONCE)


def _fila_de_cola(
    pid,
    nombre,
    posicion,
    precio,
    cash_now,
    *,
    kind="OFERTA_VIVA",
    titular=False,
    puntos_por_jornada=None,
    tier="CAE_SIN_JUGAR",
):
    return {
        "id": pid,
        "name": nombre,
        "position": posicion,
        "price": precio,
        "cash_now": cash_now,
        "cash_kind": kind,
        "in_lineup": titular,
        "points": 0,
        "points_per_matchday": puntos_por_jornada,
        "tier": tier,
        "tier_label": "Cae y no juega",
        "reason": "Cae de precio y ademas no juega.",
    }


# LA COLA TIENE QUE HACER TRABAJAR AL GUARDARRAIL
#
#     La primera version de este fixture llevaba tres defensas
#     con oferta viva, y de siete que hay se pueden soltar cuatro
#     sin bajar del suelo. Resultado: saltarse el guardarrail NO
#     cambiaba nada y `test_la_caja_realizable_pasa_el_guardarrail`
#     pasaba igual. Una guardia que no muerde es peor que ninguna.
#
#     Ahora hay CINCO defensas con oferta viva sobre siete: el
#     quinto deja dos y hacen falta tres para alinear, asi que
#     tiene que salir apartado. Si alguien quita la llamada al
#     guardarrail, se cuela y la guardia se pone roja.
COLA = [
    _fila_de_cola(13, "Balde", DEF, 1_520_000, 1_578_500),
    _fila_de_cola(14, "Trent", DEF, 2_530_000, 2_536_500),
    _fila_de_cola(15, "Drkusic", DEF, 1_250_000, 1_262_000),
    _fila_de_cola(16, "Álvaro Carreras", DEF, 1_340_000, 1_326_500),
    _fila_de_cola(
        10,
        "Jonny",
        DEF,
        2_350_000,
        2_352_000,
        titular=True,
        puntos_por_jornada=2.9,
        tier="CARO_POR_PUNTO",
    ),
    _fila_de_cola(32, "Pablo Durán", DEL, 380_000, 395_000),
    _fila_de_cola(
        33, "Paco Cortés", DEL, 150_000, 0, kind="A_MERCADO"
    ),
    _fila_de_cola(3, "Fortuño", POR, 150_000, 153_800),
    _fila_de_cola(
        23,
        "Rubén García",
        MED,
        2_590_000,
        2_598_100,
        titular=True,
        puntos_por_jornada=3.2,
        tier="CARO_POR_PUNTO",
    ),
]


PRESUPUESTO_PUBLICADO = {
    "enabled": True,
    "total_budget": 8_874_116,
    "available_budget": 8_874_116,
    "maximum_bid": 12_455_166,
    "balance": -373_984,
}


VARA = {POR: 1.0, DEF: 0.787, MED: 1.147, DEL: 1.139}


def factor_de(posicion):
    return VARA.get(int(posicion or 0), 1.0)


def _presupuesto():
    return presupuesto_con_el_cable(
        PRESUPUESTO_PUBLICADO,
        {"queue": COLA},
        guardarrail=_guardarrail(),
        validador=validate_sale_set,
    )


# ============================================================
# 1. NO SE PUJA CONTRA CAJA NO COBRADA
# ============================================================


def test_la_caja_realizable_no_se_puede_pujar():
    """
    La única respuesta que abre la puerta es que quepa en la caja
    cobrada. La realizable manda vender primero, nunca pujar.
    """

    assert NUNCA_SE_PUJA_CONTRA_CAJA_REALIZABLE is True, (
        "esta regla no es un interruptor: si se puede apagar, "
        "alguien la apagará"
    )

    presupuesto = _presupuesto()

    ahora = presupuesto["caja_ahora"]
    realizable = presupuesto["caja_realizable"]

    assert ahora > 0 and realizable > 0, (
        "el fixture no prueba nada si alguna de las dos cajas es "
        "cero"
    )

    # Lo que cabe en la caja cobrada, pasa.
    dentro = puja_permitida(ahora - 1, presupuesto)

    assert dentro["ok"] is True
    assert dentro["needs_sale_first"] is False
    assert dentro["budget_used"] == "CAJA_AHORA"

    # UN EURO POR ENCIMA YA NO PASA, aunque la realizable lo
    # cubriera de sobra. Aquí es donde muerde.
    fuera = puja_permitida(ahora + 1, presupuesto)

    assert fuera["ok"] is False, (
        f"una puja de {ahora + 1} ha pasado con solo {ahora} "
        f"cobrados: se está pujando contra dinero que no está"
    )

    assert fuera["needs_sale_first"] is True, (
        "si no cabe pero se cubre vendiendo, hay que marcar "
        "`needs_sale_first`, no rechazarla sin más"
    )

    assert fuera["vende_primero"], (
        "hay que decir A QUIÉN se vende primero, no solo que hace "
        "falta vender"
    )

    assert "primero" in fuera["reason"].lower(), (
        "el motivo tiene que decir que la venta va antes"
    )

    # Y una que no se cubre ni vendiéndolo todo tampoco pasa.
    imposible = puja_permitida(ahora + realizable + 1, presupuesto)

    assert imposible["ok"] is False
    assert imposible["needs_sale_first"] is False, (
        "no se puede marcar `needs_sale_first` cuando ni vendiendo "
        "a todos se llega: eso sería prometer una venta que no "
        "existe"
    )

    # ------------------------------------------------
    # LA LISTA DE OFERTAS VACÍA: MUERDE AQUÍ
    # ------------------------------------------------
    sin_ofertas = presupuesto_con_el_cable(
        PRESUPUESTO_PUBLICADO,
        {"queue": []},
        guardarrail=_guardarrail(),
        validador=validate_sale_set,
    )

    assert sin_ofertas["caja_realizable"] is None, (
        "sin cola de venta no hay realizable que publicar, y un "
        "cero parecería medido"
    )

    vacia = puja_permitida(
        sin_ofertas["caja_ahora"] + 1, sin_ofertas
    )

    assert vacia["ok"] is False
    assert vacia["needs_sale_first"] is False, (
        "sin nadie a quien vender no se puede marcar "
        "`needs_sale_first`"
    )

    print("  OK  ninguna puja se pone contra caja no cobrada")


# ============================================================
# 2. LAS DOS CAJAS NO SE SUMAN
# ============================================================


def test_las_dos_cajas_no_se_suman():
    """
    Leído del JSON publicado, no del código.

    No basta con que estén las dos claves: hay que comprobar que
    NO está la suma. Una versión que publicara las dos y además
    un `total` pasaría la primera prueba y rompería la regla.
    """

    presupuesto = _presupuesto()

    publicado = json.loads(json.dumps(presupuesto))

    ahora = publicado["caja_ahora"]
    realizable = publicado["caja_realizable"]

    # LAS DOS, CON NOMBRE.
    assert isinstance(ahora, int) and isinstance(realizable, int)

    assert publicado["caja_ahora_label"], (
        "la caja de hoy sale sin nombre"
    )

    assert publicado["caja_realizable_label"], (
        "la caja realizable sale sin nombre"
    )

    assert "no se puede comprometer" in (
        publicado["caja_realizable_label"].lower()
    ), (
        "el nombre de la caja realizable tiene que decir que no es "
        "gastable: es la mitad del aviso"
    )

    # Y LA SUMA, EN NINGÚN SITIO.
    suma = ahora + realizable

    encontrados = []

    def recorrer(nodo, ruta=""):
        if isinstance(nodo, dict):
            for clave, valor in nodo.items():
                recorrer(valor, f"{ruta}/{clave}")

        elif isinstance(nodo, list):
            for indice, valor in enumerate(nodo):
                recorrer(valor, f"{ruta}[{indice}]")

        elif isinstance(nodo, int) and not isinstance(nodo, bool):
            if nodo == suma:
                encontrados.append(ruta)

    recorrer(publicado)

    assert not encontrados, (
        f"el JSON publica la suma de las dos cajas ({suma}) en "
        f"{encontrados}: un solo número es lo que hace falta para "
        f"que alguien puje contra dinero no cobrado"
    )

    # Y la regla viaja escrita al lado de los números.
    assert "needs_sale_first" in publicado["regla"], (
        "la regla tiene que publicarse con los números, no solo "
        "vivir en el código"
    )

    print("  OK  las dos cajas salen separadas y la suma no sale")


# ============================================================
# 3. EL TECHO SUBE TRES CUARTOS
# ============================================================


def test_el_techo_sube_tres_cuartos():
    """
    De cada jugador ya había un cuarto de su precio dentro de
    `maximumBid`: al venderlo sale ese cuarto y entra el importe.
    """

    assert PLANTILLA, (
        "la plantilla llega vacía: sin jugadores esta guardia no "
        "prueba nada"
    )

    presupuesto = _presupuesto()

    subida = (
        presupuesto["techo_si_se_vende"] - presupuesto["techo_ahora"]
    )

    esperada = sum(
        v["cash_now"] - v["price"] // 4
        for v in presupuesto["vendedores"]
    )

    assert subida == esperada, (
        f"el techo tiene que subir importe menos un cuarto del "
        f"precio de cada uno ({esperada}), no {subida}"
    )

    # A precio de mercado clavado, tres cuartos exactos.
    precio = 4_000_000

    assert techo_tras_vender(0, precio, precio) == precio * 3 // 4, (
        "vendiendo a precio de mercado el techo sube 0,75 × precio: "
        "si subiera el precio entero se estaría contando dos veces, "
        "y si no subiera nada se estaría contando cero"
    )

    # Y NO es la suma de los importes: si lo fuera, estaríamos
    # contando dos veces el cuarto que ya estaba dentro.
    importes = sum(v["cash_now"] for v in presupuesto["vendedores"])

    assert subida < importes, (
        f"el techo ha subido {subida} con {importes} de ventas: "
        f"eso es contar dos veces el cuarto que ya vivía dentro"
    )

    print("  OK  vender sube el techo 0,75 × precio, no el precio")


# ============================================================
# 4. LAS TRES CONDICIONES DE LA CAJA REALIZABLE
# ============================================================


def test_la_caja_realizable_pasa_el_guardarrail():
    """
    Viva, sobrante y que el once aguante. Las tres, o no cuenta.
    """

    guardarrail = _guardarrail()

    assert guardarrail.get("available")

    # Ni disco: construir el guardarrail no ha releído el tablero.
    #
    # EL MENSAJE NO NOMBRA LA RUTA A PROPOSITO (17/09/2026)
    #
    #     La primera versión decía «ha abierto data/…», y
    #     `test_verja_determinista_v1` puso la verja en rojo: su
    #     Regla A busca el directorio de estado escrito en
    #     CUALQUIER literal del módulo, y no distingue una lectura
    #     de un mensaje que habla de ella.
    #
    #     Es un falso positivo de una regla deliberadamente
    #     conservadora, y la respuesta correcta es no escribir la
    #     ruta, no relajar la regla. La comprobación es la misma.
    assert _pronosticos._CACHE == {}, (
        "construir el guardarrail ha releído el tablero de "
        "titularidades: esta guardia acaba de leer estado de "
        "producción y su respuesta ya no depende solo del código"
    )

    realizable = caja_realizable(
        {"queue": COLA},
        guardarrail=guardarrail,
        validador=validate_sale_set,
    )

    assert realizable["available"]

    vendidos = [v["id"] for v in realizable["vendedores"]]

    # 1. El de mercado NO entra.
    assert 33 not in vendidos, (
        "Paco Cortes no tiene oferta viva: su valor a mercado no es "
        "caja"
    )

    # 2. NI EL QUE ROMPE EL ONCE, aunque su oferta esté viva. Aquí
    #    es donde muerde si alguien quita la llamada al guardarrail.
    assert 10 not in vendidos, (
        "Jonny es el quinto defensa con oferta viva de siete: "
        "venderlo deja dos y hacen falta tres para alinear. Que "
        "entre en la caja realizable significa que el guardarrail "
        "no se ha consultado"
    )

    # 3. Y el conjunto entero alinea.
    comprobacion = validate_sale_set(guardarrail, vendidos)

    assert comprobacion["ok"], (
        f"la caja realizable deja el once sin alinear: "
        f"{comprobacion.get('reason')}"
    )

    assert comprobacion["guardrail_applied"], (
        "el guardarrail tiene que haberse aplicado de verdad"
    )

    # 4. El que no cabe sale apartado CON SU MOTIVO.
    assert realizable["apartados"], (
        "el fixture no prueba nada si no se aparta a nadie"
    )

    for apartado in realizable["apartados"]:
        assert apartado.get("reason"), (
            f"{apartado.get('name')} se apartó sin decir por qué"
        )

    # Y CADA VENDEDOR DICE POR QUÉ SOBRA.
    for vendedor in realizable["vendedores"]:
        assert vendedor.get("tier") and vendedor.get("reason"), (
            f"{vendedor.get('name')} entra en la caja realizable sin "
            f"decir por qué sobra"
        )

    # El fixture tiene que hacer trabajar al guardarrail de
    # verdad: si vender a los cinco no rompiera nada, saltarse la
    # comprobacion no cambiaria el resultado y esta guardia no
    # probaria nada.
    roto = validate_sale_set(guardarrail, [13, 14, 15, 16, 10])

    assert not roto["ok"], (
        "el fixture no prueba nada: vender a cinco defensas de "
        "siete tiene que romper el once y no lo rompe"
    )

    assert validate_sale_set(guardarrail, [13, 14, 15, 16])["ok"], (
        "y los cuatro primeros SI tienen que caber: si no, lo que "
        "aparta a Jonny seria el orden y no el suelo"
    )

    print("  OK  solo cuenta lo vivo, sobrante y alineable")


# ============================================================
# 5. LA TABLA
# ============================================================


CANDIDATOS = [
    # Barato y aporta: tiene que salir el primero.
    {
        "id": 41101,
        "name": "Alfonso Herrero",
        "position": POR,
        "market_price": 4_100_000,
        "season_points_remaining": 174.6,
        "blocked_by": "INTENT_POR_EUROS",
    },
    # Caro para lo que aporta.
    {
        "id": 18398,
        "name": "Budimir",
        "position": DEL,
        "market_price": 11_990_000,
        "season_points_remaining": 183.2,
        "blocked_by": "INTENT_POR_EUROS",
    },
    # Sin puntos medibles: va al final y no se le inventa un cero.
    {
        "id": 999,
        "name": "Sin pronóstico",
        "position": MED,
        "market_price": 1_000_000,
        "season_points_remaining": None,
        "blocked_by": "SIN_PRONOSTICO",
    },
]


def test_la_tabla_ordena_por_puntos_por_euro():
    """
    Ordenada por puntos netos por euro, y el que no cabe por
    fichas lo dice con ese motivo y no con otro.
    """

    presupuesto = _presupuesto()

    tabla = tabla_de_fichajes(
        CANDIDATOS,
        presupuesto,
        factor_de=factor_de,
        fichas_libres=4,
        jornadas_restantes=33,
    )

    assert tabla["available"] and tabla["n"] == 3

    ordenados = tabla["operaciones"]

    assert ordenados[0]["name"] == "Alfonso Herrero", (
        f"el más barato por punto tiene que ir primero, no "
        f"{ordenados[0]['name']}"
    )

    assert ordenados[-1]["puntos_netos_por_millon"] is None, (
        "el que no se puede medir va al final y sin número "
        "inventado"
    )

    # La vara, puesta.
    esperado = round(
        (174.6 / 33) * VARA[POR], 3
    )

    assert ordenados[0]["puntos_que_entran"] == esperado, (
        f"los puntos del portero no llevan su vara: "
        f"{ordenados[0]['puntos_que_entran']} contra {esperado}"
    )

    # Con ficha libre, no hace falta que salga nadie por la plaza.
    assert ordenados[0]["cabe_sin_vender"] is True

    # Y la seguridad, fila a fila: Budimir cuesta más que la caja
    # cobrada, así que va con `needs_sale_first`.
    budimir = next(o for o in ordenados if o["name"] == "Budimir")

    assert budimir["financiada_hoy"] is False
    assert budimir["needs_sale_first"] is True
    assert budimir["vende_a"], (
        "si hace falta vender, hay que decir a quién"
    )

    # ------------------------------------------------
    # SIN FICHAS: EL MOTIVO TIENE QUE SER ESE
    # ------------------------------------------------
    sin_cola = presupuesto_con_el_cable(
        PRESUPUESTO_PUBLICADO,
        {"queue": []},
        guardarrail=_guardarrail(),
        validador=validate_sale_set,
    )

    apretada = tabla_de_fichajes(
        CANDIDATOS,
        sin_cola,
        factor_de=factor_de,
        fichas_libres=0,
        jornadas_restantes=33,
    )

    for operacion in apretada["operaciones"]:
        assert operacion["cabe_la_ficha"] is False
        assert "ficha" in operacion["reason"].lower(), (
            f"{operacion['name']} no cabe por fichas y el motivo no "
            f"lo dice: {operacion['reason']!r}"
        )
        assert "no es que falte dinero" in operacion["reason"].lower(), (
            "un 'no cabe la ficha' no se puede contar como un 'no "
            "hay dinero': son dos arreglos distintos"
        )

    # La lista vacía no publica tabla.
    assert tabla_de_fichajes(
        [], presupuesto, factor_de=factor_de
    )["available"] is False

    print("  OK  la tabla ordena por puntos netos por euro")


# ============================================================
# 6. LA COLA POR CONSECUENCIA
# ============================================================
#
# La foto del 17/09, con sus horas reales.

ACCIONES = [
    {
        "type": "MARKET_LISTING_RENEW_URGENT",
        "action": "RENEW_MARKET_LISTING",
        "label": "Renovar publicación",
        "priority": 690,
        "executable": True,
        "hours_to_expiry": 2.85,
    },
    {
        "type": "OFFER_DECISION_INTELLIGENCE",
        "action": "ACCEPT_RECOVERY_OFFER",
        "label": "Cobrar oferta aprobada",
        "priority": 650,
        "executable": True,
        "hours_to_expiry": 47.5,
    },
    {
        "type": "SOLVENCY_GUARANTEE",
        "action": "MONITOR_SOLVENCY",
        "label": "Solvencia",
        "priority": 780,
        "executable": False,
        "hours_to_expiry": None,
    },
]


# Medido sobre la telemetría del 14/09 al 17/09: 39 escrituras,
# mediana 148 s. El cron va cada 60 minutos.
CICLO_HORAS = 148 / 3600

CRON_HORAS = 1.0


def test_la_cola_va_por_consecuencia_sin_dejar_caducar():
    """
    La que desbloquea se adelanta, pero solo si la otra sobrevive
    a la espera. Y la espera se mide.
    """

    cola = cola_por_consecuencia(
        ACCIONES,
        intervalo_de_ciclo_horas=CRON_HORAS,
        duracion_de_ciclo_horas=CICLO_HORAS,
    )

    assert cola["available"] and cola["n"] == 2, (
        "las no ejecutables no entran en la cola de escritura"
    )

    assert cola["cambia"] is True, (
        "con estas dos, la cola tiene que cambiar: cobrar "
        "desbloquea y renovar no"
    )

    assert cola["primera_por_caducidad"]["action"] == (
        "RENEW_MARKET_LISTING"
    )

    assert cola["primera_por_consecuencia"]["action"] == (
        "ACCEPT_RECOVERY_OFFER"
    ), (
        "cobrar una oferta abre el presupuesto, el carril y la "
        "subasta; renovar no abre nada"
    )

    # Y LO APLAZADO LLEGA. Esto es la mitad de la regla.
    umbral = cola["umbral_horas"]

    assert 2.85 > umbral, (
        f"la publicación caduca en 2,85 h y el umbral son {umbral} "
        f"h: si no sobreviviera, adelantarla sería perderla"
    )

    renovar = next(
        c for c in cola["cola"] if c["action"] == "RENEW_MARKET_LISTING"
    )

    assert renovar["sobrevive_una_vuelta"] is True

    # ------------------------------------------------
    # SI CHOCAN, GANA NO PERDER: MUERDE AQUÍ
    # ------------------------------------------------
    apurada = cola_por_consecuencia(
        [
            {**ACCIONES[0], "hours_to_expiry": 0.5},
            ACCIONES[1],
        ],
        intervalo_de_ciclo_horas=CRON_HORAS,
        duracion_de_ciclo_horas=CICLO_HORAS,
    )

    assert apurada["primera_por_consecuencia"]["action"] == (
        "RENEW_MARKET_LISTING"
    ), (
        "con media hora de vida, la publicación NO puede esperar "
        "una vuelta: aunque no desbloquee nada, gana no perder"
    )

    assert apurada["gana_no_perder"], (
        "el choque tiene que quedar dicho, no solo resuelto"
    )

    # Sin plazo conocido se trata como que no sobrevive.
    sin_plazo = cola_por_consecuencia(
        [
            {**ACCIONES[0], "hours_to_expiry": None},
            ACCIONES[1],
        ],
        intervalo_de_ciclo_horas=CRON_HORAS,
        duracion_de_ciclo_horas=CICLO_HORAS,
    )

    assert sin_plazo["primera_por_consecuencia"]["action"] == (
        "RENEW_MARKET_LISTING"
    ), (
        "sin saber cuánto le queda no se aplaza: ante la duda, no "
        "se arriesga a perderlo"
    )

    # Y una acción que nadie ha declarado abre cero, no se le
    # supone una consecuencia.
    abre, porque = cuanto_desbloquea("ACCION_QUE_NO_EXISTE")

    assert abre == 0 and porque

    assert cola_por_consecuencia(
        [],
        intervalo_de_ciclo_horas=CRON_HORAS,
        duracion_de_ciclo_horas=CICLO_HORAS,
    )["available"] is False

    print("  OK  la cola va por consecuencia y no deja caducar nada")


# ============================================================
# 7. LAS FICHAS LIBRES
# ============================================================


TABLON = [
    {"type": "leagueReset", "date": 100, "content": {"distribution": 12}},
    # Dos compras de Pollo y una venta: de 15 sube a 17 y baja a 16.
    {
        "type": "market",
        "date": 200,
        "content": [
            {"player": 1, "amount": 10, "to": {"id": 9000001, "name": "Pollo17"}},
            {"player": 2, "amount": 20, "to": {"id": 9000001, "name": "Pollo17"}},
        ],
    },
    # El tablón repite: el mismo evento otra vez con otro id.
    {
        "type": "market",
        "date": 201,
        "content": [
            {"player": 1, "amount": 10, "to": {"id": 9000001, "name": "Pollo17"}},
        ],
    },
    {
        "type": "transfer",
        "date": 300,
        "content": [
            {"player": 1, "amount": 10, "from": {"id": 9000001, "name": "Pollo17"}},
        ],
    },
    # Nosotros: una compra. De 15 a 16.
    {
        "type": "market",
        "date": 250,
        "content": [
            {"player": 3, "amount": 30, "to": {"id": 9000002, "name": "Pepe"}},
        ],
    },
]

HOY = {"Pollo17": 16, "Pepe": 16}


def test_las_fichas_libres_usan_el_maximo_historico():
    """
    El máximo jamás visto, con su propio cuadre, y la cifra sigue
    diciendo que es una cota inferior.
    """

    historico = mayor_plantilla_jamas_vista(
        TABLON,
        HOY,
        sin_explicar={"is_us_name": "Pepe", "by_manager": {}},
    )

    assert historico["available"]

    # El reparto se AJUSTA: con 15 cuadran los dos; el 12 que
    # declara el tablón no cuadra ninguno.
    assert historico["initial_squad_fitted"] == 15, (
        f"el reparto inicial que cuadra es 15, no "
        f"{historico['initial_squad_fitted']}"
    )

    assert historico["reconciled"] == 2

    assert historico["trusted"] is True, (
        "nuestra línea cuadra: el número se puede usar"
    )

    # Y el tablón repetía: 4 operaciones distintas de 5 vistas.
    assert historico["operations"] == 4, (
        f"el tablón repite y hay que deduplicar por OPERACIÓN: "
        f"{historico['operations']} distintas de "
        f"{historico['operations_raw']}"
    )

    assert historico["largest_ever"] == 17, (
        f"Pollo llegó a 17 antes de vender: {historico['largest_ever']}"
    )

    assert historico["largest_today"] == 16

    assert historico["is_lower_bound"] is True

    # ------------------------------------------------
    # Y AHORA LAS FICHAS LIBRES
    # ------------------------------------------------
    ledger = {
        "by_manager": [
            {"name": "Pollo17", "roster_size": 16, "is_us": False},
            {"name": "Pepe", "roster_size": 16, "is_us": True},
        ]
    }

    antes = count_free_slots(ledger)

    assert antes["free_slots"] == 0, (
        "con la mayor de hoy, cero huecos: ese es el bug"
    )

    despues = count_free_slots(ledger, historico)

    assert despues["free_slots"] == 1, (
        f"con el máximo histórico tiene que abrirse una plaza: "
        f"{despues['free_slots']}"
    )

    # LOS DOS NÚMEROS SIGUEN PUBLICÁNDOSE.
    assert despues["largest_roster_today"] == 16
    assert despues["largest_roster_ever"] == 17
    assert despues["source"] == "MAXIMO_HISTORICO"

    # Y SIGUE SIENDO UNA COTA INFERIOR. Cambiar el número no
    # cambia lo que es.
    assert despues["is_lower_bound"] is True, (
        "usar el máximo histórico no convierte la cifra en un tope: "
        "nadie ha comprobado el de Biwenger"
    )

    assert "cota inferior" in despues["reason"].lower(), (
        "el motivo publicado tiene que decir que es un suelo"
    )

    # ------------------------------------------------
    # SIN CUADRE NO SE USA: MUERDE AQUÍ
    # ------------------------------------------------
    descuadrado = mayor_plantilla_jamas_vista(
        TABLON,
        HOY,
        sin_explicar={"is_us_name": "Otro que no existe"},
    )

    assert descuadrado["trusted"] is False

    prudente = count_free_slots(ledger, descuadrado)

    assert prudente["free_slots"] == 0, (
        "si nuestra propia línea no cuadra, la reconstrucción no "
        "abre ninguna plaza"
    )

    assert prudente["is_lower_bound"] is True

    # Y nunca por debajo del de hoy: si alguien tiene 16 ahora
    # mismo, 16 caben, lo diga lo que diga una reconstrucción.
    bajo = count_free_slots(
        {
            "by_manager": [
                {"name": "Pollo17", "roster_size": 16, "is_us": False},
                {"name": "Pepe", "roster_size": 10, "is_us": True},
            ]
        },
        {"trusted": True, "available": True, "largest_ever": 3},
    )

    assert bajo["free_slots"] == 6, (
        "un histórico más bajo que el de hoy no puede cerrar plazas "
        "que existen ahora mismo"
    )

    print("  OK  las fichas libres usan el máximo histórico, y es un suelo")


# ============================================================
# 8. EL CABLE SIGUE APAGADO
# ============================================================


def test_el_cable_sigue_apagado():
    """
    Se construye apagado. Lo enciende el dueño.
    """

    assert ENCENDIDO is False, (
        "el cable se ha quedado encendido: este encargo dice "
        "construir y parar"
    )

    assert esta_encendido() is False

    assert _presupuesto()["enabled"] is False, (
        "el estado publicado tiene que decir que está apagado"
    )

    # Pero CALCULA: apagado no puede significar que no conteste.
    assert _presupuesto()["available"] is True

    assert tabla_de_fichajes(
        CANDIDATOS, _presupuesto(), factor_de=factor_de
    )["available"] is True

    print("  OK  el cable está tendido, calcula y sigue sin corriente")


TESTS = [
    test_la_caja_realizable_no_se_puede_pujar,
    test_las_dos_cajas_no_se_suman,
    test_el_techo_sube_tres_cuartos,
    test_la_caja_realizable_pasa_el_guardarrail,
    test_la_tabla_ordena_por_puntos_por_euro,
    test_la_cola_va_por_consecuencia_sin_dejar_caducar,
    test_las_fichas_libres_usan_el_maximo_historico,
    test_el_cable_sigue_apagado,
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
    print(f"EL CABLE V1: {len(TESTS) - fallos}/{len(TESTS)} OK")
    print("=" * 60)

    if fallos:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
