# ENCARGO — EL BOLSILLO

**Fecha:** 2026-09-15
**Rama:** `bolsillo/de-donde-sale-el-dinero`
**Parte de:** `docs/resultado-rampa-2026-09-14.md`, donde la vía TENER quedó
encendida y bloqueada por el tope de 973.594 € por operación.

---

## Antes de nada: el retrotest está bien hecho

La tabla del 14/09 es el mejor trabajo de medición que se ha hecho en este
proyecto. Las celdas vacías marcadas como vacías, el corte de 30, el cruce con
lo medido antes, y sobre todo **no bajar el 3 % cuando era lo cómodo**. Nada de
lo que sigue lo contradice.

Pero antes de tocar ningún bolsillo hay un agujero que la propia tabla destapa
y que hay que tapar primero.

---

## BLOQUE 1 — El modelo está valorando rachas que nunca midió

De tu informe, la línea que lo dice todo:

> "todas las de racha > 7 días: **la racha máxima observable en 6 días es 5**"

Y los tres candidatos que se desbloquearían al subir el tope:

| Jugador | Ritmo | **Racha** |
|---|---:|---:|
| Roro Riquelme | 1,666 %/día | **50 días** |
| Amatucci | 1,098 %/día | **19 días** |
| Pedri | 0,305 %/día | **8 días** |

**Ninguna de esas rachas existe en el retrotest.** El tramo medido más largo es
"3-7 días", y ni siquiera llega a 7: llega a 5. Estamos aplicando a una racha de
50 días una curva calibrada sobre rachas de 1 a 5.

Y no es un detalle de precisión, porque la tabla dice que **la dirección importa
y va en contra**: con la misma tasa `> 1 %/día`, una racha de 1 día rinde
**+4,47 %** y una de 3-7 días rinde **+1,83 %**. La racha larga rinde *menos*.
Extrapolar 50 días desde una curva que solo llega a 5, en la dirección en que el
rendimiento cae, es la clase de error que este proyecto lleva un mes aprendiendo
a no cometer.

Dicho de otra forma incómoda: **los tres jugadores que el tope está bloqueando
son, según la propia medición, del tipo peor.** El tipo bueno —tasa alta con
racha corta— hoy solo lo cumple Gorosabel, y está tocado.

### Lo que hay que hacer

1. **`hold_value` no valora por encima del rango medido.** Si la racha del
   jugador supera la racha máxima observada en el retrotest, o bien se recorta
   al último tramo medido, o bien la vía se declara `SIN_RESPALDO` y no valora.
   Elige tú cuál, mídelo, y escribe por qué.
2. **Publica el rango de validez** junto al valor, en el objeto y en pantalla:
   "calibrado sobre rachas de 1 a 5 días; éste lleva 50". Que se vea que estamos
   fuera de la muestra.
3. Guardia `test_fuera_de_muestra_v1`: un jugador con racha por encima del máximo
   observado no puede recibir un `hold_value` mayor que el del último tramo
   medido.

**Esto va antes que el bolsillo**, porque si sale que Roro y Amatucci no
compensan una vez recortados al rango medido, el debate del tope se vuelve
teórico y nos hemos ahorrado meter medio patrimonio en el jugador equivocado.

---

## BLOQUE 2 — El número que falta

La tabla da mediana, p25, p75 y **porcentaje** en pérdida. No da **cuánto** se
pierde cuando se pierde. En la celda buena —`>1 %/día`, racha 1 día, m=3— el
5 % de las operaciones pierde, pero no sabemos si pierden un 1 % o un 20 %.

Sin ese número no se puede dimensionar ningún tope, porque un tope es
exactamente la respuesta a "¿cuánto puedo perder de una vez?".

Publica, para cada celda con muestra suficiente: **p5, mínimo, y la media de las
operaciones perdedoras**. Es un añadido de unas líneas a `hold_backtest.py`.

---

## BLOQUE 3 — De qué bolsillo sale, y por qué

Tu diagnóstico es correcto: el tope de 973.594 € es lo que tiene el dinero
parado, no el listón del 3 %. Pero antes de subir un intocable, mira de dónde
sale ese número.

```
bolsillo de especular  2.433.987 €  ×  40 %  =  973.594 €
bolsillo de fichar     5.350.683 €            sin usar
```

El tope es **un porcentaje de un bolsillo que ya es un porcentaje**. No es un
límite de riesgo pensado: es lo que sale de anidar dos fracciones. Y al lado hay
5.350.683 € reservados para mejoras del once que —medido ayer y anteayer— hoy no
existen: ningún objetivo compensa por la vía del once.

**La propuesta: que el bolsillo lo decida el efecto sobre el balance, no el
nombre de la vía.**

