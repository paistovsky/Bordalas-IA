# La plaza y el cable — informe

**Rama:** `medir/la-plaza-y-el-cable` (desde `carril/el-de-un-dia`)
**Fecha:** 17/09/2026
**Verja:** 146/146 en verde, exit 0, salida a fichero
**Push:** NO. **`ENCENDIDO = False`.** Ninguna escritura contra Biwenger, ningún
umbral tocado, ningún `intent` movido.

---

## Lo primero: la foto del encargo no está en disco

El encargo trae números del 17/09 —14.447.000 € sobre la mesa, 8.874.116 € de
presupuesto, `free_slots: 0`, diez candidatos, cuatro bloqueados por el `intent`—.
**Ninguno de esos números existe en el repositorio.** Lo más fresco que hay:

```
data/snapshot_20260913_171717.json          13/09 17:17   la última foto completa
dashboard-v8/public/data/status.json        14/09 18:33   construida de esa foto
data/solvency/bitacora_del_saldo.jsonl      16/09 20:54   saldo y techo
data/rival_intelligence/board_events.json   16/09 22:55   el tablón
data/autopilot/price_history.json           16/09 18:23   623 jugadores
```

Así que **todo lo que sigue lleva la fecha de su fuente delante**, y donde el
mecanismo se puede medir pero el número de hoy no, digo las dos cosas por separado.
Lo que **no** he hecho es salir a la red a buscar la foto de hoy.

---

## BLOQUE 1 — El cable que falta

### 1.1 De dónde sale `acquisition_budget`, línea a línea

Corriendo `calculate_acquisition_budget` sobre la foto del 13/09:

```
saldo (market.status.balance)                      −1.299.834
cash_budget = max(saldo, 0) × ACQUISITION_CASH_PERCENT (1,00)        0

puerta 1   Hard Safety activo                           False
puerta 2   SOLVENCY_GUARANTEE garantizada               False   <- cierra
puerta 3   ventana de deuda segura abierta              False   <- cierra
puerta 4   ventana temporal permite deuda               False   <- cierra
additional_debt_headroom                                     0
debt_budget = headroom × ACQUISITION_DEBT_PERCENT (1,00)     0

gross_budget = caja + deuda                                  0
maximumBid de Biwenger                              12.455.166
total_budget = min(bruto, maximumBid)                        0
comprometido en pujas vivas                                  0
available_budget                                             0
```

**En esa foto el presupuesto de fichar es CERO**, y no por el techo de Biwenger —que
ofrece 12,4 M— sino porque el saldo está en rojo y `cash_budget = max(saldo, 0)`.

**Lo que entra:** el saldo, y el margen de deuda si las tres puertas están abiertas.
**Lo que no entra:** ni un euro de lo que hay encima de la mesa en ofertas vivas.

Ese es el cable. Y el argumento escrito en el docstring para no tenderlo —«sumarlo
sería contarlo dos veces»— resulta ser verdad a medias. La mitad que falta es esta:

### 1.2 Qué es `maximumBid`, medido

```
maximumBid = saldo + valor_de_plantilla / 4 − pujas_vivas_comprometidas
```

**18 de 18 combinaciones distintas, al euro**, sobre 95 fotos del 12/08 al 13/09 más
tres líneas de la bitácora del 16/09:

```
         saldo     plantilla  comprometido    maximumBid     calculado
    −4.651.032    52.980.000     1.390.000     7.203.968     7.203.968
    −4.651.032    52.740.000             0     8.533.968     8.533.968
    −1.299.834    55.020.000             0    12.455.166    12.455.166
       239.968    48.660.000     3.126.002     9.278.966     9.278.966
       239.968    48.660.000       480.000    11.924.968    11.924.968
     4.474.383    48.970.000    12.217.000     4.499.883     4.499.883
       131.717    55.680.000     2.482.028    11.569.689    11.569.689
    ...                                                      18 de 18
```

Las ocho que no cuadraban con `saldo + plantilla/4` cuadran todas al restar lo que
`build_bid_exposure` dice que hay comprometido, y el ajuste es exacto en las ocho.

**De cada jugador hay UN CUARTO de su precio dentro del techo.** Venderlo a precio de
mercado saca ese cuarto de la plantilla y mete el importe entero en el saldo:

> **el techo sube 0,75 × precio, y el saldo el importe entero.**

Así que la caja realizable **no está contada dos veces: está contada al 25 %**, y el
saldo —que es de donde sale `cash_budget`— no la tiene contada en absoluto.

### 1.3 Cuál sería contando lo realizable, y a quién habría que vender

En la foto del 13/09 hay **14 ofertas vivas del Computer** por jugadores nuestros,
48.582.300 € en total. Pasadas una a una por `position_guardrail.validate_sale_set`
—prefijo a prefijo, igual que hace `sale_order`— y por la única regla de
`untouchable_reason` que no depende de un dato que falte (el portero titular no se
rota):

```
jugador        pos       oferta      precio    prima  tit
Zubeldia       DEF    1.847.000   1.800.000  +2,61 %   no   CABE
Cepeda         DEL      638.400     640.000  −0,25 %   no   CABE
Pablo Durán    DEL      420.800     430.000  −2,14 %   no   CABE
Diego Conde    POR      244.800     240.000  +2,00 %   no   CABE
Yamal          DEL   20.680.800  21.720.000  −4,78 %   SI   NO: quedaría 1 delantero
Expósito       MED    5.358.600   5.280.000  +1,49 %   SI   CABE
Olasagasti     MED    3.256.200   3.300.000  −1,33 %   SI   CABE
Jutglà         DEL    3.115.700   3.050.000  +2,15 %   SI   NO: quedaría 1 delantero
Mangala        MED    2.498.100   2.410.000  +3,66 %   SI   NO: quedarían 2 medios
Pablo Ibáñez   MED    2.420.500   2.460.000  −1,61 %   SI   NO: quedarían 2 medios
Dituro         POR    2.373.400   2.310.000  +2,74 %   SI   NO: portero titular
Jonny          DEF    2.352.000   2.380.000  −1,18 %   SI   CABE
Djené          DEF    1.773.900   1.840.000  −3,59 %   SI   NO: quedarían 2 defensas
Manu Sánchez   DEF    1.602.100   1.620.000  −1,10 %   SI   NO: quedarían 2 defensas
```

```
VENDIBLES SIN ROMPER EL ONCE      7 de 14

presupuesto publicado hoy                  0 €
caja realizable                   14.117.800 €
saldo hoy                         −1.299.834 €
saldo tras vender                 12.817.966 €
maximumBid hoy                    12.455.166 €
maximumBid tras vender            23.055.466 €
```

**Cero contra catorce millones**, y las dos cifras salen de la misma foto.

Que 14.117.800 se parezca tanto a los 14.447.000 del encargo es probablemente
coincidencia —son fotos de días distintos—, pero da la escala.

### 1.4 La lista de operaciones completas, y por qué sale corta

Aquí el encargo pide más de lo que la foto en disco puede dar, y lo digo en vez de
rellenarlo:

- **La cola de venta de la foto del 14/09 llega vacía.** Los 17 salen excluidos con
  «sin escalón conocido». No es que nadie sobre: es que el dato de jerarquía no está
  en disco (`data/intelligence/starter_multisource_*.json` es del 17/08 y no trae
  escalón; `data/ff_html/*` son del 17/08). Por eso la tabla de arriba se monta
  contra las ofertas vivas del snapshot y el guardarrail, que sí están.

- **Los candidatos de esa foto son dos, no diez** —Kang-in Lee (9,04 M) y Parrott
  (6,47 M)— y **los dos salen `SIN_PRONOSTICO`**. Sin pronóstico de titularidad no se
  puede decir cuántos puntos gana el once, y no lo estimo.

Lo que sí queda hecho y probado es **el mecanismo**: `operacion_completa()` toma un
candidato, recorre la cola cogiendo vendedores hasta cubrir el coste, valida cada
prefijo con `validate_sale_set` —no reescribe el guardarrail, lo llama—, aparta con
su motivo al que rompería el once, dice si cabe la ficha y calcula los puntos netos
con la vara de cada posición puesta (`position_factor.factor_for`). La guardia
`test_una_venta_no_rompe_el_once` lo prueba con tres defensas y comprueba que vender
a los tres rompe el once de verdad, para que el fixture no pase por casualidad.

