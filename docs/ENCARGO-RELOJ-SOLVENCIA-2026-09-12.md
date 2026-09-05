# ENCARGO — la deuda tiene fecha de caducidad

Noche del 11/09/2026. Para Claude Code en `C:\Users\PC\Bordalas-IA-clean`.

Lee antes `docs/resultado-sin-miedo-2026-09-11.md`. La puerta del encargo
anterior no se pasó, y con razón.

**Mide siempre contra `diagnostico/status.json`** (foto de producción).
`data/` del repo es de agosto.

---

## LA REGLA NUEVA, DICHA POR EL DUEÑO

> *"No quiero salir de rojo hoy. Con estar en positivo 6 horas antes del
> inicio de jornada es suficiente."*

**Estar en deuda no es un fallo. Estarlo cuando empieza la jornada, sí.**

Eso cambia el modelo entero: la solvencia deja de ser un estado que hay
que mantener y pasa a ser **un plazo que hay que cumplir**. Lejos del
cierre, el déficit es una posición legítima. Cerca, es una emergencia.

---

## EL PROBLEMA QUE HAY QUE RESOLVER

Medido anoche sobre producción:

```
saldo                  -421.792 €
pepe_now               "recuperar solvencia"
ofertas sobre la mesa   12, por 45,7 M
planes de solvencia     3 calculados, 0 ejecutados
proxima accion          BUY_SPECULATION
```

El plan A dice **vender a Lucas Cepeda**. El motor de ofertas, sobre esa
misma oferta, contesta **`HOLD_OFFER`**. Nadie desempata, no pasa nada, y
el ciclo se va a comprar.

Y en 34 horas de registro: **cero ventas ejecutadas**. La única venta
consumada venció sola mientras el bot estaba bloqueado en la transición
de jornada.

El tubo no está roto: `reject_offer` usa el mismo `PUT /offers/{id}` y
devuelve 200 cuatro veces al día. **Nunca se ha usado para aceptar.**

---

## 1. El reloj de la solvencia

Un módulo que calcule, a partir del primer partido de la jornada
(`first_kickoff`, `market_clock`):

- Horas hasta el cierre.
- **Fecha límite de solvencia: T−6h.** En ese momento el saldo tiene que
  ser ≥ 0.
- Si hoy hay déficit: ¿lo cubren las ofertas que ya están sobre la mesa?

Y de ahí, un nivel de urgencia. Las dos velocidades importan:

- **Aceptar una oferta existente es instantáneo.** Si las ofertas
  actuales cubren el déficit, se puede esperar.
- **Crear liquidez es lento**: publicar y esperar puja son días. Si las
  ofertas no cubren, **hay que empezar a publicar mucho antes**, no a
  seis horas.

Calcula tú el margen y **justifícalo con los datos**: cuánto tarda de
media una publicación en recibir oferta, según el histórico del tablón.
No inventes un número redondo.

Publícalo en el dashboard: cuántas horas quedan, si el déficit está
cubierto por ofertas vivas, y qué va a hacer.

---

## 2. Quién gana el empate

Cuando el motor de solvencia dice "vende a X" y el de ofertas dice
"conserva a X", hoy no gana nadie.

**Cerca del plazo, manda la solvencia.** Estar en números rojos cuando
empieza la jornada no es una opinión discutible.

Lejos del plazo, el motor de ofertas puede seguir diciendo que conserve
— tiene sentido no malvender con tiempo por delante.

Y que **el motivo del desempate se vea en pantalla**: *"se vende a
Cepeda pese al HOLD porque quedan 5 h y el saldo es −421.792"*.

---

## 3. Que la venta se ejecute — LA CLAVE

Todo lo demás sobra si esto no pasa.

El Offer Decision Engine está declarado observador
(`decision_executable: false`). El camino que sí escribe es
`ACCEPT_RECOVERY_OFFER`, y no se ha disparado ni una vez.

Averigua **por qué no se dispara** y arréglalo. Puede ser prioridad en
la cola, puede ser una guarda, puede ser que el plan no llegue al
ejecutor. Anoche lo dejaste apuntado: hay tres cosas —basta una— que
pasarían la puerta.

Usa `sale_order.py`, la cola que montaste anoche, como fuente de a quién
vender.

*Hecho cuando:* puedes demostrar con una ejecución real —o con una
prueba que recorra el camino entero hasta el cliente de escritura— que
una oferta se acepta.

---

## 4. El portero que se salvaba de milagro

`untouchable_reason` mira `in_lineup`; el roster trae `is_starter`. Lo
único que impedía vender al único portero era el suelo posicional.

Arréglalo. Con la venta a punto de funcionar de verdad, ese accidente
deja de ser teórico.

---

## LO QUE SIGUE APAGADO

`DEPLOYMENT_ENABLED` y la deuda para fichar **siguen apagados**. Se
encienden cuando se vea una venta ejecutada de verdad, no antes.

Con la regla nueva eso ya no es una espera indefinida: la próxima
jornada obliga a que ocurra. Si Pepe llega a T−6h en rojo, es que esto
no funciona.

No subas ningún tope, ningún porcentaje, ni `MAX_SAFE_DEBT`.

---

## Cómo dejarlo

Rama `reloj-solvencia/2026-09-12`, puerta en verde, `main` intacto.
`docs/resultado-reloj-solvencia-2026-09-12.md` empezando por:
**¿va a llegar Pepe en positivo al próximo T−6h, y con qué venta?**
Con nombre y cifra.

Y lo que te sorprendió. Si una guardia se pone en rojo, léela antes de
tocarla — van cinco veces y las cinco tenían razón.
