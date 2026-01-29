# 🔧 Corrigir Variáveis de Ambiente no Render

## Problema: Credenciais não funcionando

Se você está vendo:
- `⚠️ Usando credenciais padrão` mesmo tendo configurado no Render
- `json.decoder.JSONDecodeError: Extra data` no GOOGLE_CREDENTIALS

## ✅ Solução Passo a Passo

### 1. Configurar APP_USUARIO e APP_SENHA

1. Acesse seu serviço backend no Render
2. Vá em **Settings** → **Environment**
3. Procure por `APP_USUARIO` e `APP_SENHA`
4. Se não existirem, clique em **Add Environment Variable**:
   - **Key**: `APP_USUARIO`
   - **Value**: seu usuário (exemplo: `admin`)
   - Clique em **Save Changes**
   - Repita para `APP_SENHA` com sua senha (exemplo: `senha_segura_123`)

5. **Reinicie o serviço** (Render → Manual Deploy ou aguarde deploy automático)

### 2. Corrigir GOOGLE_CREDENTIALS (se estiver usando Google Sheets)

O erro `JSONDecodeError: Extra data` acontece quando o JSON tem quebras de linha.

**Solução:**

1. Abra seu arquivo `credentials.json` local
2. Copie TODO o conteúdo
3. Cole em um conversor online: https://www.freeformatter.com/json-formatter.html
4. Clique em **Minify** (compactar em uma linha)
5. Copie o resultado (deve ser uma linha só, sem quebras)
6. No Render, vá em **Settings** → **Environment**
7. Edite `GOOGLE_CREDENTIALS`
8. Cole o JSON minificado (uma linha só)
9. **Salve** e **reinicie o serviço**

**Exemplo de JSON correto (uma linha):**
```
{"type":"service_account","project_id":"meu-projeto","private_key_id":"abc123","private_key":"-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n","client_email":"...","client_id":"...","auth_uri":"...","token_uri":"...","auth_provider_x509_cert_url":"...","client_x509_cert_url":"..."}
```

**Exemplo ERRADO (com quebras):**
```
{
  "type": "service_account",
  "project_id": "meu-projeto",
  ...
}
```

### 3. Verificar se funcionou

Após reiniciar, veja os logs do Render. Você deve ver:

```
🔐 CONFIGURAÇÃO DE AUTENTICAÇÃO
============================================================
APP_USUARIO (variável de ambiente): seu_usuario
APP_SENHA (variável de ambiente): DEFINIDA
Usuário final usado: seu_usuario
✅ Usando credenciais personalizadas do ambiente
============================================================
```

Se ainda aparecer `⚠️ Usando credenciais padrão`, verifique:
- ✅ As variáveis estão salvas no Render?
- ✅ O serviço foi reiniciado após adicionar as variáveis?
- ✅ Os nomes das variáveis estão corretos? (`APP_USUARIO` e `APP_SENHA` em maiúsculas)

## 🐛 Debug Avançado

Se ainda não funcionar, adicione temporariamente nos logs:

No Render → Environment, adicione:
- **Key**: `DEBUG` → **Value**: `true`

Isso mostrará mais informações nos logs sobre quais variáveis estão sendo lidas.
