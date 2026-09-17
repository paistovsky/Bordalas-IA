# Los tres arreglos gratis — informe

**Rama:** `ojeador/los-tres-arreglos` (desde `ojeador/los-tres-denominadores`)
**Fecha:** 16/09/2026
**Verja:** 143/143 en verde, exit 0, salida a fichero
**Push:** NO. **Interruptor:** APAGADO, `ENCENDIDO = False` sin tocar.
**Escrituras contra Biwenger:** ninguna. Ningún umbral tocado.

---

## Lo primero: el tercero no era gratis

El encargo llamó a esto «los tres arreglos gratis» y justificó el de la curva diciendo
que **nos haría pujar menos**. Medido sobre 70 combinaciones de precio y valor:

```
SPECULATION  (tope +0,25 %, los 7 rivales de la foto)
   sube  0    baja  0    IGUAL 70

XI_UPGRADE   (sin tope de prima)
   sube 10    baja  0    igual 60
   el peor:  precio 7.820.000, valor x1,05
             7.860.665  ->  8.072.587      +211.922 EUR
```

> **La curva nueva no baja ni una puja. Sube diez, y hasta +211.922 € en una.**

**Por qué sube, y por qué el número nuevo es el correcto:** la curva vieja repartía a
los rivales hasta el +24,5 %, y con esa forma subir un poco la puja no compraba casi
nada. La masa real dice que casi todos pujan pegados al precio, así que superarlos
**sí** compra probabilidad — y el valor esperado sube con ella.

El arreglo es correcto. **La premisa de que ahorraba dinero era falsa**, y como el
sitio donde mueve dinero es `XI_UPGRADE` —que el encargo dice explícitamente que no se
toca—, **esto es una decisión tuya antes de encender nada.** Lo dejo puesto, medido y
con guardia que vigila cuánto sube; deshacerlo es una línea.

---

## BLOQUE 1 — El `intent` prestado

### No es herencia: es una etiqueta puesta mal en el origen

El encargo dice «ninguna decisión debe heredar la intención de la vía que perdió».
Miré esperando encontrar eso y **no es lo que pasa**: `mejor.get("intent")` toma el
`intent` **del ganador**, no del perdedor. El problema es otro y es más simple:

```python
# player_value_engine.py — computer_resale_value
"intent": "SPECULATION",
"route": "COMPUTER_RESALE",

# player_value_engine.py — speculation_value   (ANTES)
"intent": "SPECULATION",
#  ... y ninguna `route`
```

**Las dos vías se declaran `SPECULATION` a sí mismas, y sólo una de las dos decía por
dónde venía.** La de tendencia no declaraba `route` en absoluto: donde se leía, había
un `or "PRICE_TREND"` de respaldo tapando el hueco.

### Lo que se ha hecho

1. **`speculation_value` declara su vía**: `route: "PRICE_TREND"`. No cambia ninguna
   decisión — el respaldo ya producía esa misma cadena—, pero ahora se declara donde
   se sabe.
2. **`optimal_bid` recibe `route` y nombra la vía de verdad en el motivo.** La frase
   falsa desaparece:

```
ANTES   Marc Roca   Como especulacion rinde un 0.14 % (4.864 EUR sobre 3.370.001...)
AHORA   Marc Roca   Por reventa al Computer rinde un 0.14 % (4.864 EUR sobre 3.370.001...)
        Pedro Diaz  Por especulacion sobre el ritmo del jugador rinde un 0.60 % (...)
```

3. **El plan publica `value_route` y `value_route_label`**, también en los rechazos —
   antes un rechazo no decía de dónde venía el número que lo motivaba.
4. **Sin `route`, no se inventa un nombre**: dice «una vía no declarada (intent X)».
   Un motivo que nombra la vía equivocada es peor que uno que dice «no consta».

### Lo que NO se ha hecho, y por qué

