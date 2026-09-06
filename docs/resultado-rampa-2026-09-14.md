# LA RAMPA — resultado

Rama `rampa/valorar-tener`. **Verja: 80 de 80 en verde** (78 al empezar).
`main` intacto. `.github/workflows/bordalas-live.yml` sin tocar.
`npm run build` pasa. **Sin push.**

Medido contra `diagnostico/status.json` del **06/09/2026 09:33**.

---

## Lo que entra en el commit

Miré `git status` antes, como pediste. **Trece ficheros, todos míos.**
Ninguno suelto:

```
 M dashboard-v8/src/components/SaleOrderPanel.jsx     ritmo neto
 M dashboard-v8/src/pages/MarketPage.jsx              columna TENER
 M scripts/run_validation_gate.py                     dos guardias nuevas
 M src/analysis/acquisition_valuation.py              cuarta via
 M src/analysis/deployment.py                         clase por via que compensa
 M src/analysis/sale_order.py                         tramo "cae y no juega"
 M src/analysis/test_orden_de_venta_v1.py             + 3 pruebas
 M src/analysis/test_pantalla_lee_lo_publicado_v1.py  + 2 pruebas
?? docs/ENCARGO-LA-RAMPA-2026-09-14.md
?? src/analysis/hold_backtest.py                      el retrotest
?? src/analysis/hold_value.py                         la via TENER
?? src/analysis/test_no_contar_dos_veces_v1.py        12 pruebas
?? src/analysis/test_retrotest_rampa_v1.py            11 pruebas
```

---

# BLOQUE 1 — Tener paga. Y paga mucho.

**5.577 operaciones reconstruidas** del almacén de precios: 571 jugadores,
**6 días (12–17/08/2026)**, 5 transiciones diarias por jugador.

**Sobre la fuente, para que no haya duda.** Está en `data/`, y la regla de
la casa es no medir *el estado* contra `data/` porque miente sobre el hoy.
Un histórico es otra cosa: no pretende ser el estado actual, pretende ser
lo que pasó, y lo que pasó no caduca. **Pero es agosto, no septiembre**, y
eso hay que tenerlo delante al leer la tabla.

## El resultado, en una línea

> Comprar a alguien que sube **más del 1 % diario** con **un día de racha**
> y venderlo **tres días después** da una mediana de **+4,47 %** y falla
> solo el **5 %** de las veces. Sobre 142 operaciones.

## La tabla completa

Celdas con menos de 30 operaciones marcadas como insuficientes; celdas sin
ninguna, marcadas como vacías.

| tasa | racha | m | n | mediana | p25 | p75 | % en pérdida |
|---|---|---:|---:|---:|---:|---:|---:|
| CAE | 1 día | 1 | 214 | −1,62 % | −2,63 % | −0,76 % | **88 %** |
| CAE | 1 día | 2 | 149 | −2,99 % | −4,76 % | −1,83 % | 94 % |
| CAE | 1 día | 3 | 137 | −4,76 % | −6,98 % | −2,63 % | **95 %** |
| CAE | 1 día | 4 | 120 | −5,32 % | −8,64 % | −2,97 % | 94 % |
| CAE | 2 días | 1 | 138 | −1,29 % | −2,17 % | −0,70 % | 91 % |
| CAE | 2 días | 2 | 126 | −3,03 % | −4,54 % | −1,79 % | 94 % |
| CAE | 2 días | 3 | 114 | −3,96 % | −5,88 % | −2,21 % | 93 % |
| CAE | 3-7 días | 1 | 216 | −1,50 % | −2,27 % | −0,73 % | 93 % |
| CAE | 3-7 días | 2 | 104 | −2,85 % | −4,40 % | −1,51 % | 94 % |
| 0-0,25 % | *todas* | *todos* | 6-26 | *muestra insuficiente* | | | |
| 0,25-0,5 % | 1 día | 1 | 35 | +0,28 % | +0,15 % | +0,35 % | 9 % |
| 0,25-0,5 % | 1 día | 2 | 32 | +0,54 % | +0,22 % | +0,69 % | 16 % |
| 0,25-0,5 % | 1 día | 3 | 32 | +0,41 % | +0,00 % | +0,86 % | 22 % |
| 0,25-0,5 % | 1 día | 4 | 31 | +0,27 % | −1,40 % | +1,08 % | 39 % |
| 0,25-0,5 % | 2 días | *todos* | 26 | *muestra insuficiente* | | | |
| 0,25-0,5 % | 3-7 días | 1 | 64 | +0,24 % | −0,16 % | +0,46 % | 25 % |
| 0,25-0,5 % | 3-7 días | 2 | 31 | +0,00 % | −1,00 % | +0,51 % | 42 % |
| 0,5-1 % | 1 día | 1 | 68 | +0,60 % | +0,50 % | +0,81 % | **0 %** |
| 0,5-1 % | 1 día | 2 | 68 | +1,16 % | +0,79 % | +1,50 % | 3 % |
| 0,5-1 % | 1 día | 3 | 66 | +1,25 % | +0,75 % | +1,75 % | 12 % |
| 0,5-1 % | 1 día | 4 | 66 | +1,44 % | +0,30 % | +2,24 % | 21 % |
| 0,5-1 % | 2 días | 1 | 56 | +0,53 % | +0,40 % | +0,72 % | 0 % |
| 0,5-1 % | 2 días | 2 | 56 | +0,62 % | +0,21 % | +1,02 % | 7 % |
| 0,5-1 % | 2 días | 3 | 55 | +0,60 % | −0,28 % | +1,36 % | 31 % |
| 0,5-1 % | 3-7 días | 1 | 91 | +0,44 % | +0,00 % | +0,65 % | 11 % |
| 0,5-1 % | 3-7 días | 2 | 56 | +0,70 % | −0,29 % | +0,92 % | 25 % |
| **> 1 %** | **1 día** | **1** | 153 | **+2,30 %** | +1,35 % | +4,55 % | **1 %** |
| **> 1 %** | **1 día** | **2** | 148 | **+3,80 %** | +2,60 % | +8,06 % | **3 %** |
| **> 1 %** | **1 día** | **3** | 142 | **+4,47 %** | +2,68 % | +9,38 % | **5 %** |
| **> 1 %** | **1 día** | **4** | 139 | **+5,21 %** | +2,50 % | +10,00 % | 10 % |
| > 1 % | 2 días | 1 | 142 | +1,86 % | +1,16 % | +4,48 % | 0 % |
| > 1 % | 2 días | 2 | 137 | +2,56 % | +1,47 % | +6,25 % | 4 % |
| > 1 % | 2 días | 3 | 134 | +3,09 % | +1,49 % | +8,54 % | 10 % |
| > 1 % | 3-7 días | 1 | 170 | +1,45 % | +0,57 % | +4,81 % | 4 % |
| > 1 % | 3-7 días | 2 | 115 | +1,83 % | +0,00 % | +5,88 % | 14 % |

