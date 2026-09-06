# ENCARGO — LA DOCTRINA

**Fecha:** 2026-09-20
**Rama:** `doctrina/que-pepe-la-siga`
**Documento de referencia:** `docs/DOCTRINA.md` (versión 1.1)

---

## Qué es esto

El dueño ha juntado los consejos básicos de Biwenger, un vídeo de trucos que he
transcrito entero, y la forma medida de jugar de Pollo17. Ha dicho: *"eso es lo
que quiero que haga Pepe"*.

Está en `docs/DOCTRINA.md`: **dieciocho reglas**, cada una con su origen —VÍDEO,
CONSEJO, POLLO o MEDIDO— y su estado. **Seis hechas, doce por hacer.**

**Léelo entero antes de tocar nada.** Y si alguna regla contradice una medición
tuya, **gana la medición** y lo dices. La doctrina no es sagrada: es lo mejor que
sabemos hoy, y va fechada por eso.

El vídeo está grabado para ligas de 18 managers y la nuestra tiene siete. Donde
eso cambia el consejo, está anotado en el documento. **Adaptar no es
desobedecer**, pero adaptar sin decirlo sí es hacer trampa: si ajustas algo,
escríbelo.

---

## Dos precisiones del dueño, de hoy

**Los entrenadores se descartan.** Esta liga no los usa. El truco nº 4 del vídeo
queda anulado y así está anotado en la doctrina.

**Los otros siete se quieren todos, y ninguno por encima de los demás.** No hay
pieza central. Lo que sigue va ordenado de barato a caro por eficiencia, no por
importancia: si algo se queda fuera esta noche, se hace mañana, no se descarta.

## Orden de la noche

**Si no llegas a todo, para donde toque y dilo.** Prefiero tres bien hechos que
siete a medias.

---

### 1. Que cada decisión cite su regla — antes que nada

Cada vez que Pepe ficha, vende, alinea, puja o rechaza, la decisión lleva **el
número de la regla** que la sostiene, junto al motivo que ya escribe.

Y lo que de verdad quiero: **la lista de decisiones que no citan ninguna**. Ésas
son las que toma por un motivo que nadie ha escrito nunca.

**No fuerces la cita.** Si una decisión no encaja en ninguna regla, que salga sin
cita y en la lista. Un mapeo inventado para que no haya huecos es peor que los
huecos.

---

### 2. Dos comprobaciones baratas

Las dos son de averiguar, no de construir. **Si la respuesta es "no se puede",
esa es una respuesta buena**: escríbela y pasa a la siguiente. No inventes un
apaño.

**2.1 — ¿Se pueden ver las pujas de los rivales?** (regla 12)

El vídeo dice que Biwenger deja gastar monedas para ver quién ha pujado por un
jugador. Nosotros llevamos semanas construyendo un modelo estadístico
—`rival_bid_model`, 48 pujas calibradas, curva de primas— para **estimar** lo que
el juego quizá deje **ver**.

Averigua: ¿existe en la API? ¿tenemos monedas? ¿cómo se consiguen? ¿qué devuelve?
Solo mirar. **No gastes ni una moneda** sin que yo lo autorice.

Si existe, es más valioso que el modelo entero: se pasa de adivinar a saber.

**2.2 — ¿Qué clubes acaban de ascender?** (regla 8)

Necesario para lo de abajo. Tres equipos, un dato fijo de la temporada. De dónde
lo saques es cosa tuya, pero que quede escrito de dónde vino.

---

### 3. Recién ascendidos — la regla nueva (regla 8)

Del vídeo, el truco nº 3:

> *"Hay titulares que valen 500.000 o 600.000 y están subiendo 70.000 al día;
> como se le ocurra meter un gol se van a 6 o 7 millones."*

70.000 sobre 600.000 es un **+11,6 % diario**. Nuestro tramo `> 4 %/día` ya está
medido rindiendo **+21,15 % a tres días**. **La vía TENER ya sabe valorar esto.
Lo que no sabe es buscarlo.**

Así que no hace falta un motor nuevo: hace falta que Pepe sepa **qué club acaba
de ascender** y que eso viaje en la ficha del jugador. Con eso:

- publica la lista de titulares de recién ascendidos que hay hoy en el mercado,
  con precio y ritmo diario;
- márcalos en el panel de mercado;
- y **antes de darles ningún trato especial, mídelo**: en el histórico que
  tenemos, ¿los jugadores de recién ascendidos suben más que el resto? Si no lo
  hacen en nuestros datos, el consejo se queda como aviso y no como factor. Regla
  de la casa 18.

**No compres nada.**

---

### 4. Las noticias de los baratos (regla 10)

La otra mitad del truco más importante del vídeo:

> *"Uno del Getafe que vale 200.000; me informo y pone que el Málaga lo busca.
> Esos son los que te dan la pasta."*

Esto **no es momento, es anticipación**: la rampa detecta al que ya sube, esto al
que subirá mañana. Tenemos ojeador de prensa (MARCA, MD, Relevo) y no está
apuntando ahí.

