"""
Cada decision cita la regla que la sostiene. Y la que no, se ve.

LA REGLA 17, QUE ES LA QUE PIDE ESTO

    "Cuando Pepe ficha, vende, alinea o rechaza, dice que regla de
     este documento la sostiene. Una decision sin cita es una
     decision que nadie ha escrito, y esas son las que hay que
     descubrir."

    Lo valioso no es la lista de las que citan. Es la OTRA: las
    que Pepe toma por un motivo que no esta escrito en ninguna
    parte.

POR QUE SE LEE EL DOCUMENTO EN VEZ DE COPIARLO

    El encargo avisa: "no conviertas la doctrina en constantes
    nuevas, es un documento de intencion".

    Asi que aqui no hay dieciocho reglas escritas a mano. Se lee
    `docs/DOCTRINA.md` y se saca de ahi la tabla. Si el dueño
    añade una regla, renumera o cambia un estado, esto lo sigue
    solo; y si alguien borra el documento, este modulo lo dice en
    vez de seguir citando reglas que ya no existen.

    El documento esta versionado en git, asi que es un fixture:
    no es estado mutable como `data/`.

LO QUE NO SE HACE: FORZAR LA CITA

    "No fuerces la cita. Si una decision no encaja en ninguna
     regla, que salga sin cita y en la lista. Un mapeo inventado
     para que no haya huecos es peor que los huecos."

    Por eso hay decisiones que salen sin regla A PROPOSITO, y
    cada una lleva escrito por que no encaja. Son el resultado
    util de este modulo.

NO DECIDE NADA

    Etiqueta decisiones que ya se han tomado. No cambia ninguna.
"""

from __future__ import annotations

import re

from pathlib import Path


DOCUMENTO = Path("docs") / "DOCTRINA.md"


# ============================================================
# EL MAPEO
# ============================================================
#
# Codigo de decision -> numero de regla.
#
# Solo se mapea lo que de verdad encaja. Un `None` con motivo es
# una respuesta, no un agujero que tapar: dice que Pepe hace algo
# que nadie ha escrito todavia.
CITAS = {
    # --- El tablero de fichajes -------------------------------
    "SIN_VALOR": (
        1,
        "No mejora el once, y el once es lo unico que marca.",
    ),
    "NO_COMPENSA": (
        9,
        "No llega al liston de rendimiento de la via de comprar "
        "lo que sube.",
    ),
    "CAE": (
        13,
        "Cae, y quien cae vuelve a caer el 90,7 % de las veces.",
    ),
    "RITMO_INSUFICIENTE": (
        9,
        "No sube lo bastante al dia para la via de la rampa.",
    ),
    "SIN_RESPALDO": (
        18,
        "Su tramo del retrotest ya no rinde el liston: un umbral "
        "sin numero detras no sostiene una compra.",
    ),

    # --- El once ---------------------------------------------
    "NO_MEJORA_JERARQUIA": (
        7,
        "No mejora la calidad del once.",
    ),
    "NO_MEJORA_TITULARIDAD": (
        7,
        "No mejora la certeza de jugar, que se pagaba demasiado "
        "cara.",
    ),
    "PIERDE_TITULARIDAD": (
        7,
        "Empeora la certeza de jugar sin dar calidad a cambio.",
    ),
    "NO_MEJORA": (
        1,
        "No mejora el once.",
    ),

    # --- Las vias ---------------------------------------------
    "SPECULATION": (
        9,
        "Se compra por la rampa de precio, que es la via de "
        "comprar lo que sube.",
    ),
    "HOLD": (
        9,
        "Se compra para tenerlo mientras sube: la misma via, con "
        "horizonte.",
    ),

    # --- El dinero -------------------------------------------
    "PROTEGIDA": (
        16,
        "Se protege para llegar en positivo a T-6 h.",
    ),
    "RESERVA_SOLVENCIA": (
        16,
        "Se reserva para llegar en positivo a T-6 h.",
    ),
}


