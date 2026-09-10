# QUE GIRE — resultado

Rama `gire/quitar-los-tres-tapones`, encadenada sobre
`rueda/comprar-para-vender` (`16c7603`). **92 de 92 en verde**, también en CI con
caché fría.

**Ningún umbral se ha movido:** el 3 % sigue en 3 %, `EMERGENCY_SOLVENCY` en
1100, `MAX_SAFE_DEBT` y `MAX_SINGLE_SPECULATION_PERCENT` intactos. **Ninguna
decisión de compra cambia hoy.** No he vendido, comprado ni respondido ofertas.
**Sin push.**

---

# BLOQUE 0 — La respuesta, y es la que más vale de todo el encargo

**Se puede pujar por cualquiera que esté a la venta, y el escaparate no son 20:
son 47. El tablero excluye a los otros 27 a propósito.**

Leído en vivo del mercado, ahora mismo:

```
ventas en el mercado          61
  nuestras (no comprables)    14
  ─────────────────────────────
  COMPRABLES                  47
      del Computer            20   ← lo único que Pepe mira
      de rivales              27   ← invisible para Pepe
          Manzagool 10 · Pollo17 9 · Luismi_Haz 7 · Prinzipote 1
```

**No es una limitación de Biwenger. Es un filtro nuestro**, y está escrito con
todas las letras en `acquisition_board.py`:

> *"Un mercado de otro manager solo entra si ya hay dinero nuestro dentro. Si no,
> esta tabla seguiría siendo el mercado del Computer, como hasta ahora."*

`outside_computer_market: 0` no significaba "no hay". Significaba "no miramos".

## Y lo que hay ahí fuera hoy

De los 47 comprables, **19 suben y 8 suben más del 1 % diario**:

| Jugador | Ritmo/día | Tramo | Precio | Piden | Vendedor |
|---|---:|---|---:|---:|---|
| **André Almeida** | **+16,10 %** | > 4 % | 1.180.000 | **990.000** | Luismi_Haz |
| **Ejuke** | **+4,26 %** | > 4 % | 3.050.000 | **2.920.000** | Luismi_Haz |
| Tete Morente | +2,94 % | 2-4 % | 680.000 | 1.420.000 | Pollo17 |
| Gorosabel | +2,38 % | 2-4 % | 420.000 | 420.000 | Computer |
| Baena | +1,44 % | 1-2 % | 9.740.000 | 10.692.000 | Manzagool |
| Marc Roca | +1,25 % | 1-2 % | 3.190.000 | 3.696.000 | Manzagool |
| Roro Riquelme | +1,18 % | 1-2 % | 4.240.000 | 4.240.000 | Computer |
| Amatucci | +1,09 % | 1-2 % | 3.670.000 | 3.670.000 | Computer |

**Cinco de los ocho son de rivales. Y dos se piden POR DEBAJO de su precio de
mercado:** André Almeida sube un 16,10 % diario y Luismi lo pide a 990.000
cuando vale 1.180.000. Ejuke igual.

**Eso corrige lo que dije anoche.** Escribí *"hoy no hay qué comprar"* mirando
los 20 del Computer. Hay ocho, y los dos mejores llevan días delante sin que
nadie los mire. **No lo he tocado**: el encargo decía solo medir. Pero es la
pieza que sube al primer puesto del plan.

---

## Lo que entra en el commit

`git status` antes. **Diez ficheros:**

```
?? src/analysis/test_que_gire_v1.py       18 pruebas, fixture
 M src/analysis/hold_backtest.py          publica cada banda de racha
 M src/analysis/hold_switch.py            mira la celda que se compra
 M src/analysis/hold_value.py             le pasa la racha del jugador
 M src/analysis/decision_orchestrator.py  la emergencia, por el reloj
 M src/analysis/acquisition_budget.py     publica las tres puertas
 M src/analysis/acquisition_valuation.py  el motivo nombra a TENER
 M scripts/run_validation_gate.py         + 1 guardia
 M docs/PLAN.md                           tu actualización
?? docs/ENCARGO-QUE-GIRE-2026-09-24.md    tu encargo
```

---

