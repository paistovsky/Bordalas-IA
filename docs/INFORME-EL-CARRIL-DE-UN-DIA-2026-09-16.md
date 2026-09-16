# El carril de un día — informe

**Rama:** `carril/el-de-un-dia` (desde `medir/el-viaje-al-computer`)
**Fecha:** 16/09/2026
**Verja:** 145/145 en verde, exit 0, salida a fichero
**Push:** NO. **`ENCENDIDO = False`.** Ninguna escritura, ningún umbral tocado.

---

## Lo primero: la ventana de un día no existe

El encargo —y mi informe de ayer— leían la curva como un reloj:

```
1 noche    n=11   +3,14 %   ganan 11 de 11
2 noches   n= 6   −4,13 %   ganan  2 de  6
```

**No es un reloj. Es un sesgo de selección, y se ve comparando dos distribuciones
de la prima del Computer:**

```
las 167 ventas que alguien ACEPTÓ      mediana  +2,37 %   pasan el listón  63 %
las 13 ofertas VIVAS sin aceptar       mediana  −0,50 %   pasan el listón  46 %
```

**El Computer no ofrece +2,37 %: ofrece una mediana negativa, y el 54 % de sus
ofertas están por debajo del precio de mercado.** El +2,37 % es lo que la gente
*acepta*. Se vende los días que la oferta viene buena y se espera los demás.

La prueba de que la lectura del reloj era falsa: si la oferta buena llegara el 46 %
de los días al azar, que Pollo acertara **diez de diez seguidas** tiene una
probabilidad del **0,04 %**. No corre contra un plazo — **espera a que la oferta
valga**. Sus otros 33 viajes son de 2 a 7+ noches.

> **La regla no tiene fecha de salida. Tiene un precio de salida.**

---

## BLOQUE 1 — Mi conclusión de ayer estaba mal

Dije que lo primero era dejar de pagar +4,23 % al entrar. **Ese número era de agosto.**

```
los 5 viajes nuestros con prima medible, por mes de compra:

  2026-08   n=3   +10,00 %   Bigas +10,00 · Zubeldia +10,00 · Cepeda +0,76
  2026-09   n=2    +2,24 %   Kiko Femenía +4,23 · Diego Conde +0,25
  ------------------------------------------------------------------
  TODOS     n=5    +4,23 %   <- lo que publiqué ayer
```

**Tres de los cinco eran de agosto.** Y sobre *todas* nuestras compras, no solo las
que acabaron en viaje:

```
  2026-08   n=10   +10,00 %
  2026-09   n=12    +0,25 %   <- el tope de euro exacto funcionando
```

**El problema de entrada está resuelto en el carril.** Las doce compras de septiembre:

```
05/09  Expósito         −0,06 %      13/09  Rubén García      +7,21 %   <-
06/09  Kiko Femenía     +4,23 %   <- 13/09  Trent              0,00 %
12/09  Fortuño          +0,25 %      15/09  Selu Diallo       +0,25 %
12/09  Diego Conde      +0,25 %      15/09  Oriol Rey         +0,18 %
15/09  Balde            +0,25 %      15/09  Benavidez         +0,25 %
15/09  Paco Cortés      +0,25 %      16/09  Álvaro Carreras  +14,08 %   <-
```

**Nueve de doce a +0,25 % o menos.** Las tres que se salen —Kiko Femenía, Rubén
García, Álvaro Carreras— son **todas de `XI_UPGRADE`**, la vía que no tiene tope de
prima. Ninguna es del carril.

> **El problema de entrada sigue vivo, pero no está donde dije: está en
> `XI_UPGRADE`, no en la especulación. El carril no tiene que esperar a nada.**

*(Álvaro Carreras, +14,08 % el 16/09 con dos rivales, es la más cara y la más
reciente. No es de este encargo, pero queda dicha.)*

---

## BLOQUE 2 — La regla, y el suelo que puede impedirla

### La curva completa, por noches

