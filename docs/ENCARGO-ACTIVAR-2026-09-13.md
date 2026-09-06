# ENCARGO — ACTIVAR

**Fecha:** 2026-09-13
**Rama:** `activar/despliegue-y-puja`
**Estado de partida medido:** `diagnostico/status.json`, 2026-09-06 09:02:42, ciclo LIVE, user 14175949.

---

## Por qué este encargo

Tres frases del dueño, literales:

> *"Pollo se llevó a Natan por 7 €. Eso es que sabe que Pepe puja a 0 o a 5 clavaos. Hay que randomizar eso."*
> *"También copiarle la estrategia o hacer la misma, hay que subir patrimonio o no ganamos."*
> *"Activa lo que haga falta."*

Los tres bloques de abajo son esas tres frases traducidas a código. Nada más.

**El contexto en cuatro números.** Pepe va 4.º con 133 puntos. Pollo va 1.º con 146:
trece puntos. Pero el valor de plantilla de Pollo es 85.060.000 € contra los
49.540.000 € de Pepe: **35.520.000 € de diferencia**. La distancia deportiva es
pequeña; la financiera es enorme, y la financiera se convierte en deportiva sola,
jornada a jornada. Pollo tiene 22 fichas. Pepe tiene 14, y 5.350.683 € en el
bolsillo de fichar sin tocar desde hace semanas.

El sistema ya sabe a quién comprar. Lo que no hace es comprar.

---

## BLOQUE 1 — Que la puja deje de ser adivinable

### Lo que pasa hoy

`src/analysis/rival_bid_model.py`, función `candidate_bids()`:

```python
importes = {precio + 1}

for factor, _ in curva:
    importes.add(int(precio * factor) + 1)

importes.add(techo)
```

La curva de prima está publicada en el propio `status.json`
(`acquisition.premium_model.curve`): `1.0, 1.0052, 1.0259, 1.0411, 1.0695,
1.2027, 1.2449`. El precio de mercado lo ve todo el mundo. Por tanto **cualquiera
que sepa cómo pensamos puede enumerar nuestro conjunto de pujas candidatas con
una calculadora**. No hace falta que Pollo nos lea el código: le basta con
calcular el mismo valor razonable y ponerse unos euros por encima. Es lo que
parece haber pasado con Natan: nuestra sombra decía 3.010.000 € y él pagó
3.010.007 €.

### Honestidad antes de tocar nada

No tenemos prueba de esto. El libro de pujas (`bid_outcomes`) tiene **una sola
puja registrada**: colocada 1, ganada 1. Con una muestra de uno no se demuestra
que nadie nos esté leyendo. Los 7 € pueden ser casualidad, o dos valoraciones que
coinciden. **No construyas ninguna teoría sobre esto en el código ni en el
dashboard.** Lo que sí es cierto es que el coste de blindarse es ridículo y el
coste de que sea verdad es perder cada subasta por siete euros. Se hace por eso,
no porque lo sepamos.

### Lo que hay que construir

Un **desvío aleatorio hacia arriba**, aplicado *al final*, sobre el importe que ya
eligió `optimal_bid()`.

**No toques la matemática de `optimal_bid()`.** El EV, el techo, el rendimiento
mínimo de especulación y las guardias que dependen de ellos (incluida la lección
de Soler) se quedan exactamente como están. El desvío es la última capa, en la
ruta del ejecutor, después de decidir.

Especificación:

1. **Función nueva** en `rival_bid_model.py` (o en un módulo propio si te resulta
   más limpio):

   ```
   bid_jitter(player_id, price, matchday, fecha) -> int
   ```

   Devuelve un entero en `[0, J]` con
   `J = clamp(int(price * 0.005), 1_000, 50_000)`.
   En un jugador de 3.000.000 € eso son 15.000 € de tope y 7.500 € de media:
   **el 0,25 % de la operación**. Suficiente para saltar por encima de quien se
   pone siete euros arriba, irrelevante para el EV.

