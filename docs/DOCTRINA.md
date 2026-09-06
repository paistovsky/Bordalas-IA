# LA DOCTRINA DE PEPE

**Versión 1.4 — 2026-09-22**

Cómo juega Pepe. Cada regla dice de dónde sale y en qué estado está.

Cuatro fuentes, y ninguna manda sobre las otras:

- **VÍDEO** — "Trucos TIPS para ganar en Biwenger 2026/27", MANYOTUBEPIC, 6:00.
  Ocho trucos, transcripción leída entera.
- **CONSEJO** — los básicos de Biwenger que da cualquier jugador experimentado.
- **POLLO** — lo que hace el líder de la liga, medido en su tablón.
- **MEDIDO** — lo que hemos comprobado nosotros con datos de esta liga.

**Cuando dos se contradicen, gana MEDIDO.** Si MEDIDO no tiene muestra, se dice y
se sigue el consejo.

**Y un aviso sobre el vídeo:** está grabado el 2 de agosto para ligas de hasta 18
managers. La nuestra tiene **siete**. Algunos consejos pesan menos aquí y está
anotado dónde. Adaptar no es desobedecer.

---

## PRIMERA PARTE — Los puntos

> Solo puntúan once. Todo lo demás es inventario para comprar mejores once.

### 1. El once es lo único que marca

**MEDIDO.** El valor de plantilla no explica los puntos: r = +0,553 con siete
equipos cuando haría falta 0,754. Mex va segundo con 14 fichas y nuestro mismo
presupuesto.

**Estado: entendido.**

### 2. Balón parado — penaltis, faltas y córners

**VÍDEO (truco nº 1) + CONSEJO.** Es el primero que da, y con la cuenta hecha:

> *"Estos jugadores te pueden salvar de hacer un −2 (…) con el penalti, con el
> gol, hacerte nueve puntos. Estamos hablando de un −2 a nueve puntos."*

Y no solo penaltis: **los que tiran las faltas**, tanto por el gol directo como
porque remate otro y cuente la asistencia.

**Estado: apagado.** El módulo existe con sus bonos escritos (8,0 lanzador, 3,0
segundo) y cuelga de una API de pago rota. En el `status.json` de hoy **no hay ni
un campo** sobre esto. Las tres webs que ya leemos cada ciclo lo publican.

### 3. La portería: los dos del mismo equipo

**VÍDEO (truco nº 2).** Courtois y Lunin. Cubre lesión corta, lesión larga y
expulsión.

**Ajuste a nuestra liga:** el vídeo lo justifica por la escasez en ligas de 18
managers. En una de siete hay porteros de sobra, así que la parte innegociable es
**no quedarse nunca con uno solo**; los dos del mismo club es la versión buena
cuando salga a cuenta, no la obligación.

**Hecho el 21/09.** Regla con guardia: si solo hay un portero, fichar el segundo
es PRIORIDAD PRIMERA, por encima de cualquier operación de cartera. Hoy solo cabe
Letacek (150.000 €), tercer portero: **cubre no salir con diez, no cubre hacer
una buena jornada**, y el módulo lo dice él solo.

**Y el accidente que destapó:** la regla del portero miraba `in_lineup` mientras
el dashboard llama a ese mismo dato `is_starter`. Dituro, único portero y
titular, **no salía protegido**. Un dato con dos nombres. Es la cuarta vez que
esta familia de fallo aparece.

### 4. Más delanteros, menos defensas

**VÍDEO (truco nº 5) + MEDIDO.** El vídeo pide 3-4-3 o 3-3-4 y añade un motivo
que nosotros no habíamos contado: los defensas no solo marcan menos, además traen
**rojas y penaltis en contra**.

Nuestra medición, en la franja del 65-80 % de titularidad: defensa 3,90 puntos
por jornada, delantero 5,21, medio 6,64. Factores ×1,147 / ×1,139 / ×0,787.

**Estado: hecho el 18/09.** El once pasó de 5-4-1 a 3-4-3. Pendiente de ver si
suma en tres jornadas.

### 5. Centrocampistas con gol, no centrocampistas

