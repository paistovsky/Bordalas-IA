# INFORME — EL CANDADO Y LAS CUATRO FRASES FALSAS

Fecha: 2026-09-19 · Rama: `arreglo/el-candado-de-la-solvencia` (desde `main`, con `pull --rebase`)

---

## ANTES DE NADA: LA FOTO DEL ENCARGO NO ESTA

La foto de referencia —`generated_at` 2026-09-19T12:32:37, snapshot
`data/snapshot_20260919_122100.json`— **no existe en el repositorio**, ni en
`main` ni en ninguna rama.

- `diagnostico/` esta en `.gitignore` (linea 114). No hay historial de fotos:
  `git log -- diagnostico/status.json` da **0 revisiones**.
- El unico panel en disco es el de **18/09 16:16:38**, snapshot
  `data/snapshot_20260918_161045.json`.
- De `data/snapshot_*.json` el mas reciente es del **13/09**. No hay ninguno
  del 18 ni del 19.

Lo confirmo cruzando un dato del propio encargo: dice «ayer eran 24,56 M». El
panel en disco da `value_gap_to_leader: 24560000`. Es el de ayer.

**Consecuencia.** Todo lo que sigue sale de tres sitios que SI existen: el
codigo, los libros de `data/`, y la foto del 18/09. Donde he tenido que usar
las cifras del 19/09 las he metido como banco de pruebas fijo, y lo digo.

Y una cosa que esto rompe del encargo: el recorrido «para cada puja del
`bids_book`, mira si la foto mas cercana posterior la veia» **no se puede
hacer**. No hay fotos guardadas. Lo he medido por otra via, abajo.

---

## BLOQUE 1 — EL CANDADO

### Quien pone `SOLVENCY_RESERVED`, y con que criterio

`src/analysis/solvency_engine.py:427` — `calculate_offer_reservations`.

```python
if balance >= 0:
    return {... "reserved": [], "covered": True,
            "reason": "No hay deficit actual."}

current_debt = max(-int(balance), 0)
secured_needed = max(secured_needed, current_debt)   # <- linea 475

offers.sort(key=reservation_key)   # lo menos valioso deportivamente primero

for offer in offers:
    if reserved_total >= secured_needed:
        break
    reserved.append({**offer, "solvency_reserved": True, ...})
    reserved_total += int(offer.get("amount", 0) or 0)
```

El criterio, en una linea: **la reserva se dimensiona contra el deficit que la
motiva.** `secured_needed` nunca baja de `current_debt`, y se van reservando
ofertas —de menor a mayor valor deportivo— hasta cubrirlo.

Medido con el caso del 19/09 (deficit 455.766, las cuatro ofertas vivas):
`secured_needed = 455.766`, reserva Boyomo (1.845.800), `reserved_total`
cubre. Con las cuatro marcadas, 3.552.700 EUR reservados.

### ¿Puede levantarse la reserva para pagar el deficit que la motivo?

**Hoy no.** El candado esta en dos sitios encadenados.

`src/analysis/offer_decision_engine.py:799` — el orden importa:

```python
if reroll_action == "ACCEPT_BEFORE_EXPIRY":
    action = "ACCEPT_FOR_SOLVENCY"        # la unica puerta
elif solvency_reserved:
    action = "HOLD_SOLVENCY_RESERVED"     # el candado
```

Y quien decide `ACCEPT_BEFORE_EXPIRY`, en
`src/analysis/computer_offer_reroll_engine.py:993`:

```python
expiry_pressure   = hours_to_expiry   is not None and hours_to_expiry   <= 6.0
deadline_pressure = hours_to_deadline is not None and hours_to_deadline <= 6.0

if expiry_pressure or deadline_pressure:
    action = "ACCEPT_BEFORE_EXPIRY"
```

`ACCEPT_BEFORE_EXPIRY_HOURS = 6.0` y `ACCEPT_BEFORE_DEADLINE_HOURS = 6.0`
(lineas 35 y 43).

