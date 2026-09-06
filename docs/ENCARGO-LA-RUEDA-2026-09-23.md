# ENCARGO — LA RUEDA

**Fecha:** 2026-09-23
**Rama:** `rueda/comprar-para-vender`
**Referencia:** `docs/PLAN.md` v2 y `docs/DOCTRINA.md` v1.5

---

## Lo que el dueño quiere

He visto los dos vídeos enteros y están volcados en la doctrina. El dueño lo
resume así, y es la estrategia general a partir de ahora:

> *"Da igual si mejoran el XI o no. Lo importante es fichar a los que van a
> revalorizarse para luego venderlos habiendo ganado dinero. Por eso es tan
> importante la intel: para adelantarnos al mercado."*

Son **dos juegos a la vez**, y hasta ahora Pepe solo jugaba uno:

- **el once**, que da los puntos;
- **la rueda**, que da el dinero — comprar al que sube, aguantar, vender al
  Computer, repetir.

Un jugador que no entra en el once **no es un descarte**: es materia prima de la
rueda. Eso es lo que hay que comprobar primero.

---

## BLOQUE 1 — ¿El filtro del once está matando la rueda?

**Antes que nada, y puede hacer sobrar la mitad del encargo.**

El embudo del 20/09: de 20 objetivos, **12 mueren por `NO_MEJORA_EL_ONCE`** y
cero por el tope.

La pregunta: cuando un jugador se descarta por esa causa, **¿se le sigue
evaluando por la vía de comerciar** (TENER, reventa al Computer), o el rechazo es
terminal?

- Los **doce casos, uno a uno**: nombre, precio, ritmo diario, y **por qué vías
  se le evaluó y con qué resultado en cada una**.
- Si alguno murió sin que la vía de cartera llegara a mirarlo, **ése es el
  hallazgo**: dilo en la primera línea del informe.

**No lo arregles esta noche.** Quiero la medición delante antes de tocar la ruta
de decisión: si el arreglo es de una línea me lo dices y lo hacemos mañana con
cuidado, porque es la ruta por la que pasa todo el dinero.

---

## BLOQUE 2 — ¿Cuánto puede dar la rueda?

Nadie lo ha calculado, y decide cuánto esfuerzo merece todo lo demás.

Con lo que ya está medido:

```
fichas libres            8          (cota inferior, no objetivo)
ciclo                    3 dias     (el horizonte que maximiza la mediana)
rendimiento por op.      +4,47 %    (tramo >1 %/dia, racha corta, n=142)
operaciones en perdida   5 %
salida                   Computer, +1,72 % sobre mercado, 78 % de las veces
bolsillo especular       2.433.987 EUR  + la deuda autorizada
```

**Un número al mes**, con la cuenta al lado. Y el rango, no solo el punto medio:
qué pasa si el rendimiento real es la mitad.

Los límites que no se pueden esconder:

- **cada operación ocupa una ficha** — la rueda tiene un tamaño máximo físico;
- **el capital tiene techo**, y la deuda también;
- **el +4,47 % se midió en una sola semana de agosto**, la más rara del año.

Si el número sale pequeño, dilo. Sería un resultado buenísimo: nos ahorraría
semanas de construir una rueda que no da para nada.

---

## BLOQUE 3 — Volumen contra margen, con el retrotest

Pollo hizo **52 pujas**; Pepe, **1**. El vídeo describe muchas operaciones con
margen fino; nosotros exigimos un 3 % por operación.

El tramo `1-2 %/día` rinde **+1,80 %** y está apagado por no llegar al listón.
Con volumen, muchos +1,80 % componen.

Simula con el retrotest, **con nuestro capital y nuestras ocho fichas**:
cartera de muchas operaciones finas contra pocas gruesas. Rendimiento mensual,
operaciones en pérdida, y capital inmovilizado de cada estrategia.

**No muevas el 3 %.** Publica el resultado y decide el dueño. Si el volumen no
gana, el 3 % queda confirmado por segunda vez y también es una respuesta.

---

## BLOQUE 4 — La deuda de lunes a jueves

El reloj de solvencia funciona y **nunca se ha usado**: Pepe está `SIN_DEUDA` con
saldo positivo y jamás se ha puesto en rojo, teniendo permiso desde hace semanas.

Comprueba una cosa concreta: **¿hay algo que impida comprar en rojo de lunes a
jueves?** Un guardarraíl que exija saldo positivo *hoy* en vez de a T−6 h haría
inútil todo el permiso. Si existe, señálalo y **no lo toques**.

---

## BLOQUE 5 — Balón parado, si llegas

Cinco noches aplazado, y sigue siendo el truco nº 1 de un vídeo y el nº 5 del
otro. `ENCARGO-QUIEN-ES-BUENO-2026-09-19.md`, bloque 3, sigue vigente entero.

Con el matiz del segundo vídeo: **el valor está en el lanzador barato**, no en el
crack que además los tira. *"A Salah no lo fichas por los penaltis; Kluivert
metió seis, tres en un partido, y es mucho más barato."* Ordena por puntos de
balón parado **partido por el precio**.

---

## Reglas de la casa

1. Rama `rueda/comprar-para-vender`. `main` no se toca.
2. Verja encadenada, sin excepciones:

   ```powershell
   python scripts/run_validation_gate.py
   if ($LASTEXITCODE -eq 0) {
       git add -A
       git commit -m "rueda: comprar para vender"
   } else {
       git reset --hard origin/main
       Write-Host "VERJA EN ROJO - nada que subir"
   }
   ```

   Tú no empujas.
3. **Esta noche no se enciende la rueda ni se mueve ningún umbral.** Se mide y se
   propone. Los bloques 1 y 2 pueden cambiar el plan entero y no quiero
   construir encima de una suposición.
4. No vendas, no compres, no respondas ofertas.
5. Ninguna guardia nueva lee `data/`. Ninguna función nueva cambia de forma según
   los datos.
6. `git status` antes de commitear, y en el informe qué entra.
7. No toques el workflow ni `MAX_SINGLE_SPECULATION_PERCENT`.
8. Termina cada commit con `Autor-real: Claude Code (VS Code)`.
9. Si la medición contradice el encargo, gana la medición.

---

## Informe

- **los doce `NO_MEJORA_EL_ONCE`**, uno a uno, y si la vía de cartera llegó a
  mirarlos;
- **cuánto puede dar la rueda al mes**, con la cuenta y el rango;
- volumen contra margen: rendimiento, pérdidas y capital inmovilizado de cada
  una;
- si hay algo que impida comprar en rojo entre semana;
- balón parado, si llegaste;
- lo que no hiciste y por qué.
