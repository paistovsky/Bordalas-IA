# PASOS A Y B: DE 1.536 PETICIONES AL DÍA A 349

Rama `peticiones/bajar-el-ritmo`. **95 de 95 en verde.**
**Ni una llamada a Biwenger.** Sin push. El cron sigue igual.

---

# EL NÚMERO, MEDIDO

**Con el mismo cron de 48 vueltas, y sin perder capacidad de decisión.**

```
                              x CICLO  VUELTAS   AL DIA
  -------------------------------------------------------
  ANTES (06/09)                    32       48     1536
  AHORA, primera del dia           17        1       17
  AHORA, las otras 47               7       47      329
  + los que se mueven               1        3        3
  -------------------------------------------------------
  TOTAL AL DIA                                      349

  DE 1536 A 349 PETICIONES AL DIA (77 % menos).
```

**Sale 349 y no los 342 que proyecté**: la primera vuelta tras el reset paga
entera (17), no 7. La diferencia es mía, del modelo de anteanoche, y prefiero la
cifra medida.

**La quinta parte de lo que provocó el bloqueo** — y en realidad menos, porque el
429 lo provocó mi ráfaga de 619 fichas en cinco minutos, no el ritmo del ciclo.

## Endpoint por endpoint

| Endpoint | 1ª del día | Crucero |
|---|---:|---:|
| `GET /user/{id}` (perfiles) | **7** | **0** |
| `GET /user` | 2 | 2 |
| `POST /auth/login` | 1 | 1 |
| `GET /account` | 1 | 1 |
| `GET /market` | 1 | 1 |
| `GET /league/{id}/board` | 1 | 1 |
| `GET /user/{id}/finances` | 1 | 1 |
| `GET /competitions/la-liga/data` | 1 | **0** |
| `GET /rounds/league` | 1 | **0** |
| `GET /league` | 1 | **0** |

---

# PASO A — sin duplicados: 32 → 17

**Tres piezas, ninguna cambia un solo dato de los que Pepe ve.**

## 1. El tablón, una vez y no dos (−12)

`build_competitive_observer` llamaba a `collect_board_history()` a pelo: nuevo
login, nueva lista de managers, los siete perfiles otra vez. **Y veinte líneas más
abajo tenía escrito:**

> *"Ya se construyó antes de decidir. Volver a pedir el tablón sería una segunda
> llamada de red por el mismo dato."*

Alguien puso caché a `load_rival_intelligence` y dejó la llamada de arriba. **El
comentario documentaba una intención que el código no cumplía.**

Ahora la caché guarda también el tablón, y `board_del_ciclo(snapshot)` lo sirve.
**576 peticiones al día por un dato que ya estaba en memoria.**

## 2. El catálogo, una vez (−1)

`collect_league_snapshot` lo pedía dentro de `get_my_team()` y otra vez tres líneas
después, mismos parámetros. `get_my_team(catalog=...)` acepta ahora el que ya se
tiene; sin argumento, se comporta como siempre.

## 3. Un solo login por vuelta (−2)

Cada colector construía su propio cliente. Dos `POST /auth/login` y dos
`GET /account` para la misma sesión. `cliente_del_ciclo()` lo comparte — y como un
proceso es exactamente un ciclo, la sesión muere con él y no cruza vueltas.

**Guardia:** `test_una_vuelta_cuesta_lo_que_dice_el_informe` ejecuta los colectores
contra una sesión falsa y **falla si el número sube**, con el desglose en el
mensaje. Más `test_el_tablon_se_colecta_una_sola_vez`, que lo comprueba por el
efecto —cuántas veces se pide `/league/{id}/board`— y no por el nombre de la
función, para que valga aunque alguien reorganice el código.

---

# PASO B — caché entre resets: 17 → 7

**Dos relojes distintos, y mezclarlos era el peligro.**

## Reloj 1: lo que cambia en el reset

Catálogo, jornada y lista de managers. Valen hasta las 07:00 siguientes. La hora
**se importa** de `market_clock.FALLBACK_RESET_HOUR_UTC` — no se copia, para que no
haya dos horas del reset en el proyecto. Hay guardia.

## Reloj 2: las plantillas rivales

**Aquí el reloj del reset nos habría dejado ciegos.** Si Pollo ficha a las 16:00 y
su plantilla valiera "hasta mañana a las 07:00", Pepe decidiría contra una
plantilla que ya no existe durante quince horas.

Así que las plantillas no tienen hora: **tienen un aviso**. El tablón ya está
pedido, cuesta una petición y dice quién se ha movido. Se lee el índice antes de
abrir el libro.

```
   Perfiles: 0 de 7 se han movido o no estaban guardados; 7 se reutilizan.
```

**336 peticiones diarias de perfiles pasan a 3** — el número medido de managers que
se mueven al día.

**La guardia que pediste** es `test_el_que_se_mueve_a_media_tarde_se_refresca`: un
manager ficha media hora después de la última colecta y **tiene que salir en la
lista de refresco**, solo. Y su hermana, `test_en_un_traspaso_se_refrescan_los_dos`:
un traspaso cambia DOS plantillas, y refrescar solo la del que vende dejaría la del
comprador con un jugador de menos — que es justo la que dice cuánto puede pujar.

