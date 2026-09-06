# LA CALIBRACIÓN, REHECHA CON HISTÓRICO DE VERDAD

Rama `calibracion/veintidos-dias`, desde `main` (`6af6eb4`).
**94 de 94 en verde.** Ningún umbral movido. Sin push.

---

# PRIMERA LÍNEA: TODO LO QUE SE ENCENDIÓ ESTA SEMANA SIGUE RESPALDADO

**Los tres tramos que se encendieron el 24/09 aguantan, y con más margen del que
tenían.** No hay que apagar nada.

| Tramo (racha 1 día, h=3) | Antes *(6 días de agosto)* | Ahora *(temporada, n≈99)* | |
|---|---:|---:|---|
| **1-2 %** | 3,22 % | **4,37 %** | SIGUE |
| **2-4 %** | 5,61 % | **8,33 %** | SIGUE |
| **> 4 %** | 18,37 % | **24,44 %** | SIGUE |
| 0,5-1 % *(nunca encendido)* | 1,25 % | 2,50 % | sigue por debajo, bien apagado |

**Y el tramo más justo deja de serlo:** el 1-2 % pasaba el listón por 0,22 puntos
y ahora lo pasa por 1,37, con **99 operaciones en vez de 47**.

---

# DE DÓNDE SALEN LOS DATOS, Y POR QUÉ NO SON LOS 22 DÍAS QUE PEDÍAS

**No pude usar el almacén de producción: vive en la caché de Actions y no tengo
acceso.** Lo que sí encontré es mejor, y hay que decir en qué se diferencia.

**Biwenger publica el precio diario de cada jugador en su propia ficha:**

```
GET /players/la-liga/{slug}?fields=*,prices
   -> "prices": [[YYMMDD, precio], ...]      366 días
```

| | Almacén del ciclo | Ficha pública |
|---|---|---|
| Origen | lo que Pepe VIO al decidir | la serie oficial cerrada |
| Fondo | 22 días | **366 días** |
| Puntos | 20.288 | **98.603** |
| Para calibrar | peor | **mejor** |
| Para auditar una decisión | **mejor** | peor |

**Es el mismo concepto, no el mismo dato**, y esa distinción es justo la que nos
ha costado los seis fallos de la familia. Para lo de esta noche —¿qué rinde
comprar al que sube?— la serie oficial es la buena. Para reconstruir por qué Pepe
decidió algo un martes, no sirve.

## Lo que falta, y por qué no insistí

**418 de 578 jugadores (72 %).** A partir de la petición 419 Biwenger empezó a
devolver 429 y siguió haciéndolo después de esperar siete minutos.

**He parado de pedir a propósito.** Producción usa esa misma API cada treinta
minutos, y dejar al bot sin mercado por completar una medición sería un mal
negocio. El script quedó con reanudación: se relanza cuando el límite se levante
y completa lo que falta.

**Y comprobé que el corte no sesga**, porque es alfabético (de la R al final) y
podría no ser inocente:

| | n | mediana | media | p90 |
|---|---:|---:|---:|---:|
| **Con** histórico | 418 | 1.540.000 | 2.396.866 | 5.380.000 |
| **Sin** histórico | 160 | 1.620.000 | 2.481.312 | 5.700.000 |

Indistinguibles. Aun así son **81.788 operaciones** en la temporada, **cuatro
veces el almacén entero de producción**.

---

# EL CONTROL QUE FALTABA, Y QUE CAMBIA CÓMO SE LEE TODO LO DEMÁS

Antes de responder nada: **¿cuánto subió el mercado entero?**

Si el mercado sube un 0,6 % al día, aguantar diez días cobra un 6 % sin ninguna
habilidad. La mediana de la vía no significa nada hasta restarle la marea, y esa
resta **no se había hecho nunca**.

```
Marea del mercado (índice sobre los que tienen serie completa)

   ventana de produccion (16/08 - 06/09)   -2,30 %  en 21 dias   = -0,109 %/dia
   temporada entera      (01/08 - 06/09)   +6,04 %  en 36 dias   = +0,168 %/dia
```

