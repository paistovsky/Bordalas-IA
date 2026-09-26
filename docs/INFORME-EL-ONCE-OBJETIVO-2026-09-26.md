# INFORME — EL ONCE OBJETIVO

**Fecha:** 26/09/2026 · **Rama:** `medir/el-once-objetivo`, desde `origin/main` (`5d0ca971`)
**Solo medición y diseño. No se enciende nada.** Verja 185/185 en verde con los 5 interruptores
de producción, árbol quieto (`verja-el-once-objetivo.txt`). Salida completa del script en
`salida-el-once-objetivo.txt`.

---

## En cinco líneas

1. **Los puntos partido a partido ya los tenemos, sin pedir nada:** el catálogo trae `fitness`
   (los últimos 5 partidos de cada jugador). Cruzado con el calendario salen **1.819 partidos
   de 505 jugadores**, comprobados al punto contra los totales.
2. **El calendario existe, pero no decide el once de la temporada.** En casa +0,22 por partido
   sobre la media propia; contra la mitad baja +0,19; las dos a la vez +0,52. **Cambia un solo
   nombre en un solo once**, entre dos defensas libres empatados a 0,05.
3. **El ojeador no trae titularidad:** son subidas y bajadas de precio. **La titularidad de
   todo el catálogo ya está construida**, detrás de `BORDALAS_OBJETIVOS_EL_CATALOGO` (apagado):
   497 de 547, cero peticiones más. Doctrina 84, cuarta vez esta semana.
4. **La titularidad barata se parece a la buena, pero no tanto:** r = 0,70 (n = 143).
   Sirve como tasa para el once de la temporada, no para decidir a quién alineas.
5. **Con la caja de hoy, el plan son 3 escrituras y +0,37 puntos por jornada:** vender a Jonny
   y comprar a Hinojo, y comprar a Balliu. **El once objetivo (C) está lejos:** 8 de sus 11 son
   libres que el Computer todavía no ha sacado.

---

## BLOQUE 1 — EL CALENDARIO

### 1. Dónde están los puntos por jornada y jugador

| Sitio | Qué tiene | ¿Sirve? |
|---|---|---|
| `puntos_por_jornada.jsonl` | **una línea**: totales acumulados al cerrar la J7 | no, sin partido a partido |
| `marcador.json` | totales por jornada, **solo de nuestra plantilla** | no, 13-21 jugadores |
| perfiles del colector del tablón | son perfiles de **mánagers**, no de jugadores | no |
| **catálogo, campo `fitness`** | **puntos de los últimos 5 partidos de cada jugador**, el más reciente primero; `null` o una etiqueta si no jugó | **sí** |

**No hace falta pedir nada a Biwenger.** `fitness` viene en cada foto. Cruzarlo con el
calendario tiene una trampa, y está medida: en fotos tomadas en mitad de una jornada, la
casilla se corre una posición (208 de 2.450 observaciones repetidas no coinciden). Por eso:

- **La foto del 10/09 es tranquila** (entre la J4 y la J5) y ningún equipo llevaba más de 5
  partidos, así que su `fitness` es la temporada entera. Se comprueba: **la suma de `fitness`
  es igual a los puntos totales.**
- **La del 19/09 se lee solo por lo nuevo:** cuántas casillas se han corrido respecto a la del
  10/09, y lo nuevo se comprueba contra la resta de totales.
- **Un jugador que no cuadra se descarta entero.**

```
jugadores de campo          526
cuadran al punto            505   (96,0 %)
lo nuevo no suma             17
sin equipo o cambió          4
partidos jugados         1.819   J1 a J7 (y un aplazado de la J8)
```

**Plazo:** hasta el 19/09 a las 18:18, la última foto cruda que hay en disco. La J7 está a medias.

### 2 y 3. El efecto, en desviación sobre la media propia, por posición

Desviación = puntos de ese partido − la media de ese jugador. **Rival alto** = puesto 1-10 en
la clasificación de LaLiga del 23/09. Entre paréntesis, el intervalo del 95 %.

