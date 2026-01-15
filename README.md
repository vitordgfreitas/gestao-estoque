# Sistema de Gestão de Estoque - Aluguel de Itens

Sistema de gestão de estoque para empresas de aluguel de itens de eventos, desenvolvido com Python e Streamlit.

## Funcionalidades

- ➕ **Registrar Itens**: Cadastre itens com nome e quantidade total
- 📅 **Registrar Compromissos**: Registre aluguéis com período de início e fim
- 🔍 **Verificar Disponibilidade**: Consulte a disponibilidade de itens em datas específicas
- 📊 **Visualizar Dados**: Veja todos os itens e compromissos cadastrados

## Como Usar

### Pré-requisitos

- Python 3.8 ou superior instalado
- Make (opcional, mas recomendado) ou use os scripts `.bat` no Windows

### Executando o Sistema

#### Opção 1: Usando Make (Windows/Linux/Mac)

1. **Primeira vez - Configurar ambiente**:
   ```bash
   make api
   ```
   Isso criará o ambiente virtual e instalará as dependências automaticamente.

2. **Próximas vezes - Apenas rodar**:
   ```bash
   make run
   ```

#### Opção 2: Usando Scripts (Windows)

1. **Primeira vez - Configurar ambiente**:
   ```bash
   setup.bat
   ```

2. **Rodar aplicação**:
   ```bash
   run.bat
   ```
   Ou simplesmente:
   ```bash
   make api
   ```

#### Opção 3: Manualmente

1. **Criar ambiente virtual**:
   ```bash
   python -m venv env
   ```

2. **Ativar ambiente virtual**:
   - Windows: `env\Scripts\activate`
   - Linux/Mac: `source env/bin/activate`

3. **Instalar dependências**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Rodar aplicação**:
   ```bash
   streamlit run app.py
   ```

5. **Acesse a aplicação**:
   Abra seu navegador em `http://localhost:8501`

### Comandos Make Disponíveis

- `make api` - Configura ambiente (se necessário) e inicia a aplicação
- `make setup` - Cria e configura o ambiente virtual
- `make install` - Instala/atualiza dependências no ambiente virtual
- `make run` - Roda a aplicação Streamlit

## Estrutura do Projeto

```
.
├── app.py              # Aplicação Streamlit principal
├── models.py           # Modelos de dados (SQLAlchemy)
├── database.py         # Funções de acesso ao banco de dados
├── requirements.txt    # Dependências Python
├── Makefile           # Comandos Make
├── setup.bat          # Script de setup para Windows
├── run.bat            # Script para rodar no Windows
├── setup.sh           # Script de setup para Linux/Mac
├── env/               # Ambiente virtual (criado automaticamente)
└── data/              # Diretório do banco de dados (criado automaticamente)
```

## Banco de Dados

O sistema utiliza SQLite como banco de dados. O arquivo `estoque.db` é criado automaticamente no diretório `data/` na primeira execução.

## Exemplo de Uso

1. **Registrar um item**: 
   - Nome: "Alambrado"
   - Quantidade: 300

2. **Registrar um compromisso**:
   - Item: Alambrado
   - Quantidade: 200
   - Data Início: 01/01/2024
   - Data Fim: 05/01/2024

3. **Verificar disponibilidade**:
   - Data: 03/01/2024
   - Resultado: 100 alambrados disponíveis (300 total - 200 comprometidos)
