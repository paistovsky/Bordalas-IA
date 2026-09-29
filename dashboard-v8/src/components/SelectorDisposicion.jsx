import { Monitor, Smartphone } from "lucide-react";

/* EL SELECTOR «MÓVIL / PC» (29/09/2026)
 *
 * Marca el diseño que se está viendo. Pulsar el otro lo fuerza;
 * pulsar otra vez el que ya está forzado vuelve a automático.
 * Mientras está en automático lo dice con una palabra pequeña.
 */

export default function SelectorDisposicion({ modo, efectivo, setModo }) {
  const pulsar = (v) => setModo(modo === v ? "auto" : v);

  return (
    <div className="disposicion" role="group" aria-label="Diseño de la pantalla">
      <button
        type="button"
        className={efectivo === "movil" ? "on" : ""}
        aria-pressed={efectivo === "movil"}
        onClick={() => pulsar("movil")}
      >
        <Smartphone size={13} /> Móvil
      </button>
      <button
        type="button"
        className={efectivo === "pc" ? "on" : ""}
        aria-pressed={efectivo === "pc"}
        onClick={() => pulsar("pc")}
      >
        <Monitor size={13} /> PC
      </button>
      <span className="disposicion-modo">
        {modo === "auto" ? "auto" : "fijo"}
      </span>
    </div>
  );
}
