"""
Los cuatro ojeadores: misma forma, y ninguno miente sobre lo que
trae.

SINTOMA QUE PREVIENE

    El encargo pedia "prediccion de cambio de valor por jugador,
    con un % de confianza". Al abrir las cuatro webs el 05/09/2026
    resulto que NINGUNA publica eso:

      FutbolFantasy   su leyenda dice "Dif: Diferencia de valor
                      respecto al mercado del dia anterior" y
                      "Tend: dias consecutivos que ha estado
                      aumentando o bajando".
      Analitica       `subida` y `frenada`: el cambio del ultimo
                      mercado y cuanto se ha frenado.
      Comuniate       el cambio de precio, mas el pulso de
                      demanda.
      JornadaPerfecta ni una tabla. Es un blog de noticias.

    Las cuatro paginas se titulan "subidas y bajadas". Publican lo
    que YA paso.

CONSECUENCIA

    Un dato observado etiquetado como pronostico se convierte, a
    los dos meses, en "el sistema predijo que subiria". Esta
    guardia impide que eso pase por descuido:

      - toda señal viaja con `observed`;
      - la confianza NUNCA se inventa: o la publica la fuente, o
        va None, o dice con esas letras que la derivamos nosotros;
      - el pulso de Comuniate, que es lo unico que mira hacia
        delante, va marcado como no observado y con fuente propia.

    Y protege el contrato: los cuatro modulos contestan igual,
    para que añadir prensa o X mañana no toque nada mas.
"""

from __future__ import annotations

from src.intelligence.scout import (
    analitica_market,
    comuniate_market,
    futbolfantasy_market,
    jornada_perfecta_market,
)
from src.intelligence.scout.common import (
    DO_NOT_RETRY,
    direction,
    fetch,
    signal,
    source_result,
)


MODULOS = (
    futbolfantasy_market,
    analitica_market,
    comuniate_market,
    jornada_perfecta_market,
)


# ============================================================
# TROZOS REALES, RECORTADOS
# ============================================================
#
#     Recortados de las paginas de verdad del 05/09/2026. No se
#     guardan enteras -son 3,2 MB solo FutbolFantasy- pero la
#     forma es la misma, que es lo que prueba el parser.

FF_HTML = """
<table><tbody>
<tr class="elemento_jugador" data-id="2751" data-nombre="kike garcia"
    data-posicion="Delantero" data-equipo="7" data-valor="580000"
    data-valor1="590000" data-valor3="610000" data-valor7="650000"
    data-tendencia="-3" data-aceleracion="0"
    data-diferencia1="-10000" data-diferencia3="-30000"
    data-diferencia7="-70000"
    data-diferencia-pct1="-1.6949152542373"
    data-diferencia-pct3="-4.9180327868852"
    data-diferencia-pct7="-10.769230769231"></tr>
<tr class="elemento_jugador" data-id="99" data-nombre="lamine yamal"
    data-valor="21170000" data-tendencia="5" data-aceleracion="1"
    data-diferencia1="50000" data-diferencia-pct1="0.23"></tr>
</tbody></table>
"""

ANALITICA_HTML = (
    '<script>self.__next_f.push([1,"'
    '{\\"nickname\\":\\"Yamal\\",\\"slug\\":\\"lamine-yamal\\",'
    '\\"masterPlayerId\\":386828,\\"positionId\\":4,'
    '\\"marketValue\\":21170000,\\"subida\\":50000,'
    '\\"frenada\\":10000,\\"playerStatus\\":\\"ok\\",'
    '\\"teamName\\":\\"Barcelona\\",\\"titularityPercent\\":80,'
    '\\"currentSeason\\":{\\"points\\":10,\\"average\\":3.33}}'
    '"])</script>'
)

