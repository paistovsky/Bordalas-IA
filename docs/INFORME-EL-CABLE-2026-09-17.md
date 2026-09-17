# El cable — informe

**Foto:** `diagnostico/status.json`, **`meta.generated_at` = 2026-09-17T07:30:55**
(snapshot `data/snapshot_20260917_072308.json`, modo LIVE). Abierta con
`encoding="utf-8"`. **Todo lo que sigue es de esta foto y de ninguna otra.**

**Rama:** `motor/el-cable` (desde `medir/la-plaza-y-el-cable`)
**Verja:** 147/147 en verde, exit 0, salida a fichero
**Push:** NO. **`ENCENDIDO = False`.** Ninguna escritura contra Biwenger.

---

## BLOQUE 0 — La seguridad, y va primero

La regla, con las tres partes puestas y con guardia cada una:

```
1. dos cifras separadas, con nombre, y nunca sumadas
2. ninguna puja contra caja realizable -> needs_sale_first, y la venta va primero
3. solo cuenta lo que cumple LAS TRES: viva + sobrante + pasa el guardarrail
```

**Cómo se impide pujar contra dinero no cobrado.** `puja_permitida()` tiene una sola
puerta abierta: que el importe quepa en `caja_ahora`. Corrido contra la foto:

```
justo por debajo de la caja      8.874.115   puja SI   needs_sale_first False
un euro por encima               8.874.117   puja NO   needs_sale_first True
                                             -> "vender a Balde (1.578.500). LA VENTA VA PRIMERO"
la mitad de la realizable       16.097.616   puja NO   needs_sale_first True
                                             -> vender a Balde, Trent, Pablo Durán, Fortuño,
                                                Álvaro Carreras, Paco Cortés, Benavidez
más de lo que hay ni vendiendo  23.321.117   puja NO   needs_sale_first FALSE
                                             -> no se promete una venta que no existe
```

**Un euro por encima de la caja cobrada ya no pasa**, aunque la realizable lo cubriera
catorce veces. Eso es lo que impide el escenario que te preocupaba.

Y el cuarto caso importa tanto como el segundo: cuando ni vendiéndolo todo se llega,
`needs_sale_first` es **False**. Marcarlo sería prometer una venta que no existe.

---

## BLOQUE 1 — El cable

```
caja_ahora            8.874.116 €   lo que Pepe puede comprometer hoy
caja_realizable      14.447.000 €   lo que entraría cobrando ofertas vivas,
                                    y que NO se puede comprometer hasta cobrarla
techo_ahora          13.743.516 €
techo_si_se_vende    24.653.016 €
```

**La suma (23.321.116) no aparece en ningún campo del JSON publicado**, y hay guardia
que lo recorre entero buscándola.

### La aritmética del 25 %, respetada

```
el techo sube 10.909.500 con 14.447.000 de ventas
```

La diferencia —3.537.500— es el cuarto del precio de cada uno que **ya vivía dentro de
`maximumBid`**. Si el techo subiera por el importe entero, se estaría contando dos
veces; si no subiera nada, se estaría contando cero. Hay guardia sobre las dos cosas.

Y la identidad, confirmada una vez más **en esta foto** (la combinación 19ª):

```
−373.984 de saldo + 56.470.000/4 − 0 comprometido = 13.743.516
maximumBid publicado                             = 13.743.516   CUADRA
```

### Quién compone la caja realizable, y por qué es sobrante

Las nueve pasan las tres condiciones: oferta viva, en la cola de venta como sobrante,
y el conjunto entero pasa `position_guardrail.validate_sale_set`.

| jugador | pos | oferta | precio | titular | por qué sobra |
|---|---|---:|---:|:--:|---|
| Balde | DEF | 1.578.500 | 1.520.000 | no | Cae y no juega |
| Trent | DEF | 2.536.500 | 2.530.000 | no | Cae y no juega |
| Pablo Durán | DEL | 395.000 | 380.000 | no | Cae y no juega |
| Fortuño | POR | 153.800 | 150.000 | no | No juega |
| Álvaro Carreras | DEF | 1.326.500 | 1.340.000 | no | No juega |
| Paco Cortés | DEL | 151.200 | 150.000 | no | No juega |
| Benavidez | MED | 151.100 | 150.000 | no | No juega |
| Expósito | MED | 5.556.300 | 5.340.000 | **SÍ** | Caro por punto |
| Rubén García | MED | 2.598.100 | 2.590.000 | **SÍ** | Caro por punto |

