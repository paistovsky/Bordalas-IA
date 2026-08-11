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

function render(d){

  const m=d.meta||{};
  const s=d.summary||{};
  const dec=d.decision||{};
  const sol=d.solvency||{};
  const fr=d.franchise||{};
  const li=d.lineup||{};

  const age=(Date.now()-new Date(m.generated_at).getTime())/60000;

  const health=
    age<20
      ?["🟢 PEPE ONLINE","good"]
      :age<40
        ?["🟠 PEPE STALE","warn"]
        :["🔴 PEPE OFFLINE","bad"];

  document.getElementById("pepeStatus").textContent=health[0];
  document.getElementById("pepeStatus").className=health[1];

  document.getElementById("mode").textContent=
    `AUTOPILOT ${m.mode||"—"}`;

  document.getElementById("metaLine").textContent=
    `Jornada ${s.target_matchday??"—"} · ${ago(m.generated_at)} · ${
      String(m.snapshot||"").split(/[\\/]/).pop()||"—"
    } · ciclo principal ${m.cycle_minutes||15} min`;

  const metrics=[
    [fmtMoney(s.balance),"SALDO"],
    [`${li.playable||0}/11`,"XI VÁLIDO"],
    [`${Number(s.hours_to_deadline||0).toFixed(1)}h`,"CIERRE JORNADA"],
    [humanPhase(s.phase),"FASE"],
    [dec.priority||0,"PRIORIDAD"],
    [s.hard_safety?"🔴 BLOQUEADO":"🟢 SEGURO","HARD SAFETY"]
  ];

  document.getElementById("summary").innerHTML=
    metrics.map(x=>
      `<div class="metric">
        <b>${esc(x[0])}</b>
        <span>${esc(x[1])}</span>
      </div>`
    ).join("");

  document.getElementById("decision").innerHTML=
    `<h2>🧠 PEPE HA DECIDIDO</h2>

    <div class="big good">
      ${esc(dec.label||humanAction(dec.action))}
    </div>

    ${kv({
      "Prioridad":dec.priority,
      "Escritura":dec.executable?"PODRÍA EJECUTAR":"NO",
      "Motivo":esc(dec.reason||"—")
    })}`;

  document.getElementById("solvency").innerHTML=
    `<h2>💰 SOLVENCIA</h2>

    <div class="big ${
      sol.needed
        ?(sol.possible?"warn":"bad")
        :"good"
    }">

      ${
        sol.needed
          ?(sol.possible
              ?"🟠 PLAN FINANCIABLE"
              :"🔴 NO GARANTIZADA")
          :"🟢 GARANTIZADA"
      }

    </div>

    ${kv({
      "Déficit":fmtMoney(sol.deficit),
      "Ofertas disponibles":num(sol.incoming_offers),
      "Jugadores publicados":num(sol.listed),
      "Pendientes publicar":num(sol.to_list)
    })}`;

  // Jugadores franquicia: todos los jugadores que Pepe protege activamente.
  // Est? preparado para 0, 1, 2 o m?s franquicias.
  const protectedOffers=(d.offers||[]).filter(o=>
    ["KEEP_PROTECTED","NEVER_SELL"].includes(o.action)
  );

  const protectedNames=[
    ...new Set(
      protectedOffers.flatMap(o=>o.players||[])
    )
  ];

  const protectedPlayers=
    protectedNames.map(name=>{
      const player=(li.players||[]).find(p=>p.name===name);

      return {
        name,
        price:player?.price,
        price_increment:player?.price_increment
      };
    });

  const marketFranchiseTarget=
    fr.target||null;

  const franchisePlural=
    protectedPlayers.length>1;

  const franchiseTitle=
    protectedPlayers.length===0
      ?"NUESTRA FRANQUICIA"
      :franchisePlural
        ?"NUESTRAS FRANQUICIAS"
        :"NUESTRA FRANQUICIA";

  const franchiseNames=
    protectedPlayers.length
      ?protectedPlayers
          .map(p=>`\u2B50 ${esc(p.name)}`)
          .join(" &nbsp;&nbsp; ")
      :"NINGUNA FRANQUICIA PROTEGIDA";

  const franchiseValues=
    protectedPlayers.length
      ?protectedPlayers
          .map(p=>`${esc(p.name)} ${p.price!=null?fmtMoney(p.price):"?"}`)
          .join(" ? ")
      :"?";

  const franchiseTrends=
    protectedPlayers.length
      ?protectedPlayers
          .map(p=>{
            if(p.price_increment==null){
              return `${esc(p.name)} ?`;
            }

            return `${esc(p.name)} ${
              Number(p.price_increment)>=0?"+":""
            }${fmtMoney(p.price_increment)}`;
          })
          .join(" ? ")
      :"?";

  document.getElementById("franchise").innerHTML=
    `<h2>\u2B50 ${franchiseTitle}</h2>

    <div class="big">
      ${franchiseNames}
    </div>

    ${kv({
      "Estado":
        protectedPlayers.length
          ?"PROTEGIDO ? NO VENDER"
          :"?",

      "Valor":
        franchiseValues,

      "Tendencia":
        franchiseTrends,

      "Objetivo en mercado":
        marketFranchiseTarget
          ?esc(marketFranchiseTarget)
          :"NINGUNO"
    })}`;

  document.getElementById("lineupMeta").textContent=
    `Formación ${li.formation||"—"} · `+
    `score interno XI ${li.score||0} · `+
    `riesgo ${s.lineup_risk||"—"} · `+
    `presión ${s.lineup_pressure||0}/100`;

  const positioned=
    getPitchCoordinates(li.players||[]);

  document.getElementById("pitchPlayers").innerHTML=
    positioned.map(p=>

      `<div
        class="player"
        style="left:${p.x}%;top:${p.y}%"
        title="Score interno de selección: ${p.lineup_score}"
      >

        <strong>
          ${esc(p.name)} · ${p.points} pts
        </strong>

        <small>
          ${fmtMoney(p.price)}
          ·
          ${Number(p.price_increment||0)>=0?"↑":"↓"}
          ${fmtMoney(Math.abs(p.price_increment||0))}
        </small>

        <small class="jp">
          JP ${esc(p.jp_status||"—")}
          ${p.jp_confidence?`${p.jp_confidence}%`:""}
        </small>

        <small class="scoreline">
          Pepe score ${p.lineup_score}
        </small>

      </div>`

    ).join("");

  document.getElementById("lineupFooter").textContent=
    `XI ${li.playable||0}/11 · `+
    `huecos ${li.missing||0}. `+
    `“pts” = puntos fantasy actuales; `+
    `“Pepe score” = score interno para elegir XI, `+
    `no predicción de puntos.`;

  const managers=
    d.rival_intelligence?.managers||[];

  const ordered=[...managers].sort((a,b)=>{

    if(a.is_us)return -1;
    if(b.is_us)return 1;

    return Number(b.threat_score||0)-
           Number(a.threat_score||0);

  });

  document.getElementById("rivals").innerHTML=
    ordered.map((r,i)=>

      `<tr class="${r.is_us?"us":""}">

        <td>${i+1}</td>

        <td>
          ${r.is_us?"⭐ ":""}
          ${esc(r.name)}
          ${r.is_us
            ?''
            :""
          }
        </td>

        <td>${r.points}</td>

        <td>${fmtMoney(r.balance)}</td>

        <td>${fmtMoney(r.roster_value)}</td>

        <td>${fmtMoney(r.net_worth)}</td>

        <td>${fmtMoney(r.maximum_bid)}</td>

        <td>${fmtMoney(r.max_observed_bid)}</td>

        <td>
          ${esc(humanActivity(r.activity))}
        </td>

        <td class="${threatClass(r.threat_level)}">

          ${
            r.is_us
              ?"—"
              :`${r.threat_score??0} · ${
                  humanThreat(r.threat_level)
                }`
          }

        </td>

      </tr>`

    ).join("");


  // CENTRO DE LA LIGA - DASHBOARD V3
  const lc=d.league_center||{};

  const fantasyRows=lc.fantasy_standings||[];
  document.getElementById("fantasyStandings").innerHTML=fantasyRows.length
    ?fantasyRows.map(row=>{
      const icon=biwengerIconUrl(row.icon);
      return `<tr class="${row.is_us?"us":""}">
        <td>${row.rank}</td>
        <td><div class="manager-cell">
          ${icon
            ?`<img class="manager-avatar" src="${esc(icon)}" alt="">`
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
      <td><strong>${row.points}</strong>
        ${Number(row.points)===0&&Number(row.points_last_season)>0
          ?`<small class="muted"> · ant. ${row.points_last_season}</small>`:""}
      </td>
      <td>${fmtMoney(row.price)}
        <small class="${Number(row.price_increment||0)>=0?"good":"bad"}">
          ${Number(row.price_increment||0)>=0?"▲":"▼"}${fmtMoney(Math.abs(row.price_increment||0))}
        </small>
      </td>
      <td>${row.owner?.is_us?"⭐ ":""}${esc(row.owner?.name||"Computer / libre")}</td>
    </tr>`).join("")
    :`<tr><td colspan="5" class="muted">Aún no hay ranking de jugadores.</td></tr>`;

  const marketRows=lc.market_feed||[];
  document.getElementById("leagueMarketFeed").innerHTML=marketRows.length
    ?marketRows.map(m=>{
      const dt=m.timestamp?new Date(Number(m.timestamp)*1000):null;
      const when=dt?dt.toLocaleString("es-ES",{
        day:"2-digit",month:"2-digit",hour:"2-digit",minute:"2-digit"
      }):"—";
      let premium=null;
      if(Number(m.current_price||0)>0&&Number(m.amount||0)>0)
        premium=((Number(m.amount)-Number(m.current_price))/Number(m.current_price))*100;
      return `<div class="market-movement">
        <span class="market-time">${esc(when)}</span>
        <div class="market-action">${marketMovementText(m)}
          <small>${m.type==="BUY_FROM_COMPUTER"?"Compra al Computer":
            m.type==="SELL_TO_COMPUTER"?"Venta al Computer":"Traspaso entre managers"}
            ${premium===null?"":` · vs VM actual ${premium>=0?"+":""}${premium.toFixed(1)}%`}
          </small>
        </div>
        <span class="market-amount">${fmtMoney(m.amount)}</span>
      </div>`;
    }).join("")
    :`<div class="muted">Todavía no hay movimientos de mercado registrados.</div>`;

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
          ${row.logo
            ?`<img class="team-logo" src="${esc(row.logo)}" alt="">`
            :`<span class="team-shield-fallback">${esc(initials)}</span>`}
          <strong>${esc(row.team)}</strong>
        </div></td>
        <td>${row.played}</td><td>${row.win}</td><td>${row.draw}</td><td>${row.lose}</td>
        <td>${row.goals_for}</td><td>${row.goals_against}</td>
        <td class="${Number(row.goals_diff)>=0?"good":"bad"}">
          ${Number(row.goals_diff)>0?"+":""}${row.goals_diff}
        </td>
        <td><strong>${row.points}</strong></td>
      </tr>`;
    }).join("")
    :`<tr><td colspan="10" class="muted">${
      esc(ll.message||"La clasificación real todavía no está disponible.")
    }</td></tr>`;

  const ofs=d.offers||[];

  document.getElementById("offers").innerHTML=
    ofs.length

    ?ofs.slice(0,8).map(o=>

      `<div class="row">

        <strong>
          ${esc(o.players.join(", "))}
        </strong>

        <span>
          ${fmtMoney(o.amount)}
        </span>

        <span>
          ${Number(o.premium_percent||0)>=0?"+":""}
          ${o.premium_percent}%
        </span>

        <span>
          ${
            o.solvency_reserved
              ?"🛡 RESERVADA"
              :esc(
                  humanAction(o.action)||
                  o.action_label
                )
          }
        </span>

      </div>`

    ).join("")+

    `<div class="compact-footer">
      ${ofs.length} ofertas disponibles
    </div>`

    :`<div class="muted">
       Sin ofertas.
     </div>`;

  const sp=d.speculation||{};

  document.getElementById("speculation").innerHTML=

    `${kv({
      "Motor":
        sp.enabled
          ?"🟢 ACTIVO"
          :"🔒 BLOQUEADO",

      "Modo":
        esc(sp.mode||"—"),

      "Oportunidades":
        sp.candidate_count,

      "Ejecutables":
        sp.executable_count
    })}

    <div style="margin-top:6px">

      ${
        (sp.candidates||[])
        .slice(0,4)
        .map(x=>

          `<div class="row">

            <strong>
              ${esc(x.name)}
            </strong>

            <span>
              score ${x.score}
            </span>

            <span>
              ${fmtMoney(x.price)}
            </span>

            <span>
              ${
                Number(x.price_increment||0)>=0
                  ?"↑"
                  :"↓"
              }
              ${
                fmtMoney(
                  Math.abs(
                    x.price_increment||0
                  )
                )
              }
            </span>

          </div>`

        ).join("")
      }

    </div>`;

  const ls=d.listings||{};

  document.getElementById("listings").innerHTML=

    kv({
      "En venta":
        ls.listing_count,

      "Necesitan renovar":
        ls.renew_required_count,

      "Próxima acción":
        ls.renew_required_count
          ?"RENOVAR"
          :"NINGUNA"
    })

    +

    (ls.renew_required||[])
    .slice(0,4)
    .map(x=>

      `<div class="row">

        <strong>
          ${esc(x.name)}
        </strong>

        <span>
          ${fmtMoney(x.listed_price)}
        </span>

        <span>
          ${x.hours_to_expiry}h
        </span>

        <span>
          ♻️ RENOVAR
        </span>

      </div>`

    ).join("");

  document.getElementById("priorities").innerHTML=

    (d.priorities||[])
    .slice(0,6)
    .map((p,i)=>

      `<div class="priority">

        <b>${i+1}</b>

        <span>
          ${esc(p.label)}
        </span>

        <strong>
          ${esc(p.status)}
        </strong>

        <span>
          prioridad ${p.priority}
        </span>

      </div>`

    ).join("");

  document.getElementById("activity").innerHTML=

    (d.activity||[]).length

    ?(d.activity||[])
      .slice(0,8)
      .map(a=>

        `<div class="feed">

          <span>
            ${
              a.timestamp
                ?new Date(a.timestamp)
                  .toLocaleTimeString(
                    "es-ES",
                    {
                      hour:"2-digit",
                      minute:"2-digit"
                    }
                  )
                :"—"
            }
          </span>

          <span>
            ${actionIcon(a.action)}
            ${esc(a.label)}
          </span>

          <strong class="${
            a.write_performed
              ?(
                  a.success===false
                    ?"bad"
                    :"good"
                )
              :"muted"
          }">

            ${
              a.write_performed
                ?"EJECUTADO"
                :"OBSERVADO"
            }

          </strong>

        </div>`

      ).join("")

    :`<div class="muted">
       Aún no hay histórico disponible.
     </div>`;
}

fetch(`data/status.json?t=${Date.now()}`)

  .then(r=>{

    if(!r.ok){
      throw new Error(
        `HTTP ${r.status}`
      );
    }

    return r.json();

  })

  .then(render)

  .catch(err=>{

    document.getElementById("app").innerHTML=

      `<section class="panel bad">

        <h2>
          No se pudo cargar la telemetría
        </h2>

        <p>
          ${esc(err.message)}
        </p>

        <p>
          Genera dashboard/data/status.json con
          <code>
            python -m src.telemetry.build_dashboard
          </code>
        </p>

      </section>`;

  });
