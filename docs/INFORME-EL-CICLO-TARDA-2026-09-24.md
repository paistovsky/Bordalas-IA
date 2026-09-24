# El ciclo tarda 78 minutos: es el once, 135 veces por vuelta

**Encargo:** «EL CICLO TARDA 78 MINUTOS Y ESO YA CUESTA DINERO», 24/09/2026
**Rama:** `arreglo/el-ciclo-tarda`, desde `origin/main` en `3acf034`

| commit | qué |
|---|---|
| (1) | `el_once_se_busca_una_vez`: memoria de la búsqueda del once, **apagada** |
| (2) | este informe y `config/paso_0.json` |

**Verja 184/184 en verde, código 0**, con `BORDALAS_JORNADAS_POR_SU_FECHA=1` y
`BORDALAS_REVENTA_SOLO_SI_JUEGA=1`, sobre el árbol final. **Paso 0 PASADO**, 30 interruptores
(29 + el nuevo). Ni una petición a Biwenger: todo lo medido va con la red cortada.

Aviso de rama: `arreglo/tres-pequenas` **no está en `origin/main`**. Esta rama sale de `main` como
pide el encargo, así que no la lleva. Por ejemplo, el ciclo todavía llama a `sync_source_accuracy`
(`autopilot.py:4214`).

Dos cosas de la verja:

- **La primera salió roja** en `test_verja_determinista_v1`. Era el falso positivo de siempre: mi
  guardia escribía `"data/"` para **prohibirlo**. Lo he quitado (`open(` y `Path(` ya cubren leer
  disco), y a partir de ahí 184/184.
- **Después añadí una línea de log** (ver bloque 2), y la verja y el paso 0 se han repetido
  enteros sobre ese árbol. Los números de arriba son los de esa segunda corrida.

---

## Cómo se ha medido, y lo que vale

Un laboratorio: una copia del repo en el scratchpad, con **la foto local más reciente (19/09,
plantilla de 19)**, la red cortada a nivel de socket, el tablón servido desde
`data/rival_intelligence/` y los dos interruptores del workflow puestos. Antes de cada corrida,
`data/` vuelve a su estado original.

- **n = 1 corrida por lado**, y dos corridas sin memoria para ver el ruido propio.
- **No es producción**: la plantilla allí es de 22 y el runner es otro. Las cifras de producción
  de este informe son **extrapolaciones** y van marcadas como tales.
- No había `gh` en la máquina, así que **no he leído ningún log de Actions**. Todo lo de producción
  sale de los números del encargo.

---

## Bloque 2: dentro de los 1.070 s. La hipótesis era buena

> *«`build_lineup` es el 94-95 % de los dos»*

**Se sostiene, y se queda corta.** El reparto de `build_global_decision` (perfilador, n = 1):

| | s | % |
|---|---:|---:|
| `build_global_decision_uncached` | 149,6 | 100 |
| `build_lineup` (52 llamadas) | 146,4 | **97,8** |
| de eso, la búsqueda recursiva (`search_best_lineup_for_formation`) | 145,6 | 97,3 |
| todo lo demás | 3,2 | 2,2 |

*(149,6 s con el perfilador puesto; sin él, 88,1 s. El reparto es el mismo.)*

Las 52 llamadas, por quién las hace:

| n | s | quién llama |
|---:|---:|---|
| 16 | 46,4 | `build_deadline_state` ← `classify_liquidity_pressure` (offer_analyzer) |
| 9 | 26,1 | `build_deadline_state` ← `build_solvency_state` |
| 9 | 26,2 | `analyze_sales` ← `calculate_liquidatable_assets` (solvency_engine) |
| 5 | 11,0 | `simulate_lineup_without_players` (competitive_offer_portfolio) |
| 13 | 36,7 | otras nueve rutas, 1 o 2 llamadas cada una |

### Cuántas veces se llama a `build_lineup` en una vuelta

