# ADELANTARSE AL MERCADO — resultado

Rama `intel/adelantarse-al-mercado`. **99 de 99 en verde.**
**Ni una llamada extra a Biwenger. Cero peticiones añadidas.** Sin push.

Ningún umbral movido. Nada encendido: todo se publica.

---

# LO PRIMERO, PORQUE ERA LO URGENTE: YA SE ARCHIVA

```
  Archivado 2026-09-09: press, scout.
  1 dia(s) archivados, de 2026-09-09 a 2026-09-09.
```

**Día uno.** Cada vuelta del ciclo copia el informe del ojeador y el de prensa a
`data/intelligence/archivo/YYYY-MM-DD/`. La primera vuelta del día escribe; las 23
siguientes ven que ya está.

**Cuesta cero peticiones.** No baja nada nuevo: copia lo que el ciclo ya deja en
disco dos líneas antes. Es la pieza más barata del encargo y probablemente la más
valiosa.

Tres decisiones que van con guardia:

- **Nunca pisa lo que ya hay.** Un archivo sobrescrito es peor que no tenerlo:
  parece histórico y es la foto de hoy repetida.
- **Se guarda el informe entero, no un resumen.** Hace un mes nadie sabía que
  íbamos a querer cruzar titulares con subastas.
- **La poda no borra lo que no entiende**, y guarda 60 días — el mismo horizonte
  que el almacén de precios, porque se van a cruzar.

---

# BLOQUE 1 — Qué había ya, y no es lo que decía el encargo

| Pieza | Qué es de verdad | ¿Decide algo? |
|---|---|---|
| `news.py` | **vacío, 0 líneas** | no |
| `transfers.py` | 17 líneas: api-football (**de pago**), traspasos por jugador | sí, vía `external_status` |
| `external_status.py` | lesiones y sanciones desde api-football | **sí**: veta comprar y alinear |
| `scout/press.py` | **1.225 líneas.** MARCA, MD y Relevo por RSS | publica; no decide |

**El encargo decía que `news.py` y `transfers.py` estaban vivos en la ruta de
pujar.** Medio cierto: `transfers.py` sí, pero es api-football y sirve para saber si
un jugador está lesionado — no trae noticias de mercado. **`news.py` está vacío.**

**La prensa de verdad es `press.py`**, y trae más de lo que suponíamos.

---

# BLOQUE 2 — El cruce ya existía, y es contra el catálogo entero

```
  Informe del 05/09:  68 jugadores con noticia,  12 con señal
  MARCA 48 titulares (20 emparejados)
  MUNDO_DEPORTIVO 100 (45)
  RELEVO 15 (3)
  AS: APAGADO A PROPOSITO — su RSS lleva desde 2022 sin actualizarse
```

**Ya se lee el flujo una vez y se busca a quién menciona** —nunca jugador por
jugador— y **ya se cruza contra el catálogo completo, no contra el escaparate.**
Los dos avisos de ingeniería del bloque 2 estaban cumplidos antes de esta noche.

Lo que sí encontré, y merece un aplauso a quien lo escribió: **AS está apagado a
propósito** porque su RSS responde 200 con noticias bien formadas cuya más reciente
es de noviembre de 2022. Leerlo habría metido titulares de hace cuatro años como si
fueran de hoy.

---

# BLOQUE 3 — La clasificación existe a medias

Hay taxonomía: `BAJA`, `DUDA`, `VUELVE`, `ALINEACION`, `FICHAJE`, `MENCION`.

Hoy: **60 MENCION, 5 ALINEACION, 4 BAJA, 2 DUDA, 2 VUELVE.**

**Faltan tres de las clases que pide el encargo**: *interés de otro club*,
*cambio de entrenador* y *cesión/traspaso* como clase propia (`FICHAJE` existe pero
hoy no tiene ni un caso). Son las tres que el vídeo señala como las que dan dinero.

**No las he añadido**: reconocer "el Málaga busca a fulano" es trabajo de reglas de
lenguaje, y el libro de acierto tiene que existir antes para saber si vale la pena.

---

# BLOQUE 4 — El libro de acierto, construido y vacío

Como pediste: se publica desde el primer día para verlo llenarse.

```
  1 dia archivado, 73 avisos, 0 mediciones.
  "Hacen falta al menos 1 dia mas de archivo para medir el
   horizonte mas corto."
```

Mide, por clase de noticia y a **1, 3 y 7 días**: cuánto movió el precio, en qué
dirección y con qué porcentaje de fallo. Con menos de 30 casos no publica mediana —
dice cuántos hay.

Dos detalles que van con guardia:

- **Una noticia repetida por tres medios cuenta una.** Contarla tres veces
  inflaría la muestra sin añadir información, y todo el libro se apoya en el tamaño
  de la muestra.
- **"Vacío" no es una respuesta**: dice qué falta y cuántos días.

---

# LA PELEA COMO COSTE — tu segundo añadido

La tabla medida anoche, ahora dentro del código:

| | Cae o plano | Sube ≥ 1 % |
|---|---:|---:|
| barato < 1,5 M | 54 % | **83 %** |
| medio 1,5–3 M | 39 % | 64 % |
| **caro ≥ 3 M** | **22 %** | 67 % *(n=6)* |

Con `P(llevárselo) ≈ 1 − P(disputada)`, que es una aproximación y se dice: pujando
al +0,25 % se gana prácticamente lo que nadie disputa.

**Y se ve en el reparto:**

```
  SIN contar la pelea:  7 pujas, 1.964.907 EUR
     los siete baratos, todos con 46 % de llevárselo

  CONTANDO la pelea:    4 pujas, 2.375.929 EUR
     Gabriel Suazo  1.730.000   se lo lleva 61 %
     Letacek          150.000   se lo lleva 46 %
     Pelayo           240.000   se lo lleva 46 %
     Javi Morcillo    250.000   se lo lleva 46 %
```

**Un 61 % desplaza a tres 46 %.** Ocupa menos fichas y compromete más dinero: es el
intercambio real, y hay que verlo antes de decidir.

**Está apagado**, con guardia de que lo está. Y **sin celda medida no se inventa un
1**: dar por hecho que se gana lo que no se ha medido es como se fabrica una ventaja
que no existe.

*(La celda "caro y subiendo" tiene 6 casos. Se publica y se marca: un 67 % de seis
no es un 67 %.)*

---

# BLOQUE 0 — Las compras de Pollo: no se puede contestar todavía

**Y ésa es exactamente la razón de tu primer añadido.**

Pollo hizo **51 compras del 11/08 al 06/09**. El archivo de prensa **empieza hoy**.

Lo único comprobable: de sus **7 compras a menos de tres días del único informe que
conservamos** (05/09), **ninguna tenía noticia en él**.

**Con n=7 eso no prueba nada** —ni a favor ni en contra— pero es todo lo que hay. A
partir de mañana habrá dos días; en una semana, siete.

---

# BLOQUE 6 — El coste

```
  TOTAL AL DIA:  181 peticiones     (sin cambios)
```

**Cero añadidas.** El archivo copia ficheros locales; el libro de la prensa lee
disco; la pelea es aritmética. Las webs de recomendaciones ya se visitan cada vuelta
y no se ha tocado su ritmo.

Muy por debajo del límite de 400 que pusiste.

---

# BLOQUE 5 — Cómo entra en las decisiones

**No entra.** Fase 1 tampoco: la noticia todavía no ordena nada, porque el libro de
acierto está vacío y ordenar por una señal sin saber si acierta es exactamente lo
que el encargo pide no hacer.

Lo que sí está listo para la fase 1 en cuanto haya unos días de archivo: la
clasificación, el cruce y el libro.

---

# LO QUE ENTRA EN EL COMMIT

`git status` antes. **Seis ficheros:**

```
?? src/intelligence/archivo_diario.py     guardar hoy lo de hoy
?? src/intelligence/libro_de_la_prensa.py que clase de noticia mueve el precio
?? src/analysis/test_intel_v1.py          19 guardias, ficheros temporales
 M src/autopilot.py                       el ciclo archiva y poda
 M src/analysis/la_subasta.py             la pelea como coste, apagada
 M scripts/run_validation_gate.py         + 1 guardia
?? docs/resultado-adelantarse-2026-09-09.md
```

**No entra ningún dato**: el archivo vive en `data/`, gitignorado.

**El workflow no se ha tocado.**

---

# LO QUE NO HE HECHO

**No he añadido las tres clases de noticia que faltan** (interés de otro club,
cambio de entrenador, cesión). Es trabajo de reglas de lenguaje y el libro tiene que
decir antes si `FICHAJE` mueve algo.

**No he encendido la fase 1.** Con el libro vacío, ordenar por noticia es adivinar
con más pasos.

**No he leído Comuniate, Analítica, Jornada Perfecta ni Asesorías Fantasy como
fuente de NOTICIAS.** Las tres primeras ya se visitan como fuente de *movimiento de
precios* —son el ojeador— y añadir su sección de recomendaciones es una fuente
nueva con su propio parser. No cabía esta noche sin hacerlo mal.

**No he comprobado las compras de Pollo.** No se puede: el archivo empieza hoy.

---

**La frase para mañana:** el archivo **ya corre y cuesta cero** — desde hoy no se
pierde un día más, que era lo urgente. El cruce contra los 521 **ya existía** en
`press.py` (68 jugadores con noticia hoy) y `news.py` estaba **vacío**: media pieza
estaba hecha y media no era lo que creíamos. El libro de acierto está construido y
**se publica vacío a propósito, diciendo qué le falta**. Y la pelea entra como coste
en el reparto —**un 61 % de llevárselo desplaza a tres 46 %**— publicada y apagada.
Lo de Pollo sigue sin poder contestarse, y ésa es la mejor defensa de por qué había
que archivar hoy.
