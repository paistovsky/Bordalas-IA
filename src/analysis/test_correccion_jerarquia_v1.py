"""
Corregir a FutbolFantasy a mano, sin poder mentir en silencio.

EL CASO (22/08/2026)

    "El caso es que Mangala este año es clave en el Getafe, viene
     mal en FF."

    FF lo tenia como ROTACION. Con esa etiqueta:

      - su valor semanal salia 0,52 en vez de 0,70;
      - el plan de deuda lo eligio para venderlo por 3,07 M
        diciendo "coste deportivo: ninguno";
      - y era el jugador que MAS puntos llevaba del once (5).

    Lo paro el dueño a mano. Pidio poder corregir el escalon, y
    pidio explicitamente IMPORTANTE y no Clave.

POR QUE ESTO ES PELIGROSO Y HAY QUE ATARLO

    Un sitio donde el dueño escribe jerarquias es un sitio donde
    el bot deja de mirar la realidad y mira una opinion. Las tres
    ataduras:

      1. Solo el ESCALON. El porcentaje de titularidad de la
         semana no se toca nunca: eso es pronostico fresco.
      2. CADUCA. Una correccion sin fecha de muerte es una
         opinion fosil.
      3. SE VE. Marcada como MANUAL, con motivo y con fecha. Si
         se pinta igual que un dato de FF, es una mentira.

LO QUE SE PROTEGE AQUI

    Las tres de arriba, mas: que se aplique en UN solo sitio -el
    once, el mercado, la venta y la pantalla tienen que ver lo
    mismo-, que un fichero roto no tumbe el ciclo, y que editarlo
    tenga efecto sin esperar a que FF reescriba su tablero.
"""

from __future__ import annotations

import ast
import json
import tempfile

from datetime import date, timedelta
from pathlib import Path

from src.intelligence.correcciones_jerarquia import (
    ESCALONES,
    apply_corrections,
    describe,
    load_corrections,
)


MANGALA = 41606

HOY = date(2026, 8, 22)


# El temporal del sistema, no `/tmp` a pelo: en Windows no existe
# y el candado reventaba en la maquina del dueño mientras pasaba
# en el runner de Ubuntu. Un test que solo corre en un sitio no es
# un candado.
TMP = Path(tempfile.gettempdir())


def escribir(tmp: Path | None = None, correcciones=None) -> Path:
    tmp = Path(tmp or TMP)
    ruta = tmp / "bordalas_correcciones_test.json"
    ruta.write_text(
        json.dumps({"correcciones": correcciones}, ensure_ascii=False),
        encoding="utf-8",
    )
    return ruta


def una(**cambios):
    base = {
        "player_id": MANGALA,
        "jugador": "Mangala",
        "jerarquia": "IMPORTANTE",
        "motivo": "Titular fijo en el Getafe; FF va con retraso.",
        "desde": "2026-08-22",
        "caduca": "2026-09-21",
    }
    base.update(cambios)
    return base


def lookup_ff():
    """Como lo deja FutbolFantasy: Mangala en Rotacion."""

    return {
        MANGALA: {
            "probability": 80.0,
            "hierarchy": {
                "value": 30,
                "label": "Rotación",
                "franchise": False,
            },
            "hierarchy_value": 30,
            "hierarchy_label": "Rotación",
        },
        999: {
            "probability": 90.0,
            "hierarchy": {"value": 50, "label": "Clave"},
            "hierarchy_value": 50,
            "hierarchy_label": "Clave",
        },
    }


# ============================================================
# PRUEBAS
# ============================================================


def test_el_caso_mangala(tmp=None):
    """
    El caso entero: de Rotacion a Importante, y marcado.
    """

    ruta = escribir(tmp, [una()])

    correcciones = load_corrections(ruta, hoy=HOY)
    datos = apply_corrections(lookup_ff(), correcciones)

    ficha = datos[MANGALA]

    assert ficha["hierarchy_label"] == "Importante"
    assert ficha["hierarchy_value"] == 40
    assert ficha["hierarchy"]["value"] == 40

    assert ficha["hierarchy_source"] == "MANUAL", (
        "la correccion no se distingue de un dato de FF"
    )

    override = ficha["hierarchy_override"]

    assert override["hierarchy_before"] == "Rotación", (
        "no se guarda lo que decia FF: sin eso no se puede "
        "revisar si la correccion sigue teniendo sentido"
    )
    assert override["motivo"]
    assert override["caduca"] == "2026-09-21"


