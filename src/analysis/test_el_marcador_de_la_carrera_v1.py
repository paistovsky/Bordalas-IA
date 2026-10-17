"""
EL MARCADOR DE LA CARRERA (17/10/2026). Guardias de
`scripts/el_marcador_de_la_carrera.py`.

    1. El tablón sin copias: la misma operación dentro de una hora desde
       la PRIMERA copia es una copia; fuera, es otro hecho. La jornada se
       paga una vez y la primera parte de una partida no paga.
    2. El patrimonio cuadra en una liga de juguete: caja y plantilla a
       mano, día a día, y el reparto reconstruido desde la foto.
    3. Contra no hacer nada: quien no se mueve tiene «operar» = 0 exacto;
       vender lo que luego sube y comprar barato salen con su signo.
    4. El once por precio: 1 POR, 3-5 DEF, 2-5 MED, 1-3 DEL, 11, y el
       mismo valor que la fuerza bruta.
    5. Las subastas de la ventana, el día de mercado y las ventanas.
    6. Nunca lanza con basura, y solo escribe con `--escribir`.

Todo con datos sintéticos y pequeños: no se lee `data/` (el tablón real
son 5 MB y cambia cada vuelta), ni la red, ni el reloj.
"""

from __future__ import annotations

import contextlib
import io
import itertools
import json
import sys
import tempfile

from collections import Counter
from datetime import date, datetime, timedelta, timezone
from pathlib import Path


RAIZ = Path(__file__).parents[2]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

import scripts.el_marcador_de_la_carrera as M          # noqa: E402


PEPE, POLLO, LUISMI = M.PEPE, M.POLLO, M.LUISMI
MILLON = 1_000_000
DIAS = [date(2026, 10, 5) + timedelta(days=i) for i in range(4)]    # lunes 05/10 a jueves 08/10
D1, D2, D3, D4 = DIAS


def _ts(dia: str, hora: str) -> int:
    """Epoch de una hora de Madrid de octubre de 2026 antes del 25 (verano, UTC+2)."""
    local = datetime.fromisoformat(f"{dia}T{hora}")
    return int((local - timedelta(hours=2)).replace(tzinfo=timezone.utc).timestamp())


def _u(uid):
    return {"id": uid, "name": str(uid)}


# ============================================================
# LA LIGA DE JUGUETE
# ============================================================
#
#     Tres managers con 15 de reparto cada uno, todo a 1 M salvo:
#
#         1    de Pepe; lo vende el 06/10 a 1,05 M y sube a 1,5 M el 07/10
#         2    de Pepe; 1,0 -> 1,1 -> 1,2 M
#         41   de Luismi; 1,0 -> 0,9 -> 0,8 M (Luismi no se mueve)
#         100  del Computer; Pepe lo gana el 05/10 por 2 M; 2,0 -> 2,1 -> 2,2 M
#         21   de Pollo; se lo vende a Pepe el 06/10 por 0,9 M (vale 1 M)
#         15   de Pepe; lo vende al Computer el 08/10 a las 18:00, a su
#              precio, DESPUES de la foto de las 12:00: la foto no es
#              la plantilla de hoy, y el instante del ancla importa.
#
#     Premios: J2 partida (la 1.ª parte no paga), J3 reemitida (paga una
#     vez) y una racha de Pollo reemitida (cobra una vez).

def _posicion(pid):
    if pid == 100:
        return 4
    i = (pid - 1) % 20
    return 1 if i == 0 else 2 if i <= 5 else 3 if i <= 10 else 4


def _historial():
    precios = {pid: [MILLON] * 4
               for pid in list(range(1, 16)) + list(range(21, 36)) + list(range(41, 56))}
    precios[1] = [MILLON, MILLON, 1_500_000, 1_500_000]
    precios[2] = [MILLON, 1_100_000, 1_200_000, 1_200_000]
    precios[41] = [MILLON, 900_000, 800_000, 800_000]
    precios[100] = [2_000_000, 2_100_000, 2_200_000, 2_200_000]
    return {"players": {str(pid): {"t": [_ts(d.isoformat(), "07:15") for d in DIAS], "p": ps}
                        for pid, ps in precios.items()}}


