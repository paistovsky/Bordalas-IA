# INFORME — EL PRECIO NO SE PIERDE

**Fecha:** 26/09/2026 · **Rama:** `arreglo/el-precio-no-se-pierde`, desde `origin/main` (`80083658`)
**Interruptor:** `BORDALAS_EL_PRECIO_NO_SE_PIERDE`, **apagado**. El YAML no se ha tocado.

---

## En cinco líneas

1. **La cuenta está arreglada y vive en un solo sitio**
   (`src/analysis/el_precio_no_se_pierde.py`). Un fichaje para jugar cuesta lo que se deprecia en
   14 días, no su precio entero.
2. **Pero no es la palanca de 100-150 puntos que prometía la auditoría.** Reproducida sobre 10 días
   de fotos, la cuenta nueva ficha a **4** jugadores (99 puntos desde entonces, +7,26 M de valor);
   la vieja, también a **4** (92 puntos, +6,15 M). Comparten dos.
3. **La cuenta vieja no era "más dura" en todo.** Contaba los puntos de TODA la temporada de golpe
   contra el precio, más el 80 % del que sale. Aprobaba a los baratos y suspendía a los caros que
   suben. La nueva mide los dos lados con el mismo horizonte.
4. **Con la cuenta nueva solo pasa quien conserva su valor.** Con la depreciación conservadora
   medida, un jugador con el precio plano (−7,3 % en 14 días) necesita ~1,5 puntos por jornada por
   cada millón de precio, y sin dato de tendencia (−9,7 %), ~2. **Un Hinojo plano sigue sin pasar**, y es lo que dicen
   los números, no un fallo.
5. **Lo que sigue matando está detrás:** la mayoría de los que pasan con la cuenta nueva están en
   el mercado de un rival (Expósito, Enes Ünal, Camello), y **esa puerta la cerramos nosotros**,
   no Biwenger.

---

## BLOQUE 0 — LA CUENTA NUEVA

```
H = 14 dias (lo que se puede medir: 40,5 dias de historico dan ventanas de 14 con 7 de tendencia)

ganancia(H) = puntos por jornada x jornadas en H x 30.000 x (1 - margen) x confianza
coste(H)    = precio x depreciacion conservadora a 14 dias (por tramo de tendencia)
            + precio x coste de oportunidad diario x H

se ficha si ganancia(H) > coste(H)

y como el motor compara un valor contra el precio:
valor = precio - coste(H) + ganancia(H)          (valor > precio  <=>  ganancia > coste)
```

### 1. El horizonte: dos compras, dos cuentas, y no se mezclan

- **Esta cuenta es solo la de JUGAR** (mejora del once).
- **Revender** (especular, reventa al Computer, tener) ya valoraba el precio como lo que es: precio
  × (1 + ganancia esperada), a sus 1-3 días. **No se toca.**
- Para jugar, la ganancia y la depreciación crecen las dos con los días, así que **el horizonte
  casi se cancela**. Se usan 14 días a los dos lados.
  - Lo que se gana después de 14 días no se cuenta.
  - El sobreprecio de la puja se tiene que pagar dentro de esos 14 días.
  - Conservador a propósito.
- **Lo que se recupera vendiendo al que sale ya no se suma.** Vender es cambiar un activo por su
  dinero: ni gana ni pierde. En la cuenta vieja se sumaba porque el precio entero estaba restando.

### 2. El valor esperado al final: del histórico de precios, por tramo, conservador

Fuente: `data/autopilot/price_history.json` (40,5 días). Jugadores que juegan (≥ 5 de 7
partidos). Cambio de precio a 14 días según la tendencia de los 7 días anteriores (la tasa que la
sombra ya imprime, `rate_percent_per_day`):

