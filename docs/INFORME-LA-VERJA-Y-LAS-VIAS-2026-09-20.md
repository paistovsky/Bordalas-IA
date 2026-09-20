# LA VERJA ROJA Y QUÉ COMPRA CADA VÍA

**Fecha:** 2026-09-20 (segundo del día) · **Rama:** `arreglo/la-verja-roja`, desde
`medir/la-ventana` (la base con las cinco rojas, más el informe de esta mañana) ·
**Escrituras contra Biwenger:** ninguna · **Umbrales tocados:** ninguno ·
**Interruptores encendidos:** ninguno.

**Verja: de 5 rojas a 2.** Tres arregladas —eran un solo defecto y su consecuencia—,
dos sin tocar porque el arreglo decide algo. Y una guardia nueva, la que pediste.

---

## BLOQUE 1 — LAS CINCO ROJAS

### Antes de las cinco: nadie empujó nada roto

El encargo dice *«si llevan rojas varios días, alguien empujó algo roto y la verja no
lo paró»*. **No pasó eso.** Los dos commits que las rompieron son de anoche y
**ninguno está empujado**:

```
c5ca23b  NO esta en origin/main
5274359  NO esta en origin/main
```

Y lo confirma la producción: `diagnostico/status.json`, generado a las 09:10 de hoy
por una vuelta real, tiene 64 claves y **no trae `revisionDelCupo`** — la clave que
`c5ca23b` añade. Producción corre sin esos commits. La verja hizo exactamente su
trabajo: las cazó en el banco.

Lo que sí es cierto, y es la lección: **ninguno de los tres commits de anoche dice
haber pasado la verja.** Los de antes sí lo decían.

### Las cinco

| # | guardia | qué comprueba | por qué falla | desde cuándo |
|---|---|---|---|---|
| 1 | `test_dashboard_orden_de_variables_v1` | por AST, que `build_dashboard_state` no use una variable antes de asignarla | el literal que construye `dashboard` se lee **a sí mismo** | `c5ca23b`, 19/09 20:01 · **arreglada** |
| 2 | `test_el_ciclo_publica_v1` | que `build_dashboard_state()` corra entera | el mismo defecto, ya en ejecución: `UnboundLocalError` | idem · **arreglada** |
| 3 | `test_la_lista_blanca_v1` | que toda clave publicada la nombre `normalizeStatus` | `revisionDelCupo` se publica y `status.js` no la recoge | idem · **arreglada** |
| 4 | `test_presupuesto_de_fichar_v1` | por AST, que todo `executable_buys[0]` lleve guardia | el código se hizo **más seguro** y el patrón de la guardia no lo reconoce | `5274359`, 19/09 20:08 · **sin tocar** |
| 5 | `test_orden_de_venta_v1` | que el portero titular se aparte por ser portero, no por accidente | nombra a **«Dituro»**, vendido **hoy a las 08:55** | hoy, ~09:16 · **sin tocar** |

### 1, 2 y 3 son un solo defecto — arreglado

`c5ca23b` añadió al panel el recordatorio de que los cupos caducan el 26/09. Su
comentario dice, literalmente, *«La fecha de hoy se le PASA —del `generated_at` de
esta misma foto—, no la deduce del reloj»*. La intención es buena. La ejecución fue:

```python
dashboard = {
    "meta": {"generated_at": datetime.now().isoformat(...)},
    ...
    "revisionDelCupo": _revision_del_cupo(
        dashboard["meta"]["generated_at"]      # <- dentro del propio literal
    ),
}
```

El lado derecho se evalúa **entero** antes de la asignación, así que `dashboard` no
existe todavía: `build_dashboard_state` reventaba con `UnboundLocalError` **en cada
vuelta**. Y la clave nueva no estaba en `normalizeStatus`, que es la lista blanca del
lector: aunque hubiera llegado, moría en `raw`.

**Arreglo, sin decidir nada:** la hora se calcula una vez en una variable y se pasa
—que es lo que el comentario decía que se hacía—, y `revisionDelCupo` se recoge en
`dashboard-v8/src/lib/status.js` con la forma de su fallback, como las demás.