def _eventos():
    compra = {"player": 100, "to": _u(PEPE), "amount": 2_000_000,
              "bids": [{"user": _u(POLLO), "amount": 1_900_000}]}
    j3 = {"round": {"id": 7003, "name": "Jornada 3"},
          "results": [{"user": _u(PEPE), "points": 20, "bonus": 600_000},
                      {"user": _u(POLLO), "points": 10, "bonus": 300_000},
                      {"user": _u(LUISMI), "points": 5, "bonus": 150_000}]}
    racha = [{"user": _u(POLLO), "amount": 250_000, "reason": "dailyStreak"}]
    return [
        {"event_id": "a", "date": _ts("2026-10-05", "07:03"), "type": "market", "content": [compra]},
        # La reemisión: otro id, cinco minutos más tarde y una puja más a la vista.
        {"event_id": "b", "date": _ts("2026-10-05", "07:08"), "type": "market",
         "content": [{**compra, "bids": compra["bids"] + [{"user": _u(LUISMI), "amount": 1_800_000}]}]},
        {"event_id": "c", "date": _ts("2026-10-05", "20:00"), "type": "roundFinished",
         "content": {"round": {"id": 7000, "name": "Jornada 2"},
                     "results": [{"user": _u(PEPE), "points": 1, "bonus": 999_999}]}},
        {"event_id": "d", "date": _ts("2026-10-06", "10:00"), "type": "transfer",
         "content": [{"player": 1, "from": _u(PEPE), "amount": 1_050_000}]},
        {"event_id": "e", "date": _ts("2026-10-06", "12:00"), "type": "transfer",
         "content": [{"player": 21, "from": _u(POLLO), "to": _u(PEPE), "amount": 900_000}]},
        {"event_id": "f", "date": _ts("2026-10-06", "20:00"), "type": "roundFinished",
         "content": {"round": {"id": 7010, "name": "Jornada 2 (aplazada)", "part": 2},
                     "results": [{"user": _u(PEPE), "bonus": 100_000},
                                 {"user": _u(POLLO), "bonus": 200_000}]}},
        {"event_id": "g", "date": _ts("2026-10-07", "09:00"), "type": "bonus", "content": racha},
        {"event_id": "h", "date": _ts("2026-10-07", "09:30"), "type": "bonus", "content": racha},
        {"event_id": "i", "date": _ts("2026-10-07", "18:00"), "type": "roundFinished", "content": j3},
        {"event_id": "j", "date": _ts("2026-10-07", "18:20"), "type": "roundFinished", "content": j3},
        {"event_id": "k", "date": _ts("2026-10-07", "19:00"), "type": "bettingPool",
         "content": {"pool": {"id": 1}}},
        {"event_id": "l", "date": _ts("2026-10-08", "18:00"), "type": "transfer",
         "content": [{"player": 15, "from": _u(PEPE), "amount": MILLON}]},
    ]


PLANTILLA_DE_PEPE_EN_LA_FOTO = list(range(2, 16)) + [100, 21]
PLANTILLA_DE_PEPE_HOY = [p for p in PLANTILLA_DE_PEPE_EN_LA_FOTO if p != 15]


def _foto():
    reset = _ts("2026-10-09", "07:00")
    t = _ts("2026-10-08", "12:00")

    def j(pid):
        return {"id": pid, "name": f"J{pid}", "position": _posicion(pid)}

    return {"market_clock": {"next_reset_epoch": reset, "seconds_to_reset": reset - t},
            "rival_squads": {"managers": [
                {"user_id": PEPE, "name": "Pepe Bordalás",
                 "players": [j(p) for p in PLANTILLA_DE_PEPE_EN_LA_FOTO]},
                {"user_id": POLLO, "name": "Pollo17", "players": [j(p) for p in range(22, 36)]},
                {"user_id": LUISMI, "name": "Luismi_Haz", "players": [j(p) for p in range(41, 56)]},
            ]}}


