import PlantillaEnCifras from "../components/PlantillaEnCifras";
import OnceVsIdeal from "../components/OnceVsIdeal";
import PlantillaPorLineas from "../components/PlantillaPorLineas";

/* PLANTILLA (30/09/2026, desde cero)
 *
 * La pregunta: ¿CÓMO ESTÁ MI EQUIPO?
 *
 *   1. En tres números: puntos, lo que vale y cuántos tocados.
 *   2. Nuestro once contra el mejor posible (la nota del marcador).
 *   3. La plantilla línea a línea.
 */

export default function PlantillaPage({ data }) {
  return (
    <div className="c2-rejilla">
      <PlantillaEnCifras data={data} />
      <OnceVsIdeal data={data} />
      <PlantillaPorLineas data={data} />
    </div>
  );
}