- que el ojeador de prensa busque **cesiones, traspasos e interés de otros
  clubes**, y lo cruce con los jugadores, **sin filtrar por precio** —el vídeo
  insiste en mirar hasta los de 150.000—;
- **y no solo con los 20 del escaparate: con toda la liga.** Hoy Pepe únicamente
  conoce a quien el Computer le pone delante. La noticia buena aparece antes de
  que el jugador salga al mercado, y para eso hay que tenerlo ya fichado en la
  cabeza;
- cada aviso, con su titular, su fuente y su fecha;
- y su libro de acierto, como cualquier otra fuente: dentro de dos semanas quiero
  saber si esos titulares predijeron algo o fueron ruido.

**Dos avisos de ingeniería, porque esto puede reventar el ciclo.** El ciclo corre
cada 30 minutos y ya tuvimos un problema serio de duración en agosto:

1. **La ficha completa de los ~570 se construye una vez al día**, después del
   reset del Computer de las 07:00, y se guarda. Cada ciclo solo refresca los del
   escaparate. Enriquecer a 570 jugadores 48 veces al día no cabe.
2. **Los titulares se cruzan contra los jugadores, no al revés.** Se lee el flujo
   de noticias una vez y se busca a quién menciona. Ir jugador por jugador
   preguntando a la prensa son 570 peticiones y no hay ninguna necesidad.

**Publicar. No comprar.**

---

### 5. El embudo — la pieza que llevo dos noches pidiendo

De los 20 del escaparate de hoy: **cuántos mueren por precio, cuántos por el tope
por operación, cuántos por el listón de rendimiento, cuántos por calidad y
cuántos por disponibilidad.**

Una tabla. Con eso delante se decide qué aflojar, y no antes. Si 18 de 20 mueren
en el mismo sitio, ya sabemos dónde mirar.

**No toques ningún tope ni ningún listón esta noche.**

---

### 6. Yamal (regla 15) — solo si llegas

```
Yamal   21.210.000 EUR = 42,81 % de la plantilla   (tope 35 %)
        50 % de titularidad
        +40.000 EUR/dia = +0,19 % diario
```

Pollo vendió a Vinícius y bajó de 85 M a 67,8 M.

Calcula y publica **sin vender nada**: cuántos puntos por jornada aporta al once
—medidos, no por etiqueta—; qué se compraría con esos 21,21 M según la lista, y
cuántos puntos añadiría entre todos; qué pasa con la concentración y con la caja.

Y **el riesgo al revés, con la misma fuerza**: es un jugador del Barcelona, con
el precio al alza, y estaríamos decidiendo con cinco jornadas de datos. Vender al
mejor de la plantilla por esa cuenta puede ser el error más caro del año.

Las dos columnas. Sin recomendación. Decide el dueño.

---

## Lo que NO hay que hacer

**No conviertas la doctrina en constantes nuevas.** Es un documento de intención.
Cada regla que se implemente necesita su medición, igual que las anteriores.

**No copies a Pollo en lo que no hemos medido.** Sabemos que rota, que no
sobrepaga y que vendió a Vinícius. No sabemos si va apalancado ni cómo elige, y
sus siete compras van a −0,13 % tras 1,23 días, que no es un veredicto.

**No copies el vídeo sin filtrarlo por nuestra liga.** Está hecho para ligas de
18 managers y en agosto.

**No toques la regla 16.** El reloj de solvencia es lo único que protege dinero
de verdad.

---

## Reglas de la casa

1. Rama `doctrina/que-pepe-la-siga`. `main` no se toca.
2. Verja encadenada, sin excepciones:

   ```powershell
   python scripts/run_validation_gate.py
   if ($LASTEXITCODE -eq 0) {
       git add -A
       git commit -m "doctrina: que pepe la siga"
   } else {
       git reset --hard origin/main
       Write-Host "VERJA EN ROJO - nada que subir"
   }
   ```

   Tú no empujas.
3. Ninguna guardia nueva lee `data/`. Ninguna función nueva cambia de forma según
   los datos.
4. `git status` antes de commitear, y en el informe qué entra.
5. No toques el workflow ni `MAX_SINGLE_SPECULATION_PERCENT`.
6. Termina cada commit con `Autor-real: Claude Code (VS Code)`.
7. Si la medición contradice el encargo —o la doctrina—, gana la medición.

---

## Informe

- qué decisiones citan regla y **cuáles no citan ninguna**;
- las dos comprobaciones: pujas visibles y recién ascendidos — sí/no y desde
  dónde;
- ¿suben más los recién ascendidos en nuestro histórico? Con muestra;
- qué encuentra la prensa sobre cesiones y traspasos de baratos;
- **el embudo de los 20**, por causa de muerte;
- Yamal, las dos columnas, si llegaste;
- qué reglas de la doctrina se contradicen con algo que ya habías medido;
- lo que no hiciste y por qué.
