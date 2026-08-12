const $=id=>document.getElementById(id);
const esc=s=>String(s??"—").replace(/[&<>"']/g,m=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[m]));
const money=n=>{n=Number(n||0);if(Math.abs(n)>=1e6)return`${(n/1e6).toFixed(2)}M€`;if(Math.abs(n)>=1e3)return`${(n/1e3).toFixed(0)}k€`;return`${n.toLocaleString("es-ES")}€`};
const ago=iso=>{if(!iso)return"—";const m=(Date.now()-new Date(iso).getTime())/60000;if(m<1)return"ahora";if(m<60)return`hace ${Math.floor(m)} min`;return`hace ${(m/60).toFixed(1)} h`};
const gate=v=>({NO_ACTION_WAITING_RIVAL:"ESPERANDO RIVAL",ALLOW_SINGLE_RESPONSE:"RESPONDER",RECALCULATE:"RECALCULAR"}[v]||String(v||"—").replaceAll("_"," "));
const posLabel=p=>({1:"POR",2:"DEF",3:"MC",4:"DEL"}[Number(p)]||"JUG");

function coords(ps){
  const by={1:[],2:[],3:[],4:[]},out=[];
  ps.forEach(p=>(by[p.position]||by[4]).push(p));
  [[4,13],[3,38],[2,68],[1,91]].forEach(([pos,y])=>{
    by[pos].forEach((p,i)=>out.push({...p,x:(i+1)*100/(by[pos].length+1),y}));
  });
  return out;
}

function planCard(title,desc,p,alt=false){
  if(!p)return`<div class="plan ${alt?"alt":""}"><div class="plan-title">${title}</div><div class="plan-desc">Sin alternativa adicional calculada.</div></div>`;
  return `<div class="plan ${alt?"alt":""}">
    <div class="plan-title">${title}</div>
    <div class="plan-desc">${esc(desc)}<br><b>${esc((p.player_names||[]).join(" + ")||"—")}</b></div>
    <div class="plan-kv">
      <span>Ingreso estimado</span><b>${money(p.total_amount)}</b>
      <span>Saldo posterior</span><b class="${Number(p.post_balance)>=0?"good":"danger"}">${money(p.post_balance)}</b>
      <span>XI posterior</span><b>${p.playable_count||0}/11</b>
      <span>Formación posterior</span><b>${esc(p.formation_after||"—")}</b>
      <span>Coste deportivo</span><b>-${Number(p.lineup_score_loss_percent||0).toFixed(1)}%</b>
    </div>
    <div class="plan-foot">${p.restores_solvency?"SOLVENCIA RECUPERADA":"NO RECUPERA SOLVENCIA"}</div>
  </div>`;
}

function showTip(card,html){
  const t=$("playerTooltip");
  t.innerHTML=html;t.hidden=false;
  const r=card.getBoundingClientRect(),w=t.offsetWidth,h=t.offsetHeight;
  let left=r.right+10,top=r.top+r.height/2-h/2;
  if(left+w>innerWidth-10)left=r.left-w-10;
  if(top<10)top=10;
  if(top+h>innerHeight-10)top=innerHeight-h-10;
  t.style.left=`${left}px`;t.style.top=`${top}px`;
}
function hideTip(){$("playerTooltip").hidden=true}

function render(d){
  const m=d.meta||{},s=d.summary||{},li=d.lineup||{},c=d.competitive||{},n=d.pepe_now||{},lc=d.league_center||{};

  $("metaLine").textContent=`Jornada ${s.target_matchday??"—"} · ${ago(m.generated_at)} · ${String(m.snapshot||"").split(/[\\/]/).pop()||"—"} · ciclo ${m.cycle_minutes||15} min`;
  $("pepeStatus").textContent="● PEPE ONLINE";$("pepeStatus").className="good";
  $("mode").textContent=`AUTOPILOT ${m.mode||"—"}`;

  const mode=s.phase==="NORMAL"?"SIN URGENCIA":s.operations_locked?"BLOQUEADO":"ATENTO";
  const ops=s.operations_locked||s.hard_safety?"BLOQUEADAS":"PROTEGIDAS";
  const kpis=[
    ["SALDO",money(s.balance),s.balance<0?"DÉFICIT":"POSITIVO",s.balance<0?"danger":"good"],
    ["LINEUP",`${li.playable||0}/11`,li.playable===11?"COMPLETO":"INCOMPLETO",li.playable===11?"good":"danger"],
    ["PRÓXIMO CIERRE",`${Number(s.hours_to_deadline||0).toFixed(1)}h`,"PARA LA JORNADA","warn"],
    ["MODO DE BORDALÁS",mode,"TRANQUILO","good"],
    ["OPERACIONES",ops,s.operations_locked?"NO PUEDE OPERAR":"PUEDE OPERAR",s.operations_locked?"danger":"good"]
  ];
  $("summary").innerHTML=kpis.map(([a,b,c2,cls])=>`<div class="kpi"><small>${a}</small><b class="${cls}">${b}</b><em>${c2}</em></div>`).join("");

  $("nowTitle").textContent=n.title||"—";
  $("nowDetail").textContent=(n.detail||"—").replaceAll("Pepe","Bordalás");
  const deficit=Math.max(0,-Number(s.balance||0));
  const intel=[
    ["↗","Estrategia actual",deficit>0?"Recuperar solvencia":"Conservar ventaja"],
    ["▥","Riesgo de venta",s.lineup_risk||"—"],
    ["⌖","Objetivo de saldo",deficit?money(deficit):"POSITIVO"],
    ["◷","Presión de tiempo",Number(s.hours_to_deadline||0)<6?"ALTA":"BAJA"]
  ];
  $("nowIntel").innerHTML=intel.map(([i,l,v])=>`<div class="intel-row"><span class="intel-icon">${i}</span><span>${l}</span><b>${v}</b></div>`).join("");
  $("riskLabel").textContent=s.lineup_risk||"BAJO";

  const active=c.offers||[];
  const activeKeys=new Set(active.map(o=>`${o.player_id}|${o.rival_name}`));
  const recent=(c.recent_closed||[]).filter(o=>!activeKeys.has(`${o.player_id}|${o.rival_name}`));
  $("competitiveBadge").textContent="● LIVE";
  const row=o=>`<div class="neg-row ${o.closed_status?"neg-closed":""}">
      <div><strong>${esc(o.player_name)}</strong><small>→ ${esc(o.rival_name)}</small></div>
      <div><small>OFERTA RIVAL</small><b>${money(o.amount)}</b></div>
      <div><small>${o.closed_status?"MEJOR OFERTA":"CONTRAOFERTA"}</small><b>${money(o.authoritative_counter_amount||o.strategic_sell_price)}</b></div>
      <span class="neg-state">${o.closed_status?"RETIRADA POR RIVAL":gate(o.action_gate)}${o.closed_at?`<small>${ago(o.closed_at)}</small>`:""}</span>
    </div>`;
  $("competitiveOffers").innerHTML=
    `<div class="neg-section">ACTIVAS</div>${active.map(row).join("")}`+
    (recent.length?`<div class="neg-section recent">CIERRES RECIENTES · ÚLTIMAS 12H</div>${recent.slice(0,3).map(row).join("")}`:"");

  $("lineupMeta").textContent=`Formación ${li.formation||"—"} · Score XI ${li.score||0} · Riesgo ${s.lineup_risk||"—"} · Presión ${s.lineup_pressure||0}/100`;
  const offerMap=new Map(active.map(o=>[Number(o.player_id),o]));
  $("pitchPlayers").innerHTML=coords(li.players||[]).map(p=>`
    <div class="player ${offerMap.has(Number(p.id))?"watch":""}" data-id="${p.id}" style="left:${p.x}%;top:${p.y}%">
      <span class="pos">${posLabel(p.position)}</span>
      <strong>${esc(p.name)}</strong>
      <small>${money(p.price)} · ${Number(p.price_increment||0)>=0?"▲":"▼"}${money(Math.abs(p.price_increment||0))}</small>
      <small>${esc(p.jp_status||"—")} ${p.jp_confidence?`${p.jp_confidence}%`:""}</small>
    </div>`).join("");

  document.querySelectorAll(".player.watch").forEach(card=>{
    const id=Number(card.dataset.id);
    const p=(li.players||[]).find(x=>Number(x.id)===id);
    const o=offerMap.get(id);
    const html=`<strong>${esc(p.name)}</strong><div class="tip-grid">
      <span>Oferta</span><b>${money(o.amount)}</b>
      <span>Precio Bordalás</span><b>${money(o.authoritative_counter_amount||o.strategic_sell_price)}</b>
      <span>Entra</span><b>${esc((o.incoming_players||[]).join(", ")||"—")}</b>
      <span>Formación</span><b>${esc(o.formation_after||"—")}</b>
      <span>XI posterior</span><b>${o.post_sale_playable_count||"—"}/11</b>
      <span>Coste deportivo</span><b>-${Number(o.lineup_score_loss_percent||0).toFixed(1)}%</b>
    </div>`;
    card.onmouseenter=()=>showTip(card,html);
    card.onmouseleave=hideTip;
  });

  $("lineupFooter").textContent=`XI ${li.playable||0}/11 · Huecos ${li.missing||0}`;

  const pf=c.portfolio||{};
  const A=pf.strategic||null;
  const B=(pf.current&&JSON.stringify(pf.current)!==JSON.stringify(pf.strategic))?pf.current:null;
  $("solvencyDeficit").textContent=Number(pf.deficit||0)>0?`DÉFICIT ACTUAL ${money(pf.deficit)}`:"SOLVENTE";
  $("competitivePortfolio").innerHTML=
    planCard("PLAN A · PREFERIDO","Salida estratégica preferida por Bordalás",A)+
    planCard("PLAN B · ALTERNATIVA","Siguiente plan si el Plan A no se cumple",B,true);

  const alerts=[];
  if(recent[0])alerts.push(["red","●",recent[0].player_name,`${recent[0].rival_name} retiró su oferta de ${money(recent[0].amount)}.`]);
  if(active[0])alerts.push(["yellow","●",active[0].player_name,`${active[0].rival_name} ofrece ${money(active[0].amount)}. Bordalás espera ${money(active[0].authoritative_counter_amount||active[0].strategic_sell_price)}.`]);
  alerts.push(["green","●","XI cubierto",`Tenemos ${li.playable}/11 con el plan recomendado.`]);
  alerts.push(["orange","●","Solvencia",`Déficit de ${money(pf.deficit)}. ${A?.restores_solvency?"Hay solución calculada.":"Sin solución garantizada."}`]);
  alerts.push(["green","●","Deadline",`Quedan ${Number(s.hours_to_deadline||0).toFixed(1)}h para el cierre.`]);
  $("alerts").innerHTML=alerts.slice(0,5).map(a=>`<div class="alert-row ${a[0]}"><span>${a[1]}</span><b>${esc(a[2])}</b><span>${esc(a[3])}</span></div>`).join("");

  const ofs=d.offers||[];
  $("offers").innerHTML=ofs.length
    ?ofs.slice(0,4).map(o=>`<div class="data-row"><strong>${esc((o.players||[]).join(", "))}</strong><span>${money(o.amount)}</span><span>${o.premium_percent}%</span><span>${esc(o.action_label||"")}</span></div>`).join("")
    :`<div class="stat-big">0 nuevas</div><div class="muted">No hay ofertas nuevas de Computer.</div>`;

  const ls=d.listings||{};
  $("listings").innerHTML=`<div class="stat-big">${ls.listing_count||0} publicados</div>`+
    (ls.renew_required||[]).slice(0,4).map(x=>`<div class="data-row"><strong>${esc(x.name)}</strong><span>${money(x.listed_price)}</span><span>${x.hours_to_expiry}h</span><span>♻</span></div>`).join("");

  const sp=d.speculation||{};
  const cand=(sp.candidates||[]).slice().sort((a,b)=>Number(b.score||0)-Number(a.score||0));
  $("speculation").innerHTML=`<div class="stat-big">${sp.candidate_count||0} oportunidades</div>`+
    cand.slice(0,4).map(x=>`<div class="data-row"><strong>${esc(x.name)}</strong><span>${x.score}</span><span>${money(x.price)}</span><span>${Number(x.price_increment||0)>=0?"▲":"▼"}${money(Math.abs(x.price_increment||0))}</span></div>`).join("");

  $("topPlayers").innerHTML=(lc.top_players||[]).slice(0,5).map(x=>`<div class="mini-row"><b>${x.rank}</b><strong>${esc(x.name)}</strong><span>${x.points} pts</span></div>`).join("");
  $("leagueMarketFeed").innerHTML=(lc.market_feed||[]).slice(0,5).map(x=>`<div class="market-row"><strong>${esc(x.seller||x.buyer||"Mercado")} → ${esc(x.buyer||"Computer")}</strong><small>${esc(x.player_name)} · ${money(x.amount)}</small></div>`).join("");
  $("activity").innerHTML=(d.activity||[]).slice(0,7).map(a=>`<div class="audit-row"><span>${a.timestamp?new Date(a.timestamp).toLocaleTimeString("es-ES",{hour:"2-digit",minute:"2-digit"}):"—"}</span><span>${esc((a.label||"").replaceAll("Pepe","Bordalás"))}</span><strong>${a.write_performed?"HECHO":"VISTO"}</strong></div>`).join("");

  const ll=lc.laliga||{};
  $("laligaMeta").textContent=`${ll.season||"2026/27"} · ${ll.source||"—"}${ll.fetched_at?` · ${ago(ll.fetched_at)}`:""}`;
  $("laligaStandings").innerHTML=(ll.standings||[]).map(r=>`
    <tr class="${r.rank<=4?"ucl-row":r.rank<=7?"eu-row":r.rank>=18?"rel-row":""}">
      <td>${r.rank}</td>
      <td><div class="team-name">${r.logo?`<img class="team-logo" src="${esc(r.logo)}" alt="">`:""}<strong>${esc(r.team)}</strong></div></td>
      <td>${r.played}</td><td>${r.win}</td><td>${r.draw}</td><td>${r.lose}</td>
      <td>${r.goals_for}</td><td>${r.goals_against}</td><td>${Number(r.goals_diff)>0?"+":""}${r.goals_diff}</td>
      <td><strong>${r.points}</strong></td>
    </tr>`).join("");
}

fetch(`data/status.json?t=${Date.now()}`)
  .then(r=>{if(!r.ok)throw Error(`HTTP ${r.status}`);return r.json()})
  .then(render)
  .catch(e=>{
    $("app").innerHTML=`<section class="panel danger"><h2>No se pudo cargar la telemetría</h2><p>${esc(e.message)}</p></section>`;
  });
