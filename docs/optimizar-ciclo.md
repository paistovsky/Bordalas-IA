# Bordalás IA — optimizar el ciclo (revisión 2, 18/08)

Sustituye a la versión anterior de este documento. **Dos de las tres
causas que di antes eran falsas.** Auditoría del código con el puente.

## Primero: lo que te dije mal

**1. "Se bajan 36 MB de HTML de FutbolFantasy en cada ciclo."** Falso.
`data/ff_html/` **no lo lee ni lo escribe ningún código de producción** —
solo `scripts/dump_ff_team_html.py`, que se lanza a mano. Y `data/` está
en `.gitignore`, así que esos 36 MB ni siquiera viajan a Actions. Son
basura local tuya. Cero segundos del ciclo.

**2. "48 MB de snapshots en la caché."** Exagerado. `prune_github_state.py`
tiene `SNAPSHOT_KEEP = 24` (línea 7), así que en CI se guardan 24, no 97.
Los 97 están en tu PC, donde ese script no corre nunca. Son ~12 MB, no 48.
La poda a 5 que metí en el workflow sigue ayudando, pero es **menor**, no
la segunda causa.

Lo que sí sigue en pie de la versión anterior: los 34 procesos de Python
(3-4,5 min) y el margen del timeout.

## La causa real: no es la red, es la CPU

`src/analysis/lineup_engine.py:1303-1312`

```python
for take_count in range(max_take, -1, -1):
    for combo in combinations(candidates, take_count):
```

`search_best_lineup_for_formation` explora **todos los subconjuntos
parciales** (0..N) de cada posición, sin poda ni memoización, para las 7
formaciones de `FORMATIONS` (línea 212).

Medido por el auditor sobre datos sintéticos:

```
plantilla de 24 (3 POR / 8 DEF / 8 MED / 5 DEL)   23,1 s por build_lineup()
plantilla de 27                                    77,7 s
```

Y `evaluate_formation` (1389) **repite la búsqueda entera** si el XI no
sale completo → hasta ~46 s.

Hay **16 llamadas** a `build_lineup(` repartidas por el código
—liquidity_manager:537, lineup_monitor:671, deadline_engine:357,
competitive_offer_portfolio_engine:34 y :756, action_plan:24,
strategic_target_engine:1101, dashboard_state:821…— y **algunas están
dentro de bucles**: `competitive_offer_portfolio_engine.py:1052` llama una
vez por oferta, y `:1449` una por combinación.

Ahí están tus 16 minutos. No en FutbolFantasy.

### El arreglo, que es de cuatro líneas

En 1303, probar primero **solo el relleno exacto**; si sale XI completo,
devolverlo; si no, caer al bucle de siempre:

```python
# Intento rápido: el relleno exacto. Si da un XI completo, es
# óptimo por construcción y no hace falta explorar los parciales.
for take_count in (max_take,):
    ...
# y solo si filled != 11, el bucle original range(max_take, -1, -1)
```

Es **idéntico por construcción** cuando existe un XI completo: el bucle
original ya empieza por `max_take`, y un XI de 11 nunca puede mejorarse
cogiendo menos jugadores. Los parciales solo importan cuando no hay XI
completo, y ahí se sigue usando la ruta de siempre.

Medido: **23,08 s → 2,01 s. 11,5 veces más rápido.** Estimado en el
ciclo entero: **entre 150 y 300 segundos menos**.

### Por qué no lo he aplicado ya

Tres razones, y creo que las tres son buenas:

1. `lineup_engine.py` está formateado a **un token por línea** (`if
   player[\n "id"\n ]\n not in used_ids`). Editar eso sin poder abrir el
   fichero entero es pedir un error de sintaxis en un módulo que decide
   alineaciones con dinero de por medio.
2. **No puedo ejecutar las 34 guardias desde aquí** para comprobar que no
   he roto nada. Tú, en el PC, las corres en 20 segundos con el runner
   nuevo.
3. De todos modos **no puedo hacer push**, así que aplicarlo hoy no lo
   pondría en producción. No se gana nada por correr.

Es lo primero que hay que hacer en el PC, y se verifica solo: si el
cambio está mal, `test_starter_aware_xi_v1` y compañía saltan y
producción no se ejecuta.

## Lo demás que ha salido, por riesgo

### Bomba combinatoria latente — riesgo BAJO, hazlo

