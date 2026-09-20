# LA PRIMA POR TRAMO Y LA ETIQUETA EQUIVOCADA

**Fecha:** 2026-09-20 (quinto del día) · **Rama:** `arreglo/la-prima-y-la-etiqueta`,
desde `medir/el-orden-y-el-mercado` · **Escrituras contra Biwenger:** ninguna ·
**Interruptor nuevo:** `BORDALAS_PRIMA_POR_TRAMO`, **apagado** · **Etiqueta, `intent`,
`MERCADO_DE_RIVAL` y desempate: sin tocar.**

**Verja: 163 de 163.**

---

## LO QUE CIERRA EL DIAGNÓSTICO, ARRIBA

Con la prima por tramo, sobre **los mismos candidatos reales** donde vimos la
dispersión del 0,019 %:

```
18/09   prima PLANA      n=18   dispersion del ratio    0,019 %
18/09   prima POR TRAMO  n=18   dispersion del ratio   72,330 %
20/09   prima PLANA      n=16   dispersion del ratio    0,034 %
20/09   prima POR TRAMO  n=16   dispersion del ratio   72,335 %
```

**El ratio deja de salir plano.** Doctrina 98 confirmada: el diagnóstico estaba
completo y la entrada era el problema.

Pero hay dos cosas que van contra el arreglo y las dos son medidas, no opiniones:

1. **En los dos días con foto, la cesta compra exactamente lo mismo con la curva que
   sin ella.** Lo que ata no es el criterio: es el tope de la ventana.
2. **Tenemos CERO operaciones cerradas por encima de 3 M.** Y por encima de 1,5 M
   tenemos nueve, con **−1.038.783 €**. La prima dice que el dinero está arriba;
   nuestro historial dice que arriba es donde perdimos un millón.

---

## BLOQUE 1 — LA PRIMA POR TRAMO

### Los tramos, y por qué esos cortes

**No son cortes nuevos.** 1.500.000 y 3.000.000 son `CORTES_DE_PRECIO`, la rejilla
que `la_subasta` ya usa para la probabilidad de pelea. Las dos cosas se multiplican en
el mismo sitio —`_por_euro`— así que dos rejillas distintas para el mismo eje serían
una arbitrariedad escondida. El único corte nuevo es **6.000.000**, y sale de donde
estaba el salto.

`n = 194` ventas al Computer fechadas contra el precio de aquel momento:

| tramo | n | mediana | media | en verde | p25 | p75 | **IQR** |
|---|---:|---:|---:|---:|---:|---:|---:|
| 0 – 1.500.000 | **74** | **+1,36 %** | +1,58 % | **73 %** | −0,13 % | +4,02 % | 4,15 % |
| 1.500.000 – 3.000.000 | **51** | **+1,78 %** | +1,60 % | **75 %** | −0,64 % | +3,32 % | 3,96 % |
| 3.000.000 – 6.000.000 | **53** | **+2,63 %** | +2,50 % | **87 %** | +0,92 % | +4,09 % | 3,17 % |
| 6.000.000 + | **16** | **+4,26 %** | +3,64 % | **94 %** | +3,41 % | +4,74 % | 1,34 % |
| global | 194 | +2,38 % | | 79 % | | | |

**Ninguno sale «sin calibrar» hoy.** El mínimo es `MIN_SAMPLES = 12`, que tampoco es
nuevo: es el listón que la curva de primas del modelo de puja ya usaba. El más flaco
es el de arriba con **n = 16**, que pasa por cuatro.

Y la tasa de venta en verde **deja de ser una sola**: 73 % abajo, 94 % arriba. Va
tramo a tramo, como pediste.

> **Lo que la curva NO dice, y hay que decirlo:** el rango intercuartílico dentro de
> cada tramo (2,9 a 4,2 puntos) es **mayor** que la separación entre las medianas de
> los extremos (2,9 puntos). La curva describe la mediana, no lo que pasa en una
> operación suelta.

### ¿Deja el ratio de salir plano? Sí

```
18/09, con la curva:
  jugador              precio   prima  ganancia   por euro
  Gerard Moreno     6.910.000   4.26%   277.090   0.040000
  Grimaldo          4.880.000   2.63%   116.143   0.023740
  Cabrera           3.040.000   2.63%    72.351   0.023740
  Moncayola         2.480.000   1.78%    37.943   0.015261
  (suelo)             150.000   1.36%     1.605   0.011068
```

