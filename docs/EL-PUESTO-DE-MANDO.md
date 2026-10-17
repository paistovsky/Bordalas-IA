# EL PUESTO DE MANDO

**Si eres el Claude que acaba de despertarse: lee solo esto.**

Actualizado: 17/10/2026, 07:45 de Madrid (rafaga de las 07:15).

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

- **17/10 09:00. CORRECCION DEL DUENO (regla basica, no olvidarla): en esta
  liga, UNA VEZ EMPEZADA LA JORNADA NO SE ADMITEN CAMBIOS DE ALINEACION.** El
  once de la jornada es el que hay al empezar su primer partido. Lo que Pepe
  guarde despues vale para la siguiente. Consecuencias: (1) no vender durante
  la jornada a nadie del once con el que empezo (aunque sea suplente para la
  siguiente); (2) fichar durante la jornada solo sirve para la siguiente.
  Hoy: Cardona (ganado en el reset, puja del dueno) es del once de la J10;
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
