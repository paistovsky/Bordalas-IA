# INFORME — EL CUPO, EL ESCAPARATE Y EL SILENCIO

Fecha: 2026-09-19 (cuarto del día) · Rama: `arreglo/el-cupo-y-el-silencio`

Interruptor nuevo, apagado: **`BORDALAS_CUPO_POR_ENVIOS`**.
Los tres de antes siguen apagados y no los he tocado.

---

## DOS CORRECCIONES MÍAS, Y LAS DOS ORDENABAN BLOQUES TUYOS

**1. «La publicación número 16 es distinta» — no lo es.** Preguntaste por qué esa
una sobrevive. Las dieciséis filas de `libro_de_escaparate.jsonl` son **idénticas**:
mismo jugador, mismo `listed_price` (3.139.500), mismo mercado, mismo margen, todas
HTTP 204. El «1 operación» de mi tabla era el recuento **deduplicado**, y la que
sobrevive es simplemente la **primera**. Mi tabla daba a entender otra cosa.

**2. «Vender/salida: no escribe libro» — sí escribe.** `salida_executor` anota en la
línea 171. Lo que pasa es que nunca ha corrido, así que el fichero no existe. «El
libro no existe» y «no escribe libro» no son lo mismo, y yo los junté en la misma
fila con una raya.

---

## BLOQUE 1 — QUE EL CUPO CUENTE LO QUE SE ENVÍA

### Dónde se cuenta hoy, con la línea delante

```python
# libro_de_viajes.cuantos_en_este_reset:521
if fila.get("state") != ABIERTO:
    continue
```

Cuenta filas de `libro_de_viajes.jsonl` con `state == ABIERTO`. **Un viaje sólo se
abre cuando la puja se gana.** Ese número va a:

```python
# la_rendija.permiso:1461
quedan_reset = max(0, cupo["cupo"] - operaciones_en_este_reset)
```

Entre poner la puja y ganarla el contador no se mueve, así que repujar es gratis:
**nueve escrituras de Maffeo contra un cupo de 1.** El portero no se enteró porque
estaba contando otra cosa.

Y el segundo cupo tampoco mordía: `escrituras_en_esta_vuelta` vale 0 por defecto y
**nadie se lo pasa** — `carril_executor` llama a `permiso()` sin ese argumento.

### Cómo queda

`el_cupo_de_las_escrituras.escrituras_enviadas()` cuenta filas con `sent: True`
desde el reset, **por familia y sin deduplicar** — si dedujera por `event_id`,
repetir volvería a ser gratis. La identidad de la operación sigue siendo el
`event_id`, que es otra pregunta y otro sitio.

Y el motivo lo dice entero, como pediste:

> «puja»: van 1 escritura(s) enviada(s) de un cupo de 1 en este reset. No se escribe
> ninguna más.

Con doctrina 24 dentro: un libro que **no existe** sí es un cero —esa familia no ha
escrito nunca—; un libro que existe y **no se puede leer** es «no lo sé», y con eso
no se escribe.

### Uno solo o uno por familia — **uno por familia**

Y no es opinión, lo dice la medición. Demanda **legítima** por reset (ya sin
repeticiones, n=5 resets con actividad, 10/09 → 18/09):

| familia | pico legítimo en un reset |
|---|---:|
| **renovar** | **9** |
| puja | 2 |
| publicar | 1 |

Un cupo compartido dimensionado para la puja **estrangula a renovar**; dimensionado
para renovar deja pujar nueve veces, que es otro riesgo entero. Y las unidades no
son comparables: renovar es mantenimiento y no compromete un euro; pujar sí.

### Cuántas de las 43 no habrían salido — y aquí hay un aviso

Con el cupo **actual de 1** por familia y reset, contando envíos:

```
saldrían  6 de 43      NO saldrían 37
   puja       frenadas 12 de 16
   publicar   frenadas 15 de 16
   renovar    frenadas 10 de 11
```

**Mira las diez de `renovar`.** No son repeticiones: son **diez jugadores
distintos** el 10/09 a las 10:25 —Jonny, Manu Sánchez, Jutglà, Zubeldia, Djené,
Pablo Ibáñez…—, renovaciones perfectamente legítimas. Un cupo de 1 las mata.

**Eso enseña que el cupo no es la herramienta contra la repetición.** El cupo limita
**volumen**; la repetición es un problema de **identidad**, y de eso se encarga
`filtrar_los_repetidos`. Son dos piezas distintas y hacen falta las dos.

El detalle completo con nombre y familia está en el commit; las 37, una a una.

### El número nuevo — lo propongo, no lo pongo

