# LA VARA — resultado

Rama `vara/medir-los-puntos`, desde `main` (`6678ca4`). **88 de 88 en verde**,
y en las tres condiciones:

```
disco local                          88/88
CI con caché fría (data/ vacío)      88/88
CI con caché caliente (25 días)      88/88
```

`main` no se toca. `bordalas-live.yml` y `MAX_SINGLE_SPECULATION_PERCENT`,
sin tocar. Ninguna guardia nueva lee `data/`. `npm run build` pasa.
**Sin push.**

Medido contra `diagnostico/status.json`.

---

## Lo que entra en el commit

Miré `git status` antes. **Diecinueve ficheros:**

```
LOS FACTORES (bloque 1)
?? src/analysis/position_factor.py            los factores, muestra e interruptor
 M src/analysis/lineup_engine.py              la vara acepta posición
?? src/analysis/vara_comparada.py             los dos onces, uno al lado del otro
?? src/analysis/test_vara_v1.py               12 pruebas
?? dashboard-v8/src/components/VaraPanel.jsx
 M dashboard-v8/src/pages/SquadPage.jsx
 M dashboard-v8/src/lib/status.js

LA RED (bloque 2) Y LOS 8 PUNTOS (bloque 3)
 M src/analysis/marcador.py                   anota el once de la vara vieja
 M src/analysis/banquillo.py                  los tres números y las dos cifras
 M src/telemetry/dashboard_state.py           publica y reordena

LA FORMA (bloque 4)
?? src/analysis/test_forma_estable_v1.py      4 pruebas, la regla de la casa
 M src/analysis/hold_value.py                 } las siete funciones
 M src/analysis/hold_switch.py                } que cambiaban de forma
 M src/analysis/rival_once.py                 }
 M src/analysis/rival_scoreboard.py           }
 M src/analysis/sesgo_posicion.py             }

 M scripts/run_validation_gate.py             + 2 guardias
 M src/analysis/test_pantalla_lee_lo_publicado_v1.py
?? docs/ENCARGO-LA-VARA-2026-09-18.md
```

---

# BLOQUE 1 — Los factores, puestos

## La muestra detrás de cada uno, antes que el número

| Línea | Factor aplicado | Medido | Fichas | Observaciones jugador-jornada |
|---|---:|---:|---:|---:|
| Medio | **×1,147** | ×1,147 | 29 | 87 |
| Delantero | **×1,139** | ×1,139 | **18** | 54 |
| Defensa | **×0,787** | ×0,787 | 27 | 81 |
| Portero | ×1,000 | ×0,932 | **7** | 21 |

Ventana: **3 jornadas**, 81 fichas de las 7 plantillas de la liga.

**Lo que pediste que no te ocultara:** el factor del delantero se apoya en
**18 fichas**. Y el número ilustrativo que abre tu encargo —los 5,21
puntos del delantero en la franja 65-80 %— se apoya en **8**. Ocho.

Eso viaja pegado al número: está en el módulo, en el informe y en la
columna FICHAS del panel. No hace falta releer esto dentro de un mes.

**El portero no lleva factor.** Midió ×0,932, pero con 7 fichas no llega a
la muestra mínima de 10 que exige el propio módulo que lo midió. Se mide y
no se aplica; se queda en 1,000 y lo dice.

**Los factores están congelados, no se recalculan.** Un factor que se
recalcula solo cambia el once sin que nadie lo decida, y además sería
circular: el motor se corregiría con una medida hecha sobre plantillas que
él ayuda a formar. Al recalcularlos hoy sobre una foto nueva salían **1,147
/ 1,137 / 0,785** — se mueven en la tercera cifra. Esa estabilidad es la
razón de poder congelarlos.

## Dónde se aplican, y dónde a propósito no

**En el motor sí:** `lineup_engine`, que es donde se elige el once.

**En las fichas de plantilla no.** El `weekly_expected_value` que se
publica en cada ficha sigue saliendo crudo. Si allí se corrigiera, la
próxima medición del sesgo estaría midiendo su propia corrección y saldría
siempre neutra — nunca sabríamos si el factor sobra o falta. Hay una
guardia que vigila que no se invierta por descuido.

## El once de hoy, con las dos varas

**5-4-1 → 3-4-3.**

