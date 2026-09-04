# Datos que se recogen, se guardan y no lee nadie

04/09/2026. Trazado sobre el código en disco, con `grep`.

**Nada de esto se ha enchufado.** Los tres bloques cambian
decisiones de dinero y esa decisión no es de una noche. Esto es el
mapa: qué hay, dónde muere cada cadena, y qué costaría.

Al final hay una corrección: parte del "código muerto" de la
auditoría **no está muerto**.

---

## 1. Lo que sabemos de cómo puja cada rival

### Qué hay

`rival_intelligence_engine.py:1934` y `:1948` calculan, por manager:

```
avg_lost_bid        media de lo que pujó en las subastas que perdió
max_observed_bid    la puja más alta que le hemos visto
```

Salen de reconstruir el tablón, y hoy son números gordos y reales:
Luismi_Haz tiene `avg_lost_bid: 23.310.000` en la foto de disco;
otros tienen 11,3 M, 3,5 M, 3,0 M, 2,6 M.

### Dónde muere

**`avg_lost_bid`: no tiene un solo lector.** Se escribe en
`rival_intelligence.json` y ahí se queda. Ni el dashboard lo pinta.

**`max_observed_bid` llega más lejos, pero tampoco decide.**
`rival_bid_model.py:408` lo lee, lo mezcla con `max_lost_bid` y
`max_winning_bid` en una variable `observada`… y `observada` solo
sirve para rellenar el campo `max_observed_bid` de la fila de salida
(`:446`). Nadie lee esa fila después. La `participation` —que sí
decide— se calcula con el **número** de pujas y la cobertura del
ledger, nunca con el **importe**.

O sea: sabemos por cuánto puja cada rival y modelamos su
probabilidad de pujar sin usarlo.

### Qué costaría enchufarlo

Poco código, y ahí está el peligro. La puja se dimensiona hoy contra
`capacity` (el `maximum_bid` estimado del rival). Añadir "y por
cuánto suele pujar de verdad" es cambiar una línea en
`rival_bid_model.py`.

**El riesgo no es el código, es el dato.** La auditoría ya lo marcó:
el saldo reconstruido de Luismi_Haz se movió 23 M en un día. Si
`capacity` puede estar mal, `avg_lost_bid` sale del mismo tablón y
del mismo ledger. Alimentar el dimensionado de pujas con un número
reconstruido sin antes cerrar cuánto nos fiamos de la
reconstrucción es cambiar un error por otro más caro.

**Antes de enchufarlo hace falta:** que el libro de pujas
(`bid_outcome_ledger`, ya escribiendo desde el 03/09) acumule
suficientes cierres reales para poder contrastar el importe
reconstruido contra uno observado por nosotros mismos.

---

## 2. La metadata de FutbolFantasy

### Qué hay

`futbolfantasy_provider.py:1545-1605` escribe, en cada tablero:

| Clave | Qué dice |
|---|---|
| `low_confidence` | el nombre no gana con claridad a otro del mismo equipo |
| `price_gaps` | la identidad está clara pero el precio de FF no cuadra con el catálogo |
| `unmatched` | objetivos que no encontró |
| `no_slug` | equipos que no sabe scrapear |
| `no_team` | jugadores sin equipo en el catálogo |
| `methods` | con qué método emparejó cada jugador (`SLUG`, `NAME`…) |
| `unknown_availability_codes` | estados que FF sirve y no sabemos traducir |

### Dónde muere

**En el propio fichero.** El único lector en todo el repositorio es
`scripts/probe_starter_coverage.py`, una sonda manual que hay que
lanzar a mano. Ningún módulo de producción lo abre.

El caso que lo ilustra está en la auditoría: Javi Hernández,
emparejado por método `NAME` con margen 0,586 y un desvío de precio
del 45,7 %. Está escrito en `price_gaps` y en `low_confidence` desde
que se generó el tablero. Nadie lo ha leído nunca. Su
`starter_probability` y su jerarquía entran en la valoración con el
mismo peso que la de un emparejamiento exacto por slug.

### Qué costaría enchufarlo

Esta es **la más barata y la menos peligrosa de las tres**, porque
no hay que decidir nada nuevo: es degradar la confianza de un dato
que ya se usa.

`player_value_engine.py` ya tiene el mecanismo montado:
`predictability_confidence()` (`:779`) coge un valor de
`team_context` y devuelve un factor entre 0,85 y 1,00 que multiplica
la confianza sin tocar los puntos. Un jugador en `low_confidence`
podría pasar por el mismo embudo.

**El coste real es de calibración, no de código.** ¿Cuánto se
descuenta por un `NAME` con margen 0,586? Ese número no se puede
sacar de la nada: sale de cruzar `methods` con el libro de acierto
(`source_accuracy`) y ver si los emparejamientos flojos aciertan
peor. Los datos para medirlo ya están los dos en disco.

