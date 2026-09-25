# La sombra miente, y el embudo también

**Encargo:** «LA SOMBRA MIENTE, Y EL EMBUDO TAMBIÉN», 25/09/2026 (noche)
**Rama:** `arreglo/la-sombra-no-miente`, desde `main` en `ec32f4fa` (con los cinco interruptores)
**Scripts:** `python scripts/la_sombra_contra_lo_que_hizo.py` · `python scripts/la_lista_de_la_noche.py`

## Veredicto

**Arreglado, y con una respuesta al bloque 1 que el encargo no esperaba: Pepe no puja por un
camino, sino por cuatro.** La lista vieja solo imitaba uno (el tablero), y encima lo imitaba mal.
La nueva no reconstruye nada:

| camino | cómo lo mira la sombra ahora | ¿se puede preguntar sin escribir? |
|---|---|---|
| **tablero** (lo ejecuta la acción de la vuelta) | lee las filas que el tablero deja en `BID`, tal cual (vía, bolsillo, topes y puja salen del mismo sitio), y aparta, como el ejecutor, a las que ya tienen puja nuestra viva | **sí** |
| **ventana del reset** (04:45, `plan_del_reset`) | llama a `plan_del_reset` con **el mismo estado que el ciclo**; solo le cambia la hora, poniéndola dentro de la ventana | **sí** |
| **carril** (`la_rendija`) | enseña **lo que decidió en su última vuelta**, y dice que no es una predicción | **no**: decide dentro de `carril_executor.correr` y escribe a continuación |
| **BUY V10** | «no cubierto», dicho | **no**: decide dentro de `build_controlled_run`. Dormido desde el 04/09 |

**La prueba del 25/09 sale: «Esta noche no pujaría por nadie.»** Lo cumple la guardia con los
números de Lejeune, lo cumple la foto real de las 19:13, y lo cumple el panel montado entero.

**El embudo dice ya la verdad:** los rivales van aparte, cada candidato está en su puerta, y la
última línea es «Hoy se puede pujar por N». En las cuatro fotos da exactamente lo que el tablero
pudo pujar: **0, 2, 0 y 0**.

**Lo que no puedo darte con número serio es cuántas veces acierta** (§2): solo hay cuatro fotos, están
hechas a media tarde, y la mitad de las pujas del libro no dicen quién las puso.

---

## 1. Dónde se armaba la sombra, y qué hacía por su cuenta

En [acquisition_board.py](src/analysis/acquisition_board.py), dentro del bucle de cada fila (el
bloque «LA LISTA DE LA NOCHE (22/09/2026)», que ya no está), cada fila calculaba `la_noche` con tres
piezas propias:

1. **La vía**: `la_via_que_ganaria`, un máximo sobre las cinco vías con el valor reescalado a la
   moneda de la liga. **No era `classify_operation`**, que es quien decide la vía y, con ella, el
   bolsillo y el listón.
2. **El bolsillo**: `presupuesto`, el de la intención **de hoy**. Con Lejeune, la intención de hoy era
   especular, ese bolsillo venía `None` y `optimal_bid` con `None` **no pone tope**.
3. **Se saltaba la cadena del tablero**: estado del jugador, contraoferta, rivales, tope de tener y
   concentración.

Resultado: valor de una vía, bolsillo de otra. **Lejeune, 3.674.989**, cuando la decisión real era
`SUPERA_PRESUPUESTO`.

Y había **otra** sombra, `la_sombra_de_la_puja`, que sí llama a `plan_del_reset`, pero **levanta los
candados** (solvencia, caja, fichas) para decir lo que haría «aunque no pueda». Esa se queda como
está: contesta otra pregunta y lo dice.

### Lo que se ha cambiado

- **[acquisition_board.py](src/analysis/acquisition_board.py)**: fuera la reconstrucción (−60 líneas).
  **Ninguna decisión cambia**: `la_noche` era un campo al lado que nadie leía para actuar.
