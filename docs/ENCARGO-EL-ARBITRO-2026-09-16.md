# ENCARGO — EL ÁRBITRO

**Fecha:** 2026-09-16
**Rama:** `arbitro/quien-tenia-razon`
**Parte de:** `docs/resultado-bolsillo-2026-09-15.md`.

---

## Primero, lo que ya te puedo contestar del bloque 5

No hace falta que lo investigues, está mirado:

- El almacén vive en **`data/autopilot/price_history.json`**
  (`price_history_store.py:48-57`).
- **`data/autopilot` sí está en la lista de rutas cacheadas** del workflow
  (líneas 70-82). En producción persiste entre ciclos.
- `scripts/prune_github_state.py` poda snapshots y el log del autopilot.
  **No toca `price_history.json`.**
- Retención 45 días, que tú subiste a 60. Correcto.

O sea: **la fontanería está bien.** Las 72 pujas "sin precio de aquel momento"
son casi con seguridad pujas anteriores a la fecha en que se estrenó el almacén,
y eso se cura solo con el tiempo.

Lo que falta no es fontanería, es **visibilidad**: nadie sabe cuántos días de
histórico tiene producción ahora mismo. Publica en el dashboard una línea sola —
**días de histórico y fecha del registro más antiguo**— y dila en el informe. Si
son 20 días, el retrotest puede volver a correr ya con horizontes de 5, 7 y 10.

Y aprovecho para reconocer lo mío: yo di por buena la premisa de los 6 días y era
tu copia local caducada, no el sistema. La cazaste bien.

---

## BLOQUE 1 — El árbitro: ¿quién tenía razón?

Este es el bloque importante, y es el que más falta hace ahora mismo.

Llevamos cuatro noches construyendo una máquina de valorar cada vez mejor. Cada
noche la máquina concluye, con razón medida, **que no hay que comprar nada**.
Mientras tanto Pollo compró siete jugadores por 21.198.020 € y va primero.

Una de estas dos frases es verdad, y no sé cuál:

- **A)** Pepe tiene razón, Pollo está tirando el dinero, y en unas semanas se
  verá.
- **B)** El modelo de Pepe es demasiado exigente, se está perdiendo un mercado
  que sí paga, y la diferencia de 35.520.000 € en valor de plantilla es la
  factura.

**Se puede saber cuál, y sale casi gratis.** Esas siete compras tienen precio de
compra conocido y precio de mercado hoy. Lo mismo con nuestros rechazos.

### 1.1 — El marcador de Pollo

Coge las siete compras y compara lo pagado con lo que valen hoy:

| Jugador | Pagado |
|---|---:|
| Gerard Moreno | 6.450.007 |
| Pubill | 6.360.006 |
| Natan | 3.010.007 |
| Bardeli | 1.877.000 |
| Camavinga | 1.777.000 |
| Ratkov | 1.447.000 |
| Riki Rodríguez | 277.000 |

Publica, por jugador y en total: euros ganados o perdidos, porcentaje, y días
transcurridos. Y lo mismo con las ventas de Luismi_Haz (~14,4 M al Computer):
**¿acertó vendiendo?**

### 1.2 — El libro de rechazos

Esto es lo que de verdad nos juzga a nosotros. Cada objetivo que Pepe rechazó
—con su motivo y su fecha— contra lo que ha hecho su precio desde entonces.

La casa ya sabe hacer esto: es la misma idea que el libro de precisión de las
fuentes, que puntúa a FutbolFantasy con Brier. Aplícala a nuestras propias
decisiones. Si el almacén tiene 20 o 30 días, hay muestra para empezar.

Publícalo con la misma honestidad que el retrotest: cuántos rechazos, cuántos
subieron, cuántos bajaron, mediana del movimiento, y **cuánto habríamos ganado o
perdido comprándolos todos**.

### 1.3 — El veredicto, escrito

Una sección corta que diga cuál de las dos frases sostiene la medición, o que
diga que la muestra todavía no permite decidir. **Las tres respuestas son
válidas.** Lo que no vale es seguir otra noche sin preguntarlo.

Y si sale que el modelo es demasiado exigente, **no aflojes nada esa misma
noche**: dilo, propón qué tocarías, y lo decido yo. Si sale que Pollo está
perdiendo dinero, también quiero saberlo, porque entonces dejamos de perseguirle
y jugamos nuestro juego con calma.

---

## BLOQUE 2 — El tramo `> 1 %/día` no tiene techo, y eso aplasta la información

