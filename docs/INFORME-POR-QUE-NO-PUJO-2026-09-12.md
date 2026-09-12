# Por qué no pujó, y tres cosas más

**12/09/2026** · verja 111/111 · sin push

---

## 1. Por qué no pujó — y no fue ninguna de las cinco puertas

**No la llamaba nadie.**

```
$ grep -rn "la_rendija" src/ --include=*.py | grep -v test_
src/telemetry/dashboard_state.py:4544   <- la TELEMETRÍA. Y nada más.
```

Los módulos escritos, 24 guardias en verde, el estado publicado, el panel pintando
**EN VIVO** — y el único sitio del proyecto que importaba el carril era la pantalla
que lo dibuja. `en_vivo = True` era **la bandera del módulo**, no una prueba de que
se ejecutara.

Es mi omisión, y es la peor clase: **armar algo y no enchufarlo es peor que no
armarlo**, porque la pantalla dice que funciona. Ayer te dije «encendida» y lo que
estaba encendido era un interruptor que no iba a ningún sitio.

Arreglado: `src/actions/carril_executor.py`, llamado desde el ciclo **después de la
acción principal**, sin consumir `write_used`. Su única escritura es `place_bid` y
hay guardia que prohíbe las otras cuatro.

### Y sí: SILENCIO lo habría bloqueado igualmente

Confirmado, y era lo que sospechabas. `zona_de_silencio.permite_escribir` acepta un
`disparo` y tiene `DISPAROS_DELIBERADOS = {workflow_dispatch, repository_dispatch,
manual, ventana}`. **Mi `permiso()` lo llamaba sin el disparo**, así que los tiros
de las 04:45 y 04:50 —puestos dentro de la zona **a propósito**— se bloqueaban
igual que los del cron.

```
04:50 sin decir el disparo      ->  SILENCIO
04:50 disparo = schedule        ->  SILENCIO      (correcto: el cron no escribe)
04:50 disparo = ventana         ->  PASA
04:50 disparo = workflow_dispatch -> PASA
```

O sea: **dos fallos encadenados**, y el segundo habría aparecido en cuanto
arreglase el primero.

### Pero el bot SÍ compró hoy

En el reset de las 07:05, dos porteros:

| | precio | vale |
|---|---|---|
| Fortuño (POR) | 150.376 | 150.000 |
| Diego Conde (POR) | 240.601 | 240.000 |

**No fue el carril**: los dos están por debajo del suelo de 1 M (un +1,52 % sobre
150.000 son 2.250 €, que no pagan la ficha). Fue la ruta de siempre, casi con
seguridad la barandilla de portero.

### «PUJAS PUESTAS: ninguna · 2 sin resolver»

Son esas dos, y la casilla mezcla **dos fuentes con distinta edad**:

- **«ninguna»** = `committed`, el dinero comprometido **ahora**. Es 0 porque las
  dos pujas ya se resolvieron en el reset.
- **«2 sin resolver»** = las entradas marcadas `PENDING` en el libro de pujas, que
  **no se habían actualizado** con el resultado.

Las dos son correctas por separado y se contradicen juntas. Queda anotado; no lo he
tocado hoy porque el carril era lo urgente.

---

## 2. Alvarito: el número coincide, pero la coincidencia no prueba nada

**La reconstrucción NO le aplica jornadas anteriores a su entrada.** Entró el
**11/09 20:33** y no aparece en los `results` de ninguna de las cinco jornadas, así
que su `matchday` sale **0**. Eso no es suerte: es la consecuencia de que la caja
**lea** lo que el tablón dice que se pagó en vez de derivarlo de los puntos. Si lo
derivásemos, le habríamos pagado cinco jornadas que no jugó.

**Pero el 23.300.000 no está verificado, es aplicado.** La reconstrucción le da el
`SALDO_INICIAL` y luego publica ese mismo número: la coincidencia al euro que
notaste es **tautológica**, no una confirmación.

| | |
|---|---|
| caja | 23.300.000 ← **asumido**, no medido |
| plantilla | 28.390.000 |
| tope | 30.397.500 = 23.300.000 + 28.390.000/4 ✓ `quarterTeam` |
| compras/ventas en el tablón | **0** |

