# La regla 3: ¿veta a los que suben?

**Encargo:** «LA REGLA 3 VETA A LOS QUE SUBEN, Y DECIDE CON UN PULSO CONGELADO», 25/09/2026
**Rama:** `arreglo/la-regla-tres`, desde `main` en `e05ff8c0`
**Script:** `python scripts/la_regla_tres.py --rev HEAD`. Solo lee. Los catálogos `data/snapshot_*.json`
no están en git y se leen del disco.

## Veredicto: C, dejarla. Y no se construye nada.

**La medición contradice el encargo.** La regla no renuncia a 5,7 puntos. Ese número compara a los
vetados con el **mercado**, pero la regla nunca eligió entre un vetado y el mercado: elige entre
comprar al vetado o no comprarlo, y el dinero sigue disponible para los que **sí deja pasar**.
Comparada con esa alternativa, la regla apunta en la buena dirección a todos los plazos, en precio y
en puntos:

| vetados menos los que deja pasar, sobre el mercado de cada día | n vetados | jugadores | diferencia | IC 95 % por jugador |
|---|---|---|---|---|
| 3 días | 153 | 29 | −1,89 pp | −4,71 .. +1,06 |
| **7 días** | **135** | **29** | **−5,39 pp** | **−10,77 .. −0,07** |
| 14 días | 57 | 21 | −4,99 pp | −18,21 .. +8,03 |
| puntos por partido jugado, hasta el parón | 125 partidos | 32 | **4,05** frente a 4,70 (mercado 4,02) | — |

Es poco. Solo el de 7 días es claramente distinto de cero, y por los pelos. Además ha vetado **4
compras en 16 días**. No es una regla que proteja mucho, pero tampoco hay ningún número que diga que
cuesta dinero.

**Tampoco se puede arreglar el dato (B).** En los jugadores congelados, Comuniate congela **las tres
columnas a la vez**, así que no hay una columna buena al lado. Y la guardia que pedía el encargo,
«que no vete con un pulso muerto», soltaría precisamente a los vetados a los que peor les fue:

```
vetados con el pulso CONGELADO - los que pasan, 7 dias   -6,49 pp   IC 95 % -12,13 .. -0,67   n=101, 19 jugadores
vetados con el pulso VIVO      - los que pasan, 7 dias   -2,11 pp   IC 95 % -14,32 .. +7,96   n= 34, 10 jugadores
```

Por eso **no hay interruptor nuevo, ni guardia `test_la_regla_tres_no_decide_con_un_pulso_muerto`,
ni paso 0.** Construirlos sería construir en contra de la medición. Si decides B de todas formas, en
la sección 5 dejo cómo se haría.

**Con una advertencia que no hay que perder de vista (doctrina 95).** La regla acierta, pero en la
mayoría de sus vetos **no por el motivo que dice**. Su texto afirma «la demanda está desplomada», y en
3 de los 4 vetos reales esa «demanda» llevaba semanas sin cambiar. Lo que separa a sus vetados de sus
iguales no es la demanda de hoy. Por qué funciona entonces no lo sé.

---

## 1. Qué veta exactamente

### 1.1 La condición, con la línea

