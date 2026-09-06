# ENCARGO — QUE GIRE

**Fecha:** 2026-09-24
**Rama:** `gire/quitar-los-tres-tapones`
**Referencia:** `docs/resultado-rueda-2026-09-23.md`, `docs/PLAN.md`,
`docs/DOCTRINA.md` v1.5

---

## Lo de anoche

**Mi sospecha era falsa y la construí sobre una etiqueta.** El bloque 1 del
PLAN v2 —"el filtro del once mata la rueda"— nació de leer `SIN_VALOR` como "no
mejora el once". Los doce estaban evaluados por todas las vías y mueren porque
**ocho caen y cuatro están planos**. La rueda los rechaza bien. Corregido en el
plan.

Y debajo salieron **tres tapones reales**, que es lo que hay que quitar. Ninguno
es un umbral: los tres son el mismo tipo de fallo, mirar el sitio equivocado.

Y el que manda sobre todos: **hoy no hay qué comprar.** De los veinte del
escaparate, once cayendo, uno en el tramo 2-4 % y ninguno por encima del 4 %.
El cuello no es el capital, ni las fichas, ni el tope.

---

## BLOQUE 0 — Antes de nada: ¿qué se puede comprar de verdad?

Esta pregunta decide el valor de todo lo demás y no la hemos hecho nunca.

La rueda vale entre **718.629 € y 1.555.885 € al mes** según tu propio cálculo,
pero solo si hay a quién comprar. Hoy no lo hay. Así que:

**¿El universo comprable es únicamente los ~20 que el Computer saca cada
mañana, o se puede pujar por cualquiera de los 521?**

Lo que apunta a lo primero: `outside_computer_market: 0`, y en 67 horas de tablón
hubo 19 ventas al Computer y **una sola** entre managers, que era nuestra.

- Si son solo los ~20 diarios: en una semana pasan ~140 jugadores distintos por
  el escaparate. **Mide cuántos de ésos venían subiendo más del 1 % diario.** Ése
  es el caudal real de la rueda, y puede ser bastante menor que el techo.
- Si se puede pujar por cualquiera: entonces el ranking de los 521 no es un
  adorno, es la pieza que multiplica la rueda, y sube al primer puesto del plan.

**Solo medir y contestar.** De aquí sale si el próximo mes se dedica a la rueda o
a otra cosa.

---

## BLOQUE 1 — El interruptor mira la celda equivocada

El hallazgo más rentable de anoche, y es casi de una línea:

```
tramo 1-2 %/dia   mediana de bloque  1,80 %  ->  APAGADO
                  pero racha 1       3,22 %  ->  pasaria el liston
```

La mediana del bloque promedia racha 1 con racha 2, y la doctrina **solo compra
racha corta**. El interruptor está juzgando la vía con una celda que incluye
compras que nunca haríamos.

Y ese tramo es el que importa: **coloca el 100 % del capital** y vale
**1.244.755 € al mes**, contra los 309.634 € del tramo 2-4 %.

- Que el interruptor mire **la celda que de verdad se compra** (tasa × racha),
  no la mediana del bloque.
- **El 3 % no se toca.** Queda confirmado por segunda vez; lo que cambia es
  contra qué número se compara.
- Guardia con este caso exacto dentro: bloque 1,80 %, racha 1 a 3,22 %, y la vía
  encendida por la segunda, no apagada por la primera.
- Publica qué tramos quedan encendidos y con qué celda, en pantalla.

---

## BLOQUE 2 — La deuda: los dos que la matan

Tu hallazgo, y explica por sí solo por qué el permiso de endeudarse lleva
semanas sin usarse:

```
1)  cash_budget = max(balance, 0)      en rojo, la caja vale cero
2)  EMERGENCY_SOLVENCY  1100
    SPECULATION_BUY      400            y una accion por ciclo
```

En cuanto Pepe entra en rojo, **cada vuelta la gana recuperar solvencia** y no
vuelve a comprar. Es exactamente lo contrario de "en rojo de lunes a jueves,
verde el viernes".

**Cómo arreglarlo, y esto importa más que el arreglo:**

