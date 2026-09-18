# INFORME — EL PORTERO Y LA CAJA

**Fecha:** 2026-09-18
**Rama:** `urgente/el-portero` (dos commits, sin empujar)
**Foto:** `diagnostico/status.json`, `meta.generated_at = 2026-09-18T15:16:24`
(snapshot `data/snapshot_20260918_151033.json`)

---

## LO PRIMERO, PORQUE TIENE HORA

**Cambia el portero a mano en Biwenger antes de las 21:00 de hoy.
Esquivel fuera, Dituro dentro.**

El Elche de Dituro juega **hoy a las 21:00** contra el Espanyol: es el
primer partido de la jornada 7. Pasada esa hora Dituro queda bloqueado y
ya no se le puede alinear aunque se quiera.

El Atlético de Esquivel no juega hasta el **domingo 16:15**. O sea que
dejarlo puesto no solo cuesta el partido de hoy: deja la portería muerta
hasta el domingo.

El arreglo está hecho y probado, pero **no llega solo a esta jornada**.
El motivo está abajo, en «¿Llega a tiempo?».

---

## BLOQUE 1 — EL PORTERO

### 1. Por qué está Esquivel y no Dituro

No es un fallo de cuentas. El motor las hacía bien y le salía eso.

Los tres porteros, con los scores de la foto de las 15:16:

| | score | vara | pronóstico |
|---|---:|---:|---|
| **Esquivel** | **250.030,15** | 0,25 *(inventado)* | ninguno, cobertura 0 |
| Dituro | 235.067,68 | 0,2269 | FF 50 %, Importante |
| Iturbe | 213.230,15 | 0,2052 | FF 50 %, Reserva |

Ese 250.030,15 es **250.000 de suelo + 30,15 de base**. Nada más. El
suelo lo ponía [`lineup_engine.py`](../src/analysis/lineup_engine.py)
para los jugadores sin pronóstico, con este comentario escrito:

> «se le da un valor de 0,25 en la misma escala, que lo deja por encima
> de un suplente conocido —un Reserva al 40 % vale 0,17— y por debajo de
> cualquier titular conocido.»

**Ese comentario era cierto cuando se escribió, y dejó de serlo.** El
0,25 estaba calibrado contra `HIERARCHY_MATCH_QUALITY`, la escalera de
etiquetas cuyo peldaño más bajo es justamente 0,25 («Descarte»). Con esa
escalera, 0,25 era de verdad el último puesto.

Cuando `calidad_para_la_vara` sustituyó la etiqueta por los **puntos por
partido reales**, la vara perdió el suelo. Dituro es *Importante*, que
por etiqueta vale 0,80 de calidad; medido, con 6 puntos en 6 partidos,
sale a 0,336. Su vara cae de **0,54 a 0,227**. Por debajo del suelo.

El suelo no se movió con la escalera que lo sostenía. Desde ese día, **no
saber ganaba a saber**, y el primero en cobrarlo fue el portero.

No lo elige por valor: Esquivel es el más barato de los tres (150.000 €
en la foto). No lo elige por puntos: tiene 0. Gana solo por el suelo.

### ¿Sigue siendo nuestro Dituro?

**Sí, y está sano.** Ficha de plantilla en la foto de hoy:

```
Dituro · 2.180.000 € · 6 puntos · 6 partidos · 123 puntos la temporada pasada
status: ok · availability: DISPONIBLE · absence: null
Importante en el Elche · FF 50 % · próximo rival ESP, fuera, dificultad 5
```

No está lesionado, ni sancionado, ni vendido. Está en el banquillo, y
nada más.

### Lo que no preguntabas y es peor

**Dituro es el segundo de la cola de venta.** Motivo escrito por el
propio programa: *«Cae de precio y además no juega»*.

Y **el único jugador apartado de la venta es Esquivel**: *«sin escalón
conocido: vender a ciegas no se deshace»*.

O sea, el par completo invertido:

- el portero sin dato **juega y está protegido de la venta**;
- el portero con pronóstico y 123 puntos el año pasado **está sentado y
  en la cola para venderlo**.

Esto no lo vio nadie porque la guardia que lo vigila
(`test_orden_de_venta_v1`) solo muerde cuando hay una foto fresca en el
disco, y en CI esa foto no existe. Muerde desde hoy, y muerde con razón.

### Cuándo empezó

Esquivel entró en la plantilla **hoy mismo, a las 05:05**, en el reset,
por 150.376 €. Antes de esta madrugada no era nuestro. Es decir: el once
lleva roto desde esta mañana, no desde hace semanas.

### 2. Por qué Esquivel no está en el tablero de 151

