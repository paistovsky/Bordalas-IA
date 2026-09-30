import OrdenEnMarcha from "../components/OrdenEnMarcha";
import CascadaDinero from "../components/CascadaDinero";
import ElReset from "../components/ElReset";
import ReglasEncendidas from "../components/ReglasEncendidas";

/* EL PLAN (30/09/2026)
 *
 * La pregunta: ¿QUÉ VA A HACER PEPE, Y CON QUÉ DINERO?
 *
 *   1. La orden del gestor en marcha: a por quién, qué vende y
 *      qué no toca.
 *   2. El dinero hasta la jornada, en cascada.
 *   3. El próximo reset: qué se resuelve y qué pujará.
 *   4. Las reglas que tiene encendidas, en frases.
 *
 * Sustituye a ESTRATEGIA. Lo técnico de antes está en el TALLER.
 */

export default function PlanPage({ data }) {
  return (
    <div className="c2-rejilla">
      <OrdenEnMarcha data={data} />
      <CascadaDinero data={data} />
      <ElReset data={data} />
      <ReglasEncendidas data={data} />
    </div>
  );
}
