# INFORME — DEVOLVERLE LA PUJA A PEPE

**Fecha:** 2026-09-22
**Rama:** `arreglo/la-puja-que-vuelve`, desde `main`
**Commit:** `85fcede`
**Verja:** a fichero, **172/172 en verde, exit 0**, árbol quieto.
**No se ha empujado nada. No se ha encendido ni apagado ningún interruptor.**

---

## LO PRIMERO, PORQUE CAMBIA EL ENCARGO

El encargo dice: *«Si el interruptor apaga los dos, hemos cerrado la única puerta por
la que Pepe podría fichar a alguien bueno.»*

**No apaga los dos, y esa no es la única puerta.** Las dos cosas están medidas abajo.
Lo que `BORDALAS_SIN_SUBASTA` apaga es **una función**, y esa función solo sabe hacer
modo cartera: **dentro de la subasta del reset no hay ningún «modo plantilla»**. La
compra para quedarse no vive ahí — vive en el tablero de fichajes y en el carril de la
rendija, y **los dos siguen pujando con el interruptor puesto**.

Y hay una consecuencia peor que la que preocupaba: **el interruptor no frena la vía por
la que se compró la mitad de la temporada.** El 18/09, con la cesta abierta, el carril
puso diez escrituras contra Biwenger él solo.

---

## BLOQUE 1 — QUÉ APAGA EXACTAMENTE

### La línea, y son dos: la que lee y la que decide

```
src/analysis/la_subasta.py:1477-1483        def _sin_subasta():
                                                return os.environ.get(DISABLE_ENV, "")
                                                       .strip().lower() in {...}

src/analysis/la_subasta.py:1553             if _sin_subasta():
                                                return {... "blocked_by": "INTERRUPTOR" ...}
```

(En `main`, antes de este commit: `:1387` y `:1459`.)

### ¿Hay más de un lector? NO. Hay uno.

Barrido de todo el árbol `src/` y `scripts/`:

| fichero | qué hace con él |
|---|---|
| `la_subasta.py:1469` | lo declara: `DISABLE_ENV = "BORDALAS_SIN_SUBASTA"` |
| `la_subasta.py:1477` | **lo lee** — el único sitio |
| `la_subasta.py:1553` | **decide con él** — el único sitio |
| `dashboard_state.py:3371, 3460` | **imprime la cadena** en pantalla. No lo lee |
| `test_encender_las_pujas_v1.py`, `test_una_ventana…`, `test_solo_un_interruptor…` | guardias, lo ponen y lo quitan ellas |

**Un lector, un decisor.** No son dos interruptores.

### Qué caminos deja muertos, y cuáles no

`_sin_subasta()` cierra `plan_del_reset`. `plan_del_reset` tiene **un solo modo**
(`la_subasta.py`, la llamada a `candidatos_en_modo_cartera` dentro de la función): toda
puja que sale de ahí es **modo cartera**.

| camino de puja | ¿lo apaga `BORDALAS_SIN_SUBASTA`? | su interruptor |
|---|---|---|
| **subasta del reset, modo cartera** (`plan_del_reset` → `_pujar_en_el_reset`) | **SÍ** | `BORDALAS_SIN_SUBASTA` |
| **carril de la rendija** (`carril_executor.correr`) | **NO** | `RENDIJA_APAGADA` |
| **tablero de fichajes** (`optimal_bid` → `autopilot_executor`, `live_bid_executor`, `franchise_*`) | **NO** | ninguno propio |
| **`ROSTER_FILL`** | **NO** — no es un camino de puja, es una **vía de valoración** (`acquisition_valuation`). No escribe nada. Lo que cierra el `ROSTER_FILL` hoy es que no hay fichas libres, no el interruptor | — |

### Entonces, ¿la frase está mal escrita o es la pura verdad?

**Está mal escrita.** «No se puja nada» es verdad **de `plan_del_reset`** y falsa del
sistema. Con el interruptor puesto Pepe sigue pudiendo pujar por el carril y por el
tablero de fichajes.

Queda anotado en el código, al lado del propio interruptor (`la_subasta.py`, cabecera de
`MAX_PUJAS_PRIMER_DIA`).

---

## BLOQUE 2 — EL CORTE

### Doctrina 84 primero: no existía