**Las dos puertas son relojes. El deficit no es una entrada de esa decision.**
No hay ninguna rama, en ninguno de los dos ficheros, que mire el deficit para
soltar una reserva. La reserva se calcula contra el deficit y se libera contra
el reloj: son dos magnitudes distintas, y por eso no se cierra el circulo.

Medido en la guardia: con deficit de 455.766 y sin presion de reloj, las
cuatro salen `KEEP_SOLVENCY_RESERVED`. Con el cierre a 5,5 h y **el mismo
deficit y las mismas ofertas**, las mismas salen `ACCEPT_BEFORE_EXPIRY`.

### ¿Existe el estado del que no se sale?

**Si, y es alcanzable.** Dos niveles:

**1. El bloqueo temporal (el de hoy).** Mientras `hours_to_expiry > 6` y
`hours_to_deadline > 6`, todas las fuentes de cobertura reservadas quedan
retenidas. Se abre sola cuando el reloj baja de 6 h. No es permanente: es un
retraso de hasta `expiry - 6 h`.

**2. El bloqueo permanente.** Las dos condiciones llevan `is not None`. Si la
oferta **no trae `expires_at` ni `until` legibles** y `hours_to_deadline` es
`None`, las dos presiones son `False` para siempre y el candado no se abre
nunca, por grande que sea el deficit y por mucho que espere.

Medido, tres escenarios, con las cuatro ofertas reservadas y 455.766 de
deficit:

| caducidad | cierre | ¿alguna aceptable? |
|---|---|---|
| lejana (2100) | 480 h | **No** |
| AUSENTE | AUSENTE | **No** |
| ILEGIBLE | AUSENTE | **No** |

Con esos numeros se llega. No hace falta nada raro: basta una oferta sin fecha
de caducidad legible fuera de jornada.

> Una salvedad honesta: `ACCEPT_BEFORE_EXPIRY` es una **decision**, no una
> ejecucion. Si el executor la lleva a cabo es un camino que no he medido —
> el encargo prohibia escribir. Que aceptaras la de Boyomo a mano sugiere que
> el camino de ejecucion tampoco cierra, pero eso no lo he comprobado y no lo
> afirmo.

### ¿El motor de ofertas y los planes de solvencia son dos cabezas distintas?

**Si.** Buscados por nombre, `A_NO_XI`, `B1` y `C` **no aparecen en ningun
sitio del codigo**. Los planes que ves calculados no los conoce
`offer_decision_engine`: su decision se construye con `quality`,
`sale_is_worth_it`, `in_lineup`, `reroll_action` y `solvency_reserved`. Ni uno
de esos cinco es un plan de cobertura.

Y hay un segundo candado, distinto del primero, que el encargo mezcla:

| oferta | accion | quien la bloquea |
|---|---|---|
| Barzic, Oriol Rey | `HOLD_SOLVENCY_RESERVED` | la reserva |
| Boyomo, Pablo Duran | `KEEP_GOOD_OFFER` | `quality in {GOOD, EXCELLENT}` |

`KEEP_GOOD_OFFER` (linea 967) es la rama por defecto de una oferta favorable:
«se conserva sin vender automaticamente». No tiene nada que ver con la
solvencia. Son **dos frenos independientes**, y levantar la reserva no
desbloquea a Boyomo ni a Pablo Duran.

### DOCTRINA 87 — corrijo el diagnostico del encargo

El encargo dice: «dos modulos leen `CUBIERTO` y uno concluye tranquilo y el
otro no pujes; uno de los dos esta leyendo mal el dato». **No es eso.**

`src/analysis/la_subasta.py:1263`:

```python
SOLVENCIA_QUE_DEJA_PUJAR = frozenset({"SIN_DEUDA", "CUBIERTO"})
```

`CUBIERTO` **esta en la lista de los que dejan pujar**. Lo que bloquea es el
segundo termino (linea 1359):

```python
if estado not in SOLVENCIA_QUE_DEJA_PUJAR or deficit > 0:
```

