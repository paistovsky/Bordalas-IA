# POR QUÉ EL MOTOR COMPRA RELLENO

**Fecha:** 2026-09-20 (tercero del día) · **Rama:** `medir/por-que-relleno`, desde
`arreglo/la-verja-roja` · **Escrituras contra Biwenger:** ninguna · **Umbrales
tocados:** ninguno · **Interruptores encendidos:** ninguno · **Filtro del financiero:
sin tocar** · **`ROSTER_FILL`: sin tope puesto.**

**Verja: 160 de 160.** Las dos rojas cerradas.

---

## LA RESPUESTA, ARRIBA

> **El motor señala a los buenos.**

Con el filtro del financiero quitado, el tablero de fichajes ordena por valor y su
cabeza es un jugador de puntos los dos días que tengo foto: **Gerard Moreno (30 pts)**
y **Grimaldo (23)** el 18/09, **Julián Álvarez** y **Soler (19)** hoy. Y a los de
150.376 los valora en **cero**.

Pero eso no absuelve a nadie, porque **el tablero no es quien compró el relleno**. Lo
compró la cesta, y la cesta no elige: su cuenta de «ganancia por euro» da **el mismo
número, 0,0208, para un jugador de 150.000 y para uno de 24,9 millones**. Lo único
que desempata es quién no te lo va a disputar — que es siempre el más barato.

Y tu hipótesis del bloque 3 es falsa en los dos extremos: no fueron catorce sino
**ocho**, y no los compró `ROSTER_FILL`, que **no ha comprado nada en toda la
temporada**.

---

## BLOQUE 1 — LAS DOS ROJAS, CERRADAS

### `test_orden_de_venta_v1` → al mirador

Tu lectura era la buena. Ocho de sus diecinueve pruebas leían
`diagnostico/status.json`, que no está versionado, y una buscaba a **«Dituro» por su
nombre**. A las 08:55 lo vendimos (`transfer`, 2.188.300 €) y a las 09:16 la foto se
rehizo sin él.

Las ocho están ahora en **`scripts/mirar_el_orden_de_venta.py`**. La guardia se queda
con **11 puras, 11/11 en verde**.

Y había un segundo problema que no habíamos visto, peor que el primero:

```python
cola = _cola_de_produccion()
if cola is None:
    return          # <- las ocho empezaban asi
```

`diagnostico/` no existe en CI. **Las ocho pasaban sin mirar nada.** Rojos que no
eran fallos en el portátil, verdes que no eran nada en el servidor.

El mirador, corrido ahora mismo, sale **8/8 sin nada que mirar** — incluida la del
portero, que ahora pregunta por el **puesto** y no por el nombre. Dmitrovic se aparta
correctamente por ser portero. No había nada roto.

### `test_presupuesto_de_fichar_v1` → se arregló el patrón

Como decías: si el código se hizo más seguro con un `and`, se arregla el patrón. El
`IfExp` exigía que el test fuera **exactamente** `ast.Name("executable_buys")`, y
ahora acepta también un `BoolOp` con `And` que lo contenga.

Comprobado que **sigue pudiendo ponerse roja**, que es lo único que la hace valer:

```
sin guardia              -> FALLA (rojo)
guardia simple           -> PASA
guardia con and          -> PASA
and al reves             -> PASA
or (NO debe valer)       -> FALLA (rojo)     <- un `or` no cortocircuita
guardia de otra cosa     -> FALLA (rojo)
```

### Cuántas más se escaparon, y por qué

**Siete**, y todas por el mismo agujero. Las cinco que importan leen **el mismo
fichero**:

| guardia | qué lee | riesgo |
|---|---|---|
| `test_arbitro_v1` | `diagnostico/status.json` | cambia de color con la foto |
| `test_once_v1` | `diagnostico/status.json` | idem |
| `test_reloj_solvencia_v1` | `diagnostico/status.json` | idem |
| `test_venta_ejecutable_v1` | `diagnostico/status.json` | idem |
| ~~`test_orden_de_venta_v1`~~ | — | **movida hoy** |
| `test_el_ciclo_publica_v1` | `data/snapshot_*.json` (sólo comprueba que existan) | leve |
| `test_futbolfantasy_source_v12` | `data/ff_html`, `data/snapshot_*.json` | lee fotos de agosto |

