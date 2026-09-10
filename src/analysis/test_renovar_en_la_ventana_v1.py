"""
Renovar en la ventana, y que escribir no pueda vender.

POR QUE ESTA GUARDIA (10/09/2026)

    Hasta hoy Pepe no escribia NADA contra Biwenger. A partir de
    esta rama si, y lo primero que escribe es una renovacion.

    El endpoint de renovar -POST /market, type "sell"- vive al
    lado del de vender -PUT /offers/{id}-. Confundirlos una vez
    seria soltar a un titular el dia de la jornada.

LO MEDIDO, QUE ES LO QUE SOSTIENE LA POLITICA (10/09/2026)

    Sobre las 85 fotos del 11 al 17/08, con sellos de tiempo del
    propio Biwenger:

        · Un listado vive 48,0 h EXACTAS. 47 de 47.
        · Las ofertas del Computer caducan a las 07:00. 57 de 65.
        · La tanda nueva nace entre 07:03 y 07:09. Las 54,
          siete dias seguidos.
        · Un listado creado a las 06:42 -18 min antes del
          reset- recibio su oferta a las 07:04 del mismo dia.

    De ahi: renovar en la ventana no deja a nadie fuera de la
    tanda, y la oferta que se mata tiene minutos de vida.

LO QUE SE PROTEGE

     1. Que el camino de renovar NO pueda vender, ni con las
        filas manipuladas.
     2. Que fuera de la ventana no se renueve nada.
     3. Que la zona de silencio pare la renovacion.
     4. Que nunca se renueve un listado SIN oferta viva.
     5. Que primero se cobre y despues se renueve.
     6. Que no se renueve dos veces al mismo en una ventana.
     7. Que no se renueve lo que llega de sobra a la proxima
        ventana.
     8. Que el tope sea un corte duro.
     9. Que la zona de silencio calcule la hora en MADRID, con
        su verano, y que se calle si no puede.
    10. Que se vea que se quedo sin hacer.

REGLA 24: NINGUNA GUARDIA PASA CON LAS MANOS VACIAS.

ESTAS GUARDIAS NO LEEN EL MUNDO: ni `data/`, ni red, ni reloj.

COMO SE USA

    python -m src.analysis.test_renovar_en_la_ventana_v1
"""

from __future__ import annotations

import tempfile

from datetime import datetime, timezone
from pathlib import Path

from src.actions.renovar_executor import renovar
from src.analysis.la_subasta import (
    VENTANA_MINUTOS,
    ventana_abierta,
)
from src.analysis.renovar_ofertas import (
    HORAS_ENTRE_VENTANAS,
    TOPE_DE_RENOVACIONES,
    VIDA_DE_UN_LISTADO_HORAS,
    filas_desde_lo_publicado,
    que_renovar,
)
from src.analysis.zona_de_silencio import (
    SILENCIO_DESDE,
    SILENCIO_HASTA,
    lo_que_se_quedo_sin_hacer,
    observacion_del_reset,
    permite_escribir,
)


# ============================================================
# EL MUNDO DE MENTIRA
# ============================================================

EN_LA_VENTANA = 300          # 5 min al reset


def _listado(
    nombre,
    identificador,
    caduca_en,
    oferta=1_000_000,
    precio=2_000_000,
):
    return {
        "id": identificador,
        "name": nombre,
        "listed_price": precio,
        "listing_hours_to_expiry": caduca_en,
        "offer_amount": oferta,
        "offer_hours_to_expiry": 0.2,
    }


def _ocho():
    """Ocho listados que piden renovacion, como los de hoy."""

    return [
        _listado(f"Jugador {i}", 100 + i, 4.0 + i)
        for i in range(8)
    ]


