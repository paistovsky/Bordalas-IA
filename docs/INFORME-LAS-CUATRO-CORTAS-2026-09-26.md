# INFORME — LAS CUATRO CORTAS DEL ONCE OBJETIVO

**Fecha:** 26/09/2026 · **Rama:** `medir/el-once-objetivo`, encima de `c6334cd1`
**Solo medición.** No se enciende nada, no se ejecuta el plan y no se toca el once de producción.
Salidas completas: `salida-el-once-objetivo.txt` (tablero de FutbolFantasy del 22/09) y
`salida-el-once-objetivo-catalogo.txt` (tablero de hoy con el catálogo encendido).

---

## En seis líneas

1. **Fuera de todo once:** `injured`, `sanctioned`, `discarded` y `unknown`. **`doubt` se queda en
   el de la temporada y juega al 24 % en el de la jornada: está medido** (4 de 17 jugaron).
2. **Al filtrar solo cambian B y C:** sale Aubameyang. B baja de 52,36 a 48,95 y C de 63,31 a
   62,52. **Aubameyang queda como vigilado:** si vuelve, es el que más sube el once (+3,80 por
   jornada) y el tercero de la cola por euro.
3. **El calendario en el once de la jornada cambia nombres, pero no ha dado puntos:** cambia 19
   de 40 onces, y en los 13 con dato los cambios suman **−6 puntos**. **Se cierra como criterio
   de decisión.**
4. **Encender el catálogo no cambia A, B, C ni el plan** (usan la tasa), **sí el once de la
   jornada**. La etiqueta de titular cambia en **122 de 504 (24 %)**, y en 2 de nuestros 21.
5. **Lo cobrado por una venta NO llega a la caja de fichar con el saldo en rojo.** Anoche
   entraron 3.670.800 por ventas y la caja bajó 2.218.802. **Con eso, el plan real es una sola
   compra: Balliu, +0,12.**
6. **Para que corra solo le falta un libro de partidos.** La foto cruda no se dejó de guardar:
   producción la guarda en la caché de Actions, se poda a 24 y nunca baja al disco.

---

## 1. EL LESIONADO QUE SE COLÓ EN LA B

### El criterio, con lo medido

Para cada jugador, su estado en una foto tomada **antes** de su siguiente partido, y si jugó ese
partido. Dos momentos limpios: antes de la J1 (foto del 14/08) y antes de la J5 (foto del 10/09).
Solo jugadores con los partidos comprobados.

| Estado | n | Jugaron su siguiente partido |
|---|---|---|
| `ok` | 850 | **69 %** |
| `doubt` | 17 | **24 %** |
| `injured` | 78 | 3 % |
| `sanctioned` | 6 | 0 % |
| `discarded` | 1 | 0 % |

- **`injured`, `sanctioned`, `discarded`: fuera.** Juegan entre el 0 y el 3 %.
- **`unknown`: fuera.** No tiene medición (n = 0), y lo que no se sabe no se alinea. Son dos
  libres; no cambia nada.
- **`warned` (apercibido): dentro.** Es un aviso de sanción, no una sanción.
- **`doubt`, que era el discutible:**
  - **en el once de la TEMPORADA, dentro.** La duda es de un partido, y ese once decide a quién
    tienes para las 31 que quedan. Sacar a un jugador del objetivo por una molestia sería
    planificar con el parte médico de esta semana.
  - **en el de la JORNADA, al 24 %.** Ahí la duda está mucho más cerca de la lesión que de estar
    bien. Si FutbolFantasy trae probabilidad para ese partido, manda la suya.

### Lo que cambia cada once al filtrar

| Once | Antes | Después | Qué cambia |
|---|---|---|---|
| A | 47,61 | 47,61 | nada |
| **B** | 52,36 (3-4-3) | **48,95 (3-5-2)** | **sale Aubameyang, entra Unai López.** Lo que no es nuestro: Hinojo y Bardeli, 3,75 M |
| **C** | 63,31 | **62,52** | **sale Aubameyang, entra Roberto Fernández.** Ahora 9 de 11 son libres |
| LIGA | 70,69 | 70,69 | nada |

**Solo cambian B y C**, y solo por Aubameyang. De los otros cuatro del Computer que no están
disponibles (Rodrygo, De Jong, Redondo y Etta Eyong, este en duda), **ninguno entraría en ningún
once aunque estuviera sano.**

### Los vigilados

La cola del Computer si todos estuvieran disponibles (compra suelta, sobre el once A):

```
1. Hinojo        +0,731/jornada   0,433 por millón   1.690.000
2. Bardeli       +0,618/jornada   0,300 por millón   2.060.000
3. Aubameyang    +3,804/jornada   0,295 por millón  12.880.000   injured   VIGILADO
4. Balliu        +0,122/jornada   0,163 por millón     750.000
```

