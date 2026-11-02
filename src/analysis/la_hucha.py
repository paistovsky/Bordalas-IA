"""
LA HUCHA (02/11/2026)

POR QUE EXISTE

    Decision del CEO del 02/11 (bitacora, «OPERACION RAPHINHA, CON
    HUCHA»): Raphinha (26930, Barcelona, 144 puntos en 10, 14,4 por
    partido; Roberto 6,3) pide 24,72 M y con Yamal suma ~8 puntos por
    jornada. Ganarlo costara 27-30 M (Rodri se fue un 22,5 % por encima
    con tres pujando). Hoy nuestra puja maxima es 9,4 M. Pepe gasta cada
    euro en cuanto lo tiene: la ronda, los chollos, el carril, la mejora,
    la rotacion y el motor viejo. Nunca junta para un fichaje grande.

    La hucha aparta dinero para UN jugador (`config/la_hucha.json`) y
    ningun motor que puja lo puede gastar.

LO APARTADO

    lo_apartado = min(max(saldo - TODAS nuestras pujas vivas, 0), objetivo)

    Las pujas cuentan enteras (no el 7 % de la mejora). Crece sola con lo
    que entra (premios, la racha, las ventas) hasta el objetivo.

LA PUERTA ESTRICTA (lo que de verdad la protege)

    Restar lo apartado sin mas no basta: como se recalcula en cada vuelta
    con la caja que hay, cada gasto p baja lo apartado en p y a la vuelta
    siguiente el motor ve lo mismo de libre (el trinquete). Por eso,
    mientras este activa, solo se gasta `libre`:

        libre = saldo - pujas vivas - lo apartado

    calculado con la caja de la foto (0 en cuanto saldo - pujas <= el
    objetivo; negativo en deuda). Lo que no es caja NO paga contra la
    hucha: ni la deuda tolerada de la mejora, ni el 95 % del inventario,
    ni el 92 % de la cartera, ni MAX_SAFE_DEBT, ni el 25 % del valor que
    Biwenger suma a `maximumBid`, ni los cobros de otras parejas. Solo el
    credito LOCAL de la misma accion: la venta emparejada (`cabe(...,
    credito=...)`). Un cambio que se paga solo (neto <= 0) pasa siempre.

    El `maximumBid` que ven los motores que gastan baja tambien lo
    apartado (`maximo_para_gastar`).

LA EXENCION

    Solo la orden del gestor, en el `fichar` del jugador de la hucha
    (`player_id`): ahi se sigue el camino de siempre, con el saldo real,
    el `maximumBid` real y el reloj de siempre. La hucha nunca frena ese
    fichaje. Nadie mas tiene exencion (el motor viejo y el BUY V10 no
    fichan a Raphinha).

EL DIA DE RAPHINHA (`en_juego`, revision del 02/11)

    La hucha guarda caja (saldo - pujas), pero la puja por Raphinha la
    limita `maximumBid` (saldo + 25 % del valor - pujas vivas), y ahi
    cuenta ENTERA cualquier otra puja viva, tambien la de un cambio que
    se paga solo: con 16 M apartados y una puja de 8 M de un cambio
    viva, `maximumBid` baja a 24,9 M y la orden ya no puede pujar 29 M.
    Asi que, mientras el jugador de la hucha esta en el mercado del
    Computer de la foto o tenemos puja viva por el, la hucha esta
    `en_juego`: nadie mas puja (ni lo que se paga solo: `cabe` dice que
    no a todo lo que no es la exencion) y lo libre no pasa de 0. La
    mejora solo adopta lo que ya es nuestro (no puja). Su deficit (vende
    caro por barato) tambien espera mientras la orden aun no ha pujado
    por el: sus ventas llegan despues del reset, tarde para Raphinha, y
    su puja bajaria la puja maxima; con nuestra puja viva por el
    (`su_puja_viva`), el deficit vuelve a lo de siempre. Nada de esto
    vende ni publica. Ganado, CUMPLIDA; perdido, deja de estar en el
    mercado y la hucha vuelve a lo de siempre.

LO QUE NO TOCA (los que venden o miran la solvencia)

    El cierre de la jornada, el modo deficit de la mejora, el ultimo
    recurso de la orden, el rojo de la rotacion, la solvencia del motor
    viejo, el position manager, el panel y los libros del dinero siguen
    viendo el saldo de verdad. La hucha es dinero de verdad que paga la
    jornada: nunca provoca una venta, una publicacion ni un modo deficit.
    `leer_la_foto` no se toca.

CUANDO VALE (`vigente`)

    APAGADA     sin el interruptor (no se lee ni el fichero)
    SIN_HUCHA   sin `config/la_hucha.json` o ilegible
    MAL_ESCRITA player_id u objetivo no son enteros > 0, o `desde` /
                `caduca` sin fecha con zona
    AUN_NO      antes de `desde`
    CADUCADA    desde `caduca`
    CUMPLIDA    el jugador ya esta en nuestra plantilla (se apaga sola)

    En cualquiera de esos casos, nadie ve nada distinto de main.

EL INTERRUPTOR

    `BORDALAS_LA_HUCHA`, que se lee en UN sitio: `activa()`, al llamarse.
    Vale "1", "true", "si" o "yes"; cualquier otra cosa es apagada (en
    el YAML, "1": con "on" o "sí" el paso 0 lo daria por encendido y
    produccion correria apagada). Nace APAGADO. Apagado, todas las
    funciones devuelven lo neutro sin leer el fichero, y quien la usa no
    entra en su rama nueva: byte a byte lo de main. Este modulo no hace
    nada al importarse. Nunca lanza.
"""

