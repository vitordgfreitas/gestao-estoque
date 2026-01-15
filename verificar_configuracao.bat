@echo off
echo === Verificando Configuracao do Google Sheets ===
echo.

echo 1. Verificando arquivo credentials.json...
if exist credentials.json (
    echo    OK: Arquivo credentials.json encontrado
) else (
    echo    ERRO: Arquivo credentials.json NAO encontrado!
    echo    Coloque o arquivo credentials.json na raiz do projeto.
    echo.
    pause
    exit /b 1
)

echo.
echo 2. Verificando ID da planilha...
if defined GOOGLE_SHEET_ID (
    echo    OK: GOOGLE_SHEET_ID configurado: %GOOGLE_SHEET_ID%
) else (
    echo    AVISO: GOOGLE_SHEET_ID nao configurado
    echo    Execute: configurar_id.bat
    echo    Ou configure manualmente:
    echo    set GOOGLE_SHEET_ID=1OmKLrAJq4CBYzyhwQlbjCd-AbPl3YmMNPNExSBeAvlE
)

echo.
echo 3. Verificando email da conta de servico...
if exist credentials.json (
    echo    Extraindo email da conta de servico...
    findstr "client_email" credentials.json > temp_email.txt 2>nul
    if exist temp_email.txt (
        type temp_email.txt
        del temp_email.txt
        echo.
        echo    IMPORTANTE: Compartilhe a planilha com este email!
        echo    A permissao deve ser EDITOR
    )
)

echo.
echo === Resumo ===
echo.
echo Para configurar completamente:
echo   1. Certifique-se de que credentials.json esta na raiz
echo   2. Execute: configurar_id.bat
echo   3. Compartilhe a planilha com o email da conta de servico
echo   4. Execute: make api
echo.
pause
