@echo off
echo === Instalando Dependencias do Google Sheets ===
echo.

if not exist env\Scripts\pip.exe (
    echo ERRO: Ambiente virtual nao encontrado!
    echo Execute setup.bat primeiro para criar o ambiente virtual.
    pause
    exit /b 1
)

echo Instalando dependencias...
call env\Scripts\pip install --upgrade pip
call env\Scripts\pip install -r requirements.txt

echo.
echo ✅ Dependencias instaladas com sucesso!
echo.
echo Dependencias instaladas:
call env\Scripts\pip list | findstr "gspread\|google-auth\|streamlit\|sqlalchemy"

echo.
pause
