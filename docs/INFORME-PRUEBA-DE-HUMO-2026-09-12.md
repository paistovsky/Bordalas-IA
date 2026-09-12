# Prueba de humo: el suelo baja, y aparece el techo de verdad

**12/09/2026** · verja 112/112 · sin push

---

# VIAJES COMPLETADOS: 0

---

## Lo que pediste, hecho

| | |
|---|---|
| Suelo del carril | **400.000**, estado `PRUEBA_DE_HUMO` |
| Cupo por ciclo de reset | **1**, estado `PRUEBA_DE_HUMO` |
| Vía vieja de especular | **en pausa** (`ESPECULACION_VIEJA_EN_PAUSA`, por defecto ON) |
| Porcentajes de presupuesto | **sin tocar** — ni `MAX_SINGLE_SPECULATION_PERCENT` ni `MAX_SAFE_DEBT` |

La escalera vive en un sitio y sube sola: **1 (PRUEBA_DE_HUMO) → 2 (ESTRENO) → 4
(PLENO)**, y lo que la mueve es `un_viaje_cerrado_entero` — comprado, listado,
oferta, **cobrada por encima del suelo**. Un corte de pérdidas no la mueve: eso
cerró el viaje, no lo completó.

---

## Pero antes de encender, lo que pediste comprobar: **no sale positivo**

Con el mercado de hoy, al suelo de 400.000:

```
candidatos sobre el suelo          10
entran por margen (>= 1 %)          8
SE PUEDEN PAGAR                     0     <- de 8
tope por operación            843.612
```

**Cero.** Y no por el suelo: por el **techo**.

| no cabe | precio | | no cabe | precio |
|---|---|---|---|---|
| Cancelo | 5.970.000 | | Larrubia | 4.790.000 |
| Parrott | 6.450.000 | | Hjulmand | 4.650.000 |
| Trent | 2.760.000 | | Rubén García | 2.680.000 |
| Isaac Romero | 2.350.000 | | Maguette Gueye | 1.730.000 |

El más barato de los ocho es **el doble** del tope. En la banda comprable
—400.000 a 843.612— hay **tres** jugadores en todo el tablero, y **dos son de un
manager, no del Computer**, así que el carril no los mira: la prima de reventa que
sostiene el negocio es la del Computer recomprando, y a un manager no se le vende
así. Queda **uno**, Víctor García (MED, 660.000), y viene **cayendo −1,80 %/día**.

**Bajar el suelo era necesario y no era suficiente.** Te lo digo tal cual: la
prueba de humo está armada y hoy no tiene con quién hacerse. Lo que la
desbloquea no es otro umbral —es que el tope suba con la caja, o que el reset
saque al mercado alguien de esa banda. Las dos cosas pasan solas; ninguna la
fuerzo yo.

---

## Tres fallos que salieron al comprobarlo, y los tres habrían dejado la prueba en cero

### 1. El carril elegía a Cancelo. Siempre.

El tope se aplicaba **al pagar**, nunca **al elegir**. Y el orden de preferencia
va por prima de reventa, que prefiere a los caros — así que el carril elegía
sistemáticamente **al que menos podía pagar**, la puja se rechazaba sola, y el
ciclo se iba en un nombre imposible. Cada día. En silencio.

```
elegía     Cancelo, 5.970.000
tope         843.612
```

Arreglado: `los_que_se_pueden_pagar()`, el **mismo** tope preguntado un paso
antes. No es un umbral nuevo — es `MAX_SINGLE_SPECULATION_PERCENT`, el que ya
había, preguntado cuando todavía sirve de algo.

> Un techo que sólo se comprueba cuando ya no se puede hacer nada no es un techo:
> es un parte de defunción.

### 2. Pausar la vía vieja le quitó el dinero al carril

El corte de la pausa estaba en la primera línea y devolvía `budget: 0`. Parecía
inofensivo —si no compra, para qué quiere presupuesto—, salvo que **el
presupuesto no es una opinión de la vía vieja: es la caja de la liga, y el carril
lo lee de ahí**. Con aquel cero el carril contestaba *«Sin presupuesto de
especulación conocido no se puja»*.

O sea: **pausar la vía vieja apagaba en silencio justo lo que la pausa existía
para poder medir.**

Es la segunda vez lo mismo —antes fue `KeyError: 'owned'`—, así que va como
regla:

> **Pausar una vía para sus DECISIONES, nunca sus MEDICIONES.**

El corte está ahora después del bloque de presupuesto. Verificado en vivo: con la
vía pausada, `budget = 2.109.030`, `single_operation_limit = 843.612`.

### 3. El panel decía «8 llegan al suelo, 0 fuera»

Cierto, y la conclusión que sugería, falsa: ni uno de los ocho era comprable. Un
panel que cuenta candidatos sin contar el tope **no informa, tranquiliza**. Ahora
pinta cuántos se pueden pagar, el tope, y **los que no caben con su nombre**.

Y la telemetría llevaba el suelo escrito a mano (`>= 1_000_000`): al bajarlo a
400.000, la pantalla habría seguido pintando la lista vieja. Ahora se lo pregunta
a `suelo_de_precio()`, y hay guardia que prohíbe el número escrito en los dos
ficheros.

---

## Un error de modelo que habría hecho optimista la prueba

`margen_esperado` le aplicaba a un jugador de menos de 1 M la prima de **su
posición** en vez de la de **su tramo de precio**. Las dos tablas salen de las
mismas 34 recompras, partidas de dos formas; para un barato, la que describe su
caso es la del tramo.

```
Víctor García · MED · 660.000 · cayendo −1,80 %/día

prima de MEDIO   (+2,85 %)   margen  +0,75 %   <- entraba
prima de <1 M    (+1,52 %)   margen  −0,56 %   <- no entra
```

Casi dos puntos de margen inventados, **justo en el rango donde iba a jugarse la
prueba de humo**. Corregido.

---

## La condición de salida, apuntada como lo que era

El cupo subía de 2 a 4 **sólo si se cerraba un viaje** — y el carril **no podía
comprar**, porque el tope por operación era menor que el suelo de 1 M. La
condición dependía de que funcionara exactamente lo que estaba roto.

No era un número mal puesto: era una puerta cuya llave estaba dentro de la
habitación. Queda escrito en el módulo y en la guardia, con fecha, para que la
próxima escalera se lea preguntando *«¿quién sube este escalón, y puede?»*.

---

## Guardias

`test_la_rendija_v1` — **36/36** (eran 27). Las nuevas:

- el suelo y el cupo de la prueba, y que vuelven solos al completarse un viaje
- que un corte de pérdidas **no** la termina
- que los baratos usan la prima de su tramo
- que la vía vieja está en pausa, y que **pausar no cambia la forma** (las claves
  del retorno se comparan contra el árbol, no contra una lista a mano)
- **el fallo de Cancelo**: que el tope se pregunta al elegir, y que el ejecutor lo
  llama *antes* de elegir
- que el suelo vive en un sitio, y que la pantalla lo pinta sin escribirlo

Y las cuatro guardias viejas que afirmaban «el cupo empieza en 2» están
reescritas a la escalera nueva, no parcheadas.

---

## Estado

- Verja: **112/112**
- Suelo **400.000** · cupo **1** · vía vieja **en pausa**
- Presupuesto tras la pausa: **2.109.030** · tope por operación **843.612**
- Pantalla construida y desplegada
- Rama `main`, **sin push**

---

# VIAJES COMPLETADOS: 0