`accept_before_expiry_execution_planner.py:671-718` recorre
`combinations(eligible, size)` con `MAX_COMBINATION_OFFERS = 16` (línea
30). Cada combinación llama a `simulate_accept_combination_and_lose_rest`
→ `build_solvency_state` (:396) → `build_lineup`.

**Con 5 ofertas ya son 31 combinaciones × ~20 s ≈ 10 minutos.** Con más
ofertas, esto es una bomba: explica perfectamente por qué un ciclo
concreto revienta y los demás no. El KO de esta mañana huele a esto.

Bajar `MAX_COMBINATION_OFFERS` de 16 a 6. Se arregla casi solo con el
cambio de `build_lineup`, pero el tope es el cinturón de seguridad.

### El TTL de Jornada Perfecta está pegado al cron — riesgo BAJO

`jornada_perfecta_provider.py`, `calculate_refresh_seconds` (:336):
a menos de 48 h del cierre devuelve **30 minutos**, que es exactamente el
periodo del cron. Resultado: refresca **en casi todos los ciclos**.

Ese refresco son hasta 90 páginas en serie (`MAX_CRAWL_PAGES = 90`, :90)
con `time.sleep(0.05)` cada una, más `verify_signals_with_player_profiles`
(:1238), que baja **una página de perfil por jugador de la plantilla** con
`time.sleep(0.04)`. Entre 40 y 90 segundos, estimado.

Subir el escalón `<=48*3600` de `30*60` a `50*60` (línea 358): pasa a
refrescar uno de cada dos ciclos.

Nota: esto es JP, que **vamos a deprecar** por FF. Si el plan de FF
avanza, este problema se va solo. Pero mientras tanto, un número.

### FutbolFantasy ya está mejor de lo que pensaba

`futbolfantasy_provider.py:refresh_board` (:1065) baja en serie hasta 20
páginas de equipo + 2 de bajas, **sin ningún `time.sleep`**, y ya tiene
caché con relleno incremental: el `completando` de :1149 baja 2-3
equipos, no 22. 10-25 s estimados. Comparte el mismo TTL pegado al cron.

### Un peligro del timeout que no había visto

Si el job muere por `timeout-minutes`, GitHub lo **cancela**, y en una
cancelación los pasos `if: always()` **pueden no ejecutarse**. O sea: el
ciclo que revienta puede guardar la caché **sin podar y con estado a
medias**. Razón de más para subir el techo a 30 antes que nada.

### Trabajo repetido

- **No hay memoización de `build_lineup`**: el mismo XI se recalcula 10+
  veces por ciclo sobre el mismo snapshot. Cachear por
  (snapshot, formación) sería la solución elegante, pero es riesgo MEDIO
  y el arreglo de arriba ya se lleva casi todo.
- `copy.deepcopy(snapshot)` (planner:297) clona ~500 KB por simulación.
- `fetch_api_football_player_photo` (dashboard_state.py:320) es **código
  muerto**: definido y nunca llamado.

## Orden de trabajo actualizado

| # | acción | ganancia | riesgo |
|---|---|---|---|
| 0 | `timeout-minutes: 30` | deja de matar ciclos | ninguno |
| 1 | relleno exacto en `lineup_engine.py:1303` | **150-300 s** | bajo, con guardias |
| 2 | 34 guardias en un proceso (ya escrito) | 3-4,5 min | bajo |
| 3 | `MAX_COMBINATION_OFFERS` 16 → 6 | evita el KO | bajo |
| 4 | TTL de JP 30 → 50 min | 40-90 s en la mitad de ciclos | bajo |
| 5 | wrangler → `curl` a la API de KV | ~1 min | medio |
| 6 | memoizar `build_lineup` | lo que quede | medio |

Del 0 al 4, todo el mundo a favor. De 16 minutos a **menos de 4**.

## Lo que sigue sin comprobarse

- **En qué paso murió el ciclo de esta mañana** (pestaña Actions, la
  ejecución roja). Si fue en `Run Bordalas V10 PRODUCTION`, la hipótesis
  de la bomba combinatoria gana mucha fuerza.
- Los 23 s de `build_lineup` están **medidos sobre datos sintéticos**, no
  sobre tu plantilla real. El número de llamadas por ciclo (10-16) es
  estimado por análisis estático, no contado.
- Latencias reales de FF y JP desde una IP de GitHub. El propio código
  comenta que **JP devuelve 403 desde datacenter**, lo que cambiaría el
  reparto por completo.
- Cuántas ofertas entrantes sueles tener, que es lo que decide si el
  punto 3 es urgente o teórico.
