# EL LABORATORIO

**Si eres el Claude del laboratorio: lee esto y luego docs/EL-PUESTO-DE-MANDO.md.**

Creado: 27/09/2026, a peticion del dueno: «que en tu laboratorio no pares de
crear y mirar cual es la mejor manera de crear un bot autosuficiente para
ganar Biwenger».

## Para que existe

Los turnos del gestor arreglan a Pepe pieza a pieza y lo mantienen vivo. El
laboratorio hace otra cosa: **busca la mejor forma de ganar**, sin la atadura
del codigo que ya hay. Puede proponer rehacer una parte entera de Pepe o el
bot completo, siempre que lo DEMUESTRE con datos.

## Las reglas del laboratorio

1. **El laboratorio no toca produccion.** Trabaja en ramas `lab/<tema>` y en
   la carpeta `lab/`. Nunca fusiona a main codigo de Pepe: cuando algo gana,
   lo apunta en «Listo para el plan» y lo hace un turno del gestor (verja,
   ensayo, un interruptor cada vez).
2. **Una idea no vale nada hasta que se mide.** Cada experimento dice: la
   hipotesis, los datos (con su n), el resultado contra lo que Pepe hace hoy,
   y si se aguanta o se descarta. Un experimento que sale mal tambien se
   apunta: ahorra repetirlo.
3. **Los datos que hay:** los libros de `data/` en git (historial de precios,
   tablon de la liga con todas las compraventas de los 8 managers, pujas,
   saldo, valoraciones diarias, foto del 18/09) y los artefactos de cada ciclo
   en GitHub Actions (la red ya deja bajarlos). Para probar un Pepe distinto
   con datos de hoy sin escribir nada: el ensayo (`bordalas-ensayo.yml`).
4. **Biwenger no se toca desde aqui** salvo con el ensayo, y con cabeza: cada
   ensayo gasta las mismas peticiones que una vuelta real.
5. **El objetivo es uno: ganar la liga.** El dinero solo cuenta si acaba en
   puntos. Nada de pantallas que solo miran.

## La agenda (por orden; el laboratorio la reordena si los datos mandan)

1. **Como ganan los que ganan.** Pollo17 y Luismi_Haz: +13 M y +8,5 M en
   compraventa con el Computer; nosotros ~0. Reconstruir su regla de compra y
   de venta desde el tablon (que compran, a que precio respecto al mercado,
   cuanto aguantan, cuando venden) y ver si una regla simple la imita.
2. **Que predice que un jugador suba de precio.** Con `price_history.json`:
   titularidad, puntos recientes, tendencia de dias anteriores, calendario...
   Un modelo sencillo y honesto (con validacion fuera de muestra) antes que
   uno bonito.
3. **El once optimo.** Cuantos puntos ha dejado Pepe en el banquillo por
   jornada (cuando el cuaderno este arreglado, con datos fiables).
4. **Aceptar o no ofertas.** Cuando conviene vender a un manager o al Computer.
5. **La arquitectura de un bot nuevo.** Pepe tiene 33 interruptores, 190
   guardias y modulos que solo miran. Como seria un bot pequeno que hiciera lo
   que gana y nada mas. Prototipo en `lab/`.

6. **(PRIORIDAD, pedido del dueno el 29/09) Las noticias que se adelantan.**
   Pepe lee la alineacion probable de FutbolFantasy y prensa nacional
   (Marca, MD, Relevo), pero NO partes de entrenamiento, prensa local ni
   foros. Caso del 29/09: Aspas (Celta) roto desde ~13/09, vuelve el
   11/10 contra el Elche; Pablo Duran (Celta, «Rotacion», 30 %) paso de
   0,36 a 1,33 M del 19/09 al 29/09 por los minutos que dejaba Aspas, y
   Pepe no tenia la lesion en ningun sitio. Pregunta: ¿las noticias de
   entrenamiento (FutbolFantasy /laliga/noticias, una o dos por equipo y
   dia) y la prensa local de cada club anuncian cambios de titularidad y
   bajas ANTES de que se muevan el % de titular y el precio? ¿Cuantos
   dias? Medir con el historico de precios y un archivo diario de esas
   noticias; si se adelantan, entra en el ojeador de prensa
   (src/intelligence/scout/press.py) con su guardia.

## Experimentos

(el laboratorio los apunta aqui, el mas reciente arriba: fecha, hipotesis,
datos y n, resultado, veredicto)

### E63 · 26/10/2026 11:16 de Madrid · El precio va una semana por detras de los puntos

**Hipotesis:** Biwenger no sube el precio de un jugador de golpe tras una
buena jornada: lo va subiendo dias despues. Si es asi, el martes aun se
puede comprar barato al que puntuo mucho el fin de semana.
**Datos:** puntos de cada jugador en la J8 y la J9 (fotos de
`puntos_por_jornada`, 264 jugadores por jornada que jugaron; fuera
Athletic, Rayo y Levante) y su precio dia a dia.
**Codigo:** `lab/precio/tras_la_jornada.py`.

    Spearman entre los puntos de la jornada y el cambio de precio de cada dia
                     vie    sab    dom    lun  | mar    mie    jue    vie
    J8 (09-12/10)   +0,13  +0,33  +0,33  +0,68 | +0,70  +0,70  +0,65  +0,59
    J9 (16-19/10)   +0,17  +0,28  +0,32  +0,57 | +0,63  +0,60  +0,58  +0,58
                                                 (ya sin partidos)

    comprar al precio del martes y mirar el lunes siguiente (6 dias):
                                  J8              J9
    subio el martes, 8+ pts     +7,1 % (n=30)   +9,9 % (n=33)
    subio el martes, <8 pts     +2,9 % (n=61)   +4,5 % (n=69)
    no subio                    -4,8 %          -4,7 %

**Lo que se aprende:**
- **El precio va una semana por detras de los puntos:** con la jornada ya
  terminada, los cambios de precio del martes al viernes siguen casi tan
  ligados a los puntos como el del lunes (+0,58 a +0,70).
- **Los puntos añaden algo a «subio ayer»** (E1/E44/E51): entre los que
  suben el martes, los que hicieron 8 o mas puntos suben el doble en la
  semana (+7 a +10 % contra +3 a +4,5 %). Las dos jornadas dicen lo mismo.
- Sirve doble: suben mas Y son los que puntuan (para el once).

**Limites:** dos jornadas; 30-33 casos en el grupo bueno; son jugadores que
suben, asi que la subasta tiene pelea (E41/E49: +10 a +30 % de prima): para
revender solo compensa si se gana con prima corta; para el once, siempre.

**Veredicto: GANA** (pasa a «Listo para el plan»): ordenar a los que suben
por los puntos de la ultima jornada.

### E62 · 25/10/2026 17:15 de Madrid · Vender a un manager (agenda, punto 4): un mercado que ya no existe

**Hipotesis:** venderle a un manager paga mas que venderle al Computer,
y merece la pena buscarlo (la puerta a precio de mercado se apago el 20/10
con 2 ofertas y 0 aceptadas).
**Datos:** todas las ventas entre managers del tablon (10, del 10/08 al
18/09; 6 con precio del dia) y el precio del jugador 7 y 14 dias despues.
**Codigo:** `lab/ofertas/entre_managers.py`.

**Lo que se aprende:**
- **Entre managers casi no se vende:** 10 ventas en toda la temporada y
  **ninguna desde el 18/09** (cinco semanas). Pepe hizo cuatro, todas en
  agosto y septiembre.
- Cuando se vende, es por encima del precio (6 de 6, mediana +6,5 %), pero
  al vendedor le salio bien la mitad (3 de 6: el jugador subio mas que la
  prima en una semana).
- Con n = 6 no hay regla que sacar; lo que si se ve es que no hay
  comprador al otro lado: los rivales compran al Computer (E41/E57).

**Veredicto: NO GANA.** Confirma que apagar la puerta fue lo correcto:
vender se hace al Computer (oferta viva cada 48 h, E42), y la agenda puede
cerrar el punto 4 hasta que vuelva a haber ventas entre managers.

### E61 · 25/10/2026 11:15 de Madrid · Como elige el Computer a sus 20: cuanto se espera a un objetivo

**El caso:** el gestor ha puesto «la lista de objetivos» (el mejor equipo
posible) y la mira cada mañana en el mercado del Computer; Nino o Zabiri
por Roberto, «solo el dia que el Computer los saca». ¿Cuanto se espera?
**Datos:** `libro_del_escaparate.jsonl`, 39 dias de lista (20 jugadores al
dia, 780 apariciones, 310 jugadores distintos), contra los 424 libres de
la foto del ciclo de hoy.
**Codigo:** `lab/mercado/como_elige_el_computer.py`.

**Lo que se aprende:**
- **Cada jugador del Computer esta dos dias en la lista:** de 470 pares de
  apariciones seguidas del mismo jugador, 343 son de un dia al siguiente
  (cuadra con las 48 h de E42). Salen ~11 nuevos cada dia.
- **Es casi al azar entre los libres, sin mirar el precio:** 4,0-4,6 % de
  los dias en todos los tramos, algo menos entre 3 y 6 M (2,6 %). Un
  jugador concreto **entra en la lista ~2,6 % de los dias: uno de cada
  ~40 dias**.
- **La cuenta para la lista de objetivos:** que salga al menos uno en una
  semana:

      nombres en la lista     1      3      5      10      15
      sale alguno en 7 dias  17 %   42 %   60 %   84 %    94 %

  Con 2-3 nombres (Nino, Zabiri) lo normal es no ver ninguno en semanas;
  con 10, casi cada semana sale uno. Y entonces hay que ganar la subasta
  (E41/E57).

**Limites:** «libres» es la foto de hoy (cambia); el escaparate empieza el
17/09; no se ve si el Computer evita a los que acaban de salir.

**Veredicto: AVISO para la lista de objetivos** (pasa a «Listo para el
plan»): una lista de 2-3 nombres apenas sale; para que sirva cada semana
hacen falta ~10 por puesto que se quiera cubrir, ordenados.

### E60 · 24/10/2026 17:15 de Madrid · ¿Esta viejo el calendario de Pepe? No: el que estaba viejo era otro

**El caso:** el gestor (24/10 14:15) se equivoco con la fecha de la J11
(dijo dom 01/11; es vie 30/10) y culpo a `data/calendar/laliga_calendar.json`
(«dice 01/11, es del 28/09»).
**Datos:** el `laliga_calendar.json` del artefacto del ciclo de las 17:09
de hoy (el que usa Pepe en produccion) contra los «roundStarted» reales del
tablon (J1-J10), y `data/calendar/calendar_changes.jsonl` (380 partidos
dados de alta, 90 cambios de hora).
**Codigo:** `lab/infra/calendario_contra_biwenger.py`.

**Lo que se aprende:**
- **El calendario de produccion acierta las diez:** el primer partido de
  cada jornada del fichero coincide al minuto con el inicio de Biwenger
  (J1-J10, 0,0 h de diferencia, incluida la J6 adelantada al 03/09). El
  fichero se baja en cada vuelta (hoy a las 17:09) y da la **J11 el vie
  30/10 21:00**.
- **El cambio de la J11 se conocia desde el 03/10:** ese dia el fichero
  movio los diez partidos del 01/11 a sus horas (el primero, el
  Villarreal-Espanyol del 30/10). Los 90 cambios de hora llegaron como poco 12
  dias antes del partido (mediana 29).
- **El error no fue del fichero de Pepe, sino de quien lo leyo:** la
  copia vieja estaba fuera del ciclo (no hay `laliga_calendar.json` en git;
  solo `calendar_changes.jsonl`).

**Limites:** solo las fechas de comienzo de jornada; los aplazados (E43)
el fichero no los ve hasta que hay fecha nueva.

**Veredicto: SE AGUANTA el calendario de Pepe.** Para el gestor y el chat
del dueno: las fechas se leen del artefacto del ultimo ciclo (o del log de
Pepe), nunca de una copia local; y el «roundStarted» del tablon confirma
la hora.

### E59 · 24/10/2026 11:15 de Madrid · ¿Mas pelea con la jornada en juego? No

**Hipotesis:** el otro lado de E57: si la vispera hay poca pelea, quiza
con la jornada ya empezada hay mas (los rivales rehacen plantilla para la
siguiente). Hoy, con la J10 en juego, Pepe perdio tres pujas (Catena por
21.100, Revivo a +29 %, Thiago Fernandez) y Luismi compro cinco.
**Datos:** las 217 subastas del Computer del tablon, clasificadas por el
momento del reset que las resuelve: con una jornada principal empezada y
sin terminar, la vispera (<24 h de la siguiente) o entre jornadas.
**Codigo:** `lab/subasta/con_la_jornada_en_juego.py`.

    momento              n    con pelea   prima (mediana)   las que suben: pelea / prima con pelea
    vispera (<24 h)     23       26 %         +0,3 %                43 %  /  +24 %
    jornada en juego   119       50 %         +1,9 %                68 %  /  +8,3 %
    entre jornadas      75       49 %         +4,6 %                71 %  /  +8,7 %

**Lo que se aprende:**
- **Con la jornada en juego no hay mas pelea que entre jornadas** (50 %
  contra 49 %; en los que suben, 68 % contra 71 %, prima casi igual). La
  hipotesis no se sostiene.
- **E57 se mantiene** con otra forma de contar: la vispera, la mitad de
  pelea y prima mediana +0,3 %. (Cuando la hay, entre los que suben, es
  cara: +24 %, n muy pequeño.)
- Lo de hoy es lo normal: pujas por jugadores que suben, a prima corta,
  contra rivales que pagan +8 % de mediana (E41/E49). Catena por un 0,8 %
  es mala suerte dentro de esa regla, no un patron.

**Limites:** el tramo de la vispera se queda en 23 al separar las
subastas con una ronda en juego (los aplazados se solapan).

**Veredicto: NO GANA** (nada nuevo para el plan). Lo unico que confirma:
la ventana barata es el reset del dia de la jornada (E57).

### E58 · 23/10/2026 17:21 de Madrid · ¿Cuanto juega un 50 % de FF? Aun no hay datos para saberlo

**El caso:** el once de la J10 lleva a Jonny y a Sergi Cardona al 50 % de
FF, sin banquillo. La vara de Pepe cuenta un 50 % como medio jugador. ¿Es
asi?
**Datos:** solo habia titularidad de FF guardada para los 20 del
escaparate de cada dia: la vispera de la J8 y la J9, **60 casos**
jugador-jornada; jugo = un partido mas en `puntos_por_jornada`.
**Codigo:** `lab/puntos/titularidad_calibrada.py`.

    FF la vispera    n    jugo
      0-30 %        19    21 %
     30-50 %        14    71 %
     50-60 %        10    50 %
     70-80 %         8   100 %
     80-100 %        8    62 %

**Lo que se aprende:** con 60 casos no sale una curva: los tramos van
arriba y abajo (30-50 % juega mas que 50-60 %; 80-100 % menos que
70-80 %). «Jugo» cuenta tambien salir del banquillo. **No he aprendido
cuanto juega un 50 %.**

**Lo que si hay:** desde el 20/10 Pepe guarda cada dia la titularidad de
FF de ~505 jugadores (`la_titularidad_del_dia.jsonl`, commit 983fce96).
El script ya lee ese libro: cuando entre la foto de la J10 en
`puntos_por_jornada`, la curva saldra con ~500 casos por jornada.

**Veredicto: SIN RESULTADO** (datos insuficientes). Pendiente: correr el
script el martes 27/10, tras la J10.

### E57 · 23/10/2026 11:16 de Madrid · ¿Hay menos pelea la vispera de la jornada?

**Hipotesis (del gestor, 23/10):** Boye (+12,2 %) y Gaya se ganaron sin
rival en el reset del dia de la jornada; quiza los rivales no pujan fuerte
cuando la subasta se resuelve justo antes de que empiece la jornada (en
rojo no pueden arriesgar; lo que compren casi no llega a jugar).
**Datos:** las 210 subastas del Computer del tablon con precio y una
jornada por delante; horas desde el reset que la resuelve hasta el
siguiente «roundStarted».
**Codigo:** `lab/subasta/vispera_de_jornada.py`.

    horas a la jornada     n    con pelea   pujadores   prima del ganador   solo las que suben (n / pelea)
       0-24               39       31 %       1,46          +0,3 %              21 /  52 %
      24-48               22       41 %       1,50          +1,2 %              11 /  64 %
      48-96               51       57 %       1,78          +3,3 %              33 /  73 %
      96+                 98       50 %       1,77          +2,6 %              62 /  73 %

**Lo que se aprende:**
- **La hipotesis se sostiene:** en las subastas que se resuelven el dia de
  la jornada hay la mitad de pelea (31 % contra 50-57 %), y el ganador
  paga +0,3 % de mediana (contra +2,6 a +3,3 %). Pasa tambien con los que
  suben (52 % contra 73 %), asi que no es solo que haya menos de los que
  suben ese dia.
- **Boye (+12,2 %, sin rival) pago ~650.000 de mas casi seguro:** a
  menos de 24 h, 7 de cada 10 subastas no tienen rival.

**Limites:** n = 39 en el tramo de menos de 24 h (9 de 3 M o mas, 4 con
pelea); no mide la caja de cada rival (no hay historial de su saldo), que
seria la otra mitad de la hipotesis.

**Veredicto: GANA** (pasa a «Listo para el plan»): la prima de la orden y
de la mejora del once, un escalon mas baja cuando la puja se resuelve el
dia de la jornada.

### E56 · 22/10/2026 17:18 de Madrid · Como paga la «parte 3»: con el once y la caja de la parte 2 (E55 fallo)

**El caso:** E55 predijo que Pollo17, en rojo al saque del Levante-Athletic
(21/10), cobraria 0. La ronda 5176 se pago hoy a las 17:03 de Madrid y
**la prediccion fallo**.
**Datos:** las rondas 5125 (J6 parte 2, pagada el 18/09) y 5176 (parte 3)
del tablon, y la bitacora del saldo de Pepe.
**Codigo:** `lab/carrera/partes_de_una_jornada.py`.

    manager        parte 2 (18/09)     parte 3 (22/10)     diferencia
    Pepe            29 pts   870.000    40 pts 1.200.000    +11 pts  +330.000
    Pollo17         17 pts   510.000    24 pts   820.000     +7 pts  +310.000
    Manzagool       49                  52                   +3      +90.000
    Alvaro R.       26                  29                   +3      +90.000
    Prinzipote      35                  36                   +1      +30.000
    DiosMande       52                  52                    0            0
    Mex             13 pts   390.000    13 pts   640.000      0     +250.000
    Luismi_Haz      64 sin premio       64 sin premio        (rojo en la parte 2)

    saldo de Pepe: 6.975 -> 336.975 (+330.000 = 11 x 30.000)

**Lo que se aprende:**
- **La parte 3 no es una jornada nueva: es la misma J6 que se completa.**
  Biwenger lista los TOTALES de la J6 (parte 2 + el partido nuevo) y paga
  solo la diferencia. DiosMande, sin nadie en ese partido, sigue en 52.
- **Cuenta el once de la parte 2 (15/09), no el de hoy:** Pollo17 suma +7,
  no los ~24 de sus jugadores de ahora (E50); Pepe suma +11, no los 5 de
  Olasagasti.
- **Y el rojo que cuenta es el de la parte 2:** Pollo17 empezo el 21/10 en
  -2,86 M y cobro igual; Luismi, en rojo el 15/09, sigue sin premio.
- **El plus de los tres ultimos se recalcula con los totales:** Mex no
  suma puntos pero cobra +250.000 (ahora es penultimo de la J6 entera);
  Pollo17 cobra +100.000 por quedar antepenultimo.
- **Por tanto, E45 se equivoco dos veces** (habia ronda nueva, pero con el
  once y la caja viejos) y **el plazo de caja del 21/10 no hacia falta:**
  la venta de Rico (E47 ya decia que sobraba) no salvo nada.

**Limites:** un solo caso (n = 1). La parte 2 de la J6 si fue ronda con
caja propia (Luismi la perdio el 15/09); lo medido aqui vale para una
parte que solo completa partidos sueltos de una ronda ya pagada.

**Veredicto: CORRIGE E45/E55** y pasa a «Listo para el plan»: el partido
suelto de una jornada ya empezada no es plazo de caja. Aplica ya al
Rayo-Athletic de la J8: contara con el once y la caja del 09/10 (Pepe en
verde), y su premio llegara como diferencia sobre la J8.

### E55 · 22/10/2026 11:16 de Madrid · El aplazado del 21/10 era ronda propia, y Pollo17 la empezo en rojo

**Lo que quedaba abierto:** E45 dudaba entre dos cosas: que el
Levante-Athletic fuera el partido que le faltaba a la ronda 4904 (con el
once del 03/09) o que Biwenger abriera una ronda nueva. E50 dejo apuntada
la prueba.
**Datos:** el tablon de hoy y las fotos de los ciclos de las 19:10 y 20:09
de Madrid del 21/10 (artefactos), justo antes y despues del saque (20:00).
**Codigo:** `lab/carrera/quien_se_juega_el_21.py` (E50) sobre la foto de
las 19:10.

**Lo que dice el tablon:**

    21/10 18:00 UTC  roundStarted  «Jornada 6 (aplazada)», part 3, id 5176

- **Era ronda propia** (la hipotesis que E45 daba por menos probable). El
  gestor acerto al tratarlo como plazo de caja (E45/E47). La 4904 («Jornada
  6», 03/09) y la 4906 (J8, sin el Rayo-Athletic) siguen abiertas.

**Quien la empezo en rojo** (saldo a las 19:10 y 20:09 de Madrid, igual):

    manager        caja al saque     esperado en ese partido
    Pollo17         -2.861.849           23,7  (Ivan Romero, Robert Navarro, Brugue, De la Fuente)
    Luismi_Haz      -8.166.616            3,6
    Pepe            +1.717.983            5,2  (Olasagasti)
    los demas        en verde

- **Pollo17 empezo la ronda en rojo** (gasto el premio de la J9 en Kubo,
  Pepelu y dos mas el 21/10 a las 07:00). Por la regla de la liga (E29,
  Luismi en la J6 aplazada: 64 puntos, 0 euros), **sus ~24 puntos
  esperados de ese partido no cuentan**. Era la ronda que mas le
  favorecia (E50: +14 sobre Pepe); ahora puede ir al reves.

**(Nota del 22/10 17:18: esta prediccion FALLO; ver E56. La parte 3
cuenta con el once y la caja de la parte 2.)**

**Prediccion para cuando se pague la 5176** (por el reloj de E43, hoy
entre las 12:00 y las 17:00 de Madrid): Pollo17 y Luismi, 0 puntos y 0
euros; Pepe, los de Olasagasti x 30.000 (o el plus si queda entre los tres
ultimos de esa ronda, E52). La clasificacion de hoy (Pollo 381, Pepe 372,
solo rondas cerradas) se acercaria en lo que haga Olasagasti.

**Veredicto: CIERRA E45** (ronda propia, comprobado) y deja una
prediccion que se juzga esta tarde. Para Pepe: la regla de no empezar
nunca en rojo, otra vez, vale puntos; esta vez se los quita al rival.

### E54 · 21/10/2026 17:18 de Madrid · Tras un cero: ¿tiene razon «el parte vende»?

**Hipotesis:** un jugador que hace 0 puntos o menos en una jornada (la
señal de «el parte vende», construido y apagado, para encender tras la
J10) juega menos, puntua menos y pierde precio despues; si fuera ruido,
venderlo seria regalarlo.
**Datos:** las tres fotos de `puntos_por_jornada.jsonl` (tras J7, J8 y J9):
264 jugadores que jugaron la J8 (fuera Athletic, Rayo y Levante por los
aplazados); 21 hicieron <= 0. Puntos de la J9 y precio del 13/10 (el dia
despues de la J8) al 20/10.
**Codigo:** `lab/puntos/tras_un_cero.py`.

    J8               n    pts/partido antes   juega la J9   pts en la J9   precio a 7 dias
    <= 0 puntos     21          3,0               24 %           1,4            -8,2 %
    > 0 puntos     243          4,0               82 %           4,3            -2,0 %

    mismo nivel previo (0-3 pts/partido):  <= 0  n=4   J9 0,5   precio -6,4 %
                                            > 0  n=57  J9 3,3   precio -4,5 %

