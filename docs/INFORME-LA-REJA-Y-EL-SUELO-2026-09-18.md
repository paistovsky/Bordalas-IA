# INFORME — LA REJA Y EL SUELO

**Fecha:** 2026-09-18
**Rama:** `arreglo/la-reja-y-el-suelo` (tres commits, **sin empujar**)
**Foto:** `diagnostico/status.json`, `meta.generated_at = 2026-09-18T16:16:38`
(snapshot `data/snapshot_20260918_161045.json`)

> **Una nota sobre la rama.** El encargo decía «desde `main`», pero la rama ya
> existía apuntando al trabajo de ayer, y la he dejado así: contiene `main` más los
> tres commits del portero y la caja. Partir de `main` pelado habría tirado el
> arreglo del once y el buscador de sospechosos, que son justo sobre lo que se
> apoyan los bloques 2 y 3. Si querías lo contrario, se rehace en un minuto.

---

## BLOQUE 1 — LA REJA

### 1. Por qué llevaba la fecha dentro, y qué colgaba de ella

**No fue un descuido: fue un arreglo, y de los buenos.**

La puso el commit `bf5f596` del 10/09, *«la caja es inmune al tablón repetido»*, que
curó un descuadre de **2.860.000 €** (la J2 y la J3 pagadas dos veces). La clave

```
(tipo, FECHA, jugador, de, a, importe)
```

era la «identidad lógica» de una operación, y **funcionó ocho días** porque la
reemisión que se vio entonces cambiaba el *payload* y **conservaba el `date`**: una
puja más en `bids`, unos puntos corregidos tras un aplazamiento. Con la fecha igual,
las dos copias colapsaban.

Lo que no se había visto es la reemisión que además mueve la fecha. Y mirando el
tablón crudo, **no son reemisiones sueltas: es un lote que crece**:

```
04-09 16:29:16   transfer con 1 operación
04-09 16:34:01   transfer con 2   (la primera otra vez, y una nueva)
04-09 16:38:28   transfer con 7   (las dos anteriores, y cinco más)
```

Tres `event_id` distintos, tres fechas distintas, y la operación del jugador 31069
contada **tres veces**.

### Qué cuelga de la fecha (doctrina 69)

**La fecha está trabajando, y por eso no se quita.** Es lo único que separa dos
operaciones **legítimas** que por lo demás son idénticas: mismo jugador, mismo
importe, mismas partes.

Sin ella, comprar a un jugador por 150.376 € en el reset de hoy y volver a comprarlo
por lo mismo dentro de dos semanas se fundiría en un solo pago, y **la caja saldría de
más** — el fallo contrario, y peor, porque nadie lo estaría buscando.

Así que la fecha no se quita: **se le pone tolerancia.**

### 2. ¿Pueden fundirse dos operaciones reales? Medido

Sobre el tablón del repo, **n = 627 eventos, 09/08–18/09**, en 387 grupos de
`(tipo, jugador, de, a, importe)`:

| población | n | medida |
|---|---:|---|
| **reemisiones del tablón** | 5 | tramo máximo **9m12s** |
| **repeticiones legítimas** (mismas partes, otro importe) | 7 | separación mínima **5 días** |

**Un factor de 783 entre las dos.** Y algo más rotundo: **cero** repeticiones con el
**mismo importe** separadas por más de una hora, en 40 días.

Las 7 legítimas son reales y esperables — el mismo mánager compra al mismo jugador dos
veces —, y **en las 7 el importe es distinto**, porque el precio de Biwenger se mueve
cada día.

### Y no es solo estadística

**El mercado resuelve una vez al día.** Los **42 eventos `market` de 39 días caen
todos en la hora 05:00**, y ningún día tiene dos horas de mercado. Así que dos compras
idénticas del mismo jugador por el mismo mánager **no pueden estar a menos de ~24 h**
— veinticuatro veces la ventana. Y vender dos veces al mismo jugador exige recomprarlo
por medio, que también pasa por un reset.

**La ventana son 3.600 s:** 6,5× por encima de la mayor reemisión medida, 120× por
debajo de la repetición legítima más cercana, y 24× por debajo del ciclo del mercado.

### 3. La tabla de caja, los ocho

n = 627 eventos, 09/08–18/09. Fuente: `data/rival_intelligence/board_events.json`.

