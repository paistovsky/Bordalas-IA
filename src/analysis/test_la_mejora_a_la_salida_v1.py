"""
LA MEJORA A LA SALIDA (28/10/2026). Guardias de
`BORDALAS_LA_MEJORA_A_LA_SALIDA` en `src/actions/la_mejora_del_once.py`.

    1. Con el interruptor y LA PUJA EN 9.900 puesta (como en produccion),
       la puja por el del Computer que NO sube en el reset de hoy
       (`priceIncrement` sabido y <= 0) es lo que pide redondeado al
       primer ...9.900 (`en_9900(precio)`), no `en_9900(precio + 1 %)`.
       Nunca por debajo de lo que pide.
    2. El que sube, el que no se sabe si sube (sin dato o con basura),
       con LA PUJA FUERTE o sin LA PUJA EN 9.900: lo de siempre. Con
       basura, nunca lanza.
    3. La caja del cambio, la caja de despues, la puja que se manda y lo
       que decide si el cambio cabe salen del MISMO importe.
    4. Apagado, `decidir` es byte a byte el de main: una huella sobre una
       bateria de precios (300.000 a 9 M) y subidas (-100.000 a +200.000,
       sin dato y con basura), congelada con el codigo de main ANTES del
       cambio.
    5. Nace apagado; `correr` lo lee del entorno.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile

from pathlib import Path


RAIZ = Path(__file__).parents[2]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

import src.actions.la_mejora_del_once as mejora                     # noqa: E402
import src.analysis.test_la_mejora_del_once_v1 as base              # noqa: E402

from src.actions.la_ronda_de_la_manana import en_9900                # noqa: E402


ENV_A_LA_SALIDA = "BORDALAS_LA_MEJORA_A_LA_SALIDA"


# ------------------------------------------------------------
# EL MUNDO: uno nuestro (10) que puede salir y uno del Computer (20)
# que pide `precio`, los dos delanteros
# ------------------------------------------------------------
#
#     lejos   el 20 suma +3,0 por jornada (4,2 contra 1,2), caja de sobra
#     cerca   +0,78 (4,2 contra 3,42): con LA PUJA FUERTE, prima pequeña
#     hueco   el 10 lesionado: con SOLO SI SUBE, entra aunque no suba
#     justa   caja 0 a 100 h (minimo -1 M) y el 10 da 1,9 M: el cambio
#             cabe solo si la puja es de 2,9 M o menos
#     rojo    en rojo a 80 h: el 10 vale 12 M y el 20 suma +0,3 (caro
#             por barato)

SALIDAS = {
    "lejos": dict(tasa=2.0, valor=2_000_000, caja=50_000_000, horas=100, estados=None),
    "cerca": dict(tasa=5.7, valor=2_000_000, caja=50_000_000, horas=100, estados=None),
    "hueco": dict(tasa=2.0, valor=2_000_000, caja=50_000_000, horas=100,
                  estados={10: "injured"}),
    "justa": dict(tasa=2.0, valor=2_000_000, caja=0, horas=100, estados=None),
    "rojo": dict(tasa=6.5, valor=12_000_000, caja=-3_000_000, horas=80, estados=None),
}


def _escenario(precio, subida=None, clave="price_increment", sale="lejos"):
    """Los argumentos de `decidir`. `clave` None: la ficha del 20 sin la
    subida (no se sabe si sube)."""
    s = SALIDAS[sale]
    entra = {"tasa": 6.0, "status": "ok", "price": precio, "de_quien": "computer",
             "position": 4, "played": 6}
    if clave is not None:
        entra[clave] = subida
    return dict(
        once=[{"id": 10, "name": "Sale", "position": 4, "starter_probability": 60,
               "price": s["valor"]}],
        liga={10: {"tasa": s["tasa"], "price": s["valor"], "de_quien": "nuestro",
                   "position": 4, "played": 6},
              20: entra},
        escaparate=[{"id": 20, "name": "Entra", "position": 4, "price": precio,
                     "points": 36, "played": 6, "starter_probability": 70}],
        foto={"plantilla": {10}, "nuestras_pujas": {}, "ofertas_del_computer": {},
              "en_venta": set(), "saldo": 500_000, "maximo_de_puja": 100_000_000,
              "mercado": {20: precio}},
        libro={}, caja=s["caja"], horas_jornada=s["horas"], estados=s["estados"],
    )


# Produccion (28/10): LA PUJA EN 9.900 y SOLO SI SUBE puestas, LA PUJA
# FUERTE no. SOLO SI SUBE se apaga aqui donde hace falta que el que no
# sube entre sin ser un hueco (las dos dan lo mismo en un hueco).
PRODUCCION = dict(en_9900=True, solo_si_sube=True, puja_fuerte=None)


def _d(precio, subida=None, *, clave="price_increment", sale="lejos", a_la_salida=True,
       **banderas):
    k = {**PRODUCCION, "solo_si_sube": False, **banderas}
    return mejora.decidir(**_escenario(precio, subida, clave, sale), a_la_salida=a_la_salida,
                          **k)


def _la_puja(d):
    pujas = [a for a in d["acciones"] if a["accion"] == "PUJAR"]
    assert len(pujas) <= 1, pujas
    return pujas[0]["importe"] if pujas else None


# ------------------------------------------------------------
# 1. EL QUE NO SUBE, A LO QUE PIDE EN 9.900
# ------------------------------------------------------------

def test_el_que_no_sube_puja_lo_que_pide_en_9900():
    # 2 M sin subir: 2.009.900 (apagado, 2.029.900: el +1 % en 9.900).
    assert _la_puja(_d(2_000_000, -10_000)) == 2_009_900
    assert _la_puja(_d(2_000_000, 0)) == 2_009_900
    assert _la_puja(_d(2_000_000, -10_000, a_la_salida=False)) == 2_029_900
    # 5 M: 5.009.900 (apagado, 5.059.900).
    assert _la_puja(_d(5_000_000, -50_000)) == 5_009_900
    assert _la_puja(_d(5_000_000, -50_000, a_la_salida=False)) == 5_059_900
    # 830.000: 839.900 con y sin el interruptor (el +1 % cae en el mismo
    # ...9.900: por debajo de 1 M no se ahorra nada).
    assert _la_puja(_d(830_000, 0)) == 839_900
    assert _la_puja(_d(830_000, 0, a_la_salida=False)) == 839_900
    # El catalogo lo llama `priceIncrement`.
    assert _la_puja(_d(2_000_000, -10_000, clave="priceIncrement")) == 2_009_900


def test_el_que_sube_lo_de_siempre():
    # 2 M subiendo 30.000 (la minima de su tramo es 20.000): 2.029.900.
    assert _la_puja(_d(2_000_000, 30_000)) == 2_029_900
    assert _la_puja(_d(2_000_000, 30_000, a_la_salida=False)) == 2_029_900
    # Sube poco (1 EUR, por debajo de su minima) sigue siendo subir.
    assert _la_puja(_d(2_000_000, 1)) == 2_029_900
    # Y con produccion entera (SOLO SI SUBE puesto): el que sube, igual.
    assert _la_puja(_d(2_000_000, 30_000, solo_si_sube=True)) == 2_029_900


def test_nunca_por_debajo_de_lo_que_pide():
    # Pide algo que ya acaba en 9.900: puja eso mismo, ni un euro menos
    # (apagado, 3.299.900).
    assert _la_puja(_d(3_259_900, 0)) == 3_259_900
    assert _la_puja(_d(3_259_900, 0, a_la_salida=False)) == 3_299_900
    # Pide 9.950 de mas: al siguiente ...9.900, nunca al de abajo.
    assert _la_puja(_d(1_009_950, -1)) == 1_019_900
    # En toda la bateria: encendido, nunca por debajo de lo que pide ni
    # por encima de lo de siempre.
    for precio in PRECIOS:
        for subida in (-100_000, -1, 0):
            puja = _la_puja(_d(precio, subida))
            antes = _la_puja(_d(precio, subida, a_la_salida=False))
            assert puja == en_9900(precio) and precio <= puja <= antes, (precio, subida, puja)


def test_sin_dato_o_con_basura_lo_de_siempre_y_nunca_lanza():
    # Sin la subida (no se sabe si sube): el +1 % de siempre.
    assert _la_puja(_d(2_000_000, clave=None)) == 2_029_900
    for basura in (None, "x", "", [], {}, True, False, float("nan"), float("inf"), object()):
        assert _la_puja(_d(2_000_000, basura)) == 2_029_900, basura
        assert mejora.la_subida_de_hoy({"price_increment": basura}) is None, basura
    # La ficha misma, basura: nunca lanza.
    for ficha in (None, "x", 7, [], {"price_increment": "x", "priceIncrement": "y"}):
        assert mejora.la_subida_de_hoy(ficha) is None, ficha
        assert mejora.la_puja_a_la_salida(2_000_000, ficha, 2_029_900) == 2_029_900
    # Precio basura: lo de siempre, sin lanzar.
    for precio in (None, "x", 0, -5, [], float("nan")):
        assert mejora.la_puja_a_la_salida(precio, {"price_increment": 0}, 123) == 123, precio
    # La que sube no es basura: `price_increment` manda; si es basura,
    # vale el `priceIncrement` (como en `sube_de_verdad`).
    assert mejora.la_subida_de_hoy({"price_increment": "x", "priceIncrement": -5}) == -5
    assert mejora.la_subida_de_hoy({"price_increment": 0, "priceIncrement": 9}) == 0


def test_la_caja_cuenta_la_misma_puja():
    # Lo que se manda, lo que cuesta el cambio y la caja de despues: el
    # mismo importe.
    d = _d(2_000_000, -10_000)
    cambio, = d["plan"]["cambios"]
    assert cambio["puja"] == _la_puja(d) == 2_009_900, cambio
    assert cambio["caja"] == int(2_000_000 * mejora.VENTA) - 2_009_900, cambio
    assert d["plan"]["caja_despues"] == 50_000_000 + int(2_000_000 * 0.95) - 2_009_900
    # Y decide si cabe con ese importe: 2.880.000 sin subir, caja 0 y el
    # que sale da 1,9 M; el minimo es -1 M, asi que cabe hasta 2,9 M.
    # Apagado, 2.909.900: no cabe. Encendido, 2.889.900: cabe.
    assert _la_puja(_d(2_880_000, 0, sale="justa", a_la_salida=False)) is None
    d = _d(2_880_000, 0, sale="justa")
    assert _la_puja(d) == 2_889_900, d["plan"]
    assert d["plan"]["caja_despues"] == 0 + int(2_000_000 * 0.95) - 2_889_900 >= -1_000_000
    # Subiendo, ni encendido cabe (la puja es la de siempre).
    assert _la_puja(_d(2_880_000, 30_000, sale="justa")) is None
    # El plan dice a quienes de los elegidos se puja a lo que piden.
    assert d["plan"]["a_la_salida"] == [20], d["plan"]
    assert _d(2_000_000, 30_000)["plan"]["a_la_salida"] == []
    # El que no cabe ni a lo que pide (2.909.900) no se puja ni sale ahi.
    d = _d(2_900_000, 0, sale="justa")
    assert _la_puja(d) is None and d["plan"]["a_la_salida"] == [], d["plan"]


def test_tapar_un_hueco_en_produccion():
    # Con SOLO SI SUBE (produccion), el que no sube solo entra para tapar
    # un hueco; y ahi, a lo que pide en 9.900.
    assert _la_puja(_d(2_000_000, -10_000, solo_si_sube=True)) is None
    d = _d(2_000_000, -10_000, solo_si_sube=True, sale="hueco")
    assert _la_puja(d) == 2_009_900, d["plan"]


# ------------------------------------------------------------
# 2. LO QUE NO TOCA
# ------------------------------------------------------------

def test_sin_la_puja_en_9900_lo_de_siempre():
    # LA PUJA EN 9.900 apagada: el +1 % a miles de siempre.
    assert _la_puja(_d(2_000_000, -10_000, en_9900=False)) == mejora.la_puja(2_000_000) \
        == 2_020_000
    assert _la_puja(_d(5_000_000, 0, en_9900=False)) == 5_050_000
    assert "a_la_salida" not in _d(2_000_000, -10_000, en_9900=False)["plan"]


def test_con_la_puja_fuerte_lo_de_siempre():
    for precio, subida, sale in ((2_000_000, -10_000, "lejos"), (400_000, 0, "cerca"),
                                 (5_000_000, 0, "rojo")):
        con = _d(precio, subida, sale=sale, puja_fuerte=True)
        sin = _d(precio, subida, sale=sale, puja_fuerte=True, a_la_salida=False)
        assert json.dumps(con, sort_keys=True, default=base._canon) == \
            json.dumps(sin, sort_keys=True, default=base._canon), (precio, sale)


def test_lo_que_ya_es_nuestro_no_se_mira():
    # Adoptar no puja: el del inventario sigue con puja 0 y su coste de
    # siempre aunque no suba.
    k = _escenario(2_000_000, -10_000)
    k.update(escaparate=[], inventario={20}, foto={**k["foto"], "plantilla": {10, 20}},
             probabilidades={20: 70})
    con = mejora.decidir(**k, en_9900=True, a_la_salida=True)
    sin = mejora.decidir(**k, en_9900=True)
    assert [c["entra"] for c in con["adoptar"]] == [20], con
    assert con["adoptar"] == sin["adoptar"] and con["acciones"] == sin["acciones"]


# ------------------------------------------------------------
# 3. APAGADO: BYTE A BYTE EL DE MAIN
# ------------------------------------------------------------
#
#     La salida entera de `decidir` sobre la bateria de abajo (95
#     precios x 21 fichas x 5 mundos x 8 combinaciones de LA PUJA EN
#     9.900, SOLO SI SUBE y LA PUJA FUERTE = 79.800 llamadas), capturada
#     con el codigo de main ANTES de este cambio (6358dabe): su sha256
#     sobre el JSON canonico de cada salida, una por linea.

PRECIOS = sorted(set(range(300_000, 9_000_001, 100_000)) | {
    309_900, 830_000, 999_999, 1_009_950, 2_880_000, 3_259_900, 8_999_999})
SUBIDAS = [-100_000, -50_000, -20_000, -1, 0, 1, 10_000, 20_000, 30_000, 60_000,
           100_000, 200_000, None, "x", "", [], True]
FICHAS = ([("price_increment", s) for s in SUBIDAS]
          + [("priceIncrement", s) for s in (-50_000, 0, 30_000)]
          + [(None, None)])
BANDERAS = [dict(en_9900=a, solo_si_sube=b, puja_fuerte=c)
            for a in (False, True) for b in (False, True) for c in (None, True)]


def _bateria():
    for precio in PRECIOS:
        for clave, subida in FICHAS:
            for sale in SALIDAS:
                for banderas in BANDERAS:
                    yield {**_escenario(precio, subida, clave, sale), **banderas}


def _huella(**extra):
    h = hashlib.sha256()
    for k in _bateria():
        h.update(json.dumps(mejora.decidir(**k, **extra), sort_keys=True,
                            default=base._canon).encode())
        h.update(b"\n")
    return h.hexdigest()


HUELLA_DE_MAIN = "6d1b0430336bc4031c6b29a1b78b446d4b6abde1ac6a579629136d9b43430067"


def test_apagado_es_byte_a_byte_el_de_main():
    assert len(PRECIOS) * len(FICHAS) * len(SALIDAS) * len(BANDERAS) == 79_800
    # Sin pasarlo (lo de siempre) y pasandolo apagado.
    assert _huella() == HUELLA_DE_MAIN, _huella()
    assert _huella(a_la_salida=False) == HUELLA_DE_MAIN


# ------------------------------------------------------------
# 4. EL INTERRUPTOR
# ------------------------------------------------------------

def test_nace_apagado():
    assert mejora.ENV_A_LA_SALIDA == ENV_A_LA_SALIDA
    with base._interruptores({ENV_A_LA_SALIDA: None}):
        assert mejora.la_mejora_a_la_salida_activa() is False
    for valor in ("1", "true", "si", "yes", " SI "):
        with base._interruptores({ENV_A_LA_SALIDA: valor}):
            assert mejora.la_mejora_a_la_salida_activa() is True, valor
    for valor in ("0", "", "no", "false"):
        with base._interruptores({ENV_A_LA_SALIDA: valor}):
            assert mejora.la_mejora_a_la_salida_activa() is False, valor


def _correr(subida):
    """`correr` con todo dado (los libros, en un temporal): uno nuestro
    (10, delantero de 2 M) y uno del Computer (20) que pide 2 M."""
    k = _escenario(2_000_000, subida)
    liga = [{"id": pid, "name": f"j{pid}", **f} for pid, f in k["liga"].items()]
    status = {
        "todaLaLiga": {"players": liga},
        "lineup": {"players": k["once"]},
        "roster": {"players": k["once"]},
        "libro_del_escaparate": {"players": k["escaparate"]},
    }
    snapshot = {
        "league": {"user": {"id": 7}},
        "market": {"sales": [{"player": {"id": 20}, "user": None, "price": 2_000_000}],
                   "offers": [],
                   "status": {"maximumBid": 14_000_000, "balance": 3_000_000}},
        "my_team": [{"id": 10, "price": 2_000_000}],
        "catalog": {"data": {"players": {"10": {"status": "ok"}, "20": {"status": "ok"}}}},
    }
    escritor = base._Escritor()
    with tempfile.TemporaryDirectory() as tmp:
        rutas = {n: os.path.join(tmp, f"{n}.json") for n in ("mejora", "ronda", "chollos")}
        for ruta in rutas.values():
            Path(ruta).write_text("{}")
        s = mejora.correr(
            status=status, snapshot=snapshot, v10={}, escritor_factory=lambda: escritor,
            ahora=base.AHORA, libro_ruta=rutas["mejora"], calendario={},
            de_fuera={"orden": {}, "vetados": set(), "protegidos": set(), "rotando": set(),
                      "libro_ronda": rutas["ronda"], "libro_chollos": rutas["chollos"],
                      "horas_jornada": 100.0, "puede_escribir": True, "en_curso": False},
        )
        libro = json.loads(Path(rutas["mejora"]).read_text())
    return s, escritor, libro


def test_correr_lo_lee_del_entorno():
    comunes = {mejora.ENV: "1", mejora.ENV_CALENDARIO: None, mejora.ENV_PUJA_FUERTE: None,
               "BORDALAS_LA_CARTERA": None, mejora.ENV_SOLO_SI_SUBE: None,
               mejora.ENV_LA_JORNADA_DE_CADA_PAGINA: None, "GITHUB_RUN_ID": None}
    casos = (
        ({ENV_A_LA_SALIDA: None, mejora.ENV_PUJA_EN_9900: "1"}, -10_000, 2_029_900),
        ({ENV_A_LA_SALIDA: "1", mejora.ENV_PUJA_EN_9900: "1"}, -10_000, 2_009_900),
        ({ENV_A_LA_SALIDA: "1", mejora.ENV_PUJA_EN_9900: "1"}, 30_000, 2_029_900),
        ({ENV_A_LA_SALIDA: "1", mejora.ENV_PUJA_EN_9900: None}, -10_000, 2_020_000),
    )
    for interruptores, subida, importe in casos:
        with base._interruptores({**comunes, **interruptores}):
            s, escritor, libro = _correr(subida)
        assert escritor.llamadas == [("PUJAR", 20, importe)], (interruptores, s)
        # Lo que se apunta en el libro (y luego cuenta en la caja de la
        # jornada) es lo que se pujo.
        assert libro["20"]["puja"] == importe, libro
        cambio, = s["plan"]["cambios"]
        assert cambio["puja"] == importe and \
            cambio["caja"] == int(2_000_000 * mejora.VENTA) - importe, cambio


def test_el_tablon_lo_dice():
    from src.telemetry.el_tablon import QUE_HACE
    frase = QUE_HACE[ENV_A_LA_SALIDA]
    assert "9.900" in frase and "no sube" in frase, frase


TESTS = [
    test_el_que_no_sube_puja_lo_que_pide_en_9900,
    test_el_que_sube_lo_de_siempre,
    test_nunca_por_debajo_de_lo_que_pide,
    test_sin_dato_o_con_basura_lo_de_siempre_y_nunca_lanza,
    test_la_caja_cuenta_la_misma_puja,
    test_tapar_un_hueco_en_produccion,
    test_sin_la_puja_en_9900_lo_de_siempre,
    test_con_la_puja_fuerte_lo_de_siempre,
    test_lo_que_ya_es_nuestro_no_se_mira,
    test_apagado_es_byte_a_byte_el_de_main,
    test_nace_apagado,
    test_correr_lo_lee_del_entorno,
    test_el_tablon_lo_dice,
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