**Lo que se aprende:**
- **El cero anuncia de verdad:** de los 21, solo 5 jugaron la J9 (24 %
  contra 82 %) y su precio cayo otro -8,2 % en la semana siguiente (contra
  -2,0 %). Un cero suele ser lesion, roja o perder el sitio, no mala
  suerte.
- **Vender el dia despues compensa:** el -8,2 % se mide desde el 13/10, el
  dia siguiente a la jornada; venderlo esa mañana al Computer (oferta
  ~precio, E38/E42) se ahorra esa caida y deja hueco para uno que juegue.
- Con el mismo nivel previo, la diferencia se encoge pero no se va
  (n muy pequeño).

**Limites:** una sola jornada y 21 casos; los de 5+ pts/partido con cero
son 1. Repetir con la J10 (y separar porteros, que no se midieron aparte).

**Veredicto: SE AGUANTA la premisa de «el parte vende».** Nada nuevo que
construir (ya esta hecho y revisado); cuando se encienda tras la J10, su
primera semana sirve de prueba: los que venda, ¿bajan despues mas de un
-2 % a 7 dias?

### E53 · 21/10/2026 11:16 de Madrid · La vara de puntos fuera de muestra: el precio predice mejor

**Hipotesis:** los puntos por partido (la base de la vara de Pepe: tasa x
titularidad) predicen lo que un jugador hara despues mejor que su precio.
**Datos:** `data/intelligence/puntos_por_jornada.jsonl` ya tiene tres
fotos (tras la J7, J8 y J9). Lo que se sabia tras la J7 (puntos, partidos,
precio) contra los puntos hechos en la J8 y la J9. 364 jugadores con 3+
partidos; fuera Athletic y Rayo (su partido de la J8 no se jugo, E43).
**Codigo:** `lab/puntos/vara_fuera_de_muestra.py`.

    Spearman con los puntos de J8+J9          todos (364)   jugaron las dos (216)
    puntos por partido                           +0,34            +0,42
    puntos por partido encogidos (K=3)           +0,33            +0,42
    puntos totales                               +0,37              -
    PRECIO                                       +0,44            +0,49
    precio + encogidos (rangos sumados)          +0,42            +0,49

    por posicion (todos):  DEF ppp +0,29 / precio +0,43;  MED +0,37 / +0,46;
                           DEL +0,27 / +0,41;  POR (n=19) nada predice

**Lo que se aprende:**
- **El precio predice los puntos que vienen mejor que los puntos por
  partido**, en todas las posiciones de campo (+0,41 a +0,46 contra +0,27
  a +0,37). El precio ya resume titularidad, forma y lo que sabe el
  mercado. Sumar los puntos por partido al precio no añade nada.
- Encoger los puntos por partido hacia la media (como hace
  `el_calendario_de_puntos.tasa_encogida`) no mejora nada con estos datos.
- Cuadra con E48: cada millon da puntos, con rendimientos decrecientes.

**Limites:** dos jornadas; la foto de la J9 pudo cerrarse antes del
Getafe-Rayo; no se ha podido probar la titularidad de FF del momento (no
se guardaba), que es lo que la vara de Pepe multiplica: la vara real
(tasa x titularidad) daba ~+0,36 en E7, por debajo de este +0,44 del
precio. Repetir con la J10-J11.

**Veredicto: GANA con cautela** (pasa a «Listo para el plan» como
prueba, no como cambio directo): la mejora del once deberia mirar el
precio como segunda opinion.

### E52 · 20/10/2026 17:17 de Madrid · La formula del premio de jornada (y el premio de la J9)

**El caso:** el premio de la J9 ha entrado hoy a las **17:05 de Madrid**
(18,1 h tras el ultimo partido, dentro de la ventana de E43/E47): Pepe 49
puntos, **1.470.000**. Saldo de -2.017 a ~+1,47 M: el plazo del aplazado
de mañana esta cubierto sin la racha (E47 lo daba por hecho con un minimo
de 870.000; la venta de Rico de anoche no hacia falta). Pero los de abajo
no cobraron 30.000 por punto: DiosMande, 27 puntos, 1.310.000.
**Datos:** los 10 «roundFinished» del tablon (J1-J9 y las partes
aplazadas), 67 premios.
**Codigo:** `lab/caja/el_premio.py`.

**La formula, comprobada:**
- **Premio = 30.000 x puntos + un plus para los tres ultimos de la
  jornada:** antepenultimo +100.000, penultimo +250.000, ultimo +500.000.
  45 de 67 premios son 30.000 x puntos exactos; los 21 de abajo llevan
  justo esos plus (J1-J5, J7, J9; con 7 u 8 managers). La parte aplazada
  de la J6 no llevo plus.
- **Quien empieza en rojo cobra 0** aunque puntue (Luismi, J6 aplazada,
  64 puntos, 0 euros: E29).
- **Para Pepe nada cambia:** siempre ha quedado del 1.º al 5.º, donde el
  punto vale 30.000 justos (E16). El plus empuja a los de abajo: quedar
  ultimo con 27 puntos paga lo mismo que quedar quinto con 44.

**Limites:** 10 rondas; no se ha visto a dos empatados en el puesto del
plus (en la J5 Mex y Prinzipote empatan a 45 y solo cobra el plus el que
el tablon pone despues).

**Veredicto: SE AGUANTA E16** (30.000 por punto para Pepe) y el reloj del
premio de E43 acierta otra vez (7 de 7). Sin regla nueva. Nota para la
caja: el premio de la J9 llego a las 17:05, al final de la ventana; contar
con el a partir de las 18:00, no de las 12:00.

### E51 · 20/10/2026 11:16 de Madrid · ¿Cuanto le queda a una racha de subidas?

**Hipotesis:** cuanto mas lleva un jugador subiendo, menos le queda (la
racha «se cansa»). Si es asi, la cartera y la rotacion deberian preferir
al que acaba de empezar a subir.
**Datos:** `data/autopilot/price_history.json`, todos los jugadores, cada
dia de una racha (n = 7.519 dias-jugador subiendo).
**Codigo:** `lab/precio/rachas.py`.

    dias seguidos subiendo   casos   sube manana   le queda hasta el primer dia sin subir (mediana)
        1                     745      90,6 %         +6,8 %
        2                     646      92,4 %         +7,1 %
        3-5                 1.597      91-94 %        +5,9 a +6,5 %
        6-9                 1.496      88-92 %        +4,6 a +5,6 %
        10+                 3.035      92,4 %         +4,5 %

**Lo que se aprende:**
- **La racha no se cansa:** la probabilidad de subir mañana es ~91 % se
  lleve 1 dia o 10. Lo que si baja es lo que queda en %: de +7 % al
  empezar a +4,5 % tras 10 dias (el precio ya es mayor y las subidas
  diarias no crecen tanto). La media (+13 a +44 %) la inflan unos pocos
  baratos que se disparan.
- **La cuenta que importa para comprar:** lo que le queda a uno que sube
  (+4,5 a +7 % de mediana) contra lo que cuesta ganarlo. Sin pelea (+1 %),
  gana. Con pelea, el ganador paga hoy +10 % por los que suben poco y
  +33 % por los que suben mucho (E49): **a la mediana, una compra con
  pelea no se paga con la subida que le queda.** Solo se paga si el
  jugador entra en el once (puntos) o si es de los baratos que se
  disparan.

**Limites:** la mediana esconde colas muy largas en los baratos; no separa
por precio; dias-jugador de la misma racha no son independientes.

**Veredicto: SE AGUANTA lo que hay** (comprar al que sube, vender el
primer dia que no sube, E1/E3) y no hace falta mirar cuantos dias lleva
subiendo. Refuerza E46/E49: para revender, la prima tiene que quedarse por
debajo de lo que le queda a la racha (~+5 %); por encima, solo si es para
el once.

### E50 · 19/10/2026 17:15 de Madrid · El Levante-Athletic del 21/10, manager a manager

**Hipotesis:** el aplazado de la J6 (mie 21/10 20:00) pesa distinto para
cada manager segun cuantos jugadores tenga del Levante y del Athletic; y
si es ronda propia (E45), quien la empiece en rojo los pierde.
**Datos:** la foto del ciclo de las 17:10 de hoy (plantillas, titularidad
FF, caja de cada manager); vara de E20 (puntos por partido x titularidad).
**Codigo:** `lab/carrera/quien_se_juega_el_21.py`.

    manager        caja hoy       esperado en ese partido
    Pollo17        -377.549          17,8  (De la Fuente, Ivan Romero, Robert Navarro, Brugue)
    Mex             560.800           5,0
    Prinzipote    1.314.772           4,1
    Pepe           -432.317           3,7  (Olasagasti)
    Luismi_Haz  -12.144.016           3,0
    Manzagool    -1.578.989           2,5
    Alvaro R.    15.105.200           1,3
    DiosMande       345.475           0

**Lo que se aprende:**
- **Ese partido favorece a Pollo17 en ~14 puntos sobre Pepe** si cuenta
  con los onces de hoy (17,8 contra 3,7): la ventaja de 3 puntos de Pepe
  se iria ese miercoles.
- **Pollo17 esta en rojo** (-377.549) y, si es ronda propia, perderia esos
  ~18 puntos y ~530.000 de premio si no sale antes. Lo normal es que
  salga: cobrara el premio de la J9 el martes (E43/E47) igual que Pepe.
- **Es la prueba que zanja E45:** el jueves 22/10 por la manana, mirar si
  la clasificacion de Pollo17 sube con los puntos de esos cuatro en ese
  partido. Si sube, el aplazado iba con el once de hoy (ronda propia o la
  4904 con onces nuevos); si no se mueve hasta que termine la 4904, iba
  con el once del 03/09 (cuando Pollo17 no tenia a varios de ellos).

**Limites:** una foto; la titularidad cambia; no se sabe con que once
contara Biwenger ese partido.

**Veredicto: AVISO para la carrera y prueba apuntada.** Para Pepe no
cambia nada (plazo de caja del miercoles, E47). Para leer la clasificacion
del jueves: un salto de Pollo17 de ~15-20 puntos sin jornada nueva es este
partido.

### E49 · 19/10/2026 11:16 de Madrid · E41 fuera de muestra: la pelea se sigue viendo venir

**Hipotesis:** la regla de E41 (sin subida la vispera casi nadie pelea;
con subida >= 2 %, pelea y prima alta) vale tambien en subastas que E41 no
vio.
**Datos:** las 13 subastas del Computer resueltas del 15/10 al 19/10
(dia de mercado >= 15/10), 6 con pelea. n pequeño: es una comprobacion,
no una medida nueva.
**Codigo:** `lab/subasta/pelea_fuera_de_muestra.py`.

    vispera          n   con pelea (E41)    paga el ganador si hay pelea (E41)
    no subio         2      0 %  (13 %)          -
    subio < 2 %      7     43 %  (64 %)       +10,1 %  (+7,2 %)
    subio >= 2 %     4     75 %  (83 %)       +33,0 %  (+16,2 %)

**Lo que se aprende:**
- **El orden se mantiene:** sin subida no hay pelea; cuanto mas sube, mas
  pelea. **Pero las primas han subido:** el ganador paga ahora +10 % y
  +33 % (E41: +7 % y +16 %). Luismi puja fuerte con -7,6 M de caja y
  Pollo17 le disputa (19/10: Luismi pago 4.256.000 por uno que Pollo17
  pujaba a 3.777.000).
- **Pepe en esos dias:** Lemar (subia +0,8 %) perdida, el ganador pago
  +10,1 %; **Cardona (subia +2,2 %) GANADA a +1 %**, por 7.000 sobre
  Luismi: el unico caso que va contra E41 (que le daba un 2 % de
  ganarla). Las pujas por Alvaro Nunez y Freeman no salen en el tablon.

**Limites:** 13 subastas en 5 dias. Las primas de un mercado que se
calienta pueden volver a bajar.

**Veredicto: SE AGUANTA E41** (y con ella la regla de «Listo para el
plan»). Ajuste para cuando se use: en los que suben >= 2 %, la prima que
gana hoy esta mas cerca de +30 % que de +16 %: pujar solo si el cambio en
el once lo vale.

### E48 · 18/10/2026 17:15 de Madrid · La carrera otra vez: Pollo17 ya tiene mejor once

**Hipotesis:** E20 (05/10) daba el once de Pepe por delante del de Pollo17
(48,1 contra 46,2 esperados). Pollo17 ha comprado desde entonces a los que
suben (prima media +16,7 %): ¿ha cambiado el orden?
**Datos:** la foto del ciclo de las 17:09 de hoy (`rival_squads` +
`todaLaLiga`), la misma vara que E20 (puntos por partido x titularidad FF,
estado ok), y todos los jugadores sanos con 4+ partidos para la curva
puntos-precio (n = 259).
**Codigo:** `lab/carrera/proyeccion.py` (E20) y `lab/carrera/once_detalle.py`.

    manager        puntos   once esperado 05/10 -> 18/10   valor del once
    Luismi_Haz       287          58,8 -> 59,1                85,0 M
    Pollo17          320          46,2 -> 53,3                64,2 M
    Manzagool        253          37,2 -> 50,3                  -
    Pepe             323          48,1 -> 47,5                56,6 M

**Lo que se aprende:**
- **Pollo17 ya saca 5,7 puntos por jornada mas que Pepe** con el once de
  hoy. En 30 jornadas son **+139 a +179 puntos** (con el 81-104 % de
  acierto de la vara, E20). La ventaja de 3 puntos de hoy no aguanta ni
  una jornada. Luismi va aun mejor (59,1), pero con -7,6 M de caja.
- **No es mal reparto, es menos dinero en el once.** Pepe saca 47,5 de
  56,6 M (0,84 pts/M) y Pollo17 53,3 de 64,2 M (0,83 pts/M). Los 7,6 M de
  diferencia en el once explican la diferencia: en la curva de la liga,
  entre 5 y 10 M cada millon da ~0,7-1,0 pts por partido.
- **Yamal no es el problema.** Vender a Yamal (25,4 M, 12,1 esperados)
  para fichar cinco de 5 M (mediana 5,5 pts/partido) y quitar a los cuatro
  peores (Cardona 2,0, Jonny 2,5, Chust 3,3, Luismi Cruz 3,3) deja el once
  igual a la mediana (22 contra 23,2) y solo gana ~+4 si los cinco fueran
  del cuartil alto, antes de pagar primas. La regla del dueno no cuesta
  puntos.
- **El once de Pepe es Yamal + Roberto + nueve de 2-4 puntos.** El de
  Pollo17 no tiene ninguno por debajo de 4 salvo Ruben Sanchez (30 %).

**Limites:** la vara sobreestima (81-104 %); es una foto de una tarde; la
titularidad de FF cambia cada dia; la J9 esta a medias.

**Veredicto: AVISO para la carrera.** Con el once de hoy Pepe pierde la
liga contra Pollo17 por ~150 puntos. La palanca es meter ~7-8 M mas en el
once (patrimonio, no reventa): lo que la cartera y la rotacion ganen tiene
que acabar en el once (regla del dueno: inversion son puntos), empezando
por las plazas de 2-3 puntos (Cardona, Jonny).

### E47 · 18/10/2026 11:16 de Madrid · ¿Hace falta vender a Rico para el plazo del miercoles?

**El caso:** Pepe esta en -432.317 y el plazo del aplazado de la J6 es el
**miercoles 21/10 a las 14:00** (E45, decision del gestor). El plan es
vender a Diego Rico (oferta ~468.100) tras su partido de la J9. Pero hay
dos ingresos con fecha: la racha diaria (250.000) y el premio de la J9.
**Datos:** las 37 rachas cobradas del tablon (7 managers) y el reloj de
premios de E43; calendario de la J9 (artefacto de las 13:10 de hoy).
**Codigo:** `lab/caja/la_racha.py`.

**Lo que se aprende:**
- **La racha de Pepe es un reloj:** 250.000 cada 5 dias, las tres
  ultimas exactas (5,0 dias) a las 00:10 de Madrid (la vuelta de las
  00:07, que entra cada dia). La siguiente: **miercoles 21/10 ~00:10**,
  antes del plazo. Los rivales que no entran todos los dias la pierden
  (huecos de 9-11 dias en DiosMande y Luismi).
- **El premio de la J9:** su ultimo partido es el lunes 19/10 21:00
  (Getafe-Rayo) y la J9 no tiene aplazados en el calendario. Biwenger
  paga 13-18 h despues (E43, 6 de 6): **martes 20/10 entre las 12:00 y
  las 17:00**. La peor jornada de Pepe hasta hoy son 29 puntos = 870.000.
- **La cuenta:** -432.317 + 250.000 (racha) = -182.317; con el premio de
  la J9, **+0,7 M o mas sin vender a nadie**. Solo la racha no basta.

**Limites:** la J8 enseña que un premio puede esperar (E43), aunque alli
habia un partido sin jugar; la racha depende de que la vuelta de las 00:07
entre a su hora.

**Veredicto: AVISO con regla de decision para el gestor.** El martes 20/10
a las 21:15: si el premio de la J9 ha entrado («roundFinished» de la J9 en
el tablon y saldo arriba), no se vende a Rico por el plazo. Si no ha
entrado, vender a Rico esa noche: su oferta del lote del 19/10 07:00 sigue
viva hasta el 21/10 07:00 (E42) y deja el saldo en ~+286.000 con la racha.

### E46 · 17/10/2026 17:15 de Madrid · La rotacion con la prima de verdad

**El caso:** hoy se ha construido, apagada, «la rotacion»
(`BORDALAS_LA_ROTACION`): cambia al que lleva 2 dias sin subir por uno de
su posicion, del mercado, que sube; puja con la prima de la cartera por
precio (+12 % por debajo de 1 M, +4 % de 1 a 3 M, +1 % por encima). E41
dice que los que suben son justo los que tienen pelea. ¿Sigue ganando el
cambio pagando lo que hay que pagar para ganarlos?
**Datos:** el escaparate real de cada dia (`libro_del_escaparate.jsonl`,
31 dias, 20 del Computer al dia): 77 candidatos que subian; el historial
de precios para el viaje (vender al Computer el primer dia que no sube,
a precio x 1,007, E38) y para la deriva del que se deja (todos los que
llevan 2 dias sin subir, n de miles).
**Codigo:** `lab/rotacion/con_prima.py`.

    deriva del que lleva 2 dias sin subir: -0,7 % al dia (-3,5 % a 5 dias, -4,8 % a 7)

    prima fija   subio <2 % (n=35)            subio >=2 % (n=13)
                 se gana  cambio a 5 d        se gana  cambio a 8 d
    +1 %          41 %      +5,8 %             2 %      +18,3 %
    +5 %          58 %      +1,9 %            17 %      +13,9 %
    +8 %          76 %      -0,8 %            28 %      +10,9 %
    +12 %         88 %      -4,2 %            43 %       +7,1 %

    con las primas de la cartera por precio: positivo en las 5 casillas
    (<2 %: +2,9 % / +4,6 % / +3,5 %; >=2 %: +15,8 % / +15,0 %; n de 3 a 21)

(«cambio» = viaje del que entra - deriva del que sale, en % del precio,
contando solo las pujas que se ganan.)

**Lo que se aprende:**
- **La rotacion aguanta con la prima real.** La prima por precio de la
  cartera la deja en positivo en todos los tramos: el +12 % solo se paga
  por debajo de 1 M, donde los que suben suben mucho en %.
- **Lo que no hay que hacer: una prima fija alta para todos.** A +12 %,
  un jugador que sube poco (<2 %) da -4,2 %; pasa a perder a partir de
  +8 %. Lo confirma el propio modulo (con la puja fuerte, -3,8 %).
- **Casi todo lo da vender al que cae** (deriva -0,7 % al dia, lo mismo
  que mide el modulo, -6,1 % a 7 dias). Comprar al que sube añade poco y
  depende de ganar la subasta: a +1-4 % por uno que sube >=2 % se gana
  1 de cada 6-50 veces.

**Limites:** n pequeño en el tramo >=2 % (13); el «se gana» viene del
tablon (E41), no de pujas de Pepe; no mide la maldicion del ganador (si
lo que se gana es lo que nadie mas queria, puede salir peor). La deriva
es la mediana de todo el universo, no la de la plantilla de Pepe.

**Veredicto: SE AGUANTA la rotacion como esta construida** (prima por
precio, nunca la puja fuerte). Nada nuevo para el plan; para cuando se
encienda: no subirle la prima a los de 1 M o mas que suben poco.

### E45 · 17/10/2026 11:15 de Madrid · El Levante-Athletic del 21/10: ¿plazo de caja?

**El caso:** el puesto de mando tiene abierta la duda de si el aplazado de
la J6 (Levante-Athletic, martes 21/10 20:00) es una ronda propia que
empieza ese dia, con su propio «quien empieza en rojo no puntua». Pepe
esta hoy en **-432.317** (tras ganar a Cardona).
**Datos:** las rondas del tablon (roundStarted/roundFinished de J1 y J6,
con sus ids) y la foto del ciclo de las 11:10 de hoy (plantilla, saldo,
ofertas del Computer).
**Codigo:** `lab/carrera/aplazado_j6.py`.

**Lo que dice el tablon:**

    15/08 roundStarted  Jornada 1 (4899)        20/08 roundFinished (4899)
    25/08 roundStarted  Jornada 1 aplazada (4937) 28/08 roundFinished (4937)
    03/09 roundStarted  Jornada 6 (4904)        ... NUNCA terminada
    15/09 roundStarted  Jornada 6 aplazada (5125) 18/09 roundFinished (5125)

- **Cada parte es una ronda con su propio comienzo** (y su propio rojo:
  Luismi perdio los 64 de la 5125, E29). Eso esta medido.
- **Lo nuevo:** la ronda 4904 («Jornada 6», empezo el 03/09 con el Real
  Sociedad-Celta) **sigue abierta seis semanas despues**. Lo mas probable
  es que el Levante-Athletic sea el partido que le falta: entonces su once
  y su control del rojo fueron el 03/09, y el 21/10 NO seria un plazo
  nuevo. Es la misma pinta que la J8 (4906): empezada, sin terminar, a la
  espera del Rayo-Athletic (E43). Pero no esta probado: Biwenger tambien
  podria abrir una «parte 3» el 21/10.
- **Lo que se juega Pepe:** solo **Olasagasti** (Levante) juega ese
  partido. En el peor caso (ronda nueva y Pepe en rojo) se pierden sus
  puntos de un partido (~4-6 pts, ~150.000 de premio).
- **Taparlo es barato:** la oferta del Computer por **Diego Rico es de
  468.100** (viva hasta el 19/10 07:00 y renovada ese dia, E42) y deja el
  saldo en +35.783. Rico juega la J9 (lunes) y no puede venderse antes
  (regla del dueno del 17/10); la J10 (jue 23/10, plazo 15:00) obliga a
  estar en verde de todos modos.

**Veredicto: AVISO.** Tratar el 21/10 20:00 como plazo de caja (lo que ya
decide el gestor) cuesta casi nada: vender a Rico (o a quien toque) el
lunes 20/10 tras su partido adelanta lo que la J10 ya exige. Se sabra
cual de las dos es mirando el tablon el 21/10: si aparece un
«roundStarted» nuevo a las 18:00 UTC, es ronda propia; si no, y la 4904
termina despues, el aplazado iba con el once del 03/09.

### E44 · 16/10/2026 17:18 de Madrid · ¿Acierta la valoracion de Pepe?

**Hipotesis:** el «value» que el motor de pujas da a cada jugador del
mercado (lo que cree que vale) anuncia si su precio va a subir. Si no,
pujar por «value > precio» es pujar a ciegas.
**Datos:** `data/intelligence/libro_de_la_valoracion.jsonl` (23/09-16/10),
729 filas jugador-dia con value, precio y precio 7 dias despues. Un mismo
jugador sale varios dias: las filas no son independientes.
**Codigo:** `lab/valoracion/acierta.py`. Vara de comparacion: «subio
ayer» (la inercia de E1/E2).

    vara                          n    precio a 7 dias (mediana)   suben
    value > precio + 3 %         156          +1,0 %                53 %
    value entre -3 y +3 %        407          +2,9 %                65 %
    value < precio - 3 %         166          -6,3 %                 3 %
    subio ayer                   480          +3,8 %                72 %
    no subio ayer                249          -6,0 %                 3 %
      subio y value > +3 %       104          +9,4 %                78 %
      NO subio y value > +3 %     52          -5,8 %                 2 %

