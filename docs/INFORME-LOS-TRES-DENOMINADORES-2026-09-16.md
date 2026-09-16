# Los tres denominadores — informe

**Rama:** `ojeador/los-tres-denominadores` (desde `ojeador/conectar-el-pronostico`)
**Fecha:** 16/09/2026
**Verja:** 142/142 en verde, exit 0, salida a fichero
**Push:** NO. **Interruptor:** APAGADO.
**Escrituras contra Biwenger:** ninguna. Ningún umbral tocado.

---

## 0. La foto del 14/09 sí estaba en este disco

En el informe anterior dije que no la tenía y que «el `status.json` local es del
16/08». **Las dos cosas eran falsas**, y basta mirar los ficheros:

```
diagnostico/status.json            meta.generated_at 2026-09-14T18:12:01   69 targets
dashboard/data/status.json         meta.generated_at 2026-09-14T18:33:47   64 targets
dashboard-v8/public/.../status.json  ídem                                  64 targets
```

La foto de los 69 estaba en `diagnostico/`, generada a las 18:12 y bajada a las 18:20
(`diagnostico/ultima_foto.json`). Ninguna copia local es de agosto. Di por ausente un
dato que estaba en disco, y sobre esa ausencia construí medio informe.

Con ella todo lo que sigue está medido contra el número que produjo el motor, no
contra una reconstrucción.

**Y tu bloque 0 se confirma entero, incluida la parte contra nuestra propia serie:**

```
acquisition.targets   magnitud == price_increment / precio    69 de 69
scout.highlights      magnitud == (precio − ayer) / precio    15 de 15
market_gate.rate      == scout.mean_magnitude_percent         69 de 69
```

Los 15 destacados los comprobé **contra `price_history.json`**, no contra el
catálogo: Marcos Fernández 910.000 sobre 720.000 de ayer = +20,879 %, y el ojeador
dice +20,879 %. Quince de quince, a tres decimales. **Doctrina 57 sostenida: es un
eco, y el eco llega hasta el tercer decimal contra nuestro propio almacén.**

---

## 1. El nombre del fallo: dos vías comparten etiqueta

**No es ninguna de tus dos sospechas, y es una tercera.** El ritmo llegó, se leyó del
campo correcto, se usó, y **perdió un `max()`**.

### Los nueve, con el valor despejado de lo que publicó el motor

`EV` e `importe` vienen escritos en el rechazo; `p` sale de la curva y los rivales de
la misma foto. Con eso, `valor = importe + EV/p` no se reconstruye: se despeja.

```
jugador          precio    ritmo  racha   valor usado  = precio x           la vía    rinde
Marc Roca     3.370.000   +0,297     16     3.420.805    1,015076  COMPUTER_RESALE  0,1443 %
Starfelt      2.250.000   +0,889      7     2.283.916    1,015074  COMPUTER_RESALE  0,1443 %
Areso         2.010.000   +0,995     14     2.040.302    1,015076  COMPUTER_RESALE  0,1443 %
Gulácsi       1.670.000   +1,198      5     1.695.173    1,015074  COMPUTER_RESALE  0,1443 %
Hugo González 1.430.000   +0,699      1     1.451.559    1,015076  COMPUTER_RESALE  0,1443 %
Nacho Pérez   1.080.000   +0,926     12     1.096.284    1,015078  COMPUTER_RESALE  0,1444 %
Pedro Díaz      880.000   +4,545      2       968.282    1,100320      PRICE_TREND  0,9605 %
Riki Rodríguez  600.000   +1,667     14       611.866    1,019777      PRICE_TREND  0,1893 %
Marrero         380.000   +2,632      7       397.506    1,046068      PRICE_TREND  0,4411 %
```

**Primera corrección al encargo: no son nueve al 0,1443 %, son seis.** Los otros tres
—Pedro Díaz, Riki, Marrero— llevan cada uno su propio número, y son exactamente los
tres que cotizan por debajo del millón. La cadena funciona en tres de nueve.

