# La dirección del precio — informe

**Foto:** `diagnostico/status.json`, **`meta.generated_at` = 2026-09-17T07:30:55**, con
`encoding="utf-8"`.

**Rama:** `carril/la-direccion` (desde `motor/el-carry`)
**Verja:** **152/152 en verde, exit 0**, corrida a fichero
**Push:** NO. Se sube el arreglo del bloque 0. **`la_direccion.ENCENDIDO = False`.**

---

## La respuesta corta

> **El filtro es acertado y NO es la mejora.** Los 19 puntos son reales y aguantan.
> Pero puesto sobre lo que hicimos, **nos habría hecho pujar menos: 18 pujas en vez de
> 37.** Y el problema medido es que aparecemos poco.
>
> Lo digo con tus palabras: **si el filtro nos habría hecho pujar menos, es un fallo y
> no una mejora.**
>
> Lo que sí hace es otra cosa, y es grande: **con el 40 % del capital se quedaba el
> 79 % del resultado.** El filtro no es para pujar mejor. Es para dejar de inmovilizar
> dinero en operaciones que no rinden.

Y una corrección a mí mismo: ayer dije que la verja tocaba **cinco** libros. **Escribe
en nueve.** Medí mirando qué ficheros cambiaban de contenido, y eso es un suelo: esta
vuelta, de los nueve que escribió solo **seis** cambiaron de contenido. Los otros tres
se reescribieron iguales y no se ven en un `git status`.

---

## BLOQUE 0 — Los dos sueltos SÍ estaban en la lista. Faltaban OCHO.

### Tu pregunta 1: ¿están en la lista blanca?

**Sí, los dos.** `pujas_bajo_precio.jsonl` y `libro_de_renovaciones.jsonl` estaban en
`LIBROS` y el `.gitignore` los deja pasar. **No se están perdiendo.**

Lo que pasa es otra cosa: **producción no los ha escrito nunca**. Los que hay en tu
disco son del **10/09**, de una vuelta local tuya —11 renovaciones reales (Dituro,
Jonny, Jutglà…) y una puja bajo precio por Aubameyang—. Por eso están sin seguir: no
hay nada que guardar en el runner, y lo que hay aquí es tuyo.

**No los he subido, y te lo digo antes de decidir nada.** Si los commiteo, la vuelta
siguiente se los lleva y pasan a ser el libro de producción, con once líneas del 10/09
dentro. Eso es una decisión tuya, no mía.

### Tu pregunta 2: la lista entera contra lo que el código escribe

Medido **del AST**, no de la memoria — y no a mano, después de lo del martes con los
lectores del `intent`.

Y el primer detector estaba roto: **encontraba 2 de los 16 libros.** Porque en esta
casa ningún libro se escribe con su ruta al lado del `write`: van por
`_apendar(fila, ruta, ...)`, y la ruta llega como argumento, a veces tres saltos más
abajo. Hubo que seguirla a través de las funciones. Luego faltaban cuatro más —el
marcador, el histórico, los onces y el de posiciones— porque se escriben en atómico,
`X.with_suffix(".tmp")` y `os.replace`.

Con el detector arreglado:

```
ficheros que el código escribe bajo data/     47
clasificados como LIBRO                       24     (eran 16)
clasificados como cache, con su motivo        25
SIN CLASIFICAR                                 0
```

**OCHO libros de verdad estaban fuera de la lista.** Y como el `.gitignore` se genera
de esa misma lista, estaban **tapados**: vivían en la caché del runner y morían con
ella a los siete días sin uso. El mismo agujero que se comió `data/solvency` la semana
pasada.

```
data/trading/libro_de_viajes.jsonl            de aquí sale el COSTE de cada viaje,
                                              que es lo que fija el suelo de cobro
data/trading/libro_de_salidas.jsonl           cada oferta cobrada al cerrar un viaje
data/trading/libro_de_la_ventana.jsonl        si la ventana del reset se abrió
data/trading/libro_de_escaparate.jsonl        qué se puso a la venta al comprarlo
data/intelligence/scout_accuracy_ledger.json  si el ojeador acierta      172 líneas
data/intelligence/source_accuracy_ledger.json el Brier de cada fuente    649 líneas
data/intelligence/rejection_ledger.json       qué pasó con lo que NO compramos
data/autopilot/computer_offer_history.json    cuántas veces se repite una oferta
```

