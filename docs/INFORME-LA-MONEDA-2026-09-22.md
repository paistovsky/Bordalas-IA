# INFORME — LA MONEDA DEL QUE SE QUEDA

**Fecha:** 2026-09-22
**Rama:** `arreglo/la-moneda`, desde `main` en `70e96da`
**Commits:** `fcd0936` (bloque 0, solo) · `a4373d8` (bloques 1, 2 y 4)
**Veredicto:** verja **177/177 verde, exit 0** · paso 0 **OK con los 28, exit 0**.
Con `data/` restaurado antes de cada corrida y después de la última.
**No se ha empujado. No se ha encendido ningún interruptor.**

---

## BLOQUE 0 — EL PASO 0, EN VERDE

Corrido por mí, **antes** de tocar la moneda, y en su propio commit (`fcd0936`):

```
1/1  OK  test_ninguna_guardia_depende_del_entorno_v1     exit 0
PASADO. Quedan probados 27 interruptores.
```

### Qué le faltaba a cada una de las seis, y son **dos causas distintas**

**CUATRO por `BORDALAS_SIN_REVENTA` — y no era un caso incompleto**

`test_encender_las_pujas_v1`, `test_la_puja_del_carril_v1`,
`test_la_regla_de_compra_v1`, `test_una_ventana_que_no_se_abre_v1`.

Su **sujeto es la cesta de reventa**. No hay campo que añadirle a un candidato de
cartera para que sobreviva a un interruptor que cierra la cartera entera: **lo que se
compra para revender ES reventa.** Se caían por su propia guarda de doctrina 24 —«si no,
esta guardia no prueba nada»— diciendo la verdad.

Arreglo: **doctrina 104, la guardia pone su propio interruptor.**
`os.environ.pop("BORDALAS_SIN_REVENTA")`, igual que ya hacían con `BORDALAS_SIN_SUBASTA`.
El comportamiento **con** el puesto lo mide `test_el_corte_y_el_cupo_v1`, que lo enciende
y lo apaga ella.

**DOS casos incompletos — `test_el_corte_y_el_cupo_v1`**

- **`BORDALAS_REVENTA_SOLO_SI_JUEGA`:** sus candidatos no llevaban
  `starter_probability` ni `hierarchy_value`, así que la regla de compra los frenaba a
  todos. Las filas del tablero de verdad los traen; las del caso, ahora también.
- **`BORDALAS_CESTA_SOLO_EL_SUELO`:** el candidato de plantilla costaba **1.660.000** y
  la cesta no mira por encima de `CORTES_DE_PRECIO[0] = 1.500.000`, así que
  **desaparecía antes de llegar al corte**. Baja a 1.190.000 —lo que se mide ahí es la
  **vía**, no el precio— y se añade guardia de que el número siga por debajo del suelo,
  para que no vuelva a caducar en silencio.

**No se ha tocado un solo `assert`, y ningún filtro.**

**`test_peticiones_v1`: no era esto.** Verde sola, verde con los 25 puestos, y **no la
tumba ninguno**. Estaba fichada por saltar 3 de 5 corridas anidadas: es inestabilidad, no
dependencia del entorno. **Queda arrastrada.**

Y `config/paso_0.json` lo reescribe el propio paso 0: **de los 22 de las 10:04 a los 28
de ahora** (27 tras el bloque 0, 28 con el de la moneda).

---

## BLOQUE 1 — DARLE DE COMER AL TECHO DEL QUE SE QUEDA

### De dónde salen los dos datos

```
jornadas que quedan   `remaining_matchdays(matchday)`  player_value_engine.py:712
                      con la jornada que el tablero YA lee para la semilla del
                      desvio: `calendar_state.target_matchday`
                      (acquisition_board.py:616)
                      -> SEASON_MATCHDAYS - jornada + 1, minimo 1

puntos de mas
por jornada           `points_delta`, el delta que calcula el PROPIO motor —el
                      mismo que multiplica por la tarifa— repartido entre las 38
                      de la temporada
```

**No hay un número nuevo.** `remaining_matchdays` ya existía (doctrina 84) y el delta es
el del motor: es el mismo número, en la otra moneda.

De las dos vías de fichaje se coge **la que más vale**, que es la que
`classify_operation` elige (`max(fichaje, key=value)`). Publicar el delta de la otra sería
publicar el de una operación que no se haría.

### Qué pasa cuando no se sabe

**No se inventa.** Sin jornada o sin delta van `None` y `techo_del_que_se_queda` sigue
diciendo lo que ya decía:

> *«Sin los puntos de más por jornada y las jornadas que quedan no se calcula: los dos son
> datos de la liga y suponerlos haría este número lo que uno quiera.»*

Comprobado con los dos a `None`: `available: False`.

### Y ahora se calcula

Sobre las fotos, reconstruyendo la entrada desde lo que publican:

```
foto     filas   techo del que se queda HOY   con el arreglo   siguen en "no lo se"
18/09      54              0                       20                 34
20/09      55              0                       20                 35
```

**De cero a veinte.** Los 34/35 que quedan en «no lo sé» son los que no tienen delta de
ninguna vía de fichaje —sin pronóstico, o la vía no da nada—, y ésos **tienen que**
quedarse en «no lo sé».

Ejemplo, Cabrera el 18/09 (precio 3.040.000, delta 93, jornada 7 → quedan 32):

```
techo del comerciante   3.080.332   = 3.040.000 x (1 + 2,34 %) / 1,01
techo del que se queda  2.349.473   = 78,3 puntos x 30.000 EUR/punto
```

**Los dos viajan juntos en la fila y se publican.** No se ha cambiado cuál decide.

Y una honestidad sobre ese número: **el techo del que se queda es MÁS ESTRICTO que lo que
usa el bloque 2.** Prorratea a las jornadas que quedan (32 de 38) y cuenta sólo los
premios —ni el abono del que sale ni lo que suba el precio—, tal y como dice de sí mismo.
El bloque 2 cambia **la moneda**, no el horizonte. Son dos números distintos y no los
mezclo.

---

## BLOQUE 2 — CADA VÍA CON SU MONEDA

### `BORDALAS_LA_MONEDA_DE_LA_LIGA` — apagado

`src/analysis/la_moneda_del_fichaje.py`.

```
comprar para REVENDER   tarifa del mercado   se lo vendes al mercado
comprar para QUEDARSE   30.000 EUR/punto     te lo quedas y te paga la liga
```

`xi_upgrade_value` **sólo tiene dos llamadores** —la vía del once y la de ficha vacía, las
dos de plantilla— así que la pregunta «¿para qué lo compro?» ya está contestada en el
sitio. Lo único que cambia es **un factor de una multiplicación que ya existe**: margen,
confianza, delta, calendario y vetos se quedan donde estaban. Hay guardia de que el valor
sube **exactamente** en la proporción de la moneda (±2 €, el redondeo).

Los dos números se importan de donde se midieron: `EUROS_POR_PUNTO` de
`caja_de_la_liga`, la tarifa del mercado **se recibe**. Y el vocabulario es el que ya
existía: `SIGNING_ROUTES` e `INTENCIONES_DE_QUEDARSE`.

### La tabla contrafactual

```
                                 hoy      con la moneda de la liga
FOTO 18/09  (n=19 con valor de fichaje, tarifa del mercado 19.914 -> x1,51)
  candidatos que pasan            2                 4
  de esos, via XI_UPGRADE         1                 1
  de esos, via ROSTER_FILL        1                 2
  Dmitrovic                      NO                SI   <- pide 22.607 EUR/punto
  Maffeo                         SI                SI   <- pide 13.719
  Cabrera                        SI                SI   <- pide 15.916

FOTO 20/09  (n=20, tarifa 19.875 -> x1,51)
  candidatos que pasan            0                 4
```

**Los tres renglones de la prueba salen.** Dmitrovic pasa; Maffeo y Cabrera no se caen.

Los cuatro del 18/09: Maffeo (13.719), Cabrera (15.916), Castrín (19.596) y Dmitrovic
(22.607). Los cuatro del 20/09: Moncayola (19.077), Carlos Romero (20.833), Castrín
(22.609) y Álvaro García (25.000).

### ¿Cuántos pasan ahora? **Cuatro al día. No son cincuenta.**

Y el techo **sigue teniendo función**: el nuevo tope efectivo es 30.000 × 0,9 = **27.000
€/punto**, y sobre las dos fotos hay **21 de 39 candidatos por encima** de eso. Nico
Williams pide **60.141 €/punto** y sigue sin pasar — hay guardia de eso, porque si pasara
querría decir que el techo ya no frena a nadie.

Cuatro al día es el ritmo de Pollo17: 54 viajes en 43 días.

---

## BLOQUE 3 — LOS CINCO NÚMEROS A OJO

No se han tocado. Medida su sensibilidad sobre las dos fotos con valor de fichaje
calculado (**n=19 el 18/09, n=20 el 20/09**), contando **cuántos candidatos pasan**:

```
                                      18/09 (base 2)   20/09 (base 0)
margen 0,10  ->  la mitad (0,05)          2  (+0)          0  (+0)
margen 0,10  ->  el doble  (0,20)         1  (-1)          0  (+0)

recovered_value 0 -> contar el abono      3  (+1)          2  (+2)
                     del que sale
```

**Manda `recovered_value`, y el margen casi da igual.** Duplicar el margen quita uno;
contar lo que se recupera vendiendo al sustituido añade uno y dos. Y es el número con la
justificación más floja de los cinco: *«lo prudente es suponer que se queda de suplente y
no entra caja»*. El tablero ya publica ese abono (`abono_return`, media 663.158 € el
18/09).

Los otros tres **no multiplican: cortan**, y se ven en `xi_decision`:

```
motivo de rechazo del once        18/09 (n=54)   20/09 (n=55)
  NO_MEJORA_JERARQUIA                 14             19     <- la escalera
  NO_MEJORA                           10             10
  NO_MEJORA_TITULARIDAD               10              8
  PIERDE_TITULARIDAD                   7             11     <- STARTER_SWAP_*
  MEJORA_INSUFICIENTE                  1              2     <- MIN_DELTA = 8
  SIN_PRONOSTICO                       4              0
```

**`STARTER_SWAP_MIN_DELTA = 8` da igual** (1 y 2 casos). **La escalera de jerarquía es el
mayor rechazo de los dos días.**

### La jerarquía: cuánto pesa y si acierta

**No pesa: corta.** No multiplica el valor en ningún sitio. Entra por tres vetos:
`NO_SE_TOCA_UN_DIOS`, `NO_MEJORA_JERARQUIA` (bajar ≥ 2 escalones) y `roster_fill_veto`
(por debajo de 40 no se ocupa ficha). Es un sí/no.

**¿Acierta?** Contra los puntos por partido jugado, **n=80 jugadores distintos** de las
tres fotos:

```
jerarquia           n    pts/partido mediano    min     max
20  Reserva        13           3,33          -2,00    7,00
25  Revulsivo      12           2,90           2,00    7,14
30  Rotacion       26           3,38           1,50   12,00
40  Importante     16           4,47           1,40    8,17
50  Clave          13           3,60           1,33    7,33
```

**No ordena.** «Clave» (50) puntúa **menos** por partido que «Importante» (40), y
«Reserva» (20) puntúa como «Rotación» (30). Ocho de diez pares en orden, que es poco más
que tirar una moneda con cinco categorías. Y la dispersión **dentro** de cada banda es
enorme: en Rotación va de 1,50 a 12,00.

**Tu sospecha se confirma:** la etiqueta que más corta es la que menos ordena. *(Cabrera
sale a 2,67 puntos por partido siendo «Clave» — por debajo de la mediana de «Reserva».)*

**No lo he tocado**, como pide el encargo. Pero si algún día se toca uno de los cinco, el
orden que sale de esto es: **la escalera primero, `recovered_value` después, el margen y
el `MIN_DELTA` casi nunca.**

---

## BLOQUE 4 — QUE ESTA PREGUNTA SE PUEDA VOLVER A HACER

**Medido, no construido** — el encargo pide el tamaño y dónde, y las tres piezas son
cambios de producción que decide el dueño.

### Una foto después de cada jornada

No hace falta la foto entera (**519 KB**). Con `id`, `name`, `teamID`, `position`,
`price`, `points`, `playedHome/Away`, `fitness` y `pointsLastSeason` de los 547:

```
102 KB por jornada  ->  429 KB al mes  ->  3,79 MB la temporada entera
```

**Dónde:** `data/fotos/` ya existe y ya es un libro versionado (ahí vive
`2026-09-18.json`). Una por jornada, disparada por `roundFinished`, que es el evento que
ya se lee.

### Un libro de aciertos de la valoración

Una fila por candidato valorado: qué valor le dimos, con qué delta, qué tarifa, qué
confianza, qué decisión — y el hueco para lo que pasó después.

```
347 B por fila  ->  19 filas/dia: 193 KB al mes
                    54 filas/dia: 549 KB al mes
```

Es el más barato de los tres y el único sin el que **la fórmula no se puede calibrar
nunca**. Es el mismo argumento que abrió `libro_de_publicacion.jsonl` el 10/09.

### El registro de la vuelta a git

**El motivo que lo impedía ya no es verdad, y lo he corregido en el código.**

