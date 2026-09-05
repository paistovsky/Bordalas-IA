# ENCARGO — tarde y noche del 05/09/2026

Para Claude Code en `C:\Users\PC\Bordalas-IA-clean`. El dueño está fuera
toda la tarde y la noche. Trabaja solo.

**Mide siempre contra `diagnostico/status.json`** (foto de producción).
`data/` del repo es de agosto y ya provocó un diagnóstico falso.

Rama `tarde-noche/2026-09-05`. Puerta en verde. `main` intacto. El push
lo da el dueño. Cada pieza con su guardia.

**Nada que decida con dinero.** No se tocan umbrales, presupuestos,
topes ni `DEPLOYMENT_ENABLED`, que sigue apagado esperando el examen del
día 11.

---

## 1. El panel "La Carrera" — el dueño dice que no le gusta

Textual: *"me ha metido un cuadro 'La Carrera' que no me gusta nada. Al
menos, que lo baje abajo, que está descuadrado."*

Dos cosas, y la segunda importa más:

**Bájalo al final de INICIO.** Es contexto, no lo primero que uno mira
al abrir el panel.

**Y arregla que esté descuadrado.** Mira cómo está construido el resto
de bloques de esa página y hazlo igual — mismos anchos, mismo espaciado,
misma tipografía. El problema no es que el dato sobre: es que el bloque
no encaja con lo que tiene alrededor.

Menos caja y más línea. La información cabe en una frase —*"4º, a 13
puntos, quedan 34 jornadas: 0,37 por jornada"*— y no necesita un cajón
con bordes para decirse.

*Hecho cuando:* está abajo, encaja visualmente con el resto, y
`npm run build` pasa.

---

## 2. El ojeador de prensa — LA PIEZA GRANDE

Es lo que el dueño pidió el primer día y sigue sin existir.

Hoy Pepe solo lee webs que **copian el precio de Biwenger**: información
que ya tenía. Se midió el 06/09: las tres fuentes dan cifras idénticas
al tercer decimal. Son la misma medida repetida, no tres opiniones.

**La prensa es lo único genuinamente independiente**: un entrenador que
anuncia rotaciones, un tocado, un rumor de fichaje. Eso no está en
ningún precio todavía — y ahí es donde hay ventaja.

Fuentes con RSS: **Marca, AS, Mundo Deportivo, Relevo**. Empieza por dos
que funcionen bien antes que por cuatro a medias.

Encaja en el paquete que ya existe, `src/intelligence/scout/`, como un
módulo más. Mismo formato de informe, con su cita y su fuente:

```json
{"source": "MARCA", "direction": "...", "confidence": null,
 "quote": "texto literal de la noticia", "url": "...", "seen_at": "..."}
```

**Reglas que no se negocian:**

- **La cita literal siempre.** Si mañana la señal falla, hay que poder
  ver quién lo dijo y con qué palabras.
- **La confianza no se inventa.** Ninguna fuente publica una; va `null`
  con su motivo, como ya hiciste con las webs de precio.
- **Nada de "predicción".** La prensa informa de hechos y declaraciones.
  Si el modelo deduce algo, que quede marcado como deducción y no como
  dato.
- **Lo que no empareje con un jugador de Biwenger con confianza, a
  `unmatched`.** Nunca lo adivines.
- **Dos veces al día**, no en cada ciclo. Las noticias no cambian cada
  quince minutos y el ciclo dura dos minutos.
- **Blindado**: un fallo del ojeador jamás puede tumbar un ciclo.
- **Al libro de acierto**, para saber en dos semanas si la prensa aporta
  o es ruido. Precedente: FutbolFantasy saca 0,3365 de Brier en
  pronósticos de titular — peor que tirar una moneda. Ninguna fuente
  entra por prestigio.

**Sobre X (Twitter):** el dueño lo pidió y es donde antes se filtran las
alineaciones. Inténtalo, y **si no hay forma limpia de leerlo, dilo y no
lo fuerces**. Mejor un no honesto que un raspador frágil que se caiga
solo en dos semanas.

Y en sombra: publica lo que dice la prensa **al lado** de lo que decide
Pepe. No conectes nada a ninguna decisión.

---

## 3. La página que nadie puede ver

`dashboard-v8/src/pages/AnalysisPage.jsx` importa siete paneles y **no
está enrutada en `App.jsx`**. Anoche casi se publica ahí el reloj de
solvencia.

Mira qué hay en esos siete paneles. Y luego una de dos: o se enruta
porque vale la pena, o se borra porque no. Lo que no puede quedarse es
código vivo que nadie ve — el dueño puede llevar semanas creyendo que
tiene información que no le llega.

Decide tú y **justifícalo panel por panel** en el resumen.

Y deja guardia: que un panel importado y no enrutado se detecte.

---

## 4. El mensaje que miente sobre la causa

`src/analysis/lineup_engine.py:170-177` traduce "el tablero es de otra
jornada" a "el tablero está vacío". Son cosas distintas y llevan a sitios
distintos: una es un refresco que no llegó, la otra es una fuente caída.

Ya nos costó un diagnóstico falso el 10/09.

---

## Cómo dejarlo

`docs/resultado-tarde-noche-2026-09-05.md`:

1. Qué dice la prensa hoy, con dos o tres ejemplos reales de señal
   extraída y su cita. Es lo primero que va a mirar el dueño.
2. Qué había en los siete paneles huérfanos y qué has hecho con ellos.
3. Si X entró o no, y por qué.
4. Lo que te sorprendió.

Si una guardia se pone en rojo, **léela antes de tocarla**. Van seis
veces que te paran y las seis tenían razón.

Y si terminas y sobra noche: no empieces nada nuevo. Refuerza guardias y
deja mejor el resumen.
