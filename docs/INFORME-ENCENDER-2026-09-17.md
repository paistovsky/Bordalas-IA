# Encender — informe

**Foto:** `diagnostico/status.json`, **`meta.generated_at` = 2026-09-17T07:30:55**, con
`encoding="utf-8"`.

**Rama:** `motor/encender`, rebasada sobre `origin/main` (12 commits de libros por
debajo, cero conflictos).
**Push:** NO. Esto va entero y lo empujas tú mirando.

---

## Lo primero, porque cambia el encargo

**Las ocho ramas ya estaban dentro.** No hay seis ramas que fusionar: son **una cadena
lineal**, y `carril/la-direccion` ya las contenía todas.

```
6273023  carril/el-de-un-dia          <- y debajo, ojeador/los-tres-arreglos
1aa5276  medir/la-plaza-y-el-cable       y medir/el-viaje-al-computer
c3d010a  motor/el-cable
1dbca2a  motor/la-lista-de-la-compra
8827131  medir/el-escaparate
20d0c95  motor/el-proposito
996d1b0  motor/el-carry
7d51f2e  carril/la-direccion
```

No ha habido merge, ni conflictos, ni nada que elegir. Solo un `rebase` sobre
`origin/main` que entró limpio: **nuestros 16 commits no tocan un solo fichero de
`data/`**, así que no chocan con lo que el ciclo escribe cada hora.

**`main` local tiene 2 commits sin publicar** («el ocho por ciento»). Los comprobé uno
a uno: **los cuatro ficheros son idénticos** a los que ya están en la cadena, así que
no se pierde nada. No hace falta hacer nada con ellos.

*Nota sobre `git pull --rebase`: no salí a la red, así que rebasé contra el
`origin/main` local, que es de hoy 07:31. **Antes de empujar hay que hacer el `pull
--rebase` de verdad**, porque el ciclo habrá escrito más libros desde entonces.*

---

## PARÉ DOS VECES. Esto es lo que no cuadraba.

### 1. El cable no tiene interruptor que valga

Comprobé las **once funciones públicas** de `el_cable.py` contra todo `src/`:

```
caja_realizable              <- NADIE en src/
presupuesto_con_el_cable     <- NADIE en src/
puja_permitida               <- NADIE en src/
tabla_de_fichajes            <- NADIE en src/
cuanto_desbloquea            <- NADIE en src/
cola_por_consecuencia        <- NADIE en src/
mayor_plantilla_jamas_vista  <- NADIE en src/
maximo_historico_de_fichas   <- NADIE en src/
```

Solo lo llaman `scripts/el_cable.py` y `scripts/la_lista_de_la_compra.py`, que son
medición. **`ENCENDIDO = True` ahí no habría cambiado absolutamente nada**: sería un
interruptor decorativo.

**Decisión tomada: no se toca.** Encenderlo de verdad es cablear las dos cajas dentro
del camino del presupuesto de fichar, y eso es un encargo, no una línea.

### 2. El guardarrail sí es una línea, pero hay seis

`validate_sale_set_con_titularidad` tampoco tenía ningún llamador en producción. Y los
seis sitios que llaman al viejo **no son la misma cosa**:

```
PROPONER a quién vender            LA SALIDA DE EMERGENCIA
  sale_order.py:519                  liquidity_manager.py:1072
  sale_order.py:623                  accept_before_expiry...py:691
  sale_intent.py:281
  roster_planner.py:102
```

**Decisión tomada: solo los cuatro de proponer.** La salida de emergencia se queda con
la regla de cuerpos, para que un freno del once no pueda dejar a Pepe sin forma de
pagar.

*Lo medí antes de preguntar: hoy Pepe está en **déficit de 373.984 €** y los tres
planes de solvencia vivos —A (Pablo Durán), B1 (Oriol Rey) y C (Fortuño, Paco Cortés,
Benavidez)— **pasan los dos guardarraíles**. Hoy no habría bloqueado nada ni siquiera
encendiéndolo en los seis. La decisión es para el día que sí.*

