# EL CATÁLOGO FRESCO EL DÍA DE LA JORNADA, Y LAS 96 GUARDIAS REPASADAS

Rama `higiene/guardias-sin-reloj`, desde `main` (`97d281a`).
**96 de 96 en verde. Ni una llamada a Biwenger.** Sin push.

---

# TRABAJO 1 — El catálogo, fresco cuando importa

## Lo que cuesta, medido

```
  martes (NORMAL)            7 peticiones/vuelta   catalogo: cache
  miercoles (PREPARATION)    7                     catalogo: cache
  jornada en marcha (LOCKED) 7                     catalogo: cache
  ---
  DIA DE JORNADA (T-12 h)    8                     catalogo: FRESCO
  T-2 h (FINALIZATION)       8                     FRESCO
  T-90 min (HARD_SAFETY)     8                     FRESCO
  calendario roto            8                     FRESCO
```

**Al día siguen siendo 349.** Lo fresco vale **+24 peticiones por jornada**, no
por día: son las ~12 h de `HIGH_ATTENTION` × 2 vueltas/hora.

**No cachearlo nunca costaría 48 al día.** Pagamos 24 por jornada en vez de 336 a
la semana.

## Qué fases van frescas, y por qué ésas

Fresco mientras **la alineación todavía se puede escribir y el cierre está
cerca**:

| Fase | Cuándo | Catálogo |
|---|---|---|
| `NORMAL` | > 48 h al cierre | caché |
| `PREPARATION` | ≤ 48 h | caché |
| **`HIGH_ATTENTION`** | **≤ 12 h** | **fresco** |
| **`FINALIZATION`** | **≤ 2 h** | **fresco** |
| **`HARD_SAFETY`** | **pasado T−90 min** | **fresco** |
| `ROUND_LOCKED` | jornada en marcha | caché |
| **`CALENDAR_UNKNOWN`** | no se sabe | **fresco** |

**`ROUND_LOCKED` se cachea a propósito**: la jornada está en marcha y el once ya
no se puede tocar. Un estado viejo no puede estropear una alineación cerrada.

**No saber sale caro a propósito**: con el calendario roto se pide fresco. No
saber en qué fase estamos tiene que costar peticiones, no puntos.

**Si te parece poco margen**, meter `PREPARATION` en el conjunto sube de ~12 h a
~48 h por jornada: **+96 en vez de +24**. Es una línea, y `FASES_SIN_CACHE` está
para eso.

## Un detalle que importa

**El catálogo pedido en fase caliente no se guarda en disco.** Si se guardara,
quedaría esperando a que la fase cambie para servirse con el estado de hace una
hora. Lo que no está no se puede servir por error.

Y **la fase se mira una sola vez por vuelta** y se pasa: si cada lectura la
dedujera por su cuenta, dos llamadas de la misma vuelta podrían caer a distinto
lado del cierre.

**Seis guardias nuevas**, con los dos casos que pediste: martes cacheado, día de
jornada fresco.

---

# TRABAJO 2 — Las 96 guardias, repasadas

## El escáner que escribí primero no servía

Buscaba `datetime.now()` dentro de las guardias. Se lo pasé a la versión de ayer
de `test_ojeador_prensa_v1` —la única que sabemos que explotó sola— y dijo
**LIMPIA**.

Y con razón: **esa guardia nunca llama al reloj.** Llama a `build_press_report`
sin pasarle `now`, y la hora la lee producción. **El pecado es de omisión, no de
comisión.**

Rehecho para buscar lo que de verdad pasa: *una guardia que llama a una función
que acepta la hora y no se la da*. Con eso, la versión de ayer sale
**BOMBA_DE_RELOJERIA** señalando la línea exacta. **Un escáner que no detecta el
único incidente que existe no vale para nada.**

Está en `scripts/guardias_que_leen_el_mundo.py`. Encuentra solo **54 funciones de
producción que aceptan la hora**, leyendo el código: el día que alguien añada una
con `now=None`, entra sola.

## El inventario

**96 guardias. 76 limpias. 20 con alguna dependencia:**

| | Cuántas | Qué es |
|---|---:|---|
| **Hora omitida + fecha fija** | 7 | candidatas a bomba |
| Hora omitida sin fecha fija | 4 | revisar |
| Reloj sin fecha fija | 3 | probablemente inofensivas |
| Leen disco | 3 | dependen de la máquina |
| Tocarían la red | 3 | comprobar que están sustituidas |

## Y la prueba que decide: adelantar el reloj

Un candidato no es una bomba. **La única prueba que vale es mover el reloj y ver
qué se cae sola**, así que lo hice: **+365 días** sobre cada una de las siete.

**Dos eran falsos positivos por colisión de nombres** — el escáner empareja por
nombre de función, y `leer` y `escribir` son palabras muy comunes:

- `test_peticiones_v1` → el `leer` que ve está en `un_dato_un_nombre`, que esa
  guardia ni importa.
- `test_correccion_jerarquia_v1` → igual con `escribir`.

