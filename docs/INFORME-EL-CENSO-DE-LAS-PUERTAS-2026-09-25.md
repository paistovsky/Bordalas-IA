# El censo de las puertas: ¿dónde mueren los candidatos?

**Encargo:** «EL CENSO DE LAS PUERTAS», 25/09/2026
**Rama:** `medir/el-censo-de-las-puertas`, desde `main` en `f82c858a`
**Script:** `python scripts/el_censo_de_las_puertas.py --rev HEAD`. Solo lee. Las fotos locales
(`diagnostico/`, `dashboard/data/`) y los catálogos `data/snapshot_*.json` se leen del disco.

## Veredicto

**La puerta que más mata es la regla 2, y no decide nada.** Detrás tiene otra que mata a los 264 que
corta, sin excepción: el rendimiento mínimo del 3 % que `optimal_bid` exige a toda especulación. Los
264 dejaban entre un 1,48 % y un 1,79 %.

**Lo que de verdad no puja es una vía entera.** La reventa al Computer vale el precio más la prima
del Computer (~1,8 %). Con un listón del 3 %, **esa vía no puede producir una puja nunca**, y es la
mejor vía de **47 de los 60 candidatos** del mercado del Computer en los días con foto. Las puertas
que se ven en el tablero (regla 2, presupuesto, disponibilidad, rendimiento) solo deciden **en qué
casilla** muere cada uno.

**Propuesta: no tocar la regla 2.** A los que corta les va peor que a los que deja pasar en precio y
en puntos, y abrirla no cambiaría ni una puja. **No construyo nada.** Lo que sí queda sobre la mesa es
una pregunta para el dueño: qué se quiere que haga la reventa al Computer, ya que con el 3 % no puede
hacer nada (§4).

---

## 1. El censo

### 1.1 El orden real de las puertas, y por qué la primera no es una fila