**No he quitado el `intent: "SPECULATION"` de `computer_resale_value`.** Si dejara de
llamarse SPECULATION, `optimal_bid` dejaría de aplicarle el listón del 3 % y el mínimo
de 25.000 € — y como el techo de esa vía es 1,5075 %, **hoy ese listón la cierra por
completo**. Quitar la etiqueta abre una vía entera. Eso es mover dinero y es tuyo.

### ¿Está el patrón repetido? Sí, en seis sitios — y uno ya estaba resuelto

```
acquisition_valuation.py:952    max(sombra_opciones,  key=value)   -> sombra, publica
acquisition_valuation.py:1035   max(opciones_hoy,     key=value)   -> comparación
acquisition_valuation.py:1052   max(antes_opciones,   key=value)   -> comparación
acquisition_valuation.py:1192   max(opciones,         key=value)   -> EL QUE DECIDE
deployment.py:222               max(todas,            key=value)   -> ya separado
deployment.py:226               max(fichaje,          key=value)   -> ya separado
```

**`deployment.py` ya lo tenía resuelto** desde el 13/09, y merece la pena copiar el
patrón: separa `value` (el mayor de todas las vías, informativo) de `decision_value`
(la vía por la que se va a pagar), y `value_route` de `route`. Lo destapó
`test_acquisition_wiring_v1` con un jugador de 9.000.000 que sumaba 6 puntos.

Los cuatro de `acquisition_valuation` siguen el patrón viejo, pero **con las dos vías
declarando ya su `route`, los cuatro publican ahora una vía verdadera.** El único que
decide es el 1192, y con `DEPLOYMENT_ENABLED` apagado usa `mejor["value"]` —el mayor
de todas— que es exactamente la mezcla que `deployment` vino a arreglar. **No lo he
tocado: es el interruptor de despliegue y no es de este encargo.**

**`test_la_via_que_gana_no_presta_su_etiqueta`** prueba los dos sentidos —gana la del
Computer y gana la de tendencia— y **falla si sólo hay una vía viva**, porque con una
sola cualquier etiqueta acertaría por casualidad.

---

## BLOQUE 2 — El denominador. Aquí estaba el dinero, y no donde pensábamos

### Primero: el arreglo que pedías, hecho

```python
# summary() — ANTES: el error se acumulaba sobre TODO lo cerrado
error = entrada.get("magnitude_error_percent")
if error is not None:
    datos["_errores"].append(float(error))
```

Ahora se publican **los dos, cada uno con su nombre y su `n`**:

| campo | muestra | `n` en producción (FUTBOLFANTASY) |
|---|---|---|
| `mean_magnitude_error_percent` | sólo HIT + MISS | 7.579 |
| `magnitude_error_n` | — | 7.579 |
| `mean_magnitude_error_percent_all_outcomes` | + FLAT + UNKNOWN | 10.339 |
| `magnitude_error_all_outcomes_n` | — | 10.339 |
| `magnitude_error_shares_sample` | ¿comparten? | `True` |

El que comparte muestra con `hit_rate` se queda con el nombre de siempre, porque es el
que recorta y es el que tenía que haber sido desde el principio.

### **Pero quitar los FLAT sube el error, no lo baja**

Reconstruí el libro de acierto entero desde nuestra propia serie —las tres fuentes
publican `price_increment/precio`, 69 de 69 y 15 de 15 medido en el encargo anterior—
y medí las dos cosas sobre la misma muestra:

```
plazo    n       error | DECIDIDAS   error | TODAS   error | sólo FLAT
  1    12.615         0,748              0,666            0,399
  3     7.081         3,832              3,745            2,978
  7     2.323        12,050             12,028            9,255
agrup. 22.019         3,244              2,855            0,943
```

**Los FLAT son los errores PEQUEÑOS, no los grandes.** Y tiene un mecanismo, no es
casualidad: un FLAT ocurre cuando la fuente dice cero o cuando el precio no se movió, y
—medido en el encargo anterior— si ayer se quedó plano, hoy se queda plano el 87,2 % de
las veces. Son los días tranquilos, y en los días tranquilos todo el mundo acierta.

