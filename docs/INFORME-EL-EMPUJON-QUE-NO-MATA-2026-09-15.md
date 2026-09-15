# El empujón que no mata — informe

**Rama:** `estado/el-empujon-que-no-mata` (desde `main` en `521e766`)
**Fecha:** 15/09/2026
**Verja:** 138/138 en verde, exit 0, salida a fichero (137 + la guardia nueva)
**Push:** NO.
**Escrituras contra Biwenger:** ninguna. Esto es fontanería de git.

---

## 1. Qué hace ahora si el empujón falla

**Devuelve 0 y el ciclo sigue.** Siempre: excepción incluida. Lo que no hace es
callarse.

Éste es el log literal de una vuelta con el empujón rechazado, sacado de la
guardia (tres repos de mentira, sin red):

```
Cambian 3 libro(s) respecto a git:
  data/intelligence/libro_de_publicacion.jsonl
  data/intelligence/marcador.json
  data/intelligence/onces_de_la_jornada.jsonl
Commit hecho.
  El empujon 1 de 3 no salio: ! [remote rejected] main -> main (pre-receive hook declined)
  El empujon 2 de 3 no salio: ! [remote rejected] main -> main (pre-receive hook declined)
  El empujon 3 de 3 no salio: ! [remote rejected] main -> main (pre-receive hook declined)

============================================================
 LOS LIBROS NO SE HAN GUARDADO EN GIT
============================================================
 El empujon no salio en 3 intentos. Ultimo motivo de git: remote: rechazado ...
 ! [remote rejected] main -> main (pre-receive hook declined)
error: failed to push some refs to '...'
 El ciclo NO se para por esto: el commit queda en local y
 la vuelta siguiente lo lleva. Pero si esto se repite, los
 libros vuelven a vivir solo en la cache.
============================================================
```

`exit 0`. Y el estado que queda publicado:

```json
{
 "libros_en_disco": 3,
 "libros_cambiados": 3,
 "commit": true,
 "empujado": false,
 "intentos": 3,
 "origen_avanzo": 0,
 "ok": false,
 "motivo": "El empujon no salio en 3 intentos. Ultimo motivo de git: ...",
 "ultimo_guardado_ok": null
}
```

Tres cosas que merecen señalarse:

1. **`commit: true`.** El commit se queda hecho en local, que es exactamente por
   lo que no se pierde nada: la vuelta siguiente lo lleva junto con lo suyo.
2. **El motivo es la frase de git entera**, no un resumen. Y no se reescribe en
   ningún sitio: la pantalla la copia tal cual.
3. **Por intento se imprime la línea del `!`, no la última.** Git termina siempre
   con `error: failed to push some refs`, que es la menos útil de todas; con la
   última línea, los tres intentos imprimían tres veces la misma frase vacía. Lo
   vi al sacar este log para el informe.

La guardia exige las dos cosas —`exit 0` **y** motivo no vacío— porque un fallo
callado es peor que un fallo:

```
test_un_empujon_fallido_no_tumba_el_ciclo
    devolviendo 1 -> roja
```

---

## 2. Quién gana si los dos lados han tocado el mismo libro

**Gana el disco del runner.** Y lo importante es *por qué*: **no es una decisión
que se tome al empujar. Ya estaba tomada veinte minutos antes**, por el orden de
los pasos del job:

```
paso 1   Checkout                  trae lo que hay en git
paso 2   Restore Bordalas state    descomprime la caché ENCIMA
...
paso N   Guardar los libros        <- aquí ya no hay nada que decidir
```

Cuando el guardado corre, **el disco ya es la caché**. Lo que hubiera en git para
ese libro se pisó en el paso 2. Cualquier política que eligiera "git" aquí estaría
eligiendo un contenido que ya no existe en ninguna parte.

Y además es lo correcto en el caso normal: **los libros se acumulan**. La copia del
disco es la del último guardado *más* lo que ha escrito esta vuelta; la de git es
la del último guardado a secas. El disco es un superconjunto, no una alternativa.

El caso concurrente está cerrado por el propio workflow: `concurrency:
cancel-in-progress: false` hace cola, así que dos vueltas no se solapan.

### Dónde muerde esto, dicho claro