**El motivo es que hay tres redes y `diagnostico/` se cuela por las tres:**

1. `las_dos_poblaciones()` (`regression_check.py:92`) decide por
   `get_latest_snapshot(`. Estas no la llaman.
2. `test_verja_determinista_v1` busca la ruta `data/` **escrita** en el código. Estas
   escriben `diagnostico/`.
3. `scripts/vigila_data/sitecustomize.py` —el vigilante en ejecución, que caza las
   lecturas transitivas— sólo mira `data/`:

```python
def _bajo_data(ruta) -> bool:
    return texto.startswith("data/") or "/data/" in texto
```

**No lo he tocado.** Ensanchar `_bajo_data` a `diagnostico/` es una línea, pero
cambia qué entra en el censo `LEEN_DATA_HOY` —que «sólo puede encoger»— y haría
aparecer cuatro entradas nuevas marcadas como no censadas. Eso lo decides tú. Si
dices que sí, es esa línea y actualizar el censo.

---

## BLOQUE 2 — `SPECULATION_SCORING`

### Dónde se corta

`src/analysis/decision_orchestrator.py`, líneas **2845-2849**:

```python
tablero_manda = bool(
    (acquisition_board or {}).get("available")
)

if tablero_manda and mejor is None:
    objetivo = None                      # <- AQUI
```

`fuente_objetivo` nace como `"SPECULATION_SCORING"` en la línea 2800 y sólo
**sobrevive** si `tablero_manda` es `False`. Y `build_acquisition_board` devuelve:

- `"available": True` en la línea **1443**, la salida normal;
- `"available": False` en la línea **1621**, dentro de su `except`.

> **`SPECULATION_SCORING` sólo puede producir un candidato cuando
> `build_acquisition_board` lanza una excepción. No es una vía: es un `except`.**

### Desde cuándo

Nunca pujó, y no dejó de hacerlo: **nació cerrada**.

| commit | fecha | qué hizo |
|---|---|---|
| `32c73ec` | **2026-08-16** | crea la vía: «Un solo motor de compra: el dashboard decide y el ciclo ejecuta» |
| `c8abe87` | **2026-08-16 20:56** | la cierra: «El respaldo no es una puerta trasera: sin objetivos no se compra» |

El comentario que dejó `c8abe87` sigue ahí y cuenta el caso exacto:

> «Pasó el 16/08/2026 a las 20:48: con las tres pujas buenas ya colocadas, el tablero
> se quedaba sin candidatos libres y el ciclo siguiente habría vuelto a la lista vieja
> para comprar algo que el analista había descartado. **El becario entrando por la
> ventana.** El respaldo existe para cuando el tablero FALLA, no para cuando dice que
> no.»

Ocho minutos entre nacer y quedar cerrada.

**Pujas suyas: cero.** `n` honesto: el libro atribuye vía desde el 05/09/2026 —antes
todo es `DESCONOCIDO`, reconstruido del tablón—, y sobre **19 operaciones
atribuidas**, ninguna es suya.

### ¿Sobra?

**No sobra, y tampoco es una vía. Es un `except`, y contarla como cuarta vía fue un
error mío de ayer.** Lo digo así porque el arreglo no es borrarla:

- Como respaldo tiene sentido: si el tablero revienta, es lo único que queda para no
  dejar a Pepe sin operar por un fallo de telemetría.
- Pero **nunca se ha ejercitado**. El camino que corre cuando el tablero se cae no ha
  corrido ni una vez en producción en 35 días. Eso no es peso muerto: es una salida de
  emergencia sin probar, que es otra cosa y da más miedo.

Lo que yo haría, y no hago: una guardia que le pase un `acquisition_board` con
`available: False` y compruebe que el respaldo elige algo sensato. Es barata y es la
única forma de saber si la puerta abre el día que haga falta.

