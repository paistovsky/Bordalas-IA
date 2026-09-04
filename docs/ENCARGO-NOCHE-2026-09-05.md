# ENCARGO — noche del 04→05/09/2026 (segunda tanda)

Para Claude Code en `C:\Users\PC\Bordalas-IA-clean`. El dueño duerme.
Trabaja solo. No preguntes nada que puedas verificar tú.

Antes de nada, lee `docs/auditoria-2026-09-04.md` y
`docs/resultado-2026-09-04.md`. La primera tanda ya está hecha.

---

## LA REGLA QUE MANDA ESTA NOCHE

**Nada de lo que construyas puede cambiar una decisión.**

Todo lo nuevo se calcula **en sombra**: al lado de lo que ya hay, se
publica en el dashboard, y **no manda**. El motor viejo sigue decidiendo
exactamente igual que hoy.

Es un patrón que este repo ya usa y llama "FASE OBSERVADOR". Búscalo en
`autopilot.py:3443` y en `source_accuracy_ledger.py` para copiar el
estilo.

Prohibido esta noche, sin excepción:
- Tocar umbrales, presupuestos, topes o porcentajes.
- Tocar `rival_bid_model.py`, `speculation_engine.py`,
  `acquisition_budget.py` o cualquier ruta que escriba en Biwenger.
- Cambiar qué compra, qué vende o cuánto puja.
- `main`. Trabaja en rama.

Si una tarea te obliga a romper esto, **déjala sin hacer** y escríbelo.

Puerta en verde al terminar cada tarea:

```powershell
python scripts\run_validation_gate.py
```

Cada cosa nueva, con su guardia, al estilo de la casa
(`src/analysis/test_bid_outcome_ledger_v1.py` como plantilla) y su línea
en `.github/workflows/bordalas-live.yml`.

Rama:

```
git checkout -b noche/2026-09-05
```

---

## 1. Cerrar la tarea 2 (30 min)

`candidate_starter_lookup.py` lee el tablero de disco y **nunca lo
rechaza por jornada**. Es la otra mitad de lo que se arregló anoche en el
proveedor.

Ciérralo: si el tablero en disco es de otra jornada, no se sirve.

**Pero con una condición, y es la parte importante:** cuando eso pase,
**tiene que verse en el dashboard**. Un texto claro tipo *"El tablero es
de la jornada 3 y estamos en la 4: sin pronósticos hasta que se
refresque."* Fallar cerrado está bien; fallar en silencio, no — el dueño
se pasaría días preguntándose por qué Pepe está quieto.

*Hecho cuando:* un tablero de otra jornada no alimenta nada, el motivo
sale en pantalla, y hay guardia.

---

## 2. Que se vea lo que ya se publica (frontend)

El backend publica tres cosas que la pantalla no enseña. El dueño lleva
semanas pidiendo "ver lo que ve Pepe".

**a) `bid_outcomes`** — el libro de pujas. Puestas, ganadas, perdidas,
por cuánto nos ganan (mediana y peor caso). Hoy sale `placed: 0` porque
solo registra las pujas que pone Pepe; **enséñalo igual**, con su "sin
datos todavía" honesto.

**b) `rival_squads`** — los siete managers con su plantilla. Desde anoche
traen jugadores de verdad. Interesa ver el valor de plantilla de cada
uno contra el nuestro, que es la brecha real (47,7 M contra 69 M).

**c) El tope por operación** — `single_operation_limit`, arreglado anoche
en el lector. Que se vea junto al presupuesto.

El código está en `dashboard-v8/` (React + Vite). **Compila** para
comprobar que no rompes nada:

```
cd dashboard-v8 ; npm run build
```

**NO despliegues.** El despliegue lo hace el dueño o el workflow. Tu
trabajo acaba en que compile y el diff esté limpio.

*Hecho cuando:* las tres cosas se ven, el build pasa, y ninguna página
existente se rompe.

---

## 3. El módulo de carrera — LO IMPORTANTE

Pepe **no sabe que va cuarto**. Nada en el código lee la clasificación
para decidir. Pujaría igual siendo primero con veinte de ventaja.

