# El rojo del cuadre — por qué producción veía otra cosa

**10/09/2026** · verja 111/111 · sin push

---

## La causa: el ciclo veía 468 eventos donde yo veía 241

Bajé la foto viva de producción y el bloque lo dijo en una línea:

```
Caja de 7 managers reconstruida desde el dia 1 sobre 468 eventos
```

En local, 241. Tu primera sospecha era la buena — **el ciclo lee una lista distinta
y más larga** — sólo que al revés de como lo planteamos: no le faltaban eventos,
**le sobraban**.

### Por qué el almacén acumula

`stable_event_id` hashea el **evento entero, `content` incluido**:

```python
canonical = json.dumps(event, sort_keys=True, ...)
return hashlib.sha256(...).hexdigest()[:24]
```

Biwenger **reemite el mismo hecho con el payload cambiado** — una puja más en
`bids`, unos puntos corregidos tras un aplazamiento. El hash cambia, el merge lo
guarda como evento **nuevo**, y el almacén se queda con los dos. Producción lleva
semanas acumulando; mi caché local está recién hecha y limpia (241 eventos, 241
ids distintos).

Es la misma repetición que ya conocíamos —«169 subastas, 144 distintas»— pero
creciendo con el tiempo en `data/`.

### Y el fallo, que es mío

`reconstruir` deduplicaba compras y ventas… **y no las jornadas**. Escribí el
comentario «el tablón REPITE operaciones» y lo apliqué sólo a las operaciones de
dinero.

La cuenta sale clavada:

| jornada | pagada dos veces |
|---|---|
| J2 | 1.030.000 |
| J3 | 1.830.000 |
| **total** | **2.860.000** |

Exactamente los 2.860.000 del rojo. Nuestra jornada salía **8.540.000** en vez de
5.680.000.

---

## El arreglo: la caja es inmune al tablón sucio

Ahora se deduplica **todo lo que suma o resta**, por identidad **lógica** y no por
el id del evento:

| | clave |
|---|---|
| compras y ventas | tipo · fecha · jugador · de · a · importe |
| jornadas | `round.id`, y **gana la última versión** |
| racha diaria | fecha · usuario · importe · motivo |

Que las jornadas se queden con la última versión no es un detalle: la reemisión se
debe casi siempre a una **corrección de puntos** tras un aplazamiento. La nueva
tiene que **sustituir**, no sumarse. Hay guardia para ese caso concreto.

### Verificado con el tablón ensuciado a propósito

No basta con duplicar la lista: producción no manda copias idénticas, manda el
hecho otra vez **con más información**. Así que la prueba mete una puja falsa en
cada `bids` antes de repetir:

```
limpio 241 ev  ·  reemitido 379 ev
los siete managers: diferencia 0
```

Y por el camino de producción completo, con `build_dashboard_state()`:

```
eventos 241 | repetidos descartados 27 | jornadas 4 de 5
CUADRE: La caja reconstruida cuadra con el saldo real (4.474.383 EUR)
```

---

## Las guardias — y por qué las de antes no lo cazaron

**Porque el fixture estaba limpio.** Una guardia que sólo prueba con datos
ordenados no comprueba nada del mundo real. Las tres nuevas ensucian el tablón a
propósito:

- `test_un_tablon_repetido_no_cambia_la_caja` — y comprueba que el ensuciado fue
  real: si `_reemitido` dejara de repetir, la guardia pasaría en vacío y lo dice.
- `test_la_jornada_no_se_paga_dos_veces` — el caso exacto, más la corrección de
  puntos.
- `test_se_publica_cuantos_eventos_se_leyeron` — lo que pediste.

### El contador que pediste, y una corrección sobre él

Empecé publicando `events_unique` (hechos distintos por contenido) y **no servía**:
como la reemisión cambia el payload, dos copias del mismo hecho parecen distintas
y el número no delataba nada. Lo cambié por lo que de verdad importa:

```
events_read       cuántos eventos vio el ciclo
repeats_skipped   cuántos colapsó por identidad lógica
rounds_seen / rounds_paid
```

Hoy: `241 leídos · 27 repetidos descartados · 4 jornadas de 5`. Si `repeats_skipped`
empieza a crecer, el almacén está acumulando y se ve antes de que decida nada.

---

## Lo que dejo señalado y NO he tocado

**La causa de raíz sigue viva:** `stable_event_id` hashea el `content`, así que el
almacén de `data/rival_intelligence/board_events.json` **seguirá creciendo** con
reemisiones. La caja ya es inmune, pero cualquier otro consumidor de esa lista que
no deduplique heredará el mismo problema.

Arreglarlo es cambiar la identidad del evento (hashear sólo lo estable: tipo, fecha
y los identificadores, sin `bids`) y eso toca el colector que alimenta a media
casa. **No lo hago esta noche y con esto en rojo**; lo dejo dicho para que lo
decidas.

Un dato para dimensionarlo: **28 de mis 241 eventos** ya son reemisiones
(23 `bettingPool`, 3 `market`, 2 `transfer`), y en producción son 227 de 468.

---

## Estado

- Verja: **111/111**
- Cuadre por el camino de producción: **cuadra al euro**
- Rama `main`, **sin push**