**No la he borrado ni arreglado.**

---

## BLOQUE 3 — EL EXPERIMENTO

### Primero: no son catorce. Son ocho.

| | n |
|---|---:|
| compras de Pepe en el tablón (sin duplicar) | 36 |
| a **exactamente 150.376 €** | **8** |
| a ≤ 300.000 € | 10 |

Los 150.376 no son un misterio: son **150.000 × 1,0025 + 1**, que es
`puja_de_cartera()` con `IMPORTE_DE_CARTERA = 0,0025` sobre el suelo del mercado. Son
los jugadores que valen el mínimo.

### Por qué vía y con qué `intent` entró cada uno

| fecha | jugador | pagado | vía | `intent` | `win_prob` | ritmo %/día |
|---|---|---:|---|---|---:|---:|
| 12/09 | Fortuño | 150.376 | `SUBASTA_CARTERA` | SPECULATION | 0,46 | 0,000 |
| 12/09 | Diego Conde | 240.601 | `SUBASTA_CARTERA` | SPECULATION | 0,46 | 0,000 |
| 15/09 | Benavidez | 150.376 | `SUBASTA_CARTERA` | SPECULATION | 0,46 | 0,000 |
| 15/09 | Paco Cortés | 150.376 | `SUBASTA_CARTERA` | SPECULATION | 0,46 | 0,000 |
| 15/09 | Selu Diallo | 150.376 | `SUBASTA_CARTERA` | SPECULATION | 0,46 | 0,000 |
| 18/09 | Marcão | 150.376 | `SUBASTA_CARTERA` | SPECULATION | 0,46 | 0,000 |
| 18/09 | Barzic | 150.376 | `SUBASTA_CARTERA` | SPECULATION | 0,46 | 0,000 |
| 18/09 | Iturbe | 150.376 | `SUBASTA_CARTERA` | SPECULATION | 0,46 | 0,000 |
| 18/09 | Esquivel | 150.376 | `SUBASTA_CARTERA` | SPECULATION | 0,46 | 0,000 |
| 27/08 | Pablo Durán | 236.531 | sin libro (tuya) | — | — | — |

**Nueve de la cesta, uno tuyo. Ninguno `ROSTER_FILL`.** Y fíjate en las dos últimas
columnas: `win_probability` **0,46 en los nueve** y ritmo **0,000 en los nueve**. No
son medidas de esos jugadores: son el mismo número repetido.

### La hipótesis de `ROSTER_FILL`: falsa

`ROSTER_FILL` **no aparece ni una vez como `intent`** en el libro de pujas:

```
intents en el libro (47 filas):  None 17 · REVENDER 15 · SPECULATION 13 · XI_UPGRADE 2
```

Existe sólo como `deployment.value_route` —una **vía de valoración**, no un
propósito—. Valoró 7 candidatos el 18/09 y 12 hoy, y **no ha llegado a `BID` nunca**.

El caso más cercano lo desmiente del todo. El 18/09 el tablero decidió `BID` sobre
**Maffeo** con `value_route: ROSTER_FILL`, `intent: XI_UPGRADE`, puja **1.758.779**. Y
quien lo compró fue **el carril**, a las 05:23, por **1.664.350** con
`intent: REVENDER`. Otro importe y otro motivo: la decisión de `ROSTER_FILL` no llegó
a escribirse.

### ¿Tiene tope `ROSTER_FILL`?

**No, y ya estaba apuntado.** `src/analysis/el_proposito.py:18`, doctrina 69:

> «Ya ha mordido tres veces: `intent` se llevaba el tope de puja al quitarse,
> **`free_slots` abre `ROSTER_FILL` sin tope**.»

En `deployment.py:357` `ROSTER_FILL` sólo elige **escalón de prioridad**
(`FILL_AND_XI`, `FILL_AND_RISING`, `OTHER_SIGNING`). No hay tope de cuenta ni de
importe propio: lo que lo limita es el bolsillo de fichar (6.754.533 € hoy) y las
fichas libres (9 hoy, 3 el 18/09).

