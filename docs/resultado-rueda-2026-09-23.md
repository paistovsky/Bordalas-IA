# LA RUEDA — resultado

Rama `rueda/comprar-para-vender`, desde `main` (`40ab7b1`). **91 de 91 en
verde**, también en CI con caché fría.

**No se ha encendido la rueda ni se ha movido ningún umbral.** No he vendido,
comprado ni respondido ofertas. Ninguna guardia nueva lee `data/`. **Sin push.**

---

# La primera línea, que es la que pediste

**El filtro del once NO está matando la rueda. Y el hallazgo es que el problema
era mi etiqueta.**

El 20/09 te dije *"12 de 20 mueren por `NO_MEJORA_EL_ONCE`"*, y de ahí salió la
sospecha que abre el PLAN v2. **Esa etiqueta la puse yo y estaba mal.**
`SIN_VALOR` no significa "no mejora el once": significa **"ninguna vía lo
quiere"**, y el propio objetivo publica el veredicto de cada una.

Los doce estaban evaluados por todas las vías. Y mueren por una razón mucho más
simple: **ninguno de los doce sube.**

---

## Lo que entra en el commit

`git status` antes de commitear. **Tres ficheros, todos míos:**

```
?? src/analysis/rueda.py            la calculadora
?? src/analysis/test_rueda_v1.py    16 pruebas, fixture
 M scripts/run_validation_gate.py   + 1 guardia
```

**Aviso:** el commit `7982710` («docs: plan v2, doctrina v1.5 y el encargo de la
rueda») apareció **en esta rama** mientras trabajaba, y no lo hice yo. Es la
misma situación que investigué el 16/09 con `1459222`: tu herramienta commitea en
el repositorio durante mi sesión. Inocuo —son los tres documentos— pero lo digo.

---

# BLOQUE 1 — Los doce, uno a uno

| Jugador | Precio | Ritmo/día | ONCE | ESPECULAR | REVENTA |
|---|---:|---:|---|---|---|
| Álvaro Fernández | 290.000 | **0,00 %** | NO_MEJORA_JERARQUIA | SIN_REVALORIZACION | PRECIO_CAYENDO |
| Aitor Fernández | 260.000 | **0,00 %** | NO_MEJORA_JERARQUIA | PRECIO_CAYENDO | PRECIO_CAYENDO |
| Letacek | 150.000 | **0,00 %** | NO_MEJORA_JERARQUIA | SIN_REVALORIZACION | PRECIO_CAYENDO |
| Szczęsny | 270.000 | **0,00 %** | NO_MEJORA_JERARQUIA | SIN_REVALORIZACION | PRECIO_CAYENDO |
| Bellerín | 2.430.000 | −0,41 % | NO_MEJORA | SIN_REVALORIZACION | PRECIO_CAYENDO |
| Loureiro | 1.240.000 | −0,81 % | NO_MEJORA_TITULARIDAD | SIN_REVALORIZACION | PRECIO_CAYENDO |
| Tárrega | 2.180.000 | −1,38 % | NO_MEJORA_TITULARIDAD | PRECIO_CAYENDO | PRECIO_CAYENDO |
| Johnny | 670.000 | −1,49 % | NO_MEJORA_JERARQUIA | SIN_REVALORIZACION | PRECIO_CAYENDO |
| Drkusic | 1.730.000 | −1,73 % | NO_MEJORA_TITULARIDAD | SIN_REVALORIZACION | PRECIO_CAYENDO |
| Miguel Rodríguez | 500.000 | −2,00 % | NO_MEJORA_JERARQUIA | SIN_REVALORIZACION | PRECIO_CAYENDO |
| Bright Ede | 1.140.000 | −2,63 % | NO_MEJORA_TITULARIDAD | MARGEN_INSUFICIENTE | PRECIO_CAYENDO |
| Pelayo | 240.000 | −4,17 % | NO_MEJORA_JERARQUIA | MARGEN_INSUFICIENTE | PRECIO_CAYENDO |

**Ocho caen, cuatro están planos, ninguno sube.** La regla 13 dice que quien cae
vuelve a caer el 90,7 % de las veces. **La rueda los rechaza bien.**

## ¿Llegó la vía de cartera a mirarlos?

**Sí, las tres que se narran. Y la cuarta —TENER— también se evalúa, pero no se
publica.**

