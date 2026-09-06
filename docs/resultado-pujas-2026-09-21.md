# VER LAS PUJAS — resultado

Rama `pujas/leer-en-vez-de-adivinar`. **89 de 89 en verde**, en las tres
condiciones (disco local, CI con caché fría, CI con caché caliente).

`bordalas-live.yml` y `MAX_SINGLE_SPECULATION_PERCENT`, sin tocar. **Ningún
tope ni ningún listón movido. No he comprado ni vendido nada. Solo GET
contra Biwenger.** Ninguna guardia nueva lee `data/`. **Sin push.**

---

## Antes de nada: la rama no sale de `main`

Pediste `desde main`, y **`main` está en `7c0e75c` (vara), sin lo de anoche**
— la rama `doctrina/que-pepe-la-siga` (`db5897a`) no se ha fusionado.

Este encargo se apoya entero en esa noche: la regla 22 que se deroga, el
embudo, la prueba de Yamal, el propio `docs/DOCTRINA.md`. Desde `main` no
existirían. **Así que la rama sale de `db5897a`**, que es el estado real del
proyecto. Si prefieres lo contrario, se rehace.

## Lo que entra en el commit

Miré `git status`. **Once ficheros:**

```
?? src/analysis/calidad_medida.py            regla 6: quién es bueno, medido
?? src/analysis/porteria.py                  regla 3: nunca a un portero
?? src/analysis/soltar_un_grande.py          lo que sustituye a los intocables
?? src/analysis/test_calidad_y_porteria_v1.py  21 pruebas, fixture
 M src/analysis/sale_intent.py               la lista, derogada
 M src/analysis/test_orden_de_venta_v1.py    le quito los tres nombres
 M scripts/run_validation_gate.py            retira intocables, pone la nueva
 M src/telemetry/dashboard_state.py          publica portería y calidad
 M dashboard-v8/src/components/DoctrinaPanel.jsx
 M docs/DOCTRINA.md                          tu v1.3
?? docs/ENCARGO-VER-LAS-PUJAS-2026-09-21.md
```

---

# BLOQUE 1 — La lectura de pujas

Ejecutada. Solo GET, contra nuestra liga, con `BiwengerClient`, que carga el
`.env` por su cuenta: **no lo abrí, no lo imprimí, y no hay ni un token en
este informe.**

## Lo que devuelve

**1. El ajuste está encendido, confirmado en vivo:**

```
liga: El chiringuito | id: 2165477
marketShowBids: True
```

**2. `GET /market` — 63 ventas, CERO campos de puja:**

```json
{"date": 1788584789, "until": 1788757200, "extended": true,
 "price": 2440000, "player": {"id": 2247}, "user": null}
```

Claves, unión de las 63: `date, extended, player, price, until, user`.
**Ninguna venta trae `bids`, `offers` ni nada parecido** — ni las 43 que son
de rivales.

**3. `GET /player/26271` → HTTP 400:**

```json
{"status": 400, "message": "Invalid method"}
```

Esa ruta no existe. **Paré ahí**, como mandaba el encargo.

## El veredicto, y contradice a la doctrina v1.3

La doctrina dice: *"si la llamada correcta devuelve pujas, `rival_bid_model`
entero sobra"*. **Con lo que la API nos expone, no sobra.** Lo que sí
devuelve el mismo endpoint es esto:

```
offers: 12   claves: amount, created, from, id, requestedPlayers, status, to, type, until
   purchase  waiting   3.381.600 €  de Computer  por [3159]
   purchase  waiting   1.609.100 €  de Computer  por [8376]
   purchase  waiting   2.052.900 €  de Computer  por [9983]
   purchase  waiting  21.099.500 €  de Computer  por [26271]   ← Yamal
status: {"balance": 1725383, "maximumBid": 14110383}
```

Es decir: **vemos las ofertas que nos hacen a nosotros, no las pujas de los
rivales por terceros.** Lo primero ya lo teníamos; lo segundo, que es lo que
el vídeo promete y lo que `rival_bid_model` estima, sigue sin verse.

