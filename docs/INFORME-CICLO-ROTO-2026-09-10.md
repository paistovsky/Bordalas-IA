# El ciclo roto — NameError en build_dashboard_state

**10/09/2026** · verja 108/108 · sin push

---

## La pregunta primero: NO llega roto a actuar

El orden de [bordalas-live.yml](.github/workflows/bordalas-live.yml) es:

| paso | línea | |
|---|---|---|
| 1. verja | 131 | `run_validation_gate.py` |
| 2. **Pepe actúa** | 136 | `src.v10_full_autonomous_live` — **puja y renueva aquí** |
| 3. la pantalla | 141 | `src.telemetry.build_dashboard` — **aquí reventaba** |

**Mañana a las 04:45, con esto roto, Pepe habría pujado y renovado igual.**
Sólo nos quedábamos sin pantalla. La ventana no se perdía.

Aun así lo he arreglado esta noche, porque hay un efecto de segundo orden que no
me gusta: el paso que reventaba deja el **job en fallo**, y el estado (`data/`,
con los libros de renovación y de pujas) se guarda con `actions/cache`, cuyo
guardado en el post-job **no es fiable cuando el job falla**. En el peor caso el
ciclo siguiente restauraría una caché anterior y volvería a renovar lo ya
renovado. No lo he podido confirmar sin provocar un fallo en Actions, así que lo
dejo escrito como sospecha, no como hecho.

---

## 1. Qué era, y el camino arreglado

Regresión mía, del commit `c21953e`. Al sacar `compact_lineup` a una variable
—para que `lineup` y `posibles_cambios` contaran lo mismo— mi script buscó hacia
atrás el `return {` más cercano y **acertó el de otra función**:

```
compact_ledger_audit(audit)      ← la definición aterrizó AQUÍ
      ...   state, snapshot y photo_lookup ni existen en esa función
build_dashboard_state()          ← y aquí se usaba el nombre. L4609
```

Y tenías razón en el diagnóstico, sólo que la rama era otra: no es que
`lineup_payload` se definiera en una rama, es que **la definición se fue a otra
función entera**. Con mi prueba de la cadena no salió porque probé
`compact_lineup` sola, nunca el montaje.

**No hay valor por defecto en el arreglo.** La definición se ha movido a
`build_dashboard_state`, justo al lado de `rivales_compactos`, que es el mismo
patrón (calcular una vez lo que leen dos bloques) y está después de `state`,
`snapshot` y `photo_lookup`.

De paso desaparece un segundo fallo latente: en `compact_ledger_audit` ese bloque
habría reventado con `NameError: state` en cuanto la auditoría estuviera
disponible. Estaba después del `return` temprano, así que sólo esperaba a que la
auditoría empezara a funcionar.

**Verificado ejecutando**, no leyendo: `build_dashboard_state()` monta 53 bloques
y `posibles_cambios` sale con 2 suplentes.

---

## 2. La guardia que faltaba

`src/analysis/test_el_ciclo_publica_v1.py` — **3/3**. Dos mitades:

**a) El montaje entero.** Construye `build_dashboard_state()` con la foto real que
hay en disco y falla si revienta. No comprueba ningún valor —eso ya tiene sus
guardias— sólo que **el ciclo llega al final**.

**b) Una lectura estática**, sin ejecutar nada: caza la familia entera del fallo
—un nombre usado en una función que esa función no ata en ningún sitio, ni hereda
de una que la envuelva, ni es global—. Existe porque (a) necesita una foto en
disco y en un clon recién hecho no la hay: que no se pueda montar no puede dejar
el fichero sin vigilar.

**Comprobado que caza el fallo de verdad.** Contra el fichero roto:

```
dashboard_state.py:2956 compact_ledger_audit(): `state`
dashboard_state.py:2957 compact_ledger_audit(): `snapshot`
dashboard_state.py:2958 compact_ledger_audit(): `photo_lookup`
dashboard_state.py:4609 build_dashboard_state(): `lineup_payload`
```

Los cuatro, con línea y función. Y hay un tercer test cuyo único trabajo es
**probar el detector contra un cebo**: un detector que dice «cero» puede estar
simplemente roto —el mío lo estuvo dos veces mientras lo escribía— y además tiene
que dejar pasar lo sano (el `try/except` que asigna en las dos ramas, el cierre
que lee de fuera).

**Choca con la Regla 23** (ninguna guardia lee estado externo) y su guardia me lo
paró. Declarada en `DEUDA` con su motivo, como manda esa misma regla: sin foto en
disco informa «sin muestra» y **pasa**, nunca falla.

---

## 3. El repaso: el patrón no estaba tres veces

Escribí un analizador del árbol —no un grep— con dos preguntas:

- **A. Usado y atado en ninguna parte de su función.** La forma exacta del fallo.
  **Antes del arreglo: 14. Después: 0.**
- **B. Atado sólo en algunos caminos.** 469 hits, casi todos variables de bucle
  leídas dentro del propio bucle. Demasiado ruido para ser una guardia, y el
  `try/except` que asigna en cuerpo y en todos los `except` es sano por
  construcción. **No lo convierto en guardia**: una guardia con 469 avisos no la
  lee nadie, que es el mismo final que no tenerla.

Así que el patrón **no estaba tres veces**: estaba una, y era mía. La mitad
estática de la guardia queda puesta para que la próxima no llegue a producción.

---

## Estado

- Verja: **108/108**
- Ejecutado `build_dashboard_state()` de verdad: 53 bloques, sin excepción
- Rama `main`, **sin push**
- No hace falta volver a `c21953e`