| Tramo | Ventanas | Jugadores | Mediana | **Tercil bajo (se usa)** |
|---|---|---|---|---|
| BAJA (< −0,3 %/día) | 869 | 213 | −10,06 % | **−14,74 %** |
| PLANO | 285 | 146 | −1,80 % | **−7,34 %** |
| SUBE (> +0,3 %/día) | 792 | 198 | +8,75 % | **0** (nunca se cuenta la subida) |
| sin tramo | 1.946 | 281 | −1,89 % | **−9,70 %** |

- **El recorte:** se usa el tercil bajo, el valor que mejoran dos de cada tres compras, no la
  mediana. La subida nunca se cuenta.
- **La `n` de ventanas no es independiente** (se solapan cada 3 días); la de jugadores sí.

### 3. El coste de oportunidad: hoy 0, y es un dato

- La mejor vía alternativa medida es la cesta: **+0,12 % en toda su vida (n = 9)**. El carril
  pierde un 3,6 % y el tablero un 5,8 %. **El dinero parado no rinde: la tasa es 0.**
- Cuando haya cola, manda el **orden**: la cola coge primero al que más puntos gana por millón (ver
  el bloque 3).
- Si algún día hay una vía que rinda de verdad, su tasa entra por `oportunidad_diaria`.

### Dónde vivía la cuenta mala: dos sitios la calculaban, tres la heredaban

| # | Sitio | Qué hace |
|---|---|---|
| 1 | `player_value_engine.py`, `xi_upgrade_value`, la línea `maximo = justo × (1 − margin) × confianza + recovered_value` | **El origen.** Puntos de temporada entera contra el precio entero |
| 2 | `acquisition_valuation.py`, la vía de la ficha vacía (`xi_upgrade_value` con `replaced_points=0`, `recovered_value=0`) | Lo mismo, contra el hueco: todos los puntos del suplente contra todo su precio, aunque en esta liga el suplente no puntúa |
| 3 | `deployment.py:138`, `classify_operation` (la regla del 14/09) | **Hereda.** «Si ninguna vía de fichaje llega al precio, no es fichaje»: el once infravalorado convierte al que iba a jugar en una operación de reventa |
| 4 | `rival_bid_model.py:1160` (`NO_COMPENSA`) y `:236`/`:1290` (el 3 %) | **Hereda.** Compara ese valor con el precio, y a lo clasificado como reventa le exige el 3 % |
| 5 | `roster_expansion_shadow.py:190` (`INTENT_POR_EUROS`) | **Hereda.** Es el diagnóstico de la mezcla anterior |

**El arreglo está en uno solo:** `xi_upgrade_value` llama a `el_precio_no_se_pierde.valor_para_jugar`
cuando recibe el precio. Con eso se arreglan el 1, el 3, el 4 y el 5 sin tocar su código. El 2 tiene
su propia línea: **con el interruptor, la ficha vacía no se valora por puntos** (`SOLO_PUNTUAN_ONCE`),
porque un suplente que no entra en el once suma cero; si entra, ya lo cuenta la vía del once.

### El listón del 3 %: se queda donde está, y ahora solo mide lo que tiene que medir

- Con la cuenta nueva, quien añade puntos y conserva valor se clasifica como **fichaje**, y a un
  fichaje no se le exige el 3 %.
- **El 3 % se queda solo para las reventas.** Ahí los datos dicen que el listón no sobra: el carril
  pierde un 3,6 %, el tablero un 5,8 % y la cesta gana un 0,12 %.
- **No propongo cambiarlo.** Si acaso, para revender estaría corto.

---

## BLOQUE 1 — CONSTRUIDA

