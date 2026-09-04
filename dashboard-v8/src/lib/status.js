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

    // LA COLA DE DECISIONES SALIA VACIA (20/08/2026)
    //
    // `priorities` llega en el JSON con las entradas del ciclo y
    // este normalizador no la copiaba. La columna "COLA DE
    // DECISIONES" se pintaba en blanco, y es justo la que
    // explica por que Pepe hace una cosa y no otra.
    //
    // Septima vez en dos dias que un dato se calcula, se publica
    // y se pierde en el ultimo metro.
    priorities: raw.priorities || [],

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

    // LAS PLANTILLAS DE LA LIGA (20/08/2026)
    //
    // La propia y las seis de los rivales, con la misma ficha:
    // jerarquia, pronostico de titularidad, lesion y sancion.
    // Salen de `standings[].lineup.players + discarded`, que ya
    // venia en el snapshot y no miraba nadie.
    rivalSquads: raw.rival_squads || { available: false, managers: [] },

    // EL MARCADOR (20/08/2026)
    //
    // La nota del once jornada a jornada: lo que puntuo contra lo
    // que podia haber puntuado con la misma plantilla. Llega
    // siempre, aunque no haya ninguna jornada cerrada, para que
    // la seccion pueda decir "todavia no hay nada" en vez de
    // desaparecer.
    marcador: raw.marcador || { available: false },

    // EL LIBRO DE PUJAS (05/09/2026)
    //
    // Se escribe desde el 03/09 y no lo leia esta pantalla. Es lo
    // unico que contesta a "¿por cuanto nos ganan?". Llega
    // siempre, aunque venga a cero, para poder decir "todavia no
    // hay nada" en vez de desaparecer.
    bidOutcomes: raw.bid_outcomes || { available: false, placed: 0 },

    // EN QUE CARRERA VA PEPE (05/09/2026)
    //
    // Puesto, distancia al lider, ritmo necesario y brecha de
    // plantilla. FASE OBSERVADOR: ningun motor lo lee, y esta
    // pantalla tampoco decide con ello.
    race: raw.race || { available: false, managers: [] },

    // La segunda opinion: que vale cada candidato de aqui a la
    // jornada 38, al lado de lo que vale hoy.
    seasonHorizon: raw.season_horizon || { available: false, rows: [] },

    // A quien ficharia si pudiera llenar un hueco de plantilla.
    rosterExpansion: raw.roster_expansion || {
      available: false,
      candidates: []
    },

    // La auditoria que el generador hace de si mismo. Si esto
    // dice que no cuadra, no se decide mirando la pantalla.
    consistency: raw.consistency || { available: false, ok: true, checks: [] }
  };
}
