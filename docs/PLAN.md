# EL PLAN

**2026-09-22** — En qué orden se le enseña a Pepe lo que sabemos, y por qué ese
orden.

Acompaña a `docs/DOCTRINA.md` v1.4. La doctrina dice **qué** hay que hacer; esto
dice **en qué orden** y **cómo sabremos si funciona**.

---

## El número que juzga todo esto

```
13 puntos de diferencia con Pollo  ÷  35 jornadas  =  0,371 por jornada
```

Cuatro décimas. Todo lo que sigue se mide contra eso, y con dos cifras que se
publican cada jornada:

1. **Puntos dejados en el banquillo** — lo que hizo el once que pusimos contra el
   mejor once posible con la plantilla que teníamos. Sola, esta cifra ya valió
   **8 puntos en una jornada**.
2. **Puntos por jornada contra Pollo.**

**Si en tres jornadas esas dos cifras no se mueven, nada de lo que estamos
haciendo importa**, por bonito que sea el código. Este plan se juzga ahí y en
ningún otro sitio.

---

## Regla cero: lo que está en una rama no juega

Hay **tres ramas sin fusionar**. Todo el trabajo de la semana —la calidad medida,
la portería, la derogación de los intocables, la sonda de pujas— está en el
disco, no en producción. Pepe hoy juega con el cerebro de hace cuatro días más
los factores de posición.

**La mayor distancia entre lo que sabemos y lo que Pepe hace es una fusión de
git.** Antes de construir nada nuevo, subir lo construido.

---

## La cola

Ordenada por lo que mueve el marcador, no por lo que apetece.

### 1. Subir lo que ya está hecho

Las tres ramas. Con una verificación antes: **el veredicto sobre la oferta de
21.099.500 € por Yamal con la lista de intocables ya retirada.** Si sale
cualquier cosa distinta de "no vender", no se fusiona.

### 2. Balón parado (regla 2)

El truco nº 1 del vídeo y sigue apagado. Un lanzador de penaltis convierte un −2
en nueve puntos. El módulo existe; lo que falta es la fuente, y las tres webs que
ya leemos cada ciclo lo publican.

**Primero es lo más rentable, y va sin medir por delante:** no tenemos el dato
para medirlo hasta que lo tengamos. Se enciende como bono marcado como decretado,
y se mide en cuanto haya jornadas.

### 3. El ranking de la liga por euros/punto (regla 10)

Lo que el dueño enseñó el 22/09: **Biwenger ya publica los 521 jugadores
ordenados por puntos, con su precio.** La cuenta que sale de ahí:

| | € por punto |
|---|---:|
| Camello (4,30 M, 48 pts) | **89.583** |
| Aubameyang (11,21 M, 44) | 254.773 |
| Raphinha (18,80 M, 61) | 308.197 |
| Yamal (21,21 M, 45) | 471.333 |

Camello rinde **cinco veces** lo que Yamal por euro.

Pepe hoy solo juzga a los ~20 del escaparate. Con esta tabla dentro pasa de
reaccionar a **saber a quién quiere**. Dos columnas que la pantalla no tiene y
son las que la hacen útil:

- **quién es el dueño** — si nadie lo vende, no es una alternativa, es una
  fantasía (la lección de los porteros: los titulares valen 2,65-5,74 M y
  **ninguno estaba en venta**);
- **cuánto de esos puntos es sostenible** — Camello lleva 9,6 por jornada siendo
  un delantero de 4,3 M: o ha dado un salto, o está en racha, y eso lo distingue
  la calidad medida.

### 4. Encender la calidad medida (regla 6)

Construida y sin encender: 19,1 % → 23,5 %. Va después del ranking porque es lo
que le da sentido: sin ella, la tabla del punto 3 ordena por puntos pasados.

Con interruptor de una línea y con el marcador de cada jornada.

### 5. Centrocampistas ofensivos (regla 5)

Separar el mediocentro del mediapunta dentro de la línea de medios. El factor de
hoy (×1,147) los trata igual. **Un factor encima de otro factor**: primero hay
que ver cómo va el primero.

### 6. Las noticias de los baratos (regla 10, la otra mitad)

Anticipación en vez de momento: el que subirá mañana porque el Málaga lo busca.
Necesita la caché diaria de las ~570 fichas tras el reset de las 07:00 y el cruce
prensa→jugadores. Tres noches aplazado, y con razón: hacerlo mal revienta el
ciclo.

### 7. Rotar (regla 14)

Vender para comprar lo que ya sabemos que compensa. Va el último **a propósito**:
sin el ranking del punto 3, rotar es mover dinero sin saber hacia dónde. Amatucci
a +0,57 —proyección contra medición— no es una operación, es movimiento.

---

## Lo que NO está resuelto, y conviene no olvidarlo

- **Explicamos el 23,5 % de los puntos de un jugador.** Tres cuartas partes de lo
  que decide la liga siguen sin modelo. Todo lo de arriba se mueve dentro de ese
  cuarto.
- **El +4,47 % de la rampa se midió en una semana de agosto.** Es la semana rara
  del año: mercado recién cerrado y precios recolocándose.
- **Los recién ascendidos suben más, con n=36.** Marcador, no factor.
- **Las pujas de los rivales son invisibles.** Comprobado y cerrado: hay que
  seguir estimando.
- **Un dato con dos nombres nos ha mordido cuatro veces.** `in_lineup` contra
  `is_starter` dejó al único portero sin proteger.

---

## Cómo se trabaja

No cambia:

- una rama por encargo, `main` limpio;
- la verja encadenada con `if ($LASTEXITCODE -eq 0)`, el push lo da el dueño;
- cada arreglo con su guardia, nombrada por el incidente real;
- ninguna guardia lee `data/`;
- ninguna función cambia de forma según los datos;
- ningún umbral sin un número detrás;
- **y si la medición contradice el plan, gana la medición.** Ha pasado seis veces
  en dos semanas y las seis tenía razón la medición.
