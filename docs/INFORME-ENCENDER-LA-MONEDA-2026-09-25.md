# Encender la moneda del que se queda

**Encargo:** «ENCENDER LA MONEDA DEL QUE SE QUEDA», 25/09/2026
**Rama:** `encender/la-moneda`, desde `main` en `f57d9f1b`
**Script:** `python scripts/la_moneda_contra_las_fotos.py`. Solo lee.

## Veredicto: se puede encender, sabiendo tres cosas

La moneda hace lo que tenía que hacer: **Dmitrovic pasa, Maffeo y Cabrera siguen en pie**, pasan 3
en vez de 2 el 18/09 y 2 en vez de 0 el 23/09. Nada de cincuenta. El paso 0 está corrido hoy, con los
cuatro de producción, y ha pasado. **Pero esta noche no pujaría por nadie**, y hay tres cosas que el
dueño tiene que saber antes de pegar la línea:

1. **La lista de la noche que publica el panel está mal.** Dice que Pepe pujaría 3.674.989 por
   Lejeune, pero con la moneda puesta Lejeune cae en `SUPERA_PRESUPUESTO`: el bolsillo de fichar
   es 2.208.580. La sombra aplica **el bolsillo de la vía de hoy** (especular, que hoy viene sin
   tope) a **la vía que ganaría con la moneda** (fichar). **Pepe no pujaría por encima de los
   2.208.580.** Lo que miente es el panel (§3).
2. **No rescata a ninguno de los 10 de `RENDIMIENTO_INSUFICIENTE`**, y no tiene por qué: esos iban
   por la reventa al Computer o por tener. **La moneda ataca otra casilla, `NO_COMPENSA`**, y ahí
   rescata a 3 de los 7 del censo.
3. **Además de la vía del once, la moneda llega a un segundo camino que puja: BUY V10**, a través de
   la valoración compartida. Hoy está dormido (su última puja fue el 04/09), pero existe (§1.3).

---

## 1. Qué hay, exactamente

### 1.1 El interruptor

