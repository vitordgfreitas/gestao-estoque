# Instruções de Implantação e Teste

## 🚀 Implantação

### 1. Executar Migrações do Banco de Dados

Execute os scripts de migração na raiz do projeto:

```bash
# 1. Adiciona campo valor_entrada na tabela financiamentos
python migrate_add_valor_entrada.py

# 2. Cria tabela pecas_carros para associação de peças a carros
python migrate_add_pecas_carros.py
```

**Importante:** Execute esses scripts apenas UMA vez. Eles são idempotentes (não causam erro se executados novamente, mas fazem verificações).

### 2. Integrar Funções ao database.py

As funções para peças em carros estão no arquivo `database_pecas_carros.py`. Você precisa:

1. Abrir o arquivo `database.py`
2. Copiar o conteúdo de `database_pecas_carros.py` e colar no FINAL de `database.py`
3. Ou mover manualmente as funções:
   - `criar_peca_carro()`
   - `listar_pecas_carros()`
   - `buscar_peca_carro_por_id()`
   - `atualizar_peca_carro()`
   - `deletar_peca_carro()`

### 3. Atualizar criar_financiamento em database.py

A função `criar_financiamento()` atualizada está em `database_update_financiamento.py`. 

**IMPORTANTE:** Devido a problemas de encoding, você precisa substituir MANUALMENTE a função `criar_financiamento` em `database.py`:

1. Abra `database.py`
2. Localize a função `criar_financiamento` (por volta da linha 1198)
3. Substitua a função inteira pelo conteúdo de `database_update_financiamento.py`

### 4. Reiniciar Servidor

Após as mudanças:

```bash
# Backend (se estiver rodando local)
cd backend
uvicorn main:app --reload

# Frontend
cd frontend
npm run dev
```

---

## ✅ Checklist de Testes

### 1. Teste de Valores Decimais (CRÍTICO)

**Objetivo:** Verificar se os valores decimais são salvos e exibidos corretamente.

#### Teste no Financiamento:
1. Acesse "Financiamentos"
2. Crie um novo financiamento com:
   - Valor Total: R$ 200.000,00
   - Valor de Entrada: R$ 50.000,00
   - Número de Parcelas: 24
   - Taxa de Juros: 2% (digite "2" ou "2.00")
3. Salve o financiamento

**✅ Resultado Esperado:**
- Valor Total exibido: **R$ 200.000,00** (não R$ 200,00)
- Valor de Entrada: **R$ 50.000,00**
- Valor Financiado: **R$ 150.000,00** (200.000 - 50.000)
- Valor da Parcela: **R$ 7.287,71** (calculado com juros)
- Taxa de Juros: **2,00%** (não 200%)

#### Verificar no Google Sheets:
1. Abra o Google Sheets conectado
2. Na aba "Financiamentos", verifique os valores
3. Todos devem estar como números com 2 casas decimais:
   - `200000.00` (não `200` ou `200.0`)
   - `7287.71` (não `7.29` ou `72.88`)
   - `0.02` para taxa de juros (2%)

---

### 2. Teste de Valor de Entrada

**Objetivo:** Verificar que a entrada é deduzida do valor total.

#### Teste:
1. Crie um financiamento:
   - Valor Total: R$ 100.000,00
   - Entrada: R$ 30.000,00
   - 12 parcelas, taxa 1,5%
2. Verifique se:
   - Campo exibe "Valor financiado: R$ 70.000,00" abaixo do campo de entrada
   - As parcelas são calculadas sobre R$ 70.000,00 (não R$ 100.000,00)
   - A entrada aparece no card do financiamento

**✅ Resultado Esperado:**
- Valor Financiado calculado corretamente
- Entrada salva e exibida
- Parcelas baseadas no valor financiado

---

### 3. Teste de Categoria "Peças de Carro"

**Objetivo:** Verificar que a categoria foi adicionada corretamente.

#### Teste:
1. Acesse "Registrar Item"
2. No dropdown "Categoria", verifique se existe **"Peças de Carro"**
3. Selecione "Peças de Carro"
4. Cadastre uma peça:
   - Nome: "Pastilha de Freio Dianteira"
   - Categoria: Peças de Carro
   - Quantidade: 10
5. Salve

**✅ Resultado Esperado:**
- Categoria aparece no dropdown
- Peça é salva com sucesso
- Peça aparece em "Visualizar Dados" com categoria "Peças de Carro"

---

### 4. Teste de Associação Peças em Carros

**Objetivo:** Verificar a nova funcionalidade de associar peças a carros.

#### Pré-requisitos:
- Pelo menos 1 carro cadastrado
- Pelo menos 1 peça cadastrada (categoria "Peças de Carro")