COMUNIATE_HTML = """
<a class="ficha-player biwenger-ficha" data-id="1">
 <div class="player-row">
  <span class="player-pos pos-md">MD</span>
  <span class="player-photo">
   <img class="player-team" alt="Betis" src="/escudos/4.png"/>
  </span>
  <div class="player-main">
   <div class="player-name-line"><span class="player-name">Ceballos</span></div>
   <div class="player-price-line"><span class="player-price">1.120.000&euro;</span></div>
  </div>
  <div class="player-value up">+250.000&euro;</div>
  <div class="biwenger-pulso-mini">
   <span class="pulso-compras"><span class="pulso-etiqueta">Compras</span><strong>90%</strong></span>
   <span class="pulso-ventas"><span class="pulso-etiqueta">Ventas</span><strong>0%</strong></span>
   <span class="pulso-uso"><span class="pulso-etiqueta">Uso</span><strong>5%</strong></span>
  </div>
 </div>
</a>
<a class="ficha-player biwenger-ficha" data-id="2">
 <div class="player-row">
  <span class="player-photo"><img class="player-team" alt="Atlético"/></span>
  <div class="player-main">
   <div class="player-name-line"><span class="player-name">Jonathan David</span></div>
   <div class="player-price-line"><span class="player-price">8.000.000&euro;</span></div>
  </div>
  <div class="player-value down">-290.000&euro;</div>
 </div>
</a>
"""


# ============================================================
# 1. LOS TRES QUE RASPAN, RASPAN
# ============================================================


def test_futbolfantasy_lee_la_fila() -> None:
    r = futbolfantasy_market.scout(html=FF_HTML)

    assert r["ok"] is True
    assert len(r["records"]) == 2

    kike = r["records"][0]

    assert kike["market_value"] == 580_000, (
        "sin el valor no hay llave del euro y el emparejamiento "
        "se queda solo con el nombre"
    )
    assert kike["trend_days"] == -3

    horizontes = {s["horizon_days"] for s in kike["signals"]}
    assert horizontes == {1, 3, 7}

    uno = next(s for s in kike["signals"] if s["horizon_days"] == 1)
    assert uno["direction"] == "DOWN"
    assert uno["magnitude_eur"] == -10_000


def test_analitica_lee_el_json_escondido() -> None:
    """
    La tabla no esta en el HTML: viene dentro de los trozos de
    React como cadena escapada.
    """

    r = analitica_market.scout(html=ANALITICA_HTML)

    assert r["ok"] is True, r["error"]
    assert len(r["records"]) == 1

    yamal = r["records"][0]

    assert yamal["ff_name"] == "Yamal"
    assert yamal["market_value"] == 21_170_000
    assert yamal["deceleration"] == 10_000, (
        "la frenada es la segunda derivada, y no la da nadie mas"
    )
    assert yamal["signals"][0]["direction"] == "UP"


def test_analitica_no_estropea_los_acentos() -> None:
    """
    Desescapar con `unicode_escape` convertia "Pablo Garcia" en
    "Pablo GarcÃ­a", y despues el emparejamiento fallaba por un
    motivo que no tenia nada que ver con el emparejamiento.
    """

    html = ANALITICA_HTML.replace("Yamal", "Pablo Garc\\u00eda")

    r = analitica_market.scout(html=html)

    assert r["records"][0]["ff_name"] == "Pablo García"


def test_comuniate_lee_precio_cambio_y_pulso() -> None:
    r = comuniate_market.scout(html=COMUNIATE_HTML)

    assert r["ok"] is True
    assert len(r["records"]) == 2

    ceballos = r["records"][0]

    assert ceballos["market_value"] == 1_120_000
    assert ceballos["demand_percent"] == 90.0
    assert ceballos["supply_percent"] == 0.0

    fuentes = {s["source"] for s in ceballos["signals"]}
    assert "COMUNIATE" in fuentes
    assert "COMUNIATE_PULSO" in fuentes, (
        "el pulso es la unica señal del ojeador que mira hacia "
        "delante: no puede perderse"
    )


def test_comuniate_entiende_una_bajada() -> None:
    """El signo va en la clase CSS, no siempre en el texto."""

    r = comuniate_market.scout(html=COMUNIATE_HTML)

    david = r["records"][1]

    assert david["signals"][0]["direction"] == "DOWN"
    assert david["signals"][0]["magnitude_eur"] == -290_000


