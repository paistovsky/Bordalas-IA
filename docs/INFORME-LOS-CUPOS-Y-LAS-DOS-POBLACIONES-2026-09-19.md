# INFORME — LOS CUPOS, LOS CUATRO DIECIOCHOS Y LAS 69

Fecha: 2026-09-19 (quinto del día) · Rama: `guardias/separar-las-dos-poblaciones`

Ningún interruptor encendido. `BORDALAS_CUPO_POR_ENVIOS` sigue apagado con los tres
números dentro.

---

## BLOQUE 1 — LOS CUPOS

### Puestos

```python
CUPOS_POR_FAMILIA = {
    "renovar": 12,    # pico medido 9
    "puja": 3,        # pico medido 2
    "publicar": 4,    # pico medido 1
}
```

`vender`, `aceptar`, `reroll` y `alineacion` sin número: `cupo_de()` devuelve `None`,
que **no es cero**. No se pone tope a lo que no se ha visto — sus libros se crearon
ayer.

El carril ya los consulta (`puerta_del_cupo("puja", cupo_de("puja"))`) y frena con el
motivo entero:

> «puja»: van 3 escritura(s) enviada(s) de un cupo de 3 en este reset. No se escribe
> ninguna más.

### Dónde queda escrita la fecha de revisión

En dos sitios, y ninguno es un informe:

**1. En el código** — `el_cupo_de_las_escrituras.py`:

```python
REVISION_DE_LOS_CUPOS = "2026-09-26"
```

Con el motivo al lado (`n=5 resets`, ventana `10/09-18/09`) y
`la_revision_del_cupo(hoy)` para preguntarlo.

**2. En el panel** — `status.revisionDelCupo`, con los días que quedan y el `n` con el
que se pusieron. El día de hoy **se le pasa** —del `generated_at` de la propia foto—,
no lo deduce del reloj.

La guardia `test_los_cupos_van_por_familia_v1` comprueba las dos cosas: que el cupo de
renovar no lo consume una puja, y que la fecha existe y responde bien antes y después
del 26.

---

## BLOQUE 2 — LOS CUATRO DIECIOCHOS

### De dónde salen los cortes

De **cuantiles fijos**, no de igual recuento:

```python
CORTES_DE_LA_CURVA = (0.05, 0.20, 0.40, 0.60, 0.80, 0.95, 0.995)
indices = [min(int(corte * total), total - 1) for corte in cortes]
```

Tu cuenta de `91/7 = 13` suponía siete cubos iguales. No lo son: los cortes están
deliberadamente desiguales —el último cubre el 0,5 % de arriba para que la cola entre
en el modelo—, y el recuento de cada banda es **la distancia entre sus índices**.

### ¿Son reales los cuatro dieciochos? — **No. Son la rejilla.**

Aritmética pura, sin tocar un solo dato: sólo los cortes y N.

| N | recuentos que produce la rejilla |
|---:|---|
| **91** | **[18, 18, 18, 18, 14, 4, 1]** |
| 94 | [18, 19, 19, 19, 14, 4, 1] |
| 72 | [14, 14, 15, 14, 11, 3, 1] |
| 120 | [24, 24, 24, 24, 18, 5, 1] |

Con N=91 la rejilla da los cuatro 18 exactos antes de mirar una sola puja. **Tu
sospecha era buena.**

### Pero no es el fallo del 16/09, y conviene no confundirlos

Entonces cada peldaño llevaba `1/7` **sin mirar la rejilla**, así que el último —el
0,5 % de arriba— pesaba igual que el primero: diez veces sobrevalorado. Ahora los pesos
**siguen la rejilla de verdad** (0,15 · 0,20 · 0,20 · 0,20 · 0,15 · 0,045 · 0,005).

Que los cuatro de en medio coincidan no es un reparto inventado: **es lo que hace un
resumen por cuantiles**. La información no vive en los pesos —esos los fija la
rejilla— sino en los **factores**: dónde cae cada banda, y eso lo fijan las pujas.

La guardia lo enseña con una muestra sesgada: ahí los pesos salen
`[0,0 · 0,0 · 0,0 · 0,74 · 0,20 · 0,04 · 0,01]`, o sea que el reparto **sí** responde
a los datos cuando los datos tienen forma.

