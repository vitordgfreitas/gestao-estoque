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
   - **Build Command**: 
     ```bash
     cd backend && pip install -r requirements.txt
     ```
   - **Start Command**: 
     ```bash
     cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT
     ```
   - **Root Directory**: `backend`
5. Adicione variáveis de ambiente:
   - `USE_GOOGLE_SHEETS`: `true` ou `false`
   - `GOOGLE_SHEET_ID`: (se usar Google Sheets)
   - `GOOGLE_CREDENTIALS`: (JSON completo das credenciais, se usar Google Sheets)
6. Clique em "Create Web Service"

**Frontend (React):**
1. No Render, clique em "New +" → "Static Site"
2. Conecte o mesmo repositório
3. Configure:
   - **Name**: `crm-frontend`
   - **Build Command**: 
     ```bash
     cd frontend && npm install && npm run build
     ```
   - **Publish Directory**: `frontend/dist`
4. Adicione variável de ambiente:
   - `VITE_API_URL`: URL do backend (ex: `https://crm-backend.onrender.com`)
5. Clique em "Create Static Site"

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
```env
USE_GOOGLE_SHEETS=true
GOOGLE_SHEET_ID=seu_id_aqui
GOOGLE_CREDENTIALS={"type":"service_account",...}  # JSON completo em uma linha
PORT=8000  # Alguns serviços definem automaticamente
```

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

### 4. Criar `backend/runtime.txt` (se necessário):
```
python-3.11.0
```

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

## Próximos Passos

1. Escolha uma opção de deploy
2. Configure variáveis de ambiente
3. Faça deploy do backend primeiro
4. Anote a URL do backend
5. Configure `VITE_API_URL` no frontend
6. Faça deploy do frontend
7. Teste a aplicação!

**Boa sorte com o deploy! 🚀**
