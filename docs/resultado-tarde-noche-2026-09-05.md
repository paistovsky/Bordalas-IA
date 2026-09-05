# Tarde y noche del 05/09/2026 — resultado

Rama `tarde-noche/2026-09-05`. **Puerta: 77 de 77 en verde** (73 al
empezar). `main` intacto. `npm run build` pasa. Nada desplegado. **El
push lo das tú.** Seis commits.

Nada de esto decide con dinero. `DEPLOYMENT_ENABLED` sigue apagado
esperando el examen del día 11.

---

# 1. Qué dice la prensa hoy

**163 titulares leídos. 68 mencionan a un activo de Biwenger. 12
jugadores salen con señal de verdad.**

Estas son las que valen. La cita es literal, tal como se publicó:

### Lobete — BAJA — vale 150.000 €

> *"Julen Lobete se rompe el cruzado y será baja todo el curso"*
> — MARCA, 04/09

Y al día siguiente, la consecuencia:

> *"El Málaga estudia ir al mercado libre por la lesión de Lobete"*
> — MARCA, 05/09

**Un cruzado son ocho meses.** Eso no está en ningún precio hoy y no
lo dice ninguna de las tres webs que Pepe ya leía.

### Cucurella — DUDA — vale 11.630.000 €

> *"Cucurella, duda para recibir al Inter de Milán"*
> — MUNDO DEPORTIVO, 05/09

Es el jugador más caro de los que salen hoy. Una duda sobre once
millones y medio es exactamente el tipo de aviso que se paga.

### Etta Eyong — BAJA — vale 4.120.000 €

> *"El entrenador del Levante ha admitido que Etta Eyong podría ser
> baja para el partido del Málaga por problemas musculares"*
> — MARCA, 05/09

Declaración del entrenador, no rumor.

### Y tres más que no son bajas pero informan

| | Jugador | Cita |
|---|---|---|
| ONCE | **Nico Williams** (9,16 M) | *"Nico Williams es titular hoy frente al Atlético de Madrid"* |
| VUELVE | **Pablo Marín** (520 k) | *"Pablo Marín vuelve con el grupo en un ensayo con la vista puesta en Elche"* |
| ONCE | **Simeone** (3,01 M) | *"Simeone apuesta por un once continuista, en San Mamés"* |

*(Simeone es un activo: en Biwenger los entrenadores se fichan y están
en el catálogo con `position` 5. Cuatro de las señales de hoy son de
entrenadores.)*

## De dónde sale, y de dónde no

| Canal | Titulares | Más reciente | |
|---|---|---|---|
| MARCA | 48 | hoy 17:46 | **entra** |
| MUNDO DEPORTIVO | 100 | hoy 17:30 | **entra** |
| RELEVO | 15 | ayer 08:04 | **entra** |
| **AS** | 68 | **16/11/2022** | **NO ENTRA** |

**AS está muerto y no lo parece.** Responde 200, trae 68 noticias bien
formadas, con títulos, enlaces y categorías. Su entrada más reciente es
de hace **cuatro años**. Probé también `/rss/portada.xml` y
`/rss/tags/competiciones/primera_division.xml`: 404 los dos.

Es el caso más peligroso de todos —una fuente que parece viva— así que
queda con su módulo apagado y la fecha escrita dentro, igual que
Jornada Perfecta.

## Los cuatro candados

**Tres para no adivinar el jugador.** Un titular no trae un
`player_id`; se busca al revés, cada nombre del catálogo dentro del
texto:

1. **Cuatro letras mínimo.** "Oso" y "Sow" están en el catálogo y
   saldrían en cualquier frase.
2. **En mayúscula en el original.** *"se cortó el cabello"* es pelo;
   *"Cabello marcó"* es el jugador. Son dos de los 569 nombres que
   además son palabra corriente: Cabello y Molina.
3. **Nombre único.** Solo uno se repite en el catálogo —Moussa Diarra,
   dos fichas— y con ése no se elige el más probable: va a `unmatched`.

**Y uno para no adivinar la noticia**, que salió de la primera
ejecución en vivo:

> *"El centrocampista navarro regresa después de perderse los dos
> últimos encuentros por una leve lesión muscular, el central cubre la
> baja de Vivian"*

Una frase, tres nombres del catálogo, y la regla le colgaba **BAJA a
los tres** — cuando uno de ellos justamente *regresa*. Ahora **una
frase con más de un nombre no se clasifica**: se guarda la cita entera
y se dice que el sujeto es ambiguo. Hoy eso ha pasado en 50 de los 118
casos. La información no se pierde; simplemente no se afirma.

