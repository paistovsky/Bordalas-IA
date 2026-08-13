import { useEffect, useState } from "react";
import Sidebar from "./components/Sidebar";
import KpiStrip from "./components/KpiStrip";
import HomePage from "./pages/HomePage";
import SquadPage from "./pages/SquadPage";
import MarketPage from "./pages/MarketPage";
import NegotiationsPage from "./pages/NegotiationsPage";
import LeaguePage from "./pages/LeaguePage";
import AuditPage from "./pages/AuditPage";
import AnalysisPage from "./pages/AnalysisPage";
import { fetchStatus, normalizeStatus } from "./lib/status";
import { ago } from "./lib/utils";

const PAGE_TITLES = {
  home: "INICIO",
  squad: "PLANTILLA",
  market: "MERCADO",
  negotiations: "NEGOCIACIONES",
  league: "LIGA",
  analysis: "ANÁLISIS",
  audit: "AUDITORÍA",
  settings: "AJUSTES"
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
    return <div className="fatal-error">No se pudo cargar Bordalás IA: {error}</div>;
  }

  if (!data) {
    return <div className="loading-screen">CARGANDO BORDALÁS IA…</div>;
  }

  const pages = {
    home: <HomePage data={data} />,
    squad: <SquadPage data={data} />,
    market: <MarketPage data={data} />,
    negotiations: <NegotiationsPage data={data} />,
    league: <LeaguePage data={data} />,
    analysis: <AnalysisPage data={data} />,
    audit: <AuditPage data={data} />,
    settings: <div className="empty-page">Ajustes del dashboard — próximamente.</div>
  };

  return (
    <div className="app-shell">
      <Sidebar page={page} setPage={setPage} />

      <main className="main-workspace">
        <header className="top-header">
          <div className="matchday-title">
            <span>{PAGE_TITLES[page]}</span>
            <strong>JORNADA {data.summary.target_matchday ?? "—"}</strong>
            <small>
              Actualizado {ago(data.meta.generated_at)} · ciclo {data.meta.cycle_minutes || 15} min
            </small>
          </div>

          <KpiStrip data={data} />
        </header>

        {error && <div className="soft-error">Última actualización falló: {error}. Mostrando último estado válido.</div>}

        <section className="page-content">
          {pages[page]}
        </section>

        <footer className="status-footer">
          <span className="online-dot">● PEPE ONLINE</span>
          <span>● AUTOPILOT LIVE</span>
        </footer>
      </main>
    </div>
  );
}