### 1.5 ¿Se puede saber el tope de fichas sin salir a la red?

**No.** Y he mirado las dos vías.

**En el estado no está.** Las reglas de la liga, clave a clave:

```
auctions False · balance hidden · bonusDailyStreak True · challengesAllow True
clause disabled · clauseIncrement 1 · customScore "" · favoritesAllow False
immediateSales 0 · lineupAllowExtra False · lineupCaptain False · lineupCoach False
lineupMaxClubPlayers 0 · lineupMultiPos False · lineupReserves False
lineupStriker False · loans allow · loansMaxRounds 5 · loansMinRounds 1
marketShowBids True · maxPurchasePrice 0 · onlyAdminPosts False · privacy private
splitRound ignoreFirst · superPicaExtraPoints True · userOffers market
```

`maxPurchasePrice` es el precio máximo de compra (0 = sin tope) y
`lineupMaxClubPlayers` cuántos del mismo club caben en el once (0 = sin tope).
**Ninguna clave es el tope de plantilla.**

**En el tablón se puede acotar, no fijar.** Reconstruyendo el tamaño de cada
plantilla desde el reparto inicial (`leagueReset`, 12 fichas) con las 356 operaciones
distintas de las 389 vistas —el tablón repite operaciones, medido el 10/09—:

```
manager                         reconstruido   ledger 14/09   dif   máximo
Pollo17                                   15             19    −4       21
Luismi_Haz                                14             17    −3       20
Manzagool                                 10             13    −3       18
Pepe Bordalás                             17             17    +0       18
DiosMande                                  8             11    −3       17
Mex                                       11             14    −3       16
Prinzipote                                14             17    −3       14
Alvaro Retamosa                           10             12    −2       12
```

**Nuestra línea cuadra al cero**, que es lo que hace creíble el método, y el máximo
—21, Pollo17 el 09/09— reproduce exactamente el número del informe del 10/09. Pero
las otras siete líneas salen entre 2 y 4 fichas **por debajo** de lo que dice el
ledger: al tablón le faltan compras suyas. **Todos los errores van en la misma
dirección, así que el tope real es 21 o más.**

> **Respuesta: el tope no se puede saber sin salir a la red. Paro aquí.**

Lo que sí se puede es mejorar la cota, y lo dejo dicho sin tocarlo: hoy
`count_free_slots` compara contra la plantilla **más grande de hoy** (19) y publica
2 huecos; contra la **más grande jamás vista** (21) serían 4. Las dos son cotas
inferiores; la segunda es estrictamente mejor y está en disco.

---

## BLOQUE 2 — El `intent`, y no es el `max()`

### La respuesta corta

**No es el mismo `max()`. Es otro sitio, y el motivo que se publica está caducado.**

```
DEPLOYMENT_ENABLED = True          (DEPLOYMENT_DEFAULT = "1", deployment.py:92)
```

Con el interruptor **encendido** —que es lo que hay desde el 13/09 y lo que corre en
el workflow, que no lo pisa— la etiqueta la reparte
`deployment.classify_operation`. El `max(opciones, key=value)` de
`acquisition_valuation:1190` **solo corre con el interruptor apagado**.

Y `roster_expansion_shadow.blocked_reason:183` publica, para Budimir, Jonathan David,
Alfonso Herrero y Pépé:

> «La vía del once le da valor, pero el `intent` se elige por euros y gana la
> reventa: entonces se le exige rendimiento de especulación.»

**Eso describe un mecanismo que no está corriendo.** El mensaje no sale truncado: el
JSON lleva la frase entera más el `reason` de la fila. Lo que le pasa es que está
caducado. El panel solo pinta la etiqueta corta —«gana la reventa en el reparto por
euros»— y deja el texto en el `title` del `<td>`; de ahí el aspecto de frase cortada.

### La cadena de verdad, medida

Sobre las 43 filas valoradas de la foto del 14/09:

```
intent                { SPECULATION: 43 }
operation_class       { TRADE: 43 }
roster_fill_decision  { FICHA_NO_APTA: 43 }
xi_decision           { SIN_PRONOSTICO: 43 }
con xi_value > 0              0
con xi_value > precio         0
```

