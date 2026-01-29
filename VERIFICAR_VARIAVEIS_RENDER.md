# 🔍 Como Verificar se as Variáveis de Ambiente Estão Funcionando no Render

## Problema: "ta ignorando o en"

Se você configurou `APP_USUARIO` e `APP_SENHA` no Render mas ainda aparece `⚠️ Usando credenciais padrão`, siga estes passos:

## ✅ Passo 1: Verificar se as Variáveis Estão Configuradas

1. Acesse seu serviço backend no Render
2. Vá em **Settings** → **Environment**
3. Procure por `APP_USUARIO` e `APP_SENHA` na lista
4. **Se não existirem**, adicione:
   - Clique em **"Add Environment Variable"**
   - **Key**: `APP_USUARIO`
   - **Value**: seu usuário (exemplo: `admin`)
   - Clique em **Save Changes**
   - Repita para `APP_SENHA` com sua senha (exemplo: `senha_segura_123`)

## ✅ Passo 2: Verificar os Nomes das Variáveis

**⚠️ IMPORTANTE:** Os nomes devem ser **EXATAMENTE**:
- `APP_USUARIO` (tudo maiúsculo, com underscore)
- `APP_SENHA` (tudo maiúsculo, com underscore)

**NÃO use:**
- ❌ `app_usuario` (minúsculo)
- ❌ `APP-USUARIO` (hífen)
- ❌ `App_Usuario` (misturado)

## ✅ Passo 3: Reiniciar o Serviço

Após adicionar/editar as variáveis:

1. Vá em **Manual Deploy** → **Deploy latest commit**
2. Ou faça um novo commit/push no GitHub
3. Aguarde o deploy completar

## ✅ Passo 4: Verificar os Logs

Após o deploy, veja os logs do Render. Você deve ver:

```
🔍 DEBUG - Variáveis de Ambiente
============================================================
   APP_USUARIO (raw): 'seu_usuario'
   APP_SENHA definido: sim
============================================================

🔐 CONFIGURAÇÃO DE AUTENTICAÇÃO
============================================================
APP_USUARIO (os.getenv): 'seu_usuario'
APP_SENHA (os.getenv): DEFINIDA
Usuário final usado: 'seu_usuario'
Senha final usada: DEFINIDA
✅ Usando credenciais do ambiente (Render ou .env)
============================================================
```

**Se você ver:**
```
APP_USUARIO (raw): None
APP_SENHA definido: não
⚠️ ATENÇÃO: Nenhuma credencial definida no ambiente!
```

Isso significa que as variáveis **NÃO estão configuradas** no Render.

## 🐛 Troubleshooting

### Problema: Variáveis não aparecem nos logs

**Solução:**
1. Verifique se você está olhando os logs do serviço correto (backend, não frontend)
2. Verifique se o deploy foi concluído (deve aparecer "Your service is live 🎉")
3. Faça um novo deploy manual para garantir

### Problema: Variáveis aparecem como None mesmo configuradas

**Solução:**
1. Verifique se os nomes estão corretos (maiúsculas, underscore)
2. Verifique se não há espaços extras: `APP_USUARIO ` (com espaço no final)
3. Tente deletar e recriar as variáveis
4. Reinicie o serviço após salvar

### Problema: GOOGLE_CREDENTIALS com erro de JSON

Se você também está usando Google Sheets e vê:
```
json.decoder.JSONDecodeError: Extra data: line 1 column 3 (char 2)
```

**Solução:**
1. O JSON deve estar em **uma única linha**
2. Use um minificador: https://www.freeformatter.com/json-formatter.html
3. Cole o JSON minificado no Render
4. Veja `RENDER_ENV_FIX.md` para mais detalhes

## 📝 Checklist Final

Antes de reportar problema, verifique:

- [ ] Variáveis `APP_USUARIO` e `APP_SENHA` existem no Render → Settings → Environment
- [ ] Nomes estão corretos (maiúsculas, underscore)
- [ ] Valores estão corretos (sem espaços extras)
- [ ] Serviço foi reiniciado após adicionar/editar variáveis
- [ ] Logs mostram as variáveis sendo lidas corretamente
- [ ] Código foi atualizado no GitHub (commit + push)

## 🆘 Se Nada Funcionar

1. Tente deletar TODAS as variáveis de ambiente relacionadas
2. Adicione novamente uma por uma
3. Salve e reinicie
4. Verifique os logs novamente

Se ainda não funcionar, verifique se há algum problema com o código fazendo commit e push das alterações mais recentes.
