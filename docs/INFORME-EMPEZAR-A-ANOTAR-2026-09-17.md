# Empezar a anotar — informe

**Rama:** `marcador/empezar-a-anotar`, desde `main` (con la fusión de hoy dentro).
**Push:** NO.

---

## Antes de nada: la foto que pediste no está

```
lo que dice el encargo   diagnostico/status.json = 2026-09-17T17:20:10
lo que hay en disco      diagnostico/status.json = 2026-09-17T07:30:55
el snapshot más nuevo    data/snapshot_20260913_171717.json  (del 13/09)
```

**No se ha dejado la foto fresca.** Lo comprobé en `meta.generated_at` antes de usar
nada, como manda la casa.

**He seguido con la de las 07:30**, y aquí está por qué es suficiente: **todos los
números que cita el encargo están en ella** — `observadas 8 · anotadas 0 ·
irrecuperables 8`, la ventana del 18/09 a las 19:30, `jornadas_fiables: 0`,
`jornadas_descartadas: 3` y `diferencia_media: 1.5`.

Y el libro sí está fresco: `data/intelligence/marcador.json` tiene la jornada 5125
**vista a las 16:20 de hoy**, así que las mediciones de los bloques 2 y 3 salen de
datos posteriores al despliegue.

---

## BLOQUE 1 — Qué tiene que pasar mañana

### La cadena entera, y es más frágil de lo que parece

```
1. cron-job.org dispara a las 20:07 (Madrid)          <- FUERA DE NUESTRO CONTROL
2. la verja pasa (152 guardias)                        <- si falla, el paso 5 NO corre
3. `v10_full_autonomous_live` no revienta              <- si revienta, el paso 5 NO corre
4. el snapshot trae el once completo (11)
5. `build_dashboard` llega a `anotar_el_once`
6. `target_matchday` = 7 y el calendario tiene su hora
7. la hora de la FOTO cae entre 19:30 y 21:00
```

### El número que más me preocupa: **una sola vuelta**

```
ventana          19:30 -> 21:00   (safety_deadline -> first_kickoff)  90 min
latido           minuto :07 de cada hora
vueltas dentro   20:07   <- UNA. Y ya está.
```

19:07 es antes de que abra. 21:07 es después del pitido. **Solo la vuelta de las 20:07
puede anotar el once de mañana.**

Y hay un detalle que la estrecha más: **la hora que se mira es la de la FOTO**, no el
reloj (doctrina 50). La foto se toma al principio de la vuelta y `build_dashboard`
corre al final —medido en la bitácora: unos **24 minutos** entre el arranque y la
publicación—. Así que la vuelta de las 19:07 tampoco sirve aunque su dashboard corra a
las 19:35: su foto es de las 19:07 y la puerta de la ventana la rechaza.

### Lo que puede fallar, una por una

```
QUÉ FALLA                          QUÉ PASA
──────────────────────────────────────────────────────────────────────────
el disparo de las 20:07 no llega   NO SE ANOTA. No hay segunda vuelta.
o llega con más de ~50 min de
retraso

la verja se pone roja              NO SE ANOTA. El paso «Build Sala de
                                   Operaciones telemetry» NO tiene
                                   `if: always()`: si la verja falla, el
                                   dashboard no corre.

el ciclo revienta                  NO SE ANOTA, por lo mismo.

el once no trae 11 jugadores       NO SE ANOTA, y bien: diez nombres no son
                                   un once. Se prefiere el hueco a una nota
                                   coja.

el calendario no tiene la          NO SE ANOTA: sin la hora del primer
jornada 7                          partido, anotar no prueba nada.
                                   (Hoy SÍ la tiene: comprobado.)

el `round_id` no ha saltado        SE ANOTA CON LA ETIQUETA EQUIVOCADA.
a la jornada 7                     Ver abajo.
```

### Y una que no estaba en tu lista: **el `round_id` no cuadra con la jornada**

```
congelado_este_ciclo.round_id   5125      <- «Jornada 6 (aplazada)», jugada 15-17/09
summary.target_matchday            7      <- la de mañana
```