**Si editas un libro a mano y lo empujas, la vuelta siguiente lo va a
sobrescribir.** No por este cambio —el restore de la caché ya lo pisaba— pero sí
con una diferencia que te afecta: **antes el empujón fallaba y se notaba; ahora no
falla.**

Por eso cada vuelta **imprime qué libros cambia respecto al remoto**. Es la línea
`Cambian N libro(s) respecto a git:` del log de arriba, con los nombres. Una
sobrescritura queda en el log del run, no en silencio. La guardia lo exige:

```
test_gana_el_disco_del_runner
    ... y comprueba además que el libro pisado sale en el log
```

Si algún día hace falta editar un libro a mano de verdad, el sitio donde hay que
arreglarlo es el orden de los pasos o la caché, no aquí.

### Lo que NO se pisa

Un libro que **el remoto tiene y el runner no** sobrevive. Sólo se añaden los
libros que existen en disco; el resto se queda tal cual venía, porque nunca se
escenifica un borrado. Tiene guardia propia:
`test_un_libro_que_solo_tiene_el_remoto_no_se_borra`.

---

## 3. Cómo se trae lo de fuera: `reset --mixed`, no rebase

```
git fetch origin <rama>
git reset --mixed FETCH_HEAD     <- NO TOCA EL DISCO
git add -- <los libros>
git commit
```

`reset --mixed` mueve HEAD y el índice y **deja el directorio de trabajo
intacto**. Los libros que el ciclo acaba de escribir siguen donde estaban y se
vuelven a añadir encima de lo que venga de fuera. El commit que sale tiene el
contenido del disco y **no hay ningún conflicto que resolver**.

**Por qué no `pull --rebase`:** en un rebase, `--ours` y `--theirs` están
invertidos respecto a lo que cualquiera espera, y resolver a ciegas un conflicto
dentro de un fichero de 960 KB escrito por una máquina no es algo que deba pasar a
las tres de la mañana en un runner. Aquí no hace falta: se sabe quién gana.

Y un detalle de orden que costaría un commit espurio al día: **la pregunta "¿ha
cambiado algo?" se hace DESPUÉS de traer**, contra lo que va a ser el padre del
commit. Hecha antes, se commitearía por un cambio que el remoto ya trae.

El log de una carrera real —el dueño empuja en medio y además toca el mismo
libro—:

```
El remoto se ha movido 1 commit(s) por debajo: se ponen los libros del disco encima.
Cambian 3 libro(s) respecto a git:
  data/intelligence/libro_de_publicacion.jsonl
  data/intelligence/marcador.json
  data/intelligence/onces_de_la_jornada.jsonl
Commit hecho.
Empujado a `main` (intento 1 de 3).
```

Resultado en el remoto: el commit del dueño **sigue estando**, y el libro
disputado se queda con la versión del runner.

Si HEAD quedara suelto (sin rama) no se empuja a ciegas: se dice y se sigue.

---

## 4. Cuántos reintentos y con qué espera

```
INTENTOS = 3
ESPERAS  = (3, 9)     segundos
```

**Tres intentos, esperas de 3 y 9 segundos. Peor caso: 12 segundos de vuelta.**

Cortas a propósito. Lo que falla aquí es una **carrera** —alguien empujó entre
nuestro `fetch` y nuestro `push`— y eso se resuelve en segundos, no en minutos. El
ciclo tiene presupuesto de tiempo y un seguro no puede comerse la vuelta.

**Cada reintento vuelve a traer lo de fuera.** Reintentar el mismo commit
rechazado lo único que consigue es que lo rechacen otra vez. Y si tras traer no
queda nada que añadir —porque el remoto ya trae lo nuestro—, se para y se dice, sin
crear un commit vacío.

Las esperas de producción **no se prueban durmiendo**: la guardia las fuerza a cero
con `--espera 0` y comprueba aparte, leyendo la constante, que hay una espera por
hueco entre intentos, que crecen, que ninguna es cero y que la suma no se come la
vuelta. `--espera` existe sólo para eso; la línea del workflow no lo pasa.

---

## 5. La línea de la pantalla, tal cual se verá

En **AUDITORÍA**, dentro del cuadro ESTE CICLO:

```
Libros guardados         hace 12 min · 12 libros · en git
```

y cuando el empujón se atasca:

```
Libros guardados         hace 3 h · 12 libros · el empujón falla desde entonces
```

seguido, debajo, del motivo de git entero.

Sin fichero de estado —caché desalojada, o primera vuelta—:

```
Libros guardados         SIN DATO
```

**La edad se mide desde el último guardado que LLEGÓ A GIT**, no desde la última
vez que el script corrió: correr y no conseguir empujar es exactamente el fallo que
hay que ver.

### Y además grita: es el noveno sentido

La línea de AUDITORÍA es para mirar. Lo que hace que alguien se levante es la
alarma, así que el guardado entra también en LOS SENTIDOS DE PEPE, que ya sube a la
banda de arriba y al registro de actividad.

**Ésta es la parte que paga el arreglo nº 2.** Antes un empujón fallido se veía
porque la vuelta salía roja. Ahora la vuelta sale verde —que es lo correcto— y por
eso hace falta un sitio donde se vea que lleva una semana fallando. Sin esto
volvemos a donde estábamos la mañana del 14, y esta vez sin saberlo.

**El tope no es un número redondo.** El hueco más largo entre dos disparos
declarados en `config/disparos.json` es la ventana del reset —**145 min**, de las
04:50 a las 07:15 de Madrid; los demás son de 60 min o menos—. El tope son **dos
huecos seguidos**, redondeados hacia arriba a **5 h**: uno puede ser una vuelta que
no salió o una carrera perdida; dos seguidos es que no vuelve. Se redondea hacia
arriba para no gritar por diez minutos de margen.

Y no se queda escrito a mano: `test_el_tope_de_los_libros_sale_de_los_disparos`
**recalcula los 145 minutos desde el fichero** —vuelta de la medianoche incluida— y
salta el día que alguien cambie el latido y se olvide de esto.

### La frase se monta en un solo sitio

`los_sentidos.py`. La pantalla no compone su propia versión, y hay guardia que lo
comprueba: si el JSX escribiera `"en git"` o `"el empujón falla"` por su cuenta, la
guardia se pone roja. Habría dos verdades y el día que discreparan nadie sabría
cuál mirar.

### El estado no es un libro

Cambia en cada vuelta; como libro serían 8.400 commits al año, que es justo lo que
este script existe para no hacer. Vive en `data/autopilot/`, que **sí** está en las
rutas que el workflow mete en la caché, así que sobrevive de una vuelta a la
siguiente. Si la caché se desaloja, desaparece y la línea dice SIN DATO — que es la
verdad, no un cero. Guardia: `test_el_estado_no_es_un_libro`.

**De propina:** la edad por debajo de la hora ya dice los minutos. Decía "de hace un
rato", que para los otros ocho sentidos da igual —ninguno se refresca tan rápido—
pero no distingue una vuelta de hace diez minutos de una de hace cincuenta.

---

## 6. Las guardias

**Corren sobre tres repos de mentira** en un directorio temporal: un remoto pelado,
el runner y "el dueño". Sin red: `origin` es una ruta del disco. Sin reloj: las
esperas se fuerzan a cero.

Y el rechazo **no se simula con un remoto roto** —eso probaría el fallo del
`fetch`, que es otro camino— sino con un gancho `pre-receive` que dice que no, que
es exactamente lo que hace GitHub cuando te ganan la carrera: acepta el `fetch` y
rechaza el `push`.

| guardia | qué pasa si se rompe |
|---|---|
| `test_un_empujon_fallido_no_tumba_el_ciclo` | una vuelta entera en rojo por un seguro que no pudo guardar |
| `test_se_trae_lo_de_fuera_y_no_se_pierde` | se pierde el commit del dueño, o el empujón vuelve a chocar |
| `test_gana_el_disco_del_runner` | un libro tocado por los dos lados bloquea el empujón, o lo pisa en silencio |
| `test_un_libro_que_solo_tiene_el_remoto_no_se_borra` | el ciclo borra de git un libro que él no escribió |
| `test_se_reintenta_y_se_dice_cuantas_veces` | se queda en un intento y nadie se entera |
| `test_las_esperas_son_las_declaradas` | esperas a cero, o tan largas que se comen la vuelta |
| `test_sin_empujar_no_se_toca_el_remoto` | probarlo a mano publica algo |
| `test_el_estado_no_es_un_libro` | 8.400 commits al año |
| `test_si_los_libros_no_se_guardan_se_grita` | el empujón lleva una semana fallando y la pantalla calla |
| `test_el_tope_de_los_libros_sale_de_los_disparos` | el tope se convierte en un número puesto a ojo |
| `test_el_montaje_trae_libros_y_empuja_de_verdad` | **regla 24**: las demás se ponen verdes sin ejercitar nada |

