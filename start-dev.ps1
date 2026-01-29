# Script PowerShell para iniciar backend e frontend

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  CRM Gestao Estoque - Iniciando..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Verifica e cria ambiente virtual do backend
if (-not (Test-Path "backend\venv")) {
    Write-Host "Criando ambiente virtual do backend..." -ForegroundColor Yellow
    Set-Location backend
    python -m venv venv
    Set-Location ..
}

# Inicia o backend em nova janela
Write-Host "Iniciando Backend (FastAPI)..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD\backend'; .\venv\Scripts\Activate.ps1; pip install -q -r requirements.txt; python run.py"

# Aguarda backend iniciar
Start-Sleep -Seconds 3

# Inicia o frontend em nova janela
Write-Host "Iniciando Frontend (React)..." -ForegroundColor Green
Set-Location frontend

if (-not (Test-Path "node_modules")) {
    Write-Host "Instalando dependencias do frontend..." -ForegroundColor Yellow
    npm install
}

Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; npm run dev"

Set-Location ..

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Ambos os servidores estao rodando!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Backend:  http://localhost:8000" -ForegroundColor Yellow
Write-Host "  Frontend: http://localhost:5173" -ForegroundColor Yellow
Write-Host ""
Write-Host "Pressione qualquer tecla para continuar..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