El tablero de la jornada 7 está sano: 151 jugadores, jornada correcta,
`REFRESHED`, no rechazado, generado a las 13:10 de hoy.

**No es un problema de cobertura del Atlético.** El Atlético tiene **7
jugadores con pronóstico** en ese tablero, así que su página de
FutbolFantasy se bajó y se parseó bien. Esquivel se cayó él solo.

Y no está solo: en toda la liga hay **seis** jugadores sin pronóstico, y
los seis son de equipos con 7 a 9 compañeros cubiertos:

| jugador | equipo | partidos | puntos |
|---|---|---:|---:|
| Esquivel | Atlético de Madrid | 0 | 0 |
| Budimir | Osasuna | 6 | 45 |
| Miguel Román | Celta | 6 | 28 |
| Deossa | (87) | 6 | 23 |
| Carlos Romero | (19) | 5 | 15 |
| Mayol | (18) | 1 | 5 |

Los otros cinco son titulares habituales que FutbolFantasy publica
seguro. **Para esos cinco es un fallo de emparejamiento**, sin duda.

**Para Esquivel no puedo cerrarlo, y no voy a decir que sí.** Es el
tercer portero del Atlético, dorsal 25, 0 minutos, precio de suelo. Las
dos explicaciones siguen vivas:

- que FF no publique ficha suya (su página de equipo trae 27 nombres, no
  la plantilla entera);
- que la publique y no empareje.

Lo que inclina un poco la balanza hacia la primera: su precio de 150.000
es **único dentro de los objetivos del Atlético**, y con valor único basta
un parecido de nombre de 0,45 para cerrar la identidad. Si FF lo
publicara, casi seguro habría emparejado.

**El dato que lo cierra existe y no se publica.** El tablero guarda
`metadata.unmatched` —la lista de objetivos que no encontraron pareja, con
su nombre— y eso no sube al panel. Por eso el panel puede decir «10 de 11»
pero no puede decir quién ni por qué. Lo dejo señalado; no lo he tocado,
porque no era el encargo.

**Da igual cuál de las dos sea.** Tu decisión cubre los dos casos, y el
arreglo también.

### 3. El arreglo

Tu decisión, aplicada tal cual:

> «un jugador sin pronóstico no entra en el XI si hay uno con pronóstico
> en su puesto. Sin dato no es cero, pero tampoco es una apuesta: es el
> último recurso.»

En [`lineup_engine.py`](../src/analysis/lineup_engine.py), el suelo de
250.000 pasa a `SIN_PRONOSTICO_SCORE = -500_000`:

- queda **por debajo de cualquiera con pronóstico** (la banda con dato no
  baja de +2.500, porque la cobertura ya suma 3.000);
- queda **medio millón por encima del −1.000.000** con el que se marca a
  quien no se puede alinear;
- **sigue siendo el último recurso de verdad**: la búsqueda maximiza
  primero cuántos huecos llena y solo después el score, así que si no hay
  otro portero, el que no tiene pronóstico juega. La portería no se deja
  vacía.

Y no se inventa nada:

- `weekly_expected_value` viaja a **None**, no a 0,25;
- la tarjeta del XI lo publica a **None**, no a 0,0 —como ya hacía la
  ficha de plantilla—, porque un 0,0 ahí se lee «no se espera nada de él»,
  que es lo contrario de «no se sabe»;
- el banquillo dice **`SIN_PRONOSTICO`** («no hay pronóstico de
  titularidad suyo, y Dituro sí lo tiene») en vez de «puntúa menos», que
  era mentir sobre una comparación que nadie hizo.

Con el arreglo, el portero es **Dituro**.

### La guardia

`test_sin_pronostico_v1`. Reproduce **al euro** los tres scores de la foto
de las 15:16 y muerde de tres formas distintas, las tres comprobadas:

| se rompe esto | qué pasa |
|---|---|
| se restaura el suelo de 250.000 | 5 fallos, y Esquivel vuelve a salir de portero con 250.030,15 |
| se apaga la calidad medida (`BORDALAS_CALIDAD_ETIQUETA=1`) | 2 fallos: el banco deja de reproducir el fallo del 18/09 |
| el tablero de titularidad llega vacío | la reja se cierra: nadie tiene pronóstico y la guardia se cae |

El tercero es la trampa de este test y por eso está escrito aparte: con el
tablero vacío nadie desplaza a nadie y todo pasaría **por vacuidad**.

---

## ¿LLEGA A TIEMPO EL ARREGLO?

**No. Hay que tocar el once a mano, hoy, antes de las 21:00.**

Tres motivos, y con uno bastaría:

1. **Nada de esto escribe en Biwenger.** El once ya está puesto allí con
   Esquivel (`lineup.live.source: USER`, *«El XI puesto en Biwenger ya es
   el recomendado»*). El módulo del once es `observer_only`. Y hoy las
   escrituras están prohibidas por el encargo.
2. **Yo no empujo**, por el encargo. La rama está lista, con dos commits.
3. Aunque se empujara ahora mismo, el ciclo tarda en pasar y lo que
   cambiaría es **la recomendación**, no el once de Biwenger. Seguirías
   teniendo que ponerlo tú.

Lo que sí hace el arreglo es que **a partir del próximo ciclo Pepe
recomiende a Dituro y deje de tenerlo en la cola de venta**.

### El estado de la verja

**154 de 156 guardias en verde**, incluidas las dos nuevas. Fallan dos, y
las dos **leen `diagnostico/status.json`**, la foto que me pediste
refrescar:

- **`test_orden_de_venta_v1`** — *«el portero titular no aparece entre los
  que no se proponen»*. **No es ruido: es este mismo fallo.** Espera que
  Dituro esté apartado por ser el portero titular, y no lo está porque
  Esquivel le quitó el sitio. Se arregla solo cuando producción
  regenere la foto con el arreglo dentro.
- **`test_reloj_solvencia_v1`** — la foto de referencia quedó dentro del
  plazo al refrescarla. Es un ajuste de números de ese fichero, ajeno a
  esto, y no lo he tocado.

**CI está en verde ahora mismo**, y eso no es una suposición: la foto de
las 15:16 existe, o sea que el ciclo de producción corrió hoy a las 15:10,
o sea que la verja pasó. Las dos guardias de arriba no muerden en CI
porque allí ese fichero no existe y se saltan solas.

---

## BLOQUE 2 — LA CAJA

### 1. Qué evento no se está contando

**Una venta nuestra, contada dos veces.**

```
2026-09-18 07:03:10 UTC · transfer · jugador 15289 (LUNIN, portero)
de: Pepe Bordalés · a: (Computer) · importe: 420.200 €
```

420.200 € clavados. Es la diferencia exacta.

Y el contexto lo cierra: a Lunin **lo habíamos comprado ayer** en el reset
del 17/09 a las 05:08 por 421.000 €. Lo vendimos esta mañana a las 07:03,
una hora después del reset de las 07:00, por 420.200.

La dirección también cuadra: la reconstruida va **por encima** de la real,
o sea **sobra un cobro**, no falta un pago. Un cobro contado dos veces.

**Cómo lo sé sin ver el tablón de producción.** Reconstruí la caja con el
tablón que hay en el repo —627 eventos— y da **4.324.615 €**, que es
**exactamente el saldo real** de la foto. Producción leyó 640 eventos y le
salen 4.744.815. La diferencia son 420.200, el importe justo de esa venta,
que en el tablón local aparece **una sola vez**.

Y que no haya movimientos nuevos entre medias lo confirma el propio saldo
real: si hubiera entrado dinero de verdad después de las 11:11, la caja
real ya no coincidiría con mi reconstrucción, y coincide al euro.

**Lo que lo confirmaría del todo**, cuando se pueda mirar: dos filas
`transfer` del jugador 15289 en el tablón de producción, con fechas
distintas.

### 2. ¿Evento nuevo o viejo mal contado?

**Viejo, y mal contado.** Es `transfer`, el tipo de siempre. No hay ningún
tipo de evento nuevo: revisé los trece tipos del tablón y los nueve que la
reconstrucción ignora —`bettingPool`, `playerMovements`, `adminText`,
`roundStarted`, `userJoin`, `leagueSettings`, `userPoints`, `leagueReset`,
`userName`— **no llevan ni un campo de dinero**. La quiniela, con sus 344
eventos, es decorativa.

La avería es la reja de duplicados de `reconstruir`:

```
(tipo, FECHA, jugador, de, a, importe)
```

**Lleva la fecha dentro.** Biwenger reemite la misma operación minutos
después con otro `event_id` y otro `date`, así que la copia entra como un
hecho nuevo y el dinero se cuenta dos veces. Los 30 «repetidos saltados»
son los que sí comparten fecha; estos se cuelan por debajo.

### Y no es la primera vez — esto es lo gordo

En el tablón hay **cinco grupos más** con la misma firma, todos `transfer`,
todos separados por minutos:

| jugador | de | importe | copias | separación | se cuenta de más |
|---:|---|---:|---:|---|---:|
| 31069 | rival | 2.464.100 | **3** | 4m45s + 4m27s | 4.928.200 |
| 2001 | rival | 4.983.000 | 2 | 4m27s | 4.983.000 |
| 39885 | rival | 3.434.200 | 2 | 3m32s | 3.434.200 |
| 30505 | rival | 1.577.100 | 2 | 2m34s | 1.577.100 |
| 37724 | rival | 636.300 | 2 | 2m34s | 636.300 |

**15.558.800 € de sobrecuenta, toda en la caja de los rivales.**

Nadie lo vio porque los saldos de los rivales están ocultos y no hay contra
qué compararlos. Lo de hoy es la primera vez que le toca a una venta
**nuestra**, que es la única caja comprobable.

O sea que la conclusión del panel se queda corta. No es que *si* falla con
el nuestro tampoco valga el de los rivales: **el de los rivales lleva
semanas mal**, y lo de hoy es lo que por fin lo ha hecho visible.

(Encaja con `ledger_audit: CON_HUECOS` y los 9 jugadores sin explicar
repartidos en 4 managers.)

### 3. Las jornadas: 7 vistas, 6 pagadas

**No falta ninguna. La que no paga es exactamente la que se ignora.**

Las cuentas son literales:

```
rounds_seen  = len(jornadas pagadas) + len(ignoradas)   = 6 + 1 = 7
rounds_paid  = len(jornadas pagadas)                    = 6
ignored      = ["Jornada 1"]
```

No hay una tercera categoría: una jornada o paga o está en la lista de
ignoradas. Anoche era 6 y 5 con la misma lectura (5 pagadas + 1 ignorada),
y hoy hay una más porque entró la Jornada 6.

**Por qué la Jornada 1 no paga:** está partida, y la liga tiene
`splitRound: "ignoreFirst"`.

```
id 4899  "Jornada 1"                    <- primera parte, NO paga
id 4937  "Jornada 1 (aplazada)" part 2  <- la que paga
```

Se ignora la primera parte a propósito. Es justo el arreglo que encontró
el agujero de 870.000 € en su día.

### 4. Qué es `REVIEW_REQUIRED`

Sale de [`rival_intelligence_engine.py`](../src/analysis/rival_intelligence_engine.py).
Es un **o**, con dos causas:

```python
ledger_status = "EXACT" if (validation["exact"] and not unknown_types) else "REVIEW_REQUIRED"
```

1. **`validation["exact"]` es falso** — el saldo del libro no coincide con
   el oficial de Biwenger (`initialBalance + earnings − expenses`).
2. **`unknown_types` no está vacío** — ha llegado algún tipo de evento del
   tablón que el motor no sabe clasificar ni como económico ni como
   inofensivo.

Cualquiera de las dos lo pone en `REVIEW_REQUIRED`.

**Y aquí está el problema de fondo, que es por qué llevaba desde el 15/09
sin respuesta:** el panel publica `ledger_status` **pero no publica ni
`validation` ni `unknown_types`**. Los dos se calculan, los dos se quedan
dentro. Desde la foto es imposible saber cuál de las dos causas se
disparó.

Hoy, con el descuadre de 420.200, la primera basta para explicarlo. Pero
eso es una deducción mía, no un dato: la foto no lo dice.

Lo dejo señalado y **no lo he tocado**: publicar esos dos campos toca el
contrato del panel y no estaba en el encargo. Es una línea de trabajo, y
mientras no se haga, `REVIEW_REQUIRED` seguirá siendo una luz roja sin
etiqueta.

### 5. El arreglo de la caja

Ahora, cuando no cuadra, **se dice a qué mirar**. En
[`caja_de_la_liga.py`](../src/analysis/caja_de_la_liga.py), un
`sospechosos()` que busca dos cosas:

- **el importe que cuadra al euro** con la diferencia;
- **los grupos que la reja no puede ver**: misma operación, fechas
  distintas, pegadas en el tiempo.

`cuadra()` los publica en `suspects` y `suspect_types`, y además lo dice
con palabras. El mensaje de hoy sale así:

> LA CAJA NO CUADRA: reconstruida 4.744.815 EUR contra 4.324.615 EUR
> reales. Se separan 420.200 EUR. Si el metodo falla con el nuestro, la
> caja de los seis rivales tampoco vale. **Cuadra al euro con un evento
> `transfer` del jugador 15289 por 420.200 EUR: sobra un cobro.**

La ventana de reemisión son **3.600 s**. Sin ventana, la racha diaria
—250.000 € al mismo manager el lunes y el martes— salía marcada como copia,
y son dos cobros de verdad. Los reemitidos de verdad van de 2m34s a 4m45s,
así que una hora los separa con holgura por los dos lados.

