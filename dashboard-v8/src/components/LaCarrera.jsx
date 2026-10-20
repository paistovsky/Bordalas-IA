import Tarjeta, { Cifra, SinDato } from "./Tarjeta";
import { millones } from "../lib/lectura";

/* LA CARRERA POR EL TÍTULO (30/09/2026)
 *
 * Dónde vamos, a cuánto del primero (o cuánto le sacamos al
 * segundo), cuántas jornadas quedan y cuántos puntos por jornada
 * hay que sacarle. Sale de `race` y de la clasificación.
 *
 * LO QUE LA CLASIFICACIÓN NO CUENTA (19/10/2026)
 *
 * Los puntos de la tabla son los de Biwenger, y Biwenger solo
 * suma una ronda cuando la cierra. Este cuadro decía "Le sacamos
 * al 2º: 3" con la J8 abierta poniendo a Pollo17 treinta por
 * delante. El backend ya no nos da por líderes con rondas
 * abiertas y poca ventaja (`race.urgency` EN_JUEGO,
 * `race.lider_asegurado` false); aquí se dice lo mismo: la cifra
 * lleva "solo rondas cerradas" y debajo va la frase y el porqué.
 * Sin color: una línea más, como el resto del cuadro.
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

  const abiertas = Array.isArray(race.jornadas_abiertas) ? race.jornadas_abiertas : [];
  const enElAire = Boolean(
    somosLideres && (race.urgency === "EN_JUEGO" || race.lider_asegurado === false)
  );
  const soloCerradas = enElAire || abiertas.length > 0;
  const caveat = soloCerradas ? " (solo rondas cerradas)" : "";

  return (
    <Tarjeta titulo="LA CARRERA POR EL TÍTULO" pregunta="¿Cómo vamos en El Chiringuito?" className="c2-carrera">
      <div className="c2-cifras">
        <Cifra etiqueta="Puesto" valor={puesto ? `${puesto}º` : "—"} pie={puntos != null ? `${puntos} puntos` : null} />
        <Cifra
          etiqueta={(somosLideres ? "Le sacamos al 2º" : "Al líder") + caveat}
          valor={distancia == null ? "—" : `${distancia}`}
          pie={somosLideres ? segundo?.name : lider?.name}
        />
        <Cifra etiqueta="Quedan" valor={quedan ?? "—"} pie="jornadas" />
      </div>

      {enElAire && (
        <p className="c2-frase">
          {race.headline ||
            "Vamos primeros solo en las rondas cerradas: hay rondas sin contar y hasta que cierren no se sabe quién va primero."}
        </p>
      )}

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

      {soloCerradas && race.por_que && <p className="c2-pie">{race.por_que}</p>}
    </Tarjeta>
  );
}
