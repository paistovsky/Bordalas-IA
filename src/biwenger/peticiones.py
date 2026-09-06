"""
Cuantas peticiones hace Pepe, y que hacer cuando le dicen basta.

EL INCIDENTE (27/09/2026)

    Biwenger empezo a devolver 429 -Too Many Requests- a la
    cuenta entera. Produccion se cayo y el workflow hubo que
    desactivarlo a mano.

    La causa inmediata fue una descarga de 619 fichas de jugador
    en pocos minutos para rehacer la calibracion. Pero eso solo
    fue la gota: el ciclo normal hace 32 peticiones cada media
    hora -1.536 al dia- y de esas 12 son un duplicado exacto.

DOS COSAS QUE FALTABAN

    1. NADIE CONTABA. El numero de arriba se saco leyendo el
       codigo y sumando a mano. Un consumo que solo se conoce
       por aritmetica es un consumo que nadie vigila: cuando
       alguien añada una llamada, no se va a enterar nadie
       hasta el siguiente 429.

    2. UN 429 MATABA EL CICLO. La excepcion subia hasta arriba y
       el ciclo contaba como fallo, lo que ademas dispara el
       backoff de fallos y ensucia el diagnostico. Un limite de
       peticiones no es un fallo nuestro: es el servidor
       diciendo "ahora no". La respuesta correcta es esperar y,
       si sigue, retirarse limpiamente.

QUE HACE ESTE MODULO

    Cuenta cada peticion por endpoint, y envuelve la sesion para
    que un 429 se reintente con espera creciente y, si no cede,
    salga como una parada limpia y no como un error.

QUE NO HACE

    No decide nada, no cachea respuestas y no cambia ninguna
    llamada. Solo cuenta y aguanta.
"""

from __future__ import annotations

import re
import time


# Cuantas veces se reintenta un 429 antes de rendirse.
#
# Cuatro con espera creciente son 1 + 2 + 4 + 8 = 15 segundos de
# espera total. Un ciclo dura minutos, asi que cabe; y si el
# limite es de los largos -el de ayer duro horas- ninguna espera
# razonable lo iba a salvar y lo que toca es retirarse.
REINTENTOS_429 = 4


# La primera espera, en segundos. Cada reintento la dobla.
ESPERA_BASE = 1.0


# El codigo que significa "has pedido demasiado".
DEMASIADAS = 429


class LimiteDePeticiones(RuntimeError):
    """
    Biwenger nos ha limitado y no ha cedido al reintentar.

    NO ES UN FALLO NUESTRO

        Existe como excepcion propia para que el ciclo pueda
        distinguirla de un error de verdad. Un 429 no debe
        contar como ciclo fallido: no hay nada roto, hay que
        volver mas tarde.
    """


def _endpoint(url: str) -> str:
    """
    La URL sin identificadores, para poder agrupar.

    `/user/1234/finances` y `/user/5678/finances` son la misma
    llamada hecha dos veces, no dos llamadas distintas. Sin esto
    el recuento por endpoint no agrupa nada.
    """

    try:
        camino = str(url).split("://", 1)[-1]

        # Fuera el host y la query.
        camino = "/" + camino.split("/", 1)[-1]
        camino = camino.split("?", 1)[0]

        # Fuera la version de la API, que no distingue nada.
        camino = re.sub(r"^/api/v\d+", "", camino)

        # Los numeros son identificadores.
        return re.sub(r"/\d+", "/{id}", camino) or "/"

    except Exception:                               # noqa: BLE001
        return "?"


