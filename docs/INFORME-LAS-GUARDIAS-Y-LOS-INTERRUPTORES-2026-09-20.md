# LAS GUARDIAS Y LOS INTERRUPTORES

**Fecha:** 2026-09-20 (el siguiente) · **Rama:** `arreglo/las-guardias`, desde
`arreglo/el-marcador` · **Escrituras contra Biwenger:** ninguna · **Interruptores
encendidos:** ninguno

---

## LO PRIMERO, PORQUE CAMBIA EL PLAN DE ESTA NOCHE

> **El agujero no era uno. Eran QUINCE guardias, y TRES de los cuatro de tu cola
> habrían parado el ciclo.**

Medido corriendo la verja entera con los 21 interruptores puestos, y despues uno a
uno para saber cual tumba a cual:

```
  BORDALAS_SIN_REFERENCIA_ESCALA   (1.o de tu cola)   tumbaba 3 guardias
  BORDALAS_CESTA_SOLO_EL_SUELO     (2.o de tu cola)   tumbaba 3 guardias
  BORDALAS_JORNADAS_POR_SU_FECHA   (3.o)              ninguna
  BORDALAS_OBJETIVOS_EL_CATALOGO   (4.o)              1  <- la de anoche
```

**El único de tu cola que no habría parado nada es el tercero.** Si anoche hubieras
encendido el primero en vez del cuarto, habría pasado exactamente lo mismo — y con
una guardia más.

Las quince están arregladas y la verja pasa con los 21 puestos.

---

# BLOQUE 1 — LA GUARDIA QUE SE CAYÓ

## Por qué miraba el entorno en vez de ponerlo ella

La guardia **sí sabía** poner el interruptor: su ayudante `_lista(foto, encendido)`
lo ponía y lo quitaba en todas las pruebas. Lo que falló fue **una línea**, la
primera de `test_apagado_se_comporta_como_ayer`:

```python
assert not objetivos_el_catalogo(), (
    "el interruptor esta encendido en el entorno de la verja: ..."
)
```

**El error de concepto:** escribí «apagado» como *«lo que da el entorno cuando
nadie lo toca»*, y eso es estado de producción. Lo correcto es *«lo que da el
código con la variable borrada»*, y eso lo pone la guardia.

Es la misma familia que la regla 23 —ninguna guardia lee estado externo— aplicada a
un sitio donde no habíamos mirado: **el `env` del proceso es estado externo, y
además cambia solo cuando alguien edita un YAML.**

## ¿El lector cachea? No, y está medido

```
  con la variable en "1"      -> objetivos_el_catalogo() = True
  BORRADA                     -> False
  otra vez "1"                -> True
  "0"                         -> False
```

Cuatro cambios **después** del import, los cuatro seguidos. `objetivos_el_catalogo()`
hace su `os.environ.get(...)` dentro de la función, no al importarse.

Y no es solo ese: **de los 21 interruptores que existen, los 21 se leen al
llamarse**, ninguno al importarse. Está comprobado por AST sobre los 176 ficheros
de `src/` y `scripts/`, y hay guardia que lo exige —
`test_ningun_interruptor_se_lee_al_importarse` — porque es la condición sin la cual
«que lo ponga la guardia» no significaría nada.

## El arreglo

Para «apagado» la variable **se borra**, no se pone a `"0"` — es el estado que
tiene de verdad una máquina limpia. Y que las dos cosas signifiquen lo mismo está
medido aparte, en `test_para_el_lector_borrada_y_cero_son_lo_mismo`: no es una
suposición, es una prueba.

> La guardia pasó de 4 a **6 pruebas**: las dos nuevas son «el lector no cachea» y
> «borrada y cero son lo mismo».

## Los dos veredictos de la verja

```
  sin la variable       exit 0    220,2 s
  con la variable a "1" exit 0    518,3 s
```

**Los mismos.** Y desde hoy ese par no hay que correrlo a mano: la guardia nueva lo
hace en cada ciclo con los 21 a la vez, así que **el verde de la verja YA INCLUYE
el verde con todo puesto**.

---

# BLOQUE 2 — LAS OTRAS · LO QUE MÁS IMPORTABA

`python -m scripts.los_interruptores` · `--todos` para la comprobación que no
admite discusión.

## Sí hay más de los que listaste: son 21, no 10

Los **once** que no estaban en tu lista:

| interruptor | quién lo lee | qué hace |
|---|---|---|
| `BORDALAS_BID_SALT` | `bid_jitter.py` | la sal del desvío de puja |
| `BORDALAS_CALIDAD_ETIQUETA` | `calidad_medida.py` | **apaga** la calidad medida |
| `BORDALAS_HORIZONTE_FIJO` | **nadie** | declarado y sin lector |
| `BORDALAS_LISTON_DEL_MANAGER` | `competitive_transaction_engine.py` | el listón de ayer |
| `BORDALAS_NO_REPETIR_LA_ESCRITURA` | `la_puja_que_ya_esta.py` | freno de repetición |
| `BORDALAS_SIN_ARCHIVO` | `archivo_diario.py` | **apaga** el archivo |
| `BORDALAS_SIN_CACHE` | `cache_del_reset.py` | **apaga** la caché |
| `BORDALAS_SIN_MERCADO_RIVALES` | `acquisition_board.py` | **apaga** el mercado de rivales |
| `BORDALAS_SIN_SUBASTA` | `la_subasta.py` | **apaga** la subasta |
| `BORDALAS_VARA_PLANA` | `position_factor.py` | **apaga** los factores de posición |
| `BORDALAS_VIGILA_DATA` | `vigila_data/sitecustomize.py` | enciende el vigilante de `data/` |

Dos los nombraste en prosa (`VARA_PLANA`, `SIN_SUBASTA`), así que estrictamente
nuevos son **nueve**.

> **`BORDALAS_HORIZONTE_FIJO` no lo lee nadie.** Su propio comentario lo dice:
> *«Hoy no hace falta —nadie lee esto— pero la casa entera funciona así»*. No es un
> fallo; es un interruptor sin cable, y conviene saberlo antes de tirar de él.

## La tabla: las guardias que tocan un interruptor

Diecinueve parejas *(guardia, interruptor)*, todas con «lo pone ella: SÍ» y «se cae
si está ON: NO» después del arreglo. La que importa es la columna medida, y la
columna medida ya no tiene un solo SÍ.

**Pero esa tabla sola no valía**, y es el hallazgo del bloque: sólo ve las guardias
que **nombran** un interruptor. Catorce de las quince que se caían **no nombraban
el suyo**: lo heredaban a través del motor que llaman.

## La comprobación que no admite discusión

Corriendo la verja entera con los 21 puestos a `"1"` a la vez, y después
bisecando uno a uno:

| guardia | la tumbaba | ¿está en la cola? |
|---|---|---|
| `test_futbolfantasy_source_v12` | **SIN_REFERENCIA_ESCALA** | **sí, el 1.º** |
| `test_starter_aware_xi_v1` | **SIN_REFERENCIA_ESCALA** | **sí, el 1.º** |
| `test_verja_determinista_v1` | **SIN_REFERENCIA_ESCALA** | **sí, el 1.º** |
| `test_el_orden_distingue_tamano_v1` | **CESTA_SOLO_EL_SUELO** | **sí, el 2.º** |
| `test_intel_v1` | **CESTA_SOLO_EL_SUELO**, SIN_ARCHIVO | **sí, el 2.º** |
| `test_la_prima_va_por_tramo_v1` | **CESTA_SOLO_EL_SUELO** | **sí, el 2.º** |
| `test_la_lista_de_objetivos_v1` | **OBJETIVOS_EL_CATALOGO** | **sí, el 4.º** — la de anoche |
| `test_los_tres_arreglos_v1` | TOPE_DEL_ONCE | sí, el 4.º del protocolo |
| `test_la_puja_del_carril_v1` | CUPO_POR_ENVIOS, NO_REPETIR_LA_ESCRITURA | sí, el 2.º del protocolo |
| `test_encender_calidad_v1` | VARA_PLANA, CALIDAD_ETIQUETA | no: son de apagar |
| `test_vara_v1` | VARA_PLANA | no |
| `test_encender_las_pujas_v1` | SIN_SUBASTA | no |
| `test_una_ventana_que_no_se_abre_v1` | SIN_SUBASTA | no |
| `test_peticiones_v1` | SIN_CACHE | no |
| `test_sin_pronostico_v1` | CALIDAD_ETIQUETA | no |

**Quince.** Y **nueve** de ellas se caían con uno de los ocho que están en cola
para encenderse — tres con el primero de tu lista, tres con el segundo.