from __future__ import annotations

import json
import os

from datetime import datetime, timezone
from pathlib import Path


ENV = "BORDALAS_LA_HUCHA"

RUTA = Path("config") / "la_hucha.json"

APAGADA = "APAGADA"
SIN_HUCHA = "SIN_HUCHA"
MAL_ESCRITA = "MAL_ESCRITA"
AUN_NO = "AUN_NO"
CADUCADA = "CADUCADA"
CUMPLIDA = "CUMPLIDA"

# La guardia que se apunta en las acciones que la hucha frena.
GUARDIA = "LA_HUCHA"


def activa() -> bool:
    """El interruptor. Nunca lanza."""
    try:
        return str(os.environ.get(ENV, "")).strip().lower() in {"1", "true", "si", "yes"}
    except Exception:                               # noqa: BLE001
        return False


def _int(valor, defecto=None):
    try:
        if valor is None or isinstance(valor, bool):
            return defecto
        return int(valor)
    except (TypeError, ValueError, OverflowError):
        return defecto


def _con_zona(texto) -> datetime | None:
    """La fecha, solo si trae zona. Sin zona no se sabe cuando es."""
    try:
        d = datetime.fromisoformat(str(texto))
        return d if d.tzinfo is not None else None
    except (TypeError, ValueError):
        return None


def _utc(ahora) -> datetime:
    if not isinstance(ahora, datetime):
        return datetime.now(timezone.utc)
    return ahora if ahora.tzinfo is not None else ahora.replace(tzinfo=timezone.utc)


def leer(ruta: Path | str | None = None) -> dict | None:
    """La hucha escrita por el gestor. None si no hay o no se lee."""
    try:
        datos = json.loads(Path(RUTA if ruta is None else ruta).read_text(encoding="utf-8"))
        return datos if isinstance(datos, dict) else None
    except Exception:                               # noqa: BLE001
        return None