## Dato y deducción, separados

- **Dato:** el titular, la frase, el enlace y la fecha. Literal.
- **Deducción:** `kind` y `direction`. Los pone el bot con palabras
  clave y viajan con `deduced: True` y la frase que los disparó.
- **Confianza:** `null` siempre, con su motivo. Ningún periódico
  publica una.

*"Tocado"* se quedó **fuera** de las reglas. En castellano futbolístico
significa las dos cosas, y falló en el primer titular que la contenía:
*"Funes: no podemos amedrentarnos porque nos hayan tocado el Atlético y
el Real Madrid."* Eso es un sorteo, no una lesión.

## Al libro de acierto

Cada señal se apunta con el precio del jugador ese día, horizonte 3
días, y la fuente etiquetada por medio: `PRENSA_MARCA`,
`PRENSA_MUNDO_DEPORTIVO`. **En dos semanas se sabrá si Marca acierta
más que Mundo Deportivo, o si los dos son ruido.**

Solo entran BAJA, DUDA y VUELVE. Una noticia de alineación no dice
hacia dónde va un precio, y apuntarla como predicción inflaría el
acierto con casos que no se pueden fallar.

*Precedente: FutbolFantasy saca 0,3365 de Brier en pronósticos de
titular, peor que tirar una moneda. Ninguna fuente entra por
prestigio.*

## Lo que todavía falla

Dos de las doce señales de hoy están mal atribuidas, y las dejo a la
vista porque el libro las va a puntuar igual:

- **Odriozola** sale BAJA por una frase que habla de él en pasado
  (*"con la baja por lesión de Álvaro Odriozola"*, en un reportaje
  sobre otro jugador).
- **Bartra** sale DUDA por *"existía la duda de que Marc Bartra hubiera
  entrado antes del golpeo"* — una duda del VAR, no física.

Son frases con un solo nombre del catálogo, así que el candado del
sujeto único no las coge. **No las he tapado con más reglas**: prefiero
que el libro mida el ruido real a que yo lo esconda con parches.

---

# 2. Los paneles huérfanos

`AnalysisPage.jsx` importaba siete paneles y no estaba enrutada.
`NegotiationsPage.jsx` tampoco. Al mirar el directorio entero:
**16 componentes de 33 sin alcanzar desde `App.jsx`. La mitad.**

Y no es casualidad: **los doce paneles huérfanos usan `ui/Card` y
`ui/Badge`; los diecisiete que sí se ven usan `pan`.** Es una
generación entera del dashboard que se quedó a medio migrar.

## Panel por panel

| Panel | Qué enseñaba | Veredicto |
|---|---|---|
| `MarketClockPanel` | Reloj del reset del Computer | **Borrar.** MERCADO ya lo pinta con su propio `ClockPanel`, y ESTRATEGIA lo lee también |
| `ExposurePanel` | Caja, comprometido y pujas vivas | **Borrar.** `CashPanel` en MERCADO y `Money` en ESTRATEGIA enseñan lo mismo, y `Money` además separa el bolsillo de fichar del de especular, que éste no hacía |
| `GuardrailPanel` | Suelo por posición | **Borrar.** Está en INICIO y en PLANTILLA, con la misma información y el aviso del portero |
| `SpeculationPanel` | Radar de especulación | **Borrar, y con ganas.** Tres de sus cinco ejes eran constantes escritas a mano: Liquidez 72, Riesgo 42, Demanda 68. No salen de ningún cálculo. Un gráfico con números inventados es peor que no tener gráfico |
| `SolvencyPanel` | Déficit y si es posible sanear | **Borrar.** ESTRATEGIA lo tiene en `Money`, en `SolvencyPlansPanel` con los tres planes, y desde anoche en el reloj de solvencia con el plazo |
| `AcquisitionPanel` | Tabla de objetivos | **Borrar.** La de MERCADO tiene veinte columnas —ojeador, divergencia, confianza por vía, bolsillo— contra las siete de ésta |
| `LeaguePanel` | Clasificación, top 5 | **Borrar.** La Carrera enseña los siete mánagers con la diferencia de puntos y la brecha de plantilla contra mí |

Y los otros nueve que aparecieron al mirar:

| | |
|---|---|
| `AlertsPanel`, `BackoffPanel`, `DecisionPanel` | AUDITORIA y ESTRATEGIA ya publican `lastExecution`, `backoff` y `nextAction` |
| `LedgerAuditPanel` | LIGA lo pinta |
| `NegotiationsPanel` | AUDITORIA enseña el bloque `competitive` |
| `FranchisePanel` | Lo retiró el dueño el 19/08 con motivo escrito. Se quedó el fichero |
| `LineupPitch` y `LineupPitch_PRE_SALE_IMPACT_V91` | Sustituidos por `PitchXI`. El segundo es literalmente una copia de seguridad con el nombre puesto |
| `PlayerAvatar` | Solo lo usaban huérfanos |
| `ui/Card`, `ui/Badge` | El kit del diseño anterior. Sin consumidores vivos |

**Todo borrado: 2 páginas, 16 componentes, 2 del kit.** Unas 1.800
líneas. Está en el historial de git si algún día hace falta una.

**La prueba de que no se servía:** después de borrarlo todo, el bundle
tiene el mismo tamaño y el mismo hash que antes. No se estaba
enviando ni un byte de esto al navegador.

**Guardia nueva:** ninguna página sin enrutar y ningún componente
inalcanzable desde `App.jsx`, siguiendo el grafo de imports de verdad.

---

# 3. X (Twitter): no entra

Lo intenté por cuatro caminos y los cuatro se caen. Con evidencia:

| Camino | Qué pasó |
|---|---|
| API v2 oficial | **401.** No hay clave en el repo y la búsqueda reciente es de pago |
| `x.com/marca` sin sesión | **200 y 286 KB de JavaScript.** Un armazón vacío: el contenido lo carga el navegador tras el muro de login |
| Instancias de Nitter | **No resuelven ni el DNS.** Probadas `nitter.poast.org` y `nitter.privacydev.net` |
| `syndication.twitter.com` | **200 y 100 tweets de verdad.** Y aquí está lo interesante |

El último **parece** la solución: es el endpoint que usa el propio
widget de Twitter para incrustar timelines, no hace falta clave y
devuelve JSON dentro de la página. Lo abrí y miré lo que trae:

```
@marca   [Thu Jul 03 2025] Muere el futbolista del Liverpool Diogo Jota…
         [Fri Sep 16 2022] De cuando Griezmann bailó en el Bernabéu…
         [Sat May 31 2025] "Muy bonita la pancarta, pero no necesito…"
@relevo  [Sun Jul 14 2024] Os la devolvemos corregida, @UEFA
         [Fri Aug 25 2023] Borja Iglesias deja la Selección
```

**No es el timeline: es una selección de tweets destacados de 2022 a
2025, sin orden.** El más reciente es de julio de 2025 y los feeds RSS
van por el 05/09/2026. Leerlo metería tweets de hace un año como si
fueran de hoy — el mismo error que AS, pero disfrazado de éxito.

**Así que no.** Y no lo fuerzo: el encargo pedía un no honesto antes
que un raspador frágil, y aquí ni siquiera es cuestión de fragilidad.
El dato que devuelve está mal.

El día que haya una clave de la API, el módulo se escribe en un rato:
el emparejamiento, la clasificación y el libro de acierto ya están
hechos y son los mismos.

---

# 4. La Carrera, y por qué estaba descuadrada

El dueño: *"que lo baje abajo, que está descuadrado."*

**Estaba descuadrado literalmente, y tenía una causa exacta:**

```css
.poswrap { grid-template-columns: repeat(4, 1fr) }
```

Cuatro columnas. El panel metía **cinco** `.poscel`. El quinto caía
solo a una segunda fila y dejaba media fila vacía. Y encima el titular
iba en un `.godnote` sin modificador, y esa clase solo tiene fondo y
borde en sus variantes `.crit` y `.warn`: quedaba un bloque en negrita
flotando sin caja.

Los cinco cajones repetían, troceada, la frase que el backend ya
calcula entera. Así que se queda **la frase**:

> *Vas 4º, a 13 puntos, quedan 35 jornadas: necesitas sacarle 0,37 por
> jornada. Tu plantilla vale 23,1 M menos que la del líder.*

Y **la tabla**, que es el dato que no está en ningún otro sitio: la
brecha de plantilla contra los seis rivales. Fuera los cajones.

Y baja al final de INICIO.

---

# 5. El mensaje que mentía sobre la causa

`lineup_engine` decía siempre lo mismo cuando no había pronósticos:
*"El tablero de FutbolFantasy está vacío."* El 10/09 leí eso y concluí
que la fuente estaba caída. Lo escribí en un informe. Era falso: el
tablero tenía 64 jugadores y era de la jornada 2 con el calendario en
la 5.

Los datos ya viajaban dentro —`rejected`, `rejection_reason`,
`matchday`, `expected_matchday`—. La rama de "sin jugadores" tiraba el
diccionario entero y lo cambiaba por uno con la frase fija.

