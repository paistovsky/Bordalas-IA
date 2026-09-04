# Bordalás IA — repaso completo de la estrategia de Pepe

04/09/2026, sobre la foto de producción de las 19:34 y el código en disco.
Cuatro dominios auditados. Ordenado por lo que cuesta en puestos.

## Veredicto

**Pepe no está mal hecho: está mal cosido.** Cada pieza funciona por
separado y hace bien su trabajo. Lo que falla es el ensamblaje —hay
datos excelentes que no llegan a ninguna decisión, y puertas que se
cierran unas a otras hasta dejarlo quieto.

Medido: **84 vueltas de ciclo en 36 horas, 0 compras.** Sesenta y siete
de esas vueltas se fueron en "vigilar ofertas" sin escribir nada.

No tiene 47,7 M de plantilla por prudencia. Los tiene porque **la puerta
de fichar no se abre nunca y la de especular da a un mercado que no
rinde lo que se le exige**.

---

# 1. URGENTE: Pepe está congelado ahora mismo

```
speculation.enabled     False
speculation.budget      0
exposure.blocked_by     HARD_SAFETY
exposure.available      0
solvency.needed         False      <-- no hay problema de solvencia
solvency.deficit        0
```

**Presupuesto cero, y no porque falte dinero.** Ayer eran 8,56 M para
fichar y 3,56 M para especular. Hoy, cero.

Lo que cambió: **las tres pujas manuales del dueño comprometen
10.423.000 €**, contra un `maximum_bid` calculado de 5.006.140 € y una
caja de 3.399.140 €. Si ganara las tres quedaría unos 7 M en rojo, y el
guardarraíl de deuda segura reacciona apagando toda la operativa.

O sea: **poner pujas a mano ha dejado al bot sin capacidad de actuar.**
No es un fallo del bot —el guardarraíl hace exactamente su trabajo— pero
es un efecto que no estaba a la vista, y explica por qué hoy no hace
nada aunque le arreglemos los umbrales.

Nada de lo demás importa mientras esto siga así.

---

# 2. Lo estructural: por qué no ficha

## 2.1 No existe la operación "ampliar plantilla"

`acquisition_valuation.py:352-358`: a cada candidato solo se le compara
con **un** jugador — el titular más flojo de su posición. No hay vía
para fichar y punto.

```
Pepe        14 jugadores        Pollo17   17        Prinzipote  16
```

Si el veto salta, la fila cae a `intent = SPECULATION` y se la juzga con
el listón de la especulación. Hoy: **16 de 22 candidatos vetados** por la
regla del once.

*Arreglo mínimo:* permitir `replaces = None` cuando la plantilla tenga
hueco, y valorar el fichaje contra el hueco en lugar de contra un
titular. *Riesgo:* reabre el bucle de defensas que el comentario de la
línea 320 describe; se acota con el guardarraíl de posición que ya
existe.

## 2.2 El `intent` se elige por euros, no por tipo de operación

`acquisition_valuation.py:593`:

```python
mejor = max(opciones, key=lambda o: safe_int(o.get("value")))
```

Se calculan las tres vías —fichar, tradear, revender— y gana **la que dé
más euros**. Si la de fichar da 0, queda especulación, y entonces a un
fichaje se le exige rendimiento de reventa.

**El caso de hoy lo demuestra.** Expósito: Clave, 90 % titular, 196
puntos esperados, y Pepe lo rechaza con *"como especulación rinde un
0,59 % y se exige al menos un 3 %"*. Ni siquiera está mirando el fútbol.

## 2.3 Comprar puntos es negocio y nadie lo mira

```
EUROS_POR_PUNTO      = 30.000   (rival_intelligence_engine.py:54)
precio real del punto = 21.758   (status.json / points_market, mediana)
```

Comprar puntos rinde **~38 % en caja**, más los puntos de liga. El motor
calcula `pays_for_itself` y `cost_per_point`… y **no los lee nadie**.
Salen `null` en las 22 filas del tablero.

*Arreglo mínimo:* que `cost_per_point < 30.000` autorice la puja por sí
solo. *Riesgo:* pagar por puntos ya pasados — usar puntos esperados, no
`raw_points`.

## 2.4 Prohibido comprar cuando más falta hace

`decision_orchestrator.py:2525`: solo se compra en fase `NORMAL` o
`PREPARATION`. Eso **prohíbe comprar en las 12 h previas a cada
jornada** — justo cuando el mercado del Computer se resetea a las 07:00.

## 2.5 Los topes, con su coste

```
MAX_SPECULATION_BUDGET_PERCENT = 0.15   aparca el 85 % de la caja (2,97 M)
MAX_DEBT_SPECULATION_PERCENT   = 0.60   aparca el 40 % del margen seguro
MAX_SINGLE_SPECULATION_PERCENT = 0.40
MIN_SPECULATION_YIELD          = 0.03   contra un mercado que rinde 0,22 %
MIN_SPECULATION_EXPECTED_VALUE = 25.000 inalcanzable con el tope por operación
```

Y el que de verdad manda no es de Pepe: `maximum_bid = 5.006.140` = caja
+ 3,16 % del plantel. **Fichar depende de la caja, no del patrimonio.**
Por eso Luismi, con más caja, puede pujar 15,2 M y Pepe 5,0 M.

## 2.6 Concentración sin control

**Yamal son 21,12 M de los 47,72 M de plantilla: el 44 % en un solo
activo.** No hay ningún tope de porcentaje por jugador.

---

# 3. Los datos: buenos, y desaprovechados

## 3.1 Fallos que ensucian decisiones a diario

