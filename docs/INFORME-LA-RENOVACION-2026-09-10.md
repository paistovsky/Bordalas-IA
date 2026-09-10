# La renovación — informe

**Rama:** `liquidez/renovar-en-la-ventana` (desde `main` en `a2d1655`)
**Fecha:** 10/09/2026
**Verja:** 100/100 en verde (99 + 1 guardia nueva con 26 pruebas)
**Push:** NO.
**Escrituras contra Biwenger:** **ninguna**. La renovación está codificada,
probada y **apagada** (`RENOVACION_EN_VIVO = False`). La puja de 12.217.000 por
Aubameyang, sin tocar.

---

## 0. Antes que nada: el desfase de una hora ESTÁ CONFIRMADO

Y el cron nuevo tampoco entra en la ventana. Esto va primero porque cambia la
lectura de todo lo demás.

### La hora del reset, medida sobre el histórico

Sobre las 85 fotos de producción del 11 al 17/08, con los sellos de tiempo **del
propio Biwenger** (`created` y `until`, no cálculos nuestros):

```
OFERTAS DEL COMPUTER — caducidad          OFERTAS ENTRANTES — nacimiento
   07:00   57                                07:03   13
   07:16    1                                07:04   23
   07:46    1                                07:05    7
   08:31    2                                07:07    4
   otras    4                                07:09    7
```

Y día a día, la primera creación de cada mañana:

```
   11/08 (mar) 07:03:27      15/08 (sáb) 07:04:32
   12/08 (mié) 07:07:49      16/08 (dom) 07:05:42
   13/08 (jue) 07:04:40      17/08 (lun) 07:09:25
   14/08 (vie) 07:04:07

   mínimo 07:03 · mediana 07:04 · máximo 07:09 · 7 días seguidos
```

**El reset se ejecuta a las 07:00 de Madrid, clavado, y la tanda nueva aparece
entre 3 y 9 minutos después. No varía por día de la semana.** La letra pequeña
de Biwenger («entre las 5:00 y las 7:00») es genérica: en esta liga es el
extremo superior.

Esto **no** es un artefacto nuestro: `computer_cycle_hours: 24.0` no interviene:
son las marcas de tiempo que devuelve la API.

### El desfase: confirmado

El ciclo de hoy trae `timestamp: 2026-09-10T05:52:22Z`. El cron externo estaba
en `45,52 6 * * *` con etiqueta Europe/Madrid. Las tres lecturas posibles:

```
   interpretado como CEST (UTC+2)  ->  dispararía 04:52 UTC     ✗
   interpretado como CET  (UTC+1)  ->  dispararía 05:52 UTC     ✓ ES ESTA
   interpretado como UTC           ->  dispararía 06:52 UTC     ✗
```

**Coincide el minuto y coincide la hora: cron-job.org está aplicando CET, sin
horario de verano.** Ese trabajo se ejecutó a las **07:52 de Madrid — 52 minutos
DESPUÉS del reset**, no ocho antes.

Descarto que fuera el cron interno: `7 * * * *` habría dado 05:07 UTC, no 05:52.
Y la foto anterior (dashboard a las 06:33 Madrid = 04:33 UTC) sí encaja con el
interno de las 04:07 UTC más el tiempo de ciclo.

> **Pepe no ha entrado nunca en la ventana de la subasta.** Ha llegado siempre
> tarde. Eso explica por sí solo buena parte de las semanas sin pujar.

**Aviso de honestidad:** es **una** observación. El minuto coincidente (52) es
una señal fuerte, pero n=1. La comprobación barata es mirar mañana a qué hora
UTC arrancan las vueltas.

### El cron que hay puesto ahora tampoco entra

Me dices que ya están puestos y que no proponga crones. No propongo: doy la
aritmética, porque es medición.

```
   ventana real (Madrid)        06:45 — 07:00
   externo puesto               45,50 4 * * *   Europe/Madrid

   si cron-job.org sigue en CET  -> 05:45 / 05:50 Madrid   (1 h antes)
   si lo arreglaran a CEST       -> 04:45 / 04:50 Madrid   (2 h antes)
```