# Decisiones que NO citan ninguna regla, con el motivo escrito.
# Esta es la lista que pidio el encargo.
SIN_REGLA = {
    "SUPERA_PRESUPUESTO": (
        "El tope por operacion no esta en la doctrina. Hay reglas "
        "sobre que comprar y cuando, ninguna sobre cuanto se "
        "puede poner de una vez. Y ese tope ya salio una vez de "
        "anidar dos fracciones sin que nadie lo decidiera."
    ),
    "NO_DISPONIBLE": (
        "La disponibilidad -lesion, sancion- no aparece en la "
        "doctrina. Es obvia, y por eso mismo nadie la escribio."
    ),
    "NO_SE_TOCA_UN_DIOS": (
        "Sale de una orden del dueño del 18/08 -'los Dios juegan "
        "siempre salvo 0 % motivado'- que nunca entro en el "
        "documento. La regla 7 dice justo lo contrario en "
        "espiritu: calidad por encima de certeza de jugar."
    ),
    "SIN_PRECIO": (
        "Un jugador sin precio de mercado valido no se puede "
        "valorar ni pujar. Es higiene de datos, no doctrina: "
        "ninguna de las dieciocho reglas habla de que hacer "
        "cuando falta el dato, porque se da por hecho."
    ),
    "MONITOR_OFFERS": (
        "Gestionar las ofertas que ENTRAN no esta en la doctrina. "
        "Las dieciocho reglas hablan de comprar, vender, alinear "
        "y llegar en positivo; ninguna de que hacer cuando otro "
        "manager puja por lo nuestro. Es un hueco de verdad, y de "
        "los grandes: es la decision que mas veces toma el ciclo."
    ),
    "SIN_RITMO": (
        "Higiene de datos: sin ritmo medido no se valora a "
        "ciegas. Es practica de la casa y no esta escrita como "
        "regla."
    ),
}