**Lo que se aprende:**
- **La inercia predice mucho mejor que el value** (Spearman con el precio
  a 7 dias: 0,65 frente a 0,38). Con el value solo, «vale mas de lo que
  cuesta» acierta menos que «vale lo que cuesta».
- **El value si añade algo DENTRO de los que suben:** entre los que
  subieron ayer, los que Pepe valora por encima suben +9,4 % en una
  semana, frente a +3,3 %. Fuera de ellos, nada: de 52 que no subian y
  Pepe valoraba un 3 % por encima, subio 1.
- Los «XI_UPGRADE» bien valorados bajan (-5,3 % a 7 dias): normal, se
  compran por puntos (E14/E16), no para revender.

**Limites:** 3 semanas; filas repetidas del mismo jugador; el libro solo
tiene el mercado del Computer y de rivales que Pepe miro.

**Veredicto: CONFIRMA la rampa (E1) y ordena las dos varas.** Para
revender: primero que suba (la rampa), despues el value para elegir entre
los que suben. Un value alto en uno que no sube no es una compra. Nada
nuevo que construir si la rampa ya filtra antes de mirar el value; si en
algun camino de especulacion el value decide solo, eso hay que cerrarlo.

### E43 · 16/10/2026 11:16 de Madrid · ¿Cuando paga Biwenger el premio de la J8?

**El caso:** la J8 acabo el lunes 12/10 y el viernes 16/10 su premio sigue
sin entrar (Pepe sigue con 323 puntos y 7 jornadas contadas). El gestor
sospecha del Rayo-Athletic.
**Datos:** los «roundFinished» del tablon (J1-J7) contra el calendario de
los ciclos (`data/calendar/laliga_calendar.json` del artefacto de las
11:10 de hoy); y los partidos jugados de cada jugador (foto de hoy contra
`puntos_por_jornada.jsonl` de la J7).
**Codigo:** `lab/carrera/cuando_se_cobra.py`.

**Lo que se aprende:**
- **Biwenger paga 13-18 h despues del ultimo partido del bloque** (J1-J5
  y J7, 6 de 6; el martes por la tarde si la jornada acaba el lunes).
  Cuando habia partidos descolgados, partio la jornada y pago igual: la J1
  (cuatro partidos una semana despues, «Jornada 1 (aplazada)» cobrada
  aparte el 28/08) y la J6 (Levante-Athletic movido al 21/10, cobrada el
  18/09 sin el).
- **La J8 es la primera vez que espera.** El Rayo-Athletic (10/10) NO se
  jugo: los 27 jugadores del Athletic y los 29 del Rayo siguen con los
  mismos partidos que tras la J7; el resto de equipos, 52-71 % con un
  partido mas. Esta vez Biwenger no ha partido la jornada: el premio
  llegara cuando se juegue ese partido, o cuando decida partirla. **No hay
  fecha.** Pepe tiene a Unai Lopez (Rayo): sus puntos de la J8 tambien
  esperan.
- **El calendario de Pepe no lo sabe:** `laliga_calendar.json` sigue
  dando el Rayo-Athletic como jugado el 10/10 14:00 y no tiene fecha
  nueva. El Athletic arrastra dos aplazados (este y el Levante-Athletic
  del 21/10): cuando se encajen, el Rayo y el Athletic tendran semanas de
  dos partidos que la mejora con calendario no ve.

**Limites:** 7 jornadas; no se sabe por que esta vez Biwenger no parte la
jornada. Los ids de equipo (1 = Athletic, 70 = Rayo) se han sacado de
los nombres de sus jugadores.

**Veredicto: AVISO, no regla.** Para la caja: el premio de la J8 (~1,1-
1,4 M) no se cuenta hasta ver su «roundFinished» (el gestor ya lo hace
asi). Para la mejora con calendario (pasa a «Listo para el plan»): un
partido con fecha pasada y sin jugadores con un partido mas es un
aplazado; y una semana con dos partidos vale doble.

### E42 · 15/10/2026 17:16 de Madrid · El reloj de las ofertas del Computer (corrige E38/E40)

**El caso:** E40 tranquilizo al gestor con que «el 16/10 es noche par» y
habria oferta por Exposito. Pero la puja por Lemar se resolvio el
**jueves 15/10** a las 07:00 (no el 16), y el censo de las 02:10 del 15/10
solo tenia una oferta (Chust). Si se hubiera ganado Lemar, ¿habia con que
cobrar a Exposito?
**Datos:** `dashboard/data/status.json` de 5 vueltas de hoy (07:19, 08:11,
09:11, 13:11 y 17:10 de Madrid; artefactos bordalas-live-diagnostics),
10 ofertas por foto, con sus horas hasta caducar.
**Codigo:** `lab/ofertas/reloj_de_ofertas.py`.

**Lo que se aprende:**
- **SI la habia.** A las 07:19 de hoy Pepe tenia 10 ofertas del Computer,
  entre ellas **Exposito 4.663.800** (-3,4 %). Nueve caducaban a la vez,
  en **47,7 h**: nacieron con el reset de las 07:00 de hoy y viven 48 h.
  La de Chust, en 23,7 h: va en el otro turno.
- **El reloj de verdad:** el Computer renueva las ofertas de los
  publicados **cada 48 h, con el reset de las 07:00** (ahora los dias
  impares: 13, 15, 17...) y cada oferta vive 48 h. Las «noches pares» de
  E38/E40 eran un efecto de la foto: el censo de las 02:10 solo ve el
  lote del dia anterior en su segunda noche. Las ventas cobradas «hasta
  27 h despues del censo» de E40 cuadran: 19 h de vida antes del censo +
  27 = 46 h.
- **Para Pepe:** un jugador publicado tiene siempre una oferta viva del
  Computer; el dia de renovacion, la vieja muere a las 07:00 y la nueva
  nace con el reset. Esperar «a la siguiente oferta» (E22) es esperar
  48 h, no 24.

**Limites:** un solo dia de fotos con caducidad (5 fotos, 10 ofertas); si
el Computer cambia de fase, el dia de renovacion cambia. No se ve si
renueva tambien a un jugador recien publicado fuera de su turno.

**Veredicto: CORRIGE E38/E40** (la conclusion para el jueves se sostenia,
el porque no). Para el gestor: contar con una oferta viva por cada
publicado a cualquier hora, renovada cada 48 h a las 07:00; y E22
(esperar si la oferta es mala) cuesta dos dias, no uno.

### E41 · 15/10/2026 11:16 de Madrid · ¿Se sabe antes de pujar si habra pelea?

**El caso:** Lemar, perdido esta manana: el ganador pago 4.107.000 frente a
los 3.767.000 de Pepe (+10,1 % sobre el precio contra nuestro +1 %). La
puja fuerte de E37 (+12 %) tira un 11 % en las subastas que nadie pelea.
**Hipotesis:** lo que Pepe ve la vispera (si el precio subio) dice si
habra pelea y cuanto pagara el ganador.
**Datos:** tablon, 228 subastas del Computer con precio (106 con pelea);
y las 15 pujas de Pepe de 1 M o mas desde el 25/09.
**Codigo:** `lab/subasta/donde_hay_pelea.py`.

    precio la vispera     n   con pelea   paga el ganador   se gana a +1 % / +5 % / +12 %
    no subio             96     13 %          +2,6 %              65 % /  84 % /  97 %
    subio < 2 %          85     64 %          +7,2 %              41 % /  58 % /  88 %
    subio >= 2 %         47     83 %         +16,2 %               2 % /  17 % /  43 %

(«paga el ganador»: mediana en las que tuvieron pelea.) El precio del
jugador apenas separa (43-55 % de pelea de 0,5 M para arriba).

**Con las pujas de Pepe, cuadra entero:** las 9 perdidas tenian el precio
subiendo la vispera (Iglesias, Correia, Akhomach, Fofana, Recio, Romero,
Moi, Gerard, Lemar: de +0,5 % a +8,9 %). Las ganadas baratas (Blanco,
Zubeldia, Gulacsi, Luismi Cruz) tenian el precio bajando. La unica ganada
subiendo, Roberto Fernandez, costo +6,8 %.

**Lo que se aprende:** la pelea se ve venir. Los rivales (y la rampa de
Pepe, E1) van a por los que suben; los que bajan no los quiere nadie.
Pujar igual (+1 %) a todos es tirar las peleas que importan; pujar +12 %
a todos es tirar dinero en las que nadie pelea.

**Limites:** n = 47 en «subio >= 2 %». La regla mira solo el precio de
la vispera; no sabe a quien quiere cada rival (E11).

**Veredicto: GANA** (pasa a «Listo para el plan»): la prima de la puja,
segun la vispera, en vez de un +1 % fijo o un +12 % fijo.

### E40 · 14/10/2026 17:16 de Madrid · ¿Cuanto vive una oferta del Computer? (el jueves de Exposito)

**El caso:** si el jueves 16/10 a las 07:00 entra Lemar, Pepe queda en
-3,53 M y tiene que cobrar a Exposito (~4,68 M) antes de las 15:00. El
gestor teme que «el jueves a las 07:15 el Computer no ofrezca por
Exposito». E38 vio que las ofertas llegan las noches de fecha par (~02:10
de Madrid); el 14/10 se cumplio (9 ofertas, Jutgla vendido a las 07:18 a
la oferta de las 02:11). Falta saber si una oferta de las 02:10 sigue viva
despues del reset de las 07:00.
**Datos:** las 37 ventas de Pepe al Computer desde el 15/09 (tablon)
cruzadas con el censo de ofertas de cada noche (30 noches).
**Codigo:** `lab/ofertas/vida_de_la_oferta.py`.

**Lo que se aprende:**
- **Una oferta vive ~1 dia.** 23 de las 37 ventas cobran el importe exacto
  de una oferta censada: 17 la de esa noche y 6 la de la noche anterior.
  Se han cobrado ofertas hasta **26,9 h** despues del censo, y 16 de ellas
  despues del reset de las 07:00. Ninguna mas alla de ~27 h.
- **Tambien nacen ofertas a las 07:00.** El 30/09 y el 02/10, a las 07:18,
  Pepe cobro ofertas que no estaban en el censo de las 02:10 (4.076.200
  el 02/10): el Computer ofrece tambien con el reset, no solo de noche.
- **Para el jueves:** el 16/10 es noche par. La oferta por Exposito de
  las ~02:10 seguira viva de las 07:15 a las 15:00 (8 vueltas), y si no
  la hubiera, puede nacer otra con el reset. El 12/10 ofrecio 4.806.000
  por el. **Exposito ha tenido oferta las 7 noches pares desde el 02/10**
  (de 4.680.400 a 5.102.200) y ninguna impar. El riesgo de quedarse sin
  oferta es bajo.

**Limites:** el censo es una foto por noche: no se ve cuando nace cada
oferta ni cuando muere exactamente. 14 ventas no cuadran con ningun censo
(ofertas nacidas entre fotos). El ritmo de noches pares es de 11 noches.

**(Nota del 15/10: E42 corrige el porque. La puja se resolvia el jueves
15/10, noche impar; si habia oferta por Exposito, pero porque las ofertas
nacen con el reset de las 07:00 cada 48 h y viven 48 h.)**

**Veredicto: TRANQUILIZA, no hay regla nueva.** La cuenta del gestor para
el jueves (cobrar a Exposito entre las 07:15 y las 15:00) se sostiene. La
red de vender a otro no titular solo haria falta si a las 07:15 no hay
NINGUNA oferta por Exposito, cosa que no ha pasado en 7 noches pares.

### E39 · 14/10/2026 11:16 de Madrid · E37 contra las pujas reales de Pepe

**Hipotesis:** lo que E37 midio en el tablon (a +1 % solo se gana lo que
nadie pelea; a +12 %, dos de cada tres con pelea) vale tambien para las
pujas de Pepe. Y el «59 ganadas / 14 perdidas» del puesto de mando (13/10)
dice que Pepe gana casi siempre: ¿es verdad?
**Datos:** `data/trading/bid_outcome_ledger.json`, 76 filas (60 ganadas,
14 perdidas, 2 pendientes: Lemar y Pablo Ramon).
**Codigo:** `lab/subasta/las_pujas_de_pepe.py`.

**Lo que se aprende:**
- **El 59/14 engaña.** El libro repite la misma puja en varias vueltas
  (Maffeo 11 veces, Boyomo 6 el 18/09) y mezcla compras de 150.000 que
  nadie quiere. Pujas distintas: 47 ganadas y 14 perdidas. **De 1 M o mas
  desde el 25/09: 5 ganadas y 8 perdidas.** Las 5 ganadas son las que
  nadie peleo (Blanco +0,2 %, Zubeldia, Gulacsi, Luismi Cruz a +1 %) mas
  Roberto Fernandez, pagando +6,8 %.
- **Las perdidas, con lo que pago el ganador** (n = 11): +0,0, +1,6, +2,6,
  +7,0, +7,5, +8,5, +8,8, +10,4, +16,2, +16,8 y +41,2 %. **A +1 % se habria
  ganado 1; a +5 %, 3; a +8 %, 5; a +12 %, 8 de 11.** Coincide con E37
  (68 % a +12 % en el tablon): la puja fuerte habria ganado la mayoria de
  lo que Pepe ha perdido.

**Limites:** n = 11 perdidas con importe; tres perdidas (Caceres, Sotelo,
Carmona) sin importe ganador. No se sabe si los rivales habrian subido.

**Veredicto: CONFIRMA E37** con los datos de Pepe. Y para el gestor: la
vara de «cuanto gana Pepe sus pujas» tiene que contar pujas distintas y
de 1 M o mas; con esa vara, hoy pierde 8 de 13.

### E38 · 13/10/2026 17:20 de Madrid · ¿Cuando llega la oferta del Computer por Jutgla, y a cuanto?

**El caso:** la cuenta de la J9 del gestor (rafaga de las 14:15) da
~+0,3 M si entra Luismi Cruz el 14/10 y se vende a Jutgla «a ~2,9 M», y
avisa: «si Jutgla se vende por debajo del 90 % o tarda, rojo el jueves».
**Datos:** `data/solvency/censo_de_ofertas.jsonl` (las ofertas del Computer
que Pepe tiene vivas cada noche, 29 noches del 15/09 al 13/10, 156 ofertas)
cruzadas con el historial de precios.
**Codigo:** `lab/ofertas/cuando_llega.py`.

**Lo que se aprende:**
- **Por debajo del 90 % no ha pasado nunca.** Oferta / precio: minimo
  0,951, p10 0,966, mediana 1,007, maximo 1,049 (n = 156). Las de Jutgla
  (11 noches), entre 0,960 y 1,048.
- **Pero el precio no es 2,9 M: hoy es 2.700.000** y baja ~1 % al dia
  desde el 21/09 (3,20 M). El 16/10 rondara 2,64 M. Venta probable
  ~2,66-2,69 M; la peor vista (0,951), ~2,51 M. Es decir, **entre 0,2 y
  0,4 M menos que la cuenta del gestor**: el «+0,3 M» queda entre +0,1 y
  -0,1 M antes del premio de la J8.
- **Las ofertas llegan cada dos noches.** Desde el 04/10 el Computer
  ofrece por los jugadores de Pepe las noches de fecha par (6 ofertas, a
  las ~02:10 de Madrid) y las impares solo queda una (Chust). Una oferta
  sigue viva al menos 12 h (la del 24/09 12:10 seguia a las 00:14). Para
  la J9 hay **dos ventanas: 14/10 ~02:10 y 16/10 ~02:10**, las dos antes
  del cierre del 16/10 a las 21:00. «Tarda» no deja a Pepe sin vender;
  lo que puede pasar es que la del 14/10 llegue antes de saber si Cruz es
  nuestro (07:00) y caduque, y haya que esperar a la del 16/10.

**Limites:** 10 noches de alternancia; si el Computer cambia de ritmo, la
ventana del 16/10 puede no existir. No se sabe si el premio de la J8 se
cobra antes del 16/10 (la J8 aun no esta cerrada en los libros).

**Veredicto: AVISO para la cuenta de la J9, no regla nueva.** Contar a
Jutgla a 2,51 M (peor caso) y no a 2,9 M; con eso la J9 esta en verde
solo si el premio de la J8 entra antes del jueves.

### E37 · 13/10/2026 11:16 de Madrid · ¿Cuanto hay que pujar para ganar, y compensa la «puja fuerte»?

**El caso:** las cuatro ultimas pujas a precio + 1 % se perdieron (los
ganadores pagaron +6,4 %, +15,7 %, +0,6 % y +15 %). El gestor ha dejado
construida y APAGADA la «puja fuerte» (+4 % por cada punto por jornada que
el fichaje suma al once, hasta +12 %) y pide la cuenta antes de subirla.
**Datos:** el tablon, 230 subastas del Computer con precio del dia antes
(105 con pelea, es decir, con mas de un pujador). Para cada una, la puja
que habia que superar es la del ganador.
**Codigo:** `lab/subasta/cuanto_pujar.py`.

    puja = precio x (1+k)   se gana:  todas | con pelea | pelea y sube | pelea, 3 M o mas
    k =  1 % (Pepe hoy)                43 % |    12 %   |     9 %      |     16 %
    k =  5 %                           61 % |    34 %   |    31 %      |     32 %
    k =  8 %                           73 % |    51 %   |    49 %      |     58 %
    k = 12 % (tope puja fuerte)        83 % |    68 %   |    65 %      |     76 %
    k = 20 %                           90 % |    83 %   |    82 %      |     92 %

**Lo que se aprende:**
- **A +1 % Pepe solo gana lo que nadie quiere** (12 % de las subastas con
  pelea; 9 % si el jugador sube). Es lo que E9 ya decia y lo que han
  confirmado las cuatro derrotas seguidas. A +12 % se ganan 2 de cada 3
  con pelea, y 3 de cada 4 de los de 3 M o mas. De las cuatro perdidas,
  con +12 % se habrian ganado dos (Romero y Moi).
- **La cuenta en puntos sale con mucho margen.** Pujar +12 % en vez de
  +1 % sobre un jugador de 3 M cuesta 330.000 EUR mas (550.000 sobre 5 M),
  y ese dinero se pierde (al vender se cobra el precio, no lo pagado). Un
  fichaje que sume 1 punto por jornada durante las 29 que quedan son ~29
  puntos y 870.000 EUR de premio (E16). Aunque la estimacion de «puntos
  que suma» es ruidosa (E7, Spearman ~0,36) y se parta por la mitad,
  compensa. La regla del gestor (+4 % por punto) es prudente: el punto de
  equilibrio esta muy por encima del 12 %.
- **El limite no son los puntos, es la caja** (E36): ese sobrecoste se
  paga entero antes de la siguiente jornada y empezar en rojo es jornada
  a cero (E29). Y no vale para la reventa: E9 ya midio que pujar fuerte
  para revender pierde dinero (ROI mediano -3,1 % a x1,10).

**Limites:** no se sabe si los rivales subirian sus pujas si Pepe sube la
suya (el tablon es lo que hicieron sin Pepe fuerte). n = 105 con pelea.
El valor de «puntos que suma» es la vara del gestor, no la de este
experimento.

**Veredicto: GANA, con condicion** (pasa a «Listo para el plan»):
encender la puja fuerte SOLO para fichajes del once (nunca para la ronda
ni para reventa) y solo si el sobrecoste cabe en la cuenta de la jornada
siguiente (saldo en verde antes del cierre, la cuenta de E36).

### E36 · 12/10/2026 17:20 de Madrid · Si se ganan las pujas de mañana, ¿llega Pepe en verde a la J9?

**El caso:** hoy se ha encendido «la ronda» (compra lo que sube «con toda
la deuda») y la orden puja por dos fichajes para el once. Pujas vivas
para el reset del 13/10 07:00: **Ivan Romero 3.777.000** (por Jutgla),
**Gerard Martin 4.989.000** (por Diego Rico) y **Moi Gomez 1.101.000**
(ronda). Comprometido 9.867.000 con un saldo de 659.783. La J9 empieza el
16/10 a las 21:00 y quien empieza en rojo no puntua (E29).
**Codigo:** `lab/caja/cuentas_j9.py` (foto del ciclo de las 17:10 de hoy;
premio de la J8 a 30.000 EUR por punto, E16, con ~46 pts; ventas de la
orden al precio de hoy + 1 %, E22; Moi revendido a lo que costo).

    gana                                   saldo antes de la J9
    Romero + Gerard Martin (+ Moi)            ~ -3,42 M
    Gerard Martin (+ Moi)                     ~ -2,41 M
    Romero (+ Moi)                            ~ +1,03 M
    ninguna                                   ~ +2,04 M

**Lo que se aprende:** **Gerard Martin es el que no cabe.** Con el, aun
vendiendo a Jutgla y a Diego Rico y cobrando la J8, faltan 2,4-3,4 M. Y la
regla de la casa (E14) no deja revender a Gerard ni a Romero antes de
jugar. Para salir del rojo antes del 16/10 habria que vender a otro
titular (Exposito, Olasagasti, Unai...), y entonces el once se queda en 10
o hay que fichar otro. Los tres caminos cuestan puntos.

**Sobre la ronda (E8/E9 con su caja):** con un tope de 3 M por jugador,
pujando a precio + 1 %, la ronda gana de mediana **+0,13 M por semana** con
4 M de caja... y lo mismo con 8, 13 o 20 M: lo que la limita no es la
deuda sino que solo hay ~1,7 subastas por semana que nadie pelea. **La
deuda extra no le da nada y si le quita sitio a la caja de la J9.**

**Veredicto: AVISO URGENTE para el gestor** (pasa a «Listo para el
plan»). No es un error de codigo: es una cuenta.

### E35 · 12/10/2026 11:20 de Madrid · La J8 a medias: lo que va contra lo que predijo E23

**Que es:** la J8 aun no ha cerrado (4 equipos juegan hoy, lunes). Avance
de E23 con la foto del ciclo de las 11:10 de hoy contra la de antes del
primer partido. **Codigo:** `lab/predicciones/j8_parcial.py` (el once
guardado de cada uno, `is_starter`; titulares cuyo equipo aun no ha
jugado = «le faltan»). El juicio final, con `j8.py --juzgar` al cerrar.

    manager          once   lleva   le faltan   E23 esperaba
    Alvaro R.         11      51        1         24,9
    Pollo17           11      48        3         46,1
    Mex               11      46        2         29,0
    DiosMande         11      39        1         (sin once valido)
    Pepe              11      38        2         48,1
    Manzagool         11      37        3         36,5
    Luismi_Haz        10      30        3         58,1  (once de 10 y empezo en rojo: E31)
    Prinzipote        11      26        2         27,2

**Pepe, jugador a jugador (9 de 11 ya jugaron):** Chust 8 (esperado 2,4),
Pablo Ibanez 6 (3,4), Gulacsi 6 (4,3), Yamal 6 (11,3), Jonny 4 (2,5),
Exposito 4 (4,0), Roberto 3 (7,6), Jutgla 1 (2,9), **Diego Rico 0: no
jugo** (50 % de titularidad: el unico por debajo del 70 %, E17/E23). Los
9: 38 reales contra 39,8 esperados. Faltan Olasagasti y Unai (hoy).

**Lo que va diciendo:**
1. Para el once de Pepe, la vara acierta en el total (38 contra 39,8) y
   falla jugador a jugador (Yamal -5, Chust +6): lo normal con una
   jornada.
2. **Pollo17 va 10 por delante en la J8** con un partido mas pendiente.
   Si lo mantiene, nos pasa en la general (323 contra 320 antes de la J8).
3. **Luismi** guardo un once de 10 y, por E31, deberia contar cero.
4. La vara se equivoca mucho con los de abajo (Alvaro, Mex): con una
   jornada no se puede decir si es la vara o la suerte.