class ClienteEspia:
    """
    Un cliente de escritura que apunta TODO lo que se le llama.

    Si el camino de renovar tocara cualquier cosa que no sea
    `list_player_for_sale`, quedaria escrito aqui.
    """

    def __init__(self):
        self.llamadas = []

    def _apuntar(self, nombre, kwargs):
        self.llamadas.append((nombre, kwargs))

    def list_player_for_sale(self, **kwargs):
        self._apuntar("list_player_for_sale", kwargs)
        return {"sent": bool(kwargs.get("execute")), "success": True}

    # Todo lo que NO puede llegar a llamarse.
    def accept_offer(self, **kwargs):
        self._apuntar("accept_offer", kwargs)
        raise AssertionError(
            "el camino de renovar ha llamado a accept_offer"
        )

    def place_bid(self, **kwargs):
        self._apuntar("place_bid", kwargs)
        raise AssertionError(
            "el camino de renovar ha llamado a place_bid"
        )

    def reject_offer(self, **kwargs):
        self._apuntar("reject_offer", kwargs)
        raise AssertionError("renovar ha rechazado una oferta")

    def counter_offer(self, **kwargs):
        self._apuntar("counter_offer", kwargs)
        raise AssertionError("renovar ha contraofertado")

    def cancel_bid(self, **kwargs):
        self._apuntar("cancel_bid", kwargs)
        raise AssertionError("renovar ha cancelado una puja")

    def save_lineup(self, **kwargs):
        self._apuntar("save_lineup", kwargs)
        raise AssertionError("renovar ha tocado el once")


# ============================================================
# REGLA 24
# ============================================================

def test_hay_listados_que_comprobar():

    assert len(_ocho()) == 8, "sin listados no se prueba nada"

    assert VIDA_DE_UN_LISTADO_HORAS == 48.0, (
        "la vida medida de un listado ya no es 48 h: revisa la "
        "politica entera"
    )

    assert HORAS_ENTRE_VENTANAS == 24.0

    # Y que el mundo de mentira DE VERDAD produzca renovaciones:
    # si no, todas las guardias de abajo pasarian sin mirar nada.
    plan = que_renovar(
        _ocho(), EN_LA_VENTANA, puede_escribir=True
    )

    assert plan["count"] > 0, (
        "el fixture no genera ni una renovacion: estas guardias "
        "no probarian nada"
    )


# ============================================================
# 1. RENOVAR NO PUEDE VENDER
# ============================================================

def test_renovar_no_puede_vender():
    """
    La guardia que pidio el dueno, y la que mas importa.

    Se le pasan filas MANIPULADAS -con `offer_id`, con `accept`,
    con un tipo de operacion inventado- y el camino tiene que
    seguir haciendo una sola cosa: listar.
    """

    espia = ClienteEspia()

    manipuladas = [
        {
            "id": 101,
            "name": "Trampa 1",
            "listed_price": 1_000_000,
            "dying_offer": 900_000,

            # Todo esto es veneno: no puede tener ningun efecto.
            "offer_id": 55555,
            "accept": True,
            "type": "accept_offer",
            "operation": "SELL",
            "execute_sale": True,
        },
        {
            "id": 102,
            "name": "Trampa 2",
            "listed_price": 2_000_000,
            "dying_offer": 0,
            "action": "ACCEPT_RECOVERY_OFFER",
        },
    ]

    with tempfile.TemporaryDirectory() as carpeta:

        resultado = renovar(
            manipuladas,
            escritor=espia,
            en_vivo=True,
            ruta_del_libro=Path(carpeta) / "libro.jsonl",
        )

    assert espia.llamadas, (
        "no se ha llamado a nada: esta guardia no prueba nada"
    )

    metodos = {nombre for nombre, _ in espia.llamadas}

    assert metodos == {"list_player_for_sale"}, (
        f"el camino de renovar ha llamado a {metodos}"
    )

    # Y lo que se le mando es exactamente listar, con el precio.
    for nombre, kwargs in espia.llamadas:
        assert set(kwargs) <= {"player_id", "price", "execute"}, (
            f"a list_player_for_sale le llegan argumentos de "
            f"mas: {sorted(kwargs)}"
        )

    assert len(resultado["sent"]) == 2


def test_el_modulo_de_renovar_no_conoce_la_venta():
    """
    Ni siquiera puede alcanzarla: no importa nada que venda.

    Se mira el modulo cargado, no el texto del fichero: un
    `import` dentro de una funcion tambien contaria.
    """

    import src.actions.renovar_executor as ejecutor

    prohibidos = (
        "accept_offer",
        "execute_sale",
        "live_sale_executor",
        "sale_executor",
        "offers_to_collect",
    )

    nombres = dir(ejecutor)

    for prohibido in prohibidos:

        assert not any(
            prohibido in str(n) for n in nombres
        ), (
            f"el ejecutor de renovaciones conoce «{prohibido}»"
        )


