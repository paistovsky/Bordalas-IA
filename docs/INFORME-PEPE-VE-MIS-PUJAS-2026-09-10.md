# Pepe ve mis pujas — informe

**Rama:** `solvencia/ver-las-pujas-del-dueno` (desde `main` en `a2d1655`)
**Fecha:** 10/09/2026
**Verja:** 100/100 en verde (99 + 1 guardia nueva con 22 pruebas)
**Push:** NO.
**Escrituras contra Biwenger:** ninguna. Ni una llamada.

---

## 1. De dónde sale `has_live_bid`, y por qué leyó `false`

**Sale de un campo real de la API, no lo inferimos.** La cadena entera:

```
snapshot["market"]["offers"]          <- GET /market, tal cual
   -> build_bid_exposure()            filtra por dirección: from == nosotros,
                                      type == "purchase", status waiting/pending
   -> exposicion["operations"]
   -> acquisition_board.py:286        puja_viva[player_id] = amount
   -> acquisition_board.py:726        "has_live_bid": player_id in puja_viva
```

Y **sí ve las pujas al Computer**, no solo las de manager a manager: el ejemplo
medido el 23/08 que vive en el código muestra `type=purchase from=YO to=null`,
donde `to=null` es el Computer. El 16/08, tras pujar por Iker Muñoz, el propio
contador subió a "pujas vivas 1".

**Por qué leyó `false` el 10/09.** No es un fallo del filtro: es que en la foto
de las 07:52 **no había ninguna oferta nuestra en `market.offers`**. Y lo
confirma la otra vía, que es independiente:

```
maximumBid publicado   15.825.383
saldo                   3.315.383
25 % de la plantilla   12.510.000
                       ----------
                        15.825.383   <- cuadra al euro, sin descontar nada
```

Si hubiera 11,8 M comprometidos, `maximumBid` tendría que valer 4.025.383.
Vale el número entero. **Las tres vías, sobre la foto de hoy, dicen cero.**

Así que o **la puja se puso después de las 07:52**, o **no registró**. No puedo
distinguirlo sin llamar a Biwenger, y esta noche no llamo. La forma de saberlo,
sin pedir nada nuevo: en la próxima foto, `maximum_bid` tiene que haber bajado
exactamente 11.800.000. Si no ha bajado, la puja no existe.

Esto también dice algo bueno: **el detector no se inventa la puja**. Publica lo
que hay.

## 2. La línea de crédito: se puede fijar, y es el 25 % exacto

El encargo avisaba de la trampa. La he medido en vez de asumirla, sobre las **85
fotos de producción del 12 al 17/08**, que dan **12 estados distintos**:

```
maximumBid == saldo + valor_plantilla/4 - pujas_comprometidas

   EXACTO AL EURO en los 12 de 12.
```

| foto | saldo | maximumBid | plantilla | comprometido | ratio |
|---|---:|---:|---:|---:|---:|
| 12/08 17:55 | −4.651.032 | 8.533.968 | 52.740.000 | 0 | 0,250000 |
| 13/08 20:40 | −4.651.032 | 7.203.968 | 52.980.000 | 1.390.000 | 0,250000 |
| 15/08 21:52 | 239.968 | 12.414.968 | 48.700.000 | 0 | 0,250000 |
| 16/08 17:02 | 239.968 | 11.924.968 | 48.660.000 | 480.000 | 0,250000 |
| 16/08 20:11 | 239.968 | 10.664.967 | 48.660.000 | 1.740.001 | 0,250000 |
| 16/08 20:47 | 239.968 | 9.278.966 | 48.660.000 | 3.126.002 | 0,250000 |
| 17/08 20:25 | −264.032 | 12.053.468 | 49.270.000 | 0 | 0,250000 |

*(la tabla completa, con las 12, está empotrada en la guardia)*

Aguanta con **saldo positivo y negativo**, con plantillas de **15, 16 y 17**
fichas, y con pujas de importe **con desvío** (1.740.001, 3.126.002) que no se
pueden explicar por un redondeo afortunado.

