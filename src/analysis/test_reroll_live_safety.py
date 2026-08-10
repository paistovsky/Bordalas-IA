from src.analysis.computer_offer_reroll_engine import (
    revalidate_reroll_offer,
)

from src.analysis.market_analyzer import (
    get_latest_snapshot,
    load_snapshot,
)


def main() -> None:
    snapshot_file = get_latest_snapshot()
    snapshot = load_snapshot(
        snapshot_file
    )

    offers = (
        snapshot.get(
            "market",
            {},
        )
        .get(
            "offers",
            [],
        )
        or []
    )

    offer_ids = [
        offer.get("id")
        for offer in offers
        if offer.get("id") is not None
    ]

    print()
    print("=" * 110)
    print("                  BORDALAS IA - REROLL LIVE SAFETY V1")
    print("=" * 110)
    print()
    print(f"Snapshot:                  {snapshot_file}")
    print(f"Ofertas raw snapshot:      {len(offer_ids)}")
    print()

    if not offer_ids:
        print("No hay ofertas para probar revalidacion negativa.")
    else:
        for offer_id in offer_ids:
            validation = revalidate_reroll_offer(
                snapshot=snapshot,
                offer_id=int(offer_id),
            )

            offer = validation.get(
                "offer",
                {},
            ) or {}

            names = ", ".join(
                player.get("name", "?")
                for player in offer.get(
                    "players",
                    [],
                )
            ) or "?"

            print(
                f"{names:<24} "
                f"offer_id={offer_id} "
                f"authorized={validation.get('authorized')} "
                f"status={validation.get('status')}"
            )

            if (
                validation.get("authorized")
                and
                offer.get("action") != "REROLL_CANDIDATE"
            ):
                raise SystemExit(
                    "ERROR: autorizacion LIVE sin REROLL_CANDIDATE."
                )

            if (
                validation.get("authorized")
                and
                not offer.get("reroll_safe")
            ):
                raise SystemExit(
                    "ERROR: autorizacion LIVE sin reroll_safe."
                )

    # Oferta inexistente: siempre debe abortar.
    fake_id = 999999999999
    missing = revalidate_reroll_offer(
        snapshot=snapshot,
        offer_id=fake_id,
    )

    print()
    print(
        f"Oferta inexistente:        "
        f"authorized={missing.get('authorized')} "
        f"status={missing.get('status')}"
    )

    if missing.get("authorized"):
        raise SystemExit(
            "ERROR: una oferta inexistente ha sido autorizada."
        )

    print()
    print("REROLL LIVE SAFETY V1: OK")
    print("=" * 110)


if __name__ == "__main__":
    main()