## El arreglo, y por qué no relaja nada

En las quince, el interruptor se **apaga en el propio fichero**, antes de medir
nada, con el motivo escrito:

```python
# EL ENTORNO NO DECIDE ESTA GUARDIA  (doctrina 104, 20/09/2026)
os.environ.pop("BORDALAS_LO_QUE_SEA", None)
```

> **No es relajar la guardia: es fijarle el caso.** Cada una de las quince mide el
> comportamiento **por defecto**, y con el interruptor puesto estaba midiendo otro
> sin saberlo. El comportamiento **con el interruptor puesto** lo mide la guardia
> propia de ese interruptor, que lo enciende y lo apaga ella y comprueba las dos
> posiciones.

Y tres más se arreglaron **sin haberse caído nunca**, porque tenían la misma forma
que la de anoche y era cuestión de tiempo: `test_la_cesta_solo_el_suelo_v1`,
`test_el_liston_del_manager_v1` y `test_el_marcador_por_su_fecha_v1`.

**Dieciocho guardias tocadas. Ni un `assert` debilitado.**

---

# BLOQUE 3 — `test_sin_pronostico_v1`

## Por dónde se colaba, y no era por donde parecía

La cabecera del fichero ya decía *«no se lee el estado de producción»*, y era verdad
de todo lo que se escribe ahí. El agujero estaba en **el argumento que NO se
pasaba**:

```python
prepare_players(snapshot, lineup_intelligence, board)
                          ^^^^ iba None
```

Con `None`, `prepare_players` **construye** la inteligencia de alineación él solo —
y esa construcción abre tres ficheros:

```
  data/calendar/laliga_calendar.json
  data/intelligence/futbolfantasy_board.json
  data/intelligence/jornada_perfecta_lineups.json
```

De ahí salía un `score_adjustment` de **230,40** para Esquivel que el 18/09 no
existía. Por eso su score no cuadraba: **249.799,75 contra 250.030,15**.

Y había un **segundo** agujero, invisible desde el fichero: `build_sale_order` llama
a `build_position_guardrail`, que llama a `get_starter_lookup()`, que abre el
tablero él solo. No hay parámetro por el que pasárselo.

## El caso, fijo

1. **`INTELIGENCIA_VACIA = {"lookup": {}}`** en vez de `None`. De ese diccionario
   el motor sólo mira `external_block` y `score_adjustment`, y vacío valen `False`
   y `0.0` — que es lo que valían el 18/09 para esos tres.
2. **`sin_tablero_en_disco`**, que apunta `BOARD_FILE` a una ruta que no existe
   mientras se construye la cola de venta.

```
  VIGILANTE-DATA:  (nada)
```

> **Ya no abre un solo fichero de `data/`.**

## ¿Deja de detectar algo? Al revés: detecta más

```
  jugador     antes (leyendo data/)     ahora (caso fijo)    la foto del 18/09
  Esquivel        249.799,75               250.030,15           250.030,15
  Dituro          235.067,68               235.067,68           235.067,68
  Iturbe          213.230,15               213.230,15           213.230,15
```

**Antes reproducía dos de los tres scores de la foto. Ahora reproduce los tres.**
Fijarle el caso no le quita capacidad: se la devuelve. Y el rojo de los últimos dos
días desaparece con él — no era un fallo de código, era la foto de producción
moviéndose debajo.

**Se queda en la verja**, como pediste: guarda el arreglo del 18/09 y tiene que
parar el ciclo si ese arreglo se rompe.

---

# BLOQUE 4 — LA GUARDIA QUE IMPIDE QUE VUELVA A PASAR

## Elegí la cara, y el número me obligó a cambiar de opinión

Empecé por la barata —estática: *toda guardia que nombre un `BORDALAS_*` tiene que
ponerlo ella*— porque cuesta 7,4 s. Y la medí antes de quedármela:

> **Le pasé las catorce guardias que de verdad se caían, en su versión de antes del
> arreglo. Cazó CERO.**

El motivo es exacto y vale la pena escribirlo:

- **Trece no nombran** el interruptor que las tumba: lo heredan a través del motor
  que llaman.
- **Y las que sí lo nombran, lo ponen en alguna de sus pruebas**, así que la regla
  las daba por buenas. `test_la_lista_de_objetivos_v1` —la que rompió el ciclo—
  salía **limpia** con la regla barata.

