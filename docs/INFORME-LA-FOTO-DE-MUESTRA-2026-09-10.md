# La verja en rojo: una foto de muestra versionada

**10/09/2026** · verja 111/111 en condiciones de CI · sin push

---

## Qué pasaba

`test_la_pantalla_pinta_v1` leía la foto real de
`dashboard/data/status.json`. Ese fichero **no está en el repo**, y la caché que CI
restaura antes de la verja sólo cubre `data/`, nunca `dashboard/`. Así que en el
runner no existía nunca.

Y aquí está lo que me pone de mal humor de mi propio trabajo de ayer: cuando no la
encontraba, el guion decía `SIN MUESTRA (ENOENT)` y **salía con código 0**. Verde,
habiéndose saltado la mitad que pinta. Justo el verde vacuo que llevamos todo el
día cazando — y yo lo escribí, y encima lo declaré en `DEUDA` como si fuera un
apaño aceptable.

No lo era: la mitad que pinta **nunca corrió en CI**, ni una vez.

## Qué hay ahora

`dashboard-v8/tools/foto_de_muestra.json` — 128 KB, recortada de una foto real del
10/09 (listas a 4 elementos, cadenas a 300 caracteres, el XI entero porque es lo
que más pinta). Va **en el repo**.

- La muestra se pinta **siempre**, en todas partes.
- La foto real se pinta **además**, si está. Su ausencia ya no es un fallo ni un
  salto: simplemente no aporta la comprobación de regalo.
- Si falta la **muestra**, el guion sale en **rojo**. No hay camino a verde sin
  pintar.

```
pintar muestra:   tira 736 · inicio 14477 · auditoria 20580
pintar foto real: tira 736 · inicio 16117 · auditoria 45532
```

De paso, la guardia deja de leer estado externo para lo que importa: es
determinista y pinta lo mismo en tu disco y en el runner.

## Verificado en las condiciones exactas de CI

Aparté `dashboard/data/status.json` y lancé la verja entera:

```
Los 111 en verde. Se puede subir.
```

Y con la foto real puesta, también 111/111.

## Guardias

- `test_la_foto_de_muestra_esta_versionada` — la muestra existe, trae los cinco
  bloques que Inicio necesita, trae el XI y no es un fichero de juguete. Una
  muestra vacía pintaría una página vacía y estaríamos igual.
- `test_la_pantalla_se_monta_y_pinta` — ahora exige `pintar muestra: tira` y
  **prohíbe** que aparezca `SIN MUESTRA` en la salida.

## Lo que queda pendiente y no toco

La entrada de `DEUDA` de `test_el_ciclo_publica_v1` sigue en pie: esa monta el
estado en Python y necesita un `data/snapshot_*.json`, que en CI sí llega por la
caché. Es un caso distinto —ahí el dato sí está— pero merece el mismo tratamiento
algún día: un snapshot de muestra versionado.

No lo hago ahora. Faltan horas para las 04:45 y lo que había que dejar en verde
está en verde.

---

## Estado

- Verja: **111/111**, con y sin la foto real
- Rama `main`, **sin push**
