# Poner el dinero a trabajar — resultado de la noche del 09→10/09/2026

Rama `despliegue/2026-09-10`, subida. `main` sin tocar.
**Puerta: 72 de 72 en verde.** Eran 71 al empezar. Tres commits.
`npm run build` pasa. **Nada desplegado.**

**Todo bajo un solo interruptor, apagado.** Con `DEPLOYMENT_ENABLED`
sin poner, Pepe decide exactamente igual que ayer: todo lo de esta
noche se calcula, se publica al lado y no manda.

**No se ha subido ningún tope, ningún porcentaje ni ningún
presupuesto, y no se ha tocado la deuda.**

---

# 1. La lista

Con la foto de producción del 04/09 —la del encargo— y los tres que la
vía de ampliación ya ponía sobre la mesa el 05/09.

| Jugador | Precio | Clase | Bolsillo | Se le medía contra | Se le mediría contra |
|---|---|---|---|---|---|
| **Natan** | 3.010.000 | FICHAJE | fichar | 3.564.000 | **8.561.940** |
| Expósito | 5.130.000 | FICHAJE | fichar | 3.564.000 | 8.561.940 |
| Odysseas | 3.750.000 | FICHAJE | fichar | 3.564.000 | 8.561.940 |

## A quién ficharía hoy, con caja propia y sin tocar la deuda

**A Natan, por 3.010.000 €, del bolsillo de fichar.**

Uno. No tres.

El motivo es que **la regla de esta noche es "solo caja propia"**, y la
caja propia son 3.399.140 €. Natan cabe. Expósito y Odysseas no: sus
5,13 M y 3,75 M solo caben en los 8,56 M, y esos 8,56 M **llevan deuda
dentro** (ver el apartado 3). Con la deuda fuera de la conversación,
la lista se queda en un nombre.

**Por qué Natan y por qué ahora.** Hoy se le rechaza con *"como
especulación rinde un 0,14 % y se exige al menos un 3 %"*. Es la frase
que la auditoría señalaba: ni siquiera está mirando el fútbol. Se le
está pidiendo rendimiento de reventa a un jugador que se quiere para
que juegue. Con la clase de operación decidiendo el bolsillo, a Natan
se le mide por sus puntos y contra el dinero de fichar — que es la
cuenta que corresponde.

**Expósito es el caso que hay que mirar mañana.** Clave, 90 % titular,
196 puntos esperados, y hoy se rechaza con *"rinde un 0,59 % y se exige
un 3 %"*. Con el arreglo pasa a ser un fichaje de 5,13 M contra un
bolsillo de 8,56 M: **entra sin forzar nada**. Lo único que lo deja
fuera esta noche es la regla de no tocar la deuda. Es una decisión del
dueño, no del bot.

**Ninguno de los tres toca el tope de concentración**: Expósito sería
el 9,7 % de la plantilla, Odysseas el 7,3 % y Natan el 5,9 %.

---

# 2. A quién NO ficharía, y por qué importa

La vía de ficha vacía **no es una barra libre**. Sobre los mismos
datos, el filtro rechaza:

| Jugador | Motivo |
|---|---|
| Rubén Sánchez | *"Solo 30 % de titularidad. Una ficha ocupada por un suplente es una ficha vacía que además cuesta dinero."* |
| Jon Pacheco | *"Solo 0 % de titularidad."* |

Son exactamente **los dos únicos candidatos baratos por punto** de los
18 fichables (10.507 € y 12.134 € el punto, contra 21.758 € del
mercado). Una vía de ampliación sin filtro los compraría a los dos: es
el bucle de las catorce defensas que ya costó una intervención a mano
del dueño el 05/09.

**El filtro es lo que hace que esta vía se pueda encender.** Sin él,
sería la peor idea de la semana.

---

# 3. ¿Cuánto capital quedaría trabajando y cuánto seguiría parado?

**Antes de la respuesta hay que corregir la pregunta, y esto es lo más
importante de la noche.**

> «3,4 M parados en caja» y «8,5 M en el bolsillo de fichar sin usar»
> **no son 11,9 M. Son el mismo dinero contado dos veces.**

Medido en `acquisition_budget.py:196-243`:

```
bolsillo de fichar   = 100 % de la caja  +  100 % del margen de deuda
                       segura,  recortado por el máximo de Biwenger
bolsillo de apostar  = una porción de esa misma caja
```

Los 8.561.940 € son los 3.399.140 € de caja **más ~5,16 M de margen de
deuda segura**. No hay 8,5 M esperando: hay 3,4 M de dinero propio y
una capacidad de endeudarse que el encargo deja expresamente fuera.

## La respuesta, con la deuda intacta

| | Hoy | Con el arreglo |
|---|---|---|
| Capital propio | 3.399.140 | 3.399.140 |
| **Trabajando** | **0** | **3.010.000** *(88,6 %)* |
| **Parado** | **3.399.140** *(100 %)* | **389.140** *(11,4 %)* |
| Fichas ocupadas | 14 de 19 | 15 de 19 |
| Deuda usada | la de hoy | **la misma** |

