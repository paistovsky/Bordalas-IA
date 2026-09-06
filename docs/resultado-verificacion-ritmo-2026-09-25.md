# VERIFICACIÓN DEL RITMO, LA FUSIÓN Y EL PLAN DEL FILTRO

**2026-09-25.** Rama `gire/quitar-los-tres-tapones`.

---

# 1. Tu sospecha: refutada en la mecánica, acertada en el fondo

**El mecanismo que propones no es:** `priceIncrement` **no** sale del descuento
del vendedor.

**La prueba que lo decide:** de los **517 jugadores que NO están a la venta**,
**348 (67 %) tienen `priceIncrement` distinto de cero**, con valores de hasta
±18,25 %. Si viniera de una lista de venta, un jugador sin lista no podría
tenerlo.

```
Diomande         precio 11.060.000   increment  −330.000  = −2,98 %
Audero           precio  4.920.000   increment  −290.000  = −5,89 %
Pablo García     precio  2.250.000   increment  +290.000  = +12,89 %
```

## Pero la coincidencia que viste es real, y tiene explicación

| Jugador | Precio | Increment | Pedido | Precio − pedido | ¿Coinciden? | Vendedor |
|---|---:|---:|---:|---:|---|---|
| **André Almeida** | 1.180.000 | 190.000 | 990.000 | **190.000** | **SÍ** | Luismi_Haz |
| **Ejuke** | 3.050.000 | 130.000 | 2.920.000 | **130.000** | **SÍ** | Luismi_Haz |
| Baena | 9.740.000 | 140.000 | 10.692.000 | −952.000 | no | Manzagool |
| Tete Morente | 680.000 | 20.000 | 1.420.000 | −740.000 | no | Pollo17 |
| Marc Roca | 3.190.000 | 40.000 | 3.696.000 | −506.000 | no | Manzagool |

**Coinciden en los dos de Luismi y en ninguno más.** No es un artefacto del
sistema: es que **Luismi lista al precio del día anterior**, y el precio subió
por la noche justo ese incremento. Dos jugadores, un vendedor, un hábito.

---

## Y sin embargo tenías razón, en el sitio de al lado. El hallazgo de anoche se cae.

**Producción no usa `priceIncrement` para el ritmo.** Lo saca del consenso del
ojeador —`consensus.mean_magnitude_percent` de tres fuentes— **y con su racha**
(`trend_days`). Está en `market_rate_gate.py`.

**El que usó el campo equivocado fui yo, anoche, en la sonda.** Calculé
`priceIncrement / precio` y lo llamé "ritmo diario", **sin mirar la racha**. Y
eso rompe la tabla de dos maneras:

**Primera: un salto de un día no discrimina nada.** Sobre los 578 del catálogo:

```
|increment| / precio, en UN día
    mediana   0,78 %
    p75       1,59 %
    p90       2,98 %
    p95       4,76 %
    máximo   18,25 %

    el 42 % de la liga se mueve más de un 1 % en un solo día
```

**Mi filtro de "más del 1 % diario" lo pasan cuatro de cada diez jugadores
cualquier día.** No es una señal, es una moneda.

**Segunda, y peor: para los cinco de rivales no hay ritmo ni racha en absoluto.**
Como el tablero no los mira, el ojeador nunca les calcula nada:

| Jugador | Ritmo del ojeador | Racha |
|---|---|---|
| André Almeida | **no está en el tablero** | — |
| Ejuke | **no está en el tablero** | — |
| Tete Morente | **no está en el tablero** | — |
| Baena | **no está en el tablero** | — |
| Marc Roca | **no está en el tablero** | — |
| Gorosabel | 2,381 % | 5 días |
| Roro Riquelme | 1,179 % | **51 días** |
| Amatucci | 1,090 % | **20 días** |

**Así que no puedo decir que André Almeida sea material de rueda.** Solo sé que
su precio pegó un salto un día, medido con el campo que no toca.