def _libro_de_pujas():
    return {"version": "V1.0", "bids": {
        "a": {"player_id": 7, "player_name": "Gana", "amount": 1_000_000, "outcome": "WON",
              "placed_at": "2026-10-05T10:00:00+00:00", "resolved_at": "2026-10-06T05:18:00+00:00",
              "seller_user_id": None},
        # La misma subasta, renovada dos veces en la noche: el libro apunta
        # cada vez que se pone la puja. Sigue siendo UNA subasta.
        "a2": {"player_id": 7, "player_name": "Gana", "amount": 950_000, "outcome": "WON",
               "placed_at": "2026-10-05T11:00:00+00:00", "resolved_at": "2026-10-06T05:18:00+00:00",
               "seller_user_id": None},
        "a3": {"player_id": 7, "player_name": "Gana", "amount": 1_000_000, "outcome": "PENDING",
               "placed_at": "2026-10-05T12:00:00+00:00", "resolved_at": None, "seller_user_id": None},
        # Una perdida que subió la puja: dos filas, una subasta, la puja más alta.
        "b0": {"player_id": 8, "player_name": "Pierde", "amount": 900_000, "outcome": "LOST",
               "winning_amount": 1_100_000, "placed_at": "2026-10-06T08:00:00+00:00",
               "resolved_at": "2026-10-07T05:18:00+00:00", "seller_user_id": None},
        "b": {"player_id": 8, "player_name": "Pierde", "amount": 1_000_000, "outcome": "LOST",
              "winning_amount": 1_100_000, "placed_at": "2026-10-06T10:00:00+00:00",
              "resolved_at": "2026-10-07T05:18:00+00:00", "seller_user_id": None},
        "c": {"player_id": 9, "player_name": "Antes", "amount": 1_000_000, "outcome": "LOST",
              "placed_at": "2026-10-04T10:00:00+00:00", "resolved_at": "2026-10-05T05:18:00+00:00",
              "seller_user_id": None},
        "d": {"player_id": 10, "player_name": "Pendiente", "amount": 1_000_000, "outcome": "PENDING",
              "placed_at": "2026-10-08T08:00:00+00:00", "resolved_at": None, "seller_user_id": None},
        "e": {"player_id": 11, "player_name": "Manager", "amount": 1_000_000, "outcome": "LOST",
              "placed_at": "2026-10-06T10:00:00+00:00", "resolved_at": "2026-10-07T05:18:00+00:00",
              "seller_user_id": 14176382},
        "f": {"player_id": 12, "player_name": "Despues", "amount": 1_000_000, "outcome": "WON",
              "placed_at": "2026-10-08T10:00:00+00:00", "resolved_at": "2026-10-09T05:18:00+00:00",
              "seller_user_id": None},
    }}


BITACORA = {"at": "2026-10-08T10:00:00+00:00", "balance": 22_150_000, "roster_value": 17_400_000}


def _marcador():
    return M.el_marcador(
        eventos=_eventos(), historial=_historial(), libro_de_pujas=_libro_de_pujas(),
        foto=_foto(), bitacora=BITACORA, plantilla_del_marcador=PLANTILLA_DE_PEPE_HOY,
    )


# ============================================================
# 1. EL TABLON SIN COPIAS
# ============================================================


def test_el_tablon_sin_copias():
    t = M.movimientos_del_tablon(_eventos())
    # market + bonus + jornada reemitidos: tres copias fuera.
    assert t["copias"] == 3, t["copias"]
    tipos = Counter(m["tipo"] for m in t["movimientos"])
    assert tipos == Counter({"subasta": 1, "venta": 2, "traspaso": 1, "racha": 1, "premio": 5}), tipos
    # La 1.ª parte de la J2 no paga; la J2 aplazada y la J3, sí, una vez.
    assert t["jornadas_pagadas"] == [7003, 7010], t["jornadas_pagadas"]
    assert not any(m["importe"] == 999_999 for m in t["movimientos"])
    # La jornada lleva la fecha de la primera copia (cuando se cobró).
    j3 = [m for m in t["movimientos"] if m.get("jornada") == 7003]
    assert {m["t"] for m in j3} == {_ts("2026-10-07", "18:00")}, j3

    # LA COPIA SE ANCLA EN LA PRIMERA: a +50 min es copia, a +66 min de la
    # primera es otro hecho aunque esté a 16 min de la copia anterior.
    op = {"player": 5, "to": _u(PEPE), "amount": 500_000}
    t0 = _ts("2026-10-05", "07:05")
    cadena = [{"date": t0 + s, "type": "market", "content": [op]} for s in (0, 3_000, 4_000)]
    r = M.movimientos_del_tablon(cadena)
    assert [m["t"] for m in r["movimientos"]] == [t0, t0 + 4_000] and r["copias"] == 1, r
    # Recomprar por lo mismo dos horas después son dos hechos; la racha de
    # dos días seguidos, dos cobros.
    r = M.movimientos_del_tablon([
        {"date": t0, "type": "market", "content": [op]},
        {"date": t0 + 7_200, "type": "market", "content": [op]},
        {"date": t0, "type": "bonus", "content": [{"user": _u(PEPE), "amount": 250_000, "reason": "dailyStreak"}]},
        {"date": t0 + 86_400, "type": "bonus", "content": [{"user": _u(PEPE), "amount": 250_000, "reason": "dailyStreak"}]},
    ])
    assert len(r["movimientos"]) == 4 and r["copias"] == 0, r
    # El importe distinto no es copia (es otra operación).
    r = M.movimientos_del_tablon([
        {"date": t0, "type": "market", "content": [op]},
        {"date": t0 + 60, "type": "market", "content": [{**op, "amount": 510_000}]},
    ])
    assert len(r["movimientos"]) == 2, r


# ============================================================
# 2. EL PATRIMONIO CUADRA EN LA LIGA DE JUGUETE
# ============================================================