Lo comprobé en el código: `como_tener` se calcula (línea 822), entra a competir
(línea 1023) y viaja en la salida como `as_hold` (línea 1237). Y `DEPLOYMENT_ENABLED
= True` en producción, que es la condición para que compita.

**El defecto, y es de una línea:** la frase que explica el rechazo lista *once,
especulación y reventa* — y **no TENER**. Desde fuera es imposible saber qué dijo
la vía de la rampa, que es justo la que sostiene la rueda. Está en
`acquisition_valuation.py`, en la lista `motivos` del camino `SIN_VALOR`: falta
un `if como_tener: motivos.append(...)`.

**No lo he tocado**, como pediste. Es narración, no lógica de decisión, así que
es de las seguras — pero pasa por la ruta del dinero y prefiero que lo mires.

---

# BLOQUE 2 — Cuánto puede dar la rueda

```
bolsillo de especular   2.497.407 EUR
fichas libres           8
ciclo                   3 días        →  10,0 ciclos al mes
rendimiento medido      +4,47 %       (n=142, una semana de agosto)
prima del Computer      +1,76 %       (n=106 ventas, 73,6 % positivas)
tope por operación      973.594 EUR   →  8 × 973.594 = 7,79 M, no ata
```

| Escenario | Por operación | Por ciclo | **Al mes** | % del bolsillo |
|---|---:|---:|---:|---:|
| optimista (lo medido) | 4,47 % | 155.588 | **1.555.885** | 62,3 % |
| **prudente (la mitad)** | 2,24 % | 99.771 | **997.714** | 40,0 % |
| pesimista (un cuarto) | 1,12 % | 71.863 | **718.629** | 28,8 % |

**Lo que limita es el capital**, no las fichas ni el tope: con ocho fichas y el
tope actual caben 7,79 M y solo hay 2,50 M.

**Así que la respuesta es "es la liga", no "un entretenimiento caro":** incluso
en el escenario pesimista son **718.629 € al mes**, y el bolsillo de fichar
entero son 5,46 M.

## Pero ese número es un techo, y hoy no se alcanza ni de lejos

De los 20 del escaparate de hoy, por tramo de ritmo:

| Tramo | Jugadores | Valor |
|---|---:|---:|
| CAE | **11** | 15,38 M |
| 0-0,25 % | 5 | 1,22 M |
| 0,25-0,5 % | 1 | 15,35 M *(Pedri)* |
| **1-2 %** | **2** | **7,91 M** |
| **2-4 %** | **1** | **420.000** |
| **> 4 %** | **0** | **0** |

**Hoy el escaparate ofrece 420.000 € de material que pase el listón del 3 %, y
nada por encima del 4 %.** El cuello no es el capital, ni las fichas, ni el tope:
**es que no hay qué comprar.**

Eso explica por sí solo por qué Pepe lleva semanas sin fichar, mejor que
cualquier hipótesis sobre el filtro del once.

---

# BLOQUE 3 — Volumen contra margen

Con el escaparate real de hoy como restricción:

| Tramo | Rinde | En pérdida | n | % del capital colocable | **Al mes** |
|---|---:|---:|---:|---:|---:|
| **1-2 %** | 3,22 % | 7,4 % | 68 | **100 %** | **1.244.755** |
| 2-4 % | 5,61 % | 2,7 % | 37 | 16,8 % | 309.634 |
| > 4 % | 18,37 % | 2,7 % | 37 | **0 %** | **0** |

**Gana el volumen, y por cuatro veces.** El tramo `> 4 %` rinde casi seis veces
más por operación y da **cero**, porque hoy no hay ni un jugador ahí. Un tramo
que rinde el triple y donde no cabe un euro no rinde nada.

## Y aquí está el hallazgo que no esperaba

**El tramo `1-2 %` está apagado ahora mismo**, porque `hold_switch` usa su
mediana de bloque —**1,80 %**— y no llega al listón del 3 %.

Pero esa mediana **mezcla racha 1 y racha 2**:

```
1-2 % · racha 1 · horizonte 3   →   +3,22 %   (n=68, 7,4 % en pérdida)
1-2 % · racha 2 · horizonte 3   →   +1,80 %   (n=58, 10 % en pérdida)
                    mediana del bloque   1,80 %
```

**A racha 1 —la única que la doctrina compraría, "racha corta"— el tramo sí pasa
el listón.** Está apagado por una mediana que promedia una racha que no
compraríamos.

