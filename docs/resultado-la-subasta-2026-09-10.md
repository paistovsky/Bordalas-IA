# LA SUBASTA — resultado

Rama `subasta/estar-a-las-siete-menos-cinco`, desde `main` (`c59e454`).
**97 de 97 en verde. Ni una llamada a Biwenger, ni de lectura.** Sin push.

**No he pujado nada.** Ningún umbral movido: el listón sigue en 3 %, `MAX_SAFE_DEBT`
y el tope por operación intactos. Lo que cambia es **cuándo** y **cuántas**.

---

# BLOQUE 0 — La medición, y contradice el encargo

La regla 8 dice que gana la medición. **Gana la medición.**

Todo sale del tablón que el ciclo ya guarda: **156 compras al Computer en 27 días,
con la lista de pujas de cada una**. No hay que estimar la competencia: está
escrita.

## 0.1 — Cuántos se llevan sin competencia

```
  SIN NINGUN RIVAL:  67 de 156  (43 %)

  RIVALES   SUBASTAS
        0         67
        1         54
        2         35
```

**El 43 % se va sin que nadie puje.** Hasta aquí, el dueño tiene razón.

**Pero de esos 67, solo 16 venían subiendo** (de los 55 con histórico: **29 %**).

```
  -> 0,59 jugadores AL DIA sin competencia Y subiendo
```

**No son seis cada mañana: es uno cada dos días.** El encargo estaba diez veces por
encima.

Y no son baratos:

| Los 16 que valen | |
|---|---:|
| Precio mediano | **4.550.000** |
| Suben (mediana) | 30.000 /día |
| Caben en el tope por operación (998.962) | **2 de 16** |

Es la misma pared que el mercado de rivales: el material existe y el bolsillo
pequeño no llega.

## Pero el premio es otro, y es mucho mejor

| | Prima mediana | p90 |
|---|---:|---:|
| **Sin rival** | **+1,33 %** | +16,45 % |
| **Con rivales** | **+8,30 %** | +169,59 % |

**Siete puntos de diferencia.** Sobre un jugador de 4,5 M eso son **~318.000 EUR
por operación**.

**El negocio no es el que sube 20.000 al día: es no pagar la prima de la puja
disputada.** Eso reordena la idea entera — y la hace más valiosa, no menos.

## El reparto por comprador

| Comprador | Compras | Prima mediana | Sin rival |
|---|---:|---:|---:|
| Pollo17 | 39 | 2,74 % | 19 |
| Luismi_Haz | 32 | 4,10 % | 14 |
| Manzagool | 13 | 5,24 % | 9 |
| **Pepe Bordalás** | **11** | **8,51 %** | 4 |
| DiosMande… | 9 | 1,88 % | 3 |
| Prinzipote | 6 | **0,10 %** | 5 |
| Mex | 5 | 10,43 % | 5 |

**Pepe paga la segunda prima más alta de la liga.** Pollo y Luismi, que son los que
el dueño dice que hacen la jugada, pagan la mitad o menos. Prinzipote paga **0,10 %**:
compra seis veces y casi siempre solo.

**Y un cabo suelto que dejo apuntado:** el libro de pujas tiene **una** entrada,
pero el tablón registra **11 compras nuestras** y la inteligencia de rivales dice
`lost_bids: 9`. Tres cuentas distintas del mismo concepto. No lo he tocado —no era
el encargo— pero huele a la familia de siempre.

## 0.2 — ¿Una puja pendiente bloquea el saldo?

**Ya estaba medido en el propio código, el 16/08**, y con snapshots de 30 segundos
de diferencia:

```
  17:01:54   balance 239.968   maximumBid 12.404.968   pujas 0
  -> puja de 480.000 (HTTP 200)
  17:02:24   balance 239.968   maximumBid 11.924.968   pujas 1
```

**El balance no se mueve. `maximumBid` baja exactamente el importe de la puja.**

Para poner cuatro pujas hace falta `maximumBid` ≥ la suma de las cuatro, aunque
solo se gane una. **No hace falta tener el dinero en caja: hace falta tenerlo en
capacidad de compra.**

## 0.3 — ¿Y si ganas más jugadores que fichas libres?

**No lo he probado, y no lo voy a probar.** Averiguarlo exige ganar de más a
propósito, y eso solo se puede hacer en vivo.

**El tope queda en el número de huecos libres**, que es lo seguro, y hay guardia.

Los huecos salen de la definición que ya usa la casa desde el 25/08
(`count_free_slots`): **la plantilla más grande de la liga menos la nuestra**, y
allí está escrito que es un **suelo, no el tope de Biwenger**. Hoy: 21 − 14 = **7**.

## 0.4 — ¿Varias pujas en un mismo ciclo?

**Es decisión nuestra, no un límite de Biwenger.** En
`v10_full_autonomous_live.run_full_autonomous_cycle` hay una bandera `write_used`
que corta tras la primera escritura. Nada en la API lo impide.

