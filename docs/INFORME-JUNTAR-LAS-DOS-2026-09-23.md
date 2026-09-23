# Juntar las dos, y el pronóstico que llega tarde

**Encargo:** «JUNTAR LAS DOS, Y EL PRONÓSTICO QUE LLEGA TARDE», 23/09/2026
**Rama:** `main`, local. **Sin empujar.**
**Fecha:** 23/09/2026, mañana

---

## Bloque 1 — las dos, juntadas

```
3b34ffc paso 0 sobre las dos ramas juntadas: 29 interruptores
02c16be merge: arreglo/el-que-va-a-despegar en main
4edf6cd merge: encender/a-quien-y-cuanto en main
27486fc libros: ...                                   <- origin/main al empezar
```

Antes de empezar, `git pull --no-rebase` sobre `main`: entraron dos commits `libros:` del
ciclo. `main` queda **12 commits por delante de `origin/main`**.

### Qué chocó y cómo se resolvió

| merge | conflictos | resolución |
|---|---|---|
| 1º `encender/a-quien-y-cuanto` | **ninguno** | git la juntó sola; no toca `data/` |
| 2º `arreglo/el-que-va-a-despegar` | **uno: `config/paso_0.json`** | ver abajo |

- **`config/paso_0.json`**: los dos lados traían su propio paso 0, con fecha, segundos y huella
  distintos. **La lista de probados git ya la había juntado bien**: 29 nombres, con
  `BORDALAS_SOLVENCIA_POR_SU_PLAZO`. Me quedé con el lado más reciente, y el paso 0 corrido
  después lo ha reescrito sobre el árbol juntado.
- **`dashboard_state.py` y la lista de la verja**, que ayer avisé que chocarían: **git los juntó
  sin conflicto**. Mi aviso de ayer estaba mal. Comprobado a mano que la lista lleva las **seis**
  guardias nuevas de las dos ramas, una vez cada una: `test_la_verja_corre_como_ci_v1`,
  `test_la_sombra_de_la_moneda_v1`, `test_el_plazo_sale_del_calendario_v1`,
  `test_el_que_va_a_despegar_v1`, `test_la_sombra_de_la_puja_v1` y
  `test_el_libro_de_la_valoracion_v1`.
- **En `data/` no chocó nada**: ninguna de las dos ramas traía libros.

### La verja después de cada merge

Las dos a fichero (`verja-merge-1.txt`, `verja-merge-2.txt`), antes de firmar cada merge, con el
árbol quieto. La cabecera lo dice ella sola, porque desde el primer merge la verja se lee el
workflow:

```
corriendo con 2 interruptores de produccion: BORDALAS_JORNADAS_POR_SU_FECHA, BORDALAS_REVENTA_SOLO_SI_JUEGA
```

| después de | guardias | resultado |
|---|---|---|
| merge 1 | 179 | **179 en verde, código 0** |
| merge 2 | 183 (177 + 2 + 4) | **183 en verde, código 0** |

Ninguna rama puso la verja en rojo.

### Libros sucios después de una verja completa: 0

| | libros versionados que `git status data/` da por modificados |
|---|---|
| ayer, sin la guardia de las copias | **4** (`libro_de_publicacion`, `marcador`, `board_events`, `bitacora_del_saldo`) |
| hoy, verja completa tras el merge 1 | **0** |
| hoy, verja completa tras el merge 2 | **0** |
| hoy, paso 0 completo | **0** |

Queda un matiz que ya contó el informe de ayer: cinco guardias reescriben tres ficheros **con el
mismo contenido**. Eso cambia la hora del fichero pero no sus bytes, y `git status` no lo ve.
Ese riesgo sigue callado, pero hoy no ensucia nada.

Los dos libros nuevos, el de aciertos y la foto por jornada, **no los ha escrito ninguna verja**:
siguen sin existir en disco. Solo se escriben con la foto del día de mercado en curso.

### Interruptores, antes y después, y el paso 0

```
EL PASO 0 HA TARDADO 221 s (3.7 min).
PASADO. Quedan probados 29 interruptores, apuntados en config/paso_0.json.
```

**29 antes y 29 después, y es la misma lista.** No se ha añadido ninguno, no se ha encendido
ninguno, y ningún nombre inventado se ha colado. El workflow sigue encendiendo los mismos dos.

---

## Bloque 2 — ¿llega tarde el pronóstico de titularidad?

### El histórico del pronóstico de titularidad no se guarda.

Solo existe el de nuestra plantilla, y está roto. Me paro aquí, como pide el encargo: no hay
retraso que medir, ni mediana, ni control. No he reconstruido nada a ojo.

Esto es un «no lo sabemos» y no un «no lo hemos preguntado». El dato se pidió cada vuelta y se
tiró en la vuelta siguiente.