**De 3,4 M parados a 389.140 €**, y una ficha vacía menos. Sin subir un
solo tope y sin un euro de deuda nueva.

## Y si el dueño quisiera abrir la deuda (esta noche NO)

Los tres —Expósito, Odysseas y Natan— son 11.890.000 €, y el bolsillo
completo con deuda son 8.561.940 €. **Ni con la deuda abierta caben los
tres.** Cabrían dos: Expósito + Natan, 8.140.000 €.

Lo digo porque el número «8,5 M sin usar» invita a pensar que hay sitio
para la lista entera, y no lo hay.

---

# 4. Lo que hace cada pieza

## El bolsillo sale de la clase de operación, no de los euros

`acquisition_valuation.py` elegía `intent` con
`max(opciones, key=value)`. Como la reventa al Computer ganaba en 21 de
22 candidatos, **los 22 salían `SPECULATION`** y se medían contra los
3,5 M de apostar mientras los 8,5 M de fichar seguían intactos. Cinco
se rechazaron por «supera presupuesto» teniendo el dinero al lado.

La regla nueva:

> Si el jugador entra a la plantilla **para jugar** —mejora el once o
> llena un hueco—, es un fichaje, **aunque su reventa diera más
> euros**. Para qué lo quieres no lo decide cuál de las cuentas sale
> más gorda.

El `value` no cambia: sigue siendo el mayor de todas las vías. Lo que
cambia es de qué bolsillo se paga y con qué listón se le mide.

**Ojo con `_sin_valor`**, que era la trampa: deja `intent: None`, y
`budget_for_intent` sin intención devuelve **el mínimo de los dos**
bolsillos. Está cubierto por guardia.

## La ficha vacía, con los vetos que sí tocan

`candidatos_a_salir` era una lista de **un** elemento: el titular más
flojo de la posición. No había forma de fichar sin quitarle el sitio a
nadie, con tres huecos que no puntúan.

La vía nueva compara contra el **cero de un hueco** —que es lo que hoy
aporta— sin el veto de «no mejora el once», porque no está desplazando
a nadie. Pero **con** los que sí tocan: sin pronóstico no se ficha a
ciegas, por debajo de Rotación no se ocupa una ficha, y a un lesionado
tampoco.

**Las fichas libres son 5, y se publican como cota inferior**: tenemos
14 y la plantilla más grande de la liga tiene 19. *El tope real de
Biwenger no está en el código ni comprobado* — así que 5 es un suelo:
si Biwenger permite más, hay más sitio, nunca menos. La palabra
`is_lower_bound` viaja dentro del JSON.

## Los dos topes de concentración salen de la liga

No existía ninguno. Medido sobre las siete plantillas:

```
manager           fichas   mayor jugador   mismo club
Pollo17   (1º)      19        31,0 %           4
Mex       (2º)      14        32,2 %           2
Luismi    (3º)      15        19,0 %           2
PEPE      (4º)      14        41,1 %           2
DiosMande (5º)      11        24,7 %           4
Prinzipote(6º)      17        44,9 %           2
Manzagool (7º)      13        17,4 %           3
```

**Los tres que van por delante están entre el 19 % y el 32 %.** Los dos
más concentrados de la liga van sextos y cuartos. Con siete equipos eso
no demuestra causalidad, pero sí dice dónde está la banda de los que
ganan, y que Pepe está fuera de ella.

- **35 % por jugador**: justo encima de la banda de los líderes.
- **4 del mismo club**: lo que lleva el líder. Nadie lleva cinco.

Y **avisa y acota, no prohíbe en silencio**: que Yamal ya esté por
encima no obliga a vender a nadie. Lo que se acota es *empeorarlo*. El
motivo va escrito entero en la pantalla de PLANTILLA.

*(De paso cierra la lección de Soler del 16/08. Aquello se guardó con
un test de rendimiento, pero el problema era de concentración: 5,95 M
inmovilizando el 81 % del bolsillo. Hasta hoy no lo cubría nadie.)*

## El interruptor

```
DEPLOYMENT_ENABLED
```

En `src/analysis/deployment.py`, y en ningún otro sitio — hay una
guardia que lo comprueba escaneando el árbol con `ast` y otra que
enciende el interruptor en un subproceso y verifica que el resultado
**cambia**. Un interruptor que no se puede demostrar que hace algo no
es un interruptor.

Para encenderlo, cualquiera de las dos:

```
DEPLOYMENT_ENABLED=1        (variable de entorno)
DEPLOYMENT_ENABLED = True   (la constante del fichero)
```

Para apagarlo, quitarla. No hay más sitios que tocar.

---

# 5. Lo que me sorprendió

## 1. Los dos bolsillos son el mismo dinero

Ya está en el apartado 3, pero es el hallazgo de la noche y va aquí
también. Llevo el encargo entero leyendo «3,4 M parados **más** 8,5 M
sin usar» como dos montones. No lo son. Fichar = caja + deuda segura;
apostar = una porción de la caja. **El arreglo del `intent` no añade
capital: quita la regla equivocada de encima.** Que es mucho, pero no
es lo mismo.

