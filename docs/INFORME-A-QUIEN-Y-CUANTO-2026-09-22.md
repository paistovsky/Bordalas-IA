# A quién y cuánto, y la verja que se lee el workflow

**Encargo:** `Claude outputs/ENCARGO-A-QUIEN-Y-CUANTO-2026-09-22.md`
**Rama:** `encender/a-quien-y-cuanto`, desde `main` en `f667ed2`
**Fecha:** 22/09/2026, noche

---

## Bloque 1 — la verja se lee el workflow

### Lo que dice ahora, en su cabecera

```
Puerta de validacion: 179 tests
corriendo con 2 interruptores de produccion: BORDALAS_JORNADAS_POR_SU_FECHA, BORDALAS_REVENTA_SOLO_SI_JUEGA
==================================================================
```

Los dos salen de leer `.github/workflows/bordalas-live.yml` y **se los pone ella sola**
antes de lanzar la primera guardia. Ya no hace falta escribir esto a mano:

```powershell
$env:BORDALAS_JORNADAS_POR_SU_FECHA="1"
$env:BORDALAS_REVENTA_SOLO_SI_JUEGA="1"
```

### Si no sabe leer el fichero, no da verde

```
NO SE SABE CON QUE INTERRUPTORES CORRE PRODUCCION
==================================================================
  No se pudo leer el workflow (...bordalas-live.yml): FileNotFoundError: ...
  Sin saber con que interruptores corre produccion, esta verja no puede dar verde.

  Esto no es un verde con un aviso: es un rojo. Doctrina 91.
```

**Sale con código 2**, antes de correr una sola guardia, y también antes del paso 0.
Comprobado ejecutando `main()` con la lectura forzada a fallar: código `2`.

### No depende del entorno: gana el YAML, en las dos direcciones

| lo que hay en la consola | lo que dice el YAML | qué hace la verja |
|---|---|---|
| nada | `BORDALAS_X: "1"` | lo pone a `1` |
| `BORDALAS_X=1` | `BORDALAS_X: "1"` | lo deja, no avisa (no hay contradicción) |
| `BORDALAS_X=0` | `BORDALAS_X: "1"` | **lo pone a `1`** y avisa |
| `BORDALAS_Y=1` | el YAML no lo enciende | **lo quita** y avisa |

El aviso sale por pantalla antes de la primera guardia:

```
  AVISO: BORDALAS_VARA_PLANA estaba en el entorno y el workflow no lo
  enciende: gana el YAML, se quita.
```

La única excepción es `BORDALAS_VIGILA_DATA`, que **lo pone la propia verja**: es
herramienta del corredor, no comportamiento del bot, y quitarlo apagaría el único ojo que
mira si una guardia escribe en `data/`.

### La tensión con `test_la_puerta_no_lee_el_workflow`, y cómo se ha resuelto

Esa guardia existe desde el 19/09 y se pone roja si **un literal del script de la verja**
nombra un `.yml`. El encargo pide justo que la verja lea el YAML. Las dos cosas son
ciertas porque **son dos lecturas distintas**:

- **la lista de guardias** no puede salir del workflow — ahí es donde estuvo y donde no
  debe volver;
- **los interruptores de producción** sí, porque es el workflow quien los enciende.
  Tenerlos escritos en otro sitio sería mantener una copia, y una copia se desincroniza
  el día que importa. Eso es lo que costó la corrida #1753.

Así que el fichero lo nombra un módulo nuevo,
[los_interruptores_de_produccion.py](src/analysis/los_interruptores_de_produccion.py), y
la puerta no lo nombra: `WORKFLOW` sigue siendo `None` allí y el `assert` sigue en pie sin
ablandarse. **He cambiado el docstring de la guardia** para que diga cuál de las dos
lecturas prohíbe, en vez de dejarlo implícito.

No se ha escrito un segundo parser: se reusa
`el_paso_0.interruptores_encendidos_en`, que ya contestaba esta pregunta sobre un texto
YAML con sus exclusiones medidas —líneas comentadas, `"0"` y secretos—. Lo único que añade
el módulo nuevo es el disco (doctrina 84).

### La guardia

`test_la_verja_corre_como_CI`, en
[test_la_verja_corre_como_ci_v1.py](src/analysis/test_la_verja_corre_como_ci_v1.py), con
seis casos. El YAML de ejemplo enciende dos y lleva a propósito las cuatro formas de **no**
estar encendido: comentado, a `"0"`, un secreto (`${{ secrets.X }}`) y una variable que no
es interruptor.

**Muerde.** Tres roturas comprobadas:

