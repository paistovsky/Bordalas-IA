# ENCARGO — ENCENDER LA CALIDAD

**Fecha:** 2026-09-22
**Rama:** `calidad/encenderla` — **desde `pujas/leer-en-vez-de-adivinar`**, no
desde `main`, por lo que explicas abajo.
**Doctrina:** `docs/DOCTRINA.md` v1.4

---

## Lo de anoche

Tres cosas y las tres bien hechas.

**Las pujas no se pueden leer.** Ejecutaste, no salió, paraste a los dos
intentos. Cerrado en negativo y escrito en la doctrina: `rival_bid_model` se
queda y el desvío aleatorio también. **Un "no se puede" comprobado vale más que
un "quizá" abierto**, y me has ahorrado semanas de volver sobre ello.

**El 61,9 % circular.** Lo cazaste tú antes de publicarlo. Usar los puntos de
esta temporada para predecir los puntos de esta temporada habría sido el error
más caro del proyecto, porque habría parecido un éxito enorme. La cifra limpia
—19,1 % → 23,5 %— es modesta y es verdad.

**Y tu propio fallo en el reemplazo de los intocables.** La primera versión
desplazaba suplentes, que salen gratis, y con eso Yamal salía vendible en +0,70.
Corregido a desplazar titulares: −0,97. Tu frase —*"ya no hay lista debajo que
tape un error así"*— es exactamente el motivo por el que hay que tener cuidado
esta semana.

**Sobre la rama:** hiciste bien saliendo de `db5897a`. Yo dije `main` sin caer en
que el dueño no había fusionado. Sigue encadenando desde donde estés y dilo, como
has hecho.

---

## BLOQUE 1 — Yamal y la oferta viva, antes que nada

Encontraste una **oferta del Computer de 21.099.500 €** por Yamal, y los catorce
jugadores listados (Yamal a 33.480.000, +58 %).

Hoy a Yamal lo protege la lista de intocables. **En cuanto esto se fusione, quien
lo protege es tu cuenta nueva.** Así que antes de nada, con el código de tu rama
y los datos de hoy:

- corre la decisión sobre esa oferta concreta y **publica el veredicto y el
  número**;
- y compruébalo también con la lista ya retirada, que es como estará en
  producción.

Quiero leer, literal, "con la oferta de 21.099.500 € sobre la mesa, la decisión
es NO VENDER, neto −0,97". Si por lo que sea sale otra cosa, **para y avísame: no
lo fusionamos**.

Añade una guardia con este caso exacto, con la cifra de la oferta dentro. Es el
primer día en que un jugador de 21 millones depende de una cuenta y no de una
lista.

### Y una objeción del dueño que hay que meter en la cuenta

Dice, y tiene razón: **"muchos jugadores buenos tenemos que sacar por él, y no
hay tantos en la liga"**. Además Yamal ha hecho **17 puntos hoy**, muy por encima
de los 9,33 de media con los que hiciste el cálculo.

Dos cosas que comprobar en la cesta:

1. **¿Solo entraron jugadores realmente comprables?** Si la cesta se construyó
   con el ranking de la liga, incluye gente que **nadie vende**. Ya lo vimos con
   los porteros: los titulares valen 2,65-5,74 M y **ninguno estaba en venta**.
   Una cesta con jugadores inalcanzables no es una alternativa, es una fantasía,
   y hace que vender parezca menos malo de lo que es. Rehaz la cuenta solo con lo
   que se puede comprar hoy y publica las dos cifras.
2. **Rehazla con la media actualizada** incluyendo la jornada de hoy, y deja la
   guardia mirando la media viva, no un número congelado.

El dueño no quiere venderlo y la cuenta ya decía que no. Esto no es para
justificar la respuesta que nos gusta: es que **la escasez es una variable real
que la cesta puede no estar viendo**, y si no la ve, la cuenta está sesgada hacia
vender. Si al arreglarlo el margen se estrecha en vez de ampliarse, dilo igual.

**Y sobre los catorce listados:** el dueño quiere saber si eso lo decidió el
sistema o alguien. Explica en una línea qué los lista, a qué precio y con qué
criterio. No cambies nada.

---

## BLOQUE 2 — Encender la calidad medida (regla 6)

