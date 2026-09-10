/* LA PANTALLA PINTA, Y LOS HOOKS NO SON CONDICIONALES
 *
 * SINTOMA (10/09/2026)
 *
 *   Verja 108/108 en verde y el dashboard en blanco.
 *
 *     Minified React error #310
 *     (mas hooks que en el render anterior)
 *
 * CAUSA
 *
 *   En `App.jsx` el `useState`/`useEffect` del reloj de la
 *   pastilla quedo DEBAJO de los dos `return` tempranos. Sin
 *   datos se ejecutaban cuatro hooks y con datos seis. React
 *   cuenta los hooks por orden y en el mismo numero cada vez
 *   -asi sabe cual es cual-, asi que al aparecer dos de la nada
 *   aborta el arbol entero.
 *
 * POR QUE HACEN FALTA LAS DOS MITADES
 *
 *   1. PINTAR de verdad, con la foto real, caza que un
 *      componente reviente al leer un dato que no viene.
 *
 *   2. Pero NO caza este fallo: `renderToString` hace UNA
 *      pasada, y un hook condicional solo se nota entre dos
 *      renders del mismo componente. Por eso va tambien la
 *      lectura del arbol: ningun hook detras de un `return`,
 *      dentro de un `if`, de un bucle o de un `&&`.
 *
 *   Una sola de las dos deja la mitad del agujero abierto.
 */

import { readFileSync, mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, dirname, relative } from "node:path";
import { fileURLToPath } from "node:url";
import { createRequire } from "node:module";

import { parse } from "@babel/parser";
import * as esbuild from "esbuild";

const AQUI = dirname(fileURLToPath(import.meta.url));
const RAIZ = join(AQUI, "..");
const REPO = join(RAIZ, "..");

const HOOKS = /^use[A-Z]/;

const fallos = [];

// ============================================================
// 1. NINGUN HOOK CONDICIONAL
// ============================================================

function ficheros(dir) {
  const { readdirSync, statSync } = require_fs();
  const salida = [];

  for (const nombre of readdirSync(dir)) {
    const ruta = join(dir, nombre);

    if (statSync(ruta).isDirectory()) {
      salida.push(...ficheros(ruta));
    } else if (/\.jsx?$/.test(nombre)) {
      salida.push(ruta);
    }
  }

  return salida;
}

function require_fs() {
  return { readdirSync: fsReaddir, statSync: fsStat };
}

import { readdirSync as fsReaddir, statSync as fsStat } from "node:fs";

/**
 * Recorre el cuerpo de un componente y apunta todo hook que no
 * este en el nivel llano, o que venga despues de un `return`.
 */