[market_rate_gate.py:258-282](src/analysis/market_rate_gate.py#L258-L282). Solo se llega a ella si
el precio sube: las reglas 1 y 2 ya han cortado los ritmos negativos y el cero.

```
ritmo > 0   y   trend_days >= 3   y   demand_net no es None   y   demand_net <= -20
```

| umbral | valor | de dónde sale | tipo |
|---|---|---|---|
| `ritmo > 0` | 0 | la regla 1 corta todo lo `< 0` y la 2 el `== 0` ([:80](src/analysis/market_rate_gate.py#L80)) | lógico, no es un número |
| `STREAK_DAYS_TO_CHECK_DEMAND` | 3 | «tras 1 día continúa el 92 %, tras 2 el 94 %, desde 3 baja al 74 %» ([:84-89](src/analysis/market_rate_gate.py#L84-L89)) | **medido**, en el estudio del 07/09, sobre la continuidad del precio y no sobre la demanda |
| `DEMAND_COLLAPSED` | −20 | «el mismo corte que usa el ojeador para publicar el pulso» ([:91-95](src/analysis/market_rate_gate.py#L91-L95)), o sea `PULSO_MINIMO = 20.0` ([comuniate_market.py:72](src/intelligence/scout/comuniate_market.py#L72)) | **heredado**, y el original está **puesto a ojo**: «por debajo, la mayoría están en el mismo montón» |

Hay además una consecuencia del umbral heredado: como el ojeador **solo publica el pulso si
`|compras − ventas| ≥ 20`**, cualquier pulso negativo que llegue a la regla ya es ≤ −20. **El corte
de −20 no filtra nada.** La regla veta con cualquier pulso negativo publicado.

### 1.2 Qué cierra cuando veta

En [acquisition_valuation.py:719-905](src/analysis/acquisition_valuation.py#L719-L905) cierra **dos
de las cuatro vías de compra**: la de especulación (`como_trading`) y la de tener (`como_tener`). La
de reventa al Computer solo la cierra el precio que cae, así que esta regla **no** la toca. La mejora
del once tampoco pasa por aquí.

### 1.3 Todo lo que decide con el pulso de Comuniate

| dónde | qué hace con él | ¿decide? |
|---|---|---|
| `market_rate_gate.evaluate`, regla 3 | veta | **SÍ. Es la única.** |
| `acquisition_valuation` | recibe el veto de arriba | sí, a través de la regla 3 |
| `market_rate_gate.build_market_rates` | lo copia en `demand_net` | no, solo lo transporta |
| `la_rendija` (:1178, :1306) | llama a `evaluate`, pero solo lee `rate_percent_per_day` y `trend_days` | **no** |
| `sales_analyzer` (:109) | `build_market_rates` para el ritmo | no lo lee |
| `el_pronostico_del_ojeador` | PULSO no bate al nulo y no pesa; además `ENCENDIDO = False` y nadie lo llama | no |
| `scout/view.py`, `libro_en_la_sombra`, `divergence.py` | pantalla y libros | no |

No hay más reglas en el mismo problema. Las reglas 1 y 2 del `market_rate_gate` no leen el pulso.

### 1.4 Cuántas compras ha vetado de verdad

El libro en la sombra apunta cada día lo que la compuerta cerró en el mercado del Computer con valor
antes del corte. Hay 16 fotos, del 10/09 al 25/09, con 268 casos: **264 los cerró la regla 2
(`PRECIO_CAYENDO`) y 4 la regla 3.**

| día | jugador | precio | valía antes | ritmo | racha | pulso | ¿congelado? |
|---|---|---|---|---|---|---|---|
| 12/09 | Starfelt | 2.150.000 | 2.182.733 (+1,52 %) | +2,79 %/día | 4 | −27 | llevaba 7 días igual y cambió a +20 el 15/09 |
| 18/09 | Deossa | 1.270.000 | 1.292.574 (+1,78 %) | +3,15 %/día | 3 | −33 | **sí**: −33 los 17 días que sale |
| 18/09 | José Salinas | 980.000 | 997.419 (+1,78 %) | +1,02 %/día | 10 | −77 | **sí**: −77 los 18 días que sale |
| 19/09 | Grimaldo | 4.880.000 | 4.965.644 (+1,75 %) | +1,43 %/día | 4 | −39 | **sí**: −39 los 20 días |

**Son 4 en 16 días, y 3 de ellos con un pulso muerto.** La sombra no cubre el 08 y el 09/09, que la
regla ya estaba viva, ni el mercado de los rivales (ese lo cierra el dueño, no la compuerta).

---

## 2. El contrafactual

### 2.1 Sobre todo el libro: el patrón que veta, contra lo que deja pasar

Sobre `divergence_ledger` (11.439 filas, del 05/09 al 25/09), el precio a N días sale de
`price_history`:

- **vetados**: ritmo > 0, racha ≥ 3 y pulso ≤ −20. Son 172 filas y 32 jugadores;
- **los que deja pasar**: ritmo > 0 y racha ≥ 3 sin pulso en contra. Son 2.374 filas y 269 jugadores.

| | n | subieron | mediana | media | peor |
|---|---|---|---|---|---|
| **3 días** vetados | 153 | 76,5 % | +3,65 % | +4,54 % | −16,27 % |
| los que deja pasar | 2.020 | 85,0 % | +2,92 % | +6,38 % | −18,18 % |
| mercado, mismos días | 8.708 | 28,3 % | −0,62 % | −0,46 % | −22,51 % |
| **7 días** vetados | 135 | 57,8 % | +2,29 % | +4,60 % | −21,47 % |
| los que deja pasar | 1.605 | 73,3 % | +4,77 % | +9,98 % | −27,94 % |
| mercado, mismos días | 6.526 | 28,6 % | −2,70 % | −0,39 % | −36,11 % |
| **14 días** vetados | 57 | 56,1 % | +2,59 % | +8,18 % | −24,07 % |
| los que deja pasar | 821 | 63,6 % | +6,25 % | +13,21 % | −38,83 % |
| mercado, mismos días | 2.712 | 29,0 % | −5,39 % | +0,57 % | −54,72 % |

Frente al mercado los vetados ganan: +7,23 pp a 7 días. **Pero frente a lo que la regla deja pasar
pierden a los tres plazos.** La tabla del veredicto tiene los intervalos. El efecto no se da la vuelta
con el plazo.

Los números de ayer, con los retornos del propio libro, eran +3,20 % frente a +4,57 %, 1,4 puntos.
Con `price_history` y el grupo de «los que pasan» definido igual que la regla (con ritmo > 0) sale
+2,29 % frente a +4,77 %. Si hago el remuestreo por jugador con los retornos del libro, la diferencia
a 7 días es −5,23 pp (IC −10,54 .. +0,02). La conclusión no cambia con la fuente.

### 2.2 En puntos

Los puntos se miden desde la foto del catálogo anterior a cada día (10/09, 12/09, 13/09 o 19/09)
hasta el cierre de la jornada 7 (`puntos_por_jornada`). No se juega otra vez hasta el 09/10. Cada
jugador cuenta una vez por foto de partida.

| | tramos | jugadores | partidos jugados | **puntos por partido jugado** | no jugó ninguno |
|---|---|---|---|---|---|
| vetados | 64 | 32 | 125 | **4,05** | 6,2 % |
| los que deja pasar | 620 | 268 | 1.115 | **4,70** | 10,5 % |
| todo el mercado | 2.173 | 546 | 2.856 | 4,02 | 32,8 % |

Las dos monedas dicen lo mismo: a los vetados les va algo peor que a sus iguales, en precio y en
puntos. **No hay un grupo de vetados que sirva para la liga y la regla esté tirando.** No es el 3, el 7
ni el 14 exactos que pedía el encargo: con los catálogos que hay, no se pueden cortar los puntos por
días.

### 2.3 Cuántos eran comprables

Los **4** de la sombra, por construcción: estaban en el mercado del Computer, sin puja nuestra y con
valor. La puja máxima de `bitacora_del_saldo` era de 16.962.316 el 18/09 y de 15.870.265 el 19/09, así
que los tres cabían. Del 12/09 no hay bitácora (empieza el 15/09). **De los otros 131 del patrón,
ninguno estaba a tiro**: la regla solo mira a los que salen en el tablero.

### 2.4 En euros: si en vez de vetarlos los hubiéramos comprado

Compra al precio de mercado del día y venta al precio de mercado N días después. **Es el tope**: la
puja real habría pagado hasta su «valía antes», entre un 1,5 % y un 1,8 % por encima.

| | compra | a 3 días | a 7 días | puntos del catálogo del 19/09 al cierre de la J7 |
|---|---|---|---|---|
| Starfelt 12/09 | 2.150.000 | +100.000 | −90.000 | 0, no jugó |
| Deossa 18/09 | 1.270.000 | +310.000 | **+1.030.000** | +5 |
| José Salinas 18/09 | 980.000 | −50.000 | −120.000 | +3 |
| Grimaldo 19/09 | 4.880.000 | +340.000 | aún no | +8 |
| **total** | | **+700.000** (n=4) | **+820.000** (n=3) | |
| con la prima de puja | | ≈ +540.000 | ≈ +750.000 | |

**Todo el dinero es Deossa.** Sin él, a 7 días sale −210.000. Con n=3, esto es una anécdota con
euros, no un contrafactual. Y apunta **en contra** de la regla, al revés que las 135 filas. Lo dejo
escrito tal cual: si Deossa se repite, se verá en la sombra. A 14 días no ha vencido ninguno.

---

## 3. El pulso congelado

### 3.1 Cuántos y desde cuándo

`scout_accuracy_ledger`, `COMUNIATE_PULSO`, 20 días (del 05/09 al 25/09), 254 jugadores:

| jugadores que salen | congelados (un solo valor en todo el periodo) |
|---|---|
| 2 días o más | 116 de 244 (47,5 %) |
| 5 días o más | 113 de 209 (54,1 %) |
| **10 días o más** | **80 de 125 (64,0 %)** |
| 15 días o más | 55 de 81 (67,9 %) |

De los 80 congelados de 10 días o más, 51 ya lo estaban el primer día del libro (05/09) y 21 desde el
15/09. **No es que la fuente se pare unos días.** Cada día cambia el pulso de entre 21 y 47 jugadores
(de 110 a 139), y el resto sigue igual. Y los que sí se mueven lo hacen **a escalones**: Starfelt tuvo
−27 del 05/09 al 14/09 y +20 del 15/09 al 25/09.

### 3.2 Es de la fuente, no del cacheo

- En 121 de los 126 congelados, el **movimiento en euros del mismo registro de Comuniate** sí cambia
  cada día. Los dos salen del mismo HTML en la misma petición, así que un caché nuestro los congelaría
  a los dos.
- En nuestro lado no hay caché HTTP: `fetch` ([common.py:120](src/intelligence/scout/common.py#L120))
  es un `session.get` a pelo. El informe se rehace cada 6 horas (`DEFAULT_TTL_SECONDS`) o al cruzar el
  reset, y `build_report` lo monta desde cero.
- **Y lo he preguntado a la fuente.** Hoy he leído una vez la misma URL pública que lee el ciclo
  (`biwenger_subidas_bajadas_carga.php`) y la he comparado con el informe del ojeador guardado del
  05/09. Robbie Ure: compras 66 %, ventas 5 %, uso 40 %, **idénticos 20 días después**, y el precio ha
  vuelto a bajar hoy 30.000 €. Pasa lo mismo con Konaté (27/6/26), Sangaré (2/62/63) y Grimaldo
  (8/47/48).

### 3.3 Qué es el campo, según Comuniate

Lo dice Comuniate en el atributo `title` de cada ficha:

> **Compras**: «Usuarios que han pujado por el jugador en las últimas 24 horas»
> **Ventas**: «Ligas en las que el jugador ha sido puesto a la venta»
> **Uso**: «Ligas que tienen al jugador en una plantilla»

La página explica que **el precio** se sincroniza cada noche, pero **no dice cada cuánto se
actualiza el pulso, ni sobre qué ligas o usuarios se calcula.** Por qué un «últimas 24 horas» sigue
igual durante 20 días **no se puede saber desde la web**, porque no lo explica. Tampoco se lo hemos
preguntado a Comuniate por otra vía (doctrina 103).

### 3.4 ¿Hay un campo al lado que sí se mueva?

**No.** Comparado el 05/09 con hoy, en 157 jugadores que salen las dos veces:

```
cambia compras   114      cambia ventas   114      cambia uso   121      las TRES iguales   34
```

Cuando se congela, se congelan las tres juntas. Lo único que se mueve en una ficha congelada es el
precio y su variación, que ya son la regla 1. `player-rank` es la posición en la lista. El
`ver_observaciones_mercado` del `onclick` abre otra petición, no viene en esta respuesta y no lo he
seguido. **No estamos leyendo la columna equivocada: no hay una columna buena.**

---

## 4. La propuesta: C, razonada con el número

| | qué haría falta | qué dice el número |
|---|---|---|
| **A**, apagarla | que cueste dinero frente a su alternativa | no cuesta: frente a lo que deja pasar, sus vetados pierden −1,9, −5,4 y −5,0 pp y puntúan 4,05 frente a 4,70. Los euros de los vetos reales dicen lo contrario, pero son n=3 y un solo jugador (Deossa) |
| **B**, arreglar el dato | que el pulso se pueda leer bien y entonces acierte | no se puede leer bien (§3.4). Y lo que pide la guardia, no vetar con un pulso muerto, suelta al grupo al que peor le fue: −6,49 pp (IC −12,13 .. −0,67) |
| **C**, dejarla | que con plazos y puntos proteja | protege poco y a los tres plazos apunta al mismo lado. Ha actuado 4 veces en 16 días |

**C.** Con dos notas para el dueño:

1. **El texto del veto miente en 3 de cada 4 casos.** Dice «la demanda está desplomada» y la demanda
   llevaba semanas quieta. Cambiarlo es tocar la regla, así que no lo he tocado.
2. **La sombra sigue apuntando.** Si en dos semanas los vetos reales se parecen más a Deossa que a
   las 135 filas, la pregunta vuelve con más `n`. El script ya está hecho para repetirla.

---

## 5. Si aun así se quiere B

No lo he construido porque el número va en contra. Si se decide, sería así:

- un interruptor `BORDALAS_REGLA_TRES_PULSO_VIVO`, apagado;
- `build_market_rates` recibiría, de `divergence_ledger`, cuántos días lleva el pulso de cada jugador
  sin cambiar;
- `evaluate` no vetaría por la regla 3 si ese número pasa de N;
- la guardia sería la que pide el encargo, con un caso de pulso vivo que siga vetando y una aserción
  de que el caso tiene al menos un pulso muerto, para que no pueda pasar con las manos vacías.

Coste: un fichero, una guardia y el paso 0. Y según esta medición, empeoraría la regla.

---

## 6. Lo que no hice, y por qué

- **Ni una escritura contra Biwenger.** Sí hice **una lectura a Comuniate**, la misma URL pública
  que lee el ciclo cada seis horas y la página que la contiene, porque el encargo pedía citar lo que
  dice la web. No va en ninguna guardia ni en el script.
- **No apagué ni cambié la regla 3**, ni su texto. **No toqué las reglas 1 y 2**, aunque la 2 es la
  que hace el 98,5 % de los cortes (264 de 268).
- **No hay interruptor nuevo, así que no hay paso 0 que correr.** Los cuatro de producción siguen
  como están.
- **No escribí `test_la_regla_tres_no_decide_con_un_pulso_muerto`.** Protegería un comportamiento
  que la medición desaconseja (§4).
- No toqué fórmulas, topes, el workflow ni la divergencia. No empujé.
- No miré lo apuntado del final del encargo (Ceballos reservado, `REROLL_COMPUTER_OFFER`, Rubén
  García, Larrubia y Giménez).

Lo que entra en el commit: este informe y `scripts/la_regla_tres.py`. Ningún libro.