**Si Aubameyang vuelve, es el que más sube el once con diferencia (+3,80, cinco veces el
siguiente)** y el tercero por euro. Hoy no cabe en ninguna caja: cuesta 12,88 M.

**Guardia `test_el_once_no_alinea_lesionados_v1`:** 16 comprobaciones. El caso tiene un lesionado
que, por puntos, sería el primero del once; sin el filtro entraría. Quitando el filtro, 8 rojas.

---

## 2. EL CALENDARIO, PROBADO EN EL ONCE DE LA JORNADA

**Los porteros ya no entran en ningún cálculo:** n = 56, el signo al revés que el resto y dentro
del ruido. El script lo imprime. **El once objetivo todavía no sale en el panel** (ver el punto
4), así que no hay panel donde decirlo; cuando salga, esa línea va con él.

### La jornada 8, con la plantilla de hoy

| Tablero de FutbolFantasy | ¿Cambia algún nombre? |
|---|---|
| el del 22/09 (143 jugadores) | **no** |
| el de hoy con el catálogo (504) | **sí: sale Jonny, entra Maffeo** |

El resultado depende del tablero que se use. Es n = 1 y el partido no se ha jugado: no se sabe
si habría acertado.

### Las jornadas ya jugadas

**Método:** las 8 plantillas de hoy, las de todos los mánagers, sobre las jornadas 1 a 5
(todas jugadas antes de la última foto). Es **hipotético**: son plantillas de hoy, no las de
entonces, porque las rondas de Biwenger no casan con las jornadas del calendario (hay una "J1
aplazada" y una "J6 aplazada" aparte). Para cada once de jornada, se calcula con y sin el efecto
medido y se cobran **los puntos reales de ese partido** a los que entran y salen.

```
onces de jornada evaluados            40
cambian con el calendario             19   (48 %)
con dato de puntos de los que cambian 13
puntos de más que habrían dado        -6   (-0,46 por once que cambia)
```

Los 13, uno a uno, están en la salida del script. El nuestro: J1, entraba Pablo Durán por Unai
López, −1.

### El veredicto

**El calendario cambia nombres en el once de la jornada, uno de cada dos, porque entre titulares
parecidos cualquier empujón decide. Pero esos cambios no han dado puntos: −6 en 13.** Además,
el efecto se midió sobre esos mismos partidos, así que esto es lo más a favor que podía salir.
Aun así sale negativo.

**Se cierra como criterio de decisión**, en el de la temporada y en el de la jornada. Con 13
onces no se descarta un efecto pequeño y positivo. Se reabre si con más jornadas el mismo
cálculo sale en positivo, y no antes.

---

## 3. ENCENDER EL CATÁLOGO

### Medido hoy

Bajé las 22 páginas de FutbolFantasy **una vez**, grabándolas en el scratchpad, y pasé el
proveedor con el interruptor encendido y apagado sobre esas mismas páginas. `data/` no se tocó.

```
                          apagado        encendido
objetivos                   145            547
con probabilidad            142            504   (de 526 jugadores de campo)
peticiones                   22             22
```

### Qué cambia al encenderlo

| | ¿Cambia? |
|---|---|
| once A, B, C, LIGA de la temporada | **no**: usan la tasa de juego, no FutbolFantasy |
| el plan | **no**: va sobre el once de la temporada |
| **el once de la JORNADA 8** | **sí.** Sale Maffeo y entra Cabrera, que FutbolFantasy da de titular aunque su tasa sea 0,57. La suma baja de 42,77 a 40,78 |

**Lo que cambia en producción no está medido aquí:** los 362 que ganan pronóstico dejan de
valorarse "a ciegas" en la valoración de compras. El informe del 20/09 midió que salen 15
mejoras del once. No lo he vuelto a medir.

### La trampa: a cuántos les cambia la etiqueta de titular

```
titular (>= 50 %) según la tasa barata contra FutbolFantasy de hoy
    no coinciden     122 de 504   (24 %)
    de los nuestros    2 de 21
Pearson 0,73 · Spearman 0,73 · error medio 0,24   (n = 504)
```

**No es media plantilla: es una de cada cuatro, y en lo nuestro dos.** Y cuando discrepan, la
buena es FutbolFantasy, que es del partido que viene. La barata es lo que pasó. Hay que mirarlo,
pero no para no encenderlo: justo **para eso** se enciende.

### El comentario para el YAML (no lo he tocado)

```yaml
      # Apagado. LA TITULARIDAD PARA EL CATALOGO ENTERO, NO SOLO PARA LOS
      # OBJETIVOS.
      #
      #   LO QUE HACE. Las paginas de equipo de FutbolFantasy ya se piden
      #   las 20 en cada vuelta y traen la plantilla entera con su
      #   probabilidad de titular. Hoy solo se emparejan los objetivos
      #   (plantilla, mercado y rivales: 145). Con esto, el catalogo entero.
      #   NO PIDE NI UNA PAGINA MAS: solo empareja mas.
      #
      #   MEDIDO:
      #     26/09   22 peticiones en los dos casos; con probabilidad
      #             142 -> 504 de 526 jugadores de campo.
      #     20/09   +0,63 s por vuelta (emparejar), 497 de 547; con el
      #             catalogo salen 15 mejoras del once en vez de 0
      #             (INFORME-DE-64-A-513).
      #   Lo que cambia: el once de la JORNADA (26/09: sale Maffeo, entra
      #   Cabrera). La etiqueta de titular (>= 50 %) de FutbolFantasy y la
      #   de la tasa jugada no coinciden en 122 de 504 (24 %); en lo
      #   nuestro, en 2 de 21.
      #
      #   PASO 0 HECHO: 26/09, verja con los 5 de produccion MAS este, y el
      #   paso 0 con los 31 del inventario.
      #
      #   LO QUE NO ESTA MEDIDO Y HAY QUE VIGILAR:
      #     - Cuantas pujas cambian: los 362 que ganan pronostico dejan de
      #       valorarse "a ciegas". El 20/09 salian 15 mejoras del once; hoy
      #       no se ha rehecho.
      #     - El emparejamiento por nombre en 355 jugadores mas: hay que
      #       mirar `low_confidence` en el tablero la primera vuelta.
      #     - Si cae una pagina se pierden ~25 jugadores (20/09: 497 -> 471).
      BORDALAS_OBJETIVOS_EL_CATALOGO: "1"
```

### El paso 0 con los seis

Corrido el 26/09, con el árbol terminado y sin que cambiara durante las corridas:

```
verja con los 5 de produccion                          186/186 en verde   verja-cuatro-cortas.txt
verja con los 6 (los 5 + BORDALAS_OBJETIVOS_EL_CATALOGO) 186/186 en verde   verja-cuatro-cortas-seis.txt
paso 0, los 30 del inventario a la vez                 PASADO, 148 s      paso0-cuatro-cortas.txt
```

**Cómo se corrió la de los seis:** la verja lee la lista del YAML y quita lo que sobra, así que
no admite un sexto puesto a mano. Un envoltorio de una página (en el scratchpad, sin commitear)
le da a la verja de verdad esa lista con uno más. Todo lo demás es la verja tal cual.
`config/paso_0.json` va en este commit con `BORDALAS_OBJETIVOS_EL_CATALOGO` entre los probados.
En esta rama son 30 y no 31, porque `BORDALAS_LA_RESERVA_MIRA_EL_ONCE` vive en la otra.

---

## 4. QUE ESTO PUEDA CORRER SOLO

### Por qué la última foto cruda es del 19/09: se guarda en otro sitio y se borra

**No se dejó de guardar, y no lo sabíamos porque no lo habíamos preguntado.**

- Producción hace una foto en cada vuelta (`src/collectors/league_collector.py:209`).
- La guarda en la **caché de Actions** (`bordalas-live.yml`, paso `Restore Bordalas state`,
  `data/snapshot_*.json`).
- **La poda a las 24 últimas**, un día (`scripts/prune_github_state.py:7`,
  `SNAPSHOT_KEEP = 24`).
- **No va a git por decisión**: está en la lista de lo que no se guarda
  (`src/estado/los_libros.py:453`).
- **Y no va en el artefacto de diagnóstico** (el `upload-artifact` del YAML no la lista).

**Al disco del dueño solo llegan las fotos de sus corridas locales. La última fue el 19/09.**

### Qué le falta al cálculo para leer del ciclo

| Pieza | Hoy | En el ciclo |
|---|---|---|
| el panel (`todaLaLiga`, ofertas, saldo, caja) | `--panel` apuntando a un zip de descargas | **ya existe en el runner**: `dashboard/data/status.json`, recién hecho por `build_dashboard`. Solo cambia la ruta |
| las plantillas de los rivales | `--rivales`, del zip | en el runner: `data/rival_intelligence/rival_intelligence.json` |
| la titularidad | el tablero de FutbolFantasy | en el runner |
| **los partidos uno a uno** | **la foto tranquila del 10/09, que solo está en este portátil** | **NO EXISTE EN EL CICLO.** Con 24 fotos de un día no hay foto tranquila que cubra la temporada |

**Lo que falta de verdad es un libro de partidos:** `data/intelligence/partidos_por_jugador.jsonl`,
una línea por jugador y partido, sacada de `fitness` en cada vuelta, sin repetir, y guardada con
los demás libros (`los_libros.py`, lista `LIBROS`). Son unas ~550 líneas por jornada.

**Y el enganche al panel**, junto a `elVestuarioLibre` en `src/telemetry/dashboard_state.py:4259`,
donde ya están el catálogo, la caja y las plantillas.

### Lo que costaría (no lo he hecho)

- **El libro de partidos:** es lo delicado. El cruce de `fitness` con el calendario se descuadra en
  fotos de mitad de jornada (medido: 208 de 2.450). Hay que llevarlo desde el script a `src/`
  con su comprobación contra totales, más su guardia y su entrada en los libros. **Un encargo.**
- **El bloque del panel:** leer lo que ya hay y llamar a las funciones puras. **Medio encargo**,
  y solo tiene sentido después del libro.
- **Hasta que exista el libro,** los onces se pueden sacar en el ciclo **sin** el bloque 1: k por
  posición y calendario congelados con lo medido hoy. Pero eso es un número que se recibe, no uno
  que se mide (doctrina 90), y habría que decirlo en el panel.

---

## Sobre el plan de fichajes: no se ejecuta, y el supuesto era falso

**Lo que llega a la caja por una venta, con el saldo en rojo: nada, si la oferta ya estaba en la
garantía.** La caja de fichar, en rojo, es solo el margen de deuda
(`acquisition_budget.py:216-264`, la parte de caja es `max(saldo, 0) = 0`):

```
margen = garantía de solvencia − 500.000 − deuda        (solvency_engine.py, calculate_max_safe_debt)
```

La garantía es la cartera A/B de ofertas. Si se vende a alguien cuya oferta está en esa cartera,
**la deuda baja X y la garantía baja X: el margen no se mueve.** Solo sube si la oferta vendida
no estaba en la cartera.

**Medido (n = 1 noche):**

```
25/09 21:13   margen de deuda   3.575.478
26/09 08:11   margen de deuda   1.356.676      -2.218.802
entre medias  +3.670.800 por dos ventas, -3.447.904 por Blanco, +250.000 de bonus
```

Entraron 3,67 M y la caja bajó 2,2 M. Hay una compra y una tanda de ofertas nueva por medio, así
que esto no aísla la venta. Pero la fórmula dice lo mismo sin necesidad de aislarla.

**Con eso, el plan real con 1.356.676 €:**

```
compra Balliu (750.000)     +0,122 por jornada     1 escritura
```

**Vender a Jonny para comprar a Hinojo no cabe**, porque vender no mete dinero en la caja. **Y
no se haría aunque cupiera**, por las razones del dueño: Jonny ha jugado 6 de 7, y se le vendería
fiándose de una titularidad del 60 % que falla en uno de cada tres. Es el error de Rubén García.

**Queda como lo que es: la mejor jugada posible con 1.356.676 € captura el 0,8 % de la distancia
a C (0,12 de 15,70).** Ese es el argumento: **sin decidir qué se vende, y sin salir del rojo, no
hay plan.** La decisión es tuya: Ceballos o la chatarra.

---

## Lo que cambió en el código

| Fichero | Qué |
|---|---|
| `src/analysis/el_once_objetivo.py` | `FUERA` y `JUEGA_SI_DUDA` con su medición; `el_mejor_once` no alinea a nadie de `FUERA`; `el_plan` no compra lesionados y recibe `llega_a_la_caja` |
| `scripts/el_once_objetivo.py` | la jornada con el 24 %; los porteros fuera del calendario; los onces con y sin filtro; los vigilados y la cola; el calendario en onces de jornada (`--rivales`); la etiqueta de titular; el plan con lo que llega de verdad; `--ff` para comparar tableros |
| `src/analysis/test_el_once_no_alinea_lesionados_v1.py` | **guardia nueva**, 16 comprobaciones |
| `scripts/run_validation_gate.py` | la guardia, en la verja |

## Lo que no hice, y por qué

- **Ni una petición a Biwenger.** Las 22 páginas de FutbolFantasy se bajaron una vez, como en cada
  vuelta del ciclo, al scratchpad.
- **No encendí el catálogo ni toqué el YAML.** El bloque está arriba.
- **No construí el libro de partidos ni el bloque del panel.** Es un encargo y medio; lo decides tú.
- **No ejecuté ni propuse ninguna venta.** El plan real es una compra de 750.000, y tampoco la hago.
- **No toqué** el once de producción, la reserva de solvencia, la regla del déficit, el Position
  Manager ni ninguna constante.
- **No empujé.**