```
test_dashboard_orden_de_variables_v1   7/7 OK
test_el_ciclo_publica_v1               3/3 OK
test_la_lista_blanca_v1                3/3 OK
```

### 4 es un falso positivo: la guardia se quedó vieja, el código no

La guardia recorre el AST y exige que todo `executable_buys[0]` viva dentro de un
`IfExp` cuyo test sea **exactamente** `ast.Name("executable_buys")`. El 19/09
`5274359` endureció esa misma línea:

```python
executable_buys[0]
if executable_buys and se_sabe_que_hay_puesto(speculation)   # <- ahora es un BoolOp
else None
```

El código es **estrictamente más seguro** que cuando se escribió la guardia: con la
lista vacía cortocircuita igual, y además se abstiene si no se pudo mirar lo puesto.
La guardia se pone roja por no reconocer el `and`.

**No la toco.** Ensanchar el patrón cambia lo que una guardia acepta, y eso decides
tú. El cambio mínimo sería aceptar también un `ast.BoolOp` entre cuyos `values` esté
el `Name`; son cuatro líneas en
[test_presupuesto_de_fichar_v1.py:551](src/analysis/test_presupuesto_de_fichar_v1.py#L551).
Dime y lo hago.

### 5 no es un fallo de código: es una guardia que mira producción

`test_el_portero_titular_no_se_salva_por_accidente` busca **a Dituro por su nombre**
dentro de `diagnostico/status.json`. Ese fichero **no está versionado**: lo regenera
cada vuelta. Hoy a las 08:55 el tablón registró:

```
20/09 08:55  transfer  Dituro  de Pepe Bordalas  ->  2.188.300
```

A las 09:16 la foto se rehízo sin él y la guardia se puso roja. **Estaba verde ayer y
no ha cambiado ni una línea de código.** El portero titular de hoy es Dmitrovic.

Es el mismo fallo que ya está documentado en
[carril_executor.py:185](src/actions/carril_executor.py#L185) —«08:23 verde · 10:07
verde · 10:50 ROJO, mismo commit»— y contra el que existe la regla de la casa:
ninguna guardia lee estado de producción.

**No la toco**, porque el arreglo es una decisión de verdad y hay tres salidas
distintas:

1. **Preguntar por el puesto, no por el nombre**: buscar al portero con
   `is_starter: true` en lugar de a Dituro. Sigue leyendo producción, así que seguirá
   cambiando de color sin que cambie el código.
2. **Congelar una foto de fixture** en el repositorio y probar contra ella. Deja de
   leer producción, y deja de ver la producción de verdad.
3. **Retirar el caso de producción** y quedarse con los 18 de fixture que ya pasan.

Mi voto es la **2**: la guardia existe para comprobar que `untouchable_reason`
normaliza `is_starter`, que es una propiedad del código, no del mercado de hoy.

---

## BLOQUE 2 — QUÉ COMPRA CADA VÍA

### Primero: cuántas vías hay, y ayer me equivoqué al contarlas

**Cuatro vías en el código.** Y `DESCONOCIDO` **no es una de ellas** — ayer la conté
como vía y estaba mal. Es `ORIGEN_SIN_PROBAR`, la etiqueta que
[bid_outcome_ledger.py:544](src/intelligence/bid_outcome_ledger.py#L544) pone a una
compra cuya vía no se pudo **probar** contra el libro del carril.

| vía | dónde decide | dónde escribe | pujas puestas |
|---|---|---|---|
| `ACQUISITION_BOARD` | [decision_orchestrator.py:2858](src/analysis/decision_orchestrator.py#L2858) | `autopilot_executor` | 2 |
| `SPECULATION_SCORING` | [decision_orchestrator.py:2800](src/analysis/decision_orchestrator.py#L2800) | `autopilot_executor` | **0, nunca** |
| `RENDIJA` | `la_rendija` | `carril_executor` | 16 filas · 4 operaciones |
| `SUBASTA_CARTERA` | `la_subasta` (la cesta) | `v10_full_autonomous_live` | 13 |

**Una de las cuatro no ha escrito una puja en toda la temporada.** El respaldo del
scoring antiguo existe, tiene código y guardias, y su marca no aparece ni una vez en
el libro.

### El `n` limpio: el importe sale del TABLÓN, no del libro

Tenías razón con Chust: el libro guarda **1.871.032** y pagamos **1.887.000**. El
libro anota la puja que se envía; el tablón anota lo que se cobró. Así que:

- **el importe** de cada compra y de cada venta sale de `board_events.json`
  (eventos `market` y `transfer`);
- **la vía** sale de `bid_outcome_ledger`, cruzando por jugador y ciclo de reset.

Dos correcciones más que hice sobre la marcha, y las digo porque cambian números:

- **El tablón trae eventos duplicados** el 10, 11 y 12/08 —mismo contenido, `event_id`
  distinto—. Sin deduplicar, Yamal, Jonny y Suazo salían comprados dos veces.
- **Una posición comprada dos veces** (Jonny: 10/08 y 23/08) no puede contar el valor
  de hoy en las dos. Cada compra se cierra con la **primera venta posterior**; si no
  la hay, la posición sigue abierta y vale el precio de hoy.

Sin ese segundo arreglo la vía del dueño salía **+1.046.231**. Con él sale
**−1.303.769**. La diferencia era Jonny contado dos veces.

**Compras de Pepe en el tablón, sin duplicar: 36.** Ventas: 36.

### La tabla

| vía | ops | abiertas | puntos hoy | pagado | recuperado | valor hoy | NETO |
|---|---:|---:|---:|---:|---:|---:|---:|
| `SUBASTA_CARTERA` | 10 | 1 | **0** | 3.047.610 | 2.900.600 | 150.000 | **+2.990** |
| `RENDIJA` | 4 | 0 | **0** | 7.534.123 | 7.259.900 | 0 | **−274.223** |
| `ACQUISITION_BOARD` | 2 | 1 | 22 | 4.103.165 | 1.159.000 | 2.510.000 | **−434.165** |
| **el motor, las tres** | **16** | **2** | **22** | **14.684.898** | **11.319.500** | **2.660.000** | **−705.398** |
| **EL DUEÑO** | **20** | **11** | **315** | **60.946.482** | **12.862.713** | **46.780.000** | **−1.303.769** |

**El NETO mezcla realizado y no realizado**, y eso hay que separarlo porque las vías
del motor cierran en días y el dueño aguanta:

| | operaciones cerradas | **realizado** | abiertas | no realizado |
|---|---:|---:|---:|---:|
| `SUBASTA_CARTERA` | 9 | **+3.366** | 1 | −376 |
| `RENDIJA` | 4 | **−274.223** | 0 | — |
| `ACQUISITION_BOARD` | 1 | **−70.925** | 1 | −363.240 |
| EL DUEÑO | 9 | **+309.377** | 11 | −1.613.146 |

El −1.613.146 del dueño es casi todo **Yamal**: pagado 24.897.600, vale hoy
22.530.000, **−2.367.600**. Sin Yamal, sus diez posiciones abiertas van **+754.454**.
No es una operación mala: es la única que pesa lo suficiente para mover el total.

#### `SUBASTA_CARTERA` — la cesta

```
12/09  Fortuño          150.376  ->    153.800    +3.424   cerrada
12/09  Diego Conde      240.601  ->    250.700   +10.099   cerrada
15/09  Selu Diallo      150.376  ->    156.200    +5.824   cerrada
15/09  Balde          1.604.001  ->  1.578.500   -25.501   cerrada
15/09  Benavidez        150.376  ->    151.100      +724   cerrada
15/09  Paco Cortés      150.376  ->    151.200      +824   cerrada
18/09  Marcão           150.376  ->    151.500    +1.124   cerrada
18/09  Esquivel         150.376  ->    151.200      +824   cerrada
18/09  Barzic           150.376  ->    156.400    +6.024   cerrada
18/09  Iturbe           150.376      vale 150.000   -376   ABIERTA, 0 puntos
```

Partida en dos, que es donde está la información:

| | n | pagado | recuperado | neto | % |
|---|---:|---:|---:|---:|---:|
| a precio de suelo (≤250 k) | 9 | 1.443.609 | 1.472.100 | **+28.491** | **+1,97 %** |
| la única grande (Balde) | 1 | 1.604.001 | 1.578.500 | **−25.501** | −1,59 % |

> **Las nueve del suelo ganaron 28.491 € y la única apuesta grande perdió 25.501.**
> Una operación de 1,6 M se comió el 90 % de lo que ganaron nueve de 150 k.

#### `RENDIJA` — el carril

```
13/09  Trent    2.760.000 -> 2.536.500  -223.500
17/09  Drkusic  1.292.476 -> 1.256.100   -36.376
18/09  Boyomo   1.817.297 -> 1.845.800   +28.503
19/09  Maffeo   1.664.350 -> 1.621.500   -42.850
```

**−274.223 € sobre 7.534.123 movidos: −3,6 %.** Una de cuatro en verde. Y estas
cuatro operaciones costaron **16 escrituras** contra Biwenger: los nueve Maffeo y los
cinco Boyomo.

#### `ACQUISITION_BOARD` — el tablero de fichajes

```
06/09  Kiko Femenía   1.229.925 -> 1.159.000   -70.925   cerrada
13/09  Rubén García   2.873.240    vale 2.510.000        ABIERTA, 22 puntos
```

**n = 2.** Es la única vía que ha comprado un punto en toda la temporada, y es una
anécdota, no un rendimiento (doctrina 55).

#### EL DUEÑO — `DESCONOCIDO` + las que no están en ningún libro

```
10/08  Yamal          24.897.600   vale 22.530.000  -2.367.600   88 pts
10/08  Jonny           1.570.000 ->  1.753.200        +183.200   cerrada
10/08  Gabriel Suazo   1.629.832 ->  1.788.400        +158.568   cerrada
17/08  Yusi Enríquez     504.000 ->  1.226.068        +722.068   cerrada
18/08  #38072          1.200.001 ->  1.346.045        +146.044   cerrada
19/08  Zubeldia        2.068.001 ->  1.847.000        -221.001   cerrada
19/08  Cepeda            463.500 ->    681.000        +217.500   cerrada
20/08  #2169           2.288.001 ->  1.930.700        -357.301   cerrada
20/08  Djené           2.409.001 ->  1.870.100        -538.901   cerrada
22/08  Pablo Ibáñez    2.079.001   vale  2.510.000    +430.999   30 pts
23/08  Jonny           1.925.100   vale  2.350.000    +424.900   21 pts
27/08  Pablo Durán       236.531   vale    420.000    +183.469   26 pts
29/08  Manu Sánchez    1.564.837   vale  1.800.000    +235.163   17 pts
05/09  Expósito        5.147.000   vale  5.330.000    +183.000   35 pts
15/09  Oriol Rey       1.122.020   vale  1.190.000     +67.980   19 pts
16/09  Álvaro Carreras 1.426.025   vale  1.370.000     -56.025   21 pts
17/09  Lunin             421.000 ->    420.200            -800   cerrada
19/09  Cabrera         3.116.031   vale  2.790.000    -326.031    9 pts
20/09  Chust           1.887.000   vale  1.830.000     -57.000   21 pts
20/09  Dmitrovic       4.992.001   vale  4.660.000    -332.001   28 pts
```

Dos jugadores (`#38072`, `#2169`) no tienen nombre en ningún libro que guardemos: se
vendieron antes de que ninguna foto los recogiera. Lo digo en vez de inventarlos.

### Las tres preguntas que cierran el bloque

#### ¿Alguna vía compra puntos?

> **Ninguna vía del motor compra puntos.**

Las tres juntas, **16 operaciones**, han traído **22 puntos**, y los 22 son de **un
solo jugador** —Rubén García— por la vía que lleva **n = 2**. La cesta y el carril,
que son 14 de las 16 operaciones, han traído **cero**.

El dueño, con 20 operaciones, ha traído **315 puntos** en la plantilla de hoy. Los
tres mayores —Yamal 88, Expósito 35, Pablo Ibáñez 30— los puso él a mano, igual que
Chust, Dmitrovic y Cabrera.

#### ¿Alguna vía gana dinero?

Tenías razón en que la pregunta correcta para las de suelo es el euro y no el punto.
La respuesta, en realizado:

| vía | realizado | sobre | tasa | n |
|---|---:|---:|---:|---:|
| `SUBASTA_CARTERA` | **+3.366** | 2.896.844 | **+0,12 %** | 9 |
| `RENDIJA` | **−274.223** | 7.534.123 | **−3,64 %** | 4 |
| `ACQUISITION_BOARD` | −70.925 | 1.229.925 | −5,77 % | 1 |
| EL DUEÑO | **+309.377** | 14.166.436 | +2,18 % | 9 |

**Una gana dinero y apenas:** la cesta, +3.366 € en ocho días sobre un presupuesto de
fichar de 6,75 M. El comercio del suelo funciona —+1,97 % sobre nueve— pero es tan
pequeño que la única operación grande de la vía se lo comió entero.

**Ninguna gana puntos y ninguna gana dinero de verdad.** Es el mismo hecho visto dos
veces: las vías del motor están comprando **relleno**, y el relleno rinde lo que rinde
el relleno.

#### ¿Cuál merece seguir viva?

Mi recomendación, y la decides tú.

**`ACQUISITION_BOARD` — la que hay que alimentar.** Es la única apuntada al once y la
única que ha comprado un punto. Su problema no es el rendimiento: es que sólo ha
pujado **dos veces en la temporada**. Con `n = 2` no se juzga; se le da volumen y se
vuelve a mirar.

**`SUBASTA_CARTERA` — viva, y estrechada al suelo.** Gana poco pero gana, cuesta dos
vueltas al día y una ficha, y cierra en días. La única medición que tiene por encima
del suelo (Balde, 1,6 M) es la única perdedora de la vía. **No ensancharla** —como ya
dice el encargo— y, si acaso, apretarle el techo por operación. `n = 9` abajo y
`n = 1` arriba: no es para decidir hoy, es para volver a mirarlo el 26/09 con los
cupos.

**`RENDIJA` — la que vigilaría.** Es la única que pierde dinero medido
(−274.223 €, −3,6 %) y la que produjo las 12 escrituras repetidas de 16. Pero
**`n = 4` es una anécdota**, y apagar una vía con cuatro datos sería cometer la
doctrina 95 en la dirección contraria. Lo que sí haría ya, y no es apagarla, es
encender `filtrar_los_repetidos`: su coste en escrituras está medido (12 de 16
sobraban) aunque su cuenta de resultados no lo esté.

**`SPECULATION_SCORING` — la que hay que mirar de frente.** Cero pujas en toda la
temporada. O sobra, o hay una puerta que no abre nunca y nadie lo sabía. Yo lo
comprobaría antes que ninguna otra cosa de esta lista: código muerto que parece vivo
es peor que código apagado.

### El número corregido de volumen

El 21 % estaba contaminado por 30 días sin mecanismo. Con el corte donde toca —el
12/09, primer reset con la cesta escribiendo—:

| tramo | subastas | aparecemos | **%** | ganamos | conversión | días |
|---|---:|---:|---:|---:|---:|---:|
| antes de la cesta | 172 | 27 | 15,7 % | 17 | 63,0 % | 32 |
| **desde la cesta (12→20/09)** | **60** | **22** | **36,7 %** | **21** | **95,5 %** | **9** |

> **Desde que existe la cesta aparecemos en el 36,7 % de las subastas y ganamos el
> 95,5 % de esas.** `n = 60 subastas`, 9 días de reset, corte el **20/09 a las 09:33**,
> que es cuando la última vuelta escribió el tablón.

El volumen se multiplicó por **2,3** y la conversión subió de 63,0 % a 95,5 %. Lo que
la tabla de arriba añade es lo que esas 21 subastas ganadas compraron: relleno.

---

## BLOQUE 3 — LA CESTA ES INVISIBLE AL CUPO

### Qué habría frenado el cupo de 3, con nombre

**(a) Un cupo propio para la cesta: cuatro escrituras frenadas.**

| reset | hora | jugador | importe | qué pasó de verdad |
|---|---|---|---:|---|
| 12/09 | 04:52 | **Sotelo** | 1.604.001 | perdida igual (`RESET_SIN_JUGADOR`) |
| 15/09 | 04:54 | **Selu Diallo** | 150.376 | ganada, vendida **+5.824** |
| 18/09 | 04:53 | **Esquivel** | 150.376 | ganada, vendida **+824** |
| 18/09 | 04:53 | **Carmona** | 671.676 | perdida igual (`RESET_SIN_JUGADOR`) |

Dos de las cuatro se habrían perdido de todas formas. Las otras dos ganaron
**6.648 €** entre las dos — que sobre los **+3.366** realizados de la vía significa
que **el cupo de 3 habría puesto la cesta en números rojos**: +3.366 → **−3.282**.

No es un argumento para no ponerlo. Es la medida de lo pequeño que es lo que la cesta
gana: cabe entero en dos operaciones de 150 k.

**(b) Un cupo común con el carril: quince escrituras frenadas** — y la cesta se queda
a **cero** el 18/09.

```
reset 18/09
  01:12  RENDIJA  Boyomo      <- gasta 1
  02:12  RENDIJA  Boyomo      <- gasta 2   (el mismo jugador)
  03:11  RENDIJA  Boyomo      <- gasta 3   (el mismo jugador)
  --- cupo agotado ---
  04:49  CESTA    Marcão      FRENADA
  04:49  CESTA    Barzic      FRENADA
  04:49  CESTA    Iturbe      FRENADA
  04:53  CESTA    Esquivel    FRENADA
  04:53  CESTA    Carmona     FRENADA
```

### Cupo común o uno por vía

> **Uno por vía. Y el motivo no es que compren cosas distintas: es que con un cupo
> común la repetición de una vía se convierte en un recorte de volumen de la otra.**

La noche del 18/09 lo enseña entero. El carril repitió **tres veces el mismo
jugador** —un fallo de identidad, no de volumen— y con un cupo común esas tres
repeticiones habrían apagado la cesta antes de que despertara. La cesta no habría
hecho nada malo y habría pagado la factura de otro.

Es la doctrina 93 al pie de la letra: **el cupo es volumen, la repetición es
identidad.** Un cupo común mezcla las dos y deja que un fallo de identidad actúe de
recorte de volumen en una vía que no tuvo nada que ver.

Y hay un segundo motivo, más aburrido y más fuerte: **un cupo común lo gasta quien
escribe primero en el reloj**, no quien compra mejor. El carril escribe de noche y la
cesta a las 04:45. No hay ninguna lectura del reparto en la que el orden del reloj sea
el criterio correcto.

Tu formulación —«el relleno se comería las plazas de lo bueno»— llega a la misma
conclusión por otro camino, y el bloque 2 la confirma sólo a medias: **las dos vías
compran relleno**, la cesta a 150 k y el carril a 1,8 M. Ninguna compra puntos. Así
que no es que una sea buena y la otra no; es que un cupo compartido no protege a
ninguna de las dos.

**El número lo pones tú.** Lo único que yo diría con lo medido: los picos legítimos
de la cesta son 4, 4 y 5 por reset, así que un 3 no es un tope holgado para ella —es
un recorte.

### Lo que no cablée, y por qué

**No he cableado el cupo a la cesta.** Es un camino de escritura y el encargo dice
medir antes de cablear. Y queda una cosa antes: la cesta escribe en
`bid_outcome_ledger` y el cupo lee `libro_del_carril.jsonl`, así que cablearlo hoy
contaría cero y dejaría pasar todo.

---

## LA GUARDIA NUEVA

`src/analysis/test_cada_compra_sabe_de_que_via_vino_v1.py`, **5 pruebas, registrada
en la verja**. No lee `data/`, ni la red, ni el reloj: código del repositorio y
fixtures en un temporal. Y falla si el conjunto que tiene que revisar sale vacío.

| prueba | qué exige |
|---|---|
| `test_toda_escritura_del_motor_pasa_su_via` | los **3** sitios que llaman a `record_bid` pasan `target_source=` — si alguien abre una vía y se olvida, sus compras nacen sin dueño |
| `test_las_marcas_que_se_escriben_estan_declaradas` | ninguna marca literal del motor queda sin nombrar |
| `test_el_origen_se_prueba_cuando_el_libro_lo_prueba` | si el libro prueba la fila, el origen **no** es `DESCONOCIDO` |
| `test_sin_libro_no_se_inventa_una_via` | y si no se puede probar, se dice `DESCONOCIDO` y no se adivina |
| `test_la_cesta_no_deja_rastro_en_el_libro_del_carril` | **deja el agujero a la vista**: mientras la cesta no escriba en el libro del carril, una puja suya redescubierta del tablón pierde su vía |

La última es la que importa. Hoy la atribución de la cesta sale bien porque anota su
fila en el mismo instante en que puja. El día que una vuelta muera entre la escritura
y el apunte —**que ya pasó el 18/09 con la #1701**— esa compra aparece en la cuenta
sin dueño. La prueba está escrita para saltar cuando alguien tape el agujero, no para
exigir que se tape: es un camino de escritura y lo decides tú.

---

## LO QUE NO HICE, Y POR QUÉ

- **No arreglé las dos rojas que quedan.** Las dos tienen más de una salida razonable
  y elegir es decidir. Van arriba con las opciones y mi voto.
- **Ni una escritura contra Biwenger.** Todo de disco: `board_events.json`,
  `bid_outcome_ledger.json`, `libro_del_carril.jsonl`, `diagnostico/status.json` y las
  106 fotos de `data/snapshot_*.json`.
- **No toqué la ventana, ni ensanché la cesta, ni apagué ninguna vía, ni encendí
  ningún interruptor, ni puse ningún número nuevo, ni toqué el workflow.**
- **No cablée el cupo a la cesta** (arriba, con su motivo).
- **No arreglé que la cesta no escriba en `libro_del_carril.jsonl`.** Camino de
  escritura. La guardia nueva lo deja visible.
- **No juzgué `RENDIJA` con `n = 4` ni `ACQUISITION_BOARD` con `n = 2`.** Doctrina 55.
- **No pude nombrar a `#38072` ni a `#2169`.** No están en ningún libro que guardemos.

### La verja

```
158 de 160 OK      (eran 154 de 159)
FALLAN 2:
  src.analysis.test_presupuesto_de_fichar_v1     falso positivo, decide el dueño
  src.analysis.test_orden_de_venta_v1            lee produccion, decide el dueño
```

Salida completa a fichero, árbol quieto, sin `git add -A`. **No empujo.**

### El `n`, y cuándo se cortó

| medida | `n` | corte |
|---|---|---|
| compras de Pepe en el tablón | **36** (sin duplicar; 39 con los duplicados de agosto) | tablón a 20/09 09:33 |
| ventas de Pepe en el tablón | **36** | idem |
| apariciones desde la cesta | **60 subastas · 22 · 21** | 12→20/09, 9 días |
| la cesta | **10 ops** · 9 cerradas | 12→18/09, 8 días |
| el carril | **4 ops**, todas cerradas | 13→19/09 |
| el tablero de fichajes | **2 ops** | 06/09 y 13/09 |
| el dueño | **20 ops** · 9 cerradas | 10/08→20/09 |
| precio del punto | 21.486 €, banda ±1,8 % | `points_market.rate_median` |

Dos denominadores se movieron mientras medía y doy las dos cifras: las **36** compras
frente a las **39** sin deduplicar, y el tablón de **225** subastas de esta mañana
frente a **232** con el reset de hoy.
