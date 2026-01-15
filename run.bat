@echo off
if not exist env (
    echo Ambiente virtual nao encontrado!
    echo Execute setup.bat primeiro para configurar o ambiente.
    pause
    exit /b 1
)

echo Iniciando aplicacao Streamlit...
echo Acesse: http://localhost:8501
echo.
call env\Scripts\streamlit run app.py --server.port=8501 --server.address=0.0.0.0
