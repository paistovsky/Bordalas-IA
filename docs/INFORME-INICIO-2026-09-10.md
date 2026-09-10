# INICIO — reordenar lo que ya existe

**10/09/2026** · verja 106/106 · sin push

---

## Lo que se pidió y lo que hay

Ningún cálculo nuevo, ningún umbral, ninguna ruta de decisión. **Nada borrado.**
Se cumple: el único código que calcula algo es `banquillo_con_motivo`, y no
calcula — **lee** los valores que el motor de alineación ya había dejado puestos.

---

## 1. La tira de estado

Ocho cosas, en el orden pedido:

| | |
|---|---|
| Jornada | |
| Foto | «hace X min» |
| **Próximo ciclo** | **cuenta atrás en vivo** |
| **Deuda máxima** | con desglose debajo |
| **Reset** | **cuenta atrás en vivo** |
| Cierre de la jornada | |
| XI | |
| Pujas puestas | |

### «Deuda máxima» sustituye a «Puede gastar»

```
deuda máxima = saldo + línea de crédito − pujas ya comprometidas
```

Y **el crédito se deduce de los otros tres**, no se lee de otro sitio:

```js
const credito = deudaMaxima + comprometido - saldo;
```

Así los cuatro números **siempre cuadran entre sí**. Si el crédito se leyera
aparte, un día no sumarían y el desglose dejaría de explicar nada — que es
exactamente el problema que el desglose viene a resolver.

La deuda máxima sale del **`maximumBid` oficial de Biwenger**, no de ninguno de
nuestros dos presupuestos internos. Eso cierra por arriba el incidente del 21/08
(«PUEDE GASTAR 0 €» justo después de gastar 2,08 M), y la guardia
`test_la_pantalla_no_desmiente_al_bot` se invirtió para la tira: ahora exige
`maximum_bid` y **prohíbe** `available_budget`, `total_budget` y `speculation`.

### Las dos cuentas atrás

`dashboard-v8/src/lib/relojes.js`. El próximo ciclo sale **del cron real**, no de
una estimación:

```
interno (GitHub Actions, UTC)   "7 0-2,7-23 * * *"
externo (cron-job.org, Madrid)  04:45 · 04:50 · 07:15
```

La hora de Madrid con `Intl` y la base de zonas del navegador. Ni UTC ni la hora
del equipo: **es el error que ya costó dos semanas de ventana perdida.**

**Y si el ciclo no llega, lo dice.** Cuando el último disparo que tocaba es más
nuevo que la foto y ha pasado el margen de 12 minutos, la tira cambia:

```
Ciclo NO llegado · hace 1h 42m · debería haber entrado ya
```

en rojo, en vez de quedarse en cero fingiendo normalidad.

**Un defecto arreglado por el camino:** `meta.generated_at` viene en hora de
Madrid **sin zona** (`2026-09-10T09:04:33`). Leerlo como UTC lo adelanta dos
horas y habría dicho «el ciclo llegó» cuando no ha llegado — el mismo fallo, otra
vez. `madridNaiveAUTC()` le pone la zona que le toca antes de comparar.

---

## 2. Los cuatro paneles

| | |
|---|---|
| **El XI para la jornada** | intacto, no se ha tocado |
| **Clasificación e inteligencia** | intacto, con un cambio |
| **Cronología de Bordalás** | era «Lo que va a hacer Pepe» |
| **Posibles cambios** | nuevo |

### El cambio en Clasificación

```js
const THREAT = {
  VERY_HIGH: "pill crit",   // faltaba
  HIGH: "pill crit",
  ...
```

`VERY_HIGH` no estaba en la tabla y caía al gris del `||`: **la amenaza más alta
del tablero se pintaba igual que «ninguna».**

---

## 3. «Posibles cambios» — de dónde sale el motivo

El motor ya compara a todos y descarta en **tres cortes**, en este orden:

1. `lineup_eligible` — no puede jugar
2. `automatic_lineup` — está en duda
3. `lineup_score` — puntúa menos que el que está

