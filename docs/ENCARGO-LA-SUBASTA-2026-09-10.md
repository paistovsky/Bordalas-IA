# ENCARGO — LA SUBASTA

**Fecha:** 2026-09-10
**Rama:** `subasta/estar-a-las-siete-menos-cinco`

---

## El hueco

El dueño lo explica así, y describe una mecánica que Pepe hoy no juega:

> *"Las pujas se ejecutan en el reset. Si yo no pujo nada, pero cinco minutos
> antes entro y le meto una puja, me lo puedo llevar. Imagínate ganar seis
> jugadores así: al día siguiente tienes 20k × 6 gratis. Si no tiene pujas, no
> tiene por qué haber prima. Estas estrategias las hacen Pollo y Luismi."*

**El libro de pujas dice que Pepe ha colocado una puja en toda su vida.** Una.

Tres motivos, y el primero es mío.

---

## BLOQUE 0 — Medir la subasta antes de tocarla

Cuatro preguntas. Las tres primeras se contestan leyendo el tablón y la API sin
escribir nada; la cuarta leyendo el código.

**0.1 — ¿Cuántos jugadores se llevan sin competencia?**

En el tablón se ve el precio pagado y el precio de mercado de cada compra. El que
pagó **el precio más calderilla** no tuvo rival; el que pagó un 5 % por encima
sí. Publica, sobre todo el histórico de compras que tengamos:

- qué porcentaje se cerró prácticamente al precio de mercado;
- el reparto de primas pagadas, por comprador;
- y **cuántos de esos, además, venían subiendo** — que son los que valen.

Ese número dimensiona la idea entera. Si cada mañana hay seis jugadores que suben
y nadie puja por ellos, esto es la liga. Si hay uno cada tres días, es otra cosa.

**0.2 — ¿Una puja pendiente bloquea el saldo?**

Decide cuántas se pueden poner a la vez. Si bloquea, poner cuatro exige tener el
dinero de las cuatro aunque solo ganes una.

**0.3 — ¿Qué pasa si ganas más jugadores que fichas libres?**

¿Biwenger rechaza, obliga a vender, o deja pasar? **Si no lo puedes averiguar sin
arriesgarte, no lo pruebes**: dilo y ponemos el tope en el número de huecos
libres, que es lo seguro.

**0.4 — ¿Se pueden colocar varias pujas en un mismo ciclo?**

Mirando el código del ejecutor. "Una acción por vuelta" es una decisión nuestra,
no un límite de Biwenger — confírmalo.

---

## BLOQUE 1 — El reloj. Esto es culpa mía y va primero.

El reset del Computer es a las **07:00 de Madrid**. El cron que puse ayer
—`7 * * * *`, en UTC— deja las vueltas a las **06:07 y 07:07 de Madrid**.

```
06:07  ultima oportunidad de pujar     53 minutos antes del cierre
07:00  se resuelven todas las pujas
07:07  Pepe se entera                   7 minutos tarde
```

Cualquiera que entre a las 06:55 puja después de nosotros y no nos enteramos.
**Tú me habías propuesto el cron correcto el 07/09 y yo lo tumbé** diciendo que
el cron era lo que menos peticiones ahorraba. Estaba mirando el presupuesto y no
el reloj de la subasta.

Propón el cron definitivo, con dos condiciones:

- **una vuelta a las 06:55 de Madrid**, y alguna más pegada al cierre si crees
  que compensa;
- que funcione **en verano y en invierno**: el cron de Actions es UTC y Madrid
  cambia de huso. Tú ya lo tuviste en cuenta la otra vez; hazlo otra vez y
  explícalo en un comentario dentro del fichero.

Escribe las líneas exactas en el informe. **El workflow lo edita el dueño**, tú no
lo toques.

Y dime cuántas peticiones al día quedan con ese cron, medido con tu sonda.

---

## BLOQUE 2 — Pujar por varios en la misma ventana

No es "pujar cuatro veces seguidas". Es **elegir el conjunto** que más gana con
el dinero y las fichas que hay. Lo que las ata entre sí es el presupuesto y los
huecos, no la calidad de cada una.

