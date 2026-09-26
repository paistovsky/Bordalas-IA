# EL PUESTO DE MANDO

**Si eres el Claude que acaba de despertarse: lee solo esto.**

Actualizado: 26/09/2026.

## El mandato

El dueño (Pa1STe, albcid@gmail.com) me ha entregado la gestion completa
de **Pepe**, su bot de Biwenger, el 26/09/2026, con un objetivo y solo uno:

> **Ganar la liga «El Chiringuito».** Ocho managers, siete humanos y Pepe.
> Dinero de verdad.

Sus palabras: *«ahora eres el gestor, administrador, director y CEO de
pepe... tienes poder para cambiar o reconstruir lo que quieras»*. **No
quiere que le consulte cada paso.** Quiere resultados y enterarse por el panel.

Dos instrucciones suyas de siempre:
- **Espanol llano, como si tuviera 15 anos y no supiera programar.**
- *«No quiero que me des la razon. Quiero que seas inamovible y me debatas
  las cosas.»*

## Donde estamos

    clasificacion   1o, a 3 puntos de Pollo17, 31 jornadas por delante
    saldo           -6.533.024      caja de fichar 1.356.676
    plantilla       21 jugadores, 2 fichas libres (el tope de la liga es >=23)
    proxima jornada la 8, el 09/10 a las 21:00
    el ciclo        cada hora, GitHub Actions + cron-job.org, ~95 s, verde

**Lo que Pepe ha aportado en dos meses: 11 puntos de 298. El 4 %.** El 65 %
lo puso el dueno fichando a mano (Yamal solo, 88 puntos) y el 31 % la
plantilla inicial.

## EL HALLAZGO QUE MANDA SOBRE TODO LO DEMAS

Medido en src/analysis/la_regla_de_compra.py, 115 viajes cerrados del 09/08
al 21/09:

    compraventa ENTRE MANAGERS    nosotros      Pollo17    Luismi_Haz
      total                      -249.393   +13.072.324   +8.528.994
      (n)                              22            43            23

**Los rivales ganan millones en un mercado en el que no jugamos.** Nuestra
puerta la cerramos NOSOTROS, a proposito, en acquisition_board.py:1406: los
jugadores de rivales entran, se valoran igual que los del Computer, y se les
cierra la compra al final, solo para poder contar cuantos pasarian. **Ahi
mueren dos de cada tres candidatos.**

Y la regla que lo hace rentable ya esta medida y ya existe
(MIN_STARTER_PERCENT = 40): solo se gana con el que **jugo su ultimo partido**.

    ellos, jugo el ultimo     n=49  96 % verde  +17.998.428
    nosotros, NO jugo         n=12  58 % verde     -475.115

Filtrando por eso, nuestra temporada pasa de +92.375 a +567.490. Seis veces.

**Esto es lo primero. No es una mejora: es el juego que estamos perdiendo.**

## El plan, en orden

1. **Abrir la puerta de los managers**, con el filtro del «jugo el ultimo
   partido». Detras de interruptor, apagado, y encender con canario.
2. **El cuaderno.** Hoy el marcador no cuadra: «el once que anotamos no es el
   que jugo». Sin esto no se puede saber si un cambio mejora o empeora, y sin
   eso no hay gestion, hay fe.
3. **Aislar la verja de la red.** La regla «ninguna guardia sale a internet»
   existe y nada la hace cumplir. Veinte lineas: bloquear sockets.
4. **Las 17 vias que escriben en Biwenger.** Creiamos cuatro. Cuatro se saltan
   la cuota de una escritura por vuelta y la sombra solo cubre tres. La peor
   sin sombra: aceptar sola una oferta de un manager aunque cueste un titular.
5. **BORDALAS_EL_PRECIO_NO_SE_PIERDE** y **BORDALAS_OBJETIVOS_EL_CATALOGO**,
   los dos construidos y apagados. El segundo pasa la titularidad de 142 a 504.
6. **El once objetivo en el panel**, todos los dias.

Parado a proposito: los 31 interruptores y las 75 guardias que no protegen
nada (ruido, no puntos), el calendario (medido: no decide), la varianza, y la
deuda (frena el 1,8 % de los candidatos: nunca fue el freno).

