"""
La clasificacion que se pinta es la de Biwenger, no la del perfil.

EL CASO (28/10/2026, noche)

    `status.json` de las 20:11 (run 40751392431). Tres cuadros de
    la pantalla —`losRivales`, `league_center.fantasy_standings` y
    `rival_intelligence.managers`— decian:

        Pepe 383 y TERCERO · Manzagool 308 · Mex 246

    Y Biwenger, en LA MISMA FOTO (`competition.standings`):

        Pepe 422 y SEGUNDO · Manzagool 365 · Mex 324

    Y al reves con el valor: la clasificacion de Biwenger ponia a
    Pollo17 con 105,74 M de plantilla contando a Kubo, que vendio
    el 28/10. Su plantilla de ahora suma 102,29 M.

LA CAUSA, DOS CACHES QUE NO SE ENTERAN DE LO MISMO

    1. LOS PUNTOS salian del PERFIL de cada manager
       (`/user/{id}`), y el perfil se cachea desde el 07/09: solo
       se vuelve a pedir cuando ese manager ficha o vende
       (`cache_del_reset.perfiles_a_refrescar`). Cerrar una
       jornada NO es un movimiento del tablon: tras la J10, el que
       no se movio seguia con los puntos de la J9. Pollo17 si se
       movio —vendio a Kubo— y por eso era el unico que salia
       bien.

    2. EL VALOR salia de `rounds/league`, que se cachea desde el
       reset (`jornada`). Su `teamValue` es el de esta mañana, de
       antes de vender a Kubo. La plantilla que se suma con el
       catalogo es la de ahora: la del perfil, que SI se refresco
       al vender.

LA REGLA

    PUNTOS Y PUESTO: de la clasificacion de Biwenger de esta
    foto, con su hora (`as_of`). Si no viene, o no trae a ese
    manager, del perfil, y se dice: `points_source: "PERFIL"` y la
    hora del perfil si se sabe.

    VALOR DE PLANTILLA: la suma de la plantilla actual, jugador a
    jugador con el precio del catalogo. Sin plantilla, el
    `teamValue` de Biwenger, y se dice: `team_value_source`.

LO QUE NO TOCA, Y POR QUE

    Es la VISTA. El libro de rivales (`rival_intelligence`, en
    memoria y en disco) sigue con los puntos del perfil, porque de
    ellos cuelgan el abono de la jornada, el saldo estimado de
    cada rival, su tope de puja y el `points_rank` con el que el
    motor de transacciones competitivas marca un rival directo.
    Eso es decidir, y cambiarlo va aparte y con su interruptor.

    Aqui solo se corrigen COPIAS que van a la pantalla. Nada de
    lo que se recibe se modifica.

    Nunca lanza.
"""

from __future__ import annotations

from datetime import datetime, timezone


FUENTE_BIWENGER = "BIWENGER"
FUENTE_PERFIL = "PERFIL"
FUENTE_MIXTA = "MIXTA"

VALOR_SUMADO = "PLANTILLA_SUMADA"
VALOR_DE_BIWENGER = "BIWENGER"