```
noches      n    neto %      %/día   ganan  % ganan   deriva  prima vta  prima cpa
1 noche    11   +3,14 %   +2,952 %     11    100 %   +0,20 %   +2,67 %    +0,00 %
2 noches    6   −4,13 %   −1,422 %      2     33 %   −4,84 %   +3,11 %    +1,56 %
3 noches   10   −0,75 %   −0,202 %      5     50 %   +0,00 %   +4,35 %    +2,94 %
4 noches   10   +2,75 %   +0,593 %      7     70 %   +3,54 %   +3,44 %    +2,71 %
5 noches    9   +0,53 %   +0,103 %      6     67 %   +4,97 %   +1,13 %    +2,67 %
6 noches    6   +0,64 %   +0,092 %      4     67 %   +3,11 %   +1,93 %    +6,64 %
7+ noches  42   +7,96 %   +0,486 %     31     74 %  +14,49 %   +3,20 %    +2,24 %
```

### Y la misma curva, Pollo aparte: **es suya, no del mercado**

```
POLLO17  (n=43)                    LOS DEMÁS  (n=51)
noches   n   neto %  % ganan       noches   n   neto %  % ganan
1       10   +3,57 %   100 %       1        1   +0,90 %   100 %
2        3   +0,49 %    67 %       2        3   −7,86 %     0 %
3        3   +5,12 %    67 %       3        7   −2,36 %    43 %
4        5   +3,31 %   100 %       4        5   −0,34 %    40 %
5        4   +4,66 %   100 %       5        5   −2,27 %    40 %
7+      16   +8,66 %    94 %       7+      26   +7,22 %    62 %
```

**Pollo gana a todas las duraciones. Los demás pierden a todas menos la primera y la
última.** El «filo de los 2-4 días» que anuncié ayer es de *ellos*, no del mercado.

### Y lo que de verdad ordena el resultado es la entrada

```
mánager        n   prima de compra   neto mediano
Pollo17       37        +0,57 %          +4,67 %
Luismi_Haz    25        +1,94 %          +3,30 %
Pepe Bordalás  5        +4,23 %          +4,20 %
Manzagool     10        +5,30 %          −5,77 %
```

### La regla que propongo

> **COMPRA** — se ofrece `precio + 1` y nunca por encima del tope de la casa
> (+0,25 %). Toda la ventaja está en no pagar de más.
>
> **VENTA** — se vende **el primer día en que la oferta cubre `coste × 1,01`**. No
> hay plazo. Si no cubre, se espera.
>
> **ALARMA** — una posición que lleva más de 7 días sin una oferta que cierre no es
> un viaje: es capital parado, y se marca. No se vende: **se avisa**.

### **Sí: el suelo del +1 % puede impedir cerrar, y no por casualidad**

```
prima que paga el Computer a Pollo   +3,42 %  ->  neto +3,16 %   CIERRA
prima que nos paga a nosotros        +1,12 %  ->  neto +0,87 %   NO LLEGA
```

Con una compra a +0,25 % y una venta a +1,12 %, el neto es **+0,87 %** y el suelo
pide **+1,00 %**. **Falta por 0,13 puntos, estructuralmente**, no de vez en cuando.

Y sobre los once viajes de una noche, simulando que los hubiéramos hecho nosotros:

```
si el Computer nos pagara lo que le paga a Pollo   ->  cierran  8 de 11   +737.925 €
si nos pagara lo que nos paga a nosotros (+1,12 %) ->  cierran  6 de 11   +261.086 €
```

*(Chust, el peor de los once reales, se quedó a −0,10 % del suelo. La holgura mediana
sobre el suelo en esos once fue de sólo +2,14 %.)*

---

## BLOQUE 3 — Lo que cuesta el suelo

```
15 de nuestras 18 posiciones abiertas no tienen oferta que llegue al suelo
42.887.329 € parados · 6 de ellas por encima de 7 días

jugador            coste       oferta        suelo       falta   días  aviso
Yamal         24.897.600   20.896.900   25.146.576  +4.249.676   37,4   SÍ
Yusi             504.000   sin oferta      509.040    +509.040   30,4   SÍ
Castrón        1.200.001   sin oferta    1.212.001  +1.212.001   29,4   SÍ
Djené          2.409.001    1.773.900    2.433.091    +659.191   27,4   SÍ
Jonny          1.925.100   sin oferta    1.944.351  +1.944.351   24,4   SÍ
Manu Sánchez   1.564.837   sin oferta    1.580.485  +1.580.485   18,4   SÍ
```