def vigente(cfg, ahora, plantilla=None) -> str | None:
    """None si la hucha vale ahora. Si no, el motivo. `plantilla` None:
    no se sabe y no se mira si ya es nuestro. Nunca lanza."""
    try:
        if not isinstance(cfg, dict):
            return SIN_HUCHA
        pid, objetivo = _int(cfg.get("player_id")), _int(cfg.get("objetivo"))
        desde, caduca = _con_zona(cfg.get("desde")), _con_zona(cfg.get("caduca"))
        if not pid or pid <= 0 or not objetivo or objetivo <= 0 or desde is None or caduca is None:
            return MAL_ESCRITA
        ahora = _utc(ahora)
        if ahora < desde:
            return AUN_NO
        if ahora >= caduca:
            return CADUCADA
    except Exception:                               # noqa: BLE001
        return MAL_ESCRITA
    try:
        if plantilla is not None and pid in {_int(x) for x in plantilla}:
            return CUMPLIDA
    except Exception:                               # noqa: BLE001
        pass                                        # sin saber la plantilla, no se mira
    return None


def _suma_de_pujas(pujas) -> int:
    """Un entero, un {jugador: importe} o un {jugador: {"amount"}}."""
    if isinstance(pujas, dict):
        total = 0
        for v in pujas.values():
            total += (_int(v.get("amount"), 0) if isinstance(v, dict) else _int(v, 0)) or 0
        return total
    return _int(pujas, 0) or 0


def lo_apartado(saldo, pujas_vivas, objetivo) -> int:
    """min(max(saldo - pujas vivas, 0), objetivo). 0 sin saldo o sin
    objetivo. Pura, nunca lanza."""
    try:
        saldo, objetivo = _int(saldo), _int(objetivo, 0) or 0
        if saldo is None or objetivo <= 0:
            return 0
        return min(max(saldo - _suma_de_pujas(pujas_vivas), 0), objetivo)
    except Exception:                               # noqa: BLE001
        return 0


def _esta_en(player_id, *dicts) -> bool:
    """El jugador esta en alguno de los dicts ({jugador: ...}): el
    mercado del Computer o nuestras pujas vivas. Nunca lanza."""
    try:
        pid = _int(player_id)
        if pid is None:
            return False
        for d in dicts:
            if isinstance(d, dict) and pid in {_int(k) for k in d}:
                return True
    except Exception:                               # noqa: BLE001
        pass
    return False


def _neutra(motivo, encendida, cfg=None) -> dict:
    h = {"activa": False, "encendida": encendida, "motivo": motivo, "apartado": 0}
    if isinstance(cfg, dict) and motivo not in (APAGADA, SIN_HUCHA, MAL_ESCRITA):
        h.update({"player_id": _int(cfg.get("player_id")), "nombre": cfg.get("nombre"),
                  "objetivo": _int(cfg.get("objetivo"))})
    return h


def _las_cuentas(h: dict) -> dict:
    """Rehace apartado, libre y maximo_para_gastar con saldo, pujas y
    maximo de `h`. En juego (el dia de Raphinha), lo libre no pasa de 0."""
    h = _las_cuentas_de_la_caja(h)
    if h.get("en_juego") and _int(h.get("libre")) is not None:
        h["libre"] = min(_int(h.get("libre")), 0)
    return h


def _las_cuentas_de_la_caja(h: dict) -> dict:
    saldo, pujas, maximo = h.get("saldo"), _int(h.get("pujas"), 0) or 0, h.get("maximo_de_puja")
    if _int(saldo) is None or h.get("pujas_sin_saber"):
        # Sin saldo, o sin saber cuales son nuestras pujas: nadie gasta
        # contra la hucha (libre None; solo pasa lo que se paga solo).
        apartado = lo_apartado(saldo, pujas, h.get("objetivo")) if _int(saldo) is not None else 0
        return {**h, "apartado": apartado, "libre": None,
                "maximo_para_gastar": None if _int(maximo) is None else _int(maximo) - apartado}
    apartado = lo_apartado(saldo, pujas, h.get("objetivo"))
    return {**h, "apartado": apartado, "libre": _int(saldo) - pujas - apartado,
            "maximo_para_gastar": None if _int(maximo) is None else _int(maximo) - apartado}


