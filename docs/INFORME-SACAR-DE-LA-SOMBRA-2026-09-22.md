# INFORME — EL QUE DECIDE PUBLICAR ESTÁ EN LA SOMBRA

**Fecha:** 2026-09-22
**Rama:** `arreglo/sacar-de-la-sombra`, desde `main`
**Commit:** `8701f0e`
**Veredicto, corrido por mí:** paso 0 (los 23) **OK, exit 0** · verja **sin** el
interruptor **173/173 verde, exit 0** · verja **con** el interruptor **173/173 verde,
exit 0**. Con `data/` restaurado antes de cada una y después de la última.
**No se ha empujado. No se ha encendido ningún interruptor.**

---

## BLOQUE 1 — POR QUÉ ESTÁ EN SOMBRA

### La línea

```
src/analysis/sale_intent.py:321      "mode": "OBSERVACION",
src/analysis/sale_intent.py:398      "  OBSERVACION: no se publica ni se vende nada. "
```

**Pero esa línea no es lo que lo apaga.** Es una etiqueta. Lo que lo apaga es que **no
hay ejecutor**, y los dos módulos lo dicen de sí mismos:

```
sale_intent.py:23   "A proposito. No importa ningun executor, no escribe en disco y
                     no devuelve nada que un executor sepa ejecutar."
sale_order.py:52    "No importa ningun executor, no escribe en disco y no devuelve
                     nada que un executor sepa ejecutar."
```

Y en `main`, **el único que los leía era la pantalla**:

```
main:src/analysis/sale_order.py:91          sale_order importa untouchable_reason de sale_intent
main:src/telemetry/dashboard_state.py:4762  build_sale_order(...)   <- el unico lector
```

`sale_intent` se llama además en `autopilot.py:3917`, pero sólo para **imprimirlo** y
guardarlo en `result["state"]`. Ninguna ruta de decisión lo lee.

### ¿Había ya un interruptor? No. Ninguno.

Cero `os.environ` en `sale_intent.py` y en `sale_order.py`. **No hay nada apagado que
encender**: la puerta no se llegó a construir. Por eso tampoco hay motivo escrito que
leer antes de encenderla — lo que hay escrito es el motivo de **no construirla**, y sigue
siendo bueno:

> *«Vender mal no es como comprar mal. Una compra mala cuesta dinero y se corrige; una
> venta mala te deja SIN el jugador, y en un fantasy no se recupera: se lo lleva otro.»*

### ¿Ha publicado alguna vez? **No, ni una.**

`data/intelligence/libro_de_publicacion.jsonl`: **n = 45 entradas, 29 jugadores
distintos, del 11/09 al 22/09**, repartidas casi todos los días (10 el 19/09, 7 el
21/09, 2 el 22/09).

**Pero ese libro no dice quién publicó.** Es un cuaderno de observación y lo dice su
propia cabecera: apunta *«la PRIMERA vez que se ve a un jugador listado, y nada más»*, y
*«ESTE MODULO NO DECIDE NADA. Es un cuaderno.»* Nació el 10/09 para poder medir cuánto
lleva listado alguien cuando llega una oferta.

O sea: hay 45 apuntes de publicaciones que **ocurrieron**, y ninguna la hizo el motor de
intención — porque el motor de intención no tiene con qué.

---

## BLOQUE 2 — QUIÉN PUBLICÓ A LOS CATORCE

**El motor de solvencia**, por la acción `LIST_FOR_LIQUIDITY`:

```
liquidity_manager.py:1304      to_list = [p for p in roster if p["listing_action"] == "LIST_FOR_LIQUIDITY"]
decision_orchestrator.py:1589  player = to_list[0]
autopilot_executor.py:461      if action == "LIST_FOR_LIQUIDITY":  ->  writer.list_player_for_sale(..., execute=True)
```

Una publicación por vuelta, siempre `to_list[0]`.

### Y el criterio con el que elige es: **ninguno**

`to_list` sale de recorrer **la plantilla en el orden en que la devuelve Biwenger** y
quedarse con los que todavía no están listados:

```python
"listing_action": ("NO_ACTION" if currently_listed else "LIST_FOR_LIQUIDITY")
```

No hay puntuación, ni cola, ni filtro. **Todo el que no esté ya publicado es candidato, y
el que sale es el primero que se cruza.**

