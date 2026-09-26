# EL PUESTO DE MANDO

**Si eres el Claude que acaba de despertarse: lee solo esto.**

Actualizado: 26/09/2026, noche (punto 1 reubicado y construido, apagado; tarea diaria programada).

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

## CORRECCION 26/09/2026 (tarde): EL HALLAZGO DE ABAJO ESTABA MAL ETIQUETADO

Medido sobre data/rival_intelligence/board_events.json (tablon entero,
09/08 a 26/09) y data/fotos/2026-09-18.json:

- **Los rivales NO ganan en el mercado entre managers.** Las 262 compras del
  tablon son TODAS al mercado del Computer (Pollo17 78, Luismi_Haz 66,
  nosotros 48). Traspasos de manager a manager en toda la temporada: **10**,
  y 4 son nuestros. La tabla de abajo («compraventa ENTRE MANAGERS») son
  viajes comprados al Computer y revendidos. El hueco con Pollo17 esta en el
  mercado donde YA jugamos, no en una puerta cerrada.
- **Con la puerta abierta, el 18/09 Pepe habria fichado a nadie.** 34
  jugadores de managers en el tablero; los 34 con `would_pass: False`
  (16 SUPERA_PRESUPUESTO, 8 SIN_VALOR, 6 NO_COMPENSA, 3 RENDIMIENTO, 1 NO
  DISPONIBLE). Abrir la puerta con el liston de hoy = puerta cerrada en la
  practica. Con el filtro «juega» (titularidad >= 40 %) y sin liston:
  n=28, prima media +14,5 % sobre mercado, **-16.876.000 (-13,2 %) a precio
  de hoy, 4 de 28 en verde**. Peor que no fichar. Solo los que piden a
  precio de mercado (+-3 %): n=10, +790.000 (+2,6 %), 4 de 10 en verde, y
  casi todo es un jugador (Jonathan David, +1,18 M). Una foto, 8 dias: sin
  senal.
- Puntos hechos desde el 18/09: **no se han podido medir** (el repo no guarda
  puntos por jugador y jornada despues de la foto; la red de la nube no
  deja bajar los artefactos del ciclo).

**Decision: el punto 1 del plan se CIERRA sin tocar codigo.** No se reabre
sin dato nuevo (por ejemplo, varias fotos donde algun jugador de manager
pase el liston a precio de mercado).

## EL HALLAZGO ORIGINAL (ver la correccion de arriba)

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

1. **La regla «¿va a jugar?» en TODAS las compras para revender.**
   Reubicado el 26/09: el hueco con Pollo17 (+13.072.324, n=43, contra
   nuestro -249.393, n=22) esta en el mercado del Computer, donde ya
   jugamos, y la causa esta medida en la_regla_de_compra.py.
   - Lo que habia: la regla (MIN_STARTER_PERCENT = 40 via
     roster_fill_veto) ya se aplicaba a la reventa en la SUBASTA DEL RESET
     (BORDALAS_REVENTA_SOLO_SI_JUEGA, encendido en produccion). NO en el
     CARRIL de la rendija, que tambien compra para revender
     (RENDIJA_APAGADA sin poner = vivo). La puerta de los managers,
     cerrada con datos (ver la correccion de arriba).
   - Contrafactual: de los 12 viajes de «no jugo el ultimo» (-475.115),
     2 entraron por el carril: Trent -223.500 y Drkusic -36.376. Con la
     regla en el carril: +259.876 sobre sus 4 viajes (Boyomo +28.503 y
     Maffeo -42.850 pasan: jugaron). n=4: pequeno, pero en la direccion
     de la medicion de temporada. En la foto del 18/09 deja pasar 14 de
     20 candidatos del Computer: no ahoga el carril.
   - HECHO (commit bc82a23): BORDALAS_REVENTA_SOLO_SI_JUEGA_EN_EL_CARRIL,
     APAGADO. Guardia test_el_carril_mira_si_juega_v1. Verja 190/190 con
     los de produccion y con --con el nuevo; paso 0 PASADO con los 33
     (config/paso_0.json). La guardia cazo un fallo que habria dejado la
     puerta cerrada en la practica: el carril tiraba la titularidad del
     candidato y la regla habria frenado a TODOS.
   - **LO QUE FALTA PARA QUE ESTE HECHO DE VERDAD: encenderlo.** Poner
     `BORDALAS_REVENTA_SOLO_SI_JUEGA_EN_EL_CARRIL: "1"` en el env de
     .github/workflows/bordalas-live.yml, junto a REVENTA_SOLO_SI_JUEGA, y
     vigilar la vuelta siguiente (canario). Si sale roja, se quita. Hasta
     entonces NO frena ni una puja. Es lo primero de manana.
2. **El cuaderno.** EL SIGUIENTE, en cuanto el 1 este encendido y verde. Hoy el marcador no cuadra: «el once que anotamos no es el
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
- **La tarea programada existe desde el 26/09/2026:** rutina «Pepe: despertar
  diario del gestor» (trig_012SxTn5vFzBmsmBabtbe7RM), todos los dias a las
  08:47 hora de Madrid, abre una sesion nueva en la nube que empieza leyendo
  este documento. Avisa al dueno por el movil y por email. Sin conectores:
  si la sesion no puede clonar o empujar, lo primero es decirlo.
- La red de la nube NO deja bajar los artefactos del ciclo (blob de Azure,
  403). Lo que no este en el repo no se puede medir desde aqui.
- El repositorio es paistovsky/Bordalas-IA (la carpeta del dueno se llama
  Bordalas-IA-clean; no es lo mismo).

## Bitacora de despertares

- **26/09 (sesion con el dueno).** GitHub: escribo en main (7989423,
  b6d754b, bc82a23). Ciclos: los 30 de 25/09 10:07 a 26/09 15:07 UTC,
  verdes. Sombra: revisandose al cerrar esta sesion; si aqui no hay
  resultado, repetir el punto 3 manana. Plan: punto 1 reubicado y
  construido, APAGADO (ver arriba).
- **26/09 16:20 UTC (comprobacion programada).** El ciclo #1817 de las
  16:07, el primero con el carril nuevo (825f6a6), salio VERDE. La
  revision de la sombra (punto 3) sigue sin resultado: repetirla manana.

## Lo primero al despertarse

1. **Puedo escribir en GitHub?** Si no, decirlo y no fingir que se avanza.
2. **Los ciclos de las ultimas horas salieron verdes?** Si alguno esta rojo,
   eso manda sobre todo lo demas.
3. **Hizo Pepe algo que la sombra no aviso?** Compras, ventas, pujas subidas.
4. **Y entonces, un paso del plan. Uno. Terminado y subido, no empezado.**
