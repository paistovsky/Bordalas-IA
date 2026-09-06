# ACTIVAR — resultado

Rama `activar/despliegue-y-puja`. **Verja: 78 de 78 en verde** (77 al
empezar). `main` intacto. `.github/workflows/bordalas-live.yml` sin
tocar. `npm run build` pasa. **Sin push.**

Medido contra `diagnostico/status.json` del **06/09/2026 09:33**, ciclo
LIVE, usuario 14175949.

---

## Cómo se apaga todo, en una línea

```powershell
$env:DEPLOYMENT_ENABLED = "0"
```

Para el ciclo de producción, en `bordalas-live.yml` (**tuyo, yo no lo
toco**), dentro del bloque `env:`:

```yaml
  DEPLOYMENT_ENABLED: "0"
```

Y para dejarlo apagado de forma permanente sin variables de entorno:
cambiar `DEPLOYMENT_DEFAULT = "1"` por `"0"` en
`src/analysis/deployment.py`.

Al apagarlo vuelve exactamente lo de antes: el `intent` se elige por
euros, un fichaje se mide contra el bolsillo de especular y la vía de
ficha vacía no compite. **El desvío de puja no se apaga con eso** — va
por su cuenta y no depende del despliegue.

---

# LA CABECERA: el primer ciclo no ficha a nadie, y no es por el bolsillo

El encargo lo pedía así: *"Si el primer ciclo con esto encendido no
ficha a nadie, el informe tiene que decir por qué, objetivo por
objetivo. 'No había nada' no vale como respuesta."*

**Con el despliegue encendido, los 20 objetivos de hoy siguen sin
comprarse. Y el motivo no es el que dice el encargo.**

| Jugador | Precio | Vía que pagaría | Vale por esa vía | ¿Cabe en el bolsillo? | Veredicto |
|---|---:|---|---:|---|---|
| Pedri | 15.350.000 | ROSTER_FILL | 3.651.436 | no | no compensa **y** no cabe |
| Roro Riquelme | 4.240.000 | COMPUTER_RESALE | 4.294.696 | no (tope 973.594) | supera el bolsillo de especular |
| **Amatucci** | **3.670.000** | **XI_UPGRADE** | **2.716.842** | **sí** | **no compensa** |
| Pathé Ciss | 2.930.000 | ROSTER_FILL | 2.311.925 | sí | no compensa |
| Bellerín | 2.430.000 | — | 0 | — | ninguna vía le da valor |
| Tárrega | 2.180.000 | ROSTER_FILL | 1.571.387 | sí | no compensa |
| Gabriel Suazo | 1.730.000 | ROSTER_FILL | 1.517.201 | sí | no compensa |
| Drkusic | 1.730.000 | — | 0 | — | ninguna vía le da valor |
| Loureiro | 1.240.000 | — | 0 | — | ninguna vía le da valor |
| Bright Ede | 1.140.000 | — | 0 | — | ninguna vía le da valor |
| Johnny | 670.000 | — | 0 | — | ninguna vía le da valor |
| Kumbulla | 590.000 | — | 0 | — | `doubt` (no disponible) |
| Miguel Rodríguez | 500.000 | — | 0 | — | ninguna vía le da valor |
| Gorosabel | 420.000 | COMPUTER_RESALE | 425.418 | sí | `injured` (no disponible) |
| Álvaro Fernández | 290.000 | — | 0 | — | ninguna vía le da valor |
| Szczęsny | 270.000 | — | 0 | — | ninguna vía le da valor |
| Aitor Fernández | 260.000 | — | 0 | — | ninguna vía le da valor |
| Javi Morcillo | 250.000 | ROSTER_FILL | 165.974 | sí | no compensa |
| Pelayo | 240.000 | — | 0 | — | ninguna vía le da valor |
| Letacek | 150.000 | — | 0 | — | ninguna vía le da valor |

**Cinco de ellos caben de sobra en el bolsillo de fichar** —Amatucci,
Pathé Ciss, Tárrega, Suazo y Morcillo—. Lo que los para no es el
dinero: **es que cuestan más de lo que valen por la vía que los
pagaría.**