## Qué se cae y qué queda en pie del informe de anoche

**SE CAE:** la tabla de los ocho, el «+16,10 % diario» de André Almeida, y con
ella la frase final del informe. **No hay ocho oportunidades esperando**; hay
ocho jugadores que subieron ayer, que es lo que le pasa al 42 % de la liga.

**QUEDA EN PIE, y no depende de ningún ritmo:**

- el escaparate son **47 comprables, no 20** — es un recuento del mercado;
- **27 los venden rivales y el filtro los esconde**, citado del propio código;
- y ahora, además, **para esos 27 no existe ni ritmo ni racha**, porque nadie se
  los calcula. Eso hace el plan del punto 3 más necesario, no menos: sin quitar
  el filtro no se puede ni siquiera saber si valen algo.

**Es la quinta de la familia «un dato haciéndose pasar por otro», y esta vez fue
mía y en el informe, no en el código.** Las cuatro anteriores —`in_lineup` /
`is_starter`, `store_depth` sin `retention_days`, `hold_value` con claves de
menos, `raw_points`— estaban en el código y tienen guardia. Ésta no la habría
cazado ninguna guardia, porque el error estaba en la sonda que escribí para
mirar, no en lo que se ejecuta.

*(No pude contrastar contra `price_history.json` como pedías: el almacén local
tiene seis días de agosto —del 12 al 17— y estos precios son del 24 de
septiembre. No se solapan. La verificación se hizo contra el catálogo en vivo,
que es lo que sí tiene los dos campos.)*

---

# 2. Las dos ramas, fusionadas en local

**Hecho. `main` está listo para que el dueño solo empuje. Sin push.**

```
7d44fb5  Merge gire/quitar-los-tres-tapones      ← main
906b8d1  Merge balon-parado/quien-tira-los-penaltis
40ab7b1  calidad: encenderla                     ← donde estaba main
```

**En el orden que dijiste:** primero el balón parado —limpia, sin un solo
conflicto—, luego `gire`, que arrastró `rueda` entera.

## Los conflictos: uno, no dos

Predije dos. **Solo hubo uno**, y es el que menos importaba:

| Fichero | Predicho | Real |
|---|---|---|
| `scripts/run_validation_gate.py` | conflicto | **sí** — resuelto con las dos partes |
| `src/analysis/acquisition_valuation.py` | conflicto | **no** — git lo fusionó solo |

El de la lista de pruebas queda con las tres entradas, ninguna perdida:

```python
    "src.analysis.test_balon_parado_v1",   ← de balón parado
    "src.analysis.test_rueda_v1",          ← de gire
    "src.analysis.test_que_gire_v1",       ← de gire
```

En `acquisition_valuation.py` git acertó porque los dos cambios están a 880
líneas de distancia. **Verificado a mano que sobreviven los dos**:
`last_season_points` en la línea 277 (balón parado) y *"como tenerlo mientras
sube"* en la 1167 (gire). No me fío de un auto-merge silencioso en el fichero que
decide las compras.

## La verja entera sobre el resultado

```
Los 93 en verde. Se puede subir.
```

**93, no 92**: la fusión suma la guardia del balón parado a las 92 de anoche. Es
la primera vez que las dos ramas corren juntas, y era lo único que esta fusión
podía romper de verdad.

---

# 3. Plan para quitar el filtro del mercado de rivales

**Sin ejecutar.** Esto es para revisar antes de tocar nada.

## Qué es el filtro hoy

En `acquisition_board.py`, un jugador listado por otro manager solo entra en el
tablero si **ya hay dinero nuestro dentro** (puja viva o contraoferta):

```python
if (fuera_del_computer
        and player_id not in puja_viva
        and player_id not in contra_oferta):
    continue
```

Efecto medido: **27 de 47 comprables invisibles**, y sin ritmo ni racha porque
nadie se los pide al ojeador.

