# La escala — informe

**Rama:** `motor/la-escala`, desde `main`.
**Push:** NO.

---

## HASTA DÓNDE LLEGUÉ

```
BLOQUE 0  el once de esta noche          HECHO, arreglado y listo para subir
BLOQUE 1  de dónde sale el 3 %           HECHO (medido ayer; es la misma pregunta)
BLOQUE 2  la escala escrita              HECHO, publicada y con guardias
BLOQUE 3  la capacidad de vuelta         MEDIDO, no construido — y la premisa era falsa
BLOQUE 4  qué pujan los rivales          NO EMPEZADO
BLOQUE 5  POSITION_DESIRED               NO EMPEZADO
BLOQUE 6  el rival de la jornada         NO EMPEZADO
```

Paré donde me dijiste que parase. **Los bloques 4, 5 y 6 no están a medias: no están.**

Y del 3 te doy la medición y el hallazgo estructural, **pero no construí el cálculo de
capacidad ni sus dos guardias**. Media capacidad con dos guardias a medias es
exactamente lo que dijiste que es peor que nada.

---

## Dos avisos

**1. La foto sigue sin estar fresca.** Tercer encargo seguido:

```
diagnostico/status.json   meta.generated_at = 2026-09-17T07:30:55
hoy                       18/09
```

**2. Esta noche es la jornada 7, no la 8.** El calendario de LaLiga:

```
jornada 7   primer partido 2026-09-18T21:00   ventana desde 19:30
jornada 8   primer partido 2026-10-09T21:00
```

La jornada 8 es el **9 de octubre**, después del parón. Lo que caduca esta noche es la
**7**. Si estabas mirando la 8, estabas mirando el mes que viene.

---

## BLOQUE 0 — Arreglado y listo para subir

### ¿Cuadran `round_id` y `target_matchday`? **La pregunta estaba mal planteada**

No tienen por qué cuadrar: **son dos numeraciones distintas**.

```
round_id          4899, 4903, 5125...   el round de BIWENGER
                                        sale de `rounds.data.round.id`
target_matchday   1..38                 la jornada de LALIGA
                                        de ahí salen la ventana y el primer partido
```

El problema real no es que no sean iguales. Es que **son dos fuentes distintas y nadie
las cruzaba**:

- El once se anotaba bajo `jornada_en_curso(snapshot)` — el round que Biwenger dice que
  está en curso **ahora**.
- La ventana venía del calendario de LaLiga, de `target_matchday`.

El 17/09 la foto traía `round_id: 5125` —**la jornada 6 aplazada, ya jugada el
15-17/09**— mientras la ventana abierta era la de la jornada 7. **Si el round de
Biwenger va retrasado cuando se cruza la ventana, el once queda anotado bajo la jornada
equivocada, y la línea no tenía forma de decirlo.**

### Qué arreglé: guardar las dos, no negarme a anotar

> **Negarse a anotar por una etiqueta dudosa habría sido peor**: la jornada se juega una
> vez y no vuelve. Una etiqueta se arregla después; una jornada perdida, no.

`anotar_el_once` recibe ahora `matchday` —la jornada de LaLiga, la misma fuente de la
que sale la ventana— y la guarda en la línea junto al `round_id`:

```json
{"round_id": 5125, "matchday": 7, "formation": "4-4-2",
 "players": [...], "minutos_de_margen": 53, ...}
```

Y si el calendario fallara y no hubiera `matchday`, **se anota igual** y el motivo lo
dice: «Once de la jornada 5125 **(round de Biwenger)** anotado a 53 min…».

Tres ficheros: `el_once_que_jugo.py` (el campo y el motivo), `dashboard_state.py` (se lo
pasa), y la guardia.

### Qué tiene que verse en la vuelta de las 20:07

```
1. QUE LA VUELTA LLEGUE. Es la ÚNICA dentro de la ventana:
      19:30 se abre · 20:07 el latido · 21:00 el pitido
   Ni 19:07 (aún cerrada) ni 21:07 (ya empezado) sirven.

2. EN EL LOG, esta frase:
      "Once de la jornada 7 anotado a NN min del primer partido."
   Si dice "jornada 5125 (round de Biwenger)", se anotó igual —no se
   ha perdido nada— pero el round iba retrasado.

3. EN EL LIBRO data/trading/... perdón: data/intelligence/onces_de_la_jornada.jsonl
      una línea, con matchday: 7 y once jugadores.

4. EN LA PANTALLA, `marcador.el_once_anotado`:
      observadas 8 · anotadas 1     <- el 0 se rompe hoy o no se rompe
```

