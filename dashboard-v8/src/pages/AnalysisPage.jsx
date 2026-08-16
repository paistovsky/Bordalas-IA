import SpeculationPanel from "../components/SpeculationPanel";
import LeaguePanel from "../components/LeaguePanel";
import SolvencyPanel from "../components/SolvencyPanel";
import AcquisitionPanel from "../components/AcquisitionPanel";
import ExposurePanel from "../components/ExposurePanel";
import GuardrailPanel from "../components/GuardrailPanel";
import MarketClockPanel from "../components/MarketClockPanel";

export default function AnalysisPage({ data }) {
  return (
    <div className="analysis-layout-v94">
      <div className="analysis-constraints">
        <MarketClockPanel data={data} compact />
        <ExposurePanel data={data} />
        <GuardrailPanel data={data} />
      </div>

      <AcquisitionPanel data={data} full />

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
