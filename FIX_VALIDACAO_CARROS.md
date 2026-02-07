# 🔧 Correção: Validação de Campos de Carros

## 🐛 Problema

Ao cadastrar um carro, mesmo preenchendo todos os campos (Placa, Marca, Modelo, Ano), aparecia o erro:

```
Placa é obrigatória para carros; Marca é obrigatória para carros; 
Modelo é obrigatório para carros; Ano é obrigatório para carros
```

## 🔍 Causa Raiz

### Frontend
Quando a categoria "Carros" tem uma aba própria no Google Sheets com campos customizados (headers), o frontend envia os dados de duas formas diferentes:

**Opção 1: Com campos_categoria (quando aba existe com headers)**
```json
{
  "nome": "Fiat Uno",
  "categoria": "Carros",
  "campos_categoria": {
    "Placa": "ABC-1234",
    "Marca": "Fiat",
    "Modelo": "Uno",
    "Ano": 2020
  }
}
```

**Opção 2: Sem campos_categoria (compatibilidade, aba sem headers)**
```json
{
  "nome": "Fiat Uno",
  "categoria": "Carros",
  "placa": "ABC-1234",
  "marca": "Fiat",
  "modelo": "Uno",
  "ano": 2020
}
```

### Backend (sheets_database.py)
A função `validar_item_completo()` em `validacoes.py` espera receber os campos de carros como parâmetros separados:

```python
def validar_item_completo(
    nome, categoria, cidade, uf, quantidade_total,
    placa=None,        # ❌ Esperava aqui
    marca=None,        # ❌ Esperava aqui
    modelo=None,       # ❌ Esperava aqui
    ano=None,          # ❌ Esperava aqui
    campos_categoria=None  # ✅ Mas recebeu aqui dentro
):
    if categoria == 'Carros':
        if not placa:  # ❌ placa era None
            erros.append("Placa é obrigatória para carros")
```

## ✅ Solução

Adicionamos lógica para **extrair os campos de carros de `campos_categoria`** antes de chamar a validação:

### `criar_item()` - sheets_database.py (linha ~355)

```python
def criar_item(nome, quantidade_total, categoria=None, ..., campos_categoria=None):
    # ✅ NOVA LÓGICA: Extrai campos de carros se vieram em campos_categoria
    if categoria == 'Carros' and campos_categoria:
        if not placa and 'Placa' in campos_categoria:
            placa = campos_categoria.get('Placa')
        if not marca and 'Marca' in campos_categoria:
            marca = campos_categoria.get('Marca')
        if not modelo and 'Modelo' in campos_categoria:
            modelo = campos_categoria.get('Modelo')
        if not ano and 'Ano' in campos_categoria:
            ano = campos_categoria.get('Ano')
    
    # Agora a validação recebe os valores corretos
    valido, msg_erro = validacoes.validar_item_completo(
        nome=nome,
        categoria=categoria,
        placa=placa,      # ✅ Agora tem valor
        marca=marca,      # ✅ Agora tem valor
        modelo=modelo,    # ✅ Agora tem valor
        ano=ano,          # ✅ Agora tem valor
        ...
    )
```

### `atualizar_item()` - sheets_database.py (linha ~663)

Mesma lógica aplicada na função de atualização.

## 🎯 Comportamento Após Correção

1. **Frontend envia com `campos_categoria`**:
   - ✅ Backend extrai Placa, Marca, Modelo, Ano
   - ✅ Validação recebe valores corretos
   - ✅ Item criado com sucesso

2. **Frontend envia com parâmetros separados** (compatibilidade):
   - ✅ Backend usa valores diretos
   - ✅ Validação funciona normalmente
   - ✅ Item criado com sucesso

## 📝 Arquivos Modificados

- **sheets_database.py**:
  - `criar_item()` - linha ~355
  - `atualizar_item()` - linha ~663

## 🧪 Como Testar

1. Selecione categoria "Carros"
2. Preencha: Marca, Modelo, Placa, Ano
3. Clique em "Registrar Item"
4. ✅ Deve cadastrar sem erros

---

**Data da Correção**: 2026-02-07  
**Commit**: `4a0bf58`  
**Issue**: Validação falhava mesmo com campos preenchidos  
**Status**: ✅ RESOLVIDO
