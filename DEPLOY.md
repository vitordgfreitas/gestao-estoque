# Guia de Deploy Gratuito - CRM Gestão de Estoque

Este guia mostra como fazer deploy gratuito da aplicação usando serviços gratuitos.

## Opções de Deploy Gratuito

### Opção 1: Render.com (Recomendado - Mais Fácil)

**Backend (FastAPI):**
1. Acesse [render.com](https://render.com) e crie uma conta gratuita
2. Clique em "New +" → "Web Service"
3. Conecte seu repositório GitHub
4. Configure:
   - **Name**: `crm-backend` (ou qualquer nome)
   - **Environment**: `Python 3`
   - **Root Directory**: `backend` ⚠️ **IMPORTANTE: Configure isso primeiro!**
   - **Build Command**: 
     ```bash
     pip install -r requirements.txt
     ```
     (Não precisa de `cd backend` se Root Directory estiver configurado)
   - **Start Command**: 
     ```bash
     uvicorn main:app --host 0.0.0.0 --port $PORT
     ```
     (Não precisa de `cd backend` se Root Directory estiver configurado)
5. Adicione variáveis de ambiente:
   - `USE_GOOGLE_SHEETS`: `true` ou `false`
   - `GOOGLE_SHEET_ID`: (se usar Google Sheets)
   - `GOOGLE_CREDENTIALS`: (JSON completo das credenciais em uma linha, se usar Google Sheets)
   - `PORT`: `8000` (alguns serviços definem automaticamente)
6. Clique em "Create Web Service"

**⚠️ IMPORTANTE:** Se você já criou o serviço e está dando erro:
1. Vá em **Settings** do serviço
2. Configure **Root Directory** como `backend`
3. Atualize **Build Command** para apenas: `pip install -r requirements.txt`
4. Atualize **Start Command** para apenas: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Salve e faça um novo deploy

**Frontend (React):**
1. No Render, clique em "New +" → **"Web Service"** (NÃO Static Site!)
2. Conecte o mesmo repositório
3. Configure:
   - **Name**: `crm-frontend`
   - **Environment**: `Node`
   - **Root Directory**: `frontend` ⚠️ **IMPORTANTE: Configure isso primeiro!**
   - **Build Command**: 
     ```bash
     npm install && npm run build
     ```
   - **Start Command**: 
     ```bash
     npm start
     ```
     (Isso executa `node server.js` que serve o SPA corretamente)
4. Adicione variável de ambiente:
   - `VITE_API_URL`: URL do backend (ex: `https://crm-backend-ghly.onrender.com`)
5. Clique em "Create Web Service"

**⚠️ IMPORTANTE:** Use **Web Service**, não Static Site! O servidor Node.js garante que todas as rotas retornem `index.html`, resolvendo o problema de 404 ao dar F5.

**⚠️ IMPORTANTE:** Se você já criou como Static Site e está dando 404 ao dar F5:

**Opção A - Mudar para Web Service (RECOMENDADO):**
1. Delete o Static Site atual
2. Crie um novo **Web Service**:
   - **Environment**: `Node`
   - **Root Directory**: `frontend`
   - **Build Command**: `npm install && npm run build`
   - **Start Command**: `npm start`
   - **Environment Variable**: `VITE_API_URL=https://crm-backend-ghly.onrender.com`
3. Faça deploy

**Opção B - Se quiser manter Static Site:**
Use Vercel ao invés do Render para o frontend (Vercel tem suporte nativo para SPAs).

**Limitações do Plano Gratuito:**
- Backend pode "dormir" após 15 minutos de inatividade (primeira requisição pode demorar)
- 750 horas/mês de uso (suficiente para uso pessoal)

---

### Opção 2: Railway.app

**Backend:**
1. Acesse [railway.app](https://railway.app) e crie conta
2. Clique em "New Project" → "Deploy from GitHub repo"
3. Selecione seu repositório
4. Railway detecta automaticamente Python
5. Configure:
   - **Root Directory**: `backend`
   - Adicione variáveis de ambiente (mesmas do Render)
6. Railway faz deploy automaticamente

**Frontend:**
1. Adicione outro serviço no mesmo projeto
2. Configure:
   - **Root Directory**: `frontend`
   - **Build Command**: `npm install && npm run build`
   - **Start Command**: `npm run preview` (ou use nginx)
   - Adicione `VITE_API_URL` com URL do backend

**Limitações:**
- $5 crédito grátis/mês (suficiente para uso leve)
- Pode precisar adicionar cartão (mas não cobra se não exceder crédito)

---

### Opção 3: Vercel (Frontend) + Render (Backend)

**Backend no Render:**
- Siga instruções da Opção 1 para backend

**Frontend no Vercel:**
1. Acesse [vercel.com](https://vercel.com) e crie conta
2. Importe seu repositório GitHub
3. Configure:
   - **Framework Preset**: Vite
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
   - **Environment Variables**: `VITE_API_URL` = URL do backend Render
4. Clique em "Deploy"

**Vantagens:**
- Vercel tem excelente performance para frontend
- Deploy automático a cada push no GitHub
- CDN global gratuito

---

### Opção 4: Fly.io (Ambos)

**Backend:**
1. Instale Fly CLI: `curl -L https://fly.io/install.sh | sh`
2. No diretório `backend`, crie `Dockerfile`:
   ```dockerfile
   FROM python:3.11-slim
   WORKDIR /app
   COPY requirements.txt .
   RUN pip install -r requirements.txt
   COPY . .
   CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
   ```
3. Execute:
   ```bash
   fly launch
   fly secrets set USE_GOOGLE_SHEETS=true
   fly secrets set GOOGLE_SHEET_ID=seu_id
   fly deploy
   ```

**Frontend:**
1. No diretório `frontend`, crie `Dockerfile`:
   ```dockerfile
   FROM node:18-alpine AS builder
   WORKDIR /app
   COPY package*.json ./
   RUN npm install
   COPY . .
   RUN npm run build

   FROM nginx:alpine
   COPY --from=builder /app/dist /usr/share/nginx/html
   COPY nginx.conf /etc/nginx/conf.d/default.conf
   EXPOSE 80
   CMD ["nginx", "-g", "daemon off;"]
   ```
2. Execute `fly launch` e `fly deploy`

**Limitações:**
- 3 VMs compartilhadas grátis
- 160GB de transferência/mês

---

## Configuração de Variáveis de Ambiente

### Backend (.env ou no painel do serviço):

**⚠️ IMPORTANTE:** No Render, configure as variáveis no painel **Settings → Environment**, não em arquivo `.env`!

```env
# Autenticação (OBRIGATÓRIO para produção)
APP_USUARIO=seu_usuario_aqui
APP_SENHA=sua_senha_aqui

# Google Sheets (opcional - se não usar, será SQLite)
USE_GOOGLE_SHEETS=true
GOOGLE_SHEET_ID=seu_id_aqui
GOOGLE_CREDENTIALS={"type":"service_account",...}  # JSON completo em uma linha SEM quebras

# Porta (geralmente definida automaticamente pelo Render)
PORT=8000
```

**Como configurar no Render:**
1. Vá no seu serviço backend no Render
2. Clique em **Settings** → **Environment**
3. Clique em **Add Environment Variable**
4. Adicione cada variável:
   - **Key**: `APP_USUARIO` → **Value**: `` (ou seu usuário)
   - **Key**: `APP_SENHA` → **Value**: `` (ou sua senha)
   - **Key**: `USE_GOOGLE_SHEETS` → **Value**: `true` ou `false`
   - **Key**: `GOOGLE_SHEET_ID` → **Value**: seu ID da planilha
   - **Key**: `GOOGLE_CREDENTIALS` → **Value**: JSON completo em uma linha (sem quebras!)

**⚠️ Sobre GOOGLE_CREDENTIALS:**
- O JSON deve estar em **uma única linha**, sem quebras
- Remova todas as quebras de linha (`\n`) do JSON
- Exemplo correto: `{"type":"service_account","project_id":"...","private_key":"..."}`
- Exemplo ERRADO: `{\n  "type": "service_account",\n  ...\n}`

### Frontend (variáveis de ambiente):
```env
VITE_API_URL=https://seu-backend.onrender.com
```

**Importante:** No Vite, variáveis devem começar com `VITE_` para serem expostas ao frontend.

---

## Preparação do Código para Deploy

### 1. Criar arquivo `.env.example`:
```env
# Backend
USE_GOOGLE_SHEETS=true
GOOGLE_SHEET_ID=
GOOGLE_CREDENTIALS=

# Frontend
VITE_API_URL=http://localhost:8000
```

### 2. Atualizar `frontend/vite.config.js`:
```javascript
export default {
  // ... outras configs
  server: {
    port: 5173,
    host: true
  }
}
```

### 3. Criar `backend/Procfile` (para alguns serviços):
```
web: uvicorn main:app --host 0.0.0.0 --port $PORT
```

### 4. Criar `backend/runtime.txt` (RECOMENDADO para evitar problemas):
```
python-3.11.0
```
**Por quê?** Python 3.13 pode ter problemas de compatibilidade com SQLAlchemy 2.0.23 e outras dependências. Python 3.11 é mais estável e tem melhor suporte.

**⚠️ IMPORTANTE:** Se o `runtime.txt` não funcionar, configure manualmente no Render:
- Vá em **Settings** → **Python Version**
- Selecione **Python 3.11** (não 3.13!)

---

## Deploy com GitHub Actions (Automático)

Crie `.github/workflows/deploy.yml`:

```yaml
name: Deploy

on:
  push:
    branches: [ main ]

jobs:
  deploy-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Deploy to Render
        run: |
          curl -X POST https://api.render.com/deploy/srv/${{ secrets.RENDER_SERVICE_ID }}?key=${{ secrets.RENDER_API_KEY }}
```

---

## Recomendação Final

**Para começar rápido:** Use **Render.com** para ambos (backend e frontend)
- Mais fácil de configurar
- Interface amigável
- Deploy automático do GitHub
- Plano gratuito generoso

**Para melhor performance:** Use **Vercel (frontend) + Render (backend)**
- Vercel tem excelente CDN
- Render é confiável para backend

---

## Troubleshooting

### Backend não conecta ao Google Sheets:
- Verifique se `GOOGLE_CREDENTIALS` está como JSON em uma linha
- Verifique se a planilha foi compartilhada com o email da conta de serviço

### Frontend não encontra backend:
- Verifique se `VITE_API_URL` está correto
- Verifique CORS no backend (já configurado para localhost, adicione URL de produção)

### Backend "dorme" no Render:
- Isso é normal no plano gratuito
- Primeira requisição após inatividade pode demorar ~30 segundos
- Considere usar Railway ou Fly.io se isso for problema

---

## Deploy Automático

### ✅ Sim! O Render faz deploy automático!

Quando você conecta um repositório GitHub ao Render:

1. **Auto-Deploy está ativado por padrão**
   - Qualquer push para a branch configurada (geralmente `main` ou `master`)
   - O Render detecta automaticamente
   - Inicia um novo build e deploy

2. **Como funciona:**
   - Você faz `git push` para o GitHub
   - Render detecta a mudança
   - Executa o Build Command
   - Faz deploy da nova versão
   - Serviço fica atualizado automaticamente

3. **Verificar configuração:**
   - Vá em **Settings** do seu serviço
   - Seção **"Auto-Deploy"**
   - Deve estar marcado como **"Yes"**
   - Branch configurada (geralmente `main`)

4. **Desativar auto-deploy (opcional):**
   - Se quiser fazer deploy manual apenas
   - Desmarque **"Auto-Deploy"** em Settings
   - Use **"Manual Deploy"** quando quiser

### ⚠️ Importante:

- **Backend:** Pode levar 2-5 minutos para fazer build e deploy
- **Frontend:** Geralmente mais rápido, 1-3 minutos
- **Durante o deploy:** O serviço pode ficar temporariamente indisponível
- **Notificações:** Você pode configurar email/Slack para receber notificações de deploy

### 🔄 Workflow Recomendado:

1. Faça suas alterações localmente
2. Teste localmente (`npm run dev` / `python run.py`)
3. Commit: `git add .` e `git commit -m "sua mensagem"`
4. Push: `git push origin main`
5. Render detecta e faz deploy automaticamente
6. Aguarde alguns minutos
7. Verifique se está funcionando na URL do Render

**Próximos Passos:**

1. Escolha uma opção de deploy
2. Configure variáveis de ambiente
3. Faça deploy do backend primeiro
4. Anote a URL do backend
5. Configure `VITE_API_URL` no frontend
6. Faça deploy do frontend
7. Configure domínio customizado (opcional - veja abaixo)
8. Teste a aplicação!
9. **A partir de agora, qualquer push no GitHub atualiza automaticamente! 🚀**

---

## Configurar Domínio Customizado no Render

### Como mudar o domínio do seu app:

**Opção 1: Personalizar nome do serviço (Gratuito)**
- Vá em **Settings** → **Name**
- Mude para algo mais amigável
- Nova URL: `seu-nome.onrender.com`

**Opção 2: Domínio customizado (Recomendado para produção)**

1. **No Render:**
   - Vá em **Settings** do serviço
   - Seção **"Custom Domains"**
   - Clique em **"Add Custom Domain"**
   - Digite seu domínio (ex: `api.seudominio.com`)

2. **Configure DNS:**
   - Adicione registro CNAME no seu provedor DNS:
     ```
     Tipo: CNAME
     Nome: api (ou app)
     Valor: crm-backend-ghly.onrender.com
     ```

3. **Aguarde propagação:**
   - DNS pode levar até 48 horas
   - Render verificará automaticamente
   - SSL será configurado automaticamente

4. **Atualize frontend:**
   - Se mudar domínio do backend, atualize `VITE_API_URL`
   - Use o novo domínio: `https://api.seudominio.com`

**Veja `DOMINIO_CUSTOMIZADO.md` para guia completo!**