def de_la_foto(foto=None, *, saldo=None, pujas=None, maximo_de_puja=None, plantilla=None,
               ahora=None, ruta=None, cfg=None, pujas_sin_saber=False) -> dict:
    """
    La hucha con la caja de una foto (la de `leer_la_foto`: `saldo`,
    `nuestras_pujas`, `maximo_de_puja`, `plantilla`). Lo que se pase
    aparte manda sobre la foto (`pujas`: un entero o un dict).

        {activa, encendida, motivo, player_id, nombre, objetivo, saldo,
         pujas, maximo_de_puja, su_puja_viva, en_juego, apartado, libre,
         maximo_para_gastar}

    `su_puja_viva`: tenemos puja viva por su jugador (en `pujas` si es
    un dict; si no, en las de la foto); `en_juego`: eso, o esta en
    `mercado` (el del Computer de la foto). El dia de Raphinha.

    Apagada: {activa: False, motivo: APAGADA, apartado: 0}, sin leer el
    fichero. No vigente: lo mismo con su motivo. Nunca lanza.
    """
    if not activa():
        return _neutra(APAGADA, False)
    cfg = leer(ruta) if cfg is None else cfg
    f = foto if isinstance(foto, dict) else {}
    plantilla = f.get("plantilla") if plantilla is None else plantilla
    motivo = vigente(cfg, ahora, plantilla)
    if motivo:
        return _neutra(motivo, True, cfg)
    try:
        h = {
            "activa": True, "encendida": True, "motivo": None,
            "player_id": _int(cfg.get("player_id")), "nombre": cfg.get("nombre"),
            "objetivo": _int(cfg.get("objetivo")),
            "saldo": _int(f.get("saldo") if saldo is None else saldo),
            "pujas": _suma_de_pujas(f.get("nuestras_pujas") if pujas is None else pujas),
            "maximo_de_puja": _int(f.get("maximo_de_puja") if maximo_de_puja is None
                                   else maximo_de_puja),
        }
        h["su_puja_viva"] = _esta_en(h["player_id"], pujas if isinstance(pujas, dict)
                                     else f.get("nuestras_pujas"))
        h["en_juego"] = h["su_puja_viva"] or _esta_en(h["player_id"], f.get("mercado"))
        if pujas_sin_saber:
            h["pujas_sin_saber"] = True
        return _las_cuentas(h)
    except Exception as error:                      # noqa: BLE001
        # Vale y no se pueden hacer las cuentas: nadie gasta contra ella.
        return {"activa": True, "encendida": True, "motivo": f"ERROR: {type(error).__name__}",
                "player_id": _int(cfg.get("player_id")), "nombre": cfg.get("nombre"),
                "objetivo": _int(cfg.get("objetivo")), "apartado": 0, "libre": None,
                "maximo_para_gastar": None}


def de_la_snapshot(snapshot, *, ahora=None, ruta=None) -> dict:
    """La hucha de una foto de Biwenger (`refresh_snapshot`). Sin saber
    quien somos no se reconocen nuestras pujas; con una foto que no se
    lee, tampoco el saldo: si la hucha vale, libre None (nadie gasta
    contra ella); si no vale, lo neutro. Nunca lanza."""
    if not activa():
        return _neutra(APAGADA, False)
    try:
        from src.actions.la_orden_del_gestor import _pid, leer_la_foto

        s = snapshot if isinstance(snapshot, dict) else {}
        yo = _pid((s.get("league") or {}).get("user"))
        foto = leer_la_foto(s, yo)
        ofertas = (s.get("market") or {}).get("offers")
        sin_saber = yo is None or not isinstance(ofertas, list)
    except Exception:                               # noqa: BLE001
        foto, sin_saber = {}, True
    return de_la_foto(foto, ahora=ahora, ruta=ruta, pujas_sin_saber=sin_saber)


def esta_activa(h) -> bool:
    return isinstance(h, dict) and h.get("activa") is True


def lo_libre(h) -> int:
    """Lo que se puede gastar contra la hucha (0 si no se sabe)."""
    if not esta_activa(h):
        return 0
    return _int(h.get("libre"), 0) or 0


