# El ocho por ciento — informe

**Rama:** `medir/el-ocho-por-ciento` (desde `main` en `9c30c34`)
**Fecha:** 15/09/2026
**Verja:** 139/139 en verde, exit 0, salida a fichero
**Push:** NO.
**Escrituras contra Biwenger:** ninguna. Ningún umbral tocado.

---

## 0. Antes de nada: el 8 % no se sostiene

Hiciste bien en poner este bloque primero. **El +8,02 % no es una mediana: es una
compra.**

### Contra qué estaba medido

Contra el catálogo de una **foto del mismo día** (`snapshot_*.json`). Dos agujeros,
los dos medidos:

**1. Las fotos tienen el hueco que recordabas.** De nuestras **24 compras, sólo 5**
caen en un día con foto. Las fotos cubren 9 días sueltos.

```
manager       compras  con FOTO   con PRECIO DEL DIA
Pollo17            61        11                   51
Luismi_Haz         45        16                   33
Pepe               24         5                   21
Manzagool          24         3                   16
```

**2. Y la foto no es del momento de la compra.** Nuestras compras se resuelven a las
**07:0x de Madrid**; la foto del 13/09 es de las **17:17**. Diez horas después, y los
precios se mueven todos los días.

Medido sobre un caso: para **Trent**, la foto dice 2.730.000 y **nuestro propio
registro de puja anotó 2.760.000**. La foto daba +1,10 % donde la verdad era
+0,00 %.

### Y el 8,02 % ni siquiera es la mediana de esas cinco

Éstas son las 5, ordenadas:

```
Fortuño        12/09    +0,25 %
Diego Conde    12/09    +0,25 %
Trent          13/09    +1,10 %   <- la mediana de las cinco
Rubén García   13/09    +8,02 %   <- el 8,02 % es ESTA compra
Yusi           17/08   +29,23 %
```

`scripts/los_viajes_de_los_rivales` imprime hoy mismo **NOSOTROS +1,10 % (n=5)**. El
+8,02 % que abrió el encargo es **una sola compra**, y la de Pollo (+0,04 %) tampoco
sale de ahí: ese cuadro dice −0,05 % (n=11).

**No paramos aquí porque hay una referencia mejor**, y la tenías en disco.

### La referencia buena: el precio del día

`data/autopilot/price_history.json` guarda una serie por jugador **con marca de
tiempo**, y cubre del **16/08 al 15/09 sin huecos**. Con ella, **21 de nuestras 24
compras** tienen referencia.

**Y la hora no se supone, se mide.** Sobre **11.252 cambios de precio observados**,
el **89,8 %** aparece por primera vez en la muestra de las **07h de Madrid**; el
99,9 % ha entrado antes de las 10h. Así que:

> precio del día = la **primera** muestra de ese día a partir de las 07:00

`cuando_cambian_los_precios()` **recalcula ese histograma** desde la serie que se le
pase: la regla es medible, no un comentario.

### Contrastada contra nuestro propio libro

`bid_outcome_ledger` anota el `market_price` que el motor veía al pujar:

```
anotadas EN VIVO        coinciden al euro 11,  distintas 4
RECONSTRUIDAS luego     coinciden  0,          distintas 8
```

Las **4 distintas en vivo** se pujaron antes de las 07:00 y el precio cambió entre la
puja y la resolución — que es exactamente lo que esta referencia dice que pasa
(Cáceres 1.500.000 → 1.450.000, Sotelo y Balde 1.600.000 → 1.570.000, Larrubia
4.790.000 → 4.750.000).

Las **10 reconstruidas** a posteriori desde la plantilla no coinciden en ninguna, **y
no deberían**: su `market_price` es el del día en que se reconstruyeron. Por eso no
valen de contraste y se cuentan aparte.

### El número, con su n

| | prima de compra | |
|---|---:|---|
| **Pepe** | **+2,17 %** | n=21 |
| **Pollo17** | **+1,37 %** | n=51 |
| Luismi_Haz | +1,20 % | n=33 |
| Manzagool | +6,43 % | n=16 |
| Prinzipote | +0,01 % | n=7 |

**No somos el peor comprador de la liga.** Manzagool paga +6,43 %. Y la distancia
con Pollo es de **0,8 puntos**, no de 8.

**La prima del Computer al recomprar: +2,42 % (n=135)** — tu +2,03 % aguanta bien.

---

## 1. De dónde sale nuestra prima: era agosto, como sospechabas

