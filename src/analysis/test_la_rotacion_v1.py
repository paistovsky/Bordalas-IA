"""
LA ROTACION (17/10/2026). Guardias de `src/actions/la_rotacion.py`
(`BORDALAS_LA_ROTACION`, laboratorio de la rotacion).

    1. EL QUE CAE: hoy <= 0 Y ayer <= 0 (ayer del historico de precios;
       sin muestra, no cae). `conservar` no lo frena; `no_rotar`,
       `proteger`, Yamal y la cartera, si.
    2. EL QUE ENTRA: del Computer, sube, 'ok', juega, sin puja viva de
       nadie, no vetado, misma posicion y xP >= el del que sale (a
       igualdad de xP vale; el de mas xP, y a igualdad el que mas sube
       en proporcion). Puja con la prima del tramo en 9.900, dentro del
       tope.
    3. EL CUPO: 2 por ventana entre rondas Y por semana ISO; la perdida
       no cuenta; una puja por el que cae al dia.
    4. EL RELOJ: nada si el reset cae en una ronda o la ronda empieza
       antes del reset (el aplazado del 21/10 tambien es ronda), ni en
       la zona de silencio.
    5. LA CAJA, de todos los motores: con saldo negativo (-432.317) solo
       pasan los cambios que no gastan caja.
    6. LA VENTA: solo cuando el que entra ya llego, nunca con una ronda
       jugandose; si es titular, primero el once con el relevo en su
       sitio (y si el once no se guarda, no se vende); 99 % o 95 % con
       prisa. Puja perdida: nunca se vende.
    7. El motor viejo no vende al que sale con la puja viva (las dos
       puertas de `autopilot_executor`).
    8. Nace apagada (lo apaga esta guardia, no el entorno) y nunca lanza.
    9. La revision del 17/10: la caja no cuenta una venta frenada (titular
       antes del aplazado, sin relevo, `no_rotar` tardio, once sin leer o
       incompleto; el 19-21/10 de punta a punta); una puja que solo cabe
       con una aceptacion de esta vuelta no sale si esa no entra; la
       ventana es la ronda, no su hora; nunca de 04:45 a 07:00; lo
       vendido o publicado en esta vuelta (v10, el parte, el que entro)
       y lo que el cierre ya vende; ni el que entra ni el relevo son de
       otro libro; la hora de la foto es de Madrid y perdida es despues
       del reset; el estado se rehace del registro; el reroll, la mejora
       y el cierre ven las parejas abiertas.
   10. El aplazado solo frena a los suyos (19/10/2026): un titular del
       Levante antes del Levante-Athletic sigue frenado; uno del Espanyol
       no (su venta cuenta y se vende); sin saber el club o los equipos de
       la ronda, frena a todos. La caja no cambia: una venta que no se
       cobra antes del aplazado no paga una puja.

Todo con datos de mentira: la hora se pasa siempre, el calendario es un
dict de este fichero, la orden y los libros se escriben en una carpeta
temporal y el escritor es de mentira. No se lee el estado de
produccion, ni el reloj, ni se sale a la red.
"""

from __future__ import annotations

import contextlib
import io
import json
import os
import sys
import tempfile

from datetime import date, datetime, timedelta, timezone
from pathlib import Path


RAIZ = Path(__file__).parents[2]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from src.actions.la_rotacion import (     # noqa: E402
    ENV, GANADA, MAXIMO_DE_CAMBIOS, PERDIDA, PUJADA, ROTA, SIN_EL_COBRO, VENDIDA, activa,
    al_dia, apuntar, correr, decidir, el_cupo, el_once_de, el_precio_del_dia, el_registro,
    el_relevo, el_reloj, el_reset_del_dia, el_resumen, escribir, la_hora_de_la_foto,
    la_subida_de_ayer, la_ventana_de, las_jornadas_jugadas, las_parejas_abiertas,
    leer_el_once, leer_libro, lo_de_esta_vuelta, los_que_rota, no_rotados, por_que_no,
    por_que_no_puja, por_que_no_vende, rehacer,
)


def _utc(*a):
    return datetime(*a, tzinfo=timezone.utc)


ANTES_DE_J9 = _utc(2026, 10, 14, 5, 15)     # mie 07:15 Madrid; J9 en 61,75 h
EN_J9 = _utc(2026, 10, 17, 9, 30)           # sab, la J9 jugandose; el reset del 18 tambien
LUNES = _utc(2026, 10, 19, 5, 15)           # lun 07:15, la J9 acaba esta noche
MARTES = _utc(2026, 10, 20, 5, 15)          # el aplazado del 21/10 en 36,75 h
MIERCOLES = _utc(2026, 10, 21, 5, 15)       # el aplazado en 12,75 h: antes del reset
JUEVES = _utc(2026, 10, 22, 5, 15)          # la J10 en 37,75 h
VIERNES = _utc(2026, 10, 23, 5, 15)         # la J10 en 13,75 h: antes del reset
SILENCIO = _utc(2026, 10, 15, 3, 30)        # jue 05:30 Madrid


def _p(j, casa, fuera, cuando):
    return {"matchday": j, "home": f"Equipo {casa}", "away": f"Equipo {fuera}",
            "kickoff": cuando}


# La J9 del viernes 16/10 21:00 al lunes 19/10 21:00; el aplazado de la J6
# (Levante-Athletic) el miercoles 21/10 a las 20:00, ronda propia; la J10
# del 23/10 al 26/10 (ya en horario de invierno).
CAL = {"matchdays": [
    {"matchday": 9, "matches": [
        _p(9, 7, 1, "2026-10-16T21:00:00+02:00"),
        _p(9, 8, 9, "2026-10-17T16:00:00+02:00"),
        _p(9, 2, 10, "2026-10-17T18:30:00+02:00"),
        _p(9, 3, 4, "2026-10-18T14:00:00+02:00"),
        _p(9, 5, 6, "2026-10-19T21:00:00+02:00"),
    ]},
    {"matchday": 6, "matches": [_p(6, 11, 12, "2026-10-21T20:00:00+02:00")]},
    {"matchday": 10, "matches": [
        _p(10, 7, 8, "2026-10-23T21:00:00+02:00"),
        _p(10, 9, 10, "2026-10-24T16:00:00+02:00"),
        _p(10, 1, 2, "2026-10-24T18:30:00+02:00"),
        _p(10, 3, 4, "2026-10-25T14:00:00+01:00"),
        _p(10, 5, 6, "2026-10-26T21:00:00+01:00"),
    ]},
]}
# La ventana se nombra por la ronda que la cierra (no por su hora).
J9, J6, J10 = "J9", "J6", "J10"


# ------------------------------------------------------------------
# LA PLANTILLA Y EL MERCADO DE MENTIRA (8 jornadas jugadas)
# ------------------------------------------------------------------
#
#   El once (4-4-2): 1 portero, 2-5 defensas, 6-9 medios, 10-11 delanteros.
#     5   defensa titular, 2 M, hoy -20.000, ayer -10.000, 20 puntos  -> cae
#     12  defensa suplente, 500 mil, plano (0 y 0), 5 puntos           -> cae
#     13  medio, hoy -10.000 pero ayer +10.000                         -> no cae
#     14  medio, hoy +10.000                                           -> no cae
#     15  delantero, hoy -30.000, ayer sin muestra                     -> no cae
#     16  Lamine Yamal, cae                                            -> YAMAL
#     17  medio, 800 mil, hoy -15.000, `conservar` de la orden         -> cae
#     18  medio, cae, `no_rotar`                                       -> NO_ROTAR
#     19  medio, cae, `proteger`                                       -> PROTEGIDO
#     20  medio, cae, de la cartera                                    -> LA_CARTERA
#
#   El Computer:
#     101 defensa 1,5 M +30.000, 20 puntos (el mismo xP que el 5)
#     102 defensa 1,5 M +15.000, 20 puntos (igual xP, sube menos)
#     103 defensa 900 mil +10.000, 19 puntos (menos que el 5)
#     104 defensa en duda; 105 no sube; 106 con puja viva de otro motor;
#     107 vetado; 108 juega 2 partidos; 110 defensa de 3,5 M (tope)
#     109 medio 1 M +20.000, 30 puntos
#     201 defensa de un manager (no es subasta)

