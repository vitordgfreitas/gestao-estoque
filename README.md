# Sistema de Gestão de Estoque - CRM Profissional

Sistema de gestão de estoque para empresas de aluguel de itens de eventos, desenvolvido com **FastAPI** (backend) e **React** (frontend).

## Arquitetura

- **Backend**: FastAPI (Python) - API RESTful
- **Frontend**: React + Vite + Tailwind CSS
- **Banco de Dados**: SQLite ou Google Sheets (configurável)

## Funcionalidades

- 📊 **Dashboard**: Visão geral com KPIs e gráficos
- ➕ **Registrar Itens**: Cadastre itens com campos dinâmicos por categoria
- 📅 **Registrar Compromissos**: Registre aluguéis com período e localização
- 🔍 **Verificar Disponibilidade**: Consulte disponibilidade com filtros e agrupamento
- 📅 **Calendário**: Visualize compromissos em formato mensal, semanal ou diário
- 📋 **Visualizar Dados**: Gerencie itens e compromissos com edição e exclusão

## Pré-requisitos

- Python 3.8 ou superior
- Node.js 16+ e npm
- Google Sheets API (opcional, se usar Google Sheets)

## Instalação e Execução

### 1. Backend

```bash
cd backend
python -m venv venv
.\venv\Scripts\activate  # Windows
# ou
source venv/bin/activate  # Linux/Mac

pip install -r requirements.txt
python run.py
```

O backend estará disponível em `http://localhost:8000`

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

O frontend estará disponível em `http://localhost:5173`

### 3. Executar Tudo (Windows)

Use os scripts fornecidos:

```bash
start-dev.bat
```

ou PowerShell:

```powershell
.\start-dev.ps1
```

Isso iniciará tanto o backend quanto o frontend simultaneamente.

## Configuração

### Google Sheets (Opcional)

1. Coloque o arquivo `credentials.json` na raiz do projeto
2. Configure a variável de ambiente `GOOGLE_SHEET_ID` com o ID da planilha
3. O sistema detectará automaticamente e usará Google Sheets

### SQLite (Padrão)

Se não configurar Google Sheets, o sistema usará SQLite automaticamente. O banco será criado em `data/estoque.db`.

## Estrutura do Projeto

```
GestaoCarro/
├── backend/           # API FastAPI
│   ├── main.py       # Aplicação principal
│   ├── run.py        # Script de execução
│   └── requirements.txt
├── frontend/          # Aplicação React
│   ├── src/
│   │   ├── pages/     # Páginas da aplicação
│   │   ├── components/ # Componentes reutilizáveis
│   │   └── services/  # Serviços de API
│   └── package.json
├── models.py          # Modelos SQLAlchemy
├── database.py        # Acesso SQLite
├── sheets_database.py # Acesso Google Sheets
└── sheets_config.py   # Configuração Google Sheets
```

## API Endpoints

- `GET /api/itens` - Listar itens
- `POST /api/itens` - Criar item
- `PUT /api/itens/{id}` - Atualizar item
- `DELETE /api/itens/{id}` - Deletar item
- `GET /api/compromissos` - Listar compromissos
- `POST /api/compromissos` - Criar compromisso
- `GET /api/categorias` - Listar categorias
- `GET /api/categorias/{categoria}/campos` - Obter campos da categoria
- `POST /api/disponibilidade` - Verificar disponibilidade
- `GET /api/stats` - Estatísticas gerais

Documentação interativa disponível em `http://localhost:8000/docs`

## Desenvolvimento

O projeto usa:
- **FastAPI** para backend rápido e moderno
- **React** com hooks e componentes funcionais
- **Tailwind CSS** para estilização
- **Framer Motion** para animações
- **Recharts** para gráficos
- **React Hot Toast** para notificações

## Licença

Este projeto é de uso interno.