Con el pico observado más holgura, y **con la guardia de identidad puesta antes**
(si no, el cupo se come repeticiones en vez de trabajo):

| familia | pico medido | propuesta | por qué |
|---|---:|---:|---|
| renovar | 9 | **12** | mantenimiento, no compromete dinero; el pico fue 9 y la plantilla son 18 |
| puja | 2 | **3** | compromete caja; el pico fue 2 y el cupo de viajes ya lo acota por otro lado |
| publicar | 1 | **4** | idempotente y barata, pero 16 en un día fue un fallo, no demanda |
| vender / aceptar / reroll / alineación | sin datos | — | no se propone lo que no se ha medido |

**n = 5 resets.** Es poco para fijar un tope, y lo digo: con la foto diaria en git
desde ayer, en una semana habrá una base mejor. Por eso va **apagado** y los números
los pones tú.

---

## BLOQUE 2 — EL ESCAPARATE

### Por qué la número 16 no es distinta, y por qué pasó

Las dieciséis son idénticas. **El fallo raíz ya estaba arreglado, la misma noche.**
Lo cuenta el propio código:

> **LA CLAVE `rows` NO EXISTÍA (13/09/2026, noche).** Dos sitios la pedían —el
> escaparate, para saber qué ya está en venta, y `viajes_sin_listar`, para lo mismo—
> y los dos recibían `[]` **siempre**. La comprobación de «esto ya está publicado» no
> podía dar nunca que sí.

Las dieciséis publicaciones son del 13/09 de 12:05 a 20:10 — **antes** de ese
arreglo. Y no hay ni una repetición del escaparate después.

Así que el 93,8 % que publiqué ayer como «el peor» es la medición de un fallo ya
reparado. El freno de idempotencia existía (`if pid in en_venta`); lo que no existía
era el dato que lo alimenta.

### Lo que sí seguía abierto, y es lo que he arreglado

**1. El freno no distinguía precio.** `en_venta` era un conjunto de `player_id` a
secas, así que «ya está publicado» tapaba dos casos: al **mismo** precio (no tocar)
y a **otro** precio (republicar). **Cambiar el precio de una publicación era
imposible por este camino**, y una publicación **caducada** no se volvía a poner
nunca.

Ahora lleva `listed_price` y `expired`, y sólo frena si es la misma publicación y
sigue viva. Publicada a precio **desconocido** tampoco se toca: bajarla a ciegas es
peor que dejarla.

**2. `rows: []` seguía valiendo por dos cosas.** `compact_listings` publica ahora
`available`, y `que_publicar` no publica a ciegas.

### Y la tercera vez de la frase de Trent tiene la misma raíz

`viajes_sin_listar` con la lista de publicaciones vacía ve **todo** viaje como
huérfano. Por eso el panel decía «comprado y sin publicar» **mientras lo publicaba
dieciséis veces**: las dos frases salían del mismo hueco, el mismo día. Misma
barandilla puesta.

---

## BLOQUE 3 — EL SILENCIO

### Los sitios donde un vacío se lee como un «no»

El patrón crudo —una colección consumida como pertenencia sin mirar `available`— da
**85 sitios** en `src/`. Pero la mayoría son lectura de pantalla, donde un vacío de
más sólo pinta mal. Los que **gobiernan una escritura o un salto** los he mirado uno
a uno:

| sitio | qué decide | estado |
|---|---|---|
| `acquisition_board.py:478` — `puja_viva` ← `exposicion.operations` | si hay puja viva → si se repuja | **arreglado hoy** |
| `compact_listings` → `escaparate_executor` | si ya está publicado → si se republica | **arreglado hoy** |
| `compact_listings` → `viajes_sin_listar` | si falta por publicar | **arreglado hoy** |
| `decision_orchestrator.players_with_live_bid:464` | el conjunto de ocupados | **sigue abierto** |
| `solvency_engine.py:478` — `incoming.get("offers", [])` | qué se reserva | **comprobado, cae del lado seguro** |
| `bid_outcome_ledger.py:1116` — `exposicion.operations` | qué pujas se recogen del tablón | **sigue abierto** (medición, no escritura) |

**`players_with_live_bid` sigue siendo una mina.** No mira `available`: lee
`speculation.bid_exposure.operations` directamente. Mi `lo_que_ya_esta_puesto`
comprueba `available` **antes** de llamarla, así que el camino de escritura está a
salvo — pero el siguiente que la use sin esa precaución se lleva el vacío silencioso.
No la he tocado porque cambiar su contrato toca a sus llamadores y hoy son dos.

