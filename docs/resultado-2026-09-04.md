# Resultado de la noche del 04/09/2026

Rama `arreglos/2026-09-04`, subida. `main` sin tocar.

**Puerta: 57 de 57 en verde.** Eran 52 al empezar; las cinco nuevas
son las guardias de esta noche, y las cinco están en
`.github/workflows/bordalas-live.yml`, así que CI las corre.

Cinco commits, uno por arreglo. Ninguno toca umbrales, presupuestos,
lógica de puja ni de venta. Los umbrales de especulación revertidos
en `9bf60c4` siguen revertidos.

---

## Lo que se arregló

### 1. `VIGILAR` vuelve a significar algo

`c99bbbc` — `src/analysis/player_availability.py`

Los once titulares salían marcados VIGILAR, Yamal incluido. 205 de
los 569 jugadores del catálogo. Una etiqueta que le toca al 36 % de
la liga no avisa de nada: se lee como decorado y se deja de mirar.

La causa resultó ser más precisa de lo que decía la auditoría.
`fitness` no es solo "el array de puntos": es **el historial por
jornada**, y admite tres cosas distintas dentro:

```
un número     los puntos de esa jornada
null          jornada sin observación
un texto      no jugó, y por qué: injured, doubt, sanctioned, discarded
```

De aquellos 205, **solo 13 traían un texto**. El resto eran puntos.

Ahora VIGILAR pide una señal de verdad: un texto en `fitness`, un
`statusInfo` escrito, o un `status` que no es `ok` y no
reconocemos (`unknown`, `discarded`, que existen en el catálogo).

**Esto no cambia ninguna decisión, y está comprobado.** Los únicos
dos campos que leen el motor de alineación
(`lineup_engine.py:341,688`) y el de objetivos
(`strategic_target_engine.py:326,496`) son `available` y
`automatic_lineup`, y salen idénticos para todos los estados
posibles. Cambia la etiqueta y el `risk`, que no los lee nadie para
decidir.

Se añade `signals` a la ficha, para que la pantalla pueda decir **por
qué** se vigila a alguien en vez de solo que se le vigila.

Guardia: `test_etiqueta_vigilar_v1` (14 pruebas), con el caso
`status=ok fitness=[4]` que fallaba y un XI sano completo que tiene
que salir limpio.

### 2. El tablero rancio ya comprueba la jornada

`7e61d53` — `futbolfantasy_provider.py`, `dashboard_consistency.py`

La vía HIT comprobaba `matchday` desde el primer día. Las dos vías de
respaldo —snapshot sin objetivos, y scrapeo sin un solo
emparejamiento— devolvían el tablero anterior sin mirarla. Y el
auditor de consistencia lo daba por bueno contando jugadores, que es
justo lo que un tablero de otra jornada también cumple: trae sus 59
cabezas.

Ahora hay una sola función, `stale_fallback()`, por la que pasan las
dos vías. Si el tablero es de otra jornada **no se sirven sus
jugadores**: se devuelve vacío, con estado `STALE_WRONG_MATCHDAY` y
con la jornada real que tenía —no la de hoy, que sería disfrazarlo de
bueno—.

Un tablero sin jornada tampoco pasa. Y la comparación normaliza el
tipo: rechazar un `"4"` de JSON contra un `4` de Python habría tirado
un tablero bueno.

En el panel de consistencia hay una fila nueva que compara la jornada
del tablero contra la del calendario. Es la primera que no compara
contra Biwenger, y lo dice: `source: CALENDARIO`.

Guardia: `test_jornada_del_tablero_v1` (14 pruebas), que ejercita las
dos vías de respaldo de verdad —con `fetch` cayéndose— y las cuatro
filas del auditor.

**Queda media cadena sin cerrar, a propósito. Está más abajo.**

### 3. Las plantillas rivales traen jugadores

`a190e9f` — `src/telemetry/squads.py`, `dashboard_state.py`

Salían de `standings[].lineup`, que es la alineación que dejó puesta
cada manager, y venía vacía en los siete. Mientras tanto
`ledger_audit` conocía los rosters de todos —17, 14, 13, 12
jugadores—, reconstruidos desde los perfiles de usuario. Dos fuentes
en casa y se estaba pintando la muda.

Ahora manda el ledger, que además es la respuesta correcta a la
pregunta: la alineación dice a quién puso el sábado, el perfil dice a
quién **tiene**, y una plantilla es lo segundo. La alineación se
sigue usando para marcar quién es titular, que es lo que el ledger no
sabe. `standings[].lineup` queda de respaldo.

