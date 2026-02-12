### Visão geral

Esta documentação descreve em detalhes o funcionamento completo do projeto **GestaoCarro**, com foco em permitir que **outra IA** faça qualquer tipo de manutenção sem precisar abrir os arquivos.  
Tudo está organizado por camadas (backend, frontend, dados, regras de negócio), explicando **o que cada arquivo faz**, **quais funções expõe**, **como os módulos se relacionam** e **como alterar/estender funcionalidades**.

---

## 1. Visão geral do sistema

- **Objetivo**: CRM de gestão de estoque e aluguéis para empresas de aluguel de itens de eventos, com foco em:
  - **Carros** (categoria principal)
  - **Estrutura de evento / outros itens** (pecas, container, etc.)
- **Funcionalidades principais**:
  - Cadastro e gerenciamento de **itens** (com categorias)
  - Cadastro e gerenciamento de **compromissos/aluguéis** (reservas)
  - **Verificação de disponibilidade** por período e localização
  - **Contas a receber** e **contas a pagar**
  - **Financiamentos** e cálculo de **valor presente (NPV)** com taxa SELIC/CDI
  - **Peças em carros** (ligação entre itens “carros” e itens “peças”)
  - **Auditoria** de alterações
  - **Autenticação** com token Bearer
  - **Múltiplos backends de dados**: SQLite local, Google Sheets, Supabase (selecionáveis via header)
  - **Backup** para Google Drive (quando usando Sheets)
- **Stack**:
  - Backend: **FastAPI** (Python)
  - Frontend: **React 18 + Vite + Tailwind**
  - Dados: **SQLite** (local), **Google Sheets**, **Supabase/PostgreSQL**

---

## 2. Arquitetura geral

### 2.1 Camadas

- **Frontend React** (`frontend/`):
  - Páginas em `src/pages/` (rotas)
  - Componentes reutilizáveis em `src/components/`
  - Cliente HTTP em `src/services/api.js`
  - Utilitários e listas (ex: municípios) em `src/utils/`
- **Backend FastAPI** (`backend/` + arquivos raiz):
  - Aplicação e rotas: `backend/main.py`
  - Script de execução: `backend/run.py`
  - Módulos de dados:
    - `database.py` (SQLite)
    - `sheets_database.py` (Google Sheets)
    - `supabase_database.py` (Supabase)
  - Modelos e ORM: `models.py`
  - Validações: `validacoes.py`
  - Auditoria: `auditoria.py`
  - Taxas SELIC/CDI: `taxa_selic.py`
  - Backup: `backend/backup.py`
- **Configuração / infra**:
  - Variáveis de ambiente (`.env`, `secrets`, etc.)
  - Arquivos de deploy (`render.yaml`, `supabase_schema.sql`, migrações)

### 2.2 Fluxo requisição–resposta

1. Usuário navega no **frontend** (React).
2. Frontend chama um método do cliente HTTP (`api.js`), que:
   - injeta `Authorization: Bearer <token>` (se logado)
   - injeta `X-Use-Database` (`sheets`/`supabase`) conforme seleção
3. Requisição chega ao **backend** (`main.py`):
   - middleware de autenticação valida token (se rota protegida)
   - função `get_db(request)` escolhe o módulo (`database`, `sheets_database` ou `supabase_database`)
4. A view/rota chama funções do **módulo de dados** escolhido
5. O módulo de dados:
   - usa **SQLAlchemy** (`models.py`) para SQLite  
   - usa **gspread + Google Sheets**  
   - ou usa **Supabase client** para Postgres
6. Backend retorna JSON padronizado
7. Frontend renderiza tudo em componentes/páginas.

---

## 3. Backend em detalhes

### 3.1 Estrutura de arquivos principais do backend

- **`backend/main.py`**  
  App FastAPI, rotas, autenticação, escolha do backend de dados.
- **`backend/run.py`**  
  Script para subir o servidor (uvicorn).
- **`models.py`**  
  Modelos SQLAlchemy (entidades de banco).
- **`database.py`**  
  Implementação de operações de dados usando SQLite.
- **`sheets_database.py`**  
  Implementação compatível usando Google Sheets.
- **`supabase_database.py`**  
  Implementação compatível usando Supabase (Postgres).
- **`validacoes.py`**  
  Funções utilitárias de validação.
- **`auditoria.py`**  
  Registro de ações de CREATE/UPDATE/DELETE.
- **`taxa_selic.py`**  
  Consulta SELIC/CDI + valor presente.
- **`backend/backup.py`**  
  Rotinas e endpoints para backup/restauração (Sheets).

### 3.2 `backend/main.py` – aplicação, rotas e seleção de banco

**Responsabilidade principal**: servir como “controlador” da API.

- **Inicialização da app**:
  - Cria instância `FastAPI`
  - Configura **CORS** (origens permitidas para o frontend)
  - Define dependências comuns (ex: autenticação, `get_db`)