class Contador:
    """
    Cuantas peticiones y a donde.

    Forma fija: `resumen()` devuelve siempre las mismas claves,
    haya habido peticiones o no.
    """

    def __init__(self) -> None:
        self.por_endpoint: dict[str, int] = {}
        self.por_metodo: dict[str, int] = {}
        self.limitadas = 0
        self.esperado = 0.0

    def anota(self, metodo: str, url: str) -> None:
        clave = f"{str(metodo).upper()} {_endpoint(url)}"

        self.por_endpoint[clave] = (
            self.por_endpoint.get(clave, 0) + 1
        )

        self.por_metodo[str(metodo).upper()] = (
            self.por_metodo.get(str(metodo).upper(), 0) + 1
        )

    def anota_limite(self, esperado: float) -> None:
        self.limitadas += 1
        self.esperado += float(esperado or 0)

    def total(self) -> int:
        return sum(self.por_endpoint.values())

    def resumen(self) -> dict:
        """
        Lo que se publica. Nunca lanza.

        `repetidas` es el numero que de verdad importa: cuantas
        peticiones fueron a un endpoint al que ya se habia ido
        en este mismo ciclo. Es el ahorro disponible sin perder
        un solo dato.
        """

        try:
            repetidas = sum(
                cuantas - 1
                for cuantas in self.por_endpoint.values()
                if cuantas > 1
            )

            total = self.total()

            return {
                "available": True,
                "total": total,
                "unique_endpoints": len(self.por_endpoint),
                "repeated": repetidas,
                "repeated_percent": (
                    round(100 * repetidas / total, 1)
                    if total
                    else 0.0
                ),
                "by_endpoint": dict(
                    sorted(
                        self.por_endpoint.items(),
                        key=lambda par: -par[1],
                    )
                ),
                "by_method": dict(self.por_metodo),
                "rate_limited": self.limitadas,
                "waited_seconds": round(self.esperado, 1),
                "reason": None,
            }

        except Exception as error:                  # noqa: BLE001
            return {
                "available": False,
                "total": 0,
                "unique_endpoints": 0,
                "repeated": 0,
                "repeated_percent": 0.0,
                "by_endpoint": {},
                "by_method": {},
                "rate_limited": 0,
                "waited_seconds": 0.0,
                "reason": f"{type(error).__name__}: {error}",
            }


# El contador del proceso. Uno por ejecucion, que es exactamente
# un ciclo: el workflow arranca un proceso por vuelta.
CONTADOR = Contador()


def resumen() -> dict:
    """El recuento del ciclo, para publicarlo."""

    return CONTADOR.resumen()


def reiniciar() -> None:
    """Para las pruebas y para quien ejecute varios ciclos."""

    CONTADOR.__init__()


def envolver(session, contador: Contador | None = None):
    """
    La misma sesion, contando y aguantando el 429.

    Se envuelven `get`, `post`, `put` y `delete` y nada mas: no
    se toca ninguna llamada existente, solo se le pone un
    contador delante y un reintento detras.

    Devuelve la MISMA sesion, modificada en el sitio, para que
    todo el codigo que ya guarda una referencia siga sirviendo.
    """

    contador = contador or CONTADOR

    # Si ya esta envuelta no se envuelve dos veces: seria contar
    # cada peticion dos veces, que es justo el genero de error
    # que este modulo existe para cazar.
    if getattr(session, "_bordalas_envuelta", False):
        return session

    for metodo in ("get", "post", "put", "delete"):

        original = getattr(session, metodo, None)

        if original is None:
            continue

        setattr(
            session,
            metodo,
            _con_reintento(original, metodo, contador),
        )

    session._bordalas_envuelta = True

    return session


def _con_reintento(original, metodo: str, contador: Contador):

    def llamada(url, *args, **kwargs):

        espera = ESPERA_BASE

        for intento in range(REINTENTOS_429 + 1):

            contador.anota(metodo, url)

            respuesta = original(url, *args, **kwargs)

            if getattr(respuesta, "status_code", None) != (
                DEMASIADAS
            ):
                return respuesta

            # LIMITADOS. Se espera y se vuelve a probar.
            if intento >= REINTENTOS_429:

                raise LimiteDePeticiones(
                    f"Biwenger devolvio {DEMASIADAS} en "
                    f"{_endpoint(url)} tras "
                    f"{REINTENTOS_429} reintentos y "
                    f"{contador.esperado:.0f} s de espera. "
                    f"El ciclo se retira sin tocar nada: no hay "
                    f"nada roto, hay que volver mas tarde."
                )

            # Si el servidor dice cuanto esperar, se le hace
            # caso: adivinarlo es peor que preguntarlo.
            sugerida = _retry_after(respuesta)

            toca = sugerida if sugerida is not None else espera

            contador.anota_limite(toca)

            time.sleep(toca)

            espera *= 2

        # Inalcanzable: el bucle sale por return o por raise.
        return respuesta

    return llamada


def _retry_after(respuesta):
    """Los segundos que pide la cabecera `Retry-After`, o None."""

    try:
        cabecera = (
            getattr(respuesta, "headers", None) or {}
        ).get("Retry-After")

        if cabecera is None:
            return None

        segundos = float(str(cabecera).strip())

        # Un `Retry-After` de horas no se espera: se sale limpio
        # y se vuelve en el siguiente ciclo.
        if segundos <= 0 or segundos > 60:
            return None

        return segundos

    except (TypeError, ValueError):
        return None
