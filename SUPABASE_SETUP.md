# Configuração do Supabase para GestaoCarro

Este guia explica como criar um projeto no Supabase e configurar o app para usar Supabase como banco de dados (com toggle para alternar entre Google Sheets e Supabase).

---

## 1. Criar projeto no Supabase

1. Acesse [https://supabase.com](https://supabase.com) e faça login.
2. Clique em **New Project**.
3. Preencha:
   - **Name**: ex. `gestaocarro`
   - **Database Password**: crie uma senha forte e **guarde** (você vai usar só para acessar o dashboard; o app usa a **Service Role Key**).
   - **Region**: escolha a mais próxima (ex. South America (São Paulo)).
4. Clique em **Create new project** e aguarde o provisionamento (1–2 min).

---

## 2. Executar o SQL do schema

1. No projeto, abra **SQL Editor** (menu lateral).
2. Clique em **New query**.
3. Abra o arquivo **`supabase_schema.sql`** na raiz do projeto GestaoCarro.
4. Copie **todo** o conteúdo e cole no editor SQL do Supabase.
5. Clique em **Run** (ou Ctrl+Enter).
6. Confirme que a execução terminou sem erros (todas as tabelas e índices criados).

As tabelas criadas são: `categorias_itens`, `itens`, `carros`, `compromissos`, `contas_receber`, `contas_pagar`, `financiamentos`, `financiamentos_itens`, `parcelas_financiamento`, `pecas_carros`, e a tabela **`pecas`** (itens da categoria "Pecas").

**No Supabase**, a categoria de peças chama-se **"Pecas"** (não "Peças de Carro"). Itens dessa categoria ficam na tabela `pecas`; a associação peça↔carro fica em `pecas_carros`. Se você já tinha o schema sem a categoria Pecas, rode **`supabase_migration_categoria_pecas.sql`** no SQL Editor.

O schema também cria a função **`criar_tabela_categoria`**: quando você cadastra uma **nova categoria** no app (Supabase), uma tabela é criada automaticamente no SQL com o nome da categoria em minúsculas e com espaços em `_` (ex.: "Reboques" → tabela `reboques`). Se você já tinha o schema antigo, rode o arquivo **`supabase_migration_criar_tabela_categoria.sql`** no SQL Editor para adicionar essa função.

---

## 3. Onde salvar as credenciais

O backend precisa de **duas** variáveis de ambiente. Você pode configurá-las de duas formas:

### Opção A: Arquivo `.env` (desenvolvimento local)

Na **raiz do projeto** (ou na pasta `backend`), crie ou edite o arquivo **`.env`** e adicione:

```env
SUPABASE_URL=https://SEU_PROJECT_REF.supabase.co
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

Substitua:
- `SEU_PROJECT_REF` pelo **Reference ID** do seu projeto (em **Settings → General** no Supabase).
- `eyJ...` pela **service_role key** (ver passo 4 abaixo).

### Opção B: Variáveis de ambiente no Render (produção)

1. No [Render](https://render.com), abra seu **serviço backend**.
2. Vá em **Environment** (ou **Environment Variables**).
3. Adicione:
   - **Key**: `SUPABASE_URL`  
     **Value**: `https://SEU_PROJECT_REF.supabase.co`
   - **Key**: `SUPABASE_SERVICE_KEY`  
     **Value**: a chave **service_role** (secret) do passo 4.
4. Salve e faça um novo deploy se necessário.

**Importante:** não commite o `.env` no Git (ele já deve estar no `.gitignore`). No Render, use sempre as variáveis do painel.

---

## 4. Quais credenciais usar

No Supabase:

1. **Settings** (ícone de engrenagem) → **API**.
2. Em **Project URL**:
   - Copie a URL (ex. `https://abcdefgh.supabase.co`).  
   - Essa é o valor de **`SUPABASE_URL`**.

3. Em **Project API keys**:
   - **anon (public)** – não use para o backend.
   - **service_role (secret)** – use esta.
   - Clique em **Reveal** ao lado de **service_role** e copie a chave (começa com `eyJ...`).  
   - Essa é o valor de **`SUPABASE_SERVICE_KEY`**.

Resumo:

| Variável               | Onde achar no Supabase        | Onde salvar                          |
|------------------------|--------------------------------|--------------------------------------|
| `SUPABASE_URL`         | Settings → API → Project URL   | `.env` ou Environment no Render      |
| `SUPABASE_SERVICE_KEY` | Settings → API → service_role | `.env` ou Environment no Render     |

**Segurança:** a **service_role** ignora Row Level Security (RLS). Não exponha essa chave no frontend; use apenas no backend.

---

## 5. Toggle no app

Com as variáveis configuradas e o backend reiniciado:

1. O backend detecta Supabase e passa a aceitar o header **`X-Use-Database: supabase`**.
2. No frontend, na **barra lateral** (footer), aparece o toggle **“Usar Supabase”** (só se o backend informar que Supabase está disponível).
3. Ao **ativar** o toggle:
   - O frontend grava a preferência no `localStorage` e recarrega a página.
   - As próximas requisições enviam `X-Use-Database: supabase` e o backend usa o Supabase para todas as operações.
4. Ao **desativar** o toggle, o app volta a usar o Google Sheets (ou SQLite, conforme configurado).

Ou seja: **Google Sheets** e **Supabase** podem coexistir; o toggle só escolhe qual banco o backend usa naquele momento.

---

## 6. Checklist rápido

- [ ] Projeto criado no Supabase  
- [ ] SQL do `supabase_schema.sql` executado no SQL Editor  
- [ ] `SUPABASE_URL` no `.env` (local) ou no Environment do Render  
- [ ] `SUPABASE_SERVICE_KEY` (service_role) no `.env` ou no Render  
- [ ] Backend reiniciado (ou redeploy no Render)  
- [ ] Toggle “Usar Supabase” visível no app e alternando entre Sheets e Supabase sem erro  

---

## 7. Dependência Python

O backend usa o cliente oficial do Supabase. No `backend/requirements.txt` já está:

```text
supabase==2.10.0
```

Se instalar manualmente: `pip install supabase`.

---

## 8. Solução de problemas

- **Toggle não aparece**  
  Verifique se `SUPABASE_URL` e `SUPABASE_SERVICE_KEY` estão definidas e se o backend foi reiniciado. O endpoint `/api/info` deve retornar `supabase_available: true`.

- **Erro ao criar item / compromisso / etc. com Supabase**  
  Confirme que o SQL do `supabase_schema.sql` foi executado por completo e que não há erro nas tabelas (Table Editor no Supabase).

- **401 / 403 no Supabase**  
  Use a chave **service_role**, não a **anon**. A service_role está em Settings → API → Project API keys.

- **Dados diferentes entre Sheets e Supabase**  
  São bancos separados. O que for criado/alterado no Supabase não aparece no Sheets e vice-versa. O toggle apenas troca qual banco está “ativo” naquele momento.

Se quiser, na próxima etapa podemos revisar mensagens de erro específicas ou ajustar o schema (colunas/índices) no Supabase.
