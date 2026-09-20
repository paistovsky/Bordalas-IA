# EL MARCADOR: DOS ENFERMEDADES CON LA MISMA ETIQUETA

**Fecha:** 2026-09-20 (undécimo) · **Rama:** `arreglo/el-marcador`, desde `main` ·
**Escrituras contra Biwenger:** ninguna · **Interruptor nuevo:**
`BORDALAS_JORNADAS_POR_SU_FECHA`, **apagado**

---

## TU DIAGNÓSTICO DEL ORDEN ES FALSO, Y ESTA ES LA PRIMERA LÍNEA

> **El marcador NO ordena por `round_id`.** Desde el 14/09 ordena por
> `primer_partido`, que sale del calendario — `orden_en_el_tiempo`, con
> `key=(momento, round_id)`. El comentario que lo dice ocupa treinta líneas en
> cabecera del módulo y se llama *«`round_id` NO ES EL TIEMPO»*.

Pero el resto de tu diagnóstico es correcto, y el fallo está **una capa más
arriba**: no es la clave de orden, es **de dónde sale esa fecha**.

> **`calendario_de_jornadas` toma la hora del calendario de LaLiga, que va por
> NÚMERO de jornada. «Jornada 6» y «Jornada 6 (aplazada)» son el número 6 las
> dos, así que se llevan LA MISMA HORA. Y con el empate, el desempate es el
> `round_id` — ahí vuelve a mandar el número.**

Medido, foto del 19/09 contra el tablón:

```
  4937  Jornada 1 (aplazada)   se jugo el 25/08   el calendario le pone el 15/08
  5125  Jornada 6 (aplazada)   se jugo el 15/09   el calendario le pone el 03/09
```

Ésas son **exactamente las dos parejas rotas**. Tu tesis —«4937 y 5125 rompen el
orden»— acierta de pleno; lo que no acierta es el mecanismo.

---

## BLOQUE 1 — LA PAREJA MAL FORMADA

### Dónde se elige la foto de antes, y con qué se ordena

