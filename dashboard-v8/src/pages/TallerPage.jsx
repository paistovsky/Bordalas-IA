import Cajon from "../components/Cajon";
import bordalas from "../assets/bordalas-official.jpg";

/* EL TALLER (30/09/2026)
 *
 * Lo técnico, TODO aquí y TODO cerrado. Las pantallas de antes
 * -auditoría con el diagnóstico, mercado, estrategia, plantilla,
 * liga y marcador- siguen enteras, cada una en su cajón: ningún
 * dato que publica status.json se ha quedado sin sitio.
 *
 * Los cajones no pintan nada hasta que se abren.
 */

export default function TallerPage({ cajones = [] }) {
  return (
    <>
      <section className="pan c2 c2-taller">
        <img src={bordalas} alt="" className="c2-taller-foto" />
        <div>
          <h2>EL TALLER</h2>
          <p className="c2-frase">
            Aquí está todo lo técnico: cómo decide Pepe, sus cuentas por dentro y la salud de lo que
            lee. No hace falta para el día a día.
          </p>
        </div>
      </section>

      {cajones.map((c) => (
        <Cajon key={c.titulo} titulo={c.titulo} detalle={c.detalle}>
          {c.contenido}
        </Cajon>
      ))}
    </>
  );
}
