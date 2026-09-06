# EL BOLSILLO — resultado

Rama `bolsillo/de-donde-sale-el-dinero`. **Verja: 82 de 82 en verde**
(80 al empezar). `main` intacto. `.github/workflows/bordalas-live.yml`
sin tocar. `MAX_SINGLE_SPECULATION_PERCENT` sin tocar. `npm run build`
pasa. **Sin push.**

Medido contra `diagnostico/status.json` del 06/09/2026 09:33.

---

## Lo que entra en el commit

Miré `git status` antes. **Once ficheros, todos míos**, más este informe:

```
 M dashboard-v8/src/pages/MarketPage.jsx          rango de validez en pantalla
 M scripts/run_validation_gate.py                 dos guardias nuevas
 M src/analysis/acquisition_board.py              bolsillo y tope de la vía TENER
 M src/analysis/hold_backtest.py                  p5, peor, media de perdedoras + calibración
 M src/analysis/hold_value.py                     recorte por muestra
 M src/analysis/price_history_store.py            retención 45 → 60 días
 M src/analysis/test_no_contar_dos_veces_v1.py    ajustada al recorte (leída antes)
 M src/analysis/test_pantalla_lee_lo_publicado_v1.py  + 1 prueba
?? src/analysis/hold_budget.py                    el bolsillo y el tope deducido
?? src/analysis/test_fuera_de_muestra_v1.py       8 pruebas
?? src/analysis/test_tope_deducido_v1.py          16 pruebas
```

**Un aviso:** el fichero del encargo ya está commiteado aparte, en
`1459222`, con este mismo mensaje. No lo hice yo —no ejecuté ningún
`commit` hasta el final— pero está ahí y conviene que lo sepas.

---

# BLOQUE 1 — Tenías razón, y es peor de lo que decía el encargo

## No es 5. Es 2.

El informe de ayer decía "la racha máxima observable en 6 días es 5".
Medido con precisión: **5 es la racha máxima a UN día de horizonte**.

Una racha de `n` días consume `n` días por delante y deja `5 − n` por
detrás. **Al horizonte de tres días —el que usa la vía— la racha máxima
medible es DOS.**

| Tramo de tasa | Calibrado hasta racha de | Mediana medida | n |
|---|---:|---:|---:|
| > 1 %/día | **2 días** | +3,09 % | 134 |
| 0,5-1 % | 2 días | +0,60 % | 55 |
| 0,25-0,5 % | 1 día | +0,41 % | 32 |
| 0-0,25 % | *sin calibrar* | — | — |
| cae | 2 días | −3,96 % | 114 |

Y los tres candidatos llevan **50, 19 y 8 días**.

## Qué hice: recortar, no apagar

Elegí **recortar**, no declarar `SIN_RESPALDO`. El motivo:
`streak_confidence` sí tiene una banda de "3 días o más" medida sobre
351 casos el 07/09, así que ciegos no estamos del todo. Lo que no
tenemos es la **magnitud** del rendimiento para rachas largas.

Así que la ganancia se recorta al rendimiento de la racha más larga que
sí se midió **en su mismo tramo de tasa**. No apagamos la vía; no le
dejamos valer más de lo que valió lo más parecido que hemos visto.

## Y el resultado tumba el resto del encargo

| Jugador | Racha | Rendía ayer | Recortado | ¿pasa el 3 %? |
|---|---:|---:|---:|---|
| Roro Riquelme | 50 d | 2,92 % | **1,80 %** | no |
| Amatucci | 19 d | 1,92 % | **1,80 %** | no |
| Pedri | 8 d | 0,53 % | **0,24 %** | no |
| **Gorosabel** | 4 d | 8,49 % | **1,80 %** | no *(y tocado)* |

**Los cuatro caen, Gorosabel incluido.** Su racha de 4 días también
excede el rango calibrado de 2, y su 4,849 %/día se recorta al 3,09 %
medido.

Cualquiera fuera de muestra aterriza exactamente en **1,80 %**
(3,09 % × 0,778 de confianza × 0,75 de margen), por debajo del 3 % **por
construcción**. Dentro de muestra la vía sigue viva: un jugador a
2 %/día con racha de 1 día rinde 4,32 % y pasa.

**El tipo que el retrotest bendice —tasa alta, racha corta— hoy no
existe en el tablero.** Los que suben, suben desde hace semanas.

