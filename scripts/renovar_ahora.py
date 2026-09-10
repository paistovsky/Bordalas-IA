"""
Renovar a mano, con el dueno delante. Un disparo, deliberado.

QUE ES ESTO Y QUE NO ES

    NO es el camino automatico. `RENOVACION_EN_VIVO` sigue en
    False y la ventana sigue siendo la de siempre. Esto es un
    disparo unico, a mano, autorizado expresamente.

    Y NO abre una via paralela: llama al MISMO
    `renovar_executor.renovar` que usara el ciclo. Lo unico que
    se salta es `que_renovar`, que es quien mira la ventana —
    porque aqui el permiso lo da una persona, no el reloj.

    La ventana no se toca. Es la barandilla, no el obstaculo.

UNA ESCRITURA, NO DOS. MEDIDO (10/09/2026)

    El dueno avisaba de que en la app no hay boton de renovar:
    hay que quitar del mercado y volver a poner. En la API NO es
    asi, y esta medido sobre las 85 fotos del 11-17/08:

        · QUINCE jugadores fueron re-listados mientras su
          listado anterior seguia VIVO -entre 34,7 h y 43,2 h
          despues del primero-.

        · En las 85 fotos, NI UN SOLO listado duplicado: un
          jugador nunca aparece dos veces en `market.sales`.

        · Jonny: listado 12/08 07:01, luego 15/08 23:31, luego
          17/08 10:12. Siempre UNA entrada, con la fecha
          movida.

    Asi que `POST /market {"type": "sell"}` sobre un jugador ya
    listado REEMPLAZA el listado. No hace falta cancelar, y no
    existe el riesgo de "la segunda escritura falla y el jugador
    se queda fuera del mercado": no hay segunda escritura.

    (Y tampoco existe un metodo para quitar del mercado en todo
    el repositorio: `EXIT_LISTING` es listar, no quitar.)

COMO SE USA

    Ver el plan y NO escribir -es lo que hace sin `--confirmar`-:

        python -m scripts.renovar_ahora --jugadores Dituro

    Escribir de verdad:

        python -m scripts.renovar_ahora --jugadores Dituro \\
            --confirmar

    Varios:

        python -m scripts.renovar_ahora --confirmar \\
            --jugadores "Jutgla,Mangala,Jonny"

    Los nombres se comparan sin acentos ni mayusculas, para que
    "Jutgla" encuentre a "Jutglà".

Y LA OFERTA VIEJA NO MUERE. MEDIDO EN VIVO (10/09/2026)

    Renovar a Dituro dejo su listado nuevo -48 h- Y su oferta
    de 2.439.000 intacta, creada el 09/09 a las 07:08.

    Confirmado por segunda via: Mangala, re-listado por el
    dueno a las 09:04 del 10/09, conserva su oferta del 09/09.

    Asi que renovar no cuesta NADA: no hay que esperar a la
    ventana para hacerlo sin perder liquidez.
"""

from __future__ import annotations

import argparse
import json
import unicodedata

from datetime import datetime, timezone
from pathlib import Path

from src.actions.renovar_executor import renovar
from src.analysis.renovar_ofertas import filas_desde_lo_publicado


ESTADO = (
    Path(__file__).parent.parent / "diagnostico" / "status.json"
)


# Un solo reintento. Si la primera escritura no entra, se repite
# UNA vez y se avisa con nombre y hora. Mas reintentos contra un
# endpoint que ya ha fallado es como se llega a un 429.
REINTENTOS = 1


def euros(valor) -> str:
    try:
        return f"{int(valor or 0):,}".replace(",", ".")
    except (TypeError, ValueError):
        return "?"


def _plano(texto) -> str:
    """Sin acentos y en minusculas, para comparar nombres."""

    return "".join(
        c
        for c in unicodedata.normalize("NFD", str(texto or ""))
        if unicodedata.category(c) != "Mn"
    ).strip().lower()


def _ahora() -> str:
    return datetime.now(timezone.utc).strftime("%H:%M:%S UTC")