**En la ventana de producción la marea es NEGATIVA**, así que el neto sale mejor
que el bruto. Pero eso se supo *después* de mirar: antes de mirar, un +7,09 % era
igual de compatible con "hay señal" que con "hay marea".

**Y hay señal, medida de la forma más simple posible:**

| Horizonte | Compra el que SUBE | Compra el que CAE |
|---|---:|---:|
| 1 d | **+1,25 %** | −1,36 % |
| 3 d | **+3,41 %** | −3,95 % |
| 10 d | **+7,09 %** | −11,00 % |

Simétrico y creciente. El momento existe: no es la marea.

---

# 1. ¿SIGUE SIENDO 3 EL HORIZONTE? — No. Y la respuesta depende de qué preguntes.

**Por operación, el máximo está en 10 días** (el borde de lo medible) **y la curva
todavía no ha girado:**

| m | Bruto | Marea | **Neto** | Pierde | n |
|---|---:|---:|---:|---:|---:|
| 1 d | +1,25 % | −0,11 | **+1,36 %** | 2,8 % | 2.206 |
| 2 d | +2,44 % | −0,22 | **+2,66 %** | 6,6 % | 2.103 |
| **3 d** | **+3,41 %** | −0,33 | **+3,73 %** | **10,5 %** | 1.988 |
| 4 d | +4,20 % | −0,44 | +4,63 % | 14,7 % | 1.868 |
| 5 d | +4,76 % | −0,55 | +5,30 % | 18,4 % | 1.758 |
| 7 d | +5,99 % | −0,77 | +6,75 % | 24,1 % | 1.541 |
| **10 d** | **+7,09 %** | −1,09 | **+8,19 %** | **30,3 %** | 1.205 |

*(Ventana de producción, 16/08–06/09.)*

## Pero la rueda no gira por operación: gira por día de capital

Y esa columna dice lo contrario:

| m | Neto | **Neto POR DÍA** | Pierde |
|---|---:|---:|---:|
| **1 d** | +1,36 % | **+1,36 %** | **2,8 %** |
| 2 d | +2,66 % | +1,33 % | 6,6 % |
| 3 d | +3,73 % | +1,24 % | 10,5 % |
| 5 d | +5,30 % | +1,06 % | 18,4 % |
| 10 d | +8,19 % | **+0,82 %** | 30,3 % |

**Por día de capital inmovilizado el máximo está en UN día, y cae de forma
monótona.** Aguantar más gana más por operación y menos por día, y además pierde
tres veces más a menudo (2,8 % → 30,3 %).

**Sale igual en las dos ventanas**, con marea a favor y en contra: el máximo por
día está siempre en 1.

## Qué significa eso, y qué no

**3 días no es el máximo de ninguna de las dos métricas.** Está en medio: ni
captura lo que da aguantar, ni cobra lo que da rotar.

Cuál de las dos manda depende de qué escasee:

- **Si escasea el capital** —que es lo que decía el estudio de la rueda: el límite
  vinculante era CAPITAL— **manda el rendimiento por día, y lo corto gana.**
- **Si escasea el material** —que es lo que pasa HOY: cero comprables de 47— **manda
  el rendimiento por operación, y lo largo gana**, porque el capital iba a estar
  parado de todos modos.

**No he movido el horizonte.** Es tuya la decisión y no es obvia: depende de cuál
de los dos cuellos de botella creas que va a mandar los próximos meses, y eso no
lo contesta el retrotest.

---

# 2. ¿AGUANTA EL +4,47 % FUERA DE AGOSTO? — Sí, y sube

Es la pregunta que más me preocupaba, porque todo se midió en "la semana más rara
del año". **Agosto y el resto, por separado, horizonte 3, racha de 1 día:**

