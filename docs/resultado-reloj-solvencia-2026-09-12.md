# El reloj de la solvencia — resultado de la noche del 11→12/09/2026

## ¿Va a llegar Pepe en positivo al próximo T−6h, y con qué venta?

**Sí. Vendiendo a Lucas Cepeda por 471.200 €, y el saldo queda en
+49.408 €.**

```
primer partido de la jornada 5     11/09/2026  ~21:00
cierre real (T-15 min)             11/09/2026   20:45
PLAZO DE SOLVENCIA (T-6h)          11/09/2026   14:45
                                   ---------------------
                                   quedan 144,7 h desde la foto

saldo hoy                             -421.792 €
venta que lo tapa       Lucas Cepeda   +471.200 €   (oferta viva)
saldo después                           +49.408 €
daño al once                          ninguno: no juega
```

Es exactamente el **plan A** del motor de solvencia, al euro. Dos
caminos independientes —su cálculo y la cola de venta— eligen al mismo
jugador y llegan al mismo número.

**Y hay una condición que hay que mirar mañana.** Pepe tiene puesta una
puja viva de **1.229.925 € por Kiko Femenía**, que se resuelve en el
reset de las 07:00. Si la gana, el déficit pasa a **1.651.717 €** y la
venta que lo tapa deja de ser Cepeda: sería **Pablo Ibáñez por
2.150.700 €**, saldo +498.983. También llega, pero saca de la plantilla
4,5 veces más.

---

## Lo que se puede demostrar hoy y anoche no

**El camino de la venta funciona entero.** Hay una prueba que lo recorre
con el cliente de escritura suplantado y comprueba lo último que se
puede comprobar sin vender de verdad:

```
PUT https://biwenger.as.com/api/v2/offers/987654
{"status": "accepted"}
```

Que es exactamente lo que faltaba el 19/08: **el cuerpo**. Los siete
tramos —reserva de solvencia, `ACCEPT_BEFORE_EXPIRY`,
`ACCEPT_FOR_SOLVENCY`, filtro de cobro, emisión del orquestador,
barrera temporal y gatillo— pasan uno detrás de otro.

**Conclusión: el camino estaba bien. Lo que no había era el caso.**

`ACCEPT_FOR_SOLVENCY` exige que la oferta esté reservada para solvencia
**y** que aprieten el reloj o la caducidad. Desde que se conectó el
gatillo el 18/08 no ha coincidido nunca: en la foto del 05/09 quedaban
150,7 h para el cierre y las ofertas caducaban en 16,9 h. No es que
fallase — es que no tocaba.

---

# 1. El reloj

`src/analysis/solvency_clock.py`, en pantalla en **ESTRATEGIA**, encima
de los tres planes de solvencia — que es lo que les faltaba: nadie
decía cuándo tocaban.

## El plazo no es un número nuevo

`ACCEPT_BEFORE_DEADLINE_HOURS` vale **6.0** desde que se escribió, y
hace literalmente esto: con la jornada encima, una oferta reservada
para solvencia se cobra aunque todavía no caduque. **La regla que
pediste ya estaba en el código.** El reloj la importa en vez de
copiarla; un segundo número sería un segundo sitio donde equivocarse.

## Las dos velocidades, medidas

Sobre 67,1 horas de tablón de la liga en la foto de producción:

| | Movimientos | Uno cada |
|---|---|---|
| Ventas al Computer | 19 | **3,5 h** |
| Compras al Computer | 10 | 6,7 h |
| **Compras de mánager a mánager** | **1** | **67,1 h** |

**Una.** En casi tres días, con siete mánagers, y fue la nuestra
(Yusi Enríquez → Prinzipote). *Publicar y esperar a que un rival puje
no es un plan con fecha: es una lotería.*

La liquidez que sí tiene reloj es la del Computer. Sus ofertas caducan
**siempre en el reset de las 07:00**, en dos cohortes: 5 ofertas a
16,9 h y 7 a 40,9 h. **La diferencia entre cohortes es de 24,0 horas
exactas.**

De ahí sale el margen, y no de un número redondo: **si el déficit no
está cubierto, hace falta un ciclo entero del Computer —24 h— para que
valore lo publicado y ofrezca.** Menos de eso y solo queda la lotería
de las 67 horas.

