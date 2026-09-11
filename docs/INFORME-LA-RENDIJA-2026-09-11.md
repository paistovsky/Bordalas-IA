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
| **CUPO_DEL_RESET** | **2** de estreno, 4 cuando se cierre el primer viaje entero |
| **CUPO_DE_LA_VUELTA** | 2 escrituras del carril por vuelta |

**Sobre la zona de silencio:** pediste 05:00–07:00. La que ya existe va de **04:45**
a 07:00, así que cubre lo pedido con quince minutos de más. **No he movido ningún
umbral** — uso la que hay, y hay guardia que comprueba que sigue cubriendo tu
intervalo.

### El cupo: empieza en 2, sube solo

Hasta que no se cierre **un viaje entero** —comprado, listado, oferta recibida y
**cobrada por encima del suelo**— el cupo es **2**. Abrir con cuatro sería
comprometer el doble sobre algo que no ha funcionado ni una vez.

Un corte de pérdidas o un viaje caducado **no cuentan**: cerraron el viaje, pero la
rueda no giró — se paró. Hay guardia para esos tres casos.

**Un número, un sitio.** El cupo vive en `cupo_del_reset()` y en ningún otro lado.
La portada no lo lleva escrito: lo pregunta, y pinta también el porqué:

> *«Cupo de 2 por ciclo de reset: todavía no se ha cerrado ningún viaje entero
> —comprado, listado, oferta recibida y cobrada por encima del suelo—. Sube a 4 en
> cuanto pase una vez.»*

Hay guardia (`test_la_pantalla_lee_el_cupo_no_lo_escribe`) que prohíbe que el panel
lleve el número a mano: el día que suba a 4 cambia solo.

### El coste en peticiones

```
hoy                       181 /día
el límite que rompió     1536

con el cupo de estreno (2):
  pujas                     2 /día
  listar al ganar           2 /día
  cobrar la oferta          2 /día
  PEOR CASO                 6 /día   ->  total 187 (12,2 % del límite)

cuando suba a 4:
  PEOR CASO                12 /día   ->  total 193 (12,6 % del límite)
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
EL CUPO:  2 (ESTRENO) — aún no se ha cerrado ningún viaje entero
SALDO 4.474.383     TOPE DE PUJA 16.756.883
```

**Qué compraría ahora mismo:**

| jugador | pos | precio | listaría a | suelo de cobro | viene |
|---|---|---|---|---|---|
| Marcos Alonso | DEF | 3.590.000 | 4.128.500 | 3.625.900 | sin dato |
| Starfelt | DEF | 2.150.000 | 2.472.500 | 2.171.500 | **CAYENDO −2,01 %/día** |
| **compromete** | | **5.740.000** | | | quedarían **11.016.883** |

Dos defensas, que es el orden medido (DEF +3,67 %). Los siguientes de la lista
—Cáceres (DEF), Gulácsi (POR), Sotelo (MED), Nico Williams (DEL)— **no se
descartan**: no caben en el cupo de estreno.

### El ritmo, que es lo que pediste ver

De los 11 candidatos elegibles del carril (Computer, estado `ok`, ≥ 1 M):

```
3 subiendo · 3 cayendo · 0 planos · 5 sin dato
```

**No se confirma la sospecha del libro en la sombra.** Decía que lo rechazado era
todo `PRECIO_CAYENDO`; lo que compraríamos **no** lo es —hay de todo, y Berenguer
viene subiendo un +4,75 %/día—. Pero de los dos que entran hoy, **uno viene cayendo
un −2 %/día y del otro no hay dato**, así que tampoco puedo decirte que el
experimento no sea «comprar caídos y revender».

Con 5 de 11 sin dato, esto es una **observación, no una medición** — y ya sabemos
lo que cuesta confundirlas. Por eso queda publicado en cada ciclo: la columna
`VIENE` del panel, con el porcentaje y los días de racha, y un aviso explícito si
algún día **todos** los que traen dato vienen cayendo.

**No decide nada**: nadie se cae de la lista por su ritmo. La compuerta se quitó a
propósito porque el negocio es el spread, no la rampa.

**Cuándo cobraría:** publicado en la misma vuelta a ×1,15; la publicación vive 48 h
y las ofertas se resuelven en el reset de las 07:00. Primera oportunidad el reset
siguiente, última el segundo; a los 4 resets el viaje caduca y deja de serlo.

**El peor caso:** si se ganan las dos y ninguna oferta llega al suelo, quedan
5,74 M inmovilizados en dos jugadores vendibles durante cuatro resets, con el saldo
en 4,47 M y el tope bajando a ~11,0 M. Ninguna barandilla de solvencia o deuda se
ha tocado.

## Lo que queda apagado

**Nada de esto escribe todavía.** `en_vivo=False` es el defecto en las dos rutas
nuevas, igual que en renovar y en la salida. El ensayo de arriba es cálculo sobre
datos reales, no una operación enviada.

## Guardias

`src/analysis/test_la_rendija_v1.py` — **18/18**. Las cinco puertas del carril, el
apagado automático (y que una racha de nueve **no** apaga nada — ese error ya costó
una ventana), el escaparate, la guardia clave del viaje sin listar, el caso exacto
del `HOLD` y el orden de preferencia.

---

## Estado

- Verja: **111/111**
- Coste del carril: **6 peticiones/día** con el cupo de estreno (12 si sube a 4)
- Rama `main`, **sin push** — el push lo das tú después de leer el ensayo
