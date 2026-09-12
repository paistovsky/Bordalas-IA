"""
La rendija: el carril propio de las pujas de revender.

POR QUE UN CARRIL Y NO UN SITIO EN LA COLA

    `decision_orchestrator` elige UNA accion por vuelta, la de
    mas prioridad, y `SPECULATION_BUY` esta en 400: la ultima de
    la fila. Eso esta BIEN y no se discute — el once gana al
    dinero, y el dinero gana a especular.

    Pero la cola existe para elegir la mejor accion cuando las
    acciones son ESCASAS y CARAS. Una puja de revender no es
    ninguna de las dos cosas:

        · PERDERLA NO CUESTA NADA. Esta medido: todas las pujas
          se resuelven en el reset de las 07:00 y las pujas de
          los rivales son invisibles. No hay nada que reservar.

        · CUESTA CENTIMOS DE PETICIONES. Una puja es un POST.
          El ciclo entero son 7.

    Asi que no compite por el hueco de la vuelta: se ejecuta
    DESPUES de la accion principal, con presupuesto propio y
    pequeno.

LO QUE ESTE CARRIL NO EXIGE

    LA VENTANA. Las pujas de revender se pueden colocar a
    cualquier hora. El motivo esta medido: todas se resuelven en
    el reset y las de los rivales no se ven, asi que pujar tarde
    no nos esconde de nadie. La ventana no aportaba NADA para
    pujar — era una creencia nuestra, no una mecanica del juego.

    LA COMPUERTA DE RITMO, para el cupo de abajo.

LO QUE SE QUEDA, SIN EXCEPCION

    · LA ZONA DE SILENCIO. No se escribe nada mientras el
      mercado se resuelve. Se usa la que ya hay -04:45 a 07:00
      de Madrid-, que cubre de sobra el 05:00-07:00 pedido. No
      se mueve ningun umbral.

    · EL CUPO POR CICLO DE RESET, de 07:00 a 07:00. Al no
      haber ventana, el cupo necesitaba una unidad: esa.
      Empieza en DOS y sube a cuatro solo cuando se cierre un
      viaje entero. Vive en  y en ningun
      otro sitio.

    · DOS ESCRITURAS DE ESTE CARRIL POR VUELTA.

    · NI UNA SI LA ACCION PRINCIPAL FUE UNA EMERGENCIA. Si hay
      emergencia, el carril se calla esa vuelta.

    · El importe que dice la curva, el tope por operacion,
      `MAX_SINGLE_SPECULATION_PERCENT`, las fichas libres, las
      barandillas sobre el peor caso -que se ganen las cuatro-,
      la deuda y el reloj de solvencia. NINGUN umbral se mueve:
      esto no los toca, solo decide si el carril abre.

SE APAGA SOLA

    Tras 10 viajes cerrados, si la mediana del resultado es
    negativa, la rendija se cierra y sale en ROJO en la portada.
    No hace falta que nadie se acuerde de mirarla.
"""

from __future__ import annotations

import statistics

from datetime import datetime, timezone


# ============================================================
# LOS TOPES DEL CARRIL
# ============================================================

# Por vuelta. Dos es lo que cabe sin que el carril se note en el
# consumo: son 2 POST sobre una vuelta de 7 peticiones.
ESCRITURAS_POR_VUELTA = 2

# ============================================================
# EL CUPO, Y POR QUE HAY DOS
# ============================================================
#
# Por ciclo de reset, de 07:00 a 07:00.
#
# SE EMPIEZA POR DOS, NO POR CUATRO
#
#     Hasta que no se cierre UN viaje entero -comprado, listado,
#     oferta recibida y cobrada por encima del suelo- no sabemos
#     si la rueda gira. Abrir con cuatro seria comprometer el
#     doble sobre algo que no ha funcionado ni una vez.
#
#     En cuanto pase una vez, sube a cuatro solo.
#
# UN NUMERO EN UN SITIO
#
#     El cupo vigente no se escribe en ningun otro lado: se
#     pregunta a `cupo_del_reset()`, que ademas dice en cual
#     esta y por que, para que la portada lo pinte sin deducir
#     nada.
# ============================================================
# LA PRUEBA DE HUMO (12/09/2026)
# ============================================================
#
#     El primer viaje NO TIENE QUE GANAR DINERO: TIENE QUE
#     COMPLETARSE. Una vez, de punta a punta —comprado, listado,
#     oferta recibida, cobrada por encima del suelo—. Nueve mil
#     euros valen; lo que compran es saber que la cadena
#     funciona.
#
#     Con el bolsillo de hoy el tope por operacion son ~740.000,
#     y con el suelo normal de 1 M el carril no tiene mercado:
#     las dos condiciones eran incompatibles y no podia comprar
#     nada NUNCA.
#
#     Asi que el suelo baja a 400.000 TEMPORALMENTE. En cuanto
#     se complete un viaje, vuelve solo a 1.000.000 y el cupo
#     pasa a 2.
#
# LO QUE ESTO NO ES
#
#     No es mover un umbral medido. `PRECIO_QUE_NO_PAGA_LA_FICHA`
#     sigue siendo 1.000.000 y sigue siendo verdad: por debajo,
#     un +1,52 % sobre 150.000 son 2.250 EUR que no pagan la
#     ficha. Lo que se acepta a sabiendas es que la operacion de
#     la PRUEBA gane poco. Es el precio de saber si la cadena
#     entera funciona.
# RETIRADO EL 12/09/2026, EL MISMO DIA QUE SE PUSO.
#
#     Se bajo a 400.000 para que la prueba de humo pudiera
#     comprar algo. Medido con el mercado de ese dia: no valia.
#
#     Por debajo del millon el Computer casi no ofrece nada, y
#     cuando ofrece la prima de reventa es la PEOR de las cuatro
#     bandas -+1,52 %, medido sobre las mismas 34 recompras-. La
#     prueba se habria hecho en el unico tramo donde el negocio
#     no existe: se habria medido la cadena con el peor material
#     posible y un fracaso no habria dicho nada.
#
#     El freno nunca fue el suelo. Era el TECHO -el tope por
#     operacion, 843.612 EUR, que salia de un porcentaje del
#     bolsillo del motor de especular-. La solucion es darle al
#     carril bolsillo propio, no bajarle el suelo.
#
#     Se deja escrito y NO se borra: el numero se probo, se midio
#     y se retiro por una razon, y esa razon vale mas que el
#     numero.
SUELO_RETIRADO_DE_LA_PRUEBA = 400_000

