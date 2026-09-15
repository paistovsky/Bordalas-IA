# De dónde salió el dinero — informe

**Rama:** `medir/de-donde-salio-el-dinero` (desde `main` en `6c1fa2c`)
**Fecha:** 15/09/2026
**Verja:** 137/137 en verde, exit 0, salida a fichero (137 = 136 + la guardia nueva)
**Push:** NO.
**Escrituras contra Biwenger:** ninguna. Ni una puja, ni una oferta, ni una venta,
ni una renovación.

---

## 0. La respuesta, en tres líneas

**Tu predicción era falsa.** Comprar y vender no solo puede explicar parte de los
55 M de Pollo: le da **+10.315.724**, cinco veces el techo que predijiste, y **más
del doble** de lo que le ha dado tener a sus jugadores quietos (+4.899.948).

Pero el trozo más grande no es ninguno de los dos: son los **33,3 M de la
plantilla que le regaló el reparto** y que nadie pagó. Eso lo tienen los ocho, así
que no explica la diferencia. **Lo que sí la explica es el comercio.**

---

## 1. Qué se leyó, y de cuándo

```
eventos   board_events.json        314 eventos, el último 15/09 13:08 UTC
censo     profiles_cache.json      15/09 16:35 UTC, las ocho plantillas
precios   snapshot_20260913_171717 570 jugadores — 13/09 17:17
```

**Las tres fuentes no son de la misma hora y el script lo imprime siempre.** Los
precios son los más viejos de los tres: el catálogo del 13/09. No hay ninguno más
fresco en disco. Consecuencia concreta: un jugador comprado el 14 o el 15 se
valora a su precio del 13, así que su "subida" sale algo desplazada. No afecta al
cuadre —las dos orillas usan el mismo precio— pero sí al reparto fino entre
*subida* y *viajes* de los últimos dos días.

De 351 operaciones deduplicadas, 5 jornadas pagadas de 6 (la Jornada 1 partida no
paga, `splitRound: ignoreFirst`).

---

## 2. La tabla de los ocho, y cuadra

```
manager             premios        viajes        subida     4º montón
Pollo17           8.440.000   +10.315.724    +4.899.948    33.305.800
Luismi_Haz        7.030.000    +6.435.994   +10.964.999    28.966.900
Mex               6.710.000             0      -610.000    26.980.800
Prinzipote        6.050.000             0      -416.228    27.141.000
Pepe Bordalás     7.760.000      +788.252    -2.769.835    26.573.300
Álvaro Retamosa     950.000             0      -100.000    28.225.200
Manzagool         6.600.000    -2.951.310      -183.940    25.045.300
DiosMande         6.090.000    -1.357.400    -5.162.517    25.921.400
```

| manager | 23.300.000 + los cuatro | patrimonio de hoy | cuadra |
|---|---:|---:|:--:|
| Pollo17 | 80.261.472 | 80.261.472 | **sí** |
| Luismi_Haz | 76.697.893 | 76.697.893 | **sí** |
| Mex | 56.380.800 | 56.380.800 | **sí** |
| Prinzipote | 56.074.772 | 56.074.772 | **sí** |
| Pepe Bordalás | 55.651.717 | 55.651.717 | **sí** |
| Álvaro Retamosa | 52.375.200 | 52.375.200 | **sí** |
| Manzagool | 51.810.050 | 51.810.050 | **sí** |
| DiosMande | 48.791.483 | 48.791.483 | **sí** |

**Diferencia cero en los ocho.** No hay ningún descuadre que reportar.

### Qué prueba ese cuadre y qué no

Prueba que **el reparto en montones no inventa ni se come euros**: si una compra
se contara dos veces, o una venta se perdiera, la identidad se rompería.

**No prueba que la caja sea cierta.** Las dos orillas beben de la misma
reconstrucción. La caja solo se puede auditar contra un saldo real, y la liga
tiene `settings.balance = "hidden"`: el único saldo visible es el nuestro, y el
que hay en disco es de la foto del 13/09 (−1.299.834) contra una reconstrucción
del 15/09 (131.717). Esos 1.431.551 de separación son **dos días de actividad**,
no un descuadre — es exactamente el falso rojo que ya documenta
`caja_de_la_liga.cuadra` ("lo que estaba viejo era el otro lado"). Para cerrarlo
de verdad haría falta un saldo fresco, y eso es una lectura contra la API que no
he hecho.

