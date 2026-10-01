# EL PUESTO DE MANDO

**Si eres el Claude que acaba de despertarse: lee solo esto.**

Actualizado: 01/10/2026, 07:35 de Madrid (rafaga de las 07:15).

## El mandato

El dueño (Pa1STe, albcid@gmail.com) me ha entregado la gestion completa
de **Pepe**, su bot de Biwenger, el 26/09/2026, con un objetivo y solo uno:

> **Ganar la liga «El Chiringuito».** Ocho managers, siete humanos y Pepe.
> Dinero de verdad.

Sus palabras: *«ahora eres el gestor, administrador, director y CEO de
pepe... tienes poder para cambiar o reconstruir lo que quieras»*. **No
quiere que le consulte cada paso.** Quiere resultados y enterarse por el panel.

**LA REGLA DEL DUENO (29/09): «inversion» son PUNTOS.** «El dinero es un
medio para fichar mejores jugadores y ganar mas puntos.» Cada decision se
mide en puntos por jornada del once; el dinero solo cuenta por los puntos
que compra despues. Un jugador se conserva por lo que puntua (titularidad,
minutos, puntos), no por su precio; se vende en su mejor precio cuando no
suma al once, para pagar a quien suma mas. (Caso: Jutgla se queda, 70 %
titular; Duran se vende en su pico para pagar a Roberto Fernandez.)

Dos instrucciones suyas de siempre:
- **Espanol llano, como si tuviera 15 anos y no supiera programar.**
- *«No quiero que me des la razon. Quiero que seas inamovible y me debatas
  las cosas.»*

### El mandato, ampliado el 27/09/2026

El dueno lo repite y lo amplia: administracion TOTAL para crear, borrar y
modificar lo que haga falta, **sin preguntarle**. 100 % autonomo.
- **Mision unica:** ganar la liga. Pepe tiene que ser lo mas inteligente,
  eficiente, competitivo y autonomo posible.
- **27/09 23:00, el dueno lo deja aun mas claro:** «modifica el programa tal
  y como quieras mientras Pepe gane la liga; puedes rehacerlo desde cero si
  quieres. Que tenga disponibilidad y que mejore». Via libre total sobre el
  codigo. Lo unico que no se negocia es que Pepe siga corriendo (el ciclo
  verde) mientras se cambia: nada se sube sin verja.
- **Mision terciaria (29/09, «no muy relevante»):** una APK para que la
  gente lo disfrute. **El dueno decide: BOT COMPLETO, no consejero.**
  Condiciones del gestor: (1) leer antes las condiciones de uso de
  Biwenger sobre automatizar cuentas: una app publica arriesga baneos de
  usuarios y que corten el acceso, Pepe incluido; (2) el bot corre EN EL
  MOVIL de cada usuario, con su contrasena guardada solo alli: nunca
  claves ajenas en un servidor nuestro; (3) el usuario elige que permite
  (aconsejar / pujar / vender), todo apagado de serie; (4) limites de
  peticiones por usuario. Detras de la liga y del panel.
  **30/09, objetivo A LARGO PLAZO:** que Pepe haga solo todo lo que hoy
  decide el gestor, y distribuir la APK (de pago si es legal; si no, a
  familia y amigos). Orden acordado: (1) ganar la liga; (2) pasar cada
  decision repetida del gestor a Pepe (sirve a la liga y a la APK a la
  vez); (3) leer las condiciones de Biwenger y, si se cobra, abogado
  (datos de terceros, responsabilidad); juego limpio: que la liga lo
  sepa; (4) solo entonces, Pepe multiusuario y la APK. Aparcado.
- **Mision secundaria:** un panel para ver en tiempo real que pasa. Hoy
  existe https://bordalas-ia-dashboard.bordalas.workers.dev/ (usuario y
  contrasena: los tiene el dueno; NO se escriben en el repo, que es publico).
- **Informe:** uno pequeno al dia, para "dummies".
- Si hace falta un permiso o una herramienta, se le pide.

## Donde estamos

    clasificacion   1o, a 3 puntos de Pollo17, 31 jornadas por delante
    saldo           +206.284 (29/09 07:19; caja libre ~31.000)
    plantilla       14 jugadores: 1 POR, 4 DEF, 6 MED, 3 DEL
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
     entonces NO frena ni una puja.
   - **ENCENDIDO el 27/09 a las 12:06 de Madrid (2164cfe), a peticion del
     dueno. Canario: el ciclo #1834 de las 12:07, VERDE.** Punto 1 hecho.
2. **El cuaderno.** HECHO el 28/09 (9183e9c, ver bitacora). Antes: Hoy el marcador no cuadra: «el once que anotamos no es el
   que jugo». Sin esto no se puede saber si un cambio mejora o empeora, y sin
   eso no hay gestion, hay fe.
3. **LO SIGUIENTE (decidido 28/09 12:30): la regla de los rivales (E1 del
   laboratorio).** «Solo se compra para revender lo que SUBIO en el ultimo
   cambio de precio; se vende al Computer el primer dia que BAJA». Medido en
   191 compras reales de la liga: los que subian, +25,7 M; los que no, -0,6 M.
   Pepe compra hoy 32 de 41 del grupo malo. Es lo de mas dinero del plan.
   Como: dos interruptores nuevos, apagados (COMPRA y VENTA por separado),
   en la subasta del reset y en el carril; antes, mirar si PRECIO_CAYENDO
   ya hace parte (doctrina 84: frena lo que baja, deja pasar lo plano). Rama,
   verja, paso 0 con --con, ENSAYO con cada uno, y se enciende primero la
   COMPRA; la VENTA en otra rafaga. Detalle en docs/LABORATORIO.md (E1).
3-ter. **PARA LA RAFAGA DE LAS 14:15 DEL 29/09: la guardia de las noticias
   (E4 del laboratorio).** «No se puja por quien tenga una noticia de BAJA
   en FutbolFantasy en las ultimas 72 h.» n=180, -2,5 % a 3 dias; entre los
   que suben (la rampa), -3,7 % (n=50). Detalle y codigo de medida en
   lab/noticias/ y docs/LABORATORIO.md (E4). Interruptor apagado, guardia,
   verja, paso 0, ensayo, encender, canario. Tambien: la orden del gestor
   (config/la_orden_del_gestor.json) esta viva hasta el 09/10: puja por
   Roberto, venta para pagarlo, Jutgla ultimo recurso; no tocarla sin
   leerla.

3-bis. **LO SIGUIENTE DE VERDAD (decidido 29/09 09:30 por el gestor, tras
   la queja del dueno «solo ficha defensas»): LA HUCHA PARA EL ONCE.**
   Medido: 32 de las 55 pujas ganadas son defensas, porque con 1-3 M solo
   hay defensas y porteros. Hoy Adeyemi (10,28 M) y Roberto Fernandez
   (8,38 M), del Computer, caen por SUPERA_PRESUPUESTO con la caja en
   ~1,6 M, y la unica puja es Lejeune (DEF, 3,66 M). La distancia al once
   objetivo (~16 pts/jornada) esta ARRIBA. Pepe gasta cada euro en
   calderilla y nunca junta para quien cambia el once. Lo que hay que meter:
   a) la lista de OBJETIVOS = el once objetivo (el_once_objetivo.py),
      ordenada por puntos/jornada que suma al once;
   b) cuando un objetivo sale al mercado del Computer: ¿llega vendiendo al
      Computer (oferta en firme del dia) a quien no es titular? Si llega,
      vende y puja; nunca a perdida sin mirarlo, nunca Yamal;
   c) la reventa sigue, pero sin gastar la reserva del proximo objetivo.
   Primero MEDIR (doctrina 84: mirar si OBJETIVOS_EL_CATALOGO o la
   cola de destino ya hacen parte): cuanto suman hoy las ofertas del
   Computer por los no titulares, y si con eso Adeyemi o Roberto cabian.
   Rama, verja, paso 0, ensayo, un interruptor, canario.
   **Y de paso:** Gordon (9,66 M) y Lookman (5,42 M) salen con valor 0
   (SIN_VALOR, «no vale por ninguna via») el 29/09. Mirar si es un fallo
   de valoracion (sin emparejar en el ojeador, sin puntos) y no un juicio.