**En los dos casos cae fuera de la ventana.** Para entrar con el
comportamiento CET observado, esas dos entradas tendrían que decir **`45,52 5`**
(que ejecutadas como CET dan 06:45/06:52 de Madrid). El `15 7 * * *` sí cumple su
papel —ejecutado como CET son las 08:15 de Madrid, después del reset—.

Tú decides; la zona de silencio protege pase lo que pase con el reloj.

---

## 1. Cuándo nace la oferta renovada — la política se sostiene

Era la pregunta más importante del encargo. **Se puede contestar con el
histórico, sin escribir nada.**

De las **54 ofertas entrantes** del Computer en siete días, **las 54** nacieron
en la tanda de las 07:03–07:09. Ni una fuera. Y hay dos casos que lo cierran:

```
   jugador 41271   listado 15/08 06:42:42   oferta 15/08 07:04:32   -> 21,8 min
   jugador 38318   listado 15/08 05:51:35   oferta 15/08 07:04:32   -> 73,0 min
```

**Un listado creado 18 minutos antes del reset recibió su oferta en ese mismo
reset.** Así que renovar a las 06:52 no deja a nadie fuera de la tanda: la nueva
oferta llega unos doce minutos después.

**La política de renovar tarde se sostiene, y la medición la simplifica:**

- La oferta muere a las 07:00 **hagas lo que hagas**. Renovar a las 06:52 mata
  una opción a la que le quedan ocho minutos: **eso no cuesta nada**.
- Lo único que hay que proteger es que el jugador **siga listado** cuando pase el
  reset, porque la tanda solo mira a los listados.
- Y **un listado vive 48,0 h exactas** — 47 de 47 observaciones, ni una
  distinta —, o sea **dos ventanas**. En cada ventana solo hay que renovar lo que
  no llegaría a la siguiente.

Renovar lo demás no rompe nada, pero gasta una petición y no compra nada.

### Donde la medición contradice al encargo

**Un listado que caduca *entre* dos ventanas no lo salva ninguna de las dos.** Y
hoy eso no es teórico: de los ocho listados que piden renovación, **los ocho**
caducan antes de la ventana de mañana.

```
   Jonny           4,7 h    oferta viva 2.401.600
   Pablo Durán     6,5 h    oferta viva   431.100
   Manu Sánchez   10,9 h    oferta viva 1.600.100
   Jutglà         12,3 h    oferta viva 3.336.200
   Zubeldia       14,0 h    oferta viva 1.711.600
   Djené          14,7 h    oferta viva 1.953.800
   Pablo Ibáñez   16,3 h    oferta viva 2.294.500
   Dituro         21,4 h    oferta viva 2.439.000     (ventana a 21,9 h)
```

**No lo decido yo.** Renovarlos ahora mataría ofertas con 21 h de vida por
delante, que son justo la caja con la que se tapa la deuda contingente de
Aubameyang. Se publica en `renovacion.at_risk` y lo miras tú.

En régimen normal esto desaparece solo: al renovar en la ventana, el listado dura
48 h y siempre llega con 24 h de sobra a la siguiente. Solo pasa en la
transición — que es exactamente donde estamos — o cuando se pierde una ventana.

---

## 2. Un listado sin oferta ya está pendiente (0.2)

**Guardia dura puesta:** nunca se renueva un listado sin oferta viva.

Pero la justificación real no es la que decía el encargo. Medido: un listado de
18 minutos recibió su oferta igual. Así que renovar otra vez a las 06:52 **no**
impediría que naciera. Lo que hace es **gastar una petición y reiniciar un reloj
que no hacía falta reiniciar**. La guardia es correcta; el motivo es otro.

## 3. ¿Cuesta algo estar listado? (0.3)

**Sí, los rivales lo ven, y sí pueden pujar.** El tablero de adquisición lo
demuestra al revés: 23 de los 43 objetivos de hoy son `MERCADO_DE_RIVAL` — son
jugadores que otros managers han listado y que nosotros podemos ver y pujar.
Con los nuestros pasa lo mismo.

**Pero no perdemos el control.** Medido el 23/08: `type=purchase from=Pollo17
to=YO 977.000 pide 38072` — un rival pujó por nuestro jugador y aquello llegó
como una **oferta que hay que aceptar**, no como una venta consumada. De hecho le
contraofertamos 1.190.038.

