# INFORME — PUJAR VA EL PENÚLTIMO

**Fecha:** 2026-09-22
**Rama:** `medir/quien-se-queda-la-escritura`, desde `main`
**Commit:** `0d95dbe`
**Veredicto, corrido por mí:** paso 0 (los 23) **OK, exit 0** · verja **sin** el
interruptor **173/173 verde, exit 0** · verja **con** el interruptor **173/173 verde,
exit 0**. Con `data/` restaurado antes de cada una y después de la última.
**No se ha empujado. No se ha encendido nada. No se ha cambiado ninguna prioridad.**

---

## **TU ALARMA ES FALSA. Y no por poco.**

Lo digo en la primera línea porque me lo pediste. Dos medidas independientes, y una
tercera razón estructural que las explica:

1. **La subasta del reset no compite por la escritura.** Corre *antes* de la puerta y no
   consume el cupo. Medido: **hasta cuatro escrituras en una sola vuelta.**
2. **`BUY_SPECULATION` —la otra puja, la que sí compite a 400— no entra en la cola
   nunca.** Reconstruidas nueve vueltas: aparece **cero** veces.
3. **De 281 vueltas, 16 con puja y 5 con otra escritura. Vueltas con las dos cosas:
   cero.** La puja nunca coincidió con un trámite, ni mucho menos perdió contra él.

Pero hay un hallazgo debajo que sí importa, y es peor que el que buscabas: **la puja no
pierde la escritura porque no llega a pedirla.** El tablero da `biddable = 0`.

---

## BLOQUE 1 — LA TABLA ENTERA

### Las que consumen la escritura: son siete, no seis

Sacadas del árbol, no de la memoria: todo dict de `decision_orchestrator.py` con `action`
y `priority`, cruzado con las siete ramas que escriben en `autopilot_executor.py`.

```
accion                        prioridad   linea del candidato   linea del ejecutor
SAVE_LINEUP                   700-1000    orchestrator:1778     executor:2448
ACCEPT_CLUSTER_BEFORE_EXPIRY  665-1110    orchestrator:2339     executor: 792
REROLL_COMPUTER_OFFER         670         orchestrator:2238     executor:1057
ACCEPT_RECOVERY_OFFER         650         orchestrator:2112     executor: 603
LIST_FOR_LIQUIDITY            500-1100    orchestrator:1595     executor: 461
LIST_FOR_LIQUIDITY (manten.)  550         orchestrator:1963     executor: 461
RENEW_MARKET_LISTING          350 o 690   orchestrator:2489     executor:1316
BUY_SPECULATION               400         orchestrator:2900     executor:1594
```

Las otras quince entradas de `PRIORITY` —`MONITOR_*`, `WATCH_*`, `WAIT`, `SAFETY_MODE`,
`CONSIDER_PLAYER_EXIT`, `PUJA_BLOQUEADA`, `IDLE`— **no escriben**: son observadores.
`BUY_SPECULATION` aparece además en `orchestrator:703` con `executable: False`, que es una
copia de sombra.

### Y qué se pierde si cada una espera una vuelta

```
accion                        prioridad   que se pierde si espera UNA vuelta
--------------------------------------------------------------------------------
SAVE_LINEUP                   700-1000    los puntos de la jornada, si no llega al
                                          deadline. Irrecuperable y del once.
ACCEPT_CLUSTER_BEFORE_EXPIRY  665-1110    la oferta, si caduca en esta vuelta.
                                          Irrecuperable: la oferta no vuelve.
REROLL_COMPUTER_OFFER         670         la tirada de hoy. Vuelve mañana.
ACCEPT_RECOVERY_OFFER         650         normalmente NADA: la oferta vive hasta su
                                          caducidad, y la caducidad tiene su propia
                                          prioridad (665-1110).
LIST_FOR_LIQUIDITY            500-1100    una vuelta de escaparate de las 48 h.
                                          Recuperable.
RENEW_MARKET_LISTING (350)    350         NADA. La publicacion vive 48 h y sube sola
                                          a 690 a menos de 3 h del final.
RENEW_MARKET_LISTING (690)    690         la publicacion, si quedan <3 h.
BUY_SPECULATION               400         EL JUGADOR, si la vuelta era la ultima antes
                                          del reset. El reset se resuelve y no vuelve.
```

