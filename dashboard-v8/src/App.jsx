import { useEffect, useState } from "react";
import Sidebar from "./components/Sidebar";
import KpiStrip from "./components/KpiStrip";
import HomePage from "./pages/HomePage";
import MarketPage from "./pages/MarketPage";
import BrainPage from "./pages/BrainPage";
import SquadPage from "./pages/SquadPage";
import LeaguePage from "./pages/LeaguePage";
import AuditPage from "./pages/AuditPage";
import { fetchStatus, normalizeStatus } from "./lib/status";
import { ago, minutesOld } from "./lib/utils";

const TITLES = {
  home: "INICIO",
  market: "MERCADO",
  brain: "CEREBRO",
  squad: "PLANTILLA",
  league: "LIGA",
  audit: "AUDITORÍA"
};

export default function App() {
  const [page, setPage] = useState("home");
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      try {
        const raw = await fetchStatus();
        if (!cancelled) {
          setData(normalizeStatus(raw));
          setError("");
        }
      } catch (err) {
        if (!cancelled) setError(err.message || String(err));
      }
    };

    load();
    const timer = setInterval(load, 60_000);

    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, []);

  if (error && !data) {
    return <div className="screen err">NO SE PUDO CARGAR BORDALÁS IA · {error}</div>;
  }

  if (!data) {
    return <div className="screen">CARGANDO BORDALÁS IA…</div>;
  }

  const pages = {
    home: <HomePage data={data} />,
    market: <MarketPage data={data} />,
    brain: <BrainPage data={data} />,
    squad: <SquadPage data={data} />,
    league: <LeaguePage data={data} />,
    audit: <AuditPage data={data} />
  };

  const edad = minutesOld(data.meta.generated_at);
  const cicloMin = Number(data.meta.cycle_minutes || 30);

  // Un ciclo y medio sin regenerar ya no es "hace un rato": es
  // una foto vieja y hay que decirlo antes de que alguien tome
  // una decision con ella.
  const rancio = edad != null && edad > cicloMin * 1.5;

  return (
    <>
      <Sidebar page={page} setPage={setPage} data={data} />

      <main>
        <div className="page-head">
          <h1>{TITLES[page]}</h1>
          <span className="tag">
            JORNADA {data.summary.target_matchday ?? "—"}
          </span>
          <span className={rancio ? "freshness stale" : "freshness"}>
            ● foto de {ago(data.meta.generated_at)}
          </span>
        </div>

        {error && (
          <div className="alert warn">
            La última actualización falló ({error}). Se muestra el último estado válido.
          </div>
        )}

        {rancio && !error && (
          <div className="alert warn">
            Estos datos son de hace {Math.round(edad)} minutos y el ciclo corre
            cada {cicloMin}. Entre ciclo y ciclo lo que ves es una foto: puede
            haber pujas o movimientos que aún no aparecen aquí.
          </div>
        )}

        {data.consistency?.available && !data.consistency.ok && (
          <div className="alert crit">
            <b>ESTA PANTALLA NO CUADRA CON BIWENGER.</b>{" "}
            {data.consistency.summary}
            <ul className="consistency-list">
              {(data.consistency.checks || [])
                .filter((check) => !check.ok)
                .map((check) => (
                  <li key={check.key}>
                    {check.label}:{" "}
                    {check.source === "BIWENGER" ? "Biwenger dice " : ""}
                    <b>{check.expected_label ?? String(check.expected)}</b>
                    {check.source === "BIWENGER" ? ", aquí sale " : " · "}
                    <b>{check.found_label ?? String(check.found)}</b>.{" "}
                    {check.detail}
                  </li>
                ))}
            </ul>
          </div>
        )}

        {data.lineup?.starter_data_total > 0 &&
          !data.lineup?.starter_data_ok && (
          <div className="alert warn">
            Probabilidad de ser titular disponible solo para{" "}
            {data.lineup.starter_data_players} de{" "}
            {data.lineup.starter_data_total} jugadores del XI. Los huecos dicen
            «sin dato» en vez de un 0 % que no significaría nada.

            {/* El POR QUE, no solo el cuantos. "La fuente externa
                no ha respondido" no dice si es que la pagina dio
                un 403, si la cache estaba vacia o si el tablero
                se cayo. Sin eso no se puede arreglar. */}
            <div style={{ marginTop: 6 }}>
              <b>Motivo:</b>{" "}
              {data.lineup.starter_source_error ? (
                <code>{data.lineup.starter_source_error}</code>
              ) : data.lineup.starter_board_players === 0 ? (
                "el tablero multifuente ha salido vacío (0 jugadores). " +
                "Suele significar que no se ha podido leer Jornada Perfecta " +
                "desde donde se generó este dashboard."
              ) : (
                "sin error registrado; el tablero tiene " +
                `${data.lineup.starter_board_players ?? "?"} jugadores.`
              )}
            </div>

            <div className="dim" style={{ marginTop: 4 }}>
              tablero {data.lineup.starter_board_version || "?"} ·{" "}
              caché {data.lineup.starter_cache_status || "?"} ·{" "}
              jornada {data.lineup.starter_board_matchday ?? "?"} ·{" "}
              generado {data.lineup.starter_board_updated_at || "?"}
            </div>

            <div style={{ marginTop: 6 }}>
              El XI que ves arriba está elegido <b>sin</b> ese dato: es el
              mejor por valor y puntos, no por quién va a jugar.
            </div>
          </div>
        )}

        <KpiStrip data={data} />

        {pages[page]}

        <p className="note">
          Todos los números salen de dashboard/data/status.json. Nada inventado.
        </p>
      </main>
    </>
  );
}
