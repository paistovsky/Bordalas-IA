# El ojeador conectado — informe

**Rama:** `ojeador/conectar-el-pronostico` (desde `main` en `3bcfb39`)
**Fecha:** 15/09/2026
**Verja:** 141/141 en verde, exit 0, salida a fichero
**Push:** NO. **Interruptor:** APAGADO.
**Escrituras contra Biwenger:** ninguna. Ningún umbral tocado.

---

## 0. ¿El 89 % es un pronóstico o un espejo?

**No es un espejo.** Pero tampoco es un pronóstico *de la fuente*. Las dos cosas, y
la diferencia importa.

### Qué compara, con las dos fechas delante

```python
# accuracy.py:214 — al apuntar
"price_at_prediction": precio,          # el precio de HOY (seen_at)
"due_at": (momento + timedelta(days=horizonte)).isoformat()

# accuracy.py:301 — al puntuar
if vence is None or ahora < vence: continue      # no se toca hasta D+horizonte
precio_hoy = precios.get(player_id)               # el precio de AHORA
cambio = precio_hoy - partida
entrada["direction_hit"] = bool(dicho == real)
```

**D contra D+horizonte.** Hacia delante. No es circular.

### Pero lo que publica la fuente es el pasado — y está medido, no deducido

El propio `quote` de FutbolFantasy lo lleva escrito:

```
data-diferencia1=-10000, data-diferencia-pct1=-1.6949,
valor=580000, valor hace 1 d=590000
```

`magnitude_percent` **es el cambio de ayer**. Lo comprobé contra nuestra serie de
precios sobre el informe del 05/09, señales de horizonte 1 con movimiento ≥1 punto:

```
fuente            |lo que publica − el movimiento YA OCURRIDO|
FUTBOLFANTASY       0,000 pp   (n=95)
ANALITICA           0,025 pp   (n=97)
COMUNIATE           0,026 pp   (n=94)
COMUNIATE_PULSO    29,254 pp   (n=58)
```

Las tres buenas publican **el mismo hecho** —el cambio de precio de Biwenger— con
tres decimales de diferencia. **«542 de 543 con las tres fuentes de acuerdo» no es
un consenso de tres opiniones: son tres copias de un dato.** Y COMUNIATE_PULSO no
publica ese hecho: publica otra cosa.

### Entonces, ¿qué mide el 89 %? Si el movimiento persiste. Y persiste

Lo medí directamente sobre nuestra propia serie —30 días, 622 jugadores, **13.073
pares**— sin pasar por el ojeador:

```
cuando AYER se movió ≥ 1 punto  (n = 6.983)

   hoy va en el MISMO sentido     99,2 %  si ayer subió  (n=2.497)
                                  99,3 %  si ayer bajó   (n=4.343)

   y el tamaño se conserva        factor 0,93
      1-2 puntos → 0,97      3-5 → 0,86      8+ → 0,89
```

**Los precios de Biwenger son brutalmente autocorrelados.** El instrumento lleva
información hacia delante, y de hecho el 89 % *subestima* la propiedad.

**Conclusión: no paro.** Pero el encargo tenía razón en el aviso que se hizo a sí
mismo: lo que hay es un pronóstico **de dirección**, no de tamaño.

### Los 5.993 `pending`

`settle` deja una predicción en PENDING mientras `ahora < due_at` **o** no haya
precio para ese jugador. Dos causas, y la segunda es la que pesa:

1. **Cola estructural.** Los horizontes son 1, 3 y 7 días. Las de 7 días tardan una
   semana. Eso explica ~12 % del total, no el 37 % observado.
2. **El jugador no llega al diccionario de precios.** En el informe del 05/09,
   FutbolFantasy dejó **282 registros sin emparejar de 554**. Un registro que nunca
   casa con un jugador del catálogo no tiene precio contra el que puntuar, y se
   queda colgado hasta los `GIVE_UP_DAYS = 21`, cuando pasa a UNKNOWN.

