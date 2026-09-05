# Comprar sin miedo — resultado de la noche del 10→11/09/2026

## La puerta del punto 1 no se pasó. No hay nada encendido.

**`DEPLOYMENT_ENABLED` sigue apagado y no se ha tocado la deuda.** El
punto 3 del encargo no se ha ejecutado, por la regla que trae el propio
encargo delante:

> *"si no puedes demostrar que Pepe vende, deja `DEPLOYMENT_ENABLED`
> apagado, escribe por qué, y no sigas con el punto 3."*

No se pudo demostrar. La evidencia está en el apartado 1.

Rama `sin-miedo/2026-09-11`. **Puerta: 73 de 73 en verde** (72 al
empezar). `main` intacto. `npm run build` pasa. Nada desplegado. **El
push lo das tú.**

---

## Cómo se apaga (y cómo se enciende)

No hay nada que apagar esta noche: **el interruptor ya está apagado y
la pieza nueva no decide nada.** Aun así, esto es lo que hay:

```
                      src/analysis/deployment.py
    DEPLOYMENT_ENABLED = False        <- la constante
    DEPLOYMENT_ENABLED=1              <- o la variable de entorno

                      src/analysis/sale_order.py
    No tiene interruptor porque no hace nada: calcula la cola de
    venta y la publica. No importa ningún executor -hay guardia con
    `ast` que lo comprueba- y no escribe.
```

**Si lo enciendes**, `test_despliegue_v1` se pone **rojo** a propósito:
`test_apagado_de_serie` afirma que está apagado y su docstring lleva
dentro la evidencia de esta noche. Es una alarma, no un estorbo:
quien lo encienda tiene que leer antes por qué se dejó cerrado.

**Al apagarlo vuelve a pasar exactamente lo de hoy**: el `intent` se
elige por euros, un fichaje se mide contra el bolsillo de especular y
la vía de ficha vacía no compite.

---

## La lista del primer ciclo

Con el interruptor apagado, **el primer ciclo hace lo mismo que hoy**.
Para que no haya dudas de qué es "lo mismo":

| | |
|---|---|
| **Ficha** | nadie por la vía nueva. Lo único vivo es la puja que ya está puesta: **1.229.925 € por Kiko Femenía** |
| **Vende** | nada. `MONITOR_OFFERS`, no ejecutable |
| **Si hiciera falta caja** | **Lucas Cepeda, 471.200 €**, oferta viva del Computer |

Esa última fila es la pieza nueva, y merece el número entero:

```
déficit actual          421.792
Lucas Cepeda            471.200   (oferta viva, se cobra en un ciclo)
saldo después           +49.408
daño al once            ninguno: no juega
```

**El motor de solvencia calcula exactamente el mismo `post_balance`:
+49.408.** Dos caminos independientes —su plan A y mi cola— eligen al
mismo jugador y llegan al mismo euro. Es la mejor señal de que la cola
no se ha inventado nada.

---

# 1. La puerta: ¿sabe vender?

Todo medido sobre `diagnostico/status.json`, la foto de producción
generada el **05/09/2026 a las 14:03:26**.

## 1.1 En 34 horas de registro, cero ventas ejecutadas por Pepe

80 entradas de autopiloto, del 04/09 a las 04:02 al 05/09 a las 14:02.
Las que **escriben** son 20:

| Acción | Veces | HTTP | Verificada |
|---|---|---|---|
| `RENEW_MARKET_LISTING` | 12 | 204 | sí |
| `REROLL_COMPUTER_OFFER` | 4 | 200 | sí |
| `SAVE_LINEUP` | 2 | 200 | sí |
| `BUY_SPECULATION` | 1 | 200 | sí |
| `LIST_FOR_LIQUIDITY` | 1 | 204 | sí |
| **`ACCEPT_RECOVERY_OFFER`** | **0** | — | — |

**Pepe escribe. Lo que no hace nunca es cobrar.**

## 1.2 La única venta consumada no la hizo el bot

En el feed de la liga Pepe aparece dos veces:

```
04/09 21:57:05   USER_TRANSFER      Yusi Enríquez   1.226.068   Pepe -> Prinzipote
05/09 07:06:32   BUY_FROM_COMPUTER  Expósito        5.147.000   Computer -> Pepe
```

