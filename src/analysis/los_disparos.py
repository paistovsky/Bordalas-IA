"""
La autoridad del reloj, que YA NO VIVE EN EL REPOSITORIO.

SINTOMA (12/09/2026)

    La verja en rojo y el ciclo parado: `test_los_relojes_v1`,
    5 de 6. La que fallaba era `test_la_cadencia_sale_del_cron`,
    y fallaba porque leia el `schedule` de `bordalas-live.yml`
    como autoridad — y ese bloque ya no existe.

POR QUE SE QUITO EL SCHEDULE DE GITHUB, QUE ES LO QUE IMPORTA

    Se retiro el 12/09/2026, y NO fue por capricho ni por
    simplificar: SE SALTABA VUELTAS TODOS LOS DIAS.

        llegaba 30-40 minutos tarde
        y perdia ciclos enteros

    Los `schedule` de GitHub Actions no son una promesa: son una
    cola de baja prioridad. Cuando la cola va cargada, el disparo
    llega tarde o no llega. Con una vuelta por hora, un retraso
    de 30-40 minutos no es "un poco tarde": es que la vuelta de
    esa hora se solapa con la siguiente o se pierde.

    QUE NADIE LO VUELVA A PONER SIN SABER ESTO. Si alguien ve un
    workflow con solo `workflow_dispatch` y piensa "le falta el
    cron", esto es lo que le falta saber: se probo, se midio y se
    quito.

    El latido pasa a cron-job.org, que dispara por
    `workflow_dispatch`.

LA CONSECUENCIA DE FONDO

    LA AUTORIDAD DEL RELOJ YA NO ESTA EN EL CODIGO. Esta en un
    servicio externo que el codigo no puede leer, ni consultar,
    ni verificar.

    Asi que lo unico honesto que puede hacer el codigo es
    DECLARAR LO QUE ESPERA, en un sitio y como dato, y comparar
    la realidad contra esa declaracion. Eso es
    `config/disparos.json`.

    Y ojo a lo que eso significa: la declaracion NO ES LA
    VERDAD. Es lo que creemos haber configurado. Si cron-job.org
    estuviera parado, o con otra hora, la declaracion seguiria
    diciendo lo mismo tan tranquila. Lo unico que puede cazar esa
    diferencia es el aviso de DISPARO FUERA DE HORA, que compara
    la hora real a la que entro el ciclo contra esta
    declaracion.

    ESA ALARMA ES AHORA LA UNICA QUE MIRA LA REALIDAD.

POR QUE UN JSON Y NO UNA CONSTANTE

    Porque lo leen dos casas —Python y la pantalla— y un dato en
    dos idiomas son dos datos. Ya paso: la cadencia estuvo
    escrita a mano en tres sitios y cuando el cron cambio, los
    tres se quedaron mintiendo mientras la cuenta atras iba bien.

    `relojes.js` importa este mismo fichero. No hay espejo que
    pueda desincronizarse porque no hay espejo.

REGLA 23

    Este modulo NO lee el mundo: lee un fichero del propio
    repositorio, igual que leer una constante. No toca `data/`,
    ni la red, ni el reloj.
"""

from __future__ import annotations

import json

from pathlib import Path


RAIZ = Path(__file__).parents[2]

DECLARACION = RAIZ / "config" / "disparos.json"


# La fecha en que se retiro el `schedule` de GitHub, y el dato
# que lo motivo. Van juntos a proposito: una fecha sin el motivo
# es una nota que nadie sabe si sigue valiendo.
SCHEDULE_RETIRADO_EL = "2026-09-12"

SCHEDULE_RETRASO_MEDIDO = "30-40 minutos"

SCHEDULE_MOTIVO = (
    "Se saltaba vueltas todos los dias: llegaba 30-40 minutos "
    "tarde y perdia ciclos enteros. El latido pasa a "
    "cron-job.org."
)


def _lee() -> dict:
    """La declaracion, cruda. Lanza si no esta: sin ella no hay reloj."""

    return json.loads(DECLARACION.read_text(encoding="utf-8"))