#### Teste:
1. Acesse "Peças em Carros" no menu lateral (novo item)
2. Clique em "Adicionar Peça ao Carro"
3. Preencha:
   - Carro: Selecione um carro
   - Peça: Selecione uma peça
   - Quantidade: 4
   - Data de Instalação: (hoje)
   - Observações: "Instaladas na revisão de 20.000km"
4. Salve

**✅ Resultado Esperado:**
- Associação criada com sucesso
- Tabela exibe a associação com nome do carro e da peça
- É possível editar e deletar a associação
- Toast de sucesso aparece

---

### 5. Teste de Login Otimizado

**Objetivo:** Verificar melhorias na UX do login.

#### Teste:
1. Faça logout
2. Acesse a página de login
3. Observe:
   - Indicador "Verificando servidor..." (aparece por 1-3s)
   - Status "Servidor online" ou "Servidor inicializando"
4. Faça login com credenciais válidas

**✅ Resultado Esperado:**
- Preflight check mostra status do servidor
- Se servidor frio: mensagem clara de "aguarde 10-30s"
- Login funciona em < 5 segundos (servidor quente)
- Mensagens de erro claras e específicas

---

### 6. Teste de Formatação de Valores (Frontend)

**Objetivo:** Verificar que as funções de utilitário funcionam corretamente.

#### Áreas para verificar:
1. **Financiamentos:**
   - Valores de moeda com 2 casas decimais
   - Porcentagens exibidas corretamente
   - Entrada exibida quando > 0

2. **Peças em Carros:**
   - Datas formatadas como DD/MM/AAAA

**✅ Resultado Esperado:**
- Todos os valores monetários: R$ X.XXX,XX
- Todas as porcentagens: X,XX%
- Todas as datas: DD/MM/AAAA

---

### 7. Teste de Duplicações Removidas (Backend)

**Objetivo:** Verificar que código duplicado foi removido.

#### Verificação:
1. Abra `backend/main.py`
2. Procure por `class FinanciamentoUpdate` (deve aparecer apenas 1 vez)
3. Procure por `class FinanciamentoResponse` (deve aparecer apenas 1 vez)

**✅ Resultado Esperado:**
- Modelos Pydantic não duplicados
- Sem logs verbosos de DEBUG em produção (apenas se DEBUG_AUTH=true)

---

## ⚠️ Problemas Conhecidos e Soluções

### Problema: "Coluna valor_entrada não existe"
**Solução:** Execute `migrate_add_valor_entrada.py`

### Problema: "Tabela pecas_carros não existe"
**Solução:** Execute `migrate_add_pecas_carros.py`

### Problema: "função criar_peca_carro não definida"
**Solução:** Integre o conteúdo de `database_pecas_carros.py` ao `database.py`

### Problema: Valores ainda incorretos (ex: R$ 10,57 ao invés de R$ 10.574,22)
**Solução:** 
1. Verifique se `frontend/src/utils/format.js` existe
2. Verifique se `Financiamentos.jsx` importa as funções de `utils/format.js`
3. Limpe cache do navegador (Ctrl+Shift+Delete)

### Problema: Categoria "Peças de Carro" não aparece
**Solução:** 
- A categoria é dinâmica. Basta cadastrar um item com essa categoria uma vez
- Ou adicione manualmente ao código se necessário

---

## 📝 Resumo das Mudanças

### Backend
- ✅ Removido código duplicado (modelos Pydantic)
- ✅ Adicionado campo `valor_entrada` no modelo `Financiamento`
- ✅ Criado modelo `PecaCarro` para associação
- ✅ Criados endpoints API para peças em carros
- ✅ Corrigida formatação de decimais (sempre 2 casas)
- ✅ Otimizada autenticação (removidos logs verbosos)
- ✅ Adicionado health check endpoint

### Frontend
- ✅ Criado arquivo `utils/format.js` com funções de formatação
- ✅ Atualizado `Financiamentos.jsx` com campo de entrada
- ✅ Criada página `PecasCarros.jsx`
- ✅ Adicionada rota `/pecas-carros` no `App.jsx`
- ✅ Adicionado item no menu lateral
- ✅ Otimizado `Login.jsx` com preflight check
- ✅ Aumentado timeout para 30s (cold start)

### Database
- ✅ Scripts de migração criados
- ✅ Funções CRUD para peças em carros
- ✅ Atualizada lógica de cálculo de financiamento

---

## 🎯 Próximos Passos Recomendados

1. **Executar as migrações** (se ainda não executou)
2. **Testar cada funcionalidade** seguindo o checklist acima
3. **Verificar Google Sheets** para confirmar formato de valores
4. **Fazer backup** do banco de dados antes de usar em produção
5. **Considerar Redis** para cache de tokens em produção (ao invés do dict em memória)

---

**Data de criação:** 06/02/2026  
**Versão:** 1.0