## Los estados

| Estado | Cuándo | Qué hace |
|---|---|---|
| `SIN_DEUDA` | saldo ≥ 0 | nada |
| `CUBIERTO` | las ofertas vivas tapan el déficit | esperar: aceptar es inmediato |
| `CUBIERTO_PERO_CADUCA` | tapan hoy, no al plazo | cobrar antes de perderlas |
| `PUBLICAR` | no tapan, y quedan ≥ 24 h | publicar ya |
| `CRITICO` | no tapan, y quedan < 24 h | solo queda la lotería |
| `EN_EL_PLAZO` | dentro de las 6 h con déficit | cobrar en este ciclo |

**Hoy: `CUBIERTO`.** 421.792 € de déficit contra 14.678.700 € en
ofertas que aguantan las próximas 24 h.

---

# 2. Quién gana el empate

**Dentro de las 6 h manda la solvencia. Fuera, manda el motor de
ofertas.**

Y no es una regla nueva puesta encima: es la que ya ejecuta el motor de
reroll cuando convierte una oferta reservada en `ACCEPT_BEFORE_EXPIRY`.
El reloj usa el mismo umbral y **lo publica con su motivo**:

> *Quedan 5,0 h para el cierre y el saldo es −421.792 EUR: manda la
> solvencia por encima del HOLD del motor de ofertas.*

Y lejos del plazo lo dice igual de claro, que es la mitad que se olvida:

> *Quedan 144,7 h de margen: lejos del plazo manda el motor de ofertas,
> que para eso mira el precio.*

Malvender con seis días por delante es la otra forma de perder.

## El arreglo que sí mueve dinero: vender lo justo

Medido en producción: **déficit de 421.792 € y la oferta reservada para
taparlo era la de Gustavo Puerta, 3.377.100 €.** Ocho veces lo
necesario — y es el **plan C** del motor de solvencia, el que deja el
once incompleto (4,15 % de daño). El plan A era Cepeda por 471.200 sin
tocar el once.

La reserva elige por prima: razonable para el precio, ciego para el
tamaño. Ahora `offers_to_collect`, **entre ofertas ya aprobadas**,
cobra la más pequeña que tape el agujero. Si ninguna lo tapa, la más
grande. Sin déficit, el orden sigue siendo el de siempre.

No he tocado `reservation_key`: eso es la garantía de solvencia y
cambiarla mueve dinero por una vía que este encargo no pedía. Queda
apuntado abajo.

---

# 3. El portero

`untouchable_reason` protegía al portero titular mirando `in_lineup`;
el roster del dashboard trae ese dato como `is_starter`. **Dituro
—único portero, titular— no salía como intocable.** Lo único que
impedía venderlo era el suelo posicional.

Es palabra por palabra el accidente contra el que avisa el docstring
del propio módulo:

> *"hoy Yamal solo está a salvo por accidente: el guardarraíl posicional
> bloquea la venta porque hay exactamente dos delanteros. El día que
> entre un tercero, esa protección desaparece sola y nadie se entera."*

No toqué la regla: le doy el dato con el nombre que espera. Y hay
guardia con las dos formas de escribirlo **y** con que el segundo
portero siga siendo vendible con ambas — si no, no se podría rotar
nunca.

---

# 4. Lo que me sorprendió

## 1. Casi publico un panel en una página muerta

Monté el reloj en `AnalysisPage.jsx`. Mi propia guardia se puso verde:
la página importa el componente y lo monta. **Y el panel no salía por
ninguna pantalla.**

`AnalysisPage.jsx` no está enrutada en `App.jsx`. Es código muerto que
importa siete paneles —`MarketClockPanel`, `ExposurePanel`,
`GuardrailPanel`, `SpeculationPanel`, `SolvencyPanel`,
`AcquisitionPanel`, `LeaguePanel`— y no lo ve nadie.

Lo cacé mirando el `dist/`: la cadena `"RELOJ DE SOLVENCIA"` no estaba
en el bundle. **Comprobar que un componente está en una página no
basta; hay que comprobar que esa página existe para la app.** Hay
guardia nueva que lo hace, y el reloj vive ahora en ESTRATEGIA.

