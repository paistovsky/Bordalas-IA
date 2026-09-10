# ¿Habríamos hecho las compras de Pollo? — informe

**Fecha:** 10/09/2026 · **Verja:** 104/104 · **Push:** NO
**Llamadas nuevas:** ninguna. Tablón e histórico. **Listón:** sin tocar.
Re-ejecutable: `python -m scripts.los_viajes_de_los_rivales`

---

## La respuesta corta

**No era el reloj. Pero tampoco es el listón que creíamos.**

De las 36 compras cerradas de Pollo17, **habríamos hecho 6** — y las 30 que no
habríamos hecho valen **4.908.638 EUR: el 86 % de su dinero**.

Pero el motivo del rechazo **no es el 3 %**: 22 de sus 36 viajes lo superan. Lo
que las rechaza es la exigencia de **ritmo observado por el ojeador**, que no
existía antes del 08/09.

Y hay un resultado que va en contra de lo que yo esperaba y que cambia la
pregunta: **la dirección del precio al comprar no separa al que gana del que
pierde.**

---

## Pollo17 — 36 viajes, +5.700.524

**La forma del negocio:** mediana de **5 días**, **+3,9 %** por viaje, sobre
**3,35 M** de capital. Ganó en 32 de 36. No son pelotazos: es rotación rápida con
margen pequeño y muy consistente.

### Qué habría dicho cada vía

| vía | abre en |
|---|---:|
| SPECULATION | **0** de 36 |
| XI_UPGRADE | 1 de 36 |
| ROSTER_FILL | 6 de 36 |
| TENER | 1 de 36 |

```
LAS HARÍAMOS:      6 viajes,   791.886 EUR
NO LAS HARÍAMOS:  30 viajes, 4.908.638 EUR   <- el 83 % de sus compras
                                                y el 86 % de su dinero
```

### Por qué SPECULATION dice que no, y la trampa de ese cero

**Nuestro filtro no es un número, son dos puertas**, y llevábamos hablando solo
de la segunda:

1. **La compuerta de ritmo.** Sin **ritmo observado por el ojeador**, la vía ni
   se abre (`SIN_RITMO_OBSERVADO`). Con ritmo negativo tampoco
   (`PRECIO_CAYENDO`).
2. **El rendimiento**, `RENDIMIENTO_MINIMO_DEL_CAPITAL = 0.03`. Y ojo: es **rendimiento
   sobre el capital**, no un ritmo diario. Lo hemos llamado «el 3 % diario» y no
   lo es.

El cero de SPECULATION sale casi entero de la puerta 1, y **ese cero tiene
trampa**: el ojeador existe desde el 08/09, así que 35 de sus 36 compras son
anteriores a que la puerta pudiera abrirse siquiera. Eso es un accidente de
calendario, no un juicio sobre el filtro.

**El juicio sobre el filtro es este:** con el 3 % de rendimiento, **22 de sus 36
viajes pasan** (5.593.459 EUR). Es ex-post —lo que rindieron, no lo que se veía—
pero dice que **el 3 % no es la barrera**.

---

## Manzagool — 12 viajes, −2.879.680

Mediana de 8 días y **−7,5 %** por viaje. Perdió en 10 de 12.

```
LAS HARÍAMOS:      2 viajes, -1.031.100 EUR
NO LAS HARÍAMOS:  10 viajes, -1.848.580 EUR
```

**Nuestro filtro le habría ahorrado 1.848.580 de sus 2.879.680 — un 64 %.** Pero
le habría dejado hacer dos operaciones que pierden un millón. **Salva la mayoría
del daño, no todo.**

---

## El resultado que va en contra de lo que esperaba

Si la compuerta de ritmo hace su trabajo, comprar a los que suben debería separar
al ganador del perdedor. **Con estos datos, no lo hace:**

