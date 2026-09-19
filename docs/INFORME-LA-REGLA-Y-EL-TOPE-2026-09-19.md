# INFORME — LA REGLA DEL DÉFICIT Y EL TOPE POR VÍA

Fecha: 2026-09-19 (tarde) · Rama: `politica/la-regla-y-el-tope`, desde `arreglo/el-candado-de-la-solvencia`

Los dos interruptores nuevos, por si sólo se lee esto:

```
BORDALAS_COBRAR_EN_DEFICIT    la regla del bloque 1     APAGADO
BORDALAS_TOPE_DEL_ONCE        el tope del bloque 2      APAGADO
```

---

## BLOQUE 1 — LA REGLA DEL COBRO EN DÉFICIT

### Cómo cede cada uno de los dos frenos

Un solo sitio los hace ceder a los dos. `la_regla_del_deficit.el_cobro_que_cierra()`
elige el plan, y sus `offer_id` entran como `cobro_por_deficit` en los dos motores:

**Freno 1 — `HOLD_SOLVENCY_RESERVED`.** En
[`computer_offer_reroll_engine.py`](src/analysis/computer_offer_reroll_engine.py), la rama nueva va **detrás de
`franchise_protected` y delante de `reserved`**. Como está antes de la rama de
reserva *y* de las ramas de calidad, un solo `elif` levanta los dos frenos.

**Freno 2 — `KEEP_GOOD_OFFER`.** Para las ofertas del Computer ya queda cubierto
por lo anterior: `analyze_computer_offer` devuelve `ACCEPT_BEFORE_EXPIRY` y
`offer_decision_engine` lo convierte en `ACCEPT_FOR_SOLVENCY`. Pero las ofertas
de **managers** no pasan por el motor de reroll, así que hay una segunda rama en
[`offer_decision_engine.py`](src/analysis/offer_decision_engine.py), detrás de `NEVER_SELL`.

Medido con el caso del 19/09 (déficit 455.766, las cuatro ofertas vivas):

| oferta | sin la regla | con la regla |
|---|---|---|
| Barzic 144.800 | `KEEP_SOLVENCY_RESERVED` | `KEEP_SOLVENCY_RESERVED` |
| Oriol Rey 1.199.400 | `KEEP_SOLVENCY_RESERVED` | `KEEP_SOLVENCY_RESERVED` |
| Pablo Durán 362.700 | `KEEP_SOLVENCY_RESERVED` | `KEEP_SOLVENCY_RESERVED` |
| **Boyomo 1.845.800** | `KEEP_SOLVENCY_RESERVED` | **`ACCEPT_BEFORE_EXPIRY`** |

Una sola, la de mejor prima, y **el reloj no se movió**: `hours_to_deadline` era
480 h en las dos columnas.

Y con las cuatro sin reservar —para aislar el segundo freno— las tres que no
entran en el plan salen `KEEP_GOOD_OFFER` / `KEEP_OFFER` y Boyomo se acepta
igual.

### Qué pasó con las dos cabezas

**Elijo que mande el planificador, y sobra el criterio del motor de ofertas para
este caso.** El motivo no es estético:

`A_NO_XI` / `B1` / `C` **no existen en el código** —lo comprobé por nombre—, así
que no había dos implementaciones que reconciliar: había una cabeza que calculaba
y otra que decidía sin preguntarle. La regla que decidiste *es* `A_NO_XI` con un
criterio de orden, así que el planificador puede ser la única fuente: devuelve
una lista de `offer_id` y los motores la obedecen.

Lo que **no** he hecho es quitarle al motor de ofertas sus criterios propios.
Siguen mandando cuando no hay déficit, y `NEVER_SELL` y `franchise_protected`
siguen por delante de la regla. Esos dos no los toqué porque el plan ya excluye a
los del once y en la práctica no se cruzan — pero si algún día un Franchise no
fuera titular, gana Franchise. Queda dicho.

### El estado del que no se salía

Se cae solo, como preveías: el déficit entra como **entrada** y no depende de
ningún reloj. La guardia lo comprueba en sus dos mitades —sin la regla el candado
sigue cerrado, con la regla se abre— para que el día que se apague se vea qué se
recupera.

### El caso real de mañana, y no son buenas noticias

Probé la regla contra el escenario que me diste:

```
saldo tras cobrar a Boyomo              +1.390.034
si entran Chust y Dmitrovic             −5.262.998   (déficit 5.262.998)

ofertas vivas de fuera del once:
   Oriol Rey    1.199.400
   Pablo Durán    362.700
   Barzic         144.800
   suman        1.706.900
```