**VÍDEO (truco nº 6).** *"No es lo mismo tener un Gorrochategui, un Lucas Torró,
un Tchouaméni, un Roca que no meten goles, que tener un De Frutos"* — que además
juega de delantero y puntúa como medio.

**Estado: no hecho.** Nuestro factor ×1,147 trata igual al mediocentro defensivo
y al mediapunta. El vídeo confirma que hay que separarlos.

### 6. Calidad medida, no etiquetada

**MEDIDO.** Hoy la calidad sale de una etiqueta de FutbolFantasy convertida en
escalera. No entra ni un punto real. La vara explica el **20 %** de la varianza.

**Medido el 21/09: 19,1 % → 23,5 %.** Puntos por partido jugado, temporada pasada
y ésta pesadas por muestra. Cuatro puntos de mejora, no cuarenta: la primera
cifra que salió, 61,9 %, era **circular** —usaba los puntos de esta temporada
para predecir los puntos de esta temporada— y se descartó. Hay guardia para que
no vuelva a colarse.

**Estado: construida, medida y sin encender.** Con tres jornadas de muestra es un
cambio mayor que cualquier umbral.

### 7. Calidad por encima de seguridad de jugar

**MEDIDO (Mex).** Mex tiene **1 titular fijo de 11** y va segundo; nosotros 7 y
vamos cuartos.

**No dice "fichar suplentes".** Dice que la certeza de jugar se estaba pagando
demasiado cara. Es un reequilibrio.

**Estado: a medias.**

---

## SEGUNDA PARTE — El dinero

> El dinero no es el marcador. Es el combustible para comprar un once mejor.

### 8. Recién ascendidos

**VÍDEO (truco nº 3).** El hallazgo nuevo, y encaja con todo lo que hemos medido:

> *"Hay jugadores que son ahora mismo titulares que valen 500.000, 600.000, que
> están subiendo 70.000 al día (…) como se le ocurra meter un gol se te van a los
> 6 o 7 millones rápido. Juégatela aunque no los conozcas: infórmate de cuáles
> son titulares y apuesta por ellos."*

Un titular de un recién ascendido a 600.000 € subiendo 70.000 al día es un
**+11,6 % diario**: muy por encima del tramo `> 4 %` que ya medimos rindiendo
+21,15 % a tres días. La vía TENER ya sabe valorar esto — lo que no sabe es
**buscarlo**.

**Estado: no existe.** Pepe no sabe qué clubes acaban de ascender.

### 9. Mercado todos los días, y comprar lo que sube

**VÍDEO (truco nº 7, "el más importante") + POLLO + MEDIDO.** Comprar a alguien
que sube más del 1 % diario con racha corta y venderlo a tres días:
**+4,47 % de mediana, falla el 5 %** (n=142).

**Estado: construido y casi nunca dispara.** El tope por operación y el listón
del 3 % dejan fuera casi todo. Hay que ver dónde muere el embudo antes de tocar
nada.

### 10. Mirar a los baratos y leer las noticias de cesiones

**VÍDEO (truco nº 7, la otra mitad).** Y es la mitad que nos falta:

> *"Míratelos todos, incluso los que valen 150.000 (…) hay uno del Getafe que
> vale 200.000, me informo y pone que el Málaga lo busca. Estos jugadores son los
> que te van a dar la pasta: se van a otros equipos y empiezan a subir de 100.000
> en 100.000."*

Esto **no es momento, es anticipación**. Nuestra rampa detecta al que ya está
subiendo; esto detecta al que va a subir mañana porque ha salido una noticia.

**Estado: a medias.** Hay ojeador de prensa (MARCA, MD, Relevo) pero no está
apuntando a cesiones y traspasos de jugadores baratos, ni cruzado con el mercado.

### 11. No pagar de más

**POLLO.** Sus siete compras van de −7,7 % a +4,9 % sobre mercado, mediana pegada
a cero. El líder **no sobrepaga nunca**.

**Estado: hecho.** Modelo de primas calibrado sobre 48 pujas, más desvío
aleatorio para no ser adivinables.

### 12. Ver las pujas en vez de adivinarlas

**VÍDEO (truco nº 8).** El que más nos señala:

> *"Gástate fichas de Biwenger para ver las pujas, porque hay jugadores que igual
> tus enemigos ya no tienen dinero (…) un jugador que vale 5 millones y tú eres
> el único que puede pujarle: le metes 1 €, te lo llevas."*

Nosotros llevamos semanas construyendo un modelo estadístico para **estimar** lo
que el juego deja **ver** por unas monedas.

**Comprobado el 20/09, y mejor de lo que decía el vídeo:** en esta liga **no
existen las monedas** —Biwenger solo vende PremiumLeague y UltraLeague con dinero
real— pero los ajustes de la liga traen `marketShowBids = true`. **Ya está
encendido y es gratis.** Lo que falla es que pedimos las ventas a un sitio que no
devuelve las pujas.

**Ejecutado el 21/09: no se pueden leer, y el vídeo se equivoca para esta liga.**
El ajuste está en `true`, pero el endpoint de mercado devuelve 63 ventas **sin un
solo campo de puja** —ni en las 43 de rivales—, y la ruta por jugador responde
`400 Invalid method`: no existe. Lo único visible son las ofertas que nos hacen a
nosotros, que ya teníamos.

**Estado: cerrado en negativo.** `rival_bid_model` **se queda** —hay que seguir
estimando— y el desvío aleatorio de puja también, porque el rival sigue siendo
invisible. Un "no se puede" comprobado vale más que un "quizá" abierto.

### 13. No comprar lo que cae, y soltar lo propio que cae

**MEDIDO.** Un jugador que cae vuelve a caer el **90,7 %** de las veces. Nuestra
plantilla: 7 suben, 6 caen.

**Estado: hecho.**

### 14. Rotar, no acumular

**POLLO.** Compró 21.198.020 € y vendió 21.259.800 €. Casi al euro. Y puja mucho:
52 pujas contra las 3 de Mex.

**Estado: no hecho.**

### 15. Recoger beneficio en los activos grandes

**POLLO.** Vendió a Vinícius y bajó de 85 M a 67,8 M. No se enamoró del cromo.

**Medido el 20/09, y la respuesta es NO vender a Yamal.** Es el 42,81 % del
dinero por el 19,0 % de los puntos, y cuesta 2.272.500 € por punto y jornada
contra los 714.202 € del resto: 3,2 veces peor. **Pero hace 9,33 puntos por
jornada, el doble que el segundo**, y la mejor cesta que cabe con sus 21,21 M
deja el once **2,93 puntos por jornada peor** — porque solo puntúan once, y meter
cinco fichas desplaza a cuatro titulares. Además sus 9,33 están medidos y los de
la cesta son proyección.

**Estado: resuelto, y la regla se afina.** Recoger beneficio, sí; pero un activo
grande solo se suelta si lo que entra **cabe en el once**. Con tres jornadas de
muestra, se revisa.

---

---

## LO QUE FALTABA EN LA DOCTRINA

Descubierto el 20/09 al obligar a cada decisión a citar su regla: **38 de 45
citaban, y las que no revelaron cuatro huecos.** Ésta es la parte más útil del
documento, porque son cosas que Pepe hace todos los días sin que nadie las haya
escrito.

### 19. Las ofertas que entran

**Es lo que más veces hace el ciclo y no aparecía en ninguna regla.** Cuando un
rival o el Computer ofrece dinero por uno de los nuestros, ¿cuándo se coge?

Principio, a falta de medición: **se vende cuando el que sale no juega, o cuando
lo que entra mejora el once** (reglas 1 y 15). Lo demás es liquidez, y la
liquidez solo importa a T−6 h (regla 16).

**Estado: sin doctrina.** Hay motor (Offer Decision Engine V2, hoy vigilando 12
ofertas) y no hay regla escrita que lo gobierne.

### 20. Lo que no está disponible no se compra ni se alinea

Lesionados, sancionados, tocados. **Es una barandilla, no una preferencia**, y
por eso nunca se saltó ni se escribió. Gorosabel rendía un 8,49 % y quedó vetado
por estar tocado: bien hecho.

### 21. Ningún bolsillo se vacía en una operación

El tope por operación existe y no estaba en la doctrina, y por eso
`SUPERA_PRESUPUESTO` era una decisión sin regla. Viene de la lección de Soler:
81 % del presupuesto en un jugador.