- **[la_lista_de_la_noche.py](src/analysis/la_lista_de_la_noche.py)**, reescrito. `la_lista(tablero,
  plan_en_la_ventana, carril)` junta lo que ya deciden los que pujan, y `en_la_ventana(lectura)` es
  `plan_del_reset` con la hora puesta y `en_vivo=False`. **No importa ni `optimal_bid`, ni
  `value_candidate`, ni `classify_operation`, ni `budget_for_intent`, ni la moneda.** Hay guardia de
  eso, que mira el código y no la prosa.
- **[dashboard_state.py](src/telemetry/dashboard_state.py)**: el estado que ve la subasta se monta
  **una vez** (`estado_de_la_subasta`), y la subasta y la lista leen ese mismo. Antes la subasta lo
  armaba en línea y la lista no lo veía.
- Si el tablero y la ventana eligen al mismo jugador, sale **una** puja, la del tablero. Cuando llega
  la ventana, `lectura_del_estado` ya lo deja fuera por `has_live_bid`. Lo destapó la medición:
  Cabrera salía dos veces el 18/09.

### Lo que falta para cubrir los otros dos caminos

- **Carril:** separar en `carril_executor.correr` la decisión (permiso → margen → bolsillo →
  pagables → elegidos) de la escritura. Es tocar un ejecutor que escribe en Biwenger. No lo he
  hecho: el encargo dice que la sombra mira y no decide, y ese cambio es del ejecutor.
- **BUY V10:** lo mismo con `build_controlled_run`. Está dormido desde el 04/09.

Hasta entonces la lista **dice que no los cubre**, en su `reason` y en `caminos`.

---

## 2. La prueba: ¿acierta lo que pasó?

`scripts/la_sombra_contra_lo_que_hizo.py`. Cada foto se mide con **los interruptores que había en
producción esa noche**: `plan_del_reset` los lee, y sin ellos el 25/09 salía frenado por una
solvencia que en producción no frena. Lo real sale de `bid_outcome_ledger`, desde la hora de la foto
hasta el reset siguiente.

| foto | sombra vieja | sombra nueva | lo que pasó | puntuación |
|---|---|---|---|---|
| 14/09 16:33 UTC | no existía | no pujaría (ventana: `SOLVENCIA`) | la ventana pujó por **Balde, Benavidez, Paco Cortés y Selu Diallo** (02:48–02:54) | **4 graves** |
| 18/09 14:16 UTC | no existía | Cabrera 3.134.660 (tablero); Maffeo **aparte**: ya tiene puja viva de 1.664.350 | Cabrera 3.116.031 a las 15:18 (sin atribuir); Maffeo nada nuevo | Cabrera **dicha y pujada** |
| 23/09 06:51 UTC | no existía | no pujaría (ventana: `SOLVENCIA`) | Ceballos a las 09:20 (del dueño) | **acierta** |
| 25/09 17:13 UTC | **Lejeune 3.674.989** | **no pujaría por nadie** | la noche aún no ha pasado | sin puntuar |

**Con n = 3 noches, la cuenta es: 1 acierto, 1 dicha y pujada, 0 sustos falsos y 4 graves.** Pero
cada fallo tiene una explicación, y ninguna es la de antes:

- **Los 4 graves del 14/09 no son un fallo de la sombra: el estado cambió.** La propia foto de las
  16:33 publicaba la subasta frenada por `SOLVENCIA`, y a las 02:48 la ventana pujó. Entre la foto y
  la ventana hay diez horas. La sombra es **de la vuelta**, y en producción se recalcula cada hora:
  la que vale es la de la última vuelta antes de las 04:45 (la de las 03:07). Una foto de media tarde
  no es esa. Y además, el código de hoy sobre el estado del 14/09 no es el código del 14/09: la
  solvencia se reescribió el 23/09.