**`solvency_engine:478` cae del lado bueno:** sin ofertas, `reserved_total = 0` y
`debt_covered_by_secured` sale **False** — dice que la deuda NO está cubierta, que es
la afirmación prudente. Queda comprobado, no arreglado.

### Y lo que enseña el conjunto

El mismo fallo dio **las dos facturas del día**: las nueve pujas de Maffeo
(`operations` vacío) y las dieciséis publicaciones de Trent (`rows` vacío). No es un
descuido en dos sitios: es que **la forma «lista vacía» no tiene sitio para decir “no
lo sé”**, y el que la consume no tiene cómo preguntarlo.

Por eso lo que he puesto no es un `if` más, sino un campo: `available` /
`live_bid_known` / `lo_publicado_se_sabe`. El dato dice si se puede creer.

---

## BLOQUE 4 — EL NÚMERO QUE DECIDE EL TOPE

### Cuánto sube la probabilidad entre +0,52 % y +1,95 %

Con la curva calibrada (91 muestras) y su `n` por peldaño:

| factor | prima | peso | n |
|---:|---:|---:|---:|
| 1.0000 | +0,00 % | 0,1978 | 18 |
| **1.0052** | **+0,52 %** | 0,1978 | 18 |
| **1.0195** | **+1,95 %** | 0,1978 | 18 |
| 1.0307 | +3,07 % | 0,1978 | 18 |
| 1.0529 | +5,29 % | 0,1538 | 14 |
| 1.2027 | +20,27 % | 0,0549 | 5 |
| 1.2449 | +24,49 % | 0,0 | 0 |

```
P(ganar) a +0,52 %   =  0,2330
P(ganar) a +1,95 %   =  0,4046
                        ---------
sube                    +0,1716   (+17,16 puntos porcentuales, un +74 % relativo)
```

**No «apenas se mueve». Se mueve mucho.** Y el salto es el mismo en los dos casos
porque depende del precio, no del valor.

### La cuenta en euros, con el punto a 21.451 €

| | puja a +0,52 % | puja a +1,95 % | coste extra | EV sube | en puntos |
|---|---:|---:|---:|---:|---:|
| **Chust** (1.850.000) | 1.859.621 | 1.886.076 | **26.455 €** | **+61.099 €** | coste 1,23 pt · gana 2,85 pt |
| **Dmitrovic** (4.740.000) | 4.764.649 | 4.832.431 | **67.782 €** | **+98.748 €** | coste 3,16 pt · gana 4,60 pt |

- Chust: el valor esperado sube **2,31 veces** lo que cuesta la puja extra.
- Dmitrovic: **1,46 veces**.

### Si el tope se queda como está

Me pediste decirlo con esas palabras si la probabilidad apenas se movía. **La
condición no se cumple, así que digo lo contrario:** con la curva calibrada,
**+0,52 % no es dinero ahorrado — es valor esperado que se deja en la mesa.** En
Chust son 61.099 € de EV por 26.455 € de puja.

**No propongo cambiar el tope.** El número es tuyo y el encargo lo pone por escrito.
Ahí está la medición.

Una salvedad honesta: el valor de Chust (2.278.096) es el real del tablero; **el de
Dmitrovic lo he puesto yo** (5.500.000) porque no consta en ninguna foto. El salto de
probabilidad no depende de él, pero los euros de EV sí.

---

## BLOQUE 5 — LOS TRES LIBROS NUEVOS

| familia | dónde escribía antes | libro nuevo |
|---|---|---|
| aceptar oferta | `autopilot_executor:711` y `:960` — nada | `libro_de_aceptadas.jsonl` |
| reroll | `:1204` — sólo `record_reroll` si `success` | `libro_de_rerolls.jsonl` |
| guardar alineación | `:2543` — nada | `libro_de_alineaciones.jsonl` |

Misma forma que los que ya existen: `at`, `sent`, `http_status`, `success`,
`response`. Y **anotan aunque falle** — `record_reroll` sólo se llamaba con
`success`, así que un reroll fallido no dejaba ni una línea.

### Qué clave usan

**El `event_id` que devuelve Biwenger.** Nunca la marca de tiempo: ya nos mordió dos
veces —la reja del tablón con la fecha dentro de la clave, y el libro de pujas con
`player_id:placed_at`— y las dos una operación se convirtió en muchas.

Cuando Biwenger **no** devuelve id —guardar una alineación no lo trae— la identidad
es la **huella del contenido**: los once ordenados y la formación, en SHA-256 corto.
Dos guardados idénticos son el mismo hecho; uno con otra formación es otro. **El
reloj no entra.**

La hora viaja al lado en `at`, donde no manda. Y el cupo cuenta **filas**, no claves:
si dedujera por `event_id`, repetir volvería a ser gratis.

