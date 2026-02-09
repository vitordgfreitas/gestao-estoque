# Debug: Verificar Disponibilidade não funciona

## Verificações

### 1. Frontend está rodando?

No terminal, dentro da pasta `frontend`:
```bash
npm run dev
```

Deve mostrar algo como:
```
VITE v4.x.x  ready in xxx ms

  ➜  Local:   http://localhost:5173/
```

### 2. Backend está rodando?

No terminal, dentro da pasta `backend`:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Deve mostrar:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 3. Verificar no navegador

1. Abra o navegador
2. Pressione `F12` para abrir DevTools
3. Vá em "Console"
4. Acesse a página "Verificar Disponibilidade"
5. Clique no botão "Verificar Disponibilidade"
6. Veja se aparece algum erro no console

### 4. Verificar erros comuns

**Erro de CORS:**
```
Access to XMLHttpRequest at 'http://localhost:8000/api/disponibilidade' 
from origin 'http://localhost:5173' has been blocked by CORS policy
```

**Solução:** Verificar se o backend tem CORS configurado em `backend/main.py`

**Erro 404:**
```
POST http://localhost:8000/api/disponibilidade 404 (Not Found)
```

**Solução:** Endpoint não existe ou backend não está rodando

**Erro 401:**
```
POST http://localhost:8000/api/disponibilidade 401 (Unauthorized)
```

**Solução:** Token expirado, faça login novamente

### 5. Testar endpoint diretamente

Abra o navegador em:
```
http://localhost:8000/docs
```

Vá até `/api/disponibilidade` e teste diretamente

### 6. Verificar se deploy está atualizado

Se estiver testando no Render:

1. Vá no painel do Render
2. Verifique se o último deploy foi bem-sucedido
3. Verifique os logs para erros
4. Force um novo deploy se necessário

## Possíveis Causas

1. **Frontend não foi buildado/atualizado**
   - Solução: `cd frontend && npm run build`

2. **Backend não tem a rota de disponibilidade**
   - Verifique se `backend/main.py` tem `@app.post("/api/disponibilidade")`

3. **Token expirado**
   - Solução: Faça logout e login novamente

4. **Dados não existem**
   - Precisa ter itens e compromissos cadastrados

## Como me ajudar a debugar

Por favor, me envie:

1. **Console do navegador (F12)**
   - Tire screenshot dos erros em vermelho

2. **Network tab**
   - Vá em Network (Rede)
   - Clique no botão
   - Tire screenshot da requisição que aparece

3. **Terminal do backend**
   - Copie os últimos logs que apareceram

4. **O que acontece exatamente?**
   - Botão não responde?
   - Carrega infinitamente?
   - Mostra erro?
   - Página em branco?