**El precio de tener a Yamal, escrito al lado:** 24,9 M inmovilizados 37 días, y la
mejor oferta del Computer está 4,25 M por debajo del suelo. **Es el 86 % de la caja
de especulación.** Los puntos son suyos y esa decisión no se discute aquí — pero
ahora el número está.

*(«Sin oferta» quiere decir que el Computer no tiene una oferta viva en la foto del
14/09, no que la haya hecho mala.)*

### Cuántos viajes caben

```
presupuesto de especulación      3.780.699 €
coste típico de un viaje         2.410.007 €
                                 -> 1 plaza
tasa de cierre                   46 %/día (n=13)  -> una vuelta cada 2,2 días
margen cuando cierra             +3,69 % neto (prima mediana +3,95 %)

  un mes                 +1.231.483 €
  lo que queda de temporada (240 días)   +9.851.868 €
  distancia con Pollo                   +24.600.000 €
```

**Con una sola plaza, el carril a pleno rendimiento da ~40 % de la distancia en lo
que queda de temporada.** El cuello de botella **no son los 20 del día**: es que sólo
cabe **una** posición a la vez.

---

## BLOQUE 4 — El listón propio

```
  Para cerrar hay que comprar como mucho a mercado × 1,0025 y cobrar al menos
  coste × 1,0100.

  LISTÓN DEL CARRIL = (1 + 0,01) × (1 + 0,0025) − 1 = 1,2525 %
```

**No es un número redondo: es el producto de los dos umbrales que no se tocan.** Si
el dueño mueve cualquiera de los dos, el listón se mueve solo — que es exactamente lo
que no hacía el 3 % global.

```
techo medido de la vía COMPUTER_RESALE   1,5075 %   <- el listón cabe debajo
listón global de especulación            3,0000 %   <- no cabía (doctrina 60)
```

**Cabe, pero por 0,25 puntos.** Es un margen estrecho y hay que saberlo.

### Los falsos positivos, antes que los aciertos

```
viajes que la regla habría cerrado:    57 de 94   de esos, con pérdida:  0
viajes que la regla NO habría cerrado: 37 de 94   de esos, con pérdida: 28
   capital que habrían inmovilizado:   131.417.673 €
   días medianos abiertos:             5,1
```

**Por construcción no puede haber un cierre perdedor:** la regla exige +1 % sobre el
coste. **El riesgo de este carril no está en cerrar mal — está en no poder cerrar.**

Ésos son los falsos positivos de verdad: no compras que pierden, sino compras que se
quedan atrapadas porque la oferta nunca llega al suelo. **37 de 94, y 28 de ellas
acabaron vendiéndose en pérdida** después de esperar.

---

## Qué más se abre sin querer — **y esto es lo más importante del informe**

Separar la etiqueta no quita sólo el listón del 3 %. `optimal_bid` decide **tres
cosas** con la misma cadena `intent == "SPECULATION"`:

```python
tope_aplicable = prima_maxima if str(intent).upper() == SPECULATION_INTENT else None
...
es_especulacion = str(intent).upper() == SPECULATION_INTENT
```

```
                        con la etiqueta        sin la etiqueta
listón del 3 %               se aplica            NO se aplica
mínimo de 25.000 €           se aplica            NO se aplica
tope de puja +0,25 %         se aplica            NO SE APLICA   <-
```

Comprobado sobre un jugador de 2.000.000 €:

```
con la etiqueta SPECULATION          ->  no puja   RENDIMIENTO_INSUFICIENTE
sin la etiqueta                      ->  puja 2.010.401  (+0,52 %)
tope sin la etiqueta: hasta el valor, 2.030.150  (+1,51 %)
```

> **Quitar la etiqueta abre el carril y, en el mismo movimiento, le quita el tope de
> puja que es justo lo que lo hace rentable.** Pagaríamos +0,52 % en vez de +0,25 %, y
> el listón de 1,2525 % está calculado suponiendo +0,25 %.

**No es un detalle: es la diferencia entre Pollo (+0,57 % de prima, +4,67 % de neto) y
Manzagool (+5,30 %, −5,77 %).** Si se separa la etiqueta hay que llevarse el tope con
ella, o el carril nace roto.

