# EL ORDEN DE LA CESTA Y EL 63 % DEL MERCADO

**Fecha:** 2026-09-20 (cuarto del día) · **Rama:** `medir/el-orden-y-el-mercado`, desde
`medir/por-que-relleno` · **Escrituras contra Biwenger:** ninguna · **Orden de la
cesta: sin tocar** · **`MERCADO_DE_RIVAL`: sin abrir** · **Umbrales tocados:**
ninguno · **Interruptores encendidos:** ninguno.

**Verja: 162 de 162.**

---

## PRIMERO: UN ERROR MÍO DE AYER, Y ES EL EJE DEL BLOQUE 1

Ayer escribí, y tú lo citaste como doctrina 97:

> «lo que desempata, `win_odds`, es máximo justo donde no hay rival: en lo que nadie
> quiere.»

**Es falso, y lo peor es cómo lo hice.** Para ilustrar el efecto inventé una columna
de `win_odds` (0,95 para 150.000 … 0,10 para 24,9 M), la puse en una tabla junto a
números medidos, y al día siguiente la leí como si fuera una medición. Doctrina 90,
sobre un número que me había dado yo mismo.

Medido de verdad, `probabilidad_de_llevarselo` sube con el precio en tres escalones:

```
   < 1.500.000            0,46   (n=24)
   1.500.000 - 3.000.000  0,61   (n=18)
   >= 3.000.000           0,78   (n=32)
```

**Ganamos el 78 % de las subastas caras y el 46 % de las baratas.** Lo contrario de
lo que escribí.

Lo que sí sigue en pie es el hallazgo: el ratio se cancela. Pero la conclusión que
saqué de él —«el orden es el más barato primero»— no se sostiene, y el bloque 1
cambia entero por eso.

---

## BLOQUE 1 — EL DESEMPATE DE LA CESTA

### Las doce líneas

