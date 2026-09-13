# El escaparate, enchufado

**13/09/2026** · rama `xi/el-punto-ciego` · verja 119/119 · sin push

**Bloque 0 y sólo el bloque 0**, como pediste.

---

## Antes de nada: los tres commits ya están en `main`

```
origin/main   285ace8  el libro mira la plantilla
              f4cdc11  la hora de la puja se pasa, no se deduce
              4812e54  libro: recoge lo que ve
```

Los empujaste tú. No faltaba nada; esta rama sale de ahí.

---

## 1. Trent se publica a 3.139.500, y por qué ese precio

```
precio de mercado      2.730.000
PRIMA_DE_LA_PETICION       x1,15
                       ---------
se lista a             3.139.500     +15 %
```

**No es una regla nueva.** `PRIMA_DE_LA_PETICION` es la misma constante que usa la
renovación — vive en `renovar_ofertas` y el escaparate la importa de ahí, no la
copia. Si algún día se mueve, se mueve en los dos sitios a la vez.

Y queda **por encima del precio de mercado**, que es lo que Biwenger exige: los dos
únicos HTTP 400 de la renovación del 10/09 fueron por pedir por debajo.

### El ensayo, con los datos reales de esta mañana

```
1. RECOGIDA      13 compras de la plantilla que no estaban en el libro,
                 1 viaje del carril abierto
2. VIAJES        [('Trent', 37499)]
3. PLAN          1 para publicar
                 Trent  mercado 2.730.000  ->  LISTAR A 3.139.500
4. ESCRITURA     {player_id: 37499, price: 3139500, execute: True}
```

Y Jonny —marcado como viaje **y** titular— sale saltado con el motivo:
*«es TITULAR: no se publica aunque el libro lo marque como viaje»*.

---

## Las condiciones que pusiste, y cómo quedan

| | |
|---|---|
| **Sólo viajes del carril** | `_llenar_el_escaparate` filtra por `via == RENDIJA`. Lo que el libro no marca así no se toca |
| **Nunca un titular** | `test_publicar_no_toca_a_un_titular`. Y **con la lista vacía no se publica nada** — ni a Trent: una lista vacía no es «no hay titulares», es que no se leyó el once |
| **Zona de silencio** | `permite_escribir`, la misma puerta que la renovación, y mira la respuesta |
| **Una por vuelta** | `pendientes[:1]` |
| **Idempotente** | contra **la foto** (`compact_listings`), no contra la memoria |
| **El precio** | `PRIMA_DE_LA_PETICION`, la que ya existía |

### Dos cosas que salieron al construirlo

**`publicar()` tiene `en_vivo=False` por defecto** — y hace bien, es el defecto de
las tres rutas que escriben. Pero sin pasárselo, el ciclo se habría quedado
montando el plan y mandando `execute: False` **para siempre**: enchufado y mudo,
que es exactamente la peor forma de estar apagado. Hay guardia que lo exige.

Y tiene **interruptor propio**: `ESCAPARATE_APAGADO=1` lo para sin desplegar, como
las otras rutas.

---

## 2. La guardia de enchufado medía la intención, y por eso estaba verde

`test_ninguna_pieza_armada_esta_desenchufada` comprobaba que el **módulo** fuera
alcanzable por imports. Y lo era: la telemetría importa `escaparate_executor` para
`viajes_sin_listar`. Mientras tanto, **`publicar()` no lo llamaba nadie** y Trent
llevaba medio día en el banquillo con la verja en verde.

Medir que algo *se puede importar* es medir la intención — doctrina 37, tercera
vez. Ahora `test_las_piezas_que_escriben_se_llaman` comprueba, **del árbol**, que
el ciclo **llame** a las cuatro rutas que escriben:

```
_correr_el_carril · _llenar_el_escaparate · _renovar_en_la_ventana · _pujar_en_el_reset
```

Si mañana alguien arma una quinta y no la llama, se pone roja el mismo día.

---

## 3. La condición de parada que pusiste: no la puedo comprobar, y te digo qué mirar

Dijiste: *«Si el `libro_del_carril.jsonl` de producción no tiene la entrada de
Trent y su origen sale DESCONOCIDO, PARA y dímelo.»*

**No puedo leer producción.** `data/` está en `.gitignore` y el libro del carril
vive en el caché de Actions. Lo que sí he verificado:

```yaml
- name: Restore Bordalas state
  uses: actions/cache@v4
  path: |
    data/trading          <- el libro del carril está aquí
  restore-keys: bordalas-state-
```

**`data/trading` sí se restaura entre ciclos**, y el carril escribió su libro a las
16:45 del 12/09. Es evidencia fuerte, no prueba.

### Y el código falla del lado seguro

No he inventado ninguna marca. Si en producción el origen sale `DESCONOCIDO`:

- `recoger_compras_de_la_plantilla` **no abre el viaje** (sólo lo abre con
  `target_source == RENDIJA`)
- `_llenar_el_escaparate` no encuentra ningún viaje del carril
- **no publica nada**, y el estado dice por qué

Un día más con Trent parado, como preferías, y sin etiqueta puesta sobre una
suposición.

**La línea que hay que mirar en el próximo ciclo** es
`bid_outcomes.recogidas_de_la_plantilla`, y dentro, la entrada de Trent:

```
target_source   RENDIJA       -> se publica solo
target_source   DESCONOCIDO   -> no se publica, y hay que hablarlo
```

---

## 4. Lo que no hice, y por qué

**Bloques 1, 2 y 3: no empezados.** Dijiste «bloque 0 primero y solo… verja,
informe, y paras», y que si tenía que elegir acabase uno bien. Eso he hecho.

Así que estas preguntas del informe **quedan sin contestar hoy**, y las apunto
para que no se pierdan:

- cuántos jugadores libres hay y los veinte primeros
- si Zabiri, Fer Niño y Carlos Espí salen en esos veinte
- qué dice el histórico sobre el 50 % de titularidad, con su `n`

**Y no he tocado nada de lo prohibido:** no se vende nada, no se acepta ninguna
oferta, ninguna puja nueva, ningún techo ni prima movidos, cupo 1, suelo
1.000.000, tope 3.000.000, `bid_cap` intacto, y el workflow sin tocar.

Una nota sobre la deuda: **listar no es vender.** Trent sale al escaparate a
3.139.500, y quien juzgue las ofertas que lleguen sigue siendo `que_cobrar`, con su
suelo de coste + 1 %. Nada de esto puede cerrar una venta por su cuenta.

---

## Guardias

| | |
|---|---|
| `test_el_escaparate_publica_v1` | **7/7** — nunca un titular (y nada sin el once), sólo viajes del carril, no republica, una por vuelta, el precio de la regla que ya existe, la zona de silencio, y que publica de verdad y se apaga |
| `test_esta_enchufado_v1` | **7/7** — dos nuevas: que el ciclo **llame** al escaparate, y que llame a las cuatro rutas que escriben |

Y una vieja corregida: `test_no_se_publica_a_quien_no_esta_en_plantilla` llamaba
sin el once, y la barandilla nueva cortaba antes de llegar a lo que probaba.

---

## Estado

- Verja: **119/119**
- Rama `xi/el-punto-ciego`, un commit, **sin push**
- Pantalla construida y desplegada