## Amatucci, que era la pieza del encargo

El encargo lo daba por hecho: *"Amatucci es un fichaje de 3.670.000 €.
El bolsillo de fichar tiene 5.350.683 €. Le sobran euros y le falta
bolsillo."*

**Le sobra bolsillo y le falta valor.** Está en el propio
`status.json`, en su fila:

```
xi_reason: "Suma 46 puntos. A precio de mercado (21.696 EUR/punto)
            valen 998.016 EUR; con un 25 % de margen exigido y
            confianza 0.51, pagariamos hasta 2.716.842 EUR."

deployment: value        3.717.343
            value_route  COMPUTER_RESALE   <- ojo aquí
            route        XI_UPGRADE
```

Los 3.717.343 € que hacían que "compensara" **no son su valor como
fichaje: son su valor de reventa al Computer.** Como fichaje vale
2.716.842 €, novecientos cincuenta y tres mil por debajo de lo que
cuesta.

Y como especulación tampoco sale: comprar a 3.670.000 y revender a
3.717.343 son 47.343 € de margen, un **1,3 %**, por debajo del 3 %
que la casa exige desde hace semanas porque *"por debajo de eso la
subida estimada está dentro del ruido del precio"*.

**No hay tesis que sostenga esa compra: ni la deportiva ni la
financiera.** Encenderlo y comprarlo habría sido pagar 953.158 € de
más apoyándose en un número que su propia vía rechaza.

---

# BLOQUE 2 — Qué se encendió

## `DEPLOYMENT_ENABLED` está a `true`

Estaba apagado desde el 10/09 esperando una prueba: que se pudiera
demostrar que Pepe deshace una posición antes de dejarle endeudarse.
Esa prueba existe desde el 12/09 (`test_venta_ejecutable_v1` recorre
los siete tramos hasta el `PUT /api/v2/offers/{id}` con cuerpo), y
además **el déficit se acabó**: el saldo del 06/09 es **+1.725.383 €**,
no −421.792.

La guardia que lo fijaba en `False` se puso roja, se leyó, y se
reescribió con el motivo nuevo dentro. No se borró.

Con eso encendido:

1. **El `intent` sale de la clase de operación, no de los euros.** Lee
   `operation_class` de la capa de despliegue, que ya lo razonaba bien
   en sombra. No se ha duplicado ninguna lógica.
2. **Cada clase a su bolsillo.** `SIGNING` → fichar (5.350.683 €).
   `TRADE` → especular (2.433.987 €, tope 973.594 €).
3. **`ROSTER_FILL` encendida.** Ocho huecos, tratados como **cota
   inferior** — el módulo ya avisaba de que el tope real de Biwenger no
   está comprobado y sigue avisando. Hoy la vía da valor a cinco
   jugadores que antes salían a cero.
4. **Deuda con reloj.** El bolsillo de fichar ya incluye 3.625.300 € de
   deuda dentro de `MAX_SAFE_DEBT`, que no se ha tocado.

## Y un arreglo que no estaba en el encargo, que salió al encender

En cuanto se encendió el interruptor, **`test_acquisition_wiring_v1` se
puso rojo**. Un jugador de 9.000.000 € que suma 6 puntos salía
`PUJAR` a 9.000.001.

El motivo es el mismo que el de Amatucci, en su forma extrema: su valor
como fichaje eran 2.068.000 € y los 9.092.475 € con los que se
justificaba la puja venían de la vía de **reventa**. Se pagaba dinero
del bolsillo de fichar amparándose en un número de comerciar, y encima
sin el listón de rendimiento que esa vía tiene que pasar.

**La regla que faltaba: el bolsillo, el listón y el valor salen todos de
la misma vía.** `classify_operation` publica ahora `decision_value` —lo
que vale por la vía que va a pagar— y es eso lo que decide. Lo que vale
por todas las vías se sigue publicando en `value_all_routes`, para poder
mirarlo.

