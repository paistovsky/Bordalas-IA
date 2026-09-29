/* LO PLEGADO (30/09/2026)
 *
 * Cada página contesta UNA pregunta arriba, en frases y números
 * grandes. Lo demás -las tablas largas, los motores, las métricas
 * internas- no se borra: se pliega aquí, al final, cerrado por
 * defecto. Sigue en la página y sigue leyendo el mismo dato; sólo
 * deja de estar en medio.
 */

export default function Plegado({ titulo = "Más detalle", children }) {
  return (
    <details className="plegado">
      <summary>
        <span className="plegado-titulo">{titulo}</span>
        <span className="plegado-mas">abrir</span>
      </summary>
      <div className="plegado-cuerpo">{children}</div>
    </details>
  );
}
