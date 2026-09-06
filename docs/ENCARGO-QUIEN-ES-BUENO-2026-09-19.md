# ENCARGO — QUIÉN ES BUENO

**Fecha:** 2026-09-19
**Rama:** `calidad/puntos-de-verdad`
**Parte de:** `docs/resultado-vara-2026-09-18.md`, de una pregunta del dueño que
no tenía buena respuesta, y de una lista suya que vale más que mis cuatro últimos
encargos juntos.

---

## De dónde sale esto

El dueño trajo la lista de consejos básicos de Biwenger —los que cualquiera te da
en un vídeo de seis minutos— y preguntó cuáles hace Pepe. La repaso contra lo
medido:

| Consejo | ¿Lo hace? |
|---|---|
| Fichar a los que suben de precio | **A medias.** La vía TENER existe y está medida, pero con el tope y el listón de hoy casi nunca dispara |
| **Fichar especialistas a balón parado** | **NO.** Y está apagado a propósito |
| **Asegurar la portería** | **NO.** Tenemos un portero, y ninguna regla que lo impida |
| No saturar de defensas | **Sí, desde anoche.** Los factores de posición: 5-4-1 → 3-4-3 |
| Vender antes de la jornada si hay números rojos | **Sí.** Reloj de solvencia T−6 h, funcionando |

Dos noes, y los dos son baratos y concretos. Este encargo los cierra, y además
hace lo que ya estaba escrito: darle a Pepe una idea medida de quién es bueno.

---

## BLOQUE 1 — Primero, dónde entran (o no) los puntos reales

Tú escribiste que en la vara *"no entra ni un punto medido: la calidad es una
escalera decretada a partir de una etiqueta"*, y que la vara entera explica el
**20 %** de la varianza de los puntos.

Pero en los objetos de los objetivos veo `points_last_season` (Pedri: 211),
`raw_points` (211) y `expected_points` (220). O esos números entran en algún
sitio, o se publican y no los usa nadie.

**Traza el camino y escríbelo**, campo por campo: qué número decide, de dónde
sale cada sumando, y en qué punto exacto —si hay alguno— entra un punto que un
futbolista haya marcado de verdad.

Puede que me equivoque yo. Si es así, dilo y el resto se ajusta a lo que
encuentres.

---

## BLOQUE 2 — La calidad, medida

Sustituye la escalera de la etiqueta por **puntos medidos**.

Materia prima que ya está en casa: `points_market` (**374 jugadores con
histórico**), `points_last_season` en las fichas, y las jornadas de ésta.

Dos cosas no son opcionales:

1. **Puntos por partido jugado**, no por jornada. Un suplente que hace 6 en
   veinte minutos no es malo: es uno que juega poco, y de eso se encarga la otra
   mitad de la fórmula. Mezclarlas es contarlo dos veces.
2. **La temporada pasada y ésta no pesan igual.** Elige el peso con un criterio y
   escríbelo.

**La etiqueta no se tira: se degrada a suplente.** Donde no haya puntos medidos
—un recién llegado, uno con minutos ridículos— sigue mandando la jerarquía, y la
ficha dice cuál de las dos la está valorando. Nunca las dos a la vez.

### Cómo sabremos si ha servido

Publica el **antes y el después del 20 %**, con el mismo método con el que
mediste el 0,446. **Si no mejora, no la enciendas** y escríbelo: significaría que
el problema no es la calidad, y saberlo vale más que encenderla.

---

## BLOQUE 3 — Balón parado, que está apagado

`src/intelligence/penalty_intelligence.py` existe, tiene sus bonos escritos
(`PRIMARY_BONUS = 8.0`, `SECONDARY_BONUS = 3.0`) y **está apagado**: depende de
API-Football, que en el plan gratuito rompe la cadena por los dos extremos
—identidad solo de 2024, estadísticas pedidas de 2026— y hay guardia
(`test_penaltis_apagados_v1`) que lo deja dormido. En el `status.json` de hoy no
aparece **ni un solo campo** sobre penaltis, faltas o córners.

Es la señal más fuerte que existe en este juego y no la tenemos.

**Y no hace falta pagar la API.** Ya scrapeamos tres sitios cada ciclo
—FutbolFantasy, Analítica Fantasy, Comuniate, 543/541/389 jugadores hoy— y esos
sitios publican quién tira los penaltis. Mira si alguno lo sirve de forma
razonable de leer.

1. **Averigua qué hay disponible sin API-Football** y dilo. Si ninguna de las
   tres lo publica de forma fiable, **dilo también y para ahí**: prefiero saber
   que no se puede a que lo inventes con una lista escrita a mano.
2. Si se puede: penaltis primero, luego faltas y córners, con la fuente y la
   fecha al lado de cada nombre, y su libro de acierto como cualquier otra
   fuente.
3. **Entra en la vara como bono a la calidad, no como certeza.** Un lanzador de
   penaltis marca más; no marca siempre. Los 8,0 y 3,0 que hay escritos son
   decretados: mídelos contra los puntos reales de los lanzadores conocidos
   antes de darlos por buenos, y si no hay muestra, dilo y usa el número
   decretado marcado como decretado.