**Y el riesgo que no puedo quitar desde aquí:** el paso del dashboard en el workflow no
tiene `if: always()`. Si la verja se pone roja o el ciclo revienta, no se anota. Esa
línea es tuya y no la toco.

---

## BLOQUE 1 — El 3 %: **nunca se midió como listón**

Esta es la misma pregunta que contesté ayer en `carril/el-liston-propio`
(`docs/INFORME-EL-LISTON-PROPIO-2026-09-18.md`, commit `8d49fe2`). El resumen, con sus
fechas:

```
origen    commit 1512f22 · 2026-08-16 19:04 · Paistovsky
motivo    parar una puja concreta por Soler (0,12 % de rendimiento,
          81 % del presupuesto inmovilizado)
calibración   NINGUNA. La justificación era aritmética:
          "saltos de 10.000 EUR sobre un jugador de precio medio son
           justo un 3 %"   ->   10.000 / 333.333
```

**Y la premisa era falsa.** Lo admite el propio código desde el 10/09: «para el jugador
mediano el suelo de ruido real es **0,64 %**, casi cinco veces menos».

La tabla de **81.788 operaciones** que hoy lo respalda se añadió **después** (fichero
commiteado el 06/09, aunque se llame `...2026-09-27`) y **calibra los tramos de racha
diaria, no el listón**. Nadie ha probado nunca 2 % ni 4 %.

**Para qué vía se pensó:** para la ESPECULACIÓN, y lo dice desde el primer día. La
reventa al Computer lo hereda solo por compartir el `intent: SPECULATION`.

---

## BLOQUE 2 — La escala, escrita y publicada

En `src/analysis/la_escala.py`, un solo sitio, con la regla **y su consecuencia**:

```
1  POSITIVO_AL_CIERRE        si no, no puntuamos
   -> renovar una oferta NO es tarea menor: es el plan de emergencia
2  NO_DEGRADAR_EL_XI         ninguna reventa vale un titular
   -> pero si MEJORA, se vende comprando el recambio PRIMERO
3  MEJORAR_EL_XI             la caja y la deuda son para esto
   -> pujar por encima del rival SIN techo es el caso Rubén García
4  REVENDER                  con lo que sobre, nunca bajo el listón propio
5  LA_FORMA_NO_SE_PERSIGUE   los once mejores; la forma es el RESULTADO
```

`a_que_peldaño_responde(decision)` traduce lo que el motor dice hoy a su peldaño, y **lo
que no reconoce sale como `SIN_PELDAÑO`** en vez de colocarse a ojo.

### ¿Alguna decisión se saltó la escala? Sobre los 66 candidatos de la foto

```
peldaño 2   NO_DEGRADAR_EL_XI     4
peldaño 4   REVENDER             37
sin peldaño                      25
```

**Las 25 sin peldaño son todas `intent: None`** — «no vale la pena por ninguna vía».
Eso no es una decisión que se salte la escala: **es la ausencia de decisión.** Ninguna
de las 41 restantes contradice el orden.

**Y no encontré ninguna reventa que le quitara caja a un fichaje**, por un motivo que
importa: en toda la temporada hay **2 fichajes** en el libro de pujas. El problema no ha
sido nunca que la reventa ganara; es que apenas ha habido fichajes.

---

## BLOQUE 3 — Medido, y **la premisa era falsa**

> **`MAX_SAFE_DEBT` no es un número puesto a mano.** Es
> `solvency_engine.calculate_max_safe_debt()`, y calcula exactamente lo que pides:
>
> ```
> max_total_debt            = guaranteed_recovery − safety_buffer
> additional_debt_headroom  = max_total_debt − current_debt
> ```
>
> Es decir: **hasta donde se pueda volver a positivo**, ya. Lo único fijo ahí dentro es
> `SAFE_LIQUIDITY_BUFFER`.

Así que el bloque 3 no es «construir lo que no existe»: es **comprobar si lo que existe
cuenta solo lo vendible**. Y eso no lo he terminado.

### Lo que sí medí, sobre la foto

```
déficit de hoy                                          373.984
lo que el motor dice que levanta sin romper el once    9.748.100
margen                                                 9.374.116
```

**Lo que el freno de titularidad bloquea** (de 20 jugadores, 3):

```
Yamal      22.100.000   titular
Jutglà      3.160.000   titular
Dituro      2.200.000   titular
                        --------
                        27.460.000 BLOQUEADOS
```

**Lo que queda libre:** 17 jugadores, **29.010.000** a precio de mercado, de los cuales
**7.890.000 son no titulares**.

