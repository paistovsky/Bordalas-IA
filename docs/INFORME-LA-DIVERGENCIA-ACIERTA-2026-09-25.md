# Las 7.613 que nadie ha leído: ¿acierta la divergencia?

**Encargo:** «LAS 7.613 QUE NADIE HA LEÍDO», 25/09/2026
**Rama:** `medir/la-divergencia-acierta`, desde `main` en `92b65ae0` (el `main` de GitHub, con los
cuatro interruptores de producción en el workflow)
**Libros medidos:** los de `92b65ae0`, del 25/09 a las 16:12. Son los mismos que imprimía Pepe:
11.439 apuntadas, 7.613 cerradas y 595 divergentes, cuadran al dígito.
**Script:** `python scripts/la_divergencia_acierta.py --rev 92b65ae0`, que solo lee. Con otra revisión
los números cambian, porque el libro sigue llenándose.

## Veredicto

**No hay señal. Y lo que hay va al revés de lo que dice.**

A los que el libro marca «al alza» (el precio baja y la demanda sube) les va peor que al mercado y
peor que a los que también bajaron ayer:

| a 7 días | n | subieron | mediana |
|---|---|---|---|
| señalados al alza | 230 filas · 33 jugadores · 12 días | **9,1 %** | **−12,74 %** |
| el mercado, mismas fechas | los ~545 de cada uno de esos 12 días | 28,7 % | −2,54 % |
| los que también bajaron ayer, mismos días, sin divergencia | 2.823 | 10,7 % | −9,09 % |

La divergencia afirma que el precio se dará la vuelta y seguirá a la demanda. **A 7 días acierta el
20,2 % (n=396); seguir la tendencia acierta el 78,5 %** en esas mismas filas. Se aguanta en todos
los cortes que he probado: a 3 días, quitando la foto repetida, con una sola fila por jugador y solo
con los jugadores cuyo pulso sí cambia.

**Con un matiz que importa:** lo que se ha medido es el pulso de Comuniate **tal como lo leemos**,
y ese pulso está congelado en la mitad de los jugadores (sección 1.3). La conclusión es que **este
libro** no sirve. Si «la demanda» en general predice algo, no queda ni cerrado ni abierto: con este
dato no se puede contestar.

---

## 1. Qué apunta cada fila, y qué predice

### 1.1 La fila

