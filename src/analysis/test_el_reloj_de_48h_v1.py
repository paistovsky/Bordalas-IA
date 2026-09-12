"""
"0,0 h" no era un contador roto: era un clamp tapando un menos.

SINTOMA (12/09/2026, foto de las 14:22)

    Ocho listados con `hours_to_expiry: 0.0` clavado. Y en el
    mismo bloque, la renovacion decia de cada uno:

        "El listado caduca en 0.0 h y la ventana no llega hasta
         dentro de 16.6 h: no se puede salvar renovando en la
         ventana."

    mientras encolaba siete de esos ocho para renovar. La misma
    foto decia "no se pueden salvar" y "los estoy salvando".

LO QUE SE MIDIO, Y GANA A LAS DOS HIPOTESIS

    Se sospechaba de dos cosas: (a) que renovar no reiniciara el
    reloj de 48 h, o (b) que el contador estuviera roto. No era
    ninguna de las dos.

    1. EL RELOJ DE 48 H ES EXACTO. Sobre los 13 listados de ese
       dia, `until - date` da 48,00 h en los trece, al segundo.

    2. RENOVAR SI LO REINICIA. El libro de renovaciones del
       10/09 —10:25:48 y 10:35:31— casa AL MINUTO con la fecha
       de listado de esos seis jugadores.

    3. LOS OCHO ESTABAN CADUCADOS DE VERDAD. Listados el 10/09 a
       las 10:25 y 10:35, caducaron a esas mismas horas del 12.
       La foto es de las 14:22: llevaban 2,28 y 2,11 horas
       muertos.

    Lo que fallaba era un `max(hours_to_expiry, 0.0)`, que
    convertia "llego tarde" en "justo a tiempo". Dos cosas
    distintas con el mismo numero, y la segunda no alarma a
    nadie.

    Y la contradiccion de la foto se explica sola: los dos textos
    eran correctos. No se pueden salvar renovando en la ventana
    —porque ya estan muertos— y aun asi hay que reencolarlos,
    porque un listado caducado se vuelve a publicar.

LO QUE NO SE ARREGLA AQUI, Y HAY QUE DECIRLO

    La ultima renovacion fue el 10/09. Que un listado caduque
    significa que nadie lo renovo en 48 horas, y ESO no lo
    arregla quitar un clamp. Queda medido y dicho en el informe.

REGLA 23

    No lee estado externo: los numeros de la medicion van escritos
    aqui como constantes.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from pathlib import Path


RAIZ = Path(__file__).parents[2]

# MEDIDO EL 12/09/2026 sobre los 13 listados propios.
VIDA_DE_UN_LISTADO_HORAS = 48.0

LISTADOS_MEDIDOS = 13

# LOS DOS GRUPOS QUE CADUCARON, con su hora de listado real.
#
#     Las horas son UTC, que es como las da Biwenger en `date` y
#     `until`. En Madrid son dos mas (verano). Escribirlo importa:
#     la primera version de esta guardia tomo "10:25" por hora de
#     Madrid y le salio un desfase de 1,67 h — doctrina 35, una
#     hora sin zona es un dato con dos nombres.
LISTADO_A_UTC = datetime(
    2026, 9, 10, 10, 25, 48, tzinfo=timezone.utc
)

LISTADO_B_UTC = datetime(
    2026, 9, 10, 10, 35, 31, tzinfo=timezone.utc
)

# La foto con la que se midio.
MEDIDO_UTC = datetime(
    2026, 9, 12, 12, 42, 18, tzinfo=timezone.utc
)

CADUCADOS = {
    "A": 2.28,
    "B": 2.11,
}


def _listado(listado_utc: datetime) -> dict:
    """
    Un listado ya parseado, como lo deja `get_current_listings`.

    Biwenger lo da en epochs (`date` y `until`) y de ahi salieron
    las 48,00 h medidas; aqui se guardan los dos, el crudo para
    poder comprobar la vida y el parseado para el analisis.
    """

    caduca = listado_utc + timedelta(
        hours=VIDA_DE_UN_LISTADO_HORAS
    )

    return {
        "listed_price": 1_800_000,
        "date": int(listado_utc.timestamp()),
        "until": int(caduca.timestamp()),
        "listed_at": listado_utc,
        "expires_at": caduca,
    }


# ============================================================
# 1. EL SIGNO NO SE TIRA
# ============================================================


def test_un_listado_caducado_no_dice_cero() -> None:
    """
    EL CASO DE LA FOTO.

    Listado el 10/09 a las 10:25 UTC, mirado el 12/09 a las
    12:42 UTC: caducado hace 2,28 h. No "0,0".
    """

    from src.analysis.market_listing_lifecycle_engine import (
        analyze_listing_lifecycle,
    )

    visto = analyze_listing_lifecycle(
        listing=_listado(LISTADO_A_UTC),
        cycle_state={},
        now=MEDIDO_UTC,
    )

    horas = visto["hours_to_expiry"]

    assert horas is not None, visto

    assert horas < 0, (
        f"`hours_to_expiry` sale {horas}: el clamp sigue "
        f"convirtiendo «llego tarde» en «justo a tiempo»"
    )

    assert abs(horas + CADUCADOS["A"]) < 0.05, horas

    # DOS CASOS, DOS NOMBRES (regla 33).
    assert visto["expired"] is True, visto

    assert abs(
        visto["expired_for_hours"] - CADUCADOS["A"]
    ) < 0.05, visto

    # Y el segundo grupo, diez minutos mas tarde.
    segundo = analyze_listing_lifecycle(
        listing=_listado(LISTADO_B_UTC),
        cycle_state={},
        now=MEDIDO_UTC,
    )

    assert abs(
        segundo["expired_for_hours"] - CADUCADOS["B"]
    ) < 0.05, segundo


def test_un_listado_vivo_cuenta_hacia_delante() -> None:
    """
    La otra mitad: los que no han caducado siguen contando en
    positivo y NO se marcan como caducados.
    """

    from src.analysis.market_listing_lifecycle_engine import (
        analyze_listing_lifecycle,
    )

    # Uno de los cinco frescos: listado el 12/09 a las 05:18 UTC.
    visto = analyze_listing_lifecycle(
        listing=_listado(
            datetime(2026, 9, 12, 5, 18, tzinfo=timezone.utc)
        ),
        cycle_state={},
        now=MEDIDO_UTC,
    )

    assert visto["hours_to_expiry"] > 0, visto

    assert visto["expired"] is False, visto

    assert visto["expired_for_hours"] is None, visto


def test_sin_fecha_de_caducidad_se_dice_sin_medir() -> None:
    """
    Regla 24 y doctrina 36: "no se sabe" no puede salir como un
    numero. Un listado sin `until` no caduca en cero horas: no se
    sabe cuando caduca.
    """

    from src.analysis.market_listing_lifecycle_engine import (
        analyze_listing_lifecycle,
    )

    visto = analyze_listing_lifecycle(
        listing={
            "listed_price": 100,
            "listed_at": None,
            "expires_at": None,
        },
        cycle_state={},
        now=MEDIDO_UTC,
    )

    assert visto["hours_to_expiry"] is None, visto

    assert visto["expired"] is False, visto

    assert visto["action"] == "LISTING_EXPIRY_UNKNOWN", visto


def test_la_vida_de_un_listado_son_48_horas() -> None:
    """
    LO MEDIDO, ESCRITO.

    `until - date` = 48,00 h en los trece listados del 12/09, al
    segundo. Si Biwenger cambiara la vida de un listado, esta
    guardia no se entera —no lee el mundo— pero deja el numero
    con su fecha para que se pueda volver a medir.
    """

    assert VIDA_DE_UN_LISTADO_HORAS == 48.0

    assert LISTADOS_MEDIDOS == 13

    crudo = _listado(LISTADO_A_UTC)

    assert (crudo["until"] - crudo["date"]) == 48 * 3600


def test_la_pantalla_no_pinta_un_cero_que_no_es() -> None:
    """
    Y que la pantalla lo diga. Un "0,0 h" en una tabla se lee
    como "va justo", no como "llega tarde".
    """

    panel = (
        RAIZ / "dashboard-v8" / "src" / "pages"
        / "MarketPage.jsx"
    ).read_text(encoding="utf-8")

    for dato in ("player.expired", "expired_for_hours"):
        assert dato in panel, (
            f"la pantalla no lee `{dato}`: seguiria pintando un "
            f"cero que no es un cero"
        )

    assert "sin medir" in panel, (
        "la pantalla no distingue «no se sabe» de un numero"
    )


TESTS = [
    test_un_listado_caducado_no_dice_cero,
    test_un_listado_vivo_cuenta_hacia_delante,
    test_sin_fecha_de_caducidad_se_dice_sin_medir,
    test_la_vida_de_un_listado_son_48_horas,
    test_la_pantalla_no_pinta_un_cero_que_no_es,
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
    print(
        f"EL RELOJ DE 48H V1: "
        f"{len(TESTS) - fallos}/{len(TESTS)} OK"
    )
    print("=" * 60)

    if fallos:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