**135 en una vuelta con escritura** (laboratorio, n = 1):

| etapa | s | `build_lineup` | búsquedas | parte |
|---|---:|---:|---:|---:|
| `build_cycle_acquisition_board` | 17,6 | n = 9, 15,3 s | 63 | 87 % |
| `build_global_decision` | 88,1 | n = 51, 86,5 s | 363 | 98 % |
| `build_sale_intent` | 1,8 | n = 1, 1,8 s | 7 | 99 % |
| `build_competitive_observer` | 36,6 | n = 22, 36,0 s | 160 | 98 % |
| POST `build_global_decision` | 88,1 | n = 52, 86,5 s | 370 | 98 % |

Y fuera de `run_cycle` hay más: el V10.6 hace 56 búsquedas, el V10.7 hace 370 y el dashboard, en
su propio proceso, 587.

### Por qué crece con la plantilla

`search_best_lineup_for_formation` (`lineup_engine.py:1458`) es una búsqueda **exhaustiva por
combinaciones**: por cada posición prueba todas las combinaciones de `take_count` jugadores, desde
el máximo **hasta cero**, y sin poda. Son siete formaciones, y a veces dos pasadas por formación
(normal y de emergencia). En el perfil salen 40,9 millones de llamadas recursivas en 370
búsquedas. Por eso va «0,26 s con 15 fichas y 4,78 s con 21».

### Casi todas las preguntas son la misma

De **963 búsquedas** en la vuelta, **48 son distintas**. El once no cambia entre dos candidatos
del mismo ciclo, como sospechabas, pero el multiplicador no está en «una por candidato». Está en
que cada motor (plazo, solvencia, ventas, liquidez, ofertas) se monta la alineación por su cuenta,
y varios se montan a los otros dentro.

### Lo que se propone: `BORDALAS_EL_ONCE_UNA_VEZ`, apagado

`src/analysis/el_once_se_busca_una_vez.py`, delante de la búsqueda, en `evaluate_formation`. **La
búsqueda no se toca.**

- **Clave**: `sha256(pickle(jugadores, formación, dudosos))`. Entran todos los campos de cada
  jugador, en su orden, y la formación en su orden. Si la entrada no es idéntica byte a byte, no
  acierta. No mira la marca de la foto.
- **Lo que guarda son índices, no el once.** Al acertar, el once se reconstruye con los jugadores
  de **esa** llamada (`{**jugador, "lineup_position": p}`), que es lo mismo que construye la
  búsqueda. Así el resultado es el mismo objeto por objeto, y quien lo toque después (`build_lineup`
  lo ordena en el sitio) no ensucia la memoria.
- **No recuerda lo que no sabe reconstruir igual**: si hay ids repetidos, o si la reconstrucción no
  da `==` con lo buscado.
- Tope de 512 entradas, dentro del proceso: no persiste en disco.

#### Lo que ahorra (laboratorio, n = 1 por lado)

| etapa | sin | con |
|---|---:|---:|
| `build_cycle_acquisition_board` | 17,6 s | 3,7 s |
| `build_global_decision` | 88,1 s | 7,2 s |
| `build_sale_intent` | 1,8 s | 0,0 s |
| `build_competitive_observer` | 36,6 s | 0,6 s |
| POST `build_global_decision` | 88,1 s | 1,4 s |
| **el análisis, PRE + POST** | **232,1 s** | **12,9 s** |
| POST de verdad (la foto tras renovar una publicación nuestra) | 92,0 s | 1,8 s |
| V10.6 (`position_manager`) | 6,9 s | 3,9 s |
| V10.7 (`counter_repricing`) | 15,0 s | 2,4 s |
| `build_dashboard_state` (misma semilla de hash) | 36,6 s | 14,1 s |

#### La prueba de que no cambia nada

He comparado **campo a campo** la salida de las cinco etapas (tablero, resultado completo con
decisión y candidatas, intención de venta, observador y POST):

