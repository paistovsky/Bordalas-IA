# VENDER A MANAGERS, Y VER A LOS 546

**Fecha:** 2026-09-20 (octavo y último del día) · **Rama:**
`arreglo/vender-a-managers`, desde `arreglo/el-bucle-abajo` · **Escrituras contra
Biwenger:** ninguna · **Interruptor nuevo:** `BORDALAS_CESTA_SOLO_EL_SUELO`,
**apagado** · **Los dos aprobados siguen apagados: los enciende el dueño.**

**Verja: 165 de 165.**

---

## LO QUE HAY QUE LEER ANTES DE ENCENDER NADA

Dos hallazgos que contradicen los encargos, y los dos son buenos:

> **1. El corte de la cesta ahorra 25.501 €, no un millón.** De las nueve operaciones
> cerradas por encima de 1,5 M, la cesta hizo **una**. Las otras ocho son del carril
> (3, −237.847 €) y de compras sin libro (5, −775.435 €).

> **2. Ver a los 546 no cuesta una llamada más.** Las veinte páginas de equipo ya
> están en disco, parseadas, con `probability` y `hierarchy_value` para **513
> jugadores**. El tablero sólo empareja 64 porque la **lista de objetivos** son
> nuestra plantilla y el mercado del día. El límite no es la fuente: es a quién le
> preguntamos.

---

## BLOQUE 1 — CERRAR LA REVENTA AL COMPUTER ARRIBA

### El corte, y es el que ya existía

`CORTES_DE_PRECIO[0]` = **1.500.000**, el mismo que ya parte la rejilla de la pelea y
la de la prima por tramo. Tres cosas del mismo eje con el mismo corte (doctrina 84).

Vive en [`la_subasta.py`](src/analysis/la_subasta.py), dentro de
`candidatos_en_modo_cartera`, y sólo afecta a la cesta: **cerrar no es borrar, y no se
toca la compra por encima del corte** — ésa es la vía del tablero de fichajes.

> **Interruptor: `BORDALAS_CESTA_SOLO_EL_SUELO`, apagado.**

### La cuenta, y no es la que esperábamos

De las **47 filas** del libro de pujas, **29 llevan importe ≥ 1.500.000**. Por vía:

```
  RENDIJA            15
  DESCONOCIDO        10
  SUBASTA_CARTERA     3    <- las unicas a las que llega el corte
  ACQUISITION_BOARD   1
```

Y sobre las **23 operaciones cerradas**, las nueve por encima del corte:

| jugador | pagado | cobrado | resultado | vía |
|---|---:|---:|---:|---|
| Djené | 2.409.001 | 1.870.100 | **−538.901** | sin libro |
| #2169 | 2.288.001 | 1.930.700 | **−357.301** | sin libro |
| Trent | 2.760.000 | 2.536.500 | −223.500 | `RENDIJA` |
| Zubeldia | 2.068.001 | 1.847.000 | −221.001 | sin libro |
| Maffeo | 1.664.350 | 1.621.500 | −42.850 | `RENDIJA` |
| **Balde** | **1.604.001** | **1.578.500** | **−25.501** | **`SUBASTA_CARTERA`** |
| Boyomo | 1.817.297 | 1.845.800 | +28.503 | `RENDIJA` |
| Gabriel Suazo | 1.629.832 | 1.788.400 | +158.568 | sin libro |
| Jonny | 1.570.000 | 1.753.200 | +183.200 | sin libro |

```
  sin libro          n=5   -775.435   (74,6 % del daño)
  RENDIJA            n=3   -237.847   (22,9 %)
  SUBASTA_CARTERA    n=1    -25.501   ( 2,5 %)
```

> **El corte habría parado UNA operación cerrada —Balde— y ahorrado 25.501 €.**

La decisión es correcta en su sitio: la única vez que la cesta operó por encima del
suelo, perdió. Pero **apunta a la vía que hizo el 2,5 % del daño**. Si lo que se
quiere es dejar de perder un millón arriba, el corte tiene que alcanzar al **carril**
— y cinco de las nueve son compras **sin libro**, que ningún interruptor para.

### Quién llena esas fichas: nadie tiene que hacerlo