5. **Diego Rico, el unico <70 %, no jugo**: lo que E12/E16 avisaban
   (el defensa de recambio sigue pendiente).

**Veredicto: PENDIENTE** del cierre de la J8.

### E34 · 11/10/2026 17:20 de Madrid · ¿Se puede pujar por puntos antes de la rampa? Casi nunca hay a quien

**Por que:** E33 abrio la idea de pujar a las 04:50 por los que puntuan
bien la vispera, un dia antes de que la rampa (E1) los vea subir. Pero eso
solo sirve con un jugador que esta EN LA LISTA DEL COMPUTER el dia de su
partido (la puja se resuelve en el reset que trae la primera subida).
**Codigo:** `lab/precio/antes_de_la_rampa.py` (lista del Computer de un
dia contra los puntos de ese dia y el cambio de precio del reset
siguiente; fotos de los ciclos).

    lista del 09/10 (partido del viernes): 20; jugaron 2; con 5+ puntos 1
        Adrian Nino, 0,80 M, 8 pts -> +4,8 % y al dia siguiente +7,7 %
    lista del 10/10 (partidos del sabado): 20; jugaron 5; con 5+ puntos 1
        Mikautadze, 7,41 M, 5 pts -> -0,5 % (tit 40 %)

**Lo que se aprende:** la lista del Computer esta llena de jugadores que
no juegan (14-18 de 20 no jugaron ese dia). Candidatos para «pujar por
puntos antes de la rampa»: **uno por dia de partido**, y de los dos, uno
subio. La señal de E33 es buena, pero casi nunca coincide con un jugador
que se pueda comprar ese dia.

**Contra lo que hace Pepe:** la rampa (E1) ya coge a los que arrancan, con
un dia de retraso. Lo que se perderia esperando es el primer dia de subida
de ~1 jugador por dia de partido: poco.

**Veredicto: NO COMPENSA construirlo por ahora** (n=2). Se mira otra vez
con los partidos del domingo y el lunes (listas del 11 y 12/10) y, si en
la J8 entera hay mas de 4-5 casos, se reabre.

### E33 · 11/10/2026 11:20 de Madrid · E2 fuera de muestra, segunda prueba: los partidos del sabado de la J8

**Codigo:** `lab/precio/e2_fuera_de_muestra.py` con la foto del 10/10 07:18
(antes del sabado) y la del 11/10 07:19 (despues del reset de hoy).

**Los del sabado (primer reset despues de su partido):**

    jugaron, 5+ pts, NO venian subiendo     15/29 suben (52 %)
        Kounde (13 pts) +3,1 % · Gordon (13) +0,7 % · Diomande (11) +0,7 % ·
        Freeman (6) +1,2 % ... ; no suben: Bellingham, Pedri, Cucurella...
    jugaron, 4 pts o menos, no subian        2/51 (4 %)
    no jugaron (447)                         53 suben (12 %)

**Los del viernes, segundo reset:** los 4 que arrancaron ayer siguen y
suben MAS (Bryan Zaragoza +3,9 %, Adrian Nino +7,7 %, Recio +3,5 %,
Fortuno +15,0 %), y arrancan dos mas (Cabrera +0,9 %, Hartman +1,1 %): **6
de 10 en dos dias.**

**Juntando viernes y sabado:** 5+ pts y no subian, **19/39 arrancan al
dia siguiente (49 %)**; 4 o menos, **2/73 (3 %)**; no jugaron, 12 %. E2
(con la J7) decia 17-25 % contra 1 %: la señal es la misma y mas fuerte.
Y los que arrancan siguen (E1).

**Lo que abre (sin medir aun en dinero):** la rampa de Pepe (E1) compra
cuando el precio YA ha subido, un dia tarde. Los puntos del partido se
saben la noche del partido; la puja de las 04:50 se resuelve en el reset
que trae la primera subida. Pujar a las 04:50 por los del mercado del
Computer que jugaron ayer y sacaron 5+ puntos cogeria ese primer dia
(+0,2 a +11,8 %), con 1 de cada 2 que no arranca. Falta medir si sale a
cuenta en dinero (los que no arrancan, ¿cuanto pierden?) y si el mercado
del Computer saca jugadores asi el dia despues de su partido.

**Veredicto: E2 CONFIRMADO fuera de muestra (n=39 y 73).** La idea de
pujar por puntos antes de la subida queda PROMETEDORA, sin medir en
dinero: se mide con la J8 entera (cierra hoy-mañana).

### E32 · 10/10/2026 17:20 de Madrid · E2 fuera de muestra: el partido del viernes de la J8

**Codigo:** `lab/precio/e2_fuera_de_muestra.py`. **Por que:** E2 (28/09) vio, con una sola jornada (la J7), que los que no
venian subiendo y sacaban 4-5 puntos o mas arrancaban a subir (17-25 % en
2 dias, contra el 1 %). Era una pista, no una regla. El partido del
viernes 09/10 (el primero de la J8) es una prueba nueva que E2 no vio.
**Datos:** las fotos de los ciclos del 09/10 20:03 (antes del partido) y
del 10/10 07:18 (despues del reset): 34 jugadores con un partido mas y su
cambio de precio en el reset de hoy.

    jugaron el viernes, 5+ pts, y NO venian subiendo    4/10 suben hoy (40 %)
        Bryan Zaragoza (12 pts) +3,0 % · Adrian Nino (8) +4,8 % ·
        Recio (7) +0,9 % · Fortuno (5) +11,8 %
        no: Cabrera, Larrubia, El Hilali, Hartman, Dani Lorenzo, Dolan
    jugaron, 4 pts o menos, y no venian subiendo         0/22
    no jugaron (513)                                    63 suben (12 %), mediana -0,6 %

**Lo que se aprende:** la pista de E2 aguanta y con mas fuerza en un dia
(40 % contra 0 %), aunque con n=10. El arranque llega en el PRIMER reset
despues del partido.

**Para Pepe:** encaja con la rampa (E1): el que arranca hoy, mañana ya
cumple «subio en el ultimo cambio» y entra en la subasta; no hace falta
otra regla. Si se quisiera entrar un dia antes, la señal es «jugo y sacó
5+ puntos ayer», pero n=10 no da para tocar nada.

**Veredicto: CONFIRMA E2 (n pequeno).** Repetir con toda la J8 cuando
cierre (y el reset del 11/10 dara el segundo dia).

### E31 · 10/10/2026 11:20 de Madrid · Como empezo la J8: Luismi en rojo por 57.812 y el once cerrado

**Codigo:** `lab/carrera/arranque_j8.py` (fotos de 16 ciclos, del 09/10
20:03 al 10/10 11:09 de Madrid; `league_center` y `rival_squads`).

**1) Luismi_Haz empezo la J8 EN ROJO: -57.812.** Asi estaba en las vueltas
de las 20:03, 20:09, 21:10 y siguientes hasta el reset; despues del reset
de hoy, -1.157.813. Por la regla comprobada en E29 (Luismi perdio asi la
J6 entera), **su J8 deberia contar cero**. Su once era el mas fuerte de
la liga (58 pts esperados, E23). Se sabra al cerrar la J8.

**2) Comprobacion de E27 (¿se cierra el once al empezar la jornada?):** con
la foto refrescada de las 07:18 de hoy, el ultimo guardado de cada uno es
anterior a las 21:00: Pollo17 09/10 20:06, Luismi 09/10 19:59, Pepe 02/10
07:17, el resto de dias anteriores. **Nadie guardo despues del primer
partido (8 de 8).** Encaja con que la liga lo bloquea, pero no lo prueba
(no se ve a nadie intentandolo). Falta una prueba negativa: que en la J9
el motor del once de Pepe intente guardar despues de las 21:00 y Biwenger
lo rechace (o no).

**3) Encontrado de paso:** `rival_squads[].lineup_date` venia CONGELADO
desde el 18/09 (la fecha de la J7) en todas las fotos hasta el reset del
10/10 07:18; los jugadores de cada plantilla si estaban al dia. Quien use
esa fecha para algo (la hora del once de un rival) estaba leyendo la de
la J7.

**Veredicto:** (1) a confirmar con el cierre de la J8; (2) E27 sigue
PENDIENTE de una prueba negativa; (3) aviso para el gestor, sin nada que
construir.

### E30 · 09/10/2026 17:20 de Madrid · El dia de la J8 en directo: E24 y E29 contra lo que ha pasado

**Que es:** no es una medicion nueva; es contrastar dos experimentos con
lo que ha pasado hoy. Datos: el tablon de hoy y el saldo de los 8 en las
fotos de 16 ciclos (08/10 22:10 a 09/10 14:11 de Madrid).

**1) El saldo antes de la J8 (E29):**

    hora (Madrid)    Luismi_Haz    Pollo17      DiosMande
    08/10 22:10      -6.350.412    -3.135.349   -9.510.925
    08/10 23:10      -6.350.412    -3.135.349      +95.475
    09/10 04:49      -2.742.812    -3.135.349      +95.475   (Luismi vende a Juan Iglesias, 3.607.600)
    09/10 10:09      -2.742.812      +101.851      +95.475   (Pollo17 vende a Deossa, 3.237.200)
    09/10 12:10      -2.742.812    +9.242.751      +95.475   (Pollo17 vende a Valverde, 9.140.900)
    09/10 14:11      -2.742.812    +9.242.751      +95.475

A las 14:11, Luismi sigue en rojo. Si llega asi a las 21:00, su J8 es
cero (como la J6). Se vera al juzgar E23.

**2) El lesionado que vende Pollo17 (E24):** Valverde, lesionado en el
derbi del 21/09 (10,88 M), lo vende hoy, 18 dias despues, por 9.140.900;
su precio de hoy, 8,66 M (-20 % en 18 dias, ~1,1 % al dia, dentro de lo
que midio E24). Venderlo el dia de la lesion habria dado ~11 M: **esperar
le ha costado ~1,9 M.** Es la cuenta de la llave de Yamal en un caso real.

**Lo nuevo:** poco. Las dos mediciones se cumplen en vivo; Pollo17 tiene
ahora +9,2 M de caja para la semana que viene (puja maxima mayor que la
nuestra para los objetivos que salgan).

**Veredicto: CONFIRMA E24 y E29**, sin nada nuevo que llevar al plan.

### E29 · 09/10/2026 11:20 de Madrid · ¿Quien empieza la J8 en rojo? (la regla de la liga, comprobada)

**Por que:** la J8 empieza hoy a las 21:00. Si un manager la empieza con
saldo negativo, no puntua. **Codigo:** `lab/carrera/en_rojo.py`: suma los
puntos de cada jornada del tablon (`roundFinished`) y la compara con la
clasificacion de la foto del ciclo de las 11:10 de hoy.

**La regla, comprobada:**
- **La J1 no cuenta para nadie** (`splitRound: ignoreFirst` en el
  tablon): para los 8, clasificacion = suma del tablon - J1, exacto.
- **Luismi_Haz perdio entera la J6** (64 pts): 380 - 29 (J1) - 64 = 287,
  su clasificacion. Es la unica jornada «sin premio» del tablon.

**Saldo hoy a las 11:10:**

    Pepe          +409.783      Pollo17       +101.851
    Luismi_Haz  -2.742.812      DiosMande      +95.475
    resto en verde (Prinzipote +5,2 M, Alvaro R. +15,1 M...)

**Lo que se aprende:** Pollo17 (-8,8 M el 07/10) y DiosMande (-9,8 M) ya
han salido del rojo. **Luismi sigue en -2,74 M** a 10 horas del primer
partido. Si no vende antes, su J8 cuenta cero: su once era el mas fuerte
de la liga (58 pts esperados, E23). Para Pepe no hay nada que hacer
(estamos en verde); para la carrera es la noticia del dia, y la
prediccion de E23 para Luismi se juzgara sabiendo esto.

**Contra lo que hace Pepe:** la regla de la casa (nunca empezar una
jornada en rojo; el plazo de las 15:00) es la buena: lo medido es que
cuesta la jornada entera, ~45-60 puntos.

**Veredicto: SE AGUANTA** (la regla esta comprobada con el tablon; lo de
Luismi se vera esta noche).

### E28 · 08/10/2026 22:35 de Madrid · ¿Como hacen dinero Pollo17 y Luismi?

**Por que:** patrimonio de hoy Pollo17 100,1 M, Luismi_Haz 92,6 M, Pepe
56,3 M; los tres salieron de 23,3 M y cobran premios parecidos. E1 ya
dijo QUE compran (lo que sube); aqui se mide DE DONDE sale cada millon y
que se puede copiar con 0,4 M de caja y 11 fichas. **Codigo:**
`lab/rivales/como_hacen_dinero.py` (`python3 -I ... rival_intelligence.json`).
**Datos:** `rival_intelligence.json` del 08/10 20:10 UTC (movimientos de
los 8 desde el 10/08, plantilla de hoy con precio, coste y
`price_increment`, saldo reconstruido; la caja de Pepe cuadra al euro con
la real), el tablon (jornadas y racha) y `price_history.json`. Las
reemisiones del tablon se quitan con la misma reja de 1 h que la caja:
ventas y compras cuadran al euro con `sales_total`/`purchases_total` de
los tres, y el coste FIFO de la plantilla con `acquisition_price`.

**1) De donde sale el patrimonio** (ganancia = patrimonio - 23,3 M;
«regalo» = la plantilla de salida, gratis: lo que se cobro al venderla +
lo que vale hoy lo que queda):

                 ganancia  viajes cerrados  latente hoy  premios  regalo
    Pollo17       +76,8        +21,1           +11,4      +11,5    +32,9
    Luismi_Haz    +69,3        +15,8           +14,9       +9,6    +29,0
    Pepe          +33,0         -2,8            -1,3      +11,4    +25,7
    (premios = jornadas + racha: Pollo 9,70 + 1,75; Luismi 8,86 + 0,75;
     Pepe 9,89 + 1,50. Resto sin explicar: 0 en los tres.)

**La brecha con Pollo17 (43,8 M): 23,9 M de viajes (55 %), 12,7 M de
latente (29 %), 7,2 M de regalo (16 %), premios 0.** Con Luismi (36,3
M): 18,7 viajes, 16,1 latente, 3,3 regalo y -1,8 de premios (la J6
anulada). Del regalo, unos 4,5 M de Pollo no son suerte sino guardar a
los de salida mientras subian (Paredes 0,81 -> 3,02 M, Iker Munoz 0,48
-> 2,15, Larrubia 6,39 -> 6,68; precio del 16/08 contra la venta). El
resto es la plantilla que toco. **Los premios no explican nada: el
la brecha sale de la compraventa (cerrada + latente) en un 84-96 %.**

**2) Su compraventa (viajes cerrados, FIFO por jugador):**

                              Pollo17      Luismi_Haz     Pepe
    viajes / verdes            66 / 57      53 / 36      42 / 23
    P&L total                  +21,05 M     +15,83 M     -2,84 M
    P&L por semana (8,4 sem)    +2,5 M       +1,9 M      -0,34 M
    dias (mediana)               6,1          8,3          5,8
    P&L / ROI mediano        +0,15 M/+4,7 % +0,06/+4,3 %  0,00/+0,5 %
    compra mediana              3,24 M       2,13 M       1,21 M
    subia el dia antes          43/51        28/37        8/39
      P&L si subia / si no   +17,3 / +1,3  +11,1 / +0,8  +0,3 / -4,2
    prima compra (mediana)      +1,9 %       +2,2 %       +0,3 %
    prima venta al Computer     +3,4 %       +2,8 %       +2,3 %
    venta en dia de bajada      38/59        29/48        17/40
      ...en la PRIMERA bajada   16/59        10/48         4/40
    viajes > 21 dias          6: +7,4 M    5: +6,2 M    5: +0,8 M

Por tramo de precio de compra: Pollo gana en todos (<=1 M: 6 viajes
+6,0 M, todos verdes; 1-3 M: 25, +8,5 M, ROI med +7,9 %; 3-6 M: +2,6 M;
>6 M: +3,9 M pero ROI med +2,4 %). Luismi, lo mismo (1-3 M: 10/10
verdes, +6,4 %). **Pepe pierde justo donde ellos ganan:** 1-3 M -1,67 M
(6/19 verdes) y 3-6 M -3,31 M (0/4: los fichajes del once revendidos,
E14). Solo los <=1 M le salen (+2,14 M, 17/19). Venden casi todo al
Computer (64/66 y 50/53), en dia de bajada 2 de cada 3 veces, pero NO
esperan a la primera bajada como regla fija (16/59): venden cuando les
hace falta caja o cuando gira. **Vender en las 24 h antes de una
jornada no les cuesta:** Pollo 14 viajes, ROI med +7,2 % (13/14 verdes)
contra +4,5 % el resto; Luismi +5,9 % contra +3,9 %.

**Usuario a usuario:** pocos (7 de Pollo, 4 de Luismi), pero **el mejor
viaje de Pollo17 se lo vendio Pepe**: Javi Hernandez (regalo de salida)
a 1,25 M el 19/08, Pollo lo vendio a 3,92 M el 18/09 (+2,67 M); Castrin,
1,35 M el 24/08 -> 2,23 M (+0,88). Entre ellos: Luismi le paso a Pollo
Brugue (0,70 M el 28/08; hoy +3,45 M latentes para Pollo) y Jonathan
David (8,4 M la vispera de la J7, para tener caja; hoy +2,29 M para
Pollo).

**3) La plantilla.** Los tres salieron con 15. Pollo 11 (20/08) -> 19
(01/09) -> 20 hoy; Luismi 15 -> 20 -> 17; Pepe 13 -> 19 (15/09) -> 11.
Fuera del mejor once (vara: puntos de temporada) Pollo tiene 9 fichas
por 36,7 M (Valverde, Laporte, Fofana, Cancelo, Amatucci, Akhomach,
Deossa...): **ese «almacen» HOY no revaloriza** (-0,03 M de
`price_increment` hoy, -0,99 M de latente): es banquillo caro, no
inventario que suba. Luismi, 6 fichas por 5,9 M (+2,69 M latentes:
Hugo Gonzalez y Areso). **La revalorizacion la hacen los titulares
comprados subiendo:** Luismi Arda Guler +6,1 M, Camello +5,7, Kang-in Lee
+2,8; Pollo Brugue +3,5, Natan +2,4, Jonathan David +2,3, Luka Sucic +2,2.
Pepe: latente total -1,26 M (Roberto Fernandez -0,63).

Lo que gano cada dia la plantilla que tenia cada uno (precio de cierre
a cierre, 51 dias con precio del 17/08 al 08/10, 99-100 % de
jugador-dias con precio):

                 media/dia   por semana   ultimos 15 dias   price_increment hoy
    Pollo17      +0,72 M      +5,1 M        +0,68 M/dia        +0,41 M
    Luismi_Haz   +0,67 M      +4,7 M        +0,44 M/dia        +0,02 M
    Pepe         -0,01 M      -0,1 M        -0,02 M/dia        +0,02 M

Es el mismo dinero que el de los viajes y el latente visto dia a dia
(no se suma). Pollo rinde ~0,8 % diario sobre ~90 M; Pepe ~0 % sobre
56 M, de los que Yamal es el 45 %.

**4) La deuda.** Los dos viven en rojo entre jornadas y llegan a cero
justo al empezar:

                 dias en rojo   peor saldo            saldo al empezar jornada
    Pollo17         40/60       -20,9 M (11/09)       todas >= 0 (+0,01 a +3,8 M)
    Luismi_Haz      55/60       -21,0 M (01/10)       J6 -13,3 M; J1-ap -8,9; J2 -0,9; resto ~0
    Pepe            31/60        -9,3 M (30/09)       todas >= 0

La mecanica: en las 24 h antes de cada jornada venden lo que haga falta
(Pollo 21,5 M antes de la J5 con -20,9 M esa misma manana; Luismi 21,3
M antes de la J7, 14,9 antes de la J3). Hoy estan a -3,1 M (Pollo) y
-6,4 M (Luismi) con la J8 manana: venderan manana. **Lo que le costo a
Luismi la J6:** empezo (Real Sociedad-Celta, 03/09 19:00) a -13,3 M y
vendio al dia siguiente a las 16:29: 64 puntos anulados y 64 x 30.000 =
1,92 M sin cobrar. Sin eso iria 351 y primero. La caja de los rivales es
reconstruida (no se ve la real): las «deudas» de -0,03 a -0,06 M en
J4/J5/J7 y la de -0,9 M en la J2 no les costaron puntos, asi que el
momento exacto de la comprobacion no se sabe al minuto. La regla segura
es la nuestra: >= 0 a la hora de `roundStarted`.

**5) Que se puede copiar con 0,4 M, maximumBid 14,4 M y 11 fichas.** El
motor de ellos es capital: ~100 M de plantilla + ~20 M de linea, rotando
a lo que sube. Ese tamano no se copia (harian falta ~40 M mas). Lo que
si:

- **R1. Viajes con la linea de credito ENTRE jornadas, solo a lo que
  sube (E1) y a precio + 1 % sin pelear (E9), cerrados en las 24 h
  antes de la jornada.** Pepe tiene 14,4 M de maximumBid y llega a cada
  jornada con >= 0: hay hueco para 8-10 M de viajes de lunes a jueves.
  Que se cierren antes de la jornada no cuesta (ellos sacan +5,9/+7,2 %
  en esas ventas). Esperado: E9 midio +0,12-0,18 M/semana con 4-8 M solo
  en lo que nadie pelea; con ~10 M y ROI med +4 %, **+0,15-0,3
  M/semana**. Tope por viaje 3 M (los de 1-3 M son su mejor tramo: +6-8 %
  de ROI mediano, y los >6 M dan +1-2 %).
- **R2. Los fichajes del once, entre los que SUBEN.** A igual puntos
  esperados (E25/E16), elegir el que subio en el ultimo cambio: Luismi
  gana +12 M latentes en titulares comprados asi; Pepe pierde 1,26 M.
  Con un fichaje de ~3 M por semana, +3,5 % contra -0,4 % (E1) = **~+0,1
  M/semana**, y sin vender titulares en dias (E14: -3,3 M).
- **R3. A un manager no se le vende un jugador que sube; al Computer.**
  Pollo hizo +3,55 M con dos que le vendio Pepe (Javi Hernandez y
  Castrin). Una oferta de un rival se acepta solo si el precio no sube
  y paga mas que el Computer. Evita perdidas, no suma por semana.
- **R4 (guardia, no dinero). Saldo >= 0 antes de `roundStarted`**, con
  la venta hecha la vispera o la manana de la jornada, nunca «a ultima
  hora»: Luismi perdio 64 puntos y 1,92 M por vender un dia tarde.

**Lo que NO copiar:** (a) la plantilla de 17-20 (el almacen de Pollo son
36,7 M parados, -0,99 M latentes); (b) pelear las pujas de lo que sube
(E9: x1,10 da ROI mediano -3,1 %); (c) llegar en rojo a una jornada;
(d) viajes de > 6 M (ROI med +1-2 %: no compensan el riesgo con 0,4 M
de caja); (e) vender fichajes del once a los dias (E14).

**Lo que se aprende:**
1. **La brecha es compraventa, no premios:** +32,5 M de Pollo en viajes
   + latente (Luismi +30,7) contra -4,1 M de Pepe. Los premios estan empatados.
2. **El 70-82 % de su P&L de viajes viene de comprar lo que subia el dia
   antes** (Pollo +17,3 de 21,1; Luismi +11,1 de 15,8; el resto, sobre
   todo viajes sin precio del dia de compra). E1 se confirma
   con 30 dias mas de datos.
3. **La deuda es su palanca:** -15 a -21 M a mitad de semana y >= 0 al
   empezar la jornada, vendiendo en las ultimas 24 h sin perder ROI.
4. **Con nuestro capital la brecha no se cierra:** R1 + R2 dan ~+0,25-0,4
   M/semana contra ~+4-5 M/semana de revalorizacion de Pollo. Sirven para
   dejar de perder (Pepe va -0,34 M/semana en viajes) y para que el
   dinero que entre vaya a puntos; la liga se gana en el once (E25).

