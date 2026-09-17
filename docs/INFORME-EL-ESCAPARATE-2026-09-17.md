# El escaparate — informe

**Foto:** `diagnostico/status.json`, **`meta.generated_at` = 2026-09-17T07:30:55**.
Abierta con `encoding="utf-8"`. Los días anteriores, de los 95 `data/snapshot_*.json`.

**Rama:** `medir/el-escaparate` (desde `motor/la-lista-de-la-compra`)
**Verja:** 149/149 en verde, exit 0, salida a fichero
**Push:** NO. **`ENCENDIDO = False`.** Ni una escritura, ni un umbral, ni un
interruptor.

---

## La respuesta corta

> **Tu tesis es verdadera en su conclusión y falsa en su mecanismo.**
>
> Sí: el problema es estar listo, no elegir bien. Y hay un número de 182 subastas que
> lo demuestra. **Pero «estar listo» no es tener caja aparcada esperando a que salga
> alguien.** Hoy, con 8,87 M en el bolsillo de fichar y cuatro fichas libres, había dos
> jugadores en el escaparate que mejoran el once y **ninguno de los dos estaba
> bloqueado por caja ni por ficha.**

---

## BLOQUE 0 — ¿Existe histórico de escaparates? **No**

Lo que hacía pensar que sí, y no es:

```
`censo_del_reset`  ->  "Ya hay censo de este reset: no se duplica"
                       pero es el censo de las OFERTAS QUE RECIBIMOS por
                       jugadores NUESTROS. 10 ofertas, 19.764.500 €.
                       Nada que ver con los veinte del escaparate.

data/solvency/censo_de_ofertas.jsonl        2 líneas (15 y 16/09)
data/trading/libro_de_escaparate.jsonl      NO EXISTE — y ese «escaparate»
                                            es el NUESTRO, publicar para vender
```

**Lo único que hay es indirecto:** los 95 `data/snapshot_*.json` llevan `market.sales`
dentro. De ahí salen **nueve días de mercado**, más el de hoy: **diez**, con un agujero
del 18/08 al 09/09.

> **No hay histórico de escaparates como tal.** Hay diez días reconstruibles, y todo lo
> de abajo lleva ese `n` delante.

### El día de mercado no es el día natural

El escaparate se renueva en el reset, 05:00 UTC. Agrupando por día natural salían días
de **29 y 34** jugadores — imposible, son 20. Agrupando por día de mercado salen **20
exactos los diez días**. Esa es la comprobación de que el corte está bien puesto, y hay
guardia sobre ella.

---

## BLOQUE 1 — Cómo rota

```
10 días de mercado (12/08 a 17/09) · 200 plazas · 138 jugadores DISTINTOS
```

**De un día para otro** (solo los 6 pares de días seguidos que hay):

```
de           a            siguen  nuevos
2026-08-12   2026-08-13        6      14
2026-08-13   2026-08-14       11       9
2026-08-14   2026-08-15        9      11
2026-08-15   2026-08-16        6      14
2026-08-16   2026-08-17        9      11
2026-09-12   2026-09-13       10      10

media: 11,5 nuevos de 20 cada día (57,5 %)
```

**¿Se repiten?** `{1 vez: 84, 2: 48, 3: 4, 4: 2}`. La mayoría sale una sola vez.

### De los 101 que nos mejoran: **3 de los 20 mejores han salido alguna vez**

```
Leo Román      2 veces
Bartra         2 veces
Budimir        1 vez      <- hoy
los otros 17   ninguna
```

### Y los seis que nombraste

```
Zabiri              NO ha salido ni una vez en los diez días
Juan Iglesias       NO
Dimitrievski        NO
Roberto Fernández   NO
Espart              NO
Dmitrovic           NO
```

### Cuánto se tarda en ver a uno concreto

```
5 apariciones en 200 oportunidades jugador-día (20 vigilados × 10 días)
= 2,50 % al día por jugador
= ~40 días de espera para uno concreto
```