**Lo que sí les damos es información:** qué jugadores estamos dispuestos a
soltar y a qué precio. Con 14 de 14 listados, esa información es casi nula
—estamos dispuestos a soltar a cualquiera— pero deja de serlo el día que
listemos solo a tres.

---

## 4. Cómo queda el ciclo, y cuántas peticiones añade

Orden dentro de la vuelta, y el orden importa:

```
   1. run_cycle        analiza, y COBRA lo que toque
   1-bis. RENOVACIÓN   <- nuevo, aquí
   2. BUY V10          la única compra del ciclo
   3-5. resto de acciones V10
```

Va **después de cobrar** (cobrar y renovar en la misma vuelta es perder el
dinero: hay guardia) y **antes** de la puerta de «una escritura por ciclo»,
porque renovar no es comprar — no mueve dinero ni ocupa fichas — y en la ventana
hay que renovar varios a la vez.

**Peticiones:** una por renovación, y solo en la ventana, o sea **una vez al
día**.

```
   hoy                          181 / día   (medido el 08/09)
   + renovar los 17 listados     17 / día
   ------------------------------------------
   total                        198 / día

   el bloqueo del 08/09 llegó a 1.536 / día  ->  queda un factor de 7,8
```

**El tope por ciclo es 17**, que no es un número a ojo: es el máximo de listados
que hemos tenido nunca a la vez (12/08). Y es un **corte duro en dos sitios** —
en la decisión y otra vez en el ejecutor, que corta aunque le mientan. Hay
guardia que le pasa 39 filas con tope 2 y comprueba que solo escribe dos veces.

---

## 5. Qué impide que renovar acabe vendiendo

Es lo que más te preocupaba, y a mí también.

**Primero, un hecho que ayuda:** renovar es `POST /market {"type": "sell"}` y
vender es `PUT /offers/{id}`. Son endpoints distintos. El peligro no es que un
parámetro se cuele: es que alguien, algún día, meta una rama de venta en el
camino de renovar.

**Las tres barreras:**

1. **Camino separado.** `src/actions/renovar_executor.py` es un fichero de
   ~200 líneas cuya única llamada de escritura es `list_player_for_sale`. No
   importa el ejecutor de ventas, ni el de ofertas, ni nada que pueda
   aceptarlas.

2. **`test_renovar_no_puede_vender`**, la guardia que pediste. Le pasa filas
   **manipuladas** —con `offer_id`, `accept: True`, `type: "accept_offer"`,
   `operation: "SELL"`, `action: "ACCEPT_RECOVERY_OFFER"`— a un cliente espía que
   apunta todo lo que se le llama y que **revienta** si alguien toca
   `accept_offer`, `place_bid`, `reject_offer`, `counter_offer`, `cancel_bid` o
   `save_lineup`. Comprueba que el conjunto de métodos llamados es exactamente
   `{list_player_for_sale}` y que ni siquiera le llegan argumentos de más.

3. **`test_el_modulo_de_renovar_no_conoce_la_venta`**: inspecciona el módulo ya
   cargado —no el texto del fichero, para que un `import` dentro de una función
   también cuente— y exige que no conozca ningún nombre de venta.

**Y el libro.** Cada renovación apunta jugador, precio, **importe de la oferta
que muere**, cuánta vida le quedaba, hora, y qué se espera que nazca
(`07:03-07:09 Madrid`). Si mañana esto sale mal, se reconstruye sin adivinar.

---

## 6. La zona de silencio

**Entre las 05:00 y las 07:00 de Madrid, Pepe no escribe.** La hora se calcula
en Madrid **con su horario de verano**, reutilizando `madrid_offset_hours`, que
existe desde el 16/08 justo por este error — el mismo código imprimía las 05:00
en el PC y las 07:00 en Actions. Un dato, un nombre: se importa, no se copia.

**La excepción, y por qué no es una trampa.** El trabajo de la ventana cae
dentro de la franja a propósito. Si el silencio lo tapara, no habría subasta
nunca. Lo que distingue no es la hora: es **quién dispara**.

```
   schedule (cron de GitHub)      dentro de la franja solo por accidente  -> CALLA
   workflow_dispatch / manual     está ahí porque alguien la puso ahí     -> ESCRIBE
   origen desconocido                                                     -> CALLA
```