```
xi_decision = SIN_PRONOSTICO
   -> xi_value = 0
   -> ninguna vía de fichaje llega al precio  (deployment.py:201-210)
   -> classify_operation: fichaje = []  ->  clase TRADE
   -> intent = SPECULATION  ->  listón del 3 %
```

**El freno de arriba del todo no es el `intent`: es que no hay pronóstico de
titularidad.** Y el motivo bueno ya viaja en la propia fila, sin que nadie lo lea:

```
deployment.reason      "No entra al once ni llena hueco: se compra para revender,
                        y sale del bolsillo de especular."
deployment.route       COMPUTER_RESALE
market_gate.route_now  COMPUTER_RESALE
```

En el encargo esos cuatro salen con `INTENT_POR_EUROS`, que es la segunda puerta de
`blocked_reason` —la que se usa cuando `xi_decision` **no** es un veto—. O sea que en
la foto del 17/09 sí tienen pronóstico, y lo que los tumba es el filtro de precio de
`classify_operation`: **su valor como fichaje no llega a lo que cuestan.** No lo
puedo confirmar contra esa foto, que no está en disco.

### El mapa: qué decide cada `intent` y qué se cae si se toca

| etiqueta | sitio | qué decide |
|---|---|---|
| `SPECULATION` | `rival_bid_model.optimal_bid:1128` | **quita el tope de prima (+0,25 %) si NO es SPECULATION** |
| `SPECULATION` | `rival_bid_model.optimal_bid:1176` | el listón del 3 % de rendimiento sobre el capital |
| `SPECULATION` | `rival_bid_model.optimal_bid:1209` | el mínimo de 25.000 € de ganancia esperada |
| `XI_UPGRADE` | `acquisition_budget.budget_for_intent` | qué bolsillo se aplica: fichar o especular |
| `XI_UPGRADE` | `acquisition_board:1189` | `budget_source`: FICHAJES o ESPECULACION en pantalla |
| `XI_UPGRADE` | `los_dos_techos:298` | qué columna se marca: QUEDARSE o REVENDER |
| `XI_UPGRADE` | `hold_budget.hold_pocket` | de qué bolsillo sale la vía TENER |
| `XI_UPGRADE` | `deployment.signing_priority` | el escalón de prioridad cuando el bolsillo no llega |
| `XI_UPGRADE` | `autopilot_executor:2013` y `:2092` | **qué presupuesto lee el EJECUTOR al escribir la puja** |
| cualquiera | `roster_expansion_shadow.blocked_reason:183` | la segunda puerta de la lista de ampliar plantilla |
| cualquiera | `bid_outcome_ledger:159` | con qué etiqueta se apunta la puja en el libro |
| cualquiera | `los_tres_denominadores:726` | qué listón se le aplica en la reconstrucción |

Y los sitios donde se **decide** la etiqueta, que son dos y no seis:

```
deployment.classify_operation:253   INTENT_BY_CLASS[clase]     <- el de hoy
acquisition_valuation:1219          clase["intent"] si DEPLOYMENT_ENABLED
                                    else mejor.get("intent")   <- el max() por euros
```

Los cuatro `max(key=value)` que quedan en `acquisition_valuation` (952, 1035, 1052,
1190) y los dos de `deployment` (222, 226) siguen ahí, pero solo el de la 1190 toca
el `intent`, y solo con el interruptor apagado.

> **Qué se cae si se toca:** quitarle `SPECULATION` a una vía le quita el listón
> del 3 % **y el tope de prima a la vez** —medido ayer: con etiqueta no puja; sin
> etiqueta puja +0,52 % y el tope pasa a ser el valor entero—. **Los frenos cuelgan
> de la misma cadena que la puerta.** No he tocado ninguno.

---

## BLOQUE 3 — ¿El pago es lineal? El dato lo cierra, y no a favor de ninguno de los dos

### 1. ¿Hay premio por GANAR una jornada? **No. Y hay premio por quedar ÚLTIMO.**

En las reglas de la liga, `/rounds/data/league/settings`:

```
bonusPoint           30.000       € por punto
bonusFixed                0
bonusIdealLineup          0
bonusGameMVP              0
bonusInverse          False
bonusRoundPosition   [[−1, 500000], [−2, 250000], [−3, 100000]]
```

**Los índices son negativos: se cuentan desde el final.** Y se ve contra lo pagado de
verdad — 6 jornadas distintas en el tablón (9 eventos `roundFinished`, tres
repetidos con otro `event_id`), 43 filas de resultado:

```
Jornada 5 (id 4903), n=8

  1. Pepe Bordalás   61 pts   1.830.000   = 61 × 30.000   exacto
  2. Pollo17         55 pts   1.650.000   = 55 × 30.000   exacto
  3. Manzagool       47 pts   1.410.000   = 47 × 30.000   exacto
  4. Luismi_Haz      46 pts   1.380.000   = 46 × 30.000   exacto
  5. Mex             45 pts   1.350.000   = 45 × 30.000   exacto
  6. Prinzipote      45 pts   1.450.000   = 45 × 30.000 + 100.000   3º por la cola
  7. DiosMande       37 pts   1.360.000   = 37 × 30.000 + 250.000   2º por la cola
  8. Alvaro          15 pts     950.000   = 15 × 30.000 + 500.000   ÚLTIMO
```

**En las 6 jornadas, el ganador cobró exactamente `puntos × 30.000`. Cero extra, las
seis veces.** Los únicos que cobran algo encima son los tres últimos, y siempre
+500.000 / +250.000 / +100.000, clavado con las reglas.

(La única jornada sin premios de posición es la «Jornada 1» con `step=1`. Es
`splitRound: ignoreFirst`: el primer tramo de una jornada partida no los paga. La
«Jornada 1 (aplazada)» con `step=2` sí los pagó.)

### 2. ¿Hay premio por la posición FINAL de temporada? **No consta.**

- En las reglas de la liga no hay ninguna clave de premio por clasificación final.
  `bonusFixed` es 0.
- En el tablón, los 582 eventos se reparten en 13 tipos, y el único que reparte
  dinero fuera de `roundFinished` es `bonus`: **9 eventos, los 9 `dailyStreak`,
  250.000 € cada uno, 3.000.000 € en total.** Ninguno de posición final.
- Las 13 `adminText` son publicidad de Biwenger (Waylet, Super Pica, Champions).
- Los 319 `bettingPool` son la quiniela 1X2, que no paga nada en esta liga.

**No consta. No lo estimo y no salgo a la red a buscarlo.**

### El veredicto

> **El pago es lineal de principio a fin: 30.000 € por punto, con la única excepción
> de un consuelo a los tres últimos. No hay bote de final de temporada del que se
> sepa.**

Con un pago lineal, **20 y 0 paga exactamente igual que 10 y 10**, y la varianza no
vale nada. **Tu lado de la discusión gana, y por un margen mayor del que pedías:** no
es solo que no haya premio por ganar la jornada; es que hay premio por perderla.

Ahora bien, **lo que sí importa y no es lineal es el orden final**, si es que hay algo
en juego fuera de Biwenger (una apuesta entre vosotros, el honor, lo que sea). Eso no
está en el estado y el dueño es el único que lo sabe. Si quedar primero vale algo que
el tablón no registra, la varianza vuelve a valer y el argumento del dueño vuelve a
estar vivo. **Lo que he podido medir es lo que paga Biwenger, y eso es lineal.**

---

## BLOQUE 4 — ¿El Computer paga más por los que bajan?

### Sí, aguanta. Y mide la mitad.

Dos censos independientes y cuatro cuentas.

**CENSO A — las 90 ofertas VIVAS del Computer**, deduplicadas por `offer_id` sobre las
95 fotos del 12/08 al 13/09. Este **no tiene sesgo de aceptación**: es lo que el
Computer ofrece, no lo que la gente acepta.

```
partido por `priceIncrement` de la propia foto (cubre las 90)

  tramo        n     mediana       media    bajo mercado
  SUBIA       52    +0,0299 %   −0,1855 %       26/52
  PLANO       11    +0,5758 %   +0,1415 %        4/11
  BAJABA      27    +1,8446 %   +1,1009 %       10/27
                                        hueco  +1,81 pp
```