def declaracion() -> dict:
    """
    Los disparos que este proyecto ESPERA. Forma fija.

    Nunca lanza: si la declaracion no se puede leer se devuelve
    `available: False` y quien llame decide. Lo que NO se hace es
    inventar un horario por defecto — un valor por defecto no
    puede absorber el caso mas importante (doctrina 36), y aqui
    el caso mas importante es justamente "no se sabe a que hora
    tenia que entrar".
    """

    vacio = {
        "available": False,
        "zona": None,
        "latido": {},
        "puntuales": [],
        "cadencia_minutos": None,
        "gracia_minutos": None,
        "todos_los_minutos": [],
        "reason": None,
    }

    try:
        crudo = _lee()

        latido = crudo.get("latido") or {}

        minuto = int(latido.get("minuto"))

        horas = [int(h) for h in latido.get("horas") or []]

        puntuales = [
            p
            for p in crudo.get("puntuales") or []
            if isinstance(p, dict) and p.get("madrid")
        ]

        # Regla 24: una declaracion vacia no puede pasar como si
        # todo estuviera bien. Sin disparos no hay reloj.
        if not horas or not puntuales:
            return {
                **vacio,
                "reason": (
                    "La declaracion no tiene disparos: sin ellos "
                    "no se puede saber si un ciclo entro a su "
                    "hora."
                ),
            }

        todos = sorted(
            [h * 60 + minuto for h in horas]
            + [_minutos(p["madrid"]) for p in puntuales]
        )

        return {
            "available": True,
            "zona": crudo.get("zona"),
            "latido": {
                "minuto": minuto,
                "horas": horas,
                "cadencia_minutos": int(
                    latido.get("cadencia_minutos") or 60
                ),
            },
            "puntuales": puntuales,
            "cadencia_minutos": int(
                latido.get("cadencia_minutos") or 60
            ),
            "gracia_minutos": int(
                crudo.get("gracia_minutos") or 0
            ),
            "todos_los_minutos": todos,
            "reason": (
                f"{len(horas)} latidos al minuto :{minuto:02d} y "
                f"{len(puntuales)} disparos puntuales, hora de "
                f"{crudo.get('zona')}. Configurados en "
                f"{crudo.get('donde_se_configura')}, que el "
                f"codigo no puede leer: esto es lo que se ESPERA."
            ),
        }

    except Exception as error:                      # noqa: BLE001
        return {
            **vacio,
            "reason": (
                f"No se pudo leer la declaracion de disparos: "
                f"{type(error).__name__}: {error}"
            ),
        }


def _minutos(hhmm: str) -> int:
    """"HH:MM" -> minutos desde medianoche."""

    horas, minutos = str(hhmm).strip().split(":")

    return int(horas) * 60 + int(minutos)


def que_disparo_toca(minutos_de_madrid) -> dict:
    """
    A esa hora de Madrid, ¿que disparo tocaba, y de que clase?

    Sirve para dos cosas distintas y conviene no confundirlas:

        - saber si un ciclo entro a su hora
        - saber QUE clase de disparo es, que ya no se puede
          deducir del evento de GitHub

    LO SEGUNDO ES NUEVO Y ES IMPORTANTE

        Mientras existio el `schedule`, la zona de silencio
        distinguia el latido -`schedule`, que no escribe en la
        ventana- de los disparos deliberados. Ahora TODOS entran
        como `workflow_dispatch`, asi que el evento de GitHub ya
        no distingue nada: lo unico que los separa es LA HORA,
        contra esta declaracion.

    Forma fija. Nunca lanza.
    """

    vacio = {
        "available": False,
        "hay": False,
        "que": None,
        "minutos": None,
        "distancia": None,
        "reason": None,
    }

    try:
        decl = declaracion()

        if not decl["available"]:
            return {**vacio, "reason": decl["reason"]}

        ahora = int(minutos_de_madrid)

        candidatos = []

        for p in decl["puntuales"]:
            candidatos.append((_minutos(p["madrid"]), p["que"]))

        for h in decl["latido"]["horas"]:
            candidatos.append(
                (h * 60 + decl["latido"]["minuto"], "latido")
            )

        # La distancia da la vuelta a medianoche: 23:59 esta a un
        # minuto de 00:00, no a 1.439.
        def _dist(m: int) -> int:
            crudo = abs(m - ahora)

            return min(crudo, 24 * 60 - crudo)

        minuto, clase = min(
            candidatos, key=lambda x: _dist(x[0])
        )

        distancia = _dist(minuto)

        gracia = decl["gracia_minutos"]

        return {
            "available": True,
            "hay": distancia <= gracia,
            "que": clase,
            "minutos": minuto,
            "distancia": distancia,
            "reason": (
                f"El disparo declarado mas cercano es el de las "
                f"{minuto // 60:02d}:{minuto % 60:02d} "
                f"({clase}), a {distancia} min"
                + (
                    f", dentro de la gracia de {gracia}."
                    if distancia <= gracia
                    else (
                        f". Pasa de la gracia de {gracia}: a esa "
                        f"hora no tocaba ningun disparo."
                    )
                )
            ),
        }

    except Exception as error:                      # noqa: BLE001
        return {
            **vacio,
            "reason": (
                f"No se pudo mirar que disparo tocaba: "
                f"{type(error).__name__}: {error}"
            ),
        }