- **sin memoria contra sin memoria**: 3.467 campos distintos. Todos son de reloj (`age_hours`,
  `hours_to_expiry`, `seconds_to_*`, `now`…), textos que llevan esas horas dentro, o errores de la
  red cortada.
- **sin memoria contra con memoria**: **las mismas familias, y 0 diferencias fuera de ellas**. Da
  igual la decisión, cada once o cada candidata.
- **POST realista**, sin contra con: **0 diferencias** fuera del reloj.
- **Dashboard**: 0 fuera del reloj **con la misma semilla de hash**. Con semillas distintas sale
  desordenada `marcador.jornadas[].detalle.faltaron`: los mismos jugadores en otro orden. No es la
  memoria. Es `marcador.py:2291-2293`, que resta conjuntos de ids en texto, y los empates a puntos
  heredan el orden del conjunto, que cambia en cada proceso. Lo apunto abajo.

#### La guardia: `test_el_once_se_busca_una_vez_v1` (10 pruebas, 3,6 s)

Plantillas escritas en la propia guardia, con azar de semilla fija, **con empates, dudosos y no
alineables**. Ni disco, ni red, ni reloj. El interruptor se enciende y se apaga dentro, y se deja
como estaba.

Comprueba que apagada no toca la memoria; que encendida da `==` que apagada (12 plantillas × 7
formaciones = 84 comparaciones, y no pasa con las manos vacías); que la segunda pregunta acierta de
verdad; que un solo campo distinto no acierta (1e-9 en los puntos, `int` que pasa a `float`, un
campo que la búsqueda no lee, algo anidado); que el orden cuenta; que lo devuelto es suyo; que con
ids repetidos no recuerda; que tiene tope; que no lee el mundo; y la línea del log.

**Muerde**, probado rompiendo el módulo a mano:

- con una clave que solo mira los ids: `un_solo_campo_distinto` y `el_orden_cuenta` en rojo;
- devolviendo el once guardado sin reconstruirlo: `lo_que_devuelve_es_suyo` en rojo.

#### La línea del log

Con el interruptor puesto, debajo de los cuadros del cronómetro (análisis y panel) sale
`El once, una vez: N búsquedas hechas, M recordadas…`. Apagado no imprime nada, así que el log
queda como hoy. Va porque lo del laboratorio no es producción: la primera vuelta con el
interruptor encendido dirá allí mismo cuántas búsquedas se ahorró.

---

## Bloque 1: el POST. Tu sospecha era verdad a medias, y el atajo se descarta

### Para qué sirve, con la línea

`autopilot.py:4461-4540`, solo si `live` y hubo escritura:

1. `refresh_snapshot()` (`:4480`). **Hace falta**: deja en disco la foto después de la escritura, y
   es la que leen con `refresh=False` el V10.5, el V10.6, el V10.7 y el dashboard.
2. `build_global_decision(post_snapshot)` (`:4487`). Su resultado va a tres sitios:
   - `print_cycle_result` (`:4504`), la consola;
   - `append_log(..., "POST_ACTION")` (`:4526`), una fila del log;
   - `post_action` en el retorno, del que el V10 solo lee `bool(...)` para
     `snapshot_policy.legacy_post_write` (`v10_full_autonomous_live.py:1414`).

**Dentro de `run_cycle` no decide nada.** La fila `POST_ACTION` tiene 40 campos, y el dashboard
solo lee de ella la hora, la fase y el bloque `execution` (`dashboard_state.py:1880-1935`), que es
**el mismo objeto** que el de la fila PRE.

### Pero su cálculo sí se usa, y por eso el atajo no ahorra nada

`build_global_decision` tiene una caché de un hueco **por marca de foto**
(`decision_orchestrator.py:1141-1244`). Después de `run_cycle`, el V10 la vuelve a pedir **sobre la
última foto del disco**:

- `position_ledger_v105.py:915-917`, el V10.5: `sync_current` → `_build_current_trader` →
  `build_global_decision(snapshot)` (`:897`);
- `position_manager_shadow_v106.py:1135`, el V10.6;
- `controlled_speculation_live.py:186`, la compra V10, solo si no hubo escritura.

En una vuelta **con** escritura, la última foto es la del POST, y esas llamadas **aciertan en la
caché que dejó el POST**. En una vuelta **sin** escritura, la PRE no se cachea, porque entra con
`acquisition_board` y la clave sale `None`, así que esa segunda cuenta completa la hace
`build_controlled_run`.

**Toda vuelta hace dos `build_global_decision` completos, con escritura o sin ella.** Si se aligera
el POST, el primero en calcular pasa a ser el V10.5, y los 18,5 minutos **se mueven, no se
quitan**.

### Qué cambia de verdad con una escritura

En el laboratorio, con una renovación simulada, de los 40 campos de la fila solo cambian
`hours_to_deadline` (el reloj) y `listing_renew_required` (las horas de la publicación). En
general, una renovación mueve `listing_renew_required(_count)`; una venta o una compra mueven
`balance`, `liquidity_*` y `recovery_*`; y los `decision_*` del POST son la decisión que tomaría la
vuelta siguiente.

### Veredicto

**No he construido el atajo ni `test_el_post_no_cambia_ninguna_decision`.** El atajo no cambiaría
ninguna decisión, pero **tampoco ahorraría**: la medición manda. Con la memoria del once, el POST
realista pasa de 92,0 s a 1,8 s **sin saltarse nada**, con la foto del POST entera y el V10.5 y el
V10.6 igual de servidos.

---

## Bloque 3: el observador, 244 s para decir que no hay nada

**No pide nada a la red.** Distingo:

| | qué | coste |
|---|---|---|
| **se pide** | nada nuevo: el tablón es el de la vuelta (`board_del_ciclo`, `autopilot.py:876`), el retrato de rivales viene cacheado (`:806`) y el estado de negociación sale del disco | ~0 |
| **se calcula** | `build_offer_decision_board`, que para **todas** las ofertas rehace liquidez, tablero estratégico, especulación y reroll (`offer_decision_engine.py:1289-1420`), y `calculate_intelligent_bids` | 36,0 de 36,6 s en el lab (98 %) son alineaciones: 22 `build_lineup`, 160 búsquedas |

Después **tira todo lo que no sea `MANAGER`** (`autopilot.py:1282`), y con cero ofertas de
managers no queda nada.

**No he puesto la salida temprana.** El observador devuelve también `competitive_portfolio` e
`intelligent_bids`, que se imprimen y van al log competitivo. Salir antes cambiaría esa salida, y
eso sí es dejar de mirar. Con la memoria del once, **el observador pasa de 36,6 s a 0,6 s** (0
búsquedas nuevas) y sin cambiar un campo.

**`build_cycle_acquisition_board`** (125 s en producción): en el laboratorio da **62 objetivos**,
así que no contesta siempre lo mismo. Aquí sí hay trabajo obligatorio: el tablón se pide en esta
etapa (unas 12 peticiones, `load_rival_intelligence`) y el pronóstico de FF se refresca por TTL.
Lo calculado es 87 % alineaciones: de 17,6 s a 3,7 s con la memoria.

---

## Bloque 4: las peticiones

### Los dos logins, por qué

1. `cliente_del_ciclo()` (`client.py:34-36`): el de la vuelta. Un login y un `/account`.
2. **`BiwengerWriteClient.__init__`** (`write_client.py:25-37`) **construye su propio**
   `BiwengerClient` y hace otro login, `get_account()`, y luego `select_league()`, que **vuelve a
   pedir `/account`** (`client.py:159`). **La segunda respuesta de `/account` es la misma que la
   primera, pedida en la línea siguiente.**