---

## Y UNA TERCERA COSA, QUE NO PREGUNTÉ PORQUE YA ESTABA DECIDIDA

### El bloque 4 estaba dentro y vivo. Lo he sacado.

Dijiste: «el bloque 4 de free_slots — **NO**. Se queda fuera hasta que `ROSTER_FILL`
tenga tope de prima». La cadena lo traía puesto y **funcionando**:

```
count_free_slots(auditoria, maximo_historico_de_fichas(auditoria))
   en acquisition_valuation.py:225   <- PRODUCCION
   en dashboard_state.py:4173        <- la pantalla
```

Y el número medido en el informe del cable:

```
ANTES   free_slots = 0    (contra la mayor de HOY, 20)
CON EL BLOQUE 4  = 4      (contra la mayor JAMÁS VISTA, 24)
```

Cinco líneas más abajo de ese número, en `acquisition_valuation.py:626`:

```python
if huecos > 0:
    ...
    como_relleno["route"] = "ROSTER_FILL"
```

> **Cuatro huecos abren `ROSTER_FILL`, y esa vía no tiene tope de prima.** Era
> exactamente lo que dijiste que no entraba.

**Lo he sacado de los dos sitios**, y de los dos para que no se descuadren: si lo
quitara solo del motor, la pantalla pintaría cuatro plazas que el motor no ve, que es
el descuadre que el cable vino a arreglar.

Lo que **no** he tocado es la función: `count_free_slots` sigue aceptando
`historical_max` con valor por defecto `None`. **Nadie se lo pasa**, así que se
comporta exactamente como antes. Dejarlo así conserva la medición y sus guardias; si
prefieres revertir también la firma, dilo y lo hago.

---

## BLOQUE 0 — Los ocho libros, comprobados de verdad

### 1. En la lista

Los ocho entraron en el commit de ayer y están en esta rama. `LIBROS` pasa de **16 a
24**.

### 2. Que se suben de verdad — **no que aparezcan en la lista**

Tenías razón en la distinción, así que lo probé ejecutando, en un **clon desechable**
para no tocar nada:

```
simulé la primera vuelta: producción escribe los ocho libros
luego corrí `python scripts/guardar_los_libros.py`

    Cambian 8 libro(s) respecto a git:
      data/autopilot/computer_offer_history.json
      data/intelligence/rejection_ledger.json
      data/intelligence/scout_accuracy_ledger.json
      data/intelligence/source_accuracy_ledger.json
      data/trading/libro_de_escaparate.jsonl
      data/trading/libro_de_la_ventana.jsonl
      data/trading/libro_de_salidas.jsonl
      data/trading/libro_de_viajes.jsonl
    Commit hecho.
```

**Los ocho, en un commit de verdad.** Y el contrafactual, con el `.gitignore` que
produccion tiene HOY:

```
TAPADO   data/trading/libro_de_viajes.jsonl
TAPADO   data/intelligence/scout_accuracy_ledger.json
TAPADO   data/intelligence/source_accuracy_ledger.json
TAPADO   data/trading/libro_de_salidas.jsonl
TAPADO   data/trading/libro_de_la_ventana.jsonl
TAPADO   data/trading/libro_de_escaparate.jsonl
TAPADO   data/intelligence/rejection_ledger.json
TAPADO   data/autopilot/computer_offer_history.json
```

Los ocho, tapados. **Esa es la prueba: antes no subían, ahora suben.**

### 3. Los otros: **son 25, no 31**

El «31» salía de 47 − 16. Pero de esos 31, **ocho eran libros** y ya están dentro. El
reparto de verdad de los 47 que el código escribe: **22 libros + 25 que no lo son**,
y **cero sin clasificar**.

