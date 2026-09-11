# LA DOCTRINA DE PEPE

**Versión 1.5 — 2026-09-22**

Cómo juega Pepe. Cada regla dice de dónde sale y en qué estado está.

Cuatro fuentes, y ninguna manda sobre las otras:

- **VÍDEO** — "Trucos TIPS para ganar en Biwenger 2026/27", MANYOTUBEPIC, 6:00.
  Ocho trucos, transcripción leída entera.
- **VÍDEO-2** — "5 consejos para ganar tu liga Fantasy Biwenger 25/26", La Media
  Inglesa, 12:22. Transcripción leída entera. **Es de la Premier, no de LaLiga**:
  los nombres no valen, la mecánica del dinero es la misma.
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

**Y VÍDEO-2 añade el matiz que lo hace rentable:** el valor no está en el crack
que además tira penaltis, está en **el barato que los tira**. *"A Salah o Palmer
no los vas a fichar solo por los penaltis, pero Kluivert metió seis de penalti la
temporada pasada, tres en un partido, y es mucho más barato."* Igual con córners
y faltas: un jugador que juega mal pero saca todo **se hincha a asistencias**.

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

**VÍDEO-2 lo pone en el centro, y añade la frase que nos señala:**

> *"Todos los días dos minutitos fichando a todos los jugadores que se estén
> revalorizando. Da igual que te caigan mal, da igual que sean de tu equipo
> rival, **da igual que ni siquiera vayan a jugar**. (…) Puedes estar en −15,
> −20 toda la semana, pero **los viernes vendes para volver a positivo y poder
> puntuar**."*

**Estado: construido y casi nunca dispara.** Y el embudo del 20/09 dice dónde
muere: **12 de 20 por `NO_MEJORA_EL_ONCE`**, cero por el tope. Si un jugador
descartado para el once **no se está evaluando después por la vía de comerciar**,
entonces el filtro del once está matando operaciones de cartera — que es
exactamente lo que el vídeo dice que no hay que hacer. **Por comprobar, y es la
sospecha más cara que hay abierta.**

### 9-bis. Volumen, no solo margen

**VÍDEO-2 + POLLO.** Pollo hizo **52 pujas**; Mex, 3; Pepe, 1. El vídeo describe
una estrategia de **muchas operaciones con margen fino**; la nuestra exige un 3 %
por operación y hace casi ninguna.

Nuestro propio retrotest tiene el dato para decidirlo: el tramo `1-2 %/día` rinde
+1,80 % y está apagado por no llegar al 3 %. Con volumen, muchos +1,80 %
componen. **Sin medir: hay que comparar cartera de muchas operaciones finas
contra pocas gruesas, con nuestro capital.** No se afloja el 3 % por consejo.

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

**VÍDEO-2 lo confirma palabra por palabra:** en negativo toda la semana, en verde
el viernes. La máquina está bien.

**Estado: hecha, y sin usar nunca.** El reloj funciona, pero Pepe está
`SIN_DEUDA` con saldo positivo y **jamás se ha puesto en rojo**. Tiene permiso
para endeudarse y no lo usa, porque no hay nada que pase sus filtros de compra.
El permiso no sirve de nada si el embudo no deja pasar a nadie: esto se arregla
en la regla 9, no aquí.

### 16-bis. Al lesionado se le vende rápido

**VÍDEO-2 (consejo 3 y 4).** *"Cada jornada que lo tengas, estás perdiendo
dinero."* Y no casarse: si empieza mal, se vende **aunque sea tu favorito**,
que siempre se puede recomprar.

**Estado: a medias.** La indisponibilidad veta comprar y alinear (regla 20), y la
cola de ventas tiene tramos por "no juega" y "cae y no juega" — pero **lesionarse
no es un tramo propio**, y es el momento en que más rápido hay que salir.

### 17. Cada decisión cita su regla

Cuando Pepe ficha, vende, alinea o rechaza, dice qué regla de este documento la
sostiene. **Una decisión sin cita es una decisión que nadie ha escrito**, y ésas
son las que hay que descubrir.

### 18. Ningún umbral sin número detrás