| | compró SUBIENDO | compró PLANO | compró CAYENDO |
|---|---:|---:|---:|
| **Pollo17** | 12 veces, **+2.720.565** | 7, +386.486 | 6, **+1.781.473** |
| **Manzagool** | 3 veces, **−1.235.200** | 0 | 6, −574.630 |

- **Pollo ganó 1,78 M comprando jugadores que CAÍAN.** Nuestra compuerta
  `PRECIO_CAYENDO` habría bloqueado esas seis operaciones.
- **Manzagool perdió 1,24 M comprando jugadores que SUBÍAN** — justo las que
  nuestra compuerta habría dejado pasar.

La mediana del ritmo al comprar sí los separa (+0,00 %/día Pollo contra
−0,51 %/día Manzagool), pero **el dinero va al revés**.

### El límite de esta medición, y es serio

El histórico local tiene **7 precios por jugador**: del 12 al 17/08 y luego un
salto a hoy. De los 36 viajes de Pollo, solo **3** tienen una lectura de ritmo
**fresca** (≤2 días antes de la compra); el resto usa un precio de hasta 22 días
antes. **Con 3 y 2 lecturas frescas, la tabla de arriba es una señal, no una
prueba.**

Lo que haría falta para cerrarlo: precios diarios de todos los jugadores durante
un mes. Los tenemos desde hoy hacia adelante, no hacia atrás.

---

## Entonces, ¿listón o reloj?

**Ninguno de los dos, tal como estaban planteados.**

- **No es el reloj.** Aunque la ventana hubiera funcionado, nuestras vías se
  habrían abierto en 6 de 36. El reloj no era lo que nos separaba de ese negocio.
- **No es el 3 %.** Lo superan 22 de 36.
- **Es que no estamos jugando a lo que juega Pollo.** Él hace rotación de 5 días
  al 3,9 %, comprando en la subasta y devolviéndole el jugador al Computer.
  Nosotros buscamos **rampas** —ritmo observado, racha, demanda— y eso es otro
  negocio, uno que en esta liga apenas existe.

**Y una advertencia que no me esperaba:** la compuerta de ritmo, que es la que de
hecho rechaza casi todo, **no discrimina** en esta muestra. Bloquea las 6
compras con las que Pollo ganó 1,78 M y deja pasar las 3 con las que Manzagool
perdió 1,24 M. Si eso se confirma con datos frescos, la compuerta está cobrando
un peaje sin dar nada a cambio.

**No he movido el listón**, como pediste. Lo que propongo mirar antes de tocarlo:

1. **Un mes de precios diarios.** Es lo único que convierte esa tabla en prueba.
   Ya se están guardando; hay que esperar.
2. **Medir la prima de recompra del Computer.** Si el negocio de Pollo es que el
   Computer recompra por encima del precio, eso es medible y no necesita ninguna
   rampa — y explicaría por qué gana 32 de 36 veces con un margen tan regular.

---

## Lo que no hice

- **No he movido ningún umbral**, ni el 3 %, ni la compuerta de ritmo.
- **No he reconstruido `expected_value` de fechas pasadas**: haría falta el
  estado completo del mercado de cada día y no lo tenemos. Por eso el 3 % se
  compara **ex-post** y lo digo en cada sitio donde aparece.
- **No he reconstruido XI_UPGRADE / ROSTER_FILL / TENER fuera del 12-17/08**:
  dependen de cómo estaba nuestra plantilla ese día, y solo hay fotos de esa
  semana. Fuera de ahí sale «no reconstruible» en vez de un número inventado.
- **Ninguna escritura. No he hecho push.**

---
---

# AMPLIACIÓN (10/09/2026) — de dónde sale la ganancia

## La descomposición, en tres partes que suman

El viaje mediano de Pollo rinde **+3,86 % en 5 días**:

```
(a) lo que gana al COMPRAR        +0,15 %    compra POR DEBAJO del precio
(b) prima del Computer al vender  +2,49 %
(a) + (b)                         +2,64 %    <- el 68 % de su ganancia
(c) lo que sube mientras lo tiene +1,23 %    en 5 días = +0,25 %/día
```

**(c) es pequeño y es la deriva del mercado**, no una rampa: +0,25 %/día es
exactamente la mediana del mercado entero.

**Te habías equivocado en la hipótesis, y lo dice el propio dato:** manda (a)+(b).
Su negocio **es la subasta**, no el calendario.

## La hipótesis del calendario, refutada

```
Pollo17
   ATRAVIESAN una jornada   12 viajes  +3.396.893  +8,7 % en 10 días (+0,87 %/día)
   NO atraviesan ninguna    24 viajes  +2.303.631  +3,2 % en  2 días (+1,29 %/día)
```

**Dos tercios de sus viajes no ven jugar al jugador**, y rinden **mejor por día**
que los que sí. Aguantar la jornada da más beneficio absoluto solo porque dura
cinco veces más.

Manzagool, para contraste: pierde en los dos grupos (−0,53 %/día con jornada,
−2,05 %/día sin ella). El calendario no le salva ni le hunde.

## Dónde está su ventaja: no paga de más

Lo que paga cada manager **por encima del precio de mercado** al ganar una
subasta:

```
Pollo17      -0,15 %   n=8    <- compra al precio, o por debajo
Prinzipote   +0,20 %   n=1
DiosMande    +2,27 %   n=4
Luismi_Haz   +2,31 %   n=12
Manzagool    +7,95 %   n=1
Mex         +11,81 %   n=2
NOSOTROS    +29,23 %   n=1
```

**Y no es que venda mejor.** Su prima de venta, +2,49 %, es la **peor** de los
cinco que venden (la mediana de la liga es +2,91 %; nosotros sacamos +3,91 %).

**Gana porque no regala el margen al comprar.** Eso es todo.

### Lo que eso significa para nosotros

Nuestra única compra en subasta medida pagó **+29,23 %** sobre el precio. Con la
prima de venta en +2,5 %, esa operación nacía perdiendo un 27 %.

**La curva de la prima del 11/09 ya arregló esto** —pujar a `precio + 0,25 %`—
y esta medición dice que nos coloca **exactamente en la zona de Pollo**. No hay
nada que cambiar ahí: hay que dejarla funcionar.

Y explica el 86 % de su dinero que nuestro filtro rechazaba: **no es que
buscáramos rampas donde no las hay. Es que buscábamos rampas en lugar de buscar
el spread.**

## El arreglo del nombre

`MIN_SPECULATION_YIELD` → **`RENDIMIENTO_MINIMO_DEL_CAPITAL`**, en 23 ficheros.

Es `expected_value / bid`: lo que rinde la operación sobre el capital que
inmoviliza. **No es un ritmo diario y nunca lo fue.** Un viaje de cinco días al
3 % pasa el listón; uno que sube un 3 % diario cinco días rinde un 16 %.

**El nombre malo tuvo consecuencia:** se comparó contra ritmos diarios de rivales
para juzgar si nuestro filtro era duro, y esa comparación no significaba nada.

Barrido de «3 % diario» hecho **con cuidado**: donde se refería al listón, se
corrige; donde de verdad habla de un ritmo por día —`price_store_fixture`,
`test_retrotest_rampa`, el +2,33 %/día de `acquisition_valuation`— **no se ha
tocado**, porque ahí sí es diario. Al informe del 26/09 se le añadió una nota de
corrección en vez de reescribir lo que dijimos entonces.

## Lo que sigue sin poder medirse

La descomposición usa las operaciones que caen en un día con foto: **n=8 compras
y n=15 ventas de Pollo**. Es suficiente para ver la diferencia de 30 puntos entre
su prima de compra y la nuestra, y no lo es para afinar decimales.

**No he tocado la compuerta de ritmo**, como pediste.