def mas_lo_pujado(h, importe):
    """La hucha con `importe` mas en pujas vivas (lo pujado en la vuelta
    que la foto aun no trae): lo que daria una foto nueva. `maximumBid`
    baja lo mismo. Apagada o sin importe, la misma. Nunca lanza."""
    try:
        importe = _int(importe, 0) or 0
        if not esta_activa(h) or importe == 0 or "pujas" not in h:
            return h
        maximo = _int(h.get("maximo_de_puja"))
        return _las_cuentas({
            **h, "pujas": (_int(h.get("pujas"), 0) or 0) + importe,
            "maximo_de_puja": None if maximo is None else maximo - importe,
            "pujado_en_la_vuelta": (_int(h.get("pujado_en_la_vuelta"), 0) or 0) + importe,
        })
    except Exception:                               # noqa: BLE001
        return h


def cabe(h, importe, *, player_id=None, sustituye=0, credito=0, ya=0) -> bool:
    """
    La puerta estricta. True si la hucha no esta activa, si es el jugador
    de la hucha (la exencion: solo la orden la pide), o, fuera del dia de
    Raphinha (`en_juego`: ese dia, False a todo lo demas), si:

        neto = importe - sustituye - credito
        neto <= 0 (se paga solo)  o  libre - ya - neto >= 0

    `sustituye`, nuestra puja viva por ese jugador (vuelve al pujar);
    `credito`, la venta emparejada de ESTA accion; `ya`, lo que esta
    vuelta ya ha sacado de lo libre. Sin saber lo libre, solo lo que se
    paga solo. Nunca lanza (si algo falla, no cabe).
    """
    try:
        if not esta_activa(h):
            return True
        if player_id is not None and _int(player_id) == _int(h.get("player_id")):
            return True
        if h.get("en_juego"):
            return False
        neto = (_int(importe, 0) or 0) - (_int(sustituye, 0) or 0) - (_int(credito, 0) or 0)
        if neto <= 0:
            return True
        libre = _int(h.get("libre"))
        if libre is None:
            return False
        return libre - (_int(ya, 0) or 0) - neto >= 0
    except Exception:                               # noqa: BLE001
        return False


def _por_que(importe, h) -> str:
    h = h if isinstance(h, dict) else {}
    para = h.get("nombre") or h.get("player_id")
    if h.get("en_juego"):
        return (f"la puja de {importe} bajaria la puja maxima el dia de {para}: "
                f"esta en el mercado (o con nuestra puja viva) y solo puja la orden "
                f"por el")
    return (f"la puja de {importe} tocaria la hucha de {para} "
            f"(apartado {h.get('apartado')}, libre {h.get('libre')})")


def la_nada(accion: dict, h) -> dict:
    """La PUJAR que la hucha frena, como NADA con su guardia."""
    return {
        "accion": "NADA", "player_id": accion.get("player_id"),
        "nombre": accion.get("nombre"), "guardia": GUARDIA,
        "importe": accion.get("importe"),
        "motivo": _por_que(accion.get("importe"), h),
    }


def filtrar_pujas(acciones, h, credito_de=None, ya=0) -> list:
    """Las acciones con cada PUJAR que no cabe cambiada por NADA (guardia
    LA_HUCHA), en orden y acumulando lo que cada una saca de lo libre.
    `credito_de(accion)`, el credito local de cada una (por defecto 0).
    Apagada, las mismas. Nunca lanza."""
    if not esta_activa(h):
        return acciones
    salida, gastado = [], _int(ya, 0) or 0
    for a in acciones or []:
        if not isinstance(a, dict) or a.get("accion") != "PUJAR":
            salida.append(a)
            continue
        try:
            sustituye = _int((a.get("sustituye") or {}).get("amount"), 0) or 0
            credito = (_int(credito_de(a), 0) or 0) if credito_de else 0
        except Exception:                           # noqa: BLE001
            sustituye, credito = 0, 0
        if cabe(h, a.get("importe"), sustituye=sustituye, credito=credito, ya=gastado):
            gastado += max(0, (_int(a.get("importe"), 0) or 0) - sustituye - credito)
            salida.append(a)
        else:
            salida.append(la_nada(a, h))
    return salida


