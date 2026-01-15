# SQLite vs Google Sheets - Guia Comparativo

## O que é SQLite?

**SQLite** é um banco de dados **local e embutido** que:
- ✅ **Não precisa de servidor separado** - funciona como um arquivo no seu computador
- ✅ **É gratuito e open-source**
- ✅ **Muito rápido** - sem limites de requisições por minuto
- ✅ **Incluído no Python** - não precisa instalar nada extra
- ✅ **Dados ficam em um arquivo** (`data/estoque.db`)

## Diferenças Principais

### Google Sheets
- 📊 Dados ficam **na nuvem** (Google Drive)
- 🌐 Acesso de qualquer lugar
- ⚠️ Limite de **60 requisições por minuto**
- ⚠️ Precisa de credenciais/configuração
- ✅ Compartilhamento fácil com outras pessoas
- ✅ Visualização direta na planilha

### SQLite
- 💾 Dados ficam **localmente** (arquivo `.db`)
- 🚀 **Sem limites** de requisições
- ✅ **Muito mais rápido** para operações
- ✅ **Mais simples** - não precisa configurar nada
- ⚠️ Dados ficam apenas no servidor onde roda
- ⚠️ Não tem visualização direta (precisa do app)

## Como o App Escolhe Qual Usar?

O app verifica a variável de ambiente `USE_GOOGLE_SHEETS`:

```python
USE_GOOGLE_SHEETS = os.getenv('USE_GOOGLE_SHEETS', 'true').lower() == 'true'
```

- Se `USE_GOOGLE_SHEETS=true` → Usa **Google Sheets**
- Se `USE_GOOGLE_SHEETS=false` → Usa **SQLite**
- Se não configurado → **Padrão é Google Sheets**

## SQLite no Streamlit Cloud Gratuito

### ✅ Funciona?
**SIM**, SQLite funciona no Streamlit Cloud gratuito!

### ⚠️ MAS há uma limitação importante:

**No plano gratuito do Streamlit Cloud:**
- Os dados **NÃO são persistentes** entre reinicializações
- Quando o app "dorme" (após inatividade) ou reinicia, **os dados são perdidos**
- O arquivo `data/estoque.db` é criado em um sistema de arquivos temporário

### 📝 Quando os dados são perdidos?
- Após ~30 minutos de inatividade (app "dorme")
- Quando você faz deploy de uma nova versão
- Quando o Streamlit reinicia o app automaticamente

## Comparação Prática

| Característica | Google Sheets | SQLite |
|----------------|---------------|--------|
| **Persistência** | ✅ Permanente | ⚠️ Temporária (gratuito) |
| **Velocidade** | ⚠️ Limitada (60 req/min) | ✅ Muito rápida |
| **Limites** | ⚠️ 60 requisições/min | ✅ Sem limites |
| **Configuração** | ⚠️ Complexa | ✅ Simples |
| **Compartilhamento** | ✅ Fácil | ❌ Não disponível |
| **Visualização** | ✅ Planilha direta | ❌ Só pelo app |
| **Custo** | ✅ Gratuito | ✅ Gratuito |

## Recomendações

### Use Google Sheets quando:
- ✅ Precisa que os dados sejam **permanentes**
- ✅ Quer **compartilhar** dados com outras pessoas
- ✅ Quer **visualizar** dados diretamente na planilha
- ✅ Precisa de **backup automático** (Google Drive)

### Use SQLite quando:
- ✅ Está **desenvolvendo/testando** localmente
- ✅ Tem problemas com **limite de quota** do Google Sheets
- ✅ Precisa de **máxima velocidade**
- ✅ Os dados podem ser **temporários** (app de demonstração)

## Como Mudar de Google Sheets para SQLite

### No Streamlit Cloud:
1. Vá em **Settings** > **Secrets**
2. Adicione ou modifique:
   ```toml
   USE_GOOGLE_SHEETS = "false"
   ```
3. Salve e aguarde o app reiniciar

### Localmente:
1. Configure variável de ambiente:
   ```bash
   # Windows PowerShell
   $env:USE_GOOGLE_SHEETS="false"
   
   # Windows CMD
   set USE_GOOGLE_SHEETS=false
   
   # Linux/Mac
   export USE_GOOGLE_SHEETS=false
   ```

2. Ou crie arquivo `.env`:
   ```
   USE_GOOGLE_SHEETS=false
   ```

## Importante sobre SQLite no Streamlit Cloud Gratuito

⚠️ **ATENÇÃO**: No plano gratuito, os dados SQLite são **temporários**!

Se você precisa de persistência de dados no Streamlit Cloud gratuito, **use Google Sheets**.

Para persistência com SQLite, você precisaria:
- Usar um serviço de banco de dados externo (PostgreSQL, MySQL, etc.)
- Ou usar volumes persistentes (não disponível no plano gratuito)

## Resumo

- **SQLite** = Banco de dados local, rápido, sem limites, mas dados temporários no Streamlit Cloud gratuito
- **Google Sheets** = Banco de dados na nuvem, permanente, mas com limite de 60 requisições/minuto
- **Ambos funcionam** no Streamlit Cloud gratuito
- **Escolha baseado** nas suas necessidades de persistência e velocidade