### Las celdas vacías, y por qué

| Celdas | Motivo |
|---|---|
| **todas las de m = 5, 7 y 10** | Con 6 días de histórico no cabe una ventana de cinco. Cero operaciones, no una muestra pequeña |
| **todas las de racha > 7 días** | La racha máxima observable en 6 días es 5 |
| m = 3 y 4 con racha 2 días, m = 3 y 4 con racha 3-7 | La racha consume días por delante y no queda ventana por detrás |
| todo el tramo 0-0,25 % | Existe pero con 6 a 26 operaciones: por debajo de las 30 no se publica mediana |

**No he rellenado ninguna.** El corte de muestra es 30 y está escrito en el
módulo.

## Cruce con lo que ya estaba medido: encaja, y en un punto lo afina

| Lo medido antes | Lo que dice el retrotest |
|---|---|
| momentum r = +0,90 | ✅ el que sube sigue subiendo: 1-5 % de pérdidas en el tramo alto |
| quien cae vuelve a caer el 90,7 % | ✅ **88 %** a un día, **95 %** a tres |
| la continuación hace pico el día 2 y cae el 3.º | ✅ **y por eso la racha larga rinde menos**: con la misma tasa >1 %, racha de 1 día da +4,47 % a m=3 y racha de 3-7 da +1,83 % a m=2 |
| 83,8 % no se dan la vuelta en 6 días | ✅ consistente con las tasas de pérdida por horizonte |

**El punto que afina:** la mediana del rendimiento *sigue creciendo* con el
horizonte (+0,81 / +1,31 / +2,01 / +2,34 %) mientras la probabilidad de
continuación cae. No es contradicción: lo ganado los primeros días ya está
en el bolsillo aunque el cuarto se dé la vuelta. Lo que sí sube con el
horizonte es el **riesgo**: de 5,4 % a 17,4 % de operaciones en pérdida.

---

# BLOQUE 2 — La vía TENER, encendida

`src/analysis/hold_value.py`, cuarta vía junto a las tres de siempre.

```
ganancia   = precio × tasa_diaria × horizonte
hold_value = precio + ganancia × confianza × (1 − margen)
```

- **Horizonte: 3 días.** No es el que da el número más bonito: m=4 tiene
  mejor mediana (+2,34 % contra +2,01 %) pero la muestra baja de 474 a 242
  y la pérdida sube del 15,2 % al 17,4 %. Con más días de almacén se vuelve
  a medir.
- **La confianza sale de `route_confidence` y descuenta la ganancia, no el
  capital.** Esa lección costó una noche entera el 09/09.
- **Corte mínimo: 0,25 %/día.** El tramo de abajo no tiene ni muestra, y el
  de al lado rinde +0,41 % con un 22 % de pérdidas.