```
partido por price_history a 24 h (solo 36 de las 90 tienen histórico)

  SUBIA       20    −0,8880 %   −0,9227 %       13/20
  PLANO        3    −1,1765 %   −0,7477 %         2/3     TRAMO CORTO
  BAJABA      13    +2,1541 %   +1,2005 %        5/13
                                        hueco  +3,04 pp
```

**CENSO B — las 172 ventas ACEPTADAS al Computer de toda la liga**, del tablón. Este
**sí** lleva el sesgo que destapamos ayer —la gente vende el día que la oferta viene
buena—, así que vale de contraste, no de prueba:

```
  SUBIA       35    +1,8041 %   +1,5639 %        7/35
  PLANO       36    +0,7295 %   +0,4527 %       15/36
  BAJABA      67    +3,0836 %   +2,9122 %       10/67
                                        hueco  +1,28 pp
```

**DENTRO DE CADA JUGADOR**, que es la cuenta que quita el confundido de «a quién le
llegan ofertas»:

```
  Jutglà      SUBIA +1,66 % (n=4)   BAJABA +2,15 % (n=3)   +0,49 pp
  Yeray       SUBIA +1,39 % (n=3)   BAJABA +1,84 % (n=1)   +0,46 pp
  Yamal       SUBIA −2,26 % (n=3)   BAJABA +1,18 % (n=2)   +3,44 pp
  Dituro      SUBIA +0,30 % (n=3)   BAJABA +1,12 % (n=4)   +0,83 pp
  Zubeldia    SUBIA −5,44 % (n=1)   BAJABA +2,61 % (n=1)   +8,05 pp

  n=5 jugadores con las dos direcciones. BAJABA paga más en 5 de 5.
  Hueco mediano +0,83 pp.
```

### Y la significación, porque «n=8 y n=5» era el aviso correcto

```
  dentro del jugador      +0,83 pp   p = 0,031   n=5 jugadores   test del signo
  ofertas (increment)     +1,81 pp   p = 0,050   n=52 / 27       permutación
  ventas aceptadas        +1,28 pp   p = 0,053   n=35 / 67       permutación
  ofertas (histórico)     +3,04 pp   p = 0,091   n=20 / 13       permutación
```

(Permutación bilateral, 20.000 barajes, semilla fija.)

**No he podido confirmar el confundido con el nivel de precio**, y lo comprobé: los
que subían valen 3.549.615 € de media y los que bajaban 3.515.185 €, y partiendo por
encima y por debajo de 2 M el hueco sale en la misma dirección en los dos tramos
(+2,27 pp en los caros, +1,54 pp en los baratos).

> **Las cuatro cuentas van en la misma dirección y ninguna sola lo demuestra.** La
> única que baja de 0,05 sin discusión es la de dentro del jugador, y es la de `n`
> más pequeño. **El +3,27 pp de tu foto (n=8 contra n=5) es el borde alto del rango,
> no el centro. Lo real está entre +0,8 y +1,8 pp.**

### Qué ancla usa: ninguna que se pueda escribir

```
ancla                     n    mediana      IQR     desv   ±0,5 %
precio de HOY           141     1,0234   0,0382   0,0277   19/141
precio de AYER          138     1,0163   0,0411   0,0293   19/138

mezcla α × hoy + (1−α) × ayer
   α=0,00  desv 0,0293     α=0,50  desv 0,0259     α=1,00  desv 0,0280
   α=0,25  desv 0,0270     α=0,75  desv 0,0263
```

La más estrecha es el precio de hoy, y su IQR es de casi **4 puntos porcentuales**.
La mejor mezcla baja la desviación un 8 %, que es ruido. Probé también anteayer, la
media de 3 días, la de 7 y el `fantasyPrice`: todas peores.

**No hay fórmula que reproduzca la oferta del Computer.** Y la hipótesis del retardo
puro —«usa el precio de ayer tal cual»— queda descartada: si lo usara, la prima sobre
el precio de hoy sería exactamente menos la variación de la víspera, o sea **pendiente
−1**. Medido:

```
  ofertas vivas       n= 36    pendiente −0,2418    R² = 0,2488
  ventas aceptadas    n=142    pendiente −0,4261    R² = 0,1238
```