Inventario completo de interruptores (`scripts/los_interruptores.py`): **22 antes de
hoy**. Ninguno separa reventa de fichaje. El más cercano, `BORDALAS_CESTA_SOLO_EL_SUELO`,
acota la cesta **por precio** (debajo de 1.500.000) — es otro eje.

### El corte: `BORDALAS_SIN_REVENTA`

`src/analysis/el_corte_de_la_reventa.py`. **Apagado de fábrica.**

Mira **la vía del candidato**, no el camino de código por el que llega la puja:

```
QUEDARSE    route ∈ SIGNING_ROUTES            (deployment.py)
            o intent ∈ INTENCIONES_DE_QUEDARSE (los_dos_techos.py)
REVENDER    cualquier otro intent/route, o modo CARTERA
None        no consta  →  se frena (sin vía no se escribe)
```

**No escribe vocabulario nuevo** (doctrina 33 y 84): importa las dos listas que ya
existían. Hay guardia de que no se separen —
`test_el_corte_usa_el_vocabulario_que_ya_existe`.

Enganchado en los **dos** sitios que pujan para revender:

- `la_subasta.plan_del_reset` — antes del reparto, para que la cesta no gaste
  presupuesto en candidatos que luego se frenan. `blocked_by: "SIN_REVENTA"`.
- `carril_executor.correr` — después del filtro de repetidos, antes de `a_quien_pujar`.

### Por qué POR CANDIDATO y no por camino — y esto lo decidió la medición

Mi primer diseño era cortar el carril entero: el carril compra para revender, escribe
`intent="REVENDER"` a mano. **La medición lo tumbó.**

El 18/09 el carril puso **diez pujas por Maffeo**, y la foto de ese día lo clasifica:

```
"pasan_el_del_comerciante": [{"name": "Maffeo", "via": "QUEDARSE", ...}]
   valor como fichaje 1.992.831   ·   precio 1.660.000
```

Un corte de brocha gorda **habría tumbado una compra de plantilla** — el tercer renglón
de la tabla no habría salido cero. Está escrito en el código, en `carril_executor`,
donde vive el corte.

### La tabla contrafactual, sobre el libro entero de la temporada

Calculada llamando a `corta()`, la misma función que corre en producción, con el
interruptor puesto. **n = 56 pujas** (`data/trading/bid_outcome_ledger.json`,
10/08/2026 – 21/09/2026).

```
                                       con el corte nuevo
las 6 compras del 21/09                6 PARADAS   (2.566.406 EUR)
el resto de compras de la temporada    13 paradas por REVENDER
                                       25 paradas por via que NO CONSTA
                                       12 siguen  (via QUEDARSE)
compras "para quedarse" paradas        0     <-- CERO
```

**Las 6 del 21/09, una por una:**

| hora (UTC) | jugador | importe | origen | vía |
|---|---|---|---|---|
| 03:09:47 | Yeray | 1.624.051 | `SUBASTA_CARTERA` | REVENDER |
| 03:09:47 | Diaby | 150.376 | `SUBASTA_CARTERA` | REVENDER |
| 03:09:47 | Guevara | 160.401 | `SUBASTA_CARTERA` | REVENDER |
| 05:07:47 | Aihen | 220.551 | `DESCONOCIDO` | no consta |
| 05:07:47 | Guliashvili | 180.451 | `DESCONOCIDO` | no consta |
| 05:07:47 | Van Oevelen | 230.576 | `DESCONOCIDO` | no consta |

Las seis se paran. **Pero tres no se paran por lo que el encargo esperaba.** El encargo
dice «espero las 6 paradas: todas `SUBASTA_CARTERA`». **El libro dice que solo tres lo
son.** Las otras tres llevan:

```
"target_source": "DESCONOCIDO",  "intent": null,
"recorded_by": "PLANTILLA",      "placed_at_is_resolution": true
```

Es decir: **el libro no las apuntó al pujarlas — las encontró en la plantilla después
del reset.** Se paran por «sin vía no se escribe», no por ser reventa reconocida.
Doctrina 103: no es lo mismo «sabemos que era cartera» que «no se lo preguntamos a
nadie».

