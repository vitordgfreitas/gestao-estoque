# Correção Rápida - Erro no Render

## Problema
```
bash: cd: No such file or directory
```

## Solução Rápida

### No painel do Render:

1. **Vá em Settings do seu serviço `crm-backend`**

2. **Configure Root Directory:**
   - Encontre o campo **"Root Directory"**
   - Digite: `backend`
   - Isso faz o Render executar os comandos dentro da pasta `backend`

3. **Atualize Build Command:**
   - Remova: `bash cd backend && pip install -r requirements.txt`
   - Use apenas: `pip install -r requirements.txt`

4. **Atualize Start Command:**
   - Remova: `cd backend && uvicorn main:app...`
   - Use apenas: `uvicorn main:app --host 0.0.0.0 --port $PORT`

5. **Salve as alterações**

6. **Faça um novo deploy** (Manual Deploy ou push novo commit)

## Configuração Correta Final

```
Root Directory: backend
Build Command: pip install -r requirements.txt
Start Command: uvicorn main:app --host 0.0.0.0 --port $PORT
```

## Variáveis de Ambiente Necessárias

No painel do Render, vá em **Environment** e adicione:

```
# Autenticação (OBRIGATÓRIO)
APP_USUARIO = seu_usuario_aqui
APP_SENHA = sua_senha_aqui

# Google Sheets (opcional - se não usar, será SQLite)
USE_GOOGLE_SHEETS = true
GOOGLE_SHEET_ID = seu_id_aqui
GOOGLE_CREDENTIALS = {"type":"service_account",...}  # JSON completo em uma linha
```

**⚠️ IMPORTANTE:**
- `APP_USUARIO` e `APP_SENHA` são **obrigatórias** para o login funcionar
- O `GOOGLE_CREDENTIALS` deve ser o JSON completo em uma única linha. Se tiver quebras de linha, remova-as ou use um minificador JSON online.
- Veja `RENDER_ENV_FIX.md` para instruções detalhadas sobre como corrigir problemas com variáveis de ambiente.

## Verificação

Após o deploy, verifique:
- ✅ Build deve completar sem erros
- ✅ Serviço deve ficar "Live"
- ✅ Acesse `https://seu-backend.onrender.com` e deve ver a mensagem da API
- ✅ Acesse `https://seu-backend.onrender.com/docs` para ver a documentação Swagger

## Se ainda der erro

1. Verifique se o repositório GitHub tem a pasta `backend/`
2. Verifique se `backend/requirements.txt` existe
3. Verifique se `backend/main.py` existe
4. Veja os logs completos no Render para mais detalhes

---

# Correção Frontend - Erro no Render

## Problema
```
bash: cd: No such file or directory
```

## Solução Rápida para Frontend

### No painel do Render:

1. **Vá em Settings do seu serviço `crm-frontend`**

2. **Configure Root Directory:**
   - Encontre o campo **"Root Directory"**
   - Digite: `frontend`
   - Isso faz o Render executar os comandos dentro da pasta `frontend`

3. **Atualize Build Command:**
   - Remova: `bash cd frontend && npm install && npm run build`
   - Use apenas: `npm install && npm run build`

4. **Configure Publish Directory:**
   - ⚠️ **MUITO IMPORTANTE:** Deve ser apenas: `dist`
   - **NÃO** use `frontend/dist` (isso causa erro!)
   - Se Root Directory = `frontend`, então Publish Directory = `dist`

5. **Salve as alterações**

6. **Faça um novo deploy**

## Configuração Correta Final (Frontend)

```
Root Directory: frontend
Build Command: npm install && npm run build
Publish Directory: dist
```

## Variáveis de Ambiente Necessárias (Frontend)

No painel do Render, vá em **Environment** e adicione:

```
VITE_API_URL = https://crm-backend-ghly.onrender.com
```

**⚠️ IMPORTANTE:** Substitua `crm-backend-ghly.onrender.com` pela URL real do seu backend!

## Verificação

Após o deploy:
- ✅ Build deve completar sem erros
- ✅ Site deve ficar "Live"
- ✅ Acesse a URL do frontend e deve carregar a aplicação
- ✅ Verifique se está conectando ao backend (veja o console do navegador)
