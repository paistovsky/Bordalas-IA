# El propósito — informe

**Foto:** `diagnostico/status.json`, **`meta.generated_at` = 2026-09-17T07:30:55**.
Abierta con `encoding="utf-8"`.

**Rama:** `motor/el-proposito` (desde `medir/el-escaparate`)
**Verja:** 150/150 en verde, exit 0, salida a fichero
**Push:** NO. **Solo se enciende el libro del bloque 0.** `el_proposito.ENCENDIDO = False`.

---

## La respuesta corta al bloque 2: **tu planteamiento está mal, y te lo doy la vuelta**

> **El `intent` NO se elige por qué vía da más euros.** Eso describe el camino que
> corre con `DEPLOYMENT_ENABLED = 0`, y lleva en **1** desde el 13/09.
>
> **La separación que propones ya existe, y funciona.** La hace
> `deployment.classify_operation`: elige por **clase de operación**, no por euros. Ha
> fichado dos veces en once días y ganó las dos.
>
> Lo que pasa hoy es otra cosa, y es la que importa: **de los 66 candidatos, ninguno
> vale como fichaje lo que cuesta.** No se les aplica el listón equivocado. La vía del
> once dice, correctamente, que no pagaríamos ese precio por esos puntos.

---

## BLOQUE 0 — El libro del escaparate. **Encendido.**

```
escribe en          data/trading/libro_del_escaparate.jsonl
jugadores por línea 20
día de mercado      corta en el reset (05:00 UTC), no a medianoche
peticiones a la red 0
```

**Dónde se llama:** `dashboard_state.build_state`, justo al lado de
`censar_el_reset`, con los 20 que el tablero de objetivos ya trae marcados
`seller_kind == "COMPUTER"`. Cero peticiones nuevas.

**Qué guarda de cada uno:** `id`, `name`, `position`, `price`, `points`, `played`,
`starter_probability` y `hierarchy`. **Los partidos y el pronóstico son la mitad que
faltaba**: sin ellos, la tabla de oportunidades perdidas del 17/09 se quedó en n=1 día.

Un jugador sin pronóstico viaja con **`None`**, no con cero. Un cero se leería como
«seguro que no juega», y hay guardia sobre eso.

**Está en `los_libros.LIBROS`**, así que `guardar_los_libros.py` lo sube. Comprobado
de verdad, y por el camino salieron **dos fallos que cazaron guardias que ya existían**:

- `test_los_libros_no_estan_ignorados` se puso roja: `data/trading/` está en
  `.gitignore` con lista blanca, y el libro nuevo no estaba. **Habría vivido en el
  runner y muerto con él, que es exactamente lo que el encargo avisaba.** Añadida la
  línea `!/data/trading/libro_del_escaparate.jsonl`.
- `test_ninguna_clave_publicada_se_pierde` se puso roja: la clave nueva llegaba al
  navegador y moría en `raw` porque `normalizeStatus` no la nombraba. Añadida.

**Idempotente**, y con el corte en el reset:

```
07:30 del 17  ->  escribe      (día de mercado 2026-09-17)
09:15 del 17  ->  NO duplica
03:00 del 18  ->  NO duplica   <- todavía es el escaparate del 17
06:00 del 18  ->  escribe      (día de mercado 2026-09-18)
```

Ese tercer caso es el que `censo_del_reset` no cubre: compara contra `at[:10]`, el día
natural, así que para él una vuelta de las 03:00 y otra de las 06:00 son el mismo
reset cuando son dos. **No lo he tocado** —no es de este encargo— pero queda dicho.

### Una exposición que descubrí al correr la verja, y que dejo dicha

`test_el_ciclo_publica_v1` ejercita el ciclo de publicación, así que llama a
`build_state` y **escribe una línea en el libro**. Lo vi porque el fichero apareció en
disco después de correr la verja, sin que ningún ciclo real hubiera pasado.

**No es algo que haya introducido yo**: esa guardia ya escribe `bitacora_del_saldo.jsonl`
y toca el censo por la misma vía, y sale censada en la verja con todos los ficheros que
abre. Pero ahora también toca este libro, y conviene saberlo:

- El riesgo práctico hoy es bajo: la línea que escribe es **la misma que escribiría el
  ciclo** —los veinte de la foto real— y la idempotencia impide una segunda del mismo
  día de mercado.