def test_sin_pulso_claro_no_se_inventa_una_señal() -> None:
    """
    Jonathan David no trae pulso. No se rellena con ceros: se
    queda con una señal, la del precio.
    """

    r = comuniate_market.scout(html=COMUNIATE_HTML)

    assert len(r["records"][1]["signals"]) == 1


# ============================================================
# 2. NADIE MIENTE SOBRE LO QUE TRAE
# ============================================================


def test_todas_las_señales_dicen_si_son_observadas() -> None:
    for modulo, html in (
        (futbolfantasy_market, FF_HTML),
        (analitica_market, ANALITICA_HTML),
        (comuniate_market, COMUNIATE_HTML),
    ):
        for registro in modulo.scout(html=html)["records"]:
            for señal in registro["signals"]:
                assert "observed" in señal, (
                    f"{modulo.SOURCE} manda una señal sin decir si "
                    f"es un hecho o un pronostico"
                )


def test_el_movimiento_de_precio_va_marcado_como_observado() -> None:
    for modulo, html in (
        (futbolfantasy_market, FF_HTML),
        (analitica_market, ANALITICA_HTML),
        (comuniate_market, COMUNIATE_HTML),
    ):
        for registro in modulo.scout(html=html)["records"]:
            for señal in registro["signals"]:

                if señal["source"].endswith("_PULSO"):
                    continue

                assert señal["observed"] is True, (
                    "ninguna de las tres webs publica un pronostico: "
                    "marcarlo como tal seria inventarlo"
                )


def test_el_pulso_es_lo_unico_que_mira_hacia_delante() -> None:
    r = comuniate_market.scout(html=COMUNIATE_HTML)

    pulso = next(
        s
        for s in r["records"][0]["signals"]
        if s["source"].endswith("_PULSO")
    )

    assert pulso["observed"] is False
    assert pulso["source"] != "COMUNIATE", (
        "tiene fuente propia para que no vote dos veces en el "
        "consenso"
    )


def test_la_confianza_no_se_inventa_nunca() -> None:
    for modulo, html in (
        (futbolfantasy_market, FF_HTML),
        (analitica_market, ANALITICA_HTML),
        (comuniate_market, COMUNIATE_HTML),
    ):
        for registro in modulo.scout(html=html)["records"]:
            for señal in registro["signals"]:

                if señal["confidence"] is None:
                    assert señal["confidence_basis"], (
                        "sin confianza hay que decir por que no la hay"
                    )
                    continue

                base = str(señal["confidence_basis"] or "")

                assert base.startswith("DERIVADA"), (
                    f"{modulo.SOURCE} publica una confianza de "
                    f"{señal['confidence']} sin decir de donde sale. "
                    f"Ninguna de las webs publica confianza."
                )


def test_toda_señal_lleva_su_cita() -> None:
    """Sin la cita original no se puede discutir un fallo."""

    for modulo, html in (
        (futbolfantasy_market, FF_HTML),
        (analitica_market, ANALITICA_HTML),
        (comuniate_market, COMUNIATE_HTML),
    ):
        for registro in modulo.scout(html=html)["records"]:
            for señal in registro["signals"]:
                assert señal["quote"], (
                    f"{modulo.SOURCE} manda una señal sin decir en "
                    f"que se basa"
                )
                assert señal["seen_at"], "ni cuando se vio"


# ============================================================
# 3. EL CONTRATO, PARA PODER AÑADIR FUENTES MAÑANA
# ============================================================


def test_los_cuatro_contestan_igual() -> None:
    for modulo in MODULOS:

        assert hasattr(modulo, "SOURCE"), f"{modulo} sin SOURCE"
        assert hasattr(modulo, "scout"), f"{modulo} sin scout()"

        respuesta = modulo.scout(html="")

        for clave in ("source", "ok", "records", "error", "fetched_at"):
            assert clave in respuesta, (
                f"{modulo.SOURCE} no devuelve `{clave}`"
            )


