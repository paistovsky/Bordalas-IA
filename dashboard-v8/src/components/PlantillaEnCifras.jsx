import Tarjeta, { Cifra, SinDato } from "./Tarjeta";
import { conSigno, millones, plantilla } from "../lib/lectura";

/* LA PLANTILLA EN TRES NÚMEROS (30/09/2026)
 *
 * Puntos de la temporada, lo que vale la plantilla (y cuánto ha
 * cambiado hoy) y cuántos llegan tocados a la jornada.
 */

const TOCADO = new Set(["injured", "doubt", "sanctioned", "discarded"]);

export default function PlantillaEnCifras({ data }) {
  const js = plantilla(data);
  if (!js.length) {
    return (
      <Tarjeta titulo="LA PLANTILLA HOY" pregunta="¿Cómo llegamos a la jornada?">
        <SinDato>Esta foto no trae la plantilla.</SinDato>
      </Tarjeta>
    );
  }

  const valor = js.reduce((a, p) => a + Number(p.price || 0), 0);
  const hoy = js.reduce((a, p) => a + Number(p.price_increment || 0), 0);
  const tocados = js.filter((p) => TOCADO.has(String(p.status || "").toLowerCase()));
  const puntos = data.competition?.current_user_points;
  const puesto = data.competition?.current_user_rank;
  const once = data.lineup || {};

  return (
    <Tarjeta titulo="LA PLANTILLA HOY" pregunta="¿Cómo llegamos a la jornada?">
      <div className="c2-cifras">
        <Cifra
          etiqueta="Puntos"
          valor={puntos ?? "—"}
          pie={puesto ? `vamos ${puesto}º` : null}
        />
        <Cifra etiqueta="Vale" valor={millones(valor)} pie={hoy ? `${conSigno(hoy)} hoy` : "igual que ayer"} />
        <Cifra
          etiqueta="Tocados"
          valor={tocados.length}
          pie={tocados.length ? tocados.map((p) => p.name).join(", ") : "todos disponibles"}
        />
      </div>
      {once.playable != null && (
        <p className="c2-frase">
          Once para la jornada: {once.playable} de 11 pueden jugar
          {once.formation ? `, en ${once.formation}` : ""}.
        </p>
      )}
    </Tarjeta>
  );
}
