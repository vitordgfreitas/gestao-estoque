# Google Sheets API - Quotas e Limites

## 📊 Limites Atuais da API do Google Sheets

### Por Projeto (todos os usuários juntos)
- **Leitura (Read requests)**: **300 requisições/minuto**
- **Escrita (Write requests)**: **300 requisições/minuto**

### Por Usuário (dentro do projeto)
- **Leitura (Read requests)**: **60 requisições/minuto/usuário**
- **Escrita (Write requests)**: **60 requisições/minuto/usuário**

### ⚠️ O que acontece quando excede?
- Erro **HTTP 429** ("Too Many Requests" / "Quota exceeded")
- A operação falha
- Precisa aguardar alguns minutos antes de tentar novamente

## 🔧 Posso Aumentar a Quota?

### ✅ SIM, é possível solicitar aumento!

### Como Solicitar:

1. **Acesse o Google Cloud Console**
   - Vá para: https://console.cloud.google.com/
   - Selecione seu projeto

2. **Navegue até Quotas**
   - Menu lateral: **APIs & Services** → **Quotas**
   - Ou acesse diretamente: https://console.cloud.google.com/apis/api/sheets.googleapis.com/quotas

3. **Filtre por Google Sheets API**
   - No campo de busca, digite: `sheets.googleapis.com`
   - Selecione o serviço "Google Sheets API"

4. **Escolha a Quota que quer aumentar**
   - Procure por: **"Read requests per minute per user"** ou **"Write requests per minute per user"**
   - Ou: **"Read requests per minute"** (por projeto)

5. **Clique em "EDIT QUOTAS"**
   - Selecione a quota desejada
   - Clique no botão **EDIT QUOTAS**

6. **Preencha o Formulário**
   - **Nome da quota**: Selecione a que quer aumentar
   - **Nova quota**: Digite o valor desejado (ex: 120, 300, etc.)
   - **Justificativa**: Explique por que precisa do aumento
     - Exemplo: "Aplicação de gestão de estoque com múltiplos usuários simultâneos. Necessário para operações normais do negócio."

7. **Envie a Solicitação**
   - Clique em **Submit Request**
   - Aguarde a análise (geralmente 1-3 dias úteis)

### 📝 Dicas para Aprovação:

- **Seja específico**: Explique o uso real da aplicação
- **Mencione o número de usuários**: Se tiver muitos usuários simultâneos
- **Justifique o valor**: Explique por que precisa daquele valor específico
- **Histórico de uso**: Projetos com histórico de uso consistente têm mais chances

### ⚠️ Limitações:

- **Não é garantido**: A Google pode negar ou aprovar um valor menor
- **Valor máximo comum**: Geralmente até **300 requisições/minuto** por projeto
- **Valores maiores**: Podem exigir plano pago ou justificativa muito forte
- **Tempo de análise**: Pode levar alguns dias

## 💰 Custos

- ✅ **A solicitação de aumento é GRATUITA**
- ✅ **A API do Google Sheets é GRATUITA** (dentro dos limites)
- ✅ **Não há cobrança** por usar a API

## 🚀 Alternativas para Evitar Quota

### 1. Otimizar o Código (já implementado)
- ✅ Cache de dados (30 segundos)
- ✅ Lazy loading de relacionamentos
- ✅ Redução de chamadas desnecessárias

### 2. Usar Batch Requests
- Agrupar múltiplas operações em uma única requisição
- Reduz significativamente o número de chamadas

### 3. Implementar Retry com Backoff
- Se receber erro 429, aguardar alguns segundos antes de tentar novamente
- Aumentar o tempo de espera progressivamente

### 4. Usar SQLite para Desenvolvimento
- Para testes e desenvolvimento local
- Evita consumir quota desnecessariamente

## 📈 Valores Recomendados para Solicitar

### Para uso moderado:
- **120 requisições/minuto/usuário** (dobro do padrão)
- **600 requisições/minuto/projeto** (dobro do padrão)

### Para uso intenso:
- **300 requisições/minuto/usuário** (5x o padrão)
- **1000+ requisições/minuto/projeto** (se justificado)

## 🔍 Como Verificar Sua Quota Atual

1. Acesse: https://console.cloud.google.com/apis/api/sheets.googleapis.com/quotas
2. Procure por:
   - `ReadRequestsPerMinutePerUser`
   - `WriteRequestsPerMinutePerUser`
   - `ReadRequestsPerMinute`
   - `WriteRequestsPerMinute`

## 📝 Exemplo de Justificativa para Solicitação

```
Aplicação de gestão de estoque para aluguel de itens em eventos.

Justificativa:
- Sistema utilizado por equipe de 5-10 usuários simultâneos
- Operações frequentes de consulta de disponibilidade
- Necessário para operações críticas do negócio
- Implementamos cache e otimizações, mas ainda precisamos de maior capacidade

Uso estimado:
- ~100-150 requisições/minuto durante horários de pico
- Necessário aumento para 120-180 requisições/minuto/usuário
```

## ⚡ Solução Rápida Temporária

Se você está enfrentando problemas de quota agora:

1. **Aguarde 1-2 minutos** antes de tentar novamente
2. **Use SQLite temporariamente**:
   - Configure `USE_GOOGLE_SHEETS=false` no Streamlit Cloud Secrets
   - Ou localmente: `$env:USE_GOOGLE_SHEETS="false"`
3. **Reduza operações** que fazem muitas leituras
4. **Solicite aumento de quota** para resolver definitivamente

## 📚 Links Úteis

- **Documentação oficial**: https://developers.google.com/sheets/api/limits
- **Google Cloud Console**: https://console.cloud.google.com/
- **Solicitar aumento**: https://console.cloud.google.com/apis/api/sheets.googleapis.com/quotas
