"""
El libro de la divergencia: cuando el precio y la demanda no
dicen lo mismo.

DE DONDE SALE

    El 06/09/2026, al comparar las tres fuentes de precio, salio
    que no son tres opiniones: son dos medidas y una repetida.
    Todas copian el mismo numero de Biwenger, asi que su acuerdo
    es redundancia.

    Pero aparecio otra cosa. En 16 jugadores el precio se movio a
    un lado y el PULSO DE DEMANDA de Comuniate -cuanta gente esta
    pujando ahora mismo- apuntaba al otro. Mikel Rodriguez bajaba
    un 6,2 % con 70 puntos netos de presion compradora.

    Eso si es informacion nueva: no es otra copia del precio.

LA HIPOTESIS, QUE ESTA SIN COMPROBAR

    Que esa divergencia anticipe algo. NO ESTA MEDIDO. En el
    codigo no se llama prediccion en ningun sitio, y no lo hara
    hasta que este libro diga que acierta.

    No se puede comprobar con lo que hay: las fuentes publican la
    demanda de HOY, no una serie. Asi que hay que empezar a
    guardarla, que es todo lo que hace este fichero.

QUE HACE FALTA PARA QUE EL RESULTADO VALGA: EL CONTROL

    Que un divergente suba no dice nada si ese dia subieron
    todos. Por eso cada apunte guarda tambien a los NO
    divergentes del mismo dia, y la comparacion es siempre entre
    los dos grupos.

    Sin grupo de control esto seria una coleccion de anecdotas.

DE DONDE SALE `demand_net`, Y POR QUE ES UNA MEDIDA Y NO UN CONSENSO

        demand_net = % de usuarios que han pujado en 24 h
                   - % de ligas donde esta puesto a la venta

    Los dos numeros son de COMUNIATE, y solo de Comuniate: es la
    unica de las cuatro fuentes que publica demanda. FutbolFantasy
    y Analitica publican precio, que es otra cosa.

    Asi que esto es UNA MEDIDA, no un consenso, y el libro lo dice
    en cada apunte con `demand_source`. El dia que otra fuente
    publique demanda, se podra comparar; hoy no hay con que.

LO QUE EL ESTUDIO DEL 07/09 OBLIGA A GUARDAR

    El precio de Biwenger tiene momento, y muy fuerte: de los que
    bajaron ayer, el 90,7 % vuelve a bajar hoy, y solo el 0,5 %
    bate al mercado. El 83,8 % de los jugadores no cambia de
    direccion ni una vez en seis dias.

    Eso cambia la pregunta. Una divergencia "precio baja, demanda
    sube" no es una oportunidad porque el precio este barato: es
    una apuesta a que una rampa muy persistente se va a girar.

    Por eso cada apunte guarda `trend_days`, los dias que lleva la
    rampa. Sin ese campo no se podra contestar a lo unico que
    importa: si la demanda avisa del giro ANTES de que ocurra.

FASE OBSERVADOR

    Ningun motor lee esto.
"""

from __future__ import annotations

import json

from datetime import datetime, timedelta, timezone
from pathlib import Path


VERSION = "V1.0"

LEDGER_PATH = (
    Path("data")
    / "intelligence"
    / "divergence_ledger.json"
)


# Los dos horizontes que se cierran. Tres dias es el horizonte de
# reventa que usa el motor; siete cubre una jornada entera.
HORIZONS_DAYS = (3, 7)


# Cuanta presion de demanda hace falta para llamarlo divergencia.
#
# Por debajo de esto casi todos los jugadores estan en el mismo
# monton y la señal no distingue a nadie de nadie: es el mismo
# corte que ya usa el ojeador al publicar el pulso.
MIN_DEMAND_NET = 20.0

# Y cuanto tiene que haberse movido el precio. Un movimiento de
# cero no diverge de nada: esta quieto.
MIN_PRICE_MOVE_PERCENT = 0.01