| | en casa | fuera | rival alto | rival bajo | casa y rival bajo |
|---|---|---|---|---|---|
| **TODAS** | **+0,20** (±0,17) n=959 | −0,20 (±0,17) n=970 | **−0,20** (±0,17) n=941 | +0,19 (±0,17) n=988 | **+0,52** (±0,24) n=486 |
| POR | −0,41 (±0,84) n=56 | +0,39 (±0,73) n=59 | +0,20 (±0,88) n=58 | −0,20 (±0,69) n=57 | −0,25 (±0,99) n=27 |
| DEF | +0,22 (±0,30) n=290 | −0,21 (±0,25) n=306 | **−0,36** (±0,26) n=284 | **+0,33** (±0,29) n=312 | **+0,67** (±0,45) n=149 |
| MED | +0,12 (±0,28) n=298 | −0,13 (±0,31) n=291 | −0,17 (±0,29) n=295 | +0,17 (±0,30) n=294 | +0,33 (±0,36) n=149 |
| DEL | **+0,41** (±0,39) n=260 | **−0,41** (±0,38) n=259 | −0,12 (±0,38) n=251 | +0,11 (±0,39) n=268 | **+0,70** (±0,56) n=132 |

**Casa y fuera, exacto,** con los totales del catálogo (`pointsHome`, `playedHome`…), que no
necesitan cruzar nada: **+0,217 en casa y −0,217 fuera, n = 1.016 y 1.017.** Coincide con la
reconstrucción (+0,20), lo que valida el cruce.

**Lo que dicen los números:**

- **Tu creencia es cierta en dirección y pequeña en tamaño.** Una media de ~4 puntos por
  partido se mueve ±0,2 por el campo y ±0,2 por el rival: un 5 % cada cosa y un 13 % las dos
  juntas.
- **El delantero depende del campo (±0,41) y el defensa del rival (±0,35).** Tiene sentido:
  la portería a cero depende de a quién tienes delante.
- **Porteros: n = 56 y el signo al revés**, dentro del ruido (±0,84). No se puede decir nada.
- **En bruto parece otra cosa:** los delanteros hacen 5,06 en casa y 4,22 fuera (+0,84 de
  diferencia), y en desviación la diferencia es +0,82. Aquí coinciden. **Contra el rival, el
  bruto exagera:** 5,07 contra 4,18 (+0,89) frente a +0,23 en desviación. Esa diferencia la
  ponen los buenos, no el rival (doctrina 95).

**Salvedad:** el puesto del rival es el del 23/09, después de la J7. Esos mismos partidos han
hecho la clasificación. Con 7 jornadas no hay una clasificación anterior que no esté hecha de
ellos.

### 4. ¿Cambia algún nombre? Uno, en un empate

Apliqué el efecto medido (casa/fuera más rival alto/bajo, por posición) a los partidos que
quedan de cada equipo:

```
A    once de la temporada      NO cambia
B    once de la temporada      NO cambia
C    once de la temporada      Lago <-> Hancko   (3,72 contra 3,68: se separan 0,05)
LIGA once de la temporada      NO cambia
A    once de la JORNADA 8      NO cambia
```

**Para el once de la temporada, el calendario no sirve para decidir, y hay un motivo de fondo:**
en 38 jornadas cada equipo juega 19 en casa y 19 fuera, y contra todos dos veces. **El
calendario completo se compensa solo.** Solo queda lo que no se compensa en las 31 que faltan,
que es poco.

**Para el once de la jornada, sí puede importar en los márgenes** (±0,7 a un delantero en casa
contra un flojo), pero en la J8 no ha cambiado ningún nombre de A. Es n = 1 jornada.

**Los tramos escritos a mano** (`duro_hasta: 6`, `normal_hasta: 13`) siguen sin medir. Lo que sí
queda medido es la versión en dos mitades: −0,20 contra la de arriba y +0,19 contra la de abajo.

---

## BLOQUE 2 — LA TITULARIDAD

### 5. El ojeador no trae titularidad

Los 545 del ojeador son **movimientos de precio** («subidas y bajadas» de FutbolFantasy,
Analítica…). Su propio aviso dice *«Movimiento OBSERVADO, no pronóstico»*. No hay titularidad
ahí.

### 6. La titularidad de todo el catálogo ya existe, detrás de un interruptor apagado

