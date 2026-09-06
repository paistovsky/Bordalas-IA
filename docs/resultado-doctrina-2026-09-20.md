# LA DOCTRINA — resultado

Rama `doctrina/que-pepe-la-siga`, desde `main` (`7c0e75c`). **89 de 89 en
verde**, y en las tres condiciones:

```
disco local                          89/89
CI con caché fría (data/ vacío)      89/89
CI con caché caliente (25 días)      89/89
```

`main` no se toca. `bordalas-live.yml` y `MAX_SINGLE_SPECULATION_PERCENT`,
sin tocar. **Ningún tope ni ningún listón movido. Ninguna moneda gastada.
No he comprado nada.** Ninguna guardia nueva lee `data/`; ninguna función
nueva cambia de forma. `npm run build` pasa. **Sin push.**

**Llegué a cinco de los seis bloques. El 4 —las noticias de los baratos—
no lo hice**, y explico por qué al final.

---

## Lo que entra en el commit

Miré `git status` antes. **Catorce ficheros:**

```
?? src/analysis/doctrina.py              regla 17: las citas
?? src/analysis/ascendidos.py            regla 8: quién ascendió, y si paga
?? src/analysis/embudo.py                regla 9: dónde muere cada objetivo
?? src/analysis/activo_grande.py         regla 15: las dos columnas
?? src/analysis/test_doctrina_v1.py      23 pruebas, todas con fixture
?? dashboard-v8/src/components/DoctrinaPanel.jsx
 M src/telemetry/dashboard_state.py      publica el bloque
 M dashboard-v8/src/lib/status.js        normalizador
 M dashboard-v8/src/pages/BrainPage.jsx  monta el panel
 M src/analysis/test_pantalla_lee_lo_publicado_v1.py
 M scripts/run_validation_gate.py        + 1 guardia
?? docs/DOCTRINA.md                      tu documento
?? docs/ENCARGO-LA-DOCTRINA-2026-09-20.md
?? docs/ENCARGO-QUIEN-ES-BUENO-2026-09-19.md
```

**Aviso sobre el último:** `ENCARGO-QUIEN-ES-BUENO-2026-09-19.md` estaba sin
versionar en el repositorio y entra en este commit sin que yo lo haya
ejecutado. No me lo pediste y no lo he tocado; lo digo para que no parezca
hecho.

---

# 1. Cada decisión cita su regla (regla 17)

**38 de 45 decisiones (84,4 %) citan una regla.** Las citas se resuelven
leyendo `docs/DOCTRINA.md` —no copiándolo—, así que si renumeras o cambias
un estado, esto te sigue solo. Hay una guardia que falla si una cita apunta
a una regla que ya no existe.

| Regla | Título | Veces | Estado |
|---:|---|---:|---|
| 7 | Calidad sobre seguridad | 14 | a medias |
| 1 | El once es lo único que marca | 14 | entendido |
| 9 | Comprar lo que sube | 10 | construido, no dispara |

## Y lo que de verdad pediste: las que no citan ninguna

| Decisión | Veces | Dónde | Por qué no encaja |
|---|---:|---|---|
| **SUPERA_PRESUPUESTO** | 3 | mercado | El tope por operación **no está en la doctrina**. Hay reglas sobre qué comprar y cuándo; ninguna sobre cuánto se puede poner de una vez. Y ese tope ya salió una vez de anidar dos fracciones sin que nadie lo decidiera. |
| **NO_DISPONIBLE** | 2 | mercado | La disponibilidad —lesión, sanción— no aparece. Es obvia, y por eso mismo nadie la escribió. |
| **NO_SE_TOCA_UN_DIOS** | 1 | once | Sale de tu orden del 18/08 —"los Dios juegan siempre salvo 0 % motivado"— que nunca entró en el documento. **Y la regla 7 dice lo contrario en espíritu:** calidad por encima de certeza de jugar. |
| **MONITOR_OFFERS** | 1 | ciclo | **El hueco grande.** Gestionar las ofertas que *entran* no está en ninguna de las dieciocho. Las reglas hablan de comprar, vender, alinear y llegar en positivo; ninguna de qué hacer cuando otro manager puja por lo nuestro. Y es la decisión que más veces toma el ciclo. |