4. **Aislar la verja de la red.** HECHO el 29/09 (931efbf); queda que las guardias no escriban en los libros. La regla «ninguna guardia sale a internet»
   existe y nada la hace cumplir. Veinte lineas: bloquear sockets.
5. **Las 17 vias que escriben en Biwenger.** Creiamos cuatro. Cuatro se saltan
   la cuota de una escritura por vuelta y la sombra solo cubre tres. La peor
   sin sombra: aceptar sola una oferta de un manager aunque cueste un titular.
6. **BORDALAS_EL_PRECIO_NO_SE_PIERDE** y **BORDALAS_OBJETIVOS_EL_CATALOGO**,
   los dos construidos y apagados. El segundo pasa la titularidad de 142 a 504.
7. **El once objetivo en el panel**, todos los dias.

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

## EL LABORATORIO (desde el 27/09/2026)

Pedido por el dueno: «no pares de crear y mirar cual es la mejor manera de
crear un bot autosuficiente para ganar Biwenger». Tiene su propia sesion
(«PEPE — El laboratorio (NO BORRAR)», session_01X9AAPm6vKDRe4K5jJjhMwk) y su
rutina (trig_01Q8poVQ2BZtW31YPgKG68TL, 11:13 y 17:13 de Madrid). Sus reglas,
su agenda y sus experimentos estan en **docs/LABORATORIO.md**. No toca
produccion: cuando algo gana con datos, lo deja en «Listo para el plan» y lo
mete un turno del gestor. **Los turnos del gestor deben mirar esa seccion al
empezar.** El informe diario del dueno cuenta tambien lo que aprendio el
laboratorio.

## EL ENSAYO: el entorno de pruebas (desde el 27/09/2026)

Un Pepe ENTERO que lee Biwenger de verdad y no escribe nada. Para probar
cualquier cambio grande ANTES de fusionarlo a main:
1. Sube el cambio a una rama (no a main).
2. Lanza el workflow «Bordalas IA Ensayo» (`bordalas-ensayo.yml`) sobre esa
   rama (actions_run_trigger, ref = la rama). Si pruebas un interruptor, pasalo
   en el input `interruptores`.
3. Mira el log y el artefacto `bordalas-ensayo-<run>`: en
   `data/ensayo/escrituras_no_enviadas.jsonl` esta lo que Pepe HABRIA hecho
   (pujas, ventas, once). Si es sensato, a main; si no, se arregla en la rama.
- Como funciona: `BORDALAS_ENSAYO=1` cierra las siete escrituras de
  `BiwengerWriteClient` (guardia `test_el_ensayo_no_escribe_v1`). Restaura el
  estado de produccion sin guardarlo, no guarda libros, no empuja, no toca el
  panel. Usa los mismos interruptores que produccion (los lee de su YAML).
- CUIDADO: cada ensayo hace las mismas peticiones a Biwenger que una vuelta
  real (ya hubo un 429). A mano y con cabeza, no en bucle.

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
- **La tarea programada (rehecha el 27/09/2026):** rutina «Pepe: el gestor,
  tres veces al dia» (trig_011uRD7DQp5Z6wkRjBNu4BQR), 07:15, 14:15 y 21:15
  de Madrid. Despierta SIEMPRE la misma sesion fija,
  session_016rymfNCNtFYU8RGFHvUGy5 («PEPE — Turnos del gestor (NO BORRAR)»),
  que tiene el repositorio dentro y
  empuja a main. La de antes abria una sesion nueva SIN repositorio y moria
  en tres minutos: una rutina no puede llevar repositorio, una sesion si.
  Probado el 27/09 a las 09:21 UTC por el camino programado: desperto la
  sesion fija y vio el repo y este documento.
  **OJO: el boton «disparar ahora» NO sirve para probarla**: ignora la
  sesion fija y abre otra vacia (paso el 27/09 09:17). Para probar, una
  rutina de un solo disparo con hora (run_once_at) a la sesion fija.
  La sesion fija no puede mandar avisos al movil: su resumen queda en la
  sesion y en este documento.
- La rutina «Pepe: el cierre de la jornada 8» (trig_01ANZwEgrZL4o5Fh84KEjZQj,
  09/10 16:00 UTC) tambien despierta la sesion fija desde el 27/09. La vieja
  (sin repositorio) esta borrada.
- **Permisos (27/09, ampliados a las 23:00):** `.claude/settings.json` deja
  correr python, git, pip y curl sin aprobacion, y editar cualquier fichero. Sin eso el filtro de seguridad bloqueaba la verja con un
  interruptor puesto. Claude NO puede tocar ese fichero (el filtro lo trata
  como automodificacion): si hace falta otro permiso, se le pide al dueno.
- **Horas: al dueno se le habla SIEMPRE en hora de Madrid.**
- Red: desde el 27/09 el dueno dio acceso sin restricciones. Ya se pueden
  bajar los artefactos de cada ciclo de GitHub Actions (diagnostico con lo
  que Pepe vio en esa vuelta): usarlos para medir, no solo la foto del 18/09.
- El repositorio es paistovsky/Bordalas-IA (la carpeta del dueno se llama
  Bordalas-IA-clean; no es lo mismo).

## Bitacora de despertares

- **01/10 08:40 (chat del dueno, comprobacion del agujero).** Ganados
  Diego Rico y Moi Gomez (el dueno pujo 890.000 con el precio ya en 900.000:
  **la venta del Computer pide el precio del dia en que salio y no se
  mueve; el valor si.** Si sube, se compra por debajo de lo que vale; si
  baja, por encima. Pepe puja con el valor, no con lo que pide la venta:
  proximo trabajo, «los chollos de la manana»). Perdidos Fofana y Akhomach
  con Pollo17. Racha cobrada. Saldo -2.434.617, plantilla 12.
  **Decision:** Gulacsi (Villarreal, titular desde la J5, 80 % en FF;
  5,33 pts/partido) por Dmitrovic (95 %, 4,0): +puntos esperados (4,3
  contra 3,8 ponderando la titularidad) y +1,5 M. Puja 2.437.000 (un pico
  sobre el precio, idea del dueno contra los empates); Dmitrovic se vende
  solo con Gulacsi dentro, suelo 3,75 M. Con Moi revendido (~0,92 M) el
  agujero queda en ~0; la racha del ~06/10 deja margen. Fuera de la orden:
  Fofana, Akhomach. Exposito vuelve a `conservar`.