| mánager | caja vieja | caja nueva | diferencia |
|---|---:|---:|---:|
| Luismi_Haz | −1.720.709 | **−15.066.109** | 13.345.400 |
| Prinzipote | 5.848.172 | 3.634.772 | 2.213.400 |
| Pollo17 | 6.524.165 | 6.524.165 | 0 |
| **Pepe Bordalás** | 4.324.615 | 4.324.615 | 0 |
| Manzagool | 266.741 | 266.741 | 0 |
| DiosMande a Rodri al Palancas | 2.867.183 | 2.867.183 | 0 |
| Mex | 5.520.800 | 5.520.800 | 0 |
| Alvaro Retamosa Sanguino | 15.525.200 | 15.525.200 | 0 |
| | | **total retirado** | **15.558.800** |

**Toda la sobrecuenta estaba en dos mánagers.** Los otros seis no se mueven un euro.

**Por qué nuestra fila sale a cero:** el tablón del repo tiene la venta de Lunin **una
sola vez**. El duplicado está en el tablón de producción, que lee 640 eventos. Lo
reproduje inyectándolo:

```
tablón del repo       · reja vieja   4.324.615   dif  +0
tablón del repo       · reja nueva   4.324.615   dif  +0
+ duplicado de Lunin  · reja vieja   4.744.815   dif  +420.200   <- lo que publica producción
+ duplicado de Lunin  · reja nueva   4.324.615   dif  +0         <- arreglado
```

La reja vieja sobre el tablón sucio da **4.744.815 clavados**, que es lo que publica el
panel. El diagnóstico de ayer era correcto y el arreglo lo cierra.

### 4. Qué se mueve de verdad: `MAX_VISTO`, `AMENAZA` y el tope

| mánager | TOPE viejo | TOPE nuevo | AMENAZA | MAX_VISTO |
|---|---:|---:|---|---:|
| Luismi_Haz | 21.866.791 | **8.521.391** | 79,9 → 65,6 | 17.056.000 |
| Prinzipote | 19.130.672 | 16.917.272 | 31,8 → 32,8 | 25.440.000 |
| Pollo17 | 26.284.165 | 26.284.165 | 88,2 → 88,2 | 17.540.007 |
| Pepe Bordalás | 17.534.615 | 17.534.615 | (nosotros) | 24.897.600 |
| Manzagool | 13.806.741 | 13.806.741 | 35,1 → 41,7 **LOW→MEDIUM** | 13.170.000 |
| DiosMande… | 14.727.183 | 14.727.183 | 34,1 → 40,3 **LOW→MEDIUM** | 22.230.000 |
| Mex | 18.278.300 | 18.278.300 | 39,7 → 44,0 **LOW→MEDIUM** | 23.310.000 |
| Alvaro Retamosa | 24.727.700 | 24.727.700 | 19,5 → 20,3 **VERY_LOW→LOW** | 5.670.000 |

- **`MAX_VISTO` no cambia para nadie.** Sale de pujas observadas
  (`max_lost_bid`/`max_winning_bid`), no de la caja.
- **El tope sí:** `balance + 0,25 × valor_plantilla`. El de Luismi cae **13,3 M**.
- **La AMENAZA se mueve en los ocho**, incluso en los que no cambian de caja, porque
  es *relativa* dentro de la liga: al bajar dos, suben los demás. Cuatro cambian de
  nivel.

### ¿Qué habríamos pujado distinto en 30 días?

**Nada. Cero de 27.**

`bid_outcome_ledger.json`, **n = 27 pujas, 10/08 → 17/09** (los 30 días completos).
**Ninguna lleva `seller_user_id`**: las 27 fueron al mercado o al Computer, y ni una
fue una compra a un rival.

Y la vía por la que la caja de un rival entra en un precio es justo esa:

```
rival.balance -> calculate_liquidity_help_score
              -> calculate_strategic_max_purchase_price
              -> lo que pagaríamos por comprarle un jugador a un rival
```

Además, **ningún mánager cruza `DIRECT_RIVAL_THREAT_THRESHOLD` (60)**: Luismi baja de
79,9 a 65,6 y sigue arriba; el resto sigue abajo. La clasificación de «rival directo»
no cambia para ninguno de los siete.

