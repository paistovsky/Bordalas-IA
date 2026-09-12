# Cada puja a su precio

**12/09/2026, noche** · rama `puja/cada-una-a-su-precio` · verja 117/117 · sin push

---

# VIAJES COMPLETADOS: 0

*(la puja por Trent se resuelve mañana a las 07:00)*

---

## 1. La puja del carril, anotada — y qué pasa mañana en los dos sentidos

Estaba como decías: `bid_outcome_ledger` no la tenía. El carril escribía en su
libro propio (`libro_del_carril.jsonl`) y **ese no lo lee el resolutor**, así que el
arreglo de esta tarde —que el libro sepa perder— no le servía.

Ahora anota por `record_bid`, el mismo camino que la rueda:

```
player_name     Trent
amount          2.762.258        <- el que se pujó de verdad, con desvío
market_price    2.760.000
target_source   RENDIJA
placed_at       la misma marca que el libro del carril
outcome         PENDING
```

**Uso `target_source` y no un campo `source` nuevo**: es el que ya lleva el origen
—`SUBASTA_CARTERA`, `ACQUISITION_BOARD`— y dos nombres para el mismo dato es la
regla 33.

### Qué pasa mañana a las 07:00

| | |
|---|---|
| **si gana** | Trent aparece en plantilla → no se marca `LOST`. Queda esperando a que el tablón confirme la operación y la cierre como `WON`. «Lo tengo» no prueba por sí solo que lo ganara *esta* puja |
| **si pierde** | reset pasado + no está en plantilla → **`LOST`**, con `resolved_by: RESET_SIN_JUGADOR`. Y entra en el `win_rate` |

Las dos ramas están en la guardia `test_el_carril_tambien_pierde`, ejecutadas.

### Lo que preguntas del registro de actividad

**Es a propósito, y lo dejo.** El carril corre *después* de la acción principal y
no consume `write_used` — ése fue el diseño desde que se le dio carril propio, para
que una puja de revender no le quitara la vuelta a la decisión del ciclo. El
registro de actividad cuenta la **acción de la vuelta**, y la del carril no lo es.

Pero tienes razón en la queja: hoy la única prueba de que Pepe pujó era una frase
suelta. **Eso ya no**: a partir de ahora la prueba es la entrada en el libro
compartido, con nombre, importe, origen y hora.

---

## 2. El carril ya no puja redondo

```
antes    2.760.000     el precio de mercado, redondo clavado
ahora    2.762.258     +2.258 sobre el precio
```

Enchufado por donde lo hace la rueda: `apply_bid_jitter`, la misma función, llamada
desde el ejecutor. Comprobado del árbol, no de un `grep`.

**Un tropiezo que dejo escrito porque costó un rojo:** `ceiling` en
`apply_bid_jitter` es un **techo de importe**, no el tamaño del desvío. Con
`jitter_ceiling` —que devuelve 13.800 para un jugador de 2,76 M— el techo quedaba
por debajo del suelo `precio + 1` y la función devolvía el importe limpio **sin
desviar nada y sin quejarse**. Dos cosas distintas con nombres parecidos.

La guardia comprueba que la puja no sea el precio, ni múltiplo de 10.000, 100.000 o
1.000.000, que quede por encima del precio, y que **el desvío nunca saque la puja
por encima del tope por operación**.

---

## 3. Los dos techos, con el número de Trent

```
precio de mercado                          2.760.000

EL TECHO DEL COMERCIANTE                   2.788.146    +1,02 %
  = 2.760.000 x (1 + 2,03 %) / 1,01

EL QUE SE APLICA HOY (break_even 1,80 %)   2.809.680    +1,80 %
                                           ---------
  el aplicado pasa del comerciante en         21.534
```

Tu número era 2.788.147 y el mío 2.788.146: es truncamiento de `int()` frente a
redondeo, un euro.

**El tope aplicado está por encima del techo del comerciante.** En una puja de
revender eso permite pagar 21.534 € más de lo que el viaje puede recuperar. La puja
real de hoy (2.762.258) quedó por debajo de los dos, así que no ha costado nada
todavía.

### El techo del que se queda, para el mismo jugador

```
2 puntos/jornada x 30 jornadas x 30.000 EUR/punto  =  1.800.000 EUR
                                                      65 % del precio
```

Y eso **antes** de contar lo que suba de precio. Son dos monedas distintas, como
decías.

**Publicados, no aplicados.** `bid_cap` sigue exactamente igual —guardia que lo
comprueba: `premium_percent` 0,25 % y `break_even_percent` 1,80 %— y ninguna puja
cambia de importe. Cada fila del tablero lleva ahora `los_dos_techos`, y el tablero
un resumen.

Ninguno de los dos se inventa si falta el dato: sin la prima medida del Computer no
hay techo del comerciante, y sin los puntos y las jornadas no hay techo del que se
queda. Un techo inventado es peor que no tenerlo, porque parece medido.

---

## 4. Tus dos preguntas: la respuesta es **cero**, y con matiz

### ¿Cuántas para quedarse y cuántas para revender?

Medido sobre el tablero de esta noche, 60 objetivos:

```
SPECULATION   46
XI_UPGRADE     0        <- ninguna
sin intent    14
```

**Cero para quedarse.** Así que el techo del comerciante no se le está aplicando
hoy a ningún jugador que queramos fichar, sencillamente porque no hay ninguno.
**Te has ahorrado el cambio peligroso.**

### ¿Cuántas se perdieron por quedarse por debajo del techo del comerciante?

**Ninguna que pueda demostrar, y la razón importa más que el número.** Ninguna fila
del tablero de hoy llega siquiera a una decisión de pujar:

```
MERCADO_DE_RIVAL          40      <- la puerta del mercado de rivales está cerrada
SUPERA_PRESUPUESTO         7
SIN_VALOR                  6
RENDIMIENTO_INSUFICIENTE   4
NO_DISPONIBLE              3
```

Cero pujas con tope aplicado ⇒ cero pujas que lo pasen. Y el resumen lo dice con
esas palabras, no con un «ninguna pasa» que sonaría a que se comprobó:

> «Ninguna lleva tope aplicado en esta vuelta, así que no se puede decir si alguna
> lo pasaría.»

### Y lo que **no** puedo contestar, que lo digo claro

**El histórico de pujas no lo tengo.** Mi `bid_outcome_ledger` local tiene **una**
entrada (Aubameyang, `MANUAL_DUENO`, `SPECULATION`). Las cinco tuyas —incluidas
Cáceres y Sotelo— viven en el estado de producción, que no está en el repo.

Intenté reconstruirlo desde el tablón y **no se puede**: el tablón registra quién
ganó, no quién pujó y perdió. Nuestras 16 compras ganadas sí están; las derrotas,
por definición, no.

Así que la respuesta honesta a «¿cuántas pujas de fichar se perdieron por debajo del
techo del comerciante?» es: **con el tablero de hoy, cero — y del histórico no se
puede saber sin el libro de producción.** No me lo invento.

*(Nota: la prima del Computer que mide mi tablón local es **+2,49 %** con menos
muestras que tus +2,03 % sobre 129 ventas. He usado la tuya para los números de
arriba y dejo la mía escrita en la guardia, para que se vea que el techo se mueve
con la medición y no con la opinión.)*

---

## 5. La racha diaria: Biwenger **no** publica el contador, pero **sí** el cobro

Medido sobre el snapshot y el tablón:

| | |
|---|---|
| `league.settings.bonusDailyStreak` | `True` — la bandera está |
| `catalog.meta.config.features.dailyStreak` | `True` |
| un contador de días | **no existe**, ni en `league.user` ni en ningún sitio |
| eventos `type: bonus` con `reason: dailyStreak` | **sí**, con usuario e importe |

### Y el dato que duele, sobre 34 días observados (09/08 – 12/09)

| | cobrado |
|---|---|
| **Pollo17** | **750.000** (tres veces) |
| Prinzipote · Mex · DiosMande · Manzagool | 250.000 cada uno |
| **Pepe Bordalás** | **250.000** (una vez) |

**500.000 € de diferencia con Pollo17 en un mes**, sólo por acordarse de pulsar un
botón.

**No he montado el contador.** Se puede estimar contando días desde el último cobro
—y entonces la pantalla pondría «estimado»—, pero preferí traerte la medición
primero, que es lo que pedías, y no empezar un cuarto bloque a medias. El dato de
arriba ya es accionable esta noche sin código.

---

## 6. Lo que no hice, y por qué

- **La puja viva por Trent: intacta.** Ni cancelada, ni subida, ni bajada.
- **No moví `bid_cap` ni ninguna prima aplicada** — el bloque 3 era publicar.
- **No toqué `orden_de_preferencia`.**
- **Cupo 1, suelo 1.000.000, tope del carril 3.000.000**, sin tocar.
- **`MAX_SINGLE_SPECULATION_PERCENT` y `MAX_SAFE_DEBT`**, ni mirados.
- **No toqué el workflow.**
- **Bloque 4 (medir contra quién se puja): no empezado.** Es el que más código
  nuevo pide —registrar rivales con puja viva por cada objetivo— y preferí cerrar
  1, 2, 3 y la medición del 5.2 bien a dejar cuatro a medias, como pedías.
- **Bloque 5.1 (la foto posterior a la acción): no hecho.** Mismo motivo. Es el
  siguiente que cogería: el diagnóstico ya está cerrado por ti y `refresh_snapshot()`
  ya existe.
- **No monté el contador de la racha**, por lo dicho arriba.

---

## Guardias

| | |
|---|---|
| `test_la_puja_del_carril_v1` | **5/5** — se anota, también pierde, no puja redondo, el desvío no pasa del tope, y llama a las dos funciones de verdad |
| `test_los_dos_techos_v1` | **6/6** — los dos números de Trent, que el aplicado pasa del comerciante, que son otra moneda, que no se inventan sin dato, y que `bid_cap` no se ha movido |

---

## Estado

- Verja: **117/117**
- Rama `puja/cada-una-a-su-precio`, dos commits, **sin push**
- La puja por Trent, viva y sin tocar

---

# VIAJES COMPLETADOS: 0