**Lo que sí se puede hacer mañana sin calibrar nada:** sacar los
contadores a la pantalla. Que el panel diga "59 jugadores, 4 de
ellos con emparejamiento dudoso" no cambia ninguna decisión y le da
al dueño lo que hoy no tiene.

---

## 3. Los campos por jugador

### Qué hay

`futbolfantasy_provider.py:1053-1085` construye, para cada jugador
del tablero:

```
availability.booked          apercibido de sanción
market_flags.transferible    FF dice que su club lo vendería
market_flags.cedible         FF dice que saldría cedido
minutes                      minutos totales jugados
form                         índice de forma de FF
team_context.rotation        % de rotación de su entrenador
team_context.predictability  % de previsibilidad del entrenador
```

### Dónde muere

**`team_context.predictability` sí se lee** —`player_value_engine.py:783`,
el embudo de confianza de arriba—. Es la prueba de que el camino
existe y funciona.

**Los otros seis no tienen lector.** `minutes` y `team_context`
llegan hasta `candidate_starter_lookup.py:203-204`, que los copia a
la ficha del jugador; de ahí nadie los saca. `form`,
`market_flags` y `availability.booked` ni siquiera llegan al lookup.

### Qué costaría enchufarlo, uno a uno

**`minutes` — el más útil y el más delicado.** Hoy la valoración usa
puntos totales. Un jugador con 156 puntos en 300 minutos y otro con
156 en 2.700 no son el mismo activo, y ahora mismo son
indistinguibles. Enchufarlo es pasar de "puntos" a "puntos por
minuto", y eso **reordena el tablero entero**. No es un ajuste: es
otra forma de valorar. Decisión del dueño, y con la vista puesta en
el caso Gustavo Puerta que ya señaló la auditoría.

**`team_context.rotation` — el más barato.** Mismo embudo que
`predictability`, misma función, mismo tipo de factor. Un
entrenador que rota mucho hace menos fiable cualquier pronóstico de
titularidad. Media hora de código. La calibración vuelve a ser el
trabajo de verdad.

**`availability.booked` — pequeño y concreto.** Un apercibido a una
amarilla de la sanción tiene riesgo real de perderse la jornada
siguiente. Hoy no se distingue de quien no tiene tarjetas. Cabe como
una señal más en `player_availability.py`, junto a las que se
arreglaron esta noche. Es el único de los seis que **no** cambia
euros: cambia una etiqueta.

**`market_flags` — el que menos promete.** Es la opinión de FF sobre
qué haría un club, no un hecho. Sin medir primero si acierta, no
debería tocar nada. Y para medirlo hace falta esperar a un mercado
de fichajes entero.

**`form` — sin decidir.** No está documentado qué mide exactamente
el `data-forma_value` de FF ni en qué escala. Antes de usarlo hay
que averiguar eso, y no se averigua desde el código.

---

## 4. Corrección: el código muerto es la mitad de lo que parecía

La auditoría dice que `speculation_intelligence.py` y
`market_brain_shadow.py` no tienen importadores, y que **arrastran**
`external_status.py`, `injuries.py` y `transfers.py`.

Comprobado con `grep`, la primera mitad es cierta y la segunda no.

### Muerto de verdad

**`src/analysis/market_brain_shadow.py`** — cero importadores. Ni
código, ni tests. Nadie lo nombra.

**`src/intelligence/speculation_intelligence.py`** — un solo
importador, `src/analysis/test_external_speculation_intelligence.py`,
que es su propio test. En producción no lo llama nadie.

### Vivo, y en la ruta de pujar

**`external_status.py`, `injuries.py` y `transfers.py` NO son código
muerto.** La cadena es:

```
autopilot.py:64
  -> intelligent_bid_engine.py:10
       -> external_status.py
            -> injuries.py
            -> transfers.py
```

Y no es una importación de adorno:
`intelligent_bid_engine.py:459` llama a
`get_external_player_status()` para cada candidato con
`action == "PUJAR"`, y su `risk_score` se resta del score
(`:494`). Está envuelto en un `try` cuyo comentario recuerda el
incidente del 16/08/2026 con la ø de Sørloth.

**El caché de 38 KB (`data/external_status_cache.json`) es de esa
cadena viva, no de la muerta.** Borrarlo dando por hecho que sobra
haría salir a la red en la ruta de pujar.

`market_trader_shadow.py`, que la auditoría no menciona pero que
`market_brain_shadow.py` importa, también está vivo por otro camino
(`v10_full_autonomous_live.py` → `controlled_speculation_live.py`).

### Qué se puede borrar sin miedo

Solo los dos primeros, y con ellos el test de uno:

```
src/analysis/market_brain_shadow.py
src/intelligence/speculation_intelligence.py
src/analysis/test_external_speculation_intelligence.py
```

Ninguno está en la puerta de validación, así que borrarlos no toca
CI. **No se ha hecho esta noche:** borrar código no arregla nada y
el encargo era arreglar cosas rotas.