### Mi lectura, y la decisión es tuya

**No es solo pantalla, pero tampoco ha movido una sola puja.**

- A favor de encenderlo: **mientras está apagado, nuestra caja sigue 420.200 € alta y
  `cash_check` sigue en rojo.** Ese es el número contra el que se audita todo lo demás.
- A favor de esperar: mueve 13,3 M en la caja de un rival, y eso entra en una función
  de precio viva. «No ha disparado en 30 días» no es «no dispara».

**Lo he dejado detrás de interruptor, apagado**, como pedías:

```
BORDALAS_REJA_CON_TOLERANCIA=1
```

**Apagado reproduce producción al detalle:** 30 repetidos colapsados, 7 jornadas
vistas, 6 pagadas. Comprobado contra la foto.

**`sospechosos()` no depende del interruptor:** apagado, la pantalla sigue diciendo qué
evento descuadra la caja. Diagnosticar no es corregir.

**Mi recomendación: enciéndelo.** El coste medido de tenerlo apagado (nuestra caja
torcida, que es la única auditable) es concreto y diario; el riesgo de encenderlo
(precios de compra a rivales) no se ha materializado ni una vez en 30 días y además
esa vía está cerrada. Pero es tu decisión y el interruptor está puesto.

---

## BLOQUE 2 — EL SUELO

### 1. Ahora sale de su banda, no de una constante

Doctrina 85 nos mordió **dos veces en dos días**. El 0,25 original era un duplicado
silencioso del peldaño más bajo de la escalera. **Y el arreglo de ayer puso
`SIN_PRONOSTICO_SCORE = -500_000.0`, que era exactamente la misma clase de número:**
uno que vale mientras otra cosa no se mueva, y que no se entera cuando se mueve.

Ahora los pesos del score tienen nombre — estaban escritos a pelo dentro de
`prepare_players` — y el suelo se deriva:

```
peor_con_pronostico()  = 0×ESCALA + 1×COBERTURA + 0×PROBABILIDAD + AVISO = 2.500
suelo_sin_pronostico() = (2.500 + (−1.000.000)) / 2                      = −498.750
```

El punto medio de la banda: **501.250 € de margen a cada lado**, que es lo máximo
posible, y se mueve solo si cualquiera de los dos extremos se mueve.

El valor casi no cambia (estaba en −500.000). **Lo que cambia es que ya no hay que
acordarse de él.**

### La guardia, que es lo que pediste

`test_el_suelo_sigue_a_su_escalera_v1` **mueve cada peso y exige que el suelo se
entere**. Comprobado que muerde: con un `return -498_750.0` escrito a mano —con el
mismo valor de hoy— salen **3 fallos**.

Además barre la escalera entera (todos los peldaños × todas las probabilidades) y
exige que ningún score con dato baje del suelo, y comprueba que las dos escaleras
tienen los mismos peldaños y que el escalón «no se sabe» existe en las dos (si
desapareciera de una, `weekly_expected_value` revienta con `KeyError` en producción).

### 2. La regla del dueño

Sigue en pie y con su guardia: `test_sin_pronostico_v1`, que reproduce al euro los tres
scores de la foto y muerde con el tablero vacío, con el suelo viejo y con la calidad
medida apagada.

### 3. Y la cola de venta se da la vuelta

Comprobado, y está fijado en la guardia (sección 6):

| | antes | después |
|---|---|---|
| **Dituro** | 2.º de la cola de venta, *«no juega»* | **fuera de la cola**, apartado: *«portero titular»* |
| **Esquivel** | el **único** apartado, *«sin escalón»* | sigue apartado, pero por *«sin escalón»*, no por titular |

El mecanismo: `untouchable_reason` protege al portero **titular** vía
`is_starter`. Al volver Dituro al once, la protección le sigue. Y Esquivel sigue sin
venderse, que está bien: no se vende a ciegas a quien no se puede valorar.

---

## BLOQUE 3 — LOS TRES CAMPOS, PUBLICADOS

| campo | dónde sale ahora |
|---|---|
| `validation` | `rival_intelligence.validation` |
| `unknown_types` | `rival_intelligence.unknown_types` |
| `unmatched` | `lineup.starter_unmatched` (+ `starter_targets`, `starter_matched`) |

