# El plazo de verdad, y el que va a despegar

**Encargo:** `Claude outputs/ENCARGO-EL-QUE-VA-A-DESPEGAR-2026-09-23.md`
**Rama:** `arreglo/el-que-va-a-despegar`, desde `main` en `8c1cd3a`
**Fecha:** 23/09/2026, mañana

| commit | bloque | verja |
|---|---|---|
| `b326dc2` | 0 — el plazo sale del calendario | 178/178 |
| `f12b3f2` | 1 — el que va a despegar | 179/179 |
| `6c54c40` | 2 — la sombra de la puja | 180/180 |
| `c180f3d` | 3 — el libro de aciertos y la foto por jornada | 181/181 |

Todas corridas a fichero, con el árbol quieto y con `BORDALAS_JORNADAS_POR_SU_FECHA=1` y
`BORDALAS_REVENTA_SOLO_SI_JUEGA=1` puestos, código 0.

> **Aviso sobre la rama.** `encender/a-quien-y-cuanto` (la de ayer) **no está fusionada en
> `main`**, y esta rama sale de `main` como pide el encargo. Así que aquí **no** están ni la
> verja que se lee el workflow ni la guardia del ciclo sobre copias. Consecuencias: los
> interruptores los he puesto a mano, y cada verja ha ensuciado los mismos cuatro libros
> versionados (`libro_de_publicacion`, `marcador`, `board_events`, `bitacora_del_saldo`). Los he
> devuelto a git después de cada corrida: **no va ni un byte de esos libros en ningún commit.**
> Las dos ramas tocan `dashboard_state.py` y la lista de la verja: al fusionar la segunda habrá
> conflicto de texto en esos dos ficheros, no de lógica.

---

## Bloque 0 — el plazo sale del calendario

### La medición contradice el encargo, y gana la medición

**No había un semanal inventado.** El reloj **ya** leía el plazo del calendario. En la foto de
las 09:25 publicaba `hours_to_solvency_deadline: 390.04`, es decir, el 09/10. Lo que había eran
dos cosas distintas:

1. una **frase escrita a mano**: «el viernes hay que estar en positivo»;
2. una **regla sin fecha**: la subasta cerraba con cualquier déficit, estuviera el plazo a 6
   horas o a 16 días (`la_subasta.py`, `if estado not in SOLVENCIA_QUE_DEJA_PUJAR or deficit > 0`).
   De hecho, `CUBIERTO` estaba en la lista de estados que dejan pujar y **nunca** dejaba, porque
   `CUBIERTO` solo sale con déficit.

### El T que se aplica hoy, con la línea

```
plazo = primer partido − 15 min − 6 h  =  T − 6 h 15 min
```