def test_en_seco_no_escribe_nada():
    """
    `en_vivo=False` es el defecto y no manda nada.
    """

    espia = ClienteEspia()

    with tempfile.TemporaryDirectory() as carpeta:

        resultado = renovar(
            [
                {
                    "id": 1,
                    "name": "Uno",
                    "listed_price": 500_000,
                    "dying_offer": 1,
                }
            ],
            escritor=espia,
            ruta_del_libro=Path(carpeta) / "libro.jsonl",
        )

    assert resultado["executed"] is False

    assert espia.llamadas[0][1]["execute"] is False, (
        "en seco esta mandando execute=True"
    )


def test_cada_renovacion_va_al_libro():
    """
    Jugador, importe de la oferta que muere, hora y que se
    espera que nazca. Sin esto no se puede reconstruir nada.
    """

    import json

    espia = ClienteEspia()

    with tempfile.TemporaryDirectory() as carpeta:

        ruta = Path(carpeta) / "libro.jsonl"

        renovar(
            [
                {
                    "id": 1599,
                    "name": "Jonny",
                    "listed_price": 2_350_000,
                    "dying_offer": 2_401_600,
                    "dying_offer_hours": 0.2,
                }
            ],
            escritor=espia,
            en_vivo=True,
            ruta_del_libro=ruta,
        )

        assert ruta.exists(), "no se ha escrito el libro"

        fila = json.loads(
            ruta.read_text(encoding="utf-8").strip()
        )

    assert fila["player_id"] == 1599
    assert fila["dying_offer"] == 2_401_600, (
        "no queda apuntado lo que se mato al renovar"
    )
    assert fila["listed_price"] == 2_350_000
    assert fila["at"]


# ============================================================
# 2, 3. LA VENTANA Y EL SILENCIO
# ============================================================

def test_fuera_de_la_ventana_no_se_renueva():

    # LOS SEGUNDOS SALEN DE LA CONSTANTE, NO A MANO
    #
    #     Aqui decia `(3_600, 1_800, 901, None)`, y el 901 era
    #     "un segundo fuera" cuando la ventana eran 15 minutos.
    #     El 10/09 la ventana paso a 135 y estos numeros se
    #     quedaron DENTRO: la guardia se puso roja sin que nada
    #     estuviera roto.
    #
    #     Un dato, un nombre: el borde se deduce de
    #     `VENTANA_MINUTOS`, asi que la proxima vez que se mueva
    #     esto sigue midiendo el borde de verdad.
    justo_fuera = VENTANA_MINUTOS * 60 + 1

    # Y el borde EXACTO tiene que estar DENTRO. Sin esto, una
    # ventana que no se abriera nunca pasaria esta guardia.
    assert ventana_abierta(VENTANA_MINUTOS * 60)["abierta"], (
        "el ultimo segundo de la ventana sale cerrado"
    )

    for segundos in (justo_fuera, justo_fuera * 2, 86_400, None):

        plan = que_renovar(
            _ocho(), segundos, puede_escribir=True
        )

        assert plan["execute"] is False, (
            f"a {segundos} s del reset ya esta renovando"
        )
        assert plan["blocked_by"] == "FUERA_DE_VENTANA"


def test_dentro_de_la_ventana_si_se_renueva():
    """La contraria: si la ventana no se abriera nunca, todo lo
    de arriba pasaria igual y no probaria nada."""

    plan = que_renovar(
        _ocho(), EN_LA_VENTANA, puede_escribir=True
    )

    assert plan["execute"] is True, plan["reason"]
    assert plan["renewals"]


def test_la_zona_de_silencio_para_la_renovacion():

    plan = que_renovar(
        _ocho(), EN_LA_VENTANA, puede_escribir=False
    )

    assert plan["execute"] is False
    assert plan["blocked_by"] == "ZONA_DE_SILENCIO"
    assert plan["renewals"] == []


# ============================================================
# 4, 5, 6, 7. LAS PUERTAS DE CADA FILA
# ============================================================

