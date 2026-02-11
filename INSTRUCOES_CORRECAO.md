# 🔥 INSTRUÇÕES CRÍTICAS - LEIA E EXECUTE NA ORDEM

## ❌ PROBLEMAS IDENTIFICADOS E CORRIGIDOS

### ✅ CORREÇÕES RECENTES (11/02/2026):

1. **✅ CORRIGIDO**: Edição de itens não mostrava campos da categoria (Placa, Marca, Modelo, etc.)
   - Agora o modal de edição exibe e permite editar os campos específicos da categoria
   
2. **✅ CORRIGIDO**: Deletar item não deletava da aba da categoria
   - Agora ao deletar um item, ele é removido tanto da aba "Itens" quanto da aba da categoria

### ⚠️ PROBLEMAS ANTERIORES (já corrigidos):

1. **Google Sheets ainda tem colunas antigas** (Juros, Multa, Desconto)
2. **Render pode não ter feito redeploy do backend**
3. **handleEdit está correto, mas financiamentos não têm itens carregados**

---

## ✅ PASSO A PASSO - EXECUTE EXATAMENTE ASSIM

### PASSO 1: CORRIGIR GOOGLE SHEETS (CRÍTICO!)

1. Abra sua planilha do Google Sheets
2. Vá na aba **"Parcelas Financiamento"**
3. **DELETE AS COLUNAS I, J, K** (Juros, Multa, Desconto)
4. Verifique que os headers são **EXATAMENTE**:
   ```
   A: ID
   B: Financiamento ID
   C: Numero Parcela
   D: Valor Original
   E: Valor Pago
   F: Data Vencimento
   G: Data Pagamento
   H: Status
   I: Link Boleto
   J: Link Comprovante
   ```

5. Se você tem parcelas antigas com dados nas colunas erradas, **delete todas as linhas de parcelas** (exceto o header) e deixe o app recriar.

---

### PASSO 2: FORÇAR REDEPLOY DO BACKEND NO RENDER

1. Vá em https://render.com
2. Acesse seu serviço **backend**
3. Clique em **"Manual Deploy"** → **"Deploy latest commit"**
4. **AGUARDE** o deploy terminar (pode levar 2-3 minutos)
5. Verifique os logs do deploy - **NÃO CONTINUE** se houver erros

---

### PASSO 2.1: TESTAR AS NOVAS FUNCIONALIDADES (OPCIONAL)

#### Teste 1: Editar Campos da Categoria

1. Vá em **"Visualizar Dados"** > Aba **"Itens"**
2. Clique em **"Editar"** (ícone de lápis) em um item
3. ✅ Você deve ver:
   - Campos padrão (Nome, Categoria, Quantidade, Descrição, UF, Cidade, Endereço)
   - **Campos específicos da categoria** (ex: para Carros → Placa, Marca, Modelo, Ano)
4. Edite um campo da categoria (ex: Placa)
5. Salve
6. Verifique se a alteração foi salva na aba da categoria no Google Sheets

#### Teste 2: Deletar Item com Cascade

1. Crie um item de teste em uma categoria (ex: Carros)
2. Verifique que o item aparece tanto na aba "Itens" quanto na aba "Carros" no Google Sheets
3. Delete o item no app
4. ✅ Verifique que o item foi removido de **AMBAS** as abas ("Itens" e "Carros")

---

### PASSO 3: VERIFICAR O CÓDIGO DO CONTRATO

**FRONTEND (`Financiamentos.jsx` linha 138-149):**
```javascript
const data = {
  codigo_contrato: formData.codigo_contrato || null,  // ✅ ESTÁ AQUI
  itens_ids: itens_ids,
  valor_total: valorTotal,
  // ... resto dos campos
}
```

**Se não aparecer no app:**
- Verifique se você está preenchendo o campo "Código do Contrato" no formulário
- Verifique no Google Sheets se a coluna B tem o valor

---

### PASSO 4: VERIFICAR ITENS NO FINANCIAMENTO

**O código está correto:**
- `handleEdit` (linha 217-259) busca dados completos com `financiamentosAPI.buscar(fin.id)`
- Backend retorna `itens` no `financiamento_to_dict`

**Se os itens não aparecem ao editar:**
1. Abra o **DevTools** (F12)
2. Vá em **Network**
3. Clique em editar um financiamento
4. Veja a resposta da API `/api/financiamentos/{id}`
5. Verifique se tem `"itens": [...]` na resposta

**Se não tiver `itens` na resposta:**
- O backend não foi redeployado (volte ao PASSO 2)
- Ou a aba "Financiamentos_Itens" não tem dados para aquele financiamento

---

## 🧪 TESTE COMPLETO

### 1. Criar Novo Financiamento
- Preencha **Código do Contrato**: `TESTE-001`
- Selecione **2 itens**
- Preencha os valores
- Salve

### 2. Verificar no Google Sheets
- Aba **"Financiamentos"**: Coluna B deve ter `TESTE-001`
- Aba **"Financiamentos_Itens"**: Deve ter 2 linhas com o ID do financiamento
- Aba **"Parcelas Financiamento"**: Deve ter 10 colunas (SEM Juros/Multa/Desconto)

### 3. Editar o Financiamento
- Clique em editar
- **DEVE APARECER**: Os 2 itens selecionados
- **DEVE APARECER**: O código do contrato preenchido

### 4. Ver Detalhes
- Clique no olho
- **DEVE APARECER**: Lista de itens
- **DEVE APARECER**: Código do contrato no lugar de "Financiamento #1"

---

## 🚨 SE AINDA NÃO FUNCIONAR

Execute estes comandos no terminal do projeto:

```bash
# 1. Forçar commit vazio para trigger deploy
git commit --allow-empty -m "force: trigger redeploy"
git push origin main

# 2. Limpar cache do navegador
# Ctrl+Shift+Delete → Limpar tudo das últimas 24h

# 3. Testar backend direto
curl https://SEU-BACKEND.onrender.com/api/financiamentos
```

---

## 📋 CHECKLIST FINAL

- [ ] Deletei colunas I, J, K da aba "Parcelas Financiamento"
- [ ] Headers da aba "Parcelas Financiamento" estão corretos (10 colunas)
- [ ] Fiz redeploy manual do backend no Render
- [ ] Deploy do backend terminou sem erros
- [ ] Limpei cache do navegador
- [ ] Testei criar um financiamento novo
- [ ] Parcelas criadas têm 10 colunas no Sheets
- [ ] Código do contrato aparece no app
- [ ] Itens aparecem ao editar financiamento

---

## 💡 CÓDIGO ESTÁ CORRETO

Eu **VERIFIQUEI LINHA POR LINHA**:

1. ✅ `sheets_config.py` (linha 331, 334, 343, 348): Headers corretos (10 colunas)
2. ✅ `sheets_database.py` (linha 1758-1769, 1808-1819): `append_row` com 10 valores
3. ✅ `sheets_database.py` (linha 2257): `ParcelaFinanciamento.__init__` sem juros/multa/desconto
4. ✅ `sheets_database.py` (linha 2506-2513): Índices corretos (Link Boleto=9, Link Comprovante=10)
5. ✅ `frontend/src/pages/Financiamentos.jsx` (linha 138): `codigo_contrato` no payload
6. ✅ `frontend/src/pages/Financiamentos.jsx` (linha 217-259): `handleEdit` busca dados completos
7. ✅ `sheets_database.py` (linha 2196-2251): `deletar_financiamento` deleta Financiamentos_Itens

**O problema está no GOOGLE SHEETS ou NO RENDER não ter redeployado!**
