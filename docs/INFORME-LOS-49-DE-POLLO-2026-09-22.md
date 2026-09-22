# INFORME — LOS 49 ACIERTOS DE POLLO, Y NUESTROS 9 FALLOS

**Fecha:** 2026-09-22
**Rama:** `medir/los-49-de-pollo`, desde `main`
**Commit:** `78b4050`
**Verja:** a fichero, **172/172 en verde, exit 0**, árbol quieto.
**No se ha empujado. No se ha encendido ningún interruptor. No se ha escrito contra
Biwenger.**

---

## **TU TABLA SE SOSTIENE. AL EURO.**

Rehecha desde cero sobre `rival_intelligence.json` (generado 2026-09-22 06:23), con las
dos cosas que podían haberla roto miradas una por una:

```
                 viajes  en verde       P&L          invertido      ROI    dias  ticket medio
Pollo17            54      91 %    +14.470.717    230.649.083     6,27 %    5,1    4.271.279
Luismi_Haz         37      68 %    +12.220.792    111.585.008    10,95 %    5,5    3.015.811
Pepe Bordalas      24      62 %        +92.375     25.336.638     0,36 %    3,5    1.055.693
```

Los cinco números de cada fila salen idénticos. Sólo dos matices de forma:

- **el «ticket medio» que calculaste es la MEDIA**, no la mediana (las medianas son
  3.353.500 / 2.321.000 / 1.161.010). Las tuyas coinciden al millar con las medias.
- **nuestros días**: mediana 3,5 y no 3,8. Las suyas, 5,1 y 5,5, clavadas.

### Las reemisiones no la rompen

En toda la liga hay **siete** movimientos que la reja de `caja_de_la_liga` —la misma,
importada, no una nueva (doctrina 84)— colapsa como reemisión:

```
Pepe Bordalas   18/09 09:03  SELL_TO_COMPUTER  Lunin                420.200
Luismi_Haz      17/08 03:54  SELL_TO_COMPUTER  Ángel Pérez        3.434.200
Luismi_Haz      04/09 18:34  SELL_TO_COMPUTER  Mikel Rodriguez    2.464.100
Luismi_Haz      04/09 18:38  SELL_TO_COMPUTER  Mikel Rodriguez    2.464.100
Luismi_Haz      04/09 18:38  SELL_TO_COMPUTER  Ayoze              4.983.000
Prinzipote      19/08 07:39  SELL_TO_COMPUTER  Abqar              1.577.100
Prinzipote      19/08 07:39  SELL_TO_COMPUTER  Mendoza              636.300
```

**Las siete son VENTAS, y las siete son huérfanas**: cuando el FIFO llega a la copia, la
cola de ese jugador ya está vacía, así que la copia se cae igual con reja que sin ella.
**Con reja y sin reja la tabla sale exactamente la misma.** Lo comprobé corriendo las dos.

### El FIFO no se puede cruzar

Porque el caso que lo cruzaría **no ocurre ni una vez**: de los ocho managers, **ninguno
llegó a tener dos lotes del mismo jugador a la vez** en toda la temporada. Comprar, vender
y volver a comprar (que sí pasa) no cruza nada.

Lo que sí hay que saber, porque no está en tu tabla: los viajes cerrados son **115 de 458
movimientos**. Lo demás son **98 posiciones abiertas** y **85 ventas sin compra en el
libro** (jugadores que ya tenían antes de que empezara el tablón). Están fuera, y bien
fuera.

---

## LO QUE HAY QUE SABER DE LOS PUNTOS ANTES DE SEGUIR

El campo que pides —«puntos que hizo mientras lo tuvieron»— **no estaba guardado**.
Biwenger publica los últimos cinco partidos de cada jugador en `fitness`, **sin fecha y
sin jornada**. Para saber qué hizo dentro de una ventana hay que fecharlos.

Se fechan cruzando con los partidos de su equipo en el calendario, del más reciente al más
antiguo. **Y se comprueba**: con dos fotos que se solapan (13/09 y 19/09), el fechado
coincide en el **90 % de 541 jugadores**. El 10 % que discrepa se concentra en **cuatro
equipos —Athletic, Alavés, Osasuna y Rayo—, que son los de los partidos aplazados**: el
calendario oficial los fecha donde estaban, no donde se jugaron.

**Esos cuatro no se adivinan.** Sus jugadores salen con los puntos a «no consta» y se
cuentan aparte (doctrina 103). Eso es **21 de los 91** viajes de ellos y **5 de los 24**
nuestros. Todas las tablas de abajo llevan su `n`.

---

## BLOQUE 1 — LA ANATOMÍA DE SUS VIAJES

Cada viaje cerrado, con lo que el jugador hizo dentro. `pts` son los puntos que hizo
mientras lo tenian, `pt` los partidos de su equipo en esa ventana y `jg` los que jugo.
`p.compra` y `p.venta` son el precio de MERCADO esos dias, que no es lo que pagaron ni
lo que cobraron.

### Pollo17 — 54 viajes cerrados