**Los listados cuentan.** En las 85 fotos había jugadores nuestros publicados en
el mercado — en la del 12/08, **los 17** —, siguen en `my_team`, y entran en la
cuenta **a precio de mercado, no al precio que pedimos**. Si no contaran, el
ratio no habría salido exacto ni una vez.

**Lo que NO puedo afirmar:** cómo redondea. Todos los precios de Biwenger son
múltiplos de 10.000, así que el 25 % siempre cae exacto y no hay ni un caso que
separe "hacia arriba" de "hacia abajo" de "al más cercano". Uso división entera
y lo digo en el código.

**Conclusión: la vía B vale para decidir.** No hace falta descartarla.

## 3. Las tres vías, y qué dice cada una hoy

`src/analysis/pujas_del_dueno.py`. No lee el mundo: todo se le pasa.

| vía | qué necesita | fortaleza | debilidad |
|---|---|---|---|
| **A. TABLÓN** | `market.offers` | viene de la API, no deduce nada | solo ve lo que Biwenger publique ahí — el 10/09 no vio nada |
| **B. RESTA** | saldo, maximumBid, valor de plantilla | funciona con una sola foto | depende de la línea de crédito (ya medida) |
| **C. DIFERENCIA** | dos fotos sin reset por medio | no necesita la línea de crédito | necesita la foto anterior, y se aparta si hubo reset o si el saldo se movió |

**Manda la más conservadora**, la que diga que hay más dinero comprometido.
Nunca la optimista: equivocarse por arriba cuesta no pujar un día; por abajo,
llegar a la jornada en rojo.

**Sobre la foto de hoy (10/09 07:52):**

```
TABLON      OK              0   El tablon no publica ninguna puja nuestra.
RESTA       OK              0   3.315.383 + 12.510.000 - 15.825.383 = 0
DIFERENCIA  --              0   (no había foto anterior guardada)
-> 0 EUR comprometidos, y las tres coinciden.
```

**Sobre el par real del 16/08, con el tablón cegado a propósito** (que es el
caso del 10/09):

```
TABLON      OK              0   ciego
RESTA       OK        480.000
DIFERENCIA  OK        480.000
-> 480.000 EUR según RESTA, y las vías no coinciden: manda la conservadora.
```

**Y con la puja de Aubameyang simulada** (maximumBid 11,8 M más bajo):

```
TABLON      OK              0
RESTA       OK     11.800.000
DIFERENCIA  OK     11.800.000
-> 11.800.000 EUR comprometidos.
```

Para que la vía C pueda hacerse siempre, cada vuelta escribe una línea en
`data/solvency/bitacora_del_saldo.jsonl`: `at`, saldo, `maximumBid`, valor de
plantilla y horas al reset.

**Una desviación del encargo, y por qué.** Pedías guardar `maximumBid` "en el
archivo diario". No cabe: `archivo_diario` guarda **informes de fuentes** —
scout, prensa — en carpetas nombradas por el `generated_at` del informe, con
poda a 60 días. Meter ahí una serie numérica de cuatro campos obligaría a
inventar un informe falso con su fecha de generación. Lo he puesto en un JSONL
propio, que es la misma información y no rompe la forma del archivo. Está
escrito en la cabecera del módulo para que se pueda discutir.

## 4. El reloj, con los tres números y la etiqueta nueva

Antes: `deficit = max(-balance, 0)`. Ahora lee **saldo efectivo**, y publica los
tres por separado:

```
saldo                     3.315.383
pujas comprometidas      11.800.000
saldo efectivo (peor caso)  -8.484.617
deficit                   8.484.617
estado: DEUDA_CONTINGENTE — "Deuda contingente: se deberá si se gana"
```

> *Saldo 3.315.383 EUR, pero hay 11.800.000 EUR comprometidos en pujas vivas: si
> se ganan, el saldo queda en −8.484.617 EUR. No es deuda todavía. NO se vende a
> ningún titular por una puja que puede no ganarse.*

`DEUDA_CONTINGENTE` solo aparece cuando **el saldo está en positivo** y el
agujero lo abre una puja. Con saldo negativo la deuda ya existe y el reloj usa
su escalera de siempre. Hay guardia para que no se confundan.

**Sin pujas comprometidas, el reloj dice exactamente lo que decía.** Guardia
también para eso: lo nuevo no puede alterar lo de antes.

