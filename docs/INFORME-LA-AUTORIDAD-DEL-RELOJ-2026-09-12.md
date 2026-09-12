# La autoridad del reloj ya no vive en el repositorio

**12/09/2026** · verja 112/112 · sin push

---

## Cuál de las seis fallaba

`test_la_cadencia_sale_del_cron`. Reproducido en local con tu versión del YAML:

```
FALLA test_la_cadencia_sale_del_cron:
      el workflow no declara ningun `cron`
```

Era exactamente lo que suponías. Y el log sólo enseña las que pasan porque `main()`
imprime `OK` por cada una y el `FALLA` va al mismo sitio — en CI se truncaba.

---

## 1. La declaración, en un sitio y como dato

`config/disparos.json`:

```json
"latido":    { "minuto": 7, "horas": [0,1,2,3,8..23], "cron": "7 0-3,8-23 * * *" }
"puntuales": [ "04:45 ventana", "04:50 ventana", "07:15 tras_el_reset" ]
"zona": "Europe/Madrid"   "gracia_minutos": 12
```

**23 disparos al día** — 20 latidos y 3 puntuales. Todo en hora de pared de Madrid:
ya no queda nada en UTC, porque el único que lo estaba era el cron de GitHub.

Y no es un espejo más: **`relojes.js` importa ese mismo fichero**
(`import DISPAROS from "../../../config/disparos.json"`), y `dashboard_state.py` lo
lee por `src/analysis/los_disparos.py`. Ya no hay dos copias que puedan discrepar,
que es lo que pasó en septiembre con la cadencia escrita a mano en tres sitios.

`CRON_INTERNO` ha desaparecido de las dos casas. `CADENCIA_MINUTOS` ya no es un
número: sale de la declaración, y si no se pudiera leer vale `None` y los textos
dicen «a intervalos desconocidos» en vez de inventarse una cadencia.

---

## 2. La guardia, contra la declaración

`test_la_cadencia_sale_de_la_declaracion` — y comprueba menos cosas que antes
**a propósito**: lo que se importa no hace falta vigilarlo. Lo que sí vigila es que
nadie vuelva a copiarlo:

- que `relojes.js` siga **importando** el fichero y no lleve ninguna hora escrita
- que `dashboard_state.py` no vuelva a tener `CADENCIA_MINUTOS = <número>`
- que la declaración dé 23 disparos y una cadencia entre 1 y 1440

---

## 3. Por qué se quitó, escrito donde se va a leer

En la cabecera del propio `bordalas-live.yml`, en `los_disparos.py` y en
`relojes.js`:

> **Se retiró el 12/09/2026, y no por simplificar: se saltaba vueltas todos los
> días. Llegaba 30-40 minutos tarde y perdía ciclos enteros.** Los `schedule` de
> Actions no son una promesa: son una cola de baja prioridad. Con una vuelta por
> hora, 30-40 minutos tarde no es «un poco tarde» — es la vuelta perdida.
>
> Si abres el fichero, ves sólo `workflow_dispatch` y piensas «le falta el cron»:
> esto es lo que te falta saber. **Que nadie lo vuelva a poner sin saber por qué se
> quitó.**

Y hay guardia: `test_el_schedule_de_github_no_vuelve_sin_saber_por_que` se pone roja
si vuelve a aparecer un `schedule`, y obliga a que la fecha, el retraso medido y
`cron-job.org` sigan escritos en el workflow.

---

## 4. La alarma: sigue funcionando, y la he ejecutado

Siete casos contra la declaración nueva:

| foto del ciclo | |
|---|---|
| 04:47 Madrid (ventana 04:45) | en hora, **callado** |
| 07:18 Madrid (tras reset 07:15) | en hora, **callado** |
| 09:09 Madrid (latido 09:07) | en hora, **callado** |
| 03:46 Madrid | **AVISA** · 39 min · esperado 03:07 |
| **05:30 Madrid — dentro de la ventana** | **AVISA** · 40 min · esperado 04:50 |
| **06:40 Madrid — dentro de la ventana** | **AVISA** · 35 min · esperado 07:15 |
| 12:41 Madrid | **AVISA** · 26 min · esperado 13:07 |

Los dos casos en negrita son la forma que tendría un cron-job.org descolocado: un
ciclo entrando dentro de la ventana del reset, donde no hay ningún disparo
declarado. **Los caza.** Está en la guardia, ejecutada con `node`, no sólo
comprobada por lectura.

Y no diagnostica la causa — enseña la hora a la que entró, la que tocaba y la
diferencia. Eso sigue igual, y sigue siendo deliberado.

**Lo que esa alarma no puede hacer, y conviene decirlo:** no comprueba que
cron-job.org esté vivo. Si el servicio se parase del todo, no entraría ningún ciclo
— y una alarma que vive dentro de la pantalla que publica el ciclo no se
actualizaría tampoco. Lo que se vería es la foto envejeciendo y la cuenta atrás en
«debería haber entrado hace X». Eso funciona, pero hay que estar mirando.

---

## Una consecuencia del cambio que no me pediste y que tienes que saber

**La zona de silencio se ha quedado sin forma de distinguir quién dispara.**

Mientras existió el `schedule`, `permite_escribir` separaba el latido (no escribe en
la ventana del reset) de los disparos deliberados. Ahora **todo entra como
`workflow_dispatch`**, que está en `DISPAROS_DELIBERADOS`. Comprobado:

```
05:30 Madrid, dentro de la ventana del reset
  schedule              -> escribe False   deliberado False
  workflow_dispatch     -> escribe True    deliberado True    <- ahora todos
  repository_dispatch   -> escribe True    deliberado True
```

En funcionamiento normal no cambia nada: el latido salta las horas 4-7, así que
nunca cae dentro de la ventana. **El agujero es en el modo de fallo** — si
cron-job.org se descolocara y lanzara un latido a las 05:30, antes lo habría
frenado la zona de silencio y ahora lo dejaría escribir con el mercado sin
resetear. Que es exactamente lo que costó la primera ventana en septiembre.

**El arreglo está disponible y es corto**, porque la declaración ya lo sabe:
`que_disparo_toca(minutos_de_madrid)` devuelve la clase —`ventana`,
`tras_el_reset`, `latido`— deducida de **la hora**, que es lo único que sigue
distinguiéndolos. La zona de silencio pasaría a tratar como deliberado sólo lo que
la declaración dice que es `ventana`.

**No lo he tocado.** Cambia cuándo escribe el bot, y eso lo decides tú.

---

## Guardias

`test_los_relojes_v1` — **7/7** (eran 6). La nueva es la del `schedule` retirado.
Dos reescritas: la de la cadencia, que ahora lee la declaración, y la de la
compensación falsa, que vigila la declaración en vez de `relojes.js` (los crones
sin compensar viven ahí ahora, y el rastro de por qué la teoría era falsa sigue
donde estaba).

---

## Estado

- Verja: **112/112**
- `config/disparos.json` es la autoridad; `relojes.js` la importa, Python la lee
- Pantalla construida y desplegada
- Rama `main`, **sin push** — y ojo: `origin/main` ha avanzado dos commits tuyos
  (`a85155b`, `39f238c`) que no están en mi rama. El merge es tuyo.
