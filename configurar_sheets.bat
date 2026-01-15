@echo off
echo === Configuracao do Google Sheets ===
echo.

set /p SHEET_ID="Digite o ID da planilha (ou pressione Enter para usar o padrao): "
if "%SHEET_ID%"=="" (
    echo Usando ID padrao: 1OmKLrAJq4CBYzyhwQlbjCd-AbPl3YmMNPNExSBeAvlE
    set SHEET_ID=1OmKLrAJq4CBYzyhwQlbjCd-AbPl3YmMNPNExSBeAvlE
)

echo.
echo Configurando variaveis de ambiente...
setx GOOGLE_SHEET_ID "%SHEET_ID%"
set GOOGLE_SHEET_ID=%SHEET_ID%

echo.
echo ✅ ID da planilha configurado: %SHEET_ID%
echo.
echo Para usar Google Sheets, certifique-se de que:
echo 1. O arquivo credentials.json esta na raiz do projeto
echo 2. A planilha foi compartilhada com o email da conta de servico
echo.
echo Para iniciar a aplicacao, execute: make api
pause