```
data/autopilot/action_failure_backoff.json        la espera tras un fallo; perderla solo reintenta antes
data/autopilot/autopilot_log.jsonl                lo poda `prune_github_state`
data/autopilot/cache_biwenger.json                cache del reset
data/autopilot/competitive_observer_log.jsonl     lo poda `prune_github_state`
data/calendar/laliga_calendar.json                cache del calendario
data/dashboard_player_photo_cache.json            cache de fotos
data/external_status_cache.json                   cache de estado externo
data/ff_html/{}.html                              el HTML crudo de una petición
data/intelligence/archivo/{}.json                 el archivo del día, derivado de la foto
data/intelligence/futbolfantasy_board.json        cache de FF
data/intelligence/jornada_perfecta_lineups.json   cache de Jornada Perfecta
data/intelligence/jornada_perfecta_market.json    cache de Jornada Perfecta
data/intelligence/penalty_kickers.json            cache de penaltis
data/intelligence/press_report.json               cache de prensa
data/intelligence/scout_report.json               el informe de hoy
data/intelligence/starter_multisource_v112.json   consenso de titularidad, se rehace cada vuelta
data/intelligence/starter_multisource_v1124.json  consenso de titularidad, se rehace cada vuelta
data/league_center/laliga_standings.json          cache de LaLiga
data/lineup_monitor/state.json                    estado del vigilante
data/player_mapping_cache.json                    cache de nombres
data/rival_intelligence/board_latest_raw.json     el crudo de la última petición
data/rival_intelligence/profiles_cache.json       cache de perfiles
data/snapshot_{}.json                             una foto
data/trading/v10_full_autonomous_status.json      estado de la vuelta
data/trading/v10_production_status.json           estado de la vuelta
```

Los dos primeros merecen una línea de más: **se podan a propósito**.
`prune_github_state.py` los trunca después del ciclo y antes del guardado, así que
meterlos en la lista sería commitear la versión recortada — parecería un libro y sería
un recorte.

### Las dos guardias

```
test_todo_libro_escrito_esta_en_la_lista   corriendo en la verja
test_el_gitignore_no_tapa_un_libro         corriendo en la verja (renombrada como pediste)
```

Las dos fallan con la lista vacía. **La segunda es la que nos habría avisado hace un
mes**, y ahora está puesta.

---

## BLOQUE 1 — Los cuatro locales: archivados, no promovidos

Copiados a **`archivo/2026-09-17/`**, con un `LEEME.md` que explica qué son. **No son un
libro: producción no los lee y nadie los escribe.** Producción arranca los suyos
limpios.

### Y una corrección a mi propio número

Dije «821 líneas que no se pueden reconstruir». **Son 821 líneas de texto, no 821
registros.** Son JSON con sangría. Lo que hay dentro de verdad:

```
libro_de_renovaciones.jsonl      11 líneas   11 renovaciones del 10/09
pujas_bajo_precio.jsonl           1 línea     1 observación (Aubameyang)
scout_accuracy_ledger.json      172 líneas    8 predicciones, todas del 05/09,
                                              todas de prensa, todas sin resolver
source_accuracy_ledger.json     649 líneas    2 jornadas (17 y 16 jugadores),
                                              ninguna resuelta
```

**Total real: 11 renovaciones + 1 puja + 8 predicciones + 33 pronósticos.** El archivo
sigue mereciendo la pena, pero no es el tesoro que yo hice creer.

### Qué proporción parece de la verja

```
libro_de_renovaciones.jsonl     0 %   la verja no lo escribe (medido ejecutando la verja
pujas_bajo_precio.jsonl         0 %   entera con las escrituras interceptadas)
source_accuracy_ledger.json     0 %
scout_accuracy_ledger.json      ?     SÍ lo escribe `test_ojeador_informe_v1`
```

De los cuatro, **solo uno lo toca la verja**, y **no se puede separar línea a línea**:
las 8 predicciones son todas del 05/09, de prensa y sin resolver, y la guardia escribe
con esa misma forma. Se archiva entero y queda dicho.

### Y lo que de verdad se perdió, que no está en el archivo

