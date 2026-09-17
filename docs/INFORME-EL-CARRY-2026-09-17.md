# El carry — informe

**Foto:** `diagnostico/status.json`, **`meta.generated_at` = 2026-09-17T07:30:55**, con
`encoding="utf-8"`.

**Rama:** `motor/el-carry` (desde `motor/el-proposito`)
**Verja:** 151/151 en verde, exit 0, salida a fichero
**Push:** NO. **Solo se enciende el arreglo del bloque 0.** `el_carry.ENCENDIDO = False`.

---

## La respuesta corta: **el carry está bien y está mal colocado**

> El concepto es correcto y lo mediste bien: el coste de tener a alguien no es el
> importe. **Pero puesto dentro de `xi_upgrade_value` hace que la vía del once apruebe
> operaciones por razones de mercado** — que es exactamente el fallo que
> `classify_operation` se inventó para evitar.
>
> Y el dato que lo delata: con el carry, **Budimir pasa a costar −758.571 €**. Un coste
> que sale negativo no es un coste.

---

## BLOQUE 0 — La verja ensuciaba **cinco** libros, no uno

Medido corriendo la verja entera con los libros en HEAD antes y después:

```
[ARREGLADO]  data/trading/libro_del_escaparate.jsonl
[PENDIENTE]  data/solvency/bitacora_del_saldo.jsonl        +1 línea por vuelta
[PENDIENTE]  data/intelligence/marcador.json               se reescribe entero
[PENDIENTE]  data/intelligence/libro_de_publicacion.jsonl  +1 línea, last_seen de hoy
[PENDIENTE]  data/rival_intelligence/board_events.json     +1.119 líneas
```

**Y la bitácora es la peor de las cinco:**

```
63 líneas · 11 fechadas el 17/09
de esas 11, las 11 llevan el saldo del 13/09 (−1.299.834 / 55.020.000)
la foto de hoy dice                          −373.984 / 56.470.000
```

**Ni una sola de las once observaciones de hoy es de hoy.** La verja escribe estado del
13/09 con la fecha de ahora. `marcador.json` además **encogió** —de 1.538 a 1.524
líneas— en una vuelta.

### El arreglo

`apuntar_el_escaparate` exige ahora `foto_at` y **solo escribe si el día de mercado de
la foto es el de ahora**. Y **sin sello tampoco escribe**: «si no me llega el dato me
porto como antes» es precisamente como se cuela una foto vieja.

Cada línea nueva lleva `foto_at` dentro, así que si algún día vuelve a colarse una
vieja se verá sin deducirlo de los nombres.

**Comprobado corriendo la verja otra vez: el libro del escaparate ya no aparece entre
los tocados.** Los otros cuatro sí.

### ¿Cuántas líneas de test había? **Una, y ya no existe**

Historia entera, para que no falte nada:

- El libro nació ayer y **nunca llegó a commitearse**.
- Una vuelta de verja le escribió **una línea**, con `dia_de_mercado: 2026-09-17` y los
  veinte del **13/09** dentro. **Cero de esos veinte coincidían con los veinte de hoy.**
- **La borré ayer**, al investigar de dónde salía, y lo dije en el informe de ayer.

**No he borrado ninguna línea de ningún libro en este encargo.** Los cuatro que la
verja ensució hoy los he devuelto a HEAD con `git checkout`, no borrados.

---

## BLOQUE 1 — Las tres piezas, y la contradicción resuelta

### La contradicción

```
sale_order (17/09)   +140.000 €/día = +0,2479 %/día
  -> es la SUMA de los incrementos de NUESTRAS 20 fichas en UN día

el 15/09             mediana −376, suben 35 de 81
  -> es la MEDIANA sobre 81 jugadores
```

**Sobre las 612 fichas del catálogo con 5+ pares de días seguidos**
(`price_history.json`, sello 16/09 18:23, ventana 16/08–16/09, n=16.434 pares):

```
mediana de las medianas   +0,0000 %/día
media de las medias       +0,1285 %/día
suben 130 · bajan 248 · planos 234
```

**Las dos son ciertas**: la media sube porque una minoría sube mucho; la mediana no se
mueve porque el jugador típico no se mueve.