- **Maffeo destapó un fallo más, y ya está arreglado.** El tablero lo dejaba en `BID` **con
  1.664.350 nuestros ya vivos** (del carril, puestos a las 14:15), y quien ejecuta el tablero,
  `decision_orchestrator`, aparta a esos (`players_with_live_bid`,
  [decision_orchestrator.py:2850-2868](src/analysis/decision_orchestrator.py#L2850-L2868)). La
  primera versión de la sombra nueva lo anunciaba como puja: un susto falso. Ahora hace lo mismo que
  el ejecutor: lo aparta y lo enseña como «ya tiene puja viva». Tiene guardia
  (`test_la_que_ya_tiene_puja_viva_no_se_repite`). **Leer el `BID` del tablero no bastaba: hay que
  leer también lo que hace quien lo ejecuta.**
- **La puja de Cabrera no se puede atribuir.** El libro la apuntó `DESCONOCIDO / TABLON`: apareció
  en el tablón sin que ningún camino la registrara al ponerla. Eso es lo que hace el dueño a mano,
  **y también lo que hace el camino del tablero**, que no apunta al pujar. Con el libro de hoy **no
  se puede saber** si una puja `TABLON` la puso Pepe o el dueño. Ese hueco hace que el fallo grave
  («no dice nada y puja») sea **indetectable** para el camino del tablero.
- **Unai López (23/09, 02:56, ventana del reset)**, que es el caso que el dueño cita, **no tiene
  foto** de esa noche. No se puede puntuar.

**La sombra vieja: n = 1 publicada** (la del 25/09), **0 noches puntuables**, y su única afirmación
contradice la decisión real del propio tablero. Ése es todo su historial.

**Para que esto se pueda medir de verdad hacen falta dos cosas que no he construido:** guardar la
lista de la última vuelta antes de la ventana (hoy solo queda la foto que baja el dueño), y que el
camino del tablero apunte sus pujas en `bid_outcome_ledger` al ponerlas.

### La prueba de aceptación

- **Guardia** `test_el_25_09_no_puja_por_nadie`: con Lejeune y Antonio Blanco descartados por el
  `optimal_bid` de verdad, la ventana sin cesta y el carril sin nadie, dice **«Esta noche no pujaría
  por nadie.»**
- **Foto real del 25/09 a las 19:13:** «Esta noche no pujaría por nadie», con la ventana en
  `SIN_CESTA` (0 fichas libres).
- **Panel montado entero** con el snapshot del disco, sobre una copia: «Esta noche no pujaría por
  nadie», y **ningún libro tocado**.

### La guardia que pedía el encargo

`test_la_sombra_dice_lo_que_pepe_haria_v1`, con 8 pruebas. La principal, `test_la_sombra_dice_lo_que_pepe_haria`,
fabrica el candidato con `optimal_bid` **de verdad** y **exige que salga `SUPERA_PRESUPUESTO` antes
de mirar la lista**: si el caso no trae ninguno descartado por presupuesto, se pone roja. **Se la vio
morder:** rompiendo la sombra para que enseñara también las filas que no son `BID`, se pusieron rojas
2 de 7; al restaurarla, 7 de 7. Después se añadió la del que ya tiene puja viva. Las otras vigilan que la ventana sea `plan_del_reset` sin quitar ni
añadir nada (se compara la respuesta **entera**), que un candado que no es la hora no dé pujas, que el
módulo no haga ninguna cuenta de puja, que diga lo que no cubre, y que no toque disco, red ni reloj.

Sustituye a `test_la_sombra_de_la_moneda_v1`, que vigilaba la reconstrucción que ya no existe. **La
verja sigue en 184**: sale una y entra otra.

---

## 3. El embudo

[embudo.py](src/analysis/embudo.py), reescrito con el orden en que corre el código (el mismo del censo
de esta tarde):

| fallo | antes | ahora |
|---|---|---|
| 1. rivales | contados con los del Computer | **aparte**: cuántos son y cuántos pasarían con la puerta abierta |
| 2. lo desconocido | `RENDIMIENTO_INSUFICIENTE`, `PROBABILIDAD_INSUFICIENTE` y `MERCADO_DE_RIVAL` caían en **VIVE** | cada uno en su puerta; lo que no conoce sale como **`DESCONOCIDA`**, y **nunca** como vivo |
| 3. `SIN_VALOR` | todo era «no mejora el once» | **la puerta decisiva**: `REGLA_1/2/3` si con la compuerta abierta habría tenido valor, `SIN_VALOR` si ni así |

Y la última línea: **«Hoy se puede pujar por N.»** Con un cero si es cero.

**Contra las fotos:**

| foto | tablero `biddable` | embudo viejo «VIVE» | **embudo nuevo** | donde más mueren |
|---|---|---|---|---|
| 14/09 | 0 | 49 | **0** · 44 rivales aparte | regla 2 (9) · rendimiento (5) · precio (4) |
| 18/09 | 2 | 40 | **2** · 34 rivales aparte | regla 2 (9) · precio (3) · rendimiento (3) |
| 23/09 | 0 | 19 | **0** · 17 rivales, pasaría 1 | **regla 2 (13 de 20)** · no compensa (5) |
| 25/09 | 0 | — | **0** · 38 rivales aparte | **regla 2 (11 de 20)** · rendimiento (5) |

Cuadra puerta a puerta con el censo de esta tarde: la regla 2 suma 9 + 9 + 13 = 31, y
`RENDIMIENTO_INSUFICIENTE` 5 + 3 + 2 = 10. **Guardias nuevas** en `test_doctrina_v1`: una con las tres
trampas (un rival, dos decisiones que el viejo no conocía y una inventada), otra que exige «0» con un
cero, y otra que exige que la compuerta no se esconda, incluido un `NO_DISPONIBLE` escrito encima de
un `SIN_VALOR`.

**Una guardia vieja ha cambiado, y lo digo:** `test_el_embudo_señala_la_causa_mayor_no_la_primera`
exigía que `SIN_VALOR` se llamara `NO_MEJORA_EL_ONCE`, que era justo el fallo 3. La regla que protege
(el titular cita la causa **mayor**) sigue igual; solo cambia el nombre.

---

## 4. Verja y paso 0

- **Verja:** 184/184 en verde, con los **cinco** interruptores de producción, a fichero y con el árbol
  quieto.
- **Paso 0:** no hay interruptor nuevo, pero lo he corrido porque ha cambiado código que leen los
  interruptores. **La primera vez salió ROJO, y la culpa era mía, de esta tarde:**

  ```
  FALLA test_ningun_interruptor_se_lee_al_importarse: ... BORDALAS_LA_MONEDA_DE_LA_LIGA en
  scripts/la_moneda_contra_las_fotos.py; BORDALAS_TOPE_DEL_ONCE en scripts/la_moneda_contra_las_fotos.py
  ```

  Ese script (el del contrafactual de la moneda, **ya en `main`**) quitaba dos interruptores del
  entorno **a nivel de módulo**. Lo escribí **después** de correr el paso 0 de la moneda, así que el
  «PASADO» que se commiteó con él no lo cubría. La verja normal no ejecuta esa guardia (solo la
  ejecuta el paso 0), y por eso producción no se ha enterado. **No cambia ninguna decisión: es un
  script de medición.** Arreglado aquí: la limpieza pasa a `main()`, y el script da los mismos
  números. El paso 0 vuelto a correr, y el registro `config/paso_0.json`, van en este commit.

  **La lección, para no repetirla: el paso 0 se corre con el árbol ya terminado, no antes del último
  fichero.**

---

## 5. Lo que no hice, y por qué

- **Ni una escritura contra Biwenger.** Pero una cosa que he visto y no es mía: la guardia
  `test_el_ciclo_publica_v1` monta el panel entero **y se conecta a Biwenger para leer** con las
  credenciales del `.env` de la raíz (lo carga `load_dotenv()` al crear el cliente). No escribe, pero
  choca con «ninguna guardia sale a la red». Ya pasaba antes de hoy. Para comprobar el panel lo he
  montado yo una vez de la misma forma.
- **No cambia ninguna decisión.** Lo quitado del tablero era un campo al lado, y la subasta usa el
  mismo estado, que antes se armaba en línea.
- **No he cubierto el carril ni BUY V10**: habría que separar la decisión de la escritura en dos
  ejecutores, y eso ya no es mirar.
- **No he tocado `la_sombra_de_la_puja`** (la de los candados levantados): contesta otra pregunta y
  lo dice.
- **No he tocado el panel de React.** El bundle es del 13/09 y no enseña la lista; la lista se ve con
  el script o en el JSON.
- No he encendido ni apagado nada, ni tocado la moneda, la elección de vía, el 3 %, el workflow ni
  ninguna constante de la lista. No he empujado.

Lo que entra en el commit: el código de §1 y §3, las dos guardias, los dos scripts y este informe.
