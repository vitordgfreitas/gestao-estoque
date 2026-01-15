# Configuração do Google Sheets

Este guia explica como configurar o Google Sheets como banco de dados do sistema.

## Passo 1: Criar um Projeto no Google Cloud Console

1. Acesse [Google Cloud Console](https://console.cloud.google.com/)
2. Crie um novo projeto ou selecione um existente
3. Ative a **Google Sheets API** e **Google Drive API**:
   - Vá em "APIs & Services" > "Library"
   - Procure por "Google Sheets API" e ative
   - Procure por "Google Drive API" e ative

## Passo 2: Criar Credenciais de Conta de Serviço

1. Vá em "APIs & Services" > "Credentials"
2. Clique em "Create Credentials" > "Service Account"
3. Preencha:
   - **Name**: `gestao-estoque` (ou qualquer nome)
   - **Service account ID**: será gerado automaticamente
   - Clique em "Create and Continue"
4. Em "Grant this service account access to project":
   - Role: `Editor` (ou mais específico se preferir)
   - Clique em "Continue" e depois "Done"

## Passo 3: Gerar Chave JSON

1. Na lista de Service Accounts, clique na conta que você criou
2. Vá na aba "Keys"
3. Clique em "Add Key" > "Create new key"
4. Selecione **JSON** e clique em "Create"
5. Um arquivo JSON será baixado - **GUARDE ESTE ARQUIVO COM SEGURANÇA!**

## Passo 4: Compartilhar Planilha com a Conta de Serviço

1. Crie uma nova planilha no Google Sheets (ou use uma existente)
2. Clique em "Compartilhar" (Share)
3. Adicione o **email da conta de serviço** (encontrado no JSON baixado, campo `client_email`)
4. Dê permissão de **Editor**
5. Copie o **ID da planilha** da URL:
   ```
   https://docs.google.com/spreadsheets/d/SEU_ID_AQUI/edit
   ```

## Passo 5: Configurar no Sistema

Você tem 3 opções para configurar:

### Opção 1: Arquivo de Credenciais (Recomendado para desenvolvimento)

1. Renomeie o arquivo JSON baixado para `credentials.json`
2. Coloque na raiz do projeto (mesma pasta do `app.py`)
3. Adicione `credentials.json` ao `.gitignore` (já está incluído)

### Opção 2: Variável de Ambiente (Recomendado para produção)

1. Configure a variável de ambiente `GOOGLE_CREDENTIALS` com o conteúdo do JSON:
   ```bash
   # Windows PowerShell
   $env:GOOGLE_CREDENTIALS = Get-Content credentials.json -Raw
   
   # Linux/Mac
   export GOOGLE_CREDENTIALS=$(cat credentials.json)
   ```

### Opção 3: Caminho Personalizado

1. Coloque o arquivo JSON em qualquer local
2. Configure a variável de ambiente `GOOGLE_CREDENTIALS_PATH`:
   ```bash
   # Windows PowerShell
   $env:GOOGLE_CREDENTIALS_PATH = "C:\caminho\para\credentials.json"
   
   # Linux/Mac
   export GOOGLE_CREDENTIALS_PATH="/caminho/para/credentials.json"
   ```

## Passo 6: Configurar ID da Planilha (Opcional)

Se você já tem uma planilha criada e quer usar ela:

```bash
# Windows PowerShell
$env:GOOGLE_SHEET_ID = "seu_id_da_planilha_aqui"

# Linux/Mac
export GOOGLE_SHEET_ID="seu_id_da_planilha_aqui"
```

Se não configurar, o sistema criará uma nova planilha chamada "Gestão de Estoque".

## Passo 7: Ativar Google Sheets

Por padrão, o sistema usa Google Sheets. Para usar SQLite local, configure:

```bash
# Windows PowerShell
$env:USE_GOOGLE_SHEETS = "false"

# Linux/Mac
export USE_GOOGLE_SHEETS="false"
```

## Estrutura da Planilha

O sistema criará automaticamente duas abas:

1. **Itens**: Colunas - ID, Nome, Quantidade Total
2. **Compromissos**: Colunas - ID, Item ID, Quantidade, Data Início, Data Fim, Descrição

## Verificação

Após configurar, execute:

```bash
make api
# ou
run.bat
```

Se tudo estiver correto, você verá no menu lateral:
```
✅ Conectado ao Google Sheets
[Ver Planilha]
```

## Troubleshooting

### Erro: "FileNotFoundError: credentials.json"

- Verifique se o arquivo existe no caminho correto
- Ou configure a variável de ambiente `GOOGLE_CREDENTIALS`

### Erro: "Permission denied"

- Verifique se compartilhou a planilha com o email da conta de serviço
- Verifique se a conta de serviço tem permissão de Editor

### Erro: "API not enabled"

- Verifique se ativou Google Sheets API e Google Drive API no Google Cloud Console

### Dados não aparecem

- Verifique se está usando a planilha correta (ID correto)
- Verifique se as APIs estão ativadas
- Verifique os logs no terminal para mais detalhes

## Segurança

⚠️ **IMPORTANTE**: 
- Nunca compartilhe o arquivo `credentials.json` publicamente
- Não faça commit do arquivo no Git (já está no .gitignore)
- Use variáveis de ambiente em produção
- Revogue as credenciais se comprometidas
