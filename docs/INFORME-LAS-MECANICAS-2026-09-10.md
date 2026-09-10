# Las mecánicas del juego — informe

**Fecha:** 10/09/2026 · **Verja:** 104/104 · **Push:** NO
**Llamadas nuevas a Biwenger:** ninguna. Todo sale del tablón, de las 89 fotos y
del histórico de precios.
**Escrituras:** ninguna. **Umbrales movidos:** ninguno.

Se re-ejecuta entero con `python -m scripts.las_mecanicas_del_juego`.

---

## BLOQUE 1 — La economía. El de más valor, y confirma tu sospecha

### 30.000 por punto: confirmado, y lo publica Biwenger

No hay que inferirlo. Cada `roundFinished` del tablón trae `points` **y** `bonus`
por manager. **23 de 35 filas cuadran a 30.000 exactos.** Las otras 12 son las
del extra, y el extra tiene explicación.

### Qué son los escalones: **el puesto en la jornada**

No es la racha, no son las operaciones y no es ganar.

```
puesto   extras vistos
1        0 x5          <- los cuatro primeros
2        0 x5             no cobran extra NUNCA
3        0 x5
4        0 x5
5        0 x1, 100.000 x4
6        0 x1, 250.000 x4
7        0 x1, 500.000 x4
```

**Puesto 5 → +100.000. Puesto 6 → +250.000. Último → +500.000.** Cuatro de las
cinco jornadas, exacto. La excepción es la Jornada 1, donde no cobró extra nadie
— probablemente porque es la primera.

Es un **pago de consolación**, y más grande cuanto peor lo hagas. Manzagool ha
sido último las cuatro veces: **+2.000.000**, casi la mitad de lo que ha cobrado
por puntos.

**La `dailyStreak` que mencionabas es otra cosa distinta.** El tablón la publica
en eventos `bonus` aparte: tres vistos, todos de 250.000 — Prinzipote 02/09,
Pollo 02/09 y 07/09. No tiene relación con la jornada.

### Puntos contra la rueda: **los puntos dan 8,4 veces más**

Aquí hay una corrección importante de método. «Ventas − compras» es **caja, no
beneficio**: lo comprado sigue en la plantilla. Lo único cobrable como ganancia
es un jugador **comprado y vendido**. Contando solo esos viajes cerrados:

| manager | POR PUNTOS | viajes | BENEFICIO | por viaje |
|---|---:|---:|---:|---:|
| Pollo17 | 7.170.000 | 36 | 5.700.524 | 158.347 |
| **Pepe Bordalás** | **6.550.000** | **6** | **781.654** | **130.275** |
| Luismi_Haz | 6.520.000 | 24 | 4.512.794 | 188.033 |
| Mex | 6.370.000 | 0 | 0 | — |
| DiosMande | 5.410.000 | 2 | 750.400 | 375.200 |
| Manzagool | 5.240.000 | 12 | **−2.879.680** | −239.974 |
| Prinzipote | 5.020.000 | 0 | 0 | — |

**Para nosotros, los puntos dan 8,4 veces lo que la rueda.** Y no es que
nosotros comerciemos poco: **ni el trader más activo de la liga** —Pollo, 36
viajes cerrados— saca de comerciar lo que saca de puntuar. Manzagool ha
*perdido* 2,9 M comerciando.

> Si el once es el motor económico principal, dejar puntos en el banquillo no
> cuesta solo posición: cuesta dinero. **Esa consecuencia no la he tocado**, como
> pediste.

**Dos errores que corregí por el camino, porque cambiaban los números:**

1. Estaba sumando `playerMovements` —traspasos **reales** entre clubes de
   Primera— como si fueran operaciones de la liga. Por eso «Sevilla» y
   «Atlético» aparecían como managers con cientos de millones.
2. **El tablón repite operaciones.** Los `event_id` son únicos, pero la misma
   compra aparece dentro de eventos distintos: **169 operaciones de subasta, y
   solo 144 distintas**. Sin deduplicar, nuestras compras salían 76,8 M cuando
   son 49,2 M.

---

## BLOQUE 2 — El tope de plantilla: **21 fichas como suelo**

| manager | plantilla más grande vista |
|---|---:|
| **Pollo17** | **21** |
| Pepe Bordalás | 17 |
| Prinzipote | 17 |
| Luismi_Haz | 16 |
| Mex | 14 |
| Manzagool | 13 |
| DiosMande | 11 |

**El tope real es 21 o más.** Nadie ha tenido más, así que 21 es un suelo, no el
techo. Lo que usamos hoy —«la plantilla más grande de la liga menos la nuestra»—
es una regla distinta y más conservadora; con 13 fichas nuestras y un tope de 21
tendríamos 8 huecos, y hoy la cuenta da 8. Coinciden por casualidad.

### Qué pasa al ganar más pujas que huecos

**NO SE PUEDE SABER SIN ARRIESGAR, y no lo he probado.** Habría que ganar dos
subastas con una sola ficha libre y mirar qué pasa, y el precio de equivocarse es
una compra no deseada de millones. **El tope de la cartera se queda en huecos
libres.**

---

## BLOQUE 3 — Empates: **existen, y hay uno**

De 144 subastas, 79 con puja rival visible. **Un empate:**