Eso da exactamente 2 logins y 3 `/account`. Se podría reutilizar la sesión del ciclo: el cliente
del ciclo ya guarda `self.account`, y de ahí sale el `X-Version`. **No lo he hecho**: es el camino
de escritura, no se puede probar sin escribir, y ahorra 3 peticiones de ~21. No es el cuello de
botella.

### Las 12 repetidas (reconstruidas desde el código; no he leído el log)

En una vuelta de renovación hay **tres fotos**: la PRE, la relectura antes de escribir
(`autopilot_executor.py:1353`, `refresh_snapshot_for_write_revalidation`) y la POST. Cada foto pide
`/user` dos veces (la alineación y la plantilla, con `fields` distintos) y `/market` una.

| | repetidas | ¿misma respuesta dos veces? |
|---|---:|---|
| `POST /auth/login` | 1 | **sí**, evitable: la sesión del escritor |
| `GET /account` | 2 | **sí**, evitables: las dos del escritor |
| `GET /user` | 5 | no. 1 es la segunda consulta de la foto PRE, con otros `fields` (se podrían juntar en una, pero no es la misma respuesta). 4 son de la relectura y del POST |
| `GET /market` | 2 | no: la relectura y el POST |
| sin atribuir | 2 | ver abajo |

- **Evitables, misma respuesta pedida dos veces: 3.**
- **Inevitables mientras se mantenga la política** («leer antes de escribir» y «refrescar después»):
  6 (relectura + POST).
- **1** de la misma foto, con otra consulta.
- **2 sin atribuir sin el log.** Hay un candidato con la línea: **el V10.7 vuelve a colectar el
  tablón a pelo** (`dynamic_counteroffer_repricing_v107.py:1196`, `collect_board_history()` sin
  cliente), el mismo patrón que se arregló el 07/09 en el observador. Reutiliza la sesión, así que
  no hace login, pero pide otra vez el tablón y las finanzas. Eso cuadraría con 2. **Un número que
  encaja no es una causa** (doctrina 95).

---

## Cuánto tarda la vuelta después

Tus números del reparto **suman 60 minutos, no 78**: 12 + 24 + 19 + 5. **Faltan 18 minutos sin
atribuir.** El sospechoso con la línea es la cola del V10 que va tras `run_cycle`:

- **el V10.7 hace 370 búsquedas del once** (laboratorio). Son las de un `build_global_decision`
  entero, porque rehace `build_offer_decision_board` y la solvencia sin pasar por la caché de
  decisión;
- **el V10.6 hace 56**;
- y el POST sale a unos 3 s por búsqueda con 22 fichas, según tus 1.070 s / 363 búsquedas. A ese
  precio, 370 búsquedas son unos 18 min.

**Encaja, y precisamente por eso no lo doy por causa.** Hay que leer el log de una vuelta.

### Extrapolación a producción (interruptor ENCENDIDO; hoy está apagado)

Cada etapa de producción del encargo, multiplicada por lo que se ahorra esa misma etapa en el
laboratorio. **Es una estimación**: n = 1, con plantilla de 19 y no de 22, y en otra máquina.

| tramo | hoy | con la memoria | cómo |
|---|---:|---:|---|
| montaje (checkout + pip + node + verja) | ~12 min | ~12 min | no se toca |
| análisis 1 | 24,2 min | **~2 min** | 125 × 0,21 + 1.071 × 0,08 + 11 × 0,02 + 245 × 0,015 ≈ 117 s |
| escritura + POST | ~19 min | **~1 min** | POST × 0,02 ≈ 22 s, + la relectura, la escritura y las fotos por red |
| los 18 min sin atribuir | 18 min | **~3 min** si son el V10.7 (× 0,16); 18 si no lo son | sin medir en producción |
| dashboard + Cloudflare + git | ~5 min | ~3 min | el panel × 0,4-0,5; Cloudflare y git no cambian |
| **la vuelta** | **~78 min** | **~21 min**, o **~36** si los 18 min no son alineaciones | |

