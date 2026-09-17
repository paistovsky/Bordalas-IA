# La lista de la compra — informe

**Foto:** `diagnostico/status.json`, **`meta.generated_at` = 2026-09-17T07:30:55**
(snapshot `data/snapshot_20260917_072308.json`). Abierta con `encoding="utf-8"`.

**Rama:** `motor/la-lista-de-la-compra` (desde `motor/el-cable`)
**Verja:** 148/148 en verde, exit 0, salida a fichero
**Push:** NO. **`ENCENDIDO = False`.** `count_free_slots` e `historical_max`, como
estaban.

---

## BLOQUE 1.1 — Por qué el mercado libre no estaba: **no se puede comprar**

Lo primero, porque contradice la premisa del encargo.

No lo descarta un veto, no sale de otra fuente. **Los seis que nombras no están
publicados, y por un jugador que no está en el escaparate no se puede pujar: no hay a
quién ofrecerle nada.**

```
catálogo entero          550
con dueño                127
LIBRES                   423
de esos, nos mejoran     101
HOY EN EL ESCAPARATE       1      <- uno
```

Los veinte mejores libres de la foto, con la columna que decide:

```
pos  jugador                 precio  pts  part  nos suma  pts/M  escaparate
POR  Dmitrovic            4.780.000   31     6        25    6,5   no
POR  Dimitrievski         3.240.000   27     6        21    8,3   no
DEF  Espart               5.330.000   35     5        22    6,6   no
DEF  Juan Iglesias        3.190.000   34     6        21   10,7   no
DEL  Roberto Fernández    7.000.000   57     6        32    8,1   no
DEL  Zabiri               4.470.000   52     6        27   11,6   no
DEL  Budimir             11.990.000   45     6        20    3,8   SÍ
```

**El único que está en el escaparate es Budimir, y Budimir YA ESTÁ en
`roster_expansion`** — es uno de los tres «del Computer» que llamaste malos.

El universo que mira la lista es el comprable, y es exactamente eso:

```
market_size (escaparate del Computer)   20
outside_computer_market (de rivales)    46
buyable_universe                        66
por seller_kind      {'MANAGER': 46, 'COMPUTER': 20}
comprar a managers cerrado: True
```

> **La lista no se queda corta por filtrar de más. Se queda corta porque el escaparate
> de hoy trae lo que trae.** `elVestuarioLibre` ya publica los 423 libres y los 101 que
> nos mejoran, con los 20 mejores vigilados. La operación con Dimitrievski no está
> bloqueada: **no existe hoy**. Existirá el día que el Computer lo saque.

### Lo que sí faltaba, y es otra cosa

**El candidato no dice de quién es.** `seller_kind` y `seller_name` viajan en cada
fila de `season_horizon` —que es de donde sale la lista— y
`build_roster_expansion_shadow` no los copia al candidato.

No es un veto ni otra fuente: **es una columna que se cae al construir la lista.**
Tercera vez esta semana del mismo patrón (`deployment.reason` ignorado, `locked_ids`
ignorado, y ahora `seller_kind` no copiado).

---

## BLOQUE 1.2 — Las dos listas

**`SE_PUEDE_COMPRAR_HOY`  (n=3)** — *está en el escaparate y depende solo de nosotros*

```
 #  jugador          pos        cuesta   netos  x millón  de quién
 1  Fornals          MED     7.290.000    7,76     1,064  Computer
 2  Carlos Romero    DEF     4.900.000    4,08     0,833  Computer
 3  Budimir          DEL    11.990.000    6,32     0,527  Computer
```

**`HAY_QUE_PEDIRSELO`  (n=7)** — *lo tiene un rival y depende de que acepte*

```
 #  jugador          pos        cuesta   netos  x millón  de quién
 1  Javi Hernández   MED     3.780.000    5,86     1,550  Pollo17
 2  Kang-in Lee      MED     8.950.000   12,56     1,403  Luismi_Haz
 3  Alfonso Herrero  POR     4.100.000    5,29     1,290  DiosMande
 4  Ez Abde          DEL     7.690.000    6,83     0,889  Manzagool
 5  Jonathan David   DEL     7.870.000    6,87     0,872  Luismi_Haz
 6  Pépé             DEL    11.480.000    5,84     0,509  Pollo17
 7  Pedri            MED    15.900.000    0,49     0,031  Luismi_Haz
```

Cada grupo ordenado por puntos netos del once por euro, con la vara puesta. El que no
se puede medir va al final de su grupo, sin número inventado. Y el que no dice de
quién es cae **del lado prudente**: al grupo de pedírselo, no al de comprable.

