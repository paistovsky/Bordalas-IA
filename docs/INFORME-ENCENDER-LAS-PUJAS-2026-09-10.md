# Encender las pujas — informe

**Rama:** `pujas/encender-la-cartera` (desde `main` en `a2d1655`)
**Fecha:** 10/09/2026
**Verja:** 100/100 en verde (99 + 1 guardia nueva con 23 pruebas)
**Push:** NO. El primer reset se mira con los números delante.
**Escrituras contra Biwenger esta noche:** ninguna.

---

## 1. Las dos cosas que pediste antes de nada

### ¿Está corriendo el ciclo en producción?

**Sí.** La foto que publica producción de sí misma, bajada hace un momento:

```
publicado:  2026-09-10T06:33:03    modo LIVE
snapshot:   data/snapshot_20260910_063146.json   (2 min antes)
reloj:      quedan 0h 26m para el reset (10/09 07:00 hora de Madrid)
solvencia:  SIN_DEUDA · déficit 0 · cubierto · 38,2 h al plazo
bolsillo:   2.503.407 (497.307 de caja + 2.006.100 de margen de deuda)
objetivos:  43 en el tablero
```

Producción escribió su estado hace minutos, con un snapshot de hace dos.
El ciclo corre.

**Una salvedad, y la digo porque no la he podido verificar:** `gh` no está
instalado en esta máquina, así que **no he podido leer Actions**. Lo que
afirmo es que producción publicó un estado fresco esta mañana, que es
consecuencia de un run que terminó bien. No es lo mismo que ver la lista de
runs en verde. Si quieres esa comprobación, la miras tú en dos clics.

### ¿Qué pondría el modo cartera con el mercado de hoy?

Con la foto de las 06:33 de hoy, y **con la ventana abierta** (a 5 minutos
del reset):

**Lo que propone el reparto completo — 5 pujas:**

| jugador | puja | gana si entra | se lo lleva |
|---|---:|---:|---:|
| Gulácsi | 1.553.876 | 26.039 | 61 % |
| Benavidez | 150.376 | 2.519 | 46 % |
| Boayar | 150.376 | 2.519 | 46 % |
| Beitia | 180.451 | 3.023 | 46 % |
| Izei | 411.026 | 6.887 | 46 % |

→ compromete **2.446.105** · si las gana todas **40.987** · esperado **22.759**

**Lo que pondría de verdad, con tu tope de 3 del primer día:**

| jugador | puja | gana si entra | se lo lleva |
|---|---:|---:|---:|
| Gulácsi | 1.553.876 | 26.039 | 61 % |
| Benavidez | 150.376 | 2.519 | 46 % |
| Boayar | 150.376 | 2.519 | 46 % |

→ compromete **1.854.628** · si las gana todas **31.077** · esperado **18.201**

**Lo que cuesta tu tope:** 4.558 EUR de esperado (un 20 %), a cambio de no
comprometer 591.477 más el primer día. Me parece bien pagado.

De 43 objetivos en el tablero, **solo 18 son candidatos**: caen 23 por ser de
mercado de rival (ver el punto 4) y 2 por no estar disponibles.
Fichas libres hoy: **8**. Se usan 3.

---

## 2. HAY UNA RAZÓN POR LA QUE HOY NO PUJARÍA IGUAL, Y NO ES PRUDENCIA

**El cron nunca entra en la ventana del reset.**

- El reset es a las **07:00 de Madrid** = **05:00 UTC** (verano).
- La ventana son los últimos 15 minutos: **04:45–05:00 UTC**.
- El cron es `7 * * * *`: los runs caen en **04:07** y **05:07 UTC**.

```
  run 03:07 UTC  ->  113 min al reset  ->  ventana cerrada
  run 04:07 UTC  ->   53 min al reset  ->  ventana cerrada
  run 05:07 UTC  -> 1433 min al reset  ->  ventana cerrada   (ya pasó)
```