Tres cosas que duelen de esa lista:

1. **`libro_de_viajes.jsonl` es el que le da el coste a `que_cobrar`.** Sin él, la
   prohibición 0 dice NO VENDER. Es el libro del que depende que el carril pueda
   cerrar, y no se estaba guardando.
2. **`scout_accuracy_ledger.json` es el libro que decide si el ojeador vale.** El
   bloque 2 de este encargo conecta el ojeador, y el libro que mide si acierta era uno
   de los que morían con el runner. **649 y 172 líneas en este disco, cero en git.**
3. **Hay dos libros a una letra**: `libro_de_escaparate.jsonl` (el del carril, que ya
   existía) y `libro_del_escaparate.jsonl` (los veinte del Computer, que nació ayer).
   Queda dicho en la ficha de cada uno.

**Nadie se equivocó al clasificarlos: nadie tuvo que clasificarlos.** Un fichero nuevo
aparecía, el `.gitignore` lo tapaba y no pasaba nada. Por eso la guardia no exige
«está en `LIBROS`» sino **«alguien ha dicho cuál de las dos cosas es»**, y hay una
segunda lista, `NO_SON_LIBROS`, con los 25 caches y el motivo de cada uno. Un escritor
nuevo pone la verja en rojo hasta que alguien decida.

### Tu pregunta 3: la bitácora. Por qué miente.

**Causa, medida ejecutando la verja entera con las escrituras interceptadas** (nada
tocó el disco):

```
`test_el_estado_del_dashboard_se_construye_entero`, dentro de
`test_el_ciclo_publica_v1`, monta el dashboard ENTERO con la foto que haya
en disco. `build_state` llama en dashboard_state.py:4917 a

    apuntar_lectura(balance=..., maximum_bid=..., ...)     <- SIN `ruta`

así que la línea cae en el libro DE VERDAD, con el saldo de esa foto y la
hora de AHORA.
```

Es **la misma guardia y la misma forma** que el libro del escaparate que arreglé ayer.

**En producción la foto que hay en disco cuando corre la verja es la de la vuelta
anterior** —el ciclo escribe la nueva después—, así que **cada vuelta deja dos
líneas**: la de la verja con el saldo viejo y la del ciclo con el bueno. Se ve en el
libro de producción:

```
23:12:50   -1.044.308     <- verja, saldo de la vuelta anterior
23:25:29   +1.183.292     <- ciclo, el bueno
00:10:57   +1.183.292     <- verja, ya es el viejo
00:22:46   +1.183.292     <- ciclo
01:10:49   +1.183.292     <- verja
01:19:48   +1.339.492     <- ciclo, el bueno

hueco mediano entre líneas   24,5 min     y el ciclo corre una vez por hora
```

**Aproximadamente la mitad de las 66 líneas de la bitácora de producción las escribe la
verja.** En mi disco son 11 con el saldo del 13/09 porque la foto más nueva que tengo
aquí es `snapshot_20260913_171717.json`.

### ¿Contamina algo de lo medido esta semana? **No, y por un pelo**

La bitácora se usó en un sitio: la fórmula `maximumBid = saldo + plantilla/4 −
comprometido`, **18 de 18 al euro**.

Esa cuenta **deduplica por (saldo, plantilla, comprometido) e ignora el `at`**. Y una
línea de la verja lleva una terna **internamente consistente** —es de una foto real,
solo que vieja—, así que es una observación válida de la fórmula. **El 18/18 se
sostiene.**

> **Lo que sí está contaminado es el TIEMPO.** La bitácora no es hoy un registro fiel
> de cómo evolucionó el saldo: la mitad de sus líneas repiten el punto anterior con
> hora nueva. Cualquier medición futura de *velocidad* —cuánto cambia el saldo por
> hora, cuánto tarda en recuperarse— saldría mal. **Y no la he arreglado, porque
> pediste saber antes el porqué.**

**El arreglo, cuando lo autorices, es el mismo de ayer**: `apuntar_lectura` tiene que
recibir el sello de la foto y negarse si no es de esta vuelta.

---

## BLOQUE 1 — El rendimiento, partido por dirección y plazo