**La regla acepta las tres y NO cierra el déficit.** Deja el saldo en
**−3.556.098**. Faltan 3.556.098 y no hay de dónde sacarlos sin tocar el once.

La regla es necesaria y no es suficiente mañana. Lo que haría falta además: la
tanda nueva del Computer del reset de las 07:00, o una venta. La frase del plan
ahora lo dice con esas palabras y con la cifra que falta, en vez de anunciar
1.706.900 recuperados y dejar creer que se sale del rojo.

### Cómo se llama el interruptor

`BORDALAS_COBRAR_EN_DEFICIT`. Apagado, los dos frenos siguen mandando y el
comportamiento es exactamente el de hoy.

---

## LAS TRES GUARDIAS QUE ESTABAN EN ROJO

| guardia | antes | ahora |
|---|---|---|
| `test_la_reserva_no_bloquea_el_deficit_que_cubre` | 1 roja | **verde** |
| `test_el_panel_no_afirma_lo_que_el_json_desmiente` | 4 rojas | **verde** |
| `test_un_candidato_pujable_llega_a_la_cola` | 1 roja | **sigue roja** |

**Por qué la tercera sigue roja.** No la arregla la regla del déficit, y creo que
es correcto que no la arregle.

La regla cierra el déficit, y al cerrarlo `acquisition_budget` deja de salir
`SIN_CAPACIDAD` y el candidato de puja vuelve a generarse. Pero eso es una
**secuencia** —aceptar, cobrar, vuelta siguiente—, y lo que la guardia comprueba
es otra cosa: que **dentro de una vuelta con el déficit vivo** haya un candidato
de puja, aunque salga bloqueado y con su motivo.

Hoy no lo hay. Todo el bloque cuelga de `acquisition_budget.enabled` y dentro hay
dos salidas —`SPECULATION_BUY` y `SPECULATION_WATCH`— que no se ejecutan ninguna.
Arreglarlo es mover esa puerta para que el bloqueo se anote en vez de saltarse,
y eso cambia la forma de la lista de candidatos. No lo pedías y no lo he hecho.

---

## BLOQUE 2 — EL TOPE POR VÍA

### De qué cuelga el tope, y si esa etiqueta es fiable

**Cuelga del `intent`. El `route` no decide nada.** En `optimal_bid`:

```python
tope_aplicable = (
    prima_maxima
    if str(intent or "").upper() == SPECULATION_INTENT
    else None
)
```

El `route` sí entra en la función, pero su propio docstring lo dice: «*Solo para
el motivo: no entra en ninguna cuenta ni abre ni cierra ninguna puerta*». Y
`market_gate.route_now` vive en el bloque marcado «*EL ESQUEMA NUEVO, AL LADO Y
SIN MANDAR*».

Comprobado en la guardia: el mismo `intent` con cinco `route` distintos
—`XI_UPGRADE`, `ROSTER_FILL`, `PRICE_TREND`, `COMPUTER_RESALE`, `None`— da la
**misma puja**.

**Así que el miedo del encargo no se cumple.** Que el `market_gate` reetiquetara a
Chust como `ROSTER_FILL` es cosmético para el tope.

Lo que sí es frágil, y lo digo porque está al lado: el `intent` **sí** depende del
precio, a través de `classify_operation` —si ninguna vía de fichaje llega al
precio, la operación deja de ser fichaje (es el caso Amatucci, documentado ahí
mismo)—. Es un hook más honesto que el `route`, porque codifica *para qué* lo
compramos, pero no es inmune.

**Cuántos de los 52 cambian de vía: no lo he podido contar.** Esa lista vive en la
foto de las 12:32, que no existe. La del 18/09 que sí tengo trae
`speculation.candidates: 0` porque estaba bloqueada. A partir de mañana se podrá
contar, que es justo para lo que sirve el bloque 5c.

### La dirección del arreglo era la contraria

Lo pedías como una subida de 0,25 % a 1,2525 %. **La vía del once no tenía tope
ninguno**: `tope_aplicable` salía `None` para todo lo que no fuera `SPECULATION`.

Con el valor real de Chust (2.278.096), lo que ofrecía Pepe era **1.942.501, un
+5,00 %** — cuatro veces lo que pagaste tú a mano. Y no es un techo: con más valor
sube a +20 % y +100 %. Es donde cae el óptimo de EV.

