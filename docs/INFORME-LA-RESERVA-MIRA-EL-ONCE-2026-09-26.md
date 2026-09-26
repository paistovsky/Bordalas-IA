# INFORME — LA RESERVA MIRA EL ONCE (B + C)

**Fecha:** 26/09/2026 · **Rama:** `arreglo/la-reserva-mira-el-once`, desde `origin/main` (`dc6b91bc`)
**Interruptor:** `BORDALAS_LA_RESERVA_MIRA_EL_ONCE`, **apagado**. El YAML no se ha tocado.
**Verja:** 185/185 en verde con los 5 interruptores de producción, árbol quieto (`verja-la-reserva.txt`).
**Paso 0:** PASADO con 31 interruptores puestos a la vez, 159 s (`paso0-la-reserva.txt`, `config/paso_0.json`).

---

## Veredicto del bloque 0: B no es cosmética, sigue adelante

**En 4 de 5 episodios con déficit, la reserva metió a un titular teniendo ofertas de suplentes
que tapaban la deuda.** Pero **anoche no**: anoche hacía falta un titular sí o sí.

### 1. Anoche: no se podía tapar sin un titular

Fuente: `censo_de_ofertas.jsonl` (una fila por tanda del Computer, con quién es titular) y
`bitacora_del_saldo.jsonl`. n = 1 noche.

```
deuda a las 00:12 del 26/09                      7.005.920
ofertas de suplentes vivas esa noche             4.656.700
    Carreras    1.255.900   caducaba a las 07:00 del 26/09
    Yeray       1.385.800   \
    Maffeo      1.589.400    |  tanda del 25/09: caducaban el 27/09
    Van Oevelen   238.300    |
    Guliashvili   187.300   /
falta, como mínimo, de un titular                2.349.220
```

**Con la tanda que caducaba esa noche, solo 1.255.900 eran de suplentes.** El resto de esa
tanda eran titulares: Yamal (protegido), Rubén García, Olasagasti, Jutglà y Jonny.

*Salvedad:* la marca de titular es la del censo de las 02:11, ya sin Rubén. Si con Rubén
dentro alguno de esos cuatro suplentes era titular, había aún menos banquillo, no más.

**Lo que B habría cambiado anoche es cuál de los titulares salía, no si salía uno.** No lo
puedo decir: no hay foto de producción de esa noche con los números del once.

### 2. Sobre todas las fotos: 4 de 5 episodios

Reproduje la reserva con el código de hoy sobre las **96 fotos locales**, con el reloj fijado a
la hora de cada foto (script de solo lectura, en el scratchpad). 55 fotos con déficit, que son
**5 episodios distintos** (las fotos de un mismo día repiten saldo y ofertas):

| Episodio | Fotos | Necesita | Reservó a un titular | Suplentes elegibles | ¿Evitable? |
|---|---|---|---|---|---|
| 12/08 | 18 | 5.151.032 | Ximo Navarro 1.175.100 | 9.894.500 | **sí** |
| 13/08 | 19 | 5.151.032 | Ximo Navarro 1.180.200 | 9.303.600 | **sí** |
| 14/08 | 9 | 5.151.032 | Ximo Navarro 1.180.200 | 8.808.900 | **sí** |
| 17/08 | 5 | 264.032 | — | 3.340.900 | no hizo falta |
| 13/09 | 4 | 1.799.834 | Mangala 2.498.100 | 3.296.400 | **sí** |

**Días sin dato:** no hay fotos locales del 15-16/08, del 18/08 al 12/09 (salvo el 13/09), ni
del 20/09 en adelante. Las de producción no se guardan: solo el censo y la bitácora.

**Ojo con lo que mide esto:** es lo que **el código de hoy** habría reservado sobre esas fotos,
no lo que reservó el de agosto. Mide el criterio, no la historia.

---

## B: dónde se elige y qué cambia

### Dónde se elige hoy (dos pasos, no uno)

