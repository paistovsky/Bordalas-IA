"""
Por quien y cuanto pujaria Pepe esta noche con la moneda puesta.

LO QUE PIDE EL DUEÑO, CON SUS PALABRAS (22/09/2026)

    «Tengo que saber por quien y cuanto va a pujar Pepe. Si lo
    va a hacer antes del reset, cuando yo duermo, no me entero
    de nada.»

    La ventana del reset son las 04:45. El interruptor de la
    moneda -`BORDALAS_LA_MONEDA_DE_LA_LIGA`- esta construido y
    APAGADO, y no se enciende hasta que se vea esta lista.

    Asi que la lista se calcula CON LA MONEDA PUESTA aunque en
    produccion este quitada. Es una sombra, como
    `libro_en_la_sombra`: apunta lo que se haria, no lo hace.

NO ES UN INTERRUPTOR, Y ESO ES A PROPOSITO

    `libro_en_la_sombra` -el precedente de esta casa- no tiene
    interruptor: se publica siempre, porque calcular y publicar
    no cambia ninguna decision y no gasta un euro.

    Una sombra detras de un interruptor apagado no enseña nada
    la noche que hace falta, que es esta. Y encender un
    interruptor para poder mirar seria exactamente lo que el
    encargo prohibe.

        Esta lista NO decide. Ninguna ruta la lee. Si mañana
        desaparece, lo unico que se pierde es la vista.

NO SE VUELVE A VALORAR NADA

    El valor de un fichaje sale de `xi_upgrade_value`:

        justo  = puntos_de_mas x tarifa
        valor  = int(justo x (1 - margen) x confianza) + recuperado

    La moneda solo cambia `tarifa`. Todo lo demas -margen,
    confianza, calendario, vetos de jerarquia, suelo de
    titularidad- se queda donde estaba.

    Y como la tarifa entra multiplicando, el valor con la otra
    moneda sale de reescalar el que ya esta publicado:

        valor_liga = (valor - recuperado) x 30.000 / tarifa
                     + recuperado

    Eso NO es reimplementar la formula: es despejarla. Quien lo
    comprueba es `test_la_sombra_de_la_moneda_no_escribe`, que
    pone la misma cuenta al lado de `xi_upgrade_value` corrido
    de verdad con el interruptor puesto y exige que den lo
    mismo.

    Si algun dia la formula deja de ser lineal en la tarifa, esa
    guardia se pone roja y esto se queda vacio en vez de
    inventar.

DE MAYOR A MENOR, Y POR QUE

    «Porque es el que mas duele equivocarse.» La puja mas alta
    va la primera.

NO ESCRIBE NADA

    Ni contra Biwenger, ni en los libros, ni en disco. No sale a
    la red y no mira el reloj. Forma fija. Nunca lanza.
"""

from __future__ import annotations


from src.analysis.el_vestuario_libre import POSICIONES        # noqa: E402
from src.analysis.la_moneda_del_fichaje import (              # noqa: E402
    MONEDA_DE_LA_LIGA,
    es_para_quedarse,
)


# LAS DOS VIAS QUE COBRAN EN LA MONEDA DE LA LIGA
#
#     Las dos pasan por `xi_upgrade_value`, que es donde vive la
#     tarifa. Las otras tres -especular, revender al Computer,
#     tener- se le venden al mercado y cobran en la suya.
VIAS_DEL_QUE_SE_QUEDA = ("as_xi", "as_roster_fill")


# Todas las vias que compiten, en el mismo orden en que las monta
# `acquisition_valuation`. No se escribe una lista nueva de vias:
# se nombran las que ya publica la valoracion.
TODAS_LAS_VIAS = (
    "as_xi",
    "as_roster_fill",
    "as_speculation",
    "as_computer_resale",
    "as_hold",
)