def test_nunca_se_renueva_un_listado_sin_oferta_viva():
    """
    Guardia dura del encargo. Si el dueno renovo a mano, esos
    listados estan sin oferta hasta el reset: volver a
    renovarlos gasta una peticion y no refresca nada.
    """

    filas = _ocho()
    filas[0]["offer_amount"] = 0

    plan = que_renovar(
        filas, EN_LA_VENTANA, puede_escribir=True
    )

    nombres = [r["name"] for r in plan["renewals"]]

    assert filas[0]["name"] not in nombres, (
        "ha renovado un listado sin oferta viva"
    )

    motivos = [
        s["reason"] for s in plan["skipped"]
        if s["name"] == filas[0]["name"]
    ]

    assert motivos and "oferta viva" in motivos[0], (
        "no dice por que lo salta"
    )


def test_primero_se_cobra_y_despues_se_renueva():
    """
    Cobrar una oferta y renovarla en la misma vuelta es perder
    el dinero.
    """

    filas = _ocho()

    plan = que_renovar(
        filas,
        EN_LA_VENTANA,
        puede_escribir=True,
        cobros_de_este_ciclo=[filas[1]["name"]],
    )

    nombres = [r["name"] for r in plan["renewals"]]

    assert filas[1]["name"] not in nombres, (
        "renueva a uno que se esta cobrando en este ciclo"
    )


def test_nunca_dos_renovaciones_del_mismo_en_la_ventana():
    """
    La segunda mataria a la primera y nos dejaria sin nada.
    """

    filas = _ocho()

    plan = que_renovar(
        filas,
        EN_LA_VENTANA,
        puede_escribir=True,
        ya_renovados=[filas[2]["name"]],
    )

    nombres = [r["name"] for r in plan["renewals"]]

    assert filas[2]["name"] not in nombres, (
        "renueva por segunda vez en la misma ventana"
    )

    assert nombres.count(filas[0]["name"]) <= 1, (
        "el mismo jugador sale dos veces en la misma lista"
    )


def test_no_se_renueva_lo_que_llega_de_sobra():
    """
    Un listado dura 48 h, o sea DOS ventanas. Renovar el que
    llega de sobra gasta una peticion y no compra nada.
    """

    filas = [
        _listado("De sobra", 1, 40.0),
        _listado("Justo", 2, 10.0),
    ]

    plan = que_renovar(
        filas, EN_LA_VENTANA, puede_escribir=True
    )

    nombres = [r["name"] for r in plan["renewals"]]

    assert nombres == ["Justo"], (
        f"renueva {nombres} y solo hacia falta «Justo»"
    )


def test_con_deuda_contingente_se_renueva_mas():
    """
    La renovacion pasa a ser la caja con la que se tapa.
    """

    filas = [_listado("De sobra", 1, 30.0)]

    normal = que_renovar(
        filas, EN_LA_VENTANA, puede_escribir=True
    )

    con_deuda = que_renovar(
        filas,
        EN_LA_VENTANA,
        puede_escribir=True,
        deuda_contingente=8_901_617,
        horas_al_inicio_de_jornada=36.0,
    )

    assert normal["count"] == 0, (
        "sin deuda ya lo renovaba: la guardia no prueba nada"
    )

    assert con_deuda["count"] == 1, (
        "con deuda contingente no renueva lo que caduca antes "
        "de la jornada"
    )

    assert con_deuda["mandatory"] is True


# ============================================================
# 8. EL TOPE ES UN CORTE DURO
# ============================================================

def test_el_tope_de_renovaciones_corta_de_verdad():

    muchos = [
        _listado(f"J{i}", 200 + i, 5.0 + i * 0.01)
        for i in range(40)
    ]

    plan = que_renovar(
        muchos, EN_LA_VENTANA, puede_escribir=True, tope=3
    )

    assert plan["count"] == 3, (
        f"con tope 3 propone {plan['count']}"
    )

    assert plan["dropped_by_cap"] == 37

    # Y corta por el que MAS margen tiene, no al azar.
    assert [r["name"] for r in plan["renewals"]] == [
        "J0", "J1", "J2"
    ], "el recorte no deja los mas urgentes"

    # El ejecutor tambien corta, aunque le mientan.
    espia = ClienteEspia()

    with tempfile.TemporaryDirectory() as carpeta:

        resultado = renovar(
            [
                {
                    "id": i,
                    "name": f"J{i}",
                    "listed_price": 1_000,
                    "dying_offer": 1,
                }
                for i in range(1, 40)
            ],
            escritor=espia,
            en_vivo=True,
            tope=2,
            ruta_del_libro=Path(carpeta) / "l.jsonl",
        )

    assert len(espia.llamadas) == 2, (
        f"el ejecutor ha escrito {len(espia.llamadas)} veces con "
        f"el tope en 2"
    )
    assert resultado["dropped_by_cap"] == 37