Los tres van blindados: una escritura ya confirmada por Biwenger no puede caerse por
un fallo apuntándola.

---

## BLOQUE 6 — LOS DOS CABOS

### a) El candidato bloqueado — hecho, con tu condición

Un tercer `elif` en `decision_orchestrator`, junto a los dos que ya existían:

> «Hay 1 candidato(s) pujable(s) y no se genera ninguna puja: Para mejorar el once:
> 0 EUR. Son 0 de caja.»

**Y no puede presidir, por construcción:**

```python
PRIORITY["PUJA_BLOQUEADA"] = -1
```

Por **debajo** de `IDLE`, que se añade **siempre**. Como `decision = candidates[0]`
sale de la lista ordenada descendente, esto no puede ser el titular nunca — no por
suerte, por aritmética. Las vueltas tranquilas siguen diciendo IDLE.

Tampoco entra en la cola ejecutable (`build_action_queue` filtra `executable=True`),
y el panel ya lo sabe llamar: «Puja bloqueada».

Con esto **se cierra la última guardia que quedaba roja** de las tres.

### b) Las tres hermanas — convertidas. Pero no son tres

`test_accept_before_expiry_safety_v2`, `_v21` y `_simulated_safety_v1` están ahora en
`scripts/mirar_*.py`, con su cabecera y el motivo. Nadie las referenciaba.

**Y al convertirlas salí a contar: son 69.** Ficheros `test_*` en `src/analysis/` que
llaman a `get_latest_snapshot()`:

```
69 guardias leen estado de produccion
```

No es un descuido suelto: es **una era entera del repositorio**, de cuando las
pruebas se escribían contra la foto de producción. Convertir 66 más a mano no es el
arreglo — sería un commit de 66 ficheros que nadie puede revisar.

**Lo que propongo, y lo decides tú:**

1. Que `regression_check.py` separe las dos poblaciones: guardias de verdad y
   scripts de diagnóstico. Hoy están mezcladas y por eso un rojo no significa nada.
2. Que ninguna **nueva** pueda leer `get_latest_snapshot()` — eso sí es una guardia
   de una línea sobre el árbol de ficheros, y la escribo cuando digas.
3. Las 66 restantes, según se vayan tocando. No de golpe.

Estaba midiendo cuántas de las 69 están en rojo ahora mismo y **el barrido sigue
corriendo** cuando cierro esto; lo único que puedo afirmar es que al menos una lo
está (`test_accept_offer_live_v1`, comprobado que ya fallaba antes de tocar yo nada).

---

## LO QUE NO HICE, Y POR QUÉ

- **Ni una escritura contra Biwenger.**
- **No encendí ningún interruptor.** Ni los tres de antes, ni el nuevo.
- **No cambié el tope del once** ni lo propuse como recomendación. El bloque 4 es
  medición y está entregado como medición.
- **No puse ningún número nuevo.** Los cupos por familia van como propuesta con su
  razón y su `n`, y el interruptor va apagado precisamente para que no se apliquen
  solos.
- **No subí las escrituras por vuelta.** Y ahora con un motivo más: el cupo actual
  contando envíos frenaría 37 de 43, así que primero van los números por familia.
- **No toqué** `MAX_SINGLE_SPECULATION_PERCENT`, `MAX_SAFE_DEBT`, el suelo de cobro,
  `MIN_WIN_PROBABILITY`, `MAX_PROJECTED_DAILY_RATE`, las cinco de `PUEDEN_ENCERRARLO`
  ni el tope de reventa.
- **No apliqué `stash@{0}`.**
- **No toqué `bordalas-live.yml`.** Lo del `input` para la vuelta manual sigue
  escrito en el informe de ayer.
- **No arreglé `players_with_live_bid`.** Cambiar su contrato toca a sus llamadores;
  el camino de escritura ya está a salvo por otro lado y prefiero decirlo a tocarlo
  de paso.
- **No convertí las 66 guardias restantes.** Propuesta arriba.
- **No empujé nada.**

### Lo que haría mañana, en orden

1. Los números de cupo por familia, si los das — es lo único que falta para encender
   `BORDALAS_CUPO_POR_ENVIOS`.
2. La guardia de una línea que impida que una prueba nueva lea producción.
3. `players_with_live_bid`, con sus dos llamadores.
4. Volver a medir el desperdicio dentro de una semana, con los tres libros nuevos
   escribiendo y la foto diaria en git. Hoy el `n` es 43 escrituras en 5 días; eso es
   poco para fijar topes y lo he dicho cada vez que ha hecho falta.