**Las cinco reales, con el reloj un año por delante:**

| Guardia | Llama a | Con +365 días |
|---|---|---|
| `test_live_solvency_authority_v115` | `classify_phase()` | **sigue verde** |
| `test_action_starvation_v1` | `get_backoff()` | **sigue verde** |
| `test_estado_de_carrera_v1` | `build_race_state()` | **sigue verde** |
| `test_ojeador_informe_v1` | `record_report()` | **sigue verde** |
| `test_arbitro_v1` | `manager_scoreboard()` | **sigue verde** |

**Ninguna es bomba viva.** Son deuda —deberían recibir la hora— pero no se van a
poner rojas solas. Ahí las dejo listadas, como pediste.

## Lo que sí arreglé, y es lo más grave de la noche

**Dos llamadas más en `test_ojeador_prensa_v1` que el arreglo de ayer no cubrió.**
Ayer parché `_informe`; quedaban dos llamadas directas.

Una es inofensiva (el XML es basura, no hay ítems que caducar). **La otra no:**

`test_un_nombre_de_dos_fichas_no_se_adivina` afirma que el código **no elige**
entre dos jugadores con el mismo nombre. Comprobado:

```
  SIN pasar la hora  ->  players: 0   too_old: 1
  CON la hora fija   ->  players: 0   too_old: 0
```

**Desde ayer a las 17:00 esa prueba pasaba porque el titular se descartaba por
viejo, no porque el código se negara a adivinar.** La lista salía vacía sin que
nadie comprobara nada.

**Es peor que un rojo: un verde que dejó de probar.** Un rojo se ve; esto no lo
cuenta nadie hasta que falla de verdad, en producción.

Arreglado, y con una aserción nueva que lo blinda: `too_old == 0`. Si el ítem
vuelve a descartarse por viejo, la prueba lo dice en vez de pasar de largo.

## Las tres que leen disco y las tres que tocarían la red

Listadas, no arregladas — no explotan solas:

- **Disco**: `test_v10_full_autonomous_live`, `test_dashboard_execution_v121`
  (buscan `snapshot_*`), y `test_futbolfantasy_source_v12`, que es la única con
  deuda registrada desde el 18/09 y ya nos costó un rojo el 07/09.
- **Red**: `test_balon_parado_v1`, `test_marcador_v1`,
  `test_plantillas_rivales_v1`, `test_venta_ejecutable_v1` — todas con la sesión
  sustituida; las referencias son a los dobles, no a salidas reales.
- `test_peticiones_v1` aparece por `biwenger.as.com`, que es la URL de sus
  sesiones de mentira.

---

# LA REGLA, EN LA DOCTRINA

**Regla 23: ninguna guardia lee estado externo** — ni el disco, ni la red, ni el
reloj. Está escrita en `docs/DOCTRINA.md` con el incidente de ayer como motivo,
el caso del verde que dejó de probar, y por qué el escáner busca omisiones y no
`datetime.now()`.

---

# LO QUE ENTRA EN EL COMMIT

`git status` antes. **Siete ficheros:**

```
 M src/biwenger/cache_del_reset.py         la regla de la fase
 M src/collectors/league_collector.py      la aplica al catalogo
 M src/analysis/test_peticiones_v1.py      de 31 a 37 guardias
 M scripts/contar_peticiones_del_ciclo.py  mide por fase
 M src/analysis/test_ojeador_prensa_v1.py  las dos llamadas que faltaban
 M docs/DOCTRINA.md                        regla 23
?? scripts/guardias_que_leen_el_mundo.py   el barrido
```

**Ningún dato, ningún umbral movido, el workflow sin tocar.**

---

# LO QUE NO HE HECHO

**No he arreglado las cinco que omiten la hora sin ser bombas.** Pasarles la hora
es correcto y es una tarde; ninguna se pone roja sola y no quiero mezclar quince
ficheros con lo del catálogo, que entra antes del viernes.

**No he tocado las tres que leen disco.** La de FutbolFantasy necesita fixture
propio y es trabajo de verdad.

**No he metido `PREPARATION` en las fases frescas.** El número de hacerlo está
arriba.

**Ni una llamada a Biwenger.** El recuento sale de la sonda contra sesión falsa,
y la fase se lee del calendario que ya vive en disco: 0,00 s, sin red.

---

**La frase para mañana:** el catálogo va **fresco las 12 horas anteriores al
cierre** y cacheado el resto — **+24 peticiones por jornada** en vez de las 336
semanales que costaría no cachearlo nunca, y el día que importa no se alinea a un
lesionado con el estado de esta mañana. Del barrido de las 96: **76 limpias**, y
de las siete candidatas a bomba, **dos eran colisión de nombres y las cinco reales
aguantan un año de reloj adelantado**. Lo que sí apareció fue peor que un rojo:
**una prueba en verde que llevaba desde ayer a las 17:00 sin comprobar nada**,
porque su titular se descartaba por viejo antes de llegar a la aserción.