```
jugador         compra       importe venta          cobro   d  beneficio pts pt jg   p.compra    p.venta  qué hizo
Robert Navarro  11/08 07h  2.347.000 15/08 13h  2.398.500   4     51.500   ?  ?  ?          ?          ?  no consta
Óskarsson       11/08 07h  3.407.000 16/08 10h  3.597.000   5    190.000   0  0  0          ?          ?  sin partido
Budimir         11/08 07h 10.877.000 20/08 21h 11.136.100  10    259.100   ?  ?  ?          ? 10.720.000  no consta
Bretones        11/08 07h  1.627.000 27/08 22h  1.755.300  17    128.300   ?  ?  ?          ?  1.680.000  no consta
Urko            11/08 07h  2.257.000 01/09 09h  2.494.700  21    237.700   9  3  3          ?  2.430.000  puntuó
Comesaña        12/08 07h  4.917.000 19/08 09h  4.917.200   7        200  -1  1  1          ?  4.700.000  no puntuó
Puga            13/08 07h  2.207.000 14/08 11h  2.322.900   1    115.900   0  0  0          ?          ?  sin partido
Manu Sánchez    13/08 07h  1.617.000 19/08 09h  1.701.300   6     84.300   1  1  1          ?  1.660.000  puntuó
Toni Martínez   13/08 07h  5.557.000 22/08 09h  5.421.500   9   -135.500   ?  ?  ?          ?  5.330.000  no consta
Batalla         16/08 07h  4.050.007 17/08 08h  4.140.500   1     90.493   ?  ?  ?          ?  4.040.000  no consta
Sergio Canales  16/08 07h  7.647.000 24/08 07h  8.023.400   8    376.400   7  2  2          ?  7.760.000  puntuó
Soler           17/08 07h  5.977.007 22/08 01h  6.237.300   5    260.293   3  1  1  5.950.000  6.030.000  puntuó
Arguibide       18/08 07h    377.000 14/09 08h  2.233.300  27  1.856.300   ?  ?  ?    370.000  2.230.000  no consta
Javi Hernández  19/08 19h  1.250.000 18/09 23h  3.918.400  30  2.668.400  21  6  6  1.010.000  3.800.000  puntuó
Unai Simón      21/08 07h  5.150.000 22/08 18h  5.216.800   1     66.800   ?  ?  ?  5.100.000  5.110.000  no consta
Dumfries        21/08 07h  5.900.000 27/08 00h  6.120.400   6    220.400   8  2  2  5.820.000  5.880.000  puntuó
Foyth           21/08 07h  3.407.000 04/09 08h  3.626.400  14    219.400  10  2  2  3.240.000  3.590.000  puntuó
Agoumé          22/08 07h  2.647.000 01/09 11h  3.483.100  10    836.100  11  2  2  2.580.000  3.320.000  puntuó
Neto            23/08 07h    750.007 24/08 07h    790.600   1     40.593   2  1  1    760.000    770.000  puntuó
David Soria     23/08 07h  5.540.007 28/08 18h  6.250.000   5    709.993  10  1  1  5.540.000  5.700.000  puntuó
Antony          23/08 07h 10.077.000 11/09 10h 11.487.000  19  1.410.000  15  3  3 10.020.000 11.030.000  puntuó
Nsongo          24/08 07h  3.050.007 26/08 09h  3.065.000   2     14.993   3  1  1  3.050.000  2.930.000  puntuó
Oriol Rey       24/08 07h    447.000 28/08 18h    538.200   4     91.200   3  1  1    410.000    540.000  puntuó
Konaté          24/08 07h  5.577.000 31/08 09h  6.103.500   7    526.500   6  2  1  5.570.000  5.890.000  puntuó
Gonzalo Villar  24/08 07h  2.607.000 10/09 01h  3.024.800  17    417.800   9  2  2  2.600.000  3.000.000  puntuó
Álvaro Carreras 26/08 07h  1.177.000 27/08 11h  1.224.000   1     47.000   2  1  1  1.140.000  1.180.000  puntuó
Kochorashvili   26/08 07h  2.207.000 28/08 18h  2.261.400   2     54.400   0  0  0  2.110.000  2.190.000  sin partido
Player 39360    26/08 07h  3.577.000 29/08 10h  3.205.900   3   -371.100   ?  ?  ?  3.050.000  3.110.000  no consta
Mojica          26/08 07h  3.370.000 10/09 08h  3.493.000  15    123.000   7  2  2  2.990.000  3.410.000  puntuó
Guido Rodríguez 28/08 07h  5.110.007 29/08 10h  5.251.500   1    141.493   0  0  0  5.190.000  5.120.000  sin partido
Yangel Herrera  28/08 07h  2.410.007 29/08 23h  2.441.900   2     31.893   3  1  1  2.420.000  2.410.000  puntuó
Cárdenas        28/08 07h  1.777.000 03/09 09h  1.760.300   6    -16.700   ?  ?  ?  1.460.000  1.720.000  no consta
Laporte         28/08 18h  5.450.000 02/09 08h  5.502.700   5     52.700   ?  ?  ?  5.440.000  5.250.000  no consta
Facundo Bernal  29/08 07h  2.517.000 30/08 11h  2.634.500   1    117.500   3  1  1  2.510.000  2.520.000  puntuó
Bartra          30/08 07h  3.337.000 04/09 05h  3.447.600   5    110.600   0  0  0  3.070.000  3.300.000  sin partido
Enes Ünal       30/08 07h  5.007.000 14/09 07h  5.260.300  15    253.300   7  3  3  4.380.000  5.040.000  puntuó
Mandi           31/08 07h  2.570.000 11/09 10h  2.855.900  11    285.900   5  1  1  2.460.000  2.800.000  puntuó
Vinícius Jr     01/09 07h 17.540.007 06/09 10h 17.633.400   5     93.393   4  1  1 17.540.000 17.220.000  puntuó
Pubill          04/09 07h  6.360.006 07/09 08h  6.709.300   3    349.294   2  1  1  6.390.000  6.430.000  puntuó
Riki Rodríguez  04/09 07h    277.000 15/09 13h    619.100  11    342.100   3  2  1    270.000    590.000  puntuó
Bardeli         05/09 07h  1.877.000 21/09 07h  2.337.000  16    460.000   7  2  2  1.730.000  2.290.000  puntuó
Ratkov          06/09 07h  1.447.000 08/09 09h  1.273.100   2   -173.900   0  1  0  1.390.000  1.310.000  NO JUGÓ
Gerard Moreno   06/09 07h  6.450.007 10/09 01h  6.780.300   4    330.293   0  0  0  6.430.000  6.500.000  sin partido
Camavinga       06/09 07h  1.777.000 11/09 10h  1.985.900   5    208.900   0  0  0  1.790.000  1.940.000  sin partido
Ilaix Moriba    09/09 07h  1.940.007 10/09 08h  2.000.900   1     60.893   0  0  0  1.940.000  1.930.000  sin partido
Noubi           09/09 07h  2.677.000 18/09 18h  2.763.400   9     86.400   3  2  1  2.590.000  2.720.000  puntuó
Pépé            09/09 07h 11.207.000 19/09 18h 11.795.200  10    588.200   4  2  1 11.200.000 11.120.000  puntuó
Gordon          10/09 07h 12.707.000 17/09 00h 12.944.500   7    237.500   2  2  1 11.910.000 12.320.000  puntuó
Berenguer       12/09 07h  3.187.000 13/09 13h  3.370.000   1    183.000   ?  ?  ?  3.200.000  3.230.000  no consta
Marcos Alonso   12/09 07h  3.677.000 17/09 07h  3.693.200   5     16.200   3  1  1  3.590.000  3.530.000  puntuó
Marcos Llorente 14/09 07h  5.677.000 15/09 13h  5.700.000   1     23.000   0  0  0  5.670.000  5.600.000  sin partido
Hjulmand        14/09 07h  4.877.000 20/09 20h  4.895.700   7     18.700   2  1  1  4.640.000  4.750.000  puntuó
Dieng           16/09 07h  1.077.000 20/09 21h  1.004.800   5    -72.200   0  0  0  1.050.000    970.000  sin partido
Oyarzabal       20/09 07h 10.120.007 21/09 07h 10.271.800   1    151.793   0  0  0 10.120.000 10.060.000  sin partido
```