Las páginas de equipo de FutbolFantasy traen **la plantilla entera** con `data-probabilidad`, y
se piden las 20 en cada vuelta. Hoy solo se emparejan los objetivos (143). Con
`BORDALAS_OBJETIVOS_EL_CATALOGO`, medido el 20/09 (`INFORME-DE-64-A-513`):

```
emparejados        142  ->  497 de 547
coste              +0,63 s por vuelta, CERO peticiones
paso 0             ya lo tiene: está en los probados de config/paso_0.json
```

**No hay que construirla: hay que encenderla.** Eso es decisión tuya.

### 7. La barata contra la buena

**Barata:** partidos jugados / partidos que ha jugado su equipo, según el calendario (mejor que
entre jornadas disputadas, por los aplazados). **Buena:** FutbolFantasy del 22/09, para la J8.

```
n = 143 (los que hoy tienen FutbolFantasy; no 52)
Pearson      0,70
Spearman     0,69
error medio  0,26   (26 puntos de probabilidad)
coinciden en "titular sí o no" (corte 50 %): 101 de 143 = 71 %
```

**Se parecen, pero una de cada tres veces discrepan en si es titular.** Miden cosas distintas: la
barata es lo que pasó (y cuenta como jugado salir 5 minutos); la buena es lo que va a pasar el
próximo partido, con lesiones y rotaciones.

- **Para el once de la TEMPORADA vale la barata,** porque es una tasa.
- **Para el de la JORNADA, no:** ahí hace falta la buena, y para eso está el interruptor.

---

## BLOQUE 3 — LOS ONCES Y EL PLAN

### El método, y en qué se diferencia del tuyo

| | Tu método | El nuevo |
|---|---|---|
| Qué mide | puntos por partido **jugado** | puntos esperados por partido **de su equipo** = tasa de juego × puntos por partido |
| Encogimiento | k = 3, a ojo | **k sacado de los datos** por posición: POR 8,6 · DEF 15,2 · MED 8,1 · DEL 5,6 |
| Mínimo de partidos | 3 jugados (deja fuera a 108) | ninguno: el encogimiento ya castiga la muestra corta |
| Titularidad | no | la tasa en el de la temporada; FutbolFantasy en el de la jornada |
| Calendario | no | medido; se aplica como prueba de sensibilidad y no cambia nada |

**Por qué es mejor, con los casos del encargo:**

- **La tasa arregla "premia al que juega poco y lo hace bien".** Pablo Durán vale **4,97** con tu
  método y **3,48** con el nuevo, porque juega el 71 % de los partidos de su equipo. Para la J8,
  FutbolFantasy lo deja en 1,46. Ceballos baja de 4,21 a **1,78** (juega el 43 %).
- **El k sale de los datos, no de un número a ojo.** Con la varianza real de un partido
  (7,8 a 13,3 puntos² según la posición: DEF 7,8 · MED 8,5 · POR 11,6 · DEL 13,3) y la
  dispersión real entre jugadores, **k = 3 encoge
  entre 2 y 5 veces menos de lo que dicen los datos**. Con 7 jornadas, el ruido pesa más de lo
  que suponía el k = 3.
- **Las unidades son distintas:** mis sumas son puntos esperados por jornada (con la tasa
  dentro), y las tuyas, puntos por partido jugado. Por eso las mías salen más bajas. No se
  comparan entre sí, solo cada una con la suya.

**Tu método, reproducido con mis datos:** A 51,6 · B 55,8 · C 76,7 · LIGA 85,3. Tus números:
A+B 51,6 · C 75,2 · LIGA 85,1. **C y LIGA casan; B no.** Mi B mete a Aubameyang (12,88 M), y tú
dices "único fichaje: Bardeli". Sospecho que tu B estaba limitado por la caja; no lo sé.

### Los tres onces (método nuevo, puntos esperados por jornada)

