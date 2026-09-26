# AUDITORÍA — ¿ESTÁ PEPE JUGANDO AL JUEGO QUE ES?

**Fecha:** 26/09/2026 · **Rama:** `auditoria/la-ruta-de-decision`, desde `origin/main` (`80083658`)
**Solo lectura.** No se ha arreglado, encendido, apagado ni borrado nada. Los detalles están en el
anexo; para decidir basta con esta primera parte.

---

## La tesis: se sostiene, pero el culpable no es el que decía el encargo

**Es cierto que Pepe no convierte dinero en puntos.** De los puntos que se pueden reconstruir, el
**4 %** viene de lo que ha fichado el bot, frente al **65 %** de lo fichado por el dueño a mano y el
**31 %** de la plantilla inicial.

**Pero lo que lo frena no es la prudencia con el dinero (la caja, la deuda o el plazo), sino
cómo se valora un fichaje.** `xi_upgrade_value` (`player_value_engine.py:1215`) valora un fichaje
**solo por los puntos que añade**, como si el precio se perdiera. El jugador sigue siendo nuestro
y se revende: el coste real es la depreciación, que en las compras del dueño ha sido del **3,4 %**.

Hinojo mejora el once +0,73 puntos por jornada y sale *«vale 883.575 y cuesta 1.690.000. No hay
margen»*. **La caja solo frena 4 de 228 decisiones (1,8 %).** La valoración y la puerta de los
managers frenan antes.

---

## El bloque 0, en cuatro líneas

| | Respuesta | n |
|---|---|---|
| **0.1 Quién mata** | **Dos puertas matan al 87 %:** `MERCADO_DE_RIVAL` (65 %, no compramos a managers) y `SIN_VALOR` (22 %, el valor sale 0). **Una puja en cuatro días.** | 228 candidatos-día, 23-26/09 |
| **0.2 El precio del punto** | **Neto, lo fichado por el dueño salió a 9.127 € por punto, contra 30.000 € de premio. Comprar a jugadores que juegan es beneficio.** Lo del bot, a 134.984 €: compra reventas de 150.000 € que no juegan (7 puntos en 18 compras). | 24 y 18 compras |
| **0.3 La prudencia** | La caja frenó 4 de 228 (1,8 %). **Nunca se empezó una ronda en rojo** (hay dato de 4 de 8; la más justa, +131.717 a los 7 minutos). Las reservas caducadas: **no se sabe, no se apunta.** | 4 rondas |
| **0.4 Qué aportó el bot** | **El bot aportó el 4 %** (11 puntos de 298 reconstruidos). El dueño a mano, el 65 % (Yamal solo, 88). La plantilla inicial, el 31 %. Alineados que no jugaron: 2 en 7 rondas. | 7 rondas |

**Salvedad del 0.4:** ninguna ronda cuadra exacta. El once que guarda el marcador no es el que
jugó (el de la J7 lleva a Blanco, comprado el 26/09). **Lo que falta para contestarlo de verdad:
apuntar al cerrar cada ronda el once que puntuó y los puntos de cada jugador.** Biwenger solo
enseña la ronda en curso: lo que no se apunta en el momento se pierde.

---

## El veredicto, ordenado por los puntos que cuesta