# El suelo de verdad. No se escribe aqui: se importa de donde se
# midio.
from src.analysis.salida_del_viaje import (                # noqa: E402
    PRECIO_QUE_NO_PAGA_LA_FICHA,
)

# ============================================================
# EL BOLSILLO DEL CARRIL — PROPIO, EN EUROS
# ============================================================
#
# POR QUE EXISTE
#
#     Hasta hoy el tope por operacion del carril salia de
#     `MAX_SINGLE_SPECULATION_PERCENT` sobre el bolsillo del
#     motor de especular: 843.612 EUR el 12/09. Menor que el
#     suelo de 1.000.000, o sea que EL CARRIL NO PODIA COMPRAR
#     NADA, NUNCA, por construccion.
#
#     Y para arreglarlo habia dos caminos: tocar los porcentajes
#     del motor de especular -que mueve tambien lo que hace la
#     via vieja, y son numeros calibrados- o darle al carril su
#     propio tope. El segundo no toca nada de lo otro.
#
# POR QUE 3.000.000 Y NO 2.000.000
#
#     Por el tramo de mejor prima de reventa, medido sobre las
#     mismas 34 recompras:
#
#         <1 M    +1,52 %      3-6 M   +3,20 %
#         1-3 M   +3,46 %  <-  6 M+    +3,83 %
#
#     Con tope de 2 M el carril solo alcanza la parte baja del
#     tramo bueno. Con 3 M lo alcanza entero.
#
# LO QUE SE PUEDE PERDER
#
#     Un viaje -CUPO_DE_LA_PRUEBA = 1- de 3 M como mucho, que
#     cierra en uno o dos dias, contra un techo de puja de
#     16,72 M. Si sale mal, lo que se pierde no son los 3 M: es
#     la caida del precio durante los resets que dure, que
#     medida esta en torno al 8 % en cuatro. Unos 240.000.
CARRIL_TOPE_POR_OPERACION = 3_000_000

PRIMA_DEL_TRAMO_BARATO = 1.52

# El cupo, por ciclo de reset. UNO mientras dure la prueba: un
# viaje, y se mira.
CUPO_DE_LA_PRUEBA = 1

CUPO_DE_ESTRENO = 2

# El de cuatro sigue escrito y hoy NO SE ALCANZA por ningun
# camino automatico: su condicion era la misma que la de subir a
# dos, y no puede servir para las dos cosas. Cuando haga falta,
# necesita condicion propia.
CUPO_PLENO = 4

# Cuantos viajes cerrados hacen falta antes de juzgar si esto
# merece la pena. Menos que esto es una racha, no una medicion.
VIAJES_PARA_JUZGAR = 10

# La marca que lleva cada operacion de este carril.
MARCA = "RENDIJA"

# Si la accion principal fue una de estas, el carril se calla.
EMERGENCIAS = ("EMERGENCY_", "HARD_SAFETY", "ROUND_LOCK")

# Las primas de reventa medidas. Viven en `salida_del_viaje`
# y aqui NO se copian: se importan, para que el dia que la
# medicion se actualice cambien los dos sitios a la vez.
from src.analysis.salida_del_viaje import (              # noqa: E402
    PRIMA_MEDIANA_MEDIDA,
    PRIMA_POR_POSICION,
    SUELO_DEL_VIAJE,
)