| Universo | Formación | Suma | Qué no es nuestro | Precio de eso |
|---|---|---|---|---|
| **A** tus 21 | 3-5-2 | **47,61** | — | — |
| **B** + mercado del Computer (41) | 3-4-3 | **52,36** | Hinojo, Bardeli, Aubameyang | 16,63 M |
| **C** alcanzable (432) | 3-4-3 | **63,31** | 9 de 11 (8 libres + Aubameyang) | 83,19 M |
| LIGA (548), solo como marcador | 3-4-3 | 70,69 | 10 de 11, **9 de rivales** | 110,63 M |

**A:** Dmitrovic · Chust, Jonny, Maffeo · Olasagasti, Expósito, Pablo Ibáñez, Unai López, Antonio
Blanco · Yamal, Jutglà. Respecto a tu método, **salen Yeray, Ceballos y Pablo Durán y entran
Maffeo, Unai López y Blanco**. Es el once que Pepe alineó hoy **salvo un defensa: Maffeo en
lugar de Cabrera**, que ha jugado 4 de 7 (valor 1,80 contra 2,45).

**C:** Unai Simón · Lago, Koski, Laporte · Moleiro, Dani Olmo, Olasagasti, Rodri · Raphinha,
Yamal, Aubameyang.

**La distancia de A a C son 15,7 puntos por jornada**, y casi toda está en 8 jugadores libres
que hoy no se pueden comprar: Raphinha (11,01), Moleiro, Dani Olmo, Unai Simón, Rodri, Lago,
Koski y Laporte.

**El once de la JORNADA 8 con lo que tienes** (FutbolFantasy donde lo hay): el mismo 3-5-2, suma
42,77. Jonny baja a 2,05 porque FutbolFantasy le da menos titularidad que su tasa.

### El plan, con la caja y las fichas de hoy

> **NO SE EJECUTA, Y SU SUPUESTO ERA FALSO (corregido el mismo 26/09).** Con el saldo en rojo,
> lo cobrado por una venta **no llega** a la caja de fichar si la oferta ya estaba en la
> garantía. Medido: anoche entraron 3.670.800 y la caja bajó 2.218.802. Con eso, el plan real es
> **una sola compra, Balliu, +0,12**, y vender a Jonny no cabe. Además, B y C llevaban a
> Aubameyang, que está lesionado. Todo está en `INFORME-LAS-CUATRO-CORTAS-2026-09-26.md`. Lo de
> abajo se queda como lo que es: **la mejor jugada posible con 1.356.676 € captura el 2,4 % de
> la distancia a C, y ese es el argumento.**

Supuestos, dichos: caja 1.356.676, 2 fichas libres (23 − 21), solo se vende **con oferta en
firme del Computer**, **sin pérdida** (oferta ≥ lo que costó; con coste desconocido no se
vende: 10 de 17 lo tienen), nunca a Yamal, y **lo que entra por una venta vuelve entero a la
caja**. Esto último es un supuesto: con el saldo en rojo, no sé cuánto de una venta llega
realmente a la caja de fichar.

```
1. vende Jonny (oferta 2.106.200) y compra Hinojo (1.690.000)   +0,245   2 escrituras
2. compra Balliu (750.000)                                        +0,121   1 escritura
                                                                  ------
                                            47,61 -> 47,98       +0,37    3 escrituras
caja al final 1.022.876 · fichas al final 1
```

**Sin tope de caja:** Hinojo (vendiendo a Jonny), Bardeli y Aubameyang: 47,61 → 51,88.

**Contra tu "mejoran el once: cero":** con tu método, Balliu no entraba, porque tu A llevaba a
Yeray y a Ceballos. Con el nuevo, Maffeo es el defensa más flojo (2,45) y Balliu (2,57) lo
supera por poco. **Iker Luque**, tu mejor candidato, vale 1,83 con la tasa: juega 3 de 7.

**Lo que el plan NO hace:** no espera a que salgan los libres de C. El siguiente paso natural es
la cola de ayer con destino: vigilar que el Computer saque a Raphinha, Moleiro… y tener la caja
para cuando salgan.

---

## El interruptor (propuesta; no está en el código ni en el YAML)

**No he añadido `BORDALAS_EL_ONCE_OBJETIVO` al código:** hoy nada decidiría con él, y un
interruptor que no lee nadie sería un número bonito. El bloque, para cuando lo haya:

```yaml
      # Apagado. EL ONCE OBJETIVO: PRIMERO A DONDE VAS, DESPUES CUANTO CUESTA.
      #
      #   LO QUE HACE. Las compras dejan de preguntar "¿este mejora mi once?"
      #   una a una. Se calcula el once objetivo con lo ALCANZABLE (lo nuestro
      #   + el mercado del Computer + los libres; nunca los de rivales) y el
      #   plan es la secuencia de compras y ventas que mas once sube por euro,
      #   con la caja, las fichas, una escritura por ciclo, sin vender a
      #   perdida ni a Yamal.
      #
      #   EL VALOR DE UN JUGADOR: puntos esperados por partido de su equipo =
      #   tasa de juego x puntos por partido encogidos hacia su posicion, con
      #   k sacado de los datos (POR 8,6 · DEF 15,2 · MED 8,1 · DEL 5,6).
      #
      #   MEDIDO (26/09, panel de las 08:10, 548 jugadores):
      #       once A (lo nuestro)       47,61   3-5-2
      #       once C (alcanzable)       63,31   3-4-3   8 de 11 son libres
      #       plan con la caja de hoy   +0,37 en 3 escrituras
      #   El calendario (1.819 partidos, desviacion sobre la media propia):
      #   casa +0,22, rival flojo +0,19. Cambia 1 nombre en 1 once, un
      #   empate a 0,05. NO se usa para el once de la temporada.
      #
      #   LO QUE NO ESTA MEDIDO Y HAY QUE VIGILAR:
      #     - Que lo que entra por una venta llegue entero a la caja de
      #       fichar con el saldo en rojo. Es un supuesto del plan.
      #     - 7 jornadas: la tasa de juego de un recien llegado es ruidosa.
      #     - La titularidad de la JORNADA solo la tienen 143 de 548 hasta que
      #       se encienda BORDALAS_OBJETIVOS_EL_CATALOGO.
      #     - En produccion, n = 0: todo esto es en papel.
      BORDALAS_EL_ONCE_OBJETIVO: "1"
```

---

## Lo que cambió en el código

| Fichero | Qué |
|---|---|
| `src/analysis/el_once_objetivo.py` | **nuevo**, funciones puras: la desviación por contexto, el k de los datos, el encogimiento, el mejor once entre las siete formaciones y el plan. Nadie las llama para decidir |
| `scripts/el_once_objetivo.py` | **nuevo**, script de solo lectura que reproduce todos los números de arriba (`--panel` = el `status.json` del artefacto de las 08:10) |
| `src/analysis/test_el_calendario_se_mide_con_desviacion_v1.py` | **guardia nueva**, 24 comprobaciones. Midiendo en bruto se pone roja en 6 |
| `scripts/run_validation_gate.py` | la guardia, en la verja |

## Lo que no hice, y por qué

- **Ni una petición a Biwenger.** Los puntos partido a partido ya estaban en `fitness`.
- **No encendí `BORDALAS_OBJETIVOS_EL_CATALOGO`,** aunque es lo que da la titularidad a los 548.
  Es tuyo.
- **No añadí `BORDALAS_EL_ONCE_OBJETIVO` al código:** no hay nada que decida con él todavía.
- **No junté "la temporada pasada contra la forma de ahora".** El método nuevo **no usa la
  temporada pasada**: solo esta, encogida hacia la media de la posición. Si eso es mejor que
  mezclar las dos es justo lo que mide ese bloque, y merece su propia medición.
- **No medí la varianza** (el delantero que da 17 un día y 0 tres), ni la metí en el once de la
  jornada. Queda apuntada, como pedías.
- **No toqué** el once de producción, la reserva de solvencia, la regla del déficit, el Position
  Manager, el YAML ni ninguna constante.
- **No empujé.**

## Aviso aparte

- El panel de las 08:10 **no está en el repo**: lo leí del artefacto
  `bordalas-live-diagnostics-36222790559` de tu carpeta de descargas. El script lo pide con
  `--panel`.
- **La última foto cruda del catálogo en disco es del 19/09.** Para rehacer el bloque 1 con la
  J7 completa haría falta una foto posterior. No hay que pedir nada nuevo: basta con que el
  ciclo guarde una.