Mi hipótesis, etiquetada como tal: **`marketShowBids` gobierna la web, no
esta API.** Comprobarlo requeriría mirar el tráfico del navegador, no probar
rutas a ciegas — y eso no es cosa de esta noche.

**Consecuencia: `rival_bid_model` se queda, y el desvío aleatorio de puja
también.** No hay nada que sustituir.

## Y dos cosas que la sonda destapó sin buscarlas

**El Computer ofrece 21.099.500 € por Yamal ahora mismo.** Está en la lista
de ofertas entrantes, en estado `waiting`. Es la regla 19 —las ofertas que
entran— con el caso más grande posible encima de la mesa.

**Tenemos los catorce jugadores listados en el mercado**, puestos por
nosotros, Yamal incluido a **33.480.000 €** (su precio es 21,21 M: un +58 %).
No sé si eso es lo que quieres; lo digo porque no lo había visto nadie.

---

# BLOQUE 3 — Los intocables

## Qué incidente encerraba `test_intocables_v1`

Seis pruebas, y **solo dos eran la lista**. El resto encerraba cosas reales,
y la más importante es ésta:

> **EL ACCIDENTE DEL 12/09/2026.** La regla del portero miraba solo
> `in_lineup`. El roster del dashboard trae ese mismo dato como
> `is_starter`. Con la plantilla de pantalla, **Dituro —único portero,
> titular— NO salía como intocable**, y lo único que impedía venderlo era el
> guardarraíl posicional.

Y es palabra por palabra el accidente contra el que avisaba el propio
módulo: *"Yamal está a salvo por accidente porque hay exactamente dos
delanteros; el día que entre un tercero, esa protección desaparece sola y
nadie se entera."*

**Eso no es cariño por un jugador: es el mismo dato con dos nombres.** Se
queda.

| Prueba | Qué era | Destino |
|---|---|---|
| `test_los_de_arriba_no_se_tocan` | La lista (Dios/Clave) | **se va** |
| `test_el_veto_va_antes_que_la_puntuacion` | Sostenía la lista | **se va** |
| `test_el_portero_titular_lo_es_se_llame_como_se_llame` | El accidente del 12/09 | **se queda** |
| `test_el_portero_titular_va_aparte` | Portero por puesto, no por escalón | **se queda** (ahora es la regla 3) |
| `test_sin_escalon_no_se_vende` | Vender a ciegas no se deshace | **se queda** |
| `test_los_vetados_se_ven` | Un veto no es una desaparición silenciosa | **se queda** |

## Quién estaba dentro, el día que se retira

| Jugador | Escalón | Precio | Motivo |
|---|---|---:|---|
| **Yamal** | Dios | 21.210.000 | intocable por decisión del dueño |
| **Expósito** | Clave | 5.160.000 | intocable por decisión del dueño |
| **Olasagasti** | Clave | 2.920.000 | intocable por decisión del dueño |
| **Djené** | Clave | 2.010.000 | intocable por decisión del dueño |
| Dituro | Importante | 2.650.000 | portero titular *(sigue protegido)* |

**Cinco de catorce. Después de la derogación: uno.** Vendibles, de 9 a 13.

## Retirada, no silenciada

En `run_validation_gate.py` queda escrito, en el sitio donde corría:

> *"Aquí corría `src.analysis.test_intocables_v1` (…). El dueño la retira el
> 21/09/2026. Se quita a propósito y no se silencia (…). Lo que la sustituye
> NO es otra lista, es una cuenta."*

Hay guardia que comprueba las dos mitades: que ya no está activa **y** que
la línea que lo explica sigue ahí.

*(Efecto colateral que tuve que resolver: `test_orden_de_venta_v1` exigía por
nombre que Yamal, Djené y Olasagasti no entrasen en la cola de ventas.
Mantenerlo habría sido conservar la lista por la puerta de atrás. Le quité
los tres nombres, dejé el invariante estructural —nadie puede estar apartado
y en la cola a la vez— y lo renombré por lo que de verdad vigila.)*

## Y la que la sustituye

`soltar_un_grande.py`: antes de soltar a quien pese **más del 25 %** o esté
**entre los tres que más puntúan**, se calcula si lo que entra cabe en el
once. Con el caso de Yamal dentro, como guardia.