def test_una_pagina_rota_no_lanza_y_lo_dice() -> None:
    for modulo, _ in (
        (futbolfantasy_market, None),
        (analitica_market, None),
        (comuniate_market, None),
    ):
        r = modulo.scout(html="<html>nada de esto sirve</html>")

        assert r["ok"] is False
        assert r["error"], "una fuente caida tiene que decir por que"
        assert r["records"] == []


def test_jornada_perfecta_esta_descartada_y_escrito() -> None:
    """
    No publica precios. Se devuelve `ok=False` con motivo para
    que aparezca en el informe: una fuente que desaparece se lee
    como una que nadie penso.
    """

    r = jornada_perfecta_market.scout()

    assert r["ok"] is False
    assert "no publica" in r["error"].lower()
    assert r["note"], "y se dice que es a proposito, no un fallo"


# ============================================================
# 4. EDUCACION AL RASPAR
# ============================================================


def test_un_403_no_se_reintenta() -> None:
    """
    Un 403 o un 429 son la web diciendo "para". Insistir es la
    forma mas rapida de que nos bloqueen para siempre.
    """

    assert 403 in DO_NOT_RETRY
    assert 429 in DO_NOT_RETRY

    class SesionQueRechaza:
        def __init__(self):
            self.llamadas = 0

        def get(self, *args, **kwargs):
            self.llamadas += 1

            class Respuesta:
                status_code = 429
                text = ""

            return Respuesta()

    sesion = SesionQueRechaza()

    texto, error = fetch(sesion, "https://ejemplo")

    assert texto is None
    assert "429" in error
    assert sesion.llamadas == 1, "se pidio mas de una vez"


def test_una_caida_de_red_se_anota_y_no_lanza() -> None:
    class SesionCaida:
        def get(self, *args, **kwargs):
            raise OSError("sin red")

    texto, error = fetch(SesionCaida(), "https://ejemplo")

    assert texto is None
    assert "OSError" in error


def test_un_cero_es_flat_y_no_una_subida() -> None:
    assert direction(0) == "FLAT"
    assert direction(None) == "FLAT"
    assert direction(10) == "UP"
    assert direction(-10) == "DOWN"


def test_la_forma_de_la_señal_no_cambia_a_capricho() -> None:
    s = signal("X", direction_="UP", quote="algo")

    for clave in (
        "source", "direction", "magnitude_percent", "magnitude_eur",
        "horizon_days", "confidence", "confidence_basis", "quote",
        "observed", "seen_at",
    ):
        assert clave in s, f"la señal ha perdido `{clave}`"

    r = source_result("X", ok=True, records=[])

    for clave in ("source", "ok", "records", "error", "note", "fetched_at"):
        assert clave in r


TESTS = [
    test_futbolfantasy_lee_la_fila,
    test_analitica_lee_el_json_escondido,
    test_analitica_no_estropea_los_acentos,
    test_comuniate_lee_precio_cambio_y_pulso,
    test_comuniate_entiende_una_bajada,
    test_sin_pulso_claro_no_se_inventa_una_señal,
    test_todas_las_señales_dicen_si_son_observadas,
    test_el_movimiento_de_precio_va_marcado_como_observado,
    test_el_pulso_es_lo_unico_que_mira_hacia_delante,
    test_la_confianza_no_se_inventa_nunca,
    test_toda_señal_lleva_su_cita,
    test_los_cuatro_contestan_igual,
    test_una_pagina_rota_no_lanza_y_lo_dice,
    test_jornada_perfecta_esta_descartada_y_escrito,
    test_un_403_no_se_reintenta,
    test_una_caida_de_red_se_anota_y_no_lanza,
    test_un_cero_es_flat_y_no_una_subida,
    test_la_forma_de_la_señal_no_cambia_a_capricho,
]


def main() -> None:
    fallos = 0
    for test in TESTS:
        try:
            test()
            print(f"OK   {test.__name__}")
        except AssertionError as exc:
            fallos += 1
            print(f"FALLA {test.__name__}: {exc}")

    print("=" * 60)
    print(f"OJEADOR FUENTES V1: {len(TESTS) - fallos}/{len(TESTS)} OK")
    print("=" * 60)

    if fallos:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
