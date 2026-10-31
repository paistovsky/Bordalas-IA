"""
EL ONCE QUE SE PUEDE ESCRIBIR (31/10/2026)

LO QUE PASA (bitacora del 27/10 21:00; analisis del 29/10 y del 31/10)

    "Un dibujo de emergencia con un jugador en duda (10 alineables)
    puede ganar a uno completo de 11 sanos, y el ejecutor bloquea el
    SAVE_LINEUP."

    El motor y el ejecutor no cuentan igual un once completo:

        - el MOTOR (`lineup_engine._todas_las_formaciones`) ordena los
          siete dibujos por (huecos llenos, score). Si la busqueda
          normal -solo los alineables sin aviso (`automatic_lineup`)-
          no llena un dibujo, ese dibujo se busca en emergencia, con
          los dudosos dentro, y cuenta como lleno (11). Una duda de
          Biwenger cuesta 530 puntos de score; la vara de FF, que no la
          mira, vale 1.000.000 por unidad. Boyé en duda (~1,0 M) gana a
          Ramón Enríquez (0,40 M) o a un quinto defensa (0,09-0,43 M):
          el 3-4-3 de emergencia con Boyé gana al 3-5-2 sano;
        - el EJECUTOR (`autopilot_executor`, SAVE_LINEUP) solo escribe
          un once con 11 alineables sin aviso (`playable_count`). Con un
          dudoso dentro: BLOCKED_INVALID_LINEUP.

    Asi que el once que Pepe elige con un dudoso dentro no se puede
    escribir NUNCA, y en Biwenger se queda el ultimo once escrito. Con
    el lesionado dentro, si lo hay: Boyé en duda y Kike Salas lesionado
    (los dos juegan el Sevilla-Alavés del viernes 06/11, la J12) dejan a
    Kike en el once. Y el SAVE_LINEUP bloqueado no apunta fallo
    (`write_performed` False: sin `action_failure_backoff`), asi que se
    queda primero en la cola y se come la unica escritura de la vuelta
    (renovar 690, ofertas 650, especular 400), vuelta tras vuelta.

    Medido el 31/10 sobre la plantilla del artefacto (14 y 15
    jugadores, cada pareja de estados): 120 bloqueos evitables con 14
    (116 con 15), y en 116 de esos 120 se queda en Biwenger un titular
    lesionado o sancionado.

    Y preferir al sano es lo que dicen los numeros de la casa: de los
    `doubt` jugaron 4 de 17 (24 %), contra el 69 % de los `ok`
    (`el_once_objetivo.JUEGA_SI_DUDA`). El motor del once no lo usaba.

QUE HACE (con `BORDALAS_EL_ONCE_QUE_SE_PUEDE_ESCRIBIR`)

    El once que se escribe es siempre uno que el ejecutor acepta:

    1. SI NADIE ESTA EN DUDA (todo alineable va sin aviso), nada cambia:
       la busqueda de siempre ya solo mira a los sanos.

    2. SI HAY ALGUIEN EN DUDA, el mejor once COMPLETO de los siete
       dibujos con solo los que se pueden escribir sin mas: los
       alineables sin aviso y el Dios en duda. Un 3-5-2 de once sanos
       gana a cualquier 3-4-3 con un dudoso. EL DIOS EN DUDA JUEGA: la
       regla del dueño (18/08) es que un Dios juega siempre salvo 0 %
       asegurado -lesion, sancion u otro motivo-, y una duda no lo es;
       con su bono, el mejor once lo lleva. El ejecutor lo deja pasar
       porque va autorizado (punto 4).

    3. SI NINGUN DIBUJO SE LLENA ASI (el unico portero en duda; los
       tres delanteros en duda; con once justos, cualquiera en duda),
       el que lleva MENOS dudosos y, entre esos, el de mas score: a cada
       uno que no se puede escribir se le resta `DUDA` en la busqueda,
       asi que solo entra a llenar un hueco que nadie mas llena. Es el
       mejor once posible: un lesionado nunca juega y el dudoso, a
       veces. Con Gulácsi en duda y Kike lesionado, se escribe el once
       con Gulácsi y sin Kike, en vez de dejar a Kike en Biwenger.

    4. LA MARCA. El once sale con `el_once_que_se_puede_escribir`:
       `{se_puede_escribir, motivo, autorizados, dudosos, texto}`.
       `autorizados` son los ids de los dudosos que el punto 2 o el 3
       metieron a proposito. El ejecutor deja pasar un once con
       `playable_count` < 11 SOLO si trae la marca y cada uno de los
       que no son alineables sin aviso es alineable y esta autorizado
       (`admite`). Sin la marca -con el interruptor apagado no la hay-
       el ejecutor de siempre. `playable_count` sigue contando lo de
       siempre: el XI incompleto (COMPLETE_LINEUP, la urgencia de
       fichar un portero) se sigue viendo.

    5. Y SI NO SE PUDIERA (no deberia pasar: la marca diria
       NO_SE_PUEDE_ESCRIBIR), el monitor no pide el SAVE_LINEUP: un
       guardado bloqueado no se come la escritura de la vuelta.

    Sin once de 11 -el unico portero lesionado-, nada: no hay once
    que escribir, el monitor dice BLOCKED_INCOMPLETE_LINEUP como hoy.
    Eso solo lo arregla un segundo portero.

DONDE MANDA, Y DONDE NO

    Solo en el once QUE SE ESCRIBE: `lineup_monitor` lo pide
    (`que_se_puede_escribir`), y de ahi beben SAVE_LINEUP,
    `live_lineup`, el panel, el `once_escrito` del cierre y el `once`
    de la mejora. Los que VALORAN (venta, liquidez, deuda segura,
    fichajes...) llaman a `build_lineup` sin el y ven el once de
    siempre, interruptor puesto o no. El mismo precedente que
    `con_calendario` y `sin_los_que_se_van`. Con
    `BORDALAS_EL_ONCE_SIN_LOS_QUE_SE_VAN` puesto, su busqueda sin los
    que se van usa esta misma ordenacion.

    Lo que no toca: `unknown` y `discarded` siguen siendo VIGILAR
    (alineables sin aviso) en `player_availability`, aunque
    `el_once_objetivo` los mide como FUERA. Eso es otro arreglo.

EL INTERRUPTOR

    `BORDALAS_EL_ONCE_QUE_SE_PUEDE_ESCRIBIR`. Nace APAGADO: sin el, el
    once es el de hoy byte a byte (`test_el_once_que_se_puede_escribir_v1`,
    bateria corta en la verja y larga con `--larga`). Se lee en UN
    sitio, `lineup_monitor`; el motor recibe el argumento y el ejecutor
    solo mira la marca. Nunca lanza: si algo falla, el once de hoy.
"""