[`la_subasta.py:870`](src/analysis/la_subasta.py#L870), cuerpo sin docstring:

```python
    puja = safe_int(candidato.get("bid"))

    if puja <= 0:
        return -1.0

    ganancia = safe_float(candidato.get("expected_value"))

    if contar_la_pelea:

        odds = candidato.get("win_odds")

        if odds is not None:
            ganancia *= safe_float(odds, 1.0)

    return ganancia / puja
```

### El ratio se cancela. Confirmado sobre candidatos reales

No sobre precios inventados: sobre **los que la cesta vio de verdad**, leídos con
`lectura_del_estado` —el mismo filtro que usa el motor— en los dos días con foto.

| día | candidatos | precios | valores distintos de `_por_euro` | dispersión |
|---|---:|---|---:|---:|
| 18/09 | **n = 18** | 240.000 → 6.910.000 (**29×**) | 5 | **0,019 %** |
| 20/09 | **n = 16** | 150.000 → 7.100.000 (**47×**) | 7 | **0,034 %** |

```
      precio        puja   ganancia    por euro
     150.000     150.376      3.134    0.020841
   1.600.000   1.604.001     33.439    0.020847
   4.720.000   4.731.801     98.647    0.020848
  24.900.000  24.962.251    520.409    0.020848
```

La cuenta lo explica sin margen: `expected_value = precio × (1 + prima) − precio ×
(1 + 0,0025) − 1`, así que el precio está arriba y abajo. **Doctrina 97 confirmada.**

### Pero el ratio no es lo que ordena

`elegir_la_cesta` ordena por `-round(_por_euro(c, contar_la_pelea=True), 4)` y sólo
entonces desempata por `bid` **ascendente**. Con `contar_la_pelea=True` por defecto,
que es como lo llama `plan_del_reset`. Y con los `win_odds` medidos:

```
   >= 3 M     0,020848 x 0,78 = 0,016261  ->  0,0163
   1,5 - 3 M  0,020847 x 0,61 = 0,012717  ->  0,0127
   < 1,5 M    0,020841 x 0,46 = 0,009587  ->  0,0096
```

> **El orden efectivo de la cesta ya pone primero a los caros, por tres escalones bien
> separados. El desempate por el más barato sólo actúa DENTRO de un escalón —que es
> donde el ratio empata de verdad— y es una decisión del 11/09 con su motivo escrito:
> «el primer intento se llevó al más caro, gastó el presupuesto entero en UNA puja y
> dejó 17 fuera».**

Y encaja con lo que hizo: el 15/09 la cesta pujó **primero por Balde (1.604.001)** y
sólo en la segunda vuelta por los tres de 150.376. El caro fue primero.

### La tabla de los tres órdenes

Misma reja para los tres —fichas libres, tope de la ventana, tope por club—, sólo
cambia la clave. «Neto» es el esperado, y lo doy dos veces: con la prima única que usa
el modelo y con **la prima medida por tramo** (abajo).

**18/09** · 18 útiles · 3 fichas · tope de la ventana **3.234.502**

| orden | pujas | compromete | esperado (modelo) | esperado (prima medida) |
|---|---:|---:|---:|---:|
| **HOY** (ratio × pelea, luego el más barato) | 1 — Cabrera 3,04 M | 3.047.601 | 49.557 | **56.441** |
| **por beneficio absoluto** | 1 — Cabrera 3,04 M | 3.047.601 | 49.557 | **56.441** |
| **por puntos que suma** | 2 — Pepelu, Osorio | 3.167.902 | 35.044 | 27.954 |

**20/09** · 16 útiles · 9 fichas · tope de la ventana **1.950.080**

| orden | pujas | compromete | esperado (modelo) | esperado (prima medida) |
|---|---:|---:|---:|---:|
| **HOY** | 3 — Yeray, Diaby, Guevara | 1.934.828 | 23.632 | **18.784** |
| **por beneficio absoluto** | 2 — Yeray, Van Oevelen | 1.854.627 | 22.864 | 18.390 |
| **por puntos que suma** | 2 — Denis Suárez, Aitor Fernández | 1.854.627 | 15.240 | 11.755 |

> **Tu propuesta, medida: idéntica el 18/09 y ligeramente peor el 20/09.**

El motivo es que en los dos días **el que manda no es el orden: es el tope de la
ventana**. El 18/09 sólo cabe una puja de 3 M en 3.234.502 €, y las dos claves eligen
la misma. Ordenar distinto no cambia lo que cabe.

### El neto, contra los +3.366 medidos

Con honestidad sobre lo que **no** puedo hacer: no tengo ninguna foto de dentro de la
ventana. Las dos que hay se toman después del reset, así que reproducen el tablero que
la cesta vería **la mañana siguiente**, no el que vio. Así que lo de arriba es lo que
habría hecho con esos candidatos, no una reejecución de aquellas mañanas.

Lo que sí es realizado, y es la referencia:

| | n | pagado | recuperado | neto | tasa |
|---|---:|---:|---:|---:|---:|
| las nueve cerradas | 9 | 2.896.844 | 2.900.210 | **+3.366** | **+0,12 %** |
| — de ellas, a precio de suelo | 8 | 1.292.843 | 1.321.710 | +28.867 | +2,23 % |
| — **Balde, la única grande** | **1** | 1.604.001 | 1.578.500 | **−25.501** | **−1,59 %** |

**Sobre operaciones grandes de la cesta el `n` es UNO, y perdió.** Ese es el
denominador real de toda esta discusión.

### El hallazgo que sí apoya tu instinto, por otro camino

Fui a medir si la prima que el Computer paga al recomprar depende del tamaño. **No es
plana.** Medido sobre **n = 194** ventas al Computer de toda la liga, fechadas contra
el precio de aquel momento:

| tramo de precio | n | prima mediana | media | % en verde | € medianos |
|---|---:|---:|---:|---:|---:|
| ≤ 250.000 | 30 | **+1,32 %** | +1,23 % | 77 % | 2.050 |
| 250.000 – 1.000.000 | 32 | +0,62 % | +1,42 % | 66 % | 3.250 |
| 1.000.000 – 3.000.000 | 63 | +2,00 % | +1,84 % | 76 % | 40.300 |
| 3.000.000 – 6.000.000 | 53 | +2,63 % | +2,50 % | 87 % | 106.800 |
| **6.000.000 +** | **16** | **+4,26 %** | +3,64 % | **94 %** | 353.600 |

`r = +0,215` entre `log10(precio)` y la prima, n=194.

Y el modelo mete **una sola mediana, +2,34 %, para todos**
([`la_subasta.py`](src/analysis/la_subasta.py#L526), `candidatos_en_modo_cartera`).

> **El ratio sale constante porque la entrada es constante.** La prima real del suelo
> es +1,32 %, no +2,34 %: sobre una puja de +0,25 % el margen verdadero es **1,07 %,
> la mitad de lo que el modelo cree**. Y arriba de 3 M el margen real es 2,4–4,0 %, el
> doble.

Con la prima por tramo, **el ratio se ordenaría solo** y en la dirección que tú
propones, sin tocar el desempate. Eso es un cambio de un dato de entrada, no de un
criterio de orden.

El `n` manda en cómo se lee: el tramo de 6 M+ son **16 ventas** y es una dirección, no
una tasa (doctrina 55). El tramo 250 k–1 M rompe la monotonía. Lo que aguanta es lo
de abajo contra lo de arriba: **≤ 1 M rinde +0,62 a +1,32 % (n=62) y ≥ 1 M rinde +2,00
a +4,26 % (n=132)**.

### El riesgo de desempatar por beneficio absoluto, nombrado

**1. La concentración, que ya mordió una vez.** El comentario del 11/09 en
`elegir_la_cesta` lo cuenta: ordenar por lo que gana más se llevó al más caro, gastó
el presupuesto entero en una puja y dejó 17 candidatos fuera. Medido hoy: el 20/09 la
cesta baja de **3 pujas a 2**. Con perder gratis y veinte jugadores cada mañana, menos
tiros es peor.

**2. Perder es gratis; GANAR no.** La tesis de la cesta —«perder no cuesta nada»— es
cierta para la puja y falsa para la compra. Una puja grande ganada inmoviliza una
ficha y caja de verdad, y la única medición que tenemos por encima del suelo es
**Balde: n=1, −25.501 €**.

**3. El tope de la ventana se volvería el único freno.** `tope_de_la_ventana` =
`min(presupuesto, caja_libre / 0,05)`. Con el orden de hoy, el presupuesto se reparte
entre varios; con beneficio absoluto, la primera puja se lo come. Los límites que
citas —`MAX_SINGLE_SPECULATION_PERCENT`, el cupo, el presupuesto— acotan **cada
operación**, no la concentración de la cartera. No hay hoy ningún límite que diga
«no más del X % de la ventana en una sola puja».

**4. Y el riesgo de segundo orden, que es el que más me preocupa:** cambiar el orden
sin cambiar la prima deja el criterio siendo una constante. Se estaría cambiando el
desempate de una lotería, no el criterio.

**Mi recomendación, y la decides tú:** no toques el desempate. Toca la **prima**: que
`candidatos_en_modo_cartera` reciba la prima del tramo del jugador en vez de una
mediana única. Con eso el ratio deja de ser constante, ordena por tamaño solo, y el
desempate por capacidad del 11/09 sigue haciendo su trabajo donde debe. Es un dato de
entrada medido con n=194, no un umbral nuevo.

### La guardia

`src/analysis/test_el_orden_distingue_tamano_v1.py`, **5 pruebas, en la verja**. No
lee `data/`, ni `diagnostico/`, ni la red, ni el reloj.

| prueba | qué exige |
|---|---|
| `test_sin_tamanos_distintos_no_se_comprueba_nada` | la muestra tiene ≥3 precios y el mayor es ≥10× el menor — **falla si todos valen lo mismo**, como pediste |
| `test_el_ratio_por_euro_no_depende_del_tamano` | fija el hallazgo: si alguien hace que el ratio SÍ dependa del precio, salta y obliga a leer la cabecera |
| **`test_el_orden_distingue_tamano`** | 150.000 y 6.910.000, mismo ratio, **no pueden salir empatados** — y el caro va delante |
| `test_la_pelea_es_lo_unico_que_separa_hoy` | si alguien quita la pelea del criterio, la cesta vuelve a elegir por sorteo |
| `test_dentro_del_escalon_manda_el_mas_barato` | fija la decisión del 11/09, para que moverla sea un acto consciente |

---

## BLOQUE 2 — EL 63 % QUE NO MIRAMOS

### Dónde se corta, con su commit

**Dos sitios, no uno.**

**(a) El tablero**, [`acquisition_board.py:1283`](src/analysis/acquisition_board.py#L1283),
commit **`227acaf`, 2026-09-06**, *«mercado rivales: verlos primero»*. La fila pasa
por **todo** el camino de valoración y sólo al final:

```python
if de_rival_sin_dinero:
    fila["would_be_decision"] = fila["decision"]
    fila["would_pass"] = fila["decision"] == "BID"
    fila["would_bid"] = safe_int(fila.get("bid"))
    fila["decision"] = MERCADO_DE_RIVAL
    fila["bid"] = 0
```

**(b) La cesta**, [`la_subasta.py`](src/analysis/la_subasta.py#L153), en
`lectura_del_estado`, con su motivo escrito:

> «LA COMPRA A RIVALES SIGUE CERRADA. De 49 objetivos del 09/09, VEINTINUEVE son de
> mercado de rival. Pujar por uno es comprarle a un rival, que es una puerta que el
> dueño tiene cerrada. Se miran, no se pujan.»

### ¿Sigue vigente el motivo? Sí, pero ya no es el que era

El motivo declarado era que **la tasa de aceptación no está medida**. Eso sigue siendo
verdad y no se puede arreglar: el tablón publica lo que se cerró, nunca lo que se
ofreció y se rechazó. **No hay denominador**, y el propio código lo dice con esas
palabras.

Lo que **ya no** es cierto es la parte de «en esta liga nadie le vende a nadie».
`la_puerta_de_los_managers` —que existe desde el 14/09 justo para esto— lo mide:

```
10 traspasos de manager a manager   ·   207 compras al Computer
4 de los 10 son nuestros            ·   el ultimo, hace 1 dia
```

**No paro**, porque la puerta no está cerrada por una regla del juego: está cerrada
por una decisión tuya con un motivo que sólo cubre la mitad.

### ¿Es un corte o una puerta? Sabe hacerlo y no lo hace

**Sabe.** Tres cosas, medidas:

1. `BiwengerWriteClient.place_bid` acepta **`seller_user_id`**
   ([write_client.py:274](src/biwenger/write_client.py#L274)). El camino de escritura
   a un manager existe y está construido.
2. Ya lo hemos cruzado **cuatro veces esta temporada**, aunque a mano.
3. El tablero calcula y guarda **`would_be_decision`, `would_pass` y `would_bid`** en
   cada fila cortada: sabe exactamente qué habría hecho.

No es un corte de capacidad. Es una puerta con la llave puesta por fuera.

### Los diez traspasos, uno a uno

| fecha | jugador | de | a | importe | sobre mercado |
|---|---|---|---|---:|---:|
| 10/08 | Kike Barja | Manzagool | Prinzipote | 330.000 | — |
| **19/08** | **Cepeda** | Prinzipote | **Pepe Bordalás** | **463.500** | **+0,8 %** |
| **19/08** | **Javi Hernández** | **Pepe Bordalás** | Pollo17 | **1.250.000** | **+23,8 %** |
| **24/08** | **Castrín** | **Pepe Bordalás** | Pollo17 | **1.346.045** | **+32,0 %** |
| 28/08 | David Soria | Pollo17 | Luismi_Haz | 6.250.000 | +9,6 % |
| 28/08 | Laporte | Luismi_Haz | Pollo17 | 5.450.000 | +0,2 % |
| 28/08 | Brugué | Luismi_Haz | Pollo17 | 700.000 | +59,1 % |
| **04/09** | **Yusi Enríquez** | **Pepe Bordalás** | Prinzipote | **1.226.068** | **+7,5 %** |
| 15/09 | Marcos Llorente | Pollo17 | Á. Retamosa | 5.700.000 | +1,8 % |
| 18/09 | Jonathan David | Luismi_Haz | Pollo17 | 8.400.000 | +5,4 % |

Los cuatro nuestros: **vendimos tres** (+23,8 %, +32,0 %, +7,5 % sobre mercado) y
**compramos una** (+0,8 %). Las tres ventas están entre las cuatro mejores primas de
los diez. `n = 4`, y con ese `n` no se declara una habilidad — pero la dirección es la
buena y el hecho es que la puerta funciona.

El 28/08 hubo **tres traspasos en el mismo segundo** entre Pollo17 y Luismi_Haz: es un
intercambio pactado, no tres operaciones. Con eso, las operaciones distintas son **8**,
no 10. Doy las dos cifras.

### Cuántos de los 34-35 mejoran el once

Con la vara de su posición, la misma que usa `el_vestuario_libre` (`nos_suma` =
puntos − puntos del que ocupa hoy ese puesto):

| | 18/09 | 20/09 |
|---|---:|---:|
| cortados por `MERCADO_DE_RIVAL` | 34 de 54 | 35 de 55 |
| **mejoran el once** | **17** | **24** |
| … y su precio cabe en el bolsillo de fichar (6.754.533 €) | 13 | 20 |
| **lo que el tablero habría decidido con esos** | `would_pass`: **0** | `would_pass`: **0** |

**18/09 — los que mejoran y caben**

```
  jugador            pos  pts  vara  SUMA       piden     mercado  recargo
  Álvaro Valles      POR   49     0   +49   6.240.000   5.280.000    +18%
  David Soria        POR   42     0   +42   5.590.000   5.590.000     +0%
  De la Fuente       DEF   33    16   +17   4.990.000   4.190.000    +19%
  Hjulmand           MED   26    19    +7   5.690.000   4.760.000    +20%
  Javi Hernández     MED   26    19    +7   4.750.000   3.800.000    +25%
  Bardeli            MED   26    19    +7   3.190.000   2.290.000    +39%
  Castrín            DEF   23    16    +7   2.710.000   1.940.000    +40%
  ... 6 mas, de +5 a +2
```

**20/09 — los que mejoran y caben**

```
  De la Fuente       DEF   33     9   +24   4.990.000   4.270.000    +17%
  Álvaro Valles      POR   49    28   +21   6.240.000   5.500.000    +13%
  Veiga              DEF   28     9   +19   3.420.000   3.460.000     -1%
  Castrín            DEF   24     9   +15   2.710.000   2.080.000    +30%
  Starfelt           DEF   21     9   +12   2.532.000   1.960.000    +29%
  ... 15 mas, de +11 a +2
```

Y los que no caben, para que conste el tamaño de lo que hay detrás: **Fermín** (MED,
59 pts, **+40** sobre la vara, piden 15,6 M) y **Baena** (MED, 51 pts, **+32**, piden
12,55 M).

### El número que pediste: lo que cuesta tener esa puerta cerrada

Sólo se puede comprar uno a la vez, así que el coste no es la suma: es **la mejor
compra que hay detrás de la puerta, cada día**.

> **18/09: Álvaro Valles, portero, +49 puntos sobre la vara, piden 6.240.000 €, cabe
> en el bolsillo.**
> **20/09: De la Fuente, defensa, +24 puntos, piden 4.990.000 €, cabe.**

Contra esto: **el motor entero ha comprado 22 puntos en toda la temporada, en 16
operaciones, y los 22 son de un solo jugador.** Detrás de esta puerta, un martes
cualquiera, hay una sola compra de +49.

### Y hay una SEGUNDA puerta detrás, que no estaba en el encargo

`would_pass: 0` en los dos días. Ninguno pasaría el listón **aunque abrieras la
puerta**. Miré por qué, y el caso de Álvaro Valles lo dice entero:

```json
"name": "Álvaro Valles", "points": 49, "position": 1 (portero),
"intent": "SPECULATION",
"deployment": {"operation_class": "TRADE", "value_route": "HOLD",
               "reason": "No entra al once ni llena hueco:
                          se compra para revender"},
"budget_applied": 973594,  "budget_source": "ESPECULACION",
"would_be_decision": "SUPERA_PRESUPUESTO"
```

**Un portero con 49 puntos, cuando nuestro portero titular lleva 0, entra como
«especulación para revender» y se mide contra el bolsillo de especular —973.594 €— en
vez del de fichar —6.754.533 €.** Por eso sale `SUPERA_PRESUPUESTO` un jugador cuyo
precio cabe de sobra en el bolsillo correcto.

De los 13 que mejoran y caben el 18/09, **8 salen `SUPERA_PRESUPUESTO`**; de los 20 de
hoy, **9**. Es el mismo bolsillo equivocado.

Así que abrir `MERCADO_DE_RIVAL` hoy, sola, compraría **cero**. Son dos puertas en
serie, y la de dentro es la misma familia de fallo que llevamos toda la semana: **el
motor no reconoce una compra de puntos como una compra de puntos.**

**No he abierto ninguna de las dos.**

---

## BLOQUE 3 — LAS CUATRO QUE QUEDAN

### Las tres redes ven ya `diagnostico/`

Y la tercera no era un olvido: era un **permiso explícito**.

| red | dónde | qué se cambió |
|---|---|---|
| poblaciones | `regression_check.py:92` | criterio era sólo `get_latest_snapshot(`; ahora también `diagnostico/` |
| estática | `test_verja_determinista_v1` | `"diagnostico"` estaba en **`DEL_REPOSITORIO`**, declarado *«código versionado, igual en las dos máquinas»* — y está en `.gitignore:129`. Sale de ahí y entra en `LOS_ESTADOS` |
| en ejecución | `vigila_data/sitecustomize.py` | `_bajo_data` miraba sólo `data/`; ahora `("data/", "diagnostico/")` |

La estática pasa en verde, que significa que **ya no queda ninguna guardia nombrando
`diagnostico/`**. Y el vigilante en ejecución bajó de **32 a 31** lecturas censadas,
sin ninguna nueva.

### Las cuatro, al mirador

`scripts/mirar_contra_la_foto.py`, **8 comprobaciones, corre 8/8 limpio** contra la
foto de las 09:10 de hoy.

| guardia | se van | se quedan en la verja |
|---|---:|---:|
| `test_arbitro_v1` | 6 | **12** |
| `test_once_v1` | 1 | **22** |
| `test_reloj_solvencia_v1` | 1 | **17** |
| `test_venta_ejecutable_v1` | 0 | **14** |

`test_venta_ejecutable_v1` era **falsa alarma mía**: tenía `FOTO =
Path("diagnostico/status.json")` declarado y **no lo usaba en ninguna línea**. Línea
muerta, quitada.

### ¿Se puede impedir en general? Sí, y aquí está el coste

Lo medí antes de construir nada. Sobre las **1.925** pruebas `test_*` de `src/**`:

```
210 (10,9 %) pueden terminar sin ejecutar un solo `assert`,
             repartidas en 85 ficheros
```

**No se puede poner en rojo hoy**: la mayoría son legítimas —delegan sus afirmaciones
en un ayudante, o comprueban que algo NO lanza— y distinguirlas a máquina pide seguir
las llamadas, que es otra guardia.

Lo que **sí** se puede cercar sin falsos positivos es la forma exacta que falló: una
prueba de un fichero que lee el estado y sale por la puerta de atrás cuando el estado
no está. De esas quedaban 21 en 9 ficheros; después de mover las ocho de ayer y las
ocho de hoy, quedan **13 en 6**.

Así que la guardia es un **censo**, como hace la casa con `LEEN_DATA_HOY`:
`src/analysis/test_ninguna_pasa_con_las_manos_vacias_v1.py`, **4 pruebas, en la
verja**. Las 13 están listadas una a una **con su motivo**, el censo **sólo puede
encoger**, y cualquiera nueva la pone roja con su nombre.

**Lo que costaría bajarlo a cero:**

```
  test_futbolfantasy_source_v12   7   lee el HTML del proveedor y las fotos
  test_mercado_rivales_v1         2   lee las fotos
  test_doctrina_v1                1
  test_el_ciclo_publica_v1        1   comprueba si hay fotos
  test_la_pantalla_pinta_v1       1   ya esta retirada de la verja
  test_verja_determinista_v1      1   ES el vigilante, y es legitimo
```

**Siete de las trece son un solo fichero.** La salida es la misma que hoy: un mirador.
Una tarde, y no la he gastado porque no era el encargo.

Y la guardia se vigila a sí misma: si el barrido encontrara menos de 1.000 pruebas
—patrón roto— **falla**, en vez de dar todo por bueno.

---

## LO QUE NO HICE, Y POR QUÉ

- **No cambié el orden de la cesta.** El bloque 1 mide y propone; medido, tu propuesta
  no mejora y lo que sí mejoraría es la prima por tramo. Decides tú.
- **No toqué la prima** de `candidatos_en_modo_cartera`, aunque es donde está el
  problema. Mueve dinero.
- **No abrí `MERCADO_DE_RIVAL`, ni la segunda puerta** (el bolsillo con el que se mide
  a un fichaje clasificado como especulación).
- **No moví las trece que pueden irse de vacío.** Están censadas con su motivo y el
  coste de llevarlas a cero está arriba.
- **Ni una escritura contra Biwenger.** Ningún interruptor, ningún umbral, la ventana
  cerrada, el workflow sin tocar.
- **No pude reejecutar las mañanas de la cesta.** No hay ninguna foto de dentro de la
  ventana: las dos que existen se toman después del reset. Lo de arriba es qué haría
  con esos candidatos, no una reejecución.
- **No declaré nada sobre la tasa de aceptación de una oferta a un manager.** No tiene
  denominador y no lo va a tener: el tablón publica lo cerrado, nunca lo rechazado.

### La verja

```
162 de 162 OK      (eran 160 de 160; dos guardias nuevas)
```

Salida a fichero, árbol quieto, sin `git add -A`. **No empujo.**

### El `n`, y cuándo se cortó

| medida | `n` | corte |
|---|---|---|
| el ratio se cancela | **18** y **16** candidatos reales, 29× y 47× de rango | fotos 18/09 y 20/09 |
| `win_odds` por tramo | 24 · 18 · 32 | `rival_bid_model`, tal como lo publica |
| prima del Computer por tramo | **194** ventas fechadas | tablón a 20/09 |
| — tramo 6 M+ | **16**, dirección y no tasa | idem |
| la cesta, realizado | **9** cerradas · 1 grande | 12→18/09 |
| traspasos entre managers | **10** eventos · **8** operaciones · 4 nuestros | 10/08→18/09 |
| cortados que mejoran el once | 17 de 34 · 24 de 35 | dos fotos |
| pruebas que pueden irse de vacío | **210** de 1.925 · 13 de la forma cercada | barrido de `src/**` |

Los diez traspasos son **10 eventos y 8 operaciones**: el 28/08 hay tres en el mismo
segundo entre los mismos dos managers, que es un intercambio pactado. Doy las dos.