- El riesgo real es el día que la verja corra con una foto vieja y el ciclo no haya
  pasado: el libro se quedaría con un escaparate que no es el de ese reset.

**No lo arreglo aquí** —tocaría `test_el_ciclo_publica_v1`, que no es de este encargo—.
Lo que propongo cuando toque: que el libro solo escriba si la foto es de este reset,
comparando el `dia_de_mercado` de la foto con el de ahora. Son dos líneas.

Y el fichero que quedó escrito en disco **no va en este commit**: los libros los sube
`guardar_los_libros.py`, no yo.

---

## BLOQUE 1 — El mapa del `intent`, sacado del árbol

**Los números no están escritos aquí: se importan de donde se aplican.** Si alguien
mueve el 3 % en `rival_bid_model`, el mapa lo dice solo.

### `XI_UPGRADE` (clase SIGNING) — vías `XI_UPGRADE`, `ROSTER_FILL`

| freno | aplica | qué hay |
|---|---|---|
| listón | **NO** | en su lugar: margen del **25 %** al tocar el once (10 % si no), mínimo de **8 puntos** de mejora, veto de **2 escalones** de jerarquía, y que el valor **supere al precio** |
| bolsillo | — | **FICHAJES** — 100 % de la caja más el margen de deuda segura |
| tope de prima | **NO** | **SIN TOPE.** `optimal_bid` solo lo aplica a SPECULATION. **Este es el freno que se cae al mover la etiqueta — doctrina 69** |
| mínimo | **NO** | en su lugar: los 8 puntos y que el valor supere al precio |
| prob. mínima | 0,15 | |

### `SPECULATION` (clase TRADE) — vías `PRICE_TREND`, `COMPUTER_RESALE`, `HOLD`

| freno | aplica | valor |
|---|---|---|
| listón | **SÍ** | **3 %** de rendimiento sobre el capital inmovilizado |
| bolsillo | — | **ESPECULACION** — el límite de apostar |
| tope de prima | **SÍ** | **+0,25 %** sobre el precio de mercado |
| mínimo | **SÍ** | **25.000 €** de ganancia esperada |
| prob. mínima | 0,15 | |

### Quién lo decide: **dos**

```
src/analysis/deployment.py              classify_operation, por CLASE. El que manda hoy.
src/analysis/acquisition_valuation.py   max(opciones, key=value), por euros. Solo APAGADO.
```

### Quién lo nombra: **24 ficheros**, escaneados del árbol

Cada uno con lo que hace: `LO REPARTE` (2), `DECIDE` (6), `ENSEÑA` / `RECONSTRUYE` /
`SE AUTODECLARA` / `LO PASA` / `LO COPIA` / `LO APUNTA` (16).

> **Y aquí un fallo mío, que es justo el que el encargo pedía evitar.** La primera
> versión de este módulo escribió la lista **de memoria** y salió mal en las dos
> direcciones: **cinco ficheros que sí lo nombran faltaban** (`la_plaza_y_el_cable`,
> `position_ledger_v105`, `speculation_engine`, `autopilot`, `v10_full_autonomous_live`)
> y **quince que no lo nombran sobraban**. El encargo decía literalmente «que salga del
> código, no de la memoria» y a la primera no lo cumplí.
>
> Ahora `lectores_del_intent()` recorre el árbol y le pega a cada fichero su anotación.
> **Un fichero nuevo que lo nombre sin anotar pone la verja en rojo.**

---

## BLOQUE 2 — Tu planteamiento, corregido

### Lo que dices

> «El `intent` se elige por qué vía da más euros, y luego se aplican los listones de
> esa vía.»

### Lo que corre

```
DEPLOYMENT_ENABLED = True   (DEPLOYMENT_DEFAULT = "1", desde el 13/09)
```

La etiqueta la reparte `classify_operation`, que **ya hace lo que propones**:

```
el PROPÓSITO   classify_operation  ->  SIGNING / TRADE
la VALORACIÓN  las cuatro vías     ->  cuánto vale
el propósito manda bolsillo, listón y tope
```

### Y no está rota — el libro de pujas

```
2026-09-05  Kiko Femenía    precio  1.150.000   valor  1.494.925   WON
2026-09-12  Rubén García    precio  2.680.000   valor  3.097.172   WON
```