# ============================================================
# LO PUJADO EN LA VUELTA (para la vuelta de v10, que lleva la cuenta)
# ============================================================

def _quiza_entro(x) -> bool:
    """Una PUJAR de `ejecutar` que Biwenger pudo tomar: con exito, o
    mandada sin saber si entro, o que reviento al mandarse (un timeout
    despues del POST). Solo `exito` False (o ni se mando ni fallo: el
    ensayo) no cuenta. Como lo cuenta el carril: mejor de mas."""
    exito = x.get("exito")
    if exito is False:
        return False
    return bool(exito) or bool(x.get("enviada")) or bool(x.get("error"))


def lo_pujado_en(hechas) -> int:
    """Lo que suben nuestras pujas vivas las `hechas` de la orden, los
    chollos o la ronda: cada PUJAR que pudo entrar (`_quiza_entro`),
    menos la que sustituye."""
    total = 0
    try:
        for x in hechas or []:
            if isinstance(x, dict) and x.get("accion") == "PUJAR" and _quiza_entro(x):
                total += max(0, (_int(x.get("importe"), 0) or 0)
                             - (_int((x.get("sustituye") or {}).get("amount"), 0) or 0))
    except Exception:                               # noqa: BLE001
        pass
    return total


def lo_pujado_por_el_carril(carril) -> int:
    """Las pujas del carril que se mandaron (como las cuenta el cierre)."""
    total = 0
    try:
        for b in (carril or {}).get("bids") or []:
            if isinstance(b, dict) and b.get("sent") and b.get("success") is not False:
                total += _int(b.get("amount"), 0) or 0
    except Exception:                               # noqa: BLE001
        pass
    return total


def lo_pujado_por_el_buy(buy) -> int:
    """La puja del BUY V10, si se mando."""
    try:
        if not (buy or {}).get("writes_biwenger"):
            return 0
        ejecucion = (buy or {}).get("execution") or {}
        if not ejecucion.get("sent") or ejecucion.get("success") is False:
            return 0
        return _int(ejecucion.get("amount"), 0) or 0
    except Exception:                               # noqa: BLE001
        return 0


# ============================================================
# LAS PUERTAS DE LOS QUE NO LLEVAN `decidir`
# ============================================================

def frena_la_especulacion(snapshot, player_id, importe, *, ahora=None, ruta=None):
    """
    Para el motor viejo (el ejecutor y el orquestador): None si la puja
    cabe (o la hucha no esta activa); si no, {motivo, importe, hucha}.
    Sin exencion y sin credito: es una compra sin venta emparejada. Su
    puja viva por el mismo jugador vuelve al sustituirla. Nunca lanza.
    """
    if not activa():
        return None
    try:
        h = de_la_snapshot(snapshot, ahora=ahora, ruta=ruta)
        if not esta_activa(h):
            return None
        from src.actions.la_orden_del_gestor import _pid, leer_la_foto

        s = snapshot if isinstance(snapshot, dict) else {}
        foto = leer_la_foto(s, _pid((s.get("league") or {}).get("user")))
        ya = _int(((foto.get("nuestras_pujas") or {}).get(_int(player_id)) or {}).get("amount"), 0)
        if cabe(h, importe, sustituye=ya or 0):
            return None
        return {"motivo": GUARDIA, "importe": _int(importe), "hucha": el_resumen(h)}
    except Exception as error:                      # noqa: BLE001
        return {"motivo": GUARDIA, "importe": _int(importe),
                "hucha": {"error": f"{type(error).__name__}: {error}"}}