El once se anota bajo `jornada_en_curso(snapshot)`, pero la ventana sale de
`target_matchday`. **Hoy esos dos números no son la misma jornada.** Si mañana a las
20:07 el round todavía no ha saltado, el once de la jornada 7 quedaría anotado bajo el
`round_id` de la 6 — una entrada que parece buena y etiqueta mal.

Lo más probable es que haya saltado (la 6 aplazada terminó el 17/09 y el siguiente
round se desbloquea hoy a las 23:00), pero **es una comprobación de treinta segundos
que merece la pena hacer mañana antes de las 20:00**, y no la puedo hacer yo desde
aquí.

### ¿Puede perderse el turno por lo que la vuelta esté haciendo? **No**

> **Anotar el once NO COMPITE con nada.**

`anotar_el_once` vive en el camino de **telemetría**, es observador puro y escribe su
propio fichero. No pasa por la elección de acción por prioridad ni gasta presupuesto de
escrituras contra Biwenger. Una vuelta ocupada en aceptar una oferta anota igual.

Está atado: `test_la_ventana_de_anotar_no_se_pierde` comprueba sobre la firma que
`hay_que_anotar` no recibe plan, acción, presupuesto ni prioridad. Si algún día alguien
se los pasa, la verja se pone roja.

**El turno se pierde por otra cosa:** porque no haya vuelta dentro de la ventana, o
porque la vuelta no llegue al dashboard.

### ¿Se puede anotar tarde? **No. El plazo es el pitido inicial.**

```
21:00:00  primer partido
21:00:01  `hay_que_anotar` devuelve False y no vuelve a intentarlo nunca
```

No hay anotación tardía, ni al día siguiente ni a los cinco minutos. La puerta 3 dice
que lo que haya puesto después del pitido «no es necesariamente lo que jugó», y tiene
razón: anotarlo daría una nota falsa que parece buena.

**El plazo real útil son los 90 minutos de la ventana**, y de esos solo se aprovecha la
vuelta de las 20:07, con unos **53 minutos** de margen hasta el pitido y unos **25**
después de descontar lo que tarda la vuelta en llegar al dashboard.

> **Lo que yo haría, y no hago porque me lo prohíbes:** poner `if: always()` en el paso
> del dashboard. Es una línea en `.github/workflows/bordalas-live.yml` y convierte «la
> verja falla → se pierde la jornada» en «la verja falla → se anota igual». Es tuya.

---

## BLOQUE 2 — La referencia. Tu sospecha era buena y el culpable es otro.

### Cómo se elige, exactamente

**No se elige por número.** Eso se arregló el 14/09 y el arreglo sigue puesto: se
ordena por la **hora del primer partido** (`orden_en_el_tiempo`), y la referencia es la
inmediatamente anterior en ese orden.

Así que cuando el motivo dice «restar los totales de la jornada 4904 a los de la 4902»,
**4904 no es posterior**: su único partido se jugó el **03/09**, diez días antes que los
de 4903. El `round_id` engaña, y el motor ya lo sabía.

### Pero el orden SÍ estaba mal, por otro motivo

```
`totales` NO son los puntos de esa jornada.
Son los puntos ACUMULADOS de la temporada TAL Y COMO ESTABAN
CUANDO LOS LEÍMOS — el campo `visto`.
```

Restar dos acumulados da lo que se sumó **entre las dos lecturas**. Esa cuenta solo
tiene sentido en el orden en que se leyó. Y leímos desordenado:

```
round   visto            primer partido
4899    20/08 20:55      19/08
4900    25/08 20:54      24/08
4937    28/08 18:32      22/08     <- se jugó ANTES que 4900 y se leyó DESPUÉS
4901    03/09 20:33
4904    04/09 20:34      03/09
4902    12/09 07:16
4903    16/09 07:19      13/09
5125    17/09 16:20
```

**4900 se leyó el 25/08 y 4937 el 28/08.** Ordenando por partido, 4937 quedaba de
referencia de 4900, y restarle a 4900 los totales de 4937 le quitaba tres días de
puntos: **el jugador 26271 salía a −7.** Ése era el número grande.

### Lo intenté, y lo he dejado fuera. Aquí está por qué.