**Así que esto baja el techo del once. No lo sube.**

### La tabla de las tres pujas

| jugador | precio | pujó el dueño | % | Pepe tope viejo | Pepe tope nuevo | ¿cabe? |
|---|---:|---:|---:|---:|---:|:---:|
| Chust | 1.850.000 | 1.871.032 | +1,14 % | 1.942.501 (+5,00 %) | 1.850.001 | **SÍ** (techo 1.873.172) |
| Dmitrovic | 4.740.000 | 4.782.000 | +0,89 % | 4.977.001 (+5,00 %) | 4.740.001 | **SÍ** (techo 4.799.369) |
| Cabrera | 2.920.000 | 3.116.031 | +6,71 % | 3.066.001 (+5,00 %) | 2.920.001 | **NO** (techo 2.956.573) |

Ahí está el «no» que querías ver escrito: **Cabrera no cabe ni con el tope nuevo.**
Pagaste veintisiete veces el tope viejo y 5,4 veces el nuevo.

### Y lo que de verdad impide llegar a +1,14 %

Mira la columna «Pepe tope nuevo»: **+0,00 % en los tres**. El tope subió y la puja
no.

No es el tope. Es la **curva de primas**:

```
prima   +0,00 %   P(ganar) = 0,41
prima   +2,00 %   P(ganar) = 0,21
prima   +5,00 %   P(ganar) = 0,16
```

Entre +0,00 % y +1,25 % **no hay ningún peldaño**. Con el modelo real, `P(ganar)`
vale 0,243 en los dos extremos, así que `EV = P × (valor − puja)` siempre premia la
puja mínima. Cualquier tope por debajo del +2 % colapsa a «puja lo mínimo».

Y la curva es la de por defecto:

```
calibrada : False
muestras  : 0          ("Solo 0 pujas medibles; hacen falta 12")
subastas observadas : 161
```

**161 subastas vistas, 0 usadas para calibrar.** El modelo que decide cuánto pujar
nunca se ha ajustado contra lo que de verdad pasa en esta liga. Ése es el arreglo
que haría que Pepe llegara a +1,14 %, no el tope. Lo dejo dicho y no lo toco.

La vía de reventa sigue en **0,25 % exacto** y tiene guardia propia que además
clava el suelo de cobro (+1 %) y el tope del carril.

---

## BLOQUE 3 — EL TABLÓN

### Por qué se reescribe en local → **no se reescribe: está viejo**

```
git    649 eventos, hasta el 19/09 05:05
local  627 eventos, hasta el 18/09 11:11
```

La local es un **subconjunto estricto**: 22 eventos en git que no están en local y
**cero** al revés. El último ciclo local corrió el 18/09 11:11 —lo confirma
`board_latest_raw.json`, que tiene esa misma marca— y desde entonces sólo ha
escrito CI.

Los 5.473 insertados / 4.211 borrados que viste son el diff de un fichero viejo
contra uno nuevo. El fichero va ordenado y con `indent=2`, así que **parece una
reescritura y es una amputación**.

Lo que se habría borrado al guardarlo encima:

| evento | tipo | cuándo |
|---|---|---|
| `f45d62117756d6a7e87b9bfd` | transfer | 18/09 06:53 — **una de las dos reemisiones de Lunin** |
| `3d15660bd0c3d1e7813beaab` | market | 19/09 05:05 — la resolución de Maffeo |
| + 3 transfer, 1 roundStarted, 14 bettingPool | | |

Es decir: se habría borrado **la prueba del descuadre de 420.200** que sostiene
todo el bloque 5 de ayer.

**El freno.** `historia_que_se_perderia()` compara lo guardado con lo que se va a
escribir y `save_board_history()` lanza `ElTablonPerderiaHistoria` y **no
escribe**. Pediste una guardia que lo impida, no un aviso. La poda legítima sigue
pasando: lo anterior al `leagueReset` vigente no cuenta como pérdida, y por eso
`reset_ts` entra en la función.

### Por qué en CI no se guarda desde las 07:37 → **porque no cambia**

`guardar_los_libros` sólo commitea lo que cambió. El evento más nuevo del tablón
es del **19/09 05:05** (el mercado resuelve una vez al día, sobre las 05:00), y
entre las 07:37 y las 12:32 no hubo ninguno nuevo. CI corrió a 11:48 y 12:32 y
commiteó otros libros, no éste.