En la tabla del retrotest el tramo de arriba es **`> 1 %`, sin límite superior**.
Ahí dentro conviven un jugador que sube el 1,01 % diario y uno que sube el
4,85 %. Se les asigna el mismo rendimiento.

Se ve en el resultado de ayer: **Gorosabel (4,849 %/día) y Roro Riquelme
(1,666 %/día) aterrizan los dos exactamente en 1,80 %.** Tres veces la tasa, el
mismo valor. Eso no puede estar bien.

Parte el tramo de arriba: **1-2 %, 2-4 %, > 4 %**, con el mismo corte de 30
operaciones. La celda buena tenía 142, así que hay de dónde. Si alguno de los
tres subtramos no llega a 30, sale marcado como insuficiente igual que los demás
y no pasa nada.

---

## BLOQUE 3 — Recortar el mecanismo, no el número

Tu recorte es honesto y prefiero pecar por ahí, pero tal como está **tira a la
basura el dato más fiable que tenemos del jugador: su tasa de subida actual**.
Sustituye su rendimiento por el de otro jugador distinto que estaba en su mismo
tramo (ancho, ver bloque 2) con una racha más corta.

Lo que nos falta de las rachas largas es la **magnitud**. Lo que **sí** tenemos
medido es la **probabilidad de continuación**: 73,8 % para rachas de 3 días o
más, sobre 351 casos. Tú mismo lo citas.

Así que la alternativa es:

```
ganancia = precio × tasa_PROPIA × horizonte × P(continuación de SU racha) × (1 − margen)
```

usando el 0,738 medido para las rachas largas en vez de fabricar la magnitud.
Mantiene la tasa del jugador, castiga la racha larga por donde está medido el
castigo, y no inventa nada.

**Cuál de los dos es correcto lo decide el dato, no ninguno de los dos.** Dentro
de la muestra tienes rachas de 1 y de 2 días: mira si la caída de rendimiento
entre ellas se explica por la caída de continuación o por una caída de la tasa
misma. Si es continuación, mi fórmula; si es la tasa, la tuya. Si no se puede
distinguir con esa muestra, **quédate con la tuya** —es la conservadora— y
escríbelo.

Y en cualquier caso: publica las dos cifras una al lado de la otra en pantalla,
para poder mirarlas cuando haya más histórico.

---

## BLOQUE 4 — El commit que no hiciste

Dices que había ya un `1459222` con tu mismo mensaje conteniendo solo el fichero
del encargo, y que no fuiste tú. Te creo, y es raro.

Míralo antes de nada: `git show 1459222 --stat` y el autor y la fecha. Lo más
probable es que sea de la sesión anterior o mío desde el puente, pero quiero
saberlo escrito, porque un commit de origen desconocido en un repositorio que
mueve dinero es exactamente la clase de cosa que no se deja pasar "porque
seguramente no es nada".

Si resulta ser inocuo, dilo y seguimos. Si no lo puedes explicar, dilo también y
paro yo la fusión.

---

## Reglas de la casa

1. Rama `arbitro/quien-tenia-razon`. `main` no se toca.
2. Verja encadenada, sin excepciones:

   ```powershell
   python scripts/run_validation_gate.py
   if ($LASTEXITCODE -eq 0) {
       git add -A
       git commit -m "arbitro: quien tenia razon"
   } else {
       git reset --hard origin/main
       Write-Host "VERJA EN ROJO - nada que subir"
   }
   ```

   Tú no empujas.
3. `git status` antes de commitear, y en el informe qué entra.
4. Mide contra `diagnostico/status.json`.
5. No toques `.github/workflows/bordalas-live.yml` ni
   `MAX_SINGLE_SPECULATION_PERCENT`.
6. **Este encargo es de medir, no de aflojar.** Ningún umbral se mueve esta
   noche, salga lo que salga el bloque 1.
7. Si la medición contradice el encargo, gana la medición.

---

## Informe

- días de histórico que tiene producción y fecha del registro más antiguo;
- el marcador de Pollo, jugador por jugador y en total;
- el marcador de Luismi vendiendo;
- el libro de rechazos, con el "cuánto habríamos ganado o perdido";
- el veredicto: A, B, o "todavía no se puede decir";
- el tramo de arriba partido, con las muestras;
- si la caída por racha es continuación o tasa, y con qué te quedaste;
- qué es el commit `1459222`;
- lo que no hiciste y por qué.