- **Seleção de backend de dados**:
  - Função **`get_db(request)`**:
    - Lê header `X-Use-Database`:
      - `"sheets"` → usa `sheets_database`
      - `"supabase"` → usa `supabase_database`
      - Ausente/valor padrão → usa `database` (SQLite)
    - Retorna **módulo** (não instância) com interface padronizada:
      - `criar_item`, `listar_itens`, `criar_compromisso`, `criar_conta_receber`, etc.

- **Conversores utilitários**:
  - `item_to_dict(item)`: converte objeto de modelo (ou dict vindo de Sheets/Supabase) para JSON padrão.
  - `compromisso_to_dict(comp)`: idem para compromissos.
  - Mantém o formato uniforme independente do backend real.

#### Autenticação

- Variáveis de ambiente:
  - `APP_USUARIO`
  - `APP_SENHA`
- Em `POST /api/auth/login`:
  - Recebe `usuario` e `senha` no corpo
  - Compara com envs
  - Se OK, gera token via `secrets.token_urlsafe(32)` e guarda em `active_tokens`
  - Retorna token + dados básicos do usuário
- Em rotas protegidas:
  - Dependência **`verify_token(credentials: HTTPAuthorizationCredentials)`**:
    - Lê header `Authorization: Bearer <token>`
    - Verifica em `active_tokens`
    - Se inválido → 401
- **Importante para manutenção**:
  - Tokens só existem em memória; se o servidor reiniciar, sessões se perdem.
  - Para persistência/expiração de tokens deve-se criar armazenamento dedicado ou JWT.

### 3.3 Modelos de dados – `models.py`

**Responsabilidade**: mapeamento ORM das tabelas e criação de sessão.

- **Funções infra**:
  - `get_engine()` → retorna engine SQLite configurado (arquivo no disco).
  - `init_db()` → cria todas as tabelas se não existirem.
  - `get_session()` → cria sessão SQLAlchemy para cada operação.

- **Entidades principais**:

  - **`Item`**
    - Campos: `id`, `nome`, `quantidade_total`, `categoria`, `cidade`, `uf`, `endereco`, `descricao`, [campos específicos por categoria podem existir]
    - Usado para: estoque de qualquer item (carros, peças, estruturas, containers, etc.)

  - **`Carro`**
    - `item_id` (FK para `Item`), `placa`, `marca`, `modelo`, `ano`
    - Representa detalhes específicos de itens da categoria **Carros**.

  - **`Compromisso`**
    - `id`, `item_id`, `quantidade`, `data_inicio`, `data_fim`, `cidade`, `uf`, `contratante`, possivelmente `observacoes`
    - Representa uma **reserva/locação** de um item por período.

  - **`ContaReceber`**
    - `id`, `compromisso_id`, `descricao`, `valor`, `data_vencimento`, `status`
    - Liga recebíveis ao compromisso correspondente.

  - **`ContaPagar`**
    - `id`, `descricao`, `categoria`, `valor`, `data_vencimento`, `status`, `fornecedor`, `item_id` opcional
    - Registro de despesas/obrigações.

  - **`Financiamento`**
    - `id`, `item_id` (no SQLite), `codigo_contrato`, `valor_total`, `valor_entrada`, `numero_parcelas`, `taxa_juros`, possivelmente status
    - Representa financiamento ligado a um item (no SQLite) ou a vários itens (em Sheets/Supabase).

  - **`ParcelaFinanciamento`**
    - `id`, `financiamento_id`, `numero_parcela`, `valor_original`, `valor_pago`, `data_vencimento`, `data_pagamento`, status
    - Representa cada parcela de um financiamento.

  - **`PecaCarro`**
    - `id`, `peca_id` (Item categoria Peça), `carro_id` (Item categoria Carro), `quantidade`, `data_instalacao`
    - Relacionamento **N:N** entre itens “peças” e itens “carros”.

### 3.4 Módulo SQLite – `database.py`

**Responsabilidade**: prover uma implementação de todas as operações de dados usando **SQLite**.

**Principais funções (padrão de interface)**:

- **Itens**
  - `criar_item(...)`  
    Cria `Item` e, se categoria for “Carros”, também cria entrada em `Carro`.
  - `listar_itens(filtros...)`  
    Retorna lista de itens (possivelmente paginada/filtrada).
  - `buscar_item_por_id(item_id)`  
  - `atualizar_item(item_id, ...)`  
  - `deletar_item(item_id)`  

- **Compromissos**
  - `criar_compromisso(item_id, quantidade, data_inicio, data_fim, cidade, uf, contratante, ...)`
    - Antes de criar:
      - Chama `verificar_disponibilidade_periodo(...)`
  - `listar_compromissos(filtros...)`
  - `atualizar_compromisso(id, ...)`
  - `deletar_compromisso(id)`

- **Disponibilidade**
  - `verificar_disponibilidade(item_id, data_consulta, filtro_localizacao)`  
    Para uma data pontual.
  - `verificar_disponibilidade_periodo(item_id, data_inicio, data_fim, excluir_compromisso_id=None)`  
    Soma compromissos que colidem com o período e compara com `quantidade_total`.