Es la única capa que no depende de que un reloj ajeno se porte bien. Con el cron
interno en `7 0-2,7-23`, una vuelta de las 02:07 UTC que llegue con dos horas de
retraso cae en la franja — y se calla.

**Se ve en pantalla:** `silencio.blocked.actions` dice qué se quedó sin hacer.
Una barandilla que frena en silencio es indistinguible de una avería.

**Y sirve para medir:** cada vuelta dentro de la franja publica
`reset_observation` con si los precios ya habían cambiado. En una semana hay hora
exacta del reset sin gastar una petición.

Un apunte: al escribirla, la función devolvía silencio SIEMPRE porque le quitaba
la zona horaria a `madrid_offset_hours`, que la exige. Cayó del lado seguro,
pero era una avería muda. Arreglado y con guardia que compara verano contra
invierno.

---

## 7. Lo de esta noche (Bloque 3)

**No he renovado nada a mano.** Está codificado, probado y apagado.

En la foto de las **09:04** los ocho listados **todavía tienen oferta viva**
(21,9 h), así que a esa hora aún no habías renovado. Lo que hay que comprobar
mañana:

1. Que los ocho aparezcan **listados y SIN oferta viva** antes de las 07:00.
2. Que después de las 07:04 tengan **oferta nueva**, y de cuánto.
3. Que Kiko Femenía haya desaparecido del libro con +1.159.000 en el saldo.
4. **Y una medición que sale gratis:** el listado de **Pablo Durán** caduca en
   6,5 h y su oferta tiene 45,9 h de vida. Es el único caso natural que hay para
   saber **si una oferta sobrevive a la muerte de su listado**. No lo sabemos, y
   mañana se ve solo.

---

## 8. Las cuatro reglas nuevas

En `docs/DOCTRINA.md`, con su origen: **24** la línea es el minuto de la jornada
(y el T−6 h es nuestro, no de Biwenger, y se publican por separado) · **25** una
oferta viva es una opción gratis · **26** renovar mata la oferta viva, así que se
renueva tarde · **27** la liquidez se mantiene, no se busca.

---

## 9. Lo que entra en el commit

```
 nuevo   src/analysis/zona_de_silencio.py               la franja, en Madrid
 nuevo   src/analysis/renovar_ofertas.py                qué renovar y qué no
 nuevo   src/actions/renovar_executor.py                el camino que solo lista
 nuevo   src/analysis/test_renovar_en_la_ventana_v1.py  26 guardias
 modif   src/v10_full_autonomous_live.py                el enganche, APAGADO
 modif   src/telemetry/dashboard_state.py               silencio + renovación
 modif   docs/DOCTRINA.md                               reglas 24-27
 modif   scripts/run_validation_gate.py                 la guardia registrada
 nuevo   docs/INFORME-LA-RENOVACION-2026-09-10.md
```

Sin `git add -A`: `Claude outputs/` es tuya y no se versiona.

---

## 10. Lo que NO hice, y por qué

- **No he escrito nada contra Biwenger.** `RENOVACION_EN_VIVO = False`. Para
  armarlo es esa línea y nada más, en `src/v10_full_autonomous_live.py`.
- **No he tocado la puja de Aubameyang.**
- **No he renovado a mano los ocho listados** aunque siete se mueran hoy: me
  dijiste que no, y además mataría las ofertas con las que se tapa el agujero de
  mañana. Están publicados en `at_risk`.
- **No he propuesto crones**, como pediste. He dado la aritmética de los que hay
  puestos porque es medición, no propuesta.
- **No he tocado el workflow.**
- **No he salido de `main`**: las ramas `calibracion/el-credito-es-fijo`,
  `solvencia/ver-las-pujas-del-dueno` y `pujas/encender-la-cartera` **siguen sin
  fusionar**, así que esta rama no las lleva. Lo digo porque la regla 1 lo pedía.
  Tampoco tengo el commit `a90aadc` del cron interno: no está en este repo.
- **Ningún umbral se ha movido.**
- **No he hecho push.**

---

## 11. Lo primero que hay que mirar mañana

1. **A qué hora UTC arrancan las vueltas.** Si la de la ventana vuelve a caer en
   05:5x UTC, el desfase de CET queda confirmado con dos observaciones.
2. Que el dashboard publique `silencio` y `renovacion` con sentido.
3. Los cuatro puntos del bloque 3, arriba.
