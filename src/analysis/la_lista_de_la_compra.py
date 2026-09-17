"""
La lista de la compra: de quien es cada jugador, y en que orden se opera.

EL PROBLEMA, EN UNA LINEA

    `roster_expansion` publica diez candidatos y no dice de quien
    son. Siete son de rivales. "Se paga hoy" significa que cabe
    en el presupuesto, no que se pueda comprar.

DOCTRINA 70 — UNA LISTA QUE NO FILTRA POR QUIEN LO TIENE NO ES UNA
LISTA DE LA COMPRA: ES UNA CARTA A LOS REYES

    Sobre la foto del 17/09 07:30, los diez candidatos:

        7 de MANAGER   (Luismi_Haz 3, Pollo17 2, Manzagool 1,
                        DiosMande 1)
        3 de COMPUTER  (Fornals, Budimir, Carlos Romero)

    Y el peso de la puerta: 9 traspasos de manager a manager en
    602 eventos del tablon, contra 182 compras al Computer. De
    esos 9, cuatro son nuestros — y de los cuatro, COMPRAMOS UNO.
    En cuarenta dias de liga hemos entrado por esa puerta como
    compradores una vez.

EL DATO YA VIAJABA

    `seller_kind` y `seller_name` estan en cada fila de
    `season_horizon`, que es de donde sale la lista.
    `build_roster_expansion_shadow` no los copia al candidato.

    No es un veto ni otra fuente: es una columna que se cae al
    construir la lista. Tercera vez esta semana del mismo patron.

Y EL MERCADO LIBRE: NO ES QUE NO SE VEA, ES QUE NO SE PUEDE COMPRAR

    `elVestuarioLibre` ya publica los libres del catalogo: 423 de
    550, 101 que nos mejoran. Ninguno esta en `roster_expansion`
    y la razon NO es un veto:

        de los 101 que nos mejoran, estan HOY en el escaparate: 1

    Y ese uno es Budimir, que SI esta en la lista. En Biwenger no
    se puja por un jugador que no esta publicado: no hay a quien
    ofrecerle nada. El universo comprable de la foto son 66 filas
    —20 del Computer y 46 publicados por rivales— y esos 66 son
    exactamente los que mira la lista.

    Asi que la lista no se queda corta por filtrar de mas: se
    queda corta porque el escaparate de hoy trae lo que trae.

EL ORDEN DE LAS OPERACIONES

    `needs_sale_first` protege el dinero y desprotege la
    plantilla:

        vender y luego comprar   seguro para la caja,
                                 arriesgado para el once
        comprar y luego vender   seguro para el once,
                                 arriesgado para la caja

    Para un SOBRANTE, vender primero esta bien: si la puja se
    pierde, se ha soltado a alguien que no juega. Para un
    TITULAR, no: si se pierde la puja, el once se queda peor y no
    salta ninguna alarma.

    Asi que la regla se parte en dos, y la parte de "titular" no
    propone la venta hasta que el recambio esta dentro.

FASE OBSERVADOR

    `ENCENDIDO = False`. Calcula, publica y no manda.
"""

from __future__ import annotations


ENCENDIDO = False


# Los dos grupos, con los nombres del encargo. Son etiquetas
# publicadas: si se cambian aqui, cambian en pantalla.
COMPRABLE_HOY = "SE_PUEDE_COMPRAR_HOY"

HAY_QUE_PEDIRSELO = "HAY_QUE_PEDIRSELO"

GRUPOS = (COMPRABLE_HOY, HAY_QUE_PEDIRSELO)


ETIQUETAS = {
    COMPRABLE_HOY: (
        "Se puede comprar hoy: esta en el escaparate y depende "
        "solo de nosotros."
    ),
    HAY_QUE_PEDIRSELO: (
        "Hay que pedirselo: lo tiene un rival y depende de que "
        "acepte."
    ),
}


# Quien vende, segun lo que ya trae la fila.
COMPUTER = "COMPUTER"

