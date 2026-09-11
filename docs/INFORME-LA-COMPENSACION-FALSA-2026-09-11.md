# La compensación de los crones externos era falsa

**11/09/2026** · verja 110/110 · sin push

---

## Lo que se creía, y lo que desmiente

Del 10 al 11/09 los tres disparos externos llevaron **una hora de menos escrita a
mano**, sobre esta teoría: *«cron-job.org aplica CET siempre, aunque le pongas
`Europe/Madrid`»*.

Se dedujo de **un solo caso**. El historial la desmiente de forma directa:

```
10/09   job "45,52 6"  Europe/Madrid   ->  ciclo a las 07:52
11/09   job "45,50 3"  Europe/Madrid   ->  disparos a las 03:45 y 03:50
```

**Madrid sí se honra.** La compensación adelantaba los disparos una hora, y la
primera ventana del reset se abrió con el mercado sin resetear.

Lo del 10/09 probablemente era otra cosa —ese job venía de antes y pudo tener otra
zona— pero no se puede probar y da igual: la medición directa manda.

## 1. Fuera la compensación, con su rastro

`relojes.js` lleva ahora los crones tal cual están —`45,50 4` y `15 7`,
`Europe/Madrid`— y, encima, el registro de que hubo una compensación, que era
falsa y cómo se desmintió, con las dos líneas del historial.

No lo he borrado a propósito: dentro de tres meses, alguien mira un disparo raro y
deduce lo mismo. Ahora se encontrará escrito que ya se probó y no valía.

**Guardia:** `test_no_queda_compensacion_en_los_crones_externos`. Exige los crones
buenos, **prohíbe** que vuelvan los compensados (`45 3`, `50 3`, `15 6`) como
configuración, y exige que el rastro siga ahí —`ERA FALSA`, y las horas `03:45` y
`07:52`—. Si alguien borra la explicación para limpiar, se pone roja.

## 2. El aviso, cambiado por el que sirve

`avisoDelCambioDeHora()` vigilaba una compensación que ya no existe: no había nada
que revertir el 25 de octubre. **Fuera.**

En su sitio, `avisoDeDisparoFueraDeHora()`: si un ciclo entra a una hora que **no
es ninguna de las configuradas**, lo dice —con la hora a la que entró, la hora a la
que tenía que entrar y la diferencia—.

**Y no diagnostica la causa.** Enseña que no encaja y deja que lo mire una persona:

> *«Puede ser un retraso, una zona mal puesta o un job de más — esto no lo
> distingue, sólo dice que no encaja.»*

Esa mitad es deliberada, y hay guardia que la protege: el test comprueba que el
texto **no** menciona CET, ni el horario de verano, ni cron-job. Con una
observación no se sabe la causa, y eso es exactamente lo que costó la ventana.

La alarma sale en amarillo, sólo cuando salta, junto a las que ya existen. Con el
ciclo en hora no aparece nada.

**Lo que no puedo hacer todavía, y lo digo:** pediste avisar si un disparo llega
*sistemáticamente* a otra hora. Para «sistemáticamente» hace falta un histórico de
horas de llegada que no guardamos —`activity` sólo registra escrituras—. Lo que hay
detecta **cada** ciclo desplazado, que es el mismo hecho visto de uno en uno. Si
quieres el patrón, hay que empezar a guardar llegadas y te lo digo antes de
hacerlo.

## 3. Doctrina 35: eran dos, no tres

El cron externo **no** era uno de los fallos de zona. La tabla se queda con los dos
reales —el cálculo interno y `meta.generated_at`— y donde estaba el tercero hay
ahora una nota de que existió y era falso, porque una regla apoyada en un ejemplo
inventado enseña mal.

### Y la lección, escrita donde se ve

> **Un solo caso no es una medición**
>
> *«Monté una compensación sobre n=1 y me costó la primera ventana.»* — dueño,
> 11/09/2026
>
> Un caso aislado es una **observación**: dice que algo pasó, no por qué. Para
> convertirlo en regla hace falta historial, y hasta entonces lo honesto es dejar
> el sistema como está y seguir mirando.

Con un añadido que me parece la parte útil: **cada número medido de este documento
lleva su `n` al lado** —12 de 12 estados, 4 jornadas × 7 managers, 85 fotos— y eso
no es adorno. Es la diferencia entre una regla y una corazonada con suerte.

---

## Estado

- `test_los_relojes_v1`: **6/6**
- Verja: **110/110**
- `vite build` hecho, `dist` copiado a `dashboard/`
- Rama `main`, **sin push**