> **Esperar a Zabiri no es cuestión de días: son cuarenta, y quedan 33 jornadas.**
> Es el orden de magnitud sobre diez días, no un plazo. Pero la dirección no admite
> duda: **no se espera a un jugador.**

---

## BLOQUE 2 — ¿Hay patrón? **No se encuentra**

```
precio   mediana 1.100.000 en los que salieron (n=131)
         contra 1.520.000 en los que no (n=325)       p = 0,2071
puntos   mediana 7 contra 7                           p = 1,0000

por posición      salieron   no salieron
   POR              12,2 %       8,0 %
   DEF              40,5 %      32,9 %
   MED              25,2 %      28,0 %
   DEL              22,1 %      31,1 %
```

(Permutación bilateral, 10.000 barajes, semilla fija.)

**No se encuentra patrón.** Y lo digo con el matiz que hace falta: **esto no demuestra
que sea aleatorio.** Nueve días de escaparate con un agujero de tres semanas es una
prueba floja; dice que con estos datos no se ve nada. La consecuencia práctica es la
misma que si lo fuera: **hoy no se puede cazar al jugador, solo estar listo.**

También miré la hipótesis más plausible — «vuelven los que alguien acaba de soltar»—:
de 146 jugadores vendidos al Computer con algún día de escaparate posterior conocido,
reaparecieron 14. No lo publico como resultado porque la comparación no es limpia (cada
uno tiene una ventana distinta de días observados).

---

## BLOQUE 3 — ¿Estábamos listos? **No, y aquí está el número**

### 182 subastas del Computer, 38 días, 10/08 a 17/09

```
manager                          pujó en  ganó  convierte  % subastas  días
Pollo17                              109    61       56 %       60 %     34
Luismi_Haz                            89    48       54 %       49 %     32
Manzagool                             41    24       58 %       22 %     24
Pepe Bordalás                         37    26       70 %       20 %     21
DiosMande                             18    10       56 %       10 %     12
Mex                                    6     4       67 %        3 %      6
Prinzipote                             6     6      100 %        3 %      5
Alvaro Retamosa                        5     3       60 %        3 %      2
```

> **No fallamos eligiendo: fallamos apareciendo.** Cuando pujamos convertimos el
> **70 %** — el mejor de los ocho, mejor que Pollo (56 %) y que Luismi (54 %). Pero
> pujamos en **20 %** de las subastas contra el **60 %** de Pollo, y aparecemos en
> **21 de 38 días** contra sus **34**.

```
71 de 182 subastas pasaron en días en los que no pujamos NI UNA VEZ.
```

*Aviso: el tablón publica las pujas perdedoras que publica, así que «pujó en» es una
cota inferior para todos. Afecta igual a las ocho plantillas, así que la comparación se
sostiene aunque el nivel absoluto sea bajo.*

### Las oportunidades perdidas, con fecha, nombre y motivo

**Aquí el encargo pide más de lo que los datos dan, y lo digo.** Para saber si un
jugador del escaparate «nos mejoraba» hace falta su probabilidad de ser titular, y eso
solo está en la foto de hoy: los snapshots de agosto ni siquiera traen nuestro once
(`once = 0` en los seis). **La tabla día a día solo se puede hacer con n=1 día.**

**17/09, el único día medible:**

```
el peor titular de cada posición (puntos por partido × titularidad):
   POR  Dituro          0,90
   DEF  Djené           2,08
   MED  Rubén García    2,53
   DEL  Jutglà          2,08

MEJORAN EL ONCE: 2 de 20        (biddable 0, actionable 0)

  Budimir   DEL  11.990.000   6,75 contra 2,08   SUPERA_PRESUPUESTO
            intent SPECULATION · bolsillo ESPECULACION · aplicado 5.324.469
  Mayol     MED     470.000   3,50 contra 2,53   RENDIMIENTO_INSUFICIENTE
            intent SPECULATION · bolsillo ESPECULACION · aplicado 973.594
```

**Agrupados por motivo: `{SUPERA_PRESUPUESTO: 1, RENDIMIENTO_INSUFICIENTE: 1}`.**