Lo que sí se puede decir con el dato delante: **sus importes son exactamente
`precio × 1,0025 + 1`**, que es `puja_de_cartera` al céntimo (220.000 → 220.551;
180.000 → 180.451; 230.000 → 230.576), y suman con las otras tres los 2.566.406 EUR que
el propio YAML apunta. **Eso es indicio fuerte, no registro.** El registro se perdió:
la segunda vuelta del 21/09 no llegó a escribir sus libros (el `libro_de_la_ventana`
solo tiene la primera).

**Los 25 «no consta»:** 9 son de agosto y principios de septiembre, anteriores al libro
con origen; 5 son del carril en días sin foto —el carril **pisa el `intent` del tablero
con un `"REVENDER"` escrito a mano**, así que el libro no conserva la vía de verdad—;
el resto son reconciliaciones. **El corte los frenaría** (sin vía no se escribe), y eso
es una decisión consciente y conservadora, no un descuido. En vivo esto casi no ocurre:
la fila del tablero sí trae `intent`.

### ¿El corte tumba alguna compra de plantilla?

**Cero.** Las 12 que siguen son las 12 de vía QUEDARSE:

- Kiko Femenía (05/09, `ACQUISITION_BOARD`, `XI_UPGRADE`)
- Rubén García (12/09, `ACQUISITION_BOARD`, `XI_UPGRADE`)
- Maffeo ×10 (18/09, carril; vía QUEDARSE según la foto de ese día)
- Cabrera (18/09; vía QUEDARSE según la foto de ese día)

Guardia: **`test_el_corte_no_toca_la_compra_de_plantilla`**. Con el corte puesto, un
candidato clasificado «para quedarse» sigue generando puja — comprobado a pelo sobre
`corta()`/`separar()` **y** sobre `plan_del_reset`, que es donde se puja de verdad.
**Muerde si el caso no trae candidato de plantilla** y **también si no trae ninguna
reventa que cerrar**: sin las dos cosas, que el de plantilla siga no probaría que se
hayan separado.

**Una salvedad honesta:** las fotos de Maffeo y Cabrera son de las 16:16 del 18/09, y
sus pujas son de entre las 05:23 y las 15:18 del mismo día. Es el tablero **de ese día**,
no el del minuto exacto de la puja. No hay foto por vuelta.

---

## BLOQUE 3 — Y QUE LA PUERTA DÉ A ALGÚN SITIO

### La condición para salir «quedarse», con el código

Son **cuatro puertas en serie**, no una. Doctrina 99.

**A. Que haya ficha libre** — `acquisition_valuation.py:627`

```python
huecos = safe_int((context or {}).get("free_roster_slots"))
como_relleno = None
if huecos > 0:
```

`free_roster_slots` sale de `count_free_slots(auditoria)` **sin** `historical_max` —
decisión del dueño del 17/09, escrita ahí mismo: *«CUATRO HUECOS ABREN `ROSTER_FILL` (…)
y esa vía NO TIENE TOPE DE PRIMA. Mientras no lo tenga, la plaza se queda cerrada.»*

**B. El veto de la ficha** — `deployment.py:420` (`roster_fill_veto`)

```python
if probabilidad is None:                       return "Sin pronostico de titularidad..."
if float(probabilidad) < MIN_STARTER_PERCENT:  return "Solo X % de titularidad..."     # 40.0
if jerarquia is not None and safe_int(jerarquia) < MIN_HIERARCHY_VALUE:                # 40
                                               return "Jerarquia ... por debajo de Rotacion"
if estado.get("can_play") is False:            return "No esta disponible..."
```

**C. Que el valor de fichaje LLEGUE AL PRECIO** — `deployment.py`, `classify_operation`

```python
if price is not None and fichaje:
    compensan = [via for via in fichaje
                 if safe_int(via.get("value")) > safe_int(price)]
    if not compensan:
        fichaje = []            # <- deja de ser un fichaje
```

**D. Y entonces la columna** — `los_dos_techos.py:296`

```python
via = ("QUEDARSE" if str(intent or "").upper() in INTENCIONES_DE_QUEDARSE
       else ("REVENDER" if intent else None))
```

Con `DEPLOYMENT_ENABLED` encendido —que es lo de hoy— `intent` sale de
`INTENT_BY_CLASS[SIGNING] = "XI_UPGRADE"`. O sea: **D no filtra nada. Quien decide es C,
y antes B, y antes A.**