### De dónde sale el 1,015076

```python
# player_value_engine.py — computer_resale_value
maximo = int((objetivo - exigido) * confianza)
# objetivo = precio x (1 + prima),  exigido = ganancia x 0,25
```

```
prima mediana del Computer     2,01 %     (n=140, la MISMA para todo el tablero)
valor por COMPUTER_RESALE      precio x (1 + 0,0201 x 0,75) = precio x 1,015075
probabilidad a precio+1        0,095739   (curva y 7 rivales: iguales para todos)

rendimiento = 0,095739 x 0,015075 = 0,1443 %
```

**Ninguno de los dos factores contiene nada de ese jugador. Por eso es constante.**

### El fallo, con su nombre

```python
# player_value_engine.py:1735 — computer_resale_value devuelve
"intent": "SPECULATION",
"route": "COMPUTER_RESALE",

# acquisition_valuation.py:1194
mejor = max(opciones, key=lambda o: safe_int(o.get("value")))
...
"intent": clase["intent"] if DEPLOYMENT_ENABLED and clase["intent"]
          else mejor.get("intent"),
```

> **Dos vías distintas devuelven `intent: "SPECULATION"`, y sólo una de ellas proyecta
> el ritmo del jugador. Compiten en un `max()` por valor; la que gana presta su
> `value` y su `intent`. Cuando gana `COMPUTER_RESALE`, `optimal_bid` ve
> `intent == SPECULATION`, le aplica el listón del 3 % y escribe «Como especulación
> rinde un…» sobre un número que es la prima del Computer.**

**La prueba de que no es «no llegó el ritmo»**, en la misma foto:

```
Marc Roca   ritmo +0,297 %/día, 16 días de racha    ->  0,1443 %
Veiga       ritmo −1,187 %/día, PRECIO_CAYENDO      ->  0,1443 %
Mayoral     ritmo −1,852 %/día, sin intent          ->  0,1444 %
```

Veiga tiene `speculation_value = 0` —la vía de tendencia dice explícitamente que no
hay nada que especular— y aun así publica un «rendimiento de especulación». Un precio
que cae y uno que sube dan el mismo número. **El ritmo llegó; lo que falla es la
etiqueta.**

### Y algo peor que estaba debajo

```
techo de COMPUTER_RESALE con p = 1     1,5075 %
listón exigido                         3,0000 %
```

El 3 % se le aplica a una vía **cuyo máximo aritmético es la mitad**. No es que ese
día no pasara nadie: **es que por esa vía no puede pasar nadie, nunca, a ningún
precio.** El listón está pensado para la vía de tendencia y se está cobrando sobre
otra.

**No lo he tocado.** Es aritmética del motor y mueve dinero.

---

## 2. El plazo, los días planos, y el 99,2 %

### Antes de la tabla: el 99,2 % estaba medido sobre plazos mezclados

`medir_persistencia` recorría la lista de precios de cada jugador y tomaba posiciones
adyacentes como si fueran días seguidos. **No lo son.**

```
al almacén le falta el 07/09 ENTERO
y cada día tiene entre 366 y 579 jugadores de los 623
```

```
pares adyacentes-en-la-lista (plazo MEZCLADO)   15.107
pares en días consecutivos   (plazo 1 DÍA)      12.615
   se caen por no ser días consecutivos          2.492   (16 %)
```

**Doctrina 53, y era mía.** Un par que cruza el agujero mide tres días y se publicaba
como uno. Corregido, el número **sube**: sobre el mismo denominador de antes —sólo los
pares que se movieron— la dirección pasa de **98,8 % con plazos mezclados a 99,4 % a
un día limpio**. Es decir: los pares de plazo largo eran justo los que más se giraban,
y estaban tirando el número hacia abajo. Se equivocaba por el lado prudente, pero eso
no se sabía antes de medirlo.