### Luismi_Haz — 37 viajes cerrados

```
jugador         compra       importe venta          cobro   d  beneficio pts pt jg   p.compra    p.venta  qué hizo
Lo Celso        10/08 07h  4.263.000 18/08 02h  3.993.000   8   -270.000   0  0  0          ?  3.940.000  sin partido
Gorosabel       10/08 07h    340.001 20/08 18h    327.400  10    -12.601   0  1  0          ?    330.000  NO JUGÓ
Marcos Alonso   12/08 07h  3.686.000 28/08 18h  3.921.900  16    235.900   5  2  2          ?  3.990.000  puntuó
Guedes          13/08 07h  6.401.000 16/08 06h  5.758.300   3   -642.700   0  0  0          ?          ?  sin partido
Aleñá           14/08 07h  1.023.000 18/08 02h  1.066.500   4     43.500   ?  ?  ?          ?    990.000  no consta
Laporte         14/08 07h  5.752.000 19/08 06h  5.628.000   5   -124.000   ?  ?  ?          ?  5.540.000  no consta
Hancko          14/08 07h  3.900.000 15/09 05h  4.213.500  32    313.500  21  5  5          ?  4.030.000  puntuó
Isi Palazón     15/08 07h  3.726.000 21/08 01h  3.641.600   6    -84.400   ?  ?  ?          ?  3.630.000  no consta
Oluwaseyi       16/08 07h    425.000 19/08 04h    391.600   3    -33.400   0  1  0          ?    380.000  NO JUGÓ
Yeboah          16/08 07h    290.001 20/08 18h    351.700   4     61.699   ?  ?  ?          ?    350.000  no consta
Nico Williams   16/08 07h  9.151.000 25/08 04h  9.365.000   9    214.000   ?  ?  ?          ?  8.920.000  no consta
Almeida         16/08 07h    485.000 26/08 05h    655.300  10    170.300   0  2  0          ?    630.000  NO JUGÓ
Gerard Martín   16/08 07h  4.555.000 10/09 06h  5.521.200  25    966.200  18  4  3          ?  5.360.000  puntuó
Sierra          16/08 07h  1.056.000 15/09 19h  3.909.800  31  2.853.800  21  4  4          ?  3.780.000  puntuó
Mikel Rodriguez 19/08 07h    836.000 04/09 18h  2.464.100  16  1.628.100   ?  ?  ?    650.000  2.510.000  no consta
Pape Gueye      19/08 07h  7.700.001 08/09 06h  9.250.500  20  1.550.499  13  3  3  7.700.000  8.850.000  puntuó
Kevin Sánchez   20/08 07h    152.000 04/09 18h    152.700  15        700   0  2  0    150.000    150.000  NO JUGÓ
Redondo         23/08 07h    316.000 02/09 16h    349.800  10     33.800  -1  2  1    270.000    350.000  no puntuó
Laporte         25/08 07h  5.470.000 28/08 18h  5.450.000   3    -20.000   ?  ?  ?  5.430.000  5.440.000  no consta
Nico Serrano    25/08 07h    150.001 04/09 18h    142.700  10     -7.301   ?  ?  ?    150.000    150.000  no consta
Brugué          27/08 07h    311.000 28/08 18h    700.000   1    389.000   0  0  0    310.000    440.000  sin partido
Chust           29/08 07h  2.131.000 31/08 00h  2.150.100   2     19.100   0  0  0  2.130.000  2.120.000  sin partido
Francho         29/08 07h  1.056.000 01/09 07h  1.065.200   3      9.200   2  1  1  1.020.000  1.020.000  puntuó
Gerenabarrena   29/08 07h    800.000 18/09 19h  3.252.100  21  2.452.100   ?  ?  ?    600.000  3.230.000  no consta
Óskarsson       30/08 07h  2.780.001 04/09 18h  3.052.300   5    272.299   3  1  1  2.750.000  3.080.000  puntuó
Mikautadze      31/08 07h 10.660.001 07/09 05h 10.774.200   7    114.199   3  1  1 10.700.000 10.570.000  puntuó
Ejuke           31/08 07h  2.321.000 13/09 05h  3.366.700  13  1.045.700   5  2  2  2.090.000  3.240.000  puntuó
Rubén Sánchez   05/09 07h    377.000 10/09 06h    375.700   5     -1.300   0  1  0    330.000    350.000  NO JUGÓ
Almeida         05/09 07h  1.321.000 11/09 07h  1.676.700   6    355.700   4  1  1    990.000  1.660.000  puntuó
Roro Riquelme   07/09 07h  4.243.000 11/09 07h  4.469.200   4    226.200   0  0  0  4.240.000  4.390.000  sin partido
Bryan Zaragoza  08/09 07h  4.526.000 11/09 06h  4.508.100   3    -17.900   0  0  0  4.440.000  4.370.000  sin partido
Parrott         13/09 07h  6.512.000 18/09 05h  6.284.200   5   -227.800   6  2  1  6.450.000  6.030.000  puntuó
Giménez         14/09 07h  3.331.000 18/09 19h  3.386.800   5     55.800   2  1  1  3.100.000  3.300.000  puntuó
Jonathan David  16/09 07h  7.842.000 18/09 18h  8.400.000   2    558.000  13  1  1  7.820.000  7.970.000  puntuó
Aleñá           17/09 07h    750.002 21/09 05h    739.400   4    -10.602   ?  ?  ?    750.000    730.000  no consta
Pepelu          19/09 07h  2.596.000 21/09 14h  2.696.500   2    100.500   0  0  0  2.590.000  2.570.000  sin partido
Szczęsny        19/09 07h    351.000 21/09 14h    354.000   2      3.000   0  0  0    320.000    320.000  sin partido
```