### Sobre el riesgo que señalabas en el bloque 3

Lo dije anoche y toca corregir el matiz: **este reloj no puede hacer que Pepe
venda.** Lo he comprobado — el único consumidor de `solvency_clock` en todo el
código es `dashboard_state.py`. Es una pantalla, no una mano. Quien vende es el
camino de siempre (`ACCEPT_RECOVERY_OFFER`), que lee el **saldo real** y por
tanto **no ve la deuda contingente y no reacciona a ella**.

Es decir: el peligro de "Pepe se pone a vender para tapar un agujero que
todavía podemos no tener" **no existe con este cambio**, y no por prudencia mía
sino por cómo está montado. Lo que he hecho es dejarlo escrito donde se lee:

- `never_sell_starters: true` publicado en el plan.
- Un titular **no cuenta ni para sumar**: su oferta no entra en el cálculo de si
  el agujero está tapado. Taparlo con dinero que no se va a tocar sería mentir.
- La capacidad de pujar sale de `maximumBid` (que ya descuenta las pujas vivas),
  y la caja efectiva es la caja **menos lo comprometido**. Con 11,8 M puestos,
  la caja para repartir es **0**, no 497.307. Ningún umbral se mueve: cambia la
  entrada, que ya no miente.

## 5. El plan de los dos mundos, para mañana

Publicado en `solvency_clock.two_world_plan`, **antes del reset**:

```
SI SE GANA: faltan 8.484.617 EUR y las ofertas de los que no juegan
solo dan 2.113.500 EUR. NO HAY PLAN QUE CUBRA SIN TOCAR A UN TITULAR:
lo decide el dueño, no la máquina.
SI SE PIERDE: no hay nada que hacer.
```

Eso es exactamente lo que el 10/09 no dijo.

**Gratis en los dos mundos:** `Kiko Femenía, 1.159.000` — no juega, prima
+8,3 %, y su oferta caduca en el mismo reset en que se resuelve la puja. Se
pierde si no se cobra y no cuesta un punto en ninguno de los dos escenarios. Ya
estaba decidido (`ACCEPT_NOW`, `collecting_now: true`) y sigue estándolo.

### Una corrección de lo que te dije anoche

Te dije que hoy habían salido 9 ofertas por 19,5 M y ayer 5 por 30,6 M.
**Es al revés.** Lo he medido: una oferta del Computer vive **47,9 h** (54 de las
64 con fecha en las fotos del 11–17/08), se crea a las 05:03 UTC — 07:03 de
Madrid, justo tras el reset — y caduca en un reset dos días después. Así que
**la tanda nueva es la de caducidad más LEJANA**.

La de hoy es la de 47,1 h: **5 ofertas, 30.595.000**, de las que solo
**954.500 son de gente que no juega** (Cepeda y Pablo Durán) porque 21 M son de
Yamal. La de 19,5 M es la de ayer, y caduca mañana a las 07:00.

Esto empeora la estimación que te di: si mañana llega una tanda como la de hoy,
**no tapa los 8,5 M con banquillo**. Por eso el censo del punto 4.2 importa más
de lo que parecía.

## 6. Las dos mediciones de mañana

**4.1 — ¿Sobrevive una puja por debajo del precio nuevo?**
Apuntado el caso, sin inventar el resultado:

```
Aubameyang: puja 11.800.000 · precio hoy 12.170.000 · POR DEBAJO en 370.000
1 caso apuntado y ninguno resuelto: NO SE SABE si una puja por debajo
del precio nuevo sobrevive al reset.
```

**4.2 — El censo de la tanda nueva.** Una línea por reset, con cuántas, por
cuánto y cuántas son de no-titulares. Corre solo en cada ciclo (dedupe por día)
y también a mano:

```
python -m scripts.censo_del_reset
python -m scripts.censo_del_reset --jugador Aubameyang --puja 11800000
```

Con menos de 30 resets lo dice: *"hay cuenta, no medida"*.

## 7. La verja

```
Los 100 en verde. Se puede subir.
```

`src/analysis/test_pujas_del_dueno_v1.py`, **22 pruebas**, con los dos nombres
que pediste:

- **`test_el_dueno_pujo_y_pepe_no_se_entero`** — el par real del 16/08 como
  fixture: mismo saldo, `maximumBid` 480.000 más bajo. Comprueba primero que
  **antes** de pujar el reloj decía `SIN_DEUDA` (si no, no distinguiría nada), y
  después que publica 480.000 comprometidos, saldo efectivo −240.032 y estado
  `DEUDA_CONTINGENTE`.
- **`test_no_se_inventa_pujas_fantasma`** — las fotos sin ninguna puja: el
  detector tiene que publicar cero. Si la línea de crédito estuviera mal medida,
  esta se pone roja, que es lo que querías.

**Regla 24** en `test_hay_fotos_que_comprobar`: si la tabla se queda vacía, o se
queda sin fotos con puja, o sin fotos sin puja, **falla**.

**Las 12 fotos están empotradas como números**, no leídas de `data/`: cumple la
regla 23 y además las convierte en la medida permanente.

La guardia encontró un fallo real mientras la escribía: `por_el_tablon` con
basura que no fuera un diccionario **sí lanzaba**, contra la regla de la casa.
Arreglado.

## 8. Lo que entra en el commit

```
 nuevo    src/analysis/pujas_del_dueno.py           las tres vías + capacidad
 nuevo    src/analysis/test_pujas_del_dueno_v1.py   22 guardias
 nuevo    src/intelligence/bitacora_del_saldo.py    bitácora + censo + 4.1
 nuevo    scripts/censo_del_reset.py                la línea al día
 modif    src/analysis/solvency_clock.py            tres números, etiqueta, plan
 modif    src/telemetry/dashboard_state.py          detector, censo, publicación
 modif    scripts/que_pujaria_en_el_reset.py        caja efectiva
 modif    scripts/run_validation_gate.py            la guardia registrada
 nuevo    docs/INFORME-PEPE-VE-MIS-PUJAS-2026-09-10.md
```

**No he usado `git add -A`.** En el árbol hay una carpeta tuya sin versionar,
`Claude outputs/`, con el prompt de este encargo dentro. No es mía y no la meto
en un commit: he añadido a mano los nueve ficheros de arriba. `data/` está en
`.gitignore`, así que la bitácora y el censo no entran (producción los conserva
con el paso de *Restore/Prune state*).

## 9. Lo que NO he hecho, y por qué

- **No he vendido nada.** Kiko Femenía sigue como estaba: decidido antes, coste
  cero, `ACCEPT_NOW`.
- **Ninguna escritura contra Biwenger.** Ni una llamada, tampoco de lectura: la
  foto se baja del Worker de Cloudflare y las 85 fotos históricas ya estaban en
  disco.
- **No he tocado el workflow.**
- **Ningún umbral se ha movido.** Ni el listón, ni `MAX_SAFE_DEBT`, ni
  `MAX_SINGLE_SPECULATION_PERCENT`, ni `ACQUISITION_CASH_PERCENT`. Lo único que
  cambia es la **entrada** de la caja, que ahora resta lo comprometido.
- **No he metido la deuda contingente en los motores que venden.** Podría
  haberlo hecho pasándoles el saldo efectivo, y sería exactamente el fallo que
  señalabas: Pepe vendiendo por una puja que puede perder. Los motores siguen
  leyendo el saldo real.
- **No he tocado `has_live_bid` ni `build_bid_exposure`.** Funcionan; el
  problema no estaba ahí.
- **No he forzado la línea de crédito**: salió limpia, y si no hubiera salido lo
  habría dicho y me habría quedado con A y C.
- **No he hecho push.**

## 10. Lo que hay que mirar mañana

1. En la próxima foto, que `maximum_bid` haya bajado **11.800.000**. Si no ha
   bajado, tu puja no existe.
2. Que el reloj diga `DEUDA_CONTINGENTE` y publique los tres números.
3. A las 07:00: si la puja por debajo del precio sobrevivió, y qué trae la tanda
   nueva. Las dos quedan apuntadas solas.
4. Que el plan de los dos mundos siga diciendo en voz alta si no se puede tapar
   sin titulares.