> **Corrección al encargo: el ±3,98 % no estaba inflado por los FLAT. Quitarlos lo sube
> de 2,855 a 3,244.**

### Lo que SÍ lo inflaba: no llevaba plazo

```
error a 1 día    0,748
error a 3 días   3,832
error a 7 días  12,050
--------------------------
agrupado         3,244    <- el único que publicaba el libro
```

`estimacion(..., horizonte=1)` cogía señales de **un día** y las recortaba con un error
medido sobre todo a **tres y siete**. Un +1 % de movimiento contra un error de 3,244 da
cero; contra su 0,748 de verdad, no.

**Doctrina 53 otra vez, y en el sitio más caro.** Ahora `summary()` publica
`by_horizon`, cada plazo con su acierto, su error, su nulo y su `n`, y
`peso_de_la_fuente` usa el del plazo que estima.

### Y la pregunta honesta: **el recorte sobra**

Medido contra lo que pasó de verdad (error medio absoluto, menos es mejor):

```
                                        1 día     3 días
no pronosticar nunca                    1,8942    6,2196
con recorte, error agrupado (lo de hoy) 0,8922    4,2144    mudo 36 % / 40 %
con recorte, error CORREGIDO            0,9220    4,3567    mudo 39 % / 48 %
dos pasos, sin recorte                  0,6805    3,4496    mudo  0 % /  0 %
```

**Arreglarle el denominador lo empeora**, porque lo hace más agresivo. No es un problema
de denominador: la forma estaba mal. `1 − error/|magnitud|` confunde **dispersión** con
**encogimiento**: el error medio de un buen estimador no es un umbral por debajo del
cual no sabe nada.

La fórmula queda en dos pasos, como preferías:

> **magnitud × (2·acierto − 1) × persistencia**

### Lo que el recorte sí hacía bien, y quién lo hace ahora

Tapaba a COMUNIATE_PULSO. Eso sigue tapado, pero por **una puerta por fuente en vez de
un recorte por señal**: una fuente aporta su tamaño sólo si se equivoca **menos que no
decir nada**.

```
plazo   error   nulo |lo que pasó|   ¿bate al nulo?
  1     0,748        2,405                SÍ
  3     3,832        6,750                SÍ
  7    12,050       14,233                SÍ

COMUNIATE_PULSO     35,71  contra  ~2,4   NO
```

Se decide **una vez, por fuente**, no señal a señal. Y una fuente sin el nulo medido
**tampoco pasa**: no saber si acerca no es lo mismo que saber que acerca.

### Cuántos de los 171 vuelven

```
mudos con la fórmula vieja                       171
   vuelven con pronóstico DISTINTO de cero        86   <- los que pedías
      al alza    39
      a la baja  47
   vuelven diciendo exactamente 0,00 %            85
```

**86 exactos, que es el número que traías.** Los otros 85 son los de incremento cero:
vuelven diciendo «no se espera que se mueva», que es un pronóstico pero no una
oportunidad — aguas abajo `speculation_value` los cierra con `SIN_REVALORIZACION`.

```
jugador          incremento    observado     estima
Raphinha           +170.000     +0,916 %    +0,845 %/día
Mikel Rodríguez    −150.000     −6,227 %    −5,748 %/día
Fermín             +120.000     +0,884 %    +0,816 %/día
Bellingham         +110.000     +0,623 %    +0,575 %/día
Canales             −70.000     −1,142 %    −1,054 %/día
Budimir             +70.000     +0,650 %    +0,600 %/día
Olasagasti          +70.000     +2,460 %    +2,271 %/día
Joan García         −70.000     −0,750 %    −0,692 %/día
```

**Ninguno de los 86 llega a +3 %/día.** El mayor es Olasagasti con +2,268 %.

### Una guardia cambió lo que exige, y no en silencio

`test_un_movimiento_pequeno_no_sobrevive_a_su_error` exigía que un +0,30 % saliera
**SIN PRONÓSTICO**. Ahora se llama `test_un_movimiento_pequeno_sale_pequeno_no_mudo` y
exige que salga **+0,28 %**, que siga siendo mucho menor que uno grande, y que nunca
supere a lo observado. El motivo entero, con la medición, está en su docstring.