Fue `deficit > 0`. Los dos modulos **no leen el mismo dato**: el reloj narra
con `state`, la subasta decide con `deficit`. No se contradicen.

El fallo es otro, y es de redaccion: el mensaje imprime el **estado**, que es
justo el campo que lo dejaba pasar.

> «El reloj de solvencia dice «CUBIERTO» con 455.766 EUR de deficit. No se
> puja.»

Nombra como culpable al que absolvio. Por eso parecia una contradiccion. Es
una linea de texto, y arreglarla es barato:

```python
f"Hay {_euros(deficit)} EUR de deficit. No se puja: el viernes
  hay que estar en positivo. (El estado del reloj es «{estado}».)"
```

---

## BLOQUE 2 — PUJAR NO COMPITE

### ¿Se filtra antes de entrar en la cola, o no se genera?

**No se genera.** Y son dos sitios distintos, asi que la respuesta cambia
donde hay que tocar.

`src/analysis/decision_orchestrator.py:2675` — todo el bloque que produce el
candidato de compra cuelga de una sola puerta:

```python
if (speculation_phase_allowed
    and ((budget.get("enabled") and hay_lista_de_especulacion)
         or (acquisition_budget.get("enabled") and hay_objetivo_de_fichaje))
    and not hard_safety_mode):
```

- `hay_objetivo_de_fichaje = (acquisition_board.biddable or 0) > 0` → **se
  cumple** (biddable 1).
- `acquisition_budget.enabled` → **no se cumple**. Medido con el saldo del
  19/09: `enabled=False`, `blocked_by=SIN_CAPACIDAD`, `total_budget=0`.

Dentro de ese bloque hay **dos** salidas y las dos anaden algo:
`SPECULATION_BUY` si hay objetivo (linea 2810) y `SPECULATION_WATCH` si no lo
hay (linea 2779). Como la puerta no se abre, no se ejecuta **ninguna de las
dos**. Por eso no aparece ni siquiera bloqueado con su motivo, como si
aparece `SOLVENCY_GUARANTEE`.

El escalon existe: `PRIORITY["SPECULATION_BUY"] = 400`, y el comentario de al
lado dice lo que toca — «El mercado Computer se resetea una vez al dia: la
puja que no se hace hoy se pierde para siempre».

**Ademas, un matiz sobre la lista que viste.** `build_action_queue` (linea
549) se queda **solo con `executable=True`**. La lista de cinco entradas con
tres «no» es la de **CANDIDATOS**, no la cola. Un candidato de puja bloqueado
si se veria ahi con su motivo. No esta porque no se genero.

### `SOLVENCY_GUARANTEE` = `GARANTIZADA` con deficit vivo

`src/analysis/solvency_engine.py:534`:

```python
covered = bool(reserved_total + expected_credit >= required_recovery)

debt_covered_by_secured = bool(reserved_total >= current_debt)
```

`covered` —de donde sale la etiqueta— es **condicional**: «si se aceptaran las
ofertas reservadas, mas la liquidez esperada, se taparia». Y tienes razon en
lo que dices: **eso no va a pasar solo**, porque es exactamente lo que el
bloque 1 demuestra que el motor no hace.

El propio fichero ya distingue las dos cosas y publica `debt_covered_by_secured`
aparte, con este comentario: «La deuda real solo esta cubierta si hay dinero
REAL reservado para taparla, no liquidez esperada». El campo honesto existe.
La etiqueta de pantalla usa el otro.

---

## BLOQUE 3 — LAS TRES VIAS: LA MEDICION CONTRADICE EL ENCARGO

**Dos de las tres vieron la puja.** La foto del 18/09 16:16:38 esta en disco y
dice, literalmente:

```
TABLON      -> 1.664.350   "El tablon publica 1 puja(s) nuestras por 1.664.350 EUR."
RESTA       -> 1.664.350   mismatch 0
DIFERENCIA  -> 0           "maximumBid no ha bajado"
committed   -> 1.664.350   source TABLON
disagreement-> 1.664.350
```

