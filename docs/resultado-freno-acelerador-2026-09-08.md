# Freno y acelerador — resultado de la noche del 07→08/09/2026

Rama `freno-acelerador/2026-09-08`, subida. `main` sin tocar.
**Puerta: 70 de 70 en verde.** Eran 68 al empezar. Cuatro commits.
`npm run build` pasa. **Nada desplegado.**

---

# 1. La lista de la primera vez

Los 22 candidatos de la foto de producción del 04/09, con sus precios
reales, pasados por las reglas nuevas.

## Lo que Pepe DEJA de comprar — 6 candidatos, 6.112.162 €

| Jugador | Precio | Valía | Vale | Ritmo | Por qué |
|---|---|---|---|---|---|
| **Odysseas** | 3.750.000 | 3.788.531 | **0** | −0,81 %/día | viene bajando |
| **Calero** | 1.030.000 | 1.040.583 | **0** | −0,98 %/día | viene bajando |
| **André Almeida** | 820.000 | 828.425 | **0** | 0,00 %/día | precio quieto |
| **Álex Padilla** | 150.000 | 151.541 | **0** | 0,00 %/día | precio quieto |
| **Iñaki Rupérez** | 150.000 | 151.541 | **0** | 0,00 %/día | precio quieto |
| **Diego Murillo** | 150.000 | 151.541 | **0** | 0,00 %/día | precio quieto |

Odysseas es el caso claro: 3,75 M por un jugador cuyo precio cae un
0,81 % diario. Con un 0,5 % de aciertos comprando caídas, esa
operación era una moneda al aire de casi cuatro millones.

## Lo que sigue comprando — 14 candidatos

Ninguno cambia de valor. Los cuatro con ritmo medido —Mariano
(+1,41 %), Bardeli (+4,62 %), Yusi Enríquez (+1,72 %), Expósito
(+0,39 %)— pasan el freno; los otros diez no tienen ritmo observado y
conservan su valor por la vía de reventa al Computer, que no necesita
ritmo.

## Lo que NO pasa, y es lo más importante de esta noche

**El acelerador no sube ni una sola valoración.** Cero.

No es que no funcione: calcula bien. Con Bardeli, a su ritmo real de
+4,62 %/día, la vía de tendencia proyecta **+138.628 €** sobre un
precio de 1.650.000. Y aun así devuelve **cero**.

Por qué está en el apartado 3. Es el hallazgo de la noche y no se ha
arreglado a propósito.

---

# 2. Lo que se hizo

## El fallo, reproducido exactamente

El encargo decía que la entrada era una constante. Lo es — pero la
causa era otra de la que suponíamos, y encontrarla cambió el diseño.

Se reprodujo el número al euro:

```
computer_resale_value(1.650.000, 0,0176) = 1.671.780
```

Que es exactamente lo que valía Bardeli en la foto. **La vía que
ganaba en 21 de los 22 candidatos era la de REVENTA AL COMPUTER**,
cuyo premium es una medida de mercado —la misma para todos por
construcción— y no del jugador.

No era una velocidad rota. Era **una vía que no mira al jugador
ganándole por euros a la que sí lo mira**.

## Las tres reglas de compra

**ACELERADOR** — La tasa que se proyecta es el ritmo observado del
jugador, el que recoge el ojeador. Sin ritmo no se inventa una tasa:
la vía de tendencia no valora y se dice por qué.

**FRENO** — Un precio que viene bajando no se compra como
especulación. Sin banda de tolerancia: de los que bajaron ayer el
90,7 % siguió bajando y solo el 0,5 % batió al mercado. No hay nada
que tolerar.

**AVISO** — Racha de 3 días o más con la demanda por debajo de −20
puntos: no se compra. Los cortes no son a ojo: tras 1 día de racha la
continuidad es del 92 %, tras 2 del 94 %, y a partir de 3 cae al 74 %.
Ahí es donde tiene sentido preguntarle a la demanda si queda gasolina.

## Una distinción que costó una guardia en rojo

Frené también la vía de reventa al Computer por falta de ritmo, y
`test_reventa_al_computer_v1` se puso en rojo. **Tenía razón ella.**

Esa vía no apuesta a que el jugador suba: apuesta a que el Computer
paga por encima del mercado en el reset. Exigirle un ritmo le importa
una dependencia que no tiene, y **habría apagado una vía de ingresos
entera para más de la mitad del tablero** solo porque el ojeador no
empareja a ese jugador.

Lo que sí la frena es que el precio venga cayendo: el Computer paga
sobre el precio del reset, y sobre una base que encoge el premium vale
menos.

La misma guardia saltó por otra cosa: mi compuerta tapaba un motivo
más concreto —"prima sin medir"— con el suyo. Ahora, si una vía ya se
cerraba sola, manda su motivo.

## El freno de mano

Una posición abierta como `SPECULATION` cuyo precio se gira suma 60
puntos de venta, que es justo el corte de VENDER.

**Solo a las posiciones especulativas.** Un jugador del once que baja
de precio no es una posición girada: es un futbolista comprado por
puntos. Sin esa distinción, la primera semana mala de precios
propondría vender media plantilla.

Y **aquí se puntúa, no se ejecuta**. Pepe no vende por iniciativa
propia salvo por liquidez, y esa decisión es del dueño y está escrita
en `sale_intent`: *"una venta mala te deja SIN el jugador, y en un
fantasy no se recupera"*. La regla actúa **priorizando**: el día que
haya que soltar a alguien, la posición girada va primero.