*(Los totales no son los 13.073 del encargo porque el almacén tiene dos días más: el
histórico llega ahora al 16/09.)*

### La tabla que pediste — PLAZO: UN DÍA, n = 12.615 pares, 623 jugadores

```
de los pares en que AYER SUBIÓ (cualquier cantidad)     n = 3.938
   hoy sube      n = 3.716    94,4 %
   hoy plano     n =   112     2,8 %
   hoy baja      n =   110     2,8 %

de los pares en que AYER SUBIÓ ≥ 1 punto                n = 2.438
   hoy sube      n = 2.379    97,6 %
   hoy plano     n =    47     1,9 %
   hoy baja      n =    12     0,5 %

de los pares en que AYER BAJÓ (cualquier cantidad)      n = 5.949
   hoy sube      n =   101     1,7 %
   hoy plano     n =   144     2,4 %
   hoy baja      n = 5.704    95,9 %

de los pares en que AYER BAJÓ ≥ 1 punto                 n = 4.240
   hoy sube      n =    24     0,6 %
   hoy plano     n =    91     2,1 %
   hoy baja      n = 4.125    97,3 %

de los pares en que AYER SE QUEDÓ PLANO                 n = 2.728
   hoy sube      n =   126     4,6 %
   hoy plano     n = 2.380    87,2 %
   hoy baja      n =   222     8,1 %
```

### **Los 6.090 no son lo que pensabas, y la medición gana**

Tu hipótesis era que los que faltan son días en que hoy no se movió, y que por tanto
el 99,2 % real sería «alrededor del 53 %».

**No.** Los pares que se caían del denominador se caían por **ayer**, no por hoy:

```
|ayer| ≥ 1 punto                       n = 6.678
   ... de los que hoy NO se movió      n =   138   (2,1 %)

misma dirección / solo los que se movieron   99,4 %  (n=6.540)   <- el «99,2 %»
misma dirección / TODOS los pares            98,8 %  (n=6.678)   <- el honesto
```

**El día plano existe, pero es el 2,1 % de la muestra, no el 47 %.** Los 6.090 que
faltaban son pares donde **ayer** se movió menos de un punto —sobre todo los 2.728 en
que ayer no se movió nada—. Están en el *condicionante*, no en el resultado.

Y ahí sí aparece tu intuición, en otro sitio: **cuando ayer se quedó plano, hoy se
queda plano el 87,2 % de las veces.** El dinero parado se queda parado. Pero ese grupo
nunca entró en el 99,2 % ni debía entrar.

> **El factor honesto es 98,8 % de dirección y 0,9231 de tamaño, a un día, sobre
> n = 6.678 contando los días planos.** La constante del módulo era 0,934. La
> diferencia es de un 1,2 %.

### El plazo: 99 % ¿a un día o al horizonte del libro? — A un día

```
plazo    n        sigue    plano   se gira    factor acumulado
1 día    6.678    97,4 %    2,1 %     0,5 %       0,923
3 días   5.371    96,1 %    1,2 %     2,6 %       2,554
7 días   3.154    90,7 %    0,2 %     9,1 %       5,251
```

**Tres números distintos, y el libro trabaja a tres días.** A un día la dirección es
97,4 %; a siete, 90,7 % — el 9,1 % que se gira a una semana es la parte que no se veía.

**Y una cosa que no buscaba y sale de aquí:** el motor proyecta con
`TREND_DECAY = 0,53` compuesto, y **se queda corto** al horizonte del libro.

```
plazo   ayer mediana   real a ese plazo   lo que el motor proyecta   real/proyectado
1 día      +2,083 %         +1,923 %              +2,083 %               0,92
3 días     +2,116 %         +5,405 %              +3,876 %               1,40
7 días     +2,186 %        +11,475 %              +4,668 %               2,46
```

Se equivoca por el lado prudente, que es el lado bueno, pero se equivoca. **No lo he
tocado:** es aritmética del motor y va en su propio encargo.