### Y aquí está el número que importa

> **27,46 M están bloqueados por el freno — más que los 29,01 M libres.** Casi la mitad
> de la plantilla en euros no se puede tocar sin degradar el once.
>
> Y de esos 27,46 M, **22,1 son Yamal**, que además está bajo el suelo del +1 % desde
> hace 37 días. Está bloqueado por dos motivos a la vez.

**Hoy no hay escenario sin vuelta:** 9,75 M contra un déficit de 0,37 M. El día que el
déficit se acerque a esa cifra, los 27,46 M seguirán sin poder tocarse.

### Lo que NO hice del bloque 3, y por qué

No construí el cálculo de capacidad ni sus dos guardias
(`test_la_capacidad_no_pasa_del_techo_duro`,
`test_la_capacidad_cuenta_solo_lo_vendible`), **ni medí los diez días de escaparate**.

Dos razones:

1. **No daba tiempo a hacerlo bien**, y dijiste que un bloque a medias es peor que un
   bloque sin hacer.
2. **La premisa cambió.** Si `MAX_SAFE_DEBT` ya es el cálculo, lo que hay que hacer no
   es escribir otro al lado: es **auditar si `guaranteed_recovery` respeta el freno de
   titularidad y el suelo del +1 %**. Eso es un encargo distinto del que me diste, y
   prefiero decírtelo a construir un segundo cálculo que compita con el primero.

---

## Guardias

**+1 módulo, 6 guardias**, en `src/analysis/test_la_escala_v1.py`, dada de alta en la
verja.

```
test_el_once_se_anota_con_la_jornada_de_laliga
test_sin_jornada_de_laliga_se_anota_igual_y_se_dice
test_la_ventana_sigue_mandando
test_la_escala_se_respeta
test_cada_decision_dice_a_que_peldaño_responde
test_la_escala_se_publica_entera
```

**Las inyecciones de fallo del bloque 0 muerden, 4 de 4:**

```
MUERDE  bloque0 / se pierde la jornada de LaLiga
MUERDE  bloque0 / se inventa una jornada cuando no hay
MUERDE  bloque0 / sin jornada se niega a anotar (pierde la jornada)
MUERDE  bloque0 / la ventana deja de mandar
```

La tercera es la que más me importa: **atar que el arreglo no se convierta en un tapón**
que pierda la jornada por falta de etiqueta.

### Y una guardia vieja me cazó otra vez

`test_el_mapa_del_intent_no_miente` se puso roja porque `la_escala.py` usa `XI_UPGRADE`
y `SPECULATION` para traducir decisiones, y nadie había escrito qué decide con ellas.
**Segunda vez en dos días que ese censo por AST caza algo mío.** Declarado en el mapa,
no relajada la regla.

---

## Lo que no hice, y por qué

- **Ni una escritura contra Biwenger.**
- **No encendí nada.** Lo único que entra en producción es el arreglo del bloque 0.
- **No subí el cupo ni `MAX_SAFE_DEBT`.**
- **No toqué** `POSITION_DESIRED`, `STRATEGIC_FLOOR`, `FIXTURE_WEIGHT`, `HOME_WEIGHT`,
  el suelo del +1 %, el tope del +0,25 %, el listón del 3 %, `count_free_slots`,
  `ROSTER_FILL`, las cinco de `PUEDEN_ENCERRARLO` ni
  `MAX_SINGLE_SPECULATION_PERCENT`.
- **No propuse vender a pérdida.**
- **No conté con ningún jugador concreto** para nada futuro (doctrina 73). Yamal,
  Jutglà y Dituro aparecen como medición de lo que hay bloqueado hoy, no como plan.
- **No salí a la red.**
- **No toqué `.github/workflows/bordalas-live.yml`**, aunque ahí sigue la línea que más
  protegería esta noche.
- **No empujé.**
- **No hice los bloques 4, 5 y 6.**

### Lo que contradijo al encargo

1. **Esta noche es la jornada 7, no la 8.** La 8 es el 9 de octubre.
2. **`round_id` y `target_matchday` no tienen que cuadrar**: son numeraciones distintas.
   El fallo era que nadie las cruzaba, y se arregla guardando las dos.
3. **`MAX_SAFE_DEBT` no es un número puesto a mano**: ya se calcula como «hasta dónde
   puedo volver a positivo». Lo que falta es auditar si cuenta solo lo vendible.
4. **El 3 % nunca se calibró como listón** — misma respuesta que ayer.
5. **Ninguna decisión se saltó la escala**, y las 25 sin peldaño son ausencia de
   decisión, no desobediencia.
