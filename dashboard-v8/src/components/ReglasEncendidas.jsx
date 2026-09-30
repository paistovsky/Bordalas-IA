import Tarjeta, { SinDato } from "./Tarjeta";

/* LO QUE PEPE TIENE ENCENDIDO (30/09/2026)
 *
 * Los interruptores de producción, cada uno con lo que hace en
 * una frase. Sale de `reglas`. Sin la clave no se pinta: no es
 * «no hay nada encendido», es que no se publicó.
 */

export default function ReglasEncendidas({ data }) {
  const reglas = data.reglas;
  if (!reglas) return null;

  const filas = (reglas.reglas || []).filter((r) => r && (r.que_hace || r.nombre));

  return (
    <Tarjeta
      titulo="LO QUE PEPE TIENE ENCENDIDO"
      pregunta="¿Qué reglas sigue ahora mismo?"
      pill={filas.length ? <span className="c2-pill">{filas.length}</span> : null}
    >
      {!filas.length ? (
        <SinDato>{reglas.error ? "No se pudieron leer las reglas en esta vuelta." : "No hay ninguna regla encendida."}</SinDato>
      ) : (
        <ul className="c2-reglas">
          {filas.map((r) => (
            <li key={r.nombre || r.que_hace}>
              <span className="c2-punto" aria-hidden="true" />
              <span title={r.nombre || undefined}>{r.que_hace || r.nombre}</span>
            </li>
          ))}
        </ul>
      )}
    </Tarjeta>
  );
}