### Y la tabla que contesta la hipótesis

Partiendo sus **91 viajes** por lo que el jugador hizo **mientras lo tenían**:

```
                                 viajes   en verde   ROI mediano   beneficio mediano   mercado movió
puntuó                              43       98 %        5,49 %            253.300          —
  de ellos, 2-4 pts por partido     25      100 %        4,67 %                             +3,48 %
  de ellos, 4-6 pts por partido     12      100 %       12,56 %                            +12,31 %
  de ellos, 6+ pts por partido       5       80 %        9,44 %                             +2,40 %
no puntuó (jugó y sumó 0 o menos)    2      100 %        5,35 %             17.000          —
HABIA PARTIDO Y NO LLEGO A JUGAR     6       33 %       -2,03 %             -6.950          +0,00 %
no hubo partido en la ventana       19       79 %        2,77 %            100.500          -0,47 %
no consta (los 4 equipos)           21       62 %        2,19 %             52.700          —
```

**Las filas no se parecen: tu hipótesis es cierta, y con un matiz que la mejora.**

- **98 % en verde** cuando el jugador puntuó. **33 %** cuando había partido y no jugó.
- **Una sola fila pierde dinero en toda su temporada**, y es la del que no jugó.
- Y la columna que lo explica: **para el que no jugó, el mercado se movió +0,00 %.** Para
  los que jugaron, entre +2,40 % y +12,31 %.

El matiz: hay una cuarta fila que tu tabla no preveía —**«no hubo partido»**, 19 viajes—
y es grande, porque la tenencia mediana son 5,1 días y las jornadas son semanales. Esos
salen 79 % en verde con la mitad de ROI. Cobran la prima del Computer y poco más.

**Pero no es «compran al que va a puntuar mucho».** Mira la columna del mercado: la banda
de 2-4 puntos por partido ya está al 100 % en verde. **No hace falta que sea una estrella.
Hace falta que JUEGUE.**

---

## BLOQUE 2 — NUESTROS NUEVE FALLOS

### Primero, la respuesta, porque no es ninguna de las tres que proponías

