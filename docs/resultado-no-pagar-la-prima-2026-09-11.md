# NO PAGAR LA PRIMA — resultado

Rama `prima/pujar-bajo-por-muchos`. **97 de 97 en verde.**
**Ni una llamada a Biwenger.** Sin push. **No he pujado.**

Ningún umbral movido: el listón sigue en 3 %, la deuda y el tope por operación
intactos.

**Una cosa antes de nada:** esta rama sale de `main`, pero el encargo se apoya en
código que vive en `subasta/estar-a-las-siete-menos-cinco`, **que sigue sin
fusionar**. He fusionado esa rama **en ésta**, no en `main`. `main` no se ha
tocado, y al empujar esta rama entran las dos en orden.

---

# BLOQUE 2 — La curva. Es el resultado de la noche.

Sobre **115 subastas** del tablón con precio de referencia, probando cada importe y
contando que perder no cuesta nada:

| Ofrece | Gana | % | Prima pagada | **Neto** | Neto/ganada |
|---|---:|---:|---:|---:|---:|
| +0,00 % | 30 | 26 % | 30 | 2.376.870 | 79.229 |
| **+0,25 %** | **34** | **30 %** | 428.259 | **2.654.961** | 78.087 |
| +0,50 % | 35 | 30 % | 894.551 | 2.325.829 | 66.452 |
| +1,00 % | 35 | 30 % | 1.789.135 | 1.431.245 | 40.892 |
| +1,50 % | 40 | 35 % | 2.864.407 | 572.873 | 14.321 |
| **+2,00 %** | 46 | 40 % | 4.300.846 | **−430.126** | −9.350 |
| +3,00 % | 54 | 47 % | 7.350.054 | −2.940.054 | −54.445 |
| +5,00 % | 61 | 53 % | 13.621.061 | −8.717.501 | −142.909 |
| **+8,00 %** | 71 | 62 % | 23.923.271 | **−18.540.551** | −261.134 |

**El máximo está en `precio + 0,25 %`.**

**Pepe puja hoy al +8,51 % de prima mediana.** En esta curva, el +8 % **pierde 18,5
millones** sobre las mismas 115 subastas.

## Lo que enseña la curva

**Subir del +0,25 % al +8 % compra 37 jugadores más y cuesta 21 millones.** Cada uno
de esos 37 sale por bastante más de lo que vale.

**Y el punto de equilibrio cae exactamente donde dice la teoría:** entre el +1,5 % y
el +2 %, que es la prima que el Computer paga al recomprar — **+1,8 %, medido por
producción sobre 107 ventas**. Por encima de eso, la operación nace en pérdidas
antes de que el jugador se mueva.

*(El encargo decía +1,72 %. La cifra que publica producción hoy es +1,8 %. Uso la
suya, que es la que se recalcula sola.)*

## El sesgo, y va a favor

**Las 156 son subastas que alguien ganó.** Los jugadores por los que nadie pujó no
dejan rastro en el tablón — y ésos son exactamente los que `precio + 1` se lleva.

**Así que la columna GANA está por debajo de la realidad en los importes bajos**, y
el máximo real está igual de abajo o más. El sesgo empuja hacia la conclusión, no
en contra. Conviene saberlo antes de creérsela.

---

# BLOQUE 1 — El modo cartera

`optimal_bid` **no se toca**: sigue siendo el cálculo correcto cuando solo se puede
tirar una vez. Lo que se añade es **qué se optimiza cuando se puede tirar muchas**.

En modo cartera se ofrece `precio + 0,25 %` a todos los que se puedan comprar, y se
llena por **ganancia por euro comprometido** hasta agotar capacidad o fichas. Cada
puja publica **qué modo la decidió y por qué** (regla 17).

## Un fallo mío, y es instructivo

La primera versión eligió **una sola puja de 2,4 M y dejó 17 candidatos fuera** —
exactamente lo contrario de "pujar bajo por muchos".

**La causa:** en modo cartera **todos rinden lo mismo por euro** (la prima de
reventa menos lo que se ofrece), así que ordenar por rendimiento no discrimina
nada y se llevó al más caro.