1. **La cartera** (`safe_debt_portfolio_engine.py:538-543`) junta el nivel A (sin tocar el
   once) con el B (vendiendo titulares con el once completo) en `tier_b`, y se queda con la
   combinación **de más dinero**. Los titulares vendidos solo desempatan (`:277-287`). La
   cartera se aplica **siempre**: nunca devuelve `None`.
2. **La reserva** (`solvency_engine.py`, `reservation_key`) ordena lo de la cartera por
   franquicia, estratégica, prima e importe, y guarda hasta cubrir la deuda más 500.000.

Ninguno de los dos pregunta quién juega.

### Qué cambia con el interruptor

**Solo el orden del paso 2.** Primero va la oferta que menos once cuesta por euro, contando lo
ya elegido: dos laterales no cuestan la suma de lo que cuesta cada uno. A igual coste, el orden
de siempre. La cartera no se toca.

Medido con el interruptor sobre los mismos 5 episodios:

```
12/08   Ximo Navarro (T)  ->  Álvaro Fidalgo          1.020.800
13/08   Ximo Navarro (T)  ->  Álvaro Fidalgo          1.020.800
14/08   Ximo Navarro (T)  ->  Etta Eyong              4.102.300
17/08   Bayindir          ->  Bayindir                (igual)
13/09   Mangala (T)       ->  Zubeldia                1.847.000   y vende menos
```

**Tiempo:** no se nota. `build_solvency_state` tardó entre 0,96 y 1,66 s encendido y entre 1,30
y 2,28 s apagado (n = 5, en el portátil). Pero la corrida encendida iba siempre segunda, con la
caché caliente, así que esto **no** demuestra que sea más rápida: solo que no es más lenta.

### La unidad: y aquí no cumplo del todo el encargo

La **forma** es la misma que la de la cola de fichajes: rehacer el once entero, con todas las
formaciones, y quedarse con la diferencia. En la cola es cuánto suma el candidato dentro; aquí,
cuánto pierde el once con el jugador fuera. Las dos dan cero a quien no entra.

**El número de entrada no es el mismo.** La cola usa puntos de temporada estimados
(`estimate_season_points`). La reserva solo tiene el `lineup_score` con el que la cartera
proyecta el once. Medido en la foto del 13/09, eso es ~1.000.000 × el valor semanal esperado
(Rubén García 593.771, Mangala 570.200). No son puntos.

Por eso:

- **se ordena** con ese número. Dividir por euro no cambia el orden al cambiar la escala, y es
  el mismo número con el que Pepe elige a quién alinea;
- **se enseña** como **porcentaje del once**, que no depende de la escala y es la medida con la
  que la cartera ya corta (`lineup_score_loss_percent`, 5 %);
- **se elige** el once con `lineup_score` pero **se valora** sin el bono del Dios
  (`lineup_score_sporting`). Si no, los 10 M de bono de Yamal abaratan en proporción a todos
  los demás, que es lo que `lineup_engine` ya advierte.

**Para que vendedor y comprador hablen literalmente el mismo número** habría que meter
`estimate_season_points` en la plantilla de la cartera. No lo he hecho: toca la valoración, y
eso lleva su propio encargo.

### Cómo se cuentan los puntos de un suplente: cero, y es lo justo

En esta liga solo puntúan once (`lineupReserves: false`, sin cambios automáticos). Si sale un
suplente, el once de después es el mismo que el de antes. **Pierde cero porque rehacer el once
da cero, no porque lleve una etiqueta.**

Un titular no pierde "sus puntos": pierde **sus puntos menos los del que entra por él**. Ximo
Navarro sale al 0,0 % porque tenía un recambio casi igual; Mangala, al 4,5 %.

**Lo que esta cuenta no ve es el seguro:** un suplente cubre lesiones y sanciones, y eso vale
algo que hoy no está medido. No le invento un número. La posición mínima la sigue guardando el
guardarraíl posicional: sus intocables no entran en ninguna combinación de la cartera ni en la
alternativa del aviso.