**Las tres importantes, probadas reintroduciendo el fallo:**

```
devolver 1 en el empujón fallido   -> test_un_empujon_fallido_no_tumba_el_ciclo   ROJA
quitar el fetch previo             -> test_se_trae_lo_de_fuera_y_no_se_pierde     ROJA
subir el tope a 24 h               -> test_si_los_libros_no_se_guardan_se_grita   ROJA
```

### Tres cosas que me cazaron escribiendo esto

1. **El montaje mentía.** `git init --bare` deja `HEAD` apuntando a la rama por
   defecto de quien ejecuta —`master` en esta máquina—, así que `git clone` dejaba
   al "dueño" en una rama huérfana distinta: sus commits se iban a `master`, el
   runner no los veía nunca y **dos pruebas pasaban sin haber probado nada**. Ahora
   `test_el_montaje_trae_libros_y_empuja_de_verdad` comprueba además que el
   empujón del dueño **mueve la rama del remoto**.

2. **`test_los_sentidos_no_se_inventan_la_edad`**, por un "se desaloja a los 7
   días" escrito a mano en el texto del sentido nuevo. Tenía razón aunque el 7 sea
   una política de GitHub y no una edad: ese dato vive en `los_libros.py`, que es
   donde se declara qué es un libro.

3. **`test_ninguna_guardia_de_la_verja_lee_el_estado`**, por un literal
   `data/autopilot/...` en la guardia nueva. La ruta se le pregunta ahora al
   guardador, que es quien la declara — igual que los libros de prueba salen de
   `rutas()`.

---

## 7. Lo que no hice, y por qué

- **No toqué `.github/workflows/bordalas-live.yml`.** Y no hace falta: el paso
  `Guardar los libros` y el `contents: write` ya están puestos y funcionan. Todo
  esto vive dentro del script al que ese paso llama, así que **no hay nada que
  pegar**.
- **Ni una escritura contra Biwenger.** Ni una puja, ni una oferta, ni una venta.
- **Ningún umbral tocado**: ni cupo, ni suelo, ni tope, ni `bid_cap`, ni las cinco
  de `PUEDEN_ENCERRARLO`, ni `MAX_SINGLE_SPECULATION_PERCENT`, ni `MAX_SAFE_DEBT`.
  Las 5 h del sentido nuevo no son un umbral del motor: no cierran ninguna vía,
  sólo encienden un aviso, y salen calculadas de `config/disparos.json`.
- **No empujé.** La rama está local, con un commit.
- **No arreglé la sobrescritura de una edición a mano.** Se puede notar, y se nota
  (§2), pero arreglarla de verdad significa tocar el orden `checkout` / `Restore
  state` del workflow, que es tuyo y además no es lo que pedía el encargo. Queda
  descrito arriba.
- **No hice que el fallo del empujón se reintente en la vuelta siguiente de forma
  especial.** No hace falta: el commit queda en local y la vuelta siguiente lo
  lleva con lo suyo por el camino normal. La guardia comprueba que queda pendiente.

### Una nota sobre la rama

`main` local iba **2 commits por detrás** de `origin/main`, y esos dos son los
commits de libros que escribió el propio ciclo (`4faec3d` con 12 libros y
`e9d1035` con 5). No me puse encima de ellos: traen ficheros de `data/` que en este
disco existen sin trackear, y un `checkout` habría pisado los libros locales — que
es exactamente el error contra el que va este encargo. **Ningún fichero de código
difiere entre las dos puntas**, así que la rama sale de `521e766` y mezcla limpia.
