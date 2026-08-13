import { Card, CardHeader, CardTitle } from "./ui/Card";
import {
  Radar, RadarChart, PolarGrid, PolarAngleAxis, ResponsiveContainer
} from "recharts";
import { Badge } from "./ui/Badge";

export default function SpeculationPanel({ data }) {
  const candidates = [...(data.speculation.candidates || [])]
    .sort((a, b) => Number(b.score || 0) - Number(a.score || 0));

  const best = candidates[0]?.score || 0;
  const radarData = [
    { axis: "Revalorización", value: Math.min(100, best) },
    { axis: "Liquidez", value: 72 },
    { axis: "Oportunidad", value: Math.min(100, best * 0.95) },
    { axis: "Riesgo", value: 42 },
    { axis: "Demanda", value: 68 }
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle>RADAR DE ESPECULACIÓN</CardTitle>
        <Badge tone="success">{candidates.length} OPORTUNIDADES</Badge>
      </CardHeader>
      <div className="speculation-content">
        <div className="radar-wrap">
          <ResponsiveContainer width="100%" height="100%">
            <RadarChart data={radarData}>
              <PolarGrid stroke="#334155" />
              <PolarAngleAxis dataKey="axis" tick={{ fill: "#8291a6", fontSize: 9 }} />
              <Radar dataKey="value" stroke="#36e37d" fill="#36e37d" fillOpacity={0.24} />
            </RadarChart>
          </ResponsiveContainer>
        </div>
        <div className="speculation-list">
          {candidates.slice(0, 3).map((player, index) => (
            <div key={player.id || player.name} className="speculation-row">
              <span>{index + 1}</span>
              <strong>{player.name}</strong>
              <b>{player.score}</b>
            </div>
          ))}
        </div>
      </div>
    </Card>
  );
}