- los 15 min: `REAL_DEADLINE_MINUTES = 15` — [matchday_calendar_engine.py:47](src/analysis/matchday_calendar_engine.py#L47). `calendar_state` le pasa al reloj las horas hasta `real_deadline`;
- las 6 h: `ACCEPT_BEFORE_DEADLINE_HOURS = 6.0` — [computer_offer_reroll_engine.py:43](src/analysis/computer_offer_reroll_engine.py#L43), que `solvency_clock` importa como `SOLVENCY_DEADLINE_HOURS`;
- la resta: `horas_plazo = horas_cierre - SOLVENCY_DEADLINE_HOURS` en `build_solvency_clock`.

**Hoy: 09/10 a las 14:45** (J8, primer partido 09/10 21:00). El margen no se ha tocado.

### Lo que cambia

- El reloj publica `solvency_deadline`: la fecha sale del `real_deadline` del calendario, el mismo
  dato del que salen las horas. Los dos sitios que construyen el reloj le pasan ya ese dato.
- El motivo del freno dice esa fecha. Hoy diría:

  > El reloj de solvencia dice «CUBIERTO» con 1.525.782 EUR de deficit. No se puja: el plazo, del
  > calendario, es el 09/10 a las 14:45 -6 h antes del cierre de la jornada, 09/10 20:45-: quedan
  > 390 h (16,3 dias). Hay tiempo, pero la regla de hoy cierra con cualquier deficit;
  > BORDALAS_SOLVENCIA_POR_SU_PLAZO la haria esperar al plazo.

- **Si el calendario no trae la fecha: frena, y lo dice.** «No lo se: el calendario no trae la
  fecha del primer partido de la jornada… Con deficit y sin plazo conocido no se puja a ciegas.»
  He elegido frenar porque un plazo que no se conoce puede ser mañana: dejar de pujar un día es
  barato, y pujar en rojo contra un plazo desconocido no lo es.
- **Interruptor nuevo, apagado: `BORDALAS_SOLVENCIA_POR_SU_PLAZO`.** Con él puesto, el déficit
  solo cierra la subasta a menos de un ciclo del Computer del plazo (`COMPUTER_CYCLE_HOURS = 24`,
  que ya estaba medido: es el mismo borde en el que el reloj pasa de PUBLICAR a CRITICO). Apagado,
  el comportamiento es exactamente el de ayer.

> **Un número que encaja no es una causa (95).** Aunque se encendiera, **hoy la subasta tampoco
> pujaría**: con el saldo en −1.525.782 EUR, `cash_budget` es 0, y el tope de la ventana
> (caja libre / 5 %) sale 0. Quien frena de verdad por dinero es el tope, no el reloj.

### Cuántas vueltas frenaron con un plazo que no era el del calendario

**Ninguna usó un plazo, ni del calendario ni inventado: la regla no miraba ninguna fecha.** Sobre
`bitacora_del_saldo.jsonl`, del 16/09 07:31 al 23/09 06:51 (**n = 287 vueltas**):

| | vueltas | plazo del calendario en ese momento |
|---|---|---|
| con déficit en el reloj del ciclo (saldo < 0) | **121** | todas **fuera** del T−6: 0 de 121 dentro |
| con déficit en el reloj del panel (saldo − pujas vivas) | **159** | 0 de 159 dentro |
| **dentro de la ventana de 135 min**, con déficit, en el ciclo | **0** | — |
| dentro de la ventana, con déficit, en el panel | 5 | a 390–490 h del plazo |

Lo importante es la fila del medio: **en las ventanas del reset de estos 7 días el ciclo no
frenó ninguna vez por solvencia**. En las 9 vueltas de ventana con saldo conocido el saldo era
positivo; de las otras 6 la bitácora no tiene fila a menos de 5 minutos: **no lo sabemos**. Fuera
de la ventana, las 121 decían SOLVENCIA pero no frenaban nada: la ventana estaba cerrada de todas
formas, y el reloj va antes que la ventana en el orden de las puertas.

Las 5 del panel son la deuda contingente de nuestras propias pujas de esa misma noche (el panel
resta las pujas vivas; el ciclo no).

### La guardia

`test_el_plazo_sale_del_calendario_v1`, cinco casos. Con J8 a 16 días, el motivo no puede decir
«viernes», «esta semana» ni «semanal», y tiene que nombrar el 09/10. **Muerde:** con la frase de
antes se pone roja; con un caso sin calendario, roja («el caso no tiene calendario: esta prueba
no prueba nada»).

---

## Bloque 1 — el que va a despegar

### La marca

`nos_suma` no se toca. Encima de cada fila de `todaLaLiga` van ahora la **tasa por partido**, la
**de su vara** y `pasado_corto`, con los partidos jugados contra los posibles y el motivo. Las
cuatro clases salen de datos que ya trae el catálogo:

| clase | de dónde sale |
|---|---|
| 1 vuelve de lesión | `fitness` (últimos ≤5 partidos, el más reciente primero) marca `injured` |
| 2 recién fichado | `fitness` es más corto que los partidos de su equipo: llegó tarde |
| 3 sin histórico en Primera | `pointsLastSeason` por debajo del corte de `ascendidos` (20) |
| 4 suplente con prensa | una noticia del informe de prensa con dirección `UP` |

Partidos posibles = el máximo de partidos jugados entre los de su club. Es una cota inferior, y
así lo dice el módulo.

Los dos frenos usan números que ya existían: `PARTIDOS_PARA_JUZGAR = 3`, y el veto de lesionado
o sancionado de `_etiqueta`. Con ellos, Sergio Martínez (18 en 2) no sale marcado.

Si está marcado, sin frenos, y bate a su vara por partido: etiqueta **«va a despegar»**, entre
«nos mejora» y «chollo», y la frase «POR ESTE HAY QUE PUJAR», con su dato.

### Ceballos sale en la lista del día

Con el catálogo público de hoy (bajado con un GET sin login, al scratchpad) y la foto de las
09:25: **20 en el mercado, 10 que se pueden fichar, 3 marcados**. Ceballos sale **tercero**:

```
 1. Ximo Navarro      1.580.000  nos mejora     2,67 vs 2,25   nos_suma   7   Pepe: 0 (NO_COMPENSA)
 2. Mangala           2.120.000  nos mejora     3,29 vs 3,14   nos_suma   1   Pepe: 0 (NO_COMPENSA)
 3. Ceballos          4.180.000  va a despegar  4,33 vs 3,14   nos_suma  -9   Pepe: 0 (RENDIMIENTO_INSUFICIENTE)
 4. Belocian          1.480.000  va a despegar  2,33 vs 2,25   nos_suma  -2   Pepe: 0 (NO_COMPENSA)
 5. Oriol Rey         1.190.000  chollo         3,67 vs 3,14   nos_suma   0   Pepe: 0 (NO_COMPENSA)
 6. Turrientes        1.300.000  chollo         3,50 vs 3,14   nos_suma  -8   Pepe: 0 (SIN_VALOR)
 7. David Otorbi        840.000  chollo         3,50 vs 4,14   nos_suma  -8   Pepe: 0 (RENDIMIENTO_INSUFICIENTE)
 8. Thiago Fernández  1.190.000  chollo         3,50 vs 4,14   nos_suma -15   Pepe: 0 (NO_COMPENSA)
 9. Sannadi             150.000  sin interés    2,00 vs 4,14   nos_suma -23   Pepe: 0 (SIN_VALOR)
10. Zakharyan           150.000  sin interés    1,33 vs 3,14   nos_suma -18   Pepe: 0 (SIN_VALOR)
```

> POR ESTE HAY QUE PUJAR: 4.33 por partido contra 3.14 de su vara, en 3 de 7 partidos posibles.
> Su pasado se queda corto: vuelve de lesion: lesionado en 1 de sus ultimos 4 partidos, la ultima
> vez hace 3 partido(s); llego tarde a su equipo: esta en sus ultimos 4 partidos, y el equipo ha
> jugado 7.

**Lo que pujaría Pepe por cada uno es 0**, copiado del tablero: la marca no entra en la
valoración (el encargo lo prohíbe hasta que exista el libro del bloque 3). En Ceballos el motivo es
«por reventa rinde un 0,20 % y se exige un 3 %».

Está en el panel como `elVestuarioLibre.lista_del_dia`, que es lo que une la lista del ojeador con
el mercado del día (antes: `en_el_mercado_hoy: 0` con veinte en el mercado).

### Qué hicieron los 73 a 7 días: el motor tenía razón

La foto de hoy no tiene 7 días por delante, así que se clasifica sobre el último catálogo con una
semana cerrada detrás, el **13/09 17:17**, con el mismo `toda_la_liga` de hoy.
`python scripts/el_que_va_a_despegar.py`:

| grupo | n | precio a +7 d (mediana) | subieron | puntuaron a +6 d |
|---|---|---|---|---|
| **baten a su vara por partido, nos_suma ≤ 0** | **72** | **−8,21 %** | 15 de 72 | 44 de 70 (mediana 3) |
| de ellos, con la marca | 8 | −12,53 % | 1 de 8 | 4 de 8 (mediana 1,5) |
| control: nos_suma ≤ 0 y no la baten | 129 | −6,68 % | 22 de 129 | 72 de 125 (mediana 2) |
| referencia: nos mejoran | 215 | −0,91 % | 99 de 215 | 158 de 214 (mediana 4) |

Repetido sobre el **19/09 18:18** (precio a +3,5 días, que es lo que hay): el grupo −3,27 %
contra −3,64 % del control; puntuaron el 41 % (24 de 58) contra el 46 % (81 de 176).

**No lo hicieron mejor que el control, ni en precio ni en puntos, en ninguna de las dos bases.**
Los que `nos_suma` ya daba por buenos sí van mejor en las dos cosas. En esta muestra, que es de
una semana de mercado, **el motor tenía razón**. La marca se queda como **señal para mirar** y no
entra en ninguna decisión, y así está escrito en la cabecera del módulo.

Sobre «los 73»: con la foto de las 09:25 me salen **81** (22 de ellos en plantillas de rivales,
como Ez Abde). Con el catálogo del 13/09, **72**. No he podido reproducir el 73 exacto.

### La guardia

`test_el_que_va_a_despegar_v1`, seis casos. Un jugador con 3 partidos y buena tasa sale «va a
despegar» y no «sin interés», con `nos_suma` intacto. **Muerde:** sin la señal en `_etiqueta` se
pone roja; con un caso en el que todos jugaron todos los partidos, roja.

---

## Bloque 2 — la sombra de la puja

En cada vuelta, **en el panel** (`subasta.sombra`) y en una pantalla:

```
python scripts/la_sombra_de_la_puja.py
```

jugador · precio · lo que pujaría · la prima · por qué · qué candado le queda. De mayor a menor.

Es **la misma `plan_del_reset` que puja**, con las puertas de momento abiertas (interruptor,
solvencia, bloqueo, ventana) y `en_vivo=False`. Si aun así sale vacía por **dinero** (el tope de la
ventana) o por **fichas**, se levanta también y se apunta como candado. El interruptor se lee y
no se apaga: `plan_del_reset` tiene un parámetro nuevo, `mirar_el_interruptor`, que solo la sombra
pone a `False`.

**Hoy**, con la foto de las 09:25 y los dos interruptores del workflow:

```
Pujaria por 1 jugador(es), 1.583.951 EUR en total.
Candados: SOLVENCIA, FUERA_DE_VENTANA, TOPE_DE_LA_VENTANA

  Ximo Navarro   precio 1.580.000   PUJARIA 1.583.951   prima 3.951 (0,25 %)
```

Uno solo porque queda **1 ficha libre**. **Ceballos no sale**: la regla de «¿va a jugar?»
(`BORDALAS_REVENTA_SOLO_SI_JUEGA`, encendida) lo frena con un 30 % de titular según FutbolFantasy.
Sin esa regla, el nombre sería Ceballos, a 4.190.451.

**Guardia** `test_la_sombra_de_la_puja_v1`: con el interruptor puesto, la solvencia en rojo, la
ventana cerrada y la caja a 0, la lista sale con sus candados y los **siete** métodos que escriben
de `BiwengerWriteClient` revientan si alguien los llama: cero llamadas. **Muerde** si la sombra
toca `os.environ`, si ordena al revés y si el caso no tiene candidatos.

---

## Bloque 3 — el libro de aciertos y la foto por jornada

### Construidos, y lo que ocupan

| libro | qué guarda | medido con los datos de hoy |
|---|---|---|
| `data/intelligence/libro_de_la_valoracion.jsonl` | por jugador del tablero y día de mercado: valor, precio, puja, puja viva, decisión; y `d7`/`d14` con precio, puntos y partidos | 37 filas, **167 B/fila**, ~277 B con los dos plazos: **~300 KB/mes** |
| `data/intelligence/puntos_por_jornada.jsonl` | puntos, partidos y precio de los 547 al cerrar cada jornada | **11,9 KB/jornada, 0,44 MB la temporada** |

Ocupan menos de lo que se midió ayer (347 B y 102 KB) porque se escriben compactos.

- `d7` y `d14` los rellena la primera vuelta que llega pasado el plazo, con la fecha en que lo
  hizo: si llega tarde, se ve.
- «Jornada cerrada» = su último partido anterior al primero de la siguiente, más
  `NEXT_ROUND_UNLOCK_MINUTES`. El aplazado de la J6 del 21/10 cae en la foto de su semana: son totales.
- **Solo se escribe con la foto de este día de mercado**, igual que el escaparate. La verja pasa por
  el panel con la foto del 13/09 y **no escribió ninguno de los dos** (comprobado: no existen).
- Están en `los_libros.LIBROS` y en el `.gitignore`, así que `guardar_los_libros` los sube.

**Todavía no hay ni una fila de producción**: se empiezan a llenar en la primera vuelta tras
fusionar. El primer `d7` llegará 7 días después.

### El margen de las 51 ganadas

`python scripts/el_margen_de_las_ganadas.py`, sobre `bid_outcome_ledger.json` (del 10/08 al 23/09):

- **Contra la segunda puja: 0 de 51.** No se publica en ninguna parte: el tablón dice quién ganó y
  por cuánto, no quién quedó segundo. Es un «no se puede», no un «no se ha preguntado».
- **Contra el precio: 37 comparables.** Las otras 14 no traen el precio del momento de pujar (13
  reconstruidas desde la plantilla, más Trent sin precio).

| vía | n | por encima del precio (mediana) | media | máx |
|---|---|---|---|---|
| SUBASTA_CARTERA | 14 | +0,25 % | +0,25 % | +0,25 % |
| RENDIJA | 15 | +0,26 % | +0,30 % | +0,40 % |
| DESCONOCIDO | 6 | +1,82 % | +3,65 % | +14,08 % |
| ACQUISITION_BOARD | 2 | +7,08 % | +7,08 % | +7,21 % |
| **todas** | **37** | **+0,26 % (4.350 EUR)** | +1,19 % | +14,08 % |

**Lectura:** las dos vías que más pujan (cartera y rendija, 29 de 37) ganan con un **+0,25 %**
sobre el precio. Eso es lo más barato posible sobre el precio, así que ahí el 89,5 % **no** viene de
pagar de más: viene de que casi nadie más puja por esos jugadores. Donde se paga de más es en el
tablero (+7 %, n=2) y en las «desconocidas» (+14 % la peor). Con n=2 y n=6 no se puede decir más.

Una rareza en las perdidas: **Larrubia**, pujamos 4.797.017 y ganó una puja de 4.790.000
(margen −7.017). Perdimos pujando más. No lo he investigado.

---

## El paso 0, corrido por mí

```
EL PASO 0 HA TARDADO 225 s (3.8 min).
PASADO. Quedan probados 29 interruptores, apuntados en config/paso_0.json.
```

28 → **29**: el único nuevo es `BORDALAS_SOLVENCIA_POR_SU_PLAZO`. Revisado el diff de
`config/paso_0.json`: no se ha colado ningún nombre inventado. Va en el commit de este informe.

---

## Lo que no he hecho, y por qué

| no hecho | por qué |
|---|---|
| **Encender `BORDALAS_SOLVENCIA_POR_SU_PLAZO`** | es tuyo. Y hoy no cambiaría nada: el tope de la ventana es 0 con la caja a 0 |
| **Meter la marca en la valoración o en la puja** | lo prohíbe el encargo, y además **la medición no la respalda** |
| **Tocar `nos_suma`, el margen T−6 o los números prohibidos** | intactos: `MAX_SINGLE_SPECULATION_PERCENT`, `MAX_SAFE_DEBT`, el suelo de cobro, `MIN_WIN_PROBABILITY`, `MAX_PROJECTED_DAILY_RATE`, las cinco de `PUEDEN_ENCERRARLO`, `PRIMA_MAXIMA_DE_PUJA` y la ventana de 135 min |
| **Tocar `.github/workflows/bordalas-live.yml`** | no se ha tocado |
| **Una pantalla de React para la sombra y la lista del día** | `dashboard-v8` es un bundle compilado. Van en la foto y cada una tiene su comando |
| **La clase 2 con fecha de fichaje** | el catálogo no la trae. Se deduce de que `fitness` es más corto que los partidos del equipo, que da «llegó tarde», no «cuándo» |
| **Reproducir «los 73»** | salen 81 hoy y 72 el 13/09 |
| **Rellenar `d7`/`d14` hacia atrás** | no hay valoraciones guardadas de días pasados: por eso existe el libro |
| **Investigar lo de Larrubia** | queda anotado |
| **Traer aquí lo de la rama de ayer** | no está en `main`; el encargo dice desde `main` |
| **Escrituras contra Biwenger** | ninguna. Lo único de red ha sido un GET público del catálogo, sin login, al scratchpad, para la prueba de aceptación |
| **Empujar** | tú empujas |
