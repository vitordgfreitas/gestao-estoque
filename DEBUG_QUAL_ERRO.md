# 🔍 DEBUG: Qual erro está aparecendo?

## ✅ CORS Resolvido
Se o teste fetch retornou dados, o CORS está funcionando!

## ❓ Qual erro aparece agora?

### Por favor, verifique no console do navegador (F12):

1. Abra o app: https://crm-frontend-wtcf.onrender.com
2. Pressione F12
3. Vá na aba **Console**
4. Vá na aba **Network**
5. Faça login e tente cadastrar um item
6. Copie TODOS os erros que aparecerem

### Possíveis erros agora que CORS foi resolvido:

#### 1. Erro 401 (Não autorizado)
```
Status: 401 Unauthorized
Problema: Token inválido ou expirado
```

#### 2. Erro 500 (Erro no servidor)
```
Status: 500 Internal Server Error
Problema: Bug no backend ao processar
```

#### 3. Erro 400 (Bad Request)
```
Status: 400 Bad Request
Problema: Validação falhou
```

#### 4. Erro de timeout
```
Status: 408 Request Timeout
Problema: Backend demorou muito (cold start)
```

### O que preciso saber:

1. **Qual é o status da requisição?** (200, 400, 401, 500?)
2. **Qual endpoint está falhando?** (/api/itens, /api/categorias, etc)
3. **Qual a mensagem de erro exata?**
4. **O erro aparece ao fazer o quê?** (login, cadastrar item, listar dados?)

---

## 🔴 Se for erro ao LISTAR dados:

Pode ser o problema de variável `VITE_API_URL` no frontend.

**Verifique no console:**
```javascript
console.log('API URL:', import.meta.env.VITE_API_URL)
```

**Deve retornar:**
```
API URL: https://crm-backend-ghly.onrender.com
```

**Se retornar `undefined` ou `localhost:8000`:**
- Frontend não tem a variável configurada
- Precisa adicionar no Render Dashboard → Frontend → Environment

---

## 🔴 Se for erro ao CADASTRAR item:

Pode ser o bug do `ERR_FAILED` que já corrigimos (commit `3df6c5c`).

**Verifique:**
1. Backend fez deploy do commit `3df6c5c`?
2. Item salva no Google Sheets mas dá erro no frontend?

---

## 🔴 Se for erro 401 (Unauthorized):

Token pode ter expirado.

**Solução rápida:**
1. Logout
2. Login novamente
3. Tente novamente

---

**Me envie os detalhes do erro que vou identificar exatamente o problema!** 🔍
