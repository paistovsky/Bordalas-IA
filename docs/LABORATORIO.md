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