Un límite que nadie ha medido es una opinión disfrazada. Ya pasó con el listón
del 3 % —que resultó bien puesto— y con el tope por operación —que resultó ser un
porcentaje de un porcentaje.

### 23. Ninguna guardia lee estado externo

**Ni el disco, ni la red, ni el reloj. Si una guardia necesita una hora o un
fichero, se los pasan.**

Antes la regla era «ninguna guardia lee `data/`», y se quedaba corta por un lado
que no habíamos visto: **el reloj también es estado externo**, y es el peor,
porque cambia solo.

**EL INCIDENTE (08/09/2026).** `test_ojeador_prensa_v1` se puso rojo un martes a
las 17:00. Nadie había tocado nada. Su feed de mentira llevaba `pubDate` fijo del
05/09 y llamaba a `build_press_report` **sin pasarle `now`**, así que la hora la
leía producción. Con `MAX_ITEM_AGE_HOURS = 72`, el fixture cumplió tres días y
cuatro pruebas cayeron a la vez.

**Por qué es el peor tipo de rojo:** no falla cuando alguien rompe algo, falla un
día cualquiera. Y quien lo mire buscará el fallo en su propio cambio, que es
justo donde no está.

**Y hay algo peor que el rojo.** Al repasarlo apareció una segunda prueba, en el
mismo fichero, que tampoco pasaba la hora: `test_un_nombre_de_dos_fichas_no_se_adivina`
afirmaba que el código **no elige** entre dos jugadores del mismo nombre. Desde el
08/09 a las 17:00 eso se cumplía porque el titular se descartaba **por viejo** —
`too_old: 1`— y la lista salía vacía sin que nadie comprobara nada. **Un verde que
dejó de probar.** Ésas no las cuenta nadie hasta que fallan de verdad.

**El pecado suele ser de omisión, no de comisión.** Ninguna de las dos llamaba al
reloj: se limitaban a no pasar la hora a una función que la aceptaba. Por eso el
barrido busca *llamadas que aceptan la hora y no la reciben*, y no
`datetime.now()`. El primer escáner que escribí buscaba lo segundo y dio LIMPIA a
la única guardia que sabemos que explotó.

**Cómo se comprueba:** `python -m scripts.guardias_que_leen_el_mundo`. Y lo que
decide de verdad no es el escáner, es adelantar el reloj y ver qué se cae sola.

---

### 24. La línea la pone el minuto en que arranca la jornada

**Si estás en negativo en el minuto en que empieza la jornada, no puntúas. El
T−6 h es salvaguarda nuestra, no norma de Biwenger.**

*(Origen: DUEÑO, 10/09/2026.)*

Las dos cifras se publican **por separado** y no se mezclan nunca: una es la
regla del juego y la otra es nuestra prudencia. Confundirlas tiene los dos
errores posibles dentro — vender con seis horas de margen creyendo que es
obligatorio, y llegar al minuto cero creyendo que aún quedaban seis.

---

### 25. Una oferta viva es una opción gratis

**Tenerla no obliga a nada. Solo ejercerla cuesta.**

*(Origen: DUEÑO, 10/09/2026.)*

Es el espejo exacto de lo que ya sabíamos de las pujas: perder no cuesta nada.
Por eso el libro de ofertas vivas se cuida como se cuida una cartera de
opciones, y por eso matar una oferta sin necesidad es tirar dinero que no se ve.

**Medido el 10/09:** un listado vive **48,0 h exactas** (47 de 47
observaciones), las ofertas del Computer caducan a las **07:00** (57 de 65) y la
tanda nueva nace entre las **07:03 y las 07:09** (las 54 entrantes, siete días
seguidos).

---

### 26. Se renueva todo, todos los días — CORREGIDA el 10/09

**Renovar NO mata la oferta viva. Se renueva todos los días, a cualquier hora, y
cada renovación RE-PRECIA.**

*(Origen: DUEÑO, 10/09/2026. Corregida el mismo día por medición en vivo.)*

**Lo que decía esta regla hasta hoy**, y era falso: «renovar mata la oferta viva,
por eso se renueva tarde, en la ventana del reset». Toda la política de la
ventana colgaba de esa frase.