El P&L de un viaje se parte en tres trozos que suman exacto:

```
                                 nosotros        Pollo17      Luismi_Haz
prima de entrada (pagado de más) -1.036.806     -4.449.076     -1.552.006
MOVIMIENTO DEL MERCADO             -310.000    +10.690.000     +7.860.000
prima del Computer al vender     +1.097.413     +6.831.400     +2.221.000
-----------------------------------------------------------------------
total                              -249.393    +13.072.324     +8.528.994
(n con precio en las dos puntas)         22             43             23
```

**Nuestra prima del Computer casi cubre nuestra prima de entrada.** Lo que nos separa de
ellos es **el movimiento del mercado, y nada más.** Doctrina 100 —el margen del vendedor
no es tu beneficio— y doctrina 105: nuestros −249.393 son lo que queda de dos números
grandes.

### Los nueve, uno a uno

```
jugador        perdido   días  pts  part  jugó   prima al comprar   mercado  ¿subió tras vender?
Djené         -538.901   31,1   14    5     5         +10,0 %      -17,8 %   -0,6 % a 3 días
Bigas         -357.301    3,8    3    1     1         +10,0 %      -11,1 %   -4,9 % / -9,2 % a 7d
Trent         -223.500    4,7    4    1     1          +0,0 %       -8,3 %   -3,2 % a 3 días
Zubeldia      -221.001   26,8   11    6     5         +10,0 %      -11,2 %   -7,8 % / -13,2 % a 7d
Kiko Femenía   -70.925    4,2    2    1     1          +4,2 %       -9,3 %  -13,1 % / -20,6 % a 7d
Maffeo         -42.850    1,1    0    0     0          +0,3 %       -1,8 %   -1,2 % a 3 días
Drkusic        -36.376    1,0    0    0     0          +0,2 %       -5,4 %   -6,6 % a 3 días
Balde          -25.501    2,3    6    1     1          +0,3 %       -5,0 %   -2,6 % a 3 días
Lunin             -800    1,1    0    0     0          +0,2 %       +0,0 %   -2,4 % a 3 días
```

### ¿Compra, plazo o precio de entrada?

- **Fallo de COMPRA («alguien que no iba a jugar»): CERO de nueve.** Seis de los nueve
  **puntuaron** mientras los teníamos —Djené 14, Zubeldia 11, Balde 6, Trent 4, Bigas 3,
  Kiko 2—. Los otros tres no tuvieron partido en la ventana.
- **Fallo de PLAZO («vendimos antes de la subida»): CERO de nueve.** En los nueve, el
  precio **siguió cayendo** después de vender: −0,6 %, −4,9 %, −3,2 %, −7,8 %, −13,1 %,
  −1,2 %, −6,6 %, −2,6 %, −2,4 % a tres días. Vender estuvo bien.
- **Queda el precio de entrada, y es donde está.** Pero se parte en dos cosas distintas,
  y conviene no mezclarlas:
  - **cuatro los pagamos caros**: Djené, Bigas y Zubeldia a **+10 %** sobre mercado, Kiko
    a +4,2 %. Con el mercado cayendo un 11 %, Bigas necesitaba que subiera un 21 % para
    empatar. **Eso ya está arreglado**: hoy la prima máxima de puja es +0,25 %.
  - **cinco los pagamos bien y bajaron igual** (Trent +0,0 %, Balde +0,3 %, Maffeo,
    Drkusic, Lunin +0,2 %). Ésos no son un problema de precio: **son un problema de
    dirección.** Siete de los nueve se compraron con el precio **ya bajando** —Bigas
    −2,44 %/día, Drkusic −2,22 %, Balde −1,61 %, Maffeo −1,18 %, Trent −0,83 %, Djené
    −0,45 %—.

**Y ésta es la pieza que contradice el bloque 1 y hay que decirla:** nuestros viajes en
los que el jugador **sí puntuó** salen **40 % en verde y ROI mediano −3,68 %**, cuando los
suyos salen 98 % y +5,49 %. Puntuar no nos sirvió. La diferencia está en **cuánto** puntuó
por partido: Djené 2,80 por partido, Zubeldia 2,20, Kiko 2,00 —defensas caros que rinden
poco— contra Javi Hernández 3,50, Sierra 5,25, Antony 5,00.

---

## BLOQUE 3 — ¿EL PRECIO O LA CALIDAD?

**La calidad manda. El billete no multiplica: DIVIDE el ROI y multiplica los euros.**

Calidad = **puntos por partido jugado antes de la compra**, que es uno de los tres que me
diste y el único de los tres que está guardado con fecha. Corte en **4,0**, que es donde
los datos lo ponen. `hierarchy_value` y `starter_probability` **no** existen guardados
para esas fechas —el tablero de FutbolFantasy sólo tiene los 142 del mercado de hoy— así
que no se usan aquí (doctrina 103: no es que no se sepa, es que no se preguntó).

