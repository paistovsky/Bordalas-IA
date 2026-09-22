# INFORME — LA PUERTA QUE QUEDA: ¿VALE LO QUE DICE QUE VALE?

**Fecha:** 2026-09-22
**Rama:** `medir/la-valoracion`, desde `main`
**Commit:** `50cbc4b`
**Veredicto, corrido por mí:** paso 0 (los 23) **OK, exit 0** · verja **sin** el
interruptor **173/173 verde, exit 0** · verja **con** el interruptor **173/173 verde,
exit 0**. Con `data/` restaurado antes de cada una y después de la última.
**No se ha empujado. No se ha cambiado la valoración. No se ha encendido nada.**

---

## **EL VEREDICTO, CON TODAS LAS LETRAS**

**El motor no se queda corto por un factor. Mide en la moneda equivocada.**

No es «el mercado no ofrece nada» y tampoco es «hay que multiplicar por 1,8». Es que
`xi_upgrade_value` valora un fichaje con **lo que el mercado cobra por un punto**
(`tarifa` ≈ 18.300 €), cuando lo que decide si un fichaje compensa es **lo que un punto
nos paga**, que está medido en el árbol y vale **30.000 €**
(`caja_de_la_liga.EUROS_POR_PUNTO`, del `roundFinished`).

Y el módulo que ya dice esto —`los_dos_techos`, *«el techo del que se queda: otra moneda
entera»*— **existe, está medido, y no se calcula nunca**: sale `available: False` en las
**54 filas** de la foto del 18/09 porque nadie le pasa las jornadas que quedan.

Doctrina 99 otra vez, y esta vez la puerta cerrada es la buena.

---

## BLOQUE 1 — DE QUÉ ESTÁ HECHO EL VALOR DE FICHAJE

### La fórmula

`src/analysis/player_value_engine.py:1548-1553`

```python
delta  = puntos_esperados × factor_calendario
         − puntos_del_sustituido × factor_calendario     (:1447-1465)
justo  = delta × tarifa                                   (:1548)
maximo = justo × (1 − margin) × confidence + recovered    (:1550-1552)
```

### Cada peso, marcado

| entra | valor | de dónde sale |
|---|---|---|
| **`tarifa`** | ≈ 18.300 €/punto | **MEDIDO** — mediana de `price / pointsLastSeason` sobre el catálogo entero (`:205-244`), con `MIN_POINTS_SAMPLES` de suelo |
| **`margin`** | **0,10** | **A OJO.** El comentario lo dice él mismo: *«lo que queda aquí es solo el colchón por incertidumbre»* (`:114-128`). No hay medición detrás. Doctrina 90 |
| **`confidence`** | 1,00 / 0,55 / 0,75 | **HEREDADA** de la fuente de los puntos (`:61-103`). El 0,75 de «sin señal de titularidad» está razonado, no medido |
| **`recovered_value`** | **0** por defecto | **A OJO**, y declarado: *«lo prudente es suponer que se queda de suplente y no entra caja»* (`:1200-1202`) |
| **calendario** | tope ×1,10 | **MEDIDO**, con su razón escrita (`:395-398`) |
| `STARTER_SWAP_MARGIN` | 0,25 | **A OJO** — *«se pide más del doble»* (`:433-436`) |
| `STARTER_SWAP_MIN_DELTA` | 8 puntos | **A OJO** — *«sin esto, un cambio de +1 punto pasaría el filtro por pura aritmética»* (`:438-440`) |
| `HIERARCHY_VETO_STEPS` | 2 | **HEREDADO** de la escalera de FutbolFantasy (`:401-409`) |

**De siete entradas, dos están medidas y cinco están puestas a ojo** — todas con su razón
escrita, que es más de lo que suele haber, pero ninguna con un número detrás.

### ¿Contra qué precio se compara?