- Ordena a los candidatos por **ganancia esperada por euro comprometido** y ve
  llenando hasta agotar presupuesto o fichas. Un reparto sencillo vale; no hace
  falta nada sofisticado.
- **Las barandillas se comprueban sobre el peor caso: que se ganen todas.**
  Concentración, cuatro por club, suelos de posición y fichas libres se miran
  contra la plantilla resultante si entraran todas, no una por una.
- **Tope duro por ventana**, y que salga de una cuenta y no de un número: lo que
  se pueda deshacer el viernes **aunque el mercado haya caído un 5 %**. Esa es la
  única forma real de hacernos daño: varias posiciones en rojo a la vez con una
  fecha límite encima.
- **Nunca más pujas que fichas libres**, salvo que el bloque 0.3 diga otra cosa.

Esto solo se abre **en la ventana del reset**. El resto del día, una acción por
vuelta como siempre.

---

## BLOQUE 3 — El desvío de puja, mal calibrado por mi culpa

Cuando pusimos que las pujas no fueran cifras redondas, lo hicimos proporcional
al precio: hasta un **0,5 %**. En un jugador de 4 M eso son **20.000 €**, que es
exactamente lo que ese jugador sube en un día.

**El seguro se come la ganancia entera.** Y en la estrategia del dueño —llevarse
seis jugadores baratos que suben 20k— sería la diferencia entre ganar y perder.

El desvío tiene que ser **una fracción pequeña de la ganancia esperada, no del
precio**. Ponle un número, mídelo sobre los objetivos de hoy y publica lo que
cuesta, como ya hace ahora.

Y ojo con el otro lado: si el desvío se queda en nada, volvemos a ser
predecibles. Busca el punto y explícalo.

---

## BLOQUE 4 — Que se vea

El dueño lo dijo así: *"no veo pujas para ganar algún jugador, ni en estrategia
pone «espero a cinco minutos antes del reset»"*.

En pantalla tiene que salir, antes del reset:

- **por quién va a pujar**, cuánto, y por qué ese importe;
- cuánto dinero compromete en total y cuántas fichas ocuparía si ganara todas;
- y cuánto falta para el cierre.

Y después del reset: **qué ganó y qué perdió**, con el importe. Eso alimenta el
libro de pujas, que hoy tiene un solo registro.

---

## Lo que NO se hace esta noche

**No se puja.** Se prepara, se publica y se enseña lo que habría hecho. El primer
reset de verdad lo miramos juntos con los números delante.

Y ningún umbral se mueve: ni el listón, ni la deuda máxima, ni el tope por
operación. Lo que cambia es **cuándo** y **cuántas**, no **cuánto**.

---

## Reglas de la casa

1. Rama `subasta/estar-a-las-siete-menos-cinco` desde `main`.
2. Verja encadenada, sin excepciones:

   ```powershell
   python scripts/run_validation_gate.py
   if ($LASTEXITCODE -eq 0) {
       git add -A
       git commit -m "subasta: estar a las siete menos cinco"
   } else {
       Write-Host "VERJA EN ROJO - nada que subir"
   }
   ```

   Tú no empujas.
3. **Ninguna escritura contra Biwenger.** Lecturas las justas: venimos de un
   bloqueo por exceso de peticiones.
4. No toques `.github/workflows/bordalas-live.yml`.
5. Ninguna guardia lee estado externo ni pasa con las manos vacías.
6. `git status` antes de commitear, y en el informe qué entra.
7. Termina cada commit con `Autor-real: Claude Code (VS Code)`.
8. Si la medición contradice el encargo, gana la medición. El bloque 0.1 puede
   decir que no hay tantos jugadores gratis como creemos, y sería lo más útil de
   la noche.

---

## Informe

- **cuántos jugadores se llevan sin competencia**, y cuántos de ésos venían
  subiendo;
- si una puja pendiente bloquea saldo, y qué pasa al ganar más de las fichas
  libres;
- **el cron definitivo**, con verano e invierno, y las peticiones que deja;
- qué habría pujado hoy: nombres, importes, dinero comprometido, fichas;
- el desvío nuevo y lo que cuesta;
- lo que no hiciste y por qué.