> Te preocupaba que `scout_accuracy_ledger.json` fuera «el libro del que salen el 89 %,
> el 95 % y el 97 %». **No lo es, y me alegra decirlo.**
>
> El 89 % está medido **directamente sobre `price_history.json`** —30 días, 622
> jugadores, 13.073 pares— y el informe del 15/09 lo dice con esas palabras: «lo medí
> directamente sobre nuestra propia serie, **sin pasar por el ojeador**».
> `price_history.json` está en la lista y en git desde el 14/09. **Ninguna decisión de
> esta semana salió del libro que estaba escondido.**

Pero debajo hay algo peor, y ese sí es real:

```
el 15/09, el libro de PRODUCCIÓN tenía del orden de 16.000 predicciones
   (5.993 en `pending`, 2.760 en `flat`)
hoy, en git                                                        cero
```

Ese libro vivía **solo en la caché del runner** y nunca llegó a git. **No se puede
recuperar.** El libro local tenía 8 predicciones el 15/09 y sigue teniendo 8: en local
no se perdió nada; lo que se perdió fue lo de producción, y se perdió exactamente
porque `scout_accuracy_ledger.json` no estaba en la lista.

---

## BLOQUE 2 — El orden, no la puerta

```
ORDEN_ENCENDIDO = False
```

Construido en `src/analysis/la_direccion.py`, apagado, con su propio interruptor
separado del filtro.

### La prueba que pediste: **salen las mismas 37**

Sobre las **182 subastas** de producción:

```
subastas                    182  ->  182
PUJAS NUESTRAS               37  ->   37
mismos identificadores            True
mismas pujas, una a una           True
filas que cambian de sitio  182 de 182
```

**No se cae ninguna.** Y no es una casualidad del montaje: es un `sort`, no un
`filter`, y una ordenación es una permutación. Eso es lo que mide
`test_el_orden_no_quita_pujas` — misma cuenta, mismo conjunto, mismas decisiones BID.

Las diez primeras después del reorden:

```
id 31069  +41,30 %   NO_BID        id 38422  +12,50 %   NO_BID
id 27929  +20,59 %   BID           id 41566  +12,50 %   BID
id 23572  +15,38 %   BID           id 29185  +11,76 %   BID
id 15396  +14,81 %   NO_BID        id 22975  +11,57 %   BID
id 25815  +14,71 %   NO_BID        id 10292   +8,82 %   NO_BID
```

### El plazo va dentro, con su medición al lado

`PLAZO_DE_SALIDA = 10` no es una constante suelta: `comprobar_el_plazo()` lo vuelve a
derivar de la tabla en cada vuelta de la verja, y la guardia falla si no cuadra con el
pico. Sale de que a 10 días el que subía rinde **+7,430 %** y a 15 solo **+6,418 %**:
ahí satura y devuelve.

### Y una decisión pequeña que quiero que veas

**Al que no tiene pronóstico no se le castiga más que al que baja**: los dos van al
mismo escalón. Distinguirlos sería empezar a penalizar por no tener dato, y de ahí a
quitarlo de la lista hay un paso. Hay guardia sobre eso.

### Dónde va cuando se encienda

`src/analysis/acquisition_board.py:1330`, dentro del `filas.sort(...)`, como un
desempate más — detrás de la decisión, la puja viva y el escalón de `deployment`, y
delante del valor. **No cambia quién entra ni cuánto se paga: cambia a quién se mira
primero.**

---

## BLOQUE 3 — Qué cambia en producción, línea por línea

### LO QUE CAMBIA DE COMPORTAMIENTO