def safe_int(value, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def con_la_moneda(via: dict | None) -> dict:
    """
    Lo que valdria ESA via con la moneda de la liga.

    Forma fija:

        value         el valor reescalado
        value_antes   el que esta publicado hoy
        tarifa        la que se aplicaria
        tarifa_antes  la del mercado, la de hoy
        escalado      si se pudo despejar
        reason        por que, siempre

    Nunca lanza. Lo que no se pueda despejar se queda como
    estaba y lo dice: una sombra que inventa no sirve de nada.
    """

    salida = {
        "value": safe_int((via or {}).get("value")),
        "value_antes": safe_int((via or {}).get("value")),
        "tarifa": None,
        "tarifa_antes": None,
        "escalado": False,
        "reason": None,
    }

    try:
        if not via:
            return {**salida, "reason": "Esa via no existe en esta ficha."}

        tarifa = safe_int(via.get("rate_per_point"))

        if tarifa <= 0:
            return {
                **salida,
                "reason": (
                    "Sin `rate_per_point` publicado no se puede "
                    "despejar la tarifa: se deja el valor de hoy."
                ),
            }

        recuperado = safe_int(via.get("recovered_value"))

        antes = safe_int(via.get("value"))

        # Lo que aporta el fichaje, sin el dinero que entra por
        # vender al que sale: eso ultimo no se cobra en puntos.
        por_los_puntos = antes - recuperado

        nuevo = (
            int(por_los_puntos * MONEDA_DE_LA_LIGA / tarifa)
            + recuperado
        )

        return {
            **salida,
            "value": nuevo,
            "tarifa": MONEDA_DE_LA_LIGA,
            "tarifa_antes": tarifa,
            "escalado": True,
            "reason": (
                f"Un punto vale {MONEDA_DE_LA_LIGA:,} EUR -lo que "
                f"paga la liga- y no {tarifa:,} -lo que cobra el "
                f"mercado-: el valor pasa de {antes:,} a "
                f"{nuevo:,} EUR."
            ).replace(",", "."),
        }

    except Exception as error:                      # noqa: BLE001
        return {
            **salida,
            "reason": (
                f"No se pudo reescalar: "
                f"{type(error).__name__}: {error}"
            ),
        }


def la_via_que_ganaria(valoracion: dict | None) -> dict:
    """
    Que via ganaria con la moneda puesta, y con cuanto valor.

    Las cinco vias compiten igual que hoy; lo unico que cambia
    es que las dos del que se queda cobran en la otra moneda.

    Forma fija. Nunca lanza.
    """

    salida = {
        "via": None,
        "intent": None,
        "route": None,
        "value": 0,
        "value_antes": safe_int((valoracion or {}).get("value")),
        "via_antes": (valoracion or {}).get("route"),
        "cambia_de_via": False,
        "moneda": "MERCADO",
        "reason": None,
    }

    try:
        if not valoracion:
            return {**salida, "reason": "Sin valoracion no hay via."}

        mejor = None

        for nombre in TODAS_LAS_VIAS:

            pata = valoracion.get(nombre) or None

            if not pata:
                continue

            if nombre in VIAS_DEL_QUE_SE_QUEDA:
                valor = con_la_moneda(pata)["value"]
                moneda = "LIGA"

            else:
                valor = safe_int(pata.get("value"))
                moneda = "MERCADO"

            if valor <= 0:
                continue

            if mejor is None or valor > mejor[1]:
                mejor = (nombre, valor, pata, moneda)

        if mejor is None:
            return {
                **salida,
                "reason": (
                    "Ninguna via deja valor positivo, ni con la "
                    "moneda de la liga."
                ),
            }

        nombre, valor, pata, moneda = mejor

        via_antes = str((valoracion or {}).get("route") or "")

        ruta = str(pata.get("route") or "") or None

        return {
            **salida,
            "via": nombre,
            "intent": pata.get("intent"),
            "route": ruta,
            "value": valor,
            "moneda": moneda,
            "cambia_de_via": bool(ruta and via_antes and ruta != via_antes),
            "reason": (
                f"Gana la via {nombre} con {valor:,} EUR, cobrando "
                f"en la moneda "
                f"{'de la liga' if moneda == 'LIGA' else 'del mercado'}."
            ).replace(",", "."),
        }

    except Exception as error:                      # noqa: BLE001
        return {
            **salida,
            "reason": (
                f"No se pudo elegir via: "
                f"{type(error).__name__}: {error}"
            ),
        }


def a_quien_mejora(valoracion: dict | None) -> dict:
    """
    A quien del ONCE mejora, y por cuantos puntos.

    Sale de `as_xi.replaces`, que es quien saldria. Si la via no
    toca el once -ficha vacia, especulacion- se dice, no se
    rellena con un nombre cualquiera.

    Nunca lanza.
    """

    salida = {
        "nombre": None,
        "id": None,
        "puntos": None,
        "del_once": False,
        "reason": None,
    }

    try:
        xi = (valoracion or {}).get("as_xi") or {}

        sale = xi.get("replaces") or {}

        if not sale:
            return {
                **salida,
                "reason": (
                    "No mejora a nadie del once: no hay cambio "
                    "de titular valorado."
                ),
            }

        delta = xi.get("points_delta")

        return {
            **salida,
            "nombre": sale.get("name"),
            "id": sale.get("id"),
            "puntos": delta,
            "del_once": bool(xi.get("replaces_starter")),
            "reason": (
                f"Entra por {sale.get('name')} y suma "
                f"{delta} puntos."
                if delta is not None
                else f"Entra por {sale.get('name')}."
            ),
        }

    except Exception as error:                      # noqa: BLE001
        return {
            **salida,
            "reason": (
                f"No se pudo mirar a quien mejora: "
                f"{type(error).__name__}: {error}"
            ),
        }


def el_techo_que_lo_deja_pasar(techos: dict | None, puja: int) -> dict:
    """
    Cual de los dos techos deja pasar esa puja.

    `los_dos_techos` ya publica los dos; aqui solo se dice cual
    da el permiso. No se mueve ninguno: esta lista no decide.

    Nunca lanza.
    """

    salida = {
        "techo": None,
        "valor": None,
        "pasa": False,
        "reason": None,
    }

    try:
        if puja <= 0:
            # SIN PUJA NO HAY TECHO QUE JUZGAR.
            #
            #     Decir "la deja pasar el techo del COMERCIANTE"
            #     contra una puja de cero es ruido con forma de
            #     dato.
            return {
                **salida,
                "reason": (
                    "No se pujaria por el, asi que ningun techo "
                    "tiene nada que dejar pasar."
                ),
            }

        dos = techos or {}

        candidatos = []

        comerciante = dos.get("comerciante") or {}

        if comerciante.get("available"):
            candidatos.append(
                ("COMERCIANTE", safe_int(comerciante.get("techo")))
            )

        queda = dos.get("el_que_se_queda") or {}

        if queda.get("available"):
            candidatos.append(
                ("EL_QUE_SE_QUEDA", safe_int(queda.get("techo")))
            )

        if not candidatos:
            return {
                **salida,
                "reason": (
                    "Ningun techo calculado para esta ficha: "
                    "`los_dos_techos` no pudo con ninguno de los "
                    "dos."
                ),
            }

        pasan = [(n, v) for n, v in candidatos if v >= puja]

        if not pasan:
            alto = max(candidatos, key=lambda x: x[1])

            return {
                **salida,
                "techo": alto[0],
                "valor": alto[1],
                "reason": (
                    f"Ningun techo la deja pasar: el mas alto es "
                    f"el del {alto[0]} con {alto[1]:,} EUR y la "
                    f"puja seria {puja:,}."
                ).replace(",", "."),
            }

        # El mas ajustado de los que la dejan pasar: el que de
        # verdad manda.
        gana = min(pasan, key=lambda x: x[1])

        return {
            **salida,
            "techo": gana[0],
            "valor": gana[1],
            "pasa": True,
            "reason": (
                f"La deja pasar el techo del {gana[0]}: "
                f"{gana[1]:,} EUR contra una puja de {puja:,}."
            ).replace(",", "."),
        }

    except Exception as error:                      # noqa: BLE001
        return {
            **salida,
            "reason": (
                f"No se pudo mirar el techo: "
                f"{type(error).__name__}: {error}"
            ),
        }


def la_fila(ficha: dict | None, valoracion: dict | None, puja: dict | None) -> dict:
    """
    Una linea de la lista de la noche, con los ocho datos que
    pidio el dueño.

    `puja` es lo que devuelve `optimal_bid` corrido con el valor
    de la moneda: se recibe, no se calcula aqui. Quien tiene el
    modelo de rivales y el presupuesto es el tablero.

    Nunca lanza.
    """

    salida = {
        "id": None,
        "jugador": None,
        "posicion": None,
        "precio_de_mercado": 0,
        "lo_que_pujaria": 0,
        "prima": 0,
        "prima_percent": None,
        "por_que": None,
        "via": None,
        "moneda": None,
        "techo": None,
        "mejora_a": None,
        "puntos_de_mas": None,
        "decision": None,
        "reason": None,
    }

    try:
        datos = ficha or {}

        precio = safe_int(
            datos.get("market_price") or datos.get("price")
        )

        gana = la_via_que_ganaria(valoracion)

        importe = safe_int((puja or {}).get("bid"))

        mejora = a_quien_mejora(valoracion)

        techo = el_techo_que_lo_deja_pasar(
            datos.get("los_dos_techos"), importe
        )

        prima = importe - precio

        return {
            **salida,
            "id": datos.get("id"),
            "jugador": datos.get("name"),
            "posicion": POSICIONES.get(
                safe_int(datos.get("position")), "?"
            ),
            "precio_de_mercado": precio,
            "lo_que_pujaria": importe,
            # Sin puja no hay prima: un -100 % es aritmetica
            # correcta sobre una puja que no existe.
            "prima": prima if importe > 0 else None,
            "prima_percent": (
                round(100.0 * prima / precio, 3)
                if precio and importe > 0
                else None
            ),
            "por_que": (
                "PLANTILLA"
                if es_para_quedarse(
                    intent=gana.get("intent"), route=gana.get("route")
                )
                else "REVENTA"
            ),
            "via": gana.get("route") or gana.get("via"),
            "moneda": gana.get("moneda"),
            "techo": techo,
            "mejora_a": mejora.get("nombre"),
            "puntos_de_mas": mejora.get("puntos"),
            "decision": (puja or {}).get("decision"),
            "reason": (puja or {}).get("reason") or gana.get("reason"),
        }

    except Exception as error:                      # noqa: BLE001
        return {
            **salida,
            "reason": (
                f"No se pudo montar la fila: "
                f"{type(error).__name__}: {error}"
            ),
        }


def ordenar(filas) -> list:
    """
    De mayor a menor puja. «Es el que mas duele equivocarse.»

    Empatados, por precio de mercado: la ficha mas cara primero,
    que es la que compromete mas caja.
    """

    try:
        return sorted(
            list(filas or []),
            key=lambda f: (
                -safe_int((f or {}).get("lo_que_pujaria")),
                -safe_int((f or {}).get("precio_de_mercado")),
                str((f or {}).get("jugador") or ""),
            ),
        )

    except Exception:                               # noqa: BLE001
        return list(filas or [])


# Cuantos nombres caben en una pantalla a las tres de la mañana.
# NO SE RECORTA: si la lista pasa de aqui, se dice y se enseña
# entera. Recortar sin decirlo es lo que el encargo prohibe.
LOS_QUE_CABEN = 10


def el_mas_cerca(filas) -> dict:
    """
    De los que NO pujaria, el que menos lejos se queda.

    UNA LISTA VACIA TIENE QUE SER LEGIBLE (doctrina 103)

        Cero nombres puede ser "no hay nadie" o "esto se ha
        roto", y a las tres de la mañana no se distinguen. Asi
        que cuando no hay nadie se enseña a quien estuvo mas
        cerca y por que no.

    Nunca lanza.
    """

    try:
        fuera = [
            f
            for f in (filas or [])
            if safe_int((f or {}).get("lo_que_pujaria")) <= 0
        ]

        if not fuera:
            return {}

        # El mas caro de los mirados: es el que mas caja habria
        # movido si hubiera pasado.
        return max(
            fuera,
            key=lambda f: safe_int((f or {}).get("precio_de_mercado")),
        )

    except Exception:                               # noqa: BLE001
        return {}


def la_lista(filas) -> dict:
    """
    La lista entera, ordenada, para el panel.

    Se le pasan TODAS las filas miradas, no solo las que pujan:
    el recuento de mirados es lo que separa "no pujaria por
    nadie" de "no se ha mirado a nadie".

    Forma fija. Nunca lanza. No escribe nada.
    """

    salida = {
        "available": False,
        "n": 0,
        "mirados": 0,
        "filas": [],
        "el_mas_cerca": {},
        "recortada": False,
        "caben": LOS_QUE_CABEN,
        "reason": None,
    }

    try:
        todas = [f for f in (filas or []) if f]

        puestas = ordenar(
            [
                f
                for f in todas
                if safe_int(f.get("lo_que_pujaria")) > 0
            ]
        )

        if not puestas:
            cerca = el_mas_cerca(todas)

            return {
                **salida,
                "available": True,
                "mirados": len(todas),
                "el_mas_cerca": cerca,
                "reason": (
                    f"Con la moneda de la liga puesta, esta vuelta "
                    f"no pujaria por nadie. Mirados: {len(todas)}."
                    + (
                        f" El que mas cerca se queda es "
                        f"{cerca.get('jugador')}: "
                        f"{cerca.get('decision')}."
                        if cerca
                        else ""
                    )
                ),
            }

        # El punto de los miles se pone AQUI y no sobre la frase
        # entera: un `replace` sobre la frase se comia tambien
        # las comas de la prosa.
        total = f"{safe_int(sum(f['lo_que_pujaria'] for f in puestas)):,}".replace(",", ".")

        return {
            **salida,
            "available": True,
            "n": len(puestas),
            "mirados": len(todas),
            "filas": puestas,
            "reason": (
                f"{len(puestas)} nombre(s) de {len(todas)} mirados, "
                f"y {total} EUR en juego si la moneda estuviera "
                f"puesta. De mayor a menor puja."
                + (
                    f" Son mas de {LOS_QUE_CABEN}: se enseñan "
                    f"todos igual, recortar sin decirlo seria "
                    f"esconder el ultimo."
                    if len(puestas) > LOS_QUE_CABEN
                    else ""
                )
            ),
        }

    except Exception as error:                      # noqa: BLE001
        return {
            **salida,
            "reason": (
                f"No se pudo montar la lista: "
                f"{type(error).__name__}: {error}"
            ),
        }