### Tu sospecha, desmentida — y lo que hay es peor

Sospechabas que *«publica lo que genera oferta, y el Computer solo ofrece por lo que vale
algo»*. **No es eso: no mira nada.** Medido sobre la foto de plantilla del 19/09
(n=19 fichas):

```
jugador            once   listado          accion              estrategia      proteccion
Yamal              True     True        NO_ACTION   LIQUIDITY_ONLY_PROTECTED  NEVER_AUTO_SELL
Jutglà             True    False  LIST_FOR_LIQUIDITY         LIQUIDITY_ONLY   NORMAL
Djené              True    False  LIST_FOR_LIQUIDITY         LIQUIDITY_ONLY   NORMAL
Cabrera            True    False  LIST_FOR_LIQUIDITY         LIQUIDITY_ONLY   NORMAL
Pablo Ibáñez       True    False  LIST_FOR_LIQUIDITY         LIQUIDITY_ONLY   NORMAL
Rubén García       True     True        NO_ACTION            LIQUIDITY_ONLY   NORMAL
...
Marcão            False     True        NO_ACTION              VENTA RÁPIDA   SELLABLE
```

- **Los once titulares llevan `listing_action`.** Siete ya listados, cuatro pendientes.
- **`to_list[0]` de hoy es JUTGLÀ**, que está en el once. Es lo que se publicaría en la
  próxima vuelta con saldo negativo.