### Las muestras, repartidas

Con el informe de hoy: **94 medibles** (ayer eran 91 — el ciclo añadió tres).

```
primas distintas (crudas)        89 de 94
primas distintas al redondear    80
grupos con empate                 6   (el mayor: 1.0000 x10)
```

Los empates existen pero **no explican los dieciochos**: con 89 valores distintos de
94, la rejilla manda mucho antes que los empates.

### El intervalo del salto, sobre Chust

Bootstrap: 1.200 remuestreos con reemplazo de las 94, reconstruyendo la curva por el
**mismo camino de producción** en cada uno.

```
punto de partida (n=94)   +18,67 pp     (0,2277 -> 0,4143)
mediana del bootstrap     +17,54 pp
IC 95 %                 [ +13,83 , +20,96 ] pp
IC 90 %                 [ +14,61 , +20,54 ] pp
mínimo / máximo           +11,63 / +25,33 pp

remuestreos con salto <= 0                          0 de 1.200
remuestreos por debajo de la MITAD del salto        0 de 1.200
```

### ¿Aguanta el salto? — **Sí, y no de milagro**

Tu criterio era: si el intervalo se come la mitad del salto, no se sube. **La mitad
del salto son +9,3 pp y el extremo bajo del IC 95 % es +13,83.** No se acerca. Ni uno
solo de los 1.200 remuestreos bajó de +11,63.

**El salto aguanta. La decisión es tuya y el número no lo toco.**

Tres cosas que van con el número, porque cambian cómo se lee:

1. **El punto se movió de +17,16 a +18,67 pp** al pasar de 91 a 94 muestras, en un
   día. Está dentro del intervalo, pero da la medida de lo vivo que es: con n≈90, tres
   pujas nuevas mueven el resultado 1,5 pp.
2. **Los peldaños también se movieron.** El que ayer estaba en +0,52 % hoy está en
   **+0,31 %**. Si el tope se fija entre dos peldaños, cuál sea «el de abajo» cambia de
   un día para otro.
3. El bootstrap mide la incertidumbre **de la curva**, no la del modelo de rivales
   —participación, capacidad—, que se mantuvo fijo. El intervalo real es algo más
   ancho que éste; cuánto, no lo he medido.

---

## BLOQUE 3 — LAS DOS POBLACIONES

### Separadas

`regression_check.las_dos_poblaciones()` decide **leyendo el fichero**, no con una
lista a mano: una lista se queda vieja el día que alguien añade la 72. Por defecto
`--todos` cuenta sólo las puras y dice cuántas dejó fuera; `--con-las-del-mundo` las
devuelve para quien quiera verlas sabiendo lo que valen.

### Y no son 69: son **71**

El recuento del 19/09 miraba sólo `src/analysis/`. El barrido completo de `src/**`:

| carpeta | cuántas |
|---|---:|
| `src/analysis` | 66 |
| `src/intelligence` | 4 |
| `src/actions` | 1 |
| **total** | **71** |

### El censo, congelado

`test_ninguna_guardia_nueva_lee_produccion_v1` lo fija en 71. La lista **sólo puede
encoger**: una guardia nueva que llame a `get_latest_snapshot()` sale en rojo con su
nombre, y una del censo que ya no la llame **también** —para que el número baje de
verdad y no se quede viejo.

Detecta la **llamada** con paréntesis, no el nombre suelto: las dos guardias que
vigilan esto lo nombran para poder buscarlo, y cazar al vigilante sería absurdo. Van
excluidas por nombre y escritas, que una excepción que no se ve es un agujero.

### La lista de las 71: convertibles y no

**52 convertibles · 19 no convertibles de momento.**

El criterio no es el tamaño: es si además de la foto necesitan **bajar a disco**. Una
que sólo llama a un motor que recibe dicts se convierte escribiendo una foto fija; una
que llama al orquestador entero necesita además un calendario de mentira, y eso es
montar un segundo banco de pruebas.

**Las 19 que no, y por qué:**

| motivo | cuántas |
|---|---:|
| orquestador entero (`build_global_decision`) | 10 |
| informe de rivales en disco | 6 |
| calendario en disco | 2 |
| estado de alineación en disco | 1 |