from __future__ import annotations

import math
import os


ENV = "BORDALAS_EL_ONCE_QUE_SE_PUEDE_ESCRIBIR"

# Donde viaja la marca, en la salida de `build_lineup`.
CLAVE = "el_once_que_se_puede_escribir"

# Lo que se le resta en la busqueda del punto 3 al que no se puede
# escribir sin mas. Mas que once veces el bono del Dios (10.000.000)
# mas cualquier score (~1.000.000), y mas que los castigos del once sin
# los que se van (`NO_ENTRA`, 1.200.000.000): primero, cuantos menos
# dudosos mejor; luego, el score.
DUDA = 10_000_000_000.0

# Los motivos de la marca.
SANO = "SANO"
UN_DIOS_EN_DUDA = "UN_DIOS_EN_DUDA"
SIN_ONCE_SANO = "SIN_ONCE_SANO"
SIN_ONCE_DE_ONCE = "SIN_ONCE_DE_ONCE"
NO_SE_PUEDE_ESCRIBIR = "NO_SE_PUEDE_ESCRIBIR"

TEXTOS = {
    SANO: "once de alineables sin aviso: se puede escribir",
    UN_DIOS_EN_DUDA: "un Dios en duda juega (la regla del 18/08) y se escribe",
    SIN_ONCE_SANO: (
        "ningun dibujo se llena sin dudosos: se escribe el que lleva menos"
    ),
    SIN_ONCE_DE_ONCE: "no hay once de 11 alineables: nada que escribir",
    NO_SE_PUEDE_ESCRIBIR: "el once lleva un dudoso sin autorizar: no se escribe",
}


def activa() -> bool:
    """`BORDALAS_EL_ONCE_QUE_SE_PUEDE_ESCRIBIR`, leido como los demas.
    Nunca lanza."""
    try:
        return str(os.environ.get(ENV, "")).strip().lower() in {
            "1", "true", "si", "yes"}
    except Exception:                               # noqa: BLE001
        return False


# ============================================================
# AYUDAS QUE NUNCA LANZAN
# ============================================================

def _int(x, defecto=None):
    try:
        if x is None or isinstance(x, bool):
            return defecto
        return int(x)
    except (TypeError, ValueError):
        return defecto


def _num(x, defecto=0.0) -> float:
    try:
        if x is None or isinstance(x, bool):
            return defecto
        valor = float(x)
        return defecto if math.isnan(valor) else valor
    except (TypeError, ValueError):
        return defecto


def _dict(x) -> dict:
    return x if isinstance(x, dict) else {}


def _lista(x) -> list:
    return x if isinstance(x, list) else []


def _pid(ficha) -> int | None:
    return _int(_dict(ficha).get("id"))


# ============================================================
# 1. QUIEN SE PUEDE ESCRIBIR
# ============================================================

