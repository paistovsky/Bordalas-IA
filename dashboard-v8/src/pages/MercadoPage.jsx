import Escaparate from "../components/Escaparate";
import SubeBaja from "../components/SubeBaja";
import OfertasPorLoNuestro from "../components/OfertasPorLoNuestro";

/* MERCADO (30/09/2026, desde cero)
 *
 * La pregunta: ¿QUÉ HAY HOY EN EL MERCADO QUE NOS HAGA GANAR?
 *
 *   1. El escaparate del Computer, primero los que mejoran el once.
 *   2. Lo que sube y lo que baja, empezando por lo nuestro.
 *   3. Lo que nos ofrecen por los nuestros que están a la venta.
 *
 * El cuadro de objetivos, las publicaciones y la liga entera
 * siguen en el TALLER, en «El mercado por dentro».
 */

export default function MercadoPage({ data }) {
  return (
    <div className="c2-rejilla">
      <Escaparate data={data} />
      <SubeBaja data={data} />
      <OfertasPorLoNuestro data={data} />
    </div>
  );
}