**La columna de la derecha te da la razón en el diagnóstico**: el número fijo de 400 no
puede decir «nada» y «el jugador» a la vez. Lo que la medición corrige es **a quién le
pasa**: no a la subasta del reset, que no está en esta tabla.

---

## BLOQUE 2 — CUÁNTAS VECES HA PERDIDO LA PUJA

### Primero, lo que NO se puede medir, y por qué

**`autopilot_log.jsonl` no va a git.** El que hay en el árbol tiene **n=50 vueltas del
12/08 al 17/08** y es mi copia local; el de producción vive sólo en la caché de Actions.
Y aunque estuviera, **no guarda las candidatas que perdieron**: sólo la ganadora
(`decision_action`, `decision_priority`, `decision_reason`). Doctrina 103: no es que no lo
sepamos, es que no lo apuntamos.

### Lo que sí se puede: reconstruir la cola

Volviendo a pasar `build_global_decision` por las fotos de plantilla que sí están en el
árbol. **n=9 vueltas** (12/08, 14/08, 16/08, 17/08, 10/09, 13/09, 19/09; las dos últimas
repetidas **con el tablero de adquisición**, que es como corre en producción).

```
foto                      gana                        la cola entera
2026-08-12 23:43   SAVE_LINEUP (760)          760 · 690 · 650 · [500] · [0]
2026-08-14 17:48   SAVE_LINEUP (760)          760 · 690 · 650 · [500] · [0]
2026-08-16 22:16   SAVE_LINEUP (760)          760 · 690 · 650 · [0]
2026-08-17 21:42   SAVE_LINEUP (760)          760 · 690 · 650 · [500] · [0]
2026-09-10 12:35   SAVE_LINEUP (760)          760 · 690 · 650 · [0]
2026-09-13 17:17   SAVE_LINEUP (760)          760 · 690 · 650 · [500] · [0]
2026-09-19 18:18   SAVE_LINEUP (760)          760 · 690 · 650 · 550 · [0]
  --- con el tablero, como en produccion ---
2026-09-19 18:18   SAVE_LINEUP (760)          760 · 690 · 650 · 550 · [0]
2026-09-13 17:17   RENEW_MARKET_LISTING (690) 690 · 650 · [500] · [0]
              (los [corchetes] no escriben)
```

**`BUY_SPECULATION` no aparece en ninguna.** Y no es un artefacto de mi llamada: en las
dos con tablero, `available=True` pero **`biddable=0` y `actionable=0`**. La puja no pierde
la escritura: **no la pide**.

Y la primera columna dice la otra mitad: **gana el once en ocho de nueve**, que es lo que
tú mismo dices que no se discute. La novena la gana renovar urgente (690) — un trámite
llevándose la vuelta, sí, pero sin ninguna puja a la que ganársela.

Un aviso sobre el plazo (doctrina 53): esto es **el código de hoy sobre fotos de
entonces**, no la decisión que se tomó aquel día. Sirve para saber si la puja entra en la
cola, no para reconstruir la historia.

### El cruce sobre los libros, que sí son de producción

`bitacora_del_saldo.jsonl` apunta una fila por vuelta: **n=281 vueltas, 15/09 a 22/09**
(antes del 15/09 no existe el libro). Cruzadas con las escrituras de
`bid_outcome_ledger`, `libro_del_carril`, `libro_de_renovaciones` y
`libro_del_escaparate`, agrupando cada escritura con su vuelta:

```
vueltas con al menos una PUJA ................... 16
vueltas con alguna escritura que NO es puja ......  5
vueltas con LAS DOS COSAS ....................... CERO
```

**Ni una sola coincidencia.** No hay ningún jugador que nombrar, porque no hay ningún caso.

### Y las vueltas dentro de la ventana

`libro_de_la_ventana.jsonl`: **n=21 vueltas con la ventana abierta, del 12/09 al 22/09.**

