.PHONY: api setup install run

# Comando principal: setup + run
api:
	@powershell -Command "if (-not (Test-Path env)) { Write-Host 'Criando ambiente virtual...'; python -m venv env; Write-Host 'Instalando dependencias...'; .\env\Scripts\pip install --upgrade pip; .\env\Scripts\pip install -r requirements.txt } else { Write-Host 'Ambiente virtual ja existe.' }"
	@echo Iniciando aplicacao Streamlit...
	@echo Acesse: http://localhost:8501
	@.\env\Scripts\streamlit run app.py --server.port=8501 --server.address=0.0.0.0

# Cria e configura o ambiente virtual
setup:
	@echo Criando ambiente virtual...
	python -m venv env
	@echo Instalando dependencias...
	.\env\Scripts\pip install --upgrade pip
	.\env\Scripts\pip install -r requirements.txt

# Instala dependencias no ambiente virtual existente
install:
	.\env\Scripts\pip install --upgrade pip
	.\env\Scripts\pip install -r requirements.txt

# Roda a aplicacao
run:
	@echo Iniciando aplicacao Streamlit...
	@echo Acesse: http://localhost:8501
	.\env\Scripts\streamlit run app.py --server.port=8501 --server.address=0.0.0.0
