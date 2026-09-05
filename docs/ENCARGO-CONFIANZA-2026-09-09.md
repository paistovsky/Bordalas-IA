# ENCARGO — cada apuesta con su confianza

Noche del 08/09/2026. Para Claude Code en `C:\Users\PC\Bordalas-IA-clean`.
El dueño duerme. Trabaja solo.

Lee antes `docs/resultado-freno-acelerador-2026-09-08.md`. Este encargo
sale de lo que encontraste anoche y decidiste, con buen criterio, no
tocar de madrugada.

---

## EL HALLAZGO

El acelerador funciona y no se nota, porque una penalización lo anula:

```
Bardeli, +4,62 %/dia  ->  speculation_value proyecta +138.628 €
                          y lo multiplica por confidence = 0,4125
                          que mide la certeza sobre sus PUNTOS
```

Es un error de categoría: se está descontando una apuesta de **precio**
con la incertidumbre de los **puntos**.

Y el remate, que es lo que decide todo:

```
speculation_value      lleva confianza (la equivocada)
computer_resale_value  no lleva NINGUNA
```

La vía que **mira** al jugador va penalizada; la que **no lo mira** va
limpia. Por eso gana en 21 de 22 candidatos, y por eso todo vuelve a
salir plano: esa vía es igual para todos por construcción.

---

## LO QUE HAY QUE HACER

**No es quitar la penalización. Es que cada vía lleve la confianza de lo
que de verdad está apostando.**

| vía | a qué apuesta | qué confianza le corresponde |
|---|---|---|
| `xi_upgrade_value` | a que puntúa | la de los puntos — la de ahora, se queda igual |
| `speculation_value` | a que el precio sube | la de la **racha** |
| `computer_resale_value` | a que el Computer recompra caro | la del **premium medido** |

**La confianza de la racha** ya existe en el informe del ojeador:
`trend_days` (días consecutivos en la misma dirección) y cuántas fuentes
confirman el movimiento. Una racha de seis días confirmada por tres
fuentes es más fiable que un día suelto que ve una sola. Documenta la
forma que le des y por qué.

**La confianza del premium** también está medida: el Computer paga por
encima con `positive_ratio` de **0,778** sobre 90 ventas con precio
(`acquisition.computer_premium` en `status.json`). Esa vía **falla una de
cada cinco veces** y hoy no lleva descuento ninguno. Usa el ratio medido
y su tamaño de muestra; no inventes un número.

---

## LA REGLA QUE MANDA: TODO EN SOMBRA

Esto cambia qué vía gana en cada candidato, y por tanto qué compra Pepe.
**No lo enciendas.**

Calcula las dos valoraciones —la de hoy y la nueva— y publícalas juntas.
El motor sigue decidiendo con la vieja.

En el dashboard, por candidato: qué vía gana con cada esquema, cuánto
vale con cada uno, y **qué cambiaría**. El dueño tiene que poder mirar la
lista y decir "esto sí, esto no" antes de que se mueva un euro.

Rama `confianza/2026-09-09`. Puerta en verde. `main` intacto. Cada pieza
con su guardia.

---

## LO QUE NO SE TOCA

- Umbrales, presupuestos, topes de operación, guardarraíles de posición
  y solvencia.
- `MIN_SPECULATION_YIELD` y `MIN_SPECULATION_EXPECTED_VALUE`: siguen
  fuera de la mesa. Hubo un intento el 03/09, revertido en `9bf60c4`.
- La vía del Computer **no se frena por falta de racha**. Anoche saltó
  `test_reventa_al_computer_v1` por eso y tenía razón: esa vía no apuesta
  a que el jugador suba. Aquí solo se le añade el descuento que le
  corresponde, no un veto.

**Y si una guardia se pone en rojo, léela antes de tocarla.** Anoche te
pararon dos y las dos tenían razón. Es el mejor indicador de este repo.

---

## Cómo dejarlo

1. Rama subida, puerta en verde, nada desplegado.
2. `docs/resultado-confianza-2026-09-09.md`, empezando por **la lista de
   lo que cambiaría**: qué candidatos cambian de vía, cuáles suben o
   bajan de valor y cuánto. Con nombres y cifras.
3. Y una pregunta contestada explícitamente: **¿sigue ganando la vía del
   Computer en 21 de 22, o se reparte?** Eso es el termómetro de si el
   arreglo hace lo que esperamos.
4. Lo que te sorprendió.
5. Si algo te bloquea, no adivines: déjalo y escríbelo.