def test_el_patrimonio_cuadra_en_una_liga_de_juguete():
    r = _marcador()
    assert r["available"], r.get("reason")
    assert r["hoy"] == D4 and r["primer_dia"] == D1, (r["hoy"], r["primer_dia"])
    man = r["managers"]

    # El reparto: la plantilla de la foto + vendidos - comprados.
    assert man[PEPE]["inicial"] == {pid: 1 for pid in range(1, 16)}, man[PEPE]["inicial"]
    assert man[POLLO]["inicial"] == {pid: 1 for pid in range(21, 36)}, man[POLLO]["inicial"]
    assert all(m["reparto_cuadra"] for m in man.values())
    # Con la plantilla de HOY como ancla (sin instante) sale el mismo
    # reparto; con la de la foto sin su instante, no (sobraría el 15).
    assert M.plantilla_inicial(PLANTILLA_DE_PEPE_HOY, man[PEPE]["flujos"]) == man[PEPE]["inicial"]
    assert not M.el_reparto_cuadra(M.plantilla_inicial(PLANTILLA_DE_PEPE_EN_LA_FOTO, man[PEPE]["flujos"]))

    # La caja, a mano: 23,3 M; la subasta de 2 M; la venta de 1,05 M y la
    # compra a Pollo de 0,9 M; la J2 aplazada (0,1 / 0,2 M); la racha de
    # Pollo (0,25 M, una vez); la J3 (0,6 / 0,3 / 0,15 M, una vez); la
    # venta del 15 a su precio (1 M), que no mueve el patrimonio.
    cajas = {
        PEPE: [21_300_000, 21_550_000, 22_150_000, 23_150_000],
        POLLO: [23_300_000, 24_400_000, 24_950_000, 24_950_000],
        LUISMI: [23_300_000, 23_300_000, 23_450_000, 23_450_000],
    }
    patrimonios = {
        PEPE: [38_300_000, 38_750_000, 39_550_000, 39_550_000],
        POLLO: [38_300_000, 38_400_000, 38_950_000, 38_950_000],
        LUISMI: [38_300_000, 38_200_000, 38_250_000, 38_250_000],
    }
    precios = M.precios_por_dia(_historial())
    for uid in (PEPE, POLLO, LUISMI):
        for i, d in enumerate(DIAS):
            s = man[uid]["serie"][d]
            assert s["caja"] == cajas[uid][i], (uid, d, s["caja"])
            assert s["patrimonio"] == patrimonios[uid][i], (uid, d, s["patrimonio"])
            # LA IDENTIDAD: patrimonio = caja + plantilla, y la plantilla es
            # la suma, contada aquí aparte, de lo que se tiene a precio del día.
            a_mano = sum(precios[pid][d] * n for pid, n in s["tenencia"].items())
            assert s["plantilla"] == a_mano and s["patrimonio"] == s["caja"] + s["plantilla"], (uid, d)
            assert s["sin_precio"] == 0, (uid, d)
    assert sorted(man[PEPE]["serie"][D4]["tenencia"]) == sorted(PLANTILLA_DE_PEPE_HOY)

    # La liga no crea ni destruye dinero entre managers: lo que se mueve
    # sale del Computer o de los premios.
    cambio_de_caja = sum(man[u]["serie"][D4]["caja"] - M.SALDO_INICIAL for u in man)
    del_computer = 1_050_000 + MILLON - 2_000_000
    premios = 100_000 + 200_000 + 250_000 + 600_000 + 300_000 + 150_000
    assert cambio_de_caja == del_computer + premios, cambio_de_caja

    # El cuadre contra lo medido fuera del tablón.
    c = r["cuadre"]
    assert c["reparto_ok"] == 3 and c["reparto_de"] == 3, c
    assert c["caja"]["cuadra"] and c["caja"]["reconstruida"] == 22_150_000, c
    assert c["caja"]["plantilla_cuadra"] and c["caja"]["plantilla_reconstruida"] == 17_400_000, c
    assert c["plantilla"]["cuadra"], c
    # Y si la bitácora dice otra cosa, no cuadra.
    otra = M.el_cuadre(man, precios, {**BITACORA, "balance": 1}, [1, 2], D4)
    assert not otra["caja"]["cuadra"] and not otra["plantilla"]["cuadra"], otra

    # Un reparto que no son 15 o que sale en negativo no cuadra.
    assert not M.el_reparto_cuadra({1: 1, 2: 1})
    assert not M.el_reparto_cuadra({pid: 1 for pid in range(16)} | {99: -1})


# ============================================================
# 3. CONTRA NO HACER NADA
# ============================================================


