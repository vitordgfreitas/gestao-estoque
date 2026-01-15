# Guia de Deploy Gratuito

Este guia mostra como colocar o sistema no ar usando serviços gratuitos.

## 🚀 Opção 1: Streamlit Cloud (RECOMENDADO - Mais Fácil)

### Vantagens:
- ✅ Totalmente gratuito
- ✅ Deploy automático via GitHub
- ✅ Atualizações automáticas
- ✅ HTTPS incluído
- ✅ Sem limite de tempo
- ✅ Ideal para Streamlit

### Passo a Passo:

1. **Criar conta no GitHub** (se não tiver):
   - Acesse: https://github.com
   - Crie uma conta gratuita

2. **Criar repositório no GitHub**:
   - Clique em "New repository"
   - Nome: `gestao-estoque` (ou qualquer nome)
   - Marque como **Público** (necessário para plano gratuito)
   - Não marque "Initialize with README"
   - Clique em "Create repository"

3. **Enviar código para GitHub**:
   ```bash
   # No terminal, na pasta do projeto
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/SEU_USUARIO/gestao-estoque.git
   git push -u origin main
   ```

4. **Configurar Streamlit Cloud**:
   - Acesse: https://share.streamlit.io
   - Faça login com GitHub
   - Clique em "New app"
   - Selecione seu repositório
   - Branch: `main`
   - Main file path: `app.py`
   - Clique em "Deploy"

5. **Configurar Secrets**:
   - No Streamlit Cloud, vá em "Settings" > "Secrets"
   - Adicione as variáveis:
     ```toml
     # Autenticação
     APP_USUARIO = "seu_usuario"
     APP_SENHA = "sua_senha"
     
     # Google Sheets
     GOOGLE_SHEET_ID = "1OmKLrAJq4CBYzyhwQlbjCd-AbPl3YmMNPNExSBeAvlE"
     USE_GOOGLE_SHEETS = "true"
     ```
   - Para credenciais do Google, você tem 2 opções:
     
     **Opção A - Arquivo de credenciais (mais seguro)**:
     - Crie um arquivo `credentials.json` localmente
     - No Streamlit Cloud Secrets, adicione:
       ```toml
       GOOGLE_CREDENTIALS = """
       {
         "type": "service_account",
         "project_id": "...",
         "private_key_id": "...",
         "private_key": "...",
         "client_email": "...",
         ...
       }
       """
       ```
     
     **Opção B - Variável de ambiente**:
     - Cole o conteúdo completo do JSON em `GOOGLE_CREDENTIALS`

6. **Pronto!**
   - Seu app estará disponível em: `https://seu-app.streamlit.app`
   - Qualquer push no GitHub atualiza automaticamente o app

### ⚠️ Importante:
- Mantenha o repositório **público** para usar o plano gratuito
- NÃO faça commit do arquivo `credentials.json` (já está no .gitignore)
- Use Secrets para dados sensíveis

---

## 🌐 Opção 2: Render (Alternativa)

### Vantagens:
- ✅ Gratuito (com limitações)
- ✅ Suporta repositórios privados
- ⚠️ App "dorme" após 15 minutos de inatividade (acorda em alguns segundos)

### Passo a Passo:

1. **Criar conta no Render**:
   - Acesse: https://render.com
   - Faça login com GitHub

2. **Criar novo Web Service**:
   - Clique em "New +" > "Web Service"
   - Conecte seu repositório GitHub
   - Configure:
     - **Name**: gestao-estoque
     - **Environment**: Python 3
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `streamlit run app.py --server.port=$PORT --server.address=0.0.0.0`
     - **Plan**: Free

3. **Configurar Variáveis de Ambiente**:
   - Na seção "Environment Variables", adicione:
     - `GOOGLE_SHEET_ID`
     - `USE_GOOGLE_SHEETS=true`
     - `GOOGLE_CREDENTIALS` (conteúdo do JSON)

4. **Deploy**:
   - Clique em "Create Web Service"
   - Aguarde o build (pode levar alguns minutos)

---

## 🚂 Opção 3: Railway (Alternativa)

### Vantagens:
- ✅ $5 de crédito grátis por mês (suficiente para apps simples)
- ✅ Deploy rápido
- ⚠️ Requer cartão de crédito (mas não cobra se não exceder limite)

### Passo a Passo:

1. **Criar conta no Railway**:
   - Acesse: https://railway.app
   - Faça login com GitHub

2. **Criar novo projeto**:
   - Clique em "New Project"
   - Selecione "Deploy from GitHub repo"
   - Escolha seu repositório

3. **Configurar**:
   - Railway detecta automaticamente que é Python
   - Adicione variáveis de ambiente nas configurações
   - Railway cria a URL automaticamente

---

## 📋 Checklist Antes do Deploy

- [ ] Código no GitHub
- [ ] Arquivo `requirements.txt` atualizado
- [ ] `.gitignore` configurado (não commitar `credentials.json`)
- [ ] Variáveis de ambiente configuradas
- [ ] Google Sheets API configurada
- [ ] Planilha compartilhada com conta de serviço

---

## 🔒 Segurança

### O que NUNCA fazer:
- ❌ Commitar `credentials.json` no GitHub
- ❌ Expor credenciais em código
- ❌ Usar repositório privado no Streamlit Cloud (plano gratuito)

### O que fazer:
- ✅ Usar Secrets/Variáveis de Ambiente
- ✅ Manter `.gitignore` atualizado
- ✅ Revisar permissões da conta de serviço do Google

---

## 📝 Arquivo requirements.txt Atualizado

Certifique-se de que seu `requirements.txt` está completo:

```
streamlit==1.28.0
sqlalchemy==2.0.23
gspread==5.12.0
google-auth==2.23.4
google-auth-oauthlib==1.1.0
google-auth-httplib2==0.1.1
```

---

## 🆘 Troubleshooting

### App não inicia:
- Verifique se todas as dependências estão no `requirements.txt`
- Verifique logs no painel do serviço

### Erro de credenciais:
- Verifique se as variáveis de ambiente estão configuradas
- Verifique se a planilha foi compartilhada com o email da conta de serviço

### Erro de conexão:
- Verifique se o Google Sheets API está ativado
- Verifique se as credenciais estão corretas

---

## 💡 Recomendação

Para este projeto, recomendo **Streamlit Cloud** porque:
1. É feito especificamente para Streamlit
2. É totalmente gratuito
3. Deploy muito simples
4. Atualizações automáticas
5. Sem configuração complexa