`price_history.json`, sello **16/09 18:23**, ventana 17/08–17/09, **617 jugadores** con
serie diaria. El día de mercado corta en el **reset**, no a medianoche. La dirección es
la de **la víspera**: lo único que se sabe en el momento de pujar.

```
plazo              SUBIA                 PLANO                BAJABA
  1 d      +1,235 % (n=4120)     0,000 % (n=4865)    -1,389 % (n=6268)
  3 d      +3,356 % (n=3806)     0,000 % (n=4489)    -4,032 % (n=5739)
  5 d      +4,911 % (n=3536)     0,000 % (n=4030)    -6,502 % (n=5252)
 10 d      +7,430 % (n=3057)     0,000 % (n=3400)   -11,711 % (n=4500)
 15 d      +6,418 % (n=2281)     0,000 % (n=2458)   -15,152 % (n=3281)

hueco SUBIA - BAJABA:   1 d +2,62 pp    3 d +7,39 pp    5 d +11,41 pp
                       10 d +19,14 pp   15 d +21,57 pp
```

**El `n` es de observaciones, no de jugadores, y las ventanas se solapan** — la de un
jugador el martes y la del miércoles comparten nueve días. Dice cuánta materia hay, no
cuántas pruebas independientes. Por jugador distinto son 617.

### El pico de cada columna, y dónde satura

```
SUBIA    a 10 días   +7,430 %      y a 15 baja a +6,418 %   <- SATURA Y DEVUELVE
PLANO    a  1 día     0,000 %      plano en todos los plazos
BAJABA   a  1 día    -1,389 %      no gira: sigue cayendo hasta -15,152 % a 15 d
```

> **El plazo de salida son 10 días**, y no es un redondeo: es donde la curva del que
> sube gira. Está atado con guardia — `PLAZO_DE_SALIDA` se vuelve a derivar de la tabla
> en cada vuelta de la verja, y si alguien lo mueve a un plazo que la medición no
> respalde, muerde.
>
> **Del que baja no se sale esperando.** Su curva no tiene pico dentro de la ventana.

### Sí, cambia con la fuerza — y mucho más de lo que suponías

```
la víspera subió     rend. a 10 d    n obs   jugadores   precio mediano
0-1 %                    +0,889 %     1175         216       4.420.000
1-2 %                    +7,745 %      658         167       2.765.000
2-4 %                   +15,410 %      465         140       1.930.000
más de 4 %              +44,444 %      759         119         880.000
```

**No es que sean baratos.** Los que suben fuerte cuestan 880.000 de mediana contra
4.420.000, así que repetí la cuenta dentro de la misma franja, de 1 a 6 millones:

```
0-1 %  +0,996 %     1-2 %  +6,962 %     2-4 % +14,050 %     +4 % +36,667 %
```

**El orden aguanta entero.** Un +0,3 % diario y un +4 % diario no son el mismo negocio:
son cuarenta puntos de diferencia. Está en el módulo como `FUERZA`, **sin usar**,
porque ordenar candidatos no estaba en el encargo — pero el día que se ordenen, es esto
y no el precio lo que los ordena.

### La pregunta incómoda: **sí, los 19 puntos aguantan**

Tenías razón en que va en contra: el Computer paga peor por los que suben.

```
prima del Computer AL VENDER (censo A, 90 ofertas vivas 12/08-13/09,
sin sesgo de aceptación):
    SUBIA   +0,0299 %  (n=52)    PLANO  +0,5758 %  (n=11)    BAJABA +1,8446 %  (n=27)
```

Pero **la prima se cobra al salir, y a los diez días el jugador ya no sale como
entró**:

```
entró SUBIA   -> sale  SUBIA 52,3 %   PLANO  8,9 %   BAJABA 38,7 %   (n=2919)
entró BAJABA  -> sale  SUBIA 21,1 %   PLANO 12,4 %   BAJABA 66,5 %   (n=4262)
```

```
ENTRANDO AL QUE SUBÍA          ENTRANDO AL QUE BAJABA
 deriva      +7,430 %           deriva     -11,711 %
 prima       +0,781 %           prima       +1,304 %
 NETO        +8,211 %           NETO       -10,407 %

 hueco bruto  +19,14 pp         hueco NETO  +18,62 pp
```

> **El hueco no se cierra: la prima se come 0,52 de 19,14 puntos.** El que baja cobra
> medio punto más de prima, y pierde once de precio.