| | Vara vieja (5-4-1) | | Vara nueva (3-4-3) | |
|---|---|---:|---|---:|
| PT | Dituro | 0,696 | Dituro | 0,696 |
| DF | Djené | 0,874 | Djené | 0,688 |
| DF | Jonny Castro | 0,696 | Jonny Castro | 0,548 |
| DF | Manu Sánchez | 0,696 | Manu Sánchez | 0,548 |
| DF | **Kiko Femenía** | 0,644 | — | |
| DF | **Zubeldia** | 0,644 | — | |
| MC | Expósito | 0,874 | Expósito | 1,003 |
| MC | Olasagasti | 0,874 | Olasagasti | 1,003 |
| MC | Pablo Ibáñez | 0,748 | Pablo Ibáñez | 0,858 |
| MC | Mangala | 0,748 | Mangala | 0,858 |
| DL | Yamal | 1,000 | Yamal | 1,139 |
| DL | — | | **Jutglà** | 0,556 |
| DL | — | | **Pablo Durán** | 0,537 |

**Entran:** Jutglà (11 puntos de temporada) y Pablo Durán (8).
**Salen:** Zubeldia (9) y **Kiko Femenía (0)**.

Kiko Femenía llevaba **cero puntos en tres jornadas** y era titular. Eso es
exactamente lo que el 5-4-1 estaba produciendo.

En puntos acumulados, el once nuevo suma **130** contra **120** del viejo:
diez puntos en tres jornadas. **Ojo con ese número: es en muestra.** Los
mismos puntos que alimentaron los factores. Sirve como comprobación de
coherencia, no como prueba de que funcione — para eso está el bloque 2.

## La línea para apagarlo

```
BORDALAS_VARA_PLANA=1
```

Con eso vuelve la vara del 17/09, idéntica, sin tocar código ni desplegar.
Hay una guardia que comprueba que apagarlos devuelve **el mismo once** que
antes, no uno parecido.

El contrafactual —"qué once habría elegido la vara vieja"— se calcula con
un contexto interno, no escribiendo en el entorno del proceso: si algo
fallara a mitad, dejaría los factores apagados en producción sin que nadie
lo supiera.

---

# BLOQUE 2 — La red

Desde este ciclo, cada jornada se anota **también el once que habría
elegido la vara vieja**. Cuando la jornada cierra y llegan los puntos, el
tablero publica los tres números y el acumulado:

```
puntos del once que alineamos
puntos del once de la vara vieja
puntos del mejor once posible
```

Hoy dice, literalmente:

> *"Todavía no hay ninguna jornada jugada con los factores puestos: la
> comparación empieza en la próxima."*

Que es la verdad. **Las jornadas anteriores al cambio no tienen once
alternativo anotado y quedan fuera** en vez de entrar como ceros, que
dirían que la vara nueva no aportó nada cuando en realidad no existía.

Y si tras tres jornadas la vara nueva va por detrás, el veredicto sale en
mayúsculas con la línea para apagarla dentro:

> *"LA VARA NUEVA VA N PUNTOS POR DETRÁS DE LA VIEJA en 3 jornadas. Si esto
> se mantiene, se apaga con BORDALAS_VARA_PLANA=1."*

*(Detalle de implementación: la anotación va en dos pasos. La jornada se
anota nada más cargar el snapshot —ahí están los puntos, que es el dato que
no se recupera— y el once alternativo se completa después, cuando la
plantilla ya viene con jerarquía y titularidad. Reordenar el ciclo por esto
habría puesto en riesgo lo único irrecuperable.)*

---

# BLOQUE 3 — Los 8 puntos, recalculados

Los 8 puntos de la J4901 salían de dos cambios:

| Cambio | Ganaba | ¿Sigue siendo nuestro? |
|---|---:|---|
| Yusi Enríquez (4) por Djené (−1) | **+5** | **No.** Está en Prinzipote (1.170.000 €) |
| Lucas Cepeda (3) por Pablo Durán (0) | **+3** | Sí |

```
        histórico, con la plantilla de entonces      8 puntos
        con la plantilla de hoy                      3 puntos
```

**No las sumes ni las mezcles.** La primera **juzga al motor**: eso se dejó
en el banquillo con lo que había. La segunda es **la que vale dinero**: eso
es lo que se podría ganar mañana.

Cinco de aquellos ocho los aportaba un jugador que ya no tenemos, y por eso
la cifra que sostiene la decisión de esta noche es **3, no 8**.