```
  LAS 36 COMPRAS DE LA TEMPORADA        < 1,5 M   >= 1,5 M   total
  sin libro (las del dueño)                   4         12      16
  SUBASTA_CARTERA (la cesta)                  9          1      10
  DESCONOCIDO                                 3          1       4
  RENDIJA                                     1          3       4
  ACQUISITION_BOARD                           1          1       2
```

**La cesta compró 10 jugadores: nueve abajo y uno arriba.** El corte le quita **1 de
10**. Quien llena las fichas por encima del corte es **tu vía, con doce compras**.

Y la plantilla hoy son **15 jugadores con 9 fichas libres**: no hay ninguna presión de
llenado que la cesta estuviera resolviendo.

> **La plantilla no encoge. La cesta apenas operaba arriba.**

### La guardia

`src/analysis/test_la_cesta_solo_el_suelo_v1.py`, **4 pruebas, en la verja**.

| prueba | qué exige |
|---|---|
| `test_sin_candidatos_arriba_no_se_comprueba_nada` | **falla si todos los candidatos están por debajo del corte** |
| **`test_la_cesta_no_opera_arriba_del_suelo`** | con el interruptor puesto, nadie por encima genera puja — y los de abajo siguen enteros |
| `test_el_corte_es_el_que_ya_existia` | el corte sigue siendo `CORTES_DE_PRECIO[0]` y la prima parte por el mismo sitio |
| `test_apagado_se_comporta_como_ayer` | apagado, ni un candidato menos ni un euro distinto |

---

## BLOQUE 2 — LA VENTA A MANAGERS

### ¿Existe el camino de código? Sí, y además está encendido

| pieza | estado |
|---|---|
| `competitive_transaction_engine.evaluate_sale_to_rival` | existe, devuelve `ACCEPT_NOW` / `ACCEPT_SACRIFICE_LINEUP` / `COUNTER_OFFER` / `NEVER_SELL` |
| `competitive_live_executor` | `SUPPORTED_LIVE_ACTIONS = {COUNTER_OFFER, ACCEPT_NOW, ACCEPT_SACRIFICE_LINEUP}` |
| `write_client.accept_offer` | existe, con su `build_accept_offer_request` |
| el ciclo de producción | `run_cycle(live=True, **competitive_live=True**)` |
| el estado publicado hoy | `competitive.live_enabled: **true**`, `status: IDLE` |

> **Sabe, puede y está enchufado.** No es como `place_bid` a un rival —que sabía y no
> lo hacía por una puerta cerrada—: aquí no hay puerta cerrada. Hoy dice
> *«Competitive V2.0 está activo y no hay negociaciones de managers»*.

### ¿Por qué se rechazaron las cinco? No lo sé, y ésa es la respuesta honesta

Las cinco son del **12 y 13/08**. El libro de negociaciones —
`counteroffer_repricing_state.json` — se estrenó el **16/08** y está vacío:
`{"negotiations": {}}`.

> **No hay ningún registro de qué decidió el motor con esas cinco ofertas.** No puedo
> decirte el motivo de ninguna, y menos si fue el mismo las cinco. Lo que sí puedo
> decirte es **contra qué listón se midieron**.

### El listón, y aquí está el problema

`evaluate_sale_to_rival` acepta si `amount >= strategic_sell_price`, y

```
  strategic_sell_price = market_value
                       x (1 + internal_premium)          <- hasta +25 %
                       x (1 + competitive + temporal + sporting - solvency)
                                                          <- sporting hasta +18 %
```

Con las primas a cero el listón es el precio de mercado; con ellas altas puede pasar
del **+40 %**. Y las cinco ofertas que recibimos estaban en **+2,6 % a +6,4 %**.

### ¿Misma vara que el Computer? No. Y está del revés

| | oferta del **Computer** | oferta de un **manager** |
|---|---|---|
| quién decide | `offer_decision_engine`, con la regla `compensa` unificada el 18/08 | `evaluate_sale_to_rival` → `strategic_sell_price` |
| el listón | «compensa»: puntuación de venta y prima | mercado **× hasta +25 % × hasta +18 %** y más |
| lo que pagan, medido | **+0,55 %** de mediana, n=21 | **+7,5 %** de mediana, n=9 · **+7,5 %, +23,8 %, +32,0 %** en las tres nuestras |
| lo que hemos ganado | **−900.517 €** | **+868.112 €** (n=2 con compra previa) |

