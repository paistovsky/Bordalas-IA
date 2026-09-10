# Tres cosas cortas

**10/09/2026** · verja 107/107 · sin push

---

## 1. Doctrina 35 — una hora sin zona es un dato con dos nombres

Escrita, con los tres fallos del día nombrados: el cron externo (CET contra CEST,
la ventana sin abrir dos semanas), el cálculo interno, y `meta.generated_at`.

Lo que la regla fija en la práctica: al **escribir**, ISO con offset o `Z`; al
**leer** uno ajeno sin zona, se normaliza **en la primera línea que lo toca**; la
hora de una zona con horario de verano **se pide a la base de zonas**, nunca se
codifica como `+2` — en marzo y octubre no lo es. Y un nombre de variable no
documenta una zona: `ahora_madrid` es una promesa, no una garantía.

---

## 2. Doctrina 36 — un valor por defecto no puede absorber el caso más importante

Escrita, con los dos del día: `THREAT[...] || "pill idle"` y `state or ABIERTO`.

**La forma del fallo es siempre la misma:** el caso peligroso es el que *falta* de
la tabla —el nuevo, el raro, el que nadie previó— y el defecto lo disfraza del
caso más común, que casi siempre es el tranquilo. Y no deja rastro: sin excepción,
sin registro, nada que buscar después.

### El barrido

Un solo sitio decide qué es «desconocido»: `dashboard-v8/src/lib/tono.js`.
Devuelve un tono **propio** —ni benigno ni crítico, a rayas moradas— y **enseña el
valor crudo** que no supo traducir. Si mañana aparece un `VERY_HIGH` nuevo, se ve
que apareció.

**Pantalla — 10 sitios en 6 ficheros:**

| dónde | tabla | caía en |
|---|---|---|
| StandingsIntelPanel | `THREAT` | `pill idle` ← **el incidente** |
| PressPanel | `TONO` | `pill idle` |
| SolvencyClockPanel | `TONO` | `idle` |
| ScoutPanel | `DIRECCION` | `FLAT` |
| ScoutPanel | `ACUERDO` | `NONE` |
| PosiblesCambiosPanel | `TONO` | `pill idle` |
| MarketPage | `DIVERGENCIA` | `pill idle` |
| MarketPage | `COMPUERTA` | `dim` |
| MarketPage | `VIA` | `dim` |
| MarketPage | `DECISION` | `idle` |

`RacePanel` ya caía en `URGENCIA.SIN_DATOS` — entrada explícita, correcta. Las
tablas de posición que caen a `?` se quedan: `?` está diciendo la verdad.

### Y una que sí cambia una decisión — conviene que la veas

En `acquisition_board.py` y `intelligent_bid_engine.py`:

```python
estado = str(ficha.get("status") or "ok").lower()
```

Un jugador **sin ficha de estado entraba en el tablero como sano**. Y había un
segundo defecto encadenado: la puerta de la puja era
`if estado not in {"ok", "unknown"}`, así que **«unknown» también se pujaba**. Un
jugador del que no sabemos si está disponible se compraba igual que uno del que
sabemos que sí.

Ahora el ausente se llama `ESTADO_DESCONOCIDO` y la puerta compara exacto:
`if estado != "ok"`.

**Medido antes de tocarlo: 0 de 20 fichas del tablero llegan sin estado** (16 ok,
3 injured, 1 discarded). **No cambia ninguna puja de hoy.** Cambia el día que el
catálogo venga cojo — que es exactamente cuando importa y cuando nadie estaría
mirando. Lo señalo porque es el único punto del barrido que toca una ruta de
decisión y no solo un color.

---

## 3. El crédito derivado ahora puede desmentirse

Tenías razón en el problema: `deudaMaxima + comprometido − saldo` **cuadra
siempre**, incluso si `maximumBid` viniera mal — el crédito absorbería el error
entero y los cuatro números seguirían sumando tan tranquilos.

Se contrasta contra la vía que **no pasa por `maximumBid`**:

```
línea de crédito = valor de plantilla × 0,25
```

`50.040.000 × 0,25 = 12.510.000` — al euro, tu número.

Si las dos no coinciden (margen de 1 € por el redondeo del 0,25, ni uno más), la
tira sale **en rojo** y dice las dos:

```
Deuda máxima NO CUADRA
crédito 12.510.000 por resta, pero 11.980.000 por plantilla
(47.920.000 × 0,25): se llevan 530.000
```

La independencia de las dos vías está **guardada**:
`test_la_via_medida_no_pasa_por_maximum_bid` comprueba por firma que `headroom_de`
no recibe `maximum_bid` — si algún día lo recibiera, las dos coincidirían siempre
y el contraste dejaría de comprobar nada sin que se notase.

---

## Guardias

`src/analysis/test_lo_desconocido_v1.py` — **12/12**. No comprueban un cálculo:
comprueban una **forma**. Que ninguna tabla de severidad tenga defecto tranquilo,
que ningún permiso se conceda por la veracidad de un valor, que ninguna hora cruce
un límite sin zona, y que la pantalla pueda avisar de que se equivoca.

Una nota: `test_el_permiso_de_vender_se_compara_exacto` se saltó primero porque
leía el `state or ABIERTO` que vive **dentro del comentario** que documenta el
incidente en `salida_del_viaje.py`. Ahora quita los comentarios antes de mirar: una
guardia que obligue a borrar la explicación del fallo para pasar es una guardia que
hace daño.

---

## Estado

- Verja encadenada: **107/107**
- `vite build` hecho, `dist` copiado a `dashboard/`
- Rama `main`, **sin push**