De 0,0111 a 0,0400: **3,6 veces**. Antes, de 0,020841 a 0,020848.

### La tabla antes/después, y el neto

| día | prima | pujas | compromete | neto esperado con la prima **medida** |
|---|---|---:|---:|---:|
| 18/09 | plana (+2,34 %) | 1 — Cabrera | 3.047.601 | 56.434 |
| 18/09 | **por tramo** | **1 — Cabrera** | 3.047.601 | **56.434** |
| 20/09 | plana (+2,34 %) | 3 — Yeray, Diaby, Guevara | 1.934.828 | 16.701 |
| 20/09 | **por tramo** | **3 — los mismos** | 1.934.828 | **16.701** |

> **La cesta compra exactamente lo mismo.** El 18/09 sólo cabe una puja de 3 M en un
> tope de 3.234.502 €; el 20/09 el tope es 1.950.080 € y lo que cabe es Yeray más dos
> del suelo. **Lo que ata es el tope de la ventana, no el orden ni la prima.**

Lo que sí cambia, con el tope quitado para verlo (sensibilidad, no un estado real):

```
18/09  plana  ->  Cabrera, Marc Casadó, Dmitrovic
18/09  tramo  ->  GERARD MORENO (6,91 M), Cabrera, Marc Casadó
20/09  plana  ->  Kounde, Jon Martin, Soler, Dumfries, Julian Alvarez, ...
20/09  tramo  ->  JULIAN ALVAREZ (7,1 M) primero, y despues los mismos
```

La curva mete al de arriba y lo pone primero. Hoy no llega a hacerlo porque el
presupuesto no da.

**Contra los +3.366 medidos:** no puedo darte un neto alternativo de aquellas nueve
operaciones. No hay ninguna foto de dentro de la ventana —las dos que existen se toman
después del reset— así que no se pueden reejecutar aquellas mañanas. Lo que sí hay es
lo realizado, y está abajo.

### El riesgo, medido, y va contra mi propia recomendación de ayer

#### Operaciones cerradas por encima de 3 M

> **Tenemos CERO operaciones cerradas por encima de 3 M.**

No «menos de cinco»: **ninguna**. Las cuatro que hay por encima de esa cifra —Yamal,
Expósito, Cabrera, Dmitrovic— siguen **abiertas**, y las cuatro valen hoy menos de lo
que costaron.

Bajando el listón a 1,5 M, que es donde sí hay historial:

| jugador | pagado | cobrado | días | resultado |
|---|---:|---:|---:|---:|
| Jonny | 1.570.000 | 1.753.200 | 10,2 | **+11,67 %** |
| Gabriel Suazo | 1.629.832 | 1.788.400 | 10,2 | **+9,73 %** |
| Boyomo | 1.817.297 | 1.845.800 | 1,2 | +1,57 % |
| Balde | 1.604.001 | 1.578.500 | 2,3 | −1,59 % |
| Maffeo | 1.664.350 | 1.621.500 | 1,1 | −2,57 % |
| Trent | 2.760.000 | 2.536.500 | 4,7 | −8,10 % |
| Zubeldia | 2.068.001 | 1.847.000 | 26,8 | −10,69 % |
| #2169 | 2.288.001 | 1.930.700 | 3,8 | −15,62 % |
| Djené | 2.409.001 | 1.870.100 | 31,1 | **−22,37 %** |

```
por encima de 1,5 M    n=9   mediana -2,57 %   suma -1.038.783 EUR
a precio de suelo      n=8   mediana +1,51 %   suma    +28.867 EUR
```

**Siete de nueve en rojo arriba; siete de ocho en verde abajo.** Exactamente al revés
de lo que dice la curva.

#### Por qué no se contradicen, y por qué eso es el riesgo

La prima mide **`venta / precio del día de la venta`**. El modelo de la cesta la usa
como si fuera **`venta / lo que pagamos`**, y sólo son lo mismo si el precio no se
mueve entre la compra y la venta.

