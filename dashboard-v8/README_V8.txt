BORDALÁS IA DASHBOARD V8 - REACT EDITION

OBJETIVO
- Nuevo frontend profesional, separado del dashboard actual.
- No toca Python, Competitive, Biwenger ni producción.
- Lee el mismo /data/status.json.
- En desarrollo, Vite lee automáticamente ../dashboard/data/status.json.

INSTALACIÓN LOCAL
1) Copia la carpeta Bordalas-IA-Dashboard-V8-React dentro de:
   C:\Users\PC\Bordalas-IA-clean\dashboard-v8

2) Desde PowerShell:
   cd C:\Users\PC\Bordalas-IA-clean\dashboard-v8
   npm install
   npm run dev

3) Abre la URL que muestre Vite (normalmente http://localhost:5173)

ANTES DE ARRANCAR
Si quieres datos recién generados:
   cd C:\Users\PC\Bordalas-IA-clean
   python -m src.telemetry.build_dashboard

BUILD DE PRODUCCIÓN (NO HACER TODAVÍA)
   npm run build

Eso creará dashboard-v8\dist.
Primero aprobamos visualmente V8. Después adaptaremos Cloudflare para servir dist.
