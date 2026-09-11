# La rendija: carril propio, escaparate y el ensayo en seco

**11/09/2026** · verja 111/111 · **sin push — falta tu lectura del ensayo**

---

## 1. El carril propio

Tenías razón en la corrección: el problema no era el orden, era estar en la cola.
`SPECULATION_BUY` sigue en 400 y **no lo he tocado**. Lo que cambia es que una
operación `RENDIJA` ya no compite por el hueco de la vuelta — se ejecuta **después**
de la acción principal, con presupuesto propio.

`src/analysis/la_rendija.py`. Cinco puertas, y cada «no» dice por qué:

| puerta | |
|---|---|
| **APAGADA** | la rendija se cerró sola |
| **SILENCIO** | mientras el mercado se resuelve, nada |
| **EMERGENCIA** | si la vuelta se fue en una `EMERGENCY_*`, `HARD_SAFETY` o `ROUND_LOCK`, el carril se calla |
| **CUPO_DEL_RESET** | 4 operaciones de 07:00 a 07:00 |
| **CUPO_DE_LA_VUELTA** | 2 escrituras del carril por vuelta |

**Sobre la zona de silencio:** pediste 05:00–07:00. La que ya existe va de **04:45**
a 07:00, así que cubre lo pedido con quince minutos de más. **No he movido ningún
umbral** — uso la que hay, y hay guardia que comprueba que sigue cubriendo tu
intervalo.

### El coste en peticiones

```
hoy                       181 /día
el límite que rompió     1536

pujas                       4 /día   (cupo por reset)
listar al ganar             4 /día   (peor caso: se ganan las 4)
cobrar la oferta            4 /día   (peor caso: se cierran las 4)
----------------------------------
PEOR CASO                  12 /día

total                     193 /día   (12,6 % del límite)
margen                   1343
```

**El tope por vuelta no es el que manda.** 2 × 23 vueltas daría 46; el que ata es
el cupo por reset. En el peor caso imaginable —se ganan las cuatro y se cierran las
cuatro el mismo día— el carril cuesta **12 peticiones**.

## 2. El escaparate

`src/actions/escaparate_executor.py`. Al **ganar** la puja (no al ponerla): se marca
VIAJE y se lista **en la misma vuelta**. Precio `valor × 1,15`, la misma constante
que renovar — aquí el `max(precio_actual, …)` se resuelve solo porque un recién
comprado no tiene precio anterior que proteger.

**El orden importa y está escrito:** primero marcar, luego listar. Si se listara
primero y el marcado fallase, quedaría un jugador en venta al que la ruta del viaje
no reconoce, y lo juzgaría el motor de siempre con la pregunta equivocada. Marcando
primero, el peor caso es un viaje marcado y sin listar — y de eso hay guardia.

**El coste no se reconstruye:** sale de `owner.price`. El libro de viajes
(`libro_de_viajes.py`) guarda **sólo quién es un viaje**; cuánto costó se pregunta a
la API. Si el libro se perdiera, el coste seguiría siendo correcto y el fallo sería
del lado seguro: sin marca, la ruta no toca al jugador.

### La guardia clave

`test_un_viaje_no_puede_acabar_el_ciclo_sin_listar`. Sale en rojo en la portada con
**nombre y hora**:

```
VIAJES SIN LISTAR: Expósito (desde 2026-09-11T10:00). Comprados para
revender y no están en venta: cada vuelta así es escaparate tirado.
```

## 3. El cableado que no existía

Confirmado por el plano: hoy la oferta de un VIAJE la juzgaba
`offer_decision_engine` con `speculation_score >= 62 and price_increment > 0 →
HOLD_OFFER`.

Para un VIAJE es **la peor regla posible**: un jugador comprado para revender tiene,
por construcción, señal especulativa alta y precio subiendo. La regla lo retenía
**justo cuando el viaje estaba saliendo bien**.

Un VIAJE sale ahora de esa cola **antes de entrar**, y contesta una sola pregunta.
La guardia usa tu caso exacto —`score 90`, precio subiendo—:

```
sin marca VIAJE   ->  HOLD_OFFER     (la plantilla, sin tocar)
con marca, 5,30 M ->  ACCEPT_TRIP    supera el suelo de 5.198.470
con marca, 5,15 M ->  HOLD_TRIP      no llega al suelo
con marca, sin coste -> HOLD_TRIP    no se puede juzgar, no se vende
```

---

## EL ENSAYO EN SECO — datos de hoy, 11/09, en vivo

```
EL CARRIL:  puede escribir · quedan 2 en la vuelta y 4 en el ciclo de reset
SALDO 4.474.383     TOPE DE PUJA 16.756.883

Mercado del Computer:  20 jugadores
  con estado "ok":     15      (los 5 restantes, descartados por estado)
  de 1 M o más:        10      (los de menos no pagan la ficha)
```

**Qué compraría ahora mismo, en orden de preferencia:**

| jugador | pos | precio | listaría a | suelo de cobro |
|---|---|---|---|---|
| Marcos Alonso | DEF | 3.590.000 | 4.128.500 | 3.625.900 |
| Starfelt | DEF | 2.150.000 | 2.472.500 | 2.171.500 |
| Cáceres | DEF | 1.540.000 | 1.771.000 | 1.555.400 |
| Gulácsi | POR | 1.590.000 | 1.828.500 | 1.605.900 |
| **compromete** | | **8.870.000** | | |

Sobre un tope de 16.756.883 quedarían **7.886.883** libres.

**Los cuatro defensas y el portero primero, y no por casualidad:** es el orden
medido (DEF +3,67 %, POR +3,26 %, MED +2,85 %, DEL +1,80 %). Los siguientes de la
lista —Sotelo (MED), Nico Williams (DEL, 8 M), Robbie Ure, Berenguer— **no se
descartan**, simplemente no caben en el cupo de 4. Es orden, no filtro.

**Qué ofertas espera y cuándo cobraría:** se publica en la misma vuelta a `×1,15`,
la publicación vive 48 h, y las ofertas se resuelven en el **reset de las 07:00**.
Así que la primera oportunidad de cobrar es el reset siguiente, y la última el
segundo. Se cobra la oferta que supere el suelo de la columna de la derecha; por
debajo, se espera. A los **4 resets** el viaje caduca y deja de serlo.

**El peor caso, para que lo veas antes de decidir:** si se ganan las cuatro y
ninguna oferta llega al suelo, quedan 8,87 M inmovilizados en cuatro jugadores
vendibles durante cuatro resets, con el saldo en 4,47 M y el tope bajando a ~7,9 M.
Las barandillas de solvencia y deuda siguen puestas y ninguna se ha tocado.

---

## Lo que queda apagado

**Nada de esto escribe todavía.** `en_vivo=False` es el defecto en las dos rutas
nuevas, igual que en renovar y en la salida. El ensayo de arriba es cálculo sobre
datos reales, no una operación enviada.

## Guardias

`src/analysis/test_la_rendija_v1.py` — **14/14**. Las cinco puertas del carril, el
apagado automático (y que una racha de nueve **no** apaga nada — ese error ya costó
una ventana), el escaparate, la guardia clave del viaje sin listar, el caso exacto
del `HOLD` y el orden de preferencia.

---

## Estado

- Verja: **111/111**
- Coste del carril: **12 peticiones/día en el peor caso**
- Rama `main`, **sin push** — el push lo das tú después de leer el ensayo