- **Contas a receber / pagar**
  - `criar_conta_receber(compromisso_id, descricao, valor, data_vencimento, ...)`
  - `listar_contas_receber(filtros...)`, `atualizar_conta_receber`, `deletar_conta_receber`
  - `criar_conta_pagar(descricao, categoria, valor, data_vencimento, fornecedor, item_id, ...)`
  - `listar_contas_pagar`, `atualizar_conta_pagar`, `deletar_conta_pagar`

- **Financiamentos**
  - **Importante**: No SQLite, a função ainda segue o modelo antigo:
    - `criar_financiamento(item_id, valor_total, valor_entrada, numero_parcelas, taxa_juros, ...)`
    - Não aceita `itens_ids` nem `codigo_contrato` da forma mais moderna dos outros backends.
  - `listar_financiamentos(...)`, `atualizar_financiamento`, `deletar_financiamento`
  - `pagar_parcela_financiamento(parcela_id, valor_pago, data_pagamento, ...)`

- **Peças em carros**
  - `criar_peca_carro(peca_id, carro_id, quantidade, data_instalacao, ...)`
  - `listar_pecas_por_carro(carro_id)`, etc.

- **Integração com auditoria**
  - Em cada operação de **criação/atualização/remoção**, chama `auditoria.registrar_auditoria(...)` com:
    - `acao` = `"CREATE"|"UPDATE"|"DELETE"`
    - `tabela` = nome lógico (ex: `"Itens"`)
    - `registro_id`, `valores_antigos`, `valores_novos`, `usuario`.

### 3.5 Módulo Google Sheets – `sheets_database.py`

**Responsabilidade**: mesma interface de `database.py`, porém usando **Google Sheets**.

- **Obtenção de planilhas**:
  - `get_sheets()`:
    - Usa `sheets_config.py` para autenticar com conta de serviço
    - Abre a planilha por `GOOGLE_SHEET_ID`
    - Prepara referências para abas: Itens, Compromissos, Contas Receber, etc.

- **Cache & rate limiting**:
  - Mantém cache em memória com TTL curto para leituras (evitar ultrapassar limites do Google).
  - Função de limpeza via rota `/api/cache/clear`.

- **Operações CRUD**:
  - Mesmas assinaturas de função que `database.py`, mas:
    - Ao criar, escreve linhas na planilha (cada linha = registro).
    - Ao atualizar, localiza linha por ID.
    - Ao excluir, ou limpa a linha ou marca como inativa (dependendo da implementação).

- **Financiamentos** (versão mais avançada):
  - `criar_financiamento(itens_ids, codigo_contrato, valor_total, valor_entrada, numero_parcelas, taxa_juros, ...)`
    - Suporta **vários itens** por financiamento.
    - Usa uma aba intermediária `Financiamentos_Itens`:
      - Campos: `financiamento_id`, `item_id`, `valor_proporcional` etc.
    - Nessa implementação, `item_id` deixa de ser único por financiamento.

### 3.6 Módulo Supabase – `supabase_database.py`

**Responsabilidade**: repetir a mesma interface de `database.py` usando **Supabase** (PostgreSQL).

- **Inicialização**:
  - `get_supabase()`:
    - Usa `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`/`SUPABASE_KEY`
    - Cria cliente Supabase.
- **Estrutura de dados**:
  - Tabelas no Supabase espelham as do SQLite + tabelas adicionais:
    - `itens`, `carros`, `compromissos`, `contas_receber`, `contas_pagar`,
      `financiamentos`, `parcelas_financiamento`, `financiamentos_itens`, `pecas_carros`, etc.
  - Migrações e schema em:
    - `supabase_schema.sql`
    - `supabase_migration_*.sql`

- **Financiamentos**:
  - Igual ao Google Sheets:
    - `criar_financiamento(itens_ids, codigo_contrato, ...)`
    - Usa tabela de ligação `financiamentos_itens` (N:N).

### 3.7 Validações – `validacoes.py`

**Responsabilidade**: funções reutilizáveis de validação.

- **Padrão de retorno**:
  - `(bool, str)` → `(é_valido, mensagem_erro_ou_vazio)`

- **Principais funções**:
  - `validar_uf(uf)`:
    - Normaliza para `uf.upper()[:2]`
    - Confere se está em lista de UFs conhecidas.
  - `validar_placa(placa)`:
    - Verifica formato de placa Mercosul/tradicional.
  - `validar_quantidade(quantidade, permitir_zero=False)`:
    - Garante não-negatividade; se `permitir_zero=False`, precisa ser > 0.
  - `validar_datas(data_inicio, data_fim, permitir_passado=False)`:
    - Garante `data_inicio <= data_fim`.
    - Se `permitir_passado=False`, datas não podem estar totalmente no passado.
  - `validar_ano(ano, ...)`, `validar_item_completo(...)`, `validar_compromisso_completo(...)`:
    - Validam coesão mínima dos payloads.

### 3.8 Auditoria – `auditoria.py`

**Responsabilidade**: registrar histórico de mudanças.

- **Função principal**:
  - `registrar_auditoria(acao, tabela, registro_id, valores_antigos, valores_novos, usuario)`:
    - Armazena log com:
      - Data/hora
      - Usuário (extraído do token ou “sistema”)
      - Ação (create/update/delete)
      - Antes/depois
  - `obter_historico(tabela, registro_id)`:
    - Lê histórico para exibição futura.