**2 fichajes de 10 pujas con etiqueta, y ganamos los 2.** En los dos, el valor como
fichaje **superaba al precio**, que es exactamente la puerta que `classify_operation`
pone. (Hay 15 pujas más sin etiqueta: el campo se añadió después.)

### Entonces, ¿qué pasa hoy?

```
de los 66 candidatos:
  con valor POSITIVO como fichaje      6
  con ese valor POR ENCIMA del precio  0
```

```
jugador                 precio   valor fichaje    le falta   valor activo
Budimir             11.990.000       3.427.226   8.562.774     12.200.424
Jonathan David       7.870.000       3.213.066   4.656.934      8.025.665
Pépé                11.480.000       3.195.607   8.284.393      3.195.607
Chupe                3.960.000       2.895.184   1.064.816      2.895.184
Alfonso Herrero      4.100.000       2.486.875   1.613.125      4.171.955
Gerenabarrena        3.220.000       1.253.911   1.966.089      3.276.511
```

> **Los dos que el 17/09 «mejoraban el once» no caen por el bolsillo ni por el listón.
> Caen antes.** Budimir vale 3,43 M como fichaje y cuesta 11,99 M: pagarlo sería pagar
> 181.667 € por punto de mejora cuando el mercado paga 21.372 €. **La vía del once
> tiene razón.**

---

## Lo que SÍ está mal, y no es el `intent`

`xi_upgrade_value` **mide el dinero como si desapareciera**. Devuelve el 80 % del que
sale (`recovered_value`) pero **no cuenta que el que entra es también un activo**.

```
Budimir:  valor como fichaje    3.427.226   (899.227 de puntos + 2.528.000 de Jutglà)
          valor como activo    12.200.424
          precio               11.990.000
```

Por la primera columna es un disparate. Sumando la segunda, no lo es. **Y la vía de
reventa sí cuenta el activo** — por eso Pepe compra (26 subastas ganadas) pero casi
nunca *como fichaje*.

**Esa es la asimetría.** No el `intent`.

### Qué freno se queda huérfano al separar

**El tope de prima del +0,25 %.** Si un candidato pasa de TRADE a SIGNING, `optimal_bid`
deja de aplicárselo y puja hasta el valor. Está escrito en el mapa con su aviso y con
el número de la doctrina 69, y hay guardia que exige que **ningún freno que no aplica
salga sin decir qué hay en su lugar**.

> Esa guardia cazó un hueco en mi propio mapa: `XI_UPGRADE/mínimo` decía «no aplica» y
> se callaba que en su lugar hay **otro mínimo, en otra unidad** (8 puntos). Un freno
> que no se nombra es un freno que desaparece el día que alguien reordene la vía.

---

## BLOQUE 3 — Qué habría cambiado, y cuánto se abre

### 1. Hoy

**Nada.** Los dos del escaparate que mejoran el once seguirían cayendo, porque lo que
los tumba es que su valor como fichaje no llega al precio, y eso no lo cambia separar
el propósito.

### 2. En los diez días de escaparate: **no se puede medir**

Y por la misma razón que ayer: hace falta el valor como fichaje de cada uno de los
veinte, que necesita el pronóstico de titularidad **del que entra y del que sale ese
día**.

```
días de mercado con snapshot            9
de esos, con NUESTRO ONCE dentro        3
```

**Con el libro del bloque 0 esta tabla se puede hacer dentro de un mes.** Es justo para
lo que existe.

### 3. Cuánto más podría gastar Pepe en un día. **El número antes de encender.**

Contando el activo del que entra, **4 de los 66 pasarían a ser fichaje**:

```
jugador               precio     fichaje       activo         suma      margen
Budimir           11.990.000   3.427.226   12.200.424   15.627.650   3.637.650
Jonathan David     7.870.000   3.213.066    8.025.665   11.238.731   3.368.731
Alfonso Herrero    4.100.000   2.486.875    4.171.955    6.658.830   2.558.830
Gerenabarrena      3.220.000   1.253.911    3.276.511    4.530.422   1.310.422
```

```
bolsillo de especular (hoy)     5.324.469
bolsillo de fichar              8.874.116
techo de Biwenger              13.743.516

operación más grande HOY                0
con el activo contado           8.874.116
CUANTO MAS                      8.874.116
```