Y la segunda mentira, que era peor que la primera: **`available:
true` con `players: []`**. Una tabla en blanco marcada como
disponible se lee como "el rival no tiene jugadores", no como "no lo
sabemos". Sin una sola plantilla ahora sale `available: false` con su
motivo, y cada manager vacío dice por qué lo está. Se añade
`managers_with_squad` para que media pantalla pueda decir que es
media.

Guardia: `test_plantillas_rivales_llenas_v1` (9 pruebas), incluida la
invariante "disponible implica jugadores" probada contra cuatro
formas distintas de llegar sin datos, y una comprobación de que el
dashboard de verdad le pasa la fuente buena —arreglar la función y no
enchufarla habría dejado el fallo intacto, que es exactamente como
llevaba desde el 20/08—.

### 4. Los penaltis: apagados, y explicado

`5995b56` — `src/intelligence/penalty_intelligence.py`

**No tiene arreglo razonable, y la causa no es el emparejamiento.**
Es el plan Free de API-Football cortando la cadena por los dos
extremos:

1. **La identidad se busca en 2024.** `search_player` consulta con
   `PLAYER_LOOKUP_SEASON = 2024`, y el comentario del propio código
   dice por qué: es lo único que el plan Free sirve. Quien llegó a
   LaLiga después no aparece. En la caché de emparejamiento son **21
   de 44 con `external_id: null`** —Gustavo Puerta, Valentín Gómez,
   Gabriel Suazo, Álvaro Fidalgo, Bayindir, Mangala—. Esos son los 33
   registros con `mapping_safe: false`.

2. **Las estadísticas se piden de 2026.** Y para los 6 que sí
   emparejaron bien, la llamada pide `season = CURRENT_SEASON = 2026`,
   que el plan rechaza con todas las letras:

   > `Free plans do not have access to this season, try from 2022 to 2024.`

   Esos 6 errores están escritos en `penalty_kickers.json`.

**No hay una temporada en la que las dos mitades funcionen a la vez.**

El arreglo aparente —pedir las estadísticas de 2024— sería peor que
no tener el dato: pondría un +8 en el once de **2026** por penaltis
de hace dos temporadas, y para casi la mitad de la plantilla no
habría dato ninguno. Un bonus de 8 puntos ordena el XI. Hay una
guardia que impide que alguien lo haga como parche de una tarde.

Así que **apagado**, como pedía el encargo. El resultado es idéntico
al de hoy —bonus 0.0 para todos, ni un solo XI cambiado— pero sin
gastar cuota. La maquinaria entera se queda intacta y probada:
encender es `PENALTY_INTELLIGENCE_ENABLED=1` el día que haya plan de
pago.

Guardia: `test_penaltis_apagados_v1` (8 pruebas), que comprueba que
apagado no toca ni red ni disco, que devuelve exactamente lo que ya
salía, y que la maquinaria sigue entera para reencenderla.

### 5. El tope por operación ya no sale 0

`a8d659e` — `src/telemetry/dashboard_state.py`

Era un nombre de clave, como decía el encargo. El motor devuelve
`single_operation_limit`; el lector buscaba `max_operation` y, de
reserva, `max_single_operation`. Ninguna de las dos existe en ningún
sitio del sistema, así que `safe_int(None)` daba 0.

La pantalla no enseñaba un número pequeño: enseñaba **lo contrario**
de lo que decía el motor, y el dueño decide mirando la pantalla.

Arreglado en el lector. El motor sin tocar. Los dos nombres viejos se
quedan detrás por si algún estado guardado los trae.

Guardia: `test_tope_por_operacion_v1` (6 pruebas). La que importa
llama al motor de verdad y comprueba que sigue publicando
`single_operation_limit`, en vez de comparar contra una copia del
nombre: si mañana se renombra en el motor, salta aquí en vez de
volver a dejar la pantalla en cero en silencio.

---

## Lo que se quedó fuera, y por qué

### La otra mitad de la tarea 2

El respaldo ya rechaza un tablero de otra jornada. **Pero
`candidate_starter_lookup.py` —que es por donde pasa la valoración—
lee el fichero del disco directamente y nunca rechaza por jornada.**
Carga el `matchday` en la ficha de cada jugador (`:200`) y su propio
docstring dice que ese sello "es el guardarraíl contra usar datos de
una jornada en otra, que es justo el fallo del 16/08/2026". Lo
carga; no lo aplica.

Cerrarlo significa que, con un tablero de otra jornada, los
jugadores se quedarían sin `starter_probability` y sin jerarquía. Eso
**sí** cambia valoraciones y por tanto pujas, y el encargo decía que
no. Queda escrito aquí porque es la mitad que falta, no un detalle.

El "hecho cuando" de la tarea —el respaldo rechaza, el auditor lo
detecta, hay guardia— está cumplido entero.