```
1. position_guardrail -> sale_order.py:519 y :623, sale_intent.py:281,
   roster_planner.py:102
   `validate_sale_set` pasa a `validate_sale_set_con_titularidad`.
   EFECTO: al proponer a quién vender, ya no basta con que queden cuerpos:
   se mira si el que sale es titular. Tres jugadores cambian de veredicto.

2. rival_bid_model.py — la curva de prima
   Los pesos de los siete peldaños salen de la masa real y no de 1/7.
   EFECTO: la probabilidad de ganar deja de estar hundida por creer que un
   rival paga +24,5 % una de cada siete veces. Con Rubén García la real era
   0,8953 y el motor creía 0,5435.
   DIRECCIÓN: conservadora. Con la masa real se puja IGUAL O MENOS, nunca más.

3. scout/accuracy.py — los denominadores
   Cada ratio con su `n` y su plazo, y el nulo al lado.
   EFECTO: cambia lo que se PUBLICA sobre el acierto de las fuentes.
   No cambia ninguna puja.

4. dashboard_state.py — el libro del escaparate
   Escribe una línea por reset con los veinte del Computer, y solo si la
   foto es de este reset.
   EFECTO: empieza a existir un histórico que hoy no existe.

5. los_libros.py + .gitignore — 16 libros pasan a 24
   EFECTO: ocho libros que morían con el runner empiezan a guardarse.
```

### LO QUE NO CAMBIA

```
· Ningún umbral: listón del 3 %, suelo del +1 %, `bid_cap`,
  `PRIMA_MAXIMA_DE_PUJA`, `MIN_WIN_PROBABILITY`, cupo, las cinco de
  `PUEDEN_ENCERRARLO`, `MAX_SINGLE_SPECULATION_PERCENT`, `MAX_SAFE_DEBT`,
  puertas de deuda. Ninguno se ha tocado.
· `count_free_slots` y `historical_max`: el bloque 4 está FUERA.
  `free_slots` sigue dando 0 y `ROSTER_FILL` sigue sin abrirse.
· La salida de emergencia por falta de dinero: `liquidity_manager` y
  `accept_before_expiry` siguen con la regla de cuerpos.
· `el_cable`: no está cableado y no se ha encendido.
· `la_direccion`: el filtro apagado y el orden apagado.
· `el_carry`: descartado, apagado.
· `player_value_engine`, `acquisition_board`, `intelligent_bid_engine`:
  solo declaran la vía en el motivo publicado. El propio código lo dice:
  «NO CAMBIA NINGUNA DECISIÓN».
· `acquisition_valuation`: tras sacar el bloque 4, lo único que queda
  respecto a producción es sacar un diccionario a una variable. Cero
  cambio de comportamiento.
· La bitácora del saldo: explicada, no arreglada.
· `.github/workflows/bordalas-live.yml`: sin tocar.
```

---

## Qué hará Pepe distinto en la primera vuelta

> **Visiblemente, casi nada. Y eso es lo que tiene que pasar.**

```
la cola de venta          IDÉNTICA. Caben los mismos 11, se bloquean los
                          mismos 9 (Dituro, Jonny, Djené, Manu Sánchez,
                          Rubén García, Pablo Ibáñez, Oriol Rey, Yamal, Jutglà)
los planes de solvencia   A, B1 y C pasan igual. El déficit de 373.984 €
                          se resuelve igual que ayer.
las pujas                 iguales o MÁS BAJAS, nunca más altas
free_slots                sigue en 0
```

**Lo único que cambia de verdad hoy son tres veredictos individuales:**

```
Dituro   POR  titular   cuerpos=PASA  ->  titularidad=BLOQUEA
Yamal    DEL  titular   cuerpos=PASA  ->  titularidad=BLOQUEA
Jutglà   DEL  titular   cuerpos=PASA  ->  titularidad=BLOQUEA
```

El freno **está armado y no muerde hoy**, porque la cola pone los sobrantes delante y
nunca llega al suelo de titulares. Muerde el día que la cola llegue a uno de esos tres.
Y Yamal deja de estar a salvo por accidente del recuento.

Y **empieza a escribirse** el libro del escaparate, una línea por reset.

## Qué mirar para saber si va bien o mal

Con umbrales, para que no haya que opinar:

```
QUÉ                        BIEN                MARCHA ATRÁS SI
─────────────────────────────────────────────────────────────────────────
los libros en el commit    8 libros nuevos     la primera vuelta commitea
de la primera vuelta       aparecen en git     0 de los 8 -> el guardado no
                                               los ve, revisa la lista

ventas propuestas          0 ventas de         Pepe propone vender a Dituro,
                           titulares           Yamal o Jutglà -> el freno no
                                               está actuando

solvencia                  el déficit se       pasan 2 vueltas con déficit y
                           resuelve como       `restores_solvency: False` en
                           hoy (plan A o B1)   los tres planes -> APAGA el
                                               freno, te ha quitado la salida

importe de las pujas       igual o menor       una puja sale MÁS ALTA que con
                           que ayer            la curva vieja -> la masa está
                                               mal calculada

free_slots                 0                   sale > 0 -> el bloque 4 se ha
                                               colado de vuelta

libro del escaparate       1 línea por reset,  2 líneas con el mismo
                           con `foto_at`       `dia_de_mercado` -> la foto
                                               vieja se está colando
```

**El umbral que más miraría: dos vueltas seguidas sin resolver el déficit.** Es el
único de la lista que cuesta dinero de verdad.

---

## Plan de vuelta atrás — escrito antes de encender

```
EL GUARDARRAIL POR TITULARIDAD
  Cambia `validate_sale_set_con_titularidad` por `validate_sale_set` en
  cuatro líneas: sale_order.py:519 y :623, sale_intent.py:281 y
  roster_planner.py:102. Nada más depende de ello.

EL LIBRO DEL ESCAPARATE
  Quita la llamada a `apuntar_el_escaparate` en dashboard_state.py
  (el bloque `try` que la envuelve). El libro deja de crecer; lo escrito
  se queda.

LA CURVA DE PRIMA
  `git revert` del commit de `ojeador/los-tres-arreglos` sobre
  src/analysis/rival_bid_model.py. Es el único fichero de producción de
  ese commit que cambia dinero.

LOS OCHO LIBROS
  No se apagan: guardar un libro no cambia ninguna decisión. Si
  estorbaran por tamaño, se quitan de `LIBROS` en
  src/estado/los_libros.py y se regenera el `.gitignore` con
  `python scripts/guardar_los_libros.py --gitignore`.
```

---

## Guardias

**13 guardias** en `src/analysis/test_la_direccion_v1.py` (9 de ayer + 2 del orden + las
dos de la lista), dada de alta en la verja.

**Verja: 152/152 en verde, exit 0**, corrida a fichero.

---

## Lo que no hice, y por qué

- **Ni una escritura contra Biwenger desde esta sesión.**
- **No encendí el cable.** No tiene ningún llamador en producción: `ENCENDIDO = True`
  habría sido decorativo. Decisión tuya, tomada.
- **No encendí el guardarrail en la salida de emergencia** (`liquidity_manager`,
  `accept_before_expiry`). Decisión tuya, tomada.
- **Saqué el bloque 4**, que venía puesto y vivo en la cadena. `free_slots` vuelve a 0
  y `ROSTER_FILL` sigue cerrado.
- **No moví ningún umbral.**
- **No subí los cuatro libros locales como libro bueno.** Están archivados en
  `archivo/2026-09-17/`.
- **No arreglé la bitácora.**
- **No encendí la dirección** —ni el filtro ni el orden— ni el carry.
- **No salí a la red.** Rebasé contra el `origin/main` local, de hoy 07:31. **Falta el
  `git pull --rebase` de verdad antes de empujar.**
- **No toqué `.github/workflows/bordalas-live.yml`.**
- **No empujé.**

### Lo que contradijo al encargo

1. **No había seis ramas que fusionar: eran una cadena lineal** y ya estaban todas
   dentro.
2. **El cable no era un interruptor.** Cero llamadores en producción.
3. **El guardarrail tampoco era «una línea»: eran seis**, y dos de ellas son la salida
   de emergencia.
4. **El bloque 4 estaba dentro y funcionando.** Lo saqué.
5. **Los «31 que no son libros» son 25**, porque ocho de los 31 sí lo eran.
6. **Las 821 líneas eran de texto, no registros.** Son 53 registros de verdad.
7. **El 89 % no salía del libro escondido**, sino de `price_history.json`, que llevaba
   en git desde el 14/09.