`los_libros.py` decía:

> *«`prune_github_state.py` los trunca DESPUÉS del ciclo y ANTES del guardado. Si se
> metieran en la lista se commitearía la versión podada.»*

El workflow de hoy tiene **`Guardar los libros` en la línea 270** y **`Prune persisted
state` en la 278**. Invertidos. **El motivo ha desaparecido.**

**¿Sigue teniendo sentido la guardia?** **Sí.**
`test_ningun_libro_se_clasifico_dos_veces` comprueba que un fichero no esté en las dos
listas a la vez, y eso vale con cualquier orden del workflow. **Lo que había caducado era
el MOTIVO, no la guardia** — así que he reescrito el comentario para que diga la verdad y
deje constancia de que ahora es **una decisión del dueño, no una restricción**, con su
coste: 6,4 MB al mes, **12,1 MB estables** podado a 2.000 líneas (57 días de historia).
El repositorio ya versiona `scout_accuracy_ledger.json`, que son 31 MB.

**No lo he metido en `LIBROS`**: eso empieza a commitear un fichero de 10 MB cada hora, y
es tuyo.

---

## LO QUE SE HA TOCADO

```
COMMIT fcd0936 — BLOQUE 0, SOLO
  test_encender_las_pujas_v1.py          ponen su propio interruptor
  test_la_puja_del_carril_v1.py          (doctrina 104)
  test_la_regla_de_compra_v1.py
  test_una_ventana_que_no_se_abre_v1.py
  test_el_corte_y_el_cupo_v1.py          dos casos completados + guardia del suelo
  config/paso_0.json                     lo reescribe el paso 0: 22 -> 27

COMMIT a4373d8 — BLOQUES 1, 2 y 4
  la_moneda_del_fichaje.py         NUEVO   la moneda, apagada
  test_la_moneda_del_fichaje_v1.py NUEVO   9 guardias
  acquisition_board.py                     le da de comer al techo del que se queda
  player_value_engine.py                   la tarifa pasa por la moneda
  test_player_value_v1.py                  se ata a la tarifa APLICADA
  estado/los_libros.py                     el motivo caducado, corregido
  run_validation_gate.py                   la guardia en la verja
  config/paso_0.json                       27 -> 28
```

---

## LO QUE NO SE HA HECHO, Y POR QUÉ

| | por qué |
|---|---|
| **Ni una escritura contra Biwenger** | lo prohíbe el encargo |
| **Ningún interruptor encendido** | son 28 y los seis nuevos del día siguen apagados |
| **El workflow, intacto** | lo prohíbe el encargo |
| **`BORDALAS_SIN_SUBASTA` sigue en el código** | es el freno de mano; lo quitado es su línea del YAML |
| **Los cinco números a ojo, sin tocar** | el bloque 3 mide su sensibilidad |
| **El techo del comerciante, sin tocar** | la reventa lo sigue usando y es el correcto para ella |
| **No se ha cambiado qué techo decide** | el bloque 1 pide que exista y se vea, nada más |
| **Las ramas viejas, sin juntar ni borrar** | lo prohíbe el encargo |
| **No se ha tocado** `MAX_SINGLE_SPECULATION_PERCENT`, `MAX_SAFE_DEBT`, el suelo de cobro, `MIN_WIN_PROBABILITY`, `MAX_PROJECTED_DAILY_RATE`, `PUEDEN_ENCERRARLO`, `PRIMA_MAXIMA_DE_PUJA`, `VENTANA_MINUTOS` | lo prohíbe el encargo |
| **No se ha empujado** | «Tú no empujas» |
| **`test_peticiones_v1` sigue sin arreglar** | no depende del entorno: es inestable. El encargo dice arrastrarlo |
| **La foto por jornada y el libro de aciertos, sin construir** | el bloque 4 pide el tamaño y el sitio; construirlos toca producción y es tuyo |
| **El registro de la vuelta, sin meter en `LIBROS`** | el motivo ya no existe, pero empezar a commitear 10 MB cada hora es tuyo |

---

## LO QUE QUEDA APUNTADO

Cinco ficheros vivos en dos ramas viejas, **sin tocar en este encargo**, para que no se
vayan cuando se borren las cinco vacías:

```
carril/el-liston-propio    src/analysis/el_liston_propio.py + su guardia
encender/el-protocolo      scripts/comparar_dos_fotos.py
                           test_dice_como_se_libera_v1.py
                           test_el_financiero_no_borra_candidatos_v1.py
```