MANAGER = "MANAGER"


def safe_int(value, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def esta_encendido() -> bool:
    return bool(ENCENDIDO)


def _miles(valor) -> str:
    return f"{safe_int(valor):,}".replace(",", ".")


# ============================================================
# BLOQUE 1 — DE QUIEN ES
# ============================================================


def de_quien_es(fila: dict | None) -> dict:
    """
    De quien es este jugador y, por tanto, en que grupo cae.

    SIN SABERLO NO SE SUPONE. Una fila sin `seller_kind` no se
    cuenta como comprable: se marca desconocida y se manda al
    grupo de pedirselo, que es el lado prudente. Suponer que es
    del Computer seria pintar como comprable algo que a lo mejor
    hay que negociar.
    """

    datos = fila or {}

    clase = str(datos.get("seller_kind") or "").upper()

    vendedor = datos.get("seller_name")

    if clase == COMPUTER:
        return {
            "kind": COMPUTER,
            "seller": vendedor or "Computer",
            "grupo": COMPRABLE_HOY,
            "known": True,
            "reason": (
                "Lo saca el Computer en el escaparate de hoy: se "
                "puja y punto."
            ),
        }

    if clase == MANAGER:
        return {
            "kind": MANAGER,
            "seller": vendedor,
            "grupo": HAY_QUE_PEDIRSELO,
            "known": True,
            "reason": (
                f"Lo tiene {vendedor or 'un rival'}: se le ofrece, "
                f"y comprarlo depende de que acepte."
            ),
        }

    return {
        "kind": None,
        "seller": vendedor,
        "grupo": HAY_QUE_PEDIRSELO,
        "known": False,
        "reason": (
            "La fila no dice de quien es. No se supone que sea "
            "comprable: hasta saberlo va con los que hay que "
            "pedir."
        ),
    }


def partir_la_lista(
    candidatos: list | None,
    filas_por_id: dict | None = None,
    *,
    puerta: dict | None = None,
) -> dict:
    """
    La lista de fichajes, partida en dos y las dos publicadas.

    `filas_por_id` son las filas del universo comprable
    -`season_horizon.rows` o `acquisition.targets`- indexadas por
    id. De ahi sale `seller_kind`, que el candidato no trae.

    Cada grupo va ordenado por PUNTOS NETOS DEL ONCE POR EURO, si
    el candidato los trae calculados. Los que no se pueden medir
    van al final de su grupo, sin numero inventado.

    Nunca lanza. Con la lista vacia no publica grupos vacios como
    si fueran una medicion: dice que no hay lista.
    """

    try:
        filas = [c for c in (candidatos or []) if isinstance(c, dict)]

        if not filas:
            return {
                "available": False,
                "n": 0,
                "grupos": {},
                "reason": (
                    "La lista de candidatos llega vacia: no hay nada "
                    "que partir."
                ),
            }

        universo = filas_por_id or {}

        grupos = {COMPRABLE_HOY: [], HAY_QUE_PEDIRSELO: []}

        for candidato in filas:

            fila = universo.get(candidato.get("id")) or {}

            duenyo = de_quien_es(fila)

            grupos[duenyo["grupo"]].append(
                {
                    **candidato,
                    "seller_kind": duenyo["kind"],
                    "seller_name": duenyo["seller"],
                    "seller_known": duenyo["known"],
                    "grupo": duenyo["grupo"],
                    "grupo_label": ETIQUETAS[duenyo["grupo"]],
                    "de_quien_reason": duenyo["reason"],
                }
            )

        def _orden(item):
            valor = item.get("puntos_netos_por_millon")

            return (
                valor is None,
                -(valor or 0),
                safe_int(item.get("market_price")),
            )

        for grupo in GRUPOS:
            grupos[grupo].sort(key=_orden)

            for orden, item in enumerate(grupos[grupo], start=1):
                item["order"] = orden

        # EL DATO AL LADO DE LA SEGUNDA LISTA, que es lo que
        # impide confundir una carta con una lista de la compra.
        datos_puerta = puerta or {}

        traspasos = safe_int(datos_puerta.get("cuantos"))

        nuestros = safe_int(datos_puerta.get("nuestros"))

        compras = safe_int(datos_puerta.get("compras_al_computer"))

        return {
            "available": True,
            "n": len(filas),
            "grupos": grupos,

            "n_comprable_hoy": len(grupos[COMPRABLE_HOY]),
            "n_hay_que_pedirselo": len(grupos[HAY_QUE_PEDIRSELO]),

            "puerta": {
                "traspasos": traspasos or None,
                "nuestros": nuestros or None,
                "compras_al_computer": compras or None,
                "available": bool(datos_puerta.get("available")),
                "reason": (
                    (
                        f"{traspasos} traspaso(s) de manager a "
                        f"manager en todo el tablon"
                        + (
                            f", contra {compras} compras al Computer"
                            if compras
                            else ""
                        )
                        + (
                            f". {nuestros} son nuestros."
                            if nuestros
                            else "."
                        )
                    )
                    if datos_puerta.get("available")
                    else (
                        "No se ha podido contar cuantas veces se ha "
                        "cruzado la puerta: de la puerta no se dice "
                        "nada."
                    )
                ),
            },

            "reason": (
                f"{len(grupos[COMPRABLE_HOY])} se pueden comprar hoy "
                f"y {len(grupos[HAY_QUE_PEDIRSELO])} hay que "
                f"pedirselos a un rival."
            ),
        }

    except Exception as error:                      # noqa: BLE001
        return {
            "available": False,
            "n": 0,
            "grupos": {},
            "reason": (
                f"No se pudo partir la lista: "
                f"{type(error).__name__}: {error}"
            ),
        }


def libres_que_se_pueden_comprar(vestuario: dict | None) -> dict:
    """
    De los libres que nos mejoran, cuales estan HOY en el
    escaparate.

    El resto no son candidatos que alguien haya vetado: son
    jugadores por los que no se puede pujar, porque no estan
    publicados. Se publican igual, para que se vea el tamaño de
    lo que hay fuera.

    Nunca lanza.
    """

    try:
        datos = vestuario or {}

        jugadores = [
            j
            for j in (datos.get("players") or [])
            if isinstance(j, dict)
        ]

        if not jugadores:
            return {
                "available": False,
                "n": 0,
                "en_el_mercado": [],
                "fuera_del_mercado": [],
                "reason": (
                    "El vestuario libre llega vacio: sin catalogo no "
                    "se puede decir que hay fuera."
                ),
            }

        dentro = [j for j in jugadores if j.get("en_el_mercado")]

        fuera = [j for j in jugadores if not j.get("en_el_mercado")]

        recuento = datos.get("recuento") or {}

        return {
            "available": True,
            "n": len(jugadores),

            "libres_en_el_catalogo": datos.get("libres"),
            "nos_mejoran": recuento.get("nos_mejoran"),
            "en_el_mercado_hoy": recuento.get("en_el_mercado_hoy"),

            "en_el_mercado": dentro,
            "fuera_del_mercado": fuera,

            "reason": (
                f"{recuento.get('nos_mejoran')} libres del catalogo "
                f"nos mejoran y "
                f"{recuento.get('en_el_mercado_hoy')} estan hoy en "
                f"el escaparate. Por los demas no se puede pujar: no "
                f"estan publicados, asi que no hay a quien ofrecerle "
                f"nada. No los veta nadie."
            ),
        }

    except Exception as error:                      # noqa: BLE001
        return {
            "available": False,
            "n": 0,
            "en_el_mercado": [],
            "fuera_del_mercado": [],
            "reason": (
                f"No se pudo mirar el vestuario libre: "
                f"{type(error).__name__}: {error}"
            ),
        }


# ============================================================
# BLOQUE 2 — EL ORDEN DE LAS OPERACIONES
# ============================================================

VENTA_PRIMERO = "VENTA_PRIMERO"

RECAMBIO_PRIMERO = "RECAMBIO_PRIMERO"

SIN_VENTA = "SIN_VENTA"


def orden_de_la_operacion(
    quienes_salen: list | None,
    *,
    guardarrail: dict | None = None,
    hace_falta_vender: bool = True,
) -> dict:
    """
    En que orden va esta operacion, y por que.

    LAS TRES RESPUESTAS

        SIN_VENTA          no hace falta vender: se compra y ya.
        VENTA_PRIMERO      solo salen sobrantes. Si la puja se
                           pierde, se ha soltado a quien no juega.
        RECAMBIO_PRIMERO   sale un TITULAR. La venta no se
                           propone hasta tener el sustituto
                           dentro: perder la puja despues de
                           vender deja el once peor.

    `guardarrail` es opcional y solo se usa para saber quien esta
    bloqueado -`locked_ids`-, que es el mismo dato con el que
    `validate_sale_set_con_titularidad` decide. Sin el se mira
    `in_lineup` de cada uno, que es lo que trae la cola.

    Nunca lanza.
    """

    try:
        salen = [
            j for j in (quienes_salen or []) if isinstance(j, dict)
        ]

        if not hace_falta_vender or not salen:
            return {
                "orden": SIN_VENTA,
                "titulares_que_salen": [],
                "needs_sale_first": False,
                "reason": (
                    "No hace falta vender a nadie: se compra con la "
                    "caja que hay."
                ),
            }

        bloqueados = set(
            (guardarrail or {}).get("locked_ids") or []
        )

        titulares = [
            j
            for j in salen
            if j.get("in_lineup")
            or safe_int(j.get("id")) in bloqueados
        ]

        if not titulares:
            return {
                "orden": VENTA_PRIMERO,
                "titulares_que_salen": [],
                "needs_sale_first": True,
                "reason": (
                    "Solo salen sobrantes: la venta va primero. Si "
                    "la puja se pierde se ha soltado a quien no "
                    "juega, y eso no empeora el once."
                ),
            }

        nombres = ", ".join(
            str(j.get("name")) for j in titulares
        )

        return {
            "orden": RECAMBIO_PRIMERO,
            "titulares_que_salen": [
                {"id": j.get("id"), "name": j.get("name")}
                for j in titulares
            ],

            # LA PARTE QUE IMPORTA: no se marca `needs_sale_first`.
            # Marcarlo es exactamente lo que manda vender antes de
            # tener el recambio.
            "needs_sale_first": False,

            "reason": (
                f"Sale un titular ({nombres}): el recambio entra "
                f"PRIMERO. Vender antes de tener el sustituto deja "
                f"el once peor si se pierde la puja, y no salta "
                f"ninguna alarma."
            ),
        }

    except Exception as error:                      # noqa: BLE001
        return {
            "orden": RECAMBIO_PRIMERO,
            "titulares_que_salen": [],
            "needs_sale_first": False,
            "reason": (
                f"No se pudo decidir el orden, asi que no se vende "
                f"nada antes: {type(error).__name__}: {error}"
            ),
        }


# ============================================================
# BLOQUE 3 — LA TABLA POR PLAZAS DEL ONCE
# ============================================================


def _por_jornada(jugador: dict) -> float | None:
    """
    Puntos por partido JUGADO. Sin partidos no hay medicion: se
    devuelve None, no un cero.

    Mismo denominador que `calidad_medida.partidos_jugados`, y
    entendiendo los dos nombres del mismo dato.
    """

    partidos = safe_int(
        jugador.get("played_home")
        if jugador.get("played_home") is not None
        else jugador.get("playedHome")
    ) + safe_int(
        jugador.get("played_away")
        if jugador.get("played_away") is not None
        else jugador.get("playedAway")
    )

    if not partidos:
        partidos = safe_int(jugador.get("played"))

    if not partidos:
        return None

    return float(jugador.get("points") or 0) / partidos


def tabla_por_plazas(
    once: list | None,
    recambios: list | None,
    *,
    factor_de,
    caja_ahora: int = 0,
    guardarrail: dict | None = None,
) -> dict:
    """
    Para cada plaza del once, empezando por la peor: quien la
    ocupa, cuanto suma, y que recambios COMPRABLES HOY hay.

    `recambios` son solo los del grupo comprable hoy. Un recambio
    que hay que pedirle a un rival no es un recambio de esta
    tabla: es una carta.

    Nunca lanza. Con el once vacio no publica plazas.
    """

    try:
        titulares = [
            j for j in (once or []) if isinstance(j, dict)
        ]

        if not titulares:
            return {
                "available": False,
                "n": 0,
                "plazas": [],
                "mejor_sin_vender": None,
                "reason": (
                    "El once llega vacio: sin titulares no hay "
                    "plazas que ordenar."
                ),
            }

        disponibles = [
            r for r in (recambios or []) if isinstance(r, dict)
        ]

        bloqueados = set(
            (guardarrail or {}).get("locked_ids") or []
        )

        plazas = []

        for titular in titulares:

            posicion = titular.get("position")

            factor = float(factor_de(posicion))

            suyos = _por_jornada(titular)

            ocupa = (
                round(suyos * factor, 3) if suyos is not None else None
            )

            candidatos = []

            # SIN MEDIR NO ES LO MISMO QUE SIN HABER.
            #
            #     La primera version se saltaba a los que no tienen
            #     partidos y despues decia "hoy no hay ni un jugador
            #     de esta posicion en el escaparate". Era FALSO: en
            #     la foto del 17/09 hay dos porteros, Iturbe y
            #     Esquivel, con 0 puntos en 0 partidos.
            #
            #     Un motivo falso es peor que no tener motivo,
            #     porque se deja de discutir. Se cuentan aparte.
            sin_medir = []

            for recambio in disponibles:

                if recambio.get("position") != posicion:
                    continue

                coste = safe_int(recambio.get("price")) or safe_int(
                    recambio.get("market_price")
                )

                trae = _por_jornada(recambio)

                if trae is None or coste <= 0:
                    sin_medir.append(
                        {
                            "id": recambio.get("id"),
                            "name": recambio.get("name"),
                            "price": coste,
                            "reason": (
                                "No ha jugado ningun partido: no se "
                                "puede decir si mejora la plaza, y a "
                                "ciegas no se cambia un titular."
                                if trae is None
                                else "Sin precio."
                            ),
                        }
                    )
                    continue

                entran = round(trae * factor, 3)

                netos = (
                    round(entran - ocupa, 3)
                    if ocupa is not None
                    else None
                )

                partidos = safe_int(recambio.get("played")) or (
                    safe_int(recambio.get("played_home"))
                    + safe_int(recambio.get("played_away"))
                )

                candidatos.append(
                    {
                        "id": recambio.get("id"),
                        "name": recambio.get("name"),
                        "price": coste,
                        "points_per_match": round(trae, 3),

                        # DOCTRINA 55 Y 58: el `n` viaja con el
                        # numero. Cinco puntos en UN partido y
                        # treinta en seis no son la misma medicion,
                        # y aqui el que manda la tabla puede ser
                        # cualquiera de los dos.
                        "matches": partidos,
                        "thin": partidos < 3,

                        "con_vara": entran,
                        "puntos_netos": netos,
                        "puntos_netos_por_millon": (
                            round(netos / (coste / 1_000_000), 4)
                            if netos is not None and netos > 0
                            else None
                        ),
                        "cabe_en_caja": coste <= safe_int(caja_ahora),
                        "mejora": bool(
                            netos is not None and netos > 0
                        ),
                    }
                )

            # Los que mejoran primero, y de esos el que mas da por
            # euro. Los que no mejoran se publican igual: enseñan
            # que la plaza esta mirada y no hay nada.
            candidatos.sort(
                key=lambda c: (
                    not c["mejora"],
                    -(c["puntos_netos_por_millon"] or 0),
                    c["price"],
                )
            )

            mejoran = [c for c in candidatos if c["mejora"]]

            plazas.append(
                {
                    "position": posicion,
                    "id": titular.get("id"),
                    "name": titular.get("name"),
                    "points_per_match": (
                        round(suyos, 3) if suyos is not None else None
                    ),
                    "con_vara": ocupa,
                    "vara": round(factor, 3),
                    "es_intocable": safe_int(titular.get("id"))
                    in bloqueados,

                    "recambios": candidatos,
                    "recambios_que_mejoran": len(mejoran),
                    "sin_medir": sin_medir,

                    "mejor": mejoran[0] if mejoran else None,

                    "reason": (
                        (
                            f"{len(mejoran)} recambio(s) comprables "
                            f"hoy mejoran esta plaza."
                        )
                        if mejoran
                        else (
                            "Ningun recambio comprable hoy mejora "
                            "esta plaza."
                            if candidatos
                            else (
                                (
                                    f"{len(sin_medir)} de esta "
                                    f"posicion en el escaparate y "
                                    f"ninguno se puede medir: "
                                    + ", ".join(
                                        str(x["name"]) for x in sin_medir
                                    )
                                    + ", sin un partido jugado."
                                )
                                if sin_medir
                                else (
                                    "Hoy no hay ni un jugador de esta "
                                    "posicion en el escaparate."
                                )
                            )
                        )
                    ),
                }
            )

        # Las peores plazas primero: es donde mas hay que ganar.
        plazas.sort(
            key=lambda p: (
                p["con_vara"] is None,
                p["con_vara"] or 0,
            )
        )

        # Y ARRIBA DEL TODO: la operacion que mas puntos da por
        # euro SIN VENDER A NADIE. Cabe en caja y no hace salir a
        # nadie porque el que sale es el titular al que sustituye
        # -que se queda en el banquillo, no se vende-.
        posibles = [
            {**plaza["mejor"], "plaza": plaza["name"], "position": plaza["position"]}
            for plaza in plazas
            if plaza["mejor"] and plaza["mejor"]["cabe_en_caja"]
        ]

        posibles.sort(
            key=lambda c: -(c["puntos_netos_por_millon"] or 0)
        )

        return {
            "available": True,
            "n": len(plazas),
            "plazas": plazas,
            "mejor_sin_vender": posibles[0] if posibles else None,
            "candidatas_sin_vender": posibles,
            "caja_ahora": safe_int(caja_ahora),
            "reason": (
                (
                    f"La mejor operacion sin vender a nadie: "
                    f"{posibles[0]['name']} por "
                    f"{posibles[0]['plaza']}, "
                    f"{_miles(posibles[0]['price'])} EUR, "
                    f"{posibles[0]['puntos_netos']:+.2f} puntos por "
                    f"jornada con la vara puesta, medidos sobre "
                    f"{posibles[0].get('matches')} partido(s)."
                    + (
                        " AVISO: menos de tres partidos. El numero "
                        "que corona la tabla es el mas flojo de "
                        "muestra."
                        if posibles[0].get("thin")
                        else ""
                    )
                )
                if posibles
                else (
                    "Ninguna plaza del once tiene hoy un recambio "
                    "comprable que la mejore y quepa en caja."
                )
            ),
        }

    except Exception as error:                      # noqa: BLE001
        return {
            "available": False,
            "n": 0,
            "plazas": [],
            "mejor_sin_vender": None,
            "reason": (
                f"No se pudo montar la tabla por plazas: "
                f"{type(error).__name__}: {error}"
            ),
        }
