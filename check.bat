@echo off
echo Verificando se o ambiente virtual existe...
if not exist env (
    echo ERRO: Ambiente virtual nao encontrado!
    echo Execute: setup.bat ou make setup
    pause
    exit /b 1
)

echo Ambiente virtual encontrado.
echo.
echo Testando configuração...
call env\Scripts\python test_app.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERRO: Testes falharam. Verifique as mensagens acima.
    pause
    exit /b 1
)

echo.
echo Tudo OK! Tentando iniciar a aplicacao...
echo.
call env\Scripts\streamlit run app.py --server.port=8501 --server.address=0.0.0.0