---

## BLOQUE 3 — Los pesos de la curva

### El primer intento estaba mal, y lo destapó una guardia mía

Repartí la masa por la **distancia entre índices de corte**. Esa distancia la fijan la
rejilla de cuantiles y `N`, **no las pujas**: con 72 muestras salía siempre
`[14, 14, 15, 14, 11, 3, 1]` dieran lo que dieran los rivales. Habría sido cambiar una
constante por otra y llamarlo medir.

Ahora se **cuentan las pujas de cada banda**. Sobre las 72 de la foto del 14/09:

```
peldaño    prima   cuantil   ANTES 1/7   AHORA masa    n   estado
   1      1,0000     0,05      0,1429      0,1944     14   ok
   2      1,0052     0,20      0,1429      0,1944     14   ok
   3      1,0222     0,40      0,1429      0,2083     15   ok
   4      1,0323     0,60      0,1429      0,1944     14   ok
   5      1,0622     0,80      0,1429      0,1528     11   ok
   6      1,2109     0,95      0,1429      0,0417      3   SIN CALIBRAR
   7      1,2449    0,995      0,1429      0,0140      1   SIN CALIBRAR
                               ------      ------     --
                               1,0003      1,0000     72
```

Los pesos suman **uno exacto** — el último absorbe el redondeo, porque una curva que
suma 0,9998 mete un sesgo silencioso en cada probabilidad.

### El mínimo: **5 pujas por peldaño**, y por qué

Intervalo de Wilson al 95 % sobre el peso de un peldaño, con N=72:

```
n=1   [0,0025 , 0,0746]   30,4x de ancho
n=3   [0,0143 , 0,1155]    8,1x
n=5   [0,0300 , 0,1525]    5,1x
n=11  [0,0875 , 0,2532]    2,9x
```

Por debajo de cinco el intervalo se pasa del factor cinco y el número deja de ser una
medida. **Dos peldaños de la foto quedan por debajo** y se publican marcados, con el
aviso dentro de `reason`.

**Qué se hace con un peldaño flojo: se marca, y se deja su masa observada.** No se
borra ni se funde con el de al lado, porque las dos cosas afirmarían algo **más fuerte**
que el propio dato — borrar el de arriba sería decir «ningún rival paga tanto», y de
estas mismas 72 pujas **hubo cuatro que sí**. Un peso flojo con su aviso es más honesto
que un cero inventado.

### Qué habríamos pujado

```
XI_UPGRADE, 70 combinaciones     sube 10   baja 0   igual 60   peor +211.922 EUR
SPECULATION, 70 combinaciones    sube  0   baja 0   igual 70
```

**Con los siete rivales de la foto, la vía de especulación no se mueve ni un euro.**
Su tope de +0,25 % la deja por debajo del primer peldaño, y ninguna reponderación la
alcanza.

**Pero eso depende de cuántos rivales haya.** Con cinco en vez de siete, `p` a
`precio+1` pasa de **0,1293 a 0,1558** — y `MIN_WIN_PROBABILITY` vale **0,15**, justo
en medio. Entonces **15 de 70 combinaciones dejan de decir `PROBABILIDAD_INSUFICIENTE`
y pasan a pujar**. Al mínimo, `precio+1`, nunca más — y la guardia lo exige. No es un
fallo: la probabilidad nueva es la correcta y el suelo es el de siempre. Pero el cambio
**no es neutro** si algún rival deja de ser creíble.

### Y el 0,55 de `XI_UPGRADE` no existe

Busqué el objetivo de probabilidad que el encargo dice no tocar. **No hay ninguno.**
`optimal_bid` maximiza valor esperado y punto; el 0,5435 de Rubén García y el 0,5591 de
Kiko Femenía son **dónde cayó el máximo**, no una mira. Así que «arreglamos la
probabilidad para que apunte con la mira bien puesta» no aplica: al corregir la
probabilidad, el máximo se mueve, y se mueve **hacia arriba**.