```
Yamal pesa el 42,81 %; es el 1.º que más puntúa.
Suelta 9,33 pts/jornada, entra 10,03 y desplaza 1,67  →  neto −0,97
NO se vende: hace falta al menos +0,50.
```

**El +0,50 tiene número detrás** (regla 18): medio punto por jornada son
17,5 en 35 jornadas, del orden de la distancia al líder. Por debajo de eso,
deshacer un activo grande es movimiento, no mejora.

**Y encontré un fallo mío grave montándola.** La primera versión desplazaba
a los jugadores de campo *con menos puntos*, que son suplentes — y sacar a
un suplente no cuesta nada. Con eso Yamal salía **vendible con +0,70**.
Corregido: desplaza a **titulares**. Ya no hay lista debajo que tape un
error así, y hay guardia con ese caso.

---

# QUIÉN ES BUENO (el encargo del 19/09)

Hice los bloques **1, 2 y 4**, que es lo que ese encargo manda priorizar.

## Bloque 1 — Dónde entra un punto medido en la vara de hoy

**En ningún sitio.** Campo por campo:

```
vara = [ p + (1−p) × banquillo(jerarquía) ] × calidad(jerarquía)
```

- `p` = `starter_probability`, de FutbolFantasy. **Dato real**, pero de
  titularidad, no de puntos.
- `banquillo(...)` y `calidad(...)` = dos tablas escritas a mano indexadas
  por una **etiqueta** (Dios/Clave/Importante…).

`points_last_season`, `raw_points` y `expected_points` **existen en las
fichas del mercado y no entran en la vara del once**: `expected_points` se
usa en el horizonte de temporada y en la valoración de compra, no en elegir
el once. **Tenías razón: se publican y no los usa quien elige el once.**

## Bloque 2 — La calidad medida, y el 20 %

Construida: puntos **por partido jugado** (`playedHome + playedAway`, del
catálogo en vivo, 578 jugadores), combinando temporada pasada y ésta con

```
peso_de_esta = partidos / (partidos + 5)
```

**El criterio, escrito:** a los 5 partidos las dos mitades pesan igual, y 5
es lo que tarda un titular en jugarlos —algo más de un mes—. Antes manda lo
que ya sabíamos; después, lo que está pasando. Sin partidos, **manda la
etiqueta y la ficha dice que es ella**; nunca las dos a la vez.

### El antes y el después — y la trampa que casi cuela

| Vara | r | Varianza |
|---|---:|---:|
| **Hoy (etiqueta)** | +0,437 | **19,1 %** |
| **Con calidad medida, limpia** | +0,485 | **23,5 %** |
| ~~Con la mezcla~~ | ~~+0,787~~ | ~~61,9 %~~ |

**La tercera fila no vale nada y por poco la publico como el gran
resultado.** La mezcla usa los puntos de *esta* temporada, y la varianza se
mide contra los puntos de *esta* temporada: el mismo dato en los dos lados
de la cuenta. Sale 61,9 % por construcción.

La única calidad que no se solapa con lo que se predice es **la de la
temporada pasada**, y con ella la mejora es de **19,1 % → 23,5 %: cuatro
puntos y pico, no cuarenta**.

Hay guardia (`test_la_mejora_se_mide_sin_circularidad`) que se pone roja si
alguien vuelve a decidir con la cifra circular.

**Mejora, pero NO la he encendido.** Cuatro puntos de varianza, con tres
jornadas, y el motor eligiendo el once con ella sería un cambio mayor que
cualquier umbral de los que me prohibiste mover. Lo que la resolvería de
verdad es dejar una jornada fuera y predecirla — y eso llega solo la semana
que viene. Hay guardia de que `lineup_engine` no la importa.

## Bloque 4 — La portería

**Regla nueva, con guardia: la portería nunca se queda a uno.** Si solo hay
un portero, fichar el segundo pasa a **PRIORIDAD PRIMERA**, por encima de
cualquier operación de cartera.

Hoy, con 258.807 € de caja:

| Portero | Precio | Titularidad | ¿Cabe? |
|---|---:|---:|---|
| **Letacek** | **150.000** | 5 % | **sí**, deja 108.807 |
| Aitor Fernández | 260.000 | 0 % | no, por 1.193 € |
| Szczęsny | 270.000 | 0 % | no |
| Álvaro Fernández | 290.000 | 5 % | no |

Y el aviso que el módulo escribe solo: **un tercer portero al 5 % cubre el
salir con diez, no la jornada.** No es lo mismo y no se vende como si lo
fuera. Los titulares de la liga valen 2,65–5,74 M y ninguno está a la venta.

**No he comprado.**

---

# BLOQUE 4 de esta noche — Rotar para comprar

Con la cola de ventas que ya existe (Lucas Cepeda, Kiko Femenía, Jutglà,
Manu Sánchez, Mangala):

| Fichaje | Cuesta | Hay que soltar | Entra | Sale de titulares | **Neto** |
|---|---:|---|---:|---:|---:|
| **Amatucci** | 3.670.000 | Cepeda + Kiko + Jutglà (5,01 M) | 4,24 | 3,67 | **+0,57** |
| Roro Riquelme | 4.240.000 | los mismos tres | 1,08 | 3,67 | **−2,59** |
| Pedri | 15.350.000 | **no alcanza** ni vendiendo la cola entera (9,12 M) | — | — | — |

**Solo Amatucci paga**, y por 0,57 puntos: justo por encima del margen de
0,50. Cepeda y Kiko Femenía salen del banquillo y cuestan **cero puntos**;
lo que duele es Jutglà (3,67).

**Y el mismo aviso que con Yamal:** los 4,24 de Amatucci son una
**proyección** de la temporada pasada; los 3,67 de Jutglà están **medidos**.
No son la misma clase de dato, y +0,57 no sobrevive a esa asimetría con
holgura. **No lo he automatizado ni ejecutado.**

---

# Lo que la medición contradice

**La doctrina v1.3, regla 12**, dice que si la llamada devuelve pujas
`rival_bid_model` sobra. **No devuelve pujas de rivales.** El modelo se
queda, y el desvío aleatorio también.

**La regla 15 dice "Yamal se queda" con un neto de −2,93.** Con la cuenta
corregida —desplazando titulares y no suplentes— y la cesta de dos, el neto
es **−0,97**. Misma conclusión, número distinto; el de la doctrina venía de
la cesta de cinco.

---

# Lo que no hice, y por qué

**No probé más endpoints de pujas.** El encargo decía parar, y paré.

**No encendí la calidad medida.** Mejora 4,4 puntos de varianza con tres
jornadas. Encenderla es más grande que cualquier umbral que me prohibiste
mover, y la prueba limpia llega sola la semana que viene.

**No hice el balón parado** (bloque 3 de QUIEN-ES-BUENO) **ni la lista de la
compra** (bloque 5) **ni los centrocampistas ofensivos** (6.1). El propio
encargo lo autoriza: *"si esto es demasiado para una noche, haz los bloques
1, 2 y 4"*. Eso hice.

**No hice las noticias de los baratos** (regla 10). Segunda noche seguida, y
por lo mismo: la caché diaria de las 570 fichas es el trabajo.

**No compré el portero, ni ejecuté la rotación de Amatucci, ni respondí a la
oferta del Computer por Yamal.** Todo publicado; decides tú.

**No vendí a nadie**, aunque desde esta noche Yamal, Expósito, Olasagasti y
Djené sean técnicamente vendibles.

---

**La frase para mañana:** las pujas de los rivales **no se pueden leer** —
`marketShowBids` está encendido pero la API solo nos enseña las ofertas que
nos hacen a nosotros, así que `rival_bid_model` se queda. La lista de
intocables está retirada y lo que la sustituye ya ha demostrado su valor: al
montarla descubrí que mi primera versión **vendía a Yamal con +0,70** porque
desplazaba suplentes en vez de titulares. Y la calidad medida mejora la vara
de 19,1 % a **23,5 %** — no al 61,9 % que salía de medir los puntos contra
sí mismos. **Y hay una oferta viva de 21.099.500 € del Computer por Yamal
que nadie ha mirado.**
