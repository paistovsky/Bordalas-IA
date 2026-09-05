# ENCARGO — comprar sin miedo, y saber vender

Noche del 10/09/2026. Para Claude Code en `C:\Users\PC\Bordalas-IA-clean`.

**Este encargo ENCIENDE cosas.** Los ocho anteriores midieron, limpiaron
y construyeron en sombra. Este cambia lo que Pepe hace con dinero real,
por decisión expresa del dueño:

> *"Que se endeude y luego decida a quién vende y a quién no. Que compre
> sin miedo."*

Lee antes `docs/resultado-despliegue-2026-09-10.md`.

---

## AVISO DE ENTORNO — no repitas el error de anoche

Anoche se concluyó que el tablero de titularidad estaba rancio (jornada 2
en la jornada 5). **Era falso.** Se midió contra `data/` del disco local,
que es de agosto. En producción el tablero está en jornada 5, refrescado
y sin rechazos.

**Mide siempre contra `diagnostico/status.json`**, que es la foto de
producción. `data/` del repo es un resto de desarrollo.

---

## 1. PRIMERO: ¿sabe vender? — ES UNA PUERTA, NO UNA TAREA

**Si esto no se puede verificar, no enciendas nada más y reporta.**

Todo el plan del dueño se apoya en poder deshacer posiciones. Y hay
motivos para dudar:

- El Offer Decision Engine está declarado **observador**:
  `decision_executable: false`, *"la inteligencia general de ofertas no
  ejecuta escrituras"*. Etiqueta "Cobrar ahora" y no cobra.
- `ACCEPT_RECOVERY_OFFER` sí escribe, pero estuvo fallando con **HTTP
  500** durante semanas (`accept_offer` mandaba un PUT sin cuerpo). Se
  arregló. **Nadie ha comprobado que hoy funcione.**

Verifica de punta a punta, con evidencia:
- ¿Hay alguna venta ejecutada con éxito desde el arreglo? Mira
  `data/autopilot/autopilot_log.jsonl` **del artefacto de producción**,
  `position_ledger.json`, y el libro de pujas.
- Si no hay ninguna, ¿por qué? ¿No se ha dado el caso, o vuelve a
  fallar?

Y decide con eso: **si no puedes demostrar que Pepe vende, deja
`DEPLOYMENT_ENABLED` apagado**, escribe por qué, y no sigas con el punto
3. El dueño prefiere una noche perdida a quedarse atrapado en deuda.

---

## 2. La política de venta — a quién le toca salir

Hoy nadie decide esto: el motor que etiqueta no ejecuta.

Cuando haga falta caja, tiene que haber un orden claro y escrito, y
**publicado en el dashboard** para que el dueño lo vea antes de que pase.

Criterios, y justifícalos con los datos que ya tienes medidos:
- Primero quien **no juega**: jerarquía baja, probabilidad de titular
  baja. Un suplente no puntúa, solo ocupa ficha y dinero.
- Después, peor relación **coste por punto** — ese campo ya se calcula y
  hasta ahora no lo leía nadie.
- Y ojo con el momento: el que **viene subiendo** de precio es
  precisamente el que conviene retener, y el que **cae** se vende antes
  de que caiga más. Con r=+0,90, eso está medido.

Respeta lo que ya manda por encima: guardarraíl de posición (no vaciar
una posición), intocables, y el tope de concentración de anoche.

*Hecho cuando:* hay un orden de venta calculado, visible en pantalla con
su motivo, y guardia que comprueba que no propone vaciar una posición ni
vender a un intocable.

---

## 3. Encender el despliegue, con la deuda segura incluida

Solo si el punto 1 salió bien.

- `DEPLOYMENT_ENABLED` a **encendido**.
- La vía de fichar puede usar el **margen de deuda segura**
  (`MAX_SAFE_DEBT`), que por definición del propio sistema es deuda
  cubrible vendiendo en un ciclo.

**No subas `MAX_SAFE_DEBT` ni su colchón ni los haircuts.** El dueño
autoriza usar el margen que ya existe, no ampliarlo. La diferencia
importa: Luismi va con 10 M en rojo y eso es otra cosa.

Con eso entra Expósito (5,13 M, Clave, 90 % titular) además de Natan.

---

## 4. Cómo se entrega algo que se enciende

Distinto de las ocho noches anteriores:

- **Escribe cómo se apaga**, en la primera línea del resumen. Una
  constante, un comando, y qué vuelve a pasar al apagarlo.
- **La lista de lo que hará en el primer ciclo**: a quién ficha, por
  cuánto, con cuánta deuda, y a quién vendería si hiciera falta caja.
- **Comprueba que el libro de pujas los registra.** Es la única forma de
  saber en una semana si esto funciona.
- Rama `sin-miedo/2026-09-11`, puerta en verde, `main` intacto. **El
  push lo da el dueño**, como siempre.

---

## Cómo dejarlo

1. `docs/resultado-sin-miedo-2026-09-11.md`, empezando por cómo se apaga
   y por la lista del primer ciclo.
2. Si el punto 1 falló: dilo en la primera línea, con evidencia, y nada
   encendido.
3. Lo que te sorprendió.
4. Si una guardia se pone en rojo, **léela antes de tocarla**. Van cuatro
   veces esta semana que te paran y las cuatro tenían razón.
