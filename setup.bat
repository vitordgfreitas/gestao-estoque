@echo off
if exist env (
    echo Ambiente virtual ja existe.
    echo Deseja reinstalar? (S/N)
    set /p resposta=
    if /i "%resposta%"=="S" (
        echo Removendo ambiente virtual antigo...
        rmdir /s /q env
    ) else (
        echo Pulando criacao do ambiente virtual.
        goto :install
    )
)

echo Criando ambiente virtual...
python -m venv env

:install
echo Instalando dependencias...
call env\Scripts\pip install --upgrade pip
call env\Scripts\pip install -r requirements.txt

echo.
echo Ambiente configurado com sucesso!
echo Para rodar a aplicacao, execute: make api ou run.bat
pause
