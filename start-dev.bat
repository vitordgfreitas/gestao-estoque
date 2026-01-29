@echo off
echo ========================================
echo   CRM Gestao Estoque - Iniciando...
echo ========================================
echo.

REM Verifica se o ambiente virtual existe
if not exist "backend\venv" (
    echo Criando ambiente virtual do backend...
    cd backend
    python -m venv venv
    cd ..
)

REM Ativa o ambiente virtual e inicia o backend em background
echo Iniciando Backend (FastAPI)...
start "Backend FastAPI" cmd /k "cd backend && venv\Scripts\activate && pip install -q -r requirements.txt && python run.py"

REM Aguarda um pouco para o backend iniciar
timeout /t 3 /nobreak >nul

REM Inicia o frontend
echo Iniciando Frontend (React)...
cd frontend
if not exist "node_modules" (
    echo Instalando dependencias do frontend...
    call npm install
)
start "Frontend React" cmd /k "npm run dev"

echo.
echo ========================================
echo   Ambos os servidores estao rodando!
echo ========================================
echo   Backend:  http://localhost:8000
echo   Frontend: http://localhost:5173
echo.
echo   Pressione qualquer tecla para fechar esta janela...
pause >nul