### El guardarraíl del último de cada posición: sigue haciendo falta

`offers_to_collect` (`decision_orchestrator.py:298-309`) no solo cobra reservas: cobra todo lo
`actionable`, que incluye `ACCEPT_NOW` por buen precio, `REROLL_CANDIDATE` y ofertas de
managers que nunca pasan por la cartera. Además, la reserva se valida contra el once cuando se
hace, y el cobro llega horas después, con el once quizá cambiado. **Se queda como está.**

### La regla del déficit

Sin tocar (`la_regla_del_deficit.py:97-198`).

---

## C: el aviso

### Cambio respecto al encargo: salta cuando queda reservada, no al entrar en la ventana

**Entrar en la ventana de 6 horas y vender son el mismo ciclo.** A 6 horas o menos, el motor de
reroll pasa la oferta a `ACCEPT_BEFORE_EXPIRY` y el orquestador la cobra en esa misma vuelta.
Un aviso "al entrar en la ventana" habría llegado a la 01:13, a la vez que la venta de Rubén.

Así que **el aviso salta en cuanto una oferta de un titular queda reservada**, y dice cuántas
horas faltan para que entre en la ventana, por caducidad o por el plazo de la jornada, lo que
llegue antes. **Anoche habría salido como tarde a las 21:12, con cuatro horas por delante.**
Es lo que pedía el encargo ("cuando aún se puede hacer algo"), no lo que decía al pie de la letra.

### Los cuatro datos

Sale siempre, con o sin el interruptor, porque no decide nada. Queda en el estado de solvencia
(`ventas_de_titular`) y el resumen del ciclo lo imprime. Ejemplo real, de la foto del 13/09 con
el interruptor apagado:

```
VENTAS DE TITULAR RESERVADAS: 1
  VENTA DE TITULAR RESERVADA: Mangala por 2.498.100, cuesta el 4.5 % del once;
  entra en la ventana de cobro dentro de 40.3 h. Alternativa: Zubeldia + Diego Conde
  + Fortuño + Cepeda por 2.875.600, cuesta el 0.0 % del once.
```

La alternativa sale de las ofertas **no reservadas** y sin intocables. Si no juntan el dinero,
lo dice: *«Sin alternativa entera: lo no reservado junta X de Y»*.

### Qué canales existen ya, y cuál llega de madrugada a un móvil

| Canal | Qué es | ¿Llega solo al móvil? |
|---|---|---|
| Resumen del ciclo | log del run en GitHub Actions, con el bloque nuevo | **No**: hay que abrirlo |
| Artefacto `bordalas-live-diagnostics-<id>` | `autopilot_log`, `status.json`… | **No**, y dura 2 días |
| Panel (Cloudflare KV, `status.json`) | se actualiza en cada vuelta | **No**: hay que abrirlo. Y **el aviso no llega al panel**: `dashboard_state` no lee `ventas_de_titular` |
| Correo de GitHub Actions | lo manda GitHub | **Solo cuando el run FALLA.** Usarlo para avisar sería tumbar el ciclo |
| cron-job.org | el que dispara el latido | avisa si falla el disparo, no del contenido (no he mirado su configuración) |
| Commits de los libros a `main` | cada hora | GitHub no avisa de commits por defecto |

**Ninguno de los que hay lleva un aviso de contenido a un móvil de madrugada.** Tal como está,
C es un aviso que hay que ir a buscar. La diferencia con anoche es que saldría horas antes y con
la alternativa escrita, pero sigue siendo un tirón, no un empujón. **No he montado nada nuevo
(doctrina 84). Qué canal usar es decisión tuya.** Lo más barato con lo que hay: que el panel
enseñe `ventas_de_titular`, pero eso tampoco despierta a nadie.

---

## Bloque 3

### 7. ¿Se recalcula la deuda entre un cobro y el siguiente? Sí, en cada ciclo