---

## BLOQUE 4 — Volver a contar

```
candidatos que pasan el listón del 3 %, 7 rivales, los tres arreglos puestos:

   curva vieja 1/7          0
   curva nueva por masa     0
```

> **Siguen siendo cero.**

```
margen bruto máximo          6,04 %
p necesaria para el 3 %      0,4970
p disponible (curva nueva)   0,1178   ->  rinde 0,71 %
p disponible (curva vieja)   0,0957   ->  rinde 0,58 %
```

### Qué tope de prima haría falta — y la respuesta es peor de lo que pedías

Preguntabas un número: **+3,23 %**, trece veces el tope de hoy, da `p = 0,6479 ≥ 0,4970`.

**Pero ese no es el número que importa**, porque subir la puja compra probabilidad y a
la vez encoge `(valor − puja)`. Barriendo el tope entero:

```
 prima       puja    p nueva    rinde
 0,25%  1.002.501    0,1178    0,71 %
 1,00%  1.010.001    0,2289    1,20 %
 2,50%  1.025.000    0,4086    1,52 %
 3,23%  1.032.301    0,6479    1,93 %   <- el máximo
 4,00%  1.040.001    0,6479    1,43 %
 5,00%  1.050.001    0,6479    0,80 %
 6,00%  1.060.001    0,6479    0,18 %
```

> **El mejor rendimiento alcanzable por esta vía, con cualquier tope de prima, es
> 1,93 %. El listón son 3 %. No hay tope que lo abra.**
>
> (Con la curva vieja el máximo era 1,14 %: el arreglo de los pesos casi lo dobla, y
> aun así no llega.)

**Así que la conversación no es «subimos el tope».** Con `MAX_PROJECTED_DAILY_RATE` en
4,53 %/día y horizonte 3, el valor máximo es `precio × 1,06301`, y de ahí no salen tres
puntos de rendimiento por ninguna combinación de puja y probabilidad. **Lo que hay que
mover es el listón, el horizonte o el tope de proyección — o la vía se queda cerrada.**

No propongo ninguno. Sólo digo dónde está la pared.

---

## Lo que contradijo al encargo, y ganó la medición

1. **El error no estaba inflado por los FLAT.** Quitarlos lo **sube** (2,855 → 3,244).
   Lo que lo inflaba era agrupar plazos: 0,748 a un día contra 3,244 agrupado.
2. **Arreglar el denominador, solo, empeora la estimación** (0,8922 → 0,9220 de error,
   y de 36 % a 39 % de mudos). El recorte estaba mal de forma, no de muestra.
3. **La curva nueva no hace pujar menos.** No baja ninguna puja y sube diez de setenta
   en `XI_UPGRADE`, hasta +211.922 €.
4. **No hay ningún objetivo de 0,55 en `XI_UPGRADE`.** Es donde caía el máximo de valor
   esperado.
5. **No es herencia del perdedor**: las dos vías se declaran `SPECULATION` a sí mismas,
   y la de tendencia no declaraba `route` en absoluto.
6. **De los 171 mudos vuelven los 171**, pero sólo **86 con señal**; los otros 85 dicen
   exactamente 0,00 %.
7. **Ningún tope de prima abre la vía**: el máximo alcanzable es 1,93 % contra un listón
   de 3 %.

---

## Lo que queda en el repo

```
src/analysis/player_value_engine.py        speculation_value declara route PRICE_TREND
src/analysis/rival_bid_model.py            nombre_de_la_via, route en optimal_bid,
                                           pesos por masa, CORTES_DE_LA_CURVA,
                                           MIN_SAMPLES_PER_RUNG
src/analysis/acquisition_board.py          pasa route (dos llamadas)
src/analysis/intelligent_bid_engine.py     pasa route
src/intelligence/scout/accuracy.py         los dos errores, el nulo, by_horizon
src/analysis/el_pronostico_del_ojeador.py  formula de dos pasos, puerta por fuente
src/analysis/test_los_tres_arreglos_v1.py  8 guardias
scripts/run_validation_gate.py             +1 en la lista (143)
```