**Y es una sola jornada reconstruible.** Lo repito aquí porque me lo
pediste y porque es la limitación más importante del bloque: de seis
jornadas observadas, cuatro no se pueden reconstruir y la quinta está en
curso.

---

# BLOQUE 4 — La forma no cambia con los datos

Es un solo defecto con tres caras esta semana, y ahora es regla de la casa
con guardia propia: **cuando falta un dato, el hueco se dice con un valor
vacío y el motivo escrito; la clave no desaparece nunca.**

La guardia llama a cada función dos veces —con datos buenos y con nada— y
exige el mismo juego de claves. **Mordió a la primera: siete funciones**,
varias escritas por mí esta misma semana.

| Función | Qué le faltaba sin datos |
|---|---|
| `hold_value` | `rate_percent_per_day` |
| `hold_switch.route_state` | `backing`, `closest`, `max_loss_rate`, `switched_off`, `unmeasured` |
| `hold_switch.bucket_backing` | `margin`, `max_loss_rate` |
| `sesgo_posicion.sesgo_por_posicion` | 9 claves, entre ellas `tie_band` y `sample` |
| `rival_once.comparar_con` | 8 claves, entre ellas `rival`, `us` y `market` |
| `rival_scoreboard.value_versus_points` | `critical_r`, `r_value_points`, `significant`… |
| `vara_comparada.comparar` | `changed`, `in`, `out`, `formation_changed` |

Las siete arregladas. Y una segunda regla encima: **`available: False` sin
motivo escrito tampoco vale** — eso pilló a `manager_scoreboard`, que
devolvía un vacío mudo cuando un manager no aparecía en el tablón.

## Lo que queda por revisar, escrito para no perderlo

- **Las funciones que van a buscar su fichero solas**: `marcador.marcador()`,
  `rejection_ledger.summary()` y `rule_backtest()`. No se pueden llamar sin
  tocar `data/`, y esta guardia no toca `data/`. Habría que darles una ruta
  inyectable, como ya la tiene `store_depth(path)`.
- **Las formas anidadas.** La guardia compara claves de primer nivel. Dentro
  del marcador, una fila `medible: False` sigue trayendo tres claves y una
  `medible: True` veinte. Es el mismo defecto un piso más abajo.
- **Los constructores del dashboard** (`compact_*`, `build_*` de
  `dashboard_state`). No están en la tabla.

## Y un fallo silencioso que apareció de paso

Al mover el bloque de la vara descubrí que **el bloque de EL ONCE y el de
la vía TENER se calculaban antes de que existiera `roster`**. No reventaban
—cada uno tiene su `try`— pero se publicaban vacíos con un `NameError`
dentro. Es la peor forma de fallar: en silencio y con la clave puesta.
Movidos detrás de `roster`, con la razón escrita en el sitio.

---

# BLOQUE 5 — Las dos consecuencias

## 5.1 — La vara nueva **no abre ninguna puerta**

Probé los 20 objetivos del mercado uno a uno: añadí cada uno a la plantilla
y recalculé el mejor once con las dos varas.

| Objetivo | Pos | Precio | ¿Entraba antes? | ¿Entra ahora? | Decisión hoy |
|---|---|---:|---|---|---|
| Pedri | MC | 15.350.000 | sí | sí | SUPERA_PRESUPUESTO |
| Amatucci | MC | 3.670.000 | sí | sí | SUPERA_PRESUPUESTO |
| Pathé Ciss | MC | 2.930.000 | sí | sí | NO_COMPENSA |
| Gabriel Suazo | DF | 1.730.000 | sí | sí | NO_COMPENSA |

**Ninguno entra solo con los factores.** Los cuatro que mejorarían el once
ya lo mejoraban antes, y los dos que más aportarían están fuera de
presupuesto. La puerta no se ha abierto.

*(Curiosidad honesta: Gabriel Suazo es defensa y sigue entrando pese a la
penalización. El factor no es un veto, es un peso.)*

**No he comprado nada.**

## 5.2 — El portero suplente: solo uno cabe

**Caja disponible: 258.807 €. Fichas libres: 10.**

| Portero | Precio | Titularidad | Equipo | ¿Cabe? | Deja |
|---|---:|---:|---|---|---:|
| **Letacek** | **150.000** | 5 % | Getafe | **sí** | **108.807** |
| Aitor Fernández | 260.000 | 10 % | Osasuna | no, por 1.193 € | −1.193 |
| Szczęsny | 270.000 | 0 % | Barcelona | no | −11.193 |
| Álvaro Fernández | 290.000 | 5 % | Deportivo | no | −31.193 |

