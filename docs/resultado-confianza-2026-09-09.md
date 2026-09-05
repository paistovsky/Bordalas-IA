# Cada apuesta con su confianza — resultado de la noche del 08→09/09/2026

Rama `confianza/2026-09-09`, subida. `main` sin tocar.
**Puerta: 71 de 71 en verde.** Eran 70 al empezar. Tres commits.
`npm run build` pasa. **Nada desplegado.**

**Todo en sombra. Ninguna decisión cambia.** El motor sigue valorando
exactamente igual que ayer; el esquema nuevo se publica al lado.

---

# 1. La lista de lo que cambiaría

Los 22 candidatos de la foto de producción del 04/09, con la prima
medida de ese día (`positive_ratio` 0,745 sobre 102 ventas).

## Los 3 que cambian de vía

| Jugador | Precio | Hoy | Con su confianza | Cambio |
|---|---|---|---|---|
| **Bardeli** | 1.650.000 | 1.671.780 · Computer | **1.740.558 · tendencia** | **+68.778** |
| **Yusi Enríquez** | 1.140.000 | 1.155.048 · Computer | **1.163.462 · tendencia** | +8.414 |
| **Mariano** | 4.210.000 | 4.265.572 · Computer | **4.272.968 · tendencia** | +7.396 |

Son exactamente los tres que tienen ritmo medido y suben con fuerza.
Bardeli es el caso que abrió todo esto: **+4,62 %/día, +138.628 € de
revalorización proyectada, y hoy vale cero por esa vía.**

## Los 11 que se quedan en la vía del Computer, y bajan

| Jugador | Hoy | Con su confianza | Cambio |
|---|---|---|---|
| Expósito | 5.197.716 | 5.178.701 | −19.015 |
| Gustavo Puerta | 3.444.880 | 3.432.277 | −12.603 |
| Natan | 3.049.732 | 3.038.575 | −11.157 |
| Joaquín Muñoz | 2.026.400 | 2.018.986 | −7.414 |
| Camavinga | 1.752.836 | 1.746.423 | −6.413 |
| Thiago Fernández | 1.418.480 | 1.413.290 | −5.190 |
| Nico Guillén | 871.352 | 868.164 | −3.188 |
| Álvaro Fidalgo | 658.580 | 656.170 | −2.410 |
| Rubén Sánchez | 303.960 | 302.848 | −1.112 |
| Jon Pacheco | 192.508 | 191.803 | −705 |
| Gamón | 172.244 | 171.613 | −631 |

Bajan poco y bajan todos lo mismo en proporción: es el descuento de
una vía que **falla una de cada cuatro veces** y hasta hoy no pagaba
nada por ello.

## Los 6 que no se mueven

Odysseas, Calero, Álex Padilla, Iñaki Rupérez, Diego Murillo y André
Almeida siguen a cero: los frenó el freno de anoche por venir bajando
o estar quietos. La confianza no los resucita, y no debería.

**Balance: 3 suben, 11 bajan, 6 igual.**

---

# 2. ¿Sigue ganando la vía del Computer en 21 de 22?

**No. Se reparte.**

| | Hoy | Con su confianza |
|---|---|---|
| Vía del Computer | **14 de 14** | **11 de 14** |
| Vía de tendencia | 0 | **3** |
| Sin valor (frenados) | 6 | 6 |

De ganar en el 100 % de los candidatos con valor pasa al 79 %. Y los
tres que pierde no los pierde por azar: **son los tres únicos con un
ritmo de subida medido que pasa el freno.** Expósito también tiene
ritmo (+0,39 %/día) y se queda en la vía del Computer, que es lo
correcto: con ese ritmo la tendencia no da para más.

O sea que el reparto sale proporcionado al momento real de cada
jugador, que era exactamente lo que se buscaba. **El termómetro dice
que el arreglo hace lo que esperábamos.**

Confirmado también sobre el `status.json` recién generado con datos
locales: 9 candidatos con valor, la vía del Computer pasa de 9 a 6 y
la de tendencia se lleva 3.

---

# 3. De dónde sale cada confianza

## La racha: la continuación medida, no un número inventado

Del estudio del 07/09 sobre 554 jugadores:

```
se movió ayer, sin racha previa    85,1 %   (n=846)
1 día de racha                     92,0 %   (n=264)
2 días de racha                    94,1 %   (n=237)
3 días o más                       73,8 %   (n=351)
```

La confianza de una apuesta de precio **es** esa probabilidad. No hubo
que diseñar una forma: ya estaba medida.

**Y no es monótona, que es lo contrario de lo que suponía el
encargo.** *"Una racha de seis días confirmada por tres fuentes es más
fiable que un día suelto"* — los datos dicen que no. La continuación
sube hasta el segundo día y **cae al tercero**, del 94,1 % al 73,8 %.

Tiene sentido: una rampa que lleva tres días está más cerca de
agotarse que una de uno. Y es la misma medición que sostiene el aviso
de *"racha sin gasolina"* de anoche. Darle más confianza a una racha
larga habría ido contra nuestros propios números.

## Las fuentes suman poco, y hay que decir por qué

El 06/09 se midió que las tres fuentes de precio copian el mismo
número de Biwenger: **cero discrepancias de dirección en 288
jugadores**. Su acuerdo es redundancia.