| guardia | qué pasa si se rompe |
|---|---|
| `test_la_via_que_gana_no_presta_su_etiqueta` | vuelve «como especulación» con un número de la reventa |
| `test_el_acierto_y_el_error_comparten_muestra` | los dos números vuelven a mezclar denominadores |
| `test_los_pesos_salen_de_la_masa` | la cola del +24,5 % vuelve a valer 1/7 |
| `test_el_peso_es_la_cuenta_de_pujas_de_su_banda` | los pesos salen de la rejilla y no de las pujas |
| `test_la_curva_nueva_no_toca_la_especulacion_y_sube_el_once` | la especulación se mueve, o el once sube más de 250.000 € |
| `test_sin_via_declarada_no_se_inventa_una` | el motivo nombra una vía que no es |
| `test_un_libro_vacio_no_publica_numeros` | sin registros se publica un cero que se lee como «falla siempre» |
| `test_el_fixture_trae_de_todo` | **regla 24** |

Ninguna lee `data/`, sale a la red ni mira el reloj. Una de ellas —
`test_un_libro_vacio_no_publica_numeros` — **no** pasa `None` a `summary()` a propósito:
`summary(None)` significa «lee el libro del disco», y una guardia que lee estado de
producción daría verde o rojo según lo que el ciclo hubiera escrito esa hora.

**Un fallo de robustez encontrado de paso y arreglado:** `calibrate_premium_curve(None)`
reventaba con `TypeError` y se llevaba por delante toda la valoración. Ahora se queda
sin muestras y devuelve la curva por defecto diciendo por qué, que es el mismo camino
que «no hay suficientes pujas».

---

## Lo que NO hice, y por qué

- **No encendí nada.** `ENCENDIDO = False` sin tocar, con su guardia.
- **No toqué ningún umbral**: ni `PRIMA_MAXIMA_DE_PUJA`, ni el listón del 3 %, ni
  `MIN_WIN_PROBABILITY`, ni el cupo, ni el suelo, ni `bid_cap`, ni `PUEDEN_ENCERRARLO`,
  ni `MAX_SINGLE_SPECULATION_PERCENT`, ni `MAX_SAFE_DEBT`, ni `TREND_DECAY`, ni
  `MAX_PROJECTED_DAILY_RATE`.
- **No quité el `intent: "SPECULATION"` de `computer_resale_value"`.** Quitarlo le retira
  el listón del 3 % y abre una vía entera. Es tuyo.
- **No toqué el `max()` que decide** (`acquisition_valuation.py:1192`) ni el interruptor
  de despliegue, aunque `deployment.py` ya tiene el patrón correcto y sería el sitio del
  que copiarlo.
- **No rellené el agujero del 07/09** ni interpolé nada.
- **No metí el equipo ni la clasificación. No toqué el workflow. No empujé.**
- **No pude usar el libro de acierto de producción**: el de este disco tiene 8
  predicciones, todas de prensa y todas sin resolver. Los números corregidos salen de
  **reconstruir el libro desde nuestra propia serie**, que es legítimo porque las tres
  fuentes publican `price_increment/precio` —69 de 69 y 15 de 15—, pero **no es el libro
  de producción** y así está dicho en cada tabla. El día que el libro real llegue a este
  disco, `summary()` ya publica los dos denominadores y el reparto por plazo.

---

## Lo que hay que decidir

1. **La curva sube las pujas de `XI_UPGRADE`** hasta +211.922 € en el peor caso medido.
   Entra porque el número es correcto, pero la justificación del encargo era la
   contraria. **Si no la quieres, es una línea.**
2. **Ningún tope de prima abre la especulación**: el máximo es 1,93 % contra un listón
   de 3 %. La pared no está en el tope.
3. **`computer_resale_value` sigue llamándose `SPECULATION`** y por eso sigue cerrada
   por un listón pensado para otra vía.
