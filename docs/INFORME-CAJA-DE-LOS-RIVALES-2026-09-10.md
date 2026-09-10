# La caja de los rivales, a producción

**10/09/2026** · verja 110/110 · sin push

---

## El fallo, y los dos que había

Tu prueba era buena: 4,37 M en pantalla contra **4.474.383** reales. Cien mil
exactos. Pero al medirlo salieron **dos** fallos, no uno:

| | de más / de menos | quién lo delató |
|---|---|---|
| No se pagaba el **premio por puesto** | −100.000 (nuestro 5º de la J2) | tu observación |
| Se pagaba la **jornada partida** que la liga ignora | +870.000 | el cuadre contra el saldo real |

El segundo sólo aparece si comparas contra el saldo real. `apply_matchday_bonus`
derivaba `puntos × 30.000` y los puntos publicados **ya excluyen** la J1 ignorada,
así que los dos errores se compensaban en parte: en pantalla se veían 100.000
cuando por dentro había 970.000 mal repartidos.

Ahora la caja no deriva nada: **lee lo que el tablón dice que se pagó**, evento a
evento, con el premio incluido.

---

## 1-2. La fuente, y sin estado

`src/analysis/caja_de_la_liga.py`. Función pura de la lista de eventos:

```
caja = 23.300.000 + jornada (leída) + ventas + dailyStreak − compras
```

Se replica desde el `leagueReset` **en cada vuelta**. 241 eventos, milisegundos.
No hay acumulado ni libro en `data/`, por lo que dijiste: ese libro vive en una
caché de CI que puede retroceder, y reconstruido entero un evento perdido **se
ve**, mientras que acumulado se hereda.

`bettingPool` queda fuera con motivo escrito: son quinielas `global: true` de todo
Biwenger y el premio es en **créditos** de la app.

## 3. La comprobación permanente

Cada ciclo publica `cash_check`: nuestra caja reconstruida contra el saldo real de
la API. Hoy dice *«La caja reconstruida cuadra con el saldo real (4.474.383 EUR)»*.
Si se separan un euro, salen las dos cifras, la diferencia y la frase que importa:
**si el método falla con el nuestro, la caja de los seis rivales tampoco vale.**

Es la única auditoría posible: la liga tiene `settings.balance = "hidden"`.

## 4. Nada de respaldos

Sin reconstrucción, `balance = None`, `cash_source = "SIN_DATO"`, y **`net_worth` y
`maximum_bid` también pasan a `None`**. Ese último detalle era el peligroso:
`safe_int(None)` daba 0, y un manager sin caja habría salido con PATRIMONIO = su
plantilla entera y TOPE = un cuarto de ella, con la misma cara que un número
medido. Doctrina 36.

## 5. Lo que cuelga

`PATRIMONIO`, `TOPE` (`quarterTeam`), `PUJA %` y `AMENAZA` se recalculan solos
porque todos parten de `balance`.

**La amenaza por jugador ya usaba el tope real** — `rival_bid_model.py:588` filtra
`rival["capacity"] >= precio`, y `capacity` es `maximum_bid`. No hacía falta
tocarla: se corrige sola al corregirse la caja. La AMENAZA de la clasificación es
otra cosa (un score relativo de liga) y también toma `maximum_bid` como señal.

---

## 6. El antes y el después

**CAJA** — se mueve para los siete:

| | ANTES | AHORA | DIF |
|---|---|---|---|
| Pollo17 | −7.332.328 | −6.732.328 | +600.000 |
| **Pepe Bordalás** | **4.374.383** | **4.474.383** | **+100.000** |
| Luismi_Haz | −10.955.306 | −10.705.306 | +250.000 |
| Mex | 3.180.800 | 3.280.800 | +100.000 |
| DiosMande | 4.160.283 | 4.410.283 | +250.000 |
| Prinzipote | 284.772 | 1.134.772 | +850.000 |
| Manzagool | −1.162.220 | 837.780 | +2.000.000 |

Los +100.000 nuestros, clavados como dijiste. Manzagool se lleva 2 M: fue **7º en
las cuatro jornadas que pagaron**, 500.000 cada una.

**PATRIMONIO y TOPE:**

| | PATRIM ANTES | PATRIM AHORA | TOPE ANTES | TOPE AHORA |
|---|---|---|---|---|
| Pollo17 | 76.287.672 | 76.887.672 | 13.572.672 | 14.172.672 |
| Pepe Bordalás | 53.344.383 | 53.444.383 | 4.499.883 | 4.499.883 |
| Luismi_Haz | 72.854.694 | 73.104.694 | 9.997.194 | 10.247.194 |
| Mex | 54.940.800 | 55.040.800 | 16.120.800 | 16.220.800 |
| DiosMande | 46.960.283 | 47.210.283 | 14.860.283 | 15.110.283 |
| Prinzipote | 54.564.772 | 55.414.772 | 13.854.772 | 14.704.772 |
| Manzagool | 48.807.780 | 50.807.780 | 11.330.280 | 13.330.280 |

Nuestro TOPE no se mueve porque es el `maximumBid` **oficial** de Biwenger, no el
reconstruido — y eso es una tercera confirmación de que la caja está bien.

**El ranking de PATRIMONIO cambia, como esperabas:**

```
ANTES:  Pollo17 > Luismi_Haz > Mex > Prinzipote > Pepe > Manzagool > DiosMande
AHORA:  Pollo17 > Luismi_Haz > Prinzipote > Mex > Pepe > Manzagool > DiosMande
```

Prinzipote adelanta a Mex. Y **Manzagool sube de AMENAZA `VERY_LOW` a `LOW`**: sus
2 M de premios acumulados le cambian el escalón.

### Lo que NO ha pasado, y conviene que lo sepas

Esperabas que **Luismi_Haz pasara de +2,39 M a −10,71 M**. Sólo se mueve de
−10.955.306 a −10.705.306. Ya estaba profundamente en rojo **antes** de este
cambio.

El +2,39 M que ves en pantalla no lo produce el código actual: la foto publicada
tiene que ser anterior a alguno de los arreglos de estos días. Si al primer ciclo
sigue apareciendo +2,39 M, entonces hay un tercer camino que no he encontrado y
hay que volver sobre ello — pero no voy a decirte que lo he arreglado cuando lo
que mido no lo confirma.

---

## 7. Guardias

`src/analysis/test_la_caja_de_la_liga_v1.py` — **7/7**, con los eventos **reales**
del tablón copiados como fixture:

- `test_la_caja_reconstruida_cuadra_con_la_real`
- `test_el_premio_por_puesto_se_paga` — la J2 real, incluidos los **dos empatados a
  28 puntos que cobran distinto** (250.000 y 500.000): por eso el premio se resta,
  no se deduce de la posición
- `test_la_jornada_partida_no_paga`
- `test_la_jornada_ignorada_es_la_unica_sin_premio` — la confirmación cruzada
- `test_sin_eventos_no_hay_caja_y_se_dice` — ninguna pasa en vacío
- y dos más: el cuadre no aprueba con las manos vacías, y el motor publica el
  cuadre.

**Un aviso de mi propio proceso:** escribiendo el fixture le puse a la jornada
aplazada un `"short": "J1"` que el evento real **no tiene**, y la agrupación dejó
de funcionar. Lo cazó la guardia. Además destapó una fragilidad real —`short`
tenía prioridad sobre el nombre— que ya está corregida: manda el nombre.

---

## Estado

- Verja: **110/110**
- Cuadre en vivo: **cuadra al euro**
- Rama `main`, **sin push**
