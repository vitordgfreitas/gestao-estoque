Write-Host "=== Diagnostico do Sistema ===" -ForegroundColor Cyan
Write-Host ""

# Verificar Python
Write-Host "1. Verificando Python..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "   OK: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "   ERRO: Python nao encontrado!" -ForegroundColor Red
    exit 1
}

# Verificar ambiente virtual
Write-Host ""
Write-Host "2. Verificando ambiente virtual..." -ForegroundColor Yellow
if (Test-Path "env\Scripts\python.exe") {
    Write-Host "   OK: Ambiente virtual encontrado" -ForegroundColor Green
} else {
    Write-Host "   AVISO: Ambiente virtual nao encontrado" -ForegroundColor Yellow
    Write-Host "   Execute: setup.bat ou make setup" -ForegroundColor Yellow
}

# Verificar dependencias
Write-Host ""
Write-Host "3. Verificando dependencias..." -ForegroundColor Yellow
if (Test-Path "env\Scripts\python.exe") {
    $streamlit = & env\Scripts\pip show streamlit 2>&1
    if ($streamlit -match "Name: streamlit") {
        Write-Host "   OK: Streamlit instalado" -ForegroundColor Green
    } else {
        Write-Host "   ERRO: Streamlit nao instalado" -ForegroundColor Red
        Write-Host "   Execute: env\Scripts\pip install -r requirements.txt" -ForegroundColor Yellow
    }
    
    $sqlalchemy = & env\Scripts\pip show sqlalchemy 2>&1
    if ($sqlalchemy -match "Name: sqlalchemy") {
        Write-Host "   OK: SQLAlchemy instalado" -ForegroundColor Green
    } else {
        Write-Host "   ERRO: SQLAlchemy nao instalado" -ForegroundColor Red
    }
} else {
    Write-Host "   PULADO: Ambiente virtual nao existe" -ForegroundColor Yellow
}

# Verificar porta
Write-Host ""
Write-Host "4. Verificando porta 8501..." -ForegroundColor Yellow
$porta = netstat -ano | findstr :8501
if ($porta) {
    Write-Host "   AVISO: Porta 8501 esta em uso!" -ForegroundColor Yellow
    Write-Host "   $porta" -ForegroundColor Gray
    Write-Host "   Pare o processo ou use outra porta" -ForegroundColor Yellow
} else {
    Write-Host "   OK: Porta 8501 disponivel" -ForegroundColor Green
}

# Testar aplicacao
Write-Host ""
Write-Host "5. Testando aplicacao..." -ForegroundColor Yellow
if (Test-Path "env\Scripts\python.exe") {
    Write-Host "   Executando testes..." -ForegroundColor Gray
    & env\Scripts\python test_app.py
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   OK: Aplicacao pronta para rodar!" -ForegroundColor Green
    } else {
        Write-Host "   ERRO: Testes falharam" -ForegroundColor Red
    }
} else {
    Write-Host "   PULADO: Ambiente virtual nao existe" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=== Fim do Diagnostico ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Para iniciar a aplicacao:" -ForegroundColor Cyan
Write-Host "  make api" -ForegroundColor White
Write-Host "  ou" -ForegroundColor Gray
Write-Host "  run.bat" -ForegroundColor White