De propina, `lineup.starter_low_confidence`: los emparejados **con dudas**. El riesgo
contrario también existe y es peor — un emparejamiento flojo mete el pronóstico de
**otro** jugador en una ficha, y eso es peor que no tener pronóstico.

Ninguno decide nada. Solo se ven.

### Cuál de las dos causas disparó `REVIEW_REQUIRED`

```python
ledger_status = "EXACT" if (validation["exact"] and not unknown_types) else "REVIEW_REQUIRED"
```

**Todavía no lo puedo afirmar, y no voy a deducirlo.** Los campos ya suben, pero la
foto de las 16:16 se generó **antes** de este cambio, así que aún no los trae. Se
sabrá en el primer ciclo que corra con esto dentro.

Lo que **sí** se puede afirmar hoy: `validation["exact"]` compara el saldo del libro
con el oficial, y ese libro va 420.200 € alto — así que **la primera causa basta para
explicarlo**. Si además hay tipos sin clasificar, lo dirá `unknown_types`, y ya no
habrá que leer el código para saberlo.

---

## BLOQUE 4 — LAS COMPRAS DEL DUEÑO

### Primero, una corrección sobre la premisa

El encargo decía que las pujas del dueño salen marcadas como `source: DESCONOCIDO`. El
campo es **`target_source`**, y **no significa «lo hizo el dueño»**. El código lo dice
por escrito (`bid_outcome_ledger.py`):

> *«De una puja recogida del tablón no se sabe de qué vía salió. Se marca DESCONOCIDO
> salvo que haya prueba: el libro del carril. (…) **Una puja hecha a mano, una puesta
> por una versión anterior o una que falló al apuntarse entran igual.**»*

O sea: **`DESCONOCIDO` es un superconjunto.** Ahí caen las pujas del dueño y también
las de Pepe de antes de que existiera el marcado de vía. **El campo no puede separar
las dos cosas**, así que doy las dos medidas y sus nombres, sin elegir por ti.

De las 27 del libro: `DESCONOCIDO` 15, `SUBASTA_CARTERA` 8, `ACQUISITION_BOARD` 2,
`RENDIJA` 2.

### Medida A — compras ganadas sin prueba de vía (n = 12)

**Pepe vendió 3.**

| jugador | comprado | importe | vendido | días | resultado |
|---|---|---:|---|---:|---:|
| **Lunin** | 17-09 05:08 | 421.000 | 18-09 07:03 | **1,1** | **−800** |
| Zubeldia | 19-08 05:05 | 2.068.001 | 14-09 23:10 | 26,8 | −221.001 |
| Cepeda | 19-08 06:15 | 463.500 | 15-09 07:22 | 27,0 | +217.500 |

Las otras 9 siguen siendo nuestras (Yamal, Djené, Pablo Ibáñez, Jonny, Pablo Durán,
Manu Sánchez, Expósito, Oriol Rey, Álvaro Carreras).

### Medida B — compras que nunca entraron en el libro de pujas (n = 9)

Más estricta: compras nuestras en el tablón sin **ninguna** puja registrada de Pepe.
**Pepe vendió 4.**

| jugador | días | resultado |
|---|---:|---:|
| Bigas | 3,8 | −357.301 |
| Castrón | 6,0 | +146.044 |
| Suazo | 10,2 | +158.568 |
| Yusi | 18,6 | +722.068 |

(Las otras 5 son las de hoy: Esquivel, Iturbe, Marcão, Barzic y Boyomo.)

### El número, sin regla ni interpretación

**Entre 3 y 4**, según cuál de las dos lecturas valga — y el campo no permite
cerrarlo.

Lo que sí es nítido en las dos medidas: **solo una venta ocurrió dentro de los 4 días,
y es la de Lunin, a 1,1 días.** Todas las demás se aguantaron entre 3,8 y 27 días.

No propongo nada, que es lo que pediste. Solo dejo el contraste ahí.

---

## LO QUE NO HICE, Y POR QUÉ

- **No empujé.** Tres commits en `arreglo/la-reja-y-el-suelo`, esperando a que pasen
  las 21:00 con el partido del Elche empezado. Lo empujas tú.
- **Ni una escritura contra Biwenger.**
- **No encendí la reja.** Está detrás de `BORDALAS_REJA_CON_TOLERANCIA`, apagada. La
  medida está arriba y mi recomendación también, pero la enciendes tú.