**Y quién no entra, con su motivo:** Drkusic y Lunin, los dos porque no tienen oferta
viva. Su valor a mercado exige publicarlos y esperar a que alguien los compre, y eso
no es caja.

**Nota sobre los dos titulares.** Expósito y Rubén García entran en la caja realizable
porque el guardarrail dice que el once aguanta sin ellos, no porque convenga
venderlos. Son 8.154.400 € de los 14.447.000 — más de la mitad. El número está bien
calculado y la decisión de tocarlos no es de este encargo.

---

## BLOQUE 2 — La tabla que faltó

Los diez candidatos de `roster_expansion`, con la vara puesta (defensa ×0,787, medio
×1,147, delantero ×1,139, portero sin factor), 33 jornadas por delante y 4 fichas
libres. **Ordenada por puntos netos por millón gastado.**

```
 #  fichaje           pos        cuesta  pts/jor   netos  x millón  ficha  hoy
 1  Javi Hernández    MED     3.780.000     5,11    5,86     1,550    SÍ    SÍ
 2  Kang-in Lee       MED     8.950.000    10,95   12,56     1,403    SÍ    NO
 3  Alfonso Herrero   POR     4.100.000     5,29    5,29     1,290    SÍ    SÍ
 4  Fornals           MED     7.290.000     6,76    7,76     1,064    SÍ    SÍ
 5  Ez Abde           DEL     7.690.000     6,00    6,83     0,889    SÍ    SÍ
 6  Jonathan David    DEL     7.870.000     6,03    6,87     0,872    SÍ    SÍ
 7  Carlos Romero     DEF     4.900.000     5,18    4,08     0,833    SÍ    SÍ
 8  Budimir           DEL    11.990.000     5,55    6,32     0,527    SÍ    NO
 9  Pépé              DEL    11.480.000     5,13    5,84     0,509    SÍ    NO
10  Pedri             MED    15.900.000     5,26    0,49     0,031    SÍ    NO
```

*(`ficha` = cabe la ficha; `hoy` = se paga con la caja cobrada.)*

**A quién habría que vender, operación a operación:**

```
Javi Hernández    se paga con la caja cobrada. Quedarían 5.094.116.
Kang-in Lee       VENDER PRIMERO: Balde (1.578.500)
                  entra 1.578.500, quedarían 1.502.616.   needs_sale_first = True
Alfonso Herrero   se paga con la caja cobrada. Quedarían 4.774.116.
Fornals           se paga con la caja cobrada. Quedarían 1.584.116.
Ez Abde           se paga con la caja cobrada. Quedarían 1.184.116.
Jonathan David    se paga con la caja cobrada. Quedarían 1.004.116.
Carlos Romero     se paga con la caja cobrada. Quedarían 3.974.116.
Budimir           VENDER PRIMERO: Balde + Trent (4.115.000)
                  quedarían 999.116.                      needs_sale_first = True
Pépé              VENDER PRIMERO: Balde + Trent (4.115.000)
                  quedarían 1.509.116.                    needs_sale_first = True
Pedri             VENDER PRIMERO: Balde, Trent, Pablo Durán, Fortuño, Álvaro Carreras,
                  Paco Cortés, Benavidez y Expósito (11.848.900)
                  quedarían 4.823.016.                    needs_sale_first = True
```

**Con las cuatro fichas abiertas, los diez caben por plaza**, así que ninguno sale con
el motivo «no cabe la ficha». Con `free_slots: 0` salían los diez con ese motivo, y la
guardia comprueba que en ese caso el motivo es ese y **no** «no hay dinero»: son dos
arreglos distintos.

**Pedri sale el último y el número explica por qué.** Aporta 6,03 puntos por jornada
con la vara puesta, pero para pagarlo hay que vender ocho, y uno de los ocho es
Expósito, que es titular y aporta 5,54. **Neto: +0,49 puntos por jornada por 15,9 M**,
0,031 por millón. La operación existe y no merece la pena, que es distinto de que no
se pueda medir.