---

## Lo que NO hice, y por qué

- **No encendí nada.** `ENCENDIDO = False`, con guardia.
- **No toqué la etiqueta** `SPECULATION` de `computer_resale_value`, ni el listón del
  3 %, ni el suelo del +1 %, ni `PRIMA_MAXIMA_DE_PUJA`, ni `MIN_WIN_PROBABILITY`, ni
  `MAX_PROJECTED_DAILY_RATE`, ni el horizonte, ni el cupo, ni `bid_cap`, ni
  `PUEDEN_ENCERRARLO`, ni `MAX_SINGLE_SPECULATION_PERCENT`, ni `MAX_SAFE_DEBT`.
- **No propuse vender a nadie.** `posiciones_atascadas` no devuelve ninguna orden, y
  hay guardia de que no la devuelva.
- **No deshice la curva nueva.** No toqué el workflow. No empujé.
- **No pude medir la oferta del Computer día a día**: sólo hay **13 ofertas vivas** en
  la foto del 14/09 y dos líneas en el censo. La tasa del 46 % sale de ahí. **Es el
  número más débil de todo el informe y todo lo de arriba cuelga de él.**
- **No pude hacer el contrafactual de compra**: no hay registro histórico de qué
  sacaba el Computer cada día, así que «qué habría comprado el listón» está contestado
  sobre los viajes que de verdad ocurrieron, no sobre un mercado reconstruido.

### Los avisos de `n`, juntos

- **13 ofertas vivas** para la tasa de éxito y el techo de la vía.
- **11 viajes de una noche**, 10 de un solo mánager.
- **5 viajes nuestros** con prima medible, 3 de agosto y 2 de septiembre.
- **2 líneas** en el censo de ofertas.

---

## Lo que queda en el repo

```
src/analysis/el_carril_de_un_dia.py             la regla y el listón. Apagado
src/analysis/test_el_carril_de_un_dia_v1.py     8 guardias
scripts/run_validation_gate.py                  +1 en la lista (145)
```

| guardia | qué pasa si se rompe |
|---|---|
| `test_la_prima_de_compra_lleva_su_mes` | vuelve la mediana que mezcla agosto con septiembre |
| `test_la_ventana_sale_de_la_curva` | la regla recupera un plazo, o el listón vuelve a ser una constante |
| `test_el_liston_no_supera_el_techo_de_la_via` | el listón vuelve a pasarse del techo (doctrina 60) |
| `test_en_este_carril_se_puja_el_minimo` | se empieza a pagar de más al entrar |
| `test_el_capital_parado_se_cuenta_y_no_se_propone_vender` | el módulo empieza a ordenar ventas |
| `test_lo_que_cabe_se_limita_por_el_capital` | se proyecta un mes sin capital que lo pague |
| `test_el_carril_sigue_apagado` | se enciende solo |
| `test_el_fixture_trae_de_todo` | **regla 24** |

**Probadas reintroduciendo el fallo, en memoria:**

```
el listón es una constante escrita      ->  test_la_ventana_sale_de_la_curva
la regla de venta recupera un plazo     ->  test_la_ventana_sale_de_la_curva
la tasa se mide sobre las aceptadas     ->  test_la_ventana_sale_de_la_curva
el capital parado propone vender        ->  test_el_capital_parado_...
se queda encendido                      ->  test_el_carril_sigue_apagado
se puja por encima del mínimo           ->  test_en_este_carril_se_puja_el_minimo
```

---

## Lo que hay que decidir

1. **Si se separa la etiqueta, hay que llevarse el tope de puja con ella.** Solo es
   una línea, pero sin ella el carril nace sin la única ventaja que tiene.
2. **El listón propio es 1,2525 %**, derivado, y cabe bajo el techo de 1,5075 % **por
   0,25 puntos**. Estrecho.
3. **Cabe una plaza.** Con 42,9 M parados bajo el suelo, el carril a pleno rendimiento
   da ~9,85 M en lo que queda de temporada: el 40 % de la distancia.
4. **Y el número más flojo es el que más manda:** la tasa del 46 % sale de 13 ofertas.
   Antes de encender, esa medición merece más muestra — el censo de ofertas ya está
   escribiendo, así que se cura sola con los días.