- **Backend de armazenamento**:
  - Pode usar:
    - Abas específicas no Google Sheets
    - Ou tabela dedicada em SQLite/Supabase.

### 3.9 Taxas SELIC/CDI – `taxa_selic.py`

**Responsabilidade**: buscar taxas e calcular valor presente de parcelas.

- **Funções**:
  - `obter_taxa_selic()`:
    - Chama API do Banco Central (ex: `https://api.bcb.gov.br/...`)
    - Converte taxa anual para taxa mensal equivalente.
  - `obter_taxa_cdi()`:
    - Similar, usando o endpoint da CDI.
  - `calcular_valor_presente(parcelas, taxa_desconto, usar_cdi=False)`:
    - Recebe lista de parcelas (valor, data_vencimento).
    - Usa **taxa de desconto** (SELIC ou CDI).
    - Calcula **NPV** (valor presente).

- **Uso**:
  - Endpoint `GET /api/financiamentos/{id}/valor-presente`:
    - Carrega financiamento + parcelas
    - Chama `calcular_valor_presente(...)`
    - Retorna valor presente e detalhes.

### 3.10 Backup – `backend/backup.py`

**Responsabilidade**: lidar com backup/restauração, principalmente quando usando Google Sheets.

- **Funções típicas**:
  - `criar_backup()`:
    - Exporta estrutura/abas da planilha para arquivo de backup (local/Drive).
  - `listar_backups()`:
    - Retorna lista de backups existentes (nome, data).
  - `restaurar_backup(backup_id)`:
    - Reimporta dados de um backup específico.
- **Endpoints**:
  - `POST /api/backup/criar`
  - `GET /api/backup/listar`
  - `POST /api/backup/restaurar`

### 3.11 Rotas principais da API

Agrupamento lógico (pode haver variações na implementação exata, mas o padrão é este):

- **Autenticação**
  - `POST /api/auth/login`
  - `POST /api/auth/logout`

- **Itens**
  - `GET /api/itens`
  - `GET /api/itens/buscar` (busca/paginação/filtros)
  - `GET /api/itens/{id}`
  - `POST /api/itens`
  - `PUT /api/itens/{id}`
  - `DELETE /api/itens/{id}`
  - `GET /api/categorias`
  - `GET /api/categorias/{categoria}/campos` (campos dinâmicos para cada categoria)

- **Compromissos / calendário**
  - `GET /api/compromissos`
  - `GET /api/compromissos/{id}`
  - `POST /api/compromissos`
  - `PUT /api/compromissos/{id}`
  - `DELETE /api/compromissos/{id}`

- **Disponibilidade**
  - `POST /api/disponibilidade` (pode receber item_id + datas)

- **Financeiro – contas a receber**
  - `GET /api/contas-receber`
  - `POST /api/contas-receber`
  - `PUT /api/contas-receber/{id}`
  - `DELETE /api/contas-receber/{id}`

- **Financeiro – contas a pagar**
  - `GET /api/contas-pagar`
  - `POST /api/contas-pagar`
  - `PUT /api/contas-pagar/{id}`
  - `DELETE /api/contas-pagar/{id}`

- **Financeiro – dashboards**
  - `GET /api/financeiro/dashboard`
  - `GET /api/financeiro/fluxo-caixa`

- **Financiamentos**
  - `GET /api/financiamentos`
  - `GET /api/financiamentos/{id}`
  - `POST /api/financiamentos`
  - `PUT /api/financiamentos/{id}`
  - `DELETE /api/financiamentos/{id}`
  - `POST /api/financiamentos/{id}/parcelas/{parcela_id}/pagar`
  - `GET /api/financiamentos/{id}/valor-presente`

- **Peças em carros**
  - `GET /api/pecas-carros`
  - `POST /api/pecas-carros`
  - `PUT /api/pecas-carros/{id}`
  - `DELETE /api/pecas-carros/{id}`

- **Cache e backup**
  - `POST /api/cache/clear`
  - `POST /api/backup/criar`
  - `GET /api/backup/listar`
  - `POST /api/backup/restaurar`

---

## 4. Frontend em detalhes

### 4.1 Estrutura de pastas principais

- **`frontend/src/main.jsx`**
  - Ponto de entrada React.
  - Renderiza `App` dentro de `<BrowserRouter>`.

- **`frontend/src/App.jsx`**
  - Define as **rotas** usando React Router.
  - Implementa um **`ProtectedRoute`**:
    - Checa token no `localStorage`.
    - Redireciona para `/login` se não autenticado.
  - Envolve páginas com `Layout` (sidebar/menu).

- **`frontend/src/components/`**
  - Componentes visuais e funcionais reutilizáveis.

- **`frontend/src/pages/`**
  - Cada arquivo é uma página/rota.

- **`frontend/src/services/api.js`**
  - Cliente Axios centralizado para chamadas de API.