> **Y ninguna de las dos sirve para el carry.** Para comprar a UNO hace falta la
> condicionada, porque el dato que tienes cuando vas a comprar es qué hizo su precio
> ayer.

### La deriva condicionada — y es enorme

```
H días          SUBIA              PLANO             BAJABA
1        +1,235 % (n=4120)   0,000 % (n=4865)   −1,389 % (n=6268)
3        +3,356 % (n=3806)   0,000 % (n=4489)   −4,032 % (n=5739)
6        +5,621 % (n=3373)   0,000 % (n=3844)   −7,628 % (n=5014)
10       +7,430 % (n=3057)   0,000 % (n=3400)  −11,711 % (n=4500)   <- el techo
14       +6,963 % (n=2438)   0,000 % (n=2653)  −14,609 % (n=3512)
21       +6,061 % (n=1319)   0,000 % (n=1410)  −17,035 % (n=1970)
```

**Diecinueve puntos de diferencia a diez días entre comprar a uno que sube y a uno que
baja.** El carry no es un número: son tres, y el que aplica lo decide el momento en que
entras, no el jugador.

También miré el tramo de precio: se mueve mucho menos (de −0,84 % a +0,10 % de mediana
diaria) y no es monótono. **La víspera manda; el precio casi no.**

### Las tres piezas, un jugador de 4.000.000 a diez días

```
                        SUBIA          PLANO         BAJABA        n        plazo
prima de compra       +0,251 %       +0,251 %       +0,251 %      11     al entrar
deriva del precio     −7,430 %        0,000 %      +11,711 %   3.057     10 días
coste de oportunidad  +0,853 %       +0,853 %       +0,853 %       7     10 días
─────────────────────────────────────────────────────────────────────────────────
CARRY                 −6,327 %       +1,103 %      +12,814 %
                      DEVUELVE        cuesta         cuesta
```

**Fuentes:** prima → `bid_outcome_ledger.json`, 11 compras ganadas en 09/2026, mediana
+0,2507 % (las 8 de agosto salen a −20,74 % y **no se usan**: son posiciones adoptadas
por el bootstrap, donde `market_price` no significa lo mismo). Deriva →
`price_history.json`. Oportunidad → +4,20 % por viaje (n=7, medido 16/09) × 20,3 % de
participación en subastas (n=182, medido 17/09).

> Ese 20,3 % importa: cobrar el coste de oportunidad entero sería cobrar algo que no
> existe. **No se pierde lo que no se iba a hacer.**

### El horizonte: diez días, y sale de la medición

La deriva del que sube **satura en el día 10 y después devuelve** (+6,963 % a 14,
+6,061 % a 21). A partir de ahí, tener al que sube deja de pagar.

Y coincide con los **10,2 días** medianos que duraron nuestras posiciones cerradas
(medido el 16/09, n=7). **Es una coincidencia y la digo como coincidencia**: son dos
mediciones distintas que caen en el mismo sitio, no una derivada de la otra.

### ¿Es el carry positivo?

> **El carry es NEGATIVO —tener al jugador PAGA— si y sólo si se compra a uno cuyo
> precio venía subiendo.** Con el que baja cuesta un 12,8 % a diez días.

No lo suavizo en ninguna dirección: es −6,33 % comprando bien y +12,81 % comprando mal.
Pero **no es dinero todavía**, y eso está en el bloque 3.

---

## BLOQUE 2 — La fórmula

```
coste de fichar = prima + deriva + oportunidad, a 10 días,
                  Y CON TOPE DE PRIMA DE +0,25 %
```

**El tope va en la misma función que el coste**, no en un sitio aparte, porque esta
semana un freno se ha quedado huérfano cuatro veces. `coste_de_fichar()` devuelve el
coste **y** el techo en euros, y si alguien pide la fórmula sin tope sale marcado
`sin_tope` y el motivo lo dice con esas palabras.

**Y el tope no es un número nuevo**: es `PRIMA_MAXIMA_DE_PUJA`, el mismo +0,25 % que ya
aplica a la otra vía. Se extiende el que hay en vez de inventar uno. Si alguien lo mueve
allí, se mueve aquí.

---

