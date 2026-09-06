# EL PLAN

**Versión 2 — 2026-09-22.** Sustituye a la versión del mismo día.

La estrategia general de Pepe, con los dos vídeos dentro, puesta en orden de
trabajo. La doctrina (`docs/DOCTRINA.md` v1.5) dice **qué**; esto dice **en qué
orden** y **cómo sabremos si funciona**.

---

## La estrategia, en cinco frases

1. **Los puntos salen del once, y solo del once.** Once plazas, más delanteros y
   medios con gol que defensas, nunca sin portero de repuesto, y el que tira los
   penaltis y las faltas vale más de lo que parece.
2. **El dinero sale de la rueda**, y es otro juego: se compra al que **se está
   revalorizando** —da igual que no vaya a jugar—, se aguanta tres días y se
   vende al Computer, que paga un +1,7 % sobre mercado.
3. **Se puede ir en rojo de lunes a jueves.** El viernes se vende y se vuelve a
   verde para poder puntuar. Esa es la única fecha que importa.
4. **La ventaja está en llegar antes.** La rampa te dice quién ya sube; la
   noticia te dice quién subirá mañana. El que compra con la noticia se lleva la
   subida entera.
5. **No te cases con nadie.** Si empieza a caer, fuera. Ya se recompra.

Nada de esto es opinión mía: son los cinco consejos del vídeo de La Media
Inglesa y los siete del de MANYOTUBEPIC, cruzados con lo que hemos medido en
esta liga.

---

## El número que juzga todo

```
13 puntos con Pollo  ÷  35 jornadas  =  0,371 por jornada
```

Y dos cifras publicadas cada jornada: **puntos dejados en el banquillo** (sola
valió 8 en una jornada) y **puntos por jornada contra Pollo**. **Si en tres
jornadas no se mueven, nada de esto importa.**

---

## Regla cero: lo que está en una rama no juega

Cuatro ramas encadenadas sin fusionar. La calidad medida, la portería, los
intocables retirados, la sonda de pujas. **La mayor distancia entre lo que
sabemos y lo que Pepe hace sigue siendo una fusión de git.**

---

## La cola

### 1. ~~¿Es `NO_MEJORA_EL_ONCE` un rechazo terminal?~~ — RESUELTO 23/09, y era falso

**La sospecha estaba mal y salía de una etiqueta mal leída.** `SIN_VALOR` no
significa "no mejora el once": significa que ninguna vía lo quiere, y cada
objetivo publica el veredicto de todas. Los doce estaban evaluados por todas.
Mueren porque **ocho caen y cuatro están planos, ninguno sube**. La rueda los
rechaza bien.

### 2. ¿Cuánto puede dar la rueda? — MEDIDO 23/09

| Escenario | Al mes |
|---|---:|
| optimista (lo medido) | 1.555.885 € |
| prudente (la mitad) | 997.714 € |
| pesimista (un cuarto) | 718.629 € |

**Es la liga, no un entretenimiento.** Lo limita el capital (2,50 M disponibles
contra 7,79 M que cabrían en ocho fichas), no las fichas ni el tope.

**Pero es un techo y hoy no se alcanza: no hay qué comprar.** De los veinte del
escaparate, once cayendo, uno en el tramo 2-4 % y **ninguno por encima del 4 %**.
Eso explica por sí solo las semanas sin fichar. **La pregunta que decide todo
pasa a ser: ¿el universo comprable son solo los ~20 diarios del Computer, o los
521?**

### 3. Balón parado

El truco nº 1 de un vídeo y el nº 5 del otro. Sigue apagado, cinco noches
aplazado, y no depende de nada de lo anterior. **El valor está en el lanzador
barato**, no en el crack que además los tira.

### 4. Encender la rueda

Solo después de 1 y 2. La vía de comerciar libre del filtro del once, volumen en
vez de una operación perfecta, deuda de lunes a jueves y verde el viernes.

Sin tocar el 3 % por consejo: **si el volumen paga más que el margen, que lo diga
el retrotest** comparando cartera de muchas operaciones finas contra pocas
gruesas, con nuestro capital.

### 5. La intel — llegar antes que la rampa

Las dos mitades:

- **El ranking de los 521** por euros/punto, con **quién es el dueño** y **cuánto
  de esos puntos es sostenible**. Sin la primera columna es una fantasía.
- **Las noticias de cesiones y traspasos**, sin filtrar por precio. Caché diaria
  tras el reset de las 07:00, cruce prensa→jugadores.

### 6. Los remates

- Centrocampistas **con gol**, separados de los de contención.
- Recién ascendidos: de marcador a factor cuando haya muestra (hoy n=36).
- **Al lesionado, fuera rápido**: tramo propio en la cola de ventas.
- Dos porteros del mismo club, cuando salga a cuenta.

---

## Lo que NO está resuelto

- **Explicamos el 23,5 % de los puntos de un jugador.** Tres cuartas partes de lo
  que decide la liga siguen sin modelo.
- **El +4,47 % se midió en una semana de agosto**, la más rara del año.
- **Los recién ascendidos suben más con n=36.** Marcador, no factor.
- **Las pujas de los rivales son invisibles.** Cerrado en negativo.
- **Un dato con dos nombres nos ha mordido cuatro veces.**

---

## Cómo se trabaja

Una rama por encargo, `main` limpio. La verja encadenada con
`if ($LASTEXITCODE -eq 0)`, el push lo da el dueño. Cada arreglo con su guardia,
nombrada por el incidente real. Ninguna guardia lee `data/`. Ninguna función
cambia de forma según los datos. Ningún umbral sin un número detrás.

**Y si la medición contradice el plan, gana la medición.** Ha pasado seis veces
en dos semanas y las seis tenía razón la medición.