- **`frontend/src/utils/`**
  - `format.js`: formatação de datas, valores etc.
  - `municipios.js`: lista de municípios (para selects, etc.).

### 4.2 Cliente HTTP – `src/services/api.js`

**Responsabilidade**: fornecer instâncias Axios já configuradas.

- **Configuração base**:
  - `baseURL`:
    - Vem de `import.meta.env.VITE_API_URL` ou fallback (ex: `http://localhost:8000`).
- **Interceptors**:
  - **Request**:
    - Lê token do `localStorage`.
    - Adiciona `Authorization: Bearer <token>` se existir.
    - Lê seleção de banco (`sheets`/`supabase`) (ex: guardado no `localStorage` ou contexto) e adiciona `X-Use-Database`.
  - **Response**:
    - Se 401:
      - Remove token e dados do usuário.
      - Redireciona para `/login`.
    - Se 500: log no console.

- **APIs agrupadas**:
  - **`authAPI`**:
    - `login(credentials)` → POST `/api/auth/login`.
  - **`itensAPI`**, **`compromissosAPI`**, **`disponibilidadeAPI`**, **`statsAPI`**, **`categoriasAPI`**:
    - CRUD e buscas específicas.
  - **`contasReceberAPI`**, **`contasPagarAPI`**, **`financeiroAPI`**:
    - Operações financeiras.
  - **`financiamentosAPI`**:
    - CRUD + pagamento de parcelas + consulta de valor presente.

### 4.3 Componentes reutilizáveis

- **`Layout.jsx`**
  - Contém:
    - Sidebar com links para:
      - Dashboard, Itens, Compromissos, Disponibilidade, Calendário, Financeiro, Financiamentos etc.
    - Área principal onde as páginas são renderizadas.
    - Possível toggle de banco (`sheets`/`supabase`) que altera `X-Use-Database`.
- **`Modal.jsx`**
  - Container genérico de modal (fundo escurecido, centralização).
- **`ConfirmDialog.jsx`**
  - Diálogo para confirmar ações destrutivas (delete etc.).
- **`StatusBadge.jsx`**
  - Badge colorida para status (ex: **Pago**, **Pendente**, **Vencido**).
- **`FiltroPeriodo.jsx`**
  - Inputs de datas (início/fim) e callback onChange.
- **`TabelaParcelas.jsx`**
  - Recebe lista de parcelas de financiamento e exibe linhas com:
    - número, valor_original, valor_pago, status.
  - Botão para pagar parcela.
- **`CalculadoraNPV.jsx` / `ValorPresenteCard.jsx`**
  - Interface para mostrar resultado do cálculo de valor presente.

### 4.4 Páginas – `src/pages/`

- **`Login.jsx`**
  - Formulário com `usuario`, `senha`.
  - Usa `authAPI.login`.
  - Salva token no `localStorage` e redireciona para `/`.

- **`Dashboard.jsx`**
  - Página inicial após login.
  - Pode exibir:
    - KPIs de itens disponíveis
    - Resumo financeiro (receber/pagar)
    - Próximos compromissos.

- **`Itens.jsx`**
  - Lista de itens com filtros.
  - Formulário de criação/edição com campos dinâmicos por categoria.
  - Usa `itensAPI` para CRUD.
  - Ao salvar:
    - Chama `POST /api/itens` ou `PUT /api/itens/{id}`.

- **`Compromissos.jsx`**
  - Lista de compromissos.
  - Formulário para criar/editar:
    - Seleciona item, quantidade, `data_inicio`, `data_fim`, cidade/UF, contratante.
  - Usa `compromissosAPI`.

- **`Disponibilidade.jsx`**
  - Form para escolher item + período + localização.
  - Usa `disponibilidadeAPI` para verificar disponibilidade e mostrar resultado.

- **`Calendario.jsx`**
  - Visualização tipo calendário dos compromissos:
    - Pode usar biblioteca React Calendar ou custom.
    - Consome lista de compromissos e agrupa por dia.

- **`VisualizarDados.jsx`**
  - Página mais “CRUD genérico”:
    - Permite navegar entre diferentes tipos de dados (itens, compromissos, contas, etc.)
    - Visualizar, editar e excluir registros.

- **`ContasReceber.jsx`**
  - Tabela de contas a receber.
  - Filtros por status (Pendente, Pago, Vencido).
  - Formulário para criar/editar recebíveis.
  - Usa `contasReceberAPI`.

- **`ContasPagar.jsx`**
  - Tabela de contas a pagar.
  - Filtros por status/categoria.
  - Formulário para criar/editar.
  - Usa `contasPagarAPI`.

- **`DashboardFinanceiro.jsx`**
  - Resumo financeiro:
    - Total de receber x pagar
    - Fluxo de caixa em gráfico/tabela.
  - Usa `financeiroAPI.dashboard` e `financeiroAPI.fluxoCaixa`.

- **`Financiamentos.jsx`**
  - Lista de financiamentos (tabela).
  - Formulário de criação/edição:
    - Seleciona 1+ itens (`itens_ids`)
    - Define valores, entrada, parcelas, taxa de juros.
  - Exibe tabela de parcelas.
  - Botão “pagar parcela” chama `financiamentosAPI.pagarParcela`.
  - Botão para calcular valor presente (`financiamentosAPI.valorPresente`).