La mediana de días que aguantamos es **2,4 en el suelo y 4,7 por encima de 1,5 M**.
Djené aguantó 31 días y perdió el 22,4 %; el Computer probablemente le pagó su +2 %
sobre el precio de ESE día — un precio que para entonces había caído un cuarto.

> **«El Computer paga más arriba» y «arriba es más seguro» no son la misma frase, y la
> segunda no la hemos medido. Lo que sí hemos medido —nueve operaciones, un millón
> perdido— dice lo contrario.**

Así que la curva es correcta como medición y **peligrosa como criterio**: empuja hacia
operaciones grandes apoyándose en un número que nunca hemos realizado por encima de
3 M, y que nuestras nueve por encima de 1,5 M contradicen.

**Lo que falta antes de encenderla** —y no lo he hecho porque es otro encargo—: separar
la prima del Computer del movimiento del precio. Medir `venta / compra` sobre las
ventas de toda la liga, no `venta / precio del día`. Con eso sabríamos si la prima
sobrevive al tiempo de tenencia o si se la come la deriva del precio.

### El interruptor

> **`BORDALAS_PRIMA_POR_TRAMO`**

Apagado, `candidatos_en_modo_cartera` se comporta **exactamente** como ayer: usa la
mediana que le entra por la puerta, aunque se le pase la curva. Hay guardia que lo
exige.

La curva **se recibe, no se lee**: `la_subasta` sigue sin abrir disco. La construye
`computer_resale_premium.medir_la_prima_por_tramo` y viaja como el resto del estado.

### Las guardias

`src/analysis/test_la_prima_va_por_tramo_v1.py`, **7 pruebas, en la verja**. Fixtures
propios: no lee `data/`, ni `diagnostico/`, ni la red, ni el reloj.

| prueba | qué exige |
|---|---|
| `test_sin_varios_tramos_no_se_comprueba_nada` | ≥3 tramos calibrados y los dos extremos en tramos distintos — **falla si todos los candidatos caen en el mismo tramo** |
| **`test_la_prima_va_por_tramo`** | 300.000 y 8.000.000 **no reciben la misma prima**, y la del tramo alto es mayor |
| `test_con_la_curva_el_ratio_deja_de_ser_plano` | dispersión <0,5 % con la prima plana y >20 % con la curva |
| **`test_un_tramo_sin_masa_se_declara`** | el tramo flaco sale `calibrado: False`, sin número propio, y cae a la mediana global — **falla si todos los tramos tienen masa** |
| `test_la_tasa_de_acierto_tambien_va_por_tramo` | la tasa en verde ya no es una sola |
| `test_apagado_se_comporta_como_ayer` | con el interruptor apagado, la ganancia no cambia ni un euro |
| `test_los_cortes_son_los_de_la_casa` | los cortes de la pelea están en la rejilla de la prima |

---

## BLOQUE 2 — LA ETIQUETA

### Dónde se decide, y es UN solo sitio