**Una guardia que no caza ninguno de los catorce casos reales no es barata: es que
no está.** Así que la barata se descarta por medición, no por gusto.

## La cara, con su coste

```
  la verja entera, hoy            205 s   (3 min 25 s)
  con esta guardia dentro         410 s   (6 min 50 s)
  tope del job                   2100 s   (35 min)
  vuelta de produccion       780-1140 s   (13-19 min)
```

Medido de verdad: la guardia sola tarda **275 s** y la verja con ella dentro,
**~480 s (8 min)**. **Cabe, y sobra el 60 % del tope.**

**El intercambio, dicho entero para que puedas deshacerlo:** esto dobla largo la
verja de **todos** los ciclos para protegerte de algo que sólo puede pasar el día
que alguien toca el `env`. La misma protección está en el **paso 0** y en
`--todos`, que cuestan una corrida sólo cuando enciendes algo. Me quedo con la
guardia porque el paso 0 depende de que alguien se acuerde, y anoche demostró que
no siempre pasa. Si prefieres lo contrario, es una línea en `TESTS` y lo digo aquí
para que sea una decisión y no un descuido.

`test_ninguna_guardia_depende_del_entorno` corre la verja entera **otra vez**, con
los 21 puestos, y exige `exit 0`.

**Cómo no se muerde la cola:** la corrida de dentro va con `--solo` y la lista de la
verja **menos esta guardia**, y con `VERJA_ANIDADA=1`, que le dice al corredor que
no apunte el veredicto — si no, el mensaje del commit contaría la corrida de dentro.
*(Eso es un cambio de cuatro líneas en `run_validation_gate.py`, y no es un
`BORDALAS_*` a propósito: no cambia comportamiento, dice cómo se llama a sí misma.)*

**Doctrina 24:** si el inventario no encuentra ni un interruptor que poner, la
guardia **falla** — correr la verja dos veces con el mismo entorno sería salir en
verde sin haber comprobado nada.

Y se queda una tercera comprobación, que es la condición sin la cual todo lo demás
no valdría: **ningún lector lee el entorno al importarse**.

---

# BLOQUE 5 — EL PROTOCOLO DE ENCENDIDO

## Primero: el sitio ya existía, y no estaba aquí

> **Doctrina 84.** `src/analysis/el_protocolo_de_encendido.py` se escribió el
> **20/09 a las 00:35** —commit `3d6529a`, rama `encender/el-protocolo`— con la
> ficha de cinco campos, cuatro interruptores y su guardia. **Nunca se fusionó.**
> Por eso mis cuatro fichas de ayer acabaron en un informe: el sitio bueno existía
> y no estaba en la rama donde trabajaba.
>
> Su propia cabecera dice *«LAS FICHAS VIVEN EN EL CÓDIGO, NO EN UN INFORME»*.
> Tenía razón, y yo no la había leído.

**Lo he traído a esta rama** —los dos ficheros, sin el cambio del dashboard— y he
metido dentro las cuatro de tu cola. Ahora el protocolo tiene **ocho**, numeradas
del 1 al 8, y una sola guardia las vigila. Si prefieres que la cola viva aparte, es
una decisión tuya y se separa fácil.

## El PASO 0, escrito

```
PASO 0   correr la verja entera CON el interruptor puesto.
         Si no da el mismo verde que sin el, NO SE ENCIENDE.
```

Y el mandato de una línea para PowerShell:

```powershell
$env:BORDALAS_LO_QUE_SEA = "1"; python scripts/run_validation_gate.py > verja.txt 2>&1; $c = $LASTEXITCODE; Remove-Item Env:/BORDALAS_LO_QUE_SEA; "exit $c"
```

Pone el interruptor, corre la verja **a fichero** —doctrina 52: en una tubería el
código de salida es el del último mandato—, guarda el código, quita el interruptor
y lo enseña. **Un mandato, un paso.**

*(Con la guardia nueva dentro, este paso 0 tarda ~7 minutos. Es el precio de saber
que el ciclo va a arrancar.)*

## Las cuatro fichas de la cola

Viven en `PROTOCOLO`, órdenes 5 a 8, con los cinco campos. En resumen:

| | qué cambia | qué mirar antes | qué debería pasar | señal de apagarlo |
|---|---|---|---|---|
| **5 · SIN_REFERENCIA_ESCALA** | `SIN_PRONOSTICO` se parte en dos cuando el que falta es **el titular que saldría**; sigue valiendo cero | `acquisition.targets[].xi_decision` · `.xi_reason` · `acquisition.starter_coverage.blocked_by_starter_rule` (hoy **27**) · `roster_expansion.candidates[].blocked_by` · `alarmaDeLosSentidos.sin_pronostico` | **hoy, nada**: 55 de 55 con pronóstico. El día que pase, `SIN_REFERENCIA` con el nombre. **`blocked_by_starter_rule` NO puede bajar** | que `blocked_by_starter_rule` baje sin bajar los objetivos, o un `SIN_REFERENCIA` con `our_value > 0`. **1 vuelta** |
| **6 · CESTA_SOLO_EL_SUELO** | la cesta deja de pujar para revender por encima de **1.500.000** | `subasta.outcomes.placed/.won/.lost` (hoy 13/10/3) · `subasta.bids_book[].source` y `.amount` · `subasta.would_bid`/`.blocked_by` · `roster_expansion.slots.*` | le quita **1 de 10** compras; `placed` casi no se mueve; la plantilla **no encoge**; ahorra **25.501 €**, no un millón | `placed` parado **3 vueltas con ventana abierta**, o una puja `SUBASTA_CARTERA` ≥ 1,5 M. **3 vueltas** |
| **7 · JORNADAS_POR_SU_FECHA** | la hora de cada jornada sale del `roundStarted` del tablón, no del calendario por número | `marcador.resumen.jornadas_medibles` · `.diferencia_media` y `.diferencia_media_n` · `.jornadas_sin_hora` · `.jornadas_fiables` · `marcador.jornadas[].motivo` | medibles **4 → 5**, `diferencia_media` **+20,4 (n=2) → +3,6 (n=3)**, los dos negativos grandes desaparecen. **`jornadas_fiables` sigue en CERO** | que `jornadas_sin_hora` suba de cero, o que `jornadas_medibles` baje de 5. **1 vuelta** |
| **8 · OBJETIVOS_EL_CATALOGO** | la lista de objetivos pasa a cubrir **todo el catálogo**, también los libres | `acquisition.starter_coverage.with_forecast/.total` · `acquisition.targets[].xi_decision` · `lineup.starter_board_players` · `.starter_cache_status` · `losSentidos` | emparejados **142 → 497**, `SIN_PRONOSTICO` **385 → 30**. **Para el mercado del día no cambia NI UNA decisión.** +0,63 s, cero peticiones | que la vuelta tarde **más de un minuto** extra, que `starter_cache_status` falle, o que cambie **una sola** decisión del día. **2 vueltas** |

## En qué orden los encendería, y por qué

> ### 5 · `SIN_REFERENCIA_ESCALA` → 6 · `CESTA_SOLO_EL_SUELO` → 7 · `JORNADAS_POR_SU_FECHA` → 8 · `OBJETIVOS_EL_CATALOGO`

**El criterio es uno: primero lo que cambia lo que se VE, después lo que cambia lo
que se HACE.**

- **El 5 no mueve un euro** — el valor sigue siendo cero en las dos posiciones y hay
  guardia que lo exige. Es lo más barato que puede salir mal, y deja legible la
  pantalla con la que juzgas los otros tres.
- **El 6 sí para operaciones.** Va segundo, y con tres vueltas de ventana abierta
  por delante antes de juzgarlo.
- **El 7 es el más inofensivo de todos** —no toca ninguna decisión de compra ni de
  venta, sólo cómo se ordenan las fotos para medir lo que ya pasó—. Lo pongo
  tercero y no primero sólo porque su efecto se lee mejor con el marcador ya
  estable.
- **El 8 va el último, y no por razón técnica:** es el único que ya rompió una
  vuelta. Encenderlo al final es encenderlo cuando el paso 0 ya ha funcionado con
  los otros siete.

---

## LA VERJA: 171 DE 171

```
  Los 171 en verde. Se puede subir.      exit 0      491 s  (8 min 11 s)
  Corrida 2026-09-20T22:00:56+00:00
```

**Y ese verde incluye el verde con los 21 interruptores puestos**, porque la guardia
nueva corre la verja entera otra vez dentro. No hay que acordarse de nada.

