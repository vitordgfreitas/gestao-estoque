# 🔧 Corrigir CORS em Produção

## Problema: Erro de CORS bloqueando requisições

Se você está vendo:
```
Access to XMLHttpRequest at 'https://crm-backend.onrender.com/api/auth/login' 
from origin 'https://crm-frontend-nbrm.onrender.com' has been blocked by CORS policy
```

## ✅ Solução Passo a Passo

### 1. Verificar URL do Backend

O erro mostra que está tentando acessar `https://crm-backend.onrender.com`, mas verifique qual é a URL **real** do seu backend no Render.

**Como verificar:**
1. Acesse: https://dashboard.render.com
2. Vá no seu serviço **backend**
3. Veja a URL em "Available at your primary URL"
4. Deve ser algo como: `https://crm-backend-ghly.onrender.com`

### 2. Configurar VITE_API_URL no Frontend

No Render, vá no serviço **frontend**:

1. **Settings** → **Environment**
2. Procure por `VITE_API_URL`
3. Se não existir, clique em **Add Environment Variable**:
   - **Key**: `VITE_API_URL`
   - **Value**: `https://crm-backend-ghly.onrender.com` (use a URL REAL do seu backend)
4. **Salve** e faça um novo deploy do frontend

### 3. Verificar CORS no Backend

O backend já está configurado para permitir `https://crm-frontend-nbrm.onrender.com`, mas verifique:

1. No Render, vá no serviço **backend**
2. Veja os logs ao iniciar
3. Deve aparecer: `[CORS] Origens permitidas em produção: ['https://crm-frontend-nbrm.onrender.com', ...]`

### 4. Fazer Deploy

Após configurar `VITE_API_URL`:

1. **Frontend**: Faça um novo deploy (Manual Deploy ou push)
2. **Backend**: Se você fez alterações no código, faça deploy também

### 5. Testar

Após os deploys:

1. Acesse o frontend: `https://crm-frontend-nbrm.onrender.com`
2. Abra o console do navegador (F12)
3. Tente fazer login
4. Verifique se não há mais erros de CORS

## ⚠️ Checklist

- [ ] URL do backend verificada no Render
- [ ] `VITE_API_URL` configurada no frontend (Render → Environment)
- [ ] Valor de `VITE_API_URL` está correto (URL completa do backend)
- [ ] Frontend foi redeployado após configurar `VITE_API_URL`
- [ ] Backend foi redeployado (se fez alterações)
- [ ] Testou o login e não há mais erros de CORS

## 🐛 Se Ainda Não Funcionar

1. **Verifique os logs do backend** - deve mostrar as origens permitidas
2. **Verifique o console do navegador** - veja qual URL está sendo usada
3. **Teste a API diretamente**:
   ```
   curl https://crm-backend-ghly.onrender.com/api/info
   ```
   Deve retornar JSON sem erro

4. **Verifique se o backend está respondendo**:
   Acesse: `https://crm-backend-ghly.onrender.com/docs`
   Deve abrir a documentação Swagger
