# La divergencia — resultado de la noche del 06→07/09/2026

Rama `divergencia/2026-09-07`, subida. `main` sin tocar.

**Puerta: 68 de 68 en verde.** Eran 66 al empezar. Tres commits.
`npm run build` pasa. **Nada desplegado.**

---

# 1. ¿Momento o reversión?

## Momento. Y no por poco: es la propiedad más fuerte de este mercado

El precio de Biwenger **no es un paseo aleatorio**. Se mueve en rampas
de varios días que casi nunca se giran.

De los 554 jugadores con los seis días completos:

| | |
|---|---|
| **No cambian de dirección ni una vez en 6 días** | **464 (83,8 %)** |
| Cambian una vez | 89 |
| Cambian dos veces | 1 |

Y día a día, sobre los 1.412 pares en que el jugador se movió la
víspera:

| Lo que hizo ayer | Lo que hace hoy |
|---|---|
| **Subió** | sube el **85,1 %**, baja el 5,4 % |
| **Bajó** | baja el **90,7 %**, sube el 1,6 % |
| No se movió | sigue quieto el 87,8 % |

**Correlación entre el cambio de hoy y el de mañana: r = +0,90**
(n=1.412, t=+77). Entre los que se mueven los dos días, r = +0,91.

Se ve a ojo en las series reales:

```
Yeremay    9,17 → 9,11 → 8,72 → 8,39 → 8,16 → 8,09   (seis bajadas)
Agirrezabala 1,39 → 1,64 → 1,87 → 2,07 → 2,25 → 2,43 (seis subidas)
Sørloth    5,35 → 5,12 → 4,83 → 4,59 → 4,43 → 4,32
```

Eso no es un mercado de gente comprando y vendiendo: es un algoritmo
repreciando despacio y en la misma dirección.

## El control descarta la explicación fácil

El mercado subió los cinco días (+0,63 %, +0,60 %, +0,72 %, +0,32 %,
+0,78 % de media). Así que "subió y sigue subiendo" podría ser solo
que sube todo.

No lo es. Descontando el movimiento común y mirando solo a los que se
movieron:

- De los que **subieron** ayer, el **59,9 %** lo hace mejor que el
  mercado hoy.
- De los que **bajaron** ayer, lo hace mejor que el mercado el
  **0,5 %**. Cinco de mil.

Que casi todo suba no explica que el 90,7 % de los que bajan sigan
bajando.

## Y no es un efecto del arranque de temporada

La ventana incluye la jornada 1 (15/08), cuando el mercado se
recalibra. Partido en dos:

| | n | r | subió→sube | bajó→baja |
|---|---|---|---|---|
| Antes de la jornada 1 | 725 | +0,955 | 94,1 % | 91,6 % |
| Después de la jornada 1 | 333 | +0,876 | 91,8 % | 85,0 % |

Se debilita un poco después, y sigue siendo abrumador.

## Qué significa para la estrategia

**1. La `Tend` de FutbolFantasy es una señal buena, y va en la
dirección obvia.** Días consecutivos subiendo → sigue subiendo. Tras 1
día de racha continúa el 92 %; tras 2, el 94 %.

**2. Comprar al que acaba de bajar es comprar un cuchillo cayendo.**
Es la lectura contraintuitiva y la más útil: en este mercado el que
baja **no está barato, está bajando**, y va a seguir. La "oportunidad"
de comprar caídas no existe aquí.

**3. El modelo de Pepe tiene la forma correcta.**
`estimate_resale_price` proyecta hacia delante el ritmo de ayer, y eso
es exactamente lo que hay que hacer en un mercado con r = +0,90. **El
problema no es el modelo: es que el número por jugador no le llega.**

Sobre la foto del 04/09, la ganancia esperada sale como el precio por
una tasa fija, idéntica a cuatro decimales:

```
Bardeli        2.902 € / 1.658.581 = 0,1750 %   (ayer +6,06 %)
André Almeida  1.442 €   / 824.265 = 0,1749 %   (ayer +17,07 %)
Nico Guillén   1.512 €   / 864.473 = 0,1749 %   (ayer −2,33 %)
```

Tres comportamientos opuestos, la misma tasa. **No determiné la
causa** —`build_velocity_lookup()` sí devuelve 403 velocidades
distintas y `acquisition_valuation.py:525` sí se las pasa— y no entré
a averiguarlo porque es el motor que tengo prohibido tocar. Pero
ahora está medido lo que cuesta: se está tirando la señal más
predictiva que existe en este mercado.

## Lo que estos datos NO pueden decir

**Nada sobre los giros**, que es justo lo que la divergencia
pretende anticipar.

Solo 89 jugadores giran alguna vez en la ventana, y las rampas largas
están cortadas por el final de los datos: la "rampa de 5 días" que
aparece 123 veces no terminó, es que se acabaron los días. Cualquier
número sobre "qué avisa de un giro" saldría de una muestra que no
existe.

**Muestra:** 6 días (12–17/08/2026), 554 jugadores, 2.242 pares.
Tres semanas de antigüedad y una sola fase de mercado. Suficiente para
la pregunta del momento —el efecto es enorme y aparece en las dos
mitades— e insuficiente para la de los giros.

