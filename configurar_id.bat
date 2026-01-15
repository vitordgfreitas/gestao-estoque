@echo off
echo === Configuracao do ID da Planilha Google Sheets ===
echo.

set SHEET_ID=1OmKLrAJq4CBYzyhwQlbjCd-AbPl3YmMNPNExSBeAvlE

echo Configurando ID da planilha: %SHEET_ID%
echo.

REM Configura para a sessao atual
set GOOGLE_SHEET_ID=%SHEET_ID%

REM Configura permanentemente (requer privilégios de administrador)
setx GOOGLE_SHEET_ID "%SHEET_ID%"

echo.
echo ✅ ID da planilha configurado!
echo.
echo O sistema criara automaticamente as abas necessarias:
echo   - Itens
echo   - Compromissos
echo.
echo Certifique-se de que:
echo   1. O arquivo credentials.json esta na raiz do projeto
echo   2. A planilha foi compartilhada com o email da conta de servico
echo.
pause