**Limites:** `price_history` empieza el 16/08 (lo vendido antes se
valora a precio de venta; el regalo de salida no se puede valorar el
10/08); dias con medio catalogo (07-08/09, 22/09, 24-25/09): esos dias
caen de las cuentas de precio; las fotos de plantillas de los rivales
tienen hueco del 17/08 al 10/09 y no se usan: la plantilla en el tiempo
sale del tablon (cuadra con el recuento de hoy). La caja de los rivales
es reconstruida y no auditable (la de Pepe si). El «once» del almacen es
por puntos de temporada, no el que alinearon. 8,4 semanas; los € por
semana de R1/R2 son estimaciones apoyadas en E1/E9, no medidas con la
restriccion de jornada simulada.

**Veredicto: SE AGUANTA.** La brecha de patrimonio es compraventa de lo
que sube (55 %) + titulares comprados subiendo (29 %) + regalo (16 %).
R1-R4 pasan a «Listo para el plan» si el gestor las quiere; R4 y R3 son
guardias baratas, R1 necesita la linea de credito con cierre forzado la
vispera de cada jornada.

### E27 · 08/10/2026 17:20 de Madrid · El once de la J8 se congela en UNA sola vuelta: ¿cuanto riesgo hay?

**Por que:** sin el once congelado no hay nota de la jornada (la J7 se
perdio asi: no hubo vuelta en la ventana). `el_once_que_jugo.py` solo
anota desde el `safety_deadline` (90 min antes del primer partido) hasta
el primer partido. En la J8 (primer partido el 09/10 a las 21:00) eso es
de 19:30 a 21:00: **solo la vuelta de las 20:07 cae dentro.**
**Codigo:** `lab/infra/latido.py --horas` (historial de bordalas-live.yml).

    hora        13/09 a 07/10 (25 dias)                desde el 25/09 (13 dias)
    19h  sin vuelta verde 4/25 (18, 22, 23, 24/09)      0/13
    20h  sin vuelta verde 3/25 (18, 23, 24/09)          0/13
    21h  sin vuelta verde 3/25 (18, 23, 24/09)          0/13

**Lo que se aprende:** desde el 25/09 la vuelta de las 20h no ha fallado
nunca; en la semana mala (18-24/09) falto 3 de 7 dias, y el 18/09 era
precisamente el dia de la J7. Riesgo pequeno pero de todo o nada: si la
de las 20:07 no llega manana, la J8 tambien se queda sin nota.

**Una salida que hay que comprobar antes:** la liga tiene
`lineupRoundChanges: 0` (tablon): cuando empieza la jornada ya no se
puede cambiar el once. Si eso es asi, el once que se lee DESPUES de las
21:00 es exactamente el que juega, y cualquier vuelta de la jornada
(21:07, 22:07... hasta el lunes) serviria para anotarlo: decenas de
oportunidades en vez de una. **Comprobacion para manana (gestor o
laboratorio):** en las fotos de las vueltas de despues de las 21:00,
`rival_squads[].lineup_date` de los 8 managers no debe ser posterior a
las 21:00. Si se cumple, se puede dejar anotar despues del primer
partido con la etiqueta «leido con el once ya cerrado por la liga».

**Veredicto: PENDIENTE de la comprobacion de manana.** Nada que tocar
antes de la J8 (la vuelta de las 20:07 lleva 13 de 13).

### E26 · 08/10/2026 11:20 de Madrid · Revision de la lista de objetivos de E25 contra la foto de hoy

**Por que:** E25 (08/10, otra sesion del laboratorio) dejo una lista de
fichajes que el gestor ya ha pasado al puesto de mando («cada rafaga mira
el mercado de la manana contra esta lista»). Una lista vale lo que el dia
en que se hizo. **Codigo:** `lab/objetivos/revisa.py` (foto del ciclo de
las 11:10 del 08/10 + noticias de FF). Reglas: estado no ok = fuera (E6,
E24); precio bajando = esperar si es reventa (E1); vara = puntos totales
(E7/E17).

    Miguel Roman   FUERA: injured. FF 29/09: «se lesiona la rodilla y podria
                   pasar por quirofano». Precio 4,03 -> 2,67 M en 9 dias
                   (-34 %, lo que dice E24). Era el primero de la lista.
    Koski          FUERA: injured; hoy -190.000.
    Nacho Perez    ok, 15 pts en 5, 0,82 M, bajando
    Riedel         ok, 15 pts en 6, 0,93 M, bajando
    Galilea        ok, 15 pts en 6, 0,95 M, bajando (FF 28/09: vuelve al grupo)
    Raphinha       ok, 113 pts en 7 (Yamal 88 en 7), 24,41 M, subiendo.
                   La cuenta de E25 (+3,5 por jornada) aguanta: no es una
                   media de pocos partidos. Ojo: FF 29/09, sustituido con
                   Brasil por molestias; hoy ok.
    Rafita         ok, 30 pts en 7, 2,64 M, subiendo; es de un rival
                   (Luismi): a precio o algo mas (E18).

**Lo que se aprende:** dos de los siete objetivos (el primero incluido)
estan lesionados hoy. Los tres defensas baratos suman 15 puntos en 5-6
partidos (2,5-3 por partido): mejoran a Diego Rico (6 en 2) pero poco, y
su precio baja. Para el once mandan los puntos (regla del dueno), no la
rampa, pero un fichaje para el once que baja tambien pierde caja (E14).

**Veredicto:** la lista necesita pasar por el estado del dia antes de
cada puja. Pasa a «Listo para el plan».

### E25 · 08/10/2026 08:58 de Madrid · Los equipazos: ¿aguanta el liderato contra Pollo17 y Luismi_Haz las 5 jornadas que vienen?

(Pedido como «E13»; el numero ya estaba usado y va como E25.)

**Por que:** tras la J7 vamos primeros con 323, Pollo17 320, Luismi_Haz
287, con la mitad de patrimonio que ellos (56 M y 11 fichas contra ~100 M
y 17-20). **Codigo:** `lab/rivales/los_equipazos.py`. **Datos:** tablon
(`roundFinished` y compraventas hasta el 08/10 05:04 UTC), la foto del
18/09 (plantillas de los 8 y catalogo de 546), `puntos_por_jornada.jsonl`
(acumulado de cada jugador a la J7), precios de hoy y el estado del
ultimo ciclo archivado (29/09). Plantilla de hoy = foto del 18/09 + el
tablon: sale Pepe 11 y Pollo17 20 (cuadran); **Luismi_Haz 17, no 20**
(vendio Aitor Fernandez, Recio y Lemar el 07-08/10). Vara: puntos de
temporada / 7 («pts/jornada»: el que no jugo cuenta 0, como en el once).

**1) Por jornada** (la parte 2 de una aplazada trae la jornada entera;
cuadra con la clasificacion):

                J1  J2  J3  J4  J5  J6  J7   total  media  desv
    Pepe        41  31  61  53  61  29  47    323   46,1   12,2
    Pollo17     31  58  57  52  55  17  50    320   45,7   14,5
    Luismi_Haz  28  55  53  44  46   0  61    287   41,0   19,4
    (Luismi con los 64 que se le anularon en la J6 por saldo negativo:
     351, media 50,1, desv 11,3)

Ganamos a Pollo17 5 de 7 jornadas y a Luismi 4 de 7. Somos el MAS
REGULAR de los dos de arriba con Pollo17, pero **Luismi es el que mas
puntua de verdad**: ultimas 3 jornadas, Luismi 171, Pepe 137, Pollo17 122.
Los 36 puntos que nos saca de menos son, casi enteros, la J6 anulada.

**2) El mejor once de HOY (pts/jornada; entre parentesis, pts/partido):**

    Pepe        52,4 (58,9)  3-4-3   el mejor: Yamal 12,6 = 24 % del once
    Pollo17     58,1 (73,8)  3-4-3   el mejor: Moleiro 6,9 = 12 %
    Luismi_Haz  69,9 (74,5)  4-4-2   el mejor: Camello 10,7 = 15 %

    media por plaza   POR    DEF    MED    DEL
    Pepe              2,3    2,3    4,5    8,4
    Pollo17           4,3    5,3    5,7    5,1
    Luismi_Haz        7,0    4,5    6,6    9,3

Donde nos ganan: **en la defensa** (Jonny 3,0, Chust 3,0, Diego Rico 0,9
con 2 partidos de 7, contra Natan 6,0 / De la Fuente 5,4 / Grimaldo 4,4 de
Pollo y Juan Iglesias 5,6 de Luismi), **en la porteria** (Gulacsi 2,3: solo
3 partidos; por partido jugado 5,3, la duda es si ya es fijo) y en el
medio contra Luismi (Arda Guler 7,9, Pedri 7,1, Kang-in Lee 7,0). Solo
ganamos arriba (Yamal + Roberto Fernandez). Con la vara de E23 (que mete
la titularidad FF) la foto es menos dura: Pepe 48,1, Pollo17 46,1, Luismi
58,1 (sus onces del 07/10 siguen siendo suyos salvo Mayol y Lemar).

**Concentracion:** Yamal es el 24 % del once (Moleiro el 12 % del de
Pollo, Camello el 15 % del de Luismi). Si a Pollo17 le falta su mejor,
su once baja 2,1; a Luismi, 7,4; **a Pepe no le queda once valido**: con
3 delanteros y 4 medios no hay formacion de 10 de campo sin Yamal. Lo
mismo con cualquier baja que se sepa: una plaza vacia (E12).

**3) Banquillo:** Pollo17 tiene 9 suplentes (Valera 4,7, Valverde 4,6,
Cancelo 4,0...), Luismi 6 (Hugo Gonzalez 3,3 el mejor), Pepe 0. Contar
las plazas que no puntuaron jornada a jornada **no se puede con lo que hay
en git**: el unico once de los rivales es el de la foto del 18/09 (10
titulares guardados el 15/09) y no es el que jugaron la J7 (sus titulares
suman 31 y 45 contra los 50 y 61 del tablon). Queda como hueco de datos.

**4) Fichajes con ~0,4 M de caja** (libres entre los 8, 5+ partidos,
estado ok o duda el 29/09; Aubameyang fuera, operado). Permuta 1 x 1:
vender al Computer (x 1,024, E1) y comprar uno del mismo puesto:

    Unai Lopez 4,1  -> Miguel Roman 6,3 (2,67 M)    +2,1/j  +11 en 5 j
    Yamal 12,6      -> Raphinha 16,1 (24,41 M)      +3,5/j  +18 en 5 j
    Jonny 3,0       -> Koski 4,4 (2,36 M)           +1,4/j   +7 en 5 j
    Diego Rico 0,9  -> Nacho Perez / Riedel / Galilea 2,1 (0,8-0,95 M)  +1,2/j  +6
    Suplente DEF que juega: Balliu 0,63 M, Jesus Vazquez 0,69 M (1,7-1,9/j)

Yamal -> Raphinha deja ~1,6 M de sobra (26,0 de venta contra 24,4): da
para el defensa suplente. Portero: ninguno mejor cabe en lo que da
Gulacsi (2,7 M); Remiro 4,0 M y Leo Roman 4,1 M (+2,6-2,9/j) no llegan.

**Lo que se aprende:**
1. **El liderato es de 3 puntos sobre Pollo17 y es regularidad, no
   once**: por la vara, el once de Pollo17 rinde lo mismo o algo mas que
   el nuestro. Es una carrera a cara o cruz jornada a jornada.
2. **El peligro es Luismi**: su once es el mejor (+10 a +17 por jornada
   segun la vara; E20 ya lo dijo) y ha salido del rojo. A ese ritmo
   recorta 36 puntos en 2-4 jornadas. Solo nos salva que venda titulares.
3. **Lo que mas puntos da por millon es la defensa y un medio barato**,
   no gastar en estrellas: Unai -> Miguel Roman y Diego Rico -> un defensa
   que juegue cuestan ~0 M y suman ~3 por jornada. Yamal -> Raphinha es
   el unico salto grande que cabe sin dinero (+3,5/j) y ademas paga un
   suplente; no quita la concentracion (Raphinha seria el 30 %).

**Contra lo que hace Pepe:** confirma E12/E16/E20 (lo primero, un
defensa y banquillo). Las 3 jugadas, por orden: (1) Unai Lopez ->
Miguel Roman en cuanto salga en el mercado del Computer; (2) Diego Rico
-> un defensa de <1 M que juegue (o Jonny -> Koski); (3) si Raphinha sale
en el mercado: pujar PRIMERO y vender Yamal al Computer solo si se gana
(la venta es al momento; el saldo solo tiene que estar en verde al
empezar la jornada), y con los ~1,6 M que sobran, un defensa suplente.
Las tres juntas: ~+6,8 por jornada, ~+34 en 5 jornadas por la vara.

**Limites:** 7 jornadas (n pequeno); pts/7 castiga al que llego tarde
(Gulacsi 3 partidos, Diego Rico 2) y la vara sobreestima (E20: los de
arriba sacan el 81-104 % de lo esperado). Estados de hace 9 dias. Que un
jugador salga en el mercado del Computer es azar y la puja la puede
pelear Pollo17 (E11); los precios de compra son el precio de hoy, no lo
que se pagaria. Sin onces jornada a jornada de los rivales.

**Veredicto: SE AGUANTA como lectura de la carrera** (el liderato es
fragil: Luismi es favorito por once; Pollo17, a la par). Las permutas
pasan a «Listo para el plan» si el gestor las quiere: no tocan caja.

### E24 · 07/10/2026 17:20 de Madrid · ¿Cuanto cae el precio de un jugador caro lesionado? (la llave de Yamal)

**El caso (07/10):** decision del CEO: si Yamal se lesiona 4 semanas o
mas, se vende al Computer el primer dia, «porque su precio cae cada dia
sin puntuar» (llave `yamal_por_lesion`, cab3a81). **Codigo:**
`lab/lesiones/precio_lesionado.py`. Primera noticia de BAJA fuerte de FF
(lesion, rotura, operado, parte medico, semanas, se pierde) de jugadores
de 3 M o mas, y su precio en los dias siguientes (20 casos, 17/08 a 30/09).

    caso (precio)                +1er cambio   +7 d    +14 d   +28 d
    Aubameyang (14,3 M, operado)     -6 %      -25 %     -      -
    Valverde (10,9 M)                -0 %      -11 %   -18 %    -
    Andres Martin (5,8 M)            -4 %      -24 %   -34 %  -45 %
    Audero (5,5 M)                   -4 %      -26 %   -38 %  -52 %
    Borja Iglesias (5,0 M, rotura)   -4 %      -21 %   -26 %  -34 %
    Batalla (4,0 M)                  -2 %      -32 %   -43 %  -57 %
    Aspas (3,3 M)                    -7 %      -27 %   -34 %  (-40 % a 21 d)
    ...y 6 mas parecidos.
    Falsas alarmas (calambres, «sin lesion», molestias leves): Exposito,
    Alfonso Herrero, Juan Iglesias, De la Fuente (mal leido): suben o igual.
    Mbappe (25,6 M, «no descartado»): -1 % en 7 dias.

**Lo que se aprende:**
1. **La premisa del CEO se aguanta:** una lesion de verdad le quita al
   precio ~1,5-2 % al dia: -10 a -32 % en una semana, -21 a -57 % en
   cuatro. Con Yamal (24,5 M), cuatro semanas lesionado serian **5 a 14 M
   menos**, ademas de los puntos.
2. **Lo caro del primer dia es poco** (0 a -7 % en el primer cambio): lo
   que cae es la semana. Vender el mismo dia de la noticia, con la oferta
   del Computer que ya tiene (Yamal esta en el escaparate), evita casi
   todo. Esperar a «confirmar» una semana cuesta un 10-30 %.
3. **Una de cada cinco «bajas» es una falsa alarma** (calambres, «sin
   lesion»). Por eso la llave pide una baja estimada de 28 dias o mas, y
   eso esta bien: con Mbappe (baja corta) el precio casi no se movio.

**Contra lo que hace Pepe:** la regla nueva es la buena. Matiz para el
gestor: «el primer dia» = la primera vuelta con la baja estimada >= 28
dias, sin esperar al siguiente reset; y la oferta del Computer ya esta
ahi porque Yamal sigue en el escaparate (no quitarlo de ahi).

**Limites:** 20 casos, casi todos de 3-6 M; de mas de 10 M solo tres
(Mbappe, Aubameyang, Valverde). Sin datos de como se recupera el precio
al volver (no ha dado tiempo).

**Veredicto: SE AGUANTA** (respalda la decision del CEO del 07/10).

### E23 · 07/10/2026 11:20 de Madrid · Predicciones para la J8, apuntadas ANTES de jugarla

**Por que:** las varas del laboratorio para los puntos (E7, E16, E17, E20)
se han medido con una sola jornada, la J7. La J8 empieza el 09/10 a las
21:00: se apuntan HOY sus predicciones, para juzgarlas fuera de muestra
cuando cierre. **Codigo:** `lab/predicciones/j8.py` (`--apuntar` con la
foto del ciclo de las 11:09 del 07/10; `--juzgar` cuando la J8 este en
`puntos_por_jornada.jsonl` y en el tablon). Lo apuntado:
`lab/predicciones/j8.json`.

**Puntos esperados del mejor once (puntos por partido x titularidad FF):**

    Luismi_Haz 58,1 · Pepe 48,1 · Pollo17 46,1 · Manzagool 36,5 · Mex 29,0
    Prinzipote 27,2 · Alvaro R. 24,9 · DiosMande: sin once valido

**Pepe, jugador a jugador:** Yamal 11,3 · Roberto 7,6 · Olasagasti 5,0 ·
Gulacsi 4,3 · Exposito 4,0 · Pablo Ibanez 3,4 · Unai 3,3 · Jutgla 2,9 ·
Jonny 2,5 · Chust 2,4 · Diego Rico 1,5. Por debajo del 70 % de
titularidad (E17: juega menos de 9 de cada 10): solo **Diego Rico (50 %)**.

**Lo que la foto de hoy ya deja ver:**
- **DiosMande no puede alinear un once valido con jugadores sanos**: 3
  defensas, 3 medios y 4 delanteros sanos, y dos en duda; ninguna
  formacion de Biwenger cabe (todas piden 3+ defensas y 3+ medios con 4
  delanteros solo en 3-3-4, que no existe). Jugara con alguien en duda o
  con 10.
- **Pollo17 esta en -8,78 M** y Luismi en -7,0 M (el 04/10 estaba en
  -17 M): los dos tienen que estar en verde antes del primer partido. Si
  Pollo17 vende titulares, su once baja de 46,1 (E18: vendera al
  Computer, no barato a nosotros).

**Como se juzgara:** el orden real de la J8 contra el esperado; los
puntos de cada once contra lo esperado (en la J7 los cuatro primeros
sacaron entre el 81 % y el 104 %); y los de cada jugador de Pepe.

**Veredicto: PENDIENTE (se juzga tras la J8, hacia el 12-13/10).**

### E22 · 06/10/2026 17:20 de Madrid · Agenda 4: ¿aceptar la oferta del Computer hoy o esperar a la siguiente?

**Por que:** en 91 vueltas de produccion hubo ~800 lecturas de ofertas
del Computer por nuestros jugadores y UNA de un manager (Luismi por Pablo
Duran, 1,31 M; el Computer lo compro el 30/09 por 1,32 M). «Aceptar o
no» es, en la practica, la oferta del Computer de hoy o la siguiente.
E3 ya dijo que una reventa se vende el dia que su precio baja; aqui va el
resto de ventas (las de la orden para hacer caja, por ejemplo).
**Codigo:** `lab/ofertas/computer.py` (fotos de los ciclos del 27/09 al
05/10; los artefactos caducan a los 2 dias).

**Resultado: 19 jugadores, 51 ofertas distintas.** Prima sobre el precio
del dia: p10 -2,8 %, mediana +0,2 %, p90 +4,2 %. Cada oferta dura ~1,5
dias (38 h de mediana al verla) y luego llega otra.

    la de hoy...           n    la siguiente (mediana)   mejora
    baja (< 0 %)          19          +0,6 %             15/19
    normal (0-3 %)         6          +0,2 %              2/6
    alta (> 3 %)           7          -2,5 %              0/7

Son tiradas independientes alrededor del precio: tras una mala viene,
casi siempre, una mejor; tras una buena, una peor.

**La regla que sale (para ventas que NO son reventa):**
- Oferta de mas del 3 % sobre el precio: **aceptar**; la siguiente sera
  peor (7 de 7).
- Oferta por debajo del precio y el precio del jugador NO esta bajando:
  **esperar a la siguiente** (+2 puntos de prima de mediana, en ~1,5
  dias).
- Si el precio esta bajando: aceptar (E3: cada dia de espera cuesta un
  1,8 %, mas que lo que da la tirada nueva).
- Si hay plazo (la solvencia antes de una jornada), mandan las horas que
  quedan, no la prima.

**Contra lo que hace Pepe:** su motor de ofertas decide «KEEP_OFFER» o
reroll con su propia cuenta y la orden vende con suelo; no se ha medido
aqui si sigue esta regla (doctrina 84: mirarlo antes de construir).

**Limites:** n pequeno (32 pares de ofertas seguidas, 9 dias, casi todo
de la plantilla de 11 que no se queria vender); la prima se mide contra
el precio de cada dia.

**Veredicto: PROMETEDOR.** Pasa a «Listo para el plan» como regla de
venta para la orden y para el motor de ofertas, con n pequeno dicho.

### E21 · 06/10/2026 11:20 de Madrid · ¿Se salta cron-job.org las vueltas del reset? (falsa alarma)

**El caso (06/10 06:30, chat del dueno):** «cron-job.org se salto OTRA VEZ
las vueltas de las 05:07 y 06:07 y disparo dos casi seguidas a las 04:45
y 04:50». Se creo una red (rutina trig_01AVXpLEPRYKWuEDiEquuCdR, 06:22
cada dia: si no hubo ciclo en 30 min, lo lanza) y se pidio al dueno que
mirara cron-job.org. **Codigo:** `lab/infra/latido.py` (historial de
ejecuciones de bordalas-live.yml por la API de GitHub; 800 vueltas).

**1) Por hora de Madrid, dias sin ninguna vuelta (10/09 a 05/10, 26 dias):**
las 05h, 26 de 26; las 06h, 25 de 26. Las 04h, en cambio, con dos vueltas
23 de 26 dias (04:45 y 04:50). **No es un fallo: es el diseno.**
`config/disparos.json` declara el latido a las :07 de todas las horas
MENOS las 4, 5, 6 y 7 («es la ventana del reset del mercado»), y tres
disparos puntuales: 04:45 (pujar), 04:50 (renovar) y 07:15 (leer el reset
y cobrar). `src/analysis/zona_de_silencio.py` explica por que: el reset
de Biwenger cae entre las 05:00 y las 07:00, y una vuelta que escriba ahi
lo hace con el mercado sin resetear (lo que costo la primera ventana de
septiembre). Una vuelta fuera de esas horas dentro de la franja es
«descolocada» y no escribe.

**2) Contra lo declarado (13/09 a 05/10, 23 disparos al dia, gracia 12
min):** no llegaron 56 de 529 (10,6 %): 54 del latido y 2 de la ventana;
el de las 07:15, todos. **Pero los fallos son de una semana:** 18, 19, 22,
23 y 24/09 (de 4 a 14 vueltas ese dia). **Desde el 25/09: 20 de 20 del
latido todos los dias**, y la ventana (04:45/04:50) y las 07:15, todas.

**Lo que se aprende:** el latido va bien desde hace 11 dias. La red de
las 06:22 dispara vueltas DENTRO de la franja de silencio: no escriben
(salen descolocadas), pero gastan las mismas peticiones a Biwenger que
una vuelta normal (ya hubo un 429) y no aportan nada. Y el aviso al dueno
para que mire cron-job.org no hace falta.

**Veredicto: FALSA ALARMA, con datos.** Para el gestor (Listo para el
plan): quitar la rutina de las 06:22 y corregir la nota del 06/10.

### E20 · 05/10/2026 17:25 de Madrid · La carrera: ¿que once saca mas puntos con la plantilla de hoy?