### Dos fuentes para el coste, y coinciden

De cada jugador que alguien compró y sigue teniendo hay dos precios
independientes: el del tablón (emparejando compra con venta, FIFO) y el
`owner.price` de Biwenger.

```
coinciden al euro   81 de 81
discrepan            0
solo una fuente      0
```

Y la cola FIFO sobrante coincide **jugador a jugador** con el censo en los ocho:
cero jugadores en el libro que no estén en la plantilla, y los que están en la
plantilla sin cola son exactamente los que a Biwenger tampoco le constan.

---

## 3. El cuarto montón: 39 jugadores y 222 M

```
manager          en plantilla    valen hoy   vendidos        cobró
Pollo17                     1    4.630.000         14   28.675.800
Luismi_Haz                  0            0         15   28.966.900
Mex                        10   24.420.000          5    2.560.800
Prinzipote                  9   23.940.000          6    3.201.000
Pepe Bordalás               4   11.070.000         11   15.503.300
Álvaro Retamosa             9   24.850.000          6    3.375.200
Manzagool                   2    6.200.000         13   18.845.300
DiosMande                   4    9.800.000         11   16.121.400

TOTAL                      39  104.910.000         81  117.249.700
```

**39 jugadores en plantilla sin coste conocido, 104.910.000 a precio de hoy.** Más
81 vendidos por 117.249.700 que tampoco tenían coste. Son **222.159.700** en
total, y es el montón más grande de los cuatro para los ocho sin excepción.

El reparto del `leagueReset` (12 jugadores a cada uno) **no dejó precios en
ninguna fuente**: ni en el tablón ni en `owner.price`. Su subida no se puede
calcular, así que no se calcula. No se reparte a ojo entre los otros tres montones.

Avisabas de que si el tablón no traía el reparto inicial el cuarto montón sería
grande. Lo es: **entre el 54 % y el 102 % del crecimiento de cada uno.**

```
manager             crecimiento   premios   viajes   subida   4º montón
Pollo17              56.961.472     14,8%    18,1%     8,6%       58,5%
Luismi_Haz           53.397.893     13,2%    12,1%    20,5%       54,2%
Mex                  33.080.800     20,3%     0,0%    -1,8%       81,6%
Prinzipote           32.774.772     18,5%     0,0%    -1,3%       82,8%
Pepe Bordalás        32.351.717     24,0%     2,4%    -8,6%       82,1%
Álvaro Retamosa      29.075.200      3,3%     0,0%    -0,3%       97,1%
Manzagool            28.510.050     23,1%   -10,4%    -0,6%       87,8%
DiosMande            25.491.483     23,9%    -5,3%   -20,3%      101,7%
```

**Ojo con leer esto como "el 82 % de nuestro crecimiento es suerte".** No es
beneficio: es una dotación que a todos se les dio y que está valorada a mercado.
Lo que decide quién va delante es lo que cada uno hizo *encima* de ella.

---

## 4. Pollo, Luismi y nosotros

```
                          POLLO17      LUISMI_HAZ    NOSOTROS
operaciones                   120              89          44
  compras                      61              45          24
  ventas                       59              44          20
viajes cerrados                45              29           9
  en verde                  41/45           19/29         6/9
aguanta de media          6,9 días        9,0 días   12,2 días
  (mediana)               5,1 días        6,0 días   10,2 días
euro por viaje           +229.238        +221.931     +87.584

VENDER le ha dado     +10.315.724      +6.435.994    +788.252
TENER le ha dado       +4.899.948     +10.964.999  -2.769.835
  jugadores quietos            16              16          15
  días de media              10,5            13,4        11,3

reparto vender/tener        68/32           37/63       22/78
```

### ¿Pollo es comerciante o coleccionista?

**Comerciante, y de los que aciertan.** 120 operaciones en 37 días —más de tres
al día—, 45 viajes cerrados, y aguanta a un jugador **6,9 días de media** antes de
venderlo. Acierta en **41 de 45**. Es el que más compra, el que más vende y el que
menos tiempo tiene la mercancía en el almacén.

**Luismi llega casi igual de lejos por el camino contrario.** 29 viajes, pero su
dinero viene sobre todo de tener: +10,9 M de subida quieta contra +6,4 M de
comercio. Es el mejor de los ocho teniendo (+685.312 por jugador quieto).

