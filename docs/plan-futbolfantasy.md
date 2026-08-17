# Bordalás IA — plan: FutbolFantasy como fuente única de inteligencia

Sustituye al plan de `claude/estado-2026-08-17-titularidad.md` en todo lo
que se refiera a Jornada Perfecta. **JP se deprecia.**

## Estado confirmado en pantalla (17/08, tarde)

```
OBJETIVOS DE HOY   20 valorados · un punto 22.727 € · 0/20 CON PRONÓSTICO
  Lunin      POR  480.000 €   sin dato   vale 962.155 €   pujaría 528.001 € (83%)  PUJAR
  Eriksson   POR  2.600.000 € sin dato   vale 1.517.489 €                          NO COMPENSA
  Tenaglia   DEF  3.390.000 € sin dato   vale 0 €                                  SIN VALOR
  ...
  "Ningún candidato tiene pronóstico de titularidad, así que la regla
   del once bloquea las 17 mejoras que había."
```

Diecisiete mejoras bloqueadas por falta de dato, no por falta de chollos.
El aviso funciona: el dashboard dice la verdad sobre sí mismo. Ese es el
punto de partida.

## Las cuatro decisiones del dueño

1. **La fuente es FutbolFantasy, no Jornada Perfecta.** Más fiable
   (verificado a mano: FF da Tenaglia 90 % y Yeray 70 % en la jornada 2
   correcta, y el `ff_probability: 70.0` guardado en su `status.json`
   coincide exactamente con lo que publica la web hoy).

2. **Fuera el sistema multifuente.** No funciona: con cobertura 1 topa
   todo en 74/26 y las etiquetas dejan de significar nada. Una sola
   fuente, FF, sin consenso ni topes.

3. **Las jerarquías de FF son fundamentales** — DIOS, Clave, Importante,
   Rotación, Revulsivo, Reserva, Descarte. Es el eje del motor de
   mercado.

4. **Todo tiene que verse en el dashboard.** "Quiero ver lo que ve Pepe."

## Por qué la jerarquía cambia el motor, y no es un campo más

```
% titular   ->  ¿juega ESTE sábado?    semanal, volátil
jerarquía   ->  ¿qué es en su equipo?  estructural, toda la temporada
```

Los errores del 16 y 17/08 vienen de decidir compras que duran meses con
un dato de una semana. Castrín —97 puntos, suplente— no era un problema
de porcentaje: es Reserva, y eso no cambia el jueves.

Reparto de trabajo propuesto:

| decisión | dato |
|---|---|
| ¿lo fichamos? ¿cuánto vale? | **jerarquía** |
| ¿lo puedo vender? | **jerarquía** |
| ¿quién juega el sábado? | **% titular** |
| puntos esperados | jerarquía de base, % como ajuste de jornada |

Y el veto se vuelve estructural: se bloquea cambiar un **Clave** por un
**Revulsivo**, en vez de reaccionar a que el % bajó de 67 a 63.

## El resto de inteligencia de FF, priorizado por impacto

Inventario tomado de una página de equipo. **Sin verificar contra el
HTML** — hay que mirarlo antes de diseñar encima.

1. **Dificultad del calendario.** No tenemos nada de esto y es lo que
   más pesa: un Clave contra el Levante no vale lo que contra el Barça.
   Entra en puntos esperados y en la proyección de reventa.
2. **Estado físico, sanciones, convocatorias.** FF distingue "duda por
   lesión", "tocado o sale de lesión", "se perderá la siguiente si ve
   otra tarjeta", "sancionado FIFA, disponible J12". Biwenger solo da un
   `status` binario. Facundo Garcés sale NO DISPONIBLE en el tablero sin
   decir hasta cuándo; FF lo dice.
3. **Previsibilidad del equipo** — "87 % previsibilidad", "sin
   rotaciones / con rotaciones", "2,64 jugadores en riesgo". Es la
   calibración de confianza que hoy está escrita a mano. Multiplicador
   por equipo sobre la fiabilidad del pronóstico.
4. **Transferible / Cedible + rumores de fichajes.** Única señal
   adelantada: si el club ficha portero, la jerarquía del nuestro cambia
   antes que cualquier pronóstico.
5. **Minutos jugados, racha y media de puntos.** A partir de la jornada
   6-8 sustituyen al pronóstico: son el dato, no la predicción del dato.
6. **Valor Biwenger y su variación publicados por FF.** Segunda fuente
   para contrastar el motor de velocidad de precios.

Descartado por ruido: valores de las otras plataformas (Comunio,
Futmondo, Marca…), Predicted11 de la comunidad, edad, altura, pie.

## Orden de trabajo

**Bloque 1 — la fuente**
1. Leer el HTML real de una página de equipo de FF y confirmar cómo
   vienen jerarquía, % titular, estado físico, calendario y
   previsibilidad.
2. Extender la identidad de FF **al mercado**, no solo a la plantilla.
   Hoy `build_ff_signals(snapshot, roster, ...)` solo mira `my_team`;
   por eso ningún candidato tiene pronóstico. Es la causa directa del
   0/20 de la captura.
3. FF como fuente única: sin consenso multifuente, sin topes de 74/26.
   `source_coverage` sigue publicándose.

**Bloque 2 — la jerarquía en las decisiones**
4. Jerarquía en la valoración y en el guardarraíl, con el reparto de la
   tabla de arriba.
5. El veto del once pasa a ser estructural (jerarquía), no semanal (%).

**Bloque 3 — el resto de inteligencia**
6. Calendario y previsibilidad primero: mejoran decisiones que ya se
   toman, sin tocar arquitectura.
7. Estado físico y sanciones.
8. Lo demás, de uno en uno, **cada uno con su comprobación en
   `consistency`**.

**Transversal — el dashboard**
Cada dato que entre tiene que salir en pantalla. Columna de jerarquía en
OBJETIVOS junto a TIT., estado físico con su motivo y fecha de vuelta,
dificultad del próximo rival, y previsibilidad del equipo. Si un dato no
se ve, no se mete.

## Coherencia pendiente, que no desaparece

- La valoración se apunta el dinero de vender al sustituido **sin
  preguntar al guardarraíl si esa venta está permitida**. Con Lunin:
  650.000 € de los 962.155 € que "vale" son la venta de Bayindir.
- Vender un titular solo debe permitirse para fichar a otro titular.
- 7 aserciones de `test_position_guardrail_v1` con el suelo de portero
  antiguo (solo si se rehace el suelo a 2).
- Barreras de especulación demasiado apretadas → ranking por coste de
  oportunidad.
- Que Pepe cancele sus propias pujas muertas.

## Nada de esto está aplicado

El trabajo del 17/08 (peldaño histórico, `STARTER_FLOOR`, suelo de
porteros a 2, orden de permanencia por probabilidad) **no se subió** por
decisión del dueño. Se rehará sobre FF. Lo que sí está en producción es
el trabajo del 16/08: motor de compra unificado, auditoría de
consistencia del dashboard, columnas PUESTO / PUJARÍAMOS / TIT.