2. **Reproducible dentro del ciclo, impredecible fuera.** No uses `random`
   sin semilla. Siembra con un hash:

   ```
   semilla = sha256(f"{player_id}:{fecha}:{matchday}:{SALT}")
   ```

   Motivo: si el ciclo se reintenta o si dos módulos preguntan por el mismo
   objetivo, el importe tiene que salir idéntico, o acabamos con pujas duplicadas
   distintas por el mismo jugador — que es exactamente lo que
   `test_bid_deduplication_v1` existe para impedir.

3. **La sal.** `SALT = os.environ.get("BORDALAS_BID_SALT", "")`. Si está vacía,
   usa una constante del módulo y **sigue funcionando** — degradar, nunca romper.
   Deja escrito en el docstring que si el repositorio es público la sal real debe
   vivir en los secrets de GitHub, porque una sal en el código es una sal que no
   protege. Añadir el secret es tarea del dueño, no tuya; solo deja el hueco y
   dilo en el informe.

4. **Límites duros.** El importe final:
   - nunca por encima del techo (`min(importe + desvio, techo)`),
   - nunca por debajo de `precio + 1`,
   - nunca por encima del tope por operación vigente.

5. **Nada de números clavados.** Después del desvío, si el importe acaba en
   `0000` o en `5000`, súmale entre 1 y 999 € más (respetando el techo). Es la
   frase del dueño hecha guardia: que no acabe en 0 ni en 5 clavaos.

6. **Que se vea.** Publica en cada objetivo del dashboard el importe final y, al
   lado, el importe "limpio" que habría salido sin desvío, más la diferencia en
   euros. Quiero poder mirar la pantalla y ver cuánto nos está costando el
   seguro. Si en un mes ha costado más de lo que ha ganado, se apaga.

### Guardia nueva: `src/analysis/test_puja_impredecible_v1.py`

Estilo de la casa (SÍNTOMA / CAUSA / CONSECUENCIA, lista `TESTS`, `main()` con
`raise SystemExit(1)`). Mínimo:

- dos jugadores distintos al mismo precio reciben desvíos distintos;
- el mismo jugador, dos llamadas en el mismo ciclo, recibe el mismo importe;
- el importe final nunca supera el techo ni baja de `precio + 1`;
- sobre 200 objetivos simulados, ninguno coincide con `int(precio * factor) + 1`
  para ningún factor de la curva publicada;
- sobre esos 200, menos del 5 % termina en `000`;
- la pérdida de EV frente al óptimo sin desvío se queda por debajo del 0,5 % de
  la operación.

Añádela a `scripts/run_validation_gate.py`.

---

## BLOQUE 2 — Encender el despliegue

### Lo que ya está hecho y apagado

Esto no hay que construirlo. Está construido y publicando en sombra. De
`diagnostico/status.json` de esta mañana, tal cual:

```json
"Amatucci": {
  "operation_class": "SIGNING",
  "intent": "XI_UPGRADE",
  "route": "XI_UPGRADE",
  "value": 3717343,
  "reason": "Entra a la plantilla para jugar mejorando el once: es un fichaje
             y sale del bolsillo de fichar, aunque su reventa diera mas euros.",
  "free_roster_slots": 8,
  "enabled": false,
  "observer_only": true
}
```

Y el motivo por el que hoy no se ficha, también literal, del bloqueo de ese mismo
jugador:

> *"La vía del once le da valor, pero el `intent` se elige por euros y gana la
> reventa: entonces se le exige rendimiento de especulación. Cuesta 3.670.000 EUR
> y solo quedan 2.433.987 sin comprometer."*

Ahí está todo el problema en dos líneas. Amatucci es un fichaje de 3.670.000 €.
El bolsillo de fichar tiene **5.350.683 €**. Pero como el `intent` se elige por
euros y no por clase de operación, se le pide el bolsillo de especular, que tiene
2.433.987 € y un tope por operación de **973.594 €**. Le sobran euros y le falta
bolsillo.

### Lo que hay que hacer

**Poner `enabled` a `true` y quitar `observer_only` en la capa de despliegue.**
Concretamente:

1. **El `intent` se elige por clase de operación, no por euros.**
   `src/analysis/acquisition_valuation.py`, donde hoy hay
   `mejor = max(opciones, key=lambda o: safe_int(o.get("value")))`. La capa de
   despliegue ya calcula `operation_class` correctamente (`SIGNING` / `TRADE`) y
   ya lo razona en su campo `reason`. Haz que producción **lea ese campo** en
   lugar de recalcular por euros. No dupliques la lógica: la sombra ya acertó, se
   trata de dejarla mandar.