def test_contra_no_hacer_nada():
    r = _marcador()
    man = r["managers"]
    precios = M.precios_por_dia(_historial())

    def ventana(uid, desde, hasta):
        return M.contra_no_hacer_nada(man[uid]["serie"], man[uid]["flujos"], precios, desde, hasta)

    # Pepe, del cierre del 05/10 al del 07/10. Quieto: 1 sube 0,5 M, 2 sube
    # 0,2 M y 100 sube 0,2 M -> +0,9 M. Premios 0,7 M. Operar: vendió 1 a
    # 1,05 M y llegó a 1,5 M (-0,45 M) y compró 21 a 0,9 M que vale 1 M
    # (+0,1 M) -> -0,35 M.
    x = ventana(PEPE, D1, D3)
    assert (x["real"], x["nada"], x["premios"], x["operar"]) == (1_250_000, 900_000, 700_000, -350_000), x
    assert x["ventaja"] == x["real"] - x["nada"] and (x["compras"], x["ventas"]) == (1, 1), x
    # Pollo: su plantilla no se mueve de precio; vendió 21 a 0,9 M (-0,1 M).
    x = ventana(POLLO, D1, D3)
    assert (x["real"], x["nada"], x["premios"], x["operar"]) == (650_000, 0, 750_000, -100_000), x
    # Luismi no hace nada: operar = 0 EXACTO, y real = nada + premios.
    x = ventana(LUISMI, D1, D3)
    assert x["operar"] == 0 and x["real"] == x["nada"] + x["premios"], x
    assert (x["nada"], x["premios"]) == (-200_000, 150_000), x
    # Una ventana de un día sin nada: todo a 0.
    x = ventana(PEPE, D3, D4)
    assert (x["real"], x["nada"], x["premios"], x["operar"]) == (0, 0, 0, 0), x
    # Sin uno de los dos cierres no hay comparación.
    assert ventana(PEPE, D1 - timedelta(days=1), D3) is None

    # Las ventanas del marcador: últimos 7 días y la semana en curso son,
    # aquí, del 05/10 al 08/10, con los mismos números.
    claves = [v["clave"] for v in r["ventanas"]]
    assert claves == ["ultimos_7_dias", "semana_en_curso"], claves
    for v in r["ventanas"]:
        assert (v["desde"], v["hasta"]) == (D1, D4), v
        assert v["managers"][PEPE]["operar"] == -350_000, v["managers"][PEPE]
        assert v["managers"][LUISMI]["operar"] == 0, v["managers"][LUISMI]
        # La subasta de 100 se resolvió en el reset del 05/10: fuera.
        assert v["pujas"]["ganadas_en_el_tablon"] == 0, v["pujas"]


# ============================================================
# 4. EL ONCE POR PRECIO
# ============================================================


VALIDAS = {(d, m, f) for d in range(3, 6) for m in range(2, 6) for f in range(1, 4) if d + m + f == 10}


def _bruto(jugadores):
    """El once más caro mirando TODAS las combinaciones de 11."""
    mejor = None
    for combo in itertools.combinations(jugadores, 11):
        n = Counter(j["posicion"] for j in combo)
        if n[1] != 1 or (n[2], n[3], n[4]) not in VALIDAS:
            continue
        valor = sum(j["precio"] for j in combo)
        mejor = valor if mejor is None else max(mejor, valor)
    return mejor


def _cumple(once):
    n = Counter(j["posicion"] for j in once["jugadores"])
    return (len(once["jugadores"]) == 11 and n[1] == 1 and (n[2], n[3], n[4]) in VALIDAS
            and once["formacion"] == f"{n[2]}-{n[3]}-{n[4]}")