**Contra el precio de mercado de Biwenger**, `player["price"]`
([acquisition_valuation.py:378](src/analysis/acquisition_valuation.py#L378)), pasado a
`classify_operation` como `price` y comparado ahí:

```python
compensan = [via for via in fichaje
             if safe_int(via.get("value")) > safe_int(price)]     deployment.py
```

No es lo que pediría un vendedor (eso es `asking_price`, y esas filas salen como
`MERCADO_DE_RIVAL`), ni lo que pujaríamos (`bid`, que es precio ×1,0025). **Para el
mercado del Computer, precio de mercado ≈ lo que pagamos**, así que la comparación está
bien planteada en ese eje.

### ¿Se ha calibrado alguna vez contra un resultado real?

**No. Nunca. Ni una vez.** Dicho con esas palabras, como pediste.

El repositorio tiene un libro de aciertos para el ojeador
(`source_accuracy_ledger.json`), otro para las predicciones de precio
(`scout_accuracy_ledger.json`, 31 MB), otro para las pujas
(`bid_outcome_ledger.json`) y otro para las publicaciones. **Para la valoración de
fichajes no hay ninguno.** No existe un sitio donde se apunte «el motor dijo que X valía
2,3 M» y, semanas después, «X hizo tantos puntos y su precio acabó en tanto».

---

## BLOQUE 2 — EL JUICIO FINAL

### Primero, lo que NO se puede medir

**Los puntos de los 7 días siguientes no son medibles. Dicho con esas palabras.**

La última foto con puntos por jugador del árbol es del **19/09 18:18** (el snapshot y la
caché de Biwenger son la misma). Las fotos que tienen valor de fichaje calculado son del
**18/09 y el 20/09**, y la jornada siguiente —**J7, cerrada el 21/09 17:06**— **no está en
ningún fichero**. No es que los rechazados no puntuaran: es que no lo hemos guardado
(doctrina 103).

La foto del **14/09** sí tendría ventana (J5 y J6-aplazada), pero **no sirve para este
juicio**: ese día `xi_decision` fue `SIN_PRONOSTICO` en los **64** objetivos y
`roster_fill_decision` fue `FICHA_NO_APTA` en los 64. **No rechazó por precio: rechazó por
falta de pronóstico.** Es otro fallo, ya reportado.

### Lo que sí se mide: el precio

```
FOTO 18/09 16:16   n=19 con valor de fichaje calculado   horizonte 3,6 dias
                                              movimiento mediano   subio
  LOS DOS QUE ACEPTO (valor > precio)   n= 2        -9,51 %        0 de 2
  rechazados por poco (hueco < 10 %)    n= 0            -              -
  rechazados (hueco 10-50 %)            n= 5        +1,61 %        4 de 5
  rechazados por mucho (hueco > 50 %)   n=12        -4,77 %        5 de 12
  TODOS los rechazados                  n=17        +1,01 %        9 de 17

FOTO 20/09 09:10   n=20                                horizonte 1,9 dias
  rechazados por poco (hueco < 10 %)    n= 1        -3,23 %        0 de 1
  rechazados (hueco 10-50 %)            n= 8        +0,75 %        5 de 8
  rechazados por mucho (hueco > 50 %)   n=11        +0,24 %        6 de 11
  TODOS los rechazados                  n=20        +0,41 %       11 de 20
```

**Los dos que aceptó bajaron un 9,51 % de mediana. Los diecisiete que rechazó subieron un
1,01 %.** Con n=2 y 3,6 días eso no condena a nadie —y no lo voy a presentar como si lo
hiciera—, pero **no sostiene** que el motor esté acertando. Y los dos horizontes no se
mezclan: cada foto con el suyo (doctrina 54).

### Y lo que sí es concluyente: la aritmética

Reproduje la fórmula sobre las filas reales y sale al euro. `roster_fill_value = puntos_esperados × tarifa × 0,9`,
con `tarifa` implícita mediana de **18.300 €/punto** (18/09) y **19.874** (20/09). Dicho
en euros por punto, la regla entera es **una línea**:

```
FOTO 18/09          EUR/punto QUE PIDE    EUR/punto QUE PAGA   pasa
  Maffeo                      13.719              16.470        SI
  Cabrera                     15.916              16.556        SI
  Javi Hernandez              19.588               9.105        no
  Castrin                     19.596              16.470        no
  Noubi                       20.606               9.859        no
  Grimaldo                    21.404               9.859        no
  Dmitrovic                   22.607              16.548        no
  ...
  Pepe                        50.221              16.470        no
  Nico Williams               60.141              17.923        no
```

**El motor paga entre 9.040 y 17.923 € por punto esperado. El mercado pide entre 13.719 y
66.769.** Sólo dos bajaron del techo, y son exactamente los dos que aceptó.

Y ese techo **no es una opinión sobre el jugador: es el 90 % de la mediana de lo que cobra
el mercado.** Por construcción, sólo puede comprar en la mitad barata de la distribución,
menos el 10 % de margen. Que casi nadie pase no es un hallazgo sobre el mercado: **es lo
que la fórmula hace.**

### El segundo número, el que falta

`caja_de_la_liga.py:74`

```python
# El reparto del `leagueReset` del 09/08/2026. Despejado de
# nuestro saldo real y cuadrado al euro sobre 24 dias.
EUROS_POR_PUNTO = 30_000
```

**Medido, cuadrado al euro, sobre 24 días.** Y es lo que un punto **nos paga**, que es la
moneda de un fichaje: compramos a un jugador para que puntúe, y cada punto suyo entra en
caja a 30.000.

`tarifa` (18.300) y `EUROS_POR_PUNTO` (30.000) miden cosas distintas y el motor usa la
primera para una decisión de la segunda. **La diferencia es del 64 %.**

Y `los_dos_techos` **ya lo tiene escrito**, palabra por palabra:

> *«EL TECHO DEL QUE SE QUEDA — Otra moneda entera. Los puntos se pagan a 30.000 EUR
> (medido, publicado en `roundFinished`).»*

**Pero no se calcula nunca.** Sobre las 54 filas de la foto del 18/09,
`los_dos_techos.el_que_se_queda.available` sale **False en las 54**, con este motivo:

> *«Sin los puntos de más por jornada y las jornadas que quedan no se calcula: los dos son
> datos de la liga y suponerlos haría este número lo que uno quiera.»*

Nadie le pasa esos dos datos. **La segunda puerta de doctrina 99, y esta vez la que está
cerrada es la que tenía razón.**

### Los dos que aceptó, y el que rechazó y compró el dueño

```
Maffeo      18/09   pide 13.719 EUR/punto   ACEPTADO   comprado, ganado (carril)
Cabrera     18/09   pide 15.916             ACEPTADO   comprado 18/09 15:18, ganado
Dmitrovic   18/09   pide 22.607             RECHAZADO  lo compro el dueño a mano
                                                        el 20/09, por 4.992.001 EUR
```

**Dmitrovic pedía 22.607 €/punto.** Por debajo de 27.000 (que es 30.000 × 0,9) y por
encima de 16.548 (que es lo que el motor paga). **Con la moneda del comerciante se
rechaza; con la del que se queda, pasa.** Y el dueño lo compró.

Es un caso, no una medición. Pero es el caso que el propio motor documenta como su fallo
en `player_value_engine.py:1240-1260`, donde ya está escrito que Dmitrovic se cayó por
`SIN_PRONOSTICO` el 18/09 y se compró a mano el 20/09.

---

## BLOQUE 3 — SÍ: LE ESTAMOS PIDIENDO A UNA COMPRA DE REVENTA QUE MEJORE EL ONCE

### Con la línea

```python
# deployment.py, classify_operation
compensan = [via for via in fichaje
             if safe_int(via.get("value")) > safe_int(price)]
if not compensan:
    fichaje = []        # deja de ser un fichaje -> se clasifica TRADE
```

donde `fichaje = [as_xi, as_roster_fill]` y **los dos salen de `xi_upgrade_value`**, cuyo
`delta` es *puntos del candidato menos puntos del sustituido*: **una medida contra el
once**, incluso en la vía de ficha vacía (allí el sustituido es el cero de la ficha).

Así que la puerta que decide `biddable` mide **mejora del XI**, y el negocio que hay
detrás —el que Pollo hace 54 veces— **no necesita esa mejora**: basta con que el jugador
juegue.

### Cuántos pasarían con el criterio de reventa

Aplicando `roster_fill_veto` —el que ya existe: pronóstico presente, titularidad ≥ 40 %,
jerarquía ≥ 40, disponible— a los comprables al Computer de cada foto:

```
              objetivos   comprables   con el criterio      con el criterio
                          al Computer  de PLANTILLA         de REVENTA
  18/09           54          19            2                    6
  20/09           55          16            0                    4
```

**No son doscientos: son cuatro a seis al día.** Y ése es exactamente el ritmo de Pollo17
—54 viajes en 43 días, 1,3 al día—. **El listón no estaba de más. Está puesto en la moneda
que no toca.**

Los que se añaden: el 18/09 Gerard Moreno, Grimaldo, Dmitrovic y Dumfries; el 20/09 Soler,
Moncayola, Jon Martín y Dumfries. Y aviso de honestidad: **en el horizonte corto que hay,
esos ocho lo hicieron algo peor que el conjunto** (mediana ≈ −2,6 % a 3,6 días, −2,7 % a
1,9 días). Con esa `n` y ese plazo no prueba nada en ninguna dirección, pero no lo escondo.

---

## BLOQUE 4 — QUE DEJEMOS DE MEDIR A CIEGAS

### `BORDALAS_LA_VUELTA_SE_APUNTA` — apagado

`src/analysis/la_vuelta_se_apunta.py`. La línea del log lleva, en la misma línea que ya
existe:

- **`decision_candidates`** — todas las candidatas, con `priority`, `executable`,
  **`writes`** (si consume la escritura, que es la pregunta que se va a hacer), **`won`**
  (para no tener que cruzar con otro campo) y el motivo recortado a 200 caracteres **con
  `reason_truncated` marcado** — un texto cortado sin avisar se lee como si estuviera
  entero.
- **`requests`** — lo que costó la vuelta: total, endpoints distintos, repetidas,
  `rate_limited`, y los 12 endpoints más llamados.

No se crea ningún libro nuevo (doctrina 84): el sitio donde se apunta lo que pasó en una
vuelta ya existe.

**Lo que ocupa, medido:**

```
linea de hoy                5.088 B   (n=50, mediana = media)
cuatro perdedoras           1.276 B   con el motivo a 200 caracteres
vueltas por dia                35,1   (n=281 en 8 dias, bitacora del saldo)

  el log de hoy               5,1 MB al mes
  con las perdedoras          6,4 MB al mes     (+1,3)
  estable, podado a 2.000     9,7 -> 12,1 MB    (57 dias de historia)
```

### El fichero a git: **NO debe, y no es por tamaño**

Lo intenté —lo metí en `LIBROS` y abrí el `.gitignore`— y **una guardia me lo tumbó**:

```
test_ningun_libro_se_clasifico_dos_veces:
  Estos ficheros estan clasificados como libro Y como cache a la vez:
  data/autopilot/autopilot_log.jsonl
```

Porque **ya estaba decidido que no, con el motivo escrito**
([los_libros.py:451-457](src/estado/los_libros.py#L451)):

> *«SE PODAN A PROPÓSITO, así que guardarlos sería guardar algo que otro paso borra en la
> misma vuelta. `prune_github_state.py` los trunca DESPUÉS del ciclo y ANTES del guardado.
> Si se metieran en la lista se commitearía la versión podada, que es peor que no
> commitear nada: parecería un libro y sería un recorte.»*

Comprobado en el workflow: el paso `Prune persisted state` va **antes** de `Guardar los
libros`. **Doctrina 84: existía, con su razón. Lo revertí.**

**Y no es por tamaño:** 12,1 MB estables. El repositorio ya versiona
`scout_accuracy_ledger.json` (**31 MB**) y `divergence_ledger.json` (**5,4 MB**). Doce
megas es menos que uno solo de los que ya hay. En crecimiento del pack, un `.jsonl` que
sólo crece por el final delta-comprime a **~6 KB por vuelta ≈ 6,3 MB al mes**.

**La alternativa, con su número:** invertir los dos pasos del workflow —`Guardar los
libros` antes de `Prune persisted state`— y el fichero que se commitea pasa a ser el
entero. Cuesta **dos líneas del YAML**, que este encargo prohíbe tocar. Es tuyo.

*(La otra alternativa, un libro nuevo `libro_de_las_vueltas.jsonl` con sólo la decisión y
la cola —1,5 KB/vuelta, 1,6 MB/mes—, no la he hecho: duplicaría un registro que ya existe,
y doctrina 84 dice que primero se comprueba si hace falta otro.)*

### El contador de peticiones

`peticiones.resumen()` dice de sí mismo *«el recuento del ciclo, para publicarlo»* y
**sólo se imprime** (`autopilot.py:4524 _publicar_peticiones`). No queda en ningún sitio
legible después, así que el único aviso antes del próximo 429 es que alguien estuviera
mirando la consola.

**Con el interruptor puesto, ahora viaja en la línea del log**, junto a la cola. No lo he
metido en `dashboard_state` porque **el panel corre en OTRO PROCESO** (`build_dashboard`
se lanza después de `v10_full_autonomous_live`) y `CONTADOR` es del proceso: publicarlo
desde ahí enseñaría ceros. Para que salga en la foto hace falta que el ciclo lo persista
primero — que es justo lo que hace esto.

---

## LO QUE SE HA TOCADO

```
src/analysis/la_vuelta_se_apunta.py           NUEVO   la cola y el coste, apagados
src/analysis/test_la_vuelta_se_apunta_v1.py   NUEVO   9 guardias
src/autopilot.py                                      la linea del log los recoge
scripts/run_validation_gate.py                        la guardia en la verja
config/paso_0.json                                    lo reescribe el propio paso 0
```

---

## LO QUE NO SE HA HECHO, Y POR QUÉ

| | por qué |
|---|---|
| **Ni una escritura contra Biwenger** | lo prohíbe el encargo |
| **No se ha cambiado la valoración** | el bloque 2 juzga. `player_value_engine.py` y `deployment.py` están intactos |
| **No se ha inventado un factor de corrección** | lo prohíbe el encargo, y no hace falta: el número que falta ya está medido (`EUROS_POR_PUNTO = 30.000`) |
| **Ningún interruptor encendido** | apagado, la línea del log es la de hoy byte a byte, y hay guardia |
| **El workflow, intacto** | lo prohíbe el encargo — y es donde está la línea que haría que el log llegue a git |
| **No se ha metido el log en git** | ya estaba decidido que no, con su razón escrita, y una guardia me lo tumbó |
| **No se ha tocado** `MAX_SINGLE_SPECULATION_PERCENT`, `MAX_SAFE_DEBT`, el suelo de cobro, `MIN_WIN_PROBABILITY`, `MAX_PROJECTED_DAILY_RATE`, `PUEDEN_ENCERRARLO`, `PRIMA_MAXIMA_DE_PUJA`, `VENTANA_MINUTOS` | lo prohíbe el encargo |
| **No se ha empujado** | «Tú no empujas» |
| **No se han medido los puntos de después** | **no están en el árbol.** La última foto con puntos por jugador es del 19/09 y J7 se cerró el 21/09. Hace falta guardar una foto después de cada jornada, o apuntar los puntos por jugador y ronda en un libro |
| **No se ha alimentado `techo_del_que_se_queda`** | es el arreglo, y el encargo dice que el arreglo viene después. Necesita dos datos de la liga: las jornadas que quedan y los puntos de más por jornada |

---

## LO QUE YO HARÍA AHORA, EN ESTE ORDEN

1. **Darle de comer a `los_dos_techos`.** El número está medido (30.000 €/punto) y el
   módulo escrito desde el 12/09. Sólo le faltan las jornadas que quedan.
2. **Empezar un libro de aciertos de la valoración.** Hoy no existe: cada foto que pasa es
   evidencia que se destruye. Es el mismo argumento que abrió el
   `libro_de_publicacion.jsonl` el 10/09.
3. **Guardar una foto después de cada jornada**, para que la pregunta de este encargo se
   pueda contestar la próxima vez.

---

## LO QUE ARRASTRAMOS

**1. Tres ramas sin fusionar** (doctrina 108): `arreglo/la-puja-que-vuelve`,
`arreglo/sacar-de-la-sombra` y `medir/quien-se-queda-la-escritura`. `BORDALAS_SIN_REVENTA`,
`BORDALAS_CUPO_POR_VENTANA`, `BORDALAS_PUBLICAR_LA_COLA` y `BORDALAS_PUJAR_EN_LA_VENTANA`
no existen en `main`.

**2. `test_el_ciclo_publica_v1` volvió a ensuciar los cinco libros** en cada una de las
tres corridas de hoy. Restauré `data/` antes de cada veredicto y después del último.

**3. El modelo de las renovaciones, sin medir.** Sigue siendo la palanca más barata que
conozco, y ahora con un motivo más: las renovaciones ganaron ocho de las nueve vueltas
reconstruidas ayer.
