"""
El pronostico del ojeador, enchufado — y apagado.

EL SINTOMA (15/09/2026)

    El carril rechazaba candidatos diciendo "como especulacion
    rinde un 0,1443 % y se exige al menos un 3 %". Nueve rechazos
    distintos de la misma foto, y los NUEVE con el mismo numero
    hasta el cuarto decimal — con pronosticos del ojeador que
    iban del +0,30 % al +4,55 %.

    Un instrumento que acierta el 90 % enchufado a ninguna parte.

DE DONDE SALIA ESE 0,1443 %, DESPEJADO

        rendimiento = valor_esperado / importe
                    = p x (valor - importe) / importe

    Con `p` constante -la curva de pujas reparte 1/7 a cada uno
    de sus siete tramos por construccion, porque son CUANTILES- y
    con el importe fijado en `valor / 1,01`, sale:

        (1/7) x (1,01 - 1) = 0,1429 %

    constante para todo el mundo. El pronostico del jugador no
    entra en ningun sitio de esa cuenta: `valor` era el precio por
    la prima del Computer, que es la misma para todos.

LO QUE PUBLICA EL OJEADOR ES EL PASADO, Y ESTA MEDIDO

    Las tres fuentes publican el movimiento del ULTIMO mercado.
    No es una sospecha: se comprobo contra nuestra propia serie de
    precios sobre el informe del 05/09.

        |lo que publica - el movimiento YA OCURRIDO|
            FUTBOLFANTASY   0,000 pp (n=95)
            ANALITICA       0,025 pp (n=97)
            COMUNIATE       0,026 pp (n=94)
            COMUNIATE_PULSO 29,254 pp (n=58)

    Las tres buenas publican EL MISMO HECHO -el cambio de precio
    de Biwenger- con tres decimales de diferencia. "542 de 543
    con las tres fuentes de acuerdo" no es un consenso de tres
    opiniones: son tres copias de un mismo dato.

    Y COMUNIATE_PULSO no publica ese hecho: publica otra cosa.

POR QUE ESO SIGUE VALIENDO: LA PERSISTENCIA, MEDIDA

    Que sea el pasado no lo invalida, porque en Biwenger el
    pasado predice el futuro con una fuerza que asusta. Medido
    sobre nuestra serie, 30 dias, 13.073 pares:

        cuando ayer se movio >= 1 punto (n=6.983)
            hoy va en el MISMO sentido    99,2 % subiendo
                                          99,3 % bajando
            y el tamaño se conserva       factor 0,93

    Por tramos, el factor va de 0,86 a 0,97. Se usa el global.

LA FORMULA, EN TRES LINEAS

    1. Cada fuente aporta el movimiento que OBSERVA.
    2. Su aportacion se recorta DOS veces: por su acierto de
       direccion medido —x(2·acierto-1)— y por su error de
       tamaño —x max(0, 1 - error/|movimiento|)—.
    3. La estimacion es la media de lo que sobrevive, ponderada
       por la CALIDAD de cada fuente, y multiplicada por la
       PERSISTENCIA. Si no sobrevive nada: SIN PRONOSTICO.

    El segundo recorte es el que hace el trabajo. El error de
    tamaño de FutbolFantasy es 3,98 puntos y la magnitud que
    publica anda por el 1 %: para un movimiento pequeño el
    recorte lo deja en CERO, y solo los movimientos grandes
    sobreviven. Es lo que pedia el encargo —"el error de tamaño
    recorta la estimacion, no la adorna"— y tiene el efecto que
    interesa: pasan MENOS candidatos, no mas.

SIN OJEADOR NO HAY NUMERO (doctrina 24)

    Un jugador sin lectura, o con las fuentes contradiciendose,
    devuelve `available: False` y "SIN_PRONOSTICO". Nunca una
    constante, nunca un cero disfrazado de estimacion.

LOS PESOS NO SE ESCRIBEN: SE LEEN DEL LIBRO

    El acierto y el error de cada fuente salen del libro de
    acierto del ojeador. Una fuente sin medicion NO pesa — no se
    le presume un acierto medio. El dia que el libro diga que
    COMUNIATE_PULSO acierta el 72,9 % con 35,7 puntos de error,
    pesara lo que eso valga y no lo que valga COMUNIATE.

APAGADO

    Este modulo no lo llama nadie todavia. `ENCENDIDO = False` y
    `esta_encendido()` es lo unico que hay que tocar para
    enchufarlo. La luz la da el dueño con la tabla delante.

SIN RELOJ, SIN DISCO, SIN RED

    Todo entra por argumento.
"""

