import LaCarrera from "../components/LaCarrera";
import LosRivalesEnCartas from "../components/LosRivalesEnCartas";

/* LIGA (30/09/2026, desde cero)
 *
 * La pregunta: ¿QUIÉN NOS PUEDE QUITAR EL TÍTULO?
 *
 *   1. La carrera: puesto, distancia y ritmo.
 *   2. Los rivales, una carta cada uno, con lo que movieron esta
 *      semana.
 *
 * Absorbe MARCADOR: la nota del once vive en PLANTILLA y el
 * detalle por jornada en el TALLER.
 */

export default function LigaPage({ data }) {
  return (
    <div className="c2-liga">
      <LaCarrera data={data} />
      <LosRivalesEnCartas data={data} />
    </div>
  );
}