| # | Qué está mal o falta | Puntos al año | Arreglo |
|---|---|---|---|
| 1 | **La valoración de fichar trata el precio como gasto.** No suma lo que vale el jugador al revenderlo. Por eso el bot no ficha a nadie que juegue | **~100-150**: el once de hoy está a 15,7 puntos por jornada del alcanzable; capturar entre la cuarta parte y un tercio durante 31 jornadas | **uno** |
| 2 | **La caja es el margen de deuda:** con −6,5 M, vender no mete dinero (medido: +3,67 M en ventas y la caja bajó 2,2 M) | **se come el #1** si no se sale del rojo: el plan con la caja de hoy es una compra de +0,12 | **uno** + decisión del dueño (qué vender: Ceballos, la chatarra) |
| 3 | **No compramos a managers** (el 65 % de los candidatos). Su mercado es el doble que el del Computer (44 frente a 20) | **decenas**, pero solo después del #1: hoy pasan 0 de 35 | **uno** (`place_bid` ya acepta vendedor, `write_client.py:270`) |
| 4 | **El once no se mide:** «0 jornadas medidas limpiamente». La titularidad solo para 142 de 526 (el catálogo está apagado) | **~20-40**: dos alineados que no jugaron en 7 rondas, a ~4 puntos, más los cambios de la J8 con la titularidad buena | **uno** (encender el catálogo + el libro del once) |
| 5 | **Las ventas escriben sin sombra:** la aceptación de ofertas de managers acepta sola aunque cueste un titular; el Position Manager dice «SOLO SHADOW» y publica; la reserva vendió a Rubén García | **~10-30**: Rubén costó 14 puntos de temporada respecto a lo prometido | **uno** |
| 6 | **Las vías de reventa pierden dinero y ocupan fichas:** carril −3,6 %, BUY V10 perdió 15 de 16, tablero −5,8 %, cesta +0,12 % | **~30 en dinero** (unos −0,9 M a 30.000 € el punto) + fichas ocupadas por jugadores que no juegan | **uno** (sobre todo apagar) |
| 7 | **A los managers les vendemos con un listón de más del 40 %** (`LISTON_DEL_MANAGER` apagado) | **2-4 M al año** para fichar (n = 3 ventas, +24 % a +32 %) | **uno** (encender dos) |
| 8 | **No sabemos si el bot aporta:** el registro de cada vuelta vive 2 días y el marcador no cuadra | **no se puede estimar**, pero sin esto no se mide nada de lo de arriba | **uno** |
| 9 | 11 interruptores por encender y 8 por borrar | pocos cada uno | **dos** (uno por vuelta: 10 vueltas) |
| 10 | 75 de 184 guardias no protegen ninguna decisión viva | 0 (≈1 minuto por verja) | **uno** |
| — | La racha diaria (~50.000 € al día): ya se cobra al máximo desde el 11/09, pero nada vigila que no se rompa | 0 hoy | parte del #8 |

## Mi recomendación, en cinco líneas