```
TODAS                 +2,17 % (n=21)

2026-08              +10,80 % (n=10)    sin rival +10,80 % (n= 4)   con rival +11,03 % (n= 6)
2026-09               +0,25 % (n=11)    sin rival  +0,25 % (n=10)   con rival  +4,23 % (n= 1)
```

**Los dos mundos que planteabas: estamos en el primero.** El problema era de agosto,
con el mecanismo viejo. En septiembre pagamos **+0,25 %**.

### Por vía

```
SPECULATION                   +0,25 % (n=6)      <- el carril, limpio
CARRIL/RENDIJA                +1,10 % (n=1)
XI_UPGRADE                    +6,12 % (n=2)      <- aquí sigue la fuga
RECONSTRUIDA (agosto)         +7,31 % (n=8)
SIN LIBRO (mecanismo viejo)  +19,99 % (n=4)
```

**El carril está limpio.** Las seis compras de SPECULATION pagan **+0,25 % clavado**
las seis — es la política de euro exacto funcionando.

### Pero hay algo que sí hay que mirar, y no es el carril

**`XI_UPGRADE` paga de más por construcción.** Los dos únicos casos, de nuestro
propio libro de pujas:

```
Kiko Femenía   market 1.150.000 -> puja 1.229.925   (+6,95 %)   win_probability 0,5591
Rubén García   market 2.680.000 -> puja 2.873.240   (+7,21 %)   win_probability 0,5481
```

No puja *precio + mínimo*: puja **a una probabilidad de victoria objetivo (~0,55)**
derivada de `our_value`. Y los dos ganaron.

**Rubén García tuvo CERO rivales.** Pagamos **+213.240 €** por encima del precio del
día en una subasta que nadie más miraba. Ése es, literalmente, el +8,02 % del
encargo.

> **Aviso de n:** son **dos** compras. Es suficiente para entender el mecanismo
> —está escrito en el libro de pujas, no deducido— pero no para afirmar una mediana.

### La peor y la mejor, con nombre

```
PEOR    17/08   Yusi         pagó   504.000 contra   390.000   +29,23 %   (+114.000 €)
MEJOR   15/09   Oriol Rey    pagó 1.122.020 contra 1.150.000    -2,43 %    (-27.980 €)
```

### ¿Arrastran pocas compras caras la mediana?

Sí, pero sólo la **media**. Mediana +2,17 %, media +6,35 %; quitando las tres peores
(+15,0 %, +25,0 %, +29,2 %) la media cae a +3,57 %. Las tres son de agosto.

**En euros: pagamos +1.696.264 € por encima del precio del día** en esas 21 compras.
Casi todo en agosto.

Y **3 compras sin precio del día** (Yamal, Jonny y Suazo, del 10/08 — antes de que el
almacén existiera). **No se les estima ninguno.**

---

## 2. Cómo compra Pollo: las tres preguntas

### ¿Compra sólo lo que nadie le disputa? **No.**

```
manager       compras        sin rival         con rival
Pepe               21    +0,51 % (n=14)    +9,42 % (n= 7)
Pollo17            51    +0,18 % (n=25)    +2,86 % (n=26)
Luismi_Haz         33    +0,05 % (n=13)    +5,17 % (n=20)
```

Está **más disputado que nosotros** (26 de 51 frente a 7 de 21). No es la respuesta.

Pero esta tabla contiene el hallazgo: **sin rival los dos pagamos ~0 %. Con rival,
nosotros +9,42 % y él +2,86 %.**

**Cuidado, porque el cruce con el mes lo desmonta como problema actual:**

```
Pepe     2026-08  sin rival +10,80 % (n=4)    con rival +11,03 % (n=6)
Pepe     2026-09  sin rival  +0,25 % (n=10)   con rival  +4,23 % (n=1)
```

En agosto pagábamos +10,8 % **hubiera o no competencia**. No era un problema de
subasta: era el mecanismo. Y de septiembre con rival hay **n=1**: no se puede
concluir nada.

### ¿Puja el mínimo y asume perder muchas? **La segunda mitad, sí.**

```
manager       ganadas  perdidas  peleadas    gana
Pepe               23        10        33     70%
Pollo17            57        46       103     55%
Luismi_Haz         44        38        82     54%
```

**Pelea 103 subastas y gana el 55 %. Nosotros peleamos 33 y ganamos el 70 %.**

Eso es lo que confirma tu propuesta: **él pierde el 45 % de las subastas sin drama**,
y las pelea tres veces más. Nosotros pujamos poco y para ganar.