> **Se abre el bolsillo entero.** Se pasa de no poder comprar a nadie a poder
> comprometer **8.874.116 € en una sola operación**, sobre un jugador cuya mejora del
> once vale 3,43 M — y **sin el tope de prima**, porque al ser SIGNING se lo quita.
>
> **Mi respuesta: no lo enciendas así.** El razonamiento de contar el activo es
> correcto, pero convertido en regla autoriza a pagar 12 M por 66 puntos con el
> argumento de que se puede revender. Si de verdad se puede revender, eso ya lo hace la
> vía de reventa, con su listón del 3 % y su tope del +0,25 % puestos.
>
> Lo que faltaría antes: un freno propio para esa vía combinada. Hoy no lo hay, y por
> eso queda escrito y apagado.

### Y un error mío que encontré corriéndolo

La primera versión de la sombra sumaba `xi_value + deployment.value`. Para **Pépé y
Chupe** esos dos números son **el mismo euro** —la vía que da el máximo *es* la del
once— y la suma los doblaba: Pépé salía con 6.391.214 cuando vale 3.195.607. Corregido
mirando `value_route`, y con guardia que lo fija usando el caso de Pépé.

---

## Guardias

**+1 módulo, 6 guardias**, en `src/analysis/test_el_proposito_v1.py`, dada de alta en
`scripts/run_validation_gate.py`.

**Las trece inyecciones de fallo muerden**, probadas reintroduciendo el fallo en
memoria:

```
MUERDE  libro / duplica el reset
MUERDE  libro / corta a medianoche
MUERDE  libro / escribe el escaparate vacío
MUERDE  libro / el pronóstico None sale como 0
MUERDE  mapa / miente sobre el tope de prima
MUERDE  mapa / deja un fichero sin anotar
MUERDE  mapa / freno sin decir qué hay en su lugar
MUERDE  frenos / el fichaje hereda el listón
MUERDE  frenos / mismo bolsillo para los dos
MUERDE  frenos / una etiqueta desconocida decide
MUERDE  sombra / resucita al que el once rechazó
MUERDE  sombra / autoriza por encima del techo
MUERDE  interruptor / encendido
```

`test_el_mapa_del_intent_no_miente` **no compara el mapa consigo mismo**: ejercita
`optimal_bid` con las dos etiquetas y comprueba que el tope de prima y el listón del
3 % pasan donde el mapa dice y no pasan donde dice que no.

### Lo que no mordía no era una guardia: era el módulo

Ya está dicho arriba —la lista de lectores escrita de memoria— y queda en el docstring
del módulo y en el de la guardia, porque es el fallo más caro de los tres de hoy.

**Ninguna guardia lee `data/`**: el libro se prueba contra una ruta temporal que la
propia guardia crea y borra. Los instantes entran por argumento. El escaneo del mapa
lee **código**, no estado.

---

## Medición

`scripts/el_proposito.py` — 200 líneas de salida, exit 0, solo lectura de disco, sin
red.

```
python scripts/el_proposito.py > salida.txt 2>&1
echo $?
```

---

## Lo que no hice, y por qué

- **Ni una escritura contra Biwenger.**
- **No encendí la separación.** `el_proposito.ENCENDIDO = False`. Lo único que entra en
  producción es el libro del bloque 0.
- **No toqué `count_free_slots` ni `historical_max`** — sigue pendiente y `ROSTER_FILL`
  sigue sin tope.
- **No moví ningún listón, bolsillo ni tope.** El mapa los publica; el módulo los
  importa de donde se aplican y no los redefine.
- **No toqué `censo_del_reset`**, aunque su idempotencia use el día natural en vez del
  día de mercado. Queda dicho.
- **No construí la regla de liquidez.**
- **No propuse comprar ni vender a nadie.**
- **No salí a la red.**
- **No toqué `.github/workflows/bordalas-live.yml`.**
- **No empujé.**

### Lo que contradijo al encargo, y ganó la medición

1. **El `intent` no se elige por euros.** Se elige por clase, desde el 13/09, y la
   separación que pedías ya existe con ese nombre.
2. **No está rota:** ha fichado dos veces en once días y ganó las dos.
3. **Hoy no bloquea el `intent`:** 0 de 66 candidatos valen como fichaje lo que cuestan.
4. **Lo que sí está mal es otra cosa:** la vía del once mide el dinero como si
   desapareciera. Y arreglarlo a lo bruto abre el bolsillo entero — 8.874.116 € en una
   operación, sin tope de prima.