## Cómo falla, que es lo que importa de una caché

**Siempre hacia el lado caro.** Sin caché previa, con el interruptor puesto, con
datos corruptos o si algo revienta: **se refrescan los siete**. Una caché que se
equivoca hacia el lado caro cuesta peticiones; hacia el barato, decisiones. Hay
guardia (`test_ante_la_duda_se_refresca_de_mas`).

Y un perfil que falló al bajarse **no se guarda**: si no, ese error se serviría como
dato hasta que ese manager fichara.

**Interruptor:** `BORDALAS_SIN_CACHE=1` y todo vuelve a pedirse cada vuelta.

## El riesgo que acepto, escrito

**El catálogo trae el precio —que solo cambia en el reset— y también el estado:
lesionado, duda, sancionado. Eso sí puede cambiar a media tarde.**

Lo acepto porque **la titularidad y los partes de baja llegan por otra vía** —el
ojeador y la prensa, que no pasan por esta caché—, así que un jugador que se lesiona
a las 14:00 sigue saliendo bloqueado por el pronóstico aunque el catálogo diga "ok".

**Si te parece poco margen, la salida está medida:** sacar el catálogo de
`CACHEABLES` y volver a pedirlo cada vuelta cuesta **47 peticiones al día** — de 349
pasaríamos a 396. Es una línea.

---

# EL PASO C NO ESTÁ, COMO DIJISTE

El cron sigue siendo `7,37 * * * *`. **No he tocado el workflow.**

Y con A y B hechos, el argumento en su contra es más fuerte que cuando lo escribí:
bajar a 24 vueltas ahorraría **168 peticiones** sobre un consumo que ya son 349.
Media capacidad de reacción por un 48 % de una cifra que ya no es el problema.

---

# UN FALLO MÍO EN ESTA MISMA NOCHE

**La verja salió roja**, y en una guardia que había escrito yo anteanoche:
`test_la_sonda_del_recuento_no_escribe_estado`. Comprobaba que en la fuente
apareciera la palabra `salidas_originales`. Al reorganizar la sonda esa variable
cambió de nombre, **la guardia se puso roja y no había nada roto**: estaba vigilando
un nombre, no un comportamiento.

Reescrita: ahora **mide** los caminos de escritura antes y después de la sonda y
exige que sigan apuntando donde apuntaban. Y su hermana nueva,
`test_la_sonda_no_deja_ficheros_en_el_estado`, fotografía el árbol de estado antes y
después y falla si aparece un fichero — que es como se habría cazado en el acto el
incidente de anteanoche, en vez de tres tests más abajo y en otro fichero.

*(Y de camino, un artefacto del arnés: mi sesión falsa devolvía `id: 1` para los
siete perfiles, así que se guardaban bajo la misma clave y la medición decía que se
refrescaban seis cuando el código hacía lo correcto. **Un arnés que colapsa
identidades mide otra cosa.** Corregido para que devuelva el id pedido.)*

---

# LO QUE ENTRA EN EL COMMIT

`git status` antes. **Ocho ficheros:**

```
?? src/biwenger/cache_del_reset.py            la caché y los dos relojes
 M src/biwenger/client.py                     cliente compartido + catálogo opcional
 M src/collectors/league_collector.py         catálogo una vez, jornada cacheada
 M src/collectors/board_history_collector.py  managers cacheados, perfiles por aviso
 M src/autopilot.py                           el tablón, una sola colecta
 M src/analysis/test_peticiones_v1.py         de 18 a 31 guardias
 M scripts/contar_peticiones_del_ciclo.py     mide 1ª vuelta y crucero
?? docs/resultado-sin-duplicados-y-cache-2026-09-08.md
```

**No entra ningún dato.** La caché vive en `data/autopilot/cache_biwenger.json` y
los perfiles en `data/rival_intelligence/profiles_cache.json`: estado del ciclo,
gitignorado, y se crean solos en la primera vuelta.

---

# LO QUE NO HE HECHO

**No he tocado el cron ni el workflow.**

**No he reactivado nada.** Seguimos bloqueados y no he hecho ni una llamada.

**No he cacheado `/market` ni el tablón**, que son los dos que cambian de verdad
entre vueltas. Son 2 de las 7 peticiones de crucero y ahí está la capacidad de
reaccionar.

**No he tocado `/user`** (plantilla y alineación, 2 por vuelta): son nuestras y
cambian cuando Pepe escribe.

---

**La frase para mañana:** de **1.536 peticiones al día a 349, un 77 % menos, con el
mismo cron y sin perder una sola decisión**. La mitad del ahorro salió de dejar de
pedir dos veces lo mismo —el tablón se colectaba dos veces por vuelta con un
comentario al lado diciendo que no debía hacerse—; la otra mitad, de entender que
las plantillas rivales no se cachean con reloj sino **con aviso**: el tablón dice
quién se ha movido y cuesta una petición. **336 al día pasan a 3.** Y el que ficha a
media tarde se refresca a las y media, con guardia que lo prueba.
