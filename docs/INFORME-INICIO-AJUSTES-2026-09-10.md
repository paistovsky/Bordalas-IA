# INICIO — dos ajustes

**10/09/2026** · verja 107/107 · sin push

---

## 1. La tira baja a seis, y la pastilla lleva las dos cosas

`● foto de hace 6 min · próximo ciclo en 25:31`

Edad en **minutos enteros**, cuenta atrás en **MM:SS**. Y si el ciclo no llega,
la pastilla lo dice —«debería haber entrado hace X»— y se pone en rojo.

**Fuera de la tira:** «Foto» y «Próximo ciclo». La tira queda en seis: Jornada ·
Deuda máxima · Reset · Cierre de la jornada · XI · Pujas puestas.

El «hace 7.0107 min» venía de `minutesOld`, que devuelve fracción y se imprimía
cruda. Ahora `minutosDeLaFoto` da minutos enteros — y además le pone la zona a la
marca, que `minutesOld` la leía como hora **local**.

**Y ahí había un fallo vivo que la guardia destapó:** la tira seguía usando esa
lectura local para descontar el **cierre de la jornada**. Para quien no estuviera
en Madrid salía con dos horas de menos, sin avisar. Doctrina 35, el mismo del día.
Arreglado.

---

## 2a. Por qué «Posibles cambios» sigue vacío

**No es un fallo, y no es una foto vieja. El ciclo aún no ha corrido con el código
nuevo.**

| | |
|---|---|
| Último ciclo | **13:32:01 UTC** = 15:32 Madrid, sobre `7ab0129` |
| `8335c4f` llegó a `origin/main` | **13:35:40 UTC** = 15:35 Madrid |
| Diferencia | el código aterrizó **3 min 39 s después** de arrancar el ciclo |
| Ahora | 13:45 UTC = 15:45 Madrid |
| Próximo ciclo | **14:07 UTC = 16:07 Madrid**, a 22 minutos |

El ciclo de las 16:07 **no ha corrido todavía**: está en el futuro. El de las 15:32
corrió con código que no tenía banquillo.

**Dos cosas que despistan y conviene descartar:**

- `dashboard/data/status.json` en local es del **06/09**. No prueba nada: ese
  fichero **no está versionado**. El ciclo lo genera en CI y lo sube a Cloudflare
  KV, nunca lo devuelve al repo. La copia local siempre parecerá vieja.
- Los ocho últimos ciclos salieron **todos en verde**. No hay nada roto que buscar.

**Y la cadena de publicación está probada, no supuesta.** La verifiqué de punta a
punta con un extremo fabricado:

```
build_lineup["bench"] → lineup_monitor["lineup"] → lineup_state["lineup"]
    → compact_lineup → posibles_cambios
```

El banquillo llega entero, con su `reason_text`. Cuando entre el ciclo de las
16:07, el panel se llena.

---

## 2b. La fila entera

Una fila por suplente, y contesta sola:

| columna | qué trae |
|---|---|
| **JUGADOR** | nombre, escudo del club y posición |
| **TIT.** | su probabilidad de ser titular **en su equipo** |
| **POR QUÉ ESTÁ FUERA** | castellano llano, del corte del motor |
| **LE QUITARÍA EL PUESTO A** | el titular concreto, con nombre, escudo y su tit. % |
| **EL XI** | lo que se gana o se pierde en el cambio |

Ordenadas por cercanía a entrar, la más cerca arriba. **En verde la fila del que ya
mejoraría el once**, con filete verde a la izquierda.

**Nada de esto es un cálculo nuevo.** El rival directo es el **peor titular de su
posición** —que es justamente a quien está más cerca de quitarle el puesto— y la
diferencia es la misma con la que el motor eligió a uno sobre otro. Lo único que
hice fue dejar de tirar esos dos valores al publicar.

El `tit. %` usa **la misma cadena que las tarjetas del once**
(`starter_probability ?? jp_confidence`), para que un jugador no salga con dos
números distintos en dos sitios. Y **sin dato no es cero**: pinta «sin dato», porque
un «tit. 0 %» hace creer que no juega, que es lo contrario de no saberlo.

---

## Guardias

`test_posibles_cambios_v1` — **15/15**. Cuatro nuevas: la tira no duplica la
pastilla y se queda en seis; la edad va en minutos enteros; cada suplente trae la
fila entera con el rival y su probabilidad; sin dato no se pinta un cero.

**Una nota sobre las guardias mismas.** Van dos que tropiezan con lo mismo: leen el
comentario que *cuenta* el incidente —`state or ABIERTO`, `minutesOld`— como si
fuera código vivo. Ahora hay un `_sin_comentarios()` compartido. Una guardia que
obligue a borrar la explicación del fallo para pasar es una guardia que hace daño:
la próxima persona se encuentra el arreglo sin el motivo.

---

## Estado

- Verja: **107/107**
- `vite build` hecho, `dist` copiado a `dashboard/`
- Rama `main`, **sin push**
- No se tocó el XI, ni la clasificación, ni la cronología
