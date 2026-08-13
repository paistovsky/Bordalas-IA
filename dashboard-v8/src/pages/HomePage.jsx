import { Card, CardHeader, CardTitle } from "../components/ui/Card";
import LineupPitch from "../components/LineupPitch";
import DecisionPanel from "../components/DecisionPanel";
import NegotiationsPanel from "../components/NegotiationsPanel";
import AlertsPanel from "../components/AlertsPanel";
import SolvencyPanel from "../components/SolvencyPanel";
import SpeculationPanel from "../components/SpeculationPanel";
import LeaguePanel from "../components/LeaguePanel";

export default function HomePage({ data }) {
  return (
    <div className="home-layout">
      <Card className="home-lineup">
        <CardHeader>
          <div>
            <CardTitle>XI PARA LA JORNADA</CardTitle>
            <p className="section-subtitle">
              FORMACIÓN {data.lineup.formation || "—"} · RIESGO {data.summary.lineup_risk || "BAJO"} · PRESIÓN {data.summary.lineup_pressure || 0}/100
            </p>
          </div>
          <button className="ghost-button">VER DETALLE →</button>
        </CardHeader>
        <LineupPitch lineup={data.lineup} offers={data.competitive.offers} data={data} />
        <div className="lineup-footer">
          <span>XI {data.lineup.playable || 0}/11 · HUECOS {data.lineup.missing || 0}</span>
          <span className="success-text">✓ Sin sancionados</span>
        </div>
      </Card>

      <div className="home-right">
        <DecisionPanel data={data} />
        <NegotiationsPanel data={data} compact />
        <AlertsPanel data={data} />
      </div>

      <div className="home-bottom">
        <SolvencyPanel data={data} />
        <SpeculationPanel data={data} />
        <LeaguePanel data={data} />
        <Card>
          <CardHeader><CardTitle>OBJETIVO COMPETITIVO</CardTitle></CardHeader>
          <div className="next-matchday">
            <span>RIVAL A VIGILAR</span>
            <strong>Pollo17</strong>
            <span>OBJETIVO</span>
            <strong>Maximizar puntos sin perder solvencia</strong>
            <span>ESTRATEGIA</span>
            <strong>Solvencia + mejor XI posible</strong>
          </div>
        </Card>
      </div>
    </div>
  );
}
