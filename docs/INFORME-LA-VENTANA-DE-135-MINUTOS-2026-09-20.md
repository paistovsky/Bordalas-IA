# LA VENTANA DE 135 MINUTOS

**Fecha:** 2026-09-20 · **Rama:** `medir/la-ventana`, desde
`guardias/separar-las-dos-poblaciones` · **Escrituras contra Biwenger:** ninguna ·
**Umbrales tocados:** ninguno · **Interruptores encendidos:** ninguno.

---

## LO PRIMERO, PORQUE CAMBIA EL ENCARGO ENTERO

La ventana de 135 minutos **no es la puerta de las pujas**. Es la puerta de **una**
de las cuatro vías de puja, y la más barata de las cuatro.

En los ocho resets del 13 al 19/09, con el `n` limpio —operaciones distintas, sin
los nueve Maffeo ni los cinco Boyomo—:

| vía | momento | pujas | ganadas |
|---|---|---:|---:|
| `SUBASTA_CARTERA` | **dentro** de la ventana | 9 | 8 |
| `RENDIJA` | dentro | 1 | 1 |
| `RENDIJA` | **fuera** | 3 | 3 |
| `ACQUISITION_BOARD` | fuera | 1 | 1 |
| `DESCONOCIDO` | fuera | 7 | 4 |
| **total** | | **21** | **17** (81,0 %) |

> **11 de 21 pujas de la última semana salieron con la puerta cerrada.** La ventana
> no impide pujar: impide que la **cesta** —la puja múltiple de `la_subasta`— se
> forme. Todo lo demás puja a cualquier hora.

Y eso no es un descuido: está escrito en el código, con su motivo y su fecha.
`src/analysis/la_rendija.py:28-32`, del **11/09/2026** —un día después de ampliar la
ventana—:

> «LA VENTANA. Las pujas de revender se pueden colocar a cualquier hora. El motivo
> está medido: todas se resuelven en el reset y las de los rivales no se ven, así
> que pujar tarde no nos esconde de nadie. **La ventana no aportaba NADA para pujar
> — era una creencia nuestra, no una mecánica del juego.**»

Tu sospecha del bloque 2 ya se midió hace nueve días, ganó, y se construyó un carril
entero para saltarse la ventana. Lo que quedó sin revisar fue la vía de la cesta.

---

## BLOQUE 1 — DE DÓNDE SALE ESE 135

### El commit

No hay un commit que "ponga" los 135. Hay dos, y el segundo **amplía**, no restringe.

| commit | fecha | qué hizo |
|---|---|---|
| `99f1e13` | **2026-09-08 22:27** | crea `la_subasta` con `VENTANA_MINUTOS = 15` |
| `e7f8d82` | **2026-09-10 12:08** | `15 → 135`, y `SILENCIO_DESDE 05:00 → 04:45` |

`99f1e13` — *«subasta: estar a las siete menos cinco»*. La ventana de 15 minutos
nació para lo contrario de lo que hoy hace: **permitir varias pujas en la misma
vuelta**, cuando el resto del día Pepe pone una acción por vuelta. Quince y no cinco
porque el cron de GitHub se retrasa.

`e7f8d82` — *«ventana: 135 minutos, silencio desde las 04:45, y que la ausencia se
vea»*. Lo que arreglaba, con sus palabras:

> «Con quince minutos el disparo externo NO ENTRABA bajo ninguna lectura del reloj:
> 04:45 y 04:50 quedaban a 135 y 130 minutos del reset, y si cron-job.org aplica CET
> —medido el 10/09— a 75 y 70. Los cuatro fuera.»

**El 135 no es una medida de riesgo. Es una distancia.** Es exactamente los minutos
que hay de 04:45 —el primer disparo externo— a las 07:00, elegido para cubrir las dos
lecturas posibles del reloj de un tercero con un solo número. Doctrina 94 al revés:
es un umbral fijo puesto *para* absorber una rejilla móvil.

No es el caso del listón del 3 %. El motivo está escrito, fechado, medido antes de
tocarlo y sigue siendo cierto: **con menos de 135, el disparo de las 04:45 no entra.**

### ¿Número o constante?

