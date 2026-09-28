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

## Experimentos

(el laboratorio los apunta aqui, el mas reciente arriba: fecha, hipotesis,
datos y n, resultado, veredicto)

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