def sano(ficha) -> bool:
    """Alineable sin aviso: lo que el ejecutor cuenta en
    `playable_count`."""
    ficha = _dict(ficha)
    return bool(ficha.get("lineup_eligible") and ficha.get("automatic_lineup"))


def en_duda(ficha) -> bool:
    """Alineable, pero con aviso (`doubt`, `doubtful`, `questionable`):
    la busqueda de emergencia lo usa y el ejecutor no lo escribe."""
    ficha = _dict(ficha)
    return bool(ficha.get("lineup_eligible") and not ficha.get("automatic_lineup"))


def dios_en_duda(ficha) -> bool:
    """Un Dios (`mandatory_hierarchy`: no sentado por un 0 % motivado)
    en duda. Juega: la regla del 18/08."""
    return en_duda(ficha) and bool(_dict(ficha).get("mandatory_hierarchy"))


def se_escribe_sin_mas(ficha) -> bool:
    """Sano, o un Dios en duda."""
    return sano(ficha) or dios_en_duda(ficha)


# ============================================================
# 2. LA ORDENACION DEL ONCE QUE SE ESCRIBE
# ============================================================

def _candidata(resultado, nombre, formacion, motivo) -> dict:
    """Una candidata con las mismas claves que las de
    `evaluate_formation`, mas lo que dice si se puede escribir."""
    elegidos = _lista(_dict(resultado).get("selected"))
    return {
        **_dict(resultado),
        "formation_name": nombre,
        "formation": formacion,
        "used_warning_players": any(not sano(c) for c in elegidos),
        "se_puede_escribir": True,
        "motivo_para_escribir": motivo,
        "dudosos_autorizados": sorted(
            pid for pid in (_pid(c) for c in elegidos if not sano(c))
            if pid is not None
        ),
    }


def _completo(resultado) -> bool:
    elegidos = _lista(_dict(resultado).get("selected"))
    ids = {_pid(c) for c in elegidos}
    return bool(
        _dict(resultado).get("complete")
        and len(elegidos) == 11
        and None not in ids
        and len(ids) == 11
    )


def _con_sus_numeros(resultado, fichas) -> dict:
    """La candidata de la busqueda castigada con cada ficha y el score
    de verdad (los de `fichas`, por id), y su puesto."""
    elegidos = [
        {**fichas[_pid(c)], "lineup_position": _dict(c).get("lineup_position")}
        if _pid(c) in fichas
        else c
        for c in _lista(_dict(resultado).get("selected"))
    ]
    return {
        **_dict(resultado),
        "selected": elegidos,
        "score": sum(_num(_dict(c).get("lineup_score")) for c in elegidos),
    }


def ordenar(players, candidatas, formaciones, buscar_en_un_dibujo) -> list:
    """
    Las candidatas del once QUE SE ESCRIBE, de mejor a peor: la primera
    es el once. `candidatas`, las de la busqueda de siempre sobre
    `players` (`lineup_engine._todas_las_formaciones`); `formaciones`,
    `{nombre: formacion}`; `buscar_en_un_dibujo(lista, formacion,
    admite_dudosos)`, la busqueda de un dibujo
    (`search_best_lineup_for_formation`, con la memoria del once).

    Primero las que se pueden escribir (cabecera, puntos 2 y 3), con
    `se_puede_escribir`, `motivo_para_escribir` y `dudosos_autorizados`;
    detras, las de siempre de los dibujos que no. Si nadie esta en duda,
    o si ningun dibujo llega a 11, las de siempre tal cual. Nunca lanza:
    si algo falla, las de siempre.
    """

    try:
        if not candidatas:
            return candidatas

        players = [p for p in (players or []) if isinstance(p, dict)]

        # 1. Sin nadie en duda, la busqueda de siempre ya es la de los
        #    sanos: nada que cambiar.
        if not any(en_duda(p) for p in players):
            return candidatas

        # 2. Los que se escriben sin mas. Sin un Dios en duda son los
        #    sanos: la busqueda normal de siempre, la misma entrada
        #    (la memoria del once la recuerda).
        if any(dios_en_duda(p) for p in players):
            lista = [p for p in players if se_escribe_sin_mas(p)]
            admite = True
        else:
            lista = players
            admite = False

        escribibles = []

        for nombre, formacion in formaciones.items():
            resultado = buscar_en_un_dibujo(lista, formacion, admite)
            if _completo(resultado) and all(
                se_escribe_sin_mas(c) for c in resultado["selected"]
            ):
                motivo = (
                    UN_DIOS_EN_DUDA
                    if any(dios_en_duda(c) for c in resultado["selected"])
                    else SANO
                )
                escribibles.append(_candidata(resultado, nombre, formacion, motivo))

        escribibles.sort(key=lambda c: _num(c.get("score")), reverse=True)

        # 3. Si ninguno, el que lleva menos dudosos.
        if not escribibles:
            fichas = {_pid(p): p for p in players}
            castigada = [
                {**p, "lineup_score": _num(p.get("lineup_score")) - DUDA}
                if en_duda(p) and not se_escribe_sin_mas(p)
                else p
                for p in players
            ]

            for nombre, formacion in formaciones.items():
                resultado = buscar_en_un_dibujo(castigada, formacion, True)
                if _completo(resultado):
                    escribibles.append(_candidata(
                        _con_sus_numeros(resultado, fichas),
                        nombre, formacion, SIN_ONCE_SANO,
                    ))

            escribibles.sort(
                key=lambda c: (
                    -sum(
                        1 for p in c["selected"] if not se_escribe_sin_mas(p)
                    ),
                    _num(c.get("score")),
                ),
                reverse=True,
            )

        if not escribibles:
            return candidatas

        dibujos = {c["formation_name"] for c in escribibles}

        return escribibles + [
            c for c in candidatas
            if _dict(c).get("formation_name") not in dibujos
        ]

    except Exception:                               # noqa: BLE001
        return candidatas


