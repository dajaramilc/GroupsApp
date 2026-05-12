$ErrorActionPreference = "Stop"

Write-Host "Iniciando microservicios..." -ForegroundColor Cyan

$projectRoot = (Get-Location).Path

if (!(Test-Path "venv314\Scripts\uvicorn.exe")) {
    Write-Host "No se encontró venv314. Ejecuta pip install primero." -ForegroundColor Red
    exit 1
}

# Matar procesos anteriores de uvicorn para evitar conflictos de puertos
Get-Process uvicorn -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 1

$services = @(
    @{ Name="svc-auth"; Port=8001 },
    @{ Name="svc-users"; Port=8002 },
    @{ Name="svc-groups"; Port=8003 },
    @{ Name="svc-channels"; Port=8004 },
    @{ Name="svc-messages"; Port=8005 },
    @{ Name="svc-files"; Port=8006 },
    @{ Name="svc-presence"; Port=8007 }
)

# Crear wrappers temporales en la raíz del proyecto para cada servicio
# Esto resuelve el problema de que Python no puede importar carpetas con guiones
foreach ($svc in $services) {
    $name = $svc.Name
    $port = $svc.Port
    $safeName = $name.Replace("-", "_")
    $wrapperFile = Join-Path $projectRoot "_run_${safeName}.py"
    
    # Crear un pequeño wrapper que importa el main.py del servicio
    $wrapperContent = @"
import importlib.util, sys, os
spec = importlib.util.spec_from_file_location("main", os.path.join(os.path.dirname(__file__), "services", "$name", "main.py"))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
app = mod.app
"@
    Set-Content -Path $wrapperFile -Value $wrapperContent -Encoding UTF8
    
    Write-Host "Iniciando $name en puerto $port..." -ForegroundColor Yellow
    Start-Process -FilePath "venv314\Scripts\uvicorn.exe" -ArgumentList "_run_${safeName}:app --port $port" -WindowStyle Minimized
}

Write-Host "Iniciando API Gateway Mock (local_proxy.py) en puerto 8000..." -ForegroundColor Yellow
Start-Process -FilePath "venv314\Scripts\uvicorn.exe" -ArgumentList "local_proxy:app --port 8000" -WindowStyle Minimized

Write-Host "Todos los servicios iniciados." -ForegroundColor Green
Write-Host "El API Gateway está disponible en http://localhost:8000" -ForegroundColor Green
Write-Host "Nota: Los procesos se abrieron en ventanas minimizadas. Cierra esas ventanas para detenerlos." -ForegroundColor Gray