Pero la primera mitad —"puja el mínimo"— **no**: paga +1,37 % de mediana. De hecho
**nuestra vía de especulación (+0,25 %) compra más barato que él.** Lo que no hace es
comprar tanto.

### ¿Evita la subasta del reset? **No.**

```
Pepe        {7h: 23, 8h: 1}      96 % en el reset
Pollo17     {7h: 58, 18h: 2, 19h: 1}   95 % en el reset
```

Idénticos. No es la respuesta.

### Entonces, ¿qué hace él que nosotros no?

**Volumen con disciplina de precio.** 103 subastas peleadas contra nuestras 33,
aceptando perder casi la mitad, pagando +1,37 % de mediana. Nosotros compramos poco,
y cuando decidimos que queremos a alguien, pujamos a probabilidad de victoria.

---

## 3. Los viajes cerrados, con la definición de la liga

Tu cuenta estaba mal, y por la razón que dijiste: **44 son operaciones, no viajes.**

```
manager       viajes     beneficio   euro/viaje    dias
Pollo17           45   +10.315.724     +229.238     6,9
Luismi_Haz        30    +9.289.794     +309.660     9,7
Manzagool         13    -2.951.310     -227.024     9,3
Pepe               9      +788.252      +87.584    12,2
DiosMande          3    -1.357.400     -452.467    21,0
```

**Tenemos 9 viajes cerrados, +788.252 en total, +87.584 por viaje.** (La liga va por
100 viajes cerrados, uno más que los 99 de la semana pasada.)

### Y la pregunta que lo explica todo: **sí, él corta y nosotros no**

```
manager       viajes  en pérdida     %    lo perdido   días si pierde   días si gana
Pollo17           45           4     9%     -697.200              5,1            7,1
Luismi_Haz        30          10    33%   -1.213.602              5,7           11,7
Pepe               9           3    33%     -649.227             11,6           12,6
Manzagool         13          11    85%   -3.125.130              8,7           12,5
```

**Léelo en la penúltima columna.** Pollo cierra un viaje perdedor en **5,1 días**.
Luismi, en **5,7**. Nosotros aguantamos **11,6 días** — más del doble — y encima
nuestros ganadores no duran más que los perdedores (12,6 contra 11,6): **no cortamos,
esperamos**.

Y fíjate en Manzagool: pierde en el 85 % de sus viajes y aguanta 8,7 días. Es el
único que pierde dinero comerciando. **La disciplina de corte separa a los dos que
ganan (Pollo, Luismi) del resto.**

Nuestros 9 viajes, uno a uno:

```
Yusi            504.000 -> 1.226.068    +722.068   18,6 d
Cepeda          463.500 ->   681.000    +217.500   27,0 d
Jonny         1.570.000 -> 1.753.200    +183.200   10,2 d
Suazo         1.629.832 -> 1.788.400    +158.568   10,2 d
Castrón       1.200.001 -> 1.346.045    +146.044    6,0 d
Diego Conde     240.601 ->   250.700     +10.099    3,3 d
Kiko Femenía  1.229.925 -> 1.159.000     -70.925    4,2 d
Zubeldia      2.068.001 -> 1.847.000    -221.001   26,8 d
Bigas         2.288.001 -> 1.930.700    -357.301    3,8 d
```

**Zubeldia: 26,8 días para perder 221.001 €.** Eso es exactamente lo que Pollo no
hace.

---

## 4. Las dos doctrinas, aplicadas — y lo que incumplían

**Doctrina 54** (numerador y denominador, el mismo periodo). «Compramos al +8 % y
cobramos el +2 %» restaba una mediana de 5 compras medidas contra fotos sueltas
contra una prima de venta de otra muestra y otros meses. **La resta no significaba
nada.**

Hecha bien, con las dos mitades del mismo periodo y cada una con su n:

```
Pepe     2026-08   compra +10,80 % (n=10)  contra venta +0,87 % (n= 8)   ->  9,93 puntos BAJO el agua
Pepe     2026-09   compra  +0,25 % (n=11)  contra venta +4,46 % (n= 5)   ->  4,21 puntos POR ENCIMA
Pepe     todo      compra  +2,17 % (n=21)  contra venta +1,15 % (n=13)   ->  1,02 puntos bajo el agua

Pollo17  2026-08   compra  +1,18 % (n=32)  contra venta +3,33 % (n=24)   ->  2,15 por encima
Pollo17  2026-09   compra  +2,06 % (n=19)  contra venta +2,66 % (n=19)   ->  0,60 por encima
```

