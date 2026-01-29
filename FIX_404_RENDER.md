# 🔧 Corrigir 404 ao dar F5 no Render

## Problema

Ao dar F5 (refresh) em páginas como `/dashboard` ou `/compromissos`, aparece erro 404.

## ✅ Solução para Render Static Site

O Render Static Site não suporta configuração de redirecionamento da mesma forma que Netlify ou Vercel. Você tem duas opções:

### Opção 1: Mudar para Web Service (RECOMENDADO)

Em vez de Static Site, use um **Web Service** que serve os arquivos estáticos:

1. **Delete o Static Site atual** no Render
2. Crie um **novo Web Service**:
   - **Name**: `crm-frontend`
   - **Environment**: `Node`
   - **Root Directory**: `frontend`
   - **Build Command**: `npm install && npm run build`
   - **Start Command**: `npx serve -s dist -l 10000`
   - **Add Environment Variable**: `VITE_API_URL=https://crm-backend-ghly.onrender.com`

3. O `serve` vai servir o `index.html` para todas as rotas automaticamente

### Opção 2: Usar Vercel (MAIS FÁCIL)

Vercel tem suporte nativo para SPAs:

1. Acesse: https://vercel.com
2. Importe seu repositório GitHub
3. Configure:
   - **Framework Preset**: Vite
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
   - **Environment Variable**: `VITE_API_URL=https://crm-backend-ghly.onrender.com`
4. Deploy automático!

### Opção 3: Criar servidor Node simples

Crie um arquivo `server.js` no frontend:

```javascript
const express = require('express');
const path = require('path');
const app = express();

// Serve arquivos estáticos
app.use(express.static(path.join(__dirname, 'dist')));

// Todas as rotas retornam index.html (SPA)
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'dist', 'index.html'));
});

const port = process.env.PORT || 10000;
app.listen(port, () => {
  console.log(`Servidor rodando na porta ${port}`);
});
```

E configure no Render:
- **Start Command**: `node server.js`
- Adicione `express` ao `package.json`: `npm install express`

## ⚠️ Qual escolher?

- **Opção 1**: Funciona bem, mas precisa instalar `serve`
- **Opção 2**: Mais fácil, Vercel é otimizado para SPAs
- **Opção 3**: Mais controle, mas precisa manter código do servidor

## ✅ Recomendação

Use a **Opção 2 (Vercel)** para o frontend e mantenha o backend no Render. É a solução mais simples e funciona perfeitamente!