```
orquestador entero
   test_computer_reroll_live_chain          test_listing_lifecycle_orchestrator
   test_computer_reroll_simulated_live_chain test_offer_authority_separation_v1
   test_decision_orchestrator               test_offer_decision_orchestrator_v2
   test_autopilot_v3_safety                 test_offer_intelligence_observer
   test_accept_offer_live_v1                test_speculation_live_v1

informe de rivales en disco
   test_competitive_transactions_real       test_rival_intelligence_v1
   test_competitive_transactions_real_v13   test_rival_intelligence_v2
   test_competitive_transactions_real_v131
   test_competitive_transactions_real_v14

calendario en disco
   test_dynamic_deadline_engine             test_jornada_perfecta_live

estado de alineacion en disco
   test_lineup_monitor
```

Las 52 convertibles están en el detalle del commit. Lista, no conversiones, como
pediste.

---

## BLOQUE 4 — LA QUE ESCRIBE

### La pasada limpia: la primera línea base honesta

Con el árbol quieto y sin nadie editando:

```
ficheros bajo data/ vigilados   165
poblacion pura                  234 guardias
guardias que TOCAN data/          6
```

### Las seis, con nombre

| guardia | qué toca |
|---|---|
| **`test_el_ciclo_publica_v1`** | `marcador.json`, `laliga_standings.json`, `board_events.json`, `board_latest_raw.json`, `profiles_cache.json`, `rival_intelligence.json`, `bitacora_del_saldo.jsonl` — **siete** |
| `test_v10_full_autonomous_live` | `board_events.json`, `board_latest_raw.json`, `profiles_cache.json` |
| `test_el_plato_del_carril_v1` | `profiles_cache.json` |
| `test_jornada_perfecta_market_provider` | `jornada_perfecta_market.json` |
| `test_matchday_calendar_engine` | `laliga_calendar.json` |
| **`test_venta_ejecutable_v1`** | creó y escribió `libro_de_aceptadas.jsonl` |

Las dos primeras corren el ciclo entero: salen a la red y escriben libros. Y no
escriben caché: `test_el_ciclo_publica_v1` toca **`marcador.json`**, que es
exactamente el libro que `los_libros.py` describe como «lo que no se anotó en el
momento no se recupera JAMÁS», y **`bitacora_del_saldo.jsonl`**, y el tablón.

### La sexta es mía, y es de hoy

`test_venta_ejecutable_v1` suplanta el escritor de Biwenger —no sale nada contra la
API— pero el executor **sí anotaba la escritura**, y la anotaba en el libro de verdad,
porque el `apuntar_escritura` que puse ayer no acepta ruta. Creó
`data/trading/libro_de_aceptadas.jsonl` con dos filas inventadas (oferta 987654,
jugador 0), a las 18:13:37.

Introduje una infracción de la doctrina 92 **el mismo día que construí la guardia que
la caza**, y la guardia la cazó a la primera pasada. Arreglado: con el escritor falso,
el rastro también se desvía a una carpeta temporal. Y el libro sintético, borrado —
comprobé antes que sus dos filas eran del escritor falso y no había nada real dentro.

### Y sobre la de las 18:23:54: **no la he encontrado**

Ninguna de las seis tocó `computer_offer_history.json` en la pasada limpia. Y
analíticamente tampoco: las cuatro vías que escriben ese fichero
—`build_computer_offer_reroll_board`, `revalidate_reroll_offer`, el camino de
`offer_decision_engine` y el de `decision_orchestrator`— pasan todas
`persist_history=False`, y el único `record_reroll(` vivo está en
`autopilot_executor:1245`, que es producción.

Así que **no puedo nombrarla**, y prefiero decirlo a inventar una culpable. Lo que sí
queda es que la próxima vez tendrá nombre: la guardia corre las 234 una a una, cada
una en su proceso, y compara la huella después de cada una.

Lo que me queda por descartar, y no he hecho: que no fuera una prueba sino una de mis
propias operaciones de `git` de esa tarde.

### Las otras cinco: qué costaría

Las tres de caché (`profiles_cache`, `jornada_perfecta_market`, `laliga_calendar`) son
baratas: mismo patrón que acabo de usar, desviar la ruta. Las dos que corren el ciclo
entero no: habría que darle al ciclo un modo «sin escribir», que es más que una tarde
y toca el camino de producción. **No las he tocado**, sólo la mía.