2. **Cada clase, a su bolsillo.** `SIGNING` → bolsillo de fichar (5.350.683 €,
   con su propio tope por operación). `TRADE` → bolsillo de especular
   (2.433.987 €, tope 973.594 €). Hoy todo va al segundo.

3. **La vía `ROSTER_FILL`.** Tenemos 14 fichas y la plantilla más grande de la
   liga tiene 22: **8 huecos**. La sombra ya marca `roster_fill_decision:
   "ROSTER_FILL"` y calcula `roster_fill_value`. Enciéndela. Ojo: el propio
   módulo avisa de que 8 es **cota inferior** — el tope real de Biwenger no está
   comprobado. Trátalo como mínimo, nunca como máximo, y no intentes fichar hasta
   un número que no hemos verificado: si Biwenger rechaza una compra por plantilla
   llena, eso se registra y se aprende, no se reintenta en bucle.

4. **Comprueba la concentración *después* de la compra, no antes.**
   Hoy hay una infracción viva: Yamal es el 42,81 % de la plantilla, con el tope
   en 35 %. **Sospecha concreta que quiero que verifiques y que puede explicar
   sola los 0 objetivos pujables:** si la guardia bloquea toda compra mientras
   exista una infracción, estamos atrapados, porque **comprar es precisamente lo
   que baja el porcentaje de Yamal**. La cuenta correcta es la participación
   resultante *tras* la operación. Si está mal, arréglalo y ponle guardia. Si ya
   estaba bien, dilo en el informe y no toques nada.

5. **Deuda: sí, con reloj.** El dueño autorizó endeudarse:
   *"que se endeude y luego decida a quién vende y a quién no, que compre sin
   miedo"*, con la condición *"con estar en positivo 6 horas antes del inicio de
   jornada es suficiente"*. Eso ya es el reloj de solvencia (T−6 h) y ya está
   construido. Úsalo como autoridad para comprar en rojo. **No subas
   `MAX_SAFE_DEBT`.** Autorizó usar la deuda, no ampliar el límite.

### Lo que NO se toca

Todas las barandillas siguen puestas, sin excepción:

- concentración 35 % por jugador y 4 por club;
- suelos de posición en el once;
- reloj de solvencia T−6 h y la cola de ventas;
- el freno de los que caen (no comprar en rampa bajista);
- la confianza por vía (la vía Computer descuenta la ganancia, no el principal);
- tope por operación en los dos bolsillos.

Si para encender algo tienes que tocar una de estas, **para y déjalo escrito en el
informe**. No es una barandilla que estorba, es una factura ya pagada.

### Lo que hay que publicar el primer ciclo

Una lista, en el dashboard y en el informe:

- a quién ficha, por cuánto, de qué bolsillo, y qué saldo queda después;
- a quién rechaza y con qué motivo de una línea;
- **cómo se apaga en una sola línea de comando**, escrita entera y copiable.

Si el primer ciclo con esto encendido no ficha a nadie, el informe tiene que
decir por qué, objetivo por objetivo. "No había nada" no vale como respuesta con
20 objetivos en el mercado y 8 fichas libres.

---

## BLOQUE 3 — La estrategia de Pollo, en números

El dueño pidió copiarle. Esto es lo que hace, medido, no imaginado.

En la ventana medida Pollo compró **7 jugadores por 21.198.020 €**:

| Jugador | Pagado | Prima sobre mercado |
|---|---:|---:|
| Gerard Moreno | 6.450.007 | +0,3 % |
| Pubill | 6.360.006 | −1,1 % |
| Natan | 3.010.007 | −1,0 % |
| Bardeli | 1.877.000 | +4,9 % |
| Camavinga | 1.777.000 | −0,7 % |
| Ratkov | 1.447.000 | +4,1 % |
| Riki Rodríguez | 277.000 | −7,7 % |

**Pollo no paga de más.** Su prima mediana está pegada a cero. La idea de que "el
mercado está caro" queda muerta con esta tabla: el mercado está al precio de
siempre y él simplemente compra.

