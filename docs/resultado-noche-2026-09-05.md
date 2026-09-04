# Resultado de la noche del 04→05/09/2026

Rama `noche/2026-09-05`, subida. `main` sin tocar.

**Puerta: 63 de 63 en verde.** Eran 58 al empezar. Siete commits, uno
por tarea más dos por fallos que salieron al comprobar el trabajo
contra datos reales.

`npm run build` pasa. **No se ha desplegado nada**, y `dashboard-v8/dist/`
se ha dejado como estaba: el workflow de despliegue construye por su
cuenta y solo corre sobre `main`, asi que subir mi build seria ruido en
el diff sin ganar nada.

Ninguna decisión de Pepe cambia esta noche, con una excepción
ordenada por el encargo y explicada abajo (tarea 1).

---

## Lo que se hizo

### 1. Cerrada la otra mitad del guardarraíl de jornada

`b5adc07` — `candidate_starter_lookup.py`, `autopilot.py`,
`dashboard_state.py`

El 04/09 se tapó la mitad: el proveedor dejó de **servir** un tablero
de otra jornada. Pero `candidate_starter_lookup` lee el fichero del
disco por su cuenta —es por donde pasan el XI, el tablero de
fichajes, el plan de deuda y la pantalla— y nunca miraba la jornada.
Su propio docstring decía que `matchday` era "el guardarraíl contra
usar datos de una jornada en otra" y lo único que hacía era
publicarlo.

Ahora un tablero de otra jornada no se sirve: el lookup sale vacío,
nadie recibe pronóstico y Pepe se queda quieto.

**Esta es la única cosa de la noche que puede cambiar lo que Pepe
hace**, y solo en el caso en que el dato está mal. Va con las dos
condiciones que la hacen aceptable:

- **No se falla en silencio.** El motivo —*"El tablero es de la
  jornada 3 y estamos en la 4: sin pronósticos hasta que se
  refresque"*— sale por `board_stamps()`, por el `cache.error` que la
  pantalla ya pinta, y por dos campos nuevos y explícitos.
- **Sin saber la jornada no se rechaza nada.** Rechazar contra una
  expectativa que no tenemos sería inventarse un motivo y dejarlo
  quieto por nada. La fijan los dos procesos que sí la saben: el
  ciclo y la telemetría.

La jornada esperada entra en la firma de la caché del lookup: el
tablero se queda rancio mientras el calendario avanza, y sin eso la
jornada nueva se contestaría con la respuesta de la vieja.

Guardia: `test_jornada_en_la_valoracion_v1` (14 pruebas).

### 2. Que se vea lo que ya se publicaba

`dfb75af` — `dashboard-v8/`

- **LA CARRERA**, arriba del todo en INICIO.
- **EL LIBRO DE PUJAS**, en AUDITORÍA. Sale vacío y se enseña igual:
  un panel que aparece el día que hay datos no se mira nunca. Y dice
  *"todavía no ha jugado esta mano"*, no un 0 %, que se leería como
  "pierde siempre".
- **EL TOPE POR OPERACIÓN**, junto al presupuesto en CAJA. Se arregló
  el lector el 04/09 y seguía sin salir en ninguna parte: arreglado e
  invisible es medio arreglado.
- **A HORIZONTE DE TEMPORADA** y **SI HUBIERA HUECO**, en MERCADO y
  debajo de la tabla que comentan. Van ahí a propósito: comparar dos
  valoraciones obliga a tenerlas delante. En pantallas separadas
  nadie las compara.

La brecha de plantilla de los siete contra la nuestra estaba repartida
en dos tablas sin que nadie las restara; ahora es una columna.

Los tres paneles nuevos llevan escrito **en la propia pantalla** que
no mandan. Hay guardia que comprueba que el aviso sigue puesto.

Guardia: `test_pantalla_lee_lo_publicado_v1`, que cose los dos saltos
—Python → JSON → JavaScript— que ningún test cruzaba.

### 3. El módulo de carrera

`d4734b6` — `src/analysis/race_state.py`

