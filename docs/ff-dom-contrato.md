# FutbolFantasy — contrato del DOM de una página de equipo

Verificado el 17/08/2026 contra el HTML real de `alaves`, `athletic` y
`barcelona` (`data/ff_html/`, 78 jugadores). Cierra el punto 1 del
bloque 1 de `docs/plan-futbolfantasy.md`.

## El hallazgo

**Nada de esto hay que scrapearlo de texto.** Cada jugador es un `<div>`
con ~150 atributos `data-*`. El parser actual
(`TEAM_DOM_NEAR_PLAYER_PERCENT`, ventanas de texto alrededor de un `%`)
está leyendo por la ventana lo que está escrito en la puerta: por eso
saca 9 registros de 12 páginas.

## La fila de jugador

```
div.jugador_<ffid>.jugador.tipo_lista.d-none.block-new
```

26 filas en Alavés, 29 en Athletic, 23 en Barcelona: **la plantilla
entera**, titulares y suplentes. El `<ffid>` de la clase es el id
interno de FF y es estable.

Hay otras filas `jugador_<ffid>` con `tipo_campo` / `camiseta-wrapper`:
son las camisetas del dibujo del campo. **No usarlas** — solo cubren el
once y duplican jugadores.

### Campos que importan

| atributo | ejemplo | para qué |
|---|---|---|
| `data-nombre` | `jonny-castro` | slug de identidad, estable |
| `data-probabilidad` | `70%` | % titular |
| `data-jerarquia` | `40` | **la jerarquía, numérica** |
| `data-estado` | `0` / `40` / `50` / `90` / `130` | estado físico |
| `data-situacion` | `0` / `2` / `3` | transferible / cedible |
| `data-sancionado`, `data-apercibido` | `0` / `1` | sanciones |
| `data-valor-biwenger` | `1650000` | **valor Biwenger, publicado por FF** |
| `data-valor-diff-biwenger` | `40000` | variación del valor |
| `data-totalminutosjugados` | `90` | minutos |
| `data-forma`, `data-forma_value` | `arrow-4`, `1` | racha |
| `data-rival`, `data-equipo` | `RAY`, `ALA` | próximo partido |
| `data-rival_dif_index` | `3` | **dificultad del rival, 1-5** |
| `data-locvis` | `<img … alt='Fuera'>` | local o visitante |
| `data-edad`, `data-nacionalidad`, `data-altura`, `data-pie` | | descartados por ruido |

Además hay `data-puntos-*` y `data-valor-*` para una docena de juegos
fantasy. Solo interesan los `-biwenger`.

## La escala de jerarquía

Mapeo completo, contado sobre los 78 jugadores:

| `data-jerarquia` | etiqueta | n |
|---|---|---|
| 60 | Dios | 1 |
| 50 | Clave | 14 |
| 40 | Importante | 12 |
| 30 | Rotación | 16 |
| 25 | Revulsivo | 10 |
| 20 | Reserva | 20 |
| 10 | Descarte | 2 |
| 0 | *(sin etiqueta)* | 3 |

Tres observaciones que cambian el diseño:

1. **Es ordinal y ya viene numérica.** No hay que mapear texto a rango:
   `data-jerarquia` ya ordena. La etiqueta es decoración.
2. **El salto 25→30 no es lineal.** Revulsivo (25) y Rotación (30) están
   a 5 puntos; Rotación e Importante, a 10. La escala pesa más arriba.
3. **`0` no es Descarte, es "sin definir".** No tiene etiqueta. Hay que
   tratarlo como ausencia de dato, no como el escalón más bajo — es
   exactamente el error que el plan prohíbe ("no inventa").

La etiqueta visible, si se quiere para el dashboard, está en
`.text-truncate.ml-2` dentro de la fila.

## Estado físico

`data-estado` manda; el icono confirma:

| `data-estado` | icono | significado |
|---|---|---|
| 0 | — | disponible |
| 40 | `duda_box_min.png` | duda |
| 50 | `lesionado_box_min.png` | lesionado |
| 130 | `lesionado_box_min.png` | lesionado (otra severidad) |
| 90 | `icono_big_nodisponible.png` | no disponible |

Facundo Garcés sale `data-estado=90`, `data-nodisponible=1`. Es el caso
que el plan señala: Biwenger solo dice NO DISPONIBLE, FF dice cuál de
los cuatro es.

`data-situacion`: `2` = Transferible, `3` = Transferible + Cedible
(etiquetas en `.trn-label` / `.ced-label`).

## Datos de equipo

En la cabecera, sin atributos `data-*` — aquí sí hay que leer texto:

- Entrenador: `strong.nombre-entrenador` → `Quique Sánchez`
- Rotaciones: `div.prevision-wrapper.one-container` → barra `width:20%`
  + `.porcentaje` → `Sin rotaciones`
- Previsibilidad de la jornada: fila `Previsib. J2` → barra `width:60%`
  + `.porcentaje` → `Poco previsible`

La barra da el número (20 %, 60 %) y el `.porcentaje` la etiqueta. Para
el multiplicador de confianza por equipo que pide el plan, usar la
barra.

## Lo que NO está en esta página

- **Dificultad del calendario más allá del próximo rival.**
  `data-rival_dif_index` es solo la jornada siguiente. Para la
  proyección de reventa hará falta otra página. Bloque 3.
- **Fecha de vuelta de un lesionado.** El icono dice que está lesionado,
  no hasta cuándo. Probablemente esté en la ficha del jugador.

## Consecuencias para el bloque 1

1. `parse_ff_team_page` y sus tres estrategias de texto sobran enteras.
   Se sustituyen por lectura de atributos: un método,
   `TEAM_ROW_DATA_ATTRS`, y cobertura de plantilla completa por equipo.
2. **`data-valor-biwenger` resuelve el emparejamiento.** Hoy la
   identidad se juega a parecido de nombre (`match_score` 0.86 para
   "ferran jutgla"). Con el valor Biwenger publicado por FF hay una
   segunda llave: nombre + valor que cuadra es identidad casi segura, y
   los choques se pueden resolver en vez de descartarse.
3. La jerarquía entra ya en el scraper como `data-jerarquia` cruda, sin
   normalizar a 0-100. Que el bloque 2 decida la escala.
4. `Atlético` no resuelve slug: `FF_TEAM_SLUGS` tiene `atletico madrid`
   pero el catálogo de Biwenger lo llama `Atlético`. Un equipo de veinte
   invisible por una clave del diccionario. Los otros 19 están bien
   —incluidos `Málaga`, `Deportivo` y `Racing`, que sí están en esta
   liga.
