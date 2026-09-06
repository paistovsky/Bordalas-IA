# ENCARGO — LA RAMPA

**Fecha:** 2026-09-14
**Rama:** `rampa/valorar-tener`
**Parte de:** el resultado de `docs/resultado-activar-2026-09-13.md`, donde el
despliegue se encendió y no fichó a nadie.

---

## El hallazgo que abre este encargo

El encargo anterior hizo lo correcto: encendió el despliegue, midió, y como
ningún objetivo compensaba, no compró. La regla 6 funcionó. Pero la conclusión
"ninguno compensa" depende entera de **qué se cuenta como ganancia**, y ahí hay
un hueco.

Estos son los números de la foto del 06/09, sin interpretar:

**Lo que rinde nuestra plantilla.** Catorce jugadores, 49.540.000 €. La suma de
sus `price_increment` diarios es **+30.000 €/día**: un **+0,06 % diario**.
Prácticamente parada. Y dentro hay cuatro que sangran: Jutglà −50.000 €/día
(−1,5 % diario sobre 3.350.000), Dituro −30.000, Djené −30.000, Mangala −30.000.

**Lo que rinde el mercado que estamos rechazando.** De los mismos 20 objetivos:

| Jugador | Precio | Ritmo | Racha |
|---|---:|---:|---:|
| Roro Riquelme | 4.240.000 | **+1,666 %/día** | 50 días |
| Amatucci | 3.670.000 | **+1,098 %/día** | 19 días |
| Gorosabel | 420.000 | +4,849 %/día | 4 días |
| Pedri | 15.350.000 | +0,305 %/día | 8 días |

**Lo que rinde el dinero parado.** 5.350.683 € en el bolsillo de fichar, al 0 %.

**La contradicción.** Amatucci fue rechazado, entre otras cosas, porque "como
especulación rinde un 1,3 %, por debajo del 3 % que exige la casa". Pero
Amatucci sube **1,098 % cada día** y lleva **19 días seguidos** haciéndolo.
Cruza el 3 % en menos de tres días.

Ese 1,3 % no es el rendimiento de tener a Amatucci. Es el rendimiento de
**comprarlo y revenderlo al Computer inmediatamente**: la prima de reventa,
mediana +1,72 %, menos costes. Es la única forma de ganar dinero que el modelo
sabe contar.

**Y eso es el hueco.** Pepe valora *comprar y revender*. No valora *tener*.
Pollo tiene 22 fichas y nosotros 14, y la diferencia de valor de plantilla son
35.520.000 € — que repartidos entre esas 8 fichas de más salen a ~3,5 M cada
una, exactamente el precio medio de un jugador. **La diferencia no es que Pollo
elija mejor. Es que Pollo tiene ocho activos más montados en la rampa y nosotros
tenemos ese dinero quieto.**

Ojo, dos honestidades antes de seguir:

1. Comprar a precio de mercado **no crea patrimonio en el instante**: convierte
   caja en activo. Solo paga si el activo sube o si el jugador puntúa en el once.
   Este encargo va de lo primero, y hay que demostrarlo, no suponerlo.
2. No sabemos si Pollo está apalancado. Su valor de plantilla de 85.060.000 € no
   dice nada de su caja, que puede estar en rojo. No copies su balance a ciegas.

---

## BLOQUE 1 — Medir si tener paga (esto primero, y manda)

**Retrotest sobre el histórico que ya tenemos.** El almacén de precios cubre 374
jugadores (`points_market.samples`). Con eso se puede responder la única pregunta
que importa:

> Si el día D compro un jugador cuyo precio sube a una tasa `r` con una racha de
> `n` días, y lo vendo `m` días después, ¿cuánto gano de verdad?

Recorre el histórico y publica la distribución del rendimiento realizado
—mediana, p25, p75, y el porcentaje de operaciones en pérdida— cortando por:

- tasa diaria `r` en tramos (< 0,25 %, 0,25–0,5 %, 0,5–1 %, > 1 %);
- racha `n` (1 día, 2 días, 3–7, más de 7);
- horizonte de venta `m` (1, 2, 3, 5, 7, 10 días).

**No inventes datos.** Si el histórico no da para una celda, esa celda sale
vacía y se dice. Un retrotest con celdas rellenadas a ojo es peor que no tenerlo.

Cruza el resultado con lo que ya está medido y no lo contradigas sin explicarlo:
momentum r = +0,90; el 83,8 % no se dan la vuelta en 6 días; un jugador que cae
vuelve a caer el 90,7 % de las veces; la continuación tiene su pico el día 2
(94,1 %) y baja el día 3 (73,8 %).

**El resultado de este bloque decide los dos siguientes.** Si tener no paga, se
escribe eso en el informe, no se toca nada más, y hemos aprendido lo más
importante del mes. Si paga, sigue.

---

## BLOQUE 2 — La vía TENER, en sombra y luego encendida

Si el bloque 1 dice que paga, añade una tercera vía de valoración junto a
`xi_upgrade_value`, `speculation_value` y `computer_resale_value`:

```
hold_value = precio × tasa_diaria × horizonte × P(continuación)
```