### El código muerto no se ha borrado

Confirmado con `grep` cuál lo está de verdad (ver más abajo: la
auditoría se equivocaba en la mitad). No se ha borrado nada: borrar
código no arregla nada, y esta noche era para arreglar cosas rotas.
La lista exacta de lo que sí se puede borrar está en
`docs/datos-sin-lector-2026-09-04.md`.

### Los tres bloques de datos sin lector

No se han enchufado, como mandaba el encargo. Está todo trazado —qué
hay, dónde muere cada cadena, qué costaría y qué habría que medir
antes— en **`docs/datos-sin-lector-2026-09-04.md`**.

### Nada de lo que la auditoría marca como decisión del dueño

Ampliar plantilla, el `intent` por tipo de operación,
`cost_per_point`, los umbrales, la concentración por jugador,
`HARD_SAFETY`. Sin tocar.

---

## Lo que encontramos y no esperábamos

**1. La señal de lesión estaba dentro de `fitness` todo el tiempo.**
La auditoría lo daba por "el array de puntos", a secas. Es un
historial mixto que también trae texto. El caso que lo demuestra es
Brugué: `status: ok` y `fitness: ["sanctioned"]`. Su estado actual
dice que está bien y su historial dice que se perdió la última
jornada sancionado. Es exactamente la clase de jugador que merece un
VIGILAR, y era el único de 569 que lo merecía por esa vía. El arreglo
no fue quitar una fuente: fue leerla bien.

**2. Los penaltis no fallan por emparejar mal.** La auditoría decía
"averigua por qué el emparejamiento falla siempre". Falla, pero es el
síntoma. Aunque emparejaran los 39 perfectamente, la llamada de
estadísticas seguiría rebotando: el plan no sirve la temporada en
curso. **El código ya lo sabía y estaba escrito**, en el comentario
de `PLAYER_LOOKUP_SEASON`: "el plan Free permite consultar jugadores
ahí". Nadie ató ese comentario con la llamada de estadísticas de dos
ficheros más allá.

**3. La auditoría se equivoca sobre el código muerto, y por el lado
peligroso.** Dice que `speculation_intelligence.py` y
`market_brain_shadow.py` "arrastran `external_status.py`,
`injuries.py` y `transfers.py`". Los dos primeros sí están muertos.
**Los otros tres no**: la cadena
`autopilot.py:64 → intelligent_bid_engine.py:10 → external_status.py
→ injuries.py, transfers.py` está viva, y no es un import de adorno —
`intelligent_bid_engine.py:459` llama a `get_external_player_status()`
para cada candidato con `action == "PUJAR"` y le resta el
`risk_score` al score—. **El caché de 38 KB es de esa cadena viva.**
Borrarlo por sobrante haría salir a la red en plena ruta de pujar.

**4. `max_observed_bid` sí tiene lector, pero no decide.**
`rival_bid_model.py:408` lo lee y lo mete en una variable
`observada`… que solo sirve para rellenar el campo de salida
(`:446`). La `participation` —que sí decide cuánto pujar— se calcula
con el **número** de pujas y la cobertura del ledger, nunca con el
**importe**. Sabemos por cuánto puja cada rival y modelamos su
probabilidad de pujar sin usarlo.

**5. La puerta de validación gastaba cuota de API-Football.** Al
correrla en local se reescribían entradas de `penalty_kickers.json`
con marca de tiempo nueva: algún test del ciclo llega hasta el motor
de alineación con jugadores reales y dispara la llamada de penaltis.
Con la señal apagada ya no pasa: comprobado en la última pasada, el
fichero no se toca. La puerta corre igual de verde y sin gastar
cuota.

**6. `src/intelligence/player_status.py` tiene el mismo bicho del
`fitness` y no importa.** `normalize_biwenger_status()` levanta una
alerta "Fitness Biwenger: [...]" con la misma lógica equivocada. No
se ha tocado porque **el módulo está muerto**: su único importador es
su propio test. Si algún día se resucita, arrastra el bug arreglado
esta noche.

---

## Cómo quedó

```
rama          arreglos/2026-09-04, subida
main          sin tocar
puerta        57/57 en verde  (52 al empezar, 5 guardias nuevas)
commits       5, uno por arreglo
CI            las 5 guardias añadidas a bordalas-live.yml
dinero        cero cambios: ni umbrales, ni presupuestos, ni pujas,
              ni ventas, ni el revert de 9bf60c4
```

Nada quedó a medias por falta de tiempo. Lo único que se dejó sin
hacer —el guardarraíl de jornada en `candidate_starter_lookup`— se
dejó porque toca valoraciones, y eso lo decide el dueño.