# ============================================================
# 3. LA MARCA, Y QUIEN LA LEE
# ============================================================

def marca(players, selected, candidatas) -> dict:
    """
    La marca del once que se escribe (cabecera, punto 4), sobre el once
    YA rematado (`selected`) y la primera de `candidatas` (la que lo
    eligio). Nunca lanza: con basura, NO_SE_PUEDE_ESCRIBIR.
    """

    try:
        elegidos = [c for c in _lista(selected) if isinstance(c, dict)]
        primera = _dict((_lista(candidatas) or [None])[0])
        permitidos = {
            _int(x) for x in _lista(primera.get("dudosos_autorizados"))
        }
        dentro = {_pid(c) for c in elegidos}

        dudosos = [
            {"id": _pid(p), "name": p.get("name"), "en_el_once": _pid(p) in dentro,
             "dios": bool(p.get("mandatory_hierarchy"))}
            for p in (players or [])
            if isinstance(p, dict) and en_duda(p)
        ]

        no_sanos = [c for c in elegidos if not sano(c)]

        if len(elegidos) != 11 or len(dentro - {None}) != 11:
            motivo, autorizados = SIN_ONCE_DE_ONCE, []
        elif not no_sanos:
            motivo, autorizados = SANO, []
        elif all(
            c.get("lineup_eligible") and _pid(c) in permitidos for c in no_sanos
        ):
            motivo = primera.get("motivo_para_escribir") or SIN_ONCE_SANO
            autorizados = sorted(_pid(c) for c in no_sanos)
        else:
            motivo, autorizados = NO_SE_PUEDE_ESCRIBIR, []

        se_puede = motivo in (SANO, UN_DIOS_EN_DUDA, SIN_ONCE_SANO)
        nombres = {_pid(c): c.get("name") for c in elegidos}

        texto = TEXTOS[motivo]
        if autorizados:
            texto += " (en duda: " + ", ".join(
                str(nombres.get(pid) or pid) for pid in autorizados) + ")"

        return {
            "se_puede_escribir": se_puede,
            "motivo": motivo,
            "autorizados": autorizados,
            "dudosos": dudosos,
            "texto": texto,
        }

    except Exception:                               # noqa: BLE001
        return {"se_puede_escribir": False, "motivo": NO_SE_PUEDE_ESCRIBIR,
                "autorizados": [], "dudosos": [],
                "texto": TEXTOS[NO_SE_PUEDE_ESCRIBIR]}


def admite(lineup) -> bool:
    """
    Si el ejecutor puede escribir este once aunque `playable_count` sea
    menor que 11: trae la marca, dice que se puede escribir, son 11 ids
    distintos y cada uno de los que no son alineables sin aviso es
    alineable y esta en `autorizados`. Sin la marca (interruptor
    apagado), False: el ejecutor de siempre. Nunca lanza.
    """

    try:
        lineup = _dict(lineup)
        la_marca = lineup.get(CLAVE)

        if not isinstance(la_marca, dict) or la_marca.get("se_puede_escribir") is not True:
            return False

        elegidos = lineup.get("selected")

        if not isinstance(elegidos, list) or len(elegidos) != 11:
            return False

        ids = [_pid(c) for c in elegidos]

        if None in ids or len(set(ids)) != 11:
            return False

        autorizados = {_int(x) for x in _lista(la_marca.get("autorizados"))}

        for ficha in elegidos:
            if not isinstance(ficha, dict) or not ficha.get("lineup_eligible"):
                return False
            if ficha.get("automatic_lineup"):
                continue
            if _pid(ficha) not in autorizados:
                return False

        return True

    except Exception:                               # noqa: BLE001
        return False
