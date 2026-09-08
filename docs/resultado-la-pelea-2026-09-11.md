# LA PRIMA AL PUNTO DE EQUILIBRIO, Y QUIÉN ATRAE LA PELEA

Rama `pelea/no-ir-donde-van-todos`. **98 de 98 en verde.**
**Ni una llamada a Biwenger.** Sin push. No he pujado.

`main` ya traía lo de anoche: el dueño lo fusionó y empujó.

---

# 1. LA PRIMA, BAJADA AL 0,25 %

`PRIMA_MAXIMA_DE_PUJA = 0.0025`, con la curva entera en el comentario y una guardia
que la lleva dentro.

## Pero hay algo que hay que saber antes de celebrarlo

**El tope no cambia ninguna oferta hoy.** La curva de primas que produción tiene
calibrada está **plana** —0,1429 en los siete tramos, que es exactamente 1/7— así
que `optimal_bid` **ya ofrecía `precio + 1`** a todo el mundo.

Entonces, ¿de dónde salía el 8,51 %? **De este mismo código, cuando la curva sí
discriminaba.** Nuestras compras llevan la firma:

| Fecha | Precio | Pagamos | Prima | Rivales |
|---|---:|---:|---:|---:|
| 17/08 | 390.000 | 504.000 | **+29,23 %** | 2 |
| 18/08 | 1.000.000 | 1.200.001 | +20,00 % | 0 |
| 19/08 | 1.890.000 | 2.068.001 | +9,42 % | 0 |
| 20/08 | 2.220.000 | 2.409.001 | +8,51 % | 0 |
| 23/08 | 1.650.000 | 1.925.100 | +16,67 % | 1 |
| 27/08 | 150.000 | 236.531 | **+57,69 %** | 1 |
| 05/09 | 4.860.000 | 5.147.000 | +5,91 % | 0 |

**Los `...001` son la firma de `candidate_bids`**: esas pujas salieron de aquí,
eligiendo un tramo alto de la curva. **El tope es un techo que hoy no muerde y que
habría evitado todo eso.**

## Lo que habría ahorrado, sobre nuestras compras reales

| | Pagamos | Con el tope | |
|---|---:|---:|---|
| **4 sin rival** (las ganábamos igual) | 10.824.003 | 9.994.929 | **−829.074** |
| 7 disputadas | 9.827.395 | — | las perdíamos, y perder no cuesta |

**829.074 EUR sobre cuatro compras que habríamos ganado exactamente igual**, porque
nadie más pujaba. Es dinero que se regaló sin comprar nada.

De las 7 disputadas: pagamos 507.395 de prima sobre el precio de mercado, y **solo
3 de las 7 venían subiendo**.

## En pantalla

Cada objetivo publica ahora `bid_sin_tope`, `ahorro_del_tope` y
`prima_maxima_percent`, y el escaparate acumula en `bid_cap`: cuántas pujas se
recortaron y **la suma**. Mil euros por jugador no dicen nada; el acumulado sí.

**Hoy `bids_capped` sale 0** — y eso es información, no un fallo: el tope no está
mordiendo porque la curva está plana.

## La guardia, con la curva dentro

`test_prima_de_puja_v1`, 12 pruebas. La que pediste: **si alguien sube la prima por
encima del punto de equilibrio (+1,8 %), se pone roja** — y le enseña la tabla
entera.

Y otra que ata las dos mediciones: **la curva tiene que cambiar de signo justo en
el equilibrio**. Si alguien toca una de las dos sin la otra, se canta.

## Una tensión real que me enseñó una guardia roja

Al topar `optimal_bid` **entero**, se puso roja
`test_con_rivales_activos_se_sube_hasta_donde_compensa`: *"con seis rivales activos,
pujar el mínimo es tirar la operación"*.

**Y tiene razón en su mundo.** La curva mide el mercado diario del Computer —veinte
candidatos, pérdidas gratis—. Comprar al jugador que hace falta para el once es un
disparo, y el margen se paga en puntos, no en reventa.

**Así que el tope se aplica a la ESPECULACIÓN**, que es donde la curva mide. Con
otra intención el comportamiento es el de siempre — que es literalmente lo que
pedía tu encargo del 10/09: *"no borres `optimal_bid`, sigue siendo el cálculo
correcto cuando de verdad solo se puede tirar una vez"*.

*(Y en el primer intento monté un modelo de mentira que daba `p=1` en todos los
importes, con lo que la prueba habría pasado sin probar nada. Ahora reutiliza el
constructor de la guardia de al lado.)*

---

# 2. LA PELEA — qué distingue a un jugador disputado

**156 subastas. 89 disputadas (57 %), 67 sin nadie.**