Un run a minuto :07 **no puede** caer entre los minutos 45 y 59 de la hora
anterior. Con el cron de hoy, la subasta se enciende y no puja nunca: siempre
contestaría `FUERA_DE_VENTANA`.

Esto **no es motivo para no encenderla** — encenderla es correcto y las
puertas están puestas —, pero sí es motivo para que sepas que **encendida y
sin tocar el cron, no pujará**. Y el workflow es tuyo: no lo toco.

**La línea que falta, en `.github/workflows/bordalas-live.yml`:**

```yaml
  schedule:
    - cron: "7 * * * *"
    - cron: "46,52 4,5 * * *"   # la ventana del reset: 04:46/04:52 UTC en
                                # verano, 05:46/05:52 en invierno
```

Dos minutos distintos porque los runs de GitHub Actions **arrancan tarde** con
frecuencia; con dos tiros hay muchas más posibilidades de que uno caiga
dentro. Y las dos horas porque el cron de Actions es UTC y no sigue el
horario de verano: una de las dos siempre acierta y la otra dice
`FUERA_DE_VENTANA` y no hace nada.

**Coste:** 4 vueltas más al día. Medido a ~7,5 peticiones por vuelta, son
**unas 30 peticiones/día más** sobre las 181 de hoy → ~211/día. Lejos de las
1.536/día que provocaron el 429 del 08/09.

**Mi recomendación para el primer reset:** no toques el cron todavía. Lanza el
workflow a mano (`workflow_dispatch`) a las **06:50 de Madrid**, con la
pantalla delante. Es exactamente lo que pediste: mirarlo con los números
delante. Si sale bien, entonces pones el cron.

---

## 3. Lo que se ha encendido, y por dónde no puede pasar

`plan_del_reset()` en `src/analysis/la_subasta.py` es la única puerta. El
ciclo no decide: pregunta y ejecuta. Las puertas, en este orden, y cada una
publica su motivo:

| # | puerta | qué la cierra |
|---|---|---|
| 1 | **INTERRUPTOR** | `BORDALAS_SIN_SUBASTA=1` |
| 2 | **SOLVENCIA** | el reloj no está en `SIN_DEUDA`/`CUBIERTO`, o hay déficit > 0 |
| 3 | **BLOQUEO_TEMPORAL** | la fase tiene las operaciones cerradas |
| 4 | **FUERA_DE_VENTANA** | faltan más de 15 min para el reset |
| 5 | **SIN_CESTA** | sin fichas libres, sin tope de caja, sin candidatos |
| 6 | **PEOR_CASO** | lo que quedaba concentraría 5+ de un club |
| 7 | **SIN_LIVE** | no se pidió en vivo (calcula y no ejecuta) |

**El reloj de solvencia va el segundo, antes que la ventana, a propósito.** Si
el viernes no llegamos en positivo da igual lo buena que sea la cesta: una
puja ganada es dinero que sale.

Y tus cinco límites del primer día:

- **Máximo 3 pujas**: `MAX_PUJAS_PRIMER_DIA = 3`. El recorte se hace
  **después** del reparto, no antes: primero se elige bien entre los 18 y
  luego se corta por la cola. Recortar antes sería elegir tres al azar.
- **Todas al precio topado de la curva**: cada puja sale a
  `precio + 0,25 %`, el óptimo que salió medido el 11/09. Hay una guardia
  que compara puja a puja contra `puja_de_cartera()`.
- **Nunca más pujas que fichas libres**: con 0 fichas no se puja por nadie.
- **Barandillas sobre el peor caso**: se cuenta la plantilla que **ya
  tenemos** más la cesta entera. Tres del Betis en el banquillo y dos en la
  cesta son cinco si entran las dos; el tope de 4 por club es el que lleva
  el líder de la liga (`MAX_SAME_TEAM`, no un número inventado aquí). Y se
  publica cómo quedaría la plantilla si entraran todas.