# BLOQUE 1 — El interruptor ya mira la celda que se compra

**La causa exacta:** `calibration()` se queda con la banda de racha **más larga**
con muestra. Para el recorte está bien —a una racha de 50 días se le reconoce
como mucho lo que rindió la más larga medida— pero el interruptor reutilizaba
ese mismo número para decidir si la vía estaba respaldada.

Ahora cada tramo publica **todas sus bandas** y cada consumidor coge la suya:

| Tramo | Techo del recorte | Racha 1 día | Racha 2 días |
|---|---:|---:|---:|
| **1-2 %** | 1,80 % *(racha 2)* | **3,22 %** (n=68) | 1,80 % (n=58) |
| 2-4 % | 3,14 % | 5,61 % (n=37) | 3,14 % (n=41) |
| > 4 % | 21,15 % | 18,37 % (n=37) | 21,15 % (n=35) |
| 0,5-1 % | 0,60 % | 1,25 % (n=66) | 0,60 % (n=55) |

**Tramos encendidos: 1-2 %, 2-4 % y > 4 %** (antes solo los dos últimos).

> *Vía TENER encendida por 3 tramos. El más justo es «1-2 %», que rinde 3,22 %
> contra un listón del 3 %: le sobran 0,22 puntos. Si baja de ahí, se apaga
> sola.*

El estado se publica con **la banda y la racha con la que se ha juzgado**, para
que ningún tramo encendido sea un número sin procedencia.

**El 3 % no se ha tocado**, y hay guardia de que sigue atado a
`RENDIMIENTO_MINIMO_DEL_CAPITAL`. **Sin racha, el comportamiento es el de siempre.**

**Y no cambia ninguna decisión hoy:** Roro rinde 2,55 % y Amatucci 2,35 % — los
dos por debajo del listón. Gorosabel llega a 5,14 % y sigue `NO_DISPONIBLE` por
lesión.

---

# BLOQUE 2 — La deuda: corrijo la mitad de lo que dije anoche

## Lo que dije mal

Dije que `cash_budget = max(balance, 0)` mataba la compra en rojo. **La caja sí
se hace cero, pero la deuda segura toma el relevo**, y eso es exactamente el
diseño. Probado:

```
martes en verde                         cash 1.725.383  deuda 3.000.000  total 4.725.383  enabled True
martes EN ROJO, con garantía y holgura  cash         0  deuda 3.000.000  total 3.000.000  enabled True
```

**Comprar en rojo un martes ya era posible.** Mi conclusión de anoche era falsa,
y hay guardia para que no se vuelva a decir. *(Llegué a ella con un fixture que
usaba la clave `safe_debt` cuando el código lee `max_safe_debt`. Error mío al
montar la prueba, no del código.)*

## Lo que sí era cierto, y arreglado

`calculate_accept_expiry_priority` escalaba a **1110 por el signo del saldo**, en
cualquier fase salvo el cierre — y su propio docstring daba por hecho lo
contrario: *"la ventana urgente ya está limitada a las seis horas anteriores al
deadline"*. Nadie comprobaba el reloj.

Ahora se dispara **por la fase**, como su hermana `calculate_solvency_priority`,
que ya lo hacía bien desde siempre:

| Fase, con saldo en rojo | Antes | Ahora |
|---|---:|---:|
| **NORMAL** (lunes a jueves) | 1110 | **680** |
| PREPARATION | 1110 | 1110 |
| HIGH_ATTENTION | 1110 | 1110 |
| FINALIZATION | 1110 | 1110 |
| HARD_SAFETY | 1110 | 1110 |
| ROUND_LOCKED / TRANSITION | 0 | 0 |

**Solo cambia NORMAL.** `EMERGENCY_SOLVENCY` sigue valiendo 1100 y no se ha
tocado; lo que cambia es cuándo se dispara.

**Sobre tu pregunta de si esto puede dejar a Pepe en rojo un viernes: no.** A
T−6 h la fase es HIGH_ATTENTION o más apretada, y ahí la escalada es idéntica a
la de siempre. Y en NORMAL sigue devolviendo 680, que gana a comprar (400):
aceptar una buena oferta antes de que caduque sigue siendo prioritario. Lo que ya
no hace es aplastarlo todo un martes. **Hay guardia con los dos casos**, y la del
viernes está escrita para que si alguien la pone en rojo sepa que la rueda se ha
comido al reloj.

