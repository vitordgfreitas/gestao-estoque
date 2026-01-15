#!/bin/bash
echo "Criando ambiente virtual..."
python3 -m venv env

echo "Ativando ambiente virtual..."
source env/bin/activate

echo "Instalando dependencias..."
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "Ambiente configurado com sucesso!"
echo "Para ativar o ambiente, execute: source env/bin/activate"
echo "Para rodar a aplicacao, execute: make api"