**No están sesgadas hacia un tipo de señal**, están sesgadas hacia un tipo de
*jugador*: el que la fuente nombra de una forma que no casa. Eso es un problema de
emparejamiento, no del libro.

### Los 2.760 `flat`: se descartan, y está bien

```python
if dicho == "FLAT" or real == "FLAT":
    entrada["outcome"] = "FLAT"
    entrada["direction_hit"] = None
...
decididas = datos["hits"] + datos["misses"]
```

**No cuentan ni como acierto ni como fallo.** El razonamiento del módulo es
correcto: la mayoría de jugadores no se mueve la mayoría de los días, así que
contar los FLAT como acierto premiaría a la fuente más prudente hasta hacerla
parecer la mejor.

### Y una cosa que sí está mal, y es de las doctrinas de esta semana

**El 89,1 % y el ±3,98 % no están medidos sobre la misma muestra.**

```python
if resultado == "PENDING": continue
...
error = entrada.get("magnitude_error_percent")
if error is not None: datos["_errores"].append(...)
```

El `hit_rate` sale de **hits + misses = 7.579**. El error de tamaño se acumula
también sobre los **FLAT**, así que sale de ~**10.339**. Son dos agregados con
denominadores distintos presentados uno al lado del otro. **Doctrina 54.** No lo he
tocado —es el libro del ojeador y no lo pedía el encargo— pero queda dicho.

---

## 1. De dónde sale el 0,1443 %

**La línea**, `rival_bid_model.py:948`:

```python
rendimiento = mejor["expected_value"] / max(mejor["bid"], 1)
# con expected_value = round(p * (valor - importe))
```

### No es constante por diseño: lo fue por accidente

Lo reproduje con los nueve ritmos del ojeador sobre un precio fijo de 2.000.000,
usando la misma aritmética (`speculation_value` → `candidate_bids` →
`win_probability`):

```
ritmo ojeador     valor      mejor puja      p        rinde
    0,30 %     2.008.161     2.000.001    1,0000     0,4080 %
    0,93 %     2.025.386     2.000.001    1,0000     1,2692 %
    2,63 %     2.072.439     2.000.001    1,0000     3,6219 %
    4,55 %     2.126.025     2.000.001    1,0000     6,3012 %
```

**Los rendimientos varían, y varían con el ojeador.** La cadena
`ojeador → speculation_value → puja` funciona **cuando el ritmo llega**.

Por lo tanto: nueve valores idénticos hasta el cuarto decimal sólo pueden salir de
un `valor` idéntico para los nueve. Y `valor` sólo es idéntico si **el ritmo del
ojeador no llegó**.

> **Es el caso peor de los dos que planteabas: un valor de reserva porque la lectura
> falla y nadie se entera.**