### ¿Se agota la racha? **No.** (plazo 1 día)

```
racha        n     hoy sigue   hoy plano   se gira   factor
1 día      811       96,5 %       3,2 %      0,2 %    1,089
2-3      1.670       98,0 %       1,9 %      0,2 %    0,924
4-6      1.774       96,7 %       2,5 %      0,8 %    0,889
7-10     1.162       97,9 %       1,3 %      0,8 %    0,865
11-15      793       97,1 %       2,1 %      0,8 %    0,947
16-25      468       98,5 %       1,1 %      0,4 %    0,918
26+          0    sin muestra
```

**La dirección no se agota: 96,5 % con un día de racha y 98,5 % con dieciséis a
veinticinco.** Los 22 días de Fermín siguen al 98,5 %, no se frenan. Lo que sí baja es
el **tamaño**: de 1,089 el primer día a 0,87-0,92 a partir del cuarto.

El tramo de 26+ sale **vacío** y se dice: mi racha se corta en cada agujero del
almacén, así que es un suelo. El motor, que lee la serie de Biwenger entera, ve rachas
de 29 y 50 días (Gordon, Kang-in Lee).

### El bloque 3 rehecho con el factor honesto

```
el listón son 3,0 %  (NO se toca)   ·   288 candidatos del informe del 05/09

factor 0,934   (la constante)               pasan 13    sin pronóstico 171
factor 0,9231  (honesto, con días planos)   pasan 13    sin pronóstico 171
factor 0,9419  (sin días planos)            pasan 13    sin pronóstico 171
```

**Los 13 siguen siendo 13.** El 1,2 % de diferencia no mueve a nadie: el último de la
lista rinde 3,67 % y el listón es 3,00 %.

**Pero esa tabla estaba calculada sin rivales, y eso sí lo cambia todo** — ver §3.

---

## 3. La masa de la curva, y Rubén García

### La masa real de cada peldaño (n = 72 pujas medidas)

```
peldaño    prima    corte   por construcción   masa real    n
   1      1,0000     0,05        0,1429         0,1944     14
   2      1,0052     0,20        0,1429         0,1944     14
   3      1,0222     0,40        0,1429         0,2083     15
   4      1,0323     0,60        0,1429         0,1944     14
   5      1,0622     0,80        0,1429         0,1528     11
   6      1,2109     0,95        0,1429         0,0417      3
   7      1,2449    0,995        0,1429         0,0139      1
                                 ------         ------     --
                                 1,0000         1,0000     72
```

**El peldaño de arriba (+24,49 %) está 10,3 veces sobrevalorado: lleva 14,29 % y le
corresponde 1,39 % — una puja de las 72, no diez.** Tenías razón, y de largo.

### Qué cambia en nuestras pujas (n = 24 del libro de pujas)

```
jugador             precio        puja    p 1/7    p masa    cambio
Kiko Femenía     1.150.000   1.229.925   0,5435    0,8953   +0,3518
Rubén García     2.680.000   2.873.240   0,5435    0,8953   +0,3518
Álvaro Carreras  1.250.000   1.426.025   0,5435    0,8953   +0,3518
Djené            2.360.000   2.409.001   0,1639    0,2289   +0,0651
Oriol Rey        1.120.000   1.122.020   0,0957    0,1178   +0,0221
...
n = 24 pujas.  cambio medio +0,0595   máximo +0,3518
```

Las tres de arriba son las de `XI_UPGRADE`: **creíamos comprar un 54 % de
probabilidad y estábamos comprando un 90 %.**

### Rubén García — con una curva y con la otra

```
precio de mercado   2.680.000
our_value           3.097.172
lo que se pagó      2.873.240   (+7,21 %, +193.240 EUR)
compuerta           PRECIO_CAYENDO, −1,24 %/día, racha −7
rivales de verdad   NINGUNO

por construcción 1/7  ->  pujar 2.846.697  (+6,22 %)  p = 0,5435
por masa real         ->  pujar 2.846.697  (+6,22 %)  p = 0,8953
```