**Y un aviso sobre el segundo.** Kang-in Lee sale con 10,95 puntos por jornada porque
la foto le da 361,3 puntos de aquí a final, el doble que a cualquier otro. Pero su
pronóstico es **50 % titular (UNCERTAIN)** contra el 80 % del que saldría, que es
justo lo que `PIERDE_TITULARIDAD` estaba señalando. La tabla ordena por lo que la foto
dice; el descuento por titularidad no está en `season_points_remaining`.

> **Lo que la tabla dice, y no estaba dicho hasta hoy:** el mejor por euro es Javi
> Hernández a 3,78 M, y **se paga hoy con la caja que ya hay**. Kang-in Lee rinde casi
> lo mismo por euro y el doble en puntos absolutos, y para él basta con cobrar la
> oferta de Balde.

---

## BLOQUE 3 — La cola por consecuencia

### Las tres preguntas, medidas antes de tocar el orden

**1. ¿Es configurable el número de escrituras por vuelta? NO — es de diseño.**
No hay constante ni variable de entorno. `autopilot.run_cycle` ejecuta la primera
acción ejecutable de `action_queue`, refresca, recalcula y corta con
«No se ejecutará una segunda escritura en este ciclo». Subirlo sería un cambio
estructural, no tocar un número. **No lo he tocado.**

**2. ¿Cuántas veces ha caducado algo sin que Pepe llegara? CERO.**

```
publicaciones vivas hoy                                  18
de ellas expired = true                                   0
las siete que piden renovación                2,9 a 8,8 h

libro de publicación                          19 episodios
episodios que dejaron de estar publicados                 6
de esos, jugadores QUE SIGUEN SIENDO NUESTROS             0   <- publicación perdida
```

Los seis que dejaron de estar publicados **se vendieron** —Mangala, Zubeldia, Diego
Conde, Cepeda y dos episodios más—: ya no están en la plantilla. Ningún jugador
nuestro ha perdido su publicación.

En el libro de renovaciones hay **3 fallos de 11 intentos**, los tres del 10/09 y los
tres del mismo jugador (Jonny, HTTP 400 `Low sell price`). **Son fallos de precio, no
de plazo**, y Jonny sigue publicado hoy.

> Aviso de `n`: el libro de publicación guarda **19 episodios**, no toda la historia.
> Lo que sostiene el cero es que ningún jugador nuestro está hoy sin publicar, y eso
> se comprueba contra la plantilla entera.

**3. ¿Se refresca la foto entre acciones, y cuánto tarda el ciclo? Sí, y 148 s.**

```
duración del ciclo    n=39 escrituras   mediana 148 s   min 24 s   max 362 s
ventana medida        2026-09-14T13:10 -> 2026-09-17T07:26
fases                 POST_ACTION 39, PRE_ACTION 22
cron                  cada 60 minutos
```

Tras cada escritura, `run_cycle` llama a `refresh_snapshot()` y recalcula el estado
entero (fase `POST_ACTION`). La foto **sí** se refresca. Y después para.

### El orden, con esos números dentro

Solo hay una escritura por vuelta, así que lo que se aplaza **no se hace en un minuto:
se hace en la vuelta siguiente**. Eso es `cron + ciclo`, y entra por argumento:

```
espera de una vuelta   1,041 h    (60 min de cron + 148 s de ciclo)
umbral (×2)            2,082 h
```

```
 #  acción                       prio  abre   caduca en   sobrevive
 1  ACCEPT_RECOVERY_OFFER         650     3      23,5 h      SÍ
 2  RENEW_MARKET_LISTING          690     0       2,9 h      SÍ

por caducidad iría:   RENEW_MARKET_LISTING   (abre 0)
por consecuencia va:  ACCEPT_RECOVERY_OFFER  (abre 3)
```

**Qué cambia:** cobrar la oferta se adelanta a renovar la publicación. Cobrar mete
caja, y con el saldo en rojo esa caja es lo que abre el presupuesto de fichar, el
carril y la subasta —las tres están hoy en cero por lo mismo—. Renovar mantiene viva
una publicación que ya existe: evita perder algo, no abre nada.

**Qué no llega a caducar por ello:** la publicación de Yamal tiene 2,9 h y el umbral
son 2,08 h. **Sobran 0,82 h.**

> **Y esto hay que decirlo, porque no es holgado.** Con el cron a 60 minutos, dos
> vueltas perdidas se comen el margen. Por eso el umbral es ×2 y no ×1, y por eso la
> regla mira si sobrevive en vez de suponerlo.

