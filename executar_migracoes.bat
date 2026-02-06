@echo off
echo ============================================
echo Executando Migracoes do Banco de Dados
echo ============================================
echo.

cd /d "C:\Users\Ryzen 5 5600\Downloads\GestaoCarro"

echo [1/2] Migracao: valor_entrada
python migrate_add_valor_entrada.py
if errorlevel 1 (
    echo ERRO na migracao valor_entrada
    pause
    exit /b 1
)

echo.
echo [2/2] Migracao: pecas_carros
python migrate_add_pecas_carros.py
if errorlevel 1 (
    echo ERRO na migracao pecas_carros
    pause
    exit /b 1
)

echo.
echo ============================================
echo Todas as migracoes foram executadas!
echo ============================================
echo.
pause