> **Ninguno de los dos está bloqueado por falta de ficha, y ninguno recibe el bolsillo
> de fichar.** Los dos salen con `intent` de especulación, así que se miden contra
> 5.324.469 € (Budimir) y 973.594 € (Mayol) en vez de contra los 8.874.116 € que hay
> para fichar. Mayol cuesta 470.000 €.

### Una corrección mía, de las que cambian el resultado

Mi primera pasada contaba «mejoran el once» comparando **puntos por partido** y salían
**8 de 20**, y el motivo grupal parecía otro. Estaba mal: un jugador que hace 5 puntos
por partido pero juega el 30 % de los partidos aporta 1,5 por jornada, no 5. Metiendo
la titularidad dentro salen **2 de 20**, y `xi_decision` de producción —que ya lo hacía
así— tenía razón y yo no.

---

## BLOQUE 4 — La lista de vigilancia: **no la lee nadie, y es a propósito**

```
`elVestuarioLibre.vigilados`   20 ids
criterio                       los 5 mejores de cada puesto entre los que nos
                               suman y han jugado 3+ partidos, contra la vara
                               de SU posición
```

**Quien la lee:** un solo consumidor, `dashboard_state._con_los_vigilados`, y lo que
hace es marcar filas del cuadro de objetivos **después** de que el tablero haya
decidido. Su propio docstring lo dice:

> «La marca no puede haber influido en `decision`, `bid` ni en ningún listón — no por
> disciplina, sino porque llega tarde para hacerlo.»

**Ninguna decisión del motor la lee. Es decorativa por diseño**, y está escrito que lo
es: no es una pieza olvidada, es una pieza que se decidió que no autorizase nada.

Hoy marca **1 fila**. Y lo que se ve es lo que importa: **el único vigilado que apareció
en el escaparate es Budimir, y salió `SUPERA_PRESUPUESTO`.** O sea que el día que la
lista «acierta», no pasa nada.

---

## BLOQUE 5 — La regla de estar listo. Propuesta y apagada.

**La caja se mide contra lo que cuesta ganar**, no contra una cifra redonda. Sobre las
182 subastas medidas:

```
mediana    2.517.000 €
p75        4.877.000 €
p90        7.842.000 €
```

**A qué fracción de las subastas llega cada caja:**

```
disponible hoy tras exposición       973.594      40 de 182   (22 %)
bolsillo de especular              5.324.469     143 de 182   (79 %)
bolsillo de fichar                 8.874.116     166 de 182   (91 %)
más la caja realizable            23.321.116     180 de 182   (99 %)
```

### La regla

```
caja libre diaria    4.877.000 €     (llega al 75 % de las subastas)
fichas libres        1
```

**Una ficha libre**, porque con cero cada compra obliga a vender en la misma vuelta, y
vender un titular antes de tener el recambio es justo lo que el freno de titularidad
destapó ayer.

### Lo que cuesta mantenerla, y no lo escondo

```
12.090 € al día   ·   362.700 € al mes
```

Al ritmo de **+0,2479 %/día** al que se revaloriza la plantilla (`sale_order`, foto del
17/09), tener 4.877.000 € parados cuesta eso. **Es el alquiler de estar listo, y se
paga aunque no salga nadie.** Sobre 33 jornadas son unos 4 M — casi la caja entera.

> **Ese número es el argumento en contra de tu propia tesis, y por eso lo pongo aquí y
> no en una nota al pie.** Si la caja parada cuesta 362.700 € al mes y lo que
> desbloquea es pujar en más subastas, el cálculo solo sale si de verdad pujamos. Hoy
> pujamos en el 20 %.

**Se propone y no se aplica.** Nadie lee esto para decidir nada.

---

## Entonces, ¿tu tesis es verdadera?

**Sí, y reordena la semana como decías — pero el mecanismo no es el que creías.**

Lo verdadero, con n=182 subastas y 38 días: **el problema es aparecer, no elegir.**
Convertimos mejor que nadie y estamos en la mesa un tercio de las veces que el líder.
El cable, la cola por consecuencia, los millones parados y el déficit sí son caras de
lo mismo.