| Fichero | Qué |
|---|---|
| `src/analysis/el_precio_no_se_pierde.py` | **nuevo**: la cuenta, con las constantes medidas y apagada |
| `src/analysis/player_value_engine.py` | `xi_upgrade_value` recibe el precio y la tasa; con el interruptor, su valor es el de la cuenta nueva |
| `src/analysis/acquisition_valuation.py` | la tasa se calcula antes, para pasársela; la ficha vacía, `SOLO_PUNTUAN_ONCE` con el interruptor |
| `src/analysis/acquisition_board.py` | la fila lleva la cuenta; con el interruptor, la cola ordena por puntos por millón |
| `scripts/run_validation_gate.py` | la guardia en la verja, y **`--con BORDALAS_X`: la verja con un interruptor más**, sin envoltorio ni YAML |
| `src/analysis/test_el_precio_no_se_pierde_v1.py` | **guardia nueva**, 19 comprobaciones |
| `src/analysis/test_acquisition_wiring_v1.py` | se pone ella el interruptor apagado (ver el paso 0) |
| `src/analysis/test_ninguna_guardia_depende_del_entorno_v1.py` | **el paso 0 deja de estar vacío**: pasa los encendidos a la verja por `--con` |
| `config/paso_0.json` | el paso 0 de hoy, real, con 31 |

**La guardia** comprueba que un jugador que suma ~0,74 puntos por jornada y conserva su valor
(precio subiendo) **pasa con la cuenta nueva y no con la vieja**, y que `optimal_bid` deja de
decir `NO_COMPENSA`.

- **Muerde:** con el coste calculado sobre el precio entero, 6 rojas; ignorando el interruptor, 7.
- **Deja escrito, además,** que el mismo jugador con el precio **plano** no pasa.

---

## BLOQUE 2 — LA PRUEBA: ¿A QUIÉN HABRÍA FICHADO?

**Cómo:**

- **Fotos:** las 10 fotos diarias que hay en disco (12-17/08, 10/09, 12/09, 13/09, 19/09).
- **El tablero:** el de producción, con el interruptor puesto y quitado.
- **La caja:** la de cada día, con el reloj fijado a la hora de la foto.
- **Quién se ficha:** la primera fila `BID` de la cola.
- **Los puntos desde entonces:** reconstruidos partido a partido (`fitness` + calendario), hasta la J7.
- **El valor de hoy:** el panel de las 08:10.

| Cuenta | Día | A quién | Precio | Puntos desde entonces | Valor hoy | Beneficio |
|---|---|---|---|---|---|---|
| vieja | 12/08 | Manu Sánchez | 1.610.000 | 19 | 1.760.000 | +150.000 |
| vieja y nueva | 13/08 | Giménez | 380.000 | 23 | 3.440.000 | +3.060.000 |
| vieja | 15/08 | Tenaglia | 3.250.000 | 26 | 5.050.000 | +1.800.000 |
| vieja y nueva | 16/08 | Andrés Castrín | 1.030.000 | 24 | 2.170.000 | +1.140.000 |
| nueva | 15/08 | Miguel Sierra (reventa) | 770.000 | 39 | 4.380.000 | +3.610.000 |
| nueva | 12/09 | Larrubia | 4.790.000 | 13 | 4.240.000 | −550.000 |

```
                    fichajes   puntos desde entonces   valor hoy - precio
cuenta vieja            4             92                    +6.150.000
cuenta nueva            4             99                    +7.260.000
no fichar               0              0                            0
lo que hizo el bot   (auditoria)     11 de 298 puntos reconstruidos
lo que fichó el dueño                9.127 EUR por punto neto
```

**Veredicto:**

- **Fichar habría sido mejor que no fichar, con cualquiera de las dos cuentas.**
- **La nueva ficha un poco mejor que la vieja, pero n = 4 y comparten dos: la diferencia es ruido.**
- La nueva no ficha peor que no fichar, así que el arreglo no está mal. **Pero tampoco es por sí
  solo la diferencia entre 11 puntos y 100.**

**Las salvedades, que pesan:**

- **Agosto es inflación:** subieron casi todos los precios.
- **La reproducción usa los datos de hoy:** la titularidad es del tablero del 22/09 y la tasa, del
  informe del ojeador del 05/09. En las fotos de agosto, eso es saber quién acabó jugando. Infla a
  las dos cuentas por igual.
