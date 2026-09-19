# INFORME — LAS ESCRITURAS DESPERDICIADAS Y LA CURVA

Fecha: 2026-09-19 (tarde, tercero del día) · Rama: `arreglo/las-escrituras-y-la-curva`

Interruptor nuevo, apagado: **`BORDALAS_NO_REPETIR_LA_ESCRITURA`**.
Los dos de esta mañana siguen apagados y no los he tocado.

---

## ANTES DE NADA: UNA MÍA, Y ES LA QUE ORDENABA EL BLOQUE 2

Esta mañana publiqué **«161 subastas observadas, 0 usadas»** y construiste un bloque
entero sobre eso. Era falso, y el fallo era de mi banco de pruebas.

Llamé a `build_bid_model` **sin `price_lookup`**. Y sin él, el bucle que recorre las
pujas no se ejecuta:

```python
if price_lookup is not None:
    for manager in (managers or []):
        ...
```

La firma estaba delante y no la leí: **cero muestras Y cero descartadas a la vez**.
Si de verdad se estuvieran tirando pujas, `discarded_no_price` sería mayor que cero.

En producción `acquisition_board` **sí** lo pasa
(`price_lookup=build_historical_price_lookup()`), y la foto del 18/09 16:16:38 —la
que empezamos a guardar ayer— lo confirma: `calibrated: True`, `samples: 83`.

Es la doctrina 89 mordiendo al día siguiente de escribirla. El dato decía algo
absurdo y lo publiqué como hallazgo en vez de comprobar si había ocurrido.

**La curva lleva calibrada todo el tiempo.**

---

## BLOQUE 1 — EL 75 % DE ESCRITURAS DESPERDICIADAS

### El desglose

Sobre los libros que registran lo que de verdad salió contra Biwenger —los que
llevan `sent` y `http_status`—, ventana **10/09 10:25 → 18/09 14:15**, n=43
escrituras en 5 días con actividad:

| familia | escrituras | operaciones distintas | de más | desperdicio | n · plazo |
|---|---:|---:|---:|---:|---|
| **publicar** | 16 | 1 | 15 | **93,8 %** | n=16 en 8,1 h (13/09) |
| **puja** | 16 | 4 | 12 | **75,0 %** | n=16 en 143,5 h |
| **renovar publicación** | 11 | 9 | 2 | 18,2 % | n=11 en 0,2 h (10/09) |
| vender / salida | 0 | — | — | — | `libro_de_salidas.jsonl` no existe |
| aceptar oferta | — | — | — | — | el executor no escribe libro |
| reroll | — | — | — | — | ídem |
| guardar alineación | — | — | — | — | `state.json`, sin histórico |
| **TOTAL** | **43** | **14** | **29** | **67,4 %** | |

**El peor no es la puja: es publicar.** Trent, **dieciséis publicaciones al mismo
precio (3.139.500) en 8,1 horas**, todas `sent: true`, todas HTTP 204.

Las repeticiones, una por una:

| familia | quién | veces | span |
|---|---|---:|---:|
| publicar | Trent | 16 | 8,1 h |
| puja | Maffeo | 9 | 8,9 h |
| puja | Boyomo | 5 | 3,7 h |
| renovar | Jonny | 3 | 0,0 h |

**Lo que acota el arreglo:** tres familias no tienen ninguna repetición porque no
tienen ninguna escritura. `vender/salida` nunca ha escrito —su libro no existe—, y
`aceptar oferta` y `reroll` no llevan libro, así que no puedo medirlas. Si repiten,
no me consta.

### El fallo, con nombre — y son tres encadenados

**1. En el camino de escritura no se pregunta.** No es que nadie sepa. El tablero
lo sabe:

- [`acquisition_board.py:924`](src/analysis/acquisition_board.py#L924) calcula `has_live_bid` por fila;
- la línea 1333 la usa para mandar esas filas al final del orden;
- la línea 1554 las descuenta de `actionable`;
- y la línea 1400 **las mete a propósito** en `targets`, «para que el recorte no
  pueda esconder nuestro propio dinero».

[`carril_executor.py:224`](src/actions/carril_executor.py#L224) recibe esas mismas filas y las filtra por tres cosas:

```python
and safe_int(t.get("market_price")) >= suelo["suelo"]
and str(t.get("status") or "").lower() == "ok"
and not t.get("outside_computer_market")
```

Y por ninguna más. **El campo llega intacto a la línea de la escritura.** De tus dos
sospechas es la primera, sin matices: no pregunta.

**2. Y la respuesta puede llegar vacía sin que se note.** `has_live_bid` sale de
`puja_viva`, que se llena de `exposicion["operations"]`
([`acquisition_board.py:478`](src/analysis/acquisition_board.py#L478)). Si la exposición no está disponible, ese
diccionario queda vacío y **todas** las filas salen `has_live_bid: False`.

O sea: «no hay pujas vivas» y «no he podido mirar» se escriben igual. Tu segunda
sospecha existe, pero como riesgo latente, no como lo que pasó.

**3. Y por eso no lo caza nadie aguas abajo — ésta es la tercera y creo que es la
raíz.** El cupo del reset cuenta **viajes abiertos**, no escrituras enviadas:

```python
# libro_de_viajes.cuantos_en_este_reset
if fila.get("state") != ABIERTO:
    continue
```

Un viaje sólo se abre cuando la puja se **gana**. Así que repujar al mismo jugador
no incrementa nada y `quedan_en_el_reset` nunca baja. **Nueve escrituras contra un
cupo de 1**, y el portero no se enteró porque está contando otra cosa.

### El freno

[`la_puja_que_ya_esta.filtrar_los_repetidos()`](src/analysis/la_puja_que_ya_esta.py), llamado en `carril_executor`
**después** de `los_que_se_pueden_pagar` y **antes** de `a_quien_pujar`: así el
hueco que libera un repetido se lo queda el siguiente de la lista en la **misma
vuelta**, en vez de perderse.

El conjunto sale de `players_with_live_bid()` —doctrina 84, ya existía y nunca la
llamó nadie desde aquí—. Lo único nuevo es el detalle, porque el motivo tiene que
nombrar a quien decidió:

> «Ya hay una operación viva por Maffeo: oferta 399977192 por 1.664.350 EUR. No se
> escribe otra.»

Y cuando **no se puede mirar**, no se escribe nada, con otro motivo (`NO_SE_SABE`)
porque se arregla en otro sitio:

> «La exposición de pujas no está disponible (No se pudo leer el tablón de ofertas):
> no se sabe qué tenemos puesto. Un fallo de lectura no es vía libre.»

Interruptor: **`BORDALAS_NO_REPETIR_LA_ESCRITURA`**, apagado.

### La cuenta que decide

Por día, sobre las mismas 43 escrituras:

| día | escrituras | operaciones | de más | desperdicio |
|---|---:|---:|---:|---:|
| 10/09 | 11 | 9 | 2 | 18,2 % |
| 12/09 | 1 | 1 | 0 | 0,0 % |
| 13/09 | 16 | 1 | 15 | 93,8 % |
| 17/09 | 2 | 2 | 0 | 0,0 % |
| 18/09 | 13 | 2 | 11 | 84,6 % |
| **total** | **43** | **15** | **28** | **65,1 %** |

**n = 5 días. Media: 8,60 escrituras/día contra 3,00 operaciones distintas/día.**

Y aquí va la parte honesta, porque la cuenta no es automática: **la guardia no crea
operaciones, libera capacidad.** Una escritura ahorrada sólo se convierte en
operación nueva si había otro candidato distinto esperando.

```
cota superior (toda ahorrada se convierte) :  3,00  ->  8,60 op/día   (x2,87)
cota inferior (nunca había otro candidato) :  3,00  ->  3,00 op/día   (x1,00)
```

**El único dato que puedo comprobar dice que sí había.** La foto del 18/09 16:16:38
—en mitad de las nueve repujas de Maffeo— dice:

```
biddable        2     candidatos pujables
with_live_bid   1     Maffeo, ya puesto
actionable      1     pujables SIN puja viva   <- había otro esperando
```

Con `n=1` foto no puedo extrapolarlo a las demás vueltas, y no lo hago (doctrina
58). Desde mañana, con una foto al día, se podrá.

**Mi respuesta a tu pregunta:** no es «de 4 a 16». Está entre **×1,00 y ×2,87**, y
la única vuelta que puedo verificar tenía la conversión disponible. Yo lo
encendería, pero con la cuenta puesta así y no con el ×4 que sugería el 75 %.

Y una cosa que sí es segura sin depender de la conversión: **doce de esas escrituras
no hacían nada.** Cada una es una llamada de escritura contra Biwenger por una puja
que ya estaba puesta al mismo importe. Eso se quita gane lo que gane.

---

## BLOQUE 2 — LA CURVA

### 1 · Por qué 0 de 161 → **no era el sistema, era mi medición**

Ya está arriba. El número real, medido hoy con el informe actual:

```
pujas observadas en el informe : 169
  sin precio de aquel momento  :  64
  por debajo del precio salida :  14
  USABLES                      :  91     calibrated: True
```

Y en la foto del 18/09, 83. La curva nunca dejó de calibrarse.

### 2 · Los peldaños, de la masa observada

**Ya salían de ahí** (doctrina 84): `CORTES_DE_LA_CURVA` son cuantiles y los pesos
se cuentan sobre las pujas que caen en cada banda, con
`MIN_SAMPLES_PER_RUNG = 5` ya en vigor, arreglado el 16/09 precisamente para dejar
de usar 1/7. No he escrito una segunda.

**El mínimo por peldaño lo justifica el propio código y lo mantengo**: con N≈90, el
intervalo de Wilson al 95 % sobre el peso mide ×30,4 de ancho con n=1, ×8,1 con
n=3 y ×5,1 con n=5. Por debajo de cinco el número deja de ser una medida.

**Lo que sí estaba mal y he arreglado.** El último peldaño absorbía el redondeo para
que la curva sumase uno:

```python
peso = round(1.0 - acumulado, 4)
```

Dos formas de mentir, y las dos ocurrían:

- **Negativo.** Con los seis de arriba redondeando hacia arriba, sale por debajo de
  cero. En la foto del 18/09 el peldaño `1.2449x` publicaba **`-0.0001`**.
  No es un detalle de coma: en `win_probability` ese peso **resta** de la
  probabilidad de que un rival nos supere, así que Pepe se cree más ganador de lo
  que es y puja menos. **El sesgo va en la dirección cara.**
- **Inventado.** Con `n = 0` ese residuo no es masa observada de nada: es el sobrante
  del redondeo puesto donde no cayó ni una puja.

Ahora un peldaño vacío pesa `0.0` y sale `calibrated: False`. El peldaño **flojo**
(1 ≤ n < 5) **no se toca**: conserva su peso observado y su aviso, porque borrarlo
afirmaría «ningún rival paga tanto» cuando alguno pagó.

Estado tras el arreglo:

| factor | prima | peso | n | calibrado |
|---:|---:|---:|---:|:---:|
| 1.0000 | +0,00 % | 0,1978 | 18 | sí |
| 1.0052 | +0,52 % | 0,1978 | 18 | sí |
| 1.0195 | +1,95 % | 0,1978 | 18 | sí |
| 1.0307 | +3,07 % | 0,1978 | 18 | sí |
| 1.0529 | +5,29 % | 0,1538 | 14 | sí |
| 1.2027 | +20,27 % | 0,0549 | 5 | sí |
| 1.2449 | +24,49 % | **0,0** | 0 | **no** |

**Queda uno sin calibrar de siete**, con el mínimo en 5.

### 3 · Cuántas caen entre 0 y 2 % — **38 de 91, el 41,8 %**

No son cuatro. Es la banda más densa de todas:

| banda | n | % |
|---|---:|---:|
| +0,0 % a +0,5 % | 18 | 19,8 % |
| +0,5 % a +1,0 % | 9 | 9,9 % |
| +1,0 % a +1,5 % | **4** | 4,4 % |
| +1,5 % a +2,0 % | 7 | 7,7 % |
| **0 % a 2 %** | **38** | **41,8 %** |
| +2,0 % a +3,0 % | 15 | 16,5 % |
| +3,0 % a +5,0 % | 17 | 18,7 % |
| +5,0 % a +10,0 % | 11 | 12,1 % |
| +10 % o más | 10 | 11,0 % |

Mediana +2,48 %. La curva **sí sabe describir esa zona**: tiene tres peldaños dentro
(+0,00 %, +0,52 %, +1,95 %).

Un matiz que te debo: la sub-banda donde cayó tu puja de Chust —+1,0 % a +1,5 %—
tiene **n=4**, por debajo del mínimo de 5. La zona de 0–2 % es densa; ese tramo
concreto, no.

### 4 · La tabla, con las cuatro columnas

| jugador | precio | pujó el dueño | % | Pepe HOY | curva nueva sin tope | curva nueva con tope del once |
|---|---:|---:|---:|---:|---:|---:|
| Chust | 1.850.000 | 1.871.032 | +1,14 % | **+5,29 %** (1.947.866) | +5,29 % | **+0,52 %** (1.859.621) |
| Dmitrovic | 4.740.000 | 4.782.000 | +0,89 % | **+5,29 %** (4.990.747) | +5,29 % | **+0,52 %** (4.764.649) |
| Cabrera | 2.920.000 | 3.116.031 | +6,71 % | **+5,29 %** (3.074.469) | +5,29 % | **+0,52 %** (2.935.185) |

Nota sobre la columna «Pepe HOY»: como la curva ya estaba calibrada, **hoy Pepe puja
+5,29 %, no +5,00 %**. El +5,00 % que reporté esta mañana era la curva por defecto,
o sea otra vez mi banco de pruebas sin `price_lookup`. Las columnas «hoy» y «curva
nueva sin tope» son la misma cosa por eso mismo: la curva no cambia, sólo se le
quitó la probabilidad negativa del último peldaño.

Y **el tope ya no colapsa a «puja lo mínimo»**: con la curva calibrada cae en
+0,52 %, que es un peldaño real, no el suelo.

### 5 · ¿Sobra el tope del once? — **no sobra, pero 1,2525 % cae en un hueco**

No sobra, por una razón medida: sin él Pepe paga **+5,29 %**, cuatro veces y media
lo que pagaste tú por Chust. Un techo hace falta.

Pero **1,2525 % aterriza justo entre dos peldaños**: por encima de 1.0052 (+0,52 %)
y por debajo de 1.0195 (+1,95 %). Así que el techo recorta al peldaño de abajo y
Pepe puja +0,52 % — por debajo de tus dos pujas, y probablemente perdiendo.

La consecuencia, con los números delante:

```
sin tope        +5,29 %   paga de más
tope 1,2525 %   +0,52 %   se queda corto de tus dos pujas
un tope >= 1,95 %         permitiria el peldaño de +1,95 %,
                          que cubre tus +1,14 % y +0,89 %
```

**No lo cambio** —el tope lo decidiste tú y no está entre lo que puedo mover— pero
ahí está la medición. Un tope apenas por encima del peldaño de +1,95 % haría lo que
creo que querías: techo real contra el +5,29 %, y sitio para pujar donde tú pujaste.

---

## BLOQUE 3 — LAS DOS GUARDIAS

### a) La que lee producción — **la he convertido, ni arreglada ni borrada**

Elegí una tercera, y te digo por qué las otras dos no me convencieron.

**Borrarla** perdía algo único: es la **única** que comprueba el cableado entero
—que `build_global_decision` llegue a emitir los candidatos WATCH y SAFETY—. Sus
tres hermanas miran el tablero, no el orquestador.

**Arreglarla con un caso fijo** sale caro, y lo comprobé en vez de suponerlo: hacen
falta una foto de 285 KB escrita a mano **y** un calendario de mentira, porque
`build_deadline_state` baja a leer `data/calendar/`. Lo intenté y revienta en
`calendar_state.get_biwenger_round_id`. Eso es montar un segundo banco de pruebas
para un camino ya cubierto por unidades.

Así que se queda **lo que de verdad era**: `scripts/mirar_accept_before_expiry.py`,
una herramienta de mano para cuando haya ofertas vivas. Fuera de
`regression_check.py`, con el motivo escrito en su cabecera.

Lo que sí queda cubierto **con datos fijos**: la puerta del reloj y que la reserva
ceda (`test_la_reserva_no_bloquea_el_deficit_que_cubre_v1`), y que el déficit venza a
los dos frenos (`test_el_deficit_vence_a_la_reserva_v1`).

**Y te dejo señalado lo que encontré de paso:** `test_accept_before_expiry_safety_v2`,
`_v21` y `_simulated_safety_v1` **también** leen `get_latest_snapshot()`. Hoy pasan,
pero por cómo está el mundo, no por el código. Son tres más de la misma familia y no
las he tocado.

### b) El candidato bloqueado — **el alcance, y paro**

**Estoy de acuerdo contigo**: un candidato bloqueado tiene que verse. Es lo mismo
que hace `SOLVENCY_GUARANTEE`, que sale con `executable: false` y su motivo, y nadie
se pregunta por qué no está.

**Qué cuesta, medido:**

**Sitios que cambian: uno.**
`decision_orchestrator.py`, un tercer `elif` de ~30 líneas junto a los dos que ya
existen (el de la puerta principal, línea 2675, y el de reserva, línea 2884). Se
dispara cuando `acquisition_board.biddable > 0` pero el presupuesto está cerrado, y
copia el motivo de `acquisition_budget.blocked_by`.

**Sitios que NO cambian: dos, y es buena noticia.**
- `build_action_queue` ya filtra `executable=True`, así que un bloqueado no puede
  colarse en la cola ejecutable.
- `dashboard_state.py` ya tiene la etiqueta `"SPECULATION_BUY": "Especulación"`
  (línea 221), así que el panel lo renderiza sin tocarlo.
- `apply_backoff_to_candidates` sólo **desactiva** (`candidate["executable"] = False`,
  línea 642), nunca activa: un no-ejecutable le pasa por delante inerte.

**El riesgo, y es uno solo pero real.**
`candidates` se ordena por prioridad y **`decision = candidates[0]`**. Con la lista
del 19/09 el bloqueado (400) caería en cuarto lugar, detrás de `SOLVENCY_GUARANTEE`
(500), y el titular no cambiaría. **Pero en una vuelta tranquila —donde hoy sólo hay
`IDLE` (0)— pasaría a ser la «preocupación principal».** El panel diría
«Especulación (bloqueada)» donde hoy dice «IDLE». Eso puede ser lo que quieres o
puede ser ruido diario; es tu decisión, no mía.

**La superficie de guardias.** 70 ficheros de prueba mencionan `candidates` o
`decision`; **10 llaman a `build_global_decision`** directamente. La mayoría no
tendría `biddable > 0` con el presupuesto cerrado en su caso, así que no se
enterarían — pero no lo he comprobado una por una, y esas diez, además, leen fotos de
producción, así que su resultado depende del mundo.

**Resumen en una línea:** el cambio es pequeño y local; lo que hay que decidir es si
quieres que una puja bloqueada se convierta en el titular del panel las vueltas
tranquilas. Escrito y parado, como pediste.

---

## BLOQUE 4 — LA VUELTA MANUAL

**No he tocado nada, y te dejo las dos escritas.** Te debo la explicación porque
técnicamente una de ellas no toca el workflow.

**Opción 1 — subir `gracia_minutos` de 12 a ~25.** No toca `bordalas-live.yml`: vive
en `config/disparos.json`. Cubriría el caso de las 11:48 (19 min del latido de las
12:07).

No la he construido por dos razones. La primera: es un **umbral**, y en esta casa los
umbrales los decides tú — los dos de hoy venían con tu nombre y su número. La
segunda es medida: el `schedule` de GitHub se retiró porque llegaba **30-40 minutos
tarde**, y una gracia de 25 min deja ciega la banda de 13 a 25. Es estrechar la
única alarma que mira la realidad para tapar un aviso molesto.

**Opción 2 — un `input` en el workflow.** `workflow_dispatch` admite `inputs`, así
que cron-job.org llamaría sin él y tú con `manual: true`, y la alarma lo leería. Es
la limpia, y es la que recomiendo. Toca tu fichero:

```yaml
on:
  workflow_dispatch:
    inputs:
      manual:
        description: "Vuelta lanzada a mano"
        required: false
        default: "false"
```

Y en el job, pasarlo al ciclo como variable de entorno para que
`zona_de_silencio` pueda leerlo.

**Por qué no hay una tercera sin coste.** Lo busqué. Distinguirlas por *patrón* —una
deriva del cron es consistente y repetida, una vuelta manual es aislada— funcionaría
sin tocar nada, pero necesita el historial de vueltas, y hoy no existe: sólo se
guarda una foto al día. Montarlo significa un libro nuevo escrito por el ciclo, que
es justo el lío del que salimos ayer.

---

## LO QUE NO HICE, Y POR QUÉ

- **Ni una escritura contra Biwenger.**
- **No encendí `BORDALAS_TOPE_DEL_ONCE`**, y el motivo del encargo ya no se sostiene
  —la curva tiene peldaños por debajo del 2 %— pero **hay otro**: con el tope en
  1,2525 % Pepe puja +0,52 %, por debajo de tus dos pujas. Queda escrito arriba con
  los números.
- **No encendí `BORDALAS_COBRAR_EN_DEFICIT`** ni `BORDALAS_NO_REPETIR_LA_ESCRITURA`.
- **No subí las escrituras por vuelta.** Y ahora hay un motivo extra para no
  hacerlo: el cupo del reset no cuenta escrituras, cuenta viajes ganados, así que
  subirlo no haría lo que parece.
- **No toqué ningún umbral**: ni los de la lista, ni `gracia_minutos`.
- **No apliqué `stash@{0}`.**
- **No toqué `.github/workflows/bordalas-live.yml`.**
- **No puse el candidato bloqueado en la cola.** Alcance escrito, decisión tuya.
- **No arreglé el 93,8 % de `publicar`.** Es el peor de los tres y el freno que
  construí le vale —`filtrar_los_repetidos` no sabe de pujas, sabe de operaciones—
  pero el camino de escritura del escaparate es otro fichero y no lo pedías. Es lo
  primero que haría mañana.
- **No medí `aceptar oferta`, `reroll` ni `guardar alineación`.** No escriben libro.
  Si repiten, no me consta, y decirlo es más honesto que poner un cero.
- **No empujé nada.**

### Lo que me quedaría por delante, en orden

1. El escaparate: el mismo freno en `escaparate_executor`. 15 escrituras de 16.
2. Que el cupo del reset cuente escrituras enviadas, no viajes ganados.
3. Libro para aceptar/reroll/alineación, aunque sólo sea para poder medirlas.
4. Las tres guardias hermanas que leen producción.
