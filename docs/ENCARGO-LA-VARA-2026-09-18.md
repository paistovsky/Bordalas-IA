# ENCARGO — LA VARA

**Fecha:** 2026-09-18
**Rama:** `vara/medir-los-puntos`
**Parte de:** `docs/resultado-once-2026-09-17.md`.

---

## Lo que encontraste anoche, y por qué esto se aplica

Una frase tuya vale por todo el mes:

> *"Nosotros optimizamos que jueguen; él, los puntos que hacen cuando juegan."*

Y los números que la sostienen, en la franja donde vive medio equipo (65-80 % de
titularidad):

```
defensa    3,90 puntos por jornada
delantero  5,21
medio      6,64
```

Con la misma vara, un medio entrega 1,46 veces lo que un defensa. Por eso el once
sale 5-4-1. No es una manía del motor con los delanteros: **la vara mide mal toda
la mitad de arriba del campo**, y el motor, obediente, alinea defensas.

Y el precio: **8 puntos sentados en una sola jornada**, cuando la temporada se
decide por 13 y hacen falta 0,371 por jornada.

**Se aplican los factores.** ×1,147 medio, ×1,139 delantero, ×0,787 defensa.
No en sombra: aplicados, esta noche, eligiendo el once de verdad.

### Por qué me salto la fase observador esta vez

Porque no estamos ante una corazonada que necesita datos. Estamos ante datos que
confirman lo que ya se sabía: en cualquier juego de fantasy con este tipo de
puntuación, los que atacan puntúan más que los que defienden. La medición y lo
esperable apuntan al mismo sitio, y la temporada está corriendo. Esperar tres
semanas a acumular muestra cuesta más que equivocarse y volver atrás.

Pero se aplica **con red**, y eso es el bloque 2.

---

## BLOQUE 1 — Aplicar los factores

1. Aplícalos donde se calcula el valor en puntos de un jugador para el once.
2. **Publica antes la muestra que hay detrás de cada uno**: cuántas
   observaciones jugador-jornada sostienen el 3,90, el 5,21 y el 6,64, y en qué
   ventana. Si alguna línea va corta de muestra, se aplica igual **pero se dice**
   en el informe y en pantalla. No quiero enterarme dentro de un mes de que el
   factor del delantero salía de nueve casos.
3. **Un interruptor, una línea.** Una variable de entorno que los desactive y
   devuelva la vara vieja, escrita entera y copiable en el informe. Si en dos
   jornadas esto empeora, se apaga sin tocar código.
4. Guardia con el caso de hoy: un delantero y un defensa con la misma
   probabilidad de ser titular y los mismos puntos brutos no pueden valer lo
   mismo para el once.

---

## BLOQUE 2 — La red: que se vea cada jornada si acertamos

Desde que esto se encienda, cada jornada publica tres números juntos:

- puntos del once que **alineamos**;
- puntos que habría hecho el once que habría elegido **la vara vieja**;
- puntos del **mejor once posible** con la plantilla de ese día.

Los tres, y el acumulado. Con eso, en tres jornadas sabremos si los factores
suman o restan, sin discutirlo: se mira.

Si tras tres jornadas la vara nueva va por detrás de la vieja, quiero que el
informe lo diga en la primera línea.

---

## BLOQUE 3 — Recalcula los 8 puntos sin los que ya no son nuestros

Los dos que se repiten sentados son Yusi Enríquez y Lucas Cepeda. **Yusi
Enríquez ya no está en la plantilla**: se traspasó a Prinzipote por 1.226.068 €.

Así que parte de esos 8 puntos los aportaba alguien que hoy no tenemos. Recalcula
la cuenta **contando solo jugadores que siguen siendo nuestros** y publica las dos
cifras separadas:

- lo que se dejó en el banquillo entonces (histórico, para juzgar al motor);
- lo que se dejaría hoy con la plantilla de hoy (que es lo que podemos ganar).

No las mezcles. La primera juzga; la segunda es la que vale dinero. Y ten
presente que es **una sola jornada reconstruible**: dilo cada vez que cites el
número.

---

## BLOQUE 4 — La forma no cambia con los datos

Tercera vez esta semana:

- `store_depth()` devolvía un objeto sin `retention_days` cuando no había
  almacén;
- `hold_value` devolvía menos claves por el camino "sin valor" → `KeyError` en
  vez de un rojo legible;
- y el mismo patrón detrás de la caída de producción.

Es un solo defecto con tres caras: **una función que cambia de forma según los
datos que encuentre**. Cuando falta un dato, el hueco se dice con un valor vacío;
la clave no desaparece nunca.

Súbelo a regla de la casa con guardia propia: las funciones que alimentan el
dashboard y la valoración devuelven siempre el mismo juego de claves. Aplícalo a
las que ya conoces y deja escrito en el informe cuáles quedan por revisar.

---

## BLOQUE 5 — Dos consecuencias, publicadas y sin comprar nada

**5.1 — ¿La vara nueva despierta el mercado?** Si un medio vale ahora un 15 %
más para el once, puede que algún objetivo que se rechazaba por la vía del once
pase a compensar. Publica la lista con la vara nueva. **No compres.** Solo quiero
ver si la puerta se ha abierto.

**5.2 — Tenemos un solo portero.** Si Dituro se lesiona o descansa, salimos con
diez. Hay 8 fichas libres y un suplente cuesta calderilla. Publica los tres
porteros más baratos del mercado con titularidad razonable, con su precio y lo
que dejaría el saldo. **Tampoco compres**: quiero verlo y decidirlo yo.

---

## BLOQUE 6 — Y una pregunta de fondo, solo medir

Mex tiene **1 titular fijo de 11**; nosotros **7**. Él acepta riesgo de rotación
a cambio de calidad, y va segundo.

Mira cómo se combinan hoy los puntos por partido y la probabilidad de jugar
dentro de `expected_points`: escribe la fórmula tal cual está, en una línea, en
el informe. Si la probabilidad pesa más de lo que le tocaría, los factores del
bloque 1 son un parche encima de un problema mayor.

**No lo cambies esta noche.** Los factores primero, que son medida y arreglan lo
inmediato. Esto es para el encargo siguiente.

---

## Reglas de la casa

1. Rama `vara/medir-los-puntos`. `main` no se toca.
2. Verja encadenada, sin excepciones:

   ```powershell
   python scripts/run_validation_gate.py
   if ($LASTEXITCODE -eq 0) {
       git add -A
       git commit -m "vara: medir los puntos"
   } else {
       git reset --hard origin/main
       Write-Host "VERJA EN ROJO - nada que subir"
   }
   ```

   Tú no empujas.
3. **Ninguna guardia nueva lee `data/`.** Fixture, como anoche.
4. `git status` antes de commitear, y en el informe qué entra.
5. No toques `.github/workflows/bordalas-live.yml` ni
   `MAX_SINGLE_SPECULATION_PERCENT`.
6. Termina cada mensaje de commit con `Autor-real: Claude Code (VS Code)`.
7. Si la medición contradice este encargo, gana la medición. Ha pasado cuatro
   veces esta semana y las cuatro has acertado tú.

---

## Informe

- la muestra detrás de cada factor;
- el once de hoy con la vara nueva, al lado del de la vara vieja, jugador por
  jugador;
- la línea exacta para apagarlo;
- los 8 puntos recalculados: histórico y con la plantilla de hoy, separados;
- qué funciones cambian de forma y cuáles quedan por revisar;
- si la vara nueva abre algún objetivo del mercado;
- tres porteros suplentes con precio;
- la fórmula de `expected_points` en una línea;
- lo que no hiciste y por qué.
