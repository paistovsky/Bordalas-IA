const fmtMoney=n=>{
  n=Number(n||0);
  const a=Math.abs(n);
  if(a>=1e6)return `${(n/1e6).toFixed(2)}M€`;
  if(a>=1e3)return `${(n/1e3).toFixed(0)}k€`;
  return `${n.toLocaleString("es-ES")}€`;
};

const num=n=>Number(n||0).toLocaleString("es-ES");

const esc=s=>String(s??"—").replace(/[&<>"']/g,m=>({
  "&":"&amp;",
  "<":"&lt;",
  ">":"&gt;",
  '"':"&quot;",
  "'":"&#39;"
}[m]));

const ago=iso=>{
  if(!iso)return "—";
  const d=(Date.now()-new Date(iso).getTime())/60000;
  if(d<1)return "ahora";
  if(d<60)return `hace ${Math.floor(d)} min`;
  return `hace ${(d/60).toFixed(1)} h`;
};

const actionIcon=a=>
  a?.includes("OFFER")?"👁":
  a?.includes("LINEUP")?"⚽":
  a?.includes("RENEW")?"♻️":
  a?.includes("SPECULATION")?"📈":"🧠";

const humanActivity=v=>({
  VERY_HIGH:"MUY ALTA",
  HIGH:"ALTA",
  MEDIUM:"MEDIA",
  LOW:"BAJA",
  NONE:"NULA"
}[v]||v||"—");

const humanThreat=v=>({
  VERY_HIGH:"MUY ALTA",
  HIGH:"ALTA",
  MEDIUM:"MEDIA",
  LOW:"BAJA",
  VERY_LOW:"MUY BAJA",
  US:"—"
}[v]||v||"—");

const humanPhase=v=>({
  NORMAL:"NORMAL",
  HARD_SAFETY:"SEGURIDAD",
  ROUND_LOCKED:"JORNADA BLOQUEADA",
  ROUND_TRANSITION_LOCK:"TRANSICIÓN"
}[v]||v||"—");

const humanFranchise=v=>({
  NO_FRANCHISE:"SIN JUGADOR FRANQUICIA ACTIVO",
  IN_TEAM:"EN PLANTILLA",
  TARGET_FOUND:"OBJETIVO DETECTADO",
  ACTIVE:"ACTIVO"
}[v]||v||"SIN JUGADOR FRANQUICIA ACTIVO");

const humanAction=v=>({
  KEEP_PROTECTED:"NO VENDER",
  KEEP_OFFER:"CONSERVAR OFERTA",
  KEEP_GOOD_OFFER:"CONSERVAR BUENA OFERTA",
  HOLD_SOLVENCY_RESERVED:"RESERVADA",
  NEVER_SELL:"NO VENDER",
  MONITOR_OFFERS:"VIGILAR OFERTAS",
  SAVE_LINEUP:"GUARDAR XI"
}[v]||String(v||"—").replaceAll("_"," "));

const humanCompetitiveEvent=v=>({
  NEW_RIVAL_OFFER:"OFERTA NUEVA",
  UNCHANGED_RIVAL_OFFER:"SIN CAMBIOS",
  RIVAL_CHANGED_OFFER:"RIVAL CAMBIÓ OFERTA"
}[v]||String(v||"—").replaceAll("_"," "));

const humanNegotiationGate=v=>({
  ALLOW_SINGLE_RESPONSE:"RESPONDER",
  RECALCULATE:"RECALCULAR",
  NO_ACTION_WAITING_RIVAL:"ESPERANDO RIVAL"
}[v]||String(v||"—").replaceAll("_"," "));

const humanCompetitiveDecision=v=>({
  COUNTER_OFFER:"CONTRAOFERTAR",
  ACCEPT_NOW:"ACEPTAR",
  ACCEPT_SACRIFICE_LINEUP:"ACEPTAR AUN PERDIENDO XI",
  NEVER_SELL:"NO VENDER"
}[v]||String(v||"—").replaceAll("_"," "));

const humanReplacement=v=>({
  SECURED_BY_BENCH:"CUBIERTO POR BANQUILLO",
  NONE:"SIN REEMPLAZO",
  UNKNOWN:"DESCONOCIDO"
}[v]||String(v||"—").replaceAll("_"," "));

const threatClass=l=>
  String(l).includes("HIGH")?"threat-high":
  String(l).includes("MEDIUM")?"threat-medium":
  "threat-low";


