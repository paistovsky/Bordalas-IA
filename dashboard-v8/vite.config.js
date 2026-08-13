import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import fs from "node:fs";
import path from "node:path";

function localStatusJson() {
  return {
    name: "bordalas-local-status",
    configureServer(server) {
      server.middlewares.use("/data/status.json", (_req, res) => {
        const statusPath = path.resolve(process.cwd(), "../dashboard/data/status.json");
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
    }
  };
}

export default defineConfig({
  plugins: [react(), tailwindcss(), localStatusJson()],
  build: {
    outDir: "dist",
    emptyOutDir: true
  }
});
