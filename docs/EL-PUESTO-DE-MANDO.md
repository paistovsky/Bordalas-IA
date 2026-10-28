# EL PUESTO DE MANDO

**Si eres el Claude que acaba de despertarse: lee solo esto.**

Actualizado: 28/10/2026, 07:20 de Madrid (rafaga de las 07:15).

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
8. **DESDE EL 10/10 (tras la J8): el banquillo (E12 del laboratorio).**
   Primero un DEFENSA, despues un medio. Con 11 justos y 3 defensas, una
   baja sabida de un defensa es un cero. Va por la orden del gestor
   (fichar), con el saldo en verde.
   **Afinado por E16 (03/10):** tras la J8 habra ~1,8 M (premio ~30.000
   por punto). El defensa NO es suplente: entra TITULAR por Diego Rico,
   que pasa al banquillo. Se elige por PUNTOS ESPERADOS (media x
   titularidad de FF), no por «1-3 M que juegue»: el 03/10, Rafita
   (2,52 M, 3,86) o Puga (1,55 M, 2,57); Jorge Salinas (1,80) casi no
   mejora a Rico. Mirar el mercado de ese dia: ~+1,2 a +2,7 pts/jornada.

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
- **Antes de cada plazo con fecha** (caducidad de la orden, cierre de
  jornada, cambio de hora), una verja con el reloj en esa fecha:
  `RELOJ_FALSO=<fecha ISO con zona> PYTHONPATH=scripts/reloj_falso
  python3 scripts/run_validation_gate.py`. El 09/10 una guardia con
  fecha tumbo cinco vueltas seguidas.
- **Ninguna guardia** lee estado de produccion, sale a la red, escribe en los
  libros, pasa con las manos vacias, mira el reloj del sistema ni depende de
  que BORDALAS_* haya en el entorno.