En pantalla, en MERCADO, cada valor fuera de muestra lleva su etiqueta:
`FUERA DE MUESTRA · racha 50 d, calibrado hasta 2`.

---

# BLOQUE 2 — Cuánto se pierde cuando se pierde

La celda que enciende la vía:

```
> 1 %/día · racha 1 día · m=3 · n=142

  mediana   +4,47 %      p5     +0,38 %
  p25       +2,68 %      peor  −12,86 %
  pérdidas    4,93 %     media de las perdedoras  −4,84 %
```

**El 95 % de las operaciones hace más de +0,38 %. La peor de 142 perdió
un 12,86 %.** Ése es el número con el que se dimensiona un tope.

Tabla completa (celdas con muestra suficiente):

| tasa | racha | m | n | mediana | p5 | peor | media de perdedoras |
|---|---|---:|---:|---:|---:|---:|---:|
| cae | 1 día | 1 | 214 | −1,62 % | −5,92 % | −7,69 % | −2,25 % |
| cae | 1 día | 2 | 149 | −2,99 % | −9,87 % | −11,86 % | −3,87 % |
| cae | 1 día | 3 | 137 | −4,76 % | −13,30 % | −15,82 % | −5,46 % |
| cae | 1 día | 4 | 120 | −5,32 % | −15,62 % | −19,41 % | −6,60 % |
| cae | 2 días | 1 | 138 | −1,29 % | −4,21 % | −6,15 % | −1,78 % |
| cae | 2 días | 2 | 126 | −3,03 % | −8,16 % | −9,79 % | −3,55 % |
| cae | 2 días | 3 | 114 | −3,96 % | −10,53 % | −14,34 % | −4,70 % |
| cae | 3-7 días | 1 | 216 | −1,50 % | −4,26 % | −6,59 % | −1,77 % |
| cae | 3-7 días | 2 | 104 | −2,85 % | −8,00 % | −9,93 % | −3,32 % |
| 0,25-0,5 % | 1 día | 1 | 35 | +0,28 % | −0,33 % | −1,00 % | −0,51 % |
| 0,25-0,5 % | 1 día | 2 | 32 | +0,54 % | −2,33 % | −4,01 % | −1,50 % |
| 0,25-0,5 % | 1 día | 3 | 32 | +0,41 % | −6,33 % | −8,70 % | −2,93 % |
| 0,25-0,5 % | 1 día | 4 | 31 | +0,27 % | −11,33 % | −11,37 % | −3,46 % |
| 0,25-0,5 % | 3-7 días | 1 | 64 | +0,24 % | −0,50 % | −1,77 % | −0,45 % |
| 0,25-0,5 % | 3-7 días | 2 | 31 | +0,00 % | −2,26 % | −8,51 % | −1,70 % |
| 0,5-1 % | 1 día | 1 | 68 | +0,60 % | +0,18 % | +0,00 % | *ninguna* |
| 0,5-1 % | 1 día | 2 | 68 | +1,16 % | +0,00 % | −0,84 % | −0,56 % |
| 0,5-1 % | 1 día | 3 | 66 | +1,25 % | −1,32 % | −3,36 % | −1,43 % |
| 0,5-1 % | 1 día | 4 | 66 | +1,44 % | −2,65 % | −6,48 % | −2,00 % |
| 0,5-1 % | 2 días | 1 | 56 | +0,53 % | +0,19 % | +0,00 % | *ninguna* |
| 0,5-1 % | 2 días | 2 | 56 | +0,62 % | −0,38 % | −0,85 % | −0,51 % |
| 0,5-1 % | 2 días | 3 | 55 | +0,60 % | −2,31 % | −7,51 % | −1,37 % |
| 0,5-1 % | 3-7 días | 1 | 91 | +0,44 % | −1,19 % | −2,94 % | −1,31 % |
| 0,5-1 % | 3-7 días | 2 | 56 | +0,70 % | −8,06 % | −9,36 % | −3,16 % |
| **> 1 %** | **1 día** | **1** | 153 | +2,30 % | +0,48 % | −1,43 % | −1,43 % |
| **> 1 %** | **1 día** | **2** | 148 | +3,80 % | +0,96 % | −7,14 % | −2,93 % |
| **> 1 %** | **1 día** | **3** | 142 | **+4,47 %** | **+0,38 %** | **−12,86 %** | **−4,84 %** |
| > 1 % | 1 día | 4 | 139 | +5,21 % | −5,56 % | −15,71 % | −5,41 % |
| > 1 % | 2 días | 1 | 142 | +1,86 % | +0,59 % | +0,00 % | *ninguna* |
| > 1 % | 2 días | 2 | 137 | +2,56 % | +0,00 % | −1,76 % | −1,28 % |
| > 1 % | 2 días | 3 | 134 | +3,09 % | −3,50 % | −8,58 % | −3,73 % |
| > 1 % | 3-7 días | 1 | 170 | +1,45 % | +0,00 % | −2,26 % | −1,13 % |
| > 1 % | 3-7 días | 2 | 115 | +1,83 % | −2,43 % | −9,77 % | −2,72 % |

