# La línea de crédito no se deduce, se sabe — informe

**Rama:** `calibracion/el-credito-es-fijo` (desde `main` en `a2d1655`)
**Fecha:** 10/09/2026
**Verja:** 100/100 en verde (99 + 1 guardia nueva con 13 pruebas)
**Push:** NO.
**Escrituras contra Biwenger:** ninguna. La puja viva de 12.217.000 sigue puesta
y sin tocar.

---

## 1. Las tres vías, concordando sobre el caso real

La foto de las 09:04 es la que tengo delante — la bajé del Worker y es
exactamente la del incidente. Con el arreglo puesto:

```
A. TABLÓN       Aubameyang: has_live_bid true, live_bid 12.217.000
B. RESTA        3.315.383 + 12.510.000 − 3.608.383 = 12.217.000
C. DIFERENCIA   15.825.383 (07:52) − 3.608.383 (09:04) = 12.217.000
                mismo saldo en las dos, sin reset por medio
```

**Las tres dan 12.217.000.** Antes la B daba cero y mandaba la conservadora por
suerte, no por diseño. Hay guardia con las tres dentro.

Y la calibración, sobre la foto envenenada:

```
ratio         0,25            (antes: 0,005855)
headroom      12.510.000      (antes: 293.000)
COMPROMETIDO  12.217.000      (antes: no se publicaba: se anulaba solo)
anomalía      None
```

### Lo que cambia en el código

```
antes:   headroom = maximumBid − saldo
         ratio    = headroom / valor_plantilla

ahora:   headroom     = valor_plantilla // 4      (0,25 medido)
         comprometido = saldo + headroom − maximumBid
```

Mismo álgebra, despejado por el lado que no se contamina. El número vive en
**un solo sitio**: `src/analysis/linea_de_credito.py`.

### La capacidad de la liga, recuperada al euro

| manager | 07:52 (antes de la puja) | ahora, con el arreglo | |
|---|---:|---:|---|
| Pollo17 | 9.413.772 | **13.572.672** | sube: vendió |
| Luismi_Haz | 23.342.594 | **23.342.594** | clavado |
| Mex | 16.120.800 | **16.120.800** | clavado |
| DiosMande | 14.860.283 | **14.860.283** | clavado |
| Prinzipote | 16.068.172 | **16.068.172** | clavado |
| Manzagool | 11.330.280 | **11.330.280** | clavado |

Los cinco que no se movieron vuelven **al euro** a su valor de las 07:52,
partiendo de la foto envenenada. Eso no es una comprobación mía: es la prueba de
que la fórmula nueva reconstruye lo que había antes de que la puja lo rompiera.

La guardia no se conforma con "ninguno baja" — eso se cumpliría también
congelándolos a todos. Exige que **los cinco quietos salgan idénticos** y que
**Pollo suba**, porque Pollo sí se movió.

## 2. Si algún día el ratio real cambia

`comprometido` negativo es imposible. Si sale negativo, el 0,25 ya no vale:

```
ANOMALIA: la cuenta da -X EUR comprometidos, que es imposible.
La linea medida (0.2500) ya no cuadra con esta foto.
Se sigue con 0.2500 y se publica el aviso: un ratio nuevo no se
adopta en caliente.
```

Se publica `anomaly.implied_ratio` — lo que tendría que valer la línea para que
esa foto cuadrase — **para poder volver a medirla, no para usarla**. Adoptar en
caliente un ratio deducido de una foto rara es exactamente lo que arruinó a la
liga. Hay guardia.

## 3. Dónde se usa `rival_intelligence`, y si nos contamos como rival

**Dónde se usa:**

| consumidor | para qué |
|---|---|
| `acquisition_board` | monta el tablero de objetivos; pasa la lista al modelo de pujas |
| `rival_bid_model.build_bid_model` | quién puja, con qué frecuencia y hasta dónde |
| `acquisition_valuation` | valora cada objetivo contando la competencia |
| `intelligent_bid_engine` | cuánto ofrecer |
| `competitive_transaction_engine` / `competitive_live_executor` | negociación con managers |
| `dashboard_state` | la pantalla |

**¿Nos contamos a nosotros mismos? No, y lo he comprobado corriendo el modelo
sobre la foto de hoy:**