> **La puja no cambia. Ni un euro.**

**Segunda corrección al encargo: no son dos fallos vistos desde dos sitios. Son dos
fallos.** La masa cambia la probabilidad que *creemos* estar comprando (0,54 → 0,90),
no el importe: `candidate_bids` propone los mismos importes —los peldaños no se
mueven, sólo sus pesos— y el que maximiza el valor esperado sigue siendo el mismo.

**De dónde viene entonces el sobreprecio de Rubén García:** la puja elegida es
`2.680.000 × 1,0622 + 1`, justo por encima del **quinto peldaño** — el percentil 80
de las primas de la liga. Sube hasta ahí porque `our_value` está un 15,6 % por encima
del mercado y **la vía `XI_UPGRADE` no tiene tope de prima**: `PRIMA_MAXIMA_DE_PUJA`
(+0,25 %) sólo se aplica a `SPECULATION`. **El dinero no lo puso la curva: lo puso un
techo que existe para una vía y no para la otra.**

*(Nota de `n`: dos compras. Y el +213.240 € del informe del 15/09 está medido contra
el precio del día de la compra, 2.660.000; contra el `market_price` del libro,
2.680.000, son +193.240 €. Misma compra, dos denominadores — doctrina 54 otra vez.)*

### **Lo que no busqué y es lo más importante de todo el encargo**

La tabla de los 13 candidatos estaba calculada **sin rivales** (p = 1). Con los siete
rivales creíbles de la misma foto:

```
escenario                                          pasan el 3 %
sin rivales (p = 1) — el TECHO                          13
7 rivales, curva por construcción 1/7                    0
7 rivales, curva por MASA REAL                           0
```

Y no es cuestión de esa foto. Es aritmética, e independiente del precio:

```
ritmo máximo proyectable        4,53 %/día   (MAX_PROJECTED_DAILY_RATE)
valor máximo a 3 días           precio x 1,06301
puja máxima                     precio x 1,00250   (PRIMA_MAXIMA_DE_PUJA)
margen bruto máximo             6,04 %

para llegar al 3 % hace falta   p ≥ 0,4970
p a la puja máxima, 1/7         = 0,0957   ->  rinde 0,58 %   NO LLEGA
p a la puja máxima, masa real   = 0,1178   ->  rinde 0,71 %   NO LLEGA
```

> **Con siete rivales creíbles, la vía `SPECULATION` no puede alcanzar el 3 % para
> nadie, a ningún precio, con ningún ritmo que el motor sea capaz de proyectar.**
>
> El tope de puja (+0,25 %) y el listón de rendimiento (3 %) se contradicen: el
> primero impide comprar la probabilidad que el segundo exige. **Encender el ojeador
> no cambia esto.** Por eso la foto del 14/09 dice `biddable: 0` y `actionable: 0`.

**No he tocado ni el tope ni el listón.** Los dos están en la lista de lo que no se
toca, y la decisión de cuál de los dos cede es tuya. Pero con esto delante,
**encender el interruptor hoy no abriría ni una compra.**

---

## 4. El ojeador deja de ser una dependencia

La magnitud es nuestro propio `price_increment`, así que la estimación sale del
almacén. `estimacion_desde_el_historico` la calcula sin tocar la red.

```
los 69 candidatos de la foto del 14/09, contra NUESTRA serie:

   con pronóstico propio       31
   sin pronóstico              38
   sin serie nuestra            0
   DISCREPAN con el ojeador     0

persistencia usada: 0,9231  (n=6.678, plazo 1 día)
```

**Cero discrepancias en los 69.** Mientras siga así, las tres webs son un eco.
`contraste_con_el_ojeador` está puesto justo para el día en que dejen de serlo: si
alguna vez difiere de nuestro precio, lo grita con los dos números.

