# CUÁNTAS PETICIONES HACE PEPE, Y CÓMO BAJARLAS

Rama `peticiones/bajar-el-ritmo`, desde `main` (`a5972c7`).
**95 de 95 en verde.** Ni una llamada a Biwenger. Sin push.

---

# ANTES DE NADA: EL 429 ES CASI SEGURO MÍO

Ayer bajé **619 fichas de jugador** en unos minutos para rehacer la calibración —
una petición por jugador contra `/players/la-liga/{slug}`. Lo avisé antes de
empezar y paré en cuanto saltó el 429, pero para entonces ya estaba hecho: el
ciclo comparte cuenta.

**No es una excusa, es el dato que hace falta para dimensionar el resto**: el
ciclo normal consume 1.536 peticiones al día, y yo metí 619 más en cinco minutos.
Lo que tumbó la cuenta fue la ráfaga, no el ciclo. Pero el ciclo tampoco está
bien, y eso es lo que sigue.

---

# 1. EL RECUENTO

**32 peticiones por vuelta. 1.536 al día con el cron actual.**

**Y no es aritmética mía**: ejecuté `collect_league_snapshot()` y
`collect_board_history()` **de verdad**, contra una sesión de mentira que devuelve
payloads mínimos. Ni un byte salió a la red. Está en
`scripts/contar_peticiones_del_ciclo.py` y se puede repetir.

```
  refresh_snapshot               8
  colecta del tablon            12
  colecta del tablon (2a vez)   12   <-- duplicada
  ----------------------------------
  TOTAL POR CICLO               32

  Con cron cada 30 min (48 vueltas/dia):  1.536 al dia
```

## Endpoint por endpoint

| Peticiones/ciclo | Endpoint | De dónde sale |
|---:|---|---|
| **14** | `GET /user/{id}` | 7 managers × **2 colectas del tablón** |
| 3 | `POST /auth/login` | 1 del snapshot + 2 de las colectas |
| 3 | `GET /account` | idem (lo llama `select_league`) |
| 2 | `GET /competitions/la-liga/data` | **el catálogo, pedido dos veces** |
| 2 | `GET /league` | la lista de managers, 2 veces |
| 2 | `GET /league/{id}/board` | el tablón, 2 veces |
| 2 | `GET /user/{id}/finances` | 2 veces |
| 2 | `GET /user` | plantilla + alineación |
| 1 | `GET /market` | |
| 1 | `GET /rounds/league` | |

**Una vuelta con escritura cuesta 41**: las 32 más la escritura (1) más un
`refresh_snapshot` completo de verificación (8).

## Lo que salta a la vista

**El tablón se colecta DOS VECES por vuelta, y son 24 de las 32 peticiones.**

Y lo mejor: el código ya sabe que está mal. En `autopilot.py`, dentro de
`build_competitive_observer`, hay este comentario:

> *"Ya se construyó antes de decidir. Volver a pedir el tablón sería una segunda
> llamada de red por el mismo dato."*

**Veinte líneas más arriba, en la misma función, se hace exactamente eso.** Alguien
arregló la segunda llamada —`load_rival_intelligence` tiene caché— y dejó la
primera, que es una llamada pelada a `collect_board_history()` sin cliente: vuelve
a hacer login, vuelve a pedir la lista de managers y vuelve a pedir los siete
perfiles.

**El comentario documenta una intención que el código no cumple.** Es la misma
familia que el `raw_points` y el motivo del 3 %: una etiqueta que dice algo que no
es.

---

# 2. CÓMO BAJARLAS

## a) Lo que se puede quitar sin cachear nada, y sin perder un solo dato

| Qué | Ahorro/ciclo | Por qué es seguro |
|---|---:|---|
| **La segunda colecta del tablón** | **−12** | Es el mismo dato, segundos después. El propio código dice que no debe hacerse. |
| **El catálogo duplicado** | **−1** | `get_my_team()` ya lo pide; `collect_league_snapshot` lo vuelve a pedir con los mismos parámetros. |
| **Compartir el cliente** entre colectores | **−2** | Un login y un `/account` por vuelta, no tres. |

**32 → 17 por ciclo. 1.536 → 816 al día.** Mitad, y nadie se entera.

**No lo he tocado**: cambia lo que el observador ve dentro de una vuelta y eso es
decisión tuya. Es una tarde de trabajo con guardia.

## b) Lo que se puede cachear entre resets

El mercado del Computer cambia **una vez al día, a las 07:00** (confirmado:
`market_clock.next_reset_local = 07/09 07:00`). Hoy todo se vuelve a pedir 48
veces.