**¿Qué habría comprado con un tope? Nada.** Medido: cero compras por `ROSTER_FILL` en
toda la temporada. Un tope sobre cero es cero. **El tope no es la pieza que falta**, y
ponerlo habría sido arreglar algo que no está roto — que es exactamente lo que este
bloque existía para evitar.

### Entonces, ¿quién los eligió? Nadie. Y eso es lo grave.

La cesta ordena por `_por_euro` = `expected_value / bid`. En modo cartera:

```
expected_value = precio x (1 + prima_de_reventa) - precio x (1 + 0,0025) - 1
               ≈ precio x (prima - 0,0025)
```

El precio está **arriba y abajo**. Medido con la prima del Computer del 18/09
(+2,34 %):

```
      precio        puja   ganancia    por euro
     150.000     150.376      3.134    0.020841
     240.000     240.601      5.015    0.020844
     500.000     501.251     10.449    0.020846
   1.600.000   1.604.001     33.439    0.020847
   3.000.000   3.007.501     62.699    0.020848
   4.720.000   4.731.801     98.647    0.020848
  24.900.000  24.962.251    520.409    0.020848
```

> **La cuenta que ordena la cesta da el mismo número para un jugador de 150.000 y
> para Yamal.** Es constante hasta el quinto decimal en un rango de 166 veces.

Lo único que desempata es `win_odds`, la probabilidad de que nadie te lo dispute — y
esa sí varía, monótonamente, en contra del precio:

```
   150.000  odds 0.95  por euro 0.019799     <- el suelo
   500.000  odds 0.70  por euro 0.014592
 4.720.000  odds 0.30  por euro 0.006254
24.900.000  odds 0.10  por euro 0.002085
```

**«El mejor por euro» y «el más barato» son la misma frase en ese código.** Los nueve
del suelo no los eligió `ROSTER_FILL` ni nadie: son lo que sale cuando el criterio no
distingue y el desempate premia no tener rival.

Y encaja con los `win_probability: 0,46` idénticos de la tabla de arriba: en la cesta
no hay una puntuación por jugador que mirar, porque no la hay.

### La medición en seco

Sobre los dos días con foto, quitando el filtro del financiero y reordenando por
`our_value`:

**18/09 — 54 candidatos**

```
  decisiones: MERCADO_DE_RIVAL 34 · SIN_VALOR 8 · SUPERA_PRESUPUESTO 3
              RENDIMIENTO_INSUFICIENTE 3 · BID 2 · NO_COMPENSA 2
              PROBABILIDAD_INSUFICIENTE 1 · NO_DISPONIBLE 1

  SIN EL FILTRO DEL FINANCIERO, por valor:
  jugador              precio   pts  our_value   intent       decision
  Gerard Moreno     6.910.000    30  7.031.270   SPECULATION  SUPERA_PRESUPUESTO
  Grimaldo          4.880.000    23  4.965.644   SPECULATION  SUPERA_PRESUPUESTO
  Marc Casadó       3.630.000     7  3.693.706   SPECULATION  SUPERA_PRESUPUESTO
  Dmitrovic         4.770.000    31  3.491.573   SPECULATION  NO_COMPENSA
  Cabrera           3.040.000     8  3.220.400   XI_UPGRADE   BID
  Dumfries          4.810.000    18  2.831.270   SPECULATION  NO_COMPENSA

  a precio de suelo en esa misma lista:
  Egiluz              150.000     0     our_value 0   NO_DISPONIBLE
  Beitia              170.000     2     our_value 0   MERCADO_DE_RIVAL
```

**20/09 09:10 — 55 candidatos**

