# Deja una foto fresca del estado de Pepe donde Claude pueda leerla.
#
# POR QUE EXISTE
#
#   El status.json vivo lo sirve el Worker de Cloudflare, protegido con
#   usuario y contrasena. Claude no puede entrar ahi, y tampoco hace
#   falta que conozca las credenciales: este script las lee de un
#   fichero local, baja la foto y la deja en diagnostico\, que si es
#   accesible por el puente del escritorio.
#
# COMO SE CONFIGURA (una sola vez)
#
#   Crea el fichero  secrets\dashboard.json  con este contenido:
#
#       {
#         "url":      "https://TU-WORKER.workers.dev",
#         "usuario":  "tu-usuario",
#         "password": "tu-password"
#       }
#
#   Esa carpeta esta en .gitignore: no se sube a ninguna parte.
#
# COMO SE USA
#
#   .\scripts\foto_para_claude.ps1
#
#   Y para que se refresque solo, registralo en el Programador de
#   tareas de Windows cada 15 minutos (ver el final de este fichero).

$ErrorActionPreference = "Stop"

$raiz = Split-Path -Parent $PSScriptRoot
$conf = Join-Path $raiz "secrets\dashboard.json"
$destino = Join-Path $raiz "diagnostico"

if (-not (Test-Path $conf)) {
    Write-Host "Falta $conf" -ForegroundColor Red
    Write-Host 'Crealo con: {"url":"https://...workers.dev","usuario":"...","password":"..."}'
    exit 1
}

$c = Get-Content $conf -Raw | ConvertFrom-Json

if (-not (Test-Path $destino)) {
    New-Item -ItemType Directory -Path $destino | Out-Null
}

$par = "$($c.usuario):$($c.password)"
$b64 = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($par))

$url = ($c.url.TrimEnd('/')) + "/data/status.json"

try {
    $r = Invoke-WebRequest -Uri $url -Headers @{ Authorization = "Basic $b64" } -UseBasicParsing -TimeoutSec 30
}
catch {
    Write-Host "No se pudo bajar la foto: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Si es un 401, revisa usuario y password en $conf"
    Write-Host "Si falla durante un partido, es el bloqueo de Cloudflare: reintenta luego."
    exit 1
}

$salida = Join-Path $destino "status.json"
[IO.File]::WriteAllText($salida, $r.Content, [Text.UTF8Encoding]::new($false))

# Un sello aparte, para saber de cuando es sin abrir el JSON.
$sello = @{
    bajado_en = (Get-Date).ToString("s")
    bytes     = $r.Content.Length
    url       = $url
} | ConvertTo-Json
[IO.File]::WriteAllText((Join-Path $destino "ultima_foto.json"), $sello, [Text.UTF8Encoding]::new($false))

$kb = [math]::Round($r.Content.Length / 1KB)
Write-Host "Foto guardada en diagnostico\status.json ($kb KB)" -ForegroundColor Green


# ----------------------------------------------------------------------
# Para que se refresque sola cada 15 minutos, una vez:
#
#   $a = New-ScheduledTaskAction -Execute "powershell.exe" `
#          -Argument "-NoProfile -ExecutionPolicy Bypass -File C:\Users\PC\Bordalas-IA-clean\scripts\foto_para_claude.ps1"
#   $t = New-ScheduledTaskTrigger -Once -At (Get-Date) `
#          -RepetitionInterval (New-TimeSpan -Minutes 15)
#   Register-ScheduledTask -TaskName "Bordalas - foto para Claude" -Action $a -Trigger $t
#
# Y para quitarla:
#   Unregister-ScheduledTask -TaskName "Bordalas - foto para Claude" -Confirm:$false
# ----------------------------------------------------------------------