from __future__ import annotations

import statistics


# EL INTERRUPTOR. Se pone el enchufe; la luz la da el dueño.
ENCENDIDO = False

# LA PERSISTENCIA, MEDIDA (15/09/2026)
#
#     Mediana de lo que se mueve un precio el dia siguiente
#     contra lo que se movio el anterior, sobre 6.983 pares con
#     movimiento de al menos un punto. Por tramos va de 0,86 a
#     0,97; se usa el global.
#
#     NO ES UN UMBRAL DEL MOTOR: no cierra ninguna via. Es una
#     propiedad del mercado de Biwenger, y `medir_persistencia`
#     la recalcula desde la serie que se le pase.
PERSISTENCIA = 0.934

PERSISTENCIA_N = 6_983

# Por debajo de esto, un movimiento no se distingue del redondeo
# del propio Biwenger, que mueve los precios en saltos de 10.000.
MOVIMIENTO_MINIMO_PUNTOS = 1.0

SIN_PRONOSTICO = "SIN_PRONOSTICO"


def safe_float(value, default=None):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def esta_encendido() -> bool:
    """
    Lo unico que hay que tocar para enchufarlo.

    Mientras devuelva False, `estimacion` sigue calculando y
    publicando —para poder enseñar el antes y el despues— pero
    nadie la usa para decidir.
    """

    return bool(ENCENDIDO)


# ============================================================
# LA PERSISTENCIA SE MIDE, NO SE ESCRIBE
# ============================================================


def medir_persistencia(
    series: dict,
    minimo: float = MOVIMIENTO_MINIMO_PUNTOS,
) -> dict:
    """
    ¿Cuanto de lo que se movio ayer se repite hoy?

    `series` es {jugador: [precio del dia 1, dia 2, ...]}, en
    orden. Forma fija, nunca lanza.

    LA CONSTANTE `PERSISTENCIA` ES UNA AFIRMACION SOBRE BIWENGER,
    y una afirmacion sobre el mundo que no se puede recalcular es
    una opinion con cara de constante. Esto la recalcula.
    """

    pares = []

    for precios in (series or {}).values():

        limpios = [p for p in (precios or []) if p]

        for i in range(2, len(limpios)):

            antes, medio, despues = (
                limpios[i - 2],
                limpios[i - 1],
                limpios[i],
            )

            if not antes or not medio:
                continue

            ayer = (medio - antes) / antes * 100.0
            hoy = (despues - medio) / medio * 100.0

            pares.append((ayer, hoy))

    fuertes = [p for p in pares if abs(p[0]) >= minimo]

    if not fuertes:
        return {
            "available": False,
            "n": 0,
            "factor": None,
            "misma_direccion": None,
            "reason": (
                "No hay ni un par con movimiento suficiente: sin "
                "muestra no se mide la persistencia."
            ),
        }

    # El signo se normaliza: interesa si el movimiento CONTINUA,
    # no si sube o baja.
    ayer = statistics.median(abs(a) for a, _ in fuertes)

    hoy = statistics.median(
        h if a > 0 else -h for a, h in fuertes
    )

    vivos = [p for p in fuertes if p[1] != 0]

    return {
        "available": True,
        "n": len(fuertes),
        "factor": round(hoy / ayer, 4) if ayer else None,
        "misma_direccion": (
            round(
                sum(
                    1
                    for a, h in vivos
                    if (a > 0) == (h > 0)
                )
                / len(vivos),
                4,
            )
            if vivos
            else None
        ),
        "n_direccion": len(vivos),
        "reason": (
            f"Sobre {len(fuertes):,} pares con movimiento de al "
            f"menos {minimo} punto: lo de ayer se repite con "
            f"factor {hoy / ayer:.3f}."
            if ayer
            else "Sin movimiento medible ayer."
        ),
    }