```
con puja ...................... 7
con renovacion ................ 0
con las dos en la misma vuelta  0
sin ninguna de las dos ........ 14
```

**De las 21 vueltas dentro de la ventana, en CERO la escritura se fue a otra cosa**, por la
sencilla razón de que en la ventana no se hizo ninguna otra escritura. Las 14 vacías lo
están porque `plan_del_reset` no propuso cesta, no porque nadie le quitara el turno.

---

## BLOQUE 3 — ¿DE QUIÉN ES EL LÍMITE?

### Es nuestro. Con la línea.

```
autopilot.py:4054   # Regla global: nunca permitimos una segunda escritura en el ciclo.
autopilot.py:4481   "REGLA DE SEGURIDAD:"
autopilot.py:4485   "No se ejecutara una segunda escritura en este ciclo."
```

Tenías razón: suena a nuestro porque lo es. No hay ninguna restricción de Biwenger detrás.

### ¿Cuál es el límite real? **No se sabe.**

Biwenger no lo publica y nosotros no lo hemos medido. Lo que hay es **un incidente**, en la
cabecera de `src/biwenger/peticiones.py`: un **429 a la cuenta entera** después de bajar
619 fichas de jugador en pocos minutos, con producción caída y el workflow desactivado a
mano. Y la aritmética de aquel momento: *«el ciclo normal hace 32 peticiones cada media
hora —1.536 al día— y de esas 12 son un duplicado exacto»*.

**Las «19 peticiones por vuelta» no las puedo confirmar**: `peticiones.py` cuenta por
endpoint, pero ese contador **no se publica en el estado** — no aparece en ninguna de las
tres fotos del árbol. Doctrina 103: no es que sean 19 o no, es que nadie las está mirando
donde se puedan leer.

*(Y un detalle que anoto y no persigo: ese docstring fecha el incidente el **27/09/2026**,
que todavía no ha pasado. O la fecha está mal escrita o el fichero se escribió con el
reloj movido — doctrina 89.)*

### Cómo cupieron tres pujas el 21/09

**Porque la subasta del reset no pasa por el cupo.** Está escrito al lado:

```
v10_full_autonomous_live.py:1228   "Va ANTES de la puerta de «una escritura por ciclo»,
                                    porque en la ventana del reset la regla es otra."
v10_full_autonomous_live.py:1235   "Y no consume `write_used`: una puja no es una compra."
v10_full_autonomous_live.py:1238   subasta = _pujar_en_el_reset(cycle)
```

`plan_del_reset` devuelve **una cesta**, y `_pujar_en_el_reset` hace **un `place_bid` por
cada elegido dentro del mismo bucle**. Tres pujas son tres escrituras HTTP y **cero**
consumo de cupo. `MAX_PUJAS_PRIMER_DIA = 3` es el único freno, y es suyo.

Y no es el único camino fuera del cupo. Son cuatro:

```
_pujar_en_el_reset       v10:1238   "no consume write_used"   la subasta del reset
_renovar_en_la_ventana   v10:1258   "tampoco consume"         renovar en la ventana
_correr_el_carril        v10:1380   "NO consume write_used"   el carril de la rendija
_llenar_el_escaparate    v10:1388   (despues de la accion)    publicar lo comprado
```

**Medido sobre los libros**, esto no es teoría:

```
18/09 02:46:54   4 escrituras en una vuelta   3 de la cesta + 1 del carril   EN VENTANA
18/09 02:51:34   3 escrituras en una vuelta   2 de la cesta + 1 del carril   EN VENTANA
19/09 11:22:52   2 escrituras en una vuelta
```

**El cupo de una escritura por vuelta gobierna una sola cosa: la acción del orquestador.**
Todo lo demás escribe al margen.

---

## BLOQUE 4 — LA PROPUESTA

### `BORDALAS_PUJAR_EN_LA_VENTANA` — apagado

`src/analysis/la_hora_de_pujar.py`. La prioridad de `BUY_SPECULATION` deja de ser fija:

```
dentro de la ventana   PRIORITY["LINEUP_LOW"] - 1            = 699
fuera de la ventana    PRIORITY["MARKET_LISTING_RENEW"] - 1  = 349
hoy, fija              PRIORITY["SPECULATION_BUY"]           = 400
```

**Los dos números salen de la tabla que ya existe** (doctrina 84):

- **699** es el mayor número que sigue estando por debajo de **todo lo que protege el
  once** (700 a 1000, más 1040, 1080 y 2000) y por encima de **todos los trámites** (690,
  680, 670, 665, 650, 550, 500).
- **349** es el mayor que sigue perdiendo contra renovar (350) y publicar (500).

Y fíjate en que el cambio **también baja**: hoy, con el 400 fijo, la puja le gana a
renovar a las cuatro de la tarde. Con esto, fuera de la ventana pierde. Esa mitad es tan
parte de tu tesis como la otra.

**El once gana siempre, dentro y fuera.** Hay guardia contra las doce prioridades del once,
en los dos instantes. Y tampoco adelanta al cierre de jornada (2000), la emergencia de
solvencia (1100), la barandilla dura (1040) ni las fases con el reloj encima (960-1010) —
no por concesión, sino porque en esas fases `plan_del_reset` ya se niega a pujar por su
cuenta: el reloj de solvencia manda antes que la ventana.

**La ventana no se redefine**: se le pregunta a `la_subasta.ventana_abierta`. Hay guardia
de que el módulo no escriba ni el 135 ni su producto como literal.

### El contrafactual: **no habría cambiado nada. Ni una vuelta.**

Y las dos mitades de la cuenta:

```
lo que se habria HECHO ........... nada
lo que se habria DEJADO de hacer . nada
```

Porque:

- **`BUY_SPECULATION` no aparece en ninguna de las nueve colas reconstruidas.** Si no está
  en la cola, subirle o bajarle la prioridad no mueve nada.
- **De las 21 vueltas dentro de la ventana, ninguna tuvo una renovación** a la que ganarle
  la escritura.
- Y para la otra dirección: como nunca gana, nunca dejaría de ganar. No hay ninguna
  publicación que se hubiera caducado por pujar.

**Y hay una limitación que tengo que decir**: de las **96 fotos de plantilla del árbol,
CERO caen dentro de la ventana de 135 minutos**. La ventana va de 04:45 a 07:00 de Madrid
y no guardamos fotos a esa hora. Así que la mitad «dentro de la ventana» del contrafactual
**no se puede medir sobre fotos** — sólo sobre el libro de la ventana, que dice lo que dice
(0 renovaciones) pero no guarda la cola de candidatos.

### Lo que esto significa, y es doctrina 99

**La prioridad es la SEGUNDA puerta.** La primera —`biddable = 0` en el tablero de
adquisición— está cerrada, y abrir la segunda no abre nada.

Y la primera puerta no está cerrada siempre: sobre las tres fotos de estado del árbol,

```
14/09 18:33   biddable=0   de 64 objetivos   (44 de mercado de rival)
18/09 16:16   biddable=2   de 54 objetivos   (34 de mercado de rival)
20/09 09:10   biddable=0   de 55 objetivos   (35 de mercado de rival)
```

**Se abre, pero poco**, y lo que más la cierra es `MERCADO_DE_RIVAL` —entre 34 y 44 de cada
foto—, que es una puerta que cerró el dueño y no toca este encargo.

### La guardia

**`test_en_la_ventana_la_puja_no_pierde_contra_un_tramite`** — con el interruptor puesto,
dentro de la ventana y con una puja y una renovación **no urgente** en la cola, gana la
puja. **Muerde si el caso está fuera de la ventana** —lo comprueba con
`ventana_abierta()`— y **también si el trámite del caso fuese la renovación urgente**, que
es otra cosa y tiene que seguir ganando. Los dos instantes salen de `VENTANA_MINUTOS`, no
escritos a mano: el 10/09 la ventana pasó de 15 a 135 minutos y unos números a mano se
quedaron dentro sin que nadie se enterara.

