BORDALÁS IA — PHOTO RESOLVER V3

INSTALACIÓN

1) Descomprime este ZIP como:
C:\Users\PC\Bordalas-IA-clean\photo_resolver_v3

2) Desde:
C:\Users\PC\Bordalas-IA-clean

ejecuta:
python .\photo_resolver_v3\install_photo_resolver_v3.py

3) Valida:
python -m py_compile src\telemetry\player_photo_resolver.py
python -m py_compile src\telemetry\dashboard_state.py

4) Genera:
python -m src.telemetry.build_dashboard

5) Comprueba:
$data = Get-Content .\dashboard\data\status.json -Raw | ConvertFrom-Json
$data.lineup.players |
Select-Object name,id,photo_source,icon_hero,api_football_id,photo_url |
Format-Table -AutoSize

REACT V8.1
Copia:
PlayerAvatar_V81.jsx -> dashboard-v8\src\components\PlayerAvatar.jsx
KpiStrip_V81.jsx    -> dashboard-v8\src\components\KpiStrip.jsx

ROLLBACK
Copy-Item ".\src\telemetry\dashboard_state_PRE_PHOTO_V3_BACKUP.py" ".\src\telemetry\dashboard_state.py" -Force