La venta es real y el dinero entró. **Pero a las 21:57 el bot estaba en
`WAIT`, con `ROUND_TRANSITION_LOCK`, y no escribió nada.** Se cerró
sola: la subasta del mercado venció y Prinzipote se lo llevó.

Es una vía de venta que funciona —el bot publica y renueva
publicaciones, con 204 verificado, y hay 13 vivas— **pero no es la vía
que hace falta para sostener deuda**. Publicar y esperar a que alguien
compre no es un ciclo.

## 1.3 `accept_offer` no ha fallado: no se lo ha pedido nadie

El arreglo del 19/08 está puesto y guardado:

- `write_client.py:711-716` manda `json=request["json"]`. El bug era
  exactamente ese cuerpo que faltaba, documentado en las líneas
  624-642.
- `test_escrituras_con_cuerpo_v1` comprueba que `accept_offer`
  construye el cuerpo **y lo envía**.
- El gatillo está reconectado: el orquestador emite
  `ACCEPT_RECOVERY_OFFER` con `executable: True` en cuanto
  `offers_to_collect` devuelve algo, y el executor llama a
  `writer.accept_offer(execute=True)`.
- `backoff.blocked` está **vacío**: la acción no está apartada por
  fallos.

Y hay un argumento fuerte a favor de que el tubo está bien:
**`reject_offer` usa el MISMO `PUT /api/v2/offers/{id}` con el mismo
`{"status": ...}` y ha devuelto 200 cuatro veces hoy, verificado.** Lo
único que cambia entre aceptar y rechazar es la palabra de dentro.

**Pero no es una demostración.** Que el tubo esté bien no es lo mismo
que haber pasado agua por él, y aquí lo que se compra con la
demostración es autorización para endeudarse.

## 1.4 Lo que cierra la puerta: está en déficit y no vende

Esto es lo que decide, y no es una duda técnica:

```
saldo                     -421.792 EUR
pepe_now                  "Prioridad: recuperar solvencia"
comprometido en pujas      1.229.925 EUR  (Kiko Femenía, viva)
ofertas sobre la mesa      12, por 45.746.500 EUR   (7 con prima positiva)
planes de solvencia        3, calculados, ninguno ejecutado
próxima acción             BUY_SPECULATION   <- ejecutable
```

Y el motor de ofertas contesta, textualmente:

> *"Offer Decision Engine V2 controla 12 ofertas: 1 protegidas, 1
> reservas de solvencia, 6 buenas para conservar, 4 en espera y **0 con
> signal accionable. Ninguna para cobrar ahora.**"*

**Los tres planes de solvencia se apoyan en `COMPUTER_OFFER`** —la vía
que nunca se ha ejercido— y el plan A es vender a Lucas Cepeda por
471.200, que no juega y no toca el once. **El motor de ofertas contesta
`HOLD_OFFER` a esa misma oferta.**

Dos motores, respuestas contrarias sobre el mismo jugador, y nadie
arbitra. Mientras tanto el déficit sigue ahí y la siguiente acción es
comprar.

## Veredicto

**No se puede demostrar que Pepe deshace posiciones.** Puede publicar,
puede renovar, puede rechazar y puede comprar. Cobrar no lo ha hecho
nunca, y la única vez que la caja lo necesitaba —ahora mismo— contestó
que no había nada que cobrar.

Encender fichajes con deuda encima de eso es exactamente el escenario
que la puerta existía para evitar. **Interruptor apagado.**

---

# 2. La política de venta — hecha

Es lo que sí se podía construir esta noche, y además es la pieza que
desatasca lo de arriba: hasta hoy nadie escribía el orden.

## La cola, sobre la foto de producción

| # | Jugador | Escalón | €/punto | Momento | Entra en caja |
|---|---|---|---|---|---|
| 1 | **Lucas Cepeda** | No juega | 60.000 | quieto | **471.200 ya** |
| 2 | Jutglà | Caro por punto | 309.091 | ▼ 60.000/día | 3.381.600 ya |
| 3 | Manu Sánchez | Caro por punto | 248.333 | ▼ 10.000/día | a mercado |
| 4 | Mangala | Caro por punto | 241.818 | ▼ 30.000/día | 2.708.300 ya |
| 5 | Pablo Ibáñez | Caro por punto | 207.000 | quieto | 2.150.700 ya |

```
caja en ESTE ciclo        471.200    (Lucas Cepeda: una acción por ciclo)
sobre la mesa             8.711.800  (4 ofertas vivas, 4 ciclos)
a precio de mercado      10.100.000  (hay que publicar y esperar)
```