---

# BLOQUE 1 — El reloj

**El cron actual es `7 * * * *`** (una vuelta por hora, puesto el 08/09 tras el
bloqueo). En Madrid eso son las **06:07 y 07:07**: 53 minutos antes del cierre, y
7 después.

## El cron que pondría

```yaml
  schedule:
    # LA VENTANA DEL RESET (10/09/2026)
    #
    #   El reset del Computer es a las 07:00 de Madrid. El cron
    #   de Actions es UTC, y Madrid cambia de huso:
    #
    #       verano (CEST, UTC+2)   07:00 local = 05:00 UTC
    #       invierno (CET, UTC+1)  07:00 local = 06:00 UTC
    #
    #   Por eso las horas van en pareja "4,5" y "5,6": una cae en
    #   la ventana y la otra una hora antes o despues, que no
    #   molesta. Asi vale todo el año sin acordarse de cambiarlo
    #   en octubre.
    #
    #   Y TRES vueltas, no una: el cron de Actions se retrasa con
    #   frecuencia -a veces diez minutos-. Una sola a las 06:55
    #   se pierde entera con un retraso normal.
    - cron: "40,48,55 4,5 * * *"

    # Justo despues del reset: leer que se gano y que se perdio.
    # Es lo que alimenta el libro de pujas, que hoy tiene UN
    # registro.
    - cron: "10 5,6 * * *"

    # El resto del dia, una barrida por hora: ofertas y once.
    - cron: "25 7-22 * * *"
```

## Lo que cuesta: exactamente lo mismo

| | Vueltas/día | Peticiones/día |
|---|---:|---:|
| Cron actual `7 * * * *` | 24 | **181** |
| **Cron propuesto** | **24** | **181** |

**Mismo presupuesto, distinto sitio.** No hay nada que decidir entre ahorrar y
llegar a tiempo: se puede tener las dos cosas.

*(Y la sonda ya no supone las vueltas: las **lee del propio workflow**. Estaba
escrito 48 a mano y el dueño lo bajó a 24 el 08/09; el número del informe se había
quedado viejo sin que nadie se enterara.)*

## Una duda honesta sobre la premisa

El dueño dice "cinco minutos antes entro y le meto una puja". **Si las pujas vivas
son invisibles —y la regla 12 dice que sí, cerrada el 21/09—, esperar no nos
esconde de nadie: nadie nos ve de todas formas.**

Lo que sí gana esperar es **decidir con la información más fresca del día** y tener
el dinero comprometido menos rato. Es una razón buena, pero es otra razón. Lo digo
por si el plan se apoyaba en la primera.

---

# BLOQUE 2 — Pujar por varios

`src/analysis/la_subasta.py`, **en sombra**. `enabled` sale `False` a propósito.

- **Se ordena por ganancia esperada POR EURO comprometido**, no por ganancia. Con
  dinero limitado, un jugador que gana 41.000 con 410.000 vale diez veces más que
  otro que gana lo mismo con 4,1 M. Hay guardia con los dos.
- **Nunca más pujas que fichas libres.**
- **Las barandillas sobre el peor caso**: el cuatro-por-club se cuenta sobre la
  cesta entera, no puja a puja. Dos pujas que por separado no concentran nada
  dejan dos del mismo club si entran las dos.
- **La ventana son 15 minutos**, no 5: un retraso normal de Actions se come una
  ventana de cinco.

## El tope, que sale de una cuenta y no de un número

> *lo que se pueda deshacer el viernes aunque el mercado haya caído un 5 %*

```
    Si se compra con deuda D y el mercado cae un 5 %,
    al vender se recupera D × 0,95. Faltan D × 0,05,
    y eso sale de la caja libre.

        D × 0,05 ≤ caja_libre
        D ≤ caja_libre / 0,05
```

Hoy: 258.807 / 0,05 = **5.176.140**. Como el bolsillo son 2.497.407, **manda el
presupuesto**. Si la caja sube, el tope sube solo.

---

# BLOQUE 3 — El desvío, medido y corregido

**El encargo se quedaba corto.** Sobre las 16 compras sin rival y subiendo:

```
        PRECIO   SUBE/DIA  DESVIO HOY  % DE LA SUBIDA
     1.760.000     10.000       8.800             88 %
     7.620.000     30.000      38.100            127 %
    10.230.000     70.000      50.000             71 %

  MEDIANA: el desvio es el 52 % de lo que el jugador sube en UN DIA
           y el 17 % de lo que sube en tres
```

**El seguro cuesta una quinta parte del negocio**, y en el peor caso más de lo que
el jugador gana en un día.

## El número nuevo: 10 % de la ganancia esperada

| Fracción | Desvío mediano | % de la ganancia a 3 días | Rango |
|---|---:|---:|---|
| 5 % | 4.500 | 5 % | 1.500–18.000 |
| **10 %** | **9.000** | **10 %** | 1.550–36.000 |
| 15 % | 12.450 | 15 % | 1.550–40.500 |
| Hoy (0,5 % del precio) | 18.775 | 17 % | 1.550–50.000 |