```
                        candidato FLOJO              candidato BUENO
                     (< 4 pts por partido)       (>= 4 pts por partido)
ticket < 1,5 M      n=8    88 %   +2,43 %*     n=4   100 %  +169,28 %*
ticket 1,5 - 4 M    n=11  100 %   +3,23 %*     n=8   100 %    +8,78 %*
ticket > 4 M        n=2   100 %   +0,95 %*     n=17   88 %    +5,12 %

                    sin estrenar (0 partidos)     no consta (4 equipos)
ticket < 1,5 M      n=6    33 %   -2,03 %*     n=7    71 %   +21,28 %*
ticket 1,5 - 4 M    n=7   100 %   +5,58 %*     n=6    50 %    +0,63 %*
ticket > 4 M        n=7    71 %   +3,74 %*     n=8    62 %    +1,13 %*

  * = menos de MIN_SAMPLES (12) casos. La celda se marca, no se rellena.
```

Sólo una celda llega a los 12 de la casa. Así que la respuesta sale de los **márgenes**,
que sí tienen `n`:

```
por CALIDAD (n=91)          n    verde   ROI med          P&L
  BUENO                    29     93 %    5,49 %   +16.210.857
  FLOJO                    21     95 %    3,14 %    +1.715.371
  sin estrenar             20     70 %    4,64 %    +2.447.292
  no consta                21     62 %    2,19 %    +6.317.989

por TICKET (n=91)           n    verde   ROI med          P&L
  < 1,5 M                  25     72 %    5,41 %   +12.735.188
  1,5 - 4 M                32     91 %    4,94 %    +5.605.278
  > 4 M                    34     79 %    2,29 %    +8.351.043
```

**Cruzado, que es lo que decide:**

```
dentro de cada tramo de ticket, ¿separa la calidad?     SÍ, SIEMPRE
  < 1,5 M    BUENO 169,28 %  contra  FLOJO  2,43 %
  1,5 - 4 M  BUENO   8,78 %  contra  FLOJO  3,23 %
  > 4 M      BUENO   5,12 %  contra  FLOJO  0,95 %

dentro de cada nivel de calidad, ¿separa el billete?    SÍ, AL REVÉS
  BUENO      169,28 %  ->  8,78 %  ->  5,12 %   (baja al subir el ticket)
  FLOJO        2,43 %  ->  3,23 %  ->  0,95 %   (plano, y malo)
```

**Tu apuesta gana, con una corrección:** la calidad manda en los tres tramos. El billete
no multiplica el rendimiento — lo **reduce**. Lo que el billete grande multiplica son los
**euros por operación**: los 17 viajes BUENO de más de 4 M dan 6.861.864 €, y los 4 viajes
BUENO de menos de 1,5 M dan 6.253.300 € con **la cuarta parte del capital**.

### Y el aviso, porque el efecto podría ser cinco fichajes

**El 43 % de su P&L son cinco viajes**, y el 65 % son diez de noventa y uno:

```
Luismi  Sierra           16/08->15/09   1.056.000 ->  3.909.800   31d  +270 %  21 pts
Pollo   Javi Hernández   19/08->18/09   1.250.000 ->  3.918.400   30d  +214 %  21 pts
Luismi  Gerenabarrena    29/08->18/09     800.000 ->  3.252.100   21d  +307 %       ?
Pollo   Arguibide        18/08->14/09     377.000 ->  2.233.300   27d  +492 %       ?
Luismi  Mikel Rodriguez  19/08->04/09     836.000 ->  2.464.100   16d  +195 %       ?
```

Ticket medio de los cinco: **863.800 €**. Tenencia mediana: **27 días** contra 5,1 del
conjunto. **Eso no es la subasta del reset: es la doctrina 8 —el recién ascendido barato
que se dispara— comprada y aguantada un mes.**

**Quitando los cinco, el efecto de la calidad sigue en pie**: BUENO **5,33 %** (n=27)
contra FLOJO **3,14 %** (n=21). No son sólo los cinco. Pero los cinco son la mitad del
dinero.

### Tu contradicción, resuelta

```
Pollo17 por encima de 4 M       n=22   95 % verde   ROI mediano  +2,58 %   +6.024.345
nosotros por encima de 1,5 M    n=9    33 % verde   ROI mediano  -2,57 %   -1.038.783
nosotros por debajo de 1,5 M    n=15   80 % verde   ROI mediano  +2,28 %   +1.131.158
```

**Sus operaciones grandes son las MENOS rentables de su libro** (2,58 % frente a 6,27 % de
media). Son seguras y finas. **Subir el billete no era el camino**, y nuestras nueve por
encima de 1,5 M no perdieron por grandes: perdieron por comprar a candidatos flojos, con
prima y con el precio cayendo.

---

## BLOQUE 4 — EL MOMENTO: NO HAY DIFERENCIA

```
días entre la compra y el siguiente partido del jugador
  Pollo17     n=53   p25 1,4   mediana 2,6   p75 5,0   max 13,5
  Luismi_Haz  n=37   p25 1,6   mediana 2,6   p75 6,5   max 11,6
  NOSOTROS    n=24   p25 1,5   mediana 2,6   p75 4,2   max  5,6

días entre la venta y el partido anterior
  Pollo17     n=49   p25 0,5   mediana 1,7   p75 2,6
  Luismi_Haz  n=33   p25 1,4   mediana 2,4   p75 4,2
  NOSOTROS    n=24   p25 1,3   mediana 2,4   p75 3,4

hora de la compra
  Pollo17     52 de 54 a las 07:xx   (96 %)
  Luismi_Haz  37 de 37 a las 07:xx  (100 %)
  NOSOTROS    23 de 24 a las 07:xx   (96 %)

días entre la compra y el reset siguiente
  los tres: mediana 1,0 — porque compran EN el reset
```