- **No toqué** ningún umbral: ni el 3 %, ni el +1 %, ni el tope de puja, ni
  `MIN_WIN_PROBABILITY`, ni el cupo, ni `MAX_SAFE_DEBT`, ni `POSITION_DESIRED`, ni
  `STRATEGIC_FLOOR`, ni las cinco de `PUEDEN_ENCERRARLO`, ni
  `.github/workflows/bordalas-live.yml`. `LINEA_DE_CREDITO` (0,25) tampoco: el tope de
  puja se mueve porque cambia el saldo, no el ratio.
- **No propuse ninguna regla sobre las compras del dueño.** Solo el número.
- **No arreglé la causa raíz**, que sigue viva y es la misma que dejó dicha el commit
  del 10/09: `stable_event_id` hashea el evento entero, así que el almacén guarda cada
  reemisión como un hecho nuevo y **seguirá creciendo**. La tolerancia cura el síntoma
  en la caja; el almacén sigue engordando y cualquier otro lector de
  `board_events.json` sigue expuesto. Arreglarlo es cambiar la identidad del evento en
  el colector, que alimenta a media casa. **Es lo siguiente, y ya lleva ocho días
  señalado.**
- **No pude decir cuál de las dos causas disparó `REVIEW_REQUIRED`.** Los campos ya
  suben; la foto es anterior al cambio. Se sabrá en el primer ciclo.
- **No cerré si Esquivel es fallo de emparejamiento.** Ahora `unmatched` se publica, así
  que el próximo ciclo lo contesta solo — que era el objetivo del bloque 3.
- **No arreglé `test_reloj_solvencia_v1`**: su foto de referencia quedó dentro del
  plazo al refrescar (4,49 h). Es un ajuste de números de ese fichero, ajeno a esto.

### El estado de la verja

**157 de 159.** Los dos rojos son los mismos de ayer y los dos leen
`diagnostico/status.json`:

- `test_orden_de_venta_v1` — **es el propio fallo del portero.** Producción sigue
  publicando a Esquivel de titular porque no hay nada desplegado. Se cierra cuando
  producción regenere la foto con el arreglo dentro. Comprobado aparte que con el
  arreglo la cola se da la vuelta.
- `test_reloj_solvencia_v1` — la foto de referencia, arriba.

En CI esos dos ficheros no existen y las dos guardias se saltan solas.

### Aviso de higiene, otra vez

Correr la verja **vuelve a ensuciar los libros**. Quedan modificados y **no los he
tocado ni incluido en los commits**:

```
data/intelligence/libro_en_la_sombra.jsonl
data/intelligence/marcador.json
data/rival_intelligence/board_events.json
data/solvency/bitacora_del_saldo.jsonl
```

---

## LOS NÚMEROS Y DE DÓNDE SALEN

| dato | valor | n | fuente | fecha |
|---|---|---:|---|---|
| Tramo máximo de reemisión | 9m12s | 5 grupos | `board_events.json` | 09/08–18/09 |
| Separación legítima mínima | 5 días | 7 grupos | idem | 09/08–18/09 |
| Repeticiones mismo importe >1h | 0 | 387 grupos | idem | 09/08–18/09 |
| Mercado: hora de resolución | 05:00, siempre | 42 eventos / 39 días | idem | 09/08–18/09 |
| Sobrecuenta retirada | 15.558.800 € | 2 mánagers | idem, con `reconstruir()` | 18/09 |
| Descuadre reproducido | 4.744.815 vs 4.324.615 | — | idem + duplicado inyectado | 18/09 |
| Pujas sin `seller_user_id` | 27 de 27 | 27 | `bid_outcome_ledger.json` | 10/08–17/09 |
| Mánagers que cruzan amenaza 60 | 0 de 7 | 7 | foto + `apply_threat_scores` | 18/09 16:16 |
| Suelo derivado | −498.750 | — | `lineup_engine.suelo_sin_pronostico()` | 18/09 |
| Compras del dueño vendidas | 3 (medida A) / 4 (medida B) | 12 / 9 | libro de pujas + tablón | 10/08–18/09 |
| Verja | 157/159 | 159 | `scripts/run_validation_gate.py` | 18/09 |
