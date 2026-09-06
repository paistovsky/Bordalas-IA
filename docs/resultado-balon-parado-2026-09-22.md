# EL BALÓN PARADO — resultado

Rama `balon-parado/quien-tira-los-penaltis`, desde `main` (`40ab7b1` — habías
fusionado las tres, así que esta vez sale de `main` limpio). **91 de 91 en
verde**, también en CI con caché fría.

`bordalas-live.yml` y `MAX_SINGLE_SPECULATION_PERCENT`, sin tocar. **No he
vendido, comprado ni respondido a ninguna oferta.** Ninguna guardia nueva lee
`data/` ni la red. **Sin push.**

---

## Lo que entra en el commit

Miré `git status`. **Diez ficheros:**

```
?? src/intelligence/scout/penaltis_comuniate.py   el lector de la fuente
?? src/analysis/balon_parado.py                   la señal y el bono
?? src/analysis/test_balon_parado_v1.py           19 pruebas, fixture dentro
 M src/analysis/soltar_un_grande.py               el margen, con número
 M src/analysis/player_value_engine.py            } raw_points renombrado
 M src/analysis/acquisition_valuation.py          }
 M src/analysis/acquisition_board.py              }
 M src/analysis/un_dato_un_nombre.py              el registro, actualizado
 M scripts/run_validation_gate.py                 + 1 guardia
 M docs/DOCTRINA.md                               ← ver aviso
```

**Aviso:** `docs/DOCTRINA.md` sale modificado y **no lo he tocado yo**. Lo
actualizaste a **v1.5** mientras trabajaba, añadiendo el VÍDEO-2 (La Media
Inglesa). Entra en este commit. Lo bueno: uno de sus matices lo he podido medir
esta misma noche, y está más abajo.

---

# ¿Se puede saber quién tira los penaltis?

**Sí, y gratis.** No hacía falta la API rota.

| Fuente | Qué publica | Resultado |
|---|---|---|
| **Comuniate** `/lanzadores/penaltis` | quién tira, lanzados y anotados | **HTTP 200** |
| Comuniate `/lanzadores/faltas` | — | **404** |
| Comuniate `/lanzadores/corners` | — | **404** |
| Analítica Fantasy, estadísticas | — | **404** |
| FutbolFantasy, estadísticas | penaltis **marcados** | 200, pero es histórico, **no designación** |

**Penaltis sí. Faltas y córners no**, en ninguna de las tres. Como pedías: lo
digo y paro ahí, sin inventarlos con una lista escrita a mano. Queda declarado en
el código (`SIN_FUENTE`) con guardia, para que nadie los vuelva a buscar a
ciegas.

**Veinte equipos, veinte lanzadores designados**, con sus penaltis lanzados y
anotados:

```
Alavés   Lucas Boyé        Barcelona  Raphinha (1/1)     Osasuna   Budimir (2/2)
Athletic Sancet            Betis      Isco               Racing    Andrés Martín (2/1)
Atlético Lookman           Celta      Iago Aspas         Madrid    Mbappé (1/0)
Málaga   Chupe (2/1)       Sevilla    Peque (1/1)        Real Soc. Oyarzabal
...
```

**Un fallo del primer intento, y es instructivo:** la tarjeta del equipo va
**antes** que sus lanzadores. Cortando por jugador, cada uno se quedaba con el
equipo del siguiente y salía *"Lucas Boyé, Athletic Club"* cuando Boyé es del
Alavés. Se lee en orden de documento arrastrando el equipo vigente, y hay
guardia con ese caso.

**22 de 24 emparejados** con el catálogo de Biwenger. Los dos que no —Yeremay y
Fernando Niño— **se quedan fuera y se dicen**: meter el bono en el jugador
equivocado es peor que no meterlo.

---

# El bono NO sobrevive a la medición

Pedías medir los 8,0 / 3,0 decretados contra los puntos reales antes de darlos
por buenos. Medido:

| Grupo | n | Puntos por partido |
|---|---:|---:|
| **Lanzadores de penaltis** | 22 | **5,73** |
| Delanteros que no lanzan | 97 | 3,68 |
| Todos los que no lanzan | 397 | 3,52 |
| | | **+2,21 de diferencia** |

Parece enorme. **Y es casi todo un espejismo.** El lanzador de penaltis *es*, por
selección, el mejor atacante de su equipo. Comparando a cada uno con el **mejor
delantero de su propio equipo que no lanza**:

```
        n = 18      media −0,25      mediana −1,29
```

**Descontado "ser el mejor de tu equipo", lanzar penaltis no añade nada medible**
con tres jornadas.

Y hay una segunda razón que **no depende de la muestra**: la calidad medida son
puntos por partido, y **los puntos de un penalti marcado ya están dentro**.
Sumar un bono encima sería contar el mismo gol dos veces — el error que este
proyecto lleva un mes aprendiendo a no cometer.

**Así que el bono se publica DECRETADO y con valor 0,0.** La señal —quién
tira— se publica igual, porque es información útil que no teníamos. Hay guardia
de que el motor no lo suma, y de que solo se encendería con **muestra ≥ 30 y
signo positivo**, las dos cosas.