1. **La valoración**, `value_candidate` ([acquisition_valuation.py:356](src/analysis/acquisition_valuation.py#L356)).
   Primero el precio inválido. Después, **cinco vías en paralelo**: mejora del once, relleno de
   ficha, especulación, reventa al Computer y tener. Gana la de más valor, y el candidato solo muere
   aquí si mueren las cinco (`SIN_VALOR`, [:1157-1194](src/analysis/acquisition_valuation.py#L1157-L1194)).
   Como las vías son alternativas, una vía cortada no mata a nadie si otra da valor. Por eso en esta
   etapa cuento **la puerta decisiva**: si con la compuerta de ritmo abierta habría tenido valor
   (`market_gate.value_before > 0`), le mató la compuerta.
2. **La cadena del tablero** ([acquisition_board.py:1049-1085](src/analysis/acquisition_board.py#L1049-L1085)):
   contraoferta nuestra, puja nuestra fuera del Computer y estado del jugador. La decisión
   `NO_DISPONIBLE` **pisa** a un `SIN_VALOR` anterior. En el censo cuenta donde murió primero.
3. **El plan de puja**, `optimal_bid` ([rival_bid_model.py:1117](src/analysis/rival_bid_model.py#L1117)),
   en este orden: `NO_COMPENSA` → `SUPERA_PRESUPUESTO` → `SIN_MARGEN` → `EV_NEGATIVO` →
   `RENDIMIENTO_INSUFICIENTE` → `GANANCIA_INSUFICIENTE` → `PROBABILIDAD_INSUFICIENTE`.
4. Lo que pasa todo: `BID`.

Aparte, y al final del todo, **lo que vende un rival** se tapa con `MERCADO_DE_RIVAL`
([:1452](src/analysis/acquisition_board.py#L1452)): la compra a rivales está cerrada por orden del
dueño.

### 1.2 La tabla

Mercado del Computer. Tres días con foto: 14/09, 18/09 y 23/09, 20 candidatos cada uno, **n=60**.
Cada candidato cuenta en una sola puerta.

| puerta | fichero:línea | mueren | % | ejemplo |
|---|---|---|---|---|
| precio inválido | [acquisition_valuation.py:383](src/analysis/acquisition_valuation.py#L383) | 0 | 0,0 % | — |
| regla 1, sin ritmo | [market_rate_gate.py:202](src/analysis/market_rate_gate.py#L202) | 0 | 0,0 % | — |
| **regla 2, precio que baja o quieto** | [market_rate_gate.py:233-254](src/analysis/market_rate_gate.py#L233-L254) | **31** | **51,7 %** | Mayoral (14/09) |
| regla 3, racha con el pulso en contra | [market_rate_gate.py:258-282](src/analysis/market_rate_gate.py#L258-L282) | 0 | 0,0 % | — |
| valoración, sin valor ni con la compuerta abierta | [acquisition_valuation.py:1157-1194](src/analysis/acquisition_valuation.py#L1157-L1194) | 0 | 0,0 % | — |
| contraoferta / puja fuera del Computer | [acquisition_board.py:1051](src/analysis/acquisition_board.py#L1051), [:1075](src/analysis/acquisition_board.py#L1075) | 0 | 0,0 % | — |
| no disponible | [acquisition_board.py:1085](src/analysis/acquisition_board.py#L1085) | 2 | 3,3 % | Jon Martín (14/09) |
| `NO_COMPENSA` | [rival_bid_model.py:1164](src/analysis/rival_bid_model.py#L1164) | 7 | 11,7 % | Dmitrovic (18/09) |
| `SUPERA_PRESUPUESTO` | [rival_bid_model.py:1178](src/analysis/rival_bid_model.py#L1178) | 7 | 11,7 % | Cancelo (14/09) |
| `SIN_MARGEN`, `EV_NEGATIVO` | [:1264](src/analysis/rival_bid_model.py#L1264), [:1276](src/analysis/rival_bid_model.py#L1276) | 0 | 0,0 % | — |
| **`RENDIMIENTO_INSUFICIENTE`**, menos del 3 % | [rival_bid_model.py:1300](src/analysis/rival_bid_model.py#L1300) | **10** | **16,7 %** | Giménez (14/09), Ceballos (23/09) |
| `GANANCIA_INSUFICIENTE` | [rival_bid_model.py:1321](src/analysis/rival_bid_model.py#L1321) | 0 | 0,0 % | — |
| `PROBABILIDAD_INSUFICIENTE` | [rival_bid_model.py:1336](src/analysis/rival_bid_model.py#L1336) | 1 | 1,7 % | Osorio (18/09) |
| **pasan todas: `BID`** | — | **2** | **3,3 %** | Cabrera y Maffeo (18/09) |
| **total** | | **60** | 100 % | |

Los 2 que pasaron, los dos el 18/09, iban por la **vía del once** (Cabrera como mejora del once y
Maffeo como relleno de ficha). **El 14/09 y el 23/09 no pasó ninguno.**

**Rivales:** 95 filas en los tres días, todas `MERCADO_DE_RIVAL`. Con la puerta abierta habría pasado
**una**: Mario Martín el 23/09, por 1.398.722.

### 1.3 Por qué vía iba cada uno: la tabla que explica la de arriba

| vía que ganaba | dónde murió | n |
|---|---|---|
| **reventa al Computer** | regla 2 (con la compuerta abierta, su valor era precio + 1,75-1,81 %) | 31 |
| **reventa al Computer** | `RENDIMIENTO_INSUFICIENTE` (0,17-0,20 %) | 7 |
| **reventa al Computer** | `SUPERA_PRESUPUESTO` | 7 |
| **reventa al Computer** | no disponible | 2 |
| relleno de ficha | `NO_COMPENSA` | 6 |
| mejora del once | `NO_COMPENSA` | 1 |
| tener | `RENDIMIENTO_INSUFICIENTE` (0,40-2,40 %) | 3 |
| tener | `PROBABILIDAD_INSUFICIENTE` | 1 |
| mejora del once / relleno | **`BID`** | 2 |

**47 de 60** tenían como mejor vía la reventa al Computer, y esa vía no puede pasar el 3 %: su valor
es precio × (1 + prima) y su rendimiento no puede superar la prima. En los 31 de la regla 2 lo he
comprobado con `optimal_bid` de producción (§2.4). Los 7 de `SUPERA_PRESUPUESTO` y los 2 no
disponibles habrían caído igual dos puertas más abajo.

### 1.4 «Bloqueados por la regla del once: 25»

Ese contador suma **todas** las filas del tablero, rivales incluidos
([acquisition_board.py:1547-1557](src/analysis/acquisition_board.py#L1547-L1557)). En el mercado del
Computer, la regla del once **nunca aparece como la puerta decisiva**. Los 31 que mueren en la
valoración tenían cerradas **a la vez** la vía del once (17 por `NO_MEJORA_JERARQUIA`, 10 por
`SIN_PRONOSTICO` y 4 por `NO_MEJORA_TITULARIDAD`) y la de reventa (por la regla 2). Abrir la regla 2
no salva a ninguno. Qué pasaría abriendo la regla del once **no se puede saber desde la foto**, porque
esa valoración no se calcula. No es que sea cero: es que no se lo hemos preguntado al código
(doctrina 103).

### 1.5 El embudo que publica el panel está mal

Ya existía un censo: [embudo.py](src/analysis/embudo.py), que se publica en el panel como `funnel`.
En las mismas fotos dice:

| día | el panel dice «VIVE» | el tablero dice `biddable` |
|---|---|---|
| 14/09 | **49** de 64 | 0 |
| 18/09 | **40** de 54 | 2 |
| 23/09 | **19** de 37 | 0 |

Hay dos motivos. Mete a los de rivales en el censo. Y
[`DECISION_A_CAUSA`](src/analysis/embudo.py#L75-L84) no conoce `MERCADO_DE_RIVAL`,
`RENDIMIENTO_INSUFICIENTE` ni `PROBABILIDAD_INSUFICIENTE`, y todo lo que no conoce lo cuenta como
**VIVE**. Además, a todo `SIN_VALOR` lo llama «no mejora el once», y así esconde a la regla 2. **Es
la tabla que llevabas una semana queriendo ver, y ya existía, pero mentía.** No la he tocado: esto es
medir.

---

## 2. La regla 2

### 2.1 Qué pide, con la línea

[market_rate_gate.py:233-254](src/analysis/market_rate_gate.py#L233-L254):

```
ritmo < 0      ->  PRECIO_CAYENDO   «el precio viene bajando»
ritmo == 0     ->  PRECIO_CAYENDO   «el precio esta quieto»
```

`ritmo` es `consensus.mean_magnitude_percent` del ojeador, con signo
([:146-170](src/analysis/market_rate_gate.py#L146-L170)): lo que se movió ayer según FutbolFantasy,
Analítica y Comuniate-precio.

| umbral | valor | de dónde sale | tipo |
|---|---|---|---|
| `FALLING_RATE` | 0,0 (`ritmo < 0`) | «de los que bajaron ayer, el 90,7 % siguió bajando y solo el 0,5 % batió al mercado» ([:77-81](src/analysis/market_rate_gate.py#L77-L81)) | **medido**, estudio del 07/09. Ayer lo confirmé por otro lado: seguir la tendencia acierta el 82,9 % a 7 días (n=5.675) |
| `ritmo == 0` | 0 | «no hay ritmo que proyectar, y proyectar cero es no esperar ninguna revalorización» ([:246-256](src/analysis/market_rate_gate.py#L246-L256)) | **razonado, no medido** |

### 2.2 ¿Usa el pulso?

**No.** Solo mira el ritmo. De los 264 cortes, 35 tenían pulso apuntado y ninguno dependió de él. El
pulso muerto no afecta a esta regla.

### 2.3 ¿Hay algún umbral que no filtre nada?

**No en el sentido del −20 de la regla 3.** Los dos cortan: 169 por bajar y 95 por estar quietos.
Pero hay otras dos cosas:

- **La etiqueta miente en 95 de 264** (doctrina 87): a los quietos los llama `PRECIO_CAYENDO`, aunque
  el texto del motivo sí dice «quieto».
- **La regla entera es redundante** (§2.4): cada corte suyo lo haría también la puerta siguiente.
  Es el mismo problema que un umbral que no filtra, pero al revés: filtra, pero siempre llega antes
  que alguien que iba a filtrar lo mismo.

### 2.4 De los 264 cortes, ¿cuántos eran compras de verdad posibles? **Cero.**

Del libro en la sombra (16 fotos, del 10/09 al 25/09, 134 jugadores):

- **todos** con intención `SPECULATION`, y todos por la vía de reventa al Computer;
- margen con la compuerta abierta: mínimo +1,48 %, mediana +1,58 %, máximo +1,79 %. **Ninguno llega
  al 3 %**;
- corriendo `optimal_bid` **de producción** con la regla 2 abierta y el bolsillo infinito, con el
  modelo de puja de cada una de las tres fotos: **`RENDIMIENTO_INSUFICIENTE`: 264 de 264**, con los
  tres modelos.

No hace falta ni mirar si cabían en la caja ni si estaban disponibles. Con o sin regla 2, no se
compraba ninguno.

---

## 3. El contrafactual, con el control bueno

**El control** son los del **mismo mercado del Computer y el mismo día** a los que la compuerta deja
pasar (ritmo > 0 y sin la regla 3). Ahí es donde iría el dinero. El mercado lo he reconstruido para 13
días juntando catálogos, fotos y escaparate. En 3 de las 16 fotos de la sombra no hay mercado, y ahí
solo cuentan los cortados.

**Un aviso sobre el control.** Las fuentes no se ponen de acuerdo en qué día es cada mercado: el
catálogo del 19/09 coincide entero con el escaparate etiquetado el 20/09, y el Computer parece renovar
en dos tandas. Así que lo he corrido dos veces, con el mercado del día exacto y con el del día
anterior, el mismo y el siguiente. **La conclusión no cambia.** Doy las medianas: las medias de «los
que pasan» las inflan unos pocos cohetes.

### 3.1 En precio

| | cortados por la regla 2 | los que deja pasar (día exacto) | los que deja pasar (±1 día) |
|---|---|---|---|
| **3 días** | n=163 · 100 jug · subieron 5,5 % · **−4,12 %** | n=35 · 23 jug · 82,9 % · **+2,84 %** | n=52 · 25 jug · 80,8 % · +3,17 % |
| **7 días** | n=100 · 63 jug · 12,0 % · **−5,56 %** | n=17 · 13 jug · 76,5 % · **+5,11 %** | n=24 · 17 jug · 66,7 % · +5,08 % |
| **14 días** | n=32 · 16 jug · 18,8 % · **−5,58 %** | n=7 · 4 jug · 71,4 % · **+8,75 %** | n=7 · 4 jug · 71,4 % · +8,75 % |

Diferencia de medias, remuestreando por jugador (día exacto): **−14,8 pp** a 3 días (IC −26,7 .. −5,9),
**−28,2 pp** a 7 días (IC −70,0 .. −6,7) y **−19,9 pp** a 14 días (IC −50,4 .. −0,2). Los intervalos
son anchos por los cohetes del grupo que pasa, pero **ninguno toca el cero**. A 14 días, 4 jugadores
no son una muestra.

### 3.2 En puntos

Desde la foto del catálogo anterior a cada día hasta el cierre de la jornada 7:

| | tramos | jugadores | partidos | **puntos por partido jugado** | no jugó ninguno |
|---|---|---|---|---|---|
| cortados por la regla 2 | 145 | 123 | 136 | **3,50** | **44,8 %** |
| los que deja pasar | 29 | 25 | 41 | **5,15** | 20,7 % |

Las dos monedas dicen lo mismo: **a los que corta les va peor para la reventa y peor para la liga.**
Casi la mitad no jugó ni un partido en el tramo.

### 3.3 En euros

Comprando cada corte al precio de mercado de ese día y vendiéndolo N días después:

| | n | resultado | el que más pesa | sin él |
|---|---|---|---|---|
| 3 días | 211 | **−16.600.000 €** | Cancelo, −1.470.000 € | −15.130.000 € |
| 7 días | 148 | **−15.390.000 €** | Cancelo, −2.100.000 € | −13.290.000 € |
| 14 días | 32 | **−4.800.000 €** | Cancelo, −1.100.000 € | −3.700.000 € |

**No lo sostiene un solo jugador.** Quitando al que más pesa sigue en −15, −13 y −3,7 millones. Son
sumas de compras hipotéticas, y un mismo jugador cuenta cada día que salió: la regla corta 264 veces
a 134 jugadores. Y es un tope teórico: **el número real es 0 €**, porque ninguna de esas compras se
habría hecho (§2.4).

---

## 4. La propuesta

**Regla 2: no tocar nada.** Abrirla no cambia ni una puja: los 264 caerían en el 3 %. Y lo que corta
es peor que lo que deja pasar en las dos monedas y a los tres plazos. Además, es la puerta que
**explica** por qué no se compra lo que baja. Quitarla solo movería esos cadáveres a otra casilla del
censo.

**Lo que el censo sí pone delante, sin proponer nada construido.** La vía de reventa al Computer
(`computer_resale_value`) es la mejor vía de 47 de 60 candidatos, y con `RENDIMIENTO_MINIMO_DEL_CAPITAL
= 0,03` ([rival_bid_model.py:236](src/analysis/rival_bid_model.py#L236)) **no puede pujar por
construcción**: su prima medida está en ~1,8 %. O la vía sobra, o el listón no está pensado para ella.
Pero **eso es una decisión de negocio, no una medición**, y el encargo dice que no se toca ninguna
puerta. Antes de tocarla habría que medir si la reventa al Computer gana dinero en los días que sí
paga prima. Esa medición no está hecha.

**Y el embudo del panel** (§1.5) cuenta vivos que no existen. Arreglarlo es cambiar código, fuera de
este encargo, pero es lo más barato de todo lo que ha salido.

---

## 5. Lo que no hice, y por qué

- **Ni una escritura contra Biwenger, ni salir a la red.**
- **No toqué ninguna puerta**: ni las reglas 1, 2 y 3, ni la del once, ni el 3 %, ni el embudo.
- **Ningún interruptor.** Los cuatro de producción siguen como están. No hay paso 0 que correr.
- No toqué fórmulas, topes, el workflow ni la divergencia. No empujé.
- **El censo es de tres días** (14/09, 18/09 y 23/09), que son las fotos que hay. `libro_de_la_valoracion`
  tiene el 23, 24 y 25/09, pero solo con la decisión final: no dice qué puerta mató a un `SIN_VALOR`.
- Los puntos no se pueden cortar exactamente a 3, 7 y 14 días: los catálogos guardados son de fechas
  sueltas. Van desde la foto del catálogo anterior a cada día hasta el cierre de la jornada 7.
- No miré lo apuntado del final del encargo.

Lo que entra en el commit: este informe y `scripts/el_censo_de_las_puertas.py`. Ningún libro.