### El dato al lado de la segunda lista

```
9 traspasos de manager a manager en 602 eventos del tablón,
contra 182 compras al Computer. 4 son nuestros.
```

Y desde nuestro lado, que es el que importa para una lista de la compra:

> **De esos 4, en UNO fuimos nosotros quienes compramos.** En cuarenta días de liga
> —desde el 10/08— hemos entrado por esa puerta como compradores **una vez**, contra
> 182 compras al Computer. Los otros tres fueron ventas nuestras.

---

## BLOQUE 2.1 — El guardarrail que cuenta cuerpos

Doctrina 71, confirmada leyendo el código: `build_position_guardrail` **ya sabe** quién
es intocable —lo escribe en `locked_ids` y hasta deja el motivo—. `validate_sale_set`
nunca se lo pregunta: solo cuenta cuerpos contra `floor`.

Medido sobre los veinte de la plantilla, de uno en uno:

```
jugador          pos  once  locked   cuerpos  titularidad
Dituro           POR    SÍ      SÍ        ok      BLOQUEA
Jonny            DEF    SÍ      SÍ        ok           ok
Djené            DEF    SÍ      SÍ        ok           ok
Manu Sánchez     DEF    SÍ      SÍ        ok           ok
Expósito         MED    SÍ      SÍ        ok           ok
Olasagasti       MED    SÍ      SÍ        ok           ok
Rubén García     MED    SÍ      SÍ        ok           ok
Pablo Ibáñez     MED    SÍ      no        ok           ok
Oriol Rey        MED    SÍ      no        ok           ok
Yamal            DEL    SÍ      SÍ        ok      BLOQUEA
Jutglà           DEL    SÍ      SÍ        ok      BLOQUEA
```

**Nueve de los once titulares están marcados `locked` y `validate_sale_set` los deja
pasar a todos.** Yamal incluido.

### El caso nuevo que detecta

```
Dituro: Quedarían los cuerpos pero ninguno es titular:
        2 porteros en plantilla y 0 en el once, y hacen falta 1.
Yamal:  Quedarían los cuerpos pero no los suficientes titulares:
        3 delanteros en plantilla y 1 en el once, y hacen falta 2.
Jutglà: idem.
```

**Y no se pasa de frenada.** Los otros ocho titulares siguen pasando: con 3 defensas y
5 medios en el once contra suelos de 2, soltar uno deja once alineable. El freno muerde
donde toca.

> Y protege a Yamal **por la razón buena**. El docstring de `sale_intent` avisaba de que
> «hoy Yamal solo está a salvo por accidente: el guardarrail bloquea la venta porque hay
> exactamente dos delanteros». Deja de ser un accidente del recuento.

### Por qué es una función nueva y no un arreglo de la de al lado

`validate_sale_set` la usan `sale_order`, `sale_intent` y el cable. **Medido: encenderlo
hoy no habría cambiado nada.**

```
cola de venta HOY (cuerpos)   11 de 11   caja sobre la mesa 14.447.000
cola de venta CON EL FRENO    11 de 11   caja sobre la mesa 14.447.000
```

La cola pone los sobrantes delante y nunca llega a tocar el suelo de titulares. **Que
hoy no cambie nada no es razón para encenderlo sin avisar:** el día que la caja esté en
rojo y el motor busque a quién vender, este freno puede quitarle la única salida. La
capacidad vive en `position_guardrail` —un solo sitio se hace esta pregunta— y
encenderla es cambiar el nombre de la función en una línea.

---

## BLOQUE 2.2 — El orden de cada operación

```
fichaje           orden               needs_sale_first  quién sale
Javi Hernández    SIN_VENTA                      False
Kang-in Lee       VENTA_PRIMERO                   True  Balde
Alfonso Herrero   SIN_VENTA                      False
Fornals           SIN_VENTA                      False
Ez Abde           SIN_VENTA                      False
Jonathan David    SIN_VENTA                      False
Carlos Romero     SIN_VENTA                      False
Budimir           VENTA_PRIMERO                   True  Balde, Trent
Pépé              VENTA_PRIMERO                   True  Balde, Trent
Pedri             RECAMBIO_PRIMERO               False  ... y Expósito
```

**Pedri es el único que cambia de orden**, y por la razón exacta del encargo: para
pagarlo hay que vender a ocho, y uno de los ocho es Expósito, titular. Con
`needs_sale_first` puesto, Pepe vendería a Expósito y después intentaría la puja; si la
pierde, el once se queda sin Expósito y sin Pedri, y no salta ninguna alarma.

