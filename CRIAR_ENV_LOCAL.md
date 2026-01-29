# 📝 Como Criar o Arquivo .env para Desenvolvimento Local

## Passo 1: Criar o arquivo .env

Na **raiz do projeto** (mesmo nível que `backend/` e `frontend/`), crie um arquivo chamado `.env` (com o ponto no início).

## Passo 2: Adicionar as variáveis

Abra o arquivo `.env` e adicione:

```env
APP_USUARIO=seu_usuario
APP_SENHA=sua_senha
```

**Exemplo:**
```env
APP_USUARIO=admin
APP_SENHA=senha123
```

## Passo 3: Verificar se foi criado

Execute no terminal (na raiz do projeto):

**PowerShell:**
```powershell
Get-Content .env
```

**CMD:**
```cmd
type .env
```

**Linux/Mac:**
```bash
cat .env
```

Você deve ver:
```
APP_USUARIO=seu_usuario
APP_SENHA=sua_senha
```

## Passo 4: Reiniciar o backend

Após criar o `.env`, **pare e reinicie o backend**:

1. Pare o servidor (Ctrl+C)
2. Inicie novamente:
   ```powershell
   cd backend
   .\venv\Scripts\Activate.ps1
   python run.py
   ```

## Passo 5: Verificar os logs

Ao iniciar o backend, você deve ver:

```
✅ Carregado .env da raiz: C:\Users\...\GestaoCarro\.env

🔐 CONFIGURAÇÃO DE AUTENTICAÇÃO
============================================================
Ambiente: DESENVOLVIMENTO
APP_USUARIO (os.getenv): 'seu_usuario'
APP_SENHA (os.getenv): DEFINIDA
Usuário final: 'seu_usuario' (len=X)
Senha final: DEFINIDA (len=X)
✅ Usando credenciais do .env (desenvolvimento)
============================================================
```

## ⚠️ Problemas Comuns

### Problema: "Arquivo .env não encontrado"

**Solução:**
- Verifique se o arquivo está na **raiz do projeto** (mesmo nível que `backend/`)
- Verifique se o nome está correto: `.env` (com ponto no início)
- No Windows, pode ser necessário criar via terminal:
  ```powershell
  New-Item -Path .env -ItemType File
  ```

### Problema: "APP_USUARIO e APP_SENHA não configuradas"

**Solução:**
- Verifique se as variáveis estão no formato correto:
  ```
  APP_USUARIO=valor
  APP_SENHA=valor
  ```
- **NÃO** use espaços ao redor do `=`
- **NÃO** use aspas (a menos que o valor tenha espaços)

### Problema: Login "roda para sempre"

**Possíveis causas:**
1. Backend não está rodando
2. Frontend não está conseguindo conectar ao backend
3. CORS bloqueando a requisição

**Solução:**
1. Verifique se o backend está rodando: http://localhost:8000
2. Abra o console do navegador (F12) e veja se há erros
3. Verifique se a URL da API está correta no frontend

## ✅ Checklist

- [ ] Arquivo `.env` criado na raiz do projeto
- [ ] Variáveis `APP_USUARIO` e `APP_SENHA` configuradas
- [ ] Backend reiniciado após criar o `.env`
- [ ] Logs mostram "✅ Carregado .env da raiz"
- [ ] Logs mostram "✅ Usando credenciais do .env"
- [ ] Login funciona no frontend