**Lo que se midió, escribiendo de verdad contra Biwenger** (13 renovaciones, con
el dueño delante):

```
Dituro   listado nuevo 10/09 12:25, 48 h por delante
         oferta de 2.439.000 creada el 09/09 a las 07:08:  INTACTA
```

Trece renovaciones, **trece ofertas vivas conservadas**. La oferta no cuelga del
listado: cuelga del reset, y muere a las 07:00 haga lo que haga el listado.

**Consecuencias, y son grandes:**

- **Renovar no cuesta nada.** No hay que esperar a la ventana para no perder
  liquidez, porque no se pierde ninguna.
- **La ventana deja de restringir la renovación.** Sigue mandando para pujar
  —eso sí depende del reset— y sigue mandando la zona de silencio, que es sobre
  no escribir mientras el mercado se rehace.
- **Se renueva todo, todos los días.** Se autolimita: al renovar, el listado dura
  48 h y no vuelve a pedir renovación hasta 23 h después.
- **Y desaparece el problema de los listados que morían entre dos ventanas.** El
  10/09 eran siete de ocho.

**RENOVAR ES TAMBIÉN RE-PRECIAR, PERO HACIA ARRIBA:**

```
pedir = max(precio_actual, valor de mercado × 1,15)
```

*(El multiplicador es del dueño, 10/09. El `max`, corrección del mismo día.)*

**Sube cuando el mercado adelanta al listado; no baja nunca.** La primera versión
recalculaba siempre, y eso convertía el arreglo en un destrozo:

```
Yamal      32.160.000  ->  24.748.000    -7,4 M
Expósito    7.820.000  ->   6.014.500    -1,8 M
```

Pedir alto por alguien es **una decisión** —es el precio al que estamos
dispuestos a soltarlo—, no un descuido que haya que corregir. El problema que se
arreglaba era otro: **el rechazo por debajo de mercado**. Eso se arregla subiendo
el suelo, no reescribiendo el techo. Guardia: `test_renovar_no_baja_el_precio`.

No es cosmética: **es lo que rompió dos de las ocho renovaciones**.

```
Jonny         pedía 2.350.000   valía 2.370.000   ->  HTTP 400
Pablo Durán   pedía   400.000   valía   420.000   ->  HTTP 400
los otros seis, entre +240.000 y +740.000         ->  OK
```

**Biwenger rechaza listar por debajo del precio de mercado.** Y le pasa a los
listados viejos: se publicaron cuando el jugador valía menos y el mercado los
adelantó. Para situar el 1,15: las trece peticiones vivas ese día iban de 1,03 a
1,50, con la mediana en 1,18; Cepeda estaba en 1,03 y era el siguiente en
romperse.

### LA APP SÍ MATA LAS OFERTAS. LA API NO. — medido

**No son dos formas de hacer lo mismo: hacen cosas distintas.**

**En la app**, el botón *Renovar* lo avisa con todas las letras:

> *«Se rechazarán todas las ofertas recibidas por él»*

*(Fuente: captura del propio botón, aportada por el dueño el 10/09/2026. Lo dice
la app, no es una deducción nuestra.)*

**Por API no pasa.** Trece renovaciones el 10/09 con el dueño delante, **trece
ofertas vivas conservadas**. Y confirmado también **cambiando el precio**: Jonny
y Pablo Durán fueron re-listados a 2.700.000 y 480.000 —precios distintos de los
que tenían— y **conservaron su oferta**. Ni el re-listado ni el re-precio la
tocan.

**Lo que esto significa en la práctica:**

- **Pepe renueva por API**: no pierde nada, y por eso renueva todos los días.
- **Si renuevas tú a mano en la app, MATAS las ofertas vivas de ese jugador.**
  Un día normal da igual —el Computer vuelve a ofertar en el reset—, pero con
  deuda contingente esas ofertas son la caja con la que se tapa: matarlas la
  víspera de la jornada es exactamente lo que no hay que hacer.
- Si tienes que renovar a mano y hay ofertas que te importan, **díselo a Pepe y
  que lo haga él**.