Lo que hace, dicho en una frase: **ocupa fichas**. Siete compras repartidas por
todas las bandas de precio — de 277.000 € a 6.450.000 € — hasta llenar 22 fichas.
El dinero parado no se revaloriza; los jugadores sí. Cada ficha vacía es capital
al 0 %. Nosotros tenemos ocho.

Y el detalle que más duele: **de esos siete, cinco los había mirado Pepe y los
había rechazado.** Gerard Moreno y Pubill por `SUPERA_PRESUPUESTO` contra el
bolsillo de especular mientras el de fichar dormía. Ratkov y Riki por
`RENDIMIENTO_INSUFICIENTE`. Natan lo había valorado en 3.010.000 € — al euro.
No fallamos al elegir. Fallamos al no estar encendidos.

### La regla que hay que implementar

Con el despliegue encendido, cuando el bolsillo de fichar no llegue para todo,
el orden de prioridad es:

1. `ROSTER_FILL` que además **mejora el once** (entra a jugar);
2. `ROSTER_FILL` que **se revaloriza** (llena ficha y sube de precio);
3. especulación pura.

Repartido en varias operaciones, no en un fichaje grande. Es lo que hace Pollo y
además reparte el riesgo de concentración.

**Lo que NO hay que copiarle:** nada de su posición ni de su ritmo de puntos. Va
trece puntos por delante, no cuarenta. Lo que le copiamos es ocupar el balance,
no el estilo de juego.

---

## BLOQUE 4 — Reglas de la casa

Estas no cambian nunca.

1. **Rama `activar/despliegue-y-puja`.** `main` no se toca.
2. **La verja manda.** Nada sube con la verja en rojo. El comando va encadenado,
   siempre, sin excepciones:

   ```powershell
   python scripts/run_validation_gate.py
   if ($LASTEXITCODE -eq 0) {
       git add -A
       git commit -m "activar: despliegue y puja impredecible"
   } else {
       git reset --hard origin/main
       Write-Host "VERJA EN ROJO - nada que subir"
   }
   ```

   El `push` lo da el dueño por la mañana. Tú no empujas.
3. **Mide contra `diagnostico/status.json`, no contra `data/`.** El `data/` del
   disco es de agosto y miente. Ya nos ha engañado dos veces: dijimos que el
   tablero de titularidades estaba caducado cuando en producción estaba en la
   jornada correcta y refrescado.
4. **No toques `.github/workflows/bordalas-live.yml`.** Está protegido. Si hace
   falta un cambio ahí, escríbelo en el informe para que lo haga el dueño a mano.
5. **Cada arreglo, su guardia**, con el nombre del incidente real, en el estilo de
   la casa, y añadida a `scripts/run_validation_gate.py`.
6. **Si una medición contradice este encargo, gana la medición.** Escríbelo en el
   informe y no lo implementes. Este documento lo he escrito yo desde una foto de
   las 09:02; tú tienes el repositorio delante.

---

## Informe final

Al terminar, un documento en `docs/` con:

- qué se encendió y qué sigue apagado;
- la lista del primer ciclo: fichajes, importes, bolsillos, saldo resultante;
- la línea de comando para apagarlo todo;
- si la guardia de concentración estaba bloqueando las compras (sí / no / y qué
  hiciste);
- cuánto cuesta el desvío de puja, en euros, sobre los objetivos de hoy;
- lo que no hiciste y por qué.

---

## Cola pendiente (no en este encargo, para no mezclar)

- `src/analysis/lineup_engine.py:170-177` sigue contando "jornada equivocada"
  como "tablero vacío". Son dos averías distintas y se ven igual en pantalla.
- 332 jugadores "sin emparejar" en el dashboard, sin una línea que explique qué
  es eso. O se explica o se esconde.
- Repaso estético del dashboard: ocho paneles nuevos en una semana sin criterio
  de conjunto.
- Los delanteros: Pablo Durán con 70 % de titularidad en el banquillo mientras
  defensas con el mismo 70 % juegan. El once salió 5-4-1 con el suelo en 2
  delanteros. Sospecho que el motor infravalora la delantera; hay que medirlo.