- **El reloj de solvencia manda**: puerta 2, con guardia propia que la
  prueba con la ventana abierta y la cesta llena.

---

## 4. Dos fallos que aparecieron al encenderla

Los dos habrían pasado la verja y no se ven en el log de un ciclo fuera de la
ventana. Los dos tienen ahora guardia.

### a) El ciclo leía el estado donde no está

Escribí `cycle["state"]`. `run_cycle` devuelve
`{snapshot, result, execution, post_action}`: el estado vive en
`cycle["result"]["state"]`. Y ni siquiera ahí está el tablero de adquisición
— eso lo monta la telemetría, que corre **después** y en otro proceso.

Resultado: cero candidatos, cero pujas, **y ni un error en el log**.
Encendido y mudo, que es la peor forma de estar apagado. Habrías mirado el
lunes y no habría pasado nada, sin nada que leer.

Arreglado con `_estado_publicado()`, que arma el tablero en el propio ciclo
**sin gastar ni una petición**: el tablón y el retrato de la competencia se
piden una vez por vuelta y están cacheados desde el 07/09.

### b) La compra a rivales seguía cerrada, y mi filtro la abría

De los 49 objetivos de ayer, **29 eran de mercado de rival**. Hoy, 23 de 43.
Mi filtro solo excluía `NO_DISPONIBLE`: la subasta habría pujado por
jugadores de rivales, que es una puerta que tienes cerrada.

Hoy no habría cambiado los nombres (los tres elegidos son del Computer), pero
cualquier otro día sí.

Ahora la lectura excluye, con guardia: los de mercado de rival, los que ya
tienen puja viva nuestra, y los no disponibles.

---

## 5. En el dashboard, antes y después

Bloque nuevo `subasta` en `status.json`, calculado con **la misma función que
usa el ciclo** — si la pantalla dice tres nombres, el ciclo puja por esos
tres. No es una segunda opinión: es la misma.

**Antes del reset:**

```
would_bid        true                 (el ciclo pujaría)
bids             por quién, cuánto, a qué precio de mercado,
                 qué probabilidad de llevárselo y cuánto gana
committed        1.854.628            lo que compromete si se ganan todas
all_won          31.077               lo que ganaría si entraran todas
expected         18.201               lo esperado, contando la pelea
seconds_to_reset 300                  cuánto falta para el cierre
window_open      true
slots_used / capped_at / dropped_by_cap / dropped_by_club
worst_case       cómo quedaría la plantilla si entraran todas
blocked_by       null, o la puerta que cerró
kill_switch      BORDALAS_SIN_SUBASTA=1
```

**Después:** cada puja enviada se apunta en el libro de pujas con
`target_source: "SUBASTA_CARTERA"`, y el bloque publica el resumen **filtrado
por ese origen** (`outcomes`): puestas, ganadas, perdidas, pendientes y por
cuánto nos ganaron. Separado del camino de siempre a propósito: sumarlos
daría un porcentaje de acierto que no es el de ninguno de los dos.

El cierre (ganada/perdida) ya lo hacía `sync_bid_outcomes` en cada vuelta.
Eso no lo he tocado.

---

## 6. EL INTERRUPTOR, ENTERO

**Una línea. Apaga todo: cualquier fase, cualquier cesta, cualquier hora.**

En el workflow — `.github/workflows/bordalas-live.yml`, en el paso
`Run Bordalas V10 PRODUCTION`:

```yaml
      - name: Run Bordalas V10 PRODUCTION
        shell: bash
        env:
          BORDALAS_SIN_SUBASTA: "1"        # <-- esta línea y no puja nada
        run: |
          python -m src.v10_full_autonomous_live
```

En tu máquina, PowerShell:

```powershell
$env:BORDALAS_SIN_SUBASTA = "1"
```

En bash:

```bash
export BORDALAS_SIN_SUBASTA=1
```

