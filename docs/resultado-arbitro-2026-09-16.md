# EL ÁRBITRO — resultado

Rama `arbitro/quien-tenia-razon`. **Verja: 83 de 83 en verde** (82 al
empezar). `main` intacto. `.github/workflows/bordalas-live.yml` y
`MAX_SINGLE_SPECULATION_PERCENT` sin tocar. **Ningún umbral movido.**
`npm run build` pasa. **Sin push.**

Medido contra `diagnostico/status.json` del 06/09/2026 12:33.

---

## Lo que entra en el commit

Miré `git status` antes. **Quince ficheros, todos míos:**

```
 M dashboard-v8/src/lib/status.js                      normalizador
 M dashboard-v8/src/pages/BrainPage.jsx                monta el panel
 M scripts/run_validation_gate.py                      guardia nueva
 M src/analysis/hold_backtest.py                       tramo partido + profundidad
 M src/analysis/hold_value.py                          las dos cifras al lado
 M src/analysis/test_fuera_de_muestra_v1.py            ajustada al tramo partido
 M src/analysis/test_pantalla_lee_lo_publicado_v1.py   + 1 prueba
 M src/analysis/test_retrotest_rampa_v1.py             + 1 prueba, ajustada
 M src/autopilot.py                                    engancha el libro al ciclo
 M src/telemetry/dashboard_state.py                    publica el árbitro
?? dashboard-v8/src/components/ArbiterPanel.jsx
?? docs/ENCARGO-EL-ARBITRO-2026-09-16.md
?? src/analysis/rejection_ledger.py                    el libro de rechazos
?? src/analysis/rival_scoreboard.py                    el marcador de rivales
?? src/analysis/test_arbitro_v1.py                     17 pruebas
```

---

# BLOQUE 4 — El commit `1459222`: eres tú

```
commit 1459222dd4ec8fcbd73dda195fd1e966c78ee30d
Author:  Paistovsky <albcid@gmail.com>
Date:    Sun Sep 6 11:59:14 2026 +0200
Mensaje: bolsillo: de donde sale el dinero

 docs/ENCARGO-EL-BOLSILLO-2026-09-15.md | 211 +++++++++
 1 file changed, 211 insertions(+)
```

**Un solo fichero, Markdown, 211 líneas, cero ficheros de código.** Es
el propio encargo de anoche.

La cronología encaja: `1459222` a las **11:59**, mi commit encadenado a
las **12:15** — dieciséis minutos después. Entre mi primer `git status`
de la sesión (donde el fichero salía como `??`) y el siguiente (donde ya
no estaba), alguien ejecutó `git commit` en ese repositorio. Yo no lo
hice.

**Es inocuo y está explicado.** Un detalle que conviene saber: en este
repositorio hay una sola identidad de git configurada —la tuya— así que
mis commits y los tuyos son indistinguibles por autor. Y como el comando
encadenado usa `git commit -m` a secas, ninguno lleva el trailer
`Co-Authored-By`. Si algún día quieres poder distinguirlos, ahí está el
sitio.

---

# BLOQUE 1 — El árbitro

## 1.1 — El marcador de Pollo

| Jugador | Pagó | Vale hoy | Gana | % | Días |
|---|---:|---:|---:|---:|---:|
| Gerard Moreno | 6.450.007 | 6.430.000 | −20.007 | −0,31 % | **0,23** |
| Pubill | 6.360.006 | 6.430.000 | +69.994 | +1,10 % | 2,23 |
| Natan | 3.010.007 | 3.040.000 | +29.993 | +1,00 % | 1,23 |
| Bardeli | 1.877.000 | 1.790.000 | −87.000 | −4,64 % | 1,23 |
| Camavinga | 1.777.000 | 1.790.000 | +13.000 | +0,73 % | **0,23** |
| Ratkov | 1.447.000 | 1.390.000 | −57.000 | −3,94 % | **0,23** |
| Riki Rodríguez | 277.000 | 300.000 | +23.000 | +8,30 % | 2,23 |
| **TOTAL** | **21.198.020** | **21.170.000** | **−28.020** | **−0,13 %** | |

