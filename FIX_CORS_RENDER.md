# 🚨 CORREÇÃO URGENTE: Erro de CORS no Render

## ❌ Erro Atual

```
Access to XMLHttpRequest at 'https://crm-backend-ghly.onrender.com/api/itens' 
from origin 'https://crm-frontend-wtcf.onrender.com' has been blocked by CORS policy: 
No 'Access-Control-Allow-Origin' header is present on the requested resource.
```

## 🔍 Diagnóstico

### 1. Backend (✅ CORRIGIDO)
- CORS configurado para aceitar qualquer origem (`allow_origins=["*"]`)
- Commit: `54566e7`
- Status: **Aguardando deploy no Render**

### 2. Frontend (⚠️ VERIFICAR)
O frontend precisa ter a variável de ambiente `VITE_API_URL` configurada no Render.

## ✅ SOLUÇÃO COMPLETA

### Passo 1: Configurar Variável de Ambiente no Frontend (Render)

1. Acesse: https://dashboard.render.com
2. Selecione o serviço **crm-frontend-wtcf** (ou o frontend ativo)
3. Vá em **Environment**
4. Adicione a variável:
   ```
   VITE_API_URL=https://crm-backend-ghly.onrender.com
   ```
5. Clique em **Save Changes**

### Passo 2: Aguardar Deploys

- ✅ Backend: Aguardar deploy do commit `54566e7` (~3-5 min)
- ✅ Frontend: Aguardar redeploy após adicionar variável (~2-3 min)

### Passo 3: Testar

1. Abra o app: https://crm-frontend-wtcf.onrender.com
2. Faça login
3. Tente acessar qualquer página (Dashboard, Itens, etc.)
4. Verifique o console do navegador (F12)
5. ✅ Deve funcionar normalmente

## 🔍 Como Verificar se Está Configurado

### No Frontend (Console do Navegador - F12)

Cole no console:

```javascript
console.log('API Base URL:', import.meta.env.VITE_API_URL || 'http://localhost:8000')
```

**Resultado esperado:**
```
API Base URL: https://crm-backend-ghly.onrender.com
```

**Se retornar `http://localhost:8000`:**
- ⚠️ Variável `VITE_API_URL` NÃO está configurada no Render
- Frontend está tentando conectar no localhost (que não existe)

### No Backend (Logs do Render)

Procure por:
```
[CORS] Modo produção - CORS configurado para aceitar qualquer origem (wildcard)
```

## 📋 Checklist de Verificação

- [ ] Backend fez deploy do commit `54566e7`
- [ ] Frontend tem `VITE_API_URL` configurada
- [ ] Frontend fez redeploy após adicionar variável
- [ ] Testou login no app
- [ ] Testou acesso às páginas
- [ ] Verificou console do navegador (sem erros de CORS)

## 🔐 Após Correção: Reverter CORS (Segurança)

Quando tudo estiver funcionando, devemos reverter o CORS para aceitar apenas origens específicas:

```python
# Em backend/main.py
allow_origins = [
    "https://crm-frontend-wtcf.onrender.com",
]
allow_credentials = True
```

## 📝 Arquivos Modificados

- **backend/main.py**: CORS wildcard (linha ~154-175)
- **frontend/src/services/api.js**: Usa `VITE_API_URL` (linha 3)

## 🚀 URLs dos Serviços

- **Backend**: https://crm-backend-ghly.onrender.com
- **Frontend**: https://crm-frontend-wtcf.onrender.com
- **API Docs**: https://crm-backend-ghly.onrender.com/docs

---

**Data**: 2026-02-07  
**Status**: 🟡 Aguardando configuração de variável de ambiente  
**Prioridade**: 🔴 CRÍTICA (app não funciona sem isso)