*(Antes esto estaba escrito como aviso sin confirmar, porque Mangala —renovado a
mano a las 09:04— conservó su oferta. Con la captura del botón queda cerrado: o
Mangala no se renovó por la app, o no se llegó a confirmar el aviso.)*


### 27. La liquidez no se busca cuando hace falta: se mantiene todos los días

**Con el libro de ofertas renovado, la deuda de lunes a jueves deja de ser un
riesgo.**

*(Origen: DUEÑO, 10/09/2026.)*

Es lo que convierte la regla 16 de una alarma en una rutina. Buscar liquidez el
día que hace falta significa venderle a quien te la pida al precio que te
ofrezca. Mantenerla significa llegar a ese día con las opciones ya compradas —y
gratis.

---

---

### 28. Un panel nace en Auditoría; a la portada se sube

**Cualquier panel que se pida para VERIFICAR algo nace en Auditoría. A la portada
solo sube lo que el dueño necesita para DECIDIR.**

*(Origen: DUEÑO, 10/09/2026.)*

La portada se llenó sola, y no por descuido: cada panel se pidió por un buen
motivo, casi siempre para comprobar que algo recién construido funcionaba. Una
curva, una calibración, una sonda, un reparto. Y después se quedaba.

**El criterio es la pregunta que contesta el panel:**

- **QUÉ** — el saldo, el once, lo que se puede cobrar, lo que se pujó → portada.
- **POR QUÉ** — la curva de la prima, la calibración del ratio, el embudo, el
  histórico, la vara → **Auditoría**.

**Nada se borra.** Lo que se quita de delante se mueve, y se dice a dónde. Lo que
se pierde no se recupera; lo que se mueve, sí.

**Las ocho preguntas de la portada** *(dueño, 10/09)*, que son también su índice:

```
1. ¿Algo en ROJO que exija que yo haga algo AHORA?
2. ¿Vamos ganando?           puntos contra Pollo, y los del banquillo
3. ¿Cuánto hay y cuánto debo DE VERDAD?   saldo · comprometido · efectivo
4. ¿Qué hizo Pepe y qué hará?
5. ¿Se abrió la ventana? ¿qué pujó y qué renovó?
6. ¿Qué puedo cobrar ahora, y cuáles de esos son titulares?
7. ¿Cómo está el once?
8. ¿A por quién va Pepe?
```

Si un panel no contesta a una de esas ocho, no está en la portada.

**Y la de arriba del todo dice algo aunque no pase nada.** Una tira que solo
aparece cuando hay problemas es indistinguible de una tira rota: cuando no hay
nada, pone *NADA QUE HACER AHORA*. Es la misma lección que la ventana que no se
abría — **una ausencia tiene que anunciarse**.

---

---

### 29. Las reglas del juego, cerradas — no se vuelven a discutir

*(Origen: DUEÑO, 10/09/2026, confirmado contra el tablón donde se podía.)*

- **No hay capitán ni multiplicador.** No es liga de pago. Confirmado por el
  propio Biwenger: el evento `leagueSettings` del tablón trae
  `lineupCaptain: false`.
- **No hay cláusula de rescisión.** Solo subasta del Computer y ofertas entre
  managers.
- **Las ofertas por nuestros jugadores hay que ACEPTARLAS.** Nadie nos quita a
  nadie pagando. Un precio alto no protege nada — y medido: de cuatro ofertas de
  rivales, **dos llegaron por encima de lo que pedíamos**. El precio pedido no es
  un techo, es una señal.
- **El suplente NO puntúa para nosotros aunque el jugador puntúe.** Solo cuenta
  el XI en el minuto en que arranca la jornada, y **no hay sustitución
  automática**. Por eso los puntos del banquillo son una pérdida real y no una
  curiosidad.

---

### 30. Los puntos son el motor económico, no la rueda

**Un punto de jornada paga 30.000 EUR, y eso da ocho veces más que comprar y
vender.**

*(Medido el 10/09/2026 sobre las 5 jornadas cerradas del tablón.)*

Biwenger lo publica él mismo: cada `roundFinished` trae `points` y `bonus` por
manager. **23 de 35 filas cuadran a 30.000 exactos**; las 12 restantes son las
que cobran el extra de la regla de abajo.