Y coherente en todo el panel: `solvency_clock.committed_bids: 1664350`,
`consistency.checks[live_bids_shown]` esperado 1 / encontrado 1 → **ok**,
`live_bid_amount_shown` esperado 1.664.350 / encontrado 1.664.350 → **ok**.

No hay ningun bloque de esa foto que diga «pujas vivas 0 · comprometido 0 €».
La unica frase del encargo que aparece tal cual es la de `DIFERENCIA`.

Las otras dos citas —`TABLON -> 0` con «El tablon no publica ninguna puja
nuestra»— son el texto del **caso vacio** de `por_el_tablon`. Existe en el
codigo, pero no se disparo en esta foto.

### Por que `RESTA` dio 0 → **no dio 0, dio el numero exacto**

```
4.324.615 (saldo) + 13.210.000 (margen) − 15.870.265 (maximumBid) = 1.664.350
```

con `credito.roster_value = 52.840.000`, `ratio = 0.25`, fuente
`LINEA_MEDIDA`. `mismatch: 0`.

### ¿`maximumBid` descuenta las pujas vivas? → **SI**

Queda probado al euro por la propia resta: si `maximumBid` **no** descontara
la puja, la resta habria dado 0 y `mismatch` habria salido −1.664.350. Dio
exactamente el importe comprometido.

El panel lo afirmaba («maximumBid, que ya descuenta las pujas vivas») y es
**cierto**. La preocupacion del encargo —«toda la capacidad de compra esta mal
contada»— no se sostiene: esta bien contada.

### Entonces, ¿por que `DIFERENCIA` dijo 0?

Porque **mide otra cosa**. `por_la_diferencia` compara dos fotos y devuelve la
**bajada** de `maximumBid` entre ellas:

```python
bajada = tope_antes - tope_ahora
if bajada <= 0:
    return {"committed": 0, "delta": bajada,
            "reason": "Entre las dos fotos maximumBid no ha bajado:
                       nadie ha comprometido nada NUEVO."}
```

La puja se puso a las 12:16. A las 16:16 ya estaba en las **dos** fotos que se
comparan, asi que no hubo bajada y el incremento es cero. **Es correcto.**

**El fallo no es el cero: es publicarlo junto a dos niveles como si midiera lo
mismo.** Un incremento y un nivel no son la misma magnitud (doctrina 54), y
mezclarlos es lo que produce el `disagreement: 1.664.350` de esa foto — una
discrepancia que no existe.

Y la regla de desempate salva la cara: «manda la mas conservadora». Por eso el
panel publico 1.664.350 y no 0. El sistema acerto **a pesar** de la via C.

### Cuantas veces ha pasado, con su `n`

Como no hay fotos guardadas, lo he medido sobre `bid_outcome_ledger.json`
(47 entradas, todas con `placed_at` y `resolved_at`), contando cuantas vueltas
horarias estuvo viva cada puja. La via C solo ve la bajada en la **primera**
foto posterior; en todas las demas devuelve 0.

| | fotos horarias con puja viva | de esas, `DIFERENCIA = 0` | % |
|---|---|---|---|
| entradas del libro tal cual (n=47) | 356 | 319 | 89,6 % |
| **deduplicado por `event_id` (n=9)** | **104** | **95** | **91,3 %** |

El `n` bueno es el segundo, y aqui aparece un hallazgo que no estaba en el
encargo.

### El libro de pujas cuenta la misma puja muchas veces

De las 47 entradas, solo **9 `event_id` distintos** (y 14 entradas sin
`event_id`). La clave del libro es `player_id:placed_at`, asi que **cada vuelta
horaria crea una entrada nueva de la misma puja**:

```
10030:2026-09-18T05:23:13   Maffeo 1.664.350  event 3d15660bd0c3d1e7813beaab
10030:2026-09-18T07:14:46   Maffeo 1.664.350  event 3d15660bd0c3d1e7813beaab
10030:2026-09-18T08:14:54   Maffeo 1.664.350  event 3d15660bd0c3d1e7813beaab
...  (x10, mismo event_id, mismo importe, mismo resolved_at)
```

