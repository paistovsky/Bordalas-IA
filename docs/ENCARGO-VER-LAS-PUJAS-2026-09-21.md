# ENCARGO — VER LAS PUJAS

**Fecha:** 2026-09-21
**Rama:** `pujas/leer-en-vez-de-adivinar`
**Parte de:** `docs/resultado-doctrina-2026-09-20.md`
**Doctrina:** `docs/DOCTRINA.md` v1.3 (actualizada con tus hallazgos)

---

## Lo de anoche cambió el plan, y bien

Tres cosas tuyas mueven el rumbo:

1. **`marketShowBids = true`, encendido y gratis.** No hay monedas en esta liga.
   La información está y no la pedimos donde está.
2. **Cero de veinte mueren por el tope por operación.** Aflojarlo no habría
   comprado nada. Mi noche del bolsillo apuntaba a un freno que no frena.
3. **Yamal se queda.** La cesta que cabe con sus 21,21 M deja el once 2,93 puntos
   peor. Cerrado, y la regla 15 afinada: un activo grande solo se suelta si lo
   que entra **cabe en el once**.

Y la parte que más ha valido: **las cuatro decisiones sin regla**. Están las
cuatro escritas ya como reglas 19 a 22 en la doctrina. La 19 —qué hacer con las
ofertas que entran— es lo que más veces hace el ciclo y no lo gobernaba nada.

---

## BLOQUE 1 — Ejecuta la lectura de pujas. Autorizado.

Dejaste escrita la GET y no la ejecutaste porque te dije "solo mirar". Bien
hecho, y **ahora te autorizo**: es una **lectura** contra nuestra propia liga con
nuestras propias credenciales, de un dato que los ajustes ya nos exponen.

Condiciones, y son estrictas:

- **Solo GET.** Ni una escritura, ni una puja, ni un cambio de ajuste.
- **Nada de tocar el `.env` ni imprimir credenciales.** Usa el mismo camino de
  autenticación que ya usa producción, sin sacar el secreto de donde vive.
- **Empieza por un jugador**, mira qué devuelve, y pega la forma de la respuesta
  en el informe (con los nombres de los rivales, que no son secreto, pero sin
  ningún token).
- **Si no devuelve pujas, para.** No pruebes diez endpoints a ver si suena la
  flauta: escribe qué devolvió y lo pensamos.

**Si devuelve pujas**, entonces:

- **No borres `rival_bid_model` todavía.** Publica las dos cosas al lado: lo que
  el modelo estimaba y lo que la puja real dice. Una semana de eso y sabremos
  cuánto se equivocaba, que además es la mejor prueba de que la lectura es buena.
- Ojo con lo que significa para el desvío aleatorio de puja: si sabemos que nadie
  más va a pujar, sumar euros al azar es tirar dinero. Míralo, pero **no lo
  cambies todavía**: el desvío protege contra el caso en que sí hay rival.

---

## BLOQUE 2 — Lo que sigue pendiente y es lo más importante

**`docs/ENCARGO-QUIEN-ES-BUENO-2026-09-19.md` nunca se ha ejecutado.** Entró en
el commit de anoche como fichero, sin correr. Y cubre **tres de los siete trucos
que el dueño quiere**:

- la **calidad medida** en vez de la escalera de la etiqueta (la vara explica el
  20 % y ahí está el techo de todo lo demás);
- el **balón parado**, que es el truco nº 1 del vídeo y sigue apagado;
- el **portero suplente**, que sigue sin regla.

**Ejecútalo entero después del bloque 1.** Sigue vigente tal cual está escrito.
Si tienes que elegir entre el bloque 1 y éste, **elige éste**: las pujas son un
lujo, la calidad es el cimiento.

---

## BLOQUE 3 — Retirar los intocables (regla 22, derogada)

**El dueño retira la lista de intocables** que él mismo ordenó el 18/08. Pepe
puede vender a cualquiera si los números lo dicen.

Pero esto **no se borra sin mirar**, porque hay una guardia con su nombre en la
verja: `test_intocables_v1`. En esta casa las guardias llevan el nombre de un
incidente real.