Lo falso: **que la puerta la cierre la caja.** Hoy, con 8,87 M y cuatro fichas, los dos
jugadores del escaparate que mejoran el once caen por el bolsillo equivocado y por el
listón del 3 %. **El freno que más veces se ve en esta medición es el `intent`, el
mismo del lunes** — y sigue mapeado y quieto, como pediste.

Con n=1 día para esa última parte. La de las 182 subastas es la sólida.

---

## Guardias

**+1 módulo, 8 guardias**, en `src/analysis/test_el_escaparate_v1.py`, dada de alta en
`scripts/run_validation_gate.py`.

**Las diez inyecciones de fallo muerden**, probadas reintroduciendo el fallo en memoria:

```
MUERDE  rotación / histórico vacío devuelve ceros
MUERDE  rotación / cuenta pares de días no seguidos
MUERDE  día de mercado / corta a medianoche
MUERDE  espera / inventa un plazo con cero apariciones
MUERDE  patrón / publica un `p` con muestra corta
MUERDE  listos / no separa los días sin puja
MUERDE  listos / lista vacía dice «participamos en cero»
MUERDE  regla / esconde lo que cuesta
MUERDE  regla / publica una regla con tres subastas
MUERDE  interruptor / encendido
```

### La que no mordía

`test_el_dia_de_mercado_corta_en_el_reset` empezó con las dos fotos a las 08:00 y las
20:00 — **las dos después del reset**. Con ese par, cortar a medianoche o cortar a las
cinco da exactamente lo mismo y la guardia pasaba con el corte mal puesto. Hace falta
una foto **antes** del reset (03:20) y otra después, que es lo que pasa cada madrugada.
Ahora la guardia comprueba primero la forma del fixture.

Dos fixtures míos más salieron mal a la primera y los arreglé contra la función, no al
revés: el percentil 75 de quince importes y el recuento de pujas del líder.

**Ninguna guardia lee `data/`, sale a la red ni mira el reloj.** `dia_de_mercado` recibe
el instante y la hora del reset por argumento.

---

## Medición

`scripts/el_escaparate.py` — 253 líneas de salida, exit 0, solo lectura de disco, sin
red.

```
python scripts/el_escaparate.py > salida.txt 2>&1
echo $?
```

---

## Si quieres histórico de verdad, así se empieza

No lo he escrito —este encargo es contar— pero lo dejo dicho porque el Bloque 0 lo pide:

Una línea por reset en `data/trading/libro_del_escaparate.jsonl` con
`{at, dia_de_mercado, players:[{id, name, position, price, points, played}]}`. Son los
datos que ya trae `market.sales` más el catálogo, o sea **cero peticiones nuevas**, y se
escribe donde ya se escribe el censo de ofertas. Con treinta días de eso, todo lo de
arriba deja de llevar asterisco.

---

## Lo que no hice, y por qué

- **Ni una escritura contra Biwenger.** Esto ha sido leer ficheros y contar.
- **No encendí nada.** `ENCENDIDO = False`, con guardia.
- **No toqué `count_free_slots` ni `historical_max`** — siguen pendientes de tu
  decisión, y `ROSTER_FILL` sigue sin tope.
- **No toqué ningún umbral ni ninguna puerta de deuda**, ni ningún `intent`, ni
  `validate_sale_set`.
- **No propuse comprar ni vender a nadie.**
- **No empecé a guardar el histórico.** Lo propongo arriba; escribirlo es otro encargo.
- **No salí a la red.**
- **No toqué `.github/workflows/bordalas-live.yml`.**
- **No empujé.**

### Lo que no se pudo medir

**La tabla día a día de oportunidades perdidas, con n>1.** Hace falta la probabilidad de
titularidad de cada jugador del escaparate en cada día pasado, y eso no está en disco:
los snapshots de agosto ni traen nuestro once. Con el libro de escaparates propuesto
arriba —y guardando el pronóstico junto al precio— esa tabla se puede hacer en treinta
días.