| jugador | entradas | `event_id` |
|---|---|---|
| Maffeo | 10 | `3d15660b…` |
| Boyomo | 9 | `da7823c4…` |
| Oriol Rey | 5 | `b4e25b7e…` |
| Fortuño, Larrubia, Álvaro Carreras | 2 c/u | — |

**Es la misma familia que la reja del bloque 5**: la fecha dentro de la clave,
y la misma operacion contada muchas veces. Aqui no descuadra la caja, pero
inflaba mi propio `n` en un factor de 3,4.

### La puja del dueno no se puede confundir con la del motor — casi

`src/intelligence/bid_outcome_ledger.py:391` — `_origen_probado`:

```python
if int(fila.get("player_id")) == int(player_id) and \
   int(fila.get("amount")) == int(amount):
    return str(fila.get("marca") or ORIGEN_SIN_PROBAR)
return ORIGEN_SIN_PROBAR
```

El criterio es solo **(player_id, amount)**. No mira el tiempo.

Lo que funciona bien: Cabrera (3.116.031) no esta en
`libro_del_carril.jsonl`, asi que salio `DESCONOCIDO`. Correcto, y no lo he
tocado. Reparto medido: `DESCONOCIDO` 16, `RENDIJA` 16, `SUBASTA_CARTERA` 13,
`ACQUISITION_BOARD` 2.

Lo que puede fallar: el libro del carril **si lleva** `at` con la hora exacta,
y `_origen_probado` **no lo usa**. Si algun dia pujas a mano por un jugador
por el que el carril pujo antes **el mismo importe exacto**, esa puja tuya se
marcaria `RENDIJA`. Hoy no ha pasado. El arreglo es de una linea: exigir que
el `at` del carril caiga en una ventana alrededor del `placed_at`.

---

## BLOQUE 4 — LAS CUATRO FRASES

### (a) Trent — y las DOS frases estan mal, no una

`src/actions/escaparate_executor.py:561` — `viajes_sin_listar` cruza los
viajes contra **`listados`** y **nunca contra la plantilla**:

```python
en_venta = {safe_int(x.get("player_id")) for x in (listados or [])}
huerfanos = [... for v in (viajes or [])
             if safe_int(v.get("player_id")) not in en_venta]
```

Un viaje de un jugador que ya **no es nuestro** sale como «comprado y sin
publicar» para siempre, porque efectivamente no esta listado.

Y la fecha no esta inventada. `data/trading/libro_de_viajes.jsonl`:

```json
{"at": "2026-09-13T08:08:32", "player_id": 37499, "name": "Trent",
 "via": "RENDIJA", "state": "ABIERTO"}
```

08:08 UTC = 10:08 Madrid. Es el `opened_at` del viaje, que nunca se cerro.

**Lo que paso de verdad**, trazado en el tablon:

| cuando | que |
|---|---|
| 12/09 14:45 | puja 2.760.000, via RENDIJA |
| 13/09 05:06 | **GANADA** — tablon: `37499 → Pepe Bordalás, 2.760.000` |
| 13/09 08:08 | se abre el viaje, `ABIERTO` |
| **17/09 22:12** | **VENDIDO** — tablon: `37499 from Pepe Bordalás, 2.536.500` |

Asi que la otra frase, la que el encargo daba por buena, tambien miente:

> «Trent no esta en la plantilla: **la puja no se ha resuelto a nuestro
> favor**.»

La puja **si** se resolvio a nuestro favor. Lo compramos y lo vendimos cuatro
dias despues. Acierta la conclusion y falla el motivo.

**El arreglo:** filtrar `viajes` por pertenencia a la plantilla, y cerrar el
viaje cuando el jugador sale del roster.

### (b) «Tu plantilla vale lo mismo que la del lider»

`src/analysis/race_state.py:509`:

```python
"value_gap_to_leader": (valor_lider - nuestro_valor
                        if valor_lider and nuestro_valor else None),
```