1. **Léela primero y cuenta qué incidente encierra.** Si protege algo que no es
   la lista de nombres —una vuelta rara del ejecutor, una venta que no debía
   ocurrir— **eso se queda** aunque la lista se vaya. Escríbelo en el informe
   antes de tocar nada.
2. Publica **quién estaba en la lista** cuando la retires. Que quede en el
   registro a quién dejamos de proteger y desde cuándo.
3. Retira la lista y la guardia que la vigila, **deliberadamente**: no la
   silencies, quítala del `run_validation_gate.py` con una línea que diga que fue
   derogada el 21/09 y por quién.
4. **Y pon la que la sustituye.** No otra lista: la prueba que hicimos con Yamal.
   Antes de soltar un jugador que pese más de un 25 % de la plantilla o esté
   entre los tres que más puntúan, se calcula si **lo que entra cabe en el once**
   y el neto en puntos por jornada. Si el neto no es claramente positivo, no se
   vende. Con guardia y con el caso de Yamal dentro, que es el que la justifica.

Lo que se va es la protección por cariño. Lo que se queda es la protección por
aritmética, que además suelta al favorito el día que deje de rendir — cosa que
una lista de nombres nunca haría.

Siguen intactas: concentración del 35 %, cuatro por club, suelos de posición,
reloj de solvencia y disponibilidad.

---

## BLOQUE 4 — Rotar para comprar (regla 14)

Tu embudo lo dejó señalado: **Pedri, Roro y Amatucci valen más de lo que cuestan
y solo los frena la caja.** Eso es exactamente lo que hace Pollo: vende uno,
compra otro, mismo dinero girando.

Publica, **sin vender ni comprar nada**:

- para cada uno de los tres, qué habría que soltar para pagarlo, tomando la cola
  de ventas que ya existe;
- cuántos puntos por jornada pierde el once con lo que sale y cuántos gana con lo
  que entra — **el neto, que es lo único que importa**;
- y el mismo aviso que con Yamal: si el neto no es claramente positivo, no es una
  operación, es movimiento.

Con eso decidimos. **No lo automatices esta noche.**

---

## BLOQUE 5 — Las noticias de los baratos (regla 10), si llegas

Es el que dejaste ayer, y hiciste bien en dejarlo antes que entregar una versión
que enriquece 570 fichas cada media hora. Los dos avisos siguen en pie: **caché
diaria tras el reset de las 07:00**, y **cruce prensa → jugadores**, nunca al
revés.

Si esta noche no cabe otra vez, no pasa nada. Dilo y va al siguiente.

---

## Reglas de la casa

1. Rama `pujas/leer-en-vez-de-adivinar`. `main` no se toca.
2. Verja encadenada, sin excepciones:

   ```powershell
   python scripts/run_validation_gate.py
   if ($LASTEXITCODE -eq 0) {
       git add -A
       git commit -m "pujas: leer en vez de adivinar"
   } else {
       git reset --hard origin/main
       Write-Host "VERJA EN ROJO - nada que subir"
   }
   ```

   Tú no empujas.
3. **Solo lecturas contra Biwenger.** Ninguna escritura fuera del ciclo normal.
4. Ninguna guardia nueva lee `data/`. Ninguna función nueva cambia de forma según
   los datos.
5. `git status` antes de commitear. Si vuelve a aparecer un encargo sin versionar,
   méteo y dilo, como hiciste — está bien avisado.
6. No toques el workflow ni `MAX_SINGLE_SPECULATION_PERCENT`.
7. Termina cada commit con `Autor-real: Claude Code (VS Code)`.
8. Si la medición contradice el encargo, gana la medición.

---

## Informe

- qué devuelve la llamada de pujas, con la forma de la respuesta;
- si devuelve pujas: modelo estimado contra puja real, lado a lado;
- todo lo de `ENCARGO-QUIEN-ES-BUENO`: calidad medida con su varianza antes y
  después, balón parado, portero;
- **qué incidente encerraba `test_intocables_v1`**, quién estaba en la lista, y
  qué parte de esa guardia sobrevive;
- las tres rotaciones (Pedri, Roro, Amatucci) con su neto en puntos;
- lo que no hiciste y por qué.