function revisaComponente(nombre, nodo, ruta) {
  const cuerpo = nodo.body?.body;

  if (!Array.isArray(cuerpo)) return;

  let vistoReturn = null;

  const anota = (linea, motivo) =>
    fallos.push(
      `${relative(REPO, ruta)}:${linea}  ${nombre}(): ${motivo}`
    );


  // OJO CON DONDE VIVE EL `return`.
  //
  // La primera version de esto miraba `sentencia.type ===
  // "ReturnStatement"` y daba VERDE contra el App.jsx roto,
  // porque los dos returns tempranos van DENTRO de un `if`:
  //
  //     if (!data) {
  //       return <div>CARGANDO</div>;
  //     }
  //
  // Al nivel llano eso es un `IfStatement`, no un return. Asi
  // que hay que buscar el return DENTRO de cada sentencia, sin
  // entrar en funciones anidadas -el `return` de un callback no
  // corta el componente-.
  const contiene = (n, test) => {
    let visto = null;

    caminar(n, (hijo) => {
      if (test(hijo) && !visto) visto = hijo;
      return !esFuncion(hijo);
    });

    return visto;
  };

  const esHook = (n) =>
    n.type === "CallExpression" &&
    n.callee.type === "Identifier" &&
    HOOKS.test(n.callee.name);

  const esReturn = (n) => n.type === "ReturnStatement";

  for (const sentencia of cuerpo) {

    // 1. ¿Hay algún hook aquí, y ya pasamos por un return?
    if (vistoReturn) {
      caminar(sentencia, (hijo) => {
        if (esHook(hijo)) {
          anota(
            hijo.loc.start.line,
            `\`${hijo.callee.name}\` se ejecuta DESPUES del ` +
              `\`return\` de la linea ${vistoReturn}: con datos y ` +
              `sin datos corren un numero distinto de hooks`
          );
        }
        return !esFuncion(hijo);
      });
    }

    // 2. Un hook colgado de un `if`, un bucle o un `try` es
    //    condicional aunque no haya ningun return de por medio.
    if (
      sentencia.type === "IfStatement" ||
      sentencia.type === "ForStatement" ||
      sentencia.type === "ForOfStatement" ||
      sentencia.type === "ForInStatement" ||
      sentencia.type === "WhileStatement" ||
      sentencia.type === "SwitchStatement" ||
      sentencia.type === "TryStatement"
    ) {
      const dentro = contiene(sentencia, esHook);

      if (dentro) {
        anota(
          dentro.loc.start.line,
          `\`${dentro.callee.name}\` cuelga de un ` +
            `\`${sentencia.type}\`: se ejecuta unas veces si y ` +
            `otras no`
        );
      }
    }

    // 3. Y si esta sentencia puede salirse, lo que venga
    //    despues ya es condicional.
    if (!vistoReturn) {
      const salida = contiene(sentencia, esReturn);

      if (salida) vistoReturn = salida.loc.start.line;
    }
  }
}

function esFuncion(n) {
  return (
    n.type === "FunctionDeclaration" ||
    n.type === "FunctionExpression" ||
    n.type === "ArrowFunctionExpression"
  );
}

function caminar(nodo, visita) {
  if (!nodo || typeof nodo.type !== "string") return;

  if (visita(nodo) === false) return;

  for (const clave of Object.keys(nodo)) {
    if (clave === "loc" || clave === "leadingComments") continue;

    const valor = nodo[clave];

    if (Array.isArray(valor)) {
      for (const item of valor) caminar(item, visita);
    } else if (valor && typeof valor.type === "string") {
      caminar(valor, visita);
    }
  }
}

function revisaFichero(ruta) {
  const arbol = parse(readFileSync(ruta, "utf8"), {
    sourceType: "module",
    plugins: ["jsx"],
  });

  caminar(arbol.program, (n) => {
    if (n.type === "FunctionDeclaration" && n.id) {
      revisaComponente(n.id.name, n, ruta);
    }

    if (
      n.type === "VariableDeclarator" &&
      n.id.type === "Identifier" &&
      n.init &&
      esFuncion(n.init)
    ) {
      revisaComponente(n.id.name, { body: n.init.body }, ruta);
    }

    return true;
  });
}

// ------------------------------------------------------------
// EL DETECTOR SE PRUEBA A SI MISMO, ANTES DE OPINAR
// ------------------------------------------------------------
//
// La primera version de esto dio VERDE contra el App.jsx roto:
// miraba `sentencia.type === "ReturnStatement"` y los dos
// returns tempranos viven DENTRO de un `if`. Un detector que
// dice "cero" puede estar simplemente roto, y entonces es peor
// que no tenerlo, porque ademas tranquiliza.
//
// Asi que antes de recorrer nada se le pone delante el fallo
// exacto del 10/09, y tiene que verlo. Y lo sano tiene que
// dejarlo pasar.
const CEBO = `
function Roto({ data }) {
  const [a, setA] = useState(1);

  if (!data) {
    return null;
  }

  const [b, setB] = useState(2);
  useEffect(() => {}, []);

  return b;
}

function Sano({ data }) {
  const [a, setA] = useState(1);
  useEffect(() => {}, []);

  const filas = (data.filas || []).map((f) => {
    return f.id;
  });

  if (!data) {
    return null;
  }

  return filas;
}
`;