La roja que arrastrábamos dos días —`test_sin_pronostico_v1`— se fue con el bloque 3.



**Los dos veredictos que pediste, medidos con `--todos`:**

```
  TODOS APAGADOS (borrados)   exit 0    220,2 s
  LOS PUESTOS A "1"           exit 0    518,3 s
```

*(La segunda tarda más porque dentro va la guardia nueva, que corre la verja otra
vez.)*

**Y dos cosas que salieron por el camino, las dos mías:**

1. **Mi propio buscador se inventó un interruptor.** `BORDALAS_LO_QUE_SEA`, el
   nombre de ejemplo del mandato del paso 0, salía en el inventario como si
   existiera — porque buscaba el texto y no el código. Arreglado: ahora lee por AST
   y se salta los docstrings. Un interruptor de verdad siempre está en código.

2. **`test_el_libro_sabe_perder_v1` se puso roja por una ficha que escribí yo.**
   Esa guardia exige que el único fichero vivo de `src/` que nombre el campo del
   porcentaje de pujas ganadas sea el propio libro, para que nadie calibre la prima
   de puja con nuestros resultados. Mi ficha de `CESTA_SOLO_EL_SUELO` lo nombraba
   al listar qué mirar. **Cedió mi texto, no la guardia:** la ficha dice ahora
   `placed / .won / .lost`, que enseña lo mismo.

---

## LO QUE NO HICE, Y POR QUÉ

- **No encendí ningún interruptor.** Los ocho del protocolo siguen apagados.
- **No toqué `.github/workflows/bordalas-live.yml`.** El `env` sigue como lo
  dejaste: sin ninguna línea de `BORDALAS_*`.
- **No cambié lo que hace ningún interruptor encendido.** Aquí sólo se han
  arreglado guardias, y el único cambio de producción es de cuatro líneas en el
  corredor de la verja, para que una corrida anidada no pise el veredicto del
  commit.
- **No relajé ni un `assert`.** Las quince se arreglaron fijándoles el caso, no
  bajando el listón. Las que comprueban el comportamiento **con** el interruptor
  puesto siguen comprobándolo.
- **No saqué ninguna guardia de la verja al mirador.** `test_sin_pronostico_v1` se
  queda, con su caso fijo.
- **No arreglé `BORDALAS_HORIZONTE_FIJO`**, que está declarado y no lo lee nadie.
  Lo digo y lo dejo: ponerle cable o quitarlo es una decisión, no una limpieza.
- **No traje el cambio del dashboard** de la rama `encender/el-protocolo` (los 39
  renglones que publican `status.elProtocolo`). El módulo y su guardia sí; la
  pantalla no, porque no lo pedías.
- **No toqué** `MAX_SINGLE_SPECULATION_PERCENT`, `MAX_SAFE_DEBT`, el suelo de cobro,
  `MIN_WIN_PROBABILITY`, `MAX_PROJECTED_DAILY_RATE`, las cinco de
  `PUEDEN_ENCERRARLO`, `PRIMA_MAXIMA_DE_PUJA` ni la ventana de 135 minutos.
- **Ni una escritura contra Biwenger, ni una petición a la red.**
- **No empujo.**

---

## EL `n`, Y CUÁNDO SE CORTÓ

| medida | `n` | corte |
|---|---|---|
| interruptores que existen | **21** (tú listaste 10) | hoy |
| de esos, sin lector | **1**: `HORIZONTE_FIJO` | hoy |
| de esos, leídos al importarse | **0 de 21** | hoy |
| guardias de la verja | **171** | hoy |
| guardias que se caían con algún interruptor | **15** | medido con los 21 puestos |
| de esas, por uno de tu cola de cuatro | **7** | ídem |
| guardias tocadas en total | **18** (15 rotas + 3 con la misma forma) | hoy |
| lo que cazaba la regla estática | **0 de 14** | probado sobre las versiones de antes |
| la verja sin la guardia nueva | **205-220 s** · n=2 | hoy |
| la guardia nueva, ella sola | **275 s** · n=1 | hoy |
| la verja con ella dentro | **~480-518 s** · n=2 | hoy |
| `test_sin_pronostico_v1` | de **2 de 3** scores de la foto a **3 de 3** | foto del 18/09 15:16 |
| ficheros de `data/` que abre esa guardia | **3 → 0** | hoy |
