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
2. **El rendimiento**, `MIN_SPECULATION_YIELD = 0.03`. Y ojo: es **rendimiento
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