{
  const guardadas = fallos.splice(0, fallos.length);

  const arbol = parse(CEBO, {
    sourceType: "module",
    plugins: ["jsx"],
  });

  caminar(arbol.program, (n) => {
    if (n.type === "FunctionDeclaration" && n.id) {
      revisaComponente(n.id.name, n, "CEBO");
    }
    return true;
  });

  const cazados = fallos.splice(0, fallos.length);

  const enRoto = cazados.filter((f) => f.includes("Roto()"));
  const enSano = cazados.filter((f) => f.includes("Sano()"));

  if (enRoto.length !== 2) {
    console.error(
      `EL DETECTOR ESTA ROTO: tenia que cazar los dos hooks ` +
        `condicionales del cebo y ha cazado ${enRoto.length}.`
    );
    process.exit(1);
  }

  if (enSano.length) {
    console.error(
      "EL DETECTOR CANTA LO QUE ESTA BIEN:\n  " +
        enSano.join("\n  ")
    );
    process.exit(1);
  }

  fallos.push(...guardadas);
}

for (const ruta of ficheros(join(RAIZ, "src"))) {
  revisaFichero(ruta);
}

if (fallos.length) {
  console.error(
    "HOOKS CONDICIONALES: se ejecutan un numero distinto de veces\n" +
      "segun los datos, y React tumba la pagina entera (error #310).\n" +
      "Los hooks van SIEMPRE arriba, antes de cualquier return.\n"
  );
  for (const f of fallos) console.error("  " + f);
  process.exit(1);
}

console.log("hooks: ninguno condicional");

// ============================================================
// 2. Y LA PAGINA SE PINTA DE VERDAD
// ============================================================

const FOTO = join(REPO, "dashboard", "data", "status.json");

let crudo;

try {
  crudo = JSON.parse(readFileSync(FOTO, "utf8"));
} catch (error) {
  // Sin foto no se pinta, pero tampoco se calla: un salto
  // silencioso aqui seria el mismo agujero con otra forma.
  console.log(
    `pintar: SIN MUESTRA (${error.code || error.message}). ` +
      `La lectura de hooks sigue vigilando igual.`
  );
  process.exit(0);
}

// Rutas RELATIVAS: `resolveDir` es `dashboard-v8`, y esbuild no
// resuelve `file://` en un import.
const ENTRADA = `
import React from "react";
import { renderToString } from "react-dom/server";
import { normalizeStatus } from "./src/lib/status.js";
import HomePage from "./src/pages/HomePage.jsx";
import AuditPage from "./src/pages/AuditPage.jsx";
import KpiStrip from "./src/components/KpiStrip.jsx";

export function pinta(crudo) {
  const data = normalizeStatus(crudo);

  return {
    tira: renderToString(React.createElement(KpiStrip, { data })).length,
    inicio: renderToString(React.createElement(HomePage, { data })).length,
    auditoria: renderToString(React.createElement(AuditPage, { data })).length,
  };
}
`;

// SE SACA EN CJS, no en ESM.
//
// `react-dom/server.node` es CommonJS y hace `require("util")`
// por dentro. En un bundle ESM eso se convierte en un `require`
// de pega que lanza "Dynamic require not supported": pareceria
// que la pagina esta rota cuando lo unico roto es el envoltorio.
const carpeta = mkdtempSync(join(tmpdir(), "bordalas-pinta-"));
const salida = join(carpeta, "pinta.cjs");

await esbuild.build({
  stdin: {
    contents: ENTRADA,
    resolveDir: RAIZ,
    loader: "jsx",
  },
  bundle: true,
  format: "cjs",
  platform: "node",
  outfile: salida,
  jsx: "automatic",
  logLevel: "silent",
  define: { "process.env.NODE_ENV": '"development"' },
});

const modulo = createRequire(import.meta.url)(salida);

const tamanos = modulo.pinta(crudo);

for (const [pagina, largo] of Object.entries(tamanos)) {
  if (!largo || largo < 200) {
    console.error(
      `PANTALLA EN BLANCO: \`${pagina}\` ha pintado ${largo} ` +
        `caracteres. Se monta, pero no sale nada.`
    );
    process.exit(1);
  }
}

console.log(
  "pintar: " +
    Object.entries(tamanos)
      .map(([k, v]) => `${k} ${v}`)
      .join(" · ")
);
