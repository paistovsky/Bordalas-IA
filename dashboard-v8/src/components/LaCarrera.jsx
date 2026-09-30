import Tarjeta, { Cifra, SinDato } from "./Tarjeta";
import { millones } from "../lib/lectura";

/* LA CARRERA POR EL TÍTULO (30/09/2026)
 *
 * Dónde vamos, a cuánto del primero (o cuánto le sacamos al
 * segundo), cuántas jornadas quedan y cuántos puntos por jornada
 * hay que sacarle. Sale de `race` y de la clasificación.
 */

export default function LaCarrera({ data }) {
  const race = data.race || {};
  const tabla = [...(data.competition?.standings || [])].sort((a, b) => a.rank - b.rank);

  if (!race.available && !tabla.length) {
    return (
      <Tarjeta titulo="LA CARRERA POR EL TÍTULO" pregunta="¿Cómo vamos?">
        <SinDato>Esta foto no trae la clasificación.</SinDato>
      </Tarjeta>
    );
  }

  const nos = tabla.find((m) => m.is_current_user);
  const puesto = race.position ?? nos?.rank;
  const puntos = race.points ?? nos?.points;
  const lider = tabla[0];
  const segundo = tabla[1];
  const somosLideres = race.is_leader ?? (lider && lider.is_current_user);

  const distancia = somosLideres
    ? (segundo ? Number(puntos) - Number(segundo.points) : null)
    : race.points_behind ?? (lider ? Number(lider.points) - Number(puntos) : null);

  const quedan = race.matchdays_remaining;
  const ritmo = race.required_pace;

  return (
    <Tarjeta titulo="LA CARRERA POR EL TÍTULO" pregunta="¿Cómo vamos en El Chiringuito?" className="c2-carrera">
      <div className="c2-cifras">
        <Cifra etiqueta="Puesto" valor={puesto ? `${puesto}º` : "—"} pie={puntos != null ? `${puntos} puntos` : null} />
        <Cifra
          etiqueta={somosLideres ? "Le sacamos al 2º" : "Al líder"}
          valor={distancia == null ? "—" : `${distancia}`}
          pie={somosLideres ? segundo?.name : lider?.name}
        />
        <Cifra etiqueta="Quedan" valor={quedan ?? "—"} pie="jornadas" />
      </div>

      {!somosLideres && ritmo != null && quedan ? (
        <p className="c2-frase">
          Para alcanzarle hay que sacarle {Number(ritmo).toLocaleString("es-ES", { maximumFractionDigits: 2 })} puntos
          por jornada.
        </p>
      ) : null}

      {Number(race.value_gap_to_leader) > 0 && !somosLideres && (
        <p className="c2-pie">
          La plantilla de {lider?.name || "el líder"} vale {millones(race.value_gap_to_leader)} más que la nuestra.
        </p>
      )}
    </Tarjeta>
  );
}