**«Cada viaje nace seis puntos bajo el agua» era verdad en agosto —y peor: casi
diez— y es falsa ahora.** En septiembre nacemos 4,21 puntos por encima.

`bajo_el_agua()` **se niega a restar** si falta una de las dos mitades, y lo dice
citando la doctrina. Hay guardia.

**Doctrina 53** (un porcentaje sin su plazo no es un rendimiento). No he publicado
ninguna prima como rendimiento: una prima de compra es un **precio relativo en un
instante**, no un retorno. Donde sí hay plazo —los viajes— va siempre con sus días.

---

## 5. Lo que no hice, y por qué

- **Ni una escritura contra Biwenger.** Ni pujas, ni ofertas, ni ventas.
- **Ningún umbral tocado**: ni techo, ni suelo de cobro, ni cupo, ni `bid_cap`.
- **No encendí el techo del que se queda.** Va después, y esto refuerza que vaya
  después: hay una vía (`XI_UPGRADE`) que paga +7 % por diseño.
- **No toqué `XI_UPGRADE`**, aunque es donde está la fuga. Es un cambio de política
  de puja y la decisión es tuya. Lo que hace falta saber está arriba: puja a
  probabilidad de victoria objetivo desde `our_value`, y ganó las dos veces —una de
  ellas sin ningún rival.
- **No estimé ningún precio que no constara.** 3 compras del 10/08 se quedan sin
  referencia y se cuentan aparte.
- **No toqué el workflow. No empujé.**
- **No arreglé el almacén de precios para cubrir del 09/08 al 15/08.** No se puede:
  esos precios no existen en ninguna parte.

### Dos cosas que conviene que sepas

**Un arreglo que salió por el camino.** Las pujas perdedoras se contaban sobre los
eventos crudos, así que una subasta reemitida sumaba sus perdedores dos veces: a
Pollo le salían **60 pujas perdidas donde tiene 46**. Ahora se cuentan sobre la
operación ya deduplicada.

**Un aviso sobre el huso horario.** Madrid está fijado a UTC+2, igual que en
`los_viajes_de_los_rivales.py`. Los datos van del 09/08 al 15/09, entero dentro del
horario de verano, así que hoy es correcto. **El día que esto cruce el último domingo
de octubre hará falta una zona horaria de verdad**, y la hora del cambio de precio
—07:00— se moverá con ella. Está escrito en la cabecera del módulo y de la guardia.

---

## 6. Lo que queda en el repo

```
src/analysis/la_prima_de_compra.py        la cuenta. No lee disco, ni red, ni reloj
scripts/el_ocho_por_ciento.py             lee los ficheros e imprime los tres bloques
src/analysis/test_la_prima_de_compra_v1.py   9 pruebas
scripts/run_validation_gate.py            +1 línea
```

```
python -m scripts.el_ocho_por_ciento
python -m scripts.el_ocho_por_ciento --detalle
```

| guardia | qué pasa si se rompe |
|---|---|
| `test_la_referencia_es_la_del_dia_de_la_compra` | vuelve el precio de la víspera o el de la foto de la tarde |
| `test_sin_muestra_del_dia_no_hay_precio_ni_estimacion` | se inventa una referencia donde no la hay |
| `test_la_hora_del_cambio_se_mide_no_se_escribe` | las 07:00 pasan a ser una opinión con cara de constante |
| `test_ninguna_mediana_viaja_sin_su_n` | vuelve un «8,02 %» sin decir que son cinco |
| `test_no_se_restan_periodos_distintos` | **doctrina 54**: se restan mitades de meses distintos |
| `test_la_competencia_sale_del_tablon_y_no_se_duplica` | una subasta reemitida duplica perdedores |
| `test_el_fixture_trae_de_todo` | **regla 24**: las demás se ponen verdes sin probar nada |

**Las tres importantes, probadas reintroduciendo el fallo** (en memoria, sin tocar el
fichero):

```
la referencia pasa a ser la muestra de la tarde   ->  5 guardias en rojo
restar sin las dos mitades                        ->  1 guardia en rojo
un bloque vacío publica cero en vez de nada       ->  1 guardia en rojo
```

El fixture lleva a propósito una muestra de las **17:17 con otro precio**: es la que
hacía que un +8 % pareciera un +20 %, y hay guardia de que no se usa.
