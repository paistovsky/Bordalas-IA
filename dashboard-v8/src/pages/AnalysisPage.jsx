import SpeculationPanel from "../components/SpeculationPanel";
import LeaguePanel from "../components/LeaguePanel";
import SolvencyPanel from "../components/SolvencyPanel";

export default function AnalysisPage({ data }) {
  return (
    <div className="analysis-layout-v94">
      <div className="analysis-top-v94">
        <SpeculationPanel data={data} />
        <SolvencyPanel data={data} />
      </div>

      <div className="analysis-league-v94">
        <LeaguePanel data={data} />
      </div>
    </div>
  );
}
