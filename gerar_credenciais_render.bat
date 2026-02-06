@echo off
cd "C:\Users\Ryzen 5 5600\Downloads\GestaoCarro"
echo.
echo ========================================
echo  CREDENCIAIS PARA O RENDER
echo ========================================
echo.
echo Copie TODA a linha abaixo:
echo.
python -c "import json; print(json.dumps(json.load(open('credentials.json'))))"
echo.
echo ========================================
echo  PROXIMO PASSO:
echo  1. Copie a linha acima (comeca com {"type":)
echo  2. Va em dashboard.render.com
echo  3. Seu backend -^> Environment
echo  4. Add Environment Variable
echo  5. Key: GOOGLE_CREDENTIALS
echo  6. Value: [cole aqui]
echo  7. Save Changes
echo ========================================
pause