**Y ahora lo que ese −0,13 % esconde:** tres de las siete compras son de
**esta misma mañana a las 07:07**, cinco horas y media antes de la foto.
Su resultado no dice nada de la tesis: dice la prima que pagó sobre el
mercado. La mediana de días es **1,23**.

**6 de los 7 están subiendo hoy.** Las posiciones funcionan; no les ha
dado tiempo a nada.

## La mitad que casi se nos escapa: Pollo también vende

```
06/09 10:28   Vinícius Jr    17.633.400
04/09 08:31   Foyth           3.626.400
                             ----------
              vendido        21.259.800
              comprado       21.198.020
```

**Pollo no está desplegando caja parada. Está rotando, y casi al euro.**
Vendió a su activo más caro el mismo día que compraba a Gerard Moreno.

Eso desmonta la premisa que ha sostenido los tres últimos encargos —*"Pollo
tiene ocho fichas más y nosotros el dinero quieto"*—. Y hay una segunda
corrección de la misma familia: **la brecha de plantilla ya no son
35.520.000 €, son 18.300.000 €**, porque Pollo pasó de 85,06 M a 67,84 M
al soltar a Vinícius.

## 1.2 — El marcador de Luismi

| | |
|---|---:|
| Compró (3 jugadores) | 2.849.000 |
| Valen hoy | 2.750.000 |
| **Resultado** | **−99.000 (−3,47 %)** |
| **Vendió al Computer** | **14.413.900** |

**Luismi vendió cinco veces lo que compró.** Y sus tres compras pierden
un 3,47 % en día y medio.

**No se puede puntuar si acertó vendiendo, y lo digo en vez de
estimarlo:** un jugador vendido al Computer desaparece de todas las
plantillas de la liga, así que no hay precio de hoy con el que
compararlo. De los siete que vendió, solo Mikel Rodríguez reaparece en el
tablón del ojeador (2.180.000 hoy contra 2.464.100 cobrados: **acertó**,
se ahorró un −11,5 %). Uno de siete no es una muestra.

*(El tablón repite entradas: Mikel Rodríguez sale tres veces y Ayoze dos,
mismo importe y mismo día. Están deduplicadas; contarlas triplicaría el
marcador. Hay guardia.)*

## 1.3 — EL VEREDICTO: **A**, con una condición

**La respuesta es A: el modelo tiene razón. Y es una A medida, no
intuida.**

Apliqué la regla de Pepe —la vía TENER con su listón del 3 %— a las
**1.110 operaciones** del almacén, y comparé lo que hicieron después los
que habría comprado y los que habría rechazado:

| Grupo | N | Mediana a 3 días | Media | p25 | En pérdida |
|---|---:|---:|---:|---:|---:|
| **Los que Pepe COMPRA** | 212 | **+5,14 %** | +12,39 % | +2,73 % | **8,0 %** |
| **Los que Pepe RECHAZA** | 898 | **+0,00 %** | −0,35 % | −2,50 % | **37,4 %** |

**Comprar todo lo que Pepe rechaza habría dado una mediana de
exactamente cero y habría perdido dinero el 37 % de las veces.**

Y el dato que no depende de nuestra regla en absoluto: **el 81 % del
mercado no va a ninguna parte a tres días.** La mediana del grupo grande
es 0,00 %. Ahí es donde el modelo dice que no.

### La condición, y es importante

**Ese test es en buena parte circular.** Los cortes de la regla —el
0,25 %/día, los recortes por banda, el propio 3 %— se calibraron sobre
**estos mismos datos de agosto**. Así que mide coherencia interna, no
acierto fuera de muestra.

Lo que sí es independiente de nuestra regla:

- Pollo: **−0,13 %** en 1,23 días de mediana, comprando 21,2 M.
- Luismi: **−3,47 %** en 1,23 días, comprando 2,8 M.
- Los dos líderes son **vendedores netos o están equilibrados**, no
  acumuladores.
- Y la correlación entre valor de plantilla y puntos, sobre los 7
  managers: **r = +0,553**, cuando con n=7 hace falta **0,754** para
  distinguir de casualidad. **No lo alcanza.**

Los contraejemplos se ven a simple vista: **Mex va 2.º con 52,25 M y 14
fichas** —prácticamente nuestra plantilla y nuestras fichas— y
**Prinzipote va 6.º con 55,28 M y 17 fichas**.

**Traducción: no hay evidencia de que comprar más pague, y sí evidencia
—aunque en parte circular— de que nuestro filtro separa.** Deja de
perseguir a Pollo por el número de fichas.

**El libro de rechazos empieza hoy** y es lo que dará la respuesta no
circular en tres días. Hoy tiene **0 rechazos apuntados y 0 cerrados**, y
lo dice con esas palabras en vez de publicar una mediana de dos.

---

# BLOQUE 2 — El tramo de arriba, partido. Tenías toda la razón.

Era el error más caro de los que quedaban. Dentro de `> 1 %` convivían
tasas que rinden **5,7 veces distinto**:

| Tasa | Racha | m=3 | n | Mediana | En pérdida |
|---|---|---|---:|---:|---:|
| **1-2 %** | 1 día | | 68 | **+3,22 %** | 7 % |
| **2-4 %** | 1 día | | 37 | **+5,61 %** | 3 % |
| **> 4 %** | 1 día | | 37 | **+18,37 %** | 3 % |
| 1-2 % | 2 días | | 58 | +1,80 % | 10 % |
| 2-4 % | 2 días | | 41 | +3,14 % | 17 % |
| > 4 % | 2 días | | 35 | +21,15 % | 3 % |
| 1-2 % | 3-7 días | m=2 | 51 | +1,14 % | 22 % |
| 2-4 % | 3-7 días | m=2 | 30 | +2,29 % | 13 % |
| > 4 % | 3-7 días | m=2 | 34 | +12,80 % | 3 % |

**Los tres subtramos llegan a 30 operaciones.** Ninguno queda vacío.

## Y el efecto sobre los cuatro candidatos es exactamente el que
## sospechabas

| Jugador | %/día | Antes (tramo ancho) | Con el tramo partido |
|---|---:|---:|---:|
| Roro Riquelme | 1,666 | 1,80 % | **1,05 %** |
| Amatucci | 1,098 | 1,80 % | **1,05 %** |
| Pedri | 0,305 | 0,24 % | 0,24 % |
| **Gorosabel** | **4,849** | **1,80 %** | **8,49 %** |

**Gorosabel deja de estar recortado del todo.** Su rampa bruta (14,5 %
a tres días) cae por debajo del techo de su banda (+21,15 %), así que no
hay nada que recortar. El tramo ancho lo estaba aplastando de 8,49 % a
1,80 %.

Y Roro y Amatucci bajan más, que también es correcto: el techo de su
banda real (`1-2 %`, +1,80 %) es más bajo que el del tramo ancho
(+3,09 %).

**Gorosabel es hoy el único que pasa el 3 %. Y sigue `injured`.**

---

# BLOQUE 3 — Es la tasa, no la continuación. Se queda mi recorte.

Lo medí como pedías, comparando racha 1 con racha 2 dentro de cada
banda:

```
P(el día siguiente también sube), por racha del día de compra

    racha 1    n=264    92,0 %
    racha 2    n=237    94,1 %      SUBE
    racha 3+   n=351    73,8 %

Tasa del día siguiente, dentro de cada banda

    banda      racha 1    racha 2    racha 3+
    1-2 %      +1,36 %    +1,19 %    +0,65 %
    2-4 %      +2,56 %    +2,28 %    +1,26 %
    > 4 %      +6,94 %    +8,86 %    +6,95 %
```

