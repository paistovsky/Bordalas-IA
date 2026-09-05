# ENCARGO — la divergencia: precio contra demanda

Noche del 06/09/2026. Para Claude Code en `C:\Users\PC\Bordalas-IA-clean`.
El dueño duerme. Trabaja solo.

Lee antes `docs/resultado-m16-2026-09-06.md`. Este encargo sale de un
hallazgo tuyo de anoche.

---

## DE QUÉ VA

Anoche descubriste que las tres fuentes de precio **no son tres
opiniones: son dos medidas y una repetida**. Todas copian el mismo
número de Biwenger. Su acuerdo es redundancia.

Pero encontraste otra cosa:

> La discrepancia real está entre precio y demanda: en 16 jugadores
> apuntan a lados contrarios. Mikel Rodríguez bajó 6,2 % con 70 puntos
> netos de presión compradora.

**Eso sí es información nueva**: el precio y lo que la gente está
haciendo no coinciden. La hipótesis a comprobar es si esa divergencia
anticipa algo.

Ojo con el vocabulario, como hiciste bien anoche: esto es una
**hipótesis sin comprobar**. Nada en el código puede llamarse
"predicción" hasta que el libro diga que acierta.

---

## LAS REGLAS

Todo en sombra. Nada decide. Prohibido tocar umbrales, presupuestos,
`rival_bid_model.py`, `speculation_engine.py` ni ninguna ruta que
escriba en Biwenger. Rama: `git checkout -b divergencia/2026-09-07`.
Puerta en verde. Cada pieza con su guardia.

---

## 1. La pregunta que SÍ se puede responder esta noche

Antes de montar nada, un estudio con los datos que ya hay en disco.

Hay snapshots desde el 12/08 en `data/` con el precio de los 569
jugadores, y `data/autopilot/price_history.json`. Con eso se puede
responder la pregunta que hay debajo de todo esto:

**¿El precio de un jugador tiene momento o revierte?** Es decir: si
subió ayer, ¿tiende a seguir subiendo mañana, o a corregir?

De la respuesta depende cómo se lee la señal:
- Si hay **momento**, la `Tend` de FutbolFantasy (días consecutivos
  subiendo) es una señal de compra.
- Si **revierte**, entonces comprar al que acaba de subir es comprar
  caro, y la oportunidad está justo en el que baja.

Es la diferencia entre dos estrategias opuestas, y se puede medir con lo
que ya tienes.

**Si los datos no dan para concluir —pocos días, pocos jugadores, mucho
ruido— dilo con esas palabras.** "No hay muestra suficiente" es un
resultado válido y mucho más útil que un número endeble. No fuerces una
conclusión.

*Entregable:* la respuesta con sus números en el resumen. Esto es
investigación, no código que se despliega.

---

## 2. El registro de la divergencia

Lo que no se puede responder hoy: si la divergencia precio/demanda
anticipa una subida. **No hay histórico de demanda** — las fuentes
publican el dato de hoy, no una serie.

Así que hay que empezar a guardarlo. `data/intelligence/divergence_ledger.json`,
mismo patrón que los otros libros de la casa.

En cada refresco del ojeador, por cada jugador emparejado:

```json
{
  "player_id": 0, "player_name": "...", "seen_at": "...",
  "price": 0, "price_change_eur": 0, "price_change_percent": 0.0,
  "demand_net": 0, "demand_source": "...",
  "divergent": true,
  "divergence_kind": "PRECIO_BAJA_DEMANDA_SUBE",
  "outcome": "PENDING",
  "price_after_3d": null, "price_after_7d": null,
  "resolved_at": null
}
```

Y el cierre: pasados 3 y 7 días, se apunta el precio real y se compara
**el grupo divergente contra el resto**. Sin grupo de control no hay
resultado — que un divergente suba no dice nada si subieron todos.

Define `demand_net` con lo que ya parseas y **documenta de dónde sale**.
Si solo lo publica una fuente, dilo: será una medida, no un consenso.

*Hecho cuando:* el libro se alimenta solo, cierra por horizonte, compara
contra control, y hay guardia que lo prueba con datos sintéticos —
incluido el caso de que no haya divergentes ese día.

---

## 3. Que se vea

En MERCADO, marcar los divergentes del día con su tipo y sus dos
números. Y un bloque con el estado del estudio: cuántos apuntados,
cuántos cerrados, y **qué dice la comparación contra el control hasta
ahora** — con su "todavía no hay muestra" bien claro mientras no la haya.

`cd dashboard-v8 ; npm run build` tiene que pasar. No despliegues.

---

## 4. Un arreglo pequeño de paso

`.github/workflows/bordalas-live.yml` lleva **la lista de tests escrita
a mano**, línea por línea, mientras `scripts/run_validation_gate.py`
conoce los 66. Cada guardia nueva hay que acordarse de añadirla en dos
sitios, y el día que se olvide, CI correrá menos que el dueño en local
**sin avisar de nada**.

Sustituye las ~66 líneas por la llamada al script. Comprueba que el
script devuelve código distinto de cero cuando algo falla — si no, CI
daría verde con guardias rotas y sería peor el remedio.

---

## Cómo dejarlo

1. Rama `divergencia/2026-09-07`, puerta en verde, `main` intacto, nada
   desplegado.
2. `docs/resultado-divergencia-2026-09-07.md` con la respuesta del punto
   1 al principio y en cristiano — **¿momento o reversión?** — y qué
   significa para la estrategia.
3. Lo que te sorprendió.
4. Si algo te bloquea, no adivines: déjalo y escríbelo.

Y si terminas y sobra noche: **no empieces nada nuevo**. Refuerza
guardias y deja mejor el resumen.