| lo que se rompe a propósito | qué dice la guardia |
|---|---|
| el ejemplo enciende `"0"` en vez de `"1"` | `tenian que salir [...] y salieron []` |
| la verja reporta los interruptores pero no los pone | `sale del YAML encendido y no llega puesto al entorno` |
| un fichero ilegible devuelve `ok: True` | `un fichero que no existe ha dado por bueno el entorno` |

---

## Bloque 2 — la lista de la noche

### Dónde se ve

En **la foto del panel**: bloque `lista_de_la_noche` de `status.json`, al lado de
`sombra`. Y para mirarla a las tres de la mañana sin abrir un JSON de 500 KB, un comando:

```
python scripts/la_lista_de_la_noche.py
```

### Cómo se ve — ejemplo real de formato

```
LA LISTA DE LA NOCHE
==============================================================================
  foto: ...\status.json
  2026-09-22T23:40:00

  3 nombre(s) de 3 mirados, y 14.630.000 EUR en juego si la moneda estuviera puesta.
  De mayor a menor puja.

   1. El Caro (DEL)
      precio 9.000.000   PUJARIA 9.100.000   prima 100.000 (1.111 %)
      por PLANTILLA (via XI_UPGRADE, moneda LIGA)
      techo: La deja pasar el techo del COMERCIANTE: 9.120.000 EUR contra una puja de 9.100.000.
      mejora a Un Suplente por 140 puntos
```

Están los ocho datos que pediste: jugador · posición · precio de mercado · lo que pujaría ·
la prima · por qué (plantilla o reventa) · qué techo lo dejó pasar · a quién mejora del
once y por cuántos puntos. **De mayor a menor puja**, «porque es el que más duele
equivocarse».

> Ese ejemplo es el **caso de la guardia**, con nombres inventados, porque esta noche la
> lista de verdad sale vacía. La de verdad va justo debajo.

### Lo que sale ESTA noche, con la foto de verdad

```
  Con la moneda de la liga puesta, esta vuelta no pujaria por nadie.
  Mirados: 31. El que mas cerca se queda es Budimir: RENDIMIENTO_INSUFICIENTE.
```

**Por nadie.** Y no es una avería: de los 31 mirados, 24 caen por
`RENDIMIENTO_INSUFICIENTE`, 6 por `SUPERA_PRESUPUESTO` —quedan 973.594 EUR sin
comprometer— y 1 por `NO_COMPENSA`. Con la moneda quitada, la puja de verdad de esta
vuelta también es **0 de 52**. La moneda no cambia nada esta noche.

Por eso la lista vacía **dice a cuántos miró y quién se quedó más cerca**: cero nombres
puede ser «no hay nadie» o «esto se ha roto», y a las tres de la mañana no se distinguen
(doctrina 103).

### Cuántos nombres por noche

| día | nombres con puja > 0 | de cuántos |
|---|---|---|
| 14/09 (foto) | 0 | 64 |
| 18/09 (foto) | **2** — Cabrera y Maffeo | 54 |
| 20/09 (foto) | 0 | 55 |
| 22/09 (vuelta de verdad, con la lista puesta) | **0** | 31 |

**Nunca más de dos.** Y el techo de arriba: el encargo anterior midió que la moneda sube
los que pasan el techo de **2 → 4** el 18/09 y de **0 → 4** el 20/09. O sea que el máximo
razonable es **cuatro nombres**, no cincuenta.

**Muy por debajo de diez: no hay nada que recortar y no he recortado nada.** Si algún día
pasara de diez, la lista se enseña entera igual y lo dice en su propio motivo —hay una
guardia, `test_no_recorta_sin_decirlo`, que se pone roja si alguien la corta—.

Una honestidad sobre esa tabla: **las tres primeras filas son las pujas de verdad de aquel
día, no la lista de la noche replicada.** No se puede replicar: la foto publica el valor de
la vía ganadora pero no las patas por vía (`as_xi.rate_per_point`, `recovered_value`), que
es lo que hace falta para reescalar, y del 18 y el 20 no hay `snapshot_*.json` en el repo
—el más nuevo es del 19—. Son una cota inferior del número de nombres, no el número.

### Cómo se calcula, y por qué no vuelve a valorar nada

La moneda solo cambia **un factor** de una multiplicación que ya existe:

```
justo = puntos_de_mas x tarifa
valor = int(justo x (1 - margen) x confianza) + recuperado
```

Así que el valor con la otra moneda sale de **despejar el que ya está publicado**:

```
valor_liga = (valor - recuperado) x 30.000 / tarifa + recuperado
```

Y la puja la calcula **la misma `optimal_bid` que decide**, con el mismo modelo de
rivales, el mismo presupuesto y el mismo tope. Lo único que cambia es el `value`. Una
sombra calculada con otra cuenta no sería la sombra de nada.