```
  decisiones: MERCADO_DE_RIVAL 35 · SIN_VALOR 8 · NO_COMPENSA 4 · NO_DISPONIBLE 4
              RENDIMIENTO_INSUFICIENTE 2 · SUPERA_PRESUPUESTO 1 · GANANCIA_INSUFICIENTE 1

  Julián Alvarez    7.100.000     3  7.224.605   SPECULATION  SUPERA_PRESUPUESTO
  Soler             4.330.000    19  2.504.193   SPECULATION  NO_COMPENSA
  Moncayola         2.480.000    19  2.307.435   SPECULATION  NO_COMPENSA

  a precio de suelo: Juanmi, Lobete, Diaby, Guliashvili, Guevara -> our_value 0
```

### La respuesta binaria, con esas palabras

> **Con los candidatos de vuelta en la lista, el motor señala a los buenos.**

El tablero de fichajes pone arriba a Gerard Moreno (30 pts), Grimaldo (23), Dmitrovic
(31) y Moncayola (19), y **valora a los de 150.000 en cero**. No sigue señalando al
relleno: no los señala en absoluto.

**Pero dos correcciones a la premisa, y las dos cambian el arreglo:**

**1. El financiero no tacha 124. Tacha 3 de 54 y 1 de 55.**
`nos_lo_podemos_permitir` **no filtra a nadie**, y lo dice su propio comentario
(`el_vestuario_libre.py:376`):

> «No filtra a nadie, y es a propósito: un jugador que hoy no podemos pagar puede ser
> justo a quien hay que vender algo para llegar. Sólo que se vea.»

Sus dos únicos usos en todo el repositorio son ponerlo y contarlo. Y los libres tipo
**Remiro o Leo Román no están tachados: no están en venta**. La foto de hoy:
`en_el_mercado_hoy: 0` sobre los 20 vigilados, y `vigilados_en_el_cuadro: 0`. No se
puede pujar por un jugador que el Computer no ha sacado.

**2. El corte grande no es el financiero: es el mercado de los rivales.**
**34 de 54 y 35 de 55 candidatos** —el **63 %** de la lista, los dos días— son
`MERCADO_DE_RIVAL`: jugadores que un rival ha publicado con recargo y que no pasarían
el listón. El tablero mira 20 plazas del Computer y 35 anuncios de rivales, y descarta
casi todos los segundos por precio.

### Entonces, ¿parche o proyecto?

**Ninguna de las dos, y por eso el bloque valía la pena.**

- **No es el financiero.** Quitarlo devuelve 3 candidatos, no 124. Es un parche que no
  cambiaría nada.
- **No hace falta una valoración nueva.** El tablero ya elige bien: pone los puntos
  arriba y el suelo a cero. La valoración funciona.
- **Lo que compró relleno es otra cosa**: `_por_euro` en modo cartera, una función de
  doce líneas cuyo resultado no depende del jugador. La cesta no está eligiendo mal;
  **no está eligiendo**.

No propongo el arreglo porque no me lo pides y porque tocarlo mueve dinero. Pero el
tamaño del problema es una función, no un proyecto.

---

## BLOQUE 4 — LA VERJA SE APUNTA SOLA

Hecho, y comprobado en las dos direcciones.

`run_validation_gate.py` deja su veredicto en `.verja/ultima.json` (ignorado por git,
no es un libro):

```json
{"cuando": "2026-09-20T08:32:01+00:00", "verdes": 160, "total": 160,
 "fallos": [], "parcial": false, "huella": "61e2a950..."}
```

Y `.githooks/prepare-commit-msg` pega una línea al final del mensaje:

```
Verja: 160/160 verdes. Corrida 2026-09-20T08:32:01+00:00.
```

**La huella es lo que hace que valga algo.** Es el SHA-256 de todos los `.py` de
`src/` y `scripts/` más los `.js` del panel, **con los finales de línea
normalizados** — el primer commit que la usó dijo «el árbol cambió después» porque un
`git checkout --` había reescrito un fichero con CRLF sin mover una instrucción. Era
la misma falsa alarma que este informe le reprocha a dos guardias, cometida al
construir el aviso. Corregida y vuelta a medir.

Probado tocando un fichero después de correr la verja:

```
Verja: 160/160 verdes — PERO EL ARBOL CAMBIO DESPUES: no vale. Corrida ...
```