**Con un titular entre los que salen, `needs_sale_first` no se marca.** Marcarlo *es*
la orden de vender antes de tener el recambio. Hay guardia sobre eso, y otra sobre la
mezcla: si entre los que salen hay un solo titular, manda el titular.

---

## BLOQUE 3 — La tabla por plazas del once

Recambios **comprables hoy**: los 20 del escaparate del Computer. Lo que hay que
pedirle a un rival no es un recambio de esta tabla: es una carta.

```
plaza           pos  pts/part  con vara  recambios  mejor comprable hoy
Dituro          POR      1,00      1,00          0  2 en el escaparate y ninguno se puede medir:
                                                    Iturbe, Esquivel, sin un partido jugado
Djené           DEF      2,60      2,05          3  Carmona 670.000 (+0,71)
Manu Sánchez    DEF      3,40      2,68          1  Carmona 670.000 (+0,08)
Jonny           DEF      3,60      2,83          0  ninguno mejora
Rubén García    MED      3,17      3,63          3  Mayol 470.000 (+2,10)
Oriol Rey       MED      3,80      4,36          2  Mayol 470.000 (+1,38)
Jutglà          DEL      4,17      4,75          2  Budimir 11.990.000 (+3,80)
Pablo Ibáñez    MED      4,33      4,97          2  Mayol 470.000 (+0,77)
Expósito        MED      4,83      5,54          1  Mayol 470.000 (+0,19)
Olasagasti      MED      6,40      7,34          0  ninguno mejora
Yamal           DEL     12,67     14,43          0  ninguno mejora
```

### La mejor operación sin vender a nadie — y por qué no me quedo con ella

Por puntos netos por euro gana **Mayol, 470.000 €, +2,10 por jornada** en la plaza de
Rubén García. Pero:

> **AVISO DE `n`: un partido.** El número que corona la tabla es el más flojo de muestra
> que hay en ella. No lo quito —es la medición— pero no me quedo con él.

Todas las operaciones que caben en caja salen de muestras de uno o dos partidos.
Filtrando a tres partidos o más:

```
recambio        por la plaza de       cuesta   netos  partidos  ¿cabe en caja?
Miguel Román    Rubén García       3.720.000   +1,72         6  SÍ
José Salinas    Djené                980.000   +0,32         4  SÍ
Budimir         Jutglà            11.990.000   +3,80         6  NO — hay que vender
Gerard Moreno   Jutglà             6.860.000   +2,09         5  SÍ
Miguel Román    Oriol Rey          3.720.000   +0,99         6  SÍ
Deossa          Rubén García       1.270.000   +0,27         5  SÍ
```

> **LA MEJOR SÓLIDA QUE CABE SIN VENDER NADA: Miguel Román por la plaza de Rubén
> García. 3.720.000 €, +1,72 puntos por jornada con la vara, sobre 6 partidos.**
>
> Esa es la que yo pondría arriba, y no la de puntos por euro: la corona por euro se la
> lleva un jugador de un partido.

Y la más grande de todas —Budimir por Jutglà, **+3,80 sobre 6 partidos**— no cabe en
los 8,87 M: pide vender antes. Ahí `needs_sale_first` está bien puesto, porque los que
saldrían (Balde, Trent) son sobrantes.

### Y el caso de Dituro, que es el que motiva el encargo

**Sí, es la peor plaza del once: 1,00 punto por partido en 6 partidos.** En eso el
encargo acierta de lleno.

**Pero la operación que propones no existe hoy.** Los dos porteros del escaparate son
Iturbe y Esquivel, 150.000 € cada uno, **0 puntos en 0 partidos**. No se les puede
medir, así que no entran como recambio: cambiar un titular a ciegas no es una mejora, es
una apuesta.

Los seis recambios baratos —Dimitrievski 3,24 M, Dmitrovic 4,78 M, Remiro, Leo Román,
Joan García— **son libres y no están publicados**. Con 8,87 M en caja se pagarían sin
vender nada, exactamente como dices. **Pero no se puede pujar por ellos.**

> La plaza de Dituro no está sin arreglar por un fallo de la lista. Está sin arreglar
> porque hoy no hay portero que comprar. Existe el día que el Computer saque uno, y por
> eso los veinte están vigilados.

**Corrección a mi propio motivo:** la primera versión de esta tabla decía «hoy no hay ni
un jugador de esta posición en el escaparate». Era falso —hay dos— y un motivo falso es
peor que no tener motivo, porque se deja de discutir. Ahora los cuenta aparte y dice que
no se pueden medir.