Es la opción buena de las dos que planteabas: **la caja de los rivales no se está
calculando sobre un tablón viejo.** El tablón está al día; simplemente no pasó
nada.

Lo que no puedo descartar sin salir a la red —y no salgo— es que hubiera un evento
entre medias que no se capturó. Lo digo porque el 18/09 sí hubo seis commits del
tablón repartidos por el día, así que un 19/09 tan quieto es raro aunque posible.

### ¿Acumula o rederiva? → **acumula**

`merge_board_events` es un diccionario por `event_id`, unión de lo guardado y lo
fresco. No rederiva nada.

**Luego los duplicados de Lunin son de Biwenger reemitiendo, no nuestros: la reja
arregla, no tapa.** La guardia lo fija comprobando que las dos emisiones
sobreviven a la mezcla como dos `event_id` distintos.

Un detalle menor que queda dicho: la mezcla descarta cualquier evento guardado que
**no** traiga `event_id`, porque la clave del diccionario los filtra. Hoy no hay
ninguno así.

---

## BLOQUE 4 — EL LIBRO DE PUJAS

### El arreglo

La clave era `player_id:placed_at`. Ahora al anotar manda el par **(jugador,
importe) mientras siga PENDIENTE**, y al colapsar lo ya escrito manda el
`event_id`.

No se puede usar `event_id` a secas porque al anotar la puja **es `None`**: no se
sabe hasta que el tablón la resuelve. El par (jugador, importe) es lo que el
propio libro ya usaba en `ya_estan` para no recoger dos veces la misma del tablón.

La fecha no se pierde: quien reusa la clave conserva el `placed_at` de la primera
vuelta, que es de donde sale cuánto tiempo estuvo viva.

### Lo que apareció al medirlo, y es peor que el conteo

**El libro no mentía.** Registraba nueve pujas por Maffeo porque **hubo nueve**.
`libro_del_carril.jsonl` las tiene con `sent: true`, `http 200` y **un id de
Biwenger distinto cada vez**:

```
18/09 05:23  bid id 3127508531
18/09 07:14  bid id  876658931
18/09 08:14  bid id  874501044
...  (nueve en total, cada una ~3.600 s después)
```

| | escrituras contra Biwenger | operaciones distintas |
|---|---:|---:|
| Maffeo | 9 | 1 |
| Boyomo | 5 | 1 |
| Trent | 1 | 1 |
| Drkusic | 1 | 1 |
| **total** | **16** | **4** |

**12 escrituras de más, el 75 %.** El carril re-puja cada vuelta algo que ya tiene
vivo. No hay ninguna guardia de puja viva en `la_rendija.py` ni en
`carril_executor.py` — y `players_with_live_bid()` **ya existe** en
`decision_orchestrator.py:464`, sin que nadie la llame desde ahí.

Y cuesta: `ESCRITURAS_POR_VUELTA = 2` y el cupo del reset es 1 en el régimen de
prueba. Esas doce escrituras compiten con abrir viajes nuevos.

**No lo he arreglado**: es el camino de escritura contra Biwenger y no lo pedías.
Es el siguiente encargo, y creo que es más urgente que casi todo lo de hoy.

### Las estadísticas, con el `n` limpio

| | lo que veníamos diciendo | con el `n` limpio |
|---|---|---|
| pujas puestas / ganadas | 47 / 41 (87,2 %) | **23 / 19 (82,6 %)** · n=23 |
| subastas en las que aparecimos | 37 de 182 | **47 de 225** · n=225 |
| nuestra conversión en subastas | 70 % | **76,6 %** · n=47 |

Las dos últimas las he medido sobre el **tablón**, no sobre el libro: es la fuente
honesta y no depende del duplicado.

### ¿Seguimos siendo los mejores convirtiendo?

**Sí.** Y lo digo con esas palabras porque preguntabas por si acaso.

| manager | aparece | gana | conversión |
|---|---:|---:|---:|
| Pollo17 | 134 | 71 | 53,0 % |
| Luismi_Haz | 108 | 56 | 51,9 % |
| Manzagool | 50 | 31 | 62,0 % |
| **Pepe Bordalás** | **47** | **36** | **76,6 %** |
| DiosMande… | 30 | 17 | 56,7 % |
| Mex | 8 | 5 | 62,5 % |
| Prinzipote | 6 | 6 | 100,0 % |
| Álvaro Retamosa | 6 | 3 | 50,0 % |

Prinzipote sale al 100 % con **n=6**: eso es una anécdota, no un rendimiento
(doctrina 55). De los cuatro con `n ≥ 30` somos los mejores, y por 14,6 puntos.