**La mediana de días al siguiente partido es 2,6 para los tres. Idéntica.** Y los tres
compran en el reset de las 07:00, que es donde Biwenger resuelve las pujas: no es una
elección, es la mecánica.

**No hay regla de una línea aquí.** Comprar la víspera (a menos de 2 días del partido) les
va algo mejor —Pollo 4,92 % contra 3,48 %; Luismi 5,68 % contra 1,07 %— y a nosotros algo
peor (0,61 % contra 2,37 %), con `n` de 10 a 34. **No aguanta un umbral.**

---

## BLOQUE 5 — LA REGLA

### `BORDALAS_REVENTA_SOLO_SI_JUEGA` — apagada

> **No se compra para revender a quien no consta que vaya a jugar.**

`src/analysis/la_regla_de_compra.py`. **Una regla, ningún número nuevo.**

**De dónde sale:** de la única fila que pierde dinero en los 91 viajes de ellos —«había
partido y no jugó», 33 % en verde, ROI mediano −2,03 %— y de la columna que la explica:
**para el que no juega, el mercado se mueve +0,00 %**. Y el movimiento del mercado es de
donde sale todo el beneficio de un viaje (la tabla de tres trozos del bloque 2).

**Por qué no escribe un umbral nuevo (doctrina 84):** la pregunta «¿va a jugar?» ya está
contestada en `deployment.roster_fill_veto` —sin pronóstico no se ficha a ciegas, por
debajo del 40 % no, un descarte de su equipo no, el que no puede jugar tampoco—. Ese veto
sólo se le aplica hoy a la vía de **plantilla**. La regla **lo llama**, no lo reescribe.
Lo único que aporta es **aplicárselo a la reventa**, que hoy no lo mira. Hay guardia de
que las dos digan literalmente lo mismo.

**El 40 % que recibe, medido (doctrina 90).** No tenía medición propia. Cruzando los 142
del tablero de FutbolFantasy del 21/09 con quién jugó de verdad (n=114 cruzables):

```
corte    acierta   de los que pasan, jugaron   pasan
 10 %      82 %                       82 %      105
 30 %      81 %                       84 %       96
 40 %      81 %                       89 %       84
 50 %      77 %                       92 %       74
 60 %      67 %                       95 %       56
```

El 40 está en la meseta del acierto y es donde la pureza da el salto (84 % → 89 %).
Subirlo compra pureza pagando acierto y volumen. **No hace falta moverlo.**

### Hacia atrás, sobre nuestra temporada

La regla usa el **pronóstico**; para el retrotest sólo hay la **señal realizada** que se
sabía el día de la compra: **¿jugó el último partido de su equipo?** Es la misma pregunta
con el dato de después, y separa igual:

```
                                n   verde   ROI med           P&L
ellos, jugó el último          49    96 %   +5,06 %   +17.998.428
ellos, NO jugó el último        4    50 %   +1,06 %      +336.600
nosotros, jugó el último        5    40 %   -2,57 %      -310.396
nosotros, NO jugó el último    12    58 %   +0,55 %      -475.115
```

**Qué NO habríamos comprado, con nombres y fechas:**

```
20/08  Bigas          2.288.001 ->  1.930.700     -357.301
13/09  Trent          2.760.000 ->  2.536.500     -223.500
17/09  Drkusic        1.292.476 ->  1.256.100      -36.376
15/09  Balde          1.604.001 ->  1.578.500      -25.501
17/09  Lunin            421.000 ->    420.200         -800
15/09  Paco Cortés      150.376 ->    151.200         +824
18/09  Esquivel         150.376 ->    151.200         +824
18/09  Marcão           150.376 ->    151.500       +1.124
12/09  Fortuño          150.376 ->    153.800       +3.424
18/09  Barzic           150.376 ->    156.400       +6.024
12/09  Diego Conde      240.601 ->    250.700      +10.099
18/08  Castrín        1.200.001 ->  1.346.045     +146.044
-------------------------------------------------------------
doce viajes                                       -475.115
```

**Qué habríamos ganado: el P&L de la temporada pasa de +92.375 a +567.490 €.** Seis veces.
Cinco de los nueve fallos se paran (Bigas, Trent, Drkusic, Balde, Lunin: −643.478 €). El
precio es Castrín, +146.044, y siete micro-ganancias del suelo que suman 22.343.

**Y donde muerde de verdad: las seis compras del 21/09.** Preguntándole a la regla con el
tablero de FutbolFantasy de esa misma tarde:

```
Yeray         1.624.051   no está en el tablero        PARA  sin pronóstico
Diaby           150.376   no está en el tablero        PARA  sin pronóstico
Guevara         160.401   30 % · Reserva               PARA  solo 30 % de titularidad
Aihen           220.551   20 % · Reserva               PARA  solo 20 %
Guliashvili     180.451   10 % · Revulsivo             PARA  solo 10 %
Van Oevelen     230.576    5 % · Reserva               PARA  solo 5 %
--------------------------------------------------------------------------
                            SEIS de seis, 2.566.406 EUR
```

### Lo que la regla NO arregla, dicho aquí

