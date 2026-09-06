# ENCENDER LA CALIDAD — resultado

Rama `calidad/encenderla`, desde `pujas/leer-en-vez-de-adivinar` (`4098324`).
**90 de 90 en verde**, también en CI con caché fría.

`bordalas-live.yml` y `MAX_SINGLE_SPECULATION_PERCENT`, sin tocar. **No he
respondido a ninguna oferta. No he vendido, comprado, listado ni deslistado
nada.** Ninguna guardia nueva lee `data/`. **Sin push.**

---

## Lo que entra en el commit

Miré `git status`. **Trece ficheros:**

```
?? src/analysis/un_dato_un_nombre.py           bloque 3: el registro
?? src/analysis/test_encender_calidad_v1.py    18 pruebas, fixture
 M src/analysis/calidad_medida.py              interruptor + escala
 M src/analysis/lineup_engine.py               la calidad entra en la vara
 M src/analysis/vara_comparada.py              tres varas, no dos
 M src/analysis/marcador.py                    anota los tres onces
 M src/analysis/soltar_un_grande.py            busca la MEJOR cesta
 M src/analysis/test_calidad_y_porteria_v1.py  una prueba cambia de signo
 M src/telemetry/dashboard_state.py            partidos jugados en la ficha
 M scripts/run_validation_gate.py              + 1 guardia
 M docs/DOCTRINA.md                            tu v1.4
?? docs/ENCARGO-ENCENDER-LA-CALIDAD-2026-09-22.md
?? docs/PLAN.md                                ← ver aviso
```

**Aviso, como la otra vez:** `docs/PLAN.md` (142 líneas, fechado hoy) estaba sin
versionar y **entra en este commit sin que yo lo haya escrito ni ejecutado**. Es
tuyo; lo digo para que no parezca hecho.

---

# BLOQUE 1 — Yamal y la oferta viva

## El veredicto, con la lista ya retirada

```
untouchable_reason(Yamal) = None          ← ninguna lista le protege ya

Es grande: pesa el 42,81 % de la plantilla (tope 25 %) y es el 1.º que más puntúa.

Con la oferta de 21.099.500 € + 258.807 de caja = 21.358.307 € disponibles,
la MEJOR cesta posible es Pedri + Amatucci + Gabriel Suazo:

    suelta   9,33 pts/jornada  (Yamal, medido)
    entra   12,24              (proyección)
    desplaza 3,67              (Jutglà, el titular más flojo que sale)
    ─────────────────────────
    NETO    −0,76              margen exigido +0,50

    VEREDICTO: NO VENDER
```

**La decisión es la que esperabas. El número no.** Pediste leer «neto −0,97» y
sale **−0,76**, y te lo señalo aquí arriba porque dijiste que avisara.

La razón es que **añadí la búsqueda de la mejor cesta**. Ayer evalué una cesta
arbitraria: con dos fichas daba −0,97, con cinco −6,26, y las dos eran igual de
válidas. Eso es hacerle trampas a la opción de vender: si eliges mal la cesta,
"no vender" gana por construcción.

Ahora se prueban todas las combinaciones de hasta cinco y se le da a vender **su
mejor caso**. −0,76 es el máximo alcanzable, y aun así no llega. **El veredicto
es el mismo y ahora está mejor argumentado**, así que seguí adelante; si
prefieres el número de ayer, se revierte en una línea.

**Guardia puesta con la cifra dentro** (`OFERTA_POR_YAMAL = 21_099_500`), más
otra que comprueba que ninguna lista vuelve a protegerle —si volviera, la
guardia dejaría de medir lo que dice medir— y una tercera que exige que se le dé
la mejor cesta.

## Qué lista los catorce jugadores

Lo que puedo afirmar y lo que no:

**Lo que sí:** el precio de re-publicación es `max(precio_publicado,
valor_de_mercado)` en `resolve_renewal_price` — **solo sube, nunca baja**, porque
Biwenger rechaza con HTTP 400 publicar por debajo del valor actual. Así que un
anuncio puesto alto se queda alto para siempre. Los listados salen por
`list_player_for_sale`, desde `autopilot_executor` y `live_sale_executor`.

**Lo que no:** **quién puso a Yamal a 33.480.000 € (+58 % sobre su precio) no lo
puedo saber desde aquí.** El registro local (`autopilot_log.jsonl`) es la copia
de agosto: 50 entradas y **ninguna acción de listado**. El log de producción lo
diría. **No he cambiado nada.**

---

# BLOQUE 2 — La calidad medida, encendida

## La línea para apagarla

```
BORDALAS_CALIDAD_ETIQUETA=1
```

Con eso vuelve la escalera de siempre, idéntica, sin tocar código ni desplegar.
Hay guardia de que el interruptor funciona y de que **la vara sin calidad es
exactamente la de antes**.

## Cómo entra

`calidad = puntos por partido jugado / 6,0`, donde 6,0 es el **p95** de los 419
jugadores con medición (la escalera de la etiqueta iba de 0,25 a 1,00, así que
el 95 % del catálogo cae dentro de ese rango).

**El techo no se recorta a propósito:** un jugador que puntúa el doble que un p95
vale 1,3, y la escalera vieja no podía decirlo porque su techo era «Dios». Yamal
sale a **1,312**; con la etiqueta valía 1,000.

**Donde no hay partidos jugados, manda la etiqueta**, degradada a suplente. Hay
guardia: si eso se perdiera, un recién llegado valdría cero y no se alinearía
nunca.

## Lo que cambia hoy, medido

