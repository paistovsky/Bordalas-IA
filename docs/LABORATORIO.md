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