**Con el dato del 20/09 delante:** de los 20 objetivos, **cero mueren por el
tope**. No es el freno que creíamos.

### 22. Los intocables — DEROGADA

Había una lista de jugadores que Pepe no podía tocar, por orden del dueño del
18/08. **El dueño la retira el 21/09/2026.** Pepe puede vender a cualquiera si
los números lo dicen.

**Lo que la sustituye no es otra lista, es la prueba que ya usamos con Yamal:**
un jugador grande solo se suelta si **lo que entra cabe en el once** (regla 15).
Esa cuenta es la que dijo que Yamal se queda, y lo dijo mejor que cualquier lista
de nombres — porque una lista protege al favorito aunque deje de rendir, y la
cuenta lo suelta el día que deje de rendir.

Siguen en pie, y no son negociables: concentración del 35 %, cuatro por club,
suelos de posición, reloj de solvencia y disponibilidad (regla 20).

---

## TERCERA PARTE — Reglas de la casa

### 16. Positivo seis horas antes de la jornada

**CONSEJO + orden del dueño.** *"Con estar en positivo 6 horas antes del inicio
de jornada es suficiente."*

**Estado: hecho.** Reloj de solvencia y cola de ventas.

### 17. Cada decisión cita su regla

Cuando Pepe ficha, vende, alinea o rechaza, dice qué regla de este documento la
sostiene. **Una decisión sin cita es una decisión que nadie ha escrito**, y ésas
son las que hay que descubrir.

### 18. Ningún umbral sin número detrás

Un límite que nadie ha medido es una opinión disfrazada. Ya pasó con el listón
del 3 % —que resultó bien puesto— y con el tope por operación —que resultó ser un
porcentaje de un porcentaje.

---

## Descartado

**Entrenadores** (truco nº 4 del vídeo). **Esta liga no los usa.** Decisión del
dueño, 19/09/2026. Queda escrito aquí para que nadie lo vuelva a proponer.

De los ocho trucos del vídeo, **los siete restantes se quieren todos**, y
ninguno por encima de los demás.

---

## El marcador de la doctrina

| # | Regla | Estado |
|---|---|---|
| 1 | El once es lo único que marca | entendido |
| 2 | Balón parado | **apagado** |
| 3 | La portería nunca a uno | **hecho** 21/09 |
| 4 | Más delanteros, menos defensas | **hecho** 18/09 |
| 5 | Centrocampistas con gol | **no hecho** |
| 6 | Calidad medida | medida 19,1→23,5, **sin encender** |
| 7 | Calidad sobre seguridad | a medias |
| 8 | Recién ascendidos | **marcador puesto** 20/09 |
| 9 | Comprar lo que sube | construido, no dispara |
| 10 | Los baratos y las noticias de cesión | **a medias** |
| 11 | No pagar de más | hecho |
| 12 | Ver las pujas | **imposible**, cerrado 21/09 |
| 13 | No comprar lo que cae | hecho |
| 14 | Rotar, no acumular | **no hecho** |
| 15 | Recoger beneficio en los grandes | resuelto: Yamal se queda |
| 16 | Positivo a T−6 h | hecho |
| 17 | Cada decisión cita su regla | **hecho** 20/09 — 38 de 45 |
| 18 | Ningún umbral sin número | práctica establecida |
| 19 | Las ofertas que entran | **sin doctrina** |
| 20 | Lo no disponible no se toca | hecho, sin escribir |
| 21 | Ningún bolsillo se vacía de golpe | hecho, sin escribir |
| 22 | Los intocables | **derogada** 21/09 |

**Diez hechas. Doce por hacer.**

### El embudo, medido el 20/09

De los 20 objetivos del escaparate:

| Causa de muerte | N | % |
|---|---:|---:|
| No mejora el once | 12 | 60 % |
| Precio (no hay caja) | 3 | 15 % |
| Rendimiento | 3 | 15 % |
| Disponibilidad | 2 | 10 % |
| **Tope por operación** | **0** | **0 %** |

**Los tres que mueren por precio —Pedri, Roro, Amatucci— valen más de lo que
cuestan.** Son compras positivas bloqueadas solo por falta de caja. Eso apunta a
la regla 14, no al tope.