## BLOQUE 3 — Qué cambia, y el aviso

### Los 66 candidatos

```
jugador             precio       valor XI   dir      coste viejo    coste carry  pasa
Budimir         11.990.000      3.427.226  SUBIA     11.990.000       −758.571   SÍ
Jonathan David   7.870.000      3.213.066  SUBIA      7.870.000       −497.911   SÍ
Pépé            11.480.000      3.195.607  BAJABA    11.480.000      1.471.082   SÍ
Chupe            3.960.000      2.895.184  BAJABA     3.960.000        507.446   SÍ
Alfonso Herrero  4.100.000      2.486.875  SUBIA      4.100.000       −259.395   SÍ
Gerenabarrena    3.220.000      1.253.911  SUBIA      3.220.000       −203.720   SÍ
```

**Pasan los seis de seis.** Hoy pasan cero.

**Con nombre, como pediste:**

```
Budimir  (11.990.000, venía SUBIENDO)
  coste viejo   11.990.000 €     por punto  181.667 €
  carry           −758.571 €     por punto  −11.494 €     (mercado: 21.372 €)
  valor XI       3.427.226 €     ¿pasa? SÍ

Chupe  (3.960.000, venía BAJANDO)
  coste viejo    3.960.000 €     por punto   80.816 €
  carry            507.446 €     por punto   10.356 €
  valor XI       2.895.184 €     ¿pasa? SÍ   (se quedaba a 1.064.816; ahora sobra)
```

### Cuánto más podría gastar Pepe en un día

```
hoy                       0 €
con el carry      8.874.116 €
CUANTO MAS        8.874.116 €
```

El tope de prima acota la **puja** (precio × 1,0025), pero no el **desembolso**: el peor
caso sigue siendo el bolsillo entero, porque el candidato más caro que pasa cuesta más
que el bolsillo.

---

## El aviso, y es más gordo del que pedías

Dijiste: «si con el carry pasan de repente veinte candidatos, eso es una alarma». **Han
pasado los seis de seis**, y hay un número que lo delata antes que el recuento:

> **Budimir cuesta −758.571 €. Por punto, −11.494 €.**
> Un coste que sale negativo no es un coste: el modelo dice que nos pagan por
> quedárnoslo.

Se ha dejado fuera **dos cosas**, y la segunda es la de fondo.

### 1. Las unidades no casan

`xi_value` es lo que valen los puntos **de lo que queda de temporada** (33 jornadas).
El carry es lo que cuesta tenerlo **diez días**. Comparar uno con otro es comparar un
stock con un flujo.

Prorrateando el valor XI a los mismos diez días:

```
jugador          valor XI (temporada)   a 10 días        carry   pasa
Budimir                     3.427.226     148.365     −758.571    SÍ
Jonathan David              3.213.066     139.094     −497.911    SÍ
Pépé                        3.195.607     138.338    1.471.082    no
Chupe                       2.895.184     125.333      507.446    no
Alfonso Herrero             2.486.875     107.657     −259.395    SÍ
Gerenabarrena               1.253.911      54.282     −203.720    SÍ
```

De seis pasan cuatro. **Mejora, pero no era el problema entero.**

### 2. La deriva es papel, no caja — y éste es el de verdad

El +7,43 % es el **precio de mercado**. Para convertirlo en dinero hay que vender, y eso
ya lo medimos el 16/09:

```
deriva bruta a 6 días                    +5,621 %
neto REAL de un viaje de 6 días          +3,23 %    (n=94, toda la liga)
el nuestro                               +4,20 %    en 10,2 días (n=7)
```

**Poco más de la mitad del papel llega a caja.** El carry cobra el papel entero como si
fuera dinero cobrado.

### La conclusión

> **El carry mide bien el coste de una operación DE CARTERA**: comprar, tener unos días,
> revender. Y eso ya lo tenemos medido y con sus frenos puestos: es
> `as_computer_resale`, con su listón del 3 % y su tope del +0,25 %.
>
> **Metido en `xi_upgrade_value`, lo que hace es que la vía del once apruebe
> operaciones por razones de mercado.** Y ése es exactamente el fallo que
> `classify_operation` se inventó para evitar — el jugador de 9.000.000 que sumaba 6
> puntos y se justificaba con un número de reventa.
>
> **El carry está bien y está mal colocado.**

