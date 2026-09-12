# El carril comía de un plato vacío

**12/09/2026** · rama `carril/el-plato-vacio` · verja 115/115 · sin push

---

# VIAJES COMPLETADOS: 0

---

## 1. Qué recibía `correr`, campo por campo

Tenías razón en todo, incluido el diagnóstico. Medido con el snapshot de hoy,
pasando el mismo `cycle` por la función antes y después:

| se le pasa | de dónde | **antes** | **después** |
|---|---|---|---|
| `objetivos` | `tablero["targets"]` | **`[]`** | **60** |
| `caja` | `estado["balance"]` | `None` | **4.333.406** |
| `comprometido` | `speculation.bid_exposure` | `None` | **0** |
| `presupuesto` | `tablero["budgets"]["speculation"]` | `None` | **2.109.030** |
| `curva` | `tablero["premium_model"]["curve"]` | defecto `[[1.0, 0]]` | **del tablero, 18 pujas** |

Y la nota que avisaba del agujero estaba ochenta líneas más arriba, en el mismo
fichero. La he citado literalmente dentro de `_correr_el_carril`, para que la
próxima persona que lea esa función se encuentre las dos cosas juntas.

**La prueba cruzada que aportas es la que cierra el caso:** `_pujar_en_el_reset`
era la única función del fichero que llamaba a `_estado_publicado`, y es la única
que compró. No eran dos teorías compitiendo — una nunca se sentó a la mesa.

---

## 2. Sí hubo que publicar `balance` y `speculation`, y por qué

`_estado_publicado` ya los **usaba por dentro** —los necesita para el reloj de
solvencia— pero no los devolvía. Así que el carril tenía que ir a buscarlos por su
cuenta, que es exactamente cómo se cayó en el agujero.

No inventé un tercer camino: se publican donde ya se leen, y las dos rutas leen los
mismos campos del mismo sitio. **Un tercer camino a los mismos datos es un cuarto
fallo esperando.**

### Las guardias

- **`test_el_carril_no_come_de_un_plato_vacio`** — `cycle` de forma real
  (`{snapshot, result:{state}, execution, post_action}`, **sin `state` en la raíz**),
  tres candidatos de la foto de hoy, dos de ellos pagables. Comprueba los cinco
  campos. La curva del fixture es **1,0029** a propósito: si fuera 1,0 el defecto
  pasaría la guardia sin distinguirse.
- **`test_las_dos_rutas_leen_el_mismo_tablero`** — el mismo `cycle` por las dos, y
  el `acquisition` que ve cada una tiene que ser **el mismo objeto** (`is`, no `==`).
- **`test_solo_hay_una_puerta_al_tablero`** — del árbol: las dos rutas que escriben
  tienen que estar entre las que llaman a `_estado_publicado`. Una tercera ruta con
  su propio `.get("state")` pone esto rojo.
- **`test_el_carril_no_busca_el_estado_por_su_cuenta`** — prohíbe la expresión.

**Regla 24:** el fixture trae candidatos y la guardia exige que al menos uno sea
pagable. Una guardia que pasara con la lista vacía es justo la que no habría
detectado esto.

---

## 3. Cuántos le llegan ahora, y a quién elegiría

```
objetivos 60  ->  sobre el suelo 9  ->  entran por margen 8
              ->  4 DE 8 SE PUEDEN PAGAR (tope 3.000.000)
```

| | pos | precio | margen |
|---|---|---|---|
| **Trent** | DEF | 2.760.000 | **+3,67 %** |
| Rubén García | MED | 2.680.000 | +2,85 % |
| Isaac Romero | DEL | 2.350.000 | +1,80 % |
| Maguette Gueye | MED | 1.730.000 | +1,35 % |

```
ELEGIRÍA:  Trent (DEF, 2.760.000)    cupo 1, PRUEBA_DE_HUMO
```

### Un número que veo al pasar y que no he tocado

La curva calibrada de hoy es real —**18 pujas**, mediana **1,02x**— pero el carril
usa `curve[0][0]`, que es el **tramo más barato: 1,0000**. Es decir, puja al precio
de mercado exacto, prima 0 %.

Por valor es indistinguible del defecto; por origen no. En una liga donde el 76 %
de las subastas están disputadas, pujar al tramo más bajo de la curva es pujar a
perder. **No lo he cambiado** —es una decisión de modelo, no un arreglo— pero queda
el número.

---

## 4. Quién lee `win_rate`: nadie que decida

Tu sospecha era razonable y **no se cumple**. Comprobado, y con guardia:

```
calibrate_premium_curve(managers, price_lookup)
                        ^^^^^^^^
        las pujas de LOS RIVALES observadas en el tablón
```

`rival_bid_model.py` **no menciona** `bid_outcome_ledger`, ni `win_rate`, ni
`sync_bid_outcomes`. Nuestro libro es de sólo lectura para las decisiones: se
escribe al pujar (`record_bid`) y se pinta en `BidOutcomesPanel`. El único lector de
`win_rate` en todo Python es el propio libro, que lo calcula.

**No llevábamos días calibrando sobre «nunca perdemos».** `test_la_prima_de_puja_no_se_calibra_con_nuestro_libro`
se pone roja el día que alguien los conecte.

### El arreglo del libro

Una puja cuyo reset ya pasó y cuyo jugador no está en la plantilla es **`LOST`**,
sin necesidad del tablón — y es justo cuando el tablón no trae la operación cuando
esto importa. El caso real de hoy, en la guardia:

```
Cáceres  1.503.751  04:46:55  ->  LOST   (resolved_by: RESET_SIN_JUGADOR)
Sotelo   1.604.001  04:52:15  ->  LOST
Fortuño    150.376  04:46:55  ->  WON
D. Conde   240.601  04:46:55  ->  WON

win_rate:  1.0  ->  0.5
```

Con **dos frenos**, porque inventar derrotas sería peor que no medir: sin plantilla
conocida no se marca nada, y una plantilla vacía se trata como lectura rota (tenemos
15), no como «no tenemos a nadie».

**Y un error de zona que casi se cuela otra vez:** `_hora_de_madrid` devuelve la
hora de *pared* de Madrid todavía etiquetada UTC. Mi primera versión devolvía
`07:00+00:00`, que como instante son las 09:00 de Madrid — **dos horas tarde**, y
las pujas de la ventana se habrían quedado sin resolver toda la mañana. Corregido y
con guardia. Doctrina 35, octava vez.

---

## 5. El reloj de 48 h: medido, y no era ninguna de las dos

**n = 13 listados propios + 8 renovaciones del libro.** Y gana la medición:

| | |
|---|---|
| `until − date` | **48,00 h en los trece, al segundo** |
| los ocho de «0,0» | listados el **10/09 a las 10:25 y 10:35 UTC** |
| caducaron | **12/09 a las 10:25 y 10:35** |
| la foto | 12/09 **12:42** → **llevaban 2,28 y 2,11 h muertos** |

**(a) es falsa: renovar SÍ reinicia el reloj.** El libro de renovaciones del 10/09
casa **al minuto** con la fecha de listado de esos seis:

```
libro   10/09 10:25:48  Jutglà · Zubeldia · Djené · Pablo Ibáñez
sale    10/09 10:25     los cuatro, date = esa marca

libro   10/09 10:35:31  Jonny (tras dos intentos fallidos a las 10:26) · Pablo Durán
sale    10/09 10:35     los dos
```

**(b) es media verdad: el contador no está roto, está recortado.** Había un
`max(hours_to_expiry, 0.0)` que convierte **«llegó tarde» en «justo a tiempo»**.
Quitado. Ninguna decisión cambia —todos los consumidores comparan con `<=`, y un
negativo cumple igual que un cero— pero ahora se ve.

### Y la contradicción de la foto se explica sola

Los dos textos eran **correctos**: no se pueden salvar renovando en la ventana
—ya están muertos— y aun así hay que reencolarlos, porque un listado caducado se
vuelve a publicar. Lo que no se entendía era el «0,0».

### Sobre tu `MARKET_LISTING_RENEW_URGENT` con prioridad 690

**No es un número inventado: es un número recortado.** La dirección era correcta
—esos ocho listados están de verdad caducados y de verdad hay que republicarlos—
así que la decisión de cabecera estaba bien tomada. Lo que estaba mal era lo que
enseñaba.

### Lo que esto NO arregla, y es lo siguiente que miraría

**La última renovación fue el 10/09.** Que ocho listados caduquen significa que
nadie los renovó en 48 horas. Quitar un clamp no arregla eso. No lo he tocado
porque no está en el encargo y porque tocar la renovación mueve la escritura única
del ciclo — pero el dato está medido y es el que yo miraría mañana.

Y los tres precios que citas —Manu Sánchez 1.800.000 → 1.839.999 y los otros dos—
**no son dos observaciones**: entre mis dos fotos (12:42 y 14:36) los trece
listados están **idénticos**, mismo precio y misma fecha, cero cambios. Son precios
**propuestos** por el plan de renovación, no aplicados. Eso encaja con que la
última renovación real fuera la del 10/09.

---

## 6. Lo que no hice, y por qué

- **No subí el cupo.** Sigue en 1: la prueba de humo no ha pasado.
- **No toqué el suelo (1.000.000) ni el tope (3.000.000).**
- **No toqué `MAX_SINGLE_SPECULATION_PERCENT` ni `MAX_SAFE_DEBT`.**
- **No despausé el motor de especular.**
- **No toqué `.github/workflows/bordalas-live.yml`.**
- **No arreglé la renovación que lleva dos días sin correr** — medido y dicho
  arriba, fuera del encargo, y mueve la escritura única del ciclo.
- **No cambié `curve[0][0]` por la mediana** — es una decisión de modelo, tuya.
- **No toqué el `max(..., 0.0)` de `computer_offer_reroll_engine`**, que tiene el
  mismo clamp para *ofertas*. Otro dominio; queda señalado.

## 5-bis. Lo que funciona y no se ha tocado

La zona de silencio con el criterio nuevo, la ventana del reset, y la renovación
que reprecia. Confirmado por tu foto y no modificado.

---

## Guardias

Tres ficheros nuevos, **16 guardias**, las tres registradas en la verja:

| | |
|---|---|
| `test_el_plato_del_carril_v1` | **5/5** |
| `test_el_libro_sabe_perder_v1` | **6/6** |
| `test_el_reloj_de_48h_v1` | **5/5** |

Y una sexta vez que una guardia tropezaba con la nota que documenta el fallo: ahora
hay un `_codigo_vivo()` que quita comentarios **y docstrings**, estos últimos por el
árbol y no a ojo. Una guardia que obliga a borrar la explicación para pasar hace
daño.

`test_verja_determinista_v1` cazó una ruta `data/` en mi fixture —nunca se leía—
y tenía razón: quitada.

---

## Estado

- Verja: **115/115**
- Rama `carril/el-plato-vacio`, **sin push**
- Pantalla construida y desplegada

---

# VIAJES COMPLETADOS: 0