Y un detalle que se lee solo: **la cola se alarga con el horizonte**. En
el tramo bueno, la peor pasa de −1,43 % a un día a −15,71 % a cuatro.

---

# BLOQUE 3 — El bolsillo, y por qué SÍ pero con condición

**Lo implementé, y no creo que rompa la regla del 13/09 — pero encontré
un riesgo que la regla no cubre y lo he tapado.**

La regla dice que valor, listón y bolsillo tienen que ser coherentes
entre sí. Aquí lo son: el valor lo da TENER, el listón es el 3 % de
TENER, y el bolsillo lo da el hecho contable de que la ficha estaba
vacía. Nadie se justifica con un número prestado.

**Pero hay algo que la regla no dice.** El bolsillo de especular es más
pequeño *a propósito*: el 40 % por operación es donde vive la lección de
Soler. Mandar una apuesta de precio al bolsillo grande diluiría ese
límite aunque no rompa la regla de las vías.

Así que:

- **el bolsillo pone los fondos** — fichar si llena ficha vacía,
  especular si rota;
- **el tope pone el riesgo**, y es propio, deducido, y **arranca
  exactamente donde está hoy el límite por operación**.

**El primer día no se afloja absolutamente nada.**

---

# BLOQUE 4 — El tope, con la cuenta al lado

```
CONDICIÓN 1 — que la peor pérdida medida la aguante la caja
  saldo 1.725.383 / 0,1286  =  13.416.664 €

CONDICIÓN 2 — no más del 10 % del patrimonio en una posición que no juega
  0,10 × 49.540.000 / (1 − 0,10)  =  5.504.444 €

TECHO = el menor de los dos              =  5.504.444 €
PELDAÑO 0, hoy                           =    973.594 €
```

## De dónde sale el 10 %

Medido sobre la liga el 15/09 — la mayor posición **no titular** de cada
mánager:

| Mánager | Puesto | Mayor no-titular | % de su plantilla |
|---|---:|---|---:|
| Pollo17 | 1.º | Gerard Moreno | **9,48 %** |
| Mex | 2.º | Peio Canales | 4,29 % |
| Luismi_Haz | 3.º | Areso | **1,70 %** |
| Pepe | 4.º | Expósito | 10,42 % |
| Prinzipote | 5.º | Agirrezabala | 5,79 % |
| Manzagool | 7.º | Ez Abde | **15,53 %** |

Mismo patrón que el tope de concentración del 10/09: **los tres que van
por delante están entre el 1,70 % y el 9,48 %, y el más concentrado va
último.** El límite se pone justo encima de la banda de los que ganan.

## La escalera

```
peldaños:  973.594  →  1.947.188  →  3.894.376  →  5.504.444
```

**N = 12.** No es redondo: es `PREMIUM_SHRINK_SAMPLES`, el corte que la
casa ya usa para decidir cuándo una medida pesa más que su prior — *"con
las 12 ventas mínimas que exige el propio medidor, el ratio y el prior
pesarían lo mismo"*. Reutilizar una constante ya justificada vale más
que inventar una.

**El margen: +2,68 %**, el **p25 del retrotest**. Es decir: si la mitad
de lo que nos pasa en vivo bate lo que batía un cuarto de lo medido, el
retrotest aguanta. Tampoco es redondo, y sale de la tabla.

- Sube un peldaño por cada 12 operaciones cerradas cuya mediana llegue
  al p25.
- **Baja al peldaño 0** si la mediana viva se pone en negativo.
- Y **una sola posición TENER abierta a la vez** hasta que haya
  operaciones cerradas: con cero, el tope de la segunda es 0 €.

