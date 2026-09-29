# E4 · 29/09/2026 · ¿Las noticias se adelantan al precio? (agenda 6)

**Codigo:** `lab/noticias/archivar.py` (archivo), `analizar.py` (clasifica y mide),
`contra_e1.py` (contra la salida de E1), `caso_aspas.py` (caso Celta).
**Datos:** `archivo.jsonl` (3.174 noticias de FutbolFantasy /laliga/noticias, IDs
148550-151926, del 08/08 al 29/09, con hora de publicacion y equipo),
`eventos.jsonl`, `episodios.json`; precios de `price_history.json` (16/08-29/09).

**Hipotesis:** los partes de entrenamiento y lesiones de FutbolFantasy salen
antes de que el precio de Biwenger se mueva, y eso se puede operar (vender
antes de la bajada / comprar antes de la subida).

## 1. El archivo

- El listado `/laliga/noticias/pagina/N` esta cacheado (se queda en el 24/09),
  asi que se recorrio cada ID de articulo (`/laliga/noticias/<id>` redirige).
  3.174 articulos; ~1-2 partes por equipo y dia, publicados sobre todo de 11 a
  15 h y de 21 a 23 h de Madrid: **16-20 h antes del siguiente cambio de
  precio (07:00)**.
- Clasificacion por titular (regex, sin descripcion): fuera 701 traspasos y
  selecciones y 346 ruedas de prensa/entrevistas. Eventos: **629 BAJA, 291
  VUELTA, 135 TITULARIDAD**. Sin asignar: 290 titulares con palabra clave y
  sin jugador reconocible, 82 apellidos ambiguos, 1.272 jugador nombrado sin
  tipo claro. Muestra a mano de 30: ~80 % bien clasificados (errores tipicos:
  "no sufre lesion", entrenadores con apellido de jugador).
- Episodio = primera noticia de ese tipo para ese jugador en 7 dias. Con
  precio: 260 BAJA, 145 VUELTA, 100 TITULARIDAD (180 / 94 / 79 con precio >= 1 M).

## 2. Resultados (precio >= 1 M)

E = primer cambio de precio tras la noticia; base = precio al leerla. Exceso =
contra todos los jugadores >= 0,5 M ese mismo dia y con el MISMO sentido en
el cambio anterior (descuenta la inercia de E1). Intervalos al 90 % (bootstrap).

| grupo | n | 1er cambio | a 3 cambios | exceso 3 | exceso 7 |
|---|---|---|---|---|---|
| BAJA todas | 180 | -0,6 % | -3,2 % | **-2,5 %** [-3,6; -1,2] | -4,3 % [-7,3; -0,7] |
| BAJA, venia subiendo o quieto | 70 | +1,0 % | 0,0 % | **-4,2 %** [-6,4; -1,9] | -7,4 % |
| BAJA, venia quieto | 20 | -1,5 % | -6,3 % | -5,5 % [-8,0; -3,1] | -10,3 % |
| BAJA fuerte (lesion/rotura/parte), no venia bajando | 13 | -0,2 % | -5,4 % | -9,8 % | -20,4 % |
| VUELTA todas | 94 | -1,1 % | -2,4 % | -1,3 % [-2,0; -0,7] | -2,0 % |
| VUELTA, no venia subiendo | 69 | -1,8 % | -4,1 % | -0,4 % [-1,1; +0,3] | +0,2 % |
| TITULARIDAD | 77 | +0,3 % | +0,4 % | +0,9 % [-0,6; +2,7] | +2,3 % |

BAJA por mitades: exceso 3 = -1,7 % hasta el 06/09 (n=99, pretemporada y
mercado abierto) y -3,5 % [-4,5; -2,4] desde el 07/09 (n=78).

**¿Quien va primero? (BAJA, n=180)**

- En el **58 %** (105) el precio YA bajaba antes de la noticia (lesion en
  partido: el precio cae por los puntos y la noticia llega a la vez o tarde).