**Por debajo de 35 minutos si los 18 sin atribuir son el V10.7. Si no lo son, en el límite.** La
primera vuelta con el interruptor lo dirá, con la línea `El once, una vez: …`.

### Lo que queda irreducible

- **El montaje, ~720 s**, de ellos ~384 s la verja en el runner (tu dato del 22/09). No se toca en
  este encargo: no se toca el YAML.
- **Las búsquedas distintas.** Son 48 por vuelta en el laboratorio, 143 en el proceso del panel y
  0 nuevas en el POST. Con 22 fichas, a ~3 s cada una (extrapolado de tus 1.070 s / 363), **unos
  140 s en el análisis**. Bajar de ahí es cambiar la búsqueda (poda), y eso puede cambiar el
  desempate. No lo he hecho: es otro encargo.
- **La red**: las ~21 peticiones de la vuelta, más el tablón que colectan el dashboard y el V10.7.
  Son segundos, no minutos.
- **Un riesgo sobre el ahorro, no sobre la corrección**: la clave lleva todos los campos del
  jugador, incluido `external_lineup.age_hours`. En el laboratorio es estable dentro del proceso
  (el POST no añade ninguna búsqueda). Si en producción cambiase entre llamadas, se acertaría
  menos, y la decisión seguiría siendo la misma. Lo dirá la línea del log.

---

## El paso 0

```
EL PASO 0 HA TARDADO 211 s (3.5 min).
PASADO. Quedan probados 30 interruptores, apuntados en config/paso_0.json.
```

Uno más que ayer: `BORDALAS_EL_ONCE_UNA_VEZ`. **No se enciende en el YAML**: eso es tuyo.
`config/paso_0.json` va en el commit del informe.

---

## Lo que no he hecho, y por qué

| no hecho | por qué |
|---|---|
| **Encender `BORDALAS_EL_ONCE_UNA_VEZ`** | prohibido. Para encenderlo: `BORDALAS_EL_ONCE_UNA_VEZ: "1"` en el `env` del job, con este `paso_0.json`. Llega a los tres pasos (verja, ciclo y panel) |
| **El atajo del POST y `test_el_post_no_cambia_ninguna_decision`** | la medición dice que el cálculo del POST lo reutilizan el V10.5 y el V10.6: el atajo movería 18 min, no los quitaría |
| **Salida temprana del observador** | cambiaría `competitive_portfolio` e `intelligent_bids`, que se imprimen y se registran. Con la memoria cuesta 0,6 s |
| **Que el escritor reutilice la sesión del ciclo** | es el camino de escritura y no se prueba sin escribir. Son 3 peticiones |
| **Quitar la segunda colecta del tablón del V10.7** | apuntado con la línea. Es la cola de escritura V10.7 y merece su propio encargo |
| **Podar la búsqueda del once** | es lo único que baja las 48 búsquedas distintas, pero toca el desempate |
| **Leer el log de producción** | no hay `gh` en esta máquina |
| **Tocar el workflow, el `concurrency`, los números prohibidos o los interruptores** | prohibido; no se han tocado |
| **Empujar** | tú empujas. `git pull --no-rebase` antes |

## Apuntado, sin tocar

- **`marcador.py:2291-2293`**: el orden de `faltaron` y `sobraron` depende de la semilla de hash del
  proceso cuando hay empate a puntos. Es un orden inestable en la pantalla, no una decisión. Se
  arregla con un desempate por id en el `sort`.
- **El V10.7 colecta el tablón por segunda vez** (`dynamic_counteroffer_repricing_v107.py:1196`).
- Lo que traía el encargo: Ceballos en OBSERVACIÓN, `BORDALAS_SOLVENCIA_POR_SU_PLAZO` apagado, y
  el libro de la divergencia (10.894 predicciones apuntadas, 7.070 cerradas) sin puntuar. Sin
  tocar.