**Por qué 10 y no 5**, que es el otro lado del encargo: Biwenger mueve los precios
en escalones de 10.000, y **9.000 es casi un escalón entero** — quien quiera
asegurarse de superarnos tiene que subir un escalón completo, no unos euros. Con el
5 % el desvío mediano baja a 4.500, medio escalón, y superarnos empieza a salir
barato.

**Lo que no cambia:** sin ganancia esperada, el desvío es el de siempre. Y el tope
del precio sigue siendo el límite absoluto — **la ganancia solo puede apretar,
nunca aflojar**. Hay guardia de las dos cosas.

Y ahora se publica `jitter_percent_of_gain`: **lo que costó el seguro contra lo que
aseguraba**, que es la única forma de saber si es caro. Antes solo salían los euros.

---

# BLOQUE 4 — Qué se vería, y qué habría pujado hoy

```
  Quedan 32 min para el reset: la ventana son los ultimos 15.
  Plantilla: 14; la mayor de la liga tiene 21 -> 7 fichas libres
  Caja libre: 258.807 EUR    Bolsillo: 2.497.407 EUR

  Candidatos con decision PUJAR: 0 de 20

  Ninguna puja: 0 candidatos y ninguno pasa.
  Tope de la ventana: manda el presupuesto, 2.497.407 EUR.

  ENCENDIDO: False  (observador: True)
```

**Hoy no habría pujado por nadie: los 20 del escaparate dan cero pujables.** Es el
mismo cero de las últimas noches, y no lo arregla la subasta — lo arregla que algo
pase el listón.

La pantalla publica lo que pediste: por quién, cuánto, por qué ese importe, cuánto
compromete, cuántas fichas ocuparía si ganara todas, cuánto falta para el cierre, y
un hueco `last_reset` para qué ganó y qué perdió.

---

# LO QUE ENTRA EN EL COMMIT

`git status` antes. **Diez ficheros, y dos no son míos:**

```
?? src/analysis/la_subasta.py              la ventana, la cesta, el peor caso
?? src/analysis/test_la_subasta_v1.py      24 guardias, fixture entero
?? scripts/medir_la_subasta.py             el bloque 0, sobre el tablon
?? scripts/que_pujaria_en_el_reset.py      el bloque 4
 M src/analysis/bid_jitter.py              el desvio, pagado con la ganancia
 M src/analysis/acquisition_board.py       le pasa la ganancia esperada
 M scripts/contar_peticiones_del_ciclo.py  lee el cron del workflow
 M scripts/run_validation_gate.py          + 1 guardia
?? docs/resultado-la-subasta-2026-09-10.md
```

**Y dos encargos tuyos sin commitear** que `git add -A` va a recoger:
`ENCARGO-LA-SUBASTA-2026-09-10.md` (éste) y **`ENCARGO-ADELANTARSE-2026-09-09.md`,
que no he leído ni ejecutado** — estaba en el árbol y no era el de esta noche. Lo
digo por si esperabas otra cosa.

**El workflow no se ha tocado.**

---

# UN FALLO MÍO, OTRA VEZ EL MISMO

`.replace(",", ".")` sobre una frase entera se comió una coma de la prosa: *"Con
258.807 EUR de caja libre**.** una caida del 5 %"*. **Quinta vez de esta familia en
el proyecto.** Arreglado con un `_euros()` que formatea el número y no toca la
frase, y el comentario dice por qué existe.

---

# LO QUE NO HE HECHO

**No he pujado, ni he leído nada de Biwenger.** Todo sale del tablón en disco y de
`status.json`.

**No he probado el 0.3.** Exige ganar de más a propósito, en vivo.

**No he enganchado la subasta al ciclo.** Está en sombra: el primer reset de verdad
se mira con los números delante, como dice el encargo.

**No he tocado el cron.** Las líneas están arriba.

**No he investigado las tres cuentas del libro de pujas** (1 registro, 11 compras,
9 pujas perdidas). No era el encargo.

---

**La frase para mañana:** la idea es buena pero por otra razón. **No son seis
jugadores gratis cada mañana: son 0,59 al día** —uno cada dos días— y con precio
mediano de 4,5 M. **El premio no es el que sube 20.000: es no pagar la prima.**
Estar solo cuesta **+1,33 %**; con rivales, **+8,30 %**. Siete puntos, que sobre un
jugador de 4,5 M son **318.000 EUR por operación** — y Pepe hoy paga la segunda
prima más alta de la liga. El cron que llega a tiempo cuesta **exactamente las
mismas 181 peticiones** que el de ahora. Y el seguro de la puja, que se llevaba el
**52 % de lo que un jugador sube en un día**, pasa a costar el 10 % de la ganancia.