De todo ese trabajo **solo publicaba los once y tiraba el porqué**.
`banquillo_con_motivo()` le saca ese motivo y dice en cuál de los tres cortes se
quedó cada uno:

| motivo | en castellano |
|---|---|
| `NO_DISPONIBLE` | «lesionado», «sancionado»… |
| `NO_JUEGA_SU_EQUIPO` | «su club no lo alinea esta jornada» |
| `EN_DUDA` | «hay dudas de que vaya a jugar» |
| `POSICION_CUBIERTA` | «su posición ya está cubierta» |
| `PUNTUA_MENOS` | «puntúa menos que Jonny Castro» |

### Cuánto costaría o ganaría el once

La distancia contra **el peor titular de su misma posición**, que es a quien
tendría que ganar para entrar — y es exactamente la comparación que hizo el motor
al ordenar. No contra el mejor ni contra el once entero: esos números no
explicarían ninguna decisión.

**Sale en verde cuando es positiva**, y eso solo puede pasar cuando el motivo
*no* es puntuar menos: es decir, **cuando lo que le falta no es nivel, es poder
jugar**. Un suplente mejor que el titular al que no dejan jugar es justo el caso
que hay que ver de un vistazo.

Si no hay contra quién comparar, **se dice que no hay** (regla 23). Un cero
puesto donde falta el dato se lee como «está igual de bien», que es lo contrario
de la verdad.

### Bloque propio

Se publica como `posibles_cambios`, no colgado de `lineup`, para que el panel
pueda distinguir **«no hay suplentes»** de **«no se sabe»** sin arrastrar al XI.
`compact_lineup` se calcula ahora **una sola vez** en una variable: los dos
bloques tienen que contar lo mismo.

---

## 4. Lo que se movió — nada se borró

A **Auditoría**, enteros y leyendo los mismos datos:

`AhoraPanel` · `DineroPanel` · `VentanaPanel` · `CobrarPanel` · `ElOncePanel` ·
`Objetivos`

La guardia `test_inicio_tiene_los_cuatro_paneles_y_solo_esos` comprueba las dos
mitades: que **no están** en Inicio y que **sí llegaron** a Auditoría. Salir de
Inicio y no llegar a ninguna parte sería haberlos borrado, y el encargo decía que
no.

La tabla `CADENAS` de `test_pantalla_lee_lo_publicado_v1` se actualizó para los
cinco bloques que cambiaron de página, más el panel nuevo.

---

## Guardias nuevas

`src/analysis/test_posibles_cambios_v1.py` — **11/11**

- `test_cada_suplente_dice_por_que_esta_fuera`
- `test_el_motivo_va_en_castellano_llano`
- `test_se_compara_contra_el_peor_titular_de_su_posicion`
- `test_el_que_mejoraria_el_once_se_ve_en_positivo`
- `test_el_que_esta_mas_cerca_de_entrar_sale_primero`
- `test_ningun_titular_aparece_como_suplente`
- `test_sin_once_no_se_inventa_una_comparacion`
- `test_inicio_tiene_los_cuatro_paneles_y_solo_esos`
- `test_la_amenaza_mas_alta_sale_en_rojo`
- `test_las_dos_cuentas_atras_corren_en_el_navegador`
- `test_la_deuda_maxima_ensena_su_desglose`

Doctrina **regla 34 — «Inicio contesta, no informa»**. Con la 28 (*un panel nace
en Auditoría*) cierra el círculo: a Inicio solo sube lo que hace falta para
decidir, y a Auditoría baja lo que sirve para verificar.

---

## Estado

- Verja encadenada: **106/106**
- `vite build` hecho, `dist` copiado a `dashboard/`
- Rama `main`, **sin push**

## Lo único pendiente de ver

El bloque `posibles_cambios` estará vacío hasta el próximo ciclo real: la foto
publicada es anterior a este cambio. **Mientras tanto el panel dice que no se
sabe, que es lo correcto** — no finge un banquillo vacío.

Por la misma razón, la foto de hoy trae `maximum_bid = 12.053.468`: es anterior
al arreglo de la línea de crédito. El número que el dueño espera ver —
**3.608.383** — saldrá en la primera foto nueva.