Cambié la clave de orden a `visto`. **La verja se puso roja**: dos guardias del
encargo del 14/09 se cayeron, y tenían razón.

```
test_una_jornada_con_hueco_no_se_mide     FALLA
test_una_foto_a_cero_no_es_referencia     FALLA
```

**El motivo es real, no un detalle de montaje.** El emparejamiento pasaba a ir por
`visto`, pero el detector de huecos —`jornadas_en_medio`, que es lo que impide
publicar como «la jornada 4» una resta que cubre tres— **sigue mirando ventanas entre
horas de partido**. Con las dos claves cruzadas, la ventana del hueco puede salir
invertida y el detector deja de detectar.

Probé también a mover el hueco a la misma clave. Siguió rojo: las fixtures de esa
guardia ponen `visto` como `round_id % 28`, un valor de relleno que nadie leía, y con
mi cambio pasan a mandar. **Para que mi cambio pasara tendría que reescribir las
fixtures de otra guardia para que encajen conmigo**, y eso es exactamente al revés de
como se hace aquí.

### Y lo que decide: **rescatar no recupera ninguna nota**

Medido sobre el libro, antes de decidir nada:

```
                        pares   con puntos negativos
por hora de partido       4            4  (todos)
por `visto`               7            3
```

```
4900   ref pasaría de 4937 a 4899   ->  resta limpia   sería MEDIBLE
4901   ref pasaría de 4900 a 4937   ->  9983: 6 -> 5   sigue cayendo
4902   ref seguiría siendo 4904     ->  17482: 2 -> 0  sigue cayendo
```

> **Se rescataría UNA de las tres, y ninguna daría nota.** Para puntuar hace falta
> `cuadra` **y** `reconstruccion_completa`, y las ocho jornadas están en `sin_once`:
> el once de ninguna se anotó. 4900 pasaría de «no medible» a «medible» y se quedaría
> ahí.

**Así que el cambio vale cero notas y cuesta el detector de huecos, la víspera de la
primera anotación de verdad.** No lo subo. Es la misma regla que aplicaste ayer al
cable: prefiero no encender a encender a ciegas.

> **Tenías razón en la segunda mitad de tu bloque 2:** «si no se rescata ninguna,
> dilo: puede que estén perdidas por otro motivo y el orden solo sea el síntoma que se
> ve». **Es exactamente eso.** El orden está mal y no es lo que las mata. Lo que las
> mata es que nunca se anotó el once — que es lo que mañana empieza a arreglarse.

### Lo que sí dejo puesto

`test_la_referencia_es_anterior_en_el_tiempo`, la guardia que pediste, atando el
comportamiento **actual**: la referencia va antes **por fecha y no por número**. El
montaje lo pone difícil a propósito —los `round_id` en un orden y las fechas en otro—
y comprueba antes de nada que los dos órdenes no coincidan, porque si coincidieran la
guardia pasaría con las dos reglas y no probaría nada.

### Por qué caen las otras dos — y una regla que está mal

Los dos casos que quedan **no son de orden**:

```
9983  (Djené)   total 6 el 28/08  ->  5 el 03/09     Biwenger revisó a la baja
17482 (Dituro)  total 2 el 04/09  ->  0 el 12/09     Biwenger revisó a la baja
```

Y hay un tercero que destapa algo peor:

```
8376 (Zubeldia)  total 0 el 25/08  ->  -1 el 28/08
```

**Un total de temporada NEGATIVO.** En Biwenger un jugador puede puntuar en negativo
—roja, en propia—, así que la regla que descarta la jornada («un jugador no pierde
puntos») **es falsa**, y está costando jornadas.

**No la he tocado**: relajar una regla que descarta datos malos es peligroso y no
estaba en el encargo. Queda medida y dicha.

### Lo que haría en un encargo propio

Mover **las dos** claves a la vez —el orden y la ventana del hueco—, y actualizar las
fixtures del 14/09 con `visto` coherentes. Es un cambio de semántica del marcador y
merece su propia medición, no el hueco de otro encargo.

---

## BLOQUE 3 — El número que miente, quitado. Pero no como pedías.