def la_puja_toca_la_hucha(market, yo, player_id, importe, *, ahora=None, ruta=None):
    """
    Para `execute_bid` (BUY V10 y las CLI), con el mercado fresco que ya
    tiene: None si cabe o la hucha no esta activa; si no, el motivo en
    una frase. Sin la plantilla no se mira CUMPLIDA. Nunca lanza.
    """
    if not activa():
        return None
    try:
        snapshot = {"market": market if isinstance(market, dict) else {},
                    "league": {"user": None if yo is None else {"id": yo}}}
        frenada = frena_la_especulacion(snapshot, player_id, importe, ahora=ahora, ruta=ruta)
        if frenada is None:
            return None
        return f"La hucha: {_por_que(importe, frenada.get('hucha'))}."
    except Exception as error:                      # noqa: BLE001
        return f"La hucha no se pudo mirar ({type(error).__name__}): no se puja."


def la_cesta_con_la_hucha(plan, snapshot, *, ahora=None, ruta=None):
    """
    La cesta del reset (`la_subasta.plan_desde_el_estado`, hoy cerrada
    con `BORDALAS_SIN_SUBASTA`): con la hucha activa, puja entera solo si
    TODAS sus pujas caben en lo libre; si no, ninguna (LA_HUCHA). Apagada
    o sin pujas, el mismo plan. Nunca lanza.
    """
    if not activa():
        return plan
    try:
        if not isinstance(plan, dict) or not plan.get("bids"):
            return plan
        h = de_la_snapshot(snapshot, ahora=ahora, ruta=ruta)
        if not esta_activa(h):
            return plan
        total = sum(_int((b or {}).get("bid"), 0) or 0 for b in plan.get("bids") or [])
        if cabe(h, total):
            return plan
        return {
            **plan, "execute": False, "bids": [], "committed": 0, "expected": 0,
            "all_won": 0, "slots_used": 0, "worst_case": None, "blocked_by": GUARDIA,
            "reason": (f"La cesta pujaria {total} y lo libre de la hucha es "
                       f"{h.get('libre')}"
                       + (" (el dia de su jugador, solo puja la orden por el)"
                          if h.get("en_juego") else "") + ": no se puja."),
            "hucha": el_resumen(h),
        }
    except Exception:                               # noqa: BLE001
        return plan


# ============================================================
# EL PANEL
# ============================================================

def el_resumen(h) -> dict:
    """Lo que se ensena de una hucha."""
    h = h if isinstance(h, dict) else {}
    claves = ("activa", "motivo", "player_id", "nombre", "objetivo", "saldo", "pujas",
              "en_juego", "su_puja_viva", "apartado", "libre", "maximo_de_puja",
              "maximo_para_gastar", "pujado_en_la_vuelta")
    return {k: h.get(k) for k in claves if k in h}


def el_bloque(h, mercado=None) -> dict:
    """
    El bloque `hucha` del estado de la vuelta, solo con el interruptor
    puesto (apagada: {} y el estado es el de siempre). `mercado`, el del
    Computer de la foto ({player_id: precio}). Nunca lanza.
    """
    try:
        if not isinstance(h, dict) or not h.get("encendida"):
            return {}
        objetivo = _int(h.get("objetivo"))
        apartado = _int(h.get("apartado"), 0) or 0
        maximo = _int(h.get("maximo_de_puja"))
        pid = _int(h.get("player_id"))
        return {"hucha": {
            "activa": bool(h.get("activa")),
            "motivo": h.get("motivo"),
            "para": h.get("nombre"),
            "player_id": pid,
            "objetivo": objetivo,
            "apartado": apartado,
            "falta": None if objetivo is None else max(objetivo - apartado, 0),
            "libre": h.get("libre"),
            "en_el_mercado_hoy": (None if mercado is None or pid is None
                                  else pid in {_int(k) for k in mercado}),
            "en_juego": bool(h.get("en_juego")),
            "nuestra_puja_maxima_real": maximo,
            "nuestra_puja_maxima_para_los_demas": h.get("maximo_para_gastar"),
            "pujado_en_la_vuelta": _int(h.get("pujado_en_la_vuelta"), 0) or 0,
        }}
    except Exception:                               # noqa: BLE001
        return {}