### Los 171 «sin pronóstico»: **no**, y hay un hueco que no habíamos visto

```
candidatos del informe del ojeador (05/09):  288
   SIN pronóstico   171   (59 %)

   de esos, con incremento = 0      85
   de esos, con incremento ≠ 0      86   <- NO son los de incremento cero
```

**La mitad de los silenciados sí se mueven.** Y no poco:

```
Raphinha          incremento  +170.000   magnitudes [0,921, 0,913, 0,913]
Mikel Rodríguez   incremento  −150.000   magnitudes [−5,976, −6,356, −6,356, 70,0]
Fermín            incremento  +120.000   magnitudes [0,889, 0,881, 0,881]
Bellingham        incremento  +110.000   magnitudes [0,626, 0,622, 0,622]
Budimir           incremento   +70.000   magnitudes [0,653, 0,649, 0,649]
Joan García       incremento   −70.000   magnitudes [−0,746, −0,752, −0,752]
```

El recorte por error de tamaño los mata: COMUNIATE se equivoca 0,93 puntos y Raphinha
se mueve 0,92, así que `1 − 0,93/0,92 < 0` y la fuente pesa cero. Las tres fuentes
pesan cero y sale `SIN_PRONOSTICO`.

> **El silencio no describe al jugador: describe a la fuente.** Y describe mal, porque
> el error de tamaño con el que se recorta (±3,98 / ±1,12 / ±0,93) está medido sobre
> una muestra distinta que el acierto de dirección — la doctrina 54 que dejé escrita y
> sin arreglar en el informe anterior, y que ahora se sabe a quién deja fuera.

**Fermín es el caso que lo resume:** 22 días de racha según el motor, +120.000 € en un
día, y el estimador basado en el ojeador dice «no sé nada de él». Nuestra propia serie
lo sabe exactamente.

---

## 5. Lo que queda en el repo

```
src/analysis/los_tres_denominadores.py             la medición. Ni disco, ni red, ni reloj
scripts/los_tres_denominadores.py                  el informe entero, por bloques
src/analysis/test_los_tres_denominadores_v1.py     16 guardias
scripts/run_validation_gate.py                     +1 en la lista (142)
```

```
python -m scripts.los_tres_denominadores
python -m scripts.los_tres_denominadores --bloque 2
```

| guardia | qué pasa si se rompe |
|---|---|
| `test_el_valor_de_reserva_grita` | vuelve un valor constante disfrazado de estimación, y en silencio |
| `test_la_persistencia_cuenta_los_dias_planos` | el factor vuelve a quitar los días planos del denominador |
| `test_el_ojeador_funciona_sin_red` | sin las tres webs se inventa un número en vez de decir que no sabe |
| `test_el_plazo_de_cada_par_esta_garantizado` | un par que cruza un agujero se publica como de un día |
| `test_el_horizonte_largo_exige_todos_los_dias` | el plazo de 3 días se mide sobre menos de 3 días |
| `test_la_racha_se_corta_en_el_agujero` | rachas de veinte días que nunca existieron |
| `test_la_masa_de_la_curva_no_es_un_septimo` | el peldaño del +24,5 % vuelve a valer 1/7 |
| `test_la_masa_no_se_inventa_sin_muestras` | sin muestra se publica una masa igualmente |
| `test_la_tabla_suma_cien_y_lleva_su_n` | hay pares que no se cuentan en ninguna fila |
| `test_la_racha_se_mide_por_tramos_y_los_vacios_se_dicen` | un tramo sin muestra hereda el número del de al lado |
| `test_una_discrepancia_con_el_ojeador_se_grita` | el día que difieran de nuestro precio, nadie se entera |
| `test_un_movimiento_de_redondeo_no_es_un_pronostico` | un +0,5 % pasa por señal |
| `test_la_serie_por_dia_no_mira_el_reloj` | la medición depende de la máquina donde corre |
| `test_un_tablero_sano_no_dispara_el_aviso` | el aviso grita siempre y deja de distinguir |
| `test_dos_jugadores_con_el_mismo_ritmo_no_son_sospechosos` | el motor funcionando se toma por avería |
| `test_el_fixture_trae_de_todo` | **regla 24** |