Todo recalculado cada ciclo, no escrito a mano. Guardia:
`test_tope_deducido_v1`, 16 pruebas, incluida una que salta si
`MAX_SINGLE_SPECULATION_PERCENT` deja de ser 0,40.

---

# BLOQUE 5 — El almacén: la premisa era falsa

**La retención nunca fue de 6 días. Estaba en 45.**

Los 6 días son de **mi copia local**, que dejó de escribirse el 17/08.
En producción el almacén vive en la caché de GitHub Actions
(`data/autopilot`, con `restore-keys` encadenadas), que leí y está bien
configurada.

Pero **en producción tampoco llega**, y hay una señal medible: el modelo
de primas descarta **72 pujas "sin precio de aquel momento"** (48
calibradas de 120). Si el almacén tuviera 45 días de verdad, esas 72 no
se descartarían.

No puedo determinar desde aquí si es que el almacén empezó hace poco o
si la caché se pierde entre ejecuciones. **Lo dejo apuntado, no
adivinado.**

## Lo que sí hice

Subir la retención **de 45 a 60 días**, porque cuesta nada:

```
22,3 bytes por punto · 573 jugadores · 1 punto/día

   6 días     75 KB
  45 días    562 KB   (0,55 MB)
  60 días    749 KB   (0,73 MB)
```

**190 KB más.** Menos que la mitad de un snapshot.

Subir la constante **no crea histórico retroactivamente**: hay que dejar
correr los días. `hold_backtest` está preparado para volver a correr sin
tocar una línea, y `DEFAULT_HORIZON_DAYS` se revisa cuando haya
ventana.

---

# Qué compraría el primer ciclo: nadie, y por fin por el motivo bueno

| Jugador | Precio | Vía | Rinde | Veredicto |
|---|---:|---|---:|---|
| Pedri | 15.350.000 | HOLD | 0,24 % | rinde menos del 3 % |
| Roro Riquelme | 4.240.000 | HOLD | 1,80 % | rinde menos del 3 % |
| Amatucci | 3.670.000 | HOLD | 1,80 % | rinde menos del 3 % |
| Gorosabel | 420.000 | HOLD | 1,80 % | tocado |
| Pathé Ciss, Tárrega, Suazo, Morcillo | | ROSTER_FILL | negativo | no compensan |
| los otros 12 | | — | — | ninguna vía les da valor |

**Saldo resultante: 1.725.383 €, el mismo.** Ninguna compra.

**Y esto es lo que ha cambiado de verdad.** Ayer el motivo del rechazo
era *"supera el bolsillo de 973.594"* — un problema de fontanería. Hoy
es *"rinde un 1,80 % y se exige un 3 %"* — un problema de precio. **El
bolsillo ha dejado de ser la excusa.**

---

# Lo que no hice, y por qué

**No toqué `MAX_SINGLE_SPECULATION_PERCENT`.** Este encargo estaba
escrito para no tener que hacerlo, y no hizo falta: el tope de la vía
TENER es propio y arranca en el mismo número.

**No subí el peldaño 0.** Con cero operaciones TENER cerradas, la única
evidencia viva que tenemos es ninguna.

**No apagué la vía TENER.** Sigue encendida y sigue pudiendo disparar
—un jugador a 2 %/día con racha corta rinde 4,32 % y pasa—. Lo que no
puede es valorar lo que nunca hemos medido.

**No arreglé el almacén de producción.** No sé si el problema es la
caché o que empezó hace poco, y adivinarlo desde aquí sería exactamente
lo que este proyecto no hace. La retención está en 60 días; si en una
semana el retrotest sigue viendo 6, el problema es la caché y hay que
mirar el workflow — que es tuyo.

**No metí las operaciones TENER en el libro de pujas.** La escalera las
necesita, pero como no hay ninguna que registrar, escribir el
registrador hoy sería código sin caso de uso. El módulo recibe
`closed_operations` y `live_median` como parámetros: engancharlo es una
línea el día que haya la primera.

---

**La frase para mañana:** el tope no era el problema, y ahora se sabe
porque se ha quitado de en medio. Los tres jugadores que bloqueaba
llevan rachas de 50, 19 y 8 días, y al horizonte de tres días este
sistema nunca ha medido una racha de más de **dos**. Recortados a lo
medido, los tres rinden un 1,80 % y no llegan al 3 %. La vía TENER
funciona; lo que falta es un jugador del tipo que el retrotest bendice
—subiendo fuerte y desde hace poco— y hoy en el tablero no hay ninguno.
