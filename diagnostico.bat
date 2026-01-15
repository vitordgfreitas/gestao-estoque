@echo off
echo === Diagnostico do Sistema ===
echo.

echo 1. Verificando Python...
python --version >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    python --version
    echo    OK: Python encontrado
) else (
    echo    ERRO: Python nao encontrado!
    pause
    exit /b 1
)

echo.
echo 2. Verificando ambiente virtual...
if exist env\Scripts\python.exe (
    echo    OK: Ambiente virtual encontrado
) else (
    echo    AVISO: Ambiente virtual nao encontrado
    echo    Execute: setup.bat ou make setup
)

echo.
echo 3. Verificando dependencias...
if exist env\Scripts\python.exe (
    env\Scripts\pip show streamlit >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        echo    OK: Streamlit instalado
    ) else (
        echo    ERRO: Streamlit nao instalado
        echo    Execute: env\Scripts\pip install -r requirements.txt
    )
    
    env\Scripts\pip show sqlalchemy >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        echo    OK: SQLAlchemy instalado
    ) else (
        echo    ERRO: SQLAlchemy nao instalado
    )
) else (
    echo    PULADO: Ambiente virtual nao existe
)

echo.
echo 4. Verificando porta 8501...
netstat -ano | findstr :8501 >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo    AVISO: Porta 8501 esta em uso!
    netstat -ano | findstr :8501
    echo    Pare o processo ou use outra porta
) else (
    echo    OK: Porta 8501 disponivel
)

echo.
echo 5. Testando aplicacao...
if exist env\Scripts\python.exe (
    echo    Executando testes...
    call env\Scripts\python test_app.py
    if %ERRORLEVEL% EQU 0 (
        echo    OK: Aplicacao pronta para rodar!
    ) else (
        echo    ERRO: Testes falharam
    )
) else (
    echo    PULADO: Ambiente virtual nao existe
)

echo.
echo === Fim do Diagnostico ===
echo.
echo Para iniciar a aplicacao:
echo   make api
echo   ou
echo   run.bat
pause