| Ventana | 1-2 % | 2-4 % | > 4 % |
|---|---:|---:|---:|
| **La semana del 12-17 ago** *(donde se midió)* | +3,20 % (47) | sin muestra | sin muestra |
| Los 22 días de producción | +4,52 % (52) | sin muestra | +31,82 % (57) |
| **TODO MENOS esa semana** | **+4,84 % (48)** | sin muestra | +25,07 % (58) |
| Agosto entero | +4,35 % (89) | +8,11 % (75) | +24,00 % (83) |
| **Temporada entera** | **+4,37 % (99)** | **+8,33 % (86)** | **+24,44 % (94)** |

**Fuera de la semana de agosto rinde MÁS, no menos: +4,84 % contra +3,20 %.** El
número no era una rareza de agosto; si acaso, agosto lo estaba deprimiendo.

**Septiembre no puede contestar todavía**: solo van 6 días y ninguna celda de
tramo llega a 30 operaciones. Sale "sin muestra", no "sale mal". En dos semanas
sí se podrá.

---

# 3. ¿SIGUE EL 3 % DONDE TIENE QUE ESTAR? — Sí, y ahora se ve por qué

Con muestra de verdad, el listón cae **exactamente en la frontera** entre el tramo
que no paga y el que sí:

```
   0,25-0,5 %   +1,91 %   |
   0,5-1 %      +2,50 %   |  por DEBAJO del 3 %
   ------------------------  <-- el liston
   1-2 %        +4,37 %   |
   2-4 %        +8,33 %   |  por ENCIMA
   > 4 %       +24,44 %   |
```

*(Temporada, h=3, racha 1 día.)*

**No hay ningún tramo a caballo.** El 3 % separa limpiamente, y ahora con 99
operaciones por celda en vez de 44. **Confirmado por tercera vez, y esta es la
primera con muestra.**

## Pero el motivo escrito al lado del 3 % está mal, y conviene saberlo

En `rival_bid_model.py` el 3 % se justifica así:

> *"los precios de Biwenger se mueven a saltos de 10.000 EUR, que sobre un jugador
> de precio medio son justo un 3 %"*

**Medido sobre el catálogo de hoy, eso solo es cierto para los más baratos:**

| | Precio | 10.000 EUR sobre él |
|---|---:|---:|
| p25 | 370.000 | 2,70 % |
| **mediana** | **1.570.000** | **0,64 %** |
| p75 | 3.250.000 | 0,31 % |

**Un salto de 10.000 EUR son el 3 % solo por debajo de 333.333 EUR: 135 de 578
jugadores (23 %).** Para el jugador mediano el suelo de ruido real es **0,64 %**,
casi cinco veces menos.

**El número está bien; la frase que lo explica, no.** Y eso importa porque el día
que alguien quiera mover el 3 % va a leer esa frase y creer que está tocando un
suelo de ruido cuando estaría tocando otra cosa. **No lo he cambiado** —ningún
umbral se mueve— pero queda dicho, con su número, como pide la regla 18.

---

# 4. LAS CELDAS VACÍAS — de 6 llenas a 26 de 28

| Ventana | Celdas con muestra (h=3) | Operaciones |
|---|---:|---:|
| La semana de agosto | **6 de 28** | 3.686 |
| Los 22 días de producción | 25 de 28 | 43.594 |
| **Temporada entera** | **26 de 28** | **81.788** |

## Y con ellas se cierra el agujero del 15/09

Aquel día quedó escrito que la vía TENER se encendió con una celda de racha de
**un** día y se aplicó a Roro Riquelme (51 días), Amatucci (20) y Pedri (8) —
rachas que **no existían en el retrotest**. Con 6 días de ventana la racha máxima
medible a horizonte 3 era **dos**.

**Ahora la banda «> 7 días» existe, y con muestra grande:**

| Tramo | Mediana | n | Pierde |
|---|---:|---:|---:|
| CAE | −3,93 % | 1.731 | 93,2 % |
| 0-0,25 % | +0,17 % | 113 | 45,1 % |
| 0,25-0,5 % | +0,64 % | 270 | 32,2 % |
| 0,5-1 % | +1,59 % | 555 | 15,3 % |
| **1-2 %** | **+3,46 %** | **572** | **6,3 %** |
| **2-4 %** | **+5,61 %** | **307** | 8,8 % |
| **> 4 %** | **+15,97 %** | **293** | 2,0 % |