**Y la comparación que importa**, contando solo jugadores comprados **y**
vendidos —lo demás sigue en la plantilla y no es beneficio—:

```
                   POR PUNTOS   viajes    BENEFICIO   por viaje
Pollo17             7.170.000       36    5.700.524     158.347
Pepe Bordalás       6.550.000        6      781.654     130.275
Luismi_Haz          6.520.000       24    4.512.794     188.033
Manzagool           5.240.000       12   -2.879.680    -239.974
Mex                 6.370.000        0            0           —
```

**Para nosotros los puntos dan 8,4 veces lo que la rueda.** Y ni siquiera el
trader más activo de la liga —Pollo, con 36 viajes cerrados— saca de comerciar
lo que saca de puntuar. Manzagool ha *perdido* 2,9 M comerciando.

**Consecuencia pendiente de decidir:** si el once es el motor económico
principal, dejar puntos en el banquillo no cuesta solo posición — cuesta dinero.

---

### 31. Quedar de los últimos en la jornada PAGA

**Puesto 5 de la jornada: +100.000. Puesto 6: +250.000. Último: +500.000.**

*(Medido el 10/09/2026. Encaja en 4 de las 5 jornadas; en la Jornada 1 no cobró
extra nadie.)*

Los cuatro primeros no cobran extra **nunca**. No es una racha, no son las
operaciones y no es ganar: es un **pago de consolación**, y más grande cuanto
peor lo hagas.

```
puesto 1-4:  0 x5 cada uno
puesto 5:    100.000 x4      (y 0 x1, la Jornada 1)
puesto 6:    250.000 x4
puesto 7:    500.000 x4
```

Manzagool ha sido último en las cuatro: **+2.000.000 de consolación**, que es
casi la mitad de lo que ha cobrado por puntos.

**Y es otra cosa que el `dailyStreak`**, que el tablón publica en eventos
`bonus` aparte: tres vistos, todos de 250.000 (Prinzipote 02/09, Pollo 02/09 y
07/09). Ése sí parece una racha de conexión diaria, y no tiene que ver con la
jornada.

---

---

### 32. El negocio de esta liga es la subasta, no el calendario

**Medido el 10/09/2026 sobre los 36 viajes cerrados de Pollo17 (+5.700.524).**

Su viaje mediano rinde **+3,86 % en 5 días**. De dónde sale, en tres partes que
suman:

```
(a) lo que gana al COMPRAR      +0,15 %   compra POR DEBAJO del precio
(b) prima del Computer al vender +2,49 %
(a) + (b)                        +2,64 %   <- el 68 % de su ganancia
(c) lo que sube mientras lo tiene +1,23 %  en 5 días = +0,25 %/día
```

**(c) es la deriva del mercado, no una rampa.** Su negocio es el spread entre la
subasta y la recompra del Computer.

**Y la hipótesis del calendario queda refutada:** 24 de sus 36 viajes **no
atraviesan ninguna jornada**, y esos rinden **+1,29 %/día** contra +0,87 %/día de
los 12 que sí. Aguantar la jornada da más beneficio absoluto porque dura cinco
veces más, no porque rente mejor.

### Dónde está su ventaja, y es una sola cosa

**No paga de más en la subasta.** Lo que paga cada uno por encima del precio de
mercado:

```
Pollo17      -0,15 %      <- compra al precio, o por debajo
Prinzipote   +0,20 %
DiosMande    +2,27 %
Luismi_Haz   +2,31 %
Manzagool    +7,95 %
Mex         +11,81 %
NOSOTROS    +29,23 %      <- n=1, nuestra única compra medida
```

**Y no es que venda mejor:** su prima de venta (+2,49 %) es la **peor** de los
cinco que venden. Gana porque no regala el margen al comprar.

Eso valida la curva de la prima del 11/09 —pujar a `precio + 0,25 %`— que nos
pone justo en su zona. Y explica el 86 % de su dinero que nuestro filtro
rechazaba: no buscábamos rampas donde no las hay, buscábamos rampas en lugar de
buscar el spread.

---