- **Yamal, `NEVER_AUTO_SELL`, está publicado A PROPÓSITO.** No se coló: hay una
  estrategia entera para él, `LIQUIDITY_ONLY_PROTECTED`, y una constante con su
  comentario ([liquidity_manager.py:38](src/analysis/liquidity_manager.py#L38)):

> ```python
> # Para jugadores que estratégicamente NO queremos vender,
> # los publicamos igualmente por liquidez, pero con un precio
> # público alto.
> PROTECTED_LISTING_MULTIPLIER = 1.50
> ```

**Así que el criterio no está invertido: está ausente, y encima hay una regla escrita que
publica al intocable a posta.** Publicamos lo que queremos conservar porque nada lo
impide, y guardamos lo que queremos soltar porque no le ha llegado el turno.

Recuento sobre esa misma foto: **7 de 11 del once publicados** y **5 de 8 de fuera del
once publicados**. Los porcentajes son casi iguales (64 % y 63 %) — que es exactamente lo
que se espera de un procedimiento que no distingue.

---

## BLOQUE 3 — EL CORTE, DETRÁS DE UN INTERRUPTOR APAGADO

### `BORDALAS_PUBLICAR_LA_COLA` — apagado

`src/analysis/el_que_publica.py`. Con el interruptor puesto, `to_list` sale **en el orden
de la cola de `sale_order`** y **el once no se publica**.

**No reordena y no inventa criterio.** El orden es el de la cola, que ya lleva sus
escalones, sus intocables, el suelo por posición y el tope de concentración. Lo único que
añade es el corte, y usa `in_lineup`, que **ya viaja en cada fila** de la cola y nadie
miraba al publicar.

### Por qué hace falta el corte aunque la cola esté bien

Porque **la cola de VENDER termina en titulares** — y hace bien, vender al octavo de la
cola es sensato. Publicar no lo es:

```
18/09   cola de 9   ->  puestos 8 y 9: Expósito y Rubén García, los dos en el once
20/09   cola de 6   ->  puestos 5 y 6: los mismos dos
```

Y tu razón: publicar a un titular invita a una oferta del Computer sobre él, y entonces
la decisión de venderlo la toma la oferta y no nosotros.

### La tabla contrafactual

Sobre la **foto de plantilla del 19/09 18:18** (n=19 fichas), que es la única que tiene
`to_list` reconstruible:

```
                                        hoy            con el interruptor
publicaciones que se habrian hecho       7 en cola      3 en cola
de esas, cuantas eran del ONCE           4              0
la primera (to_list[0], la que se ejecuta)  JUTGLÀ (once)   MAFFEO
lo que habriamos publicado           13.790.000        3.360.000  (mercado)
   al +-5 % del Computer                              3.292.000 a 3.528.000 EUR
```

Los tres que quedan, en su orden: **Maffeo** (1.640.000), **Pablo Durán** (360.000),
**Álvaro Carreras** (1.360.000). Los cuatro frenados: **Jutglà, Djené, Cabrera y Pablo
Ibáñez**, los cuatro del once.

Sobre los **tres días con `status.json` en el árbol** (14, 18 y 20/09):

```
foto          cola   se publican   del ONCE   valor
2026-09-14       0             0          0       0
2026-09-18       9             0          0       0
2026-09-20       6             0          0       0
```

Cero, y no por el corte: **esos días el lastre ya estaba publicado** —Boyomo, Dituro,
Pablo Durán, Marcão, Barzic, Álvaro Carreras, Iturbe— y lo único que quedaba en la cola
eran los dos titulares, que el corte para. Es el caso bueno: no hay nada que hacer y no
se hace nada.

**El segundo renglón es CERO en las cuatro fotos.**

### Lo que cuesta

11,87 s → **12,14 s** por vuelta de `build_liquidity_state` (n=19 fichas, foto del
19/09). **Y sólo se paga con el interruptor puesto**: apagado, la función sale por la
primera línea sin calcular la cola. `build_lineup` —el 94-95 % del coste del ciclo, 4,78 s
con 21 fichas— **no se vuelve a llamar**: el once se lee del tablero ya construido.

### La guardia

**`test_el_que_publica_no_publica_titulares`** — con el interruptor puesto, un jugador del
once no entra en la cola de publicación. **Muerde si en el caso no hay ningún titular**
(no habría nada que frenar) **y también si no hay nadie fuera del once** (entonces no
probaría que el corte distingue, sólo que apaga). Comprueba además que los de fuera del
once **sí** entran, y en su orden.

Ocho más: que el orden sea el de la cola y no otro; que apagado no cambie nada; que al que
ya está publicado no se le republique; que sin cola no se invente un orden; que al que la
cola no conoce se le ponga **detrás** y no se le pierda; que `to_list` salga ordenado del
motor de liquidez —ejercitando el motor, no leyendo el mapa—; que la forma no cambie con
los datos; y que el módulo no lea el mundo.

---

## BLOQUE 4 — LA COLA CONTRA EL CUPO DE UNA ESCRITURA

### ¿Sobrevive entre vueltas? **No. Se recalcula entera, y cambia.**

No hay fichero de estado ni cola persistida: `build_liquidity_state(snapshot)` se
reconstruye cada vuelta desde la foto. Medido sobre las dos fotos del árbol:

```
18/09   Boyomo, Dituro, Pablo Durán, Marcão, Barzic, Álvaro Carreras, Iturbe, Expósito, Rubén García
20/09   Jonny, Iturbe, Álvaro Carreras, Pablo Durán, Expósito, Rubén García
```

En dos días la cabeza cambió de Boyomo a Jonny. Lo que la mueve: el precio (`momentum`
manda dentro de cada escalón), el once del día, y quién ha entrado o salido del mercado.

**Consecuencia para el cupo:** publicar al primero de la cola cada vuelta **no garantiza
recorrerla en orden**, porque la cola de mañana puede no empezar donde acabó la de hoy.
Lo que sí garantiza es publicar siempre al que la cola considera más urgente **ese día**,
que es lo que se pidió.

### ¿Contra quién compite? Con el número

`LIST_FOR_LIQUIDITY` recibe la prioridad de solvencia, que con saldo negativo y fase
NORMAL es **`SOLVENCY_NORMAL = 500`** (sube a 780, 960, 1010 o 1100 según aprieta el
reloj).

```
PIERDE contra                                     GANA a
  LINEUP_* ........................ 700 a 1000      SPECULATION_BUY ....... 400
  MARKET_LISTING_RENEW_URGENT ............. 690     MARKET_LISTING_RENEW .. 350
  ACCEPT_EXPIRY_URGENT .................... 680     SPECULATION_WATCH ..... 300
  COMPUTER_OFFER_REROLL_WATCH ............. 670
  ACCEPT_EXPIRY_WATCH ..................... 665
  INCOMING_OFFERS ......................... 650
  LIQUIDITY_MAINTENANCE ................... 550
```

### La pregunta incómoda: **sí puede retrasar una renovación. No puede perderla.**

Publicar (500) **adelanta a renovar** (350). Así que sí: una vuelta puede irse en publicar
a un suplente de 150.000 mientras una publicación buena espera su renovación.

**Pero no se pierde, y el número lo dice.** Una publicación vive 48 h, y a menos de
`RENEW_URGENT_HOURS = 3.0` del final sube a `MARKET_LISTING_RENEW_URGENT = 690`, que le
gana a publicar. Con vuelta horaria, eso son **tres vueltas seguidas en las que renovar
gana siempre**. Para perder una publicación habría que perder las tres, y no hay forma:
en esas tres, publicar está 190 puntos por debajo.

El coste real, entonces, no es perder el anuncio: es **renovarlo más tarde de lo que se
habría renovado**. Y hay un matiz que lo reduce más: en el ciclo en vivo la renovación de
la ventana (`_renovar_en_la_ventana`) corre **antes** del cupo y **no consume la
escritura**, así que en la ventana del reset no compite con nada.

---

## LO QUE SE HA TOCADO

```
src/analysis/el_que_publica.py             NUEVO   la cola de publicar, y el corte
src/analysis/test_el_que_publica_v1.py     NUEVO   9 guardias
src/analysis/liquidity_manager.py                  `to_list` en el orden de la cola
scripts/run_validation_gate.py                     la guardia en la verja
config/paso_0.json                                 lo reescribe el propio paso 0
```

---

## LO QUE NO SE HA HECHO, Y POR QUÉ

| | por qué |
|---|---|
| **Ni una escritura contra Biwenger** | lo prohíbe el encargo |
| **Ningún interruptor encendido** | el nuevo nace apagado; con él quitado `to_list` sale exactamente como hoy, y hay guardia de eso |
| **El workflow, intacto** | lo prohíbe el encargo |
| **No se ha cambiado el criterio de la cola de venta** | no se toca `sale_order`: se **lee**. El único criterio añadido es el corte del once, con `in_lineup`, que la cola ya publicaba |
| **No se publica «a todos»** | se publica `to_list[0]`, uno por vuelta, como hoy |
| **No se ha subido el cupo** | sigue siendo una escritura por vuelta: siete publicaciones siguen siendo siete vueltas |
| **No se ha tocado** `MAX_SINGLE_SPECULATION_PERCENT`, `MAX_SAFE_DEBT`, el suelo de cobro, `MIN_WIN_PROBABILITY`, `MAX_PROJECTED_DAILY_RATE`, `PUEDEN_ENCERRARLO`, `PRIMA_MAXIMA_DE_PUJA`, `VENTANA_MINUTOS` | lo prohíbe el encargo |
| **No se ha empujado** | «Tú no empujas» |
| **No se ha tocado `PROTECTED_LISTING_MULTIPLIER = 1.50`** | es la regla que publica a Yamal a posta. Cambiarla es cambiar un criterio de venta, y el encargo dice que no. **Queda dicho: mientras esté, el intocable se sigue publicando cuando le toque** — el corte del once lo tapa hoy porque Yamal está en el once, pero el día que no lo esté, vuelve a salir |
| **No se ha enchufado `sale_intent`** | su cola de `PUBLICAR_EN_MERCADO` y la de `sale_order` son la misma decisión contada dos veces. Se ha enchufado **una**, la que tiene orden y motivo por puesto. Juntarlas o retirar una es otra decisión |
| **No se ha medido si publicar el lastre genera oferta** | haría falta publicarlo. Doctrina 101 |

---

## DOS AVISOS

**1. Doctrina 108 — `arreglo/la-puja-que-vuelve` sigue sin fusionar.** El corte de la
reventa (`BORDALAS_SIN_REVENTA`) y el cupo por ventana (`BORDALAS_CUPO_POR_VENTANA`) **no
existen en `main`**, así que no están en esta rama ni en producción. Las otras dos —
`medir/los-49-de-pollo` y `arreglo/las-dos-que-se-rompen`— sí están dentro.

**2. `test_el_ciclo_publica_v1` sigue ensuciando cinco libros** (`marcador.json`,
`libro_de_publicacion.jsonl`, `libro_en_la_sombra.jsonl`, `bitacora_del_saldo.jsonl`,
`board_events.json`) en cada corrida de la verja. Restauré `data/` antes de cada uno de
los tres veredictos y después del último. Sigue sin arreglar y sigue sin estar en ningún
encargo.