[`deployment.py:202`](src/analysis/deployment.py#L202), dentro de
`classify_operation`:

```python
if price is not None and fichaje:

    compensan = [
        via
        for via in fichaje
        if safe_int(via.get("value")) > safe_int(price)
    ]

    if not compensan:
        fichaje = []          # <- AQUI deja de ser un fichaje
```

Y el `intent` es una **función pura de la clase**
([`deployment.py:120`](src/analysis/deployment.py#L120)):

```python
INTENT_BY_CLASS = {SIGNING: "XI_UPGRADE", TRADE: "SPECULATION"}
```

> **Los tres casos son el mismo sitio.** Una sola línea decide si la operación es un
> fichaje, y de ahí salen el `intent`, el bolsillo y el listón. El 16/09, el 19/09 y
> el 20/09 son tres síntomas de esa línea.

La regla que la puso, del 14/09, es buena y está escrita: *«decir "entra a la
plantilla para jugar" de alguien por el que NO pagaríamos su precio para que juegue es
falso»*. El caso Amatucci. **No la discuto.**

### Pero la causa de los tres NO es la misma, y eso cambia el arreglo

La línea descarta el fichaje cuando **ninguna vía de fichaje llega al precio**. Y las
vías de fichaje llegan a cero por **cinco motivos distintos**:

```
18/09   SIN_PRONOSTICO 4 · PIERDE_TITULARIDAD 7 · NO_MEJORA 10
        NO_MEJORA_JERARQUIA 14 · NO_MEJORA_TITULARIDAD 10 · MEJORA_INSUFICIENTE 1
20/09   PIERDE_TITULARIDAD 11 · NO_MEJORA 10 · NO_MEJORA_TITULARIDAD 8
        NO_MEJORA_JERARQUIA 19 · MEJORA_INSUFICIENTE 2
```

El caso de Valles, entero:

```json
"name": "Álvaro Valles", "points": 49, "position": 1,
"xi_decision": "SIN_PRONOSTICO",
"xi_reason": "No hay pronostico de titularidad del que saldria.
              Sin ese dato no se puede saber si el once mejora,
              y a ciegas no se puja.",
"deployment": {"roster_fill_value": 1935672, "operation_class": "TRADE"}
```

El portero titular el 18/09 era **Esquivel — comprado por la cesta dos días antes a
150.376 €, con 0 puntos y sin historial**. El motor no puede pronosticar a quien acaba
de comprar en el suelo, así que no puede evaluar sustituirlo, así que un portero de 49
puntos sale «especulación».

> **El relleno que compra la cesta es lo que ciega la vía del once.** Es el mismo bucle
> de toda la semana, cerrándose sobre sí mismo.

Y hoy, con Dmitrovic en la portería, **el mismo Valles sale `NO_MEJORA`** en vez de
`SIN_PRONOSTICO`: el motor ya puede comparar y dice que no. Eso no es ceguera, es un
desacuerdo — y puede que tenga razón.

### ¿Puede el `market_gate` reetiquetar de fichaje a especulación? No. El precio sí

`evaluate_market_rate` sólo entra en `como_trading`
([acquisition_valuation.py:703](src/analysis/acquisition_valuation.py#L703)). Quitar
valor a la vía de especular **no puede** convertir un fichaje en comercio: si acaso
hace lo contrario.

Lo de Chust —`XI_UPGRADE` → `ROSTER_FILL`— es un cambio de **ruta dentro del fichaje**,
no de clase. Las dos son `SIGNING_ROUTES` y las dos van al bolsillo de fichar.

**Pero tu sospecha acierta por otra puerta:** `classify_operation` recibe
`price = player["price"]`, el **precio de mercado del día**. Si el precio sube por
encima de lo que vale por la vía de fichaje, `fichaje = []` y la operación pasa a
comercio. **La etiqueta sí se mueve con el precio del día**, sólo que a través de
`price`, no del `market_gate`.

### Cuántos cambiarían de bolsillo

Usando la vara de su posición —la misma que `el_vestuario_libre`—:

| | 18/09 | 20/09 |
|---|---:|---:|
| candidatos | 54 | 55 |
| `operation_class: TRADE` | **34** | **38** |
| `SIGNING` | 2 | **0** |
| **mejoran el once por la vara Y salen TRADE** | **20** | **23** |

**18/09 — los diez que más suman**

```
  jugador            pos  pts  vara  SUMA     precio     xi_decision
  Álvaro Valles      POR   49     0   +49  5.280.000  SIN_PRONOSTICO
  David Soria        POR   42     0   +42  5.590.000  SIN_PRONOSTICO
  Baena              MED   51    19   +32 10.500.000  PIERDE_TITULARIDAD
  Dmitrovic          POR   31     0   +31  4.770.000  SIN_PRONOSTICO
  Mariano            DEL   48    25   +23  5.670.000  NO_MEJORA_JERARQUIA
  De la Fuente       DEF   33    16   +17  4.190.000  PIERDE_TITULARIDAD
  Pépé               DEL   36    25   +11 11.350.000  (sin valorar)
  Grimaldo           DEF   23    16    +7  4.880.000  PIERDE_TITULARIDAD
  Hjulmand           MED   26    19    +7  4.760.000  PIERDE_TITULARIDAD
  Javi Hernández     MED   26    19    +7  3.800.000  PIERDE_TITULARIDAD
```

**20/09 — los diez que más suman**

```
  Fermín             MED   59    19   +40 15.680.000  PIERDE_TITULARIDAD
  Baena              MED   51    19   +32 10.670.000  PIERDE_TITULARIDAD
  De la Fuente       DEF   33     9   +24  4.270.000  PIERDE_TITULARIDAD
  Mariano            DEL   50    29   +21  5.700.000  NO_MEJORA_JERARQUIA
  Álvaro Valles      POR   49    28   +21  5.500.000  NO_MEJORA
  Veiga              DEF   28     9   +19  3.460.000  MEJORA_INSUFICIENTE
  Castrín            DEF   24     9   +15  2.080.000  NO_MEJORA
  Starfelt           DEF   21     9   +12  1.960.000  NO_MEJORA
  Cristian Romero    DEF   20     9   +11  5.330.000  NO_MEJORA_JERARQUIA
  Bellerín           DEF   19     9   +10  2.700.000  NO_MEJORA
```

### Tu propuesta, discutida

> *«un jugador que mejora el once es un fichaje y se mide contra el bolsillo de
> fichar, aunque además se pudiera revender»*

**Estoy de acuerdo con el principio y en desacuerdo con el criterio que propones para
aplicarlo**, y el desacuerdo está en la tabla de arriba.

«Mejora el once» según la vara son **puntos acumulados**. `xi_upgrade_value` usa un
**pronóstico de titularidad**. No son la misma pregunta:

- **Baena, 51 puntos**, sale `PIERDE_TITULARIDAD`. Si ya no juega, sus 51 puntos son
  historia, no promesa. **Ahí el motor probablemente tiene razón y la vara no.**
- **Valles el 18/09**, 49 puntos, sale `SIN_PRONOSTICO` porque el titular era un
  jugador recién comprado en el suelo. **Ahí el motor está ciego, no en desacuerdo.**

Son dos cosas distintas y la línea las trata igual. Con un solo arreglo en
`deployment.py:202` se caen los tres casos **y también los 14 y 19 de
`NO_MEJORA_JERARQUIA`**, que es justo lo que no queremos.

> **Un solo sitio, sí. Un solo arreglo, no.** El sitio es `classify_operation`; lo que
> hay que arreglar está **encima**: distinguir «no mejora» de «no se puede saber si
> mejora». Hoy las dos dan cero y la línea las trata igual, y eso es la doctrina 24
> otra vez — un hueco de información leído como un «no».

**No lo he cambiado.**

---

## BLOQUE 3 — LAS DOS PUERTAS, EN SECO

### Qué habría comprado

| | 18/09 | 20/09 |
|---|---|---|
| **hoy** (las dos cerradas) | 2 BID: Cabrera (3,04 M), Maffeo (1,66 M) | **0 BID** |
| **A) sólo `MERCADO_DE_RIVAL`** | **0 nuevos** | **0 nuevos** |
| **B) sólo la etiqueta** | 2 nuevos: Gerard Moreno (+5), Grimaldo (+7) | **0 nuevos** |
| **C) las dos** | **11 comprables** | **9 comprables** |

> **Doctrina 99, medida: abrir una no abre nada.** El día que la puerta del mercado de
> rivales sola habría comprado algo es **ninguno de los dos**.

**C) las dos abiertas, 18/09**

```
  jugador            pos  SUMA       piden    origen     bolsillo de fichar 9.743.865
  Álvaro Valles      POR   +49   6.240.000    rival
  Mariano            DEL   +23   6.780.000    rival
  De la Fuente       DEF   +17   4.990.000    rival
  Grimaldo           DEF    +7   4.880.000    Computer
  Hjulmand           MED    +7   5.690.000    rival
  Javi Hernández     MED    +7   4.750.000    rival
  Castrín            DEF    +7   2.710.000    rival
  Gerard Moreno      DEL    +5   6.910.000    Computer
  ... 3 mas
  -> la mejor compra del dia: Álvaro Valles, +49 puntos por 6.240.000
```

**C) las dos abiertas, 20/09**