1. **Primero la valoración (#1):** que el coste de un fichaje sea la depreciación esperada, no el precio. Es el freno de verdad; la caja y las 184 guardias no lo son.
2. **A la vez, salir del rojo (#2):** sin eso el #1 no tiene dinero. Vender lo que no puntúa es decisión tuya, y es la que desbloquea todo.
3. **Después, medir (#8):** apuntar el once que puntuó y el registro de cada vuelta. Hoy el bot aporta el 4 % y no podemos ni saberlo con exactitud.
4. **Cerrar lo que pierde y vigilar lo que vende (#5, #6):** apagar el carril y BUY V10; poner sombra a las ventas a managers y al Position Manager.
5. **Los interruptores y las guardias, al final:** no dan puntos, solo quitan ruido. «Cerrar el sistema» no es lo urgente; lo urgente es que Pepe fiche.

---
---

# ANEXO

## A. Bloque 0 en detalle

**0.1** (`libro_de_la_valoracion.jsonl`, 23-26/09, n = 228 candidatos-día, 102 distintos)

```
MERCADO_DE_RIVAL          148   64,9 %   acum.  64,9 %
SIN_VALOR                  50   21,9 %          86,8 %
NO_DISPONIBLE              11    4,8 %          91,7 %
RENDIMIENTO_INSUFICIENTE    8    3,5 %
NO_COMPENSA                 6    2,6 %
SUPERA_PRESUPUESTO          4    1,8 %
BID                         1
```

- `SIN_VALOR` es *«No vale la pena por ninguna vía»*: la mejora del once cae por
  `NO_MEJORA_JERARQUIA` (22 de 52 objetivos en el panel de las 08:10) y las otras tres vías por
  `PRECIO_CAYENDO`.
- De los 32 `MERCADO_DE_RIVAL` del panel, si se abriera la puerta, 19 caerían en `SUPERA_PRESUPUESTO`.
- Salvedad: el libro solo cubre 4 días. Las fotos locales anteriores no guardan la decisión.

**0.2** Fuentes: el tablón (46 compras), el libro de pujas (quién pujó) y los puntos partido a
partido reconstruidos desde `fitness`, más la cola de la J7.

```
                 n   pagado       neto (pagado - venta o valor hoy)   puntos mientras nuestro   EUR/pto neto
dueño           24   68.248.198   2.318.285                           254                       9.127
bot             18   14.805.488     944.888                             7                     134.984
el punto en premios: 30.000 (bonusPoint, roundFinished)
```

- "Del bot" = pujas con intención registrada (reventa, especulación, mejora del once).
- "Del dueño" = compras que solo aparecen en el tablón, sin registro del bot. Puede incluir
  alguna vía que escriba sin registrar.
- Las compras de los últimos 7 días apenas han jugado: no ha habido jornada desde el 20/09.

**0.3**

- **La caja frenó** 4 de 228 (`SUPERA_PRESUPUESTO`).
- **Blanco:** lo pujó el dueño (3.288.000) y el bot subió la puja a 3.447.904 a las 22:11
  (`XI_UPGRADE`). No es un caso de "él pudo y Pepe no".
- **Saldo al empezar ronda:**
  - J1: +239.968
  - J5: +4,47 M
  - J6 aplazada: +131.717 (el 13/09 estaba en −1,30 M)
  - J7: +4,32 M
  - Del resto no hay dato.
- **La regla de Biwenger para empezar en rojo** no está en los ajustes (`balance: hidden`).
  **No lo sabemos, y no lo hemos preguntado.**
- **Ajustes de la liga:** `clause: disabled`, `loans: allow` (1-5 rondas), `userOffers: market`,
  `bonusDailyStreak: true`.

**0.4** Ventana de cada ronda del tablón (inicio → fin) × once del marcador × partidos
reconstruidos.

```
ronda        oficial  reconstruido
J1             29        25
J2             31        29
J1 aplazada    41        12
J3             61        54
J4             53        51
J5             61        65
J6 aplazada    29        27
J7             47        33     (once del 26/09, con Blanco)
total         352       298

dueño 194 (65 %: Yamal 88, Pablo Ibáñez 23, Jonny 18...) · inicial 91 (31 %: Olasagasti 33, Jutglà 27)
bot 11 (4 %: Yeray 5, Unai López 4, Rubén García 2)
```

## B. El mapa (resumen; tabla completa en la salida del agente de mapa, citada por fichero y línea)

| Bloque | Módulos | Funciona | No funciona | Nadie lo ha comprobado |
|---|---|---|---|---|
| ALINEAR | 6 | 2 (la prioridad, el once una vez) | 0 | **3**: `build_lineup` y `SAVE_LINEUP` (**no lo hemos preguntado**: el marcador guarda el once), el monitor (**no lo sabemos**: su estado vive 2 días) |
| FICHAR | 11 | 3 (el importe de la puja gana el 83 %, n = 35; el corte de «revender solo si juega», 81 %, n = 114; la cesta, apenas) | **5**: tablero −5,8 %, reventa con listón del 3 % imposible, carril −3,6 %, BUY V10 15 de 16 perdidas, la lista vieja | 1 (la moneda: **no lo hemos preguntado**) |
| VENDER | 12 | 1 (la renovación escribe: 8 de 11) | 2 (escaparate: Trent publicado 16 veces, ya arreglado; aceptar antes de caducar) | **8**: reroll, cobrar ofertas, contraofertas, EXIT, efecto de publicar y de renovar (**no lo hemos preguntado**: están en el tablón y los libros); contraofertas y EXIT (**no lo sabemos**: su estado vive 2 días) |
| EL DINERO | 9 | 2 (presupuesto de fichar, el reloj) | 0 | **5**: solvencia, deuda segura, T-15, la solvencia por su plazo, la reserva (**no lo hemos preguntado**: está en la bitácora) |

## C. Todas las vías que escriben en Biwenger: 17 en producción

Todas acaban en `BiwengerWriteClient` (`src/biwenger/write_client.py`, 7 métodos).

| Vía | ¿Pasa por la cuota de una por vuelta? | ¿La cubre la sombra antes de escribir? |
|---|---|---|
| Autopilot: publicar para liquidez, cobrar oferta, aceptar grupo, reroll, renovar, guardar el once | sí | a medias (solo la primera de la cola) |
| Autopilot: puja del tablero | sí | sí |
| Oferta de manager: contraoferta | sí | **no** |
| **Oferta de manager: aceptar (también sacrificando al once)** | sí | **no. La más peligrosa: irreversible y puede costar un titular** |
| BUY V10 (dormido, pero armado) | sí | **no** |
| V10: cancelar contraoferta, subir contraoferta | sí | **no** (el módulo dice «SHADOW») |
| **V10 EXIT_LISTING (Position Manager)** | sí | **no. Dice «SOLO SHADOW» y publica** (`v10_full_autonomous_live.py:1356-1360`, desde el 14/08) |
| Subasta del reset | **no**, a propósito | sí |
| Renovación de ventana | **no** | sí |
| Carril | **no** | a medias |
| Escaparate | **no** | a medias |

**Resumen:**

- **Cuota:** 4 vías escriben fuera de la cuota de una escritura por vuelta.
- **Sombra:** cubre 3 vías del todo, 8 a medias y ninguna de las otras 6.
- **Cuándo se ve:** el panel se construye después del ciclo, así que lo que ves es la vuelta anterior.
- **No alcanzables desde producción:** `salida_executor`, `franchise_*` y los `src/live_*.py`, que son de uso a mano.

## D. Los que miran y no hacen

| Módulo | ¿A propósito? |
|---|---|
| `roster_expansion_shadow` | a propósito ("FASE OBSERVADOR", 04/09), **sin fecha ni condición para encenderlo** |
| `sale_intent` | a propósito: "no se vende hasta que el dueño lo haya leído" |
| `el_que_publica` | a propósito: interruptor apagado |
| `el_cable` / `la_plaza_y_el_cable` | a propósito: `ENCENDIDO=False` |
| `season_horizon_shadow` | a propósito |
| `horizonte_adaptativo` | **se quedó así**: no lo importa nadie |
| candidata `CONSIDER_PLAYER_EXIT` del orquestador | **se quedó así**: `executable: False`, sin comentario |
| BUY V10 | **se quedó así**: armado, duerme porque nada pasa sus umbrales |
| Position Manager y repricing V10.7 | **no miran: escriben.** La etiqueta SHADOW se quedó así |

## E. Los 31 interruptores

**Ya encendidos (5):** `JORNADAS_POR_SU_FECHA`, `REVENTA_SOLO_SI_JUEGA`, `EL_ONCE_UNA_VEZ`,
`SOLVENCIA_POR_SU_PLAZO`, `LA_MONEDA_DE_LA_LIGA`.

**ENCENDER (11), en este orden, uno por vuelta:**

1. `SIN_REFERENCIA_ESCALA`: solo cambia el texto.
2. `REJA_CON_TOLERANCIA`: la caja cuadra al euro; apagado, 420.200 de más.
3. `LA_VUELTA_SE_APUNTA`: el registro de la vuelta.
4. `NO_REPETIR_LA_ESCRITURA`: sobraban 28 de 43 escrituras.
5. `CUPO_POR_ENVIOS`.
6. `CUPO_POR_VENTANA`.
7. `PUBLICAR_LA_COLA`: nunca publica a un titular.
8. `LISTON_DEL_MANAGER` junto con `MARGEN_DEL_MANAGER` = "2.45".
9. `OBJETIVOS_EL_CATALOGO`: de 142 a 504 con titularidad.
10. `LA_RESERVA_MIRA_EL_ONCE`, después de fusionar su rama.

**BORRAR (8):**

- `CESTA_SOLO_EL_SUELO`: el código no está al revés; lo que está al revés es la premisa. Por encima
  de 1,5 M los rivales ganan, y el filtro que hacía falta ya es `REVENTA_SOLO_SI_JUEGA`.
- `HORIZONTE_FIJO`: no lo lee nadie.
- `PRIMA_POR_TRAMO`: lo medido dice que empeora.
- `PUJAR_EN_LA_VENTANA`: arregla una alarma falsa.
- `SIN_ARCHIVO`, `SIN_CACHE` y `SIN_MERCADO_RIVALES`: vuelven a un mundo que ya no existe.
- `SIN_REVENTA`: si se quiere un freno de mano, quedarse con este y no con `SIN_SUBASTA`.

**EXCEPCIÓN (7):**

- `BID_SALT` y `VIGILA_DATA` no son interruptores (un secreto y una herramienta de la verja):
  sacarlos del inventario.
- `CALIDAD_ETIQUETA` y `VARA_PLANA`: se juzgan con 3 jornadas, y desde el 18-22/09 solo se ha jugado la J7.
- `COBRAR_EN_DEFICIT`: condición escrita, "en calma, en positivo".
- `SIN_SUBASTA`: el freno de mano.
- `TOPE_DEL_ONCE`: falta la tabla del peldaño.

## F. Las guardias: 184 en `origin/main`

```
defienden una decision viva      95
solo miran o pintan              55
defienden algo que ya no existe  20
fontaneria de la propia verja    14
se podrian borrar sin dejar desprotegida ninguna decision viva: 75 (41 %)
```

**Las 20 que defienden algo que ya no existe** son, entre otras: `portfolio_budget`,
`roster_plan_guardrail`, `balon_parado`, `rueda`, `calibracion_larga`, `la_salida_del_viaje`,
`el_dinero_cuadra`, `la_prima_de_compra`, `el_ojeador_conectado`, `los_tres_denominadores`,
`el_viaje_al_computer`, `el_carril_de_un_dia`, `la_plaza_y_el_cable`, `el_cable`,
`la_lista_de_la_compra`, `el_proposito`, `el_carry`, `la_direccion`, `la_escala` y
`solo_un_interruptor_por_vuelta`.

**Un caso aparte:** `soltar_un_grande`, la cuenta que según la verja sustituye a los intocables,
está escrita y probada, **pero no conectada a producción**.

## G. Qué no existe

| Cosa | ¿Existe? | ¿Regla o decisión? | Cuánto vale |
|---|---|---|---|
| **Racha diaria** | solo se lee | regla (`bonusDailyStreak`) | **~50.000 € al día.** La cobramos al máximo desde el 11/09 (4 cobros de 250.000); antes perdimos ~250.000. Nada avisa si se rompe; no se sabe qué la paga |
| **Comprar a managers** | valorado y cerrado (`acquisition_board.py:1399`) | **decisión nuestra** dentro de la regla: solo lo que el rival pone en el mercado | hoy no pasa el listón (0 de 35); con la valoración arreglada, el doble de escaparate |
| **Vender a managers** | encendido, con listón alto | decisión nuestra | +24 % a +32 % en 3 ventas; 2-4 M al año |
| **Los 391 sin dueño** | no se pueden pedir | regla de Biwenger | el Computer saca ~10,7 al día (n = 14 días) |
| **Cesiones** | no existen en el código | la regla lo permite (1-5 rondas) | no se sabe: ni una cesión en el tablón |
| **Pujar pensando en lo que necesita Pollo17** | no existe (`rival_bid_model` calibra importes; los demás solo miran) | decisión nuestra | puntos, n = 0 |
| **Retos** (`challengesAllow`) | no | la regla lo permite | no se sabe |
| Cláusula, capitán, suplentes, cambios durante la jornada, once ideal, MVP | no hace falta | la liga no los tiene | 0 |
| **Del código, mío:** el valor de reventa de lo que se ficha | no existe en `xi_upgrade_value` | decisión nuestra | es el #1 del veredicto |