**Si chocan, gana no perder, y queda dicho.** Con la publicación a media hora de
caducar, la cola no se reordena: `RENEW_MARKET_LISTING` se queda delante aunque no
desbloquee nada, y el choque se publica en `gana_no_perder`. Hay guardia sobre ese
caso, y otra sobre el de plazo desconocido: sin saber cuánto le queda, **no se
aplaza**.

Lo que **no** se ha tocado: la tabla `PRIORITY` de `decision_orchestrator`, el cron, y
el número de escrituras por vuelta. Esto es una pieza nueva al lado, apagada.

---

## BLOQUE 4 — `count_free_slots`, arreglado

La reconstrucción, con su propio cuadre:

```
reparto inicial ajustado    15        (el tablón declara 12, y con 12 no cuadra ninguna)
cuadran                     7 de 8
operaciones                 367 distintas de 400 vistas   (el tablón repite)
trusted                     True      (NUESTRA línea cuadra al cero)
```

| manager | hoy | reconstr. | dif | sin explicar | máximo |
|---|---:|---:|---:|---:|---:|
| Pollo17 | 20 | 19 | −1 | 1 | **24** |
| Luismi_Haz | 19 | 19 | +0 | 0 | 23 |
| Manzagool | 13 | 13 | +0 | 2 | 21 |
| **Pepe Bordalás** | 20 | 20 | **+0** | 3 | **21** |
| DiosMande | 11 | 11 | +0 | 4 | 20 |
| Mex | 14 | 14 | +0 | 0 | 19 |
| Prinzipote | 17 | 17 | +0 | 0 | 17 |
| Alvaro Retamosa | 13 | 13 | +0 | 0 | 15 |

**El único descuadre es Pollo17 por −1, y tiene exactamente 1 jugador sin explicar en
el ledger.** El ajuste no es un truco: el reparto se prueba del 8 al 25 y se queda el
que hace cuadrar más líneas.

```
ANTES   free_slots = 0    (contra la mayor de HOY, 20)
AHORA   free_slots = 4    (contra la mayor JAMÁS VISTA, 24)

is_lower_bound: True      source: MAXIMO_HISTORICO
```

**Y la cifra sigue viajando diciendo que es una cota inferior**, con las dos columnas
publicadas (`largest_roster_today` y `largest_roster_ever`) y el motivo del cuadre al
lado. Cambiar el número no cambia lo que es: nadie ha comprobado el tope de Biwenger, y
esto no lo comprueba. Hay guardia sobre eso.

**Se ignora solo si su cuadre no pasa.** Si nuestra línea reconstruida dejara de
coincidir con la de hoy, `trusted` se pone a `False` y `count_free_slots` vuelve a la
mayor de hoy. Y nunca baja del número de hoy: si alguien tiene 20 ahora mismo, 20
caben, lo diga lo que diga una reconstrucción.

Los dos llamantes —`dashboard_state` y `acquisition_valuation`— salen del **mismo
sitio**, `el_cable.maximo_historico_de_fichas`. Dos respuestas distintas a «cuántas
fichas caben» es como se acaba pintando una plaza que el motor no ve.

### Este arreglo NO es gratis, y lo digo antes de que lo veas

Abrir fichas abre la vía `ROSTER_FILL` en `classify_operation`. Medido sobre las 66
filas del horizonte de esta foto:

```
con 0 fichas libres, la vía de ficha vacía no se abría para nadie
con 4, pasan el veto 27 de 66
```

Los que pasan incluyen a Pedri (15,9 M), Budimir (11,99 M), Pépé (11,48 M) y Nico
Williams (8,46 M). Lo que entre por ahí **deja de ser TRADE y pasa a ser SIGNING**, y
eso significa otro bolsillo (8,87 M en vez de 5,32 M) **y perder el tope de prima del
+0,25 %**.

> **27 es una cota SUPERIOR**: sólo entran de verdad las que además superen su precio
> por la vía de relleno. Pero es el único cambio de este encargo que toca producción
> fuera del interruptor, y tenías que saberlo por escrito y no descubrirlo en la
> pantalla. **Deshacerlo es una línea** —no pasar `historical_max`— y es decisión tuya.

---

## Guardias