```
ANTES   jornadas_fiables: 0 · jornadas_descartadas: 3 · diferencia_media: 1.5
AHORA   diferencia_media: 4.5 · diferencia_media_n: 1
```

**No lo he puesto a `null`, y te debo la explicación.**

### De dónde salía el 1,5

```
4903   diferencia_liga  0.0     media_rivales  0.0    ← DIEZ partidos, nuestro once sumó 60
4904   diferencia_liga  0.0     media_rivales  0.0
4899   diferencia_liga  4.5     media_rivales 24.5    ← Biwenger nos dio 29

media = (0.0 + 0.0 + 4.5) / 3 = 1.5
```

### Por qué no lo puse a `null`: una guardia del 21/08 dice lo contrario

Hice lo que pedías —sacar la media de `fiables`— y **la verja se puso roja**:

```
test_contra_la_liga_manda_el_dato_oficial     FALLA
    assert datos["resumen"]["diferencia_media"] == 9.0
    # "Y aunque la nota se descarte, la diferencia se conserva:
    #  no depende de que la reconstrucción sea buena."
```

Esa guardia lleva desde el 21/08 clavando justo lo contrario, **y tiene razón**: el
+4,5 de 4899 **es un hecho**. Sale de los puntos oficiales —Biwenger nos dio 29, los
rivales promediaron 24,5— y no depende de nuestra reconstrucción. Tirarlo porque el
once no cuadra sería tirar un dato bueno por un motivo que no le afecta.

### Lo que sí estaba podrido eran los otros dos

`4903` entraba con `media_rivales: 0,0`. Es una jornada de **diez partidos** en la que
nuestro once sumó **60 puntos**. Que los ocho managers de la liga puntúen exactamente
cero **no pasa**.

> **Ese cero no es una jornada mala: es una resta que no midió nada.** La clasificación
> de 4903 es idéntica a la de su referencia, así que el reparto oficial sale entero a
> cero — y el motor lo publicaba como si fuera un resultado.

**El 1,5 era un 4,5 hundido por dos ceros que no medían nada.**

### El arreglo, que satisface a las dos partes

Se excluye de la media la jornada **que no midió la liga** —reparto oficial entero a
cero—, no la que no cuadra. Cada fila publica `liga_medida`, y la media va **con su
`n`** (doctrina 55):

```
diferencia_media: 4.5   diferencia_media_n: 1
```

Así el hecho de 4899 sobrevive, los dos ceros falsos desaparecen, y la guardia del
21/08 sigue verde.

**Y no es un caso de laboratorio:** la guardia nueva lo reproduce exactamente —dos
jornadas que miden y una con la clasificación idéntica a la anterior— y sin el arreglo
la media cae de 9,0 a 6,0.

> **Si aun así quieres el `null` literal**, dímelo y lo pongo: es cambiar `medibles`
> por `fiables` en una línea y ajustar la guardia del 21/08. Pero entonces perdemos el
> único número verdadero que tenemos, y no me parece que sea lo que la doctrina 82
> quiere decir.

---

## Cuándo llegará la primera nota de verdad

```
18/09  20:07   se anota el once de la jornada 7        <- la única vuelta
18-20/09       se juega la jornada 7
09/10          se juega la jornada 8                   <- TRES SEMANAS DESPUÉS
```

Para puntuar una jornada hace falta una observación **posterior** que la cierre. La
jornada 8 no es hasta el **9 de octubre** — parón de selecciones por medio.

> **La primera nota de verdad no llega antes de finales de septiembre, y lo más probable
> es que sea a partir del 9 de octubre.** No depende de nada que se pueda acelerar desde
> el código: depende de que se juegue otra jornada.
>
> Y hay una condición más que ya no depende de mañana: que el once anotado **coincida**
> con el que Biwenger diga que jugó. Si no coincide, sale `cuadra: false` y vuelve a no
> haber nota — que es lo que les pasó a las ocho anteriores.

---

## Guardias

**+1 módulo, 5 guardias**, en `src/analysis/test_empezar_a_anotar_v1.py`, dada de alta
en la verja.

```
test_la_ventana_de_anotar_no_se_pierde
test_un_once_a_medias_no_se_anota
test_la_referencia_es_anterior_en_el_tiempo
test_una_jornada_que_no_midio_la_liga_no_entra_en_la_media
test_el_veredicto_dice_que_no_hay_media
```