**Esto tiene un coste y lo digo:** un jugador que valga 2 M como fichaje
y 5 M de reventa ahora se puja hasta 2 M, no hasta 5. Se pueden perder
subastas contra quien valore la reventa. La alternativa era pagar de más
con un número prestado, y perder una subasta cuesta una subasta mientras
que pagar de más cuesta dinero.

## Lo que NO se tocó

Ninguna barandilla. Concentración 35 % / 4 por club, suelos de posición,
reloj T−6 h, cola de ventas, freno de los que caen, confianza por vía,
topes por operación en los dos bolsillos, `MAX_SAFE_DEBT`. **Ni uno.**

---

# La guardia de concentración: NO estaba bloqueando nada

El encargo pedía verificarlo. **Verificado: no bloquea, y no hacía falta
arreglar nada.**

`check_purchase` calcula la participación **resultante** —
`P / (total + P)` — y **no mira `breaches` para decidir**. La infracción
viva de Yamal no gatea ninguna compra.

Con la plantilla del 06/09 —49.540.000 € en 14 fichas, Yamal al
**42,81 %** con el tope en el 35 %— el tope por compra sale en:

```
P <= 0,35 · 49.540.000 / (1 - 0,35)  =  26.675.384 EUR
```

Muy por encima de cualquier cosa que haya en el mercado. Probado contra
las cuatro compras plausibles de hoy (250.000, 1.730.000, 2.930.000 y
3.670.000): **ninguna se acota**.

Como el encargo decía —*"si ya estaba bien, dilo y no toques nada"*— no
he tocado nada. Sí he dejado guardia
(`test_una_infraccion_viva_no_bloquea_las_compras`) para que no pueda
volverse al revés sin que la verja lo cante.

---

# BLOQUE 1 — La puja deja de ser adivinable

`src/analysis/bid_jitter.py`. Módulo propio, aplicado **al final**, en
la ruta del ejecutor, después de que el motor haya decidido y después de
que el presupuesto haya dado el visto bueno.

**`optimal_bid` no se ha tocado.** Hay guardia que lo comprueba: si
algún día aparece `bid_jitter` dentro de `rival_bid_model.py`, la verja
se pone roja.

```
J = clamp(int(precio · 0,005), 1.000, 50.000)
semilla = sha256(f"{player_id}:{fecha}:{jornada}:{SALT}")
desvío  = semilla mod (J + 1)
```

**Límites duros**, en este orden: nunca por encima del techo, nunca por
encima del tope por operación, nunca por debajo de `precio + 1`.

**Nada de números clavados:** si el importe acaba en `0000` o `5000` se
le suma entre 1 y 999 (y si eso rompiera el techo, se resta).

**Reproducible dentro, impredecible fuera.** El mismo jugador el mismo
día da el mismo importe — que es lo que impide que el reintento de un
ciclo genere dos pujas distintas, justo lo que
`test_bid_deduplication_v1` existe para evitar. Al día siguiente cambia.

## Lo que cuesta el seguro, en euros, sobre los objetivos de hoy

**Hoy cuesta 0 €**, porque no hay ninguna puja. Simulado sobre los 20
objetivos como si se pujara `precio + 1` por todos:

| | |
|---|---:|
| Suma de precios | 40.280.000 € |
| Coste total del desvío | **95.787 €** |
| Coste relativo | **0,238 %** |

Ejemplos: Pedri +30.349 €, Bellerín +11.836 €, Pathé Ciss +10.235 €,
Amatucci +3.541 €.

Está en pantalla, en MERCADO, debajo de la columna PUJARÍAMOS: el
importe real arriba y `limpia X · +Y` debajo. Si en un mes ha costado
más de lo que ha ganado, se ve y se apaga.

## La sal: te toca a ti

```
BORDALAS_BID_SALT
```

Sin ella el módulo funciona con la constante de respaldo — degradar,
nunca romper. **Pero una sal escrita en el código es una sal
publicada**: si el repositorio es público, cualquiera lee
`DEFAULT_SALT` y vuelve a enumerar nuestras pujas con un paso más.