---

## Guardias

**+1 módulo, 7 guardias**, en `src/analysis/test_la_lista_de_la_compra_v1.py`, dada de
alta en `scripts/run_validation_gate.py`. Las cuatro del encargo más tres.

**Las quince inyecciones de fallo muerden**, probadas reintroduciendo el fallo en
memoria:

```
MUERDE  lista / el desconocido se cuenta comprable
MUERDE  lista / grupo sin nombre
MUERDE  lista / catálogo vacío publica grupos
MUERDE  lista / ordena por coste
MUERDE  libres / cuenta los no publicados
MUERDE  orden / marca needs_sale_first en un titular
MUERDE  orden / solo mira al primero de los que salen
MUERDE  orden / sin guardarrail deja de frenar
MUERDE  guardarrail / vuelve a contar cuerpos
MUERDE  guardarrail / bloquea cualquier venta
MUERDE  tabla / empieza por la mejor plaza
MUERDE  tabla / sin la vara
MUERDE  tabla / propone lo que no cabe
MUERDE  puerta / se inventa un cero
MUERDE  interruptor / encendido
```

### La que no mordía, dicho porque importa más que las que sí

`test_el_guardarrail_mira_titularidad` empezó con tres porteros de los que **dos** eran
titulares. Con ese fixture, vender al primero deja un titular y el suelo se cumple: la
comprobación pasaba con y sin el freno nuevo. El fixture tiene que tener **un** portero
titular y dos que no juegan —que es justo la foto del 17/09— y por eso ahora la guardia
comprueba primero la forma del fixture y falla si alguien la cambia.

**Ninguna guardia lee `data/`, sale a la red ni mira el reloj.** La vara entra por
argumento y la caché de pronósticos se clava vacía antes de nada. Ningún mensaje de
aserción nombra el directorio de estado: la Regla A de `test_verja_determinista_v1` lo
busca en cualquier literal del módulo y no distingue una lectura de una frase que hable
de ella.

---

## Medición

`scripts/la_lista_de_la_compra.py` — 246 líneas de salida, exit 0, solo lectura de
disco, sin red. Lo primero que imprime es `meta.generated_at`.

```
python scripts/la_lista_de_la_compra.py > salida.txt 2>&1
echo $?
```

---

## Lo que no hice, y por qué

- **Ni una escritura contra Biwenger.** Ni pujas, ni ofertas, ni la de Balde.
- **No encendí nada.** `ENCENDIDO = False`, con guardia.
- **No toqué `count_free_slots` ni `historical_max`.** El bloque 4 del encargo anterior
  sigue pendiente de tu decisión y `ROSTER_FILL` sigue sin tope. Está como lo dejé.
- **No cambié `validate_sale_set`.** El freno de titularidad es una función nueva al
  lado, y está medido que hoy encenderlo no cambiaría la cola de venta.
- **No toqué ningún umbral:** ni el listón del 3 %, ni el suelo del +1 %, ni `bid_cap`,
  ni `PRIMA_MAXIMA_DE_PUJA`, ni `MIN_WIN_PROBABILITY`, ni el cupo, ni las cinco de
  `PUEDEN_ENCERRARLO`, ni `MAX_SINGLE_SPECULATION_PERCENT`, ni `MAX_SAFE_DEBT`, ni las
  tres puertas de deuda, ni `POSITION_FLOOR`, ni `STARTER_FLOOR`, ni `POSITION_DESIRED`.
- **No toqué ningún `intent`.**
- **No abrí ninguna oferta a rivales.** Este encargo solo las etiqueta.
- **No propuse vender a Yamal** — y el freno nuevo, de hecho, lo protege.
- **No salí a la red.**
- **No toqué `.github/workflows/bordalas-live.yml`.**
- **No empujé.**

### Lo que contradijo al encargo, y ganó la medición

1. **El mercado libre no está porque no se puede comprar**, no porque lo vete nadie. De
   101 libres que nos mejoran, hoy hay 1 en el escaparate, y ese 1 ya estaba en la
   lista.
2. **La operación de Dituro no existe hoy.** Los seis recambios que nombras no están
   publicados; los dos porteros que sí lo están llevan 0 partidos.
3. **El guardarrail deja pasar a nueve titulares, no solo a Dituro.** Yamal incluido.
4. **La mejor operación por puntos-por-euro tiene n=1.** La mejor sólida que cabe sin
   vender es Miguel Román, y es otra.