Y sólo en las **disputadas** —donde hubo pelea de verdad— también:

| manager | aparece | gana | conversión |
|---|---:|---:|---:|
| **Pepe Bordalás** | **25** | **14** | **56,0 %** |
| Manzagool | 39 | 20 | 51,3 % |
| DiosMande… | 25 | 12 | 48,0 % |
| Pollo17 | 104 | 41 | 39,4 % |
| Luismi_Haz | 83 | 31 | 37,3 % |

**La tesis no sólo aguanta: sale más fuerte.** Pollo aparece en 134 subastas y
nosotros en 47 — **2,85 veces más**. No fallamos eligiendo; fallamos apareciendo,
y el número que lo dice es mejor de lo que creíamos, no peor.

---

## BLOQUE 5 — LAS TRES DE UNA LÍNEA

### (a) `relojes.js:78`

Publicaba sólo los tres `puntuales`. Ahora publica también el latido, como una
entrada **sin hora concreta** —`":07 cada hora"`— porque son veinte al día: poner
«00:07» sería cambiar una lista incompleta por una lista falsa.

Un matiz: la **detección** ya incluía el latido (`disparos()` en ese mismo fichero
y `que_disparo_toca` en Python). Sólo mentía quien lo **enseñaba**.

**La segunda mitad no se puede hacer como la pides.** `config/disparos.json` dice
`"como_entra": "workflow_dispatch"`, y desde que se retiró el `schedule` **todas**
las vueltas entran así: las de cron-job.org y las tuyas. No existe ninguna señal
que las separe. Las dos opciones reales, las dos tuyas:

1. **Subir `gracia_minutos`** de 12 a ~25. Es un umbral y no estaba entre los dos
   que decidiste, así que no lo he tocado. Cubriría el caso de las 11:48 (19 min)
   a costa de tapar retrasos reales de hasta 25 min.
2. **Meter un `input` en el workflow** (`inputs.manual: true`) y que la alarma lo
   lea. Es tu fichero. Es la opción limpia.

### (b) La reja

Mergeada: `git merge arreglo/la-reja-y-el-suelo`, sin conflictos, siete commits.
Las cinco guardias que traía pasan en verde.

Los tres pasos, y el tercero es tuyo:

```
1. git merge arreglo/la-reja-y-el-suelo      <- hecho
2. git push                                  <- tuyo (yo no empujo)
3. en bordalas-live.yml, en el env del job:
       BORDALAS_REJA_CON_TOLERANCIA: "1"     <- tuyo
```

### (c) La foto diaria

`scripts/guardar_la_foto.py`, paso aparte del ciclo. Escribe
`data/fotos/YYYY-MM-DD.json` y `.gitignore` la deja pasar.

**Cuánto ocupa, medido sobre la foto del 18/09:**

| | tamaño | como blob de git | al año |
|---|---:|---:|---:|
| entera, con indent | 1.541,5 KB | — | — |
| entera, compacta | 1.054,3 KB | ~113,3 KB | **40,4 MB** |
| recorte de 10 campos | 23,6 KB | ~5,1 KB | 1,8 MB |

**Elijo la entera, y el motivo es concreto.** El recorte es 22 veces más barato y
aun así no compensa: la lista que proponías —`summary`, `race`, `solvency`,
`solvency_clock`, `subasta`, `listings`, `offers`, `acquisition`, `marcador`,
`bid_outcomes`— **no incluye `pujas_del_dueno`**, que es exactamente el bloque que
resolvió el caso de Maffeo esta mañana. Tampoco `consistency`, ni `silencio`, ni
`loNuestroALaVenta`, que también hicieron falta hoy.

Un recorte guarda lo que hoy creemos que vamos a necesitar. 40 MB al año es barato
al lado de descubrir dentro de un mes que el campo que hace falta no está.

**Compacta y sin comprimir** porque git ya comprime: un `.gz` no se deltifica entre
días ni se lee con `git log -p`. El `indent` son 487 KB de espacios por foto.

La fecha sale de `meta.generated_at`, **no del reloj del sistema**, y sin ella no
se guarda: una foto archivada bajo el día equivocado es peor que no tenerla.

Para el workflow, si lo quieres automático (tuyo):

```yaml
- name: Guardar la foto del dia
  if: always()
  run: python scripts/guardar_la_foto.py
```

