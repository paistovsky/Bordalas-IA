# EL PUESTO DE MANDO

**Si eres el Claude que acaba de despertarse: lee solo esto.**

Actualizado: 28/09/2026, 21:35 de Madrid (rafaga de las 21:15: la rampa, ENCENDIDA).

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
- **Mision secundaria:** un panel para ver en tiempo real que pasa. Hoy
  existe https://bordalas-ia-dashboard.bordalas.workers.dev/ (usuario y
  contrasena: los tiene el dueno; NO se escriben en el repo, que es publico).
- **Informe:** uno pequeno al dia, para "dummies".
- Si hace falta un permiso o una herramienta, se le pide.

## Donde estamos

    clasificacion   1o, a 3 puntos de Pollo17, 31 jornadas por delante
    saldo           +1.569.876 (28/09; 1.363.592 apartados en la puja por Zubeldia)
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
4. **Aislar la verja de la red.** La regla «ninguna guardia sale a internet»
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