Ocho más: que fuera de la ventana pierda contra renovar y publicar; que **el once gane
siempre** (las doce prioridades, en los dos instantes); que apagado sea el 400 de siempre
—y encendido cambie en las dos direcciones, para que la primera no pase por casualidad—;
que los dos números salgan de la tabla, ejercitados contra todos los trámites; que sin
reloj no se suba nada; que la ventana no se redefina; que la forma no cambie con los datos;
y que el módulo no lea el mundo.

---

## LO QUE SE HA TOCADO

```
src/analysis/la_hora_de_pujar.py             NUEVO   la prioridad por el reloj
src/analysis/test_la_hora_de_pujar_v1.py     NUEVO   9 guardias
src/analysis/decision_orchestrator.py                el candidato lee el reloj
scripts/run_validation_gate.py                       la guardia en la verja
config/paso_0.json                                   lo reescribe el propio paso 0
```

---

## LO QUE NO SE HA HECHO, Y POR QUÉ

| | por qué |
|---|---|
| **Ni una escritura contra Biwenger** | lo prohíbe el encargo |
| **Ningún interruptor encendido** | apagado, la prioridad es el 400 de siempre, y hay guardia |
| **No se ha cambiado ninguna prioridad** | el bloque 4 **propone**: la tabla `PRIORITY` está intacta |
| **No se ha subido el cupo ni tocado el límite de peticiones** | lo prohíbe el encargo |
| **El workflow, intacto** · **la protección del once, intacta** | lo prohíbe el encargo |
| **No se ha tocado** `MAX_SINGLE_SPECULATION_PERCENT`, `MAX_SAFE_DEBT`, el suelo de cobro, `MIN_WIN_PROBABILITY`, `MAX_PROJECTED_DAILY_RATE`, `PUEDEN_ENCERRARLO`, `PRIMA_MAXIMA_DE_PUJA`, `VENTANA_MINUTOS` | lo prohíbe el encargo |
| **No se ha empujado** | «Tú no empujas» |
| **No se ha medido la cola de candidatos de una vuelta REAL dentro de la ventana** | no hay ninguna foto de plantilla a esa hora, de las 96 que hay. Hace falta guardar una foto en la ventana, o apuntar la cola de candidatos en el log |
| **No se ha hecho que el `autopilot_log` guarde las candidatas que pierden** | es lo que haría medible este encargo sin reconstruir nada, y es un cambio de lo que se apunta en producción. **Es lo que yo haría primero** |
| **No se ha tocado `biddable=0`** | es la primera puerta y el cuello de verdad, pero lo que más la cierra es `MERCADO_DE_RIVAL`, que es decisión tuya |
| **No se ha medido el modelo de las renovaciones** | ver abajo |

---

## LAS TRES QUE ARRASTRAMOS

**1. `arreglo/la-puja-que-vuelve` sigue sin fusionar** (doctrina 108).
`BORDALAS_SIN_REVENTA` y `BORDALAS_CUPO_POR_VENTANA` no existen en `main`, así que tampoco
en esta rama. Lo mismo `arreglo/sacar-de-la-sombra`, de hace un rato.

**2. `test_el_ciclo_publica_v1` sale a la red y escribe en cinco libros.** Confirmado otra
vez hoy: ensució `marcador.json`, `libro_de_publicacion.jsonl`, `libro_en_la_sombra.jsonl`,
`bitacora_del_saldo.jsonl` y `board_events.json` en **cada una de las tres** corridas de la
verja. Restauré `data/` antes de cada veredicto y después del último.

**3. El modelo de las renovaciones, y por qué toca de lleno este encargo.** No lo he
medido, y tienes razón en que es la palanca. Si renovar antes de que caduque no produce
nada, entonces **cada `RENEW_MARKET_LISTING` de prioridad 350 es una escritura tirada** —y
son las que ganaron ocho de las nueve vueltas reconstruidas después del once. Lo que hace
falta para medirlo está en el árbol: `libro_de_publicacion.jsonl` tiene las fechas de
primera publicación (n=45) y `censo_de_ofertas.jsonl` las ofertas recibidas. **Cruzarlos
diría si una renovación adelanta una sola oferta.** No lo he hecho porque no estaba en el
encargo y porque merece el suyo.