def verificar(nombres: list) -> dict:
    """
    Mirar en Biwenger como quedo cada uno.

    TRES PREGUNTAS, LAS DEL ENCARGO

        ¿quedo listado? ¿perdio la oferta vieja? ¿algo a medias?

    "A medias" seria: no listado Y sin oferta. Con una sola
    escritura eso no deberia poder pasar, pero se comprueba
    igual: lo que no se mira es lo que sale mal.
    """

    from src.autopilot import refresh_snapshot

    _, snapshot = refresh_snapshot()

    mercado = snapshot.get("market") or {}

    yo = (
        ((snapshot.get("league") or {}).get("user") or {}).get(
            "id"
        )
    )

    plantilla = {
        _plano(j.get("name")): j.get("id")
        for j in (snapshot.get("my_team") or [])
        if isinstance(j, dict)
    }

    listados = {}

    for venta in (mercado.get("sales") or []):

        if not isinstance(venta, dict):
            continue

        usuario = venta.get("user")

        uid = (
            usuario.get("id")
            if isinstance(usuario, dict)
            else usuario
        )

        if yo is not None and uid != yo:
            continue

        jugador = venta.get("player")

        pid = (
            jugador.get("id")
            if isinstance(jugador, dict)
            else jugador
        )

        listados[pid] = venta

    con_oferta = set()

    for oferta in (mercado.get("offers") or []):

        if not isinstance(oferta, dict):
            continue

        if oferta.get("from") is not None:
            continue

        for pedido in (oferta.get("requestedPlayers") or []):

            con_oferta.add(
                pedido.get("id")
                if isinstance(pedido, dict)
                else pedido
            )

    filas = []

    for nombre in nombres:

        pid = plantilla.get(_plano(nombre))

        venta = listados.get(pid)

        filas.append(
            {
                "name": nombre,
                "id": pid,
                "listado": bool(venta),
                "listado_desde": (
                    datetime.fromtimestamp(
                        venta["date"], timezone.utc
                    ).isoformat()
                    if venta and venta.get("date")
                    else None
                ),
                "precio": (venta or {}).get("price"),
                "tiene_oferta": pid in con_oferta,
                "a_medias": bool(
                    not venta and pid not in con_oferta
                ),
            }
        )

    return {"rows": filas, "snapshot_user": yo}