**Por que:** lo que decide la liga son los puntos por jornada, no el
dinero. Con las plantillas de los 8 (foto del ciclo de las 17:09 del
05/10, `rival_squads` + `todaLaLiga`) se calcula el mejor once de cada uno
con la vara de E16/E17 (puntos por partido x titularidad FF, estado ok).
**Codigo:** `lab/carrera/proyeccion.py` (la foto se pasa por argumento:
los artefactos caducan a los 2 dias).

    manager        puntos  fichas  once esperado  banquillo (3 mejores)  real por jornada (J1-J7)
    Luismi_Haz       287     19        58,8              8,6                 47,5
    Pepe             323     11        48,1              0,0                 44,0
    Pollo17          320     20        46,2             10,9                 42,6
    DiosMande        281     13        37,4              2,9                 39,0
    Manzagool        253     16        37,2              3,2                 32,9
    Mex              246     16        28,2              4,6                 36,0
    Prinzipote       258     17        27,9              4,3                 34,0
    Alvaro R.        198     14         (sin portero sano: no sale once)     22,7

(La vara sobreestima algo: los 4 primeros sacaron de verdad entre el 81 %
y el 104 % de lo esperado, con plantillas que no eran las de hoy. El orden
coincide con el real en los cuatro de arriba.)

**Lo que se aprende:**
1. **El once de Pepe es el segundo mejor de la liga** y va por delante del
   de Pollo17 (48,1 contra 46,2). La ventaja de Pollo17 es el dinero y el
   banquillo (10,9 contra 0), no el once.
2. **El rival en puntos es Luismi_Haz**, no Pollo17: su once es el mas
   fuerte (58,8; Camello, Budimir, David Soria, Pedri, Arda Guler) y ha
   sacado 47,5 por jornada, el que mas. Esta 36 puntos por detras, pero
   puede recortar ~10 por jornada. Esta en -17 M y tiene que vender: si
   vende a Rafita, Tenaglia y Areso (los que tiene a la venta), su once
   solo baja a 56,8. Para cuadrar 17 M tendria que vender titulares
   caros, y ahi si se hunde.
3. **El hueco de Pepe es el banquillo**: 0 contra 8-11 de los otros dos
   de arriba (E12: ~1-2,5 pts por jornada).

**Contra lo que hace Pepe:** confirma el orden del plan: lo primero tras
la J8 es el defensa que entra de titular y deja banquillo (E12/E16). Y
anade algo para el gestor: **vigilar a Luismi en puntos** (no a Pollo17)
y que tendra que vender titulares para salir de -17 M.

**Limites:** una foto; la vara es de una jornada validada (E17); la
titularidad FF cambia de una semana a otra.

**Veredicto: SE AGUANTA como lectura de la carrera** (no hay nada que
construir). Repetir cada semana con la foto del dia.

### E19 · 05/10/2026 11:20 de Madrid · Lo que un rival le vende al Computer, ¿vuelve al mercado?

**El caso:** tras E18 el gestor apunta (04/10): «lo que hay que vigilar
es el mercado del Computer: lo que los rivales le vendan saldra ahi».
**Codigo:** `lab/rivales/vuelven_al_mercado.py`. Ventas al Computer del
tablon (sin repetidos) contra las listas diarias del Computer de
`libro_del_escaparate.jsonl` (20 jugadores al dia, 17/09 a 05/10).

**Resultado (56 ventas al Computer con al menos 7 dias de listas
detras):**

    vuelven a salir en la lista antes del 05/10   15/56 (27 %)
      a los 1-3 dias 3; a los 4-7 dias 5; a los 8 o mas 7
    en 7 dias: los vendidos al Computer salen el 14 %;
               un jugador libre cualquiera, el 20 %

**Lo que se aprende:** el Computer no los «devuelve» antes: salen en su
lista igual o menos que cualquier jugador libre, al azar, uno de cada
siete por semana. Si Luismi vende a Rafita al Computer, la probabilidad
de verlo en el mercado del Computer en la semana siguiente es ~1 de 7.

**Contra lo que hace Pepe y el plan:** no cambia lo que hace Pepe (la
subasta ya mira la lista del Computer cada dia). Corrige la expectativa:
si se quiere a un jugador que tiene un rival, la forma realista es
pujarle a ese rival a precio o algo mas (E18) o buscar otro igual en la
lista del dia (E16: salen mas de un defensa que sirve al dia), no esperar
a que el Computer lo saque.

**Veredicto: SE DESCARTA** que las ventas de los rivales al Computer
lleguen antes al mercado. n=56, 19 dias de listas.

### E18 · 04/10/2026 17:20 de Madrid · ¿Un rival en rojo antes de la jornada vende BARATO?

**El caso (04/10):** Luismi_Haz (-17 M) y DiosMande (-9,8 M) tienen que
estar en verde antes de la J8 y ponen jugadores a la venta (Rafita,
Tenaglia, Veiga...). La estrategia del gestor (punto 4) espera que alguno
salga barato. **Codigo:** `lab/rivales/venden_en_rojo.py` (tablon y
precios; los eventos repetidos se quitan).

**La sospecha:** un manager en rojo siempre puede vender al Computer, que
paga el precio + 1-3 % (E3). Con ese suelo, no tiene por que regalar nada
a otro manager.

**1) Traspasos de manager a manager (toda la temporada): 9, y NINGUNO por
debajo del precio.** Mediana +7,5 % sobre el precio (de +0,2 % a +59 %).
Los de Luismi_Haz: a Pollo17 por +59 %, +0,2 % y +5,4 %.

**2) Ventas de los rivales al Computer:**

    en las 48 h antes de empezar una jornada   n=91   mediana +2,0 %   por debajo del precio 23 (25 %)
    el resto del tiempo                        n=82   mediana +3,2 %   por debajo del precio  9 (11 %)

Con prisa, los rivales SI venden peor... **pero al Computer**: aceptan la
oferta que haya, aunque este por debajo del precio, antes que bajarle el
precio a otro manager.

**Lo que se aprende:** del rival en rojo no salen chollos para Pepe: o
vende al Computer, o vende a otro manager a precio o por encima. Lo que
SI pasa es que **se debilita**: vende titulares (Rafita, 90 %; Veiga,
80 %) y eso le quita puntos en la carrera. Y los que vende al Computer
vuelven mas adelante al mercado del Computer, donde se compran a lo que
piden (E9, E13).

**Contra lo que hace Pepe:** la decision de las rafagas («con 159.783 no
llega ninguno: no se puja») es la buena. Si se quiere a Rafita el 10/10,
contar con pagar el precio o algo mas, no menos.

**Veredicto: SE DESCARTA la idea de chollos de rivales en rojo** (9 de 9
traspasos a precio o mas). n pequeno en traspasos; con prisa se ve en las
ventas al Computer (n=91).

### E17 · 04/10/2026 11:20 de Madrid · ¿La vara de E16 (puntos por partido x titularidad) anticipa los puntos?

**Por que:** E16 eligio el defensa para la J8 por «puntos esperados» =
puntos por partido x titularidad de FutbolFantasy, y lo dejo sin validar.
**Codigo:** `lab/puntos/valida_esperado.py`. Datos: los 140 jugadores con
titularidad FF en la foto del 18/09 (antes de la J7) y sus puntos en la
J7.

    vara                           Spearman con la J7   mejor tercio (n=46)   jugaron
    puntos esperados (E16)              +0,37                4,67 pts           98 %
    puntos totales (E7, `nos_suma`)     +0,36                4,63               98 %
    precio                              +0,34                4,54               98 %
    puntos por partido                  +0,31                4,28               89 %
    titularidad FF sola                 +0,28                3,65               93 %

**La titularidad de FF esta bien calibrada:** con 70-89 % jugaron el 92 %
(n=51); 90-100 %, el 100 % (n=11); 40-69 %, el 79 % (n=43); menos de
40 %, el 43 % (n=35).

**Resultado:** la vara de E16 vale lo mismo que el total de puntos (+0,37
contra +0,36), ni mejor ni peor. Las dos dejan fuera al que no juega; la
media por partido sola es la peor (premia al que jugo poco y bien, como ya
vio E7). Una jornada, n=140.

**Veredicto: SE AGUANTA, sin cambio.** El punto 8 del plan puede usar
cualquiera de las dos varas (el total o la de E16); lo que no conviene es
la media por partido sola. Para el banquillo (E12/E16): **titularidad FF
de 70 % o mas** = juega 9 de cada 10.

### E16 · 03/10/2026 17:20 de Madrid · El primer fichaje despues de la J8: cuanta caja habra y en que se gasta

**Por que:** E15 dice que lo que decide es fichar para el once con la
caja. El plan del gestor (punto 8) es, desde el 10/10, un defensa suplente
de 1-3 M que juegue (E12). Aqui se mide cuanta caja habra y que defensa
da mas. **Codigo:** `lab/puntos/primer_fichaje.py` (tablon + la foto del
ciclo de hoy + las fotos de 89 ciclos del 27/09 al 03/10).

**1) Cada punto de la jornada es dinero:** Biwenger paga **30.000 EUR por
punto** (las 8 jornadas de Pepe; algo mas cuando se va abajo en la
general). J7: 47 pts, 1.510.000. Despues de la J8, con ~45-50 pts y la
racha: saldo +159.783 + ~1,4-1,5 M + 0,25 M = **~1,8 M para fichar**.
Un punto mas por jornada en el once son ~0,9 M en lo que queda de liga,
ademas del punto.

**2) El hueco mas flojo del once (puntos por partido x titularidad):**
Diego Rico 1,50; Jonny 2,10; Chust 2,40; Jutgla 2,90; el resto, 3,3 a 11,3.
Los tres defensas son los tres peores del once.

**3) Lo que el Computer saco en 7 dias (defensas <= 3,2 M, titular >=
60 %, estado ok): 9 distintos**, mas de uno al dia:

    Rafita        2,52 M   3,86 pts/jornada esperados
    Kike Salas    3,02 M   3,42
    Puga          1,55 M   2,57
    Freeman       1,45 M   2,33
    Rueda         1,74 M   2,20
    (y Bellerin, Sadick, Jorge Salinas, Sergi Cardona: 1,0-2,1)

**La cuenta:** el defensa que se fiche no es un suplente: es TITULAR en
lugar de Diego Rico, y Rico pasa al banquillo. Con un Puga (1,55 M): +1,1
pts por jornada en el once, mas Rico cubriendo bajas de defensa (3 x
3,2-8 % x 1,5 = +0,15-0,35). Con un Rafita (2,52 M): +2,4 y lo mismo.
Eso son ~1,2-2,7 pts por jornada (36.000-80.000 EUR de premio por jornada).
El plan del gestor acierta en la posicion; lo que cambia es el criterio:
**elegirlo por puntos esperados (media x titularidad), no solo «de 1-3 M
que juegue»** (Jorge Salinas, 2,22 M y 70 %, solo da 1,80: casi lo mismo
que Rico).

**Limites:** «puntos esperados» = media x titularidad de FF, sin validar
fuera de muestra (E7 valido el total de puntos, no esto); 7 dias de
mercado; el premio de la J8 depende de la J8.

**Veredicto: SE AGUANTA** (afina el punto 8 del plan). Actualizado en
«Listo para el plan».

### E15 · 03/10/2026 11:20 de Madrid · El bot pequeno, prototipo, contra Pepe en 91 vueltas reales

**Que es:** `lab/bot_pequeno/bot.py`, ~100 lineas, solo con lo medido:
caja sin deuda; reventa E1+E9 (lo que sube, estado ok, titular >= 40 %,
puja = max(lo que pide, precio + 1 %)); venta E3/E5 (el dia que baja; E14:
el once no se revende antes de jugar; Yamal nunca); once E7 (11 de mas
puntos con estado ok en la mejor formacion); banquillo E12.
`lab/bot_pequeno/replay.py` lo pasa por las fotos REALES de produccion:
la del 18/09 y los status.json de 89 ciclos (27-29/09 y 01-03/10,
artefactos de Actions que caducan a los 2 dias: no estan en git).

**1) El once:** igual que el de Pepe en 44 de 91 fotos. Las diferencias
son de transicion: el 18/09 Pepe ponia a Djene y Esquivel (0 puntos en
toda la temporada) y el bot a Dituro y Alvaro Carreras: en la J7, 4 contra
5 puntos. El 02/10, Gulacsi (Pepe) contra Dmitrovic (bot, mas puntos
totales; se vendia esa manana). Con 11 justos no hay nada que elegir.

**2) La caja:** en 30 de 91 fotos no habia ni un euro libre (saldo menos
pujas vivas <= 0). El bot no pujaria nada en esas vueltas.

**3) La reventa:** el bot pondria 4 pujas en 91 vueltas (Bouare, Osorio y
Szczesny el 18/09; Freeman el 28/09). Sus precios despues: +9 %, +126 %,
+2 % (vendidos el dia que bajaron) y +7 % (aun subiendo). **Pero las
cuatro se las llevaron rivales pagando mas:** Luismi_Haz 921.000 por
Bouare (el bot 878.700), 878.000 por Osorio (575.700), 351.000 por
Szczesny (323.200); Manzagool 1.850.000 por Freeman (1.464.500, Pollo17
1.777.000). **El bot no habria ganado ninguna.** Pepe esos dias: Boyomo
+28.503, Maffeo -42.850, Zubeldia -98.092 y jugadores de 150.000.

**Lo que se aprende:**
1. Con la caja de hoy y la pelea de hoy (E9, E11), **la reventa no da
   casi nada**, ni a Pepe ni al bot pequeno. El precio + 1 % no pierde
   dinero, pero tampoco gana subastas cuando hay alguien mirando.
2. Lo que de verdad decide el bot es **el once y la caja** (que hay para
   fichar puntos y cuando). Esa es la pieza que hay que hacer bien.
3. Un bot de ~100 lineas reproduce lo que hace Pepe en el once y no
   hace ninguna de las compras que perdieron dinero (E14), porque no
   compra sin caja ni lo que no sube.

**Limites:** 91 fotos de 3 ventanas cortas, casi todas con Pepe en rojo
o con 11 justos; no se puede probar su reventa con caja (no la hubo). Los
precios de despues llegan solo al 03/10.

**Veredicto: PROMETEDOR, NO LISTO.** El prototipo funciona sobre fotos
reales y no hace nada malo, pero en estas vueltas casi no hace nada. Se
sigue con la pieza que decide: fichar para el once con la caja (E7, E12,
E14), cuando haya caja despues de la J8.

### E14 · 02/10/2026 17:20 de Madrid · Agenda 5: ¿que parte de Pepe gana dinero de verdad?

**Por que:** antes de dibujar un bot pequeno hay que saber que vias de
compra han hecho algo bueno. **Codigo:** `lab/arquitectura/quien_gana.py`.
Cada compra de Pepe al Computer del tablon (50, del 10/08 al 02/10; el
tablon repite eventos y se quitan los duplicados) se cruza con la puja de
`bid_outcome_ledger.json`, que dice quien la decidio. Cerradas: venta real
menos compra. Abiertas: valor de hoy menos compra.

    via (quien decidio)                    n   P&L          verde   rampa (E1)
    subasta del reset                     14     -339.814   10/14     1/14
    carril                                 5     -372.315    1/5      0/5
    tablero (para el once)                 2     -529.265    0/2      1/2
    sin decision de Pepe apuntada (tablon)  11   -4.778.553    1/11     4/11
    sin decision de Pepe (plantilla)       13     +480.451    9/13     5/13
    sin apunte (agosto)                    5     +852.579    4/5      0/5

Las tres vias automaticas de Pepe (subasta, carril, tablero): **21
compras, -1,24 M, y solo 2 cumplian la rampa.** La subasta del reset vive
de jugadores de 150.000 (+35.000 en 11) y pierde en los de 1,6 M (Balde,
Yeray).

**Lo que mas cuesta no es la reventa: son fichajes caros revendidos sin
jugar.** Seis fichajes de 2,5 M o mas ya vendidos: -3.989.914. **Cuatro
se vendieron ANTES de jugar una sola jornada con nosotros** (todos en el
paron, sin decision de Pepe apuntada): Cabrera -684.031, Dmitrovic
-915.801, Ceballos -1.159.538 (tres dias), Antonio Blanco -548.704 (cuatro
dias). **-3.308.074 y cero puntos.** El porque esta medido: los jugadores
de 2,5 M o mas bajan de mediana un 5-8 % cada 11 dias (n=185-199; solo
suben 4 de cada 10), con jornadas o sin ellas, y la compra ya se paga
+4-14 % sobre el precio. Comprar caro y revender en dias es perder un
10-20 % seguro.

**Para el bot pequeno (agenda 5):** las vias que compran hoy no ganan;
lo que gana esta medido en E1/E3/E9 (rampa, precio + 1 %, vender el dia
que baja) y casi nada de eso lo hacen hoy las vias automaticas. El bot
pequeno necesita tres piezas y no veinte: (1) reventa con E1/E3/E9;
(2) fichajes para el once por puntos (E7), que NO se revenden en dias;
(3) el once y el banquillo (E12). Siguiente paso: el prototipo en `lab/`.

**Limites:** la etiqueta de quien decidio sale de un libro con huecos
(«sin apunte», «sin decision de Pepe»: el dueno o la orden del gestor);
los abiertos se valoran a precio de hoy; los puntos de los fichajes no se
cuentan (los cuatro vendidos no jugaron, asi que ahi no hay puntos que
contar).

**Veredicto: SE AGUANTA.** Pasa a «Listo para el plan» una regla de
proceso: un fichaje para el once no se revende antes de jugar con
nosotros.

### E13 · 02/10/2026 16:15 de Madrid · ¿Se puede pujar el precio VIEJO de la venta del Computer? (Moi Gómez, a fondo)

(Renumerado de E12 a E13 por el laboratorio a las 17:20: el E12 del banquillo ya existia y el puesto de mando lo cita. Su commit es d77cc6e.)

**El caso (01/10):** el dueño pujó 890.000 por Moi Gómez con el valor ya
en 900.000, y lo ganó (esa mañana valía 920.000). Hipótesis: la venta del
Computer pide el valor del día en que salió y no se mueve; el valor sí.
E10 solo miró el escaparate. **Código:** `lab/subasta/chollos_de_publicacion.py`.
Tablón (compras al Computer, 17/08 a 02/10, 214 con valor) + historial de
precios + las listas del Computer de `libro_del_escaparate.jsonl` (15 días,
17/09 a 02/10; falta el 21/09). Ojo: las fotos del 19 al 21/09 se hicieron
antes del cierre y son la lista del día anterior; corregido.

**1) El mecanismo es cierto.** Una venta del Computer dura uno o dos días
(salen 1 día: 53; 2 días: 62; 4 días: 2, re-puestos). Pide el valor del día en que salió y
no se mueve el 2.º día: de las 16 compras en 2.º día, las 16 pagan lo que
pedía o más, nunca menos. Biwenger acepta pujar lo que pide aunque el valor
ya haya subido.

**2) Cuántas veces se gana por debajo del valor (todo el tablón):**

    ganadas por debajo del valor que se veía al pujar     7 de 214
      Pollo17 4, Luismi_Haz 2, Pepe 1 (Moi)
      todas a «lo que pide» + 7 € / + 1.000-3.000 €
      ganancia contra el valor de la mañana de compra       +232.000 en total (7 casos, 47 días)
    ganadas por debajo del valor con que se despiertan     33 de 214
      (casi todo es que el precio siguió subiendo esa noche, no el truco)

**3) Lo que de verdad estaba disponible (15 días de listas):** 98 jugadores
siguieron sin vender un día después de salir. De ellos **valen MÁS de lo que
piden 6**, menos 53, igual 39. La diferencia es pequeña: +10.000 a +50.000
(+0,1 % a +1,6 %). De esos 6: Luismi se llevó 2, Pollo17 1, otro rival 1,
Pepe 1 (Moi) y 1 se quedó sin comprar. O sea: unos 3 a la semana, y los
rivales ya pujan por la mitad.

    Regla probada, solo sobre esos 6 (venta como E3 o a valor al día siguiente):
    pujar lo que pide + 1 €     ganadas 2   +50.000 al cierre   +80.000 al día siguiente
    pujar lo que pide + 1 %     ganadas 4   +71.000             +161.000
    pujar el VALOR de hoy       ganadas 4   +90.000             +180.000   (4/4 verdes)
    (13 días medibles; 11 M metidos, 6,9 M de ellos en un solo jugador)

**Contra lo que hace Pepe:** la puja de Moi no la puso Pepe: el libro de
pujas la apunta al encontrarlo en la plantilla (`EN_LA_PLANTILLA`, sin
valor ni probabilidad). Pepe no mira lo que pide la venta, solo el valor.

**Veredicto: el mecanismo SE CONFIRMA; como negocio NO da para mucho.**
Unos 3 casos a la semana, ~+50.000-100.000 a la semana en el mejor caso,
y la mitad ya se los llevan Pollo17 y Luismi con «lo que pide + poco». No
tapa ningún agujero. Sí vale como **regla menor, sin riesgo:** por un
jugador del Computer en su 2.º día en la lista (salió ayer) que hoy vale
más de lo que pide, **pujar su valor de hoy, ni un euro más.** Se paga
menos de lo que vale, se gana a las pujas de «pide + 7 €» de Pollo17 y
Luismi, y se pierde sin pena cuando alguien puja más. Y la regla de defensa
de E10 sigue: en 2.º día casi siempre pide MÁS de lo que vale (53 de 98);
ahí no pujar mirando el valor sino lo que pide.

### E12 · 02/10/2026 11:20 de Madrid · ¿Cuantos puntos cuesta jugar con 11 justos?

**El caso (02/10):** Pepe sale del rojo con 11 jugadores, sin banquillo.
En esta liga el once se cierra al empezar la jornada (`lineupRoundChanges:
0` en el tablon): un suplente solo sirve si se sabe ANTES del primer
partido que un titular no juega. **Codigo:** `lab/puntos/sin_banquillo.py`.

**Datos:** «fijos» = los que jugaron 5-6 de los 6 partidos hasta la J6
(n=249, lo mas parecido a un titular). Estado de Biwenger en la foto del
18/09 a las 16:16 (5 h antes del primer partido de la J7) y en los 45
ciclos del 27-29/09 (`lab/noticias/ciclos_27_29_09.json`).

**1) Cuantos fijos se caen:**

    no jugaron la J7                       29/249  (11,6 %)
      SE SABIA antes (lesion/duda/sancion)  8/249   (3,2 %)   <- un suplente lo cubre
      no se sabia (ok y no jugo)           22/249   (8,8 %)   <- nada lo cubre
    fijos con estado no ok en el paron (27-29/09): 18-20/249 (7,2-8,0 %)

Con 10 de campo, la probabilidad de que al menos uno se sepa fuera antes
de cerrar el once va del 28 % (3,2 %) al 57 % (8 %).

**2) Lo que da el suplente si entra (J7, estado ok):** un medio de 1-3 M
que venia jugando, 3,18 pts (jugo el 82 %); un defensa de 1-3 M, 2,31;
uno de menos de 1 M casi nunca juega (41-48 %). No hay multiposicion, pero
la formacion se puede cambiar antes de cerrar, y todas las de Biwenger
llevan 3 defensas o mas: **un medio suplente cubre a un medio (3-4-3) o a
un delantero (3-4-3 -> 3-5-2); a un defensa, solo otro defensa.**

**3) La cuenta:** plazas vacias que se saben a tiempo, 11 x 3,2-8 % =
**0,35 a 0,85 por jornada**; por ~3 pts del suplente = **~1 a 2,5 pts por
jornada, 30-80 en lo que queda de liga**. Vamos a 3 puntos de Pollo17.
Como inversion (E7: subir una plaza de <3 M a 3-6 M da ~1,5 pts por
~2,3 M), un suplente que juegue por ~2 M rinde lo mismo o mas.

**Contra lo que hace Pepe hoy:** 11 justos (1 POR, 3 DEF, 4 MED, 3 DEL
en 3-4-3). Con 3 DEF, un defensa que caiga NO lo cubre un medio (no hay
formacion de 2 defensas): el primer suplente tiene que ser DEFENSA, y el
segundo, un medio.

