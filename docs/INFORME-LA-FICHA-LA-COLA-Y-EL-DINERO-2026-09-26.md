# La ficha, la cola y el dinero

**Encargo:** «LA FICHA, LA COLA Y EL DINERO», 26/09/2026 (sustituye a la v1)
**Rama:** `medir/intent-por-euros`, desde `main` en `ea499429`
**Script:** `python scripts/la_ficha_la_cola_y_el_dinero.py`. Solo lee.
**Módulo nuevo, sin conectar:** [la_cola.py](src/analysis/la_cola.py), con su guardia
`test_la_cola_ordena_entre_escalas_v1`.
**Fotos:** 14/09, 18/09, 23/09 y 25/09 (la de hoy, de las 19:13). No he bajado una nueva.

## Veredicto

1. **La medición contradice al encargo en su premisa: la escala del 16-161 % no existe.** En esta
   liga **solo puntúan los once titulares** (`lineupReserves: false`, sin cambios automáticos,
   [DOCTRINA.md:593](docs/DOCTRINA.md#L593)). La vía de ficha vacía cuenta **todos** los puntos del
   candidato, como si jugara ([acquisition_valuation.py:640-674](src/analysis/acquisition_valuation.py#L640-L674)).
   Los cinco de ficha vacía del Computer del 23/09, publicados entre el 98 % y el 128 %, **no
   entraban en nuestro once: sumaban cero.** Una ficha libre no vale el 98 % de un jugador bueno;
   vale lo que ese jugador sume al once.
2. **Las fichas sí se gastaron mal, pero no por lo que decía el encargo.** La cesta las llenó con
   jugadores que sumaban **cero** al once, y **en cada ventana había en el mismo mercado alguien que
   sumaba más de 85 puntos y cabía en el bolsillo** (Larrubia, Carlos Romero, Dumfries, Enes Ünal).
3. **La unidad común es una sola: lo que suma el once rehecho**, en euros de la liga y por euro de
   caja neta. Con ella, las dos escalas de quedárselo son la misma cuenta.
4. **El freno de hoy es la caja, y también la ficha.** Con la cola bien ordenada, hoy pasarían 4 del
   Computer, y **ninguno cabe** en los 2.208.580. Con 1, 2 o 4 fichas libres: **cero**.
5. **Hallazgo lateral y grave:** el Position Manager, presentado como «sombra», **publica jugadores en
   producción**. Eso resuelve lo de Pablo Durán y la línea `Action: EXIT_LISTING` (§3.6).

---

## 1. La ficha

### 1.1 En qué se gastó cada ficha

`bid_outcome_ledger.json`, compras ganadas desde el 13/09 que ocuparon ficha:

| fecha (UTC) | jugador | importe | camino | P(ganar) |
|---|---|---|---|---|
| 15/09 02:48 | Balde | 1.604.001 | cesta (`SUBASTA_CARTERA`) | 0,61 |
| 15/09 02:54 | Benavidez, Paco Cortés, Selu Diallo | 150.376 c/u | cesta | 0,46 |
| 17/09 05:08 | Lunin | 421.000 | entró por `PLANTILLA`, sin puja apuntada | — |
| 18/09 02:49-53 | Marcão, Barzic, Iturbe, Esquivel | 150.376 c/u | cesta | 0,46 |
| 21/09 03:09 | Yeray · Diaby · Guevara | 1.624.051 · 150.376 · 160.401 | cesta | 0,61 / 0,46 |
| 21/09 05:07 | Aihen, Guliashvili, Van Oevelen | 220.551 · 180.451 · 230.576 | `PLANTILLA` | — |
| 23/09 02:56 | Unai López | 2.756.876 | cesta | 0,61 |

**Qué decía Pepe que valían:** la cesta **no apunta valor** (`our_value: null` en todas). Su cuenta
([la_subasta.py:675-680](src/analysis/la_subasta.py#L675-L680)) es `precio × (1 + prima de reventa) −
puja`: con la prima del día (2,11 %), un jugador de suelo valía **unos 2.800 € de margen**. Es
comprar para revender al Computer al día siguiente, no para jugar.

### 1.2 Cuánto costó

Para cada ventana, el mercado de ese día (reconstruido: la foto del 14/09 y el escaparate del 17, 21
y 23/09, donde están los comprados), la plantilla de la foto más cercana **sin los comprados**, y el
once rehecho con cada candidato dentro:

| ventana | lo comprado | suma al once | lo mejor que cabía | suma al once | premios de temporada | precio |
|---|---|---|---|---|---|---|
| 15/09 | Selu Diallo (y otros 3 fuera de ese mercado) | **0** | Larrubia | +108 | 2.898.947 | 4.750.000 |
| 18/09 | Marcão, Barzic, Iturbe, Esquivel | **0** | Carlos Romero | +131 | 3.412.894 | 4.900.000 |
| 21/09 | Yeray, Diaby, Guevara | **0** | Dumfries | +109 | 2.753.684 | 4.720.000 |
| 23/09 | Unai López | **0**\* | Enes Ünal | +87 | 2.197.894 | 4.150.000 |

**El precio del error, proyectado: unos 435 puntos de temporada y 11,3 M de premios** que el once
habría cobrado de más, por 18,5 M de compras que cabían en el bolsillo de esos días (5,97-9,74 M).

**Pero con dos cautelas grandes, y las dos cuentan:**

- **Es una proyección** (histórico de la temporada pasada × titularidad). Lo que ha pasado de verdad
  con los dos que la cola habría fichado y tienen historia (§2.5) **no la sostiene**: Larrubia
  −10,1 % de precio y 13 puntos en 2-3 jornadas; Cabrera −18,1 % y 1 punto. n=2 y dos semanas.
- \*Unai López **sí** está hoy en el once publicado. Pero el once publicado se elige por
  `lineup_score` y el mío por la proyección: son dos medidas distintas del mismo once (§2.3).

### 1.3 Por qué pasó, con la línea

**La cesta compra por euro de margen de reventa, no por lo que suma al once.**
[`elegir_la_cesta`](src/analysis/la_subasta.py#L1028-L1246) ordena por `_por_euro` = margen esperado ×
probabilidad de ganar / puja ([:992-1025](src/analysis/la_subasta.py#L992-L1025)). En modo cartera
todos rinden lo mismo por euro, así que **el desempate es el más barato**
([:1155-1167](src/analysis/la_subasta.py#L1155-L1167)): de ahí los 150.376. La ficha es solo un
límite de cuántos caben ([:1183](src/analysis/la_subasta.py#L1183)), **no un recurso con precio**, y
los puntos se llevan «para que se puedan mirar en pantalla: no decide nada»
([:2242-2244](src/analysis/la_subasta.py#L2242-L2244)). **Sí: es la regla del barato gastando el
recurso caro.**

### 1.4 ¿Se repetiría mañana?

**La chatarra, no. El error, sí.**

- **No compraría un jugador de 150.000 que no juega.** Desde el 22/09,
  `BORDALAS_REVENTA_SOLO_SI_JUEGA` veta a quien tiene pronóstico < 40 %, jerarquía por debajo de
  Importante o no puede jugar ([deployment.py:421-477](src/analysis/deployment.py#L421-L477)).
- **Sí volvería a llenar la ficha con el más barato que pase ese filtro**, sin mirar si entra en el
  once. Es lo que pasó con Unai López el 23/09, ya con el filtro puesto.
- **Hoy no puede:** con 0 fichas libres, la cesta no puja
  ([la_subasta.py:1100-1110](src/analysis/la_subasta.py#L1100-L1110)).

### 1.5 El tope de fichas

**No se puede sacar del código ni de lo que ya se guarda.**

- `count_free_slots` ([roster_expansion_shadow.py:202-330](src/analysis/roster_expansion_shadow.py#L202-L330))
  resta nuestra plantilla a la mayor de la liga, y lo marca como cota inferior.
- En el catálogo guardado, `league.settings` trae `loansMaxRounds`, `maxPurchasePrice`,
  `lineupMaxClubPlayers` y `lineupReserves`, **pero no el tamaño máximo de plantilla**.
- Donde podría estar: `GET /league/{id}` (la configuración de la liga), que **producción no llama**.
  Solo lo pide un script de diagnóstico ([inspect_biwenger.py:46](src/inspect_biwenger.py#L46)).
  No lo he llamado.
- **Lo más rápido: que el dueño lo mire en la app.** Es un número.

### 1.6 Con 1, 2 o 4 fichas libres hoy

De los 58 de la foto, 53 pueden jugar y **19 suman al once** (4 del Computer):

| fichas | pasan con el bolsillo de 2.208.580 | sin mirar la caja, por orden de la cola |
|---|---|---|
| 1 | **0** | Lejeune (+103, 73,1 %, 3,56 M) |
| 2 | **0** | + Antonio Blanco (+67, 52,4 %, 3,23 M) |
| 4 | **0** | + Juan Iglesias (+46, 34,0 %), Javi Hernández (+43, 31,6 %) |

**Hoy las fichas no son el freno: es la caja.** Aunque hubiera cuatro, no cabe ninguno.

---

## 2. La cola

### 2.1 Qué debe filtrar cada escala, y por qué el rendimiento no filtra

- **Comerciar:** un listón del 3 % contra una prima del 1-2 % no deja pasar a nadie **por diseño**.
  Es una decisión de negocio: o esa vía sobra, o necesita otro listón.
- **Quedárselo (las dos escalas):** debería filtrar **si entra en el once**, los vetos de titularidad
  y jerarquía, y la caja. Hoy:
  - la ficha vacía **no mira si entra en el once** (fallo);
  - la mejora del once lo mira solo contra su posición (el fallo del informe de ayer);
  - **y el 3 % no filtra por accidente de diseño, no porque sobre.** `MEJORA_INSUFICIENTE` exige 8
    puntos de mejora ([player_value_engine.py:1581-1592](src/analysis/player_value_engine.py#L1581-L1592)),
    y 8 × 30.000 × 31/38 = 195.789 € ya es el 3 % de cualquier jugador de menos de 6,5 M. **El filtro
    de verdad es un número de puntos, no un rendimiento: el listón está en el sitio equivocado.**
  - En la unidad común sí aparecen rendimientos bajos: **2 de 19** por debajo del 3 % (Fermín, 2,9 %;
    Baena, 0,5 %). Los dos cuestan más de 10 M.

### 2.2 Los que no tienen puntos de más, desglosados

Foto del 25/09, 45 de 58 sin `el_que_se_queda`:

| grupo | motivo | n |
|---|---|---|
| **sin puntos de más** | `NO_MEJORA` (no supera al titular de su posición) | **10** |
| | `NO_MEJORA_JERARQUIA` | 6 |
| | `PIERDE_TITULARIDAD` | 3 |
| | `NO_MEJORA_TITULARIDAD` | 2 |
| **sin techos** | `SIN_VALOR` (ninguna vía) | 19 |
| | `NO_DISPONIBLE` | 5 |

**De los 21 sin puntos de más: 10 por no mejorar, 11 por vetos**, y ninguno por falta de pronóstico.
Pero `NO_MEJORA` se mide contra la posición: es el filtro que cambia si se rehace el once.

### 2.3 La unidad común

**Euros de premios que el once rehecho cobraría de más, por euro de caja neta** ([la_cola.py](src/analysis/la_cola.py)):

```
premios   = mejora del once rehecho (puntos de temporada) x jornadas que quedan / 38 x 30.000
caja neta = precio - lo que se recupera vendiendo para hacer sitio
```

**La defensa:**

- **Solo cobra lo que puntúa en el once.** Un 16 % de ficha vacía y un 70 % de mejora del once no
  son comparables porque el primero cuenta puntos que no se cobran. Rehaciendo el once, los dos se
  miden igual: lo que suma el once nuevo contra el de hoy. La ficha vacía es simplemente la que no
  obliga a vender.
- **Los euros son los de la liga:** 30.000 por punto, medido (`bonusPoint: 30000` en la propia
  configuración de la liga).
- **Se divide por la caja neta** porque el jugador sigue siendo nuestro: lo que se inmoviliza es el
  precio menos lo que se cobra por el que sale.

**Una limitación, dicha:** los puntos son la proyección de la valoración (histórico × titularidad),
y el once de producción se elige por `lineup_score`, que pesa también el partido de la semana. Son
parecidos pero no iguales: Unai López está en el once publicado y en el mío no suma.

**La guardia** `test_la_cola_ordena_entre_escalas_v1` (3 pruebas, en la verja): pone un medio de
ficha vacía, más alto en crudo pero que no entra en el once, frente a un delantero de mejora del
once, más bajo en crudo pero que sí entra. La cola pone primero al segundo. **Muerde:** si la ficha
vacía contara todos sus puntos (las dos escalas en la misma unidad), falla diciendo que no mediría
nada.

### 2.4 El precio de reserva: no se puede justificar todavía, y así se mediría

Lo que hay medido:

| qué | n | resultado |
|---|---|---|
| precio a 14 días (11/09 → 25/09) de los que puntúan (≥ 4 puntos por partido, ≥ 4 jugados) | 150 | mediana **+3,07 %**, suben el 60 % |
| lo mismo, del resto | 393 | mediana **−10,53 %**, suben el 16 % |
| prima mediana del Computer al recomprar | — | 2,11 % |

**Propuesta, defendible hoy:** que el rendimiento en la unidad común supere al de **la alternativa
que de verdad se tomaría** con ese dinero y esa ficha, que es **el siguiente de la cola**. Es un
precio de reserva móvil, no un número redondo: la ficha vale lo que valga el mejor que no entra. Y
como suelo, la prima del Computer (2,11 %): si quedárselo rinde menos que revenderlo, se revende.

**Lo que no se puede fijar todavía es cuánto descontar por el riesgo del precio en toda la
temporada**: la historia de precios tiene cinco semanas. Se medirá con `libro_de_la_valoracion`, que
rellena el precio y los puntos a 7 y 14 días de cada candidato. Las primeras filas a 14 días llegan
el 07/10.

### 2.5 A quién habría fichado Pepe cada día

Con la cola y **el primero del Computer que cabe** en el bolsillo de fichar de ese día:

| foto | suman al once | bolsillo | habría fichado | qué pasó después (hasta el 25/09) |
|---|---|---|---|---|
| 14/09 | 7 de 20 | 5,97 M | **Larrubia**, 4.750.000 (+108, 61 %) | precio −10,1 %; de 14 a 27 puntos |
| 18/09 | 7 de 19 | 9,74 M | **Cabrera**, 3.040.000 (+114, 98 %) | **se compró** (15:18). Precio −18,1 %; de 8 a 9 puntos |
| 23/09 | 0 de 18 | 8,64 M | nadie: ninguno suma al once | — |
| 25/09 | 4 de 17 | 2,21 M | nadie: el primero, Lejeune (3,56 M), no cabe | — |

**Entre 0 y 1 al día con la caja, y hasta 7 al día sin ella.** Los dos casos con historia salieron
mal en sus primeras dos semanas. **n=2: no dice que la cola se equivoque, dice que la proyección de
puntos aún no está medida contra lo que pasa.** Es el encargo del calendario.

### 2.6 Dónde caen las dos pujas del dueño

Cola del 25/09, 19 que suman al once:

| puesto | jugador | rendimiento | |
|---|---|---|---|
| 1 | **Lejeune** | 73,1 % | Computer · el dueño no puja por él |
| 2 | Cristian Romero | 62,9 % | rival |
| **3** | **Antonio Blanco** | 52,4 % | **puja del dueño, 3.288.000** |
| 4 | Chupe | 40,7 % | rival |
| 5 | Ez Abde | 35,7 % | rival |
| **6** | **Juan Iglesias** | 34,0 % | **puja del dueño, 3.520.000** |

Entre los del Computer: **Lejeune 1.º, Antonio Blanco 2.º, Juan Iglesias 3.º.** La cola pone arriba
las dos del dueño, pero **pondría a Lejeune por delante de las dos**: suma +103 al once por
3,56 M. Coherente, no una prueba (n=2, doctrina 95).

---

## 3. El dinero

### 3.1 Cuánto hay, y en cuánto tiempo

Caja **−7.005.920**; pujas vivas del dueño **6.808.000**; déficit del reloj **13.813.920**. Hay **14
ofertas vivas del Computer**, que se cobran al aceptar:

| grupo | suma | coste en puntos del once |
|---|---|---|
| **reservadas por solvencia, fuera del once** (Yeray, Álvaro Carreras, Van Oevelen, Guliashvili, Iturbe) | **3.214.300** | **0** |
| reservadas, en el once (Maffeo, Rubén García) | 4.004.300 | 11 y 14 |
| no reservadas, titulares normales (Olasagasti, Jutglà, Cabrera, Jonny) | 11.429.400 | 19, 33, 63 y 6 |
| protegidas (Expósito, Dmitrovic) | 9.881.100 | 76 y 180 |
| Yamal (`NEVER_SELL`) | 22.661.400 | — |

**Por publicar y esperar, sin oferta:** Ceballos (4,21 M), Pablo Durán (1,1 M), Aihen, Diaby y
Guevara. Cuestan cero puntos, pero pueden no venderse nunca.

**Lo barato de verdad: 3.214.300 € hoy, por cero puntos, y 5 fichas libres.** Según la identidad
medida del tope de puja (`puja máxima = saldo + valor de la plantilla / 4 − comprometido`,
[la_plaza_y_el_cable.py:30](src/analysis/la_plaza_y_el_cable.py#L30)), eso subiría la puja máxima en
unos **2,4 M, hasta unos 4,6 M**, y Lejeune cabría. **Pero esas cinco son justo las que la solvencia
tiene reservadas para tapar el agujero** (§3.5): ese dinero ya tiene destino.

### 3.2 Cuánto cuesta cada venta

Está en la tabla de arriba: todos los de la cola de venta (`sale_order`) que no están en el once
cuestan **0 puntos**. Maffeo (+11) y Rubén García (+14) son los únicos baratos que sí están en el
once. **Cada venta libera una ficha.**

### 3.3 Ceballos: confirmado

**El tablón de Biwenger dice 5.480.138**, con Manzagool segundo a 4.450.000. Hoy vale 4.210.000:
**−1.270.138, −23,18 %**. El libro de pujas decía 5.280.138 y **se equivoca**; el de posiciones
acierta. Y un dato que faltaba: **se pagó 1.030.138 más que la segunda puja.**

- **Venderlo** realiza **−1,27 M**. No tiene oferta del Computer: habría que publicarlo y esperar.
- **No venderlo** cuesta **4,21 M de caja parada que no suma puntos**: no entra en el once
  (proyección 20 puntos, 30 % titular). Con 13,8 M de agujero al 09/10, esa caja es la más cara del
  equipo.

**No lo decido yo.**

### 3.4 Los tres bolsillos

| cifra | qué es | quién la usa |
|---|---|---|
| **Puja máxima** 2.208.580 | `market.status.maximumBid` de Biwenger, tal cual ([league_collector.py:242-264](src/collectors/league_collector.py#L242-L264)) | tope duro de todos: el ejecutor rechaza por encima ([live_bid_executor.py:255](src/actions/live_bid_executor.py#L255)) |
| **Presupuesto trading** 2.145.286 | el presupuesto de **BUY V10** ([market_trader_shadow.py:309-323](src/analysis/market_trader_shadow.py#L309-L323)) | solo BUY V10, que hoy **está inerte**: la especulación vieja está en pausa y no le llegan candidatos |
| **Capital sporting-safe** 3.575.478 | `sporting_safe_spend_capacity` ([market_trader_shadow.py:126-172](src/analysis/market_trader_shadow.py#L126-L172)) | solo como tope de BUY V10 |

**Ninguna de las tres paga un fichaje del tablero.** El fichaje se compara contra **el bolsillo de
fichar** (`acquisition_budget`, [acquisition_budget.py:109-338](src/analysis/acquisition_budget.py#L109-L338)):
caja + margen de deuda, topado por la puja máxima y descontando las pujas vivas. En la foto de hoy
vale **2.208.580**, igual que la puja máxima, porque es la puja máxima quien lo topa. **Con ventas,
sube la puja máxima (0,75 × lo vendido), y con ella el bolsillo de fichar.**

### 3.5 Las reservas de solvencia

**Son siete, no seis: falta Iturbe.** Suman 7.218.600.

- **Se reservan contra la deuda de caja (7.005.920), no contra el déficit del reloj (13.813.920)**
  ([solvency_engine.py:427-564](src/analysis/solvency_engine.py#L427-L564)). Las dos pujas del dueño
  (6,8 M) no están cubiertas. **Si las ganan, la deuda de caja salta a 13,8 M y se reservan más**:
  Olasagasti, Jutglà, Cabrera y Jonny.
- **El algoritmo:** se ordenan por menor valor deportivo (franquicia, luego valor estratégico, luego
  mayor prima) y se van reservando hasta cubrir la deuda. **Una oferta deja de estar reservada
  cuando la deuda baja de lo que suman las que van delante de ella.** La primera no se libera
  mientras el saldo sea negativo. La foto no publica el orden, así que no puedo dar el número exacto
  de cada una.
- **¿Vender barato libera caro? Sí, casi seguro.** Las cinco de fuera del once (3,21 M, cero puntos)
  son las de menos valor deportivo, así que van delante. Venderlas baja la deuda a 3,79 M, y **Maffeo
  y Rubén García (4,0 M, los dos del once) dejarían de estar reservados**. Es condicional al orden
  exacto, que la foto no enseña.

### 3.6 Pablo Durán: manda el Position Manager, y no está en sombra

- **Intención de venta** ([sale_intent.py:188-336](src/analysis/sale_intent.py#L188-L336)): mide si el
  jugador sobra deportivamente (jerarquía, once, puntos, precio que cae). **Nunca mira la ganancia
  sobre lo que se pagó.** 40/100 = «vigilado». **Solo observa.**
- **Position Manager** ([position_manager_shadow_v106.py:549-724](src/analysis/position_manager_shadow_v106.py#L549-L724)):
  mide la ganancia contra el precio de entrada. Pablo Durán entró a **236.531** y vale **1.100.000**:
  +365 % → `TAKE_PROFIT`, 95.
- **Discrepan porque miden cosas distintas y no comparten ni un dato.**
- **Y el Position Manager decide en producción**, aunque su pantalla diga «SOLO SHADOW»: con un
  candidato de salida y sin escritura previa en la vuelta, publica al jugador a su valor de mercado
  ([v10_full_autonomous_live.py:1355-1371](src/v10_full_autonomous_live.py#L1355-L1371)), **sin
  guardarraíl posicional**.
- **De ahí sale el `Action: EXIT_LISTING` sin escritura** que estaba apuntado: `action_taken` se
  escribe aunque no se envíe nada (por ejemplo, porque ya estaba publicado).

**No lo he tocado. Hay que decidir si eso es una sombra o una puerta de venta.**

---

## 4. El interruptor, propuesto y apagado

**Nombre:** `BORDALAS_FICHAR_POR_EL_ONCE`. **No existe en el código**: este encargo solo diseña. Lo
que tendría que hacer al construirlo:

1. **La vía de quedárselo**, las dos escalas, se valora con la **mejora del once rehecho**
   (`la_cola.mejora_del_once`) y no contra la posición ni con todos los puntos.
2. **La clase** de la operación se decide en la unidad común: si quedárselo rinde más que la prima del
   Computer, es un fichaje.
3. **Una cola**, no un listón: uno por ventana, el primero que cabe.
4. **Precio de reserva:** el rendimiento del siguiente de la cola, y como suelo la prima del Computer.
5. **Con 0 fichas, vender antes** al primero de `sale_order` que cueste 0 puntos.

**Comentario para el YAML** (el dueño lo pega a mano cuando exista el código):

```yaml
      # FICHAR POR EL ONCE — propuesto 26/09, NO construido todavia.
      #
      #   QUE HARIA. Valorar a quien se ficha para quedarselo por lo que suma
      #   el once REHECHO (las siete formaciones), en premios de la liga
      #   (30.000 EUR/punto) por euro de caja neta. En esta liga SOLO PUNTUAN
      #   ONCE (lineupReserves: false): hoy la ficha vacia cuenta todos los
      #   puntos del candidato aunque se quede en el banquillo, y la mejora
      #   del once se mide solo contra el titular de su posicion. Y en vez de
      #   un liston, una cola: uno por ventana, el primero que cabe.
      #
      #   MEDIDO (fotos del 14, 18, 23 y 25/09, n=74 del Computer):
      #     - la cesta lleno las fichas con jugadores que sumaban 0 al once;
      #       en cada ventana habia alguien de +87 a +131 que cabia.
      #     - pasarian el criterio 7, 7, 0 y 4 al dia; con la caja, 1, 1, 0, 0.
      #     - hoy: Lejeune primero (+103, 73 %), y no cabe en 2.208.580.
      #
      #   LO QUE NO ESTA MEDIDO Y HAY QUE VIGILAR:
      #     - AVISO: ESTE INTERRUPTOR PUEDE CONVERTIR A PEPE DE "NO FICHA A
      #       NADIE" EN "QUIERE FICHAR A TODOS", CON DINERO DE VERDAD. Sin la
      #       caja, pasarian hasta 7 al dia. Lo que lo frena es la cola (uno
      #       por ventana) y el bolsillo: si alguno de los dos se quita, no
      #       queda freno.
      #     - Si la cola ofrece mas de uno y hay una ficha, entra el primero y
      #       los demas esperan a la ventana siguiente; con 0 fichas, hay que
      #       vender antes, y eso es otra escritura.
      #     - La proyeccion de puntos (historico x titularidad) NO esta medida
      #       contra lo que pasa: los dos casos con historia (Larrubia,
      #       Cabrera) perdieron precio y puntuaron poco en dos semanas. n=2.
      #     - El precio de reserva por riesgo de precio no esta medido: el
      #       historico tiene cinco semanas. libro_de_la_valoracion da d14 a
      #       partir del 07/10.
      #     - Los vetos de titularidad se aplican contra el que sale del once
      #       rehecho: 4 de 8 caian por PIERDE_TITULARIDAD en la foto del 25/09.
      BORDALAS_FICHAR_POR_EL_ONCE: "1"
```

---

## 5. Lo que no hice, y por qué

- **Ni una escritura ni una llamada a Biwenger.** Tampoco he bajado una foto nueva: todo es de las
  cuatro fotos y los libros.
- **No he construido el interruptor**: el encargo diseña y mide. [la_cola.py](src/analysis/la_cola.py)
  son funciones puras que nadie llama para decidir.
- **No he vendido, publicado ni aceptado nada**, ni he tocado el Position Manager, aunque publica en
  producción (§3.6): es una decisión del dueño.
- **No he dado el número exacto que libera cada reserva**, porque la foto no publica el orden. Doy la
  regla y el caso barato.
- **No he corrido el paso 0**: no hay interruptor nuevo.
- No he tocado la vía, la moneda, las reglas 2 y 3, el calendario, el arreglo del once, el workflow
  ni ninguna constante de la lista. No he empujado.

Lo que entra en el commit: este informe, `la_cola.py`, su guardia (registrada en la verja) y el
script.
