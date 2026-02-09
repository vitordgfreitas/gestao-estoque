# Solução para Erro 500 do GitHub no Render

## Problema

O Render está tentando fazer clone do repositório GitHub e recebendo erro 500:

```
remote: Internal Server Error
fatal: unable to access 'https://github.com/vitordgfreitas/gestao-estoque.git/': The requested URL returned error: 500
```

## Causas Possíveis

1. **Problema temporário do GitHub** (mais comum)
2. **Repositório privado sem permissão** no Render
3. **Rate limiting do GitHub**
4. **Problema de conectividade** entre Render e GitHub

## Soluções

### Solução 1: Aguardar e Tentar Novamente (RECOMENDADO)

Erros 500 do GitHub são geralmente temporários:

1. **Aguarde 5-10 minutos**
2. No Render, vá em **Manual Deploy** → **Deploy latest commit**
3. Tente novamente

### Solução 2: Verificar Permissões do Repositório

Se o repositório é privado:

1. **No GitHub:**
   - Vá em **Settings** do repositório
   - **Manage access** → Verifique se o Render tem acesso

2. **No Render:**
   - Vá em **Settings** do serviço
   - **GitHub** → Verifique se está conectado corretamente
   - Se necessário, reconecte a conta GitHub

### Solução 3: Verificar Status do GitHub

1. Acesse: https://www.githubstatus.com/
2. Verifique se há incidentes reportados
3. Se houver, aguarde até resolver

### Solução 4: Fazer Deploy Manual via Git Push

Se o problema persistir, force um novo deploy:

1. **No seu computador:**
   ```bash
   git add .
   git commit -m "Trigger deploy"
   git push
   ```

2. **No Render:**
   - O deploy deve iniciar automaticamente
   - Se não iniciar, vá em **Manual Deploy** → **Deploy latest commit**

### Solução 5: Verificar Configuração do Repositório no Render

1. **No Render:**
   - Vá em **Settings** do serviço
   - **Repository** → Verifique se a URL está correta:
     - Deve ser: `https://github.com/vitordgfreitas/gestao-estoque`
   - **Branch** → Verifique se está na branch correta (geralmente `main` ou `master`)

### Solução 6: Usar SSH ao Invés de HTTPS (Avançado)

Se o problema persistir, você pode configurar SSH:

1. **No Render:**
   - Vá em **Settings** → **Repository**
   - Altere a URL para formato SSH:
     - De: `https://github.com/vitordgfreitas/gestao-estoque.git`
     - Para: `git@github.com:vitordgfreitas/gestao-estoque.git`
   - Configure chave SSH se necessário

## Verificação Rápida

### Checklist:

- [ ] GitHub Status está OK? (https://www.githubstatus.com/)
- [ ] Repositório é público ou Render tem acesso?
- [ ] URL do repositório está correta no Render?
- [ ] Branch está correta?
- [ ] Aguardou alguns minutos e tentou novamente?

## Solução Temporária: Deploy Manual

Se precisar fazer deploy urgente enquanto o GitHub está com problemas:

1. **No Render:**
   - Vá em **Settings** → **Build & Deploy**
   - **Deploy Hook** → Copie a URL do webhook
   - Use essa URL para fazer deploy manual via curl ou Postman

2. **Ou use Render CLI:**
   ```bash
   render deploy
   ```

## Prevenção Futura

1. **Configure Deploy Hooks** para deploy manual quando necessário
2. **Monitore status do GitHub** antes de deploys importantes
3. **Tenha backup** do código localmente
4. **Use branches** para testar antes de fazer deploy da main

## Quando Contatar Suporte

Contate o suporte do Render se:

- O erro persistir por mais de 1 hora
- Outros serviços no Render estão funcionando normalmente
- Você suspeita de problema específico da sua conta

## Links Úteis

- **GitHub Status**: https://www.githubstatus.com/
- **Render Status**: https://status.render.com/
- **Render Support**: https://render.com/docs/support

---

**Na maioria dos casos, aguardar 5-10 minutos e tentar novamente resolve o problema!**