**Limites:** una jornada de «se sabia» (n=8) y el paron infla las bajas
(7-8 %); la foto es de 5 h antes del cierre (lo que se sabe al cerrar es
algo mas). Puntos del suplente de una sola jornada.

**Veredicto: SE AGUANTA.** Tener al menos un suplente que juegue vale
~1-2,5 pts por jornada. Pasa a «Listo para el plan».

### E11 · 01/10/2026 17:25 de Madrid · ¿Se sabe de antemano que subasta NO va a pelear Pollo17?

**Por que:** E9 dice que las subastas de jugadores que suben y que nadie
pelea se ganan con precio + 1 % y salen 33/33 en verde, pero solo son el
30 %. Si se supiera cuales, Pepe pujaria solo por esas y no bloquearia
caja en pujas perdidas. **Codigo:** `lab/subasta/quien_no_pelea.py`.
118 subastas de jugadores que subian (tablon), 35 sin pelea. Se mira la
tasa «sin pelea» por tramos, con dos mitades (hasta el 10/09 y desde).

    subida del ultimo cambio 0-1 %    18/42 (43 %)   mitades 12/18 -> 6/24
                             1-2 %    10/31 (32 %)            6/16 -> 4/15
                             2-4 %     1/16  (6 %)            0/9  -> 1/7
                             4+ %      6/29 (21 %)            2/18 -> 4/11
    dias seguidos subiendo, precio, posicion: todos entre el 21 y el 36 %,
    y cambian de orden entre mitades.
    dias desde el final de la jornada: 0-1 d 37 %, 2-3 d 34 %, 4+ d 20 %.

**Resultado:** nada separa de forma estable. Lo unico que apunta es que
las subidas pequenas (0-1 %) se pelean menos, pero de una mitad a otra
pasa del 67 % al 25 %. Ademas, la pelea va a mas: sin pelea el 33 % hasta
el 10/09 y el 26 % despues. Los rivales ya juegan a lo mismo que E1.

**Contra lo que hace Pepe:** nada que comparar; la pregunta era si se
podia afinar la regla de E9, y no se puede con estos datos.

**Veredicto: SE DESCARTA.** No hay forma de saber de antemano quien
queda sin pelea. La regla sigue siendo la de E9: pujar precio + 1 % por
TODOS los que suben y perder sin pena unas 7 de cada 10. El coste de esa
regla es la caja bloqueada en pujas vivas que se pierden: con el saldo en
rojo, que lo tenga en cuenta quien la meta.

### E10 · 01/10/2026 15:50 de Madrid · ¿Hay «chollos de la mañana» en el precio fijo del Computer?

**El caso (01/10, lo vio el dueño):** Moi Gómez se pujó a 890.000 con el
precio ya en 900.000. **La venta del Computer pide el precio del día en que
salió y no se mueve; el valor sí.** Hipótesis: comprar cada mañana a los
que siguen en el mercado y ya valen más de lo que piden.

**Cómo:** `libro_del_escaparate.jsonl`, última foto de cada día, 15 días
(17/09 a 01/10). Lo que pide = precio del primer día de su racha en el
mercado. 120 apariciones de 2.º día o más. (Ojo: el escaparate son los ~20
que Pepe mira cada día, no todo el mercado.)

    valen MÁS de lo que piden    7    (+10.000 a +50.000; total +160.000)
    valen MENOS                  61
    igual                        52

**Veredicto: NO SE AGUANTA como negocio.** Los que suben se venden el
primer día (Pollo17 puja en el 75 %, E9); los que se quedan en el mercado
son, sobre todo, los que bajan. Lo que sí deja: **(1) regla de defensa:**
por un jugador que lleva días en el mercado, pujar mirando lo que PIDE la
venta, no su valor: casi siempre pide más de lo que vale (Lejeune, Rico,
Cubarsí el 30/09). **(2)** Si sale uno que vale más de lo que pide (como
Moi), pujar lo que pide: ganancia pequeña y sin pelea.

### E9 · 01/10/2026 11:20 de Madrid · ¿Hay viajes sin pelearse con Pollo17? (y E8 CORREGIDO a la baja)

**El caso (01/10):** Pollo17 gano las dos pujas grandes de la orden
(Fofana, Akhomach). El gestor: «los viajes cortos tienen que ir a
jugadores que nadie mas puja». **Codigo:** `lab/subasta/competencia.py`.
211 subastas del Computer con precio (tablon, 17/08 a 01/10), con la puja
ganadora y las perdedoras.

**1) Pollo17 ya juega a E1.** De los 118 subastados que SUBIAN, Pollo17
pujo en **89** (Luismi en 76). De los 93 que no subian, en 17. Solo 35 de
los que suben (30 %) tuvieron un unico pujador.

**2) Lo que paga el ganador y como sale el viaje (venta como E3):**

    SUBE, un solo pujador          n=35   paga +0,1 % sobre el precio   verde 32/35   ROI med +4,3 %
    SUBE, con Pollo17 pujando      n=89        +7,4 %                       66/89           +4,6 %
    SUBE, disputada sin Pollo17    n=10       +10,4 %                        6/10           +2,2 %
    NO sube, un solo pujador       n=79        +0,3 %                       30/79           -0,2 %

Cuando Pepe gana una disputada paga **+14,1 % sobre el precio y +8,6 %
sobre la segunda puja** (n=10); Pollo17, +7,4 % y +3,3 %. Pepe se pasa.

**3) La regla «pujar precio + 1 % por TODO el que sube» (se gana solo si
nadie puja mas):** 33 ganadas, **33/33 en verde**, ROI mediano +3,1 %.
Subir la puja gana mas subastas pero peores: x1,03 33/42 verdes; x1,05
29/55; x1,10 30/85 y ROI mediano -3,1 % (desde el 08/09, -4,9 M). **Pelear
con Pollo17 subiendo la puja no compensa.**

**4) E8 ESTABA INFLADO.** E8 suponia ganar cualquier subasta pagando +1 %
sobre el ganador real, y el ganador real de lo que sube suele ser
Pollo17. Rehecho ganando SOLO lo que nadie pelea (puja precio + 1 %), 36
semanas:

    caja 4 M, tope 2 M por viaje    mediana   +70.700/semana   verde 25/36   0,9 viajes/semana
    caja 4 M, tope 4 M              mediana  +121.200          verde 33/36   1,3
    caja 8 M, tope 4 M              mediana  +179.860          verde 33/36   2,4
    (E8 decia +685.540 con 4 M y tope 2 M: unas diez veces mas)

**Veredicto:** (a) **SE AGUANTA** como regla de puja: por los que suben,
pujar precio + 1 % y perder sin pena las que pelea Pollo17 (33/33 en
verde); no subir la puja para ganarle. (b) **Los viajes cortos NO tapan
el agujero del 09/10:** con 4 M dan ~0,07-0,12 M a la semana. El agujero
tiene que salir de los cambios uno por uno y de la red. Corregido E8 en
«Listo para el plan».

### E8 · 30/09/2026 17:25 de Madrid · ¿Cuanto dan los VIAJES CORTOS con plazo fijo? (el agujero del 09/10)

**CORREGIDO por E9 (01/10): estos numeros suponen ganarle la puja a Pollo17 y estan inflados unas diez veces. Ver E9.**

**El caso:** Pepe en rojo (~-1,3 M) y tiene que estar en verde el 09/10
a las 15:00 sin vender a los top. La estrategia (2) del gestor: viajes
cortos de reventa (E1/E3), tope 2 M por viaje, 3-4 M en total, todo
vendido antes del 07/10. Su cuenta a ojo: +0,2-0,4 M. **Codigo:**
`lab/precio/viajes_con_plazo.py`.

**Como:** 35 semanas (arranques del 20/08 al 23/09). En cada una: compra
de S a S+5 lo que el Computer subasto y SUBIO en el ultimo cambio
(tablon), pagando lo del ganador real + 1 %; vende al Computer el primer
dia que baja o, a la fuerza, el dia S+7; ofertas segun E3; el dinero
vuelve al dia siguiente.

    caja   tope/viaje   mediana    peor semana   mejor      en verde   viajes/sem
    2 M       2 M      +327.123     -87.870    +2.444.324    29/35       2,2
    3 M       2 M      +389.979    -175.294    +1.983.564    31/35       3,1
    4 M       2 M      +685.540     -22.220    +2.424.594    34/35       4,2
    4 M       1 M      +327.123     -57.417    +2.444.324    24/35       2,9

    semanas que tapan 1,3 M:  2 M: 3/35   3 M: 6/35   4 M: 5/35
    semanas que dan >= 0,5 M: 2 M: 13/35  3 M: 15/35  4 M: 20/35

- **Las semanas del paron (arranques del 20 al 23/09), con 4 M:** +0,28
  a +0,99 M. En el paron tambien funciona.
- **El 75 % de los viajes se venden A LA FUERZA el ultimo dia**, y aun
  asi ganan: lo que se compra subiendo sigue subiendo la semana entera.
  El plazo no es el peligro; el peligro es no ganar la puja.
- El tope de 1 M por viaje estorba: deja fuera a los que mas suben.

**Contra el plan del gestor:** su +0,2-0,4 M es prudente. La mediana
medida es +0,33 M (2 M de caja) a +0,69 M (4 M), casi nunca pierde (peor
semana -0,18 M) y **tapa el agujero entero solo 1 semana de cada 6-7**.

**Limites:** solo se ven los jugadores que alguien compro, y se supone
ganar la puja con +1 % sobre el ganador real (Pepe gano el 84 % de sus
pujas). No cuenta que meter 4 M hunde el saldo a ~-5 M unos dias (hay
que tenerlos devueltos antes del 09/10 15:00, y lo estan: el plazo es el
07/10). Seis semanas de datos.

**Veredicto: SE AGUANTA como ayuda, NO como solucion.** Abrir 3-4 M
acotados a viajes E1/E3 hasta el 07/10 da, de mediana, +0,4-0,7 M con muy
poco riesgo; el resto del agujero tiene que salir del cambio uno por uno
o de la red (Jutgla). Numeros en «Listo para el plan».

### E7 · 30/09/2026 11:20 de Madrid · Que predice los PUNTOS de la jornada siguiente (y cuanto cuesta un punto)

**Por que:** la regla del dueno (29/09) es que la inversion son puntos.
Para fichar y vender pensando en puntos hay que saber que dato los
anticipa y cuanto cuesta subir una plaza del once. **Codigo:**
`lab/puntos/que_predice_puntos.py`.

**Datos:** lo unico con puntos por jugador en git: totales tras la J6
(foto del 18/09, antes de la J7) y tras la J7 (`puntos_por_jornada.jsonl`).
Puntos de la J7 = diferencia; n=545. **Una sola jornada fuera de muestra**
(no hay fotos antiguas en git y los artefactos duran 2 dias).

**1) Que predice la J7 (correlacion de rangos; estado ok el 18/09, n=479):**

    puntos totales hasta J6 (lo que usa `nos_suma`)   +0,48   el mejor 20 % hizo 4,88 pts
    precio de Biwenger                                +0,46                      4,60
    puntos por partido jugado                          +0,44                      4,54

Casi empatan; la media por partido es la peor, como ya midio
`el_que_va_a_despegar` el 13/09 y el 19/09. **Pepe ordena bien.** Por
posicion, lo mas previsible son los porteros (+0,71) y lo menos, los
defensas (+0,36).

**2) El estado es el filtro que mas separa:** ok 2,77 pts (jugaron 69 %),
doubt 1,29 (14 %), injured 0,06 (2 %), sancionado 0.

**3) Cuanto da cada tramo de precio (estado ok):**

    tramo     n    jugaron   puntos J7   media hasta J6   precio medio
    0-1 M    169     43 %       1,41        1,62/partido       0,41 M
    1-3 M    157     75 %       2,58        3,24               1,87 M
    3-6 M    113     90 %       4,27        4,61               4,20 M
    6-10 M    23    100 %       4,87        5,88               7,84 M
    10+ M     17    100 %       5,35        8,40              14,80 M

Subir una plaza del once de 1-3 M a 3-6 M da +1,7 pts en la J7 (+1,4 de
media) por ~2,3 M: **~0,6-0,7 pts por millon**. De 3-6 M a 6-10 M, +0,6
(J7) a +1,3 (media) por ~3,6 M: 0,2-0,35 por millon. Por encima de 10 M,
la J7 dice +0,5 por 7 M; la temporada, +2,5. Lo mas barato en puntos es
**sacar del once a los de menos de 3 M**; los de menos de 1 M ni juegan
(43 %). Y por posicion, los defensas dan menos (2,31 en la J7) que medios
(3,16) y delanteros (3,42).

**Contra lo que hace Pepe:** 32 de sus 55 pujas ganadas son defensas de
1-3 M (medido por el gestor el 29/09): el tramo y la posicion que menos
puntos dan por plaza.

**Limites:** una jornada; la «media hasta J6» por tramo es circular (el
precio sube con los puntos), por eso se dan las dos columnas. Sin
titularidad historica.

**Veredicto: NADA QUE CAMBIAR EN COMO ORDENA PEPE** (total de puntos y
precio van igual de bien; el estado ya se filtra). **Numeros para las
decisiones del gestor (la hucha, el agujero del 06/10):** el punto mas
barato esta en subir las plazas de menos de 3 M a 3-6 M, y mejor en
medio o delantera que en defensa. Repetir con la J8 (cierra hacia el
12/10) antes de convertirlo en regla.

### E6 · 29/09/2026 17:30 de Madrid · E4-bis: ¿los filtros de hoy ya frenan las noticias de BAJA?

**Pregunta del gestor (29/09 14:15):** de las BAJA de E4, ¿cuantas pasarian
HOY los filtros que ya hay (estado de Biwenger, titularidad >= 40 %, la
rampa)? Si son pocas, E4 esta cubierto.

**Codigo y datos:** `lab/noticias/e4bis_filtros.py`. Archivo de FF
ampliado hasta el 29/09 16:24 (`eventos_hasta_29_09.jsonl`). El estado de
Biwenger y el ultimo cambio de precio de los 547, hora a hora, sacados de
los 45 artefactos de produccion que quedan (27/09 16:10 a 29/09 15:09 UTC;
caducan a los 2 dias) mas la foto del 18/09
(`ciclos_27_29_09.json`, extracto de 0,6 MB). Una BAJA «se cuela» si en
algun ciclo de sus 72 h el jugador tiene estado ok Y su precio sube (y,
si esta en el tablero, disponible y con titularidad >= 40 %).

**Resultado: 41 episodios de BAJA con algun ciclo en sus 72 h.**

    frenados por lo que ya hay                 30/41
      Biwenger ya lo marca en el 1er ciclo      22   (injured, doubt, sanctioned)
      la rampa (el precio no sube) o lo marca despues   8
    se cuelan                                  11/41
      noticia mal clasificada (no es una baja)   6   Tsitaishvili «golpe sin
                                                     importancia», Valentini y
                                                     J. David (titularidad),
                                                     Simeone, Szczesny «dudas»,
                                                     De la Fuente (seleccionador)
      baja de verdad                             2   Gaya (-6,2 % en 3 dias),
                                                     Danjuma (0 %; en el tablero)
      demasiado recientes para saberlo           3   Rioja, Raphinha, Miguel
                                                     Roman (29/09; 2-4 h de ciclos)

**El caso que si cuesta: Zubeldia.** FF: «sigue al margen», 28/09 a las
14:59. Biwenger lo pasa a «doubt» el 29/09 a las 07:19 de Madrid, DESPUES
del reset en que Pepe lo gano (1.363.592; la puja se puso el 28/09 a las
07:19, antes de la noticia y antes de encender la rampa). La noticia fue
**16 horas por delante de Biwenger**, y la puja viva no se reviso.

**Lo que se aprende:**
1. Para las pujas NUEVAS, E4 ya esta casi cubierto: los filtros de hoy
   frenan 30 de 41, y de las 11 que se cuelan 6 no son bajas. Una guardia
   por palabras frenaria tantas buenas como malas.
2. El hueco real son las **pujas ya puestas** cuando llega la noticia (o
   cuando Biwenger cambia el estado): la regla actua al pujar, no antes
   del reset.

**Veredicto: NO CONSTRUIR la fuente nueva de noticias.** n=41 en dos
ventanas cortas (15-18/09 y 24-29/09). Pista para el gestor, sin medir
bien (n=1): revisar las pujas vivas en el ultimo ciclo antes del reset
con lo que ya hay en la foto (estado de Biwenger, `absence` de FF con
fecha posterior a la puja, la rampa) y retirarlas si ya no pasarian.
Antes (doctrina 84): mirar si Pepe ya retira pujas y por que via.

### E5 · 29/09/2026 11:20 de Madrid · Vender el dia que baja (E1) o aceptar la primera oferta +1 % (salida_del_viaje)

**Pregunta del gestor (29/09 07:15):** comparar las dos salidas con la
misma vara (%/dia, con la caja limitada de Pepe) y decir por donde vende
Pepe hoy. **Codigo:** `lab/precio/salida_contra_viaje.py`.

**Como:** mismas compras para las dos (las de la rampa: el precio subio
en el ultimo cambio). E1 vende al Computer el primer dia que el precio
baja. VIAJE (`src/analysis/salida_del_viaje.py`) acepta la primera oferta
>= coste + 1 %; tras 4 resets caduca y pasa a E1. La oferta de cada dia
se saca al azar de las 204 ventas reales al Computer del tablon, segun el
precio ese dia (50 repeticiones, semilla fija).

**1) Sin tope de caja (6.239 entradas, un dia muerto por viaje):**

    E1      verde 91,1 %   ROI medio +31,9 %   +2,66 %/dia
    VIAJE   verde 94,6 %   ROI medio  +3,9 %   +1,35 %/dia

**2) Con la caja de Pepe (solo lo que el Computer subasto, puja = ganador
+ 1 %, 20/08 a 29/09):**

    caja    salida   viajes   cobrado      sin vender     total
    2 M     E1         10    +2.048.909   +3.468.802   +5.517.711
    2 M     VIAJE      16      +771.633      -63.137     +708.495
    5 M     E1         15    +2.962.267   +4.775.962   +7.738.229
    5 M     VIAJE      27      +414.428     -165.876     +248.552
    10 M    E1         21    +3.485.551   +7.636.692  +11.122.243
    10 M    VIAJE      42    +1.201.792     -315.495     +886.297

Aun contando solo lo ya cobrado, E1 gana: +2,05 M contra +0,77 M con 2 M
de caja. VIAJE mueve el doble de viajes y gana entre 3 y 30 veces menos.
Vende al primer reset, justo cuando la subida acaba de empezar: la
inercia de E1 (92 % de «manana sigue») es lo que regala. Su 3,05 %/dia
salio de medir la prima del Computer (n=34), no lo que el precio sigue
subiendo despues de vender.

**3) Como vende Pepe de verdad (33 viajes cerrados del tablon, 31 al
Computer):** ni con una regla ni con la otra. El dia de la venta el precio
subio en 5, estaba quieto en 15 y bajo en 13. Aguanta 4 dias de mediana,
pero 16 de 33 pasan de 5 dias y tres pasan de 24 (-221.001, -538.901,
+246.363). Desde el 14/09: 27 viajes, **-2.742.657**, y solo 11 cobrados
por encima de coste + 1 %. El peor: Ceballos, comprado el 24/09 a
5.480.138 y vendido el 27/09 a 4.320.600 (-1.159.538). Vende lo que el
escaparate y las ofertas del Computer le traen, cuando le llegan.

**Limites:** las primas se sacan de ventas que alguien ACEPTO (las
ofertas que se rechazaron no se ven: favorece un poco a VIAJE). Lo que
sigue sin vender se valora a precio de hoy sin prima. Seis semanas.

**Veredicto: GANA E1, CON CLARIDAD. `salida_del_viaje` NO se enciende.**
La mitad de venta que hay que construir es la de E3 (actualizado en
«Listo para el plan»).

### E4 · 29/09/2026 12:00 de Madrid · ¿Las noticias se adelantan al precio?

**Codigo e informe:** `lab/noticias/` (INFORME.md, archivar.py, analizar.py,
contra_e1.py, caso_aspas.py). Archivo: 3.174 noticias de FutbolFantasy del
08/08 al 29/09 (recorridas por ID, el listado esta cacheado), con hora y
equipo; 629 BAJA, 291 VUELTA, 135 TITULARIDAD tras quitar traspasos y
ruedas de prensa; clasificacion por palabras, ~80 % bien en 30 a mano.

**Resultado (jugadores >= 1 M, exceso contra los del mismo dia y sentido):**

    BAJA         n=180   -2,5 % a 3 dias (IC90 -3,6 / -1,2)   -4,3 % a 7
    VUELTA       n= 94   sin senal de subida (-1,3 %)
    TITULARIDAD  n= 77   sin senal (+0,9 %, cruza el cero)

- La BAJA adelanta la caida 0-1 dias; en el 58 % el precio ya caia (lesion
  en partido). Vender al leerla NO mejora la salida de E1 (-4,2 % de
  media, gana 14 de 70): E1 ya sale a tiempo.
- Lo que si vale: **NO COMPRAR** a quien tiene BAJA reciente. En los que
  venian subiendo (justo la compra de E1): -3,7 % a 3 dias (n=50).
- Caso Celta: Aspas, parte en FF el 13/09 16:15, el precio cae el 14 y el
  15 (-7,3 %); -37 % hasta el 29/09. Duran subio por su doblete del 19/09
  (E2), no por una noticia. Jutgla: ninguna noticia explica su caida.
- **Piloto de fuentes locales (Celta, n=1):** Faro de Vigo se lee (hora por
  articulo): lesion 5 h DESPUES que FF, plazo de baja ~39 h antes que el
  parte oficial, pero con el precio ya cayendo. Moi Celeste, Minuto
  Noventa, foros celtistas: cortan la conexion; Reddit 403; X sin sesion
  nada. No compensa montar fuentes locales para los 20: basta FF.

**Veredicto: PROMETEDOR COMO GUARDIA DE COMPRA.** Pasa a «Listo para el
plan»: «no pujar por quien tenga una noticia de BAJA en FutbolFantasy en
las ultimas 72 h». Limites: 6 semanas, pretemporada, parón desde el 20/09,
clasificacion por palabras, piloto local n=1.

### E3 · 28/09/2026 17:20 de Madrid · Cuando vender lo que se compro subiendo

**Codigo:** `lab/precio/cuando_vender.py`. Lee el tablon y
`price_history.json` (16/08 a 28/09, 626 jugadores; falta el 07/09 entero
y se salta como un dia).

**Hipotesis:** la mitad de VENTA de E1 («al Computer el primer dia que
baja») es la mejor salida; esperar a confirmar la bajada, vender por
tiempo o vender en cuanto la subida frena, rinden menos.

**1) Como paga el Computer (202 ventas reales de la liga):**

    dia en que el precio...   n    oferta sobre el precio   precio al dia siguiente
    subio                    39           +2,1 %                    +0,4 %
    quedo quieto             55           +1,0 %                     0,0 %
    BAJO                    108           +3,2 %                    -1,8 %

El dia que baja, el Computer aun paga +3,2 % sobre el precio nuevo (casi
el de antes de bajar). Al dia siguiente se pierde otro 1,8 %. **Se vende
el MISMO dia de la bajada, no al siguiente.** Y los managers lo saben:
108 de sus 202 ventas son en dia de bajada.

**2) Salidas (6.126 entradas: cada jugador-dia en que el precio subio;
se paga +2,2 %; lo que sigue abierto, a precio de hoy):**

    salida                        verde   ROI mediano   dias   ROI por dia*
    tras 1 bajada (E1)            91,1 %     +6,6 %       8      +2,70 %
    cuando la subida frena        86,8 %     +2,8 %       3      +2,56 %
    tras 2 bajadas                78,4 %     +5,8 %       9      +2,34 %
    si cae 3 % desde el pico      69,9 %     +5,1 %      10      +2,10 %
    a los 5 dias                  79,5 %     +4,1 %       5      +2,00 %
    a los 3 dias / a los 7        85,5 / 74,1 %  +2,9 / +4,7 %  3 / 7   +1,95 / +1,93 %
    (*) contando un dia muerto por viaje: se cobra hoy y se puja para manana