---

## 5. Modelo de dados e relacionamentos

### 5.1 Visão geral

- **Item**: entidade base de **estoque**.
- **Carro**: detalhes extras para itens de categoria “Carros”.
- **Compromisso**: “reserva/locação” de um item.
- **ContaReceber**: recebíveis ligados a compromissos.
- **ContaPagar**: despesas gerais (com ou sem vínculo a item).
- **Financiamento**: contrato financeiro de aquisição.
- **ParcelaFinanciamento**: uma parcela de financiamento.
- **PecaCarro**: relação N:N entre itens “peças” e “carros”.
- **Financiamentos_Itens** (Sheets/Supabase, não existe nativamente no SQLite): relação N:N entre financiamentos e itens.

### 5.2 Diagrama lógico textual

- `Item (1) ─── (1) Carro`
- `Item (1) ─── (N) Compromisso`
- `Compromisso (1) ─── (N) ContaReceber`
- `Item (1) ─── (N) ContaPagar` (opcional)
- `Item (1) ─── (N) Financiamento` (no SQLite)
- `Financiamento (1) ─── (N) ParcelaFinanciamento`
- `Financiamento (N) ─── (N) Item` (via `Financiamentos_Itens` em Sheets/Supabase)
- `Item (N) ─── (N) Item` (Peças x Carros, via `PecaCarro`)

### 5.3 Campos e regras principais

- **Item**
  - `quantidade_total`:
    - Deve ser >= 0.
    - É usada como capacidade máxima para compromissos.
- **Compromisso**
  - `data_inicio <= data_fim`.
  - Não pode exceder disponibilidade existente (ver função de verificação).
- **ContaReceber / ContaPagar**
  - Possuem `status`:
    - Receber: `Pendente`, `Pago`, `Vencido`.
    - Pagar: `Pendente`, `Paga`, `Atrasada`.
- **Financiamento**
  - `valor_entrada <= valor_total`.
  - Soma das parcelas deve fechar com `valor_total - valor_entrada` (respeitando pequenas diferenças de arredondamento).
- **PecaCarro**
  - `peca_id` aponta para `Item` com categoria “Peças”.
  - `carro_id` aponta para `Item` com categoria “Carros`.

---

## 6. Fluxos de negócio principais

### 6.1 Autenticação

1. Usuário acessa `/login`.
2. Frontend envia `usuario` + `senha` para `POST /api/auth/login`.
3. Backend compara com `APP_USUARIO` e `APP_SENHA`.
4. Se válido:
   - Gera token e guarda em memória.
   - Retorna token.
5. Frontend:
   - Guarda token em `localStorage`.
   - Rotas protegidas só renderizam se token presente.

### 6.2 Cadastro/edição de item

1. Página `Itens.jsx` monta formulário:
   - Campos comuns: `nome`, `categoria`, `quantidade_total`, `cidade`, `uf`, `endereco`, `descricao`.
   - Campos específicos:
     - Para “Carros”: `placa`, `marca`, `modelo`, `ano`.
2. Ao salvar:
   - Chama `itensAPI.criar` ou `itensAPI.atualizar`.
3. Backend:
   - Em `POST /api/itens` ou `PUT /api/itens/{id}`:
     - Usa `get_db` para escolher backend de dados.
     - Chama `validar_item_completo`.
     - Se categoria = “Carros`, também registra/atualiza em `Carro`.
     - Chama `db_module.criar_item` / `db_module.atualizar_item`.
     - Registra auditoria.

### 6.3 Cadastro/edição de compromisso

1. Página `Compromissos.jsx`:
   - Usuário escolhe item, define quantidade, `data_inicio`, `data_fim`, cidade/UF, contratante.
2. Ao salvar:
   - Chama `compromissosAPI.criar` ou `compromissosAPI.atualizar`.
3. Backend:
   - Em `POST /api/compromissos`:
     - `validar_compromisso_completo`.
     - `db_module.verificar_disponibilidade_periodo`:
       - Soma compromissos que colidem com intervalo.
       - Se `quantidade_solicitada + quantidade_reservada > quantidade_total` → erro.
     - Se ok, `db_module.criar_compromisso`.
     - Cria automaticamente conta a receber associada (opcional, dependendo da versão).
     - Registra auditoria.

### 6.4 Verificação de disponibilidade

1. Página `Disponibilidade.jsx`:
   - Formulário: item, data ou período, cidade/UF (opcional).
2. Ao consultar:
   - Chama `POST /api/disponibilidade` com os parâmetros.
3. Backend:
   - `db_module.verificar_disponibilidade` ou `verificar_disponibilidade_periodo`.
   - Retorna:
     - `quantidade_total`
     - `quantidade_reservada`
     - `quantidade_disponivel`
     - Lista de compromissos que impactam.

### 6.5 Contas a receber

1. Geralmente ligadas à criação de compromissos.
2. Página `ContasReceber.jsx`:
   - Carrega via `contasReceberAPI.listar`.
   - Permite alterar status para “Pago”, “Vencido”.