**Probadas reintroduciendo el fallo, en memoria y sin tocar el fichero:**

```
el factor vuelve a tirar los días planos   ->  test_la_persistencia_cuenta_los_dias_planos
el valor de reserva no grita               ->  test_el_valor_de_reserva_grita
la lista de candidatos vacía pasa          ->  test_el_valor_de_reserva_grita
sin histórico se inventa un número         ->  test_el_ojeador_funciona_sin_red  (+1)
el plazo se deja de garantizar             ->  test_el_plazo_de_cada_par...      (+1)
la masa vuelve a ser 1/7                   ->  test_la_masa_de_la_curva_no_es_un_septimo
```

Ninguna guardia lee `data/`, sale a la red ni mira el reloj: las series son fixtures
con fechas escritas a mano y el huso entra por argumento.
`scripts/guardias_que_leen_el_mundo` la da limpia.

---

## 6. Lo que NO hice, y por qué

- **No encendí nada.** `ENCENDIDO = False`, con su guardia de antes.
- **No toqué ningún umbral**: ni el 3 %, ni la curva de primas, ni el cupo, ni el
  suelo, ni el tope, ni `bid_cap`, ni `PUEDEN_ENCERRARLO`, ni
  `MAX_SINGLE_SPECULATION_PERCENT`, ni `MAX_SAFE_DEBT`, ni `PRIMA_MAXIMA_DE_PUJA`.
- **No toqué la curva de pujas.** El bloque 3 dice «sólo medir» y sólo he medido: la
  masa real se publica **al lado** de la de construcción, y `calibrate_premium_curve`
  sigue devolviendo 1/7.
- **No toqué la puja de `XI_UPGRADE`** ni el hecho de que no tenga tope de prima,
  aunque §3 apunta a que ahí está el dinero de Rubén García.
- **No arreglé el `intent` compartido de `computer_resale_value`.** Es el fallo del
  bloque 1 y tiene nombre, pero cambiarlo mueve qué vía decide: es una decisión tuya.
- **No arreglé el `TREND_DECAY = 0,53`**, que se queda un 40 % corto a tres días y un
  146 % corto a siete. Es el acelerador del motor.
- **No arreglé el denominador mezclado del libro de acierto** (±3,98 contra 89,1 %).
  Sigue pendiente del informe anterior, y ahora se sabe que es quien silencia a
  Raphinha, Fermín y Bellingham.
- **No metí el equipo ni la clasificación. No toqué el workflow. No empujé.**
- **No pude medir el tramo de racha de 26+ días**: mi racha se corta en cada agujero
  del almacén y ninguna llega. Está dicho como vacío, no interpolado.

### Lo que contradijo al encargo, y ganó la medición

1. **No son nueve al 0,1443 %, son seis.** Tres llevan su propio número.
2. **Los 6.090 no son días planos de hoy**, son pares donde ayer no se movió. El día
   plano de hoy es el 2,1 %, no el 47 %, y el factor honesto es 98,8 %, no 53 %.
3. **La curva y Rubén García no son el mismo fallo.** Con la masa real la puja sale
   idéntica al euro; lo que cambia es la probabilidad que creemos comprar.
4. **Los 171 «sin pronóstico» no son los de incremento cero.** La mitad se mueven.

### Y lo que hay que decidir antes de encender

**Con siete rivales creíbles, la vía de especulación no llega al 3 % para nadie.** El
ojeador enchufado, la persistencia honesta y la masa corregida no abren ni una compra
mientras el tope de puja siga en +0,25 % y el listón en 3 %.

**Esa es la tabla que pedías tener delante.**