`build_solvency_state` lee el saldo de la foto nueva (`solvency_engine.py:1420`). La deuda se
recalcula (`:368-369`, `:486-487`) y la reserva vuelve a dimensionarse desde cero en cada
vuelta. Lo que ya no hace falta deja de estar reservado y, por tanto, deja de cobrarse a 6 horas.

**Cuánto puede sobre-cobrar, por construcción:** el colchón de 500.000 (`SAFE_LIQUIDITY_BUFFER`)
más lo que se pase la última oferta reservada, porque se guarda hasta que la suma **llega o se
pasa** (`:569`). Con el interruptor, además, se tiende a vender lo justo: el 13/09 guardaba
1.847.000 para una necesidad de 1.799.834, en vez de 2.498.100.

**Lo de anoche no fue quedarse corto por un fallo:** solo se cobran las reservadas que caducan.
De esa tanda solo se podía cobrar a Rubén y a Carreras. Las demás reservas caducan el 27/09, y
el plazo es el 09/10.

### 8. Los 90.096 €: son dos cosas, y las dos están en los libros

```
-3.335.120   a las 04:54, tras vender a Carreras
-3.447.904   Blanco NO costo 3.288.000: la puja se subio a las 22:11 del 25/09
             (XI_UPGRADE) y se pago 3.447.904   (bid_outcome_ledger.json)
-----------
-6.783.024   a las 07:21, exacto
  +250.000   bonus "dailyStreak" (racha diaria), 07:22   (board_events.json)
-----------
-6.533.024   a las 08:11, exacto

   +250.000 - 159.904 (Blanco por encima de 3.288.000) = +90.096
```

**El libro cuadra al euro.** La cifra de −3.288.000 del resumen de la mañana era el primer
importe de la puja, no el que se pagó. Ya consta en el tablón de dónde sale el bonus. La
bitácora del saldo no lo apunta por separado: solo registra el saldo.

### 9. ¿Cuántas reservadas caducaron sin cobrar por quedarse sin turno? No se puede contar

**No lo sabemos, y no es por no haberlo preguntado (doctrina 103): no está apuntado.** Qué se
reserva en cada vuelta solo queda en `autopilot_log.jsonl`, que no va a git y cuyo artefacto
dura 2 días. `computer_offer_history.json` guarda rerolls, no qué pasó con cada oferta.

**Anoche (n = 1): cero.** Dato nuevo: **en la ventana no caben 6 turnos sino 5.** El latido va a
los :07 de 0 a 3 h y luego salta a 04:45 y 04:50. Anoche fueron 01:13 (Rubén), 02:11 (once),
03:11 (Carreras), 04:49 y 04:54. **Sobraron dos turnos.**

Para contarlo haría falta apuntar, por vuelta, las reservadas y qué pasó con ellas. No lo he
hecho: es un libro nuevo, y eso lo decides tú.

---

## El interruptor, para el YAML (no lo he tocado)