## La subida es el predictor, y confirma la ironía

| Subía el día antes | Subastas | Disputadas |
|---|---:|---:|
| **Cae** (< 0 %) | 32 | **28 %** |
| 0–0,25 % | 29 | 41 % |
| **≥ 2 %** | 18 | **83 %** |

**El que sube ≥2 % es disputado el 83 % de las veces. El que cae, el 28 %. Tres
veces más.**

Es exactamente lo que sospechabas: **la señal que nos hace fijarnos es la misma que
hace que se fijen los demás.** No es que compitamos por casualidad — competimos
porque miramos donde mira todo el mundo.

## Y el precio va al revés de lo que parece

| Precio | Subastas | Disputadas |
|---|---:|---:|
| < 300.000 | 14 | **64 %** |
| 1,5–3 M | 29 | 48 % |
| **≥ 6 M** | 17 | **18 %** |

**Los caros están MENOS disputados.** Mediana de precio: 1.925.000 en las
disputadas contra 3.390.000 en las tranquilas. Tiene sentido — pocos managers
pueden pagar seis millones, así que arriba hay menos gente.

## El cruce, que es lo accionable

| | Cae o plano | Sube ≥ 1 % |
|---|---:|---:|
| barato < 1,5 M | 54 % | **83 %** |
| medio 1,5–3 M | 39 % | 64 % |
| **caro ≥ 3 M** | **22 %** | 67 % |

**Subir cuesta unos 30 puntos de probabilidad de pelea. Ser caro ahorra otros 30.**
Y las dos cosas actúan en todos los niveles del otro.

**La celda tranquila es el caro que no está subiendo: 22 % de peleas sobre 32
subastas.** La celda ruidosa es el barato que sube: 83 %.

Esto encaja con lo de anteanoche: los 16 que se llevaron sin competencia **y**
subiendo tenían un precio mediano de 4.550.000. Eran caros.

## Lo que propongo, y no he tocado

**Que la probabilidad de pelea entre en el cálculo como coste, no como efecto
secundario.** Hoy un jugador que sube recibe solo el bono del momento; debería
recibir también la penalización de que el 83 % de las veces habrá que pelearlo — y
pelear cuesta siete puntos de prima.

Con dos candidatos parecidos, **preferir el caro**. Es contraintuitivo y está
medido.

**No lo he implementado**: dijiste medir y proponer.

## Lo que no he podido medir

**Si salió en una web de recomendaciones.** El libro del ojeador guarda **8
predicciones, todas del 05/09**, y las subastas van del 10/08 al 06/09. No se
solapan.

Para contestarlo haría falta archivar el informe del ojeador por día. Hoy se
sobrescribe. **Lo digo en vez de inventar una correlación con un solo día.**

**Titularidad y puntos** salen cojos por lo mismo: el catálogo local solo tiene 34
fichas completas, y de las tranquilas solo hay 5 medibles. No publico ese
porcentaje.

---

# LO QUE ENTRA EN EL COMMIT

`git status` antes. **Cinco ficheros:**

```
 M src/analysis/rival_bid_model.py       la prima maxima y el tope
 M src/analysis/acquisition_board.py     publica el antes, el ahora y el acumulado
 M scripts/run_validation_gate.py        + 1 guardia
?? src/analysis/test_prima_de_puja_v1.py 12 guardias, la curva dentro
?? scripts/quien_atrae_la_pelea.py       la medicion de la pelea
?? docs/resultado-la-pelea-2026-09-11.md
```

**No ha aparecido ningún encargo sin versionar ajeno.**

**El workflow no se ha tocado. Ningún otro umbral se ha movido.**

---

# LO QUE NO HE HECHO

**No he cambiado cómo se eligen los objetivos.** La pelea se mide y se propone.

**No he tocado el listón, la deuda ni el tope por operación.**

**No he pujado ni he leído nada de Biwenger.**

**No he archivado el informe del ojeador por día**, que es lo que haría falta para
cerrar la última dimensión de la pelea.

---

**La frase para mañana:** la prima baja al **0,25 %** con guardia que se pone roja
si alguien la sube por encima del equilibrio — **pero hoy no muerde**, porque la
curva de primas está plana y `optimal_bid` ya ofrecía el precio y un euro. El 8,51 %
salía de aquí cuando la curva sí discriminaba, y el tope **habría ahorrado 829.074
EUR en cuatro compras que ganábamos igual porque nadie más pujaba**. Y la pelea
tiene predictor: **el que sube ≥2 % es disputado el 83 % de las veces y el que cae
el 28 %** — la señal que nos hace mirar es la que hace mirar a todos. El precio va
al revés: **los caros se pelean el 18 %**. La celda tranquila es el caro que no
está subiendo.
