import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import fs from "node:fs";
import path from "node:path";

/* LA FOTO DE MUESTRA PARA DESARROLLAR (29/09/2026)
 *
 * `npm run dev` lee ../dashboard/data/status.json, que solo existe
 * si se ha corrido `python -m src.telemetry.build_dashboard` con
 * una foto de Biwenger y credenciales.
 *
 * `npm run dev:muestra` (vite --mode muestra) lee en cambio
 * dev/status.muestra.json: una copia EXACTA de la foto diaria
 * versionada data/fotos/2026-09-18.json. Sin red, sin
 * credenciales, y siempre la misma, para las capturas. */
const RUTA_DE_LA_FOTO = {
  muestra: "dev/status.muestra.json"
};

function localStatusJson(mode) {
  // El mismo servidor de la foto para `vite` y para `vite preview`:
  // asi se puede mirar tambien el bundle compilado con la muestra.
  const servir = (server) => {
      server.middlewares.use("/data/status.json", (_req, res) => {
        const statusPath = path.resolve(
          process.cwd(),
          RUTA_DE_LA_FOTO[mode] || "../dashboard/data/status.json"
        );
        try {
          const body = fs.readFileSync(statusPath, "utf8");
          res.statusCode = 200;
          res.setHeader("Content-Type", "application/json; charset=utf-8");
          res.setHeader("Cache-Control", "no-store");
          res.end(body);
        } catch {
          res.statusCode = 503;
          res.setHeader("Content-Type", "application/json; charset=utf-8");
          res.end(JSON.stringify({
            error: "No se encontró ../dashboard/data/status.json. Ejecuta python -m src.telemetry.build_dashboard primero."
          }));
        }
      });
  };

  return {
    name: "bordalas-local-status",
    configureServer: servir,
    configurePreviewServer: servir
  };
}

export default defineConfig(({ mode }) => ({
  plugins: [react(), tailwindcss(), localStatusJson(mode)],
  build: {
    outDir: "dist",
    emptyOutDir: true
  }
}));