```
  De la Fuente       DEF   +24   4.990.000    rival      bolsillo de fichar 6.754.533
  Álvaro Valles      POR   +21   6.240.000    rival
  Veiga              DEF   +19   3.420.000    rival
  Castrín            DEF   +15   2.710.000    rival
  ... 5 mas
  -> la mejor compra del dia: De la Fuente, +24 puntos por 4.990.000
```

Nueve de las once y ocho de las nueve vienen **del mercado de rivales**. La puerta que
más trae es ésa; la que la hace servir de algo es la otra.

### Qué le falta a `would_pass` para dejar de ser cero

El campo es
[`acquisition_board.py:1285`](src/analysis/acquisition_board.py#L1285):

```python
fila["would_pass"] = fila["decision"] == "BID"
```

Se evalúa **antes** del reetiquetado, así que `would_pass` ya dice la verdad sobre el
listón. Es cero porque `decision` no llega a `BID`, y la cadena exacta es:

```
classify_operation            -> operation_class: TRADE
INTENT_BY_CLASS[TRADE]        -> intent: SPECULATION
budget_for_intent(SPECULATION)-> budget_applied: 3.760.204   (el de especular)
precio > budget_applied       -> decision: SUPERA_PRESUPUESTO
                              -> would_pass: False
```

> **El campo que falta cambiar no es `would_pass`: es `deployment.operation_class`.**
> Con `SIGNING`, `budget_applied` pasa de 3.760.204 a 6.754.533 y ocho de trece
> (18/09) y nueve de veinte (hoy) dejan de ser `SUPERA_PRESUPUESTO`.

### Los traspasos: qué pedían y qué se pagó

| fecha | jugador | de | a | **pidió** | **pagó** | mercado | sobre mdo |
|---|---|---|---|---:|---:|---:|---:|
| 10/08 | Kike Barja | Manzagool | Prinzipote | no consta | 330.000 | — | — |
| 19/08 | Lucas Cepeda | Prinzipote | **Pepe** | no consta | 463.500 | 460.000 | +0,8 % |
| 19/08 | Javi Hernández | **Pepe** | Pollo17 | **510.000** | **1.250.000** | 1.010.000 | +23,8 % |
| 24/08 | Castrín | **Pepe** | Pollo17 | no consta | 1.346.045 | 1.020.000 | +32,0 % |
| 28/08 | David Soria | Pollo17 | Luismi_Haz | no consta | 6.250.000 | 5.700.000 | +9,6 % |
| 28/08 | Laporte | Luismi_Haz | Pollo17 | **5.580.000** | **5.450.000** | 5.440.000 | +0,2 % |
| 28/08 | Brugué | Luismi_Haz | Pollo17 | no consta | 700.000 | 440.000 | +59,1 % |
| 04/09 | Yusi Enríquez | **Pepe** | Prinzipote | no consta | 1.226.068 | 1.140.000 | +7,5 % |
| 15/09 | Marcos Llorente | Pollo17 | Á. Retamosa | no consta | 5.700.000 | 5.600.000 | +1,8 % |
| 18/09 | Jonathan David | Luismi_Haz | Pollo17 | no consta | 8.400.000 | 7.970.000 | +5,4 % |

**El precio pedido sólo se recupera en 2 de 10**, y los dos casos dicen cosas
opuestas:

- **Javi Hernández: pedíamos 510.000 y nos pagaron 1.250.000. 2,45 veces.**
  (Comprobado en las fotos: lo teníamos anunciado a 210.000 el 12/08 y lo fuimos
  subiendo a 510.000.)
- **Laporte: pedían 5.580.000 y se pagaron 5.450.000. 0,98 veces.**

> **El precio pedido en Biwenger es un SUELO, no un precio.** El comprador ofrece por
> encima y el vendedor acepta o no, y el tablón sólo publica lo que se cerró. Con `n=2`
> y un rango de 0,98× a 2,45×, **no tenemos un número con el que decidir cuánto
> ofrecer, y no lo vamos a tener de esta fuente.**

**Lo que sí sirve, y es el número que pedías por otro camino:**

> **Un traspaso entre managers se cierra a una mediana de +7,5 % sobre el precio de
> mercado, y los nueve que tienen precio de mercado están POR ENCIMA.** `n = 9`, del
> 19/08 al 18/09.

De los nuestros: **vendimos** a +23,8 %, +32,0 % y +7,5 %, y **compramos** a +0,8 %.
`n = 4`, y con ese `n` no se declara una habilidad, pero las tres ventas están entre
las cuatro mejores primas de los diez.

---

## BLOQUE 4 — LAS TRECE MANOS VACÍAS

**Siete de golpe, hechas.** `test_futbolfantasy_source_v12` pasa de 20 pruebas a 13, y
las siete que se iban de vacío viven en **`scripts/mirar_la_fuente_unica.py`**, que
corre **7/7 limpio** contra el HTML y las fotos que hay en disco.

Las siete conservan **sus `assert` intactos**: el mirador las llama y un `assert` que
salta se imprime en vez de tumbar nada, porque lo que falla puede ser el mundo.

```
censo de manos vacias:  13  ->  6
```

Y el censo **encogió de verdad**, no sólo en la lista: `test_el_censo_solo_puede_encoger`
exige que no queden fantasmas, y las siete salieron.

**Lo que queda, y lo que costaría:**

```
  test_mercado_rivales_v1        2   lee las fotos
  test_doctrina_v1               1
  test_el_ciclo_publica_v1       1   comprueba si hay fotos
  test_la_pantalla_pinta_v1      1   ya esta retirada de la verja
  test_verja_determinista_v1     1   ES el vigilante, y es legitimo
```

De las seis, **una es legítima** —el vigilante, que se declara inaplicable a
propósito— y **otra está fuera de la verja**. Las cuatro de verdad son media tarde.

**Y la verja cazó un efecto lateral que yo no había visto:** al mover las siete,
`test_futbolfantasy_source_v12` dejó de mirar el reloj, y seguía censado como excepción
en `test_el_reloj_de_las_guardias_v1`. El censo se puso rojo con
*«estas excepciones ya no hacen falta»* y hubo que retirarlo. Es el mecanismo del
«sólo puede encoger» funcionando en la dirección correcta.

---

## LO QUE NO HICE, Y POR QUÉ

- **No encendí `BORDALAS_PRIMA_POR_TRAMO`.** Y además recomiendo no encenderlo todavía:
  con cero operaciones cerradas por encima de 3 M y −1.038.783 € en las nueve que hay
  por encima de 1,5 M, la curva empuja hacia donde nunca hemos ganado.
- **No cambié la etiqueta ni el `intent`.** Y creo que el arreglo no está en
  `classify_operation` sino encima: distinguir «no mejora» de «no se puede saber».
- **No abrí `MERCADO_DE_RIVAL`**, ni ninguna de las dos puertas.
- **No cambié el desempate de la cesta.** Medido y rechazado ayer.
- **No medí la prima descontando el movimiento del precio**, que es lo que de verdad
  falta antes de encender la curva. Es otro encargo y lo digo arriba.
- **No pude reejecutar las mañanas de la cesta**: no hay foto de dentro de la ventana.
- **No recuperé el precio pedido de 8 de los 10 traspasos.** No está en lo que
  guardamos, y aunque estuviera, con `n=2` va de 0,98× a 2,45×.
- **Ni una escritura contra Biwenger.** Ningún umbral, la ventana cerrada, el workflow
  sin tocar.

### La verja

```
163 de 163 OK      (eran 162; una guardia nueva)
```

Salida a fichero, árbol quieto, sin `git add -A`. **No empujo.**

### El `n`, y cuándo se cortó

| medida | `n` | corte |
|---|---|---|
| la prima por tramo | **194** ventas fechadas · 74 · 51 · 53 · **16** | tablón a 20/09 |
| el ratio deja de ser plano | 18 y 16 candidatos reales | fotos 18/09 y 20/09 |
| operaciones cerradas > 3 M | **0** · 4 abiertas | 10/08→20/09 |
| operaciones cerradas > 1,5 M | **9**, mediana −2,57 %, suma −1.038.783 € | idem |
| operaciones cerradas en el suelo | **8**, mediana +1,51 %, suma +28.867 € | idem |
| mejoran el once y salen TRADE | 20 de 54 · 23 de 55 | dos fotos |
| traspasos con precio pedido | **2** de 10 | fotos guardadas |
| traspasos con precio de mercado | **9** de 10, mediana +7,5 %, nueve positivos | tablón |
| manos vacías | 13 → **6** | barrido de `src/**` |

El tramo de 6 M+ tiene **n = 16**: pasa el mínimo de la casa (12) por cuatro. No lo
trataría como una tasa hasta doblarlo.