def test_el_tope_por_defecto_cabe_en_el_presupuesto():
    """
    17 es el maximo de listados que hemos tenido nunca. No es un
    numero a ojo.
    """

    assert TOPE_DE_RENOVACIONES == 17

    # 181 al dia hoy + 17 = 198, contra las 1.536 que rompieron.
    assert 181 + TOPE_DE_RENOVACIONES < 1536 / 4, (
        "el tope se ha acercado demasiado al bloqueo del 08/09"
    )


# ============================================================
# 9. LA ZONA DE SILENCIO
# ============================================================

def _utc(mes, dia, hora, minuto=0):
    return datetime(2026, mes, dia, hora, minuto, tzinfo=timezone.utc)


def test_la_hora_se_calcula_en_madrid_con_su_verano():
    """
    Ni en UTC ni con la hora del contenedor. Es el error que ya
    se cometio el 16/08 y que arreglo `madrid_offset_hours`.
    """

    # VERANO: 04:30 UTC son las 06:30 de Madrid -> dentro.
    verano = permite_escribir(_utc(9, 10, 4, 30), "schedule")

    assert verano["madrid_time"] == "06:30:00", (
        f"en verano calcula {verano['madrid_time']}"
    )
    assert verano["in_window"] is True

    # INVIERNO: 04:30 UTC son las 05:30 de Madrid -> dentro.
    invierno = permite_escribir(_utc(12, 10, 4, 30), "schedule")

    assert invierno["madrid_time"] == "05:30:00", (
        f"en invierno calcula {invierno['madrid_time']}"
    )
    assert invierno["in_window"] is True

    # Y la misma hora UTC cae fuera en verano y dentro en
    # invierno: si esto no se distingue, la franja esta mal.
    fuera_verano = permite_escribir(_utc(9, 10, 5, 30), "schedule")
    dentro_invierno = permite_escribir(
        _utc(12, 10, 5, 30), "schedule"
    )

    assert fuera_verano["in_window"] is False
    assert dentro_invierno["in_window"] is True


def test_el_cron_que_llega_tarde_no_escribe():
    """
    Los `schedule` de GitHub se retrasan. Uno que caiga dentro
    de la franja se calla.
    """

    tarde = permite_escribir(_utc(9, 10, 4, 52), "schedule")

    assert tarde["allowed"] is False
    assert "SILENCIO" in tarde["reason"]


def test_el_disparo_deliberado_si_escribe():
    """
    El trabajo de la ventana cae DENTRO de la franja a
    proposito. Si el silencio lo tapara, no habria subasta
    nunca.
    """

    ventana = permite_escribir(
        _utc(9, 10, 4, 52), "workflow_dispatch"
    )

    assert ventana["allowed"] is True
    assert ventana["in_window"] is True
    assert ventana["deliberate"] is True


def test_sin_saber_quien_dispara_se_calla():

    sin_saber = permite_escribir(_utc(9, 10, 4, 52), None)

    assert sin_saber["allowed"] is False, (
        "escribe sin saber quien ha disparado la vuelta"
    )


def test_fuera_de_la_franja_se_escribe_siempre():

    for hora in (0, 3, 7, 12, 20, 23):

        r = permite_escribir(_utc(9, 10, hora), "schedule")

        # EN MINUTOS, como las constantes.
        #
        #     Aqui se comparaba una HORA contra `SILENCIO_DESDE`.
        #     El 10/09 esa constante paso a minutos -porque las
        #     04:45 no son una hora redonda- y la cuenta se
        #     quedo comparando 5 contra 285.
        madrid = ((hora + 2) % 24) * 60

        esperado = not (
            SILENCIO_DESDE <= madrid < SILENCIO_HASTA
        )

        assert r["allowed"] is esperado, (
            f"a las {madrid // 60}:{madrid % 60:02d} de Madrid "
            f"dice allowed={r['allowed']}"
        )


def test_si_no_se_puede_calcular_la_hora_se_calla():

    roto = permite_escribir("no soy una fecha", "schedule")

    assert roto["allowed"] is False, (
        "con la hora rota deja escribir"
    )


