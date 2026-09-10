# Pantalla en blanco — React #310

**10/09/2026** · verja 109/109 · sin push

---

## 1. Dónde estaba

`App.jsx`. Los dos hooks del reloj de la pastilla quedaron **debajo de los dos
`return` tempranos**:

```
  if (error && !data) { return <div>NO SE PUDO CARGAR…</div>; }   ← sale con 4 hooks
  if (!data)          { return <div>CARGANDO…</div>; }            ← sale con 4 hooks
  ...
  const [ahora, setAhora] = useState(...)   ← y en el render siguiente, 6
  useEffect(...)
```

Primer render sin datos: cuatro hooks. Llega la foto, vuelve a renderizar: seis.
React los cuenta **por orden y en el mismo número cada vez** —así sabe cuál es
cuál— y al aparecer dos de la nada aborta el árbol entero. Blanco.

Arreglado subiéndolos: los seis hooks corren siempre, antes de cualquier `return`.
Lo condicional sigue siendo lo que se pinta.

**Regresión mía**, del commit de los ajustes de Inicio.

---

## 2. La guardia — y sí se puede, sin montar nada

No hace falta banco de pruebas: **`node_modules` está versionado** (8.308 ficheros)
y el workflow ya instala Node 24 **antes** de la verja. Se usan el `esbuild` y el
`react-dom/server` que ya estaban ahí.

`dashboard-v8/tools/comprobar_pantalla.mjs`, dos mitades, y hacen falta las dos:

| | qué hace | qué caza |
|---|---|---|
| **Árbol** | lee todos los `.jsx` y prohíbe un hook detrás de un `return`, dentro de un `if`, un bucle o un `try` | **este fallo** |
| **Pintar** | monta Inicio, Auditoría y la tira con `renderToString` y la foto real | un componente que revienta al leer un dato que no viene |

**Ninguna sola basta.** `renderToString` hace UNA pasada, y un hook condicional
sólo se nota entre dos renders del mismo componente: la mitad que pinta **no
habría cazado esto**. Y la lectura del árbol no ve un `undefined.foo`.

Hoy pinta: `tira 736 · inicio 16.117 · auditoría 45.532` caracteres.

### El detector mintió una vez, y por eso se prueba a sí mismo

La primera versión dio **verde contra el `App.jsx` roto**. Miraba
`sentencia.type === "ReturnStatement"` y los dos returns tempranos viven **dentro
de un `if`**: al nivel llano eso es un `IfStatement`, no un return, así que nunca
marcaba el punto de corte.

Corregido —ahora busca el `return` *dentro* de cada sentencia, sin entrar en
funciones anidadas— y contra el fichero roto dice:

```
App.jsx:86  App(): `useState` se ejecuta DESPUES del `return` de la linea 60
App.jsx:88  App(): `useEffect` se ejecuta DESPUES del `return` de la linea 60
```

Y el guion **se pone delante el fallo exacto antes de opinar de nada**: un cebo
con un componente roto (tiene que cazar dos) y uno sano (no puede cantar ninguno).
Si el cebo no sale, aborta. Un detector que dice «cero» estando roto es peor que
no tenerlo, porque además tranquiliza — es la segunda vez hoy que me pasa.

---

## 3. El repaso: estaba una vez

Cuatro ficheros usan hooks. El detector barre `src` entero; verificados también a
mano:

| | hooks | posición |
|---|---|---|
| `App.jsx` | 6 | **estaba roto** · arreglado |
| `KpiStrip.jsx` | 2 | líneas 59 y 64, componente en 58 — limpio |
| `AuditPage.jsx` | 2 | líneas 210 y 213, componente en 209 — limpio |
| `SquadPage.jsx` | 1 | línea 52, componente en 44 — limpio |

`PosiblesCambiosPanel` no tiene ningún hook: sus dos caminos —«no se sabe» y con
banquillo— son sólo `return` distintos, que es exactamente lo permitido.

**Estaba una vez.** La mitad estática queda puesta para que la próxima no llegue a
la pantalla.

---

## Lo que sigue sin cubrir, y lo digo

La mitad que pinta usa `renderToString`: monta el árbol una vez, **no simula
interacción ni re-render**. Un fallo que sólo aparezca al pulsar un filtro, o al
llegar la segunda foto, seguiría pasando. Para eso haría falta un banco de pruebas
de verdad (jsdom + testing-library), que sí sería trabajo aparte. Lo dejo escrito
en vez de dar por cubierto más de lo que está.

---

## Estado

- Verja: **109/109**
- `vite build` hecho, `dist` copiado a `dashboard/`
- Rama `main`, **sin push**