```
05/09 07:06, jugador 41385
   GANÓ   Pollo17                        1.877.000
   perdió DiosMande a Rodri al Palancas  1.877.000   <-- la misma cantidad
   perdió Luismi_Haz                     1.856.000
```

**El empate se resuelve, no se repite la subasta.** Con un solo caso **no se
puede saber qué lo decide**: encaja igual de bien con «ganó el que pujó antes»
—tu sospecha— que con «ganó el id más bajo» (Pollo 14145555, DiosMande
14151726). Esas dos no se separan con una observación.

**Lo que sí cambia:** el desvío aleatorio de importes se puso para no empatar, y
aquí se ve que **los empates pasan**: 1 de 79 subastas con rival visible, un
1,3 %. No es cero, así que el desvío está haciendo trabajo real.

---

## BLOQUE 4 — El precio que pedimos: **no protege, y probablemente no espanta**

Sobre 67 listados nuestros con multiplicador y **cuatro** ofertas de rivales en
todo el histórico:

```
Ximo Navarro   pedíamos 1.360.000 (x1,03)   Pollo ofreció    1.200.000
Jutglà         pedíamos 3.900.000 (x1,23)   Pollo ofreció    4.300.000  <-- POR ENCIMA
Olasagasti     pedíamos 3.760.000 (x1,18)   Pollo ofreció    2.750.000
Yeray          pedíamos 1.950.000 (x1,01)   Luismi ofreció   2.000.000  <-- POR ENCIMA
```

**Lo que sí se puede afirmar con cuatro casos:** el precio pedido **no es un
techo**. Dos de las cuatro ofertas llegaron por encima. El rival ofrece lo que
quiere, mire lo que mire. **Pedir alto no protege nada: solo dice lo que te
gustaría cobrar.** Eso confirma tu lectura.

**Lo que NO se puede afirmar:** que pedir poco traiga más ofertas. La mediana del
multiplicador es x1,11 con oferta y x1,16 sin ella — va en esa dirección, pero
**con cuatro casos eso es una anécdota, no una medida**. No he cambiado ninguna
regla.

Y el contexto que lo explica: el canal manager-a-manager **está casi muerto**.
Medido el 05/09 sobre 67 h de tablón, **una** sola compra entre managers en toda
la ventana, y fue nuestra.

---

## BLOQUE 5 — Qué mueve los precios

Sobre 2.813 pares jugador-día de **días consecutivos** (las fotos del 12 al
17/08):

| puntos ese día | casos | mediana | media | sube |
|---|---:|---:|---:|---:|
| 0 | 2.685 | 0 | +2.201 | **35 %** |
| 1-3 | 75 | 0 | +8.266 | 48 % |
| 4-7 | 42 | **+20.000** | +30.714 | **69 %** |
| 8+ | 11 | **+20.000** | +22.727 | 64 % |

**Los puntos mueven el precio, y de forma monótona.** Con 4 o más puntos la
mediana salta a +20.000 y sube en el 69 % de los casos, contra el 35 % de los que
no puntúan.

**Los tramos altos tienen pocos casos** (42 y 11): la dirección es sólida, la
magnitud exacta no. Y **queda mucho sin explicar**: hasta los que no puntúan
suben el 35 % de los días. Los puntos son *una* causa, no la única.

*(Nota de método: la primera versión comparaba foto contra foto y daba un
resultado al revés. Mezclaba pares de la misma mañana —donde el precio no se
mueve porque solo se mueve en el reset— con un par que saltaba 24 días y se
comía el resultado.)*

### El «25 % Compras / 0 % Ventas / 99 % Uso»

**No lo tenemos, y no se puede sacar de lo que descargamos.** El catálogo trae
`price`, `priceIncrement`, `points`, `fitness`, `status` y poco más. Ese dato
vive en la **ficha individual** del jugador.

- Todos los jugadores: **574 peticiones/día**, contra las 181 que gasta hoy el
  ciclo entero. Inviable.
- **Solo los del mercado (unos 20): 20 peticiones/día, un 11 % más.** Viable.

Si es una señal de demanda diaria, es exactamente la intel externa que llevamos
semanas buscando, y la sirve la propia casa. **La decisión es tuya**; aquí solo
lo mido y lo digo.

---

## A la doctrina

**29 — Las reglas del juego, cerradas.** Sin capitán (confirmado por el propio
`leagueSettings` del tablón: `lineupCaptain: false`), sin cláusula, las ofertas
hay que aceptarlas, y el suplente no puntúa: solo cuenta el XI en el minuto en
que arranca la jornada, sin sustitución automática.

**30 — Los puntos son el motor económico, no la rueda.** x8,4.

**31 — Quedar de los últimos en la jornada paga.** 100.000 / 250.000 / 500.000.

---

## Lo que no hice, y por qué

- **No he tocado ningún umbral ni ninguna regla.** Los bloques 4 y 5 apuntan a
  cambios posibles; los dos tienen muestras demasiado pequeñas para justificarlos
  y me pediste medir, no cambiar.
- **No he probado qué pasa al ganar más pujas que huecos.** No se puede saber sin
  arriesgar una compra no deseada.
- **No he tocado el tope de la cartera**, que sigue en huecos libres.
- **No he pedido ni una ficha individual de jugador**, que es lo que haría falta
  para el «% Compras / % Uso».
- **Ninguna escritura contra Biwenger. No he hecho push.**