**`BORDALAS_LA_MONEDA_DE_LA_LIGA`**, en [la_moneda_del_fichaje.py:92](src/analysis/la_moneda_del_fichaje.py#L92):

```python
ENV = "BORDALAS_LA_MONEDA_DE_LA_LIGA"
```

Se lee en `activa()` ([:100-111](src/analysis/la_moneda_del_fichaje.py#L100-L111)) con los valores
`1`, `true`, `si` o `yes`.

### 1.2 Su estado hoy: apagado, y no se enciende en ningún otro sitio

- **No está en `.github/workflows/bordalas-live.yml`.** Los `BORDALAS_*` con valor del workflow son
  cuatro: `JORNADAS_POR_SU_FECHA`, `REVENTA_SOLO_SI_JUEGA`, `EL_ONCE_UNA_VEZ` y
  `SOLVENCIA_POR_SU_PLAZO` (más `BID_SALT`, que es un secreto).
- En el código solo aparece en el propio módulo, en dos comentarios (`player_value_engine`,
  `la_lista_de_la_noche`), en `config/paso_0.json` y en tres guardias, que **lo quitan** del
  entorno (`os.environ.pop`). Nadie lo pone.

### 1.3 A qué vías afecta

**Por vías: solo a las dos de quedárselo.** La moneda solo entra en `xi_upgrade_value`
([player_value_engine.py:1279-1281](src/analysis/player_value_engine.py#L1279-L1281)), que solo tiene
dos llamadores: la vía del once ([acquisition_valuation.py:553](src/analysis/acquisition_valuation.py#L553))
y la de ficha vacía ([:639](src/analysis/acquisition_valuation.py#L639)). **La reventa al Computer
no pasa por ahí** (`computer_resale_value`), ni la especulación, ni la de tener. Hay guardia:
`test_el_que_se_revende_paga_la_del_mercado`.

**Pero hay algo que el encargo no preguntaba y hay que saber.** `value_candidate` no solo lo llama el
tablero. También lo llama `calculate_intelligent_bids`
([intelligent_bid_engine.py:779](src/analysis/intelligent_bid_engine.py#L779)), y de ahí sale una
cadena que puja de verdad:

```
v10_full_autonomous_live:1272  build_controlled_run(execute_live=True)     <- BUY V10, en cada vuelta sin escritura
  -> market_trader_shadow -> calculate_intelligent_bids -> value_candidate  <- aqui entra la moneda
       -> suggested_bid -> build_market_bid_authority: authority_bid = max(precio, legacy_bid, sintetica)
  -> recommended = min(authority_bid, max_rational)
```

Con la moneda, una vía de plantilla que antes no pujaba puede dar un `suggested_bid`, y eso **puede
subir lo que puja BUY V10**, que es un camino de **especulación**. Tiene dos frenos que no dependen de
la moneda: `max_rational`, que es precio × (1 + subida esperada) / (1 + rendimiento exigido), y sus
puertas (`BUY_SPECULATION`, rendimiento y saldo negativo sin deuda segura). **Hoy está dormido**: sus
16 posiciones `CONTROLLED_LIVE` son del 18/08 al 04/09 (15 perdidas), y no ha vuelto a pujar. No es
la vía de reventa, así que no es el fallo que el encargo decía que parara todo. Pero es la moneda de
quedarse entrando en un camino de comerciar, y no está medido cuánto. **Hay que vigilarlo** (va en
el texto del YAML).

### 1.4 El paso 0, corrido hoy

```
python scripts/run_validation_gate.py --paso-0
(corriendo con 4 interruptores de produccion: BORDALAS_EL_ONCE_UNA_VEZ, BORDALAS_JORNADAS_POR_SU_FECHA,
 BORDALAS_REVENTA_SOLO_SI_JUEGA, BORDALAS_SOLVENCIA_POR_SU_PLAZO)
EL PASO 0 HA TARDADO 151 s (2.5 min).
PASADO. Quedan probados 30 interruptores, apuntados en config/paso_0.json.
```

**PASADO, hoy a las 17:23 UTC, con los 30 del inventario a la vez**, `BORDALAS_LA_MONEDA_DE_LA_LIGA`
incluido. `config/paso_0.json` cambia en fecha, duración y huella; la lista es la misma. **Va en este
commit.** El paso 0 avisa de que ese fichero tiene que llegar a git con el cambio del YAML, y así,
cuando el dueño pegue la línea, el registro ya está en `main`.

---

## 2. El contrafactual, con los datos de hoy

### 2.1 El método, y por qué hay que fiarse de él

La moneda cambia **un** factor de una multiplicación: el valor de fichaje con la moneda es
(valor − recuperado) × 30.000 / tarifa + recuperado, y hay guardia de que es lineal. **Y después se
vuelve a clasificar**: con la moneda, una vía de plantilla puede pasar a superar el precio, y entonces
`classify_operation` convierte la operación en **fichaje**. Eso cambia el bolsillo y el listón
(sin el 3 %). Por eso el script llama a las funciones de producción (`classify_operation`,
`budget_for_intent`, `optimal_bid`) y no a una copia. El modelo de puja es el de producción
(`build_bid_model` sobre `rival_intelligence.json`): reproduce la puja de Cabrera del 18/09 en
3.133.329 frente a 3.133.633, con un 66 % frente al 65 %.

**La prueba de que la reconstrucción vale:** sin la moneda da **la misma decisión que publicó la
foto en 20 de 20** candidatos el 18/09, **20 de 20** el 23/09 y **19 de 20** hoy. El que falla hoy es
Félix Correia, por la vía de tener, cuyo tope de bolsillo no reproduzco. La moneda no le afecta.

### 2.2 La tabla

| | 18/09 hoy | 18/09 con la moneda | 23/09 hoy | 23/09 con la moneda | 25/09 hoy | 25/09 con la moneda |
|---|---|---|---|---|---|---|
| tarifa del mercado → factor | 21.529 → ×1,393 | | 21.214 → ×1,414 | | 21.517 → ×1,394 | |
| **pasan todas** | **2** | **3** | **0** | **2** | **0** | **0** |
| **Dmitrovic** | NO (`NO_COMPENSA`) | **SÍ**, pujaría 4.784.788 | | | | |
| **Maffeo** | SÍ, 1.755.284 | **SÍ**, 1.755.284 | | | | |
| **Cabrera** | SÍ, 3.133.329 | **SÍ**, 3.214.496 | | | | |
| **Ceballos** | | | NO (`RENDIMIENTO_INSUFICIENTE`) | **NO**, igual | | |
| Thiago Fernández | | | `NO_COMPENSA` | SÍ, 1.258.306 | | |
| Oriol Rey | | | `NO_COMPENSA` | SÍ, 1.258.306 | | |
| Lejeune | | | | | `NO_COMPENSA` | `SUPERA_PRESUPUESTO` |
| Antonio Blanco | | | | | `SUPERA_PRESUPUESTO` | `SUPERA_PRESUPUESTO` |

El 14/09 no se puede medir: ningún candidato tenía valor por una vía de plantilla (era la época sin
pronóstico de titularidad), así que la moneda no tenía nada que cambiar.

**Los tres renglones de la prueba salen.** Dmitrovic pasa y Maffeo y Cabrera no se caen. Pero ojo:
**a Cabrera le sube la puja en 81.167 €** (de 3.133.329 a 3.214.496), porque con la moneda gana su
vía de ficha vacía, que vale más. La moneda no solo decide quién pasa: también cuánto se paga.

**Ceballos no se rescata, y es correcto:** su vía era la reventa al Computer (0,20 % de rendimiento).
La moneda no la toca, y el encargo pide que no la toque.

### 2.3 Diferencia con la medición del 23/09

El 22/09 salía «18/09: de 2 a 4», con Castrín como cuarto. Hoy sale de 2 a 3, porque **aquella
medición usó una tarifa de 19.914 €/punto (×1,51) y la foto publica 21.529 (×1,393)**. Castrín pide
19.596 €/punto y con el factor bueno no pasa. La foto del 20/09 (0 → 4) no está en local y no la he
podido rehacer.

### 2.4 ¿Cuántos pasan al día? Entre 0 y 3. No son cincuenta.

Tres días con valor de fichaje: **3, 2 y 0** (n=60 candidatos). Y el listón sigue funcionando. De
los que tienen alguna vía de plantilla con valor, con la moneda superan el precio 3 de 6 el 18/09,
2 de 5 el 23/09 y 2 de 4 hoy. El resto sigue en `NO_COMPENSA` o en el bolsillo: Dumfries pide
23.237 €/punto y Mangala 24.941. El techo efectivo es 30.000 × 0,9 = 27.000 €/punto con confianza
1,0, y menos con la confianza real.

### 2.5 ¿Cuántos de los 10 de `RENDIMIENTO_INSUFICIENTE` rescata? **Cero.**

Y no es un fallo de la moneda: es que esos 10 no eran de su casilla. Del censo: 7 iban por la
**reventa al Computer** (Giménez, Gorrotxategi, Fran González, Ndukwe, Firpo, Pepelu y Ceballos) y 3
por **tener** (Bouare, Szczęsny y David Otorbi). Ninguno tiene vía de plantilla con valor. La moneda
**sí** ataca la casilla de al lado: **de los 7 `NO_COMPENSA` del censo rescata 3** (Dmitrovic,
Thiago Fernández y Oriol Rey). Lo que el censo midió como «no puede pasar nunca» (la reventa contra el
3 %) **sigue sin poder pasar**. Esa conversación sigue abierta y la moneda no la cierra.

---

## 3. La lista de esta noche

Foto de hoy: `diagnostico/status.json`, generada el 25/09 a las 19:13 (bajada con
`foto_para_claude.ps1`). Bolsillo de fichar: **2.208.580**. Bolsillo de especular: `None`.

**Lo que publica el panel, tal cual** (`lista_de_la_noche`, 1 nombre de 34 mirados):

```
jugador   precio      lo que pujaria   via          que le hacia morir antes
Lejeune   3.560.000   3.674.989        XI_UPGRADE   NO_COMPENSA (vale 3.313.524 a precio de mercado)
```

**Lo que haría de verdad con la moneda puesta:**

```
jugador          precio      vale con la moneda   bolsillo    decision
Lejeune          3.560.000   3.922.963            2.208.580   SUPERA_PRESUPUESTO   -> no puja
Antonio Blanco   3.230.000   3.761.633            2.208.580   SUPERA_PRESUPUESTO   -> no puja
```

**Esta noche no pujaría por nadie. No querría pujar por encima de los 2.208.580: lo impide su propio
bolsillo.**

**Por qué la sombra dice otra cosa, con la línea.** En
[acquisition_board.py:1350-1356](src/analysis/acquisition_board.py#L1350-L1356), `_plan_noche` corre
`optimal_bid` con `available_budget=presupuesto`, y ese `presupuesto` es el de la intención **de hoy**
(`budget_for_intent(valoracion.intent)`, [:1097](src/analysis/acquisition_board.py#L1097)). Hoy Lejeune
es `SPECULATION` (su fichaje no llega al precio), el bolsillo de especular viene `None`, y
`optimal_bid` con `None` **no pone tope**. Con la moneda, `classify_operation` lo haría fichaje, y el
bolsillo sería el de fichar. **La sombra mezcla el bolsillo de una vía con el valor de otra**, que es
el error que [deployment.py:261-280](src/analysis/deployment.py#L261-L280) describe como «la misma mezcla
que ya costó dos noches». **No lo he arreglado**: el encargo es comprobar y no tocar.

Mientras siga así, **la lista del panel no sirve para lo que pidió el dueño** («por quién y cuánto»),
porque puede enseñar pujas que no van a salir. Para esta noche lo que vale es la segunda tabla.

---

## 4. El texto para el YAML

Para pegar en `env:`, debajo de `BORDALAS_SOLVENCIA_POR_SU_PLAZO`:

```yaml
      # Encendido 25/09. EL QUE SE QUEDA COBRA EN LA MONEDA DE LA LIGA.
      #
      #   NO CAMBIA LA FORMULA: cambia UN factor. En `xi_upgrade_value` el
      #   punto se pagaba a la tarifa del MERCADO (mediana de precio/puntos
      #   del catalogo, ~21.500 EUR). Para quien te quedas, un punto vale lo
      #   que PAGA LA LIGA: 30.000 EUR, de `caja_de_la_liga`, cuadrado al euro
      #   sobre 24 dias. Margen, confianza, vetos del once y suelo de
      #   titularidad no se tocan.
      #
      #   SOLO LAS DOS VIAS DE PLANTILLA: mejora del once y ficha vacia. La
      #   reventa al Computer, especular y tener siguen en la del mercado
      #   (guardia `test_el_que_se_revende_paga_la_del_mercado`).
      #
      #   MEDIDO, reconstruyendo las fotos con las funciones de produccion
      #   (sin la moneda la reconstruccion da la decision publicada en 20/20,
      #   20/20 y 19/20):
      #       18/09   pasan 2 -> 3   Dmitrovic pasa; Maffeo y Cabrera siguen
      #       23/09   pasan 0 -> 2   Thiago Fernandez, Oriol Rey
      #       25/09   pasan 0 -> 0   Lejeune y Antonio Blanco: SUPERA_PRESUPUESTO
      #   Entre 0 y 3 al dia, n=60 candidatos en 3 fotos. El liston sigue
      #   frenando: pasan el precio 7 de 15 con via de plantilla.
      #   Rescata 3 de los 7 NO_COMPENSA del censo y 0 de los 10
      #   RENDIMIENTO_INSUFICIENTE (esos van por reventa o tener: no es su via).
      #
      #   Paso 0 PASADO el 25/09 con los 30, este incluido, y los cuatro de
      #   produccion puestos.
      #
      #   LO QUE NO ESTA MEDIDO Y HAY QUE VIGILAR:
      #     - Tambien sube CUANTO se paga, no solo quien pasa: Cabrera
      #       3.133.329 -> 3.214.496 (+81.167) el 18/09.
      #     - La LISTA DE LA NOCHE del panel usa el bolsillo de la via de HOY,
      #       no el de la via que gana con la moneda: el 25/09 decia 3.674.989
      #       por Lejeune y la decision real era SUPERA_PRESUPUESTO. Hasta que
      #       se arregle, no dice lo que va a pasar.
      #     - Llega tambien a BUY V10 (build_controlled_run -> market_trader_shadow
      #       -> calculate_intelligent_bids -> value_candidate), que es un
      #       camino de ESPECULAR: puede subir su authority_bid, acotado por
      #       max_rational. Dormido desde el 04/09. Si vuelve a pujar, mirar
      #       si la puja sale de un suggested_bid de plantilla.
      #     - Si pasan mas de 3-4 al dia, el liston se ha quedado sin funcion:
      #       mirar el EUR/punto que piden los que pasan.
      BORDALAS_LA_MONEDA_DE_LA_LIGA: "1"
```

---

## 5. Lo que no hice, y por qué

- **Ni una escritura contra Biwenger.** Todo es reconstrucción sobre fotos.
- **No encendí el interruptor ni toqué el workflow.** Lo pega el dueño.
- **Salí una vez a la red, al panel del dueño**, con su `scripts/foto_para_claude.ps1`, para tener la
  foto de hoy. Es lectura del propio panel: sin Biwenger y sin ver las credenciales. Antes guardé la
  foto del 23/09 en `diagnostico/status-2026-09-23.json`, porque el script la pisa y el censo de esta
  tarde la usa.
- **No arreglé la sombra de la noche** (§3) ni la fuga a BUY V10 (§1.3). Son cambios de código y el
  encargo era comprobar.
- No toqué la regla 2, el listón del 3 %, la reventa, ninguna fórmula ni ninguna constante de la
  lista. No empujé.

Lo que entra en el commit: este informe, `scripts/la_moneda_contra_las_fotos.py` y
`config/paso_0.json` (el registro del paso 0 de hoy).