def _f(pid, nombre, pos, precio, sube, puntos=10, jugados=8, estado="ok"):
    return {"id": pid, "name": nombre, "position": pos, "price": precio,
            "priceIncrement": sube, "points": puntos, "playedHome": jugados // 2,
            "playedAway": jugados - jugados // 2, "status": estado}


ONCE = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
POS_DEL_ONCE = {1: 1, 2: 2, 3: 2, 4: 2, 5: 2, 6: 3, 7: 3, 8: 3, 9: 3, 10: 4, 11: 4}

PLANTILLA = {i: _f(i, f"Titular {i}", POS_DEL_ONCE[i], 3_000_000, 10_000, 30) for i in ONCE}
PLANTILLA[5] = _f(5, "Cae titular", 2, 2_000_000, -20_000, 20)
PLANTILLA.update({
    12: _f(12, "Cae plano", 2, 500_000, 0, 5),
    13: _f(13, "Rebota", 3, 1_000_000, -10_000),
    14: _f(14, "Sube hoy", 3, 1_000_000, 10_000),
    15: _f(15, "Sin ayer", 4, 1_000_000, -30_000),
    16: _f(16, "Lamine Yamal", 4, 20_000_000, -100_000, 60),
    17: _f(17, "Conservado", 3, 800_000, -15_000, 10),
    18: _f(18, "No rotar", 3, 800_000, -15_000, 10),
    19: _f(19, "Protegido", 3, 800_000, -15_000, 10),
    20: _f(20, "De la cartera", 3, 800_000, -15_000, 10),
})
AYER = {i: 10_000 for i in ONCE}
AYER.update({5: -10_000, 12: 0, 13: 10_000, 14: -10_000, 15: None, 16: -50_000,
             17: -10_000, 18: -10_000, 19: -10_000, 20: -10_000})

MERCADO = {
    101: _f(101, "Sube mucho", 2, 1_500_000, 30_000, 20, 6),
    102: _f(102, "Sube poco", 2, 1_500_000, 15_000, 20, 6),
    103: _f(103, "Menos xP", 2, 900_000, 10_000, 19, 6),
    104: _f(104, "En duda", 2, 1_000_000, 50_000, 40, 8, "doubt"),
    105: _f(105, "No sube", 2, 1_000_000, 0, 40),
    106: _f(106, "Pujado por otro", 2, 1_000_000, 50_000, 40),
    107: _f(107, "Vetado", 2, 1_000_000, 50_000, 40),
    108: _f(108, "Juega poco", 2, 1_000_000, 50_000, 40, 2),
    109: _f(109, "Medio que sube", 3, 1_000_000, 20_000, 30),
    110: _f(110, "Caro", 2, 3_500_000, 50_000, 60),
}
DE_MANAGERS = {201: _f(201, "De un manager", 2, 1_500_000, 50_000, 60)}
# Sin la puja viva del 106, el 106 tambien seria candidato: fuera.
LIBRE = {p: f["price"] for p, f in MERCADO.items() if p != 106}
FICHAS = {**PLANTILLA, **MERCADO, **DE_MANAGERS}
RELOJ = el_reloj(ANTES_DE_J9, CAL, True)


def _d(**k):
    """`decidir` con la plantilla de mentira, ya leida."""
    base = dict(
        plantilla=set(PLANTILLA), fichas=FICHAS,
        mercado={p: f["price"] for p, f in MERCADO.items()},
        subidas_de_ayer=AYER, rondas_jugadas=8, saldo=5_000_000,
        pujas_vivas={106: 1_100_000}, maximo_de_puja=20_000_000,
        ofertas_del_computer={}, en_venta=set(), parejas=[],
        protegidos={19}, no_rotar={18}, aguanta={20}, vetados={107},
        reloj=RELOJ,
    )
    base.update(k)
    return decidir(**base)


def _pujas(d):
    return [(a["sale"], a["player_id"], a["importe"]) for a in d["acciones"]
            if a["accion"] == "PUJAR"]


def _acciones(d, accion=None):
    return [(a["accion"], a.get("player_id")) for a in d["acciones"]
            if accion is None or a["accion"] == accion]


def _pareja(sale, entra, estado, dia="2026-10-13", ventana=J9, semana="2026-W42", **k):
    return {"id": f"{sale}>{entra}@{dia}", "sale": sale, "entra": entra, "estado": estado,
            "dia": dia, "ventana": ventana, "semana": semana, "puja": 1_569_900,
            "pujada_en": f"{dia}T06:00:00+00:00", **k}


# ------------------------------------------------------------------
# 1. EL QUE CAE
# ------------------------------------------------------------------

def test_el_que_cae_dos_dias_sin_subir():
    d = _d()
    assert d["activo"] and d["motivo"] is None, d
    caidos = [c["player_id"] for c in d["caidos"]]
    # El que mas baja hoy primero; el plano en el suelo tambien cae.
    assert caidos == [5, 17, 12], d["caidos"]
    por = {n["player_id"]: n["por"] for n in d["no_rota"]}
    assert por == {16: "YAMAL", 18: "NO_ROTAR", 19: "PROTEGIDO", 20: "LA_CARTERA"}, por
    # 13 (ayer sube), 14 (hoy sube) y 15 (ayer sin muestra) ni se miran.
    assert not {13, 14, 15} & (set(caidos) | set(por)), d
    # A igualdad de lo que baja hoy, el de menos xP primero.
    d = _d(fichas={**FICHAS, 17: {**FICHAS[17], "priceIncrement": -20_000, "points": 5}})
    assert [c["player_id"] for c in d["caidos"]][:2] == [17, 5], d["caidos"]
    # `conservar` no frena la rotacion: el 17 se cambia por el 109.
    assert (17, 109, 1_049_900) in _pujas(_d()), _pujas(_d())


def test_ayer_sale_del_historico_y_sin_muestra_no_cae():
    # El dia de mercado del 14/10 empieza en su reset (05:00 UTC, 07:00 de
    # Madrid): ayer es [13/10 05:00, 14/10 05:00), anteayer el anterior.
    t = lambda *a: _utc(*a).timestamp()                             # noqa: E731
    serie = {"t": [t(2026, 10, 12, 5, 20), t(2026, 10, 13, 5, 20), t(2026, 10, 14, 5, 20)],
             "p": [1_000_000, 990_000, 980_000]}
    assert la_subida_de_ayer(serie, ANTES_DE_J9) == -10_000
    # Plano: apunta cada 20 h; el ultimo de cada dia vale.
    plano = {"t": [t(2026, 10, 11, 5, 20), t(2026, 10, 12, 23, 0), t(2026, 10, 13, 19, 0)],
             "p": [150_000, 150_000, 150_000]}
    assert la_subida_de_ayer(plano, ANTES_DE_J9) == 0
    # Un dia sin muestra: no se sabe.
    hueco = {"t": [t(2026, 10, 11, 5, 20), t(2026, 10, 13, 19, 0)], "p": [1_000_000, 990_000]}
    assert la_subida_de_ayer(hueco, ANTES_DE_J9) is None
    assert el_precio_del_dia(serie, t(2026, 10, 13, 5, 0), t(2026, 10, 14, 5, 0)) == 990_000
    # Con el cambio de hora del 25/10, el reset sigue a las 07:00 de Madrid.
    assert el_reset_del_dia(date(2026, 10, 24)) == _utc(2026, 10, 24, 5, 0)
    assert el_reset_del_dia(date(2026, 10, 25)) == _utc(2026, 10, 25, 6, 0)
    assert el_reset_del_dia(date(2026, 3, 29)) == _utc(2026, 3, 29, 5, 0)
    # Las jornadas jugadas: el libro de las cerradas; si no, el catalogo.
    with tempfile.TemporaryDirectory() as carpeta:
        ruta = Path(carpeta) / "puntos.jsonl"
        ruta.write_text('{"jornada": 7}\n{"jornada": 8}\nbasura\n')
        assert las_jornadas_jugadas({}, ruta) == 8
        assert las_jornadas_jugadas(FICHAS, Path(carpeta) / "no.jsonl") == 8


# ------------------------------------------------------------------
# 2. EL QUE ENTRA
# ------------------------------------------------------------------

def test_el_que_entra_y_el_desempate_por_xp():
    d = _d()
    # 5 (xP 2,5): 101 y 102 empatan en xP con el (vale), 103 no llega;
    # gana 101, que sube mas en proporcion. Puja +4 % en 9.900.
    assert _pujas(d) == [(5, 101, 1_569_900), (17, 109, 1_049_900)], _pujas(d)
    puja = [a for a in d["acciones"] if a["accion"] == "PUJAR"][0]
    assert puja["xp_sale"] == puja["xp_entra"] == 2.5 and puja["sustituye"] is None
    # Un punto menos que el que sale: no vale (tolerancia 0).
    d = _d(fichas={**FICHAS, 101: {**FICHAS[101], "points": 19},
                   102: {**FICHAS[102], "points": 19}}, parejas=[])
    assert [p for p in _pujas(d) if p[0] == 5] == [], _pujas(d)
    # El de mas xP gana aunque suba menos en proporcion.
    d = _d(fichas={**FICHAS, 102: {**FICHAS[102], "points": 25}})
    assert (5, 102, 1_569_900) in _pujas(d), _pujas(d)
    # Sin cupo para el 17, el 12 (5 puntos) se lleva el mejor que queda: 102.
    d = _d(no_rotar={17, 18})
    assert _pujas(d) == [(5, 101, 1_569_900), (12, 102, 1_569_900)], _pujas(d)
    # Duda, no sube, puja viva de otro motor, vetado, juega poco, por
    # encima del tope y el del manager: nunca.
    solos = {p: f["price"] for p, f in MERCADO.items() if p in {104, 105, 106, 107, 108, 110}}
    d = _d(mercado=solos)
    assert _pujas(d) == [], _pujas(d)
    # `maximumBid` corto: no se puja por encima.
    d = _d(maximo_de_puja=1_500_000)
    assert _pujas(d) == [(17, 109, 1_049_900)], _pujas(d)


# ------------------------------------------------------------------
# 3. EL CUPO
# ------------------------------------------------------------------

def test_dos_por_ventana_y_por_semana():
    assert MAXIMO_DE_CAMBIOS == 2
    # Dos en la ventana de la J9 (con puja viva o ya ganadas): nada.
    d = _d(parejas=[_pareja(30, 301, PUJADA), _pareja(31, 311, VENDIDA)])
    assert _pujas(d) == [] and d["por_que_no_puja"] == "SIN_CUPO", d
    # Una perdida no gasta cupo.
    d = _d(parejas=[_pareja(30, 301, PUJADA), _pareja(31, 311, PERDIDA)])
    assert _pujas(d) == [(5, 101, 1_569_900)] and d["cupo"]["quedan"] == 1, d
    # Por semana ISO: el 22/10 (ventana de la J10) con dos del 19 y 20/10
    # (ventana del aplazado, semana 43) no queda cupo.
    reloj = el_reloj(JUEVES, CAL, True)
    assert reloj["ventana"] == J10 and reloj["semana"] == "2026-W43", reloj
    parejas = [_pareja(30, 301, VENDIDA, "2026-10-19", J6, "2026-W43"),
               _pareja(31, 311, ROTA, "2026-10-20", J6, "2026-W43")]
    assert el_cupo(parejas, J10, "2026-W43") == {"ventana": 0, "semana": 2, "quedan": 0}
    d = _d(parejas=parejas, reloj=reloj)
    assert _pujas(d) == [] and d["por_que_no_puja"] == "SIN_CUPO", d
    # Una puja por el que cae al dia, aunque se perdiera.
    d = _d(parejas=[_pareja(5, 101, PERDIDA, "2026-10-14", J9, "2026-W42")])
    assert 5 not in [p[0] for p in _pujas(d)], _pujas(d)
    assert {"player_id": 5, "nombre": "Cae titular", "por": "UNA_PUJA_AL_DIA"} in d["no_rota"]


# ------------------------------------------------------------------
# 4. EL RELOJ (con el aplazado del 21/10 como ronda propia)
# ------------------------------------------------------------------

def test_el_reloj_y_el_aplazado():
    r = el_reloj(ANTES_DE_J9, CAL, True)
    assert (r["horas_ronda"], r["horas_reset"], r["ventana"]) == (61.75, 23.75, J9), r
    assert r["en_curso"] is False and r["reset_en_ronda"] is False and por_que_no_puja(r) is None
    # Con la J9 jugandose y el reset del domingo dentro de ella: ni puja ni vende.
    r = el_reloj(EN_J9, CAL, True)
    assert por_que_no_puja(r) == "EL_RESET_CAE_EN_UNA_RONDA" and por_que_no_vende(r) == "JORNADA_EN_CURSO"
    d = _d(reloj=r, parejas=[_pareja(5, 101, GANADA)], plantilla=set(PLANTILLA) | {101},
           ofertas_del_computer={5: {"offer_id": 905, "amount": 5_000_000}},
           once={"ids": ONCE, "formacion": "4-4-2"})
    assert _pujas(d) == [] and _acciones(d, "ACEPTAR_OFERTA_DEL_COMPUTER") == [], d
    assert _acciones(d, "PONER_A_LA_VENTA") == [] and _acciones(d, "CAMBIAR_EL_ONCE") == []
    # El lunes por la mañana la J9 sigue, pero la puja se resuelve el martes,
    # despues de su ultimo partido: se puja. Vender, no.
    r = el_reloj(LUNES, CAL, True)
    assert r["en_curso"] and not r["reset_en_ronda"] and r["ventana"] == J6, r
    assert por_que_no_puja(r) is None and por_que_no_vende(r) == "JORNADA_EN_CURSO"
    assert _pujas(_d(reloj=r)), _d(reloj=r)
    # El miercoles el aplazado (20:00) llega antes que el reset del jueves:
    # la puja se resolveria con esa ronda empezada.
    r = el_reloj(MIERCOLES, CAL, True)
    assert r["horas_ronda"] == 12.75 and r["ronda_parcial"], r
    assert por_que_no_puja(r) == "LA_PUJA_SE_RESOLVERIA_CON_LA_RONDA_EMPEZADA"
    assert _pujas(_d(reloj=r)) == []
    # En la zona de silencio, nada.
    assert por_que_no(el_reloj(SILENCIO, CAL, False)) == "ZONA_DE_SILENCIO"
    assert por_que_no(el_reloj(ANTES_DE_J9, {}, True)) == "SIN_CALENDARIO"
    assert _d(reloj=el_reloj(SILENCIO, CAL, False))["acciones"] == []
    # A 15 minutos del cierre no se toca el once.
    assert por_que_no_vende({"en_curso": False, "horas_ronda": 0.2}) == "CERCA_DEL_CIERRE"


# ------------------------------------------------------------------
# 5. LA CAJA
# ------------------------------------------------------------------

def test_con_saldo_negativo_solo_lo_que_no_gasta_caja():
    # -432.317 hoy. 5 (2 M, se cobra al 95 % antes de la J9) por 101 a
    # 1.569.900: -432.317 - 1.569.900 + 1.900.000 = -102.217, mejor que
    # antes: vale. 17 (800 mil) por 109 a 1.049.900 gastaria: no.
    d = _d(saldo=-432_317, pujas_vivas={}, mercado=LIBRE)
    assert _pujas(d) == [(5, 101, 1_569_900)], _pujas(d)
    assert d["caja"]["antes"] == -432_317 and d["caja"]["despues"] == -102_217, d["caja"]
    # El martes el cobro ya no llega antes del aplazado: no se cuenta y no
    # pasa ninguno.
    d = _d(saldo=-432_317, pujas_vivas={}, mercado=LIBRE, reloj=el_reloj(MARTES, CAL, True))
    assert _pujas(d) == [], d
    # Las pujas vivas de los demas motores cuentan: 1 M de saldo y 3 M
    # pujados por otro es como estar en rojo.
    d = _d(saldo=1_000_000, pujas_vivas={106: 3_000_000})
    assert _pujas(d) == [(5, 101, 1_569_900)], _pujas(d)
    # Con caja, los dos.
    assert len(_pujas(_d(saldo=5_000_000))) == 2
    # Sin saldo en la foto no se puja.
    assert _d(saldo=None)["por_que_no_puja"] == "SIN_SALDO"
    # Lo que se espera cobrar por una pareja ya ganada cuenta (publicado y
    # con la oferta antes de la ronda): 5 ganada (1,9 M) deja pujar por el 17.
    d = _d(saldo=-432_317, pujas_vivas={}, mercado=LIBRE, plantilla=set(PLANTILLA) | {101},
           parejas=[_pareja(5, 101, GANADA)])
    assert d["caja"]["cobros_esperados"] == 1_900_000 and (17, 109, 1_049_900) in _pujas(d), d
    # Con una ronda jugandose no se publica: ese cobro no se cuenta.
    d = _d(saldo=-432_317, pujas_vivas={}, mercado=LIBRE, plantilla=set(PLANTILLA) | {101},
           parejas=[_pareja(5, 101, GANADA)], reloj=el_reloj(LUNES, CAL, True))
    assert d["caja"]["cobros_esperados"] == 0 and _pujas(d) == [], d
    # Sin saldo no hay prisa: el que sale se cobra desde el 99 %.
    d = _d(saldo=None, plantilla=set(PLANTILLA) | {103}, en_venta={12},
           parejas=[_pareja(12, 103, GANADA)], once={"ids": ONCE, "formacion": "4-4-2"},
           ofertas_del_computer={12: {"offer_id": 912, "amount": 475_000}})
    assert _acciones(d, "ACEPTAR_OFERTA_DEL_COMPUTER") == [], d["acciones"]


# ------------------------------------------------------------------
# 6. LA VENTA
# ------------------------------------------------------------------

def test_solo_se_vende_cuando_el_que_entra_ha_llegado():
    oferta = {5: {"offer_id": 905, "amount": 1_990_000}}
    # Con la puja viva: ni se publica ni se cobra, y no vuelve a caer.
    d = _d(parejas=[_pareja(5, 101, PUJADA)], ofertas_del_computer=oferta,
           pujas_vivas={101: 1_569_900}, once={"ids": ONCE, "formacion": "4-4-2"})
    assert [a for a in _acciones(d) if a[1] == 5] == [], d["acciones"]
    assert {"player_id": 5, "nombre": "Cae titular", "por": "YA_EN_UNA_PAREJA"} in d["no_rota"]
    # Llegado (en la plantilla): primero el once, despues la venta.
    d = _d(parejas=[_pareja(5, 101, GANADA)], ofertas_del_computer=oferta,
           plantilla=set(PLANTILLA) | {101}, once={"ids": ONCE, "formacion": "4-4-2"})
    assert _acciones(d)[:2] == [("CAMBIAR_EL_ONCE", None),
                                ("ACEPTAR_OFERTA_DEL_COMPUTER", 5)], d["acciones"]
    # Sin oferta y sin publicar: se publica a su valor.
    d = _d(parejas=[_pareja(5, 101, GANADA)], plantilla=set(PLANTILLA) | {101},
           once={"ids": ONCE, "formacion": "4-4-2"})
    assert ("PONER_A_LA_VENTA", 5) in _acciones(d)
    assert [a["precio"] for a in d["acciones"] if a["accion"] == "PONER_A_LA_VENTA"] == [2_000_000]


def test_el_99_y_el_95_con_prisa():
    base = dict(parejas=[_pareja(12, 103, GANADA)], plantilla=set(PLANTILLA) | {103},
                en_venta={12}, once={"ids": ONCE, "formacion": "4-4-2"})
    # 12 vale 500 mil: 99 % = 495.000. A 494.999, nada (publicado y esperando).
    d = _d(**base, ofertas_del_computer={12: {"offer_id": 912, "amount": 494_999}})
    assert _acciones(d, "ACEPTAR_OFERTA_DEL_COMPUTER") == [], d["acciones"]
    d = _d(**base, ofertas_del_computer={12: {"offer_id": 912, "amount": 495_000}})
    acepta = [a for a in d["acciones"] if a["accion"] == "ACEPTAR_OFERTA_DEL_COMPUTER"]
    assert [(a["player_id"], a["suelo"], a["requiere_el_once"]) for a in acepta] == [
        (12, 495_000, False)], d["acciones"]
    # En rojo, desde el 95 %.
    d = _d(**base, saldo=-432_317, ofertas_del_computer={12: {"offer_id": 912, "amount": 475_000}})
    assert _acciones(d, "ACEPTAR_OFERTA_DEL_COMPUTER") == [("ACEPTAR_OFERTA_DEL_COMPUTER", 12)]
    # Si la siguiente oferta no llega antes de la ronda (jueves: J10 en 37,75 h).
    d = _d(**base, reloj=el_reloj(JUEVES, CAL, True),
           ofertas_del_computer={12: {"offer_id": 912, "amount": 475_000}})
    assert _acciones(d, "ACEPTAR_OFERTA_DEL_COMPUTER") == [("ACEPTAR_OFERTA_DEL_COMPUTER", 12)]
    # Aunque ahora suba: la pareja esta hecha.
    d = _d(**{**base, "fichas": {**FICHAS, 12: {**FICHAS[12], "priceIncrement": 30_000}}},
           ofertas_del_computer={12: {"offer_id": 912, "amount": 495_000}})
    assert _acciones(d, "ACEPTAR_OFERTA_DEL_COMPUTER") == [("ACEPTAR_OFERTA_DEL_COMPUTER", 12)]


def test_el_titular_no_deja_un_hueco():
    oferta = {5: {"offer_id": 905, "amount": 1_990_000}}
    base = dict(parejas=[_pareja(5, 101, GANADA)], ofertas_del_computer=oferta,
                plantilla=set(PLANTILLA) | {101})
    # El que entra ocupa su sitio: mismo indice, mismo dibujo.
    d = _d(**base, once={"ids": ONCE, "formacion": "4-4-2"})
    cambio = d["acciones"][0]
    assert cambio["accion"] == "CAMBIAR_EL_ONCE" and cambio["formacion"] == "4-4-2", cambio
    assert cambio["once"] == [1, 2, 3, 4, 101, 6, 7, 8, 9, 10, 11], cambio
    assert d["acciones"][1]["requiere_el_once"] is True
    # El que entra no esta sano: el suplente sano de su posicion (12).
    fichas = {**FICHAS, 101: {**FICHAS[101], "status": "doubt"}}
    d = _d(**base, fichas=fichas, once={"ids": ONCE, "formacion": "4-4-2"})
    assert d["acciones"][0]["once"][4] == 12, d["acciones"]
    assert el_relevo(5, 101, set(ONCE), set(PLANTILLA) | {101}, fichas, 8) == 12
    # El relevo nunca es otro que sale de su pareja.
    d = _d(**{**base, "parejas": base["parejas"] + [_pareja(12, 103, PUJADA)]},
           fichas=fichas, once={"ids": ONCE, "formacion": "4-4-2"})
    assert _acciones(d, "ACEPTAR_OFERTA_DEL_COMPUTER") == [], d["acciones"]
    # Sin relevo sano: no se vende.
    fichas[12] = {**FICHAS[12], "status": "injured"}
    d = _d(**base, fichas=fichas, once={"ids": ONCE, "formacion": "4-4-2"})
    assert _acciones(d, "ACEPTAR_OFERTA_DEL_COMPUTER") == [] and _acciones(d, "CAMBIAR_EL_ONCE") == []
    assert {"accion": "NADA", "player_id": 5, "pareja": "5>101@2026-10-13",
            "motivo": "SIN_RELEVO_PARA_EL_ONCE"} in d["acciones"], d["acciones"]
    # Sin leer el once vigente no se vende (y se pide leerlo); sin poder
    # leerlo, tampoco.
    d = _d(**base)
    assert d["necesita_el_once"] and _acciones(d, "ACEPTAR_OFERTA_DEL_COMPUTER") == []
    d = _d(**base, once={})
    assert not d["necesita_el_once"] and _acciones(d, "ACEPTAR_OFERTA_DEL_COMPUTER") == []
    # Fuera del once: se vende sin tocarlo.
    d = _d(**base, once={"ids": [1, 2, 3, 4, 12, 6, 7, 8, 9, 10, 11], "formacion": "4-4-2"})
    assert _acciones(d)[0] == ("ACEPTAR_OFERTA_DEL_COMPUTER", 5), d["acciones"]
    # Titular antes del aplazado (solo juegan dos equipos): su relevo
    # seguramente no juega; se vende cuando acabe. Del banquillo, si.
    d = _d(**base, once={"ids": ONCE, "formacion": "4-4-2"}, reloj=el_reloj(MARTES, CAL, True))
    assert _acciones(d, "ACEPTAR_OFERTA_DEL_COMPUTER") == [], d["acciones"]
    d = _d(**base, once={"ids": [1, 2, 3, 4, 12, 6, 7, 8, 9, 10, 11], "formacion": "4-4-2"},
           reloj=el_reloj(MARTES, CAL, True))
    assert _acciones(d, "ACEPTAR_OFERTA_DEL_COMPUTER") == [("ACEPTAR_OFERTA_DEL_COMPUTER", 5)]


def test_puja_perdida_nunca_vende_y_se_reintenta():
    perdida = _pareja(5, 101, PUJADA, pujada_en="2026-10-13T06:00:00+00:00")
    # Foto de despues del reset que resuelve la puja (14/10 07:00 de
    # Madrid), sin el 101 ni su puja: perdida. La hora de la foto, sin
    # zona, es de Madrid: 07:12 = 05:12 UTC.
    parejas, eventos = al_dia([perdida], plantilla=set(PLANTILLA), pujas_de_la_foto=set(),
                              foto_en="2026-10-14T07:12:00", ahora=ANTES_DE_J9)
    assert parejas[0]["estado"] == PERDIDA and eventos[0]["evento"] == PERDIDA, parejas
    # Con una foto de antes de la puja, no se sabe: sigue pujada.
    parejas_b, _ = al_dia([perdida], plantilla=set(PLANTILLA), pujas_de_la_foto=set(),
                          foto_en="2026-10-13T07:00:00", ahora=ANTES_DE_J9)
    assert parejas_b[0]["estado"] == PUJADA
    # Perdida: el 5 nunca se vende por ella (ni con oferta) y vuelve a caer al dia siguiente.
    d = _d(parejas=parejas, ofertas_del_computer={5: {"offer_id": 905, "amount": 2_000_000}},
           once={"ids": ONCE, "formacion": "4-4-2"})
    assert _acciones(d, "ACEPTAR_OFERTA_DEL_COMPUTER") == [] and _acciones(d, "PONER_A_LA_VENTA") == []
    assert (5, 101, 1_569_900) in _pujas(d) and d["cupo"]["quedan"] == 2, d
    # Ganada: GANADA; vendido el que sale: VENDIDA; se fue el que entro: ROTA.
    p, e = al_dia([perdida], plantilla=set(PLANTILLA) | {101}, pujas_de_la_foto=set(),
                  foto_en="2026-10-14T07:12:00", ahora=ANTES_DE_J9)
    assert p[0]["estado"] == GANADA and p[0]["llego_en"], p
    p, _ = al_dia(p, plantilla=(set(PLANTILLA) - {5}) | {101}, pujas_de_la_foto=set())
    assert p[0]["estado"] == VENDIDA
    p, _ = al_dia([_pareja(5, 101, GANADA)], plantilla=set(PLANTILLA), pujas_de_la_foto=set())
    assert p[0]["estado"] == ROTA


# ------------------------------------------------------------------
# 7. DE PUNTA A PUNTA, Y EL MOTOR VIEJO
# ------------------------------------------------------------------

class _Escritor:
    llamadas: list = []
    creados = 0
    guarda_el_once = True

    def __init__(self):
        type(self).creados += 1

    def _ok(self, nombre, k):
        type(self).llamadas.append((nombre, k))
        return {"sent": True, "success": True, "http_status": 200}

    def accept_offer(self, **k):
        return self._ok("accept_offer", k)

    def list_player_for_sale(self, **k):
        return self._ok("list_player_for_sale", k)

    def place_bid(self, **k):
        return self._ok("place_bid", k)

    def cancel_bid(self, **k):
        return self._ok("cancel_bid", k)

    def save_lineup(self, **k):
        type(self).llamadas.append(("save_lineup", k))
        ok = type(self).guarda_el_once
        return {"sent": True, "success": ok, "http_status": 200 if ok else 400}


class _EscritorQueRevienta:
    def __getattr__(self, nombre):
        raise RuntimeError("la red se ha caido")


def _limpiar(guarda=True):
    _Escritor.creados, _Escritor.llamadas, _Escritor.guarda_el_once = 0, [], guarda


def _entorno(**valores):
    """Pone los interruptores (None = quitarlo) y devuelve como estaban."""
    antes = {k: os.environ.get(k) for k in valores}
    for k, v in valores.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v
    return antes


# Los interruptores que esta guardia lee, puestos por ella (doctrina 104).
ENCENDIDO = {ENV: "1", "BORDALAS_LA_ORDEN_DEL_GESTOR": "1", "BORDALAS_LA_CARTERA": "1",
             "GITHUB_RUN_ID": None}


# La hora de la foto, como la apunta `league_collector`: sin zona, de Madrid
# (el workflow corre con TZ Europe/Madrid). 07:10 de Madrid = 05:10 UTC.
def _la_foto(plantilla=None, ofertas=None, saldo=5_000_000, cuando="2026-10-14T07:10:00"):
    plantilla = set(PLANTILLA) if plantilla is None else plantilla
    return {
        "timestamp": cuando,
        "league": {"user": {"id": 99}},
        "market": {
            "status": {"balance": saldo, "maximumBid": 20_000_000},
            "sales": [{"player": {"id": p}, "user": None, "price": f["price"]}
                      for p, f in MERCADO.items() if p not in plantilla]
            + [{"player": {"id": 201}, "user": {"id": 7}, "price": 1_500_000}],
            "offers": [{"id": 806, "status": "waiting", "amount": 1_100_000,
                        "requestedPlayers": [{"id": 106}], "from": {"id": 99}}]
            + [{"id": o, "status": "waiting", "amount": a, "requestedPlayers": [{"id": p}],
                "from": None} for p, (o, a) in (ofertas or {}).items()],
        },
        "my_team": [{"id": p, "price": FICHAS[p]["price"]} for p in sorted(plantilla)],
        "catalog": {"data": {"players": {str(p): f for p, f in FICHAS.items()}}},
        "user_lineup": {"data": {"lineup": {"type": "4-4-2",
                                            "players": [{"id": i} for i in ONCE]}}},
    }


def _historico(dia=date(2026, 10, 14)):
    """Ayer y anteayer (del dia de mercado `dia`) para que caigan los de `AYER`."""
    t1 = datetime(dia.year, dia.month, dia.day, 6, tzinfo=timezone.utc) - timedelta(days=2)
    t1, t2 = t1.timestamp(), (t1 + timedelta(days=1)).timestamp()
    salida = {}
    for pid, ayer in AYER.items():
        if ayer is None:
            continue
        base = PLANTILLA[pid]["price"]
        salida[str(pid)] = {"t": [t1, t2], "p": [base - ayer, base]}
    return salida


def _ficheros(carpeta):
    orden = Path(carpeta) / "orden.json"
    orden.write_text(json.dumps({
        "caduca": "2026-11-30T23:59:00+01:00",
        "proteger": [{"player_id": 19, "nombre": "Protegido"}],
        "conservar": [{"player_id": 17, "nombre": "Conservado"}],
        "no_pujar": [{"player_id": 107, "nombre": "Vetado"}],
        "no_rotar": [{"player_id": 18, "nombre": "No rotar"}],
    }))
    ronda = Path(carpeta) / "la_ronda.json"
    ronda.write_text(json.dumps({"20": 800_000}))
    return orden, ronda


def _correr(carpeta, **k):
    orden, ronda = _ficheros(carpeta)
    base = dict(cycle={"snapshot": _la_foto()}, escritor_factory=_Escritor, ahora=ANTES_DE_J9,
                calendario=CAL, orden_ruta=orden, libro_ronda_ruta=ronda,
                libro_ruta=Path(carpeta) / "la_rotacion.json",
                registro_ruta=Path(carpeta) / "la_rotacion.jsonl", historico=_historico(),
                rondas_jugadas=8, otros_venden=set(), v10={}, vuelta_mejora={},
                plan_cierre={}, lector_del_once=lambda e: {"ids": ONCE, "formacion": "4-4-2"},
                rastro_ruta=Path(carpeta) / "rastro.jsonl", vuelta_parte={})
    base.update(k)
    return correr(**base)


def test_de_punta_a_punta():
    antes = _entorno(**ENCENDIDO)
    try:
        with tempfile.TemporaryDirectory() as carpeta:
            libro = Path(carpeta) / "la_rotacion.json"
            registro = Path(carpeta) / "la_rotacion.jsonl"
            # Miercoles 14/10: se puja por el 101 (sale el 5) y el 109 (sale el 17).
            _limpiar()
            r = _correr(carpeta)
            assert r["motivo"] == "EJECUTADA", r
            assert [c[0] for c in _Escritor.llamadas] == ["place_bid", "place_bid"], _Escritor.llamadas
            # El 201 lo vende un manager: no es subasta, no se puja.
            assert 201 not in [c[1]["player_id"] for c in _Escritor.llamadas]
            assert _Escritor.llamadas[0][1] == {"player_id": 101, "amount": 1_569_900,
                                                "execute": True}
            assert [(p["sale"], p["entra"], p["estado"]) for p in leer_libro(libro)["parejas"]] == [
                (5, 101, PUJADA), (17, 109, PUJADA)]
            assert los_que_rota(libro) == {5, 17}
            # La orden (proteger, no_rotar) y la cartera llegan de sus
            # ficheros hasta `decidir`.
            por = {n["player_id"]: n["por"] for n in r["decision"]["no_rota"]}
            assert por == {16: "YAMAL", 18: "NO_ROTAR", 19: "PROTEGIDO", 20: "LA_CARTERA"}, por
            # Otra vuelta el mismo dia (la foto aun es de antes): ni pujas
            # nuevas ni se dan por perdidas.
            _limpiar()
            r = _correr(carpeta, ahora=ANTES_DE_J9.replace(hour=6))
            assert r["motivo"] == "NADA_QUE_HACER" and _Escritor.creados == 0, r
            assert los_que_rota(libro) == {5, 17}
            # Jueves 15/10 07:15: el 101 llego y el 109 se perdio. El 5 es
            # titular y tiene oferta al 99,5 %: el once con el 101 en su
            # sitio y despues la venta. El 17 no se vende.
            _limpiar()
            foto = _la_foto(plantilla=set(PLANTILLA) | {101}, cuando="2026-10-15T07:12:00",
                            ofertas={5: (905, 1_990_000), 17: (917, 900_000)})
            r = _correr(carpeta, cycle={"snapshot": foto}, ahora=_utc(2026, 10, 15, 5, 15))
            assert r["motivo"] == "EJECUTADA", r
            nombres = [c[0] for c in _Escritor.llamadas]
            assert nombres[:2] == ["save_lineup", "accept_offer"], _Escritor.llamadas
            assert _Escritor.llamadas[0][1] == {"player_ids": [1, 2, 3, 4, 101, 6, 7, 8, 9, 10, 11],
                                                "formation": "4-4-2", "reserve_ids": [],
                                                "execute": True}
            assert ("accept_offer", {"offer_id": 917, "execute": True}) not in _Escritor.llamadas
            estados = {(p["sale"], p["entra"]): p["estado"] for p in leer_libro(libro)["parejas"]}
            assert estados[(5, 101)] == VENDIDA and estados[(17, 109)] == PERDIDA, estados
            assert los_que_rota(libro) == set()
            eventos = [json.loads(x)["evento"] for x in registro.read_text().splitlines()]
            for e in ("PUJAR", "GANADA", PERDIDA, "CAMBIAR_EL_ONCE", "ACEPTAR_OFERTA_DEL_COMPUTER"):
                assert e in eventos, eventos
            assert (Path(carpeta) / "rastro.jsonl").exists()
            assert any("EJECUTADA" in linea for linea in el_resumen(r))
    finally:
        _entorno(**antes)


def test_si_el_once_no_se_guarda_no_se_vende():
    antes = _entorno(**ENCENDIDO)
    try:
        with tempfile.TemporaryDirectory() as carpeta:
            libro = Path(carpeta) / "la_rotacion.json"
            libro.write_text(json.dumps({"parejas": [_pareja(5, 101, GANADA)]}))
            foto = _la_foto(plantilla=set(PLANTILLA) | {101}, ofertas={5: (905, 1_990_000)})
            _limpiar(guarda=False)
            r = _correr(carpeta, cycle={"snapshot": foto})
            assert [c[0] for c in _Escritor.llamadas
                    if c[0] in ("save_lineup", "accept_offer")] == ["save_lineup"], _Escritor.llamadas
            fallo = [h for h in r["hechas"] if h["accion"] == "ACEPTAR_OFERTA_DEL_COMPUTER"]
            assert fallo and fallo[0]["error"] == "EL_ONCE_NO_SE_GUARDO", r["hechas"]
            assert leer_libro(libro)["parejas"][0]["estado"] == GANADA
            # Sin poder leer el once vigente: ni se escribe el once ni se vende.
            _limpiar()
            r = _correr(carpeta, cycle={"snapshot": foto}, lector_del_once=lambda e: None)
            assert not [c for c in _Escritor.llamadas
                        if c[0] in ("save_lineup", "accept_offer")], _Escritor.llamadas
            assert any(a.get("motivo") == "SIN_ONCE_DE_BIWENGER" for a in r["acciones"]), r
            # Con la J9 jugandose: ni el once, ni la venta, ni se lee nada.
            _limpiar()
            r = _correr(carpeta, cycle={"snapshot": foto}, ahora=EN_J9)
            assert _Escritor.creados == 0 and r["motivo"] == "NADA_QUE_HACER", r
            # En la zona de silencio: nada, sin leer.
            _limpiar()
            r = _correr(carpeta, cycle={"snapshot": foto}, ahora=SILENCIO)
            assert r["motivo"] == "ZONA_DE_SILENCIO" and _Escritor.creados == 0, r
            assert "decision" in r and r["decision"] is None
    finally:
        _entorno(**antes)


def test_el_once_vigente_se_lee_de_biwenger():
    class _Respuesta:
        def raise_for_status(self):
            return None

        def json(self):
            return {"data": {"lineup": {"type": "4-3-3", "players": [{"id": i} for i in ONCE]}}}

    class _Sesion:
        pedido = None

        def get(self, url, params=None, timeout=None):
            type(self).pedido = (url, params)
            return _Respuesta()

    class _Cliente:
        BASE_URL = "https://biwenger.example/api/v2"
        session = _Sesion()

    class _ConCliente:
        client = _Cliente()

    assert leer_el_once(_ConCliente()) == {"ids": ONCE, "formacion": "4-3-3"}
    assert _Sesion.pedido == ("https://biwenger.example/api/v2/user",
                              {"fields": "*,lineup(*,players(*))"})
    assert leer_el_once(object()) is None
    assert el_once_de({"type": "4-4-2", "players": [7, {"id": 8}]}) == {
        "ids": [7, 8], "formacion": "4-4-2"}
    assert el_once_de({}) is None


def test_el_motor_viejo_no_vende_al_que_rota():
    texto = (RAIZ / "src" / "actions" / "autopilot_executor.py").read_text(encoding="utf-8")
    # Las dos puertas que aceptan ofertas lo miran, junto a `conservar` y la cartera.
    assert texto.count("_conservados() | _aguanta() | _rota()") == 2
    assert texto.count("from src.actions.la_rotacion import los_que_rota as _rota") == 2
    antes = _entorno(**{ENV: "1"})
    try:
        with tempfile.TemporaryDirectory() as carpeta:
            libro = Path(carpeta) / "la_rotacion.json"
            libro.write_text(json.dumps({"parejas": [
                _pareja(5, 101, PUJADA), _pareja(12, 103, GANADA), _pareja(17, 109, PERDIDA),
                {"sale": "x", "estado": PUJADA}, "basura"]}))
            # Solo el que sale con la puja viva: el de una ganada lo puede
            # vender cualquiera (ya hay relevo).
            assert los_que_rota(libro) == {5}
            assert los_que_rota(Path(carpeta) / "no_existe.json") == set()
            _entorno(**{ENV: None})
            assert los_que_rota(libro) == set()
    finally:
        _entorno(**antes)


# ------------------------------------------------------------------
# 8. NACE APAGADA Y NUNCA LANZA
# ------------------------------------------------------------------

def test_nace_apagada():
    antes = _entorno(**{ENV: None})
    try:
        assert activa() is False
        # Sin argumentos: vuelve antes de leer nada.
        assert correr() == {"activa": False, "motivo": "APAGADA", "acciones": [],
                            "hechas": [], "decision": None}
        with tempfile.TemporaryDirectory() as carpeta:
            _limpiar()
            r = _correr(carpeta)
            assert r["motivo"] == "APAGADA" and _Escritor.creados == 0, r
            assert not (Path(carpeta) / "la_rotacion.json").exists()
        for valor in ("0", "", "no", "false"):
            _entorno(**{ENV: valor})
            assert activa() is False, valor
        for valor in ("1", "true", "si", "yes", " TRUE "):
            _entorno(**{ENV: valor})
            assert activa() is True, valor
    finally:
        _entorno(**antes)
    from src.telemetry.el_tablon import QUE_HACE

    assert "dos días sin subir" in QUE_HACE[ENV] and "99 %" in QUE_HACE[ENV], QUE_HACE.get(ENV)


def test_no_rotar_es_de_la_orden_viva():
    antes = _entorno(**ENCENDIDO)
    try:
        with tempfile.TemporaryDirectory() as carpeta:
            orden, _ = _ficheros(carpeta)
            assert no_rotados(orden, ANTES_DE_J9) == {18}
            assert no_rotados(orden, _utc(2026, 12, 1)) == set()        # caducada
            _entorno(BORDALAS_LA_ORDEN_DEL_GESTOR=None)
            assert no_rotados(orden, ANTES_DE_J9) == set()
    finally:
        _entorno(**antes)


def test_nunca_lanza_con_basura():
    for basura in (None, "x", 5, [1, 2], {"a": object()}, object()):
        d = decidir(plantilla=basura, fichas=basura, mercado=basura, subidas_de_ayer=basura,
                    rondas_jugadas=basura, saldo=basura, pujas_vivas=basura,
                    maximo_de_puja=basura, ofertas_del_computer=basura, en_venta=basura,
                    parejas=basura, protegidos=basura, no_rotar=basura, aguanta=basura,
                    vetados=basura, otros_venden=basura, vendidos=basura, listados=basura,
                    once=basura, reloj=basura)
        assert isinstance(d, dict) and d["acciones"] == [], d
        d = _d(plantilla=basura, fichas=basura, mercado=basura, parejas=basura, once=basura)
        assert isinstance(d, dict), d
        el_resumen(basura)
        al_dia(basura, plantilla=basura, pujas_de_la_foto=basura, foto_en=basura, ahora=basura)
        el_cupo(basura, basura, basura)
        el_once_de(basura)
        la_subida_de_ayer(basura, ANTES_DE_J9)
        por_que_no(basura)
        por_que_no_puja(basura)
        por_que_no_vende(basura)
        v = lo_de_esta_vuelta(basura, basura, basura, ANTES_DE_J9, basura, basura)
        assert v["pujas"] == {} and v["vendidos"] == {}, v
        assert rehacer(basura) == [] and la_ventana_de(basura) is None
        assert la_hora_de_la_foto(basura) is None
        if basura is not None:          # None seria el de produccion
            assert isinstance(el_registro(basura), list) and isinstance(leer_libro(basura), dict)
            assert las_parejas_abiertas(basura)["salen"] == set()
            assert las_parejas_abiertas(libro=basura)["salen"] == set()
        assert isinstance(escribir(basura, _Escritor()), list)
    assert apuntar({}, "x", 5, None, None, ANTES_DE_J9, "/no/se/puede/x.json")["escrito"] is False
    antes = _entorno(**ENCENDIDO)
    try:
        with tempfile.TemporaryDirectory() as carpeta:
            orden, ronda = _ficheros(carpeta)
            for basura in (None, "x", 5, [1, 2], {"snapshot": "x"}, {"snapshot": {"my_team": 5}}):
                nada = {} if basura is None else basura
                r = correr(cycle=nada, escritor_factory=_Escritor, ahora=ANTES_DE_J9,
                           calendario=CAL, orden_ruta=orden, libro_ronda_ruta=ronda,
                           libro_ruta=Path(carpeta) / "l.json",
                           registro_ruta=Path(carpeta) / "l.jsonl", historico=nada,
                           rondas_jugadas=nada, otros_venden=nada, v10=nada,
                           vuelta_mejora=nada, plan_cierre=nada)
                assert isinstance(r, dict) and r["motivo"], r
            r = correr(cycle={}, ahora=ANTES_DE_J9, calendario="x", orden_ruta=orden)
            assert r["motivo"] == "SIN_CALENDARIO", r
            # El escritor revienta: queda en `hechas` con el error, no lanza.
            r = _correr(carpeta, escritor_factory=_EscritorQueRevienta)
            assert r["motivo"] == "EJECUTADA" and all(h.get("error") for h in r["hechas"]), r
            # La fabrica revienta: el motivo lo dice.
            r = _correr(carpeta, escritor_factory=lambda: 1 / 0)
            assert r["motivo"].startswith("ERROR"), r
            # El libro roto no tumba nada.
            (Path(carpeta) / "roto.json").write_text("{no es json")
            assert leer_libro(Path(carpeta) / "roto.json") == {"parejas": []}
    finally:
        _entorno(**antes)


# ------------------------------------------------------------------
# 9. LO QUE DIJO LA REVISION (17/10/2026)
# ------------------------------------------------------------------

ONCE_442 = {"ids": ONCE, "formacion": "4-4-2"}


def test_la_caja_no_cuenta_una_venta_frenada():
    oferta = {5: {"offer_id": 905, "amount": 1_990_000}}
    ganada = dict(saldo=-432_317, pujas_vivas={}, mercado=LIBRE,
                  plantilla=set(PLANTILLA) | {101}, parejas=[_pareja(5, 101, GANADA)],
                  en_venta={5})
    # Martes 20/10, el aplazado del 21/10 es la proxima ronda: el 5 es
    # titular y no se vende hasta que acabe. Su 1,9 M no cuenta y con
    # -432.317 no se puja por el 109 (antes: 1,9 M fantasma, puja de
    # 1.049.900 y el aplazado empezaba en -1,48 M).
    martes = el_reloj(MARTES, CAL, True)
    d = _d(**ganada, ofertas_del_computer=oferta, once=ONCE_442, reloj=martes)
    assert _pujas(d) == [] and d["caja"]["cobros_esperados"] == 0, d["caja"]
    assert d["caja"]["antes"] == d["caja"]["despues"] == -432_317, d["caja"]
    assert {"accion": "NADA", "player_id": 5, "pareja": "5>101@2026-10-13",
            "motivo": "TITULAR_ANTES_DE_UNA_RONDA_PARCIAL"} in d["acciones"], d["acciones"]
    assert d["sin_cobro"] == {5: "TITULAR_ANTES_DE_UNA_RONDA_PARCIAL"}, d["sin_cobro"]
    # Sin oferta (publicado, esperando) tampoco cuenta.
    d = _d(**ganada, once=ONCE_442, reloj=martes)
    assert d["caja"]["cobros_esperados"] == 0 and _pujas(d) == [], d
    # Sin leer el once (y sin el de la foto) puede ser titular: no cuenta.
    d = _d(**ganada, ofertas_del_computer=oferta, once=None, reloj=martes)
    assert d["caja"]["cobros_esperados"] == 0 and _pujas(d) == [], d
    # Del banquillo en el once de la foto: se espera cobrar.
    d = _d(**ganada, reloj=martes, once_de_la_foto=[1, 2, 3, 4, 12, 6, 7, 8, 9, 10, 11])
    assert d["caja"]["cobros_esperados"] == 1_900_000 and d["sin_cobro"] == {}, d["caja"]
    # `no_rotar` (o proteger, o la cartera) puesto despues de emparejarlo:
    # no se vende, no cuenta, y el 17 por el 109 (gasta) no pasa.
    d = _d(**ganada, no_rotar={18, 5})
    assert d["sin_cobro"] == {5: "NO_ROTAR"} and d["caja"]["cobros_esperados"] == 0, d
    assert _pujas(d) == [], _pujas(d)
    # Titular sin relevo sano (el que entro en duda, el 12 lesionado): no cuenta.
    fichas = {**FICHAS, 101: {**FICHAS[101], "status": "doubt"},
              12: {**FICHAS[12], "status": "injured"}}
    d = _d(**ganada, fichas=fichas, once_de_la_foto=ONCE)
    assert d["sin_cobro"] == {5: "SIN_RELEVO_PARA_EL_ONCE"}, d["sin_cobro"]
    assert d["caja"]["cobros_esperados"] == 0, d["caja"]


def test_el_aplazado_del_21_de_19_a_21():
    # Lunes 19/10: la J9 se juega, el reset del martes cae despues; la
    # proxima ronda es el aplazado (solo dos equipos). El 5 es titular: su
    # venta se frena hasta el miercoles por la noche, asi que no paga la
    # puja por el 101 (antes pasaba con 300 mil: el aplazado empezaba en
    # -1,72 M). El 17 (banquillo) por el 109, si: 300.000 - 1.049.900 +
    # 760.000 = 10.100.
    lunes = el_reloj(LUNES, CAL, True)
    assert lunes["ronda_parcial"] and por_que_no_puja(lunes) is None, lunes
    d = _d(saldo=300_000, pujas_vivas={}, mercado=LIBRE, reloj=lunes, once_de_la_foto=ONCE)
    assert _pujas(d) == [(17, 109, 1_049_900)], _pujas(d)
    assert d["caja"]["despues"] == 10_100, d["caja"]
    assert d["parejas_nuevas"][0]["se_cobra_antes"] is True
    # Sin saber el once, cualquiera puede ser titular: ninguna.
    assert _pujas(_d(saldo=300_000, pujas_vivas={}, mercado=LIBRE, reloj=lunes)) == []
    # Fuera de una ronda de aplazados, el titular cuenta (se vende antes).
    d = _d(saldo=-432_317, pujas_vivas={}, mercado=LIBRE, once_de_la_foto=ONCE)
    assert _pujas(d) == [(5, 101, 1_569_900)] and d["caja"]["despues"] == -102_217, d
    # De punta a punta: el once sale de la foto (`user_lineup`). 1,4 M de
    # saldo y 1,1 M pujados por otro motor (el 106) = 300 mil.
    antes = _entorno(**ENCENDIDO)
    try:
        with tempfile.TemporaryDirectory() as carpeta:
            _limpiar()
            r = _correr(carpeta, ahora=LUNES, historico=_historico(date(2026, 10, 19)),
                        cycle={"snapshot": _la_foto(saldo=1_400_000,
                                                    cuando="2026-10-19T07:10:00")})
            assert r["motivo"] == "EJECUTADA", r
            assert [c[1]["player_id"] for c in _Escritor.llamadas] == [109], _Escritor.llamadas
    finally:
        _entorno(**antes)


# EL APLAZADO SOLO FRENA A LOS SUYOS (19/10/2026). El mismo calendario,
# con los nombres de verdad del Levante-Athletic del 21/10 (los de
# MARCA_CALENDAR), y los clubes de Biwenger en el catalogo.
CAL_REAL = {"matchdays": [
    CAL["matchdays"][0],
    {"matchday": 6, "matches": [
        {"matchday": 6, "home": "Levante UD", "away": "Athletic Club",
         "kickoff": "2026-10-21T20:00:00+02:00"}]},
    CAL["matchdays"][2],
]}
EQUIPOS = {1: "Levante", 2: "Athletic", 3: "Espanyol"}


def _de(equipo, *pids):
    """FICHAS con esos jugadores en ese club (`teamID`)."""
    return {**FICHAS, **{p: {**FICHAS[p], "teamID": equipo} for p in pids}}


def test_el_aplazado_solo_frena_a_los_suyos():
    # El reloj sabe quien juega la ronda de aplazados.
    lunes = el_reloj(LUNES, CAL_REAL, True)
    assert lunes["ronda_parcial"] and lunes["equipos_parcial"] == ["athletic", "levante"], lunes
    assert el_reloj(ANTES_DE_J9, CAL_REAL, True)["equipos_parcial"] is None
    # Un partido sin nombres: no se sabe, None (frena a todos).
    sin_nombres = {"matchdays": [CAL["matchdays"][0], {"matchday": 6, "matches": [
        {"matchday": 6, "home": "Levante UD", "away": "",
         "kickoff": "2026-10-21T20:00:00+02:00"}]}, CAL["matchdays"][2]]}
    assert el_reloj(LUNES, sin_nombres, True)["equipos_parcial"] is None

    # Lunes 19/10, 300 mil de caja. El 5 (titular que cae) del LEVANTE:
    # frenado como siempre, su venta no cuenta y solo pasa el 17 por el 109.
    base = dict(saldo=300_000, pujas_vivas={}, mercado=LIBRE, reloj=lunes,
                once_de_la_foto=ONCE, equipos=EQUIPOS)
    d = _d(**base, fichas=_de(1, 5))
    assert _pujas(d) == [(17, 109, 1_049_900)], _pujas(d)
    # Del ESPANYOL: no juega el aplazado, su venta (1,9 M, se cobra antes)
    # cuenta y el 5 por el 101 pasa: 300.000 - 1.569.900 + 1.900.000 =
    # 630.100; y despues el 17 por el 109: 340.200.
    d = _d(**base, fichas=_de(3, 5))
    assert _pujas(d) == [(5, 101, 1_569_900), (17, 109, 1_049_900)], _pujas(d)
    assert d["caja"]["despues"] == 340_200, d["caja"]
    assert d["parejas_nuevas"][0]["se_cobra_antes"] is True
    # Sin saber de que club es (sin `equipos` o sin `teamID`): frena.
    d = _d(**{**base, "equipos": None}, fichas=_de(3, 5))
    assert _pujas(d) == [(17, 109, 1_049_900)], _pujas(d)
    assert _pujas(_d(**base)) == [(17, 109, 1_049_900)]

    # Martes 20/10, la pareja 5>101 ganada y oferta de 1,99 M. Del
    # Levante: no se vende y su cobro no cuenta.
    martes = el_reloj(MARTES, CAL_REAL, True)
    ganada = dict(saldo=-432_317, pujas_vivas={}, mercado=LIBRE,
                  plantilla=set(PLANTILLA) | {101}, parejas=[_pareja(5, 101, GANADA)],
                  en_venta={5}, ofertas_del_computer={5: {"offer_id": 905, "amount": 1_990_000}},
                  once=ONCE_442, reloj=martes, equipos=EQUIPOS)
    d = _d(**ganada, fichas=_de(1, 5, 101))
    assert d["sin_cobro"] == {5: "TITULAR_ANTES_DE_UNA_RONDA_PARCIAL"}, d["sin_cobro"]
    assert _acciones(d, "ACEPTAR_OFERTA_DEL_COMPUTER") == [] and _pujas(d) == [], d
    # Del Espanyol: el once con el 101 en su sitio y se acepta. Con ese
    # 1,99 M la caja pasa a +1.557.683 y cabe el 17 por el 109, que solo
    # sale si la aceptacion entra (`cuenta_con_lo_aceptado`).
    d = _d(**ganada, fichas=_de(3, 5, 101))
    assert _acciones(d)[:2] == [("CAMBIAR_EL_ONCE", None),
                                ("ACEPTAR_OFERTA_DEL_COMPUTER", 5)], d["acciones"]
    assert d["sin_cobro"] == {} and d["caja"]["cobros_esperados"] == 1_990_000, d["caja"]
    assert [(a["player_id"], a["cuenta_con_lo_aceptado"]) for a in d["acciones"]
            if a["accion"] == "PUJAR"] == [(109, [5])], d["acciones"]

    # LA CAJA NO CAMBIA. El martes la venta del 5 ya no se cobra antes del
    # aplazado (dos resets: el del miercoles no llega a cobrar), asi que,
    # aunque sea del Espanyol, el 5 por el 101 no pasa en rojo ni con 300
    # mil: el aplazado empezaria en negativo.
    for saldo in (-432_317, 300_000):
        d = _d(saldo=saldo, pujas_vivas={}, mercado=LIBRE, reloj=martes,
               once_de_la_foto=ONCE, equipos=EQUIPOS, fichas=_de(3, 5))
        assert d["por_que_no_puja"] is None and (5, 101, 1_569_900) not in _pujas(d), d
        assert d["caja"]["despues"] >= 0 or d["caja"]["despues"] >= d["caja"]["antes"], d["caja"]

    # DOS RONDAS DE APLAZADOS SEGUIDAS. Un Rayo-Getafe de la J8 el jueves
    # 22/10 (o esa misma tarde, a la misma hora o despues del
    # Levante-Athletic) es otra ronda de aplazados antes de la J10: el
    # titular del Rayo tambien se frena, aunque no juegue la primera.
    equipos_rayo = {**EQUIPOS, 4: "Rayo Vallecano"}
    for hora in ("2026-10-22T20:00:00+02:00", "2026-10-21T20:00:00+02:00",
                 "2026-10-21T21:00:00+02:00", "2026-10-21T19:00:00+02:00"):
        cal = json.loads(json.dumps(CAL_REAL))
        cal["matchdays"].insert(2, {"matchday": 8, "matches": [
            {"matchday": 8, "home": "Rayo Vallecano", "away": "Getafe CF", "kickoff": hora}]})
        martes_j8 = el_reloj(MARTES, cal, True)
        assert martes_j8["equipos_parcial"] == ["athletic", "getafe", "levante", "rayo"], (
            hora, martes_j8)
        for club in (4, 1):
            d = _d(**{**ganada, "reloj": martes_j8, "equipos": equipos_rayo},
                   fichas=_de(club, 5, 101))
            assert _acciones(d) == [("NADA", 5)], (hora, club, d["acciones"])
            assert d["sin_cobro"] == {5: "TITULAR_ANTES_DE_UNA_RONDA_PARCIAL"}, (hora, club)
        # Y el del Espanyol, que no juega ninguna, se sigue vendiendo.
        d = _d(**{**ganada, "reloj": martes_j8, "equipos": equipos_rayo},
               fichas=_de(3, 5, 101))
        assert d["sin_cobro"] == {} and ("ACEPTAR_OFERTA_DEL_COMPUTER", 5) in _acciones(d), (
            hora, d["acciones"])
        # El lunes la venta del del Rayo no paga el 5 por el 101.
        lunes_j8 = el_reloj(LUNES, cal, True)
        d = _d(**{**base, "reloj": lunes_j8, "equipos": equipos_rayo}, fichas=_de(4, 5))
        assert _pujas(d) == [(17, 109, 1_049_900)], (hora, _pujas(d))
        assert d["caja"]["despues"] == 10_100, d["caja"]
    # Una de ellas sin nombres: no se sabe, None (frena a todos).
    cal = json.loads(json.dumps(CAL_REAL))
    cal["matchdays"].insert(2, {"matchday": 8, "matches": [
        {"matchday": 8, "home": "Rayo Vallecano", "away": "",
         "kickoff": "2026-10-22T20:00:00+02:00"}]})
    assert el_reloj(MARTES, cal, True)["equipos_parcial"] is None
    # Con la J10 (entera) por medio, la de despues ya no cuenta.
    cal = json.loads(json.dumps(CAL_REAL))
    cal["matchdays"].append({"matchday": 8, "matches": [
        {"matchday": 8, "home": "Rayo Vallecano", "away": "Getafe CF",
         "kickoff": "2026-10-28T20:00:00+01:00"}]})
    assert el_reloj(MARTES, cal, True)["equipos_parcial"] == ["athletic", "levante"]

    # De punta a punta: el club sale del catalogo de la foto (`teams`).
    antes = _entorno(**ENCENDIDO)
    try:
        for club, pujados in ((3, [101, 109]), (1, [109])):
            with tempfile.TemporaryDirectory() as carpeta:
                _limpiar()
                foto = _la_foto(saldo=1_400_000, cuando="2026-10-19T07:10:00")
                foto["catalog"] = {"data": {
                    "players": {str(p): f for p, f in _de(club, 5).items()},
                    "teams": {str(k): {"id": k, "name": v} for k, v in EQUIPOS.items()}}}
                r = _correr(carpeta, ahora=LUNES, calendario=CAL_REAL,
                            historico=_historico(date(2026, 10, 19)), cycle={"snapshot": foto})
                assert r["motivo"] == "EJECUTADA", r
                assert [c[1]["player_id"] for c in _Escritor.llamadas] == pujados, (
                    club, _Escritor.llamadas)
                assert r["reloj"]["equipos_parcial"] == ["athletic", "levante"], r["reloj"]
    finally:
        _entorno(**antes)


def test_si_la_aceptacion_no_entra_no_se_puja_con_su_dinero():
    oferta = {5: {"offer_id": 905, "amount": 1_990_000}}
    base = dict(pujas_vivas={}, mercado=LIBRE, plantilla=set(PLANTILLA) | {101},
                parejas=[_pareja(5, 101, GANADA)], ofertas_del_computer=oferta, once=ONCE_442)
    # -432.317 + 1.990.000 de la aceptacion: el 109 cabe SOLO con ella.
    d = _d(**base, saldo=-432_317)
    assert [(a["accion"], a.get("player_id"), a.get("cuenta_con_lo_aceptado"))
            for a in d["acciones"]] == [("CAMBIAR_EL_ONCE", None, None),
                                         ("ACEPTAR_OFERTA_DEL_COMPUTER", 5, None),
                                         ("PUJAR", 109, [5])], d["acciones"]
    assert d["caja"]["aceptado_en_esta_vuelta"] == 1_990_000
    # Con caja de sobra, la puja no depende de nada.
    assert [a["cuenta_con_lo_aceptado"] for a in _d(**base, saldo=5_000_000)["acciones"]
            if a["accion"] == "PUJAR"] == [[]]
    escrituras = [a for a in d["acciones"] if a["accion"] != "NADA"]

    class _NoAcepta(_Escritor):
        def accept_offer(self, **k):
            type(self).llamadas.append(("accept_offer", k))
            return {"sent": True, "success": False, "http_status": 409}

    # El rastro del once, en el temporal (nunca en el libro de produccion).
    with tempfile.TemporaryDirectory() as carpeta:
        rastro = Path(carpeta) / "rastro.jsonl"
        # El once no se guarda: ni la venta ni la puja.
        _limpiar(guarda=False)
        hechas = escribir(escrituras, _Escritor(), rastro)
        assert [c[0] for c in _Escritor.llamadas] == ["save_lineup"], _Escritor.llamadas
        assert [(h["accion"], h.get("error")) for h in hechas] == [
            ("CAMBIAR_EL_ONCE", None), ("ACEPTAR_OFERTA_DEL_COMPUTER", "EL_ONCE_NO_SE_GUARDO"),
            ("PUJAR", SIN_EL_COBRO)], hechas
        # Biwenger rechaza la aceptacion: tampoco.
        _limpiar()
        hechas = escribir(escrituras, _NoAcepta(), rastro)
        assert "place_bid" not in [c[0] for c in _Escritor.llamadas], _Escritor.llamadas
        assert hechas[-1]["error"] == SIN_EL_COBRO
        # Entra: se puja.
        _limpiar()
        escribir(escrituras, _Escritor(), rastro)
        assert [c[0] for c in _Escritor.llamadas] == ["save_lineup", "accept_offer", "place_bid"]
        # La que no se mando no deja pareja (ni FALLIDA: se mira en la
        # vuelta siguiente), pero si su linea en el registro.
        libro = Path(carpeta) / "la_rotacion.json"
        r = apuntar({}, [_pareja(5, 101, GANADA)], [],
                    [{**escrituras[-1], "enviada": False, "exito": False, "error": SIN_EL_COBRO}],
                    d["parejas_nuevas"], ANTES_DE_J9, libro)
        assert [p["id"] for p in r["parejas"]] == ["5>101@2026-10-13"], r["parejas"]
        assert [x["evento"] for x in el_registro(libro.with_suffix(".jsonl"))] == ["PUJAR"]


def test_la_ventana_es_la_ronda_y_no_su_hora():
    # El primer partido de la J9 se mueve de viernes a sabado a mitad de
    # ventana: la ventana sigue siendo la misma y las dos parejas cuentan.
    movido = json.loads(json.dumps(CAL))
    movido["matchdays"][0]["matches"][0]["kickoff"] = "2026-10-17T14:00:00+02:00"
    antes, despues = el_reloj(ANTES_DE_J9, CAL, True), el_reloj(ANTES_DE_J9, movido, True)
    assert antes["inicio_ronda"] != despues["inicio_ronda"], (antes, despues)
    assert antes["ventana"] == despues["ventana"] == J9, (antes, despues)
    dos = [_pareja(30, 301, PUJADA), _pareja(31, 311, GANADA)]
    assert el_cupo(dos, despues["ventana"], "2026-W43") == {"ventana": 2, "semana": 0, "quedan": 0}
    assert _d(parejas=dos, reloj=despues)["por_que_no_puja"] == "SIN_CUPO"
    # Los aplazados fuera de su jornada son otra ventana.
    assert la_ventana_de({"jornada": 6, "aparte": True}) == "J6-aparte"
    assert la_ventana_de({"jornada": 10, "aparte": False}) == "J10"
    # La ventana sola aprieta: dos en la de la J10 de la semana 42 y el
    # jueves 22/10 (semana 43, misma ventana) no queda cupo.
    jueves = el_reloj(JUEVES, CAL, True)
    dos = [_pareja(30, 301, VENDIDA, "2026-10-18", J10, "2026-W42"),
           _pareja(31, 311, PUJADA, "2026-10-18", J10, "2026-W42")]
    assert el_cupo(dos, J10, "2026-W43") == {"ventana": 2, "semana": 0, "quedan": 0}
    d = _d(parejas=dos, reloj=jueves)
    assert _pujas(d) == [] and d["por_que_no_puja"] == "SIN_CUPO", d


def test_nunca_en_la_franja_de_silencio():
    # Las vueltas de la ventana (04:45 y 04:50, con 12 min de gracia) si
    # pueden escribir; la rotacion no: no es trabajo de la ventana y la
    # subasta del reset que v10 puja en ellas no esta en su caja.
    antes = _entorno(**ENCENDIDO)
    try:
        with tempfile.TemporaryDirectory() as carpeta:
            for h, m in ((2, 45), (2, 52), (2, 57), (3, 2)):      # 04:45-05:02 de Madrid
                _limpiar()
                r = _correr(carpeta, ahora=_utc(2026, 10, 22, h, m))
                assert r["motivo"] == "ZONA_DE_SILENCIO" and _Escritor.creados == 0, (h, m, r)
                assert r["reloj"]["puede_escribir"] is False
            assert not (Path(carpeta) / "la_rotacion.json").exists()
            # A las 07:15 de Madrid (05:15 UTC), si.
            _limpiar()
            r = _correr(carpeta, ahora=JUEVES, cycle={"snapshot": _la_foto(
                cuando="2026-10-22T07:10:00")})
            assert r["motivo"] != "ZONA_DE_SILENCIO", r
    finally:
        _entorno(**antes)


def test_lo_vendido_en_esta_vuelta():
    # El que entro lo vendio otro en esta vuelta: el que iba a salir no se
    # vende, y su cobro no cuenta.
    d = _d(plantilla=set(PLANTILLA) | {102}, parejas=[_pareja(12, 102, GANADA)],
           vendidos={102}, en_venta={12}, once=ONCE_442, reloj=el_reloj(JUEVES, CAL, True),
           ofertas_del_computer={12: {"offer_id": 912, "amount": 499_000}})
    assert _acciones(d, "ACEPTAR_OFERTA_DEL_COMPUTER") == [], d["acciones"]
    assert {"accion": "NADA", "player_id": 12, "pareja": "12>102@2026-10-13",
            "motivo": "EL_QUE_ENTRO_SE_VENDIO_EN_ESTA_VUELTA"} in d["acciones"]
    assert d["caja"]["cobros_esperados"] == 0, d["caja"]
    # `al_dia` con lo vendido en esta vuelta: ROTA si es el que entro,
    # VENDIDA si es el que salia.
    p, e = al_dia([_pareja(5, 101, GANADA)], plantilla=set(PLANTILLA) | {101},
                  pujas_de_la_foto=set(), vendidos={101})
    assert p[0]["estado"] == ROTA and e[0]["evento"] == ROTA, p
    p, _ = al_dia([_pareja(5, 101, GANADA)], plantilla=set(PLANTILLA) | {101},
                  pujas_de_la_foto=set(), vendidos={5})
    assert p[0]["estado"] == VENDIDA, p
    # Lo que vende otro libro no cae.
    d = _d(otros_venden={5})
    assert {"player_id": 5, "nombre": "Cae titular", "por": "LO_VENDE_OTRO_LIBRO"} in d["no_rota"]
    assert 5 not in [s for s, _, _ in _pujas(d)], _pujas(d)
    # Publicado, sin oferta, y la del proximo reset no llega antes de la
    # ronda (miercoles: el aplazado a las 20:00): no se espera cobrar.
    base = dict(plantilla=set(PLANTILLA) | {103}, parejas=[_pareja(12, 103, GANADA)],
                en_venta={12})
    assert _d(**base)["caja"]["cobros_esperados"] == 475_000
    assert _d(**base, reloj=el_reloj(MIERCOLES, CAL, True))["caja"]["cobros_esperados"] == 0
    # Y el viernes 23/10, la J10 (ronda entera) a las 21:00, antes del reset.
    viernes = el_reloj(VIERNES, CAL, True)
    assert not viernes["ronda_parcial"] and viernes["horas_ronda"] == 13.75, viernes
    d = _d(**base, reloj=viernes)
    assert d["caja"]["cobros_esperados"] == 0 and d["sin_cobro"] == {}, d


def test_lo_de_esta_vuelta_llega_a_la_rotacion():
    antes = _entorno(**ENCENDIDO)
    try:
        with tempfile.TemporaryDirectory() as carpeta:
            # v10 de ESTA vuelta: la ronda pujo por el 101 y cobro al 17.
            v10 = {"timestamp": ANTES_DE_J9.isoformat(), "ronda": {"hechas": [
                {"accion": "PUJAR", "player_id": 101, "importe": 1_600_000, "exito": True},
                {"accion": "ACEPTAR_OFERTA_DEL_COMPUTER", "player_id": 17, "importe": 790_000,
                 "exito": True}]}}
            _limpiar()
            r = _correr(carpeta, v10=v10)
            d = r["decision"]
            por = {n["player_id"]: n["por"] for n in d["no_rota"]}
            assert por.get(17) == "VENDIDO_O_PUBLICADO_EN_ESTA_VUELTA", por
            assert d["caja"]["pujas_vivas"] == 1_100_000 + 1_600_000, d["caja"]
            pujados = [c[1]["player_id"] for c in _Escritor.llamadas if c[0] == "place_bid"]
            assert 101 not in pujados and pujados[0] == 102, _Escritor.llamadas
        with tempfile.TemporaryDirectory() as carpeta:
            # El parte (su fichero de la vuelta) vendio al 12 y publico al 17.
            parte = {"run_id": None, "generated_at": ANTES_DE_J9.isoformat(), "hechas": [
                {"accion": "ACEPTAR_OFERTA_DEL_COMPUTER", "player_id": 12, "importe": 480_000,
                 "exito": True, "enviada": True},
                {"accion": "PONER_A_LA_VENTA", "player_id": 17, "precio": 800_000,
                 "exito": True, "enviada": True}]}
            _limpiar()
            r = _correr(carpeta, vuelta_parte=parte)
            por = {n["player_id"]: n["por"] for n in r["decision"]["no_rota"]}
            assert por.get(12) == por.get(17) == "VENDIDO_O_PUBLICADO_EN_ESTA_VUELTA", por
            # De otra vuelta (hace una hora), no cuenta.
            _limpiar()
            vieja = {**parte, "generated_at": ANTES_DE_J9.replace(hour=4).isoformat()}
            r = _correr(carpeta, vuelta_parte=vieja, libro_ruta=Path(carpeta) / "otro.json",
                        registro_ruta=Path(carpeta) / "otro.jsonl")
            assert any(v.startswith("parte:") for v in r["vuelta_descartada"]), r
            assert 17 in [c["player_id"] for c in r["decision"]["caidos"]]
        # El parte lo deja desde su `main`, encendido (no desde `correr`).
        import src.actions.el_parte_vende as parte_mod

        with tempfile.TemporaryDirectory() as carpeta:
            ruta, correr_de_verdad = parte_mod.VUELTA_PARTE, parte_mod.correr
            try:
                parte_mod.VUELTA_PARTE = Path(carpeta) / "el_parte_vuelta.json"
                parte_mod.correr = lambda: {"activa": True, "motivo": "EJECUTADA",
                                            "hechas": parte["hechas"]}
                with contextlib.redirect_stdout(io.StringIO()):
                    parte_mod.main()
                escrito = json.loads(parte_mod.VUELTA_PARTE.read_text())
                assert escrito["hechas"] == parte["hechas"] and escrito["generated_at"], escrito
                parte_mod.VUELTA_PARTE.unlink()
                parte_mod.correr = lambda: {"activa": False, "motivo": "APAGADA", "hechas": []}
                with contextlib.redirect_stdout(io.StringIO()):
                    parte_mod.main()
                assert not parte_mod.VUELTA_PARTE.exists()
            finally:
                parte_mod.VUELTA_PARTE, parte_mod.correr = ruta, correr_de_verdad
    finally:
        _entorno(**antes)


def test_lo_que_el_cierre_ya_vende_no_se_empareja():
    from src.analysis.los_que_otros_venden import lo_que_vende_el_cierre

    plan = {"generated_at": ANTES_DE_J9.isoformat(), "vender": [12],
            "candidatos": [{"id": 12, "elegido": True}, {"id": 17, "elegido": False}]}
    assert lo_que_vende_el_cierre(plan, ANTES_DE_J9) == {12}
    assert lo_que_vende_el_cierre(plan, ANTES_DE_J9.replace(hour=9)) == set()   # de hace 4 h
    # -432.317: el cierre ya eligio vender al 12 (cuenta con su dinero).
    # Emparejarlo con el 111 (400 mil) contaba su 95 % dos veces.
    fichas = {**FICHAS, 111: _f(111, "Barato que sube", 2, 400_000, 20_000, 30)}
    base = dict(fichas=fichas, mercado={**LIBRE, 111: 400_000}, saldo=-432_317, pujas_vivas={},
                en_venta={12}, no_rotar={5, 17, 18})
    assert _pujas(_d(**base)) == [(12, 111, 449_900)], _pujas(_d(**base))
    assert _pujas(_d(**base, otros_venden={12})) == []
    antes = _entorno(**ENCENDIDO)
    try:
        with tempfile.TemporaryDirectory() as carpeta:
            _limpiar()
            r = _correr(carpeta, plan_cierre=plan)
            por = {n["player_id"]: n["por"] for n in r["decision"]["no_rota"]}
            assert por.get(12) == "LO_VENDE_OTRO_LIBRO", por
            # Sus `candidatos` no: el 17 se sigue cambiando.
            assert 17 in [c["player_id"] for c in r["decision"]["caidos"]], r["decision"]
    finally:
        _entorno(**antes)


def test_el_que_entra_no_es_de_otro_libro():
    # La cartera lo aguanta, otro libro lo vende o es un `fichar` del
    # gestor: el 5 se lleva el 102 en vez del 101.
    for k in ({"aguanta": {20, 101}}, {"otros_venden": {101}}, {"protegidos": {19, 101}}):
        assert _pujas(_d(**k))[0] == (5, 102, 1_569_900), (k, _pujas(_d(**k)))


def test_el_relevo_no_lo_vende_otro_sin_mirar_el_once():
    oferta = {5: {"offer_id": 905, "amount": 1_990_000}}
    fichas = {**FICHAS, 101: {**FICHAS[101], "status": "doubt"},
              21: _f(21, "Defensa de la cartera", 2, 1_000_000, 10_000, 40),
              22: _f(22, "Defensa suplente", 2, 1_000_000, -5_000, 15)}
    base = dict(fichas=fichas, parejas=[_pareja(5, 101, GANADA)], ofertas_del_computer=oferta,
                once=ONCE_442)
    # Sin nadie mas: el de mas xP del banquillo (21, 40 puntos; no el 12
    # de 5 ni el 22 de 15).
    d = _d(**base, plantilla=set(PLANTILLA) | {101, 21, 22})
    assert d["acciones"][0]["entran"] == [21], d["acciones"]
    # El 21 lo aguanta la cartera (o lo vende otro): el 22, el siguiente.
    for k in ({"aguanta": {20, 21}}, {"otros_venden": {21}}, {"listados": {21}}):
        d = _d(**base, plantilla=set(PLANTILLA) | {101, 21, 22}, **k)
        assert d["acciones"][0]["entran"] == [22], (k, d["acciones"])
    # Solo quedan los de otros: no se vende.
    fichas[12] = {**FICHAS[12], "status": "injured"}
    d = _d(**base, plantilla=set(PLANTILLA) | {101, 21}, aguanta={20, 21})
    assert _acciones(d, "ACEPTAR_OFERTA_DEL_COMPUTER") == [], d["acciones"]
    assert any(a.get("motivo") == "SIN_RELEVO_PARA_EL_ONCE" for a in d["acciones"])


def test_el_once_incompleto_no_se_toca():
    oferta = {5: {"offer_id": 905, "amount": 1_990_000}}
    base = dict(parejas=[_pareja(5, 101, GANADA)], ofertas_del_computer=oferta,
                plantilla=set(PLANTILLA) | {101})
    for once in ({"ids": ONCE, "formacion": None}, {"ids": ONCE[:10], "formacion": "4-4-2"},
                 {"ids": ONCE[:10] + [5], "formacion": "4-4-2"}):
        d = _d(**base, once=once)
        assert _acciones(d, "CAMBIAR_EL_ONCE") == [] and \
            _acciones(d, "ACEPTAR_OFERTA_DEL_COMPUTER") == [], (once, d["acciones"])
        assert {"accion": "NADA", "player_id": 5, "pareja": "5>101@2026-10-13",
                "motivo": "ONCE_INCOMPLETO"} in d["acciones"], (once, d["acciones"])
        assert d["sin_cobro"] == {5: "ONCE_INCOMPLETO"}


def test_la_hora_de_la_foto_es_de_madrid():
    # La foto de las 08:07 de Madrid (06:07 UTC, sin zona) es de ANTES de
    # la puja de las 06:14 UTC: la puja sigue viva (antes: PERDIDA).
    pujada = _pareja(5, 101, PUJADA, pujada_en="2026-10-14T06:14:00+00:00")
    assert la_hora_de_la_foto("2026-10-14T08:07:00") == _utc(2026, 10, 14, 6, 7)
    assert la_hora_de_la_foto("2026-12-14T08:07:00") == _utc(2026, 12, 14, 7, 7)   # invierno
    assert la_hora_de_la_foto("2026-10-14T06:07:00+00:00") == _utc(2026, 10, 14, 6, 7)
    p, e = al_dia([pujada], plantilla=set(PLANTILLA), pujas_de_la_foto=set(),
                  foto_en="2026-10-14T08:07:00", ahora=_utc(2026, 10, 14, 7, 14))
    assert p[0]["estado"] == PUJADA and e == [], p
    # La de las 07:05 de Madrid del 15/10 (05:05 UTC) aun no sabe si se
    # perdio en el reset de las 07:00; leida como UTC (07:05) lo daba.
    p, _ = al_dia([pujada], plantilla=set(PLANTILLA), pujas_de_la_foto=set(),
                  foto_en="2026-10-15T07:05:00", ahora=_utc(2026, 10, 15, 5, 15))
    assert p[0]["estado"] == PUJADA, p
    # Una foto de despues de la puja pero de antes del reset que la
    # resuelve (15/10 07:00 de Madrid) tampoco la da por perdida.
    p, _ = al_dia([pujada], plantilla=set(PLANTILLA), pujas_de_la_foto=set(),
                  foto_en="2026-10-14T20:00:00", ahora=_utc(2026, 10, 14, 18, 30))
    assert p[0]["estado"] == PUJADA, p
    # Despues del reset, si.
    p, _ = al_dia([pujada], plantilla=set(PLANTILLA), pujas_de_la_foto=set(),
                  foto_en="2026-10-15T07:12:00", ahora=_utc(2026, 10, 15, 5, 15))
    assert p[0]["estado"] == PERDIDA, p
    # Perdida por una foto vieja y el 101 aparece antes del reset siguiente:
    # vuelve a GANADA. Despues de ese reset, no (lo habra comprado otro).
    perdida = {**pujada, "estado": PERDIDA}
    p, e = al_dia([perdida], plantilla=set(PLANTILLA) | {101}, pujas_de_la_foto=set(),
                  foto_en="2026-10-15T09:10:00", ahora=_utc(2026, 10, 15, 7, 15))
    assert p[0]["estado"] == GANADA and e[0]["evento"] == GANADA, p
    p, _ = al_dia([perdida], plantilla=set(PLANTILLA) | {101}, pujas_de_la_foto=set(),
                  foto_en="2026-10-16T09:10:00", ahora=_utc(2026, 10, 16, 7, 15))
    assert p[0]["estado"] == PERDIDA, p


def test_el_estado_se_rehace_del_registro():
    antes = _entorno(**ENCENDIDO)
    try:
        with tempfile.TemporaryDirectory() as carpeta:
            libro = Path(carpeta) / "la_rotacion.json"
            _limpiar()
            assert _correr(carpeta)["motivo"] == "EJECUTADA"
            guardadas = leer_libro(libro)["parejas"]
            assert [(p["sale"], p["entra"], p["estado"]) for p in guardadas] == [
                (5, 101, PUJADA), (17, 109, PUJADA)]
            # Se pierde el estado (la cache se desalojo; el registro, de git).
            libro.unlink()
            rehecho = leer_libro(libro)
            assert rehecho["rehecho"] is True and rehecho["parejas"] == guardadas, rehecho
            assert los_que_rota(libro) == {5, 17}
            # Otra vuelta el mismo dia: ni otra puja por el 5 y el 17 ni
            # cupo de mas (antes: pujas por el 102 y el 103).
            _limpiar()
            r = _correr(carpeta, ahora=ANTES_DE_J9.replace(hour=6))
            assert r["motivo"] == "NADA_QUE_HACER" and r["libro_rehecho"], r
            assert _Escritor.creados == 0
            assert leer_libro(libro)["parejas"] == guardadas and "rehecho" not in leer_libro(libro)
            # Un estado mas viejo que el registro tambien se rehace.
            libro.write_text(json.dumps({"actualizado": "2026-10-01T00:00:00+00:00",
                                         "parejas": []}))
            assert leer_libro(libro)["parejas"] == guardadas
            # Al dia siguiente: el 101 llega, se publica al 5; sin estado,
            # se rehace con todo.
            _limpiar()
            foto = _la_foto(plantilla=set(PLANTILLA) | {101}, cuando="2026-10-15T07:12:00")
            _correr(carpeta, cycle={"snapshot": foto}, ahora=_utc(2026, 10, 15, 5, 15))
            despues = leer_libro(libro)["parejas"]
            libro.unlink()
            assert leer_libro(libro)["parejas"] == despues, (leer_libro(libro), despues)
            estados = {(p["sale"], p["entra"]): p["estado"] for p in despues}
            assert estados[(5, 101)] == GANADA and estados[(17, 109)] == PERDIDA, estados
    finally:
        _entorno(**antes)


def test_los_demas_motores_ven_las_parejas():
    from src.analysis.los_que_otros_venden import quien_los_vende

    antes = _entorno(**{**ENCENDIDO, "BORDALAS_LA_ORDEN_DEL_GESTOR": None,
                        "BORDALAS_EL_CIERRE_DE_LA_JORNADA": "1", "BORDALAS_LA_CARTERA": None,
                        "BORDALAS_LA_PUJA_EN_9900": None})
    try:
        with tempfile.TemporaryDirectory() as carpeta:
            libro = Path(carpeta) / "la_rotacion.json"
            libro.write_text(json.dumps({"parejas": [
                _pareja(5, 101, PUJADA), _pareja(12, 103, GANADA), _pareja(17, 109, PERDIDA)]}))
            assert las_parejas_abiertas(libro) == {"salen": {5, 12}, "entran": {101, 103},
                                                   "se_van": {12}}
            # El reroll del orquestador no tira sus ofertas.
            rutas = {k: Path(carpeta) / f"{k}.json" for k in ("ronda", "chollos", "mejora",
                                                               "cierre", "orden")}
            assert quien_los_vende({**rutas, "rotacion": libro}, ANTES_DE_J9) == {
                5: ["LA_ROTACION"], 12: ["LA_ROTACION"]}
            # La mejora del once no le busca otro relevo al que sale (ni
            # puja por el que entra), dado o de su libro junto al de la mejora.
            import src.analysis.test_la_mejora_del_once_v1 as mejora

            s, escritor, _ = mejora._correr([40], [41], [40], con_calendario=True)
            assert s["motivo"] == "EJECUTADA", s
            s, escritor, _ = mejora._correr([40], [41], [40], con_calendario=True, rotando={40})
            assert s["motivo"] == "NADA_QUE_HACER" and escritor.llamadas == [], s
            s, escritor, _ = mejora._correr([40], [41], [40], con_calendario=True,
                                            rotacion={"parejas": [_pareja(40, 999, PUJADA)]})
            assert s["motivo"] == "NADA_QUE_HACER" and escritor.llamadas == [], s
            # El cierre no pone en su once al que sale de una pareja ganada.
            import src.analysis.test_el_cierre_de_la_jornada_v1 as cierre
            from src.actions.el_cierre_de_la_jornada import correr as correr_el_cierre

            libros = {"ronda": {}, "chollos": {}, "mejora": {},
                      "rotacion": {"parejas": [_pareja(12, 999, GANADA)]}}
            r = correr_el_cierre(status=cierre._status_con(once_escrito=cierre.ONCE),
                                 snapshot=cierre._foto_con(saldo=10_000_000), v10={},
                                 libros=libros, calendario=cierre.CAL,
                                 orden_ruta=Path(carpeta) / "no.json",
                                 escritor_factory=cierre._Escritor, ahora=cierre.AHORA,
                                 plan_ruta=Path(carpeta) / "plan.json")
            assert 12 not in r["decision"]["once"]["ids"], r["decision"]["once"]
            # Apagada, nadie ve nada.
            _entorno(**{ENV: None})
            assert las_parejas_abiertas(libro) == {"salen": set(), "entran": set(),
                                                   "se_van": set()}
            assert quien_los_vende({**rutas, "rotacion": libro}, ANTES_DE_J9) == {}
            s, _, _ = mejora._correr([40], [41], [40], con_calendario=True,
                                     rotacion={"parejas": [_pareja(40, 999, PUJADA)]})
            assert s["motivo"] == "EJECUTADA", s
            r = correr_el_cierre(status=cierre._status_con(once_escrito=cierre.ONCE),
                                 snapshot=cierre._foto_con(saldo=10_000_000), v10={},
                                 libros=libros, calendario=cierre.CAL,
                                 orden_ruta=Path(carpeta) / "no.json",
                                 escritor_factory=cierre._Escritor, ahora=cierre.AHORA,
                                 plan_ruta=Path(carpeta) / "plan.json")
            assert 12 in r["decision"]["once"]["ids"], r["decision"]["once"]
    finally:
        _entorno(**antes)


TESTS = [
    test_el_que_cae_dos_dias_sin_subir,
    test_ayer_sale_del_historico_y_sin_muestra_no_cae,
    test_el_que_entra_y_el_desempate_por_xp,
    test_dos_por_ventana_y_por_semana,
    test_el_reloj_y_el_aplazado,
    test_con_saldo_negativo_solo_lo_que_no_gasta_caja,
    test_solo_se_vende_cuando_el_que_entra_ha_llegado,
    test_el_99_y_el_95_con_prisa,
    test_el_titular_no_deja_un_hueco,
    test_puja_perdida_nunca_vende_y_se_reintenta,
    test_de_punta_a_punta,
    test_si_el_once_no_se_guarda_no_se_vende,
    test_el_once_vigente_se_lee_de_biwenger,
    test_el_motor_viejo_no_vende_al_que_rota,
    test_nace_apagada,
    test_no_rotar_es_de_la_orden_viva,
    test_nunca_lanza_con_basura,
    test_la_caja_no_cuenta_una_venta_frenada,
    test_el_aplazado_del_21_de_19_a_21,
    test_el_aplazado_solo_frena_a_los_suyos,
    test_si_la_aceptacion_no_entra_no_se_puja_con_su_dinero,
    test_la_ventana_es_la_ronda_y_no_su_hora,
    test_nunca_en_la_franja_de_silencio,
    test_lo_vendido_en_esta_vuelta,
    test_lo_de_esta_vuelta_llega_a_la_rotacion,
    test_lo_que_el_cierre_ya_vende_no_se_empareja,
    test_el_que_entra_no_es_de_otro_libro,
    test_el_relevo_no_lo_vende_otro_sin_mirar_el_once,
    test_el_once_incompleto_no_se_toca,
    test_la_hora_de_la_foto_es_de_madrid,
    test_el_estado_se_rehace_del_registro,
    test_los_demas_motores_ven_las_parejas,
]


def main() -> None:
    fallos = 0
    for test in TESTS:
        try:
            test()
            print(f"OK   {test.__name__}")
        except Exception as error:                  # noqa: BLE001
            fallos += 1
            print(f"FALLA {test.__name__}: {type(error).__name__}: {error}")
    print("=" * 60)
    print(f"{len(TESTS) - fallos}/{len(TESTS)} en verde")
    sys.exit(1 if fallos else 0)


if __name__ == "__main__":
    main()