def test_el_once_por_precio_respeta_las_formaciones():
    formaciones = {f"{d}-{m}-{f}" for d, m, f in M.FORMACIONES}
    assert formaciones == {"3-4-3", "3-5-2", "4-3-3", "4-4-2", "4-5-1", "5-2-3", "5-3-2", "5-4-1"}, formaciones

    # Siete defensas carísimos, dos porteros, delanteros medios, medios
    # baratos: un solo portero (el caro), cinco defensas como mucho, dos
    # medios como poco, tres delanteros como mucho.
    plantilla = ([{"id": i, "posicion": 2, "precio": 10 * MILLON} for i in range(1, 8)]
                 + [{"id": 10 + i, "posicion": 3, "precio": MILLON} for i in range(5)]
                 + [{"id": 20 + i, "posicion": 4, "precio": 5 * MILLON} for i in range(4)]
                 + [{"id": 30, "posicion": 1, "precio": 3 * MILLON},
                    {"id": 31, "posicion": 1, "precio": 8 * MILLON}])
    o = M.once_por_precio(plantilla)
    assert o["formacion"] == "5-2-3" and o["valor"] == 75 * MILLON and o["completo"], o
    assert _cumple(o) and 31 in [j["id"] for j in o["jugadores"]], o

    # Contra la fuerza bruta, en plantillas de 17 con precios variados.
    for semilla in (1, 2, 3):
        puestos = [1, 1, 2, 2, 2, 2, 2, 2, 3, 3, 3, 3, 3, 4, 4, 4, 4]
        jugadores = [{"id": i, "posicion": p, "precio": ((i * 7919 * semilla) % 97) * 100_000 + 150_000}
                     for i, p in enumerate(puestos, 1)]
        o = M.once_por_precio(jugadores)
        assert _cumple(o) and o["valor"] == _bruto(jugadores), (semilla, o, _bruto(jugadores))

    # Sin portero no hay once completo, y no se inventa.
    sin_portero = [j for j in plantilla if j["posicion"] != 1]
    o = M.once_por_precio(sin_portero)
    assert not o["completo"] and o["huecos"] == 1, o
    assert all(j["posicion"] != 1 for j in o["jugadores"]), o
    # Sin posición o sin precio no entra, y se cuenta.
    o = M.once_por_precio(plantilla + [{"id": 99, "posicion": None, "precio": 50 * MILLON},
                                       {"id": 98, "posicion": 2, "precio": None}])
    assert o["sin_posicion"] == 1 and o["sin_precio"] == 1 and o["valor"] == 75 * MILLON, o

    # En la liga de juguete: los 16 de Pepe, a precio del 08/10.
    o = _marcador()["onces"][PEPE]
    assert o["completo"] and _cumple(o) and o["valor"] == 9 * MILLON + 1_200_000 + 2_200_000, o


# ============================================================
# 5. LAS SUBASTAS, EL DIA DE MERCADO Y LAS VENTANAS
# ============================================================


def test_las_subastas_de_la_ventana():
    p = M.las_pujas(_libro_de_pujas(), D1, D4)
    # a (resuelta el 06/10), b (07/10) y d (pujada el 08/10, pendiente).
    # c se resolvió en el reset del 05/10 y f en el del 09/10: fuera. e era
    # a un manager: aparte.
    assert (p["pujadas"], p["ganadas"], p["perdidas"], p["pendientes"]) == (3, 1, 1, 1), p
    assert p["acierto"] == 0.5 and p["a_managers"] == 1, p
    assert p["perdidas_detalle"] == [{"jugador": 8, "nombre": "Pierde", "reset": D3, "puja": 1_000_000,
                                      "gano_con": 1_100_000, "por_encima": 10.0}], p
    # Siete filas del libro dentro (a, a2, a3, b0, b, d y e) y tres
    # subastas, más una puja a un manager.
    assert p["filas_del_libro"] == 7, p
    # Del 08/10 al 09/10 solo se resuelve f (ganada): 100 %.
    assert M.las_pujas(_libro_de_pujas(), D4, D4 + timedelta(days=1))["acierto"] == 1.0
    # Sin resueltas no hay acierto: es «sin dato», no un 0 %.
    assert M.las_pujas({"bids": {}}, D1, D4)["acierto"] is None


def test_el_dia_de_mercado_y_la_hora_de_madrid():
    assert M.dia_de_mercado(_ts("2026-10-05", "06:59")) == date(2026, 10, 4)
    assert M.dia_de_mercado(_ts("2026-10-05", "07:00")) == date(2026, 10, 5)
    # En invierno el reset de las 07:00 es a las 06:00 UTC.
    enero = datetime(2026, 1, 15, 6, 0, tzinfo=timezone.utc).timestamp()
    assert M.dia_de_mercado(enero) == date(2026, 1, 15)
    assert M.dia_de_mercado(enero - 1) == date(2026, 1, 14)
    # Los cambios de hora de 2026: 29/03 y 25/10 a la 01:00 UTC.
    otono = datetime(2026, 10, 25, 1, 0, tzinfo=timezone.utc).timestamp()
    assert M.hora_de_madrid(otono - 1) == datetime(2026, 10, 25, 2, 59, 59)
    assert M.hora_de_madrid(otono) == datetime(2026, 10, 25, 2, 0)
    primavera = datetime(2026, 3, 29, 1, 0, tzinfo=timezone.utc).timestamp()
    assert M.hora_de_madrid(primavera - 60) == datetime(2026, 3, 29, 1, 59)
    assert M.hora_de_madrid(primavera) == datetime(2026, 3, 29, 3, 0)
    # Texto ISO con zona, y sin zona (UTC).
    assert M.dia_de_mercado("2026-10-17T05:19:41.583039+00:00") == date(2026, 10, 17)
    assert M.dia_de_mercado("2026-10-17T04:59:00") == date(2026, 10, 16)
    # La foto del 18/09 dice 16:16:38 en hora de Madrid.
    assert M._desde_hora_de_madrid("2026-09-18T16:16:38") == datetime(
        2026, 9, 18, 14, 16, 38, tzinfo=timezone.utc).timestamp()

    # El precio del día es la ÚLTIMA muestra del día de mercado; la de las
    # 06:59 es del día anterior; y se arrastra 3 días, no 4.
    h = {"players": {"5": {"t": [_ts("2026-10-06", "20:00"), _ts("2026-10-06", "06:59"),
                                 _ts("2026-10-06", "07:15")],
                           "p": [1_200_000, 900_000, 1_100_000]}}}
    pr = M.precios_por_dia(h)
    assert pr == {5: {date(2026, 10, 5): 900_000, date(2026, 10, 6): 1_200_000}}, pr
    assert M.precio(pr, 5, date(2026, 10, 9)) == 1_200_000
    assert M.precio(pr, 5, date(2026, 10, 10)) is None