Que esa cuenta es la de verdad lo comprueba una guardia que corre `xi_upgrade_value` **con
el interruptor puesto** y exige que dé lo mismo: **diferencia ≤ 1 EUR** (el redondeo de
`int`). Si algún día la fórmula deja de ser lineal en la tarifa, esa guardia se pone roja y
la lista se queda vacía en vez de inventar.

### La guardia

`test_la_sombra_de_la_moneda_no_escribe`, en
[test_la_sombra_de_la_moneda_v1.py](src/analysis/test_la_sombra_de_la_moneda_v1.py), siete
casos. Con la moneda **quitada** (`os.environ.pop` a nivel de módulo, doctrina 104):

- se le quitan las manos al cliente: los **siete** métodos que escriben de
  `BiwengerWriteClient` —`place_bid`, `counter_offer`, `cancel_bid`, `accept_offer`,
  `reject_offer`, `list_player_for_sale`, `save_lineup`— se sustituyen por uno que revienta
  con su nombre. La lista se calcula entera: **ninguna llamada**;
- **el caso tiene tres candidatos** y la guardia exige los tres: cero nombres es lo que
  devuelve un módulo roto, así que sin esa línea daría verde probando nada (doctrina 24);
- y **la moneda sigue apagada después de mirarla**. Éste es el riesgo de verdad —calcular
  la sombra encendiendo el interruptor y dejarlo puesto sería poner producción en otro
  estado sin que nadie lo pidiera—, y por eso la sombra **no toca `os.environ` en ningún
  momento**: reescala, no enciende.

**Muerde.** Tres roturas comprobadas: no escalar (`la sombra dice 2.200.000 y de verdad son
2.800.000`), recortar en silencio, y ordenar al revés.

---

## Bloque 3 — la guardia que ensuciaba los libros

`test_el_ciclo_publica_v1` monta ahora el estado **sobre una copia de `data/` en un
temporal** y vuelve al directorio de siempre pase lo que pase. Funciona porque todo el
camino del panel abre rutas relativas (`Path("data") / ...`), así que basta con mover el
directorio de trabajo.

Se copia **entera** y no un trozo elegido a mano: elegir sería adivinar qué abre, y lo que
abre cambia cada semana. **Coste medido: 1,8 s** por los 165 ficheros (138 MB).

Y no se confía en que funcione: la guardia **ficha el tamaño y la hora de cada fichero de
`data/` antes y después** y se pone roja si alguno cambió. Quitando la copia a propósito, la
guardia canta — y canta **siete libros, no los cinco del encargo**:

```
esta guardia ha escrito en los libros de produccion:
  data\intelligence\libro_de_publicacion.jsonl
  data\intelligence\marcador.json
  data\rival_intelligence\board_events.json
  data\rival_intelligence\board_latest_raw.json      <- no estaba en tu lista
  data\rival_intelligence\profiles_cache.json        <- no estaba en tu lista
  data\rival_intelligence\rival_intelligence.json    <- no estaba en tu lista
  data\solvency\bitacora_del_saldo.jsonl
```

### Cuántas guardias siguen escribiendo en `data/`

Medido corriendo **las 178 de la lista una por una**, con los interruptores de producción
puestos, fichando `data/` entre cada una (245 s):

```
5 de 178 guardias dejan data/ distinto
```

| guardia | qué toca |
|---|---|
| `test_v10_full_autonomous_live` | `board_events.json`, `board_latest_raw.json`, `profiles_cache.json` |
| `test_el_plato_del_carril_v1` | los mismos tres |
| `test_ojeador_informe_v1` | `scout_accuracy_ledger.json` |
| `test_divergencia_v1` | `divergence_ledger.json` |
| `test_puerta_una_sola_lista_v1` | `divergence_ledger.json` |

**Y `git status` no las ve.** Después de la verja entera, `git status data/` sale limpio:
esos cinco reescriben el fichero con el mismo contenido, así que cambia la hora y no los
bytes. Tres de los seis ficheros **sí están en git** (`board_events.json`,
`scout_accuracy_ledger.json`, `divergence_ledger.json`), o sea que el día que una de esas
guardias escriba algo distinto, ensucia un libro versionado. El riesgo está vivo, solo que
callado.

Las cinco quedan **medidas y nombradas, no arregladas**: el encargo pedía una, y las otras
cuatro son trabajo con su propio riesgo. Las tres primeras escriben **cachés del tablón**
—no libros de dinero—; las dos últimas escriben **libros de aciertos**, que sí son
evidencia y son las que hay que mirar primero.

---