Por mitades: hasta el 06/09 gana la de E1 (3,07 %/dia contra 3,02 % de
«cuando frena»); desde el 07/09 empatan (1,95 % contra 2,02 %, y la de E1
tiene aun el 56 % de viajes abiertos y subiendo). Esperar a una segunda
bajada pierde siempre (13 puntos menos de verdes).

**Contra Pepe hoy (E1):** vendio en dia de bajada 13 de 30 viajes y, de
mediana, 2 dias despues del pico. Publica con precio pedido alto (Ceballos
a 6,8 M valiendo 4,22 M), pero el Computer le pago 4.320.600 = precio
+2,4 %: **el precio pedido no cambia lo que paga el Computer.**

**Limites:** todos los jugadores, no solo los que se pueden comprar; sin
tope de caja; la prima de compra es la mediana (+2,2 %). Es la comparacion
entre salidas lo que vale, no los porcentajes absolutos.

**Veredicto: SE AGUANTA.** La salida de E1 es la mejor o empata con la
mejor en todo lo medido, y el detalle que faltaba es de horas: aceptar la
oferta del Computer el mismo dia de la bajada. Actualizado en «Listo para
el plan».

### E2 · 28/09/2026 11:30 de Madrid · Que hace que un jugador EMPIECE a subir

**Codigo:** `lab/precio/que_predice.py`. Lee `price_history.json` (16/08 a
28/09, 626 jugadores), el tablon (finales de jornada), la foto del 18/09 y
`puntos_por_jornada.jsonl` (totales del 23/09). Puntos de la J7 = totales
del 23/09 menos los del 18/09.

**Hipotesis:** E1 dice que lo que sube sigue subiendo. Lo que falta es
saber que ARRANCA una subida, para entrar antes que Pollo17. Idea: los
puntos de la jornada que acaba de terminar.

**A) Cuando arrancan (42 dias, 16.875 casos de jugador quieto o bajando):**

    dias desde el final de la jornada    0      1      2      3      4      5     6+
    empiezan a subir                   7,6 %  2,3 %  4,3 %  2,3 %  1,2 %  2,7 %  1,0 %

Las subidas nacen con el resultado de la jornada: el mismo dia y dos dias
despues. El resto de la semana casi nadie arranca.

**B) Quien arranca tras la J7 (398 que NO venian subiendo el 21/09):**

    no jugo la J7        n=204   arrancan en 2 dias  0,5 %   semana: -3,7 % (mediana)
    jugo, < 2 puntos     n= 47                       0,0 %           -9,4 %
    jugo, 2-5 puntos     n=137                       2,9 %           -6,8 %
    jugo, 6+ puntos      n= 10                      50,0 %    -1,7 % (6-9) / +3,0 % (10+)
    (ya venian subiendo  n=147                                        +7,1 %; media +18,1 %)

Fuera de muestra (mitades de jugadores al azar, umbral elegido en una y
medido en la otra): con 4-5 puntos o mas, arrancan el **17-25 %** (n=23 y
n=8) contra el **1 %** del resto (n=176 y 191).

**C) Que dia compra cada uno (dias desde el final de la jornada):** Pepe
compra el 46 % el mismo dia del final (0d); Pollo17 reparte (29 % al dia
siguiente) y Luismi_Haz tambien. Descriptivo: no dice por si solo quien
acierta.

**Lo que se aprende:**
1. La inercia de E1 sigue siendo la senal grande: los que ya subian
   ganaron +7,1 % en la semana; los que no, perdieron entre 3,7 y 9,4 %.
   **Comprar a un jugador que no sube es perder dinero aunque no pagues
   prima**: la semana despues de la J7 bajo casi todo el mercado.
2. El que no jugo cae (-3,7 %) y casi nunca arranca (1 de 204). Confirma la
   regla «¿va a jugar?», que ya esta encendida.
3. Los puntos de la jornada si anticipan el arranque (1 de cada 4-5 con 5+
   puntos, contra 1 de cada 100), pero **con una sola jornada y n=8/23 no
   es una regla**: es una pista.

**Veredicto: PROMETEDOR, NO LISTO.** No pasa al plan. Para cerrarlo hacen
falta mas jornadas con puntos por jugador: `puntos_por_jornada.jsonl`
guardara la J8 (cierra el 12-13/10). Siguiente paso: bajar las fotos de
jornadas anteriores de los artefactos de Actions, si las hay, y repetir
B con 3-4 jornadas.

### E1 · 28/09/2026 01:10 de Madrid · Como ganan Pollo17 y Luismi_Haz

**Codigo:** `lab/rivales/viajes.py` (reconstruye los viajes) y
`lab/rivales/regla_simple.py` (prueba la regla). Solo leen
`board_events.json` y `price_history.json` (precios del 16/08 al 27/09).

**Hipotesis:** su regla es «compra al Computer lo que esta subiendo de
precio y vendeselo al Computer cuando empieza a bajar», y Pepe no la sigue.

**Lo que hacen (viajes cerrados al Computer, tablon del 09/08 al 27/09):**

                                  Pollo17     Luismi_Haz        Pepe
    compras / viajes cerrados       78 / 56       66 / 43      48 / 30
    P&L cerrado                 +11.970.510   +13.136.092     -812.038
    verde                             48/56         28/43        17/30
    SU PRECIO SUBIO EL DIA ANTES      50/60         35/49     **9/41**
    prima sobre el precio            +2,6 %        +2,6 %       +0,3 %
    pujas en la subasta (mediana)         2             2            1
    dias aguantado (mediana)              5             6            4
    vende al Computer                 54/56         40/43        28/30
    dias entre el pico y la venta         1             2            2

**Por que funciona (626 jugadores, todos los dias):** el precio de
Biwenger tiene inercia brutal. Si subio hoy, manana sube el **92 %** de
las veces (+3 % de media; n=5.338). Si bajo hoy, manana baja el 80-94 %.
Si no se movio, manana casi nunca se mueve. Los costes del viaje se anulan:
la puja ganadora paga +2,2 % sobre el precio (mediana, n=196) y el
Computer compra a +2,4 % (mediana, n=204).

**La regla simple lo imita.** Todas las compras reales al Computer de los
8 managers (n=191 con precio), al precio que pagaron y saliendo el primer
dia que el precio baja:

    su precio subio el dia antes    n=109  verde 57/73  ROI med +3,5 %  P&L +25.701.957
    su precio NO subio              n= 82  verde 24/58  ROI med -0,4 %  P&L    -567.940

Con presupuesto (10 M a la vez, solo jugadores que el Computer subasto,
pagando +1 % sobre el ganador real): +3,29 M en 14 viajes cerrados (10
verdes) + 7,79 M latentes en 8 abiertos. Aguanta en las dos mitades
(hasta el 06/09: 9/10 verdes; desde el 07/09: 3/3 cerrados, el resto
sigue subiendo). La misma regla AL REVES (solo lo que no subio, lo que
hace Pepe): 5/16 verdes, -259.661.

**Limites (honestos):** solo vemos a los jugadores que alguien compro (los
que el Computer saco y nadie quiso no salen en el tablon); se supone que se
gana la puja con +1 % sobre el ganador; 6 semanas de datos. La senal es
tan grande (92 % contra 5 %) que estos limites no la tumban, pero el P&L
con presupuesto es una estimacion, no una promesa.

**Veredicto: SE AGUANTA.** Pepe compra, sobre todo, jugadores cuyo precio
no se mueve (32 de 41), y ahi no hay nada que ganar. Pasa a «Listo para
el plan».

## Listo para el plan

(ideas que han ganado con datos y estan listas para que un turno del gestor
las meta en Pepe; al pasarlas, se mueven al plan de EL-PUESTO-DE-MANDO.md)

- **(E63, 26/10 11:16) Entre los que suben, primero los que puntuaron 8+
  en la ultima jornada.** El precio sigue a los puntos toda la semana
  siguiente (Spearman +0,6-0,7 de martes a viernes). Comprando al precio
  del martes, los que suben y hicieron 8+ ganan +7/+10 % en 6 dias; los que
  suben con menos, +3/+4,5 % (J8 y J9). Para la cartera, la rotacion, el
  informe de la mañana y la mejora: a igualdad de lo demas, elegir al que
  hizo mas puntos en la ultima jornada. Para revender, solo si la prima
  queda por debajo de ~+7 % (E49/E51).
- **(E61, 25/10 11:15) La lista de objetivos necesita ~10 nombres.** El
  Computer saca ~11 nuevos al dia casi al azar entre los ~424 libres y cada
  uno se queda dos dias: un jugador concreto sale uno de cada ~40 dias. Con
  3 nombres, sale alguno en una semana el 42 % de las veces; con 10, el
  84 %. Para Roberto por Nino o Zabiri, contar con semanas, no dias; y
  ampliar la lista con suplentes igual de buenos por puesto.
- **(E57, 23/10 11:16) Prima mas baja si la puja se resuelve el dia de la
  jornada.** En los resets a menos de 24 h del primer partido hay la mitad
  de pelea (31 % contra 50-57 %; los que suben, 52 % contra 73 %) y el
  ganador paga +0,3 % de mediana (contra ~+3 %); n = 39. Para la orden y
  la mejora: en esas pujas, bajar la prima un escalon de E41 (lo que
  pedia +8-12 %, +4 %; lo que pedia +3 %, +1 %). Boye a +12,2 % sin rival:
  ~650.000 probablemente de mas.
- **(E56, 22/10 17:18) Un partido suelto de una jornada ya empezada NO es
  plazo de caja.** La parte 3 de la J6 (Levante-Athletic, 21/10) conto con
  el once y la caja de la parte 2 (15/09): Pollo17, en rojo el 21/10,
  cobro igual; Biwenger lista los totales de la jornada y paga solo la
  diferencia (Pepe +11 pts, +330.000). Para Pepe: no vender ni frenar
  compras por el Rayo-Athletic de la J8 cuando tenga fecha (contara con
  el once y la caja del 09/10). Quitar la regla «el aplazado es ronda
  propia» de la rotacion y del cierre si la tienen. n = 1: vigilar la
  siguiente.
- **(E53, 21/10 11:16) El precio como segunda opinion en la mejora del
  once.** Fuera de muestra (J8+J9, n = 364), el precio predice los puntos
  que vienen mejor que los puntos por partido (Spearman +0,44 contra
  +0,34; en los que juegan, +0,49 contra +0,42), en todas las posiciones
  de campo. Propuesta: que la mejora NO haga un cambio cuyo xP sube pero
  que cambia a un jugador por otro bastante mas barato (el precio dice lo
  contrario), o que encoja la tasa hacia la que corresponde a su precio
  (curva de E48) en vez de hacia la media. Antes de encender: medirlo en
  el ensayo con la J10-J11 contra la vara de hoy.
- **(E47, 18/10 11:16) Plazo del mie 21/10 14:00: no vender a Rico si el
  premio de la J9 entra el martes.** -432.317 + racha (250.000, mie 21/10
  ~00:10; Pepe la cobra cada 5,0 dias exactos) + premio de la J9 (mar 20/10
  12-17 h, minimo historico 29 pts = 870.000) = +0,7 M o mas. Martes 21:15:
  si no hay «roundFinished» de la J9, vender a Rico (oferta viva hasta el
  21/10 07:00). Y en la caja de cada jornada, contar la racha de Pepe como
  ingreso con fecha (cada 5 dias a las 00:10).
- **(E43, 16/10 11:16) El calendario de la mejora tiene que ver los
  aplazados.** El Rayo-Athletic de la J8 (10/10) no se jugo y
  `laliga_calendar.json` lo da por jugado, sin fecha nueva. Regla: si un
  partido tiene fecha pasada y ningun jugador de los dos equipos tiene un
  partido mas, es un aplazado; cuando aparezca su fecha nueva, esa ronda
  vale dos partidos para esos equipos (Rayo y Athletic; el Athletic
  ademas juega el Levante-Athletic de la J6 el 21/10). Y el premio de una
  jornada con un aplazado pendiente no se cuenta hasta su «roundFinished»
  (la J8 lleva 4 dias sin pagarse; las J1 y J6 se partieron y se pagaron
  en 13 h).
- **(E41, 15/10 11:16) La puja del once segun el precio de la vispera**
  (afina E37/E39). Si el precio no subio: +3 % (se gana el 80 %; nadie
  pelea). Si subio menos de un 2 %: la puja fuerte, +8 a +12 % (76-88 %).
  Si subio un 2 % o mas: el ganador paga +16 % de mediana; ni el +12 %
  gana la mitad: pujar solo si el cambio en el once vale ese +16 %, si no,
  buscar otro que no suba. Las 9 pujas que Pepe ha perdido desde el 25/09
  subian la vispera; las que gano barato, bajaban. Siempre con la caja de
  la jornada en verde (E36/E38).
- **(E39, 14/10 11:16) Confirma E37 con las pujas de Pepe; y el contador
  de pujas ganadas engaña.** De 1 M o mas desde el 25/09 Pepe ha ganado 5
  y perdido 8 (no «59 / 14»: el libro repite filas y cuenta pujas de
  150.000). De las 11 perdidas con importe ganador, a +12 % se habrian
  ganado 8. La puja fuerte (solo once y con la caja de la jornada en
  verde, E37/E38) es lo que falta para que la mejora del once fiche.
- **(E38, 13/10 17:20) Cuenta de la J9 con Luismi Cruz: contar la venta de
  Jutgla a 2,51 M (peor caso), no a 2,9 M.** Su precio hoy es 2.700.000 y
  baja ~1 % al dia; el Computer ofrece entre 0,951 y 1,049 del precio
  (n = 156, nunca por debajo del 90 %). Ofertas cada dos noches (fechas
  pares, ~02:10 de Madrid): ventanas 14/10 y 16/10, ambas antes del
  cierre. Si la del 14/10 llega antes de las 07:00 y Cruz entra, venderla
  ese dia; si no, la del 16/10. Sin el premio de la J8 cobrado, la caja
  queda entre +0,1 y -0,1 M.
- **(E37, 13/10 11:16) Encender la «puja fuerte» (BORDALAS_LA_MEJORA_PUJA_FUERTE)
  solo para fichajes del once, y solo si el sobrecoste cabe en la caja de
  la jornada siguiente.** Con el tablon (105 subastas con pelea): a +1 %
  se gana el 12 %; a +8 %, la mitad; a +12 %, el 68 % (76 % en jugadores
  de 3 M o mas). Pagar +11 % de mas sobre 3-5 M cuesta 330-550 mil EUR;
  un punto por jornada en lo que queda de liga vale ~870 mil de premio y
  ~29 puntos. Nunca para la ronda ni para reventa (E9: pierde dinero).
  Antes de cada puja fuerte: la cuenta de E36 (`lab/caja/cuentas_j9.py`)
  con la puja ganada, en verde antes del cierre.
- **(E36, 12/10 17:20) URGENTE ANTES DEL RESET DEL 13/10: si se gana la
  puja por Gerard Martin (4.989.000), Pepe no llega en verde a la J9.**
  Cuenta con la foto de las 17:10: saldo 659.783, comprometido 9.867.000;
  con Romero + Gerard (+ Moi), aun vendiendo Jutgla y Diego Rico y
  cobrando la J8 (~1,38 M), queda ~-3,4 M; solo con Gerard, ~-2,4 M; con
  Romero sin Gerard, ~+1,0 M. Gerard y Romero no se pueden revender antes
  de jugar (regla de la casa, E14): el agujero lo tendria que tapar otro
  titular. Opciones para el gestor: retirar la puja por Gerard antes de
  las 04:45, o decidir YA a quien se venderia (y con que relevo) para
  estar en verde el 16/10 antes de las 21:00. Y la ronda: su deuda no le
  suma (E9: la limita la oferta, no la caja); que no cuente la deuda de
  la J9.
- **(E26, 08/10) Quitar de la lista de objetivos de E25 a Miguel Roman y a
  Koski (lesionados hoy), y pasar la lista por el estado del dia antes de
  cada puja** (`lab/objetivos/revisa.py`, o la misma regla dentro de la
  orden: estado de Biwenger distinto de ok = no se puja). Miguel Roman,
  rodilla y posible quirofano desde el 29/09, ya ha perdido el 34 %.
- **(E22, 06/10) Vender al Computer cuando NO es una reventa: aceptar si
  la oferta pasa del +3 % sobre el precio; si esta por debajo del precio
  y el precio no baja, esperar a la siguiente.** Las ofertas son tiradas
  independientes (mediana +0,2 %, de -2,8 % a +4,2 %): tras una baja,
  la siguiente mejora 15 de 19; tras una alta, empeora 7 de 7. Si el
  precio baja, aceptar (E3). Si hay plazo de solvencia, mandan las horas.
  Antes de construir: mirar si el motor de ofertas o la orden ya lo hacen.
  n pequeno (32 pares, 9 dias).
- **(E21, 06/10) Quitar la red de las 06:22 (trig_01AVXpLEPRYKWuEDiEquuCdR)
  y no pedir al dueno que mire cron-job.org.** Las vueltas de las 05h y
  06h no existen a proposito (`config/disparos.json`: el latido salta las
  4-7 de Madrid; la ventana son los disparos de 04:45, 04:50 y 07:15; ver
  `zona_de_silencio.py`). Desde el 25/09 han llegado todas las vueltas
  declaradas. La red lanza vueltas descolocadas que no escriben y gastan
  peticiones a Biwenger. Las rutinas solo se tocan desde el chat
  principal.
- **(E14, 02/10) Un fichaje para el once NO se revende antes de jugar con
  nosotros** (salvo lesion larga). Cuatro fichajes de 2,5 M o mas
  vendidos en el paron sin jugar una jornada: -3.308.074 y cero puntos.
  Los de 2,5 M o mas bajan de mediana un 5-8 % cada 11 dias y se compran
  pagando +4-14 %: revender en dias es perder un 10-20 % seguro. Para la
  orden del gestor y para Pepe: si un fichaje para el once se quiere
  cambiar antes de jugar, el cambio tiene que ganar en puntos MAS de lo
  que cuesta en dinero, contado con E7 (~0,6 pts por millon como mucho).
- **(E12, 02/10) Antes del cierre de la J8 (09/10 21:00), un suplente
  que juegue; con el 3-4-3 de hoy, primero un DEFENSA.** Con 11 justos,
  cada jornada hay un 28-57 % de que un titular se sepa fuera antes de
  cerrar el once y esa plaza de 0: ~1-2,5 pts por jornada. Un defensa de
  1-3 M que venga jugando (estado ok, 4+ partidos) da ~2,3 pts cuando
  entra; un medio, ~3,2 (y cubre bajas de medio y delantero cambiando de
  formacion). Condiciones: que el saldo quede >= 0 el 09/10 a las 15:00, y
  comprobar (doctrina 84) que el motor del once cambia al titular «injured/
  doubt» por el suplente en la ultima vuelta antes del cierre.
  - **Afinado por E16 (03/10):** el defensa que se fiche entra de TITULAR
    por Diego Rico (1,5 pts esperados, el peor del once) y Rico pasa a
    suplente. Elegirlo por puntos esperados (media x titularidad >= 2,5),
    no solo por precio: en 7 dias el Computer saco 9 defensas <= 3,2 M con
    titular >= 60 % (Rafita 3,86 por 2,52 M; Puga 2,57 por 1,55 M). Caja
    esperada tras la J8: ~1,8 M (30.000 EUR por punto + racha). Gana
    ~1,2-2,7 pts por jornada.
- **(E4, 29/09) «No se puja por quien tenga una noticia de BAJA en
  FutbolFantasy en las ultimas 72 h», aunque cumpla la rampa.** n=180:
  -2,5 % a 3 dias y -4,3 % a 7; entre los que subian, -3,7 % (n=50). FF
  publica entre las 11 y las 15 h, 16-20 h antes del cambio de las 07:00:
  hay tiempo de quitar la puja. Como: leer el listado de noticias de FF
  por ID en el ojeador de prensa, casar por nombre (sin ambiguos) y
  frenar en la subasta del reset y en el carril, con interruptor apagado,
  guardia, ensayo y canario.
  - **(E6, 29/09 17:30) Contestado al gestor: la guardia de noticias NO
    hace falta para las pujas nuevas.** De 41 BAJA, los filtros de hoy
    frenan 30; de las 11 que se cuelan, 6 son noticias mal leidas y 2
    bajas de verdad (Gaya, Danjuma). El hueco esta en las pujas YA
    PUESTAS (Zubeldia: FF 16 h antes que Biwenger; Pepe lo gano igual).
    Si se hace algo: revisar las pujas vivas antes del reset con la foto
    (estado, `absence` posterior a la puja, la rampa). n=1: es pista.
- **(E8, 30/09 17:25; CORREGIDO por E9 el 01/10) Los viajes cortos para
  el agujero del 09/10 dan POCO:** E8 suponia ganarle la puja a quien la
  gano (casi siempre Pollo17). Ganando solo lo que nadie pelea: mediana
  +0,07 M/semana con 4 M y tope 2 M (+0,12 M con tope 4 M). No cuentan
  para tapar el agujero.
- **(E9, 01/10) Pujar por los que suben a precio + 1 % y NO pelear.** De
  las subastas de jugadores que suben, Pollo17 puja en el 75 %. Las que
  nadie pelea se ganan con precio + 1 % y salen en verde 33 de 33; subir
  la puja para ganarle a Pollo17 empeora (x1,10: ROI mediano -3,1 %).
  Pepe, cuando gana una disputada, paga +14 % sobre el precio. Para
  meterlo: en la subasta y el carril, la puja de REVENTA = precio + 1 %
  (sin escalar por competencia), y en la orden del gestor lo mismo para
  los viajes cortos. Para los fichajes del once (puntos) es otra cosa: ahi
  pagar mas puede valer (Roberto).
- **(E1, 28/09) «Solo se compra para revender lo que SUBIO en el ultimo
  cambio de precio; se vende al Computer el primer dia que BAJA».** Medido
  en 191 compras reales: los que subian, 57/73 verdes y +25,7 M; los que
  no, 24/58 y -0,57 M. Pepe hoy compra 32 de 41 del segundo grupo. Para
  meterlo: en las compras de especulacion (subasta del reset y carril),
  exigir precio(ayer) > precio(anteayer); y en la salida, publicar/aceptar
  la oferta del Computer en cuanto el precio baja un dia. Un interruptor
  para cada mitad, apagados, ensayo y de uno en uno. Antes, comprobar
  (doctrina 84) si la compuerta PRECIO_CAYENDO de la sombra ya hace parte
  de esto: frena lo que BAJA, pero deja pasar lo PLANO, que es donde Pepe
  pierde.
  - **La mitad de VENTA, afinada con E3 (28/09 17:20):** (1) todo lo
    comprado para revender se publica EN CUANTO se compra (sin oferta del
    Computer no hay venta el dia de la bajada); el precio pedido da igual,
    el Computer paga precio +1 a +3 %. (2) En la primera vuelta despues
    del reset en que `price_increment` < 0, se acepta la oferta del
    Computer. Ese mismo dia, no al siguiente: esperar cuesta un 1,8 % mas
    (mediana, n=108) y esperar a una segunda bajada baja los verdes del
    91 % al 78 %. (3) No vender por tiempo ni «cuando frena»: rinden
    menos o empatan. Excepciones que no mide esto: Yamal y los titulares
    del once (no son reventa).
  - **(E5, 29/09) Contestado al gestor: NO usar `salida_del_viaje.py`
    (aceptar la primera oferta >= coste + 1 %).** Con la misma vara y la
    caja de Pepe (2 M), E1 +5,5 M (+2,0 M ya cobrados) contra +0,7 M.
    Vende al primer reset y se pierde la subida. Lo que hay que
    construir es la salida de E3, y se puede reusar de `salida_executor`
    lo que valga (la unica llamada `accept_offer`, los limites de la
    ruta: nunca el once, nunca el ultimo portero, nunca Yamal), cambiando
    la condicion: «el precio bajo hoy» en vez de «oferta >= coste + 1 %».
