# El margen esperado, y la rendija encendida

**11/09/2026** · verja 111/111 · `en_vivo = True` · sin push

---

## El caso de Starfelt: cuál aplica, y por qué

```
Starfelt · defensa · 2.150.000 · cayendo −2,01 %/día
prima de puja +0,28 % (tramo bajo de la curva calibrada en vivo)

coste          2.150.000 × 1,0028  =  2.156.020
precio al día  2.150.000 × 0,9799  =  2.106.785
```

| prima de reventa | oferta esperada | margen | ¿llega al suelo? |
|---|---|---|---|
| mediana de la liga, +2,91 % | 2.168.092 | **+0,56 %** | **NO** |
| **de su posición, defensa +3,67 %** | 2.184.104 | **+1,30 %** | **sí** |

**Aplica la de su posición.** El Computer no recompra igual a un defensa que a un
delantero —medido: DEF +3,67 · POR +3,26 · MED +2,85 · DEL +1,80— así que la
mediana de la liga, que mezcla las cuatro, es para un defensa un **estimador
sesgado a la baja**: le aplica el promedio de un grupo en el que él es de los que
más recuperan.

Y ojo a lo que separa el suelo: **+0,56 % no llega al 1 %**, así que con la mediana
la operación esperaría una oferta que nosotros mismos rechazaríamos. Con la prima
de defensa, +1,30 %, sí se puede cerrar.

### La cautela, que hay que decirla

Esos 34 casos repartidos en cuatro posiciones son **8 o 9 por posición**. La prima
por posición es el estimador **correcto** y a la vez el más **débil**. Por eso el
margen se publica **por partida doble** —el de su posición y el de la mediana— y no
sólo el que conviene: elegir el estimador más favorable para que una operación
justa pase es la forma más cómoda de hablarse a uno mismo para entrar en un mal
negocio.

## Lo que el margen cambia, que no es poco

**El orden se da la vuelta.** Con sólo la preferencia por posición, los primeros
eran los defensas. Con el margen, el primero es **Berenguer, delantero**:

| | pos | precio | ritmo | margen | con mediana | ¿suelo? |
|---|---|---|---|---|---|---|
| **Berenguer** | DEL | 3.180.000 | **+4,75** | **+6,33 %** | +7,49 % | sí |
| **Marcos Alonso** | DEF | 3.590.000 | +0,00 * | **+3,38 %** | +2,62 % | sí |
| Cáceres | DEF | 1.540.000 | +0,00 * | +3,38 % | +2,62 % | sí |
| Sotelo | MED | 1.630.000 | +0,00 * | +2,56 % | +2,62 % | sí |
| Gulácsi | POR | 1.590.000 | −1,26 | +1,68 % | +1,33 % | sí |
| Nico Williams | DEL | 8.000.000 | +0,00 * | +1,52 % | +2,62 % | sí |
| Isaac Romero | DEL | 2.400.000 | +0,00 * | +1,52 % | +2,62 % | sí |
| Starfelt | DEF | 2.150.000 | −2,01 | +1,30 % | +0,56 % | sí |
| Robbie Ure | DEL | 3.590.000 | −1,01 | **+0,49 %** | +1,59 % | **NO** |
| ~~Hugo González~~ | | | | **−1,89 %** | | fuera |

`*` ritmo **supuesto** (mediano del mercado, **+0,00 %/día**), no medido — 5 de 11.

Un delantero que sube un 4,75 % al día bate a un defensa parado, aunque su prima de
reventa sea la peor de las cuatro. **Eso es exactamente lo que el margen añade y la
preferencia por posición no veía.**

## Un hueco que sale al medirlo, y que dejo señalado sin cerrar

**Robbie Ure entra con +0,49 % y no llega al suelo.**

El suelo de venta es `coste + 1 %`, y el margen es `oferta/coste − 1`. Así que
`margen ≥ 1 %` **es exactamente** «la oferta esperada supera el suelo». Un margen
positivo pero por debajo del 1 % es una operación que, por construcción, **espera
una oferta que rechazaríamos**: el viaje entra y no puede cerrarse con ganancia.

El filtro que pediste es «margen negativo fuera», y **no lo he cambiado**. Lo que he
hecho es publicar `llega_al_suelo` en cada fila y pintarlo en rojo en el panel, para
que la diferencia se vea. Si quieres que el umbral pase de `> 0` a `≥ 1 %`, es una
línea — pero es mover un umbral y eso lo decides tú.

**Y un aviso sobre el supuesto:** el ritmo mediano del mercado hoy es **+0,00 %/día**
exacto. Con esa suposición el margen se reduce a «prima de posición menos prima de
puja», que es una cuenta muy plana. Cinco de los once descansan en eso, y por eso
van marcados con `*` en la pantalla y contados aparte en el resumen.

---

## EL ENSAYO FINAL — con margen, datos de hoy

```
EL CUPO:  2 (ESTRENO)      TOPE DE PUJA 16.756.883
ritmo mediano del mercado (supuesto): +0,00 %/día
11 candidatos -> 9 con margen positivo -> 2 entran por cupo
```

| | coste | listaría a | suelo de cobro | margen |
|---|---|---|---|---|
| **Berenguer** (DEL) | 3.188.904 | 3.657.000 | 3.211.800 | **+6,33 %** |
| **Marcos Alonso** (DEF) | 3.600.052 | 4.128.500 | 3.625.900 | +3,38 % |
| **compromete** | **6.770.000** | | | de un tope de 16.756.883 |

Marcos Alonso entra con el ritmo **supuesto**: su margen de +3,38 % descansa en
suponer que su precio no se mueve. Si resultara caer como Starfelt, su margen real
sería ~+1,3 %.

---

## Encendida

`en_vivo = True`. Se apaga **sin desplegar** con `RENDIJA_APAGADA=1`, igual que
`BORDALAS_SIN_SUBASTA` y `BORDALAS_VARA_PLANA` — el día que haya que pararla no se
puede depender de un commit. Hay guardia que comprueba las dos cosas: que está
armada, y que el interruptor la apaga.

Lo demás sigue exactamente igual: zona de silencio, cupo de estreno 2, dos
escrituras por vuelta, silencio absoluto tras una emergencia, las cinco
prohibiciones de `que_cobrar`, y el apagado automático tras 10 viajes cerrados con
mediana negativa.

## Guardias

`src/analysis/test_la_rendija_v1.py` — **24/24**. Las seis nuevas: el caso de
Starfelt con los dos estimadores, que el margen **no** es la compuerta de ritmo
(con un caso que cae y entra, y uno que sube y no), que el margen negativo no
entra, que sin ritmo se usa el supuesto **y se dice**, que se publica si llega al
suelo, y que la rendija está armada y se apaga con el interruptor.

---

## Estado

- Verja: **111/111**
- `en_vivo`: **True** (apagable con `RENDIJA_APAGADA=1`)
- Rama `main`, **sin push**
