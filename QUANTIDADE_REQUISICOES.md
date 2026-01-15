# Quantidade de Requisições ao Google Sheets

## 📊 Resposta Direta

### Para 200 itens no "Visualizar Dados":

**✅ Apenas 1 requisição** para buscar todos os itens!

A função `get_all_records()` do gspread faz **UMA única requisição** à API do Google Sheets e retorna **todos os registros de uma vez**.

## 🔍 Como Funciona

### `listar_itens()` - Busca Todos os Itens
```python
records = sheet_itens.get_all_records()  # ← UMA requisição para TODOS os registros
```

**Resultado**: 
- 1 requisição busca todos os 200 itens
- Os dados são processados localmente (em memória)
- Não há requisições adicionais por item

### `listar_compromissos()` - Busca Todos os Compromissos
```python
records = sheet_compromissos.get_all_records()  # ← UMA requisição para TODOS os registros
```

**Resultado**:
- 1 requisição busca todos os compromissos
- Os dados são processados localmente

## ⚠️ ATENÇÃO: Problema Encontrado!

Há um problema no código atual que pode causar muitas requisições:

### No "Visualizar Dados" - Aba Itens:
```python
for item in itens:  # Loop pelos itens
    # ...
    compromissos_count = len([c for c in db.listar_compromissos() if c.item_id == item.id])
    # ↑ Isso chama listar_compromissos() para CADA item!
```

**Problema**: Se você tem 200 itens, isso chama `listar_compromissos()` **200 vezes**!

**Solução**: Carregar compromissos UMA vez antes do loop.

## 📈 Requisições Reais por Operação

### Visualizar Dados - Aba Itens:
- ✅ **1 requisição** para buscar todos os itens (`listar_itens()`)
- ⚠️ **200 requisições** para contar compromissos (se não corrigir)
- **Total**: 201 requisições (com o problema atual)

### Visualizar Dados - Aba Compromissos:
- ✅ **1 requisição** para buscar todos os compromissos (`listar_compromissos()`)
- ✅ **1 requisição** para buscar todos os itens (para cache)
- **Total**: 2 requisições

### Registrar Item:
- ✅ **1 requisição** para buscar próximo ID
- ✅ **1 requisição** para adicionar o item
- **Total**: 2 requisições

### Registrar Compromisso:
- ✅ **1 requisição** para buscar próximo ID
- ✅ **1 requisição** para verificar disponibilidade (busca compromissos)
- ✅ **1 requisição** para adicionar o compromisso
- **Total**: 3 requisições

## 🚀 Otimizações Já Implementadas

1. **Cache de 30 segundos**: Dados são armazenados por 30 segundos
   - Se você visualizar dados novamente em menos de 30 segundos = **0 requisições** (usa cache)

2. **Lazy Loading**: Itens relacionados só são carregados quando necessário

3. **Cache de itens em compromissos**: `listar_compromissos()` carrega todos os itens de uma vez

## 🔧 Correção Necessária

Preciso corrigir o código que conta compromissos dentro do loop para evitar múltiplas chamadas.