**Las 13 inyecciones de fallo muerden, 13 de 13:**

```
MUERDE  ventana / no se anota nunca (turno perdido)
MUERDE  ventana / se anota SIEMPRE, también después del pitido
MUERDE  ventana / anotar empieza a depender del presupuesto
MUERDE  once a medias / se anota una alineación incompleta
MUERDE  referencia / vuelve a ordenar por `round_id`
MUERDE  referencia / la referencia es POSTERIOR
MUERDE  referencia / se pierde una jornada por el camino
MUERDE  referencia / coloca a ojo una jornada sin hora
MUERDE  media / el cero que no midió vuelve a contar
MUERDE  media / se publica sin su `n`
MUERDE  media / se pierde el hecho de la jornada que no cuadra
MUERDE  media / el marcador llega vacío (manos vacías)
MUERDE  veredicto / deja de decir que no hay media
```

Dos merecen una línea:

- **«el cero que no midió vuelve a contar»** es el caso de producción reproducido
  entero: sin el arreglo la media cae de 9,0 a 6,0.
- **«se pierde el hecho de la jornada que no cuadra»** existe para que mi arreglo no
  pueda convertirse en el que la guardia del 21/08 prohíbe. Las dos cosas tienen que
  ser verdad a la vez.

Ninguna lee estado de producción, sale a la red, mira el reloj del sistema ni escribe en
los libros. La hora entra por la puerta en todas.

---

## Lo que no hice, y por qué

- **Ni una escritura contra Biwenger.**
- **No toqué nada de lo que se encendió hoy**: ni el freno del once, ni los libros, ni
  las etiquetas de vía, ni el estimador.
- **No encendí nada**: ni la dirección como orden, ni el listón del carril, ni el cable,
  ni `ROSTER_FILL`.
- **No toqué `count_free_slots` ni `historical_max`.**
- **No moví ningún umbral.**
- **No inventé el once de ninguna jornada pasada.** Las ocho siguen irrecuperables.
- **No toqué `.github/workflows/bordalas-live.yml`**, aunque ahí está la línea que más
  protegería mañana (`if: always()` en el paso del dashboard). Queda dicha.
- **No relajé la regla de los puntos negativos**, aunque está medida como falsa.
- **No cambié la clave de orden del marcador**, aunque está medida como equivocada. Dos
  guardias del 14/09 se pusieron rojas y tenían razón: el detector de huecos sigue
  mirando ventanas entre horas de partido, y con las claves cruzadas deja de detectar.
  Además no recupera ni una nota. Queda para su propio encargo.
- **No reescribí las fixtures de `test_el_orden_del_tiempo_v1`** para que mi cambio
  pasara. Ajustar la guardia de otro encargo para que encaje con lo mío es al revés de
  como se hace aquí.
- **No empujé.**

### Lo que contradijo al encargo

1. **La foto de las 17:20 no estaba en disco.** Trabajé con la de las 07:30, que trae
   todos los números citados.
2. **La referencia NO se elige por número**: se elegía por hora de partido, y el arreglo
   del 14/09 sigue puesto. Tu sospecha apuntaba al sitio correcto por el motivo
   equivocado.
3. **Lo que estaba mal era otra cosa**: hay que ordenar por cuándo se LEYÓ, porque los
   totales son acumulados.
4. **No son tres jornadas las que caen por eso: son cuatro** (4937 también).
5. **Se rescataría una, no tres — y ninguna daría nota**, porque a las ocho les falta
   el once. Por eso el arreglo del orden **no entra**: vale cero notas y cuesta el
   detector de huecos.
6. **`diferencia_media` NO queda en `null`, queda en 4,5 con `n=1`.** Una guardia del
   21/08 pinta lo contrario de lo que pedías y tiene razón: el +4,5 es un hecho
   oficial. Lo podrido eran los dos ceros, que son restas que no midieron nada.
7. **Hay una regla falsa debajo**: un jugador SÍ puede perder puntos, y Zubeldia lo
   demuestra con un total de −1.