```yaml
      # Apagado. LA RESERVA DE SOLVENCIA GUARDA PRIMERO AL QUE NO JUEGA.
      #
      #   LO QUE PASABA. La reserva elegia que ofertas guardar para tapar la
      #   deuda por franquicia, estrategica, prima e importe: nada de eso
      #   pregunta quien juega. Lo reservado se cobra solo a 6 h de caducar.
      #   El 26/09 a la 01:13 se vendio asi a Ruben Garcia, titular.
      #
      #   LO QUE HACE. Solo cambia el ORDEN de la reserva: primero lo que
      #   menos once rehecho pierde por euro (cero para un suplente); a igual
      #   perdida, el orden de siempre. La cartera A/B, la regla del deficit,
      #   el guardarrail posicional y la ventana de 6 h NO se tocan.
      #
      #   MEDIDO reproduciendo la reserva sobre las 96 fotos locales (12/08-
      #   19/09), 5 episodios con deficit: en 4 metio a un titular teniendo
      #   suplentes que tapaban la deuda de sobra (Ximo Navarro x3, Mangala).
      #   Con el interruptor, los 4 pasan a suplentes, y el 13/09 vende menos
      #   (1.847.000 en vez de 2.498.100 para 1.799.834). La noche del 25/09
      #   NO lo habria evitado: habia 4.656.700 de suplentes para 7.005.920.
      #
      #   PASO 0 HECHO: 31 interruptores a la vez, en verde (26/09).
      #
      #   LO QUE NO ESTA MEDIDO Y HAY QUE VIGILAR:
      #     - El orden no mira la caducidad: puede preferir un suplente de la
      #       tanda nueva a un titular de la que caduca esta noche. Tapa la
      #       deuda un dia mas tarde. Con el plazo lejos no importa; cerca del
      #       plazo, la presion de jornada cobra lo reservado igualmente.
      #     - Un suplente cuesta cero porque no puntua; su valor como seguro
      #       ante lesiones no esta medido. La posicion minima la guarda el
      #       guardarrail, no esta cuenta.
      #     - El "valor del once" es el lineup_score de la cartera, no los
      #       puntos de temporada de la cola de fichajes: misma forma,
      #       distinta entrada.
      #     - En produccion, n=0: las fotos son de agosto y septiembre, con
      #       el codigo de hoy.
      BORDALAS_LA_RESERVA_MIRA_EL_ONCE: "1"
```

**Si decides encenderlo, `config/paso_0.json` ya va en esta rama con el interruptor probado.**

---

## Lo que cambió en el código

| Fichero | Qué |
|---|---|
| `src/analysis/la_reserva_mira_el_once.py` | **nuevo**: el orden por once perdido por euro y el aviso. Funciones puras, nunca lanza, sin reloj ni disco. El interruptor se lee al llamar. La ventana de 6 horas la toma del motor de reroll, no la copia |
| `src/analysis/solvency_engine.py` | la reserva recibe la cartera y, con el interruptor, ordena por once perdido; devuelve `orden`. `build_solvency_state` añade `ventas_de_titular` |
| `src/analysis/safe_debt_portfolio_engine.py` | devuelve `plantilla_del_once` e `intocables`; la plantilla lleva `lineup_score_sporting`. No cambia ninguna decisión suya |
| `src/autopilot.py` | el resumen del ciclo imprime `VENTAS DE TITULAR RESERVADAS` |
| `src/analysis/test_la_reserva_prefiere_al_que_no_juega_v1.py` | **guardia nueva**, 29 comprobaciones. Se vio ponerse roja rompiendo el módulo de dos maneras (3 y 8 rojas) |
| `scripts/run_validation_gate.py` | la guardia, en la verja |
| `config/paso_0.json` | el paso 0 de hoy, 31 interruptores |

## Lo que no hice, y por qué

- **No encendí el interruptor ni toqué el YAML.** Es tuyo.
- **No monté ningún canal de avisos** ni llevé el aviso al panel. Decisión tuya, con la tabla de
  arriba.
- **No igualé la unidad con la de la cola** (`estimate_season_points`): toca la valoración.
- **No conté las reservadas caducadas por falta de turno:** no está apuntado, y apuntarlo sería
  un libro nuevo.
- **No toqué** la regla del déficit, el Position Manager, la cuota de una escritura por ciclo, la
  ventana de 6 horas ni ninguna constante de la lista.
- **Ni una escritura contra Biwenger ni una llamada nueva a su API.** Todo sale de fotos y libros
  que ya estaban en el disco.
- **No empujé.**

## Aviso aparte: el `main` local no es el de producción

El `main` local tiene encima `9af14464` ("medir: Pepe compara mal antes de decidir"), sin
empujar. La rama `medir/comparar-bien` apunta a `e2438238`, no a `9af14464` como decía el
resumen de la mañana. **Esta rama sale de `origin/main`** para no arrastrar ese commit. No he
tocado ninguna de las dos.