def safe_int(value, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


# ============================================================
# LEER EL DOCUMENTO
# ============================================================


def cargar_reglas(path: Path | None = None) -> dict:
    """
    Las dieciocho reglas, leidas del documento.

    Forma fija: las mismas claves haya documento o no.
    """

    vacio = {
        "available": False,
        "version": None,
        "rules": {},
        "count": 0,
        "reason": None,
    }

    documento = path or DOCUMENTO

    try:
        if not documento.exists():
            return {
                **vacio,
                "reason": (
                    f"No se encuentra {documento}: sin documento "
                    f"no se puede citar ninguna regla."
                ),
            }

        texto = documento.read_text(encoding="utf-8")

        version = None

        marca = re.search(
            r"\*\*Versi[oó]n\s+([0-9.]+)", texto
        )

        if marca:
            version = marca.group(1)

        reglas = {}

        # La tabla del final: | 4 | Mas delanteros... | hecho |
        for numero, titulo, estado in re.findall(
            r"^\|\s*(\d+)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|$",
            texto,
            re.MULTILINE,
        ):
            reglas[int(numero)] = {
                "number": int(numero),
                "title": titulo.strip(),
                "state": (
                    estado.replace("*", "").strip()
                ),
            }

        if not reglas:
            return {
                **vacio,
                "version": version,
                "reason": (
                    "El documento no tiene la tabla de reglas: no "
                    "se puede citar sin ella."
                ),
            }

        return {
            "available": True,
            "version": version,
            "rules": reglas,
            "count": len(reglas),
            "reason": None,
        }

    except Exception as error:                       # noqa: BLE001
        return {
            **vacio,
            "reason": (
                f"No se pudo leer la doctrina: "
                f"{type(error).__name__}: {error}"
            ),
        }


# ============================================================
# CITAR UNA DECISION
# ============================================================


def citar(codigo, reglas: dict | None = None) -> dict:
    """
    Que regla sostiene esta decision, si es que alguna.

    Forma fija. `rule` a None NO es un fallo: es el resultado
    interesante.
    """

    catalogo = (
        reglas
        if reglas is not None
        else cargar_reglas()
    )

    disponibles = (catalogo or {}).get("rules") or {}

    clave = str(codigo or "").strip().upper()

    salida = {
        "decision": clave or None,
        "rule": None,
        "title": None,
        "state": None,
        "why": None,
        "uncited_reason": None,
    }

    if not clave:
        salida["uncited_reason"] = "Decision sin codigo."
        return salida

    if clave in CITAS:

        numero, porque = CITAS[clave]
        regla = disponibles.get(numero) or {}

        salida.update({
            "rule": numero,
            "title": regla.get("title"),
            "state": regla.get("state"),
            "why": porque,
        })

        if not regla:
            salida["uncited_reason"] = (
                f"La decision cita la regla {numero} y esa regla "
                f"no esta en el documento."
            )

        return salida

    salida["uncited_reason"] = SIN_REGLA.get(
        clave,
        (
            "Esta decision no encaja en ninguna regla escrita. "
            "No se le inventa una: si se repite, hay que "
            "escribirla o quitarla."
        ),
    )

    return salida


# ============================================================
# LA AUDITORIA
# ============================================================


def _decisiones(status: dict) -> list:
    """Todas las decisiones que Pepe publica hoy, con su sitio."""

    estado = status or {}

    salida = []

    for objetivo in (
        (estado.get("acquisition") or {}).get("targets") or []
    ):
        salida.append({
            "where": "mercado",
            "subject": objetivo.get("name"),
            "decision": objetivo.get("decision"),
        })

        if objetivo.get("xi_decision"):
            salida.append({
                "where": "once",
                "subject": objetivo.get("name"),
                "decision": objetivo.get("xi_decision"),
            })

    for fila in (
        (estado.get("season_horizon") or {}).get("rows") or []
    ):
        if fila.get("intent"):
            salida.append({
                "where": "horizonte",
                "subject": fila.get("name"),
                "decision": fila.get("intent"),
            })

    ciclo = estado.get("decision") or {}

    if ciclo.get("action"):
        salida.append({
            "where": "ciclo",
            "subject": "el ciclo",
            "decision": ciclo.get("action"),
        })

    return salida


def auditar(status: dict | None, path: Path | None = None) -> dict:
    """
    Cuantas decisiones citan regla y cuales no citan ninguna.

    Nunca lanza. Forma fija.
    """

    vacio = {
        "available": False,
        "version": None,
        "rules": 0,
        "decisions": 0,
        "cited": 0,
        "uncited": 0,
        "cited_percent": None,
        "by_rule": [],
        "without_rule": [],
        "reason": None,
    }

    try:
        catalogo = cargar_reglas(path)

        if not catalogo["available"]:
            return {**vacio, "reason": catalogo["reason"]}

        decisiones = _decisiones(status)

        if not decisiones:
            return {
                **vacio,
                "available": False,
                "version": catalogo["version"],
                "rules": catalogo["count"],
                "reason": (
                    "Pepe no ha publicado ninguna decision en esta "
                    "foto."
                ),
            }

        por_regla = {}
        sin_regla = {}

        citadas = 0

        for entrada in decisiones:

            cita = citar(entrada["decision"], catalogo)

            if cita["rule"] is not None:

                citadas += 1

                ficha = por_regla.setdefault(
                    cita["rule"],
                    {
                        "rule": cita["rule"],
                        "title": cita["title"],
                        "state": cita["state"],
                        "count": 0,
                        "examples": [],
                    },
                )

                ficha["count"] += 1

                if len(ficha["examples"]) < 3:
                    ficha["examples"].append(
                        f"{entrada['subject']} "
                        f"({entrada['decision']})"
                    )

                continue

            ficha = sin_regla.setdefault(
                str(entrada["decision"]),
                {
                    "decision": entrada["decision"],
                    "count": 0,
                    "where": set(),
                    "why": cita["uncited_reason"],
                    "examples": [],
                },
            )

            ficha["count"] += 1
            ficha["where"].add(entrada["where"])

            if len(ficha["examples"]) < 3:
                ficha["examples"].append(entrada["subject"])

        huerfanas = [
            {
                "decision": f["decision"],
                "count": f["count"],
                "where": sorted(f["where"]),
                "why": f["why"],
                "examples": f["examples"],
            }
            for f in sorted(
                sin_regla.values(),
                key=lambda f: -f["count"],
            )
        ]

        total = len(decisiones)

        return {
            "available": True,
            "version": catalogo["version"],
            "rules": catalogo["count"],
            "decisions": total,
            "cited": citadas,
            "uncited": total - citadas,
            "cited_percent": round(100 * citadas / total, 1),
            "by_rule": sorted(
                por_regla.values(),
                key=lambda f: -f["count"],
            ),
            "without_rule": huerfanas,
            "reason": _reason(total, citadas, huerfanas),
        }

    except Exception as error:                       # noqa: BLE001
        return {
            **vacio,
            "reason": (
                f"No se pudo auditar: "
                f"{type(error).__name__}: {error}"
            ),
        }


def _reason(total: int, citadas: int, huerfanas: list) -> str:

    porcentaje = round(100 * citadas / total, 1) if total else 0

    frase = (
        f"{citadas} de {total} decisiones ({porcentaje} %) citan "
        f"una regla de la doctrina."
    )

    if not huerfanas:
        return frase + " Ninguna se queda sin cita."

    mayor = huerfanas[0]

    return frase + (
        f" Las que no: "
        + ", ".join(
            f"{h['decision']} ({h['count']})"
            for h in huerfanas[:4]
        )
        + f". La mas repetida es «{mayor['decision']}», "
        f"{mayor['count']} veces: son las decisiones que Pepe "
        f"toma por un motivo que nadie ha escrito."
    )
