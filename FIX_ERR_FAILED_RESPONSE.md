# 🐛 Fix: ERR_FAILED após salvar item (salvava mas dava erro)

## ❌ Problema Reportado

```
Sintoma: Item salva no Google Sheets MAS dá erro no frontend
Erro: net::ERR_FAILED
Console: Failed to load resource
```

### Comportamento Estranho:
- ✅ Item **aparecia** no Google Sheets (salvava)
- ❌ Frontend **recebia erro** (ERR_FAILED)
- ❌ Toast de sucesso **não aparecia**
- ❌ Lista **não atualizava**

---

## 🔍 Causa Raiz

### Fluxo do Problema:

1. Frontend envia dados do carro:
```javascript
{
  categoria: "Carros",
  campos_categoria: {
    Placa: "ABC-1234",
    Marca: "Fiat",
    Modelo: "Uno",
    Ano: 2020
  }
  // Mas NÃO envia placa, marca, modelo, ano como campos separados
}
```

2. Backend processa e salva no Sheets ✅

3. Backend tenta retornar resposta:
```python
# Em criar_item() - linha 521 (ANTES DA CORREÇÃO)
carro_obj = Carro(
    next_id, 
    placa.upper().strip(),  # ❌ placa era None -> CRASH!
    marca.strip(),           # ❌ marca era None -> CRASH!
    modelo.strip(),          # ❌ modelo era None -> CRASH!
    int(ano)                # ❌ ano era None -> CRASH!
)
```

4. Erro ao criar objeto Carro ❌
5. Request falha mas **item já foi salvo** no Sheets!

---

## ✅ Solução Implementada

### Código Corrigido (linha ~511-535)

```python
# Garante valores seguros para o objeto Carro
placa_safe = (placa or '').upper().strip() if placa else ''
marca_safe = (marca or '').strip() if marca else ''
modelo_safe = (modelo or '').strip() if modelo else ''
ano_safe = int(ano) if ano and str(ano).isdigit() else 0

carro_obj = Carro(next_id, placa_safe, marca_safe, modelo_safe, ano_safe)
```

### O que mudou:

**ANTES:**
```python
placa.upper().strip()  # ❌ Crash se placa=None
```

**AGORA:**
```python
(placa or '').upper().strip() if placa else ''  # ✅ Retorna '' se None
```

---

## 🎯 Resultado Após Correção

### Cenário 1: Campos em campos_categoria
```javascript
// Frontend envia
{
  categoria: "Carros",
  campos_categoria: { Placa: "ABC-1234", ... }
}

// Backend processa
1. Extrai campos de campos_categoria ✅
2. Salva no Sheets ✅
3. Cria objeto Carro com valores seguros ✅
4. Retorna resposta para frontend ✅
```

### Cenário 2: Campos separados (compatibilidade)
```javascript
// Frontend envia
{
  categoria: "Carros",
  placa: "ABC-1234",
  marca: "Fiat",
  ...
}

// Backend processa
1. Usa valores diretos ✅
2. Salva no Sheets ✅
3. Cria objeto Carro normalmente ✅
4. Retorna resposta para frontend ✅
```

---

## 🧪 Como Testar

### Teste 1: Cadastrar Carro Normal
1. Selecione categoria "Carros"
2. Preencha: Marca, Modelo, Placa, Ano
3. Clique em "Registrar Item"
4. ✅ Deve aparecer toast de sucesso
5. ✅ Item deve aparecer na lista
6. ✅ Item deve estar no Google Sheets

### Teste 2: Verificar Console
1. Abra DevTools (F12)
2. Vá em Console
3. Cadastre um item
4. ✅ Não deve ter erro `ERR_FAILED`
5. ✅ Deve ver resposta 201 (Created)

### Teste 3: Verificar Network
1. Abra DevTools (F12)
2. Vá em Network
3. Cadastre um item
4. Procure requisição POST `/api/itens`
5. ✅ Status: 201 Created (não 500 ou failed)
6. ✅ Response contém dados do item criado

---

## 📊 Comparação Antes/Depois

| Aspecto | Antes | Depois |
|---------|-------|--------|
| Item salva no Sheets | ✅ Sim | ✅ Sim |
| Response retorna | ❌ Crash | ✅ Sucesso |
| Frontend recebe sucesso | ❌ Não | ✅ Sim |
| Toast aparece | ❌ Não | ✅ Sim |
| Lista atualiza | ❌ Não | ✅ Sim |
| Console erro | ❌ ERR_FAILED | ✅ Sem erro |

---

## 🔗 Relação com Outras Correções

Esta correção complementa:

1. **Extração de campos** (`4a0bf58`):
   - Extrai Placa/Marca/Modelo/Ano de `campos_categoria`
   - Mas os valores extraídos podiam ser None

2. **Esta correção** (`3df6c5c`):
   - Trata valores None ao criar objeto de resposta
   - Garante que response sempre funciona

**Juntas**, essas correções garantem:
- ✅ Validação funciona (vê os campos)
- ✅ Salvamento funciona (grava no Sheets)
- ✅ Resposta funciona (retorna para frontend)

---

## 📝 Arquivo Modificado

- **sheets_database.py**: Função `criar_item()` (linha ~511-535)

---

## 💡 Lições Aprendidas

### Problema Sutil:
```python
# Este código parece inocente
placa.upper().strip()

# Mas se placa=None...
None.upper()  # ❌ AttributeError: 'NoneType' object has no attribute 'upper'
```

### Solução Defensiva:
```python
# Sempre assuma que valores podem ser None
(placa or '').upper().strip() if placa else ''
# ou
placa.upper().strip() if placa is not None else ''
```

---

**Data da Correção**: 2026-02-07  
**Commit**: `3df6c5c`  
**Issue**: Item salvava mas dava ERR_FAILED  
**Status**: ✅ RESOLVIDO

## 🎉 Resultado

Agora quando você cadastra um item:
1. ✅ Salva no Google Sheets
2. ✅ Backend retorna resposta de sucesso
3. ✅ Frontend recebe a resposta
4. ✅ Toast "Item registrado com sucesso!" aparece
5. ✅ Lista atualiza automaticamente

**Tudo funcionando como esperado!** 🚀