## En qué se diferencia pujar a un manager de comprarle al Computer

Esto es lo que hace que no sea un cambio de una línea.

| | Computer | Manager |
|---|---|---|
| **La compra** | Al precio pedido, se ejecuta | **Es una OFERTA: la acepta o no** |
| Competencia | Otros managers pujan a ciegas | Igual, y además el dueño elige |
| Plazo | Cierra en el ciclo del Computer | Lo marca el vendedor |
| Dinero comprometido | Bloqueado hasta resolver | Igual |
| **La salida** | — | — |
| Revender al Computer | **+1,76 %, 73,6 % de las veces** | **Lo mismo: el jugador ya es nuestro** |

**Tú lo dices bien y conviene subrayarlo: la salida garantizada sigue valiendo.**
Una vez el jugador es nuestro, da igual a quién se lo compramos. **Lo que no está
garantizado es la entrada.**

Y de ahí salen las tres diferencias que sí importan:

1. **Una oferta rechazada inmoviliza dinero para nada.** Con el Computer, pujar y
   no llevárselo también, pero ahí la probabilidad la modela `rival_bid_model`
   sobre 48 pujas. Contra un manager **no tenemos ninguna medición**: en 67 horas
   de tablón hubo **una sola venta entre managers, y era nuestra**.
2. **El vendedor ve quién puja.** Contra el Computer somos anónimos. Contra
   Pollo, cada oferta le dice qué estamos buscando — y es el líder.
3. **El precio pedido puede ser una trampa o un regalo, y no sabemos cuál.**
   Manzagool pide 10.692.000 por Baena, que vale 9.740.000: un 9,8 % por encima.
   Luismi pide 990.000 por André Almeida, que vale 1.180.000: un 16 % por debajo.
   **Sin saber por qué, las dos son igual de sospechosas.**

## El plan, en cuatro pasos y en este orden

**Paso 1 — Verlos, sin poder comprarlos.** Levantar el filtro solo para
*publicar*: que los 27 entren en el tablero marcados `seller: MANAGER` y con
`decision: NO_EVALUADO`. Que el ojeador les calcule ritmo y racha, que es lo que
hoy no existe.

*Guardias:* que ningún jugador de manager pueda salir con decisión de compra en
este paso; que el recuento publicado del escaparate distinga las dos fuentes.

**Coste: bajo. Valor: alto.** Después de una semana sabremos si de verdad hay
material ahí fuera, medido con el ritmo bueno y no con un salto de un día.

**Paso 2 — Medir la tasa de aceptación.** Antes de pujar en serio hace falta
saber cuántas ofertas a managers se aceptan. Hoy la muestra es **una**. Se puede
empezar apuntando en un libro de acierto —como el de rechazos— cada oferta que se
haga y en qué acaba.

*Guardia:* que la vía no se encienda con menos de N observaciones, con N escrito.

**Paso 3 — Un listón propio, más alto.** Una compra al Computer que sale mal
cuesta el margen. Una oferta a un manager que sale mal cuesta el margen **más el
dinero inmovilizado mientras decide** más la información que le regalamos. El 3 %
no vale aquí tal cual; hace falta un número medido en el paso 2.

**Paso 4 — Entonces sí, comprar.** Y con el mismo interruptor de una línea que
todo lo demás.

## Lo que NO haría

**No levantaría el filtro y encendería la compra a la vez.** Es exactamente el
patrón que nos ha costado los cinco fallos de la familia: dar por bueno un dato
que no se ha mirado. Aquí el dato que falta es *la tasa de aceptación*, y sin ella
el paso 4 es una apuesta.

**No usaría el precio pedido como señal de oportunidad** hasta entender por qué
Luismi lista por debajo del mercado. Hoy sabemos que lista al precio del día
anterior; lo que no sabemos es si eso es un descuido suyo o si el precio va a
volver a bajar.