# ============================================================
# LO QUE VALE CADA FUENTE
# ============================================================


def peso_de_la_fuente(medicion: dict | None, magnitud) -> dict:
    """
    Cuanto vale lo que dice una fuente sobre UN movimiento.

    Dos recortes, y los dos salen del libro de acierto:

        DIRECCION   x (2 x acierto - 1). Acertar el 50 % es no
                    saber nada y vale 0; acertar el 97,1 % vale
                    0,942; acertar el 72,9 % vale 0,458.

        TAMAÑO      x max(0, 1 - error / |magnitud|). Si la
                    fuente se equivoca en mas de lo que mide, su
                    tamaño no es informacion.

    Una fuente sin medicion en el libro NO pesa. No se le presume
    un acierto medio: se dice que no se sabe.
    """

    vacio = {
        "usable": False,
        "direccion": None,
        "tamano": None,
        "peso": 0.0,
        "n": 0,
        "reason": None,
    }

    if not medicion:
        return {
            **vacio,
            "reason": (
                "La fuente no esta medida en el libro de "
                "acierto: no pesa."
            ),
        }

    decididas = int(medicion.get("decided") or 0)

    acierto = safe_float(medicion.get("hit_rate"))

    if not decididas or acierto is None:
        return {
            **vacio,
            "n": decididas,
            "reason": (
                f"La fuente tiene {decididas} predicciones "
                f"decididas: sin acierto medido no pesa."
            ),
        }

    # El acierto viaja en tanto por ciento en el libro.
    p = acierto / 100.0 if acierto > 1 else acierto

    direccion = max(0.0, 2.0 * p - 1.0)

    error = safe_float(
        medicion.get("mean_magnitude_error_percent")
    )

    tamano = 0.0

    if error is not None and abs(safe_float(magnitud, 0.0) or 0.0):
        tamano = max(
            0.0,
            1.0 - abs(error) / abs(float(magnitud)),
        )

    elif error is None:
        # Sin error medido no se puede recortar el tamaño, asi
        # que el tamaño no se usa: solo la direccion.
        tamano = 0.0

    peso = direccion * tamano

    return {
        "usable": peso > 0,
        "direccion": round(direccion, 4),
        "tamano": round(tamano, 4),
        "peso": round(peso, 6),
        "n": decididas,
        "reason": (
            f"Acierta el {100 * p:.1f} % (n={decididas}) y se "
            f"equivoca {error:.2f} puntos en el tamaño sobre un "
            f"movimiento de {abs(float(magnitud)):.2f}."
            if error is not None
            else f"Acierta el {100 * p:.1f} % (n={decididas}) y "
            f"no tiene error de tamaño medido."
        ),
    }


# ============================================================
# LA ESTIMACION
# ============================================================