Ahora hay **tres mensajes para tres causas**, y el de la jornada lleva
los dos números dentro, que es lo que lo hace accionable:

> *El tablero es de la jornada 2 y estamos en la 5: sin pronósticos
> hasta que se refresque.*

---

# 6. Lo que me sorprendió

## 1. La mitad del directorio de componentes no se veía

Esperaba encontrar los siete paneles del encargo. Encontré dieciséis, y
dos páginas enteras. El dueño podía llevar meses creyendo que tenía
información que no le llegaba a ninguna pantalla.

## 2. Una fuente muerta que responde 200

AS lleva cuatro años sin publicar en ese RSS y contesta perfectamente:
código 200, XML válido, 68 noticias con título, enlace y categorías.
Si no llego a mirar las fechas, entra como fuente buena y hoy estaría
diciendo que Take Kubo se va del Madrid.

Es la misma clase de error que el del tablero de titularidad: **algo
que parece un dato y es un dato viejo.** Dos veces en la misma tarde.

## 3. Mi propia guardia se puso verde con el panel invisible

Anoche escribí la guardia de "el componente está montado en su página"
y hoy me ha dejado publicar la prensa en una página muerta —bueno, casi:
lo cacé mirando el bundle, no el test—. Comprobar que un componente
está en *una* página no basta: hay que comprobar que esa página existe
para la app. Ya lo comprueba.

## 4. La guardia de prensa encontró un bug del código, no del test

Escribí las pruebas con feeds inventados y salieron jugadores que no
estaban en ningún feed inventado: Simeone, Cucurella. `build_press_report`
recorría los cuatro canales y **se bajaba de internet los que no le
habías dado**. La puerta habría dependido de que Marca estuviese de pie.
Arreglado: con feeds en la mano no se sale a la calle.

## 5. Los entrenadores son fichas

Al ver que "Corberán", "Pellegrini" y "Bordalás" emparejaban con el
catálogo pensé que era un falso positivo. No lo era: en Biwenger los
entrenadores se fichan y están en el catálogo con `position` 5. Cuatro
de las doce señales de hoy son de entrenadores, y son legítimas: un
entrenador que anuncia rotaciones mueve el precio de sus jugadores.

---

## Cómo quedó

```
rama          tarde-noche/2026-09-05   (sin subir: el push lo das tu)
main          intacto (lo dejaste en f6456a0 al mergear el reloj)
puerta        77/77 en verde  (73 al empezar, 4 guardias nuevas)
commits       6
frontend      npm run build OK · NO desplegado · dist/ intacto

1. La Carrera     abajo, sin los cinco cajones, causa del descuadre
                  documentada en el codigo.

2. Prensa         MARCA + MUNDO DEPORTIVO + RELEVO. 163 titulares,
                  68 con activo, 12 jugadores con señal. AS apagado
                  con la fecha dentro. Al libro de acierto por medio.
                  Observador puro, guardia `ast` en los dos sentidos.

3. Huerfanos      2 paginas y 18 ficheros borrados, justificados uno
                  a uno. El bundle no cambia de hash.

4. El mensaje     tres causas, tres mensajes, con los numeros dentro.

X (Twitter)       NO. Los cuatro caminos probados, con evidencia.

umbrales          ninguno tocado
DEPLOYMENT_ENABLED = False
```

## Comprobado en vivo antes de cerrar

`sync_press` corre dentro del ciclo sin tocar la red cuando el
informe es fresco, y deja las predicciones apuntadas:

```
sync_press -> status HIT · 163 titulares · 12 con señal · 8 apuntadas

libro de acierto:  PRENSA_MARCA             3
                   PRENSA_MUNDO_DEPORTIVO   5
                   vencen el 08/09, todas PENDING
```

Con la noche que sobraba no empecé nada nuevo: tres guardias más
para la prensa —que el TTL se respete, que un informe vacío no pise
al bueno, y que los cuatro contadores del ruido se publiquen—. Sin
ellos, doce señales parecen doce aciertos cuando salen de 163
titulares y 95 descartes.

**La frase para mañana:** Pepe ya lee prensa, y lo primero que ha
encontrado es que a Lobete se le rompió el cruzado y está en el mercado
a 150.000 €. Ninguna de las tres webs de precio que leía antes sabía
eso, porque el precio todavía no se ha enterado. En dos semanas el
libro de acierto dirá si eso es ventaja o es ruido —y hay dos señales
de hoy mal atribuidas que no he tapado, precisamente para que las mida.