**Las rachas largas aguantan por encima del listón.** Roro y Amatucci caen en esa
banda, y ya no son una extrapolación: son 572 operaciones.

**Rinden menos que las rachas cortas** (+3,46 % contra +4,37 % en el 1-2 %), así
que la dirección que se midió en agosto era correcta: el rendimiento baja con la
racha. Pero **baja mucho menos de lo que se temía**, y no cruza el listón.

**No hay que cambiar nada para aprovecharlo.** El tope de racha se calcula solo:

```python
observada = min(tope_de_banda[banda], (resultado["days"] or 1) - 1 - horizon)
```

Con 6 días daba 2. Con el almacén de producción creciendo hacia 60 días de
retención, **subirá a 8 él solo** en cuanto haya días. **Nada que tocar: solo
esperar.**

---

# LO QUE ENTRA EN EL COMMIT

`git status` antes. **Cuatro ficheros:**

```
 M scripts/run_validation_gate.py             + 1 guardia
?? src/analysis/test_calibracion_larga_v1.py  11 pruebas, mercados inventados
?? scripts/bajar_historico_precios.py         el histórico, solo GET, con reanudación
?? scripts/recalibrar_ventana_larga.py        el retrotest por ventanas + la marea
```

**No entra ningún dato.** El histórico descargado son 2 MB de estado mutable y se
queda fuera del repo; el script lo vuelve a bajar cuando haga falta.

## La guardia: «una mediana sin su marea no es un dato»

Once pruebas sobre **mercados sintéticos con la marea puesta a mano**, ni una
lectura de estado. La que importa: un mercado donde **todos** suben un 1 % diario
y nadie se distingue de nadie. Ahí "comprar el que sube" no puede aportar nada, y
la guardia exige que el bruto salga alto **y el neto salga cero**. Si la resta de
la marea se rompe, esa prueba se pone roja antes de que nadie publique un +10 %
que era la marea.

---

# LO QUE NO HE HECHO, Y POR QUÉ

**No he movido el horizonte de 3**, aunque las dos métricas apuntan fuera de él —
en direcciones opuestas. Es tu decisión y depende de qué cuello de botella mande.

**No he movido el 3 %**, que además sale confirmado.

**No he tocado la frase que lo justifica** en `rival_bid_model.py`, aunque está
medida mal. Cambiarla es tocar el comentario de un umbral y prefiero que lo veas
primero.

**No he completado los 160 jugadores que faltan.** Biwenger me limitó y paré: esa
API la necesita producción.

**No he rehecho la rueda con los números nuevos.** El techo mensual se calculó con
el +4,47 % y ahora hay una curva entera por horizonte; recalcularlo cambia la cifra
que decide cuánto esfuerzo merece todo lo demás. Es lo siguiente.

**No he comprado, vendido ni respondido a ninguna oferta.**

---

**La frase para mañana:** la calibración entera estaba medida sobre seis días de
agosto y ahora está medida sobre **81.788 operaciones**. **Todo lo que encendiste
esta semana sigue respaldado y con más margen** —el tramo justo pasó de sobrarle
0,22 puntos a sobrarle 1,37—, **el +4,47 % rinde MÁS fuera de agosto que dentro**
(+4,84 contra +3,20), y **el 3 % cae exactamente en la frontera** entre el tramo
que no paga y el que sí. Se llenaron **26 de 28 celdas** y con ellas la banda de
rachas largas, así que Roro y Amatucci dejan de ser una extrapolación. Y aparecen
dos cosas que no buscaba: **el horizonte de 3 días no es el máximo de ninguna
métrica** —por operación gana 10, por día de capital gana 1—, y **el motivo escrito
al lado del 3 % solo vale para 135 de 578 jugadores**.