---

# 2. El registro de la divergencia

`data/intelligence/divergence_ledger.json`. Ya tiene **288
observaciones de hoy, 16 de ellas divergentes.**

**`demand_net` = compras 24 h − ventas, las dos de Comuniate.** Es la
única de las cuatro fuentes que publica demanda, así que es **una
medida, no un consenso**, y cada fila lo dice en `demand_source`.

## Sin grupo de control no hay resultado

Cada refresco apunta **a los divergentes y a todos los demás**. Que un
divergente suba no dice nada si ese día subieron todos. El estudio
compara siempre los dos grupos a 3 y 7 días, y mientras no haya 20 de
cada dice *"todavía no hay muestra"* y **no pinta ninguna diferencia**.

## Lo que el estudio del punto 1 obligó a añadir

El encargo no lo pedía, y sin él el libro no habría servido: **cada
observación guarda `trend_days`**, los días que lleva la rampa.

Con r = +0,90, una divergencia *"precio baja, demanda sube"* no es una
oportunidad porque el precio esté barato — es **una apuesta a que una
rampa muy persistente se va a girar**. Sin saber cuántos días lleva
esa rampa, dentro de un mes el libro no podría contestar a lo único
que importa: si la demanda avisa del giro antes de que ocurra.

En la foto de hoy ya se ve el caso: **Sangaré y Lookman llevan siete
días subiendo con la demanda desplomada** (−60 y −57 puntos). Si la
hipótesis vale para algo, es para esos dos.

---

# 3. El arreglo de la puerta

Las 66 guardias estaban escritas a mano en el workflow, y el script
las leía de ahí. Ahora la lista está en el script y el workflow le
llama.

**Había una trampa:** sustituir las líneas sin más habría dejado al
script leyendo un YAML recién vaciado — habría dicho *"no hay tests
que correr"* y CI se habría caído. La lista se mueve primero.

Y se comprobó lo que pedía el encargo, que es la mitad que importa:
**una guardia rota devuelve ≠ 0 y una buena devuelve 0**, ejecutándolo
de verdad. Para eso hay un `--solo` nuevo que corre una sola guardia
en vez de esperar a las 68.

---

# 4. Lo que me sorprendió

**1. Que el efecto fuera tan grande.** Esperaba una autocorrelación
débil, de las que hay que defender con un test estadístico. Salió
r = +0,90 y el 83,8 % de los jugadores sin girar ni una vez. No hace
falta estadística para ver eso: se ve mirando cuatro series.

**2. Que la primera medición estuviera mal, y por un motivo bonito.**
La primera pasada dio r = +0,75 sobre *todos* los pares. Era en buena
parte un artefacto: el 37,3 % de las observaciones son de jugadores
que no se mueven, y una masa de puntos en (0,0) con la media en
(+0,63, +0,63) infla la correlación sola. Condicionar a "se movió
ayer" lo subió a 0,90 y lo hizo interpretable. **La primera versión
daba un número más bajo por el motivo equivocado.**

**3. Que el hallazgo desinfle la hipótesis que venía a apoyar.** El
encargo salía de la divergencia, y lo primero que dice el estudio es
que apostar contra el precio es apostar contra lo más fuerte que hay
en este mercado. No invalida la hipótesis —los giros existen, 89
jugadores giraron— pero la reencuadra: **la divergencia solo puede
valer para detectar el final de una rampa, no para contradecirla.**
Y eso es una pregunta mucho más estrecha que la que el encargo
planteaba.

**4. Que la conclusión sea que el motor está bien y la tubería mal.**
Iba buscando si había que cambiar la forma de estimar la reventa. La
respuesta es que no: proyectar el ritmo de ayer es lo correcto aquí.
Lo que falla es que ese ritmo, medido y disponible, no llega al
cálculo.

---

# 5. Lo que se quedó fuera, y por qué

**Por qué la ganancia esperada sale como una tasa fija.** Está
localizado y medido, no diagnosticado. Vive en
`player_value_engine.py` / `acquisition_valuation.py`, que el encargo
prohíbe tocar. Es lo primero que yo miraría mañana: el estudio dice
que ahí se está tirando la mejor señal del mercado.

**Qué anticipa un giro.** No hay muestra. Dicho con esas palabras en
el punto 1, y es exactamente lo que el libro nuevo empieza a acumular.

**Conectar la divergencia a cualquier decisión.** Prohibido, y
vigilado por guardia: ninguna ruta de decisión importa el módulo, y
hay un test que busca las palabras "predicción" en él.

---

## Cómo quedó

```
rama          divergencia/2026-09-07, subida
main          sin tocar
puerta        68/68 en verde  (66 al empezar, 2 guardias nuevas)
commits       3
frontend      npm run build OK · NO desplegado · dist/ intacto
libro         288 observaciones apuntadas, 16 divergentes, 0 cerradas
              (las primeras se cierran dentro de tres días)
dinero        cero cambios
```

**La frase para mañana por la mañana:** el precio de Biwenger tiene
memoria, y mucha. El que sube sigue subiendo el 85 % de las veces y el
que baja sigue bajando el 91 %. Pepe ya proyecta eso correctamente —
solo que con el mismo número para todos.
