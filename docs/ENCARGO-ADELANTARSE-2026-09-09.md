# ENCARGO — ADELANTARSE AL MERCADO

**Fecha:** 2026-09-09
**Rama:** `intel/adelantarse-al-mercado`
**Doctrina:** regla 10 · **Vídeo:** truco nº 7, el que su autor llama "el más
importante"

---

## Lo que pide el dueño

> *"Es importantísimo adelantarse al mercado con intel externa. Pepe ha de saber
> a quién hay que fichar porque va a subir."*

Hoy Pepe sabe **quién está subiendo**. No sabe **quién va a subir**. Sus tres
fuentes publican movimiento ya ocurrido —lo dice su propio aviso: *"Movimiento
OBSERVADO, no pronóstico"*— y la rampa, por definición, llega tarde: cuando un
jugador lleva días subiendo, media subida ya pasó.

Lo que falta es lo del vídeo: *"uno del Getafe que vale 200.000; me informo y pone
que el Málaga lo busca. Ésos son los que te dan la pasta."*

---

## BLOQUE 0 — Dónde está nuestra ventaja

El dueño conoce a sus rivales y lo dice sin rodeos:

> *"Ellos se informan y leen sobre noticias de la liga, probablemente en webs tipo
> FutbolFantasy. Por eso fichan a gente que saben que va a subir. Tenemos que ser
> mejores que ellos en eso."*

Eso da por buena la premisa, y cambia la pregunta. **Leer las mismas webs nos
empata, no nos adelanta.** Lo que nos puede hacer mejores son tres cosas que un
humano no tiene:

1. **Velocidad.** Pepe mira cada hora. Ellos, cuando se acuerdan. Una noticia de
   las 11:40 se puede aprovechar a las 12:07.
2. **Cobertura.** Ellos leen los titulares que les llaman la atención. Pepe puede
   cruzar los **521** de la liga, incluidos los de 150.000 € que nadie mira.
3. **Memoria — y ésta es la buena.** Un humano lee *"el Málaga busca a fulano"* y
   decide a ojo. Nosotros podemos saber **qué pasó las cincuenta veces anteriores
   que salió esa clase de noticia.** Si "interés de otro club" mueve el precio un
   8 % el 60 % de las veces y "renovación" no lo mueve nada, ellos siguen
   adivinando y nosotros no.

Por eso el libro de acierto del bloque 4 **no es una precaución lenta: es la
pieza que nos hace mejores que ellos.** Constrúyelo como si fuera el producto,
no como si fuera un test.

### Una comprobación que sigue mereciendo la pena

Coge las siete compras de Pollo —Gerard Moreno, Pubill, Natan, Bardeli,
Camavinga, Ratkov, Riki Rodríguez— y mira si hubo noticia en los días previos.
No para dudar del dueño, sino para **saber qué clase de noticia mueve a un rival
a comprar**: si las siete llevaban detrás un "vuelve de lesión", ya sabemos qué
mirar primero.

Si el archivo de prensa no llega tan atrás, dilo y sigue.

---

## BLOQUE 1 — Qué hay ya, antes de escribir una línea

Existen `src/intelligence/news.py` y `transfers.py`, y **están vivos en la ruta
de pujar** — casi los borro un día creyéndolos muertos. Y existe el ojeador de
prensa con MARCA, MD y Relevo.

Dime, en una lista corta: **qué traen hoy, para qué jugadores, y si algo de eso
llega a decidir algo.** Puede que media pieza ya esté hecha y no lo sepamos.

---

## BLOQUE 2 — El cruce: noticias contra los 521

La pieza nueva. Dos avisos de ingeniería que no son negociables, porque hacerlo
al revés revienta el ciclo y acabamos de salir de un bloqueo por exceso de
peticiones:

1. **Se lee el flujo de noticias una vez y se busca a quién menciona.** Nunca
   jugador por jugador preguntando a la prensa: eso son 570 peticiones para nada.
2. **La ficha completa de los ~570 se construye una vez al día**, después del
   reset de las 07:00, y se guarda. Cada vuelta solo refresca lo del escaparate.

Y lo que lo hace útil de verdad: **se cruza contra los 521 de la liga, no contra
los 47 del escaparate.** La noticia buena aparece *antes* de que el jugador salga
al mercado. Si solo miramos el escaparate, llegamos tarde otra vez.

**Sin filtrar por precio.** El vídeo insiste en mirar hasta los de 150.000, y es
justo donde dice que está el dinero.

---

## BLOQUE 3 — Qué clase de noticia, porque no todas valen

No sirve un titular cualquiera. Clasifica y publica la clase, que es lo que
después permite medir cuál predice:

- **cesión o traspaso** — se va a otro equipo
- **interés de otro club** — le buscan, todavía no está cerrado
- **vuelve de lesión** o **se lesiona**
- **cambio de entrenador** en su club
- **renovación** o salida en el aire

Cada aviso lleva **titular, fuente y fecha**. Sin eso no es información, es un
rumor sin dueño.

---

## BLOQUE 4 — El libro de acierto. Esto es el producto.

**No es un test de seguridad: es lo que nos hace mejores que un rival que lee las
mismas webs.** Trátalo con esa importancia.

Para cada aviso publicado, guarda **el precio del jugador ese día** y luego **a 1,
3 y 7 días**. Y agrégalo **por clase de noticia**, que es lo que de verdad
contesta la pregunta:

- ¿cuántas veces movió el precio cada clase, y cuánto?
- ¿en qué dirección, y con qué porcentaje de fallo?
- ¿cuánto tarda en moverse? Si tarda dos días, hay margen para entrar; si se mueve
  en dos horas, llegar el primero es lo único que importa.

Ese último número decide si merece la pena mirar cada hora o basta una vez al día.

Es el mismo libro que ya puntúa a FutbolFantasy con Brier. Reutiliza lo que haya y
publícalo en pantalla desde el primer día, aunque al principio esté vacío: quiero
verlo llenarse.

---

## BLOQUE 5 — Cómo entra en las decisiones. Con cuidado.

**Fase 1, ahora: la noticia NO crea compras.** Solo ordena. Entre los candidatos
que ya pasan el listón por su cuenta, los que tienen noticia van primero. Si un
jugador no pasa el listón, la noticia no lo mete.

**Fase 2, cuando el libro diga que predice:** entonces sí, la noticia entra en el
cálculo del ritmo esperado, con el peso que diga la medición. **No antes.**

Sé que el dueño tiene prisa y que esto parece lento. Pero encender una señal sin
saber si acierta es exactamente cómo se pierde dinero rápido, y llevamos una
semana demostrando que la mitad de lo que damos por bueno resulta ser falso al
medirlo. La fase 2 puede llegar en dos semanas si la fase 1 arranca hoy.

---

## BLOQUE 6 — El coste, medido

Cuántas peticiones al día añade todo esto, con tu sonda. **Las noticias no van
contra Biwenger** —son webs externas—, pero el presupuesto es el presupuesto:
venimos de 1.536 al día, estamos en 349, y no quiero enterarme del número cuando
nos vuelvan a bloquear.

Si tu diseño sube de 400 al día, para y dímelo antes de seguir.

---

## Reglas de la casa

1. Rama `intel/adelantarse-al-mercado` desde `main`. `main` no se toca.
2. Verja encadenada, sin excepciones:

   ```powershell
   python scripts/run_validation_gate.py
   if ($LASTEXITCODE -eq 0) {
       git add -A
       git commit -m "intel: adelantarse al mercado"
   } else {
       Write-Host "VERJA EN ROJO - nada que subir"
   }
   ```

   Tú no empujas.
3. **Ninguna llamada extra a Biwenger.** Las fuentes de prensa sí, con cabeza.
4. No compres, no vendas, no respondas ofertas. Ningún umbral se mueve.
5. Ninguna guardia lee estado externo: ni disco, ni red, ni reloj. Y ninguna pasa
   con las manos vacías — si comprueba algo sobre una lista, exige primero que la
   lista no esté vacía.
6. `git status` antes de commitear, y en el informe qué entra.
7. No toques `.github/workflows/bordalas-live.yml`.
8. Termina cada commit con `Autor-real: Claude Code (VS Code)`.
9. **Si la medición contradice el encargo, gana la medición.**

---

## Si no llegas a todo

Haz los bloques 1, 2 y 4: qué hay ya construido, el cruce contra los 521, y el
libro de acierto. Esos tres son la pieza. El resto puede esperar a mañana.

Y sobre las fuentes: **empieza por las que el dueño dice que leen sus rivales**
—FutbolFantasy y las de su familia—, que además ya las visitamos cada vuelta.
Añadir MARCA o Relevo encima está bien, pero primero hay que leer lo que leen
ellos.

---

## Informe

- **¿tenían noticia detrás las compras de Pollo?** Cuántas de siete, cuáles, y
  de qué clase era cada una;
- qué traen hoy `news.py`, `transfers.py` y el ojeador de prensa, y si deciden
  algo;
- cuántos de los 521 tienen alguna noticia hoy, por clase;
- los tres o cuatro avisos más interesantes de hoy, con titular, fuente y fecha;
- cuántas peticiones al día añade;
- lo que no hiciste y por qué.
