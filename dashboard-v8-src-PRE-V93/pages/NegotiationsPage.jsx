import NegotiationsPanel from "../components/NegotiationsPanel";
import AlertsPanel from "../components/AlertsPanel";

export default function NegotiationsPage({ data }) {
  return (
    <div className="two-column">
      <NegotiationsPanel data={data} />
      <AlertsPanel data={data} />
    </div>
  );
}