def test_las_ventanas():
    v = M.las_ventanas(date(2026, 10, 17), date(2026, 8, 18))           # sábado
    assert [(x["clave"], x["desde"], x["hasta"]) for x in v[:3]] == [
        ("ultimos_7_dias", date(2026, 10, 10), date(2026, 10, 17)),
        ("semana_en_curso", date(2026, 10, 12), date(2026, 10, 17)),
        ("lunes_2026-10-05", date(2026, 10, 5), date(2026, 10, 12)),
    ], v[:3]
    semanas = [x for x in v if x["clave"].startswith("lunes_")]
    # Del 24/08 (primer lunes con precios) al 05/10: siete, todas de lunes a lunes.
    assert len(semanas) == 7 and semanas[-1]["desde"] == date(2026, 8, 24), semanas[-1]
    assert all(x["desde"].weekday() == 0 and (x["hasta"] - x["desde"]).days == 7 for x in semanas)
    # Un lunes no tiene semana en curso.
    assert "semana_en_curso" not in [x["clave"] for x in M.las_ventanas(date(2026, 10, 12), date(2026, 8, 18))]
    assert M.las_ventanas(date(2026, 8, 18), date(2026, 8, 18)) == []


# ============================================================
# 6. NUNCA LANZA, Y SOLO ESCRIBE CON --escribir
# ============================================================


BASURA = [
    None, "x", 42, 3.5, True, [], {}, [None, "y", 7], {"players": "x"},
    {"players": {"1": {"t": "x", "p": [1]}}}, {"bids": [1, "a", {"outcome": 3}]},
    {"type": "market", "content": "x"},
    [{"type": "market", "date": "nope", "content": [{"player": "x"}]}],
    [{"type": "roundFinished", "date": 1, "content": {"round": "x"}}],
    [{"type": "transfer", "date": 10**12, "content": [{"player": 1, "from": "x", "amount": []}]}],
    {"rival_squads": {"managers": "x"}}, {"rival_squads": {"managers": [{"user_id": 1, "players": "x"}]}},
    {"market_clock": {"next_reset_epoch": "x"}, "rival_squads": {"managers": [{"user_id": 1, "players": [{"id": 1}]}]}},
]


def test_nunca_lanza_con_basura():
    for b in BASURA:
        assert isinstance(M.movimientos_del_tablon(b), dict)
        assert isinstance(M.flujos_de(b, PEPE), list)
        assert isinstance(M.precios_por_dia(b), dict)
        assert M.precio(b, 1, D1) is None or isinstance(M.precio(b, 1, D1), int)
        assert isinstance(M.valorar(b, b, b), tuple)
        assert isinstance(M.plantilla_inicial(b, b, b), dict)
        assert M.el_reparto_cuadra(b) is False
        assert isinstance(M.serie_de_patrimonio(b, b, b, b), dict)
        M.caja_en(b, b)
        assert M.contra_no_hacer_nada(b, b, b, b, b) is None
        assert M.las_ventanas(b, b) == []
        assert isinstance(M.las_pujas(b, b, b), dict)
        assert isinstance(M.once_por_precio(b), dict)
        assert isinstance(M.las_fichas(b), tuple)
        M.el_ancla(b)
        assert isinstance(M.el_cuadre(b, b, b, b, b), dict)
        r = M.el_marcador(b, b, b, b, b, b, b, b)
        assert r["available"] is False and r["reason"], r
        assert isinstance(M.informe(b), str) and isinstance(M.informe(r), str)
        json.dumps(M.para_json(b))
        M.dia_de_mercado(b)
        M.hora_de_madrid(b)
        M.nuestra_plantilla_del_marcador(b)
    # Basura mezclada con lo bueno: lo bueno sigue contando.
    mezcla = _eventos() + BASURA
    assert M.movimientos_del_tablon(mezcla)["copias"] == 3
    # Con el tablón bueno y los precios rotos, dice por qué.
    r = M.el_marcador(_eventos(), {"players": "x"}, foto=_foto())
    assert r["available"] is False and "precios" in r["reason"], r
    # El resultado bueno se pinta y se pasa a JSON.
    r = _marcador()
    texto = M.informe(r)
    assert "EL MARCADOR DE LA CARRERA" in texto and "CUADRA" in texto and "NO CUADRA" not in texto, texto
    j = json.loads(json.dumps(M.para_json(r)))
    assert j["available"] and j["managers"][str(PEPE)]["serie"][-1]["patrimonio"] == 39_550_000, j


