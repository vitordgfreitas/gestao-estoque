# Como Aumentar o Limite da API do Google Sheets

## 📊 Limites Padrão da API

A API do Google Sheets tem os seguintes limites padrão:

- **60 requisições por minuto por usuário** (leitura)
- **300 requisições por minuto por usuário** (escrita)
- **100 requisições por 100 segundos por usuário** (métodos batch)

## 🔧 Passo a Passo para Aumentar a Quota

### 1. Acessar o Google Cloud Console

1. Acesse: https://console.cloud.google.com/
2. Selecione seu projeto (ou crie um novo)
3. Certifique-se de que a **Google Sheets API** está habilitada

### 2. Verificar Quotas Atuais

1. No menu lateral, vá em **APIs e Serviços** → **Quotas**
2. No filtro, digite: `sheets`
3. Você verá todas as quotas relacionadas ao Google Sheets API

### 3. Solicitar Aumento de Quota

1. Clique na quota que deseja aumentar (ex: "Read requests per minute per user")
2. Clique em **EDIT QUOTAS** (Editar Quotas)
3. Preencha o formulário:
   - **Nome**: Seu nome
   - **Email**: Seu email
   - **Justificativa**: Explique por que precisa do aumento
     - Exemplo: "Sistema de gestão de carros que precisa fazer múltiplas leituras simultâneas. Aplicação em produção com múltiplos usuários."
   - **Nova quota solicitada**: Digite o valor desejado (ex: 300, 600, 1000)
4. Clique em **SUBMIT REQUEST** (Enviar Solicitação)

### 4. Aguardar Aprovação

- Geralmente leva **24-48 horas** para aprovação
- Você receberá um email quando a solicitação for aprovada ou negada
- Pode levar mais tempo se precisar de valores muito altos

## 💡 Alternativas e Otimizações

### 1. Usar Batch Operations

Em vez de fazer múltiplas chamadas individuais, agrupe operações:

```python
# ❌ Ruim: Múltiplas chamadas
for item in itens:
    sheet.append_row([item.id, item.nome])

# ✅ Bom: Uma única chamada batch
values = [[item.id, item.nome] for item in itens]
sheet.append_rows(values)
```

### 2. Melhorar o Cache

Você já tem cache implementado, mas pode otimizar:

```python
# Aumentar TTL do cache para reduzir chamadas
_cache_ttl = 60  # 1 minuto ao invés de 30 segundos

# Cache mais agressivo para dados que mudam pouco
# Ex: Categorias, configurações
```

### 3. Usar `batch_update` do gspread

Para múltiplas atualizações:

```python
from gspread import Client

# Em vez de múltiplos update_cell
updates = [
    {'range': 'A1', 'values': [[valor1]]},
    {'range': 'A2', 'values': [[valor2]]},
    {'range': 'A3', 'values': [[valor3]]},
]
sheet.batch_update(updates)
```

### 4. Implementar Rate Limiting no Código

Adicione um rate limiter para evitar exceder limites:

```python
import time
from collections import deque

class RateLimiter:
    def __init__(self, max_calls=50, period=60):
        self.max_calls = max_calls
        self.period = period
        self.calls = deque()
    
    def wait_if_needed(self):
        now = time.time()
        # Remove chamadas antigas
        while self.calls and self.calls[0] < now - self.period:
            self.calls.popleft()
        
        # Se atingiu o limite, espera
        if len(self.calls) >= self.max_calls:
            sleep_time = self.period - (now - self.calls[0])
            if sleep_time > 0:
                time.sleep(sleep_time)
                self.calls.popleft()
        
        self.calls.append(time.time())

# Uso:
rate_limiter = RateLimiter(max_calls=50, period=60)

def listar_itens():
    rate_limiter.wait_if_needed()
    # ... resto do código
```

## 🚀 Solução Rápida: Aumentar Retry e Delay

Você já tem retry implementado. Pode aumentar os delays:

```python
def _retry_with_backoff(func, max_retries=5, initial_delay=2.0):
    # Aumenta max_retries de 3 para 5
    # Aumenta initial_delay de 1.0 para 2.0
    # Isso dá mais tempo entre tentativas
```

## 📝 Exemplo de Justificativa para Solicitação

```
Solicito aumento da quota de leitura da Google Sheets API de 60 para 300 requisições por minuto.

Justificativa:
- Aplicação web de gestão de carros em produção
- Múltiplos usuários simultâneos acessando dados
- Sistema precisa fazer múltiplas leituras para:
  * Verificar disponibilidade de itens
  * Carregar dados de categorias dinamicamente
  * Exibir informações em tempo real
- Implementamos cache e retry, mas ainda precisamos de mais capacidade
- Aplicação está crescendo e precisamos de mais margem

Valor solicitado: 300 requisições/minuto
```

## ⚠️ Importante

- **Quotas são por projeto**, não por usuário
- Se você tem múltiplos projetos, precisa solicitar para cada um
- Quotas muito altas podem exigir plano pago do Google Workspace
- Considere usar **SQLite local** para desenvolvimento/testes

## 🔍 Verificar Uso Atual

No Google Cloud Console:
1. **APIs e Serviços** → **Dashboard**
2. Selecione **Google Sheets API**
3. Veja gráficos de uso nos últimos 30 dias

## 📞 Suporte

Se a solicitação for negada ou demorar muito:
- Entre em contato com o suporte do Google Cloud
- Considere migrar para Google Workspace Business (tem limites maiores)
- Use SQLite para desenvolvimento e Google Sheets apenas em produção