[divergence.py:225-287](src/intelligence/scout/divergence.py#L225-L287). Se apunta **una fila por
jugador y día** (clave `player_id|fecha UTC`) para **todos** los jugadores del informe del ojeador,
unos 545 al día, sean divergentes o no:

- **precio**: `market_price`, el precio de Biwenger del catálogo;
- **«el precio»** de la divergencia: `price_change_percent`, lo que **se movió ayer**. Es el consenso
  de FutbolFantasy, Analítica y Comuniate
  ([report.py:206](src/intelligence/scout/report.py#L206)), una señal observada a 1 día;
- **«la demanda»**: `demand_net`, que sale de **una sola fuente**, Comuniate: `compras − ventas`
  ([comuniate_market.py:194-196](src/intelligence/scout/comuniate_market.py#L194-L196)). Solo existe
  si el jugador sale en el pulso de Comuniate y `|compras − ventas| ≥ 20`. Hay dato en **2.559 de
  11.439 filas**.

### 1.2 «El precio y la demanda en contra», con la línea

[divergence.py:192-222](src/intelligence/scout/divergence.py#L192-L222):

```
|cambio de ayer| >= 0,01 %   y   |demanda| >= 20
    cambio < 0  y  demanda > 0   ->  PRECIO_BAJA_DEMANDA_SUBE   (el «al alza»)
    cambio > 0  y  demanda < 0   ->  PRECIO_SUBE_DEMANDA_BAJA
```

### 1.3 Lo que predice, y cuándo se cierra

**Ninguna fila predice nada de forma explícita.** El propio módulo lo dice: «en el código no se
llama predicción en ningún sitio» ([divergence.py:21-23](src/intelligence/scout/divergence.py#L21-L23)).
Lo que tiene es una **hipótesis en la cabecera**: que la divergencia avisa del giro. Y cada fila
guarda su resultado:

- `price_after_3d` y `price_after_7d`: el precio de Biwenger en la primera vuelta en que la fila
  cumple 3 y 7 días. Las 7.613 cerraron **exactamente a los 7 días**;
- la fila pasa a `CLOSED` cuando tiene el precio a 7 días, y a `UNKNOWN` a los 21 días sin él;
- **es de dirección, no de tamaño.** No dice cuánto.

No es solo una foto, porque la foto lleva su resultado al lado, así que **sí se puede puntuar**. Lo
que se puntúa es lo que afirma cada tipo sin decirlo: «el precio seguirá a la demanda».

### 1.4 Tres cosas que no son lo que parecen

1. **Las 7.613 no son 7.613 predicciones.** Son **396 divergentes y 7.217 de control.** El grupo de
   control está bien pensado, pero la muestra de verdad son 396 filas.
2. **«595 jugadores con el precio y la demanda en contra» no son 595 jugadores de hoy.** Son las
   filas divergentes de 21 días, que corresponden a **78 jugadores distintos**. Hoy son **33**. La
   etiqueta de [autopilot.py:4292](src/autopilot.py#L4292) imprime `divergent_total` del estudio,
   que cuenta todo el libro. No lo he tocado.
3. **El pulso de Comuniate está congelado.** Robbie Ure tiene +61 los 21 días mientras su precio va
   de 3.960.000 a 2.620.000. Konaté tiene +21 los 21 días y Dolan +41 los 21 días. En el libro, **131
   de 249 jugadores con pulso tienen un único valor** en todo el periodo. Y el fallo es de la fuente,
   no del lector: en `scout_accuracy_ledger`, **en la misma respuesta de Comuniate**, el cambio de
   precio se mueve cada día y el pulso no (126 de 254 con un solo valor). El código lo describe como
   «% de usuarios que han pujado en 24 h», pero no se comporta como un dato de 24 h. **Qué es de
   verdad no lo sé, porque no se lo hemos preguntado a la página** (doctrina 103).

Hay además **dos fotos repetidas**: la del 06/09 es copia exacta de la del 05/09 y la del 25/09 de
la del 24/09 (545 de 545 filas cada una). Quitar la del 06/09 no cambia nada (§2.3).

---

## 2. ¿Acierta la dirección?

«Acierta» significa que el precio a N días se movió en la dirección que afirma el tipo.
**Control A**: el mercado entero **del mismo día** con la misma dirección, es decir, lo que acertaría
cualquiera. **Control B**: seguir la tendencia de ayer. En un divergente, B es por construcción lo
contrario de la divergencia.

### 2.1 Plazo 7 días (filas del 05/09 al 18/09)

Mercado entero: n=7.613, mediana **−2,56 %**, subieron el 28,8 %.

| | n | jugadores | acierta | control A | control B | mov. mediano | frente al mercado del día |
|---|---|---|---|---|---|---|---|
| **todas las divergentes** | **396** | 61 | **20,2 %** | 39,5 % | **78,5 %** | −6,93 % | −4,20 pp |
| precio baja, demanda sube | 230 | 33 | **9,1 %** | 28,7 % | 90,4 % | −12,74 % | −10,14 pp |
| precio sube, demanda baja | 166 | 30 | 35,5 % | 54,5 % | 62,0 % | +4,85 % | +7,43 pp |

Por tamaño del movimiento realizado:

| | n | acierta | control A | mov. mediano |
|---|---|---|---|---|
| grandes, > 5 % | 312 | **16,0 %** | 38,7 % | −10,00 % |
| medios, 1-5 % | 67 | 37,3 % | 40,7 % | −2,78 % |
| pequeños, < 1 % | 17 | 29,4 % | 49,7 % | 0,00 % |
| al alza, > 5 % | 191 | **5,8 %** | 28,7 % | −14,38 % |
| a la baja, > 5 % | 121 | 32,2 % | 54,5 % | +8,76 % |

**Donde está el dinero, que son los movimientos grandes, es donde más falla.**

### 2.2 Plazo 3 días (filas del 05/09 al 22/09)

Mercado entero: n=9.800, mediana −0,55 %.

| | n | acierta | control A | control B | mov. mediano |
|---|---|---|---|---|---|
| todas las divergentes | 499 | **9,4 %** | 37,1 % | 89,2 % | −3,17 % |
| precio baja, demanda sube | 306 | 4,2 % | 28,3 % | 94,1 % | −6,03 % |
| precio sube, demanda baja | 193 | 17,6 % | 51,0 % | 81,3 % | +3,67 % |
| al alza, > 5 % | 179 | **1,1 %** | 28,2 % | 98,9 % | −7,80 % |

Seguir la tendencia **en todo el libro** acierta el 82,9 % a 7 días (n=5.675) y el 89,5 % a 3 días
(n=7.263). Es el momento que ya se midió el 07/09.

### 2.3 Robustez, a 7 días

| precio baja, demanda sube | n | jugadores | acierta | frente al mercado |
|---|---|---|---|---|
| todas | 230 | 33 | 9,1 % | −10,14 pp |
| sin la foto repetida del 06/09 | 215 | 33 | 9,8 % | −10,14 pp |
| solo jugadores cuyo pulso **sí** cambia | 13 | 7 | 15,4 % | −12,16 pp |
| una fila por jugador (la primera) | 33 | 33 | 12,1 % | −9,33 pp |

Con el otro tipo pasa lo mismo: 35,1 %, 24,4 % y 30,0 %. Que el pulso esté congelado no explica el
fallo, porque los que tienen el pulso vivo fallan igual o más. **Pero n=13 y 7 jugadores no es una
muestra.** Lo apunto y no lo uso.

---

## 3. La cuenta de comprar

### 3.1 Si hubiéramos comprado a los señalados al alza

| a 7 días | n | subieron | mediana | peor | mejor |
|---|---|---|---|---|---|
| **señalados al alza** | 230 | **9,1 %** | **−12,74 %** | −33,48 % | +103,33 % |
| mercado, mismas fechas (ponderado por día) | los ~545 de esos 12 días | 28,7 % | −2,54 % | −36,11 % | +552,94 % |
| **bajaron ayer, mismos días, sin divergencia** | 2.823 | 10,7 % | **−9,09 %** | −36,11 % | +552,94 % |

| a 3 días | n | subieron | mediana | peor |
|---|---|---|---|---|
| señalados al alza | 306 | 4,2 % | −6,03 % | −22,51 % |
| mercado, mismas fechas (ponderado por día) | los ~545 de esos 16 días | 28,3 % | −0,52 % | −22,51 % |
| bajaron ayer, mismos días, sin divergencia | 3.766 | 5,2 % | −4,35 % | −20,47 % |

La comparación que decide es la tercera fila. Esos jugadores también bajaron ayer y solo les falta
la demanda a favor, **y les va mejor que a los señalados.** El pulso positivo no rescata a nadie.

Diferencia sobre la mediana del mercado de cada día, remuestreando **por jugador** (ocho jugadores
salen los doce días, y doce días de Konaté no son doce observaciones):

```
7 días   −7,79 pp   IC 95 %  −11,01 .. −3,42   n=230 filas, 33 jugadores, 12 días   baten al mercado 10,9 %
3 días   −5,34 pp   IC 95 %   −6,29 .. −4,39   n=306 filas, 41 jugadores, 16 días   baten al mercado  5,2 %
```

Los doce días a 7 días dan todos lo mismo: los señalados entre −9,3 % y −14,8 % y el mercado entre
−2,1 % y −3,1 %. No hay un solo día en que los señalados batan al mercado.

### 3.2 ¿Cuántos eran comprables?

Hay registro del mercado desde el 17/09 (`libro_del_escaparate`, las 20 fichas libres) y desde el
23/09 con los rivales (`libro_de_la_valoracion`). Cuento como «a la venta» al que salga en
cualquiera de los dos, que es la cota generosa. El presupuesto sale de la puja máxima de
`bitacora_del_saldo` de ese día.

```
17/09 – 25/09   177 señales al alza · 34 jugadores
                  8 a la venta ese día
                  6 dentro de la puja máxima
```

Son Sergio Martínez (22 y 23/09), Mangala (23 y 24/09), Tenaglia (24/09, de un rival) y Redondo
(25/09). Aubameyang y Tenaglia el 25/09 no cabían: la puja máxima era 2.208.580.

**Ninguno de los seis tiene todavía el precio a 7 días.** Los dos días con registro del mercado que
ya han cerrado (17 y 18/09) tienen **cero** comprables. Así que el cruce «comprable y además
acertó» es **n=0**. Aunque la señal funcionara, habría dado para un jugador a la semana.

---

## 4. Ceballos y Unai López

**Ceballos** (puja del dueño creada el 23/09 a las 09:39 UTC, ganada el 24/09; entrada 5.480.138
con el precio del libro en 4.200.000). **Nunca fue divergente**: el precio y el pulso fueron en la
misma dirección los 21 días. Lo que sí se ve es la rampa apagándose, y el pulso bajando con ella:

```
            precio      ayer       pulso   a 7 días
05/09    1.120.000   +22,32 %      90     +175,9 %
10/09    2.150.000   +13,02 %     100      +67,9 %
14/09    3.240.000    +4,63 %      93      +25,6 %
18/09    3.770.000    +4,24 %      95      +11,4 %
22/09    4.130.000    +1,45 %      40         —
23/09    4.160.000    +0,72 %      40         —      <- se crea la puja
24/09    4.200.000    +0,48 %      20         —      <- se gana
```

Ceballos es de los pocos con el pulso vivo. El día de la puja el pulso estaba en 40 y bajando desde
100, y la subida diaria en +0,72 % y bajando desde +22 %. **El libro no lo marcó como divergente
porque no lo era.** Que el pulso cayera junto a la rampa es un caso, n=1, y un número que encaja no
es una causa (doctrina 95).

**Unai López** (puja de Pepe creada el 23/09 a las 03:19 UTC, ganada a las 05:42; entrada 2.756.876).
**No tiene pulso ningún día**: no sale en el de Comuniate o no llega a ±20. El libro no dice nada de
él, ni a favor ni en contra. Estaba en el escaparate libre del 23/09, subiendo +0,36 % al día con 3
días de racha.

**El libro no vio venir a ninguno de los dos.** De uno no tenía datos, y el otro no cumplía la
condición.

---

## 5. Lo que queda apuntado, sin tocar

### 5.1 La regla 3 ya usa el patrón espejo, y está viva

El encargo dice «no se conecta la divergencia a ninguna decisión», y el libro efectivamente no lo
lee nadie. Pero **el patrón ya está conectado por otro lado**: la regla 3 de
[market_rate_gate.py:258-282](src/analysis/market_rate_gate.py#L258-L282), el AVISO (`RACHA_SIN_DEMANDA`),
**veta la compra especulativa** de quien lleva 3 días o más subiendo con el pulso ≤ −20. La usan
`acquisition_valuation` y `la_rendija`. Medido en este libro:

| a 7 días | n | subieron | mediana |
|---|---|---|---|
| sube con demanda en contra y racha ≥ 3 (lo que veta) | 135 | 58,5 % | **+3,20 %** |
| racha ≥ 3 sin demanda en contra, mismos días | 1.357 | 72,8 % | +4,57 % |
| mercado, mismas fechas | — | — | −2,54 % |

Los que veta **baten al mercado en unos 5,7 pp**, y les va unos 1,4 pp peor que a sus iguales. La
diferencia va en la dirección que dice la regla, pero es pequeña, con 29 jugadores y sin intervalo.
Y la demanda con la que decide es el mismo pulso congelado. **No lo he tocado.** Es la siguiente
pregunta si se quiere hacer.

### 5.2 Lo que habría que preguntar antes de dar la demanda por muerta

Qué publica de verdad Comuniate en `.pulso-compras` / `.pulso-ventas`, y por qué no cambia en 20
días para la mitad de los jugadores. Hasta que se pregunte, «la demanda no predice» y «este campo no
es la demanda» son igual de posibles (doctrina 103). Esa pregunta es la que deja pendiente la
búsqueda de fuera (Analítica Fantasy).

### 5.3 Del encargo

No he mirado nada de lo apuntado: Ceballos con `Reserved solvencia`, la prioridad de
`REROLL_COMPUTER_OFFER`, Rubén García reservado, ni Larrubia y Giménez. Sigue igual.

---

## 6. Lo que no hice, y por qué

- **Ni una escritura contra Biwenger, ni salir a la red.** El script lee los libros de git con
  `git show` o del disco.
- **No encendí ni apagué nada.** Los cuatro de producción (`JORNADAS_POR_SU_FECHA`,
  `REVENTA_SOLO_SI_JUEGA`, `EL_ONCE_UNA_VEZ`, `SOLVENCIA_POR_SU_PLAZO`) siguen como estaban. El
  encargo dice «cinco», pero el workflow tiene esos cuatro (más `BORDALAS_BID_SALT`, que es un
  secreto y no un interruptor).
- **No conecté la divergencia a nada**, y **no toqué la regla 3** aunque la medición le pone pegas.
- **No fui a Comuniate a preguntar qué es el pulso.** Sería salir a la red en un encargo de solo
  medir.
- **No arreglé la etiqueta «595 jugadores»** ni las fotos repetidas. Son cambios de código y el
  encargo es solo medir.
- **No toqué fórmulas, topes ni el workflow.**
- **No empujé.**
- **Sobre el control A del encargo** (−6,68 % a 7 días, del 23/09): no lo he reproducido. Mi mercado
  es el de este libro en las mismas fechas: −2,56 % de mediana, n=7.613, filas del 05/09 al 18/09.
  Son poblaciones o periodos distintos, y he usado el mío para que la comparación sea del mismo
  periodo (doctrina 54).

Lo que entra en el commit: este informe y `scripts/la_divergencia_acierta.py`. Ningún libro.