4. **No enciendas `penalty_intelligence.py` tal cual.** Sigue colgando de una API
   rota; lo que se enciende es la vía nueva.

---

## BLOQUE 4 — La portería

Tenemos **un portero**. Si Dituro se lesiona, descansa o ve dos amarillas,
salimos con diez y esa jornada está perdida. No hay ninguna regla que lo impida:
simplemente no se le ocurrió a nadie.

1. **Regla nueva: la portería nunca se queda a uno.** Si solo hay un portero en
   plantilla, fichar el segundo sube al principio de la cola de prioridades, por
   encima de cualquier operación de cartera. Con guardia.
2. Anoche mediste que con 258.807 € solo cabe Letacek (150.000) y que los cuatro
   del mercado son terceros porteros. **Vuelve a mirarlo cada ciclo** y publica
   la mejor opción alcanzable hoy, incluyendo la que se abriría vendiendo al
   primero de la cola de ventas.
3. El consejo de la calle dice *"los dos porteros del mismo club"*. Publícalo
   como opción cuando exista —si el titular y el suplente del mismo equipo están
   disponibles y caben— pero no lo hagas regla: son dos fichas para una plaza.

**No compres nada.** Publica y decido yo.

---

## BLOQUE 5 — La lista de la compra

Hoy Pepe solo mira los ~20 jugadores que el Computer pone en el escaparate cada
mañana. No tiene lista propia. No va *a por* nadie: juzga a quien le aparece
delante.

Constrúyele el **ranking de la liga entera** con la calidad del bloque 2 más el
bono del 3, y encima los que de verdad interesan:

- **Solo puntúan once.** Cada fila lleva **a quién sustituiría y cuántos puntos
  por jornada añadiría**. Un crack que no entra en el once vale para revender, no
  para esta lista.
- **Precio al lado**, y marcado si cabe en la caja de hoy, si cabría vendiendo, o
  si no cabe de ninguna manera.
- **Corta en 15.**
- Cuando uno de la lista **aparezca en el escaparate**, que salte en el
  dashboard: *"éste estaba en la lista, puesto 4"*.

No compres nada.

---

## BLOQUE 6 — Dos matices que la lista del dueño afina

**6.1 — "Centrocampistas ofensivos", no "centrocampistas".** El factor de anoche
(×1,147) trata igual a un mediocentro defensivo y a un mediapunta. El consejo
distingue, y con razón. Mira si con los datos que hay se puede separar dentro de
la línea de medios —por puntos medidos, que es lo que el bloque 2 construye— y si
sale una diferencia clara, publícala. **No la apliques todavía**: un factor
encima de otro factor, sin ver antes cómo va el primero, es cómo se pierde el
hilo.

**6.2 — "Revisa el mercado a diario".** Eso ya lo hace: 48 ciclos al día. Lo que
no hace es **comprar**, porque el tope por operación y el listón del 3 % dejan
fuera casi todo. No toques ninguno de los dos en este encargo. Solo publica una
línea: de los 20 del escaparate de hoy, cuántos rechaza por precio, cuántos por
tope y cuántos por calidad. Quiero ver dónde muere el embudo.

---

## Reglas de la casa

1. Rama `calidad/puntos-de-verdad`. `main` no se toca.
2. Verja encadenada, sin excepciones:

   ```powershell
   python scripts/run_validation_gate.py
   if ($LASTEXITCODE -eq 0) {
       git add -A
       git commit -m "calidad: puntos de verdad"
   } else {
       git reset --hard origin/main
       Write-Host "VERJA EN ROJO - nada que subir"
   }
   ```

   Tú no empujas.
3. **Ninguna guardia nueva lee `data/`.** Fixture.
4. **Ninguna función nueva cambia de forma según los datos.**
5. `git status` antes de commitear, y en el informe qué entra.
6. No toques el workflow ni `MAX_SINGLE_SPECULATION_PERCENT`.
7. Termina cada commit con `Autor-real: Claude Code (VS Code)`.
8. **Si esto es demasiado para una noche, haz los bloques 1, 2 y 4** —la calidad
   y la portería— y deja el balón parado y la lista para mañana. Prefiero tres
   bloques bien medidos que seis a medias. Di cuál dejaste y por qué.
9. Si la medición contradice el encargo, gana la medición. Van cinco veces esta
   semana y las cinco has acertado tú.

---

## Informe

- dónde entra (o no) un punto medido en la vara de hoy, campo por campo;
- cómo combinas temporada pasada y ésta, y por qué así;
- **la varianza explicada, antes y después**; si no mejora, la vara nueva se
  queda apagada;
- si se puede saber quién tira los penaltis sin API-Football, y desde dónde;
- si los bonos 8,0 / 3,0 aguantan contra los puntos reales;
- la mejor portería alcanzable hoy, y la que se abriría vendiendo;
- la lista de la compra: 15 nombres, a quién sustituye, puntos que añade, precio,
  si cabe;
- dónde muere el embudo de los 20 del escaparate;
- lo que no hiciste y por qué.