Es la decimoquinta vez que este repo pierde un dato en el último metro,
y la primera en la que el último metro tenía un metro más.

## 2. La regla que pediste ya estaba escrita

`ACCEPT_BEFORE_DEADLINE_HOURS = 6.0`, con este comentario dentro:

> *"Sin esta regla la única presión era la caducidad de la propia
> oferta, que es independiente del calendario: se podía llegar al cierre
> de jornada en negativo con ofertas buenas sin tocar."*

Alguien ya había pensado exactamente esto. Lo que faltaba no era la
regla: era **que se viera** y que alguien dijera cuándo aprieta.

## 3. La primera versión del reloj daba una alarma absurda

Preguntaba *"¿sobreviven las ofertas de hoy hasta el plazo?"* con el
plazo a 144,7 h. Como las del Computer caducan cada 24 h, la respuesta
era siempre no, y el reloj decía **"cubierto pero caduca" a seis días
del cierre**.

El horizonte que importa no es el plazo: es el plazo **o un ciclo del
Computer, el que sea menor**. Más allá de un ciclo, las ofertas de hoy
no son las que van a tapar nada. Hay guardia con ese caso exacto.

## 4. La misma coma me mordió dos noches seguidas

`.replace(",", ".")` sobre la frase entera dejó escrito *"cubren los
421.792 EUR. pero caducan"*. Pasó el 11/09 en `sale_order` y volvió a
pasar el 12/09 en el reloj. Ahora hay una función `euros()` y una
guardia que busca esa secuencia concreta.

## 5. Y una que no es mérito mío

`test_intocables_v1` pasó **sin cambios** después de arreglar el
portero, porque estaba escrita contra el comportamiento y no contra la
implementación. Cinco noches de guardias en rojo y ésta se dejó
extender sin pelear.

---

# 5. Lo que se queda fuera, y por qué

**`DEPLOYMENT_ENABLED` sigue apagado y la deuda para fichar también.**
Lo dice el encargo y estoy de acuerdo: se enciende cuando se vea una
venta ejecutada de verdad, no una prueba. La diferencia entre las dos
es todo lo que este repo lleva aprendiendo.

**La próxima jornada obliga a que ocurra.** Si Pepe llega al 11/09 a
las 14:45 en rojo, es que esto no funciona, y se sabrá sin discutirlo.

**`reservation_key`.** Reserva por prima y puede reservar de más. El
arreglo de esta noche lo compensa en el momento de cobrar —se cobra la
más pequeña que tape—, pero la reserva sigue eligiendo grande. Tocarla
es mover la garantía de solvencia y no lo pedía este encargo.

**Ningún tope, ningún porcentaje y `MAX_SAFE_DEBT`: sin tocar.**

---

## Cómo quedó

```
rama          reloj-solvencia/2026-09-12   (sin subir: el push lo das tú)
main          intacto
puerta        75/75 en verde  (72 al empezar, 3 guardias nuevas)
commits       3
frontend      npm run build OK · NO desplegado · dist/ intacto

PUNTO 1   HECHO. Reloj con los seis estados, en ESTRATEGIA, con el
          margen de publicacion medido sobre 67,1 h de tablon.

PUNTO 2   HECHO, y resulta que ya existia: el desempate a 6 h es
          ACCEPT_BEFORE_DEADLINE_HOURS. Ahora se ve, con su motivo,
          y se cobra la venta mas pequeña que tape el agujero.

PUNTO 3   DEMOSTRADO. `test_venta_ejecutable_v1` recorre los siete
          tramos hasta el PUT con cuerpo. 14 pruebas.

PUNTO 4   HECHO. El portero ya no depende del suelo posicional.

interruptor   DEPLOYMENT_ENABLED = False    sin tocar
              MAX_SAFE_DEBT                 sin tocar
              deuda para fichar             sin tocar
```

**La frase para mañana:** el tubo estaba bien y la regla de las seis
horas ya estaba escrita; lo que faltaba era que alguien dijera cuándo
aprieta y a quién se vende. Con eso puesto, Pepe llega al plazo del
11/09 a las 14:45 en positivo vendiendo a Lucas Cepeda por 471.200 € y
sin tocar el once. Y si gana la puja de Kiko Femenía, el que sale es
Pablo Ibáñez por 2.150.700 €.