| pieza | línea | qué hace |
|---|---|---|
| [`marcador.py:321`](src/analysis/marcador.py#L321) `calendario_de_jornadas` | | `{round_id: {"primer_partido", "fuente"}}` |
| [`marcador.py:600`](src/analysis/marcador.py#L600) `orden_en_el_tiempo` | `key=lambda item: (item["momento"], item["round_id"])` | **ordena por la hora, y el id sólo desempata** |
| [`marcador.py:1703`](src/analysis/marcador.py#L1703) `marcador()` | `previa = actual` al final del bucle | la foto de antes es **la anterior en ese orden** |

Una jornada **sin hora** no se coloca a ojo: sale en `sin_hora` y no se mide. Eso
también estaba bien.

### Las dos fuentes de la hora, y por qué las dos son ciegas

```
  los PARTIDOS de la foto      fecha exacta por round_id
                               pero Biwenger solo publica lo que QUEDA por jugar:
                               de las 9 jornadas observadas, 8 no tienen ni un partido

  el CALENDARIO DE LALIGA      el respaldo, y va por NUMERO de jornada
                               «Jornada 6» y «Jornada 6 (aplazada)» -> la misma hora
```

Ocho de las nueve jornadas observadas tiran del respaldo. Y el respaldo no puede
distinguir una aplazada de su hermana, porque LaLiga no tiene el `round_id` de
Biwenger.

### ¿Tenemos la fecha real? Sí, y no la estábamos pidiendo

> **Doctrina 103.** El tablón publica `roundStarted` y `roundFinished` **con el
> `round_id` dentro**, y hasta un `part: 2` con el que el propio Biwenger marca la
> mitad aplazada.

```
  4899  Jornada 1                 empieza 2026-08-15 17:30   termina 2026-08-20 10:06
  4900  Jornada 2                 empieza 2026-08-20 19:00   termina 2026-08-25 15:09
  4937  Jornada 1 (aplazada)  p2  empieza 2026-08-25 19:00   termina 2026-08-28 08:36
  4901  Jornada 3                 empieza 2026-08-28 17:00   termina 2026-09-01 15:06
  4904  Jornada 6                 empieza 2026-09-03 19:00   termina      -
  4902  Jornada 4                 empieza 2026-09-04 19:00   termina 2026-09-08 15:17
  4903  Jornada 5                 empieza 2026-09-11 19:00   termina 2026-09-15 10:05
  5125  Jornada 6 (aplazada)  p2  empieza 2026-09-15 17:00   termina 2026-09-18 08:35
  4905  Jornada 7                 empieza 2026-09-18 19:00   termina      -
```

**Cubre las nueve.** Y el fichero —`data/rival_intelligence/board_events.json`— ya
se carga cada vuelta para contar la puerta de los managers: **cero peticiones
nuevas**.

Se usa `roundStarted` y no `roundFinished` porque cubre las nueve —4904 y 4905 no
tienen fin— y porque donde están las dos, el orden que dan es el mismo.

**No era «no lo sabemos»: era «no lo habíamos preguntado».**

> **Interruptor: `BORDALAS_JORNADAS_POR_SU_FECHA`, apagado.** Es una tercera fuente
> en `calendario_de_jornadas`, por encima de las otras dos. Apagado, el calendario
> es exactamente el de ayer.

### Antes y después

`python -m scripts.el_marcador_antes_y_despues`

```
  HOY                      orden  4899 4937 4900 4901 4904 5125 4902 4903 4905
                           observadas 9 · MEDIBLES 4 · fiables 0 · descartadas 4
                           diferencia_media 20,4 (n=2)

  CON LA FECHA DEL TABLON  orden  4899 4900 4937 4901 4904 4902 4903 5125 4905
                           observadas 9 · MEDIBLES 5 · fiables 0 · descartadas 5
                           diferencia_media  3,6 (n=3)
```

| | hoy | con la fecha del tablón |
|---|---:|---:|
| observadas | 9 | 9 |
| **medibles** | **4** | **5** |
| fiables | 0 | 0 |
| `diferencia_media` | **+20,4** (n=2) | **+3,6** (n=3) |
| restas con negativos grandes | 2 (−7 y −31) | **0** |
| restas con un −1/−2 suelto | 2 | 3 |

**Las dos parejas invertidas desaparecen.** Lo que queda son tres negativos de un
solo jugador y de −1 o −2, que son otra cosa — el bloque 2.

**Fiables siguen siendo cero**, y eso no lo arregla este bloque: ninguna jornada
cuadra todavía con Biwenger.

> `test_las_jornadas_se_ordenan_por_su_fecha_no_por_su_numero` — 5 pruebas, en la
> verja. Falla si el caso no trae una jornada fuera de serie, y falla también si
> **apagado** ya saliera bien.

### Un tercer sitio donde la hora estaba mal, y no lo buscaba

La jornada **4905** también cambia: el calendario le daba **19/09 16:30** —el
próximo partido que quedaba por jugar— y el tablón dice que empezó el **18/09
19:00**. La fuente «exacta» de los partidos es exacta para lo que falta, no para lo
que ya se jugó. Hoy no rompe ninguna pareja porque 4905 es la última.

---

## BLOQUE 2 — UN −1 NO ES UNA FOTO AL REVÉS

Tienes razón: el mensaje era falso. `4937 ← 4899` y `4901 ← 4900` están bien
ordenadas en el tiempo y publicaban *«las dos fotos están al revés»*.

> **Doctrina 87.** Un motivo que nombra una causa que no decidió es una afirmación
> falsa.

### La distribución, y se separan limpiamente

Las 9 fotos del libro (10/08 → 20/09) permiten **72 restas ordenadas**. Separadas
por si la previa es de verdad anterior:

| | restas | con algún negativo | jugadores con negativo | el peor de cada una |
|---|---:|---:|---|---|
| **orden correcto** | 36 | **11** (25 limpias) | **1 siempre** | **−1 o −2 siempre** |
| **orden invertido** | 36 | **36** (0 limpias) | **de 2 a 11** | **de −4 a −88** |

> **Los dos grupos NO se solapan por ninguno de los dos ejes.** Ni por cuántos
> jugadores —1 contra 2 o más—, ni por el tamaño —−2 contra −4—. El umbral no me lo
> he inventado: sale de ahí, y hay hueco entre los dos grupos en las dos
> direcciones.

**El `n` honesto no es 72.** Son **9 fotos** y **8 parejas consecutivas reales**;
las 72 son todas sus combinaciones y no son independientes. El margen es ancho, la
muestra es corta, y las dos cosas van dichas en el código.

Las ocho consecutivas de verdad, con el orden arreglado:

```
  4900 <- 4899   limpia
  4937 <- 4900   1 jugador, -1   (Zubeldia)
  4901 <- 4937   1 jugador, -1   (Djene)
  4904 <- 4901   limpia
  4902 <- 4904   1 jugador, -2   (Dituro)
  4903 <- 4902   limpia
  5125 <- 4903   limpia
  4905 <- 5125   limpia
```

### Lo que he cambiado, y lo que no

**He separado las dos causas en el motivo.** Las dos siguen sin medirse: **ni una
decisión cambia**. Lo único que cambia es que el motivo deja de mentir.

```
  >= 2 jugadores          -> «las dos fotos estan al reves»
  1 jugador y >= -2       -> «es una correccion retroactiva de Biwenger»
                             + la medicion que lo sostiene
                             + «hoy se descarta igual, y esa regla la revisa el dueño»
```

### Mi recomendación: **no, un −1 no debe tumbar la jornada**

Y el motivo, en tres partes:

1. **Cuesta tres de ocho.** Con el orden arreglado, 3 de las 8 restas consecutivas
   tienen un −1/−2 suelto. Tumbarlas es perder el **37,5 %** de las jornadas por
   uno o dos puntos.
2. **El error que se acepta está acotado y es diminuto.** Un −1 en un jugador es
   **1 punto** sobre una jornada de 60 a 121: entre el **0,8 % y el 1,7 %**. Y sólo
   cuenta si ese jugador estaba en el once.
3. **La separación está medida y es ancha.** No hay que elegir un umbral fino: la
   frontera cae entre 1 y 2 jugadores, con cero casos en medio en 72 restas.

**Lo que propongo en concreto, y no he hecho:** que un negativo de un solo jugador
y de −1 o −2 **se recorte a cero, se nombre al jugador y se siga midiendo la
jornada**, marcándola con una nota. Absorberlo en silencio sí sería un error: la
corrección es de Biwenger, no nuestra, y tiene que verse.

**No lo he tocado.** Es el criterio de qué jornada es fiable y lo decides tú.

---

## BLOQUE 3 — EL VERDE QUE NO SIGNIFICA NADA

Tienes razón otra vez, y el caso es peor de lo que pensabas: **eran dos jornadas,
no una**.

```
  4904   once 0  ·  biwenger 0  ·  cuadra: true    completa: false
         «No se anoto que once jugo esa jornada.»

  4899   once 13 ·  biwenger 29 ·  cuadra: false   completa: false
         «4 de los 11 que alinearon ya no estaban en la plantilla al mirar.»
```

El primero es el verde falso. El segundo es su espejo: un **rojo** igual de vacío,
porque tampoco había con qué medir el cuadre.

> **Doctrina 91, del otro lado.** Un verde que puede darse sin haber medido nada
> vale lo mismo que un rojo. Y convertirlo en rojo sería la otra mitad del mismo
> error.

**Arreglado.** Con `reconstruccion_completa` en falso, `cuadra` pasa a valer
**`None`** —no es que no cuadre: es que no se puede medir— y viaja un
`cuadra_motivo` que lo dice con el nombre del agujero. La fila **sigue siendo
`medible`**: la resta de totales sí funcionó y los puntos oficiales son un hecho.
Lo único que deja de afirmarse es el cuadre.

*(Leo tu «que diga no medible» como «el CUADRE no es medible». Tirar la fila entera
se llevaría por delante el dato oficial, que es bueno. Si lo quieres al revés, es
una línea.)*

### ¿Entra en alguna cuenta? Sí, en una — y hay otra peor

| número | ¿se apoyaba en jornadas incompletas? | |
|---|---|---|
| `jornadas_fiables` | **no** — ya exigía `cuadra` **y** `reconstruccion_completa` | 0 antes y después |
| `eficiencia_media` | **no** — sale sólo de las fiables | `null`, bien puesto |
| **`cuadra_todo`** | **SÍ** — era `all(cuadra)` sobre todas las medibles | arreglado: ahora sólo mira las que se pudieron medir |
| **`diferencia_media`** | **sí, y a propósito** — usa los puntos oficiales, que no dependen de nuestra reconstrucción | **y ahí está el número que miente, por otro motivo** |

> **`diferencia_media` es el número de la pantalla que miente, y no es por
> `cuadra`: es por la pareja.** Publica **+20,4** porque una de sus dos jornadas es
> `5125 ← 4904`, que abarca **quince días y tres jornadas**. Con la fecha del
> tablón baja a **+3,6** (n=3), y la contribución de 5125 pasa de **+36,2 a +15,0**.

`cuadra_todo` hoy valía `false` de todas formas —4903 y 5125 no cuadran—, así que el
verde falso no llegó a mentir en pantalla. Pero podía: el día que las demás
cuadraran, una jornada de la que no anotamos nada habría dicho que sí.

> `test_una_jornada_sin_once_no_cuadra` — 4 pruebas, en la verja. Falla si en el
> caso todas las jornadas están completas, y comprueba además que las fiables no se
> mueven.

---

## BLOQUE 4 — LOS SIETE PUNTOS DE LA ÚNICA JORNADA BUENA

### No era la única jornada buena. No era una jornada.

La pareja que produce ese 121 es **`5125 ← 4904`**, y sus dos fotos son del **4 de
septiembre** y del **19 de septiembre**. Entre medias Biwenger cerró **tres
jornadas**: 4902 (08/09), 4903 (15/09) y 5125 (18/09).

### De dónde salen los 7, jugador a jugador

```
  jugador                ahora    antes    resta   el motor
  Dituro                     6        2        4          4
  Manu Sánchez              17        6       11         11
  Jonny                     18       12        6          6
  Djené                     16        5       11         11
  Olasagasti                32       21       11         11
  Expósito                  29        -       29          0   <- no estaba en la foto de 4904
  Pablo Ibáñez              26       10       16         16
  Rubén García              19        -       19          0   <- no estaba en la foto de 4904
  Oriol Rey                 19        -       19          0   <- no estaba en la foto de 4904
  Yamal                     76       28       48         48
  Jutglà                    25       11       14         14
  ------------------------------------------------------------
  SUMA                                       188        121
```

> **Los 7 no son de un jugador ni son un punto en siete jugadores. Son lo que queda
> después de que dos errores grandes casi se cancelen.**

```
  188  la resta cruda de los once, sobre TRES jornadas
  -67  tres jugadores que no estaban en la foto de 4904 y el motor pone a cero
       (Exposito 29 + Ruben Garcia 19 + Oriol Rey 19)
  ----
  121  lo que publica el marcador

  114  lo que Biwenger nos dio en esos quince dias (247 - 133 en la clasificacion)
  ----
   -7  el descuadre
```

El sobrante por medir tres jornadas en vez de una es **+74** (188 − 114). Lo que se
pierde por los tres ceros es **−67**. **La diferencia es el −7.** Es una
coincidencia aritmética, no una señal.

### Los cuatro sospechosos, descartados con dato

Del evento `leagueSettings` del propio tablón:

```
  lineupCaptain:        false     -> no hay capitan
  lineupStriker:        false     -> no hay multiplicador de delantero
  lineupRoundChanges:   0         -> NO se puede cambiar el once dentro de la jornada
  lineupMultiPos:       false
```

- **Capitán o multiplicador:** no existen en esta liga. Cerrado.
- **Cambios en vivo:** `lineupRoundChanges: 0`. No los hay, ni sustitución
  automática (doctrina 29).
- **Un jugador que entró o salió del once durante la jornada:** imposible por lo
  anterior.
- **Puntos revisados después:** existen y están medidos — son los negativos del
  bloque 2, **de −1 o −2 y en un solo jugador**. No llegan a 7 ni de lejos.

**Ninguno de los cuatro. La causa es la pareja.**

### ¿Es sistemático el 6,1 %? No se puede saber — y aquí el `n` no es 1, es 0

Lo digo con las palabras que pediste, y con una corrección:

> **Con una sola jornada no se puede saber si el descuadre es sistemático.** Y en
> este caso es peor: **esa jornada tampoco es una medición**, porque la resta
> abarcaba tres jornadas y quince días. **No tenemos `n = 1`: tenemos `n = 0`.**

Nuestro 121 **no está inflado un 6 %**: está inflado un **74 sobre 114 (+65 %)** por
medir tres jornadas, y desinflado **67** por los tres ceros. Decir «6 %» sería
tomarse por una medida el residuo de dos errores.

### Y con la fecha arreglada, 5125 tampoco mide limpio

```
  5125 <- 4903   nuestro once 27   ·   Biwenger 61   ·   descuadre +34
```

El motivo es un tercer agujero, distinto de los tres anteriores: **la foto de 4903
se tomó el 16/09 a las 05:04, y la jornada 5125 había empezado el 15/09 a las
17:00.** Es una foto tomada con la jornada siguiente ya en marcha.

Y hay una segunda mitad: esa misma foto tiene **la clasificación sin mover** —los
puntos de 4903 ya estaban en los jugadores (+60) pero el abono a los managers aún
no había pasado—. `foto_a_medias` no lo caza porque exige que los siete managers
marquen **cero absoluto**, y aquí marcan 186.

**No lo he arreglado.** No lo pedías, y tocar cuándo se toma la foto es cambiar
`observar()`, que es la puerta de entrada del libro.

> **Conclusión del bloque 4: seguimos sin una sola jornada medida limpiamente.** Lo
> que el arreglo del bloque 1 consigue no es dar por buena la 5125 — es **dejar de
> publicar un +36,2 contra la liga que no existía**.

---

## LA VERJA: 168 DE 169, Y LA ROJA ES LA DE AYER

```
  104/169  OK    test_el_marcador_por_su_fecha_v1
  105/169  OK    test_una_jornada_sin_once_no_cuadra_v1
  164/169  FALLA test_sin_pronostico_v1
           -> Esquivel con el suelo viejo sale con el score de la foto
              (calculado=249.799,75, foto=250.030,15)
```

**Es la misma roja del encargo de las guardias, y sigue sin ser del código.**
Comprobado otra vez en esta rama: con mis tres ficheros guardados en `stash`,
**sigue roja**. Y ya se comprobó que con el `laliga_calendar.json` y el
`jornada_perfecta_lineups.json` de producción sale verde.

Su veredicto cuelga de dos ficheros de estado local sin versionar. Es de las **31
que leen la carpeta de estado** y la propia verja la marca como *«NUEVA, no
censada»*. **No la he tocado: sacarla de la verja lo decides tú.**

**Aviso sobre el árbol:** mientras corría la verja entró una vuelta de producción
—22:45— y reescribió `marcador.json`, `board_events.json`,
`libro_de_publicacion.jsonl` y `bitacora_del_saldo.jsonl`. **Ninguno va en el
commit.** Volví a correr la medición con el libro nuevo y **no cambia ni un
número**.

---

## LO QUE NO HICE, Y POR QUÉ

- **No encendí ningún interruptor.** Ni el nuevo ni los aprobados: hasta que no esté
  hecho el bloque 2 del encargo de las guardias, no se enciende nada.
- **No cambié el criterio de qué jornada es fiable.** Un −1 sigue tumbando la
  jornada; el bloque 2 recomienda y tú decides.
- **No recorté ningún negativo a cero.** Va en la recomendación, no en el código.
- **No arreglé la foto tomada con la jornada siguiente ya empezada** (4903 el 16/09
  a las 05:04). Es el tercer agujero, toca `observar()` y no lo pedías.
- **No amplié `foto_a_medias`** para cazar «los jugadores ya se movieron y la
  clasificación no». Mismo motivo.
- **No rellené ninguna jornada antigua.** 4899 y 4900 siguen con la reconstrucción
  incompleta porque cuatro y tres de los once ya no están en la plantilla, y eso no
  se recupera.
- **No toqué `.github/workflows/bordalas-live.yml`.**
- **No toqué** `MAX_SINGLE_SPECULATION_PERCENT`, `MAX_SAFE_DEBT`, el suelo de cobro,
  `MIN_WIN_PROBABILITY`, `MAX_PROJECTED_DAILY_RATE`, las cinco de
  `PUEDEN_ENCERRARLO`, `PRIMA_MAXIMA_DE_PUJA` ni la ventana de 135 minutos.
- **Ni una escritura contra Biwenger, ni una petición a la red.** Todo sale de
  ficheros que ya estaban en `data/`.
- **No empujo.**

---

## EL `n`, Y CUÁNDO SE CORTÓ

| medida | `n` | corte |
|---|---|---|
| jornadas observadas en el libro | **9** | 15/08 → 20/09 |
| jornadas con fecha en el tablón | **9 de 9** (`roundStarted`) | ídem |
| jornadas cuya hora cambia con el arreglo | **3**: 4937, 5125 y 4905 | ídem |
| jornadas medibles | **4 → 5** | ídem |
| `diferencia_media` | **+20,4 (n=2) → +3,6 (n=3)** | ídem |
| restas ordenadas que permite el libro | **72** (pero sólo **8** consecutivas reales) | ídem |
| negativos con las fotos en orden | 11 de 36 · **1 jugador siempre** · **−1 o −2** | ídem |
| negativos con las fotos al revés | 36 de 36 · **2 a 11 jugadores** · **−4 a −88** | ídem |
| restas consecutivas con un −1/−2 suelto | **3 de 8** (37,5 %) | ídem |
| el descuadre de 5125 | **−7** = +74 de medir tres jornadas − 67 de tres ceros | 04/09 → 19/09 |
| jornadas medidas limpiamente | **0** | toda la temporada |

**Dos avisos.** Las 72 restas no son 72 observaciones independientes: son las
combinaciones de 9 fotos, y el `n` que manda es 8 parejas consecutivas. Y todo esto
se mide contra la foto del **19/09 18:18**, la última completa que hay en disco,
con el libro del marcador de las **22:13** de hoy.
