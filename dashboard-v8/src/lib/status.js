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

    // EL OJEADOR (06/09/2026)
    //
    // Lo que tres webs dicen del precio de cada jugador, con su
    // libro de acierto y los que no se pudieron emparejar.
    // FASE OBSERVADOR: ningun motor lo lee, y esta pantalla
    // tampoco decide con ello.
    scout: raw.scout || { available: false, sources: {}, unmatched: [] },

    // EL OJEADOR DE PRENSA (05/09/2026)
    //
    // Lo unico que no copia el precio de Biwenger. Observador:
    // se publica al lado, no decide.
    press: raw.press || {
      available: false,
      sources: {},
      items: [],
      unmatched: []
    },

    // LA CONCENTRACION (10/09/2026)
    //
    // Cuanto pesa el jugador mas caro y cuantos hay del
    // mismo club. Yamal son el 41 % de la plantilla.
    concentration: raw.concentration || {
      available: false,
      players: [],
      teams: [],
      breaches: []
    },

    // EL ORDEN DE VENTA (11/09/2026)
    //
    // A quien le toca salir cuando haga falta caja. Observador:
    // se calcula y se enseña, no vende.
    saleOrder: raw.sale_order || {
      available: false,
      queue: [],
      excluded: [],
      blocked: []
    },

    // LA DOCTRINA (20/09/2026)
    //
    // Las dieciocho reglas de docs/DOCTRINA.md aplicadas a lo que
    // Pepe decide: que decisiones citan una y CUALES NO CITAN
    // NINGUNA, los recien ascendidos, el embudo del mercado y el
    // activo que pesa demasiado.
    doctrina: raw.doctrina || {
      available: false,
      citations: { available: false },
      funnel: { available: false }
    },

    // LA VARA DEL ONCE (18/09/2026)
    //
    // Los factores por posicion, de cuantas fichas sale cada uno,
    // el once que sale con ellos y el que salia sin ellos, y la
    // linea para apagarlos. Esto SI decide: elige el once.
    vara: raw.vara || { available: false, rows: [], active: null },

    // ¿SIGUE RESPALDADA LA VIA TENER? (17/09/2026)
    //
    // El tramo que la sostiene, comprobado en cada ciclo contra
    // el almacen de produccion. Si deja de rendir el liston, la
    // via se apaga sola y aqui se ve por que.
    holdRoute: raw.hold_route || { available: false, on: null, buckets: [] },

    // EL ONCE (17/09/2026)
    //
    // Los puntos que se quedaron sentados, si la vara con la que
    // se ordena el once mide igual en las cuatro posiciones, y en
    // que se diferencia nuestro equipo del de Mex -que va segundo
    // con nuestras mismas catorce fichas-.
    //
    // FASE OBSERVADOR: ningun motor lo lee.
    once: raw.once || {
      available: false,
      bench: { available: false, jornadas: [] },
      position_bias: { available: false, rows: [] },
      rival: { available: false }
    },

    // EL ARBITRO (16/09/2026)
    //
    // Quien tenia razon: el marcador de los rivales, el libro de
    // nuestros rechazos y los dias de historico que hay de verdad.
    arbiter: raw.arbiter || {
      available: false,
      managers: {},
      history: {}
    },

    // EL RELOJ DE LA SOLVENCIA (12/09/2026)
    //
    // Cuanto queda para el plazo -T-6h del primer partido-, si
    // la deuda llega tapada y quien gana el desempate.
    solvencyClock: raw.solvency_clock || {
      available: false,
      state: null,
      recommended_sale: null
    },

    // LO QUE SE CONSTRUYO EL 10/09 Y NO LLEGABA A NINGUNA
    // PANTALLA. Se calculaba en cada vuelta y no se veia.

    // Por quien va a pujar el ciclo en la ventana del reset, y
    // que gano o perdio despues.
    subasta: raw.subasta || { available: false, bids: [] },

    // Cuanto dinero nuestro esta comprometido en pujas vivas,
    // aunque las haya puesto el dueno a mano.
    pujasDelDueno: raw.pujas_del_dueno || {
      available: false,
      committed: 0,
      sources: {}
    },

    // Que se renovaria, que no llega vivo a la proxima ventana,
    // y cuando se entro por ultima vez en la ventana.
    renovacion: raw.renovacion || {
      available: false,
      renewals: [],
      at_risk: [],
      ventana: null
    },

    // Si Pepe esta en la franja en la que no escribe, y que se
    // quedo sin hacer por ella.
    silencio: raw.silencio || { available: false, allowed: true },
    rendija: raw.rendija || { available: false },
    posiblesCambios: raw.posibles_cambios || {
      available: false,
      bench: []
    },

    // Que trae la tanda nueva del Computer en cada reset.
    censoDelReset: raw.censo_del_reset || { available: false },

    // La auditoria que el generador hace de si mismo. Si esto
    // dice que no cuadra, no se decide mirando la pantalla.
    consistency: raw.consistency || { available: false, ok: true, checks: [] }
  };
}
