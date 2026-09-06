# EL ONCE — resultado

Rama `once/puntos-en-el-banquillo`, con el arreglo de la verja ya dentro.
**86 de 86 en verde**, y en las tres condiciones que importan:

```
disco local (almacén de 6 días)      86/86
CI con caché fría (data/ vacío)      86/86
CI con caché caliente (25 días)      86/86
```

`main` no se toca. `bordalas-live.yml` y `MAX_SINGLE_SPECULATION_PERCENT`,
sin tocar. **Ningún umbral movido.** `npm run build` pasa. **Sin push.**

Medido contra `diagnostico/status.json` del 06/09/2026 12:54.

---

## Lo que entra en el commit

Miré `git status` antes. **Dieciocho ficheros**, de dos trabajos:

**EL ONCE (bloques 1 a 5)**

```
 M src/analysis/marcador.py                            arregla el cuadre
 M src/telemetry/dashboard_state.py                    publica el bloque
 M dashboard-v8/src/lib/status.js                      normalizador
 M dashboard-v8/src/pages/HomePage.jsx                 monta el panel
 M src/analysis/test_pantalla_lee_lo_publicado_v1.py   + cadenas
 M scripts/run_validation_gate.py                      guardias nuevas
?? src/analysis/banquillo.py                           bloque 1
?? src/analysis/sesgo_posicion.py                      bloque 2
?? src/analysis/rival_once.py                          bloque 3
?? src/analysis/test_once_v1.py                        23 pruebas
?? dashboard-v8/src/components/ElOncePanel.jsx
?? docs/ENCARGO-EL-ONCE-2026-09-17.md
```

**EL INTERRUPTOR DE TENER (lo que se mudó de la verja)**

```
 M src/analysis/hold_value.py                          apaga la vía
 M src/analysis/test_no_contar_dos_veces_v1.py         deja de leer el almacén
?? src/analysis/hold_switch.py                         el interruptor
?? src/analysis/test_interruptor_tener_v1.py           14 pruebas
?? dashboard-v8/src/components/ViaTenerPanel.jsx
 M dashboard-v8/src/pages/MarketPage.jsx               monta el panel
```

---

# BLOQUE 1 — Los puntos que se quedaron sentados

## Primero: por qué no había ningún número que leer

El marcador llevaba **un mes sin dar nota**. Decía *"5 jornadas cerradas,
pero ninguna cuadra con Biwenger"*, y con eso el proyecto se quedó sin la
única medida que dice si el motor de alineación funciona.

No era el motor. Eran **dos fallos de aritmética**, los dos míos de leer
mal el dato:

**1. La clasificación de Biwenger es ACUMULADA.** `points` no son los
puntos de la jornada: son los de la temporada hasta ahí. El cuadre
comparaba `puntos_once` —una jornada— contra ese acumulado.

En la jornada 1 coincide, porque no hay nada antes. **Por eso el fallo
sobrevivió un mes.** De la 2 en adelante estaba comparando 17 contra 60.

La misma raíz hacía que la diferencia contra la liga saliera **+13,5 tres
jornadas seguidas**: era la brecha de *temporada* repetida, no la de la
jornada.

**2. Un jugador vendido se lleva sus puntos.** El almacén solo guarda a
los que seguían en plantilla al mirar. Quien alineó el sábado y se vendió
el lunes aporta cero.

En las jornadas 1 y 2 eso pasaba con **cuatro y con tres de los once**. El
once salía a 13 y a 17 puntos cuando Biwenger pagó 29 y 31 — y la pantalla
publicaba **"61,9 % del óptimo"** como si eso midiera el motor. No medía el
motor: medía el agujero.

Los dos arreglados. El primero del todo; el segundo no se puede recuperar
hacia atrás, pero ahora **se dice**, con los nombres de quién falta, y esa
jornada queda fuera de la media en vez de ensuciarla.

## Y ahora el número

De seis jornadas observadas, **hay exactamente una reconstruible**:

| Jornada | Alineó | Podía | Sentados | % | Estado |
|---|---:|---:|---:|---:|---|
| J4899 | 13 (4-4-2) | 21 | 8 | 61,9 % | 4 de los once ya estaban vendidos |
| J4900 | 17 (5-3-2) | 24 | 7 | 70,8 % | 3 de los once ya estaban vendidos |
| **J4901** | **70 (3-4-3)** | **78 (3-4-3)** | **8** | **89,7 %** | **entera · 4,1 % de descuadre** |
| J4902 | 8 (4-3-3) | 8 | 0 | 100 % | Biwenger pagó 0 esa jornada |
| J4904 | — | — | — | — | no se anotó qué once jugó |
| J4937 | — | — | — | — | jornada en curso |

