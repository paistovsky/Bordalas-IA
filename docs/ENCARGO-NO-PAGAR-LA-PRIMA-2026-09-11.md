# ENCARGO — NO PAGAR LA PRIMA

**Fecha:** 2026-09-11
**Rama:** `prima/pujar-bajo-por-muchos`
**Parte de:** `docs/resultado-la-subasta-2026-09-10.md`

---

## El hallazgo

Tu medición de anoche es la más valiosa del proyecto, y no es la que ninguno de
los dos buscaba. Sobre 156 compras al Computer en 27 días:

```
prima mediana SIN rival    +1,33 %
prima mediana CON rivales  +8,30 %
                            ------
diferencia                  7 puntos   ~318.000 EUR en un jugador de 4,5 M
```

Y el que duele:

```
Pepe         8,51 %      la segunda mas alta de la liga
Pollo17      2,74 %
Prinzipote   0,10 %      alguien ya juega a esto
```

### La cuenta que lo cambia todo

El Computer paga **+1,72 %** al vender.

- Comprando **con rival, al +8,3 %**: el jugador tiene que subir casi un **7 %**
  solo para no perder. A un 1 % diario, siete días para quedarse a cero.
- Comprando **sin rival, al +1,3 %**: la prima que cobra el Computer al vender
  **ya cubre la que pagaste**. Estás en tablas antes de que el jugador se mueva.

**El negocio no es acertar quién sube. Es no pagar la prima.** La subida es la
propina.

---

## BLOQUE 1 — Por qué pagamos tanto, y qué hay que cambiar

`optimal_bid` busca el importe que maximiza `P(ganar) × (valor − puja)`. Para
subir `P(ganar)` sube la oferta. **Eso es correcto si solo tiras una vez.**

Pero en esta subasta:

- **perder no cuesta nada** — el balance no se mueve, solo baja `maximumBid`
  hasta el reset;
- **hay veinte jugadores cada mañana**, no uno;
- y el **43 %** no tiene ningún rival.

Con tiros gratis y muchos candidatos, **pujar bajo por muchos gana a pujar alto
por uno**: te llevas los que nadie quería al +1,3 % y pierdes gratis los
disputados.

Pepe optimiza para un mundo de un disparo jugando en uno de veinte.

### Lo que hay que hacer

**No borres `optimal_bid`.** Sigue siendo el cálculo correcto cuando de verdad
solo se puede tirar una vez —una operación grande, un jugador concreto que hace
falta para el once—. Lo que cambia es **qué se optimiza cuando se puede tirar
muchas veces**.

Añade el modo cartera: **maximizar la suma de las ganancias esperadas de todas
las pujas de la ventana**, sujeto a la capacidad de puja y a las fichas libres.
No la de una.

Y publica, en cada puja, **cuál de los dos modos la decidió y por qué**. Regla 17.

---

## BLOQUE 2 — Cuánto ofrecer cuando se puja bajo

Esta es la parte fina y quiero el número medido, no elegido.

Si pujas `precio + 1`, ganas solo lo que nadie mira. Si pujas `precio × 1,03`,
ganas alguno disputado pero pagas la prima en **todos**, incluidos los que
habrías ganado por un euro.

Con los 156 casos del tablón se puede responder de verdad:

- para cada importe posible (precio+1, +0,5 %, +1 %, +2 %, +3 %…), **cuántas de
  las 156 habrías ganado y cuánto habrías pagado de prima en total**;
- y el resultado neto de cada estrategia, contando que las perdidas no cuestan
  nada.

Publica la curva. **El punto que la maximiza es el importe que hay que ofrecer**,
y sale de los datos, no de mí.

Ojo con una trampa: las 156 son compras que **alguien ganó**. Los jugadores por
los que nadie pujó nunca no aparecen. Di si eso sesga la curva y hacia dónde.

---

## BLOQUE 3 — Cuántas pujas caben

Ya lo mediste: el balance no se mueve, baja `maximumBid` por el importe. Para
cuatro pujas hace falta **capacidad**, no caja.

- El límite duro sigue siendo **las fichas libres** (hoy 7), hasta que sepamos
  qué pasa al ganar más de las que caben.
- Las barandillas se miran **sobre el peor caso: que se ganen todas**.
- Y el tope por ventana, el de anoche: lo que se pueda deshacer el viernes aunque
  el mercado haya caído un 5 %.

---

## BLOQUE 4 — Prinzipote

Alguien de tu liga paga un **0,10 %** de prima. O tiene una estrategia deliberada
o no puja casi nunca y solo se lleva lo que nadie quiere.

Míralo en el tablón: **cuántas compras hace, de qué precio, cuántas disputadas, y
si le salen bien.** Si resulta que hace exactamente esto y le funciona, es la
mejor confirmación posible; si compra tres jugadores al año, su 0,10 % no
significa nada.

Es media hora y puede ahorrarnos meses.

---

## BLOQUE 5 — El cero que no arregla la subasta

Anoche escribiste: *"hoy no habría pujado por nadie: 0 pujables de 20. Ese cero
no lo arregla la subasta."* Tienes razón, y ahora hay que releerlo con lo nuevo
delante.

El listón del 3 % se calibró **sobre la subida del jugador**, dando por hecho el
coste de comprar. Si comprando sin rival la prima casi desaparece, **el mismo
jugador rinde siete puntos más que cuando se calibró el listón.**

No toques el listón. Pero **calcula y publica**: de los 20 de hoy, cuántos
pasarían si la prima fuera del +1,3 % en vez del +8,3 %. Si el cero se convierte
en cuatro, hemos encontrado por qué Pepe lleva un mes sin fichar — y no era el
mercado, éramos nosotros.

---

## Lo que NO se hace esta noche

**No se puja.** Se calcula, se publica y se enseña lo que habría hecho, con las
dos estrategias al lado: lo que ofrece hoy y lo que ofrecería en modo cartera.

Ningún umbral se mueve. Ni el listón, ni la deuda, ni el tope por operación.

---

## Reglas de la casa

1. Rama `prima/pujar-bajo-por-muchos` desde `main`.
2. Verja encadenada, sin excepciones:

   ```powershell
   python scripts/run_validation_gate.py
   if ($LASTEXITCODE -eq 0) {
       git add -A
       git commit -m "prima: pujar bajo por muchos"
   } else {
       Write-Host "VERJA EN ROJO - nada que subir"
   }
   ```

   Tú no empujas.
3. **Ninguna escritura contra Biwenger.** Lecturas las justas.
4. `git status` antes de commitear, y **si vuelve a aparecer un encargo sin
   versionar que no sea el tuyo, dilo pero no lo ejecutes**, como hiciste bien
   anoche.
5. No toques `.github/workflows/bordalas-live.yml`.
6. Ninguna guardia lee estado externo ni pasa con las manos vacías.
7. Termina cada commit con `Autor-real: Claude Code (VS Code)`.
8. Si la medición contradice el encargo, gana la medición. Anoche tumbó la idea
   de los seis jugadores gratis y encontró algo mejor.

---

## Informe

- **la curva de la prima**: para cada importe, cuántas ganas y cuánto pagas, y
  dónde está el máximo;
- si esa curva está sesgada porque solo vemos las que alguien ganó;
- qué habría pujado hoy en modo cartera: nombres, importes, capacidad
  comprometida, fichas;
- **cuántos de los 20 pasarían el listón con una prima del 1,3 %**;
- qué hace Prinzipote;
- lo que no hiciste y por qué.