**No bajes `EMERGENCY_SOLVENCY`.** Esa prioridad está bien puesta *cuando de
verdad hay una emergencia*. El fallo no es el número: es que **se dispara por el
signo del saldo en vez de por el plazo**. Ya tenemos el reloj de solvencia con su
T−6 h; la emergencia debe mandar cuando el reloj aprieta, no cuando el saldo es
negativo un martes.

- Que la prioridad de emergencia se decida por **horas hasta T−6 h y si la venta
  disponible cubre el agujero**, no por `balance < 0`.
- Que `cash_budget` cuente la deuda autorizada disponible en vez de recortar a
  cero, **dentro del margen que ya existe** —`MAX_SAFE_DEBT` no se sube—.
- Guardia con los dos casos: martes en rojo con holgura → se puede comprar;
  viernes a T−6 h en rojo → manda la solvencia y no se compra nada.

Si al mirarlo ves que esto puede dejar a Pepe en rojo un viernes, **para y
dímelo**. Es la única regla que protege dinero de verdad y prefiero la rueda
apagada a una jornada sin puntuar.

---

## BLOQUE 3 — El motivo que no nombra a TENER

Defecto de una línea que señalaste: el texto del rechazo narra once, especulación
y reventa, **y no TENER** — que es justo la vía que sostiene la rueda. Con la
regla 17 (cada decisión cita su regla), un rechazo que no cuenta la vía que
decide es un rechazo que miente por omisión.

---

## BLOQUE 4 — Fusionar lo que está hecho

**El balón parado está terminado desde anteanoche** en
`balon-parado/quien-tira-los-penaltis` (`682d65d`) y sin fusionar. Es la regla
cero del plan mordiendo por tercera vez.

Deja escrito en el informe, en un sitio visible, **qué ramas hay sin fusionar y
en qué orden hay que hacerlo** para que el dueño lo ejecute de una vez. No las
fusiones tú.

---

## Dos cosas menores

**El commit `7982710` era mío**, del dueño a través del puente: son tres
documentos (`PLAN.md` v2 y este encargo). Igual que el `1459222` del 16/09. Deja
de investigarlo, no hay misterio: cuando aparezca un commit solo de `docs/`, es
de esta parte.

**`git reset --hard origin/main` en tu rama se llevaría por delante esos
documentos.** Si la verja sale roja, resetea al commit anterior de tu rama, no a
`origin/main`.

---

## Reglas de la casa

1. Rama `gire/quitar-los-tres-tapones`, desde donde estés encadenado. `main` no
   se toca.
2. Verja encadenada, sin excepciones:

   ```powershell
   python scripts/run_validation_gate.py
   if ($LASTEXITCODE -eq 0) {
       git add -A
       git commit -m "gire: quitar los tres tapones"
   } else {
       Write-Host "VERJA EN ROJO - nada que subir"
   }
   ```

   Tú no empujas.
3. **Ningún umbral se mueve:** ni el 3 %, ni `MAX_SAFE_DEBT`, ni
   `MAX_SINGLE_SPECULATION_PERCENT`, ni `EMERGENCY_SOLVENCY`. Lo que cambia es
   **qué mira cada uno**, no cuánto vale.
4. No vendas, no compres, no respondas ofertas.
5. Ninguna guardia nueva lee `data/`. Ninguna función nueva cambia de forma según
   los datos.
6. `git status` antes de commitear, y en el informe qué entra.
7. No toques el workflow.
8. Termina cada commit con `Autor-real: Claude Code (VS Code)`.
9. Si la medición contradice el encargo, gana la medición. Anoche la tuya tumbó
   el bloque 1 del plan entero, y estuvo bien hecho.

---

## Informe

- **¿se puede pujar por cualquiera de los 521, o solo por los ~20 del día?** Y si
  es lo segundo, cuántos de los ~140 semanales venían subiendo más del 1 %;
- qué celda mira ahora el interruptor y qué tramos quedan encendidos;
- si la deuda entre semana ya es posible, con los dos casos de la guardia;
- las ramas sin fusionar y en qué orden;
- lo que no hiciste y por qué.