# ============================================================
# 10. QUE SE VEA
# ============================================================

def test_se_ve_lo_que_se_quedo_sin_hacer():
    """
    Una barandilla que frena en silencio es indistinguible de
    una averia.
    """

    silencio = permite_escribir(_utc(9, 10, 4, 52), "schedule")

    visto = lo_que_se_quedo_sin_hacer(
        silencio, ["renovar 8 listados", "pujar por 3"]
    )

    assert visto["blocked"] is True
    assert len(visto["actions"]) == 2
    assert "renovar 8 listados" in visto["reason"]

    # Y cuando no bloquea, no inventa nada.
    libre = lo_que_se_quedo_sin_hacer(
        permite_escribir(_utc(9, 10, 12), "schedule"), ["algo"]
    )

    assert libre["blocked"] is False
    assert libre["actions"] == []


def test_la_franja_sirve_para_medir_el_reset():

    silencio = permite_escribir(_utc(9, 10, 4, 30), "schedule")

    obs = observacion_del_reset(silencio, precios_cambiados=False)

    assert obs["in_window"] is True
    assert obs["prices_changed"] is False
    assert "todavia NO" in obs["reason"]


def test_se_publica_lo_que_no_llega_a_la_proxima_ventana():
    """
    Medido el 10/09: siete de los ocho listados caducaban antes
    de la ventana de manana. Renovar en la ventana no puede
    salvarlos, asi que hay que verlos.
    """

    filas = [
        _listado("Se muere antes", 1, 4.0),
        _listado("Aguanta", 2, 40.0),
    ]

    # A 22 h de la ventana.
    plan = que_renovar(
        filas, 22 * 3600, puede_escribir=True
    )

    nombres = [r["name"] for r in plan["at_risk"]]

    assert nombres == ["Se muere antes"], (
        f"el riesgo sale mal: {nombres}"
    )


# ============================================================
# FORMA Y BLINDAJE
# ============================================================

def test_la_forma_no_cambia_con_los_datos():

    con = que_renovar(_ocho(), EN_LA_VENTANA, puede_escribir=True)
    sin = que_renovar(None, None)

    assert set(con) == set(sin), (
        f"la forma cambia: {set(con) ^ set(sin)}"
    )


def test_nada_de_esto_lanza():

    for basura in (None, "no", {}, [], 0):

        assert isinstance(que_renovar(basura, basura), dict)
        assert isinstance(permite_escribir(basura, basura), dict)
        assert isinstance(
            filas_desde_lo_publicado(basura, basura, basura), list
        )
        assert isinstance(
            lo_que_se_quedo_sin_hacer(basura, basura), dict
        )


TESTS = [
    test_hay_listados_que_comprobar,
    test_renovar_no_puede_vender,
    test_el_modulo_de_renovar_no_conoce_la_venta,
    test_en_seco_no_escribe_nada,
    test_cada_renovacion_va_al_libro,
    test_fuera_de_la_ventana_no_se_renueva,
    test_dentro_de_la_ventana_si_se_renueva,
    test_la_zona_de_silencio_para_la_renovacion,
    test_nunca_se_renueva_un_listado_sin_oferta_viva,
    test_primero_se_cobra_y_despues_se_renueva,
    test_nunca_dos_renovaciones_del_mismo_en_la_ventana,
    test_no_se_renueva_lo_que_llega_de_sobra,
    test_con_deuda_contingente_se_renueva_mas,
    test_el_tope_de_renovaciones_corta_de_verdad,
    test_el_tope_por_defecto_cabe_en_el_presupuesto,
    test_la_hora_se_calcula_en_madrid_con_su_verano,
    test_el_cron_que_llega_tarde_no_escribe,
    test_el_disparo_deliberado_si_escribe,
    test_sin_saber_quien_dispara_se_calla,
    test_fuera_de_la_franja_se_escribe_siempre,
    test_si_no_se_puede_calcular_la_hora_se_calla,
    test_se_ve_lo_que_se_quedo_sin_hacer,
    test_la_franja_sirve_para_medir_el_reset,
    test_se_publica_lo_que_no_llega_a_la_proxima_ventana,
    test_la_forma_no_cambia_con_los_datos,
    test_nada_de_esto_lanza,
]


def main() -> None:

    print()
    print("=" * 60)
    print("RENOVAR EN LA VENTANA V1")
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
