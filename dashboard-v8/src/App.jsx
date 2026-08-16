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
import { ago } from "./lib/utils";

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

  return (
    <>
      <Sidebar page={page} setPage={setPage} data={data} />

      <main>
        <div className="page-head">
          <h1>{TITLES[page]}</h1>
          <span className="tag">
            JORNADA {data.summary.target_matchday ?? "—"} · actualizado{" "}
            {ago(data.meta.generated_at)}
          </span>
        </div>

        {error && (
          <div className="alert warn">
            La última actualización falló ({error}). Se muestra el último estado válido.
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