> **Le exigimos más al comprador que paga más.** Al Computer, que da +0,55 %, le
> aplicamos la regla flexible del 18/08; al manager, que da entre +7,5 % y +32 %, le
> exigimos un precio estratégico que puede ser un 40 % por encima del mercado.

Y el plazo va en la misma dirección equivocada: la venta a un manager tarda más (6 y
18,6 días contra 4,7), y eso pesa **en contra** en el suelo de cobro — cuando es
precisamente donde estuvo el +143,3 % de Yusi Enríquez.

### Tu regla, discutida

> *«Una oferta de un manager por encima del mercado se acepta salvo que el jugador
> esté en el once.»*

**Coincido en la dirección y no en el umbral,** y por lo medido hoy:

- **A favor:** las tres ventas cerradas a managers fueron +7,5 %, +23,8 % y +32,0 %, y
  las nueve de la liga con precio comparable están **todas** por encima del mercado.
  Con `n = 12` entre las nuestras y las ajenas, «por encima del mercado» no es una
  corazonada.
- **En contra, y con un caso:** dos de las cuatro ofertas que rechazamos eran por
  **Jutglà y Olasagasti**, que siguen con nosotros con 29 y 32 puntos. Tu propia
  excepción —«salvo que esté en el once»— los habría protegido. Bien.
- **Pero el «por encima del mercado» a secas es poco listón:** Ximo Navarro y Yeray,
  los dos que sí soltamos, nos dieron **+185.700** y **−161.900** contra las ofertas
  rechazadas. Empate de 23.800 € en `n = 2`. Aceptar a +2,6 % habría sido peor en uno
  de los dos.

**Lo que yo pondría, y el número es tuyo:** el listón no es «por encima del mercado»
sino **«por encima de lo que nos daría el Computer»**, que está medido: **+0,55 % de
mediana en 21 ventas**, y por tramo, +1,51 % en el suelo y −2,57 % arriba. Una oferta
de manager que supere eso ya gana, y no hace falta exigirle un 25 % de prima interna.

### Qué costaría abrir la puerta

**Nada de código nuevo.** Las piezas están y están enchufadas. Lo que hay que mover es
un umbral:

1. **Bajar `strategic_sell_price` para las ofertas de manager** a la vara del
   Computer. Es un número, es tuyo, y está medido.
2. **Apuntar cada decisión en el libro de negociaciones**, que lleva vacío desde el
   16/08. Sin eso, la próxima vez tampoco sabremos por qué se dijo que no. Esto sí es
   trabajo, y es media tarde.
3. **Nada más.** No hay que escribir ningún camino de escritura: `accept_offer` existe
   y `competitive_live` está en `true`.

**No he tocado ningún umbral.**

---

## BLOQUE 3 — VER A LOS 546

### Por qué 64: no es un filtro ni una llamada. Es una lista de objetivos

```
  el tablero de hoy    targets 64   =  roster 16  +  mercado del dia 48
                       matched 64
                       team_pages 13  de 20 equipos de LaLiga
```

`build_starter_lookup` recorre `futbolfantasy_board.players`, y ese tablero se
construye **a partir de una lista de objetivos**: nuestra plantilla más lo que está a
la venta hoy. El proveedor descarga **páginas de equipo**, no jugadores, y sólo
descarga los equipos donde hay un objetivo: **13 de 20**.

### Qué costaría cubrir 115 y 546: nada, porque ya está descargado

```
  paginas de equipo en data/ff_html:   20
  jugadores en esas paginas:          513
  con `probability` y `hierarchy`:    513
```

> **Las veinte páginas están en disco, parseadas, con la probabilidad y la jerarquía
> de los 513. El tablero empareja 64 porque sólo le pedimos 64.**

| objetivo | páginas a pedir | llamadas nuevas | minutos |
|---|---:|---:|---|
| los 64 de hoy | 13 | — | lo de ahora |
| los **115 candidatos** | ≤ 20 | **0 a 7** | segundos |
| los **546 del catálogo** | **20** | **7** | segundos |

Siete peticiones más, con `TIMEOUT = 25 s` por petición y una caché de `TTL = 7200 s`
que hoy sale `TOPPED_UP`. Contra una vuelta normal de **13 a 19 minutos** y un tope de
job de **35**.

> **Cabe de sobra. No es un problema de red ni de minutos: es que la lista de
> objetivos se construyó para «lo que puedo comprar hoy» y nunca se amplió a «lo que
> hay».**