- **Bolsillo:** operación de cartera → especular, y el listón de especular.
  La regla del 13/09 —bolsillo, listón y valor de la misma vía— sin
  excepción.

**¿Con qué muestra la encendí?** Corte de 30 operaciones por celda; la
celda que la sostiene tiene **142** con un 5 % de pérdidas. Está en la
guardia: si esa celda deja de rendir más del 3 %, `test_tener_paga_en_el_tramo_de_arriba`
se pone roja y la vía deja de estar respaldada.

**La fórmula es conservadora y sé cuánto.** Extrapolar linealmente la tasa
de Amatucci da 3,33 % a tres días; la mediana *realizada* de su tramo es
+4,47 %. La fórmula se queda corta en un tercio. La dejo así: preferimos
equivocarnos por debajo.

## Y un arreglo que salió al conectarla

`classify_operation` clasificaba como fichaje a cualquiera con valor por
una vía de fichaje, **aunque ese valor fuera menor que el precio**.
Amatucci: vale 2.716.842 como fichaje, cuesta 3.670.000, salía `SIGNING`,
se decidía con 2.716.842 y se rechazaba — sin llegar a mirar si por otra
vía sí compensaba.

Decir "entra a la plantilla para jugar" de alguien por el que **no**
pagaríamos su precio para que juegue es falso. Ahora la clase la decide la
vía que **justifica la compra**. Comprobado que el agujero de ayer sigue
cerrado: el jugador de 9 M que suma 6 puntos sigue saliendo `TRADE` por
reventa, con el listón de reventa, y sigue rechazado.

---

# BLOQUE 3 — El 3 % era correcto. Se queda.

**No lo he bajado, y ahora hay un número detrás.**

Exigir un 3 % de rendimiento selecciona exactamente el tramo `> 1 %/día`:

| Tramo | mediana a 3 días | en pérdida | ¿pasa el 3 %? |
|---|---:|---:|---|
| > 1 %/día | **+4,47 %** | **5 %** | sí |
| 0,5-1 % | +1,25 % | 12 % | no |
| 0,25-0,5 % | +0,41 % | 22 % | no |
| 0-0,25 % | *sin muestra* | | no |
| cae | −4,76 % | 95 % | no |

Bajarlo al 1,5 % dejaría entrar el tramo 0,5-1 %: **+1,25 % de mediana con
un 12 % de operaciones en pérdida**, consumiendo el único turno del ciclo.
El 3 % está donde tiene que estar.

`MIN_SPECULATION_EXPECTED_VALUE = 25.000` también se queda. Con la mediana
del tramo bueno (+4,47 %) exige un precio de unos 560.000 €, que es un
umbral coherente con "no merece el turno".

**Soler:** no toqué ningún umbral, así que
`test_la_especulacion_de_soler_ya_no_se_puja` no llegó a ponerse en rojo.

---

# BLOQUE 4 — Dejar de tener lo que baja

## El ritmo neto de la plantilla

```
+30.000 EUR/día   sobre 49.540.000   =   +0,0606 %/día
```

Y la línea de debajo es la que importa: **7 suben (+190.000/día) y 6 caen
(−160.000/día)**. El neto positivo esconde seis que sangran.

Está en pantalla, en PLANTILLA, arriba de la cola de ventas, con el
desglose en el tooltip.

## El tramo nuevo

`"Cae y no juega"`, por encima de todos los demás. La cola de hoy:

| # | Jugador | Tramo | Precio | Ritmo | Caja |
|---|---|---|---:|---:|---|
| **1** | **Jutglà** | **Cae y no juega** | 3.350.000 | **−50.000/día** | oferta viva |
| 2 | Lucas Cepeda | No juega | 480.000 | 0 | oferta viva |
| 3 | Kiko Femenía | Caro por punto | 1.180.000 | +30.000/día | a mercado |
| 4 | Manu Sánchez | Caro por punto | 1.480.000 | −10.000/día | oferta viva |
| 5 | Mangala | Caro por punto | 2.630.000 | −30.000/día | a mercado |

Jutglà sube del puesto 3 al **1**. Es el único de la plantilla que cae *y*
está fuera del once; los otros cinco que caen son titulares y siguen
puntuando.

**Una decisión que quiero dejar escrita.** Jutglà tiene el pronóstico
clavado en el **40,0 %**, que es exactamente el corte de suplente: con
`_plays()` sale que juega, porque 40,0 no es menor que 40,0. Mover
`BENCH_PERCENT` para que entrase habría sido ajustar la regla al caso. El
tramo mira el hecho observable —no está en el once— y `BENCH_PERCENT` se
queda donde estaba. Hay guardia con ese caso exacto.

**No se vende nada automáticamente**, como pedía el encargo. La cola
ordena y se muestra.

---