Va **antes** de «Guardar los libros» y no necesita nada más: una al día, el resto
de vueltas no hacen nada.

---

## BLOQUE 6 — EL VIAJE DE TRENT

El único viaje completo que tenemos, de punta a punta:

| | |
|---|---|
| comprado | **13/09 05:06**, por **2.760.000** |
| precio de mercado aquel día | 2.730.000 → prima **+1,10 %** |
| vendido | **17/09 22:12**, por **2.536.500** |
| a quién | **al Computer** (el `transfer` sólo lleva `from`, no `to`) |
| precio de mercado aquel día | 2.530.000 → prima **+0,26 %** |

```
neto        −223.500 EUR
neto %         −8,10 %
días             4,71
por día      −47.429 EUR/día   (−1,718 %/día)
```

**De dónde salió la pérdida.** El mercado se movió **−7,33 %** en esos 4,71 días:

| | euros | del total |
|---|---:|---:|
| el precio de Trent cayendo | −200.000 | 89,5 % |
| nuestras primas (entrada +1,10 %, salida +0,26 %) | −23.500 | 10,5 % |

Compramos 30.000 por encima del mercado y vendimos 6.500 por encima. Las primas
nos costaron 23.500; el resto lo puso el mercado. **No fue una mala ejecución: fue
un mal momento.** Aunque hubiéramos comprado y vendido clavados al mercado, la
operación pierde 200.000.

Con `n=1` esto no dice si los viajes funcionan (`VIAJES_PARA_JUZGAR = 10`). Dice
qué pasó en éste.

Y `viajes_sin_listar` arreglado: cruzaba contra LISTADOS y nunca contra la
plantilla. Por eso llevaba tres fotos diciendo que Trent estaba comprado sin
publicar cuando se había vendido dos días antes.

**Y la otra frase también estaba mal**, la que ayer di por buena: «la puja no se ha
resuelto a nuestro favor». **Sí** se resolvió. Lo compramos y lo vendimos. Acertaba
la conclusión con el motivo equivocado — doctrina 87 otra vez, la cuarta este mes.

---

## LO QUE NO HICE, Y POR QUÉ

- **Ni una escritura contra Biwenger.** El bloque 1 se entrega apagado.
- **No subí ningún umbral** salvo los dos decididos, con su alcance exacto:
  `BORDALAS_TOPE_DEL_ONCE` sólo para `intent` de fichaje (`XI_UPGRADE`,
  `ROSTER_FILL`). Intactos y con guardia: `PRIMA_MAXIMA_DE_PUJA` (0,25 %), el
  `TOPE_DE_COMPRA` del carril, el suelo de cobro (+1 %). Intactos sin tocar:
  `MAX_SINGLE_SPECULATION_PERCENT`, `MAX_SAFE_DEBT`, el cupo,
  `MIN_WIN_PROBABILITY`, `MAX_PROJECTED_DAILY_RATE`, las cinco de
  `PUEDEN_ENCERRARLO`.
- **No apliqué `stash@{0}`.** Sigue ahí, y sigue midiendo 627 contra 649. El
  freno del bloque 3 ahora lo impediría aunque alguien lo intentara.
- **No toqué `bordalas-live.yml`.** Los dos cambios que necesita —la variable de
  la reja y el paso de la foto— están escritos arriba, no hechos.
- **No arreglé el re-pujado del carril.** 12 escrituras de más de 16 es el
  hallazgo más caro del día y toca el camino de escritura. No lo pedías.
- **No conté cuántos de los 52 cambian de vía**: esa foto no existe. Desde mañana
  se podrá.
- **No calibré la curva de primas.** Es lo que de verdad impide pujar a +1,14 %,
  pero es un cambio de modelo y no estaba en el encargo.
- **No empujé nada.**

### Una guardia que ya fallaba y no es mía

`test_accept_before_expiry_orchestrator_v1` está en rojo. Lo comprobé poniendo los
dos motores en su versión anterior: **ya fallaba**. Lee estado de producción y hoy
no hay ofertas sobre la mesa. Queda dicho para que no se le achaque a esto.

### Y una cosa tuya que sigue en pie

De los cuatro fallos que me apuntaste arriba, tres eran de lectura y uno de
premisa. El que más me ayudó fue el cuarto: que Trent tuviera **las dos** frases
mal, y no una, es lo que me hizo mirar el tablón en vez de creerme la que sonaba
bien. Sin eso no habría encontrado la venta del 17/09, y el viaje del bloque 6 no
existiría.
