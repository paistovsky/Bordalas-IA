"""
LA SUBASTA EN EL COLCHON (01/11/2026)

POR QUE EXISTE

    El 31/10 a las 04:48 la cesta del reset del motor viejo
    (`la_subasta.plan_del_reset`, la que puja `_pujar_en_el_reset` en las
    vueltas de las 04:45 y 04:50) pujo 2.025.051 por Dani Lorenzo con el
    saldo en 1.299.975 y 929.800 en pujas vivas de la ronda (Macia
    709.900, Angel Ortiz 219.900). Se gano y dejo el saldo en -944.976.

        - el freno de la solvencia dijo SIN_DEUDA: no ve la cesta ni las
          pujas vivas;
        - el tope es min(presupuesto, 3 x saldo);
        - no mira lo cerca que esta la jornada;
        - y el colchon de la casa (`BORDALAS_UN_SOLO_COLCHON`,
          `la_ronda_de_la_manana.cabe_en_el_colchon`) solo lo mira el
          ejecutor del motor viejo, no esta cesta.

    Repetida: el colchon era 1.179.775 contra 2.025.051. No cabia. Y Dani
    subia +10.000 sobre 2.020.000, por debajo de la subida minima de su
    tramo (22.220). Su historial desde el 22/09: 2 pujas, unos -305.000;
    solo el cubo de menos de 1,5 M gano dinero (bitacora del 31/10 22:30).

LA REGLA

    Sobre las pujas que ya eligio la cesta (despues del reparto, el tope
    del primer dia, el peor caso y la orden del gestor), y en este orden:

    1. EL RELOJ. Si faltan menos de `HORAS_SIN_COMPRAR` (40 h, la de la
       ronda: lo comprado tiene que recibir al menos una oferta del
       Computer antes de la jornada) o no se sabe cuanto falta, no se
       puja: CERCA_DE_LA_JORNADA. Las horas son las de
       `horas_a_la_jornada`, la misma cuenta que la ronda.
    2. SUBE DE VERDAD. Solo las que suben hoy al menos la subida minima
       de su tramo (`la_mejora_del_once.sube_de_verdad`, la vara de la
       mejora y del motor viejo): `price_increment` > 0 no basta. Si no
       queda ninguna: NO_SUBE_DE_VERDAD.
    3. EL COLCHON. En el orden de la cesta, cada puja tiene que caber en
       el colchon de la casa CONTANDO las que ya caben delante
       (`cabe_en_el_colchon(foto, jugador, acumulado + puja)`): saldo
       menos todas las pujas vivas mas el 92 % de lo de la cartera. La
       que no cabe se queda fuera y la siguiente se mira igual. Sin
       colchon (sin saldo en la foto) no se puja a ciegas. Si no queda
       ninguna: SIN_COLCHON.
    4. Las cuentas del plan (`committed`, `expected`, `all_won`,
       `slots_used`, `worst_case`, `execute`, `reason`) se rehacen con lo
       que queda. Lo que se ha mirado va en `en_el_colchon`.

    Sin pujas que mirar (la cesta ya estaba cerrada por otra puerta), el
    plan sale tal cual.

EL INTERRUPTOR

    `BORDALAS_LA_SUBASTA_EN_EL_COLCHON`, que se lee en UN sitio:
    `la_subasta._en_el_colchon`, desde `plan_desde_el_estado`, por donde
    pasan el ciclo y la pantalla. Este modulo no lo lee. Nace APAGADO, y
    apagado no se llama.

QUE NO HACE

    No toca la ronda, la mejora, los chollos, el carril ni el tablero de
    fichajes: cada uno tiene lo suyo. Tampoco la sombra
    (`la_sombra_de_la_puja`) ni la lista de la noche, que llaman a
    `plan_del_reset` directamente para ver lo que haria la cesta sin
    candados. No sube ninguna puja: solo quita.

    Importarlo no hace nada. Lee la foto que se le pasa, el calendario y
    el libro de la ronda (los de la casa si no se pasan). Nunca lanza: si
    algo falla, no se puja y se dice por que.
"""

from __future__ import annotations


CERCA_DE_LA_JORNADA = "CERCA_DE_LA_JORNADA"
NO_SUBE_DE_VERDAD = "NO_SUBE_DE_VERDAD"
SIN_COLCHON = "SIN_COLCHON"