- **Por eso en la reproducción la cuenta vieja también ficha**, y en producción no fichó: en agosto
  faltaba la titularidad de casi todos (`SIN_PRONOSTICO`). La cuenta no era el único freno.
- **En septiembre, el régimen de hoy (4 fotos):** la vieja no ficha a nadie; la nueva, a Larrubia.

---

## BLOQUE 3 — EL FRENO CONTRA PASARSE

Cuántos pasan al día por la vía del once (valor > precio), sobre las mismas 10 fotos:

```
con el tercil (lo construido)    0-3 al dia  (n = 10 dias)
con la mediana (sensibilidad)    0-5 al dia
```

- **Dentro de los 4-5 del límite.** No hay nada mal en la cuenta por ese lado.
- **Todos los que pasan con el tercil tienen el precio subiendo:** la cuenta es conservadora de verdad.
- **La cola sigue siendo una cola:** una escritura por vuelta, y la primera es la que más puntos gana
  por millón (orden nuevo, solo con el interruptor).
- **No se ha tocado ningún tope:** `MAX_SINGLE_SPECULATION_PERCENT`, `MAX_SAFE_DEBT`, el suelo de
  cobro, `MIN_WIN_PROBABILITY`, `MAX_PROJECTED_DAILY_RATE`, las de `PUEDEN_ENCERRARLO`,
  `PRIMA_MAXIMA_DE_PUJA`, el margen del plazo y la cuota siguen igual. La caja sigue siendo el techo
  de cada puja.

---

## BLOQUE 4 — LA PUERTA DE LOS MANAGERS: ES NUESTRA

**14. Es una decisión nuestra, no una regla de Biwenger.**

- **La regla de la liga lo permite:** `userOffers: "market"` deja pujar por lo que un rival pone en
  el mercado.
- **El cliente de escritura ya lo sabe hacer:** `place_bid` acepta el vendedor (`seller_user_id`).
- **Quien la cierra es el tablero:** marca la fila (`acquisition_board.py:764-769`,
  `de_rival_sin_dinero`), la valora entera y **al final le cambia la decisión**
  (`acquisition_board.py:1406-1411`: `decision = MERCADO_DE_RIVAL`, `bid = 0`). Guarda lo que habría
  decidido en `would_be_decision`.

**15. Abrirla es un encargo:**

- dejar pasar como `BID` las filas de rival que pasan, detrás de un interruptor;
- que el ejecutor mande `seller_user_id`;
- **apuntar cuántas acepta el rival**, que hoy no se sabe: el tablón solo publica las aceptadas.

**Ojo:** son **los que el rival pone a la venta** (44 el 19/09), no sus plantillas. Los 8 de 11 del
mejor once de la liga solo entran si los publican.

---

## El interruptor, para el YAML (no lo he tocado)

```yaml
      # Apagado. EL PRECIO NO SE PIERDE: FICHAR ES CAMBIAR DINERO POR UN ACTIVO.
      #
      #   LO QUE PASABA. Un fichaje para jugar se valoraba por los puntos que
      #   añade y se comparaba con el precio ENTERO, como si pagar fuera
      #   perder. Hinojo: "vale 883.575 y cuesta 1.690.000. No hay margen".
      #
      #   LO QUE HACE. Para JUGAR (mejora del once), el coste es lo que el
      #   jugador se deprecia en 14 dias -tercil conservador del historico de
      #   precios, por tramo de tendencia- y la ganancia, sus puntos en esos
      #   14 dias a 30.000. La ficha vacia deja de valorarse por puntos (solo
      #   puntuan once). La cola ordena por puntos por millon. Revender no se
      #   toca; el 3 % se queda para revender.
      #
      #   MEDIDO sobre 10 fotos (12/08-19/09), reproduciendo el tablero:
      #     pasan por el once 0-3 al dia; fichados 4 (99 pts desde entonces,
      #     +7,26 M de valor) contra 4 de la cuenta vieja (92 pts, +6,15 M).
      #     Agosto infla todo y la reproduccion usa la titularidad de hoy.
      #
      #   PASO 0 HECHO: 26/09, verja con los 5 de produccion MAS este, y el
      #   paso 0 con todos los del inventario.
      #
      #   LO QUE NO ESTA MEDIDO Y HAY QUE VIGILAR:
      #     - Solo pasa quien sube de precio: con PLANO (-7,3 %) hacen falta
      #       ~1,5 puntos por jornada por millon; sin tramo (-9,7 %), ~2. Si el tercil resulta
      #       demasiado duro, la mediana (0-5 al dia) es el siguiente paso.
      #     - La tasa del precio sale del informe del ojeador, que no cubre a
      #       todos: los que no cubre van al tramo "sin tramo".
      #     - En produccion, n = 0.
      BORDALAS_EL_PRECIO_NO_SE_PIERDE: "1"
```