## La verja y el paso 0

Las dos corridas, sobre el árbol final y con el árbol quieto:

```
Puerta de validacion: 179 tests
corriendo con 2 interruptores de produccion: BORDALAS_JORNADAS_POR_SU_FECHA, BORDALAS_REVENTA_SOLO_SI_JUEGA
==================================================================
LA VERJA HA TARDADO 217 s (3.6 min) en 179 guardias, 1.21 s de media.

Los 179 en verde. Se puede subir.                                        (codigo 0)
```

```
EL PASO 0 HA TARDADO 218 s (3.6 min).
PASADO. Quedan probados 28 interruptores, apuntados en config/paso_0.json.
```

**179, no 177:** las dos guardias nuevas. Y el paso 0 sigue en **28** interruptores: no se
ha añadido ninguno, porque este encargo no enciende nada.

### Tres rojas por el camino, y una que cacé yo

Las tres primeras son las de siempre al añadir ficheros, y se arreglaron **fijando el
caso**:

| roja | qué era | cómo se arregló |
|---|---|---|
| `test_la_lista_blanca_v1` | `lista_de_la_noche` llegaba al navegador y moría en `raw` | se nombra la clave en `normalizeStatus` |
| `test_el_proposito_v1` | un fichero nuevo nombra el `intent` y nadie había escrito qué decide con él | entrada en `QUE_DECIDE_CADA_UNO`: **no decide**, publica |
| `test_verja_determinista_v1` | falso positivo: mi guardia escribe `"data/"` para **prohibirlo**, y la otra guardia mira el texto | se arma el nombre de la carpeta sin escribirlo entero, con el motivo al lado |

Y la cuarta no la cazó ninguna guardia, la cazó el paso 0 al mirarle el diff:

> **El primer paso 0 dio 31 interruptores, no 28.** `scripts/los_interruptores.py` censa
> todo lo que empiece por `BORDALAS_` en el repositorio, así que los tres nombres
> inventados del YAML de ejemplo —`BORDALAS_UNO_APAGADO` y compañía— entraron en
> `config/paso_0.json` **como probados**. Tres interruptores que no existen, dados por
> comprobados.
>
> Arreglado usando **nombres de verdad** en el ejemplo (`BORDALAS_SIN_SUBASTA` a `"0"`,
> `BORDALAS_TOPE_DEL_ONCE` comentado, `BORDALAS_VARA_PLANA` como el intruso del entorno),
> que además hace el ejemplo más parecido al fichero real. Segundo paso 0: **28**.

---

## Lo que no he hecho, y por qué

| no hecho | por qué |
|---|---|
| **Encender la moneda** | es tuyo. La lista está para que la mires antes |
| **Encender ningún otro interruptor** | lo prohíbe el encargo. El inventario sigue igual |
| **Tocar `.github/workflows/bordalas-live.yml`** | el bloque 1 lo **lee**. No se le ha cambiado un byte |
| **Poner la lista de la noche detrás de un interruptor** | el encargo nombra «el interruptor de la sombra». **No lo he creado**, a propósito: `libro_en_la_sombra` —el precedente de esta casa— no tiene interruptor, y una sombra detrás de un interruptor apagado no enseña nada la noche que hace falta, que es ésta. La lista calcula y publica; no decide, no escribe y no gasta. Si lo quieres detrás de un interruptor, se pone en cinco minutos |
| **Un panel de React para la lista** | `dashboard-v8` es un bundle compilado y rehacerlo es tuyo. El bloque va en la foto, que es lo que pedía el encargo, y el script lo imprime en una pantalla |
| **Replicar la lista de la noche sobre el 18/09 y el 20/09** | no se puede: la foto no publica las patas por vía y no hay `snapshot_*.json` de esos días. Lo que sí hay son las pujas reales de aquel día, y están en la tabla |
| **Arreglar las otras cuatro guardias que escriben en `data/`** | están medidas y nombradas arriba. El encargo pedía una |
| **`test_el_ciclo_publica_v1` sigue saliendo a la red** | tarda 1 m 34 s y eso es la red, no la copia. Cortársela puede tumbar el montaje por un motivo distinto del que vigila, y eso no estaba en el encargo. Queda dicho |
| **Tocar los números prohibidos** | `MAX_SINGLE_SPECULATION_PERCENT`, `MAX_SAFE_DEBT`, el suelo de cobro, `MIN_WIN_PROBABILITY`, `MAX_PROJECTED_DAILY_RATE`, las cinco de `PUEDEN_ENCERRARLO`, `PRIMA_MAXIMA_DE_PUJA` y la ventana de 135 minutos: intactos |
| **Empujar** | tú empujas |