def estimacion(
    ficha: dict | None,
    libro: dict | None,
    *,
    horizonte: int = 1,
    persistencia: float = PERSISTENCIA,
) -> dict:
    """
    Cuanto se espera que suba ESTE jugador, segun el ojeador.

    `ficha` es la entrada del informe del ojeador para un
    jugador: `{"signals": [...]}`. `libro` es
    `scout_accuracy.summary()["sources"]`.

    Forma fija, nunca lanza. Devuelve el porcentaje esperado a un
    dia, o `available: False` con el motivo.
    """

    vacio = {
        "available": False,
        "percent_per_day": None,
        "decision": SIN_PRONOSTICO,
        "sources": [],
        "agreement": None,
        "reason": None,
    }

    try:
        señales = [
            s
            for s in ((ficha or {}).get("signals") or [])
            if isinstance(s, dict)
            and s.get("horizon_days") == horizonte
        ]

        if not señales:
            return {
                **vacio,
                "reason": (
                    f"El ojeador no dice nada de este jugador a "
                    f"{horizonte} dia(s)."
                ),
            }

        medidas = (libro or {})

        aportaciones = []

        detalle = []

        for señal in señales:

            fuente = señal.get("source")

            magnitud = safe_float(señal.get("magnitude_percent"))

            if magnitud is None:
                continue

            valor = peso_de_la_fuente(
                medidas.get(fuente), magnitud
            )

            detalle.append(
                {
                    "source": fuente,
                    "magnitude_percent": magnitud,
                    **valor,
                }
            )

            if valor["usable"]:
                aportaciones.append(
                    (valor["peso"], valor["n"], magnitud)
                )

        if not aportaciones:
            return {
                **vacio,
                "sources": detalle,
                "reason": (
                    "Ninguna fuente sobrevive a su propio error "
                    "medido: no hay pronostico que dar."
                ),
            }

        # LAS QUE SOBREVIVEN TIENEN QUE DECIR LO MISMO.
        #
        #     Si una dice que sube y otra que baja, la media
        #     daria un numero pequeño con cara de certeza. Eso es
        #     peor que no saber.
        signos = {1 if m > 0 else -1 for _, _, m in aportaciones}

        if len(signos) > 1:
            return {
                **vacio,
                "sources": detalle,
                "agreement": "CONTRADICTORIAS",
                "reason": (
                    "Las fuentes que pesan se contradicen en la "
                    "direccion: sin pronostico."
                ),
            }

        # EL RECORTE MULTIPLICA LA MAGNITUD, NO SOLO LA MEZCLA.
        #
        #     Primera version: el peso solo ponderaba la media, y
        #     COMUNIATE_PULSO —35,71 puntos de error sobre un
        #     movimiento de 36,6— colaba un +34,18 %/dia como
        #     unica fuente. El peso decidia CUANTO contaba su
        #     opinion, no cuanto recortaba su numero.
        #
        #     Asi que cada fuente aporta `magnitud x peso`, y la
        #     media pondera esas aportaciones ya recortadas por
        #     el `n` con que se midio la fuente. El encargo lo
        #     decia: el error de tamaño RECORTA la estimacion.
        #     Y LA MEZCLA PONDERA POR LA CALIDAD, NO POR EL `n`.
        #
        #     Segunda version: ponderaba por el `n` con que se
        #     midio cada fuente, y entonces mandaba la PEOR por
        #     ser la mas prolifica — FutbolFantasy tiene 7.579
        #     decididas y 3,98 puntos de error, asi que tres
        #     fuentes de acuerdo en +4,55 daban MENOS que
        #     COMUNIATE sola. El `n` mide cuanto la hemos
        #     observado, no cuanto vale.
        #
        #     El encargo lo pedia asi: "cada fuente pesa segun SU
        #     acierto medido".
        arriba = sum(
            peso * (magnitud * peso)
            for peso, _, magnitud in aportaciones
        )

        abajo = sum(peso for peso, _, _ in aportaciones)

        if not abajo:
            return {
                **vacio,
                "sources": detalle,
                "reason": "Los pesos suman cero: sin pronostico.",
            }

        observado = arriba / abajo

        esperado = observado * float(persistencia)

        return {
            "available": True,
            "percent_per_day": round(esperado, 4),
            "observed_percent": round(observado, 4),
            "persistence": float(persistencia),
            "decision": "PRONOSTICO",
            "sources": detalle,
            "agreement": (
                "UNANIMOUS" if len(aportaciones) > 1 else "SINGLE"
            ),
            "n_sources": len(aportaciones),
            "reason": (
                f"{len(aportaciones)} fuente(s) util(es) "
                f"observan {observado:+.2f} % y la persistencia "
                f"medida ({persistencia:.3f}) lo deja en "
                f"{esperado:+.2f} % al dia."
            ),
        }

    except Exception as error:                      # noqa: BLE001
        return {
            **vacio,
            "reason": (
                f"No se pudo estimar: "
                f"{type(error).__name__}: {error}"
            ),
        }