def safe_int(value, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


# ============================================================
# LA HORA
# ============================================================


def _iso_de_epoch(epoch) -> str | None:
    """Epoch -> ISO en UTC. `None` si no hay epoch que valga."""

    try:
        segundos = int(epoch)
    except (TypeError, ValueError):
        return None

    if segundos <= 0:
        return None

    try:
        return datetime.fromtimestamp(
            segundos, timezone.utc
        ).isoformat(timespec="seconds")
    except (OverflowError, OSError, ValueError):
        return None


def el_sello(snapshot: dict | None) -> dict:
    """
    De cuando es la clasificacion de Biwenger de esta foto.

    `rounds_as_of` es la hora en que se pidio `rounds/league` de
    verdad: si vino de la cache del reset, la de esa peticion, no
    la de la foto. Las fotos de antes del 28/10 no lo traen y se
    cae a la hora de la foto, y se dice: con esa, la clasificacion
    puede ser de horas antes.
    """

    foto = snapshot if isinstance(snapshot, dict) else {}

    pedida = _iso_de_epoch(foto.get("rounds_as_of"))

    if pedida:
        return {
            "as_of": pedida,
            "as_of_source": "rounds_as_of",
        }

    marca = foto.get("timestamp")

    if marca:
        return {
            "as_of": str(marca),
            "as_of_source": "snapshot.timestamp",
        }

    return {"as_of": None, "as_of_source": None}


# ============================================================
# LO QUE DICE BIWENGER
# ============================================================


def indice_de_biwenger(competition: dict | None) -> dict:
    """`{user_id: fila}` de `competition.standings`. Vacio si no hay."""

    filas = (
        (competition or {}).get("standings")
        if isinstance(competition, dict)
        else None
    ) or []

    indice = {}

    for fila in filas:

        if not isinstance(fila, dict):
            continue

        uid = safe_int(fila.get("user_id"))

        if uid > 0:
            indice[uid] = fila

    return indice


def valor_sumado(manager: dict | None) -> int | None:
    """
    Lo que suma la plantilla de ahora, segun el libro de rivales.

    `roster_value` es la suma, jugador a jugador, del precio del
    catalogo. `None` si no hay plantilla: un cero se leeria como
    "no tiene nada".
    """

    if not isinstance(manager, dict):
        return None

    if safe_int(manager.get("roster_count")) <= 0:
        return None

    valor = safe_int(manager.get("roster_value"))

    return valor if valor > 0 else None


def _valor_de_biwenger(fila: dict | None) -> int | None:
    """
    El `teamValue` que dijo Biwenger para esa fila.

    Si la fila ya paso por `con_el_valor_de_las_plantillas`, su
    `team_value` es el sumado y el de Biwenger esta al lado.
    """

    if not isinstance(fila, dict):
        return None

    if "team_value_biwenger" in fila:
        return safe_int(fila.get("team_value_biwenger"))

    return safe_int(fila.get("team_value"))


def _hora_del_perfil(perfil: dict | None) -> str | None:
    return _iso_de_epoch((perfil or {}).get("_fetched_at"))


# ============================================================
# LA TABLA (league_center.fantasy_standings)
# ============================================================


def la_tabla(
    *,
    managers: list | None,
    competition: dict | None,
    perfiles: dict | None = None,
    iconos: dict | None = None,
) -> dict:
    """
    `{filas, fuente}`. Nunca lanza.

    Si cruzar con Biwenger fallara, se pinta la del perfil y se
    dice por que; si ni eso, una tabla vacia con el motivo. La
    tabla cuelga de la generacion entera del estado: una averia
    aqui no puede dejar la pantalla sin foto.
    """

    try:
        return _la_tabla(
            managers=managers,
            competition=competition,
            perfiles=perfiles,
            iconos=iconos,
        )

    except Exception as error:                      # noqa: BLE001
        averia = f"{type(error).__name__}: {error}"

    try:
        tabla = _la_tabla(
            managers=managers,
            competition=None,
            perfiles=perfiles,
            iconos=iconos,
        )

        tabla["fuente"]["reason"] = (
            f"No se pudo cruzar con la clasificacion de Biwenger "
            f"({averia}). " + tabla["fuente"]["reason"]
        )

        return tabla

    except Exception as error:                      # noqa: BLE001
        return {
            "filas": [],
            "fuente": {
                "points_source": None,
                "as_of": None,
                "as_of_source": None,
                "from_biwenger": 0,
                "from_profile": 0,
                "team_value_source": None,
                "reason": (
                    f"No se pudo montar la clasificacion: {averia}; "
                    f"{type(error).__name__}: {error}"
                ),
            },
        }


def _la_tabla(
    *,
    managers: list | None,
    competition: dict | None,
    perfiles: dict | None = None,
    iconos: dict | None = None,
) -> dict:
    """
    `{filas, fuente}`. Las filas con las claves de siempre mas de
    donde sale cada numero.

    `managers` es `rival_intelligence.managers`. `competition` es
    lo que devuelve `compact_biwenger_competition`, con su
    `as_of`. `perfiles` es `{user_id: perfil}` para la hora del
    perfil cuando hay que caer a el.
    """

    perfiles = perfiles or {}
    iconos = iconos or {}

    biwenger = indice_de_biwenger(competition)

    sello = {
        "as_of": (competition or {}).get("as_of")
        if isinstance(competition, dict)
        else None,
        "as_of_source": (competition or {}).get("as_of_source")
        if isinstance(competition, dict)
        else None,
    }

    filas = []
    vistos = set()

    for manager in (managers or []):

        if not isinstance(manager, dict):
            continue

        uid = safe_int(manager.get("user_id"))

        vistos.add(uid)

        de_biwenger = biwenger.get(uid)
        perfil = perfiles.get(uid) or {}

        puntos_del_perfil = safe_int(manager.get("points"))

        if de_biwenger is not None:
            puntos = safe_int(de_biwenger.get("points"))
            fuente = FUENTE_BIWENGER
            hora = sello["as_of"]
            puesto = safe_int(de_biwenger.get("rank")) or None

        else:
            puntos = puntos_del_perfil
            fuente = FUENTE_PERFIL
            hora = _hora_del_perfil(perfil)
            puesto = None

        sumado = valor_sumado(manager)

        if sumado is not None:
            valor = sumado
            fuente_del_valor = VALOR_SUMADO

        elif _valor_de_biwenger(de_biwenger):
            valor = _valor_de_biwenger(de_biwenger)
            fuente_del_valor = VALOR_DE_BIWENGER

        else:
            valor = safe_int(manager.get("roster_value"))
            fuente_del_valor = VALOR_SUMADO

        saldo = safe_int(manager.get("balance"))

        filas.append({
            "_puesto_de_biwenger": puesto,
            "user_id": uid,
            "name": manager.get("name", "?"),
            "points": puntos,
            "balance": saldo,
            "roster_value": valor,

            # El patrimonio con el MISMO valor que se pinta al
            # lado. Con el viejo, la columna no cuadraria a ojo.
            # Sin caja reconstruida no se suma nada: se queda lo
            # que dijera el libro (doctrina 36).
            "net_worth": (
                saldo + valor
                if manager.get("balance") is not None
                else safe_int(manager.get("net_worth"))
            ),

            "is_us": bool(
                manager.get("threat_level") == "US"
                or (de_biwenger or {}).get("is_current_user")
            ),
            "icon": (
                perfil.get("icon")
                or iconos.get(uid)
                or (de_biwenger or {}).get("icon")
            ),

            "points_source": fuente,
            "points_as_of": hora,

            # LO QUE DECIA EL PERFIL, al lado. Es lo que leen los
            # motores; si no cuadra con Biwenger, se ve aqui.
            "profile_points": puntos_del_perfil,

            "roster_value_source": fuente_del_valor,
            "team_value_biwenger": _valor_de_biwenger(de_biwenger),
        })

    # LOS QUE BIWENGER TIENE Y EL LIBRO NO. Sin ellos los puestos
    # saltarian un numero. No hay saldo que poner: `None`, no 0.
    for uid, de_biwenger in biwenger.items():

        if uid in vistos:
            continue

        valor = safe_int(_valor_de_biwenger(de_biwenger))

        filas.append({
            "_puesto_de_biwenger": (
                safe_int(de_biwenger.get("rank")) or None
            ),
            "user_id": uid,
            "name": de_biwenger.get("name") or "?",
            "points": safe_int(de_biwenger.get("points")),
            "balance": None,
            "roster_value": valor,
            "net_worth": None,
            "is_us": bool(de_biwenger.get("is_current_user")),
            "icon": iconos.get(uid) or de_biwenger.get("icon"),
            "points_source": FUENTE_BIWENGER,
            "points_as_of": sello["as_of"],
            "profile_points": None,
            "roster_value_source": VALOR_DE_BIWENGER,
            "team_value_biwenger": valor,
        })

    de_biwenger_todas = bool(filas) and all(
        f["points_source"] == FUENTE_BIWENGER for f in filas
    )

    if de_biwenger_todas:
        # EL PUESTO, EL DE BIWENGER. Con sus desempates, que no
        # son los nuestros.
        filas.sort(
            key=lambda f: (
                f["_puesto_de_biwenger"] or 999,
                str(f.get("name") or ""),
            )
        )

        for indice, fila in enumerate(filas, start=1):
            fila["rank"] = fila["_puesto_de_biwenger"] or indice

    else:
        # SIN BIWENGER (o con huecos) SE CUENTA: puntos, y a
        # igualdad el puesto que diera Biwenger, y el patrimonio.
        filas.sort(
            key=lambda f: (
                -safe_int(f.get("points")),
                f["_puesto_de_biwenger"] or 999,
                -safe_int(f.get("net_worth")),
                str(f.get("name") or ""),
            )
        )

        for indice, fila in enumerate(filas, start=1):
            fila["rank"] = indice

    salida = []

    for fila in filas:
        fila.pop("_puesto_de_biwenger", None)
        salida.append({"rank": fila.pop("rank"), **fila})

    de_biwenger = sum(
        1 for f in salida if f["points_source"] == FUENTE_BIWENGER
    )
    del_perfil = len(salida) - de_biwenger

    if not salida:
        fuente = None
    elif not del_perfil:
        fuente = FUENTE_BIWENGER
    elif not de_biwenger:
        fuente = FUENTE_PERFIL
    else:
        fuente = FUENTE_MIXTA

    return {
        "filas": salida,
        "fuente": {
            "points_source": fuente,
            "as_of": sello["as_of"] if de_biwenger else None,
            "as_of_source": (
                sello["as_of_source"] if de_biwenger else None
            ),
            "from_biwenger": de_biwenger,
            "from_profile": del_perfil,
            "team_value_source": VALOR_SUMADO,
            "reason": _por_que(fuente, del_perfil, sello),
        },
    }


def _por_que(fuente, del_perfil: int, sello: dict) -> str:

    if fuente is None:
        return "Sin managers: no hay clasificacion que pintar."

    if fuente == FUENTE_BIWENGER:
        return (
            "Puntos y puesto de la clasificacion de Biwenger"
            + (f" ({sello['as_of']})" if sello.get("as_of") else "")
            + "; valor, la suma de la plantilla de ahora."
        )

    perfil = (
        f"{del_perfil} con los puntos del PERFIL, que solo se "
        f"vuelve a pedir cuando el manager ficha o vende: pueden "
        f"ir una jornada o mas por detras. Mira `points_as_of`."
    )

    if fuente == FUENTE_PERFIL:
        return (
            "Esta foto no trae la clasificacion de Biwenger. "
            + perfil
        )

    return (
        "La clasificacion de Biwenger no trae a todos. " + perfil
    )


# ============================================================
# LAS OTRAS DOS COPIAS
# ============================================================


def con_los_puntos_de_biwenger(
    filas: list | None,
    competition: dict | None,
) -> list:
    """
    `rival_intelligence.managers` de la pantalla, con los puntos y
    el puesto de Biwenger.

    Filas NUEVAS: las que llegan no se tocan. `profile_points` se
    queda al lado, que es lo que usaron el abono, el saldo y el
    tope de puja de esa misma fila.
    """

    try:
        return _con_los_puntos_de_biwenger(filas, competition)

    except Exception:                               # noqa: BLE001
        # Sin cruzar, las de siempre: mejor viejas que ninguna.
        return [f for f in (filas or []) if isinstance(f, dict)]


def _con_los_puntos_de_biwenger(filas, competition) -> list:

    biwenger = indice_de_biwenger(competition)

    hora = (
        (competition or {}).get("as_of")
        if isinstance(competition, dict)
        else None
    )

    salida = []

    for fila in (filas or []):

        if not isinstance(fila, dict):
            continue

        de_biwenger = biwenger.get(safe_int(fila.get("user_id")))

        nueva = {
            **fila,
            "profile_points": safe_int(fila.get("points")),
        }

        if de_biwenger is not None:
            nueva["points"] = safe_int(de_biwenger.get("points"))
            nueva["rank"] = (
                safe_int(de_biwenger.get("rank"))
                or fila.get("rank")
            )
            nueva["points_source"] = FUENTE_BIWENGER
            nueva["points_as_of"] = hora

        else:
            nueva["points_source"] = FUENTE_PERFIL
            nueva["points_as_of"] = None

        salida.append(nueva)

    return salida


def con_el_valor_de_las_plantillas(
    competition: dict | None,
    managers: list | None,
) -> dict:
    """
    `competition` con el valor de plantilla sumado.

    El `teamValue` de Biwenger viene de `rounds/league`, que se
    cachea desde el reset: no se entera de una venta de media
    tarde. Se queda al lado como `team_value_biwenger`.
    """

    try:
        return _con_el_valor_de_las_plantillas(competition, managers)

    except Exception:                               # noqa: BLE001
        # Sin sumar, la de Biwenger tal cual.
        return competition


def _con_el_valor_de_las_plantillas(competition, managers):

    if not isinstance(competition, dict):
        return competition

    por_id = {
        safe_int(m.get("user_id")): m
        for m in (managers or [])
        if isinstance(m, dict) and safe_int(m.get("user_id"))
    }

    filas = []

    for fila in (competition.get("standings") or []):

        if not isinstance(fila, dict):
            continue

        manager = por_id.get(safe_int(fila.get("user_id")))

        sumado = valor_sumado(manager)

        nueva = {
            **fila,
            "team_value_biwenger": fila.get("team_value"),
            "team_value_inc_biwenger": fila.get("team_value_inc"),
        }

        if sumado is not None:
            nueva["team_value"] = sumado
            nueva["team_value_inc"] = safe_int(
                manager.get("roster_price_increment")
            )
            nueva["team_value_source"] = VALOR_SUMADO

        else:
            nueva["team_value_source"] = VALOR_DE_BIWENGER

        filas.append(nueva)

    return {**competition, "standings": filas}
