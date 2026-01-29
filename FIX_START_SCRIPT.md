# 🔧 Corrigir Erro "Missing script: start"

## Problema

O Render está dando erro:
```
npm error Missing script: "start"
```

## ✅ Solução

O `package.json` já tem o script `start`, mas o Render pode estar usando uma versão antiga.

### Passo 1: Verificar se os arquivos estão commitados

Certifique-se de que fez commit e push:

```bash
git add frontend/package.json frontend/server.js
git commit -m "Add server.js e script start"
git push
```

### Passo 2: Verificar configuração no Render

No Render, vá no serviço **frontend**:

1. **Settings** → Verifique:
   - **Root Directory**: `frontend`
   - **Build Command**: `npm install && npm run build`
   - **Start Command**: `npm start` (deve ser exatamente isso)

2. Se o Start Command estiver diferente, edite para: `npm start`

### Passo 3: Fazer novo deploy

1. Vá em **Manual Deploy** → **Deploy latest commit**
2. Ou faça um novo commit/push

### Passo 4: Verificar logs

Após o deploy, veja os logs. Deve aparecer:

```
==> Running 'npm start'
Servidor rodando na porta 10000
```

## ⚠️ Se ainda não funcionar

1. Verifique se o `package.json` no GitHub tem o script `start`:
   - Acesse: `https://github.com/seu-usuario/seu-repo/blob/main/frontend/package.json`
   - Procure por `"start": "node server.js"`

2. Se não estiver lá, faça commit novamente:
   ```bash
   git add frontend/package.json
   git commit -m "Fix: adiciona script start"
   git push
   ```

3. Faça um novo deploy no Render

## ✅ Checklist

- [ ] `frontend/package.json` tem `"start": "node server.js"` nos scripts
- [ ] `frontend/server.js` existe
- [ ] `express` está nas dependencies do `package.json`
- [ ] Arquivos foram commitados e pushados
- [ ] Render está configurado com **Start Command**: `npm start`
- [ ] Novo deploy foi feito