## Y un agujero de visibilidad que apareció mirando esto

Que Pepe pueda comprar en rojo depende de **tres campos**, y **ninguno se
publicaba**:

```
solvency_guaranteed · debt_window_open · temporary_debt_allowed
```

Al investigar por qué el permiso llevaba semanas sin usarse, **no había forma de
saber cuál de las tres puertas estaba cerrada** — y desde `status.json` sigo sin
poder decirlo, porque el bloque de solvencia publicado no los trae. Ahora el
presupuesto los publica, con su holgura. Es la misma familia que todo lo de esta
semana: el dato existía y no se veía.

---

# BLOQUE 3 — El motivo ya nombra a TENER

El texto del rechazo narraba once, especulación y reventa. Ahora también *"como
tenerlo mientras sube"*. Con la regla 17, un rechazo que no cuenta la vía que
decide es un rechazo que miente por omisión.

---

# BLOQUE 4 — Las ramas sin fusionar, y en qué orden

**`main` está en `40ab7b1`. Hay dos cabezas sin fusionar y NO están encadenadas
entre sí:**

```
main  40ab7b1
 ├── balon-parado/quien-tira-los-penaltis   682d65d   (1 commit)
 └── rueda/comprar-para-vender              16c7603   (2 commits)
      └── gire/quitar-los-tres-tapones      ← esta rama (3 con el de hoy)
```

`rueda` salió de `main` porque me lo pediste así, y por eso **no incluye el balón
parado**. Son paralelas.

**Orden recomendado:**

1. **`balon-parado/quien-tira-los-penaltis`** primero — es una sola rama y la más
   independiente.
2. **`gire/quitar-los-tres-tapones`** después — arrastra `rueda` entera.

**Conflictos que vas a encontrar, los dos triviales y con la misma resolución
(quedarse con las dos partes):**

- `scripts/run_validation_gate.py` — las dos ramas añaden entradas a la lista.
- `src/analysis/acquisition_valuation.py` — balón parado añadió
  `last_season_points`; ésta añadió el motivo de TENER. Son sitios distintos del
  mismo fichero.

**No las he fusionado**, como pediste.

---

# Lo que no hice, y por qué

**No quité el filtro del mercado de rivales.** Es el hallazgo del bloque 0 y el
encargo decía *"solo medir y contestar"*. Es también el cambio más grande de los
cinco: multiplicaría por 2,4 el universo que Pepe juzga y abriría la puerta a
pujar contra managers, que es un juego distinto —hay que ofrecer al dueño, no al
Computer— y la salida garantizada al Computer no aplica igual.

**No he modelado el caudal semanal de los ~140.** La pregunta era condicional
("si son solo los 20 del día") y la respuesta es que **no son solo esos**, así
que la medición pierde sentido: lo que hay que medir es el flujo de los 47, y eso
son varias semanas de observación.

**No he tocado la prioridad `SOLVENCY_NORMAL` (500) frente a `SPECULATION_BUY`
(400).** Vender para recuperar sigue ganando a comprar cuando el saldo está en
rojo, y eso me parece correcto: se resuelve solo en cuanto el saldo vuelve a
verde.

**No he publicado los tres campos de la deuda en el dashboard**, solo en el
presupuesto. Falta el panel.

**No he comprado, vendido ni respondido a ninguna oferta.**

---

**La frase para mañana:** anoche dije que no había qué comprar y estaba mirando
por la mirilla. **El escaparate no son 20 jugadores, son 47** — los otros 27 los
venden los rivales y un filtro nuestro los esconde. Ahí fuera hay **ocho subiendo
más del 1 % diario**, y dos de ellos —**André Almeida a +16,10 % diario, que
Luismi pide a 990.000 cuando vale 1.180.000**— llevan días delante sin que nadie
los mire. Los tres tapones están quitados y ningún umbral se ha movido, pero el
cuarto, que es éste, decide si la rueda vale un millón al mes o trescientos mil.