Y el arreglo tampoco entró a la primera: puse un desempate por precio, pero los
rendimientos **empataban en el 1,5461 % y diferían en el decimal quince**, así que
el desempate no llegaba a ejecutarse. Hubo que **redondear a la centésima de punto**
antes de comparar. Dos rendimientos que se distinguen en la millonésima son el
mismo rendimiento.

---

# BLOQUE 3 — Cuántas caben

Sin cambios respecto de anoche, y ya estaba medido:

- **Perder no cuesta un euro**: el balance no se mueve, baja `maximumBid` hasta el
  reset (medido el 16/08 con dos snapshots a 30 segundos).
- **Límite duro: las fichas libres**, hoy **7** (la plantilla mayor de la liga, 21,
  menos la nuestra, 14 — la definición que la casa usa desde el 25/08, y allí queda
  escrito que es un suelo, no el tope de Biwenger).
- **Barandillas sobre el peor caso**: que se ganen todas.
- **Tope por ventana**: `caja / 0,05` = lo que se deshace el viernes aunque el
  mercado caiga un 5 %.

---

# QUÉ HABRÍA PUJADO HOY, CON LOS DOS MODOS AL LADO

```
  Fichas libres: 7      Caja libre: 258.807      Bolsillo: 2.497.407
  El Computer recompra a +1,8 %.  Modo cartera ofrece precio +0,25 %.

  HOY (un disparo)
    Ninguna puja: 0 candidatos y ninguno pasa.

  MODO CARTERA
    7 pujas por 1.964.907 EUR, ocupando 7 de 7 fichas libres.
    Si se ganaran TODAS: 30.373 EUR de ganancia esperada.

    JUGADOR                PRECIO        PUJA       GANA   POR EURO
    Letacek               150.000     150.376      2.324    1,545 %
    Pelayo                240.000     240.601      3.719    1,546 %
    Javi Morcillo         250.000     250.626      3.874    1,546 %
    Aitor Fernández       260.000     260.651      4.029    1,546 %
    Szczęsny              270.000     270.676      4.184    1,546 %
    Álvaro Fernández      290.000     290.726      4.494    1,546 %
    Miguel Rodríguez      500.000     501.251      7.749    1,546 %

    Peor caso: la plantilla quedaría en 21. Máximo por club: 1.
```

**De cero pujas a siete.** Pero léelo con dos avisos, porque son importantes:

**1. Son 30.373 EUR y se comen las siete fichas libres.** El día que aparezca un
fichaje de verdad, no habría dónde meterlo. La ganancia por ficha ocupada son 4.339
EUR: hay que decidir si esas fichas valen eso.

**2. La ganancia depende entera de que el Computer recompre a +1,8 %.** Es una
mediana sobre 107 ventas con un **73,8 % de casos positivos** — o sea que **una de
cada cuatro sale por debajo**. Estas siete no son dinero seguro: son siete apuestas
pequeñas con una ventaja del 1,55 % y una cola a la baja.

Ninguna de las dos cosas invalida el modo cartera. Las dos cambian de qué tamaño es
el negocio: **no es "20k × 6 gratis", es un 1,55 % de arbitraje sobre lo que quepa.**

---

# BLOQUE 5 — El cero, releído

De los 20 de hoy, cuántos pasarían el listón del 3 % según la prima que se pague:

| Comprando a | Pasan el listón |
|---|---:|
| **+8,3 %** (lo que pagamos hoy) | **0 de 20** |
| **+1,3 %** (sin rival) | **0 de 20** |
| **+0,25 %** (el óptimo de la curva) | **1 de 20** |

**El cero no se convierte en cuatro. Se convierte en uno — y es Gorosabel, que está
lesionado.**

**No era la prima.** Los márgenes son demasiado finos: **12 de los 20 valen cero**
para nosotros, y de los cinco con margen positivo, cuatro están entre el 1,27 % y el
1,91 %.

Lo que sí hace la prima es **convertir cinco jugadores marginalmente positivos en
cinco claramente negativos**:

| Jugador | Margen | @ +8,3 % | @ +0,25 % |
|---|---:|---:|---:|
| Gorosabel | 4,06 % | −3,91 % | **+3,80 %** |
| Roro Riquelme | 1,91 % | −5,90 % | +1,65 % |
| Amatucci | 1,86 % | −5,95 % | +1,60 % |
| Pedri | 1,35 % | −6,42 % | +1,10 % |
| Gabriel Suazo | 1,27 % | −6,49 % | +1,02 % |

**Pagar el 8,3 % no nos quita fichajes que pasarían el listón: nos convierte en
perdedores seguros a los que estarían en tablas.** Es peor de otra manera.

---

# BLOQUE 4 — Prinzipote, y lo que aparece de rebote

| | Compras | Disputadas | Prima mediana | Precio mediano |
|---|---:|---:|---:|---:|
| **Prinzipote** | **6** | 1 (17 %) | **+0,10 %** | 1.150.000 |
| Pollo17 | 51 | 26 (**51 %**) | +2,74 % | 2.520.000 |
| **Pepe Bordalás** | 17 | 13 (**76 %**) | **+8,51 %** | 1.700.000 |

**Prinzipote no es un modelo a copiar: compra 6 veces en 27 días.** Su 0,10 % es
real pero con n=6 no es una estrategia, es abstención. El propio encargo lo
anticipaba.

**Lo que sí sale de la comparación es sobre nosotros: Pepe entra en subastas
disputadas tres de cada cuatro veces.** Pollo, que compra tres veces más, se pelea
la mitad de las veces. Prinzipote, una de cada seis.

**No es solo que paguemos caro: es que elegimos pelea.** Y de nuestras 17 compras,
solo 3 venían subiendo.

---

# LO QUE ENTRA EN EL COMMIT

`git status` antes. **Cinco ficheros, más lo que arrastra la fusión:**

```
 M src/analysis/la_subasta.py            la curva, el modo cartera, el desempate
 M src/analysis/test_la_subasta_v1.py    de 24 a 35 guardias
 M scripts/que_pujaria_en_el_reset.py    los dos modos al lado
?? scripts/la_curva_de_la_prima.py       el bloque 2
?? docs/ENCARGO-NO-PAGAR-LA-PRIMA-2026-09-11.md
?? docs/resultado-no-pagar-la-prima-2026-09-11.md
```

**Y la fusión de `subasta/estar-a-las-siete-menos-cinco`**, que trae lo de anoche.

**No ha aparecido ningún encargo sin versionar que no sea el mío.** El único
untracked era éste.

---

# LO QUE NO HE HECHO

**No he pujado, ni he leído nada de Biwenger.** La curva sale del tablón en disco;
los dos modos, de `status.json`.

**No he encendido el modo cartera.** `enabled` sale `False`: el primer reset se mira
con los números delante.

**No he tocado `optimal_bid`.** Sigue decidiendo igual cuando solo se tira una vez.

**No he movido el listón**, aunque el bloque 5 deja claro que la prima convierte
cinco empates en cinco derrotas. Eso es una conversación, no un cambio de una
línea.

**No he investigado las tres cuentas del libro de pujas** (1 registro, 17 compras en
el tablón, 9 pujas perdidas). Sigue pendiente de anoche.

---

**La frase para mañana:** la curva dice que el importe correcto es **`precio +
0,25 %`**, y que al **+8 %** —donde pujamos— se pierden **18,5 millones** sobre las
mismas 115 subastas. El punto de equilibrio cae justo en la prima que el Computer
paga al recomprar, **+1,8 %**, como decía la teoría. **Pero el cero de los 20 no era
la prima**: con la puja óptima pasa uno, y está lesionado. Lo que sí hace pagar el
8,3 % es **convertir cinco jugadores en tablas en cinco perdedores seguros**. Y de
rebote: **Pepe entra en subasta disputada el 76 % de las veces**, contra el 51 % de
Pollo y el 17 % de Prinzipote. No es solo que paguemos caro — es que elegimos pelea.