Siendo lideres, `lider` somos nosotros → la resta da 0 → linea 310:
`". Tu plantilla vale lo mismo que la del lider."`

Lo mas sangrante: la **cabeza de la misma frase** ya usa `is_leader`
(linea 264) para decir «Vas 1º». El dato esta a dos lineas y la cola no lo
mira.

Reproducido en la guardia con los numeros del 19/09:

> «Vas 1º, con 6 de ventaja, quedan 31 jornadas: necesitas sacarle 0,00 por
> jornada. Tu plantilla vale lo mismo que la del lider.»

El arreglo, con tus palabras: **cuando somos lideres, la comparacion util es
contra el segundo**. El dato esta disponible — `race.managers` trae los 8 con
`rank` y `team_value`.

> Un aviso al hacerlo: el segundo **por puntos** no es el segundo por dinero.
> En la foto del 18/09 el mas rico era Luismi_Haz (94,35 M), tercero. Si la
> frase va a hablar de dinero, di contra quien.

### (c) Dos fichas o ocho

`src/analysis/deployment.py:364`. La palabra **«ocho» esta escrita a mano**:

```python
"priority_reason": (
    "Con ocho fichas vacias, llenar una vale mas que una "
    "especulacion: el dinero parado no se revaloriza..."
```

`signing_priority(operation, *, as_xi, price_increment)` **no recibe**
`free_roster_slots`. No es que lo lea mal: no puede saberlo. Dira «ocho»
siempre, con 2 fichas libres o con 17.

Arreglo: pasarle el recuento y formatearlo.

### (d) «El ciclo no ha entrado a su hora»

Aqui tambien corrijo el encargo: **el cron horario SI esta declarado.**

`config/disparos.json`:

```json
"latido": { "minuto": 7, "horas": [0,1,2,3,8,...,23],
            "cron": "7 0-3,8-23 * * *", "cadencia_minutos": 60 }
```

De ahi sale el 12:07. Y `que_disparo_toca` (`los_disparos.py:243`) **si mete
el latido entre los candidatos**. La foto del 18/09 lo confirma:

```
silencio.declared_reason:
  "El disparo declarado mas cercano es el de las 16:07 (latido), a 9 min,
   dentro de la gracia de 12."
```

El que se deja el latido fuera es **la pantalla**.
`dashboard-v8/src/lib/relojes.js:78`:

```javascript
export const DISPAROS_ESPERADOS = DISPAROS.puntuales;   // <- solo los tres
```

y en la linea 545 se publica tal cual como `configurados:`. Por eso el aviso
imprime 04:45 · 04:50 · 07:15 y no el 12:07 que el mismo aviso acaba de
nombrar. **Arreglo de una linea, y no toca el workflow.**

**La segunda parte no se puede hacer como la pides.** `config/disparos.json`
dice `"como_entra": "workflow_dispatch"`, y `zona_de_silencio.py:138` lo
explica: desde que se retiro el `schedule` de GitHub, **todas** las vueltas
entran como `workflow_dispatch` — las de cron-job.org y las tuyas a mano. No
existe ninguna senal que las separe.

Lo unico que las distingue es la hora contra la declaracion, y eso es
exactamente lo que ya hace. La vuelta de las 11:48 esta a 19 min del 12:07,
fuera de la gracia de 12 → salta. **Funciona como esta disenado.**

Si quieres que una vuelta manual no chille, las opciones reales son: subir
`gracia_minutos`, o meter una marca explicita (un `input` en el dispatch) que
diga «esta la he lanzado yo». La segunda toca el workflow, que es tuyo.

---

## BLOQUE 5 — LA REJA

### ¿El hueco de 420.200 es el duplicado de Lunin? — **SI, al euro**

Trazado movimiento por movimiento en `board_events.json`:

| evento | `event_id` | cuando | contenido |
|---|---|---|---|
| `market` | `5444297c…` | 17/09 05:08 | `player 15289 → Pepe Bordalás, 421.000` (compra) |
| `transfer` | `f45d6211…` | **18/09 06:53:34** | `player 15289 from Pepe Bordalás, 420.200` |
| `transfer` | `62a54356…` | **18/09 07:03:10** | `player 15289 from Pepe Bordalás, 420.200` **+ player 41418** |

Las dos emisiones llevan **el mismo payload** para Lunin y **distinto
`event_id` y distinto `date`**. Y la segunda es un **lote que crece**: reemite
a Lunin y anade una operacion nueva. Es exactamente el patron que describe el
commit `17fd828`.

```
separacion: 576 s = 9m 36s
ventana de la reja: 3.600 s  -> la cubre, con 6,25x de margen
```

Y la aritmetica cierra:

```
caja reconstruida (−35.566) − caja real (−455.766) = +420.200
```

La venta de 420.200 se cuenta **dos veces** como ingreso, asi que la caja
reconstruida sale 420.200 **por encima** de la real. Coincide al euro y en
signo.

> Un dato para la proxima: 9m36s es **mayor** que el «tramo maximo 9m12s»
> (n=5) que anoto el commit de la reja. La poblacion de reemisiones ahora
> llega a 576 s. Sigue 6,25 veces por debajo de la ventana, asi que no cambia
> nada — pero el maximo medido ya no es el que dice el comentario.

### Tabla antes/despues, con la reja encendida

`reconstruir()` sobre los 649 eventos del tablon, con el interruptor en los
dos lados:

| manager | reja APAGADA | reja ENCENDIDA | diferencia |
|---|---:|---:|---:|
| 14456960 | 15.525.200 | 15.525.200 | 0 |
| 14156489 Luismi_Haz | 8.572.191 | −4.773.209 | **−13.345.400** |
| 14154203 Prinzipote | 5.848.172 | 3.634.772 | **−2.213.400** |
| 14178736 | 5.520.800 | 5.520.800 | 0 |
| 14151726 | 2.867.183 | 2.867.183 | 0 |
| 14176382 | 266.741 | 266.741 | 0 |
| **14175949 Pepe Bordalás** | **−35.566** | **−455.766** | **−420.200** |
| 14145555 Pollo17 | −7.508.035 | −7.508.035 | 0 |

**Con la reja encendida nuestra caja reconstruida da −455.766, que es
exactamente la caja real.** Cuadra.

Cinco de los ocho no se mueven un euro. Prinzipote da el mismo par que anoto
el commit (5.848.172 → 3.634.772) y Luismi el mismo delta (13.345.400).

### Lo que NO he hecho: encenderla

La hipotesis se sostiene, asi que tocaba encender. **No he podido, y las dos
vias estan cerradas por el propio encargo:**

1. **El codigo de la reja no esta en `main`.** `git merge-base --is-ancestor
   17fd828 main` → **NO**. Toda la rama `arreglo/la-reja-y-el-suelo` (4
   commits) esta sin mergear. En una rama salida de `main`,
   `BORDALAS_REJA_CON_TOLERANCIA` **no existe**: `grep` da 0 en
   `src/analysis/caja_de_la_liga.py`. (La tabla de arriba la he sacado
   ejecutando la version de la rama, en solo lectura, fuera del arbol.)

2. **Encenderla en produccion es una variable de entorno del workflow**, y
   `.github/workflows/bordalas-live.yml` es tuyo y esta fuera de limites.

Asi que lo que hace falta, en orden, y lo decides tu:

```
1. git merge arreglo/la-reja-y-el-suelo   (un paso, un comando)
2. git push
3. anadir al workflow:  BORDALAS_REJA_CON_TOLERANCIA: "1"
```

### La guardia que pedias ya existe

**Doctrina 84.** `test_la_reja_no_cuenta_dos_veces_el_mismo_movimiento` es
`src/analysis/test_la_reja_no_se_come_dos_operaciones_reales_v1.py`, en la
rama de la reja, y cubre justo lo que pides:

- reemision con otro `event_id` dentro de la ventana → no suma dos veces;
- repeticion legitima a 5 dias → si cuenta dos (linea 249-257);
- muerde con la lista de eventos vacia (linea 141-153);
- y con el interruptor en los dos lados.

No he escrito una segunda.

---

## LAS GUARDIAS

Commit `f9da78e`. Cuatro ficheros, 1.259 lineas. **Tres salen en rojo a
proposito**: son los fallos convertidos en comprobacion, y se ponen verdes el
dia que decidas la politica — no antes.

| guardia | estado | que fija |
|---|---|---|
| `test_la_reserva_no_bloquea_el_deficit_que_cubre_v1` | **3 de 4 verde** | secciones 0-3 verdes (la reserva se dimensiona contra el deficit; sin reloj no se suelta; con reloj si). **Seccion 4 roja: el candado.** |
| `test_un_candidato_pujable_llega_a_la_cola_v1` | **3 de 4 verde** | el escalon existe; el presupuesto se apaga con deficit; la cola descarta no-ejecutables. **Seccion 4 roja: no se genera candidato.** |
| `test_una_puja_viva_se_ve_por_alguna_via_v1` | **VERDE** | `maximumBid` descuenta pujas vivas, al euro; dos de tres vias ven la puja; la via C mide incrementos |
| `test_el_panel_no_afirma_lo_que_el_json_desmiente_v1` | **4 rojas** | las tres frases, reproducidas con entradas fijas |

Las cuatro empiezan por una **seccion 0** que muerde con el banco vacio: sin
ofertas, sin candidato pujable, sin puja en el tablon o sin plantilla, el
resto pasaria por vacuidad.

Ninguna lee estado de produccion, sale a la red, mira el reloj del sistema ni
escribe en los libros. Las caducidades son fechas fijas lejanas (ano 2100) y
la presion de cierre entra por parametro.

---

## LO QUE NO HICE, Y POR QUE

- **Ni una escritura contra Biwenger.** Ni pujas, ni ofertas, ni ventas, ni
  renovaciones.
- **No toque la politica de pujar en deficit.** Medida y ensenada; la decides
  tu.
- **No subi ningun umbral.** Ni uno.
- **No toque `bordalas-live.yml`.** Para el 4d digo que cambiar, no lo cambio
  — y resulta que el arreglo principal del 4d ni siquiera esta ahi, esta en
  `relojes.js`.
- **No encendi la reja.** Las dos vias estan cerradas (arriba). El codigo no
  esta en `main` y el interruptor vive en el workflow.
- **No escribi la quinta guardia.** Ya existe (doctrina 84).
- **No rellene ningun hueco ni estime ningun precio.**
- **No pude recorrer las fotos** para el `n` del bloque 3: `diagnostico/` esta
  en `.gitignore` y no hay ni una guardada. Lo medi sobre el libro de pujas y
  digo por que via.

### Dos cosas que te dejo pendientes

**El stash.** Para ramear desde `main` limpio guarde los libros que el ciclo
habia escrito hoy (`libro_en_la_sombra.jsonl`, `marcador.json`,
`board_events.json`, `bitacora_del_saldo.jsonl`). Estan en
`stash@{0}` («encargo-candado: libros del ciclo 19-09 antes de ramear»). No
los he devuelto porque `main` ha avanzado 26 commits desde entonces y
mezclarlos a ciegas es justo lo que no toca. Recuperables cuando quieras.

**Tres afirmaciones del encargo que la medicion tumba**, por si alguna
cambiaba una decision:

1. Las tres vias **no** dieron cero: dos de tres vieron la puja, y
   `maximumBid` **si** descuenta las pujas vivas.
2. `CUBIERTO` **si** deja pujar. Lo que bloqueo fue `deficit > 0`. Los dos
   modulos no leen el mismo dato.
3. El cron horario **si** esta entre los configurados, en
   `config/disparos.json` y en `que_disparo_toca`. El que lo omite es
   `relojes.js`.

Y una que se sostiene entera, al euro: el hueco de 420.200 **es** el duplicado
de Lunin.
