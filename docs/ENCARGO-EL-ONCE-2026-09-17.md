# ENCARGO — EL ONCE

**Fecha:** 2026-09-17
**Rama:** `once/puntos-en-el-banquillo`
**Parte de:** `docs/resultado-arbitro-2026-09-16.md`.

---

## Lo primero: me equivoqué, y hay que decirlo entero

Las cuatro últimas noches han salido de una tesis mía, y la tesis era falsa.

Yo dije: *Pollo despliega capital parado, ocupa fichas vacías, sube patrimonio, y
por eso nos gana. Cópiale.* De ahí salieron el encargo de activar, el de la
rampa y el del bolsillo.

El árbitro la ha desmontado en tres piezas:

1. **Pollo no despliega caja parada. Rota.** Compró 21.198.020 € y vendió
   21.259.800 € (Vinícius y Foyth). Casi al euro. No es un acumulador con
   dinero fresco: es un tradeador con el mismo dinero dando vueltas.
2. **La brecha no era 35,5 M. Es 18,3 M.** Su plantilla cayó a 67,84 M al soltar
   a Vinícius. La mitad de la alarma era un cromo caro que ya no tiene.
3. **Y lo importante: el valor de plantilla no explica los puntos.** r = +0,553
   cuando con siete equipos hace falta 0,754. **Mex va segundo con nuestras
   mismas catorce fichas y una plantilla como la nuestra.**

Ese tercer punto tumba el motivo entero. Llevo cuatro noches empujando hacia
"sube patrimonio o no ganamos" y la liga dice que el patrimonio no es lo que
gana. Lo que gana son los puntos, y los puntos los marcan **once** jugadores.

**La máquina de comerciar que has construido no se toca ni se apaga.** Está
medida, funciona dentro de muestra y algún día pagará el once. Simplemente no es
la palanca de la liga, y yo la traté como si lo fuera.

## Y la cuenta que hay que tener delante

```
13 puntos de diferencia  ÷  35 jornadas  =  0,371 puntos por jornada
```

No hace falta un equipo nuevo. Hace falta sacarle a Pollo **cuatro décimas de
punto por jornada**. Si nuestro once está dejando puntos en el banquillo, ahí
está la liga entera.

---

## BLOQUE 1 — Cuántos puntos hemos dejado en el banquillo

Esta es la medición de la noche, y es la más importante que se ha pedido.

Para cada jornada jugada:

- los puntos que hizo **el once que alineamos**;
- los puntos que habría hecho **el mejor once posible con la plantilla que
  teníamos ese día**, respetando formaciones legales;
- la diferencia: **los puntos que se quedaron sentados**.

Y el total acumulado. Ese número, comparado con los 13 de diferencia y con las
0,371 por jornada, dice de una vez si el problema está en el mercado o en la
alineación.

**No lo maquilles.** Si sale que el once es casi óptimo y sólo dejamos una décima
por jornada, se escribe y se cierra el asunto: entonces el problema está en la
calidad de la plantilla y volvemos al mercado con otra cabeza. Si sale que
dejamos tres o cuatro puntos por jornada, hemos encontrado la liga.

Si el histórico no permite reconstruir la plantilla de aquel día, dilo y mide
sólo las jornadas que sí se puedan. Media medición honesta vale; una entera
inventada, no.

---

## BLOQUE 2 — ¿Acierta el motor al predecir puntos, y acierta igual en todas las
posiciones?

El once se elige por `expected_points`. Nunca hemos comprobado si ese número
acierta.

Para cada jugador y jornada jugada, compara `expected_points` con los puntos
reales. Publica el error medio **y, sobre todo, el error medio por posición**:
portero, defensa, medio, delantero.

**La sospecha concreta**, que viene del propio dueño mirando la pantalla: el once
salió **5-4-1**, con el suelo de delanteros en 2, y **Pablo Durán con un 70 % de
titularidad estaba en el banquillo mientras defensas con ese mismo 70 %
jugaban**. Si el motor infravalora sistemáticamente a los delanteros, alinea
defensas, y eso cuesta puntos cada jornada sin que nadie lo note.