**J4901: ocho puntos en el banquillo.** El once reconstruido suma 70 y
Biwenger pagó 73 — se queda a tres puntos, un 4,1 %, y ese descuadre tiene
nombre: un fichado a mitad de semana cuenta como 0 por diseño, porque no se
sabe cuánto de su total es de esa jornada.

**No cuadra exactamente, así que no puntúa.** El cuadre no se afloja: una
media que mezcla reconstrucciones buenas con cojas no mide nada. Pero
tampoco se tira a la basura una jornada que se queda a tres puntos igual
que una que se queda a dieciséis. Sale publicada aparte, etiquetada
**«casi»**, y nunca entra en la media.

## La cuenta que pedías

```
        sentados en la única jornada reconstruible      8,00 / jornada
        lo que hace falta para alcanzar al líder        0,371 / jornada
                                                        ─────────────
                                                        21,6 veces
```

**Ocho puntos en una jornada. La distancia entera de la temporada son
trece.**

Con una sola jornada eso es un aviso, no una conclusión, y el veredicto lo
dice con esas palabras. Pero apunta en una dirección muy clara, y el
resto del informe apunta a la misma.

## Lo único accionable: dos nombres

En **las tres jornadas**, los mismos dos jugadores aparecen en "debieron
jugar":

| | Debieron jugar | Jugaron en su lugar |
|---|---|---|
| J4901 | **Yusi Enríquez** (DF, 4) · **Lucas Cepeda** (DL, 3) | Djené (DF, **−1**) · Pablo Durán (DL, 0) |
| J4900 | **Yusi Enríquez** (DF, 4) · **Lucas Cepeda** (DL, 3) · Pablo Ibáñez (MC, 0) | tres ya vendidos |
| J4899 | **Yusi Enríquez** (DF, 4) · **Lucas Cepeda** (DL, 2) · Djené · Zubeldia | cuatro ya vendidos |

Tres jornadas seguidas sentando a los mismos dos. **Eso no es mala suerte,
es un sesgo del motor** — y el bloque 2 dice de qué sesgo se trata.

Y fíjate en el detalle: en J4901 **Pablo Durán jugó y sacó 0**, mientras
Lucas Cepeda sacaba 3 desde el banquillo. Tu sospecha era sobre Pablo
Durán, y va en la dirección contraria a la que pensabas: ese día el error
no fue sentarlo, fue ponerlo. Lo que se repite no es "delantero sentado",
es **"el motor elige mal dentro de cada línea"**.

---

# BLOQUE 2 — Sí hay sesgo, y es más ancho de lo que sospechabas

## Antes, una precisión que cambia la pregunta

`expected_points` no existe como predicción de puntos. Lo que ordena el
once es `weekly_expected_value`, y su propio código lo dice: *"no es una
predicción de puntos: es una vara común para ordenar el once"*, de 0 a 1,
jerarquía × probabilidad de ser titular.

Así que **"error medio en puntos" no se puede calcular**: no hay puntos que
restar. Publicar uno sería inventarme la unidad.

La pregunta que sí se puede contestar, y es la de verdad:

> con la **misma marca de la vara**, ¿cuántos puntos entrega un delantero y
> cuántos un defensa?

Si la vara fuese neutra, el cociente sería igual en las cuatro posiciones.

## No lo es

Sobre 81 jugadores de las siete plantillas de la liga, 3 jornadas:

| Posición | N | Vara media | Pts/jornada | **Pts por unidad de vara** | Factor que haría falta |
|---|---:|---:|---:|---:|---:|
| Medio | 29 | 0,640 | 5,51 | **8,61** | ×1,147 |
| Delantero | 18 | 0,646 | 5,52 | **8,55** | ×1,139 |
| Portero | 7 | 0,826 | 5,71 | 6,92 | *(muestra corta)* |
| **Defensa** | 27 | 0,677 | 4,00 | **5,90** | ×0,787 |

**Con la misma marca de la vara, un medio entrega 1,46 veces los puntos que
un defensa.** Un delantero, 1,45.

## Y tu caso exacto, medido

Tú lo planteaste así: *"Pablo Durán con un 70 % de titularidad en el
banquillo mientras defensas con ese mismo 70 % jugaban."* Ahí es justo donde
la vara los empata y el motor tiene que desempatar:

| Con 65-80 % de titularidad | N | Vara media | Pts/jornada |
|---|---:|---:|---:|
| Medio | 13 | 0,647 | **6,64** |
| Delantero | 8 | 0,715 | **5,21** |
| Defensa | 17 | 0,698 | **3,90** |

**Misma vara (0,70 contra 0,72), y el delantero entrega un 33,5 % más que el
defensa.** El medio, un 70 % más.