Nota: los números **+0,58 % / +3,85 %** de tu encargo no están en ningún informe de esta
semana y no he podido reproducirlos; los que uso son los del censo A de «la plaza y el
cable», que sí están medidos y llevan su `n`.

---

## BLOQUE 2 — El filtro, apagado

```
ENCENDIDO = False
el carril compra SOLO a los que el ojeador dice que SUBEN,
y los tiene 10 días — no hasta el día siguiente.
```

**Por qué la dirección y no la magnitud:** doctrina 57. La magnitud del ojeador es un
eco de `price_increment` y por eso lleva una semana sin conectarse. La dirección no lo
es: **persiste al 88,3 % (n=16.873)**, y es lo único que se sabe del futuro de un
precio al pujar. **No entra ni un euro del ojeador en ninguna cuenta.**

```
el ojeador dice UP      -> PUJA
el ojeador dice DOWN    -> NO PUJA   (-11,711 % a 10 días, n=4500)
el ojeador dice FLAT    -> NO PUJA   (0,000 % a 10 días, no paga ni la prima)
el ojeador no se moja   -> NO PUJA   SIN PRONÓSTICO
no hay pronóstico       -> NO PUJA   SIN PRONÓSTICO
```

**«SIN PRONÓSTICO» es una respuesta** (doctrina 24): no saber si va a subir no es saber
que va a subir, y el motivo lo dice con esas palabras.

**Ningún umbral se mueve.** El filtro dice qué entra, no cuánto se paga — el precio lo
sigue poniendo `regla_de_compra` con su tope. Hay guardia para eso: si `puede_comprar`
empieza a devolver un importe, la verja se pone roja.

---

## BLOQUE 3 — Qué habría cambiado

Sobre las **182 subastas** de producción (`origin/main`, sello 17/09 07:23). Entre
paréntesis, lo que da el libro de esta rama, un turno por detrás: **175**, y las
mismas conclusiones.

```
víspera SUBIA     77  (42,3 %)        pujamos en 37 de 182  (20 %)
víspera PLANO     18  ( 9,9 %)        ganamos      26       (70 %)
víspera BAJABA    31  (17,0 %)
víspera sin dato  56  (30,8 %)
```

Esos 56 sin dato **son un agujero del histórico, no del filtro**: `price_history`
empieza el 17/08 y la liga arrancó el 09/08. En producción el ojeador habla de los
veinte de hoy.

### 1. ¿En cuántas habríamos pujado?

```
manager                  pujó  ganó  conv   % subastas   y con el filtro
Pollo17                   109    61   56 %       60 %          34 %
Luismi_Haz                 89    48   54 %       49 %          27 %
Manzagool                  41    24   59 %       23 %           9 %
Pepe Bordalás              37    26   70 %       20 %          10 %
```

**El filtro deja pasar 77 de 182 (42 %).** Pero de **nuestras 37 pujas quedan 18.**

### 2. ¿Cuántas buenas nos habría quitado? **19 de las 26 que ganamos**

```
2026-08-10  id 26271   24.897.600   sin dato      2026-09-12  id 12087    240.601  PLANO
2026-08-10  id 1599     1.570.000   sin dato      2026-09-13  id 1602   2.873.240  BAJABA
2026-08-10  id 38194    1.629.832   sin dato      2026-09-13  id 37499  2.760.000  BAJABA
2026-08-17  id 37525      504.000   sin dato      2026-09-15  id 41560    150.376  PLANO
2026-08-18  id 38072    1.200.001   BAJABA        2026-09-15  id 10040  1.604.001  BAJABA
2026-08-19  id 8376     2.068.001   BAJABA        2026-09-15  id 30507    150.376  PLANO
2026-08-20  id 2169     2.288.001   BAJABA        2026-09-15  id 39736    150.376  PLANO
2026-08-20  id 9983     2.409.001   BAJABA        2026-09-17  id 15289    421.000  PLANO
2026-08-22  id 14800    2.079.001   BAJABA        2026-09-17  id 42119  1.292.476  BAJABA
2026-09-12  id 30334      150.376   PLANO
```

### 3. Y el neto — **aquí está lo que el recuento no dice**

Una ganada no es una buena operación: es una operación. Lo que hizo el precio después:

```
                                        n    capital        resultado   por euro
LAS QUE EL FILTRO DEJA  (subía)         7   12.651.438        +419.412    +3,32 %
LAS QUE EL FILTRO QUITA (plana/baja)   14   18.627.351        +111.760    +0,60 %

el filtro se queda con el 40 % del capital y con el 79 % del resultado
y LIBERA 18.627.351 EUR que rindieron +0,60 %
```

(Las cuatro de agosto sin histórico no se pueden juzgar y quedan fuera de esta cuenta.)

En euros absolutos **ganaríamos menos**: +419.412 en vez de +531.173, unos **112.000 €
menos**. Pero con **18,6 millones libres** que estaban dando un 0,60 %.

---

## Si el filtro nos haría pujar menos — **sí, y lo digo con esas palabras**

> **EL FILTRO NOS HARÍA PUJAR MENOS: 18 pujas en vez de 37.**
>
> Y por la regla que pusiste en el encargo, **eso es un fallo y no una mejora**. El
> problema medido es que aparecemos poco: convertimos el 70 %, el mejor de los ocho,
> y pujamos en el 20 % contra el 60 % de Pollo.

**Un filtro no hace aparecer a nadie. Solo quita.**

### Lo que falta, y es la otra mitad

```
subastas que el filtro deja pasar        77
...en las que aparecimos                 18
...en las que NO aparecimos              59      <- el hueco de verdad

de esas 59, 55 medibles:  mediana +5,86 %   subieron 37 de 55 (67 %)
                          costaban 237.358.234
                          habrían dado +15.351.849   (+6,47 % por euro)
```

**El filtro acierta en QUIÉN y no hace nada con CUÁNTOS.** Los 237 millones no caben en
nuestro bolsillo, pero el número que importa es el otro: **había 59 subastas de las
buenas en las que no estábamos.**

> **Mi lectura: este filtro no se enciende solo.** Encendido tal cual, sobre el
> comportamiento de hoy, es una resta. Vale la pena cuando vaya junto con lo que nos
> haga aparecer — y eso es lo que mide el bloque 3 del escaparate, no esto.
>
> Lo que sí haría ya, si me lo pides: **ponerlo en `as_computer_resale` como criterio
> de ORDEN, no de veto.** Que entre primero el que sube, y dentro de los que suben,
> el que subió más fuerte. Eso no quita ni una puja y se queda con los 19 puntos.

---

## Guardias

**+9 guardias**, en `src/analysis/test_la_direccion_v1.py`, dada de alta en
`scripts/run_validation_gate.py`.

```
test_todo_libro_escrito_esta_en_la_lista
test_el_gitignore_no_tapa_un_libro
test_ningun_libro_se_clasifico_dos_veces
test_el_rendimiento_lleva_direccion_y_plazo
test_los_diecinueve_puntos_aguantan_la_prima_del_computer
test_el_carril_no_compra_a_los_que_bajan
test_el_filtro_no_toca_ningun_umbral
test_el_plazo_de_salida_sale_de_donde_gira_la_curva
test_esto_sigue_apagado
```

**Las 21 inyecciones de fallo muerden, 21 de 21:**

```
MUERDE  censo / un libro sale de la lista y nadie lo reclasifica
MUERDE  censo / el detector devuelve vacío (manos vacías)
MUERDE  censo / el detector se queda corto (2 de 47)
MUERDE  censo / un fichero clasificado como libro Y como cache
MUERDE  censo / una exclusión sin motivo
MUERDE  rendimiento / la tabla llega vacía (manos vacías)
MUERDE  rendimiento / una celda sin su `n`
MUERDE  rendimiento / falta una celda de la partición
MUERDE  rendimiento / las dos direcciones cambiadas de sitio
MUERDE  rendimiento / interpola un plazo que no se midió
MUERDE  prima / se cobra la dirección de ENTRADA, no la de salida
MUERDE  prima / llega sin su `n`
MUERDE  prima / el hueco publicado no es el que sale de la cuenta
MUERDE  filtro / compra a los que bajan
MUERDE  filtro / deja pasar a todo el mundo
MUERDE  filtro / es un tapón: no deja pasar ni al que sube
MUERDE  filtro / sin pronóstico se supone que sube
MUERDE  filtro / empieza a devolver un importe
MUERDE  plazo / puesto donde la curva no gira
MUERDE  plazo / el pico está en el borde de la ventana
MUERDE  interruptor / encendido
```