La sal de verdad tiene que ir a los secrets de GitHub y llegar por
entorno. **Añadirla es tuyo**: yo no toco el workflow. La línea sería,
en el bloque `env:` de `bordalas-live.yml`:

```yaml
  BORDALAS_BID_SALT: ${{ secrets.BORDALAS_BID_SALT }}
```

## Sobre los 7 € de Natan

**No hay ninguna teoría sobre Pollo en el código ni en la pantalla**, y
la guardia lo dice explícitamente. El libro de pujas tiene **una** puja
registrada: con n=1 no se demuestra que nadie nos lea. Los siete euros
pueden ser casualidad o dos valoraciones que coinciden.

Se hace porque el seguro cuesta el 0,24 % y el incendio cuesta perder
cada subasta por siete euros.

---

# BLOQUE 3 — El orden de prioridad

Implementado en `deployment.signing_priority`, y el tablero ordena por
él antes que por valor esperado:

```
0  llena ficha Y mejora el once
1  llena ficha Y se revaloriza
2  cualquier otro fichaje
3  especulación pura
```

Con el despliegue apagado el escalón vale igual para todos y el orden es
exactamente el de antes.

**Sobre "repartir en varias operaciones":** no hace falta ningún
mecanismo nuevo. El ciclo ejecuta una acción por vuelta, así que ordenar
ya reparte — la primera compra cambia el saldo y el reparto de
concentración antes de que se evalúe la segunda.

**Lo que no se ha copiado de Pollo:** nada de su posición ni de su ritmo
de puntos, como pedía el encargo. Solo ocupar el balance.

---

# Lo que no hice, y por qué

**No ficho a Amatucci.** El encargo lo daba por hecho; la medición dice
que vale 2.716.842 € y cuesta 3.670.000 €. Gana la medición, como manda
la regla 6. Si prefieres comprarlo igualmente —tesis de que el mercado
lo va a revalorizar por encima de nuestra estimación— eso es una
decisión tuya y se hace a mano, no aflojando una regla.

**No toqué el workflow.** Las dos líneas que hacen falta ahí
—`BORDALAS_BID_SALT` y, si algún día quieres apagarlo,
`DEPLOYMENT_ENABLED: "0"`— están escritas arriba para copiar.

**No subí ningún tope.** `MAX_SAFE_DEBT` y los seis umbrales
intocables siguen donde estaban; hay guardia que lo comprueba.

**No intenté fichar hasta llenar las 22 fichas.** Los 8 huecos son cota
inferior, no objetivo. Y hoy la cuestión es otra: no hay nada que
comprar a estos precios.

**Una corrección al encargo:** la cola pendiente dice que
`lineup_engine.py:170-177` sigue confundiendo "jornada equivocada" con
"tablero vacío". **Ya está arreglado** desde el 05/09: hay tres mensajes
para tres causas y guardia (`test_motivo_del_tablero_v1`). El encargo se
escribió sobre esa suposición y la medición dice que no.

---

# Lo que va a pasar en el próximo ciclo

Con esto encendido y el mercado de hoy: **Pepe no compra**, y ahora el
motivo sale escrito objetivo por objetivo en vez de esconderse detrás de
un `SUPERA_PRESUPUESTO` que ya no es cierto.

Lo que sí ha cambiado, y se notará el día que aparezca el candidato
correcto:

- un fichaje ya no se mide contra 973.594 € sino contra 5.350.683 €;
- cinco jugadores que salían a cero ahora tienen valor por llenar ficha,
  y entrarán en cuanto su precio baje por debajo de ese valor;
- cuando entren, irán antes que cualquier especulación;
- y la puja no se podrá enumerar desde la curva publicada.

**La frase para mañana:** el bolsillo estaba mal elegido y ya está
arreglado, pero el bolsillo no era lo que frenaba las compras. Lo que
frena hoy es que los cinco candidatos que caben en el bolsillo de fichar
cuestan entre un 12 % y un 51 % más de lo que valen por la vía que los
pagaría. Pollo compró siete jugadores a prima cero; nosotros no tenemos
hoy en el tablero ninguno a prima cero.