## 2. Un guardarraíl rojo, y tenía razón

`test_ampliar_plantilla_sombra_v1` se puso rojo en dos aserciones. Lo
leí antes de tocarlo, como estaba mandado: **la guardia del 05/09
prohibía exactamente lo que este encargo ordena hacer** —usar la lista
de ampliación dentro de la ruta de decisión— y lo prohibía con razón
para su fecha.

No se borró. Se estrechó con precisión: sigue prohibiendo la **lista**
(`build_roster_expansion_shadow`) en la ruta de valoración, y ahora
además **exige** que se reutilice el **conteo** (`count_free_slots`) en
vez de escribir uno nuevo, y que todo cuelgue del interruptor. La
guardia ha quedado más estricta que antes, no menos.

Van tres veces esta semana que un guardarraíl me para y las tres tenía
razón.

## 3. La pantalla dice el motivo equivocado cuando no hay pronóstico

Al correr la vía de ficha vacía sobre los datos locales, **los 20
candidatos salieron `FICHA_NO_APTA`**. El filtro estaba funcionando —
pero el motivo era el mismo en los 20: *sin pronóstico de titularidad*.

Ninguno de los 16 jugadores de mi plantilla ni de los 20 del mercado
tiene pronóstico. Y el tablero de FutbolFantasy **sí** los tiene: 64
jugadores en disco, con los 16 míos y los 20 candidatos dentro.

Lo que pasa es esto:

```
El tablero es de la jornada 2 y estamos en la 5:
sin pronosticos hasta que se refresque.
```

Es el guardarraíl del 05/09 haciendo su trabajo con una foto vieja —
correcto. **Pero eso no es lo que sale en pantalla.**
`lineup_engine.py:170-177` colapsa «rechazado por jornada» en *«El
tablero de FutbolFantasy está vacío»*, y el motivo exacto —que existe,
en `board_stamps()` — no llega. Al dueño se le dice «no hay datos»
cuando la verdad es «los datos son de hace tres jornadas».

**No lo he arreglado**: está fuera de este encargo y toca la ruta de
alineación. Queda apuntado, con el fichero y la línea.

## 4. Con la deuda fuera, hoy el bolsillo de fichar es cero

En la foto local el saldo es **−264.032 €**. Los 5.107.168 € que
publica el bolsillo de fichar son **0 de caja y 5.107.168 de deuda**.
Con la regla de esta noche —solo caja propia— hoy no se ficha a nadie
aquí, y no por los topes: por el saldo.

La foto del 04/09 tenía 3.399.140 € de caja de verdad. Por eso la lista
del apartado 1 va sobre ella y no sobre la local.

## 5. Yamal ha subido, no bajado

La auditoría midió el 44 %. Al medirlo con el código nuevo sobre la
plantilla de hoy sale **45,1 %** (22,2 M de 49,27 M en 16 fichas). El
problema que este encargo quería acotar **ha crecido mientras se
escribía el encargo**.

---

# 6. Lo que se quedó fuera, y por qué

**Encender el interruptor.** Es lo que pedía la pieza 4: calcular,
publicar, no decidir. La lista del apartado 1 es lo que hay que aprobar
antes.

**El motivo equivocado del tablero de titularidad** (apartado 5.3).
Fuera de encargo, y toca la ruta de alineación.

**La deuda.** Expresamente. Luismi va tercero con 10 M en rojo; ésa es
otra estrategia y otra conversación.

**El tope real de plantilla de Biwenger.** No está en el código y no lo
he podido comprobar contra la API. Se usa la mayor observada de la liga
y se publica diciendo que es una cota inferior.

---

## Cómo quedó

```
rama          despliegue/2026-09-10, subida
main          sin tocar
puerta        72/72 en verde  (71 al empezar, 1 guardia nueva)
commits       3
frontend      npm run build OK · NO desplegado · dist/ intacto

interruptor   DEPLOYMENT_ENABLED, apagado.
              Definido en src/analysis/deployment.py y en ningun
              otro sitio, con guardia que lo comprueba con `ast`.

decisiones    ninguna cambia con el interruptor apagado. Verificado
              generando el dashboard con el interruptor a 0 y a 1:
              las 20 filas salen identicas.

umbrales      MAX_SPECULATION_BUDGET_PERCENT   sin tocar
              MAX_SINGLE_SPECULATION_PERCENT   sin tocar
              MAX_DEBT_SPECULATION_PERCENT     sin tocar
              MAX_SAFE_DEBT                    sin tocar
              MIN_SPECULATION_YIELD            sin tocar
              MIN_SPECULATION_EXPECTED_VALUE   sin tocar
              deuda                            sin tocar
```

**La frase para mañana:** el dinero no estaba parado porque los topes
fueran estrechos —está parado porque a un fichaje se le pedía
rendimiento de reventa y se le medía contra el bolsillo equivocado. Con
eso arreglado y sin tocar un euro de deuda, entra Natan y la caja pasa
de 3.399.140 € parados a 389.140 €. Y si mañana decides abrir la deuda,
el primero de la lista es Expósito.