**Sobre si la plantilla se le descontó:** el modelo dice que no, y hay un argumento
—`newUsers: 12` coincide con el `distribution: 12` del `leagueReset`, y nuestro
propio plantel inicial no tiene `owner.price`, o sea que fue gratis—. Pero es una
**inferencia de los ajustes, no una medición**. Si a él se le hubiera descontado,
su caja real sería negativa y estaríamos sobrestimando su tope en 28,4 M.

**No se puede comprobar**: la liga tiene `settings.balance = "hidden"`. Lo único
que lo resolvería es verle hacer una operación y ver si el tablón cuadra. Con
30,4 M de tope estimado es el rival que más importa, así que **lo dejo marcado como
supuesto** y no como medido.

---

## 3. La competencia con ocho

| objetivo | precio | pueden | quiénes |
|---|---|---|---|
| Berenguer | 3.180.000 | **7 de 7** | todos |
| Cáceres, Sotelo, Torró, P. Martínez | 1,2–1,6 M | **7 de 7** | todos |
| Cancelo | 6.260.000 | 7 de 7 | todos |
| Aubameyang | 12.170.000 | 6 | todos menos Manzagool |
| Fermín | 14.510.000 | 4 | Luismi, Mex, Prinzipote, **Alvarito** |

**Alvarito puede pagar absolutamente todo lo que hay en el mercado.** Con 30,4 M es
el único que llega a Fermín con holgura, y entra en los cuatro que pueden.

### Lo que me preguntas y no se puede estimar todavía

*«¿Cuánto sube la probabilidad de que una subasta sea disputada por un manager con
la plantilla a medio llenar y la caja intacta?»*

**No se puede, y prefiero decirlo.** El modelo de puja rival se calibra sobre el
**historial de pujas observadas** de cada manager, y Alvarito tiene **cero**:
`participation` y `never_bids` salen de subastas pasadas que él no ha jugado.

Cualquier número que te diera hoy saldría de suponer que se comporta como la media
de los otros siete —que llevan un mes y la plantilla llena—, y eso es justo lo
contrario de su situación. Sería una regla montada sobre n=0, que es aún peor que
n=1.

**Lo que sí se puede decir sin inventar nada:** tiene 15 jugadores de un tope de 25
y 23,3 M sin gastar, así que **estructuralmente** es el que más incentivo tiene
para pujar por todo. Se mide en cuanto haga la primera puja y el tablón la
registre.

---

## 4. Los dos ciclos rojos

Confirmado, y era eso:

```
#1499  11/09 14:10  6b104cb  failure
#1500  11/09 17:35  6b104cb  failure
#1501  11/09 17:39  ab0c4ce  success   <- el commit del arreglo
```

Los dos sobre `6b104cb`, que es **anterior** a `ab0c4ce` («las guardias de
peticiones dicen en qué fase miden»). Y el primero que corre **con** el arreglo,
cuatro minutos después, pasa. No hubo otra cosa.

---

## Un rojo falso que encontré por el camino, y que importa

El cuadre de la caja estaba en **ROJO por 140.977 €** — y **la reconstrucción era
correcta**:

```
reconstruida   4.333.406
saldo REAL     4.333.406   <- pedido a la API ahora mismo
contra el que comparaba   4.474.383   <- de la FOTO
```

Entre la foto y ahora habían entrado las dos compras del reset (390.977) y una
racha diaria (250.000): `390.977 − 250.000 = 140.977`, clavado.

**Un rojo falso gasta la confianza igual que un verde falso, y peor: enseña a no
mirar la alarma.** Arreglado — el saldo se pide fresco, y si no se puede pedir se
manda `None` para que el cuadre diga «no se sabe» en vez de compararse contra algo
caduco.

---

## El arreglo pendiente: margen ≥ 1 %

Hecho. El filtro pasa de `> 0` a `≥ suelo`:

```
Robbie Ure  +0,49 %   ->   FUERA   (ayer entraba)
```

Y la guardia comprueba también que su margen **sigue siendo positivo** — si dejara
de serlo, estaría probando otra cosa.

---

## Guardias

`test_la_rendija_v1` — **27/27**. Las tres nuevas: que el ciclo llama al carril y
que el carril sólo puja, que el disparo deliberado viaja hasta la zona de silencio,
y que el filtro es el suelo y no el cero.

---

## Estado

- Verja: **111/111**
- Cuadre: **verde** (4.333.406, al euro)
- El carril: **cableado**, y ahora sí corre
- Rama `main`, **sin push**