### Dónde muere, medido

Sobre las tres fotos que hay en el árbol:

| foto | objetivos | A: huecos | B: pasan el veto | C: valor > precio | **QUEDARSE** |
|---|---|---|---|---|---|
| 14/09 18:33 | 64 | 2 | **0** | 0 | **0** |
| 18/09 16:16 | 54 | 3 | 19 | **2** | **2** |
| 20/09 09:10 | 55 | 9 | 20 | **0** | **0** |

- **14/09:** los 64 mueren en B, y **todos por la misma causa: «sin pronóstico de
  titularidad».** Ese día el ojeador no trajo nada. No es que no hubiera candidatos: es
  que no se les preguntó (doctrina 103).
- **20/09:** con **nueve** fichas libres, **veinte** candidatos pasan el veto y **ninguno**
  llega a fichaje. El más cerca, Moncayola: vale 2.307.435, cuesta 2.480.000. Faltan
  172.565 EUR.
- **Hoy:** cero fichas libres (las 21 fichas del 21/09). **La puerta A está cerrada, y
  con ella todo lo demás.** Eso es lo que da el «0 de 46».

### ¿Cuántas veces ha salido «quedarse» en toda la temporada?

**n = 5 lecturas sobre 4 días con foto** (14/09, 18/09, 20/09 ×2 —la del árbol y la que
cita el encargo— y 21/09):

```
14/09 18:33   quedarse 0    revender 41    (n=64 objetivos)
18/09 16:16   quedarse 2    revender 34    (n=54)
20/09 09:10   quedarse 0    revender 38    (n=55)
20/09 22:18   quedarse 0    revender 33    (del encargo)
21/09 22:18   quedarse 0    revender 21    (del encargo)
```

**NO es cero. Han salido DOS, los dos el 18/09: Cabrera y Maffeo.** Y no se quedaron en
la pantalla: **los dos se compraron y los dos se ganaron** — Cabrera el 18/09 a las
15:18 por 3.116.031 (`WON`), Maffeo por el carril el mismo día (`WON`).

Así que la respuesta al *«por qué Pepe no ha fichado un solo punto en toda la
temporada»* **no es que la puerta nunca se abra.** Se abrió el 18/09 y entraron dos. Lo
que hay es una puerta que se abre poco — **2 de 173 filas de objetivo en tres fotos,
un 1,2 %** — y que hoy está cerrada de raíz por A.

**Y lo importante para el plan de la semana:** el cuello de botella medido **no es el
criterio de «quedarse»**, es **C**: el valor de fichaje no llega al precio. El 20/09
fueron **0 de 20** los que lo pasaron. Reabrir A vendiendo el relleno abre 20
candidatos que **se caen todos en C**. Doctrina 99 otra vez, un escalón más abajo.

### Los campos que se pierden por el camino

**Sí los necesita, y no solo la de quedarse.** Dos sitios los tiraban:

1. `la_subasta.lectura_del_estado` copiaba **seis** campos.
2. `carril_executor.correr` copiaba **cinco** (`player_id`, `name`, `position`,
   `market_price`, `bid`).

**Qué necesita cada decisión:**

- **La de «quedarse»** necesita `starter_probability` y `hierarchy_value`: son
  literalmente los dos números de `roster_fill_veto` (puerta B). Sin ellos no se puede
  decidir nada de plantilla.
- **La de cartera también los necesita, y por eso pasó lo del 21/09.** Cinco de las seis
  compras son suplentes de 150.000-230.000 que el propio motor etiqueta «Es Reserva en
  su equipo: no va a puntuar». **La cesta no los prefirió: no podía verlos.** En modo
  cartera todos rinden igual por euro, así que decidía el desempate —«gana el que
  consume menos capacidad»— que en el suelo significa comprar lo peor del mercado.
  **Doctrina 110.**
- **`intent` y `route`** son lo que el corte mira. Sin ellos el corte frena a todos y la
  separación es imposible.

**Llevados.** `lectura_del_estado` lleva ahora once campos; el carril, siete.