# Qué compraría el primer ciclo: nadie. Y el motivo es nuevo.

Con la vía TENER encendida, tres objetivos **sí compensan** por primera
vez:

| Jugador | Precio | %/día | Racha | Valor TENER | Margen | Rinde |
|---|---:|---:|---:|---:|---:|---:|
| Roro Riquelme | 4.240.000 | 1,666 | 50 d | 4.363.652 | +123.652 | 2,92 % |
| Amatucci | 3.670.000 | 1,098 | 19 d | 3.740.538 | +70.538 | 1,92 % |
| Pedri | 15.350.000 | 0,305 | 8 d | 15.431.953 | +81.953 | 0,53 % |
| **Gorosabel** | **420.000** | **4,849** | **4 d** | **455.650** | **+35.650** | **8,49 %** |

**Y ninguno se compra, por dos motivos distintos:**

**Los tres primeros: el tope por operación.** Una compra por la vía TENER
es una operación de cartera, así que sale del bolsillo de especular
(2.433.987 €) con un **tope por operación de 973.594 €**. Cuestan entre
3,67 M y 15,35 M: entre **cuatro y quince veces** lo que ese bolsillo puede
poner en una sola operación. Roro Riquelme además se queda a 8 centésimas
del 3 %.

**Gorosabel: está tocado.** Es el único que pasa todo —cabe bajo el tope,
rinde un 8,49 %, genera EV suficiente— y `availability: TOCADO` lo veta.
Un veto de disponibilidad es una barandilla, y no se toca.

## El hallazgo estructural, y aquí paro

**La vía de la rampa apunta a un mercado cuyos precios están entre 1 M y
15 M, y solo puede gastar 973.594 € por operación.**

Calculado: para que una compra por esta vía sea posible hacen falta a la
vez **≥1,5 %/día con racha corta** (o ≥2 %/día con racha larga) para pasar
el 3 %, **y** un precio bajo el tope de 973.594 € que aun así genere
25.000 € de valor esperado. La ventana existe —Gorosabel entra en ella—
pero es estrecha, y deja fuera por construcción a los Gerard Moreno
(6,45 M) y Pubill (6,36 M) que compró Pollo.

`MAX_SINGLE_SPECULATION_PERCENT` está en la lista de intocables y **el
encargo dice que si para encender algo hay que tocar una barandilla, se
para y se escribe**. Así que paro y lo escribo:

> Mientras la vía TENER cobre del bolsillo de especular con un tope del
> 40 %, no puede comprar nada por encima de un millón. Los 5.350.683 € del
> bolsillo de fichar siguen reservados a mejoras del once. Eso, y no el
> listón del 3 %, es lo que mantiene el dinero parado.

Hay tres salidas y las tres son decisión tuya, no mía:

1. **Subir `MAX_SINGLE_SPECULATION_PERCENT`.** Es un tope pagado, y la
   lección de Soler iba justo de eso.
2. **Dar a la vía TENER su propio bolsillo**, con su propio tope, separado
   de las apuestas a corto.
3. **Dejarlo como está** y aceptar que la rampa solo se monta con jugadores
   baratos.

---

# Lo que no hice, y por qué

**No bajé el 3 %.** El retrotest dice que estaba bien. Un umbral confirmado
por medición vale más que uno heredado, y éste queda confirmado.

**No toqué ningún tope.** `MAX_SINGLE_SPECULATION_PERCENT`,
`MIN_SPECULATION_EXPECTED_VALUE`, `MAX_SAFE_DEBT` y los demás siguen donde
estaban. Cuando el tope se convirtió en el obstáculo, paré y lo escribí,
que es lo que manda el encargo.

**No moví `BENCH_PERCENT`** para que Jutglà entrase en el tramo nuevo.

**No vendí nada.** La cola ordena y se muestra.

**No medí más allá de 4 días de horizonte** porque el almacén tiene 6 días.
Las celdas están vacías y marcadas. El día que haya tres semanas de
histórico, `hold_backtest` vuelve a correr sin tocar una línea y
`DEFAULT_HORIZON_DAYS` se revisa.

**Una advertencia sobre la ventana:** el retrotest es de agosto. Que el
mercado de septiembre se comporte igual es una suposición razonable —el
momentum r=+0,90 se midió en septiembre y coincide— pero es una
suposición. La guardia la vigila: si el tramo bueno deja de rendir, la vía
se queda sin respaldo y salta.

---

**La frase para mañana:** tener paga —+4,47 % en tres días comprando a más
del 1 % diario, fallando el 5 % de las veces— y ahora Pepe sabe valorarlo.
Lo que le impide usarlo no es el listón del 3 %, que estaba bien puesto:
es que la vía de cartera cobra de un bolsillo que solo deja poner 973.594 €
por operación, y la rampa que queremos montar cuesta entre tres y quince
millones.