Así que *"confirmado por tres fuentes"* no dice que el movimiento sea
más real: dice que lo hemos **leído** bien. Es confianza en la lectura
—contra un fallo de parseo o de emparejamiento—, no en el mercado. Por
eso suma 0,02 por fuente extra con techo en 0,04. Tratarlo como
corroboración sería contar tres veces el mismo dato.

## El premium: su ratio medido, encogido por la muestra

`positive_ratio` = 0,745 → 76 de 102 ventas con precio. Encogido hacia
0,5 con peso `n/(n+12)`, queda en **0,719**. Con las 12 ventas mínimas
que exige el propio medidor, el ratio y el prior pesarían lo mismo.

*(El encargo cita 0,778 sobre 90 ventas; en la foto que tengo son
0,745 sobre 102. Uso la medida que trae el bloque, no una constante.)*

---

# 4. Lo que me sorprendió

## La confianza se aplicaba al capital, y eso no estaba en el encargo

Puse las confianzas correctas y **todas las vías cayeron a cero**. Las
once, las catorce, todas.

El motivo no era el número. Es dónde se multiplica:

```
maximo = (objetivo − ganancia × margen) × confianza
```

Eso multiplica el **precio entero que estaríamos dispuestos a pagar**.
Con la vía del Computer, cuya ventaja es del 1,76 %, una confianza de
0,72 deja el máximo en **1.202.010 €** sobre un precio de 1.650.000:
por debajo del propio precio → `MARGEN_INSUFICIENTE` → cero.

**Cualquier confianza por debajo de 1 anula la vía.** Por eso la vía
del Computer no llevaba ninguna: con esta aritmética, ponérsela era
apagarla.

Y la corrección es conceptual, no numérica: **el principal no está en
riesgo.** Si la apuesta falla sigues teniendo un jugador que vale
aproximadamente el precio de mercado; no se evapora el dinero. Lo
incierto es la **ganancia**:

```
maximo = precio + ganancia × confianza × (1 − margen)
```

Con Bardeli: la vía del Computer pasa de 0 a 1.665.660 y la de
tendencia a 1.740.558. Y ahí la tendencia por fin gana.

**Solo está en la sombra.** Cambiar esa semántica en el motor mueve
dinero y no era lo que se pedía.

## El último metro, otra vez

`value_candidate` calculaba la sombra perfectamente y la columna de la
pantalla salía **vacía**: `acquisition_board` copia los campos uno a
uno y le faltaba la línea.

Lo destapó mirar el `status.json` de verdad — no el código. Mis
propias guardias de pantalla comprueban que el JSX *lee* el campo,
nunca que el backend lo *publique*. Hay guardia nueva para las dos
mitades.

Es la decimotercera vez que este repo pierde un dato en el último
metro, y la segunda que me pasa a mí esta semana.

## El encargo se equivocaba en una premisa, y los datos lo dijeron

*"Una racha de seis días es más fiable que un día suelto"* es
intuitivo y falso en este mercado. Escribirlo como el encargo lo
sugería habría metido una confianza que sube donde la realidad baja —
y encima habría contradicho el aviso de racha sin gasolina que yo
mismo había implementado la noche anterior con los mismos números.

## El efecto es pequeño en euros y grande en criterio

Las bajadas son de 600 a 19.000 € sobre valoraciones de millones:
décimas de punto porcentual. Las subidas, salvo Bardeli, también.

Pero eso es mirar el número equivocado. Lo que cambia no es cuánto
vale cada uno: es **qué apuesta está haciendo Pepe**. Pasar de "compro
porque el Computer recompra caro" a "compro porque este jugador está
subiendo un 4,6 % diario" son dos negocios distintos, y solo el
segundo mira al jugador.

---

# 5. Lo que se quedó fuera, y por qué

**Encender el esquema nuevo.** Es lo que pedía el encargo: en sombra.
La lista del apartado 1 es lo que hay que aprobar antes.

**Cambiar dónde se aplica la confianza en el motor vivo.** Es la
corrección más importante que encontré y la que más mueve: sin ella,
cualquier confianza que se le ponga a una vía la apaga. Está
implementada y probada en la sombra, con guardia que fija los números.
Encenderla es una decisión del dueño.

**La confianza de la vía del once.** Se queda como está, y es lo
correcto: ahí la incertidumbre sobre los puntos **sí** es la que toca.

---

## Cómo quedó

```
rama          confianza/2026-09-09, subida
main          sin tocar
puerta        71/71 en verde  (70 al empezar, 1 guardia nueva)
commits       3
frontend      npm run build OK · NO desplegado · dist/ intacto

decisiones    ninguna cambia. La vía viva de tendencia sigue con la
              confianza de puntos; `computer_resale_value` sigue en
              1,0 por defecto y devuelve los mismos 1.671.780 de la
              foto del 04/09.

umbrales      MIN_SPECULATION_YIELD = 0,03           sin tocar
              MIN_SPECULATION_EXPECTED_VALUE = 25000 sin tocar
```

**La frase para mañana:** con cada vía llevando su propia confianza,
la del Computer deja de ganarlo todo —de 14 de 14 pasa a 11 de 14— y
la de tendencia se lleva justo a los tres que están subiendo de
verdad. Pero para que eso funcione hay que descontar la ganancia, no
el capital, y esa línea sigue sin tocar en el motor.
