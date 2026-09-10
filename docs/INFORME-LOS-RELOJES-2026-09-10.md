# Los relojes: una sola cadencia, y el cambio de hora se detecta

**10/09/2026** · verja 111/111 · sin push

---

## 1. Los dos textos, atados al cron

Tenías razón en el diagnóstico: la cuenta atrás iba bien porque lee el cron real, y
eran los textos los que mentían. La cadencia estaba escrita a mano en **tres**
sitios, no dos.

| dónde | decía | ahora |
|---|---|---|
| aviso amarillo | «el ciclo corre cada 30» | `cadenciaEnPalabras()` → «cada hora» |
| lateral | «ciclo 30 min» | `cadenciaEnPalabras()` |
| `STALE_CYCLE_SECONDS` | `2 * 30 * 60` | `2 * CADENCIA_MINUTOS * 60` |

**El tercero era el peor y no se veía:** con `2 × 30 min` y un ciclo horario, el
cuadro «ESTE CICLO» se marcaba como *historia* a la hora de vida — es decir, en
cuanto entraba el siguiente. Un aviso que salta siempre no se lee.

`cadenciaMinutos()` **no es una constante**: cuenta los huecos entre los disparos
de verdad, los mismos que alimentan la cuenta atrás, y se queda con el más
frecuente. Se toma la moda y no la media a propósito: el hueco de la madrugada
—cinco horas sin cron interno— se llevaría la media a un sitio que no describe
ningún ciclo real. Hoy da **60**.

### Para que no puedan volver a discrepar

La autoridad es el cron de `bordalas-live.yml`. `test_la_cadencia_sale_del_cron`
lo **lee del YAML**, calcula la cadencia y obliga a los dos espejos —`relojes.js` y
`dashboard_state.py`— a llevar el mismo cron y el mismo número. Si mañana el cron
cambia y alguien no toca los espejos, la verja se pone roja antes que la pantalla.

---

## 2. Los crones externos, escritos y detectados

La compensación está donde vive la definición de los relojes, junto al cron
interno, con la fecha en que caduca:

```
escrito  45,50 3 * * *   ->  dispara 04:45 y 04:50 reales   (ventana)
escrito  15 6 * * *      ->  dispara 07:15 reales           (tras el reset)
```

**Y mejor que recordarlo: se detecta.** `avisoDelCambioDeHora()` no mira el
calendario ni lleva un `+1` escrito — **le pregunta a la base de zonas** si Madrid
sigue en verano. Mientras lo esté, no aparece nada. Cuando deje de estarlo, sale
una línea roja de página con los crones exactos:

```
45 3 * * *  ->  45 4 * * *   (04:45 · ventana del reset)
50 3 * * *  ->  50 4 * * *   (04:50 · ventana del reset)
15 6 * * *  ->  15 7 * * *   (07:15 · tras el reset)
```

Verificado ejecutándolo con dos fechas: el 10/09 devuelve `null`, el 15/11 devuelve
el aviso con esos tres crones y `desfaseMadrid = 60`.

**Un matiz sobre lo que pediste.** Dijiste «que avise cuando un disparo externo
llegue *sistemáticamente* a una hora distinta». Eso necesitaría un histórico de
horas de llegada que hoy no guardamos, y además sólo lo detectaría *después* de
varios ciclos ya perdidos. La versión que he puesto es determinista y salta **el
mismo 25 de octubre, antes del primer disparo malo**: la causa no es una deriva,
es que Madrid cambia de zona, y eso se puede preguntar. Si aun así quieres la
detección por observación, hay que empezar a guardar las horas de llegada y te lo
digo antes de hacerlo.

---

## 3. Doctrina 35 — y un fallo vivo que salió al aplicarla

Añadido el caso motivador a la regla. Y al escribir la guardia que prohíbe
desfases a mano, saltó uno que estaba puesto:

```js
} catch {
  // Sin `Intl` no se inventa: se usa el horario de verano
  // europeo, que es lo que rige diez meses al año.
  return 120;
}
```

El comentario decía «no se inventa» y justo debajo se inventaba. **Acierta diez
meses al año y falla exactamente los dos en que el desfase importa**, callado. Es
la 35 y la 36 a la vez: un desfase escrito a mano, y un defecto benigno tapando un
«no se sabe». Ahora `desfaseMadrid` devuelve `null` y quien llama devuelve su forma
de «no se sabe» en vez de colocar una hora inventada.

**Lo que sí puede seguir escrito** es `CET_DE_CRON_JOB = 60`, y la guardia lo
permite explícitamente: CET es **+1 por definición y no cambia nunca**. Lo que
cambia es Madrid — y por eso Madrid se pregunta y CET se escribe.

---

## Guardias

`src/analysis/test_los_relojes_v1.py` — **6/6**:

- `test_la_cadencia_sale_del_cron` — el YAML manda sobre los dos espejos
- `test_ningun_texto_lleva_la_cadencia_escrita_a_mano`
- `test_el_ciclo_no_se_pone_rancio_antes_de_tiempo`
- `test_la_compensacion_de_cron_job_esta_escrita_donde_se_ve`
- `test_el_bot_avisa_del_cambio_de_hora` — **ejecuta** el aviso con verano e
  invierno
- `test_ningun_desfase_horario_escrito_a_mano`

Van ya **tres** guardias que tropezaron leyendo el comentario que *cuenta* el
incidente como si fuera código vivo. Ésta comparte el mismo `_sin_comentarios()`:
una guardia que obligue a borrar la explicación del fallo para pasar hace daño.

---

## Estado

- Verja: **111/111**
- Pantalla: pinta igual (`inicio 16.117`)
- Rama `main`, **sin push**
