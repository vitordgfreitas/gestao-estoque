# 🚨 ERRO CORS - VERIFICAÇÃO E SOLUÇÃO URGENTE

## ❌ Erro Atual
```
Access to XMLHttpRequest at 'https://crm-backend-ghly.onrender.com/api/itens' 
from origin 'https://crm-frontend-wtcf.onrender.com' has been blocked by CORS policy
```

---

## ✅ SOLUÇÃO PASSO A PASSO

### PASSO 1: Verifique o Backend Deploy ⏱️

1. Acesse: https://dashboard.render.com/web/srv-ctvn6kqj1k6c73ekb430
2. Verifique se o último deploy contém o commit `54566e7`
3. Se não, force o deploy:
   - Clique em "Manual Deploy" → "Deploy latest commit"

### PASSO 2: Configure Variável no Frontend 🔧

**CRÍTICO: Este é o problema mais provável!**

1. Acesse: https://dashboard.render.com
2. Selecione o serviço: **crm-frontend-wtcf**
3. Vá em: **Environment**
4. Procure pela variável `VITE_API_URL`

#### Se NÃO EXISTE:
```
Clique em "Add Environment Variable"
Key: VITE_API_URL
Value: https://crm-backend-ghly.onrender.com
Clique em "Save Changes"
```

#### Se JÁ EXISTE:
```
Verifique se o valor está correto:
https://crm-backend-ghly.onrender.com
(sem barra no final)
```

5. **IMPORTANTE**: Após salvar, o Render vai fazer **redeploy automático**
6. Aguarde ~2-3 minutos

---

## 🔍 COMO TESTAR SE ESTÁ CONFIGURADO

### Teste 1: Console do Navegador (MAIS RÁPIDO)

1. Abra: https://crm-frontend-wtcf.onrender.com
2. Pressione **F12** (abre DevTools)
3. Vá na aba **Console**
4. Cole e execute:

```javascript
console.log('API URL:', import.meta.env.VITE_API_URL || 'VARIÁVEL NÃO CONFIGURADA')
```

**Resultado esperado:**
```
API URL: https://crm-backend-ghly.onrender.com
```

**Se aparecer:**
```
API URL: VARIÁVEL NÃO CONFIGURADA
```
ou
```
API URL: http://localhost:8000
```
❌ **PROBLEMA**: Frontend não tem a variável configurada!

### Teste 2: Network Tab

1. Abra: https://crm-frontend-wtcf.onrender.com
2. Pressione **F12**
3. Vá na aba **Network**
4. Faça login
5. Verifique as requisições:

**Se vê requisições para:**
- ❌ `http://localhost:8000/api/...` → Variável NÃO configurada
- ✅ `https://crm-backend-ghly.onrender.com/api/...` → Variável OK

---

## 📊 Status Atual

| Item | Status | Ação |
|------|--------|------|
| Backend CORS wildcard | ✅ Commit `54566e7` | Aguardar deploy |
| Frontend `VITE_API_URL` | ❓ Desconhecido | **VOCÊ PRECISA VERIFICAR** |
| Frontend build com variável | ❓ Depende do acima | Aguardar redeploy |

---

## 🎯 CHECKLIST DE VERIFICAÇÃO

Marque conforme completa:

- [ ] **Backend**: Verificou deploy do commit `54566e7` no Render
- [ ] **Frontend**: Adicionou variável `VITE_API_URL` no Render
- [ ] **Frontend**: Aguardou redeploy (~2-3 min)
- [ ] **Teste**: Abriu console e verificou URL da API
- [ ] **Teste**: Fez login e verificou requisições no Network tab
- [ ] **Resultado**: App funcionando sem erros de CORS

---

## 🆘 SE AINDA NÃO FUNCIONAR

### Opção 1: Force Clear do Cache (Render)

No **Frontend** (Render Dashboard):
```
Settings → Build & Deploy → Clear build cache & deploy
```

### Opção 2: Verifique Logs do Backend

No **Backend** (Render Dashboard):
```
Logs → Procure por:
[CORS] Modo produção - CORS configurado para aceitar qualquer origem
```

Se não aparecer, backend não deployou ainda.

### Opção 3: Teste Direto da API

Abra: https://crm-backend-ghly.onrender.com/docs

Se a página carregar, backend está funcionando.

---

## 📞 RESUMO: O QUE FAZER AGORA

**1️⃣ MAIS IMPORTANTE:**
```
Configure VITE_API_URL no frontend Render
Valor: https://crm-backend-ghly.onrender.com
```

**2️⃣ Aguarde:**
```
- Backend deploy: ~3-5 min
- Frontend redeploy: ~2-3 min
```

**3️⃣ Teste:**
```
Console: import.meta.env.VITE_API_URL
Deve retornar: https://crm-backend-ghly.onrender.com
```

---

**Data**: 2026-02-07  
**Prioridade**: 🔴 CRÍTICA  
**Tempo estimado**: 5-10 minutos

## 🎬 GIF Tutorial (passo a passo visual)

Infelizmente não posso criar GIFs, mas aqui está o caminho visual:

```
Render Dashboard
  └─ Seleciona serviço "crm-frontend-wtcf"
      └─ Clica em "Environment" (menu lateral)
          └─ Clica em "Add Environment Variable"
              └─ Key: VITE_API_URL
              └─ Value: https://crm-backend-ghly.onrender.com
              └─ Clica "Save Changes"
                  └─ Aguarda redeploy automático
```