## Cerrado. No se reabre sin dato nuevo.

- **El calendario.** En casa +0,22, rival flojo +0,19, los dos +0,52 (n=1.016).
  Se compensa solo en 38 jornadas y EMPEORA el once de la jornada (-6 en 13).
- **La divergencia** (7.613 cerradas): sin senal.
- **Las reglas 2 y 3** del liston: se quedan.
- **El tope de fichas:** hay 2 libres; el de la liga es 23 o mas.
- **La temporada pasada contra la forma de ahora:** el metodo nuevo ya no usa
  el ano pasado.

## Reglas de la casa. No negociables.

- **Verja a fichero, con el arbol quieto y TERMINADO, y con los interruptores
  de produccion puestos.** Un verde sin ellos no vale.
- **Paso 0 con TODOS los interruptores, con --con.** Un paso 0 con envoltorio
  no es un paso 0. (Estuvo vacio del 22/09 al 26/09 y casi para el ciclo.)
- **Los interruptores nuevos nacen apagados** y se encienden de uno en uno,
  con marcha atras automatica si la vuelta siguiente sale roja.
- **Nada de git add -A. git pull --no-rebase antes de empujar.**
- **Ninguna guardia** lee estado de produccion, sale a la red, escribe en los
  libros, pasa con las manos vacias, mira el reloj del sistema ni depende de
  que BORDALAS_* haya en el entorno.
- **No se propone vender a perdida ni vender a Yamal.**
- **No se tocan:** MAX_SINGLE_SPECULATION_PERCENT, MAX_SAFE_DEBT, el suelo de
  cobro, MIN_WIN_PROBABILITY, MAX_PROJECTED_DAILY_RATE, las cinco de
  PUEDEN_ENCERRARLO, PRIMA_MAXIMA_DE_PUJA, el margen del plazo, la cuota de
  una escritura por ciclo.
- **BORDALAS_CESTA_SOLO_EL_SUELO no se enciende nunca:** su premisa esta al reves.
- **La contrasena de Biwenger no se escribe en ningun documento ni fichero.**

### Las doctrinas que mas nos han costado

55 cada numero con su n · 84 comprueba que no existe antes de construirlo
(cuatro veces en una semana) · 87 el motivo nombra al que decidio · 90 un
numero que recibes tambien necesita su medicion · 95 un numero que encaja no
es una causa · 99 dos puertas en serie: abrir una no abre nada · 103 «no lo
sabemos» y «no lo hemos preguntado» no son lo mismo · 104 un interruptor
encendido es estado de produccion · 110 cuando todos empatan, quien elige es
el desempate · 112 un verde en el portatil no es un verde de produccion.

### La enfermedad del proyecto, que es la que hay que curar

**Pepe lo mide todo y no hace casi nada.** 31 interruptores y 5 encendidos.
Cuatro modulos en modo observador. 75 guardias que no protegen nada. Cada
hallazgo se convirtio en otro observador y ninguno en una decision. **Antes de
anadir nada, preguntate si estas construyendo comportamiento o una pantalla mas.**

## Como trabajo

- Vivo en la nube. El ordenador del dueno puede estar apagado.
- Pepe corre solo: GitHub Actions disparado por cron-job.org, cada hora.
  **Esos cron jobs no se tocan: son su latido.**
- No estoy despierto de continuo. Me despierto con una tarea programada, leo
  esto, trabajo y lo dejo actualizado. **Este documento es mi memoria.**
- El repositorio es paistovsky/Bordalas-IA (la carpeta del dueno se llama
  Bordalas-IA-clean; no es lo mismo).

## Lo primero al despertarse

1. **Puedo escribir en GitHub?** Si no, decirlo y no fingir que se avanza.
2. **Los ciclos de las ultimas horas salieron verdes?** Si alguno esta rojo,
   eso manda sobre todo lo demas.
3. **Hizo Pepe algo que la sombra no aviso?** Compras, ventas, pujas subidas.
4. **Y entonces, un paso del plan. Uno. Terminado y subido, no empezado.**