Puesto, distancia, jornadas restantes, ritmo necesario, brecha de
plantilla y urgencia.

**La pregunta útil no es "¿a cuántos puntos vas?" sino "¿cuánto mejor
que el líder hay que ser cada jornada?".** Sobre la foto del 04/09:
13 puntos, 35 jornadas, **0,37 puntos por jornada**. Y como 0,37
sueltos no significan nada, se mide contra lo que Pepe saca en una
jornada normal (44,3): **un 0,8 %**.

La escala de urgencia se ordena por ese porcentaje y no por la
distancia, porque trece puntos en la jornada 4 y trece en la 35 son
la misma distancia y no son el mismo problema.

Las jornadas jugadas salen del calendario real contando las
**terminadas**: una jornada a medias todavía reparte puntos, y
contarla encogería el ritmo necesario.

Guardia: `test_estado_de_carrera_v1` (21 pruebas), incluida una que
recorre **diez rutas de decisión** y falla si alguna nombra
`race_state`.

### 4. La valoración a horizonte de temporada, en sombra

`e466ae8` — `src/analysis/season_horizon_shadow.py`

```
puntos por jornada = puntos esperados / 38
puntos restantes   = puntos por jornada × jornadas que quedan
valor temporada    = puntos restantes × precio del punto
```

Con el precio del punto **medido** (21.758) y no la constante
`EUROS_POR_PUNTO = 30.000`, que está un 38 % por encima de lo que
paga esta liga.

Los ajustes que pedía el encargo —jerarquía, probabilidad de titular,
disponibilidad— **ya vienen dentro de `expected_points`**,
multiplicados en `expected_points_factor`. No se vuelven a aplicar:
contarlos dos veces era el error fácil, y hay guardia que lo fija
comprobando que el valor es lineal en los puntos.

**La dificultad de calendario no se aplica, y es a propósito.** A
tres días importa mucho contra quién juegas; de aquí a la jornada 38
cada equipo juega contra todos, en casa y fuera, así que el ajuste
tiende a uno por construcción. Lo único que quedaría sería el ruido
de emparejar *"Deportivo Alavés"* con *"Alavés"*, y ese tipo de ruido
ya nos ha costado dinero por otro lado.

**El número sale con sus peros**, publicados en la misma fila:
sin pronóstico los puntos no llevan descuento (caso Gustavo Puerta),
y el pronóstico semanal pesa 0,15, así que un suplente conserva casi
todos sus puntos.

`acquisition_valuation.py` **no se ha tocado**. Un campo nuevo allí
habría sido más corto y habría metido la sombra dentro de la ruta que
decide.

Guardia: `test_valor_temporada_sombra_v1` (21 pruebas).

### 5. La vía de ampliar plantilla, en sombra

`48a67d1` + `[fix]` — `src/analysis/roster_expansion_shadow.py`

**Los huecos no se inventan.** El tope de plantilla de Biwenger no
está en el código y la auditoría lo dejó como no comprobado. Se
cuenta contra la plantilla más grande de la liga (17) y se publica
como lo que es: una **cota inferior**, con esa palabra dentro del
JSON.

**Hay dos puertas por las que se cae un fichaje, no una.** La primera
versión filtraba solo por el veto de `as_xi` (16 de 22) y se dejaba
fuera al mejor candidato del tablero: a Expósito no le vetan —la vía
del once le da valor, *"Suma 81 puntos"*— sino que le gana la reventa
en el `max()` por euros, y entonces se le exige rendimiento de
especulación.

Guardia: `test_ampliar_plantilla_sombra_v1` (26 pruebas).

---

## Qué habría hecho distinto el cerebro nuevo

**Lo primero, y es lo contrario de lo que esperábamos: el cerebro
nuevo es más conservador, no más agresivo.**

Sobre las 22 filas de la foto de producción del 04/09:

| | |
|---|---|
| Ratio temporada / hoy, mediana | **×0,62** |
| Filas valoradas **por debajo** de hoy | **19 de 22** |
| Fichables más baratos por punto que el mercado | **2 de 18** |