def test_solo_escribe_con_escribir():
    # El único sitio donde escribe, y en ningún sitio sale a la red.
    assert M.SALIDA == M.RAIZ / "data" / "trading" / "el_marcador_de_la_carrera.json", M.SALIDA
    fuente = Path(M.__file__).read_text(encoding="utf-8")
    assert fuente.count(".write_text(") == 1, "más de una escritura en el script"
    for red in ("import urllib", "import requests", "import socket", "http.client", "from urllib"):
        assert red not in fuente, red

    nombres = ("TABLON", "PRECIOS", "LIBRO_DE_PUJAS", "ESCAPARATE", "MARCADOR", "BITACORA", "FOTOS", "SALIDA")
    viejos = {n: getattr(M, n) for n in nombres}
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        try:
            (tmp / "fotos").mkdir()
            (tmp / "fotos" / "2026-10-08.json").write_text(json.dumps(_foto()), encoding="utf-8")
            (tmp / "tablon.json").write_text(json.dumps(_eventos()), encoding="utf-8")
            (tmp / "precios.json").write_text(json.dumps(_historial()), encoding="utf-8")
            (tmp / "pujas.json").write_text(json.dumps(_libro_de_pujas()), encoding="utf-8")
            (tmp / "bitacora.jsonl").write_text("roto\n" + json.dumps(BITACORA) + "\n", encoding="utf-8")
            M.TABLON, M.PRECIOS, M.LIBRO_DE_PUJAS = tmp / "tablon.json", tmp / "precios.json", tmp / "pujas.json"
            M.ESCAPARATE, M.MARCADOR, M.BITACORA = tmp / "no.jsonl", tmp / "no.json", tmp / "bitacora.jsonl"
            M.FOTOS, M.SALIDA = tmp / "fotos", tmp / "salida" / "marcador.json"

            consola = io.StringIO()
            with contextlib.redirect_stdout(consola):
                assert M.main([]) == 0
            assert not M.SALIDA.exists(), "escribió sin --escribir"
            assert "CUADRA" in consola.getvalue(), consola.getvalue()

            with contextlib.redirect_stdout(io.StringIO()):
                assert M.main(["--escribir"]) == 0
                assert M.main(["--hoy", "no-es-fecha"]) == 2
            escrito = json.loads(M.SALIDA.read_text(encoding="utf-8"))
            assert escrito["available"] and escrito["hoy"] == "2026-10-08", escrito.get("hoy")
            assert sorted(p.name for p in tmp.iterdir()) == [
                "bitacora.jsonl", "fotos", "precios.json", "pujas.json", "salida", "tablon.json"]
        finally:
            for n, v in viejos.items():
                setattr(M, n, v)


TESTS = [
    test_el_tablon_sin_copias,
    test_el_patrimonio_cuadra_en_una_liga_de_juguete,
    test_contra_no_hacer_nada,
    test_el_once_por_precio_respeta_las_formaciones,
    test_las_subastas_de_la_ventana,
    test_el_dia_de_mercado_y_la_hora_de_madrid,
    test_las_ventanas,
    test_nunca_lanza_con_basura,
    test_solo_escribe_con_escribir,
]


def main() -> None:
    fallos = 0
    for test in TESTS:
        try:
            test()
            print(f"OK   {test.__name__}")
        except AssertionError as error:
            fallos += 1
            print(f"FALLA {test.__name__}: {error}")
    print("=" * 60)
    print(f"{len(TESTS) - fallos}/{len(TESTS)} en verde")
    sys.exit(1 if fallos else 0)


if __name__ == "__main__":
    main()