**`penalty_intelligence.py` sigue apagado**, como pediste. La vía nueva no lo
importa, y hay guardia por AST.

---

# El matiz del VÍDEO-2, medido esta noche

Tu v1.5 añade: *"el valor no está en el crack que además tira penaltis, está en
el barato que los tira"*. Lo medí, y **es exactamente así**:

| | Mediana € por punto y partido |
|---|---:|
| Lanzadores de penaltis | **1.039.000** |
| Delanteros que no lanzan | **553.333** |

**Ser lanzador no es buen precio: cuestan casi el doble por punto.** Pero dentro
de los lanzadores hay **6,7 veces** de diferencia:

| Lanzador | Precio | Pts/partido | € por punto |
|---|---:|---:|---:|
| **De la Fuente** | 3.560.000 | 8,00 | **445.000** |
| **Peque** | 2.790.000 | 5,67 | **492.353** |
| **Boyé** | 3.360.000 | 6,50 | **516.923** |
| … | | | |
| Mbappé | 24.880.000 | 9,75 | 2.551.795 |
| Lookman | 8.180.000 | 2,75 | 2.974.545 |

**Tres lanzadores baratos baten a la mediana de los delanteros que no lanzan.**
El vídeo tiene razón y la afinación importa: no es "fichar lanzadores", es
"fichar al lanzador barato". Publicado en `por_euro_y_punto`. **No he comprado
nada.**

---

# Las dos cortas

## 1. El margen de +0,50 ya tiene número (regla 18)

En una venta de este tipo, lo que **sale** está medido y lo que **entra** es una
proyección. Así que el margen tiene que cubrir cuánto se equivoca una proyección.
Sobre **259 jugadores** con al menos dos partidos:

```
error (real − proyección), en puntos por partido
    p10      −1,33
    p25      −0,42     ← de aquí sale el margen
    mediana  +0,71
    p75      +1,95
    desviación típica 2,27
```

**Una de cada cuatro veces la proyección se pasa de largo en 0,42 puntos por
partido o más.** Un neto por debajo de eso puede ser enteramente error de
proyección: no es una mejora, es ruido con signo.

**Lo dejo en 0,50** —el p25 redondeado hacia arriba, con 0,08 de colchón— en vez
de bajarlo a 0,42: **el número que había resulta estar bien puesto**, y moverlo
para ganar dos centésimas sería fingir precisión. Ahora tiene procedencia
(`MARGEN_ORIGEN`) y viaja con el número.

**Y un aviso que salió de paso, que te afecta:** la proyección que usamos
—`puntos temporada anterior / 38`— **da por hecho que todos jugaron las 38**, así
que infravalora a quien se perdió partidos: la media real supera a la proyectada
en **+1,01**. Eso hace la prueba de venta **más conservadora** (entra menos de lo
que entraría), así que las conclusiones sobre Yamal y Amatucci van en la
dirección segura. No lo corrijo a ciegas: sin los partidos jugados del año
pasado, cambiaría un sesgo conocido por uno desconocido.

## 2. `raw_points` renombrado

Ahora es **`last_season_points`**, con el alias viejo conservado mientras queden
lectores. En `player_value_engine`, `acquisition_valuation` y
`acquisition_board`, los tres con la nota de por qué.

En el registro de "un dato, un nombre" pasa a **unificado**, con el incidente
fechado: *el 20/09 lo dividí por las jornadas jugadas y salió que Pedri hacía 70
puntos por jornada*. Los cuatro nombres se leen igual, con guardia. **Quedan 4
conceptos registrados, 3 unificados, 1 en la lista.**

---

# Lo que no hice, y por qué

**No enciendo el bono.** Lo mide todo en contra: n=18, signo negativo dentro del
equipo, y doble conteo con la calidad medida. Se enciende solo si el libro de
acierto lo desmiente en tres jornadas.

**No hay libro de acierto todavía.** Pedías uno "como cualquier otra fuente" y no
llegué: hace falta anotar la designación de hoy y contrastarla dentro de dos
semanas, y eso es un fichero de estado más y su ciclo. La señal ya se publica, que
es lo que hace falta para empezar a anotar mañana.

**No lo he enchufado al ciclo ni a la pantalla.** El módulo lee y mide; nadie lo
llama todavía desde `dashboard_state`. Es media hora de trabajo y preferí dejar la
medición bien hecha antes que enchufar un bono de 0,0.

**No toqué faltas ni córners.** No existen en la fuente.

---

**La frase para mañana:** el dato que llevábamos un mes sin tener estaba **gratis
y a una URL de distancia** — Comuniate publica los veinte lanzadores de penaltis
de LaLiga, y la API de pago rota nunca hizo falta. Pero el bono que íbamos a
pagarles **no se sostiene**: los lanzadores hacen +2,21 puntos por partido más que
el resto, y contra el mejor delantero de su propio equipo la diferencia es
**−0,25**. Era el sesgo de ser la estrella del equipo. Lo que sí se sostiene es el
matiz de tu VÍDEO-2: **ser lanzador cuesta el doble por punto, y el valor está en
el barato que los tira** — De la Fuente a 445.000 € por punto contra los
2.974.545 de Lookman.