**Lo que cuesta, medido:** foto del 18/09, n = 54 objetivos, 2.000 repeticiones:
**0,014 ms con seis campos → 0,025 ms con once.** **Once microsegundos por vuelta**,
contra vueltas de 47 minutos. Ni red, ni disco, ni una llamada más: la fila ya está en
memoria.

**No deciden nada todavía.** `candidatos_en_modo_cartera` no los lee. Viajan para que el
corte los mire y para que se vean en pantalla. Que la cesta mire la jerarquía antes de
comprar es el trabajo siguiente, y es la condición que el propio dueño puso en el YAML
para reabrir la reventa.

---

## BLOQUE 4 — EL CUPO, POR VENTANA

### `BORDALAS_CUPO_POR_VENTANA`, apagado

Una línea, sobre el libro que ya llega:

```python
en_la_ventana = len(puestos)          # `puestos` ya existía: es `ya_pujados`
if cupo_por_ventana():
    tope = max(0, tope - en_la_ventana)
```

`ya_pujados` viene de `pujados_desde(...)` sobre `bid_outcome_ledger`, y ya se usaba
para no repetir jugador. **Ni un número nuevo:** el cupo sigue siendo `3`.

### Lo que decía el libro, medido

`data/trading/libro_de_la_ventana.jsonl`, **n = 19 vueltas con la ventana abierta, en 10
ventanas** (12/09 – 21/09):

```
ventanas con dos vueltas dentro ........ 9 de 10
ventanas cuya SUMA pasó de tres ........ 3

    12/09   3 + 1 = 4
    15/09   1 + 3 = 4
    18/09   3 + 2 = 5
```

El 21/09 el libro solo tiene la primera vuelta —la segunda no llegó a escribir— pero el
libro de pujas tiene **las seis compras**, 2.566.406 EUR.

### Qué habría parado

Simulado sobre el libro, con el cupo aplicado a lo que propone la subasta y
`ya_pujados` contando todo lo nuestro sin resolver en la ventana:

```
7 pujas paradas  ·  3.208.007 EUR

  12/09 02:52   Sotelo          1.604.001
  15/09 02:54   Selu Diallo       150.376
  18/09 02:53   Esquivel          150.376
  18/09 02:53   Carmona           671.676
  21/09 05:07   Aihen             220.551   \
  21/09 05:07   Guliashvili       180.451    > las tres de ayer: 631.578
  21/09 05:07   Van Oevelen       230.576   /
```

Las tres de ayer y sus 631.578 EUR: **paradas.**

### Lo que hay que saber antes de encenderlo

**`ya_pujados` cuenta TODAS nuestras pujas sin resolver de la ventana, vengan de la
cesta o del carril.** Es la misma lista que ya se usa para no repetir jugador, y no hay
otra sin preguntarle al libro una segunda cosa. **Cuenta de menos pujas, nunca de más.**
Está escrito en el código.

**Y la pantalla:** el panel llama a `plan_desde_el_estado` **sin** el libro, así que ahí
`ya_en_la_ventana` sale 0. Eso es «no se ha preguntado», no «van cero» (doctrina 103), y
se publica al lado del plan para que se note.

Guardia: **`test_el_cupo_de_la_ventana_no_se_reinicia_por_vuelta`**. Dos vueltas dentro
de la misma ventana, tres pujas en la primera, la segunda no puja. **Muerde si el caso
tiene una sola vuelta** —comprueba con `ventana_abierta()` que los dos instantes caen
dentro— y **muerde también si la primera vuelta no llegó a pujar tres**, porque entonces
no habría cupo gastado que probar. Y comprueba que el cupo **resta**, no cierra: con dos
puestas todavía cabe una.

---

## LO QUE SE HA TOCADO

```
src/analysis/el_corte_de_la_reventa.py        NUEVO   el corte
src/analysis/test_el_corte_y_el_cupo_v1.py    NUEVO   10 guardias
src/analysis/la_subasta.py                            corte + cupo + 5 campos
src/actions/carril_executor.py                        corte + 2 campos
src/telemetry/dashboard_state.py                      los dos en pantalla
src/analysis/el_proposito.py                          el mapa del intent
scripts/run_validation_gate.py                        la guardia en la verja
```

