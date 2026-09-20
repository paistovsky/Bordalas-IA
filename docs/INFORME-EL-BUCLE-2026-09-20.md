# CORTAR EL BUCLE

**Fecha:** 2026-09-20 (sexto del día) · **Rama:** `medir/el-bucle`, desde
`arreglo/la-prima-y-la-etiqueta` · **Escrituras contra Biwenger:** ninguna · **Nada
encendido, nada arreglado.** Todo es medir.

**Verja: 163 de 163.**

---

## ANTES DE NADA: DOS CORRECCIONES MÍAS, Y LA SEGUNDA TUMBA MIS DOS ÚLTIMOS INFORMES

### 1. La vara SÍ es el peor titular

Dije que «para defensas la vara era Cabrera (9 pts), que no es titular, mientras el
peor central titular era Djené (16)». **Es falso, y mezclé dos días.**

```
18/09   DEF titulares: Djene 16, Manu Sanchez 17, Jonny 18   -> vara = Djene (16)
20/09   DEF titulares: Cabrera 9, Manu Sanchez 17, Chust 21  -> vara = Cabrera (9)
```

Cabrera **es titular** hoy. `la_vara`
([toda_la_liga.py:95](src/analysis/toda_la_liga.py#L95)) recorre **sólo el once** y se
queda con el de menos puntos de cada posición. Es el peor titular, por construcción, y
está bien.

### 2. La vara no es lo que mide el motor — y por eso mis cuentas de los dos últimos días estaban infladas

La vara compara **puntos acumulados** contra el **peor titular**. El motor compara
**puntos esperados del resto de temporada** contra **el titular que de verdad
perdería el puesto**, y pesa la probabilidad de jugar y la jerarquía.

Hoy, con Dmitrovic en la portería:

```
Alvaro Valles     49 pts acumulados,  108 esperados
Dmitrovic         28 pts acumulados,  182 esperados,  95 % titular, Clave

xi_reason: "Suma 108 puntos y el que sustituiria tiene 182. No es una mejora."
la vara:   +21
```

> **Los «+49 de Valles», los «17 de 34 mejoran el once», los «24 de 35», los «+153» y
> «+172 puntos» de mis dos últimos informes son números de la VARA. Miden puntos
> acumulados contra el peor titular, que no es lo que decide nada.** La propia
> `el_vestuario_libre` lo avisa en su `reason`: *«Esta lista NO puja.»* Lo usé como si
> pujara.

Lo que sigue usa las dos varas y dice cuál está usando cada vez.

---

## BLOQUE 1 — EL BUCLE

### Existe, se disparó una vez, y fue en la portería

| | 18/09 | 20/09 |
|---|---:|---:|
| candidatos | 54 | 55 |
| `SIN_PRONOSTICO` | **4** | **0** |
| … de ellos, por falta de datos de **la vara** | **4** | — |
| … por falta de datos del **candidato** | **0** | — |

**Los cuatro eran porteros:**

```
  Alvaro Valles   POR   49 pts   "No hay pronostico de titularidad DEL QUE SALDRIA"
  David Soria     POR   42 pts   idem
  Dmitrovic       POR   31 pts   idem
  Szczesny        POR   -2 pts   idem
```

Y la vara de portero ese día era **Esquivel**: comprado por la cesta el **18/09 a las
07:05 por 150.376 €**, con **0 puntos** y **`starter_probability: None`**.

> **El motor no pudo valorar a Dmitrovic el 18/09 porque el portero contra el que
> tenía que compararlo lo había comprado la cesta esa misma mañana en el suelo. El
> 20/09 compraste a Dmitrovic tú, a mano, por 4.992.001 €.**

Ése es el bucle entero, con nombre, fecha y factura.

### Por qué en la portería y en ninguna otra posición

```
titulares por posicion el 18/09:   POR 1   ·   DEF 3   ·   MED 5   ·   DEL 2
```

El sustituido lo elige
[`acquisition_valuation.py:456`](src/analysis/acquisition_valuation.py#L456):

```python
candidatos_a_salir = [
    min(titulares_pos, key=lambda j: safe_int(j.get("points")))
]
```

**El peor titular POR PUNTOS.** Y un jugador recién comprado en el suelo tiene 0
puntos, así que gana siempre ese concurso — y es, a la vez, el único que no tiene
pronóstico. **Las dos cosas son el mismo hecho.**

Con un solo titular en la posición no hay segunda opinión: ese jugador **es** la vara,
sin alternativa. Con tres defensas o cinco medios, un fichaje en el suelo no se lleva
la vara por delante.

Y el código **ya cazó este bucle una vez, un piso más abajo**. El comentario de
[`acquisition_valuation.py:441`](src/analysis/acquisition_valuation.py#L441) lo cuenta:

> «Tienes nueve defensas, el peor es malo, compras otro. […] El sustituido es el peor
> TITULAR de esa posición. **De paso desaparece el bucle sin prohibir nada.**»

Lo arreglaron para los defensas en agosto. La portería es la misma forma con `n = 1`
titular, y ahí el arreglo no alcanza.

### A cuántos cegó cada vara de relleno, y el `n`

```
  Esquivel  (150.376 EUR, 0 pts)   vara de POR el 18/09   cego a 4 candidatos
                                                          (3 de ellos reales)
```

**Y ése es todo el censo, con su `n` y su límite:** sólo tengo **dos fotos** con once
y candidatos —18/09 y 20/09—, así que el bucle se puede observar en **2 días** y se
disparó en **1**. Esquivel entró el 18/09 a las 07:05 y salió el 20/09 a las 08:55:
**dos días de exposición**. Iturbe, el otro portero de 150.376 €, sigue en la
plantilla y **no llegó a ser titular**, así que no llegó a ser vara.

No puedo reconstruir más atrás: el once no está guardado día a día. Decirlo es parte
de la medición.

### Dónde cortarlo — mi voto, y por qué los otros dos no valen aquí

**Coincido contigo: abajo.** Y ahora puedo decir por qué los otros dos no sirven para
este caso, que es más útil que coincidir.

| opción | qué toca | ¿habría arreglado los cuatro del 18/09? |
|---|---|---|
| **arriba** — que la cesta no compre 0 puntos | `la_subasta` / `elegir_la_cesta` | **Sí, ese día.** Sin Esquivel, la vara habría sido Dituro (6 pts, 50 % titular, Importante), que sí tiene pronóstico |
| **en medio** — sin pronóstico no se puede ser vara | `acquisition_valuation.py:456` | **NO. Cero de cuatro.** Con **un** titular en portería no hay alternativa: quitar a Esquivel deja la vara vacía y el veto salta igual |
| **abajo** — una comparación sin datos dice «no lo sé» y escala | `deployment.classify_operation` | **Sí, los cuatro. Y el siguiente.** |

**«En medio» no funciona aquí y eso está medido**, no razonado: la posición tenía un
solo titular.

**«Arriba» funciona este día y no el siguiente.** Prohibir comprar a 0 puntos no
arregla el hueco: cualquier fichaje recién llegado —comprado en el suelo o no— llega
sin historial. El agujero es de información, no de precio.

**«Abajo» es donde se pierde el dato**, y es un sitio concreto. Hoy
`xi_upgrade_value` **ya dice «no lo sé»**: devuelve `SIN_PRONOSTICO` con su frase
escrita. Lo que pasa es que lo devuelve con `value = 0`, y en
[`deployment.py:202`](src/analysis/deployment.py#L202) un cero por «no lo sé» y un
cero por «no mejora» son **el mismo cero**:

```python
compensan = [via for via in fichaje if via["value"] > price]
if not compensan:
    fichaje = []          # aqui mueren los dos ceros, indistinguibles
```

> **Doctrina 24, del revés, exactamente como lo dijiste: el motor no pasa con las
> manos vacías, pero rechaza con las manos vacías.** Y lo hace en una línea que no
> sabe que las manos estaban vacías, porque el dato se perdió un piso antes.

**Lo que yo haría, y no hago:** que `classify_operation` distinga una vía que vale
cero de una vía que **no se ha podido valorar**, y que el segundo caso no descarte el
fichaje: lo marque. El rechazo silencioso se convierte en una pregunta visible, que es
justo lo que dijiste que vale aunque no se haga nada más.

**No lo he tocado.**

---

## BLOQUE 2 — LOS CINCO MOTIVOS, CUANTIFICADOS

Con la vara —puntos acumulados—, que es la que infla:

**18/09, 54 candidatos**

| motivo | cands | mejoran (vara) | **puntos** | los 3 que más suman |
|---|---:|---:|---:|---|
| **`SIN_PRONOSTICO`** | **4** | 3 | **122** | Valles +49, Soria +42, Dmitrovic +31 |
| `PIERDE_TITULARIDAD` | 7 | 5 | 70 | Baena +32, De la Fuente +17, Grimaldo +7 |
| (sin valorar) | 8 | 5 | 23 | Pépé +11, Gerard Moreno +5, Marc Roca +3 |
| `NO_MEJORA_JERARQUIA` | **14** | **1** | 23 | Mariano +23 |
| `NO_MEJORA` | 10 | 4 | 17 | Castrín +7, Nico Williams +5, Bellerín +3 |
| `NO_MEJORA_TITULARIDAD` | 10 | 2 | 7 | Starfelt +5, Guridi +2 |
| `MEJORA_INSUFICIENTE` | 1 | 1 | 7 | Bardeli +7 |

**20/09, 55 candidatos**

| motivo | cands | mejoran (vara) | **puntos** | los 3 que más suman |
|---|---:|---:|---:|---|
| **`PIERDE_TITULARIDAD`** | 11 | 8 | **122** | Fermín +40, Baena +32, De la Fuente +24 |
| `NO_MEJORA` | 10 | 10 | 92 | Valles +21, Castrín +15, Starfelt +12 |
| `NO_MEJORA_JERARQUIA` | **19** | **4** | 35 | Mariano +21, C. Romero +11, Pedro Díaz +2 |
| `MEJORA_INSUFICIENTE` | 2 | 2 | 20 | Veiga +19, Denis Suárez +1 |
| (sin valorar) | 5 | 2 | 11 | Álvaro García +8, Marc Roca +3 |
| `NO_MEJORA_TITULARIDAD` | 8 | 3 | 9 | Guridi +5, Koundé +3, Berenguer +1 |

### `NO_MEJORA_JERARQUIA`: no, el arreglo del bloque 1 no se lo lleva

**33 candidatos entre los dos días y sólo 5 mejoran la vara. 58 puntos en total, 1,8
por candidato — el más flojo de los seis motivos.**

Y no tiene nada que ver con el bucle: su frase es *«sustituiría a un Importante por un
Revulsivo: 2 escalones de bajada. El once empeora toda la temporada, no sólo esta
jornada»*. Eso es una comparación **con datos de los dos lados**, no un hueco. El
arreglo de abajo no lo toca, y es correcto que no lo toque.

### El caso Baena: sí, el motor acierta y la vara falla

```
Baena      51 pts acumulados,  74 esperados,  70 % titular,  Rotacion
xi_reason: "Suma 17 puntos pero juega menos: 70 % titular contra
            80 % del que sale. Los puntos estan en la hoja, no en el campo."
la vara:   +32
```

Tres diferencias, y las tres a favor del motor:

1. **El motor compara esperados (74), la vara acumulados (51).**
2. **El motor compara contra el titular que de verdad saldría**, no contra el peor del
   once. Por eso dice +17 y la vara +32.
3. **El motor pesa la probabilidad de jugar**: 70 % contra 80 %. Baena está en
   rotación y los 51 puntos ya están cobrados.

Y se generaliza: **Alfonso Herrero** (180 esperados) contra Dmitrovic (182) → «no es
una mejora», y la vara diría +7. **Valles** (108) contra Dmitrovic (182) → «no es una
mejora», y la vara diría +21.

> **Tenías razón, y va más lejos de lo que apuntabas: si el motor acierta y la vara
> falla, entonces el coste de las puertas cerradas que yo calculé estos dos días está
> inflado. Lo que de verdad se quedó fuera no son 17 ni 24 jugadores: son los que el
> motor NO PUDO VALORAR —los cuatro de `SIN_PRONOSTICO`— más los que rechazó por
> motivos que habría que auditar uno a uno.**

Eso **no** cambia el bloque 1: lo refuerza. El único motivo donde el motor no se
equivoca ni acierta —**porque no mira**— es `SIN_PRONOSTICO`.

### Cuál se lleva más puntos por delante

**`SIN_PRONOSTICO`, y por densidad no hay color:**

```
SIN_PRONOSTICO         122 puntos con  4 candidatos  ->  30,5 por candidato
PIERDE_TITULARIDAD     192 puntos con 18 candidatos  ->  10,7
NO_MEJORA              109 puntos con 20 candidatos  ->   5,5
NO_MEJORA_JERARQUIA     58 puntos con 33 candidatos  ->   1,8
```

Y es el único de los seis que **no es un juicio**: es una ceguera. Los otros cinco
pueden estar bien o mal y hay que auditarlos; éste no puede estar bien, porque no
compara nada.

---

## BLOQUE 3 — `VENTA / COMPRA`

`n = 23` operaciones cerradas, todas las de la temporada.

| tramo de COMPRA | plazo | n | mediana | en verde | suma |
|---|---|---:|---:|---:|---:|
| suelo (<300 k) | ≤ 2 días | 1 | +3,87 % | 100 % | +5.824 |
| suelo (<300 k) | 2 – 7 días | 7 | +0,75 % | 100 % | +23.043 |
| **suelo (<300 k)** | **todo** | **8** | **+1,51 %** | **100 %** | **+28.867** |
| 300 k – 1,5 M | ≤ 2 días | 2 | −1,50 % | 0 % | −37.176 |
| 300 k – 1,5 M | 2 – 7 días | 2 | +3,20 % | 50 % | +75.119 |
| 300 k – 1,5 M | > 7 días | 2 | +95,10 % | 100 % | +939.568 |
| **300 k – 1,5 M** | **todo** | **6** | +5,99 % | 50 % | **+977.511** |
| 1,5 M – 3 M | ≤ 2 días | 2 | −0,50 % | 50 % | −14.347 |
| 1,5 M – 3 M | 2 – 7 días | 3 | −8,10 % | 0 % | −606.302 |
| 1,5 M – 3 M | > 7 días | 4 | −0,48 % | 50 % | −418.134 |
| **1,5 M – 3 M** | **todo** | **9** | **−2,57 %** | **33 %** | **−1.038.783** |
| **≥ 3 M** | — | **0** | — | — | — |
| **TODAS** | | **23** | **+0,55 %** | 61 % | **−32.405** |

> **Ninguna celda de la rejilla llega a `MIN_SAMPLES = 12`. Ni una.** La mayor tiene
> 9. Están todas marcadas y ninguna rellenada.

### ¿Se gana sólo abajo? Sí, con esas palabras — pero hay una excepción que lo cambia todo

> **Sólo se gana abajo: las ocho operaciones a precio de suelo son las únicas ocho de
> veintitrés que están todas en verde, y suman +28.867 €.**

Pero el `+939.568` del tramo 300 k – 1,5 M a más de 7 días no es reventa: **son las dos
ventas a managers.**

```
A QUIEN LE VENDIMOS
  Computer      n=21   mediana +0,55 %   suma   -900.517 EUR
  Prinzipote    n= 1   +143,27 %         suma   +722.068 EUR
  Pollo17       n= 1   + 12,17 %         suma   +146.044 EUR
```

Y sólo al Computer, por tramos:

```
  suelo (<300 k)   n= 8   +1,51 %   100 % verde     +28.867
  300 k - 1,5 M    n= 4   -1,50 %    25 %          +109.399
  1,5 M - 3 M      n= 9   -2,57 %    33 %        -1.038.783
  >= 3 M           n= 0        -        -                 -
  TODAS            n=21   +0,55 %    57 %          -900.517
```

> **Al Computer perdemos 900.517 € en veintiuna operaciones. A los managers ganamos
> 868.112 € en dos.**

`n = 2` es una anécdota y lo digo (doctrina 55). Pero la dirección es **la contraria**
a toda la tesis de la cesta, y es el mismo sitio donde está la puerta cerrada del
bloque 4.

**Y la respuesta a la prima:** con cero operaciones por encima de 3 M y nueve en rojo
entre 1,5 y 3 M, **no hay ningún tramo por encima del suelo donde ganemos**. El número
que faltaba para poder encender `BORDALAS_PRIMA_POR_TRAMO` dice que no se encienda.

### ¿El plazo lo elegimos o nos lo encuentran? Lo elegimos, en un 75 %

Sobre las nueve ventas al Computer que tienen publicación apuntada —el libro empieza el
11/09, así que `n = 9` de 21—:

```
  dias de COMPRA a venta     mediana  4,71
  dias de PUBLICAR a venta   mediana  1,17
  -> esperando comprador: el 25 % del plazo
```

> **Tres cuartas partes del plazo son nuestras: el tiempo que el jugador pasa en la
> plantilla antes de que lo publiquemos. Una vez publicado, el Computer lo compra en
> poco más de un día.**

Así que el −22,4 % de Djené en 31 días no es que «nos encontraran» el plazo: es que
tardamos en sacarlo. Eso es una decisión, y decisiones se pueden arreglar.

Con el aviso del `n`: nueve de veintiuna, y las doce sin publicación apuntada son las
anteriores al 11/09 — entre ellas los grandes perdedores. **Lo medido cubre el tramo
bueno y no el malo**, así que el 75 % es un suelo, no un techo.

---

## BLOQUE 4 — LA TERCERA PUERTA

### Tu apuesta era cero. Son cuatro y cuatro

| | 18/09 | 20/09 |
|---|---:|---:|
| pasan con las dos puertas abiertas | 11 | 9 |
| **sobreviven al tope que rige (+0,25 %)** | **4** | **4** |
| sobreviven al discutido (+1,95 %) | **4** | **4** |
| sobreviven a la mediana de traspasos (+7,5 %) | 4 | 5 |

**Y el motivo es que el recargo es bimodal**: un rival que quiere vender pide **por
debajo** del mercado, y uno que no quiere pide **+13 % a +40 %**. No hay casi nada en
medio.

```
18/09   Bellerin   -1,9 %   Berenguer  -0,3 %   |   Valles +18,2 %  Castrin +39,7 %
20/09   Veiga      -1,2 %   C. Romero  -1,7 %   |   Castrin +30,3 %  Bellerin +31,9 %
        A. Garcia  -0,8 %   H. Alvarez -1,8 %   |   De la Fuente +16,9 %
```

> **Subir el tope de +0,25 % a +1,95 % no desbloquearía ni un jugador más en ninguno
> de los dos días. El tope no es lo que ata.**

(De los cuatro del 18/09, dos —Gerard Moreno y Grimaldo— son del Computer y no llevan
recargo por definición. Los que vienen de rivales y sobreviven son dos el 18/09 y
cuatro el 20/09.)

### ¿El tope de la subasta ciega se está aplicando a una negociación? Sí

`PRIMA_MAXIMA_DE_PUJA = 0.0025` sale de
[`rival_bid_model.py:906`](src/analysis/rival_bid_model.py#L906), y su calibración es
**íntegramente del Computer**:

- la curva de 115 **subastas del tablón**, donde perder no cuesta nada;
- cruzada contra la prima que el **Computer** paga al recomprar (+1,8 % sobre 107
  ventas).

Las filas del mercado de rivales pasan por **todo** el camino de valoración antes del
reetiquetado, así que se les calcula el mismo `prima_maxima_percent: 0.25` que a una
puja al Computer.

> **Sí: un número calibrado sobre una subasta ciega —donde perder es gratis y por eso
> conviene pujar bajo por muchos— se le está aplicando a una negociación con una
> persona, donde perder significa que el jugador se queda con el rival y hay que
> volver a pedirlo.** Son mecánicas opuestas. Y como `MERCADO_DE_RIVAL` cierra antes
> de que se puje, **nunca se ha ejercido**: el número está ahí, listo, sin haberse
> aplicado nunca a lo que no es.

**El número es tuyo y no propongo ninguno.**

### Valles, concreto

| | mercado | piden | al +7,5 % ofreceríamos | ¿cabe en 6.754.533? | ¿llega a lo que piden? |
|---|---:|---:|---:|---|---|
| 18/09 | 5.280.000 | 6.240.000 | 5.676.000 | sí (bolsa 9.743.865) | **no** |
| 20/09 | 5.500.000 | 6.240.000 | **5.912.500** | **sí** | **no** |

> **Cabe de sobra en el bolsillo de fichar y se queda 327.500 € por debajo de lo que
> piden.** Para llegar al anuncio harían falta **+13,5 %** sobre el mercado, no +7,5 %.

Y la mediana de +7,5 % es lo que se **cerró**, no lo que se **pidió**: ya medimos ayer
que el precio pedido es un suelo y que en el único caso comprobable se pagó 2,45 veces
lo pedido. Así que +7,5 % tampoco es una guía fiable para esta negociación concreta.

---

## LO QUE NO HICE, Y POR QUÉ

- **No corté el bucle.** El bloque 1 mide y vota; el voto está arriba, con el dato de
  por qué las otras dos opciones no sirven aquí.
- **No toqué la vara, ni el `intent`, ni `deployment.py:202`, ni
  `acquisition_valuation.py:456`.**
- **No abrí `MERCADO_DE_RIVAL` ni toqué ningún tope.**
- **No encendí `BORDALAS_PRIMA_POR_TRAMO`** — y la medición del bloque 3 dice que no
  se encienda: no hay ningún tramo por encima del suelo donde ganemos.
- **No pude reconstruir el bucle más atrás de dos días.** El once no se guarda día a
  día; sólo hay dos fotos con once y candidatos. El censo de «relleno que fue vara» es
  de `n = 2 días`, y se disparó en uno.
- **No audité los otros cinco motivos uno a uno.** `PIERDE_TITULARIDAD` se lleva 192
  puntos entre los dos días y el caso de Baena sugiere que el motor acierta, pero eso
  es una muestra de uno.
- **No medí el plazo de las doce operaciones anteriores al 11/09**, que son las que
  más perdieron. El libro de publicación no llega.
- **Ni una escritura contra Biwenger.** La ventana cerrada, el workflow sin tocar.

### La verja

```
163 de 163 OK      (sin cambios de codigo: este encargo solo mide)
```

Salida a fichero, árbol quieto, sin `git add -A`. **No empujo.**

### El `n`, y cuándo se cortó

| medida | `n` | corte |
|---|---|---|
| el bucle | **2 días con foto**, disparó en 1 | 18/09 y 20/09 |
| `SIN_PRONOSTICO` por la vara | **4 de 4** (18/09) · 0 de 55 (20/09) | idem |
| los cinco motivos | 54 y 55 candidatos | idem |
| `venta / compra` | **23** operaciones cerradas · **ninguna celda llega a 12** | 10/08→20/09 |
| al Computer | **21**, suma −900.517 € | idem |
| a managers | **2**, suma +868.112 € | idem |
| el plazo publicado | **9 de 21**, el libro empieza el 11/09 | idem |
| sobreviven al tope | 4 de 11 · 4 de 9 | dos fotos |

Y el aviso que más pesa: **las celdas de `venta / compra` no llegan a doce ni una
sola**. Todo lo de arriba es dirección, no tasa.
