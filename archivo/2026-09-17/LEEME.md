# Archivo del 17/09/2026 — cuatro libros locales

**Esto NO es un libro. Producción no lo lee y nadie lo escribe.** Son copias
congeladas, guardadas aquí para que no se pierdan mientras producción arranca sus
libros limpios.

## Por qué no se promueven a libro bueno

Las cuatro copias salen de vueltas **locales**, en la máquina del dueño, y **la verja
escribe en nueve libros**. No sabemos si están limpias, y subirlas las convertiría en
la verdad de producción sin haberla comprobado. Producción arranca el suyo vacío.

## Qué hay dentro, de verdad

Cuidado con el tamaño aparente: son ficheros JSON impresos con sangría, así que
**«líneas de texto» no es «registros»**. Lo que hay es mucho menos de lo que parece:

```
fichero                         líneas   contenido real
libro_de_renovaciones.jsonl         11   11 renovaciones del 10/09 (Dituro, Jonny,
                                         Jutglà, Zubeldia, Djené, Pablo Ibáñez,
                                         Manu Sánchez, Pablo Durán)
pujas_bajo_precio.jsonl              1   1 observación: Aubameyang, 10/09
scout_accuracy_ledger.json         172   8 predicciones, TODAS del 05/09, todas de
                                         prensa y todas sin resolver
source_accuracy_ledger.json        649   2 jornadas (17 y 16 jugadores), ninguna
                                         resuelta
```

Total real: **11 renovaciones + 1 puja + 8 predicciones + 33 pronósticos de
titularidad**. No son 821 registros; son 821 líneas de texto.

## Qué proporción viene de la verja

```
libro_de_renovaciones.jsonl     0 %   la verja no lo escribe (medido ejecutando)
pujas_bajo_precio.jsonl         0 %   tampoco
source_accuracy_ledger.json     0 %   tampoco
scout_accuracy_ledger.json      ?     SÍ lo escribe `test_ojeador_informe_v1`
```

De los cuatro, **solo `scout_accuracy_ledger.json` lo toca la verja**, y no se puede
separar línea a línea: las 8 predicciones son todas del 05/09, de prensa y sin
resolver, y la guardia escribe con esa misma forma. **Se archiva entero y se dice.**

## Lo que de verdad se perdió, y no está aquí

El 15/09 el libro de **producción** tenía del orden de **16.000 predicciones**
—5.993 en `pending` y 2.760 en `flat`—. Ese libro vivía únicamente en la caché del
runner y **nunca llegó a git**. Aquí no está y no se puede recuperar.

El libro local ya tenía 8 predicciones el 15/09, y sigue teniendo 8: **en local no se
ha perdido nada**. Lo que se perdió fue lo de producción, y se perdió porque
`scout_accuracy_ledger.json` no estaba en la lista de guardado hasta hoy.