- En el 42 % restante (75): primera bajada en el cambio 0 (el de la manana
  siguiente) 24, cambio +1: 11, +2: 5, +3 a +6: 13, no baja en 8 dias: 22.
  **La noticia adelanta la caida 0-1 dias**, y la caida fuerte llega en los
  cambios +1 a +3 (caso tipico: -1 %, -6 %, -6 %, -5 %: Sadiq, Casado,
  Mikel Rodriguez, Sangare, Valverde).

**VUELTA no anuncia subidas:** 50 de 94 no suben ni un dia en los 8
siguientes; el que vuelve de lesion sigue sin puntos y el precio sigue su
inercia. **TITULARIDAD:** sin senal (y el titular es ambiguo).

## 3. ¿Se puede operar?

- **Vender al leer la BAJA no gana a la salida de E1** (vender al Computer el
  primer dia que baja, que aun paga +3,2 %): en los 70 que no venian bajando,
  vender al leer rinde **-4,2 % de media (mediana -1,4 %) frente a E1, gana
  solo 14/70**; en las 13 lesiones fuertes, -0,3 % (3/13). El que venia
  subiendo sigue subiendo un dia o dos aunque este lesionado, y la primera
  bajada es suave: E1 ya sale a tiempo.
- **Donde si vale: NO COMPRAR.** Un jugador con BAJA en los ultimos 3 dias
  rinde -2,5 % a 3 cambios y -4,3 % a 7 frente a sus iguales (n=180); si
  venia subiendo (la senal de compra de E1), **-3,7 % a 3 cambios frente a
  los que suben sin noticia (n=50)**. Pepe puja el dia antes del cambio: la
  noticia de las 11-15 h llega a tiempo de retirar la puja.

## 4. Caso Celta: Aspas, Duran, Jutgla

| dia | Aspas | Duran | Jutgla | noticias (hora Madrid) |
|---|---|---|---|---|
| 13/09 | 3,36 | 0,43 | 3,05 | Celta-Malaga. **FF 16:15** "Primer parte medico de Aspas"; FF 17:02 Giraldez habla de "las lesiones de Aspas y Pablo Duran"; **Faro 21:36** "Aspas se lesiona y volvera despues del paron" (rotura fibrilar) |
| 14/09 | 3,29 (-2,1 %) | 0,42 | 3,07 | FF 11:27 "El Celta descansa pendiente de Aspas..." ; Faro 17:06 "golpe de calor de Duran" |
| 15/09 | 3,05 (-7,3 %) | 0,40 | 3,10 | **FF 12:12 parte oficial: grado I recto anterior, ~1 mes** |
| 16-19/09 | 2,87 → 2,48 | 0,39 → 0,36 | 3,13 → 3,19 | FF 17/09, 18/09: "sin Aspas ni Antanon". 19/09 Celta-Racing: doblete de Duran |
| 20/09 | 2,44 | **0,42 (+16,7 %)** | 3,20 | Faro 19/09 23:56 "doblete de Pablo Duran" |
| 21-29/09 | → 2,13 | → 1,33 (+24 %/dia, frenando) | 3,20 → 3,00 | Faro 22/09 06:10 "Pablo Duran, o triunfo da perseveranza"; FF 21/09, 22/09, 28/09 "sin Aspas" |

- **Aspas:** la noticia (FF 13/09 16:15) y la primera bajada (14/09) van en el
  mismo cambio; la caida fuerte (-7,3 %) llega el 15/09. Vendiendo el 13/09
  por la tarde: 3,36 M; con E1 (vender el 14/09 al Computer, +3,2 %): ~3,40 M.
  **Empate.** Lo que si daba la noticia: no comprar a Aspas desde el 13/09
  (perdio -37 % hasta el 29/09).
- **Duran:** la subida la arranca el **doblete del 19/09** (partido), no una
  noticia. Ni FF ni Faro dijeron antes del partido que Duran fuera a jugar
  mas (FF el 13/09 incluso lo daba tocado). Es la regla de E2 (las subidas
  nacen con la jornada), no esta. La prensa local escribio de Duran el 22/09,
  con el precio ya +80 % (0,36 → 0,65 M).