**De racha 1 a racha 2 la continuación SUBE (92,0 → 94,1 %) mientras la
tasa BAJA.** La continuación no puede explicar una caída que ocurre
mientras ella misma mejora.

Y de racha 1 a 3+, descomponiendo:

| Banda | Caída de tasa | Caída de continuación | Sin explicar |
|---|---:|---:|---:|
| 1-2 % | ×0,478 | ×0,802 | **40 %** |
| 2-4 % | ×0,492 | ×0,802 | **39 %** |
| > 4 % | ×1,001 | ×0,802 | la tasa *sube* |

**Cuatro de cada diez puntos de caída no los explica la continuación.**
Por tu propia regla —*"si es continuación, mi fórmula; si es la tasa, la
tuya"*— **se queda el recorte**.

*(Una honestidad sobre la curva: reproduce el 92,0 / 94,1 / 73,8 al
decimal porque el estudio del 07/09 se calculó sobre este mismo almacén.
Es una comprobación de consistencia, no una corroboración independiente.)*

**Las dos cifras se publican juntas** en MERCADO, como pediste: el valor
recortado y el valor sin recortar, para poder mirarlas cuando haya más
histórico. Hoy: Roro 1,05 % contra 2,92 %; Amatucci 1,05 % contra 1,92 %;
Gorosabel 8,49 % en las dos.

---

# BLOQUE 5 — Los días de histórico, ya visibles

Gracias por la comprobación de la fontanería: coincide con lo que vi
—`data/autopilot` cacheado, `prune_github_state.py` sin tocar el
almacén— y explica las 72 pujas descartadas.

**Ahora se publica en el dashboard, en ESTRATEGIA, primera línea del
panel:**

```
Histórico de precios   N días desde AAAA-MM-DD · N jugadores · retención 60 d
Horizontes medibles    1, 2, 3, 4 días
```

Mi copia local dice **6 días desde 2026-08-12, 573 jugadores, 3.386
puntos**. **Producción dirá el suyo en el próximo ciclo**, y ahí es donde
hay que mirarlo: si son 20, el retrotest vuelve a correr con horizontes
de 5, 7 y 10 sin tocar una línea.

Los horizontes medibles se calculan del propio almacén (`n + m + 1` días
de serie para una racha de `n` y un horizonte de `m`), así que la línea
no puede prometer un horizonte que no cabe.

---

# Lo que no hice, y por qué

**No moví ningún umbral.** Lo dice el encargo y no hizo falta: el
veredicto salió A.

**No propuse aflojar nada.** Si hubiera salido B, aquí iría la
propuesta. Salió lo contrario.

**No puntué las ventas de Luismi.** Seis de sus siete vendidos no tienen
precio de hoy en ningún sitio de la foto. Estimarlo con el precio de
mercado del día de la venta sería inventarme el dato que falta.

**No arreglé la circularidad del retrotest de la regla.** No se puede
desde aquí: haría falta histórico que no se usó para calibrar. El libro
de rechazos, que empieza hoy, es exactamente eso.

**No toqué la fórmula de la vía TENER más allá del tramo partido.** El
recorte se queda porque la medición lo respalda, y ambas cifras se ven.

---

**La frase para mañana:** Pollo compró 21,2 M y vendió 21,26 M el mismo
día — no está desplegando caja, está rotando, y sus siete compras van a
−0,13 % en día y medio. Nuestra regla, aplicada a 1.110 operaciones,
compra cosas que rinden un +5,14 % de mediana y rechaza cosas que rinden
un 0,00 % exacto y pierden el 37 % de las veces. La brecha de plantilla
no son 35,5 M sino 18,3 M, y el segundo clasificado tiene nuestra misma
plantilla y nuestras mismas catorce fichas. **Deja de perseguirle: el
modelo estaba en lo cierto, y en tres días el libro de rechazos lo dirá
sin la circularidad.**