La razón está en qué es cada número. Hoy, con `intent = SPECULATION`,
la valoración de Pepe es esencialmente **el precio de reventa**:
`our_value ≈ precio × 1,01` en las 22 filas. La valoración a
temporada dice otra cosa: **lo que valen los puntos que va a dar**, al
precio al que esta liga los paga.

### ¿Habría fichado a alguien que hoy se rechaza?

**Con esta foto, no.** Y eso es un resultado, no un fracaso.

Los tres candidatos de más peso son los que el encargo señalaba:

| Jugador | Precio | Pepe hoy | A temporada | €/punto |
|---|---|---|---|---|
| Expósito | 5,13 M | 5,20 M | **3,93 M** | 28.417 |
| Odysseas | 3,75 M | 3,80 M | **2,89 M** | 28.274 |
| Natan | 3,01 M | 3,05 M | **2,22 M** | 29.441 |

El mercado paga el punto a **21.758**. Los tres cuestan entre 28.000
y 29.000 el punto. **El cerebro nuevo también dice que no** —pero por
una razón de fútbol, no de trading.

Ese es el cambio real, y no es pequeño. Hoy Expósito se rechaza con
*"como especulación rinde un 0,59 % y se exige al menos un 3 %"*, que
como decía la auditoría ni siquiera está mirando el fútbol. Con la
segunda opinión al lado, el mismo "no" pasa a ser *"pagarías 28.417 €
por punto cuando el mercado los da a 21.758"*. Un motivo que se puede
discutir.

### Los únicos dos que salen baratos son de banquillo

De los 18 fichables, solo dos cuestan el punto por debajo del
mercado: **Rubén Sánchez** (10.507 €/punto, *Revulsivo*, 30 %
titular) y **Jon Pacheco** (12.134 €/punto, *Reserva*, 0 % titular).
Los dos son BENCH.

**Y ahí hay una advertencia que conviene leer antes de conectar
nada.** Un cerebro que valorase solo a temporada empujaría a acumular
suplentes baratos que suman puntos por poco dinero — que es
exactamente el bucle de las catorce defensas que la regla del peor
titular se construyó para cortar. La valoración a temporada **no
sustituye** a esa regla: la complementa.

El motivo técnico está publicado en cada fila: el pronóstico semanal
pesa 0,15 en los puntos esperados, así que un jugador al 0 % conserva
casi todos. A tres días eso da igual; a horizonte de temporada es la
diferencia entre un chollo y un banquillo caro.

### Lo que sí desbloquearía, y cuánto

Con **3 fichas libres** (14 nuestras contra 17 la mayor de la liga),
la lista serían Expósito, Odysseas y Natan: **11,89 M** por
**415 puntos** de aquí a final. A 21.758 el punto eso son **9,04 M**
de valor en puntos por 11,89 M de precio. Sigue sin salir.

**La conclusión honesta: el horizonte no es lo que tiene a Pepe
quieto.** Con los precios de esta foto, ni valorando a temporada hay
una compra clara. Lo que la auditoría señalaba como causa —el veto
del once, el `intent` por euros, el presupuesto en cero por
`HARD_SAFETY`— sigue siendo lo que manda.

---

## Lo que me sorprendió

**1. El dashboard se generaba sin los cinco bloques nuevos, y en
verde.** Al añadir los bloques se reordenó código sin querer y
`build_acquisition_board` quedó llamándose con `exposure` antes de
que existiera. `UnboundLocalError`, capturado por un `try/except`
puesto para proteger la telemetría. El fichero compilaba, la puerta
seguía verde con 58 guardias y `status.json` salía sin `race`,
`season_horizon`, `roster_expansion`, `rival_squads` ni
`bid_outcomes`.

Lo peor no fue el fallo: fue que **mis propias guardias lo dejaron
pasar** porque comprobaban el orden leyendo el *texto* del fichero
(`fuente.index(a) < fuente.index(b)`). El texto estaba en orden; la
ejecución no. La guardia nueva lee el árbol y recorre las
asignaciones en el orden en que se ejecutan, y se prueba a sí misma
con el código roto de esta noche reducido a cuatro líneas.