### El pronóstico casero: acierta el 85 %, y no hace falta

Medido contra los 64 de la fuente, quedándome con los **53** que tienen veredicto
claro (27 `STARTER`, 26 `BENCH`) y usando **sólo nuestros datos** (`playedHome +
playedAway` y `points` del catálogo):

| regla casera | acierto | falsos titulares | titulares perdidos |
|---|---:|---:|---:|
| decir siempre `STARTER` (la base) | 50,9 % | — | — |
| ha jugado ≥ 3 jornadas | 83,0 % | 9 | 0 |
| **ha jugado ≥ 5 jornadas** | **84,9 %** | **5** | **3** |
| ha jugado ≥ 6 jornadas | 75,5 % | 1 | 12 |
| 4+ jornadas y ≥ 2,0 pts/jornada | 83,0 % | 7 | 2 |

**`n = 53`, jornada 7.** El mejor casero acierta el **84,9 %** contra un 50,9 % de
base: mucho mejor que nada, y **ocho errores de 53 en una decisión que mueve dinero**.

> **Y sobre todo: no hace falta.** El pronóstico bueno de los 513 ya está en disco y
> no cuesta una llamada. Construir un sustituto del 85 % para no usar el 100 % que ya
> tenemos sería trabajo para empeorar.

**Donde sí valdría** es como red de seguridad: el tablero se vacía entero cuando es de
otra jornada (`board_rejection`), y ese día Pepe se queda quieto. Un casero al 85 %
sería mejor que cero. Pero eso es otro encargo.

### ¿Cabe en los 35 minutos?

> **Sí, cabe.** Siete peticiones más sobre una vuelta de 13-19 minutos, con un tope de
> 35. No es el plazo lo que nos impide ver a los 546.

---

## LO QUE NO HICE, Y POR QUÉ

- **No encendí ningún interruptor**, tampoco los dos que aprobaste: los enciendes tú,
  uno por vuelta, con su ficha. Los tres que hay armados y apagados son
  `BORDALAS_SIN_REFERENCIA_ESCALA`, `BORDALAS_CESTA_SOLO_EL_SUELO` y
  `BORDALAS_PRIMA_POR_TRAMO`.
- **No abrí la venta a managers ni toqué `strategic_sell_price`.** Es un umbral y es
  tuyo.
- **No construí el pronóstico casero.** Medido su acierto: 84,9 %, `n = 53`.
- **No amplié la lista de objetivos del tablero de pronóstico**, que es donde está el
  arreglo del bloque 3. No lo pedías y toca un colector.
- **No pude decir por qué se rechazaron las cinco ofertas.** El libro de negociaciones
  está vacío desde el 16/08 y las ofertas son del 12-13/08.
- **No recomiendo el corte de la cesta como está planteado sin decir esto:** ahorra
  25.501 € medidos, no un millón. El millón es del carril y de tus compras.
- **Ni una escritura contra Biwenger.** La ventana cerrada, el workflow sin tocar,
  ningún umbral movido.

### La verja

```
165 de 165 OK      (eran 164; una guardia nueva)
```

Salida a fichero, árbol quieto, sin `git add -A`. **No empujo.**

### El `n`, y cuándo se cortó

| medida | `n` | corte |
|---|---|---|
| el corte de la cesta | **1** operación cerrada parada · **+25.501 €** | 10/08 → 20/09 |
| las nueve por encima de 1,5 M | 5 sin libro · 3 carril · **1 cesta** | idem |
| las compras de la cesta | **10**: 9 abajo, 1 arriba | idem |
| ofertas de managers recibidas | **5**, todas del 12-13/08 · 0 aceptadas | fotos densas |
| ventas a managers | **3**, +7,5 % / +23,8 % / +32,0 % | 19/08 → 04/09 |
| ventas al Computer | **21**, +0,55 % de mediana, −900.517 € | idem |
| páginas de equipo en disco | **20**, con **513** jugadores y su probabilidad | hoy |
| el tablero de pronóstico | **64** objetivos, 13 páginas pedidas | hoy |
| el pronóstico casero | **84,9 %** sobre `n = 53` (27 titulares, 26 suplentes) | jornada 7 |

El casero se midió contra el veredicto de la fuente, no contra quién jugó de verdad.
Es coherencia con FutbolFantasy, no acierto sobre el campo — y eso es un techo, no una
garantía.