def safe_int(value, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def safe_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _euros(valor) -> str:
    try:
        return f"{int(valor):,}".replace(",", ".")
    except (TypeError, ValueError):
        return "?"


# ============================================================
# SE APAGA SOLA
# ============================================================


def se_apaga_sola(cierres: list | None) -> dict:
    """
    ¿Sigue mereciendo la pena la rendija? Forma fija.

    `cierres` son los viajes YA CERRADOS, cada uno con su
    `profit`. Con menos de `VIAJES_PARA_JUZGAR` no se opina: una
    racha de tres no dice nada, y apagar por una racha seria el
    mismo error que montar una regla sobre un caso.
    """

    try:
        resultados = [
            safe_int(c.get("profit"))
            for c in (cierres or [])
            if isinstance(c, dict) and c.get("profit") is not None
        ]

        if len(resultados) < VIAJES_PARA_JUZGAR:
            return {
                "available": True,
                "apagada": False,
                "cerrados": len(resultados),
                "mediana": None,
                "reason": (
                    f"{len(resultados)} viaje(s) cerrado(s) de "
                    f"{VIAJES_PARA_JUZGAR}: aun no hay con que "
                    f"juzgar."
                ),
            }

        mediana = statistics.median(resultados)

        apagada = mediana < 0

        return {
            "available": True,
            "apagada": apagada,
            "cerrados": len(resultados),
            "mediana": mediana,
            "reason": (
                (
                    f"LA RENDIJA SE HA CERRADO SOLA: la mediana "
                    f"de {len(resultados)} viajes cerrados es "
                    f"{_euros(mediana)} EUR. Pierde dinero."
                )
                if apagada
                else (
                    f"Mediana de {len(resultados)} viajes: "
                    f"{_euros(mediana)} EUR."
                )
            ),
        }

    except Exception as error:                      # noqa: BLE001
        return {
            "available": False,
            "apagada": True,
            "cerrados": 0,
            "mediana": None,
            "reason": (
                f"No se pudo juzgar la rendija, asi que se cierra: "
                f"{type(error).__name__}: {error}"
            ),
        }


# ============================================================
# EL CUPO VIGENTE
# ============================================================


def un_viaje_cerrado_entero(cierres: list | None) -> dict:
    """
    ¿Ha dado alguno la vuelta completa? Forma fija.

    "Entero" es: comprado, listado, oferta recibida y COBRADA
    POR ENCIMA DEL SUELO. Un corte de perdidas o un viaje
    caducado NO cuentan: la rueda no ha girado, solo se ha
    parado.
    """

    try:
        for cierre in cierres or []:

            if not isinstance(cierre, dict):
                continue

            beneficio = cierre.get("profit")

            if beneficio is None:
                continue

            if safe_int(beneficio) > 0 and not cierre.get(
                "loss_cut"
            ):
                return {
                    "available": True,
                    "hay": True,
                    "player_name": cierre.get("player_name"),
                    "profit": safe_int(beneficio),
                    "at": cierre.get("at"),
                }

        return {"available": True, "hay": False}

    except Exception:                               # noqa: BLE001
        # Sin saberlo, por el lado prudente: no hay.
        return {"available": False, "hay": False}


def viajes_completados(cierres: list | None) -> int:
    """
    CUANTOS han dado la vuelta entera. La linea que el dueno
    quiere ver cada dia hasta que ponga 1.

    Usa EXACTAMENTE la misma definicion de "entero" que
    `un_viaje_cerrado_entero` —cobrado por encima del suelo, sin
    corte de perdidas—, porque si contara con otra regla habria
    dos verdades sobre el mismo hecho y una estaria mal.

    Devuelve un entero. Si no se sabe, 0: el lado prudente es no
    dar por completado lo que no consta.
    """

    try:
        return len(
            [
                c
                for c in cierres or []
                if isinstance(c, dict)
                and un_viaje_cerrado_entero([c]).get("hay")
            ]
        )

    except Exception:                               # noqa: BLE001
        return 0


def suelo_de_precio(cierres: list | None = None) -> dict:
    """
    Por debajo de que precio no mira el carril, y POR QUE.

    Es el unico sitio donde vive ese numero. Hoy tiene un solo
    estado: el 12/09 se bajo a 400.000 para la prueba de humo y
    se devolvio el mismo dia, porque por debajo del millon el
    Computer casi no ofrece nada y la prima de reventa es la peor
    de las cuatro bandas. Ver `SUELO_RETIRADO_DE_LA_PRUEBA`.

    `cierres` se sigue aceptando aunque hoy no cambie nada: la
    firma la usan el ejecutor y la telemetria, y quitarla para
    volver a ponerla es mas ruido que dejarla.
    """

    return {
        "available": True,
        "suelo": PRECIO_QUE_NO_PAGA_LA_FICHA,
        "estado": "NORMAL",
        "reason": (
            f"Suelo de {_euros(PRECIO_QUE_NO_PAGA_LA_FICHA)} "
            f"EUR: por debajo, la prima de reventa medida es "
            f"+{PRIMA_DEL_TRAMO_BARATO} % —la peor de las cuatro "
            f"bandas— y sobre 150.000 son 2.250 EUR, que no "
            f"pagan la ficha que ocupan."
        ),
    }


def cupo_del_reset(cierres: list | None = None) -> dict:
    """
    Cuantas operaciones caben en este ciclo de reset, y POR QUE.

    ES EL UNICO SITIO DONDE VIVE ESE NUMERO. La portada lo pinta
    de aqui: ni lo deduce ni lo lleva escrito.
    """

    primero = un_viaje_cerrado_entero(cierres)

    if primero.get("hay"):
        return {
            "available": True,
            "cupo": CUPO_DE_ESTRENO,
            "estado": "ESTRENO",
            "reason": (
                f"Cupo de {CUPO_DE_ESTRENO} por ciclo de reset: "
                f"ya se completo un viaje entero"
                + (
                    f" ({primero.get('player_name')}, "
                    f"+{_euros(primero.get('profit'))} EUR)"
                    if primero.get("player_name")
                    else ""
                )
                + "."
            ),
        }

    return {
        "available": True,
        "cupo": CUPO_DE_LA_PRUEBA,
        "estado": "PRUEBA_DE_HUMO",
        "reason": (
            f"Cupo de {CUPO_DE_LA_PRUEBA} por ciclo de reset: "
            f"PRUEBA DE HUMO. Un viaje, de punta a punta "
            f"-comprado, listado, oferta recibida y cobrada por "
            f"encima del suelo-. Sube a {CUPO_DE_ESTRENO} en "
            f"cuanto pase una vez."
        ),
    }


def bolsillo_del_carril(caja=None, comprometido=None) -> dict:
    """
    Cuanto puede comprometer el carril en UNA operacion, y POR
    QUE ese numero.

    ES SUYO, EN EUROS, Y NO SALE DE NINGUN PORCENTAJE DEL MOTOR
    DE ESPECULAR. Ese fue el cambio del 12/09: mientras el tope
    salia de un porcentaje del bolsillo ajeno, valia 843.612 EUR
    —menos que el suelo— y el carril no podia comprar nada.

    PERO EL DINERO TIENE QUE EXISTIR

        Tener bolsillo propio no es tener dinero propio. Si la
        caja no llega a 3.000.000, el tope es la caja: el carril
        no abre deuda para especular, y por eso no puede romper
        ninguna barandilla de solvencia — nunca compromete mas de
        lo que hay.

        Sin saber la caja NO SE PUJA. Pujar a ciegas con un tope
        de 3 M es justo lo que esta funcion existe para impedir.

    Y LO YA COMPROMETIDO NO ES CAJA

        El motor de especular descuenta de SU presupuesto las
        pujas vivas (`apply_exposure_to_budget`), asi que ve lo
        que compromete el carril. Al reves no pasaba: el carril
        tiene bolsillo propio y podria comprometer 3 M sobre una
        caja de la que la ruta normal ya hubiera apartado otro
        tanto, y las dos pujas se resuelven en el MISMO reset.

        `comprometido` es ese dinero apartado. Se resta antes de
        nada: tener bolsillo propio no es tener dinero propio.

    Forma fija. Nunca lanza.
    """

    try:
        disponible = safe_int(caja) - max(
            0, safe_int(comprometido)
        )

        if disponible <= 0:
            # DOS CASOS, DOS NOMBRES (regla 33). "No se sabe
            # cuanto hay" y "se sabe, y esta todo apartado" se
            # arreglan de formas distintas: el primero es una
            # lectura rota, el segundo es el sistema funcionando.
            return {
                "available": False,
                "tope": 0,
                "limitado_por": (
                    "CAJA_DESCONOCIDA"
                    if safe_int(caja) <= 0
                    else "SIN_CAJA_LIBRE"
                ),
                "reason": (
                    f"Sin caja libre no se puja. Caja "
                    f"{_euros(safe_int(caja))} EUR menos "
                    f"{_euros(max(0, safe_int(comprometido)))} "
                    f"EUR ya comprometidos en pujas vivas. El "
                    f"tope del carril son "
                    f"{_euros(CARRIL_TOPE_POR_OPERACION)} y "
                    f"comprometerlos a ciegas es exactamente lo "
                    f"que no puede pasar."
                ),
            }

        if disponible < CARRIL_TOPE_POR_OPERACION:
            return {
                "available": True,
                "tope": disponible,
                "limitado_por": "CAJA",
                "reason": (
                    f"Tope de {_euros(disponible)} EUR: es la "
                    f"caja LIBRE, que hoy no llega a los "
                    f"{_euros(CARRIL_TOPE_POR_OPERACION)} del "
                    f"carril. El carril no abre deuda para "
                    f"especular."
                ),
            }

        return {
            "available": True,
            "tope": CARRIL_TOPE_POR_OPERACION,
            "limitado_por": "CARRIL_TOPE_POR_OPERACION",
            "reason": (
                f"Tope de "
                f"{_euros(CARRIL_TOPE_POR_OPERACION)} EUR por "
                f"operacion: es el bolsillo propio del carril, "
                f"no un porcentaje del motor de especular. "
                f"Alcanza el tramo de mejor prima de reventa "
                f"medida, 1-3 M (+3,46 %). Caja disponible, "
                f"{_euros(disponible)} EUR."
            ),
        }

    except Exception as error:                      # noqa: BLE001
        return {
            "available": False,
            "tope": 0,
            "limitado_por": "ERROR",
            "reason": (
                f"No se pudo calcular el bolsillo del carril: "
                f"{type(error).__name__}: {error}"
            ),
        }


# ============================================================
# EL IMPORTE DE LA PUJA
# ============================================================
#
# POR QUE EL CARRIL NO SE LO PIDE AL TABLERO
#
#     12/09/2026. Con el carril ya enchufado, seguia sin pujar:
#     el tablero daba importe CERO a los 59 objetivos.
#
#         decision: RENDIMIENTO_INSUFICIENTE
#
#     Esa es `RENDIMIENTO_MINIMO_DEL_CAPITAL`, la compuerta que
#     exige que la operacion rinda un minimo sobre el capital que
#     inmoviliza. Para la via de especular esta bien; para el
#     carril es justo la que se quito, porque el negocio de un
#     viaje no es el rendimiento sino el SPREAD.
#
#     O sea: el carril le pedia el importe a una pieza que
#     decide con el criterio que el carril no usa. Tercer fallo
#     de la misma familia que los dos de hoy — una pieza armada
#     cuya entrada la corta algo de mas arriba.
#
# DE DONDE SALE ENTONCES
#
#         importe = precio de mercado x curva de puja
#
#     La curva calibrada en vivo sobre las pujas medidas de esta
#     liga. Es "el importe que dice la curva", literalmente.
#
# Y LOS TOPES QUE SIGUEN MANDANDO
#
#     · el tope por operacion
#     · MAX_SINGLE_SPECULATION_PERCENT del presupuesto
#
#     Ninguno se mueve: se aplican. Y si alguno no se sabe, NO
#     se puja — un importe sin tope conocido es la puerta
#     abierta mas cara que hay.


def importe_de_la_puja(
    precio_de_mercado,
    curva: float,
    presupuesto=None,
    tope_por_operacion=None,
) -> dict:
    """
    Lo que se puja por un candidato del carril. Forma fija.

    `curva` es el multiplicador (1,0028 = +0,28 %), tal como lo
    publica `premium_model`.
    """

    vacio = {
        "available": False,
        "amount": 0,
        "capped_by": None,
        # EL TOPE, COMO DATO Y NO DENTRO DE UNA FRASE.
        #
        #     Estaba solo en el texto del motivo, asi que para
        #     saber el numero habia que leer una cadena. Un dato,
        #     un nombre (regla 33).
        "tope": None,
        "reason": None,
    }

    try:
        precio = safe_int(precio_de_mercado)

        if precio <= 0:
            return {
                **vacio,
                "reason": "Sin precio de mercado no se puja.",
            }

        multiplicador = safe_float(curva)

        if multiplicador is None or multiplicador < 1:
            return {
                **vacio,
                "reason": (
                    f"Curva de puja imposible ({curva}): no se "
                    f"puja por debajo del precio."
                ),
            }

        bruto = int(round(precio * multiplicador))

        # LOS TOPES. Sin ellos NO se puja.
        #
        # EL CARRIL TRAE EL SUYO, Y ENTONCES MANDA EL SUYO
        #
        #     Mientras el tope del carril salia de un porcentaje
        #     del bolsillo del motor de especular valia 843.612
        #     EUR: MENOS QUE EL SUELO de 1.000.000, o sea que el
        #     carril no podia comprar nada por construccion.
        #
        #     Desde el 12/09 el carril tiene bolsillo propio en
        #     euros (`CARRIL_TOPE_POR_OPERACION`), y cuando lo
        #     pasa NO se consulta `MAX_SINGLE_SPECULATION_PERCENT`
        #     — no es que se ignore un limite: es que ese limite
        #     es de OTRO bolsillo y se estaba aplicando aqui por
        #     no tener uno propio.
        #
        #     El bolsillo del carril ya viene acotado por la caja
        #     (`bolsillo_del_carril`), asi que no puede
        #     comprometer dinero que no hay.
        if tope_por_operacion is not None:
            cual = "CARRIL_TOPE_POR_OPERACION"

            tope = safe_int(tope_por_operacion)

        else:
            presupuesto = safe_int(presupuesto)

            if presupuesto <= 0:
                return {
                    **vacio,
                    "reason": (
                        "Sin presupuesto de especulacion "
                        "conocido no se puja."
                    ),
                }

            from src.analysis.speculation_engine import (
                MAX_SINGLE_SPECULATION_PERCENT,
            )

            cual = "MAX_SINGLE_SPECULATION_PERCENT"

            tope = int(
                presupuesto * MAX_SINGLE_SPECULATION_PERCENT
            )

        if tope <= 0:
            return {
                **vacio,
                "reason": (
                    f"El tope `{cual}` sale {tope}: no se puja."
                ),
            }

        if bruto > tope:
            return {
                "available": True,
                "amount": 0,
                "capped_by": cual,
                "tope": tope,
                "reason": (
                    f"La puja de {_euros(bruto)} EUR pasa el tope "
                    f"`{cual}` ({_euros(tope)} EUR). NO se recorta "
                    f"a la baja: pujar por debajo de la curva es "
                    f"pagar la ficha por perder la subasta."
                ),
            }

        return {
            "available": True,
            "amount": bruto,
            "capped_by": None,
            "tope": tope,
            "reason": (
                f"{_euros(bruto)} EUR = {_euros(precio)} x "
                f"{multiplicador:.4f} (la curva), dentro del tope "
                f"`{cual}` de {_euros(tope)} EUR."
            ),
        }

    except Exception as error:                      # noqa: BLE001
        return {
            **vacio,
            "reason": (
                f"No se pudo calcular el importe: "
                f"{type(error).__name__}: {error}"
            ),
        }



def los_que_se_pueden_pagar(
    candidatos: list | None,
    curva: float,
    presupuesto=None,
    tope_por_operacion=None,
) -> dict:
    """
    De los candidatos, a quien se le puede pagar la puja. Y el
    resto, con su nombre.

    SINTOMA (12/09/2026)

        Se bajo el suelo a 400.000 para que el carril pudiera
        comprar por fin algo, y siguio sin comprar. El panel
        decia "8 llegan al suelo, 0 fuera" y el carril elegia a
        CANCELO, de 5.970.000, con un tope por operacion de
        843.612. Siete veces.

    CAUSA

        EL TOPE SE APLICABA AL PAGAR, NUNCA AL ELEGIR.

        `importe_de_la_puja` lo miraba —y hacia bien en no
        recortar a la baja— pero para entonces el candidato ya
        estaba elegido y el cupo, gastado en un nombre imposible.
        Y el orden de preferencia NO MIRA EL PRECIO: va por
        prima de posicion —defensas primero—, asi que el
        primero de la lista puede costar cualquier cosa. Ese
        dia era Cancelo, defensa de 5.970.000.

    CONSECUENCIA

        El mismo tope, un paso antes. No es un umbral nuevo:
        es `MAX_SINGLE_SPECULATION_PERCENT`, el que ya habia,
        preguntado cuando todavia sirve de algo.

        Y los que no caben salen por su nombre, para que la
        pantalla diga POR QUE no se compro en vez de callarse.
    """

    salida = {
        "available": False,
        "caben": [],
        "no_caben": [],
        "tope": None,
        "reason": None,
    }

    try:
        caben = []

        no_caben = []

        tope = None

        for candidato in candidatos or []:

            if not isinstance(candidato, dict):
                continue

            precio = safe_int(
                candidato.get("market_price")
                or (candidato.get("margen") or {}).get(
                    "market_price"
                )
            )

            cuanto = importe_de_la_puja(
                precio,
                curva=curva,
                presupuesto=presupuesto,
                tope_por_operacion=tope_por_operacion,
            )

            if tope is None:
                tope = cuanto.get("tope")

            if safe_int(cuanto.get("amount")) > 0:
                caben.append(candidato)

            else:
                no_caben.append(
                    {
                        "name": (
                            candidato.get("name")
                            or (
                                candidato.get("margen") or {}
                            ).get("name")
                        ),
                        "market_price": precio,
                        "reason": cuanto.get("reason"),
                        "capped_by": cuanto.get("capped_by"),
                    }
                )

        # Regla 24: si no venia ninguno, se dice, no se pasa en
        # vacio como si todo estuviera bien.
        if not (candidatos or []):
            return {
                **salida,
                "available": True,
                "reason": (
                    "No habia candidatos que mirar: el tope no "
                    "ha descartado a nadie porque no habia nadie."
                ),
            }

        return {
            "available": True,
            "caben": caben,
            "no_caben": no_caben,
            "tope": tope,
            "reason": (
                f"{len(caben)} de {len(candidatos)} se pueden "
                f"pagar"
                + (
                    f"; {len(no_caben)} pasan el tope por "
                    f"operacion"
                    if no_caben
                    else ""
                )
                + "."
            ),
        }

    except Exception as error:                      # noqa: BLE001
        return {
            **salida,
            "reason": (
                f"No se pudo mirar quien se puede pagar: "
                f"{type(error).__name__}: {error}"
            ),
        }


# ============================================================
# EL MARGEN ESPERADO
# ============================================================
#
# Es el numero que define un viaje, y hasta hoy no estaba.
#
#     coste          = precio x (1 + prima de puja)
#     precio al dia  = precio x (1 + ritmo diario)
#     oferta         = precio al dia x (1 + prima de reventa)
#     margen         = oferta / coste - 1
#
# QUE NO ES ESTO
#
#     NO es la compuerta de ritmo. Aquella exigia que el precio
#     SUBIERA, que es el negocio equivocado: el nuestro es el
#     spread, no la rampa. Esto exige que la OPERACION GANE
#     DINERO, que es lo unico que define un viaje. Un jugador
#     que cae un 2 % al dia puede seguir dando margen si la
#     prima de reventa de su posicion lo compensa — y uno que
#     sube puede no darlo.
#
# QUE PRIMA DE REVENTA SE APLICA, Y POR QUE
#
#     LA DE SU POSICION. El Computer no recompra igual a un
#     defensa que a un delantero: medido el 10/09 sobre 34
#     recompras, defensa +3,67 %, portero +3,26 %, medio
#     +2,85 %, delantero +1,80 %.
#
#     La mediana de la liga mezcla las cuatro, asi que para un
#     defensa es un estimador SESGADO A LA BAJA: le aplica el
#     promedio de un grupo en el que el es de los que mas
#     recuperan.
#
#     PERO CON UNA CAUTELA QUE HAY QUE DECIR: esos 34 casos
#     repartidos en cuatro posiciones son unos 8 o 9 por
#     posicion. La prima por posicion es el estimador CORRECTO y
#     a la vez el mas DEBIL. Por eso se publican los dos margenes
#     -el de su posicion y el de la mediana- y no solo el que
#     conviene: elegir el estimador mas favorable para que una
#     operacion justa pase es la forma mas comoda de hablarse a
#     uno mismo para entrar en un mal negocio.


def margen_esperado(
    candidato: dict | None,
    prima_de_puja: float,
    ritmo_diario=None,
    ritmo_supuesto=None,
) -> dict:
    """
    Lo que se espera ganar con este viaje. Forma fija, nunca
    lanza.

    `prima_de_puja` y las primas de reventa van en TANTO POR
    CIENTO, como se miden y como se publican.

    Sin ritmo observado se usa `ritmo_supuesto` -el mediano del
    mercado- y la fila queda marcada `supuesto=True`: no es lo
    mismo un margen medido que uno que descansa en un supuesto,
    y hay que poder juzgarlos aparte.
    """

    vacio = {
        "available": False,
        "margen_percent": None,
        "supuesto": False,
        "reason": None,
    }

    try:
        ficha = candidato or {}

        precio = safe_int(ficha.get("market_price"))

        if precio <= 0:
            return {
                **vacio,
                "reason": (
                    "Sin precio de mercado no se puede calcular "
                    "el margen."
                ),
            }

        posicion = safe_int(ficha.get("position"))

        prima_posicion = PRIMA_POR_POSICION.get(posicion)

        # LOS BARATOS SE RECOMPRAN PEOR, Y ESO ESTA MEDIDO APARTE
        #
        #     Las dos tablas salen de las MISMAS 34 recompras,
        #     partidas de dos formas: por posicion y por tramo de
        #     precio. Para un jugador de menos de 1 M la que
        #     describe su caso es la del TRAMO (+1,52 %), no la
        #     de su posicion.
        #
        #     Sin esto, la prueba de humo salia optimista: a un
        #     medio de 660.000 le aplicaba +2,85 % cuando su
        #     tramo se recompra a +1,52 %. Casi dos puntos de
        #     margen inventados, justo en el rango donde se va a
        #     jugar la prueba.
        if precio < PRECIO_QUE_NO_PAGA_LA_FICHA:

            prima_posicion = PRIMA_DEL_TRAMO_BARATO

        if prima_posicion is None:
            return {
                **vacio,
                "reason": (
                    f"Posicion desconocida ({posicion}): no hay "
                    f"prima de reventa medida para ella."
                ),
            }

        ritmo = safe_float(ritmo_diario)

        supuesto = ritmo is None

        if supuesto:
            ritmo = safe_float(ritmo_supuesto)

        if ritmo is None:
            return {
                **vacio,
                "reason": (
                    "Sin ritmo observado ni supuesto no se puede "
                    "calcular el margen."
                ),
            }

        puja = safe_float(prima_de_puja)

        if puja is None:
            return {
                **vacio,
                "reason": (
                    "Sin prima de puja no se sabe lo que costaria."
                ),
            }

        coste = precio * (1 + puja / 100.0)

        precio_al_dia = precio * (1 + ritmo / 100.0)

        oferta = precio_al_dia * (1 + prima_posicion / 100.0)

        margen = (oferta / coste - 1) * 100.0

        # El mismo calculo con la mediana de la liga, para que se
        # vea de cuanto depende la eleccion del estimador.
        oferta_mediana = precio_al_dia * (
            1 + PRIMA_MEDIANA_MEDIDA / 100.0
        )

        margen_mediana = (oferta_mediana / coste - 1) * 100.0

        return {
            "available": True,
            "player_id": safe_int(ficha.get("player_id")),
            "name": ficha.get("name"),
            "position": posicion,
            "market_price": precio,
            "prima_de_puja_percent": round(puja, 4),
            "ritmo_percent_dia": round(ritmo, 4),
            "supuesto": supuesto,
            "prima_de_reventa_percent": prima_posicion,
            "cost": int(round(coste)),
            "price_next_day": int(round(precio_al_dia)),
            "expected_offer": int(round(oferta)),
            "margen_percent": round(margen, 4),
            "margen_con_mediana_percent": round(
                margen_mediana, 4
            ),
            "gana": margen > 0,

            # ¿LLEGA LA OFERTA ESPERADA AL SUELO DE VENTA?
            #
            #     El suelo es coste x (1 + SUELO_DEL_VIAJE), o
            #     sea coste + 1 %. Y el margen es exactamente
            #     oferta/coste - 1. Asi que:
            #
            #         margen >= 1 %  <=>  la oferta esperada
            #                             supera el suelo
            #
            #     Un margen POSITIVO pero por debajo del 1 % es
            #     una operacion que espera una oferta que
            #     NOSOTROS MISMOS RECHAZARIAMOS: el viaje entra
            #     y, por construccion, no puede cerrarse con
            #     ganancia.
            #
            #     El filtro que pidio el dueno es "negativo
            #     fuera". Esto NO lo cambia: lo publica, para
            #     que la diferencia se vea y la decida el.
            "llega_al_suelo": margen >= SUELO_DEL_VIAJE * 100,
            "reason": (
                f"{ficha.get('name') or precio}: coste "
                f"{_euros(coste)} (+{puja:.2f} % de puja), "
                f"precio al dia {_euros(precio_al_dia)} "
                f"({ritmo:+.2f} %"
                + (" SUPUESTO" if supuesto else "")
                + f"), oferta esperada {_euros(oferta)} "
                f"(+{prima_posicion:.2f} % de su posicion) -> "
                f"margen {margen:+.2f} %"
                + (
                    f" (con la mediana de la liga seria "
                    f"{margen_mediana:+.2f} %)"
                )
                + (
                    ""
                    if margen >= SUELO_DEL_VIAJE * 100
                    else (
                        f" OJO: no llega al suelo de venta "
                        f"({SUELO_DEL_VIAJE * 100:.0f} %), asi "
                        f"que el viaje no podria cerrarse con "
                        f"ganancia."
                    )
                )
                + "."
            ),
        }

    except Exception as error:                      # noqa: BLE001
        return {
            **vacio,
            "reason": (
                f"No se pudo calcular el margen: "
                f"{type(error).__name__}: {error}"
            ),
        }


def ritmo_mediano(rates: dict | None) -> float | None:
    """
    El ritmo diario mediano del mercado. Es el SUPUESTO que se
    usa para quien no trae dato propio.

    Se publica siempre como supuesto, nunca como medido: hoy son
    5 de 11 candidatos, y un margen que descansa en un supuesto
    tiene que poder juzgarse aparte del que no.
    """

    try:
        valores = [
            safe_float(v.get("rate_percent_per_day"))
            for v in (rates or {}).values()
            if isinstance(v, dict)
        ]

        valores = [v for v in valores if v is not None]

        if not valores:
            return None

        return round(statistics.median(valores), 4)

    except Exception:                               # noqa: BLE001
        return None


def con_margen(
    candidatos: list | None,
    prima_de_puja: float,
    rates: dict | None = None,
) -> dict:
    """
    Los candidatos con su margen esperado, y FUERA los que no
    llegan al suelo de cobro.

    Es el unico filtro que este carril anade, y no filtra por
    direccion del precio: filtra por que la operacion se pueda
    CERRAR con ganancia.
    """

    vacio = {
        "available": False,
        "entran": [],
        "fuera": [],
        "ritmo_supuesto": None,
        "reason": None,
    }

    try:
        from src.analysis.market_rate_gate import evaluate

        supuesto = ritmo_mediano(rates)

        entran = []

        fuera = []

        for candidato in candidatos or []:

            if not isinstance(candidato, dict):
                continue

            visto = evaluate(
                safe_int(candidato.get("player_id")), rates
            )

            fila = margen_esperado(
                candidato,
                prima_de_puja=prima_de_puja,
                ritmo_diario=visto.get("rate_percent_per_day"),
                ritmo_supuesto=supuesto,
            )

            if not fila.get("available"):
                fuera.append(fila)
                continue

            # EL FILTRO ES EL SUELO, NO EL CERO (12/09/2026).
            #
            #     El suelo de cobro es coste + 1 %, y el margen
            #     es oferta/coste - 1. Asi que un margen entre 0
            #     y 1 % es un viaje que espera una oferta que
            #     NOSOTROS MISMOS RECHAZARIAMOS: entra y no
            #     puede cerrarse.
            #
            #     Ayer entro asi Robbie Ure, con +0,49 %.
            if fila["llega_al_suelo"]:
                entran.append({**candidato, "margen": fila})

            else:
                fuera.append(fila)

        # El de mas margen, primero.
        entran.sort(
            key=lambda x: -x["margen"]["margen_percent"]
        )

        supuestos = sum(
            1 for x in entran if x["margen"]["supuesto"]
        )

        return {
            "available": True,
            "entran": entran,
            "fuera": fuera,
            "ritmo_supuesto": supuesto,
            "con_supuesto": supuestos,
            "reason": (
                f"{len(entran)} llegan al suelo "
                f"(+{SUELO_DEL_VIAJE * 100:.0f} %), "
                f"{len(fuera)} fuera"
                + (
                    f"; {supuestos} de los que entran usan el "
                    f"ritmo SUPUESTO ({supuesto:+.2f} %/dia)"
                    if supuestos and supuesto is not None
                    else ""
                )
                + "."
            ),
        }

    except Exception as error:                      # noqa: BLE001
        return {
            **vacio,
            "reason": (
                f"No se pudo calcular el margen de los "
                f"candidatos: {type(error).__name__}: {error}"
            ),
        }



# ============================================================
# EL RITMO DE LOS CANDIDATOS
# ============================================================


def ritmo_de_los_candidatos(
    candidatos: list | None,
    rates: dict | None = None,
) -> dict:
    """
    De lo que el carril compraria: ¿viene SUBIENDO o CAYENDO, y a
    que ritmo? Forma fija, nunca lanza.

    LA COMPUERTA DE RITMO SE QUITO A PROPOSITO. El negocio es el
    spread, no la rampa: se compra al precio del Computer y se
    revende por encima, y para eso da igual hacia donde vaya el
    precio.

    Pero quitarla no es dejar de mirar. El libro en la sombra
    decia que lo que se rechazaba era todo PRECIO_CAYENDO; si lo
    que compramos tambien lo es, el experimento real es "comprar
    caidos y revender", y eso hay que saberlo MIENTRAS PASA, no
    despues.

    ESTO NO DECIDE NADA. Solo cuenta lo que se esta comprando.
    """

    vacio = {
        "available": False,
        "filas": [],
        "subiendo": 0,
        "cayendo": 0,
        "planos": 0,
        "sin_dato": 0,
        "todos_cayendo": False,
        "reason": None,
    }

    try:
        from src.analysis.market_rate_gate import (
            FALLING,
            build_market_rates,
            evaluate,
        )

        ritmos = (
            rates if rates is not None else build_market_rates()
        )

        filas = []

        for candidato in candidatos or []:

            if not isinstance(candidato, dict):
                continue

            pid = safe_int(candidato.get("player_id"))

            visto = evaluate(pid, ritmos)

            ritmo = safe_float(visto.get("rate_percent_per_day"))

            if ritmo is None:
                direccion = "SIN_DATO"

            elif ritmo > 0:
                direccion = "SUBIENDO"

            elif ritmo < 0:
                direccion = FALLING

            else:
                direccion = "PLANO"

            filas.append(
                {
                    "player_id": pid,
                    "name": candidato.get("name"),
                    "position": safe_int(
                        candidato.get("position")
                    ),
                    "market_price": safe_int(
                        candidato.get("market_price")
                    ),
                    "direction": direccion,
                    "rate_percent_per_day": ritmo,
                    "trend_days": visto.get("trend_days"),
                }
            )

        cuenta = {
            "subiendo": sum(
                1 for f in filas if f["direction"] == "SUBIENDO"
            ),
            "cayendo": sum(
                1 for f in filas if f["direction"] == FALLING
            ),
            "planos": sum(
                1 for f in filas if f["direction"] == "PLANO"
            ),
            "sin_dato": sum(
                1 for f in filas if f["direction"] == "SIN_DATO"
            ),
        }

        con_dato = len(filas) - cuenta["sin_dato"]

        todos_cayendo = bool(
            con_dato and cuenta["cayendo"] == con_dato
        )

        return {
            "available": True,
            "filas": filas,
            **cuenta,
            "todos_cayendo": todos_cayendo,
            "reason": (
                f"{len(filas)} candidato(s): "
                f"{cuenta['subiendo']} subiendo, "
                f"{cuenta['cayendo']} cayendo, "
                f"{cuenta['planos']} planos, "
                f"{cuenta['sin_dato']} sin dato."
                + (
                    " TODOS los que traen dato vienen CAYENDO: el "
                    "experimento es «comprar caidos y revender»."
                    if todos_cayendo
                    else ""
                )
            ),
        }

    except Exception as error:                      # noqa: BLE001
        return {
            **vacio,
            "reason": (
                f"No se pudo medir el ritmo de los candidatos: "
                f"{type(error).__name__}: {error}"
            ),
        }



# ============================================================
# EL INTERRUPTOR
# ============================================================
#
# ARMADA EL 11/09/2026, con el dueno delante y despues de leer
# el ensayo en seco.
#
# Se puede apagar SIN DESPLEGAR: `RENDIJA_APAGADA=1` y el carril
# se calla. Es la misma forma que `BORDALAS_SIN_SUBASTA` y
# `BORDALAS_VARA_PLANA`, y existe por lo mismo: el dia que haya
# que pararla, no se puede depender de un commit.
APAGADO_ENV = "RENDIJA_APAGADA"


def en_vivo() -> bool:
    """¿Escribe el carril de verdad? Nunca lanza."""

    try:
        import os

        return str(
            os.getenv(APAGADO_ENV, "")
        ).strip().lower() not in ("1", "true", "si", "yes")

    except Exception:                               # noqa: BLE001
        # Si no se sabe, NO se escribe.
        return False


# ============================================================
# EL PERMISO DEL CARRIL
# ============================================================


def permiso(
    ahora: datetime | None = None,
    accion_principal: str | None = None,
    escrituras_en_esta_vuelta: int = 0,
    operaciones_en_este_reset: int = 0,
    cierres: list | None = None,
    armada: bool | None = None,
    disparo: str | None = None,
) -> dict:
    """
    ¿Puede escribir el carril de la rendija ahora mismo?

    Forma fija, nunca lanza. Cada "no" dice por que, y en este
    orden: apagado, silencio, emergencia, cupo del reset, cupo de
    la vuelta.
    """

    vacio = {
        "available": False,
        "puede": False,
        "quedan_en_la_vuelta": 0,
        "quedan_en_el_reset": 0,
        "blocked_by": None,
        "reason": None,
    }

    try:
        momento = ahora or datetime.now(timezone.utc)

        armada_ahora = (
            en_vivo() if armada is None else bool(armada)
        )

        apagado = se_apaga_sola(cierres)

        cupo = cupo_del_reset(cierres)

        quedan_reset = max(
            0,
            cupo["cupo"]
            - safe_int(operaciones_en_este_reset),
        )

        quedan_vuelta = max(
            0,
            ESCRITURAS_POR_VUELTA
            - safe_int(escrituras_en_esta_vuelta),
        )

        base = {
            "available": True,
            "puede": False,
            "quedan_en_la_vuelta": quedan_vuelta,
            "quedan_en_el_reset": quedan_reset,
            "cupo_por_vuelta": ESCRITURAS_POR_VUELTA,
            "cupo_por_reset": cupo["cupo"],
            "cupo_estado": cupo["estado"],
            "cupo_reason": cupo["reason"],
            "apagado": apagado,
            "en_vivo": armada_ahora,
        }

        # 1. ¿SE HA APAGADO SOLA?
        if apagado.get("apagada"):
            return {
                **base,
                "blocked_by": "APAGADA",
                "reason": apagado.get("reason"),
            }

        # 2. LA ZONA DE SILENCIO. La que ya hay, sin tocarla.
        from src.analysis.zona_de_silencio import (
            permite_escribir,
        )

        # EL DISPARO VIAJA (12/09/2026).
        #
        #     Aqui se llamaba sin `disparo`, asi que un
        #     disparo DELIBERADO -el de las 04:45 y 04:50,
        #     puestos a proposito dentro de la zona- se
        #     bloqueaba igual que uno del cron. La zona
        #     existe para que el cron no escriba mientras el
        #     mercado se resuelve, no para vetar lo que se
        #     programo a mano para esa hora.
        silencio = permite_escribir(momento, disparo=disparo)

        if not silencio.get("allowed", True):
            return {
                **base,
                "blocked_by": "SILENCIO",
                "reason": (
                    "Zona de silencio: el mercado se esta "
                    "resolviendo y los datos son de otro mundo. "
                    + str(silencio.get("reason") or "")
                ).strip(),
            }

        # 3. LA EMERGENCIA MANDA. Si la vuelta se fue en una,
        #    el carril se calla: no es momento de comprar para
        #    revender.
        principal = str(accion_principal or "").upper()

        if any(principal.startswith(e) for e in EMERGENCIAS):
            return {
                **base,
                "blocked_by": "EMERGENCIA",
                "reason": (
                    f"La accion principal de esta vuelta fue "
                    f"«{principal}»: con una emergencia encima, "
                    f"el carril no escribe."
                ),
            }

        # 4. EL CUPO DEL RESET, de 07:00 a 07:00.
        if quedan_reset <= 0:
            return {
                **base,
                "blocked_by": "CUPO_DEL_RESET",
                "reason": (
                    f"Ya van {safe_int(operaciones_en_este_reset)} "
                    f"operaciones en este ciclo de reset y el "
                    + cupo["reason"]
                ),
            }

        # 5. EL CUPO DE LA VUELTA.
        if quedan_vuelta <= 0:
            return {
                **base,
                "blocked_by": "CUPO_DE_LA_VUELTA",
                "reason": (
                    f"Ya van {safe_int(escrituras_en_esta_vuelta)} "
                    f"escrituras del carril en esta vuelta y el "
                    f"tope son {ESCRITURAS_POR_VUELTA}."
                ),
            }

        return {
            **base,
            "puede": True,
            "reason": (
                f"El carril puede escribir: quedan "
                f"{quedan_vuelta} en la vuelta y {quedan_reset} "
                f"en este ciclo de reset."
                + (
                    ""
                    if armada_ahora
                    else f" (APAGADO por {APAGADO_ENV}.)"
                )
            ),
        }

    except Exception as error:                      # noqa: BLE001
        # Si no se sabe si se puede, NO se puede.
        return {
            **vacio,
            "reason": (
                f"No se pudo decidir el permiso del carril, asi "
                f"que no escribe: {type(error).__name__}: {error}"
            ),
        }


# ============================================================
# A QUIEN PREFERIR
# ============================================================


def a_quien_pujar(
    candidatos: list | None,
    cuantos: int | None = None,
) -> dict:
    """
    Los candidatos, EN ORDEN de preferencia, y cuantos caben.

    No es un filtro nuevo: es el orden que sale de lo medido el
    10/09 sobre 34 recompras del Computer —defensas +3,67 %,
    porteros +3,26 %, medios +2,85 %, delanteros +1,80 %— y del
    suelo de ficha: por debajo de 1 M, un +1,52 % sobre 150.000
    son 2.250 EUR y no pagan la ficha.

    `orden_de_preferencia` ya hace ese trabajo y aqui no se
    duplica: se reutiliza, para que el dia que la medicion se
    actualice cambien los dos sitios a la vez.
    """

    try:
        from src.analysis.salida_del_viaje import (
            orden_de_preferencia,
        )

        ordenados = orden_de_preferencia(candidatos)

        tope = (
            cupo_del_reset()["cupo"]
            if cuantos is None
            else max(0, safe_int(cuantos))
        )

        return {
            "available": True,
            "orden": ordenados,
            "elegidos": ordenados[:tope],
            "reason": (
                f"{len(ordenados)} candidato(s) en orden de "
                f"preferencia; caben {tope}."
            ),
        }

    except Exception as error:                      # noqa: BLE001
        return {
            "available": False,
            "orden": [],
            "elegidos": [],
            "reason": (
                f"No se pudo ordenar a los candidatos: "
                f"{type(error).__name__}: {error}"
            ),
        }