Si hay sesgo por posición, **no lo corrijas esta noche con un factor a ojo**.
Mídelo, publícalo, y propón la corrección con su número. La decisión es del
dueño.

---

## BLOQUE 3 — Mex, que es el que hay que estudiar

Hemos pasado un mes mirando la cartera de Pollo. El equipo que hay que mirar es
**Mex**: segundo, 141 puntos, **14 fichas** —las mismas que nosotros— y
52.250.000 € de plantilla contra nuestros 49.540.000. Prácticamente el mismo
equipo en dinero y en tamaño, ocho puntos por delante.

Con lo que el tablón y el centro de liga permitan ver, y **sin inventar lo que no
se vea**:

- ¿En qué se diferencia su once del nuestro? Reparto por posiciones, formación.
- ¿Cuántos de sus once son titulares fijos en su equipo real, contra los
  nuestros?
- ¿Ha movido mercado, o está quieto y ganando?

Si Mex está quieto y va segundo con nuestro mismo presupuesto, la lección no está
en comprar mejor: está en alinear mejor. Y si resulta que no se puede ver lo
suficiente de su plantilla, dilo — es un resultado válido y prefiero saberlo a
leer una comparación hecha con huecos.

---

## BLOQUE 4 — Que la pantalla deje de contar la película vieja

1. **La brecha de plantilla dice 35,5 M y son 18,3 M.** Corrígelo.
2. **Junto a esa cifra, la advertencia:** r = +0,553 con n = 7, por debajo del
   0,754 que haría falta. Una línea en cristiano: *"el valor de plantilla no
   predice los puntos en esta liga con los datos que hay"*. Que nadie —yo el
   primero— vuelva a montar una estrategia encima de ese número.
3. **Sube el marcador de puntos dejados en el banquillo** (bloque 1) a donde se
   vea sin buscarlo. Si esa cifra crece, es la alarma más importante del
   tablero.

---

## BLOQUE 5 — Dos cosas cortas

**El libro de rechazos.** Arrancó ayer y el veredicto A está calibrado sobre los
mismos datos que fijaron los cortes: coherencia interna, no predicción. Lo dijiste
tú y está bien dicho. **No lo vuelvas a tocar esta noche.** En tres días tendrá
muestra y entonces se lee.

**Las identidades de git.** Tienes razón en que es un riesgo: tus commits y los
míos son indistinguibles. No lo arregles tú desde dentro del repositorio — es
configuración de la máquina del dueño y se la explico yo.

---

## Reglas de la casa

1. Rama `once/puntos-en-el-banquillo`. `main` no se toca.
2. Verja encadenada, sin excepciones:

   ```powershell
   python scripts/run_validation_gate.py
   if ($LASTEXITCODE -eq 0) {
       git add -A
       git commit -m "once: puntos en el banquillo"
   } else {
       git reset --hard origin/main
       Write-Host "VERJA EN ROJO - nada que subir"
   }
   ```

   Tú no empujas.
3. `git status` antes de commitear, y en el informe qué entra.
4. Mide contra `diagnostico/status.json`.
5. No toques `.github/workflows/bordalas-live.yml` ni
   `MAX_SINGLE_SPECULATION_PERCENT`.
6. **Esta noche tampoco se mueve ningún umbral.** Ni los del mercado ni los del
   once. Se mide y se propone.
7. Si la medición contradice el encargo, gana la medición. Ya ha pasado tres
   veces esta semana y las tres veces has acertado tú.

---

## Informe

- puntos dejados en el banquillo, por jornada y acumulado, contra los 13 de
  diferencia;
- error de `expected_points` global y **por posición**;
- si hay sesgo contra los delanteros, y qué corrección propones con su número;
- qué se ve del once de Mex y en qué se diferencia del nuestro;
- lo que no se pudo medir y por qué;
- lo que no hiciste y por qué.
