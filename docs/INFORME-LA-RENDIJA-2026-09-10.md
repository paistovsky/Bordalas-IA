# La rendija — informe

**Fecha:** 10/09/2026 · **Verja:** 104/104 · **Push:** NO
**Escrituras contra Biwenger:** ninguna. **Umbrales movidos:** ninguno.
**La compuerta de ritmo:** sin tocar.

---

## LA RENDIJA NO SE ABRE

Tú pusiste la condición: *«Si el cierre no puede ser automático, DILO Y NO ABRAS
LA RENDIJA»*.

**No puede serlo hoy, y falla por las dos patas.**

### 1. Nada lista a un jugador recién comprado

El único camino que lista es el del gestor de posiciones, y solo dispara con
`TAKE_PROFIT`, `CUT_LOSS` o `ROTATE_CAPITAL` — condiciones de beneficio o
pérdida sobre un jugador que **ya llevas**. Ninguna dice «acabo de comprar esto
para darle la vuelta, ponlo en el mercado».

Un jugador comprado por la rendija se quedaría **fuera del mercado**. Y si no
está listado, el Computer no le hace oferta: el viaje no puede ni empezar a
cerrarse.

### 2. Y si llegara la oferta, no se cobraría

Con las 14 ofertas vivas de hoy delante:

```
KEEP_GOOD_OFFER   8      "Oferta Computer buena, pero el jugador
HOLD_OFFER        3       no está para vender: se conserva la
REROLL_CANDIDATE  1       opcionalidad."
NEVER_SELL        1
ACCEPT_NOW        1   <-- una de catorce
```

El motor vende cuando el jugador **está para vender** (`sale_score`). Un jugador
comprado solo para darle la vuelta no tiene nada malo: su `sale_score` es bajo, y
el motor lo **conserva**.

**Resultado: comprarías cuatro al día y no venderías ninguno.** Que es
exactamente lo que temías — *«así se acaba con 21 fichas y sin caja»*.

### Qué haría falta para abrirla

Dos piezas, ninguna existe:

1. **Auto-listado del recién comprado.** Al ganar una puja marcada RENDIJA,
   listar al jugador en la misma vuelta, al precio que diga la regla de siempre
   (`max(precio_actual, valor × 1,15)`).
2. **Cierre del viaje.** Que el motor de ofertas cobre la del Computer **para los
   marcados RENDIJA**, salvo que el jugador haya entrado en el once. No es mover
   un umbral: es una excepción explícita para una cohorte marcada, con su propia
   guardia.

Las dos son código nuevo que **vende**. No las he escrito porque abrir esto sin
tu visto bueno sobre el mecanismo de venta sería justo lo contrario de lo que
pediste.

**Se abre cuando esas dos estén y las mires.** Todo lo demás del encargo —el tope
de cuatro, el apagado solo a los 10 viajes, la marca RENDIJA en el libro— es
fácil encima de eso; lo difícil y lo peligroso es la venta.

---

## El libro en la sombra: EN MARCHA

`src/intelligence/libro_en_la_sombra.py`. **Sin dinero: ninguna ruta lo lee.**

No re-valora nada: la propia compuerta ya publica `intent_before` y
`value_before` —lo que el jugador valía **antes** del corte—, así que la sombra
lee lo que el tablero publica y lo apunta.

Excluye a propósito lo que **no** rechaza la compuerta: los de mercado de rival
(cerrados por orden tuya) y los que ya tienen puja viva. Si se colaran, la sombra
mediría el efecto de otras reglas y se lo achacaría a ésta.

**Hoy apunta 16 casos**, todos `PRECIO_CAYENDO`:

```
Urko            precio 2.140.000   valía 2.170.976   +1,4 %
Cancelo         precio 6.260.000   valía 6.350.613   +1,4 %
Lunin           precio   420.000   valía   426.079   +1,4 %
...
16 casos en 1 día. Faltan 264 para los 280 con los que se decide.
```

Un detalle que ya se ve: **el margen es +1,4 % en todos**. La valoración
pre-compuerta les da a todos el mismo margen, así que lo que la compuerta
rechaza hoy no es un puñado de gangas — es el mercado entero al mismo precio.
Con dos semanas se verá si alguno de ellos subió.

---

## La pata de vuelta: cuánto paga el Computer al recomprar

Sobre **34 ventas** al Computer en días con foto:

```
min -2,73   p25 +1,63   MEDIANA +2,91   p75 +4,20   max +10,50
negativas: 2 de 34 (6 %)
```

**Es una distribución ancha, no un número.** Entre el p25 y el p75 hay 2,6 puntos
— más que el margen entero de un viaje de Pollo. Elegir bien *cuándo* cobrar vale
tanto como elegir bien qué comprar.

### Depende de la posición

```
defensa     n=12   +3,67 %
portero     n= 2   +3,26 %
medio       n= 8   +2,85 %
delantero   n=12   +1,80 %
```

**Un defensa se recompra dos puntos más caro que un delantero.** Si eso aguanta
con más muestra, la rendija —cuando se abra— debería preferir defensas, y es lo
contrario de donde mira hoy el escaparate.

### Y del precio del jugador

```
<1 M     n=16   +1,52 %
1-3 M    n= 8   +3,46 %
3-6 M    n= 9   +3,20 %
6 M+     n= 1   +3,83 %
```

**Los baratos se recompran peor.** Por debajo de 1 M la prima cae a la mitad, y
son justo los que más aparecen en el escaparate. Un viaje de 150.000 al +1,5 %
deja 2.250 EUR: no paga ni la ficha que ocupa.

### De cuánto lleva listado: NO SE PUEDE MEDIR

Y el motivo es algo que aprendimos hoy mismo: **renovar reescribe la fecha del
listado**. Al renovar, `date` pasa a ser el momento de la renovación, mientras la
oferta —creada antes— sobrevive. Por eso hay ofertas con fecha *anterior* a la de
su propio listado (mediana −0,2 días, mínimo −1,6).

La evidencia de cuándo se listó por primera vez **se destruye en cada
renovación**. Para contestarlo habría que apuntar la fecha de la primera
publicación en un libro propio, desde hoy hacia adelante.

---

## Lo que entra

```
 nuevo   src/intelligence/libro_en_la_sombra.py
 modif   src/telemetry/dashboard_state.py     publica `sombra`
 modif   scripts/los_viajes_de_los_rivales.py la pata de vuelta, medida
 nuevo   docs/INFORME-LA-RENDIJA-2026-09-10.md
```

## Lo que NO hice, y por qué

- **No he abierto la rendija.** El cierre no es automático; me dijiste que en ese
  caso lo dijera y no la abriera.
- **No he escrito el auto-listado ni el cierre automático.** Son código que
  vende, y quiero que decidas tú el mecanismo antes de que exista.
- **No he tocado la compuerta de ritmo**, ni ningún umbral.
- **No he hecho push.**
