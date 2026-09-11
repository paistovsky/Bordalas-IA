# `test_peticiones_v1`: dos guardias que leían el reloj

**11/09/2026** · verja 110/110 · sin push

---

## Las dos

```
FALLA test_la_cache_del_reset_caduca_en_el_reset
      Fase «HIGH_ATTENTION»: la alineacion aun se puede escribir
      y el cierre esta cerca. El catalogo se pide fresco para no
      alinear a un lesionado.

FALLA test_la_vuelta_de_crucero_cuesta_lo_que_dice_el_informe
      una vuelta de crucero cuesta 8 y el informe dice 7.
      Desglose: {'GET /user': 2, 'POST /auth/login': 1,
      'GET /account': 1, 'GET /market': 1,
      'GET /competitions/la-liga/data': 1,
      'GET /league/{id}/board': 1, 'GET /user/{id}/finances': 1}
```

**Son el mismo fallo**, y no es la puja de Aubameyang. Ninguna de las dos da por
hecho que haya una puja viva: ni tocan `maximum_bid`.

## La causa: sí, es la regla 23

`cache_del_reset.leer()` decide si sirve el catálogo según la **fase del
calendario**. En `NORMAL` sirve; en `HIGH_ATTENTION` no, **a propósito** — la
alineación aún se puede escribir y el cierre está cerca, así que el catálogo se
pide fresco para no alinear a un lesionado. Esa regla está bien y no se toca.

Cuando no se le dice la fase, `leer()` la deduce de `fase_del_calendario()`, que
lee el calendario dinámico en disco. **O sea, del reloj.**

- El 10/09 la verja corrió lejos del cierre → `NORMAL` → catálogo de caché →
  vuelta de 7 → verde.
- El 11/09 a las 17:34 la jornada estaba cerca → `HIGH_ATTENTION` → catálogo
  fresco → vuelta de 8 → rojo.

Nadie tocó nada. Cambió la hora.

Y lo mismo tumbó a la primera: la caché del reset devolvía `fresco: False` por la
fase, antes de que el test llegara a comprobar lo que mide, que es la caducidad
**por el reset**.

## Lo que más me molesta: el mecanismo ya existía

El docstring de `se_cachea_en_esta_fase` lo dice con estas palabras:

> `fase` se puede pasar —**las guardias lo hacen**— o se deduce.

Cuatro llamadas de ese fichero la pasaban. Dos no. No era un hueco de diseño: era
una omisión, repetida dos veces.

## El arreglo

Pasar la fase. En las dos que fallaban y en las otras cuatro que no la pasaban y
hoy acertaban por casualidad:

| | |
|---|---|
| caché del reset | `fase="NORMAL"`, para que lo único que varíe sea el reset |
| vuelta de crucero | `fase="NORMAL"` — **crucero *es* una fase**, y había que decirla |
| las otras cuatro | pinadas también; **ningún número se movió**, así que no dependían del reloj — pero ahora además lo dicen |

Una salió mejorada: el test del interruptor `BORDALAS_SIN_CACHE` asertaba
`not leer("catalogo")["fresco"]` sin fase, así que podía pasar **por el motivo
equivocado** (una fase sensible) sin comprobar el interruptor. Ahora se le pone una
fase que *sí* cachearía, y así lo único que puede apagar la caché es el
interruptor.

## Guardia

`test_nadie_mide_sin_decir_en_que_fase` — recorre el árbol del propio fichero y
falla si alguna llamada a `medir_un_ciclo` o `leer` no lleva `fase=`. No comprueba
un número: comprueba que **nadie mida sin decir en qué fase**. Y lleva su propia
red: si el barrido dejara de encontrar llamadas, pasaría en vacío, así que exige
encontrar al menos seis.

Pasó de 37 a **38 pruebas, todas en verde**.

## Sobre el `/tmp` que señalaste

Bien visto, pero ahí no estaba: `test_la_cache_del_reset_caduca_en_el_reset` usa
`tempfile.TemporaryDirectory()` y lo limpia solo. La ruta que sale en el error es
de la sonda de conteo, que también usa un temporal propio — y de eso hay guardia
(`test_la_sonda_no_deja_ficheros_en_el_estado`), que pasó. El estado que cambiaba
entre ejecuciones no era el fichero: era la hora.

---

## Estado

- `test_peticiones_v1`: **38/38**
- Verja: **110/110**
- Rama `main`, **sin push**