- **No se propone vender a perdida ni vender a Yamal.**
- **Un fichaje para el once no se revende antes de jugar con nosotros**
  (E14, 02/10): cuatro lo hicieron en el paron, -3,3 M y cero puntos. Si
  hace falta caja, se vende antes a quien ya ha jugado y no suma al once.
  Excepcion unica: un cambio por otro MEJOR del mismo puesto, con los
  puntos esperados medidos y apuntados en la orden.
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
- La rutina «Pepe: el cierre de la jornada 9» (trig_01PnAXQSyaryBqT7Yku9DAP3,
  16/10 10:45 UTC) despierta la sesion fija. La de la J8
  (trig_01ANZwEgrZL4o5Fh84KEjZQj,
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

- **28/10 07:15 (rafaga de la manana).** Ciclos: verdes (#2538 a #2546;
  #2547 de las 07:15 en marcha). Saldo +1.418.975 (dato de las 04:53,
  antes del reset; no habia pujas vivas, asi que el reset no podia
  restar). J11 vie 30/10: cubierta. Cardona 35-40 % (titular en la Copa).

- **27/10 21:30 (laboratorio de la tarde: la prima que gana).** **Rivales:**
  J10 cerrada: Pepe 39 (5.o), Pollo17 44; nos saca ~10 en la general.
  Premio cobrado: caja +1.418.975, 0 pujas vivas. Como pujan (780 dias
  de mercado del Computer,
  17/09-26/10, prima sobre el precio de salida): Luismi mediana +2,2 % (a
  menudo salida + 1 EUR), Pollo17 +6,4 %, Manzagool +10,4 %. **Lo
  medido:** casi todo lo decide si el jugador SUBE de valor el dia de la
  puja. Si no sube (688 de 780), solo hay rival el 4 % de las veces, y la
  salida redondeada a ...9.900 gana el 99 %. Si sube menos del 2 %, hay
  rival el 72 % (mediana +6 %). Si sube un 2 % o mas, siempre hay rival
  (mediana +17 %). Los que suben y alguien pelea siguen subiendo; los que
  no suben pierden un 5-6 % en una semana. **Esceptico (rehizo los datos
  con su codigo: mismos numeros): ADOPTAR MAS ESTRECHO.** Probado fuera de
  muestra, solo esto: (1) si no sube, pujar la salida redondeada a ...9.900,
  sin el +1 % (ahorra 0 por debajo de 1 M, ~13,5 mil entre 1 y 3 M y ~50
  mil por encima de 3 M; perdemos ~2 de cada 100 frente al salida+7-27 mil
  de Pollo); (2) la ronda deja de revender a los que suben menos del 2 %,
  con cualquier prima (resultado real a 7 dias <= 0 en las dos mitades).
  NO probado: subir la prima de los que suben (+9 % / +15-20 %). En la
  prueba hacia delante pierde contra el +1 % de hoy, y un % fijo paga de
  mas por encima de ~1 M. Se queda como guia manual del gestor con tope en
  euros: **la prima nunca pasa de la mitad de lo que vale la mejora en el
  once** (pts/jornada x 30 mil x 3). Con 8+ puntos y subiendo <2 %: +5 %;
  +9 % solo si son 2+ pts/jornada y la prima <= ~450 mil. Subiendo 2 % o
  mas: <1 M +20 %, 1-3 M +12 %, 3 M+ se queda en +1 %; siempre dentro del
  tope. **Aplicado hoy:** la regla manual ya manda en la decision de
  Cardona del mie (ver el parte del 27/10). En produccion no se toca nada
  esta semana: (1) y (2) se construyen apagados (un interruptor cada uno) y
  se encienden despues de la J11, en rafagas separadas del parte vende (mar
  03/11). Re-medir las primas de los que suben dentro de 3-4 semanas, con
  la prueba escrita antes de mirar los datos.

- **27/10 21:15 (rafaga de la noche).** Ciclos: verdes (#2531 a #2538).
  **Entro el premio de la J10** (+1.170.000): saldo **+1.418.975**, 0
  comprometido. La J11 (vie 30/10, plazo 15:00) cubierta con margen.
  Sergi Cardona al 45 % (unico lateral izquierdo): duda para la J11.

- **27/10 21:00 (Pepe: el once sin los que se van, APAGADO).** Workflow de 5
  (entender, construir, 2 revisores, arreglar). El caso: el 26/10 el once
  escrito tenia a Jonny (lo vendia la orden esa noche) y no a Cardona (FF
  50/50; Jonny «Importante» y mas puntos). Nuevo interruptor
  **BORDALAS_EL_ONCE_SIN_LOS_QUE_SE_VAN** (nace apagado; solo lo lee el once
  que se escribe): (1) no alinea a quien se vende ANTES del cierre (la orden
  con su relevo sano dentro, la mejora, la rotacion GANADA, viajes) si hay
  alternativa; nunca a un Dios ni a un intocable; respeta las rondas
  parciales; solo acepta el once nuevo si es igual de completo; (2) Jornada
  Perfecta desempata con FF a menos de 10 puntos, solo si JP dice que el de
  dentro puede no jugar (DUDA/SUPLENTE/NO_CONVOCADO) y el de fuera es
  alineable. Apagado: identico (huella de main). Merge en main. **Encender:**
  tras la J11, en su propia rafaga (no el mismo dia que el parte vende).
  **Hallazgo aparte (pendiente):** con el interruptor apagado, un dibujo de
  emergencia con un jugador en duda (10 alineables) puede ganar a uno
  completo de 11 sanos, y el ejecutor bloquea el SAVE_LINEUP. Con 11 justos
  no cambia nada; con 12+ si. A estudiar.

- **27/10 19:00 (el dueno: la Copa y Reto El Clasico).** «La copa no la
  jugamos, es solo liga»: la Copa no puntua; solo se mira como pista de
  rotacion para la jornada de liga (un titular en Copa a mitad de semana
  descansa mas el fin de semana). «Lo del reto el clasico olvidalo, ademas
  ya ha pasado. Eso fuera»: fuera de config/las_ligas.json y de los
  pendientes (no hay plan multiliga). Se mantiene la proteccion: Pepe solo
  juega El Chiringuito por su id. «El resto guay, sigue mejorando, eres el
  CEO.» Plan de la semana: mie, decision de Cardona; jue-vie, sin encender
  nada; vie-lun, J11; Pepe (apagado entre semana): el once no alinea a quien
  vende la orden y desempata con JP y con quien juega antes del cierre; el
  arreglo de FF para el hueco del vie 21:07-22:07 y para los demas motores;
  la prima de puja segun el tipo de jugador; mar 03/11, encender el parte
  vende.

- **27/10 14:15 (rafaga de la tarde, llego a las 14:50).** Ciclos:
  verdes (#2524 a #2531). Saldo +248.975, 0 comprometido, sin movimientos.
  El premio de la J10 aun no ha entrado. El chat del dueno deja «el parte
  vende» apagado hasta el 03/11 (despues de la J11): bien, nada se
  enciende en la semana del cierre.

- **27/10 12:30 (laboratorio: el parte vende, revision final).** **Rivales:**
  en el reset, Luismi gano a Vivian (1.512.000) a Pollo (1.407.000) y
  compro al 21084 (3.250.001). **Revision final de BORDALAS_EL_PARTE_VENDE
  (2 revisores):** seguro, pero ESTA SEMANA no hace nada (los 11 en el once
  y en conservar) y tenia un choque real con el cambio de Cardona: no leia
  `vender_si_ficha`, asi que podia vender a Cardona por su cuenta al 95 %
  aunque la orden lo estuviera reteniendo (relevo en duda, oferta bajo el
  suelo del gestor). **Arreglado (apagado, merge en main; workflow
  construir + revisor + arreglar):** (1) no toca a nadie de
  `vender_si_ficha.jugadores` ni de `viajes.candidatos` (motivo LA_ORDEN);
  (2) sin la orden encendida y valida no vende a nadie (ORDEN_APAGADA /
  ORDEN_NO_VALIDA; antes, con la orden caducada, conservar y proteger se
  quedaban sin escudo); una fila de la orden sin player_id cuenta como
  orden que no se entiende. Prueba 17/17 (las nuevas fallan sin el
  arreglo); verja 223/223 y con --con. **Encendido: mar 03/11 10:30**, tras
  la J11 (turno programado), con ensayo y la salida del parte guardada en el
  artefacto. **Pendiente:** renovar `caduca` de la orden antes del 30/11.

- **27/10 07:15 (rafaga de la manana).** Ciclos: verdes (#2515 a #2524,
  la de las 07:15 incluida). **Jonny vendido** (ya no esta en la
  plantilla; entro ~1,70 M de madrugada). Saldo **+248.975** en la vuelta
  de las 07:18 (despues del reset), 0 comprometido, 11 jugadores con Kike
  Salas. **La J11 (vie 30/10, plazo 15:00) ya esta en positivo** aunque no
  llegue el premio de la J10.

- **26/10 21:15 (rafaga de la noche).** Ciclos: verdes (#2508 a #2515;
  el interruptor nuevo lleva 9 vueltas verdes). Saldo -1.452.225, 0
  comprometido, sin movimientos. Carrera: a 5 puntos de Pollo17 (chat del
  dueno). Control de caja de la J11: mie 28/10 21:15.

- **26/10 20:47 (laboratorio de rivales).** **Rivales:** Pollo17 vendio al
  Computer a Jonathan David (DEL) por 9.716.300, el dia que bajaba -710.000
  (comprado a Luismi el 18/09 por 8,4 M: +1,32 M en 5 semanas). Es su regla
  de siempre: vender el activo caro en la primera caida fuerte. Luismi y
  Prinzipote, solo lo del reset (Drkusic 746.000, +6,6 %). **Carrera:**
  Pollo 388, Pepe 383 en jornadas cerradas; J10 nuestra 39 (se cierra hoy
  con Sevilla-Osasuna). Valor de plantilla: Pollo 112,5 M, nosotros 59,7 M.
  **Hoy, de produccion:** encendida BORDALAS_LA_JORNADA_DE_CADA_PAGINA (ver
  entrada de las 11:30); la vuelta de las 13:07 refresco el tablero con las
  marcas, sin avisos ni errores. **Aplicado:** nada mas. **Nota del lab de
  la otra sesion (E63/E64):** el precio va una semana por detras de los
  puntos, pero por los que hicieron 8+ ya hay pelea en la subasta (+9 %):
  para revender no queda margen; para el once, si.

- **26/10 14:15 (rafaga de la tarde).** Ciclos: verdes (#2501 a #2508).
  El chat del dueno encendio `BORDALAS_LA_JORNADA_DE_CADA_PAGINA`
  (7ac2f3e3, 11:24 de Madrid): las tres vueltas de despues (12:07, 13:07,
  14:07) verdes. Saldo -1.452.225, 0 comprometido, sin movimientos.

- **26/10 11:30 (ENCENDIDO: BORDALAS_LA_JORNADA_DE_CADA_PAGINA).** Revision
  final de 2 (SAFE_WITH_FIXES). **Lo que habria pasado sin ella:** el plan
  (linea del YAML + paso_0.json) ponia la verja ROJA en la primera vuelta:
  test_el_tablon_v1 exige una frase de QUE_HACE por cada interruptor
  encendido, y ni --con ni el ensayo lo ven (leen el entorno, no el YAML).
  Se habria parado el ciclo, la venta de Jonny de esta noche incluida.
  **Leccion: antes de encender, la verja SIN --con contra el YAML ya
  editado.** Arreglado en el mismo commit: (1) la frase en
  src/telemetry/el_tablon.py; (2) el selector de FF lee la opcion ELEGIDA
  (`selected`), no la primera: en semana de Copa FF pone primero el partido
  de Copa (`data-jornada="1"`) y 9 de 20 paginas de hoy salian sin jornada;
  ahora 20 de 20 (prueba nueva que falla sin el arreglo). Ensayo
  #40300393985 verde (sirvio el tablero de la cache, sin marcas: no ejercita
  lo nuevo; las marcas llegan con el primer refresco, <= 2 h). Paso 0 con
  54, verja 223/223 contra el YAML editado. **Esta semana:** hoy nada
  cambia (todas las paginas son POSIBLE); desde ~20:00 Sevilla y Osasuna
  confirmadas de la J10: la mejora no saca a Kike ni mete a uno de esos dos
  equipos hasta su pagina de la J11. **Pendiente (bajo):** congelar toda
  CONFIRMADA (hueco del vie 21:07-22:07 con el tablero aun en la J(N));
  contar los congelados en la metadata; ronda/chollos/rotacion/cierre no lo
  usan. Si la vuelta siguiente sale roja, se quita la linea del YAML.

- **26/10 07:15 (rafaga de la manana).** Ciclos: verdes (#2492 a #2501,
  la de las 07:15 incluida). Saldo **-1.452.225** a las 07:20 (+250.000,
  la racha), 0 comprometido, reset sin compras ni ventas. Para el vie 30/10
  15:00 faltan ~1,45 M: Jonny (~1,80 M) tras la J10 y el premio de la J10.

- **25/10 21:15 (rafaga de la noche).** Ciclos: verdes (#2485 a #2492).
  Saldo -1.702.225, 0 comprometido, sin movimientos. Plan para el vie
  30/10 15:00 sin cambios (Jonny tras la J10 + premio de la J10). El chat
  del dueno prepara un interruptor nuevo para el lunes (paso 0 en seco
  verde): uno, y con su vuelta vigilada.

- **25/10 20:47 (laboratorio de rivales).** **Rivales:** nada en todo el
  domingo (tablon sin eventos desde el reset). **J10:** 33 pts con 9 de 11
  (faltan Olasagasti, hoy en Anoeta, y Yamal en el Clasico). **Preparado:**
  el paso 0 en seco con TODOS los interruptores (54, incluido el nuevo
  BORDALAS_LA_JORNADA_DE_CADA_PAGINA) pasa en 148 s; config/paso_0.json
  revertido (va en el commit del YAML, manana). **Medido de paso:** la caja
  de los rivales (caja_de_la_liga) solo se desvia mientras una jornada esta
  partida (el premio por partes); hoy no hay ninguna pagada a medias (la J8
  sigue sin pagarse), asi que su arreglo no corre prisa. El cierre de esta
  semana abre el mie 05:00, cuando las paginas del lunes ya traen la J11: no
  le afecta el fallo de las confirmadas. **Aplicado:** nada nuevo.

- **25/10 14:15 (rafaga de la tarde; la de las 07:15 quedo a medias).**
  A las 07:15 Bash no respondio (el clasificador dio error 4 veces): solo
  pude mirar los ciclos por MCP. Comprobado entonces: tras el cambio a
  horario de invierno los disparos siguen a su hora de Madrid (04:45/04:50
  = 03:45/03:50 UTC; 07:15 = 06:15 UTC). Ahora: ciclos verdes (#2477 a
  #2485). **Kike Salas GANADO** (3.439.900, sin rival por encima). Saldo
  **-1.702.225**, 0 comprometido, plantilla 59,73 M. Para el plazo de la
  J11 (**vie 30/10 15:00**): venta de Jonny tras la J10 (oferta ~1,80 M)
  y el premio de la J10 (martes, si la J10 acaba el lunes) => positivo.
  Mi control: el miercoles 28/10 a las 21:15; si no hay venta en marcha,
  aviso al dueno con a quien vender.

- **25/10 10:47 (laboratorio de rivales).** **Rivales:** nada desde el reset
  (Luismi, el 26299 por 446.000). **Corregido (nace apagado):
  BORDALAS_LA_JORNADA_DE_CADA_PAGINA** (merge e6f00878; workflow de 5:
  entender, construir, dos revisores, arreglar). El fallo: cada pagina de
  equipo de FF se leia como pronostico de la jornada siguiente aunque
  mostrara la ALINEACION CONFIRMADA de la que se juega (Cardona 0 %, Chust
  100 % el 24/10). Medido: ~21 % de las horas-equipo de cada semana (vie
  23:00 a ~mar); una confirmada vieja falla un 29 % de media y da un 11,8 %
  de huecos falsos; un pronostico viejo (POSIBLE) solo un 11 % (es lo mejor
  que hay). 4 de las ultimas 15 pujas se hicieron en esas ventanas. El
  arreglo: el tablero apunta la jornada de cada pagina (cabecera de la
  alineacion, selector y «Previsib. J<N>», que coinciden en 199 de 202
  paginas guardadas; cuatro trampas evitadas) y, encendido, la mejora no
  saca a un titular SANO ni mete a un candidato cuya cifra salga de una
  CONFIRMADA de otra jornada (la duda, el lesionado y el sancionado, como
  siempre); avisa si la ventana de 40 h se cierra con alguien congelado y si
  FF cambia la pagina. Apagado: identico (prueba con la huella del tablero y
  de la mejora). Verja 223/223 y con --con. **Para encenderlo (lun 26/10):**
  revision adversarial del diff final, paso 0 con --con, ensayo, linea del
  YAML y config/paso_0.json en el mismo commit; forzar un refresco del
  tablero (la cache de antes no trae marcas). Pendiente aparte: el cierre
  del martes 07:15 sigue leyendo la confirmada de un equipo que jugo el
  lunes.

- **25/10 10:00 (el mejor equipo posible y Roberto por Nino).** El dueno
  pidio el mejor once con los libres y nuestro dinero (58,0 M = plantilla
  59,73 M + caja -1,70 M) y despues: «We can always trade Roberto for Zabiri
  or Adrian Nino in the future». Dos workflows (dos modelos + esceptico, y
  comparar + mecanismo + esceptico). **El mejor once (3-4-3, 57,99 M):**
  Remiro; Juan Iglesias, Chust, Ndukwe; Exposito, Agoume, Ivan Martin,
  Olasagasti; Yamal, Adrian Nino, Boye: ~160 xP en J11-J13 contra ~140 del
  nuestro (+7 por jornada), pero en ritmo de temporada ~54 contra 53,4: es
  una apuesta de forma. Ninguno esta en el mercado: cada libre sale ~2 % de
  los dias. **Roberto por Nino o Zabiri: NO «siempre».** Solo el dia que el
  Computer los saca (Zabiri 0 veces en 39 listas; Nino no desde el 09/10):
  ~1 de 10 antes de la J11, contando la subasta. Nino sube ~340 k/dia y
  Roberto baja ~80 k: el hueco que libera (~5 M hoy) se cierra en ~1 semana.
  En puntos los tres van parejos (segun el modelo, Roberto es el mejor de
  los tres en J11-J13); Zabiri cuesta dinero y tiene 4 amarillas. **No se
  deja una orden esperando** (la mejora resta la puja entera si un dia lee el
  mercado vacio: riesgo de modo deficit). **Aplicado:** «La lista de
  objetivos» en docs/EL-PARTE-DE-LA-PLANTILLA.md, y la supervision de las
  08:22 la mira cada manana en el mercado del Computer y escribe la orden el
  mismo dia si sale uno (con esceptico). Lo urgente sigue siendo Cardona
  (decision del mie 28), que no necesita el dinero de Roberto.

- **25/10 08:22 (supervision).** **Kike Salas GANADO** en el reset (07:04
  CET): 3.439.900; Luismi pujo 3.163.000 (+0,4 %): con el +1 % de la mejora
  (3.189.900) tambien se habria ganado; la prima costo ~250.000 de mas, a
  cambio de asegurar. Luismi compro ademas al 26299 (446.000). Nada mas en
  el tablon. Pepe solo: nada (ronda, chollos y carril NADA_QUE_HACER; la
  orden espera a vender a Jonny: JORNADA_EN_CURSO). Plantilla 12, caja
  **-1.702.225**, 0 pujas vivas, 132 h a la J11. Oferta del Computer por
  Jonny: 1.701.200 (suelo 1.450.000): se vende el mar 27/10 00:07. Racha
  4/5 (la cobra manana, +250.000). **Orden limpia:** Kike sale de fichar y
  pasa a conservar; la venta de Jonny sigue (si_esta 28115 ya en plantilla).
  Mirada del lun 23:05 (Sevilla-Osasuna) en pie.

- **24/10 20:47 (laboratorio de rivales).** **Rivales:** nada desde el
  reset de la manana (tablon sin eventos nuevos). **La carrera (jornadas
  cerradas):** Pollo17 388, **Pepe 383 (-5)**, Luismi 353 (su J6 vale 0 por
  empezar en rojo; sin eso iria primero), Manzagool y DiosMande 308. J10 por
  ahora: Pepe 18, Pollo 0 (no ha jugado ninguno suyo con informe). **Medido
  (workflow de 3): el banquillo, otra vez.** Con 11 justos (J8-J10) perdimos
  4 de 33 huecos (12 %); con banquillo (J1-J7), ~4 %. Solo un cero era
  seguro antes del cierre y no estructural: Jonny en la J10 (0 % a las
  20:15). Rico (J8, J9) era un titular flojo, no falta de banquillo (se
  arregla con un cambio 1 por 1). J9 tenia dos avisos (Rico 30 %, Olasagasti
  0 % y entro y puntuo 3): un 12.o habria ganado ~+0,8, no +3,8. Un 12.o
  vale ~0,3-0,7 pts/jornada y cuesta ~0,35-1,0 (perdida de valor de los de
  <1 M: mediana -11/-13 % en 14 dias): **neto ~0. Se mantiene lo del 20/10:
  sin banquillo fijo, sin 13.o, sin regla en los motores.** Si acaso UNO
  oportunista por la orden: <= 1,0 M, ok, FF >= 70 %, 3+ partidos, 2,5+
  pts/partido, en el mercado del Computer, subasta >= 64 h antes del cierre,
  caja >= +0,5 M en el plazo de la J11 tras pujar, puja <= valor +5 %, y
  mejor un MEDIO (con 4 DEF cubre cualquier ausencia de campo); fuera de
  conservar. Solo ~4 de 38 dias aparece uno asi. **Lo que de verdad paga:**
  cambiar a los titulares flojos 1 por 1 (Kike por Jonny ya; Cardona el mie
  28). Los rivales: banquillo medio Pollo 7, Prinzipote 5,5, Luismi 4,6, Pepe
  2,0; correlacion con los puntos debil (+0,1/+0,2) y mezclada con el valor
  de la plantilla; ningun rival visto usando el banquillo para tapar un
  cero. **Datos:** la J6 parte 3 se puntuo con el once de la parte 2 (ahora
  n=8 onces): el aplazado Rayo-Athletic de la J8 puntuara con el once de la
  J8. **Fallo visto:** marcador.json guarda mi_once desplazado una jornada
  desde la 4902 (pendiente). **Aplicado:** nada. Re-medir en la J16
  guardando el FF del once en cada cierre (artefacto de las 20:07).

- **24/10 21:15 (rafaga de la noche).** Ciclos: verdes (#2461 a #2468).
  Saldo +1.737.675, puja viva Kike Salas 3.439.900 (dom 07:00). Sin
  movimientos. Esta noche Madrid pasa a horario de invierno (UTC+1): manana
  compruebo que las rafagas y el latido llegan a su hora de Madrid.

- **24/10 19:30 (el parte de cada jugador, el primero).** Workflow de 6.
  **Sergi Cardona, suplente en Mestalla** (sano; FF 0 %, Buchanan de
  carrilero): DUDA para la J11 (~35 %), con Carlos Romero volviendo a final
  de mes. Jonny DUDA (cubierto por la orden de Kike). El resto TITULAR
  (75-90 %). No se toca nada hoy (el esceptico tumbo todas las lineas).
  Plan y decision del mie 28/10 en docs/EL-PARTE-DE-LA-PLANTILLA.md. Ojo: la
  mejora puede pujar sola desde el dom leyendo el 0 % de Cardona; mirar el
  objetivo. Fallo de Pepe: el tablero de FF mezcla jornadas por equipo
  (pendiente: comprobar la jornada de cada pagina).

- **24/10 14:15 (rafaga de la tarde).** Ciclos: verdes (#2454 a #2461).
  Saldo +1.737.675; puja viva **Kike Salas 3.439.900** (por Jonny, que no
  jugo la J10; si llega, Jonny se vende tras la J10). Peor caso si entra:
  -1.702.225 hasta cobrar a Jonny (oferta de 1,80 M el 23/10), y hay de
  margen hasta el plazo de la J11. **Gracias al chat del dueno por pillar
  mi error:** la J11 es el **vie 30/10 21:00**, no el dom 01/11; el
  `data/calendar/laliga_calendar.json` esta viejo (dice 01/11) y yo me fie
  de el. **Leccion:** la fecha manda la de Biwenger (first_kickoff del log
  de Pepe), no el fichero del 28/09. Creado mi turno de la J11 para esta
  sesion, vie 30/10 12:50 (trig_01YG8Zb7LBN2wYmsgujup8UG), como segunda
  mirada tras el del chat del dueno (12:45). **Pendiente para quien toque
  el calendario:** refrescar `laliga_calendar.json` (la J11 adelantada).

- **24/10 13:00 (Jonny no jugo; orden para Kike Salas).** El dueno: «Jhonny
  didn't play yesterday». Workflow de 6 (porque, mercado, motores, plan y dos
  esceptivos). **Por que:** decision tecnica de Quique, no lesion: suplente
  sin jugar en Alaves 1-1 Malaga; Valentini lleva 5 titularidades seguidas
  y, con la defensa entera, gano el duelo. J11 en el Camp Nou (sab 31/10
  21:00): FF 50 %, JP 40 %, y el once del Alaves sale DESPUES de nuestro
  cierre (vie 30/10 20:45). ~4 xP en J11-J13. **Pepe solo no hacia nada:**
  la mejora solo entra si Jonny baja de 50 % o si el que llega sube su
  minimo del tramo (Kike +10.000 < 20.000); su prima +1 % es la que perdio
  Catena. **Orden:** fichar **Kike Salas** (Sevilla, 3,15 M, 4,0 pts/partido,
  FF 90 % Clave, ~10 xP en J11-J13) a **3.439.900** (+9,2 %), sin
  la_pagan_sus_ventas; si llega, vender_si_ficha **Jonny** (suelo 1.450.000)
  en la primera vuelta tras la J10 (mar 27/10 00:07). Caja esperada si se
  gana: -1,70 M el dom, -1,45 M el lun (racha +250.000), ~+0,15/+0,33 M tras
  vender a Jonny, y despues el premio de la J10. P(ganar) 0,7-0,85 (DiosMande
  tiene un solo defensa sano y pujo +23,5 % por Revivo). **Contingencia
  (obligatoria):** Sevilla-Osasuna lun 26/10 21:00. Si Kike se lesiona o le
  expulsan, vaciar vender_si_ficha.jugadores ANTES de la vuelta de las 00:07
  (Biwenger tarda en marcarlo) y decidir a mano antes del jue 29/10 12:45:
  (a) vender a Jonny igual con si_saldo_negativo (mejor un hueco que 0
  puntos) o (b) sacar a Kike de fichar y publicarlo. Sin eso, el codigo
  empieza la J11 en rojo (la orden dice NADA FUERA y la mejora cuenta una
  venta fantasma de +1,53 M). Mirada programada el lun 26/10 23:05.
  **Si se pierde el dom 07:00:** el domingo por la tarde, cambiar el objetivo
  (Lago solo si sigue en el mercado y no ve la 5.a amarilla ante el Betis;
  si no, el mejor defensa ok >= 70 % de los mercados dom-mie). Comprobaciones
  de la leccion del 20/10 en la vuelta siguiente: puja viva a 3.439.900,
  caja de la mejora ~-171.670, cierre inactivo hasta el mie 07:15, rotacion
  sin Jonny. **Nuevo turno diario:** «El parte de cada jugador» a las 18:37
  (trig_01DtfCcQ5VtRdskbX5PNFk7g), por orden del dueno («This analysis
  should be done daily on each player»): veredicto de cada jugador, recambio
  si falta y actuar; apunta en docs/EL-PARTE-DE-LA-PLANTILLA.md. Errata de
  codigo vista: el_cierre_de_la_jornada.py:198-202 dice que 64 h antes de un
  viernes 21:00 es «martes 05:00»; es miercoles 05:00.

- **24/10 10:47 (laboratorio de rivales).** **Rivales:** solo el reset de
  las 07:00. Luismi compro cinco (13,74 M: Fornals 5.663.000, Satriano
  3.156.000, Catena 2.621.000, Villares 1.221.000 y Thiago Fernandez
  1.076.000) desde ~0 de caja, a 159 h de la J11; Manzagool, Revivo
  (2.227.000). **Medido (workflow de 3, toda la temporada: 5.671 filas
  rival x jugador en 36 resets del escaparate):** la hipotesis de ayer
  («un rival en rojo cerca de la jornada no puja fuerte») **NO se sostiene**.
  En conjunto, los que estan en rojo pujan MAS (8,7 % / 4,2 % frente a
  2,6 % en positivo), porque los que mas mueven (Luismi, Pollo) son los que
  suelen estar en rojo; y si su deficit es menor que el precio, pujan
  igual cerca de la jornada (5/12 frente a 9/19) y no mas barato (+3,2 %
  frente a +2,6 % de mediana). Ejemplos: Pollo a -6,7 M se llevo a
  Aubameyang a +16,5 % 14 h antes de la J5; luego vendio y empezo en
  positivo. La version estrecha (deficit >= precio y <48 h) salia
  p=0,043, pero **los dos esceptivos la tumban**: cuenta filas como
  independientes (por reset, p=0,08-0,28), depende de tomar la parte 1
  de la J6 como plazo (con splitRound=ignoreFirst el plazo fue la parte 2:
  Luismi vendio 42 min tarde y lo dijo en el chat), y con ese plazo la
  regla falla el 14/09 (Luismi a -5,4 M gana a +7,5 %). Solo aguanta el
  tramo «desde el 16/09», elegido a posteriori, y casi todo es Luismi.
  **Boye y Gaya sin rival: base, no suerte** (el 54 % de las subastas
  cercanas a la jornada de jugadores >=1M que suben no tienen puja rival
  de +1 % o mas). **Manzagool es la amenaza real cerca de la jornada:**
  casi siempre en positivo, puja en el 25 % de esos casos, mediana +7,1 %.
  **Aplicado: nada.** No se toca la prima de la orden ni de la mejora.
  **Dos hallazgos de paso, apuntados:** (1) caja_de_la_liga paga el premio
  de una jornada partida solo en la ultima parte; Biwenger lo paga por
  partes (a Pepe le faltan 870 k entre el 18/09 y el 22/10 en la
  reconstruccion). Afecta a la caja de los rivales que leen los motores de
  analisis, no a la nuestra (la nuestra es la real). Arreglo con test, otro
  dia. (2) Con la jornada partida y ignoreFirst, el plazo de caja es la
  primera parte que cuenta, no la primera que empieza. **Y un error mio,
  corregido:** la J11 NO es el dom 01/11; la adelantaron el 03/10 y empieza
  el **vie 30/10 a las 21:00** (Villarreal-Espanyol; Pepe ya lo sabe:
  first_kickoff 30/10 21:00, cierre 20:45). El turno del domingo
  (trig_01NzaNuaDH69dCE38wMa7wg2) queda pausado; el nuevo es el **vie 30/10
  a las 12:45** (trig_01YPqTGcmBTwP46U7Vdc37rp): plazo de caja a las 15:00.

- **24/10 08:22 (supervision).** Pepe solo, desde ayer (con la J10 ya
  empezada, ventana hacia la J11): la mejora pujo 2.599.900 por **Catena**
  (DEF) para sustituir a Jonny (suplente en Alaves; +3,0 xP por jornada,
  caja -927.900 con deuda permitida a mas de 64 h) y los chollos 1.029.000
  por **Thiago Fernandez**; el carril ya tenia la de Revivo (1.723.901).
  **Las tres perdidas** en el reset: Catena y Thiago, Luismi (2.621.000,
  por 21.100; y 1.076.000); Revivo, Manzagool (2.227.000). Nada vendido.
  Luismi compro cinco (13,74 M, Fornals 5.663.000 entre ellos): vuelve a
  hundirse en rojo. Caja **1.737.675**, 0 pujas vivas; alineacion 4-3-3
  con 11 en la J10. Orden sin nada que limpiar.

- **24/10 07:15 (rafaga de la manana).** Ciclos: verdes (#2445 a #2454,
  la de las 07:15 incluida). Reset: **Revivo PERDIDO** (1.723.901 contra
  2.227.000, +29 %) y **Catena PERDIDO** (2.599.900 contra 2.621.000:
  por 21.100, un 0,8 %). Saldo **+1.737.675**, 0 comprometido, 11 en
  plantilla (sin banquillo). **Dato para el chat del dueno:** Catena se
  pierde por menos de un 1 %; si la puja la hizo un motor con prima fija,
  vale la pena mirar si un escalon mas (p.ej. terminacion o +1 %) habria
  ganado, sin romper el colchon. La J11 es el dom 01/11 (plazo 11:00).

- **23/10 21:15 (rafaga de la noche; la J10 ya ha empezado).** Ciclos:
  verdes (#2443 a #2445). Saldo +1.737.675 al empezar la J10: puntua.
  Puja viva Revivo 1.723.901 (sab 07:00). **Para el fin de semana (no en
  viernes):** el banquillo, empezando por un defensa, y revisar que la
  mejora no vuelva a dejarnos en 11 justos antes de la J11 (dom 01/11,
  plazo 11:00, horario de invierno).

- **23/10 20:47 (laboratorio de rivales).** Desde la manana, solo Luismi:
  vendio a Areso al Computer por 2.302.300 (comprado el 04/09 por 1.151.000:
  **+1,15 M en 49 dias**, el doble) y al 24956 (154.100). Con eso, su caja
  reconstruida queda en ~-5.000 al empezar la J10 (si la reconstruccion
  cuadra al euro, premio 0 otra vez; margen de error de la reconstruccion,
  pequeno pero no nulo). Pollo, en positivo. Areso es otra vez el patron
  de septiembre (comprado barato subiendo y aguantado semanas); desde el
  21/09 ese patron ya no paga en media (laboratorio del 21/10). Nosotros:
  sin movimientos; puja del carril por Revivo viva (1.723.901, se resuelve
  el sab 07:00, con la J10 en juego: no toca la alineacion). Caja al
  empezar la J10: 1.737.675 - 1.723.901 = 13.774. Viernes: sin
  interruptores.

- **23/10 20:15 (segunda mirada al cierre de la J10).** Ciclos: verdes
  (#2438 a #2444, la de las 20:07 incluida). Saldo +1.737.675: solvente.
  Once (artefacto de #2444): 4-3-3, 11 jugables, todos «ok». **Jonny baja
  a 0 %** (a las 12:07, 50 %): con las alineaciones publicadas, parece
  suplente. Sergi Cardona sube a 90 %, Boye y Pablo Ibanez a 100 %. No hay
  recambio (11 justos): nada que hacer a mano. **Para despues de la J10:**
  sigue haciendo falta un banquillo, empezando por un defensa (es la
  segunda jornada seguida que perdemos un titular por no tener recambio).

- **23/10 14:15 (rafaga de la tarde).** Ciclos: verdes (#2436 a #2438).
  Saldo +1.737.675 a las 14:10: el plazo de las 15:00 se pasa en verde.
  Puja viva Revivo 1.723.901 (sab 07:00). Viernes: nada que tocar.
  Segunda mirada a las 20:15.

- **23/10 12:45 (TURNO DEL CIERRE DE LA J10).** Calendario sin cambios
  (J10 hoy 21:00; J11 dom 01/11 17:00, turno ya creado a las 09:45).
  (1) Solvencia: **+1.737.675** a las 12:10: verde para las 15:00. (2) Once
  (artefacto de #2436, 12:07): **4-3-3, 11 jugables, 0 huecos, todos
  «ok»**, con Boye y Gaya. Dudosos: Jonny y Sergi Cardona, 50 %; no hay
  banquillo (11 justos tras vender a Luismi y Exposito). (3) Ciclos:
  verdes (#2431 a #2436). (4) Puja viva: Revivo 1.723.901, se resuelve el
  sab 07:00, con la J10 ya empezada: no toca la caja del inicio; si entra,
  la caja queda en ~+13.774. (5) Segunda mirada a las 20:15 programada.
  (6) Turno de la J11 en pie (trig_01NzaNuaDH69dCE38wMa7wg2).

- **23/10 10:47 (laboratorio de rivales).** Desde anoche: **Pollo17**
  vendio al Computer el 25159 (4.127.100, +4,2 %; 22 dias, -349.900) y a
  Pepelu (2.699.000; 2,1 dias, +92.000): con eso y la racha/premio sale
  del rojo (~+0,75 M) antes de la J10. **Luismi** compro el 33938 por
  241.000 (+20,5 %, sin rival) y sigue en rojo (~-2,46 M): si no vende
  antes de las 21:00, premio 0 de la J10. **Manzagool** vendio el 37719
  (847.700, -5,8 %; +53.870). Nosotros: Boye 5.989.900 (+12,2 %) **sin
  rival**; Luismi Cruz y Exposito vendidos con perdida sobre lo pagado
  (-292.900 en 9 dias y -715.500 en 48: caian). **Lo aprendido (hipotesis,
  n pequeno):** a menos de 24 h de una jornada, los rivales en rojo no
  pujan fuerte por los caros (Boye y Gaya, sin rival; Pollo -11 M y Luismi
  -2 M esa noche). El modelo de la subasta del 22/10 no miraba la caja de
  los rivales ni las horas a la jornada: pagamos ~650k de prima que quiza
  no hacia falta. **A medir** (laboratorio, no hoy): P(rival) segun su
  caja y las horas a la jornada; si se confirma, la prima de la orden y de
  la mejora la tendra en cuenta. Viernes: sin interruptores.

- **23/10 08:20 (mirada tras las ventas).** Vuelta #2432 (08:07) verde:
  vendidos Luismi Cruz (2.959.100) y Exposito (4.431.500). Saldo
  **+1.737.675** a las 08:10, justo lo calculado. **El plazo de la J10
  (15:00) esta cubierto.** La puja del carril por Revivo (chat del dueno)
  se resuelve el sab 07:00, con la J10 ya empezada: no toca la caja de
  hoy. Turno del cierre a las 12:45.

- **23/10 08:15. BOYE, NUESTRO.** Reset de las 07:00: Boye por 5.989.900,
  **sin rival** (nadie mas pujo). En la vuelta de las 07:15 la orden vendio
  a Luismi Cruz (2.959.100) y a Exposito (4.431.500, su oferta nueva del
  reset, como se esperaba): saldo **+1.737.675**. Vuelta de las 08:07:
  alineacion de Biwenger 4-3-3 con 11 (Gulacsi; Chust, Gaya, Jonny,
  Cardona; Olasagasti, Ibanez, Unai; Yamal, Roberto, Boye), 45,4 xP (antes
  42,9). Orden limpia: Boye a `conservar`, fuera el fichar y las ventas
  hechas (19a7a617; verja 222/222). En esa vuelta el carril (RENDIJA) pujo
  por **Revivo** (DEF, 1.720.000, +50k/dia cinco dias seguidos, FF 90 %)
  1.723.901: caja al empezar la J10, 13.774 >= 0; se resuelve el sab 07:00
  con la J10 en juego (no cambia la alineacion). Se deja: sube de verdad y
  pasa la puerta de solo si sube del carril.

- **23/10 07:15 (rafaga de la manana, DIA DEL CIERRE DE LA J10).** Ciclos:
  verdes (#2422 a #2431). **Boye GANADO** (5.989.900). Saldo a las 07:19:
  **-5.652.925**, 0 comprometido, 13 en plantilla. Ofertas vivas del
  Computer (artefacto de #2431): **Exposito 4.431.500** (si llego, por
  encima del suelo de 3.050.000) y **Luismi Cruz 2.959.100**: juntas
  7.390.600 => **~+1.737.675** cuando la orden las cobre (vuelta de las
  08:07). Once 3-4-3, 11 jugables, todos «ok». Programada una mirada a las
  08:20 (trig_01VHZqLmwkce7RahxKkbeeVD); el turno del cierre, 12:45. Hoy
  no se construye nada.

- **22/10 21:15 (rafaga de la noche).** Ciclos: verdes (#2415 a #2422).
  Entro el premio de la J6 (+330.000): saldo **+336.975**, puja viva Boye
  5.989.900 (vie 07:00). **CORRECCION MIA (por E56 del chat del dueno):**
  el 21/10 escribi «cada aplazado es una ronda aparte y un plazo de caja
  propio». Es falso: la parte aplazada se puntua con el once y la caja del
  inicio de la jornada (n=2). El plazo del 21/10 no hacia falta (no costo
  nada) y el Rayo-Athletic de la J8 NO necesita turno de caja propio. Lo
  que si queda: el roundStarted nuevo no significa ronda con plazo nuevo.
  Peor caso del vie si entra Boye: 336.975 - 5.989.900 + Luismi 2.959.100
  + Exposito (>= 3.050.000) => >= +356.175; sin oferta por Exposito,
  -2,69 M. Turnos del vie: chat del dueno 07:25, yo 12:45.

- **22/10 20:47 (laboratorio de rivales). CONFIRMADO: LA PARTE APLAZADA SE
  PUNTUA CON EL ONCE DEL INICIO DE LA JORNADA (n=2).** La ronda 5176
  (Levante-Athletic) cerro a las 16:23: nuestra J6 pasa de 29 a **40**
  puntos (+11) y cobramos la diferencia, **+330.000** (saldo 336.975).
  Los +11 son exactamente los del once del 15/09: Olasagasti +5, Manu
  Sanchez +3, Oriol Rey +3 (con el once de hoy habrian sido solo los +5 de
  Olasagasti). Totales de la J6: Luismi 64 (premio 0: empezo en rojo,
  E52), Manzagool 52, DiosMande 52, Pepe 40, Prinzipote 36, Alvaro 29,
  Pollo17 24, Mex 13. **Rivales:** Pollo vendio a Tchouameni al Computer
  (4.370.300, +1,6 %; comprado el 19/10 a 4.277.000, +93k en 3 dias): su
  caja, ~-6,1 M con el premio de la J6; tiene que vender ~6,1 M mas antes
  de la J10 (vie 21:00). Luismi sigue en ~-2,2 M. **Nosotros:** puja por
  Boye viva (5.989.900); si llega, con la venta de Luismi la caja queda en
  -2,69 M y la de Exposito la deja en ~+1,8 M. Hoy es jueves: sin
  interruptores. Comprobacion propia manana a las 05:25 UTC.

- **22/10 14:15 (rafaga de la tarde).** Ciclos: verdes (#2408 a #2415).
  Saldo +6.975; puja viva **Boye 5.989.900** (orden del dueno, vie 07:00).
  Leido el plan del chat del dueno y lo doy por bueno: si entra, se venden
  Luismi Cruz (oferta viva 2.959.100) y Exposito (oferta del reset del
  vie, suelo 3.050.000) => ~+1,47 M. **El riesgo que queda:** si el
  Computer no ofrece por Exposito el viernes, la J10 empezaria en -3,02 M
  (0 puntos); el chat del dueno tiene su turno el vie 07:25 y yo el de la
  J10 a las 12:45, ambos antes del plazo de las 15:00. Si a las 12:45
  sigue en rojo, aviso al dueno con a quien vender (con oferta viva, nunca
  Yamal).

- **22/10 14:15. LAS LIGAS.** El dueno se apunto sin querer a una segunda
  liga, **Reto El Clasico (2210645)**. Pepe elegia la PRIMERA liga de la
  cuenta (`leagues[0]`): ahora juega El chiringuito por su id (2165477,
  `config/las_ligas.json`) y, si no estuviera en la cuenta, se para
  (2960ff1d). Cada vuelta escribe las ligas de la cuenta: #2415 (14:07)
  verde, «Liga: El chiringuito (2165477); en la cuenta: El chiringuito,
  Reto El Clasico». **Cambiar de liga AUN NO SE PUEDE** (revision
  adversarial): el tablon, las caches, las posiciones, el marcador, las
  pujas y la orden no llevan liga; una vuelta en otra liga borraria o
  mezclaria los de El chiringuito y la orden podria pujar por Boye alli.
  `test_las_ligas_v1` para la verja si se intenta, a proposito (3cf4be2c,
  fdc3dfe3). **Error mio:** 3cf4be2c subio con la verja en rojo (mi comando
  no paraba si fallaba); arreglado en 6 minutos (fdc3dfe3), antes de
  ninguna vuelta. Desde ahora: subir solo dentro de `if verja; then`.
  Jugar las dos ligas: separar los libros por liga; plan y coste al dueno
  despues de la J10.

- **22/10 10:47 (laboratorio de rivales).** Workflow de 4 (rivales; la
  subasta de Boye; un escéptico por informe, ninguno refuta). **Puja por
  Boye puesta** (vuelta de las 11:07: 5.989.900, http 200; el cierre la
  cuenta pagada por sus ventas, EN_POSITIVO, sin escrituras). **Rivales:**
  en el reset Pollo17 gano a Cubarsi (Barcelona, DEF, 8.407.000, +4,2 %;
  Luismi 8.221.000); Luismi vendio a Ilaix (-59.800) y Danjuma (+74.699).
  Cajas: Pollo **-11,27 M** (tiene que vender ~11,3 M de banquillo antes de
  la J10), Luismi -2,22 M. Patrimonio: Pollo +51,09 M sobre nosotros; su
  once por precio, 84,3 M (+27,3 M). La parte aplazada de la J6 (ronda
  5176) aun sin roundFinished. **La subasta de Boye:** es el unico de mas
  de 3 M que sube hoy; P(ganar) a 5.989.900 (+12,2 %) ~85 % con toda la
  temporada, **~75 % con octubre** (los rivales pujan mas fuerte desde el
  01/10). Amenaza: Manzagool (caja +1,04 M, le falta un delantero, sus
  ultimas pujas por los que suben +13,6 % a +32,3 %). Subir no compensa
  (6,08 M: ~0,8-2,6 M por victoria extra); bajar tampoco. **Se queda.**
  **La caja si se gana:** la oferta de Exposito muere en el mismo reset; la
  nueva llega cada 2 dias (patron de toda la temporada), pero si no
  llegara, la J10 empezaria en -3,02 M (premio 0). Turno propio mio el vie
  23/10 a las 05:25 UTC para comprobarlo y, si hace falta, vender a otro con
  oferta antes de las 14:00 UTC. Hoy es jueves: ningun interruptor.

- **22/10 11:00. BOYE, POR ORDEN DEL DUENO («ok, do it»).** Boye (Alaves,
  DEL, 5,34 M, FF 90 %, 58 pts en 8 partidos) salio al mercado; Pepe no
  podia pujar: caja 6.975 (Gaya) y el reloj de 40 h antes de la J10 (vie
  21:00) frena toda compra que se pague vendiendo, aunque nuestros
  titulares tengan ya oferta viva del Computer (el mismo hueco que con
  Kubo). **Hecho:** nueva marca del gestor en la orden,
  `la_pagan_sus_ventas` (solo si se escribe): el fichaje puede pujar dentro
  del reloj si las ofertas vivas por los que salen por EL (el `si_esta`
  general) pagan la puja entera, y solo si se resuelve en el proximo reset
  con 2 h o mas antes del partido. El cierre cuenta esa puja por lo que sus
  ventas no cubren (sin esto vendia a Cardona por un agujero de 5,98 M que
  no existe). Orden: fichar Boye 5.989.900; si llega, se venden Luismi Cruz
  (oferta viva 2.959.100) y Exposito (la del reset del vie; suelo 3.050.000,
  lo minimo que deja la J10 en >= 0). Once 4-3-3 con Boye y Cardona, +1,4/
  +2,0 xP por jornada; caja tras las ventas ~1,47 M. **Dos revisiones
  adversariales** (4 agentes): la primera, NO (el cierre vendia a Cardona;
  sin limite de hora; emparejamiento distinto del de la venta; dos fichajes
  contaban la misma caja); arreglado todo; la segunda, SAFE TO PUSH con 5
  arreglos menores, tambien aplicados (credito solo con la orden viva, no
  si la puja viva supera la escrita, con lo cobrado en la vuelta, el
  `_la_paga_la_caja` cuenta lo ya pujado, el credito en el plan y el log).
  Simulacion de la cadena orden+cierre: jueves EN_POSITIVO sin escrituras;
  ganado, +1.466.475 y 11 en 4-3-3; perdido, nada. Verja 221/221. Riesgo
  aceptado: si la oferta nueva por Exposito baja de 3,05 M (-33 %), la J10
  empezaria en rojo; lo miro el vie a las 08:22.

- **22/10 08:22 (supervision).** Vuelta #2409 (08:07). En el reset de las
  07:00 entro **Gaya** (puja del dueno, 1.711.008, sin rival); nada perdido.
  Pepe solo: 0 compras, 0 ventas (la ronda, los chollos, la orden, la
  mejora y la rotacion, NADA: caja libre 6.975). Saldo **6.975**, 12
  jugadores, 58,24 M. Once de la J10 (3-4-3, 42,9 xP): Gaya entra, Sergi
  Cardona al banquillo (FF 50 %, como Jonny, que va por xP). El cierre,
  EN_POSITIVO, no vende nada. **Caja de la J10** (vie 21:00, a 36,8 h):
  6.975 >= 0, sin pujas vivas. **Orden:** Gaya a `conservar` (fichaje del
  dueno y titular; E14); verja 221/221. Rivales en el reset: Pollo17 gano
  al 32440 por 8.407.000 (Luismi 8.221.000); Luismi vendio dos al Computer
  (3.401.200 y 2.544.700). Clasificacion (solo rondas cerradas, con la J9):
  Pollo 381, **Pepe 372**, Luismi 353. La parte aplazada de la J6 (ronda
  5176) aun no tiene roundFinished: el once del 15/09, por comprobar.

- **22/10 07:15 (rafaga de la manana).** Ciclos: verdes (#2399 a #2408).
  **Gaya GANADO** (1.711.008, sin rival por encima). Saldo **+6.975** a las
  07:18, 0 comprometido, plantilla 58,24 M (12 jugadores: por fin uno de
  banquillo). Para la J10 (vie 23/10, plazo 15:00) estamos en positivo pero
  al limite: **cualquier puja que se resuelva el vie 07:00 sin una venta
  que la cubra nos deja en rojo**. Lo miro esta tarde y esta noche; el
  turno del vie 12:45 lo confirma. Jueves: no se enciende nada.

- **21/10 21:15 (rafaga de la noche).** Ciclos: verdes (#2397 a #2399).
  Saldo +1.717.983, puja viva Gaya 1.711.008 (jue 07:00). Segun el chat del
  dueno, Pollo17 y Luismi empezaron la parte aplazada de la J6 en rojo:
  nosotros no. Turno del cierre de la J10 en pie (vie 23/10 12:45); el de
  la J11 lo crea ese turno: **ojo, la J11 empieza el dom 01/11 a las
  17:00 (horario de invierno, UTC+1), asi que el plazo T-6 es a las 11:00
  y el turno tiene que ser a las 09:45 de Madrid (08:45 UTC), no a las
  12:45 de siempre.** Creado ya: dom 01/11 09:45 (trig_01NzaNuaDH69dCE38wMa7wg2).
  Viernes: no se enciende nada.

- **21/10 20:47 (laboratorio de rivales).** Desde el reset, dos ventas al
  Computer y las dos con perdida: **Pollo17** vendio a Espi (comprado el
  19/10 a 2.777.000, +7,2 % y subiendo) por 2.521.300 a los 2,1 dias
  (-255.700), el primer dia que bajaba; **Manzagool** a Fran Garcia
  (comprado el 20/09 a 5.135.070) por 3.924.400 tras 31 dias (-1.210.670).
  Las dos cuadran con lo medido esta manana: prima alta en 1-3 M y
  aguantar en >3 M pierden. Cajas al empezar la parte aplazada de la J6
  (ronda 5176, 18:00 UTC), reconstruidas del tablon: Pollo -2,86 M (vendio
  y cobro la racha, no llego), Luismi -8,17 M (nada), Manzagool +1,04 M:
  **Pollo y Luismi cobran 0 por esa parte** (E52); nosotros, +1.717.983.
  Distancia de patrimonio con Pollo, ~50,4 M. **Nosotros:** la ronda, los
  chollos, la orden, la mejora y la rotacion, NADA en la vuelta de las
  20:07 (la caja libre es 6.975: la puja del dueno por Gaya, 1.711.008, se
  lleva el resto; se resuelve manana a las 07:00). Sin cambios ni
  interruptores esta noche. Manana: comprobar los puntos de la parte
  aplazada (el once del 15/09) y si llego Gaya.

- **21/10 20:30 (mirada al aplazado de la J6). RESUELTO: ES RONDA PROPIA.**
  En `data/rival_intelligence/board_events.json` aparece un «roundStarted»
  nuevo a las 18:00 UTC (20:00 de Madrid): ronda **5176, «Jornada 6
  (aplazada)», part 3**. El saldo a esa hora era **+1.717.983** (vuelta
  de las 20:07, #2398 verde): Pepe la empieza en positivo y sus puntos
  cuentan. **Regla que queda:** cada aplazado es una ronda aparte y un
  plazo de caja propio. El siguiente sera el Rayo-Athletic de la J8 (Unai
  Lopez en el once) cuando tenga fecha: crear su turno en cuanto salga.

- **21/10 14:15 (rafaga de la tarde).** Ciclos: verdes (#2390 a #2392).
  Saldo +1.717.983 a las 14:10: el plazo del aplazado (14:00) PASADO EN
  VERDE. Puja viva Gaya 1.711.008 (jue 07:00). Nada mas; a las 20:30 miro
  si el aplazado abrio ronda propia.

- **21/10 13:15. EL PARTE VENDE, ARREGLADO (sigue APAGADO).** Dos rondas
  de arreglos con revision adversarial (workflows de 3 agentes cada uno).
  Ronda 1 (ac13f484): D1 no vende un fichaje de menos de 7 dias (fechas de
  compra del tablon); D2 sin el once de Biwenger (GET /user caido) no se
  hace nada; D3 el sancionado no se vende (un partido, sin medir). Los
  revisores encontraron dos huecos y ronda 2 (6c814023) los cierra: H1, un
  fichaje no se vende hasta que acaba una ronda PRINCIPAL que empezo
  despues de su llegada (E14: el paron de noviembre y Navidad), nunca
  antes de 7 dias, y sin ronda conocida tras el fichaje no se vende; H2,
  con el tablon atrasado nadie tiene fecha y no se vende a nadie. Segunda
  revision: 0 defectos de venta (30.000 casos al azar sobre el calendario
  real, 0 violaciones); solo un hueco de la guardia (el filtro `aparte`),
  cubierto por mi (5be80a4f; la mutacion ya la pilla). Verja 221/221 con
  los de produccion y con `--con BORDALAS_EL_PARTE_VENDE`. Pendiente para
  encenderlo (mar 27 o mie 28/10, tras la J10): paso 0, ensayo y la linea
  del YAML con config/paso_0.json en el mismo commit.

- **21/10 12:45 (TURNO DEL APLAZADO DE LA J6).** Ciclos: verdes (#2385 a
  #2390). Saldo **+1.717.983** a las 12:10, el plazo de las 14:00 CUBIERTO.
  Puja viva de Pepe: **Gaya 1.711.008** (la rendija, de las 07:19), se
  resuelve el jue 22/10 07:00, despues del aplazado; si entra, peor caso
  +6.975: sigue en positivo para la J10 (vie 23/10, plazo 15:00), pero
  justo. Kubo se lo llevo Pollo17 (3.407.000). Programada la mirada de las
  20:30 (trig_01Qh1ZrwmiJLTRFcTinyESnd) para ver si el aplazado abrio
  ronda propia.

- **21/10 10:47 (laboratorio de rivales).** Workflow de 7 (rivales, el
  horizonte de las primas, el parte vende; 2 escepticos por conclusion,
  ninguno la refuta; `scratchpad/lab2110/`). **Rivales:** en el reset de
  las 07:00 Pollo17 gano Kubo (3.407.000, +18,3 %), Pepelu (2.607.000,
  +6,4 %), Gorrotxategi (1.077.000, +22,4 %) y Riedel (1.007.000, +13,1 %,
  sin subir), tres de ellos sin rival; Manzagool, De Jong (2.870.000, +32,3
  %). Tras el reset Pollo esta 648k por debajo de lo pagado y Manzagool
  600k. Luismi vendio a Zakharyan (+350k en 26 dias, el primer dia sin
  subir) y a Cordoba. **Los tres de arriba, en rojo** antes del aplazado de
  esta noche: Pollo -5,63 M, Luismi -8,17 M, Manzagool -2,89 M (premio 0 de
  esa parte si siguen asi). Nosotros +1.717.983 (6.975 si gana Gaya).
  Patrimonio: Pollo +50,11 M sobre nosotros; su once por precio, +24,56 M.
  Con nuestra cartera (+4 % en 1-3 M) habriamos perdido los 4. **Lo
  aprendido (219 subastas, 23/08-21/10):** aguantar MAS no rescata las
  primas: en 1-3 M y >3 M el mercado cae ~3,5-4,5 % cada 14 dias; vender el
  primer dia que no sube gana +97,8k por compra y le saca 245k a aguantar
  14 dias y 349k a aguantar 28 (IC 80 % fuera del 0). Pollo aguanta una
  mediana de 6 dias, no semanas; su ventaja es el precio de venta, no
  aguantar. Desde el 21/09 todas las reglas pierden dinero (el mercado
  ya no infla). **Sin cambios** en PRIMAS_DE_LA_CARTERA ni en la regla de
  venta; para mas adelante, «vender en la primera bajada» (+6k por compra
  en 1-3 M). **El parte vende: NO se enciende hoy** (no ganaria nada: 10 de
  11 en conservar/proteger y nadie con parte malo) y tiene 3 defectos
  reproducidos: vende a un fichaje recien llegado (Gaya), el once de
  Biwenger es opcional si falla GET /user, y vende al sancionado de un
  partido. Arreglos en marcha (apagado); encender el mar 27 o mie 28/10.

- **21/10 08:22 (supervision).** Vuelta #2386 (08:07). Racha cobrada
  (+250.000, 01:11): saldo **1.717.983**. Pepe no hizo nada solo desde
  ayer: 0 compras, 0 ventas (la ronda, los chollos, la orden y el carril,
  NADA; el aplazado frena la compra hasta las 20:00). En el reset de las
  07:00 no teniamos pujas: nada ganado ni perdido. **Kubo** se lo llevo
  Pollo17 por 3.407.000 (+18 %; Manzagool 3.380.000, Luismi 3.256.000): el
  tope de 3.090.000 que propuse habria perdido. Pollo tambien gano a Pepelu
  (2.607.000, +6,4 %), Gorrotxategi (1.077.000, +22 %) y otro por 1.007.000;
  Manzagool, a De Jong (2.870.000, +32 %). **Puja viva:** Gaya (Valencia,
  lateral, 1.710.000) por 1.711.008, puesta a mano desde la app (Pepe la ve
  como `pujas_del_dueno`); FF: 80 %, no esta en el parte de bajas del
  Valencia. Se resuelve el jue 07:00, despues del aplazado. **Caja:** al
  empezar el aplazado (hoy 20:00), 1.717.983 - 1.711.008 = **6.975 >= 0**;
  con Gaya, J10 en 6.975. Orden limpia: fuera la linea de Kubo/Luismi
  (Kubo no llego); verja 221/221.

- **21/10 07:15 (rafaga de la manana, dia del aplazado de la J6).** Ciclos:
  verdes (#2376 a #2385, la de las 07:15 tras el reset incluida). Saldo
  **+1.717.983** a las 07:19 (entro la racha, +250.000), 0 comprometido,
  plantilla 56,48 M y 11 jugadores, sin Kubo: la puja del dueno no entro
  (saldo y plantilla no cambian), asi que Luismi Cruz no se vende. **El
  plazo de hoy 14:00 esta cubierto.** Turno de las 12:45 en pie.

- **20/10 21:15 (rafaga de la noche).** Ciclos: verdes (#2369 a #2376).
  **El premio de la J9 ENTRO:** saldo **+1.467.983** a las 21:09 (+1,47 M).
  0 pujas de Pepe. El dueno puja por Kubo desde la app (se resuelve mie
  07:00); la orden ya tiene el plan si llega: vender a Luismi Cruz a su
  oferta del Computer (2.958.000) en la vuelta siguiente, antes del
  aplazado. Peor caso del mie: +1.467.983 + racha 250.000 - Kubo, tapado
  por Luismi en la vuelta de las 08:07. Mi turno del mie 12:45 lo
  comprueba con la vuelta de despues del reset, no con una anterior.

- **20/10 20:47 (laboratorio de rivales).** **Rivales:** premio de la J9
  pagado a todos (30.000/punto + plus a los tres ultimos, E52): Luismi
  1,98 M, Pollo 1,83 M, Manzagool 1,56 M, Pepe 1,47 M. Solo dos ventas al
  Computer: Pollo, Ruben Sanchez a +3,3 % (subia; 15,5 dias; +435k) y
  Luismi, Alvaro Carreras a +2,3 % (-5,6k). Cajas: Pollo +2,46 M, Luismi
  **-9,07 M**, Manzagool -19k: si siguen en rojo el mie a las 20:00 cobran
  0 por la parte aplazada. Pollo: patrimonio 108,41 M frente a 57,96 M
  (distancia 50,46 M); su once por precio, 24,1 M mas caro. **Kubo:** nadie
  lo tiene; a las 20:09 no habia puja nuestra (la orden ya vende a Luismi
  si llega). **El aplazado frena la compra 40 h** (hallado hoy): cuesta UN
  reset por ronda aparte (este, el del 21/10; ~10 rondas aparte mas en la
  temporada). Disenado y construido APAGADO (la orden, la mejora y el
  cierre; la ronda y los chollos, no). Con el interruptor apagado es
  identico a main (fuzz de 3.000 casos), pero la revision adversarial
  encontro defectos con el encendido: (1) ALTO, la orden deja pasar un
  segundo `fichar` sin pareja por `_la_paga_la_caja` sin contar las pujas
  de la misma vuelta; (2) ALTO, el cierre cancela la puja que genera el
  credito y se queda con el credito (hay que llevarlo por relevo o poner
  esos relevos en no_retirar); (3) los chollos de las 04:50 no ven la puja
  de la orden de la misma vuelta; (4) el umbral de 40 h a la principal se
  mide distinto al pujar y al cobrar; (5) se acredita a un saliente ya
  vendido en la vuelta; (6) la orden que caduca antes del cobro; (7) la
  publicacion se compara con el inicio y no con el cobro. **NO va a main:**
  guardado en `claude/ecstatic-turing-j6tgw6` (0167687d) para arreglarlo
  con calma; la proxima ronda aparte (Rayo-Athletic) no tiene fecha.

- **20/10 14:15 (rafaga de la tarde).** Ciclos: verdes (#2362 a #2369).
  Saldo -2.017 a las 14:10, 0 comprometido; el premio de la J9 aun no ha
  entrado (ventana 12:00-17:00). El chat del dueno APAGO la puerta a
  precio de mercado (6080b86d: 2 ofertas y 0 aceptadas): bien, un
  interruptor menos que vigilar. Control: hoy 21:15 (premio dentro o no).

- **20/10 10:47 (laboratorio de rivales).** Workflow de 8 (rivales,
  nuestras tacticas, el coste de los ceros, huecos, 2 escepticos por
  hallazgo; `scratchpad/lab2010/`). **Rivales:** en el reset del 20/10
  nadie gano ni vendio nada (0 subastas; ultimo movimiento del tablon, la
  venta de Rico). Pollo17 sigue ganando por aguantar: +5,70 M en 7 dias, de
  ellos +5,50 M sin tocar su plantilla del 13/10 y -0,05 M por operar;
  patrimonio 106,55 M frente a 56,49 M (distancia 50,06 M, +0,83 M al dia);
  su once por precio, 80,6 M frente a 56,5 M. **Correccion:** Pollo SI
  opero: vendio a Sucic al Computer el 18/10 (5,42 M) y gano a Tchouameni
  (4,28 M, +0,2 %) y Espi (2,78 M, +7,2 %) en el reset del 19/10; caja
  -0,38 M. Luismi gano a Carvajal a +33 % (4,26 M; vale 3,44 M), va a -12,14
  M y ha pasado a publicar 10 a su valor (x1,00, antes x1,5): necesita
  vender ~12 M antes de la J10. Manzagool -1,58 M. **Nuestras tacticas:** la
  cartera y la mejora solo si sube, 0 pujas desde el 17/10 (sin caja); la
  puerta, 2 ofertas y 0 aceptadas en su vida; el informe de la manana
  acierta la subida del dia siguiente 17 de 27 (base 6/27), pero los de
  nota 2,0 justa (menos de 1 M y sin subir) solo 1 de 9. **Los ceros:** esta
  liga NO tiene suplentes automaticos (lineupReserves false): un banquillo
  solo sirve si se mete en el once antes del cierre. Nos costaron 3 ceros en
  33 huecos (J7-J9), ~5 de los 28 puntos de la J8 con Pollo; dos suplentes
  baratos valen 0,2-0,5 pts por jornada: **el punto 7 del laboratorio baja
  de prioridad**. **La prima segun la subida (punto 5):** NO se construye;
  en 1-3 M no se ve ganancia frente al +4 % (+8 % es una moneda al aire) y
  +1 % parece mejor con solo 2 victorias que lo decidan; se repite el 31/10.
  **Aplicado:** la puerta APAGADA (la colchoneta solo le cobra puja - 0,92 x
  valor: el mie por la noche mandaria ~4 M en ofertas que la rotacion cuenta
  enteras); verja 221/221. Y retirado mi ultimo recurso de las 08:22 (ver
  abajo).

- **20/10 11:55. RETIRO MI ULTIMO RECURSO DE LAS 08:22 (error mio).** El
  `vender_si_ficha` con `si_saldo_negativo` (Luismi Cruz) lo leen otros
  motores como venta YA en marcha: la mejora conto +2,11 M que no existen
  (caja de la jornada 2.109.093 en #2364-#2366, en vez de -2.017; no pujo
  de milagro), el cierre armo el once de la J10 con 10 (39,3 xP, sin
  Luismi) y la rotacion no podia tocarlo (LO_VENDE_OTRO_LIBRO). El ultimo
  recurso es de antes (29/09) que la mejora y el cierre, y nadie lo
  integro con ellos. **Ademas sobraba:** nuestros titulares ya tienen
  ofertas vivas del Computer (Luismi 2.958.000 hasta ~jue 07:00, Jonny
  1.900.400, Chust 1.725.200...): si la racha fallara, una linea en la
  orden el mie por la manana se cobra en la vuelta siguiente, antes de las
  20:00. Orden de vuelta a `vender_si_ficha` vacio; verja 221/221.
  Pendiente (no urgente): que la mejora, el cierre y la rotacion solo
  cuenten un `si_saldo_negativo` cuando de verdad toca (saldo < 0 y pasado
  `desde`). Leccion: una linea de la orden mueve a TODOS los motores;
  antes de escribirla, mirar la caja de la mejora y el once del cierre en
  la vuelta siguiente.

- **20/10 08:22 (supervision).** Vuelta #2363 (08:07). Reset sin
  movimientos (0 pujas vivas: nada ganado ni perdido). Desde ayer, una sola
  operacion de Pepe: la mejora vendio a Rico al Computer (430.300). Saldo
  **-2.017**, plantilla de 11 (56,49 M); la ronda, los chollos, la orden,
  la mejora y la rotacion, NADA (sin caja). El informe de la manana: 20
  nuevos, arriba Kubo (+7,5 %) y Osambela (+21,1 %). **Plazo del mie 21/10
  20:00:** la racha va 4 de 5 y se ha cobrado 7 de 7 veces, cada 5 dias, en
  la vuelta de la 01:07 (+250.000 => +247.983). Por si falla, la orden
  lleva un ULTIMO RECURSO: Luismi Cruz (el que mas cae de los
  prescindibles, -60k/dia, xP 2,3) se publica solo si a partir del mie
  01:30 seguimos en rojo, y se acepta la oferta del Computer del reset de
  las 07:00 (suelo 2 M). Simulado en los 7 casos; verja 221/221. Rico
  fuera de `conservar`. El mie a las 08:22 se borra el ultimo recurso.

- **20/10 07:15 (rafaga de la manana).** Ciclos: UNA ROJA, ya arreglada
  por el chat del dueno: #2355 (mar 20/10 00:07 de Madrid), la guardia
  de la titularidad leia
  el tablero de FF de disco (886d30bc); #2356 de las 00:19 verde y verdes
  desde entonces (#2356 a #2362). **Venta:** Diego Rico vendido por la
  mejora (430.300). Saldo a las 07:19: **-2.017**, 0 comprometido. Con el
  premio de la J9 (hoy 12:00-17:00) y la racha (mie 00:10) queda de sobra
  en positivo para el plazo del mie 21/10 14:00. Control: hoy 21:15.

- **20/10 00:23 (verja roja y venta de Rico).** La vuelta de las 00:07
  (#39332653635) se paro en la verja: la guardia nueva de la titularidad
  leia el tablero de FF del cache de produccion (en local no hay `data/`
  y pasaba). Arreglada para no leer disco (886d30bc) y relanzada a mano
  (#39334128386): todo verde. En esa vuelta **la mejora acepto la oferta
  del Computer por Diego Rico (430.300, http 200)**: caja -2.017 para el
  aplazado del mie 21/10 20:00. La cubre la racha (+250k, ~21/10 00:10) o
  el premio de la J9. La rotacion ya solo frena a titulares de Levante y
  Athletic. Leccion: una guardia que lee `data/` en CI ve lo de produccion.

- **19/10 21:15 (rafaga de la noche).** Ciclos: verdes (#2345 a #2352).
  Saldo -432.317, 0 comprometido, sin movimientos. Leido lo del chat del
  dueno: la J8 sigue abierta (Rayo-Athletic suspendido) y al cerrarla
  vamos segundos a ~27 puntos de Pollo17; ese Rayo-Athletic, cuando tenga
  fecha, sera OTRO plazo de caja (lo apunto para crear su turno en cuanto
  salga en el calendario). Para el mie 21/10 nada cambia: premio de la J9
  manana, control mio manana a las 21:15.

- **19/10 20:47 (laboratorio de rivales).** Sin reset desde la manana: el
  tablon no trae compras ni ventas. Nosotros: -432.317, 0 pujas; Rico con
  oferta de 430.300 (caduca en 35 h) para la mejora desde el 20/10 00:00. En
  marcha el experimento 'el once con nuestro dinero' (mejor once posible con
  56,6 M, camino realista con el mercado de cada dia, Yamal en numeros):
  Pollo no nos gana especulando sino con un once que vale 23,4 M mas (~10
  puntos por jornada).

- **19/10 tarde. CORRECCION DEL DUENO: la clasificacion 323-320 NO es la
  real.** Solo cuenta las jornadas cerradas (hasta la J7). La J8 sigue
  abierta por el Rayo-Athletic suspendido, y en ella Pollo17 hizo 74 y
  nosotros 44: al cerrarla iremos SEGUNDOS, a unos 27 puntos (394-367),
  mas lo que deje la J9 (nosotros 43 con Unai por jugar). El panel de la
  carrera (`race`) dice LIDER por lo mismo: hay que corregirlo para que
  cuente las jornadas abiertas como provisionales. Y el Rayo-Athletic,
  cuando tenga fecha, sera otra ronda aparte (como el Levante-Athletic):
  otro plazo de caja, con Unai Lopez en el once.

- **19/10 14:15 (rafaga de la tarde).** Ciclos: verdes (#2338 a #2345).
  Saldo -432.317, 0 comprometido, sin movimientos. Nada que cambiar: hoy a
  las 21:00 el Getafe-Rayo cierra la J9; el premio, manana 12:00-17:00.

- **19/10 10:47 (laboratorio de rivales).** Reset del 19/10: Luismi gano a
  Carvajal por 4.256.000 (+33 %; hoy vale 3,34 M: -916k en papel) y a Danjuma
  (valor + 1 euro), y queda en -12,14 M de caja; Pollo17 rompio su parada:
  vendio a Sucic al Computer (+2,64 M tras 48 dias), gano a Tchouameni (a
  valor, sin subir) y a Espi (+7,2 %), perdio a Carvajal pujando 3.777.000
  (+18 %) y queda en -0,38 M. Cuatro en negativo antes del aplazado del
  21/10 (Pollo, Luismi, Manzagool, nosotros). Distancia con Pollo: 49,27 M
  (+0,8 M al dia); puntos 323-320 a nuestro favor con la J9 sin cerrar. Las
  compras de la semana de los rivales pierden en papel (Pollo -1,30 M,
  Luismi -1,14 M): su ventaja es lo que ya tienen, no lo que compran. El
  informe de la manana del 18/10 puntuo a 3 de los 4 que se llevaron
  (Carvajal sube +35, el mejor). Nada que construir (el esceptico lo
  confirma). Caja del 21/10: Rico 430.300 -> -2.017; la racha (+250k,
  ~21/10 00:10) la pone en positivo; si fallara, solo los puntos de
  Olasagasti en ese partido.

- **19/10 07:15 (rafaga de la manana).** Ciclos: verdes (#2329 a #2338,
  la de las 07:15 incluida). Saldo -432.317 a las 07:19, 0 comprometido,
  nada comprado ni vendido en el reset del lunes. Sin cambios en el plan:
  premio de la J9 el mar 20/10 (12:00-17:00), racha el mie 21/10 00:10,
  plazo del aplazado de la J6 el mie 21/10 14:00. Control: mar 20/10 21:15.

- **18/10 21:15 (rafaga de la noche).** Ciclos: verdes (#2322 a #2329).
  Saldo -432.317, 0 comprometido, sin compras ni ventas. El chat del dueno
  encendio el informe de la manana (solo observa, no compra: no cuenta
  como motor). Manana lunes 19/10 la rotacion ya puede pujar; con el
  colchon en negativo no deberia: lo miro en la rafaga de las 21:15 del
  lunes (cualquier puja viva el lunes noche se resuelve el martes 07:00,
  antes del premio de la J9).

- **18/10 20:47 (laboratorio de rivales).** Sin reset desde la manana: el
  tablon solo trae la racha de Manzagool (+250k). Nosotros: -432.317, 0
  pujas, la cartera y la rotacion en NADA con la J9 jugandose. La
  publicacion de Rico se renovo (caduca en 40 h): seguira publicado en los
  resets del 19 y el 20, y la mejora lo vende desde el 20/10 00:00. J9: 37
  puntos con Jonny, Ibanez (Celta-Alaves) y Unai (lunes) por puntuar.

- **18/10 tarde: EL INFORME DE LA MAÑANA (encargo del dueno, tras Carvajal).**
  Laboratorio (1.981 jugador-dia de mercado, 22.520 de catalogo; informe en
  `scratchpad/lab_informe/INFORME.md`): lo que sube a 7 dias lo dice el
  cambio de precio de HOY (rho +0,63; las webs de mercado publican ese mismo
  numero, r 0,97); suman algo una noticia de VUELTA en FF (72 h) y valer menos
  de 1 M. Los puntos los dice la titularidad de FF por los puntos por partido
  (rho +0,45); resta la prensa de BAJA/DUDA. Recomendaciones tipo 'ficha si
  sale', jerarquia, racha: sin efecto medible o sin historia (peso 0, se
  apuntan). Formulas: sube = -1 + 4,5*cambio% + 2*VUELTA + 3*(<1 M);
  puntua = 0,5 + 0,85*titular*puntos por partido - 1*prensa. Construido
  y revisado (12 arreglados), ENCENDIDO en modo observador (dca3790d;
  ensayo #39129474545: 20 nuevos, Carvajal sube 35 / puntua 1,3). Fase 2,
  tras 1-2 semanas medido: sube en la cartera y la rotacion, puntua en la
  mejora, con su interruptor; ojo con las ventas de managers (Raba pide
  x1,5 su valor: la nota mira el valor). Tambien: la jornada en vivo elegia
  la J6 por el aplazado (27d86b0d).

- **18/10 14:15 (rafaga de la tarde).** Ciclos: verdes (#2315 a #2322).
  Saldo -432.317, 0 comprometido; la puja vieja por Manu Sanchez sale
  PERDIDA en el libro (Manzagool pago +19,3 %). Revisada la cuenta de E47:
  me la creo. Sin vender a nadie: racha +250.000 el mie 21/10 ~00:10 y el
  premio de la J9 el mar 20/10 entre 12:00 y 17:00 (minimo historico
  ~870.000) => positivo antes del plazo del mie 21/10 14:00. **Mi punto de
  control sigue:** mar 20/10 21:15. Si el premio no ha entrado para
  entonces, la racha sola deja -182.317 y aviso al dueno con a quien vender.

- **18/10 10:47 (laboratorio de rivales).** Rivales en el reset del 18/10:
  Manzagool gano a Manu Sanchez por 1.968.500 (+19,3 %; nuestra puja
  cancelada de 1.778.494 habria perdido) y queda en -1,83 M de caja;
  Luismi gano a Ilaix (3,46 M, sin rival) y queda en -7,62 M, y republico
  19 a x1,5. Pollo17 no opera desde el 15/10 y gana ~0,9 M al dia con 18 de
  19 subiendo: 105,07 M, 48,4 M por encima de nosotros (56,68 M). Puso a
  Giuliano Simeone (6,25 M) y German Valera (5,21 M) a su precio: la
  puerta los ve, pero no hay caja y pasan del tope de 3 M. Tres con caja
  negativa antes del aplazado del 21/10: Luismi, Manzagool y nosotros.
  Nuestras tacticas: la cartera, 0 pujas en 32 vueltas (colchon <= 0); la
  puerta, 2 ofertas en su vida y 0 aceptadas; la mejora solo si sube, 0
  pujas. **Encendido:** el motor viejo solo si sube (88bb2676; ensayo
  #39112934857, paso 0 con 52). **La caja del 21/10:** la vende la mejora
  (Rico es su 'sale', con Cardona dentro): desde el 20/10 00:00 acepta la
  oferta si llega al 90 % de su valor y, a menos de 20 h, cualquiera; el
  motor viejo renueva su publicacion. Si no se vendiera, empezariamos el
  aplazado en -432k y la J10 en -182k aun con la racha: vigilarlo el
  martes 08:22.

- **18/10 07:15 (rafaga de la manana).** Ciclos: verdes (#2306 a #2315,
  esperada la de las 07:15 tras el reset). Saldo **-432.317** a las 07:19,
  0 comprometido, plantilla 57,1 M. Nada vendido ni comprado en el reset
  del domingo. **CORRECCION DE FECHAS (mia, y arrastrada en varias
  entradas):** el 21/10 es MIERCOLES, no martes, y el 23/10 (J10) es
  VIERNES, no jueves. Los turnos programados estan bien de fecha (mie
  21/10 12:45 y vie 23/10 12:45); solo estaban mal los nombres de los dias.
  Quedan tres resets (lun 19, mar 20 y mie 21/10, 07:00) para llegar a
  positivo antes del plazo del miercoles 21/10 14:00 (aplazado de la J6).
  Dato del chat del dueno que lo refuerza: Luismi perdio los 64 puntos de
  la J6 aplazada por empezarla en negativo. Si el martes 20/10 a las 21:15
  no hay venta en marcha, aviso al dueno con a quien vender. Leccion:
  comprobar el dia de la semana con el calendario, no de memoria.

- **17/10 noche (laboratorio de rivales, tercera vuelta).** Rivales: nadie
  compro ni vendio desde la manana. Pollo17 en 7 dias: 4 compras al
  Computer, todas subiendo, prima media +16,7 % (Diomande 14,0 M a +23,5 %,
  ahora -1,9 M); 3 ventas al Computer el primer dia que no subian (-1,09 M
  realizado). Su patrimonio +2,98 M en 7 dias, casi todo revalorizacion; la
  distancia con nosotros paso de 44,7 a 47,5 M. Puntos con la J9 en vivo:
  Pepe 323, Pollo 320. Luismi (-4,16 M de caja) perdio los 64 puntos de la
  J6 aplazada por empezarla en negativo. Manzagool republico 11 a +20 %.
  Nuestras tacticas: la cartera y la puerta, 0 pujas (colchon <= 0 desde el
  reset del 17/10); la mejora solo si sube, 0 candidatos validos; un solo
  colchon paro 8 pujas del motor viejo (1.778.494, Manu Sanchez vetado).
  **Aplicado:** la rotacion ENCENDIDA (e144fd3e; NADA con la J9 jugandose);
  el motor viejo respeta los vetados de la orden en el orquestador y el
  executor (40a66164) y trae `BORDALAS_EL_MOTOR_VIEJO_SOLO_SI_SUBE` apagado
  (lo que pujo por jugadores que bajaban: -716k, n=3; subiendo: +1,18 M,
  n=4); el artefacto lleva la rotacion, la cartera y el plan del cierre.
  **Caja del 21/10 20:00 (aplazado, juega Olasagasti):** -432.317; vendiendo
  a Rico (oferta ~468k, desde el 20/10 07:00) queda entre -24k y +36k; la
  racha (+250k, ~21/10 00:10) y el premio de la J9 la cubririan. Revisar el
  martes por la manana.

- **17/10 21:15 (rafaga de la noche).** Ciclos: verdes (#2299 a #2306).
  Saldo -432.317, 0 comprometido. El chat del dueno encendio la rotacion
  (e144fd3e): es el septimo interruptor en ~20 h; lo dejo apuntado, el
  dueno decide. **Lo que miro por el plazo del martes 21/10 14:00:** la
  rotacion puede pujar el lunes 19/10 (se resuelve el 20/10 07:00) y vende
  al que sale cuando el otro ya llego; si esa venta va al Computer, el
  dinero entra el 21/10 hacia las 07:00, antes del plazo, pero justo. El
  lunes 21:15 compruebo que el saldo del peor caso del martes 07:00 llega
  a positivo; si no, aviso al dueno con a quien vender.

- **17/10 tarde (laboratorio de rivales, segunda vuelta): LA ROTACION.**
  Nuestra plantilla (12, 57,1 M; Yamal 25,4 M) pierde ~140k/dia (Roberto
  -80k, Exposito -40k, Luismi Cruz -40k, Unai -30k, Jonny -20k, Rico
  -10k); Pollo17 gana ~1 M/dia aguantando 19 que suben. Laboratorio
  (`scratchpad/lab_rotacion/INFORME.md`): cambiar al que lleva 2 dias sin
  subir por uno de su posicion que sube y puntua igual o mas da ~+30k/dia
  (un 20 % de la deriva), con datos finos (31 dias, 1 jornada puntuada, 6
  cambios) y Roberto no rotable a tolerancia 0. Construida apagada
  (`BORDALAS_LA_ROTACION`, c061b59a): 2 por ventana y por semana, caja de
  todos los motores, vende al que sale cuando el otro ya llego, rehace el
  once sin hueco, nada con la ronda jugandose, el aplazado del 21/10 es
  ronda propia. Revision adversarial: 22 hallazgos confirmados y
  arreglados; verja 216/216. El ensayo ahora corre tambien el parte y la
  rotacion (2a89c7db). Primer dia en que puede pujar: lun 19/10 (se
  resuelve el 20/10, J9 ya acabada). **La jornada en vivo** cuenta el once
  que empezo (59f53d5a): daba 12 puntos de J9 contando a Cardona; son 5.

- **17/10 14:15 (rafaga de la tarde).** Ciclos: verdes (#2292 a #2299).
  Saldo **-432.317**, comprometido 0 (la puja del motor viejo por Manu
  Sanchez ya no cuenta: la orden la retiro). **Decision del gestor sobre
  E45:** el aplazado de la J6 (mar 21/10 20:00) SE TRATA COMO PLAZO DE
  CAJA: positivo el martes a las 14:00. Creado el turno de ese dia (mar
  21/10 12:45, trig_01Jn67Ptjd3PqbSftxpM9jLK); el de la J10 sigue (jue
  23/10 12:45). Hay que recuperar ~0,45 M antes del martes: la cartera
  vende el primer dia que no sube; si el lunes 20/10 a las 21:15 sigue en
  rojo sin venta en marcha, aviso al dueno con a quien vender. **Lo debato
  (regla del dueno):** en ~14 h se han encendido seis interruptores (la
  puerta, la cartera, la mejora solo si sube, el 9.900 en la mejora, la
  puerta a +2 %, un solo colchon). Cada uno paso su verja y su ensayo,
  pero con seis a la vez, si algo sale mal no sabremos cual fue. Propongo
  parar de encender hasta ver dos o tres vueltas de reset (dom y lun
  07:00) y mirar que hizo cada uno.

- **17/10 11:00 (el laboratorio de rivales, primera vuelta).** Lo que han
  hecho: **Pollo17**, 0 compraventas y +1,97 M en dos dias (18 de sus 19
  jugadores suben): gana aguantando, no operando. **Luismi** ficho a Raba a
  +43,6 % (cohete barato) y va a -4,16 M de caja. **Manzagool** retiro sus
  ventas tras nuestras ofertas. **DiosMande** puso 12 a precio fijo; Cristian
  Romero y Veiga por debajo de valor, pero el tope de 3 M por viaje los deja
  fuera. Aplicado hoy: la puja en 9.900 en la mejora (ON, 6a4fd722), la
  puerta a +2 % con libro (ON), el marcador de la carrera (solo lectura),
  el parte vende (construido, OFF). **Dos correcciones:** (1) la puja de
  Cardona la hizo la mejora del once (corrida 38952525724, 16/10 21:10), no
  el dueno; corregido tambien en la orden. (2) el motor viejo (AUTOPILOT V3,
  ACQUISITION_BOARD, XI_UPGRADE) pujo 1.778.494 por Manu Sanchez (+7,8 %)
  con el colchon de la cartera en negativo: no mejora el once (3,5
  pts/partido, como Jonny y Chust) y dejaria la caja en -2,21 M antes del
  aplazado del 21/10. Vetado en `no_pujar`; la orden retira la puja en el
  siguiente ciclo, antes del reset del domingo. **Un solo colchon,
  ENCENDIDO** (`BORDALAS_UN_SOLO_COLCHON`, 50890424): con la cartera, lo
  que puja el motor viejo tiene que caber en el colchon de la ronda y
  cuenta entero. Verja 215/215, paso 0 con 50, ensayo #39021140487 verde.

- **17/10 09:00. CORRECCION DEL DUENO (regla basica, no olvidarla): en esta
  liga, UNA VEZ EMPEZADA LA JORNADA NO SE ADMITEN CAMBIOS DE ALINEACION.** El
  once de la jornada es el que hay al empezar su primer partido. Lo que Pepe
  guarde despues vale para la siguiente. Consecuencias: (1) no vender durante
  la jornada a nadie del once con el que empezo (aunque sea suplente para la
  siguiente); (2) fichar durante la jornada solo sirve para la siguiente.
  Hoy: Cardona (ganado en el reset; la puja era de la mejora del once, no
  del dueno: ver la entrada de las 11:00) es del once de la J10;
  Diego Rico juega la J9 y vuelve a `conservar` hasta el lunes.

- **17/10 07:15 (rafaga de la manana).** Ciclos: verdes (#2284 a #2291;
  #2292 en marcha). **Hecho:** el enlace del Rayo en FutbolFantasy
  (`FF_TEAM_SLUGS`: `rayo` -> `rayo-vallecano`; comprobado a mano: /rayo
  404, /rayo-vallecano 200). Sin interruptor, sin paso 0. Verja 211/211,
  ensayo #39005792044 verde en `arreglo/rayo-ff`, fusionado (d76c0f8c).
  **Pujas de la noche (reset 07:00):** Sergi Cardona GANADA (919.000);
  Alvaro Nunez (1.091.000) y Freeman (2.012.000) PERDIDAS. Saldo a las
  07:19: **-432.317**, 0 pujas vivas. La J10 (jue 23/10 21:00, plazo
  15:00) queda lejos y la cartera vende el primer dia que no sube, pero
  **sigue abierta la duda del aplazado de la J6 (21/10)** que el chat del
  dueno apunto como posible plazo de caja: hay que verificarlo antes del
  martes. No toco a Pablo Ramon en `no_pujar` (ya no esta en el mercado; lo
  dejo al chat del dueno, que lleva la cartera, para no ser dos manos).

- **17/10 03:00. EL LABORATORIO DE LA REVALORIZACION (wf_cf56a431-a90).**
  Panel diario comun (33.563 filas, 628 jugadores, 18/08-16/10; cuadra al
  euro) + 8 modelos + 2 verificadores + estratega. Lo CONFIRMADO:
  (1) el que no sube hoy sube manana el 2,4 % (551/23.301); el que sube,
  el 91,8 %. En la lista del Computer, el que no sube pierde -5,9 % a 7
  dias (n=369); las 34 compras nuestras asi, -4,44 M (Luismi Cruz, 14/10,
  la mejora, tras 16 dias bajando). (2) La salida de la cartera (primer
  dia que no sube) sobre nuestras 46 compras: +2,19 M. (3) Terminacion en
  9.900: 24 de 109 subastas al alza con rival frente a 6. (4) Desde
  mediados de septiembre la prima ya no paga: Pollo17 se queda en -1,2 %
  en octubre; la deuda alta no rinde (10 % = 25 % en el simulador).
  (5) Puntos: +0,43 pts/jornada por millon de XI (error 0,20, n=51); el
  XI de Pollo vale 78,3 M y el nuestro 56,3 M. (6) FutbolFantasy a 1 dia
  copia el cambio de hoy (97,4 %): no sirve como senal. (7) Luismi
  empezo la J6 aplazada en -2,87 M: 64 puntos y ~1,92 M perdidos.
  **Orden de construccion:** 1 la mejora solo si sube (hecho 17/10,
  97fe9bbd, ensayo y encendido); 2 el marcador semanal de la carrera; 3
  terminacion 9.900 tambien en la mejora; 4 vender por parte malo o <=0
  puntos; 5 prima de 1-3 M segun la subida (tras 2 semanas de marcador);
  6 la puerta a +2 % con registro de aceptaciones; 7 dos suplentes con
  premios (con datos de J10-J11). **No:** comprar nunca lo que no sube;
  primas >4 % en >=3 M; aflojar el colchon; plazos fijos de venta; usar FF
  como senal; vender a Yamal.

- **16/10 23:00 a 17/10 01:00. EL DUENO: «Pollo nos gana… ponlo en marcha
  ya… la misma estrategia que ellos… el laboratorio a probar y probar».**
  Diagnostico verificado (workflow de 4 analistas + verificador): de los
  +50,4 M de Pollo17 desde el 18/08, +46,1 M son revalorizacion de ~20
  jugadores comprados cuando suben y AGUANTADOS (viajes >7 dias: +18,68 M);
  los nuestros, revendidos antes de cada jornada: -2,84 M. Subastas con
  rival: la liga gana a +8,1 % de mediana; a +1 % perdimos las 20. Si un
  precio sube hoy, manana sube el 89,9 %. Premios iguales (9,7 vs 9,9 M).
  **Hecho esta noche:**
  1. `BORDALAS_LA_PUERTA_A_PRECIO_DE_MERCADO` ENCENDIDA (42ee30de): la ronda
     puja por los de los managers que piden su valor (+3 % max), suben y
     juegan. 00:07: ofertas a Manzagool por Freeman 2.012.000 y Alvaro
     Nunez 1.091.000 (200).
  2. `BORDALAS_LA_CARTERA` construida (23d652fd..64299fea), revisada por 3
     lupas + verificacion: aguanta lo que sube, vende el primer dia que no
     sube (>=97 % del valor), prima por tramo verificada (+12 % <1 M, +4 %
     1-3 M) solo a >=64 h, terminada en 9.000, max 20 jugadores, EL
     COLCHON (saldo - pujas vivas + 0,92 x lo de la ronda >= 0), el motor
     viejo no vende lo que aguanta, el cierre en rojo vende la cartera (y
     como ultimo recurso la alineada). Se enciende tras el ensayo.
  3. Laboratorio lanzado (wf_cf56a431-a90): panel diario comun + 8 modelos
     (cuando/a quien fichan Pollo y Luismi, que sube, noticias y calendario,
     puja optima, simulador con grid search, Luismi vs Pollo, puntos vs
     patrimonio) + 2 verificadores + estratega.
  **Pendiente (orden del plan verificado):** puja al alza en la mejora del
  once (+1 % + 4 %/punto, techo 10 %, solo si sube); el aplazado de la J6
  (21/10) se trata como plazo de caja: verificar en Biwenger.

- **16/10 22:50. EL DUENO: «¿No se puja por nadie?».** Cierto: 0 pujas
  desde el jueves 07:00. De jueves 05:00 a la J9 (21:00) no se compra a
  proposito; desde las 21:00 si, y a las 21:07 la ronda y la mejora no
  encontraron nada: en el mercado del Computer solo suben Ayoze (+10.000)
  y Sergi Cardona (+20.000), por debajo del minimo; los cambios del once
  que quedan (Bartra, Betis, rotacion 50 %, cae 25 dias; Mojica, en duda)
  no pasan. Pablo Ramon ya no esta en el mercado. **Lo que suben estan en
  las listas de los managers** y esa compra esta cerrada desde septiembre
  (pedian +14,5 % y se perdia). Hoy hay dos a precio de mercado y subiendo
  ~4 %/dia: **Alvaro Nunez** (Celta, DEF, 70 %, 5 pts/partido; Manzagool
  pide 1.080.000, vale 1.070.000) y **Freeman** (Villarreal, DEF, 70 %;
  pide 1.992.000, vale 2.000.000); las dos listas acaban el sabado ~07:12.
  Propuesto al dueno: pujar por Nunez desde la app (Pepe no puede).
  **Para el sabado:** abrir la compra a managers SOLO a precio de mercado
  (pide <= valor +3 %), que suba y que juegue; nace apagada, protocolo
  completo. La medicion de septiembre ya decia que ese caso (n=10) era el
  unico en verde (+2,6 %).

- **16/10 21:15 (rafaga de la noche; la J9 ya ha empezado).** Ciclos:
  verdes (#2281 a #2283, la de las 21:07 tambien). Saldo +486.683, 0
  pujas. Nada que tocar en viernes. **Para manana sabado (por orden):**
  (a) el enlace del Rayo en FutbolFantasy (`rayo` -> `rayo-vallecano`),
  con verja y ensayo; (b) quitar a Pablo Ramon de `no_pujar`; (c) el
  banquillo (punto 8), empezando por un defensa, si la caja lo permite.

- **16/10 20:15 (segunda mirada al cierre de la J9).** Ciclos: verdes
  (#2276 a #2282; la de las 20:07, #2282, verde). Saldo +486.683, 0 pujas:
  solvente. Once (artefacto de #2282): 3-4-3, 11 jugables, los 11 «ok».
  **Mala noticia:** Olasagasti baja a **0 %** de titular (a las 12:07, 90 %)
  y Luismi Cruz sube a 100 %: juegan los dos hoy a las 21:00 y con las
  alineaciones ya publicadas parece que Olasagasti sale suplente. No hay
  recambio (11 en plantilla), asi que no hay nada que hacer a mano: si no
  entra desde el banquillo, puntua 0. Diego Rico sigue en 30 %. **Leccion
  para la J10:** con 11 justos, dos dudas nos cuestan dos huecos; el
  banquillo (punto 8) es lo primero cuando haya caja.

- **16/10 14:15 (rafaga de la tarde, dia del cierre de la J9).** Ciclos:
  verdes (#2274 a #2276). Saldo +486.683 a las 14:10, 0 pujas: el plazo de
  las 15:00 se pasa en verde. Leida la entrada de las 13:20 del chat del
  dueno (el enlace del Rayo en FutbolFantasy da 404): de acuerdo en no
  tocarlo hoy; queda para el sabado, con verja y ensayo. Segunda mirada a
  las 20:15 programada.

- **16/10 13:20 (jornada en vivo, antes del primer partido).** J9: 0 puntos,
  los 11 por jugar (vie 21:00 Olasagasti y Luismi Cruz; ... lun 21:00 Unai
  Lopez). FutbolFantasy: 10 de 11 en su once probable sin lesion; Diego
  Rico fuera del once (30 %), sano. Gulacsi se perdio el Villarreal-Napoles
  por un atraco en su casa; el 15/10 volvio al grupo y «se apunta al
  Elche» (60 %). **Fallo encontrado (no se toca en viernes):**
  `FF_TEAM_SLUGS` en `src/intelligence/multisource_starter_v112.py` manda
  al Rayo a `/laliga/equipos/rayo`, que da 404; la buena es
  `rayo-vallecano`. La fuente FF no ve a Unai Lopez.

- **16/10 12:45 (TURNO DEL CIERRE DE LA J9).** Calendario sin cambios (J9
  hoy 21:00, J10 jue 23/10 21:00). (1) Solvencia: saldo **+486.683** a las
  12:10, 0 pujas vivas: verde para las 15:00 pase lo que pase. (2) Once
  (artefacto de #2274, 12:07): 3-4-3, 11 jugables, 0 huecos, los 11 «ok».
  Lo dudoso: **Diego Rico, 30 % de titular** (a las 08:25 era 72 %), y no
  hay defensa de recambio (3 DEF); Gulacsi y Luismi Cruz, 60 %. No hay nada
  que hacer hoy (a <40 h no se compra). (3) Ciclos: verdes (#2268 a #2274).
  (4) Pujas vivas: ninguna. (5) Segunda mirada programada a las 20:15
  (trig_01Sns1DGmVUC24bDT5frfUM4). (6) Creado el turno del cierre de la J10:
  jue 23/10 12:45 (trig_01FJsMrME8M86DHFfzB1i1XB). **Correccion mia:** a
  las 07:15 dije que los +250.000 eran «probablemente el premio de la J8»;
  la supervision de las 08:25 lo aclara: es la racha diaria (E43: la J8
  espera al Rayo-Athletic). **Para despues de la J9:** con 3 DEF, un solo
  defensa en duda nos deja en 10; el banquillo (punto 8) empieza por un
  defensa.

- **16/10 08:25 (supervision, dia de la J9).** Saldo **+486.683**, 0
  pujas vivas, 11 en plantilla: la J9 (hoy 21:00) empieza en positivo. Los
  +250.000 de medianoche NO son el premio de la J8 (seguimos con 323 puntos
  y 7 jornadas contadas): son la racha diaria, que paso de 4 a 0 a la vez
  (el modulo dice «cobrada: no», asi que la pago Biwenger sola). El cierre:
  EN_POSITIVO, 3-4-3 de 40,3 xP; Diego Rico sale SUPLENTE (72 %) y no hay
  otro defensa: con 3 DEF el 3-4-3 es la unica formacion posible. La
  mejora, la ronda y los chollos, nada (a <40 h no se compra). Orden del
  gestor: nada que limpiar. **Para despues de la J9 (no en viernes):**
  (a) el sabado, quitar a Pablo Ramon de `no_pujar`; (b) el peor caso de
  la mejora es muy estricto lejos de la jornada: Bartra (tasa 6,6) por
  Rico (+3,6 por partido, -2,77 M) no cabe en -1 M de deuda, y con 11 en
  plantilla no hay banquillo que vender. Pensar si a >=88 h la venta de un
  jugador con oferta del Computer en mano debe contar (se cobra al
  momento).

- **16/10 07:15 (rafaga de la manana, dia del cierre de la J9).** Ciclos:
  verdes (#2260 a #2268; #2269 en marcha). Saldo **+486.683** (04:52): entro
  +250.000 redondos entre las 00:10 y las 01:09 de hoy, sin compra ni venta
  y 0 pujas: lo mas probable es el premio de la J8 (sin confirmar en el
  libro). Plantilla 11, once de 11 en el marcador de la J9. Caja en verde
  para el plazo de las 15:00 pase lo que pase. Viernes: no se enciende
  nada. 12:45, el turno del cierre de la J9.

- **15/10 21:15 (rafaga de la noche).** Ciclos: verdes (#2253 a #2260).
  Saldo +236.683 a las 21:10, 0 pujas vivas: la caja de la J9 esta en
  verde incluso en el peor caso (no hay nada que pueda restar antes del
  plazo de manana 15:00). No hace falta avisar al dueno. Manana, viernes,
  no se enciende nada: 12:45 el turno del cierre de la J9.

- **15/10 14:15 (rafaga de la tarde).** Ciclos: verdes (#2246 a #2253).
  Confirmo la supervision de las 08:25: Lemar perdido, saldo +236.683, 0
  pujas vivas, la J9 (vie 16/10 21:00) empieza en positivo. **Correccion
  mia:** a las 07:15 escribi «se resuelve el jueves 07:00» y «manana se
  cierra»; hoy 15/10 ES jueves y la puja ya se habia resuelto (mire la
  bitacora del saldo de las 04:53, anterior al reset). Leccion: tras las
  07:00, mirar la vuelta de las 07:15 antes de dar una puja por viva.
  Jueves: no se enciende nada. Turno del cierre de la J9 manana 12:45.

- **15/10 08:25 (supervision tras el reset).** Lemar PERDIDO: otro pago
  4.107.000 frente a nuestros 3.767.000 (+340.000). Exposito se queda (su
  venta solo iba si entraba Lemar) y su publicacion se renovo a las 07:18
  (204). Saldo **+236.683**, 0 pujas vivas, 11 en plantilla: la J9 (vie
  16/10 21:00) empieza en positivo. El cierre: EN_POSITIVO, once 3-4-3 de
  40,3 xP (lo flojo, Diego Rico, 0,96 xP). La mejora y la ronda, nada:
  estamos a <40 h y no se compra; los cambios que habia (Pablo Ramon o Jon
  Martin por Rico) quitan 0,96 y 2,36 M que la caja no tiene. El miercoles
  la ronda no compro a nadie (20 en el mercado del Computer; ninguno subia
  lo bastante y jugaba); su bloque no guarda por que descarta a cada uno:
  hueco de telemetria. Orden del gestor: nada resuelto que limpiar; Pablo
  Ramon sigue en `no_pujar` hasta que acabe la J9.

- **15/10 07:15 (rafaga de la manana).** Ciclos: verdes (#2238 a #2245;
  #2246 en marcha). Saldo +236.683, puja viva por Lemar 3.767.000 (unica
  comprometida; se resuelve el jueves 07:00). El premio de la J8 sigue sin
  entrar. Turno del cierre de la J9 confirmado (16/10 12:45). No enciendo
  nada: manana se cierra jornada. Esta noche (21:15) repaso la caja de la
  J9 en el peor caso.

- **14/10 21:15 (rafaga de la noche).** Ciclos: verdes (#2230 a #2237).
  Saldo +236.683, puja viva por Lemar 3.767.000 (jueves 07:00). E40
  tranquiliza: en 7 de 7 noches pares hubo oferta del Computer por
  Exposito a las 07:15; la cuenta del jueves se sostiene. Nada mas.
  Manana (15/10) no hay reset que resolver; jueves 07:15 y 12:45, el
  cierre de la J9.

- **14/10 14:15 (rafaga de la tarde).** Ciclos: verdes (#2223 a #2230).
  Jutgla vendido (2.828.900), saldo **+236.683**, puja viva por Lemar
  **3.767.000** (se resuelve el jueves 16/10 07:00). Revisada la cuenta
  del chat del dueno: si entra Lemar, -3,53 M a las 07:00 hasta cobrar a
  Exposito (oferta del Computer ~4,68 M) => ~+1,1 M; hay 8 vueltas
  (07:18 a 14:07) antes del plazo de las 15:00. Si no entra, +236.683.
  Cuadra. **Un hueco que sigo:** el premio de la J8 no ha entrado y la
  J8 acabo el lunes; si el jueves a las 07:15 el Computer no ofrece por
  Exposito, el cierre debe vender a otro no titular antes de las 15:00:
  lo mira el turno del cierre de la J9 (12:45) con tiempo.

- **14/10 10:15. UBUNTU 26.04, PROBADO.** GitHub pasa `ubuntu-latest` a
  Ubuntu 26.04 desde el 19/10. Ensayo #38532152205 en `runs-on:
  ubuntu-26.04` (imagen 20260927.149.1, CPython 3.13.15): verja 208/208,
  ciclo en seco, panel, mejora y cierre sin un solo error de Python. No hace
  falta fijar `ubuntu-24.04`. La rama `prueba/ubuntu-26` sigue en GitHub
  (el proxy no deja borrar ramas); es inofensiva y el dueño puede borrarla.

- **14/10 09:30 (plan de caja de la J9). UN RIESGO GORDO, CORTADO.** La
  mejora habia pujado por Lemar (por Exposito: DA caja, +0,84 M) y, contando
  con ese dinero, por Pablo Ramon (por Diego Rico: QUITA 1,0 M). Las dos se
  resuelven a la vez el jueves 07:00: si se ganaba Pablo y se perdia Lemar,
  la J9 empezaba en -0,7 M (0 puntos) y ya sin tiempo (a <40 h no se
  compra). **Hecho:** Pablo Ramon a `no_pujar` (la orden retiro la puja,
  204) y la mejora pasa a contar la caja en el PEOR caso (dde2ec85): la
  venta cuyo relevo aun no es nuestro vale como mucho lo que cuesta el
  relevo; en una combinacion nueva, fuera del rojo, lo que da caja no
  cuenta y lo que la quita, entero; en rojo, solo cambios que dan caja.
  Y una puja retirada en la misma vuelta ya no cuenta como viva
  (be822d4b). **J9 ahora:** saldo 236.683; puja viva Lemar 3.767.000. Si
  entra: se cobra a Exposito (oferta del Computer ~4,68 M) => ~+1,1 M; si
  no, +236.683. Positiva en los dos casos.

- **14/10 08:40 (supervision de la manana). PEPE SOLO, TODO EL CICLO.**
  Reset: **Luismi Cruz GANADO** (3.252.000). 07:15, la mejora: cobra a
  Jutgla (2.828.900, por encima de su valor) y puja 3.767.000 por Lemar
  (Elche, MED, 6,4 pts/partido, 70 %) por Exposito (+0,3 pts por jornada con
  calendario, +0,58 sin el; caja +840.500). 08:07: puja 1.464.000 por Pablo
  Ramon (Racing, DEF, 70 %) por Diego Rico (+1,47 pts por jornada). Los dos
  sanos en FutbolFantasy. Caja de la J9 segun la mejora: +78.683 si entran
  los dos y se cobran Exposito y Diego Rico (ya publicados: oferta del
  Computer el jueves 07:00). El cierre (encendido, ventana abierta) dice
  FALTA porque cuenta solo lo cobrado y no hay banquillo: ruido esperado,
  no actua sobre el once. Orden: nada que limpiar salvo Jutgla de
  `conservar`. Saldo 236.683; el premio de la J8 sigue sin llegar.

- **14/10 07:15 (rafaga de la manana). LUISMI CRUZ ES NUESTRO**
  (3.252.000, sin pelea). Ciclos: verdes (#2214 a #2223); **el cierre ya
  esta encendido** (linea 248 del workflow; lo hizo el chat del dueno
  anoche) y las vueltas siguen verdes. **Saldo -2.592.217**, plantilla
  12; el once ya lleva a Cruz y no a Jutgla. Jutgla sigue publicado (a
  3,51 M); falta la oferta del Computer (E38: peor caso 2,51 M). El
  premio de la J8 aun no ha entrado. **Cuenta del jueves 15:00:** con
  Jutgla a 2,51 M, -82.217; con el premio, verde. Si no llega ninguno de
  los dos, el cierre debe vender a otro no titular. **Vigilo:** 14:15 y
  21:15 de hoy y 07:15 del 15/10; si el miercoles a las 21:15 sigue en
  rojo sin venta en marcha, aviso al dueno con el numero.

- **13/10 21:40. ENCENDIDO EL CIERRE DE LA JORNADA**
  (`BORDALAS_EL_CIERRE_DE_LA_JORNADA`, commit 900d6dda). Todas las vueltas
  del dia verdes con el calendario en la mejora. Verja 208/208; paso 0 con
  44; ensayo #38454935628 verde (fuera de su ventana a 71,5 h). Abre su
  ventana el miercoles 14/10 a las 05:00. **Caja de la J9:** saldo 659.783,
  puja viva por Luismi Cruz 3.252.000 (se resuelve el miercoles 07:00). Si
  entra: -2,59 M hasta cobrar a Jutgla (~2,4-2,6 M, el jueves 07:15) =>
  entre -0,16 M y -0,03 M; con el minimo en 0 desde las 64 h, la mejora en
  modo rojo buscara el cambio que lo cubra (caro por barato) antes del
  jueves 05:00. **El premio de la J8 aun no ha llegado** (saldo y puntos
  sin moverse): el Rayo-Athletic aplazado puede tener la J8 abierta; no se
  cuenta con el. La rutina del miercoles 06:40 vigila.

- **13/10 21:15 (rafaga de la noche). AVISO PARA LA J9.** Ciclos: verdes
  (#2207 a #2214). Puja viva por Luismi Cruz (3.252.000), saldo
  +659.783. **E38 corrige mi cuenta de las 14:15:** la oferta del
  Computer por Jutgla puede ser de 2,51 M (peor caso), no 2,9 M. Si entra
  Cruz: 659.783 - 3.252.000 + 2.510.000 = **-82.217 el jueves** salvo que
  el premio de la J8 entre antes. **BORDALAS_EL_CIERRE_DE_LA_JORNADA
  sigue APAGADO** (el plan del chat del dueno era encenderlo esta noche,
  antes de su ventana del miercoles 05:00). No lo enciendo yo: es su
  pieza y esta en marcha; dos manos a la vez en lo mismo es el error de
  Maffeo. **Si mañana a las 07:15 entro Cruz y el cierre sigue apagado,
  aviso al dueno con el numero** (y propongo encenderlo con su verja,
  paso 0, ensayo y canario, o vender otro no titular).

- **13/10 14:15 (rafaga de la tarde).** Ciclos: verdes (#2200 a #2207).
  **Canario del calendario en la mejora** (encendido 08:57, 3d2fe880):
  verdes las seis vueltas siguientes. Puja viva de Pepe (la mejora):
  Luismi Cruz por Jutgla, **comprometido 3.252.000**; saldo +659.783.
  **Cuenta de la J9 si entra Cruz** (14/10 07:00): -2,59 M hasta vender
  a Jutgla (precio ~2,9 M, publicado a 3,51 M): queda ~+0,3 M. **En verde
  pero justo**: si Jutgla se vende por debajo del 90 % o tarda, rojo el
  jueves. Lo miro el 14/10 a las 07:15 y el 15/10 a las 21:15. E37 (la
  puja fuerte): gana solo para fichajes del once y si cabe en la cuenta
  de la J9; sigue apagada, bien.

- **13/10 09:20. ENCENDIDO EL CALENDARIO EN LA MEJORA DEL ONCE**
  (`BORDALAS_EL_CALENDARIO_EN_LA_MEJORA`, commit 3d2fe880). Verja 208/208;
  paso 0 con 44 (el primero salio ROJO: las guardias de `correr` no
  fijaban la puja fuerte y con todos los interruptores puestos se caian;
  arreglado); ensayo #38358298552 verde. Primera vuelta en produccion
  (09:07, #38360682968): verde, la mejora con calendario de las J9, J10 y
  J11, 6 rivales duros, NADA_QUE_HACER con la caja de la J9 en -27.217 (la
  puja por Luismi Cruz y la venta de Jutgla dentro), 1 cambio frenado por
  el margen. Subida APAGADA la puja fuerte (`BORDALAS_LA_MEJORA_PUJA_FUERTE`:
  +4 % por punto por jornada, hasta +12 %, solo para lo que mejora el
  once). Siguiente: el cierre de la jornada (martes noche) y la puja fuerte
  (cuando el cierre lleve un dia en verde).

- **13/10 08:30 (supervision de la manana).** Reset: las tres pujas
  PERDIDAS — Ivan Romero y Moi Gomez para Pollo17, Gerard Martin para
  Luismi_Haz (otra vez el +1 % no basta contra un rival que quiere al
  jugador: 59 ganadas / 14 perdidas, nos ganan por 200.000 de mediana).
  **Pepe solo, a las 07:15:** la mejora del once puja 3.252.000 por Luismi
  Cruz (Deportivo, DEL, 5,0 pts/partido, 90 % titular, J9 en casa contra
  el Levante) por Jutgla: +2,25 pts por jornada, caja de la J9 -687.000
  (dentro del -1 M). Orden limpiada (fichar y vender_si_ficha vacios;
  Jutgla y Diego Rico a `conservar`). Caja de la J9 si entra Luismi Cruz y
  se cobra Jutgla: ~0 antes del premio de la J8. Ciclos de la noche y de
  la manana verdes. Pendiente de pensar: pujar mas que +1 % cuando la
  mejora del once gana mucho (un +2 pts por jornada vale ~60.000 EUR de
  premio por jornada que queda).

- **13/10 07:15 (rafaga de la manana). LAS TRES PUJAS PERDIDAS.** Ciclos:
  verdes (#2191 a #2200). Ivan Romero 3.777.000 contra 4.001.000 (+6 %),
  Gerard Martin 4.989.000 contra 5.771.000 (+16 %), Moi Gomez 1.101.000
  contra 1.107.000 (+0,5 %: por 6.000). Con Recio ayer, **cuatro de
  cuatro perdidas a precio +1 %** en jugadores que suben. Saldo
  +659.783, comprometido 0, plantilla 11, once 11: el riesgo de la J9
  desaparece por ahora. **Para el chat del dueno (dato, no orden):** con
  rivales en caja, el +1 % solo gana cuando nadie mas puja (E9: un 25-30 %
  de las subastas de los que suben); la ronda y la orden van a seguir
  perdiendo lo disputado. Medir el margen que hubiera ganado cada una
  (aqui: +6,4 %, +15,7 %, +0,6 %, +15 %) antes de subir la puja, y nunca
  subirla sin la cuenta de la J9 delante.

- **12/10 21:15 (rafaga de la noche).** Ciclos: verdes (#2184 a #2191),
  tambien tras las olas 1 y 2 del chat del dueno. Comprometido
  **9.867.000** (Ivan Romero, Gerard Martin, Moi Gomez; se resuelven el
  13/10 07:00), saldo +659.783, puja maxima que queda 4,77 M. E36 lo
  mide: **si entra Gerard Martin, sin el cierre no llegamos en verde a la
  J9 (-2,4 a -3,4 M)**. El plan del chat del dueno lo cubre (encender el
  cierre el martes por la noche, antes de su ventana del miercoles 05:00).
  **Lo que vigilo yo:** (1) 07:15 del 13/10: que entro y que la caja de
  la J9 con ventas previstas cuadra; (2) que el cierre se encienda el
  martes y su canario salga verde; (3) jueves 07:15: si la caja de la J9
  no esta en verde con lo ya vendido, aviso al dueno con el numero y a
  quien vender. Turno del cierre de la J9: 16/10 12:45 (creado).

- **12/10 20:45 (chat del dueno). OLA 2 Y ARREGLOS ANTES DEL RESET.**
  Subido (verja 208/208; ensayos #38275852357 y #38290081550 verdes, sin
  errores): (1) **apagados**, el calendario en la mejora
  (`BORDALAS_EL_CALENDARIO_EN_LA_MEJORA`: xP de las 3 proximas jornadas
  PRINCIPALES -el aplazado Levante-Athletic del 21/10 se juega con el once
  de la J6 y no cuenta-, encoge a los de pocos partidos hacia su tramo, y
  nunca vende a uno 0,5 pts mejor por calendario; en el ensayo frena 5
  cambios asi), el calendario en el once que se escribe
  (`BORDALAS_EL_CALENDARIO_EN_EL_ONCE`: NO se enciende antes de la J9,
  con el las protecciones de venta mirarian otro once) y el cierre de la
  jornada (`BORDALAS_EL_CIERRE_DE_LA_JORNADA`: paso propio DESPUES de la
  mejora; desde 64 h antes elige el mejor once y vende lo que sobra hasta
  >= 0; nunca a un titular del once escrito). (2) **Dentro de lo
  encendido**, lo que encontro la revision de todo junto (4 lentes y un
  esceptico por hallazgo): la caja de la mejora contaba dos veces las
  ventas ya cobradas de la orden (+3,1 M falsos el martes: habria dejado
  la J9 en rojo) y restaba pujas perdidas; la orden retira la puja de un
  fichaje lesionado/en duda/sancionado; el reroll del orquestador ya no
  rechaza ofertas que la ronda, los chollos, la mejora, la orden o el
  cierre van a cobrar; el ciclo apunta su run_id y los pasos de despues
  solo cuentan lo de su vuelta. **Ojo esta noche:** el catalogo de
  Biwenger esta en cache hasta el reset: si Ivan Romero se lesiona en el
  Levante-Sevilla, la retirada automatica no lo ve; hay un turno a las
  23:15 para meterlo en `no_pujar` a mano. **Plan:** martes tras el reset,
  encender el calendario en la mejora; martes noche, el cierre (antes de
  que abra su ventana el miercoles 05:00). Nada se enciende jueves ni
  viernes.

- **12/10 16:20 (chat del dueno). EL CALENDARIO, OLA 1 EN PRODUCCION.** El
  dueno: «fichas jugadores mejores cada dia y gente que va a subir; antes
  de la jornada se mira el calendario, se decide el mejor XI y se vende a
  los que falten para estar en positivo… mejor tener jugadores de los
  equipos de arriba». Medido (laboratorio, n=564 actuaciones J7-J8 con la
  tabla de ANTES de cada partido): casa x1,06 / fuera x0,94 (porteros 1,0),
  rival del top 6 x0,90, resto x1,04; la fuerza del propio equipo ya esta
  en sus puntos por partido (no se multiplica: solo como prior para los de
  pocos partidos). El calendario es un desempate (-15 %/+10 % en 3
  partidos), no una razon para vender a un crack. Nuestro once viene de
  equipos de media 11,2 en la tabla (1 del top 6, Yamal); el de Pollo de
  6,7 (7 del top 6), el de Luismi de 8,8. **Subido a main (verja 205/205),
  dentro de modulos ya encendidos:** (1) `el_calendario_de_puntos` (puro,
  aun sin uso); (2) `la_proxima_jornada`: rondas como las de Biwenger
  (aplazados y adelantados son ronda propia: el Levante-Athletic del 21/10
  cuenta), y ni la ronda ni los chollos cobran con jornada jugandose; la
  ronda ya no compra subidas minimas (n=7.286: +10.000 sigue subiendo el
  70 %, +20.000 el 90 %); (3) la orden con reloj (no puja a menos de 40 h
  salvo lo que paga la caja) y parte del relevo (no cobra al que sale si
  el que entra esta lesionado o en duda; en rojo a <24 h, si); (4) la
  ranura del ciclo ya no se tira: llevaba 10 dias gastando su unica
  escritura en intentar publicar a Yamal (protegido) — 36 FAILED en el
  log. **Orden:** Roberto y Gulacsi pasan de `proteger` a `conservar`
  (solo Yamal intocable): la mejora del once puede cambiarlos si suma.
  **Ola 2 en marcha (nace apagada):** el calendario dentro de la mejora
  del once (`BORDALAS_EL_CALENDARIO_EN_LA_MEJORA`) y de la alineacion
  (`BORDALAS_EL_CALENDARIO_EN_EL_ONCE`), y el cierre de la jornada
  (`BORDALAS_EL_CIERRE_DE_LA_JORNADA`: mejor XI con calendario y vender lo
  que sobre hasta >= 0). Regla: nada se enciende jueves ni viernes.

- **12/10 14:20 (chat del dueno). PEPE DEJA DE DORMIR: REVISION EN CADA
  VUELTA, CON DEUDA.** El dueno: «Pepe esta dormido… se compra, se ejecuta
  toda la deuda, se aguanta y se vende mas caro o se mejora el XI; revision
  cada ciclo, que para eso esta 24/7» y «no se trata de ejecutar mis ordenes
  al pie de la letra, se trata de que entiendas como funciona el juego».
  Tenia razon y la causa era nuestra: la reventa cabia en la caja libre
  (casi nunca hay), el fichaje del dia exigia caja >= 0 SIN deuda (tiro a
  Ivan Romero por 520.000 € y a Gerard por 3,8 M) y lo decidia una rutina
  fuera de Pepe una vez al dia. Pollo17 vale 100 M y Luismi 93 M; nosotros
  56 M: les sacamos 3 puntos con medio equipo de valor.
  **Encendidos dos interruptores** (verja 202/202, paso 0 con 40):
  `BORDALAS_LA_RONDA_DE_LA_MANANA` (ensayo #38245120244): en cada vuelta
  fuera de la zona de silencio puja precio +1 % por los del Computer que
  suben, sanos y que juegan; hasta 3 M por jugador y hasta maximumBid - 1 M
  (maximumBid ya descuenta las pujas vivas); no compra a menos de 40 h de la
  jornada; vende con beneficio, el primer dia que baja a -2 %, a 36 h a -7 %
  y a 20 h lo que haya. `BORDALAS_LA_MEJORA_DEL_ONCE` (ensayo #38247206025):
  paso propio tras el panel; en cada vuelta la combinacion de cambios (misma
  posicion, hasta 3) que mas puntos esperados suma, pudiendo cambiar caro
  por barato para pagar al bueno; caja de la jornada >= -1 M a 64 h o mas,
  >= 0 despues; en rojo desde 88 h, la combinacion que menos puntos pierde;
  el que sale solo se vende con el relevo dentro (desde el 90 %), nunca con
  la jornada jugandose; si la ronda compro a alguien que mejora el once, se
  lo queda el once. **Vuelta de las 14:07, real:** Ivan Romero 3.777.000,
  Gerard Martin 4.989.000 (orden) y Moi Gomez 1.101.000 (ronda), las tres
  con 200. Se resuelven el 13/10 a las 07:00. **Caja de la J9** (16/10
  21:00) si entra todo: ~-6,1 M antes de ventas; con Jutgla, Diego Rico y
  Moi vendidos y el premio de la J8 queda ~-3,5 M: la mejora del once lo
  ataca sola desde el 13/10 05:00 (88 h); la rutina del 14/10 06:40
  vigila. La rutina de las 08:22 ya no decide fichajes: supervisa lo que
  hizo Pepe y las noticias de sus pujas. Apagada la rutina obsoleta
  «Encender los chollos tras la J8».

- **12/10 14:15 (rafaga de la tarde, escrita a la vez que la de 14:20).** Ciclos: verdes (#2177 a #2184).
  **Canario de LA RONDA (BORDALAS_LA_RONDA_DE_LA_MANANA, encendida por el
  chat del dueno a las 13:55, b3326521): la #2184 de las 14:07, verde.**
  CORRIJO lo que escribi primero («aun sin pujas»): miraba el libro del
  saldo de las 14:09, escrito antes de pujar; la propia #2184 puso tres
  pujas (ver la entrada de las 14:20 encima: 9,87 M entre las tres).
  Se encendio tambien BORDALAS_LA_MEJORA_DEL_ONCE en el mismo rato: dos
  interruptores en una rafaga (la regla de la casa dice uno). **Mi objecion, para que conste
  (el dueno lo decidio y es su liga):** E14 midio que las compras
  automaticas para revender perdieron -1,24 M; lo que gana (E1/E9) es la
  rampa a precio +1 % sin pelear, y la ronda usa TODA la deuda con el
  plazo de la J9 el 16/10 a las 15:00. Riesgo: llegar al jueves con
  jugadores sin vender y la caja en rojo = cero en la J9 (lo que le paso
  a Luismi). **Vigilo desde la rafaga de las 07:15 del 13/10:** que la
  ronda compre solo lo que SUBE, lo que debe, y que el miercoles 15/10
  por la noche este todo vendido o la caja en verde sin ello. Si el
  jueves por la manana no cuadra, aviso al dueno y propongo apagarla.

- **12/10 07:15 (rafaga de la manana). RECIO PERDIDO.** Ciclos: verdes
  (#2168 a #2177). Nuestra puja de 1.142.000 (precio +1 %) perdio contra
  **1.313.000 (+16 %)**: la tercera vez que un rival paga bastante mas en
  un jugador que sube (E9: Pollo17 puja en el 75 % de los que suben).
  Diego Rico sigue (no se vende: la orden lo ata a Recio), la duda de sus
  puntos de la J8 ya no aplica. Saldo +659.783, comprometido 0, plantilla
  11, once 11. **Para el chat del dueno / el fichaje del dia:** el +1 %
  sirve contra empates, no contra un rival que quiere al jugador; con
  defensas titulares que suben, contar con perder salvo que nadie mas
  puje.

- **11/10 21:15 (rafaga de la noche).** Ciclos: verdes (#2161 a #2168).
  **Puja por Recio puesta: comprometido 1.142.000** (saldo +659.783); se
  resuelve el 12/10 a las 07:00. La rafaga de las 07:15 del 12/10 mira:
  si entro, que Diego Rico se venda (suelo 500.000) y el once siga con
  11; y la duda de los puntos de Rico en la J8 (ver 11/10 14:15).
  Laboratorio E34: pujar por puntos antes de la rampa casi nunca tiene
  candidato (1 por dia de partido); nada que meter.

- **11/10 14:15 (rafaga de la tarde).** Ciclos: verdes (#2154 a #2161).
  Saldo +659.783, comprometido 0. Revisada la orden del chat del dueno:
  `fichar` Recio (41419) a 1.142.000; `vender_si_ficha` Diego Rico (suelo
  500.000) con `si_esta` = Recio: Rico solo se vende con Recio dentro.
  Cuentas: si se gana el 12/10 a las 07:00, -0,48 M hasta vender a Rico
  (~0,5-0,55 M) y entra el premio de la J8: positivo de sobra antes del
  plazo de la J9 (16/10 15:00). **Duda que dejo apuntada, sin tocar
  nada:** la J8 sigue viva hasta el lunes por la noche (Levante de
  Olasagasti); Rico ya jugo el sabado. Si Biwenger cuenta los puntos de
  la jornada por la plantilla al CERRARLA y no al empezarla, vender a
  Rico el lunes por la manana podria restarnos sus puntos de la J8.
  Comprobar en el tablon/premio de la J8 si eso pasa (n=1), antes de
  convertirlo en regla. El fichaje del dia (rutina 08:22) lo lleva el
  chat del dueno; no lo duplico.

- **11/10 14:00 (chat del dueno). EL FICHAJE DEL DIA.** El dueno: «¿lo has
  decidido porque te dije de mirar? Esto lo quiero todos los dias». Cierto:
  las mejoras del once dependian de que el gestor mirase. Nuevo
  `scripts/el_fichaje_del_dia.py`: puntos esperados (pts/partido x
  titularidad) del mejor del Computer contra nuestro titular mas flojo de
  su puesto; ficha si gana >= 0,5/jornada y la caja queda >= 0 sin contar
  premios; puja precio +1 %; el que sale se vende con el relevo dentro y
  suelo del 90 %. Probado con el mercado de hoy: elige solo Recio por Diego
  Rico (+0,68/jornada). Rutina diaria 08:22 de Madrid (tras la vuelta de
  las 07:15): lo pasa con `--escribir`, verja, push, y una linea al dueno.
  Fase 2: meterlo en el ciclo de Pepe cuando lleve una semana acertando.

- **11/10 13:00 (chat del dueno). Intel del dueno: Djene NO** («siempre le
  dan un 2 y muchas veces roja»; los datos lo confirman: 2,38 pts/partido
  en 8). El defensa del lunes (premio de la J8): **Kike Salas** (2,81 M,
  3,8/partido, 90 %) o, mas barato, **Recio** (1,13 M, 3,1/partido, 70 %),
  por Diego Rico. Andres Martin (Racing, 3,15 M, 30 %, vuelve de lesion,
  +0,3 %/dia): no, salvo que juegue y puntue esta noche. El dueno: si no
  hay nadie para el XI o para aguantar y vender, no se ficha.

- **11/10 11:00 (chat del dueno). ERROR MIO: di a Diego Rico por puntuado
  (0) cuando jugaba esa tarde, y puse a Olasagasti en la Real Sociedad (es
  del Levante, juega el lunes).** El dueno: «estar siempre atento, sobre
  todo cuando la jornada se esta jugando; empaparse de todo». Arreglo:
  `scripts/la_jornada_en_vivo.py` (equipo de Biwenger -> partido del
  calendario -> JUGADO/JUGANDOSE/FALTA + puntos de la jornada) y una rutina
  en jornada (vie-lun 13:13, 17:13, 21:13) que lo pasa y mira noticias de
  los 11 (lesiones, rojas, suspensiones). Rayo-Athletic de la J8:
  suspendido por lanzamiento de objetos, se retoma en noviembre; cuenta con
  el once de la jornada (el dueno: los aplazados dan igual salvo lesion).

- **11/10 07:15 (rafaga de la manana). Reset sin nada.** Ciclos: verdes
  (#2145 a #2154). **Racha cobrada: saldo +659.783** (de 409.783),
  comprometido 0; plantilla 11, once 11. Defensas titulares en el
  mercado: Kike Salas 2,81 M (90 %), Djene 1,59 M (90 %), Jorge Salinas
  2,06 M (70 %), Recio 1,13 M (70 %). Aun no cabe ninguno: el punto 8
  espera al premio de la J8 (la jornada acaba el lunes 12/10).

- **10/10 21:15 (rafaga de la noche).** Ciclos: verdes (#2138 a #2145).
  Saldo +409.783, comprometido 0; sin compras ni ventas. Laboratorio E32
  (E2 fuera de muestra con el viernes de la J8: los de 5+ pts que no
  subian, 4 de 10 suben al dia siguiente; los de 4 o menos, 0 de 22):
  una medicion, nada que meter aun. Sigue esperando el premio de la J8
  para el punto 8.

- **10/10 14:15 (rafaga de la tarde).** Ciclos: verdes (#2131 a #2138);
  **canario del reloj falso superado** (la #2132 corrio sobre 61ff9b6e,
  verde). Saldo +409.783, comprometido 0; sin compras ni ventas. Mercado
  de hoy, defensas titulares: **Kike Salas (2,81 M, 90 %; 3,42 pts
  esperados en E16)**, Djene (1,60 M, 90 %), Jorge Salinas (2,07 M, 70 %);
  Puga 1,47 M pero 50 %. Ninguno cabe con 0,41 M: el punto 8 espera al
  premio de la J8 (cuando acabe la jornada). E31: Luismi empezo la J8 en
  rojo, su J8 deberia ser cero.

- **10/10 07:15 (rafaga de la manana). EL RELOJ FALSO.** Ciclos: verdes
  (#2122 a #2131). Reset sin nada; saldo +409.783 (el premio de la J8
  llega al acabar la jornada), plantilla 11, once 11. **Hecho:** las
  bombas con fecha (la verja roja del 09/10). Medido, no supuesto: (1)
  las 12 guardias que leen el reloj real pasan con el reloj congelado el
  10/10, 16/10, 01/11 y 31/12; (2) la verja ENTERA, con los interruptores
  de produccion, 200/200 el 16/10 19:00, 23/10 18:30, 31/10 23:30 y 31/12
  23:30 UTC; (3) el metodo pilla el fallo de verdad: el codigo de antes
  del arreglo (b11cb53c^) con el reloj el 09/10 15:30 de Madrid FALLA en
  `test_la_orden_del_gestor_v1`, y el 08/10 pasa. **Nueva herramienta:**
  `scripts/reloj_falso/usercustomize.py` (sin RELOJ_FALSO no hace nada;
  verja normal 200/200 con ella dentro). Uso en la regla de la casa de
  abajo. **Siguiente: el punto 8 (el banquillo) cuando entre el premio
  de la J8.**

- **09/10 21:15 (rafaga de la noche, J8 en juego).** Ciclos: verdes
  desde el arreglo (#2120 a #2122). Saldo +409.783, comprometido 0. Nada
  construido (dia de partido). **Para la rafaga de las 07:15 del 10/10
  (primer paso del dia):** 12 guardias leen el reloj real
  (`datetime.now()`/`date.today()`/`time.time()`): competitive_transactions_v121,
  dashboard_truth, el_carril_de_un_dia, el_escaparate,
  el_reloj_de_las_guardias, el_viaje_al_computer, empezar_a_anotar,
  la_plaza_y_el_cable, la_rendija, los_tres_arreglos,
  los_tres_denominadores, marcador. Mirar cual depende de una FECHA
  (como la de la orden de hoy) y no solo de medir tiempo; ojo, ya existe
  `test_el_reloj_de_las_guardias_v1` (doctrina 84: ver que vigila antes
  de construir). Despues, el punto 8 (banquillo) con el dinero de la J8.

- **09/10 20:15 (SEGUNDA MIRADA DEL CIERRE DE LA J8). EL ONCE ESTA BIEN.**
  La vuelta de las 20:07 (#2121) salio verde y dejo el once 3-4-3 con 11
  nombres, los 11 «ok» (Exposito y Roberto, 100 %; el mas dudoso, Diego
  Rico, 50 %). Nada que hacer a mano. **Lo que paso esta tarde:** cinco
  vueltas ROJAS seguidas (#2115 a #2119, 15:07 a 19:07): fallo la verja
  en `test_la_orden_del_gestor_v1` (la orden caducaba hoy a las 15:00 y
  una guardia usaba el reloj real, regla 23). Lo arreglo el chat del
  dueno a las 20:00 (b11cb53c) y lanzo la #2120 a mano: verdes desde
  ahi. Ningun cambio del once se perdio: la vuelta que lo congela es la
  de las 20:07. **Leccion para manana:** una guardia que mira el reloj
  real es una bomba de relojeria con fecha; buscar si queda alguna mas
  (doctrina 50, regla 23) antes del proximo plazo.

- **09/10 20:15 (chat del dueno). VERJA ROJA 5 VUELTAS (15:07-19:07).** La
  orden del gestor caducaba el 09/10 15:00 y dos guardias de
  test_la_orden_del_gestor_v1 usaban una orden de prueba con esa misma
  fecha contra el reloj REAL: desde las 15:00 la verja paraba el ciclo.
  Arreglo b11cb53c: orden renovada hasta el 30/11 (vacia; solo proteger
  Yamal/Roberto/Gulacsi y conservar; fuera la red de Jutgla) y las dos
  guardias con una orden sin caducidad cercana. Vuelta lanzada a mano
  #37970217104 verde. Once de la J8 en Biwenger: 3-4-3 con 11, igual que el
  recomendado. **Leccion: una fecha de caducidad en config no puede romper
  la verja; antes de cada caducidad, renovar o retirar.**

- **09/10 14:15 (rafaga de la tarde, dia de la J8).** Ciclos: verdes
  (#2111 a #2114). Saldo +409.783, comprometido 0: el plazo de las 15:00
  se cumple. **Creado el turno del cierre de la J9**
  (trig_01PnAXQSyaryBqT7Yku9DAP3, 16/10 12:45 de Madrid, a esta sesion;
  primer partido 16/10 21:00 segun el calendario del 28/09). Su prompt
  pide comprobar el calendario y crear el de la J10 (23/10). La segunda
  mirada de hoy sigue a las 20:15.

- **09/10 12:45 (TURNO DEL CIERRE DE LA J8).** (1) **Solvencia: +409.783,
  comprometido 0: el plazo de las 15:00 se cumple sin hacer nada.** (2)
  **Once:** 3-4-3 con 11 nombres, los 11 «ok» en el ciclo #2112 (Gulacsi;
  Jonny, Chust, Diego Rico; Exposito, Olasagasti, Unai, Pablo Ibanez;
  Yamal, Roberto, Jutgla). El mas dudoso, Diego Rico (50 % FF); sin
  banquillo no hay relevo (punto 8 del plan, desde el 10/10). (3) Ciclos:
  verdes (#2107 a #2112). (4) Pujas vivas: ninguna. (5) Segunda mirada
  programada a las 20:15 (trig_015VK1RmFydKisGdCTXi5wfo), tras la vuelta
  de las 20:07 que congela el once. E29: Luismi sigue en -2,74 M; si no
  sale del rojo antes de las 15:00, no puntua la J8.

- **09/10 07:15 (rafaga de la manana, DIA DE LA J8). Reset sin nada.**
  Ciclos: verdes (#2098 a #2107); hoy no hubo vuelta a las 06:22 (la red
  parece apagada). Saldo +409.783 (positivo: el plazo de las 15:00 se
  cumple), comprometido 0, plantilla 11, once 11. Mercado de hoy:
  ninguno de la lista de objetivos. A las 12:45, turno del cierre.

- **08/10 21:15 (rafaga de la noche).** Ciclos: verdes (#2091 a #2098).
  Pepe: sin compras, ventas ni pujas; saldo +409.783, comprometido 0.
  Laboratorio E27: el once de la jornada se congela en la vuelta de las
  20:07 del dia del partido (13/13). **Para manana:** el turno del cierre
  (12:45) programa su segunda mirada a las 20:15, justo despues de esa
  vuelta: es la buena para comprobar que salen 11 nombres.

- **08/10 14:15 (rafaga de la tarde).** Ciclos: verdes (#2084 a #2091).
  Pepe: sin compras, ventas ni pujas; saldo +409.783, comprometido 0.
  **Mercado del Computer de hoy contra la lista de objetivos (E25):
  ninguno** (ni Miguel Roman, ni Nacho Perez, Riedel, Galilea, Koski, ni
  Raphinha). E26: Miguel Roman y Koski estan lesionados; Raphinha se
  sostiene. Nada que hacer. Manana: turno del cierre de la J8 (12:45),
  y el saldo de Luismi.

- **08/10 09:40 (laboratorio E25, chat del dueno). Liderato fragil.** Contra
  Pollo17 vamos a la par (ganamos 5 de 7 jornadas, por regularidad); **el
  peligro es Luismi**: su once rinde 10-17 pts/jornada mas (la J6 la perdio
  entera, 64 pts, por saldo negativo). Somos peores en POR y DEF, mejores
  arriba; sin Yamal no hay once valido (3 DEL, 4 MED). **Lista de objetivos
  (solo si salen al mercado del Computer; un jugador libre no se puede
  fichar sin que lo publique):** Miguel Roman (MED, 6,3/j) por Unai Lopez;
  un DEF barato que juegue (Nacho Perez, Riedel, Galilea; o Koski) por
  Diego Rico/Jonny; **Raphinha (16,1/j): pujar y vender a Yamal SOLO si se
  gana la puja** (`si_esta`). Cada rafaga mira el mercado de la manana
  contra esta lista. **Luismi en rojo a 1 dia de la J8:** si no sale, otro
  cero; mirar su saldo en la rafaga de las 14:15 del 09/10.

- **08/10 09:10 (chat del dueno, con capturas de cron-job.org). ERROR MIO
  DE DIAGNOSTICO, CORREGIDO.** cron-job.org NO fallaba: son tres tareas a
  proposito (latido `7 0-3,8-23`, pre-reset 04:45 y 04:50, after-reset
  07:15; zona de silencio 04:45-07:00, `zona_de_silencio.py`). Lo que
  estaba mal era mio: (1) **los chollos pujaban solo a <65 min del reset y
  ninguna vuelta cae ahi: no habrian pujado nunca.** Ahora pujan en la
  vuelta de las 04:50 (<=129 min; la de las 04:45 llega a ~131-133) y solo
  si `permite_escribir` lo deja. (2) La «red de las 06:22»
  (trig_01AVXpLEPRYKWuEDiEquuCdR) lanzaba vueltas en plena zona de silencio:
  APAGADA. Las vueltas que lance a mano el 06, 07 y 08/10 no escribieron
  nada (no tenian que hacer). Leccion: leer la doctrina del reloj antes de
  llamar «fallo» a un hueco del latido.

- **08/10 07:15 (rafaga de la manana). Reset sin nada.** Ciclos: verdes
  (#2075 a #2084). Pepe: sin compras, ventas ni pujas (comprometido 0).
  Saldo +409.783: la red de Jutgla (desde hoy, solo con saldo negativo)
  no salta. Plantilla 11, once 11; los 11 «ok» en el ciclo #2084, Yamal
  ok y 90 %. Manana, turno del cierre de la J8 a las 12:45.

- **07/10 21:15 (rafaga de la noche).** Ciclos: verdes (#2067 a #2074;
  falta la de las 17:07, no disparada: una suelta). Pepe: sin compras,
  ventas ni pujas; saldo +409.783, comprometido 0; plantilla 11, once 11.
  **Estado de la plantilla (ciclo #2074): los 11 «ok», Yamal ok y 90 %
  titular.** Revisada la llave de Yamal (cab3a81, chat del dueno): la
  orden no la lleva, asi que Yamal sigue intocable; de acuerdo con la
  regla (baja >= 28 dias: vender el primer dia; su precio cae 1,5-2 % al
  dia segun E24). Nada construido ni encendido.

- **07/10 18:30 (chat del dueno). PLAN SI SE LESIONA YAMAL** (Pollo17: «en
  cuanto se lesione Lamine nos adelanta»; el dueno: «tu eres el CEO, el
  objetivo es ganar la liga»). Yamal: 88 pts en 7 (12,6/partido), ~1/4 de
  nuestros puntos; le sacamos 3 a Pollo (323-320). **Regla nueva (decision
  del CEO):** (1) baja corta (<4 semanas): Yamal se queda; ese dia se ficha
  el mejor DEL/MED barato TITULAR que quepa en caja propia (somos 11 justos:
  sin el, hueco = 0). (2) **baja de 4 semanas o mas: Yamal se vende al
  Computer el primer dia** (su precio cae cada dia sin puntuar) y se
  reinvierte en dos titulares. Mecanismo: la orden lleva
  `yamal_por_lesion: {motivo, baja_estimada_dias >= 28}`; sin esa llave
  sigue intocable (codigo y guardia `test_la_llave_de_yamal`). Hay que
  quitarlo tambien de `proteger`. (3) Tras la J8: 1-2 suplentes baratos que
  jueguen. **Cada rafaga mira el estado de Yamal** (catalogo y FF/prensa).

- **07/10 14:15 (rafaga de la tarde), A MEDIAS.** Pull bien; saldo
  +409.783 y comprometido 0 (libro del saldo, vuelta de las 14:09): sin
  pujas. **No pude mirar los ciclos ni la plantilla:** el filtro de
  permisos nego la lectura (sin motivo). Laboratorio E23: predicciones
  de la J8 apuntadas antes de jugarla (Luismi 58, Pepe 48, Pollo17 46).

- **07/10 07:15 (rafaga de la manana). Reset sin nada.** Ciclos: verdes
  (#2045 a #2061). Pepe: sin compras, ventas ni pujas (comprometido 0).
  Saldo +409.783, plantilla 11, once 11. **La rafaga de las 21:15 del
  06/10 NO SE HIZO:** el filtro de permisos bloqueo el pull y las
  lecturas de siempre (motivo «Account & Standing-Rule Changes»); hoy el
  pull vuelve a funcionar. La red de las 06:22 sigue encendida (disparo
  la #2060 a las 06:22, verde, sin escribir): sigue pendiente que el
  dueno la apague. Laboratorio E22 (ofertas del Computer: aceptar si
  pasan del +3 %): para despues de la J8, con la VENTA de E1.

- **06/10 14:15 (rafaga de la tarde).** Ciclos: verdes (#2037 a #2044).
  Pepe: sin compras, ventas ni pujas. Saldo +409.783, plantilla 11, once
  11. **CORRIJO la nota de las 07:15 (y la del chat del dueno de las
  06:30): cron-job.org NO falla.** E21: las 05h y 06h no tienen vuelta A
  PROPOSITO (config/disparos.json: latido a las :07 salvo 4-7; disparos
  puntuales 04:45, 04:50 y 07:15; zona de silencio del reset). El latido
  va 20/20 desde el 25/09. El dueno no tiene que mirar nada en
  cron-job.org. **La red de las 06:22 (trig_01AVXpLEPRYKWuEDiEquuCdR)
  sobra:** dispara cada dia una vuelta dentro de la franja de silencio
  que no escribe y gasta peticiones a Biwenger (riesgo de 429). Intente
  APAGARLA (no borrarla) y el filtro de permisos me lo nego: **queda
  para el dueno** (apagarla en sus rutinas, o pedirselo al chat que la
  creo, session_012cLZwP2316MR6pWJ7k5bZh).


- **06/10 07:15 (rafaga de la manana).** Ciclos: verdes (#2029 a
  #2037), salvo **#2028 (05/10 22:07) ROJA: la caida de GitHub Actions**
  que apunto el chat del dueno, no un fallo nuestro; las siguientes,
  verdes. Primera vuelta despues del reset con los chollos encendidos
  (#2037, 07:18): «Los chollos: NADA_QUE_HACER», orden NADA, revision de
  pujas fuera de ventana; la unica escritura, renovar un listado del
  escaparate. Saldo **+409.783** (racha cobrada), comprometido 0,
  plantilla 11, once 11. Aviso del log, sin importancia: seis listados
  del escaparate (Chust, Pablo Ibanez, Jonny, Unai, Jutgla, Diego Rico)
  caducan hoy y no se pueden renovar hasta manana: mejor asi antes de la
  J8. La red de las 06:22 (trig_01AVXpLEPRYKWuEDiEquuCdR) queda vigilada:
  la rafaga de las 07:15 del 07/10 mira si hubo vuelta entre las 06:00 y
  las 07:00.

- **06/10 06:30 (chat del dueno). cron-job.org SE SALTO OTRA VEZ las vueltas
  de las 05:07 y 06:07** (como el 28/09) y disparo dos casi seguidas a las
  04:45 y 04:50. Lance a mano el ciclo a las 06:21 (#37413306575, verde):
  racha ya cobrada en la de las 04:45 (saldo 409.783), revision de pujas
  TODAS_PASAN, orden NADA, **chollos NADA_QUE_HACER** (primera vuelta en la
  ventana: ningun chollo que quepa en caja propia). **Red nueva:** rutina
  trig_01AVXpLEPRYKWuEDiEquuCdR a las 06:22 de Madrid cada dia: si no hubo
  ciclo en los ultimos 30 min, lo lanza. El dueno deberia mirar la tarea de
  cron-job.org (solo el tiene acceso): parece fallar de 05:00 a 06:59.

- **05/10 23:40 (chat del dueno). ENCENDIDO BORDALAS_LOS_CHOLLOS** (el dueno:
  «¿por que no encendemos ya los chollos?»; la regla de las 72 h ya impide
  que una compra nos ponga en rojo antes de la J8). Paso 0 con 38, ensayo
  #37375467264 verde («Los chollos: NADA_QUE_HACER», fuera de la ventana),
  verja 200/200. GitHub Actions tuvo una caida grande esa noche (22:07 y el
  primer ensayo sin maquina). **La rafaga de las 07:15 del 06/10 mira:** el
  log de la vuelta de las 06:07 («Los chollos: ...»), si pujo y por quien,
  y data/trading/los_chollos.json. Con 159.783 EUR de saldo y la J8 a <72 h,
  solo puede pujar con caja propia.

- **05/10 21:15 (rafaga de la noche).** Ciclos: verdes (#2020 a #2027).
  Pepe: sin compras, ventas ni pujas. Saldo +159.783, plantilla 11, once
  11. Laboratorio E20 (la carrera): nuestro once es el segundo mejor
  (48 pts esperados contra 46 de Pollo17; Luismi 59), y **el hueco de
  Pepe es el banquillo**: confirma el punto 8 del plan (10/10). Nada que
  construir ni encender.

- **05/10 14:15 (rafaga de la tarde).** Ciclos: verdes (#2013 a #2020).
  Pepe: sin compras, ventas ni pujas. Saldo +159.783, plantilla 11, once
  11. **CORRIJO la nota del 04/10 21:15:** escribi que lo que los rivales
  en rojo vendan al Computer «saldra» en su mercado. E19 lo mide: no
  vuelve antes que cualquier libre (14 % en 7 dias). No hay atajo por
  ahi; su urgencia no es nuestra oportunidad. Queda en pie lo de Rafita
  (escaparate de Luismi) para el 10/10.

- **05/10 07:15 (rafaga de la manana). Reset sin nada.** Ciclos: verdes
  (#2005 a #2013). Pepe: sin compras, ventas ni pujas (comprometido 0).
  Saldo +159.783, plantilla 11, once 11. La racha (~+0,25 M) se espera
  el ~06/10: la rafaga de manana mira que entre.

- **04/10 21:15 (rafaga de la noche).** Ciclos: verdes (#1997 a #2004).
  Pepe: sin compras, ventas ni pujas. Saldo +159.783, plantilla 11, once
  11. Escaparate de Luismi y DiosMande (ciclo #2004): los mismos 19, a
  precio de mercado (-3 % a +7 %); Rafita sigue a 2,56 M. **E18 lo
  confirma con datos: los rivales en rojo no venden barato a otro
  manager (9/9 a precio o mas); con prisa malvenden al COMPUTER.** O sea:
  lo que hay que vigilar no es su escaparate sino el mercado del
  Computer del reset (lo que ellos le vendan saldra ahi), y eso ya lo
  miran los chollos (apagados hasta el 13/10) y la subasta. Las rafagas
  hasta el 09/10 bastan con mirar si Rafita sigue a la venta.

- **04/10 14:15 (rafaga de la tarde).** Ciclos: verdes (#1990 a #1997).
  Pepe: sin compras, ventas ni pujas. Saldo +159.783, plantilla 11, once
  11. Nuevo en main (chat del dueno): los chollos (BORDALAS_LOS_CHOLLOS,
  apagado, se encienden el 13/10) y E17. **Lo que venden los rivales en
  rojo (ciclo #1997):** Luismi_Haz pone a **Rafita** (DEF, 90 %, pide
  2,56 M = precio; el primero de la lista de E16, 3,86 pts esperados),
  Tenaglia (DEF 80 %, 4,78 M) y Areso (DEF 70 %, 2,36 M). DiosMande (13
  a la venta): Veiga (DEF 80 %, 3,98 M), Alfonso Herrero (POR 95 %,
  4,08 M), Cristian Romero (DEF 70 %, 6,24 M), Alvaro Garcia (DEL 80 %,
  4,04 M), Gordon, Fermin. Todos a precio de mercado (+-2 %), sin
  descuento: venden por necesidad pero aun no regalan. **Con 159.783 no
  llega ninguno con caja propia antes del 09/10 15:00: no se puja.** Si
  Rafita sigue a la venta el 10/10, es el defensa del punto 8. Las
  rafagas hasta el 09/10 siguen mirando si alguno baja de precio.

- **04/10 13:40 (chat del dueno). PATRIMONIO Y ESTRATEGIA (el dueno: «la
  estrategia es cosa tuya»).** Patrimonio (rival_intelligence, 04/10):
  Pollo17 98,7 M (20 jug., puja max 27,8 M), Luismi 92,0 M (saldo -17,0 M),
  Pepe 56,0 M (11 jug., puja max 14,1 M), lideres en puntos (323 contra 320).
  Diferencia: mercado (Pollo +64 M, Luismi +59 M, Pepe +22 M) y plantilla
  que sube (Pollo +0,62 M/dia, Pepe +0,05). **Estrategia:** no pelear a
  Pollo en su terreno (E9); recortar sin pelear: (1) chollos (se encienden
  el 13/10), (2) viajes a precio +1 % perdiendo sin pena lo que pelea
  Pollo, (3) tras la J8, la caja nueva a jugadores que sumen puntos Y
  suban (no solo puntos), (4) **Luismi en -17 M y DiosMande en -9,8 M a 5
  dias de la J8: venderan.** Cada rafaga hasta el 09/10 mira que ponen a
  la venta; si sale alguien bueno barato, al comparador, y solo con caja
  propia hasta el 09/10 15:00. Medir el patrimonio una vez por semana.

- **04/10 07:15 (rafaga de la manana). Reset sin nada.** Ciclos: verdes
  (#1982 a #1990). Pepe: sin compras, ventas ni pujas (comprometido 0).
  Saldo +159.783, plantilla 11, once 11. En el reset el escaparate
  renovo a Jonny, Unai Lopez, Jutgla y Diego Rico a la venta (+20 %
  sobre su precio): es lo de siempre desde septiembre (Yamal incluido),
  no algo nuevo. La regla de la casa sigue: si llega una oferta por un
  titular antes del 09/10, no se acepta sin relevo en el once.

- **03/10 21:15 (rafaga de la noche).** Ciclos: verdes (#1974 a #1981).
  Pepe: sin compras, ventas ni pujas. Saldo +159.783, plantilla 11, once
  11. Laboratorio E16 afina el punto 8 del plan (el defensa entra de
  titular por Diego Rico, elegido por puntos esperados): plan
  actualizado. Nada construido ni encendido.

- **03/10 14:15 (rafaga de la tarde).** Ciclos: verdes (#1967 a #1974).
  Pepe: sin compras, ventas ni pujas. Saldo +159.783, plantilla 11, once
  11. Laboratorio E15 (el bot pequeno contra Pepe en 91 vueltas):
  «prometedor, no listo»; nada que meter. Nada construido ni encendido.

- **03/10 07:15 (rafaga de la manana). Reset de las 07:00 sin nada.**
  Ciclos: verdes (#1959 a #1967; la #1967 es la de despues del reset).
  Pepe: sin compras, ventas ni pujas (comprometido 0). Saldo +159.783,
  plantilla 11, once 11. Nada nuevo del laboratorio desde el E14. No se
  construye ni se enciende nada: el plan dice banquillo desde el 10/10 y
  el saldo no da para mas antes del plazo del 09/10 15:00.

- **02/10 21:15 (rafaga de la noche).** Ciclos: verdes (#1952 a #1958).
  Pepe: sin compras, ventas ni pujas; saldo +159.783, comprometido 0;
  plantilla 11, once 11. **Laboratorio E14 («Listo para el plan»):** las
  tres vias automaticas de Pepe, 21 compras, -1,24 M (casi todas antes de
  encender la rampa el 29/09); y lo que mas costo, cuatro fichajes de
  2,5 M+ revendidos ANTES de jugar con nosotros (Cabrera, Dmitrovic,
  Ceballos, Blanco): **-3,3 M y cero puntos**. Los caros bajan un 5-8 %
  cada 11 dias y se pagan +4-14 %: comprar caro y revender en dias es
  perder seguro. **Hecho:** la regla pasa a «Reglas de la casa» (abajo).
  Es una regla del gestor y de la orden, no codigo: Pepe no ficha caro
  para el once por su cuenta. La rafaga de las 07:15 del 03/10 mira el
  reset (sin pujas vivas: no deberia cambiar nada).

- **02/10 14:15 (rafaga de la tarde).** Ciclos: verdes (#1944 a #1951).
  Confirmado en el libro del saldo: **+159.783**, comprometido 0. Plantilla
  11, once 3-4-3 con 11 (Gulacsi de portero). Sin compras ni ventas desde
  las 07:18. Orden limpia por el chat del dueno (c7aac47); no la toco.
  **E12 (suplente, «Listo para el plan»): lo debato y lo APLAZO al 10/10.**
  En el mercado de hoy, el defensa que juega de verdad (Jorge Salinas,
  2,25 M, 70 %) nos devuelve al rojo antes del plazo del 09/10 15:00; los
  que caben son de 0,2-0,3 M y 40 % (Berrocal, Boselli), y aun asi Boselli
  (320.000) deja -160.000 hasta la racha del ~06/10. Cuenta: un defensa
  suplente solo cubre a los 3 defensas (3 de 11 de las bajas sabidas,
  ~0,1-0,25 por jornada) y uno del 40 % juega la mitad: **~0,1 pts en la
  J8, contra arriesgar la regla de la solvencia.** No compensa. Tras la
  J8 (pago de la jornada + racha) va lo primero: un defensa de 1-3 M que
  juegue, despues un medio. Lo apunto en el plan.

- **02/10 08:35 (chat del dueno, comprobacion del agujero). EXAMEN
  APROBADO: FUERA DEL ROJO SIN VENDER A NINGUN TOP.** Libro del saldo de
  las 08:09: **+159.783**. Camino: Roberto (9,65 M) -> ventas de
  Cabrera, Zubeldia, Duran, Guevara y Blanco -> Diego Rico -> racha ->
  Gulacsi por Dmitrovic (+1,64 M y mas puntos) -> viaje de Moi (+65.200).
  Orden limpia: `fichar` vacio, viajes vacios; Gulacsi a `proteger`;
  queda solo la red de Jutgla (08/10, si_saldo_negativo: no salta en
  verde). Rutina diaria del agujero apagada. Margen fino: la racha del
  ~06/10 (+0,25 M) lo agranda; cualquier puja nueva antes del 09/10 15:00
  tiene que dejar el saldo en verde a esa hora.

- **02/10 07:15 (rafaga de la manana). Reset de las 07:00: GULACSI ES
  NUESTRO** (2.437.000). Ciclos: verdes (#1936 a #1944). La orden hizo
  lo suyo en la vuelta de las 07:18 (tablon): **vendio a Dmitrovic al
  Computer por 4.076.200** (suelo 3,75 M; relevo Gulacsi dentro) **y a
  Moi Gomez por 955.200** (pagado 890.000: viaje corto +65.200). Saldo
  antes de las ventas -4.871.617; despues, por cuenta, **~+159.783: fuera
  del rojo antes del 09/10**. El once 3-4-3 ya lleva a Gulacsi de
  portero, 11 nombres; plantilla 11 (sin banquillo). Pendiente de
  confirmar en el libro del saldo de la vuelta de las 08:07 (la foto del
  marcador de las 07:18 es de antes de las ventas). **La rafaga de las
  14:15 mira:** saldo positivo en la bitacora del saldo, plantilla 11 y
  once 11; y que la orden quite a Dmitrovic y a Moi de sus listas (si
  no, nada que vender: no hace dano, pero se limpia).

- **01/10 21:15 (rafaga de la noche).** Ciclos: verdes (#1929 a #1935).
  Pepe: sin compras, ventas ni pujas nuevas; sigue solo la de Gulacsi
  (2.437.000, comprometido igual), que se resuelve el 02/10 a las 07:00.
  Saldo -2.434.617, plantilla 12, once 3-4-3 con 11. Laboratorio: E10
  (chollos de la manana, raros) y E11 (adivinar que subasta no pelea
  Pollo17, descartado): nada listo para el plan. Rutina del cierre J8
  comprobada (09/10 12:45). **La rafaga de las 07:15 del 02/10 mira:**
  si entro Gulacsi, que Dmitrovic se venda (suelo 3,75 M) y el once siga
  con 11; si no, que Dmitrovic siga en el once.

- **01/10 14:15 (rafaga de la tarde).** Ciclos: verdes (#1922 a #1928).
  Pepe: sin compras ni ventas desde el reset. Puja viva de la orden por
  Gulacsi (2.437.000) para cambiarlo por Dmitrovic (+puntos, +1,5 M de
  caja si se vende Dmitrovic); se resuelve el 02/10 07:00. Saldo
  -2.434.617. Plantilla 12, once con 11. E9 del laboratorio confirma la
  leccion del reset: Pollo17 puja en el 75 % de los que suben; pujar a
  precio +1 % y no pelear. Nada que construir ni encender por mi parte.

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