**Cuatro de los nueve fallos sí jugaron** —Djené, Zubeldia, Kiko Femenía y Maffeo, 873.677
€ juntos— y la regla los deja pasar. Ésos perdieron por la prima de entrada (+4 % a +10 %)
y por comprar con el precio ya cayendo. La prima ya está cerrada en +0,25 %; el freno de
la dirección **ya existe** en `market_rate_gate` desde el 07/09, y por eso no hay aquí una
segunda regla (doctrina 84). Lo que falta es que la **cesta del reset** y el **carril** lo
miren, y eso es otro encargo.

### La guardia

`test_la_regla_de_compra_v1`, **nueve pruebas**, en la verja. La que pediste:

**`test_la_regla_de_compra_mira_si_va_a_jugar`** — con el interruptor puesto, un candidato
sin pronóstico de titularidad no genera puja de reventa. **Muerde si en el caso todos los
candidatos son titulares** (no habría nada que frenar) **y también si no hay ningún
titular** (entonces no probaría que la regla distingue, sólo que apaga). Comprueba además
que el titular **sigue** pujando.

Las otras ocho: que apagada no cambie ni una puja; que el motivo se llame `NO_VA_A_JUGAR`
y no «no hay cesta» (doctrina 87); que el umbral sea el de la casa —ejercitando
`roster_fill_veto` y comparando, no leyendo la constante—; que `lectura_del_estado` lleve
los tres campos que la regla mira; que la forma no cambie con los datos; que la regla no
lea el mundo; y **las dos piezas de las que cuelga tu tabla**: la reja de reemisiones y el
FIFO.

---

## LO QUE SE HA TOCADO

```
scripts/los_viajes.py                         NUEVO   emparejar, fechar los puntos, precios
src/analysis/la_regla_de_compra.py            NUEVO   la regla, apagada
src/analysis/test_la_regla_de_compra_v1.py    NUEVO   9 guardias
src/analysis/la_subasta.py                            la regla en la cesta + 3 campos
src/telemetry/dashboard_state.py                      el recuento en pantalla
scripts/run_validation_gate.py                        la guardia en la verja
```

`scripts/los_viajes.py` **no decide nada**: lee los ficheros que el ciclo ya guarda y
devuelve listas. Está en el repo para que estos números se puedan volver a sacar sin
creerme a mí.

---

## LO QUE NO SE HA HECHO, Y POR QUÉ

| | por qué |
|---|---|
| **Ni una escritura contra Biwenger** | lo prohíbe el encargo |
| **Ningún interruptor encendido** | la regla nace apagada. `BORDALAS_CESTA_SOLO_EL_SUELO` **no se ha tocado**, y esta medición dice que está del revés: por debajo de 1,5 M ellos hacen 12.735.188 € |
| **El workflow, intacto** | lo prohíbe el encargo |
| **Ninguna regla de compra ni de venta cambiada** | el bloque 5 **propone**: con el interruptor quitado el sistema se comporta exactamente como ayer, y hay guardia de eso |
| **La reventa sigue cerrada** | `BORDALAS_SIN_SUBASTA=1`, que puso el dueño |
| **Ningún índice de calidad nuevo** | se usa «puntos por partido antes de comprar», que es uno de los tres que diste |
| **No se ha tocado** `MAX_SINGLE_SPECULATION_PERCENT`, `MAX_SAFE_DEBT`, el suelo de cobro, `MIN_WIN_PROBABILITY`, `MAX_PROJECTED_DAILY_RATE`, `PUEDEN_ENCERRARLO`, `PRIMA_MAXIMA_DE_PUJA`, `VENTANA_MINUTOS` | lo prohíbe el encargo |
| **No se ha empujado** | «Tú no empujas» |
| **La regla no se ha enganchado al CARRIL** | es la segunda puerta de reventa —16 de las 56 pujas de nuestro libro salen de ahí— y sus filas tampoco llevan `starter_probability`. Cerrarla cuesta una clave más en la copia de candidatos y tres líneas. **No se ha hecho** porque el encargo pide UNA regla entregada apagada, y engancharla en dos sitios sin poder medir el segundo sería media cosa |
| **No se ha simulado qué habríamos comprado EN LUGAR de los doce** | doctrina 101: una lista que no puja no mide lo que pujarías. Lo que sí se puede afirmar es lo que esos doce costaron |
| **No se han recuperado los cuatro equipos aplazados** | el calendario oficial los fecha donde estaban. Recuperarlos pide un calendario con las fechas REALES de los aplazados, que no tenemos |

---

## DOS COSAS QUE NO PEDISTE Y CAMBIAN EL PLAN

**1. Las ocho compras del suelo (< 300.000 €) dan 28.867 € entre las ocho.** Mediana
2.274 €. Un punto de la liga vale 30.000: **las ocho juntas valen 0,96 puntos**, y ocupan
ocho fichas. La cesta del suelo no es un negocio pequeño: es ruido que cuesta plantilla.

**2. Su negocio grande no es la subasta.** Los cinco viajes que hacen el 43 % de su dinero
se compraron a **863.800 € de media y se aguantaron 27 días**, mientras la tenencia
mediana del conjunto son 5,1. Nuestro horizonte de reventa son 3-5 días. **Mientras
vendamos a los tres días no podemos hacer ninguno de esos cinco viajes**, compremos lo que
compremos.