**Lo que no puedo hacer:** nombrar el fallback exacto. Hace falta la foto del 14/09 y
en este disco no está (el `status.json` local es del 16/08 y las fotos se paran el
13/09). Dónde mirar: `context["market_rates"]` → `evaluate_market_rate` en
[acquisition_valuation.py:687](src/analysis/acquisition_valuation.py#L687).

### ¿A cuántos deja fuera? A todos

Con el listón en 3 %, un rendimiento de 0,1443 % **no lo pasa nadie, nunca**. No es
que dejara fuera a nueve de 69: es que la vía de reventa estaba cerrada al completo.

### La curva de pujas NO está rota

Los siete 0,1429 son esto:

```python
cortes = [0.05, 0.20, 0.40, 0.60, 0.80, 0.95, 0.995]
curva.append((round(muestras[indice], 4), round(1.0 / len(cortes), 4)))
```

Son **siete cuantiles**, y cada cuantil lleva 1/7 de la masa **por construcción**. Lo
calibrado es el eje x —los factores 1,0000 / 1,0052 / … / 1,2449, que son la
distribución real de primas medida en esta liga—, no los pesos. **Una columna de
pesos plana aquí no dice «no tengo ni idea»: dice «éstos son los siete cuantiles».**

**Pero hay un defecto real al lado, y es de los caros.** Los cortes no están
repartidos por igual: los saltos son 0,15 / 0,20 / 0,20 / 0,20 / 0,15 / **0,045**.
Darle 1/7 = 14,3 % de la masa al cuantil 0,995 afirma que **un rival puja +24,5 %
una de cada siete veces**. Eso hunde la probabilidad de ganar, y con ella el valor
esperado y el rendimiento.

**No lo he tocado.** Es aritmética del motor y la decisión es tuya.

---

## 2. La fórmula, en tres líneas

> **1.** Cada fuente aporta el movimiento que **observa**.
> **2.** Se recorta **dos veces**: por su acierto de dirección `×(2·acierto−1)` y por
> su error de tamaño `× max(0, 1 − error/|movimiento|)`.
> **3.** La estimación es la media de lo que sobrevive, **ponderada por la calidad de
> cada fuente**, multiplicada por la **persistencia medida** (0,93). Si no sobrevive
> nada: **SIN PRONÓSTICO**.

### El ejemplo numerado: las tres buenas dicen +4,55 %

```
COMUNIATE       dirección 2(0,971)−1 = 0,942
                tamaño    1 − 0,93/4,55 = 0,796      peso 0,750
ANALITICA       dirección 0,910 · tamaño 0,754       peso 0,686
FUTBOLFANTASY   dirección 0,782 · tamaño 0,125       peso 0,098

media ponderada por peso   =  3,09 %
× persistencia 0,934       =  +2,89 %/día
```

Fíjate en FutbolFantasy: su error (3,98) se come casi todo su propio mensaje
(+4,55), así que pesa 0,098 frente al 0,750 de COMUNIATE. **Eso es «cada fuente pesa
según SU acierto medido».**

### Los tres cuidados que pedías

**(a) La dirección es fiable, el tamaño mucho menos.** El segundo recorte es el que
hace el trabajo:

```
las tres dicen +0,30 %   ->  SIN PRONÓSTICO   (el error se lo come)
las tres dicen +1,00 %   ->  +0,06 %/día
las tres dicen +2,63 %   ->  +1,40 %/día
las tres dicen +4,55 %   ->  +2,89 %/día
solo COMUNIATE_PULSO +36,6 %  ->  +0,38 %/día
```

**Un +36,6 % de la fuente que se equivoca 35,71 puntos sale como +0,38 %.** Y un
+0,30 % no sale: sale «sin pronóstico», que es la verdad.

**(b) Sin ojeador, no hay estimación.** Sin lectura, sin libro de acierto, con la
fuente no medida, con `n=0`, o con las fuentes contradiciéndose → `available: False`
y `SIN_PRONOSTICO`. Nunca un número.

**(c) El listón no se toca.** `RENDIMIENTO_MINIMO_DEL_CAPITAL` sigue en 0,03.

### Dos versiones que descarté por el camino, las dos medidas

1. **El peso sólo ponderaba la mezcla.** COMUNIATE_PULSO, sola, colaba un
   **+34,18 %/día**: su peso decidía cuánto contaba su opinión, no cuánto recortaba
   su número. Ahora el recorte **multiplica la magnitud**.
2. **La mezcla ponderaba por el `n`.** Entonces mandaba la **peor** fuente por ser la
   más prolífica: FutbolFantasy tiene 7.579 decididas y 3,98 de error, así que tres
   fuentes de acuerdo en +4,55 daban **menos** que COMUNIATE sola. El `n` mide cuánto
   la hemos observado, no cuánto vale.

---

## 3. El antes y el después

Sobre los **288 jugadores** del informe del ojeador que hay en disco. **La foto de
los 69 candidatos es del 14/09 y aquí no está** (el `status.json` local es del
16/08); el reparto entre «entra» y «no entra» es lo que importa y no depende de cuál
sea la foto.

```
el listón son 3,0 %  (NO se toca)

candidatos mirados                288
rinde HOY 0,1443 % para todos  ->  pasan   0
con el ojeador                 ->  pasan  13
sin pronóstico (no entran)         171   (59 %)
```

**No entran cuarenta: entran 13 de 288 (4,5 %).** Y **no sale nadie**, porque antes
no entraba nadie: el 0,1443 % estaba por debajo del 3 % para todo el mundo.

```
jugador                 precio   pronóstico    rinde
Turrientes           1.810.000     +5,737 %    6,30 %
Andrés García        1.430.000    +13,796 %    6,30 %
Dotor                1.710.000    +12,530 %    6,30 %
Giménez                370.000    +15,830 %    6,30 %
Brugué                 250.000     +5,043 %    6,30 %
Arguibide              370.000     +3,985 %    5,53 %
Iker Muñoz             530.000     +3,539 %    4,90 %
Héctor Fort            790.000     +3,158 %    4,36 %
Bardeli                940.000     +3,120 %    4,31 %
Nacho Pérez            160.000     +3,068 %    4,23 %
Berenguer            2.290.000     +2,948 %    4,07 %
Ejuke                  650.000     +2,788 %    3,84 %
Oriol Rey              240.000     +2,694 %    3,71 %
```

**Dos avisos sobre esta tabla:**

- El **6,30 % se repite cinco veces** porque `MAX_PROJECTED_DAILY_RATE = 4,53`
  recorta cualquier ritmo por encima. Es un techo real del motor, no un artefacto
  mío.
- Está calculada **sin rivales** (p = 1), así que es el **techo**. Con rivales todos
  bajan. Sirve para comparar porque el 0,1443 % de hoy es el mismo para todos.

**Y lo más importante de la tabla: los 171 «sin pronóstico» (59 %).** Ésa es la
seguridad. El recorte por error de tamaño deja fuera a seis de cada diez, y son
justo los de movimiento pequeño, donde el ojeador no distingue señal de redondeo.

```
ENCENDIDO = False
```

`test_el_enchufe_esta_puesto_y_la_luz_apagada` lo comprueba. Se enciende cambiando
esa línea, con esta tabla delante.

---

## 4. La etiqueta del catálogo

Elegí **cambiar la etiqueta**, que era la opción que menos toca el motor.

```
antes:   138 nos mejorarían el once
ahora:   138 tienen más puntos en la hoja

antes:   DEF — mejoran a Trent (12 pts), nuestro peor titular del puesto
ahora:   DEF — más puntos que Trent (12 pts), nuestro peor titular del puesto
```

Y el pie, nuevo:

> **«Más puntos en la hoja» no es «mejora el once».** Esta columna es la resta de
> puntos contra el peor titular nuestro de su posición, y nada más: **no mira el
> pronóstico de titularidad** ni aplica la vara con la que decide el motor. Un
> jugador puede tener más puntos y aun así empeorar el once —si el que sale es
> titular confirmado y el que entra no va a jugar—. Quien decide eso es OBJETIVOS,
> con su `xi_decision`; esta lista es para mirar.

**El motor no se ha tocado ni un byte**, y hay guardia de que `el_vestuario_libre` no
empiece a mirar `xi_decision` por la puerta de atrás — porque eso cambiaría lo que
mide el catálogo, y entonces la etiqueta vieja volvería a ser legítima; pero sería
una decisión, no un descuido.

---

## 5. Lo que no hice, y por qué

- **No encendí nada.** `ENCENDIDO = False`, con guardia.
- **No toqué ningún umbral**: ni el 3 %, ni el cupo, ni el suelo, ni el tope, ni
  `bid_cap`, ni `PUEDEN_ENCERRARLO`, ni `MAX_SINGLE_SPECULATION_PERCENT`, ni
  `MAX_SAFE_DEBT`.
- **No toqué la puja de `XI_UPGRADE`**, ni metí el equipo ni la clasificación.
- **No arreglé el reparto de masa de la curva de pujas**, aunque está mal (§1). Es
  aritmética del motor y mueve dinero: la decisión es tuya.
- **No arreglé el denominador mezclado del libro de acierto** (§0). Es el libro del
  ojeador y no lo pedía el encargo.
- **No enchufé el estimador a `acquisition_valuation`.** El módulo existe, calcula y
  está probado, pero **la llamada no está puesta**: enchufarlo de verdad es un
  cambio en la ruta que decide, y el encargo dice «el enchufe se pone; la luz la doy
  yo». Cuando lo enciendas, el sitio es `velocity_percent_per_day` en
  [acquisition_valuation.py:716](src/analysis/acquisition_valuation.py#L716) — que
  ya acepta exactamente este número.
- **No toqué el workflow. No empujé.**
- **No pude reproducir el 0,1443 % exacto** ni verificar el 89,1 %: hacen falta la
  foto del 14/09 y el libro de acierto de producción, y ninguno está en este disco
  (el libro local tiene 8 predicciones, todas de prensa y todas sin resolver).

### Una nota sobre la persistencia

`PERSISTENCIA = 0,934` es una afirmación sobre Biwenger, y las afirmaciones sobre el
mundo que no se pueden recalcular son opiniones con cara de constante. Por eso
`medir_persistencia()` la recalcula desde la serie que se le pase, y el script la
recalcula en cada ejecución: hoy da **0,918 con n=7.242**, y 98,7 % de dirección
sobre n=7.005. Coherente con el 0,934 que lleva la constante.

---

## 6. Lo que queda en el repo

```
src/analysis/el_pronostico_del_ojeador.py            la estimación. No lee nada
scripts/el_ojeador_conectado.py                      el antes y el después
src/analysis/test_el_ojeador_conectado_v1.py         8 pruebas
src/analysis/test_la_etiqueta_dice_lo_que_mide_v1.py 4 pruebas
dashboard-v8/.../ElVestuarioLibrePanel.jsx           la etiqueta y el pie
```

```
python -m scripts.el_ojeador_conectado
python -m scripts.el_ojeador_conectado --libro local
```

| guardia | qué pasa si se rompe |
|---|---|
| `test_la_especulacion_lee_al_ojeador` | vuelve el 0,1443 % para todos |
| `test_sin_ojeador_no_hay_numero` | sin lectura se inventa una constante |
| `test_una_fuente_mala_pesa_menos` | la del 72,9 % empuja como la del 97,1 % |
| `test_un_movimiento_pequeno_no_sobrevive_a_su_error` | un +0,30 % pasa por pronóstico |
| `test_la_estimacion_no_supera_a_lo_observado` | el «recorte» infla en vez de recortar |
| `test_la_persistencia_se_mide_no_se_escribe` | 0,934 se vuelve un número puesto a ojo |
| `test_el_enchufe_esta_puesto_y_la_luz_apagada` | se enciende solo |
| `test_la_etiqueta_dice_lo_que_mide` | la pantalla vuelve a afirmar lo que no mide |
| `test_el_pie_explica_la_diferencia` | se cambia el nombre sin explicarlo |
| `test_no_se_ha_tocado_el_motor` | el catálogo empieza a mirar `xi_decision` a escondidas |
| `test_el_fixture_trae_de_todo` (×2) | **regla 24** |

**Probadas reintroduciendo el fallo, en memoria y sin tocar el fichero:**

```
la estimación vuelve a ser constante    ->  4 guardias en rojo
todas las fuentes pesan igual           ->  3 guardias en rojo
se queda encendido                      ->  1 guardia en rojo
vuelve «nos mejorarían el once»         ->  1 guardia en rojo
```