**Nosotros no hacemos ni lo uno ni lo otro.** 44 operaciones —la tercera parte que
Pollo—, 9 viajes que dan +788.252, y una plantilla quieta que **pierde**
2.769.835. Aguantamos 12,2 días de media, casi el doble que Pollo, y en un mercado
donde el viaje mediano dura 5,8.

### Lo que hizo él que nosotros no

La pregunta buena. El hueco contra nosotros, repartido:

**Pollo nos saca 24.609.755:**

| trozo | diferencia | % del hueco |
|---|---:|---:|
| viajes | +9.527.472 | **38,7 %** |
| subida quieta | +7.669.783 | 31,2 % |
| 4º montón (el reparto) | +6.732.500 | 27,4 % |
| premios | +680.000 | 2,8 % |

**Luismi nos saca 21.046.176:**

| trozo | diferencia | % del hueco |
|---|---:|---:|
| subida quieta | +13.734.834 | **65,3 %** |
| viajes | +5.647.742 | 26,8 % |
| 4º montón | +2.393.600 | 11,4 % |
| premios | −730.000 | −3,5 % |

Hay dos caminos y los dos funcionan. El de Pollo es comerciar. El de Luismi es
fichar mejor y aguantar. **Nosotros no estamos en ninguno de los dos**, y nuestro
único trozo positivo aparte del reparto son los premios —donde vamos segundos, que
es lo que se hace bien—.

---

## 5. Cuánto da un viaje y cuánto da tener quieto

```
COMPRAR Y VENDER   n=99   medio +133.649   mediana  +84.300   70/99 en verde
                          dura 8,7 días de media (5,8 de mediana)

TENER QUIETO       n=81   medio  +81.758   mediana     -376   35/81 en verde
                          lleva 14,7 días de media (11,5 de mediana)

POR DÍA DE CAPITAL        viaje +15.293/día      quieto +5.552/día
```

Tres cosas que merecen leerse despacio:

1. **El viaje medio de esta liga da +133.649 y el 71 % acaban en verde.** No es la
   prima teórica: es el euro que se ha llevado la gente, 99 veces.

2. **Tener quieto tiene mediana NEGATIVA** (−376) y solo 35 de 81 suben. La media
   sale positiva (+81.758) porque unos pocos aciertos grandes —los de Luismi—
   arrastran al resto. Tener a un jugador al azar en esta liga **no sube**.

3. **Por día de capital inmovilizado, un viaje rinde casi tres veces lo que tener
   quieto** (+15.293 contra +5.552), y además libera el dinero en 5,8 días de
   mediana para volver a usarlo. Esa rotación no está contada en el número: si lo
   estuviera, la distancia sería mayor.

---

## 6. Qué significa `ledger_status: REVIEW_REQUIRED`