- Una compra que **ocupa una ficha vacía** es un fichaje a efectos de balance,
  aunque la tesis sea la rampa. Tenemos 8 fichas libres. Sale del bolsillo de
  fichar.
- Una compra que **rota** (entra uno, sale otro) es cartera. Sale del bolsillo
  de especular.

**Esto no rompe la regla que estableciste el 13/09** —bolsillo, listón y valor
de la misma vía—. Esa regla dice que los tres tienen que ser coherentes *entre
sí*: que no se justifique con la reventa una compra que cobra del bolsillo de
fichar y se examina con el listón del once. Aquí siguen siéndolo: el valor lo da
TENER, el listón es el de TENER (3 %), y el bolsillo lo da el hecho contable de
que la ficha estaba vacía. **Si crees que sí la rompe, no lo hagas y explícalo:
esa regla vale más que este encargo.**

Y con esto **no hay que tocar `MAX_SINGLE_SPECULATION_PERCENT`**. Se queda donde
está, con su lección de Soler intacta.

---

## BLOQUE 4 — El tope, deducido en vez de decretado

El tope por operación de la vía TENER no debe ser un porcentaje de nada. Debe
ser el mayor importe que cumpla las tres condiciones a la vez:

1. **Que la peor pérdida medida** de su celda (bloque 2) siga dejando el reloj de
   solvencia en positivo a T−6 h. La maquinaria ya existe: úsala, no la
   reimplementes.
2. **Que no supere el X % del patrimonio** en una sola posición que no juega en
   el once. Deriva X de la liga como se hizo con la guardia de concentración, no
   a ojo.
3. **Una sola posición TENER abierta a la vez**, hasta que el libro de pujas
   tenga operaciones reales que confirmen el retrotest.

Publica el número que salga, con la cuenta al lado, y una guardia que lo
recalcule en vez de dejarlo escrito a mano.

### La escalera, escrita antes de subirla

142 operaciones de **una sola semana de agosto** son evidencia decente y fina a
la vez. Agosto es la semana rara del año: se acaba de cerrar el mercado y todos
los precios se están recolocando. Que septiembre se comporte igual es una
suposición razonable, y sigue siendo una suposición.

Así que el tope sube **con evidencia viva, según una regla escrita hoy**:

- cada operación TENER se registra en el libro de pujas con su rendimiento
  realizado;
- tras N operaciones cerradas cuya mediana se parezca a la del retrotest dentro
  de un margen que fijes tú, el tope sube un escalón;
- si no se parece, baja. Y si el tramo bueno deja de rendir el 3 %, la vía se
  apaga sola, que eso ya lo dejaste puesto.

Fija N y el margen con un criterio, no con un número redondo, y escríbelos en el
informe.

---

## BLOQUE 5 — Que el almacén deje de ser de seis días

El retrotest tiene 6 días porque el almacén de precios guarda 6 días. Con tres
semanas tendríamos horizontes de 5, 7 y 10 y rachas de verdad, y las celdas
vacías se llenarían solas.

Averigua por qué son 6 —retención configurada, poda, o que empezó ahí— y si es
retención, súbela a **60 días**. Mira el tamaño en disco antes y dilo: si son
megabytes, es la mejora más barata del mes; si son cientos, se busca otra forma.

Y deja `hold_backtest` preparado para volver a correr sin tocar una línea cuando
haya más días, como ya escribiste.

---

## Reglas de la casa

1. Rama `bolsillo/de-donde-sale-el-dinero`. `main` no se toca.
2. Verja encadenada, sin excepciones:

   ```powershell
   python scripts/run_validation_gate.py
   if ($LASTEXITCODE -eq 0) {
       git add -A
       git commit -m "bolsillo: de donde sale el dinero"
   } else {
       git reset --hard origin/main
       Write-Host "VERJA EN ROJO - nada que subir"
   }
   ```

   Tú no empujas.
3. `git status` antes de commitear, y en el informe qué entra. Ayer lo hiciste.
4. Mide contra `diagnostico/status.json`.
5. No toques `.github/workflows/bordalas-live.yml`.
6. **`MAX_SINGLE_SPECULATION_PERCENT` sigue siendo intocable.** Este encargo está
   escrito precisamente para no tener que tocarlo.
7. Si la medición contradice este encargo, gana la medición. El bloque 1 puede
   perfectamente dejar sin objeto los bloques 3 y 4, y sería un buen resultado.

---

## Informe

- si Roro, Amatucci y Pedri siguen compensando una vez recortados al rango de
  racha medido;
- p5, mínimo y media de las perdedoras, por celda;
- el tope deducido, con la cuenta;
- la escalera: N, el margen, y por qué esos;
- días de histórico antes y después, y cuánto ocupa;
- qué compraría el primer ciclo: nombres, importes, bolsillo, saldo;
- lo que no hiciste y por qué.