Tenías razón, y te quedaste corto: **el sesgo no es contra los delanteros,
es contra toda la mitad de arriba.** Por eso el once sale 5-4-1 y por eso
Yusi Enríquez y Lucas Cepeda llevan tres jornadas sentados.

## La corrección, propuesta y NO aplicada

```
        Medio       × 1,147
        Delantero   × 1,139
        Defensa     × 0,787
        Portero     × 0,922      (n=7: no llega a la muestra mínima)
```

**No he tocado el motor.** `lineup_engine.py` no importa este módulo y hay
una guardia que lo comprueba. La decisión es tuya, y con tres jornadas y 81
jugadores yo no la tomaría todavía: la muestra es transversal —los puntos
son del acumulado y las plantillas son las de hoy—, así que hay ruido, pero
el ruido no tiene por qué favorecer a una posición.

---

# BLOQUE 3 — Mex: quieto, con nuestro presupuesto, y ocho puntos por delante

|  | Mex | Nosotros |
|---|---|---|
| Puesto | **2.º**, 141 pts | 4.º, 133 pts |
| Fichas | **14** | **14** |
| Plantilla | 52,25 M | 49,54 M |
| Dibujo | **3-5-2** | 4-3-3 |
| De medio arriba | **7** | 6 |
| Puntos de su once | **163** | **123** |
| Puntos del banquillo | 27 | 24 |
| **Titulares fijos (≥80 %)** | **1 de 11** | **7 de 11** |
| Movimientos en el tablón | **0** | 2 compras, 2 ventas |
| Pujas perdidas | **3** | 9 |

Tres cosas, y la tercera es la incómoda.

**Está quieto.** Cero compras y cero ventas en la ventana del tablón, tres
pujas perdidas — contra las **52 de Pollo**. Va segundo sin tocar el
mercado. *(Honestidad: el tablón solo guarda del 04/09 al 06/09, 2,2 días.
"Quieto" significa quieto ahí, no toda la temporada.)*

**Está cargado donde se paga.** Su once lleva 5 medios y 2 delanteros; el
nuestro, 4 defensas. Y el bloque 2 dice que el medio campo entrega 1,46
veces lo que la defensa por unidad de vara. **Dos mediciones
independientes, la misma conclusión.** Nuestro once recomendado de hoy es
5-4-1: cinco defensas.

**Y gana con jugadores que nuestra vara considera dudosos.** Uno de sus
once llega al 80 % de titularidad. Del nuestro, siete. Nosotros optimizamos
la seguridad de que jueguen; él optimiza los puntos que hacen cuando
juegan. Bellingham al 70 % lleva 44 puntos.

*(No he usado `activity` ni `profile` de la ficha de rivales: los siete
managers salen con el mismo valor en las dos —VERY_HIGH y AGGRESSIVE—, así
que no distinguen a nadie. Usarlas para decir que Mex es agresivo sería
fabricar una diferencia que el dato no tiene. Hay una guardia que impide
volver a usarlas.)*

---

# BLOQUE 4 — La pantalla ya no cuenta la película vieja

**1. La brecha ya decía 18,3 M.** Se recalcula sola en cada ciclo:
`value_gap_to_leader = 18.300.000`, y el titular ya dice *"Tu plantilla vale
18,3 M menos que la del líder"*. Los 35,5 M del encargo venían de una foto
vieja. **No había nada que corregir**, y prefiero decírtelo a apuntarme un
arreglo que no hice.

**2. La advertencia, pegada a la cifra.** El panel EL ONCE cierra con la
correlación y su valor crítico: *"el valor de plantilla no predice los
puntos en esta liga"*, r = +0,553 contra el 0,754 que haría falta con siete
equipos.

**3. Los puntos sentados, arriba.** `ElOncePanel` va en HomePage **justo
encima de LA CARRERA**, a propósito: primero lo que gana puntos, y después
el termómetro sobre el que se montó una estrategia equivocada durante
cuatro noches.

---

# EL INTERRUPTOR DE TENER — lo que se mudó de la verja

Las dos aserciones que quité anoche no se han perdido. Están donde tenían
que estar desde el principio.

**En la verja** se comprobaban una vez, contra el almacén de quien lanzara
CI, y ponían el despliegue en rojo cuando cambiaba el mercado — que es
justo cuando menos hay que parar el despliegue. **Ahora** se comprueban en
cada ciclo, contra el almacén de producción, y lo que hacen es apagar la
vía que se ha quedado sin nada debajo.

## Cómo está la vía ahora mismo

