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

## Listo para el plan

(ideas que han ganado con datos y estan listas para que un turno del gestor
las meta en Pepe; al pasarlas, se mueven al plan de EL-PUESTO-DE-MANDO.md)