def _cerrado(plan: dict, motivo: str, reason: str, detalle: dict, **extra) -> dict:
    """El plan sin ninguna puja, con su motivo. Nunca lanza."""

    return {
        **plan,
        "execute": False,
        "bids": [],
        "committed": 0,
        "expected": 0,
        "all_won": 0,
        "slots_used": 0,
        "worst_case": None,
        **extra,
        "blocked_by": motivo,
        "reason": reason,
        "en_el_colchon": detalle,
    }


def en_el_colchon(
    plan: dict | None,
    snapshot: dict | None,
    plantilla: list | None = None,
    ahora=None,
    calendario=None,
    libro_ruta=None,
) -> dict:
    """
    El plan de la cesta, con solo las pujas que pasan el reloj, suben de
    verdad y caben en el colchon de la casa. Ver la cabecera.

        plan        la salida de `plan_del_reset` (ya con la orden)
        snapshot    la foto de Biwenger de la vuelta: saldo y pujas vivas
        plantilla   la de `lectura_del_estado`, para el peor caso
        ahora       UTC; `None` es el reloj de verdad
        calendario  ruta o dict; `None` es el de la casa
        libro_ruta  el libro de la ronda; `None` es el de la casa

    Nunca lanza.
    """

    base = plan if isinstance(plan, dict) else {}

    detalle = {
        "puesta": True,
        "horas_a_la_jornada": None,
        "horas_minimas": None,
        "colchon": None,
        "comprometido": 0,
        "caben": [],
        "fuera": [],
        "no_suben": [],
    }

    try:
        from datetime import datetime, timezone

        from src.actions.la_mejora_del_once import sube_de_verdad
        from src.actions.la_ronda_de_la_manana import (
            HORAS_SIN_COMPRAR,
            cabe_en_el_colchon,
            horas_a_la_jornada,
            la_subida_minima,
        )
        from src.analysis.la_subasta import (
            _euros,
            peor_caso,
            safe_float,
            safe_int,
        )

        pujas = base.get("bids")

        if not pujas:
            return base

        pujas = (
            [b for b in pujas if isinstance(b, dict)]
            if isinstance(pujas, list)
            else []
        )

        if not pujas:
            return _cerrado(
                base, SIN_COLCHON,
                "Las pujas de la cesta no se pueden leer: no se puja.",
                detalle,
            )

        # 1. EL RELOJ
        minimas = float(HORAS_SIN_COMPRAR)
        detalle["horas_minimas"] = minimas

        horas = horas_a_la_jornada(
            ahora or datetime.now(timezone.utc), calendario
        )

        if horas is None:
            return _cerrado(
                base, CERCA_DE_LA_JORNADA,
                (
                    "No se sabe cuanto falta para la jornada (sin "
                    "calendario): la cesta no puja a ciegas."
                ),
                detalle,
            )

        horas = float(horas)
        detalle["horas_a_la_jornada"] = horas

        if horas < minimas:
            return _cerrado(
                base, CERCA_DE_LA_JORNADA,
                (
                    f"Faltan {f'{horas:.1f}'.replace('.', ',')} h para la "
                    f"jornada y la cesta no "
                    f"compra a menos de {minimas:.0f} h: lo que se gane en "
                    f"el reset no llegaria a recibir la oferta del Computer "
                    f"antes del cierre. No se puja."
                ),
                detalle,
            )

        # 2. SUBE DE VERDAD
        siguen, no_suben = [], []

        for puja in pujas:
            precio = safe_int(puja.get("market_price"))
            sube = puja.get("price_increment")

            if sube_de_verdad({"price": precio, "price_increment": sube}):
                siguen.append(puja)
                continue

            no_suben.append({
                "id": safe_int(puja.get("id")),
                "name": puja.get("name"),
                "market_price": precio,
                "price_increment": sube,
                "minima": la_subida_minima(precio),
            })

        detalle["no_suben"] = no_suben

        texto_no_suben = "; ".join(
            f"{f['name']} "
            f"{'+' if safe_int(f['price_increment']) > 0 else ''}"
            f"{_euros(f['price_increment'])} sobre "
            f"{_euros(f['market_price'])} (pide {_euros(f['minima'])})"
            for f in no_suben
        )

        if not siguen:
            return _cerrado(
                base, NO_SUBE_DE_VERDAD,
                (
                    f"Ninguna sube de verdad hoy (la subida minima de su "
                    f"tramo, la vara de la mejora): {texto_no_suben}. No "
                    f"se puja."
                ),
                detalle,
                dropped_by_no_sube_de_verdad=len(no_suben),
            )

        # 3. EL COLCHON, ACUMULADO
        acumulado = 0
        colchon = None
        caben, fuera = [], []

        for puja in siguen:
            importe = safe_int(puja.get("bid"))

            mira = cabe_en_el_colchon(
                snapshot, puja.get("id"), acumulado + importe, libro_ruta
            )

            if not isinstance(mira, dict) or mira.get("colchon") is None:
                return _cerrado(
                    base, SIN_COLCHON,
                    (
                        "No se puede calcular el colchon de la casa (sin "
                        "saldo en la foto): la cesta no puja a ciegas."
                    ),
                    detalle,
                    dropped_by_no_sube_de_verdad=len(no_suben),
                )

            if colchon is None:
                colchon = int(mira["colchon"])

            if importe > 0 and mira.get("cabe") is True:
                caben.append(puja)
                acumulado += importe
                continue

            fuera.append({
                "id": safe_int(puja.get("id")),
                "name": puja.get("name"),
                "bid": importe,
                "acumulado": acumulado,
                "colchon": int(mira["colchon"]),
            })

        detalle.update({
            "colchon": colchon,
            "comprometido": acumulado,
            "caben": [safe_int(b.get("id")) for b in caben],
            "fuera": fuera,
        })

        texto_fuera = "; ".join(
            f"{f['name']} {_euros(f['bid'])}"
            + (f" (con {_euros(f['acumulado'])} delante)" if f["acumulado"] else "")
            for f in fuera
        )

        if not caben:
            return _cerrado(
                base, SIN_COLCHON,
                (
                    f"Ninguna puja cabe en el colchon de la casa "
                    f"({_euros(colchon)} EUR: saldo menos todas las pujas "
                    f"vivas mas el 92 % de lo de la cartera): "
                    f"{texto_fuera}. No se puja."
                ),
                detalle,
                dropped_by_colchon=len(fuera),
                dropped_by_no_sube_de_verdad=len(no_suben),
            )

        # 4. LAS CUENTAS, CON LO QUE QUEDA
        comprometido = sum(safe_int(b.get("bid")) for b in caben)

        esperado = int(
            sum(
                safe_float(b.get("expected_value"))
                * safe_float(b.get("win_odds"), 0.0)
                for b in caben
            )
        )

        si_todas = int(
            sum(safe_float(b.get("expected_value")) for b in caben)
        )

        ventana = base.get("window")
        ventana = ventana.get("reason") if isinstance(ventana, dict) else None

        reason = (
            f"{len(caben)} puja(s) por {_euros(comprometido)} EUR, "
            f"esperado {_euros(esperado)} EUR; caben en el colchon de la "
            f"casa ({_euros(colchon)} EUR)."
            + (f" No caben: {texto_fuera}." if fuera else "")
            + (f" No suben de verdad: {texto_no_suben}." if no_suben else "")
            + (f" {ventana}" if ventana else "")
            + (
                " NO se ejecuta: falta el modo en vivo."
                if base.get("blocked_by") == "SIN_LIVE"
                else ""
            )
        )

        return {
            **base,
            "execute": bool(base.get("execute")) and bool(caben),
            "bids": caben,
            "committed": comprometido,
            "expected": esperado,
            "all_won": si_todas,
            "slots_used": len(caben),
            "worst_case": peor_caso({"elegidos": caben}, plantilla),
            "dropped_by_colchon": len(fuera),
            "dropped_by_no_sube_de_verdad": len(no_suben),
            "reason": reason,
            "en_el_colchon": detalle,
        }

    except Exception as error:                      # noqa: BLE001
        return _cerrado(
            base, SIN_COLCHON,
            (
                f"No se pudo mirar el colchon de la casa: "
                f"{type(error).__name__}: {error}. No se puja."
            ),
            detalle,
        )