Solo se vio **generando el dashboard de verdad**. Ningún test de los
63 lo hacía.

**2. La lista de fichajes proponía fichar a uno nuestro y a un
lesionado.** Al comprobarla contra la foto de producción salió que
proponía a **Gustavo Puerta** —que es nuestro; la fila está ahí
porque Luismi_Haz nos ofrece 4,47 M por él— y marcaba a **Calero**
como el mejor chollo del tablero. Calero está lesionado.

La causa: el tablero de adquisición no es una lista de compra, es
todo lo que Pepe mira, y dentro hay filas que no son fichajes
posibles. Es un buen recordatorio de por qué esto va en sombra: un
observador equivocado cuesta una línea mal pintada; lo mismo
conectado a la ruta de compra habría puesto dinero encima de un
jugador que ya teníamos.

**3. La brecha con el líder es ruido.** 0,37 puntos por jornada, un
**0,8 %** de lo que Pepe saca en una jornada normal. Iba a la tarea 3
esperando encontrar urgencia y lo que hay es lo contrario: la
distancia deportiva es pequeñísima y la de plantilla es enorme
(21,7 M). Lo que decide esta liga no es correr más: es que 47,7 M de
plantilla rindan como 69 M, o dejar de tener 47,7.

Por eso la escala de urgencia se ordena por exigencia y no por
puntos. Dramatizar 13 puntos habría sido fácil y falso.

**4. La dificultad de calendario se cancela sola a horizonte de
temporada.** Fui a implementarla porque el encargo la pedía y me
encontré con que no tiene sentido: de aquí a la 38 todos juegan
contra todos. El ajuste tiende a uno y lo único que quedaría sería el
ruido del emparejamiento de nombres. Es la única parte del encargo
que no está hecha como estaba escrita, y está explicada en el código.

**5. La temporada local no ha empezado, y el marcador se coronaba
líder.** Con el snapshot en disco —del 17/08, los siete a cero— la
frase salía *"Vas 7º, a 0 puntos"* con urgencia **LÍDER**: `max()`
con empate devuelve el primero de la lista. Dos cosas contradictorias
en el mismo renglón, y solo visible ejecutando con datos reales.

---

## Lo que se quedó fuera, y por qué

**La dificultad de calendario en la valoración a temporada.** Por lo
de arriba: el ajuste tiende a uno y solo aportaría ruido. Si el dueño
quiere igualmente el número, lo que hace falta primero es un mapeo
fiable entre los nombres del calendario de LaLiga y los del catálogo
de Biwenger. Sin eso, no.

**Conectar cualquiera de las tres cosas nuevas a una decisión.** Es
lo que el encargo prohibía y hay tres guardias que lo vigilan: once
rutas de decisión revisadas una a una por `race_state`,
`season_horizon_shadow` y `roster_expansion_shadow`.

**Un test que genere el dashboard entero en CI.** Es lo único que
habría cazado el fallo del punto 1 de raíz, y tarda un par de minutos
y necesita snapshot en disco. El detector de variables cubre esa
clase de fallo sin coste; un end-to-end de verdad es una decisión de
CI que no me correspondía tomar de madrugada.

**El tope real de plantilla de Biwenger.** Sigue sin comprobarse. Se
publica una cota inferior y se dice que lo es. Se resuelve mirando
Biwenger un minuto, y eso lo hace el dueño.

---

## Cómo quedó

```
rama          noche/2026-09-05, subida
main          sin tocar
puerta        63/63 en verde  (58 al empezar, 5 guardias nuevas)
commits       7
frontend      npm run build OK · NO desplegado
dinero        cero cambios: ni umbrales, ni presupuestos, ni pujas,
              ni ventas. Los tres modulos nuevos son observadores
              y hay guardias que lo comprueban.
```

Lo único que puede cambiar el comportamiento de Pepe es el
guardarraíl de jornada de la tarea 1, que era el encargo, y solo se
activa cuando el tablero es de otra jornada — es decir, cuando el
dato está mal de todas formas. Y cuando lo haga, lo dirá en pantalla.