### Un agujero que encontré de paso

`los_libros.sin_clasificar()` devuelve **0**, y debería devolver mis tres libros
nuevos. No los ve porque `escritos_por_el_codigo()` sigue la ruta con el AST y mi
`apuntar_escritura` la saca de un **diccionario** (`LIBROS_POR_FAMILIA.get(familia)`),
no de una constante.

O sea: el mecanismo que existe para que «un fichero nuevo entre en `data/` y alguien
tenga que decidir qué es» tiene un punto ciego, y lo abrí yo ayer. Los tres libros
nuevos tampoco están en las excepciones del `.gitignore`, así que hoy no se suben.
Queda dicho; no lo arreglo en este encargo.

### Qué protege `data/` de una escritura que no venga del ciclo

**No hay nada.** Con esas palabras.

Lo que sí existe, y no es esto:

- **`los_libros.escritos_por_el_codigo()`** recorre `src/` y `scripts/` con el AST y
  dice **qué fichero escribe qué módulo**, siguiendo la ruta a través de las
  funciones. Es un catálogo, no un permiso.
- **`sin_clasificar()`** marca lo que el código escribe y nadie ha declarado libro o
  caché. Contesta «¿está declarado?», no «¿quién puede escribirlo?».
- **La lista blanca del 16/09** decide **qué se sube a git**. No toca quién escribe en
  disco.
- **`.gitignore`** oculta, no protege.

No hay permisos de sólo lectura, ni un envoltorio único de escritura, ni un bloqueo.
**Cualquier código que se importe puede abrir cualquier fichero de `data/` en modo
escritura, y nada se entera hasta que alguien mira una fecha.**

No lo construyo hoy, como pediste. Pero dejo dicho cuál creo que es la forma barata:
que todo el que escriba en `data/` pase por una función única —ya casi es así, por la
familia de `apuntar`— y que esa función se niegue si no viene del ciclo. Eso es una
tarde, no un proyecto.

---

## BLOQUE 5 — LOS CABOS

### a) `players_with_live_bid`, con sus dos llamadores

**No le cambié el contrato** —devuelve un conjunto, y lo usan dos sitios— sino que le
puse al lado `se_sabe_que_hay_puesto()`, y los **dos** llamadores preguntan antes de
decidir.

Y hay un detalle que casi se me escapa: vaciar `pendientes_legacy` no bastaba, porque
el código caía a `executable_buys[0]` **sin filtrar**:

```python
objetivo = (
    pendientes_legacy[0] if pendientes_legacy
    else (executable_buys[0] if executable_buys else None)
)
```

Vaciar una lista y luego coger el primero de la lista sin vaciar es no haber hecho
nada. Cerrado también: el respaldo se abstiene si no se sabe qué hay puesto.

### b) `bid_outcome_ledger:1116`

Era barato: una comprobación antes del bucle, hecha.

No cuesta dinero —no escribe en Biwenger— pero mentía justo donde dices: un cero por
no haber mirado **baja el denominador** de la conversión y nos hace parecer mejores de
lo que somos. Es el número con el que decidimos si el problema es elegir o aparecer.

### c) Volver a medir dentro de una semana

En el código y en el panel, no en un informe. Está en el bloque 1.

---

## LO QUE NO HICE, Y POR QUÉ

- **Ni una escritura contra Biwenger.**
- **No encendí ningún interruptor**, incluido `BORDALAS_CUPO_POR_ENVIOS` con los tres
  números ya dentro.
- **No cambié el tope del once.** El bloque 2 es medición; el número es tuyo y ahora
  tiene su intervalo.
- **No convertí las 71.** Lista con su reparto, como pediste.
- **No construí nada contra la escritura en `data/`.** El 4.3 era contestar, y la
  respuesta es que no hay nada.
- **No toqué** `MAX_SINGLE_SPECULATION_PERCENT`, `MAX_SAFE_DEBT`, el suelo de cobro,
  `MIN_WIN_PROBABILITY`, `MAX_PROJECTED_DAILY_RATE`, las cinco de `PUEDEN_ENCERRARLO`
  ni el tope de reventa.
- **No apliqué `stash@{0}`** ni toqué `bordalas-live.yml`.
- **No empujé nada.**