No forcé ninguna cita. `SPECULATION` y `HOLD` sí las mapeé a la regla 9
—son literalmente la vía de comprar lo que sube—, y eso no me parece
forzar; si no estás de acuerdo, se quita y suben a la lista de huérfanas.

---

# 2. Las dos comprobaciones

## 2.1 — Ver las pujas: **la respuesta es mejor de lo que esperabas, y peor**

**No hay monedas.** Buscando en todo lo que capturamos de la API, no
aparece ningún concepto de "fichas" ni de saldo consumible. Lo único que
Biwenger vende en esta liga son dos mejoras de pago real:

```
league.upgrades = { premium: PremiumLeague 29,99 € ,  ultra: UltraLeague 49,99 € }
```

**Pero hay algo mucho mejor. La liga ya tiene esto activado:**

```
league.settings.marketShowBids = true
```

Junto a `balance: "hidden"`, `auctions: false`, `clause: "disabled"`. Es
decir: **las pujas del mercado están declaradas como visibles en esta
liga**, y no cuesta nada.

**Lo que falta:** el endpoint que llamamos, `/api/v2/market`, devuelve las
ventas sin pujas —solo `date`, `until`, `price`, `player`, `user`—. Ni
siquiera en las 43 ventas de rivales. Así que la información existe pero no
está en el sitio del que tiramos.

**Lo que NO hice, a propósito:** no me autentiqué ni leí el `.env`. Probar
el endpoint de detalle de jugador con tus credenciales es una llamada a un
servicio externo con tu cuenta, y me dijiste "solo mirar". La comprobación
que falta es **una sola GET de lectura**, y la dejo escrita para que la
autorices:

```
GET https://biwenger.as.com/api/v2/players/{id}          (con X-League y X-User)
GET https://biwenger.as.com/api/v2/market/{sale_id}
```

Si alguno devuelve una lista de pujas, **el modelo estadístico de
`rival_bid_model` —48 pujas calibradas, curva de primas— sobra**, y se pasa
de adivinar a saber. Es la comprobación más rentable que queda pendiente en
todo el proyecto.

## 2.2 — Los recién ascendidos: **Racing, Málaga y Deportivo**

No de mi memoria: **deducidos del catálogo de Biwenger**, de la media de
puntos de la temporada anterior por club, sobre los 569 jugadores.

| Club | Jugadores | Media temp. anterior | % de plantilla a 0 |
|---|---:|---:|---:|
| **Racing** | 20 | **3,6** | 95 % |
| **Málaga** | 29 | **4,3** | 93 % |
| **Deportivo** | 30 | **5,5** | 93 % |
| Elche | 30 | 46,1 | 33 % |

**Ocho veces de separación** entre el tercero y el cuarto. Cualquier umbral
entre 10 y 40 da los mismos tres. Y si algún año la frontera no fuese
limpia, el módulo lo dice en vez de elegir por su cuenta —hay guardia—.

---

# 3. ¿Suben más los recién ascendidos? (regla 8 + regla 18)

**Sí, pero solo en el segmento que el vídeo describe.** Medido sobre
nuestro almacén de precios:

| Grupo | N | Media diaria | Pasan del 4 %/día |
|---|---:|---:|---:|
| **Ascendidos ≤ 1 M** | 36 | **+1,320 %** | **13,9 %** |
| Resto ≤ 1 M | 227 | +0,853 % | 9,3 % |
| **Ascendidos > 1 M** | 43 | **−0,232 %** | 2,3 % |
| Resto > 1 M | 261 | +0,444 % | 5,0 % |

**Los baratos de recién ascendidos suben 1,55 veces más que los otros
baratos**, y entran un 50 % más a menudo en el tramo `> 4 %/día` que ya
tenemos medido rindiendo +21,15 % a tres días.

**Y es solo en los baratos: los caros de esos mismos clubes caen.** Eso es
exactamente lo que dice el vídeo, y es la clase de precisión que no
esperaba encontrar.

**Aun así lo dejo como marcador, no como factor.** n=36, seis días, agosto,
y el efecto vive en la cola —las medianas son 0,000 % en los dos grupos—.
La vía TENER ya sabe valorar el tramo `> 4 %/día`; lo que le faltaba era
saber dónde mirar, y eso ya lo tiene. Regla 18: ningún umbral sin número, y
36 casos no son número suficiente para un factor.