### De dónde sale el pronóstico, fuente por fuente

| fuente | ¿alimenta la regla de «¿va a jugar?»? | ¿guarda histórico? |
|---|---|---|
| **FutbolFantasy** | **sí, y es la única desde el 17/08**. `candidate_starter_lookup.build_starter_lookup` lee `BOARD_FILE`, que es `data/intelligence/futbolfantasy_board.json` ([candidate_starter_lookup.py:51](src/analysis/candidate_starter_lookup.py#L51)), y pasa la `starter_probability` de FF «tal cual». El tablero la copia desde `valoracion["starter"]["probability"]` ([acquisition_board.py:935](src/analysis/acquisition_board.py#L935)) | **no**. `futbolfantasy_provider` reescribe el fichero entero cada vuelta ([futbolfantasy_provider.py:1721-1723](src/intelligence/futbolfantasy_provider.py#L1721-L1723)), y el fichero no está en git |
| **Jornada Perfecta** | **no**. Retirada el 17/08 junto con el consenso multifuente (cabecera de `candidate_starter_lookup.py`) | no |
| **la prensa** | **no es fuente de titularidad**. `press_report.json` da noticias con dirección, y ningún lector la usa como probabilidad | no |

Así que la sospecha de que una fuente llega al día y otra tarde **no aplica hoy**: el
pronóstico que tumba a Ceballos sale de una sola fuente.

### Lo que sí hay guardado, y por qué no sirve

1. **`data/intelligence/source_accuracy_ledger.json`**: un pronóstico por jornada y por fuente,
   pero **solo de nuestra plantilla**. Son 14–16 jugadores por jornada, en las jornadas 1, 2, 3,
   4, 5, 7 y 8. Además está **roto como prueba**, por dos cosas:
   - el pronóstico de cada jugador es **idéntico de J2 a J8**. Por ejemplo, Yamal tiene
     `FUTBOLFANTASY 60 / ANALITICA_FANTASY 70` en todas las jornadas;
   - el resultado sale **«no jugó» para todos en todas las jornadas**, Yamal incluido.
     `appearances_before == appearances_after` siempre, porque el resultado se puntúa con la
     misma foto en la que se hizo el pronóstico.

   Casos utilizables: **n = 0**.
2. **`data/trading/libro_del_escaparate.jsonl`**: guarda la `starter_probability` de los veinte
   del Computer de cada día, **desde el 17/09**. Son 7 líneas, 81 jugadores distintos, y 43 de
   ellos vistos dos o más días. Solo cubre **una jornada (J7)**, y un retraso «de dos o tres
   jornadas» no se mide con una.
3. **Los minutos**: Biwenger no los da, solo partidos jugados y puntos. FF sí trae `minutes`
   (141 de 143 filas hoy), pero son **los de hoy**, en un fichero que se pisa.

### Lo que haría falta para contestarla, propuesto y no construido

Un libro más en `los_libros`: una línea por día de mercado con `{id: [probabilidad FF,
jerarquía, minutos FF]}` de las ~143 filas del tablero de FF. Con el mismo formato compacto que
la foto por jornada debería ocupar del orden de **~5 KB/día**. Es una estimación, no una medida.
Con 3–4 jornadas de libro se podría contestar la pregunta con su `n` y su control.

No lo he construido: el encargo dice que este bloque es una medición, y con el dato ausente toca
parar. Tampoco propongo el arreglo de «mirar minutos en vez de pronóstico», porque su condición
era que el retraso existiera, y **no se sabe**.

---

## Lo que no he hecho, y por qué

| no hecho | por qué |
|---|---|
| **Empujar** | tú empujas. `main` va 12 commits por delante de `origin/main`; antes de empujar hace falta otro `git pull --no-rebase`, porque el ciclo sigue escribiendo libros |
| **Medir el retraso** | **el histórico del pronóstico de titularidad no se guarda** |
| **Construir el libro del pronóstico** | el bloque 2 era una medición. Queda propuesto arriba |
| **Arreglar `source_accuracy_ledger`** | queda diagnosticado: pronóstico congelado desde J2, y el resultado se puntúa con la foto del pronóstico. No era de este encargo |
| **Encender nada** | ningún interruptor, tampoco `BORDALAS_SOLVENCIA_POR_SU_PLAZO` |
| **Tocar la regla de «¿va a jugar?», la valoración o la marca «va a despegar»** | prohibido por el encargo |
| **Tocar el workflow y los números prohibidos** | intactos |
| **Juntar o borrar las ramas viejas** | prohibido por el encargo. `encender/a-quien-y-cuanto` y `arreglo/el-que-va-a-despegar` siguen existiendo, ya fusionadas |
| **Larrubia, y los cinco ficheros de las ramas viejas** | apuntados, sin mirar, como pide el encargo |
