from datetime import date, datetime

from src.intelligence.bulk_player_mapper import (
    map_player,
)

from src.intelligence.external_status_cache import (
    get_cached_status,
    set_cached_status,
)

from src.intelligence.injuries import (
    get_player_sidelined,
)

from src.intelligence.transfers import (
    get_player_transfers,
)


OPEN_EVENT_MAX_AGE_DAYS = 90
RECENT_TRANSFER_DAYS = 180


def parse_date(
    value: str | None,
) -> date | None:

    if not value:
        return None

    try:
        return datetime.strptime(
            value,
            "%Y-%m-%d",
        ).date()

    except ValueError:
        return None


def analyze_sidelined(
    records: list[dict],
) -> dict:

    today = date.today()

    active_events = []
    historical_events = []

    for item in records:

        start_date = parse_date(
            item.get("start")
        )

        end_date = parse_date(
            item.get("end")
        )

        historical_events.append(
            item
        )

        if start_date is None:
            continue

        if (
            end_date is not None
            and start_date
            <= today
            <= end_date
        ):
            active_events.append(
                item
            )

            continue

        if end_date is None:

            age = (
                today - start_date
            ).days

            if (
                0 <= age
                <= OPEN_EVENT_MAX_AGE_DAYS
            ):
                active_events.append(
                    item
                )

    risk_score = 0
    alerts = []

    for item in active_events:

        event_type = (
            item.get("type")
            or "Unknown"
        )

        event_lower = (
            event_type.lower()
        )

        if "suspend" in event_lower:

            risk_score = max(
                risk_score,
                70,
            )

            alerts.append(
                f"Sanción activa: "
                f"{event_type}"
            )

        else:

            risk_score = max(
                risk_score,
                60,
            )

            alerts.append(
                f"Posible baja activa: "
                f"{event_type}"
            )

    return {
        "active":
            bool(active_events),

        "active_events":
            active_events,

        "historical_count":
            len(historical_events),

        "risk_score":
            risk_score,

        "alerts":
            alerts,
    }


def extract_latest_transfer(
    records: list[dict],
) -> dict | None:

    all_transfers = []

    for record in records:

        player = record.get(
            "player",
            {},
        )

        for transfer in record.get(
            "transfers",
            [],
        ):

            all_transfers.append(
                {
                    **transfer,

                    "external_player":
                        player,

                    "api_update":
                        record.get(
                            "update"
                        ),
                }
            )

    if not all_transfers:
        return None

    def transfer_sort_key(
        transfer: dict,
    ) -> date:

        parsed = parse_date(
            transfer.get("date")
        )

        return (
            parsed
            or date.min
        )

    all_transfers.sort(
        key=transfer_sort_key,
        reverse=True,
    )

    return all_transfers[0]


def analyze_transfers(
    records: list[dict],
    biwenger_team: str | None,
) -> dict:

    latest = extract_latest_transfer(
        records
    )

    if latest is None:

        return {
            "latest": None,
            "recent": False,
            "risk_score": 0,
            "alerts": [],
        }

    transfer_date = parse_date(
        latest.get("date")
    )

    today = date.today()

    recent = False

    if transfer_date:

        age = (
            today
            - transfer_date
        ).days

        recent = (
            0 <= age
            <= RECENT_TRANSFER_DAYS
        )

    teams = latest.get(
        "teams",
        {},
    )

    team_in = (
        teams
        .get("in", {})
        .get("name")
    )

    team_out = (
        teams
        .get("out", {})
        .get("name")
    )

    risk_score = 0
    alerts = []

    if recent:

        if (
            biwenger_team
            and team_in
            and team_in.lower()
            != biwenger_team.lower()
        ):

            risk_score = 40

            alerts.append(
                "Traspaso reciente no coincide "
                f"con Biwenger: {team_in}"
            )

        else:

            alerts.append(
                "Traspaso reciente detectado"
            )

    return {
        "latest":
            latest,

        "recent":
            recent,

        "team_in":
            team_in,

        "team_out":
            team_out,

        "risk_score":
            risk_score,

        "alerts":
            alerts,
    }


def get_external_player_status(
    snapshot: dict,
    player: dict,
) -> dict:

    biwenger_id = player["id"]

    # --------------------------------------------------
    # 1. CACHÉ EXTERNA
    # --------------------------------------------------

    cached = get_cached_status(
        biwenger_id
    )

    if cached:
        return cached

    # --------------------------------------------------
    # 2. MAPPING
    # --------------------------------------------------

    mapping = map_player(
        snapshot,
        player,
    )

    result = {
        "biwenger_id":
            biwenger_id,

        "name":
            player["name"],

        "mapping":
            mapping,

        "external_available":
            False,

        "sidelined":
            None,

        "transfers":
            None,

        "risk_score":
            0,

        "status":
            "SIN DATOS EXTERNOS",

        "alerts":
            [],

        "external_from_cache":
            False,
    }

    if not mapping.get(
        "safe_for_automatic_use",
        False,
    ):

        result["status"] = (
            "MAPPING NO VALIDADO"
        )

        result["alerts"].append(
            "Mapping externo no suficientemente fiable."
        )

        set_cached_status(
            biwenger_id,
            result,
        )

        return result

    external_id = mapping.get(
        "external_id"
    )

    if external_id is None:

        result["status"] = (
            "SIN ID EXTERNO"
        )

        set_cached_status(
            biwenger_id,
            result,
        )

        return result

    result[
        "external_available"
    ] = True

    # --------------------------------------------------
    # 3. BAJAS / SANCIONES
    # --------------------------------------------------

    try:

        records = (
            get_player_sidelined(
                external_id
            )
        )

        sidelined_analysis = (
            analyze_sidelined(
                records
            )
        )

        result["sidelined"] = (
            sidelined_analysis
        )

    except Exception as error:

        sidelined_analysis = {
            "risk_score": 0,
            "alerts": [],
        }

        result["alerts"].append(
            "No se pudieron consultar bajas: "
            f"{type(error).__name__}"
        )

    # --------------------------------------------------
    # 4. TRASPASOS
    # --------------------------------------------------

    try:

        records = (
            get_player_transfers(
                external_id
            )
        )

        transfer_analysis = (
            analyze_transfers(
                records,
                mapping.get(
                    "biwenger_team"
                ),
            )
        )

        result["transfers"] = (
            transfer_analysis
        )

    except Exception as error:

        transfer_analysis = {
            "risk_score": 0,
            "alerts": [],
        }

        result["alerts"].append(
            "No se pudieron consultar "
            "traspasos: "
            f"{type(error).__name__}"
        )

    # --------------------------------------------------
    # 5. RIESGO TOTAL
    # --------------------------------------------------

    risk_score = max(
        sidelined_analysis.get(
            "risk_score",
            0,
        ),
        transfer_analysis.get(
            "risk_score",
            0,
        ),
    )

    result["risk_score"] = (
        risk_score
    )

    result["alerts"].extend(
        sidelined_analysis.get(
            "alerts",
            [],
        )
    )

    result["alerts"].extend(
        transfer_analysis.get(
            "alerts",
            [],
        )
    )

    if risk_score >= 60:

        result["status"] = (
            "PELIGRO"
        )

    elif risk_score >= 30:

        result["status"] = (
            "REVISAR"
        )

    else:

        result["status"] = (
            "OK"
        )

    # --------------------------------------------------
    # 6. GUARDAR RESULTADO 6 HORAS
    # --------------------------------------------------

    set_cached_status(
        biwenger_id,
        result,
    )

    return result