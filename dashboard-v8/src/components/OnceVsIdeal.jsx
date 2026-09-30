import Tarjeta, { Cifra, SinDato } from "./Tarjeta";

/* NUESTRO ONCE CONTRA EL MEJOR POSIBLE (30/09/2026)
 *
 * De la última jornada medida del marcador: lo que puntuó el once
 * que pusimos y lo que habría puntuado el mejor once posible con
 * la MISMA plantilla. La diferencia son puntos que se quedaron en
 * el banquillo: lo único de la jornada que depende de acertar.
 *
 * Si la reconstrucción no cuadra con Biwenger, se dice en una
 * línea: el número se enseña, pero no se vende como exacto.
 */

export default function OnceVsIdeal({ data }) {
  const marcador = data.marcador || {};
  const medidas = (marcador.jornadas || []).filter(
    (j) => j && j.medible && j.puntos_once != null && j.mejor_puntos != null
  );
  const ultima = medidas[0];

  if (!marcador.available || !ultima) {
    return (
      <Tarjeta titulo="NUESTRO ONCE CONTRA EL MEJOR POSIBLE" pregunta="¿Pusimos a los que más puntuaron?">
        <SinDato>Todavía no hay ninguna jornada medida.</SinDato>
      </Tarjeta>
    );
  }

  const puestos = Number(ultima.puntos_once);
  const mejor = Number(ultima.mejor_puntos);
  const perdidos = Math.max(0, mejor - puestos);
  const sobran = ultima.detalle?.faltaron || [];

  return (
    <Tarjeta
      titulo="NUESTRO ONCE CONTRA EL MEJOR POSIBLE"
      pregunta="¿Pusimos a los que más puntuaron? · última jornada medida"
    >
      <div className="c2-cifras">
        <Cifra etiqueta="Nuestro once" valor={puestos} pie={ultima.formacion || null} />
        <Cifra etiqueta="El mejor posible" valor={mejor} pie={ultima.mejor_formacion || null} />
        <Cifra etiqueta="En el banquillo" valor={perdidos} pie="puntos" tono={perdidos === 0 ? "bien" : ""} />
      </div>

      {sobran.length > 0 && perdidos > 0 && (
        <p className="c2-frase">
          Tenían que haber jugado:{" "}
          {sobran
            .filter((j) => Number(j.points) > 0)
            .map((j) => `${j.name} (${j.points})`)
            .join(", ") || "—"}
          .
        </p>
      )}

      {ultima.media_rivales != null && (
        <p className="c2-pie">
          La media de los rivales esa jornada: {Number(ultima.media_rivales).toLocaleString("es-ES")} puntos.
        </p>
      )}

      {ultima.cuadra === false && (
        <p className="c2-pie">
          La reconstrucción no cuadra del todo con Biwenger
          {ultima.descuadre != null ? ` (se separa ${Math.abs(Number(ultima.descuadre))} puntos)` : ""}.
        </p>
      )}
    </Tarjeta>
  );
}