Pediste tres; **solo uno cabe en la caja**, y prefiero decírtelo a
maquillar la lista.

**Y una advertencia sobre lo que compra ese dinero.** Los cuatro son
terceros porteros (0-10 %). Un suplente al 5 % que tampoco juega puntúa
cero igual: el seguro no es contra una mala jornada, es contra **salir con
diez**, que es otra cosa y peor. Por 150.000 € eso está bien pagado.

Los porteros titulares de la liga cuestan entre 2,65 M (Dituro) y 5,74 M
(David Soria). Ninguno está en el mercado, y no llegaríamos.

**Tampoco he comprado.** Es tuyo decidirlo.

---

# BLOQUE 6 — La fórmula, y la sospecha no se confirma

La fórmula tal cual está, en una línea:

```
vara = [ p + (1 − p) × aparece_desde_banquillo(jerarquía) ] × calidad_cuando_juega(jerarquía)
```

con `p` = probabilidad de ser titular / 100, y las dos tablas fijadas a
mano:

```
                 aparece_banquillo   calidad
    Dios               0,70            1,00
    Clave              0,50            0,92
    Importante         0,35            0,80
    Rotación           0,20            0,62
    Revulsivo          0,45            0,50
    Reserva            0,08            0,38
    Descarte           0,03            0,25
```

**Lo primero que hay que ver: ahí no entra ni un punto medido.** La mitad
de "puntos por partido" es `calidad_cuando_juega`, una escalera decretada
a partir de una etiqueta de FutbolFantasy. La probabilidad de jugar es el
único dato empírico de la fórmula.

**Tu sospecha era que la probabilidad pesa de más. Medido, no se
confirma.** Sobre las 98 fichas de la liga:

```
    probabilidad de jugar   vs puntos/jornada    r = +0,396
    calidad por jerarquía   vs puntos/jornada    r = +0,400
    la vara entera          vs puntos/jornada    r = +0,446

    crítico para n=98:      0,199
```

Las dos mitades llevan **prácticamente la misma señal**, las dos son
significativas, y juntas mejoran a cada una por separado. La escalera
decretada resulta ser un proxy tan bueno como el dato real.

Así que **los factores no son un parche encima de un problema mayor** por
ese lado. El problema real es otro y sí es de fondo: **la vara entera
explica un 20 % de la varianza de los puntos** (r = +0,446), y ninguna de
sus dos mitades sabe en qué línea juega el jugador. Eso último es lo que
los factores arreglan; el 20 % es material para el encargo siguiente.

**No he cambiado nada de esto**, como pediste.

---

# Lo que no hice, y por qué

**No apliqué el factor del portero.** Midió ×0,932 sobre 7 fichas, por
debajo del mínimo que exige la propia medición.

**No apliqué los factores en las fichas de plantilla**, solo en el motor.
Corregir el número publicado haría que la próxima medición del sesgo se
midiera a sí misma.

**No recalculo los factores en cada ciclo.** Congelados y auditables; al
remedirlos hoy coinciden en la tercera cifra.

**No compré ningún portero ni ningún objetivo del mercado.**

**No toqué `expected_points` ni las tablas de jerarquía** (bloque 6).

**No arreglé las formas anidadas ni las funciones que leen su fichero
solas.** Están listadas arriba con nombre.

**No puedo demostrar todavía que los factores sumen.** Los +10 puntos del
once nuevo son en muestra. La prueba limpia empieza en la próxima jornada,
y es justo lo que monta el bloque 2.

---

**La frase para mañana:** el once pasa de **5-4-1 a 3-4-3**; sale Kiko
Femenía, que llevaba **cero puntos siendo titular**, y entran dos
delanteros. Los factores están puestos, se apagan con una línea
—`BORDALAS_VARA_PLANA=1`— y desde la próxima jornada el tablero dirá solo
si acertamos. De los 8 puntos que se dejaron en el banquillo, **hoy son
recuperables 3**: los otros 5 los ponía Yusi Enríquez, que ya es de
Prinzipote. Y la sospecha de que la probabilidad de jugar pesa demasiado
**no se confirma**: pesa lo mismo que la otra mitad. Lo que ninguna de las
dos sabía era en qué línea juega el jugador, y eso es lo que se acaba de
corregir.