**No he tocado nada.** Es una propuesta y hay tres formas de leerla: que el
interruptor deba mirar la celda de racha 1, que el listón esté bien y el tramo
mal medido, o que promediar sea lo prudente con seis días de ventana. Decides tú.

**Y el 3 % queda confirmado por segunda vez en un sentido distinto:** no hace
falta bajarlo. Basta con que el interruptor mire la racha que se compra.

---

# BLOQUE 4 — La deuda de lunes a jueves

**Sí hay algo, y son dos cosas. Señaladas y sin tocar.**

**1. La caja se hace cero en rojo.** En `acquisition_budget.py`:

```python
cash_budget = int(max(balance, 0) * ACQUISITION_CASH_PERCENT)
```

Con saldo negativo, `max(balance, 0) = 0`. Lo único que queda es la deuda segura.

**2. Y la deuda segura no es el problema: la prioridad sí.** El ciclo ejecuta
**una acción por vuelta**, y la tabla dice:

```
EMERGENCY_SOLVENCY   1100     ← se activa con balance < 0
MARKET_LISTING_RENEW  690
ACCEPT_EXPIRY_URGENT  680
SPECULATION_BUY       400
```

**Setecientos puntos de diferencia.** En cuanto Pepe se pone en rojo, cada vuelta
del ciclo la gana recuperar solvencia, y **nunca llega a comprar**. Es
exactamente lo contrario de *"se puede ir en rojo de lunes a jueves"*.

*(Lo que NO es un problema: `debt_window_open = guaranteed and headroom > 0`. No
hay ninguna puerta de calendario; la puerta es "puedo recuperar antes del plazo".
Conviene saberlo antes de buscar un calendario que no existe.)*

Hay guardia con los dos números dentro: no exige que se arregle, exige que si
alguien lo arregla sea a propósito.

---

# BLOQUE 5 — Balón parado

**Ya está hecho, y no en esta rama.** Lo hice anoche en
`balon-parado/quien-tira-los-penaltis`, commit `682d65d`, **sin fusionar**.

Resumen para que no se pierda: Comuniate publica los veinte lanzadores gratis;
faltas y córners no existen en ninguna de las tres fuentes; y **el bono no
sobrevive a la medición** —contra el mejor delantero de su propio equipo, el
lanzador rinde −0,25—. Lo que sí se sostiene es el matiz del VÍDEO-2: **ser
lanzador cuesta casi el doble por punto y el valor está en el barato que los
tira** (De la Fuente 445.000 €/punto contra Lookman 2.974.545).

Como me pediste rama desde `main` y `main` no tiene esa rama, aquí no está. **Es
la regla cero del PLAN mordiendo otra vez:** hay dos ramas sin fusionar y esto es
lo que cuesta.

---

# Lo que no hice, y por qué

**No arreglé la narración de TENER** en el motivo del rechazo. Pediste la
medición delante antes de tocar la ruta de decisión, y aunque esto es narración,
pasa por donde pasa el dinero.

**No toqué el interruptor del tramo 1-2 %**, ni el listón del 3 %, ni la tabla de
prioridades, ni el `max(balance, 0)`. Los cuatro están señalados con su número.

**No modelé el mercado dentro de la calculadora.** El techo mensual asume que se
puede colocar todo el capital cada ciclo, y hoy no se puede ni de lejos. Está
dicho en el módulo y en este informe, pero el número sigue siendo un techo, no
una previsión. Modelarlo bien necesita medir cuántos jugadores aptos aparecen por
día durante varias semanas, y eso son datos que no tenemos.

**No compré, no vendí, no respondí ofertas, no encendí la rueda.**

---

**La frase para mañana:** la sospecha que abría el plan era mía y era falsa — el
filtro del once no mata la rueda; **de los doce rechazados, ninguno sube**. Lo
que sí la mata es que **hoy el escaparate ofrece 420.000 € de material aprovechable
y nada por encima del 4 %**, y que **en cuanto Pepe se pone en rojo la solvencia
gana a comprar por setecientos puntos de prioridad**, lo que hace inútil el
permiso de endeudarse entre semana. Y hay una llave pequeña con efecto grande:
**el tramo `1-2 %` rinde +3,22 % a racha 1 y está apagado por una mediana de
1,80 % que promedia una racha que no compraríamos** — ahí caben 1,24 M al mes, el
cuádruple que en el tramo bueno.