def test_a_quien_no_se_corrige_no_se_le_toca():

    ruta = escribir(TMP, [una()])

    datos = apply_corrections(
        lookup_ff(), load_corrections(ruta, hoy=HOY)
    )

    otro = datos[999]

    assert otro["hierarchy_label"] == "Clave"
    assert otro.get("hierarchy_source") is None


def test_el_porcentaje_de_titularidad_no_se_toca_nunca():
    """
    LA ATADURA QUE MAS IMPORTA.

    El escalon es estructural y FF tarda semanas en actualizarlo:
    ahi una correccion tiene sentido. El porcentaje es el
    pronostico de ESTA jornada, sale fresco cada dia, y tocarlo
    seria decidir con un dato inventado.
    """

    ruta = escribir(
        TMP,
        [una(probability=99, starter_probability=99)],
    )

    datos = apply_corrections(
        lookup_ff(), load_corrections(ruta, hoy=HOY)
    )

    assert datos[MANGALA]["probability"] == 80.0, (
        "se ha colado una correccion del pronostico semanal"
    )

    fuente = (
        Path(__file__).parents[1]
        / "intelligence"
        / "correcciones_jerarquia.py"
    ).read_text(encoding="utf-8")

    arbol = ast.parse(fuente)

    for nodo in ast.walk(arbol):

        if not isinstance(nodo, ast.FunctionDef):
            continue

        if nodo.name != "apply_corrections":
            continue

        cuerpo = " ".join(
            ast.dump(n) for n in nodo.body
            if not (
                isinstance(n, ast.Expr)
                and isinstance(n.value, ast.Constant)
            )
        )

        assert "probability" not in cuerpo, (
            "apply_corrections ha empezado a tocar el pronostico "
            "de titularidad"
        )
        return

    raise AssertionError("no se encuentra apply_corrections")


def test_una_correccion_caducada_no_se_aplica():
    """
    Dentro de un mes puede que FF tenga razon y tu no, y nadie se
    va a acordar de revisarlo.
    """

    ruta = escribir(
        TMP, [una(caduca="2026-08-21")]
    )

    correcciones = load_corrections(ruta, hoy=HOY)

    assert not correcciones["aplicadas"]
    assert len(correcciones["caducadas"]) == 1

    datos = apply_corrections(lookup_ff(), correcciones)

    assert datos[MANGALA]["hierarchy_label"] == "Rotación"


def test_sin_fecha_caduca_sola():
    """
    Que se pueda escribir rapido no puede significar que viva para
    siempre.
    """

    ruta = escribir(
        TMP,
        [{
            "player_id": MANGALA,
            "jerarquia": "IMPORTANTE",
            "motivo": "prueba",
            "desde": "2026-08-22",
        }],
    )

    correccion = load_corrections(ruta, hoy=HOY)["aplicadas"][MANGALA]

    caduca = date.fromisoformat(correccion["caduca"])

    assert caduca > HOY
    assert caduca <= HOY + timedelta(days=45), (
        "una correccion sin fecha esta viviendo demasiado"
    )


def test_sin_motivo_no_se_aplica():
    """
    Dentro de tres semanas, "Mangala = Importante" sin explicacion
    no se puede ni revisar ni defender.
    """

    ruta = escribir(TMP, [una(motivo="")])

    correcciones = load_corrections(ruta, hoy=HOY)

    assert not correcciones["aplicadas"]
    assert correcciones["invalidas"]


def test_un_escalon_inventado_no_se_aplica():

    ruta = escribir(TMP, [una(jerarquia="SUPERCRACK")])

    correcciones = load_corrections(ruta, hoy=HOY)

    assert not correcciones["aplicadas"]
    assert "escalon desconocido" in (
        correcciones["invalidas"][0]["problema"]
    )


def test_se_escriben_con_palabras_y_con_tildes():
    """
    Quien escribe esto piensa en palabras, no en numeros. Y
    'Rotación' con tilde tiene que valer igual que 'ROTACION'.
    """

    for texto, esperado in (
        ("Importante", 40),
        ("IMPORTANTE", 40),
        ("rotación", 30),
        ("Clave", 50),
    ):
        ruta = escribir(TMP, [una(jerarquia=texto)])
        correcciones = load_corrections(ruta, hoy=HOY)

        assert correcciones["aplicadas"][MANGALA][
            "hierarchy_value"
        ] == esperado, texto

    assert set(ESCALONES) == {
        "DIOS", "CLAVE", "IMPORTANTE", "ROTACION",
        "REVULSIVO", "RESERVA", "DESCARTE",
    }