- **Jutgla:** ninguna noticia sobre el (solo aparece en ruedas de prensa del
  12, 13 y 19/09). Baja -1 %/dia desde el 22/09 por no tener puntos en el
  paron, sin causa en noticias.

## 5. Fuentes por equipo: piloto Celta

| fuente | URL | ¿se lee con curl? | listado con fecha / RSS |
|---|---|---|---|
| FutbolFantasy | futbolfantasy.com/laliga/noticias/<id> | si (200) | listado cacheado; por ID con `datePublished` |
| Faro de Vigo | farodevigo.es/celta-de-vigo/ y /temas/iago-aspas-1191288/ | si (200) | fecha en la URL, `datePublished` en el articulo; la seccion solo muestra ~10 dias (`?page` no pagina); temas por jugador si |
| Atlantico Diario | atlantico.net | portada 200; /deportes/celta 404 | /rss/ existe, sin feed de Celta a la vista |
| Metropolitano.gal | metropolitano.gal/feed/ | si (200) | RSS general (poca informacion de Celta) |
| Moi Celeste, Minuto Noventa, celtavigo.net, celtistas.net, forocelta | — | **no** (el proxy/TLS los corta: codigo 000) | — |
| Reddit r/celtadevigo | reddit.com/r/celtadevigo/new.json | **403** (bloqueo a bots) | — |
| X/Twitter de periodistas locales | x.com | 200 pero sin contenido sin sesion | — |

Primera noticia de cada cosa (n=1 caso con 3 jugadores):

| hecho | FutbolFantasy | Faro de Vigo | precio |
|---|---|---|---|
| lesion de Aspas | 13/09 16:15 | 13/09 21:36 | baja desde 14/09 (-2,1 %), fuerte 15/09 |
| plazo (~1 mes / tras el paron) | 15/09 12:12 (parte oficial) | **13/09 21:36** | ya bajando |
| Duran gana minutos | nunca antes del partido | 19/09 23:56 (tras el doblete) | sube desde 20/09 |
| Jutgla | nada | nada | baja desde 22/09 |

**Ventaja de la prensa local: ninguna en el hecho (FF fue 5 h antes), ~39 h
en el plazo, que no cambia nada operable (el precio ya caia).** Con n=1
equipo y 1 lesion no se puede generalizar, pero no hay indicio de que montar
20 fuentes locales (la mitad no se deja leer) de mas que FutbolFantasy, que
ya recoge la prensa local de cada club y la publica con hora.

## 6. Veredicto

**PROMETEDOR, como guardia de compra, no como senal de compraventa.**

- **Regla propuesta (guardia en `press.py`):** si en las ultimas 72 h hay en
  FutbolFantasy una noticia BAJA de un jugador (lesion, parte medico, "sin X",
  al margen, expulsado/sancionado), **no pujar por el**, aunque cumpla la
  regla de compra de E1. Evita -2,5 % a 3 dias y -4,3 % a 7 frente a sus
  iguales (n=180); en los que iban subiendo, -3,7 % a 3 dias (n=50).
- **No** vender por noticia: la salida de E1 empata o gana (vender al leer
  pierde -4,2 % de media frente a E1, n=70).
- **No** comprar por VUELTA ni por TITULARIDAD: sin senal (n=94 y 77).
- Lo que movio a Duran fue el partido, no una noticia: eso es E2.

**Limites:** 6 semanas de precios (con pretemporada y mercado abierto hasta
el 01/09); clasificacion por regex con ~80 % de acierto; se descartan los
apellidos ambiguos; el paron (desde el 20/09) aplana los precios; sin tope de
caja ni coste de la puja. El caso de las fuentes locales es n=1.
Para confirmar: repetir en octubre con `archivar.py` diario (desde el ID
151927) y medir la guardia contra las pujas reales de Pepe.
