# `test_la_pantalla_pinta_v1`, retirada de la verja

**10/09/2026, de madrugada** · verja 110/110 · sin push

---

## Lo que se ha hecho, y nada más

1. **Fuera de la lista** de `scripts/run_validation_gate.py`. Comentada, no
   borrada.
2. Declarada en una tabla nueva, **`RETIRADAS`**, arriba del propio fichero de la
   verja, con motivo y fecha. Una guardia comentada dentro de una lista de 200
   líneas se vuelve invisible en dos días; ahí arriba, no.
3. Verja **110/110**, comprobada también **sin** `dashboard/data/status.json`, que
   es el estado exacto del runner.

**Una corrección sobre lo que pediste:** intenté apuntarla en `DEUDA` y esa tabla
la rechazó, con razón. `DEUDA` significa *«esta guardia lee estado mutable»*, y
ésta ya no lo hace — la arreglé esta noche con la muestra versionada. Meterla ahí
habría sido mentir sobre por qué está exenta. Por eso lleva lista propia:
`RETIRADAS` significa otra cosa, *«esto no se está comprobando»*, y cada entrada es
una promesa a plazo.

**Mientras esté ahí, la pantalla NO se comprueba en CI.**

---

## El diagnóstico: ya está, y no hacía falta el log

Miraste bien: era `node_modules`. Pero no que llegara incompleto — llega entero.
Es que **el binario que lleva es de la plataforma equivocada**.

```
runs-on: ubuntu-latest

dashboard-v8/node_modules/@esbuild/   ->   win32-x64   (y sólo eso)
                                            esbuild.exe
```

esbuild no es JavaScript: es un **binario nativo por plataforma**. El repo tiene
versionado `@esbuild/win32-x64/esbuild.exe`, que es tu Windows. El runner es Linux
y necesita `@esbuild/linux-x64`, que **no está en el repo**.

Cuando el paquete de la plataforma falta, el lanzador de esbuild lanza y Node
imprime su pie de versión **después** del error. De ahí que el log sólo dejara
`Node.js v24.20.0`: las líneas que importaban estaban justo encima, y son las de
esbuild diciendo que no encuentra su binario.

Encaja también con por qué falló **distinto** las dos veces: el primer intento
moría antes, al no encontrar la foto (1/2); el segundo ya encontraba la muestra,
llegaba a construir el bundle y moría en esbuild (2/3).

### Por qué el resto del dashboard sí funciona en CI

Porque el workflow de deploy hace `npm ci`, que **descarga el binario de Linux**.
La verja del ciclo no hace `npm ci` — se apoya en el `node_modules` versionado — y
ahí sólo hay el de Windows.

### Salida de CI, tal cual, para el registro

```
test_la_pantalla_pinta_v1
  ...
  Node.js v24.20.0
```

Es todo lo que quedó. Lo de arriba se perdió, pero con lo anterior ya no hace
falta.

---

## Cómo se recupera mañana

Tres caminos, por orden de lo que menos me gusta a lo que más:

1. **Versionar también `@esbuild/linux-x64`.** Rápido, pero mete un binario de 10
   MB en el repo y el problema vuelve con cada actualización de esbuild.
2. **Un `npm ci` antes de la verja** en `bordalas-live.yml`. Correcto, pero añade
   ~30 s y una dependencia de red a un paso que hoy no la tiene, justo antes del
   ciclo.
3. **Quitar esbuild de la comprobación.** Es lo que prefiero: sólo se usa para
   empaquetar el JSX, y `@babel/parser` —que sí es JavaScript puro y funciona en
   cualquier plataforma— ya está ahí. La mitad estática (los hooks condicionales)
   no necesita esbuild para nada; sólo la mitad que pinta. Se puede transformar el
   JSX con Babel y montar sin bundler.

Con la (3), la guardia deja de depender de un binario nativo y vuelve a ser
determinista de verdad en cualquier máquina. **Lo miro mañana; no lo toco esta
noche.**

---

## Estado

- Verja: **110/110**, con y sin la foto real
- `test_la_pantalla_pinta_v1`: **retirada**, entera y pasando 3/3 en local
- Rama `main`, **sin push**