Con eso puesto, el plan sale `blocked_by: INTERRUPTOR`, cero pujas y cero
comprometido, y lo dice en el log y en la pantalla. No hay que tocar código
ni revertir nada. Hay una guardia que lo prueba **con la cesta llena y la
ventana abierta**: un interruptor que solo apaga cuando no había nada que
apagar no es un interruptor.

---

## 7. La verja

```
Los 100 en verde. Se puede subir.
```

Guardia nueva: `src/analysis/test_encender_las_pujas_v1.py`, **23 pruebas**,
registrada en `scripts/run_validation_gate.py`.

Protegen: el interruptor con la cesta llena · la solvencia por encima de la
ventana · el déficit de 1 EUR · fuera de la ventana · **dentro** de la
ventana (la contraria, para que romper la ventana entera no deje todo en
verde) · el bloqueo de fase · nunca más pujas que fichas · el tope de 3 · que
el tope se quede con las mejores · el precio topado de la curva puja a puja ·
el peor caso contando la plantilla · sin `en_vivo` no se ejecuta · la compra
a rivales cerrada · las pujas vivas · las fichas libres · la forma estable ·
que el ciclo lea el estado donde vive · que lo pujado llegue al libro con su
origen · y que nada de esto lea `data/`, la red ni el reloj.

Ninguna guardia toca `data/` ni Biwenger: la del libro escribe en un
directorio temporal, la del ciclo sustituye por delante las dos funciones que
tocarían la red. `git status data/` sale limpio.

También he comprobado el camino entero de punta a punta con la red y el libro
desviados: 3 pujas, `execute=True`, vendedor `None` (mercado del Computer) y
las tres apuntadas en el libro como `PENDING`.

---

## 8. Lo que entra en el commit

```
 scripts/run_validation_gate.py          la guardia nueva, registrada
 src/analysis/la_subasta.py              plan_del_reset + lectura_del_estado
 src/analysis/test_encender_las_pujas_v1.py   (nuevo) 23 guardias
 src/intelligence/bid_outcome_ledger.py  filtro por origen en el resumen
 src/telemetry/dashboard_state.py        el bloque `subasta`
 src/v10_full_autonomous_live.py         _estado_publicado, _pujar_en_el_reset,
                                         _anotar_en_el_libro
```

**Y dos ficheros que no son de este encargo:**

```
 src/intelligence/archivo_diario.py
 src/analysis/test_intel_v1.py
```

Son los cambios de la rama **`archivo/fechar-por-el-informe`** (fechar la
carpeta por el `generated_at` del informe), que estaban en el índice cuando
salí de `main` y se han venido en esta rama. He comprobado que son **idénticos
bit a bit** a esa rama (`git diff archivo/fechar-por-el-informe` sobre esos
dos ficheros sale vacío). Esa rama **sigue sin fusionar**: si la fusionas
después, no habrá conflicto.

---

## 9. Lo que NO he hecho

- **No he hecho push.** Nada de esto está en producción.
- **No he tocado el workflow.** Ni el cron, ni el interruptor: son tuyos.
- **No he pujado.** Ni una escritura contra Biwenger esta noche.
- **No he leído Actions**: `gh` no está instalado (ver punto 1).
- **No he movido ningún umbral.** El 0,25 % de la curva, el 4 por club, el
  15 de la ventana y el 5 % de caída son los de antes.
- **No he cambiado cómo se eligen los objetivos** fuera de la ventana: el
  camino de siempre está intacto.

---

## 10. Lo que hay que mirar en el primer reset

1. Que en la pantalla, a las 06:50, salga `subasta.would_bid: true` con tres
   nombres y `seconds_to_reset` por debajo de 900.
2. Que en el log del ciclo salga el bloque `LA SUBASTA DEL RESET` con
   `ENVIADAS 3 · FALLIDAS 0`.
3. Que a las 07:05 las tres estén en el libro, y a la vuelta siguiente ya
   cerradas en ganada o perdida.
4. Si algo de eso no cuadra: `BORDALAS_SIN_SUBASTA=1` y a mirarlo con calma.