### 33. Un dato, un nombre — van siete

**`RENDIMIENTO_MINIMO_DEL_CAPITAL`**, antes `MIN_SPECULATION_YIELD`.

*(Corregido el 10/09/2026.)*

Llevábamos semanas llamándolo **«el listón del 3 % diario»**. No lo es y nunca lo
fue:

```
rendimiento = expected_value / bid
```

Es lo que rinde **la operación sobre el capital que inmoviliza**, no lo que sube
el jugador en un día. Un viaje de cinco días que rinde un 3 % pasa el listón; uno
que sube un 3 % diario durante cinco días rinde un 16 % y pasa de sobra. **No son
la misma cosa ni se parecen.**

**El nombre malo tuvo consecuencia:** se comparó contra ritmos diarios de rivales
para decidir si nuestro filtro era duro, y esa comparación no significaba nada.

El **ritmo diario**, que es otra cosa, vive en `market_rate_gate` y **no tiene
listón**: solo exige que no sea negativo.

---

### 34. Inicio contesta, no informa

*(Cerrado por el dueño el 10/09/2026.)*

**Inicio es la tira de estado y cuatro paneles. Nada más.**

| | |
|---|---|
| **XI para la jornada** | quién juega |
| **Clasificación e inteligencia** | cómo vamos y quién aprieta |
| **Cronología de Bordalás** | qué hizo y qué hará |
| **Posibles cambios** | quién está fuera del XI, y por qué |

La tira de arriba lleva ocho cosas: jornada · edad de la foto · **próximo ciclo
(en vivo)** · **deuda máxima** · **reset (en vivo)** · cierre de la jornada · XI ·
pujas puestas.

**«Deuda máxima» sustituye a «Puede gastar»**, y no es un cambio de nombre:

```
deuda máxima = saldo + línea de crédito − pujas ya comprometidas
```

Ese número **ya descuenta las pujas vivas**. El 10/09 son **3.608.383** y no
15.825.383, porque hay 12.217.000 puestos en Aubameyang. Por eso lleva el
desglose debajo — *saldo · comprometido · crédito*: sin él se lee como «se me ha
hundido el saldo» cuando lo que pasa es que hay una puja puesta.

**Las dos cuentas atrás corren en el navegador**, no en la foto. Y **si un ciclo
no llega, lo dicen**: pasan a «debería haber entrado hace X» en vez de quedarse
en cero fingiendo normalidad. Un ciclo que no entra es exactamente lo que hay que
ver — es lo que tapó dos semanas de ventana perdida.

**Nada se borra: lo que sale de Inicio se mueve.** AhoraPanel, DineroPanel,
VentanaPanel, CobrarPanel, ElOncePanel y los objetivos bajaron a Auditoría
enteros, leyendo los mismos datos. Si se duda de dónde va algo, va a Auditoría.