**Enciéndela.** 19,1 % → 23,5 % es modesto, pero la dirección es la que cualquiera
esperaría —los puntos que un jugador ha hecho predicen mejor que una etiqueta— y
la medición lo confirma. Igual que con los factores de posición: cuando lo
esperable y lo medido coinciden y la temporada corre, se enciende.

Con la misma red que aquella vez, y no negociable:

1. **Un interruptor de una línea**, escrito entero en el informe.
2. **El marcador de cada jornada**: puntos del once que alineamos, puntos del
   once que habría elegido la vara anterior, y puntos del mejor once posible.
   Acumulado incluido. Si a las tres jornadas la nueva va por detrás, el informe
   lo dice en la primera línea.
3. **Publica la advertencia en pantalla**: calibrada con tres jornadas, y con
   qué peso entra cada temporada.

**Ojo con el orden:** ya hay encendidos los factores de posición del 18/09. Esto
es un segundo cambio encima del primero antes de saber cómo fue el primero. Es
deliberado —la temporada corre— pero el marcador del punto 2 tiene que poder
separar los dos efectos. Si no puede, dilo y lo pensamos.

---

## BLOQUE 3 — Un dato, un nombre

Cuarta vez que aparece esta familia: `in_lineup` contra `is_starter`,
`store_depth()` sin `retention_days`, `hold_value` con claves de menos, y el
bloque que se calculaba antes de que existiera `roster`.

Ya pusiste la regla de que una función no cambia de forma según los datos. Falta
la hermana: **un concepto, un nombre**. Que el dato de "es titular" no se llame
de dos maneras según quién lo mire.

- Haz el inventario de los conceptos que viajan con más de un nombre entre el
  motor y el dashboard. Solo el inventario y el impacto de cada uno.
- Unifica **los que ya han causado un incidente**. Los demás, en la lista.
- Guardia que impida que un concepto ya unificado se vuelva a bifurcar.

No lo conviertas en una refactorización general. Cuatro incidentes justifican
cerrar cuatro puertas, no reescribir la casa.

---

## BLOQUE 4 — Lo que sigue pendiente, por orden

Si llegas. Si no, dilo y va al siguiente, como siempre.

1. **Balón parado** (regla 2) — sigue siendo el truco nº 1 del vídeo y sigue
   apagado. Está en `ENCARGO-QUIEN-ES-BUENO-2026-09-19.md`, bloque 3.
2. **La lista de la compra** (regla 10) — mismo encargo, bloque 5.
3. **Centrocampistas ofensivos** (regla 5) — separar el mediocentro del
   mediapunta con la calidad ya medida. **Solo publicar**, no aplicar: es un
   factor encima de otro factor.
4. **Las noticias de los baratos** — tercera noche pendiente. Caché diaria tras
   el reset de las 07:00, cruce prensa→jugadores.

**Amatucci no se toca.** +0,57 es una proyección contra una medición: no es una
operación, es movimiento.

---

## Reglas de la casa

1. Rama `calidad/encenderla`, desde donde estés encadenado. `main` no se toca.
2. Verja encadenada, sin excepciones:

   ```powershell
   python scripts/run_validation_gate.py
   if ($LASTEXITCODE -eq 0) {
       git add -A
       git commit -m "calidad: encenderla"
   } else {
       git reset --hard origin/main
       Write-Host "VERJA EN ROJO - nada que subir"
   }
   ```

   Tú no empujas.
3. **No respondas a ninguna oferta.** Ni la de Yamal ni ninguna otra.
4. No vendas, no compres, no listes, no deslistes.
5. Ninguna guardia nueva lee `data/`. Ninguna función nueva cambia de forma según
   los datos.
6. `git status` antes de commitear, y en el informe qué entra.
7. No toques el workflow ni `MAX_SINGLE_SPECULATION_PERCENT`.
8. Termina cada commit con `Autor-real: Claude Code (VS Code)`.
9. Si la medición contradice el encargo, gana la medición.

---

## Informe

- **el veredicto sobre la oferta de 21.099.500 € por Yamal, con la lista ya
  retirada**, y su guardia;
- qué lista los catorce jugadores, a qué precio y con qué criterio;
- la línea para apagar la calidad medida;
- si el marcador puede separar el efecto de los factores de posición del de la
  calidad;
- el inventario de conceptos con dos nombres, y cuáles unificaste;
- lo que no hiciste y por qué.