### Entonces, ¿dónde va?

Lo dejo dicho y no lo construyo, porque es otro encargo:

- **En la vía de reventa ya está**, implícito. Lo que le falta a esa vía no es el carry:
  es la deriva **condicionada**. Hoy `as_computer_resale` no distingue comprar a uno que
  sube de comprar a uno que baja, y son diecinueve puntos a diez días.
- **En la vía del once no cabe**, porque un fichaje no se tiene diez días: se tiene la
  temporada, y para ese plazo **no hay deriva medida**. La curva satura a los diez días
  y luego se da la vuelta; extrapolarla a 231 días sería inventarla.

**Si algo hay que hacer con esto, es meter la dirección del precio en la vía de reventa,
no bajarle el coste a la del once.**

---

## Guardias

**+1 módulo, 6 guardias**, en `src/analysis/test_el_carry_v1.py`, dada de alta en
`scripts/run_validation_gate.py`.

**Las once inyecciones de fallo muerden:**

```
MUERDE  libro / vuelve a aceptar la foto vieja
MUERDE  libro / sin sello se porta como antes
MUERDE  libro / no escribe nunca
MUERDE  carry / una pieza sin `n`
MUERDE  carry / la deriva entra con signo positivo
MUERDE  carry / sin dirección inventa un carry
MUERDE  coste / pierde el tope
MUERDE  coste / no abarata nada
MUERDE  deriva / promedia las tres direcciones
MUERDE  horizonte / puesto donde no gira la curva
MUERDE  interruptor / encendido
```

**Por qué `test_la_verja_no_escribe_en_los_libros` no corre la verja entera:** hacerlo
duplicaría la verja —medido en esta casa: no termina en diez minutos— y **escribiría en
los libros de verdad**, que es justo lo que se quiere impedir. Así que prueba la
**causa**: el escritor recibe una foto vieja y tiene que negarse. El síntoma lo medí a
mano, antes y después, y está arriba.

**Y una que puso la verja en rojo:** `test_verja_determinista_v1` falló porque mi lista
de libros nombraba rutas `data/` dentro de un módulo de la verja. Mismo falso positivo
de la Regla A que el lunes. La respuesta fue mover la lista a `el_carry.py` —es un dato
sobre producción, su sitio— **no relajar la regla**.

---

## Medición

`scripts/el_carry.py` — exit 0, sólo lectura de disco, sin red, sin borrar nada.

```
python scripts/el_carry.py > salida.txt 2>&1
echo $?
```

---

## Lo que no hice, y por qué

- **Ni una escritura contra Biwenger.**
- **No encendí la fórmula.** `el_carry.ENCENDIDO = False`. Lo único que entra en
  producción es el arreglo del libro.
- **No arreglé los otros cuatro libros.** El encargo pedía la lista, no el arreglo, y
  tocar `bitacora_del_saldo`, `marcador`, `libro_de_publicacion` y `board_events` es
  cambiar cuatro escritores de producción. La lista está en
  `el_carry.LIBROS_QUE_LA_VERJA_TOCABA` y la guardia falla si alguien la encoge sin
  decirlo.
- **No borré ninguna línea de ningún libro.** Los cuatro que la verja ensució los
  devolví a HEAD.
- **No toqué `count_free_slots` ni `historical_max`.**
- **No moví ningún umbral.** El tope de la vía del once es el que ya existe.
- **No construí la regla de liquidez.**
- **No propuse comprar ni vender a nadie.**
- **No salí a la red.**
- **No toqué `.github/workflows/bordalas-live.yml`.**
- **No empujé.**

### Lo que contradijo al encargo

1. **La verja ensuciaba cinco libros, no uno.** Y el más dañado no es el mío: es la
   bitácora, donde las once líneas de hoy llevan el saldo del 13/09.
2. **El carry está mal colocado.** El concepto es correcto; el sitio no.
3. **Pasan seis de seis**, no veinte — y es peor, porque son todos los que tenían valor.
4. **Un coste negativo no es un coste**, y ése es el número que delata lo que falta.
