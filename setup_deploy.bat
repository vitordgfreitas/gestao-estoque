@echo off
echo === Preparacao para Deploy ===
echo.

echo Verificando se o Git esta instalado...
git --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERRO: Git nao encontrado!
    echo Instale o Git de: https://git-scm.com/downloads
    pause
    exit /b 1
)

echo Git encontrado!
echo.

echo Verificando arquivos importantes...
if not exist requirements.txt (
    echo AVISO: requirements.txt nao encontrado
)

if not exist app.py (
    echo ERRO: app.py nao encontrado!
    pause
    exit /b 1
)

echo.
echo Arquivos verificados!
echo.
echo Proximos passos:
echo 1. Crie um repositorio no GitHub
echo 2. Execute os comandos Git abaixo (substitua SEU_USUARIO):
echo.
echo    git init
echo    git add .
echo    git commit -m "Initial commit"
echo    git branch -M main
echo    git remote add origin https://github.com/SEU_USUARIO/gestao-estoque.git
echo    git push -u origin main
echo.
echo 3. Acesse https://share.streamlit.io e faca o deploy
echo.
echo Veja DEPLOY.md para instrucoes completas!
echo.
pause