Constante con nombre: `VENTANA_MINUTOS = 135`, en
[la_subasta.py:95](src/analysis/la_subasta.py#L95), con 40 líneas de cabecera que
cuentan su historia. Nadie la copia a mano: las guardias que la comprueban la
importan.

**Quién la lee:**

| sitio | para qué |
|---|---|
| [la_subasta.py:153](src/analysis/la_subasta.py#L153) `ventana_abierta()` | la calcula |
| [la_subasta.py:1395](src/analysis/la_subasta.py#L1395) | **la puerta**: `blocked_by = FUERA_DE_VENTANA`, cesta vacía |
| [v10_full_autonomous_live.py:444](src/v10_full_autonomous_live.py#L444) | cuánto lleva abierta, para la dedup del libro |
| [v10_full_autonomous_live.py:1151](src/v10_full_autonomous_live.py#L1151) | si se apunta la entrada en `libro_de_la_ventana` |
| [renovar_executor.py:137](src/actions/renovar_executor.py#L137) | lo mismo, para la dedup de renovaciones |
| [zona_de_silencio.py:99](src/analysis/zona_de_silencio.py#L99) | atada a ella por comentario y por guardia |

### Las ventanas de tiempo del motor

Pediste la lista por si hubiera cinco relojes. **Hay dos que deciden si se escribe, y
son el mismo intervalo.** El resto son plazos de caducidad, alarmas o mediciones.

**(a) Las que abren o cierran una escritura**

| valor | dónde | qué hace |
|---|---|---|
| **135 min** (04:45–07:00) | `la_subasta.VENTANA_MINUTOS` | **única puerta horaria de escritura del motor.** Fuera de ella, `la_subasta` devuelve cesta vacía |
| **04:45–07:00** | `zona_de_silencio.SILENCIO_DESDE/HASTA` | prohíbe escribir mientras el Computer resuelve, **salvo** disparo deliberado. Desde que se retiró el `schedule` (12/09) todas las vueltas son deliberadas, así que hoy no frena ninguna |
| 15 / 90 / 120 min | `matchday_calendar_engine` | `bloqueo_temporal` por jornada; `la_subasta` lo consulta **antes** que la ventana |
| 1.800 → 21.600 s | `action_failure_backoff` | espera tras un fallo |

Las dos primeras son **el mismo intervalo, y van atadas a propósito**: ampliar la
ventana sin mover el silencio dejaba 04:45–05:00 abierto y sin vigilar. Hay guardia
que lo exige (`test_una_ventana_que_no_se_abre_v1`). Si alguien mueve el 135, tiene
que mover el silencio con él.

**(b) Las que NO son ventanas aunque lo parezcan**

`renovar` **ya no tiene ventana**: la puerta se le quitó y el comentario de
[v10:1137](src/v10_full_autonomous_live.py#L1137) lo dice. `publicar` y `cobrar`
tampoco. `computer_cycle_engine` (05:00–07:00, 23:30) proyecta *cuándo* recogerá el
Computer un listado: no frena nada. `el_escaparate.HORA_DEL_RESET = 5` UTC y
`la_prima_de_compra.HORA_DEL_CAMBIO = 7` Madrid son **el mismo instante medido**, no
dos relojes.

Plazos de caducidad, no ventanas: 72 h (`bid_outcome_ledger`), 47,9 h
(`bitacora_del_saldo`), 48 h (`libro_de_publicacion`), 24 h (`archivo_diario`), 6 h
(`offer_decision`, `accept_before_expiry`, `reroll`), 12/3 h
(`market_listing_lifecycle`). Alarmas: 145 min y 5 h (`los_sentidos`), 24 h
(`libro_de_la_ventana`).

**No hay cinco relojes. Hay uno, de 04:45 a 07:00, con dos nombres.**

### El motivo documentado, ¿sigue valiendo?

**Sí para el 135, no para la ventana.** Son dos cosas distintas:

- **Por qué 135 y no 15**: válido y vigente. Si se baja, el disparo de las 04:45 se
  queda fuera y no se puja ningún día.
- **Por qué existe una ventana**: el propio repositorio lo desmintió el 11/09 y
  construyó `la_rendija` para esquivarla. Sigue en pie sólo en la vía de la cesta.

Así que **no paro**, pero paro en la mitad: el 135 no se toca, y el que sobra es el
concepto de ventana en `plan_del_reset`, que no es un número tuyo sino una puerta.

---

## BLOQUE 2 — ¿PROTEGE DE ALGO? NO

Tu sospecha es correcta. Tres medidas, las tres con su `n`.

### 1. El tablón no publica ninguna puja viva. De nadie.

`market.sales` —el tablón del Computer, la fuente de todas las subastas— tiene
exactamente seis claves: `date`, `extended`, `player`, `price`, `until`, `user`.
**No hay ningún campo donde pueda aparecer una puja.** No es que estén ocultas: no
existe el hueco. Comprobado en todas las fotos de `data/snapshot_*.json`.

Las pujas sólo aparecen dentro del evento `market` del tablón, **el que resuelve la
subasta**. Los 44 eventos `market` de la temporada están fechados entre las **07:02 y
las 07:11 de Madrid**, ninguno antes. `n = 44 eventos · 232 subastas`.

Y `market.offers` sólo trae operaciones en las que estamos nosotros: vemos las
nuestras, nunca las de un rival con un tercero.

**Prueba directa:** nuestra puja por Trent, enviada el 12/09 a las 16:45 de Madrid,
respondió `status: "waiting"`, `until: 13/09 07:00`. Estuvo **catorce horas y cuarto**
colgada, y nadie pudo verla. Si un rival pudiera reaccionar a una puja, ésa era la
que tenía que haber caído.

### 2. Casos medidos de puja superada después de puesta: **cero**, y no por suerte

`bid_outcome_ledger`, `n` limpio: **35 operaciones distintas** (47 filas menos los
nueve Maffeo y los cinco Boyomo), **29 ganadas, 6 perdidas → 82,9 %**.

Las seis perdidas:

| jugador | puesta | nuestra | ganadora | por qué se perdió |
|---|---|---:|---:|---|
| Cáceres | 12/09 04:46 | 1.503.751 | — | `RESET_SIN_JUGADOR` |
| Sotelo | 12/09 04:52 | 1.604.001 | — | `RESET_SIN_JUGADOR` |
| Carmona | 18/09 04:53 | 671.676 | — | `RESET_SIN_JUGADOR` |
| Larrubia | 13/09 18:35 | 4.797.017 | 4.790.000 | rival, margen **−7.017** |
| Giménez | 13/09 23:29 | 3.115.017 | 3.331.000 | rival, +215.983 |
| Dieng | 15/09 17:25 | 1.056.003 | 1.077.000 | rival, +20.997 |

Tres no tuvieron rival: el jugador desapareció del tablón. Tres las ganó alguien que
pagó más.

**De esas tres no se puede decir si nos superaron o si ya estaban puestas, y eso es
justamente la respuesta.** Biwenger no publica la hora de ninguna puja rival, ni en
el tablón ni en la foto. Nadie puede medir el orden — **ni ellos ni nosotros**. Una
ventana que esconde algo que nadie puede ver tampoco esconde nada.

(El Larrubia con margen **negativo** —pujamos 7.017 más y perdimos— es un apunte
sucio del tablón, no un fenómeno. Lo anoto y no lo uso.)

### 3. El precio NO se mueve dentro del día

Sobre nueve días con dos o más fotos del mismo día:

```
SOLO COMPUTER (user = null)     0 de 203 jugadores-día cambiaron de precio   0,0 %
todas las ventas (con rivales) 19 de 643                                     3,0 %
```

**Cero de 203.** Los 19 cambios son rivales retocando **su propio** anuncio —doce de
ellos exactamente +1.000.000, el recargo de reventa—, no el Computer moviendo un
precio.

Y hay más, que refuerza lo mismo: **el censo del Computer tampoco se mueve.**

```
20260812  17:55 -> 23:43   n=20   salen 0  entran 0
20260813  16:24 -> 22:17   n=20   salen 0  entran 0
20260815  21:52 -> 23:25   n=20   salen 0  entran 0
20260817  20:25 -> 21:42   n=20   salen 0  entran 0
20260910  12:25 -> 12:35   n=20   salen 0  entran 0
20260912  12:42 -> 14:36   n=20   salen 0  entran 0
20260913  08:42 -> 17:17   n=20   salen 0  entran 0
```

Veinte plazas exactas. Los listados nacen a las 07:05 y **todos caducan en el reset
siguiente**: diez nuevos y diez heredados cada mañana.

> **El tablón que ve una puja a las 04:45 es, jugador a jugador y euro a euro, el
> mismo tablón que había a las 07:05 de la mañana anterior. Veintiuna horas y
> cuarenta minutos congelado.**

**Veredicto del bloque 2: la ventana no protege de nada.** Ni hay canal por el que un
rival pueda ver una puja, ni el precio se mueve, ni el censo cambia. La asimetría que
dice la cabecera de `la_subasta` —«llegar tarde cuesta la ventana entera; llegar
pronto, información, y poca»— está bien vista, pero el coste de llegar pronto no es
«poco»: es **cero medido**.

---

## BLOQUE 3 — QUÉ SE GANARÍA, EN PUNTOS

### Primero: la cuenta del encargo da el número bueno por el motivo malo

```
tu cuenta:  135 min / 60  =  2,25 vueltas dentro  ->  ~2 pujas/dia
```

Dos vueltas es correcto. **Pero no las raciona la ventana: las raciona el cron.**

`config/disparos.json`, campo `latido`:

```json
"horas": [0, 1, 2, 3, 8, 9, ..., 23],
"cron":  "7 0-3,8-23 * * *",
"_POR_QUE_ESAS_HORAS": "Salta las 4, 5, 6 y 7 de Madrid..."
```

**El latido horario salta a propósito las horas 4, 5, 6 y 7.** Dentro de la ventana
sólo entran los dos disparos puntuales, a las **04:45 y las 04:50**. Medido sobre las
16 entradas reales de `libro_de_la_ventana.jsonl` (12→19/09, 2 al día, 8 días de 8):

```
minutos al reset al entrar:
  134 133 133 133 132 131 131 130 128 128 128 127 127 121 121 116

banda pisada:  de 134 a 116 min al reset  =  18 minutos
sin una sola vuelta:  117 de 135 minutos  =  el 87 % de la ventana
```

> **La ventana dura 135 minutos y las vueltas ocupan 18. Los 116 minutos pegados al
> reset —justo los que la ventana existe para cubrir— no los pisa nadie, ningún
> día.** Abrirla a 24 h no mete **ni una** vuelta más dentro: para eso hay que tocar
> el cron, que es otro fichero y otra decisión.

### Cuántas pujas saldrían de verdad

Con el tablón congelado 21 h 40 min y el precio quieto, **una vuelta a las 15:00 ve
exactamente la misma cesta** que la de las 04:45. Así que abrir la ventana no añade
candidatos. Lo medido, 8 resets:

| | hoy | ventana 24 h, cupo 3 |
|---|---:|---:|
| días con cesta | 3 de 8 | 3 de 8 (mismo tablón) |
| pujas de la cesta | 4 + 4 + 5 = **13** | 3 + 3 + 3 = **9** |
| pujas/día | **1,63** | **1,13** |

**El cupo de 3 no abriría la puerta: la estrecharía.** Los tres días con trabajo ya
sacaron 4, 4 y 5 pujas —la cesta pone hasta `MAX_PUJAS_PRIMER_DIA = 3` **en una sola
vuelta**, y son dos vueltas—. Un cupo de 3 por reset habría frenado cuatro de las
trece.

Contra tu 1,2 medido (47 apariciones / 40 días): ese 1,2 es de **toda la temporada**,
y el 70 % de ella es anterior a que `la_subasta` existiera. Por tramos:

| tramo | subastas | aparecemos | ganamos | días | ap/día |
|---|---:|---:|---:|---:|---:|
| antes de la subasta (<08/09) | 159 | 26 | 17 | 28 | 0,93 |
| ventana de 15 min (08–09/09) | 9 | 0 | 0 | 2 | **0,00** |
| 135 min, sin libro (10–11/09) | 4 | 1 | 0 | 2 | 0,50 |
| **135 min con libro (12–19/09)** | 60 | **22** | **21** | 9 | **2,44** |

**Las apariciones ya se multiplicaron por 2,6.** Y no fue la ventana: en esos mismos
ocho resets, 11 de las 21 pujas salieron **fuera** de ella.

### Y eso en puntos

Los diez jugadores ganados dentro de la ventana en ocho días:

| jugador | pagado | precio hoy | puntos |
|---|---:|---:|---:|
| Fortuño | 150.376 | vendido | — |
| Diego Conde | 240.601 | vendido | — |
| Balde | 1.604.001 | vendido | — |
| Benavidez | 150.376 | vendido | — |
| Paco Cortés | 150.376 | vendido | — |
| Selu Diallo | 150.376 | vendido | — |
| Marcão | 150.376 | 150.000 | 0 |
| Barzic | 150.376 | 150.000 | **5** |
| Iturbe | 150.376 | 150.000 | 0 |
| Esquivel | 150.376 | 150.000 | 0 |
| **total** | **3.047.610** | | **5** |

**Cinco puntos entre los diez.** Al punto a 21.486 €: **107.430 €**.

Nueve de las diez se pagaron a 150.376 — el suelo de 150.000 más el desvío. **Esta
vía no compra puntos: compra suelo para revenderlo.** Pedir su rendimiento en puntos
es medir un camión en caballos de vapor: el número sale, y no significa nada. Lo que
hay que preguntarle es qué revendió, y eso lo contesta `libro_de_viajes`, no éste.

**Los puntos que la ventana nos cuesta, medidos: ninguno.** Con la ventana abierta
habríamos pujado por los mismos jugadores, al mismo precio, el mismo día.

### Sobre el punto a 21.486 € (doctrina 90)

No vive en el código. Lo calcula el motor cada vuelta como
`points_market.rate_median` y lo publica en la razón de cada valoración. Sus valores
medidos: **21.758** (05/09), **21.372** (17/09), **21.529** (18/09), 21.486 (el tuyo,
hoy). Es un número vivo con una banda de ±1,8 % en quince días. El 107.430 € de
arriba lleva esa banda: **entre 106.860 y 108.790 €**. No cambia nada, porque la
cifra que manda es el 5.

### Cuántas de las 225 subastas cayeron fuera de la ventana

**Cero.**

Las 232 subastas de la temporada —225 hasta el 19/09, más las 7 del reset de hoy, que
entraron en el tablón a las 09:33 mientras medía— se resuelven **todas** entre las
07:02 y las 07:11 de Madrid. La ventana de 04:45 a 07:00 va inmediatamente delante de
cada una. Ninguna cayó fuera.

El número que creo que buscabas es otro, y es peor:

- **159 de 225 (70,7 %)** se resolvieron **antes de que `la_subasta` existiera**
  (antes del 08/09). Ahí no es que Pepe no pudiera mirar: es que no había ojo.
- **9 más** bajo la ventana de 15 minutos, que **no se abrió ni una sola vez** —lo
  dice el commit `e7f8d82`— y en las que aparecimos **0 veces**.
- **60** en la era de los 135 minutos. Aparecimos en 22 y ganamos 21.

> **168 de 225 subastas (74,7 %) pasaron sin que existiera una cesta que mirarlas.
> Ése es el número de veces que Pepe ni siquiera pudo mirar, y no lo causó la
> ventana: lo causó llegar tarde al calendario.**

---

## BLOQUE 4 — EL CUPO POR ENVÍOS

Lo comprobé, y **no**. Con tus palabras, invertidas:

> **`BORDALAS_CUPO_POR_ENVIOS` con puja = 3 no es inútil mientras la ventana siga en
> 135 minutos. Es al revés: es lo único que frena la vía que la ventana no toca, y no
> ve nada de la vía que sí toca.**

Dos hechos, cada uno con su sitio en el código:

**(a) El cupo está cableado en el carril, que no tiene ventana.**
`cupo_por_envios_activo()` se llama en un solo sitio:
[carril_executor.py:230](src/actions/carril_executor.py#L230). El carril
(`la_rendija`) **puja a cualquier hora, a propósito y por escrito**. Lo que el cupo
frenaría, medido:

| ciclo de reset | escrituras | horas (Madrid) | con cupo 3 |
|---|---:|---|---:|
| 2026-09-18 (Boyomo) | 5 | 01:12 · 02:12 · 03:11 · 04:49 · 04:53 | 3 → **2 frenadas** |
| 2026-09-19 (Maffeo) | 9 | 07:23 → 16:15, una por hora | 3 → **6 frenadas** |

**Ocho escrituras frenadas de catorce, y las catorce fuera o a caballo de la
ventana.** Encenderlo habría movido algo — y precisamente donde más duele, que es la
repetición del carril.

**(b) La cesta ni consulta el cupo ni escribe en el libro que el cupo lee.**
`LIBROS_POR_FAMILIA["puja"]` apunta a `libro_del_carril.jsonl`
([el_cupo_de_las_escrituras.py:239](src/analysis/el_cupo_de_las_escrituras.py#L239)).
Las pujas de `la_subasta` se anotan en `bid_outcome_ledger` vía
[`_anotar_en_el_libro`](src/v10_full_autonomous_live.py#L573), **no ahí**. Lo confirma
el fichero: `libro_del_carril.jsonl` tiene 16 filas, las 16 con `marca: RENDIJA`, y
ninguna de las trece pujas de cesta del 12, 15 y 18/09.

Así que las 4, 4 y 5 pujas de la ventana son **invisibles** para el cupo. Y si algún
día se cablea, lo primero que hará es cortarlas a 3.

**Recomendación (no ejecutada, es tuya):** el cupo por envíos no se pospone por la
ventana. Se enciende o no por sus propios números —y `la_puja_que_ya_esta`
(`filtrar_los_repetidos`) tapa la repetición por identidad mejor que un cupo, que es
volumen (doctrina 93)—. Ninguno de los dos está puesto en
`.github/workflows/bordalas-live.yml`, que sólo exporta `BORDALAS_BID_SALT`.

---

## LO QUE NO HICE, Y POR QUÉ

- **No toqué `VENTANA_MINUTOS`.** El número es tuyo y el encargo lo mide. Además el
  135 en sí está bien puesto: con menos, el disparo de las 04:45 no entra.
- **No toqué ningún otro umbral, ni el workflow, ni encendí ningún interruptor.**
- **Ni una escritura contra Biwenger.** Todo sale de disco: `board_events.json`,
  `bid_outcome_ledger.json`, `libro_de_la_ventana.jsonl`, `libro_del_carril.jsonl`,
  las 106 fotos de `data/snapshot_*.json` y `config/disparos.json`.
- **No arreglé que `libro_del_carril.jsonl` no vea las pujas de la cesta.** Es un
  camino de escritura y no lo pedías. Queda apuntado arriba.
- **No conté las pujas de los cinco días con cesta vacía** como «perdidas por la
  ventana». Con el tablón congelado 21 h 40 min, habrían estado vacías a cualquier
  hora, y decir lo contrario sería una simulación disfrazada de medición.
- **No puedo decir el orden de las tres pujas perdidas contra un rival.** El dato no
  existe en ninguna fuente. Eso es un límite de Biwenger, no del trabajo.

### La verja

**Roja, y ya lo estaba.** `5 de 159` fallan en
`guardias/separar-las-dos-poblaciones`, el punto de partida, sin que yo haya tocado
una línea de código:

```
src.analysis.test_presupuesto_de_fichar_v1
src.analysis.test_dashboard_orden_de_variables_v1
src.analysis.test_el_ciclo_publica_v1
src.analysis.test_la_lista_blanca_v1
src.analysis.test_orden_de_venta_v1
```

Son de cableado del panel y de presupuesto, heredadas de la rama base y ajenas a
esto. No las arreglo aquí porque este encargo no toca código, pero **no se sube nada
encima hasta que estén verdes**. Salida completa a fichero, árbol quieto.

### El `n`, y cuándo se cortó

| medida | `n` | corte |
|---|---|---|
| subastas de la temporada | 225 (232 con el reset de hoy) | tablón a 20/09 09:33 |
| apariciones / conversión | 47 aparece · 36 gana · **76,6 %** | idem, hasta 19/09 |
| pujas nuestras, sin duplicar | 35 operaciones · 29 ganadas · **82,9 %** | `bid_outcome_ledger` |
| pujas de la cesta | 13 · 10 ganadas · **76,9 %** | 8 resets, 12→19/09 |
| entradas en la ventana | 16 · 2/día · 8 días de 8 | `libro_de_la_ventana` |
| precio intradía del Computer | **0 de 203** jugadores-día | 9 días con ≥2 fotos |
| censo intradía del Computer | 0 altas / 0 bajas en 7 de 9 días | idem |

El tablón creció de 225 a 232 subastas **mientras medía** —una vuelta de producción
escribió a las 09:33—. Doy las dos cifras. La conversión pasa de 76,6 % a 77,6 %; no
cambia ninguna conclusión.

---

## LO QUE YO HARÍA, Y NO HICE

Por orden de lo que mueve un euro:

1. **El cupo por envíos no depende de la ventana.** Decidir sobre él con sus números.
2. **Si se abre la ventana, abrirla no basta.** El latido salta las horas 4–7 a
   propósito; sin tocar `config/disparos.json` no entra una vuelta más. Y el tablón
   congelado dice que ni así saldrían más pujas.
3. **Lo que la ventana sí cuesta es robustez, no pujas.** Toda la vía de la cesta
   cuelga de dos vueltas en 18 minutos. La vuelta #1699 se colgó y GitHub la mató a
   los 35. Si le toca a la de las 04:45 y a la de las 04:50, el día entero se pierde
   sin que nadie lo note. Ése es el riesgo real, y es un argumento **a favor** de
   abrirla — pero por seguro, no por volumen.