Con la [regla 28](#28-un-panel-nace-en-auditoría) — *un panel nace en Auditoría* —
esto cierra el círculo: **a Inicio solo sube lo que hace falta para decidir, y
solo baja a Auditoría lo que sirve para verificar.**

**Guardia:** `test_inicio_tiene_los_cuatro_paneles_y_solo_esos`, que además
comprueba que los seis que bajaron **llegaron** a Auditoría. La portada ya se
llenó una vez, y se vuelve a llenar sola en cuanto nadie mira.


---

### 35. Una hora sin zona es un dato con dos nombres

*(Cerrado por el dueño el 10/09/2026. Corregido el 11/09: eran **dos**, no tres.)*

**Toda marca de tiempo que cruce un límite —fichero, red, pantalla— lleva su zona
pegada, o se normaliza justo ahí.** No hay tercera opción, y «se sobreentiende
que es de Madrid» no es llevarla pegada.

`2026-09-10T09:04:33` es dos instantes distintos según quién lo lea, y los dos
parecen correctos. Ese es el problema: **no falla ruidosamente**. Da una respuesta
plausible y equivocada, y sobrevive a todas las pruebas que no midan el desfase.

**Los dos del 10/09**, mismo error en dos capas:

| dónde | qué pasó |
|---|---|
| **El cálculo interno** | `VENTANA_MINUTOS` comparaba contra una hora de pared sin decir de dónde |
| **`meta.generated_at`** | se publica en hora de Madrid **sin zona**. Leerlo como UTC lo adelanta dos horas: la cuenta atrás habría dicho «el ciclo llegó» cuando no ha llegado |

> **Aquí había un tercero, y era falso.** Se dio por hecho que `cron-job.org`
> aplicaba CET aunque le pusieras `Europe/Madrid`. **No es verdad**, y la
> corrección está abajo. Se queda escrito porque una regla que se apoya en un
> ejemplo inventado enseña mal, y porque el modo en que se coló importa más que
> el error.

**En la práctica:**

- Al **escribir** un instante: ISO con offset, o `Z`. Nunca `datetime.now()` sin
  `timezone`.
- Al **leer** uno ajeno sin zona: se normaliza **en la primera línea que lo
  toca**, no más abajo. `madridNaiveAUTC()` existe para eso.
- La hora de una zona con horario de verano **se pide a la base de zonas**
  (`Intl`, `zoneinfo`), no se codifica como `+2`. En marzo y octubre no es `+2`.
- Un nombre de variable **no** documenta una zona. `ahora_madrid` es una promesa,
  no una garantía.

### La compensación que no hacía falta — y la lección, que es del dueño

Del 10 al 11/09 los tres disparos externos llevaron **una hora de menos escrita a
mano**, sobre esta teoría: *«cron-job.org aplica CET siempre, aunque le pongas
Europe/Madrid»*.

**Era falsa.** Se dedujo de **un solo caso** —un job que disparó a una hora que no
cuadraba— y el historial del día siguiente la desmintió de forma directa:

```
10/09   job "45,52 6"  Europe/Madrid   ->  ciclo a las 07:52
11/09   job "45,50 3"  Europe/Madrid   ->  disparos a las 03:45 y 03:50
```

El segundo es la medición buena: **Madrid sí se honra.** La compensación adelantaba
los disparos una hora, y **la primera ventana del reset se abrió con el mercado sin
resetear**. Lo del 10/09 probablemente era otra cosa —ese job venía de antes y pudo
tener otra zona— pero no se puede probar y da igual: la medición directa manda.

Los crones están ya sin compensación: `45,50 4` y `15 7`, `Europe/Madrid`.

> ### Un solo caso no es una medición
>
> **Palabras del dueño, 11/09/2026:** *«Monté una compensación sobre n=1 y me costó
> la primera ventana.»*
>
> Un caso aislado es una **observación**: dice que algo pasó, no por qué. Para
> convertirlo en regla hace falta historial, y hasta entonces lo honesto es dejar
> el sistema como está y seguir mirando.
>
> Esto vale para todo lo demás de este documento: cada número medido lleva su `n`
> escrito al lado —12 de 12 estados, 4 jornadas × 7 managers, 85 fotos— y no es
> adorno. Es la diferencia entre una regla y una corazonada con suerte.

Lo que se vigila ahora no es el cambio de hora —no hay nada que revertir en
octubre— sino lo que de verdad importa: **que un ciclo entre a una hora que no es
ninguna de las configuradas**, sea cual sea el motivo.
`avisoDeDisparoFueraDeHora()` enseña la hora a la que entró, la hora a la que
tenía que entrar y la diferencia, **y no diagnostica la causa**. Precisamente
porque la última vez que se dedujo una causa de un solo caso salió cara.

**Y el que se cazó escribiendo esto:** `desfaseMadrid` tenía un `return 120` de
reserva para cuando `Intl` fallase, *«que es lo que rige diez meses al año»*. Por
eso mismo estaba mal — acierta diez meses y falla justo los dos en que el desfase
importa, sin decir nada. Es la 35 y la [36](#36-un-valor-por-defecto-no-puede-absorber-el-caso-más-importante)
a la vez: un desfase a mano, y un defecto benigno tapando un «no se sabe». Ahora
devuelve `null` y quien llama dice que no lo sabe.

Esto es la [regla 33](#33-un-dato-un-nombre--van-siete) —*un dato, un nombre*—
aplicada al tiempo: **un instante con dos lecturas posibles ya son dos datos.**

---

### 36. Un valor por defecto no puede absorber el caso más importante

*(Cerrado por el dueño el 10/09/2026, después de que cayeran dos el mismo día.)*

**Lo desconocido sale como desconocido. Nunca como el caso benigno.**

Un `||` o un `or` que elige por defecto en una ruta que **decide** o que **pinta
una alarma** convierte «no lo sé» en «no pasa nada». Y no deja rastro: no hay
excepción, no hay registro, no hay nada que buscar después. El sistema informa de
calma con la misma cara con la que informaría de calma verdadera.

**Los dos del 10/09:**

```js
THREAT[intel.threat_level] || "pill idle"      // VERY_HIGH no estaba en la tabla
```

La amenaza **más alta** del tablero se pintaba en gris, exactamente igual que
«ninguna». El caso que más urgía ver era el único invisible.

```python
state or ABIERTO      # una marca VIAJE en blanco daba permiso para vender
```

Un campo vacío se leía como «viaje abierto» y **autorizaba una venta**. Lo cazó
una guardia propia, no una prueba.

**La forma del fallo es siempre la misma:** el caso peligroso es el que *falta* de
la tabla —el nuevo, el raro, el que nadie previó— y el defecto lo disfraza del
caso más común, que casi siempre es el tranquilo.

**En la práctica:**

- Una tabla de severidad **tiene una entrada explícita para lo desconocido**, con
  su propio tono, y **enseña el valor crudo** que no supo traducir. Si aparece un
  `VERY_HIGH` nuevo mañana, que se vea que apareció.
- Un permiso se concede con una **comparación exacta** (`== "ABIERTO"`), nunca con
  la veracidad de un valor.
- El defecto benigno se permite donde no decide ni alarma: una etiqueta de
  posición que cae a `?` está diciendo la verdad.

**Guardia:** `test_lo_desconocido_no_se_pinta_de_benigno`.


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
| 9 | Comprar lo que sube | construido, **no dispara** |
| 9-bis | Volumen, no solo margen | **sin medir** |
| 10 | Los baratos y las noticias de cesión | **a medias** |
| 11 | No pagar de más | hecho |
| 12 | Ver las pujas | **imposible**, cerrado 21/09 |
| 13 | No comprar lo que cae | hecho |
| 14 | Rotar, no acumular | **no hecho** |
| 15 | Recoger beneficio en los grandes | resuelto: Yamal se queda |
| 16 | Positivo a T−6 h | hecho, **nunca usado** |
| 16-bis | Al lesionado, fuera rápido | a medias |
| 17 | Cada decisión cita su regla | **hecho** 20/09 — 38 de 45 |
| 18 | Ningún umbral sin número | práctica establecida |
| 19 | Las ofertas que entran | **sin doctrina** |
| 20 | Lo no disponible no se toca | hecho, sin escribir |
| 21 | Ningún bolsillo se vacía de golpe | hecho, sin escribir |
| 22 | Los intocables | **derogada** 21/09 |
| 23 | Ninguna guardia lee estado externo | **hecha** 08/09 — barrido de las 96 |
| 24 | La línea es el minuto de la jornada | **nueva** 10/09 |
| 25 | Una oferta viva es una opción gratis | **nueva** 10/09 |
| 26 | Se renueva todo, todos los días, subiendo el precio | **corregida** 10/09 — medida en vivo y ENCENDIDA |
| 27 | La liquidez se mantiene, no se busca | **nueva** 10/09 |
| 28 | Un panel nace en Auditoría; a la portada se sube | **nueva** 10/09 |
| 29 | Las reglas del juego, cerradas | **nueva** 10/09 |
| 30 | Los puntos son el motor económico, no la rueda | **medida** 10/09 — x8,4 |
| 31 | Quedar de los últimos en la jornada paga | **medida** 10/09 |
| 32 | El negocio es la subasta, no el calendario | **medida** 10/09 |
| 33 | Un dato, un nombre — el 3 % no es diario | **corregida** 10/09 |

**Once hechas. Doce por hacer. Cuatro nuevas el 10/09.**

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