Sale sola una propiedad que me gustó: `analyze_sales` resta 15 por
estar en el once, así que una posición girada que además está jugando
se queda en 45 —CONSIDERAR VENTA, no VENDER—. No está programado como
caso especial. Si está dando puntos, no se malvende por una racha de
precio.

## El test de Soler

**Sigue verde, y hay un motivo concreto:** llama a `optimal_bid` con
precio y valor fijos, sin pasar por `value_candidate`. La compuerta
vive en la valoración, así que no puede tocarlo. Y no se ha movido
ningún umbral.

Pero como dice el encargo, su lección es de **concentración**, y eso
no lo cubría ninguna guardia. Ahora hay una que comprueba que el
ejecutor sigue rechazando una puja por encima del tope por operación
(`bid_amount > authorised`). Sobre una foto con presupuesto abierto,
los 5,95 M de Soler son **4,9 veces** el tope de 1.225.720 €.

## El libro de pujas

`record_bid` ya estaba en la ruta de puja. Ahora apunta además **el
ritmo con el que se compró**, la compuerta que lo autorizó y la racha.
Es lo único que permitirá contestar en una semana a *"¿comprar rachas
funcionó?"* en vez de discutirlo.

---

# 3. Lo que me sorprendió

## El acelerador está drogado por una confianza que no es la suya

Es el hallazgo de la noche y deja la pieza 1 inerte sobre el tablero
de hoy.

`speculation_value` multiplica el valor por `confidence`. Para
Bardeli esa confianza vale **0,4125**, y sale de dos penalizaciones:
no tiene histórico en LaLiga (`IMPLICITO_MERCADO`) y no tiene
pronóstico de titularidad.

Es decir: **una apuesta sobre el PRECIO se está descontando por lo
inseguros que estamos de sus PUNTOS.** Para una compra de momentum da
igual cuántos puntos vaya a hacer; lo que importa es si su precio
sigue subiendo, que es justo lo que sí está medido.

```
Bardeli, +4,62 %/día, precio 1.650.000

  revalorización proyectada          +138.628 €
  con confianza de puntos (0,4125)   → 0   MARGEN_INSUFICIENTE
  con confianza 1,0                  → 1.753.971  (×1,0630)
  vía del Computer, sin confianza    → 1.666.953  (×1,0102)
```

Y aquí está el remate: **`computer_resale_value` no aplica ninguna
confianza.** Esa asimetría es toda la historia. La vía que no mira al
jugador no lleva descuento; la que sí lo mira, sí. Por eso gana
siempre, y por eso todos valían lo mismo.

**No lo he arreglado.** Quitar esa penalización subiría valoraciones y
haría a Pepe más agresivo, y eso se decide con el dueño delante — no
de madrugada y no en el mismo commit que introduce tres reglas nuevas.
Queda medido, con números, y con una guardia
(`test_LA_ASIMETRIA_QUE_QUEDA_SIN_ARREGLAR`) que salta si alguien lo
cambia sin querer.

**Es lo primero que yo miraría mañana.**

## La guardia tenía razón y yo no

Dos veces en la misma noche `test_reventa_al_computer_v1` me paró, y
las dos veces el código estaba mal, no el test. Frenar la reventa al
Computer por falta de ritmo habría apagado una vía de ingresos entera
por una razón prestada.

Es exactamente lo que el encargo avisaba sobre el test de Soler —"no
lo ajustes sin entenderlo"— aplicado a otro test.

## Volví a caer en el mismo error de anoche

Escribí una guardia que buscaba la palabra "presupuesto" en el módulo
para comprobar que no lo tocaba... y saltó contra su propio
**docstring**, que dice justamente que no toca presupuestos. Igual que
el 07/09 con el docstring de la puerta. Ahora mira los `import` con
AST, no la prosa.

## El freno hace casi todo el trabajo

Esperaba que el acelerador fuera la pieza grande y el freno el
complemento. Es al revés: el freno retira 6,11 M de valoración
especulativa sobre seis candidatos, y el acelerador no mueve nada.

En un mercado donde el que baja sigue bajando el 90,7 % de las veces,
**la mayor parte del dinero se gana no comprando.**

---

# 4. Lo que se quedó fuera, y por qué

**La asimetría de la confianza.** Localizada, medida y con guardia.
Cambiarla sube valoraciones: decisión del dueño.

**El 45 % de los candidatos sin ritmo observado.** El ojeador empareja
la mitad del mercado con el catálogo local, que es de hace tres
semanas. En producción el snapshot es del momento y debería mejorar,
pero **no lo he podido comprobar** y no lo doy por hecho.

Mientras tanto esos candidatos conservan su valor por la vía del
Computer, que no necesita ritmo — así que el freno no los toca y
tampoco se quedan sin valorar.

**Que Pepe venda por iniciativa propia.** El freno de mano prioriza,
no inicia. Convertirlo en una venta automática contradice una decisión
del dueño escrita en el código.

---

## Cómo quedó

```
rama          freno-acelerador/2026-09-08, subida
main          sin tocar
puerta        70/70 en verde  (68 al empezar, 2 guardias nuevas)
commits       4
frontend      npm run build OK · NO desplegado · dist/ intacto

umbrales      MIN_SPECULATION_YIELD = 0,03          sin tocar
              MIN_SPECULATION_EXPECTED_VALUE = 25000 sin tocar
              presupuestos, topes y guardarrailes    sin tocar

efecto        6 candidatos dejan de valorarse como especulación
              (6.112.162 €). Ninguna valoración sube.
```

**La frase para mañana:** el freno ya está trabajando; el acelerador
está montado y enchufado pero lo anula una confianza que mide otra
cosa. Arreglar eso es una línea, y es tuya.