3. Backend:
   - `db_module.criar_conta_receber` / `atualizar_conta_receber`.

### 6.6 Contas a pagar

1. Página `ContasPagar.jsx`:
   - Usuário pode cadastrar despesas diversas (combustível, manutenção, etc.).
2. Backend:
   - `db_module.criar_conta_pagar`, `listar`, `atualizar`, `deletar`.

### 6.7 Financiamentos e parcelas

1. Página `Financiamentos.jsx`:
   - Usuário define:
     - Lista de itens (`itens_ids`)
     - `valor_total`, `valor_entrada`, `numero_parcelas`, `taxa_juros`, `codigo_contrato`.
   - Pode escolher gerar parcelas automaticamente ou manualmente.
2. Ao salvar:
   - Chama `financiamentosAPI.criar`.
3. Backend:
   - Em `POST /api/financiamentos`:
     - Se backend de dados for Sheets/Supabase:
       - `db_module.criar_financiamento(itens_ids, codigo_contrato, ...)`.
     - Se backend for SQLite:
       - **Cuidado**: implementação aceita só `item_id` (provável uso de `itens_ids[0]`).
     - Cria registros em `financiamentos_itens` (Sheets/Supabase) ou só `item_id` (SQLite).
     - Gera `parcelas_financiamento`.
4. Pagamento de parcela:
   - Clique em “Pagar” em `TabelaParcelas`.
   - Chama `financiamentosAPI.pagarParcela(financiamentoId, parcelaId, data_pagamento, valor_pago)`.
   - Backend:
     - `db_module.pagar_parcela_financiamento`.
     - Atualiza `valor_pago` e `data_pagamento`.
     - Se todas as parcelas quitadas → status do financiamento = `Quitado`.

### 6.8 Cálculo de valor presente (NPV)

1. Em `Financiamentos.jsx`, botão tipo “Calcular valor presente”.
2. Chama `GET /api/financiamentos/{id}/valor-presente`.
3. Backend:
   - Carrega financiamento + parcelas.
   - Chama:
     - `obter_taxa_selic()` ou `obter_taxa_cdi()` em `taxa_selic.py`.
     - `calcular_valor_presente(parcelas, taxa)` com base na data de hoje.
   - Retorna valor presente.
4. Frontend:
   - Exibe em `ValorPresenteCard`.

### 6.9 Peças em carros

1. Em alguma interface (página específica ou dentro de item/carro):
   - Usuário seleciona um carro e uma peça (itens do tipo “Peças”), quantidade, data de instalação.
2. Chamada para `POST /api/pecas-carros`.
3. Backend:
   - `db_module.criar_peca_carro(peca_id, carro_id, quantidade, data_instalacao)`.
   - Pode ajustar disponibilidade de peças (especialmente em Sheets/Supabase).

### 6.10 Backup e restauração (quando usando Sheets)

1. Tela administrativa (se existir) ou chamada manual:
   - `POST /api/backup/criar` → cria backup.
   - `GET /api/backup/listar` → lista backups.
   - `POST /api/backup/restaurar` → restaura.
2. Backend:
   - Usa `backend/backup.py` + Google Drive API ou armazenamento local.

---

## 7. Configuração, ambientes e deploy

- **Variáveis de ambiente principais**:
  - `APP_USUARIO`, `APP_SENHA`
  - `GOOGLE_SHEET_ID`, `GOOGLE_CREDENTIALS`
  - `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`
  - `VITE_API_URL` (frontend)
  - `USE_GOOGLE_SHEETS`, `RENDER`, `DEBUG`, etc.

- **Deploy backend**:
  - `render.yaml` (raiz ou pasta backend) define:
    - Comando: `uvicorn main:app --host 0.0.0.0 --port $PORT`
  - `runtime.txt` indica versão Python.

- **Deploy frontend**:
  - `frontend/render.yaml` (ou similar) define build `npm run build` e serve estático.

- **Scripts de desenvolvimento**:
  - `start-dev.py`:
    - Sobe backend e frontend juntos (ex: via subprocess/threads).
  - `start-dev.bat` / `.ps1`:
    - Atalhos para Windows.

---

## 8. Convenções e pontos críticos para manutenção

- **Interface única de dados**:
  - Os 3 módulos (`database.py`, `sheets_database.py`, `supabase_database.py`) devem ter **mesmas funções** e **assinaturas compatíveis**.
  - Ao adicionar nova operação, é obrigatório implementá-la nos 3.

- **Validações centralizadas**:
  - Sempre usar funções de `validacoes.py` em vez de replicar lógica.
  - Isso facilita mudar regras de negócio (por exemplo, formato de placa).

- **Auditoria obrigatória**:
  - Toda alteração significativa de dados deve chamar `auditoria.registrar_auditoria`.

- **Tratamento de erros**:
  - Para erros de validação → HTTP 400 (Bad Request).
  - Para não encontrado → HTTP 404.
  - Para não autorizado → 401.
  - Para falhas internas → 500 (evitar expor detalhes sensíveis).