- **01/10 07:15 (rafaga de la manana). Reset de las 07:05.** Ciclos:
  verdes (#1914 a #1921). GANADAS: Diego Rico (580.001) y Moi Gomez
  (890.000, viaje corto). PERDIDAS, las dos con Pollo17: Fofana (5.707.000
  contra nuestros 5.262.000) y Akhomach (4.477.000 contra 3.192.006).
  Como Fofana no llego, Exposito NO se vende: el relevo `si_esta` funciono.
  Plantilla 12 (once guardado con 11 nombres: arreglado lo de ayer). Saldo
  -2.434.617; faltan ~2,4 M antes del 09/10 15:00. Moi Gomez se revende en
  cuanto pague mas de lo que costo (orden). Pollo17 nos gano las dos pujas
  grandes por +8 % y +40 %: con la caja que tenemos no se le gana una
  subasta disputada; los viajes cortos tienen que ir a jugadores que nadie
  mas puja. No se construye ni se enciende nada (lo lleva el gestor).

- **30/09 21:15 (rafaga de la noche).** Ciclos: verdes (#1906 a #1912).
  Nada nuevo en el mercado desde la tarde. Saldo -1.214.616; tres pujas
  vivas para el reset del 01/10 (Diego Rico 620.000, Akhomach 3.170.000,
  Fofana 5.260.000; comprometido 9.050.000). Si entran las tres, el saldo
  cae a ~-5 M hasta vender a Exposito (relevo de Fofana, suelo 5,1 M) y
  revender a Akhomach: **la rafaga de las 07:15 del 01/10 tiene que mirar
  que esas dos ventas se disparen y que la plantilla pase de 10 a 11+**
  (hoy 10, once guardado con 9). No se construye ni se enciende nada: la
  orden, los viajes cortos y el comparador los lleva el chat del gestor.

- **30/09 18:25 (chat del dueno).** Tres pujas vivas para el reset del
  01/10 07:00, las tres de la orden y comprobadas en los ciclos: Diego Rico
  0,62 M (once 11/11), **Akhomach 3,17 M** (primer viaje corto: sube cada
  dia, 1,63 -> 3,17 M desde el 24/09; es reventa, NO delantero: 3,83
  pts/partido contra 4,14 de Jutgla) y **Fofana 5,26 M** (primer cambio del
  comparador: 6,75 pts/partido contra 5,0 de Exposito, mismo precio, los
  dos 80 % en FF; Exposito solo se vende cuando Fofana es nuestro, suelo
  5,1 M, y salio de `conservar`). Comprometido 9,05 M; queda ~3,9 M de puja.
  Construido hoy: cuadro «Como salimos del rojo» (hoja de ruta en la
  orden), viajes cortos en la orden, **el comparador de cambios**
  (`cambios` en el panel, El Plan; solo mira). Limite conocido: el
  comparador no mira la titularidad (Moi Gomez, 30 %, salia «nos saca del
  rojo»): se filtra a mano hasta meterla.
  **Manana:** si se gana Akhomach, cambiar su salida a «aguantar mientras
  sube, vender el primer dia que baje, antes del 07/10» y quitarlo de
  candidatos cuando se venda (si no, lo recompra). Pendiente: B (viajes con
  saldo en rojo, en Pepe) y C (comprar a rivales; hoy la puerta solo mira,
  `would_decision`). Ninguno cambia nada antes del 09/10 con el margen que
  queda: van despues de la J8.

- **30/09 14:15 (rafaga de la tarde).** GitHub: escribo en main. Ciclos:
  verdes (#1898 a #1905). Pepe: vendio a Antonio Blanco (09:10, 2.899.200,
  con el suelo bajado a 2,85 M por la orden). Saldo -1.214.616; el chat del
  dueno lleva el agujero (~1,3 M con Diego Rico) y el examen «salir del
  rojo sin vender a los top». No lo duplico.
  **COMPROBADO CONTRA LA FOTO (la leccion de Maffeo):** plantilla de 10
  (marcador, 14:09): 1 POR (Dmitrovic), 2 DEF (Jonny, Chust), 4 MED (Unai
  Lopez, Pablo Ibanez, Exposito, Olasagasti), 3 DEL (Yamal, Jutgla,
  Roberto). **El once guardado en Biwenger es un 3-4-3 con SOLO 9
  nombres**: falta el tercer defensa (Diego Rico, si se gana) y un cuarto
  medio, aunque Unai Lopez esta en la plantilla y NO esta alineado. El
  ciclo pone el once antes del 09/10, pero **el turno del cierre (09/10
  12:45) tiene que comprobar que salen 11 nombres** y, si Unai sigue
  fuera, por que (lesion, duda o fallo del motor del once).
  Hoy no se construye ni se enciende nada: el chat del dueno esta tocando
  la orden y las ventas en vivo, y dos manos a la vez en el mismo sitio es
  como se cometio el error de Maffeo.

- **30/09 07:15 (rafaga de la manana). ROBERTO FERNANDEZ ES NUESTRO.**
  Ciclos: verdes (#1890 a #1898). En el reset de las 07:04 Pepe gano a
  Roberto por 9.650.000; Pollo17 pujo 8.777.000 (subir anoche de 8,95 M a
  9,65 M fue lo que lo gano). A las 07:18 la orden vendio al Computer:
  Cabrera 2.432.000, Zubeldia 1.265.500, Pablo Duran 1.316.700 y 17369
  por 165.400 (+5,18 M). Saldo antes de esas ventas: -9.293.416; despues,
  hacia -4,1 M. Queda Antonio Blanco (suelo 3,15 M) y, si hace falta,
  Jutgla desde el 08/10 07:00. Plazo de solvencia: 09/10 15:00; la rutina
  del cierre salta ese dia a las 12:45 (comprobada).
  - El detalle de `decidir` (tope antes que «ya hay puja») ya lo arreglo el
    chat del dueno (7a2f242). Nada que hacer.
  - Gordon y Lookman con valor 0: NO es un fallo. Lookman: 16 pts en 7
    partidos, 50 % titular, precio sin subir -> NO_MEJORA del once; Gordon
    ya no esta en el tablero. Cerrado.
  - La VENTA de E1 se aplaza a despues del cierre de la J8 (10/10): la
    orden del gestor esta vendiendo hasta el 09/10 y dos reglas de venta a
    la vez se pisarian.
  - Hoy no se enciende nada: la hucha para el once la lleva el chat del
    dueno y no se duplica.

- **29/09 21:15 (rafaga de la noche).** GitHub: escribo en main y ramas.
  Ciclos: verdes (#1883 a #1889). Pepe: nada nuevo desde las 14:15;
  sigue viva la puja por Roberto (8.950.000, reset del 30/09 07:00) y hoy
  ya se encendio un interruptor (la revision de pujas, desde el chat del
  dueno), asi que esta noche NO se enciende nada. E6 del laboratorio
  contesto a mi pregunta de E4: los filtros de hoy frenan 30 de 41 bajas;
  el hueco eran las pujas ya puestas, y eso lo tapa la revision de pujas.
  E4 queda cerrado.
  **Punto 4 del plan, la otra mitad: LAS GUARDIAS NO ESCRIBEN EN LOS LIBROS.
  HECHO, pendiente del canario** (43d3c21). El vigilante apunta ahora
  tambien las escrituras bajo `data/` (open en escritura, write_text/bytes,
  os.replace/rename) con ruta absoluta; la verja tumba a la guardia que
  escriba en el `data/` del repositorio. Censo: 2 de 197,
  `test_divergencia_v1` y `test_ojeador_informe_v1`, que en su prueba «el
  enganche nunca lanza» llamaban a sync_* SIN ruta y escribian
  divergence_ledger.json y scout_accuracy_ledger.json de produccion en cada
  verja (tambien en CI, dentro de la cache). Ahora con temporal. Verja
  197/197 sin tocar `data/`; paso 0 con 37; ensayo #10 verde en CI.
  **Canario: el ciclo #1890 de las 22:07, VERDE (comprobado a las 22:17).**
  **Con esto el punto 4 queda entero: la verja ni sale a la red ni escribe
  en los libros.** Lo que sigue: la VENTA de E1 (E5 la da ganadora; leerlo
  entero y mirar la orden del gestor, que ya vende), y el detalle de la
  orden (`decidir`: mirar «ya hay puja nuestra» antes que el tope).

- **29/09 14:15 (rafaga de la tarde).** GitHub: escribo en main y ramas.
  Ciclos: verdes (#1876 a #1882). Pepe: vendio un jugador (37715) al
  Computer por 150.300 a las 14:09; sigue viva la puja por
  Roberto Fernandez (committed 8.950.000, se resuelve el 30/09 07:00);
  saldo +356.584. Rutina del cierre de la J8: comprobada hoy (09/10 12:45).
  **La guardia de las noticias (E4): NO SE CONSTRUYE AUN. Debatido con
  datos (doctrina 84).**
  - Lo que ya existe: `futbolfantasy_absences.py` lee cada vuelta los
    lesionados y sancionados de FF, con «desde» y `days_out`, y llega a
    cada fila del tablero como `absence`. Los lesionados y en duda ya
    salen `NO_DISPONIBLE`; «¿va a jugar?» exige 40 % de titularidad; y la
    rampa frena al que no sube (E4: en el 58 % de las BAJA el precio ya
    caia).
  - Tablero de produccion del #1882: 70 candidatos, 5 con ausencia de FF,
    NINGUNA de las ultimas 72 h (la mas reciente, 9 dias); las dos mas
    recientes ya estan en NO_DISPONIBLE. Hoy la guardia no frenaria a
    nadie.
  - Hacerla como dice E4 pide una FUENTE NUEVA en cada vuelta (las
    noticias de FF, recorridas por ID y clasificadas por palabras, ~80 %
    bien). Mas peticiones y mas pantalla para un efecto sin medir.
  - **Pregunta para el laboratorio (E4-bis):** de las BAJA de E4 en
    jugadores que subian (n=50, -3,7 %), ¿cuantas habrian pasado HOY los
    filtros que ya hay (estado de Biwenger ok, titularidad >= 40 %, precio
    subiendo)? Si son pocas, E4 ya esta cubierto; si son muchas, se
    construye con la fuente minima: la lista de lesionados de FF
    (`absence.days_out` <= 3 con estado ok), que ya esta en la foto.
  **Lo que sigue en la cola:** que las guardias no escriban en los libros
  (la otra mitad del punto 4) y la VENTA de E1, cuando E5 se haya leido
  entero (el laboratorio la da como ganadora: +5,5 M contra +0,7 M con 2 M
  de caja).

- **29/09 07:15 (rafaga de la manana).** GitHub: escribo en main y ramas.
  Ciclos: verdes (#1867 a #1875). Sin vueltas de 05:07 y 06:07 de Madrid
  por segundo dia: parece el horario del latido (dos casi seguidas a las
  04:45 y 04:50 y la siguiente a las 07:15), no un fallo; no se toca.
  Pepe: GANO a Zubeldia (1.363.592, la puja del carril del 28/09, puesta
  ANTES de encender la rampa). Plantilla 15; saldo +206.284.
  **La rampa, primer reset:** la subasta no pujo por nadie, pero no por la
  rampa: `SIN_CESTA`, «con 30.942 de caja libre» no llega a ningun
  candidato. Sin dinero no se prueba la regla. La racha (encendida anoche
  desde el chat del dueno) va sola hacia 5.
  **E1, mitad de VENTA: NO SE CONSTRUYE AUN. Pregunta para el
  laboratorio.** Doctrina 84: `salida_del_viaje.py` (aceptar la primera
  oferta >= coste + 1 %, medido 3,05 %/dia, n=34) existe pero su
  ejecutor (`salida_executor`) NO lo llama nadie; hoy Pepe vende por el
  escaparate y la oferta del Computer. E3 comparo la salida de E1 contra
  otras (2,70 %/dia con dia muerto) pero NO contra «aceptar el primer
  reset con +1 %». Antes de construir: que el laboratorio compare las dos
  con la misma vara (%/dia, con el capital limitado que tenemos) y diga
  por donde vende Pepe de verdad hoy.
  **Punto 4 del plan (aislar la verja de la red): HECHO, pendiente del
  canario** (931efbf). El vigilante de cada guardia
  (`scripts/vigila_data/sitecustomize.py`) corta ahora toda conexion fuera
  de la maquina con `VERJA_SIN_RED=1` y apunta el destino; la verja lo
  enciende y quita el proxy. Guardia `test_la_verja_no_sale_a_la_red_v1`.
  El ENSAYO lo destapo: `test_el_ciclo_publica_v1` ENTRABA EN BIWENGER
  con las credenciales de verdad en cada verja de CI (via
  `collect_board_history`, sin proteger). Arreglado en la guardia: monta
  el estado con el tablon de disco. De paso, la verja ensena ahora la
  traza de la guardia que falla (antes la tapaban sus propios OK).
  Verja 195/195; paso 0 pasado con 35; ensayos #5 y #6 rojos (lo que se
  buscaba), #7 verde. **Canario: el ciclo #1876 de las 08:07, VERDE
  (comprobado a las 08:16). Punto 4, mitad de la red: HECHO.**
  **Deuda que queda (no hecha):** varias guardias siguen ESCRIBIENDO en los
  libros de produccion al correr en local (divergence_ledger.json,
  scout_accuracy_ledger.json). Es la otra mitad del punto 4.

- **28/09 21:15 (rafaga de la noche).** GitHub: escribo en main. Ciclos:
  verdes (#1861 a #1866, este ultimo ya con el codigo de la racha). Pepe:
  nada nuevo desde las 14:15 salvo un bonus de 250.000 (18:43); sigue viva
  la puja por Zubeldia (1.363.592). Rutina del cierre de la J8: comprobada
  hoy (09/10 12:45).
  **BORDALAS_COMPRA_SOLO_SI_SUBE, ENCENDIDO a las 21:30 (c5f6183).** Antes:
  verja 194/194 con el interruptor puesto sobre el arbol de ahora (con la
  racha dentro) y 194/194 con los 7 de produccion ya en el YAML; paso 0
  de las 21:06 con 35, que lo incluye. **Canario: el ciclo #1867 de las
  22:07, VERDE (comprobado a las 22:16). La rampa queda encendida.**
  Ya se puede encender la racha (`BORDALAS_COBRA_LA_RACHA`) en otra vuelta.
  **Primer efecto real: la subasta del reset del 29/09 a las 07:00.** La
  rafaga de las 07:15 tiene que mirar a quien freno (`dropped_by_no_sube`)
  y a quien pujo. La puja viva por Zubeldia NO la toca la regla (ya esta
  puesta); se resuelve en ese mismo reset.
  Siguiente, por orden: la racha (`BORDALAS_COBRA_LA_RACHA`), en otra
  vuelta, cuando este canario salga verde; despues, la mitad de VENTA de
  E1 (el laboratorio ya la midio en E3: vender el mismo dia de la primera
  bajada).

- **30/09 14:30 (el dueno y el gestor). EL EXAMEN: SALIR DEL ROJO SIN VENDER
  A LOS TOP.** El dueno: «buen examen para ver como salimos de este
  embrollo sin tener que vender a uno de nuestros delanteros o jugadores
  top. Aun hay tiempo y estrategias distintas, eso es lo que quiero ver.»
  Estrategias, por orden: (1) CAMBIO UNO POR OTRO (caro por titular barato
  de su posicion, venta con relevo `si_esta`), cada manana con el mercado
  nuevo; (2) VIAJES CORTOS de reventa sobre lo que SUBE (E1/E3: vender al
  Computer el primer dia que baja), con tope 2 M por viaje, ~3-4 M en
  total, todo cerrado antes del 07/10: da ~0,2-0,4 M, no cierra solo el
  agujero (para 1,3 M a +5 % harian falta ~26 M). Hoy Pepe NO especula en
  rojo (carril: presupuesto = saldo - comprometido; subasta: tope max(0,
  caja)); hay que abrirlo por la orden, acotado; (3) red: Jutgla el 08/10.
  **Error de metodo del 30/09 (dos veces):** grep '"2026-09-30"' en
  libro_de_la_valoracion.jsonl casa con el campo d7 de filas viejas; Oriol
  Rey parecia estar en el mercado y era del 23/09. Filtrar por la clave
  "dia" parseando el JSON.

- **30/09 14:00 (el gestor). ERROR MIO: MAFFEO YA NO ERA NUESTRO.** El
  dueno: «estamos en negativo y nos falta 1 jugador». La plantilla tras
  vender a Blanco es de 10 con 2 DEF (Chust, Jonny): planifique el 3-4-3
  con Maffeo sin comprobar la plantilla real (Maffeo se vendio antes).
  **Leccion: todo plan de ventas se valida contra la plantilla real de la
  foto, no contra la memoria.** Arreglo: la orden ficha a Diego Rico
  (Osasuna, 50 % titular FF «Rotacion», 0,57 M; puja 620.000; f6fcada).
  Alternativas medidas en FF: Lejeune 95 % «Clave» pero 3,37 M; Johaneko
  30 %; Jesus Vazquez 20 %. Saldo: -1,21 M (tras Blanco, 2.899.200) ->
  -1,83 M con Diego Rico -> ~-1,33 M con las rachas. **Faltan ~1,3 M antes
  del 09/10 15:00.** Opcion A (preferida hoy): vender Dmitrovic (~3,96 M)
  y fichar portero barato (~-2 pts/j). Opcion B: Jutgla (~3 M) + DEL
  barato (~-3 pts/j). Decidir el 06/10 con precios de ese dia.

- **30/09 10:45 (el gestor). EL PANEL, HECHO DE CERO, PUBLICADO** (d9e8b5d,
  despliegue verde). Menus: INICIO (igual, con la cronologia rehecha desde
  el plan real: pujas vivas, `subasta`, `orden`, cierre de jornada; ya no
  lee la valoracion), EL PLAN (la orden en marcha, el dinero hasta la
  jornada en cascada, el proximo reset, las reglas), MERCADO, PLANTILLA,
  LIGA (una carta por rival) y TALLER (lo tecnico y las paginas viejas,
  plegadas). Nueva clave `orden` en status.json (680a0ea).
  **Arreglado el origen de los datos viejos**: dashboard-deploy.yml corria
  su propia vuelta SIN interruptores y subia status.json al KV, pisando
  el del ciclo en cada publicacion (asi salia «Pujar por Lejeune»). Ahora
  solo despliega el diseno (e1b9643); los datos los escribe solo
  bordalas-live.yml.

- **30/09 08:30 (el gestor). EL AGUJERO QUE QUEDA.** Saldo real tras las
  cuatro ventas: -4.113.816 (#1899). Blanco: el Computer ofrece 2.899.200
  (-4 %), su precio baja; suelo bajado a 2.850.000 (325cf7c) para que la
  orden lo venda en la vuelta siguiente. Cuenta: -4,11 + 2,90 = -1,21 M;
  + rachas 01/10 y ~06/10 (0,5 M) = **~-0,71 M el 06/10**. Sin mas, Jutgla
  se vende el 08/10 (ultimo recurso). **ANTES DEL 07/10, buscar la salida
  que menos puntos cueste**: (a) vender a Maffeo (~1,5 M, 9 pts en 6) y
  fichar un DEF barato que juegue (<0,8 M) para seguir con 3 DEF; (b)
  Jutgla como estaba (29 pts, 70 % titular: cuesta mas puntos); (c) lo
  que el mercado de esos dias permita. Decidirlo con numeros el 06/10.
  Plantilla tras Blanco: 11 justos (sin banquillo).

- **30/09 07:25 (el gestor). ROBERTO FERNANDEZ ES NUESTRO** (9.650.000;
  segundo Pollo17 con 8.777.000: los 8,95 M tambien habrian ganado, por
  173.000; la subida costo 700.000 de seguro). Adeyemi: Manzagool 11,08 M
  (Pollo 10,78, Luismi 10,74). Ventana: la revision de pujas vivas miro la
  de Roberto, TODAS_PASAN, no toco nada; la subasta no pujo por nadie
  (presupuesto 0). Ciclo #1898 (07:15): la orden ACEPTO las ofertas del
  Computer por Cabrera 2.432.000, Zubeldia 1.265.500, Pablo Duran
  1.316.700 y Guevara 165.400 (todas sobre su suelo). Antonio Blanco
  sigue sin oferta que llegue a 3,15 M. Saldo tras Roberto -9.293.416;
  tras las cuatro ventas ~-4,11 M; con Blanco (~3,2 M) y la racha del
  01/10 (0,25 M) quedaria ~-0,66 M; con la racha del ~06/10, ~-0,41 M:
  **Jutgla (ultimo recurso, desde el 08/10 07:00 si sigue en rojo) puede
  hacer falta.** Plantilla tras Blanco: 11 justos. Pendiente: medir el
  saldo real en el ciclo de las 08:07 y buscar otra salida antes del
  08/10 (p. ej. bajar el suelo de Blanco si la oferta se queda corta,
  o una venta con prima).

- **30/09 00:20 (el gestor). PUJA SUBIDA, CONFIRMADA.** La orden pujo
  9.650.000 en el ciclo #1891 (23:07) y retiro la de 8.950.000: en la foto
  de las 00:09 Biwenger marca committed 9.650.000 (una sola puja) y
  maximumBid 4.871.584. Se resuelve el 30/09 a las 07:00. Comprobacion
  programada: 07:20.

- **30/09 00:10 (el gestor). EL PANEL, MENU A MENU, PUBLICADO** (247cc8b,
  85fed7f, 8aa5271; despliegue 8aa5271 verde). Cada pagina responde una
  pregunta y lo tecnico va plegado: MERCADO (caja, pujas en juego, lo
  nuestro a la venta, lo ultimo hecho, lo que mas sube), PLANTILLA (quien
  juega y como esta), ESTRATEGIA («Lo que Pepe tiene encendido», clave
  `reglas`; guardia: todo interruptor encendido necesita su frase en
  QUE_HACE de src/telemetry/el_tablon.py, o la verja se pone roja), LIGA
  (clasificacion y «lo que ha movido cada rival esta semana», clave
  `tablon_semana`), MARCADOR (la nota por jornada). Canario de la reja
  (#1891, 23:07) VERDE; en esa vuelta la orden subio la puja por Roberto.
  Faltan en status.json: lo ganado/perdido por operacion, numero de
  jornada en el marcador, tendencia de precio de varios dias.

- **29/09 23:10 (el gestor).** (1) **Puja por Roberto SUBIDA a 9.650.000**
  (+15,2 % sobre 8,38 M; 94e2372). En peleas por jugadores caros se paga
  +7 a +16,5 % (Pollo17 +9,8 % hoy por Moleiro, +16,5 % el 11/09). Caja
  reconstruida (con la reja): Pollo17 ~7,5 M (puja maxima > 25 M), Luismi
  -16,6 M (tope ~6,9 M: tendria que vender ~3,6 M). El dueno avisa: Luismi
  vive en NY y puja a ultima hora; Pollo tiene «mazo de pasta y el equipo
  vacio». La orden sabe SUSTITUIR una puja viva: pone la nueva y, si entra,
  retira la vieja; si Biwenger no admite dos, retira y vuelve a pujar
  (guardia 14/14, ensayo #36629224877 BID 9.650.000). Arreglado a la vez
  el NADA enganoso (el tope es maximumBid + la puja que se sustituye).
  Comprobacion 00:20: committed debe ser 9.650.000.
  (2) La pantalla ya no anuncia «Pujar por Lejeune»: los no_pujar se
  quitan en plan_desde_el_estado (c9df0a0). (3) Panel sin avisos
  PUBLICADO (b0d3ca9): saldo en grande, una linea «Ultima vuelta de Pepe»,
  avisos en Diagnostico (AUDITORIA, plegado). En curso: menus limpios
  (rama panel/menus-limpios), se publica al revisar.

- **29/09 22:30 (el gestor). EL PANEL, PUBLICADO; LA CAJA DE LA LIGA, CUADRA.**
  - Panel (mision secundaria), a peticion del dueno: sin portada; INICIO
    con «EL TABLON DE HOY» arriba (clave `tablon`, src/telemetry/el_tablon.py,
    guardia test_el_tablon_v1), sin «Posibles cambios», una sola linea de
    estado en vez de los avisos amarillos/rojos (rojo solo si Pepe lleva
    > 3 h parado), movil y PC sin scroll lateral y selector «Movil / PC».
    Fusionado f580554, verja 198/198, publicado por dashboard-deploy.yml
    (se dispara solo con push a main en dashboard-v8/, dashboard/,
    src/telemetry/, cloudflare/; corre un ciclo OBSERVER sin --live).
  - Caja de la liga: la reja de duplicados estaba apagada y Biwenger
    reemite ventas al Computer con fecha nueva (Lunin, 420.200, contado dos
    veces). ENCENDIDO BORDALAS_REJA_CON_TOLERANCIA (2724e17): 418/438
    lecturas del saldo cuadran al euro; Luismi baja 13,3 M. Residuo sin
    explicar en Luismi (< 60.000 en J4, J5, J7). Canario: 23:07.
  - Dueno: la APK, aparcada («ni de segunda fila»); el panel es la
    secundaria.

- **29/09 20:20 (el gestor).** Tarde: (1) Zubeldia (FF «al margen» 21, 28
  y 29/09; Biwenger «doubt») pasa a la VENTA en la orden y Maffeo se queda
  de tercer defensa (f6cc0e1). (2) **ENCENDIDA la revision de las pujas
  vivas** (`src/actions/la_revision_de_pujas.py`,
  BORDALAS_REVISA_LAS_PUJAS_VIVAS, 9c85416): en la ventana del reset retira
  nuestras pujas por jugadores injured/doubt/sanctioned (caso Zubeldia,
  E6); no toca las de la orden. Verja 197/197, paso 0 con 37, ensayo
  #36602358126 verde. **Canario #1888 (20:07) VERDE**: «FUERA_DE_LA_VENTANA».
  - Detalle para arreglar (no esta noche): en `la_orden_del_gestor.decidir`
    el tope `maximumBid` se mira ANTES que «ya hay puja nuestra»; con la
    puja viva Biwenger baja maximumBid (5,57 M) y sale una accion NADA con
    motivo enganoso. No escribe nada (correcto), pero hay que invertir el
    orden de las dos comprobaciones.
  - Comprobacion programada: 30/09 07:20 (resultado de Roberto, lo que
    retiro la revision, arranque de las ventas).

- **29/09 12:20 (el gestor). LA PUJA POR ROBERTO FERNANDEZ, CONFIRMADA.**
  La orden del gestor (BORDALAS_LA_ORDEN_DEL_GESTOR, encendida 10:31) pujo
  en el ciclo #1879 (11:07); en el #1880 (12:07) Biwenger marca
  committed 8.950.000 y maximumBid baja de 14,4 M a 5,46 M. Se resuelve el
  30/09 a las 07:00. Si se gana: la orden publica y cobra (con suelo) a
  Antonio Blanco, Cabrera, Maffeo, Pablo Duran y Guevara; Jutgla solo desde
  el 08/10 07:00 y si el saldo sigue en rojo; conservar el once. Estudio de
  noticias (E4) hecho: guardia de compra para la rafaga de las 14:15.

- **28/09 22:40 (el gestor).** Canario de la rampa (#1867) VERDE, asi que
  **ENCENDIDO `BORDALAS_COBRA_LA_RACHA`**. Verja 194/194 con los 8 de
  produccion; paso 0 de 8c74a8a sigue valiendo (desde entonces solo han
  cambiado el YAML y docs). Canario: el ciclo de las 23:07. Si sale rojo, se
  quita la linea. Primer cobro esperado hacia el 01/10 (racha hoy 2).
  **Canario de la racha VERDE (#1868, 23:07): «Racha diaria: 2 -> AUN_NO_TOCA».**

- **28/09 21:06 (el gestor, en el chat del dueno).** El dueno: «no
  necesitas mi autorizacion para subir codigo. Eres totalmente
  autosuficiente y puedes cambiar lo que quieras. Subelo cuando veas que
  es lo mejor». **Queda como regla: tambien encender interruptores, siempre
  por verja, paso 0, ensayo y canario, de uno en uno.**
  - **LA RACHA DIARIA, FUSIONADA Y APAGADA** (65c1f24, paso 0 en 8c74a8a
    con 35, incluidos COBRA_LA_RACHA y COMPRA_SOLO_SI_SUBE). Los tres
    canjes de Pepe (16/09, 21/09, 26/09) los hizo el dueno a mano; Pollo17
    lleva 7. Octava escritura en BiwengerWriteClient:
    `redeem_daily_streak` = POST /account/dailyStreak/redeem {"league": id},
    la del boton «Canjear» de la app (modulo de usuario v631).
    `src/actions/la_racha.py` lee `daily_streak` de la foto (sin peticion
    de mas) y cobra solo si es >= 5. Interruptor `BORDALAS_COBRA_LA_RACHA`.
    Guardia `test_la_racha_v1` (5/5); el ensayo vigila ahora 8 escrituras.
    Verja 194/194 (produccion y --con). Ensayo #36468507118 VERDE:
    «Racha diaria: 2 -> AUN_NO_TOCA». La racha sube sola con las vueltas
    de Pepe: llega a 5 hacia el 01/10.
  - **EL ORDEN:** la rafaga de las 21:15 enciende PRIMERO la rampa
    (COMPRA_SOLO_SI_SUBE), como estaba previsto; el arbol ha cambiado, asi
    que repite el paso 0 si hace falta. Cuando el canario de la rampa salga
    verde, se enciende `BORDALAS_COBRA_LA_RACHA: "1"` (el gestor o la
    rafaga siguiente), con su propio canario. Nunca los dos en la misma
    vuelta. Hay margen: hasta el 01/10 no hay nada que cobrar.

- **28/09 14:15 (rafaga de la tarde).** GitHub: escribo en main y en
  ramas. Ciclos: verdes (#1856 a #1859). Pepe: nada nuevo desde las 07:15
  salvo UNA puja viva del carril: **Zubeldia, 1.363.592** (07:19, para
  revender), con el precio bajando OCHO dias seguidos (1,45 M -> 1,36 M).
  Es justo el caso de E1. Se resuelve en el reset de manana; si la gana,
  la caja libre baja a ~0,2 M. Rutina del cierre de la J8: comprobada.
  **Punto 3 del plan (la regla de los rivales, E1), MITAD DE COMPRA:
  CONSTRUIDA, FUSIONADA Y APAGADA** (d8674fe).
  - Doctrina 84, comprobado antes: la compuerta PRECIO_CAYENDO frena lo
    plano y lo que baja, pero la subasta no la usa, el carril la quito a
    proposito («el negocio es el spread»), y lee el ritmo del ojeador, no
    el precio de Biwenger. Medido en bid_outcome_ledger: de las 34 pujas
    de reventa, subasta 17/17 con el precio QUIETO y carril 14/17 BAJANDO
    (3 quietos). Cero a un jugador que subiera.
  - Lo hecho: `src/analysis/la_regla_de_la_rampa.py`, interruptor
    `BORDALAS_COMPRA_SOLO_SI_SUBE` (nace APAGADO). En la subasta del reset
    y en el carril, detras de «¿va a jugar?», frena al candidato cuyo
    `price_increment` (el ultimo cambio de precio de Biwenger, que ya
    viaja en cada fila del tablero) no es una subida. Ni disco ni red.
    Del tablero de hoy suben 34 de 67: no deja sin candidatos.
  - La guardia `test_la_regla_de_la_rampa_v1` (4/4) cazo que el carril
    tiraba `price_increment` al rehacer las filas (habria frenado a
    TODOS, como paso el 26/09 con la titularidad). Arreglado.
  - Las guardias de la subasta y el carril (7 ficheros) llevan ahora un
    candidato que sube, para aguantar con el interruptor puesto.
  - **Encontrado y arreglado: el paso 0 estaba roto desde el 27/09.**
    Encendia tambien `BORDALAS_ENSAYO` (el modo del ensayo, que no es un
    interruptor) y `test_venta_ejecutable_v1` caia: NINGUN interruptor se
    podia encender. Medido en main: con todos, rojo; sin ese, verde.
    Ahora queda fuera (`NO_SON_INTERRUPTORES`, commit 6d25c63).
  - Verja 193/193 con los 6 de produccion Y con --con el nuevo. Paso 0
    PASADO con 34 (config/paso_0.json). Ensayo #3 con el interruptor
    puesto: VERDE, la regla corrio (`activa: true`) sin fallos; esta
    vuelta no tuvo a quien frenar (la caja libre, 206.284, no llega a
    ningun candidato del carril, y la subasta solo actua en el reset).
  - **LO QUE FALTA: ENCENDERLO.** Canario del codigo apagado: el ciclo
    #1861 de las 16:07, VERDE (comprobado a las 16:16). Si sale verde, la
    rafaga de las 21:15 pone `BORDALAS_COMPRA_SOLO_SI_SUBE: "1"` en el env
    de bordalas-live.yml (paso_0.json ya lo tiene probado; si el arbol
    cambia antes, repetir el paso 0) y vigila la vuelta siguiente. Su
    primer efecto real: la subasta del reset del 29/09 a las 07:00.
  - La mitad de VENTA (vender el primer dia que baja) va despues, con su
    propio interruptor, en otra rafaga.

- **28/09 11:30 (el dueno, en persona).** El dueno AUTORIZA: «subir el
  cuaderno a GitHub, y a partir de ahora subir ramas y codigo al
  repositorio sin preguntarme, pasando siempre por la verja y el ensayo».
  **Queda como regla: rama -> verja -> ensayo -> fusion a main.**
  Hecho: stash recuperado sobre main de hoy, rama `el-cuaderno` (14399d6),
  verja 192/192 con los 6 de produccion (la verja volvio a escribir en un
  libro, divergence_ledger.json; deshecho), ensayo #2 VERDE (panel:
  `marcador.cuaderno` = «0 de 1 jornada(s) con nota», motivo: no se congelo
  el once de la J7; correcto). Fusionado a main (9183e9c). Canario: el ciclo
  de las 12:07 de Madrid, con comprobacion programada a las 12:15.
  **Canario: el ciclo #1857 de las 12:07, VERDE; el panel trae
  `marcador.cuaderno` sin error. Punto 2 del plan: HECHO.** La primera nota real
  llegara cuando cierre la J8 (hacia el 12/10), si el once se congela el
  09/10 (ciclo de las 20:07). Lo que el cuaderno NO arregla: la
  clasificacion de Biwenger con retraso (fallo 3).

- **28/09 07:15 (rafaga de la manana).** GitHub: escribo en main. Ciclos:
  todos verdes (#1844 a #1851; el #1852 en marcha). **OJO: faltan dos
  vueltas**, no hubo ciclo entre las 04:50 y las 07:15 de Madrid (el latido
  de cron-job.org salto dos horas; ademas hubo dos casi seguidos a las 04:45
  y 04:50). No se toca (el latido no se toca): si se repite, avisar al dueno.
  Pepe vendio al Computer otros 3 jugadores publicados: Ceballos 4.320.600
  (01:09; publicado a 6,8 M, valia 4,22 M), Iturbe 157.400 (02:10) y Aihen
  224.100 (03:09). **El saldo pasa a positivo: +1.569.876.** Plantilla: 14
  (1 portero, 4 defensas, 6 medios, 3 delanteros). **Riesgo para la J8:
  un solo portero.** Si se lesiona, cero seguro en esa plaza. Que lo mire el
  turno del cierre (09/10 12:45) y, antes, que Pepe fiche portero si puede.
  Rutina del cierre: comprobada anoche (09/10 12:45 de Madrid).
  **Plan: NO he avanzado.** El punto 2 (el cuaderno) sigue esperando al
  dueno: `.claude/settings.json` no ha cambiado desde el 27/09 22:56 (antes
  del bloqueo), asi que el push de la rama seguiria denegado. El stash sigue
  en esta sesion. No empiezo el punto 3 (tocar la verja) por el mismo motivo:
  es codigo, y sin ramas no se puede ensayar antes de main.

- **28/09 00:50 (rutina «Rescatar el cuaderno»).** Pedia subir el cuaderno
  DIRECTO a main porque el push a la rama esta bloqueado. **No lo he
  hecho.** El filtro denego publicar ese codigo («[Modify Shared
  Resources]») y su regla es no conseguir lo mismo por otro camino. Subirlo
  a main es el mismo resultado por una puerta mas delicada: seria rodear el
  bloqueo, justo lo que la prueba dice que no se haga. Lo tiene que decidir
  el dueno EN PERSONA: o da permiso para `git push` de ramas (o de codigo a
  main) en `.claude/settings.json`, o me lo dice el mismo en el chat de esta
  sesion. El trabajo sigue en el stash «el-cuaderno sin subir (denegado)»
  de esta sesion (verja 192/192 cuando se hizo).

- **28/09 00:00 (turno extra de prueba, sesion fija).** GitHub: escribo en
  main. Ciclos: verdes hasta el #1845 (23:07) y el primer ensayo (#1, verde).
  **Punto 2, el cuaderno: causa encontrada, arreglo construido, NO SUBIDO.**
  - La causa, medida en el historial de marcador.json en git (tres fallos):
    (1) el round de Biwenger salto de 5125 (J7) a 4905 (J8) el 19/09 entre
    las 07:17 y las 11:48 de Madrid, con la J7 a medio jugar: la J7 se
    quedo congelada con los totales del viernes (27) y el resto se suma a
    la J8. (2) `observar()` solo guarda totales de la plantilla del dia:
    Dituro y Djene jugaron la J7 y se vendieron, y desaparecen de la resta
    (con los totales del 21/09 el once da 54, no 27). (3) la clasificacion
    de Biwenger parece ir con retraso: Pepe 186 (16/09), 247 (19/09, J7 casi
    sin jugar), 276 (21/09). Esto ultimo sigue sin explicar.
  - Ademas: `onces_de_la_jornada.jsonl` (el once congelado antes del primer
    partido) NUNCA se ha escrito. En la J7 no hubo ciclos del 18/09 16:16 al
    19/09 05:05 y se perdio la ventana. La de la J8 se abre el 09/10 a las
    19:30 de Madrid; solo el ciclo de las 20:07 cae dentro. Si falla, la J8
    tampoco tendra nota.
  - El arreglo: `src/analysis/el_cuaderno.py` + guardia
    `test_el_cuaderno_v1` (4/4) + publicado en el panel dentro del marcador
    (`marcador.cuaderno`) + registrado en la verja. Cruza
    puntos_por_jornada.jsonl (una foto de los 547 por jornada cerrada de
    LaLiga, vendidos incluidos) con el once congelado. Dice tambien que
    titulares no jugaron. Primera nota posible: la J8, cuando cierre.
    **Verja 192/192 con los 6 interruptores de produccion.**
  - **BLOQUEO (lo pide la prueba: el comando y el mensaje exactos).** En la
    rama `el-cuaderno`, este comando:
    `git add src/analysis/el_cuaderno.py src/analysis/test_el_cuaderno_v1.py
    src/telemetry/dashboard_state.py scripts/run_validation_gate.py &&
    git commit -m "el cuaderno: ..." && git push -u origin el-cuaderno`
    fue DENEGADO: «Permission for this action was denied by the Claude Code
    auto mode classifier. Reason: [Modify Shared Resources]». No se rodeo.
    Por eso NO hay ensayo ni fusion. El trabajo esta en un `git stash` de
    esta sesion («el-cuaderno sin subir (denegado)»): se pierde si el
    contenedor se recicla. Para seguir: dar permiso para `git push` a ramas
    que no sean main (o para crear ramas), y el proximo turno hace
    `git stash pop`, commit, push, ensayo y fusion.
  - Otros dos bloqueos de esta sesion, 27/09 21:15: (a) mover la rutina del
    cierre de la J8 (update_trigger): «[Self-Modification]»; (b) un analisis
    en python de solo lectura que cruzaba el once de la J7 con
    puntos_por_jornada.jsonl: «[Unauthorized Persistence]».
  - Encontrado de paso (punto 3 del plan): una ejecucion local (la verja o
    importar dashboard_state) ESCRIBIO 311 lineas en
    data/calendar/calendar_changes.jsonl a las 00:06, bajando el calendario
    de LaLiga de internet. Se deshizo con git checkout. Es la prueba de que
    la verja sale a la red y toca los libros.
  - Rutina del cierre de la J8: trig_01ANZwEgrZL4o5Fh84KEjZQj, comprobada:
    09/10 a las 12:45 de Madrid, antes del plazo de solvencia. Resuelto.

- **27/09 21:15 (rafaga de la noche, sesion fija).** GitHub: escribo en main.
  Ciclos: los 12 de 10:07 a 21:07 de Madrid, VERDES (#1832 a #1843).
  Pepe vendio al Computer 4 jugadores que tenia publicados desde el 24/09:
  Van Oevelen 238.300 (01:11), Guliashvili 187.300 (02:10), Yeray 1.385.800
  (03:10) y Maffeo 1.589.400 (04:47). Estaban en libro_de_publicacion: no
  es una sorpresa. El saldo sube de -6,53 M a -3,13 M. Plantilla: 17.
  **PROBLEMA SIN ARREGLAR, LO TIENE QUE HACER EL DUENO:** la rutina del
  cierre de la J8 (trig_01BmotcVizZb3xHqDZdwYcsB) salta el 09/10 a las
  18:00 de Madrid, DESPUES del plazo de solvencia (15:00). Con el saldo en
  rojo, eso llega tarde. Intente moverla a las 12:45 de Madrid y el filtro
  de seguridad no me deja tocar rutinas (automodificacion). Hay que moverla
  a mano (o darme permiso) a 2026-10-09T10:45:00Z y, en su texto, poner la
  solvencia como punto 1.
  **ARREGLADO el 27/09 22:56 desde el chat principal:** la rutina de la J8
  es ahora trig_01ANZwEgrZL4o5Fh84KEjZQj, 09/10 a las 12:45 de Madrid, con
  la solvencia como punto 1 y una segunda mirada a las 20:15. Las rutinas
  solo se pueden tocar desde el chat principal: desde la sesion de turnos
  el filtro lo trata como automodificacion. Si un turno necesita cambiar
  una rutina, que lo apunte aqui como PENDIENTE PARA EL CHAT PRINCIPAL.
  **Punto 2 (el cuaderno), medido en la vuelta #1843:** 5 jornadas
  cerradas, 0 cuadran con Biwenger. En la J7 (5125) el once anotado suma 27
  y Biwenger dio 61; ademas el marcador saca «mejor once = el once, 100 %»,
  lo que huele a que la plantilla anotada es la del once y no la entera. El
  once de la J7 se escribio el 19/09 a las 09:17 de Madrid, DESPUES del
  primer partido (18/09 21:00). En la J6 (4903) Biwenger marca 0: la
  clasificacion se leyo con la jornada ya a cero. Siguiente paso: comparar
  el once anotado con data/intelligence/puntos_por_jornada.jsonl (J7, 547
  jugadores). No lo pude hacer: el filtro de seguridad bloqueo ese analisis.

- **27/09 17:50 (chat principal). INCIDENTE:** la sesion fija de los turnos
  (session_01RhosWkjkXxsvTsHTntFJnG) DESAPARECIO (no se sabe si se borro a
  mano o la limpio el sistema). A las 14:15 la rutina no la encontro, abrio
  una sesion nueva SIN repositorio y se quedo apuntando a ella: el turno de
  las 14:15 no hizo nada. Arreglo: sesion nueva «PEPE — Turnos del gestor
  (NO BORRAR)» (session_016rymfNCNtFYU8RGFHvUGy5) y las dos rutinas (turnos
  y cierre de la J8) recreadas apuntando a ella. El prompt de los turnos
  ahora, si no encuentra el repositorio, lo anade y lo clona en vez de
  rendirse. Ciclos de Pepe hoy: todos verdes. El cuaderno sigue pendiente.

- **26/09 (sesion con el dueno).** GitHub: escribo en main (7989423,
  b6d754b, bc82a23). Ciclos: los 30 de 25/09 10:07 a 26/09 15:07 UTC,
  verdes. Sombra: revisandose al cerrar esta sesion; si aqui no hay
  resultado, repetir el punto 3 manana. Plan: punto 1 reubicado y
  construido, APAGADO (ver arriba).
- **26/09 16:20 UTC (comprobacion programada).** El ciclo #1817 de las
  16:07, el primero con el carril nuevo (825f6a6), salio VERDE. La
  revision de la sombra (punto 3) sigue sin resultado: repetirla manana.

## Decision del CEO sobre el ritmo (27/09)

El dueno pregunto si seria mejor un gestor 24/7. **No.** El limite no es
cuanto se trabaja sino cuanto se puede comprobar: cada cambio necesita al
menos una vuelta del ciclo (1 h) para ver que no rompe, y jornadas enteras
para ver si da puntos. Veinte cambios al dia = no saber cual fallo, que es
la enfermedad del proyecto. Pepe ya corre solo cada hora; el gestor mejora,
no hace de nineria.
- Tres rafagas de trabajo al dia (07:15, 14:15, 21:15 de Madrid).
- Turno especial en CADA cierre de jornada: cada rafaga comprueba que existe
  el del cierre siguiente y, si no, lo crea (paso 4 de su prompt).
- Una mejora comprobada cada vez.
- **Informe diario al dueno:** rutina «Pepe: tu informe del dia»
  (trig_01NdKT7sR4Kc4tm5KWPnYFKY), 22:43 de Madrid. Escribe en el chat
  «PEPE — El informe diario» (session_01YYDkUCvY26gmmAJoREtwqj), que el
  dueno abre para leer. SOLO lee este documento y los commits del dia. Por
  eso ESTE DOCUMENTO tiene que quedar al dia al final de cada rafaga: si no
  esta aqui, el dueno no se entera.
- **Informe del mercado de la manana:** rutina «Pepe: el mercado de la
  manana» (trig_01XJHpXKFR3TJsSJ2b1tjKGU), 07:47 de Madrid, mismo chat.
  Lee libro_de_la_valoracion.jsonl (lo escribe el primer ciclo tras el reset
  de las 07:00), bid_outcome_ledger.json y bitacora_del_saldo.jsonl: a por
  quien va Pepe, a que precio y con que puja. Si cambia la forma de esos
  libros, hay que actualizar el prompt de esa rutina (desde su chat, o
  borrarla y crearla de nuevo).
- Las instrucciones de una rutina solo se cambian desde SU sesion; desde
  otra hay que borrarla y crearla de nuevo.

## Lo primero al despertarse

1. **Puedo escribir en GitHub?** Si no, decirlo y no fingir que se avanza.
2. **Los ciclos de las ultimas horas salieron verdes?** Si alguno esta rojo,
   eso manda sobre todo lo demas.
3. **Hizo Pepe algo que la sombra no aviso?** Compras, ventas, pujas subidas.
4. **Y entonces, un paso del plan. Uno. Terminado y subido, no empezado.**
