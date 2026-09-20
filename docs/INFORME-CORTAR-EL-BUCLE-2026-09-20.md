# CORTAR EL BUCLE, Y MIRAR DONDE SE GANA

**Fecha:** 2026-09-20 (séptimo del día) · **Rama:** `arreglo/el-bucle-abajo`, desde
`medir/el-bucle` · **Escrituras contra Biwenger:** ninguna · **Interruptor nuevo:**
`BORDALAS_SIN_REFERENCIA_ESCALA`, **apagado** · **Vara, topes y `MERCADO_DE_RIVAL`:
sin tocar.**

**Verja: 164 de 164.**

---

## BLOQUE 1 — EL ARREGLO

### Qué se ha hecho

`SIN_PRONOSTICO` tenía dos causas metidas en la misma etiqueta. Ahora se separan en
[`player_value_engine.py:1239`](src/analysis/player_value_engine.py#L1239):

| causa | etiqueta | qué hace |
|---|---|---|
| no hay pronóstico **del candidato** | `SIN_PRONOSTICO` | callarse es correcto: no sabemos nada de quien queremos meter |
| no hay pronóstico **de la referencia** | **`SIN_REFERENCIA`** | el candidato no es malo: no hay con qué compararlo |

**Las dos siguen valiendo CERO.** A ciegas no se puja y el guardarraíl del 17/08 se
queda entero — hay guardia que lo exige con el interruptor en las dos posiciones. Lo
único que cambia es que la segunda **se ve**.

### Cómo escala: al panel, con el nombre

De las tres formas que ofrecías, elijo **al panel**, y las otras dos las descarto con
el dato delante:

- **«a otro titular de la posición»** no existe en el caso que venimos a arreglar: el
  18/09 la portería tenía **un solo titular**. No hay segundo a quien preguntar.
- **«a un valor de referencia declarado»** sería inventarse el número que falta, que
  es exactamente la doctrina 24 al revés otra vez.

La salida lleva tres campos nuevos:

```python
"escala": True,
"escala_a": "PANEL",
"falta": "Esquivel",
```

Y el motivo **nombra la causa** (doctrina 87):

> «No puedo compararlo porque **Esquivel** no tiene pronóstico de titularidad. El
> candidato no es peor: es que no hay con qué medirlo. A ciegas no se puja, pero esto
> no es un «no».»

Comparado con lo de hoy: *«No hay pronóstico de titularidad del que saldría. Sin ese
dato no se puede saber si el once mejora, y a ciegas no se puja»* — verdadero, pero
anónimo y con forma de rechazo.

### Los tres contadores que ya conocen la etiqueta nueva

El 17/08 el contador de bloqueados pasó de 12 a 5 **el día que el veto hizo MÁS
trabajo**, porque nadie le dijo los nombres nuevos. No se repite:

```
  acquisition_board.VETOS_DEL_ONCE        + SIN_REFERENCIA
  los_sentidos (la alarma)                + SIN_REFERENCIA
  roster_expansion_shadow.XI_VETOES       + SIN_REFERENCIA
```

Hay guardia que lo comprueba leyendo los tres ficheros.

### La tabla que decide si sirve

**18/09 — los cuatro `SIN_PRONOSTICO` de portería**

| jugador | hoy | con el arreglo | referencia |
|---|---|---|---|
| Álvaro Valles | `SIN_PRONOSTICO` | **`SIN_REFERENCIA`** + escala | Esquivel (prob `None`) |
| David Soria | `SIN_PRONOSTICO` | **`SIN_REFERENCIA`** + escala | Esquivel (prob `None`) |
| **Dmitrovic** | `SIN_PRONOSTICO` | **`SIN_REFERENCIA`** + escala | Esquivel (prob `None`) |
| Szczęsny | `SIN_PRONOSTICO` | **`SIN_REFERENCIA`** + escala | Esquivel (prob `None`) |

**20/09 — los 0 de 55**

```
  candidatos cuya DECISION cambia:  0
  candidatos cuyo VALOR   cambia:   0
```

> **El 20/09 no cambia nada.** El arreglo no se ha pasado de rosca: toca exactamente
> el caso que venía a tocar.

Y el 18/09 **cambian 4 decisiones y CERO valores**. No abre ninguna compra.

### El interruptor

> **`BORDALAS_SIN_REFERENCIA_ESCALA`**

Apagado: misma decisión, mismo motivo, mismo cero, y sin campos nuevos en la salida.
Hay guardia que lo exige.

### La guardia

`src/analysis/test_el_bucle_de_la_vara_v1.py`, **7 pruebas, en la verja**. Fichas
construidas ahí: no lee `data/`, ni `diagnostico/`, ni la red, ni el reloj.

| prueba | qué exige |
|---|---|
| `test_el_caso_que_vino_a_mirar_se_da` | **falla si los dos tienen datos** |
| **`test_sin_pronostico_distingue_quien_falta`** | las dos causas no salen con la misma etiqueta, y el motivo nombra a Esquivel |
| `test_no_desaparece_escala` | `escala: True`, `escala_a: PANEL`, `falta: Esquivel` |
| `test_a_ciegas_sigue_sin_pujarse` | valor cero en los cuatro cruces de causa × interruptor |
| **`test_una_posicion_con_un_titular_no_se_ciega`** | **falla si la posición del caso tiene más de un titular** |
| `test_apagado_se_comporta_como_ayer` | apagado, ni un campo nuevo |
| `test_los_contadores_ven_la_etiqueta_nueva` | los tres ficheros conocen `SIN_REFERENCIA` |

---

## BLOQUE 2 — DÓNDE SE GANA DINERO DE VERDAD

### Son TRES ventas a managers, no dos

Corrijo mi `n` de ayer: dije dos porque conté sólo las que tenían compra previa en el
tablón. **Javi Hernández venía de la plantilla inicial**, así que no entraba en las 23
operaciones cerradas pero sí es una venta a un manager.

| jugador | a | fecha | cobrado | mercado ese día | sobre mercado | comprado | días | resultado |
|---|---|---|---:|---:|---:|---|---:|---:|
| **Javi Hernández** | Pollo17 | 19/08 19:41 | 1.250.000 | 1.010.000 | **+23,8 %** | plantilla inicial | — | — |
| **Andrés Castrín** | Pollo17 | 24/08 07:48 | 1.346.045 | 1.020.000 | **+32,0 %** | 18/08 por 1.200.001 | **6,0** | **+146.044 (+12,2 %)** |
| **Yusi Enríquez** | Prinzipote | 04/09 21:57 | 1.226.068 | 1.140.000 | **+7,5 %** | 17/08 por 504.000 | **18,6** | **+722.068 (+143,3 %)** |

### ¿Ganan por el mismo motivo? Sí, y son dos motivos encadenados

**Las tres se venden por encima del mercado** (+7,5 %, +23,8 %, +32,0 %), cuando las
21 ventas al Computer dan una mediana de **+0,55 %**. Ése es el primero.

El segundo es el plazo: **6 y 18,6 días**, contra los 4,7 de mediana de las ventas al
Computer. Yusi Enríquez ganó +143,3 % porque **se revalorizó mientras lo teníamos** —
504.000 → 1.140.000 de mercado en dieciocho días— y encima se vendió un 7,5 % por
encima de ese mercado ya subido.

> **Al Computer le vendemos rápido y a precio de mercado. A un manager le vendemos
> tarde y con prima.** Son dos negocios distintos y sólo tenemos abierto el que
> pierde.

`n = 3`, y con tres no se declara una ley (doctrina 55). Pero las tres apuntan al
mismo sitio y ninguna al contrario.

### Ofertas de managers que hemos rechazado: cinco de cinco

| quién | por | ofrecía | mercado 12/08 | sobre mdo | ¿sigue con nosotros? |
|---|---|---:|---:|---:|---|
| Pollo17 | **Jutglà** | 4.300.000 | 4.120.000 | **+4,4 %** | sí, 29 pts hoy |
| Pollo17 | **Olasagasti** | 2.750.000 | 2.620.000 | **+5,0 %** | sí, 32 pts hoy |
| Pollo17 | Olasagasti (2ª) | 2.740.000 | 2.620.000 | +4,6 % | sí |
| Pollo17 | Ximo Navarro | 1.200.000 | 1.170.000 | +2,6 % | no |
| Luismi_Haz | Yeray | 2.000.000 | 1.880.000 | +6,4 % | no |

**Cinco ofertas, cero aceptadas.** Las cuatro distintas estaban **todas por encima del
mercado**, de +2,6 % a +6,4 % — el mismo rango que las ventas que sí cerramos.

Y lo que pasó con los dos que acabamos soltando:

```
  Ximo Navarro   vendido al Computer el 20/08 por 1.385.700   (+185.700 sobre la oferta)
  Yeray          vendido al Computer el 22/08 por 1.838.100   (-161.900 sobre la oferta)
```

**Un empate: +23.800 € entre los dos.** Rechazarlas no salió mal, pero tampoco salió
bien, y `n = 2`.

> **Aviso del `n`: las cinco ofertas son del 12 y el 13/08, los dos únicos días con
> fotos densas antes del hueco del 18/08 al 09/09.** No sé si llegaron más y no las
> vi. Una oferta al día en la única ventana observada es mucho para darlo por cerrado.

### ¿Merece seguir abierta la reventa al Computer por encima del suelo?

**No, y lo digo con los números delante:**

```
  al Computer, por tramo de COMPRA
    suelo (<300 k)   n= 8   +1,51 %   100 % verde       +28.867
    300 k - 1,5 M    n= 4   -1,50 %    25 %            +109.399
    1,5 M - 3 M      n= 9   -2,57 %    33 %          -1.038.783
    >= 3 M           n= 0        -        -                   -
```

**Mi recomendación, y la decides tú: dejar la cesta viva SÓLO en el suelo y cerrar la
reventa al Computer por encima de 300.000 €.** Motivos, por orden de peso:

1. **Nueve operaciones y un millón perdido** por encima de 1,5 M, con sólo 33 % en
   verde. No es una racha: es un tercio de aciertos sostenido.
2. **El suelo es el único tramo con 8 de 8 en verde**, y gana 28.867 € — céntimos,
   pero céntimos consistentes y con muy poco capital inmovilizado.
3. El tramo intermedio sale positivo **sólo por las dos ventas a managers**. Quitadas,
   pierde.
4. Y el `n` manda: **ninguna celda llega a `MIN_SAMPLES = 12`**. Por eso digo «cerrar
   por encima del suelo» y no «apagar la cesta»: lo que está medido es que arriba
   pierde, no que abajo no sirva.

**Lo que abriría en su lugar, y no abro:** la venta a managers. Tres ventas, las tres
con prima, y cinco ofertas recibidas que no contestamos. Ahí hay un negocio medido y
está cerrado por omisión.

**No he apagado nada.**

---

## BLOQUE 3 — LOS QUE PIDEN POR DEBAJO DEL MERCADO

### No son cuatro: son seis y diez

Corrijo otro `n` mío. «Cuatro» eran los que sobrevivían **a la vez** al filtro de la
vara y al tope. Pidiendo estrictamente **por debajo del mercado**, de un rival:

```
  18/09   6   Requena -5,9 %   Bellerin -1,9 %   Jonathan David -1,3 %
              Danjuma -0,5 %   Tchouameni -0,4 %   Berenguer -0,3 %
  20/09  10   Osorio -15,9 %   Requena -2,8 %   Hugo Alvarez -1,8 %
              Cristian Romero -1,7 %   Veiga -1,2 %   Bouare -1,1 %
              Alvaro Garcia -0,8 %   Buchanan -0,7 %   Rioja -0,7 %   Fermin -0,5 %
```

### ¿Mejoran el once, con los números del MOTOR? Ninguno

Y esta vez sin la vara. Puntos **esperados** contra el titular que de verdad saldría:

| jugador | pide | esperados | sustituiría a | **el motor dice** |
|---|---:|---:|---|---|
| **Veiga** | 3.420.000 | 105 | Cabrera (102) | **`MEJORA_INSUFICIENTE`** — «Sólo sumaría **3** puntos y saldría del once un titular. Para tocar el once hacen falta **8**» |
| Cristian Romero | 5.240.000 | 62 | Cabrera | `NO_MEJORA_JERARQUIA` (Reserva ← Importante, 3 escalones) |
| Álvaro García | 3.870.000 | 156 | Jutglà | vale **451.206 €** como fichaje (+21 pts × 21.486) y pide 3,87 M |
| Hugo Álvarez | 1.090.000 | 67 | Oriol Rey | `PIERDE_TITULARIDAD` (50 % contra 80 %) |
| Buchanan | 2.740.000 | 92 | Oriol Rey | `PIERDE_TITULARIDAD` (50 % contra 80 %) |
| Fermín | 15.600.000 | 126 | Oriol Rey | `PIERDE_TITULARIDAD` (50 % contra 80 %) |
| Bellerín (18/09) | 2.560.000 | 63 | Djené (99) | `NO_MEJORA` |
| Berenguer (18/09) | 3.310.000 | 66 | Jutglà (145) | `NO_MEJORA` |

> **Ninguno de los dieciséis mejora el once según el motor.** El que más cerca queda
> es **Veiga**: le faltan **5 puntos** de los 8 que exige el listón para mover el once.

### ¿Alguno pasa las tres puertas?

**Ninguno.** Y las tres fallan por sitios distintos, que es lo interesante:

| puerta | Veiga, el mejor candidato |
|---|---|
| **1. el mercado de rivales** | `MERCADO_DE_RIVAL` — cerrada |
| **2. la etiqueta / el bolsillo** | `TRADE`/`SPECULATION`, bolsillo de **973.594 €** para un jugador de 3,42 M |
| **3. el tope de puja** | pide **−1,2 %** sobre mercado: **ésta sí la pasa** |

**El tope es la única de las tres que no ata.** Lo confirma lo de ayer: subir de
+0,25 % a +1,95 % no desbloquea a nadie.

> **No hay hoy ningún jugador de un rival que el motor pudiera fichar. El más cercano
> es Veiga, y no es la puerta del mercado ni el tope lo que lo para: es que sólo suma
> tres puntos.**

---

## BLOQUE 4 — LA LISTA DE VIGILANCIA

### No queda casi vacía. No se puede hacer

```
  libres en el catalogo                 417
  candidatos (suman y han jugado 3+)    115
  vigilados publicados                   20

  el pronostico del motor cubre          64 jugadores de 546 del catalogo
  de los 20 vigilados, CON pronostico     1
```

> **Con esas palabras: la lista de vigilancia no se puede rehacer con los números del
> motor, porque el motor no tiene números para esos jugadores. Uno de los veinte tiene
> pronóstico, y ese uno no mejora el once.**

El único con pronóstico:

```
  Paredes   DEF   2.410.000   70 % titular   Rotacion
            sustituiria a Cabrera (80 % titular, Clave)
            -> NO_MEJORA_JERARQUIA: Rotacion por Clave
```

Y los diecinueve restantes sólo tienen `nos_suma` — el número de la vara, el que te
pasé y no sirve para decidir. Encabezados por **Raphinha, `nos_suma` 84, 21.230.000 €**,
del que no sabemos ni si juega.

### Por qué, y qué costaría

`build_starter_lookup` cubre **64 de 546** jugadores del catálogo (11,7 %): sólo los
**20 del mercado del día** y **nuestra plantilla**. El pronóstico se pide para lo que
se puede comprar hoy, no para el catálogo entero.

Así que la lista de libres no es que esté mal ordenada: **es que ningún criterio bueno
se le puede aplicar con lo que hay en disco.** Arreglarlo es pedir pronóstico para los
115 candidatos, que es una llamada a la red y no es este encargo.

**Mientras tanto, la lista que te pasé no se puede usar para decidir.** Lo que sí dice
—cuántos libres hay, cuáles han jugado, a cuánto están— sigue siendo cierto. Lo que no
dice, y parecía decir, es cuál mejora el once.

---

## LO QUE NO HICE, Y POR QUÉ

- **No encendí `BORDALAS_SIN_REFERENCIA_ESCALA`** ni `BORDALAS_PRIMA_POR_TRAMO`.
- **No toqué la vara**, ni `acquisition_valuation.py:456`, ni
  `deployment.classify_operation`. El arreglo está donde se pierde el dato, no donde
  se usa.
- **No apagué ninguna vía.** El bloque 2 recomienda cerrar la reventa al Computer por
  encima del suelo; la decisión es tuya.
- **No abrí `MERCADO_DE_RIVAL` ni toqué ningún tope.**
- **No pedí pronóstico para los 115 libres.** Es una llamada a la red.
- **No puedo decir si llegaron más ofertas de managers** entre el 18/08 y el 09/09: no
  hay fotos de ese periodo.
- **No sé si las cinco ofertas se rechazaron activamente o expiraron solas.** El tablón
  publica lo que se cierra; cuatro quedaron `waiting` en la última foto y una `expired`.
- **Ni una escritura contra Biwenger.** La ventana cerrada, el workflow sin tocar.

### La verja

```
164 de 164 OK      (eran 163; una guardia nueva)
```

Salida a fichero, árbol quieto, sin `git add -A`. **No empujo.**

### El `n`, y cuándo se cortó

| medida | `n` | corte |
|---|---|---|
| el arreglo, 18/09 | 4 decisiones cambian · **0 valores** | foto 18/09 |
| el arreglo, 20/09 | **0 cambia** | foto 20/09 |
| ventas a managers | **3** (2 con compra previa) | 19/08 → 04/09 |
| ofertas de managers recibidas | **5**, todas del 12-13/08 · **0 aceptadas** | fotos densas |
| los dos que soltamos después | 2, saldo **+23.800 €** | 20 y 22/08 |
| reventa al Computer por tramo | 8 · 4 · 9 · **0** — ninguna celda llega a 12 | 10/08 → 20/09 |
| piden por debajo del mercado | **6** (18/09) · **10** (20/09) | dos fotos |
| … que mejoran el once según el motor | **0** | idem |
| cobertura del pronóstico | **64 de 546** · **1 de 20** vigilados | hoy |

Dos correcciones de `n` mías en este informe: las ventas a managers son **tres** y no
dos, y los que piden por debajo del mercado son **seis y diez**, no cuatro. Los
«cuatro» eran los que pasaban a la vez el filtro de la vara y el tope.
