import { useState } from "react";

/* EL CAJÓN DEL TALLER (30/09/2026)
 *
 * Un plegable que NO pinta lo de dentro hasta que se abre. En el
 * taller hay seis pantallas enteras de las de antes; montarlas
 * todas de golpe para tenerlas escondidas sería pagar la página
 * más pesada para no verla.
 */

export default function Cajon({ titulo, detalle, children }) {
  const [abierto, setAbierto] = useState(false);

  return (
    <details className="plegado cajon" onToggle={(e) => setAbierto(e.currentTarget.open)}>
      <summary>
        <span className="plegado-titulo">
          {titulo}
          {detalle && <small className="cajon-detalle">{detalle}</small>}
        </span>
        <span className="plegado-mas">abrir</span>
      </summary>
      {abierto && <div className="plegado-cuerpo">{children}</div>}
    </details>
  );
}
