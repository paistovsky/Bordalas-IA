# ENCARGO — poner el dinero a trabajar

Noche del 09/09/2026. Para Claude Code en `C:\Users\PC\Bordalas-IA-clean`.
El dueño duerme. Trabaja solo.

Lee antes `docs/auditoria-2026-09-04.md` y
`docs/resultado-confianza-2026-09-09.md`.

---

## POR QUÉ

Siete noches arreglando cómo decide Pepe. Ninguna ha tocado lo que de
verdad le separa del líder:

```
3.400.000 €    parados en caja
3              fichas de plantilla vacias (14 de 17)
21.700.000 €   menos de plantilla que Pollo17
8.561.940 €    en el bolsillo de FICHAR, sin usar
```

Y se midió de dónde sale el dinero en esta liga: **no de comerciar.**
Pollo lleva −27 M en ventas menos compras. Su patrimonio sale de tener
una plantilla grande que se revaloriza. Cada euro parado revaloriza
cero, y cada ficha vacía no puntúa nada.

---

## LA REGLA MÁS IMPORTANTE DE ESTE ENCARGO

**No subas ningún tope, ningún porcentaje, ningún presupuesto.**

El dinero no está parado porque los límites sean estrechos. Está parado
porque **la fontanería no llega hasta él**. Arregla la fontanería y mira
qué pasa. Si después de esto sigue habiendo caja ociosa, entonces se
hablará de límites — con el dueño delante.

Concretamente, siguen intocables: `MAX_SPECULATION_BUDGET_PERCENT`,
`MAX_SINGLE_SPECULATION_PERCENT`, `MAX_DEBT_SPECULATION_PERCENT`,
`MAX_SAFE_DEBT`, `MIN_SPECULATION_YIELD`,
`MIN_SPECULATION_EXPECTED_VALUE`.

**Y no se toca la deuda.** Luismi va tercero con 10 M en rojo; ésa es
otra estrategia y otra conversación. Aquí solo se despliega caja propia
y se llenan huecos.

---

## 1. El `intent` por tipo de operación, no por euros

`src/analysis/acquisition_valuation.py:593`

```python
mejor = max(opciones, key=lambda o: safe_int(o.get("value")))
return {"intent": mejor.get("intent"), ...}
```

Se calculan las tres vías y **gana la que dé más euros**. El `intent` no
dice qué clase de operación es: dice cuál salió más gorda. Y de ese
`intent` cuelga **qué bolsillo se usa** (`acquisition_board.py:575`,
`budget_for_intent`).

Consecuencia medida: los 22 candidatos salían con `intent: SPECULATION`
y se comparaban contra los 3,5 M de especular, **mientras los 8,5 M de
fichar seguían intactos**. Cinco se rechazaron por "supera presupuesto"
teniendo dinero de sobra al lado.

Enruta por **clase de operación**: si la vía que gana es una mejora del
once o un fichaje, el bolsillo es el de fichar. Si es reventa o
tendencia, el de especular.

Ojo con `_sin_valor` (`:654`), que pone `intent: None` y hace que
`budget_for_intent` devuelva el **mínimo** de los dos bolsillos.

---

## 2. La vía que hoy no existe: llenar un hueco

`acquisition_valuation.py:341-373`: `candidatos_a_salir` es una lista de
**un solo elemento** — el titular más flojo de esa posición. No hay
forma de fichar sin sustituir a nadie.

Pepe tiene 14 fichas de 17. **Tres huecos que no puntúan.**

Añade la vía: cuando hay ficha libre, un candidato se valora **contra el
hueco**, no contra un titular. Sin veto de "no mejora el once", porque
no está desplazando a nadie — pero **con** los vetos que sí aplican:
jerarquía mínima, disponibilidad, y pronóstico de titularidad.

`roster_expansion_shadow.py` ya calcula esto en sombra desde el 05/09.
Reutilízalo en vez de reescribirlo.

Cuidado con lo que avisaste el 05/09: de 18 fichables, los dos únicos
baratos por punto eran suplentes. Una vía de ampliación sin filtro
empuja al bucle de las catorce defensas. El filtro de jerarquía y
titularidad es lo que lo corta.

**Verifica el tope real de plantilla de Biwenger** antes de asumir 17.
Si no puedes, usa el máximo observado entre los rivales y dilo.

---

## 3. El guardarraíl que falta, y ahora hace falta de verdad

No existe ningún tope de concentración. Hoy:

```
Yamal = 21.120.000 de 47.720.000  ->  44 % de la plantilla en un jugador
```

Si Pepe empieza a comprar, esto importa más, no menos. Dos topes nuevos,
en la familia de `position_guardrail`:

- **Por jugador**: porcentaje máximo del valor de plantilla en un solo
  nombre.
- **Por equipo**: número máximo de jugadores del mismo club. Comparten
  calendario: puntúan juntos y se hunden juntos.

Como el resto de guardarraíles de la casa: **avisan y acotan, no
prohíben en silencio**. Y el motivo, en pantalla.

Elige los valores tú y **justifícalos con los datos** — mira qué
concentración tienen Pollo, Luismi y Mex, que son los que van por
delante. No inventes un número redondo.

Esto cierra por fin la lección de Soler del 16/08: era un problema de
concentración y hasta hoy no lo cubría nadie.

---

## 4. En sombra, con interruptor

Igual que las siete noches anteriores: calcula, publica, **no decidas**.

Pero esta vez deja además **un interruptor único y documentado** —una
constante o una variable de entorno, en un solo sitio— para que el dueño
pueda encenderlo por la mañana después de leer la lista. Que se vea
claro en el resumen cómo se enciende y cómo se apaga.

**La lista es el entregable principal:** con el dinero y las fichas de
hoy, a quién ficharía, por cuánto, de qué bolsillo, y por qué. Con
nombres. Eso es lo que va a mirar antes de darle al interruptor.

---

## Cómo dejarlo

1. Rama `despliegue/2026-09-10`, puerta en verde, `main` intacto, nada
   desplegado.
2. `docs/resultado-despliegue-2026-09-10.md`, empezando por la lista.
3. Y contesta esto explícitamente: **¿cuánto capital quedaría trabajando
   y cuánto seguiría parado?** Hoy son 3,4 M parados y 8,5 M sin tocar.
4. Lo que te sorprendió.
5. Si una guardia se pone en rojo, **léela antes de tocarla**. Te han
   parado tres veces esta semana y las tres tenían razón.
