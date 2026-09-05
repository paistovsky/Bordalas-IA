# ENCARGO — freno y acelerador

Noche del 07/09/2026. Para Claude Code en `C:\Users\PC\Bordalas-IA-clean`.
El dueño duerme. Trabaja solo.

**Este es el primer encargo de la semana que cambia lo que Pepe compra
con dinero de verdad.** Los seis anteriores fueron medir, limpiar y
construir en sombra. Trabaja en consecuencia.

Lee antes `docs/resultado-divergencia-2026-09-07.md`, que es de donde
sale todo esto.

---

## LO QUE SE MIDIÓ

```
r = +0,90 entre el cambio de precio de hoy y el de mañana
el que subió ayer sube hoy el 85,1 %
el que bajó ayer baja hoy el 90,7 %
de los que bajaron, solo el 0,5 % bate al mercado
```

Y el fallo concreto:

```
ganancia esperada = precio × tasa fija
André Almeida subió 17 % → 0,17 %
Nico Guillén  bajó   2 % → 0,17 %
```

**El modelo tiene la forma correcta.** Proyectar el ritmo de ayer es
justo lo que corresponde con r=+0,90. Lo que falla es que la entrada es
una constante. No hay que rediseñar el motor: hay que darle el número
bueno.

---

## LAS CUATRO PIEZAS

Las cuatro salen de la **misma** medición. No son cuatro ideas: son una
leída en cuatro direcciones.

### 1. El acelerador — la entrada real

Sustituir la tasa fija por el **ritmo observado** del jugador, que ya
recoge el ojeador (`scout_report.json`: `magnitude_percent`,
`magnitude_eur`, `trend_days`).

Si no hay dato del ojeador para ese jugador, **no inventes una tasa**:
que la operación no se valore como especulación, y que se diga por qué.
Volver a la constante sería reintroducir el fallo con otro nombre.

### 2. El freno — no comprar cuchillos cayendo

Un jugador cuyo precio viene bajando **no se compra como especulación**.
Con un 0,5 % de aciertos, no hay lectura de los datos en la que eso sea
buena idea.

Ojo: esto es el veto **de la vía especulativa**. Si un jugador que cae
mejora el once por razones de fútbol, esa es otra vía y no la toca este
encargo.

### 3. El freno de mano — la regla de salida

La misma medición dice que el que baja sigue bajando. Así que: **una
posición especulativa que se gira, se vende.** No hay que adivinar
cuándo acaba una racha; basta con reaccionar el día que se gira.

Esto es lo que hace aceptable el acelerador. Sin regla de salida,
comprar rachas es comprar techos tarde o temprano.

### 4. El aviso — rachas sin gasolina

Una racha de subidas **con la demanda desplomada** no se compra.
Sangaré y Lookman llevan siete días subiendo con la demanda hundida: es
el patrón de una racha agotándose.

La divergencia no sirve para entrar. Sirve para **no** entrar.

---

## LO QUE NO SE TOCA

**No bajes `MIN_SPECULATION_YIELD` ni `MIN_SPECULATION_EXPECTED_VALUE`.**
Bloqueaban todo porque la entrada era una constante del 0,22 %. Con el
ritmo real, un jugador que subió un 17 % pasa el 3 % de sobra. El umbral
no estaba mal: medía un número inventado. **Arregla la entrada y mira
qué pasa antes de tocar el listón.**

Hubo un intento de bajarlos el 03/09 y se revirtió en `9bf60c4`. No lo
repitas.

Tampoco se tocan presupuestos, topes de operación ni guardarraíles de
posición y solvencia. Todos siguen mandando por encima de esto.

---

## EL TEST DE SOLER — LÉELO ANTES DE TOCARLO

`test_la_especulacion_de_soler_ya_no_se_puja` puede ponerse en rojo con
este cambio. **No lo ajustes sin entenderlo.** Ya casi se borra una vez
por comodidad.

Lo que guarda: el 16/08 se pujó por Soler a 5.950.000 con un margen
finísimo que **inmovilizaba el 81 % del presupuesto**. La lección es de
**concentración**, no de rendimiento — el test usa el umbral de
rendimiento solo porque prueba `optimal_bid` aislado, y esa función no
ve el presupuesto.

En producción, una operación de 5,95 M contra un tope por operación de
~1,4 M se cae por presupuesto, no por rendimiento. Si el test se pone en
rojo, **verifica primero que la concentración lo sigue bloqueando** y
recoloca el test sobre el mecanismo que de verdad lo protege. Y déjalo
escrito.

---

## CÓMO SE ENTREGA — importante

Rama `freno-acelerador/2026-09-08`. Puerta en verde. Cada pieza con su
guardia. `main` intacto.

Y además, porque esto sí mueve dinero:

**Publica la comparación.** En el dashboard, para cada candidato: lo que
decidía Pepe antes y lo que decide ahora, con el motivo. El dueño tiene
que poder ver de un vistazo qué cambia antes de que se gaste un euro.

**Escribe la lista de la primera vez.** En el resumen, qué habría
comprado hoy con las reglas nuevas y qué no, con nombres y cifras. Eso
es lo primero que va a mirar.

**Y el libro de pujas ya está montado** (`bid_outcome_ledger`): asegúrate
de que estas operaciones quedan apuntadas. Es la única forma de saber en
una semana si esto funciona.

---

## Cómo dejarlo

1. Rama subida, puerta en verde, nada desplegado.
2. `docs/resultado-freno-acelerador-2026-09-08.md`, empezando por la
   lista de la primera vez.
3. Lo que te sorprendió.
4. Si algo te bloquea, no adivines: déjalo y escríbelo. Esta vez menos
   que nunca.