## Paso 0: y el paso 0 estaba vacío

```
verja con los 5 de produccion                              185/185   verja-el-precio.txt
verja con los 5 + BORDALAS_EL_PRECIO_NO_SE_PIERDE (--con)  185/185   verja-el-precio-seis.txt
paso 0, los 31 del inventario, DE VERDAD                   PASADO, 158 s   paso0-el-precio.txt
```

**La primera corrida con los seis salió ROJA:** `test_acquisition_wiring_v1`, 2 de 10.

- **Por qué:** esa guardia prueba el cableado de la puja con un Tenaglia que la cuenta vieja puja,
  porque suma sus puntos de toda la temporada. Con la cuenta nueva, sin tasa de precio (−9,7 %), no
  se puja.
- **Arreglo:** la guardia **se pone ella** el interruptor apagado, porque lo suyo es el cableado. La
  cuenta nueva tiene su propia guardia.
- **Encenderlo sin esto habría parado el ciclo.**

**Y lo más importante: el paso 0 no lo cazó, porque llevaba vacío desde el 22/09.**

- El paso 0 pone todos los interruptores y lanza la verja. Pero la verja prepara su propio entorno
  de producción y **quita todo `BORDALAS_*` que el YAML no enciende**
  (`los_interruptores_de_produccion.py`: «gana el YAML, se quita»).
- Así que "todos puestos" llegaba a las guardias como "solo los 5", y el paso 0 decía PASADO sin
  haber probado ninguno de los demás.
- **Arreglado:** el paso 0 le pasa ahora los encendidos a la verja por `--con`, la opción nueva.
- **Comprobado:** la llamada interna corre "con 31 interruptores".
- **Resultado:** este es el primer paso 0 real desde el 22/09, y pasa con los 31. **Incluye los
  otros 25 apagados:** ninguno tumba la verja.

**Consecuencia para otra rama:** el "paso 0 PASADO con los 31" que di para
`arreglo/la-reserva-mira-el-once` **no probaba su interruptor**. Hay que volver a correrlo allí con
`--con BORDALAS_LA_RESERVA_MIRA_EL_ONCE`, o con este paso 0 arreglado, antes de encenderlo. El del
catálogo sí quedó probado de verdad, porque se hizo con la lista ampliada.

---

## Lo que no hice, y por qué

- **Ni una petición a Biwenger.** Todo sale de fotos y libros en disco.
- **No encendí el interruptor ni toqué el YAML.**
- **No cambié el 3 %:** los datos de las reventas no lo piden.
- **No abrí la puerta de los managers:** el encargo solo preguntaba.
- **No usé la mediana** aunque deja pasar más: el encargo pedía conservador. Queda como el siguiente
  paso si el tercil resulta demasiado duro.
- **No toqué** las vías que escriben, el Position Manager, el YAML ni ninguna constante de la lista.
- **No empujé.**