**Hoy no hay nada que cazar.** En el escaparate hay 4 jugadores de
ascendidos, todos del Deportivo, y ninguno es un titular barato con rampa:

| Jugador | Precio | Titularidad | Ritmo |
|---|---:|---:|---:|
| Amatucci | 3.670.000 | 90 % | +1,09 %/día |
| Loureiro | 1.240.000 | 30 % | −0,81 % |
| Bright Ede | 1.140.000 | 30 % | −2,63 % |
| Álvaro Fernández | 290.000 | 5 % | 0,00 % |

**No he comprado nada.**

---

# 4. Las noticias de los baratos — **NO LO HICE**

Es el único bloque que dejo sin hacer, y prefiero decírtelo a entregarlo a
medias.

**Por qué:** los dos avisos de ingeniería que tú mismo escribiste son el
trabajo. Construir la ficha de los ~570 una vez al día y guardarla, y
cruzar el flujo de prensa contra los jugadores en vez de al revés, es un
cambio en el ciclo de producción —caché diaria, invalidación tras el reset
de las 07:00, y un libro de acierto nuevo—. Con lo que quedaba de noche
habría entregado una versión sin caché que enriquece 570 fichas cada media
hora, que es exactamente lo que me advertiste que no hiciera.

**Lo que sí dejo listo para mañana:** el ojeador de prensa ya existe y ya
lee MARCA, MD y Relevo; el cruce necesita el diccionario de nombres, que
está en `candidate_starter_lookup`, y el patrón de libro de acierto está en
`scout_accuracy_ledger` y en `rejection_ledger`. Es una noche de trabajo,
no una semana.

---

# 5. El embudo — **12 de 20 mueren en el mismo sitio**

| Causa de muerte | N | % | Qué es |
|---|---:|---:|---|
| **NO_MEJORA_EL_ONCE** | **12** | **60,0 %** | No vale para nuestro once: la posición ya está mejor cubierta |
| PRECIO | 3 | 15,0 % | Cuesta más de lo que hay, incluso vendiendo antes |
| RENDIMIENTO | 3 | 15,0 % | Se puede pagar, pero no deja margen |
| DISPONIBILIDAD | 2 | 10,0 % | Lesión o sanción |
| **TOPE POR OPERACIÓN** | **0** | **0 %** | Cabe en la caja pero no en el tope |
| VIVE | 0 | 0 % | |

**La respuesta a la pregunta que llevabas dos noches haciendo: el embudo no
muere en el tope por operación. Muere en la calidad.** Ni uno solo de los
veinte cae por el tope. Aflojarlo no habría comprado nada.

Y los tres que mueren por PRECIO **valen más de lo que cuestan**:

| Jugador | Vale | Cuesta | Margen |
|---|---:|---:|---:|
| Pedri | 15.552.620 | 15.350.000 | **+202.620** |
| Roro Riquelme | 4.325.859 | 4.240.000 | **+85.859** |
| Amatucci | 3.740.025 | 3.670.000 | **+70.025** |

Los tres son compras positivas bloqueadas **solo por caja**: hay 2.433.987
sin comprometer. No es un problema de listón ni de tope: es que no hay
dinero. Eso conecta con la regla 14 —rotar, no acumular— que sigue sin
hacer.

**No he tocado ningún tope ni ningún listón.**