| Tramo | N | Rinde a 3 días | En pérdida | Sobre el listón | Estado |
|---|---:|---:|---:|---:|---|
| > 4 % | 35 | **+21,15 %** | 2,9 % | +18,15 | respalda |
| **2-4 %** | 41 | **+3,14 %** | 17,1 % | **+0,14** | **respalda, al límite** |
| 1-2 % | 58 | +1,80 % | 10,3 % | −1,20 | **apagado** |
| 0,5-1 % | 55 | +0,60 % | 30,9 % | −2,40 | apagado |
| 0,25-0,5 % | 32 | +0,41 % | 21,9 % | −2,59 | apagado |
| 0-0,25 % | — | — | — | — | sin muestra |
| CAE | 114 | −3,96 % | 93,0 % | — | no se compra ahí |

**El aviso que querías ver:** el tramo que sostiene la vía va a **catorce
centésimas** del listón. Si el 2-4 % baja de 3,00 %, se apaga solo y la vía
se queda colgando únicamente del `> 4 %`.

## Lo que apaga hoy, y lo que no cambia

```
Gorosabel   4,849 %/día   HOLD           8,49 %    (tramo > 4 %)
Roro        1,666 %/día   SIN_RESPALDO   0         (tramo 1-2 %, 1,80 %)
Amatucci    1,098 %/día   SIN_RESPALDO   0         (tramo 1-2 %, 1,80 %)
Pedri       0,305 %/día   SIN_RESPALDO   0         (tramo 0,25-0,5 %, 0,41 %)
```

**Ninguna decisión de hoy cambia.** Esos tres ya rendían 1,05 %, 1,05 % y
0,24 % —por debajo del listón del 3 %— y ya se estaban rechazando aguas
abajo. Lo que cambia es que **ahora se rechazan antes y con el motivo
escrito**, en vez de llegar hasta el final con un valor pequeño que nadie
sabía de dónde salía.

## Dos decisiones de diseño que conviene que sepas

**Sin muestra no apaga.** Un tramo que no se ha medido sale como «sin
muestra», que es una cosa distinta de «medido y malo». Apagar una vía por no
haberla mirado sería el mismo error que valorarla sin mirarla, del otro
lado.

**El listón se importa, no se copia.** `MIN_TENER_YIELD` es
`MIN_SPECULATION_YIELD`, el 3 % de siempre — la regla del 13/09: el
bolsillo, el listón y el valor salen todos de la misma vía. Dos treses en
dos ficheros se separan el día que alguien mueve uno, y hay una guardia que
lo impide.

---

# Un tercer defecto de la misma familia, encontrado de paso

Al enchufar el interruptor, `test_no_contar_dos_veces_v1` se cayó con un
**KeyError**, no con un rojo legible: `hold_value` devolvía menos claves por
el camino de "sin valor" que por el normal.

Es **exactamente el mismo defecto** que `store_depth` esta mañana: *la forma
del objeto cambiaba con el contenido*. Arreglado igual — los campos siguen
ahí, en cero, con el motivo escrito. «Ausencia de dato ≠ dato» vale para el
valor, nunca para la clave.

Y las tres pruebas de esa guardia que se apoyaban en el almacén real (medían
la fórmula, pero leyéndolo por debajo) ahora reciben su calibración a mano.
Es el mismo fallo que tiró producción, un piso más abajo.

---

# Lo que no hice, y por qué

**No moví ningún umbral del once ni del mercado.** El factor por posición
está calculado y publicado; el motor sigue ordenando exactamente igual que
ayer.

**No puntué las cinco jornadas.** Cuatro no se pueden reconstruir y digo de
cada una por qué. Media medición honesta vale; una entera inventada, no.

**No recuperé los puntos de los jugadores vendidos.** No se puede hacia
atrás. De aquí en adelante sí, porque la jornada queda marcada como
incompleta en el momento de observarla.

**No comparé el once de Mex jornada a jornada.** El tablón solo guarda la
alineación vigente. La comparación es de hoy y lo dice.

**No toqué el libro de rechazos**, como pediste. En tres días tendrá muestra.

**No saqué de `data/` los HTML del ojeador.** `test_futbolfantasy_source_v12`
sigue leyendo estado mutable; está declarado en `DEUDA` con su motivo y la
Regla B lo ejecuta sin estado y exige que pase. Es trabajo aparte.

---

**La frase para mañana:** en la única jornada que se puede reconstruir
dejamos **ocho puntos en el banquillo**, y la temporada entera se decide por
trece. El motor sienta a los mismos dos jugadores tres jornadas seguidas, y
ahora se sabe por qué: **con la misma vara, un medio entrega 1,46 veces lo
que un defensa, y el motor los trata como iguales** — por eso alinea 5-4-1.
Mex va segundo con nuestras mismas catorce fichas, sin tocar el mercado,
cargado de medios y con **un solo titular fijo contra nuestros siete**. La
liga no estaba en el mercado. Estaba en el banquillo.