# Pasado esto sin poder cerrar, se deja de esperar. No se inventa
# un resultado.
GIVE_UP_DAYS = 21


UP = "UP"
DOWN = "DOWN"


def safe_int(value, default: int = 0) -> int:
    try:
        return int(round(float(value)))
    except (TypeError, ValueError):
        return default


def safe_float(value, default=None):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def empty_ledger() -> dict:
    return {
        "version": VERSION,
        "observations": {},
    }


def load_ledger(path: Path | None = None) -> dict:

    ruta = path or LEDGER_PATH

    if not ruta.exists():
        return empty_ledger()

    try:
        datos = json.loads(ruta.read_text(encoding="utf-8-sig"))

    except (OSError, json.JSONDecodeError):
        return empty_ledger()

    if not isinstance(datos, dict):
        return empty_ledger()

    datos.setdefault("version", VERSION)
    datos.setdefault("observations", {})

    return datos


def save_ledger(ledger: dict, path: Path | None = None) -> None:

    ruta = path or LEDGER_PATH

    ruta.parent.mkdir(parents=True, exist_ok=True)

    ruta.write_text(
        json.dumps(ledger, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _parse(marca) -> datetime | None:
    if not marca:
        return None

    try:
        momento = datetime.fromisoformat(
            str(marca).replace("Z", "+00:00")
        )

    except ValueError:
        return None

    if momento.tzinfo is None:
        momento = momento.replace(tzinfo=timezone.utc)

    return momento


# ============================================================
# LEER UNA FICHA DEL INFORME
# ============================================================


def classify(
    price_change_percent,
    demand_net,
) -> tuple[bool, str | None]:
    """
    ¿Divergen? Y si divergen, ¿de que manera?

    Devuelve `(divergente, tipo)`. Un jugador que no se mueve o
    sin demanda medible NO es divergente: es que no hay nada que
    comparar.
    """

    precio = safe_float(price_change_percent)
    demanda = safe_float(demand_net)

    if precio is None or demanda is None:
        return (False, None)

    if abs(precio) < MIN_PRICE_MOVE_PERCENT:
        return (False, None)

    if abs(demanda) < MIN_DEMAND_NET:
        return (False, None)

    if precio < 0 and demanda > 0:
        return (True, "PRECIO_BAJA_DEMANDA_SUBE")

    if precio > 0 and demanda < 0:
        return (True, "PRECIO_SUBE_DEMANDA_BAJA")

    return (False, None)


def _observation(player_id: str, ficha: dict, momento: datetime) -> dict | None:
    """Una fila del libro a partir de una ficha del informe."""

    consenso = ficha.get("consensus") or {}
    demanda = ficha.get("demand") or {}

    precio = safe_int(ficha.get("market_price"))

    if precio <= 0:
        return None

    cambio_pct = consenso.get("mean_magnitude_percent")
    cambio_eur = consenso.get("mean_magnitude_eur")

    if cambio_pct is None:
        return None

    # El signo va en la direccion del consenso, no en la magnitud:
    # el ojeador publica la magnitud siempre positiva cuando la
    # direccion es DOWN.
    if consenso.get("direction") == DOWN:
        cambio_pct = -abs(float(cambio_pct))
        cambio_eur = -abs(safe_int(cambio_eur)) if cambio_eur is not None else None

    presion = demanda.get("pressure_points")

    divergente, tipo = classify(cambio_pct, presion)

    return {
        "player_id": player_id,
        "player_name": ficha.get("player_name"),
        "seen_at": momento.isoformat(),

        "price": precio,
        "price_change_eur": cambio_eur,
        "price_change_percent": round(float(cambio_pct), 3),

        # De donde sale la demanda, escrito en cada fila: es UNA
        # medida, de Comuniate, no un consenso de varias fuentes.
        "demand_net": presion,
        "demand_source": (
            "COMUNIATE_PULSO (compras 24 h - ventas)"
            if presion is not None
            else None
        ),

        # LO QUE PIDE EL ESTUDIO DEL 07/09
        #
        #     Los dias que lleva la rampa. Sin esto no se puede
        #     contestar a si la demanda avisa del giro, que es lo
        #     unico interesante en un precio con este momento.
        "trend_days": ficha.get("trend_days"),

        "divergent": divergente,
        "divergence_kind": tipo,

        "outcome": "PENDING",
        "price_after_3d": None,
        "price_after_7d": None,
        "return_3d_percent": None,
        "return_7d_percent": None,
        "resolved_at": None,
    }


def record_report(
    report: dict | None,
    ledger: dict | None = None,
    *,
    path: Path | None = None,
    save: bool = True,
    now: datetime | None = None,
) -> dict:
    """
    Apunta la foto de hoy: divergentes Y no divergentes.

    Los dos, siempre. El grupo de control no es un extra: sin el
    no hay resultado que valga.
    """

    libro = load_ledger(path) if ledger is None else ledger

    observaciones = libro.setdefault("observations", {})

    momento = now or datetime.now(timezone.utc)
    dia = momento.date().isoformat()

    for player_id, ficha in (
        (report or {}).get("players") or {}
    ).items():

        if not isinstance(ficha, dict):
            continue

        # Una fila por jugador y dia. El ojeador puede refrescar
        # varias veces al dia y no son observaciones distintas.
        clave = f"{player_id}|{dia}"

        if clave in observaciones:
            continue

        fila = _observation(str(player_id), ficha, momento)

        if fila is not None:
            observaciones[clave] = fila

    libro["version"] = VERSION

    if save:
        save_ledger(libro, path)

    return libro


# ============================================================
# CERRAR
# ============================================================


def settle(
    prices: dict | None,
    ledger: dict | None = None,
    *,
    path: Path | None = None,
    save: bool = True,
    now: datetime | None = None,
) -> dict:
    """
    Apunta el precio real a los 3 y a los 7 dias.

    `prices` es `{player_id: precio}` de Biwenger HOY.
    """

    libro = load_ledger(path) if ledger is None else ledger

    ahora = now or datetime.now(timezone.utc)

    precios = {
        str(k): safe_int(v)
        for k, v in (prices or {}).items()
    }

    for fila in (libro.get("observations") or {}).values():

        if fila.get("outcome") == "CLOSED":
            continue

        nacida = _parse(fila.get("seen_at"))

        if nacida is None:
            continue

        precio_hoy = precios.get(str(fila.get("player_id")))
        partida = safe_int(fila.get("price"))

        edad = (ahora - nacida).days

        for dias in HORIZONS_DAYS:

            clave = f"price_after_{dias}d"

            if fila.get(clave) is not None or edad < dias:
                continue

            if not precio_hoy or partida <= 0:
                continue

            fila[clave] = precio_hoy
            fila[f"return_{dias}d_percent"] = round(
                (precio_hoy - partida) * 100.0 / partida, 3
            )

        if fila.get(f"price_after_{HORIZONS_DAYS[-1]}d") is not None:
            fila["outcome"] = "CLOSED"
            fila["resolved_at"] = ahora.isoformat()

        elif edad >= GIVE_UP_DAYS:
            # Ni precio ni paciencia. Se cierra sin inventar nada.
            fila["outcome"] = "UNKNOWN"
            fila["resolved_at"] = ahora.isoformat()

    if save:
        save_ledger(libro, path)

    return libro


# ============================================================
# EL ESTUDIO: DIVERGENTES CONTRA CONTROL
# ============================================================


def _media(valores):
    return round(sum(valores) / len(valores), 3) if valores else None


def study(
    ledger: dict | None = None,
    path: Path | None = None,
) -> dict:
    """
    ¿Le va mejor al grupo divergente que al resto?

    Nunca inventa un numero. Sin observaciones cerradas dice que
    no hay muestra, con esas palabras.
    """

    libro = load_ledger(path) if ledger is None else ledger

    filas = [
        f
        for f in (libro.get("observations") or {}).values()
        if isinstance(f, dict)
    ]

    apuntadas = len(filas)

    divergentes_hoy = sum(1 for f in filas if f.get("divergent"))

    resultados = {}

    for dias in HORIZONS_DAYS:

        clave = f"return_{dias}d_percent"

        con_dato = [f for f in filas if f.get(clave) is not None]

        divergentes = [f for f in con_dato if f.get("divergent")]
        control = [f for f in con_dato if not f.get("divergent")]

        # HACE FALTA QUE LOS DOS GRUPOS TENGAN GENTE
        #
        #     Comparar 3 divergentes contra 400 de control no es
        #     una comparacion: es una anecdota con un decorado de
        #     estadistica al lado.
        suficiente = len(divergentes) >= 20 and len(control) >= 20

        media_div = _media([f[clave] for f in divergentes])
        media_ctrl = _media([f[clave] for f in control])

        por_tipo = {}

        for tipo in ("PRECIO_BAJA_DEMANDA_SUBE", "PRECIO_SUBE_DEMANDA_BAJA"):

            grupo = [
                f[clave]
                for f in divergentes
                if f.get("divergence_kind") == tipo
            ]

            por_tipo[tipo] = {
                "n": len(grupo),
                "mean_return_percent": _media(grupo),
                "enough": len(grupo) >= 20,
            }

        resultados[f"{dias}d"] = {
            "horizon_days": dias,
            "divergent_n": len(divergentes),
            "control_n": len(control),
            "divergent_mean_return_percent": media_div,
            "control_mean_return_percent": media_ctrl,
            "difference_percent": (
                round(media_div - media_ctrl, 3)
                if media_div is not None and media_ctrl is not None
                else None
            ),
            "enough_sample": suficiente,
            "by_kind": por_tipo,
            "reason": (
                None
                if suficiente
                else (
                    f"Todavia no hay muestra: {len(divergentes)} "
                    f"divergentes y {len(control)} de control con el "
                    f"precio ya cerrado a {dias} dias. Hacen falta "
                    f"al menos 20 de cada."
                )
            ),
        }

    cerradas = sum(1 for f in filas if f.get("outcome") == "CLOSED")

    hay_algo = any(r["enough_sample"] for r in resultados.values())

    return {
        "available": bool(filas),
        "observer_only": True,

        # Que quede escrito: esto es una hipotesis, no un
        # resultado, mientras `enough_sample` sea False.
        "hypothesis_confirmed": None if not hay_algo else "VER_HORIZONTES",

        "recorded_total": apuntadas,
        "closed_total": cerradas,
        "divergent_total": divergentes_hoy,

        "horizons": resultados,

        "reason": (
            None
            if filas
            else (
                "El libro esta vacio: todavia no se ha apuntado "
                "ninguna observacion."
            )
        ),

        "caveat": (
            "Hipotesis SIN COMPROBAR. Las fuentes publican la "
            "demanda de hoy, no una serie, asi que no habia "
            "historico con que medirla: este libro empieza a "
            "guardarla desde el 07/09/2026. Hasta que haya muestra "
            "de los dos grupos, esto no dice nada."
        ),
    }


def sync_divergence(
    report: dict | None,
    prices: dict | None,
    *,
    path: Path | None = None,
) -> dict:
    """
    El enganche del ciclo: apunta lo de hoy y cierra lo vencido.

    NUNCA LANZA.
    """

    try:
        libro = record_report(report, path=path, save=False)
        libro = settle(prices, ledger=libro, path=path, save=True)

        return study(libro)

    except Exception as error:                      # noqa: BLE001
        return {
            "available": False,
            "observer_only": True,
            "recorded_total": 0,
            "closed_total": 0,
            "divergent_total": 0,
            "horizons": {},
            "reason": (
                f"No se pudo alimentar el libro de divergencia: "
                f"{type(error).__name__}: {error}"
            ),
        }