def test_un_fichero_roto_no_tumba_el_ciclo():

    ruta = TMP / "bordalas_correcciones_roto.json"
    ruta.write_text("{esto no es json", encoding="utf-8")

    correcciones = load_corrections(ruta, hoy=HOY)

    assert correcciones["available"] is False
    assert not correcciones["aplicadas"]

    # Y aplicar eso deja el lookup exactamente como estaba.
    datos = apply_corrections(lookup_ff(), correcciones)
    assert datos[MANGALA]["hierarchy_label"] == "Rotación"


def test_a_quien_no_esta_en_ff_no_se_le_inventa_ficha():
    """
    Sin pronostico de titularidad no hay jerarquia que corregir, y
    meter media ficha seria peor que no meter ninguna.
    """

    ruta = escribir(
        TMP, [una(player_id=123456, jugador="Fantasma")]
    )

    correcciones = load_corrections(ruta, hoy=HOY)
    datos = apply_corrections(lookup_ff(), correcciones)

    assert 123456 not in datos

    ficha = correcciones["aplicadas"][123456]
    assert ficha["aplicada"] is False
    assert ficha["problema"]


def test_se_aplica_en_un_solo_sitio():
    """
    El once, el tablero de fichajes, el plan de deuda y la
    pantalla leen todos de `build_starter_lookup`. Corregir en
    varios sitios seria garantizar que un dia dos de ellos digan
    cosas distintas del mismo jugador.
    """

    fuente = (
        Path(__file__).parent / "candidate_starter_lookup.py"
    ).read_text(encoding="utf-8")

    assert "apply_corrections" in fuente, (
        "las correcciones ya no se aplican en el punto unico"
    )

    # Y editando el fichero tiene que notarse sin esperar a que FF
    # reescriba su tablero.
    assert "CORRECCIONES_FILE" in fuente, (
        "la cache no mira el fichero de correcciones: editarlo no "
        "tendria efecto hasta el proximo scrapeo"
    )


def test_la_pantalla_lo_marca():
    """
    Una jerarquia tocada a mano que se pinte igual que una de FF
    es exactamente la mentira silenciosa que esto viene a evitar.
    """

    estado = (
        Path(__file__).parents[1]
        / "telemetry"
        / "dashboard_state.py"
    ).read_text(encoding="utf-8")

    assert '"hierarchy_source"' in estado, (
        "el dashboard no recibe de donde sale la jerarquia"
    )

    pitch = (
        Path(__file__).parents[2]
        / "dashboard-v8" / "src" / "components" / "PitchXI.jsx"
    ).read_text(encoding="utf-8")

    assert "hierarchy_source" in pitch, (
        "el campo se pinta igual venga de FF o de una correccion"
    )


def test_se_puede_contar_lo_que_hay():

    ruta = escribir(
        TMP,
        [una(), una(player_id=2, caduca="2026-01-01"),
         una(player_id=3, motivo="")],
    )

    resumen = describe(load_corrections(ruta, hoy=HOY))

    assert resumen["activas"] == 1
    assert resumen["caducadas"] == 1
    assert resumen["invalidas"] == 1


def main():

    pruebas = [
        test_el_caso_mangala,
        test_a_quien_no_se_corrige_no_se_le_toca,
        test_el_porcentaje_de_titularidad_no_se_toca_nunca,
        test_una_correccion_caducada_no_se_aplica,
        test_sin_fecha_caduca_sola,
        test_sin_motivo_no_se_aplica,
        test_un_escalon_inventado_no_se_aplica,
        test_se_escriben_con_palabras_y_con_tildes,
        test_un_fichero_roto_no_tumba_el_ciclo,
        test_a_quien_no_esta_en_ff_no_se_le_inventa_ficha,
        test_se_aplica_en_un_solo_sitio,
        test_la_pantalla_lo_marca,
        test_se_puede_contar_lo_que_hay,
    ]

    for prueba in pruebas:
        prueba()
        print(f"  OK  {prueba.__name__}")

    print()
    print("Correccion de jerarquia: todo en verde.")


if __name__ == "__main__":
    main()