Y sin veredicto:

```
Verja: NO SE CORRIO sobre este arbol.
```

Tres detalles con su motivo:

- **No bloquea el commit.** Un hook que impide guardar el trabajo se desinstala el
  primer día malo — es la misma razón por la que el vigilante de `data/` avisa y no
  tumba.
- **Una corrida con `--solo` o `--extra` se marca `parcial`**, para que el mensaje no
  pueda presumir de un verde que no es la verja entera.
- **No duplica la línea** si el mensaje ya la lleva, para poder rehacer un commit.

Se instala con `git config core.hooksPath .githooks` — ya está puesto aquí. **No se
instala solo a propósito**: un hook que se instala solo es un hook que nadie decidió.
Y no corre en CI, porque los hooks no viajan con el checkout.

---

## LO QUE NO HICE, Y POR QUÉ

- **No ensanché `_bajo_data` a `diagnostico/`.** Es una línea, pero cambia qué entra
  en el censo `LEEN_DATA_HOY`, que «sólo puede encoger». Decides tú.
- **No moví las otras cuatro guardias que leen `diagnostico/status.json`** — están
  verdes hoy y moverlas es la misma decisión de arriba.
- **No borré ni arreglé `SPECULATION_SCORING`.** Y no escribí la guardia que le
  pasaría un tablero caído: es trabajo nuevo, no medición.
- **No puse tope a `ROSTER_FILL`.** Medido que no habría cambiado nada: cero compras.
- **No toqué el filtro del financiero.** Medido en seco, como pedías.
- **No toqué `_por_euro`** aunque es donde está el problema. Mueve dinero.
- **No toqué la ventana, ni ensanché la cesta, ni apagué ninguna vía, ni encendí
  ningún interruptor, ni puse ningún número nuevo, ni toqué el workflow.**
- **Ni una escritura contra Biwenger.**
- **No pude probar que Cabrera fuera del tablero.** El 18/09 el tablero decidió `BID`
  sobre él a 3.134.660 con `intent: XI_UPGRADE`, y el libro registra una puja de
  **3.116.031** a las 15:18 con vía `DESCONOCIDO` e `intent: None`. Los importes no
  coinciden y no hay nada que ate las dos cosas. Si fuera la misma, `ACQUISITION_BOARD`
  serían 3 operaciones y tu vía 19. Es exactamente el agujero que dejó a la vista la
  guardia de ayer.

### La verja

```
160 de 160 OK      (eran 158 de 160)
```

Salida a fichero, árbol quieto, sin `git add -A`. **No empujo.**

### El `n`, y cuándo se cortó

| medida | `n` | corte |
|---|---|---|
| compras de Pepe en el tablón | **36** (sin duplicar) | tablón a 20/09 09:33 |
| compras a 150.376 exactos | **8** · 9 con Diego Conde | idem |
| operaciones con vía atribuida | **19** de 35 distintas | libro desde 05/09 |
| pujas de `SPECULATION_SCORING` | **0** de 47 filas | idem |
| `ROSTER_FILL` como `intent` | **0** de 47 filas | idem |
| candidatos del tablero | **54** (18/09) · **55** (20/09) | dos fotos |
| tachados por el financiero | **3** de 54 · **1** de 55 | idem |
| `MERCADO_DE_RIVAL` | **34** de 54 · **35** de 55 | idem |
| guardias que leen producción sin `get_latest_snapshot()` | **7**, una movida hoy | barrido de `src/**` |
| planitud de `_por_euro` | 5 decimales iguales en 7 precios de 150 k a 24,9 M | aritmética pura |

Dos días de foto es `n = 2` para el experimento en seco. La conclusión —el tablero
pone puntos arriba y el suelo a cero— sale igual los dos días y es coherente con que
los `our_value` del suelo sean **cero por construcción**, no por poco. Pero dos días
son dos días, y si mañana quieres el mismo corte con una semana, hay que guardar la
foto diaria: hoy sólo existe la del 18/09.
