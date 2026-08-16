# =====================================================================
#  Bordalas IA - reconstruir y publicar el dashboard
# =====================================================================
#
#  Que hace, en orden:
#
#    1. Compila el React de dashboard-v8.
#    2. Copia el resultado a dashboard\ SIN tocar dashboard\data,
#       que es donde vive status.json.
#    3. Sube el resultado a Cloudflare.
#
#  Lo que NO hace: subir los datos. El status.json del dashboard
#  publicado sale del KV de Cloudflare y ahi solo escribe GitHub
#  Actions. Para refrescar los datos hay que hacer push y dejar
#  que corra el ciclo.
#
#  Uso, desde la raiz del proyecto:
#
#      .\deploy_dashboard.ps1
#
# =====================================================================

$ErrorActionPreference = "Stop"

$raiz = $PSScriptRoot

if (-not $raiz) { $raiz = (Get-Location).Path }

Set-Location $raiz

Write-Host ""
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host " 1/3  COMPILANDO EL DASHBOARD" -ForegroundColor Cyan
Write-Host "=====================================================" -ForegroundColor Cyan

Set-Location (Join-Path $raiz "dashboard-v8")

npm run build

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "La compilacion ha fallado. No se copia nada." -ForegroundColor Red
    Set-Location $raiz
    exit 1
}

Set-Location $raiz

Write-Host ""
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host " 2/3  COPIANDO A dashboard\" -ForegroundColor Cyan
Write-Host "=====================================================" -ForegroundColor Cyan

$dist    = Join-Path $raiz "dashboard-v8\dist"
$destino = Join-Path $raiz "dashboard"

if (-not (Test-Path $dist)) {
    Write-Host "No existe $dist. Algo ha ido mal en la compilacion." -ForegroundColor Red
    exit 1
}

# Los ficheros compilados llevan un hash en el nombre, asi que si
# no se limpia antes se van acumulando bundles viejos.
$assets = Join-Path $destino "assets"

if (Test-Path $assets) {
    Remove-Item (Join-Path $assets "*") -Recurse -Force
}

# Se copia todo menos data\, que es el status.json y no viene del
# build.
Get-ChildItem -Path $dist -Force | Where-Object { $_.Name -ne "data" } |
    ForEach-Object {
        Copy-Item $_.FullName -Destination $destino -Recurse -Force
    }

Write-Host ""
Write-Host "Contenido de dashboard\assets:"
Get-ChildItem (Join-Path $destino "assets") | Select-Object Name, Length, LastWriteTime | Format-Table

Write-Host ""
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host " 3/3  PUBLICANDO EN CLOUDFLARE" -ForegroundColor Cyan
Write-Host "=====================================================" -ForegroundColor Cyan

Set-Location (Join-Path $raiz "cloudflare")

npx --yes wrangler@4.120.1 deploy

$codigo = $LASTEXITCODE

Set-Location $raiz

if ($codigo -ne 0) {
    Write-Host ""
    Write-Host "El deploy ha fallado." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "=====================================================" -ForegroundColor Green
Write-Host " LISTO" -ForegroundColor Green
Write-Host "=====================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Recuerda: esto actualiza el ASPECTO del dashboard."
Write-Host "Los DATOS que ves publicados vienen del KV, y ese lo"
Write-Host "escribe GitHub Actions cuando corre el ciclo."
Write-Host ""
Write-Host "En el navegador, recarga con Ctrl+F5 para saltarte la cache."
Write-Host ""