**+1 módulo, 8 guardias**, en `src/analysis/test_el_cable_v1.py`, dada de alta en
`scripts/run_validation_gate.py`. Las cuatro del encargo más cuatro.

**Las quince inyecciones de fallo muerden**, probadas reintroduciendo el fallo en
memoria:

```
MUERDE  puja / suma las dos cajas
MUERDE  puja / no manda vender primero
MUERDE  presupuesto / publica la suma en un campo
MUERDE  techo / sube el importe entero
MUERDE  realizable / se salta el guardarrail
MUERDE  realizable / cuenta el valor a mercado como caja
MUERDE  tabla / ordena por coste
MUERDE  cola / se queda con la caducidad
MUERDE  cola / aplaza lo que no sobrevive
MUERDE  fichas / ignora el máximo histórico
MUERDE  fichas / deja de decir que es un suelo
MUERDE  fichas / se cree el reparto que declara el tablón
MUERDE  fichas / no deduplica el tablón
MUERDE  interruptor / encendido
```

### Dos que NO mordían, dicho porque importa más que las que sí

**`test_las_dos_cajas_no_se_suman`** comprobaba que existieran las dos claves. Una
versión que además publicara un `total` con la suma las tenía igual y **pasaba**. Ahora
recorre el JSON entero buscando cualquier valor que valga la suma y falla si aparece.
Comprobar que está lo que debe estar no es comprobar que no está lo que no debe.

**`test_la_caja_realizable_pasa_el_guardarrail`** llevaba una cola con tres defensas, y
de siete que hay caben cuatro sin bajar del suelo. O sea que sustituir el guardarrail
por uno que dijera «todo vale» **no cambiaba el resultado**: la guardia pasaba sin
haber probado nada. Ahora la cola trae cinco defensas con oferta viva, el quinto rompe
el once, y la guardia comprueba que no entra.

### Y una que puso la verja en rojo por una frase

El mensaje de una aserción decía «ha abierto `data/`», y `test_verja_determinista_v1`
falló: su Regla A busca el directorio de estado escrito en **cualquier** literal del
módulo, y no distingue una lectura de un mensaje que habla de ella. Es un falso
positivo de una regla deliberadamente conservadora, y la respuesta correcta es no
escribir la ruta, **no relajar la regla**. La comprobación es la misma.

**Ninguna guardia lee `data/`, sale a la red ni mira el reloj.** La vara entra por
argumento y la espera de la cola también. `maximo_historico_de_fichas` sí lee disco, y
por eso no se prueba: se prueba `mayor_plantilla_jamas_vista`, que es pura y come
fixtures.

---

## Medición

`scripts/el_cable.py` — 240 líneas de salida, exit 0, solo lectura de disco, sin red.
Lo primero que imprime es `meta.generated_at`.

```
python scripts/el_cable.py > salida.txt 2>&1
echo $?
```

---

## Lo que no hice, y por qué

- **Ni una escritura contra Biwenger.** Ni la de Balde, que sigue en ACCEPT_NOW.
- **No encendí el cable.** `ENCENDIDO = False`, con guardia, y el estado publicado
  lleva `enabled: false`.
- **No subí el número de escrituras por vuelta** ni toqué el cron ni la tabla
  `PRIORITY`. La cola por consecuencia es una pieza al lado, apagada.
- **No toqué ningún umbral:** ni el listón del 3 %, ni el suelo del +1 %, ni
  `bid_cap`, ni `PRIMA_MAXIMA_DE_PUJA`, ni `MIN_WIN_PROBABILITY`, ni el cupo, ni las
  cinco de `PUEDEN_ENCERRARLO`, ni `MAX_SINGLE_SPECULATION_PERCENT`, ni
  `MAX_SAFE_DEBT`, ni las tres puertas de deuda, ni `MIN_STARTER_PERCENT`, ni
  `MIN_HIERARCHY_VALUE`.
- **No toqué ningún `intent`.** Sigue mapeado y quieto.
- **No propuse vender a Yamal.**
- **No salí a la red.**
- **No toqué `.github/workflows/bordalas-live.yml`.**
- **No empujé.**

### Lo único que sí cambia producción, y va fuera del interruptor

`count_free_slots` pasa de 0 a 4 huecos, porque el encargo pedía arreglarlo. Eso abre
la vía de ficha vacía para hasta 27 filas. Está medido arriba, y deshacerlo es una
línea.