**Los dos interruptores nacen apagados.** Con ellos quitados el sistema se comporta
exactamente como el 21/09, y hay guardia de eso
(`test_el_corte_apagado_no_frena_ni_una_puja`, `test_el_cupo_apagado_se_comporta_como_ayer`).

**El paso 0 no se ha corrido**: va antes de encenderlos en el YAML, y eso lo hace el
dueño. `test_el_paso_0_no_se_olvida_v1` sigue verde porque ninguno está encendido.

---

## LO QUE NO SE HA HECHO, Y POR QUÉ

| | por qué |
|---|---|
| **Ninguna escritura contra Biwenger** | lo prohíbe el encargo |
| **No se ha encendido ni apagado ningún interruptor** | los toca el dueño en el YAML |
| **No se ha tocado `.github/workflows/bordalas-live.yml`** | lo prohíbe el encargo |
| **No se ha reabierto la reventa** | sigue cerrada por `BORDALAS_SIN_SUBASTA=1`, que el dueño puso |
| **No se ha inventado criterio de «quedarse»** | el bloque 3 mide el que hay |
| **No se ha vendido nada** | lo decide el dueño |
| **No se ha empujado** | «Tú no empujas» |
| **No se ha tocado** `MAX_SINGLE_SPECULATION_PERCENT`, `MAX_SAFE_DEBT`, el suelo de cobro, `MIN_WIN_PROBABILITY`, `MAX_PROJECTED_DAILY_RATE`, `PUEDEN_ENCERRARLO`, `PRIMA_MAXIMA_DE_PUJA`, `VENTANA_MINUTOS` | lo prohíbe el encargo |
| **No se ha hecho que la cesta mire la jerarquía** | los campos ya llegan, pero **usarlos es un criterio nuevo de compra** y no estaba pedido. Es el trabajo siguiente, y es la condición que el propio YAML pone para reabrir la reventa |
| **No se ha arreglado que el carril pise el `intent`** | `record_bid(..., intent="REVENDER")` escrito a mano borra la vía del tablero. Es doctrina 33 y es por lo que 5 pujas del libro salen «no consta». Tocarlo cambia lo que el libro dice de la temporada, y eso se mira aparte |
| **No se ha arreglado `test_el_ciclo_publica_v1`** | ver abajo |

### Un hallazgo que no venía en el encargo

**`test_el_ciclo_publica_v1` sale a la red y escribe en los libros.** Corriendo la verja
con el árbol limpio, esa guardia deja modificados:

```
data/intelligence/libro_de_publicacion.jsonl
data/intelligence/libro_en_la_sombra.jsonl
data/intelligence/marcador.json          (y marcador.json.tmp)
data/rival_intelligence/board_events.json
data/solvency/bitacora_del_saldo.jsonl
```

Reproducido a mano: `python -m src.analysis.test_el_ciclo_publica_v1` sobre árbol limpio
ensucia esos cinco. La regla de la casa es que **ninguna guardia escribe en los libros ni
sale a la red**. Es deuda anterior a este encargo —el censo de la propia verja ya la
tiene fichada como lectora— pero **escribir no es leer**, y significa que «árbol quieto»
después de la verja no se puede comprobar sin restaurar `data/` a mano. **No se ha
tocado**: no estaba en el encargo y arreglarla es un cambio de su tamaño.

---

## SI LA MEDICIÓN CONTRADICE EL ENCARGO, GANA LA MEDICIÓN

Tres sitios donde ha ganado:

1. **«Si el interruptor apaga los dos»** — no apaga dos. Apaga uno, y dentro de la
   subasta del reset no existe el segundo. La puerta de fichar nunca estuvo cerrada por
   `BORDALAS_SIN_SUBASTA`.
2. **«Espero las 6 paradas: todas `SUBASTA_CARTERA`»** — se paran las seis, pero solo
   tres constan como `SUBASTA_CARTERA`. Las otras tres las apuntó el libro al
   encontrarlas en la plantilla. Los importes dicen que eran cartera; el libro no lo
   dice.
3. **«Si la respuesta es cero, dilo con esas palabras»** — **no es cero: son dos**,
   Cabrera y Maffeo, el 18/09, y los dos se compraron. Lo que no hay es una puerta
   cerrada del todo; lo que hay es un cuello de botella **en el precio** (puerta C:
   0 de 20 el 20/09), no en el criterio.