- **Diferenças de backend**:
  - **Ponto crítico**: Financiamentos em SQLite vs Sheets/Supabase:
    - SQLite: 1 financiamento ↔ 1 item (`item_id`).
    - Sheets/Supabase: 1 financiamento ↔ N itens (`itens_ids`) + tabela de ligação.
  - Qualquer mudança nessa área exige atenção especial para manter compatibilidade.

---

## 9. Guia prático de manutenção para uma IA

### 9.1 Adicionar um novo campo em `Item`

1. **Backend – modelo**:
   - Adicionar campo em `models.py` na classe `Item`.
   - Rodar migração no SQLite (ajustar schema) e Supabase (SQL).
2. **Módulos de dados**:
   - Em `database.py`:
     - Incluir o novo campo em `criar_item`, `atualizar_item`, `listar_itens`, etc.
   - Em `sheets_database.py`:
     - Adicionar coluna correspondente na aba `Itens`.
     - Ajustar mapeamento (índices de colunas).
   - Em `supabase_database.py`:
     - Garantir que a coluna exista na tabela `itens` e está sendo lida/escrita.
3. **Serialização**:
   - Atualizar `item_to_dict` em `backend/main.py` para incluir o campo.
4. **Frontend**:
   - Em `Itens.jsx`:
     - Adicionar campo ao formulário.
     - Incluir no payload enviado para criação/edição.
   - Atualizar exibição na tabela (se necessário).
5. **Validações (opcional)**:
   - Se o campo precisa de regra específica, criar função em `validacoes.py`.

### 9.2 Criar uma nova categoria de item

1. **Definir regras de negócio**:
   - Que campos específicos essa categoria terá?
   - Há alguma lógica especial de disponibilidade?

2. **Backend**:
   - Em `sheets_database.py` / `supabase_database.py`:
     - Adicionar lógica de campos dinâmicos em `obter_campos_categoria(categoria)`.
   - Em `database.py`:
     - Se esta categoria tiver tabela auxiliar (como `Carro`), criar novo modelo e relacionamentos em `models.py`.
     - Atualizar funções `criar_item` / `atualizar_item` para tratar a categoria.

3. **Frontend**:
   - Em `frontend/src/pages/Itens.jsx`:
     - Incluir a categoria na lista de opções.
     - Exibir campos extras no formulário condicionalmente à categoria.
   - Se necessário, criar página/componente específico.

### 9.3 Adicionar um novo endpoint (ex.: relatório customizado)

1. **Backend**:
   - Em `backend/main.py`:
     - Criar nova rota (ex: `GET /api/relatorios/xyz`).
     - No corpo da rota:
       - Usar `db_module` para buscar dados necessários.
       - Combinar/transformar resultados.
       - Retornar JSON.

2. **Módulos de dados**:
   - Via de regra, crie funções **genéricas** em `database.py`, `sheets_database.py` e `supabase_database.py` para buscar os dados, em vez de fazer SQL bruto dentro de `main.py`.
   - Exemplo: `listar_compromissos_por_periodo(...)`.

3. **Frontend**:
   - Criar novo serviço em `api.js` ou estender um existente.
   - Criar nova página ou componente para exibir o relatório.

### 9.4 Alterar regra de disponibilidade

1. Localizar funções:
   - `verificar_disponibilidade` / `verificar_disponibilidade_periodo` nos módulos de dados.
2. Ajustar regra:
   - Por exemplo, considerar apenas compromissos com status “Confirmado” e ignorar “Rascunho”.
   - Ou aplicar filtros mais complexos de localização.
3. Garantir consistência:
   - Replicar mudança em `database.py`, `sheets_database.py`, `supabase_database.py`.
4. Frontend:
   - Se o payload da API mudar (novos filtros, campos de retorno), atualizar `Disponibilidade.jsx` e `disponibilidadeAPI`.

### 9.5 Migrar lógica de financiamento para ser igual em todos backends

1. **Objetivo**: alinhar `database.py` com o modelo multi-itens de Sheets/Supabase.
2. Passos:
   - Criar tabela de ligação `financiamentos_itens` no SQLite (modelo em `models.py` + migração).
   - Alterar assinatura de `criar_financiamento` em `database.py` para aceitar `itens_ids` e `codigo_contrato`.
   - Adaptar endpoints em `backend/main.py` para usar **sempre** `itens_ids`, independentemente do backend.
   - Atualizar quaisquer pontos do frontend que assumam um único `item_id`.
3. Testar:
   - Criar financiamento com múltiplos itens em todos backends.
   - Verificar cálculo de parcelas e valor presente.

---

Se você (outra IA) seguir esta documentação, conseguirá:

- Localizar rapidamente **qual módulo** é responsável por cada funcionalidade.
- Entender **como os dados fluem** do frontend para o banco e vice-versa.
- Adaptar regras de negócio, adicionar entidades, campos e rotas mantendo a **compatibilidade entre SQLite, Google Sheets e Supabase**.
- Evoluir a parte de **financiamentos**, **disponibilidade**, **auditoria** e **integrações externas** de forma segura.