| Endpoint | Cada cuánto cambia de verdad | Hoy | Podría ser |
|---|---|---:|---:|
| `/competitions/la-liga/data` | **precios, una vez al día en el reset** | 96/día | **1-2/día** |
| `/league` (lista de managers) | casi nunca | 96/día | **1/día** |
| `/user/{id}` (plantillas rivales) | **solo cuando alguien ficha** | 672/día | **~20/día** |
| `/user/{id}/finances` | con cada movimiento | 96/día | ~24/día |
| `/market` | continuamente | 48/día | 48/día |
| `/league/{id}/board` | continuamente | 96/día | 48/día |

**La clave son los perfiles: 672 peticiones al día, el 44 % del total.** Y la
plantilla de un rival **solo cambia cuando ficha o vende — y eso lo dice el
tablón**, que cuesta UNA petición. Así que:

> Se pide el tablón. Si desde la última vez no hay movimiento de un manager, su
> perfil no se vuelve a pedir. Se refresca solo el de quien se haya movido.

Eso no pierde nada: es leer el índice antes de abrir el libro.

**Con caché: ~8 peticiones por vuelta. 1.536 → ~384 al día.**

## c) El cron

**No lo he tocado.** Hoy es:

```yaml
- cron: "7,37 * * * *"     # 48 vueltas al día
```

**Lo que yo pondría, y por qué:**

```yaml
    # Antes del reset: ver el mercado que se va, en los dos husos.
    - cron: "45 4,5 * * *"
    # El reset y la hora siguiente, que es cuando aparece todo.
    - cron: "5,20,40 5,6 * * *"
    # Una barrida por hora el resto del día: ofertas y alineación.
    - cron: "25 7-22 * * *"
```

**24 vueltas al día en vez de 48**, y concentradas donde pasan cosas.

**Tres avisos sobre esto, y el segundo importa:**

1. **El cron de GitHub Actions es UTC, no local.** El reset de las 07:00 de Madrid
   son las **05:00 UTC en verano y las 06:00 en invierno**. Por eso las dos líneas
   densas cubren `4,5` y `5,6`: para que valgan en los dos husos sin tener que
   acordarse de cambiarlas en octubre. Cuesta un par de vueltas de más y evita que
   media temporada se mire el mercado una hora antes de que exista.

2. **El cron actual no es el problema, y bajarlo tampoco es la solución.**
   48 vueltas × 32 = 1.536. 24 × 32 = 768: sigue siendo mucho. **Lo que baja el
   consumo de verdad es (a) y (b), no el cron.** Con las 8 peticiones de la caché,
   incluso 48 vueltas serían 384 al día. Si tengo que elegir una sola cosa, elijo
   quitar la colecta duplicada, no recortar vueltas.

3. **Menos vueltas cuesta reacción.** Una oferta de un rival caduca, y con una
   barrida por hora se puede llegar tarde. Por eso la barrida nocturna se queda
   horaria y no se espacia más.

## d) La idea mejor, que no es ninguna de las tres

**Separar "cada cuánto miro" de "cuánto pido".** El ciclo ya calcula
`market_clock` y ya sabe si el mercado se ha movido. Podría decidir solo:

- **Vuelta barata** (1 petición: `/market`): ¿hay ofertas nuevas? ¿ha cambiado
  algo? Si no, se acabó la vuelta.
- **Vuelta completa** (las 8): solo tras el reset, cuando el tablón se ha movido,
  o cerca del cierre de jornada.

Con eso el cron puede seguir siendo denso —que es bueno para reaccionar— y el
consumo baja igual. **Es más trabajo que (a) y (b), y no lo haría hasta tener esos
dos hechos y medidos.**

---

# 3. EL 429, ARREGLADO

Esto sí lo he implementado, porque es lo que impide reactivar el workflow con
seguridad.

## Lo que pasaba

**`main()` de `src/v10_full_autonomous_live.py` —que es lo que ejecuta el
workflow— llamaba a `run_cycle()` sin un solo `try`.** La excepción salía del
proceso, el paso de Actions se ponía rojo, y de ahí a desactivarlo a mano.

**Casi lo arreglo en el sitio equivocado.** Puse la rama primero en
`autopilot.main()`, que es el bucle largo, y solo al leer el workflow vi que el
`run:` dice `python -m src.v10_full_autonomous_live`. Habría quedado el incidente
igual y con sensación de resuelto. Hay guardia con ese nombre.

## Lo que hace ahora