function leagueInitials(name){
  const parts=String(name||"?").trim().split(/\s+/).filter(Boolean);
  return parts.length?parts.slice(0,2).map(x=>x[0]?.toUpperCase()||"").join(""):"?";
}
function biwengerIconUrl(icon){
  if(!icon)return null;
  const value=String(icon);
  if(/^https?:\/\//i.test(value))return value;
  return `https://biwenger.as.com/${value.replace(/^\/+/, "")}`;
}
function marketMovementText(m){
  if(m.type==="BUY_FROM_COMPUTER")
    return `<strong>${esc(m.buyer)}</strong> compró a <strong>${esc(m.player_name)}</strong>`;
  if(m.type==="SELL_TO_COMPUTER")
    return `<strong>${esc(m.seller)}</strong> vendió a <strong>${esc(m.player_name)}</strong>`;
  return `<strong>${esc(m.seller)}</strong> → <strong>${esc(m.buyer)}</strong> · ${esc(m.player_name)}`;
}

function kv(obj){
  return `<div class="kv">${
    Object.entries(obj)
      .map(([k,v])=>`<span>${esc(k)}</span><strong>${v}</strong>`)
      .join("")
  }</div>`;
}

function getPitchCoordinates(players){
  const by={1:[],2:[],3:[],4:[]};

  players.forEach(p=>{
    (by[p.position]||by[4]).push(p);
  });

  const out=[];

  const add=(items,y)=>{
    const n=items.length;
    if(!n)return;

    items.forEach((p,i)=>{
      out.push({
        ...p,
        x:(i+1)*100/(n+1),
        y
      });
    });
  };

  // Delanteros arriba, portero abajo.
  add(by[4],13);
  add(by[3],37);
  add(by[2],67);
  add(by[1],91);

  return out;
}

function biwengerHeroUrl(path){
  if(!path)return null;
  const value=String(path);
  if(/^https?:\/\//i.test(value))return value;
  return `https://biwenger.as.com/${value.replace(/^\/+/,"")}`;
}

function playerInitials(name){
  return String(name||"?")
    .trim()
    .split(/\s+/)
    .slice(0,2)
    .map(x=>x[0]?.toUpperCase()||"")
    .join("");
}

function render(d){
  const m=d.meta||{};
  const s=d.summary||{};
  const dec=d.decision||{};
  const sol=d.solvency||{};
  const li=d.lineup||{};
  const comp=d.competitive||{};
  const now=d.pepe_now||{};

  const age=(Date.now()-new Date(m.generated_at).getTime())/60000;
  const health=
    age<20?["🟢 PEPE ONLINE","good"]:
    age<40?["🟠 PEPE STALE","warn"]:
           ["🔴 PEPE OFFLINE","bad"];

  document.getElementById("pepeStatus").textContent=health[0];
  document.getElementById("pepeStatus").className=health[1];
  document.getElementById("mode").textContent=`AUTOPILOT ${m.mode||"—"}`;
  document.getElementById("metaLine").textContent=
    `Jornada ${s.target_matchday??"—"} · ${ago(m.generated_at)} · ${
      String(m.snapshot||"").split(/[\\/]/).pop()||"—"
    } · ciclo ${m.cycle_minutes||15} min`;

  const metrics=[
    [fmtMoney(s.balance),"SALDO",s.balance<0?"bad":"good"],
    [`${li.playable||0}/11`,"XI VÁLIDO",li.playable===11?"good":"bad"],
    [`${Number(s.hours_to_deadline||0).toFixed(1)}h`,"CIERRE JORNADA",""],
    [humanPhase(s.phase),"FASE",""],
    [s.hard_safety?"BLOQUEADO":"SEGURO","HARD SAFETY",s.hard_safety?"bad":"good"]
  ];

  document.getElementById("summary").innerHTML=
    metrics.map(([value,label,cls])=>
      `<div class="metric">
        <b class="${cls}">${esc(value)}</b>
        <span>${esc(label)}</span>
      </div>`
    ).join("");

  const nowClass=
    now.level==="ACTION"?"bad":
    now.level==="SOLVENCY"?"warn":
    now.level==="WAIT"?"good":"good";

  document.getElementById("pepeNow").innerHTML=
    `<div class="now-kicker">🧠 QUÉ HARÍA PEPE AHORA</div>
     <div class="now-main ${nowClass}">${esc(now.title||dec.label||"—")}</div>
     <div class="now-detail">${esc(now.detail||dec.reason||"—")}</div>`;

  document.getElementById("decision").innerHTML=
    `<h2>🎯 DECISIÓN GLOBAL</h2>
     <div class="big good">${esc(dec.label||humanAction(dec.action))}</div>
     ${kv({
       "Prioridad":dec.priority,
       "Escritura":dec.executable?"PODRÍA EJECUTAR":"NO"
     })}`;

  document.getElementById("lineupMeta").textContent=
    `Formación ${li.formation||"—"} · score XI ${li.score||0} · `+
    `riesgo ${s.lineup_risk||"—"} · presión ${s.lineup_pressure||0}/100`;

  const positioned=getPitchCoordinates(li.players||[]);

  document.getElementById("pitchPlayers").innerHTML=
    positioned.map(p=>{
      const hero=biwengerHeroUrl(p.icon_hero);
      const trend=Number(p.price_increment||0);

      return `<div class="player player-v5"
                   style="left:${p.x}%;top:${p.y}%"
                   title="Pepe score ${p.lineup_score} · ${esc(p.jp_status||"—")} ${p.jp_confidence||0}%">
          <div class="player-portrait">
            ${hero
              ?`<img src="${esc(hero)}" alt="${esc(p.name)}"
                    onerror="this.style.display='none';this.nextElementSibling.style.display='grid'">`
              :""}
            <span class="player-fallback" style="${hero?"display:none":""}">
              ${esc(playerInitials(p.name))}
            </span>
          </div>

          <div class="player-info">
            <strong>${esc(p.name)}</strong>
            <small>${fmtMoney(p.price)} ·
              <span class="${trend>=0?"good":"bad"}">${trend>=0?"▲":"▼"}${fmtMoney(Math.abs(trend))}</span>
            </small>
            <small class="jp">${esc(p.jp_status||"—")} ${p.jp_confidence?`${p.jp_confidence}%`:""}</small>
          </div>
        </div>`;
    }).join("");

  document.getElementById("lineupFooter").textContent=
    `XI ${li.playable||0}/11 · huecos ${li.missing||0} · `+
    `las fotos usan iconHero oficial de Biwenger cuando está disponible.`;

  const badge=document.getElementById("competitiveBadge");
  badge.textContent=comp.live_enabled
    ?(comp.status==="WAITING_RIVAL"?"LIVE · ESPERANDO":
      comp.status==="ACTIONABLE"?"LIVE · ACCIÓN":"LIVE")
    :"OFF";
  badge.className=`mini-badge ${
    comp.status==="ACTIONABLE"?"badge-alert":"badge-live"
  }`;

  const crows=comp.offers||[];
  document.getElementById("competitiveOffers").innerHTML=
    crows.length
      ?crows.map(o=>`
        <div class="neg-row">
          <div>
            <strong>${esc(o.player_name)}</strong>
            <small>← ${esc(o.rival_name)}</small>
          </div>
          <div class="neg-money">
            <b>${fmtMoney(o.amount)}</b>
            <small>Pepe ${o.authoritative_counter_amount?fmtMoney(o.authoritative_counter_amount):"—"}</small>
          </div>
          <span class="neg-state ${o.should_respond?"neg-action":"neg-wait"}">
            ${esc(humanNegotiationGate(o.action_gate))}
          </span>
        </div>`).join("")
      :`<div class="muted">Sin negociaciones activas.</div>`;

  const p=comp.portfolio||{};
  const strategic=p.strategic||{};
  document.getElementById("competitivePortfolio").innerHTML=
    `<div class="solvency-hero ${Number(p.deficit||0)>0?"warn":"good"}">
       ${Number(p.deficit||0)>0?"DÉFICIT "+fmtMoney(p.deficit):"SOLVENCIA GARANTIZADA"}
     </div>
     ${kv({
       "Plan":strategic.player_names?.length
          ?esc(strategic.player_names.join(" + "))
          :"—",
       "Caja":strategic.total_amount?fmtMoney(strategic.total_amount):"—",
       "Saldo post":strategic.post_balance!==undefined?fmtMoney(strategic.post_balance):"—",
       "XI post":strategic.playable_count?`${strategic.playable_count}/11`:"—",
       "Pérdida XI":strategic.lineup_score_loss_percent!==undefined
          ?`${Number(strategic.lineup_score_loss_percent||0).toFixed(1)}%`
          :"—"
     })}`;

  const managers=d.rival_intelligence?.managers||[];
  const ordered=[...managers].sort((a,b)=>{
    if(a.is_us)return -1;
    if(b.is_us)return 1;
    return Number(b.threat_score||0)-Number(a.threat_score||0);
  });

  document.getElementById("rivals").innerHTML=
    ordered.map((r,i)=>`
      <tr class="${r.is_us?"us":""}">
        <td>${i+1}</td>
        <td>${r.is_us?"⭐ ":""}${esc(r.name)}</td>
        <td>${r.points}</td>
        <td>${fmtMoney(r.balance)}</td>
        <td>${fmtMoney(r.roster_value)}</td>
        <td>${fmtMoney(r.net_worth)}</td>
        <td>${fmtMoney(r.maximum_bid)}</td>
        <td>${fmtMoney(r.max_observed_bid)}</td>
        <td>${esc(humanActivity(r.activity))}</td>
        <td class="${threatClass(r.threat_level)}">
          ${r.is_us?"—":`${r.threat_score??0} · ${humanThreat(r.threat_level)}`}
        </td>
      </tr>`).join("");

  const ofs=d.offers||[];
  document.getElementById("offers").innerHTML=
    ofs.length
      ?ofs.slice(0,5).map(o=>`
        <div class="row">
          <strong>${esc(o.players.join(", "))}</strong>
          <span>${fmtMoney(o.amount)}</span>
          <span>${Number(o.premium_percent||0)>=0?"+":""}${o.premium_percent}%</span>
          <span>${o.solvency_reserved?"🛡 RESERVADA":esc(humanAction(o.action)||o.action_label)}</span>
        </div>`).join("")+
       `<div class="compact-footer">Top 5 de ${ofs.length} ofertas disponibles</div>`
      :`<div class="muted">Sin ofertas.</div>`;

  const sp=d.speculation||{};
  document.getElementById("speculation").innerHTML=
    `${kv({
      "Motor":sp.enabled?"🟢 ACTIVO":"🔒 BLOQUEADO",
      "Modo":esc(sp.mode||"—"),
      "Oportunidades":sp.candidate_count,
      "Ejecutables":sp.executable_count
    })}
    <div style="margin-top:7px">
      ${(sp.candidates||[]).slice(0,4).map(x=>`
        <div class="row">
          <strong>${esc(x.name)}</strong>
          <span>score ${x.score}</span>
          <span>${fmtMoney(x.price)}</span>
          <span>${Number(x.price_increment||0)>=0?"▲":"▼"}${fmtMoney(Math.abs(x.price_increment||0))}</span>
        </div>`).join("")}
    </div>`;

  const ls=d.listings||{};
  document.getElementById("listings").innerHTML=
    kv({
      "En venta":ls.listing_count,
      "Necesitan renovar":ls.renew_required_count,
      "Próxima acción":ls.renew_required_count?"RENOVAR":"NINGUNA"
    })+
    (ls.renew_required||[]).slice(0,4).map(x=>`
      <div class="row">
        <strong>${esc(x.name)}</strong>
        <span>${fmtMoney(x.listed_price)}</span>
        <span>${x.hours_to_expiry}h</span>
        <span>♻️ RENOVAR</span>
      </div>`).join("");

  document.getElementById("priorities").innerHTML=
    (d.priorities||[]).slice(0,6).map((p,i)=>`
      <div class="priority">
        <b>${i+1}</b>
        <span>${esc(p.label)}</span>
        <strong>${esc(p.status)}</strong>
        <span>${p.priority}</span>
      </div>`).join("");

  const lc=d.league_center||{};
  const fantasyRows=lc.fantasy_standings||[];
  document.getElementById("fantasyStandings").innerHTML=fantasyRows.length
    ?fantasyRows.map(row=>{
      const icon=biwengerIconUrl(row.icon);
      return `<tr class="${row.is_us?"us":""}">
        <td>${row.rank}</td>
        <td><div class="manager-cell">
          ${icon?`<img class="manager-avatar" src="${esc(icon)}" alt="">`
                :`<span class="manager-dot">${row.is_us?"⭐":esc(leagueInitials(row.name))}</span>`}
          <strong>${row.is_us?"⭐ ":""}${esc(row.name)}</strong>
        </div></td>
        <td><strong>${row.points}</strong></td>
        <td>${fmtMoney(row.net_worth)}</td>
      </tr>`;
    }).join("")
    :`<tr><td colspan="4" class="muted">Sin clasificación disponible.</td></tr>`;

  const topRows=lc.top_players||[];
  document.getElementById("topPlayers").innerHTML=topRows.length
    ?topRows.map(row=>`<tr>
      <td>${row.rank}</td>
      <td><strong>${esc(row.name)}</strong></td>
      <td><strong>${row.points}</strong></td>
      <td>${fmtMoney(row.price)}
        <small class="${Number(row.price_increment||0)>=0?"good":"bad"}">
          ${Number(row.price_increment||0)>=0?"▲":"▼"}${fmtMoney(Math.abs(row.price_increment||0))}
        </small>
      </td>
      <td>${row.owner?.is_us?"⭐ ":""}${esc(row.owner?.name||"Computer / libre")}</td>
    </tr>`).join("")
    :`<tr><td colspan="5" class="muted">Aún no hay ranking.</td></tr>`;

  const marketRows=lc.market_feed||[];
  document.getElementById("leagueMarketFeed").innerHTML=marketRows.length
    ?marketRows.map(m=>{
      const dt=m.timestamp?new Date(Number(m.timestamp)*1000):null;
      const when=dt?dt.toLocaleString("es-ES",{day:"2-digit",month:"2-digit",hour:"2-digit",minute:"2-digit"}):"—";
      return `<div class="market-movement">
        <span class="market-time">${esc(when)}</span>
        <div class="market-action">${marketMovementText(m)}</div>
        <span class="market-amount">${fmtMoney(m.amount)}</span>
      </div>`;
    }).join("")
    :`<div class="muted">Sin movimientos registrados.</div>`;

  const ll=lc.laliga||{};
  document.getElementById("laligaMeta").textContent=
    `${ll.season||"2026/27"} · ${ll.source||"—"} · ${ll.cache_status||"—"}${
      ll.fetched_at?` · actualizado ${ago(ll.fetched_at)}`:""}`;

  const llRows=ll.standings||[];
  document.getElementById("laligaStandings").innerHTML=llRows.length
    ?llRows.map(row=>{
      const zone=row.rank<=4?"zone-ucl":row.rank<=7?"zone-europe":
        row.rank>=18?"zone-relegation":"";
      const initials=leagueInitials(row.team);
      return `<tr class="${zone}">
        <td><strong>${row.rank}</strong></td>
        <td><div class="team-cell">
          ${row.logo?`<img class="team-logo" src="${esc(row.logo)}" alt="">`
                   :`<span class="team-shield-fallback">${esc(initials)}</span>`}
          <strong>${esc(row.team)}</strong>
        </div></td>
        <td>${row.played}</td><td>${row.win}</td><td>${row.draw}</td><td>${row.lose}</td>
        <td>${row.goals_for}</td><td>${row.goals_against}</td>
        <td class="${Number(row.goals_diff)>=0?"good":"bad"}">${Number(row.goals_diff)>0?"+":""}${row.goals_diff}</td>
        <td><strong>${row.points}</strong></td>
      </tr>`;
    }).join("")
    :`<tr><td colspan="10" class="muted">${esc(ll.message||"La clasificación real todavía no está disponible.")}</td></tr>`;

  document.getElementById("activity").innerHTML=
    (d.activity||[]).length
      ?(d.activity||[]).slice(0,8).map(a=>`
        <div class="feed">
          <span>${a.timestamp?new Date(a.timestamp).toLocaleTimeString("es-ES",{hour:"2-digit",minute:"2-digit"}):"—"}</span>
          <span>${actionIcon(a.action)} ${esc(a.label)}</span>
          <strong class="${a.write_performed?(a.success===false?"bad":"good"):"muted"}">
            ${a.write_performed?"EJECUTADO":"OBSERVADO"}
          </strong>
        </div>`).join("")
      :`<div class="muted">Aún no hay histórico disponible.</div>`;
}

fetch(`data/status.json?t=${Date.now()}`)
  .then(r=>{
    if(!r.ok)throw new Error(`HTTP ${r.status}`);
    return r.json();
  })
  .then(render)
  .catch(err=>{
    document.getElementById("app").innerHTML=
      `<section class="panel bad">
        <h2>No se pudo cargar la telemetría</h2>
        <p>${esc(err.message)}</p>
      </section>`;
  });