def main() -> None:

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--jugadores",
        required=True,
        help="Nombres separados por comas.",
    )

    parser.add_argument(
        "--precios",
        default="",
        help=(
            "Precio explicito por jugador: "
            "\"Jonny=2700000,Pablo Duran=480000\". "
            "Re-preciar NO es renovar: lo decide una persona, "
            "por eso hay que escribirlo a mano."
        ),
    )

    parser.add_argument(
        "--confirmar",
        action="store_true",
        help="Sin esto NO se escribe nada.",
    )

    args = parser.parse_args()

    pedidos = [
        n.strip()
        for n in args.jugadores.split(",")
        if n.strip()
    ]

    estado = json.loads(ESTADO.read_text(encoding="utf-8"))

    todas = filas_desde_lo_publicado(
        estado.get("listings"),
        estado.get("offers"),
        estado.get("roster"),
    )

    # LOS PRECIOS QUE MANDA LA PERSONA, si los hay.
    puestos = {}

    for trozo in args.precios.split(","):

        if "=" not in trozo:
            continue

        nombre, valor = trozo.split("=", 1)

        try:
            puestos[_plano(nombre)] = int(valor.strip())

        except (TypeError, ValueError):
            continue

    buscados = {_plano(n) for n in pedidos}

    filas = [f for f in todas if _plano(f["name"]) in buscados]

    for fila in filas:

        nuevo_precio = puestos.get(_plano(fila["name"]))

        if nuevo_precio:
            fila["precio_anterior"] = fila["listed_price"]
            fila["listed_price"] = nuevo_precio

    encontrados = {_plano(f["name"]) for f in filas}

    faltan = buscados - encontrados

    # ------------------------------------------------------
    # LO QUE VA A HACER, ANTES DE HACERLO
    # ------------------------------------------------------

    print()
    print("=" * 74)
    print("RENOVAR A MANO — LO QUE VA A HACER")
    print("=" * 74)
    print(
        f"  Foto de produccion: "
        f"{(estado.get('meta') or {}).get('generated_at')}"
    )
    print(
        "  Una escritura por jugador: POST /market type=sell "
        "(medido: reemplaza, no duplica)"
    )
    print()

    # EL PRECIO PEDIDO NO PUEDE ESTAR POR DEBAJO DEL DE MERCADO
    #
    #     MEDIDO EN VIVO el 10/09: de siete renovaciones, seis
    #     entraron y una -Jonny- volvio con HTTP 400 dos veces.
    #     La unica diferencia: pediamos 2.350.000 por un jugador
    #     que vale 2.370.000. Los otros seis pedian entre
    #     240.000 y 740.000 POR ENCIMA.
    #
    #     Biwenger rechaza listar por debajo del precio de
    #     mercado. Y le pasa solo a los listados viejos: se
    #     publicaron cuando el precio era mas bajo y el mercado
    #     los ha adelantado.
    #
    #     Se avisa ANTES de escribir. Renovar no re-precia: si
    #     hay que subir la peticion, lo decide una persona.
    valor = {
        str(j.get("id")): j.get("price")
        for j in ((estado.get("roster") or {}).get("players") or [])
        if isinstance(j, dict)
    }

    rechazables = []

    for fila in filas:

        vale = valor.get(str(fila.get("id")))

        aviso = ""

        if vale and fila.get("listed_price"):

            if int(fila["listed_price"]) < int(vale):
                aviso = (
                    f"   <-- POR DEBAJO DE MERCADO "
                    f"({euros(vale)}): Biwenger lo rechazara"
                )
                rechazables.append(fila["name"])

        print(
            f"    {str(fila['name'])[:18]:<19} id "
            f"{str(fila['id']):<8} re-lista a "
            f"{euros(fila['listed_price']):>10}"
            f"   conserva oferta de "
            f"{euros(fila['offer_amount']):>10}"
            + aviso
            + (
                f"   [re-preciado desde "
                f"{euros(fila.get('precio_anterior'))}]"
                if fila.get("precio_anterior")
                else ""
            )
        )

    if faltan:
        print()
        for nombre in sorted(faltan):
            print(
                f"    NO ENCONTRADO en la foto: «{nombre}» — no "
                f"se toca."
            )

    if not filas:
        print()
        print("  Nada que hacer.")
        return

    print()

    if rechazables:
        print()
        print(
            f"  AVISO: {', '.join(rechazables)} se pide(n) por "
            f"debajo del precio de mercado y Biwenger devolvera "
            f"400. Hay que subir la peticion, y eso es re-preciar: "
            f"lo decide una persona."
        )

    if not args.confirmar:
        print(
            "  EN SECO: no se ha escrito nada. Repite con "
            "--confirmar para disparar."
        )
        return

    # ------------------------------------------------------
    # EL DISPARO
    # ------------------------------------------------------

    print("=" * 74)
    print(f"ESCRIBIENDO EN BIWENGER — {_ahora()}")
    print("=" * 74)

    resultado = renovar(filas, en_vivo=True)

    print(f"  {resultado.get('reason')}")

    fallidas = list(resultado.get("failed") or [])

    # UN reintento, con nombre y hora.
    for intento in range(REINTENTOS):

        pendientes = [
            f
            for f in filas
            if any(
                _plano(x.get("name")) == _plano(f["name"])
                for x in fallidas
            )
        ]

        if not pendientes:
            break

        print()
        print(
            f"  REINTENTO {intento + 1} a las {_ahora()} para: "
            + ", ".join(str(f["name"]) for f in pendientes)
        )

        otra = renovar(pendientes, en_vivo=True)

        fallidas = list(otra.get("failed") or [])

        print(f"  {otra.get('reason')}")

    if fallidas:
        print()
        print("  " + "!" * 66)
        for fallo in fallidas:
            print(
                f"  SIN RENOVAR: {fallo.get('name')} a las "
                f"{_ahora()} — {fallo.get('error')}"
            )
        print("  " + "!" * 66)

    # ------------------------------------------------------
    # COMO QUEDO, MIRANDO BIWENGER
    # ------------------------------------------------------

    print()
    print("=" * 74)
    print("COMO QUEDO EN BIWENGER")
    print("=" * 74)

    try:
        comprobacion = verificar(
            [f["name"] for f in filas]
        )

        for fila in comprobacion["rows"]:
            estado_txt = (
                "A MEDIAS: ni listado ni con oferta"
                if fila["a_medias"]
                else (
                    "listado"
                    if fila["listado"]
                    else "NO LISTADO"
                )
            )

            print(
                f"    {str(fila['name'])[:18]:<19}"
                f"{estado_txt:<34}"
                f"oferta vieja: "
                f"{'SIGUE' if fila['tiene_oferta'] else 'fuera'}"
                f"   listado desde "
                f"{str(fila['listado_desde'])[11:19]}"
            )

    except Exception as error:                      # noqa: BLE001
        print(
            f"    No se pudo comprobar contra Biwenger: "
            f"{type(error).__name__}: {error}"
        )
        print(
            "    OJO: la escritura puede haber entrado igual. "
            "Mirar a mano."
        )

    print()


if __name__ == "__main__":
    main()
