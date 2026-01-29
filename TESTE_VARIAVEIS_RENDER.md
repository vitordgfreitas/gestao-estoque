# 🧪 Teste Rápido - Variáveis de Ambiente no Render

## Passo 1: Verificar o que está sendo lido

Após fazer deploy, acesse:
```
https://seu-backend.onrender.com/api/info
```

Você deve ver algo como:
```json
{
  "database": "SQLite",
  "use_google_sheets": false,
  "env_vars": {
    "APP_USUARIO": null,
    "APP_SENHA": null,
    "USE_GOOGLE_SHEETS": null,
    "GOOGLE_SHEET_ID": null,
    "RENDER": "true",
    "PORT": "10000"
  },
  "credentials_configured": {
    "usuario": "seu_usuario",
    "senha_defined": false
  }
}
```

## Passo 2: Se APP_USUARIO está null

Isso significa que a variável **NÃO está configurada** no Render.

### Solução:

1. **Render Dashboard** → Seu serviço backend → **Settings** → **Environment**
2. Clique em **"Add Environment Variable"**
3. **Key**: `APP_USUARIO` (EXATAMENTE assim, maiúsculas)
4. **Value**: seu usuário (exemplo: `admin`)
5. Clique em **Save Changes**
6. Repita para `APP_SENHA` com sua senha (exemplo: `senha_segura_123`)
7. **IMPORTANTE**: Faça um novo deploy (Manual Deploy ou push)

## Passo 3: Verificar novamente

Após o deploy, acesse `/api/info` novamente. Agora deve mostrar:
```json
{
  "env_vars": {
    "APP_USUARIO": "seu_usuario",
    "APP_SENHA": "***",
    ...
  },
  "credentials_configured": {
    "usuario": "seu_usuario",
    "senha_defined": true
  }
}
```

## ⚠️ Problemas Comuns

### Problema: Variável existe mas aparece null

**Causa**: Nome com espaços ou maiúsculas/minúsculas erradas

**Solução**: 
- Delete a variável
- Crie novamente com nome EXATO: `APP_USUARIO` e `APP_SENHA`
- Sem espaços antes ou depois

### Problema: Variável existe mas não funciona

**Causa**: Serviço não foi reiniciado após adicionar variável

**Solução**: 
- Faça um **Manual Deploy** após adicionar/editar variáveis
- Ou faça um commit/push no GitHub

### Problema: RENDER está null

**Causa**: Não está rodando no Render (teste local)

**Solução**: Isso é normal em desenvolvimento local. Use arquivo `.env` local.

## ✅ Checklist Final

- [ ] Acessei `/api/info` e vi o JSON
- [ ] Verifiquei que `env_vars.APP_USUARIO` não é null
- [ ] Verifiquei que `env_vars.APP_SENHA` não é null  
- [ ] Fiz deploy após adicionar variáveis
- [ ] Testei login com as credenciais configuradas
