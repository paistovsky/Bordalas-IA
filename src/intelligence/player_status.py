from typing import Optional


STATUS_OK = "OK"
STATUS_WARNING = "WARNING"
STATUS_DANGER = "DANGER"


def normalize_biwenger_status(
    player: dict,
) -> dict:

    status = player.get("status", "ok")
    fitness = player.get("fitness", [])

    alerts = []

    if status != "ok":
        alerts.append(
            f"Estado Biwenger: {status}"
        )

    if fitness:
        alerts.append(
            f"Fitness Biwenger: {fitness}"
        )

    return {
        "biwenger_status": status,
        "fitness": fitness,
        "alerts": alerts,
    }


def build_player_status(
    player: dict,
    injury: Optional[dict] = None,
    transfer: Optional[dict] = None,
    news: Optional[list] = None,
) -> dict:

    biwenger = normalize_biwenger_status(
        player
    )

    alerts = list(
        biwenger["alerts"]
    )

    risk_score = 0

    # -----------------------------------------
    # LESIONES
    # -----------------------------------------

    if injury:

        injury_status = injury.get(
            "status"
        )

        if injury_status == "injured":
            risk_score += 60
            alerts.append(
                "Jugador lesionado"
            )

        elif injury_status == "doubt":
            risk_score += 30
            alerts.append(
                "Jugador en duda"
            )

    # -----------------------------------------
    # TRASPASOS
    # -----------------------------------------

    if transfer:

        transfer_status = transfer.get(
            "status"
        )

        if transfer_status == "left_league":
            risk_score += 100
            alerts.append(
                "Ha abandonado LaLiga"
            )

        elif transfer_status == "confirmed":
            risk_score += 20
            alerts.append(
                "Traspaso confirmado"
            )

        elif transfer_status == "rumour":
            risk_score += 10
            alerts.append(
                "Rumor de traspaso"
            )

    # -----------------------------------------
    # ESTADO FINAL
    # -----------------------------------------

    risk_score = min(
        risk_score,
        100,
    )

    if risk_score >= 60:
        overall_status = STATUS_DANGER

    elif risk_score >= 20:
        overall_status = STATUS_WARNING

    else:
        overall_status = STATUS_OK

    return {
        "id": player["id"],
        "name": player["name"],
        "team_id": player.get("teamID"),

        "biwenger_status":
            biwenger["biwenger_status"],

        "fitness":
            biwenger["fitness"],

        "injury":
            injury,

        "transfer":
            transfer,

        "news":
            news or [],

        "risk_score":
            risk_score,

        "status":
            overall_status,

        "alerts":
            alerts,
    }