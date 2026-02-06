@echo off
echo [*] Limpando cache do backend no Render...
echo.
echo IMPORTANTE: Troque "SEU_TOKEN_AQUI" pelo token de login do seu app
echo.
pause
curl -X POST "https://crm-backend-ghly.onrender.com/api/cache/clear" -H "Authorization: Bearer SEU_TOKEN_AQUI"
echo.
echo.
echo [OK] Pronto! Agora recarregue o app (Ctrl+Shift+R)
pause