con estas condiciones:

1. **El horizonte no se inventa: sale del retrotest.** Usa el `m` que maximiza
   la mediana del rendimiento realizado, no el que da el número más bonito.
2. **`P(continuación)` sale de `route_confidence`**, que ya tiene las curvas
   medidas. Y como en la vía Computer, **el descuento se aplica a la ganancia,
   no al principal**. Esa lección ya costó una vez.
3. **Prohibido sumar la prima de reventa a la rampa.** El +1,72 % del Computer
   está medido contra el precio de mercado *de ese momento*; si el precio está
   subiendo, parte de esa prima **es** la rampa. Sumarlas es contar el mismo
   euro dos veces. Guardia obligatoria: `test_no_contar_dos_veces_v1`.
4. **Bolsillo:** una compra por la vía TENER es una operación de cartera, no un
   fichaje para el once. Va contra el bolsillo que le corresponda por
   `classify_operation`, y el listón que se le exige es el de **su propia vía** —
   la regla que estableciste ayer al arreglar `test_acquisition_wiring_v1`
   (bolsillo, listón y valor de la misma vía) se respeta sin excepción.
5. **Publica en sombra primero**, con las cuatro vías una al lado de la otra en
   cada objetivo, y **enciéndela en el mismo turno solo si el retrotest del
   bloque 1 la respalda con muestra suficiente**. Di en el informe cuál fue el
   corte de muestra que usaste y por qué.

---

## BLOQUE 3 — El listón del 3 %, con número en vez de decreto

`MIN_SPECULATION_YIELD = 0.03` y `MIN_SPECULATION_EXPECTED_VALUE = 25.000` son
cifras puestas a mano para evitar operaciones ruidosas. Puede que estuvieran
bien y puede que sean lo que nos tiene con 5,35 M parados.

**No las bajes por instinto.** Sustitúyelas por el número que salga del bloque 1:
el rendimiento por debajo del cual la operación pierde dinero después de
descontar la confianza de la vía. Si el retrotest dice que el 3 % era correcto,
déjalo en 3 % y escríbelo — un umbral confirmado por medición vale mucho más que
uno heredado.

**Cuidado con Soler.** La lección de aquella operación no era el rendimiento,
era la **concentración**: el 81 % del presupuesto en un jugador. `optimal_bid` se
prueba aislado y no ve el presupuesto; quien lo frena en producción es el tope
por operación. Si tocar el umbral pone en rojo
`test_la_especulacion_de_soler_ya_no_se_puja`, **no toques el test**: mira
primero si lo que has roto es la guardia de concentración por otra puerta.

---

## BLOQUE 4 — Dejar de tener lo que baja

Nuestra plantilla neta gana 30.000 €/día porque cuatro jugadores restan. Jutglà
pierde 50.000 € cada día y ya es el número 3 de la cola de ventas. Un jugador que
cae vuelve a caer el 90,7 % de las veces.

Añade a `sale_order` un tramo nuevo, por encima de los actuales:
**"cae de precio y no es titular"**. Con la misma lógica del freno que ya
impide comprar en rampa bajista, pero mirando hacia dentro. Y publica en el
dashboard una línea sola: **el ritmo neto de la plantilla en euros/día**. Quiero
poder mirar eso y saber si el dinero está trabajando o durmiendo.

No vendas nada automáticamente en este encargo. Ordena la cola y muéstrala.

---

## Reglas de la casa

Las de siempre, sin cambios:

1. Rama `rampa/valorar-tener`. `main` no se toca.
2. La verja encadenada, sin excepciones:

   ```powershell
   python scripts/run_validation_gate.py
   if ($LASTEXITCODE -eq 0) {
       git add -A
       git commit -m "rampa: valorar tener"
   } else {
       git reset --hard origin/main
       Write-Host "VERJA EN ROJO - nada que subir"
   }
   ```

   Tú no empujas. El push lo da el dueño.
3. **`git add -A` metió ayer un fichero suelto en el commit.** Antes de commitear,
   mira `git status` y di en el informe qué entra. Si hay algo que no es tuyo, no
   lo metas.
4. Mide contra `diagnostico/status.json`, no contra `data/` del disco.
5. No toques `.github/workflows/bordalas-live.yml`.
6. Cada arreglo, su guardia, con nombre de incidente real, en el estilo de la
   casa, y añadida a `scripts/run_validation_gate.py`.
7. **Si la medición contradice este encargo, gana la medición.** Ayer lo hiciste
   con Amatucci y estuvo bien hecho. Hazlo otra vez si toca: el bloque 1 puede
   perfectamente tumbar los bloques 2 y 3, y ese sería un buen resultado.

---

## Informe

En `docs/`, con:

- la tabla del retrotest completa, con las celdas vacías marcadas como vacías;
- el umbral que sustituye al 3 %, o la confirmación de que el 3 % era correcto;
- si encendiste la vía TENER y con qué muestra;
- qué compraría el primer ciclo con ella encendida: nombres, importes, bolsillos,
  saldo resultante;
- el ritmo neto de la plantilla en euros/día;
- lo que no hiciste y por qué.
