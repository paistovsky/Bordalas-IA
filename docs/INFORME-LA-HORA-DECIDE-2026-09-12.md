# La hora decide, no quien llama

**12/09/2026** · verja 112/112 · sin push

---

## Tus dos commits, traídos

```
c7289e8  la autoridad del reloj sale del repositorio        <- mios
9161161  el carril con bolsillo propio
de3f7d5  la prueba de humo
d678ce6  el carril, enchufado de verdad
3eef7b1  cablear el carril
39f238c  Update bordalas-live.yml                           <- tuyos
a85155b  Update bordalas-live.yml
```

Rebase, no merge: mis cinco encima de los tuyos, historia recta y sin commit de
mezcla. El único fichero que tocábamos los dos era el workflow y salió limpio — mi
copia local ya partía de tu versión. Verja verde después del rebase, antes de tocar
nada más.

---

## La regla, como la pediste

```python
CLASES_DELIBERADAS = frozenset({"ventana", "tras_el_reset"})
```

Un disparo cuenta como **deliberado** sólo si cae en una de las horas declaradas
en `config/disparos.json`, dentro de su margen de gracia. Cualquier otro está
**descolocado** y no escribe dentro de la zona de silencio, venga por donde venga.

`permite_escribir` ya no mira `DISPAROS_DELIBERADOS`. La lista **se queda escrita**
—renombrada a `DISPAROS_DELIBERADOS_RETIRADOS`, con el porqué— y el nombre del
disparo se sigue publicando como `trigger`: para mirar un incidente vale, para
decidir ya no.

### La tabla, ejecutada

| hora Madrid | `schedule` | `workflow_dispatch` | `manual` | *(sin disparo)* | declarado |
|---|---|---|---|---|---|
| 04:45 | ESCRIBE | ESCRIBE | ESCRIBE | ESCRIBE | ventana |
| 04:47 | ESCRIBE | ESCRIBE | ESCRIBE | ESCRIBE | ventana |
| 04:50 | ESCRIBE | ESCRIBE | ESCRIBE | ESCRIBE | ventana |
| 05:00 | ESCRIBE | ESCRIBE | ESCRIBE | ESCRIBE | ventana *(gracia)* |
| **05:30** | **calla** | **calla** | **calla** | **calla** | — |
| **06:40** | **calla** | **calla** | **calla** | **calla** | — |
| 06:52 | calla | calla | calla | calla | — |
| 07:15 | ESCRIBE | ESCRIBE | ESCRIBE | ESCRIBE | fuera de la franja |
| 12:07 | ESCRIBE | ESCRIBE | ESCRIBE | ESCRIBE | fuera de la franja |

**Las cuatro columnas dicen lo mismo en todas las filas.** Eso es exactamente el
punto: quien llama dejó de importar.

---

## Los dos casos que pediste conservar

**05:30 y 06:40 siguen en la guardia, y ahora en dos sitios:**

- `test_el_bot_avisa_si_el_ciclo_no_entra_a_su_hora` — la alarma los ve (40 y 35
  minutos de desfase). Sin tocar.
- `test_el_descolocado_no_escribe_venga_de_donde_venga` — **nueva**: los prueba
  contra cinco llamantes distintos (`workflow_dispatch`, `repository_dispatch`,
  `manual`, `ventana`, y sin disparo) y exige `allowed=False` en los veinte casos.

---

## Una cosa que tienes que saber, y es un número

**El margen de gracia hace que la ventana sea más ancha que las tres horas.**

La gracia declarada son 12 minutos, y está ahí por un motivo real: un ciclo
disparado a las 04:50 tarda en arrancar, correr y llegar a la escritura. Sin
gracia, **el trabajo de la ventana se bloquearía a sí mismo**.

El efecto es que la banda deliberada no son tres instantes, sino:

```
04:33 - 05:02    (04:45 y 04:50, con su gracia)
07:03 - 07:27    (07:15 — y ya está fuera de la franja de silencio)
```

O sea: **de 04:33 a 05:02 un disparo descolocado seguiría contando como el trabajo
de la ventana.** Fuera de esa banda —05:03 en adelante— no escribe nada.

No he inventado ese número: es `gracia_minutos` de la declaración, el mismo que usa
la alarma. Si te parece ancho, se estrecha cambiando **un campo del JSON** y las
dos cosas se mueven juntas. Te lo digo porque la tabla de arriba enseña 05:00
escribiendo y quiero que se entienda por qué, no que te lo encuentres un día.

---

## Cuatro guardias que decían lo contrario

El eje cambió, así que cuatro guardias afirmaban lo opuesto a la regla nueva. Las
he **reescrito, no parcheado**, y cada una lleva escrito qué premisa cambió:

| guardia | qué decía antes |
|---|---|
| `test_el_disparo_deliberado_si_escribe` | `workflow_dispatch` escribe en la ventana → ahora **la hora** escribe |
| `test_sin_saber_quien_dispara_se_calla` | sin disparo conocido, se calla → ahora **no saber quién no cambia nada** |
| `test_fuera_de_la_franja_se_escribe_siempre` | 05:00 bloqueado → ahora cuenta la gracia, leída de la declaración |
| `test_el_silencio_cubre_la_ventana_entera` | `schedule` calla / `workflow_dispatch` escribe → ahora las dos según la hora |
| `test_el_disparo_deliberado_viaja_hasta_el_silencio` | el ciclo pasa el disparo y eso salva la ventana → el disparo **se pasa y se publica, pero no decide** |

Y una nueva: `test_sin_declaracion_no_se_escribe_en_la_ventana`. Si la declaración
no se pudiera leer, **no** es deliberado. El lado seguro de no saber a qué hora
tocaba entrar es no tocar el mercado mientras se resetea.

---

## Doctrina 38

> **Lo que decide no puede depender de quién pregunta.**
>
> El criterio no se volvió más permisivo el día que se quitó el `schedule`: **dejó
> de distinguir nada**, en silencio y sin ponerse rojo. Una decisión se toma sobre
> una propiedad del hecho —aquí, la hora—, no sobre la identidad de quien lo trae.
> Quién llama es un dato del entorno: cambia por motivos que no tienen nada que ver
> con la decisión, y cuando cambia no avisa.
>
> Es la regla 33 llevada a las decisiones: **un criterio, una propiedad**. Si el
> criterio necesita saber quién pregunta, es que aún no se ha encontrado la
> propiedad.

---

## Estado

- Verja: **112/112**
- Rebase hecho: tus dos commits abajo, los cinco míos encima
- Pantalla construida y desplegada
- Rama `main`, **sin push**