*(De paso: la frase de cabecera del embudo tenía un fallo mío —cogía la
primera causa de la lista en vez de la mayor, y decía "la más común es
DISPONIBILIDAD" con 2 cuando eran 12—. Arreglado, con guardia.)*

---

# 6. Yamal — las dos columnas

| TENERLO | | VENDERLO | |
|---|---:|---|---:|
| Puntos por jornada, **medidos** | **9,33** | Libera | 21.210.000 € |
| % de los puntos / % del dinero | **19,0 % / 42,81 %** | Cesta que cabe | 21.270.000 € |
| € por punto/jornada (él) | 2.272.500 | Entrarían al once | 5 |
| € por punto/jornada (el resto) | **714.202** | **Puntos netos por jornada** | **−2,93** |
| Sube al día | +0,189 % | Concentración después | **30,95 %** |
| Titularidad | **100 %** | Caja restante | 198.807 € |

**Los dos números incómodos, en las dos direcciones:**

**Contra tenerlo:** cuesta **3,2 veces más por punto** que el resto de la
plantilla (2.272.500 € contra 714.202 €), es el 42,81 % del dinero por el
19,0 % de los puntos, sube por debajo del mercado, y rompe el tope de
concentración del 35 %. Venderlo lo arreglaría: bajaría a 30,95 %.

**A favor de tenerlo:** hace **9,33 puntos por jornada**, más que los cinco
últimos de la plantilla juntos, y el doble que el segundo (Olasagasti,
7,00). Y el mercado de hoy **no tiene con qué sustituirlo**: la mejor cesta
posible —Pedri, Amatucci, Suazo, Morcillo, Szczęsny por 21,27 M— deja el
once **2,93 puntos por jornada peor**, porque solo puntúan once y meter
cinco fichas desplaza a cuatro titulares actuales.

**Y la asimetría que hay que decir cada vez:** sus 9,33 están **medidos
esta temporada**; los de la cesta son una **proyección de la anterior**. No
son la misma clase de dato, y la proyección sale de una vara que explica el
20 % de la varianza.

**Con tres jornadas.** Vender al mejor de la plantilla con esa muestra
puede ser el error más caro del año. **Sin recomendación: decides tú.**

Un apunte: la doctrina dice que Yamal tiene **50 % de titularidad**. La
foto de hoy dice **100 %**. Ese dato está desactualizado en el documento.

---

# Lo que la medición contradice

**Regla 12 — "Ver las pujas con monedas".** No hay monedas en esta liga. Lo
que hay es un ajuste, `marketShowBids: true`, que ya está encendido y no
cuesta nada. El consejo del vídeo se adapta: **no es gastar, es mirar donde
no miramos.**

**Regla 8 — los recién ascendidos.** Se confirma, pero **solo en los
baratos**. Los caros de esos mismos clubes caen un 0,232 % diario. Aplicar
el consejo a todo el club sería perder dinero.

**Regla 15 y el 42,81 % de Yamal.** La doctrina lo plantea como una
anomalía a corregir. La cuenta dice que hoy **no hay con qué sustituirlo**,
y que su titularidad ya no es del 50 % sino del 100 %.

**Regla 9 — "construido y casi nunca dispara".** Cierto, pero no por donde
se sospechaba: **cero de veinte mueren en el tope por operación**. Mueren
por no mejorar el once (12) y por falta de caja (3).

**Regla 7 contra la orden del 18/08.** `NO_SE_TOCA_UN_DIOS` sienta la regla
7 —calidad por encima de certeza de jugar— por una orden que no está en el
documento. Hoy no hace daño (Yamal está al 100 %), pero las dos no pueden
convivir escritas así.

---

# Lo que no hice, y por qué

**No gasté ninguna moneda ni me autentiqué.** No hay monedas, y probar el
endpoint requiere tu autorización.

**No hice el bloque 4** (noticias de cesiones de los baratos). Explicado
arriba: la caché diaria de 570 fichas es el trabajo, y hacerlo mal revienta
el ciclo.

**No di factor a los recién ascendidos.** n=36. Marcador sí, factor no.

**No moví ningún tope ni ningún listón**, aunque el embudo dice claramente
dónde está el cuello.

**No compré ningún jugador ni ningún portero.**

**No toqué la regla 16** ni el reloj de solvencia.

**No actualicé `docs/DOCTRINA.md`.** Es tu documento; te dejo aquí las tres
cosas que le sobran o le faltan —la titularidad de Yamal, las monedas que
no existen, y `MONITOR_OFFERS` sin regla— para que decidas tú la versión
1.3.

---

**La frase para mañana:** el embudo no muere donde creíamos. **Cero de
veinte objetivos caen por el tope por operación**; doce caen por no mejorar
el once y tres —que valen más de lo que cuestan— solo por falta de caja.
Y la regla 12 tiene mejor respuesta de la esperada: **no hacen falta
monedas, `marketShowBids` ya está en `true`** y lo único que falta es pedir
las pujas al endpoint correcto — una GET de lectura que dejo escrita y sin
ejecutar hasta que la autorices.