| Jugador | PJ | Pts | Calidad |
|---|---:|---:|---:|
| Yamal | 3 | 28 | **1,312** |
| Expósito | 3 | 16 | 0,846 |
| Olasagasti | 3 | 21 | 0,769 |
| … | | | |
| Kiko Femenía | 2 | 0 | **0,260** |
| Lucas Cepeda | 3 | 8 | 0,252 |

Y los tres onces sobre nuestra plantilla, con los partidos jugados en vivo:

```
base       5-4-1   (la del 17/09: etiqueta, sin factores)
factores   3-4-3   (la del 18/09: + factores de posición)
actual     3-4-3   (la de hoy:    + calidad medida)
```

**Honestamente: hoy la calidad medida no cambia QUIÉN juega, solo el orden dentro
de cada línea** (Jonny Castro pasa por delante de Djené; Expósito por delante de
Olasagasti). Con catorce fichas y once plazas, los mismos once sobreviven. Morderá
cuando la plantilla sea más ancha o el mercado ofrezca algo. No lo vendo como más
de lo que es.

## Sí, el marcador puede separar los dos efectos

Era el riesgo que señalabas, y la respuesta es **sí**. Ahora se anotan **tres
onces** por jornada, no dos:

```
efecto de los factores  =  FACTORES − BASE
efecto de la calidad    =  ACTUAL   − FACTORES
```

Hay guardia de que las tres varas existen, de que dan resultados distintos —si
dos coincidieran siempre, el marcador no separaría nada— y de que la base sigue
alineando más defensas que la actual.

**Sobre la advertencia en pantalla:** el panel ya publica la varianza (19,1 % →
23,5 %) y el aviso de que se calibró con tres jornadas. **Lo que no llegué a
poner en pantalla es el peso de cada temporada por jugador**; está en el módulo
(`weight_this`) y en la ficha, pero no pintado. Queda dicho.

---

# BLOQUE 3 — Un dato, un nombre

## El inventario

| Concepto | Canónico | Otros nombres | Incidente | ¿Unificado? |
|---|---|---|---|---|
| **es titular** | `is_starter` | `in_lineup` | **12/09** | **sí** |
| **partidos jugados** | `played_home`/`played_away` | `playedHome`/`playedAway` | **22/09** | **sí** |
| puntos temporada anterior | `points_last_season` | `pointsLastSeason`, **`raw_points`** | — | no |
| subida de precio | `price_increment` | `priceIncrement` | — | no |

**Unifiqué los dos que costaron un incidente**, como pediste. Los otros dos van
en la lista.

**El segundo incidente lo encontré esta noche y era mío:** el motor calculaba la
calidad medida con los partidos que vienen en `my_team`, y **la plantilla
publicada no los llevaba**. Quien leyera el tablero no podía reproducir el once
del motor: le salía otro. Arreglado añadiendo `played_home`, `played_away` y
`points_last_season` a la ficha publicada, y haciendo que `partidos_jugados`
entienda los dos nombres.

**Y el que más me preocupa de los que quedan abiertos:** `raw_points` **parece**
puntos de esta temporada y son de la anterior. El 20/09 lo dividí por las
jornadas jugadas y me salió que Pedri hacía 70 puntos por jornada. Lo cacé
entonces por absurdo; otro no lo cazaría.

## La guardia

No comprueba nombres: comprueba **comportamiento**. Una ficha con el alias tiene
que dar la misma respuesta que una con el nombre canónico, en las funciones que
de verdad los consumen. Y otra exige que todo concepto con incidente esté
unificado — si mañana aparece un quinto, no se puede dejar en la lista.

**No lo convertí en una refactorización general**, como pediste: cuatro
incidentes, cuatro puertas cerradas.

---

# Una guardia que cambió de signo, dicho en voz alta

`test_la_calidad_medida_no_esta_encendida` exigía que el motor **no** usara la
calidad. Tenía razón hasta anoche. Hoy la enciendes, así que la actualicé **a
propósito y con la explicación dentro**, igual que con los intocables: pasa a
llamarse `test_la_etiqueta_sobrevive_al_encendido` y vigila lo que sigue siendo
cierto —que sin partidos jugados manda la jerarquía y que el interruptor
devuelve la escalera entera—.

---

# Lo que no hice, y por qué

**No hice el bloque 4 entero:** balón parado, lista de la compra,
centrocampistas ofensivos y las noticias de los baratos. Cuarta noche que caen
las noticias, y el motivo sigue siendo el mismo: la caché diaria de las 570
fichas es el trabajo, no un añadido.

Entre los cuatro, **el que más valdría mañana es el balón parado**: es el truco
nº 1 del vídeo, sigue apagado, y no depende de nada de lo que hemos encendido
esta semana.

**No pinté en pantalla el peso de cada temporada**, solo la varianza y el aviso
de las tres jornadas.

**No toqué el precio de los catorce listados** ni el mecanismo que los publica.

**No respondí a la oferta por Yamal.** El veredicto está calculado y publicado;
la orden es tuya.

**Amatucci no se ha tocado**, como dijiste.

---

**La frase para mañana:** con la oferta de 21.099.500 € sobre la mesa y sin
ninguna lista que le proteja, **la cuenta dice NO VENDER a Yamal** — y lo dice
dándole a la opción de vender su mejor caso posible, **−0,76**, no una cesta
elegida a conveniencia. La calidad medida está encendida y se apaga con
`BORDALAS_CALIDAD_ETIQUETA=1`; hoy reordena las líneas pero no cambia el once, y
lo digo así en vez de venderlo como más. Y el marcador ya anota **tres onces por
jornada**, así que dentro de tres sabremos por separado qué aportó cada uno de
los dos cambios de esta semana.