Ni de lejos. **No es un retardo: es dispersión con un sesgo pequeño y persistente**, y
ese sesgo es justo el hueco de arriba.

---

## ¿Está del revés el plan del ojeador? Para el carril de un día, SÍ

Sin suavizarlo, que es lo que pediste.

**La persistencia de la dirección del precio, n = 16.873 pares de días seguidos**
(623 jugadores, `price_history.json`, 16/08 al 16/09):

```
  ayer SUBE    n=4.430   ->  hoy  SUBE 88,3 %   PLANO  8,9 %   BAJA  2,8 %
  ayer PLANO   n=5.642   ->  hoy  SUBE  6,7 %   PLANO 81,4 %   BAJA 11,9 %
  ayer BAJA    n=6.801   ->  hoy  SUBE  1,6 %   PLANO  9,4 %   BAJA 89,0 %
```

**Comprar lo que sube y venderlo al día siguiente es vender en el tramo SUBIA nueve
de cada diez veces, y ese es el tramo que el Computer paga peor.**

Ahora, la parte que salva el plan a plazos largos. Ayer medimos de dónde sale el
+3,23 % del viaje medio:

```
  deriva del mercado mientras lo tenemos   +1,97 pp
  lo que aporta el Computer                +1,30 pp
```

Así que:

- **Viaje de 1 día (el carril).** La deriva mide +0,20 % —el mercado no se mueve en
  una noche—. Lo único que queda es la prima del Computer, y comprar lo que sube te
  mete en el tramo malo. **Aquí el plan está del revés, y no un poco: te estás
  pagando entre 0,8 y 1,8 pp de peaje en el único sitio donde hay margen.** El listón
  del carril es 1,2525 % y su techo 1,5075 %: un peaje de 1,8 pp se lo come entero.

- **Viaje de 8 días o más.** La deriva es +10,80 pp. Un peaje de 1,8 pp no lo tumba.
  **Aquí el plan no está del revés: está a la mitad de lo que parecía.**

> **Lo que hay que separar no es «comprar lo que sube» de «comprar lo que baja».
> Es la fecha de venta de la fecha de compra.** Comprar un jugador que sube está
> bien: sube. Venderlo el día siguiente, mientras sigue subiendo, es vendérselo al
> Computer justo cuando menos paga.
>
> **Y no lo arreglo.** Es un cambio de regla y va con esta tabla delante.

---

## Y una corrección tuya que confirmo, y un matiz

**Tu retirada del argumento de Yamal está bien hecha**, y el dato del día la
refuerza desde otro sitio: el Computer ofrece por Yamal **20.680.800 € sobre un
precio de 21.720.000, un −4,78 %**. La peor prima de las catorce ofertas de la foto.
No solo es que no haya sustituto: es que el único comprador que hay paga mal.

El matiz: en la foto del 13/09, el guardarrail **no deja venderlo de todos modos** —
quedaría un delantero y hacen falta dos—. Como avisaba el docstring de `sale_intent`,
hoy Yamal sigue a salvo por accidente. **No propongo venderlo; lo que digo es que la
razón por la que no se vende no es la que se cree.**

---

## Lo que no hice, y por qué

- **Ni una escritura contra Biwenger.** Ni pujas, ni ofertas, ni ventas, ni aceptar
  ninguna oferta. La de Balde no la he tocado ni la he mirado.
- **No abrí ofertas a rivales.** Es otro encargo.
- **No encendí nada.** `ENCENDIDO = False`, con guardia.
- **No toqué ningún umbral:** ni el listón del 3 %, ni el suelo del +1 %, ni
  `bid_cap`, ni `PRIMA_MAXIMA_DE_PUJA`, ni `MIN_WIN_PROBABILITY`, ni el cupo, ni las
  cinco de `PUEDEN_ENCERRARLO`, ni `MAX_SINGLE_SPECULATION_PERCENT`, ni
  `MAX_SAFE_DEBT`, ni `ACQUISITION_CASH_PERCENT`, ni `DEPLOYMENT_DEFAULT`.
- **No toqué ningún `intent`**, ni `blocked_reason`, ni `count_free_slots`. Los
  mapeo y digo qué les pasa.