Lo pediste antes de fiarte del tablón. La marca se calcula en
[rival_intelligence_engine.py:2433](src/analysis/rival_intelligence_engine.py#L2433):

```python
ledger_status = "EXACT" if (validation["exact"] and not unknown_types) else "REVIEW_REQUIRED"
```

`unknown_types` cuenta los eventos cuyo tipo **no está dado de alta** en
`KNOWN_NON_ECONOMIC_TYPES` y que el bucle del libro por manager no clasifica. Hoy
son 21 de 314:

| tipo | n | qué es | ¿mueve euros de la liga? |
|---|---:|---|---|
| `roundFinished` | 7 | los abonos de jornada | **sí, y se pagan** |
| `bonus` | 5 | la racha diaria | **sí, y se paga** |
| `bettingPool` | 7 | quinielas | no |
| `userPoints` | 2 | corrección de puntos | no |

**Ninguno de los 21 es un euro sin contar:**

- **`roundFinished` y `bonus` sí se pagan** — pero los paga `caja_de_la_liga`, que
  es un módulo distinto del bucle que rellena `unknown_types`. Cuando
  `caja_de_la_liga` se hizo cargo de los abonos (10/09), **nadie actualizó la lista
  blanca del motor**. Son 47.630.000 de jornada y 2.000.000 de racha repartidos
  entre los ocho —49.630.000 en total— que están dentro de la caja y a la vez
  marcados como "tipo desconocido".
- **`bettingPool`:** los 7 son quinielas `global: true` de toda Biwenger, con
  `credits: {required: 1, prizes: true}`. Los premios son **créditos de la app**,
  no euros de la liga, y los `prizes` son números como `[0, 117]` o `[0,0,27,67,0]`.
  En toda la temporada ha participado una sola persona una sola vez (tú, pool
  627678, 7 aciertos).
- **`userPoints`:** las dos son Pollo17 (admin) ajustándole los puntos a Álvaro,
  el 11/09 y el 15/09. Puntos, no dinero.

**Conclusión: la marca dice "hay tipos de evento que nadie ha dado de alta", no
"las cuentas no salen".** Y es **permanente por construcción**: mientras sigan
terminando jornadas y pagándose rachas, `ledger_status` no podrá volver a ser
`EXACT` aunque todo esté bien. Ya hay un test que documenta ese mecanismo
(`test_ledger_dedup_v1.py:237`: *"sin darlo de alta deja el ledger en
REVIEW_REQUIRED para siempre"*).

**No afecta a este recuento.** Esta medición no lee `ledger_status` ni el libro por
manager: reconstruye desde los eventos y cuadra al euro por su cuenta.

---

## 7. Dos cosas que el encargo daba por hechas y no lo son

### Los ocho no empezasteis con 23.300.000: fuisteis siete

Álvaro Retamosa **entró en la liga el 11/09 a las 18:33**, 33 días después del
reset, y aparece por primera vez en la Jornada 5. Las jornadas 1 a 4 repartieron
entre **siete**. Sus 9 jugadores sin coste tienen `owner.date` = su fecha de
entrada, no la del reparto: le dieron una plantilla y el tablón no dice a cambio de
qué.

Su fila de la tabla **cuadra**, pero cuadra porque las dos orillas asumen los mismo
23.300.000 iniciales. **Ese número es una suposición para él, no una medida.** Su
crecimiento de 29.075.200 y su 97,1 % de cuarto montón hay que leerlos sabiéndolo.

### La caja de los rivales no está auditada contra nada

Ya está en el §2, pero conviene repetirlo aquí: `settings.balance = "hidden"`. De
los siete rivales **no hay ningún saldo real contra el que contrastar**. El método
se valida con el nuestro y se extrapola. Es lo que hay, y es lo que ya hacía
`cash_check`, pero no es lo mismo que medirlo.

---

## 8. Lo que no hice, y por qué

- **No pujé, no oferté, no vendí, no renové.** Ni una escritura contra Biwenger.
- **No cambié ninguna decisión del motor**: ni un umbral, ni una prima, ni un
  techo. Lo del §4 y §5 sugiere cambiar de estrategia; esa decisión es tuya y se
  queda escrita aquí.
- **No toqué** `.github/workflows/bordalas-live.yml`. La guardia nueva entra por
  `scripts/run_validation_gate.py`, que es donde la casa dice que va.
- **No empujé.** La rama está local.
- **No estimé ningún precio que no constara.** 39 jugadores en plantilla y 81
  vendidos se quedaron sin coste y van contados en el §3.
- **No arreglé `ledger_status`.** Dar de alta `roundFinished` y `bonus` en
  `KNOWN_NON_ECONOMIC_TYPES` —o clasificarlos como económicos en ese bucle— pondría
  la marca en `EXACT` y es probablemente lo correcto, pero es tocar el motor y el
  encargo era contar. Queda descrito arriba con el fichero y la línea.
- **No pedí un saldo fresco** para cerrar el cuadre contra la API, por la misma
  razón: todo tenía que salir de ficheros en disco.

### Una cosa que sí hice y no debí

Ejecutando guardias relacionadas para comprobar que no había roto nada, corrí
`src.analysis.test_rival_intelligence_v2`, que **no está en la verja y lee la API
en vivo**. No escribió nada contra Biwenger, pero **sí reescribió cuatro ficheros
locales** — `board_events.json`, `board_latest_raw.json`, `profiles_cache.json` y
`rival_intelligence.json` — dejándolos con datos del 15/09 en vez de los del 14/09
con los que empecé.

Las cifras de este informe son las de **después** del refresco, que son más
frescas y por tanto mejores. Lo medí también antes, con los datos del 14/09:
**cuadraba igual al euro en los ocho y la conclusión era la misma** (Pollo: viajes
+9.950.624 contra subida +5.205.948). El refresco no cambió ninguna respuesta, pero
debí haberlo previsto antes de lanzar ese test y no después.

---

## 9. Tu predicción, contrastada

Lo que escribiste antes de ver el resultado:

> Creo que comprar y vender NO puede explicar los 55 M de Pollo. Si hizo unos 36
> viajes con una prima del orden del +2 % sobre unos 2 M, eso son menos de 2
> millones. Faltarían 53. Mi apuesta es que casi todo viene de que sus jugadores
> subieron mientras los tenía.

**Era falsa.** Lo escribo con esas palabras, como pediste.

Falla en las tres piezas:

| lo que predijiste | lo medido |
|---|---|
| unos 36 viajes | **45** |
| menos de 2 M en total | **+10.315.724** |
| "casi todo viene de tener quieto" | tener quieto le da **+4.899.948**, menos de la mitad que vender |

Dónde se torció el razonamiento: la prima del +2 % es correcta en orden de
magnitud, pero **tratabas cada viaje como una inmovilización de 2 M durante toda la
temporada**. Pollo no inmoviliza: rota. Sus 45 viajes ocupan 6,9 días de media, así
que los mismos euros dan la vuelta seis o siete veces. Un +2 % que se cobra siete
veces no es un +2 %.

Y hay una cuarta cosa que la predicción no contemplaba y resultó ser el trozo
mayor: **los 33,3 M de la plantilla regalada.** De los 57 M de crecimiento de
Pollo, 33 no los ganó nadie — se los dieron el 09/08 y hoy valen eso.

### Qué sugiere esto para la estrategia (decisión tuya, no mía)

El encargo decía: *"Si el dinero sale de comprar y vender, hay que comerciar más."*
Sale de ahí. Y los números de apoyo son estos:

- el viaje medido de esta liga da **+133.649** y acierta **70 de 99**;
- tener un jugador quieto tiene **mediana negativa** y acierta 35 de 81;
- por día de capital, comerciar rinde **casi el triple**;
- **hacemos 44 operaciones donde Pollo hace 120**, y aguantamos 12,2 días donde el
  mercado rota en 5,8.

No he tocado nada. Está escrito y parado.

---

## 10. Lo que queda en el repo

```
src/analysis/de_donde_salio_el_dinero.py       la cuenta. No lee disco, ni red,
                                               ni reloj: se lo pasan todo
scripts/de_donde_salio_el_dinero.py            lee los ficheros e imprime
src/analysis/test_el_dinero_cuadra_v1.py       15 pruebas
scripts/run_validation_gate.py                 +1 línea
```

```
python -m scripts.de_donde_salio_el_dinero
python -m scripts.de_donde_salio_el_dinero --detalle Pollo17
```

Las guardias, con lo que protege cada una:

| guardia | qué pasa si se rompe |
|---|---|
| `test_el_dinero_cuadra` | los cuatro trozos dejan de dar el patrimonio; la diferencia sale **con nombre** |
| `test_cada_trozo_vale_lo_que_tiene_que_valer` | cada trozo contra una cifra calculada a mano, porque dos errores que se cancelan también cuadran |
| `test_ningun_precio_de_compra_inventado` | alguien publica una subida sobre un coste que no viene de ninguna fuente |
| `test_el_del_reparto_va_al_cuarto_monton_valorado` | un jugador del reparto se cuela entre los que tienen coste |
| `test_el_fifo_empareja_con_la_compra_mas_antigua` | comprar-vender-recomprar deja de emparejarse bien |
| `test_una_plantilla_que_cambia_de_manos_descuadra_y_se_dice` | un jugador que desaparece sin venderse se traga en silencio |
| `test_un_coste_que_solo_conoce_biwenger_descuadra_a_proposito` | fija la decisión de **no tapar** un evento perdido del tablón |
| `test_un_jugador_sin_precio_no_vale_cero` | un precio que falta pasa como un cero |
| `test_un_tablon_repetido_no_cambia_los_montones` | la reemisión de Biwenger duplica compras |
| `test_el_fixture_tiene_de_todo` | **regla 24**: sin viajes, quietos y cuarto montón las demás se pondrían verdes sin probar nada |
| `test_sin_eventos_no_hay_descomposicion` | un tablón vacío devuelve una tabla en vez de decir que no puede |

Sin disco, sin red y sin reloj: el tablón es un fixture escrito a mano y el `ahora`
es una constante. Pasado por el escáner de `guardias_que_leen_el_mundo`: **cero
hallazgos** de RELOJ, DISCO o RED.