```
modelo de pujas CON nuestro id  -> 6 rivales
   Pollo17, Luismi_Haz, Mex, DiosMande, Prinzipote, Manzagool
modelo de pujas SIN nuestro id  -> 7 rivales
   ... + Pepe Bordalás
```

`build_bid_model` nos excluye por `user_id` ([rival_bid_model.py:440-450](src/analysis/rival_bid_model.py#L440-L450)),
y `own_user_id` **sí llega**: se lo pasa `acquisition_board` con
`current_user_id`. Así que **el 76 % de subastas disputadas no está
contaminado por esta vía**, y no hace falta tocar nada ahí.

**Sobre el `id: None` que viste:** las filas publicadas **no tienen** una clave
`id` — llevan `user_id` (14145555, 14175949, …). Quien lo lee, lo lee bien
(`manager.get("user_id") or manager.get("id")`). La identidad está y funciona.
Aparecemos en la lista publicada **a propósito**, marcados con `is_us: true`:
es la pantalla, no el conteo de competidores.

**Dos cosas que sí he encontrado mirando, y que NO he tocado:**

1. **`calibrate_premium_curve(managers, …)` recibe la lista entera, con nosotros
   dentro** ([rival_bid_model.py:517](src/analysis/rival_bid_model.py#L517)). Es
   la curva de "qué prima paga esta liga", y nuestras propias pujas la
   alimentan. No he podido medir cuánto pesa sin reconstruir la inteligencia
   rival (llamadas a Biwenger), así que **digo que existe y no digo cuánto**.
   Arreglarlo movería una curva calibrada, y eso no me lo has pedido.

2. **El desfase de 100.000 en nuestro saldo.** No es de la lista de rivales: el
   `balance` de cada manager está **reconstruido del libro** (reparto inicial +
   ingresos − gastos + abono de jornada), porque Biwenger no publica el saldo de
   nadie más. Para nosotros esa reconstrucción se queda 100.000 corta frente al
   oficial, y el propio motor ya lo sabe: `ledger_status: REVIEW_REQUIRED`.

   Con el arreglo, **nuestra capacidad publicada ya no hereda ese error**: pasa
   a ser el `maximumBid` oficial (`maximum_bid_source: OFICIAL_BIWENGER`), con
   el bruto al lado para ver cuánto nos quita la puja. El `balance` de la fila
   sigue siendo el reconstruido; eso es harina de otro costal y no lo toco sin
   que me lo digas.

## 4. Qué pasa cuando Pepe tiene cuatro pujas puestas

Era el motivo urgente del encargo. Con la cartera colocando pujas en la ventana
del reset, el `maximumBid` propio baja y —antes— el ratio se hundía justo cuando
hay que decidir cuánto ofrecer.

| manager | sin pujas | con 1 puja de 12,2 M | con 4 pujas de 2 M |
|---|---:|---:|---:|
| Pollo17 | 13.572.672 | 13.572.672 | 13.572.672 |
| Luismi_Haz | 23.342.594 | 23.342.594 | 23.342.594 |
| Mex | 16.120.800 | 16.120.800 | 16.120.800 |
| DiosMande | 14.860.283 | 14.860.283 | 14.860.283 |
| Prinzipote | 16.068.172 | 16.068.172 | 16.068.172 |
| Manzagool | 11.330.280 | 11.330.280 | 11.330.280 |

**No se mueve ni un euro.** Con el código viejo, esa misma columna de "1 puja"
era:

```
Pollo17           0        Luismi_Haz  2.880.828      Mex        3.483.871
DiosMande 4.410.890        Prinzipote  2.815.998      Manzagool          0
```

La capacidad de cada rival sale ahora **de su saldo y su plantilla**, y de nada
más. Hay guardia para el caso de una puja y para el de cuatro.

## 5. Pollo se ha movido (anotado, no perseguido)

Entre las 07:52 y las 09:04:

```
saldo      -12.826.228  ->  -7.332.328     (+5.493.900)
plantilla   88.960.000  ->  83.620.000     (-5.340.000)
```

Ha vendido unos **5,34 M** de plantilla y el saldo le sube **5,49 M**: unos
154.000 por encima del valor de mercado, un **2,9 %** de prima, en línea con lo
que paga el Computer. La cifra hay que cogerla con pinzas — el saldo de un rival
está **reconstruido del libro**, no publicado por Biwenger — pero la dirección
es sólida: entre las dos fotos no hubo reset, así que la caída de plantilla no
puede ser un cambio de precios. Su capacidad estimada sube de 9.413.772 a
13.572.672. Sigue con 7,3 M de deuda.

Anotado aquí. No lo he perseguido.

## 6. La verja

```
Los 100 en verde. Se puede subir.
```

`src/analysis/test_linea_de_credito_v1.py`, **13 pruebas**, con
**`test_una_puja_del_dueno_no_arruina_a_la_liga`** de titular: las dos fotos
reales de hoy empotradas como números, ratio 0,25, comprometido 12.217.000, y
ningún rival por debajo de su capacidad de las 07:52.

Las demás protegen: que Pollo suba porque vendió (y no por nosotros) · que el
ratio no se deduzca de `maximumBid` · que la capacidad de un rival no dependa de
una puja nuestra · ni de cuatro · las tres vías concordando · los 12 estados de
la medición del 09/09 · que lo imposible se avise y no se adopte · que nuestro
`maximum_bid` sea el oficial · que nadie salga a cero teniendo plantilla · la
forma estable · y que nada lance.

**Regla 24**: si las tablas se vacían —o si las dos fotos dejan de llevarse el
importe de la puja— la guardia falla en vez de pasar de largo.

**Ninguna lee estado externo**: las dos fotos son números en el fichero.

## 7. Lo que entra en el commit

```
 nuevo    src/analysis/linea_de_credito.py            el número, en un solo sitio
 nuevo    src/analysis/test_linea_de_credito_v1.py    13 guardias
 modif    src/analysis/rival_intelligence_engine.py   el despeje bueno
 modif    scripts/run_validation_gate.py              la guardia registrada
 nuevo    docs/INFORME-EL-CREDITO-ES-FIJO-2026-09-10.md
```

**Sin `git add -A`.** `Claude outputs/` es tuya y no se versiona: he añadido a
mano los cinco ficheros.

## 8. Lo que NO he hecho, y por qué

- **No he tocado la puja de Aubameyang.** Sigue viva, 12.217.000, se resuelve
  mañana a las 07:00. Ninguna escritura contra Biwenger, de ningún tipo.
- **No he tocado la curva de prima**, aunque nos incluye. Movería un número
  calibrado y no me lo has pedido; queda dicho arriba para que lo decidas.
- **No he tocado el `balance` reconstruido** de la lista de managers ni el
  desfase de 100.000: me dijiste que dijera dónde se usa antes de tocar, y lo
  que he tocado es solo la **capacidad**, que era lo roto.
- **No he tocado el conteo de competidores**: ya nos excluía, y comprobarlo era
  parte del encargo. Cambiarlo habría sido romper algo que funciona.
- **Ningún umbral se ha movido.** El 0,25 no es un umbral nuevo: es el que
  producción ya usaba cuando no había pujas vivas. Lo que cambia es que ahora no
  se puede envenenar.
- **No he tocado el workflow.**
- **No he unificado `LINEA_DE_CREDITO` con la copia de la rama
  `solvencia/ver-las-pujas-del-dueno`**, porque esa rama no está en `main` y no
  puedo importar de ella. Cuando la fusiones, su constante tiene que pasar a
  importarse de `linea_de_credito.py`: un dato, un nombre. Está escrito en la
  cabecera del módulo.
- **No he hecho push.**

## 9. Lo que hay que mirar mañana

1. Que la calibración publique `ratio: 0.25` y `committed: 12.217.000` mientras
   la puja siga viva.
2. Que `maximum_bid_source` diga `LINEA_MEDIDA` en los rivales y
   `OFICIAL_BIWENGER` en nuestra fila.
3. A las 07:00, cuando la puja se resuelva: que `committed` vuelva a cero solo,
   sin que nadie toque nada.
4. Si algún día aparece `anomaly` en la calibración: **no es para arreglarlo en
   caliente**, es para volver a medir la línea con fotos.