**`VIGILAR` no significa nada.** `player_availability.py:120-145` marca
VIGILAR si `fitness` no está vacío. Pero `fitness` es el array de puntos
recientes, no una lesión: *De la Fuente, status=ok, fitness=[4]*. **Los
11 del XI salen VIGILAR**, Yamal incluido. 205 de 569 jugadores. Es
ruido puro.

**El fallback rancio no comprueba la jornada.**
`futbolfantasy_provider.py:1409-1419`: si FF falla, se devuelve el
tablero anterior **sin revalidar `matchday`**. Esa comprobación solo
existe en la vía HIT. Y el auditor de consistencia lo da por bueno
contando cabezas. **Un tablero de la jornada 3 puede servir la 4 y salir
en verde** — que es exactamente el fallo del 16/08 volviendo por otra
puerta.

**Los penaltis son cero absoluto.** `penalty_kickers.json`: **39 de 39**
con `role: UNKNOWN` y `bonus: 0.0`. El `PRIMARY_BONUS = 8.0` que ordena
el XI **no se ha aplicado nunca**, y se gasta cuota de API-Football cada
24 h para no devolver nada.

**Las plantillas rivales están vacías.** `rival_squads.available: true`
pero `squad_size: 0` y `players: []` **en los siete**. Sale de
`standings[].lineup` (`squads.py:214-255`), que viene vacío, mientras
`ledger_audit` **sí** conoce los rosters (17/14/13/12). Dos fuentes, se
usa la vacía. Por eso la pantalla de plantillas no enseña nada.

**Un jugador sin pronóstico no se penaliza en la valoración.** Gustavo
Puerta sale con `expected_points: 156 = raw_points: 156`, el segundo más
alto del tablero, sin descuento por no tener dato de titularidad. El XI
sí está protegido; la valoración no.

## 3.2 Recogido, guardado… y sin un solo lector

- `avg_lost_bid` y `max_observed_bid` de cada rival — solo se pintan.
- Metadata entera de FF: `price_gaps`, `low_confidence`, `unmatched`,
  `no_slug`, `no_team`, `methods` — ningún lector.
- Por jugador: `minutes`, `form`, `market_flags.transferible/cedible`,
  `availability.booked`, `team_context.rotation`.
- **Cadenas de código muertas**: `speculation_intelligence.py` y
  `market_brain_shadow.py` no tienen importadores; arrastran
  `external_status.py`, `injuries.py`, `transfers.py` y un caché de 38 KB.
- El catálogo de Biwenger trae `pointsHome`, `pointsAway`, `playedHome`,
  `playedAway` en **los 569 jugadores**. El propio comentario de
  `player_value_engine.py:597` dice que el peso de local/visitante será
  medible "cuando haya puntos acumulados por local y visitante". **Ya los
  hay, desde el principio.**

## 3.3 El saldo de los rivales puede estar muy mal

```
Luismi_Haz   03/09: -10.135.606      04/09: +13.038.494
             maximum_bid estimado: 15.210.886
```

Veintitrés millones de diferencia en un día. Parte se explica por ventas
(su plantilla bajó de 81,2 a 68,8 M), pero no toda. Ese número es
**reconstruido**, no leído, y alimenta la `capacity` con la que se
calcula cuánto pujar y la probabilidad de ganar. Si está mal, las pujas
están mal dimensionadas.

## 3.4 El libro de acierto dice algo incómodo

Brier de la jornada 1: **FF 0.3365**, JP 0.4799, AF 0.3613. Un 0.25
sería apostar 50 % fijo a todo. Con n=17 no concluye nada, pero **FF
puntúa peor que no saber nada**, y es la única razón por la que sigue
corriendo el multifuente de tres scrapers.

---

# 4. Lo que no está modelado y debería

- **Horizonte de temporada.** Todo se decide a 3 días
  (`DEFAULT_SPECULATION_HORIZON = 3`) o a un ciclo. No existe "puntos ×
  30.000 € × jornadas restantes".
- **La brecha con el líder.** Nada en el código sabe que va 4º a 13
  puntos. Pujaría igual siendo primero. No hay agresividad condicionada
  a la posición.
- **El coste de la caja parada.** Se penaliza gastar mal, nunca no gastar.
- **El calendario más allá del próximo partido.** Hay 380 partidos en
  disco y solo se mira el siguiente rival, con peso 0,10. Rachas,
  congestión y jornadas dobles están sin tocar.

---

# 5. Orden de trabajo propuesto

1. **Desbloquear HARD_SAFETY.** Sin esto no hay nada que probar. Decidir
   qué hacer con las tres pujas vivas.
2. **`VIGILAR`** — un fallo de una línea que ensucia los 11 titulares.
3. **La jornada en el fallback rancio** — es el fallo del 16/08
   esperando a repetirse.
4. **Las plantillas rivales** — cambiar de fuente, de `standings[].lineup`
   a la que ya funciona.
5. **La vía de ampliar plantilla** — es la que más plantilla desbloquea.
6. **El `intent` por tipo de operación**, no por euros.
7. **`cost_per_point` como razón de compra por sí sola.**
8. **Los umbrales de especulación** (ya preparado y revertido: ver
   `estado-2026-09-03-rueda-de-trading.md`).
9. Penaltis, `pointsHome`/`pointsAway`, concentración por jugador.

Los cuatro primeros son fallos claros y baratos. Del quinto en adelante
son decisiones de estrategia, y ahí manda el dueño.

## No comprobado

- El `data/` local es del 17/08; producción vive en la caché de Actions.
  Todo lo citado sale de la foto de KV o del código.
- Si Biwenger permite más de 17 jugadores (no hay constante de tope en
  el código).
- Si Javi Hernández es un emparejamiento erróneo o solo un precio rancio
  de FF: método `NAME`, margen 0,586, desvío de precio del 45,7 %.
- Si `EUROS_POR_PUNTO = 30.000` es el abono real de esta liga.
