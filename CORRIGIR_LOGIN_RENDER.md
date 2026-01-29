# 🔧 Corrigir Login no Render

## Problema: "Usando credenciais padrão"

Se você vê `⚠️ Usando credenciais padrão` nos logs do Render, significa que `APP_USUARIO` e `APP_SENHA` **não estão configuradas** ou **não estão sendo lidas**.

## ✅ Solução Passo a Passo

### 1. Verificar se as Variáveis Existem

1. Acesse: https://dashboard.render.com
2. Vá no seu serviço **backend** (crm-backend)
3. Clique em **Settings** → **Environment**
4. Procure por `APP_USUARIO` e `APP_SENHA` na lista

### 2. Se NÃO Existirem - Adicionar

1. Clique em **"Add Environment Variable"**
2. **Key**: `APP_USUARIO` (EXATAMENTE assim, maiúsculas)
3. **Value**: seu usuário (exemplo: `admin`)
4. Clique em **Save Changes**
5. Repita para `APP_SENHA`:
   - **Key**: `APP_SENHA`
   - **Value**: sua senha (exemplo: `senha_segura_123`)
6. Clique em **Save Changes**

### 3. Se JÁ Existirem - Verificar

1. Clique em cada variável para editar
2. Verifique:
   - ✅ Nome está correto? (`APP_USUARIO` e `APP_SENHA` - maiúsculas)
   - ✅ Não há espaços extras antes/depois do nome?
   - ✅ Valor está correto? (seus valores configurados)
   - ✅ Não há espaços extras antes/depois do valor?

### 4. IMPORTANTE: Reiniciar o Serviço

Após adicionar/editar variáveis, você **DEVE** fazer um novo deploy:

**Opção A - Manual Deploy:**
1. Vá em **Manual Deploy** → **Deploy latest commit**
2. Aguarde o deploy completar

**Opção B - Push no GitHub:**
1. Faça um commit qualquer
2. Push para o GitHub
3. O Render fará deploy automático

### 5. Verificar se Funcionou

Após o deploy, veja os logs. Você deve ver:

```
🔐 CONFIGURAÇÃO DE AUTENTICAÇÃO
============================================================
APP_USUARIO (os.getenv): 'seu_usuario'
APP_SENHA (os.getenv): DEFINIDA
Usuário final: 'seu_usuario' (len=X)
Senha final: DEFINIDA (len=X)
✅ Usando credenciais do ambiente
============================================================
```

**Se ainda aparecer:**
```
⚠️ ATENÇÃO: Usando credenciais padrão!
```

Isso significa que as variáveis **ainda não estão configuradas** ou o serviço **não foi reiniciado**.

## 🧪 Testar Login

Após configurar, teste:

1. Acesse seu frontend: `https://seu-frontend.onrender.com`
2. Vá para `/login`
3. Use as credenciais que você configurou:
   - **Usuário**: o valor de `APP_USUARIO`
   - **Senha**: o valor de `APP_SENHA`
4. Clique em "Entrar"

Se der erro, veja o console do navegador (F12) para mais detalhes.

## 🐛 Debug Avançado

Se ainda não funcionar, acesse:
```
https://seu-backend.onrender.com/api/info
```

Veja o campo `env_vars`:
```json
{
  "env_vars": {
    "APP_USUARIO": "seu_usuario",  // Deve aparecer aqui
    "APP_SENHA": "***",     // Deve aparecer "***" se definido
    ...
  }
}
```

Se `APP_USUARIO` estiver `null`, a variável não está configurada.

## ✅ Checklist Final

- [ ] Variáveis `APP_USUARIO` e `APP_SENHA` existem no Render
- [ ] Nomes estão corretos (maiúsculas, sem espaços)
- [ ] Valores estão corretos (seus valores configurados)
- [ ] Serviço foi reiniciado após adicionar/editar
- [ ] Logs mostram "✅ Usando credenciais do ambiente"
- [ ] Login funciona no frontend
