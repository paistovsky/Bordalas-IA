/* LA TARJETA DE LAS PÁGINAS NUEVAS (30/09/2026)
 *
 * Un título corto, una línea que dice qué contesta, y el
 * contenido. Nada de avisos de colores: si falta un dato, el
 * cuadro lo dice con `<SinDato>` en una línea neutra.
 */

export default function Tarjeta({ titulo, pregunta, pill, className = "", children }) {
  return (
    <section className={`pan c2 ${className}`}>
      <header className="c2-head">
        <div className="c2-titulos">
          <h2>{titulo}</h2>
          {pregunta && <p className="c2-pregunta">{pregunta}</p>}
        </div>
        {pill}
      </header>
      {children}
    </section>
  );
}

export function SinDato({ children }) {
  return <p className="c2-sindato">{children}</p>;
}

/** Una cifra grande con su etiqueta encima y una línea debajo. */
export function Cifra({ etiqueta, valor, pie, tono = "" }) {
  return (
    <div className={`c2-cifra ${tono}`}>
      <span className="c2-cifra-l">{etiqueta}</span>
      <b className="c2-cifra-v">{valor}</b>
      {pie && <span className="c2-cifra-p">{pie}</span>}
    </div>
  );
}