**1. Reintenta con espera creciente.** Un 429 se reintenta hasta 4 veces con
esperas de 1, 2, 4 y 8 segundos. Si Biwenger manda cabecera `Retry-After`, se le
hace caso — salvo que pida más de 60 s, en cuyo caso no se duerme dentro del
workflow: se sale y se vuelve.

**2. Si no cede, sale limpio.** Excepción propia `LimiteDePeticiones`, rama propia
en los dos `main`, y **código de salida 0**:

```
====================================================
LIMITE DE PETICIONES DE BIWENGER
Biwenger devolvio 429 en /market tras 4 reintentos...
El ciclo se retira limpiamente. NO es un fallo: no se
ha tocado nada y se vuelve en la siguiente vuelta.
====================================================
```

**Cualquier otra excepción sigue subiendo igual que siempre** y sigue poniendo el
paso en rojo. Aquí solo se aparta el caso que no es un error.

**3. Y ahora se cuenta.** Cada petición queda anotada por endpoint —con los
identificadores fuera, para que `/user/1` y `/user/2` agrupen— y el ciclo lo
imprime al terminar:

```
Peticiones a Biwenger en este ciclo: 32 (10 endpoints distintos, 22 repetidas = 68.8 %)
     14  GET /user/{id}   <-- repetida
      3  POST /auth/login   <-- repetida
      ...
```

**Un consumo que nadie mide es un consumo que crece.** El día que alguien meta una
llamada dentro de un bucle, esta línea lo canta en la primera vuelta y no en el
siguiente 429.

Va en el constructor del cliente, así que vale también para los colectores, que
llaman a `client.session.get` directamente.

---

# LO QUE ENTRA EN EL COMMIT

`git status` antes. **Diez ficheros, y tres NO son de este encargo:**

**De esta noche:**

```
?? src/biwenger/peticiones.py                 el contador y el aguante del 429
?? src/analysis/test_peticiones_v1.py         15 guardias, sesiones de mentira
?? scripts/contar_peticiones_del_ciclo.py     el recuento, ejecutando de verdad
 M src/biwenger/client.py                     envuelve la sesion
 M src/v10_full_autonomous_live.py            salida limpia (el camino real)
 M src/autopilot.py                           salida limpia + publica el recuento
 M scripts/run_validation_gate.py             + 1 guardia
```

**Del encargo que interrumpiste, ya terminados y en verde:**

```
 M src/analysis/rival_bid_model.py            el comentario del 3 %, corregido
?? scripts/embudo_del_escaparate.py           el embudo por causa de muerte
?? src/analysis/horizonte_adaptativo.py       el horizonte adaptativo, en sombra
```

**Y una cosa guardada, no perdida:** el enganche del horizonte al dashboard estaba
a medias cuando paraste, y lo aparté a `stash@{0}` para no mezclarlo. Se recupera
con `git stash pop`.

**Si prefieres que esos tres no viajen aquí, dilo y los saco a su rama.** Iban en
el árbol y `git add -A` los recoge; me pareció peor esconderlo que decirlo.

---

# LO QUE NO HE HECHO

**No he tocado el cron ni el workflow.** Es tuyo. Arriba está la línea y el porqué.

**No he quitado la colecta duplicada del tablón**, que es el ahorro más grande y
más fácil (−12 de 32). Cambia lo que el observador ve dentro de una vuelta y
querías proponer antes de tocar.

**No he cacheado nada.** Misma razón, y además la caché de perfiles necesita su
propia guardia: una caché que devuelve una plantilla vieja es exactamente el tipo
de dato que engaña sin fallar.

**No he hecho ni una llamada a Biwenger.** El recuento sale de ejecutar el código
contra una sesión falsa.

**No he reactivado el workflow.** Con el 429 aguantado ya es seguro reactivarlo —
si la cuenta sigue limitada, el ciclo se retirará en verde en vez de caerse—, pero
**yo esperaría a que el límite se levante solo** antes de encenderlo, y a decidir
al menos el punto (a).

---

**La frase para mañana:** el ciclo hace **32 peticiones por vuelta y 1.536 al día**,
y **24 de esas 32 son colectar el tablón dos veces** — con un comentario en el
propio código diciendo que no se debe hacer. Quitar el duplicado y el catálogo
repetido baja a **17 sin perder un dato**; cachear lo que solo cambia en el reset
de las 07:00 baja a **~8**. El cron es lo de menos: 24 vueltas de 32 peticiones
siguen siendo 768. Y el 429 ya no tumba nada — reintenta, y si no cede se retira
en verde, **en el `main` que ejecuta el workflow, que no era el que yo estaba
arreglando**.