**Los tres números son distintos a propósito.** Sumar las ofertas y
llamarlo "caja en un ciclo" sería prometer en media hora lo que tarda
cuatro ciclos — y esa promesa es justo la que sostendría una deuda.

## Los que no se proponen, con su motivo

| Jugador | | Motivo |
|---|---|---|
| Yamal | 21.170.000 | Dios: intocable por decisión del dueño |
| Expósito | 5.150.000 | Clave: intocable |
| Olasagasti | 2.870.000 | Clave: intocable |
| Djené | 2.040.000 | Clave: intocable |
| Dituro | 2.680.000 | portero titular: no se rota y no se improvisa |
| Gustavo Puerta | 3.400.000 | sin escalón conocido: vender a ciegas no se deshace |

Y apartados por el suelo de su posición: **Jonny Castro** y **Zubeldia**
(quedarían 2 defensas y hacen falta 3) y **Pablo Durán** (quedaría 1
delantero y hacen falta 2).

Todo eso se ve en pantalla, en PLANTILLA, con el motivo escrito entero.

## Por qué el orden es ése

Los tres criterios del encargo son **escalones, no sumandos**:

1. **Primero quien no juega.** Un titular carísimo por punto no sale
   antes que un suplente, aunque su número sea mucho peor. Metidos en
   una puntuación única harían lo contrario de lo que dice la frase —hay
   guardia con el caso: un titular a 2.000.000 € el punto contra un
   suplente a 50.000, y sale el suplente.
2. **Después, coste por punto.** Con `points` de la temporada. Sin
   puntos no se inventa un coste: se dice "sin puntos" y se ordena
   aparte, porque cero no es infinito ni es cero.
3. **El momento ordena DENTRO del escalón.** Con r=+0,90 medido el
   07/09, el que cae hoy cae mañana. Jutglà cae 60.000 €/día: si hay
   que vender, antes que después.

## Y aguanta prefijos

Es una **cola**, no una lista de sugerencias: vender a los `k`
primeros, **para cualquier k**, deja todas las posiciones por encima de
su suelo. Si meter al siguiente rompiera un suelo, se aparta con el
motivo en vez de colarse más abajo — bajarlo de puesto sería mentir
sobre el orden.

Guardia: `test_orden_de_venta_v1`, 16 pruebas. Comprueba los prefijos
uno a uno, que ningún intocable entre, que cada fila lleve motivo, y
—con `ast`— que el módulo no importe ningún executor ni reimplemente
los intocables o el suelo.

---

# 3. Lo que me sorprendió

## 1. Ya fichaste a Expósito, y eso es lo que abrió el déficit

```
05/09 07:06:32   BUY_FROM_COMPUTER   Expósito   5.147.000
```

No está en el libro de pujas —que solo registra lo que puja el bot—
así que la puja fue tuya. El informe de anoche decía *"Expósito es el
primero de la lista el día que se decida abrir la deuda"*, y se abrió.

La cuenta cuadra: 3.399.140 de caja del 04/09, más 1.226.068 de la
venta de Yusi, menos los 5.147.000 de Expósito deja el saldo en
negativo. **Los −421.792 de hoy son ese fichaje.**

Lo cuento porque cambia la lectura de la puerta: no es una precaución
teórica. Pepe **ya** está en la posición que el encargo quería crear
—endeudado por un fichaje— y desde hace siete horas no ha hecho nada
para deshacerla.

## 2. Compró otra vez estando en déficit

A las 11:32, cuatro horas después de entrar en negativo, `BUY_SPECULATION`
por Kiko Femenía. HTTP 200, verificada, 1.229.925 € comprometidos.

`pepe_now` dice *"prioridad: recuperar solvencia"* y `next_action` dice
*"comprar para especular"*. No es una contradicción en el código —son
dos motores con prioridades distintas y cada uno hace bien su trabajo—
pero es exactamente el comportamiento contra el que existe la puerta.

## 3. Tenías razón con lo del tablero, y me equivoqué de disco

Anoche escribí que la pantalla decía *"el tablero está vacío"* cuando
la verdad era *"es de la jornada 2 y estamos en la 5"*. **Medí contra
`data/` del repo, que es de agosto.** En producción:

```
starter_board_matchday   5
starter_board_players    116
starter_cache_status     REFRESHED
starter_board_rejected   false
```

El tablero está perfectamente. **El defecto de código sigue siendo
real** —`lineup_engine.py:170-177` colapsa "rechazado por jornada" en
"está vacío"— pero **el síntoma que reporté no existe en producción**, y
la conclusión que saqué de él era falsa. A partir de esta noche las
guardias nuevas leen `diagnostico/status.json` y lo dicen en el
docstring.

## 4. El portero se salvaba por accidente

`untouchable_reason` protege al "portero titular" mirando `in_lineup`.
El roster del dashboard trae ese dato como `is_starter`. Con la
plantilla tal cual, **Dituro no salía como intocable**: lo único que lo
sacaba de la cola era el suelo posicional, que bloquea porque hay
exactamente un portero.

Es palabra por palabra el accidente contra el que avisa el docstring de
`sale_intent`:

> *"hoy Yamal solo está a salvo por accidente: el guardarraíl posicional
> bloquea la venta porque hay exactamente dos delanteros. El día que
> entre un tercero, esa protección desaparece sola y nadie se entera."*

No toqué la regla: le doy el dato con el nombre que espera. Hay guardia
que exige que Dituro esté apartado **por ser portero**, no por el suelo.

## 5. El libro de pujas no ve lo que haces tú

`bid_outcomes`: 1 puesta, 1 pendiente. Esa es la de Kiko Femenía, del
bot. **Los 5.147.000 de Expósito no aparecen.** El libro registra lo que
puja Pepe, no lo que pujas tú.

El encargo pedía comprobar que el libro los registra "para saber en una
semana si esto funciona". Los del bot sí. Los tuyos no, y hoy los tuyos
son los que mueven el saldo. Es un agujero en la medición, no en la
ejecución, y no lo he tapado porque tocarlo sin encargo sería inventar.

---

# 4. Lo que hace falta antes de encender

No es una lista larga. **Con una sola de estas tres, la puerta se pasa:**

1. **Una venta cobrada.** Que `ACCEPT_RECOVERY_OFFER` devuelva un 200
   una vez, con cualquier oferta. Basta una.
2. **Que alguien arbitre entre los dos motores.** Hoy el de solvencia
   dice "vende a Lucas Cepeda" y el de ofertas dice "hold" sobre la
   misma oferta. Mientras eso no se resuelva, el plan de solvencia es
   un documento, no un plan.
3. **O bajar el listón de cobro cuando hay déficit.** Las doce ofertas
   se juzgan por prima; ninguna llega. Con el saldo en rojo, la pregunta
   no es si la prima es buena: es si tapa el agujero sin romper el once
   — y esa pregunta ya tiene respuesta calculada, tres veces.

La número 2 es la que yo haría primero, y es pequeña: la cola de venta
de esta noche ya dice a quién y en qué orden, y coincide al euro con el
plan A del motor de solvencia.

---

## Cómo quedó

```
rama          sin-miedo/2026-09-11   (sin subir: el push lo das tú)
main          intacto
puerta        73/73 en verde  (72 al empezar, 1 guardia nueva)
commits       2
frontend      npm run build OK · NO desplegado · dist/ intacto

PUNTO 1       NO PASADO. Cero ventas ejecutadas por Pepe en 34 h de
              registro. `accept_offer` sin usar desde el arreglo del
              19/08. Déficit de -421.792 sin atender.

PUNTO 2       HECHO. Cola de venta con motivo, en pantalla, con
              guardia de 16 pruebas. Observador puro.

PUNTO 3       NO EJECUTADO, por la regla del propio encargo.
              DEPLOYMENT_ENABLED = False
              deuda                sin tocar
              MAX_SAFE_DEBT        sin tocar
              colchón y haircuts   sin tocar
```

**La frase para mañana:** el tubo de vender está casi seguro bien —su
gemelo `reject_offer` devuelve 200 cuatro veces al día por el mismo
endpoint—, pero Pepe lleva siete horas en números rojos con doce
ofertas encima de la mesa contestando que no hay nada que cobrar, y su
siguiente movimiento previsto es comprar. No es el tubo lo que falta:
es que alguien decida quién sale. Eso es lo que se ha construido esta
noche, y por eso el primer nombre de la cola es Lucas Cepeda, 471.200 €,
que deja el saldo en +49.408 sin tocar el once.