**Esto solo informa. No cambia ni un euro de la reconstrucción ni una sola
decisión.**

### La guardia

`test_la_caja_cuadra_o_dice_por_que_v1`, con tablón fijo escrito a mano: no
lee producción, no sale a la red, no mira el reloj. Comprobado que muerde:

| se rompe esto | qué pasa |
|---|---|
| se vuelve a publicar solo el número | 7 fallos |
| la lista de eventos llega vacía | 7 fallos |

---

## LO QUE NO HE HECHO, Y POR QUÉ

- **No he escrito nada contra Biwenger.** Por eso el once lo tienes que
  tocar tú, hoy, antes de las 21:00.
- **No he empujado.** Rama `urgente/el-portero`, dos commits.
- **No he tocado** ningún umbral, ni `POSITION_DESIRED`, ni
  `STRATEGIC_FLOOR`, ni el cupo, ni `MAX_SAFE_DEBT`, ni las cinco de
  `PUEDEN_ENCERRARLO`, ni `.github/workflows/bordalas-live.yml`.
- **No he inventado un pronóstico para Esquivel.** Su vara sale a `None` y
  el panel dirá «sin dato», que es la respuesta correcta.
- **No he salido a la red** más que para bajar la foto que me pediste
  refrescar, con tu propio script.
- **No he arreglado la reja de duplicados**, que es la causa raíz del
  descuadre. Lo he dejado señalado y medido. Tocar la clave de
  deduplicación cambia la caja de los siete managers de golpe —incluidos
  15,5 M de sobrecuenta en los rivales— y eso mueve `MAX_VISTO`, `AMENAZA`
  y el tope de puja. No es cosa de hacerlo con la jornada encima y sin que
  lo decidas. **Es lo siguiente.**
- **No he publicado `validation` ni `unknown_types`** en el panel, ni
  `metadata.unmatched` del tablero de titularidad. Los tres se calculan y
  ninguno sube. Son tres líneas de trabajo, las tres fuera del encargo.
- **No he arreglado `test_reloj_solvencia_v1`**: su foto de referencia
  quedó dentro del plazo al refrescar, y ajustar esos números es otra
  cosa.
- **No he tocado los cinco jugadores que no emparejan** (Budimir, Miguel
  Román, Deossa, Carlos Romero, Mayol). Con el arreglo de hoy ya no
  desplazan a nadie del once, que era la urgencia, pero siguen sin
  pronóstico y siguen sin poder valorarse.

### Un aviso de higiene

Correr la verja **ensucia los libros**. Al terminar, estos cuatro ficheros
quedan modificados en el árbol y **no los he tocado ni incluido en los
commits**:

```
data/intelligence/libro_en_la_sombra.jsonl
data/intelligence/marcador.json
data/rival_intelligence/board_events.json
data/solvency/bitacora_del_saldo.jsonl
```

La regla de la casa dice que ninguna guardia escribe en los libros, y la
propia verja ya lo canta («LEEN LA CARPETA DE ESTADO AL CORRERSE»). Los
dejo como están para que decidas tú.

---

## LOS NÚMEROS Y DE DÓNDE SALEN

| dato | valor | fuente | fecha |
|---|---|---|---|
| Scores de los tres porteros | 250.030,15 / 235.067,68 / 213.230,15 | `diagnostico/status.json` → `lineup` | 18/09 15:16 |
| Ficha de Dituro | 2,18 M · 6 pts · 6 partidos · DISPONIBLE | idem → `roster.players` | 18/09 15:16 |
| Tablero de titularidad | 151 jugadores · jornada 7 · REFRESHED | idem → `lineup.starter_board_*` | 18/09 13:10 |
| Cobertura del Atlético | 7 jugadores con pronóstico | idem, cruzando `todaLaLiga` | 18/09 15:16 |
| Sin pronóstico en la liga | 6 de 146 | idem | 18/09 15:16 |
| Descuadre de la caja | 4.744.815 vs 4.324.615 = 420.200 | idem → `rival_intelligence.cash_check` | 18/09 15:16 |
| Venta de Lunin | 420.200 € · 07:03:10 UTC | `data/rival_intelligence/board_events.json` (n=627) | 18/09 |
| Reemisiones de rivales | 5 grupos · 15.558.800 € | idem | 17/08–04/09 |
| Reconstrucción local | 4.324.615 = saldo real, al euro | idem, con `reconstruir()` | 18/09 |
| Primer partido J7 | 2026-09-18 21:00 CEST (Elche–Espanyol) | `diagnostico/status.json` → `elCalendario` | 18/09 15:16 |
| Verja | 154/156 | `scripts/run_validation_gate.py` | 18/09 |
