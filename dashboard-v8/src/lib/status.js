export async function fetchStatus() {
  const response = await fetch(`/data/status.json?t=${Date.now()}`, {
    cache: "no-store"
  });

  if (!response.ok) {
    throw new Error(`Telemetría HTTP ${response.status}`);
  }

  return response.json();
}

export function normalizeStatus(raw = {}) {
  const summary = raw.summary || {};
  const lineup = raw.lineup || {};
  const competitive = raw.competitive || {};
  const league = raw.league_center || {};
  const competition = raw.competition || league.competition || { standings: [] };
  const activity = raw.activity || [];
  const providedLastExecution = raw.last_execution || {};
  const lastExecution = providedLastExecution.action
    ? providedLastExecution
    : activity.find((item) => item.write_performed) || {};

  const activeOffers = competitive.offers || [];
  const activeKeys = new Set(
    activeOffers.map((offer) => `${offer.player_id}|${offer.rival_name}`)
  );

  const recentClosed = (competitive.recent_closed || []).filter(
    (offer) => !activeKeys.has(`${offer.player_id}|${offer.rival_name}`)
  );

  return {
    raw,
    meta: raw.meta || {},
    summary,
    solvency: raw.solvency || {},
    lineup,
    roster: raw.roster || { starters: lineup.players || [], substitutes: [], players: lineup.players || [] },
    competitive: {
      ...competitive,
      offers: activeOffers,
      recentClosed
    },
    now: raw.pepe_now || {},
    offers: raw.offers || [],
    listings: raw.listings || {},
    speculation: raw.speculation || {},
    activity,
    cycle: raw.cycle || {},
    lastExecution,
    nextAction: raw.next_action || {},
    decision: raw.decision || {},
    league,
    competition,
    laliga: league.laliga || {},

    // V10.14: telemetria nueva. Cada bloque se declara disponible
    // o no, para que la interfaz no invente lo que no ha medido.
    marketClock: raw.market_clock || { available: false },
    guardrail: raw.position_guardrail || { available: false },
    exposure: raw.exposure || { available: false },
    acquisition: raw.acquisition || { available: false },
    pointsMarket: raw.points_market || { calibrated: false },
    ledgerAudit: raw.ledger_audit || { available: false },
    rivalIntel: raw.rival_intelligence || { managers: [] },
    backoff: raw.backoff || { blocked: [], blocked_count: 0 },

    // La auditoria que el generador hace de si mismo. Si esto
    // dice que no cuadra, no se decide mirando la pantalla.
    consistency: raw.consistency || { available: false, ok: true, checks: [] }
  };
}