Tres merecen una línea:

- **«el detector devuelve vacío»** y **«se queda corto»** existen porque el detector
  **estuvo roto de verdad** esta mañana: encontraba 2 de 16 libros y salía verde. Una
  guardia que aprueba un censo vacío aprueba cualquier cosa.
- **«es un tapón»**: sin esa inyección, un filtro que rechazara a todo el mundo pasaba
  la guardia entera.
- **«el pico está en el borde de la ventana»**: un máximo en el último plazo medido no
  es una saturación, es el final de los datos.

**Por qué `test_todo_libro_escrito_esta_en_la_lista` no corre la verja entera:** lo
duplicaría —medido: no termina en diez minutos— y escribiría en los libros de verdad,
que es lo que se quiere impedir. Prueba **la causa** (un fichero escrito que nadie ha
clasificado). El síntoma lo medí ejecutando, con las escrituras interceptadas en
memoria, y está arriba.

---

## Medición

```
python scripts/la_direccion.py > salida.txt 2>&1
echo $?                                              # 0
```

Solo lectura de disco, sin red, sin encender nada, sin borrar ni escribir ninguna línea
de ningún libro.

---

## Lo que no hice, y por qué

- **Ni una escritura contra Biwenger.**
- **No encendí el filtro.** `ENCENDIDO = False`, y no está conectado a
  `as_computer_resale` ni a ninguna otra vía. Lo único que entra en producción es la
  clasificación de los libros.
- **No arreglé la bitácora.** Pediste saber antes por qué falla; está arriba, y el
  arreglo propuesto también. Tocarlo es cambiar un escritor de producción.
- **No subí ninguna línea de ningún libro.** Al meter los ocho que faltaban en la
  lista, el `.gitignore` los destapa y ahora hay **cuatro** libros en tu disco sin
  seguir por git:

  ```
  data/trading/libro_de_renovaciones.jsonl          11 líneas, del 10/09
  data/solvency/pujas_bajo_precio.jsonl              1 línea,  del 10/09
  data/intelligence/scout_accuracy_ledger.json     172 líneas
  data/intelligence/source_accuracy_ledger.json    649 líneas
  ```

  Son datos reales y no reconstruibles, pero **producción no tiene ninguno de los
  cuatro**, y commitearlos los convierte en el libro bueno de producción. Eso es una
  decisión tuya. Lo que este commit arregla es que **a partir de ahora el runner sí
  los guarde**.
- **No borré ninguna línea de ningún libro.** Los que la verja ensució al correr los
  devolví a HEAD con `git checkout`.
- **No toqué `count_free_slots` ni `historical_max`.**
- **No moví ningún umbral**: ni el listón del 3 %, ni el suelo del +1 %, ni `bid_cap`,
  ni `PRIMA_MAXIMA_DE_PUJA`, ni `MIN_WIN_PROBABILITY`, ni el cupo, ni las cinco de
  `PUEDEN_ENCERRARLO`, ni `MAX_SINGLE_SPECULATION_PERCENT`, ni `MAX_SAFE_DEBT`, ni las
  puertas de deuda.
- **No metí el carry en ningún sitio.** Sigue descartado y con motivo.
- **No construí la regla de liquidez.**
- **No propuse comprar ni vender a nadie.**
- **No salí a la red.** Los libros de producción los leí de `origin/main` con
  `git show`, que es el repositorio local.
- **No toqué `.github/workflows/bordalas-live.yml`.**
- **No empujé.**

### Lo que contradijo al encargo

1. **Los dos sueltos SÍ estaban en la lista.** No se pierden. Tu premisa era falsa por
   ese lado — y por el otro faltaban **ocho** que no habías nombrado.
2. **La verja tocaba nueve libros, no cinco.** El cinco era mío, de ayer, y era un
   suelo: contar ficheros que cambian no ve los que se reescriben iguales.
3. **La bitácora no contamina nada de lo medido esta semana.** Contamina el tiempo, no
   los valores, y la única cuenta que la usó deduplicaba por valor.
4. **El filtro nos haría pujar menos**, que por tu propia regla es un fallo y no una
   mejora.