- **No propuse vender a Yamal.**
- **No salí a la red** a por el tope de fichas ni a por la foto de hoy.
- **No toqué `.github/workflows/bordalas-live.yml`.**
- **No empujé.**

### Lo que NO pude contestar, y es del encargo

1. **Los diez candidatos con su operación completa.** La foto en disco tiene dos, los
   dos `SIN_PRONOSTICO`. El mecanismo está escrito y probado; la tabla necesita la
   foto de hoy.
2. **El motivo exacto que bloquea a Budimir, Jonathan David, Alfonso Herrero y
   Pépé.** Sé quién reparte la etiqueta y con qué regla, y sé que la frase publicada
   describe otro mecanismo. Lo que no puedo es correr esa regla contra unas filas que
   no tengo.
3. **La cola de venta de 11 jugadores.** En disco llega vacía por falta del escalón.

Las tres se contestan solas corriendo un ciclo y volviendo a mirar. Ninguna necesita
que se toque código.

---

## Guardias

**+1 módulo, 7 guardias**, en `src/analysis/test_la_plaza_y_el_cable_v1.py`, dada de
alta en `scripts/run_validation_gate.py`.

Las cuatro del encargo, más la del techo medido, la del pago de la liga y la del
interruptor. **Las once inyecciones de fallo muerden**, probadas reintroduciendo el
fallo en memoria:

```
MUERDE  presupuesto / con la cola vacía devuelve 0 en vez de None
MUERDE  presupuesto / cuenta el valor a mercado como si fuera caja
MUERDE  operación / se salta el guardarrail
MUERDE  operación / puntos netos sin la vara
MUERDE  motivo / contesta con el mecanismo caducado
MUERDE  motivo / sale cortado
MUERDE  prima / tramos sin su `n`
MUERDE  prima / censo vacío publica tramos a cero
MUERDE  techo / cuenta la plantilla entera en vez de un cuarto
MUERDE  premios / lee −1 como «el primero»
MUERDE  interruptor / encendido
```

**Y una que no mordía, dicho porque importa más que las que sí:**

`test_una_venta_no_rompe_el_once` llama a `build_position_guardrail`, y eso —por
`_keep_value` → `get_starter_lookup()`— **abre
`data/intelligence/futbolfantasy_board.json`**. El vigilante de la verja la censó
leyendo `data/` sin que ninguna línea de la guardia lo pidiera. Una guardia que lee
estado de producción cambia de respuesta el día que el ciclo escriba ese fichero, y
entonces no prueba el código: prueba el disco. Arreglado clavando la caché de
pronósticos vacía antes de nada —no parcheando `build_position_guardrail`, que sería
probar otra cosa— y con una aserción propia que falla si vuelve a leer.

**Ninguna guardia lee `data/`, sale a la red ni mira el reloj.** La vara entra por
argumento en vez de leerse del entorno, y los instantes son fijos.

---

## Medición

`scripts/la_plaza_y_el_cable.py` — 418 líneas de salida, exit 0, solo lectura de
disco, sin red.

```
python scripts/la_plaza_y_el_cable.py > salida.txt 2>&1
echo $?
```

---

## Lo que contradijo al encargo, y ganó la medición

1. **El motivo del `intent` no está truncado: está caducado.** Y no lo pone el
   `max()` por euros, lo pone `classify_operation`.
2. **El freno de arriba no es el `intent`:** en la foto que tengo, las 43 filas caen
   antes, en `SIN_PRONOSTICO`.
3. **La caja realizable no está contada dos veces: está contada al 25 %.** El
   docstring de `acquisition_budget` decía lo contrario y por eso el cable no se
   tendió.
4. **El pago no es «lineal y ya»: hay un premio por quedar ÚLTIMO.** El pago al
   ganador sí es exactamente lineal, seis de seis.
5. **El hueco del Computer aguanta pero mide la mitad:** +0,8 a +1,8 pp, no +3,3.
6. **El plan del ojeador no está del revés en general: lo está a un día.** A ocho
   días o más, la deriva del mercado se come el peaje.
7. **El tope de fichas no se puede saber sin red**, pero la cota que se usa hoy (19)
   es peor que la que está en disco (21).