Crea `src/analysis/race_state.py` que calcule, y **solo calcule**:

- Puesto actual y puntos.
- Puntos del líder y distancia.
- Jornadas jugadas y **restantes** (la temporada son 38).
- **Ritmo necesario**: distancia ÷ jornadas restantes = cuántos puntos
  por jornada hay que sacarle al líder.
- Valor de plantilla nuestro y de cada rival, y la brecha.
- Un nivel de urgencia derivado de todo eso, en una escala clara y
  documentada.

Los datos están en `status.json`: `rival_squads.managers` trae `rank`,
`points`, `team_value` de los siete. El calendario, en
`data/calendar/laliga_calendar.json`.

**No lo conectes a ninguna decisión.** Publícalo en el dashboard como un
bloque propio: *"Vas 4º, a 13 puntos, quedan 34 jornadas: necesitas
sacarle 0,38 por jornada. Tu plantilla vale 21,7 M menos que la del
líder."*

*Hecho cuando:* el bloque sale en pantalla con números correctos, hay
guardia que verifica el cálculo con datos de ejemplo, y **ningún motor
lo lee**.

---

## 4. La valoración a horizonte de temporada, en sombra

Hoy todo se valora a tres días (`DEFAULT_SPECULATION_HORIZON = 3`) o a un
ciclo. Un jugador que da 6 puntos por jornada durante 30 jornadas vale
180 puntos; lo que valga su reventa el jueves es otra cosa.

Añade un cálculo **paralelo** que valore a temporada:

```
valor_temporada = puntos_esperados_por_jornada × jornadas_restantes
```

Con los ajustes que ya existen y son buenos: probabilidad de titular,
jerarquía, disponibilidad, dificultad de calendario.

**Publícalo junto al valor actual en cada candidato del tablero**, como
un campo nuevo. Que se puedan comparar los dos lado a lado en la Sala de
Operaciones: *"Pepe hoy lo valora en X; a horizonte de temporada valdría
Y."*

**No sustituyas nada. No cambies ninguna decisión.** Es una segunda
opinión escrita al margen.

*Hecho cuando:* cada candidato lleva las dos valoraciones, se ven en
pantalla, y hay guardia. El motor de decisión sigue usando **solo** la
vieja.

---

## 5. La vía de "ampliar plantilla", también en sombra

Hoy a cada candidato solo se le compara con **un** jugador: el titular
más flojo de su posición (`acquisition_valuation.py:352-358`). No existe
"fichar para llenar un hueco". Pepe tiene 14 fichas; los de arriba, 17.

Calcula —**sin ejecutar**— qué ficharía si pudiera llenar los huecos:
cuántas fichas libres hay y qué candidatos entrarían por ellas, con su
valoración a temporada del punto 4.

Publícalo como una lista aparte: *"Con 3 fichas libres, estos serían los
candidatos."*

*Hecho cuando:* la lista sale en pantalla, y **no se ha tocado**
`acquisition_valuation.py` ni ninguna ruta de decisión.

---

## Cómo dejarlo

1. Rama `noche/2026-09-05` subida, **puerta en verde**, `main` intacto.
2. Un commit por tarea, con mensaje que diga qué y por qué.
3. `docs/resultado-noche-2026-09-05.md` con: qué se hizo, qué se quedó
   fuera y por qué, y **lo que te sorprendió** — ese apartado ha sido el
   más valioso de la primera tanda.
4. En ese resumen, una sección **"qué habría hecho distinto el cerebro
   nuevo"**: con los datos de hoy, ¿en qué difiere la valoración a
   temporada de la actual? ¿Habría fichado a alguien que hoy se rechaza?
   Eso es lo primero que va a mirar el dueño por la mañana.
5. Si algo te bloquea, **no adivines**. Déjalo y escríbelo. Es una liga
   con dinero y un fallo silencioso cuesta más que una tarea a medias.

Y si terminas todo y sobra noche: **no empieces nada nuevo**. Repasa lo
hecho, refuerza guardias, y deja el resumen mejor.
