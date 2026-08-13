import SpeculationPanel from "../components/SpeculationPanel";
import LeaguePanel from "../components/LeaguePanel";
import SolvencyPanel from "../components/SolvencyPanel";

export default function AnalysisPage({ data }) {
  return (
    <div className="three-column">
      <SpeculationPanel data={data} />
      <SolvencyPanel data={data} />
      <LeaguePanel data={data} />
    </div>
  );
}
